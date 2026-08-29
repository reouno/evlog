#!/usr/bin/env python3
"""Build report.html for this experiment.

Charts: matplotlib, exported as SVG and inlined. Diagram: hand-written SVG.
Run from the repo root: uv run python experiments/e003_genome_world/report.py
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

# Hand-written mechanism diagram.
DIAGRAM = """
<figure class="diagram">
<svg viewBox="0 0 720 250" role="img" aria-label="A genome is decoded once at birth into eight traits and a movement policy; five traits change how the agent eats, moves, senses, splits and ages, each with a cost; three traits do nothing." style="max-width:100%;height:auto;display:block">
<defs><marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="currentColor"/></marker></defs>
<g fill="none" stroke="currentColor" stroke-width="1.2" font-size="12" font-family="system-ui, sans-serif">
  <rect x="20" y="95" width="120" height="58" rx="6"/>
  <text x="80" y="119" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">Genome</text>
  <text x="80" y="137" text-anchor="middle" fill="currentColor" stroke="none" opacity="0.75">512 symbols</text>
  <line x1="140" y1="124" x2="198" y2="124" marker-end="url(#arr)"/>
  <text x="169" y="117" text-anchor="middle" fill="currentColor" stroke="none">decode</text>
  <text x="169" y="140" text-anchor="middle" fill="currentColor" stroke="none" opacity="0.75">at birth</text>
  <rect x="200" y="80" width="150" height="88" rx="6" stroke="var(--s1)" stroke-width="2"/>
  <text x="275" y="104" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">Body</text>
  <text x="275" y="122" text-anchor="middle" fill="currentColor" stroke="none" opacity="0.75">8 traits in 0..1</text>
  <text x="275" y="140" text-anchor="middle" fill="currentColor" stroke="none" opacity="0.75">+ movement policy</text>
  <text x="275" y="158" text-anchor="middle" fill="currentColor" stroke="none" opacity="0.75">(35 weights)</text>
  <!-- trait effects -->
  <g fill="currentColor" stroke="none">
    <text x="440" y="34" font-weight="600">size</text><text x="500" y="34">bigger bite, higher upkeep</text>
    <text x="440" y="58" font-weight="600">speed</text><text x="500" y="58">may jump 2 cells, dearer moves</text>
    <text x="440" y="82" font-weight="600">sense</text><text x="500" y="82">sees 2 cells away, costs upkeep</text>
    <text x="440" y="106" font-weight="600">fertility</text><text x="500" y="106">splits at lower energy</text>
    <text x="440" y="130" font-weight="600">lifespan</text><text x="500" y="130">lives longer, costs upkeep</text>
    <text x="440" y="166" font-weight="600" opacity="0.6">metabolism</text><text x="520" y="166" opacity="0.6">no effect (control)</text>
    <text x="440" y="190" font-weight="600" opacity="0.6">greed</text><text x="520" y="190" opacity="0.6">no effect (control)</text>
    <text x="440" y="214" font-weight="600" opacity="0.6">boldness</text><text x="520" y="214" opacity="0.6">no effect (control)</text>
  </g>
  <line x1="350" y1="100" x2="430" y2="30" marker-end="url(#arr)"/>
  <line x1="350" y1="108" x2="430" y2="54" marker-end="url(#arr)"/>
  <line x1="350" y1="116" x2="430" y2="78" marker-end="url(#arr)"/>
  <line x1="350" y1="124" x2="430" y2="102" marker-end="url(#arr)"/>
  <line x1="350" y1="132" x2="430" y2="126" marker-end="url(#arr)"/>
  <line x1="350" y1="144" x2="430" y2="162" stroke-dasharray="3 3"/>
  <line x1="350" y1="150" x2="430" y2="186" stroke-dasharray="3 3"/>
  <line x1="350" y1="156" x2="430" y2="210" stroke-dasharray="3 3"/>
  <text x="80" y="200" text-anchor="middle" fill="currentColor" stroke="none" opacity="0.75">child = copy + 2 random</text>
  <text x="80" y="216" text-anchor="middle" fill="currentColor" stroke="none" opacity="0.75">symbol changes</text>
  <path d="M275,168 L275,225 L80,225 L80,160" marker-end="url(#arr)" stroke-dasharray="4 3"/>
  <text x="180" y="240" text-anchor="middle" fill="currentColor" stroke="none" opacity="0.75">split: energy halves, child inherits the genome</text>
