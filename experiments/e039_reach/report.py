#!/usr/bin/env python3
"""Build report.html for this experiment.

Charts: matplotlib, exported as SVG and inlined. Diagram: hand-written SVG.
Run from the repo root: uv run python experiments/e039_reach/report.py
"""
import csv
import html
import statistics
import io
import json
import math
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
SIDE_MAX = 16

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

BASE = "128_sigma0_r64_f0_flat_eyes8_flesh1_w1_season2_digest0_sidegrow_store5_yolk0_breed0_winterhigh_water0.1_leach0.01_depth0.01_mix0.2"


def run(reach=None, seed=9):
    return f"{BASE}{'' if reach is None else f'_reach{reach}'}_seed{seed}"


# The pilots on seed 9 in e038's season world (water 0.1, leach 0.01, depth 0.01, mix 0.2, flow 0,
# winter high 2, store 5, grow, rain flat, no ground store, k 1, sun 1): label -> (folder, run
# prefix, color slot). `reach` 0 is e038 byte for byte, the control.
RUNS = {
    "reach 0 (today)": (HERE, run(), 5),
    "reach 0.5": (HERE, run(0.5), 0),
    "reach 1": (HERE, run(1), 1),
    "reach 2": (HERE, run(2), 2),
}
SEEDS = [1, 2, 3]
E035 = os.path.join(HERE, "..", "e035_water")  # the control on seeds 1-3, 300,000 steps: e035's batch is this world, byte for byte
KNOCK = {  # the knockout (e009's rule): the same reach for every body, no gradient
    "reach 1": (HERE, lambda seed: run(1, seed)),
    "fix 1": (HERE, lambda seed: f"{BASE}_reachfix1_seed{seed}"),
}
STEPS = 100_000
SEASON = 20_000
CELLS = 128 * 128
BAND = ["valley", "slope", "ridge"]
LINEAGE_PALETTE = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#7b61ff", "#00a3c4", "#c94c4c", "#6aa84f", "#b8860b", "#8e44ad", "#e67e22"]

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



def lineage_stats(run, folder=HERE):
    """Per lineage: first and last step seen as a group, max size."""
    first, last, size = {}, {}, defaultdict(int)
    for r in load_rows(f"results/{run}_lineages.csv", folder):
        i, t = int(r["lineage"]), int(r["step"])
        first.setdefault(i, t)
        last[i] = t
        size[i] = max(size[i], int(r["size"]))
    return first, last, size


def control_run(seed):
    """The control: seed 9 is this experiment's `reach` 0 run, seeds 1-3 are e035's batch (the same code)."""
    return (HERE, run()) if seed == 9 else (E035, f"{BASE}_seed{seed}")


def window_mean(folder, name, keys, lo=50_000, hi=100_000):
    """The mean of each key over the log steps in the window, or None if the run has not reached it."""
    d = load_csv(f"results/{name}_log.csv", folder)
    sel = [i for i, t in enumerate(d["step"]) if lo <= t <= hi]
    if not sel or max(d["step"]) < hi:
        return None
    return {k: sum(d[k][i] for i in sel) / len(sel) for k in keys if k in d}


# ---------- the diversity number (#42) ----------
# The measure of a law (principles 7): how many different bodies prosper at once, and in how many
# places. One number, the same in every experiment from e039 on, beside the lineage count.
#
# The winners of a window are the lineages holding at least WIN_SHARE of its body-steps. Two
# winners are the same body when their sizes are within SIZE_FACTOR and the mixes of their blocks
# (each kind's count over the size) differ by at most MIX_DIST in sum; the winners are grouped by
# single linkage on that relation (e006's rule for lineages, applied to shapes) and the number of
# groups is the diversity. Counted for the whole world and per height band. The block counts a
# lineage logs are its mean over the world, so a lineage with a different body on each place
# (e012) counts once: this number is a floor.
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
    groups = []  # single linkage on same_body
    for i in win:
        hit = [g for g in groups if any(same_body(mean[i], mean[j]) for j in g)]
        if hit:
            merged = [i] + [j for g in hit for j in g]
            groups = [g for g in groups if g not in hit] + [merged]
        else:
            groups.append([i])
    return len(groups), [(i, total[i] / body_steps, sum(mean[i]), mean[i]) for i in win]


def winners(by, first_step=250_000):
    """The top lineage at each lineages.csv step from `first_step`: the distinct winners, the longest hold in steps, the holds."""
    top = {}
    for rows in by.values():
        for row in rows:
            t = int(row["step"])
            if t < first_step:
                continue
            n = int(row["size"])
            if n > top.get(t, (0, None))[0]:
                top[t] = (n, int(row["lineage"]))
    steps = sorted(top)
    if not steps:
        return 0, 0, []
    seq = [top[t][1] for t in steps]
    holds, cur, start = [], seq[0], steps[0]
    for t, l in zip(steps, seq):
        if l != cur:
            holds.append((cur, start, t))
            cur, start = l, t
    holds.append((cur, start, steps[-1] + 1000))
    return len(set(seq)), max(b - a for _, a, b in holds), holds


