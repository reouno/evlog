#!/usr/bin/env python3
"""Build report.html for this experiment.

Charts: matplotlib, exported as SVG and inlined. Diagram: hand-written SVG.
Run from the repo root: uv run python experiments/e002_genome_map/report.py
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
:root[data-theme="dark"] .verdict {{ color: #0ca30c; }} :root[data-theme="dark"] .verdict.no {{ color: #e66767; }}
@media (prefers-color-scheme: dark) {{ :root:not([data-theme="light"]) .verdict {{ color: #0ca30c; }} :root:not([data-theme="light"]) .verdict.no {{ color: #e66767; }} }}
"""

# Hand-written mechanism diagram.
DIAGRAM = """
<figure class="diagram">
<svg viewBox="0 0 720 250" role="img" aria-label="How a genome becomes traits: a promoter marks genes, each gene has a tag and a product, products bind matching tags and raise or lower expression, and the settled levels are read into eight traits through a fixed table." style="max-width:100%;height:auto;display:block">
<defs><marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="currentColor"/></marker></defs>
<g fill="none" stroke="currentColor" stroke-width="1.2" font-size="12" font-family="system-ui, sans-serif">
  <!-- genome string -->
  <text x="20" y="34" fill="currentColor" stroke="none" font-weight="600">Genome: 512 symbols from {0,1,2,3}</text>
  <text x="20" y="58" fill="currentColor" stroke="none" font-family="ui-monospace, Menlo, monospace" font-size="13" letter-spacing="1">3 1 2 <tspan fill="var(--s1)" font-weight="700">0 1 0</tspan> 2 2 0 1 3 3 1 2 <tspan fill="var(--s1)" font-weight="700">0 1 0</tspan> 1 0 3 ...</text>
  <path d="M60,64 L60,74 L131,74 L131,64" /><text x="96" y="90" text-anchor="middle" fill="currentColor" stroke="none">promoter = "here starts a gene"</text>
  <!-- one gene -->
  <text x="400" y="34" fill="currentColor" stroke="none" font-weight="600">One gene = 8 symbols after a promoter</text>
  <rect x="400" y="44" width="100" height="26" rx="4"/><text x="450" y="61" text-anchor="middle" fill="currentColor" stroke="none">tag (4)</text>
  <rect x="500" y="44" width="100" height="26" rx="4"/><text x="550" y="61" text-anchor="middle" fill="currentColor" stroke="none">product (4)</text>
  <text x="400" y="90" fill="currentColor" stroke="none" opacity="0.75">a product that matches a tag in 3 or 4 places binds it</text>
  <!-- network -->
  <text x="20" y="118" fill="currentColor" stroke="none" font-weight="600">Genes act on each other</text>
  <circle cx="60" cy="180" r="14"/><text x="60" y="184" text-anchor="middle" fill="currentColor" stroke="none">A</text>
  <circle cx="140" cy="160" r="14"/><text x="140" y="164" text-anchor="middle" fill="currentColor" stroke="none">B</text>
  <circle cx="140" cy="215" r="14"/><text x="140" y="219" text-anchor="middle" fill="currentColor" stroke="none">C</text>
  <circle cx="220" cy="185" r="14"/><text x="220" y="189" text-anchor="middle" fill="currentColor" stroke="none">D</text>
  <line x1="74" y1="176" x2="125" y2="164" marker-end="url(#arr)"/>
  <line x1="74" y1="185" x2="125" y2="210" marker-end="url(#arr)" stroke-dasharray="3 3"/>
  <line x1="154" y1="164" x2="205" y2="181" marker-end="url(#arr)"/>
  <path d="M154,220 C185,232 215,220 226,200" marker-end="url(#arr)" stroke-dasharray="3 3"/>
  <path d="M130,148 C118,128 162,128 149,148" marker-end="url(#arr)"/>
  <text x="20" y="243" fill="currentColor" stroke="none" opacity="0.75">solid = raises, dashed = lowers; 40 rounds until levels settle</text>
  <!-- levels -> traits -->
  <line x1="250" y1="185" x2="318" y2="185" marker-end="url(#arr)"/>
  <text x="284" y="178" text-anchor="middle" fill="currentColor" stroke="none">levels</text>
  <rect x="320" y="150" width="170" height="70" rx="6" stroke="var(--s1)" stroke-width="2"/>
  <text x="405" y="176" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">Fixed table</text>
  <text x="405" y="194" text-anchor="middle" fill="currentColor" stroke="none" opacity="0.75">product pattern -> 8 weights</text>
  <text x="405" y="210" text-anchor="middle" fill="currentColor" stroke="none" opacity="0.75">same for every genome</text>
  <line x1="490" y1="185" x2="558" y2="185" marker-end="url(#arr)"/>
  <text x="524" y="178" text-anchor="middle" fill="currentColor" stroke="none">sum</text>
  <rect x="560" y="150" width="140" height="70" rx="6"/>
  <text x="630" y="176" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">8 traits in 0..1</text>
  <text x="630" y="194" text-anchor="middle" fill="currentColor" stroke="none" opacity="0.75">speed, metabolism,</text>
  <text x="630" y="210" text-anchor="middle" fill="currentColor" stroke="none" opacity="0.75">sense, size, lifespan, ...</text>
</g>
</svg>
<figcaption>Figure 1. From string to traits. The genome decides which genes exist and how they push each other; the fixed table (the "laws of physics", not part of the genome) decides what settled gene levels mean. Nothing in the string says "speed" directly.</figcaption>
</figure>
"""

