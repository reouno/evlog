#!/usr/bin/env python3
"""Build report.html for this experiment.

Charts: matplotlib, exported as SVG and inlined. Diagram: hand-written SVG.
Run from the repo root: uv run python experiments/e043_crown/report.py
(`report.py lineages` prints the top lineages of every run, to pick the gallery;
`report.py numbers` prints the means over the second half, for the README.)
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

BASE = "128_sigma0_r64_f0_flat_eyes8_flesh1_w1_season2_digest0_sidegrow_store5_yolk0_breed0_winterhigh_water0.1_leach0.01_depth0.01_mix0.2_strict"


def run(sat=0, hold=0, seed=9):
    return f"{BASE}{'_sat' if sat else ''}{'_hold' if hold else ''}_seed{seed}"


# e042's season world under strict (winter high 2, water 0.1, leach 0.01, depth 0.01, mix 0.2,
# flow 0, rain flat, side grow, k 1, sun 1, reach 0, thirst 0, stock 0, store 5): label ->
# (folder, run prefix, color slot). sat 0 and hold 0 is e042's strict run byte for byte.
RUNS = {
    "control": (HERE, run(0, 0), 5),
    "sat": (HERE, run(1, 0), 0),
    "hold": (HERE, run(0, 1), 1),
    "sat + hold": (HERE, run(1, 1), 2),
}
# Round 2: a second seed for the two runs with the saturation (the control is e042's strict seed
# 10, the same world byte for byte), and the start of sat + hold on six more seeds (20,000 steps:
# the first winter).
E042 = os.path.join(HERE, "..", "e042_strict")
SEED10 = {
    "control": (E042, run(0, 0, 10), 5),
    "sat": (HERE, run(1, 0, 10), 0),
    "sat + hold": (HERE, run(1, 1, 10), 2),
}
START_SEEDS = [11, 12, 13, 14, 15, 16]
STEPS = 100_000
SEASON = 20_000
LOG = 10_000  # steps per log.csv row

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


def exists(folder, run):
    """A run whose log has rows (a run still writing keeps its log empty until its buffer flushes)."""
    path = os.path.join(folder, f"results/{run}_log.csv")
    return os.path.exists(path) and os.path.getsize(path) > 200


def half_mean(d, key, lo=STEPS // 2, hi=STEPS):
    """The mean of a column over the rows with lo < step <= hi."""
    idx = [i for i, t in enumerate(d["step"]) if lo < t <= hi]
    return sum(d[key][i] for i in idx) / len(idx) if idx else float("nan")


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


def fine(run, folder, last_step):
    """Every 1,000 steps (pop.csv): the bodies alive, where the food lies; lineages of 5 or more."""
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


def sitter_share(run, folder=HERE):
    """Every lineages.csv step: (steps, share of the bodies in lineages whose mean body has under one muscle block)."""
    tot, sit = defaultdict(float), defaultdict(float)
    for r in load_rows(f"results/{run}_lineages.csv", folder):
        t, n = int(r["step"]), float(r["size"])
        tot[t] += n
        if float(r["muscle"]) < 1.0:
            sit[t] += n
    steps = sorted(tot)
    return [float(t) for t in steps], [sit[t] / tot[t] if tot[t] > 0 else float("nan") for t in steps]


def sitters_last_third(run, folder=HERE):
    """The sitters' share (as sitter_share) averaged over the last third of the run: one sample swings by 30 points."""
    ts, sh = sitter_share(run, folder)
    lo = ts[-1] - (ts[-1] - ts[0]) / 3
    last = [s for t, s in zip(ts, sh) if t >= lo]
    return sum(last) / len(last)


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
    """The lineage holding the most body-steps of the last third: (id, share, mean cells, mean muscle, flesh share)."""
    rows = load_rows(f"results/{run}_lineages.csv", folder)
    steps = [int(r["step"]) for r in rows]
    lo = max(steps) - (max(steps) - min(steps)) // 3
    total, muscle, cells, meat, plant = defaultdict(float), defaultdict(float), defaultdict(float), defaultdict(float), defaultdict(float)
    for r in rows:
        if int(r["step"]) < lo:
            continue
        i, n = int(r["lineage"]), float(r["size"])
        total[i] += n
        muscle[i] += n * float(r["muscle"])
        cells[i] += n * sum(float(r[k]) for k in KIND_COLS)
        meat[i] += n * float(r["meat"])
        plant[i] += n * float(r["plant"])
    i = max(total, key=total.get)
    all_n = sum(total.values())
    return i, total[i] / all_n, cells[i] / total[i], muscle[i] / total[i], meat[i] / max(meat[i] + plant[i], 1e-9)


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
    if xlabel == "step":
        ax.xaxis.set_major_formatter(kfmt)
    ax.set_xlabel(xlabel, loc="right")
    ax.margins(x=0)
    return fig, ax