def median(x):
    x = sorted(v for v in x if v == v)
    return x[len(x) // 2] if x else float("nan")


def exists(folder, run):
    """A run whose log has rows (a run still writing keeps its log empty until its buffer flushes)."""
    path = os.path.join(folder, f"results/{run}_log.csv")
    return os.path.exists(path) and os.path.getsize(path) > 200


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


def line_chart(title, subtitle, xs, series, ymin=None, ymax=None, percent=False, xlabel="step", bands=None):
    """series: list of (label, ys, slot). bands: list of (lo, hi, slot) shaded around a series."""
    fig, ax = new_axes(xlabel)
    for lo, hi, slot in bands or []:
        ax.fill_between(xs, lo, hi, color=SERIES[slot], alpha=0.15, linewidth=0)
    for label, ys, slot in series:
        ax.plot(xs, ys, color=SERIES[slot], linewidth=1.6, label=label)
    top = max((v for _, ys, _ in series for v in ys if v == v), default=1.0)
    if ymin is not None:
        ax.set_ylim(ymin, ymax if ymax is not None else top * 1.12)
    ax.yaxis.set_major_formatter((lambda y, _p: f"{y:.0%}") if percent else kfmt)
    ax.yaxis.set_major_locator(MaxNLocator(4))
    legend_above(ax, min(len(series), 4))
    return figure(title, subtitle, to_svg(fig))


def hist_chart(title, subtitle, series, bins, xlabel):
    """series: list of (label, values, weights, slot)."""
    fig, ax = new_axes(xlabel)
    ax.margins(x=0.02)
    for label, values, weights, slot in series:
        ax.hist(values, bins=bins, weights=weights, color=SERIES[slot], alpha=0.7, label=label, edgecolor="none")
    ax.yaxis.set_major_locator(MaxNLocator(4))
    ax.yaxis.set_major_formatter(kfmt)
    legend_above(ax, len(series))
    return figure(title, subtitle, to_svg(fig))


def scatter_chart(title, subtitle, series, xlabel, ylabel):
    """series: list of (label, xs, ys, sizes, slot)."""
    fig, ax = new_axes(xlabel)
    ax.margins(x=0.05)
    ax.set_ylabel(ylabel)
    for label, xs, ys, sizes, slot in series:
        ax.scatter(xs, ys, s=sizes, color=SERIES[slot], alpha=0.6, label=label, linewidths=0, rasterized=True)
    ax.yaxis.set_major_locator(MaxNLocator(4))
    legend_above(ax, len(series))
    return figure(title, subtitle, to_svg(fig))


def timeline_chart(title, subtitle, by, color_key="side", lo=4, hi=16):
    """Every lineage as a band: bodies over time, colored by the lineage's side (dark: small grid, yellow: large)."""
    fig, ax = new_axes(size=(13, 3.2))
    ax.set_ylabel("bodies in the lineage")
    cmap = matplotlib.colormaps["viridis"]
    for lid, rows in by.items():
        if max(int(r["size"]) for r in rows) < 20:
            continue
        xs = [int(r["step"]) for r in rows]
        ys = [int(r["size"]) for r in rows]
        d = median(float(r[color_key]) for r in rows)
        c = cmap((d - lo) / (hi - lo))
        ax.fill_between(xs, 0, ys, color=c, alpha=0.35, linewidth=0, rasterized=True)
        ax.plot(xs, ys, color=c, linewidth=0.9, rasterized=True)
    ax.set_ylim(0, None)
    ax.yaxis.set_major_locator(MaxNLocator(4))
    ax.yaxis.set_major_formatter(kfmt)
    sm = matplotlib.cm.ScalarMappable(cmap=cmap, norm=matplotlib.colors.Normalize(lo, hi))
    cb = fig.colorbar(sm, ax=ax, pad=0.01, fraction=0.03)
    cb.set_label("side")
    cb.outline.set_visible(False)
    cb.ax.tick_params(colors=INK)
    return figure(title, subtitle, to_svg(fig))


def figure(title, subtitle, svg):
    return f"""
<figure class="fig">
  <figcaption><strong>{html.escape(title)}</strong><span>{html.escape(subtitle)}</span></figcaption>
  {svg}
</figure>"""


def data_table(cols, rows_by_name, every=10):
    """Collapsed tables for the appendix. rows_by_name: {name: {col: [values]}}."""
    out = []
    for name, d in rows_by_name.items():
        cols = [c for c in cols if c in d]
        rows = "".join(
            "<tr>" + "".join(f"<td>{d[c][i]:g}</td>" for c in cols) + "</tr>"
            for i in range(0, len(d[cols[0]]), every)
        )
        out.append(f"<details><summary>{html.escape(name)}</summary><div class='tw'><table><thead><tr>"
                   + "".join(f"<th>{c}</th>" for c in cols) + f"</tr></thead><tbody>{rows}</tbody></table></div></details>")
    return "\n".join(out)


def gallery(picks, caption):
    """picks: [(label, folder, run, lineage id, name, what the shape does[, step])]. The most common body of each lineage at its
    peak (or at the step given), on the grid it grew on (side by side cells, drawn at the same width whatever the side), front up."""
    cards = []
    cache = {}
    for label, folder, run, lid, name, what, *rest in picks:
        at = rest[:1]  # the step to draw at, if given
        pick = rest[1] if len(rest) > 1 else None  # a predicate on the cells, to draw a kind of body a varied lineage holds
        if run not in cache:
            cache[run] = (lineage_rows(run, folder), load_bodies(run, folder), list(read_frames(f"results/{run}_long.jsonl", folder)))
        by, bodies, frames = cache[run]
        rows = by[lid]
        peak = max(rows, key=lambda r: int(r["size"])) if not at else min(rows, key=lambda r: abs(int(r["step"]) - at[0]))
        span = int(rows[-1]["step"]) - int(rows[0]["step"]) + CONFIRM_STEPS
        frame = min((fr for fr in frames if any(a[4] == lid for a in fr["agents"])), key=lambda fr: abs(fr["step"] - int(peak["step"])))
        # The most common body among the grown ones (at least three quarters of the lineage's
        # mean cells at its peak): a lineage in bloom is mostly newborns of one or two cells.
        grown = 0.75 * sum(float(peak[k]) for k in ("hard", "muscle", "sensor", "digestive"))
        ids = [a[2] for a in frame["agents"] if a[4] == lid]
        c = Counter(i for i in ids if sum(ch != "0" for ch in bodies[i][1]) >= grown and (pick is None or pick(bodies[i][1]))) or Counter(ids)
        side, cells = bodies[c.most_common(1)[0][0]]
        u = 88 / side
        rects = "".join(f'<rect x="{(i % side) * u:.2f}" y="{(i // side) * u:.2f}" width="{u * 0.9:.2f}" height="{u * 0.9:.2f}" fill="{KIND_COLOR[int(k)]}"/>' for i, k in enumerate(cells) if k != "0")
        m, pl = float(peak["meat"]), float(peak["plant"])
        meat = m / (m + pl) if m + pl > 0 else 0
        cards.append(f"""<figure class="card"><svg viewBox="-1 -1 89 89" width="120" height="120" role="img" aria-label="{html.escape(name)}"><rect x="-1" y="-1" width="89" height="89" fill="var(--cell)"/>{rects}<line x1="-1" y1="-0.5" x2="88" y2="-0.5" stroke="var(--ink2)" stroke-width="1.5" stroke-dasharray="3 2"/></svg>
<figcaption><strong>{html.escape(name)}</strong><br>{html.escape(label)}, lineage {lid}: {span:,} steps, {int(peak["size"]):,} agents at {"step " + format(int(peak["step"]), ",") if at else "its peak"}<br>side {float(peak["side"]):.0f} (grid {side}x{side}), density {float(peak["density"]):.2f}; mass {float(peak["mass"]):.0f} on {float(peak["foot"]):.1f} cells, {float(peak["len_fwd"]):.1f} long: hard {float(peak["hard"]):.0f}, muscle {float(peak["muscle"]):.0f}, sensor {float(peak["sensor"]):.1f}, digestive {float(peak["digestive"]):.0f}; flesh {meat:.0%} of the intake<br>{html.escape(what)}</figcaption></figure>""")
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
<svg viewBox="0 0 900 282" width="100%" role="img" aria-label="A column of plant matter, a short mouth and a long one" font-size="12" fill="currentColor" stroke="currentColor">
  <text x="40" y="26" font-size="11" stroke="none">A cell's standing plant is a column, and 1 of matter stands 1 cell tall (the canopy's reading since e021). The trees stand at 4 on average, the lawn at 0.04.</text>
  <g stroke-width="1.2" fill="none"><path d="M40,190 L860,190"/></g>
  <g fill="#1baf7a" stroke="none" opacity="0.85"><rect x="300" y="90" width="46" height="100"/><rect x="740" y="90" width="46" height="100"/></g>
  <g fill="#1baf7a" stroke="none" opacity="0.3"><rect x="60" y="184" width="180" height="6"/><rect x="500" y="184" width="180" height="6"/></g>
  <g fill="var(--s1)" stroke="none">
    <rect x="252" y="165" width="24" height="24"/>
    <rect x="616" y="165" width="24" height="24"/><rect x="641" y="165" width="24" height="24"/><rect x="666" y="165" width="24" height="24"/><rect x="691" y="165" width="24" height="24"/>
  </g>
  <g fill="none" stroke-width="1.4" stroke-dasharray="4 3"><path d="M246,165 L362,165"/><path d="M610,90 L802,90"/></g>
  <g stroke="none" font-size="11">
    <text x="60" y="152">a short body,</text><text x="60" y="168">4 sub-cells long</text>
    <text x="368" y="169">its reach: 1 of the column's 4</text>
    <text x="500" y="152">a long body, 16 sub-cells long</text>
    <text x="808" y="94">its reach: 4</text>
    <text x="60" y="218">a quarter of its bite comes off this column:</text><text x="60" y="234">0.005 a step per gut block</text>
    <text x="500" y="218">the whole bite: 0.02 a step per gut block</text>
    <text x="500" y="234">- four times the income on the same food</text>
  </g>
  <g stroke="none" font-size="10" opacity="0.85">
    <text x="60" y="258">The lawn under both (0.04 standing) is within every reach; the fruit and the dead lie on the ground and both take those whole.</text>
    <text x="60" y="274">What stands above a mouth's reach shades its neighbours and spills its growth as fruit, as since e021.</text>
  </g>
