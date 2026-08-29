#!/usr/bin/env python3
"""Build report.html for e006.

Charts: matplotlib, exported as SVG and inlined. Diagram: hand-written SVG.
Run from the repo root: uv run python experiments/e006_species/report.py
"""
import base64
import csv
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
# Lineage colors for the timeline and the viewer: lineages get palette slots in the order they were confirmed,
# so lineages alive at the same time (usually close in that order) get different colors.
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
RUNS = {"sexual": "sexual_d6_r1", "asexual": "asexual_d6_r1"}
VARIANTS = {"D = 3": "sexual_d3_r1_seed1", "D = 6": "sexual_d6_r1_seed1", "D = 10": "sexual_d10_r1_seed1", "radius 3": "sexual_d6_r3_seed1"}
KIND_COLOR = {1: SERIES[0], 2: SERIES[1], 3: SERIES[3], 4: SERIES[2]}
D = 6
CONFIRM_STEPS = 5000


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


def lifetimes(run):
    first, last, _ = lineage_stats(run)
    return [last[i] - first[i] + CONFIRM_STEPS for i in first]


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


def line_chart(title, subtitle, xs, series, ymin=None, percent=False):
    fig, ax = new_axes()
    for label, ys, slot in series:
        ax.plot(xs, ys, color=SERIES[slot], linewidth=1.6, label=label)
    if ymin is not None:
        ax.set_ylim(ymin, max(v for _, ys, _ in series for v in ys) * 1.12)
    ax.yaxis.set_major_formatter((lambda y, _p: f"{y:.0%}") if percent else kfmt)
    ax.yaxis.set_major_locator(MaxNLocator(4))
    legend_above(ax, len(series))
    return figure(title, subtitle, to_svg(fig))


def hist_chart(title, subtitle, series, bins, xlabel, density=False, log=False):
    fig, ax = new_axes(xlabel)
    ax.margins(x=0.02)
    for label, values, slot in series:
        if len(series) == 1:
            ax.hist(values, bins=bins, color=SERIES[slot], alpha=0.75, label=label, density=density, edgecolor="none", rwidth=0.9)
        else:
            ax.hist(values, bins=bins, color=SERIES[slot], label=label, density=density, histtype="step", linewidth=1.8)
    if log:
        ax.set_xscale("log")
        ax.xaxis.set_major_formatter(kfmt)
    ax.yaxis.set_major_locator(MaxNLocator(4))
    ax.yaxis.set_major_formatter(kfmt)
    if density:
        ax.set_yticklabels([])
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
pre.log {{ background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 10px 14px; font-size: 12.5px; overflow-x: auto; color: var(--ink2); }}
.viewer {{ background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 14px; display: grid; grid-template-columns: 1fr; gap: 10px; }}
.viewer .canvases {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10px; align-items: start; }}
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
<svg viewBox="0 0 720 300" role="img" aria-label="A parent ready to split looks for a mate within reach whose gene list is at most D away; with a mate the child is a crossover, without one a copy. Every 1,000 steps the living agents are grouped by the same distance, and groups that last become lineages with logged births, splits, merges and extinctions." style="max-width:100%;height:auto;display:block">
<defs><marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="currentColor"/></marker></defs>
<g fill="none" stroke="currentColor" stroke-width="1.2" font-size="12" font-family="system-ui, sans-serif">
  <rect x="20" y="40" width="200" height="130" rx="6"/>
  <text x="120" y="64" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">Parent ready to split</text>
  <g fill="currentColor" stroke="none">
    <text x="35" y="90">energy &gt;= 2 + 0.1 x mass</text>
    <text x="35" y="112">looks in its cell + 4 neighbors</text>
    <text x="35" y="134">for a living agent with</text>
    <text x="35" y="156" font-weight="600">gene distance &lt;= D = 6</text>
  </g>
  <line x1="220" y1="80" x2="298" y2="80" marker-end="url(#arr)" stroke="var(--s1)" stroke-width="2"/>
  <text x="259" y="72" text-anchor="middle" fill="currentColor" stroke="none">mate found</text>
  <line x1="220" y1="140" x2="298" y2="140" marker-end="url(#arr)"/>
  <text x="259" y="132" text-anchor="middle" fill="currentColor" stroke="none">none</text>

  <rect x="300" y="50" width="170" height="52" rx="6" stroke="var(--s1)" stroke-width="2"/>
  <text x="385" y="72" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">One-point crossover</text>
  <text x="385" y="91" text-anchor="middle" fill="currentColor" stroke="none" opacity="0.75">parent's start + mate's end</text>
  <rect x="300" y="114" width="170" height="52" rx="6"/>
  <text x="385" y="136" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">Copy (as e005)</text>
  <text x="385" y="155" text-anchor="middle" fill="currentColor" stroke="none" opacity="0.75">the child is the parent</text>

  <line x1="470" y1="76" x2="518" y2="98" marker-end="url(#arr)"/>
  <line x1="470" y1="140" x2="518" y2="118" marker-end="url(#arr)"/>
  <rect x="520" y="72" width="184" height="72" rx="6"/>
  <text x="612" y="94" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">Child</text>
  <text x="612" y="113" text-anchor="middle" fill="currentColor" stroke="none" opacity="0.75">+ 2 point mutations</text>
  <text x="612" y="131" text-anchor="middle" fill="currentColor" stroke="none" opacity="0.75">gets half the parent's energy</text>

  <line x1="360" y1="180" x2="360" y2="208" marker-end="url(#arr)" stroke-dasharray="4 3"/>
  <text x="372" y="198" fill="currentColor" stroke="none" opacity="0.75">every 1,000 steps, all living agents</text>
  <rect x="20" y="212" width="680" height="72" rx="6"/>
  <text x="360" y="234" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">Lineage detection: the same distance, the same D</text>
  <g fill="currentColor" stroke="none" text-anchor="middle">
    <text x="130" y="256">group = agents linked by chains of</text><text x="130" y="272">gene distance &lt;= 6, at least 5 of them</text>
    <text x="360" y="256">a group that lasts 5 detections</text><text x="360" y="272">is a lineage (birth or split)</text>
    <text x="590" y="256">carriers relabeled into another: merge</text><text x="590" y="272">no living carrier: extinct</text>
  </g>
