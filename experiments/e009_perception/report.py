#!/usr/bin/env python3
"""Build report.html for e009.

Charts: matplotlib, exported as SVG and inlined. Diagram: hand-written SVG.
Run from the repo root: uv run python experiments/e009_perception/report.py
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
# Variant name -> run prefix. Slot order is also the chart color order.
VARIANTS = {"counts (e007)": "128_patchy_counts", "who": "128_patchy_who", "blind": "128_patchy_blind"}
KIND_COLOR = {1: SERIES[0], 2: SERIES[1], 3: SERIES[3], 4: SERIES[2]}
CONFIRM_STEPS = 5000
VIEWER_VARIANT = "who"
VIEWER_SEED = 4
VIEWER_RUN = f"{VARIANTS[VIEWER_VARIANT]}_seed{VIEWER_SEED}"
VIEWER_LABEL = f"{VIEWER_VARIANT}, seed {VIEWER_SEED}"
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
<svg viewBox="0 0 720 300" role="img" aria-label="What an agent's policy sees. Left: the cross of cells around the agent, distance 1 solid, distance 2 dashed. Right: the inputs per direction. e007 (counts): food and number of agents, distance 2 times sense. e009 (who): plus how many of those neighbors can eat me and how many I can eat, by the predation rule, times sense. Blind: sense forced to 0." style="max-width:100%;height:auto;display:block">
<g fill="none" stroke="currentColor" stroke-width="1.2" font-size="12" font-family="system-ui, sans-serif">
  <!-- cross of cells -->
  <g transform="translate(70,40)">
    <rect x="48" y="0" width="22" height="22" stroke-dasharray="3 2"/>
    <rect x="48" y="24" width="22" height="22" stroke-width="1.5"/>
    <rect x="0" y="48" width="22" height="22" stroke-dasharray="3 2"/>
    <rect x="24" y="48" width="22" height="22" stroke-width="1.5"/>
    <rect x="48" y="48" width="22" height="22" fill="var(--s1)" opacity="0.9"/>
    <rect x="72" y="48" width="22" height="22" stroke-width="1.5"/>
    <rect x="96" y="48" width="22" height="22" stroke-dasharray="3 2"/>
    <rect x="48" y="72" width="22" height="22" stroke-width="1.5"/>
    <rect x="48" y="96" width="22" height="22" stroke-dasharray="3 2"/>
    <text x="59" y="140" fill="currentColor" stroke="none" text-anchor="middle">the agent (blue)</text>
    <text x="59" y="156" fill="currentColor" stroke="none" text-anchor="middle">solid: distance 1</text>
    <text x="59" y="172" fill="currentColor" stroke="none" text-anchor="middle">dashed: distance 2</text>
  </g>
  <!-- inputs -->
  <text x="260" y="24" fill="currentColor" stroke="none" font-weight="600">inputs per direction (4 directions), plus food here and energy</text>
  <rect x="260" y="36" width="440" height="66" rx="6"/>
  <text x="272" y="56" fill="currentColor" stroke="none" font-weight="600">counts (e007)</text>
  <text x="272" y="76" fill="currentColor" stroke="none">food at distance 1 + sense x food at distance 2</text>
  <text x="272" y="94" fill="currentColor" stroke="none">agents at distance 1 + sense x agents at distance 2</text>
  <rect x="260" y="114" width="440" height="84" rx="6" stroke="var(--s1)" stroke-width="2"/>
  <text x="272" y="134" fill="var(--s1)" stroke="none" font-weight="600">who (e009): the two above, and</text>
  <text x="272" y="154" fill="currentColor" stroke="none">sense x neighbors (distance 1 and 2) that can eat me</text>
  <text x="272" y="172" fill="currentColor" stroke="none">sense x neighbors (distance 1 and 2) that I can eat</text>
  <text x="272" y="190" fill="currentColor" stroke="none">"can eat" = attack above defense, mass within gut, not my body</text>
  <rect x="260" y="210" width="440" height="44" rx="6"/>
  <text x="272" y="230" fill="currentColor" stroke="none" font-weight="600">blind (knockout): sense = 0 for everyone</text>
  <text x="272" y="248" fill="currentColor" stroke="none">distance 2 and the who inputs are 0; sensor blocks still cost upkeep</text>
  <text x="20" y="284" fill="currentColor" stroke="none">sense = sensor blocks / 8 (0 without sensors, 1 with a full eye). A sensor block costs 0.002 per step, like any block.</text>
</g>
</svg>
<figcaption>Figure 1. What an agent's policy sees. In every mode the policy is a linear map from these inputs to five moves (stay, four directions), grown from the genome. e007 gives counts of agents in each direction; e009's <em>who</em> mode adds, per direction, how many of those neighbors could eat the agent and how many it could eat, by the predation rule, times sense. Without sensor blocks these inputs are zero, so an eye is what buys them. The <em>blind</em> mode is the knockout: the same world with sense forced to 0.</figcaption>
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


def sensor_lineages(run, min_steps=20_000):
    """Lineages whose mean sensor blocks per body is at least 1, and for how long they held it."""
    lin = load_rows(f"results/{run}_lineages.csv")
    by = defaultdict(list)
    for r in lin:
        by[int(r["lineage"])].append(r)
    out = []
    for lid, rows in by.items():
        eyes = [r for r in rows if float(r["sensor"]) >= 1.0]
        if not eyes:
            continue
        span = int(eyes[-1]["step"]) - int(eyes[0]["step"]) + CONFIRM_STEPS
        if span < min_steps:
            continue
        peak = max(eyes, key=lambda r: int(r["size"]))
        out.append(dict(id=lid, span=span, first=int(eyes[0]["step"]), last=int(eyes[-1]["step"]), size=int(peak["size"]),
                        sensor=float(peak["sensor"]), attack=float(peak["attack"]), hard=float(peak["hard"]), muscle=float(peak["muscle"]), digestive=float(peak["digestive"]),
                        meat=float(peak["meat"]), plant=float(peak["plant"])))
    out.sort(key=lambda d: -d["span"])
    return out


def carnivore_count(run, min_steps=20_000):
    lin = load_rows(f"results/{run}_lineages.csv")
    by = defaultdict(list)
    for r in lin:
        by[int(r["lineage"])].append(r)
    n = 0
    for rows in by.values():
        c = [r for r in rows if float(r["meat"]) > float(r["plant"])]
        if c and int(c[-1]["step"]) - int(c[0]["step"]) + CONFIRM_STEPS >= min_steps:
            n += 1
    return n


def grazer_intake(run, half_step=500_000):
    """Plant intake per digestive block per step of grazers (0 muscle, age >= 50) in the second half, with and without sensors."""
    with_s, without = [], []
    for r in load_rows(f"results/{run}_agents.csv"):
        if int(r["step"]) <= half_step or int(r["muscle"]) > 0 or int(r["age"]) < 50 or int(r["digestive"]) == 0:
            continue
        v = float(r["plant"]) / int(r["age"]) / int(r["digestive"])
        (with_s if int(r["sensor"]) > 0 else without).append(v)
    m = lambda x: statistics.mean(x) if x else float("nan")
    return m(with_s), m(without), len(with_s), len(without)


def main():
    logs = {v: {s: load_csv(f"results/{p}_seed{s}_log.csv") for s in SEEDS} for v, p in VARIANTS.items()}
    events = {v: {s: load_rows(f"results/{p}_seed{s}_events.csv") for s in SEEDS} for v, p in VARIANTS.items()}

    def by_variant(key, seed=1):
        return [(v, logs[v][seed]["step"], logs[v][seed][key], k) for k, v in enumerate(VARIANTS)]

    def by_seed(v, key):
        return [(f"Seed {s}", logs[v][s]["step"], logs[v][s][key], k) for k, s in enumerate(SEEDS)]

    def ratio(log, a, b):
        return [x / max(y, 1) for x, y in zip(log[a], log[b])]

    def escape_share(log):
        return [e / max(e + k, 1) for e, k in zip(log["escapes"], log["deaths_eaten"])]

    def eaten_rate_ratio(log):
        """Per-capita rate of being eaten, agents with sensors over agents without, per window (nan where undefined)."""
        out = []
        for pop, share, eaten, eaten_s in zip(log["pop"], log["sensor_agents_share"], log["deaths_eaten"], log["eaten_with_sensor"]):
            ns, nn = pop * share, pop * (1 - share)
            if ns < 5 or nn < 5 or eaten - eaten_s <= 0:
                out.append(float("nan"))
            else:
                out.append((eaten_s / ns) / ((eaten - eaten_s) / nn))
        return out

    def med(x):
        x = [v for v in x if v == v]
        return statistics.median(x) if x else float("nan")

    def summarize(v, s):
        log = logs[v][s]
        ev = events[v][s]
        run = f"{VARIANTS[v]}_seed{s}"
        first, last, size = lineage_stats(run)
        life = [last[i] - first[i] + CONFIRM_STEPS for i in first]
        n_lin = load_rows(f"results/{run}_lineages.csv")
        per_step = Counter(int(r["step"]) for r in n_lin)
        last_step = int(log["step"][-1])
        counts = Counter(r["event"] for r in ev)
        half = [i for i, t in enumerate(log["step"]) if t > last_step / 2]
        # Second-half per-capita rates: eaten and kills, with sensors vs without.
        def rate(idx, num_s, num_all):
            ns = sum(log["pop"][i] * log["sensor_agents_share"][i] for i in idx)
            nn = sum(log["pop"][i] * (1 - log["sensor_agents_share"][i]) for i in idx)
            es = sum(log[num_s][i] for i in idx)
            en = sum(log[num_all][i] - log[num_s][i] for i in idx)
            return (es / ns) / (en / nn) if ns > 0 and nn > 0 and en > 0 else float("nan"), ns / max(ns + nn, 1)
        eaten_ratio, share_half = rate(half, "eaten_with_sensor", "deaths_eaten")
        kill_ratio, _ = rate(half, "kills_by_sensor", "deaths_eaten")
        gw, gwo, nw, nwo = grazer_intake(run)
        eyes = sensor_lineages(run)
        return dict(
            pop=med(log["pop"]), sensor=med(log["sensor_mean"]), sensor_max=max(log["sensor_mean"]), sensor_windows=sum(1 for m in log["sensor_mean"] if m > 1.0) * 10_000,
            sensor_agents=med(log["sensor_agents_share"]), share_half=share_half,
            used=med([u for u, d in zip(log["sense_used"], log["sense_decisions"]) if d > 0]),
            who_used=med([u for u, d in zip(log["who_used"], log["who_decisions"]) if d > 0] or [float("nan")]),
            who_share=sum(log["who_decisions"]) / max(sum(log["sense_decisions"]), 1),
            eaten_ratio=eaten_ratio, kill_ratio=kill_ratio, grazer_with=gw, grazer_without=gwo, n_grazer_with=nw,
            eaten=sum(log["deaths_eaten"]) / max(sum(log["births"]), 1), escapes=sum(log["escapes"]) / max(sum(log["escapes"]) + sum(log["deaths_eaten"]), 1),
            meat=sum(log["meat_intake"]) / max(sum(log["plant_intake"]) + sum(log["meat_intake"]), 1),
            attack=med(log["attack_mean"]), hard=med(log["hard_mean"]), muscle=med(log["muscle_mean"]), digestive=med(log["digestive_mean"]),
            lineages=med([per_step.get(t, 0) for t in range(1000, last_step + 1, 1000)]), ids=len(first), life=med(life) if life else 0,
            rate=sum(counts.values()) / (last_step // 1000), eyes=len(eyes), eyes_span=eyes[0]["span"] if eyes else 0, carn=carnivore_count(run),
            sps=med(log["steps_per_sec"]), sps_min=min(log["steps_per_sec"]),
        )

    S = {(v, s): summarize(v, s) for v in VARIANTS for s in SEEDS}
    eyes_all = {(v, s): sensor_lineages(f"{VARIANTS[v]}_seed{s}") for v in VARIANTS for s in SEEDS}

    charts = {}
    smax = max(max(logs[w][s]["sensor_mean"]) for w in VARIANTS for s in SEEDS) * 1.12
    for k, v in enumerate(VARIANTS):
        charts[f"sensor_{k}"] = line_chart(f"Sensor blocks per body ({v})", "Population mean of sensor blocks, every 10,000 steps; same scale in all three. A plateau is a lineage that kept its eyes.", by_seed(v, "sensor_mean"), ymin=0, ymax=smax)
        charts[f"eaten_ratio_{k}"] = line_chart(f"Eaten per capita, with eyes over without ({v})", "Rate of being eaten for agents with sensors divided by the rate for agents without, per window. Below 1: eyes are eaten less. Gaps: too few agents on one side.", [(f"Seed {s}", logs[v][s]["step"], eaten_rate_ratio(logs[v][s]), j) for j, s in enumerate(SEEDS)], ymin=0, ymax=3)
    charts["who_used"] = line_chart("Who inputs in use (who)", "Of the moves decided by agents with sensors that saw a threat or prey, the share that differs from the move with the who inputs zeroed. 0% means seeing who changes nothing.", by_seed("who", "who_used"), ymin=0, percent=True)
    charts["used_who"] = line_chart("Sensors in use (who)", "Of the moves decided by agents with sensor blocks, the share that differs from the move the same policy picks blind.", by_seed("who", "sense_used"), ymin=0, percent=True)
    charts["escapes"] = line_chart("Escapes per encounter (seed 1)", "Escapes divided by escapes plus kills, per window. Higher means prey get away more often.", [(v, logs[v][1]["step"], escape_share(logs[v][1]), k) for k, v in enumerate(VARIANTS)], ymin=0, percent=True)
    charts["eaten"] = line_chart("Predation deaths per birth (seed 1)", "Agents eaten divided by agents born in each window.", [(v, logs[v][1]["step"], ratio(logs[v][1], "deaths_eaten", "births"), k) for k, v in enumerate(VARIANTS)], ymin=0)
    charts["pop"] = line_chart("Population (seed 1)", "Living agents on four islands.", by_variant("pop"), ymin=0)
    charts["attack"] = line_chart("Attack per body (seed 1)", "Population mean of attack = min(hard blocks in the front rows, muscle blocks).", by_variant("attack_mean"), ymin=0)
    charts["hard"] = line_chart("Hard blocks per body (seed 1)", "Population mean. Defense is hard / 2; 46 or more is immune to any bite.", by_variant("hard_mean"), ymin=0)
    charts["lineages"] = line_chart("Lineages alive (seed 1)", "Confirmed lineages at each log step.", by_variant("lineages"), ymin=0)
    charts["sps"] = line_chart("Steps per second (seed 1)", "Simulation speed, twelve runs sharing one machine, one thread each.", by_variant("steps_per_sec"), ymin=0)

    timeline = timeline_chart(f"Lineages over time ({VIEWER_LABEL})", "Each colored band is one lineage, height = agents in it; marks are events at the size they were logged with.", VIEWER_RUN, events[VIEWER_VARIANT][VIEWER_SEED])

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

    def fmt_ratio(x):
        return "-" if x != x else f"{x:.2f}"

    def row(label, f):
        return f"<tr><td>{label}</td>" + "".join(f"<td>{f(S[(v, s)])}</td>" for v in VARIANTS for s in SEEDS) + "</tr>"

    summary = ("<thead><tr><th>Measure</th>" + "".join(f"<th>{v}<br>seed {s}</th>" for v in VARIANTS for s in SEEDS) + "</tr></thead><tbody>"
               + row("Population, median", lambda d: f"{d['pop']:,.0f}")
               + row("Sensor blocks per body, median (max)", lambda d: f"{d['sensor']:.2f} ({d['sensor_max']:.1f})")
               + row("Steps with sensor mean above 1", lambda d: f"{d['sensor_windows']:,}")
               + row("Sensor lineages (mean &ge; 1 sensor for 20,000+ steps)", lambda d: f"{d['eyes']}")
               + row("Longest sensor lineage (steps)", lambda d: f"{d['eyes_span']:,}")
               + row("Agents with any sensor, median share", lambda d: f"{d['sensor_agents']:.0%}")
               + row("Sensors in use, median share of decisions", lambda d: "-" if d['used'] != d['used'] else f"{d['used']:.0%}")
               + row("Decisions with a who input above 0, share of sensor decisions", lambda d: "-" if d['who_share'] == 0 else f"{d['who_share']:.1%}")
               + row("Who inputs in use, median share of those", lambda d: "-" if d['who_used'] != d['who_used'] else f"{d['who_used']:.0%}")
               + row("Agents with any sensor, 2nd half share", lambda d: f"{d['share_half']:.0%}")
               + row("Eaten per capita, with eyes / without (2nd half; - if eyes under 5%)", lambda d: fmt_ratio(d['eaten_ratio']) if d['share_half'] >= 0.05 else "-")
               + row("Kills per capita, with eyes / without (same)", lambda d: fmt_ratio(d['kill_ratio']) if d['share_half'] >= 0.05 else "-")
               + row("Grazer intake per digestive block, with / without eyes", lambda d: f"{d['grazer_with']:.4f} / {d['grazer_without']:.4f}" if d['grazer_with'] == d['grazer_with'] else f"- / {d['grazer_without']:.4f}")
               + row("Escapes per encounter", lambda d: f"{d['escapes']:.1%}")
               + row("Predation deaths per birth", lambda d: f"{d['eaten']:.2f}")
               + row("Meat share of intake", lambda d: f"{d['meat']:.1%}")
               + row("Carnivore lineages (meat &gt; plant, 20,000+ steps)", lambda d: f"{d['carn']}")
               + row("Attack per body, median", lambda d: f"{d['attack']:.1f}")
               + row("Hard / muscle / digestive blocks, median", lambda d: f"{d['hard']:.0f} / {d['muscle']:.0f} / {d['digestive']:.0f}")
               + row("Lineages alive, median", lambda d: f"{d['lineages']:.0f}")
               + row("Lifetime, median (steps)", lambda d: f"{d['life']:,.0f}")
               + row("Steps per second, median (min)", lambda d: f"{d['sps']:,.0f} ({d['sps_min']:,.0f})")
               + "</tbody>")

    eye_rows = []
    for (v, s), lst in eyes_all.items():
        for c in lst[:3]:
            diet = c["meat"] / (c["meat"] + c["plant"]) if c["meat"] + c["plant"] > 0 else 0
            eye_rows.append(f"<tr><td>{v}, seed {s}</td><td>{c['id']}</td><td>{c['first']:,}-{c['last']:,}</td><td>{c['span']:,}</td><td>{c['size']}</td><td>{c['sensor']:.1f}</td><td>{c['attack']:.0f}</td><td>{c['hard']:.0f} / {c['muscle']:.0f} / {c['digestive']:.0f}</td><td>{diet:.0%}</td></tr>")
    eye_table = ("<thead><tr><th>Run</th><th>Lineage</th><th>Sensor &ge; 1 from-to</th><th>Steps</th><th>Peak size</th><th>Sensors</th><th>Attack</th><th>Hard / muscle / digestive</th><th>Meat share</th></tr></thead><tbody>"
                 + "".join(eye_rows) + "</tbody>") if eye_rows else ""

    tables = data_table(["step", "pop", "births", "deaths_eaten", "escapes", "sensor_mean", "sensor_agents_share", "sense_used", "who_decisions", "who_used", "eaten_with_sensor", "kills_by_sensor", "attack_mean", "hard_mean", "lineages", "steps_per_sec"],
                        {f"{v} seed {s} (every 100,000 steps)": logs[v][s] for v in VARIANTS for s in SEEDS}, every=10)

    text = TEXT
    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>e009 Perception - Report</title>
<style>{CSS}</style>
</head>
<body>
<main>
<h1>e009: Does an eye pay once it can tell prey from threat?</h1>
<p class="sub">Experiment report - 2026-08-29 - 128x128 patchy world, policy inputs counts (e007) / who (can eat me, can I eat it) / blind (sense knocked out), four seeds, 1,000,000 steps each</p>

<section class="tldr">
<h2>TL;DR</h2>
<p>{text["tldr"]}</p>
</section>

<h2>1. Question</h2>
<p>{text["question"]}</p>
<ol>
  <li><strong>Eyes pay when they can see who.</strong> In <em>who</em>, agents with sensors are eaten less often per capita than agents without (ratio below 0.8) or kill more, and the sensor mean stays above 1 for 100,000+ steps in at least two of four seeds.</li>
  <li><strong>e007's eyes were passengers.</strong> In <em>blind</em>, sensor blocks appear at the same rate as in <em>counts</em>.</li>
  <li><strong>Behavior changes.</strong> In <em>who</em>, escapes per encounter rise and predation deaths per birth fall against <em>counts</em>; the who inputs change more than 10% of the decisions where they are non-zero; speed within 20% of <em>counts</em>.</li>
</ol>

<h2>2. The world</h2>
<p>{text["world"]}</p>
{DIAGRAM}
<p><strong>Runs.</strong> counts, who, blind, seeds 1-4, 1,000,000 steps on the 128x128 patchy world (four islands); twelve runs sharing one machine, one thread each. <em>counts</em> is e007 <em>128 patchy</em> byte for byte; <em>who</em> at the same seed has the same laws and initial population. We record, every 10,000 steps, on top of e008's log:</p>
<ul class="measures">
  <li><strong>Eaten with eyes</strong>: prey killed that had a sensor block; with the share of agents carrying sensors this gives the per-capita rate of being eaten, with eyes and without.</li>
  <li><strong>Kills with eyes</strong>: kills made by an eater with a sensor block, the same way.</li>
  <li><strong>Who inputs in use</strong>: decisions by agents with sensors where a who input was non-zero, and the share where the move differs from the move with those inputs zeroed.</li>
  <li><strong>Sensors in use</strong> as e007: the share of decisions that differ from the blind choice.</li>
  <li><strong>Escapes per encounter</strong>, predation deaths per birth, meat share.</li>
  <li><strong>Sensor lineages</strong>: lineages with a mean of at least 1 sensor block for 20,000+ steps; <strong>grazer intake</strong> per digestive block with and without sensors (second half, grazers of age 50+), from the agent dumps.</li>
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
{charts["sensor_2"]}{charts["who_used"]}
</div>
{"<div class='tw'><table>" + eye_table + "</table></div>" if eye_table else ""}
<p>{text["r1"]}</p>

<h3>3.2 {text["h2"]}</h3>
<div class="grid2">
{charts["eaten_ratio_1"]}{charts["eaten_ratio_0"]}
</div>
<div class="grid2">
{charts["escapes"]}{charts["eaten"]}
</div>
<p>{text["r2"]}</p>

<h3>3.3 {text["h3"]}</h3>
<div class="grid2">
{charts["pop"]}{charts["attack"]}
</div>
<div class="grid2">
{charts["hard"]}{charts["lineages"]}
</div>
<div class="wide">{timeline}</div>
<p>{text["r3"]}</p>

<h3>3.4 Watching the world</h3>
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
  <div class="bar" id="legend">Blocks: {legend} <span class="sw dot"></span> can bite (attack &gt; 0)</div>
  <div class="bar">Left: the whole 128x128 world, each agent colored by its lineage (gray: none), a white dot on agents with attack above 0. Green: food; the bright spots are the patches. Click to move the white box. Right: the box at 24x24 cells, bodies drawn on the lineage color. Labels: agents per lineage, then mean attack (teeth), defense (armor), and sensor blocks (eyes). {VIEWER_LABEL}.</div>
</div>
<p>{text["viewer"]}</p>
<div class="grid2">{charts["used_who"]}{charts["sps"]}</div>

<h2>4. Discussion</h2>
{text["discussion"]}

<h2>5. Conclusion and next step</h2>
<p>{text["conclusion"]}</p>

<h2>Appendix: data</h2>
<p>Every 100,000th record; full logs in <code>results/*_log.csv</code>, lineages in <code>results/*_lineages.csv</code>, events in <code>results/*_events.csv</code>, snapshots in <code>results/*_{{long,clip,bodies}}.jsonl</code>. Build this report with <code>uv run python experiments/e009_perception/report.py</code>.</p>
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
    "tldr": "Telling an agent who is next to it does not make eyes pay, because there is almost never anyone to see. In the who mode the new inputs are non-zero in 1% of the decisions made by agents with sensors: a body in this world is an armored grazer among armored kin, immune to every bite and able to bite nobody, so threat and prey are both zero almost every step, while the eye costs upkeep every step and its new weights add noise to the moves until evolved. Sensor blocks are selected less with the who inputs than without (16 sensor lineages in four seeds against 43; 30,000 steps with the mean above 1 against 160,000), escapes and predation are unchanged, and grazers with eyes take in no more food. The knockout says e007's eyes were not quite passengers: with sense forced to 0, sensor lineages drop to 6 and the mean never passes 1, in every seed fewer than with the distance-2 inputs. But the rebate is small and shows in nothing we measure. Perception is not the lever either; the lever is a world where who is next to you matters, which means bodies that can be bitten. Next: the attack cap and the price of armor.",
    "question": "e007 found sensor blocks that stayed but could not show that they paid; e008 found that carnivory is limited by access, not by the value of a kill: an agent cannot tell who is next to it. This experiment gives the policy that information, paid for by sensor blocks, and knocks sense out in the same world to separate an eye that pays from one that rides along. We add no rule for fleeing or hunting; only inputs.",
    "world": "Everything is e007 <em>128 patchy</em> (four islands, e007's kill value, the diet columns of e008 in the lineage log). What changes is what the policy sees (Figure 1). e007's ten inputs stay. Mode <em>who</em> adds eight: per direction, how many neighbors at distance 1 and 2 could eat the agent, and how many it could eat, by the predation rule itself (attack above defense, mass within gut, not the same body), times sense = sensor blocks / 8. Mode <em>blind</em> forces sense to 0 for everyone. The weights of the new inputs come from their own random stream, so <em>counts</em> is e007 byte for byte and <em>who</em> at the same seed shares its laws, initial population, and e007 weights.",
    "c1": "no", "l1": "No", "v1": "With the who inputs, sensor blocks are selected less, not more: median 0.01-0.14 per body against 0.00-0.47 in counts, 30,000 steps with the mean above 1 (one seed) against 160,000, 16 sensor lineages against 43. Grazers with eyes take in 0.0094-0.0113 per digestive block per step against 0.0098-0.0121 without. Only seed 4 has enough eyes to compare predation: agents with eyes are eaten half as often per capita (0.51; counts seed 4: 1.34), one seed, and it did not make them spread.",
    "c2": "partly", "l2": "Partly", "v2": "The population mean is the same blind as with the distance-2 inputs (0.00-0.12 against 0.00-0.47) and the eye is in use in 17-19% of decisions in counts. But lineages with an eye are fewer blind in every seed (2 / 0 / 4 / 0 against 8 / 1 / 25 / 9) and the mean never passes 1 (0 steps against 160,000). The distance-2 inputs were worth something to a lineage; nothing we measure shows what.",
    "c3": "partly", "l3": "Partly", "v3": "Where a who input is non-zero, it changes the move in 19-24% of the decisions. But that is 1% of the decisions of agents with sensors. Escapes per encounter are 1.6-6.9% against 1.3-5.9%, predation deaths per birth 0.25-0.47 against 0.31-0.44: unchanged. Speed 1,674-2,030 steps per second against 1,748-2,462, within 20%.",
    "h1": "Eyes are selected less with the who inputs, and there is almost nothing to see",
    "r1": "Top row: counts (e007) and who at the same seeds. Seed 4 of counts carries a sensor lineage for 760,000 steps (lineage 233, an armored grazer with one sensor block); in who the same seed has a grazer lineage with one sensor for 377,000 steps and the mean stays below 0.6. Seed 3, the seed that grows eyes in e007, makes 25 sensor lineages in counts and 12 in who. Bottom left, blind: the mean never passes 0.6 and sensor lineages are 6 in four seeds. Bottom right: where a who input is non-zero it changes the move in 19-24% of cases, so the policy does read it. The table lists the longest sensor lineages: every one is an armored grazer (hard 37-44, attack 0) with one or two sensor blocks, except a hunter with one sensor in counts seed 4 and one in blind seed 3. The number that explains the rest is in the summary table: in who, a who input is non-zero in 1.0-1.4% of the decisions of agents with sensors. An armored grazer with defense 20 cannot be eaten by anyone (attack is at most 24, and 24-attack hunters are rare booms), and with attack 0 can eat nobody; its threat and prey inputs are zero every step. The eye is paid for every step and used once in a hundred.",
    "h2": "Seeing who changes nothing in who gets eaten",
    "r2": "The per-capita rate of being eaten for agents with eyes over agents without (top row) is a noisy line: with 0-6% of agents carrying sensors, a few catchable mutants with a sensor block swing it. Seed 4 is the exception in both modes (22% with eyes in counts, 13% in who); there, agents with eyes are eaten 1.34 times as often as agents without in counts and 0.51 times in who. That is the one result in the direction of the hypothesis, in one seed, and the lineage behind it (284, an armored grazer with one sensor block) did not grow past 6% of the population. Bottom row: escapes per encounter stay at 1-7% and predation deaths per birth at 0.25-0.5 in every mode; the blind runs have the highest escape rate (15% in seed 1), which comes from a muscular grazer lineage there, not from seeing. Kills are decided by bodies, not by moves: the prey is younger than the eater in 75% of kills, so the eater moves first in that step; 15% of prey die at age 0, before their first move (instrumented trial, seed 9, 30,000 steps).",
    "h3": "The world is the same in all three modes",
    "r3": "Population 810-1,260, attack 1.7-6.8, hard 25-41, lineages alive 4-9: the three modes are within the seed spread of each other on every measure of the world. Carnivore lineages: 1 in counts, 6 in who, 0 in blind, all without eyes (sensor 0.0-0.1 per body); the who inputs cannot be what made them, since a hunter without sensors sees nothing. The timeline of who seed 4 shows the sensor lineage 284 as one of the bands from step 628,000: an ordinary grazer lineage that happens to carry one sensor block.",
    "viewer": "who, seed 4. From step 628,000 lineage 284 (eyes 1.0, teeth 0, armor 21) is one of the large grazer lineages; nothing in its behavior tells it apart from the sensor-less lineages beside it. Hunters (white dots) are rare and blind. In the clip, agents on a patch move little; the who inputs of nearly all of them are zero, because nobody around them can be bitten.",
    "discussion": "<p>The premise of issue #8 was that seeing further buys nothing because the inputs do not say whether a neighbor can eat you. Now they do, and it still buys nothing, for a reason the numbers make plain: in this world a neighbor that can eat you, or that you can eat, is next to you one step in a hundred. Predation is decided by the body plan before any move is made. An armored grazer is immune; a hunter can bite only the few bodies under 46 hard blocks, and it bites them when they are born next to it. Perception is an input to a decision that the rules do not leave open.</p><p>The knockout adds a nuance to e007. With sense forced to 0, lineages with a sensor block are fewer in every seed, and the mean never passes 1; so the distance-2 inputs did give a lineage with a sensor block something. But it is a small rebate on a cheap block (two sensor blocks cost 2% of a grazer's intake), invisible in intake, predation, or lineage lifetime. The honest description of e007's eyes is a near-neutral passenger with a slight tailwind.</p><p>Two things this experiment does not show. It does not show that the who inputs could not be used: where they are non-zero they change one move in five, and one seed had agents with eyes eaten half as often. It does not show what happens to eyes in a world where being next to somebody matters. Both point the same way. Every experiment since e005 has found the same wall from a different side: attack is capped at 24 by three front rows, defense goes to 32, and armor costs the same per block as anything else, so the population armors up and predation becomes a tax on newborns. e008 could not raise meat with a prize, e009 cannot raise it with eyes. The next change is to the wall itself: a bite that can grow beyond 24 or armor that costs more than a block of gut, so that there are bodies worth seeing.</p>",
    "conclusion": "Perception is not the lever. Given inputs that say who can eat whom, agents with eyes have those inputs non-zero once in a hundred decisions; sensor blocks are selected less than before, and nothing in predation, escapes, or intake moves. The knockout shows e007's eyes were a passenger with a slight tailwind: fewer sensor lineages and none above a mean of 1 when sense is forced to 0, but no measurable gain when it is not. Keep the who inputs in the code (they cost nothing where sense is 0) and keep e007's law (counts). The wall is the body plan: attack capped at 24, cheap armor. Next: make bodies biteable, with a bite that can grow (attack from hard blocks over more of the body, or muscle multiplying it) or armor that costs more, then run who and counts again on the same world. Only when who is next to you matters can an eye be tested; and only then is there a predator-prey arms race for the viewer to watch.",
}

if __name__ == "__main__":
    main()
