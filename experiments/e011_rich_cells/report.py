#!/usr/bin/env python3
"""Build report.html for e011.

Charts: matplotlib, exported as SVG and inlined. Diagram: hand-written SVG.
Run from the repo root: uv run python experiments/e011_rich_cells/report.py
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
# Worlds: label -> (run prefix, folder). Slot order is also the chart color order. Width 8 is e010's world (its runs).
E010 = os.path.join(HERE, "..", "e010_contact")
WORLDS = {
    "width 8 (e010)": ("128_patchy", E010, INK, 0.10),
    "width 4": ("128_patchy_cap8_sigma4", HERE, SERIES[0], 0.41),
    "width 2": ("128_patchy_cap8_sigma2", HERE, SERIES[1], 1.63),
    "width 1": ("128_patchy_cap8_sigma1", HERE, SERIES[2], 6.52),
}
if os.environ.get("E011_SMOKE"):  # build against e010's runs only, to test the script before the runs finish
    WORLDS = {w: ("128_patchy", E010, c, x) for w, (_, _, c, x) in WORLDS.items()}
NEW = [w for w in WORLDS if "e010" not in w]
KIND_COLOR = {1: SERIES[0], 2: SERIES[1], 3: SERIES[3], 4: SERIES[2]}
CONFIRM_STEPS = 5000
VIEWER_WORLD = "width 1"
VIEWER_SEED = 1
VIEWER_RUN = f"{WORLDS[VIEWER_WORLD][0]}_seed{VIEWER_SEED}"
VIEWER_DIR = WORLDS[VIEWER_WORLD][1]
VIEWER_W = 128


# ---------- data ----------

def load_csv(path, folder=HERE):
    with open(os.path.join(folder, path)) as f:
        rows = list(csv.DictReader(f))
    return {k: [float(r[k]) for r in rows] for k in rows[0]}


def load_rows(path, folder=HERE):
    with open(os.path.join(folder, path)) as f:
        return list(csv.DictReader(f))


def lineage_stats(run, folder=HERE):
    """Per lineage: first and last step seen as a group, max size."""
    lin = load_rows(f"results/{run}_lineages.csv", folder)
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
    first, _, _ = lineage_stats(run, VIEWER_DIR)
    return {lid: k % len(LINEAGE_PALETTE) for k, lid in enumerate(sorted(first, key=first.get))}


def timeline_chart(title, subtitle, run, events):
    """Every lineage as a band: size over time, colored by confirmation order. Events as marks."""
    slot = color_slots(run)
    lin = load_rows(f"results/{run}_lineages.csv", VIEWER_DIR)
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
<svg viewBox="0 0 720 300" role="img" aria-label="The same regrowth on fewer cells. Four food patches of width 8, 4, 2 and 1 with the same total regrowth; the narrower the patch, the more each cell regrows per step: 0.10, 0.41, 1.63, 6.5. A digestive cell takes 0.02 per step from the cell its body stands on. The gut that keeps up with one cell is regrowth over 0.02: 5, 20, 80, 330 cells." style="max-width:100%;height:auto;display:block">
<g fill="none" stroke="currentColor" stroke-width="1.2" font-size="12" font-family="system-ui, sans-serif">
  <text x="20" y="20" fill="currentColor" stroke="none" font-weight="600">one food patch, the same total regrowth (41 per patch per step), on fewer cells</text>
  <line x1="20" y1="190" x2="700" y2="190"/>
  <text x="20" y="208" fill="currentColor" stroke="none">world cells along one line through the center of the patch</text>
  <path d="M 30,190 C 60,188 80,182 100,175 S 130,160 150,160 S 200,175 220,182 S 250,188 270,190" stroke="#898781" stroke-width="1.6"/>
  <text x="150" y="150" text-anchor="middle" fill="#898781" stroke="none">width 8 (e010): 0.10 per cell per step</text>
  <path d="M 330,190 C 345,186 355,170 365,150 S 380,120 390,120 S 405,140 415,160 S 435,186 450,190" stroke="#2a78d6" stroke-width="1.6"/>
  <text x="390" y="110" text-anchor="middle" fill="#2a78d6" stroke="none">width 4: 0.41</text>
  <path d="M 490,190 C 500,188 506,150 512,110 S 520,70 525,70 S 535,110 540,150 S 550,188 560,190" stroke="#eb6834" stroke-width="1.6"/>
  <text x="525" y="60" text-anchor="middle" fill="#eb6834" stroke="none">width 2: 1.63</text>
  <path d="M 610,190 C 616,188 619,140 622,90 S 626,36 628,36 S 633,90 637,140 S 640,188 646,190" stroke="#1baf7a" stroke-width="1.6"/>
  <text x="655" y="46" text-anchor="start" fill="#1baf7a" stroke="none">width 1: 6.5</text>
  <text x="20" y="240" fill="currentColor" stroke="none" font-weight="600">what a body takes from the cell it stands on</text>
  <text x="20" y="258" fill="currentColor" stroke="none">0.02 per digestive cell per step, if the cell has it; bodies on the same cell eat in turn until it is empty.</text>
  <text x="20" y="276" fill="var(--s1)" stroke="none" font-weight="600">the gut that keeps up with one cell alone: regrowth / 0.02 = 5, 20, 80, 330 digestive cells (the grid holds 64).</text>
  <text x="20" y="294" fill="currentColor" stroke="none">a cell holds at most 8 (e010: 1). bodies, costs, contact physics, mating, lineages: e010's, unchanged.</text>
</g>
</svg>
<figcaption>Figure 1. The only change from e010. A food patch is a Gaussian bump of regrowth; its width is an argument and its total is fixed, so a narrower patch puts the same food on fewer cells. Whether a body with a larger gut, a tooth or a shell pays is left to selection; no rule about bodies changed.</figcaption>
</figure>
"""


