#!/usr/bin/env python3
"""Build report.html for this experiment.

Charts: matplotlib, exported as SVG and inlined. Diagram: hand-written SVG.
Run from the repo root: uv run python experiments/e029_size/report.py
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

BASE = "128_sigma0_r64_f0.1_flat_eyes8_flesh1_w1_season0.5"
# The runs: label -> (folder, run prefix, color slot). The control is e026's season pilot, this code with side 8.
RUNS = {
    "e026 (control, side 8)": (E026, f"{BASE}_seed9", 1),
    "grow": (HERE, f"{BASE}_digest0_sidegrow_seed9", 0),
    "side 16": (HERE, f"{BASE}_digest0_side16_seed9", 2),
}
CONTROL, GROW, S16 = list(RUNS)
STEPS = 100_000
# The batch: grow and side 16 on seeds 1-4, 500,000 steps, against e026's season runs (this code with side 8).
BATCH = {
    "grow": (HERE, f"{BASE}_digest0_sidegrow", 0),
    "side 16": (HERE, f"{BASE}_digest0_side16", 2),
    "e026 (control, side 8)": (E026, BASE, 1),
}
B_GROW, B_S16, B_CONTROL = list(BATCH)
SEEDS = [1, 2, 3, 4]
LAST_STEP = 500_000
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
        c = Counter(a[2] for a in frame["agents"] if a[4] == lid)
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
<figure class="diagram">
<svg viewBox="0 0 900 295" role="img" aria-label="A body grows on a grid of side by side cells. The six morphogen gradients span the grid whatever its side, so the same genome writes the same pattern on a 4 by 4, an 8 by 8 or a 16 by 16 grid, at 16, 64 or 256 cells at most. Under grow the genome expresses the side, from 4 to 16, read from the gene network like the density." style="max-width:100%;height:auto;display:block">
<defs><marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="currentColor"/></marker></defs>
<g fill="none" stroke="currentColor" stroke-width="1.2" font-size="12" font-family="system-ui, sans-serif">
  <!-- the genome -->
  <rect x="30" y="90" width="170" height="110" rx="4"/>
  <text x="115" y="112" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">the genome</text>
  <text x="115" y="134" text-anchor="middle" fill="currentColor" stroke="none">a gene network, settled</text>
  <text x="115" y="152" text-anchor="middle" fill="currentColor" stroke="none">once per cell (position in)</text>
  <text x="115" y="170" text-anchor="middle" fill="currentColor" stroke="none">and once without position:</text>
  <text x="115" y="188" text-anchor="middle" fill="currentColor" stroke="none">policy, density, and the side</text>
  <!-- the grids -->
  <rect x="260.0" y="60.0" width="30.0" height="30.0" fill="var(--s1)" fill-opacity="0.08" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="290.0" y="60.0" width="30.0" height="30.0" fill="var(--s1)" fill-opacity="0.26" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="320.0" y="60.0" width="30.0" height="30.0" fill="var(--s1)" fill-opacity="0.45" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="350.0" y="60.0" width="30.0" height="30.0" fill="var(--s1)" fill-opacity="0.63" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="260.0" y="90.0" width="30.0" height="30.0" fill="var(--s1)" fill-opacity="0.08" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="290.0" y="90.0" width="30.0" height="30.0" fill="var(--s1)" fill-opacity="0.26" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="320.0" y="90.0" width="30.0" height="30.0" fill="var(--s1)" fill-opacity="0.45" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="350.0" y="90.0" width="30.0" height="30.0" fill="var(--s1)" fill-opacity="0.63" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="260.0" y="120.0" width="30.0" height="30.0" fill="var(--s1)" fill-opacity="0.08" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="290.0" y="120.0" width="30.0" height="30.0" fill="var(--s1)" fill-opacity="0.26" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="320.0" y="120.0" width="30.0" height="30.0" fill="var(--s1)" fill-opacity="0.45" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="350.0" y="120.0" width="30.0" height="30.0" fill="var(--s1)" fill-opacity="0.63" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="260.0" y="150.0" width="30.0" height="30.0" fill="var(--s1)" fill-opacity="0.08" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="290.0" y="150.0" width="30.0" height="30.0" fill="var(--s1)" fill-opacity="0.26" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="320.0" y="150.0" width="30.0" height="30.0" fill="var(--s1)" fill-opacity="0.45" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="350.0" y="150.0" width="30.0" height="30.0" fill="var(--s1)" fill-opacity="0.63" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="430.0" y="60.0" width="15.0" height="15.0" fill="var(--s1)" fill-opacity="0.08" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="445.0" y="60.0" width="15.0" height="15.0" fill="var(--s1)" fill-opacity="0.16" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="460.0" y="60.0" width="15.0" height="15.0" fill="var(--s1)" fill-opacity="0.24" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="475.0" y="60.0" width="15.0" height="15.0" fill="var(--s1)" fill-opacity="0.32" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="490.0" y="60.0" width="15.0" height="15.0" fill="var(--s1)" fill-opacity="0.39" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="505.0" y="60.0" width="15.0" height="15.0" fill="var(--s1)" fill-opacity="0.47" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="520.0" y="60.0" width="15.0" height="15.0" fill="var(--s1)" fill-opacity="0.55" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="535.0" y="60.0" width="15.0" height="15.0" fill="var(--s1)" fill-opacity="0.63" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="430.0" y="75.0" width="15.0" height="15.0" fill="var(--s1)" fill-opacity="0.08" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="445.0" y="75.0" width="15.0" height="15.0" fill="var(--s1)" fill-opacity="0.16" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="460.0" y="75.0" width="15.0" height="15.0" fill="var(--s1)" fill-opacity="0.24" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="475.0" y="75.0" width="15.0" height="15.0" fill="var(--s1)" fill-opacity="0.32" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="490.0" y="75.0" width="15.0" height="15.0" fill="var(--s1)" fill-opacity="0.39" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="505.0" y="75.0" width="15.0" height="15.0" fill="var(--s1)" fill-opacity="0.47" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="520.0" y="75.0" width="15.0" height="15.0" fill="var(--s1)" fill-opacity="0.55" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="535.0" y="75.0" width="15.0" height="15.0" fill="var(--s1)" fill-opacity="0.63" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="430.0" y="90.0" width="15.0" height="15.0" fill="var(--s1)" fill-opacity="0.08" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="445.0" y="90.0" width="15.0" height="15.0" fill="var(--s1)" fill-opacity="0.16" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="460.0" y="90.0" width="15.0" height="15.0" fill="var(--s1)" fill-opacity="0.24" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="475.0" y="90.0" width="15.0" height="15.0" fill="var(--s1)" fill-opacity="0.32" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="490.0" y="90.0" width="15.0" height="15.0" fill="var(--s1)" fill-opacity="0.39" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="505.0" y="90.0" width="15.0" height="15.0" fill="var(--s1)" fill-opacity="0.47" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="520.0" y="90.0" width="15.0" height="15.0" fill="var(--s1)" fill-opacity="0.55" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="535.0" y="90.0" width="15.0" height="15.0" fill="var(--s1)" fill-opacity="0.63" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="430.0" y="105.0" width="15.0" height="15.0" fill="var(--s1)" fill-opacity="0.08" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="445.0" y="105.0" width="15.0" height="15.0" fill="var(--s1)" fill-opacity="0.16" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="460.0" y="105.0" width="15.0" height="15.0" fill="var(--s1)" fill-opacity="0.24" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="475.0" y="105.0" width="15.0" height="15.0" fill="var(--s1)" fill-opacity="0.32" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="490.0" y="105.0" width="15.0" height="15.0" fill="var(--s1)" fill-opacity="0.39" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="505.0" y="105.0" width="15.0" height="15.0" fill="var(--s1)" fill-opacity="0.47" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="520.0" y="105.0" width="15.0" height="15.0" fill="var(--s1)" fill-opacity="0.55" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="535.0" y="105.0" width="15.0" height="15.0" fill="var(--s1)" fill-opacity="0.63" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="430.0" y="120.0" width="15.0" height="15.0" fill="var(--s1)" fill-opacity="0.08" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="445.0" y="120.0" width="15.0" height="15.0" fill="var(--s1)" fill-opacity="0.16" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="460.0" y="120.0" width="15.0" height="15.0" fill="var(--s1)" fill-opacity="0.24" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="475.0" y="120.0" width="15.0" height="15.0" fill="var(--s1)" fill-opacity="0.32" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="490.0" y="120.0" width="15.0" height="15.0" fill="var(--s1)" fill-opacity="0.39" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="505.0" y="120.0" width="15.0" height="15.0" fill="var(--s1)" fill-opacity="0.47" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="520.0" y="120.0" width="15.0" height="15.0" fill="var(--s1)" fill-opacity="0.55" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="535.0" y="120.0" width="15.0" height="15.0" fill="var(--s1)" fill-opacity="0.63" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="430.0" y="135.0" width="15.0" height="15.0" fill="var(--s1)" fill-opacity="0.08" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="445.0" y="135.0" width="15.0" height="15.0" fill="var(--s1)" fill-opacity="0.16" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="460.0" y="135.0" width="15.0" height="15.0" fill="var(--s1)" fill-opacity="0.24" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="475.0" y="135.0" width="15.0" height="15.0" fill="var(--s1)" fill-opacity="0.32" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="490.0" y="135.0" width="15.0" height="15.0" fill="var(--s1)" fill-opacity="0.39" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="505.0" y="135.0" width="15.0" height="15.0" fill="var(--s1)" fill-opacity="0.47" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="520.0" y="135.0" width="15.0" height="15.0" fill="var(--s1)" fill-opacity="0.55" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="535.0" y="135.0" width="15.0" height="15.0" fill="var(--s1)" fill-opacity="0.63" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="430.0" y="150.0" width="15.0" height="15.0" fill="var(--s1)" fill-opacity="0.08" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="445.0" y="150.0" width="15.0" height="15.0" fill="var(--s1)" fill-opacity="0.16" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="460.0" y="150.0" width="15.0" height="15.0" fill="var(--s1)" fill-opacity="0.24" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="475.0" y="150.0" width="15.0" height="15.0" fill="var(--s1)" fill-opacity="0.32" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="490.0" y="150.0" width="15.0" height="15.0" fill="var(--s1)" fill-opacity="0.39" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="505.0" y="150.0" width="15.0" height="15.0" fill="var(--s1)" fill-opacity="0.47" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="520.0" y="150.0" width="15.0" height="15.0" fill="var(--s1)" fill-opacity="0.55" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="535.0" y="150.0" width="15.0" height="15.0" fill="var(--s1)" fill-opacity="0.63" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="430.0" y="165.0" width="15.0" height="15.0" fill="var(--s1)" fill-opacity="0.08" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="445.0" y="165.0" width="15.0" height="15.0" fill="var(--s1)" fill-opacity="0.16" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="460.0" y="165.0" width="15.0" height="15.0" fill="var(--s1)" fill-opacity="0.24" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="475.0" y="165.0" width="15.0" height="15.0" fill="var(--s1)" fill-opacity="0.32" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="490.0" y="165.0" width="15.0" height="15.0" fill="var(--s1)" fill-opacity="0.39" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="505.0" y="165.0" width="15.0" height="15.0" fill="var(--s1)" fill-opacity="0.47" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="520.0" y="165.0" width="15.0" height="15.0" fill="var(--s1)" fill-opacity="0.55" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="535.0" y="165.0" width="15.0" height="15.0" fill="var(--s1)" fill-opacity="0.63" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="600.0" y="60.0" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.08" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="607.5" y="60.0" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.12" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="615.0" y="60.0" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.15" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="622.5" y="60.0" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.19" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="630.0" y="60.0" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.23" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="637.5" y="60.0" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.26" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="645.0" y="60.0" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.30" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="652.5" y="60.0" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.34" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="660.0" y="60.0" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.37" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="667.5" y="60.0" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.41" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="675.0" y="60.0" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.45" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="682.5" y="60.0" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.48" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="690.0" y="60.0" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.52" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="697.5" y="60.0" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.56" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="705.0" y="60.0" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.59" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="712.5" y="60.0" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.63" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="600.0" y="67.5" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.08" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="607.5" y="67.5" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.12" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="615.0" y="67.5" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.15" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="622.5" y="67.5" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.19" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="630.0" y="67.5" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.23" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="637.5" y="67.5" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.26" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="645.0" y="67.5" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.30" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="652.5" y="67.5" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.34" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="660.0" y="67.5" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.37" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="667.5" y="67.5" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.41" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="675.0" y="67.5" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.45" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="682.5" y="67.5" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.48" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="690.0" y="67.5" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.52" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="697.5" y="67.5" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.56" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="705.0" y="67.5" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.59" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="712.5" y="67.5" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.63" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="600.0" y="75.0" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.08" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="607.5" y="75.0" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.12" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="615.0" y="75.0" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.15" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="622.5" y="75.0" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.19" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="630.0" y="75.0" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.23" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="637.5" y="75.0" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.26" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="645.0" y="75.0" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.30" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="652.5" y="75.0" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.34" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="660.0" y="75.0" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.37" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="667.5" y="75.0" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.41" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="675.0" y="75.0" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.45" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="682.5" y="75.0" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.48" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="690.0" y="75.0" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.52" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="697.5" y="75.0" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.56" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="705.0" y="75.0" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.59" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="712.5" y="75.0" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.63" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="600.0" y="82.5" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.08" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="607.5" y="82.5" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.12" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="615.0" y="82.5" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.15" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="622.5" y="82.5" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.19" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="630.0" y="82.5" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.23" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="637.5" y="82.5" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.26" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="645.0" y="82.5" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.30" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="652.5" y="82.5" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.34" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="660.0" y="82.5" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.37" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="667.5" y="82.5" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.41" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="675.0" y="82.5" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.45" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="682.5" y="82.5" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.48" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="690.0" y="82.5" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.52" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="697.5" y="82.5" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.56" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="705.0" y="82.5" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.59" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="712.5" y="82.5" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.63" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="600.0" y="90.0" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.08" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="607.5" y="90.0" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.12" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="615.0" y="90.0" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.15" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="622.5" y="90.0" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.19" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="630.0" y="90.0" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.23" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="637.5" y="90.0" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.26" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="645.0" y="90.0" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.30" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="652.5" y="90.0" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.34" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="660.0" y="90.0" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.37" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="667.5" y="90.0" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.41" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="675.0" y="90.0" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.45" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="682.5" y="90.0" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.48" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="690.0" y="90.0" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.52" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="697.5" y="90.0" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.56" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="705.0" y="90.0" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.59" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="712.5" y="90.0" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.63" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="600.0" y="97.5" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.08" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="607.5" y="97.5" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.12" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="615.0" y="97.5" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.15" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="622.5" y="97.5" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.19" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="630.0" y="97.5" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.23" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="637.5" y="97.5" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.26" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="645.0" y="97.5" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.30" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="652.5" y="97.5" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.34" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="660.0" y="97.5" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.37" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="667.5" y="97.5" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.41" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="675.0" y="97.5" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.45" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="682.5" y="97.5" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.48" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="690.0" y="97.5" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.52" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="697.5" y="97.5" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.56" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="705.0" y="97.5" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.59" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="712.5" y="97.5" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.63" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="600.0" y="105.0" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.08" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="607.5" y="105.0" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.12" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="615.0" y="105.0" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.15" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="622.5" y="105.0" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.19" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="630.0" y="105.0" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.23" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="637.5" y="105.0" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.26" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="645.0" y="105.0" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.30" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="652.5" y="105.0" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.34" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="660.0" y="105.0" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.37" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="667.5" y="105.0" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.41" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="675.0" y="105.0" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.45" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="682.5" y="105.0" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.48" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="690.0" y="105.0" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.52" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="697.5" y="105.0" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.56" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="705.0" y="105.0" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.59" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="712.5" y="105.0" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.63" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="600.0" y="112.5" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.08" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="607.5" y="112.5" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.12" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="615.0" y="112.5" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.15" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="622.5" y="112.5" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.19" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="630.0" y="112.5" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.23" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="637.5" y="112.5" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.26" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="645.0" y="112.5" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.30" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="652.5" y="112.5" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.34" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="660.0" y="112.5" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.37" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="667.5" y="112.5" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.41" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="675.0" y="112.5" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.45" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="682.5" y="112.5" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.48" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="690.0" y="112.5" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.52" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="697.5" y="112.5" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.56" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="705.0" y="112.5" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.59" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="712.5" y="112.5" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.63" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="600.0" y="120.0" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.08" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="607.5" y="120.0" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.12" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="615.0" y="120.0" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.15" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="622.5" y="120.0" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.19" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="630.0" y="120.0" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.23" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="637.5" y="120.0" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.26" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="645.0" y="120.0" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.30" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="652.5" y="120.0" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.34" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="660.0" y="120.0" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.37" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="667.5" y="120.0" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.41" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="675.0" y="120.0" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.45" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="682.5" y="120.0" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.48" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="690.0" y="120.0" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.52" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="697.5" y="120.0" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.56" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="705.0" y="120.0" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.59" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="712.5" y="120.0" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.63" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="600.0" y="127.5" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.08" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="607.5" y="127.5" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.12" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="615.0" y="127.5" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.15" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="622.5" y="127.5" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.19" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="630.0" y="127.5" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.23" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="637.5" y="127.5" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.26" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="645.0" y="127.5" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.30" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="652.5" y="127.5" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.34" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="660.0" y="127.5" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.37" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="667.5" y="127.5" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.41" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="675.0" y="127.5" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.45" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="682.5" y="127.5" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.48" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="690.0" y="127.5" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.52" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="697.5" y="127.5" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.56" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="705.0" y="127.5" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.59" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="712.5" y="127.5" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.63" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="600.0" y="135.0" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.08" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="607.5" y="135.0" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.12" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="615.0" y="135.0" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.15" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="622.5" y="135.0" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.19" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="630.0" y="135.0" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.23" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="637.5" y="135.0" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.26" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="645.0" y="135.0" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.30" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="652.5" y="135.0" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.34" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="660.0" y="135.0" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.37" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="667.5" y="135.0" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.41" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="675.0" y="135.0" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.45" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="682.5" y="135.0" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.48" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="690.0" y="135.0" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.52" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="697.5" y="135.0" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.56" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="705.0" y="135.0" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.59" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="712.5" y="135.0" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.63" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="600.0" y="142.5" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.08" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="607.5" y="142.5" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.12" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="615.0" y="142.5" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.15" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="622.5" y="142.5" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.19" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="630.0" y="142.5" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.23" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="637.5" y="142.5" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.26" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="645.0" y="142.5" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.30" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="652.5" y="142.5" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.34" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="660.0" y="142.5" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.37" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="667.5" y="142.5" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.41" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="675.0" y="142.5" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.45" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="682.5" y="142.5" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.48" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="690.0" y="142.5" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.52" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="697.5" y="142.5" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.56" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="705.0" y="142.5" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.59" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="712.5" y="142.5" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.63" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="600.0" y="150.0" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.08" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="607.5" y="150.0" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.12" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="615.0" y="150.0" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.15" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="622.5" y="150.0" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.19" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="630.0" y="150.0" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.23" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="637.5" y="150.0" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.26" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="645.0" y="150.0" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.30" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="652.5" y="150.0" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.34" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="660.0" y="150.0" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.37" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="667.5" y="150.0" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.41" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="675.0" y="150.0" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.45" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="682.5" y="150.0" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.48" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="690.0" y="150.0" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.52" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="697.5" y="150.0" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.56" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="705.0" y="150.0" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.59" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="712.5" y="150.0" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.63" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="600.0" y="157.5" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.08" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="607.5" y="157.5" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.12" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="615.0" y="157.5" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.15" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="622.5" y="157.5" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.19" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="630.0" y="157.5" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.23" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="637.5" y="157.5" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.26" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="645.0" y="157.5" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.30" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="652.5" y="157.5" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.34" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="660.0" y="157.5" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.37" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="667.5" y="157.5" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.41" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="675.0" y="157.5" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.45" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="682.5" y="157.5" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.48" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="690.0" y="157.5" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.52" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="697.5" y="157.5" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.56" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="705.0" y="157.5" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.59" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="712.5" y="157.5" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.63" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="600.0" y="165.0" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.08" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="607.5" y="165.0" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.12" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="615.0" y="165.0" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.15" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="622.5" y="165.0" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.19" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="630.0" y="165.0" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.23" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="637.5" y="165.0" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.26" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="645.0" y="165.0" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.30" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="652.5" y="165.0" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.34" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="660.0" y="165.0" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.37" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="667.5" y="165.0" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.41" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="675.0" y="165.0" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.45" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="682.5" y="165.0" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.48" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="690.0" y="165.0" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.52" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="697.5" y="165.0" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.56" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="705.0" y="165.0" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.59" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="712.5" y="165.0" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.63" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="600.0" y="172.5" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.08" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="607.5" y="172.5" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.12" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="615.0" y="172.5" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.15" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="622.5" y="172.5" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.19" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="630.0" y="172.5" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.23" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="637.5" y="172.5" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.26" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="645.0" y="172.5" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.30" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="652.5" y="172.5" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.34" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="660.0" y="172.5" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.37" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="667.5" y="172.5" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.41" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="675.0" y="172.5" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.45" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="682.5" y="172.5" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.48" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="690.0" y="172.5" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.52" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="697.5" y="172.5" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.56" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="705.0" y="172.5" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.59" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/><rect x="712.5" y="172.5" width="7.5" height="7.5" fill="var(--s1)" fill-opacity="0.63" stroke="currentColor" stroke-opacity="0.35" stroke-width="0.6"/>
  <text x="320" y="200" text-anchor="middle" fill="currentColor" stroke="none">side 4: 16 cells at most</text>
  <text x="490" y="200" text-anchor="middle" fill="currentColor" stroke="none">side 8: 64 (e004-e028)</text>
  <text x="660" y="200" text-anchor="middle" fill="currentColor" stroke="none">side 16: 256</text>
  <text x="490" y="46" text-anchor="middle" fill="currentColor" stroke="none">the gradient x (one of six) spans every grid: a pattern scales with its body</text>
  <!-- arrows -->
  <line x1="200" y1="145" x2="256" y2="145" marker-end="url(#arr)"/>
  <path d="M115,200 L115,250 L430,250" marker-end="url(#arr)"/>
  <text x="130" y="240" text-anchor="start" fill="currentColor" stroke="none" font-weight="600">grow: the side the genome expresses, 8 x 2^(2 sigmoid - 1), 4 to 16</text>
  <text x="130" y="272" text-anchor="start" fill="currentColor" stroke="none">side 16: every body on the large grid, whatever its genome</text>
  <!-- the world -->
  <rect x="745" y="90" width="145" height="110" rx="4"/>
  <text x="817" y="112" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">the world, unchanged</text>
  <text x="817" y="134" text-anchor="middle" fill="currentColor" stroke="none">upkeep per cell</text>
  <text x="817" y="152" text-anchor="middle" fill="currentColor" stroke="none">a child costs its mass</text>
  <text x="817" y="170" text-anchor="middle" fill="currentColor" stroke="none">a gut eats what lies</text>
  <text x="817" y="188" text-anchor="middle" fill="currentColor" stroke="none">under it</text>
  <line x1="722" y1="145" x2="741" y2="145" marker-end="url(#arr)"/>
</g>
</svg>
<figcaption>Figure 1. The body's grid. Development is e004's: the network settles once per cell with the cell's position as input, and the cell becomes the kind with the highest score. The six gradients (x, 1 - x, y, 1 - y, r, 1 - r) span the grid whatever its side, so a larger grid samples the same field finer. Nothing in the world's laws changes with the grid.</figcaption>
</figure>
"""



