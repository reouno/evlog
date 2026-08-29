#!/usr/bin/env python3
"""Build report.html for this experiment.

Charts: matplotlib, exported as SVG and inlined. Diagram: hand-written SVG.
Run from the repo root: uv run python experiments/e005_body_world/report.py
"""
import csv
import html
import io
import os

import matplotlib
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator

matplotlib.use("svg")

HERE = os.path.dirname(os.path.abspath(__file__))
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4"]  # fixed slot order

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


# ---------- data ----------

def load_csv(path):
    """Read a CSV of numbers into {column: [floats]}."""
    with open(os.path.join(HERE, path)) as f:
        rows = list(csv.DictReader(f))
    return {k: [float(r[k]) for r in rows] for k in rows[0]}


# ---------- chart helpers ----------

def kfmt(x, _pos):
    return f"{x/1000:g}k" if abs(x) >= 1000 else f"{x:g}"


def to_svg(fig):
    buf = io.StringIO()
    fig.savefig(buf, format="svg", bbox_inches="tight", pad_inches=0.05)
    plt.close(fig)
    return buf.getvalue()


def new_axes(xlabel="step"):
    fig, ax = plt.subplots(figsize=(6.4, 2.6))
    ax.xaxis.set_major_formatter(kfmt)
    ax.set_xlabel(xlabel, loc="right")
    ax.margins(x=0)
    return fig, ax


def hist_chart(title, subtitle, series, bins, xlabel, density=False):
    """series: list of (label, values, slot). Overlapping histograms with a surface gap."""
    fig, ax = new_axes(xlabel)
    ax.margins(x=0.02)
    for label, values, slot in series:
        ax.hist(values, bins=bins, color=SERIES[slot], alpha=0.75, label=label, density=density,
                edgecolor="none", rwidth=0.9 if len(series) == 1 else 1.0)
    ax.yaxis.set_major_locator(MaxNLocator(4))
    ax.yaxis.set_major_formatter(kfmt)
    if density:
        ax.set_yticklabels([])  # heights are relative; the numbers mean nothing to a reader
    legend_above(ax, len(series))
    return figure(title, subtitle, to_svg(fig))


def legend_above(ax, n):
    ax.legend(loc="lower left", bbox_to_anchor=(0, 1.0), ncols=n, handlelength=1.2, borderaxespad=0, columnspacing=1.2)


def line_chart(title, subtitle, xs, series, ymin=None):
    """series: list of (label, ys, slot)."""
    fig, ax = new_axes()
    for label, ys, slot in series:
        ax.plot(xs, ys, color=SERIES[slot], linewidth=1.6, label=label)
    if ymin is not None:
        ax.set_ylim(ymin, max(v for _, ys, _ in series for v in ys) * 1.12)
    ax.yaxis.set_major_formatter(kfmt)
    ax.yaxis.set_major_locator(MaxNLocator(4))
    legend_above(ax, len(series))
    return figure(title, subtitle, to_svg(fig))


