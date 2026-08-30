#!/usr/bin/env python3
"""Build report.html for e014.

Charts: matplotlib, exported as SVG and inlined. Diagram: hand-written SVG.
Run from the repo root: uv run python experiments/e014_body_space/report.py
"""
import base64
import csv
import gzip
import html
import io
import json
import os
import statistics
from collections import Counter, defaultdict

import matplotlib
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator

matplotlib.use("svg")

HERE = os.path.dirname(os.path.abspath(__file__))
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4"]  # fixed slot order
LINEAGE_PALETTE = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#7b61ff", "#00a3c4", "#c94c4c", "#6aa84f", "#b8860b", "#8e44ad", "#e67e22"]
NONE_COLOR = "#898781"

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

E012 = os.path.join(HERE, "..", "e012_two_places")
E013 = os.path.join(HERE, "..", "e013_facing_space")
# Worlds of this experiment: label -> (run prefix, world size, widths, seeds). Places are named by their width.
WORLDS = {
    "grass and trees": ("128_sigma8-1", 128, (8, 1), [1, 2, 3, 4]),
    "grass and edge": ("128_sigma8-2", 128, (8, 2), [1, 2, 3, 4]),
    "grass and shrubs": ("128_sigma8-4", 128, (8, 4), [1, 2, 3, 4]),
    "grass and trees, 256": ("256_sigma8-1", 256, (8, 1), [1, 2, 3, 4]),
    "grass and edge, 256": ("256_sigma8-2", 256, (8, 2), [1, 2]),
}
# The same world with space at the cell level (e013) and without space (e012), seeds 1-4: label -> (run prefix, folder, widths).
REFS = {
    "grass and trees, e013": ("128_sigma8-1", E013, (8, 1)),
    "grass and trees, e012": ("128_sigma8-1", E012, (8, 1)),
}
PLACE_NAME = {8: "grass (width 8)", 4: "shrubs (width 4)", 2: "edge (width 2)", 1: "trees (width 1)", 0: "beyond the patches"}
PLACE_COLOR = {8: SERIES[0], 4: SERIES[3], 2: SERIES[1], 1: SERIES[2], 0: INK}
WORLD_COLOR = {"grass and trees": SERIES[2], "grass and edge": SERIES[1], "grass and shrubs": SERIES[3], "grass and trees, 256": SERIES[4], "grass and edge, 256": SERIES[0]}
KIND_COLOR = {1: SERIES[0], 2: SERIES[1], 3: SERIES[3], 4: SERIES[2]}
CONFIRM_STEPS = 5000
MAIN = "grass and trees"
VIEWER_WORLD = "grass and trees, 256"
VIEWER_SEED = 1
if os.environ.get("E014_SMOKE"):  # build against the 128 runs only, to test the script before the 256 runs finish
    WORLDS["grass and trees, 256"] = ("128_sigma8-1", 128, (8, 1), [1, 2, 3, 4])
    WORLDS["grass and edge, 256"] = ("128_sigma8-2", 128, (8, 2), [1, 2])
LAST_STEP = 1_000_000


def seeds_of(w):
    return WORLDS[w][3]


# ---------- data ----------

def load_csv(path, folder=HERE):
    with open(os.path.join(folder, path)) as f:
        rows = list(csv.DictReader(f))
    return {k: [float(r[k]) for r in rows] for k in rows[0]}


def load_rows(path, folder=HERE):
    with open(os.path.join(folder, path)) as f:
        return list(csv.DictReader(f))


def load_places(run, folder=HERE):
    """places.csv split by place: {width: {column: [values]}}."""
    rows = load_rows(f"results/{run}_places.csv", folder)
    out = {}
    for r in rows:
        p = int(float(r["place"]))
        d = out.setdefault(p, defaultdict(list))
        for k, v in r.items():
            d[k].append(float(v))
    return out


def lineage_rows(run, folder=HERE):
    by = defaultdict(list)
    for r in load_rows(f"results/{run}_lineages.csv", folder):
        by[int(r["lineage"])].append(r)
    return by


def lineage_stats(run, folder=HERE):
    """Per lineage: first and last step seen as a group, max size."""
    first, last, size = {}, {}, defaultdict(int)
    for r in load_rows(f"results/{run}_lineages.csv", folder):
        i, s = int(r["lineage"]), int(r["step"])
        first.setdefault(i, s)
        last[i] = s
        size[i] = max(size[i], int(r["size"]))
    return first, last, size


def home_of(r):
    """The kind of place most of a lineage's members stand in at one detection: 0 (first width), 1 (second), or None."""
    p0, p1 = int(r["p0"]), int(r["p1"])
    if p0 + p1 == 0:
        return None
    return 0 if p0 >= p1 else 1


def lineage_places(run):
    """Per lineage: detections with home in the first kind, in the second kind, and with both kinds holding
    at least 10% of the members. A lineage that moved home has 20+ detections (20,000 steps) of each home;
    a shared one has 20+ detections with both."""
    out = {}
    for lid, rows in lineage_rows(run).items():
        h0 = sum(1 for r in rows if home_of(r) == 0)
        h1 = sum(1 for r in rows if home_of(r) == 1)
        both = sum(1 for r in rows if min(int(r["p0"]), int(r["p1"])) >= 0.1 * int(r["size"]))
        out[lid] = dict(h0=h0, h1=h1, both=both, moved=h0 >= 20 and h1 >= 20, shared=both >= 20,
                        steps=int(rows[-1]["step"]) - int(rows[0]["step"]) + CONFIRM_STEPS, agent_steps=sum(int(r["size"]) for r in rows))
    return out


def hunter_lineages(run, folder=HERE, min_steps=20_000, min_bite=2.0, key="bite"):
    out = []
    for lid, rows in lineage_rows(run, folder).items():
        h = [r for r in rows if float(r[key]) >= min_bite]
        if not h:
            continue
        span = int(h[-1]["step"]) - int(h[0]["step"]) + CONFIRM_STEPS
        if span < min_steps:
            continue
        peak = max(h, key=lambda r: int(r["size"]))
        m, p = float(peak["meat"]), float(peak["plant"])
        out.append(dict(id=lid, span=span, size=int(peak["size"]), mass=float(peak["mass"]), bite=float(peak["bite"]), diet=m / (m + p) if m + p > 0 else 0.0,
                        front=float(peak.get("shell_front", 0)), back=float(peak.get("shell_back", 0))))
    out.sort(key=lambda d: -d["span"])
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
    ax.xaxis.set_major_formatter(kfmt)
    ax.set_xlabel(xlabel, loc="right")
    ax.margins(x=0)
    return fig, ax


def legend_above(ax, n):
    ax.legend(loc="lower left", bbox_to_anchor=(0, 1.0), ncols=n, handlelength=1.2, borderaxespad=0, columnspacing=1.2)


def figure(title, subtitle, svg):
    return f"""
<figure class="fig">
  <figcaption><strong>{html.escape(title)}</strong><span>{html.escape(subtitle)}</span></figcaption>
  {svg}
</figure>"""


def finish(ax, ymin, ymax, top, percent, n_legend):
    if ymin is not None:
        ax.set_ylim(ymin, max(ymax if ymax is not None else top * 1.12, ymin + 1e-9))
    fine = percent and ax.get_ylim()[1] < 0.02
    ax.yaxis.set_major_formatter((lambda y, _p: f"{y:.2%}" if fine else f"{y:.0%}") if percent else kfmt)
    ax.yaxis.set_major_locator(MaxNLocator(4))
    legend_above(ax, n_legend)


def place_chart(title, subtitle, places, world, key_fn, refs=None, ymin=0, ymax=None, percent=False):
    """One thin line per seed and place, colored by place, for one world. refs: {label: (value, color)} as dashed lines."""
    fig, ax = new_axes()
    top = 0
    for p in WORLDS[world][2]:
        for k, s in enumerate(seeds_of(world)):
            d = places[world][s][p]
            ys = key_fn(d)
            top = max(top, max(ys))
            ax.plot(d["step"], ys, color=PLACE_COLOR[p], linewidth=1.1, alpha=0.85, label=PLACE_NAME[p] if k == 0 else None)
    for label, (v, color) in (refs or {}).items():
        ax.axhline(v, color=color, linestyle="--", linewidth=1, label=label)
        top = max(top, v)
    finish(ax, ymin, ymax, top, percent, 2)
    return figure(title, subtitle, to_svg(fig))


def narrow_chart(title, subtitle, places, worlds, key_fn, ymin=0, ymax=None, percent=False, refs=None):
    """The narrow place of several worlds on one chart: one thin line per seed, colored by world."""
    fig, ax = new_axes()
    top = 0
    for w in worlds:
        p = WORLDS[w][2][1]
        for k, s in enumerate(seeds_of(w)):
            d = places[w][s][p]
            ys = key_fn(d)
            top = max(top, max(ys))
            ax.plot(d["step"], ys, color=WORLD_COLOR[w], linewidth=1.1, alpha=0.85, label=f"{PLACE_NAME[p].split(' (')[0]} (width {p})" if k == 0 else None)
    for label, (v, color) in (refs or {}).items():
        ax.axhline(v, color=color, linestyle="--", linewidth=1, label=label)
        top = max(top, v)
    finish(ax, ymin, ymax, top, percent, 2)
    return figure(title, subtitle, to_svg(fig))