def read_frames(path):
    with open(os.path.join(VIEWER_DIR, path)) as f:
        for line in f:
            yield json.loads(line)


def load_bodies(run):
    out = {}
    with open(os.path.join(VIEWER_DIR, f"results/{run}_bodies.jsonl")) as f:
        for line in f:
            d = json.loads(line)
            out[d["id"]] = d["cells"]
    return out


def pack_frames(path, confirmed_at, data, every=1, limit=None):
    """Frames packed small into `data`: food as 4-bit nibbles; agents as x, y, body id (3 bytes), lineage (2 bytes).
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
            ag += bytes((x, y, b & 255, (b >> 8) & 255, b >> 16, lin & 255, lin >> 8))  # 3-byte body id: a run can have 100,000+ distinct (damaged) bodies
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


def hunter_lineages(run, folder=HERE, min_steps=20_000, min_bite=2.0):
    lin = load_rows(f"results/{run}_lineages.csv", folder)
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


def world_chart(title, subtitle, logs, key_fn, ymin=0, percent=False, ymax=None, worlds=None):
    """One thin line per seed, colored by world; one legend entry per world."""
    fig, ax = new_axes()
    top = 0
    for w in worlds or WORLDS:
        color = WORLDS[w][2]
        for k, s in enumerate(SEEDS):
            log = logs[w][s]
            ys = key_fn(log)
            if ys is None:
                continue
            top = max(top, max(ys))
            ax.plot(log["step"], ys, color=color, linewidth=1.1, alpha=0.85, label=w if k == 0 else None)
    if ymin is not None:
        ax.set_ylim(ymin, max(ymax if ymax is not None else top * 1.12, ymin + 1e-9))
    ax.yaxis.set_major_formatter((lambda y, _p: f"{y:.0%}") if percent else kfmt)
    ax.yaxis.set_major_locator(MaxNLocator(4))
    legend_above(ax, 4)
    return figure(title, subtitle, to_svg(fig))


def dose_chart(title, subtitle, points, ylabel, ymax=None, ref=None):
    """points: {world: [(x, y) per seed]} on a log x axis of peak regrowth per cell. ref: (label, fn) drawn as a dashed line."""
    fig, ax = new_axes(xlabel="regrowth per cell per step at the center of a patch", size=(6.4, 2.8))
    ax.set_xscale("log")
    ax.margins(x=0.1)
    ax.set_ylabel(ylabel)
    if ref:
        xs = [WORLDS[w][3] for w in WORLDS]
        ax.plot(xs, [ref[1](x) for x in xs], color=INK, linestyle="--", linewidth=1, label=ref[0])
    for w, pts in points.items():
        ax.scatter([p[0] for p in pts], [p[1] for p in pts], color=WORLDS[w][2], s=22, label=w, zorder=3)
    ax.set_xticks([WORLDS[w][3] for w in WORLDS])
    ax.set_xticklabels([f"{WORLDS[w][3]:.2f}\n{w.split(' (')[0]}" for w in WORLDS])
    ax.set_ylim(0, ymax)
    ax.yaxis.set_major_locator(MaxNLocator(4))
    ax.yaxis.set_major_formatter(kfmt)
    legend_above(ax, 5)
    return figure(title, subtitle, to_svg(fig))


def hist_chart(title, subtitle, masses):
    """masses: {world: [mass, ...]} pooled over seeds; share of bodies per size."""
    fig, ax = new_axes(xlabel="cells in the body", size=(6.4, 2.8))
    ax.margins(x=0.02)
    for w, ms in masses.items():
        c = Counter(ms)
        n = max(len(ms), 1)
        xs = list(range(1, 65))
        ax.plot(xs, [c.get(x, 0) / n for x in xs], color=WORLDS[w][2], linewidth=1.4, label=w)
    ax.yaxis.set_major_formatter(lambda y, _p: f"{y:.0%}")
    ax.yaxis.set_major_locator(MaxNLocator(4))
    ax.set_ylim(0, None)
    legend_above(ax, 4)
    return figure(title, subtitle, to_svg(fig))


# Lineages that prospered, one per shape: (world, seed, lineage id, what to call it).
GALLERY = [
    ("width 4", 3, 352, "corner column"),
    ("width 4", 2, 609, "center block"),
    ("width 2", 1, 225, "hook along two edges"),
    ("width 2", 3, 384, "corner triangle"),
    ("width 1", 3, 2, "four corners"),
    ("width 1", 4, 813, "tortoise"),
    ("width 1", 4, 1198, "tortoise with teeth"),
    ("width 1", 3, 200, "carnivore"),
]


def gallery(logs_unused=None):
    """The most common body of each GALLERY lineage at its peak, as an 8x8 grid, with one line of numbers."""
    cards = []
    for w, seed, lid, name in GALLERY:
        run, folder = f"{WORLDS[w][0]}_seed{seed}", WORLDS[w][1]
        rows = [r for r in load_rows(f"results/{run}_lineages.csv", folder) if int(r["lineage"]) == lid]
        peak = max(rows, key=lambda r: int(r["size"]))
        span = int(rows[-1]["step"]) - int(rows[0]["step"]) + CONFIRM_STEPS
        bodies = {}
        with open(os.path.join(folder, f"results/{run}_bodies.jsonl")) as f:
            for line in f:
                d = json.loads(line)
                bodies[d["id"]] = d["cells"]
        frame, best = None, None
        with open(os.path.join(folder, f"results/{run}_long.jsonl")) as f:
            for line in f:
                fr = json.loads(line)
                if best is None or abs(fr["step"] - int(peak["step"])) < abs(best - int(peak["step"])):
                    frame, best = fr, fr["step"]
        c = Counter(a[2] for a in frame["agents"] if a[4] == lid)
        cells = bodies[c.most_common(1)[0][0]]
        rects = "".join(f'<rect x="{(i % 8) * 11}" y="{(i // 8) * 11}" width="10" height="10" fill="{KIND_COLOR[int(k)]}"/>' for i, k in enumerate(cells) if k != "0")
        m, pl = float(peak["meat"]), float(peak["plant"])
        meat = m / (m + pl) if m + pl > 0 else 0
        cards.append(f"""<figure class="card"><svg viewBox="-1 -1 89 89" width="120" height="120" role="img" aria-label="{html.escape(name)}"><rect x="-1" y="-1" width="89" height="89" fill="var(--cell)"/>{rects}</svg>
