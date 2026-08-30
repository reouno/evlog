#!/usr/bin/env python3
"""Build report.html for e012.

Charts: matplotlib, exported as SVG and inlined. Diagram: hand-written SVG.
Run from the repo root: uv run python experiments/e012_two_places/report.py
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

SEEDS = [1, 2, 3, 4]
E010 = os.path.join(HERE, "..", "e010_contact")
E011 = os.path.join(HERE, "..", "e011_rich_cells")
# Mixed worlds of this experiment: label -> (run prefix, world size, widths). Places are named by their width.
WORLDS = {
    "grass and trees": ("128_sigma8-1", 128, (8, 1)),
    "grass and edge": ("128_sigma8-2", 128, (8, 2)),
    "grass and trees, 256": ("256_sigma8-1", 256, (8, 1)),
}
# Single-kind reference worlds (their own runs, seeds 1-4): label -> (run prefix, folder, width).
REFS = {
    "width 8 alone (e010)": ("128_patchy", E010, 8),
    "width 2 alone (e011)": ("128_patchy_cap8_sigma2", E011, 2),
    "width 1 alone (e011)": ("128_patchy_cap8_sigma1", E011, 1),
}
PLACE_NAME = {8: "grass (width 8)", 2: "edge (width 2)", 1: "trees (width 1)", 0: "beyond the patches"}
PLACE_COLOR = {8: SERIES[0], 2: SERIES[1], 1: SERIES[2], 0: INK}
WORLD_COLOR = {"grass and trees": SERIES[2], "grass and edge": SERIES[1], "grass and trees, 256": SERIES[4]}
KIND_COLOR = {1: SERIES[0], 2: SERIES[1], 3: SERIES[3], 4: SERIES[2]}
CONFIRM_STEPS = 5000
MAIN = "grass and trees"
VIEWER_WORLD = "grass and trees, 256"
VIEWER_SEED = 1
if os.environ.get("E012_SMOKE"):  # build against the 128 runs only, to test the script before the 256 runs finish
    WORLDS["grass and trees, 256"] = ("128_sigma8-1", 128, (8, 1))
LAST_STEP = 1_000_000


# ---------- data ----------

def load_csv(path, folder=HERE):
    with open(os.path.join(folder, path)) as f:
        rows = list(csv.DictReader(f))
    return {k: [float(r[k]) for r in rows] for k in rows[0]}


def load_rows(path, folder=HERE):
    with open(os.path.join(folder, path)) as f:
        return list(csv.DictReader(f))


def load_places(run):
    """places.csv split by place: {width: {column: [values]}}."""
    rows = load_rows(f"results/{run}_places.csv")
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


def hunter_lineages(run, folder=HERE, min_steps=20_000, min_bite=2.0):
    out = []
    for lid, rows in lineage_rows(run, folder).items():
        h = [r for r in rows if float(r["bite"]) >= min_bite]
        if not h:
            continue
        span = int(h[-1]["step"]) - int(h[0]["step"]) + CONFIRM_STEPS
        if span < min_steps:
            continue
        peak = max(h, key=lambda r: int(r["size"]))
        m, p = float(peak["meat"]), float(peak["plant"])
        out.append(dict(id=lid, span=span, size=int(peak["size"]), mass=float(peak["mass"]), bite=float(peak["bite"]), diet=m / (m + p) if m + p > 0 else 0.0))
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
    ax.yaxis.set_major_formatter((lambda y, _p: f"{y:.0%}") if percent else kfmt)
    ax.yaxis.set_major_locator(MaxNLocator(4))
    legend_above(ax, n_legend)


def place_chart(title, subtitle, places, world, key_fn, refs=None, ymin=0, ymax=None, percent=False):
    """One thin line per seed and place, colored by place, for one mixed world. refs: {label: (value, color)} as dashed lines
    (the same measure in the single-kind worlds, median over their seeds and the second half of the run)."""
    fig, ax = new_axes()
    top = 0
    for p in WORLDS[world][2]:
        for k, s in enumerate(SEEDS):
            d = places[world][s][p]
            ys = key_fn(d)
            top = max(top, max(ys))
            ax.plot(d["step"], ys, color=PLACE_COLOR[p], linewidth=1.1, alpha=0.85, label=PLACE_NAME[p] if k == 0 else None)
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
        for k, s in enumerate(SEEDS):
            ys = key_fn(logs[w][s])
            if ys is None:
                continue
            top = max(top, max(ys))
            ax.plot(logs[w][s]["step"], ys, color=colors[w], linewidth=1.1, alpha=0.85, label=w if k == 0 else None)
    finish(ax, ymin, ymax, top, percent, 3)
    return figure(title, subtitle, to_svg(fig))


def lineage_place_chart(title, subtitle, run, widths, min_steps=50_000):
    """Share of each long lineage's members standing on the second kind of place (trees), over its life."""
    fig, ax = new_axes()
    slot = color_slots(run)
    lp = lineage_places(run)
    n = 0
    for lid, rows in lineage_rows(run).items():
        if int(rows[-1]["step"]) - int(rows[0]["step"]) + CONFIRM_STEPS < min_steps or not (lp[lid]["moved"] or lp[lid]["shared"]):
            continue
        xs = [int(r["step"]) for r in rows]
        raw = [int(r["p1"]) / max(int(r["p0"]) + int(r["p1"]), 1) for r in rows]
        ys = [sum(raw[max(0, k - 9):k + 1]) / len(raw[max(0, k - 9):k + 1]) for k in range(len(raw))]  # mean over 10 detections (10,000 steps)
        ax.plot(xs, ys, color=LINEAGE_PALETTE[slot[lid]], linewidth=1.1, alpha=0.9)
        n += 1
    ax.set_ylim(-0.02, 1.02)
    ax.set_xlim(0, LAST_STEP)
    ax.set_yticks([0, 0.5, 1])
    ax.set_yticklabels([PLACE_NAME[widths[0]].split(" (")[0], "half", PLACE_NAME[widths[1]].split(" (")[0]])
    return figure(title, subtitle + f" ({n} lineages of {min_steps//1000},000+ steps that moved home or were shared)", to_svg(fig))


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
@media (max-width: 700px) {{ .viewer .canvases {{ grid-template-columns: 1fr; }} }}
"""

DIAGRAM = """
<figure class="diagram">
<svg viewBox="0 0 720 268" role="img" aria-label="One world with two kinds of food patch. Two wide patches (grass, width 8, 0.10 regrowth per cell per step at the center) and two narrow ones (trees, width 1, 6.5 per cell per step) drift on the same 128x128 torus; every patch carries the same total regrowth, 41 per step. A body eats from the cell it stands on and can walk from one place into the other; the world records for every cell which patch feeds it most." style="max-width:100%;height:auto;display:block">
<g fill="none" stroke="currentColor" stroke-width="1.2" font-size="12" font-family="system-ui, sans-serif">
  <text x="20" y="20" fill="currentColor" stroke="none" font-weight="600">one world, four patches, two widths; every patch carries the same total regrowth (41 per step)</text>
  <line x1="20" y1="170" x2="700" y2="170"/>
  <text x="20" y="188" fill="currentColor" stroke="none">world cells along one line through the centers of a wide patch and a narrow one</text>
  <path d="M 40,170 C 80,168 110,158 140,140 S 190,110 210,110 S 260,140 290,158 S 330,168 370,170" stroke="#2a78d6" stroke-width="1.6"/>
  <text x="210" y="98" text-anchor="middle" fill="#2a78d6" stroke="none">grass: width 8, 0.10 per cell per step, about 1,800 cells</text>
  <path d="M 520,170 C 528,168 532,130 536,90 S 541,62 543,62 S 548,90 552,130 S 558,168 566,170" stroke="#1baf7a" stroke-width="1.6"/>
  <text x="543" y="52" text-anchor="middle" fill="#1baf7a" stroke="none">trees: width 1, 6.5 per cell per step, about 30 cells</text>
  <path d="M 380,150 L 505,150" stroke="var(--s1)" stroke-width="1.4" marker-end="url(#arrow)"/>
  <path d="M 505,160 L 380,160" stroke="var(--s1)" stroke-width="1.4" marker-end="url(#arrow)"/>
  <text x="442" y="140" text-anchor="middle" fill="var(--s1)" stroke="none" font-weight="600">bodies walk; the world only counts who crosses</text>
  <text x="20" y="218" fill="currentColor" stroke="none">each cell belongs to the patch that feeds it most (its place); a cell beyond every patch belongs to none.</text>
  <text x="20" y="236" fill="currentColor" stroke="none">a cell holds at most 8; patches drift one cell every 50 steps.</text>
  <text x="20" y="254" fill="currentColor" stroke="none">bodies, costs, contact physics, mating, lineages: e011's, unchanged.</text>