def legend_above(ax, n):
    ax.legend(loc="lower left", bbox_to_anchor=(0, 1.0), ncols=n, handlelength=1.2, borderaxespad=0, columnspacing=1.2)


def line_chart(title, subtitle, xs, series, ymin=None, ymax=None, percent=False, xlabel="step", fmt=None):
    """series: list of (label, ys, slot)."""
    fig, ax = new_axes(xlabel)
    for label, ys, slot in series:
        ax.plot(xs, ys, color=SERIES[slot], linewidth=1.6, label=label)
    top = max((v for _, ys, _ in series for v in ys if v == v), default=1.0)
    if ymin is not None:
        ax.set_ylim(ymin, ymax if ymax is not None else top * 1.12)
    ax.yaxis.set_major_formatter(fmt or ((lambda y, _p: f"{y:.0%}") if percent else kfmt))
    ax.yaxis.set_major_locator(MaxNLocator(4))
    legend_above(ax, 4)
    return figure(title, subtitle, to_svg(fig))


def budget_chart(title, subtitle, rows, parts):
    """rows: [(run label, {part: value})]; parts: [(key, name, color)]. One stacked bar per run, the first on top."""
    fig, ax = plt.subplots(figsize=(6.4, 2.6))
    y = list(range(len(rows)))[::-1]
    left = [0.0] * len(rows)
    for key, name, color in parts:
        vals = [v[key] for _, v in rows]
        ax.barh(y, vals, left=left, color=color, height=0.62, label=name)
        left = [a + b for a, b in zip(left, vals)]
    ax.set_yticks(y, [label for label, _ in rows])
    ax.grid(False, axis="y")
    ax.grid(True, axis="x")
    ax.xaxis.set_major_locator(MaxNLocator(4))
    ax.set_xlabel("light a step", loc="right")
    ax.margins(x=0)
    legend_above(ax, len(parts))
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
    """picks: [(label, folder, run, lineage id, name, what the shape does)]. The most common grown body of each lineage
    at its peak, on the grid it grew on (drawn at the same width whatever the side), front up."""
    cards = []
    cache = {}
    for label, folder, run, lid, name, what in picks:
        if run not in cache:
            cache[run] = (lineage_rows(run, folder), load_bodies(run, folder), list(read_frames(f"results/{run}_long.jsonl", folder)))
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
<figcaption><strong>{html.escape(name)}</strong><br>{html.escape(label)}, lineage {lid}: {span:,} steps, {int(peak["size"]):,} agents at its peak<br>side {float(peak["side"]):.0f} (grid {side}x{side}); mass {float(peak["mass"]):.0f}: hard {float(peak["hard"]):.0f}, muscle {float(peak["muscle"]):.0f}, sensor {float(peak["sensor"]):.1f}, digestive {float(peak["digestive"]):.0f}; flesh {meat:.0%} of the intake<br>{html.escape(what)}</figcaption></figure>""")
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
th:first-child, td:first-child {{ text-align: left; }}
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
<svg viewBox="0 0 900 300" width="100%" role="img" aria-label="A column claims the light of the cells around it; what it cannot grow by falls as fruit on the ring of eight; sat scales the claim by the column's room, hold stops the claim of a column under a body" font-size="12" fill="currentColor" stroke="currentColor">
  <defs>
    <marker id="ar" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="currentColor" stroke="none"/></marker>
    <marker id="ar1" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="var(--s1)" stroke="none"/></marker>
  </defs>
  <g fill="none" stroke-width="1.2">
    <rect x="20" y="62" width="220" height="56" rx="6"/>
    <rect x="400" y="62" width="190" height="56" rx="6"/>
    <rect x="660" y="16" width="220" height="50" rx="6"/>
    <rect x="400" y="200" width="190" height="50" rx="6"/>
  </g>
  <rect x="660" y="112" width="220" height="56" rx="6" fill="none" stroke="var(--s1)" stroke-width="2"/>
  <g fill="none" stroke-width="1.3" marker-end="url(#ar)">
    <path d="M240,90 H396"/>
    <path d="M590,78 L656,44"/>
  </g>
  <path d="M590,102 L656,136" fill="none" stroke="var(--s1)" stroke-width="2" marker-end="url(#ar1)"/>
  <path d="M400,225 H270 V96" fill="none" stroke-width="1.3" stroke-dasharray="5 4" marker-end="url(#ar)"/>
  <g stroke="none">
    <text x="130" y="86" text-anchor="middle">the sun on the cells around</text>
    <text x="130" y="104" text-anchor="middle" font-size="11">every cell within the column's height</text>
    <text x="495" y="86" text-anchor="middle">a column (a tree)</text>
    <text x="495" y="104" text-anchor="middle" font-size="11">plant, dead and fruit, cap 8</text>
    <text x="770" y="38" text-anchor="middle">the column grows</text>
    <text x="770" y="55" text-anchor="middle" font-size="11">while it has room</text>
    <text x="770" y="136" text-anchor="middle" fill="var(--s1)" font-weight="600">fruit on the ring of 8</text>
    <text x="770" y="154" text-anchor="middle" font-size="11">growth past the cap, or under a body</text>
    <text x="495" y="222" text-anchor="middle">a body stands on it</text>
    <text x="495" y="239" text-anchor="middle" font-size="11">the column cannot grow (e016)</text>
    <text x="318" y="80" text-anchor="middle" font-size="11">claim, rate 2</text>
    <text x="342" y="112" text-anchor="middle" font-size="11">sat: × room / 8</text>
    <text x="604" y="50" font-size="11">room</text>
    <text x="606" y="158" font-size="11" fill="var(--s1)">no room</text>
    <text x="280" y="175" font-size="11">hold: no claim</text>
    <text x="20" y="286" font-size="11">Control (e022's law): a column claims at rate 2 whatever its height, and a column under a body claims too, so all it claims falls.</text>
  </g>
</svg>
<figcaption>Figure 1. The canopy under the fall. A column claims from every cell within its height a share of that cell's sun: the rate times (the height difference less the distance walked) over the cap. What it cannot grow by falls as fruit on the eight cells around it. <code>sat</code> multiplies the claim by the column's room (a full crown claims nothing, as in e021); <code>hold</code> stops the claim of a column under a body.</figcaption>
</figure>
"""


