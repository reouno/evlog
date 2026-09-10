#!/usr/bin/env python3
"""Build report.html for this experiment.

Charts: matplotlib, exported as SVG and inlined. Diagram: hand-written SVG.
Run from the repo root: uv run python experiments/e042_strict/report.py
(`report.py lineages` prints the top lineages of every run, to pick the gallery.)
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
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#8a8a86", "#c9c8c0", "#7b61ff"]  # fixed slot order; slots 5 and 6 are the control
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

BASE = "128_sigma0_r64_f0_flat_eyes8_flesh1_w1_season2_digest0_sidegrow_store{store}_yolk0_breed0_winterhigh_water0.1_leach0.01_depth0.01_mix0.2"


def run(strict=0, store=5, seed=9):
    return f"{BASE.format(store=store)}{'_strict' if strict else ''}_seed{seed}"


# e041's season world (winter high 2, water 0.1, leach 0.01, depth 0.01, mix 0.2, flow 0, rain
# flat, side grow, k 1, sun 1, reach 0, thirst 0, stock 0): label -> (folder, run prefix, color
# slot). `strict` 0 at store 5 is e041 byte for byte (all but the three new log columns).
RUNS = {
    "control, seed 9": (HERE, run(0, 5, 9), 5),
    "control, seed 10": (HERE, run(0, 5, 10), 6),
    "strict, seed 9": (HERE, run(1, 5, 9), 0),
    "strict, seed 10": (HERE, run(1, 5, 10), 7),
    "strict, no store, seed 9": (HERE, run(1, 0, 9), 1),
}
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


def median(x):
    x = sorted(v for v in x if v == v)
    return x[len(x) // 2] if x else float("nan")


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
    """Every 1,000 steps (pop.csv): the bodies alive, the share at zero energy, per band; lineages of 5 or more."""
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
    legend_above(ax, 3)
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
.tw {{ overflow-x: auto; }}
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
<svg viewBox="0 0 900 312" width="100%" role="img" aria-label="A body's upkeep is paid by its energy, this step's food and its fat, in that order; what the energy and the food paid is fixed as fat in the same step; what cannot be paid was dropped up to e041 and kills the body under strict" font-size="12" fill="currentColor" stroke="currentColor">
  <defs>
    <marker id="ar" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="currentColor" stroke="none"/></marker>
    <marker id="ar1" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="var(--s1)" stroke="none"/></marker>
  </defs>
  <g fill="none" stroke-width="1.2">
    <rect x="20" y="30" width="170" height="40" rx="6"/>
    <rect x="20" y="100" width="170" height="40" rx="6"/>
    <rect x="20" y="170" width="170" height="40" rx="6"/>
    <rect x="320" y="100" width="190" height="40" rx="6"/>
    <rect x="620" y="36" width="262" height="62" rx="6"/>
  </g>
  <rect x="620" y="146" width="262" height="48" rx="6" fill="none" stroke="var(--s1)" stroke-width="2"/>
  <g fill="none" stroke-width="1.3" marker-end="url(#ar)">
    <path d="M190,50 L316,109"/>
    <path d="M190,120 L316,120"/>
    <path d="M190,190 L316,131"/>
    <path d="M415,140 V252 H105 V214"/>
    <path d="M510,120 H590 V67 H616"/>
  </g>
  <path d="M590,120 V170 H616" fill="none" stroke="var(--s1)" stroke-width="2" marker-end="url(#ar1)"/>
  <g stroke="none">
    <text x="105" y="55" text-anchor="middle">energy</text>
    <text x="105" y="125" text-anchor="middle">food eaten this step</text>
    <text x="105" y="195" text-anchor="middle">fat (the store, e030)</text>
    <text x="415" y="117" text-anchor="middle">upkeep owed</text>
    <text x="415" y="132" text-anchor="middle" font-size="11">0.002 a block + 0.032 a step</text>
    <text x="262" y="68" font-size="11">first</text>
    <text x="250" y="112" font-size="11">then</text>
    <text x="262" y="182" font-size="11">then</text>
    <text x="522" y="110" font-size="11">not paid</text>
    <text x="632" y="56">e030-e041: dropped</text>
    <text x="632" y="72" font-size="11">the fat was just refilled from the food,</text>
    <text x="632" y="87" font-size="11">so a body that ate anything lives on</text>
    <text x="632" y="166" fill="var(--s1)" font-weight="600">strict (e042): the body dies</text>
    <text x="632" y="182" font-size="11">at the end of the step, of hunger</text>
    <text x="260" y="270" text-anchor="middle" font-size="11">flesh 1: what the energy and the food paid is fixed as fat, in the same step</text>
    <text x="20" y="302" font-size="11">Moving: up to e041 paid from the energy only, so free at zero energy; under strict from the energy, then the fat, or the body dies.</text>
  </g>
</svg>
<figcaption>Figure 1. The ledger of one body in one step. The upkeep is paid from the energy, then from this step's food, then from the fat. What the energy and the food paid is fixed as fat at once (the flesh law, e024), so the death test - energy at zero and no fat - fails for any body that ate. Nothing else moves: the season, the water and the store's cap are e041's.</figcaption>
</figure>
"""