def world_chart(title, subtitle, logs, key_fn, worlds, colors, ymin=0, ymax=None, percent=False):
    """One thin line per seed, colored by world; one legend entry per world."""
    fig, ax = new_axes()
    top = 0
    for w in worlds:
        for k, s in enumerate(seeds_of(w)):
            ys = key_fn(logs[w][s])
            if ys is None:
                continue
            top = max(top, max(ys))
            ax.plot(logs[w][s]["step"], ys, color=colors[w], linewidth=1.1, alpha=0.85, label=w if k == 0 else None)
    finish(ax, ymin, ymax, top, percent, 3)
    return figure(title, subtitle, to_svg(fig))


def sides_chart(title, subtitle, places, world, place):
    """Hardness of the front, the back and the sides on one place, one line per seed and side."""
    fig, ax = new_axes()
    top = 0
    for key, color, label in (("shell_front", SERIES[1], "front"), ("shell_back", SERIES[0], "back")):
        for k, s in enumerate(seeds_of(world)):
            d = places[world][s][place]
            ys = d[key]
            top = max(top, max(ys))
            ax.plot(d["step"], ys, color=color, linewidth=1.1, alpha=0.85, label=label if k == 0 else None)
    finish(ax, 0, None, top, False, 2)
    return figure(title, subtitle, to_svg(fig))


def color_slots(run):
    first, _, _ = lineage_stats(run)
    return {lid: k % len(LINEAGE_PALETTE) for k, lid in enumerate(sorted(first, key=first.get))}


def timeline_chart(title, subtitle, run, events):
    """Every lineage as a band: size over time, colored by confirmation order. Events as marks."""
    slot = color_slots(run)
    by = lineage_rows(run)
    fig, ax = new_axes(size=(13, 3.6))
    ax.set_ylabel("agents in the lineage")
    for lid, rows in by.items():
        xs = [int(r["step"]) for r in rows]
        ys = [int(r["size"]) for r in rows]
        ax.fill_between(xs, 0, ys, color=LINEAGE_PALETTE[slot[lid]], alpha=0.35, linewidth=0)
        ax.plot(xs, ys, color=LINEAGE_PALETTE[slot[lid]], linewidth=1.0)
    marks = {"split": ("v", SERIES[1]), "merge": ("^", SERIES[2]), "extinct": ("x", SERIES[3]), "birth": ("o", SERIES[0])}
    for ev, (m, c) in marks.items():
        xs = [int(r["step"]) for r in events if r["event"] == ev]
        ys = [int(r["size"]) for r in events if r["event"] == ev]
        if xs:
            ax.scatter(xs, ys, marker=m, s=18, color=c, label=f"{ev} ({len(xs)})", zorder=3, linewidths=1)
    ax.set_ylim(0, None)
    ax.yaxis.set_major_locator(MaxNLocator(4))
    ax.yaxis.set_major_formatter(kfmt)
    legend_above(ax, 4)
    return figure(title, subtitle, to_svg(fig))


