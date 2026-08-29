#!/usr/bin/env python3
"""Build report.html for this experiment.

Charts: matplotlib, exported as SVG and inlined. Diagram: hand-written SVG.
Run from the repo root: uv run python experiments/e004_genome_shape/report.py
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

import json

KIND_COLOR = {1: SERIES[0], 2: SERIES[1], 3: SERIES[3], 4: SERIES[2]}  # hard blue, muscle orange, sensor yellow, digestive aqua
KIND_NAME = {1: "hard", 2: "muscle", 3: "sensor", 4: "digestive"}
SEEDS = [1, 2, 3]

# Hand-written mechanism diagram.
DIAGRAM = """
<figure class="diagram">
<svg viewBox="0 0 720 260" role="img" aria-label="For each of the 64 cells, the genome's gene network is run with the cell's position fed in as six morphogen signals; the settled expression is read through a fixed table into five scores, and the highest decides the cell's content." style="max-width:100%;height:auto;display:block">
<defs><marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="currentColor"/></marker></defs>
<g fill="none" stroke="currentColor" stroke-width="1.2" font-size="12" font-family="system-ui, sans-serif">
  <rect x="20" y="110" width="120" height="58" rx="6"/>
  <text x="80" y="134" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">Genome</text>
  <text x="80" y="152" text-anchor="middle" fill="currentColor" stroke="none" opacity="0.75">512 symbols</text>
  <line x1="140" y1="139" x2="228" y2="139" marker-end="url(#arr)"/>
  <text x="184" y="132" text-anchor="middle" fill="currentColor" stroke="none">genes</text>

  <rect x="230" y="96" width="170" height="86" rx="6"/>
  <text x="315" y="120" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">Gene network (e002)</text>
  <text x="315" y="138" text-anchor="middle" fill="currentColor" stroke="none" opacity="0.75">products bind tags,</text>
  <text x="315" y="154" text-anchor="middle" fill="currentColor" stroke="none" opacity="0.75">levels settle in 40 steps</text>
  <text x="315" y="172" text-anchor="middle" fill="currentColor" stroke="none" opacity="0.75">(~8 genes)</text>

  <rect x="230" y="14" width="170" height="44" rx="6" stroke="var(--s1)" stroke-width="2"/>
  <text x="315" y="32" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">Position of the cell</text>
  <text x="315" y="49" text-anchor="middle" fill="currentColor" stroke="none" opacity="0.75">x, 1-x, y, 1-y, r, 1-r in [-1, 1]</text>
  <line x1="315" y1="58" x2="315" y2="94" marker-end="url(#arr)" stroke="var(--s1)" stroke-width="2"/>
  <text x="325" y="80" fill="currentColor" stroke="none">6 morphogens bind tags too</text>

  <line x1="400" y1="139" x2="488" y2="139" marker-end="url(#arr)"/>
  <text x="444" y="132" text-anchor="middle" fill="currentColor" stroke="none">levels</text>

  <rect x="490" y="96" width="210" height="86" rx="6"/>
  <text x="595" y="120" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">Fixed table, 5 scores</text>
  <text x="595" y="138" text-anchor="middle" fill="currentColor" stroke="none" opacity="0.75">empty, hard, muscle,</text>
  <text x="595" y="154" text-anchor="middle" fill="currentColor" stroke="none" opacity="0.75">sensor, digestive</text>
  <text x="595" y="172" text-anchor="middle" fill="currentColor" stroke="none" opacity="0.75">highest wins; ties go to empty</text>

  <path d="M595,182 L595,222 L315,222 L315,184" marker-end="url(#arr)" stroke-dasharray="4 3"/>
  <text x="455" y="240" text-anchor="middle" fill="currentColor" stroke="none" opacity="0.75">one cell decided; repeat for all 64 cells of the 8x8 grid</text>
