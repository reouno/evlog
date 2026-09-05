#!/usr/bin/env python3
"""Build report.html for this experiment.

Charts: matplotlib, exported as SVG and inlined. Diagram: hand-written SVG.
Run from the repo root: uv run python experiments/e030_store/report.py
"""
import csv
import html
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
E026 = os.path.join(HERE, "..", "e026_weather")
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4"]  # fixed slot order
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

BASE = "128_sigma0_r64_f0.1_flat_eyes8_flesh1_w1_season0.75"
# The pilots: label -> (folder, run prefix, color slot). The control is e026's pilot at 0.75: this code with store 0.
RUNS = {
    "e026 (control, store 0)": (E026, f"{BASE}_seed9", 1),
    "store 1": (HERE, f"{BASE}_digest0_side8_store1_seed9", 3),
    "store 5": (HERE, f"{BASE}_digest0_side8_store5_seed9", 0),
    "grow, store 5": (HERE, f"{BASE}_digest0_sidegrow_store5_seed9", 2),
}
CONTROL, STORE1, STORE5, GROW5 = list(RUNS)
STEPS = 100_000
# The batch: grow at store 5 and at store 0 (the control at the same seeds), seeds 1-3, 300,000 steps.
BATCH = {
    "grow, store 5": (HERE, f"{BASE}_digest0_sidegrow_store5", 0),
    "grow, store 0 (control)": (HERE, f"{BASE}_digest0_sidegrow_store0", 1),
}
B_STORE, B_CONTROL = list(BATCH)
SEEDS = [1, 2, 3]
LAST_STEP = 300_000
SEASON = 20_000
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
    top = max(v for _, ys, _ in series for v in ys)
    if ymin is not None:
        ax.set_ylim(ymin, ymax if ymax is not None else top * 1.12)
    ax.yaxis.set_major_formatter((lambda y, _p: f"{y:.0%}") if percent else kfmt)
    ax.yaxis.set_major_locator(MaxNLocator(4))
    legend_above(ax, len(series))
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


