#!/usr/bin/env python3
"""Build report.html for this experiment.

Charts: matplotlib, exported as SVG and inlined. Diagram: hand-written SVG.
Run from the repo root: uv run python experiments/e041_stock/report.py
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


def run(thirst=None, stock=None, seed=9):
    return f"{BASE}{'' if thirst is None else f'_thirst{thirst}'}{'' if stock is None else f'_stock{stock}'}_seed{seed}"


E037 = os.path.join(HERE, "..", "e037_upkeep")  # e037's pilot at k 1 is this world byte for byte (e038 sun 1, e039 reach 0, e040 thirst 0, e041 stock 0)
E035 = os.path.join(HERE, "..", "e035_water")  # the control on seeds 1-3, 300,000 steps: e035's batch is this world, byte for byte
# The pilot on seed 9 in e040's season world (water 0.1, leach 0.01, depth 0.01, mix 0.2, flow 0,
# winter high 2, store 5, grow, rain flat, no ground store, k 1, sun 1, reach 0): label ->
# (folder, run prefix, color slot). `stock` 0 with `thirst` 0 is e040 byte for byte, the control.
RUNS = {
    "control (stock 0, thirst 0)": (HERE, run(), 5),
    "thirst 0.002": (HERE, run(0.002), 3),
    "stock 1": (HERE, run(None, 1), 0),
    "stock 1 + thirst 0.002": (HERE, run(0.002, 1), 1),
    "stock 4": (HERE, run(None, 4), 2),
}
SEEDS = [1, 2, 3]
BATCH_DOSE = 1
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
    """The control: seed 9 is e037's pilot (the same code), seeds 1-3 are e035's batch (the same code)."""
    return (E037, run()) if seed == 9 else (E035, f"{BASE}_seed{seed}")


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


DIAGRAM = """
<figure class="fig diagram">
<svg viewBox="0 0 900 350" width="100%" role="img" aria-label="Left: a tall column takes its neighbours' light and drops fruit around it. Right: the share of its light a cell uses, against what stands on it" font-size="12" fill="currentColor" stroke="currentColor">
  <text x="25" y="22" font-size="11" stroke="none">Where the food comes from (e021 + e022)</text>
  <g stroke-width="1.2" fill="none"><path d="M30,240 H430"/></g>
  <g stroke="none" opacity="0.45"><rect x="55" y="234" width="26" height="6"/><rect x="345" y="234" width="26" height="6"/></g>
  <g stroke="none" opacity="0.30"><rect x="205" y="130" width="32" height="110"/></g>
  <g stroke="none" fill="var(--s1)"><rect x="205" y="106" width="32" height="22"/></g>
  <g fill="none" stroke-width="1.3"><path d="M68,228 C110,198 152,168 197,146"/><path d="M358,228 C316,198 274,168 245,146"/></g>
  <g stroke="none"><path d="M197,146 l10,2 l-3,-8 z"/><path d="M245,146 l-10,2 l3,-8 z"/></g>
  <g fill="none" stroke-width="1.3" stroke-dasharray="4 3"><path d="M209,130 C170,160 132,198 108,226"/><path d="M233,130 C272,160 310,198 334,226"/></g>
  <g stroke="none"><path d="M108,226 l7,-6 l-8,-2 z"/><path d="M334,226 l-7,-6 l8,-2 z"/></g>
  <g stroke="none" font-size="11">
    <text x="196" y="118" text-anchor="end">a body</text>
    <text x="30" y="258">a grazed cell: 0.03-0.05 standing</text>
    <text x="240" y="258">a tree: 1-8 standing, as many cells tall</text>
    <text x="25" y="286">Solid: a column takes the light of every cell within its height.</text>
    <text x="25" y="302">Dashed: what it cannot hold falls as fruit on the ring of 8 - 96 a step</text>
    <text x="25" y="318">of the world's 164 of sun, against 9 grown on the cells themselves.</text>
    <text x="25" y="334">A column under a body claims but cannot grow: it all falls at its feet.</text>
  </g>
  <text x="490" y="22" font-size="11" stroke="none">The law (#43): the share of its light a cell uses</text>
  <g stroke-width="1.2" fill="none"><path d="M520,230 H870"/><path d="M520,230 V90"/></g>
  <g fill="none" stroke="var(--s1)" stroke-width="2"><path d="M520,216 L620,90 L860,90"/></g>
  <g fill="none" stroke-width="1" stroke-dasharray="3 3" opacity="0.7"><path d="M620,96 V230"/></g>
  <g stroke="none" font-size="11">
    <text x="512" y="94" text-anchor="end">1</text>
    <text x="512" y="220" text-anchor="end">0.1</text>
    <text x="520" y="250" text-anchor="middle">0</text>
    <text x="620" y="250" text-anchor="middle">stock</text>
    <text x="860" y="250" text-anchor="middle">the cap, 8</text>
    <text x="520" y="272">what stands on the cell, in matter</text>
    <text x="645" y="76">at the knee and above, the full rate</text>
    <text x="645" y="150">below it a cell grows by the share it</text>
    <text x="645" y="166">stands of the knee, and a bare cell</text>
    <text x="645" y="182">still grows by a tenth: the seed,</text>
    <text x="645" y="198">the root, the spore</text>
    <text x="490" y="318">Run at stock 1 - a tree grows in full, the lawn at the floor -</text>
    <text x="490" y="334">and at stock 4, where the columns are throttled too.</text>
  </g>
</svg>
<figcaption>Figure 1. Left: the world's food since e021 and e022. A column takes the light of every cell within its height, and what it cannot hold falls as fruit on the ring of 8 around it; a column under a body claims too, and everything it takes lands at the body's feet. Right: the law tested here. A cell uses <code>max(0.1, min(1, res / stock))</code> of the light it has - its own and its crown's - and the rest is lost, as a dry cell's is. Nothing else moves: the water, the season, the upkeep and the eye are e040's.</figcaption>
</figure>
"""


TEXT = {}  # filled in main(); counted at the end


def agents_at(run, step, folder=HERE):
    return [r for r in load_rows(f"results/{run}_agents.csv", folder) if int(r["step"]) == step]


def fine(run, folder, last_step, lineage_only=False):
    """Every 1,000 steps (pop.csv): the bodies alive, per band, born elsewhere, their fill and the drinkers (e040); lineages of 5 or more."""
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


def sitter_share(run, folder=HERE):
    """Every lineages.csv step: (steps, share of the bodies in lineages whose mean body has under one muscle block)."""
    rows = load_rows(f"results/{run}_lineages.csv", folder)
    tot, sit = defaultdict(float), defaultdict(float)
    for r in rows:
        t, n = int(r["step"]), float(r["size"])
        tot[t] += n
        if float(r["muscle"]) < 1.0:
            sit[t] += n
    steps = sorted(tot)
    return [float(t) for t in steps], [sit[t] / tot[t] if tot[t] > 0 else float("nan") for t in steps]


def band_share(f, b):
    return [f[f"pop{b}"][i] / f["pop"][i] if f["pop"][i] > 0 else float("nan") for i in range(len(f["step"]))]


def cross_share(f, b):
    return [f[f"cross{b}"][i] / f[f"pop{b}"][i] if f[f"pop{b}"][i] > 0 else float("nan") for i in range(len(f["step"]))]


def floors(f):
    """Per season window: the trough and the peak, with the valley's share at the trough and the ridge's at the peak."""
    out = []
    n = int(max(f["step"])) // SEASON
    for c in range(n):
        idx = [i for i, t in enumerate(f["step"]) if c * SEASON < t <= (c + 1) * SEASON]
        if not idx:
            continue
        lo = min(idx, key=lambda i: f["pop"][i])
        hi = max(idx, key=lambda i: f["pop"][i])
        out.append(dict(step=int(f["step"][lo]), pop=int(f["pop"][lo]), lin=f["lineages"][lo],
                        valley=f["pop0"][lo] / max(f["pop"][lo], 1), peak=int(f["pop"][hi]), peak_ridge=f["pop2"][hi] / max(f["pop"][hi], 1)))
    return out


def summer_mean(f, lo, hi):
    """Means over the pop.csv rows in (lo, hi] in the summer half of each season (the sun above its mean): the share per band, the ridge's bodies born elsewhere, the fill per band, the drinkers' share."""
    idx = [i for i, t in enumerate(f["step"]) if lo < t <= hi and (t % SEASON) < SEASON / 2]
    n = len(idx) or 1
    m = lambda fn: sum(fn(i) for i in idx) / n
    out = dict(pop=m(lambda i: f["pop"][i]))
    for b in range(3):
        out[f"share{b}"] = m(lambda i: f[f"pop{b}"][i] / max(f["pop"][i], 1))
        out[f"cross{b}"] = m(lambda i: f[f"cross{b}"][i] / max(f[f"pop{b}"][i], 1))
        out[f"fill{b}"] = m(lambda i: f[f"fill{b}"][i]) if f"fill{b}" in f else float("nan")
        out[f"drink{b}"] = m(lambda i: f[f"drink{b}"][i] / max(f[f"pop{b}"][i], 1)) if f"drink{b}" in f else float("nan")
    return out


def main():
    logs = {label: load_csv(f"results/{run}_log.csv", folder) for label, (folder, run, _) in RUNS.items() if exists(folder, run)}
    fines = {label: fine(run, folder, STEPS) for label, (folder, run, _) in RUNS.items() if label in logs}
    slot = {label: s for label, (_, _, s) in RUNS.items()}
    xs = max((d["step"] for d in logs.values()), key=len)
    fx = max((d["step"] for d in fines.values()), key=len)
    sit = {label: sitter_share(r, folder) for label, (folder, r, _) in RUNS.items() if label in logs}
    fx2 = max((v[0] for v in sit.values()), key=len)
    sitters = [(label, sit[label][1] + [float("nan")] * (len(fx2) - len(sit[label][1])), slot[label]) for label in RUNS if label in sit]

    def pad(ys, n):
        return ys + [float("nan")] * (n - len(ys))

    def series(key, labels=None, scale=1.0):
        return [(label, pad([v * scale for v in logs[label][key]], len(xs)), slot[label]) for label in (labels or RUNS) if label in logs and key in logs[label]]

    def fine_fn(fn, need="pop", labels=None):
        return [(label, pad(fn(fines[label]), len(fx)), slot[label]) for label in (labels or RUNS) if label in fines and need in fines[label]]

    charts_world = [
        line_chart("Bodies", "Bodies alive every 1,000 steps (pop.csv). The dips are the winters. A line below the control is a world the law made poorer.",
                   fx, fine_fn(lambda f: list(f["pop"])), ymin=0),
        line_chart("The cells' own regrowth", "Plant matter grown on the cells, per step, mean over each 10,000 steps. This is the flow the law acts on; the world's other food falls as fruit.",
                   xs, series("regrowth"), ymin=0),
    ]
    charts_move = [
        line_chart("The sitters hold the world", "Share of the bodies in lineages whose mean body has under one muscle block, every 1,000 steps. A fall would be the law making movement pay.",
                   fx2, sitters, ymin=0, ymax=1, percent=True),
        line_chart("What a body spends on moving", "Energy paid for moving per body per step, mean over each 10,000 steps. A body that walks to its food pays more; a sitter pays almost nothing.",
                   xs, series("move_spent"), ymin=0),
    ]
    charts_trees = [
        line_chart("Trees", "Cells holding at least 1 of standing matter, every 10,000 steps. Under the law a tree eaten below the knee comes back slowly, and fewer stand.",
                   xs, series("trees"), ymin=0),
        line_chart("The tallest column", "The most standing matter on one cell, every 10,000 steps. The world answers the law with fewer and taller trees: each one claims more light.",
                   xs, series("res_max"), ymin=0),
    ]
    charts_fruit = [
        line_chart("Fruit made", "Plant matter that fell as fruit around the columns, per step, mean over each 10,000 steps. It is ten times the cells' own regrowth, and the law hardly touches it.",
                   xs, series("fruit"), ymin=0),
        line_chart("The ridge's bodies born elsewhere", "Of the bodies standing on the ridge, the share born in another band, every 1,000 steps. A rise would be bodies travelling; the control's level is the winter's wave.",
                   fx, fine_fn(cross_share_fn(2), need="cross2"), ymin=0, percent=True),
    ]

    def summary_row(label, lo=STEPS // 2, hi=STEPS):
        d, f = logs[label], fines[label]
        folder, r, _ = RUNS[label]
        w = floors(f)
        half = [i for i, t in enumerate(d["step"]) if lo < t <= hi]
        mean = lambda k: sum(d[k][i] for i in half) / len(half) if k in d else float("nan")
        div, wins = diversity(r, folder)
        st, sh = sitter_share(r, folder)
        return (f"<tr><td>{label}</td><td>{', '.join(format(x['pop'], ',') for x in w)}</td><td>{mean('pop'):,.0f}</td>"
                f"<td>{(mean('plant_intake') + mean('meat_intake')) / 10_000:,.0f}</td><td>{mean('regrowth'):.1f}</td>"
                f"<td>{mean('fruit'):.0f}</td><td>{mean('trees'):.0f}</td><td>{mean('bare'):.1f}</td>"
                f"<td>{mean('muscle_mean'):.2f}</td><td>{mean('move_spent'):.5f}</td>"
                f"<td>{sh[-1]:.0%}</td><td>{f['lineages'][-1]}</td><td>{div} of {len(wins)}</td></tr>")

    rows = "".join(summary_row(label) for label in RUNS if label in logs)

    tables = data_table(["step", "pop", "births", "deaths_energy", "plant_intake", "meat_intake", "regrowth", "bare", "grazed", "fruit", "fruit_eaten", "trees", "res_max", "muscle_mean", "speed_mean", "move_spent", "size_p50", "sense_used", "lineages"],
                        {f"{label}, seed 9": d for label, d in logs.items()}, every=1)
    TEXT.update(TEXTS)
    TEXT["gallery"] = gallery(GALLERY, GALLERY_CAPTION)
    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>e041 A plant that grows from what stands - Report</title>
<style>{CSS}</style>
</head>
<body>
<main>
<h1>e041: A plant that grows from what stands</h1>
<p class="sub">Experiment report - 2026-09-09 - a cell's growth follows the plant standing on it (#43), at a knee of 1 and 4, alone and with e040's thirst, on seed 9. Answer: {TEXT["sub_answer"]}</p>

<section class="tldr">
<h2>TL;DR</h2>
<p>{TEXT["tldr"]}</p>
</section>

<h2>1. Question</h2>
<p>{TEXT["question"]}</p>
<ol>
  <li><strong>The sitter loses:</strong> the food under a body runs out, so movers hold the winners' share, the bodies move, and the crowd's footprint moves.</li>
  <li><strong>And then the thirst shapes a route:</strong> with both laws on, the bodies go between the water and the grazing.</li>
  <li><strong>Or the law is only a tax:</strong> the world's food already falls from the tree crowns, so a law on the cells' growth costs bodies and leaves the sitter where it was.</li>
</ol>

<h2>2. The law</h2>
<p>{TEXT["world"]}</p>
{DIAGRAM}
<p><strong>Runs.</strong> {TEXT["runs"]}</p>
<ul class="measures">
  <li><strong>bodies and floors</strong> - bodies alive every 1,000 steps and the five winter troughs: what the law costs the world.</li>
  <li><strong>regrowth, bare, grazed</strong> - the plant grown on the cells per step, the light lost to the law, and the share of cells below the knee.</li>
  <li><strong>fruit, trees, tallest column</strong> - the fall the crowd lives on, and the columns that make it.</li>
  <li><strong>the sitters' share</strong> - the bodies in lineages with under one muscle block; and move_spent, the energy a body pays for moving.</li>
  <li><strong>the trips</strong> - the ridge's bodies born in another band (cross2, pop.csv), the lineages, and the diversity number (#42).</li>
</ul>

<h2>3. Results</h2>
<div class="tw"><table>
<thead><tr><th>Seed 9, 100,000 steps (means over the last half)</th><th>winter floors</th><th>bodies</th><th>eaten a step</th><th>regrowth</th><th>fruit made</th><th>trees</th><th>light lost</th><th>muscle</th><th>move cost a body</th><th>sitters at the end</th><th>lineages</th><th>diversity (#42)</th></tr></thead>
<tbody>{rows}</tbody></table></div>
<ol class="verdicts">
{TEXT["verdicts"]}
</ol>

<h3>3.1 {TEXT["h_world"]}</h3>
<div class="grid2">
{"".join(charts_world)}
</div>
<p>{TEXT["p_world"]}</p>

<h3>3.2 {TEXT["h_move"]}</h3>
<div class="grid2">
{"".join(charts_move)}
</div>
<p>{TEXT["p_move"]}</p>

<h3>3.3 {TEXT["h_trees"]}</h3>
<div class="grid2">
{"".join(charts_trees)}
</div>
<p>{TEXT["p_trees"]}</p>

<h3>3.4 {TEXT["h_fruit"]}</h3>
<div class="grid2">
{"".join(charts_fruit)}
</div>
<p>{TEXT["p_fruit"]}</p>
{TEXT["gallery"]}

<h2>4. Discussion</h2>
{TEXT["discussion"]}

<h2>5. Conclusion and next step</h2>
<p>{TEXT["conclusion"]}</p>

<h2>Appendix: data</h2>
<p>Every log step of the five runs on seed 9; the full data are in <code>results/*.csv</code>. Build this report with <code>uv run python experiments/e041_stock/report.py</code>.</p>
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


def band_share_fn(b):
    return lambda f: band_share(f, b)


def cross_share_fn(b):
    return lambda f: cross_share(f, b)


GALLERY = [
    ("control, seed 9", HERE, run(), 1, "the wide bar", "Ten gut cells lying across the facing, no muscle: it eats what falls at its feet, and 68% of the bodies alive at the end are its."),
    ("control, seed 9", HERE, run(), 352, "the mover the control already had", "Six muscle behind eight gut: the control has a walker before any law, and it lives on the dead, not on the grass. It holds 32% at the end."),
    ("stock 1, seed 9", HERE, run(None, 1), 213, "the sitter under the law", "Six gut cells on a 7x7 grid, the smallest winner of the five runs. Under a growth that follows the stock it ends holding 76% of the bodies."),
    ("stock 1, seed 9", HERE, run(None, 1), 471, "the scavenger, not the grazer", "Eight muscle against seven gut, on a 4x4 grid: the fastest body of that run. Where the law puts muscle on the world, the muscle hunts carrion."),
    ("stock 4, seed 9", HERE, run(None, 4), 430, "the boom at the harder knee", "Ten muscle and nine gut, the top lineage of the last third at 26% - and a boom: it runs from step 70,000 and is gone by 87,000."),
    ("stock 1 + thirst 0.002, seed 9", HERE, run(0.002, 1), 89, "two needs, one gut", "Twelve gut cells, one hard, no muscle. With both laws on, this lineage is every body alive at step 100,000: the least mobile world of the five."),
]
GALLERY_CAPTION = "The most common body of the lineage at its peak, on the grid it grew on, front up (blue hard, orange muscle, yellow sensor, aqua gut). The law does not replace the sitter with a grazer that walks; where it puts muscle on the world, the muscle belongs to a scavenger."

TEXTS = {
    "sub_answer": "no. The crowd does not eat the cell it stands on, so throttling that cell taxes the world and the sitter wins by more.",
    "tldr": ("A cell that grows only as fast as the plant standing on it does not make a herd move. At a knee of 1 and 4 the law costs the world "
             "39% and 49% of its bodies and two thirds of the cells' own regrowth, and the sitters end holding 76% and 88% of the bodies against "
             "the control's 68%. With the thirst on top, one gutted lineage holds every body alive. Not kept: 91% of what the bodies eat is fruit "
             "falling from the crowns above them."),
    "question": ("e040 read the world's answer to every need as \"sit where the food is\". The premise of #43 is that a real lawn grows from its "
                 "leaves, so a place eaten to the ground stays bare and the herd moves on - the minimal reason to leave, without which no second "
                 "need (thirst, a reach, a store) can shape a route. This tests the growth law and the thirst as one 2x2, because the claim is "
                 "about two conditions together."),
    "world": ("A cell uses max(0.1, min(1, res / stock)) of the light it has, its own and what its column claims from around it; the rest is lost, "
              "as a dry cell's light is. A cell grazed to the ground takes about 330 steps to stand at 1 again, against 100 under e040's growth. "
              "Nothing else changes."),
    "runs": ("Seed 9, 100,000 steps, five runs at once, 12-13 minutes a run: the control (both laws off, e037's pilot byte for byte), the thirst "
             "alone at 0.002, the law at stock 1 (a tree grows in full, the lawn at the floor), the two together, and stock 4, where the columns "
             "are throttled too. No batch on seeds 1-3: the law did not change who wins."),
    "verdicts": ("<li><span class=\"verdict no\">No</span> the sitter does not lose: it ends with 76% and 88% of the bodies against the control's 68%, "
                 "and a body pays 0.0009-0.0011 of energy a step for moving, as in the control.</li>"
                 "<li><span class=\"verdict no\">No</span> no trips: with both laws on, the ridge's summer bodies born elsewhere are the lowest of "
                 "the five (15.9% against the control's 18.0%) and the mean muscle is 0.27 against 3.13.</li>"
                 "<li><span class=\"verdict\">Yes</span> a tax: 10.0 and 16.8 of the sun's 164 a step are lost, and the world falls to 2,252 and 1,857 bodies "
                 "with winter floors of 371-413 and 309-496 against 626-775.</li>"),
    "h_world": "The law binds on the whole world and takes a third of it",
    "p_world": ("The lawn stands at 0.03-0.05, so at either knee the law binds nearly everywhere and the cells' own regrowth falls from 9.0 to 3.5 and "
                "3.0 a step. The bodies fall further than the food does - 39% and 49% against 6% and 22% of what is eaten - because the crowd thins "
                "until each gut earns more: 0.0033 against the control's 0.0026."),
    "h_move": "Nobody leaves",
    "p_move": ("The share of the world held by muscle-free lineages does not fall under the law; it rises. A body's spending on movement is flat, "
               "the share of bodies standing outside the band where they were born falls from 9.0% to 6.9%, and the mean speed from 0.114 to 0.102. "
               "The crowd does not spread out either: 79-82% of its move attempts are blocked against the control's 74%."),
    "h_trees": "The world answers with fewer, taller trees",
    "p_trees": ("A column eaten below the knee comes back slowly, so the trees fall from 239 cells to 111 and 74 - and the tallest column doubles, "
                "from 38 to 73 and 79. With fewer tall columns each remaining one claims more of the light around it. The law does not thin the "
                "canopy's income; it concentrates it."),
    "h_fruit": "Because the food falls from above",
    "p_fruit": ("Fruit made barely moves (96 to 95 and 84 a step) while the cells' own regrowth is cut by two thirds, and 91% of what the bodies eat "
                "is fruit lying on the ground. A body on a column is paid for standing: the column claims its neighbours' light and drops at the "
                "body's feet what it cannot hold. The ground under a sitter never empties."),
    "discussion": ("<p>The premise is right and the law is in the wrong place. A herd leaves a place it has emptied; this crowd never empties the ground "
                   "under it, because the ground under it is fed from above. Since e021 and e022 the world's food is a fountain, and the fountain is "
                   "strongest exactly where a body stands, because a column under a body cannot grow and so drops everything it takes.</p>"
                   "<p>What the law does instead is instructive. It costs the world a third to a half of its bodies and buys a little more life at the "
                   "edges: the lineage count at the end rises from 2 to 5-6, and muscled scavengers - 28-49% of their intake is meat - hold a fifth to "
                   "a quarter of the body-steps for 7,000-20,000 steps at a time. But the diversity number (#42) is 2 in every run: more lineages, the "
                   "same two shapes, and both of them were in the control.</p>"
                   "<p>What this does not show: one seed, 100,000 steps, two knees. A 20,000-step trial at a knee of 0.05 left the population at "
                   "the control's, so the law can be made nearly free - but nothing here suggests a dose where it buys movement.</p>"),
    "conclusion": ("Not kept; `stock` stays an argument at 0. The reason to leave cannot be built on a cell's regrowth while nine tenths of what the "
                   "bodies eat falls from the crowns above them. The next version acts on the fall: e022 lets a column under a body claim its "
                   "neighbours' light, which is the sitter's engine and has never been tested on its own. Take it away and standing on a tree stops "
                   "the fruit. Then #38."),
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