</svg>
<figcaption>Figure 1. The law. A gut block's bite from the standing plant is its bite times min(1, reach / height of the column); a body's reach is `reach` cells per world cell of its length front to back (4 sub-cells to a world cell). Nothing else moves: the bite, the upkeep, the weight, the canopy and the spill are e038's. The runs are reach 0 (nothing out of reach, e038 byte for byte), 0.5, 1 and 2, and a knockout that gives every body the same reach.</figcaption>
</figure>
"""


TEXT = {}  # filled in main(); counted at the end


def agents_at(run, step, folder=HERE):
    return [r for r in load_rows(f"results/{run}_agents.csv", folder) if int(r["step"]) == step]


def fine(run, folder, last_step, lineage_only=False):
    """Every 1,000 steps: the bodies alive (pop.csv from e031; the lineage log's sums for e030's control), lineages of 5 or more, and (pop.csv) the share on their fat, the fat and the mean age."""
    by = lineage_rows(run, folder)
    lin, lsum = Counter(), Counter()
    for rows in by.values():
        for r in rows:
            t = int(r["step"])
            if t <= last_step:
                lin[t] += 1
                lsum[t] += int(r["size"])
    path = os.path.join(folder, f"results/{run}_pop.csv")
    if os.path.exists(path) and not lineage_only:
        d = load_csv(f"results/{run}_pop.csv", folder)
        keep = [i for i, t in enumerate(d["step"]) if t <= last_step]
        out = {k: [v[i] for i in keep] for k, v in d.items()}
    else:
        steps = sorted(lsum)
        out = {"step": [float(t) for t in steps], "pop": [float(lsum[t]) for t in steps]}
    out["lineages"] = [lin[int(t)] for t in out["step"]]
    return out


def winters(f, first=0):
    """Per cycle of the season from `first`: (trough step, bodies at the trough, lineages at the trough, peak bodies)."""
    out = []
    n = int(max(f["step"])) // SEASON
    for c in range(first, n):
        idx = [i for i, t in enumerate(f["step"]) if c * SEASON < t <= (c + 1) * SEASON]
        if not idx:
            continue
        lo = min(idx, key=lambda i: f["pop"][i])
        hi = max(idx, key=lambda i: f["pop"][i])
        out.append((int(f["step"][lo]), int(f["pop"][lo]), f["lineages"][lo], int(f["pop"][hi])))
    return out


def band_share(f, b):
    return [f[f"pop{b}"][i] / f["pop"][i] if f["pop"][i] > 0 else float("nan") for i in range(len(f["step"]))]


def cross_share(f, b):
    return [f[f"cross{b}"][i] / f[f"pop{b}"][i] if f[f"pop{b}"][i] > 0 else float("nan") for i in range(len(f["step"]))]


def floor_rows(f, first=0):
    """Per winter from `first`: (trough step, bodies, lineages, valley share of the bodies, ridge bodies, share of the ridge's bodies born elsewhere, peak bodies, ridge share at the peak)."""
    out = []
    n = int(max(f["step"])) // SEASON
    for c in range(first, n):
        idx = [i for i, t in enumerate(f["step"]) if c * SEASON < t <= (c + 1) * SEASON]
        if not idx:
            continue
        lo = min(idx, key=lambda i: f["pop"][i])
        hi = max(idx, key=lambda i: f["pop"][i])
        has = "pop0" in f
        out.append(dict(step=int(f["step"][lo]), pop=int(f["pop"][lo]), lin=f["lineages"][lo],
                        valley=f["pop0"][lo] / max(f["pop"][lo], 1) if has else float("nan"),
                        ridge=int(f["pop2"][lo]) if has else 0,
                        ridge_cross=f["cross2"][lo] / max(f["pop2"][lo], 1) if has else float("nan"),
                        peak=int(f["pop"][hi]), peak_ridge=f["pop2"][hi] / max(f["pop"][hi], 1) if has else float("nan")))
    return out


def floors(f):
    """Per season window: the trough and the peak, with the valley's share at the trough."""
    out = []
    n = int(max(f["step"])) // SEASON
    for c in range(n):
        idx = [i for i, t in enumerate(f["step"]) if c * SEASON < t <= (c + 1) * SEASON]
        if not idx:
            continue
        lo = min(idx, key=lambda i: f["pop"][i])
        hi = max(idx, key=lambda i: f["pop"][i])
        out.append(dict(step=int(f["step"][lo]), pop=int(f["pop"][lo]), lin=f["lineages"][lo],
                        valley=f["pop0"][lo] / max(f["pop"][lo], 1), peak=int(f["pop"][hi])))
    return out


def sizes_at_end(run, folder=HERE):
    """The living cells of every body at the last dump (agents.csv)."""
    rows = load_rows(f"results/{run}_agents.csv", folder)
    last = max(int(r["step"]) for r in rows)
    return [int(r["size"]) for r in rows if int(r["step"]) == last]


def main():
    logs = {label: load_csv(f"results/{run}_log.csv", folder) for label, (folder, run, _) in RUNS.items() if exists(folder, run)}
    fines = {label: fine(run, folder, STEPS) for label, (folder, run, _) in RUNS.items() if label in logs}
    sizes = {label: sizes_at_end(run, folder) for label, (folder, run, _) in RUNS.items() if label in logs}
    slot = {label: s for label, (_, _, s) in RUNS.items()}
    xs = max((d["step"] for d in logs.values()), key=len)
    fx = max((d["step"] for d in fines.values()), key=len)

    def pad(ys, n):
        return ys + [float("nan")] * (n - len(ys))

    def series(key, labels=None):
        return [(label, pad(list(logs[label][key]), len(xs)), slot[label]) for label in (labels or RUNS) if label in logs and key in logs[label]]

    def fine_fn(fn, need="pop", labels=None):
        return [(label, pad(fn(fines[label]), len(fx)), slot[label]) for label in (labels or RUNS) if label in fines and need in fines[label]]

    eaten = lambda d: [(d["plant_intake"][i] + d["meat_intake"][i]) / 10_000 for i in range(len(d["step"]))]
    charts_trees = [
        line_chart("What the trees pay out", "Intake from cells holding 1 or more of standing plant (tree_eaten), per step, mean over each 10,000 steps. The reach takes a share of every bite from a tall column, so a fall is the law working.",
                   xs, series("tree_eaten"), ymin=0),
        line_chart("The standing plant", "Matter standing in those cells (tree_res), every 10,000 steps. What the mouths cannot take grows: a rise is the matter locked above them.",
                   xs, series("tree_res"), ymin=0),
    ]
    charts_body = [
        line_chart("How long a body is", "len_fwd: the mean length front to back, in sub-cells (4 to a world cell), every 10,000 steps. This is what the law prices: at reach 1 a body of 4 reaches a column of height 1.",
                   xs, series("len_fwd"), ymin=0),
        line_chart("The median body", "Living cells of the median body, every 10,000 steps. Length and size are not the same thing: a body can grow long without growing large.",
                   xs, series("size_p50"), ymin=0),
        hist_chart("Sizes at the end", "Bodies by living cells at step 100,000, all bodies alive (agents.csv). The browser the law was meant to allow would be a tail to the right.",
                   [(label, sizes[label], None, slot[label]) for label in RUNS if label in sizes], bins=range(0, 41, 2), xlabel="living cells"),
    ]
    charts_world = [
        line_chart("Bodies", "Bodies alive every 1,000 steps (pop.csv). The dips are the winters; the floors are what the world can carry through one.",
                   fx, fine_fn(lambda f: list(f["pop"])), ymin=0),
        line_chart("What a gut block earns", "intake_per_gut: what one gut block takes per step, mean over each 10,000 steps (the points alternate summer and winter). The bite is 0.02; the crowd pins this at 0.003-0.005 (e038).",
                   xs, series("intake_per_gut"), ymin=0),
    ]

    def summary_row(label):
        d, f = logs[label], fines[label]
        folder, r, _ = RUNS[label]
        w = floors(f)
        half = [i for i, t in enumerate(d["step"]) if t >= STEPS // 2]
        mean = lambda k: sum(d[k][i] for i in half) / len(half) if k in d else float("nan")
        div, wins = diversity(r, folder)
        return (f"<tr><td>{label}</td><td>{min(x['pop'] for x in w):,}-{max(x['pop'] for x in w):,}</td><td>{mean('pop'):,.0f}</td>"
                f"<td>{mean('size_p10'):.0f} / {mean('size_p50'):.0f} / {mean('size_p90'):.0f}</td>"
                f"<td>{mean('len_fwd'):.2f}</td>"
                f"<td>{mean('tree_res'):,.0f} on {mean('trees'):.0f}</td><td>{mean('tree_eaten'):.1f}</td>"
                f"<td>{mean('intake_per_gut'):.4f}</td><td>{mean('biters_any_share'):.0%}</td>"
                f"<td>{f['lineages'][-1]}</td><td>{div} of {len(wins)}</td></tr>")

    rows = "".join(summary_row(label) for label in RUNS if label in logs)

    # The knockout (e009's rule): the same reach for every body. Per seed, the mean over steps
    # 50,000-100,000 of the mean body, its length and the bodies alive.
    def knock_rows():
        keys = ["size_mean", "len_fwd", "pop", "trees"]
        out = []
        for seed in [9] + SEEDS:
            cells = []
            for folder, name in [control_run(seed), (KNOCK["reach 1"][0], KNOCK["reach 1"][1](seed)), (KNOCK["fix 1"][0], KNOCK["fix 1"][1](seed))]:
                m = window_mean(folder, name, keys) if exists(folder, name) else None
                if m is None:
                    cells.append("<td>-</td><td>-</td><td>-</td>")
                    continue
                cells.append(f"<td>{m['size_mean']:.1f}</td><td>{m['len_fwd']:.2f}</td><td>{m['pop']:,.0f}</td>")
            out.append(f"<tr><td>seed {seed}</td>" + "".join(cells) + "</tr>")
        return "".join(out)

    # The batch: seeds 1-3 at 300,000 steps, reach 1 against the control (e035's runs of this world).
    def batch_rows():
        keys = ["size_mean", "size_p50", "size_p90", "len_fwd", "pop", "trees", "tree_res", "biters_any_share", "intake_per_gut", "lineages"]
        out = []
        for seed in SEEDS:
            for label, (folder, name) in [("control", control_run(seed)), ("reach 1", (HERE, run(1, seed)))]:
                m = window_mean(folder, name, keys, 150_000, 300_000) if exists(folder, name) else None
                if m is None:
                    continue
                f = fine(name, folder, 300_000)
                w = floors(f)
                div, wins = diversity(name, folder)
                out.append(f"<tr><td>seed {seed}, {label}</td><td>{', '.join(format(r['pop'], ',') for r in w[-5:])}</td>"
                           f"<td>{m['size_p50']:.0f} / {m['size_mean']:.1f} / {m['size_p90']:.0f}</td><td>{m['len_fwd']:.2f}</td>"
                           f"<td>{m['tree_res']:,.0f} on {m['trees']:.0f}</td><td>{m['intake_per_gut']:.4f}</td>"
                           f"<td>{m['biters_any_share']:.0%}</td><td>{f['lineages'][-1]}</td><td>{div} of {len(wins)}</td></tr>")
        return "".join(out)

    knock = knock_rows()
    batch = batch_rows()

    tables = data_table(["step", "pop", "births", "deaths_energy", "plant_intake", "meat_intake", "regrowth", "barren", "dry", "size_p10", "size_p50", "size_p90", "size_max", "mass_p10", "mass_p50", "mass_p90", "mass_max", "density_mean", "fat_stock", "biters_any_share", "trees", "lineages"],
                        {f"{label}, seed 9": d for label, d in logs.items()}, every=1)
    TEXT.update(TEXTS)
    TEXT["gallery"] = gallery(GALLERY, GALLERY_CAPTION)
    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>e039 A food only a big body reaches - Report</title>
<style>{CSS}</style>
</head>
<body>
<main>
<h1>e039: A food only a big body reaches</h1>
<p class="sub">Experiment report - 2026-09-09 - a bite that reaches only so far up a column (#41), at 0.5, 1 and 2 cells of height per world cell of a body's length, with a knockout and three seeds at 300,000 steps. Answer: the world grows longer bodies, not bigger ones.</p>

<section class="tldr">
<h2>TL;DR</h2>
<p>{TEXT["tldr"]}</p>
</section>

<h2>1. Question</h2>
<p>{TEXT["question"]}</p>
<ol>
  <li><strong>Size pays:</strong> the standing column is worth more to a long body than to a short one, so the bodies grow (median above 16 cells, 90th percentile above 25), the trees go to the longer mouths, and a browser holds beside the grazer - two winners.</li>
  <li><strong>Or the world only pays:</strong> the trees are 5% of the intake, so the reach may only lock that away - the trees grow past every mouth, the crowd lives on the fruit they spill, the bodies stay at 11-16 cells and the floors fall.</li>
</ol>

<h2>2. The law</h2>
<p>{TEXT["world"]}</p>
{DIAGRAM}
<p><strong>Runs.</strong> {TEXT["runs"]}</p>
<ul class="measures">
  <li><strong>a gut block's income</strong> - intake_per_gut: what one gut block takes per step, mean over 10,000 steps (log.csv); summer and winter alternate.</li>
  <li><strong>size</strong> - living cells of a body: the 10th, 50th and 90th percentiles and the largest, every 10,000 steps, and every body at the end (agents.csv).</li>
  <li><strong>soil</strong> - matter in the soil per cell: whether the regrowth, min(sun, soil), is bound by the soil.</li>
  <li><strong>bodies and floors</strong> - bodies alive every 1,000 steps (pop.csv), the winter troughs and the valley's share of them.</li>
  <li><strong>eaten, biters, lineages</strong> - what the world digests per step, the share of bodies with a tooth, lineages of five or more.</li>
</ul>

<h2>3. Results</h2>
<div class="tw"><table>
<thead><tr><th>Seed 9, 100,000 steps</th><th>winter floors</th><th>bodies</th><th>size p10 / p50 / p90</th><th>length</th><th>standing plant, on cells</th><th>trees pay</th><th>a gut block earns</th><th>biters</th><th>lineages</th><th>diversity (#42)</th></tr></thead>
<tbody>{rows}</tbody></table></div>
<ol class="verdicts">
{TEXT["verdicts"]}
</ol>

<h3>3.1 {TEXT["h_income"]}</h3>
<div class="grid2">
{"".join(charts_trees)}
</div>
<p>{TEXT["p_income"]}</p>

<h3>3.2 {TEXT["h_size"]}</h3>
<div class="grid2">
{"".join(charts_body)}
</div>
<p>{TEXT["p_size"]}</p>

<h3>3.3 {TEXT["h_world"]}</h3>
<div class="grid2">
{"".join(charts_world)}
</div>
<p>{TEXT["p_world"]}</p>

<h3>3.4 {TEXT["h_knock"]}</h3>
<div class="tw"><table>
<thead><tr><th>Steps 50,000-100,000</th><th>control: body</th><th>length</th><th>bodies</th><th>reach 1: body</th><th>length</th><th>bodies</th><th>fix 1: body</th><th>length</th><th>bodies</th></tr></thead>
<tbody>{knock}</tbody></table></div>
<p>{TEXT["p_knock"]}</p>

<h3>3.5 {TEXT["h_batch"]}</h3>
<div class="tw"><table>
<thead><tr><th>Seeds 1-3, 300,000 steps (means over the last half)</th><th>last five winter floors</th><th>size p50 / mean / p90</th><th>length</th><th>standing plant, on cells</th><th>a gut block earns</th><th>biters</th><th>lineages at the end</th><th>diversity (#42)</th></tr></thead>
<tbody>{batch}</tbody></table></div>
<p>{TEXT["p_batch"]}</p>
{TEXT["gallery"]}

<h2>4. Discussion</h2>
{TEXT["discussion"]}

<h2>5. Conclusion and next step</h2>
<p>{TEXT["conclusion"]}</p>

<h2>Appendix: data</h2>
<p>Every log step of the four doses on seed 9; the knockout, the batch and the full data are in <code>results/*.csv</code>. Build this report with <code>uv run python experiments/e039_reach/report.py</code>.</p>
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
    ("reach 0 (today), seed 9", HERE, run(), 1, "the wide bar", "Ten gut cells lying across the facing, 2.1 sub-cells long and 6.6 wide: the body that has won since e016, and the shortest mouth in the world."),
    ("reach 1, seed 9", HERE, run(1), 590, "the winner under the reach", "Twenty-one cells, nine muscle, eleven gut, 5.2 long over 3.9 world cells: the top lineage from step 77,000."),
    ("reach 2, seed 9", HERE, run(2), 484, "the armored hunter", "Thirty-five cells, sixteen hard, thirteen muscle, a bite of 2.7 and 57% flesh: the hunter state reach 2 entered at step 40,000 and held."),
    ("control, seed 2", E035, f"{BASE}_seed2", 158, "the bar it replaced", "Nine cells, 2.6 long and 6.2 wide, 54% of the body-steps of the control's last third, beside a mover of 24.8 cells."),
    ("reach 1, seed 2", HERE, run(1, 2), 2433, "the pole", "Thirteen cells, 14.7 long and 2.8 wide over four world cells, nine gut blocks, no bite: the body the reach bought, 75% of the body-steps of the last third."),
    ("reach 1, seed 3", HERE, run(1, 3), 1976, "the world that refused", "Seventeen cells, seven muscle, 4.1 long: seed 3 under the same law keeps the control's body and its length."),
]
GALLERY_CAPTION = "The most common body of the lineage at its peak, on the grid it grew on, front up (blue hard, orange muscle, yellow sensor, aqua gut). The control's winner lies across its facing, 2.1 sub-cells long: the shortest mouth the world can grow, and the body the reach punishes most. Under the law they stand 4.1-14.7 long, and the pole is what the reach bought."

TEXTS = {
    "tldr": ("The reach prices one thing - the body's length front to back - and the world pays exactly that: the length rises in four seeds "
             "of four, and to 13.4 sub-cells of a possible 16 in one seed of three. Size does not follow, because a pole of 12.7 cells "
             "reaches a crown as well as a big body would. Not kept: a reach has to be priced on mass."),
    "question": ("Every winner since e016 is 11-16 cells. e037 made a big body cheaper and e038 gave the world four times the sun; "
                 "neither moved size, because the crowd pins what a gut block earns at 0.003-0.005 a step. What the crowd cannot dilute "
                 "is a food it cannot reach. The world has that food already - the trees of e021 stand four cells tall - but a bite is "
                 "the same bite whatever stands on the cell."),
    "world": ("A column of h matter stands h cells tall. What a gut block takes from the standing plant is its bite times min(1, reach / h); "
              "the fruit and the dead lie on the ground and are taken whole. A body's reach is `reach` cells per world cell of its length "
              "front to back, so the longest body reaches four times what the shortest does."),
    "runs": ("Seed 9, 100,000 steps at reach 0 (e038 byte for byte), 0.5, 1 and 2. Then the knockout - one reach for every body - at 1.0 and "
             "1.25 on seed 9 and at 1.0 on seeds 1-3. Then seeds 1-3 at 300,000 steps at reach 1, against e035's runs of this world."),
    "verdicts": ("<li><span class=\"verdict\">Yes</span> the world pays what the law prices: the length rises in four seeds of four (+0.34 to "
                 "+2.18 sub-cells); under the knockout, which prices nothing, it does not.</li>"
                 "<li><span class=\"verdict no\">No</span> size does not follow: the mean body is +1.6, +2.5, +5.6 and -1.0 cells by seed, "
                 "against a control that is itself 11.0-16.4.</li>"
                 "<li><span class=\"verdict no\">No</span> no second body that prospers: the diversity number is 2 against 3 on the pilot's seed, "
                 "and 2-2, 2-1, 1-2 over the three seeds at 300,000 steps.</li>"),
    "h_income": "The trees keep what the crowd cannot take",
    "p_income": ("A tax on taking the standing plant is a subsidy to the plant: at reach 0.5 and 1 it doubles and pays out more in total than "
                 "in the control, 10.3 and 9.4 a step against 5.6, though every bite from it is cut to a quarter or a half. At reach 2 the "
                 "mouths reach most columns and eat them down. The world eats 8-12% less than the control."),
    "h_size": "The bodies get longer, not bigger",
    "p_size": ("Length is what the reach prices and length is what moves. Size does not: the median at reach 1 is 14-15 cells against the "
               "control's 9 on this seed, but the seeds disagree (3.4), and there is no browser's tail - the largest bodies at the end are "
               "77-86 cells, the control's 108 included. A long body is not a heavy one."),
    "h_world": "The world pays a quarter of its bodies",
    "p_world": ("The bodies fall from 3,591 to 2,730-2,796 and a gut block earns 0.0024-0.0027 against 0.0030: standing plant out of reach is "
                "income taken out of the world, and the fruit it spills does not make it back. At reach 0.5 the first winter is a near miss, "
                "57 bodies. At reach 2 the world enters the hunter state at step 40,000 and holds it: 21% of bodies bite."),
    "h_knock": "The knockout: the same reach for every body does the same",
    "p_knock": ("The knockout (e009's rule) keeps the law's loss and drops its gradient. What survives it is not the reach's: the mean body "
                "moves as much or more (+10.0, +6.3, +0.5, -2.0 cells) and the forest grows as well. What does not survive is the length: "
                "+1.48, +0.62, -0.38, -1.12 against four rises out of four."),
    "h_batch": "Three seeds, 300,000 steps",
    "p_batch": ("One world of three takes the offer. Seed 2 grows a body 14.7 long and 2.8 wide over four world cells, nine gut blocks and no "
                "bite, holding 75% of the last third's body-steps over a forest six times the control's - and its floors fall from 691-874 to "
                "144-551, its winners from two to one. Seeds 1 and 3 stay at 4 long."),
    "discussion": ("<p>Nothing here makes a long body cost more than a short one with the same cells: the upkeep is per cell, the weight per "
                   "block, and a line of twelve cells over four world cells reaches the crown of a four-cell column. The law's offer was "
                   "taken in the cheapest currency. That is the answer to #41 as written: a food out of reach buys a shape, not a mass.</p>"
                   "<p>The knockout splits the pilot in two. A tax on the standing plant, with no gradient at all, grows the forest two to six "
                   "times and moves the mean body as much as the law does; the gradient adds the length and nothing else. Without it the "
                   "reach would have been credited with a size effect that is the loss's.</p>"
                   "<p>What this does not show: three seeds at one dose, and why two of them refused the offer - their forests are a sixth of "
                   "seed 2's, so what the law is worth is the world's own state. The trees stay 4-9 a step of an intake of 110-120.</p>"),
    "conclusion": ("Not kept; `reach` stays an argument at 0. The world answers a food out of reach with a pole, because where there is no up "
                   "axis a body's height is free. The next law for size needs an axis that costs matter to stand up in (#5). Next: #37, a body "
                   "that needs water, and #38, the rain on the ridge."),
}


if __name__ == "__main__":
    if len(os.sys.argv) > 1 and os.sys.argv[1] == "lineages":
        for label, (folder, run, _) in RUNS.items():
            if not exists(folder, run):
                continue
            print(label)
            by = lineage_rows(run, folder)
            top = sorted(by, key=lambda lid: -sum(int(r["size"]) for r in by[lid]))[:5]
            for lid in top:
                rows = by[lid]
                peak = max(rows, key=lambda r: int(r["size"]))
                cells = sum(float(peak[k]) for k in ("hard", "muscle", "sensor", "digestive"))
                print(f"  lineage {lid}: {sum(int(r['size']) for r in rows):,} bodies-samples, {int(rows[0]['step']):,}-{int(rows[-1]['step']):,}, peak {peak['size']} at {int(peak['step']):,}; cells {cells:.0f} mass {float(peak['mass']):.0f} hard {float(peak['hard']):.0f} muscle {float(peak['muscle']):.0f} sensor {float(peak['sensor']):.1f} gut {float(peak['digestive']):.0f} side {float(peak['side']):.0f} density {float(peak['density']):.2f} bite {float(peak['bite_any']):.2f} meat {float(peak['meat']):.2f}")
    else:
        main()
