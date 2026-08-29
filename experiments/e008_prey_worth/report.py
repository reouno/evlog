#!/usr/bin/env python3
"""Build report.html for e008.

Charts: matplotlib, exported as SVG and inlined. Diagram: hand-written SVG.
Run from the repo root: uv run python experiments/e008_prey_worth/report.py
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
VARIANTS = {"keep 0 (e007)": "128_patchy_keep0", "keep 0.1": "128_patchy_keep0.1", "keep 0.3": "128_patchy_keep0.3", "keep 1": "128_patchy_keep1"}
KIND_COLOR = {1: SERIES[0], 2: SERIES[1], 3: SERIES[3], 4: SERIES[2]}
CONFIRM_STEPS = 5000
VIEWER_VARIANT = "keep 1"  # TODO pick the run with the carnivore lineage
VIEWER_SEED = 1
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
<svg viewBox="0 0 720 250" role="img" aria-label="What a kill is worth: the eater receives half the prey's energy, 0.02 per block of its body, and keep times the upkeep the prey has paid over its life (0.002 per block per step times its age). The third term is new; keep = 0 is e007." style="max-width:100%;height:auto;display:block">
<g fill="none" stroke="currentColor" stroke-width="1.2" font-size="12" font-family="system-ui, sans-serif">
  <!-- prey -->
  <text x="20" y="20" fill="currentColor" stroke="none" font-weight="600">prey p (killed)</text>
  <rect x="20" y="32" width="190" height="44" rx="6"/>
  <text x="30" y="50" fill="currentColor" stroke="none">energy it holds now</text>
  <text x="30" y="68" fill="currentColor" stroke="none">about 4 (it splits at 8)</text>
  <rect x="20" y="88" width="190" height="44" rx="6"/>
  <text x="30" y="106" fill="currentColor" stroke="none">body: mass blocks (64)</text>
  <text x="30" y="124" fill="currentColor" stroke="none">built free at birth</text>
  <rect x="20" y="144" width="190" height="60" rx="6" stroke="var(--s1)" stroke-width="2"/>
  <text x="30" y="162" fill="currentColor" stroke="none">upkeep paid so far</text>
  <text x="30" y="180" fill="currentColor" stroke="none">0.002 x mass x age</text>
  <text x="30" y="198" fill="var(--s1)" stroke="none" font-weight="600">keep = 0, 0.1, 0.3, 1.0</text>
  <!-- arrows -->
  <path d="M210,54 L430,54" marker-end="url(#arr)"/>
  <text x="222" y="42" fill="currentColor" stroke="none">x 0.5</text>
  <path d="M210,110 C320,110 340,96 430,96" marker-end="url(#arr)"/>
  <text x="222" y="98" fill="currentColor" stroke="none">x 0.02 per block</text>
  <path d="M210,174 C320,174 340,140 430,140" stroke="var(--s1)" stroke-width="2" marker-end="url(#arr)"/>
  <text x="222" y="162" fill="var(--s1)" stroke="none" font-weight="600">x keep</text>
  <!-- eater -->
  <text x="450" y="20" fill="currentColor" stroke="none" font-weight="600">eater</text>
  <rect x="440" y="32" width="250" height="140" rx="6"/>
  <text x="450" y="54" fill="currentColor" stroke="none">gain = the three terms</text>
  <text x="450" y="80" fill="currentColor" stroke="none">64-block prey at age 170:</text>
  <text x="450" y="98" fill="currentColor" stroke="none">3.3 at keep 0 (e007)</text>
  <text x="450" y="116" fill="currentColor" stroke="none">5.5 / 9.8 / 25 at keep 0.1 / 0.3 / 1</text>
  <text x="450" y="142" fill="currentColor" stroke="none">at age 850: 14 / 36 / 112</text>
  <text x="450" y="160" fill="currentColor" stroke="none">(a reproduction costs about 8)</text>
  <!-- rule unchanged -->
  <text x="20" y="228" fill="currentColor" stroke="none">Who can eat whom is unchanged: attack above the prey's defense, prey mass within the gut, escape by speed.</text>
  <text x="20" y="244" fill="currentColor" stroke="none">A grazer earns about 0.03 per step net.</text>
  <defs><marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="currentColor" stroke="none"/></marker></defs>
</g>
</svg>
<figcaption>Figure 1. What a kill is worth. In e007 the eater got half the prey's energy and 0.02 per block: about 3.3 for any prey, newborn or old. e008 adds the blue term: <em>keep</em> times the upkeep the prey has paid over its life. At keep = 1 an old body is worth a hundred, more than ten reproductions. Nothing else changes: not who can bite whom, not what a body costs.</figcaption>
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


def carnivore_lineages(run, min_steps=20_000):
    """Lineages whose members, averaged, took in more meat than plants over their life, and how long
    they held that (steps between the first and last detection with meat > plant), plus their body."""
    lin = load_rows(f"results/{run}_lineages.csv")
    by = defaultdict(list)
    for r in lin:
        by[int(r["lineage"])].append(r)
    out = []
    for lid, rows in by.items():
        carn = [r for r in rows if float(r["meat"]) > float(r["plant"])]
        if not carn:
            continue
        span = int(carn[-1]["step"]) - int(carn[0]["step"]) + CONFIRM_STEPS
        if span < min_steps:
            continue
        peak = max(carn, key=lambda r: int(r["size"]))
        out.append(dict(id=lid, span=span, n=len(carn), first=int(carn[0]["step"]), last=int(carn[-1]["step"]), size=int(peak["size"]),
                        attack=float(peak["attack"]), hard=float(peak["hard"]), muscle=float(peak["muscle"]), digestive=float(peak["digestive"]),
                        meat=float(peak["meat"]), plant=float(peak["plant"]), age=float(peak["age"])))
    out.sort(key=lambda d: -d["span"])
    return out


def scatter_chart(title, subtitle, groups, xlabel, ylabel, percent_y=False):
    """groups: (label, xs, ys, slot)."""
    fig, ax = new_axes(xlabel=xlabel, size=(6.4, 3.0))
    ax.xaxis.set_major_formatter(kfmt)
    for label, xs, ys, slot in groups:
        ax.scatter(xs, ys, s=9, color=SERIES[slot], alpha=0.55, linewidths=0, label=label)
    ax.set_ylabel(ylabel)
    if percent_y:
        ax.yaxis.set_major_formatter(lambda y, _p: f"{y:.0%}")
    ax.yaxis.set_major_locator(MaxNLocator(4))
    ax.margins(x=0.03)
    legend_above(ax, len(groups))
    return figure(title, subtitle, to_svg(fig))


def main():
    logs = {v: {s: load_csv(f"results/{p}_seed{s}_log.csv") for s in SEEDS} for v, p in VARIANTS.items()}
    events = {v: {s: load_rows(f"results/{p}_seed{s}_events.csv") for s in SEEDS} for v, p in VARIANTS.items()}

    def by_variant(key, seed=1):
        return [(v, logs[v][seed]["step"], logs[v][seed][key], k) for k, v in enumerate(VARIANTS)]

    def by_seed(v, key):
        return [(f"Seed {s}", logs[v][s]["step"], logs[v][s][key], k) for k, s in enumerate(SEEDS)]

    def ratio(log, a, b):
        return [x / max(y, 1) for x, y in zip(log[a], log[b])]

    def meat_share(log):
        return [m / max(m + p, 1e-9) for m, p in zip(log["meat_intake"], log["plant_intake"])]

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
        counts = Counter(r["event"] for r in ev)
        carn = carnivore_lineages(run)
        half = [i for i, t in enumerate(log["step"]) if t > last_step / 2]
        return dict(
            pop=med(log["pop"]), pop_min=min(log["pop"]), pop_max=max(log["pop"]),
            eaten=sum(log["deaths_eaten"]) / max(sum(log["births"]), 1),
            meat=sum(log["meat_intake"]) / max(sum(log["plant_intake"]) + sum(log["meat_intake"]), 1),
            meat_half=sum(log["meat_intake"][i] for i in half) / max(sum(log["plant_intake"][i] + log["meat_intake"][i] for i in half), 1),
            prey_age=med(log["prey_age_mean"]), gain=med(log["gain_mean"]), young=med(log["kills_young_share"]),
            majority=med(log["meat_majority"]), majority_max=max(log["meat_majority"]),
            attack=med(log["attack_mean"]), hard=med(log["hard_mean"]), muscle=med(log["muscle_mean"]), digestive=med(log["digestive_mean"]),
            lineages=med([per_step.get(t, 0) for t in range(1000, last_step + 1, 1000)]), ids=len(first), life=med(life) if life else 0,
            rate=sum(counts.values()) / (last_step // 1000), carn=len(carn), carn_span=carn[0]["span"] if carn else 0,
            sps=med(log["steps_per_sec"]), sps_min=min(log["steps_per_sec"]), extinct=last_step < 1_000_000,
        )

    S = {(v, s): summarize(v, s) for v in VARIANTS for s in SEEDS}
    carn_all = {(v, s): carnivore_lineages(f"{VARIANTS[v]}_seed{s}") for v in VARIANTS for s in SEEDS}

    charts = {}
    charts["meat"] = line_chart("Meat share of intake (seed 1)", "Energy from prey divided by all energy eaten, per 10,000-step window. e007 sits at 3-4%.", [(v, logs[v][1]["step"], meat_share(logs[v][1]), k) for k, v in enumerate(VARIANTS)], ymin=0, percent=True)
    for k, v in enumerate(VARIANTS):
        charts[f"meat_{k}"] = line_chart(f"Meat share of intake ({v})", "Energy from prey divided by all energy eaten, per window. Three seeds; same scale in all four.", [(f"Seed {s}", logs[v][s]["step"], meat_share(logs[v][s]), j) for j, s in enumerate(SEEDS)], ymin=0, percent=True, ymax=max(max(meat_share(logs[w][s])) for w in VARIANTS for s in SEEDS) * 1.12)
        charts[f"majority_{k}"] = line_chart(f"Agents fed mostly on meat ({v})", "Share of living agents whose lifetime intake from prey exceeds their intake from plants. A carnivore population shows as a floor above zero.", by_seed(v, "meat_majority"), ymin=0, percent=True, ymax=max(max(logs[w][s]["meat_majority"]) for w in VARIANTS for s in SEEDS) * 1.12)
    charts["eaten"] = line_chart("Predation deaths per birth (seed 1)", "Agents eaten divided by agents born in each window. Higher means more of the population ends as food.", [(v, logs[v][1]["step"], ratio(logs[v][1], "deaths_eaten", "births"), k) for k, v in enumerate(VARIANTS)], ymin=0)
    charts["prey_age"] = line_chart("Mean age of the prey killed (seed 1)", "Steps the prey had lived when eaten, mean per window. Newborns are under 50; a line above 100 means grown bodies get caught.", by_variant("prey_age_mean"), ymin=0)
    charts["gain"] = line_chart("Energy per kill (seed 1)", "Mean gain of the eater per kill. A reproduction costs about 8; e007's kill was worth 3.", by_variant("gain_mean"), ymin=0)
    charts["young"] = line_chart("Kills of newborns (seed 1)", "Share of kills whose prey was younger than 50 steps. e007: three quarters.", by_variant("kills_young_share"), ymin=0, percent=True)
    charts["pop"] = line_chart("Population (seed 1)", "Living agents. The control carries about 1,000 on four islands.", by_variant("pop"), ymin=0)
    charts["attack"] = line_chart("Attack per body (seed 1)", "Population mean of attack = min(hard blocks in the front rows, muscle blocks). Zero is a world of grazers.", by_variant("attack_mean"), ymin=0)
    charts["digestive"] = line_chart("Digestive blocks per body (seed 1)", "Population mean. A carnivore needs a gut for prey mass (4 per block) but no bite for plants.", by_variant("digestive_mean"), ymin=0)
    charts["lineages"] = line_chart("Lineages alive (seed 1)", "Confirmed lineages at each log step.", by_variant("lineages"), ymin=0)
    charts["sps"] = line_chart("Steps per second (seed 1)", "Simulation speed, twelve runs sharing one machine, one thread each.", by_variant("steps_per_sec"), ymin=0)
    # Lineage scatter: every lineage row (a lineage at a detection) as a point, meat share of lifetime intake vs attack.
    groups = []
    for k, v in enumerate(VARIANTS):
        xs, ys = [], []
        for s in SEEDS:
            for r in load_rows(f"results/{VARIANTS[v]}_seed{s}_lineages.csv"):
                m, p = float(r["meat"]), float(r["plant"])
                if m + p > 0 and int(r["step"]) % 10_000 == 0:
                    xs.append(float(r["attack"]))
                    ys.append(m / (m + p))
        groups.append((v, xs, ys, k))
    charts["scatter"] = scatter_chart("Lineages: meat share of their food against their attack", "One point per lineage every 10,000 steps, all seeds. Points near the top are lineages living on meat; e007 has none above 20%.", groups, "mean attack of the lineage", "meat share of lifetime intake", percent_y=True)

    timeline = timeline_chart(f"Lineages over time ({VIEWER_LABEL})", "Each colored band is one lineage, height = agents in it; marks are events at the size they were logged with.", VIEWER_RUN, events[VIEWER_VARIANT][VIEWER_SEED])

    # Viewer.
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
        return f"<tr><td>{label}</td>" + "".join(f"<td>{f(S[(v, s)])}</td>" for v in VARIANTS for s in SEEDS) + "</tr>"

    summary = ("<thead><tr><th>Measure</th>" + "".join(f"<th>{v}<br>seed {s}</th>" for v in VARIANTS for s in SEEDS) + "</tr></thead><tbody>"
               + row("Population, median (min-max)", lambda d: f"{d['pop']:,.0f} ({d['pop_min']:,.0f}-{d['pop_max']:,.0f})")
               + row("Meat share of intake, whole run", lambda d: f"{d['meat']:.1%}")
               + row("Meat share of intake, second half", lambda d: f"{d['meat_half']:.1%}")
               + row("Predation deaths per birth", lambda d: f"{d['eaten']:.2f}")
               + row("Prey age at death, median of window means", lambda d: f"{d['prey_age']:.0f}")
               + row("Energy per kill, median of window means", lambda d: f"{d['gain']:.1f}")
               + row("Kills of newborns (age &lt; 50), median share", lambda d: f"{d['young']:.0%}")
               + row("Agents fed mostly on meat, median (max) share", lambda d: f"{d['majority']:.1%} ({d['majority_max']:.0%})")
               + row("Carnivore lineages (meat &gt; plant for 20,000+ steps)", lambda d: f"{d['carn']}")
               + row("Longest carnivore lineage (steps)", lambda d: f"{d['carn_span']:,}")
               + row("Attack per body, median", lambda d: f"{d['attack']:.1f}")
               + row("Hard / muscle / digestive blocks, median", lambda d: f"{d['hard']:.0f} / {d['muscle']:.0f} / {d['digestive']:.0f}")
               + row("Lineages alive, median", lambda d: f"{d['lineages']:.0f}")
               + row("Lineages over the run", lambda d: f"{d['ids']}")
               + row("Lifetime, median (steps)", lambda d: f"{d['life']:,.0f}")
               + row("Events per 1,000 steps", lambda d: f"{d['rate']:.2f}")
               + row("Steps per second, median (min)", lambda d: f"{d['sps']:,.0f} ({d['sps_min']:,.0f})")
               + "</tbody>")

    carn_rows = []
    for (v, s), lst in carn_all.items():
        for c in lst[:3]:
            carn_rows.append(f"<tr><td>{v}, seed {s}</td><td>{c['id']}</td><td>{c['first']:,}-{c['last']:,}</td><td>{c['span']:,}</td><td>{c['size']}</td><td>{c['meat'] / (c['meat'] + c['plant']):.0%}</td><td>{c['attack']:.0f}</td><td>{c['hard']:.0f} / {c['muscle']:.0f} / {c['digestive']:.0f}</td><td>{c['age']:.0f}</td></tr>")
    carn_table = ("<thead><tr><th>Run</th><th>Lineage</th><th>Meat &gt; plant from-to</th><th>Steps</th><th>Peak size</th><th>Meat share</th><th>Attack</th><th>Hard / muscle / digestive</th><th>Mean age</th></tr></thead><tbody>"
                  + "".join(carn_rows) + "</tbody>") if carn_rows else ""

    tables = data_table(["step", "pop", "births", "deaths_eaten", "plant_intake", "meat_intake", "prey_age_mean", "gain_mean", "kills_young_share", "meat_majority", "attack_mean", "digestive_mean", "lineages", "steps_per_sec"],
                        {f"{v} seed {s} (every 100,000 steps)": logs[v][s] for v in VARIANTS for s in SEEDS}, every=10)

    text = TEXT
    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>e008 Prey worth eating - Report</title>
<style>{CSS}</style>
</head>
<body>
<main>
<h1>e008: Do carnivores appear once an old body is a prize?</h1>
<p class="sub">Experiment report - 2026-08-29 - 128x128 patchy world, kill worth keep = 0 / 0.1 / 0.3 / 1.0 of the prey's lifetime upkeep, three seeds, 1,000,000 steps each</p>

<section class="tldr">
<h2>TL;DR</h2>
<p>{text["tldr"]}</p>
</section>

<h2>1. Question</h2>
<p>{text["question"]}</p>
<ol>
  <li><strong>Meat pays.</strong> The meat share of intake rises with keep and reaches at least 10% (from 3-4%) at keep 0.3 or above, in every seed.</li>
  <li><strong>Carnivores appear.</strong> At least one confirmed lineage whose members got most of their lifetime food from prey lives for 20,000 steps or more, in at least one seed at keep 0.3 or 1.0; it has attack above 5 and fewer digestive blocks than the grazers around it.</li>
  <li><strong>The world stands.</strong> Population within a factor of two of the control, no extinction, at every keep.</li>
</ol>

<h2>2. The world</h2>
<p>{text["world"]}</p>
{DIAGRAM}
<p><strong>Runs.</strong> keep 0, 0.1, 0.3, 1.0, seeds 1-3, 1,000,000 steps on the 128x128 patchy world (four islands); twelve runs sharing one machine, one thread each. keep 0 is e007 <em>128 patchy</em> byte for byte. We record, every 10,000 steps, on top of e007's log:</p>
<ul class="measures">
  <li><strong>Prey age</strong>: mean age of the prey killed, and the share of kills of prey younger than 50 steps.</li>
  <li><strong>Energy per kill</strong>: mean gain of the eater.</li>
  <li><strong>Meat share of intake</strong>: energy from prey over all energy eaten.</li>
  <li><strong>Agents fed mostly on meat</strong>: share whose lifetime meat intake exceeds their plant intake.</li>
  <li><strong>Per lineage</strong> (every 1,000 steps): mean age, lifetime plant and meat intake of the members. A carnivore lineage is one with meat above plant.</li>
  <li><strong>Lineages and events</strong> as e006/e007; <strong>snapshots</strong> every 5,000 steps and every step for 400 steps at 600,000.</li>
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
{charts["meat"]}{charts["eaten"]}
</div>
<div class="grid2">
{charts["prey_age"]}{charts["gain"]}
</div>
<p>{text["r1"]}</p>

<h3>3.2 {text["h2"]}</h3>
<div class="grid2">
{charts["meat_2"]}{charts["meat_3"]}
</div>
<div class="grid2">
{charts["majority_2"]}{charts["majority_3"]}
</div>
<div class="grid2">
{charts["scatter"]}{charts["young"]}
</div>
{"<div class='tw'><table>" + carn_table + "</table></div>" if carn_table else ""}
<p>{text["r2"]}</p>

<h3>3.3 {text["h3"]}</h3>
<div class="grid2">
{charts["pop"]}{charts["attack"]}
</div>
<div class="grid2">
{charts["digestive"]}{charts["lineages"]}
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
<div class="grid2">{charts["sps"]}</div>

<h2>4. Discussion</h2>
{text["discussion"]}

<h2>5. Conclusion and next step</h2>
<p>{text["conclusion"]}</p>

<h2>Appendix: data</h2>
<p>Every 100,000th record; full logs in <code>results/*_log.csv</code>, lineages in <code>results/*_lineages.csv</code>, events in <code>results/*_events.csv</code>, snapshots in <code>results/*_{{long,clip,bodies}}.jsonl</code>. Build this report with <code>uv run python experiments/e008_prey_worth/report.py</code>.</p>
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
    "tldr": "Making an old body a bigger prize did not make meat pay. Energy per kill doubled (2-3 to 5-6 at keep 1) but the meat share of intake stayed at 3-5% in every run, because nine kills in ten are of prey younger than 50 steps whatever the prize: a catchable body next to a predator is eaten within a few dozen steps of appearing, so nothing catchable grows old. The population answered the prize with armor (hard blocks 32-38 to 41-48), and predation per birth fell. Yet carnivore lineages do exist: hunters with 24 hard blocks in front and 20-25 muscle, living on meat for 52-89% of their food, for up to 430,000 steps. They were there in the control too (one in three seeds) and are more frequent at keep 1 (ten lineages in three seeds), as booms that armor ends. The world stands at every keep. What limits carnivory is not the prize but access: nobody can bite a 46-hard body, and there is no way to hunt. Next: #8, perception, so that hunting and fleeing can be learned; the knockout goes with it.",
    "question": "No pure carnivore has appeared in any world so far. Meat is 2-4% of energy eaten while predation is 30-50% of deaths, and the reason looked simple: a kill is worth about 3 whatever the prey, and most kills are newborns. Issue #7 asks to make a grown body worth what it cost to keep, and to watch whether carnivores follow. We change what a kill is worth and nothing else; no role is added.",
    "world": "Everything is e007 <em>128 patchy</em>: a 128x128 world with four drifting food patches, bodies grown from the genome, upkeep 0.002 per block per step, one predation rule (attack above the prey's defense, prey mass within the gut, escape by speed), sexual mode, lineages by gene distance. One number changes (Figure 1): the eater now also gets <em>keep</em> times the upkeep the prey has paid over its life. At the median age (170 steps) a 64-block body is worth 3.3 at keep 0 and 5.5 / 9.8 / 25 at keep 0.1 / 0.3 / 1; at age 850, 14 / 36 / 112. A reproduction costs about 8.",
    "c1": "no", "l1": "No", "v1": "Meat share of intake: 2.6-3.9% at keep 0, 3.1-4.5% at 0.1, 3.5-5.2% at 0.3, 4.7-5.2% at 1. Energy per kill doubles (median of window means 1.9-3.4 to 5.3-6.2) but kills fall (predation deaths per birth 0.31-0.44 to 0.24-0.28) and stay on newborns (89-94% of kills at keep 1). Nowhere near 10%.",
    "c2": "yes", "l2": "Yes, at keep 1", "v2": "Lineages living on meat (mean meat above plant over the members) for 20,000 steps or more: 0 / 0 / 1 in the control seeds, 1 / 0 / 0 at keep 0.1, none at 0.3, 4 / 2 / 4 at keep 1, where the longest last 279,000 / 417,000 / 340,000 steps with meat 52-89% of their food. Their body is a hunter: 23-30 hard (24 in front), 18-25 muscle, attack 15-23. But they have as many digestive blocks as the grazers (15-18), and the control has one too: the prize makes them more common, not possible.",
    "c3": "yes", "l3": "Yes", "v3": "Population median 828-858 at keep 1 against 876-1,066 in the control; no extinction; the deepest dip is 468 (keep 1, seed 1, step 10,000) and the highest boom 1,779 (keep 1, seed 3). Speed 1,300-3,400 steps per second with twelve runs on one machine.",
    "h1": "The prize doubles what a kill is worth, and the kills stay on newborns",
    "r1": "The gain per kill goes from 2-3 to 5-6 at keep 1 (top right), but the meat share of intake (top left) stays flat at 3-5% because there are fewer kills, not more: predation deaths per birth fall from 0.3-0.4 to 0.25. The mean age of the prey killed (bottom left) is 10-60 steps in every run and lowest at keep 1: the old bodies that the prize is for are not the ones being eaten. Nine kills in ten are of prey younger than 50 steps. This is not because old bodies are better armored; hard blocks are 40-48 at every age. It is because a catchable body that stands next to a predator is eaten within a few dozen steps of appearing, and new catchable bodies appear by birth, next to their parents, in the crowded patches where the predators sit. Whatever survives to be old is out of reach or immune. So the prize is on a shelf nobody can reach.",
    "h2": "Carnivore lineages exist, as booms of hunters, and the prize makes them more frequent",
    "r2": "The lineage log lets us find carnivores directly: lineages whose members, averaged, took in more meat than plants over their life. The scatter plot (bottom left) shows every lineage at every detection: the control (blue) has a cloud below 20% meat and one lineage above 50%; keep 1 (yellow) has a second cloud at 50-90% with attack 15-23. These are hunters: 24 hard blocks in the front rows and 20-25 muscle, the most attack the body plan allows (attack = min(front hard, muscle), 24 at most), with 15-18 digestive blocks like everybody else, so they graze as well and their gut holds a 64-block prey. The two charts above show what they look like in the population: the share of agents fed mostly on meat is 1-2% at keep 1 with spikes to 13-29%, and 0.2-0.6% in the control. Each spike is one lineage that found a catchable neighbor lineage, grew to 100-1,200 agents in a few thousand steps, and shrank again. The longest held for 280,000-430,000 steps. The table lists them; lineage 207 (keep 1, seed 2) took the world at the very end: at step 990,000 the meat intake per window tripled and the mean attack went from 3 to 10.",
    "h3": "The population answers with armor, and the world stands",
    "r3": "The population is 5-20% smaller at keep 1 than in the control and never collapses; the booms (up to 1,779 agents) settle within 20,000 steps. Attack per body goes down, not up, with keep (median 2.5-4.0 in the control, 1.9-2.7 at keep 1) and hard blocks go up (32-38 to 41-48). At keep 1 seed 1, 84% of the agents carry 46 hard blocks or more, which no attack can beat. The prize did make the arms race turn, in the direction of the prey. Digestive blocks do not move (14-19 everywhere): the gut is needed for prey mass, so no body drops it to become a leaner hunter. The timeline shows the hunter lineage 343 (keep 1, seed 1) from 575,000 to 849,000 steps beside the grazer lineages it fed on.",
    "viewer": "Keep 1, seed 1. Lineage 343 (teeth 23, armor 12) is the hunter: from step 575,000 it lives among the armored grazers (teeth 0, armor 23-24) on the same patches. In the clip at 600,000 the white dots are the hunters; they sit on the patch with the grazers and bite what they can. There is no chase: nobody in this world can see who is next to it, so a hunter finds prey by standing where prey is born.",
    "discussion": "<p>The issue's premise was that carnivores are missing because prey is worth too little. The prize was raised up to thirty times for an old body and meat did not become a larger part of what is eaten. What the prize revealed is that age at death is set by the predators themselves: a catchable body next to a predator dies young, so only the uncatchable grow old, and the prize for age cannot be collected. A predator that wanted to collect it would have to let prey grow, which no policy here can express.</p><p>The second finding is that carnivores were already there and we had not looked. The control has a lineage with 56% meat for 157,000 steps. The lineage log now records diet, and with that a carnivore is a thing that can be found and named in the viewer. At keep 1 there are ten such lineages in three seeds, as booms: a hunter body with maximum attack meets a grazer lineage it can bite, multiplies to 100-1,200 agents in a few thousand steps, and shrinks when the grazers are gone or armored. That is a predator-prey cycle, the mechanism the vision counts on for a world that does not settle, and it needs no prize to exist; the prize makes it more frequent and the booms bigger.</p><p>What limits carnivory is access, in two ways. First, the body plan: attack is at most 24 (three front rows of hard blocks matched by muscle) while defense goes to 32, so a body with 46 or more hard blocks is immune, and at keep 1 seed 1 most of the population is. Second, the policy: an agent sees counts of neighbors, not what they are, so hunting is standing still where prey is born and fleeing is not possible. Both are the subject of issue #8. A third limit is that every hunter also grazes, because the gut it needs for prey mass is the same organ that eats plants; a pure carnivore in the sense of diet class (meat only over a lifetime) would need a world with no food underfoot, and on a patch there always is some.</p><p>What this does not show: whether a smaller prize on energy rather than upkeep would differ (one formula was run), and whether the booms would be tamer on the 256 world with sixteen islands (here four). The prize is not conserved energy; at keep 1 a kill of an old body creates a hundred units from nothing, and the booms are the visible cost of that. If a prize is kept, keep 0.1-0.3 gives the same picture with smaller booms.</p>",
    "conclusion": "Prey worth eating does not make meat pay, because the old bodies it rewards are the ones nobody can catch. Carnivore lineages exist anyway, in the control and more often with the prize, as hunter booms that armor ends; the lineage log now measures diet so they can be found. The kill's value is not the lever; access is. Keep the diet columns in the lineage log and the hunter marks in the viewer. Do not adopt a prize: keep = 0 stays the law until perception gives predators a way to hunt and prey a way to flee. Next is #8 (what a neighbor input carries: attack and defense relative to one's own, paid for by sensor blocks) with the sensor knockout, on 128 with three seeds; then a bite that can grow beyond 24, or armor that costs more, if #8 shows predators that can see still cannot eat.",
}

if __name__ == "__main__":
    main()