<figcaption><strong>{html.escape(name)}</strong><br>{w}, seed {seed}, lineage {lid}<br>{span:,} steps, {int(peak["size"]):,} agents at its peak<br>mass {float(peak["mass"]):.0f}: hard {float(peak["hard"]):.0f}, muscle {float(peak["muscle"]):.0f}, digestive {float(peak["digestive"]):.0f}<br>meat {meat:.0%} of its food</figcaption></figure>""")
    return f"""<figure class="diagram"><div class="cards">{"".join(cards)}</div>
<figcaption>Figure 2. Bodies of lineages that prospered: the most common body of the lineage at its peak, on the 8x8 grid a body grows on. Blue: hard, orange: muscle, green: digestive, yellow: sensor. Numbers are the lineage's means at its peak. Every shape is a way of standing on a crowded cell: a gut in one corner (a hunter's muscle sits in the middle rows, so the outer lines are never pushed with force), a gut at the center (the cheapest place for the gene network to switch cells on), a wall of hard around a gut, or a wall with muscle behind it.</figcaption></figure>"""


def main():
    logs, events, agents = {}, {}, {}
    for w, (run, folder, _, _) in WORLDS.items():
        logs[w] = {s: load_csv(f"results/{run}_seed{s}_log.csv", folder) for s in SEEDS}
        events[w] = {s: load_rows(f"results/{run}_seed{s}_events.csv", folder) for s in SEEDS}
        agents[w] = {s: load_rows(f"results/{run}_seed{s}_agents.csv", folder) for s in SEEDS}

    def med(x):
        x = [v for v in x if v == v]
        return statistics.median(x) if x else float("nan")

    def pct(vals, f):
        vals = sorted(vals)
        return vals[int((len(vals) - 1) * f)] if vals else 0

    def summarize(w, s):
        log = logs[w][s]
        run, folder = f"{WORLDS[w][0]}_seed{s}", WORLDS[w][1]
        first, last, size = lineage_stats(run, folder)
        life = [last[i] - first[i] + CONFIRM_STEPS for i in first]
        n_lin = load_rows(f"results/{run}_lineages.csv", folder)
        per_step = Counter(int(r["step"]) for r in n_lin)
        last_step = int(log["step"][-1])
        counts = Counter(r["event"] for r in events[w][s])
        hunters = hunter_lineages(run, folder)
        half = [i for i, t in enumerate(log["step"]) if t > last_step / 2]
        final = [int(r["mass"]) for r in agents[w][s] if int(r["step"]) == last_step]
        opt = lambda k: med(log[k]) if k in log else float("nan")
        return dict(
            pop=med(log["pop"]), pop_min=min(log["pop"]), pop_max=max(log["pop"]), extinct=last_step < 1_000_000,
            mass=med(log["mass_mean"]), mass_std=med(log["mass_std"]), mass_std_min=min(log["mass_std"]), full=med(log["full_share"]), full_max=max(log["full_share"]),
            p10=pct(final, 0.1), p50=pct(final, 0.5), p90=pct(final, 0.9), p99=pct(final, 0.99),
            open=med(log["open_mean"]), damaged=med(log["damaged_share"]), hard=med(log["hard_mean"]), muscle=med(log["muscle_mean"]), sensor=med(log["sensor_mean"]), digestive=med(log["digestive_mean"]),
            bite=med(log["bite_mean"]), bite_max=max(log["bite_mean"]), biters=med(log["biters_share"]), biters_max=max(log["biters_share"]), shell=med(log["shell_mean"]), shell_max=max(log["shell_mean"]),
            broken=sum(log["cells_broken"]) / last_step, contacts=sum(log["contacts"]) / last_step,
            deaths_broken=sum(log["deaths_broken"]) / max(sum(log["births"]), 1), deaths_broken_half=sum(log["deaths_broken"][i] for i in half) / max(sum(log["births"][i] for i in half), 1),
            meat=sum(log["meat_intake"]) / max(sum(log["plant_intake"]) + sum(log["meat_intake"]), 1), meat_half=sum(log["meat_intake"][i] for i in half) / max(sum(log["plant_intake"][i] + log["meat_intake"][i] for i in half), 1),
            majority=med(log["meat_majority"]), majority_max=max(log["meat_majority"]), per_cell=med(log["meat_per_cell"]),
            hunters=len(hunters), hunter_span=hunters[0]["span"] if hunters else 0, hunter_diet=max((h["diet"] for h in hunters), default=0.0),
            lineages=med([per_step.get(t, 0) for t in range(1000, last_step + 1, 1000)]), ids=len(first), life=med(life) if life else 0, rate=sum(counts.values()) / (last_step // 1000),
            births=sum(log["births"]) / last_step, sps=med(log["steps_per_sec"]), sps_min=min(log["steps_per_sec"]),
            crowd=opt("crowd_max"), occupied=opt("occupied_cells"), wasted=opt("wasted"), intake_gut=opt("intake_per_gut"), res=med(log["mean_res"]),
        )

    S = {w: {s: summarize(w, s) for s in SEEDS} for w in WORLDS}
    hunters_all = {(w, s): hunter_lineages(WORLDS[w][0] + f"_seed{s}", WORLDS[w][1]) for w in WORLDS for s in SEEDS}

    charts = {}
    charts["pop"] = world_chart("Population", "Living agents. The per-body cost bounds it near 5,000 whatever the world; fewer cells with food means fewer, larger bodies.", logs, lambda l: l["pop"])
    charts["sps"] = world_chart("Steps per second", "Simulation speed, twelve runs sharing one machine, one thread each (e010: same).", logs, lambda l: l["steps_per_sec"])
    charts["mass"] = world_chart("Mass per body", "Population mean of cells per body (64 is a full square). Flat at 5 would be e010's world.", logs, lambda l: l["mass_mean"], ymax=66)
    charts["mass_std"] = world_chart("Spread of mass", "Standard deviation of cells per body. Zero would mean one body size.", logs, lambda l: l["mass_std"])
    charts["digestive"] = world_chart("Digestive cells per body", "Population mean. Each takes 0.02 per step from the cell the body stands on, if the cell has it.", logs, lambda l: l["digestive_mean"])
    charts["hard"] = world_chart("Hard cells per body", "Population mean. Hard is hardness at a tip and nothing else.", logs, lambda l: l["hard_mean"])
    charts["muscle"] = world_chart("Muscle per body", "Population mean. Muscle is force along its line and speed (muscle / mass).", logs, lambda l: l["muscle_mean"])
    charts["crowd"] = world_chart("Most bodies in one cell", "The most crowded cell of the world at each log step.", logs, lambda l: l.get("crowd_max"), worlds=NEW)
    charts["bite"] = world_chart("Bite per body", "Population mean of the largest force behind a hard tip. 2 breaks a soft tip; 0 means no body can bite.", logs, lambda l: l["bite_mean"])
    charts["biters"] = world_chart("Bodies with a bite", "Share of bodies with a hard tip and at least one muscle cell behind it.", logs, lambda l: l["biters_share"], percent=True)
    charts["shell"] = world_chart("Shell per body", "Mean hardness of the tips that can be touched. 1 is soft everywhere; 3 is a hard tip.", logs, lambda l: l["shell_mean"])
    charts["broken"] = world_chart("Cells broken per step", "Cells removed from bodies by pushes, per step.", logs, lambda l: [c / 10_000 for c in l["cells_broken"]])
    charts["deaths"] = world_chart("Deaths by damage per birth", "Bodies that lost their last cell, divided by births, per window.", logs, lambda l: [d / max(b, 1) for d, b in zip(l["deaths_broken"], l["births"])])
    charts["meat"] = world_chart("Meat share of intake", "Energy from broken cells of other bodies divided by all energy eaten.", logs, lambda l: [m / max(m + p, 1e-9) for m, p in zip(l["meat_intake"], l["plant_intake"])], percent=True)
    charts["contacts"] = world_chart("Pushes per step", "Moves into a cell that holds another body, per step.", logs, lambda l: [c / 10_000 for c in l["contacts"]])
    charts["lineages"] = world_chart("Lineages alive", "Confirmed lineages at each log step.", logs, lambda l: l["lineages"])
    charts["dose_gut"] = dose_chart("Gut follows the world", "Digestive cells per body (median over the run, one point per seed) against how fast a cell regrows. The dashed line is the gut that would take everything one cell gives: regrowth / 0.02.",
                                    {w: [(WORLDS[w][3], S[w][s]["digestive"]) for s in SEEDS] for w in WORLDS}, "digestive cells per body", ymax=64, ref=("regrowth / 0.02", lambda x: min(x / 0.02, 64)))
    charts["dose_mass"] = dose_chart("Sizes spread out", "Mass at the 10th, 50th and 90th percentile of the population at step 1,000,000 (dots low to high per seed). Points that sit on one another would be one size with noise.",
                                     {w: [(WORLDS[w][3] * f, S[w][s][k]) for s in SEEDS for f, k in ((0.85, "p10"), (1.0, "p50"), (1.18, "p90"))] for w in WORLDS}, "cells in the body", ymax=66)
    charts["hist"] = hist_chart("Sizes at the end of the runs", "Share of bodies by cells in the body at step 1,000,000, four seeds pooled. One peak is one size; a wide floor is many sizes.",
                                {w: [int(r["mass"]) for s in SEEDS for r in agents[w][s] if int(r["step"]) == 1_000_000] for w in WORLDS})

    timeline = timeline_chart(f"Lineages over time ({VIEWER_WORLD}, seed {VIEWER_SEED})", "Each colored band is one lineage, height = agents in it; marks are events at the size they were logged with.", VIEWER_RUN, events[VIEWER_WORLD][VIEWER_SEED])

    first, _, _ = lineage_stats(VIEWER_RUN, VIEWER_DIR)
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

    def rng(w, key, fmt):
        vals = [S[w][s][key] for s in SEEDS]
        vals = [v for v in vals if v == v]
        if not vals:
            return "-"
        lo, hi = min(vals), max(vals)
        return fmt(lo) if fmt(lo) == fmt(hi) else f"{fmt(lo)}-{fmt(hi)}"

    def row(label, key, fmt):
        return f"<tr><td>{label}</td>" + "".join(f"<td>{rng(w, key, fmt)}</td>" for w in WORLDS) + "</tr>"

    n0 = lambda v: f"{v:,.0f}"
    d1 = lambda v: f"{v:.1f}"
    d2 = lambda v: f"{v:.2f}"
    d3 = lambda v: f"{v:.3f}"
    p1 = lambda v: f"{v:.1%}"
    summary = ("<thead><tr><th>Measure (range over four seeds)</th>" + "".join(f"<th>{w}<br><span style='font-weight:400'>{WORLDS[w][3]:.2f} per cell per step</span></th>" for w in WORLDS) + "</tr></thead><tbody>"
               + row("Population, median", "pop", n0)
               + row("Mass per body, median of means", "mass", d1)
               + row("Spread of mass, median of std", "mass_std", d1)
               + row("Spread of mass, minimum of std", "mass_std_min", d1)
               + row("Mass at the 10th percentile, step 1,000,000", "p10", n0)
               + row("Mass at the 50th percentile", "p50", n0)
               + row("Mass at the 90th percentile", "p90", n0)
               + row("Full squares, median share", "full", p1)
               + row("Digestive cells per body, median", "digestive", d1)
               + row("Hard cells per body, median", "hard", d2)
               + row("Muscle cells per body, median", "muscle", d2)
               + row("Sensor cells per body, median", "sensor", d2)
               + row("Most bodies in one cell, median", "crowd", n0)
               + row("Cells with a body, median", "occupied", n0)
               + row("Plant intake per digestive cell per step, median", "intake_gut", lambda v: f"{v:.4f}")
               + row("Bite per body, median", "bite", d2)
               + row("Bite per body, maximum", "bite_max", d2)
               + row("Bodies with a bite, maximum share", "biters_max", p1)
               + row("Shell per body, median", "shell", d2)
               + row("Hunter lineages (bite &ge; 2 for 20,000+ steps)", "hunters", n0)
               + row("Longest hunter lineage (steps)", "hunter_span", n0)
               + row("Pushes per step", "contacts", d1)
               + row("Cells broken per step", "broken", d2)
               + row("Deaths by damage per birth", "deaths_broken", lambda v: f"{v:.4f}")
               + row("Meat share of intake", "meat", lambda v: f"{v:.2%}")
               + row("Agents fed mostly on other bodies, maximum share", "majority_max", p1)
               + row("Births per step", "births", d1)
               + row("Lineages alive, median", "lineages", n0)
               + row("Lineage lifetime, median (steps)", "life", n0)
               + row("Steps per second, median", "sps", n0)
               + "</tbody>")

    h_rows = []
    for (w, s), lst in hunters_all.items():
        for c in lst[:3]:
            h_rows.append(f"<tr><td>{w}, seed {s}</td><td>{c['id']}</td><td>{c['first']:,}-{c['last']:,}</td><td>{c['span']:,}</td><td>{c['size']}</td><td>{c['mass']:.0f}</td><td>{c['bite']:.1f}</td><td>{c['shell']:.1f}</td><td>{c['hard']:.0f} / {c['muscle']:.0f} / {c['digestive']:.0f}</td><td>{c['diet']:.0%}</td></tr>")
    h_table = ("<thead><tr><th>Run</th><th>Lineage</th><th>Bite &ge; 2 from-to</th><th>Steps</th><th>Peak size</th><th>Mass</th><th>Bite</th><th>Shell</th><th>Hard / muscle / digestive</th><th>Meat share</th></tr></thead><tbody>"
               + "".join(h_rows) + "</tbody>") if h_rows else ""

    tables = data_table(["step", "pop", "births", "deaths_energy", "deaths_broken", "cells_broken", "contacts", "plant_intake", "meat_intake", "mass_mean", "mass_std", "mass_p10", "mass_p50", "mass_p90", "digestive_mean", "hard_mean", "muscle_mean", "bite_mean", "biters_share", "shell_mean", "crowd_max", "lineages", "steps_per_sec"],
                        {f"{w}, seed {s} (every 100,000 steps)": logs[w][s] for w in NEW for s in SEEDS}, every=10)

    text = TEXT
    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>e011 Rich cells - Report</title>
<style>{CSS}</style>
</head>
<body>
<main>
<h1>e011: Food that a small body cannot take</h1>
<p class="sub">Experiment report - 2026-08-30 - e010's world and physics, the same regrowth on fewer cells (patch width 4, 2, 1 against e010's 8), four seeds each, 1,000,000 steps</p>

<section class="tldr">
<h2>TL;DR</h2>
<p>{text["tldr"]}</p>
</section>

<h2>1. Question</h2>
<p>{text["question"]}</p>
<ol>
  <li><strong>Gut follows the world.</strong> The median gut moves with the patch width in the order 8, 4, 2, 1 (the gut that keeps up with one cell is regrowth / 0.02: 5, 20, 80, 330), and the median mass in the concentrated worlds is at least three times e010's (over 16).</li>
  <li><strong>Sizes coexist.</strong> The spread of mass stays above 5 for the whole run, and the 10th and 90th percentiles of mass differ by at least a factor of 2, in every seed of the concentrated worlds.</li>
  <li><strong>The world stands at a bounded cost.</strong> No extinction; population above 500; at least 300 steps per second with twelve runs sharing the machine.</li>
  <li><strong>Teeth have something to reach.</strong> Hunter lineages (mean bite at least 2 for 20,000+ steps, 20% of their food from other bodies) in at least a third of the concentrated seeds, with deaths by damage per birth above 0.01 there.</li>
</ol>

<h2>2. The world</h2>
<p>{text["world"]}</p>
{DIAGRAM}
<p>{text["trials"]}</p>
<p><strong>Runs.</strong> Patch width 4, 2 and 1 with a cap of 8, seeds 1-4 each, 1,000,000 steps on the 128x128 patchy world; twelve runs sharing one machine, one thread each. Reference: e010's twelve runs (width 8, cap 1), of which seeds 1-4 are shown. We record, every 10,000 steps, e010's measures and:</p>
<ul class="measures">
  <li><strong>Mass</strong> at the 10th, 50th, 90th percentile and the maximum, besides the mean and spread; <strong>digestive cells</strong> per body (the gut).</li>
  <li><strong>Crowding</strong>: cells with at least one body, and the most bodies in one cell.</li>
  <li><strong>Regrowth lost to the cap</strong> (a full cell does not grow), and <strong>plant intake per digestive cell</strong> per step.</li>
  <li><strong>Bite</strong>: the largest force behind a hard tip (2 breaks a soft tip); <strong>shell</strong>: mean hardness of the touchable tips. Measures only; no rule reads them.</li>
  <li><strong>Pushes</strong>, <strong>cells broken</strong>, <strong>deaths by damage</strong>, meat share of intake; <strong>lineages and events</strong> as e006, with mass, bite, shell and diet per lineage; <strong>snapshots</strong> every 5,000 steps and every step for 400 steps at 600,000.</li>
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
{charts["dose_gut"]}{charts["digestive"]}
</div>
<div class="grid2">
{charts["mass"]}{charts["crowd"]}
</div>
<p>{text["r1"]}</p>

<h3>3.2 {text["h2"]}</h3>
<div class="grid2">
{charts["hist"]}{charts["dose_mass"]}
</div>
<div class="grid2">
{charts["mass_std"]}{charts["lineages"]}
</div>
{gallery()}
<p>{text["r2"]}</p>

<h3>3.3 {text["h3"]}</h3>
<div class="grid2">
{charts["pop"]}{charts["sps"]}
</div>
<p>{text["r3"]}</p>

<h3>3.4 {text["h4"]}</h3>
<div class="grid2">
{charts["hard"]}{charts["muscle"]}
</div>
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
<p>{text["r4"]}</p>

<h3>3.5 Watching the world</h3>
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
  <div class="bar">Left: the whole 128x128 world, each agent colored by its lineage (gray: none), a white dot on bodies with a bite. Green: food (scaled to the cap of 8); the bright spots are the patches. Click to move the white box. Right: the box at 24x24 cells, bodies drawn on the lineage color, damage included. Labels: agents per lineage, then mean mass, bite, shell, and sensor cells (eyes). {VIEWER_WORLD}, seed {VIEWER_SEED}.</div>
</div>
<p>{text["viewer"]}</p>
<div class="grid2">{charts["contacts"]}</div>

<h2>4. Discussion</h2>
{text["discussion"]}

<h2>5. Conclusion and next step</h2>
<p>{text["conclusion"]}</p>

<h2>Appendix: data</h2>
<p>Every 100,000th record; full logs in <code>results/*_log.csv</code>, lineages in <code>results/*_lineages.csv</code>, events in <code>results/*_events.csv</code>, agents every 100,000 steps in <code>results/*_agents.csv</code>, snapshots in <code>results/*_{{long,clip,bodies}}.jsonl</code>. e010's runs are read from <code>../e010_contact/results</code>. Build this report with <code>uv run python experiments/e011_rich_cells/report.py</code>.</p>
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
    "tldr": "One change to the world, none to the bodies: the same regrowth on fewer cells. In e010 a cell regrew 0.10 per step and every seed went to a five-cell gut in a corner. With the patch width halved (0.41 per cell) bodies go to 7-10 cells; halved again (1.63) to 15-16; at width 1 (6.5 per cell) to 18-43. The gut itself only grows from 5 to 10-16 cells, because the bodies crowd onto the rich cells (12, 28 and 45-77 to a cell) and share them. What grows is everything else. At width 1, and in two of four seeds at width 2, the crowd turns into an arms race that e010 never reached: hard cells go from 0.1 to 6-26 per body, 12-24% of bodies have a bite, meat is 9-19% of all energy eaten, and 26-50 hunter lineages per seed last up to 483,000 steps (e010: one, for 12,000). Three kinds of body coexist on one island: full-square tortoises with a two-cell wall of armor around a gut, hunters with a hard tip and muscle behind it, and corner bodies, two to twelve digestive cells placed only in the corners of the grid, where no tooth reaches. Sizes coexist (mass 3-8 at the 10th percentile, 48-64 at the 90th). We asked the real world why elephants exist and took one premise from it, a cell that holds more than one bite; the world answered with tortoises. Next: a world with both kinds of place, and bodies that are not capped at 64 cells.",
    "question": "e010 removed every trait rule, and the world went to the smallest grazer in all twelve seeds: three or four digestive cells, because a cell of the world regrows 0.10 per step at the center of a patch and a digestive cell takes 0.02, so five cells take everything a cell gives and the sixth returns nothing. Size had no reason to exist. principles.md says to ask the real world why: elephants and whales live on food that is concentrated and regrows faster than a small mouth can take it. The simplest premise in that is <em>a cell can hold more than one bite</em>. Is one law of the world enough to make sizes, and once there are large soft bodies, do teeth have something to reach?",
    "world": "Everything is e010's (128x128, four food patches drifting one cell every 50 steps, bodies of 8x8 cells in five kinds grown from the genome, contact physics, a cell that costs what it holds, 0.032 per body per step) except two constants of the food law, which became arguments: the width of a patch (e010: 8) and what a cell can hold (e010: 1). The total regrowth is fixed at 0.01 per world cell per step, so a narrower patch puts the same food on fewer cells (Figure 1). With the defaults the program reproduces e010 byte for byte.",
    "trials": "<strong>Trials before the runs</strong> (seed 9, 100,000 steps, one run per world, not kept). Width 8, 4, 2, 1 gave a median gut of 5.3, 8.5, 14.6, 28.1 cells and a mass of 5.7, 9.1, 15.9, 31.9; the cap made no difference (cap 1 and 4 at width 4: mass 9.1 and 8.0; cap 4 and 16 at width 2: 15.9 and 16.5), because a crowded cell is emptied every step and a store never builds up. The width is the lever; the runs vary it and fix the cap at 8, above the peak regrowth of width 1, so that no regrowth is lost to it.",
    "c1": "partly", "l1": "Partly", "v1": "The median gut moves with the width in the right order: 5.0-5.5 (e010), 6.3-8.7, 9.6-14.1, 10.5-15.6 cells; but it stays far from the gut that would take one cell alone (20, 80, 330), because 12, 28 and 45-77 bodies stand on one cell and share it: intake per digestive cell stays at 0.005-0.009 per step in every world. Mass passes 16 only at width 1 (median of means 18-43); width 2 gives 14-16 and width 4 gives 7-10.",
    "c2": "yes", "l2": "Yes, at width 2 and 1", "v2": "The spread of mass never falls below 5.7-8.8 at width 2 and 13.9-18.5 at width 1, and the 90th percentile of mass is at least 2.0 times the 10th at every log step of all twelve runs (width 4 included; its spread dips to 3.7-5.4). At the end of the width-1 runs, 3-27% of bodies have at most 4 cells and 3-28% have 60 or more.",
    "c3": "yes", "l3": "Yes", "v3": "No extinction; population 1,138-3,272 (median), never below 950. Speed 376-846 steps per second (median per run) with twelve runs on one machine; the slowest single window was 203 (a width-4 run, during the report build). Fewer, larger bodies run faster: width 1 is the fastest world at 574-846.",
    "c4": "partly", "l4": "Partly", "v4": "Hunter lineages (bite at least 2 for 20,000+ steps) in all four width-1 seeds (26-50 per seed, the longest 156,000-483,000 steps, 26-85% of their food from other bodies) and in two of four width-2 seeds (44 and 4); none at width 4. That is 6 of 8 concentrated seeds, more than the third asked for. Deaths by damage per birth pass 0.01 in only two of those six (0.016 and 0.018); the others are 0.002-0.008, because most of what a tooth breaks is a cell of a tortoise, not a body's last cell.",
    "h1": "Bodies grow with the concentration of food, the gut less than the rest",
    "r1": "The gut follows the world in order but not in proportion: 5, 7, 13, 14 digestive cells as a cell's regrowth goes 0.10, 0.41, 1.63, 6.5. The dashed line in the first chart is what one body alone could take from one cell; the population never lets a body be alone. The crowd on the richest cells rises as the patch narrows (12, 28, 45-77 bodies in the most crowded cell), the cell is emptied every step, and each digestive cell gets 0.005-0.009 per step whatever the world. Mass rises more than the gut does (8, 15, 18-43) because at width 1 a body is mostly armor: hard cells go from 0.1 per body to 6-26. The size came, but not the way the metaphor said: not a bigger stomach, a shell.",
    "h2": "Sizes coexist: corner bodies, tortoises and hunters on one island",
    "r2": "e010's world has one peak at 5 cells and nothing above 15. Width 4 moves the peak to 6-8. Width 2 and 1 spread it out and, at width 1, make it two-humped: 3-27% of bodies have at most 4 cells and 3-28% are full squares of 60-64 cells; the 10th percentile of mass is 3-8 and the 90th 48-64. The most common bodies at the end of width 1, seed 4: a full square with a two-cell wall of hard around a 4x4 gut (28 hard, 16 digestive: a tortoise, 186 agents), and two to four digestive cells sitting only in the corners of the grid (65 agents); the largest lineage of width 1 (seed 3, lineage 2: alive for the whole run, 2,179 agents at its peak) is three digestive cells in each of the four corners (Figure 2). The corner is not an accident: a hunter's muscle sits in the middle rows of its grid, so its force is in lines 2-5, and a cell in line 0 or 7 (a corner) is never in a line where a tooth has force. Nobody wrote hiding; it is a shape. Lineages are fewer than in e010 at width 2 (1-6 alive) and width 1 (4-10): an island is now a few cells wide, and one lineage after another takes it (the timeline in 3.5).",
    "h3": "The world stands, faster with larger bodies",
    "r3": "The population settles at 2,900-3,300 (width 4), 2,100-2,400 (width 2) and 1,100-2,000 (width 1); the per-body cost bounds it and the same food feeds fewer, larger bodies. Speed follows the number of bodies: 376-656, 579-782 and 574-846 steps per second. The contact loop, which is where the cost of a crowd would show (6,000-13,000 pushes per step at width 1), does not slow the world.",
    "h4": "Teeth appear where bodies crowd, and armor answers",
    "r4": "In e010 a body with a bite was a one-in-twelve-million event. At width 1, hard cells are above 1 per body from the first log step in every seed, 12-24% of bodies have a bite, 260-550 cells break per step, and meat is 9-19% of all energy eaten. Hunter lineages are no longer booms of a few thousand steps: 26-50 per seed, the longest 156,000-483,000 steps, with 26-34% of their food from other bodies as a rule and 83-85% in width 1, seed 3 (three lineages of mass 41-59 with 30-44 hard cells, 6-12 muscle and a gut of 3: carnivores that graze almost nothing). Armor answers: the mean hardness of a touchable tip goes from 1.0 in e010 to 2.3-8.1 (a two-cell wall is 6), and in seed 4 the wall thickens over the run (hard 8 to 25-32 per body from 200,000 to 500,000 steps) while the meat share halves from 18% to 8-10%. Width 2 is on the edge: seeds 2 and 4 flip into the same regime (at 280,000 and 600,000 steps, hard from 0.4 to 12 in one 100,000-step window in seed 2), seeds 1 and 3 never do. Deaths by damage stay low (0.002-0.018 per birth) because a bite mostly takes one cell of a tortoise, and a corner body is never in its way.",
    "viewer": "Width 1, seed 1. In the long view the islands are a few cells wide and one lineage at a time holds most of the population (the bands of the timeline, 1,000-1,500 agents, replacing each other every 100,000-200,000 steps). In the zoom, a tortoise is a square of blue with green inside; a hunter has orange behind a blue tip; a corner body is green cells in the corners of its square and nothing between them. White dots are bodies with a bite. Scrub through the clip to watch the crowd on a patch push and be pushed.",
    "discussion": "<p>The premise we took from the real world was that a cell can hold more than one bite. What it did is not what the metaphor said. The gut grew a little; the crowd grew a lot, and the crowd made contact the main fact of life on an island. Everything e010 had said was unreachable then became reachable: a tooth pays on every step in a cell of fifty bodies, armor on every side keeps a parent's tooth off its children (a tortoise's child is born a tortoise), and a shape that cannot be touched (cells in the corners only, two to twelve of them) is found by mutation because it is one cell away from a corner blob. The three things a hunter needed at once are all cheaper in a crowd. The world made tortoises, hunters and corner bodies, not elephants, and that is the point of principles.md: the metaphor is a source, not a target.</p><p>Size did get a reason in the world, but the reason is armor, and armor is 64 cells at most. The 90th percentile of mass is 64 at width 1: the grid is the wall now, as the defense rule was in e008. This is the argument for #5 (3D bodies, or a larger grid): not that bodies should be bigger, but that the population is pressed against a limit we drew.</p><p>What the experiment does not show. Width 2 flips in two seeds of four and width 1 in four of four (and width 8 in none of twelve): what decides the flip is not measured here; seed 2 of width 2 went from hard 0.4 to 12 in one 100,000-step window, which looks like one lineage finding the tortoise and the tooth close together. Lineages are fewer (1-10) than in e010 (8-17): an island a few cells wide is one niche with one holder at a time, plus the corner bodies. A cap on what a cell holds was tried and does nothing here, since a crowded cell never fills; it would matter in a world where a patch can stand ungrazed. And the crowd is a product of the drift rule: a patch of width 1 moves one cell every 50 steps, and 6,000-13,000 pushes per step are bodies following it.</p><p>What the viewer sees is different from e010: bodies with shapes, three kinds on one screen, one lineage after another taking an island. It is one island at a time, though; four of them in 128x128, each a few cells wide. A world with both kinds of place, thin grass and dense trees, would let e010's grazers and these tortoises exist in the same run, and let a lineage move between them.</p>",
    "conclusion": "One law of the world, the same regrowth on fewer cells, gives size a reason and starts the arms race that seven experiments of trait rules could not: at width 1 (6.5 regrowth per cell per step), bodies of 18-43 cells with 6-26 hard cells, 12-24% with a bite, meat 9-19% of intake, 26-50 hunter lineages per seed lasting up to 483,000 steps, and three body kinds coexisting (tortoise, hunter, corner body). The gut is not why: bodies crowd and share a cell, and the gut stays at 10-16 cells in every concentrated world; the size is armor. Keep the width as a law of the world (1 or 2; 2 is the edge where the arms race starts in half the seeds) and drop the cap. Next: a world with both kinds of place in one run (wide patches and narrow ones), so that grazers and tortoises are neighbors and lineages can move between them; then #5, since a full square is the wall now (the 90th percentile of mass is 64), and #4.",
}

if __name__ == "__main__":
    main()
