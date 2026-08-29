#!/usr/bin/env python3
"""Build report.html for e007.

Charts: matplotlib, exported as SVG and inlined. Diagram: hand-written SVG.
Run from the repo root: uv run python experiments/e007_patchy_world/report.py
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

SEEDS = [1, 2, 3]
# Variant name -> run prefix. Slot order is also the chart color order.
VARIANTS = {"64 uniform": "64_uniform", "64 patchy": "64_patchy", "256 uniform": "256_uniform", "256 patchy": "256_patchy"}
KIND_COLOR = {1: SERIES[0], 2: SERIES[1], 3: SERIES[3], 4: SERIES[2]}
CONFIRM_STEPS = 5000
VIEWER_RUN = "256_patchy_seed1"
VIEWER_W = 256


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
<svg viewBox="0 0 720 250" role="img" aria-label="Left: uniform regrowth, +0.01 in every cell. Right: patchy regrowth, a Gaussian patch of width 8 cells with peak 0.10 that drifts one cell every 50 steps; the same total. Below: an agent's inputs reach one cell without sensors and two cells with them." style="max-width:100%;height:auto;display:block">
<g fill="none" stroke="currentColor" stroke-width="1.2" font-size="12" font-family="system-ui, sans-serif">
  <!-- uniform -->
  <text x="20" y="20" fill="currentColor" stroke="none" font-weight="600">uniform (e006)</text>
  <line x1="20" y1="90" x2="300" y2="90"/>
  <line x1="20" y1="70" x2="300" y2="70" stroke-dasharray="4 3"/>
  <text x="20" y="108" fill="currentColor" stroke="none">regrowth +0.01 per cell per step, everywhere</text>
  <text x="308" y="74" fill="currentColor" stroke="none">0.01</text>
  <text x="308" y="94" fill="currentColor" stroke="none">0</text>
  <!-- patchy -->
  <text x="400" y="20" fill="currentColor" stroke="none" font-weight="600">patchy (e007)</text>
  <line x1="400" y1="90" x2="680" y2="90"/>
  <path d="M400,90 C470,90 500,88 520,60 C540,32 560,32 580,60 C600,88 630,90 680,90" stroke="var(--s1)" stroke-width="2"/>
  <line x1="550" y1="34" x2="550" y2="90" stroke-dasharray="3 3"/>
  <text x="556" y="44" fill="currentColor" stroke="none">peak 0.10</text>
  <text x="518" y="104" fill="currentColor" stroke="none">sigma = 8 cells</text>
  <path d="M600,20 l18,0" marker-end="url(#arr)"/>
  <text x="622" y="24" fill="currentColor" stroke="none">1 cell / 50 steps</text>
  <text x="400" y="122" fill="currentColor" stroke="none">1 patch per 64x64 cells; same total as uniform</text>
  <!-- agent inputs -->
  <text x="20" y="160" fill="currentColor" stroke="none" font-weight="600">what an agent's policy sees</text>
  <g transform="translate(20,172)">
    <rect x="0" y="0" width="22" height="22" fill="var(--cell)"/><rect x="24" y="0" width="22" height="22" fill="var(--cell)"/><rect x="48" y="0" width="22" height="22" fill="var(--cell)"/><rect x="72" y="0" width="22" height="22" fill="var(--cell)"/><rect x="96" y="0" width="22" height="22" fill="var(--cell)"/>
    <rect x="48" y="0" width="22" height="22" fill="var(--s1)" opacity="0.9"/>
    <rect x="24" y="0" width="22" height="22" stroke="currentColor" stroke-width="1.5"/><rect x="72" y="0" width="22" height="22" stroke="currentColor" stroke-width="1.5"/>
    <rect x="0" y="0" width="22" height="22" stroke="currentColor" stroke-width="1.5" stroke-dasharray="3 2"/><rect x="96" y="0" width="22" height="22" stroke="currentColor" stroke-width="1.5" stroke-dasharray="3 2"/>
    <text x="130" y="10" fill="currentColor" stroke="none">solid: food and agents at distance 1, always</text>
    <text x="130" y="26" fill="currentColor" stroke="none">dashed: distance 2, weighted by sensor blocks / 8 (0 without sensors)</text>
  </g>
  <text x="20" y="232" fill="currentColor" stroke="none">A sensor block costs the same upkeep as any block (0.002 per step). Nothing else changes.</text>
  <defs><marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="currentColor" stroke="none"/></marker></defs>
</g>
</svg>
<figcaption>Figure 1. Two food laws with the same total regrowth. Uniform (left) adds 0.01 to every cell every step. Patchy (right) adds it as Gaussian patches, one per 64x64 cells, whose centers random-walk one cell every 50 steps; a cell at a center regrows ten times faster than a uniform cell, a cell three widths away almost not at all. The agents are unchanged: they see one cell around them, and two cells if they carry sensor blocks.</figcaption>
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
  // Same rules as the simulation: attack = min(hard blocks in the top 3 rows, muscle blocks); defense = hard / 2.
  function stat(id){
    if (stats[id]) return stats[id];
    const cells = bodies[id] || ''; let hard = 0, front = 0, muscle = 0, sensor = 0;
    for (let k = 0; k < 64; k++) { const v = cells.charCodeAt(k) - 48; if (v === 1) { hard++; if (k < 24) front++; } else if (v === 2) muscle++; else if (v === 3) sensor++; }
    return stats[id] = { attack: Math.min(front, muscle), defense: hard / 2, sensor: sensor };
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
    const counts = {}, teeth = {}, armor = {}, eyes = {}; let n = 0;
    for (let k = 0; k < ag.length; k += 6) {
      const x = ag[k], y = ag[k + 1], id = ag[k + 2] | (ag[k + 3] << 8), lin = ag[k + 4] | (ag[k + 5] << 8);
      const st = stat(id);
      ctx.fillStyle = color(lin); ctx.fillRect(x * S, y * S, S, S);
      if (st.attack > 0) { ctx.fillStyle = '#fff'; ctx.fillRect(x * S + S / 2 - 1, y * S + S / 2 - 1, 2, 2); }
      const dx = (x - zx + W) % W, dy = (y - zy + H) % H;
      if (dx < ZN && dy < ZN) { zctx.fillStyle = color(lin); zctx.fillRect(dx * ZS + 1, dy * ZS + 1, ZS - 2, ZS - 2); zctx.drawImage(sprite(id), dx * ZS + 3, dy * ZS + 3, ZS - 6, ZS - 6);
        if (st.attack > 0) { zctx.fillStyle = '#fff'; zctx.fillRect(dx * ZS + ZS / 2 - 2, dy * ZS + ZS / 2 - 2, 4, 4); } }
      counts[lin] = (counts[lin] || 0) + 1; teeth[lin] = (teeth[lin] || 0) + st.attack; armor[lin] = (armor[lin] || 0) + st.defense; eyes[lin] = (eyes[lin] || 0) + st.sensor; n++;
    }
    zctx.strokeStyle = 'rgba(255,255,255,0.35)'; zctx.lineWidth = 1;
    for (let k = 0; k <= ZN; k++) { zctx.beginPath(); zctx.moveTo(k * ZS, 0); zctx.lineTo(k * ZS, zv.height); zctx.stroke(); zctx.beginPath(); zctx.moveTo(0, k * ZS); zctx.lineTo(zv.width, k * ZS); zctx.stroke(); }
    ctx.strokeStyle = '#fff'; ctx.lineWidth = 1.5; ctx.strokeRect(zx * S, zy * S, ZN * S, ZN * S);
    stepLbl.textContent = 'step ' + fr.s.toLocaleString() + ' - ' + n + ' agents';
    const keys = Object.keys(counts).map(Number).sort((a, b) => counts[b] - counts[a]).slice(0, 12);
    linLbl.innerHTML = keys.map(l => '<span class="lin" style="background:' + color(l) + '">' + (l ? 'lineage ' + l : 'none') + ': ' + counts[l]
      + ' (teeth ' + Math.round(teeth[l] / counts[l]) + ', armor ' + Math.round(armor[l] / counts[l]) + ', eyes ' + (eyes[l] / counts[l]).toFixed(1) + ')</span>').join('');
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


def main():
    logs = {v: {s: load_csv(f"results/{p}_seed{s}_log.csv") for s in SEEDS} for v, p in VARIANTS.items()}
    events = {v: {s: load_rows(f"results/{p}_seed{s}_events.csv") for s in SEEDS} for v, p in VARIANTS.items()}

    def by_variant(key, seed=1):
        return [(v, logs[v][seed]["step"], logs[v][seed][key], k) for k, v in enumerate(VARIANTS)]

    def by_seed(v, key):
        return [(f"Seed {s}", logs[v][s]["step"], logs[v][s][key], k) for k, s in enumerate(SEEDS)]

    def ratio(log, a, b):
        return [x / max(y, 1) for x, y in zip(log[a], log[b])]

    def med(x):
        return statistics.median(x)

    def summarize(v, s):
        log = logs[v][s]
        ev = events[v][s]
        run = f"{VARIANTS[v]}_seed{s}"
        first, last, size = lineage_stats(run)
        life = [last[i] - first[i] + CONFIRM_STEPS for i in first]
        n_lin = load_rows(f"results/{run}_lineages.csv")
        per_step = Counter(int(r["step"]) for r in n_lin)
        last_step = int(log["step"][-1])
        dets = last_step // 1000
        counts = Counter(r["event"] for r in ev)
        sensor_windows = sum(1 for m in log["sensor_mean"] if m > 1.0) * 10_000
        return dict(
            pop=med(log["pop"]), sensor=med(log["sensor_mean"]), sensor_max=max(log["sensor_mean"]), sensor_windows=sensor_windows,
            sensor_agents=med(log["sensor_agents_share"]), used=med([u for u, d in zip(log["sense_used"], log["sense_decisions"]) if d > 0] or [0]),
            eaten=sum(log["deaths_eaten"]) / max(sum(log["births"]), 1), res=med(log["mean_res"]), above=med(log["res_above_half"]),
            regrowth=med(log["regrowth"]), lineages=med([per_step.get(t, 0) for t in range(1000, last_step + 1, 1000)]),
            ids=len(first), life=med(life) if life else 0, rate=sum(counts.values()) / dets,
            sps=med(log["steps_per_sec"]), sps_min=min(log["steps_per_sec"]), hard=med(log["hard_mean"]), muscle=med(log["muscle_mean"]),
            attack=med(log["attack_mean"]), meat=sum(log["meat_intake"]) / max(sum(log["plant_intake"]) + sum(log["meat_intake"]), 1),
        )

    S = {(v, s): summarize(v, s) for v in VARIANTS for s in SEEDS}

    charts = {}
    for k, v in enumerate(VARIANTS):
        charts[f"sensor_{k}"] = line_chart(f"Sensor blocks per body ({v})", "Population mean of sensor blocks, every 10,000 steps; same scale in all four. A spike is a random body that died out; a plateau is a lineage that kept its eyes.", by_seed(v, "sensor_mean"), ymin=0, ymax=4.6)
        charts[f"used_{k}"] = line_chart(f"Sensors in use ({v})", "Of the moves decided by agents with sensor blocks, the share that differs from the move the same policy picks blind. 0% means the eye changes nothing.", by_seed(v, "sense_used"), ymin=0, percent=True)
    charts["pop"] = line_chart("Population (seed 1)", "Living agents. The 256 world has 16x the cells; the same laws should carry about 16x the agents.", by_variant("pop"), ymin=0)
    charts["eaten"] = line_chart("Predation deaths per birth (seed 1)", "Agents eaten divided by agents born in each 10,000-step window. Lower means predators find prey less often.", [(v, logs[v][1]["step"], ratio(logs[v][1], "deaths_eaten", "births"), k) for k, v in enumerate(VARIANTS)], ymin=0)
    charts["above"] = line_chart("Cells with food above half (seed 1)", "Share of cells holding more than 0.5 of the cap. Near zero means the world is grazed down flat; patches show up as a floor above zero.", by_variant("res_above_half"), ymin=0, percent=True)
    charts["regrowth"] = line_chart("Food actually added per step (seed 1)", "Regrowth after the cap at 1.0 (a full cell wastes its share). Both laws are set to the same total before the cap.", by_variant("regrowth"), ymin=0)
    charts["attack"] = line_chart("Attack per body (seed 1)", "Population mean of attack = min(hard blocks in the front rows, muscle blocks). Zero is a world of grazers.", by_variant("attack_mean"), ymin=0)
    charts["lineages"] = line_chart("Lineages alive (seed 1)", "Confirmed lineages at each log step.", by_variant("lineages"), ymin=0)
    charts["sps"] = line_chart("Steps per second (seed 1)", "Simulation speed, twelve runs sharing one machine.", by_variant("steps_per_sec"), ymin=0)
    timeline = timeline_chart(f"Lineages over time (256 patchy, seed 1)", "Each colored band is one lineage, height = agents in it; marks are events at the size they were logged with.", VIEWER_RUN, events["256 patchy"][1])

    # Viewer: 256 patchy, seed 1.
    first, _, _ = lineage_stats(VIEWER_RUN)
    bodies = load_bodies(VIEWER_RUN)
    data = bytearray()
    long_frames, used_l = pack_frames(f"results/{VIEWER_RUN}_long.jsonl", first, data, every=4)
    clip_frames, used_c = pack_frames(f"results/{VIEWER_RUN}_clip.jsonl", first, data, every=2, limit=60)
    legend = " ".join(f'<span class="sw" style="background:{KIND_COLOR[k]}"></span>{name}' for k, name in ((1, "hard"), (2, "muscle"), (3, "sensor"), (4, "digestive")))
    viewer_data = {"w": VIEWER_W, "h": VIEWER_W, "long": long_frames, "clip": clip_frames, "bodies": {str(b): bodies[b] for b in used_l | used_c},
                   "kindColors": {str(k): v for k, v in KIND_COLOR.items()}, "palette": LINEAGE_PALETTE, "none": NONE_COLOR,
                   "slots": {str(k): v for k, v in color_slots(VIEWER_RUN).items()}}
    # One gzip'd binary blob: 4-byte header length, JSON header, then the frame bytes.
    header = json.dumps(viewer_data, separators=(",", ":")).encode()
    blob = base64.b64encode(gzip.compress(len(header).to_bytes(4, "little") + header + bytes(data), 9)).decode()

    def row(label, f):
        return f"<tr><td>{label}</td>" + "".join(f"<td>{f(S[(v, s)])}</td>" for v in VARIANTS for s in SEEDS) + "</tr>"

    summary = ("<thead><tr><th>Measure</th>" + "".join(f"<th>{v}<br>seed {s}</th>" for v in VARIANTS for s in SEEDS) + "</tr></thead><tbody>"
               + row("Population, median", lambda d: f"{d['pop']:,.0f}")
               + row("Sensor blocks per body, median (max)", lambda d: f"{d['sensor']:.2f} ({d['sensor_max']:.1f})")
               + row("Steps with sensor mean above 1", lambda d: f"{d['sensor_windows']:,}")
               + row("Agents with any sensor, median share", lambda d: f"{d['sensor_agents']:.0%}")
               + row("Sensors in use, median share of decisions", lambda d: f"{d['used']:.0%}")
               + row("Predation deaths per birth", lambda d: f"{d['eaten']:.3f}")
               + row("Meat share of intake", lambda d: f"{d['meat']:.1%}")
               + row("Attack per body, median", lambda d: f"{d['attack']:.1f}")
               + row("Hard / muscle blocks, median", lambda d: f"{d['hard']:.0f} / {d['muscle']:.0f}")
               + row("Food per cell, median", lambda d: f"{d['res']:.2f}")
               + row("Cells above half, median share", lambda d: f"{d['above']:.1%}")
               + row("Food added per step, median", lambda d: f"{d['regrowth']:.0f}")
               + row("Lineages alive, median", lambda d: f"{d['lineages']:.0f}")
               + row("Lineages over the run", lambda d: f"{d['ids']}")
               + row("Lifetime, median (steps)", lambda d: f"{d['life']:,.0f}")
               + row("Events per 1,000 steps", lambda d: f"{d['rate']:.2f}")
               + row("Steps per second, median (min)", lambda d: f"{d['sps']:,.0f} ({d['sps_min']:,.0f})")
               + "</tbody>")

    tables = data_table(["step", "pop", "births", "deaths_eaten", "mean_res", "res_std", "res_above_half", "regrowth", "sensor_mean", "sensor_agents_share", "sense_used", "hard_mean", "muscle_mean", "attack_mean", "lineages", "steps_per_sec"],
                        {f"{v} seed {s} (every 100,000 steps)": logs[v][s] for v in VARIANTS for s in SEEDS}, every=10)

    text = TEXT
    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>e007 Patchy world - Report</title>
<style>{CSS}</style>
</head>
<body>
<main>
<h1>e007: Does a bigger world with patchy food give eyes a reason to exist?</h1>
<p class="sub">Experiment report - 2026-08-29 - 64x64 and 256x256 worlds, uniform and patchy food, three seeds, 1,000,000 steps each</p>

<section class="tldr">
<h2>TL;DR</h2>
<p>{text["tldr"]}</p>
</section>

<h2>1. Question</h2>
<p>{text["question"]}</p>
<ol>
  <li><strong>Density alone does not do it.</strong> The 256x256 world with uniform food has fewer predation deaths per birth, and sensor blocks stay below 0.5 per body in every seed.</li>
  <li><strong>Patchy food does.</strong> With drifting patches, sensor blocks rise above 1 per body for at least 100,000 steps in at least one seed, and the sensors are used (the move differs from the blind choice in more than 10% of decisions).</li>
  <li><strong>Cost.</strong> The 256x256 world stays above 500 steps per second.</li>
</ol>

<h2>2. The world</h2>
<p>{text["world"]}</p>
{DIAGRAM}
<p><strong>Runs.</strong> 64x64 and 256x256, uniform and patchy, seeds 1-3, 1,000,000 steps; twelve runs sharing one machine. <em>64 uniform</em> is e006's sexual mode byte for byte. We record, every 10,000 steps, on top of e006's log:</p>
<ul class="measures">
  <li><strong>Sensor blocks</strong> per body (mean), and the share of agents with at least one.</li>
  <li><strong>Sensors in use</strong>: of the moves decided by agents with sensors, the share where the choice differs from the same policy fed sense = 0.</li>
  <li><strong>Food shape</strong>: standard deviation over cells, share of cells above 0.5, and food actually added per step after the cap.</li>
  <li><strong>Predation</strong>: deaths by being eaten, per birth.</li>
  <li><strong>Lineages and events</strong> as e006 (gene distance at most 6, groups of 5 that last 5,000 steps).</li>
  <li><strong>Snapshots</strong> every 5,000 steps, and every step for 400 steps at 600,000.</li>
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
{charts["sensor_0"]}{charts["sensor_1"]}
</div>
<div class="grid2">
{charts["sensor_2"]}{charts["sensor_3"]}
</div>
<p>{text["r1"]}</p>
<div class="grid2">
{charts["used_2"]}{charts["used_3"]}
</div>
<div class="grid2">
{charts["used_0"]}{charts["used_1"]}
</div>
<p>{text["r1b"]}</p>

<h3>3.2 {text["h2"]}</h3>
<div class="grid2">
{charts["above"]}{charts["regrowth"]}
</div>
<div class="grid2">
{charts["pop"]}{charts["eaten"]}
</div>
<p>{text["r2"]}</p>

<h3>3.3 {text["h3"]}</h3>
<div class="grid2">
{charts["attack"]}{charts["lineages"]}
</div>
<div class="wide">{timeline}</div>
<p>{text["r3"]}</p>

<h3>3.4 Watching the patchy world</h3>
<div class="viewer">
  <div class="canvases">
    <canvas id="world" width="1024" height="1024"></canvas>
    <canvas id="zoom" width="480" height="480"></canvas>
  </div>
  <div class="bar">
    <button id="play">Play</button>
    <select id="mode"><option value="long">Long view: every 20,000 steps</option><option value="clip">Clip: every 2nd step from 600,000</option></select>
    <select id="speed"><option value="1">Slow</option><option value="2">Normal</option><option value="4">Fast</option></select>
    <span id="steplbl"></span>
  </div>
  <div class="bar"><input id="scrub" type="range" min="0" max="0" value="0"></div>
  <div class="bar" id="linlbl"></div>
  <div class="bar" id="legend">Blocks: {legend} <span class="sw dot"></span> can bite (attack &gt; 0)</div>
  <div class="bar">Left: the whole 256x256 world, each agent colored by its lineage (gray: none), a white dot on agents with attack above 0. Green: food; the bright spots are the patches. Click to move the white box. Right: the box at 24x24 cells, bodies drawn on the lineage color. Labels: agents per lineage, then mean attack (teeth), defense (armor), and sensor blocks (eyes). 256 patchy, seed 1.</div>
</div>
<p>{text["viewer"]}</p>
<div class="grid2">{charts["sps"]}</div>

<h2>4. Discussion</h2>
{text["discussion"]}

<h2>5. Conclusion and next step</h2>
<p>{text["conclusion"]}</p>

<h2>Appendix: data</h2>
<p>Every 100,000th record; full logs in <code>results/*_log.csv</code>, lineages in <code>results/*_lineages.csv</code>, events in <code>results/*_events.csv</code>, snapshots in <code>results/*_{{long,clip,bodies}}.jsonl</code>. Build this report with <code>uv run python experiments/e007_patchy_world/report.py</code>.</p>
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
    "tldr": "Eyes appear, and it is the patches that bring them. On the 256x256 world with drifting food patches, one seed carries sensor blocks for the whole run (population mean above 1 for 820,000 steps, 42% of agents with at least one sensor, the sensor changing one move in five) and a second seed rises late; on the same world with uniform food the mean stays at 0.04-0.24. Size alone changes nothing: a 256 world with uniform food is the 64 world sixteen times over, same density, same predation. But we cannot yet say the eye pays: grazers with sensors take in no more food per digestive block than grazers without, and two sensor blocks cost 2% of a grazer's intake, cheap enough to ride along. Patches do two more things worth keeping: the world splits into islands (12-21 lineages alive instead of 4-6, three times the events) and predation halves. Next: keep patchy food as a law; give sensors something to say (#8) and knock them out to see if it matters; then prey worth eating (#7).",
    "question": "Sensor blocks never evolved in e005 and e006, and the world explains why: food is grazed flat and regrows everywhere, so the cell two steps away looks like the cell one step away, and an eye costs upkeep. This experiment changes the environment only. A bigger world, and food that grows in patches that move, so that seeing further could pay. Do sensors appear? We do not tune for it; we watch.",
    "world": "Everything is e006 in sexual mode (D = 6, mate search in 5 cells): bodies grown from the genome, upkeep per block, one predation rule, lineages by gene distance. Two things are arguments now: the side of the world (64 or 256 cells; the initial population scales with the area) and the food law (Figure 1). <em>64 uniform</em> is e006 sexual, byte for byte.",
    "c1": "partly", "l1": "Partly", "v1": "Density alone does not do it: sensors stay at 0.04-0.24 per body on 256 uniform. But the premise was wrong: the 256 world is not less dense (5.7% of cells hold an agent in both), and predation deaths per birth are the same (0.62-0.71 vs 0.38-0.70). Food per cell is the same law, so the population scales with the area.",
    "c2": "yes", "l2": "Yes", "v2": "Patchy food does: seed 3 holds a sensor mean above 1 for 820,000 steps (42% of agents with sensors, the sensor changing 20% of their moves); seed 1 rises to 0.8 in its last 300,000 steps; seed 2 has none. Sensors in use: 15-20% of decisions on patchy, 8-13% on uniform.",
    "c3": "partly", "l3": "Partly", "v3": "Cost: 256 worlds run at 390-730 steps per second (median) with twelve runs sharing the machine, minimum 250; four of six stay above 500. A million steps took 25-45 minutes.",
    "h1": "Sensors appear on the patchy 256 world, and nowhere else for long",
    "r1": "Top row, the 64 worlds: sensors flicker. A body with sensors shows up, spreads for 20,000-100,000 steps, and is gone; seed 3 of 64 uniform spends 22% of the run above a mean of 1 in bursts, and seed 3 of 64 patchy starts at 3 (the random initial bodies) and loses them by step 300,000. Bottom left, 256 uniform: the same flicker at a lower level, one burst to 1.1 in seed 3. Bottom right, 256 patchy: seed 3 (aqua) is a plateau, 1.0-1.3 for the whole run after step 100,000, and seed 1 (blue) climbs to 0.8 from step 700,000. The plateau is one lineage: lineage 508 is confirmed at step 121,000 and is still there at 1,000,000, with 2-3 sensor blocks per body for 878,000 steps and up to 601 agents. Its body is an armored grazer (46 hard, 15 digestive, no muscle, no attack) with a few sensor cells inside the shell: a quarter of an eye (sense = sensors / 8), not a full one.",
    "r1b": "Do the sensors do anything? For every move by an agent with sensors we also compute the move it would make blind; the charts show the share that differ. On uniform food it is 8-13%; on patchy food 15-24%, in the 64 worlds as well as the 256. So the distance-2 input changes the choice more often when food has a shape, whatever the number of sensor blocks. What we cannot show is that the changed choice is better: among grazers older than 50 steps in the second half of the runs, those with sensors take in 0.0131 units of food per digestive block per step and those without 0.0137 (256 patchy seed 3; seed 1: 0.0119 vs 0.0125). The eye is not paying in the currency we can measure.",
    "h2": "Patches change how the world is eaten, not how much",
    "r2": "The food actually added per step is the same under both laws (650 vs 655 per step on 256, 40 vs 41 on 64): agents sit on the patches and eat the regrowth as it comes, so the cap wastes little. What differs is where the food is. Under patchy food, mean food per cell drops from 0.15 to 0.06 and cells above half are 1-2% either way: the patches are grazed down and the rest of the world is bare. The population is a little smaller (3,480-3,870 vs 3,740-3,810 on 256; 195-210 vs 220-257 on 64). And predation halves: deaths by being eaten per birth are 0.31-0.44 on 256 patchy against 0.62-0.71 on uniform (0.26-0.30 vs 0.38-0.70 on 64), meat is 3-4% of intake instead of 5-6%, and the mean attack per body is 2.0-2.7 instead of 3.7-5.0. On a patch, an omnivore is surrounded by armored grazers it cannot bite; in the desert it meets nobody.",
    "h3": "Patches make islands: three times the lineages, three times the events",
    "r3": "On 256 uniform, 4-6 lineages are alive at a time and the run logs 140-280 splits. On 256 patchy, 12-21 lineages are alive and the run logs 330-750 splits and 240-600 extinctions: each patch is an island with its own kin group, and a patch that drifts into another mixes them. The timeline shows this as many small bands instead of a few wide ones. Lineage lifetimes are short in both (median 7,000-9,000 steps on uniform, 10,000-12,000 on patchy; the confirmation window is 5,000 of that); the difference is in how many there are. The 64 patchy world has one patch: 2-4 lineages alive and 30-80 splits, like 64 uniform, but its lineages last longer (median 13,000-34,000 steps against 11,000), which fits one island that nobody leaves.",
    "viewer": "This is what the patches look like: bright green blobs, each covered by agents, and a dark desert between them with a few agents in transit. Play the long view to see patches drift and colors change as one lineage takes over a patch. Lineage 2041 (yellow, teeth 0, armor 21, eyes 2.8) is a sensor lineage: at step 805,000 it is one of three lineages above 500 agents, and the label is what tells it apart from the other two armored grazer lineages beside it. Omnivores (teeth 21, white dots) are a minority on every patch. The clip shows 120 steps of one moment: agents on a patch move little, and the ones in the desert walk in straight lines.",
    "discussion": "<p>The patches did what the argument said they would, and the argument was about information, not density. Uniform food on a bigger world is the same world; the density is set by food per cell, so predation and sensors are unchanged. Patchy food gives the distance-2 input something to say (the sensor changes one move in five instead of one in ten), and on that world a sensor lineage persisted for 90% of a run. That is the first time in this project that a sensor block has been anything but noise.</p><p>But persisting is not paying. The measured intake per digestive block is the same with and without sensors, and two sensor blocks cost 0.004 per step against an intake of 0.2: the eye is within 2% of free. A body plan that carries a few sensor cells inside its shell can spread by drift and by the rest of the plan being good, and the numbers here cannot tell that apart from an eye that earns its keep. Two things would settle it: a knockout run (the same world with sense forced to 0 for everyone; if lineage 508 still wins, the eyes were passengers), and inputs worth seeing, which is issue #8. Both are cheap.</p><p>The bigger surprise is what patches do to the world as a whole. They cut predation in half and multiply lineages by three. Both come from geography: a patch is an island, its grazers are armored kin, and an omnivore has to cross the desert to find another. For a world that people watch, islands with their own lineages that drift, touch, and merge is closer to the vision than one mixed population. It also raises the question of pace again: 12-21 lineages turning over every 10,000-12,000 steps is a lot of color changes.</p><p>What this does not show: whether the 256 world is worth its cost (16x the compute for 16x the agents; the per-agent cost is unchanged), and whether the patch parameters matter. One width, one drift speed, one density of patches were run, chosen for gradients and not tuned. The 64 patchy world with its single patch was not different from uniform, so it is the number of islands, not the patchiness of one, that does the work.</p>",
    "conclusion": "Patchy food becomes a law of the world: it makes islands, halves predation, multiplies lineages, and is the first environment in which sensor blocks stayed. Keep the 256 world for the next experiments (the viewer needs its islands; the cost is linear in agents) and keep the viewer as built. Eyes are present but not proven: before building on them, run the knockout, and give the policy inputs that reward seeing (#8). The order of work stays: #7 prey worth eating next, then #8 with the knockout.",
}

if __name__ == "__main__":
    main()