def data_table(cols, rows_by_name, every=10):
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
.wide {{ margin: 12px 0; }}
.diagram {{ margin: 12px 0; background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 12px 16px 8px; color: var(--ink); }}
.diagram figcaption {{ color: var(--ink2); font-size: 13px; margin-top: 4px; }}
.cards {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(215px, 1fr)); gap: 14px; margin: 6px 0 10px; }}
.card {{ margin: 0; display: flex; gap: 10px; align-items: flex-start; }} .card svg {{ flex: none; }} .card figcaption {{ font-size: 12.5px; line-height: 1.4; color: var(--ink2); }} .card strong {{ color: var(--ink); }}
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
.viewer {{ background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 14px; display: grid; grid-template-columns: 1fr; gap: 10px; }}
.viewer .canvases {{ display: grid; grid-template-columns: 2fr 1fr; gap: 10px; align-items: start; }}
.viewer canvas {{ width: 100%; height: auto; image-rendering: pixelated; border-radius: 4px; }}
.viewer .bar {{ display: flex; gap: 10px; align-items: center; font-size: 13px; color: var(--ink2); flex-wrap: wrap; }}
.viewer input[type=range] {{ flex: 1; }}
.viewer button, .viewer select {{ font: inherit; font-size: 13px; padding: 2px 10px; }}
.viewer .lin {{ display: inline-block; padding: 0 6px; border-radius: 3px; color: #fff; font-size: 12px; margin-right: 4px; }}
.viewer .sw {{ display: inline-block; width: 11px; height: 11px; border-radius: 2px; vertical-align: -1px; margin: 0 3px 0 6px; }}
.viewer .sw.dot {{ background: #666; position: relative; }} .viewer .sw.dot::after {{ content: ""; position: absolute; left: 4px; top: 4px; width: 3px; height: 3px; background: #fff; }}
.viewer .sw.front {{ background: #666; border-top: 2px solid #fff; }}
@media (max-width: 700px) {{ .viewer .canvases {{ grid-template-columns: 1fr; }} }}
"""

DIAGRAM = """
<figure class="diagram">
<svg viewBox="0 0 800 372" role="img" aria-label="The space law of e013 rewritten at the resolution of the body. Left: a block of world cells, each drawn as 4x4 sub-cells; three bodies hold exactly the sub-cells their grids fill, turned to their facing, and a small body stands inside the gap of a larger one; no two bodies share a sub-cell; each digestive cell eats from the world cell under it. Right: a move is one sub-cell along the facing; where a cell of the mover would enter a cell of another body the two faces meet: the softer face breaks if the mover's muscle in that line exceeds its hardness (3 per contiguous hard cell behind the face, else 1); the move happens only if the way is clear afterwards; a push whose muscle exceeds the other's mass shoves it one sub-cell." style="max-width:100%;height:auto;display:block">
<g fill="none" stroke="currentColor" stroke-width="1.2" font-size="12" font-family="system-ui, sans-serif">
  <text x="20" y="20" fill="currentColor" stroke="none" font-weight="600">a body holds its own cells; the world is drawn at the body's resolution</text>
  <!-- 3x3 world cells of 4x4 sub-cells, 10 px per sub-cell -->
  <g stroke="currentColor" stroke-opacity="0.25">
    <path d="M 40,46 v 120 M 50,46 v 120 M 60,46 v 120 M 70,46 v 120 M 80,46 v 120 M 90,46 v 120 M 100,46 v 120 M 110,46 v 120 M 120,46 v 120 M 130,46 v 120 M 140,46 v 120 M 150,46 v 120 M 160,46 v 120"/>
    <path d="M 40,46 h 120 M 40,56 h 120 M 40,66 h 120 M 40,76 h 120 M 40,86 h 120 M 40,96 h 120 M 40,106 h 120 M 40,116 h 120 M 40,126 h 120 M 40,136 h 120 M 40,146 h 120 M 40,156 h 120 M 40,166 h 120"/>
  </g>
  <rect x="40" y="46" width="120" height="120" stroke-dasharray="4 3"/>
  <line x1="80" y1="46" x2="80" y2="166" stroke-dasharray="4 3"/><line x1="120" y1="46" x2="120" y2="166" stroke-dasharray="4 3"/>
  <line x1="40" y1="86" x2="160" y2="86" stroke-dasharray="4 3"/><line x1="40" y1="126" x2="160" y2="126" stroke-dasharray="4 3"/>
  <g stroke="none">
    <!-- a two-mouthed body: two corners of digestive cells six columns apart, one row of hard below the right one -->
    <rect x="50" y="66" width="30" height="10" fill="#1baf7a"/><rect x="50" y="76" width="10" height="10" fill="#1baf7a"/>
    <rect x="100" y="66" width="30" height="10" fill="#1baf7a"/><rect x="120" y="76" width="10" height="10" fill="#1baf7a"/>
    <!-- a small body inside its gap -->
    <rect x="80" y="76" width="20" height="10" fill="#eda100"/><rect x="90" y="86" width="10" height="10" fill="#eda100"/>
    <!-- a tooth facing east, below -->
    <rect x="60" y="126" width="10" height="10" fill="#2a78d6"/><rect x="40" y="126" width="20" height="10" fill="#eb6834"/><rect x="40" y="136" width="20" height="10" fill="#1baf7a"/>
  </g>
  <path d="M 66,58 L 66,64" stroke="var(--s1)" stroke-width="2" marker-end="url(#arrow)"/>
  <path d="M 72,131 L 78,131" stroke="var(--s1)" stroke-width="2" marker-end="url(#arrow)"/>
  <text x="176" y="72" fill="currentColor" stroke="none">a world cell is 4x4 sub-cells (dashed);</text>
  <text x="176" y="88" fill="currentColor" stroke="none">a body fills the sub-cells its grid</text>
  <text x="176" y="104" fill="currentColor" stroke="none">holds, turned to its facing (arrow)</text>
  <text x="176" y="128" fill="currentColor" stroke="none">a small body is small: it stands in</text>
  <text x="176" y="144" fill="currentColor" stroke="none">the gap of another; a gut cell eats</text>
  <text x="176" y="160" fill="currentColor" stroke="none">from the world cell under it</text>
  <text x="20" y="196" fill="currentColor" stroke="none">no two bodies share a sub-cell; a move is one sub-cell along the facing (a second with probability speed)</text>
  <text x="20" y="214" fill="currentColor" stroke="none">turn left / right: the grid rotates about its center, if the sub-cells it would newly hold are free</text>
  <text x="20" y="232" fill="currentColor" stroke="none">a child is placed where its cells find free sub-cells, one to eight from its parent, or it is lost</text>

  <text x="430" y="20" fill="currentColor" stroke="none" font-weight="600">a move into another body's cell is a push, face to face</text>
  <g stroke="currentColor" stroke-opacity="0.25">
    <path d="M 440,46 v 80 M 450,46 v 80 M 460,46 v 80 M 470,46 v 80 M 480,46 v 80 M 490,46 v 80 M 500,46 v 80 M 510,46 v 80 M 520,46 v 80 M 530,46 v 80 M 540,46 v 80"/>
    <path d="M 440,46 h 100 M 440,56 h 100 M 440,66 h 100 M 440,76 h 100 M 440,86 h 100 M 440,96 h 100 M 440,106 h 100 M 440,116 h 100 M 440,126 h 100"/>
  </g>
  <g stroke="none">
    <!-- mover: tooth facing east: hard tip at column 3, two muscle behind, gut below -->
    <rect x="470" y="76" width="10" height="10" fill="#2a78d6"/><rect x="450" y="76" width="20" height="10" fill="#eb6834"/><rect x="450" y="86" width="30" height="10" fill="#1baf7a"/>
    <!-- other: a soft gut body to the east, its cell right ahead of the tip -->
    <rect x="480" y="66" width="30" height="30" fill="#1baf7a"/>
    <!-- a hard wall body further east -->
    <rect x="510" y="56" width="10" height="50" fill="#2a78d6"/><rect x="520" y="66" width="20" height="30" fill="#1baf7a"/>
  </g>
  <path d="M 462,70 L 478,70" stroke="var(--s1)" stroke-width="2" marker-end="url(#arrow)"/>
  <text x="556" y="62" fill="currentColor" stroke="none">the tip's face meets the cell ahead:</text>
  <text x="556" y="78" fill="currentColor" stroke="none">hardness 3 per contiguous hard cell</text>
  <text x="556" y="94" fill="currentColor" stroke="none">behind a hard face, else 1; the softer</text>
  <text x="556" y="110" fill="currentColor" stroke="none">face breaks if the muscle in the line</text>
  <text x="556" y="126" fill="currentColor" stroke="none">exceeds its hardness (here 2 &gt; 1)</text>
  <text x="440" y="150" fill="currentColor" stroke="none">the move happens only if every cell of the mover finds its</text>
  <text x="440" y="166" fill="currentColor" stroke="none">next sub-cell free; muscle over the other's mass shoves it</text>
  <text x="440" y="182" fill="currentColor" stroke="none">one sub-cell; the pusher pays the move whether or not it moves</text>
  <text x="20" y="266" fill="currentColor" stroke="none">facing as in e013: only the front pushes; the policy sees the world from the body (food under it; food and crowd ahead, behind, left, right)</text>
  <text x="20" y="284" fill="currentColor" stroke="none">at most 16 body cells fit in a world cell, so a cell feeds at most 16 gut cells (0.32 per step): e011's crowd of 45-77 bodies at a cell cannot return</text>
  <text x="20" y="318" fill="currentColor" stroke="none">occupancy: one index per sub-cell (16 times e013's cells, 1 MB at 128), a count of held sub-cells per world cell (the crowd a body sees)</text>
  <text x="20" y="336" fill="currentColor" stroke="none">everything else (two kinds of place, costs, materials, contact rule, mating, lineages) is e013's</text>
</g>
<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="var(--s1)"/></marker></defs>
</svg>
<figcaption>Figure 1. e013's space law at the resolution of the body. Left: the world is drawn in sub-cells (4x4 per world cell) and a body holds exactly the sub-cells its grid fills, so a small body is small and stands in the gap of a larger one. Right: a push is e010's contact rule between the two faces that meet; the move happens only if the way clears. Nothing names a tooth or a wall.</figcaption>
</figure>
"""


def read_frames(path):
    with open(os.path.join(HERE, path)) as f:
        for line in f:
            yield json.loads(line)


def load_bodies(run):
    out = {}
    with open(os.path.join(HERE, f"results/{run}_bodies.jsonl")) as f:
        for line in f:
            d = json.loads(line)
            out[d["id"]] = d["cells"]
    return out


def pack_frames(path, confirmed_at, data, every=1, limit=None):
    """Frames packed small into `data`: food as 4-bit nibbles; agents as x, y (sub-cells, 2 bytes each), body id (3 bytes), lineage (2 bytes), facing (1 byte).
    Returns one index entry per frame (step, patches, offsets and lengths into `data`).
    A lineage id is written only once the lineage is confirmed (else 0)."""
    out = []
    used = set()
    n = 0
    for i, fr in enumerate(read_frames(path)):
        if i % every:
            continue
        food = fr["food"]
        nib = bytes((food[j] << 4) | food[j + 1] for j in range(0, len(food), 2))
        ag = bytearray()
        for x, y, b, _d, lin, f in fr["agents"]:
            lin = lin if confirmed_at.get(lin, 10**12) <= fr["step"] else 0
            ag += bytes((x & 255, x >> 8, y & 255, y >> 8, b & 255, (b >> 8) & 255, b >> 16, lin & 255, lin >> 8, f))  # 3-byte body id: a run can have 100,000+ distinct (damaged) bodies
            used.add(b)
        out.append({"s": fr["step"], "p": fr["patches"], "fo": len(data), "fl": len(nib), "ao": len(data) + len(nib), "al": len(ag)})
        data += nib
        data += ag
        n += 1
        if limit and n >= limit:
            break
    return out, used


VIEWER_JS = r"""
(async function(){
  // One gzip'd blob: 4-byte header length, JSON header, then the frame bytes (a 256x256 world is 50 KB per frame raw).
  const raw = Uint8Array.from(atob(document.getElementById('frames').textContent), c => c.charCodeAt(0));
  const all = new Uint8Array(await new Response(new Blob([raw]).stream().pipeThrough(new DecompressionStream('gzip'))).arrayBuffer());
  const hlen = all[0] | (all[1] << 8) | (all[2] << 16) | (all[3] << 24);
  const data = JSON.parse(new TextDecoder().decode(all.subarray(4, 4 + hlen)));
  const bytes = all.subarray(4 + hlen);
  const bodies = data.bodies, KC = data.kindColors, PAL = data.palette, NONE = data.none;
  const cv = document.getElementById('world'), ctx = cv.getContext('2d');
  const zv = document.getElementById('zoom'), zctx = zv.getContext('2d');
  // W x H world cells of food; SW x SH sub-cells (4 per cell) where the bodies are. S: pixels per sub-cell on the world; ZN world cells in the zoom.
  const SUB = 4, W = data.w, H = data.h, SW = W * SUB, SH = H * SUB, S = cv.width / SW, ZN = 24, ZS = zv.width / (ZN * SUB), REC = 10;
  const off = document.createElement('canvas'); off.width = W; off.height = H;
  const octx = off.getContext('2d'), img = octx.createImageData(W, H);
  ctx.imageSmoothingEnabled = false; zctx.imageSmoothingEnabled = false;
  const slider = document.getElementById('scrub'), stepLbl = document.getElementById('steplbl'), linLbl = document.getElementById('linlbl');
  const playBtn = document.getElementById('play'), mode = document.getElementById('mode');
  let frames = data.long, i = 0, timer = null, zx = (SW / 2 - ZN * SUB / 2) | 0, zy = (SH / 2 - ZN * SUB / 2) | 0;
  const stats = {}, rotated = {};
  function color(lin){ return lin ? PAL[data.slots[lin] || 0] : NONE; }
  // The body grid in the world frame: the front row (row 0) turned to point where the body faces (0 north, 1 south, 2 east, 3 west).
  function toWorld(k, f){ const r = k >> 3, c = k & 7, m = 7; let r2, c2;
    if (f === 0) { r2 = r; c2 = c; } else if (f === 1) { r2 = m - r; c2 = m - c; } else if (f === 2) { r2 = c; c2 = m - r; } else { r2 = m - c; c2 = r; }
    return r2 * 8 + c2; }
  // The cells a body holds in the world frame, as [column, row, kind] triples, and their bounding box.
  function rot(id, f){ const key = id + ':' + f; if (rotated[key]) return rotated[key];
    const cells = bodies[id] || '', out = [], bb = [8, -1, 8, -1];
    for (let k = 0; k < 64; k++) { const v = cells.charCodeAt(k) - 48; if (v > 0) { const w = toWorld(k, f), r = w >> 3, c = w & 7; out.push([c, r, v]);
      bb[0] = Math.min(bb[0], r); bb[1] = Math.max(bb[1], r); bb[2] = Math.min(bb[2], c); bb[3] = Math.max(bb[3], c); } }
    return rotated[key] = { cells: out, bb: bb }; }
  // Same rules as the simulation, in the body frame: per side, per line, the tip is the outermost cell; a hard tip has hardness 3 per
  // contiguous hard cell; force is the muscle in the line. Bite = largest force behind a hard tip on the front (side 0); shell = mean
  // hardness of touchable tips; extent = rows and columns the body spans.
  function stat(id){
    if (stats[id]) return stats[id];
    const cells = bodies[id] || ''; let mass = 0, sensor = 0, bite = 0, hsum = 0, hn = 0, r0 = 8, r1 = -1, c0 = 8, c1 = -1;
    for (let k = 0; k < 64; k++) { const v = cells.charCodeAt(k) - 48; if (v > 0) { mass++; r0 = Math.min(r0, k >> 3); r1 = Math.max(r1, k >> 3); c0 = Math.min(c0, k & 7); c1 = Math.max(c1, k & 7); } if (v === 3) sensor++; }
    const at = (side, line, k) => side === 0 ? k * 8 + line : side === 1 ? (7 - k) * 8 + line : side === 2 ? line * 8 + (7 - k) : line * 8 + k;
    for (let side = 0; side < 4; side++) for (let line = 0; line < 8; line++) {
      let force = 0, k0 = -1;
      for (let k = 0; k < 8; k++) { const v = cells.charCodeAt(at(side, line, k)) - 48; if (v === 2) force++; if (v > 0 && k0 < 0) k0 = k; }
      if (k0 < 0) continue;
      let h = 1;
      if (cells.charCodeAt(at(side, line, k0)) - 48 === 1) { h = 0; for (let k = k0; k < 8 && cells.charCodeAt(at(side, line, k)) - 48 === 1; k++) h += 3; }
      hsum += h; hn++;
      if (side === 0 && h > 1 && force > bite) bite = force;
    }
    return stats[id] = { mass: mass, bite: bite, shell: hn ? hsum / hn : 0, sensor: sensor, fwd: mass ? r1 - r0 + 1 : 0, side: mass ? c1 - c0 + 1 : 0 };
  }
  function foodAt(food, c){ return (c % 2 === 0) ? (food[c >> 1] >> 4) : (food[c >> 1] & 15); }
  function paintFood(target, food, x0, y0, n, cell){ // x0, y0: the zoom's corner in sub-cells; cell: pixels per world cell
    const wx = Math.floor(x0 / SUB), wy = Math.floor(y0 / SUB), ox = (x0 % SUB) * cell / SUB, oy = (y0 % SUB) * cell / SUB;
    for (let y = 0; y <= n; y++) for (let x = 0; x <= n; x++) {
      const c = ((wy + y) % H) * W + ((wx + x) % W);
      const g = 40 + foodAt(food, c) * 12;
      target.fillStyle = 'rgb(' + (g * 0.35 | 0) + ',' + g + ',' + (g * 0.45 | 0) + ')';
      target.fillRect(x * cell - ox, y * cell - oy, cell, cell);
    }
  }
  // Each patch as a ring of radius 2 sigma around its center (on the torus: drawn up to 4 times when it wraps). Wide: blue; narrow: aqua.
  function paintPatches(fr){
    const CS = S * SUB;
    for (const [px, py, sg] of fr.p) {
      ctx.strokeStyle = sg >= 4 ? '#2a78d6' : '#1baf7a'; ctx.lineWidth = 1.5; ctx.setLineDash([4, 4]);
      const r = Math.max(2 * sg, 1.5) * CS;
      for (const ox of [0, -W, W]) for (const oy of [0, -H, H]) {
        const cx = (px + 0.5 + ox) * CS, cy = (py + 0.5 + oy) * CS;
        if (cx + r < 0 || cy + r < 0 || cx - r > cv.width || cy - r > cv.height) continue;
        ctx.beginPath(); ctx.arc(cx, cy, r, 0, 2 * Math.PI); ctx.stroke();
      }
      ctx.setLineDash([]);
    }
  }
  function draw(){
    const fr = frames[i]; const food = bytes.subarray(fr.fo, fr.fo + fr.fl), ag = bytes.subarray(fr.ao, fr.ao + fr.al);
    const px = img.data;
    for (let c = 0; c < W * H; c++) {
      const g = 40 + foodAt(food, c) * 12;
      px[c * 4] = g * 0.35; px[c * 4 + 1] = g; px[c * 4 + 2] = g * 0.45; px[c * 4 + 3] = 255;
    }
    octx.putImageData(img, 0, 0);
    ctx.drawImage(off, 0, 0, cv.width, cv.height);
    paintFood(zctx, food, zx, zy, ZN, ZS * SUB);
    const counts = {}, teeth = {}, armor = {}, eyes = {}, masses = {}, fwd = {}, side = {}; let n = 0;
    const inZoom = [], ZW = ZN * SUB;
    for (let k = 0; k < ag.length; k += REC) {
      const x = ag[k] | (ag[k + 1] << 8), y = ag[k + 2] | (ag[k + 3] << 8), id = ag[k + 4] | (ag[k + 5] << 8) | (ag[k + 6] << 16), lin = ag[k + 7] | (ag[k + 8] << 8), f = ag[k + 9];
      const st = stat(id), body = rot(id, f);
      ctx.fillStyle = color(lin);
      for (const [c, r] of body.cells) ctx.fillRect(((x + c) % SW) * S, ((y + r) % SH) * S, S, S);
      if (st.bite > 0) { ctx.fillStyle = '#fff'; const bb = body.bb; ctx.fillRect(((x + (bb[2] + bb[3]) / 2) % SW) * S - 1, ((y + (bb[0] + bb[1]) / 2) % SH) * S - 1, 2, 2); }
      const dx = (x - zx + SW) % SW, dy = (y - zy + SH) % SH;
      if (dx < ZW + 8 && dy < ZW + 8) inZoom.push([dx, dy, id, lin, f, st, body]);
      counts[lin] = (counts[lin] || 0) + 1; teeth[lin] = (teeth[lin] || 0) + st.bite; armor[lin] = (armor[lin] || 0) + st.shell; eyes[lin] = (eyes[lin] || 0) + st.sensor; masses[lin] = (masses[lin] || 0) + st.mass; fwd[lin] = (fwd[lin] || 0) + st.fwd; side[lin] = (side[lin] || 0) + st.side; n++;
    }
    // The zoom: each cell of a body on its sub-cell, the block kind inside a frame of the lineage color, a white edge on the front of the body's box.
    for (const [dx, dy, id, lin, f, st, body] of inZoom) {
      for (const [c, r, v] of body.cells) { zctx.fillStyle = color(lin); zctx.fillRect((dx + c) * ZS, (dy + r) * ZS, ZS, ZS); zctx.fillStyle = KC[v]; zctx.fillRect((dx + c) * ZS + 1, (dy + r) * ZS + 1, ZS - 2, ZS - 2); }
      const bb = body.bb, x0 = (dx + bb[2]) * ZS, y0 = (dy + bb[0]) * ZS, LW = (bb[3] - bb[2] + 1) * ZS, LH = (bb[1] - bb[0] + 1) * ZS;
      zctx.fillStyle = '#fff';
      if (f === 0) zctx.fillRect(x0, y0, LW, 2); else if (f === 1) zctx.fillRect(x0, y0 + LH - 2, LW, 2); else if (f === 2) zctx.fillRect(x0 + LW - 2, y0, 2, LH); else zctx.fillRect(x0, y0, 2, LH);
      if (st.bite > 0) { const cx = x0 + LW / 2, cy = y0 + LH / 2; zctx.fillRect(cx - 2, cy - 2, 4, 4); }
    }
    paintPatches(fr);
    zctx.strokeStyle = 'rgba(255,255,255,0.35)'; zctx.lineWidth = 1;
    const ox = (zx % SUB) * ZS, oy = (zy % SUB) * ZS;
    for (let k = 0; k <= ZN; k++) { zctx.beginPath(); zctx.moveTo(k * ZS * SUB - ox, 0); zctx.lineTo(k * ZS * SUB - ox, zv.height); zctx.stroke(); zctx.beginPath(); zctx.moveTo(0, k * ZS * SUB - oy); zctx.lineTo(zv.width, k * ZS * SUB - oy); zctx.stroke(); }
    ctx.strokeStyle = '#fff'; ctx.lineWidth = 1.5; ctx.strokeRect(zx * S, zy * S, ZW * S, ZW * S);
    stepLbl.textContent = 'step ' + fr.s.toLocaleString() + ' - ' + n + ' agents';
    const keys = Object.keys(counts).map(Number).sort((a, b) => counts[b] - counts[a]).slice(0, 12);
    linLbl.innerHTML = keys.map(l => '<span class="lin" style="background:' + color(l) + '">' + (l ? 'lineage ' + l : 'none') + ': ' + counts[l]
      + ' (mass ' + (masses[l] / counts[l]).toFixed(0) + ', ' + (fwd[l] / counts[l]).toFixed(1) + ' long x ' + (side[l] / counts[l]).toFixed(1) + ' wide, bite ' + (teeth[l] / counts[l]).toFixed(1) + ', shell ' + (armor[l] / counts[l]).toFixed(1) + ', eyes ' + (eyes[l] / counts[l]).toFixed(1) + ')</span>').join('');
  }
  function densest(){ // start the zoom where the agents are, not in the desert
    const ag = bytes.subarray(frames[0].ao, frames[0].ao + frames[0].al); const n = {}, ZW = ZN * SUB;
    for (let k = 0; k < ag.length; k += REC) { const x = ag[k] | (ag[k + 1] << 8), y = ag[k + 2] | (ag[k + 3] << 8); const key = ((x / ZW) | 0) + ',' + ((y / ZW) | 0); n[key] = (n[key] || 0) + 1; }
    const best = Object.keys(n).sort((a, b) => n[b] - n[a])[0]; if (!best) return;
    zx = +best.split(',')[0] * ZW; zy = +best.split(',')[1] * ZW;
  }
  function setMode(){ frames = data[mode.value]; i = 0; slider.max = frames.length - 1; densest(); draw(); }
  function tick(){ i = (i + 1) % frames.length; draw(); }
  const speed = document.getElementById('speed');
  function interval(){ return (mode.value === 'clip' ? 250 : 600) / +speed.value; }
  playBtn.onclick = function(){ if (timer) { clearInterval(timer); timer = null; playBtn.textContent = 'Play'; } else { timer = setInterval(tick, interval()); playBtn.textContent = 'Pause'; } };
  speed.onchange = function(){ if (timer) { clearInterval(timer); timer = setInterval(tick, interval()); } };
  slider.oninput = function(){ i = +slider.value; draw(); };
  mode.onchange = function(){ if (timer) playBtn.onclick(); setMode(); };
  cv.onclick = function(e){ const r = cv.getBoundingClientRect(); const ZW = ZN * SUB; zx = (Math.floor((e.clientX - r.left) / r.width * SW - ZW / 2) + SW) % SW; zy = (Math.floor((e.clientY - r.top) / r.height * SH - ZW / 2) + SH) % SH; draw(); };
  setMode();
})();
"""


def gallery(world, seed, picks):
    """picks: [(lineage id, name, what the shape does)]. The most common body of each lineage at its peak, on the 8x8 grid, front up."""
    run = f"{WORLDS[world][0]}_seed{seed}"
    widths = WORLDS[world][2]
    by = lineage_rows(run)
    bodies = load_bodies(run)
    frames = list(read_frames(f"results/{run}_long.jsonl"))
    cards = []
    for lid, name, what in picks:
        rows = by[lid]
        peak = max(rows, key=lambda r: int(r["size"]))
        span = int(rows[-1]["step"]) - int(rows[0]["step"]) + CONFIRM_STEPS
        frame = min(frames, key=lambda fr: abs(fr["step"] - int(peak["step"])))
        c = Counter(a[2] for a in frame["agents"] if a[4] == lid)
        cells = bodies[c.most_common(1)[0][0]]
        rects = "".join(f'<rect x="{(i % 8) * 11}" y="{(i // 8) * 11}" width="10" height="10" fill="{KIND_COLOR[int(k)]}"/>' for i, k in enumerate(cells) if k != "0")
        m, pl = float(peak["meat"]), float(peak["plant"])
        meat = m / (m + pl) if m + pl > 0 else 0
        p0, p1 = sum(int(r["p0"]) for r in rows), sum(int(r["p1"]) for r in rows)
        home = f"{p0 / max(p0 + p1, 1):.0%} on {PLACE_NAME[widths[0]].split(' (')[0]}"
        cards.append(f"""<figure class="card"><svg viewBox="-1 -1 89 89" width="120" height="120" role="img" aria-label="{html.escape(name)}"><rect x="-1" y="-1" width="89" height="89" fill="var(--cell)"/>{rects}<line x1="-1" y1="-0.5" x2="88" y2="-0.5" stroke="var(--ink2)" stroke-width="1.5" stroke-dasharray="3 2"/></svg>
<figcaption><strong>{html.escape(name)}</strong><br>lineage {lid}: {span:,} steps, {int(peak["size"]):,} agents at its peak, {home}<br>mass {float(peak["mass"]):.0f} on {float(peak["foot"]):.1f} cells: hard {float(peak["hard"]):.0f}, muscle {float(peak["muscle"]):.0f}, digestive {float(peak["digestive"]):.0f}; bite {float(peak["bite"]):.1f}, front {float(peak["shell_front"]):.1f} / back {float(peak["shell_back"]):.1f}; meat {meat:.0%}<br>{html.escape(what)}</figcaption></figure>""")
    return f"""<figure class="diagram"><div class="cards">{"".join(cards)}</div>
<figcaption>Figure 2. Bodies of lineages that prospered in {world}, seed {seed}: the most common body of the lineage at its peak, on the 8x8 grid a body grows on, front up (the dashed edge). Blue: hard, orange: muscle, green: digestive, yellow: sensor. "Cells" is the world cells the body covers; "front / back" the mean hardness of the tips on those sides.</figcaption></figure>"""


def main():
    logs, events, places = {}, {}, {}
    for w, (run, _, _, seeds) in WORLDS.items():
        logs[w] = {s: load_csv(f"results/{run}_seed{s}_log.csv") for s in seeds}
        events[w] = {s: load_rows(f"results/{run}_seed{s}_events.csv") for s in seeds}
        places[w] = {s: load_places(f"{run}_seed{s}") for s in seeds}
    rlogs = {w: {s: load_csv(f"results/{run}_seed{s}_log.csv", folder) for s in [1, 2, 3, 4]} for w, (run, folder, _) in REFS.items()}
    rplaces = {w: {s: load_places(f"{run}_seed{s}", folder) for s in [1, 2, 3, 4]} for w, (run, folder, _) in REFS.items()}

    def med(x):
        x = [v for v in x if v == v]
        return statistics.median(x) if x else float("nan")

    def half(d, key):
        n = len(d["step"])
        return d[key][n // 2:]

    def summarize(w, s):
        log = logs[w][s]
        run = f"{WORLDS[w][0]}_seed{s}"
        widths = WORLDS[w][2]
        pl = places[w][s]
        first, last, _ = lineage_stats(run)
        life = [last[i] - first[i] + CONFIRM_STEPS for i in first]
        per_step = Counter(int(r["step"]) for r in load_rows(f"results/{run}_lineages.csv"))
        last_step = int(log["step"][-1])
        lp = lineage_places(run)
        hunters = hunter_lineages(run)
        hunters_any = hunter_lineages(run, key="bite_any")
        d = dict(pop=med(log["pop"]), pop_min=min(log["pop"]), extinct=last_step < LAST_STEP, sps=med(log["steps_per_sec"]), sps_min=min(log["steps_per_sec"]),
                 crossers=med(half(log, "crossers")), crossers_max=max(log["crossers"]), pop_none=med(half(log, "pop_none")),
                 lineages=med([per_step.get(t, 0) for t in range(1000, last_step + 1, 1000)]), ids=len(first), life=med(life) if life else 0,
                 moved=sum(1 for v in lp.values() if v["moved"]), shared=sum(1 for v in lp.values() if v["shared"]),
                 hunters=len(hunters), hunters_any=len(hunters_any), hunter_span=hunters[0]["span"] if hunters else 0,
                 meat=sum(log["meat_intake"]) / max(sum(log["plant_intake"]) + sum(log["meat_intake"]), 1),
                 blocked=med(half(log, "blocked")), shoves=med(half(log, "shoves")), turns_blocked=med(half(log, "turns_blocked")), no_room=med(half(log, "births_no_room")),
                 foot=med(half(log, "foot_mean")), len_fwd=med(half(log, "len_fwd")), len_side=med(half(log, "len_side")), cover=med(half(log, "cover")),
                 contacts=med([c / max(p, 1) / 10_000 for c, p in zip(half(log, "contacts"), half(log, "pop"))]), births=med(half(log, "births")),
                 forward=med(half(log, "forward")), turns=med([a + b for a, b in zip(half(log, "left"), half(log, "right"))]), stay=med(half(log, "stay")),
                 biters=med(half(log, "biters_share")), biters_any=med(half(log, "biters_any_share")), wasted=med(half(log, "wasted")))
        for k, p in (("a", widths[0]), ("b", widths[1])):
            q = pl[p]
            n = len(q["step"])
            h = slice(n // 2, n)
            d[f"pop_{k}"] = med(q["pop"][h])
            d[f"pop_{k}_min"] = min(q["pop"])
            d[f"mass_{k}"] = med(q["mass"][h])
            d[f"hard_{k}"] = med(q["hard"][h])
            d[f"hard_{k}_max"] = max(q["hard"])
            d[f"muscle_{k}"] = med(q["muscle"][h])
            d[f"digestive_{k}"] = med(q["digestive"][h])
            d[f"biters_{k}"] = med(q["biters"][h])
            d[f"biters_{k}_max"] = max(q["biters"])
            d[f"meat_{k}"] = sum(q["meat_intake"][h]) / max(sum(q["plant_intake"][h]) + sum(q["meat_intake"][h]), 1)
            d[f"movers_{k}"] = med([m / max(p_, 1) for m, p_ in zip(q["movers"][h], q["pop"][h])])
            d[f"lineages_{k}"] = med(q["lineages"][h])
            d[f"cover_{k}"] = med(q["cover"][h])
            d[f"foot_{k}"] = med(q["foot"][h])
            d[f"front_{k}"] = med(q["shell_front"][h])
            d[f"back_{k}"] = med(q["shell_back"][h])
        return d

    S = {w: {s: summarize(w, s) for s in seeds_of(w)} for w in WORLDS}

    def rplace(w, p, key):
        """A reference world's per-place value: median over seeds of the median over the second half."""
        if key not in rplaces[w][1][p]:
            return float("nan")
        return med([med(rplaces[w][s][p][key][len(rplaces[w][s][p][key]) // 2:]) for s in [1, 2, 3, 4]])

    def rsum(w, key):
        if key not in rlogs[w][1]:
            return float("nan")
        return med([med(half(rlogs[w][s], key)) for s in [1, 2, 3, 4]])

    R = "grass and trees, e012"
    R13 = "grass and trees, e013"
    refs_hard = {"grass, e012": (rplace(R, 8, "hard"), PLACE_COLOR[8]), "trees, e012": (rplace(R, 1, "hard"), PLACE_COLOR[1])}
    refs_biters = {"grass, e012": (rplace(R, 8, "biters"), PLACE_COLOR[8]), "trees, e012": (rplace(R, 1, "biters"), PLACE_COLOR[1])}
    refs_mass = {"grass, e012": (rplace(R, 8, "mass"), PLACE_COLOR[8]), "trees, e012": (rplace(R, 1, "mass"), PLACE_COLOR[1])}
    refs_pop = {"grass, e012": (rplace(R, 8, "pop"), PLACE_COLOR[8]), "trees, e012": (rplace(R, 1, "pop"), PLACE_COLOR[1])}

    narrow = ["grass and trees", "grass and edge", "grass and shrubs"]
    charts = {}
    charts["hard"] = place_chart("Hard cells per body, by place", "Mean over the bodies standing on each kind of place (grass and trees, 128, one line per seed). Dashed: e012, the same world without space.", places, MAIN, lambda d: d["hard"], refs=refs_hard)
    charts["biters"] = place_chart("Bodies with a bite, by place", "Share of bodies on each place with a hard tip and muscle behind it on the front. Dashed: e012 (a bite on any side).", places, MAIN, lambda d: d["biters"], refs=refs_biters, percent=True)
    charts["mass"] = place_chart("Mass per body, by place", "Mean cells per body on each place. Dashed: e012.", places, MAIN, lambda d: d["mass"], refs=refs_mass, ymax=66)
    charts["pop"] = place_chart("Population by place", "Bodies standing on each kind of place. Dashed: e012, where 45-77 bodies could share one tree cell; e013 held 41-65 on the trees.", places, MAIN, lambda d: d["pop"], refs=refs_pop)
    charts["cover"] = place_chart("Cover, by place", "Share of the place's sub-cells held by a body. e013 counted whole cells (a body held 16 sub-cells per cell); here a body holds only its own.", places, MAIN, lambda d: d["cover"], percent=True, ymax=1.0)
    charts["foot"] = place_chart("World cells under a body, by place", "Mean world cells a body's cells lie in (1 to 9). e013's winner lay over 1.4-2.1; a body at the four corners of its grid lies over four or five.", places, MAIN, lambda d: d["foot"], ymin=1, ymax=6)
    charts["narrow_hard"] = narrow_chart("Hard cells per body on the narrow place, three widths", "The narrow place of each 128 world (trees, edge, shrubs), one line per seed. Which width keeps an arms race once a cell holds one body.", places, narrow, lambda d: d["hard"])
    charts["narrow_biters"] = narrow_chart("Bodies with a bite on the narrow place, three widths", "Share of the bodies on the narrow place with a tooth on the front.", places, narrow, lambda d: d["biters"], percent=True)
    charts["narrow_pop"] = narrow_chart("Population on the narrow place, three widths", "Bodies standing on the narrow place of each world. e012's trees held 620-1,050.", places, narrow, lambda d: d["pop"])
    charts["narrow_meat"] = narrow_chart("Meat share of intake on the narrow place, three widths", "Energy from broken cells of other bodies over all energy eaten there, per window.", places, narrow, lambda d: [m / max(m + p, 1e-9) for m, p in zip(d["meat_intake"], d["plant_intake"])], percent=True)
    charts["contacts"] = world_chart("Contacts per body per step", "Bodies pressed by a move, per body per step, per log window. e012: 2-4 with trees (a move into a tree cell pushed into dozens of bodies); e013: 0.1-0.3.", logs, lambda l: [c / max(p, 1) / 10_000 for c, p in zip(l["contacts"], l["pop"])], list(WORLDS), WORLD_COLOR)
    charts["no_room"] = world_chart("Children lost for want of room", "Share of children that found no free sub-cells within eight of the parent and were lost. e013: 81-90%.", logs, lambda l: l["births_no_room"], list(WORLDS), WORLD_COLOR, percent=True, ymax=1.0)
    charts["forward"] = world_chart("Forward actions", "Share of decisions that are a forward move (the only action that can touch another body). The rest is stay or turn.", logs, lambda l: l["forward"], list(WORLDS), WORLD_COLOR, percent=True, ymax=1.0)
    charts["births"] = world_chart("Births per 10,000 steps", "Children born (with room). e013: 29,000-40,000; e012: 200,000-392,000.", logs, lambda l: l["births"], list(WORLDS), WORLD_COLOR)
    charts["blocked"] = world_chart("Moves that did not happen", "Share of forward actions blocked (a cell of the mover found its next sub-cell taken). e013: 78-94%.", logs, lambda l: l["blocked"], list(WORLDS), WORLD_COLOR, percent=True, ymax=1.0)
    charts["actions"] = world_chart("Turning", "Share of decisions that are a turn (left or right). A turn costs nothing and most do not happen.", logs, lambda l: [a + b for a, b in zip(l["left"], l["right"])], list(WORLDS), WORLD_COLOR, percent=True, ymax=1.0)
    charts["lineages"] = world_chart("Lineages alive", "Confirmed lineages at each log step. e013: 1-8 at 128, 9-21 at 256; e012: 9-13 and 19-50.", logs, lambda l: l["lineages"], list(WORLDS), WORLD_COLOR)
    charts["crossers"] = world_chart("Crossers", "Share of living bodies standing in a kind of place other than the one they were born in. e012: 0.1-1.6%.", logs, lambda l: l["crossers"], list(WORLDS), WORLD_COLOR, percent=True)

    viewer_run = f"{WORLDS[VIEWER_WORLD][0]}_seed{VIEWER_SEED}"
    timeline = timeline_chart(f"Lineages over time ({VIEWER_WORLD}, seed {VIEWER_SEED})", "Each colored band is one lineage, height = agents in it; marks are events at the size they were logged with.", viewer_run, events[VIEWER_WORLD][VIEWER_SEED])

    first, _, _ = lineage_stats(viewer_run)
    bodies = load_bodies(viewer_run)
    data = bytearray()
    long_frames, used_l = pack_frames(f"results/{viewer_run}_long.jsonl", first, data, every=4)
    clip_frames, used_c = pack_frames(f"results/{viewer_run}_clip.jsonl", first, data, every=4, limit=50)
    legend = " ".join(f'<span class="sw" style="background:{KIND_COLOR[k]}"></span>{name}' for k, name in ((1, "hard"), (2, "muscle"), (3, "sensor"), (4, "digestive")))
    vw = WORLDS[VIEWER_WORLD][1]
    viewer_data = {"w": vw, "h": vw, "long": long_frames, "clip": clip_frames, "bodies": {str(b): bodies[b] for b in used_l | used_c},
                   "kindColors": {str(k): v for k, v in KIND_COLOR.items()}, "palette": LINEAGE_PALETTE, "none": NONE_COLOR,
                   "slots": {str(k): v for k, v in color_slots(viewer_run).items()}}
    header = json.dumps(viewer_data, separators=(",", ":")).encode()
    blob = base64.b64encode(gzip.compress(len(header).to_bytes(4, "little") + header + bytes(data), 9)).decode()

    def rng(w, key, fmt):
        vals = [S[w][s][key] for s in seeds_of(w)]
        vals = [v for v in vals if v == v]
        if not vals:
            return "-"
        lo, hi = min(vals), max(vals)
        return fmt(lo) if fmt(lo) == fmt(hi) else f"{fmt(lo)}-{fmt(hi)}"

    def row(label, key, fmt, refkey=None, by_place=False):
        """A row with one cell per world (grass / narrow when by_place) and one per reference world."""
        cells = "".join(f"<td>{rng(w, key + '_a', fmt)} / {rng(w, key + '_b', fmt)}</td>" if by_place else f"<td>{rng(w, key, fmt)}</td>" for w in WORLDS)
        f_ = lambda v: "-" if v != v else fmt(v)
        if refkey and by_place:
            refs = "".join(f"<td>{f_(rplace(r, REFS[r][2][0], refkey))} / {f_(rplace(r, REFS[r][2][1], refkey))}</td>" for r in REFS)
        elif refkey:
            refs = "".join(f"<td>{f_(rsum(r, refkey))}</td>" for r in REFS)
        else:
            refs = "".join("<td>-</td>" for r in REFS)
        return f"<tr><td>{label}</td>{cells}{refs}</tr>"

    n0 = lambda v: f"{v:,.0f}"
    d1 = lambda v: f"{v:.1f}"
    p1 = lambda v: f"{v:.1%}"
    p0 = lambda v: f"{v:.0%}"
    summary = ("<thead><tr><th>Measure (range over seeds; grass / narrow where two)</th>" + "".join(f"<th>{w}</th>" for w in WORLDS) + "".join(f"<th>{r}</th>" for r in REFS) + "</tr></thead><tbody>"
               + row("Population, median", "pop", n0, "pop")
               + row("Population by place, median", "pop", n0, "pop", by_place=True)
               + row("Cover by place (share of sub-cells held), median", "cover", p0, by_place=True)
               + row("World cells under a body by place, median", "foot", d1, "foot", by_place=True)
               + row("Contacts per body per step, median", "contacts", lambda v: f"{v:.2f}")
               + row("Births per 10,000 steps, median", "births", n0, "births")
               + row("Mass per body by place, median", "mass", d1, "mass", by_place=True)
               + row("Hard cells per body by place, median", "hard", d1, "hard", by_place=True)
               + row("Bodies with a bite on the front by place, median share", "biters", p1, "biters", by_place=True)
               + "<tr><td>Hardness of the front / back, narrow place, median</td>" + "".join(f"<td>{rng(w, 'front_b', d1)} / {rng(w, 'back_b', d1)}</td>" for w in WORLDS) + "".join("<td>-</td>" for r in REFS) + "</tr>"
               + row("Meat share of intake by place, second half", "meat", p1, by_place=True)
               + row("Moves blocked, median share of forward actions", "blocked", p0, "blocked")
               + row("Shoves, median share of forward actions", "shoves", p1)
               + row("Children lost for want of room, median share", "no_room", p0, "births_no_room")
               + row("Crossers, median share of all bodies", "crossers", p1, "crossers")
               + row("Lineages alive, median", "lineages", n0, "lineages")
               + row("Hunter lineages (front bite &ge; 2 for 20,000+ steps)", "hunters", n0)
               + row("Steps per second, median", "sps", n0, "steps_per_sec")
               + "</tbody>")

    tables = data_table(["step", "place", "pop", "mass", "hard", "muscle", "digestive", "bite", "shell", "biters", "cover", "foot", "shell_front", "shell_back", "plant_intake", "meat_intake", "lineages", "movers"],
                        {f"{w}, seed {s}, {PLACE_NAME[p]} (every 100,000 steps)": places[w][s][p] for w in WORLDS for s in seeds_of(w) for p in WORLDS[w][2]}, every=10)
    tables += data_table(["step", "pop", "births", "deaths_broken", "cells_broken", "mass_mean", "hard_mean", "biters_share", "biters_any_share", "blocked", "shoves", "turns_blocked", "births_no_room", "foot_mean", "len_fwd", "len_side", "cover", "contacts", "wasted", "meat_intake", "plant_intake", "crossers", "lineages", "steps_per_sec"],
                         {f"{w}, seed {s}, whole world (every 100,000 steps)": logs[w][s] for w in WORLDS for s in seeds_of(w)}, every=10)

    text = TEXT
    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>e014 Space at the resolution of the body - Report</title>
<style>{CSS}</style>
</head>
<body>
<main>
<h1>e014: Space at the resolution of the body</h1>
<p class="sub">Experiment report - 2026-08-30 - e013's world with its space law rewritten: bodies hold their own cells on a world drawn at the resolution of the body cell (4x4 sub-cells per world cell), contact is the meeting of real cells, facing is kept. Grass with trees, edge or shrubs at 128x128 (four seeds each), grass with trees and with the edge at 256x256; 1,000,000 steps</p>

<section class="tldr">
<h2>TL;DR</h2>
<p>{text["tldr"]}</p>
</section>

<h2>1. Question</h2>
<p>{text["question"]}</p>
<ol>
  <li><strong>Contact comes back.</strong> On the narrow place, second half, bodies touch another body more than once per step on average (e012: 2-4 on the trees; e013: 0.1-0.3), in at least three seeds of four at width 1.</li>
  <li><strong>The jam clears.</strong> Blocked moves below 50% of forward actions and children lost for want of room below 50% of births (e013: 78-94% and 81-90%), in every world.</li>
  <li><strong>Teeth and armor return with contact, and point forward.</strong> On at least one narrow width (1, 2 or 4) the arms race stands: hard above 5 per body and over 10% of bodies with a bite on the narrow place, second half, in at least two seeds of four; and among bodies with a bite on any side, at least half have it on the front.</li>
  <li><strong>The world stands at a bounded cost.</strong> No extinction; population above 500; at least 300 steps per second with twelve runs sharing the machine.</li>
</ol>

<h2>2. The world</h2>
<p>{text["world"]}</p>
{DIAGRAM}
<p>{text["runs"]}</p>
<ul class="measures">
  <li><strong>Bite</strong>: the largest force (muscle in the line) behind a hard tip on the front; <strong>bite any</strong>: on any side (e012's bite).</li>
  <li><strong>Hardness of a side</strong>: mean hardness of the touchable tips on the front, the back, or the two sides of the body grid.</li>
  <li><strong>Cells</strong> a body lies over: world cells under its cells (1-9); <strong>long</strong> and <strong>wide</strong>: cells the body spans along and across the facing.</li>
  <li><strong>Cover</strong>: share of a place's sub-cells held by a body. <strong>Contacts</strong>: bodies pressed per move, per body per step.</li>
  <li><strong>Blocked</strong>: forward actions that did not move the body; <strong>shoves</strong>: bodies moved by a push; <strong>turns blocked</strong>; <strong>children lost</strong> for want of free sub-cells next to the parent.</li>
  <li>e013's measures: bite on the front and on any side, hardness per side, per place (population, body means, intake, lineages, movers), crossers, hunter lineages, snapshots (position in sub-cells and facing).</li>
</ul>

<h2>3. Results</h2>
<div class="tw"><table>{summary}</table></div>
<ol class="verdicts">
<li><span class="verdict {text["c1"]}">{text["l1"]}</span> {text["v1"]}</li>
<li><span class="verdict {text["c2"]}">{text["l2"]}</span> {text["v2"]}</li>
<li><span class="verdict {text["c3"]}">{text["l3"]}</span> {text["v3"]}</li>
<li><span class="verdict {text["c4"]}">{text["l4"]}</span> {text["v4"]}</li>
</ol>

<h3>3.1 {text["h1"]}</h3>
<div class="grid2">
{charts["pop"]}{charts["cover"]}
</div>
<div class="grid2">
{charts["mass"]}{charts["foot"]}
</div>
<p>{text["r1"]}</p>

<h3>3.2 {text["h2"]}</h3>
<div class="grid2">
{charts["narrow_hard"]}{charts["narrow_biters"]}
</div>
<div class="grid2">
{charts["narrow_pop"]}{charts["narrow_meat"]}
</div>
<p>{text["r2"]}</p>

<h3>3.3 {text["h3"]}</h3>
<div class="grid2">
{charts["contacts"]}{charts["blocked"]}
</div>
<div class="grid2">
{charts["forward"]}{charts["no_room"]}
</div>
{gallery(VIEWER_WORLD, VIEWER_SEED, GALLERY)}
<p>{text["r3"]}</p>

<h3>3.4 Watching the world</h3>
<div class="wide">{timeline}</div>
<div class="viewer">
  <div class="canvases">
    <canvas id="world" width="1024" height="1024"></canvas>
    <canvas id="zoom" width="480" height="480"></canvas>
  </div>
  <div class="bar">
    <button id="play">Play</button>
    <select id="mode"><option value="long">Long view: every 20,000 steps</option><option value="clip">Clip: every 4th step from 600,000</option></select>
    <select id="speed"><option value="1">Slow</option><option value="2">Normal</option><option value="4">Fast</option></select>
    <span id="steplbl"></span>
  </div>
  <div class="bar"><input id="scrub" type="range" min="0" max="0" value="0"></div>
  <div class="bar" id="linlbl"></div>
  <div class="bar" id="legend">Blocks: {legend} <span class="sw front"></span> the front (white edge) <span class="sw dot"></span> has a bite on the front</div>
  <div class="bar">Left: the whole {vw}x{vw} world at the resolution of the body ({vw * 4}x{vw * 4} sub-cells), every cell a body holds colored by its lineage (gray: none), a white dot on bodies with a bite. Green: food; dashed rings are the patches (blue: grass, width 8; aqua: trees, width 1; radius two widths). Click to move the white box. Right: the box at 24x24 world cells, each body drawn cell by cell where it stands, turned the way it faces, with a white edge on its front, damage included. Labels: agents per lineage, then mean mass, cells spanned along x across the facing, bite, shell, and sensor cells (eyes). {VIEWER_WORLD}, seed {VIEWER_SEED}.</div>
</div>
<p>{text["viewer"]}</p>
<div class="grid2">{charts["lineages"]}{charts["births"]}</div>

<h2>4. Discussion</h2>
{text["discussion"]}

<h2>5. Conclusion and next step</h2>
<p>{text["conclusion"]}</p>

<h2>Appendix: data</h2>
<p>Every 100,000th record; full logs in <code>results/*_log.csv</code>, per place in <code>results/*_places.csv</code>, lineages in <code>results/*_lineages.csv</code>, events in <code>results/*_events.csv</code>, agents every 100,000 steps in <code>results/*_agents.csv</code>, snapshots in <code>results/*_{{long,clip,bodies}}.jsonl</code>. Reference runs are read from <code>../e013_facing_space/results</code> and <code>../e012_two_places/results</code>. Build this report with <code>uv run python experiments/e014_body_space/report.py</code>.</p>
{tables}
</main>
<script id="frames" type="application/octet-stream">{blob}</script>
<script>{VIEWER_JS}</script>
</body>
</html>
"""
    out = os.path.join(HERE, "report.html")
    with open(out, "w") as f:
        f.write(page)
    print(f"wrote {out} ({os.path.getsize(out)//1024} KB)")


# Lineages that prospered in the viewer run: (lineage id, name, what the shape does). Filled after the runs.
GALLERY = [
]

TEXT = {
    "question": "e013 gave bodies a front and a size in the world at the level of a world cell (one cell per 4x4 quarter of the grid that holds a cell, no two bodies in a cell). Bodies became readable and reach paid, but the world jammed: a 3-cell body blocked a whole cell, 78-94% of moves and 81-90% of children were blocked for want of room, and contact fell from 2-4 to 0.1-0.3 touches per body per step; with it went meat, teeth, armor and the arms race, at every width and in every seed. The crowd was the premise of the arms race. We keep space and facing and give space the resolution of the body: a body holds exactly the sub-cells its grid fills, a small body is small, bodies pass each other and nest, and contact is the meeting of real cells. Does contact come back where food is dense, does the jam clear, do teeth and armor return with it and point forward, and does the world still stand? One thing the resolution cannot give back: at most 16 body cells fit in a world cell, so a cell feeds at most 16 gut cells (0.32 per step); e011's crowd of 45-77 bodies at a tree cell is not possible in a world with size.",
    "world": "Everything is e013's (128x128 or 256x256 on a torus, drifting food patches of two widths, bodies of 8x8 cells in five kinds grown from the genome, e010's contact rule, a cell that costs what it holds, 0.032 per body per step, a facing per body, only the front pushes, four actions: stay, forward, turn left, turn right) with the space law rewritten (Figure 1). Occupancy is kept per sub-cell (4x4 per world cell, 16 times e013's cells): a body anchored at a sub-cell holds the sub-cells its world-frame grid fills, and no two bodies share one. A move is one sub-cell along the facing (a second with probability speed). Every cell of the mover whose next sub-cell is held by another body meets the cell there face to face: the softer face breaks if the mover's muscle in that line exceeds its hardness (3 per contiguous hard cell behind the face, else 1); a body still in the way is shoved one sub-cell if the muscle on it exceeds its mass and it has room; the move happens if every cell of the mover finds its next sub-cell free. A turn happens if the rotated grid's cells find free sub-cells. A child is placed at the first anchor one to eight sub-cells from its parent's, in the four directions, where its cells find room, else it is lost. Food stays per world cell and a digestive cell eats from the cell under it. Moving costs 0.001 per block per body cell moved, whether or not the move happens; a world cell is four of them now. The policy's inputs are e013's, seen through the body's bounding box (food under it; food and crowd one and two cells ahead, behind, left, right; energy).",
    "runs": "<strong>Runs.</strong> At 128x128, two patches of each kind: grass and trees (widths 8 and 1), grass and the edge (8 and 2), grass and shrubs (8 and 4), seeds 1-4 each, twelve runs at once on one machine, one thread each. At 256x256, eight patches of each kind: grass and trees (seeds 1-4) and grass and the edge (seeds 1-2), six at once. 1,000,000 steps. Reference: e013 (space at the cell level) and e012 (no space) on the same worlds and seeds at 128. We record e013's measures and:",
    "tldr": "e013's space law, rewritten at the resolution of the body: a body holds exactly the sub-cells its grid fills (4x4 per world cell), a small body is small, bodies nest, and contact is the meeting of real cells. The world stands (1,380-2,510 bodies at 128, 290-430 steps/s), births are four times e013's, the narrow places hold three to four times e013's bodies, and still nobody touches anybody: 0.06-0.22 contacts per body per step at every width in every seed (e012: 2-4), no bite, no hard cell, no meat, no hunter lineage, 62-92% of moves blocked. The resolution was not the problem; the motive is. In e012 a move always succeeded and a push into fifty bodies was its free by-product; once bodies take up space, a push is a failed move that costs the mover, a body without a tooth gains nothing from it, and the winning policies stay and turn (forward is 7-15% of decisions). Selection keeps only reach, and reach alone makes plants: the body that wins everywhere is four to eight digestive cells at the four corners of its grid, a constellation lying over four or five world cells that hardly moves. 256: (filled from the runs). Next: charge a move by the distance moved (work is force times distance), folded into ground and friction (#16), so that pushing into a body is free to try and contact can again be a by-product of moving.",
    "c1": "no", "l1": "No", "v1": "0.06-0.22 contacts per body per step on the whole world and no more on the narrow places (the log counts bodies pressed per move; forward actions are 7-15% of decisions, and 62-92% of them press on somebody, so nearly every contact is a blocked move). e013: 0.08-0.33; e012: 2.1-3.7 with trees.",
    "c2": "no", "l2": "No", "v2": "Blocked moves 62-92% of forward actions (e013: 78-94%) in every world; children lost 47-63% (e013: 81-90%). Births are back, four to five times e013's (134,000-202,000 per 10,000 steps against 29,000-40,000; e012: 200,000-392,000), because a small child finds a spot where a 2x2 block did not; the moves are not, because the winning body is 7 cells wide and its every cell must find its next sub-cell free.",
    "c3": "no", "l3": "No, at every width", "v3": "Trees (width 1), edge (2), shrubs (4): hard cells per body 0.00-0.14, bodies with a bite 0% on the front and 0-0.3% on any side, meat 0.000% of the intake, no hunter lineage, in all twelve runs; the front and the back of a body are equally soft (1.00-1.06). Cells broken: 0-24 per 10,000 steps (one window of 221 in seed 3 with trees, a passing body with muscle). 256: (filled from the runs).",
    "c4": "yes", "l4": "Yes", "v4": "No extinction; population 1,380-2,510 at 128, never below 1,250; 290-430 steps per second with twelve runs on one machine (e013: 710-1,550; the sub-cell physics costs about twice per body and there are more bodies). 256: (filled from the runs).",
    "h1": "A constellation over four world cells; the narrow places fill up",
    "r1": "The grass holds 1,210-1,410 bodies at 128 (e013: 1,100-1,320) with 14-15% of its sub-cells held; the trees 169-192 (e013: 41-65; e012: 622-1,050) at 59-62%, the edge 540-636 (e013: 148-216), the shrubs 1,100-1,212 (e013: 424-442). Regrowth lost to the cap falls from 83-88 to 67-68 of the 164 per step with trees, from 69-79 to 41-42 with the edge, from 49-55 to 4 with shrubs: three or four times the bodies eat at a rich cell now. The body that wins, in all twelve runs, is 4-8 digestive cells at the four corners of its 8x8 grid (Figure 2): it spans 7x7 body cells with 6-9 of them, its four corners lie in four different world cells (3.9-5.2 world cells under a body; e013's winner lay over 1.4-2.1), and 1-24% of the bodies stand wholly inside another body's box. Intake per digestive cell is 0.008-0.010 per step (e013: 0.013-0.015): a corner shares its world cell with the corners of its neighbors, so reach no longer pays per cell, but the body with the most corners wins. Mass 6-9 (10th-90th percentile 2-12); sensor and muscle 0.00-0.05 cells per body.",
    "h2": "No tooth at any width",
    "r2": "No width keeps an arms race, as in e013 and for the same reason with the room taken away: a body presses on another 0.06-0.22 times per step. Nearly every forward action is a push, but a forward action is 7-15% of the decisions (e013: 6-22%): bodies stay 1-55% of the time and turn 30-90% (a turn is free and 46-92% of them do not happen, so turning is what a policy does instead of moving). A push costs the mover 0.001 per cell whether or not it moves, and without a tooth it gains nothing, so the policies that survive do not push; a tooth needs a hard tip, two muscle cells behind it and a policy that pushes into bodies, and none of the three is paid for alone. Births are four times e013's, so the tries were there (1.3-2.0 million per run) and none found it. The narrow places hold grazers of 4.3-5.5 cells (the grass 7.2-8.9): a rich cell feeds a smaller body with fewer corners. Lineages alive: 1-3 (e013: 1-8; e012: 6-15), peaks of 7-17, with 20-200 splits and as many extinctions per run: one shape sweeps, splits into near-clones and they replace each other.",
    "h3": "Contact is a failed move; the viewer reads a constellation",
    "r3": "The charts of contact, blocked moves, forward actions and children lost say one thing: bodies move little, and when they move they press on somebody, and nothing comes of it. Moves blocked do not fall over the run in any world (the winning body is seven cells wide), children lost stay at half, and shoves are zero (nobody has muscle). Figure 2 shows the bodies of the lineages that prospered in the 256 world: corners, and corners with a second cell, front up; the viewer reads a body as four dots of one color with other bodies standing between them.",
    "viewer": "Grass and trees, 256, seed 1. (filled from the run.) ",
    "discussion": "<p>The resolution did what it promised: a small body is small, a corner body holds three sub-cells instead of sixteen, bodies pass and nest, children find room four times as often, the narrow places hold three to four times the bodies and waste a third less regrowth. What it did not give back is the thing the arms race ran on. In e011 and e012 a body had no size, a move never failed, and every move into a rich cell was a push into fifty bodies: contact was a free by-product of moving, and a random tooth was paid on its first step. With space of any resolution, a push is a move that failed and cost the mover 0.001 per cell, a body without a tooth gains nothing from it, and the policies that win are the ones that do not push: forward is 7-15% of decisions, turning (free, and mostly blocked) takes the rest. A tooth needs three things at once (a hard tip, two muscle cells behind it, a policy that pushes into bodies) and no step of the way pays. Space and the arms race are in tension: contact must be sought, and nothing in the world rewards seeking it before the tooth exists.</p><p>What selection kept is reach, and reach alone makes plants. The body that wins in every run is four cells at the four corners of its grid, one in each of four world cells, a constellation 7 cells across that moves once in ten steps and is blocked eight times in ten when it does; other bodies stand between its cells. e013's winner was the same idea at the cell level (four cells in four quarters); here the grid is used to its edges. The world is a lawn of sessile grazers with far-flung mouths, and the viewer reads it: dots of one color in a square, not a body with a front.</p><p>The lever, then, is not the food (the spill would spread the trees over more cells and feed more corner bodies; it would not make one push) and not more room, but the cost law of moving. Charging a push that moves nothing as if it had moved is what makes pushing a losing action and turning a substitute for it. In the real world work is force times distance: a body pressing on another spends little until something gives. Charging the move by the distance moved is a law about the world, not about a trait; it makes pushing into a body free to try, and it tests whether contact as a by-product of moving, e011's engine, can exist in a world with space. It belongs with ground and friction (#16), where the cost of moving is rewritten anyway (by the cells that touch the ground). If contact comes back with it, the tooth has its first step paid; if it does not, the tension is deeper than a cost and the next question is what a body gains from another body without a tooth.</p>",
    "conclusion": "Space at the resolution of the body keeps what e013 won (readable bodies, reach) and gives back room (births four times e013's, narrow places three to four times as full) but not contact: 0.06-0.22 touches per body per step at every width in every seed, no tooth, no armor, no hunter, one to three lineages alive. Contact is a failed move now, and a body without a tooth has no reason to fail one; selection keeps reach alone, and the winning body is four cells at the four corners of its grid, a constellation over four world cells that hardly moves. Next: charge a move by the distance moved, folded into ground and friction (#16), so that pushing into a body costs nothing until something gives; the spill (a full cell that feeds its neighbors) stays on the table for the trees' waste.",
}

if __name__ == "__main__":
    main()