def seeds_chart(title, subtitle, logs_by_world, key_fn, ymin=0, ymax=None, percent=False):
    """One line per seed, colored by world (the first seed carries the legend)."""
    fig, ax = new_axes()
    top = 0
    for world, (folder, run, slot) in BATCH.items():
        for k, (seed, d) in enumerate(logs_by_world.get(world, {}).items()):
            ys = [key_fn(d, i) for i in range(len(d["step"]))]
            if not ys or all(v != v for v in ys):  # a world without the measure
                continue
            top = max(top, max(ys))
            ax.plot(d["step"], ys, color=SERIES[slot], linewidth=1.2, alpha=0.85, label=world if k == 0 else None)
    ax.set_ylim(ymin, ymax if ymax is not None else top * 1.12)
    ax.yaxis.set_major_formatter((lambda y, _p: f"{y:.0%}") if percent else kfmt)
    ax.yaxis.set_major_locator(MaxNLocator(4))
    legend_above(ax, len(BATCH))
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
    for label, folder, run, lid, name, what, *at in picks:
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
        c = Counter(i for i in ids if sum(ch != "0" for ch in bodies[i][1]) >= grown) or Counter(ids)
        side, cells = bodies[c.most_common(1)[0][0]]
        u = 88 / side
        rects = "".join(f'<rect x="{(i % side) * u:.2f}" y="{(i // side) * u:.2f}" width="{u * 0.9:.2f}" height="{u * 0.9:.2f}" fill="{KIND_COLOR[int(k)]}"/>' for i, k in enumerate(cells) if k != "0")
        m, pl = float(peak["meat"]), float(peak["plant"])
        meat = m / (m + pl) if m + pl > 0 else 0
        cards.append(f"""<figure class="card"><svg viewBox="-1 -1 89 89" width="120" height="120" role="img" aria-label="{html.escape(name)}"><rect x="-1" y="-1" width="89" height="89" fill="var(--cell)"/>{rects}<line x1="-1" y1="-0.5" x2="88" y2="-0.5" stroke="var(--ink2)" stroke-width="1.5" stroke-dasharray="3 2"/></svg>
<figcaption><strong>{html.escape(name)}</strong><br>{html.escape(label)}, lineage {lid}: {span:,} steps, {int(peak["size"]):,} agents at {"step " + format(int(peak["step"]), ",") if at else "its peak"}<br>side {float(peak["side"]):.0f} (grid {side}x{side}), density {float(peak["density"]):.2f}; mass {float(peak["mass"]):.0f} on {float(peak["foot"]):.1f} cells: hard {float(peak["hard"]):.0f}, muscle {float(peak["muscle"]):.0f}, sensor {float(peak["sensor"]):.1f}, digestive {float(peak["digestive"]):.0f}; flesh {meat:.0%} of the intake<br>{html.escape(what)}</figcaption></figure>""")
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
<svg viewBox="0 0 820 300" width="100%" role="img" aria-label="The store law" font-size="12" fill="currentColor" stroke="currentColor">
  <defs><marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0,0 L10,5 L0,10 z" stroke="none" fill="currentColor"/></marker></defs>
  <g fill="none" stroke-width="1.2">
    <rect x="20" y="120" width="140" height="44" rx="6"/>
    <rect x="240" y="120" width="140" height="44" rx="6"/>
    <rect x="470" y="20" width="160" height="56" rx="6" stroke="var(--s1)" stroke-width="2"/>
    <rect x="480" y="200" width="140" height="44" rx="6"/>
    <rect x="240" y="240" width="140" height="44" rx="6"/>
    <rect x="700" y="20" width="110" height="56" rx="6"/>
  </g>
  <text x="90" y="138" text-anchor="middle">food under the gut</text>
  <text x="90" y="153" text-anchor="middle" font-size="10">plants, fruit, the dead</text>
  <text x="310" y="138" text-anchor="middle">energy</text>
  <text x="310" y="153" text-anchor="middle" font-size="10">a child at 2 + 0.1 mass</text>
  <text x="550" y="44" text-anchor="middle" fill="var(--s1)">fat, in the flesh</text>
  <text x="550" y="60" text-anchor="middle" font-size="10">at most store x mass</text>
  <text x="550" y="218" text-anchor="middle">the air</text>
  <text x="550" y="233" text-anchor="middle" font-size="10">rains on every cell alike</text>
  <text x="310" y="258" text-anchor="middle">the ground</text>
  <text x="310" y="273" text-anchor="middle" font-size="10">food where the body lay</text>
  <text x="755" y="44" text-anchor="middle">the eater</text>
  <text x="755" y="60" text-anchor="middle" font-size="10">of a broken cell</text>
  <g fill="none" stroke-width="1.2" marker-end="url(#ah)">
    <path d="M160,142 L240,142"/>
    <path d="M330,120 C330,48 420,48 470,48"/>
    <path d="M500,76 C500,142 440,142 380,142"/>
    <path d="M550,76 L550,200"/>
    <path d="M310,164 L310,240"/>
    <path d="M630,48 L700,48"/>
  </g>
  <text x="200" y="132" text-anchor="middle" font-size="10">0.02 a gut cell</text>
  <text x="318" y="92" text-anchor="end" font-size="10">upkeep is fixed:</text>
  <text x="318" y="104" text-anchor="end" font-size="10">0.002 a cell + 0.032 a body</text>
  <text x="450" y="166" text-anchor="middle" font-size="10" fill="var(--s1)">energy short: the fat pays</text>
  <text x="560" y="122" text-anchor="start" font-size="10">what the fat pays,</text>
  <text x="560" y="134" text-anchor="start" font-size="10">and fat over the ceiling,</text>
  <text x="560" y="146" text-anchor="start" font-size="10">is breathed</text>
  <text x="320" y="206" text-anchor="start" font-size="10">death: energy and fat</text>
  <text x="665" y="38" text-anchor="middle" font-size="10">its share</text>
  <text x="665" y="64" text-anchor="middle" font-size="10">of the fat</text>