TEXT = {}  # filled in main(); counted at the end


def load_all():
    logs = {label: load_csv(f"results/{r}_log.csv", folder) for label, (folder, r, _) in RUNS.items() if exists(folder, r)}
    fines = {label: fine(r, folder, STEPS) for label, (folder, r, _) in RUNS.items() if label in logs}
    return logs, fines


def numbers():
    """The means over the second half, and the floors and the winner, per run (for the README)."""
    logs, fines = load_all()
    for label, d in logs.items():
        f = fines[label]
        folder, r, _ = RUNS[label]
        m = lambda k: half_mean(d, k)
        fm = lambda k: half_mean(f, k)
        eaten = (m("plant_intake") + m("meat_intake")) / LOG
        w = floors(f)
        i, share, cells, muscle, meat = top_lineage(r, folder)
        div, wins = diversity(r, folder)
        _, sh = sitter_share(r, folder)
        print(f"{label}: floors {[x['pop'] for x in w]} bodies {fm('pop'):.0f} trees {m('trees'):.0f} | shade {m('shade'):.1f} fruit {m('fruit'):.1f} "
              f"regrowth {m('regrowth'):.1f} dry {m('dry'):.1f} barren {m('barren'):.1f} shaded {m('shaded'):.1f} | fruit lying {m('fruit_stock'):.0f} "
              f"fruit_cells {fm('fruit_cells'):.3f} fruit_top {fm('fruit_top'):.3f} food_cells {fm('food_cells'):.3f} food_top {fm('food_top'):.3f} | "
              f"eaten {eaten:.1f} fruit eaten {m('fruit_eaten'):.1f} flesh {m('meat_intake') / (m('plant_intake') + m('meat_intake')):.2f} | "
              f"size p50 {m('size_p50'):.1f} p90 {m('size_p90'):.1f} muscle {m('muscle_mean'):.2f} speed {m('speed_mean'):.3f} move {m('move_spent'):.5f} "
              f"on_fat {fm('on_fat'):.2f} deaths {m('deaths_energy') / LOG:.1f} births {m('births') / LOG:.1f} | sitters end {sh[-1]:.2f} "
              f"lineages end {f['lineages'][-1]} top {i} {share:.0%} {cells:.1f} cells {muscle:.1f} muscle {meat:.0%} flesh | diversity {div} of {len(wins)}")


