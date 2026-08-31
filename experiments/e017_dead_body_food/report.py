#!/usr/bin/env python3
"""Build report.html for e017.

Charts: matplotlib, exported as SVG and inlined. Diagram: hand-written SVG.
Run from the repo root: uv run python experiments/e017_dead_body_food/report.py
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

E016 = os.path.join(HERE, "..", "e016_plant_under_body")
# Worlds of this experiment: label -> (run prefix, world size, widths, seeds). Places are named by their width.
WORLDS = {
    "grass and trees": ("128_sigma8-1", 128, (8, 1), [1, 2, 3, 4]),
    "grass and edge": ("128_sigma8-2", 128, (8, 2), [1, 2, 3, 4]),
    "grass and shrubs": ("128_sigma8-4", 128, (8, 4), [1, 2, 3, 4]),
    "grass and trees, cell 0.1": ("128_sigma8-1-cell0.1", 128, (8, 1), [1, 2, 3, 4]),
}
STRICT = ["grass and trees", "grass and edge", "grass and shrubs"]  # a cell of 0.02 (e010's value)
# The same worlds where a dead body vanished (e016), seeds 1-4: label -> (run prefix, folder, widths). The e016 run of each world of
# this experiment is E016_OF[world].
REFS = {
    "grass and trees, e016": ("128_sigma8-1", E016, (8, 1)),
    "grass and edge, e016": ("128_sigma8-2", E016, (8, 2)),
    "grass and shrubs, e016": ("128_sigma8-4", E016, (8, 4)),
}
E016_OF = {"grass and trees": "128_sigma8-1", "grass and edge": "128_sigma8-2", "grass and shrubs": "128_sigma8-4", "grass and trees, cell 0.1": "128_sigma8-1"}
PLACE_NAME = {8: "grass (width 8)", 4: "shrubs (width 4)", 2: "edge (width 2)", 1: "trees (width 1)", 0: "beyond the patches"}
PLACE_COLOR = {8: SERIES[0], 4: SERIES[3], 2: SERIES[1], 1: SERIES[2], 0: INK}
WORLD_COLOR = {"grass and trees": SERIES[2], "grass and edge": SERIES[1], "grass and shrubs": SERIES[3], "grass and trees, cell 0.1": SERIES[0]}
KIND_COLOR = {1: SERIES[0], 2: SERIES[1], 3: SERIES[3], 4: SERIES[2]}
CONFIRM_STEPS = 5000
MAIN = "grass and trees"
VIEWER_WORLD = "grass and trees"
VIEWER_SEED = 1
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


def to_world(i, f):
    """Where cell i of the body grid lands in the world frame when the body faces f (the simulation's rule)."""
    r, c = divmod(i, 8)
    m = 7
    if f == 0:
        r2, c2 = r, c
    elif f == 1:
        r2, c2 = m - r, m - c
    elif f == 2:
        r2, c2 = c, m - r
    else:
        r2, c2 = m - c, r
    return r2 * 8 + c2


def neighbors_of(run, folder=HERE, size=128, first_step=500_000):
    """Mean over bodies of the other bodies holding a sub-cell in the 3x3 world cells around the cell under the
    middle of the body's box, per snapshot from `first_step` on; returns (steps, values). Read from long.jsonl."""
    bodies = load_bodies(run, folder)
    rotated = {}
    sw = size * 4
    steps, vals = [], []
    for fr in read_frames(f"results/{run}_long.jsonl", folder):
        if fr["step"] < first_step:
            continue
        holders = defaultdict(set)  # world cell -> bodies holding a sub-cell in it
        heres = []
        for k, (x, y, b, _d, _lin, f) in enumerate(fr["agents"]):
            key = (b, f)
            if key not in rotated:
                cells = bodies[b]
                pts = [divmod(to_world(i, f), 8) for i, v in enumerate(cells) if v != "0"]
                rs = [r for r, _ in pts]
                cs = [c for _, c in pts]
                rotated[key] = (pts, ((min(rs) + max(rs)) // 2, (min(cs) + max(cs)) // 2)) if pts else ([], (0, 0))
            pts, (mr, mc) = rotated[key]
            for r, c in pts:
                holders[(((y + r) % sw) // 4, ((x + c) % sw) // 4)].add(k)
            heres.append((k, ((y + mr) % sw) // 4, ((x + mc) % sw) // 4))
        n = 0
        for k, cy, cx in heres:
            others = set()
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    others |= holders.get(((cy + dy) % size, (cx + dx) % size), set())
            others.discard(k)
            n += len(others)
        steps.append(fr["step"])
        vals.append(n / max(len(heres), 1))
    return steps, vals


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
<svg viewBox="0 0 800 330" role="img" aria-label="Regrowth of food in e015 and in e016. e015: a world cell regrows every step whether or not a body holds any of its sub-cells, so the gut cells standing on it eat its regrowth in place. e016: a cell held by a body does not regrow (strict reading), or regrows by its free sub-cells (free reading); the cell a body leaves recovers." style="max-width:100%;height:auto;display:block">
<g fill="none" stroke="currentColor" stroke-width="1.2" font-size="12" font-family="system-ui, sans-serif">
  <text x="20" y="20" fill="currentColor" stroke="none" font-weight="600">e015: food regrows under the body that eats it</text>
  <g stroke="currentColor" stroke-opacity="0.35"><path d="M 40,40 v 80 M 60,40 v 80 M 80,40 v 80 M 100,40 v 80 M 120,40 v 80 M 40,40 h 80 M 40,60 h 80 M 40,80 h 80 M 40,100 h 80 M 40,120 h 80"/></g>
  <g stroke="none">
    <rect x="41" y="41" width="18" height="18" fill="#1baf7a"/>
    <rect x="101" y="41" width="18" height="18" fill="#1baf7a"/>
    <rect x="61" y="101" width="18" height="18" fill="#1baf7a"/>
  </g>
  <path d="M 150,80 L 122,80" stroke="var(--s1)" stroke-width="2" marker-end="url(#arrow)"/>
  <text x="158" y="70" fill="currentColor" stroke="none">regrowth g per step, held or not</text>
  <text x="158" y="86" fill="currentColor" stroke="none">(g: 0.10 on grass, up to 6.5 on a tree cell)</text>
  <text x="158" y="108" fill="currentColor" stroke="none">each gut cell on it eats 0.02 per step</text>
  <text x="40" y="146" fill="currentColor" stroke="none">a world cell is 4x4 sub-cells and holds food up to 8;</text>
  <text x="40" y="162" fill="currentColor" stroke="none">a body's cell is one sub-cell; the cell feeds the</text>
  <text x="40" y="178" fill="currentColor" stroke="none">gut cells standing on it out of its regrowth, so the</text>
  <text x="40" y="194" fill="currentColor" stroke="none">best body stands still and reaches (a lawn)</text>

  <text x="430" y="20" fill="currentColor" stroke="none" font-weight="600">e016: a plant under a body does not grow</text>
  <g stroke="currentColor" stroke-opacity="0.35"><path d="M 450,40 v 80 M 470,40 v 80 M 490,40 v 80 M 510,40 v 80 M 530,40 v 80 M 450,40 h 80 M 450,60 h 80 M 450,80 h 80 M 450,100 h 80 M 450,120 h 80"/></g>
  <g stroke="none">
    <rect x="451" y="41" width="18" height="18" fill="#1baf7a"/>
    <rect x="511" y="41" width="18" height="18" fill="#1baf7a"/>
    <rect x="471" y="101" width="18" height="18" fill="#1baf7a"/>
  </g>
  <path d="M 560,80 L 532,80" stroke="var(--s1)" stroke-width="2" stroke-dasharray="4 3" marker-end="url(#arrow)"/>
  <text x="568" y="70" fill="currentColor" stroke="none">strict (any): regrowth 0 while any</text>
  <text x="568" y="86" fill="currentColor" stroke="none">sub-cell is held</text>
  <text x="568" y="108" fill="currentColor" stroke="none">free: g x free sub-cells / 16 (13/16 here)</text>
  <g stroke="currentColor" stroke-opacity="0.35"><path d="M 450,140 v 80 M 470,140 v 80 M 490,140 v 80 M 510,140 v 80 M 530,140 v 80 M 450,140 h 80 M 450,160 h 80 M 450,180 h 80 M 450,200 h 80 M 450,220 h 80"/></g>
  <path d="M 560,180 L 532,180" stroke="var(--s1)" stroke-width="2" marker-end="url(#arrow)"/>
  <text x="568" y="176" fill="currentColor" stroke="none">the cell a body left: regrowth g,</text>
  <text x="568" y="192" fill="currentColor" stroke="none">it recovers; the lost regrowth is</text>
  <text x="568" y="208" fill="currentColor" stroke="none">counted (shaded), not moved elsewhere</text>

  <text x="20" y="252" fill="currentColor" stroke="none">everything else is e015: space at the resolution of the body, facing, e010's contact rule, work = force x distance</text>
  <text x="20" y="270" fill="currentColor" stroke="none">(a forward action that moves nothing costs nothing), two kinds of place, costs, materials, mating, lineages</text>
  <text x="20" y="298" fill="currentColor" stroke="none">compute: nothing per step (the crowd per cell is kept already); the law takes food from the world instead:</text>
  <text x="20" y="316" fill="currentColor" stroke="none">regrowth on cells that bodies stand on is lost, so standing still exhausts the spot and the population is smaller</text>
</g>
<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="var(--s1)"/></marker></defs>
</svg>
<figcaption>Figure 1. Regrowth of food, before and after. In e015 (left) a world cell regrows every step whether or not a body holds any of its 16 sub-cells, so a body eats its regrowth in place and the best body stands still. In e016 (right) a cell held by a body does not regrow (the strict reading, the main runs), or regrows by its free sub-cells (the free reading, four runs on the trees world); the cell a body leaves recovers. Nothing else changes; the regrowth that does not happen is lost, not moved.</figcaption>
</figure>
"""


def read_frames(path, folder=HERE):
    with open(os.path.join(folder, path)) as f:
        for line in f:
            yield json.loads(line)


def load_bodies(run, folder=HERE):
    out = {}
    with open(os.path.join(folder, f"results/{run}_bodies.jsonl")) as f:
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
        d = dict(pop=med(half(log, "pop")), pop_min=min(log["pop"]), extinct=last_step < LAST_STEP, sps=med(log["steps_per_sec"]), sps_min=min(log["steps_per_sec"]),
                 crossers=med(half(log, "crossers")), crossers_max=max(log["crossers"]), pop_none=med(half(log, "pop_none")),
                 lineages=med([per_step.get(t, 0) for t in range(1000, last_step + 1, 1000)]), ids=len(first), life=med(life) if life else 0,
                 moved=sum(1 for v in lp.values() if v["moved"]), shared=sum(1 for v in lp.values() if v["shared"]),
                 hunters=len(hunters), hunters_any=len(hunters_any), hunter_span=hunters[0]["span"] if hunters else 0,
                 meat=sum(log["meat_intake"]) / max(sum(log["plant_intake"]) + sum(log["meat_intake"]), 1),
                 blocked=med(half(log, "blocked")), shoves=med(half(log, "shoves")), turns_blocked=med(half(log, "turns_blocked")), no_room=med(half(log, "births_no_room")),
                 foot=med(half(log, "foot_mean")), len_fwd=med(half(log, "len_fwd")), len_side=med(half(log, "len_side")), cover=med(half(log, "cover")),
                 contacts=med([c / max(p, 1) / 10_000 for c, p in zip(half(log, "contacts"), half(log, "pop"))]), births=med(half(log, "births")),
                 forward=med(half(log, "forward")), turns=med([a + b for a, b in zip(half(log, "left"), half(log, "right"))]), stay=med(half(log, "stay")),
                 biters=med(half(log, "biters_share")), biters_any=med(half(log, "biters_any_share")), wasted=med(half(log, "wasted")),
                 pushes=med(half(log, "pushes")), move_spent=med(half(log, "move_spent")), muscle=med(half(log, "muscle_mean")), hard=med(half(log, "hard_mean")),
                 cells_broken=med(half(log, "cells_broken")), happened=med([(1 - b) * f for b, f in zip(half(log, "blocked"), half(log, "forward"))]),
                 shaded=med([sh / max(sh + r + wa, 1e-9) for sh, r, wa in zip(half(log, "shaded"), half(log, "regrowth"), half(log, "wasted"))]),
                 shaded_abs=med(half(log, "shaded")), regrowth=med(half(log, "regrowth")),
                 pop_hold=med(log["pop"][3 * len(log["pop"]) // 4:]) / max(med(log["pop"][len(log["pop"]) // 2: 3 * len(log["pop"]) // 4]), 1),
                 above_half=med(half(log, "res_above_half")), mean_res=med(half(log, "mean_res")), intake_gut=med(half(log, "intake_per_gut")))
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
        if key == "contacts_per":
            return med([med([c / max(p, 1) / 10_000 for c, p in zip(half(rlogs[w][s], "contacts"), half(rlogs[w][s], "pop"))]) for s in [1, 2, 3, 4]])
        if key not in rlogs[w][1]:
            return float("nan")
        return med([med(half(rlogs[w][s], key)) for s in [1, 2, 3, 4]])

    R = "grass and trees, e015"
    refs_mass = {"grass, e015": (rplace(R, 8, "mass"), PLACE_COLOR[8]), "trees, e015": (rplace(R, 1, "mass"), PLACE_COLOR[1])}
    refs_foot = {"grass, e015": (rplace(R, 8, "foot"), PLACE_COLOR[8]), "trees, e015": (rplace(R, 1, "foot"), PLACE_COLOR[1])}

    narrow = STRICT
    charts = {}
    charts["forward"] = world_chart("Forward actions", "Share of decisions that are a forward move, per log window, one line per run. e015: 9-27% in the second half; stay and turn are the rest.", logs, lambda l: l["forward"], list(WORLDS), WORLD_COLOR, percent=True, ymax=0.6)
    charts["happened"] = world_chart("Moves that happened", "Share of decisions that moved the body (forward and not blocked). e015: 1-3%; a body that walks its patch would show as tens of percent.", logs, lambda l: [(1 - b) * f for b, f in zip(l["blocked"], l["forward"])], list(WORLDS), WORLD_COLOR, percent=True, ymax=0.6)
    charts["contacts"] = world_chart("Contacts per body per step", "Bodies pressed by a forward action, per body per step. e015: 0.10-0.37; e012 (no space): 2-4 with trees.", logs, lambda l: [c / max(p, 1) / 10_000 for c, p in zip(l["contacts"], l["pop"])], list(WORLDS), WORLD_COLOR)
    charts["shaded"] = world_chart("Regrowth lost to standing bodies", "Share of the world's regrowth (164 per step at 128) that fell on a cell a body held and did not grow. Zero is e015's world; 100% would be a world with no food.", logs, lambda l: [sh / max(sh + r + wa, 1e-9) for sh, r, wa in zip(l["shaded"], l["regrowth"], l["wasted"])], list(WORLDS), WORLD_COLOR, percent=True, ymax=1.0)
    charts["narrow_hard"] = narrow_chart("Hard cells per body on the narrow place, three widths", "The narrow place of each strict world (trees, edge, shrubs), one line per seed. e015: 0.00-0.03; an arms race would show as 5 or more.", places, narrow, lambda d: d["hard"])
    charts["narrow_biters"] = narrow_chart("Bodies with a bite on the narrow place, three widths", "Share of the bodies on the narrow place with a hard tip and muscle behind it on the front. e015: 0%.", places, narrow, lambda d: d["biters"], percent=True)
    charts["mass"] = place_chart("Mass per body, by place", "Mean cells per body on each place (grass and trees, strict reading, one line per seed). Dashed: e015, where food regrew under the body.", places, MAIN, lambda d: d["mass"], refs=refs_mass, ymax=66)
    charts["foot"] = place_chart("World cells under a body, by place", "Mean world cells a body's cells lie in (1 to 9). Dashed: e015, whose winner, eight cells at the corners of its grid, lay over 4.5.", places, MAIN, lambda d: d["foot"], refs=refs_foot, ymin=1, ymax=6)
    charts["pop"] = world_chart("Population", "Bodies alive at each log step, one line per run. e015: 1,420-2,450; a line that keeps falling is a world that starves.", logs, lambda l: l["pop"], list(WORLDS), WORLD_COLOR)
    charts["lineages"] = world_chart("Lineages alive", "Confirmed lineages at each log step. e015: 1-4; e012: 6-15.", logs, lambda l: l["lineages"], list(WORLDS), WORLD_COLOR)

    viewer_run = f"{WORLDS[VIEWER_WORLD][0]}_seed{VIEWER_SEED}"
    timeline = timeline_chart(f"Lineages over time ({VIEWER_WORLD}, seed {VIEWER_SEED})", "Each colored band is one lineage, height = agents in it; marks are events at the size they were logged with.", viewer_run, events[VIEWER_WORLD][VIEWER_SEED])

    first, _, _ = lineage_stats(viewer_run)
    bodies = load_bodies(viewer_run)
    data = bytearray()
    long_frames, used_l = pack_frames(f"results/{viewer_run}_long.jsonl", first, data, every=2)
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
               + row("Forward actions, median share of decisions", "forward", p0, "forward")
               + row("Moves that happened, median share of decisions", "happened", p1)
               + row("Moves blocked, median share of forward actions", "blocked", p0, "blocked")
               + row("Contacts per body per step, median", "contacts", lambda v: f"{v:.2f}", "contacts_per")
               + row("Regrowth lost to standing bodies, median share of regrowth", "shaded", p0)
               + row("Cells broken per 10,000 steps, median", "cells_broken", n0, "cells_broken")
               + row("Mass per body by place, median", "mass", d1, "mass", by_place=True)
               + row("Hard cells per body by place, median", "hard", d1, "hard", by_place=True)
               + row("Muscle cells per body, median", "muscle", lambda v: f"{v:.2f}", "muscle_mean")
               + row("Bodies with a bite on the front by place, median share", "biters", p1, "biters", by_place=True)
               + row("Cover of the place by bodies, median", "cover", p0, "cover", by_place=True)
               + row("World cells under a body by place, median", "foot", d1, "foot", by_place=True)
               + row("Lineages alive, median", "lineages", n0, "lineages")
               + row("Steps per second, median", "sps", n0, "steps_per_sec")
               + "</tbody>")

    tables = data_table(["step", "place", "pop", "mass", "hard", "muscle", "digestive", "bite", "shell", "biters", "cover", "foot", "shell_front", "shell_back", "plant_intake", "meat_intake", "lineages", "movers"],
                        {f"{w}, seed {s}, {PLACE_NAME[p]} (every 100,000 steps)": places[w][s][p] for w in WORLDS for s in seeds_of(w) for p in WORLDS[w][2]}, every=10)
    tables += data_table(["step", "pop", "births", "deaths_broken", "cells_broken", "mass_mean", "hard_mean", "biters_share", "biters_any_share", "forward", "stay", "blocked", "pushes", "move_spent", "foot_mean", "cover", "contacts", "regrowth", "shaded", "wasted", "res_above_half", "intake_per_gut", "meat_intake", "plant_intake", "lineages", "steps_per_sec"],
                         {f"{w}, seed {s}, whole world (every 100,000 steps)": logs[w][s] for w in WORLDS for s in seeds_of(w)}, every=10)

    text = TEXT
    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>e016 A plant under a body does not grow - Report</title>
<style>{CSS}</style>
</head>
<body>
<main>
<h1>e016: A plant under a body does not grow</h1>
<p class="sub">Experiment report - 2026-08-31 - e015's world with one law added: a cell held by a body does not regrow. Grass with trees, edge or shrubs at 128x128, four seeds each, plus the trees world under the milder reading (a cell regrows by its free sub-cells), 1,000,000 steps</p>

<section class="tldr">
<h2>TL;DR</h2>
<p>{text["tldr"]}</p>
</section>

<h2>1. Question</h2>
<p>{text["question"]}</p>
<ol>
  <li><strong>Bodies move.</strong> Forward is more than 30% of decisions (e015: 9-27%) and moves that happen (forward actions that found room) more than 10% of decisions (e015: 1-3%), second half, in at least three seeds of four in at least one world.</li>
  <li><strong>The winning body moves.</strong> The most common body at the end has muscle (e015: 0.00-0.10 per body) or lies over fewer world cells than e015's constellation (4.5), in at least half the runs.</li>
  <li><strong>Contact returns with the moving.</strong> Contacts above 1 per body per step (e015: 0.10-0.37; e012: 2-4 with trees) on at least one world, second half, in at least two seeds of four. A tooth or armor is watched, not predicted.</li>
  <li><strong>The world stands at a bounded cost, with less food.</strong> No extinction; a population that holds over the second half (last quarter within 20% of the third); at least 200 steps per second with six runs sharing a machine; regrowth lost to standing bodies below half of the regrowth on every world.</li>
</ol>

<h2>2. The world</h2>
<p>{text["world"]}</p>
{DIAGRAM}
<p>{text["runs"]}</p>
<ul class="measures">
  <li><strong>Forward</strong>: share of decisions that are a forward move (the only action that can touch another body); <strong>blocked</strong>: forward actions that did not move the body; <strong>moves that happened</strong>: forward and not blocked.</li>
  <li><strong>Contacts</strong>: bodies pressed by a forward action, per body per step; <strong>pushes</strong>: forward actions that pressed on at least one body; <strong>cells broken</strong>: cells lost to a push.</li>
  <li><strong>Regrowth lost to standing bodies</strong> (<code>shaded</code>): the regrowth that fell on held cells and did not grow, next to <strong>wasted</strong>, the regrowth lost to full cells; the share is over the world's whole regrowth (164 per step at 128).</li>
  <li><strong>Bite</strong>: the largest force (muscle in the line) behind a hard tip on the front; <strong>bite any</strong>: on any side. <strong>Hardness of a side</strong>: mean hardness of the touchable tips there.</li>
  <li>e015's measures: per place (population, body means, intake, lineages, movers), cover (share of a place's sub-cells held by bodies), world cells under a body, energy paid for moving, hunter lineages, snapshots (position in sub-cells and facing).</li>
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
{charts["forward"]}{charts["happened"]}
</div>
<div class="grid2">
{charts["contacts"]}{charts["shaded"]}
</div>
<p>{text["r1"]}</p>

<h3>3.2 {text["h2"]}</h3>
<div class="grid2">
{charts["narrow_hard"]}{charts["narrow_biters"]}
</div>
<p>{text["r2"]}</p>

<h3>3.3 {text["h3"]}</h3>
<div class="grid2">
{charts["mass"]}{charts["foot"]}
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
    <select id="mode"><option value="long">Long view: every 10,000 steps</option><option value="clip">Clip: every 4th step from 600,000</option></select>
    <select id="speed"><option value="1">Slow</option><option value="2">Normal</option><option value="4">Fast</option></select>
    <span id="steplbl"></span>
  </div>
  <div class="bar"><input id="scrub" type="range" min="0" max="0" value="0"></div>
  <div class="bar" id="linlbl"></div>
  <div class="bar" id="legend">Blocks: {legend} <span class="sw front"></span> the front (white edge) <span class="sw dot"></span> has a bite on the front</div>
  <div class="bar">Left: the whole {vw}x{vw} world at the resolution of the body ({vw * 4}x{vw * 4} sub-cells), every cell a body holds colored by its lineage (gray: none), a white dot on bodies with a bite. Green: food; dashed rings are the patches (blue: grass, width 8; aqua: trees, width 1; radius two widths). Click to move the white box. Right: the box at 24x24 world cells, each body drawn cell by cell where it stands, turned the way it faces, with a white edge on its front, damage included. Labels: agents per lineage, then mean mass, cells spanned along x across the facing, bite, shell, and sensor cells (eyes). {VIEWER_WORLD}, seed {VIEWER_SEED}.</div>
</div>
<p>{text["viewer"]}</p>
<div class="grid2">{charts["pop"]}{charts["lineages"]}</div>

<h2>4. Discussion</h2>
{text["discussion"]}

<h2>5. Conclusion and next step</h2>
<p>{text["conclusion"]}</p>

<h2>Appendix: data</h2>
<p>Every 100,000th record; full logs in <code>results/*_log.csv</code>, per place in <code>results/*_places.csv</code>, lineages in <code>results/*_lineages.csv</code>, events in <code>results/*_events.csv</code>, agents every 100,000 steps in <code>results/*_agents.csv</code>, snapshots in <code>results/*_{{long,clip,bodies}}.jsonl</code>. Reference runs are read from <code>../e015_move_work/results</code> and <code>../e014_body_space/results</code>. Build this report with <code>uv run python experiments/e016_plant_under_body/report.py</code>.</p>
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
    (144, "the wedge", "Three digestive cells along the front edge, two below, then one and one down the right edge: seven cells in the front-right corner of the grid over 1.6 world cells. Born at step 119,000, alive at 1,000,000, 570 agents at its peak: the body of the run. Every mouth arrives on the same cell when it steps."),
    (57, "the wedge, wider", "Four cells along the front, then three, two, one: nine cells over 2.3 world cells. The winner of the first 350,000 steps, replaced by the tighter wedge."),
    (344, "the block, double", "A 3x2 block with a tail: 15 digestive cells over 3.1 world cells, the heaviest body that lasted. Born at step 495,000, alive at the end with 580 agents at its peak; twice the mouths on the same footprint."),
    (241, "the block", "Three cells along the front, three below, two below that: eight cells over 2.3 world cells in the front-right corner. The shape every run ends with, in one corner or another."),
    (177, "the block, trees", "Ten cells in a 3x4 patch of the front rows (14 cells of mass on average) over 2.9 world cells, on the trees: 124 agents at step 250,000, gone by 270,000."),
    (247, "the block with a tooth, trees", "A 3x3 block with one cell ahead of it, on the trees: the one body of the run with hard cells (1.3) and muscle (1.2) at its peak. 58 agents, 51,000 steps, and it bit nothing."),
    (420, "the column, trees", "A 2x3 column at the right edge, on the trees: eight cells over 2.1 world cells; 52 agents for 68,000 steps in the second half."),
]


TEXT = {
    "question": "e015 made a push free and nobody pushed: forward 9-27% of decisions, contacts 0.10-0.37 per body per step, no tooth, and the same winner as e014, eight digestive cells at the corners of a grid that lies over 4.5 world cells and hardly moves. The reading was that food regrows in place, under the body that eats it, so the best body stands still and reaches: a lawn, and a lawn has no herd. The real world's herds move because a plant under a standing animal does not grow, and the grass a herd leaves recovers. This experiment adds that premise as a law about the world (issue #18): a cell held by a body does not regrow. It names no trait and costs nothing per step; it takes food from the world instead. The hypotheses:",
    "world": "Everything is e015's (128x128 on a torus, drifting food patches of two widths, bodies of 8x8 cells in five kinds grown from the genome, space at the resolution of the body with 4x4 sub-cells per world cell, a facing per body, only the front pushes, e010's contact rule, a cell that costs what it holds, 0.032 per body per step, work = force x distance for a move, four actions: stay, forward, turn left, turn right) with one law added to the regrowth of food (Figure 1). Food is per world cell (up to 8); a body's cell is one sub-cell. Before a cell's regrowth is added, the crowd of the cell is read: under the strict reading (<code>shade</code> = any, the main runs) a cell that any body holds a sub-cell of adds nothing; under the free reading (<code>shade</code> = free) it adds its regrowth times the share of its 16 sub-cells that are free. The regrowth that does not happen is lost, not moved, and counted (<code>shaded</code>).",
    "runs": "<strong>Runs.</strong> At 128x128, two patches of each kind: grass and trees (widths 8 and 1), grass and the edge (8 and 2), grass and shrubs (8 and 4), seeds 1-4 each under the strict reading (twelve runs), and grass and trees seeds 1-4 under the free reading (four runs); six at a time on each of two machines, one thread each, 1,000,000 steps (8-16 minutes per strict run, the world being small; 23-40 minutes for a free run). A pilot (seed 9, 100,000 steps, trees, both readings) came first; the batch ran both readings because the free one left the pilot a lawn. Reference: e015 (the same world, food regrowing under the body) and e014 on the same worlds and seeds. We record e015's measures and:",
    "tldr": "A cell a body stands on no longer regrows, and the lawn becomes a pasture: bodies move (moves that happen 11-20% of decisions against e015's 1-3%, and only 12-26% of forward actions blocked against 78-95%), the winner is a block of 7-9 digestive cells in a corner of its grid over 1.6-2.7 world cells instead of a constellation over 4.5, and the world is half as full (630-1,093 bodies against 1,420-2,450) because 66-78% of its regrowth falls on cells that bodies hold. Nobody meets anybody: contacts fall to 0.02-0.05 per body per step, no tooth, no armor, no meat. The free reading (a cell regrows by its free sub-cells) leaves the lawn a lawn: 1,028-1,333 bodies, moves that happen 4-6% of decisions, 62-81% of forward actions blocked, and corners again: 6-12 gut cells at two to four corners of its grid over 3.9-6.0 world cells (e015: 4.5). Moving is now what a body does, and it still finds nothing but grass; the next law is matter that does not vanish, so that a dead body is food where it lies and a crowd is a place worth going to.",
    "c1": "partly", "l1": "Half", "v1": "Moves that happen are 11-20% of decisions in all twelve strict runs (e015: 1.0-2.8%), above 10% everywhere; forward is 14-24% (e015: 9-27%), never the 30% asked for. A body moves once every 5-9 steps and 74-88% of its forward actions find room (e015: 5-22%); the rest of its decisions are turns (76-86%) and stays (0-1%). The free reading: forward 14-21% of decisions, moves that happen 4-6%, with 62-81% of forward actions blocked: e015's numbers.",
    "c2": "yes", "l2": "Yes", "v2": "The most common body at the end of every strict run is 7-9 digestive cells in one block, a 3x3 square or a wedge of three, three, two (or three, two, two, one), in a corner of the grid, lying over 1.6-2.7 world cells (e015's constellation: 4.5), with no muscle (0.00-0.17 per body over all bodies). It moves because it can: 74-88% of its forward actions find room. The free reading keeps the corners: 6-12 digestive cells at two to four corners of the grid, over 3.9-6.0 world cells (e015: 4.5).",
    "c3": "no", "l3": "No", "v3": "Contacts 0.02-0.05 per body per step in every strict run, below e015's 0.10-0.37 and e012's 2-4: bodies move, and there is nobody in the way. Cover is 2-3% of the world (7-8% of the grass, 27-28% of the trees, 20-26% of the edge, 15-18% of the shrubs; e015: 62%, 53%, 33% of the narrow places). Hard cells 0.00-0.13 per body, bodies with a bite 0% on the front and on any side, meat 0% of the intake, cells broken 0-74 per 10,000 steps.",
    "c4": "partly", "l4": "Stands, on a third of the food", "v4": "No extinction; population 630-750 with trees, 713-830 with the edge, 848-1,093 with shrubs (e015: 1,420-2,450), never below 318 (seed 4 with trees, early) and holding over the second half (last quarter 0.94-1.06 of the third); 541-1,892 steps per second with six runs on a machine. Regrowth lost to standing bodies is 66-78% of the world's regrowth (75-78% with trees, 74-77% with the edge, 66-71% with shrubs), well over the half asked for: the world lives on 33-55 of its 164 regrowth per step. The free reading loses 51-53% of the regrowth and holds 1,028-1,333 bodies: half the shading, two thirds more bodies.",
    "h1": "Bodies move, and meet nobody",
    "r1": "The share of decisions that move the body rises from 1-3% to 11-20%, and the share of forward actions blocked falls from 78-95% to 12-26%: a body steps once every 5-9 steps into room it finds. Forward actions themselves stay at 14-24% (e015: 9-27%); what changed is not how often a body tries to move but how often it can, because the world it moves in is 2-3% covered instead of 33-62% on the narrow places. Contacts fall with the crowd, to 0.02-0.05 per body per step: a body that moves through an empty world presses on nothing. Two thirds to three quarters of the regrowth falls on held cells and is lost, most of it on the trees, whose regrowth sits on a few cells that a few bodies hold 27% of the time; the world lives on the rest. The free reading shades 51-53% of the regrowth and moves nothing: forward 14-21%, moves that happen 4-6%, blocked 62-81%, contacts 0.11-0.25, cover 10-13% of the grass and 51-52% of the trees, as in e015.",
    "h2": "No tooth at any width, again",
    "r2": "Hard cells per body on the narrow places 0.00-0.08 (single windows on the trees reach 12 hard per body and 6% of bodies with a bite: one or two bodies among 32-40, passing), muscle 0.00-0.18, no body with a bite on the front in the second half of any strict run, meat 0% of the intake, cells broken 0-74 per 10,000 steps (seed 3 with the edge and with shrubs: single bodies with muscle passing through). The narrow places are held by 32-40 bodies on the trees, 110-150 on the edge, 268-370 on the shrubs, a fifth to a third of e015's numbers, at 15-28% cover. Births are 26,000-51,000 per 10,000 steps (e015: 125,000-193,000): fewer tries, and none of them found the tooth. There is nothing to bite: a body gains nothing from another body in this world but its place, and places are free.",
    "h3": "The block replaces the constellation",
    "r3": "Mass 7.8-10.6 per body, 1.8-2.7 world cells under a body (e015: 3.5-5.0), 1-5 lineages alive with 7-18 kept over a run: the constellation is gone from every strict run, replaced by a block or a wedge of 7-9 digestive cells in a corner of the grid. Reach is worth nothing when standing exhausts every cell under the body alike; what pays is bringing every mouth onto the cell the body just entered, and a block does that. Figure 2 shows the viewer run's bodies: the wedge that wins (lineage 144, born at step 119,000, alive at the end, 570 agents at its peak, over 1.6 world cells), a wider wedge before it, a double block of 15 cells that lasted, and on the trees a block, a column, and the one body of the run with hard cells and muscle (lineage 247, 58 agents, 51,000 steps, no bite landed). The free reading's winner is the corners again, 6-12 cells at two to four corners over 3.9-6.0 world cells: a sixteenth of the regrowth per held sub-cell is a tax on standing that reach pays for, not a reason to move.",
    "viewer": "Grass and trees, 128, seed 1, strict reading. The grass is no longer a lawn of one color but a scatter of blocks with room between them, each stepping now and then; the tree knots are a few bodies on a few cells. Play the clip: a block steps forward, turns, steps again; the room between the blocks is where the food is. The long view shows the wedge (lineage 144) taking the grass by step 300,000 and holding it, with two or three challengers a run, and the trees changing hands every hundred thousand steps.",
    "discussion": "<p>One law about the world, and the lawn is a pasture. A body that stands still eats what is under it in a few steps and then nothing, so the policies that win step off the exhausted cell into one that has recovered: moves that happen went from 1-3% of decisions to 11-20%, blocked moves from 78-95% of forward actions to 12-26%, and the winning body from eight cells reaching over 4.5 world cells to a block of 7-9 over 1.6-2.7. Nothing in the law names a move or a shape; the herd's premise gave a body that walks and a body that brings its mouths together. The price is food: two thirds to three quarters of the regrowth falls on held cells and is lost, and the world holds half as many bodies. The free reading shows the same law at a sixteenth of the strength does the opposite: it shades 51-53% of the regrowth and the winner keeps its corners (3.9-6.0 world cells), because a body that loses a sixteenth of a cell's regrowth per sub-cell it holds gains more by holding a piece of one more cell than by stepping.</p><p>What did not come: contact, and with it teeth, armor, meat. Bodies move through a world that is 2-3% covered and press on nothing (0.02-0.05 contacts per body per step, less than when they stood still in a crowd). A body gains nothing from another body here but its place, and there is room; moving is what a body does now, and it finds only grass. The premise that is missing is the one the sentence \"a crowd is a place worth going to\" needs: matter that does not vanish. A dead body is food where it lies, so a body gains from another without a tooth, and a place where bodies die is a place to walk to. That is vision's \"Next\" 2 and the recommended next experiment; the spill (a full cell feeds its neighbors, for the trees' waste, which is small now: 0-4 of 164) waits behind it.</p><p>What this does not show: whether the strict reading is the right resolution. It stops a whole world cell's regrowth for one sub-cell held, and the free reading (a sixteenth per sub-cell) is a tax that reach pays and nobody moves for. Where the truth of a grazed plant lies between them is not a question this world can answer; the strict reading is the one that made a herd's premise bite, at the cost of a third of the food, and it stays until a reason to change it appears.</p>",
    "conclusion": "A plant under a body does not grow, and bodies move: moves that happen 11-20% of decisions (e015: 1-3%), 74-88% of forward actions finding room (e015: 5-22%), the winner a block of 7-9 gut cells over 1.6-2.7 world cells in every run, the world standing at 630-1,093 bodies on a third of its regrowth. Contact does not return (0.02-0.05 per body per step), because a body that moves through an empty world meets nobody and gains nothing from a body it meets. The law stays (strict reading). Next: matter that does not vanish, a dead body is food where it lies, so that a crowd is a place worth going to; then the spill.",
}

if __name__ == "__main__":
    main()
