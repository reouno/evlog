#!/usr/bin/env python3
"""Build report.html for this experiment.

Charts: matplotlib, exported as SVG and inlined. Diagram: hand-written SVG.
Run from the repo root: uv run python experiments/e044_wear/report.py
(`report.py lineages` prints the top lineages of every run, to pick the gallery;
`report.py numbers` prints the measures over the second half, for the README.)
"""
import csv
import html
import io
import json
import os
import re
from collections import Counter, defaultdict

import matplotlib
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator

matplotlib.use("svg")

HERE = os.path.dirname(os.path.abspath(__file__))
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#8a8a86", "#c9c8c0", "#7b61ff"]  # fixed slot order; slot 5 is the control
KIND_COLOR = {1: SERIES[0], 2: SERIES[1], 3: SERIES[3], 4: SERIES[2]}
CONFIRM_STEPS = 5000

# Chart chrome that reads on both light and dark backgrounds.
INK = "#898781"
plt.rcParams.update({
    "svg.fonttype": "none",
    "font.family": "sans-serif",
    "font.size": 9,
    "text.color": INK,
    "axes.edgecolor": INK,
    "axes.labelcolor": INK,
    "axes.facecolor": "none",
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.spines.left": False,
    "axes.grid": True,
    "axes.grid.axis": "y",
    "grid.color": INK,
    "grid.alpha": 0.25,
    "grid.linewidth": 0.8,
    "xtick.color": INK,
    "ytick.color": INK,
    "ytick.left": False,
    "legend.frameon": False,
    "legend.fontsize": 9,
    "figure.facecolor": "none",
    "savefig.transparent": True,
})

BASE = "128_sigma0_r64_f0_flat_eyes8_flesh1_w1_season2_digest0_sidegrow_store5_yolk0_breed0_winterhigh_water0.1_leach0.01_depth0.01_mix0.2_strict_sat_hold"


def run(wear=0, seed=9):
    return f"{BASE}{f'_wear{wear}' if wear else ''}_seed{seed}"


# e043's season world with sat 1 and hold 1 (strict, winter high 2, water 0.1, leach 0.01, depth
# 0.01, mix 0.2, flow 0, rain flat, side grow, store 5): label -> (run prefix, color slot, line
# style). wear 0 is e043's sat + hold run byte for byte.
RUNS = {
    "fixed age, seed 9": (run(0, 9), 5, "-"),
    "wear, seed 9": (run(3000, 9), 0, "-"),
    "fixed age, seed 10": (run(0, 10), 5, "--"),
    "wear, seed 10": (run(3000, 10), 0, "--"),
}
STEPS = 100_000
SEASON = 20_000
LOG = 10_000  # steps per log.csv row
BIN = 50  # deaths.csv bins the age at death by this many steps
OLD = 2_000  # "old": the age by which a body of 16 blocks expects its first worn block

# ---------- data ----------

def load_csv(path, folder=HERE):
    """Read a CSV of numbers into {column: [floats]}."""
    with open(os.path.join(folder, path)) as f:
        rows = [r for r in csv.DictReader(f) if None not in r.values()]
    return {k: [float(r[k]) for r in rows] for k in rows[0]}


def load_rows(path, folder=HERE):
    with open(os.path.join(folder, path)) as f:
        return [r for r in csv.DictReader(f) if None not in r.values()]


def lineage_rows(run, folder=HERE):
    by = defaultdict(list)
    for r in load_rows(f"results/{run}_lineages.csv", folder):
        by[int(r["lineage"])].append(r)
    return by


def load_bodies(run, folder=HERE):
    out = {}
    with open(os.path.join(folder, f"results/{run}_bodies.jsonl")) as f:
        for line in f:
            try:
                d = json.loads(line)
            except json.JSONDecodeError:
                break
            out[d["id"]] = (int(d.get("side", 8)), d["cells"])
    return out


def read_frames(path, folder=HERE):
    with open(os.path.join(folder, path)) as f:
        for line in f:
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                return


def exists(run, folder=HERE):
    """A run whose log has rows (a run still writing keeps its log empty until its buffer flushes)."""
    path = os.path.join(folder, f"results/{run}_log.csv")
    return os.path.exists(path) and os.path.getsize(path) > 200


