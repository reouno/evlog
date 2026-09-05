#!/usr/bin/env python3
"""Build report.html for this experiment.

Charts: matplotlib, exported as SVG and inlined. Diagram: hand-written SVG.
Run from the repo root: uv run python experiments/e034_stillsoil/report.py
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
E026 = os.path.join(HERE, "..", "e026_weather")
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#8a8a86", "#c9c8c0"]  # fixed slot order; the last two are the controls
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

def base(flow, rain):
    return f"128_sigma0_r64_f{flow}_{rain}_eyes8_flesh1_w1_season2_digest0_sidegrow_store5_yolk0_breed0_winterhigh_seed9"

E032 = os.path.join(HERE, "..", "e032_winter")
E033 = os.path.join(HERE, "..", "e033_wetridge")
# The pilots on seed 9 (winter high 2, store 5, grow): label -> (folder, run prefix, color slot). The controls are the flow-0.1 pilots
# of e032 (rain flat; its pop.csv has no soil columns) and e033 (rain high).
RUNS = {
    "flow 0, rain flat": (HERE, base("0", "flat"), 0),
    "flow 0.0001, rain flat": (HERE, base("0.0001", "flat"), 2),
    "flow 0.001, rain flat": (HERE, base("0.001", "flat"), 1),
    "flow 0.1, rain flat (e032)": (E032, base("0.1", "flat"), 5),
    "flow 0, rain high": (HERE, base("0", "high"), 3),
    "flow 0.001, rain high": (HERE, base("0.001", "high"), 4),
    "flow 0.1, rain high (e033)": (E033, base("0.1", "high"), 6),
}
STEPS = 100_000
BATCH = {}
SEEDS = [1, 2, 3]
LAST_STEP = 300_000
SEASON = 20_000
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
<svg viewBox="0 0 820 320" width="100%" role="img" aria-label="Where the soil goes when it does not flow" font-size="12" fill="currentColor" stroke="currentColor">
  <defs><marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0,0 L10,5 L0,10 z" stroke="none" fill="currentColor"/></marker>
  <marker id="ahs" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0,0 L10,5 L0,10 z" stroke="none" fill="var(--s1)"/></marker></defs>
  <path d="M20,270 C120,270 180,260 240,220 C300,180 340,130 400,110 C460,90 520,140 580,170 C640,200 700,210 800,210" fill="none" stroke-width="2"/>
  <line x1="20" y1="290" x2="800" y2="290" stroke-width="1" stroke-dasharray="3 3" opacity="0.5"/>
  <text x="24" y="306" font-size="10" stroke="none">height 0 (the bottom of the valley): the winter refuge</text>
  <rect x="20" y="20" width="780" height="34" rx="6" fill="none" stroke-width="1.2"/>
  <text x="410" y="41" text-anchor="middle" stroke="none">the air: what the bodies breathe, 30-60 in the world</text>
  <g stroke-width="1.2" opacity="0.8" fill="none"><line x1="32" y1="62" x2="32" y2="264" marker-end="url(#ah)"/><line x1="330" y1="62" x2="330" y2="132" marker-end="url(#ah)"/><line x1="788" y1="62" x2="788" y2="204" marker-end="url(#ah)"/></g>
  <text x="530" y="78" text-anchor="middle" font-size="10" stroke="none">the rain, alike on every cell: 0.0006-0.0009 per cell per step</text>
  <g stroke-width="1.5" fill="none" marker-end="url(#ah)"><line x1="155" y1="206" x2="155" y2="62"/></g>
  <text x="165" y="130" font-size="10" stroke="none">the breath: what the</text>
  <text x="165" y="144" font-size="10" stroke="none">crowd eats goes up</text>
  <g fill="none" stroke-width="1.2"><rect x="45" y="212" width="100" height="34" rx="4"/></g>
  <text x="95" y="233" text-anchor="middle" font-size="10" stroke="none">the crowd eats</text>
  <text x="95" y="258" text-anchor="middle" font-size="10" stroke="none">0.01 per cell per step</text>
  <g stroke="var(--s1)" fill="var(--s1)" stroke-width="0"><path d="M300,180 C340,128 380,112 400,110 C450,100 500,118 560,160 L540,170 C500,140 450,125 400,128 C370,132 340,150 315,185 z" opacity="0.35"/></g>
  <text x="585" y="120" font-size="10" fill="var(--s1)" stroke="none">the pile: where nothing eats</text>
  <text x="585" y="134" font-size="10" fill="var(--s1)" stroke="none">(dark in winter, full in summer)</text>
  <g fill="none" stroke="var(--s1)" stroke-width="1.5" stroke-dasharray="5 3" marker-end="url(#ahs)"><path d="M330,190 C290,225 240,250 190,266"/></g>
  <text x="235" y="262" font-size="10" fill="var(--s1)" stroke="none">the flow: the only road back down</text>
  <text x="235" y="276" font-size="10" fill="var(--s1)" stroke="none">0.1 of the drop per step since e019; 0 here</text>
  <text x="600" y="238" font-size="10" stroke="none">the ridge's soil: 300 with the flow,</text>
  <text x="600" y="252" font-size="10" stroke="none">61,000-72,000 without it (of 131,000)</text>
</svg>
<figcaption>Figure 1. The cycle of the matter over the terrain. The crowd eats in the valley and breathes; the air rains on every cell alike; so what the valley eats comes back in thirds to the valley, the slope and the ridge. A cell's plant uses at most the sun's 0.01 per step and stands full when nobody eats it, so the soil that lands where nothing eats stays. The flow (the accent) is the only road that brings it down again; the still soil cuts it.</figcaption>
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


def main():
    logs = {label: {k: v[:STEPS // 10_000] for k, v in load_csv(f"results/{run}_log.csv", folder).items()} for label, (folder, run, _) in RUNS.items() if exists(folder, run)}
    fines = {label: fine(run, folder, STEPS) for label, (folder, run, _) in RUNS.items() if label in logs}
    slot = {label: s for label, (_, _, s) in RUNS.items()}
    xs = max((d["step"] for d in logs.values()), key=len)

    def pad(ys, n):
        return ys + [float("nan")] * (n - len(ys))

    def series(f, labels=None, src=None):
        src = src or logs
        return [(label, pad([f(src[label], i) for i in range(len(src[label]["step"]))], len(xs)), slot[label]) for label in (labels or RUNS) if label in src]

    fx = max((d["step"] for d in fines.values()), key=len)

    def fine_series(key, labels=None):
        return [(label, pad(list(fines[label][key]), len(fx)), slot[label]) for label in (labels or RUNS) if label in fines and key in fines[label]]

    def fine_fn(fn, need="pop0", labels=None):
        return [(label, pad(fn(fines[label]), len(fx)), slot[label]) for label in (labels or RUNS) if label in fines and need in fines[label]]

    def rng(d, k, fmt="{:.2f}"):
        if k not in d:
            return "-"
        return f"{fmt.format(min(d[k]))}-{fmt.format(max(d[k]))}"

    charts_winter = [
        line_chart("Bodies every 1,000 steps", "All bodies alive (pop.csv). The floor of a dip is what lives through the winter; e032's pilot is the control.", fx, fine_series("pop"), ymin=0),
        line_chart("The valley's share of the bodies", "Bodies in the valley over all bodies, every 1,000 steps. The valley is a third of the cells; a third would mean the bodies do not prefer it.", fx, fine_fn(lambda f: band_share(f, 0)), ymin=0, ymax=1, percent=True),
    ]
    charts_soil = [
        line_chart("Soil in the valley", "Soil in the valley's cells every 1,000 steps (pop.csv from e033's code on; e032's pilot has no soil column). Flat would mean the soil stays where it started, 43,700 per band.", fx, fine_fn(lambda f: list(f["soil0"]), need="soil0"), ymin=0),
        line_chart("Soil on the ridge", "Soil in the ridge's cells every 1,000 steps. Rising means the ridge holds what the valley eats.", fx, fine_fn(lambda f: list(f["soil2"]), need="soil2"), ymin=0),
    ]

    def summary_row(label):
        d, f = logs[label], fines[label]
        alive = [i for i, p in enumerate(d["pop"]) if p > 0]
        d = {k: [v[i] for i in alive] for k, v in d.items()}
        w = floor_rows(f)
        fmt = lambda k, s: ", ".join(s.format(r[k]) for r in w)
        half = [i for i, t in enumerate(d["step"]) if t > STEPS // 2]
        mean = lambda k: sum(d[k][i] for i in half) / len(half)
        return (f"<tr><td>{label}</td><td>{fmt('pop', '{:,}')}</td><td>{fmt('lin', '{}')}</td><td>{fmt('valley', '{:.0%}')}</td>"
                f"<td>{min(r['peak'] for r in w):,}-{max(r['peak'] for r in w):,}</td><td>{fmt('peak_ridge', '{:.0%}')}</td><td>{mean('plant_intake') / 10_000:.0f}</td><td>{mean('barren'):.0f}</td><td>{mean('soil'):,.0f}</td><td>{mean('fat_stock'):,.0f}</td></tr>")

    rows = "".join(summary_row(label) for label in RUNS if label in logs)

    def band_rows(label):
        folder, run, _ = RUNS[label]
        pl = [r for r in load_rows(f"results/{run}_places.csv", folder) if int(r["step"]) >= STEPS // 2]
        band = json.load(open(os.path.join(folder, f"results/{run}_terrain.json")))["band"]
        soil = list(read_frames(f"results/{run}_soil.jsonl", folder))[-1]["soil"]
        out = ""
        for p in "012":
            rr = [r for r in pl if r["place"] == p]
            m = lambda k, s: s.format(statistics.median(float(r[k]) for r in rr))
            v = sorted((x for x, b in zip(soil, band) if b == int(p)), reverse=True)
            tot = sum(v)
            out += (f"<tr><td>{label if p == '0' else ''}</td><td>{BAND[int(p)]}</td><td>{tot:,.0f}</td><td>{sum(1 for x in v if x < 0.01) / len(v):.0%}</td><td>{sum(v[:len(v) // 10]) / tot if tot else 0:.0%}</td>"
                    f"<td>{m('barren', '{:.1f}')}</td><td>{m('rain', '{:.1f}')}</td><td>{min(int(r['pop']) for r in rr):,}-{max(int(r['pop']) for r in rr):,}</td></tr>")
        return out

    brows = "".join(band_rows(label) for label in RUNS if label in logs)
    tables = data_table(["step", "pop", "births", "deaths_energy", "plant_intake", "regrowth", "rain", "air", "soil", "soil_cells", "deep", "barren", "fat_stock", "biters_any_share", "side_mean", "mass_p50", "lineages"],
                        {f"{label}, seed 9": d for label, d in logs.items()}, every=1)
    TEXT.update(TEXTS)
    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>e034 The soil barely moves - Report</title>
<style>{CSS}</style>
</head>
<body>
<main>
<h1>e034: The soil barely moves</h1>
<p class="sub">Experiment report - 2026-09-05 - the flow of the soil at 0, 0.0001 and 0.001 instead of 0.1, and the rain on the mountains under a still soil: five pilots on seed 9 in the season world against the flow-0.1 pilots of e032 and e033. No batch: the pilots settle where the soil goes.</p>

<section class="tldr">
<h2>TL;DR</h2>
<p>{TEXT["tldr"]}</p>
</section>

<h2>1. Question</h2>
<p>{TEXT["question"]}</p>
<ol>
  <li><strong>The fall does not return:</strong> with the soil still (flow 0) the world stands at e032's floors, because the bodies move with the season and lay their dead where they live.</li>
  <li><strong>The lake is the bodies' now:</strong> the soil lies where the bodies die; the valley keeps most of it, the ridge holds thousands instead of 300.</li>
  <li><strong>A tiny flow (0.001) is a still soil:</strong> the same world as flow 0.</li>
  <li><strong>The ridge's rain is the ridge's soil:</strong> under a still soil the ridge holds more soil than the valley, loses less sun for want of it, and its summer share rises over 17-20%.</li>
</ol>

<h2>2. The laws</h2>
<p>{TEXT["world"]}</p>
{DIAGRAM}
<p><strong>Runs.</strong> {TEXT["runs"]}</p>
<ul class="measures">
  <li><strong>bodies and soil per band</strong> - every 1,000 steps (pop.csv): the winter floors, the valley's share, where the soil is.</li>
  <li><strong>barren, rain per band</strong> - at the equinoxes (places.csv): the sun lost in a band for want of soil, and the rain fallen there, per step.</li>
  <li><strong>bare cells, top 10%</strong> - from the last soil map: the share of a band's cells with less than a step of sun's worth of soil (0.01), and the share of its soil in its richest tenth of cells (10% would be even).</li>
  <li><strong>eaten, soil, fat</strong> - the log's plant intake per step, the soil and the fat in the bodies over the second half.</li>
</ul>

<h2>3. Results</h2>
<div class="tw"><table>
<thead><tr><th>Seed 9, 100,000 steps (five winters)</th><th>winter floors, in order</th><th>lineages of 5+ at the floors</th><th>valley share at the floors</th><th>summer peaks</th><th>ridge share at the peaks</th><th>eaten per step</th><th>sun lost for want of soil, per step (of 164)</th><th>soil</th><th>fat in bodies</th></tr></thead>
<tbody>{rows}</tbody></table></div>
<ol class="verdicts">
{TEXT["verdicts"]}
</ol>

<h3>3.1 {TEXT["h_winter"]}</h3>
<div class="grid2">
{"".join(charts_winter)}
</div>
<p>{TEXT["p_winter"]}</p>

<h3>3.2 {TEXT["h_soil"]}</h3>
<div class="grid2">
{"".join(charts_soil)}
</div>
<div class="tw"><table>
<thead><tr><th>At the end (soil) and the second half's equinoxes (median)</th><th>band</th><th>soil</th><th>bare cells</th><th>top 10% of cells hold</th><th>barren (sun lost per step)</th><th>rain per step</th><th>bodies</th></tr></thead>
<tbody>{brows}</tbody></table></div>
<p>{TEXT["p_soil"]}</p>

<h2>4. Discussion</h2>
{TEXT["discussion"]}

<h2>5. Conclusion and next step</h2>
<p>{TEXT["conclusion"]}</p>

<h2>Appendix: data</h2>
<p>Every log step of the pilot runs; the full data is in <code>results/*.csv</code>, <code>../e032_winter/results/</code> and <code>../e033_wetridge/results/</code>. Build this report with <code>uv run python experiments/e034_stillsoil/report.py</code>.</p>
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


TEXTS = {
    "tldr": ("With the soil still (flow 0, or 0.0001) the soil climbs: it leaves the valley (18,300 of 131,000, 41-56% of its cells bare) and piles on the slope and the ridge, where nothing eats. The world stands at half the bodies (floors 178-462 against 542-825) and loses 52-63% of its sun for want of soil. "
             "The road is the air: the crowd eats in the valley, the rain falls alike everywhere, and only the flow brings the soil back down. 0.001 re-forms the lake at 80% of the floors. The rain on the ridge under a still soil kills the valley. Not kept; no batch."),
    "question": ("What runs downhill in the real world is water; the soil stays where the dead and the dung lie. e019's flow moves the nutrient itself, a tenth of the drop per step, 10-100 times a plant's use, and the lake in the valley and the barren ridge are that shortcut's. "
                 "e018 (flow 0, no terrain) fell because the soil bound where bodies died. With the crowd, the net, the store and the winter's wave: does a still soil stand, where does the soil go, and is the ridge's rain the ridge's soil then?"),
    "world": ("e033's code unchanged: the season world (winter by height at 2, store 5, the grid's side heritable) with the flow rate as the argument. A cell gives flow of its soil to its lower neighbors per step, at most an eighth of the drop. rain flat rains alike on every cell; rain high by height, none at the bottom of the valley."),
    "runs": ("Five pilots on seed 9, 100,000 steps (five winters), one thread each, 17 minutes: flow 0, 0.0001 and 0.001 with rain flat, and flow 0 and 0.001 with rain high. Controls: the flow-0.1 pilots of e032 (rain flat) and e033 (rain high). Measures:"),
    "verdicts": ("<li><span class=\"verdict partly\">Partly</span> No world dies (rain high at flow 0 is a lottery of 22-80), but the floors are 178-462 against 542-825: the soil binds to the high ground, not to trails.</li>"
                 "<li><span class=\"verdict no\">No</span> The valley holds 18,300 of the soil at flow 0 (the control 82,700) and 4,500 at 0.0001; the ridge 61,000-72,000. The soil goes where the bodies are not.</li>"
                 "<li><span class=\"verdict no\">No</span> 0.001 is a lake cell's 0.008 a step, the plant's own order: the valley holds 65,700 again and the floors are 428-670. 0.0001 is the still soil.</li>"
                 "<li><span class=\"verdict partly\">Partly</span> Under a still soil rain high puts 104,400 on the ridge and 20 in the valley (93% bare); the world is a lottery of 22-80. The soil is there and it is idle.</li>"),
    "h_winter": "The world stands at half, and the refuge starves",
    "p_winter": ("The still worlds eat 28-44 per step against 67, and lose 85-104 of the sun's 164 for want of soil against 37-39. The matter sits in the soil (123,000-129,000 of 140,000) instead of the bodies (fat 6,300-12,000 against 38,500). The valley's share at the floors falls to 43-69% from 73-85%, because the refuge is the stripped band; the ridge's summer share doubles to 31-38%, because its soil is there."),
    "h_soil": "The soil climbs: it piles where nothing eats",
    "p_soil": ("The crowd strips a valley cell at 0.01 a step; the rain gives it back 0.0006-0.0009. What the valley eats returns through the air in thirds to every band, and stays where nobody eats it: a plant uses at most the sun's 0.01 and stands full when uneaten, so the ridge (dark in winter) keeps its rain and its dead. "
               "At flow 0 the valley's soil is heaped (the richest tenth of its cells hold 61-80%, the ridge's 17-34%). e018's fall in a milder form: the sun is used only where a body died lately."),
    "discussion": ("<p>The premise held the wrong half. The dead do not lie in this world: the world eats them (e024), and the matter returns through the air, which rains alike on every cell. So a still soil is the rain's soil, uniform, and the crowd's place is stripped of it. The lake in the valley is the flow's, and the valley's crowd lives on the lake: a soil concentrated where the sun is used is worth more bodies than a soil spread where half the year is dark.</p>"
                   "<p>The rate that matters is the plant's: 0.01 per cell per step. Flow 0.001 moves a lake cell's soil at that rate and re-forms the lake with 16,600 left on the ridge (e032's 300), and the bodies use it in summer. The flow at 0.1 is a hundred times more than the ledger needs.</p>"
                   "<p>Not shown: whether a slower carrier changes the winners (one seed, 100,000 steps; the bodies are e032's in every world), and whether a soil that stays feeds anything through the dark. A store in the ground is still the missing law: the ridge's 61,000 of soil under a sun that is out is worth nothing to a body that cannot carry it.</p>"),
    "conclusion": ("Not kept: the flow stays 0.1. For #29 (water as the carrier): the carrier's job is to bring the matter back to the sunlit crowd, at the order of the plant's use (0.001 of a lake cell per step, a hundredth of the flow now); the return road from the bodies is the air. A slower carrier leaves the ridge a soil the bodies use in summer; holding the ridge through the winter needs a store in the ground."),
}


if __name__ == "__main__":
    main()
