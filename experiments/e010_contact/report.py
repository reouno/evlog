#!/usr/bin/env python3
"""Build report.html for e010.

Charts: matplotlib, exported as SVG and inlined. Diagram: hand-written SVG.
Run from the repo root: uv run python experiments/e010_contact/report.py
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

SEEDS = list(range(1, 13))
# Variant name -> run prefix. Slot order is also the chart color order.
RUN = "128_patchy"
KIND_COLOR = {1: SERIES[0], 2: SERIES[1], 3: SERIES[3], 4: SERIES[2]}
CONFIRM_STEPS = 5000
VIEWER_SEED = 1  # TODO pick the seed with hunters
VIEWER_RUN = f"{RUN}_seed{VIEWER_SEED}"
VIEWER_LABEL = f"seed {VIEWER_SEED}"
VIEWER_W = 128


# ---------- data ----------

def load_csv(path):
    with open(os.path.join(HERE, path)) as f:
        rows = list(csv.DictReader(f))
    return {k: [float(r[k]) for r in rows] for k in rows[0]}


def load_rows(path):
    with open(os.path.join(HERE, path)) as f:
        return list(csv.DictReader(f))


def lineage_stats(run):
    """Per lineage: first and last step seen as a group, max size."""
    lin = load_rows(f"results/{run}_lineages.csv")
    first, last, size = {}, {}, defaultdict(int)
    for r in lin:
        i, s = int(r["lineage"]), int(r["step"])
        first.setdefault(i, s)
        last[i] = s
        size[i] = max(size[i], int(r["size"]))
    return first, last, size


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


def line_chart(title, subtitle, series, ymin=None, percent=False, ymax=None):
    """series: (label, xs, ys, slot)."""
    fig, ax = new_axes()
    for label, xs, ys, slot in series:
        ax.plot(xs, ys, color=SERIES[slot], linewidth=1.6, label=label)
    if ymin is not None:
        top = ymax if ymax is not None else max(v for _, _, ys, _ in series for v in ys) * 1.12
        ax.set_ylim(ymin, max(top, ymin + 1e-9))
    ax.yaxis.set_major_formatter((lambda y, _p: f"{y:.0%}") if percent else kfmt)
    ax.yaxis.set_major_locator(MaxNLocator(4))
    legend_above(ax, len(series))
    return figure(title, subtitle, to_svg(fig))


def color_slots(run):
    first, _, _ = lineage_stats(run)
    return {lid: k % len(LINEAGE_PALETTE) for k, lid in enumerate(sorted(first, key=first.get))}


def timeline_chart(title, subtitle, run, events):
    """Every lineage as a band: size over time, colored by confirmation order. Events as marks."""
    slot = color_slots(run)
    lin = load_rows(f"results/{run}_lineages.csv")
    by = defaultdict(list)
    for r in lin:
        by[int(r["lineage"])].append((int(r["step"]), int(r["size"])))
    fig, ax = new_axes(size=(13, 3.6))
    ax.set_ylabel("agents in the lineage")
    for lid, pts in by.items():
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
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
<svg viewBox="0 0 720 330" role="img" aria-label="Contact physics. Body A moves east into the cell of body B. Along each of the 8 lines, the outermost cells are the tips. A's force in a line is its muscle cells in that line. A hard tip has hardness 3 per contiguous hard cell behind it, other tips 1. The softer tip breaks if the force exceeds its hardness. A broken cell is gone; its energy goes to the pusher if it has digestive cells." style="max-width:100%;height:auto;display:block">
<g fill="none" stroke="currentColor" stroke-width="1.2" font-size="12" font-family="system-ui, sans-serif">
  <text x="20" y="20" fill="currentColor" stroke="none" font-weight="600">A moves east into B's cell: they touch line by line (4 of the 8 lines shown)</text>
  <g transform="translate(40,40)">
    <rect x="0" y="0" width="16" height="16" fill="#1baf7a"/><rect x="16" y="0" width="16" height="16" fill="#1baf7a"/><rect x="32" y="0" width="16" height="16" fill="#eb6834"/><rect x="48" y="0" width="16" height="16" fill="#eb6834"/><rect x="64" y="0" width="16" height="16" fill="#eb6834"/><rect x="80" y="0" width="16" height="16" fill="#2a78d6"/>
    <rect x="0" y="18" width="16" height="16" fill="#1baf7a"/><rect x="16" y="18" width="16" height="16" fill="#1baf7a"/><rect x="32" y="18" width="16" height="16" fill="#1baf7a"/><rect x="48" y="18" width="16" height="16" fill="#1baf7a"/><rect x="64" y="18" width="16" height="16" fill="#eb6834"/><rect x="80" y="18" width="16" height="16" fill="#eb6834"/>
    <rect x="0" y="36" width="16" height="16" fill="#1baf7a"/><rect x="16" y="36" width="16" height="16" fill="#1baf7a"/><rect x="32" y="36" width="16" height="16" fill="#1baf7a"/>
    <rect x="0" y="54" width="16" height="16" fill="#1baf7a"/><rect x="16" y="54" width="16" height="16" fill="#1baf7a"/><rect x="32" y="54" width="16" height="16" fill="#1baf7a"/><rect x="48" y="54" width="16" height="16" fill="#1baf7a"/><rect x="64" y="54" width="16" height="16" fill="#2a78d6"/><rect x="80" y="54" width="16" height="16" fill="#2a78d6"/>
    <rect x="-2" y="-2" width="132" height="74" stroke-dasharray="3 2"/>
    <text x="0" y="90" fill="currentColor" stroke="none" font-weight="600">A (pusher)</text>
    <text x="-30" y="12" fill="currentColor" stroke="none">1</text><text x="-30" y="30" fill="currentColor" stroke="none">2</text><text x="-30" y="48" fill="currentColor" stroke="none">3</text><text x="-30" y="66" fill="currentColor" stroke="none">4</text>
    <path d="M136,34 l24,0" marker-end="url(#arr)" stroke="var(--s1)" stroke-width="2"/>
  </g>
  <g transform="translate(220,40)">
    <rect x="0" y="0" width="16" height="16" fill="#2a78d6"/><rect x="16" y="0" width="16" height="16" fill="#1baf7a"/><rect x="32" y="0" width="16" height="16" fill="#1baf7a"/><rect x="48" y="0" width="16" height="16" fill="#1baf7a"/>
    <rect x="0" y="18" width="16" height="16" fill="#2a78d6"/><rect x="16" y="18" width="16" height="16" fill="#2a78d6"/><rect x="32" y="18" width="16" height="16" fill="#1baf7a"/><rect x="48" y="18" width="16" height="16" fill="#1baf7a"/>
    <rect x="0" y="36" width="16" height="16" fill="#1baf7a"/><rect x="16" y="36" width="16" height="16" fill="#1baf7a"/><rect x="32" y="36" width="16" height="16" fill="#1baf7a"/><rect x="48" y="36" width="16" height="16" fill="#1baf7a"/>
    <rect x="0" y="54" width="16" height="16" fill="#1baf7a"/><rect x="16" y="54" width="16" height="16" fill="#1baf7a"/><rect x="32" y="54" width="16" height="16" fill="#1baf7a"/><rect x="48" y="54" width="16" height="16" fill="#1baf7a"/>
    <rect x="-2" y="-2" width="132" height="74" stroke-dasharray="3 2"/>
    <text x="0" y="90" fill="currentColor" stroke="none" font-weight="600">B (in the cell A moves into)</text>
  </g>
  <g transform="translate(400,40)">
    <text x="0" y="12" fill="currentColor" stroke="none">1: A tip hard (3), force 3. B tip hard (3).</text>
    <text x="0" y="28" fill="currentColor" stroke="none">   equal hardness: nothing.</text>
    <text x="0" y="48" fill="currentColor" stroke="none">2: A tip muscle (1), force 2. B tip hard x2 (6).</text>
    <text x="0" y="64" fill="currentColor" stroke="none">   2 &gt; 1: A's soft tip breaks on B's armor.</text>
    <text x="0" y="84" fill="currentColor" stroke="none">3: A has no cell here: nothing to touch.</text>
    <text x="0" y="104" fill="currentColor" stroke="none">4: A tip hard x2 (6), force 0. B tip soft (1).</text>
    <text x="0" y="120" fill="currentColor" stroke="none">   0 &gt; 1 is false: nothing. Armor is not a tooth.</text>
  </g>
  <text x="20" y="190" fill="currentColor" stroke="none" font-weight="600">the rule, per line where both have a cell</text>
  <text x="20" y="210" fill="currentColor" stroke="none">force = the pusher's muscle cells in the line. hardness = 3 per contiguous hard cell behind a hard tip, else 1.</text>
  <text x="20" y="228" fill="currentColor" stroke="none">the softer tip breaks if force &gt; its hardness. equal hardness: nothing. a body that does not move pushes nobody.</text>
  <text x="20" y="246" fill="var(--s1)" stroke="none" font-weight="600">a broken cell is gone; its energy (energy / mass, plus 0.02 for the matter) goes to the pusher if it has digestive cells.</text>
  <text x="20" y="274" fill="currentColor" stroke="none" font-weight="600">what a cell costs</text>
  <text x="20" y="292" fill="currentColor" stroke="none">0.02 to build (paid by the parent), 0.002 per step to keep; a body pays 0.032 per step besides its cells.</text>
  <text x="20" y="310" fill="currentColor" stroke="none">no attack, no defense, no gut, no escape roll, no kin exclusion, no kill rule. blue: hard, orange: muscle, green: digestive.</text>
  <defs><marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="currentColor" stroke="none"/></marker></defs>
</g>
</svg>
<figcaption>Figure 1. Contact physics. A body that moves toward a cell holding other bodies pushes into them along the facing side, line by line. Only materials and geometry decide what happens: a hard tip with muscle behind it in the same line is a tooth; contiguous hard cells are armor; an empty line cannot be touched. Nothing in the code names a bite, a shell, or a prey.</figcaption>
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
    """Frames packed small into `data`: food as 4-bit nibbles; agents as x, y, body id (2 bytes), lineage (2 bytes).
    Returns one index entry per frame (step, offsets and lengths into `data`).
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
            ag += bytes((x, y, b & 255, b >> 8, lin & 255, lin >> 8))
            used.add(b)
        out.append({"s": fr["step"], "fo": len(data), "fl": len(nib), "ao": len(data) + len(nib), "al": len(ag)})
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
  function draw(){
    const fr = frames[i]; const food = bytes.subarray(fr.fo, fr.fo + fr.fl), ag = bytes.subarray(fr.ao, fr.ao + fr.al);
    const px = img.data;
    for (let c = 0; c < W * H; c++) {
      const g = 40 + foodAt(food, c) * 12;
      px[c * 4] = g * 0.35; px[c * 4 + 1] = g; px[c * 4 + 2] = g * 0.45; px[c * 4 + 3] = 255;
    }
    octx.putImageData(img, 0, 0);
    ctx.drawImage(off, 0, 0, cv.width, cv.height);
    paintFood(zctx, food, zx, zy, ZN, ZS);
    const counts = {}, teeth = {}, armor = {}, eyes = {}, masses = {}; let n = 0;
    for (let k = 0; k < ag.length; k += 6) {
      const x = ag[k], y = ag[k + 1], id = ag[k + 2] | (ag[k + 3] << 8), lin = ag[k + 4] | (ag[k + 5] << 8);
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
    for (let k = 0; k < ag.length; k += 6) { const key = ((ag[k] / ZN) | 0) + ',' + ((ag[k + 1] / ZN) | 0); n[key] = (n[key] || 0) + 1; }
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


def hunter_lineages(run, min_steps=20_000, min_bite=2.0):
    lin = load_rows(f"results/{run}_lineages.csv")
    by = defaultdict(list)
    for r in lin:
        by[int(r["lineage"])].append(r)
    out = []
    for lid, rows in by.items():
        h = [r for r in rows if float(r["bite"]) >= min_bite]
        if not h:
            continue
        span = int(h[-1]["step"]) - int(h[0]["step"]) + CONFIRM_STEPS
        if span < min_steps:
            continue
        peak = max(h, key=lambda r: int(r["size"]))
        m, p = float(peak["meat"]), float(peak["plant"])
        out.append(dict(id=lid, span=span, first=int(h[0]["step"]), last=int(h[-1]["step"]), size=int(peak["size"]), mass=float(peak["mass"]),
                        bite=float(peak["bite"]), shell=float(peak["shell"]), hard=float(peak["hard"]), muscle=float(peak["muscle"]), digestive=float(peak["digestive"]),
                        diet=m / (m + p) if m + p > 0 else 0.0))
    out.sort(key=lambda d: -d["span"])
    return out


def seed_chart(title, subtitle, logs, key_fn, ymin=0, percent=False, ymax=None):
    fig, ax = new_axes()
    for k, s in enumerate(SEEDS):
        ax.plot(logs[s]["step"], key_fn(logs[s]), color=LINEAGE_PALETTE[k % len(LINEAGE_PALETTE)], linewidth=1.3, label=f"{s}")
    if ymin is not None:
        top = ymax if ymax is not None else max(max(key_fn(logs[s])) for s in SEEDS) * 1.12
        ax.set_ylim(ymin, max(top, ymin + 1e-9))
    ax.yaxis.set_major_formatter((lambda y, _p: f"{y:.0%}") if percent else kfmt)
    ax.yaxis.set_major_locator(MaxNLocator(4))
    ax.legend(loc="lower left", bbox_to_anchor=(0, 1.0), ncols=12, handlelength=1.0, borderaxespad=0, columnspacing=0.8, title="seed", title_fontsize=8, fontsize=8)
    return figure(title, subtitle, to_svg(fig))


def main():
    logs = {s: load_csv(f"results/{RUN}_seed{s}_log.csv") for s in SEEDS}
    events = {s: load_rows(f"results/{RUN}_seed{s}_events.csv") for s in SEEDS}

    def med(x):
        x = [v for v in x if v == v]
        return statistics.median(x) if x else float("nan")

    def summarize(s):
        log = logs[s]
        run = f"{RUN}_seed{s}"
        first, last, size = lineage_stats(run)
        life = [last[i] - first[i] + CONFIRM_STEPS for i in first]
        n_lin = load_rows(f"results/{run}_lineages.csv")
        per_step = Counter(int(r["step"]) for r in n_lin)
        last_step = int(log["step"][-1])
        counts = Counter(r["event"] for r in events[s])
        hunters = hunter_lineages(run)
        half = [i for i, t in enumerate(log["step"]) if t > last_step / 2]
        return dict(
            pop=med(log["pop"]), pop_min=min(log["pop"]), pop_max=max(log["pop"]), extinct=last_step < 1_000_000,
            mass=med(log["mass_mean"]), mass_std=med(log["mass_std"]), mass_std_min=min(log["mass_std"]), full=med(log["full_share"]), full_max=max(log["full_share"]),
            open=med(log["open_mean"]), damaged=med(log["damaged_share"]), hard=med(log["hard_mean"]), muscle=med(log["muscle_mean"]), sensor=med(log["sensor_mean"]), digestive=med(log["digestive_mean"]),
            bite=med(log["bite_mean"]), bite_max=max(log["bite_mean"]), biters=med(log["biters_share"]), biters_max=max(log["biters_share"]), shell=med(log["shell_mean"]), shell_max=max(log["shell_mean"]),
            broken=sum(log["cells_broken"]) / last_step, contacts=sum(log["contacts"]) / last_step,
            deaths_broken=sum(log["deaths_broken"]) / max(sum(log["births"]), 1), deaths_broken_half=sum(log["deaths_broken"][i] for i in half) / max(sum(log["births"][i] for i in half), 1),
            meat=sum(log["meat_intake"]) / max(sum(log["plant_intake"]) + sum(log["meat_intake"]), 1), meat_half=sum(log["meat_intake"][i] for i in half) / max(sum(log["plant_intake"][i] + log["meat_intake"][i] for i in half), 1),
            majority=med(log["meat_majority"]), majority_max=max(log["meat_majority"]), per_cell=med(log["meat_per_cell"]),
            hunters=len(hunters), hunter_span=hunters[0]["span"] if hunters else 0, hunter_diet=max((h["diet"] for h in hunters), default=0.0),
            lineages=med([per_step.get(t, 0) for t in range(1000, last_step + 1, 1000)]), ids=len(first), life=med(life) if life else 0, rate=sum(counts.values()) / (last_step // 1000),
            births=sum(log["births"]) / last_step, sps=med(log["steps_per_sec"]), sps_min=min(log["steps_per_sec"]),
        )

    S = {s: summarize(s) for s in SEEDS}
    hunters_all = {s: hunter_lineages(f"{RUN}_seed{s}") for s in SEEDS}

    charts = {}
    charts["pop"] = seed_chart("Population", "Living agents on four islands. The per-body cost bounds it near 5,000; e007's law carried about 1,000 full-square bodies.", logs, lambda l: l["pop"])
    charts["mass"] = seed_chart("Mass per body", "Population mean of cells per body. e007's law: 64 (a full square) in every seed.", logs, lambda l: l["mass_mean"], ymax=66)
    charts["mass_std"] = seed_chart("Spread of mass", "Standard deviation of cells per body. Zero would mean one body size.", logs, lambda l: l["mass_std"])
    charts["full"] = seed_chart("Full squares", "Share of bodies with all 64 cells.", logs, lambda l: l["full_share"], percent=True, ymax=1.0)
    charts["open"] = seed_chart("Open lines per body", "Of the 32 lines (8 per side), those with no cell to touch. 32 would be an empty body; 0 a body that can be touched from everywhere.", logs, lambda l: l["open_mean"], ymax=33)
    charts["bite"] = seed_chart("Bite per body", "Population mean of the largest force behind a hard tip. 2 is enough to break a soft tip; 0 means no body can bite.", logs, lambda l: l["bite_mean"])
    charts["biters"] = seed_chart("Bodies with a bite", "Share of bodies with a hard tip and at least one muscle cell behind it.", logs, lambda l: l["biters_share"], percent=True)
    charts["shell"] = seed_chart("Shell per body", "Mean hardness of the tips that can be touched. 1 is soft everywhere; 3 is a hard tip; 6 two hard cells thick.", logs, lambda l: l["shell_mean"])
    charts["broken"] = seed_chart("Cells broken per step", "Cells removed from bodies by pushes, per step.", logs, lambda l: [c / 10_000 for c in l["cells_broken"]])
    charts["contacts"] = seed_chart("Pushes per step", "Moves into a cell that holds another body, per step.", logs, lambda l: [c / 10_000 for c in l["contacts"]])
    charts["deaths"] = seed_chart("Deaths by damage per birth", "Bodies that lost their last cell, divided by births, per window.", logs, lambda l: [d / max(b, 1) for d, b in zip(l["deaths_broken"], l["births"])])
    charts["meat"] = seed_chart("Meat share of intake", "Energy from broken cells of other bodies divided by all energy eaten.", logs, lambda l: [m / max(m + p, 1e-9) for m, p in zip(l["meat_intake"], l["plant_intake"])], percent=True)
    charts["majority"] = seed_chart("Agents fed mostly on other bodies", "Share whose lifetime intake from broken cells exceeds their intake from plants.", logs, lambda l: l["meat_majority"], percent=True)
    charts["muscle"] = seed_chart("Muscle per body", "Population mean of muscle cells. Muscle is force along its line and speed (muscle / mass).", logs, lambda l: l["muscle_mean"])
    charts["hard"] = seed_chart("Hard cells per body", "Population mean. Hard is hardness at a tip and nothing else.", logs, lambda l: l["hard_mean"])
    charts["lineages"] = seed_chart("Lineages alive", "Confirmed lineages at each log step.", logs, lambda l: l["lineages"])
    charts["sps"] = seed_chart("Steps per second", "Simulation speed, twelve runs sharing one machine, one thread each.", logs, lambda l: l["steps_per_sec"])

    timeline = timeline_chart(f"Lineages over time (seed {VIEWER_SEED})", "Each colored band is one lineage, height = agents in it; marks are events at the size they were logged with.", VIEWER_RUN, events[VIEWER_SEED])

    first, _, _ = lineage_stats(VIEWER_RUN)
    bodies = load_bodies(VIEWER_RUN)
    data = bytearray()
    long_frames, used_l = pack_frames(f"results/{VIEWER_RUN}_long.jsonl", first, data, every=2)
    clip_frames, used_c = pack_frames(f"results/{VIEWER_RUN}_clip.jsonl", first, data, every=2, limit=100)
    legend = " ".join(f'<span class="sw" style="background:{KIND_COLOR[k]}"></span>{name}' for k, name in ((1, "hard"), (2, "muscle"), (3, "sensor"), (4, "digestive")))
    viewer_data = {"w": VIEWER_W, "h": VIEWER_W, "long": long_frames, "clip": clip_frames, "bodies": {str(b): bodies[b] for b in used_l | used_c},
                   "kindColors": {str(k): v for k, v in KIND_COLOR.items()}, "palette": LINEAGE_PALETTE, "none": NONE_COLOR,
                   "slots": {str(k): v for k, v in color_slots(VIEWER_RUN).items()}}
    header = json.dumps(viewer_data, separators=(",", ":")).encode()
    blob = base64.b64encode(gzip.compress(len(header).to_bytes(4, "little") + header + bytes(data), 9)).decode()

    def row(label, f):
        return f"<tr><td>{label}</td>" + "".join(f"<td>{f(S[s])}</td>" for s in SEEDS) + "</tr>"

    summary = ("<thead><tr><th>Measure</th>" + "".join(f"<th>seed {s}</th>" for s in SEEDS) + "</tr></thead><tbody>"
               + row("Population, median (min-max)", lambda d: f"{d['pop']:,.0f} ({d['pop_min']:,.0f}-{d['pop_max']:,.0f})")
               + row("Mass per body, median of means", lambda d: f"{d['mass']:.1f}")
               + row("Spread of mass, median (min) of std", lambda d: f"{d['mass_std']:.1f} ({d['mass_std_min']:.1f})")
               + row("Full squares, median (max) share", lambda d: f"{d['full']:.1%} ({d['full_max']:.0%})")
               + row("Open lines per body, median", lambda d: f"{d['open']:.1f}")
               + row("Hard / muscle / sensor / digestive, median", lambda d: f"{d['hard']:.1f} / {d['muscle']:.1f} / {d['sensor']:.1f} / {d['digestive']:.1f}")
               + row("Bite per body, median (max)", lambda d: f"{d['bite']:.2f} ({d['bite_max']:.1f})")
               + row("Bodies with a bite, median (max) share", lambda d: f"{d['biters']:.1%} ({d['biters_max']:.0%})")
               + row("Shell per body, median (max)", lambda d: f"{d['shell']:.2f} ({d['shell_max']:.2f})")
               + row("Hunter lineages (bite &ge; 2 for 20,000+ steps)", lambda d: f"{d['hunters']}")
               + row("Longest hunter lineage (steps)", lambda d: f"{d['hunter_span']:,}")
               + row("Highest meat share of a hunter lineage", lambda d: f"{d['hunter_diet']:.0%}")
               + row("Pushes per step", lambda d: f"{d['contacts']:.1f}")
               + row("Cells broken per step", lambda d: f"{d['broken']:.2f}")
               + row("Energy per broken cell, median", lambda d: f"{d['per_cell']:.3f}")
               + row("Deaths by damage per birth (2nd half)", lambda d: f"{d['deaths_broken']:.3f} ({d['deaths_broken_half']:.3f})")
               + row("Damaged bodies, median share", lambda d: f"{d['damaged']:.1%}")
               + row("Meat share of intake (2nd half)", lambda d: f"{d['meat']:.1%} ({d['meat_half']:.1%})")
               + row("Agents fed mostly on other bodies, median (max)", lambda d: f"{d['majority']:.1%} ({d['majority_max']:.0%})")
               + row("Births per step", lambda d: f"{d['births']:.1f}")
               + row("Lineages alive, median", lambda d: f"{d['lineages']:.0f}")
               + row("Lifetime, median (steps)", lambda d: f"{d['life']:,.0f}")
               + row("Steps per second, median (min)", lambda d: f"{d['sps']:,.0f} ({d['sps_min']:,.0f})")
               + "</tbody>")

    h_rows = []
    for s, lst in hunters_all.items():
        for c in lst[:3]:
            h_rows.append(f"<tr><td>seed {s}</td><td>{c['id']}</td><td>{c['first']:,}-{c['last']:,}</td><td>{c['span']:,}</td><td>{c['size']}</td><td>{c['mass']:.0f}</td><td>{c['bite']:.1f}</td><td>{c['shell']:.1f}</td><td>{c['hard']:.0f} / {c['muscle']:.0f} / {c['digestive']:.0f}</td><td>{c['diet']:.0%}</td></tr>")
    h_table = ("<thead><tr><th>Run</th><th>Lineage</th><th>Bite &ge; 2 from-to</th><th>Steps</th><th>Peak size</th><th>Mass</th><th>Bite</th><th>Shell</th><th>Hard / muscle / digestive</th><th>Meat share</th></tr></thead><tbody>"
               + "".join(h_rows) + "</tbody>") if h_rows else ""

    tables = data_table(["step", "pop", "births", "deaths_energy", "deaths_broken", "cells_broken", "contacts", "plant_intake", "meat_intake", "mass_mean", "mass_std", "full_share", "open_mean", "hard_mean", "muscle_mean", "digestive_mean", "bite_mean", "biters_share", "shell_mean", "damaged_share", "lineages", "steps_per_sec"],
                        {f"seed {s} (every 100,000 steps)": logs[s] for s in SEEDS}, every=10)

    text = TEXT
    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>e010 Contact physics - Report</title>
<style>{CSS}</style>
</head>
<body>
<main>
<h1>e010: What can a body do when nothing is defined but its materials?</h1>
<p class="sub">Experiment report - 2026-08-30 - 128x128 patchy world, trait rules removed, contact physics between bodies, twelve seeds, 1,000,000 steps each</p>

<section class="tldr">
<h2>TL;DR</h2>
<p>{text["tldr"]}</p>
</section>

<h2>1. Question</h2>
<p>{text["question"]}</p>
<ol>
  <li><strong>The world stands at a bounded cost.</strong> No extinction; population between 1,000 and 5,000; at least 400 steps per second per run with twelve sharing the machine.</li>
  <li><strong>Shape is free and used.</strong> Full squares under 10% of bodies, median mass under 32, spread of mass above 3 for the whole run, in every seed.</li>
  <li><strong>Teeth come from shape, and armor answers.</strong> In at least six of twelve seeds, a lineage with mean bite at least 2 lasts 20,000+ steps and takes at least 20% of its food from other bodies; deaths by damage per birth rise above 0.05 there; the population's shell rises above 1.2 within 100,000 steps of the first hunter lineage.</li>
</ol>

<h2>2. The world</h2>
<p>{text["world"]}</p>
{DIAGRAM}
<p>{text["trials"]}</p>
<p><strong>Runs.</strong> Seeds 1-12, 1,000,000 steps on the 128x128 patchy world (four islands); twelve runs sharing one machine, one thread each. Reference: e009 <em>counts</em>, e007's law on the same world. We record, every 10,000 steps:</p>
<ul class="measures">
  <li><strong>Pushes</strong>: moves into a cell holding another body; <strong>cells broken</strong>; <strong>deaths by damage</strong> (a body's last cell) and their age.</li>
  <li><strong>Energy per broken cell</strong>, meat share of intake, agents fed mostly on other bodies.</li>
  <li><strong>Shape</strong>: mass mean and spread, full squares, open lines (of 32, those with no cell to touch), damaged bodies (fewer cells than at birth).</li>
  <li><strong>Bite</strong>: the largest force behind a hard tip (2 breaks a soft tip); <strong>shell</strong>: mean hardness of the touchable tips. Both are measures only; no rule reads them.</li>
  <li><strong>Per lineage</strong>: mass, bite, shell, open lines, diet. A hunter lineage has mean bite at least 2 for 20,000+ steps.</li>
  <li><strong>Lineages and events</strong> as e006; <strong>snapshots</strong> every 5,000 steps and every step for 400 steps at 600,000.</li>
</ul>

<h2>3. Results</h2>
<div class="tw"><table>{summary}</table></div>
<ol class="verdicts">
<li><span class="verdict {text["c1"]}">{text["l1"]}</span> {text["v1"]}</li>
<li><span class="verdict {text["c2"]}">{text["l2"]}</span> {text["v2"]}</li>
<li><span class="verdict {text["c3"]}">{text["l3"]}</span> {text["v3"]}</li>
</ol>

<h3>3.1 {text["h1"]}</h3>
<div class="grid2">
{charts["pop"]}{charts["sps"]}
</div>
<p>{text["r1"]}</p>

<h3>3.2 {text["h2"]}</h3>
<div class="grid2">
{charts["mass"]}{charts["mass_std"]}
</div>
<div class="grid2">
{charts["full"]}{charts["open"]}
</div>
<div class="grid2">
{charts["hard"]}{charts["muscle"]}
</div>
<p>{text["r2"]}</p>

<h3>3.3 {text["h3"]}</h3>
<div class="grid2">
{charts["bite"]}{charts["biters"]}
</div>
<div class="grid2">
{charts["shell"]}{charts["broken"]}
</div>
<div class="grid2">
{charts["deaths"]}{charts["meat"]}
</div>
{"<div class='tw'><table>" + h_table + "</table></div>" if h_table else ""}
<p>{text["r3"]}</p>
<p><strong>Extension.</strong> Seed 1 rerun to 2,000,000 steps (<code>results/128_patchy_seed1_2M_*.csv</code>; the first million is the same run byte for byte): in the second million, population 3,542, mass 5.2, bite 0.00 at every log step, meat 0.0000% of intake, 0.01 cells broken per step. Over 2,000,000 steps, two lineages ever had a mean bite of 2, for 10,000-11,000 steps each.</p>

<h3>3.4 Watching the world</h3>
<div class="wide">{timeline}</div>
<div class="viewer">
  <div class="canvases">
    <canvas id="world" width="1024" height="1024"></canvas>
    <canvas id="zoom" width="480" height="480"></canvas>
  </div>
  <div class="bar">
    <button id="play">Play</button>
    <select id="mode"><option value="long">Long view: every 10,000 steps</option><option value="clip">Clip: every 2nd step from 600,000</option></select>
    <select id="speed"><option value="1">Slow</option><option value="2">Normal</option><option value="4">Fast</option></select>
    <span id="steplbl"></span>
  </div>
  <div class="bar"><input id="scrub" type="range" min="0" max="0" value="0"></div>
  <div class="bar" id="linlbl"></div>
  <div class="bar" id="legend">Blocks: {legend} <span class="sw dot"></span> has a bite (a hard tip with muscle behind it)</div>
  <div class="bar">Left: the whole 128x128 world, each agent colored by its lineage (gray: none), a white dot on bodies with a bite. Green: food; the bright spots are the patches. Click to move the white box. Right: the box at 24x24 cells, bodies drawn on the lineage color, damage included. Labels: agents per lineage, then mean mass, bite, shell, and sensor cells (eyes). Seed {VIEWER_SEED}.</div>
</div>
<p>{text["viewer"]}</p>
<div class="grid2">{charts["contacts"]}{charts["lineages"]}</div>

<h2>4. Discussion</h2>
{text["discussion"]}

<h2>5. Conclusion and next step</h2>
<p>{text["conclusion"]}</p>

<h2>Appendix: data</h2>
<p>Every 100,000th record; full logs in <code>results/*_log.csv</code>, lineages in <code>results/*_lineages.csv</code>, events in <code>results/*_events.csv</code>, snapshots in <code>results/*_{{long,clip,bodies}}.jsonl</code>. Build this report with <code>uv run python experiments/e010_contact/report.py</code>.</p>
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


TEXT = {
    "tldr": "With every trait rule removed, the world does not collapse and does not explode: 3,400-3,500 bodies on four islands at 400-670 steps per second, in all twelve seeds. What the physics selects is the smallest grazer: three or four digestive cells in one corner of the grid, mass 5, no hard, no muscle, no eyes. Shapes left the square on the first day and went to the other corner of what is possible. Teeth are physically profitable (a broken cell of a grazer is worth ten steps of grazing) and evolutionarily almost unreachable: no lineage with a bite lasted 20,000 steps in twelve seeds; the one that appeared (seed 1, step 985,000: mass 19, hard tip with muscle behind it, 58% of its food from other bodies, 181,000 cells broken in one window) was gone within 12,000 steps, most likely because a body that pushes with a tooth also shreds its own children, born next to it. The laws are now the right kind; what is missing is a reason for a body to be more than a corner of gut: nothing a large body can do that a small one cannot, except bite, and biting needs three things at once (a tooth, a policy that moves, and kin it does not hurt).",
    "question": "Every experiment since e005 ran into a wall we had built: attack capped at 24 by three front rows, defense as hard / 2, a full square for every body. principles.md now says laws are about materials and the world, never about traits. This experiment applies that: no attack, no defense, no gut, no escape roll, no kin exclusion, no kill rule. A block is a material with a cost, a hardness, a force; bodies that move into each other interact line by line. What can a body do when nothing is defined but its materials?",
    "world": "e007's world (128x128, four drifting food patches, sexual mode, lineages) and e004's bodies (an 8x8 grid of five kinds grown from the genome). What is new is only what a cell is and what happens when bodies touch (Figure 1). A cell costs 0.02 to build and holds 0.02 when eaten, plus its share of its body's energy; energy is conserved through a bite. A body pays 0.032 per step besides its cells. A body that moves toward a cell holding other bodies pushes into them; in each line where both have a cell, the softer tip breaks if the pusher's muscle in that line exceeds the tip's hardness. A broken cell is gone. A body with no cells left dies.",
    "trials": "<strong>Trials before the runs</strong> (seed 9, short). With contact every step between every adjacent pair and free bodies, the world was a cannibal soup: 85 births and 4,700 broken cells per step, meat 4.5 times plants, because breeding a body and eating it made energy from nothing. With cells that cost what they hold and force only in the direction of movement, the soup was gone and the smallest body won: 14,000 bodies of four cells at 421 steps per second. Plant intake is capped by the food in one cell whatever the body, and upkeep was per cell, so a four-cell body was the best grazer; in e005-e009 only the defense rule had made bodies large. The per-body cost of 0.032 per step (the upkeep of 16 cells) was added as a world law for principle 3 (compute is finite): it bounds the population at regrowth / 0.032, about 5,000. It was chosen for that bound, not for any shape.",
    "c1": "yes", "l1": "Yes", "v1": "No extinction. Population median 3,360-3,512 in every seed, minimum 2,676, maximum 3,669; the per-body cost holds it at two thirds of its bound. Speed 389-666 steps per second median with twelve runs sharing the machine (one seed at 389, just under 400).",
    "c2": "yes", "l2": "Yes, to a corner", "v2": "Full squares are 0.1-0.3% of bodies at most; mass per body is 5.2-5.9 (median of means) with a spread of 2.9-3.9; 20-22 of a body's 32 lines have nothing to touch. Shape is free, and every seed used the freedom the same way: three or four digestive cells in the bottom-left corner of the grid and nothing else.",
    "c3": "no", "l3": "No", "v3": "No lineage with a mean bite of 2 or more lasted 20,000 steps in any of twelve seeds; lineages with any bite at all are 0-5 per seed and short. Cells broken per step 0.1-1.7, deaths by damage per birth below 0.002, meat 0.01-0.2% of intake. One hunter appeared: seed 1, lineage 1136, from step 985,000, mass 19, hard 5, muscle 7, bite 2.8, 58% of its food from other bodies, 181,000 cells broken in one 10,000-step window, extinct by 997,000. Shells never rose: mean tip hardness 1.0-1.5 at most.",
    "h1": "The world stands, at two thirds of the bound the per-body cost sets",
    "r1": "The population settles within 10,000 steps at 3,400-3,500 and stays there in every seed; the dips (to 2,700) are patch drifts, as in e007. e007's law carried 900-1,100 full squares on the same food; the same food now feeds three and a half times as many bodies of one twelfth the mass, and every one of them lives at the margin: births equal deaths by starvation at 25 per step, the median age is 320 steps, the median energy 1.3. Speed is 400-670 steps per second, set by the number of bodies, not their size.",
    "h2": "Shape is free, and selection took it to the smallest corner",
    "r2": "Mass falls from the random start (about 30 cells) to 5-6 within 20,000 steps and stays. The three most common bodies of seed 1 at step 1,000,000 are three, four and five digestive cells packed into the bottom-left corner, and they are 20% of the population between them; 514 distinct bodies are alive, almost all variations of that corner. Hard, muscle and sensor cells are 0.02-0.2 per body. The corner is where the gene network of e004 finds it easiest to switch cells on (the morphogens are strongest there), and the smallest body is the best grazer because intake is capped by the food in one cell (about 0.05 per step at 3,500 bodies) while every cell costs 0.002 per step. The spread of mass (2.9-3.9) is newborn variation and mutation, not coexisting sizes: the population is one size with noise.",
    "h3": "Teeth pay on paper and almost never appear",
    "r3": "The arithmetic favors a hunter: a grazer's cell holds about 0.3 (its share of the body's energy) plus 0.02, ten steps of grazing, and a push into a crowded patch breaks one on average. But a hunter needs a hard tip with two muscle cells behind it in the line it moves along, a policy that moves into occupied cells (the grazers stay put 62% of the time and have nothing to gain from moving), and a way not to hurt its own kind: a newborn is placed next to its parent, and a parent that pushes with a tooth breaks whatever soft line of the child meets it. Bite per body stays at 0-0.3 in every seed. Seed 1 found one at step 985,000 (lineage 1136, mass 19, hard 5, muscle 7, digestive 6, bite 2.8): in its one window it broke 181,000 cells and killed 3,300 bodies, took 58% of its own food from them, and shrank from 45 to 7 agents while doing so. Shells never answered, because nothing lasted long enough to be answered. Seed 1 was rerun to 2,000,000 steps to see what came after the boom: nothing. In the second million, bite is 0.00 at every log step, 0.01 cells break per step, and meat is 0.0000% of intake; the hunter did not return.",
    "viewer": "Seed 1. Play the long view: the population fills the patches with small gray and colored specks, the patches drift, lineages of corner-blobs replace each other. Scrub to the last frames (990,000-1,000,000) for the hunter boom: white dots (bodies with a bite) appear on one island. In the zoom, a body is three or four green cells in a corner; a hunter is a blue tip with orange behind it.",
    "discussion": "<p>The laws are now of the kind principles.md asks for, and the first thing they showed is what the old trait rules had been hiding: bodies were large because defense counted hard blocks, not because size was worth anything. Take the rule away and the world goes to the smallest grazer at once, in every seed, because the two laws that remain (food capped per cell, cost per cell) make a small body the best one. The per-body cost we added keeps the population finite; it does not change the answer.</p><p>The second thing is that emergence has a reachability problem, not a profitability problem. A four-cell hunter would out-earn a four-cell grazer several times over; it appeared once in twelve million births and died in twelve thousand steps. Three things have to be true at once for a hunter to persist, and each has to be found by mutation of a body that is a corner of gut: the tooth (a hard tip with muscle behind it in one line), the habit of moving into occupied cells, and some way of not eating one's own children. Under the old rules the third was free (kin do not eat kin); here it costs armor on every side or a policy that turns away, both of which are far from a blob. This is the honest version of the arms race: it has to be climbed, and the first step is the hardest.</p><p>What this does not show: whether a different starting point (larger bodies, as in e004's dense default) would reach hunters, since the initial random bodies here dissolve into blobs within 20,000 steps; whether the 2D grid is the limit (a corner is the cheapest shape only because morphogens make it so); and whether a third million would differ from the second (seed 1 to 2,000,000 steps: the boom did not recur). It also does not test the contact rule's details (hardness 3 per hard cell, force as muscle per line); those were chosen once and not tuned.</p><p>What would make a large body worth having, without naming a trait? In the world, not in the body: food that a small body cannot reach (a cell holds more than one bite; food that is only for a body of enough digestive cells; a world with places a small body cannot cross), or a cost that is not per cell (the per-body cost, which we set low). In the body, only geometry: a body that can be touched from fewer sides, which the corner blob already is. The next experiment should change the world, not the physics.</p>",
    "conclusion": "Contact physics is a law of the right kind and it stands: the world runs at a bounded cost with no attack, defense, gut, or kill rule. But with only these laws, the freedom of shape is used in one way, the smallest corner of gut, in all twelve seeds; teeth are profitable and were found once in twelve million births, and did not last. The trait rules were also holding the world up. Keep the physics (cells cost what they hold, force acts the way a body moves, the softer tip breaks) and the measures (bite, shell, open lines). Next: give size a reason in the world, not in the body: food that a small body cannot take (more food per cell than one bite, or a bite that scales with the body), so that bodies grow because the world rewards it, and see whether teeth then have something to reach. Running longer alone does not help: seed 1 to 2,000,000 steps had no second hunter.",
}

if __name__ == "__main__":
    main()