TEXT = {}  # filled in main(); counted at the end


def side_hist(title, subtitle, agents_by_seed):
    """agents_by_seed: {seed: [(side, ...)]} at the last dump; one bar set per seed, share of bodies."""
    fig, ax = new_axes("side of the grid")
    ax.margins(x=0.02)
    width = 0.8 / max(len(agents_by_seed), 1)
    for k, (sd, sides) in enumerate(sorted(agents_by_seed.items())):
        c = Counter(sides)
        n = max(sum(c.values()), 1)
        xs = list(range(4, SIDE_MAX + 1))
        ax.bar([x + (k - len(agents_by_seed) / 2 + 0.5) * width for x in xs], [c.get(x, 0) / n for x in xs], width=width, color=LINEAGE_PALETTE[k], label=f"seed {sd}", linewidth=0)
    ax.set_xticks(list(range(4, SIDE_MAX + 1, 2)))
    ax.yaxis.set_major_formatter(lambda y, _p: f"{y:.0%}")
    ax.yaxis.set_major_locator(MaxNLocator(4))
    legend_above(ax, len(agents_by_seed))
    return figure(title, subtitle, to_svg(fig))


def agents_at(run, step, folder=HERE):
    return [r for r in load_rows(f"results/{run}_agents.csv", folder) if int(r["step"]) == step]