</svg>
<figcaption>Figure 1. The store law. A body's upkeep leaves its energy and is fixed in its flesh as fat (e024's flesh law), now with a ceiling of <code>store</code> per unit of mass (5: a body of mass 15 holds 75, 1,300 steps of its upkeep). When the energy cannot pay the upkeep, the fat pays the rest and that is breathed to the air: a body at zero energy lives on its fat and dies when it is gone. The fat still goes to the eater when a cell is broken and to the ground at death; the work of moving is paid from the energy as before. <code>store</code> 0 is e029: no ceiling, and the fat pays nothing.</figcaption>
</figure>
"""

TEXT = {}  # filled in main(); counted at the end


def agents_at(run, step, folder=HERE):
    return [r for r in load_rows(f"results/{run}_agents.csv", folder) if int(r["step"]) == step]


def fine(by, last_step):
    """Every 1,000 steps from the lineage log: bodies (in lineages of 5 or more), lineages, mass per body, side per body."""
    pop, lin, mass, side = Counter(), Counter(), Counter(), Counter()
    for rows in by.values():
        for r in rows:
            t = int(r["step"])
            if t > last_step:
                continue
            n = int(r["size"])
            pop[t] += n
            lin[t] += 1
            mass[t] += n * float(r["mass"])
            side[t] += n * float(r.get("side", 8))
    steps = sorted(pop)
    return {"step": steps, "pop": [pop[t] for t in steps], "lineages": [lin[t] for t in steps],
            "mass": [mass[t] / pop[t] for t in steps], "side": [side[t] / pop[t] for t in steps]}


def winters(f, first=0):
    """Per cycle of the season from `first`: (trough step, bodies at the trough, lineages at the trough, mass at the trough, peak bodies, mass at the peak)."""
    out = []
    n = max(f["step"]) // SEASON
    for c in range(first, n):
        idx = [i for i, t in enumerate(f["step"]) if c * SEASON < t <= (c + 1) * SEASON]
        if not idx:
            continue
        lo = min(idx, key=lambda i: f["pop"][i])
        hi = max(idx, key=lambda i: f["pop"][i])
        out.append((f["step"][lo], f["pop"][lo], f["lineages"][lo], f["mass"][lo], f["pop"][hi], f["mass"][hi]))
    return out


def main():
    logs = {label: {k: v[:STEPS // 10_000] for k, v in load_csv(f"results/{run}_log.csv", folder).items()} for label, (folder, run, _) in RUNS.items() if exists(folder, run)}
    lineages = {label: lineage_rows(run, folder) for label, (folder, run, _) in RUNS.items() if label in logs}
    fines = {label: fine(by, STEPS) for label, by in lineages.items()}
    slot = {label: s for label, (_, _, s) in RUNS.items()}
    xs = logs[CONTROL]["step"]

    def series(f, labels=None, src=None):
        src = src or logs
        return [(label, [f(src[label], i) for i in range(len(src[label]["step"]))], slot[label]) for label in (labels or RUNS) if label in src]

    fx = fines[CONTROL]["step"]
    charts_store = [
        line_chart("Bodies living on their fat", "Share of the bodies alive whose energy is at zero, every 10,000 steps. Without the law such a body is dead; the line is the store in use.", xs,
                   series(lambda d, i: d["on_fat"][i] if "on_fat" in d else 0.0, [STORE1, STORE5, GROW5]), ymin=0, ymax=1, percent=True),
        line_chart("Fat burned per step", "Fat spent by bodies short of energy, per step of the world. The sun gives 41-287 per step over the season; zero would mean no body draws on its store.", xs,
                   series(lambda d, i: d["fat_spent"][i] if "fat_spent" in d else 0.0, [STORE1, STORE5, GROW5]), ymin=0),
    ]
    charts_winter = [
        line_chart("Bodies every 1,000 steps", "Bodies in lineages of 5 or more, from the lineage log. Each dip is a winter (the sun at a quarter at 15,000, 35,000, ...); the floor of a dip is what lives through it.", fx,
                   series(lambda d, i: d["pop"][i], src=fines), ymin=0),
        line_chart("Lineages alive", "Lineages of 5 or more bodies every 1,000 steps. One line at the floor of a winter is a lottery.", fx,
                   series(lambda d, i: d["lineages"][i], src=fines), ymin=0),
        line_chart("Mass per body every 1,000 steps", "Mean mass of the bodies alive (cells by kind times density). A rise in each winter means the heavy bodies are the ones that live through it.", fx,
                   series(lambda d, i: d["mass"][i], src=fines), ymin=0),
        line_chart("Bodies killed per step", "Deaths by a broken body per step, every 10,000 steps. Zero would mean no body breaks another.", xs, series(lambda d, i: d["deaths_broken"][i] / 1e4), ymin=0),
    ]

    def rng(d, k, f=lambda v: v, fmt="{:.2f}"):
        if k not in d:
            return "-"
        vals = [f(v) for v in d[k]]
        return f"{fmt.format(min(vals))}-{fmt.format(max(vals))}"

    def summary_row(label):
        d, f = logs[label], fines[label]
        w = winters(f)
        kills = [k / 1e4 for k in d["deaths_broken"]]
        side = f"{d['side_mean'][-1]:.1f}" if "side_std" in d and d["side_std"][-1] > 0 else "8"
        return (f"<tr><td>{label}</td><td>{min(p for _, p, _, _, _, _ in w):,}-{max(p for _, p, _, _, _, _ in w):,}</td><td>{min(l for _, _, l, _, _, _ in w)}-{max(l for _, _, l, _, _, _ in w)}</td>"
                f"<td>{min(p for _, _, _, _, p, _ in w):,}-{max(p for _, _, _, _, p, _ in w):,}</td>"
                f"<td>{min(m for _, _, _, m, _, _ in w):.0f}-{max(m for _, _, _, m, _, _ in w):.0f} / {min(m for _, _, _, _, _, m in w):.0f}-{max(m for _, _, _, _, _, m in w):.0f}</td>"
                f"<td>{rng(d, 'on_fat', fmt='{:.0%}')}</td><td>{rng(d, 'fat_spent', fmt='{:.0f}')}</td><td>{rng(d, 'fat_mean', fmt='{:.0f}')}</td>"
                f"<td>{min(kills):.2f}-{max(kills):.2f}</td><td>{rng(d, 'biters_share', fmt='{:.0%}')}</td><td>{side}</td></tr>")

    rows = "".join(summary_row(label) for label in RUNS if label in logs)
    tables = data_table(["step", "pop", "on_fat", "fat_spent", "fat_over", "fat_mean", "fat_stock", "air", "deaths_energy", "deaths_broken", "biters_share", "sensor_agents_share", "size_mean", "side_mean", "mass_p50", "mass_p90", "lineages"],
                        {f"{label}, seed 9": d for label, d in logs.items()}, every=1)

    # ---- the batch ----
    blogs, blin, bfine = {}, {}, {}
    for world, (folder, run, _) in BATCH.items():
        blogs[world] = {sd: {k: v[:LAST_STEP // 10_000] for k, v in load_csv(f"results/{run}_seed{sd}_log.csv", folder).items()} for sd in SEEDS if exists(folder, f"{run}_seed{sd}")}
        blin[world] = {sd: lineage_rows(f"{run}_seed{sd}", folder) for sd in SEEDS if sd in blogs[world]}
        bfine[world] = {sd: fine(by, LAST_STEP) for sd, by in blin[world].items()}
    have_batch = bool(blogs[B_STORE]) and bool(blogs[B_CONTROL])
    bsum = {}
    for world in BATCH:
        for sd, d in blogs[world].items():
            n = len(d["step"])
            h = slice(n // 2, n)
            by, f = blin[world][sd], bfine[world][sd]
            w = winters(f, first=LAST_STEP // SEASON // 2)
            spans = sorted((int(r[-1]["step"]) - int(r[0]["step"]) + CONFIRM_STEPS for r in by.values()), reverse=True)
            nw, hold, holds = winners(by, first_step=LAST_STEP // 2)
            bsum[(world, sd)] = dict(pop=median(d["pop"][h]), trough=min(p for _, p, _, _, _, _ in w), trough_lin=median(l for _, _, l, _, _, _ in w),
                                     peak=median(p for _, _, _, _, p, _ in w), mass_tr=median(m for _, _, _, m, _, _ in w), mass_pk=median(m for _, _, _, _, _, m in w),
                                     on_fat=median(d["on_fat"][h]) if "on_fat" in d else 0.0, kills=median(k / 1e4 for k in d["deaths_broken"][h]), biters=median(d["biters_share"][h]),
                                     sensor=max(d["sensor_agents_share"]), side=d["side_mean"][-1], side_std=d["side_std"][-1], cells=median(d["size_mean"][h]), p50=median(d["mass_p50"][h]), p90=median(d["mass_p90"][h]),
                                     longest=spans[0] if spans else 0, winners=nw, hold=hold, last=int(d["step"][-1]))
    charts_batch, brows = [], ""
    if have_batch:
        charts_batch = [
            seeds_chart("Bodies every 1,000 steps, three seeds", "One line per seed and world, from the lineage log. The floors are the winters; the control's floors are the lottery.", bfine, lambda d, i: d["pop"][i], ymin=0),
            seeds_chart("Lineages alive, three seeds", "Lineages of 5 or more bodies every 1,000 steps, per seed and world.", bfine, lambda d, i: d["lineages"][i], ymin=0),
            seeds_chart("The side of the grid", "Mean side over the bodies alive, per seed and world. Every body starts near 8; the store world above the control would be size paying.", blogs, lambda d, i: d["side_mean"][i], ymin=0, ymax=17),
            seeds_chart("Mass per body every 1,000 steps", "Mean mass of the bodies alive, per seed and world. A saw-tooth rising into each winter is the heavy bodies living through it.", bfine, lambda d, i: d["mass"][i], ymin=0),
            seeds_chart("Bodies killed per step", "Deaths by a broken body per step, per seed and world.", blogs, lambda d, i: d["deaths_broken"][i] / 1e4, ymin=0),
            seeds_chart("Bodies with a bite", "Share of the bodies alive with a hard tip and muscle behind it, per seed and world.", blogs, lambda d, i: d["biters_share"][i], ymin=0, percent=True),
        ]
        brows = "".join((f"<tr><td>{world}, seed {sd}</td><td>{b['pop']:,.0f}</td><td>{b['trough']:,}</td><td>{b['trough_lin']:.0f}</td><td>{b['mass_tr']:.0f} / {b['mass_pk']:.0f}</td>"
                         f"<td>{b['on_fat']:.0%}</td><td>{b['side']:.1f} &plusmn; {b['side_std']:.1f}</td><td>{b['p50']:.0f} / {b['p90']:.0f}</td>"
                         f"<td>{b['kills']:.2f}</td><td>{b['biters']:.0%}</td><td>{b['longest']:,}</td><td>{b['winners']}; {b['hold']:,}</td></tr>")
                        for (world, sd), b in bsum.items())
    TEXT["question"] = ("The season showed the ceiling of the bodies: a body has no store of its own. Its upkeep is fixed in its flesh as fat (e024), but the fat is its eater's, so a body that eats "
                        "less than its upkeep dies in 40-90 steps whatever it holds, and the season at 0.75 was a lottery every winter. This experiment makes the fat the body's own, with a ceiling in its flesh, and asks:")
    TEXT["world"] = ("e026's season world (128x128, the weight and flesh laws, the canopy, the spill, rain on every cell alike) at amplitude 0.75: the sun at a quarter at midwinter, under a half for 6,700 steps of every 20,000. "
                     "The control is this code with store 0 (e029 byte for byte).")
    TEXT["runs"] = ("Three pilots on seed 9, 100,000 steps (five winters, 11 minutes each): side 8 at store 1 and store 5, and grow at store 5, against e026's pilot at 0.75. "
                    "Then grow at store 5 and at store 0 on seeds 1-3, 300,000 steps (15 winters), one thread each. Every 1,000 steps the lineage log counts the bodies; every 10,000 the log records:")
    TEXT["h_store"] = "Half the bodies live on their fat, summer and winter"
    TEXT["p_store"] = ("At every log step 47-75% of the bodies are at zero energy and alive on their fat, burning 22-69 of fat per step, a fifth to a third of the sun. "
                       "Without the law these bodies died: starvation deaths fall from 15-48 per step to 2-11.")
    TEXT["h_winter"] = "More lineages live through a winter; the survivors are the heavy bodies"
    TEXT["p_winter"] = ("The winter floors are the control's (500-1,100 bodies at store 5, the control 200-1,100 in its first five winters) but 3-9 lineages stand on them instead of 1-2, "
                        "and at store 5 the bodies at the floor weigh 27-43 against 12-28 at the peak; the control's weigh the same in both seasons. Kills fall from 0.7-8 a step to 0.04-2, but at store 5 a fifth of the bodies bite, where the control has none.")
    TEXT["h_batch"] = "Fifteen winters: floors of 327 or more and 2-22 lineages, against a lottery"
    TEXT["p_batch"] = ("The store world's lowest winter floor is 327-908 bodies in three seeds, with 2-22 lineages on the floors after the third winter; the control's floors fall to 18, 25 and 45 in seven winters of 45, "
                       "always with 1-2 lineages. Starvation deaths fall from 17-21 a step to 2-6: the control's winners eat 70-84% flesh, the store's 13-49%.")
    TEXT["h_size"] = "The side falls; the store's body is a dense 4x4 block, not a large one"
    TEXT["p_size"] = ("The side ends at 4.0-5.6 against the control's 4.8-7.2, and the cells per body at 8-15 against 14. Mass rises in two seeds (32 against 15) by density, not by cells: "
                      "the store is per unit of mass and the upkeep is per cell, so a block at density 2 holds twice the store for the same upkeep and pays for it in the work of moving. "
                      "The tooth stays gone (0-1% bite in both worlds), and the eye stays: the winner of seed 3 carries a sensor for 153,000 steps.")
    store = lambda sd: (f"store 5, seed {sd}", HERE, f"{BASE}_digest0_sidegrow_store5_seed{sd}")
    TEXT["gallery"] = gallery([
        (*store(1), 1, "Seed 1, the light gut", "Six guts on a 6x6 grid at density 1.1, mass 8: it sits and eats what it stands on, and its store of 40 is 700 steps of upkeep. Alive for the whole run, the top place for 151,000 steps."),
        (*store(1), 945, "Seed 1, the dense block", "Five muscle and four guts filling a 4x4 grid at density 2, mass 19: a store of 95, and the muscle to walk from cell to cell. It shares seed 1 with the light gut for 87,000 steps."),
        (*store(2), 1981, "Seed 2, the block with an eye", "Nine guts, five muscle and a sensor on a 4x4 grid at density 2, mass 29: the heaviest winner, a store of 140. Its lineage holds seed 2 from 162,000 to the end."),
        (*store(3), 1216, "Seed 3, the gut with an eye", "A row of guts on a 7x7 grid at density 1, mass 12, a sensor on most bodies of the lineage: it sees the cells around it and lives 153,000 steps beside the blocks, eating 16% flesh."),
        (*store(3), 465, "Seed 3, the muscle block", "Ten muscle and five guts on a 4x4 grid at density 2, mass 31: a mover that eats 49% flesh (the dead that lie where the crowd is). It held 49,000 steps."),
        ("store 0, seed 1", HERE, f"{BASE}_digest0_sidegrow_store0_seed1", 1638, "The control's winner", "Eleven guts and three muscle on an 8x8 grid at density 1.2, mass 18, eating 73% flesh: a body that lives on the starved. The control's lineages are 1-2 at every winter floor."),
    ], "Figure 2. Bodies of lineages that prospered: the most common body of the lineage at its peak, drawn on the grid it grew on (4x4 to 8x8, at one width), front up (the dashed edge). Blue: hard, orange: muscle, green: digestive, yellow: sensor.")
    TEXT["tldr"] = ("A body's fat is now its own store, bounded by its flesh at store per unit of mass, and burned when the energy runs short. Half the bodies live on their fat at every season, and the winter is no longer a lottery: "
                    "at amplitude 0.75 the floors are 327-908 bodies with 2-22 lineages, where the control falls to 18-45 with one or two. Size does not pay: the store's body is a dense 4x4 block (mass 32 by density 2), and the side falls. "
                    "Kept at store 5. Next: the season at amplitude 1, and the cloud on a mountain world.")
    TEXT["verdicts"] = ("<li><span class=\"verdict\">Yes</span> 45-75% of the bodies are at zero energy and alive; starvation deaths fall from 17-21 a step to 2-6.</li>"
                        "<li><span class=\"verdict\">Yes</span> The lowest winter floor is 327 bodies in 45 winters of three seeds (the control 18), with 2-22 lineages on the floors (the control 1-2).</li>"
                        "<li><span class=\"verdict no\">No</span> The side ends at 4.0-5.6 against the control's 4.8-7.2; the mass rises by density (32 against 15 in two seeds), and the survivors of a winter are not heavier than the summer's bodies in the batch.</li>"
                        "<li><span class=\"verdict\">Yes</span> 1,700-3,100 bodies against 3,100-3,750; the air rains 38-49 a step against 11-16; the winners eat 13-49% flesh against 70-84%.</li>")
    TEXT["discussion"] = ("<p>The store is not a winter organ. Half the bodies are at zero energy in every season, because most bodies of a crowded world eat less than their upkeep; before the law they died in 40-90 steps and fed the ground, "
                          "now they wait on their fat for hundreds of steps. That is what changes the winter: the bodies on the floor are the ones with fat left, and a lineage's chance is its store, not the lottery of the last cell.</p>"
                          "<p>Size did not pay because the store is per unit of mass and mass is free of upkeep. A block at density 2 doubles its store without a cell more, and pays in the work of moving and the matter of its children; a body twice as large pays twice the upkeep every step. "
                          "The store made density worth more, as the weight law made it worth resistance; the light sitting gut holds the other place: two kinds of body in every seed.</p>"
                          "<p>The cycle moved from the ground to the air: the control's winners eat three quarters flesh, the dead of the starved; the store world's eat a quarter, and the air, fed by the fat that is burned, rains three times as much.</p>")
    TEXT["conclusion"] = ("Kept, at store 5: the winter is a matter of the store now, not a lottery, and the world holds 2-22 lineages through it. #28's question is answered the other way: the store makes density pay, not size. "
                          "At amplitude 1 the world now lives (e026's died in its first winter) but as a lottery of 7-25 bodies each winter (a pilot, seed 9): the next step is that winter, then the cloud on a mountain world.")
    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>e030 A store a body can spend - Report</title>
<style>{CSS}</style>
</head>
<body>
<main>
<h1>e030: A store a body can spend</h1>
<p class="sub">Experiment report - 2026-09-05 - the fat a body fixes from its upkeep made the body's own store, with a ceiling in its flesh, in e026's season world at amplitude 0.75: three pilots on seed 9 and grow at store 5 against store 0 on seeds 1-3 for 300,000 steps.</p>

<section class="tldr">
<h2>TL;DR</h2>
<p>{TEXT["tldr"]}</p>
</section>

<h2>1. Question</h2>
<p>{TEXT["question"]}</p>
<ol>
  <li><strong>The store exists.</strong> Bodies short of energy live on their fat: a share of the bodies at zero energy alive, fat burned every step, starvation deaths down.</li>
  <li><strong>The season goes past 0.5.</strong> At 0.75 the winter floor rises from the control's lottery (23-40 bodies, one lineage, in e026's later winters) to hundreds, with more than one lineage.</li>
  <li><strong>Size begins to pay.</strong> Under grow the side and the mass rise against the control at the same seeds, or at least the winter's survivors are heavier than the summer's bodies: a store is store times mass, and the upkeep per cell falls with size.</li>
  <li><strong>The world changes shape.</strong> Fewer, fatter bodies; the air rains again (the fat is breathed when burned; the flesh law at 1 breathed nothing).</li>
</ol>

<h2>2. The law</h2>
<p>{TEXT["world"]}</p>
{DIAGRAM}
<p><strong>Runs.</strong> {TEXT["runs"]}</p>
<ul class="measures">
  <li><strong>on_fat</strong> - the share of bodies alive at zero energy; <strong>fat_spent</strong>, <strong>fat_over</strong> - fat burned by such bodies, and fat breathed over the ceiling, per step.</li>
  <li><strong>bodies, lineages</strong> - every 1,000 steps, from the lineage log (lineages of 5 or more); the winter floor is the least in each cycle of 20,000.</li>
  <li><strong>mass, side</strong> - mass per body (cells by kind times density) and the side of the grid, over the bodies alive.</li>
  <li>fat per body, the air, kills per step, bodies with a bite, bodies with a sensor, the longest lineage and the holders of the top place.</li>
</ul>

<h2>3. Results</h2>
<div class="tw"><table>
<thead><tr><th>Seed 9, 100,000 steps (five winters)</th><th>winter floors</th><th>lineages at the floor</th><th>summer peaks</th><th>mass at the floor / at the peak</th><th>on their fat</th><th>fat burned a step</th><th>fat per body</th><th>killed a step</th><th>bodies with a bite</th><th>side at the end</th></tr></thead>
<tbody>{rows}</tbody></table></div>
<ol class="verdicts">
{TEXT["verdicts"]}
</ol>

<h3>3.1 {TEXT["h_store"]}</h3>
<div class="grid2">
{"".join(charts_store)}
</div>
<p>{TEXT["p_store"]}</p>

<h3>3.2 {TEXT["h_winter"]}</h3>
<div class="grid2">
{"".join(charts_winter)}
</div>
<p>{TEXT["p_winter"]}</p>

<h3>3.3 {TEXT["h_batch"]}</h3>
<div class="tw"><table>
<thead><tr><th>300,000 steps (second half)</th><th>bodies</th><th>lowest winter floor</th><th>lineages at the floors</th><th>mass at the floor / peak</th><th>on their fat</th><th>side at the end</th><th>mass p50 / p90</th><th>killed a step</th><th>bodies with a bite</th><th>longest lineage</th><th>winners; longest hold</th></tr></thead>
<tbody>{brows}</tbody></table></div>
<div class="grid2">
{"".join(charts_batch[:4])}
</div>
<p>{TEXT["p_batch"]}</p>

<h3>3.4 {TEXT["h_size"]}</h3>
<div class="grid2">
{"".join(charts_batch[4:])}
</div>
<p>{TEXT["p_size"]}</p>
{TEXT["gallery"]}

<h2>4. Discussion</h2>
{TEXT["discussion"]}

<h2>5. Conclusion and next step</h2>
<p>{TEXT["conclusion"]}</p>

<h2>Appendix: data</h2>
<p>Every log step of the pilot runs; the full data is in <code>results/*.csv</code> and <code>../e026_weather/results/</code>. Build this report with <code>uv run python experiments/e030_store/report.py</code>.</p>
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


if __name__ == "__main__":
    main()