</g>
<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="var(--s1)"/></marker></defs>
</svg>
<figcaption>Figure 1. The only change from e011: the patches of one world can have different widths (patch k has the k-th width of the list, cycling). Which body pays on which place, and whether a body ever leaves its place, is left to selection. The place of a cell is a measure, not a rule: nothing reads it.</figcaption>
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
    """Frames packed small into `data`: food as 4-bit nibbles; agents as x, y, body id (3 bytes), lineage (2 bytes).
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
        for x, y, b, _d, lin in fr["agents"]:
            lin = lin if confirmed_at.get(lin, 10**12) <= fr["step"] else 0
            ag += bytes((x, y, b & 255, (b >> 8) & 255, b >> 16, lin & 255, lin >> 8))  # 3-byte body id: a run can have 100,000+ distinct (damaged) bodies
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
  const W = data.w, H = data.h, S = cv.width / W, ZN = 24, ZS = zv.width / ZN;
  const off = document.createElement('canvas'); off.width = W; off.height = H;
  const octx = off.getContext('2d'), img = octx.createImageData(W, H);
  ctx.imageSmoothingEnabled = false; zctx.imageSmoothingEnabled = false;
  const slider = document.getElementById('scrub'), stepLbl = document.getElementById('steplbl'), linLbl = document.getElementById('linlbl');
  const playBtn = document.getElementById('play'), mode = document.getElementById('mode');
  let frames = data.long, i = 0, timer = null, zx = (W / 2 - ZN / 2) | 0, zy = (H / 2 - ZN / 2) | 0;
  const sprites = {}, stats = {};
  function color(lin){ return lin ? PAL[data.slots[lin] || 0] : NONE; }
  // Same rules as the simulation: per side, per line, the tip is the outermost cell; a hard tip has hardness 3 per contiguous hard cell;
  // force is the muscle in the line. Bite = largest force behind a hard tip; shell = mean hardness of touchable tips.
  function stat(id){
    if (stats[id]) return stats[id];
    const cells = bodies[id] || ''; let mass = 0, sensor = 0, bite = 0, hsum = 0, hn = 0;
    for (let k = 0; k < 64; k++) { const v = cells.charCodeAt(k) - 48; if (v > 0) mass++; if (v === 3) sensor++; }
    const at = (side, line, k) => side === 0 ? k * 8 + line : side === 1 ? (7 - k) * 8 + line : side === 2 ? line * 8 + (7 - k) : line * 8 + k;
    for (let side = 0; side < 4; side++) for (let line = 0; line < 8; line++) {
      let force = 0, k0 = -1;
      for (let k = 0; k < 8; k++) { const v = cells.charCodeAt(at(side, line, k)) - 48; if (v === 2) force++; if (v > 0 && k0 < 0) k0 = k; }
      if (k0 < 0) continue;
      let h = 1;
      if (cells.charCodeAt(at(side, line, k0)) - 48 === 1) { h = 0; for (let k = k0; k < 8 && cells.charCodeAt(at(side, line, k)) - 48 === 1; k++) h += 3; }
      hsum += h; hn++;
      if (h > 1 && force > bite) bite = force;
    }
    return stats[id] = { mass: mass, bite: bite, shell: hn ? hsum / hn : 0, sensor: sensor };
  }
  function sprite(id){
    if (sprites[id]) return sprites[id];
    const c = document.createElement('canvas'); c.width = 8; c.height = 8; const x = c.getContext('2d');
    const cells = bodies[id] || '';
    for (let k = 0; k < 64; k++) { const v = cells.charCodeAt(k) - 48; if (v > 0) { x.fillStyle = KC[v]; x.fillRect(k % 8, (k / 8) | 0, 1, 1); } }
    return sprites[id] = c;
  }
  function foodAt(food, c){ return (c % 2 === 0) ? (food[c >> 1] >> 4) : (food[c >> 1] & 15); }
  function paintFood(target, food, x0, y0, n, cell){
    for (let y = 0; y < n; y++) for (let x = 0; x < n; x++) {
      const c = ((y0 + y) % H) * W + ((x0 + x) % W);
      const g = 40 + foodAt(food, c) * 12;
      target.fillStyle = 'rgb(' + (g * 0.35 | 0) + ',' + g + ',' + (g * 0.45 | 0) + ')';
      target.fillRect(x * cell, y * cell, cell, cell);
    }
  }
  // Each patch as a ring of radius 2 sigma around its center (on the torus: drawn up to 4 times when it wraps). Wide: blue; narrow: aqua.
  function paintPatches(fr){
    for (const [px, py, sg] of fr.p) {
      ctx.strokeStyle = sg >= 4 ? '#2a78d6' : '#1baf7a'; ctx.lineWidth = 1.5; ctx.setLineDash([4, 4]);
      const r = Math.max(2 * sg, 1.5) * S;
      for (const ox of [0, -W, W]) for (const oy of [0, -H, H]) {
        const cx = (px + 0.5 + ox) * S, cy = (py + 0.5 + oy) * S;
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
    paintPatches(fr);
    paintFood(zctx, food, zx, zy, ZN, ZS);
    const counts = {}, teeth = {}, armor = {}, eyes = {}, masses = {}; let n = 0;
    for (let k = 0; k < ag.length; k += 7) {
      const x = ag[k], y = ag[k + 1], id = ag[k + 2] | (ag[k + 3] << 8) | (ag[k + 4] << 16), lin = ag[k + 5] | (ag[k + 6] << 8);
      const st = stat(id);
      ctx.fillStyle = color(lin); ctx.fillRect(x * S, y * S, S, S);
      if (st.bite > 0) { ctx.fillStyle = '#fff'; ctx.fillRect(x * S + S / 2 - 1, y * S + S / 2 - 1, 2, 2); }
      const dx = (x - zx + W) % W, dy = (y - zy + H) % H;
      if (dx < ZN && dy < ZN) { zctx.fillStyle = color(lin); zctx.fillRect(dx * ZS + 1, dy * ZS + 1, ZS - 2, ZS - 2); zctx.drawImage(sprite(id), dx * ZS + 3, dy * ZS + 3, ZS - 6, ZS - 6);
        if (st.bite > 0) { zctx.fillStyle = '#fff'; zctx.fillRect(dx * ZS + ZS / 2 - 2, dy * ZS + ZS / 2 - 2, 4, 4); } }
      counts[lin] = (counts[lin] || 0) + 1; teeth[lin] = (teeth[lin] || 0) + st.bite; armor[lin] = (armor[lin] || 0) + st.shell; eyes[lin] = (eyes[lin] || 0) + st.sensor; masses[lin] = (masses[lin] || 0) + st.mass; n++;
    }
    zctx.strokeStyle = 'rgba(255,255,255,0.35)'; zctx.lineWidth = 1;
    for (let k = 0; k <= ZN; k++) { zctx.beginPath(); zctx.moveTo(k * ZS, 0); zctx.lineTo(k * ZS, zv.height); zctx.stroke(); zctx.beginPath(); zctx.moveTo(0, k * ZS); zctx.lineTo(zv.width, k * ZS); zctx.stroke(); }
    ctx.strokeStyle = '#fff'; ctx.lineWidth = 1.5; ctx.strokeRect(zx * S, zy * S, ZN * S, ZN * S);
    stepLbl.textContent = 'step ' + fr.s.toLocaleString() + ' - ' + n + ' agents';
    const keys = Object.keys(counts).map(Number).sort((a, b) => counts[b] - counts[a]).slice(0, 12);
    linLbl.innerHTML = keys.map(l => '<span class="lin" style="background:' + color(l) + '">' + (l ? 'lineage ' + l : 'none') + ': ' + counts[l]
      + ' (mass ' + (masses[l] / counts[l]).toFixed(0) + ', bite ' + (teeth[l] / counts[l]).toFixed(1) + ', shell ' + (armor[l] / counts[l]).toFixed(1) + ', eyes ' + (eyes[l] / counts[l]).toFixed(1) + ')</span>').join('');
  }
  function densest(){ // start the zoom where the agents are, not in the desert
    const ag = bytes.subarray(frames[0].ao, frames[0].ao + frames[0].al); const n = {};
    for (let k = 0; k < ag.length; k += 7) { const key = ((ag[k] / ZN) | 0) + ',' + ((ag[k + 1] / ZN) | 0); n[key] = (n[key] || 0) + 1; }
    const best = Object.keys(n).sort((a, b) => n[b] - n[a])[0]; if (!best) return;
    zx = +best.split(',')[0] * ZN; zy = +best.split(',')[1] * ZN;
  }
  function setMode(){ frames = data[mode.value]; i = 0; slider.max = frames.length - 1; densest(); draw(); }
  function tick(){ i = (i + 1) % frames.length; draw(); }
  const speed = document.getElementById('speed');
  function interval(){ return (mode.value === 'clip' ? 250 : 600) / +speed.value; }
  playBtn.onclick = function(){ if (timer) { clearInterval(timer); timer = null; playBtn.textContent = 'Play'; } else { timer = setInterval(tick, interval()); playBtn.textContent = 'Pause'; } };
  speed.onchange = function(){ if (timer) { clearInterval(timer); timer = setInterval(tick, interval()); } };
  slider.oninput = function(){ i = +slider.value; draw(); };
  mode.onchange = function(){ if (timer) playBtn.onclick(); setMode(); };
  cv.onclick = function(e){ const r = cv.getBoundingClientRect(); zx = (Math.floor((e.clientX - r.left) / r.width * W - ZN / 2) + W) % W; zy = (Math.floor((e.clientY - r.top) / r.height * H - ZN / 2) + H) % H; draw(); };
  setMode();
})();
"""