def main():
    logs, fines = load_all()
    slot = {label: s for label, (_, _, s) in RUNS.items()}
    xs = max((d["step"] for d in logs.values()), key=len)
    fx = max((d["step"] for d in fines.values()), key=len)
    sit = {label: sitter_share(r, folder) for label, (folder, r, _) in RUNS.items() if label in logs}
    fx2 = max((v[0] for v in sit.values()), key=len)

    def pad(ys, n):
        return ys + [float("nan")] * (n - len(ys))

    def series(key, labels=None, scale=1.0):
        return [(label, pad([v * scale for v in logs[label][key]], len(xs)), slot[label]) for label in (labels or RUNS) if label in logs and key in logs[label]]

    def fine_series(key, labels=None):
        return [(label, pad(list(fines[label][key]), len(fx)), slot[label]) for label in (labels or RUNS) if label in fines]

    sitters = [(label, pad(sit[label][1], len(fx2)), slot[label]) for label in RUNS if label in sit]
    # The log's rows are 10,000 steps apart, half a season: a pair of rows is one season.
    sx = [xs[i + 1] for i in range(0, len(xs) - 1, 2)]

    def season(fn, labels=None):
        out = []
        for label in (labels or RUNS):
            if label in logs:
                v = fn(logs[label])
                out.append((label, pad([(v[i] + v[i + 1]) / 2 for i in range(0, len(v) - 1, 2)], len(sx)), slot[label]))
        return out

    budget = [(label, {k: half_mean(logs[label], k) for k in ("regrowth", "fruit", "shaded", "dry", "barren")}) for label in RUNS if label in logs]
    charts_light = [
        budget_chart("Where the light goes", "The 146 of light a step that reaches the cells, by what it becomes, mean over steps 50,000-100,000. The canopy only moves light between cells.",
                     budget, [("regrowth", "grown on the cells", SERIES[7]), ("fruit", "fruit", SERIES[3]), ("shaded", "under bodies", SERIES[4]), ("dry", "dry", SERIES[6]), ("barren", "no soil", INK)]),
        line_chart("Food on the richest 1% of cells", "Share of all a gut can eat (plant, dead, fruit) lying on the richest 164 of 16,384 cells, every 1,000 steps. Lower is spread out.",
                   fx, fine_series("food_top"), ymin=0, ymax=1, percent=True),
    ]
    charts_world = [
        line_chart("Bodies", "Bodies alive every 1,000 steps; the dips are the winters.",
                   fx, fine_series("pop"), ymin=0),
    ]
    charts_bodies = [
        line_chart("Decisions that move", "Share of the decisions that step forward and find room, mean over each season (20,000 steps).",
                   sx, season(lambda d: [f * (1 - b) for f, b in zip(d["forward"], d["blocked"])]), ymin=0, percent=True),
        line_chart("The sitters' share", "Share of the bodies in lineages whose mean body has under one muscle block, mean over each season (it swings from 0 to 100% within one).",
                   sx, [(label, pad([sum(ys[i] for i in w) / len(w) for w in ([i for i, t in enumerate(fx2) if c * SEASON < t <= (c + 1) * SEASON] for c in range(len(sx))) if w], len(sx)), s)
                        for label, ys, s in sitters], ymin=0, ymax=1, percent=True),
    ]

    def light_row(label):
        d, f = logs[label], fines[label]
        m = lambda k: half_mean(d, k)
        fm = lambda k: half_mean(f, k)
        eaten = m("plant_intake") + m("meat_intake")
        return (f"<tr><td>{label}</td><td>{m('shade'):.0f}</td><td>{m('fruit'):.0f}</td><td>{m('regrowth'):.0f}</td>"
                f"<td>{m('fruit_stock'):,.0f}</td><td>{fm('fruit_top'):.0%}</td><td>{fm('food_top'):.0%}</td><td>{fm('food_cells'):.0%}</td>"
                f"<td>{m('trees'):.0f}</td><td>{eaten / LOG:.0f}</td><td>{m('meat_intake') / eaten:.0%}</td></tr>")

    def body_row(label):
        d, f = logs[label], fines[label]
        folder, r, _ = RUNS[label]
        w = floors(f)
        m = lambda k: half_mean(d, k)
        div, wins = diversity(r, folder)
        i, share, cells, muscle, meat = top_lineage(r, folder)
        moved = m("forward") * (1 - m("blocked"))
        return (f"<tr><td>{label}</td><td>{min(x['pop'] for x in w):,}-{max(x['pop'] for x in w):,}</td><td>{half_mean(f, 'pop'):,.0f}</td>"
                f"<td>{half_mean(f, 'age_mean'):,.0f}</td><td>{m('size_p50'):.1f}</td><td>{m('muscle_mean'):.2f}</td><td>{moved:.0%}</td><td>{m('move_spent'):.4f}</td>"
                f"<td>{sitters_last_third(r, folder):.0%}</td><td>{share:.0%}: {cells:.0f} cells, {muscle:.0f} muscle, {meat:.0%} flesh</td><td>{div} of {len(wins)}</td></tr>")

    light_rows = "".join(light_row(label) for label in RUNS if label in logs)
    body_rows = "".join(body_row(label) for label in RUNS if label in logs)

    def seed10_row(label):
        folder, r, _ = SEED10[label]
        d, f = load_csv(f"results/{r}_log.csv", folder), fine(r, folder, STEPS)
        m = lambda k: half_mean(d, k)
        w = floors(f)
        div, wins = diversity(r, folder)
        i, share, cells, muscle, meat = top_lineage(r, folder)
        top = f"{half_mean(f, 'food_top'):.0%}" if "food_top" in f else "-"  # e042 did not log it
        return (f"<tr><td>{label}, seed 10</td><td>{m('fruit'):.0f}</td><td>{m('regrowth'):.0f}</td><td>{top}</td>"
                f"<td>{min(x['pop'] for x in w):,}-{max(x['pop'] for x in w):,}</td><td>{half_mean(f, 'pop'):,.0f}</td>"
                f"<td>{m('forward') * (1 - m('blocked')):.0%}</td><td>{m('move_spent'):.4f}</td><td>{sitters_last_third(r, folder):.0%}</td>"
                f"<td>{share:.0%}: {cells:.0f} cells, {muscle:.0f} muscle, {meat:.0%} flesh</td><td>{div} of {len(wins)}</td></tr>")

    seed10_rows = "".join(seed10_row(label) for label, (folder, r, _) in SEED10.items() if exists(folder, r))
    start = []
    for s in START_SEEDS:
        p = os.path.join(HERE, f"results/{run(1, 1, s)}_pop.csv")
        if os.path.exists(p) and os.path.getsize(p) > 200:
            f = load_csv(f"results/{run(1, 1, s)}_pop.csv")
            start.append((s, int(min(f["pop"])), int(f["step"][f["pop"].index(min(f["pop"]))]), int(f["pop"][-1]), int(f["step"][-1])))
    start_rows = "".join(f"<tr><td>{s}</td><td>{lo:,} at {t:,}</td><td>{end:,} at {te:,}</td></tr>" for s, lo, t, end, te in start)
    tables = data_table(["step", "pop", "shade", "fruit", "regrowth", "fruit_stock", "fruit_eaten", "trees", "dry", "barren", "plant_intake", "meat_intake",
                         "move_spent", "size_p50", "muscle_mean", "speed_mean", "lineages"],
                        {label: d for label, d in logs.items()})
    TEXT.update(TEXTS)
    TEXT["gallery"] = gallery(GALLERY, GALLERY_CAPTION) if GALLERY else ""
    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>e043 What a crown takes - Report</title>