</g>
</svg>
<figcaption>Figure 1. Reproduction and detection use one rule. Above: a parent that can split mates with the first neighbor whose gene list is within D = 6 of its own, else it buds as in e005; the parent pays either way. Below: lineages are the groups that this same rule would let genes flow through, kept only if they last, and every change of the set of lineages is one line in the event log.</figcaption>
</figure>
"""


# ---------- viewer ----------

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


def pack_frames(path, confirmed_at, every=1, limit=None):
    """Frames packed small: food as 4-bit nibbles; agents as x, y, body id (2 bytes), lineage (2 bytes).
    A lineage id is written only once the lineage is confirmed (else 0)."""
    out = []
    used = set()
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
        out.append({"s": fr["step"], "f": base64.b64encode(nib).decode(), "a": base64.b64encode(bytes(ag)).decode()})
        if limit and len(out) >= limit:
            break
    return out, used


VIEWER_JS = r"""
(function(){
  const data = JSON.parse(document.getElementById('frames').textContent);
  const bodies = data.bodies, KC = data.kindColors, PAL = data.palette, NONE = data.none;
  const cv = document.getElementById('world'), ctx = cv.getContext('2d');
  const zv = document.getElementById('zoom'), zctx = zv.getContext('2d');
  const W = 64, H = 64, S = cv.width / W, ZN = 12, ZS = zv.width / ZN;
  const off = document.createElement('canvas'); off.width = W; off.height = H;
  const octx = off.getContext('2d'), img = octx.createImageData(W, H);
  ctx.imageSmoothingEnabled = false; zctx.imageSmoothingEnabled = false;
  const slider = document.getElementById('scrub'), stepLbl = document.getElementById('steplbl'), linLbl = document.getElementById('linlbl');
  const playBtn = document.getElementById('play'), mode = document.getElementById('mode');
  let frames = data.long, i = 0, timer = null, zx = 26, zy = 26;
  const sprites = {}, stats = {};
  function color(lin){ return lin ? PAL[data.slots[lin] || 0] : NONE; }
  // Same rules as the simulation: attack = min(hard blocks in the top 3 rows, muscle blocks); defense = hard / 2.
  function stat(id){
    if (stats[id]) return stats[id];
    const cells = bodies[id] || ''; let hard = 0, front = 0, muscle = 0;
    for (let k = 0; k < 64; k++) { const v = cells.charCodeAt(k) - 48; if (v === 1) { hard++; if (k < 24) front++; } else if (v === 2) muscle++; }
    return stats[id] = { attack: Math.min(front, muscle), defense: hard / 2 };
  }
  function sprite(id){
    if (sprites[id]) return sprites[id];
    const c = document.createElement('canvas'); c.width = 8; c.height = 8; const x = c.getContext('2d');
    const cells = bodies[id] || '';
    for (let k = 0; k < 64; k++) { const v = cells.charCodeAt(k) - 48; if (v > 0) { x.fillStyle = KC[v]; x.fillRect(k % 8, (k / 8) | 0, 1, 1); } }
    return sprites[id] = c;
  }
  function b64(s){ const b = atob(s); const u = new Uint8Array(b.length); for (let k = 0; k < b.length; k++) u[k] = b.charCodeAt(k); return u; }
  function paintFood(target, food, x0, y0, n, cell){
    for (let y = 0; y < n; y++) for (let x = 0; x < n; x++) {
      const c = ((y0 + y) & 63) * W + ((x0 + x) & 63);
      const v = (c % 2 === 0) ? (food[c >> 1] >> 4) : (food[c >> 1] & 15);
      const g = 40 + v * 12;
      target.fillStyle = 'rgb(' + (g * 0.35 | 0) + ',' + g + ',' + (g * 0.45 | 0) + ')';
      target.fillRect(x * cell, y * cell, cell, cell);
    }
  }
  function draw(){
    const fr = frames[i]; const food = b64(fr.f), ag = b64(fr.a);
    const px = img.data;
    for (let c = 0; c < W * H; c++) {
      const v = (c % 2 === 0) ? (food[c >> 1] >> 4) : (food[c >> 1] & 15);
      const g = 40 + v * 12;
      px[c * 4] = g * 0.35; px[c * 4 + 1] = g; px[c * 4 + 2] = g * 0.45; px[c * 4 + 3] = 255;
    }
    octx.putImageData(img, 0, 0);
    ctx.drawImage(off, 0, 0, cv.width, cv.height);
    paintFood(zctx, food, zx, zy, ZN, ZS);
    const counts = {}, teeth = {}, armor = {}; let n = 0;
    for (let k = 0; k < ag.length; k += 6) {
      const x = ag[k], y = ag[k + 1], id = ag[k + 2] | (ag[k + 3] << 8), lin = ag[k + 4] | (ag[k + 5] << 8);
      const st = stat(id);
      ctx.fillStyle = color(lin); ctx.fillRect(x * S + 1, y * S + 1, S - 2, S - 2);
      if (st.attack > 0) { ctx.fillStyle = '#fff'; ctx.fillRect(x * S + S / 2 - 1.5, y * S + S / 2 - 1.5, 3, 3); }
      const dx = (x - zx + 64) & 63, dy = (y - zy + 64) & 63;
      if (dx < ZN && dy < ZN) { zctx.fillStyle = color(lin); zctx.fillRect(dx * ZS + 1, dy * ZS + 1, ZS - 2, ZS - 2); zctx.drawImage(sprite(id), dx * ZS + 5, dy * ZS + 5, ZS - 10, ZS - 10);
        if (st.attack > 0) { zctx.fillStyle = '#fff'; zctx.fillRect(dx * ZS + ZS / 2 - 3, dy * ZS + ZS / 2 - 3, 6, 6); } }
      counts[lin] = (counts[lin] || 0) + 1; teeth[lin] = (teeth[lin] || 0) + st.attack; armor[lin] = (armor[lin] || 0) + st.defense; n++;
    }
    zctx.strokeStyle = 'rgba(255,255,255,0.35)'; zctx.lineWidth = 1;
    for (let k = 0; k <= ZN; k++) { zctx.beginPath(); zctx.moveTo(k * ZS, 0); zctx.lineTo(k * ZS, zv.height); zctx.stroke(); zctx.beginPath(); zctx.moveTo(0, k * ZS); zctx.lineTo(zv.width, k * ZS); zctx.stroke(); }
    ctx.strokeStyle = '#fff'; ctx.lineWidth = 1.5; ctx.strokeRect(zx * S, zy * S, ZN * S, ZN * S);
    stepLbl.textContent = 'step ' + fr.s.toLocaleString() + ' - ' + n + ' agents';
    const keys = Object.keys(counts).map(Number).sort((a, b) => counts[b] - counts[a]);
    linLbl.innerHTML = keys.map(l => '<span class="lin" style="background:' + color(l) + '">' + (l ? 'lineage ' + l : 'none') + ': ' + counts[l]
      + ' (teeth ' + Math.round(teeth[l] / counts[l]) + ', armor ' + Math.round(armor[l] / counts[l]) + ')</span>').join('');
  }
  function setMode(){ frames = data[mode.value]; i = 0; slider.max = frames.length - 1; draw(); }
  function tick(){ i = (i + 1) % frames.length; draw(); }
  playBtn.onclick = function(){ if (timer) { clearInterval(timer); timer = null; playBtn.textContent = 'Play'; } else { timer = setInterval(tick, mode.value === 'clip' ? 100 : 200); playBtn.textContent = 'Pause'; } };
  slider.oninput = function(){ i = +slider.value; draw(); };
  mode.onchange = function(){ if (timer) playBtn.onclick(); setMode(); };
  cv.onclick = function(e){ const r = cv.getBoundingClientRect(); zx = Math.floor((e.clientX - r.left) / r.width * W - ZN / 2) & 63; zy = Math.floor((e.clientY - r.top) / r.height * H - ZN / 2) & 63; draw(); };
  setMode();
})();
"""


def main():
    logs = {m: {s: load_csv(f"results/{RUNS[m]}_seed{s}_log.csv") for s in SEEDS} for m in RUNS}
    events = {m: {s: load_rows(f"results/{RUNS[m]}_seed{s}_events.csv") for s in SEEDS} for m in RUNS}
    L = logs["sexual"][1]
    xs = L["step"]
    run1 = f"{RUNS['sexual']}_seed1"

    def seeds(mode, key):
        return [(f"Seed {s}", logs[mode][s][key], i) for i, s in enumerate(SEEDS)]

    def med(v):
        return statistics.median(v)

    def summarize(run):
        log = load_csv(f"results/{run}_log.csv")
        ev = load_rows(f"results/{run}_events.csv")
        first, last, size = lineage_stats(run)
        life = [last[i] - first[i] + CONFIRM_STEPS for i in first]
        n_lin = load_rows(f"results/{run}_lineages.csv")
        per_step = Counter(int(r["step"]) for r in n_lin)
        dets = int(log["step"][-1]) // 1000
        counts = Counter(r["event"] for r in ev)
        births = sum(log["births"])
        return dict(
            pop=med(log["pop"]),
            lineages=med([per_step.get(s, 0) for s in range(1000, int(log["step"][-1]) + 1, 1000)]),
            multi=sum(1 for s in range(1000, int(log["step"][-1]) + 1, 1000) if per_step.get(s, 0) >= 2) / dets,
            top=med(log["top_lineage_share"]), top9=sum(1 for t in log["top_lineage_share"] if t > 0.9) / len(log["pop"]),
            none=med(log["no_lineage_share"]), ids=len(first), life=med(life) if life else 0,
            life90=sorted(life)[int(0.9 * len(life))] if life else 0, longest=max(life) if life else 0,
            big=sum(1 for i in first if size[i] >= 100),
            births=counts["birth"], splits=counts["split"], merges=counts["merge"], extinct=counts["extinct"],
            rate=sum(counts.values()) / dets,
            neighbor=sum(log["births_with_neighbor"]) / births, sexual=sum(log["sexual_births"]) / births,
            sps=med(log["steps_per_sec"]), sps_min=min(log["steps_per_sec"]),
        )

    S = {f"{m} {s}": summarize(f"{RUNS[m]}_seed{s}") for s in SEEDS for m in ("sexual", "asexual")}
    V = {name: summarize(run) for name, run in VARIANTS.items()}

    charts = {
        "pop": line_chart("Population (sexual)", "Living agents. A flat line at zero would be extinction.", xs, seeds("sexual", "pop"), ymin=0),
        "sexshare": line_chart("How children are made (sexual, seed 1)", "Share of births with a living agent in reach, and with a compatible mate (a crossover). Zero would mean every child is a copy.", xs,
                               [("neighbor in reach", [n / max(1, b) for n, b in zip(L["births_with_neighbor"], L["births"])], 0),
                                ("mated", [n / max(1, b) for n, b in zip(L["sexual_births"], L["births"])], 1)], ymin=0, percent=True),
        "nlin_sex": line_chart("Number of lineages (sexual)", "Confirmed lineages alive at each log step. One would mean a single mating pool; zero, nothing that lasted 5,000 steps.", xs, seeds("sexual", "lineages"), ymin=0),
        "nlin_asex": line_chart("Number of lineages (asexual control)", "Same detection in the world without mating: the groups are kin clusters.", xs, seeds("asexual", "lineages"), ymin=0),
        "top_sex": line_chart("Share of the largest lineage (sexual)", "Fraction of living agents in the biggest lineage. Near 100% means one lineage is the world.", xs, seeds("sexual", "top_lineage_share"), ymin=0, percent=True),
        "top_asex": line_chart("Share of the largest lineage (asexual control)", "Same measure without mating.", xs, seeds("asexual", "top_lineage_share"), ymin=0, percent=True),
        "life": hist_chart("How long lineages last", "Lineages per lifetime bin (first sighting to last), both modes, seeds 1-3, log scale. A spike at the left edge would be lineages that vanish as soon as confirmed.",
                           [("sexual", sum((lifetimes(f"{RUNS['sexual']}_seed{s}") for s in SEEDS), []), 0),
                            ("asexual", sum((lifetimes(f"{RUNS['asexual']}_seed{s}") for s in SEEDS), []), 1)],
                           bins=[5000 * 1.35 ** k for k in range(14)], xlabel="steps", log=True),
        "sps": line_chart("Steps per second (sexual)", "Simulation speed, four or five runs sharing one machine. Mating and detection are on.", xs, seeds("sexual", "steps_per_sec"), ymin=0),
    }

    # Gene distance histograms, sexual seed 1, three times.
    dist = load_rows(f"results/{run1}_dist.csv")
    fig, ax = new_axes(xlabel="gene distance between two living agents")
    ax.margins(x=0.02)
    for slot, step in enumerate([100000, 500000, 1000000]):
        h = {int(r["value"]): int(r["count"]) for r in dist if r["measure"] == "genes" and int(r["step"]) == step}
        tot = sum(h.values())
        ax.bar([v + (slot - 1) * 0.28 for v in range(25)], [h.get(v, 0) / tot for v in range(25)], width=0.28, color=SERIES[slot], label=f"step {step:,}")
    ax.axvline(D + 0.5, color=INK, linewidth=1, linestyle="--")
    ax.yaxis.set_major_formatter(lambda y, _p: f"{y:.0%}")
    ax.yaxis.set_major_locator(MaxNLocator(4))
    legend_above(ax, 3)
    charts["dist"] = figure("Gene distance between living agents (sexual, seed 1)", "Share of all pairs at each distance, three moments. The dashed line is D = 6: pairs left of it could mate. Mass far right of it is between lineages.", to_svg(fig))

    timeline = timeline_chart("Lineages over time (sexual, seed 1)", "Each colored band is one lineage, height = agents in it; marks are events at the size they were logged with. Read left to right: this is the evolution log as a picture.", run1, events["sexual"][1])

    # Viewer.
    first, _, _ = lineage_stats(run1)
    bodies = load_bodies(run1)
    long_frames, used_l = pack_frames(f"results/{run1}_long.jsonl", first, every=2)
    clip_frames, used_c = pack_frames(f"results/{run1}_clip.jsonl", first, limit=200)
    legend = " ".join(f'<span class="sw" style="background:{KIND_COLOR[k]}"></span>{name}' for k, name in ((1, "hard"), (2, "muscle"), (3, "sensor"), (4, "digestive")))
    viewer_data = {"long": long_frames, "clip": clip_frames, "bodies": {str(b): bodies[b] for b in used_l | used_c},
                   "kindColors": {str(k): v for k, v in KIND_COLOR.items()}, "palette": LINEAGE_PALETTE, "none": NONE_COLOR,
                   "slots": {str(k): v for k, v in color_slots(run1).items()}}

    # Event log sample.
    sample = events["sexual"][1][:14]
    log_txt = "step,event,lineage,other,size\n" + "\n".join(",".join(r[k] for k in ("step", "event", "lineage", "other", "size")) for r in sample) + "\n..."

    def row(label, f):
        return f"<tr><td>{label}</td>" + "".join(f"<td>{f(S[f'sexual {s}'])}</td><td>{f(S[f'asexual {s}'])}</td>" for s in SEEDS) + "</tr>"

    summary = ("<thead><tr><th>Measure</th>" + "".join(f"<th>Seed {s} sexual</th><th>Seed {s} asexual</th>" for s in SEEDS) + "</tr></thead><tbody>"
               + row("Population, median", lambda d: f"{d['pop']:.0f}")
               + row("Children with a mate", lambda d: f"{d['sexual']:.0%}")
               + row("Lineages alive, median", lambda d: f"{d['lineages']:.0f}")
               + row("Detections with 2+ lineages", lambda d: f"{d['multi']:.0%}")
               + row("Largest lineage, median share", lambda d: f"{d['top']:.0%}")
               + row("Windows with one lineage above 90%", lambda d: f"{d['top9']:.0%}")
               + row("Lineages over the run", lambda d: f"{d['ids']}")
               + row("Lineages that reached 100 agents", lambda d: f"{d['big']}")
               + row("Lifetime, median / p90 (steps)", lambda d: f"{d['life']:,.0f} / {d['life90']:,.0f}")
               + row("Longest lifetime (steps)", lambda d: f"{d['longest']:,.0f}")
               + row("Events: births / splits / merges / extinctions", lambda d: f"{d['births']} / {d['splits']} / {d['merges']} / {d['extinct']}")
               + row("Events per 1,000 steps", lambda d: f"{d['rate']:.2f}")
               + row("Steps per second, median (min)", lambda d: f"{d['sps']:,.0f} ({d['sps_min']:,.0f})")
               + "</tbody>")

    def vrow(label, f):
        return f"<tr><td>{label}</td>" + "".join(f"<td>{f(V[n])}</td>" for n in VARIANTS) + "</tr>"

    variants = ("<thead><tr><th>Seed 1, sexual</th>" + "".join(f"<th>{n}</th>" for n in VARIANTS) + "</tr></thead><tbody>"
                + vrow("Children with a neighbor in reach / with a mate", lambda d: f"{d['neighbor']:.0%} / {d['sexual']:.0%}")
                + vrow("Lineages alive, median", lambda d: f"{d['lineages']:.0f}")
                + vrow("Largest lineage, median share", lambda d: f"{d['top']:.0%}")
                + vrow("Agents in no lineage, median share", lambda d: f"{d['none']:.0%}")
                + vrow("Lineages over the run / reached 100", lambda d: f"{d['ids']} / {d['big']}")
                + vrow("Lifetime, median (steps)", lambda d: f"{d['life']:,.0f}")
                + vrow("Events per 1,000 steps", lambda d: f"{d['rate']:.2f}")
                + "</tbody>")

    tables = data_table(["step", "pop", "births", "births_with_neighbor", "sexual_births", "lineages", "top_lineage_share", "no_lineage_share", "mass_mean", "hard_mean", "muscle_mean", "digestive_mean", "attack_mean", "distinct_bodies", "steps_per_sec"],
                        {f"Seed {s} {m} (every 100,000 steps)": logs[m][s] for s in SEEDS for m in ("sexual", "asexual")}, every=10)

    text = TEXT
    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>e006 Species - Report</title>
<style>{CSS}</style>
</head>
<body>
<main>
<h1>e006: Does sex under a compatibility limit make lineages that are born, split, and die?</h1>
<p class="sub">Experiment report - 2026-08-29 - three seeds, 1,000,000 steps each, with and without mating, plus three variants</p>

<section class="tldr">
<h2>TL;DR</h2>
<p>{text["tldr"]}</p>
</section>

<h2>1. Question</h2>
<p>{text["question"]}</p>
<ol>
  <li><strong>Lineages form.</strong> Two or more lineages exist for more than half of the run, and one lineage is not the whole population.</li>
  <li><strong>Lineages split and die.</strong> The event log has splits and extinctions, and lineages are not one-detection flickers: median lifetime at least 10,000 steps.</li>
  <li><strong>Sex holds a lineage together.</strong> The largest lineage holds a bigger share, and events are rarer, in the sexual world than in the asexual control.</li>
  <li><strong>Cost.</strong> Above 5,000 steps per second with mating and detection on.</li>
</ol>

<h2>2. The world</h2>
<p>{text["world"]}</p>
{DIAGRAM}
<p>{text["distance"]}</p>
<p><strong>Runs.</strong> Seeds 1-3 in both modes, 1,000,000 steps, D = 6, mate search in the cell and its 4 neighbors. Seed 1 also with D = 3, D = 10, and a search radius of 3 (25 cells). We record:</p>
<ul class="measures">
  <li><strong>Births</strong>, births with a living agent in reach, births with a mate.</li>
  <li><strong>Lineages</strong> every 1,000 steps: size, mean blocks by kind, distinct bodies.</li>
  <li><strong>Events</strong>: birth, split, merge, extinction, with the lineage's size at the time.</li>
  <li><strong>Largest lineage</strong> share and agents in no lineage, every 10,000 steps.</li>
  <li><strong>Gene distance</strong> between all pairs of living agents, every 50,000 steps.</li>
  <li><strong>Snapshots</strong> with each agent's body and lineage, and e005's log of bodies, diet, and deaths.</li>
</ul>

<h2>3. Results</h2>
<div class="tw"><table>{summary}</table></div>
<ol class="verdicts">
<li><span class="verdict">Yes</span> {text["v1"]}</li>
<li><span class="verdict partly">Partly</span> {text["v2"]}</li>
<li><span class="verdict no">No</span> {text["v3"]}</li>
<li><span class="verdict partly">Partly</span> {text["v4"]}</li>
</ol>

<h3>3.1 Lineages exist, and there are usually two or more</h3>
<div class="grid2">
{charts["nlin_sex"]}{charts["top_sex"]}
</div>
<div class="grid2">
{charts["nlin_asex"]}{charts["top_asex"]}
</div>
<p>{text["r1"]}</p>

<h3>3.2 The evolution log: lineages appear, split, merge, and go extinct</h3>
<div class="wide">{timeline}</div>
<pre class="log">{html.escape(log_txt)}</pre>
<div class="grid2">
{charts["life"]}{charts["dist"]}
</div>
<p>{text["r2"]}</p>

<h3>3.3 Sex is rare, and it does not change the picture</h3>
<div class="grid2">
{charts["sexshare"]}{charts["pop"]}
</div>
<div class="tw"><table>{variants}</table></div>
<p>{text["r3"]}</p>

<h3>3.4 Watching lineages</h3>
<div class="viewer">
  <div class="canvases">
    <canvas id="world" width="640" height="640"></canvas>
    <canvas id="zoom" width="480" height="480"></canvas>
  </div>
  <div class="bar">
    <button id="play">Play</button>
    <select id="mode"><option value="long">Long view: every 10,000 steps</option><option value="clip">Clip: every step from 600,000</option></select>
    <span id="steplbl"></span>
  </div>
  <div class="bar"><input id="scrub" type="range" min="0" max="0" value="0"></div>
  <div class="bar" id="linlbl"></div>
  <div class="bar" id="legend">Blocks: {legend} <span class="sw dot"></span> can bite (attack &gt; 0)</div>
  <div class="bar">Left: the whole world, each agent colored by its lineage (gray: none); a white dot marks an agent with attack above 0, so it can eat prey. Click to move the white box. Right: the box at 12x12 cells, bodies drawn on the lineage color, the same dot on the ones that can bite. Green: food. Labels: agents per lineage, then the lineage's mean attack (teeth) and defense (armor). Sexual mode, seed 1.</div>
</div>
<p>{text["viewer"]}</p>
<div class="grid2">{charts["sps"]}</div>

<h2>4. Discussion</h2>
{text["discussion"]}

<h2>5. Conclusion and next step</h2>
<p>{text["conclusion"]}</p>

<h2>Appendix: data</h2>
<p>Every 100,000th record; full logs in <code>results/*_log.csv</code>, lineages in <code>results/*_lineages.csv</code>, events in <code>results/*_events.csv</code>, distance histograms in <code>results/*_dist.csv</code>, snapshots in <code>results/*_{{long,clip,bodies}}.jsonl</code>. Build this report with <code>uv run python experiments/e006_species/report.py</code>.</p>
{tables}
</main>
<script id="frames" type="application/json">{json.dumps(viewer_data, separators=(",", ":"))}</script>
<script>{VIEWER_JS}</script>
</body>
</html>
"""
    out = os.path.join(HERE, "report.html")
    with open(out, "w") as f:
        f.write(page)
    print(f"wrote {out} ({os.path.getsize(out)//1024} KB)")