TEXT = {}  # filled in main(); counted at the end


def main():
    logs = {label: load_csv(f"results/{r}_log.csv", folder) for label, (folder, r, _) in RUNS.items() if exists(folder, r)}
    fines = {label: fine(r, folder, STEPS) for label, (folder, r, _) in RUNS.items() if label in logs}
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

    charts_gap = [
        line_chart("What the control forgave", "Share of the upkeep owed that was not paid, mean over each 10,000 steps. Under strict it is only the last step of a body that dies.",
                   xs, series("unpaid"), ymin=0, percent=True),
        line_chart("Bodies at zero energy", "Share of the bodies whose energy is at zero, living on their fat, every 1,000 steps. Without the store no body lives at zero energy.",
                   fx, fine_series("on_fat"), ymin=0, ymax=1, percent=True),
    ]
    def computed(fn, labels=None):
        return [(label, pad(fn(logs[label]), len(xs)), slot[label]) for label in (labels or RUNS) if label in logs]

    four_decimals = lambda y, _p: f"{y:.4f}".rstrip("0").rstrip(".") if y else "0"
    charts_world = [
        line_chart("Bodies", "Bodies alive every 1,000 steps. The dips are the winters; the gap between a control and its strict run is the bodies the forgiveness fed.",
                   fx, fine_series("pop"), ymin=0),
        line_chart("Body size", "The median body in cells, every 10,000 steps. A rise under strict is the smallest bodies thinning out.",
                   xs, series("size_p50"), ymin=0),
    ]
    charts_bodies = [
        line_chart("The sitters' share", "Share of the bodies in lineages whose mean body has under one muscle block, every 1,000 steps.",
                   fx2, sitters, ymin=0, ymax=1, percent=True),
        line_chart("The work of moving", "What a body owed for moving per step, paid or not, mean over each 10,000 steps. In the control about half of it was never paid.",
                   xs, computed(lambda d: [a + b for a, b in zip(d["move_spent"], d["move_free"])]), ymin=0, fmt=four_decimals),
    ]
    charts_move = [
        line_chart("Flesh in the diet", "Share of what the bodies eat that is flesh (the dead and broken cells), mean over each 10,000 steps. Without the store the world lives on its dead.",
                   xs, computed(lambda d: [m / (m + p) if m + p > 0 else float("nan") for m, p in zip(d["meat_intake"], d["plant_intake"])]), ymin=0, ymax=1, percent=True),
    ]

    def summary_row(label, lo=STEPS // 2, hi=STEPS):
        d, f = logs[label], fines[label]
        folder, r, _ = RUNS[label]
        w = floors(f)
        half = [i for i, t in enumerate(d["step"]) if lo < t <= hi]
        fhalf = [i for i, t in enumerate(f["step"]) if lo < t <= hi]
        mean = lambda k: sum(d[k][i] for i in half) / len(half)
        fmean = lambda k: sum(f[k][i] for i in fhalf) / len(fhalf)
        div, wins = diversity(r, folder)
        _, sh = sitter_share(r, folder)
        return (f"<tr><td>{label}</td><td>{min(x['pop'] for x in w):,}-{max(x['pop'] for x in w):,}</td><td>{fmean('pop'):,.0f}</td>"
                f"<td>{(mean('plant_intake') + mean('meat_intake')) / LOG:,.0f}</td><td>{fmean('on_fat'):.0%}</td>"
                f"<td>{mean('deaths_energy') / LOG:.2f}</td><td>{mean('unpaid'):.1%}</td>"
                f"<td>{mean('size_p50'):.1f}</td><td>{mean('muscle_mean'):.2f}</td><td>{mean('move_spent'):.5f}</td>"
                f"<td>{sh[-1]:.0%}</td><td>{f['lineages'][-1]}</td><td>{div} of {len(wins)}</td></tr>")

    rows = "".join(summary_row(label) for label in RUNS if label in logs)
    tables = data_table(["step", "pop", "births", "deaths_energy", "deaths_age", "deaths_broken", "plant_intake", "meat_intake", "on_fat", "fat_spent", "short", "unpaid", "move_free", "move_spent", "size_p50", "size_p90", "muscle_mean", "speed_mean", "lineages"],
                        {label: d for label, d in logs.items()})
    TEXT.update(TEXTS)
    TEXT["gallery"] = gallery(GALLERY, GALLERY_CAPTION) if GALLERY else ""
    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>e042 A body pays what it owes - Report</title>
<style>{CSS}</style>
</head>
<body>
<main>
<h1>e042: A body pays what it owes</h1>
<p class="sub">Experiment report - 2026-09-10 - the upkeep a body cannot pay is no longer dropped (#46): the control and <code>strict</code> on seeds 9 and 10, and <code>strict</code> without the store on seed 9. Answer: {TEXT["sub_answer"]}</p>

<section class="tldr">
<h2>TL;DR</h2>
<p>{TEXT["tldr"]}</p>
</section>

<h2>1. Question</h2>
<p>{TEXT["question"]}</p>
<ol>
  <li><strong>The world stands, smaller:</strong> the bodies and the winter floors fall by about the unpaid share of the upkeep, and fewer bodies sit at zero energy.</li>
  <li><strong>The bodies get smaller:</strong> the gap paid most to big bodies that ate a fraction of their upkeep.</li>
  <li><strong>The store is still worth keeping:</strong> under strict, a store holds higher winter floors than no store.</li>
</ol>

<h2>2. The law</h2>
<p>{TEXT["world"]}</p>
{DIAGRAM}
<p><strong>Runs.</strong> {TEXT["runs"]}</p>
<ul class="measures">
  <li><strong>bodies and floors</strong> - bodies alive every 1,000 steps and the five winter troughs.</li>
  <li><strong>zero energy</strong> - the share of bodies whose energy is at zero, living on their fat.</li>
  <li><strong>starvation deaths, flesh</strong> - deaths of hunger per step, and the share of what is eaten that is the dead.</li>
  <li><strong>unpaid</strong> - the share of the upkeep owed that was not paid (new; counted in every run).</li>
  <li><strong>size, muscle, moving</strong> - the median body in cells, the mean muscle blocks, what a body pays for moving a step and what it owed, paid or not.</li>
  <li><strong>sitters, lineages, diversity</strong> - the bodies in lineages with under one muscle block, the lineages alive, and the diversity number (#42).</li>
</ul>

<h2>3. Results</h2>
<div class="tw"><table>
<thead><tr><th>run</th><th>winter floors</th><th>bodies</th><th>eaten a step</th><th>at zero energy</th><th>starvation deaths a step</th><th>upkeep unpaid</th><th>median size</th><th>muscle</th><th>move cost a body</th><th>sitters at the end</th><th>lineages</th><th>diversity (#42)</th></tr></thead>
<tbody>{rows}</tbody></table></div>
<ol class="verdicts">
{TEXT["verdicts"]}
</ol>

<h3>3.1 {TEXT["h_gap"]}</h3>
<div class="grid2">
{"".join(charts_gap)}
</div>
<p>{TEXT["p_gap"]}</p>

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

<h3>3.4 {TEXT["h_move"]}</h3>
<div class="grid2">
{"".join(charts_move)}
</div>
<p>{TEXT["p_move"]}</p>
{TEXT["gallery"]}

<h2>4. Discussion</h2>
{TEXT["discussion"]}

<h2>5. Conclusion and next step</h2>
<p>{TEXT["conclusion"]}</p>

<h2>Appendix: data</h2>
<p>Every log step (10,000 steps) of the five runs; the full data are in <code>results/*.csv</code>. Build this report with <code>uv run python experiments/e042_strict/report.py</code>.</p>
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
    ("control, seed 9", HERE, run(0, 5, 9), 1, "the wide bar", "A row of gut cells across the front, no muscle: the control's top lineage, 53% of the last third. It eats what falls at its feet."),
    ("control, seed 10", HERE, run(0, 5, 10), 3, "the other control's sitter", "A wedge of gut cells, no muscle: 49% of the last third."),
    ("strict, seed 9", HERE, run(1, 5, 9), 465, "the mover on top", "Muscle at the front, gut behind, a full 4x4 grid; 44% flesh. The top lineage under strict, 47% of the last third."),
    ("strict, seed 9", HERE, run(1, 5, 9), 118, "the sitter that stays", "A few gut cells, no muscle, light (mass 5): the second winner, 42%. A small gut that pays its upkeep where it sits."),
    ("strict, seed 10", HERE, run(1, 5, 10), 178, "the other seed's mover", "Muscle around a core of gut, 44% flesh: 51% of the last third. Strict puts a mover on top in both seeds."),
    ("strict, seed 10", HERE, run(1, 5, 10), 90, "and its sitter", "A block of gut cells, no muscle: 45% of the last third."),
    ("strict, no store, seed 9", HERE, run(1, 0, 9), 1172, "the gut that eats the dead", "A hollow U of gut cells, no muscle, 57% flesh: without the store the fat is never spent, and the world's food is its dead."),
]
GALLERY_CAPTION = "The most common grown body of each lineage at its peak, on the grid it grew on, front up (blue hard, orange muscle, yellow sensor, aqua gut). Under strict the top lineage is a mover in both seeds, and a sitting gut is second."

TEXTS = {
    "sub_answer": "the world stands. Paying in full leaves 20-35% fewer bodies on the same food, bigger and with more muscle, and a mover as the top lineage in both seeds.",
    "tldr": ("Up to e041 a body that could not pay its upkeep lived on if it ate anything: in the control 6-18% of the upkeep owed went unpaid "
             "and half the moving was free. Under strict, where a body that cannot pay dies, the world stands on both seeds with 20-35% fewer "
             "bodies on the same food. The median body grows from 5-9 cells to 10-12, muscle rises, and a mover replaces the sitter on top. "
             "Kept: strict from here."),
    "question": ("The viewer showed a body of 36 blocks sitting at zero energy for 454 steps, owing three times what it ate. Since e030 the upkeep "
                 "a body cannot pay from its energy, its food and its fat is dropped, and the food just eaten is fixed as fat, so the body passes "
                 "the death test. e030 kept the store partly on this gap, and every experiment since stands on it. What of the world was the "
                 "store, and what was the gap?"),
    "world": ("Under strict (argument 38) a body that cannot pay its upkeep in full - from its energy, this step's food and its fat - dies of "
              "hunger at the end of the step. The work of moving is paid from the energy, then the fat, on the same terms. strict 0 is e041 "
              "byte for byte."),
    "runs": ("e041's season world, 100,000 steps (five winters), five runs at once, 28 minutes: the control and strict on seeds 9 and 10, and "
             "strict without the store (store 0: the fat is never spent) on seed 9. Means over the second half; the floors are the five winter "
             "troughs."),
    "verdicts": ("<li><span class=\"verdict\">Yes</span> it stands on both seeds with 35% and 20% fewer bodies and floors 13% and 20% lower; "
                 "zero energy falls from 57% and 54% to 43% and 46%.</li>"
                 "<li><span class=\"verdict no\">No</span> the opposite: the median body grows from 9.0 to 12.4 cells on seed 9 and from 5.2 "
                 "to 10.0 on seed 10.</li>"
                 "<li><span class=\"verdict no\">No</span> without the store the floors are as high (623-684 against 549-698) and the bodies "
                 "more (2,943 against 2,020).</li>"),
    "h_gap": "The control forgave 6-18% of the upkeep, and half the moving",
    "p_gap": ("Over the second half 18% (seed 9) and 6% (seed 10) of the upkeep owed went unpaid, and up to 35% early in the run. Of the work "
              "of moving, 43% and 53% was never paid: a body at zero energy, half the world at any time, moved for nothing. Under strict nearly "
              "half the bodies still live at zero energy, on a fat that now pays in full."),
    "h_world": "The world stands with fewer, bigger bodies",
    "p_world": ("Both strict worlds eat what their controls eat (109 and 115 a step against 116 and 106) with 20-35% fewer bodies. The median "
                "body grows by 3.4 and 4.8 cells as the smallest thin out; on seed 9 the largest go too (the 90th percentile 21.8 to 16.0 "
                "cells). The same food feeds fewer bodies of 10-16 cells that move more."),
    "h_bodies": "A mover takes the top",
    "p_bodies": ("In both controls the top lineage of the last third is a gut with no muscle (53% and 49% of the body-steps). Under strict it is "
                 "a body with 6-7 muscle blocks that eats 44% flesh (47% and 51%), beside a sitting gut of 6-8 cells. The work of moving, paid "
                 "or not, rises 1.6 and 1.7 times, and the mean muscle from 3.1 and 1.5 to 4.3 and 3.0."),
    "h_move": "Without the store the world eats its dead",
    "p_move": ("With store 0 the fat is never spent, so the upkeep a body pays is fixed in its flesh and none of it is breathed. Under strict that "
               "world stands as well as the store's (floors 623-684) with more and bigger bodies (2,943, median 16 cells), and eats 251 a step, "
               "68% of it flesh, against 109 and 36%."),
    "discussion": ("<p>The gap paid most to a body that ate less than it owed and did not move: it lived as long as it ate anything. Take it "
                   "away and what the world eats does not change, but who eats it does - fewer bodies, bigger, with more muscle, and a mover on "
                   "top. #43 and #37 looked for this in the environment; part of what made sitting free was the ledger.</p>"
                   "<p>The store's case changes. e030 kept it for the winter on flat ground, where a body without one died in the first dark "
                   "weeks. Under e032's winter by height the valley is the refuge, and without the forgiveness the store does not show in the "
                   "floors (one seed). What it decides is where the matter cycles - through the air, or through the dead - and how big the "
                   "bodies are.</p>"
                   "<p>What this does not show: two seeds, 100,000 steps, and e037 found a pilot's winner that was the start's transient. No "
                   "batch was run: keeping strict does not depend on who wins, because it fixes a ledger that e030 already described as strict. "
                   "The next experiment's control runs under it and shows whether the mover's lead lasts.</p>"),
    "conclusion": ("Kept: the season world is strict 1 from here (the next experiment's default; strict 0 stays as e041). The store stays at 5. "
                   "Every result from e030 to e041 about bodies at zero energy - the winter floors, the sitter, \"size does not pay\" - was "
                   "measured with 6-18% of the upkeep forgiven. Next: #45, the canopy's fall and its saturation unbundled, under strict; then "
                   "#47, ageing."),
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
    else:
        main()