def main():
    logs = {label: {k: v[:STEPS // 10_000] for k, v in load_csv(f"results/{run}_log.csv", folder).items()} for label, (folder, run, _) in RUNS.items() if exists(folder, run)}
    lineages = {label: lineage_rows(run, folder) for label, (folder, run, _) in RUNS.items() if label in logs}
    xs = logs[CONTROL]["step"]
    slot = {label: s for label, (_, _, s) in RUNS.items()}

    def series(f, labels=None):
        return [(label, [f(logs[label], i) for i in range(len(logs[label]["step"]))], slot[label]) for label in (labels or RUNS) if label in logs]

    side_of = lambda d, i: d["side_mean"][i] if "side_mean" in d else 8.0
    charts_side = [
        line_chart("The side of the grid over the bodies", "Mean side over the bodies alive, one standard deviation shaded for grow. Every body starts near 8; a line that leaves 8 is selection on the side.", xs,
                   series(side_of), ymin=0, ymax=17,
                   bands=[([m - s for m, s in zip(logs[GROW]["side_mean"], logs[GROW]["side_std"])], [m + s for m, s in zip(logs[GROW]["side_mean"], logs[GROW]["side_std"])], slot[GROW])] if GROW in logs else None),
        line_chart("Cells per body", "Mean cells per body alive. On a 16 grid the same genome would make four times the cells; the line says whether the world takes them.", xs, series(lambda d, i: d["size_mean"][i]), ymin=0),
    ]
    charts_mass = [
        line_chart("Mass of the median body", "The 50th percentile of mass over the bodies alive (mass: cells by kind times density). The ceiling of 64 cells binds only if bodies climb to it.", xs, series(lambda d, i: d["mass_p50"][i]), ymin=0),
        line_chart("Mass of the largest body", "The heaviest body alive at each log step. Up to e028 the most is 64 cells at density 2 (a hard cell weighs 2): 128-256.", xs, series(lambda d, i: d["mass_max"][i]), ymin=0),
    ]
    charts_world = [
        line_chart("Bodies", "Bodies alive at each log step; the season halves them each winter.", xs, series(lambda d, i: d["pop"][i]), ymin=0),
        line_chart("Bodies killed per step", "Deaths by a broken body per step. Zero would mean no body breaks another.", xs, series(lambda d, i: d["deaths_broken"][i] / 1e4), ymin=0),
    ]

    def rng(d, k, f=lambda v: v, fmt="{:.2f}"):
        if k not in d:
            return "-"
        vals = [f(v) for v in d[k]]
        return f"{fmt.format(min(vals))}-{fmt.format(max(vals))}"

    def summary_row(label):
        d = logs[label]
        kills = [k / 1e4 for k in d["deaths_broken"]]
        by = lineages[label]
        spans = sorted((int(r[-1]["step"]) - int(r[0]["step"]) + CONFIRM_STEPS for r in by.values()), reverse=True)
        side = f"{d['side_mean'][-1]:.1f} &plusmn; {d['side_std'][-1]:.1f}" if "side_std" in d else "8"
        return (f"<tr><td>{label}</td><td>{rng(d, 'pop', fmt='{:,.0f}')}</td><td>{side}</td><td>{rng(d, 'size_mean', fmt='{:.0f}')}</td>"
                f"<td>{rng(d, 'mass_p10', fmt='{:.0f}')}</td><td>{rng(d, 'mass_p50', fmt='{:.0f}')}</td><td>{rng(d, 'mass_p90', fmt='{:.0f}')}</td><td>{rng(d, 'mass_max', fmt='{:.0f}')}</td>"
                f"<td>{rng(d, 'full_share', fmt='{:.0%}')}</td><td>{min(kills):.2f}-{max(kills):.2f}</td><td>{rng(d, 'sensor_agents_share', fmt='{:.1%}')}</td><td>{rng(d, 'lineages', fmt='{:.0f}')}</td><td>{spans[0]:,}</td></tr>")

    rows = "".join(summary_row(label) for label in RUNS if label in logs)
    tables = data_table(["step", "pop", "side_mean", "side_std", "size_mean", "size_p10", "size_p50", "size_p90", "size_max", "mass_p10", "mass_p50", "mass_p90", "mass_max", "full_share", "deaths_broken", "biters_share", "sensor_agents_share", "lineages", "develops", "steps_per_sec"],
                        {f"{label}, seed 9": d for label, d in logs.items()}, every=1)

    # ---- the batch ----
    blogs, blin = {}, {}
    for world, (folder, run, _) in BATCH.items():
        blogs[world] = {sd: {k: v[:LAST_STEP // 10_000] for k, v in load_csv(f"results/{run}_seed{sd}_log.csv", folder).items()} for sd in SEEDS if exists(folder, f"{run}_seed{sd}")}
        blin[world] = {sd: lineage_rows(f"{run}_seed{sd}", folder) for sd in SEEDS if exists(folder, f"{run}_seed{sd}")}
    have_batch = bool(blogs[B_GROW])
    bsum = {}
    for world in BATCH:
        for sd, d in blogs[world].items():
            n = len(d["step"])
            h = slice(n // 2, n)
            by = blin[world][sd]
            spans = sorted((int(r[-1]["step"]) - int(r[0]["step"]) + CONFIRM_STEPS for r in by.values()), reverse=True)
            per_step = Counter(int(r["step"]) for rows in by.values() for r in rows)
            nw, hold, holds = winners(by)
            bsum[(world, sd)] = dict(pop=median(d["pop"][h]), pop_min=min(d["pop"]), kills=median(k / 1e4 for k in d["deaths_broken"][h]),
                                     biters=median(d["biters_share"][h]), sensor=max(d["sensor_agents_share"]),
                                     side=d["side_mean"][-1] if "side_mean" in d else 8.0, side_std=median(d["side_std"][h]) if "side_std" in d else 0.0,
                                     cells=median(d["size_mean"][h]), p10=median(d["mass_p10"][h]), p50=median(d["mass_p50"][h]), p90=median(d["mass_p90"][h]), mmax=max(d["mass_max"][h]),
                                     full=median(d["full_share"][h]), muscle=median(d["muscle_mean"][h]),
                                     lineages=median(per_step.get(t, 0) for t in range(LAST_STEP // 2, LAST_STEP + 1, 1000)), longest=spans[0] if spans else 0,
                                     winners=nw, hold=hold, holds=holds, last=int(d["step"][-1]))
    charts_batch, timelines, brows, charts_end = [], [], "", []
    if have_batch:
        charts_batch = [
            seeds_chart("The side, four seeds of grow", "Mean side over the bodies, one line per seed. The start is near 8; the line says where selection takes it.", {B_GROW: blogs[B_GROW]}, lambda d, i: d["side_mean"][i] if "side_mean" in d else float("nan"), ymin=0, ymax=17),
            seeds_chart("Mass of the 90th percentile body", "One line per seed and world. Large bodies would lift grow or side 16 above the control.", blogs, lambda d, i: d["mass_p90"][i], ymin=0),
            seeds_chart("Mass of the largest body", "The heaviest body alive, per seed and world. The control's ceiling is 64 cells; side 16's is 256.", blogs, lambda d, i: d["mass_max"][i], ymin=0),
            seeds_chart("Bodies", "Bodies alive, one line per seed and world.", blogs, lambda d, i: d["pop"][i], ymin=0),
            seeds_chart("Bodies killed per step", "Deaths by a broken body per step, per seed and world.", blogs, lambda d, i: d["deaths_broken"][i] / 1e4, ymin=0),
            seeds_chart("Muscle per body", "Mean muscle blocks per body, per seed and world. A sitting gut has none.", blogs, lambda d, i: d["muscle_mean"][i], ymin=0),
        ]
        last = {sd: [int(r["side"]) for r in agents_at(f"{BATCH[B_GROW][1]}_seed{sd}", bsum[(B_GROW, sd)]["last"])] for sd in blogs[B_GROW]}
        pts = []
        for sd, by in blin[B_GROW].items():
            for rows in by.values():
                if max(int(r["size"]) for r in rows) < 20:
                    continue
                for r in rows[::10]:
                    pts.append((float(r["side"]), float(r["mass"]), int(r["size"])))
        charts_end = [
            side_hist("The side at the end, four seeds of grow", "Share of bodies on each grid side at the last dump of each seed. Two peaks would be two kinds of body.", last),
            scatter_chart("Lineages of grow: side against mass", "One point per lineage that reached 20 bodies and 10,000 steps, sized by bodies. Bodies on a small grid can still be heavy: mass is cells times density.", [(B_GROW, [x for x, _, _ in pts], [y for _, y, _ in pts], [max(n / 40, 2) for _, _, n in pts], 0)], "side of the grid", "mass per body"),
        ]
        brows = "".join((f"<tr><td>{world}, seed {sd}</td><td>{b['pop']:,.0f}</td><td>{b['pop_min']:,.0f}</td><td>{b['side']:.1f} &plusmn; {b['side_std']:.1f}</td><td>{b['cells']:.0f}</td><td>{b['p10']:.0f} / {b['p50']:.0f} / {b['p90']:.0f}</td><td>{b['mmax']:.0f}</td>"
                         f"<td>{b['full']:.0%}</td><td>{b['muscle']:.1f}</td><td>{b['kills']:.2f}</td><td>{b['biters']:.1%}</td><td>{b['sensor']:.1%}</td><td>{b['lineages']:.0f}</td><td>{b['longest']:,}</td><td>{b['winners']}; {b['hold']:,}</td></tr>")
                        for (world, sd), b in bsum.items())
    TEXT["question"] = ("The user's premise (#28): the real world spans mites to whales. Every body so far grew on an 8x8 grid, and e026's winners reach 57 cells. "
                        "This experiment raises the grid to 16x16, for every body or as a side the genome expresses, and asks whether size is the world's or the grid's:")
    TEXT["world"] = ("e026's season world (128x128, the sun a sine of 20,000 steps at amplitude 0.5, the weight and flesh laws, the canopy, the spill, rain on every cell alike), "
                     "with the body's grid as the one change. The control is e026 itself: this code with side 8 is e026 byte for byte.")
    TEXT["runs"] = ("Two pilots on seed 9, 100,000 steps, six threads each (25 minutes): side 16 and grow, against e026's pilot. "
                    "Then both forms on seeds 1-4, 500,000 steps, one thread each (grow 1.7-4.2 hours a run, side 16 4.0-4.5: development is side squared network runs), against e026's four season runs. Every 10,000 steps the log records:")
    TEXT["h_side"] = "The side moves under grow; the cells per body do not"
    TEXT["p_side"] = ("Under grow the side falls from 8 to 5.4 in 10,000 steps and stays. On the 16 grid, where the same genome would make four times the cells, "
                      "the bodies are 10-17 cells: the control's. The world takes the cells it can feed, whatever grid they are written on.")
    TEXT["h_mass"] = "The largest body is a newborn; the median is e026's"
    TEXT["p_mass"] = ("The median mass is 8-26 in every run. Bodies of 50 cells or more are under 1% at any dump, "
                      "and the giants of the batch (up to 240 cells of gut, mass 480) are 8-14 steps old: born and starved.")
    TEXT["h_world"] = "The world stands; the 16 grid loses the tooth"
    TEXT["p_world"] = ("Kills fall on the 16 grid (0.03-0.69 a step in the batch, control 1.3-4.6) and the bite is gone in three seeds of four: "
                       "a bite is a hard tip with muscle behind it in one line, and 12 cells on a 16 grid make few lines of two.")
    TEXT["h_batch"] = "Four seeds, four sides, one size"
    TEXT["p_batch"] = ("The grow seeds end at side 4.4, 5.2, 8.1 and 14.3, each with a spread of 0.8-2.4 over its bodies, while the cells per body are 11-16 in all four, in every side 16 run and in the control. "
                       "The side goes where the seed's history takes it; the size stays where the sun puts it.")
    TEXT["h_end"] = "The side sorts a seed's two kinds of body; both are e026's size"
    TEXT["p_end"] = ("Every grow seed holds e026's two kinds: a dense mover (density 2, 3-6 muscle, speed 0.12-0.16) and a light sitting gut (density 1, no muscle, the sensors). "
                     "Seeds 3 and 4 write the mover on a full 4x4 block and the gut on side 6-7; seed 1 the mover on side 8-9; seed 2 has guts only, dense ones over a 14-16 grid and a light one with eyes on side 9.")
    TEXT["p_timelines"] = ("Seed 2 goes up: its lineage of 500,000 steps (side 9) is overtaken from step 250,000 by dense guts on side 16. Seed 4 goes down: one lineage on side 8 holds 212,000 steps "
                           "while the full blocks of side 4 take the rest.")
    grow = lambda sd: (f"grow, seed {sd}", HERE, f"{BASE}_digest0_sidegrow_seed{sd}")
    if have_batch:
        TEXT["gallery"] = gallery([
            (*grow(3), 7796, "Seed 3, the full block", "Fifteen cells filling a 4x4 grid at density 2: five muscle around ten guts, mass 30, speed 0.16. Nothing light shoves it; it walks from cell to cell and eats what it stands on."),
            (*grow(3), 8215, "Seed 3, the sitting gut", "Thirteen guts on a 6x6 grid at density 1, no muscle: it sits and eats the cells under it. The same size as the block, a different grid and a different life."),
            (*grow(2), 1378, "Seed 2, dense gut on the 16 grid", "Seventeen guts spread over a 16x16 grid at density 2: a net over more cells of ground than a block covers, mass 30. It held the top place 117,000 steps."),
            (*grow(2), 8, "Seed 2, the light gut with eyes", "Ten guts and a sensor on a 9x9 grid, density 1: alive for the whole run, the winner until the dense nets came."),
            (*grow(1), 894, "Seed 1, the tooth on side 8", "Three muscle behind a hard tip: e026's hunter, on the grid e026 had. It held the top place 246,000 steps and 49% of its world bites."),
            ("side 16, seed 3", HERE, f"{BASE}_digest0_side16_seed3", 1512, "Side 16, the one tooth", "The only biting winner on the 16 grid: seven guts, two muscle and a hard tip in one line, on a grid of 256. It held 91,000 steps."),
        ], "Figure 2. Bodies of lineages that prospered: the most common body of the lineage at its peak, drawn on the grid it grew on (4x4 to 16x16, at one width), front up (the dashed edge). Blue: hard, orange: muscle, green: digestive, yellow: sensor.")
        timelines = [timeline_chart(f"Lineages of grow, seed {sd}", "Bodies in every lineage that reached 20 over the run, colored by the lineage's side (dark: a small grid, yellow: a large one).", blin[B_GROW][sd]) for sd in [2, 4] if sd in blin[B_GROW]]
    TEXT["tldr"] = ("Raising the body's grid from 8x8 to 16x16 changes nothing about size: on the 16 grid the bodies are 12-14 cells, the control's; with the side heritable, four seeds settle on sides 4, 5, 8 and 14 "
                    "and all four make bodies of 11-16 cells. The side sorts a seed's two kinds of body (a dense mover, a sitting gut) onto grids by chance; the giants are newborns that starve. "
                    "Size is the world's: a body of 16 cells costs the sun of six cells. Not kept as the default. Next: a store a body can spend, so that size pays.")
    TEXT["verdicts"] = ("<li><span class=\"verdict\">Yes</span> The grid is a rescale: 12.5-14.2 cells per body on the 16 grid (control 8-21).</li>"
                        "<li><span class=\"verdict\">Yes</span> The side is selected: 4.4, 5.2, 8.1 and 14.3 at the end of four seeds, spread 0.8-2.4; but by history, not toward a size.</li>"
                        "<li><span class=\"verdict no\">No</span> The 90th percentile of cells is 16-24 in every run; no lineage of 100 bodies at side 6 or less shares a step with one at side 10 or more.</li>"
                        "<li><span class=\"verdict\">Yes</span> 2,480-3,980 bodies against the control's 2,620-4,760.</li>")
    TEXT["discussion"] = ("<p>The ceiling was never why bodies are 10-20 cells. A body pays 0.002 a cell and 0.032 a body per step, a gut takes at most 0.02 a step from the cell under it, and the sun gives every cell 0.01: "
                          "a body of 16 cells costs the sun of six cells, and 16,000 cells feed 2,700 such bodies, which is what every world holds. A larger body costs more sun and gains nothing per cell, "
                          "since a cell of ground holds what the sun gives it whatever stands on it.</p>"
                          "<p>The heritable side is a working axis (it is selected within a seed, spread 0.8-2.4) with nothing to select for: the same 15 cells can be a full 4x4 block or a net over a 16x16 grid, "
                          "and which a seed takes is decided by which lineage got there first. The one cost the grid carries is the tooth: on the 16 grid the bite is gone in three seeds of four.</p>"
                          "<p>Size will pay when a body can do with size what a small body cannot: carry a store through the winter (the fat is its eater's now), or reach food a small body cannot. "
                          "3D bodies (#5) meet the same ceiling and should wait for that.</p>")
    TEXT["conclusion"] = ("Not kept as the default: side stays 8, and the argument (a number, or grow) stays for a world where size pays. #28's answer is that size is set by the sun per cell of ground, "
                          "not by the grid; 256 cells buy only compute (2x per step) and a lost tooth. Next: a store a body can spend, tested under grow now that the side is heritable.")
    for k in ["tldr", "question", "world", "runs", "verdicts", "h_side", "p_side", "h_mass", "p_mass", "h_world", "p_world", "gallery", "h_batch", "p_batch", "h_end", "p_end", "p_timelines", "discussion", "conclusion"]:
        TEXT.setdefault(k, "TODO")
    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>e029 Small and large bodies in one world - Report</title>
<style>{CSS}</style>
</head>
<body>
<main>
<h1>e029: Small and large bodies in one world</h1>
<p class="sub">Experiment report - 2026-09-05 - the ceiling of the body's grid raised from 8x8 to 16x16 in e026's season world, fixed for every body (side 16) or expressed by the genome (grow, 4 to 16): two pilots on seed 9 and both forms on seeds 1-4 for 500,000 steps, against e026's runs.</p>

<section class="tldr">
<h2>TL;DR</h2>
<p>{TEXT["tldr"]}</p>
</section>

<h2>1. Question</h2>
<p>{TEXT["question"]}</p>
<ol>
  <li><strong>The grid alone is a rescale.</strong> On a 16 grid the world settles at e026's cells per body (8-21): the size is the world's, not the grid's.</li>
  <li><strong>The side is selected under grow.</strong> The mean over bodies leaves 8 and the spread grows past the start's.</li>
  <li><strong>Small and large bodies coexist.</strong> The 90th percentile of cells is three times the 10th, and lineages under side 7 and over 10 hold top places together for 100,000 steps.</li>
  <li><strong>The world stands</strong> at e026's population within a factor of two.</li>
</ol>

<h2>2. The law</h2>
<p>{TEXT["world"]}</p>
{DIAGRAM}
<p><strong>Runs.</strong> {TEXT["runs"]}</p>
<ul class="measures">
  <li><strong>side_mean, side_std</strong> - the side of the grid over the bodies alive: mean and spread.</li>
  <li><strong>cells</strong> - cells per body, its mean and percentiles; <strong>full</strong> - the share of bodies filling their whole grid.</li>
  <li><strong>mass</strong> - cells by kind times density: percentiles and the largest body (the issue's judge).</li>
  <li><strong>lineages</strong> - each lineage's side, mass, muscle and bite every 1,000 steps; the longest lineage in steps; the holders of the top place.</li>
  <li>bodies, kills per step, muscle per body, bodies with a sensor.</li>
</ul>

<h2>3. Results</h2>
<div class="tw"><table>
<thead><tr><th>Seed 9, 100,000 steps (range over the log)</th><th>bodies</th><th>side at the end</th><th>cells per body</th><th>mass p10</th><th>p50</th><th>p90</th><th>largest</th><th>full grids</th><th>killed a step</th><th>with a sensor</th><th>lineages</th><th>longest lineage</th></tr></thead>
<tbody>{rows}</tbody></table></div>
<ol class="verdicts">
{TEXT["verdicts"]}
</ol>

<h3>3.1 {TEXT["h_side"]}</h3>
<div class="grid2">
{"".join(charts_side)}
</div>
<p>{TEXT["p_side"]}</p>

<h3>3.2 {TEXT["h_mass"]}</h3>
<div class="grid2">
{"".join(charts_mass)}
</div>
<p>{TEXT["p_mass"]}</p>

<h3>3.3 {TEXT["h_world"]}</h3>
<div class="grid2">
{"".join(charts_world)}
</div>
<p>{TEXT["p_world"]}</p>

<h3>3.4 {TEXT["h_batch"]}</h3>
<div class="tw"><table>
<thead><tr><th>500,000 steps (second half unless said)</th><th>bodies</th><th>fewest</th><th>side at the end</th><th>cells per body</th><th>mass p10 / p50 / p90</th><th>largest</th><th>full grids</th><th>muscle per body</th><th>killed a step</th><th>with a bite</th><th>with a sensor, most</th><th>lineages</th><th>longest lineage</th><th>winners; longest hold</th></tr></thead>
<tbody>{brows}</tbody></table></div>
<div class="grid2">
{"".join(charts_batch)}
</div>
<p>{TEXT["p_batch"]}</p>

<h3>3.5 {TEXT["h_end"]}</h3>
<div class="grid2">
{"".join(charts_end)}
</div>
<p>{TEXT["p_end"]}</p>
{"".join(timelines)}
<p>{TEXT["p_timelines"]}</p>
{TEXT["gallery"]}

<h2>4. Discussion</h2>
{TEXT["discussion"]}

<h2>5. Conclusion and next step</h2>
<p>{TEXT["conclusion"]}</p>

<h2>Appendix: data</h2>
<p>Every log step of the three pilot runs; the full data is in <code>results/*.csv</code> and <code>../e026_weather/results/</code>. Build this report with <code>uv run python experiments/e029_size/report.py</code>.</p>
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