TEXT = {
    "tldr": "Yes to lineages, no to sex. Grouping living agents by gene distance (two agents are linked if their gene lists differ by at most 6 genes) finds two or more lineages for 71-98% of the run, the largest holding half to three quarters of the population, and the log records 34-97 splits and 28-92 extinctions per million steps, lineages lasting a median 11,000 steps (60-100 generations) and up to 856,000. Lineages differ in body: an armored lineage and an omnivore lineage live side by side for 100,000 steps. But mating under the compatibility limit changes none of this: the asexual control has the same lineage counts, shares, and event rates. A mate is in reach at only 16-23% of births, and when found it is a near-clone. The species boundaries come from mutation and drift; the limit only names them. Next: keep the detector, the log, and the viewer; sex needs a reason to exist before it can matter.",
    "question": "e005 gave a world with bodies and a food web that does not settle. The vision's third mechanism is species: sexual reproduction that only works between similar genomes, so that a species boundary is real (genes flow inside, not across), plus detection of lineages by the same rule and an event log of their births, splits, and extinctions. Does that produce lineages that appear, spread, and die, and is any of it different from what kinship alone does in the asexual world?",
    "world": "Everything is e005: the 64x64 world, bodies grown from the genome, upkeep per block, one predation rule, and the batched development from issue #6. Only reproduction changes (Figure 1). Mode <em>asexual</em> skips the mate search and reproduces e005 byte for byte; it is the control.",
    "distance": "<strong>Distance</strong> is measured on gene lists, not on the 512 symbols. A gene is 8 symbols after a promoter; the distance between two genomes is the number of genes in one list but not the other. A mutation inside a gene moves it by 2, one that makes or breaks a promoter by 1, one outside the genes (most of them) by 0. Hamming distance over all symbols was rejected after measuring it: at 2 mutations per child, two members of one family are 50-150 symbols apart within 100,000 steps while their gene lists differ by 0-4. D = 6 sits in the valley of the gene-distance histogram measured on the asexual world (within-family 0-4, between-family 15-22).",
    "v1": "Lineages form: two or more lineages at 71-98% of detections, largest lineage 49-76% of the population (median), above 90% in at most a quarter of the windows.",
    "v2": "Lineages split and die: 34-97 splits and 28-92 extinctions per run; median lifetime 11,000 steps from first sighting, of which 5,000 is the confirmation window; a tenth last 85,000 steps or more.",
    "v3": "Sex holds a lineage together: the largest lineage's share and the event rate are the same as in the asexual control (differences within seed-to-seed spread).",
    "v4": "Cost: 7,600-15,600 steps per second median with four or five runs sharing the machine; the minimum drops to 3,200 in one seed.",
    "r1": "With or without mating, the world holds two to three lineages most of the time, one of them large. The asexual charts (bottom row) are the control: same shape, same range. Seeds differ more from each other than the modes do. Agents in no lineage are 0-12% of the population: the detector labels nearly everyone.",
    "r2": "The timeline is the evolution log drawn: bands are lineages, and every mark is one line of <code>events.csv</code>. Almost every lineage is born by splitting from another (one or two <em>birth</em> events per run, all the rest <em>split</em>). Lifetimes are heavy-tailed: half the lineages are gone within 6,000 steps of confirmation, a tenth last 85,000 steps or more, and seed 2 has one that lasts 856,000. A generation is 100-170 steps here, so a median lineage is 60-100 generations. Lineages have different bodies: in seed 1, lineage 1 (armored grazer, 28-36 hard blocks, no muscle) and lineage 13 (omnivore, 20 hard, 19 muscle, attack 17) coexist from step 18,000 to 132,000. The gene-distance histogram shows why the detector works: within a lineage, pairs are 0-4 apart; between lineages, 15-22; little sits at the threshold.",
    "r3": "A mate is found at 16-23% of births. The reason is density, not incompatibility: a living agent is in reach (5 cells) at only 25-36% of births, and when one is, it is compatible 61-63% of the time. With a search radius of 3 (25 cells) mating rises to 58% of births, and the lineage picture does not move. D = 3 makes lineages smaller and shorter (195 over the run, 0.39 events per 1,000 steps, 23% of agents in none); D = 10 makes them fewer and bigger (53, 0.10 events per 1,000 steps, the largest above 90% in 38% of windows). D is a law that sets the grain of the log; sex is not a law that changes the world.",
    "viewer": "Each agent is drawn in its lineage's color, and a white dot marks the ones that can bite (attack above 0, the same rule the world uses). In the long view, the world is one or two colors at a time, with a new color appearing at an edge and either spreading or vanishing; the labels under the canvas count agents per lineage and give the lineage's mean teeth and armor, so an omnivore lineage (teeth 10-20) and a grazer lineage (teeth 0, armor 15-20) can be told apart without reading the bodies. At step 305,000, for example, lineage 42 (102 agents, teeth 11) is the one with dots and lineage 260 (120 agents, teeth 0, armor 21) has none. In the clip, colors barely change: 400 steps is two or three generations, and lineages are things of tens of thousands of steps.",
    "discussion": "<p>The evolution log is real. Detection by gene distance, with a confirmation window and merges told apart from extinctions, produces a log with about one event per 5,000 steps and lineages that last tens of thousands of steps. Without the confirmation window, the first version of the detector logged one event per 1,000 steps and a median lifetime of one detection: groups fall apart and rejoin whenever a connecting agent dies. The 5,000-step window is a filter on the detector, not a change to the world.</p><p>Sex, as built, is a no-op, and the numbers say why twice over. First, it is rare: with 250 agents on 4,096 cells a parent has nobody in reach three times out of four. Second, when it happens, it is between genomes whose gene lists already match within 6, so a one-point crossover of two near-clones is a near-clone. Widening the search to 25 cells fixes the first and not the second. The species boundaries in this world are made by mutation, drift, and the clonal sweeps of e005; separate families are 15-22 genes apart within 60-100 generations, and the compatibility limit only names what is already there.</p><p>What this does not show: whether sex could matter if it had a reason to exist (a cost to budding, an advantage to recombination) and a wider compatibility limit. Nor whether 60-100 generations per lineage is a good pace to watch; the app phase decides that, and the knobs are the mutation rate and D, both laws. One rough edge in the log: at a split the bigger piece keeps the name, and once in seed 1 that piece died within 2,000 steps while the armored piece went on under a new id. A naming rule that follows the body would read better.</p>",
    "conclusion": "Keep the detector, the event log, and the lineage-colored viewer: they turn e005's world into something with a history a person can read. Keep the mating code, it is cheap, but do not count on it: species in this world are kin groups, and sex neither makes nor holds them. The three mechanisms of <code>vision.md</code> are now built; the world has bodies, a food web, and named lineages that are born, split, and die on their own. Next: the open items from e005 (prey worth eating, sensors that mean something) and the question of pace, since lineages turn over every 60-100 generations and the viewer shows a world that changes its colors every few frames.",
}

if __name__ == "__main__":
    main()