</g>
</svg>
<figcaption>Figure 1. One genome, decoded once at birth, sets both the body and the behavior. Five traits change what the agent can do and what it pays; three do nothing and serve as a control: if selection moves them, it is dragging them along by accident.</figcaption>
</figure>
"""

TRAITS = ["speed", "metabolism", "sense", "size", "lifespan", "greed", "boldness", "fertility"]
USED = ["speed", "sense", "size", "fertility", "lifespan"]
UNUSED = ["metabolism", "greed", "boldness"]
SEEDS = [1, 2, 3]


def pack_frames(path, every=1, limit=None):
    """Read jsonl frames and pack them small: food as 4-bit nibbles, agents as 4 bytes each, base64."""
    out = []
    with open(os.path.join(HERE, path)) as f:
        for i, line in enumerate(f):
            if i % every:
                continue
            fr = json.loads(line)
            food = fr["food"]
            nib = bytes((food[j] << 4) | food[j + 1] for j in range(0, len(food), 2))
            ag = bytes(v for a in fr["agents"] for v in a)
            out.append({"s": fr["step"], "f": base64.b64encode(nib).decode(), "a": base64.b64encode(ag).decode()})
            if limit and len(out) >= limit:
                break
    return out


VIEWER_JS = r"""
(function(){
  const data = JSON.parse(document.getElementById('frames').textContent);
  const cv = document.getElementById('world'), ctx = cv.getContext('2d');
  const W = 64, H = 64, S = cv.width / W;
  const off = document.createElement('canvas'); off.width = W; off.height = H;
  const octx = off.getContext('2d'), img = octx.createImageData(W, H);
  ctx.imageSmoothingEnabled = false;
  const slider = document.getElementById('scrub'), stepLbl = document.getElementById('steplbl');
  const playBtn = document.getElementById('play'), mode = document.getElementById('mode');
  let frames = data.long, i = 0, timer = null;
  function b64(s){ const b = atob(s); const u = new Uint8Array(b.length); for (let k = 0; k < b.length; k++) u[k] = b.charCodeAt(k); return u; }
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
    for (let k = 0; k < ag.length; k += 4) {
      const x = ag[k], y = ag[k + 1], life = ag[k + 3] / 255;
      ctx.fillStyle = '#eb6834';
      ctx.beginPath(); ctx.arc(x * S + S / 2, y * S + S / 2, 1.5 + 3 * life, 0, 6.28); ctx.fill();
    }
    stepLbl.textContent = 'step ' + fr.s.toLocaleString() + ' - ' + (ag.length / 4) + ' agents';
    slider.value = i;
  }
  function setMode(){ frames = data[mode.value]; i = 0; slider.max = frames.length - 1; draw(); }
  function tick(){ i = (i + 1) % frames.length; draw(); }
  playBtn.onclick = function(){ if (timer) { clearInterval(timer); timer = null; playBtn.textContent = 'Play'; } else { timer = setInterval(tick, mode.value === 'clip' ? 80 : 150); playBtn.textContent = 'Pause'; } };
  slider.oninput = function(){ i = +slider.value; draw(); };
  mode.onchange = function(){ if (timer) playBtn.onclick(); setMode(); };
  setMode();
})();
"""


def main():
    logs = {s: load_csv(f"results/seed{s}_log.csv") for s in SEEDS}
    L = logs[1]
    xs = L["step"]

    def seeds(key):
        return [(f"Seed {s}", logs[s][key], i) for i, s in enumerate(SEEDS)]

    charts = {
        "pop": line_chart("Population", "Living agents. Flat means the world is neither dying out nor exploding.", xs, seeds("pop"), ymin=0),
        "genes": line_chart("Genes per genome", "Average number of genes in living agents. Rising means selection is quietly favoring longer coding regions.", xs, seeds("mean_genes"), ymin=0),
        "used": line_chart("Traits the world uses (seed 1)", "Population average of each trait that has a cost or benefit. Moving away from 0.5 means selection is acting on it.", xs,
                           [(t, L[f"{t}_mean"], i) for i, t in enumerate(USED)], ymin=0),
        "unused": line_chart("Traits the world ignores (seed 1)", "Population average of the three traits with no effect. If selection were clean, these would stay near 0.5.", xs,
                             [(t, L[f"{t}_mean"], i) for i, t in enumerate(UNUSED)], ymin=0),
        "std": line_chart("Spread of the used traits (seed 1)", "Standard deviation across the population. Near zero means everyone has the same value: diversity is gone.", xs,
                          [(t, L[f"{t}_std"], i) for i, t in enumerate(USED)], ymin=0),
        "deaths": line_chart("How agents die (seed 1)", "Deaths per 10,000 steps, by cause. Old age becomes the main cause once agents stop starving.", xs,
                             [("ran out of energy", L["deaths_energy"], 1), ("old age", L["deaths_age"], 0)], ymin=0),
    }
    for c in ("used", "unused", "std"):
        charts[c] = charts[c].replace(">step<", ">step<")

    def trait_table():
        head = "<thead><tr><th>Trait</th><th>Role</th>" + "".join(f"<th>Seed {s}: start &rarr; 1M (std)</th>" for s in SEEDS) + "</tr></thead>"
        rows = []
        for t in USED + UNUSED:
            cells = "".join(f"<td>{logs[s][f'{t}_mean'][0]:.2f} &rarr; <strong>{logs[s][f'{t}_mean'][-1]:.2f}</strong> ({logs[s][f'{t}_std'][-1]:.2f})</td>" for s in SEEDS)
            rows.append(f"<tr><td>{t}</td><td>{'used' if t in USED else 'ignored'}</td>{cells}</tr>")
        return head + "<tbody>" + "".join(rows) + "</tbody>"

    frames = {"long": pack_frames("results/seed1_long.jsonl", every=2), "clip": pack_frames("results/seed1_clip.jsonl", limit=200)}
    tables = data_table(["step", "pop", "mean_genes", "births", "deaths_energy", "deaths_age"] + [f"{t}_mean" for t in TRAITS], {f"Seed {s} (every 100,000 steps)": logs[s] for s in SEEDS}, every=10)

    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>e003 Genome World - Report</title>
<style>{CSS}
.viewer {{ background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 14px; display: grid; grid-template-columns: 1fr; gap: 10px; max-width: 560px; }}
.viewer canvas {{ width: 100%; height: auto; image-rendering: pixelated; border-radius: 4px; }}
.viewer .bar {{ display: flex; gap: 10px; align-items: center; font-size: 13px; color: var(--ink2); }}
.viewer input[type=range] {{ flex: 1; }}
.viewer button, .viewer select {{ font: inherit; font-size: 13px; padding: 2px 10px; }}
</style>
</head>
<body>
<main>
<h1>e003: Can selection climb the genome map when traits have costs?</h1>
<p class="sub">Experiment report - 2026-08-29 - three runs of 1,000,000 steps, agents born from 512-symbol genomes</p>

<section class="tldr">
<h2>TL;DR</h2>
<p>Yes, and quickly: every trait with a cost or a benefit moves the way the costs predict, within 30,000-300,000 steps. Two problems showed up. Four of the five traits ran to the edge of their range and stayed there, because in this world they were pure cost or pure benefit; only lifespan, which has a real trade-off, kept a spread. And two traits the world ignores were dragged far from neutral, because genes touch many traits at once. Lesson: a trait needs a two-sided trade-off or evolution just pins it. Next: sparser genes, and traits with real trade-offs. The report also carries a small viewer of the world; watching works.</p>
</section>

<h2>1. Question</h2>
<p>e001 gave us a world that runs. e002 gave us a genome that produces traits without anyone being able to read it. Here we join them: each agent is born from a genome, and the genome decides how it eats, moves, senses, breeds and ages. Can natural selection find its way through a tangled, indirect map? And can we watch it happen?</p>
<ol>
  <li><strong>Survival.</strong> Genome-born agents last 1,000,000 steps.</li>
  <li><strong>Selection climbs.</strong> Traits with a cost or benefit move away from the random baseline of 0.5, while the three traits the world ignores stay near 0.5.</li>
  <li><strong>Diversity survives.</strong> No used trait collapses onto one value (std above 0.03 at the end).</li>
  <li><strong>Cost.</strong> Decoding at birth keeps the world above 20,000 steps per second.</li>
</ol>

<h2>2. The world</h2>
<p>The grid, food and movement rules are those of e001. What is new is where an agent's numbers come from: a genome decoded once at birth (Figure 1). The decoding is e002's, extended so that the same fixed table also produces the 35 weights of the movement policy. One genome, one map, both body and behavior.</p>
{DIAGRAM}
<p><strong>Runs.</strong> Three seeds, 1,000,000 steps, starting from 300 random genomes. Every 10,000 steps we record:</p>
<ul class="measures">
  <li><strong>Population</strong>, births, deaths by cause (energy, old age).</li>
  <li><strong>Trait means and spreads</strong> across living agents, for all 8 traits.</li>
  <li><strong>Genes per genome</strong> - the e002 bias check.</li>
  <li><strong>Snapshots</strong> - the food grid and every agent's position, every 5,000 steps, plus every step for 400 steps at step 600,000.</li>
</ul>

<h2>3. Results</h2>
<div class="tw"><table>{trait_table()}</table></div>
<ol class="verdicts">
<li><span class="verdict">Yes</span> Survival: population 368-783 throughout, 718-740 at the end.</li>
<li><span class="verdict partly">Partly</span> Selection climbs: used traits move hard and in the predicted direction. But greed and boldness, which do nothing, end at 0.88-0.97 and 0.68-0.81 in two seeds. Only metabolism behaves as a control.</li>
<li><span class="verdict no">No</span> Diversity: speed, sense, size and fertility end with std 0.01-0.05, pinned at an edge. Lifespan keeps 0.07-0.10.</li>
<li><span class="verdict">Yes</span> Cost: 35,000-40,000 steps per second with three runs sharing one machine.</li>
</ol>

<h3>3.1 Selection finds the cheap body fast</h3>
<div class="grid2">
{charts["used"]}{charts["unused"]}
</div>
<p>Speed, sense and size fall to almost zero; fertility rises to almost one. In this world a bigger bite buys nothing (the grid is always bare), a two-cell jump buys nothing, and seeing further buys little, so each of them is just a cost to shed. Fertility is a pure benefit. Lifespan is the only trait that trades a cost against a gain, and it is the only one that settles in the middle. The right chart is the pleiotropy problem from e002 made real: greed and boldness are supposed to do nothing, and they still move by 0.3 or more.</p>

<h3>3.2 Once pinned, diversity is gone</h3>
<div class="grid2">
{charts["std"]}{charts["deaths"]}
</div>
<p>The spread of the four pinned traits collapses within the first 100,000 steps and never recovers. With everyone near the same body, most agents now die of old age rather than hunger: 44% of deaths in seed 1 and 77-78% in seeds 2 and 3 over the last 100,000 steps.</p>

<h3>3.3 The population is stable and the genomes get longer</h3>
<div class="grid2">
{charts["pop"]}{charts["genes"]}
</div>
<p>Population is bounded by food as before, at a higher level than e001 because bodies are cheaper. Gene count climbs from 12 to 17 over the run and is still rising at the end: the "more genes, more extreme traits" bias from e002 is being selected for.</p>

<h3>3.4 Watching the world</h3>
<div class="viewer">
  <canvas id="world" width="512" height="512"></canvas>
  <div class="bar">
    <button id="play">Play</button>
    <select id="mode"><option value="long">Long view: every 10,000 steps</option><option value="clip">Clip: every step from 600,000</option></select>
    <span id="steplbl"></span>
  </div>
  <div class="bar"><input id="scrub" type="range" min="0" max="0" value="0"></div>
  <div class="bar">Green: food (dark = bare). Orange dots: agents, larger = longer lifespan trait. Seed 1.</div>
</div>
<p>The clip shows the actual motion: agents drift across the grid one cell at a time, newborns appear next to their parents (the pairs and small clusters), and food regrows behind them. The long view shows that the world looks the same at 100,000 steps and at 1,000,000. This is the feasibility check for observation: the simulation only writes a log; the viewer replays it. Nothing here is tuned for beauty.</p>

<h2>4. Discussion</h2>
<p>The map is climbable, which was the real question. Selection moved five traits in the predicted directions within a few tens of thousands of steps, through a genome nobody can read. The mechanism holds.</p>
<p>The two failures are about the world, not the genome. First, a trait with only a cost, or only a benefit, is not a trait; it is a knob evolution turns to the stop. Designing a trait means designing the thing that pushes back: size should matter only where food is thick, speed should matter only when something is worth reaching. Second, pleiotropy is doing real damage: traits with no meaning moved as far as traits with meaning. If the ignored traits had meaning too, selection on one would fight selection on another in ways that have nothing to do with the world. A sparse table, where each product touches one to three traits, is the obvious fix and is cheap to test.</p>
<p>The gene-count bias is now confirmed in a living population. It is not harmful yet, but a genome that grows for no reason is a slow leak.</p>

<h2>5. Conclusion and next step</h2>
<p>Keep the genome map, the decode-at-birth design, and the snapshot log. Next: (a) make the table sparse and re-run this world, and check whether the ignored traits stay put; (b) give every trait a two-sided trade-off, which probably means a world where food is not always bare, and check whether the traits settle in the middle and keep their spread. These can be two small experiments or one.</p>

<h2>Appendix: data</h2>
<p>Every 100,000th record; full logs in <code>results/seed*_log.csv</code>, snapshots in <code>results/seed*_{{long,clip}}.jsonl</code>. Build this report with <code>uv run python experiments/e003_genome_world/report.py</code>.</p>
{tables}
</main>
<script id="frames" type="application/json">{json.dumps(frames, separators=(",", ":"))}</script>
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
