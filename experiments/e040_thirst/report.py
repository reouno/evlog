#!/usr/bin/env python3
"""Build report.html for this experiment.

Charts: matplotlib, exported as SVG and inlined. Diagram: hand-written SVG.
Run from the repo root: uv run python experiments/e040_thirst/report.py
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


def run(thirst=None, seed=9):
    return f"{BASE}{'' if thirst is None else f'_thirst{thirst}'}_seed{seed}"


E037 = os.path.join(HERE, "..", "e037_upkeep")  # the control on seed 9: e037's pilot at k 1 is this world, byte for byte (e038 sun 1, e039 reach 0, e040 thirst 0)
E035 = os.path.join(HERE, "..", "e035_water")  # the control on seeds 1-3, 300,000 steps: e035's batch is this world, byte for byte
# The pilots on seed 9 in e039's season world (water 0.1, leach 0.01, depth 0.01, mix 0.2, flow 0,
# winter high 2, store 5, grow, rain flat, no ground store, k 1, sun 1, reach 0): label ->
# (folder, run prefix, color slot). `thirst` 0 is e039 byte for byte, the control.
RUNS = {
    "thirst 0 (today)": (E037, run(), 5),
    "thirst 0.001": (HERE, run(0.001), 0),
    "thirst 0.002": (HERE, run(0.002), 1),
    "thirst 0.005": (HERE, run(0.005), 2),
}
SEEDS = [1, 2, 3]
BATCH_DOSE = 0.002
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
<svg viewBox="0 0 900 330" width="100%" role="img" aria-label="A valley with a pool, a dry ridge, and a body that dries and drinks" font-size="12" fill="currentColor" stroke="currentColor">
  <text x="40" y="24" font-size="11" stroke="none">The sky gives every cell 1 of water a step and 1% of it evaporates: a cell alone holds WET = 100. What stands above 100 came down from higher cells - a pool.</text>
  <g stroke-width="1.2" fill="none"><path d="M40,250 L300,250 L620,150 L860,150"/></g>
  <g fill="#2a78d6" stroke="none" opacity="0.5"><rect x="60" y="234" width="220" height="16"/></g>
  <g fill="var(--s1)" stroke="none"><rect x="150" y="208" width="24" height="24"/></g>
  <g fill="var(--s1)" stroke="none" opacity="0.55"><rect x="720" y="126" width="24" height="24"/></g>
  <g fill="none" stroke-width="1.4"><path d="M180,209 L712,135"/><path d="M712,145 L180,219"/></g>
  <g fill="currentColor" stroke="none"><path d="M712,135 l-10,-1 l3,7 z"/><path d="M180,219 l10,1 l-3,-7 z"/></g>
  <g stroke="none" font-size="11">
    <text transform="translate(300,166) rotate(-8)">upper arrow, out to the ridge: the fill drains by `thirst` a step, whatever the body does</text>
    <text transform="translate(300,182) rotate(-8)">lower arrow, back to the pool: the fill rises by 0.1 x the pool's depth a step</text>
    <text x="60" y="200">a body drinking, fill 1</text>
    <text x="752" y="122">a body dry, fill 0: it dies</text>
    <text x="640" y="176">the ridge: water 66, one pool cell in 25</text>
    <text x="640" y="192">its plants grow at 0.66 of the sun</text>
    <text x="60" y="276">the valley: water 137 (median), a pool 0.37 WET deep, three cells of four hold one;</text>
    <text x="60" y="292">a body on it fills by 0.037 a step, dry to full in 27. At thirst 0.002 a full body is dry in 500 steps; it moves a quarter of a cell a step.</text>
  </g>
  <g stroke="none" font-size="10" opacity="0.85">
    <text x="60" y="318">The eye sees the pools as it sees the food (four directions, as far as it sees) and the body reads its thirst (1 - fill): five inputs to the same four moves.</text>
  </g>
</svg>
<figcaption>Figure 1. The law. A body holds a fill of water, 1 full, 0 dry. It dries by `thirst` a step whatever it does, drinks on a cell holding standing water (above WET) by 0.1 times the pool's depth in units of WET, and dies at 0 as a starved body does. A child is born with its mother's fill. The water is a field, not matter: nothing is consumed. Nothing else moves: the plants, the season, the upkeep and the eye are e039's at reach 0.</figcaption>
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

    def pad(ys, n):
        return ys + [float("nan")] * (n - len(ys))

    def series(key, labels=None, scale=1.0):
        return [(label, pad([v * scale for v in logs[label][key]], len(xs)), slot[label]) for label in (labels or RUNS) if label in logs and key in logs[label]]

    def fine_fn(fn, need="pop", labels=None):
        return [(label, pad(fn(fines[label]), len(fx)), slot[label]) for label in (labels or RUNS) if label in fines and need in fines[label]]

    charts_place = [
        line_chart("The ridge's share of the bodies", "Bodies standing on the ridge (the highest third of the cells) over all bodies, every 1,000 steps. The ridge empties each winter; a summer share near 0 is a ridge nobody can live on.",
                   fx, fine_fn(band_share_fn(2)), ymin=0, percent=True),
        line_chart("The ridge's bodies born elsewhere", "Of the bodies on the ridge, the share born in the valley or on the slope, every 1,000 steps. A rise is bodies coming up from the water; the control's 20-30% are the winter's wave.",
                   fx, fine_fn(cross_share_fn(2), need="cross2"), ymin=0, percent=True),
    ]
    charts_fill = [
        line_chart("The fill on the ridge", "Mean fill (1 full, 0 dry) of the bodies standing on the ridge, every 1,000 steps. A fill that sits near 1 is bodies that came up full and go down before they dry; a fall to 0 is bodies dying there.",
                   fx, fine_fn(lambda f: list(f["fill2"]), need="fill2"), ymin=0, ymax=1),
        line_chart("Deaths by thirst", "Bodies that died dry, per step, mean over each 10,000 steps. Zero is a world where every body reaches water in time.",
                   xs, series("deaths_thirst", scale=1 / 10_000), ymin=0),
    ]
    charts_world = [
        line_chart("Bodies", "Bodies alive every 1,000 steps (pop.csv). The dips are the winters; the floors are what the world can carry through one.",
                   fx, fine_fn(lambda f: list(f["pop"])), ymin=0),
        line_chart("The eye decides", "sense_used: the share of moves by bodies with a sensor that differ from what the same body would do blind, mean over each 10,000 steps. A rise under the law is the eye reading the pools or the thirst.",
                   xs, series("sense_used"), ymin=0, percent=True),
    ]

    def summary_row(label, lo=STEPS // 2, hi=STEPS):
        d, f = logs[label], fines[label]
        folder, r, _ = RUNS[label]
        w = floors(f)
        half = [i for i, t in enumerate(d["step"]) if lo < t <= hi]
        mean = lambda k: sum(d[k][i] for i in half) / len(half) if k in d else float("nan")
        sm = summer_mean(f, lo, hi)
        div, wins = diversity(r, folder)
        thirst = f"{mean('deaths_thirst') / 10_000:.3f}" if "deaths_thirst" in d else "-"
        fill = f"{sm['fill0']:.2f} / {sm['fill1']:.2f} / {sm['fill2']:.2f}" if "fill0" in f else "-"
        return (f"<tr><td>{label}</td><td>{', '.join(format(x['pop'], ',') for x in w)}</td><td>{mean('pop'):,.0f}</td>"
                f"<td>{sm['share0']:.0%} / {sm['share1']:.0%} / {sm['share2']:.0%}</td><td>{sm['cross2']:.0%}</td>"
                f"<td>{fill}</td><td>{thirst}</td><td>{mean('deaths_energy') / 10_000:.3f}</td>"
                f"<td>{mean('sense_used'):.0%}</td><td>{mean('intake_per_gut'):.4f}</td>"
                f"<td>{f['lineages'][-1]}</td><td>{div} of {len(wins)}</td></tr>")

    rows = "".join(summary_row(label) for label in RUNS if label in logs)

    # The batch: seeds 1-3 at 300,000 steps, one dose against the control (e035's runs of this world).
    def batch_rows():
        out = []
        for seed in SEEDS:
            for label, (folder, name) in [("control", control_run(seed)), (f"thirst {BATCH_DOSE}", (HERE, run(BATCH_DOSE, seed)))]:
                if not exists(folder, name):
                    continue
                d = load_csv(f"results/{name}_log.csv", folder)
                f = fine(name, folder, 300_000)
                half = [i for i, t in enumerate(d["step"]) if 150_000 < t <= 300_000]
                mean = lambda k: sum(d[k][i] for i in half) / len(half) if k in d else float("nan")
                sm = summer_mean(f, 150_000, 300_000)
                w = floors(f)
                div, wins = diversity(name, folder)
                thirst = f"{mean('deaths_thirst') / 10_000:.3f}" if "deaths_thirst" in d else "-"
                fill = f"{sm['fill0']:.2f} / {sm['fill2']:.2f}" if "fill0" in f else "-"
                out.append(f"<tr><td>seed {seed}, {label}</td><td>{', '.join(format(r['pop'], ',') for r in w[-5:])}</td><td>{mean('pop'):,.0f}</td>"
                           f"<td>{sm['share0']:.0%} / {sm['share1']:.0%} / {sm['share2']:.0%}</td><td>{sm['cross2']:.0%}</td><td>{fill}</td><td>{thirst}</td>"
                           f"<td>{mean('sense_used'):.0%}</td><td>{mean('intake_per_gut'):.4f}</td><td>{f['lineages'][-1]}</td><td>{div} of {len(wins)}</td></tr>")
        return "".join(out)


    tables = data_table(["step", "pop", "births", "deaths_energy", "deaths_thirst", "plant_intake", "meat_intake", "regrowth", "dry", "fill_mean", "drinking", "pool", "sense_used", "size_p50", "size_p90", "fat_stock", "biters_any_share", "lineages"],
                        {f"{label}, seed 9": d for label, d in logs.items()}, every=1)
    TEXT.update(TEXTS)
    TEXT["gallery"] = gallery(GALLERY, GALLERY_CAPTION)
    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>e040 A body that needs water - Report</title>
<style>{CSS}</style>
</head>
<body>
<main>
<h1>e040: A body that needs water</h1>
<p class="sub">Experiment report - 2026-09-09 - a body that dries and must drink where water stands (#37), at 0.001, 0.002 and 0.005 of its fill a step on seed 9, then {TEXT["sub_batch"]}. Answer: {TEXT["sub_answer"]}</p>

<section class="tldr">
<h2>TL;DR</h2>
<p>{TEXT["tldr"]}</p>
</section>

<h2>1. Question</h2>
<p>{TEXT["question"]}</p>
<ol>
  <li><strong>Trips:</strong> the ridge becomes a place visited from the water - its summer bodies are born in the valley, their fill is lowest there, few die dry, and the valley holds more of the summer's bodies.</li>
  <li><strong>Or the ridge empties:</strong> a body cannot learn the trip (the pools are 20-40 cells away, a body moves a quarter of a cell a step), so the ridge's bodies die dry and the world lives on the pools, smaller.</li>
</ol>

<h2>2. The law</h2>
<p>{TEXT["world"]}</p>
{DIAGRAM}
<p><strong>Runs.</strong> {TEXT["runs"]}</p>
<ul class="measures">
  <li><strong>where the bodies are</strong> - bodies per height band every 1,000 steps (pop.csv), and of the ridge's, the share born in another band (cross2): the trips.</li>
  <li><strong>fill</strong> - the mean fill of the bodies per band (fill0..2), 1 full, 0 dry; and the share standing on a pool (drink0..2).</li>
  <li><strong>deaths by thirst</strong> - bodies that died dry, per step (log.csv); beside the deaths by hunger.</li>
  <li><strong>the eye decides</strong> - sense_used: moves by a body with a sensor that differ from the same body's blind move.</li>
  <li><strong>bodies and floors</strong> - bodies alive every 1,000 steps, the winter troughs, a gut block's income, lineages, the diversity number (#42).</li>
</ul>

<h2>3. Results</h2>
<div class="tw"><table>
<thead><tr><th>Seed 9, 100,000 steps (means over the last half; places in summer)</th><th>winter floors</th><th>bodies</th><th>valley / slope / ridge</th><th>ridge born elsewhere</th><th>fill valley / slope / ridge</th><th>deaths dry per step</th><th>deaths hungry</th><th>eye decides</th><th>a gut block earns</th><th>lineages</th><th>diversity (#42)</th></tr></thead>
<tbody>{rows}</tbody></table></div>
<ol class="verdicts">
{TEXT["verdicts"]}
</ol>

<h3>3.1 {TEXT["h_place"]}</h3>
<div class="grid2">
{"".join(charts_place)}
</div>
<p>{TEXT["p_place"]}</p>

<h3>3.2 {TEXT["h_fill"]}</h3>
<div class="grid2">
{"".join(charts_fill)}
</div>
<p>{TEXT["p_fill"]}</p>

<h3>3.3 {TEXT["h_world"]}</h3>
<div class="grid2">
{"".join(charts_world)}
</div>
<p>{TEXT["p_world"]}</p>

<h3>3.4 {TEXT["h_batch"]}</h3>
<p>{TEXT["p_batch"]}</p>
{TEXT["gallery"]}

<h2>4. Discussion</h2>
{TEXT["discussion"]}

<h2>5. Conclusion and next step</h2>
<p>{TEXT["conclusion"]}</p>

<h2>Appendix: data</h2>
<p>Every log step of the three doses and the control on seed 9; the full data are in <code>results/*.csv</code>. Build this report with <code>uv run python experiments/e040_thirst/report.py</code>.</p>
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
    ("thirst 0 (today), seed 9", E037, run(), 1, "the wide bar", "Ten gut cells lying across the facing, no muscle: the sitter that has won since e016, 53% of the body-steps of the last third."),
    ("thirst 0.001, seed 9", HERE, run(0.001), 180, "the same sitter, on a pool", "Twelve cells, eleven gut, no muscle, 57% of the body-steps from step 13,000 on. A body that never moves never dries where it sits, and it sits in the valley."),
    ("thirst 0.002, seed 9", HERE, run(0.002), 308, "the sitter again", "Eleven gut cells, no muscle, 42% of the last third. Its kin (lineage 299, ten gut) holds another 32%: one body, two lineages."),
    ("thirst 0.002, seed 9", HERE, run(0.002), 100, "the mover that lost", "Twenty-seven cells, nine muscle, sixteen gut, 39% flesh: the scavenger that walks. It peaks at step 45,000 and is gone by 72,000."),
    ("thirst 0.005, seed 9", HERE, run(0.005), 127, "the big gut", "Nineteen cells, seventeen gut, under a thirst that dries a body in 200 steps. With a third of the bodies gone the crowd thins and the gut grows."),
    ("thirst 0.005, seed 9", HERE, run(0.005), 313, "the gut with eyes", "Twenty-four cells, twenty gut, two sensors, one muscle: 45% of the last third. The eye is here, but the world's moves that differ from a blind body's fall to 16%."),
]
GALLERY_CAPTION = "The most common body of the lineage at its peak, on the grid it grew on, front up (blue hard, orange muscle, yellow sensor, aqua gut). Under every thirst the winner is a gut without muscle: the world's answer to a body that must drink is to sit on the water, not to walk to it."

TEXTS = {
    "sub_batch": "no batch (the pilot shows no trips, steady over five winters)",
    "sub_answer": "the bodies do not walk to the water; they sit on it, and the ridge lives on its own pools.",
    "tldr": ("A body that dries and must drink where water stands does not learn the trip. Over five winters at three doses the ridge's bodies "
             "born elsewhere stay at the control's 14-18%, the eye decides less (16-22% against 27%), and the ridge stays held at 14-24% of the "
             "bodies because one ridge cell in twenty-five is a pool. The bodies off a pool die dry, 2-7 deaths in 10; the world pays 28-71% of its "
             "bodies; the winner everywhere is a gut with no muscle. Not kept. Next: #38, the rain on the ridge."),
    "question": ("Since e035 the world has water, pooled in the valley, and the plants live on it; the bodies do not. The only reason a body has ever "
                 "had to change place is the winter. #37 gives it the animal's second need, as a law about its material: it loses water as it burns "
                 "and takes it where it stands. Does drinking make the ridge a place visited from the valley, and give the ridge's summer bodies a route down?"),
    "world": ("A body's fill drains by `thirst` a step and fills by 0.1 times the pool's depth on a cell holding water above WET; at 0 the body dies. "
              "The eye sees the pools as it sees the food, and the body reads its thirst: five inputs to the same four moves, from their own column of the law table."),
    "runs": ("Seed 9, 100,000 steps, at thirst 0.001 (a full body lasts 1,000 steps), 0.002 (500) and 0.005 (200), against e037's pilot on the same seed "
             "(the same code with the law off). Three at once, 10-11 minutes a run. No batch: the pilot's measures are steady over five winters."),
    "verdicts": ("<li><span class=\"verdict no\">No</span> trips: the ridge's bodies born elsewhere are 14-18% in summer against the control's 17%, "
                 "and flat from step 50,000 to 100,000 at every dose.</li>"
                 "<li><span class=\"verdict no\">No</span> the ridge does not empty either: it holds 24, 23 and 14% of the summer's bodies (control 27%), "
                 "living on its own pools - one cell in twenty-five.</li>"
                 "<li><span class=\"verdict\">Yes</span> the law kills: 1.7-3.9 bodies a step die dry, 23-72% of all deaths, and the world loses 28, 33 and 71% of its bodies.</li>"),
    "h_place": "The ridge is held from its own pools, not from the valley",
    "p_place": ("The ridge's share and its share of bodies born elsewhere keep the control's rhythm: a summer plateau and a winter wave, at every dose, "
                "with no drift over five winters. What holds the ridge is not traffic but the 4% of its cells that stand above WET: bodies on the "
                "ridge stand on a pool 5-12% of the time, one to three times what chance gives, and the bodies around them die."),
    "h_fill": "The bodies off the water dry and die",
    "p_fill": ("The fill reads the place: 0.87 in the valley, 0.55 on the slope, 0.31-0.41 on the ridge, in every run. A body that walked down "
               "when thirsty would raise the ridge's fill; it does not move. The deaths by thirst follow the summer's crowd, 6-9 a step at the "
               "peaks, and take the bodies hunger would have taken later: the deaths by hunger fall from 8.9 to 5.6, 5.4 and 1.5."),
    "h_world": "The world pays, and the eye decides less",
    "p_world": ("Bodies fall from 3,674 to 2,644, 2,459 and 1,065 while a gut block earns the same 0.0027-0.0031 a step; the thinned crowd grows "
                "bigger bodies (the median 12-26 cells against 9). The moves that differ from a blind body's fall from 27% to 22, 19 and 16%: "
                "the five new inputs are noise to the policy, and selection did not make them a signal in 100,000 steps."),
    "h_batch": "No batch",
    "p_batch": ("The rule was a batch only if the pilot shows trips. It shows none, at three doses, with no trend over the last five winters, so "
                "seeds 1-3 at 300,000 steps were not run (three runs, about 75 minutes)."),
    "discussion": ("<p>The world's answer to a need for water is the answer it gives to every need: sit where the food and the water are. The winner "
                   "at every dose is a gut without muscle, the control's own winner; a sitter on a valley pool never dries, and a sitter on the ridge dies "
                   "and is replaced by a child born there. The law selects places, not trips, because a body that does not move already has the best "
                   "of both - the eye has nothing to add.</p>"
                   "<p>The ridge's own pools are what the pilot found. The issue's premise was a dry ridge visited from the valley; the water law of e035 "
                   "leaves one ridge cell in twenty-five above WET, and that is enough for a sitter's lineage. A ridge with no pool at all would ask a "
                   "different question - but it would also be a ridge the law empties, not one it makes a destination.</p>"
                   "<p>What this does not show: one seed and 100,000 steps. Whether selection would turn the water inputs into a signal over 300,000 steps "
                   "is open, but the sign at 100,000 is down, not flat, and nothing in the crowd rewards a walk that a sitter avoids.</p>"),
    "conclusion": ("Not kept; `thirst` stays an argument at 0. Drinking does not make a reason to move in a world whose bodies win by sitting; it makes "
                   "a second map of where a body can live, and the map already agrees with the food's. Next: #38, the rain on the ridge again, "
                   "under e035's carrier - the ridge's soil as its own before any law asks a body to go there."),
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