TRAITS = ["speed", "metabolism", "sense", "size", "lifespan", "greed", "boldness", "fertility"]
SEEDS = [1, 2, 3]


def main():
    rnd = {s: load_csv(f"results/seed{s}_random.csv") for s in SEEDS}
    mut = {s: load_csv(f"results/seed{s}_mutation.csv") for s in SEEDS}
    pairs = {s: load_csv(f"results/seed{s}_pairs.csv") for s in SEEDS}
    r, m, p = rnd[1], mut[1], pairs[1]

    pooled = [v for t in TRAITS for v in r[t]]
    nonneutral = [d for d in m["dist"] if d >= 1e-6]
    neutral_share = 1 - len(nonneutral) / len(m["dist"])
    moved = [sum(1 for t in TRAITS if m[f"d_{t}"][i] > 0.01) for i in range(len(m["dist"])) if m["dist"][i] >= 1e-6]

    # extremity vs gene count
    by_genes = {}
    for i, n in enumerate(r["n_genes"]):
        by_genes.setdefault(int(n), []).extend(abs(r[t][i] - 0.5) for t in TRAITS)
    gcounts = sorted(g for g, vals in by_genes.items() if len(vals) >= 50 * len(TRAITS))
    extremity = [sum(by_genes[g]) / len(by_genes[g]) for g in gcounts]

    charts = [
        hist_chart("Trait values", "All 8 traits of 5,000 random genomes, pooled. A spike would mean a trait is stuck; a flat spread across 0..1 would mean no structure.",
                   [("trait value", pooled, 0)], bins=40, xlabel="trait value"),
        hist_chart("Genes per genome", "How many genes a random 512-symbol string contains. Zero means the genome produces nothing.",
                   [("genomes", r["n_genes"], 0)], bins=range(0, 22), xlabel="genes"),
        hist_chart("Effect of one mutation vs. distance between strangers",
                   f"Trait distance after changing one symbol (only the {1-neutral_share:.0%} that changed anything; the other {neutral_share:.0%} moved nothing), compared with the distance between two random genomes.",
                   [("one mutation", nonneutral, 1), ("two random genomes", p["dist"], 0)], bins=40, xlabel="trait distance", density=True),
        hist_chart("How many traits one mutation touches", "Of the 8 traits, how many moved by more than 0.01 after a non-neutral mutation. 1 would mean genes map to single traits.",
                   [("mutations", moved, 1)], bins=range(0, 10), xlabel="traits moved"),
        line_chart("More genes, more extreme traits", "Average distance of traits from the middle (0.5), by number of genes in the genome. Flat would mean gene count does not matter.",
                   gcounts, [("mean |trait - 0.5|", extremity, 2)], ymin=0),
    ]
    # x axis for the last chart is gene count, not steps
    charts[4] = charts[4].replace(">step<", ">genes<")

    def summary_rows():
        rows = []
        for s in SEEDS:
            rr, mm, pp = rnd[s], mut[s], pairs[s]
            nn = sorted(d for d in mm["dist"] if d >= 1e-6)
            neutral = 1 - len(nn) / len(mm["dist"])
            med_pair = sorted(pp["dist"])[len(pp["dist"]) // 2]
            decode = sum(rr["decode_ns"]) / len(rr["decode_ns"]) / 1000
            genes = sum(rr["n_genes"]) / len(rr["n_genes"])
            rows.append(f"<tr><td>{s}</td><td>{genes:.1f}</td><td>{neutral:.0%}</td><td>{nn[len(nn)//2]:.2f} / {nn[round((len(nn)-1)*0.9)]:.2f} / {nn[-1]:.2f}</td><td>{med_pair:.2f}</td><td>{decode:.1f}</td></tr>")
        return "".join(rows)

    tables = data_table(["id", "n_genes", "n_edges", "decode_ns"] + TRAITS, {"Seed 1: random genomes (every 250th)": r}, every=250)
    tables += data_table(["id", "n_genes_before", "n_genes_after", "dist"], {"Seed 1: one-mutation trials (every 100th)": m}, every=100)

    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>e002 Genome Map - Report</title>
<style>{CSS}</style>
</head>
<body>
<main>
<h1>e002: Can a DNA-like string produce traits that vary, evolve in small steps, and cannot be read by hand?</h1>
<p class="sub">Experiment report - 2026-08-29 - 5,000 random genomes and 2,000 single mutations, three seeds, no world</p>

<section class="tldr">
<h2>TL;DR</h2>
<p>Yes. A 512-symbol string decoded through a small gene network gives eight traits that are spread out, not stuck, and not readable from the string. One-symbol changes do nothing 83% of the time, make a small change most of the rest of the time, and occasionally a big one. Decoding costs 4 microseconds. This becomes the base for individuals.
Two things to watch later: almost every gene touches almost every trait, and genomes with more genes get more extreme traits. Next: put this into the world with trade-offs between traits.</p>
</section>

<h2>1. Question</h2>
<p>We want every individual to be born from a genome: a long string over four symbols, so that the space of possible genomes cannot be explored by trying. The hard part is not the string, it is the map from string to traits. If position 1 means speed and position 2 means size, anyone can read it and the world is boring. Biology is not readable because its map is indirect: genes act on each other, one gene touches several traits, and the result comes out of a process. We test one cheap way to get those properties, on its own, with no world around it.</p>
<ol>
  <li><strong>Variety.</strong> Random genomes give varied traits: nothing stuck at one value, no collapse onto a few points.</li>
  <li><strong>Small steps, rare jumps, neutrality.</strong> Changing one symbol usually does nothing or a little, and sometimes a lot. Evolution needs all three: neutral changes to drift on, small ones to climb with, big ones to escape with.</li>
  <li><strong>Cost.</strong> Decoding a genome takes under 100 microseconds.</li>
</ol>

<h2>2. The map</h2>
<p>Figure 1 shows the whole mechanism. A genome is 512 symbols. A fixed 3-symbol pattern marks where a gene starts; the next 8 symbols are the gene, split into a tag and a product. Products that look like another gene's tag bind it and push its level up or down. After 40 rounds the levels settle, and a fixed table turns "which products are present, at what level" into eight numbers between 0 and 1. The table is the same for every genome; it is part of the world's laws, not of the individual.</p>
{DIAGRAM}
<p>The traits have names (speed, metabolism, ...) but in this experiment they are just numbers. What they do to an individual, and what they cost, is the next experiment's job. Changes during life (learning, aging, health) are a separate layer on top of these birth traits and are not part of the map.</p>
<p><strong>Runs.</strong> Three seeds; each seed draws its own fixed table, so agreement across seeds means the result does not depend on one lucky table. Per seed:</p>
<ul class="measures">
  <li><strong>5,000 random genomes</strong> - traits, gene count, decode time.</li>
  <li><strong>2,000 single mutations</strong> - change one symbol of a genome, measure how far the 8 traits moved (straight-line distance).</li>
  <li><strong>2,000 random pairs</strong> - distance between two unrelated genomes, as the yardstick for "a lot".</li>
  <li><strong>Neutral</strong> - a mutation that moved the traits by exactly nothing.</li>
</ul>

<h2>3. Results</h2>
<div class="tw"><table>
<thead><tr><th>Seed</th><th>Genes per genome</th><th>Neutral mutations</th><th>Non-neutral effect median / p90 / max</th><th>Distance between strangers (median)</th><th>Decode (us)</th></tr></thead>
<tbody>{summary_rows()}</tbody></table></div>
<ol class="verdicts">
<li><span class="verdict">Yes</span> Variety: every trait spans about 0.08-0.97 with a spread (std) of 0.11; strangers differ by 0.41 on average.</li>
<li><span class="verdict">Yes</span> Small steps, rare jumps, neutrality: 83% of mutations do nothing; the typical non-neutral step is a quarter of the distance between strangers; the largest reach that distance.</li>
<li><span class="verdict">Yes</span> Cost: 3.7 microseconds per decode, 25 times under the limit.</li>
</ol>

<h3>3.1 Traits are spread out and the string is not empty</h3>
<div class="grid2">
{charts[0]}{charts[1]}
</div>
<p>Traits cluster around the middle and thin out toward the edges, so the map has structure without being stuck. A random string carries about 8 genes; only 1 in 5,000 carries none.</p>

<h3>3.2 One symbol usually does little, sometimes a lot</h3>
<div class="grid2">
{charts[2]}{charts[3]}
</div>
<p>The mutation curve sits well to the left of the stranger curve but overlaps its lower end: most steps are small, a few are as large as swapping the whole genome. That is the shape evolution can climb. The right chart is the caveat: a mutation that does anything moves 6 of the 8 traits on average. Genes are not specialists.</p>

<h3>3.3 Bigger genomes, bolder traits</h3>
<div class="grid2">
{charts[4]}
</div>
<p>Traits drift further from the middle as the gene count rises. In a world that rewards any extreme trait, this will quietly reward having more genes.</p>

<h2>4. Discussion</h2>
<p>The map does what we asked: it is cheap, it is varied, and it has the step-size profile evolution needs. Nothing in it is designed to produce a particular trait, which is the point; you can write a genome, but you cannot predict what it makes without running it.</p>
<p>Two properties were not asked for and may bite later. First, pleiotropy is near total: because each product carries weights for all eight traits, selecting for one trait drags the others along. If adaptation in the world stalls for this reason, the fix is a sparse table (each product touches one to three traits). Second, trait extremity scales with gene count, so selection will favor longer coding regions. Neither is wrong, and neither should be tuned before the world shows whether it matters.</p>
<p>Traits sit mostly between 0.3 and 0.7. Whether that range is wide enough depends on what the world does with a trait, which this experiment did not test.</p>

<h2>5. Conclusion and next step</h2>
<p>Keep this map as the base for individuals: promoter, tag + product, binding by match, settle, read through a fixed table. Next, put it into the world from e001: give the traits meaning and costs (fast means hungry, sharp senses cost energy), and see whether selection finds its way through the map and whether individuals become worth watching one by one.</p>

<h2>Appendix: data</h2>
<p>Every row is in <code>results/seed*_{{random,mutation,pairs}}.csv</code>; summaries in <code>results/seed*_summary.txt</code>. Build this report with <code>uv run python experiments/e002_genome_map/report.py</code>.</p>
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