</g>
</svg>
<figcaption>Figure 1. Development of one body. The genome and its gene network are those of e002. What is new is the blue box: six position signals act on the genes like extra products, so a gene can be on at one side of the body and off at the other. The same fixed table and the same six morphogen patterns are used for every genome; they are the laws, not the genome.</figcaption>
</figure>
"""


# ---------- bodies ----------

def body_svg(cells, size=6, title=None):
    """One 8x8 body as inline SVG. cells: 64-char string of kind digits."""
    n = 8
    w = n * size
    parts = [f'<svg viewBox="0 0 {w} {w}" width="{w*1.5}" height="{w*1.5}" class="body"' + (f' aria-label="{html.escape(title)}"' if title else "") + ">"]
    parts.append(f'<rect x="0" y="0" width="{w}" height="{w}" fill="var(--cell)"/>')
    for i, ch in enumerate(cells):
        k = int(ch)
        if k == 0:
            continue
        x, y = (i % n) * size, (i // n) * size
        parts.append(f'<rect x="{x+0.3}" y="{y+0.3}" width="{size-0.6}" height="{size-0.6}" fill="{KIND_COLOR[k]}"/>')
    parts.append("</svg>")
    return "".join(parts)


def gallery(bodies, cls="gallery", labels=None):
    items = []
    for i, b in enumerate(bodies):
        lab = f'<span>{html.escape(labels[i])}</span>' if labels else ""
        items.append(f'<div class="cell">{body_svg(b)}{lab}</div>')
    return f'<div class="{cls}">{"".join(items)}</div>'


def legend():
    sw = "".join(f'<span><i style="background:{KIND_COLOR[k]}"></i>{KIND_NAME[k]}</span>' for k in (1, 2, 3, 4))
    return f'<div class="legend">{sw}<span><i style="background:var(--cell);border:1px solid var(--grid)"></i>empty</span></div>'


def bar_chart(title, subtitle, categories, series, xlabel):
    """Grouped bars. series: list of (label, values, slot)."""
    fig, ax = new_axes(xlabel)
    ax.margins(x=0.05)
    n = len(series)
    width = 0.8 / n
    for j, (label, values, slot) in enumerate(series):
        xs = [i + (j - (n - 1) / 2) * width for i in range(len(categories))]
        ax.bar(xs, values, width=width * 0.95, color=SERIES[slot], label=label)
    ax.set_xticks(range(len(categories)), categories)
    ax.xaxis.set_major_formatter(lambda x, _p: categories[int(x)] if 0 <= int(x) < len(categories) else "")
    ax.yaxis.set_major_locator(MaxNLocator(4))
    ax.yaxis.set_major_formatter(lambda y, _p: f"{y:.0%}")
    legend_above(ax, n)
    return figure(title, subtitle, to_svg(fig))


def main():
    rnd = {s: load_csv(f"results/seed{s}_random.csv") for s in SEEDS}
    mut = {s: load_csv(f"results/seed{s}_mutation.csv") for s in SEEDS}
    pairs = {s: load_csv(f"results/seed{s}_pairs.csv") for s in SEEDS}
    with open(os.path.join(HERE, "results/seed1_bodies.json")) as f:
        bodies = json.load(f)

    def pct(vals, pred):
        return sum(1 for v in vals if pred(v)) / len(vals)

    def kinds_present(r, i):
        return sum(1 for k in ("hard", "muscle", "sensor", "digestive") if r[k][i] > 0)

    def uniform(r, i):
        return r["n_blocks"][i] == 0 or max(r[k][i] for k in ("hard", "muscle", "sensor", "digestive")) == 64

    stats = {}
    for s in SEEDS:
        r = rnd[s]
        n = len(r["id"])
        d1 = mut[s]["dist1"]
        nz = [d for d in d1 if d > 0]
        dp = sorted(pairs[s]["dist"])
        stats[s] = dict(
            dev_us=sum(r["dev_ns"]) / n / 1000,
            uniform=sum(uniform(r, i) for i in range(n)) / n,
            empty=pct(r["n_blocks"], lambda v: v == 0),
            full=pct(r["n_blocks"], lambda v: v == 64),
            connected=pct(r["connected"], lambda v: v == 1),
            med_blocks=sorted(r["n_blocks"])[n // 2],
            neutral=pct(d1, lambda v: v == 0),
            mut_med=sorted(nz)[len(nz) // 2],
            mut_p90=sorted(nz)[int(len(nz) * 0.9)],
            pair_med=dp[len(dp) // 2],
        )

    # Kinds present per body, by seed.
    cats = ["0 (empty)", "1", "2", "3", "4"]
    kinds_series = []
    for i, s in enumerate(SEEDS):
        r = rnd[s]
        counts = [0] * 5
        for j in range(len(r["id"])):
            counts[kinds_present(r, j)] += 1
        kinds_series.append((f"Seed {s}", [c / len(r["id"]) for c in counts], i))

    # Shaped bodies as a function of morphogen edges (seed 1), bucketed by 2.
    r = rnd[1]
    buckets = {}
    for j in range(len(r["id"])):
        b = min(int(r["morph_edges"][j]), 16) // 2 * 2
        buckets.setdefault(b, [0, 0])
        buckets[b][0] += 1
        buckets[b][1] += not uniform(r, j)
    bx = sorted(buckets)
    by = [buckets[b][1] / buckets[b][0] for b in bx]

    charts = {
        "blocks": hist_chart("Blocks per body", "How many of the 64 cells hold a block, over 5,000 random genomes. A spike at 64 means most bodies fill the grid.",
                             [(f"Seed {s}", rnd[s]["n_blocks"], i) for i, s in enumerate(SEEDS)], bins=range(0, 66, 2), xlabel="blocks", density=True),
        "kinds": bar_chart("Kinds of block per body", "Share of random bodies that contain 0, 1, 2, 3 or all 4 kinds. All at 1 would mean bodies are single-material blobs.",
                           cats, kinds_series, "kinds present"),
        "dist": hist_chart("How far a body moves", "Cells that differ (0-64) after one mutation, after two, and between two random bodies. Seed 1, zero-distance cases left out.",
                           [("one mutation", [d for d in mut[1]["dist1"] if d > 0], 0), ("two mutations", [d for d in mut[1]["dist2"] if d > 0], 1), ("random pair", pairs[1]["dist"], 2)],
                           bins=range(0, 66, 2), xlabel="cells that differ", density=True),
        "morph": line_chart("Position has to reach the genes", "Share of bodies that are not uniform, against how many gene-morphogen bindings the genome has. Seed 1. Flat would mean position does not matter.",
                            bx, [("shaped bodies", by, 0)], ymin=0),
    }
    charts["morph"] = charts["morph"].replace(">step<", ">morphogen bindings<")

    def row(label, f):
        return f"<tr><td>{label}</td>" + "".join(f"<td>{f(stats[s])}</td>" for s in SEEDS) + "</tr>"

    summary = ("<thead><tr><th>Measure</th>" + "".join(f"<th>Seed {s}</th>" for s in SEEDS) + "</tr></thead><tbody>"
               + row("Development time per body", lambda t: f"{t['dev_us']:.0f} us")
               + row("Uniform bodies (same thing in every cell)", lambda t: f"{t['uniform']:.0%}")
               + row("Empty bodies", lambda t: f"{t['empty']:.1%}")
               + row("Full bodies (no empty cell)", lambda t: f"{t['full']:.0%}")
               + row("Connected bodies", lambda t: f"{t['connected']:.0%}")
               + row("Median blocks per body", lambda t: f"{t['med_blocks']:.0f} / 64")
               + row("One mutation: no change", lambda t: f"{t['neutral']:.0%}")
               + row("One mutation: cells changed, when it changes (median / p90)", lambda t: f"{t['mut_med']:.0f} / {t['mut_p90']:.0f}")
               + row("Two random bodies: cells that differ (median)", lambda t: f"{t['pair_med']:.0f}")
               + "</tbody>")

    fam_html = ""
    for fam in bodies["families"]:
        fam_html += f'<div class="family"><div class="cell parent">{body_svg(fam["parent"])}<span>parent #{fam["id"]}</span></div><div class="arrow">&rarr;</div>{gallery(fam["children"], cls="kids")}</div>'

    walk = bodies["walk"]
    walk_html = gallery(walk, cls="gallery walk", labels=[("parent" if i == 0 else f"+{i}") for i in range(len(walk))])

    tables = data_table(["id", "n_genes", "morph_edges", "n_blocks", "hard", "muscle", "sensor", "digestive", "largest", "connected", "dev_ns"],
                        {f"Seed {s}: random bodies (every 250th)": rnd[s] for s in SEEDS}, every=250)
    tables += data_table(["id", "n_blocks_before", "n_blocks_after", "dist1", "dist2"], {f"Seed {s}: mutations (every 100th)": mut[s] for s in SEEDS}, every=100)

    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>e004 Genome Shape - Report</title>
<style>{CSS}
:root {{ --cell: #f1f0ea; }}
@media (prefers-color-scheme: dark) {{ :root:not([data-theme="light"]) {{ --cell: #262624; }} }}
:root[data-theme="dark"] {{ --cell: #262624; }}
.gallery {{ display: flex; flex-wrap: wrap; gap: 10px; background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 14px; }}
.cell {{ display: flex; flex-direction: column; align-items: center; gap: 2px; font-size: 11px; color: var(--ink2); }}
.body {{ display: block; border-radius: 3px; }}
.legend {{ display: flex; gap: 16px; font-size: 13px; color: var(--ink2); margin: 8px 0 14px; }}
.legend i {{ display: inline-block; width: 12px; height: 12px; border-radius: 2px; margin-right: 6px; vertical-align: -1px; }}
.family {{ display: flex; align-items: center; gap: 12px; background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 12px 14px; margin: 10px 0; flex-wrap: wrap; }}
.family .kids {{ display: flex; flex-wrap: wrap; gap: 10px; }}
.family .arrow {{ font-size: 22px; color: var(--ink2); }}
.walk .cell span {{ font-variant-numeric: tabular-nums; }}
</style>
</head>
<body>
<main>
<h1>e004: Can the gene network grow a body on a grid?</h1>
<p class="sub">Experiment report - 2026-08-29 - 5,000 random genomes and 2,000 mutations per seed, three seeds, no world</p>

<section class="tldr">
<h2>TL;DR</h2>
<p>Yes. Feed each cell's position into the e002 gene network as six morphogen signals, read the settled expression through a fixed table, and bodies come out: patches and stripes of four block kinds, almost always in one connected piece, 3,800 different shapes among 5,000 random genomes, 0.2 ms each. A child looks like its parent: 83% of point mutations change nothing, and the rest move a region of about 13 cells, a quarter of the distance between two random bodies. Two things to carry forward: random bodies are dense (half of them fill the grid), and mutations move regions, not single blocks. Next: give the blocks meaning in the world (e005) and let upkeep decide how big bodies should be.</p>
</section>

<h2>1. Question</h2>
<p>The vision says shapes should come from development, so that a limb or a fang is an arrangement of blocks that happens to work, not a part in a list. e002 gave us a gene network that turns a genome into numbers. Can the same network, run once per cell with the cell's position as input, turn a genome into a shape? Four hypotheses:</p>
<ol>
  <li><strong>Variety.</strong> Random genomes give varied, mostly connected bodies: not all empty, not all full, no collapse onto a few shapes.</li>
  <li><strong>Small steps.</strong> One point mutation usually changes the body a little (a few blocks), sometimes a lot, often not at all.</li>
  <li><strong>Heritability.</strong> The body distance after one mutation is much smaller than the distance between two random bodies.</li>
  <li><strong>Cost.</strong> Developing one body takes under 1 ms.</li>
</ol>

<h2>2. The mechanism</h2>
<p>A body is an 8x8 grid. Each cell holds nothing or one block of four kinds: hard, muscle, sensor, digestive. To decide a cell, we run the genome's gene network with six extra inputs that say where the cell is (left-right, top-bottom, center-edge, each in both directions), wait for the expression levels to settle, and read the levels through a fixed table into five scores. The highest score wins the cell (Figure 1). The table and the six morphogen patterns are drawn once per seed and shared by every genome: they are laws of the world, not part of any individual.</p>
{DIAGRAM}
<p>One rule needed a decision. If the position signals are in [0, 1] and bind genes as strictly as gene products do, 72% of genomes never notice where a cell is and grow the same thing everywhere. Stretching the signals to [-1, 1] (a signal that activates a gene on one side and represses it on the other) and letting morphogens bind on 2 matching symbols instead of 3 brings that down to 22%. Both are structural choices rather than tuned numbers, and the gene network itself is unchanged from e002.</p>
<p><strong>Runs.</strong> Three seeds. For each: 5,000 random genomes, one point mutation on 2,000 of them, 2,000 random pairs. We record:</p>
<ul class="measures">
  <li><strong>Blocks per body</strong> and the share of empty, full and uniform bodies. Uniform = the same thing in every cell: position never reached the output.</li>
  <li><strong>Kinds present</strong> per body, and the share of cells by kind.</li>
  <li><strong>Connected</strong> - all blocks in one 4-neighbor piece.</li>
  <li><strong>Distinct bodies</strong> among 5,000 - a low count would mean collapse.</li>
  <li><strong>Body distance</strong> - number of the 64 cells that differ, after one mutation, after two, and between random bodies.</li>
  <li><strong>Development time</strong> per body.</li>
</ul>

<h2>3. Results</h2>
<div class="tw"><table>{summary}</table></div>
<ol class="verdicts">
<li><span class="verdict partly">Partly</span> Variety: 3,800-3,900 distinct bodies, 78-80% shaped, 94-97% of those connected. But the typical body is dense: median 62-64 blocks, and half of all bodies have no empty cell.</li>
<li><span class="verdict partly">Partly</span> Small steps: 83-84% of mutations change nothing, and the rest are small next to a random pair. But the typical change is a region of 12-13 cells, not a few blocks; single-block edits (1-8 cells) are 6% of mutations.</li>
<li><span class="verdict">Yes</span> Heritability: median 13 cells after a non-neutral mutation vs 56-57 between random bodies.</li>
<li><span class="verdict">Yes</span> Cost: 216-220 us per body.</li>
</ol>

<h3>3.1 Random genomes grow shaped bodies, but dense ones</h3>
{legend()}
{gallery(bodies["random"])}
<p class="sub" style="margin-top:6px">The first 40 random genomes of seed 1, in order, nothing picked by hand.</p>
<div class="grid2">
{charts["blocks"]}{charts["kinds"]}
</div>
<p>Patches, stripes and gradients appear because a gene bound to a morphogen is on in one part of the grid and off in another, and each gene drags the five scores in its own direction. Two out of three bodies use more than one kind. The density comes from the read-out: one empty column competes against four block columns, so a block wins most cells. Whether that is a problem is a question for the world, where every block will cost upkeep.</p>
<div class="grid2">
{charts["morph"]}
</div>
<p>Shape needs position to reach the genes. Genomes with few morphogen bindings are mostly uniform; with a dozen or more, four in five are shaped. This is why the morphogen rule mattered so much.</p>

<h3>3.2 A child looks like its parent; a mutation moves a region or nothing</h3>
{fam_html}
<p class="sub" style="margin-top:6px">Four parents from seed 1 (the first with 8-56 blocks and at least one morphogen binding), each with seven children carrying one random point mutation.</p>
{walk_html}
<p class="sub" style="margin-top:6px">One lineage: the first parent above, then 32 successive single mutations, each body drawn after its mutation.</p>
<div class="grid2">
{charts["dist"]}
</div>
<p>Most children are copies. When a mutation does act, it changes a gene's expression, and expression is shared by all the cells where that gene is on, so the change is a region: an outline shifts, a patch changes kind, or in 2-3% of cases the whole body flips. The lineage shows the same in time: long stretches of nothing, then a step. This is what development gives, and it is different from a body that is edited block by block.</p>

<h2>4. Discussion</h2>
<p>The main question is answered: the e002 network, unchanged, grows shapes when it is told where it is. Nothing here names a limb, and yet bodies have outlines, sides, and patches of different material. That is the foundation mechanism 1 of the vision asked for.</p>
<p>The surprise was how much the way position enters matters. The gene network on its own is blind to position; with a timid morphogen rule three quarters of genomes grow blobs. The chosen rule (two-sided signals, broad binding) is part of the laws now and should be recorded as such.</p>
<p>Two findings are neither good nor bad yet. Bodies are dense by default. In e005 every block will cost upkeep, so selection will push toward smaller bodies; the question is whether the genome can find them, and p10 of 9-26 blocks says small bodies exist. Mutations act on regions. That is good for exploring outlines and bad for fine-tuning a single block; whether a small feature like a fang can be kept under mutation is something to watch, not something to fix in advance.</p>
<p>What this does not show: anything about function. Whether a hard block at the front bites, whether muscle over mass gives speed, whether these shapes are worth having, all of that is e005.</p>

<h2>5. Conclusion and next step</h2>
<p>Keep the mechanism: e002 network, six position morphogens in [-1, 1] binding on 2 of 4, fixed table read-out with the highest score winning. Development costs 0.2 ms, cheap enough to run at every birth. Next, e005: derive mass, speed, attack, defense and diet from the blocks, put the bodies in the world with upkeep per block and the one predation rule, and see whether a food web appears and whether the shapes keep changing.</p>

<h2>Appendix: data</h2>
<p>Every 250th random body and every 100th mutation; full rows in <code>results/seed*_{{random,mutation,pairs}}.csv</code>, the gallery in <code>results/seed*_bodies.json</code>, summaries in <code>results/seed*_summary.txt</code>. Build this report with <code>uv run python experiments/e004_genome_shape/report.py</code>.</p>
{tables}
</main>
</body>
</html>
"""
    out = os.path.join(HERE, "report.html")
    with open(out, "w") as f:
        f.write(page)
    print(f"wrote {out} ({os.path.getsize(out)//1024} KB)")


if __name__ == "__main__":
    main()