def gallery(world, seed, picks):
    """picks: [(lineage id, name, what the shape does)]. The most common body of each lineage at its peak, on the 8x8 grid."""
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
        cards.append(f"""<figure class="card"><svg viewBox="-1 -1 89 89" width="120" height="120" role="img" aria-label="{html.escape(name)}"><rect x="-1" y="-1" width="89" height="89" fill="var(--cell)"/>{rects}</svg>
<figcaption><strong>{html.escape(name)}</strong><br>lineage {lid}: {span:,} steps, {int(peak["size"]):,} agents at its peak, {home}<br>mass {float(peak["mass"]):.0f}: hard {float(peak["hard"]):.0f}, muscle {float(peak["muscle"]):.0f}, digestive {float(peak["digestive"]):.0f}; meat {meat:.0%}<br>{html.escape(what)}</figcaption></figure>""")
    return f"""<figure class="diagram"><div class="cards">{"".join(cards)}</div>
<figcaption>Figure 2. Bodies of lineages that prospered in {world}, seed {seed}: the most common body of the lineage at its peak, on the 8x8 grid a body grows on. Blue: hard, orange: muscle, green: digestive, yellow: sensor. "On grass" is the share of the lineage's agent-steps spent on the wide patches.</figcaption></figure>"""


def main():
    logs, events, places = {}, {}, {}
    for w, (run, _, _) in WORLDS.items():
        logs[w] = {s: load_csv(f"results/{run}_seed{s}_log.csv") for s in SEEDS}
        events[w] = {s: load_rows(f"results/{run}_seed{s}_events.csv") for s in SEEDS}
        places[w] = {s: load_places(f"{run}_seed{s}") for s in SEEDS}
    rlogs = {w: {s: load_csv(f"results/{run}_seed{s}_log.csv", folder) for s in SEEDS} for w, (run, folder, _) in REFS.items()}

    def med(x):
        x = [v for v in x if v == v]
        return statistics.median(x) if x else float("nan")

    def half(d, key):
        n = len(d["step"])
        return d[key][n // 2:]

    def ref_value(w, key_fn):
        """Median over the seeds of a reference world of the median over the second half of the run."""
        return med([med(key_fn(rlogs[w][s])[len(rlogs[w][s]["step"]) // 2:]) for s in SEEDS])

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
        d = dict(pop=med(log["pop"]), pop_min=min(log["pop"]), extinct=last_step < LAST_STEP, sps=med(log["steps_per_sec"]), sps_min=min(log["steps_per_sec"]),
                 crossers=med(half(log, "crossers")), crossers_max=max(log["crossers"]), pop_none=med(half(log, "pop_none")),
                 lineages=med([per_step.get(t, 0) for t in range(1000, last_step + 1, 1000)]), ids=len(first), life=med(life) if life else 0,
                 moved=sum(1 for v in lp.values() if v["moved"]), shared=sum(1 for v in lp.values() if v["shared"]),
                 hunters=len(hunters), hunter_span=hunters[0]["span"] if hunters else 0,
                 meat=sum(log["meat_intake"]) / max(sum(log["plant_intake"]) + sum(log["meat_intake"]), 1))
        for k, p in (("a", widths[0]), ("b", widths[1])):
            q = pl[p]
            n = len(q["step"])
            h = slice(n // 2, n)
            d[f"pop_{k}"] = med(q["pop"][h])
            d[f"pop_{k}_min"] = min(q["pop"])
            d[f"mass_{k}"] = med(q["mass"][h])
            d[f"hard_{k}"] = med(q["hard"][h])
            d[f"hard_{k}_max"] = max(q["hard"])
            d[f"digestive_{k}"] = med(q["digestive"][h])
            d[f"biters_{k}"] = med(q["biters"][h])
            d[f"biters_{k}_max"] = max(q["biters"])
            d[f"meat_{k}"] = sum(q["meat_intake"][h]) / max(sum(q["plant_intake"][h]) + sum(q["meat_intake"][h]), 1)
            d[f"movers_{k}"] = med([m / max(p_, 1) for m, p_ in zip(q["movers"][h], q["pop"][h])])
            d[f"lineages_{k}"] = med(q["lineages"][h])
            d[f"crowd_{k}"] = med(q["crowd_max"][h])
        return d

    S = {w: {s: summarize(w, s) for s in SEEDS} for w in WORLDS}

    def rsum(w, key):
        """A reference world's whole-population value: median over seeds of the median over the second half."""
        return med([med(half(rlogs[w][s], key)) for s in SEEDS])

    refs_hard = {"width 8 alone": (rsum("width 8 alone (e010)", "hard_mean"), PLACE_COLOR[8]), "width 1 alone": (rsum("width 1 alone (e011)", "hard_mean"), PLACE_COLOR[1])}
    refs_biters = {"width 8 alone": (rsum("width 8 alone (e010)", "biters_share"), PLACE_COLOR[8]), "width 1 alone": (rsum("width 1 alone (e011)", "biters_share"), PLACE_COLOR[1])}
    refs_mass = {"width 8 alone": (rsum("width 8 alone (e010)", "mass_mean"), PLACE_COLOR[8]), "width 1 alone": (rsum("width 1 alone (e011)", "mass_mean"), PLACE_COLOR[1])}
    refs_pop = {"width 8 alone, per patch": (rsum("width 8 alone (e010)", "pop") / 4, PLACE_COLOR[8]), "width 1 alone, per patch": (rsum("width 1 alone (e011)", "pop") / 4, PLACE_COLOR[1])}
    refs_hard2 = {"width 8 alone": (rsum("width 8 alone (e010)", "hard_mean"), PLACE_COLOR[8]), "width 2 alone": (rsum("width 2 alone (e011)", "hard_mean"), PLACE_COLOR[2])}

    charts = {}
    charts["hard"] = place_chart("Hard cells per body, by place", "Mean over the bodies standing on each kind of place (grass and trees, one line per seed). Dashed: the same worlds alone (e010, e011).", places, MAIN, lambda d: d["hard"], refs=refs_hard)
    charts["biters"] = place_chart("Bodies with a bite, by place", "Share of the bodies on each place with a hard tip and muscle behind it. Dashed: the single-kind worlds.", places, MAIN, lambda d: d["biters"], refs=refs_biters, percent=True)
    charts["mass"] = place_chart("Mass per body, by place", "Mean cells per body on each place. Flat at 5 is e010's grazer; 18-43 is e011's trees.", places, MAIN, lambda d: d["mass"], refs=refs_mass, ymax=66)
    charts["pop"] = place_chart("Population by place", "Bodies standing on each kind of place. Dashed: the single-kind worlds divided by their four patches.", places, MAIN, lambda d: d["pop"], refs=refs_pop)
    charts["meat"] = place_chart("Meat share of intake, by place", "Energy from broken cells of other bodies over all energy eaten on the place, per window.", places, MAIN, lambda d: [m / max(m + p, 1e-9) for m, p in zip(d["meat_intake"], d["plant_intake"])], percent=True)
    charts["hard_edge"] = place_chart("Hard cells per body, grass and edge", "The same measure in the world whose narrow patches have width 2 (the edge in e011: two seeds of four flipped alone).", places, "grass and edge", lambda d: d["hard"], refs=refs_hard2)
    charts["crossers"] = world_chart("Crossers", "Share of living bodies standing in a kind of place other than the one they were born in. Zero would mean nobody ever leaves.", logs, lambda l: l["crossers"], list(WORLDS), WORLD_COLOR, percent=True)
    charts["lineages"] = world_chart("Lineages alive", "Confirmed lineages at each log step, mixed worlds. e010 alone: 8-17; e011 width 1 alone: 5-13.", logs, lambda l: l["lineages"], list(WORLDS), WORLD_COLOR)
    charts["moving"] = lineage_place_chart(f"Where each lineage lives ({VIEWER_WORLD}, seed {VIEWER_SEED})", "Share of a lineage's members on the trees, over its life (mean over 10,000 steps); one line per lineage that lived in both places. A line that climbs or falls is a lineage that moved.", f"{WORLDS[VIEWER_WORLD][0]}_seed{VIEWER_SEED}", WORLDS[VIEWER_WORLD][2])

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
        vals = [S[w][s][key] for s in SEEDS]
        vals = [v for v in vals if v == v]
        if not vals:
            return "-"
        lo, hi = min(vals), max(vals)
        return fmt(lo) if fmt(lo) == fmt(hi) else f"{fmt(lo)}-{fmt(hi)}"

    def row(label, key, fmt, refkeys=None, by_place=False):
        """A row with one cell per mixed world (grass / narrow when by_place) and one per reference world."""
        cells = "".join(f"<td>{rng(w, key + '_a', fmt)} / {rng(w, key + '_b', fmt)}</td>" if by_place else f"<td>{rng(w, key, fmt)}</td>" for w in WORLDS)
        refs = "".join(f"<td>{fmt(rsum(r, refkeys)) if refkeys else '-'}</td>" for r in REFS)
        return f"<tr><td>{label}</td>{cells}{refs}</tr>"

    n0 = lambda v: f"{v:,.0f}"
    d1 = lambda v: f"{v:.1f}"
    p1 = lambda v: f"{v:.1%}"
    p0 = lambda v: f"{v:.0%}"
    summary = ("<thead><tr><th>Measure (range over four seeds; grass / narrow where two)</th>" + "".join(f"<th>{w}</th>" for w in WORLDS) + "".join(f"<th>{r}</th>" for r in REFS) + "</tr></thead><tbody>"
               + row("Population, median", "pop", n0, "pop")
               + row("Population by place, median", "pop", n0, by_place=True)
               + row("Mass per body by place, median", "mass", d1, "mass_mean", by_place=True)
               + row("Hard cells per body by place, median", "hard", d1, "hard_mean", by_place=True)
               + row("Digestive cells per body by place, median", "digestive", d1, "digestive_mean", by_place=True)
               + row("Bodies with a bite by place, median share", "biters", p1, "biters_share", by_place=True)
               + row("Meat share of intake by place, second half", "meat", p1, by_place=True)
               + row("Movers by place (born in the other kind), median share", "movers", p1, by_place=True)
               + row("Crossers, median share of all bodies", "crossers", p1)
               + row("Lineages alive, median", "lineages", n0, "lineages")
               + row("Lineage lifetime, median (steps)", "life", n0)
               + row("Lineages that moved home (20,000+ steps in each place)", "moved", n0)
               + row("Lineages shared by both places (20,000+ steps)", "shared", n0)
               + row("Hunter lineages (bite &ge; 2 for 20,000+ steps)", "hunters", n0)
               + row("Steps per second, median", "sps", n0, "steps_per_sec")
               + "</tbody>")

    tables = data_table(["step", "place", "pop", "mass", "hard", "muscle", "digestive", "bite", "shell", "biters", "crowd_max", "plant_intake", "meat_intake", "lineages", "movers"],
                        {f"{w}, seed {s}, {PLACE_NAME[p]} (every 100,000 steps)": places[w][s][p] for w in WORLDS for s in SEEDS for p in WORLDS[w][2]}, every=10)
    tables += data_table(["step", "pop", "births", "deaths_broken", "cells_broken", "mass_mean", "hard_mean", "biters_share", "meat_intake", "plant_intake", "crossers", "pop_none", "lineages", "steps_per_sec"],
                         {f"{w}, seed {s}, whole world (every 100,000 steps)": logs[w][s] for w in WORLDS for s in SEEDS}, every=10)

    text = TEXT
    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>e012 Two kinds of place - Report</title>
<style>{CSS}</style>
</head>
<body>
<main>
<h1>e012: Two kinds of place in one world</h1>
<p class="sub">Experiment report - 2026-08-30 - e011's world and physics, food patches of two widths in one run (grass and trees), 128x128 and 256x256, four seeds each, 1,000,000 steps</p>

<section class="tldr">
<h2>TL;DR</h2>
<p>{text["tldr"]}</p>
</section>

<h2>1. Question</h2>
<p>{text["question"]}</p>
<ol>
  <li><strong>Each place keeps its regime.</strong> Grass: mass under 10, hard under 1, under 1% with a bite (e010). Trees: hard above 5, over 10% with a bite, meat over 5% of the intake there (e011). Every seed, second half of the run; neither place empties.</li>
  <li><strong>Lineages cross between places.</strong> At least 1% of bodies stand in the other kind of place from their birth place, and every seed has a lineage with members in both kinds of place for 20,000+ steps.</li>
  <li><strong>Two niches make more lineages.</strong> Lineages alive at least e011's (5-13), with no shorter lifetime.</li>
  <li><strong>The world stands at a bounded cost.</strong> No extinction; population above 500; at least 300 steps per second with twelve runs sharing the machine.</li>
  <li><strong>A grass neighbor pushes the edge over.</strong> With width 2 next to width 8, the arms race starts in more than two seeds of four.</li>
</ol>

<h2>2. The world</h2>
<p>{text["world"]}</p>
{DIAGRAM}
<p>{text["runs"]}</p>
<ul class="measures">
  <li><strong>Place</strong> of a cell: the patch that feeds it most, named by its width; none beyond every patch. A measure only.</li>
  <li><strong>Per place</strong>, every 10,000 steps: population, mass, hard, muscle, digestive, bite, shell, bodies with a bite, the most crowded cell, plant and meat intake eaten there, lineages present, movers (born in the other kind of place).</li>
  <li><strong>Crossers</strong>: share of living bodies standing in a kind of place other than their birth place.</li>
  <li><strong>Per lineage</strong>, every 1,000 steps: e011's columns plus members on each kind of place. A lineage <strong>moved home</strong> if most of its members stood on grass for 20,000+ steps and on trees for 20,000+ steps; it is <strong>shared</strong> if both places held 10% of its members for 20,000+ steps.</li>
  <li>e011's measures (bite, shell, pushes, cells broken, deaths by damage, meat share, hunter lineages) and snapshots, which now carry the patch centers.</li>
</ul>

<h2>3. Results</h2>
<div class="tw"><table>{summary}</table></div>
<ol class="verdicts">
<li><span class="verdict {text["c1"]}">{text["l1"]}</span> {text["v1"]}</li>
<li><span class="verdict {text["c2"]}">{text["l2"]}</span> {text["v2"]}</li>
<li><span class="verdict {text["c3"]}">{text["l3"]}</span> {text["v3"]}</li>
<li><span class="verdict {text["c4"]}">{text["l4"]}</span> {text["v4"]}</li>
<li><span class="verdict {text["c5"]}">{text["l5"]}</span> {text["v5"]}</li>
</ol>

<h3>3.1 {text["h1"]}</h3>
<div class="grid2">
{charts["hard"]}{charts["biters"]}
</div>
<div class="grid2">
{charts["mass"]}{charts["pop"]}
</div>
<p>{text["r1"]}</p>

<h3>3.2 {text["h2"]}</h3>
<div class="grid2">
{charts["crossers"]}{charts["moving"]}
</div>
<p>{text["r2"]}</p>

<h3>3.3 {text["h3"]}</h3>
<div class="grid2">
{charts["lineages"]}{charts["hard_edge"]}
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
  <div class="bar" id="legend">Blocks: {legend} <span class="sw dot"></span> has a bite (a hard tip with muscle behind it)</div>
  <div class="bar">Left: the whole {vw}x{vw} world, each agent colored by its lineage (gray: none), a white dot on bodies with a bite. Green: food; dashed rings are the patches (blue: grass, width 8; aqua: trees, width 1; radius two widths). Click to move the white box. Right: the box at 24x24 cells, bodies drawn on the lineage color, damage included. Labels: agents per lineage, then mean mass, bite, shell, and sensor cells (eyes). {VIEWER_WORLD}, seed {VIEWER_SEED}.</div>
</div>
<p>{text["viewer"]}</p>
<div class="grid2">{charts["meat"]}</div>

<h2>4. Discussion</h2>
{text["discussion"]}

<h2>5. Conclusion and next step</h2>
<p>{text["conclusion"]}</p>

<h2>Appendix: data</h2>
<p>Every 100,000th record; full logs in <code>results/*_log.csv</code>, per place in <code>results/*_places.csv</code>, lineages in <code>results/*_lineages.csv</code>, events in <code>results/*_events.csv</code>, agents every 100,000 steps in <code>results/*_agents.csv</code>, snapshots in <code>results/*_{{long,clip,bodies}}.jsonl</code>. Reference runs are read from <code>../e010_contact/results</code> and <code>../e011_rich_cells/results</code>. Build this report with <code>uv run python experiments/e012_two_places/report.py</code>.</p>
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
    (4904, "corner grazer, grass", "Three digestive cells in one corner: e010's grazer. A hunter's force is in its middle lines, so a corner is never pushed with force."),
    (3605, "edge line, grass", "Six digestive cells along one edge. The top line can be touched, but there is nothing on the grass that bites."),
    (2397, "four corners, both places", "One cell in each corner, 6,246 agents at its peak and the most agent-steps of the run; lived on the grass and in the trees at once for 360,000 steps. Untouchable from every side."),
    (5398, "four corners of three, trees", "The same shape with three cells per corner, in the crowd of the trees, where the small body among tortoises is e011's corner body."),
    (4138, "tortoise, trees", "A two-cell wall of hard around a 4x4 gut, no muscle: it cannot bite and cannot be bitten; 1% of its food from other bodies. 234 plant per agent: the gut is the largest a wall leaves room for."),
    (3120, "tortoise with teeth, trees", "The same wall with 7 muscle cells inside: bite 2.3, 12% of its food from other bodies."),
    (4066, "hollow hunter, trees", "A frame of hard with muscle at the corners and a 4-cell gut: 32 cells, bite 2, 61% of its food from other bodies. Half the cost of a tortoise, and untouchable in its middle lines, which are empty."),
    (5148, "hunter on the grass", "Hard all around, a ring of 15 muscle cells, a gut of 15: bite 4.7, 43% of its food from other bodies. It lived 170,000 steps on a grass island, among grazers of 5 cells, and never went to the trees."),
]

TEXT = {
    "tldr": "One law of the world changed, none of the bodies: the food patches of one world can have different widths. With wide patches (grass) and narrow ones (trees) in one world, each place keeps the regime it had alone: on the grass, bodies of 6 cells with no armor (e010); on the trees, bodies of 16-37 cells with 4-21 hard cells, 12-34% with a bite and meat 11-20% of the intake (e011); in every seed at 128x128, and at 256x256 too, except that there the trees' hunters take grass islands for 100,000-800,000 steps in three seeds of four (mass 49-56, hard 24-30, a ring of muscle, bite 3-5, living among grazers of 5 cells). Bodies cross (0.1-1.6% stand in the other kind of place at any time): small grazers walk into the trees, tortoises walk out, and 2-13 lineages per seed live in both places at once for 20,000+ steps; one lived 978,000 steps with half its members on each place and a different body on each (4 cells on the grass, 12 on the trees), and the largest lineage of the 256 world, one cell in each corner, lived on both. Lineages alive are 9-13 at 128 (e010's number, not the sum) and 19-50 at 256. Next: bodies that face a direction and take up space (#15).",
    "question": "e011 found that the width of a food patch decides what lives on it, and every run had one width, so one regime and one holder per island. The real world has grass and trees side by side, and a grazer can walk from one into the other. The simplest premise in that is <em>the patches of one world need not all have the same width</em>. Do both regimes stand in one world, or does one take over? Do bodies and lineages move between places? And does a neighbor change what happens on the edge width, where e011's arms race started in half the seeds?",
    "world": "Everything is e011's (128x128 or 256x256, one drifting food patch per 4,096 cells, bodies of 8x8 cells in five kinds grown from the genome, contact physics, a cell that costs what it holds, 0.032 per body per step) except that patch k has the k-th width of a list, cycling: \"8,1\" makes every other patch wide and the rest narrow (Figure 1). Every patch carries the same total regrowth, 41 per step, whatever its width. What a cell can hold is a constant 8 now (e011 showed it does nothing). With one width the program reproduces e011 byte for byte.",
    "runs": "<strong>Runs.</strong> Grass and trees (widths 8 and 1) at 128x128, two patches of each; grass and edge (8 and 2) at 128x128; grass and trees at 256x256, eight patches of each. Seeds 1-4 each, 1,000,000 steps, twelve runs at once on one machine, one thread each. References: e010's width-8 runs and e011's width-1 and width-2 runs (128x128, seeds 1-4). We record e011's measures and:",
    "c1": "partly", "l1": "Yes at 128, mostly at 256", "v1": "At 128x128, every seed: on the grass (second half of the run) mass 5.7-6.2, hard 0.1-0.2 per body, 0.1-0.2% of bodies with a bite, as in e010 alone (5.3, 0.1, 0.1%); on the trees mass 15.5-31.5, hard 4.4-15.1, 12-34% with a bite, meat 14-18% of what is eaten there, as in e011 alone (31, 15, 19%; seed 2's trees have lighter armor, 4.4, with 12% biters and 16% meat). Neither place empties: 1,620-1,675 bodies on the grass (e010: 1,745 per two patches), 622-1,046 on the trees (e011: 647). At 256x256 the trees are the same (mass 15.5-36.9, hard 4.4-21.2, 12-14% with a bite, meat 11-20%), but hunters hold grass islands in three seeds of four: hard 1-4 per body on the grass and 3-12% with a bite for 800,000 steps in seed 2, from 600,000 to the end in seed 1, in two bouts in seed 3; seed 4 stays at 0.1 and 0.3%.",
    "c2": "partly", "l2": "Partly", "v2": "Crossers are 0.1-0.7% of living bodies at 128 and 0.6-1.6% at 256 (median; up to 2-6% at some log steps), under the 1% asked for in the small world. But every seed has lineages with both places holding 10%+ of their members for 20,000+ steps (2-4 at 128, 2-13 at 256, 10-22 with the edge width) and 1-5 that moved home; lineage 101 of seed 2 (128) lived from step 27,000 to the end with half its members on each place.",
    "c3": "yes", "l3": "Yes, as many as e010", "v3": "9-13 lineages alive (median) at 128 against 4-10 for e011's trees alone and 7-14 for e010's grass alone, 19-50 at 256 (e007's 256 world: 12-21); the median lifetime is 10,000-13,000 steps everywhere. Two niches did not add up at 128: the mixed world has e010's count, not the sum.",
    "c4": "partly", "l4": "Yes at 128, 151-232 steps/s at 256", "v4": "No extinction; population never below 1,601 at 128 and 6,525 at 256. 526-588 steps per second (grass and trees) and 372-550 (grass and edge) at 128 with twelve runs on one machine; 151-232 at 256 with 7,600-11,100 bodies (e007's 256 world ran 400-700 with fewer, smaller bodies). Linear in bodies, as before.",
    "c5": "no", "l5": "No", "v5": "Alone, width 2 flipped for good in two seeds of four. Next to grass it flipped for good in one (seed 4, from step 100,000: hard 17-25 on the edge from 400,000 on), in bouts in one (seed 1: hard 11 at 100,000 and 400,000, 6-7 from 550,000 to 700,000, then under 1), late and weakly in one (seed 3: hard 5 at 850,000) and never in one (seed 2: at most 4.3). The neighbor did not push the edge over; the edge pushed into the grass instead, once (3.3).",
    "h1": "Each place keeps its regime; at 256 the hunters raid the grass",
    "r1": "The two places are two worlds a few cells apart. On the grass every 128 seed has e010's grazer: 5-6 cells, no armor, one body in 500 with a bite. On the trees every seed has e011's crowd (53-89 bodies in the most crowded cell) and its arms race: 4-21 hard cells per body, 12-34% of bodies with a bite, meat 11-20% of all energy eaten there, and 9-29 hunter lineages per seed at 128 (91-126 at 256) of mass 33-59 and hard 20-46. The population of each place is what the single-kind world had per patch. At 128 the trees' hunters never take the grass (hard per body on the grass at most 1.4). At 256, with eight grass islands instead of two, they do, in three seeds of four: lineages of mass 49-56 with 24-30 hard cells, a ring of 10-15 muscle cells and a bite of 3-5, with 0-4% of their members in the trees, hold an island for 40,000-170,000 steps each (9-11 such lineages per seed) and get 13-24 energy per agent from other bodies against 8-30 from plants; the grass population falls from 7,000 to 4,300-5,200 while they are there (seed 1), and the grass clears when they go (seed 2, last 150,000 steps).",
    "h2": "Bodies cross, lineages straddle, hunters mostly stay",
    "r2": "At any time 0.1-1.6% of bodies stand in the other kind of place from the one they were born in, and 2-3% stand beyond every patch, on their way. Who crosses is not symmetric: into the trees walk small grazers (3-8 cells, no armor), out of the trees walk tortoises (64 cells, 48 hard) that then graze among the small bodies (1% of the grass at the end of two seeds). Lineages straddle more than bodies do: 2-13 per seed hold 10%+ of their members in both places for 20,000+ steps, and 1-5 move home. Lineage 101 of seed 2 at 128 (alive from 27,000 to 1,000,000 steps, 2,353 agents at its peak) had half its members on each place for the whole run, with a different body on each: 4 cells and an age of 500-700 steps on the grass, 8-12 cells and an age of 30-60 on the trees (the small bodies of the trees are e011's corner bodies, 26-41% of what stands there). At 256, the largest lineage of seed 1 (2397: one digestive cell in each corner, 6,246 agents at its peak, 361,000 steps) lived 60% on the grass and 40% in the trees. One gene pool, two bodies, sorted by place; nobody wrote a niche.",
    "h3": "Two niches, e010's number of lineages; and the edge pushed into the grass once",
    "r3": "Lineages alive are 9-13 in every mixed world at 128, against 4-10 on trees alone and 7-14 on grass alone; they are not the sum. At 256 (sixteen islands) they are 19-50. With the edge width (2) next to the grass, the arms race did not start more often than alone (one seed for good, one in bouts, against two of four alone). What did happen is new at 128: in seed 4, from step 450,000 to 850,000, the hunters of the edge held the grass as well (hard 5-7 per body on the grass, 18-26% of bodies with a bite, meat 11% of the grass intake, the grass population halved to 860), through lineages of mass 32-43 with 12-23 hard cells that had 30-70% of their members on the grass; by 900,000 the grass was clear again. The edge is four cells wide (20-26 bodies to a cell against 53-89 on the trees), so a lineage that lives on both sides of its border is common there: 10-22 shared lineages per seed against 2-4 with the trees.",
    "viewer": "Grass and trees, 256, seed 1. Eight wide islands and eight narrow ones on one screen: the blue rings are grass, sparse and green, with a few thousand small bodies spread thin; the aqua rings are trees, a spot of 50-90 bodies to a cell where the zoom shows tortoises (squares of blue with green inside), hunters (orange inside blue, white dot) and corner bodies (green in the corners, nothing between). Scrub to 600,000 and after: a hunter lineage takes a grass island (white dots on a wide island, the lineage label with bite 3-5), and the island's grazers thin out. The timeline shows the largest lineage of the run (2397, the four-corner body) rising in the middle of the run on both kinds of place at once.",
    "discussion": "<p>The premise was that the places of one world can differ, and the world answered with two regimes side by side, each at the density its single-kind world had, and with a traffic between them that is small in bodies (one in a hundred or a thousand) and large in consequences: lineages that straddle both places with a different body on each, tortoises grazing among grazers, and, when there are enough islands, hunters that take a grass island for a hundred thousand steps. None of that was written. The place of a cell is a number the world keeps for the log; no rule reads it.</p><p>Why hunters take the grass at 256 and not at 128 is the open question. A hunter lineage that lives on grass at 256 has a body the trees made (a wall, a ring of muscle, a gut) and eats grazers that have no armor at all: the meat is there in both worlds. What differs is the number of islands (eight and eight against two and two) and so the number of tries, and the number of tree islands sending hunters out: with two grass islands and 1,000,000 steps, the eight seed-islands of 128 saw no invasion, and the 32 of 256 saw 30 hunter lineages on the grass. It looks like a rate, not a barrier; a longer run at 128 would tell. Also open: why the grass clears again (seed 2 at 256, seed 4 of the edge world): the grazers thin out, and a hunter on a thin island starves.</p><p>What the viewer sees is what the issue asked for: two kinds of island on one screen, bodies with shapes a reader can tell apart, a lineage crossing from one kind to the other, and a raid. The world is still made of one verb per body kind (eat, push, resist, be untouchable), and the corner body, the shape that cannot be touched, is the largest lineage in the 256 world. The next freedom to add is a front and a size in the world (#15), so that a tooth points somewhere and a body blocks a path; places will then have more to select among.</p>",
    "conclusion": "A world can have two kinds of place under one law (patch widths as a list), at no added cost, and both regimes stand in every seed: e010's grazers on the grass, e011's tortoises and hunters on the trees, each at its own density, with 9-13 lineages alive at 128 and 19-50 at 256. Bodies cross at 0.1-1.6%, lineages straddle (2-13 per seed for 20,000+ steps, one for 978,000 steps with a different body on each place), tortoises walk out onto the grass, and at 256 hunters take grass islands in three seeds of four for 100,000-800,000 steps. Widths as a list are a law of the world from here on; 128 with two patches of each kind is the world for questions about places, 256 with eight and eight is the world people watch. Next: #15, bodies face a direction and take up space; then #16, ground and friction.",
}

if __name__ == "__main__":
    main()