def stacked_area(title, subtitle, xs, layers):
    """layers: list of (label, ys, slot); fractions summing to ~1."""
    fig, ax = new_axes()
    ax.stackplot(xs, [ys for _, ys, _ in layers], labels=[l for l, _, _ in layers],
                 colors=[SERIES[s] for _, _, s in layers], linewidth=0)
    ax.set_ylim(0, 1)
    ax.yaxis.set_major_formatter(lambda y, _p: f"{y:.0%}")
    ax.yaxis.set_major_locator(MaxNLocator(4))
    legend_above(ax, len(layers))
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
  --s1: {SERIES[0]};
}}
@media (prefers-color-scheme: dark) {{
  :root:not([data-theme="light"]) {{
    --surface: #1a1a19; --page: #0d0d0d; --ink: #ffffff; --ink2: #c3c2b7; --grid: #2c2c2a; --border: rgba(255,255,255,0.10);
    --s1: #3987e5;
  }}
}}
:root[data-theme="dark"] {{
  --surface: #1a1a19; --page: #0d0d0d; --ink: #ffffff; --ink2: #c3c2b7; --grid: #2c2c2a; --border: rgba(255,255,255,0.10);
  --s1: #3987e5;
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

import base64
import json
from collections import Counter

KIND_COLOR = {1: SERIES[0], 2: SERIES[1], 3: SERIES[3], 4: SERIES[2]}  # hard blue, muscle orange, sensor yellow, digestive aqua
KIND_NAME = {1: "hard", 2: "muscle", 3: "sensor", 4: "digestive"}
DIET_COLOR = {0: SERIES[2], 1: SERIES[3], 2: SERIES[1], 3: "#898781"}  # plants aqua, mixed yellow, meat orange, none gray
DIET_NAME = {0: "plants only", 1: "mixed", 2: "meat only", 3: "nothing yet"}
SEEDS = [1, 2, 3]
KINDS = ["hard", "muscle", "sensor", "digestive"]

DIAGRAM = """
<figure class="diagram">
<svg viewBox="0 0 720 300" role="img" aria-label="A body's blocks give mass, speed, sense, bite and gut, attack and defense; one rule lets an agent eat a neighbor when its attack beats the neighbor's defense, the gut accepts its mass, and the neighbor does not out-run it." style="max-width:100%;height:auto;display:block">
<defs><marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="currentColor"/></marker></defs>
<g fill="none" stroke="currentColor" stroke-width="1.2" font-size="12" font-family="system-ui, sans-serif">
  <rect x="20" y="60" width="130" height="150" rx="6"/>
  <text x="85" y="84" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">Body (e004)</text>
  <text x="85" y="104" text-anchor="middle" fill="currentColor" stroke="none" opacity="0.75">8x8 blocks</text>
  <g stroke="none">
    <rect x="45" y="118" width="12" height="12" fill="%(hard)s"/><text x="63" y="128" fill="currentColor">hard</text>
    <rect x="45" y="138" width="12" height="12" fill="%(muscle)s"/><text x="63" y="148" fill="currentColor">muscle</text>
    <rect x="45" y="158" width="12" height="12" fill="%(sensor)s"/><text x="63" y="168" fill="currentColor">sensor</text>
    <rect x="45" y="178" width="12" height="12" fill="%(digestive)s"/><text x="63" y="188" fill="currentColor">digestive</text>
  </g>
  <line x1="150" y1="135" x2="228" y2="135" marker-end="url(#arr)"/>
  <text x="189" y="128" text-anchor="middle" fill="currentColor" stroke="none">derive</text>

  <rect x="230" y="30" width="230" height="212" rx="6"/>
  <text x="345" y="54" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">Function, per block</text>
  <g fill="currentColor" stroke="none">
    <text x="245" y="80">mass = blocks</text><text x="365" y="80" opacity="0.75">upkeep 0.002 each</text>
    <text x="245" y="102">speed = muscle / mass</text><text x="365" y="102" opacity="0.75">2-cell moves, escape</text>
    <text x="245" y="124">sense = sensor / 8</text><text x="365" y="124" opacity="0.75">sees 2 cells out</text>
    <text x="245" y="146">bite = 0.02 x digestive</text><text x="365" y="146" opacity="0.75">plants per step</text>
    <text x="245" y="168">gut = 4 x digestive</text><text x="365" y="168" opacity="0.75">largest prey</text>
    <text x="245" y="190">attack = min(front hard, muscle)</text>
    <text x="245" y="212">defense = hard / 2</text>
    <text x="245" y="234" opacity="0.75">split at energy 2 + 0.1 x mass</text>
  </g>

  <line x1="460" y1="135" x2="538" y2="135" marker-end="url(#arr)" stroke="var(--s1)" stroke-width="2"/>
  <text x="499" y="128" text-anchor="middle" fill="currentColor" stroke="none">meet</text>

  <rect x="540" y="60" width="160" height="150" rx="6" stroke="var(--s1)" stroke-width="2"/>
  <text x="620" y="84" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">One rule</text>
  <g fill="currentColor" stroke="none" text-anchor="middle">
    <text x="620" y="108">eat a neighbor if</text>
    <text x="620" y="130">attack &gt; its defense</text>
    <text x="620" y="150">its mass &lt;= gut</text>
    <text x="620" y="170">it does not out-run you</text>
    <text x="620" y="196" opacity="0.75">gain: half its energy</text>
  </g>
  <text x="360" y="280" text-anchor="middle" fill="currentColor" stroke="none" opacity="0.75">Herbivore, carnivore, armored, fast: none of these is a role. They are bodies that happen to work.</text>
</g>
</svg>
<figcaption>Figure 1. From blocks to function to predation. Every number on the left is derived from the body, and every block costs upkeep, so armor, teeth, speed, and gut compete for the same 64 cells. The one rule on the right is the only thing that says who eats whom.</figcaption>
</figure>
"""
for _k, _n in KIND_NAME.items():
    DIAGRAM = DIAGRAM.replace("%(" + _n + ")s", KIND_COLOR[_k])


# ---------- bodies ----------

def body_svg(cells, size=6, scale=1.5):
    n = 8
    w = n * size
    parts = [f'<svg viewBox="0 0 {w} {w}" width="{w*scale}" height="{w*scale}" class="body">']
    parts.append(f'<rect x="0" y="0" width="{w}" height="{w}" fill="var(--cell)"/>')
    for i, ch in enumerate(cells):
        k = int(ch)
        if k == 0:
            continue
        x, y = (i % n) * size, (i // n) * size
        parts.append(f'<rect x="{x+0.3}" y="{y+0.3}" width="{size-0.6}" height="{size-0.6}" fill="{KIND_COLOR[k]}"/>')
    parts.append("</svg>")
    return "".join(parts)


def legend():
    sw = "".join(f'<span><i style="background:{KIND_COLOR[k]}"></i>{KIND_NAME[k]}</span>' for k in (1, 2, 3, 4))
    return f'<div class="legend">{sw}<span><i style="background:var(--cell);border:1px solid var(--grid)"></i>empty</span></div>'


def load_bodies(seed):
    out = {}
    with open(os.path.join(HERE, f"results/seed{seed}_bodies.jsonl")) as f:
        for line in f:
            d = json.loads(line)
            out[d["id"]] = d["cells"]
    return out


def read_frames(path):
    with open(os.path.join(HERE, path)) as f:
        for line in f:
            yield json.loads(line)


def pack_frames(path, every=1, limit=None):
    """Frames packed small: food as 4-bit nibbles; agents as x, y, body id (2 bytes), diet."""
    out = []
    used = set()
    for i, fr in enumerate(read_frames(path)):
        if i % every:
            continue
        food = fr["food"]
        nib = bytes((food[j] << 4) | food[j + 1] for j in range(0, len(food), 2))
        ag = bytearray()
        for x, y, b, d in fr["agents"]:
            ag += bytes((x, y, b & 255, b >> 8, d))
            used.add(b)
        out.append({"s": fr["step"], "f": base64.b64encode(nib).decode(), "a": base64.b64encode(bytes(ag)).decode()})
        if limit and len(out) >= limit:
            break
    return out, used


def body_attrs(cells):
    k = Counter(int(c) for c in cells)
    front = sum(1 for i, c in enumerate(cells[:24]) if c == "1")
    return dict(mass=64 - k[0], hard=k[1], muscle=k[2], sensor=k[3], digestive=k[4], attack=min(front, k[2]), defense=k[1] / 2)


VIEWER_JS = r"""
(function(){
  const data = JSON.parse(document.getElementById('frames').textContent);
  const bodies = data.bodies, KC = data.kindColors;
  const cv = document.getElementById('world'), ctx = cv.getContext('2d');
  const zv = document.getElementById('zoom'), zctx = zv.getContext('2d');
  const W = 64, H = 64, S = cv.width / W, ZN = 12, ZS = zv.width / ZN;
  const off = document.createElement('canvas'); off.width = W; off.height = H;
  const octx = off.getContext('2d'), img = octx.createImageData(W, H);
  ctx.imageSmoothingEnabled = false; zctx.imageSmoothingEnabled = false;
  const slider = document.getElementById('scrub'), stepLbl = document.getElementById('steplbl');
  const playBtn = document.getElementById('play'), mode = document.getElementById('mode');
  let frames = data.long, i = 0, timer = null, zx = 26, zy = 26;
  const sprites = {};
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
    let n = 0;
    for (let k = 0; k < ag.length; k += 5) {
      const x = ag[k], y = ag[k + 1], id = ag[k + 2] | (ag[k + 3] << 8);
      ctx.drawImage(sprite(id), x * S, y * S, S, S);
      const dx = (x - zx + 64) & 63, dy = (y - zy + 64) & 63;
      if (dx < ZN && dy < ZN) zctx.drawImage(sprite(id), dx * ZS + 2, dy * ZS + 2, ZS - 4, ZS - 4);
      n++;
    }
    zctx.strokeStyle = 'rgba(255,255,255,0.35)'; zctx.lineWidth = 1;
    for (let k = 0; k <= ZN; k++) { zctx.beginPath(); zctx.moveTo(k * ZS, 0); zctx.lineTo(k * ZS, zv.height); zctx.stroke(); zctx.beginPath(); zctx.moveTo(0, k * ZS); zctx.lineTo(zv.width, k * ZS); zctx.stroke(); }
    ctx.strokeStyle = '#fff'; ctx.lineWidth = 1.5; ctx.strokeRect(zx * S, zy * S, ZN * S, ZN * S);
    stepLbl.textContent = 'step ' + fr.s.toLocaleString() + ' - ' + n + ' agents';
    slider.value = i;
  }
  function setMode(){ frames = data[mode.value]; i = 0; slider.max = frames.length - 1; draw(); }
  function tick(){ i = (i + 1) % frames.length; draw(); }
  playBtn.onclick = function(){ if (timer) { clearInterval(timer); timer = null; playBtn.textContent = 'Play'; } else { timer = setInterval(tick, mode.value === 'clip' ? 100 : 150); playBtn.textContent = 'Pause'; } };
  slider.oninput = function(){ i = +slider.value; draw(); };
  mode.onchange = function(){ if (timer) playBtn.onclick(); setMode(); };
  cv.onclick = function(e){ const r = cv.getBoundingClientRect(); zx = Math.floor((e.clientX - r.left) / r.width * W - ZN / 2) & 63; zy = Math.floor((e.clientY - r.top) / r.height * H - ZN / 2) & 63; draw(); };
  setMode();
})();
"""


def scatter_chart(title, subtitle, rows, xkey, ykey, xlabel, ylabel):
    """rows: list of dicts with xkey, ykey, diet. Colored by diet, jittered."""
    import random
    rnd = random.Random(1)
    fig, ax = new_axes(xlabel)
    ax.set_ylabel(ylabel)
    ax.margins(x=0.05)
    for d in (3, 0, 1, 2):
        xs = [r[xkey] + rnd.uniform(-0.4, 0.4) for r in rows if r["diet"] == d]
        ys = [r[ykey] + rnd.uniform(-0.4, 0.4) for r in rows if r["diet"] == d]
        if xs:
            ax.scatter(xs, ys, s=6, color=DIET_COLOR[d], alpha=0.5, linewidths=0, label=f"{DIET_NAME[d]} ({len(xs)})")
    ax.yaxis.set_major_locator(MaxNLocator(4))
    legend_above(ax, 2)
    return figure(title, subtitle, to_svg(fig))


def diet_of(r):
    p, m = r["plant"], r["meat"]
    if p + m <= 0:
        return 3
    if m <= 0:
        return 0
    if p <= 0:
        return 2
    return 1


def main():
    logs = {s: load_csv(f"results/seed{s}_log.csv") for s in SEEDS}
    agents = {s: load_csv(f"results/seed{s}_agents.csv") for s in SEEDS}
    L = logs[1]
    xs = L["step"]

    def seeds(key):
        return [(f"Seed {s}", logs[s][key], i) for i, s in enumerate(SEEDS)]

    # Drift: distance between the mean body (4 kind means) now and 100k steps (10 rows) earlier.
    def drift(log, lag=10):
        out = []
        for i in range(len(log["step"])):
            j = max(0, i - lag)
            out.append(sum((log[f"{k}_mean"][i] - log[f"{k}_mean"][j]) ** 2 for k in KINDS) ** 0.5)
        return out

    drifts = {s: drift(logs[s]) for s in SEEDS}

    charts = {
        "pop": line_chart("Population", "Living agents. A flat line at zero would be extinction; a steady climb would be an explosion.", xs, seeds("pop"), ymin=0),
        "mass": line_chart("Mean body mass", "Average number of blocks per living agent. Constant would mean the body size question is settled.", xs, seeds("mass_mean"), ymin=0),
        "kinds": line_chart("Blocks by kind (seed 1)", "Population average of each block kind. Lines crossing mean the typical body is being rebuilt.", xs,
                            [(k, L[f"{k}_mean"], i) for i, k in enumerate(KINDS)], ymin=0),
        "distinct": line_chart("Distinct bodies", "Number of different bodies among living agents. One would mean a single clone owns the world.", xs, seeds("distinct_bodies"), ymin=0),
        "top": line_chart("Share of the biggest clone", "Fraction of agents that share the most common body. Near 1 means one body for everyone.", xs, seeds("top_body_share"), ymin=0),
        "diet": stacked_area("What agents have eaten (seed 1)", "Share of living agents by lifetime intake. If the meat band disappears, predation has stopped.", xs,
                             [("plants only", L["diet_plants"], 2), ("mixed", L["diet_mixed"], 3), ("meat only", L["diet_meat"], 1), ("nothing yet", L["diet_none"], 0)]),
        "deaths": line_chart("How agents die (seed 1)", "Deaths per 10,000 steps by cause. Eaten above starved means predation is the main pressure.", xs,
                             [("starved", L["deaths_energy"], 1), ("eaten", L["deaths_eaten"], 0), ("old age", L["deaths_age"], 2)], ymin=0),
        "drift": line_chart("How fast the mean body moves", "Distance between the mean body now and 100,000 steps earlier (blocks). Zero would mean the world has settled.", xs,
                            [(f"Seed {s}", drifts[s], i) for i, s in enumerate(SEEDS)], ymin=0),
        "sps": line_chart("Steps per second", "Simulation speed with three runs sharing one machine. Drops when births, and so developments, are frequent.", xs, seeds("steps_per_sec"), ymin=0),
        "attack": line_chart("Attack and speed (seed 1)", "Population average attack (blocks) and speed (muscle over mass, times 10 for scale).", xs,
                             [("attack", L["attack_mean"], 0), ("speed x10", [v * 10 for v in L["speed_mean"]], 1)], ymin=0),
    }

    # Scatter of bodies at 500k and 1M, seed 1.
    A = agents[1]
    rows = [dict(step=A["step"][i], hard=A["hard"][i], muscle=A["muscle"][i], digestive=A["digestive"][i], sensor=A["sensor"][i], mass=A["mass"][i],
                 attack=A["attack"][i], plant=A["plant"][i], meat=A["meat"][i]) for i in range(len(A["step"]))]
    for r in rows:
        r["diet"] = diet_of(r)
    last_step = int(max(r["step"] for r in rows))
    mid_step = 500000
    scatters = {
        "mid": scatter_chart(f"Bodies at step {mid_step:,} (seed 1)", "Each dot is a living agent: hard blocks against muscle blocks, colored by what it has eaten. Separate clouds are separate kinds of body.",
                             [r for r in rows if r["step"] == mid_step], "hard", "muscle", "hard blocks", "muscle blocks"),
        "end": scatter_chart(f"Bodies at step {last_step:,} (seed 1)", "Same as left, at the end of the run. Different clouds from the left chart mean the types themselves changed.",
                             [r for r in rows if r["step"] == last_step], "hard", "muscle", "hard blocks", "muscle blocks"),
    }

    # Viewer data and top bodies at the end, seed 1.
    bodies = load_bodies(1)
    long_frames, used_l = pack_frames("results/seed1_long.jsonl", every=2)
    clip_frames, used_c = pack_frames("results/seed1_clip.jsonl", limit=200)
    used = used_l | used_c
    last_frame = None
    for fr in read_frames("results/seed1_long.jsonl"):
        last_frame = fr
    top = Counter(b for _, _, b, _ in last_frame["agents"]).most_common(12)
    n_last = len(last_frame["agents"])
    top_html = ""
    for bid, cnt in top:
        at = body_attrs(bodies[bid])
        diets = Counter(d for _, _, b, d in last_frame["agents"] if b == bid)
        dtxt = ", ".join(f"{DIET_NAME[d]} {c}" for d, c in diets.most_common())
        top_html += (f'<div class="cell">{body_svg(bodies[bid], scale=1.6)}<span>{cnt} agents ({cnt/n_last:.0%})</span>'
                     f'<span>mass {at["mass"]}, attack {at["attack"]}, defense {at["defense"]:g}</span><span>{html.escape(dtxt)}</span></div>')
    viewer_data = {"long": long_frames, "clip": clip_frames, "bodies": {str(b): bodies[b] for b in used},
                   "kindColors": {str(k): v for k, v in KIND_COLOR.items()}}

    # Summary table.
    def last(s, key):
        return logs[s][key][-1]

    def dominant(s, step):
        A = agents[s]
        c = Counter(tuple(int(A[k][i]) for k in KINDS) for i in range(len(A["step"])) if A["step"][i] == step)
        return ", ".join(str(v) for v in c.most_common(1)[0][0]) if c else "-"

    def row(label, f):
        return f"<tr><td>{label}</td>" + "".join(f"<td>{f(s)}</td>" for s in SEEDS) + "</tr>"

    summary = ("<thead><tr><th>Measure</th>" + "".join(f"<th>Seed {s}</th>" for s in SEEDS) + "</tr></thead><tbody>"
               + row("Population, min / at 1M", lambda s: f"{min(logs[s]['pop']):.0f} / {last(s, 'pop'):.0f}")
               + row("Steps per second, median", lambda s: f"{sorted(logs[s]['steps_per_sec'])[len(logs[s]['steps_per_sec'])//2]:,.0f}")
               + row("Distinct bodies at 1M", lambda s: f"{last(s, 'distinct_bodies'):.0f}")
               + row("Biggest clone at 1M", lambda s: f"{last(s, 'top_body_share'):.0%}")
               + row("Agents that have eaten meat at 1M", lambda s: f"{last(s, 'diet_mixed') + last(s, 'diet_meat'):.0%}")
               + row("Deaths by predation, last 100k", lambda s: f"{sum(logs[s]['deaths_eaten'][-10:]) / max(1, sum(logs[s]['deaths_eaten'][-10:] + logs[s]['deaths_energy'][-10:] + logs[s]['deaths_age'][-10:])):.0%}")
               + row("Mean body drift, min over run (blocks)", lambda s: f"{min(drifts[s][10:]):.2f}")
               + row("Mean mass at 500k / 1M", lambda s: f"{logs[s]['mass_mean'][49]:.0f} / {last(s, 'mass_mean'):.0f}")
               + row("Dominant body (hard, muscle, sensor, digestive) 500k", lambda s: f"{dominant(s, 500000)}")
               + row("Dominant body 1M", lambda s: f"{dominant(s, 1000000)}")
               + "</tbody>")

    tables = data_table(["step", "pop", "births", "deaths_energy", "deaths_eaten", "deaths_age", "mass_mean", "hard_mean", "muscle_mean", "sensor_mean", "digestive_mean", "attack_mean", "distinct_bodies", "top_body_share", "diet_plants", "diet_mixed", "diet_meat", "steps_per_sec"],
                        {f"Seed {s} (every 100,000 steps)": logs[s] for s in SEEDS}, every=10)

    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>e005 Body World - Report</title>
<style>{CSS}
:root {{ --cell: #f1f0ea; }}
@media (prefers-color-scheme: dark) {{ :root:not([data-theme="light"]) {{ --cell: #262624; }} }}
:root[data-theme="dark"] {{ --cell: #262624; }}
.gallery {{ display: flex; flex-wrap: wrap; gap: 14px; background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 14px; }}
.cell {{ display: flex; flex-direction: column; align-items: center; gap: 2px; font-size: 11px; color: var(--ink2); width: 150px; text-align: center; }}
.body {{ display: block; border-radius: 3px; }}
.legend {{ display: flex; gap: 16px; font-size: 13px; color: var(--ink2); margin: 8px 0 14px; flex-wrap: wrap; }}
.legend i {{ display: inline-block; width: 12px; height: 12px; border-radius: 2px; margin-right: 6px; vertical-align: -1px; }}
.viewer {{ background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 14px; display: grid; grid-template-columns: 1fr; gap: 10px; }}
.viewer .canvases {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10px; align-items: start; }}
.viewer canvas {{ width: 100%; height: auto; image-rendering: pixelated; border-radius: 4px; }}
.viewer .bar {{ display: flex; gap: 10px; align-items: center; font-size: 13px; color: var(--ink2); flex-wrap: wrap; }}
.viewer input[type=range] {{ flex: 1; }}
.viewer button, .viewer select {{ font: inherit; font-size: 13px; padding: 2px 10px; }}
@media (max-width: 700px) {{ .viewer .canvases {{ grid-template-columns: 1fr; }} }}
</style>
</head>
<body>
<main>
<h1>e005: Does shape-derived function plus one predation rule make a food web?</h1>
<p class="sub">Experiment report - 2026-08-29 - three runs of 1,000,000 steps, agents with bodies grown from the genome</p>

<section class="tldr">
<h2>TL;DR</h2>
<p>Yes, a food web of sorts, and no, the world does not settle. In every seed two kinds of body keep appearing: an armored grazer (about 40 hard blocks, no muscle, a gut) that nobody can bite, and an omnivore with teeth and muscle that eats whatever is less armored, mostly newborns. Predation is 26-54% of all deaths, the mean body keeps moving through the whole run, and in one seed a predator body took over the entire population at step 810,000 before diversity came back. Two things fell short: no pure carnivores appeared (meat is 2-4% of all energy eaten), and one seed ended with a single clone at 64%. Getting here took three rules: with teeth alone, one immune body won in 10,000 steps; only when the bite needed muscle behind it did armor, teeth and speed start competing. The run is slow (1,500 steps per second) because every birth develops a body.</p>
</section>

<h2>1. Question</h2>
<p>e004 grows a body from a genome. Here the body decides everything the agent can do, and one rule lets agents eat each other. Nobody is assigned a role: a herbivore is a body with a gut and no teeth, a carnivore is a body with teeth and muscle, an armored body is one nobody can bite. Does a mix of such bodies appear and stay, or does one body win as in e001 and e003? And does the world keep changing?</p>
<ol>
  <li><strong>Survival.</strong> 1,000,000 steps without extinction.</li>
  <li><strong>Differentiation.</strong> Several bodies coexist at the end (no clone above 50%), and agents that eat other agents coexist with agents that eat only plants.</li>
  <li><strong>Ongoing change.</strong> The mean body keeps moving through the whole run, and the dominant body at 1M is not the one at 500k.</li>
  <li><strong>Cost.</strong> Tens of thousands of steps per second.</li>
</ol>

<h2>2. The world</h2>
<p>The grid, food, and life cycle are those of e003. The body is e004's 8x8 grid of blocks. Figure 1 shows how blocks become numbers and how the numbers decide who eats whom. The movement policy is read from the same genome and gets ten inputs: food and other agents in four directions, food here, and its own energy. It is not told whether a neighbor is prey or a threat.</p>
{DIAGRAM}
<p><strong>Getting to this rule took three tries</strong> (100,000 steps each). With attack = hard blocks at the front and nothing else, one body won within 10,000 steps: 48 hard blocks and 16 digestive, the highest possible attack and a defense nobody could beat, all within the 64 cells. Adding escape by speed changed nothing, because nobody had muscle. Requiring muscle behind the bite (attack = min(front hard, muscle)) is what made armor, teeth, and speed compete for the same cells, and the world started moving. The lesson of e003 again: a trait without a two-sided trade-off gets pinned.</p>
<p><strong>Runs.</strong> Three seeds, 1,000,000 steps, 400 random genomes to start. Every 10,000 steps we record:</p>
<ul class="measures">
  <li><strong>Population</strong>, births, deaths by cause (starved, eaten, old age, born without a body), escapes.</li>
  <li><strong>Mean and spread of mass and of each block kind</strong>, attack, speed.</li>
  <li><strong>Distinct bodies</strong> and the share of the biggest clone: how many kinds of body are alive.</li>
  <li><strong>Diet</strong>: share of agents whose lifetime intake is plants only, mixed, meat only.</li>
  <li><strong>Body drift</strong>: distance between the mean body now and 100,000 steps earlier.</li>
  <li><strong>Snapshots</strong> with every agent's body, every 5,000 steps and every step for 400 steps at 600,000.</li>
</ul>

<h2>3. Results</h2>
<div class="tw"><table>{summary}</table></div>
<ol class="verdicts">
<li><span class="verdict">Yes</span> Survival: population 190-540 throughout, 212-249 at the end.</li>
<li><span class="verdict partly">Partly</span> Differentiation: two body types coexist in every seed, and 7-25% of agents at the end have eaten meat. But no pure carnivore exists (at most 0.4% of agents), and seed 2 ends with one clone at 64%.</li>
<li><span class="verdict">Yes</span> Ongoing change: the mean body moves at least 0.4-1.3 blocks per 100,000 steps at every point of the run (median 6-9), and the dominant body at 1M differs from the one at 500k in all seeds.</li>
<li><span class="verdict no">No</span> Cost: median 1,500 steps per second (800-5,700), three runs sharing one machine.</li>
</ol>

<h3>3.1 The world lives, and bodies are heavy</h3>
<div class="grid2">
{charts["pop"]}{charts["mass"]}
</div>
<p>Population sits at 200-300, lower than e003's 700, because bodies are heavy: the mean is 40-64 blocks and the world's food supports fewer of them. Mass swings by 20-40 blocks within a seed as armor is built up and stripped away, which is the first sign that nothing is settled.</p>

<h3>3.2 Two kinds of body, and predation as the main pressure</h3>
<div class="grid2">
{charts["distinct"]}{charts["top"]}
</div>
<div class="grid2">
{charts["diet"]}{charts["deaths"]}
</div>
<p>Tens of distinct bodies are alive at any time, and the biggest clone holds 10-40% most of the time, with brief takeovers. Predation is the main cause of death for half the run in seeds 1 and 2 (54% and 53% of deaths in the last 100,000 steps; 26% in seed 3). Yet meat is only 2-4% of the energy eaten: predators kill a lot and gain little, because what they catch is mostly newborns with little energy. Predation here is a mortality force more than a food source. Nobody lives on meat alone.</p>
<div class="grid2">
{scatters["mid"]}{scatters["end"]}
</div>
{legend()}
<div class="gallery">{top_html}</div>
<p class="sub" style="margin-top:6px">The twelve most common bodies at step 1,000,000, seed 1, with how many agents share each and what those agents have eaten.</p>
<p>The two clouds are the same in every seed. One is the armored grazer: 40-48 hard blocks, no muscle, 15-22 digestive, attack zero, defense 20-24. The other is the omnivore: 22-28 hard blocks, 20-23 muscle, a gut, attack about 21, which beats any body with fewer than 42 hard blocks. The grazers' armor sits right at that line. Neither was designed; both are arrangements of blocks that happen to work against each other. Sensor blocks are never used (population mean below 3), and escapes are 2-7% of encounters: speed is bought for teeth, not for running away.</p>

<h3>3.3 Armor goes up and down; nothing settles</h3>
<div class="grid2">
{charts["kinds"]}{charts["drift"]}
</div>
<div class="grid2">
{charts["attack"]}{charts["sps"]}
</div>
<p>The mean body never stops moving. Hard blocks swing between 8 and 43 in seed 1; in seed 3 a single omnivore body (22 hard, 23 muscle, 3 sensor, 16 digestive) reached 100% of the population at step 810,000 and diversity was back within 100,000 steps. The dominant body at 1,000,000 is not the one at 500,000 in any seed, although it is of the same kind (an armored grazer) in seeds 2 and 3. The cost chart shows why the run is slow: every birth develops a body (0.22 ms), and there are one to three births per step.</p>

<h3>3.4 Watching the world</h3>
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
  <div class="bar">Left: the whole world, each agent drawn as its body. Click anywhere to move the white box. Right: the box at 12x12 cells, blocks visible. Green: food (dark = bare). Seed 1.</div>
</div>
<p>In the long view, agents are drawn as their bodies: blue-heavy tiles are armored grazers, orange-and-blue tiles are omnivores. The clip shows the everyday motion: bodies drift, newborns appear next to parents, and an omnivore next to a lighter neighbor removes it. Click on the world to move the zoom box; the right panel shows the blocks.</p>

<h2>4. Discussion</h2>
<p>The main question has a real answer: derived function plus one rule gives a world with more than one kind of body, where the kinds keep each other in check and keep the world moving. This is the first time in this project that a run did not settle on one strategy. The reason is the arms race: armor at the edge of what the omnivore's bite can beat, the omnivore's attack limited by how much muscle fits next to its teeth.</p><p>The way there is the lesson. With attack from hard blocks alone, the same blocks gave attack and defense, the ceiling was affordable, and one immune body won in 10,000 steps: e001 and e003 all over again. Requiring muscle behind the bite created a trade-off that no cost constant could have created. The size of the costs only scales the population; the shape of the trade-offs decides what evolves.</p><p>What fell short. No pure carnivores: meat is worth too little because prey are mostly newborns, so every predator also grazes. Sensors are useless: the policy inputs about neighbors do not say whether a neighbor is prey or a threat, and running away is rarely worth it when the armored body cannot be eaten anyway. And the run is slow. None of these is a failure of the mechanism; they are the next things to look at.</p>

<h2>5. Conclusion and next step</h2>
<p>Keep everything: e004 bodies, derived function, the one rule with muscle behind the bite, the body viewer. The world has a food web and does not settle, which is what the vision needed before species. Next, e006: sexual reproduction with a compatibility limit, lineage detection, and the event log, on top of this world. Alongside, three smaller things: make development faster (a cheaper sigmoid or a thread per birth) so that the world runs at tens of thousands of steps per second again; see whether meat can be worth more (prey that has grown); and watch whether the gene count, now rising from 6-9 to 14-16 per genome, keeps climbing.</p>

<h2>Appendix: data</h2>
<p>Every 100,000th record; full logs in <code>results/seed*_log.csv</code>, one row per agent every 100,000 steps in <code>results/seed*_agents.csv</code>, snapshots in <code>results/seed*_{{long,clip,bodies}}.jsonl</code>. Build this report with <code>uv run python experiments/e005_body_world/report.py</code>.</p>
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


if __name__ == "__main__":
    main()