<style>{CSS}</style>
</head>
<body>
<main>
<h1>e043: What a crown takes</h1>
<p class="sub">Experiment report - 2026-09-10 - e022's canopy unbundled (#45, #44): the saturation and a held column's rest put back under the fall, one at a time and together, on seed 9 under strict, then on seed 10 and through the first winter of six more seeds. Answer: {TEXT["sub_answer"]}</p>

<section class="tldr">
<h2>TL;DR</h2>
<p>{TEXT["tldr"]}</p>
</section>

<h2>1. Question</h2>
<p>{TEXT["question"]}</p>
<ol>
  <li><strong>The rain is the saturation's:</strong> with <code>sat</code> the canopy moves under 30 a step and the fruit falls by half; <code>hold</code> alone moves the take by under a quarter.</li>
  <li><strong>The world stands</strong> in all four runs.</li>
  <li><strong>A mover wins when the food is spread and a body pays what it owes:</strong> under <code>sat</code> the moving and the muscle rise and the sitters' share falls.</li>
</ol>

<h2>2. The law</h2>
<p>{TEXT["world"]}</p>
{DIAGRAM}
<p><strong>Runs.</strong> {TEXT["runs"]}</p>
<ul class="measures">
  <li><strong>the canopy's take, fruit made, own growth</strong> - light moved into the columns, fruit falling, and plant grown on the cells, per step.</li>
  <li><strong>where the food lies</strong> - the share of the fruit, and of all a gut eats, on the richest 1% of cells, and the share of cells holding a step's sun of it (new).</li>
  <li><strong>bodies, floors, trees</strong> - bodies alive every 1,000 steps, the five winter troughs, cells standing at 1 or more.</li>
  <li><strong>eaten, flesh</strong> - what the bodies eat a step, and the share that is the dead.</li>
  <li><strong>size, muscle, moving</strong> - the median body in cells, the mean muscle blocks, what a body pays for moving a step.</li>
  <li><strong>sitters, top lineage, diversity</strong> - the bodies in lineages with under one muscle block, the lineage with the most of the last third, and the diversity number (#42).</li>
</ul>

<h2>3. Results</h2>
<p>Means over the second half (steps 50,000-100,000).</p>
<div class="tw"><table>
<thead><tr><th>run</th><th>canopy's take</th><th>fruit made</th><th>own growth</th><th>fruit lying</th><th>fruit on top 1%</th><th>food on top 1%</th><th>cells with food</th><th>trees</th><th>eaten a step</th><th>flesh</th></tr></thead>
<tbody>{light_rows}</tbody></table></div>
<div class="tw"><table>
<thead><tr><th>run</th><th>winter floors</th><th>bodies</th><th>mean age</th><th>median size</th><th>muscle</th><th>decisions that move</th><th>move cost a body</th><th>sitters, last third</th><th>top lineage of the last third</th><th>diversity (#42)</th></tr></thead>
<tbody>{body_rows}</tbody></table></div>
<ol class="verdicts">
{TEXT["verdicts"]}
</ol>

<h3>3.1 {TEXT["h_light"]}</h3>
<div class="grid2">
{"".join(charts_light)}
</div>
<p>{TEXT["p_light"]}</p>

<h3>3.2 {TEXT["h_world"]}</h3>
<div class="grid2">
{"".join(charts_world)}
</div>
<p>{TEXT["p_world"]}</p>

<h3>3.3 {TEXT["h_bodies"]}</h3>
<div class="grid2">
{"".join(charts_bodies)}
</div>
<p>{TEXT["p_bodies"]}</p>
{TEXT["gallery"]}

<h3>3.4 {TEXT["h_seeds"]}</h3>
<div class="tw"><table>
<thead><tr><th>run</th><th>fruit made</th><th>own growth</th><th>food on top 1%</th><th>winter floors</th><th>bodies</th><th>decisions that move</th><th>move cost a body</th><th>sitters, last third</th><th>top lineage of the last third</th><th>diversity (#42)</th></tr></thead>
<tbody>{seed10_rows}</tbody></table></div>
<div class="tw"><table>
<thead><tr><th>sat + hold, seed</th><th>fewest bodies (step)</th><th>bodies at the end (step)</th></tr></thead>
<tbody>{start_rows}</tbody></table></div>
<p>{TEXT["p_seeds"]}</p>

<h2>4. Discussion</h2>
{TEXT["discussion"]}

<h2>5. Conclusion and next step</h2>
<p>{TEXT["conclusion"]}</p>

<h2>Appendix: data</h2>
<p>Every log step (10,000 steps) of the four runs; the full data are in <code>results/*.csv</code>. Build this report with <code>uv run python experiments/e043_crown/report.py</code>.</p>
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
    ("sat + hold", HERE, run(1, 1), 253, "the grazer", "Eight muscle cells in front, eight gut behind: the muscle adds a second sub-cell to a step, so it reaches fresh lawn faster than a gut. 61% of the last third."),
    ("sat + hold", HERE, run(1, 1), 583, "the big sitter", "Sixteen gut cells and no muscle: it steps one sub-cell at a time and eats with every cell it has."),
    ("sat + hold", HERE, run(1, 1), 489, "the small sitter", "A bar of gut along the front, no muscle, mass 7: the cheapest body to keep and to move, 3% flesh."),
    ("sat + hold, seed 10", HERE, run(1, 1, 10), 801, "seed 10's winner", "A wide band of gut along the front, no muscle, mass 10: light for its size. 69% of the last third, where seed 9's grazer won."),
    ("sat", HERE, run(1, 0), 276, "the mover of the rich world", "The grazer's block in the world with the most bodies: 46% of what it eats is flesh, the dead lying where the crowd is."),
    ("sat", HERE, run(1, 0), 262, "its sitter", "A diagonal of gut cells on a 9x9 grid, no muscle: few blocks spread over many world cells."),
    ("hold", HERE, run(0, 1), 81, "the sitter on top", "A bar of eleven gut cells across the front, no muscle, mass 9: e042's sitter, on top when the free crowns still rain."),
]
GALLERY_CAPTION = "The most common grown body of each lineage at its peak, front up (orange muscle, aqua gut). The mover is one block in every world; the sitters differ: a full block, a bar, a diagonal."

TEXTS = {
    "sub_answer": "both. Each law alone leaves a third or more of the fruit rain; together they stop it, the lawn comes back, and the bodies move about twice as often.",
    "tldr": ("Since e022 the world's food is fruit raining onto a few hundred points under the trees. e022 had changed the canopy in two ways at "
             "once: a full crown kept taking light, and so did a crown under a body. Undoing either alone leaves a third or more of the rain; "
             "undoing both stops it (fruit 94-96 to 0.5-2 a step on two seeds). The lawn comes back, the bodies move on 40-46% of their decisions "
             "against 23-24%, and diversity is 3 against 2. Kept: both."),
    "question": ("In the season world the canopy moves 132 of the 146 of light a step into the tall columns, and 94 falls back as fruit, half of "
                 "it on 1% of the cells. Every law since e022 that needed a body to move lost to a body that stood still. When e022 added the "
                 "fall it also dropped e021's saturation and let a column under a body claim. Which of the two makes the rain?"),
    "world": ("Two laws about the plant, each off by default. sat: a column claims the rate times its room over the cap, so a full crown claims "
              "nothing (e021). hold: a column under a body claims nothing (e021). The fall stays: what a column cannot grow by falls on the eight "
              "cells around it."),
    "runs": ("e042's season world under strict, seed 9, 100,000 steps (five winters), four runs at once, 11-16 minutes each: the control "
             "(e042's strict run byte for byte), sat, hold, and both. Then sat and both on seed 10, and both on seeds 11-16 through the first "
             "winter. Means over the second half."),
    "verdicts": ("<li><span class=\"verdict partly\">Partly</span> sat alone cuts the fruit by half to two thirds (94 to 49; 96 to 31 on seed 10) "
                 "and hold alone by 14%; only both stop it (0.5 and 2.2).</li>"
                 "<li><span class=\"verdict\">Yes</span> all four stand on seed 9, and both on eight seeds; under both the winter floors are 8% "
                 "and 33% under the controls'.</li>"
                 "<li><span class=\"verdict partly\">Partly</span> the bodies move more (under both 40-46% of decisions, against 23-24%), but "
                 "muscle-free lineages keep 42-49% of the bodies on seed 9, and 74% under both on seed 10.</li>"),
    "h_light": "Only both laws stop the rain",
    "p_light": ("Each law closes one tap. Under hold the full crowns nobody stands on still take at the full rate (fruit 80 a step). Under sat "
                "the full crowns take nothing, but a column under a body is bitten, so it has the most room, claims hardest, and all of it falls "
                "around the body (49). With both, the light stays on the cells: 78 grown on them against 12, and 27% of the food on the richest "
                "1% against 48%."),
    "h_world": "The world stands in all four",
    "p_world": ("The bodies and the floors are the control's in three runs; sat alone feeds 51% more bodies on 26% more food, with 1,439 "
                "trees against 217. Under both, 40 of the 146 of light is lost under bodies, since a plant under a body does not grow, and the "
                "world eats 102 a step against 109."),
    "h_bodies": "The bodies move more; the sitters stay",
    "p_bodies": ("Under both, 46% of the decisions move a body against 23%: more step forward and fewer are blocked, since the crowd is spread. "
                 "The work of moving is 4.1 times the control's. A muscle-free gut is not still - it steps one sub-cell at a time - and holds "
                 "42-49% of the bodies in all four runs."),
    "h_seeds": "On a second seed the rain stops again, and who wins changes",
    "p_seeds": ("On seed 10 both stop the rain again (2.2 of fruit a step against 96) and give diversity 3 against 2, with floors a third "
                "lower. The top lineage is a light gut of 16 cells with no muscle (69% of the last third), where seed 9's is the grazer. sat "
                "alone leaves 31 of fruit. Under both, seeds 11-16 fall to 409-796 bodies in the first winter and recover: no lottery."),
    "discussion": ("<p>The rain came from e022 opening two taps at once, and the world uses whichever is left open. Close the full crowns' tap "
                   "and the bodies stand on the trees they bite, which a saturating crown feeds hardest; close the held crowns' tap and the free "
                   "full crowns keep pouring. Tested one at a time, each law would have looked like a small part of the answer.</p>"
                   "<p>Under both, the world is e021's canopy with a true overflow: the light stays where it falls, a plant under a body does not "
                   "grow, and a body eats by moving on. That is the condition every law since e022 that needed movement lacked. The moving "
                   "doubles, but the gut without muscle does not vanish: slow is not still.</p>"
                   "<p>What this does not show: the four-way comparison on one seed, 100,000 steps, and what the lawn selects in the long run - "
                   "a grazer on seed 9, a light gut on seed 10. The lower winter floors (8% and 33%) are the cost to watch.</p>"),
    "conclusion": ("Kept: the season world is sat 1 and hold 1 from here (the next experiment's default; both default to 0 here, e042 byte "
                   "for byte). The canopy is e021's again, and only what a column truly cannot hold falls. The laws since e022 that needed "
                   "movement - the thirst (#37), a growth that follows the stock (#43) - were tested in the rain and can be tried again. Next: "
                   "#47 ageing, then #38, #5."),
}


if __name__ == "__main__":
    if len(os.sys.argv) > 1 and os.sys.argv[1] == "lineages":
        for label, (folder, r, _) in RUNS.items():
            if not exists(folder, r):
                continue
            print(label)
            by = lineage_rows(r, folder)
            top = sorted(by, key=lambda lid: -sum(int(x["size"]) for x in by[lid]))[:6]
            for lid in top:
                rows = by[lid]
                peak = max(rows, key=lambda x: int(x["size"]))
                cells = sum(float(peak[k]) for k in KIND_COLS)
                print(f"  lineage {lid}: {sum(int(x['size']) for x in rows):,} body-samples, {int(rows[0]['step']):,}-{int(rows[-1]['step']):,}, peak {peak['size']} at {int(peak['step']):,}; cells {cells:.0f} mass {float(peak['mass']):.0f} hard {float(peak['hard']):.0f} muscle {float(peak['muscle']):.0f} sensor {float(peak['sensor']):.1f} gut {float(peak['digestive']):.0f} side {float(peak['side']):.0f} meat {float(peak['meat']) / max(float(peak['meat']) + float(peak['plant']), 1e-9):.2f}")
            div, wins = diversity(r, folder)
            print(f"  diversity {div} of {len(wins)} winners: " + "; ".join(f"{i} {s:.0%} {c:.1f} cells" for i, s, c, _ in wins))
    elif len(os.sys.argv) > 1 and os.sys.argv[1] == "numbers":
        numbers()
    else:
        main()