def half_mean(d, key, lo=STEPS // 2, hi=STEPS):
    """The mean of a column over the rows with lo < step <= hi."""
    idx = [i for i, t in enumerate(d["step"]) if lo < t <= hi]
    return sum(d[key][i] for i in idx) / len(idx) if idx else float("nan")


def deaths(run, lo=STEPS // 2):
    """The deaths of bodies that lived after step lo: {(cause, age bin, size bin): [deaths, of them after a worn block]}."""
    out = defaultdict(lambda: [0, 0])
    for r in load_rows(f"results/{run}_deaths.csv"):
        if int(r["step"]) > lo:
            k = (r["cause"], int(r["age"]), int(r["size"]))
            out[k][0] += int(r["n"])
            out[k][1] += int(r["worn"])
    return out


def by_age(d):
    out = Counter()
    for (_c, a, _s), (n, _w) in d.items():
        out[a] += n
    return out


def quantile(counts, q):
    """The q-quantile of a distribution of ages in bins of BIN, linear within a bin."""
    total = sum(counts.values())
    if total == 0:
        return float("nan")
    target, acc = q * total, 0
    for a in sorted(counts):
        if acc + counts[a] >= target:
            return a + BIN * (target - acc) / counts[a]
        acc += counts[a]
    return float(max(counts) + BIN)


def death_stats(run):
    """The deaths of the second half: age quantiles, the fullest bin, causes, and the share that followed a worn block."""
    d = deaths(run)
    ages = by_age(d)
    total = sum(ages.values())
    cause = Counter()
    for (c, _a, _s), (n, _w) in d.items():
        cause[c] += n
    old = [(c, n, w) for (c, a, _s), (n, w) in d.items() if a >= OLD]
    old_n = sum(n for _, n, _ in old)
    old_worn = sum(w for _, _, w in old)
    old_worn_by = Counter()
    for c, _, w in old:
        old_worn_by[c] += w
    old_bins = [n for a, n in ages.items() if a >= 1000]
    return dict(total=total, p10=quantile(ages, 0.1), p50=quantile(ages, 0.5), p90=quantile(ages, 0.9), p99=quantile(ages, 0.99),
                top_bin=max(ages.values()) / total, top_age=max(ages, key=ages.get), oldest=max(ages) + BIN,
                top_old=max(old_bins, default=0) / total,
                cause={c: cause[c] / total for c in ("hunger", "broken", "age", "wear", "thirst")},
                worn=sum(w for _n, w in d.values()) / total, old=old_n / total, old_worn=old_worn / max(old_n, 1),
                old_worn_by={c: old_worn_by[c] / max(old_worn, 1) for c in ("hunger", "broken", "wear")})


def survival(run):
    """(ages, the share of the bodies that died in the second half that had reached each age)."""
    ages = by_age(deaths(run))
    total = sum(ages.values())
    xs = list(range(0, 5000, BIN))
    left, out = total, []
    for a in xs:
        out.append(left / total)
        left -= ages.get(a, 0)
    return xs, out


def worn_by_age(run, width=250):
    """(ages, the share of the deaths at each age that followed a worn block), in bins of `width` with 20 deaths or more."""
    n, w = Counter(), Counter()
    for (_c, a, _s), (k, wn) in deaths(run).items():
        n[a // width * width] += k
        w[a // width * width] += wn
    xs = list(range(0, 4500, width))
    return [x + width / 2 for x in xs], [w[x] / n[x] if n[x] >= 20 else float("nan") for x in xs]


def reach_by_size(run, age=OLD, least=200):
    """{size bin: the share of the bodies of that size at birth that reached `age`}, for bins with `least` deaths or more."""
    n, reached = Counter(), Counter()
    for (_c, a, s), (k, _w) in deaths(run).items():
        n[s] += k
        if a >= age:
            reached[s] += k
    return {s: reached[s] / n[s] for s in sorted(n) if n[s] >= least}


# ---------- the diversity number (#42), copied from e039 ----------
# The winners of a window are the lineages holding at least WIN_SHARE of its body-steps. Two
# winners are the same body when their sizes are within SIZE_FACTOR and the mixes of their blocks
# differ by at most MIX_DIST in sum; single linkage on that relation, the number of groups.
WIN_SHARE = 0.05
SIZE_FACTOR = 1.5
MIX_DIST = 0.4
KIND_COLS = ["hard", "muscle", "sensor", "digestive"]
PLACE_COL = {"world": "size", "valley": "p0", "slope": "p1", "ridge": "pnone"}


def same_body(a, b):
    """Two mean bodies (counts by kind) are the same shape."""
    sa, sb = sum(a), sum(b)
    if sa <= 0 or sb <= 0:
        return False
    if max(sa, sb) > SIZE_FACTOR * min(sa, sb):
        return False
    return sum(abs(x / sa - y / sb) for x, y in zip(a, b)) <= MIX_DIST


def diversity(run, folder=HERE, place="world", window=None):
    """(diversity, winners): the groups of winner bodies, and the winners, over `window` steps."""
    rows = load_rows(f"results/{run}_lineages.csv", folder)
    if not rows:
        return 0, []
    steps = [int(r["step"]) for r in rows]
    lo, hi = window or (max(steps) - (max(steps) - min(steps)) // 3, max(steps))
    col = PLACE_COL[place]
    total, shape = defaultdict(float), defaultdict(lambda: [0.0] * len(KIND_COLS))
    for r in rows:
        if not lo <= int(r["step"]) <= hi:
            continue
        n = float(r[col])
        if n <= 0:
            continue
        i = int(r["lineage"])
        total[i] += n
        for j, k in enumerate(KIND_COLS):
            shape[i][j] += n * float(r[k])
    body_steps = sum(total.values())
    if body_steps <= 0:
        return 0, []
    win = sorted((i for i, n in total.items() if n >= WIN_SHARE * body_steps), key=lambda i: -total[i])
    mean = {i: [x / total[i] for x in shape[i]] for i in win}
    groups = []
    for i in win:
        hit = [g for g in groups if any(same_body(mean[i], mean[j]) for j in g)]
        if hit:
            merged = [i] + [j for g in hit for j in g]
            groups = [g for g in groups if g not in hit] + [merged]
        else:
            groups.append([i])
    return len(groups), [(i, total[i] / body_steps, sum(mean[i]), mean[i]) for i in win]


def fine(run, folder=HERE, last_step=STEPS):
    """Every 1,000 steps (pop.csv): the bodies alive and their mean age; lineages of 5 or more."""
    lin = Counter()
    for rows in lineage_rows(run, folder).values():
        for r in rows:
            if int(r["step"]) <= last_step:
                lin[int(r["step"])] += 1
    d = load_csv(f"results/{run}_pop.csv", folder)
    keep = [i for i, t in enumerate(d["step"]) if t <= last_step]
    out = {k: [v[i] for i in keep] for k, v in d.items()}
    out["lineages"] = [lin[int(t)] for t in out["step"]]
    return out


def floors(f):
    """Per season window: the trough (bodies, lineages) and the peak."""
    out = []
    for c in range(int(max(f["step"])) // SEASON):
        idx = [i for i, t in enumerate(f["step"]) if c * SEASON < t <= (c + 1) * SEASON]
        if not idx:
            continue
        lo = min(idx, key=lambda i: f["pop"][i])
        hi = max(idx, key=lambda i: f["pop"][i])
        out.append(dict(step=int(f["step"][lo]), pop=int(f["pop"][lo]), lin=f["lineages"][lo], peak=int(f["pop"][hi])))
    return out


def top_lineage(run, folder=HERE):
    """The lineage holding the most body-steps of the last third: (id, share, mean cells, mean muscle, mean gut, flesh share)."""
    rows = load_rows(f"results/{run}_lineages.csv", folder)
    steps = [int(r["step"]) for r in rows]
    lo = max(steps) - (max(steps) - min(steps)) // 3
    total, muscle, gut, cells, meat, plant = (defaultdict(float) for _ in range(6))
    for r in rows:
        if int(r["step"]) < lo:
            continue
        i, n = int(r["lineage"]), float(r["size"])
        total[i] += n
        muscle[i] += n * float(r["muscle"])
        gut[i] += n * float(r["digestive"])
        cells[i] += n * sum(float(r[k]) for k in KIND_COLS)
        meat[i] += n * float(r["meat"])
        plant[i] += n * float(r["plant"])
    i = max(total, key=total.get)
    all_n = sum(total.values())
    return i, total[i] / all_n, cells[i] / total[i], muscle[i] / total[i], gut[i] / total[i], meat[i] / max(meat[i] + plant[i], 1e-9)


# ---------- chart helpers ----------

def kfmt(x, _pos):
    return f"{x/1000:g}k" if abs(x) >= 1000 else f"{x:g}"


def to_svg(fig):
    buf = io.StringIO()
    fig.savefig(buf, format="svg", bbox_inches="tight", pad_inches=0.05)
    plt.close(fig)
    return buf.getvalue()


def new_axes(xlabel="step", size=(6.4, 2.6)):
    fig, ax = plt.subplots(figsize=size)
    if xlabel in ("step", "age at death (steps)"):
        ax.xaxis.set_major_formatter(kfmt)
    ax.set_xlabel(xlabel, loc="right")
    ax.margins(x=0)
    return fig, ax


def legend_above(ax, n):
    ax.legend(loc="lower left", bbox_to_anchor=(0, 1.0), ncols=n, handlelength=1.8, borderaxespad=0, columnspacing=1.2)


def line_chart(title, subtitle, xs, series, ymin=None, ymax=None, percent=False, xlabel="step", fmt=None, ncols=2, vline=None):
    """series: list of (label, ys, slot, line style)."""
    fig, ax = new_axes(xlabel)
    for label, ys, slot, ls in series:
        ax.plot(xs, ys, color=SERIES[slot], linewidth=1.6, label=label, linestyle=ls)
    if vline is not None:
        ax.axvline(vline, color=INK, linewidth=0.8, linestyle=":")
    top = max((v for _, ys, _, _ in series for v in ys if v == v), default=1.0)
    if ymin is not None:
        ax.set_ylim(ymin, ymax if ymax is not None else top * 1.12)
    ax.yaxis.set_major_formatter(fmt or ((lambda y, _p: f"{y:.0%}") if percent else kfmt))
    ax.yaxis.set_major_locator(MaxNLocator(4))
    legend_above(ax, ncols)
    return figure(title, subtitle, to_svg(fig))


def figure(title, subtitle, svg):
    return f"""
<figure class="fig">
  <figcaption><strong>{html.escape(title)}</strong><span>{html.escape(subtitle)}</span></figcaption>
  {svg}
</figure>"""


def data_table(cols, rows_by_name, every=1):
    """Collapsed tables for the appendix. rows_by_name: {name: {col: [values]}}."""
    out = []
    for name, d in rows_by_name.items():
        cs = [c for c in cols if c in d]
        rows = "".join("<tr>" + "".join(f"<td>{d[c][i]:g}</td>" for c in cs) + "</tr>" for i in range(0, len(d[cs[0]]), every))
        out.append(f"<details><summary>{html.escape(name)}</summary><div class='tw'><table><thead><tr>"
                   + "".join(f"<th>{c}</th>" for c in cs) + f"</tr></thead><tbody>{rows}</tbody></table></div></details>")
    return "\n".join(out)


def gallery(picks, caption):
    """picks: [(label, run, lineage id, name, what the shape does)]. The most common grown body of each lineage
    at its peak, on the grid it grew on (drawn at the same width whatever the side), front up."""
    cards = []
    cache = {}
    for label, run, lid, name, what in picks:
        if run not in cache:
            cache[run] = (lineage_rows(run), load_bodies(run), list(read_frames(f"results/{run}_long.jsonl")))
        by, bodies, frames = cache[run]
        rows = by[lid]
        peak = max(rows, key=lambda r: int(r["size"]))
        span = int(rows[-1]["step"]) - int(rows[0]["step"]) + CONFIRM_STEPS
        frame = min((fr for fr in frames if any(a[4] == lid for a in fr["agents"])), key=lambda fr: abs(fr["step"] - int(peak["step"])))
        # The most common body among the grown ones (at least three quarters of the lineage's
        # mean cells at its peak): a lineage in bloom is mostly newborns of one or two cells.
        grown = 0.75 * sum(float(peak[k]) for k in KIND_COLS)
        ids = [a[2] for a in frame["agents"] if a[4] == lid]
        c = Counter(i for i in ids if sum(ch != "0" for ch in bodies[i][1]) >= grown) or Counter(ids)
        side, cells = bodies[c.most_common(1)[0][0]]
        u = 88 / side
        rects = "".join(f'<rect x="{(i % side) * u:.2f}" y="{(i // side) * u:.2f}" width="{u * 0.9:.2f}" height="{u * 0.9:.2f}" fill="{KIND_COLOR[int(k)]}"/>' for i, k in enumerate(cells) if k != "0")
        m, pl = float(peak["meat"]), float(peak["plant"])
        meat = m / (m + pl) if m + pl > 0 else 0
        cards.append(f"""<figure class="card"><svg viewBox="-1 -1 89 89" width="120" height="120" role="img" aria-label="{html.escape(name)}"><rect x="-1" y="-1" width="89" height="89" fill="var(--cell)"/>{rects}<line x1="-1" y1="-0.5" x2="88" y2="-0.5" stroke="var(--ink2)" stroke-width="1.5" stroke-dasharray="3 2"/></svg>
<figcaption><strong>{html.escape(name)}</strong><br>{html.escape(label)}, lineage {lid}: {span:,} steps, {int(peak["size"]):,} agents at its peak<br>side {float(peak["side"]):.0f} (grid {side}x{side}); mass {float(peak["mass"]):.0f}: hard {float(peak["hard"]):.0f}, muscle {float(peak["muscle"]):.0f}, sensor {float(peak["sensor"]):.1f}, digestive {float(peak["digestive"]):.0f}; flesh {meat:.0%} of the intake; mean age {float(peak["age"]):.0f}<br>{html.escape(what)}</figcaption></figure>""")
    return f"""<figure class="diagram"><div class="cards">{"".join(cards)}</div>
<figcaption>{caption}</figcaption></figure>"""


# ---------- page ----------

CSS = f"""
:root {{
  --surface: #fcfcfb; --page: #f9f9f7; --ink: #0b0b0b; --ink2: #52514e; --grid: #e1e0d9; --border: rgba(11,11,11,0.10);
  --s1: {SERIES[0]}; --cell: #f1f0ea;
}}
@media (prefers-color-scheme: dark) {{
  :root:not([data-theme="light"]) {{
    --surface: #1a1a19; --page: #0d0d0d; --ink: #ffffff; --ink2: #c3c2b7; --grid: #2c2c2a; --border: rgba(255,255,255,0.10);
    --s1: #3987e5; --cell: #262624;
  }}
}}
:root[data-theme="dark"] {{
  --surface: #1a1a19; --page: #0d0d0d; --ink: #ffffff; --ink2: #c3c2b7; --grid: #2c2c2a; --border: rgba(255,255,255,0.10);
  --s1: #3987e5; --cell: #262624;
}}
* {{ box-sizing: border-box; }}
body {{ margin: 0; background: var(--page); color: var(--ink); font: 15px/1.55 system-ui, -apple-system, "Segoe UI", sans-serif; }}
main {{ max-width: 960px; margin: 0 auto; padding: 32px 20px 64px; }}
h1 {{ font-size: 26px; margin: 0 0 4px; }}
h2 {{ font-size: 19px; margin: 40px 0 8px; }}
h3 {{ font-size: 16px; margin: 24px 0 8px; }}
p, li {{ color: var(--ink); max-width: 72ch; }}
.sub {{ color: var(--ink2); margin: 0 0 24px; }}
.tldr {{ background: var(--surface); border: 1px solid var(--border); border-left: 4px solid var(--s1); border-radius: 8px; padding: 12px 18px; }}
.tldr h2 {{ margin: 0 0 6px; font-size: 15px; }}
.tldr p {{ margin: 0; }}
.grid2 {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(420px, 1fr)); gap: 20px; }}
@media (max-width: 480px) {{ .grid2 {{ grid-template-columns: 1fr; }} }}
.grid2 > .fig:only-child {{ max-width: 470px; }}
.fig {{ margin: 0; background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 14px 14px 8px; }}
.fig svg {{ width: 100%; height: auto; display: block; font-family: system-ui, -apple-system, "Segoe UI", sans-serif; }}
figcaption strong {{ display: block; font-size: 15px; }}
figcaption span {{ display: block; color: var(--ink2); font-size: 13px; min-height: 2.6em; margin-bottom: 6px; }}
.diagram {{ margin: 12px 0; background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 12px 16px 8px; color: var(--ink); }}
.diagram figcaption {{ color: var(--ink2); font-size: 13px; margin-top: 4px; }}
.cards {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 16px; }}
.card {{ margin: 0; display: grid; grid-template-columns: 120px 1fr; gap: 12px; align-items: start; }}
.card figcaption {{ font-size: 12.5px; color: var(--ink2); margin: 0; }} .card figcaption strong {{ display: inline; font-size: 13px; color: var(--ink); }}
.measures {{ columns: 2; column-gap: 24px; max-width: none; padding-left: 20px; }} .measures li {{ break-inside: avoid; }}
@media (max-width: 640px) {{ .measures {{ columns: 1; }} }}
table {{ border-collapse: collapse; font-size: 13.5px; font-variant-numeric: tabular-nums; }}
th, td {{ padding: 6px 12px; text-align: right; border-bottom: 1px solid var(--grid); }}
th:first-child, td:first-child {{ text-align: left; white-space: nowrap; }}
th {{ color: var(--ink2); font-weight: 600; }}
.tw {{ overflow-x: auto; margin: 8px 0; }}
details {{ margin: 8px 0; }} summary {{ cursor: pointer; color: var(--ink2); }}
.verdicts {{ list-style: none; padding: 0; margin: 12px 0 0; }} .verdicts li {{ margin: 4px 0; }}
.verdict {{ display: inline-block; padding: 1px 8px; border-radius: 4px; font-size: 12.5px; font-weight: 600; background: rgba(12,163,12,0.12); color: #006300; }}
.verdict.no {{ background: rgba(208,59,59,0.12); color: #a12b2b; }}
.verdict.partly {{ background: rgba(250,178,25,0.15); color: #8a5a00; }}
:root[data-theme="dark"] .verdict.partly {{ color: #fab219; }}
@media (prefers-color-scheme: dark) {{ :root:not([data-theme="light"]) .verdict.partly {{ color: #fab219; }} }}
:root[data-theme="dark"] .verdict {{ color: #0ca30c; }} :root[data-theme="dark"] .verdict.no {{ color: #e66767; }}
@media (prefers-color-scheme: dark) {{ :root:not([data-theme="light"]) .verdict {{ color: #0ca30c; }} :root:not([data-theme="light"]) .verdict.no {{ color: #e66767; }} }}
"""

# Hand-written mechanism diagram. Label every arrow; currentColor for lines and text;
# var(--s1) for the one element the argument hinges on. Keep 10-15px between text and lines.
DIAGRAM = """
<figure class="fig diagram">
<svg viewBox="0 0 900 300" width="100%" role="img" aria-label="Each block of a living body fails with a chance that doubles every 300 steps of the body's age; a failed block lies on the ground as dead matter; the body lives on with fewer blocks and dies of hunger when it cannot pay for what is left, or of wear when no block is left" font-size="12" fill="currentColor" stroke="currentColor">
  <defs>
    <marker id="ar" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="currentColor" stroke="none"/></marker>
    <marker id="ar1" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="var(--s1)" stroke="none"/></marker>
  </defs>
  <g fill="none" stroke-width="1.2">
    <rect x="20" y="40" width="230" height="56" rx="6"/>
    <rect x="420" y="40" width="240" height="56" rx="6"/>
    <rect x="20" y="180" width="230" height="56" rx="6"/>
    <rect x="420" y="150" width="240" height="44" rx="6"/>
    <rect x="420" y="218" width="240" height="44" rx="6"/>
  </g>
  <path d="M250,68 H416" fill="none" stroke="var(--s1)" stroke-width="2" marker-end="url(#ar1)"/>
  <g fill="none" stroke-width="1.3" marker-end="url(#ar)">
    <path d="M135,96 V176"/>
    <path d="M250,200 L416,174"/>
    <path d="M250,216 L416,238"/>
  </g>
  <g stroke="none">
    <text x="135" y="64" text-anchor="middle">a block of a living body</text>
    <text x="135" y="82" text-anchor="middle" font-size="11">made at birth: its age is the body's</text>
    <text x="333" y="58" text-anchor="middle" fill="var(--s1)" font-weight="600">fails, chance h(age)</text>
    <text x="333" y="88" text-anchor="middle" font-size="11">doubles every 300 steps</text>
    <text x="540" y="64" text-anchor="middle">dead matter on the cell under it</text>
    <text x="540" y="82" text-anchor="middle" font-size="11">its matter, its share of energy and fat</text>
    <text x="147" y="140" font-size="11">what is left</text>
    <text x="135" y="204" text-anchor="middle">the body, a block less</text>
    <text x="135" y="222" text-anchor="middle" font-size="11">less food, less speed, less upkeep</text>
    <text x="540" y="168" text-anchor="middle">dies of hunger</text>
    <text x="540" y="184" text-anchor="middle" font-size="11">cannot pay for what is left (strict)</text>
    <text x="540" y="236" text-anchor="middle">dies of wear</text>
    <text x="540" y="252" text-anchor="middle" font-size="11">no block left</text>
    <text x="318" y="172" text-anchor="middle" font-size="11">cannot pay</text>
    <text x="330" y="250" text-anchor="middle" font-size="11">last block fails</text>
    <text x="700" y="160" font-size="11">h per block per step, wear 3,000:</text>
    <text x="700" y="180" font-size="11">at birth 1.6e-6</text>
    <text x="700" y="198" font-size="11">at age 2,000 1.6e-4</text>
    <text x="700" y="216" font-size="11">at age 3,000 1.6e-3</text>
    <text x="20" y="290" font-size="11">Fixed age (e043, wear 0): no block fails, and a body dies in the step it passes age 3,000.</text>
  </g>
</svg>
<figcaption>Figure 1. Wear. Every step each block of a living body fails with the chance h(a) = h0 · 2<sup>a/300</sup> at the body's age a, set so that half the blocks of age 3,000 have failed. A failed block falls as dead matter, as a broken block does, and the body lives on with what is left.</figcaption>
</figure>
"""


TEXT = {}  # filled in main(); counted at the end


def load_all():
    logs = {label: load_csv(f"results/{r}_log.csv") for label, (r, _, _) in RUNS.items() if exists(r)}
    fines = {label: fine(r) for label, (r, _, _) in RUNS.items() if label in logs}
    stats = {label: death_stats(r) for label, (r, _, _) in RUNS.items() if label in logs}
    return logs, fines, stats


def numbers():
    """The measures over the second half, per run (for the README)."""
    logs, fines, stats = load_all()
    for label, d in logs.items():
        f, s = fines[label], stats[label]
        r = RUNS[label][0]
        m = lambda k: half_mean(d, k)
        w = floors(f)
        i, share, cells, muscle, gut, meat = top_lineage(r)
        div, wins = diversity(r)
        print(f"{label}: deaths {s['total']:,} p10 {s['p10']:.0f} p50 {s['p50']:.0f} p90 {s['p90']:.0f} p99 {s['p99']:.0f} oldest {s['oldest']} "
              f"fullest bin {s['top_bin']:.1%} at {s['top_age']} | causes " + " ".join(f"{c} {v:.1%}" for c, v in s["cause"].items())
              + f" | worn {s['worn']:.1%} past {OLD} {s['old']:.1%} of them worn {s['old_worn']:.0%} (" + " ".join(f"{c} {v:.0%}" for c, v in s["old_worn_by"].items()) + ")")
        print(f"   floors {[x['pop'] for x in w]} bodies {half_mean(f, 'pop'):.0f} births {m('births') / LOG:.2f} mean age {half_mean(f, 'age_mean'):.0f} "
              f"lineages {half_mean(f, 'lineages'):.1f} worn/step {m('worn'):.3f} worn bodies {m('worn_bodies'):.3f} | size p50 {m('size_p50'):.1f} "
              f"muscle {m('muscle_mean'):.2f} gut {m('digestive_mean'):.2f} eaten {(m('plant_intake') + m('meat_intake')) / LOG:.1f} "
              f"flesh {m('meat_intake') / (m('plant_intake') + m('meat_intake')):.2f} | top {i} {share:.0%} {cells:.1f} cells {muscle:.1f} muscle {gut:.1f} gut {meat:.0%} flesh | diversity {div} of {len(wins)}")
        print("   reach 2,000 by size: " + " ".join(f"{s_}:{v:.1%}" for s_, v in reach_by_size(r).items()))


def main():
    logs, fines, stats = load_all()
    style = {label: (slot, ls) for label, (_, slot, ls) in RUNS.items()}
    fx = max((d["step"] for d in fines.values()), key=len)

    def pad(ys, n):
        return ys + [float("nan")] * (n - len(ys))

    def fine_series(key):
        return [(label, pad(list(fines[label][key]), len(fx)), *style[label]) for label in RUNS if label in fines]

    surv = {label: survival(RUNS[label][0]) for label in logs}
    ax_age = surv[next(iter(surv))][0]
    worn = {label: worn_by_age(RUNS[label][0]) for label in logs if "wear" in label}
    ax_worn = next(iter(worn.values()))[0] if worn else []
    charts_age = [
        line_chart("Survival by age", "Share of the bodies that died in the second half that had reached each age. The fixed age ends in a wall at 3,000.",
                   ax_age, [(label, ys, *style[label]) for label, (_, ys) in surv.items()], ymin=0, ymax=1, percent=True, xlabel="age at death (steps)"),
        line_chart("Deaths after a worn block", "Share of the deaths at each age (bins of 250 steps) that came after the body had lost a block to wear. Wear runs only.",
                   ax_worn, [(label, ys, *style[label]) for label, (_, ys) in worn.items()], ymin=0, ymax=1, percent=True, xlabel="age at death (steps)"),
    ]
    charts_world = [
        line_chart("Bodies", "Bodies alive every 1,000 steps; the dips are the winters.", fx, fine_series("pop"), ymin=0),
        line_chart("Lineages alive", "Lineages of 5 bodies or more, every 1,000 steps.", fx, fine_series("lineages"), ymin=0),
    ]

    def death_row(label):
        s = stats[label]
        c = s["cause"]
        wear, na = "wear" in label, "<td>-</td>"
        return (f"<tr><td>{label}</td><td>{s['p10']:,.0f}</td><td>{s['p50']:,.0f}</td><td>{s['p90']:,.0f}</td><td>{s['p99']:,.0f}</td>"
                f"<td>{s['top_bin']:.1%}</td><td>{s['top_old']:.1%}</td><td>{c['hunger']:.0%}</td><td>{c['broken']:.0%}</td>"
                + (na if wear else f"<td>{c['age']:.1%}</td>") + (f"<td>{c['wear']:.2%}</td><td>{s['worn']:.1%}</td>" if wear else na * 2)
                + f"<td>{s['old']:.1%}</td>" + (f"<td>{s['old_worn']:.0%}</td>" if wear else na) + "</tr>")

    def world_row(label):
        d, f = logs[label], fines[label]
        r = RUNS[label][0]
        w = floors(f)
        m = lambda k: half_mean(d, k)
        div, wins = diversity(r)
        i, share, cells, muscle, gut, meat = top_lineage(r)
        return (f"<tr><td>{label}</td><td>{min(x['pop'] for x in w):,}-{max(x['pop'] for x in w):,}</td><td>{half_mean(f, 'pop'):,.0f}</td>"
                f"<td>{m('births') / LOG:.1f}</td><td>{half_mean(f, 'age_mean'):,.0f}</td><td>{half_mean(f, 'lineages'):.1f}</td>"
                f"<td>{share:.0%}: {cells:.0f} cells, {muscle:.0f} muscle, {gut:.0f} gut, {meat:.0%} flesh</td><td>{div} of {len(wins)}</td></tr>")

    death_rows = "".join(death_row(label) for label in RUNS if label in logs)
    world_rows = "".join(world_row(label) for label in RUNS if label in logs)
    tables = data_table(["step", "pop", "births", "deaths_energy", "deaths_age", "deaths_broken", "deaths_wear", "worn", "worn_bodies", "worn_deaths",
                         "age_p10", "age_p50", "age_p90", "size_p50", "muscle_mean", "digestive_mean", "lineages"],
                        {label: d for label, d in logs.items()})
    TEXT.update(TEXTS)
    TEXT["gallery"] = gallery(GALLERY, GALLERY_CAPTION) if GALLERY else ""
    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>e044 Wear - Report</title>
<style>{CSS}</style>
</head>
<body>
<main>
<h1>e044: Wear</h1>
<p class="sub">Experiment report - 2026-09-11 - ageing as a law of the material (#47): every block fails with a chance that doubles with the body's age, against the fixed age of 3,000, on seeds 9 and 10 in e043's world. Answer: {TEXT["sub_answer"]}</p>

<section class="tldr">
<h2>TL;DR</h2>
<p>{TEXT["tldr"]}</p>
</section>

<h2>1. Question</h2>
<p>{TEXT["question"]}</p>
<ol>
  <li><strong>The age at death spreads:</strong> no 50-step bin of age holds more than 2% of the deaths.</li>
  <li><strong>A decline comes before death:</strong> most deaths past age 2,000 follow a worn block, and most of those are by hunger.</li>
  <li><strong>The world stands and turns over faster:</strong> bodies and floors within 15%, more births, lineages and diversity at least the fixed age's.</li>
</ol>

<h2>2. The law</h2>
<p>{TEXT["world"]}</p>
{DIAGRAM}
<p><strong>Runs.</strong> {TEXT["runs"]}</p>
<ul class="measures">
  <li><strong>age at death</strong> - p10, p50, p90 and p99 of the bodies that lived (born with a block), steps 50,000-100,000.</li>
  <li><strong>fullest bin</strong> - the largest share of those deaths in one 50-step bin of age, and the same among the bins past age 1,000.</li>
  <li><strong>causes</strong> - hunger (cannot pay), broken (by another body), age (the fixed age), wear (no block left).</li>
  <li><strong>after a worn block</strong> - the share of the deaths whose body had lost a block to wear; the same for the deaths past age 2,000.</li>
  <li><strong>bodies, floors, births, mean age</strong> - bodies alive every 1,000 steps, the five winter troughs, births a step, the mean age of the living.</li>
  <li><strong>lineages, top lineage, diversity</strong> - lineages of 5 or more, the one with the most of the last third, and the diversity number (#42).</li>
</ul>

<h2>3. Results</h2>
<p>Means over the second half (steps 50,000-100,000).</p>
<div class="tw"><table>
<thead><tr><th>run</th><th>age at death p10</th><th>p50</th><th>p90</th><th>p99</th><th>fullest bin</th><th>past 1,000</th><th>hunger</th><th>broken</th><th>age</th><th>wear</th><th>after a worn block</th><th>past 2,000</th><th>of those, after a worn block</th></tr></thead>
<tbody>{death_rows}</tbody></table></div>
<div class="tw"><table>
<thead><tr><th>run</th><th>winter floors</th><th>bodies</th><th>births a step</th><th>mean age</th><th>lineages alive</th><th>top lineage of the last third</th><th>diversity (#42)</th></tr></thead>
<tbody>{world_rows}</tbody></table></div>
<ol class="verdicts">
{TEXT["verdicts"]}
</ol>

<h3>3.1 {TEXT["h_age"]}</h3>
<div class="grid2">
{"".join(charts_age)}
</div>
<p>{TEXT["p_age"]}</p>

<h3>3.2 {TEXT["h_world"]}</h3>
<div class="grid2">
{"".join(charts_world)}
</div>
<p>{TEXT["p_world"]}</p>
{TEXT["gallery"]}

<h2>4. Discussion</h2>
{TEXT["discussion"]}

<h2>5. Conclusion and next step</h2>
<p>{TEXT["conclusion"]}</p>

<h2>Appendix: data</h2>
<p>Every log step (10,000 steps) of the four runs; the full data are in <code>results/*.csv</code> (<code>deaths.csv</code>: the deaths by cause, age and size at birth). Build this report with <code>uv run python experiments/e044_wear/report.py</code>.</p>
{tables}
</main>
</body>
</html>
"""
    out = os.path.join(HERE, "report.html")
    with open(out, "w") as f:
        f.write(page)
    words = sum(len(re.sub(r"<[^>]+>", " ", html.unescape(v)).split()) for k, v in TEXT.items() if k != "gallery")
    print(f"wrote {out} ({os.path.getsize(out)//1024} KB); TEXT {words} words")


GALLERY = [
    ("fixed age, seed 9", run(0, 9), 253, "the grazer at the wall", "Five muscle blocks in front of ten gut on a 4x4 grid. Its bodies live past 1,000 steps, and the fixed age took them on one step."),
    ("wear, seed 9", run(3000, 9), 705, "the grazer under wear", "The same plan in a new lineage. Its old bodies lose blocks before they die, and it holds 32% of the last third, not 61%."),
    ("wear, seed 9", run(3000, 9), 336, "the sitter beside it", "Eleven gut blocks, no muscle, mass 10: it steps a sub-cell at a time and lives a few hundred steps, before wear begins."),
    ("fixed age, seed 10", run(0, 10), 801, "the light gut", "Sixteen gut blocks spread on a wide grid, mass 10: e043's winner of seed 10, 69% of the last third."),
    ("wear, seed 10", run(3000, 10), 575, "seed 10's gut under wear", "Fifteen gut blocks and no muscle: the same plan wins, and its bodies die at a few hundred steps, before wear begins."),
    ("wear, seed 10", run(3000, 10), 438, "a hunter beside it", "Seven muscle blocks, four or five sensors, four gut: 81% of what it eats is flesh. Alive from step 30,000 to the end."),
]
GALLERY_CAPTION = "The most common grown body of each lineage at its peak, front up (orange muscle, aqua gut, yellow sensor). Wear does not change the plan on top: a grazer on seed 9, a gut on seed 10."

TEXTS = {
    "sub_answer": "the wall at 3,000 becomes a slope. The old die between 2,000 and 4,200, almost all after losing blocks, and the world stands. Kept at 3,000.",
    "tldr": ("Every body died at exactly age 3,000, 11% of all deaths on seed 9. Under wear each block fails with a chance that doubles "
             "with age and falls as dead matter. The pile at 3,001 is gone: the old die between 2,000 and 4,200, and 96% of them had lost "
             "blocks first, most dying of hunger. The world stands on both seeds; on seed 9 births rise 31%. Kept: wear 3,000. Next: #38."),
    "question": ("A body died in the step it passed age 3,000, with nothing before it. In e043's world this wall took 11% of the deaths on "
                 "seed 9. A clock is a law of the world; the project wants laws of the material (#47). Can the chance of death rise with "
                 "age through the blocks themselves, and what does that change: the age at death, a decline before death, the turnover?"),
    "world": ("Every step each block of a living body fails with a chance that doubles every 300 steps of the body's age, set so that half "
              "the blocks of age 3,000 have failed. A failed block lies on the ground with its share of energy and fat. Not heritable, "
              "and nothing about size."),
    "runs": ("e043's world (strict, sat, hold), seeds 9 and 10, 100,000 steps, four runs at once, 11-15 minutes each: the fixed age (e043 "
             "byte for byte) and wear 3,000. The deaths are those of bodies born with a block, steps 50,000-100,000."),
    "verdicts": ("<li><span class=\"verdict partly\">Partly</span> As written no: newborns fill the youngest bins (18-26%) in every run. "
                 "Past age 1,000 no bin holds over 0.8% under wear, against 10.9% at 3,001.</li>"
                 "<li><span class=\"verdict\">Yes</span> 96% of the deaths past 2,000 on seed 9 followed a worn block (93% on seed 10); "
                 "61% of those were hunger, 35% wear.</li>"
                 "<li><span class=\"verdict partly\">Partly</span> The world stands (lowest floors 475 and 446, against 491 and 435); on "
                 "seed 9 births rise 31% and lineages triple, but the mean age does not fall. Diversity: 2 against 3.</li>"),
    "h_age": "The wall becomes a slope",
    "p_age": ("On seed 9, 13% of the bodies reach age 2,000; under the fixed age those alive at 3,000 all die on its next step. Under wear "
              "they start losing blocks near 2,000 (92% of the living past 2,000 had lost some, 5 on average) and die over the next 2,000 "
              "steps. Seed 10's bodies rarely get old (p90 age at death 456-480): wear touches 1.5% of its deaths."),
    "h_world": "The world stands; where bodies get old, it turns over faster",
    "p_world": ("On seed 9 births rise from 3.2 to 4.1 a step and the bodies from 2,000 to 2,380 on the same food, and the top lineage holds "
                "32% of the last third against 61%. The lineages alive swing with the season, 5-34 against 2-10, peaking at the end of each "
                "summer. Seed 10's runs differ as two paths of one world do after the first worn block."),
    "discussion": ("<p>Wear moves the old deaths off one step and onto a decline. Most old bodies do not lose every block: they lose five "
                   "or so, eat less, and die of hunger (61% on seed 9) before the last block goes (35%). The decline comes from the upkeep "
                   "law, not from a rule about age.</p>"
                   "<p>Wear matters only where bodies get old. On seed 9 the winner is a grazer whose bodies live past 1,000 steps; wear "
                   "halves its share and more lineages come and go beside it. On seed 10 most bodies die before 500 steps.</p>"
                   "<p>What this does not show: the rise in births and lineages rests on one seed where wear matters, so it is a reading. "
                   "Whether size buys a longer life cannot be read: the bodies that reach 2,000 are one lineage's 16-block body. The "
                   "diversity number falls to 2 with more winners (4 and 5 against 3), because the new winners share the old shapes.</p>"),
    "conclusion": ("Kept: wear 3,000 is the season world's default from here, and the fixed age is gone (wear 0 keeps it, e043 byte for "
                   "byte). A body ages by losing blocks and dies of what it can no longer pay for. No batch: the plan on top is the same "
                   "with and without wear on both seeds. Next: #38, the rain on the ridge under the water carrier, then #5."),
}


if __name__ == "__main__":
    if len(os.sys.argv) > 1 and os.sys.argv[1] == "lineages":
        for label, (r, _, _) in RUNS.items():
            if not exists(r):
                continue
            print(label)
            by = lineage_rows(r)
            top = sorted(by, key=lambda lid: -sum(int(x["size"]) for x in by[lid]))[:6]
            for lid in top:
                rows = by[lid]
                peak = max(rows, key=lambda x: int(x["size"]))
                cells = sum(float(peak[k]) for k in KIND_COLS)
                print(f"  lineage {lid}: {sum(int(x['size']) for x in rows):,} body-samples, {int(rows[0]['step']):,}-{int(rows[-1]['step']):,}, peak {peak['size']} at {int(peak['step']):,}; cells {cells:.0f} mass {float(peak['mass']):.0f} hard {float(peak['hard']):.0f} muscle {float(peak['muscle']):.0f} sensor {float(peak['sensor']):.1f} gut {float(peak['digestive']):.0f} side {float(peak['side']):.0f} age {float(peak['age']):.0f} meat {float(peak['meat']) / max(float(peak['meat']) + float(peak['plant']), 1e-9):.2f}")
            div, wins = diversity(r)
            print(f"  diversity {div} of {len(wins)} winners: " + "; ".join(f"{i} {s:.0%} {c:.1f} cells" for i, s, c, _ in wins))
    elif len(os.sys.argv) > 1 and os.sys.argv[1] == "numbers":
        numbers()
    else:
        main()
