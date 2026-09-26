#!/usr/bin/env python3
"""Build report.html for e103 (#116 rung 2): producers that evolve, and the small eaters.

Charts: matplotlib, exported as SVG and inlined. Diagram: hand-written SVG.
Run from the repo root: uv run python experiments/e103_producers/report.py
"""
import base64
import csv
import html
import io
import os
import sys

import matplotlib
import matplotlib.pyplot as plt
from matplotlib.colors import BoundaryNorm, ListedColormap, LogNorm
from matplotlib.ticker import MaxNLocator
import numpy as np

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


# ---------- page ----------

# A report is dark only (the user, 2026-09-16): one palette, no light branch.
CSS = """
:root {
  color-scheme: dark;
  --surface: #1a1a19; --page: #0d0d0d; --ink: #ffffff; --ink2: #c3c2b7; --grid: #2c2c2a; --border: rgba(255,255,255,0.10);
  --s1: #3987e5;
}
* { box-sizing: border-box; }
body { margin: 0; background: var(--page); color: var(--ink); font: 15px/1.55 system-ui, -apple-system, "Segoe UI", sans-serif; }
main { max-width: 960px; margin: 0 auto; padding: 32px 20px 64px; }
h1 { font-size: 26px; margin: 0 0 4px; }
h2 { font-size: 19px; margin: 40px 0 8px; }
h3 { font-size: 16px; margin: 24px 0 8px; }
p, li { color: var(--ink); max-width: 72ch; }
.sub { color: var(--ink2); margin: 0 0 24px; }
.tldr { background: var(--surface); border: 1px solid var(--border); border-left: 4px solid var(--s1); border-radius: 8px; padding: 12px 18px; }
.tldr h2 { margin: 0 0 6px; font-size: 15px; }
.tldr p { margin: 0; }
.grid2 { display: grid; grid-template-columns: repeat(auto-fit, minmax(420px, 1fr)); gap: 20px; }
.grid2 > .fig:only-child { max-width: 470px; }
.fig { margin: 0; background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 14px 14px 8px; }
.fig svg { width: 100%; height: auto; display: block; font-family: system-ui, -apple-system, "Segoe UI", sans-serif; }
figcaption strong { display: block; font-size: 15px; }
figcaption span { display: block; color: var(--ink2); font-size: 13px; min-height: 2.6em; margin-bottom: 6px; }
.diagram { margin: 12px 0; background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 12px 16px 8px; color: var(--ink); }
.diagram figcaption { color: var(--ink2); font-size: 13px; margin-top: 4px; }
.measures { columns: 2; column-gap: 24px; max-width: none; padding-left: 20px; } .measures li { break-inside: avoid; }
table { border-collapse: collapse; font-size: 13.5px; font-variant-numeric: tabular-nums; }
th, td { padding: 6px 12px; text-align: right; border-bottom: 1px solid var(--grid); }
th:first-child, td:first-child { text-align: left; }
th { color: var(--ink2); font-weight: 600; }
.tw { overflow-x: auto; }
details { margin: 8px 0; } summary { cursor: pointer; color: var(--ink2); }
.verdicts { list-style: none; padding: 0; margin: 12px 0 0; } .verdicts li { margin: 4px 0; }
.verdict { display: inline-block; padding: 1px 8px; border-radius: 4px; font-size: 12.5px; font-weight: 600; background: rgba(12,163,12,0.12); color: #0ca30c; }
.verdict.no { background: rgba(208,59,59,0.12); color: #e66767; }
.verdict.partly { background: rgba(250,178,25,0.15); color: #fab219; }
"""

sys.path.insert(0, HERE)
import measure as M  # noqa: E402  (the reader: same loading, same thresholds)
sys.path.insert(0, os.path.dirname(os.path.dirname(HERE)))
from analysis.groups import group, vectors  # noqa: E402

RUN_LABELS = ["run 1", "run 2"]


def rows(path):
    with open(os.path.join(HERE, path)) as f:
        return list(csv.DictReader(f))


def kfmt(x, _pos):
    return f"{x/1000:g}k" if abs(x) >= 1000 else f"{x:g}"


def to_svg(fig):
    buf = io.StringIO()
    fig.savefig(buf, format="svg", bbox_inches="tight", pad_inches=0.05)
    plt.close(fig)
    return buf.getvalue()


def legend_above(ax, n):
    ax.legend(loc="lower left", bbox_to_anchor=(0, 1.0), ncols=n, handlelength=1.2, borderaxespad=0, columnspacing=1.2)


def figure(title, subtitle, svg):
    return f"""
<figure class="fig">
  <figcaption><strong>{html.escape(title)}</strong><span>{html.escape(subtitle)}</span></figcaption>
  {svg}
</figure>"""


def map_fig(title, subtitle, img, cmap, norm=None, label="", mask=None, ticks=None, ticklabels=None):
    """A world map as a PNG inside the figure (a 512x512 field is too large for SVG)."""
    fig, ax = plt.subplots(figsize=(6.4, 3.4))
    a = np.ma.masked_array(img, mask=mask) if mask is not None else img
    im = ax.imshow(a, cmap=cmap, norm=norm, interpolation="nearest")
    ax.set_xticks([]), ax.set_yticks([])
    ax.grid(False)
    for sp in ax.spines.values():
        sp.set_visible(False)
    cb = fig.colorbar(im, ax=ax, fraction=0.035, pad=0.02, ticks=ticks)
    if ticklabels:
        cb.set_ticklabels(ticklabels)
    cb.set_label(label)
    cb.outline.set_visible(False)
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=110, bbox_inches="tight", pad_inches=0.05, facecolor="#1a1a19")
    plt.close(fig)
    b64 = base64.b64encode(buf.getvalue()).decode()
    return figure(title, subtitle, f'<img src="data:image/png;base64,{b64}" style="width:100%;height:auto;display:block" alt="{html.escape(title)}">')


def line_chart(title, subtitle, series, xlabel, fmt=None, ymax=None):
    """series: (label, xs, ys, slot, dashed)."""
    fig, ax = plt.subplots(figsize=(6.4, 2.6))
    for label, xs, ys, slot, dashed in series:
        ax.plot(xs, ys, color=SERIES[slot], linewidth=1.8, label=label, linestyle="--" if dashed else "-")
    ax.set_xlabel(xlabel, loc="right")
    ax.set_ylim(0, ymax)
    ax.yaxis.set_major_locator(MaxNLocator(4))
    ax.yaxis.set_major_formatter(fmt or kfmt)
    ax.margins(x=0)
    legend_above(ax, len(series))
    return figure(title, subtitle, to_svg(fig))


# Hand-written mechanism diagram: how a genotype reaches the land, and where a mutant stops.
DIAGRAM = """
<figure class="diagram">
<svg viewBox="0 0 720 250" role="img" aria-label="A stand makes seeds, seeds travel to seed banks, a bank's best takes a free slot; stands do not die of age, so slots rarely free" style="max-width:100%;height:auto;display:block">
<defs><marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="currentColor"/></marker>
<marker id="arra" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="var(--s1)"/></marker></defs>
<g fill="none" stroke="currentColor" stroke-width="1.4" font-size="12" font-family="system-ui, sans-serif">
  <rect x="20" y="95" width="170" height="54" rx="6"/><text x="105" y="117" text-anchor="middle" fill="currentColor" stroke="none">stand (cohort)</text><text x="105" y="135" text-anchor="middle" fill="currentColor" stroke="none">leaf, wood, root, store, seed</text>
  <rect x="275" y="20" width="170" height="44" rx="6"/><text x="360" y="47" text-anchor="middle" fill="currentColor" stroke="none">seed release (1 in 500: mutant)</text>
  <rect x="530" y="95" width="170" height="54" rx="6"/><text x="615" y="117" text-anchor="middle" fill="currentColor" stroke="none">seed bank</text><text x="615" y="135" text-anchor="middle" fill="currentColor" stroke="none">4 genotypes a cell</text>
  <rect x="275" y="180" width="170" height="54" rx="6" stroke="var(--s1)"/><text x="360" y="202" text-anchor="middle" fill="var(--s1)" stroke="none">a free slot (4 a cell)</text><text x="360" y="220" text-anchor="middle" fill="var(--s1)" stroke="none">frees only when a stand dies</text>
  <path d="M110,89 C130,50 200,42 269,42" marker-end="url(#arr)"/><text x="130" y="60" text-anchor="end" fill="currentColor" stroke="none">seed share of growth</text>
  <path d="M451,42 C540,42 610,55 615,89" marker-end="url(#arr)"/><text x="560" y="36" fill="currentColor" stroke="none">wind, river, near</text>
  <path d="M615,155 C610,200 520,207 451,207" stroke="var(--s1)" marker-end="url(#arra)"/><text x="600" y="200" fill="var(--s1)" stroke="none">best seeds</text>
  <path d="M269,207 C170,207 110,190 105,155" marker-end="url(#arr)"/><text x="160" y="226" text-anchor="middle" fill="currentColor" stroke="none">new stand</text>
</g>
</svg>
<figcaption>Figure 1. How a genotype takes ground. A stand puts part of its growth into seed; seeds go on the wind,
down the rivers or nearby into seed banks, and the bank's best takes a free slot. A stand's tissue turns over, but
the stand itself never dies of age: a slot frees only after drought, frost, fire, storm or starvation kill it.</figcaption>
</figure>
"""


def main():
    ms = rows("results/measure.csv")
    ys = rows("results/years.csv")
    f = float
    runs = M.RUNS
    logs = [list(csv.DictReader(open(os.path.join(HERE, "results", r + "_log.csv")))) for r in runs]

    # the maps of run 1: leading group, biomass
    prefix = os.path.join(HERE, "results", runs[0])
    _, ym, st = M.load_maps(prefix)
    n = int(round(len(st["sea"]) ** 0.5))
    sea = st["sea"] > 0
    lyears, lead, none = M.load_lead(prefix)
    cen = [r for r in csv.DictReader(open(prefix + "_census.csv")) if int(r["year"]) == lyears[-1]]
    x, w = vectors(cen)
    g = group(x, w)
    gm = {}
    for i, gi in enumerate(g):
        gm[gi] = gm.get(gi, 0.0) + w[i]
    top = [gi for gi, _ in sorted(gm.items(), key=lambda t: -t[1])[:5]]
    code = {int(cen[i]["id"]): (top.index(g[i]) if g[i] in top else 5) for i in range(len(cen))}
    lm = lead[-1]
    gmap = np.array([code.get(int(v), 5) if v != none else -1 for v in lm], dtype=float)
    gmap = np.ma.masked_array(gmap, mask=gmap < 0).reshape(n, n)
    names = []
    for gi in top:
        r = cen[gi]
        where = "sea" if f(r["mass_sea"]) > f(r["mass_land"]) else "land"
        names.append(f"{f(r['h_real']):.1f} m, {where}")
    group_colors = ListedColormap(SERIES + ["#5a5955"])

    charts = {}
    charts["groups_map"] = map_fig(
        "Run 1: the leading group in each cell, year 310",
        "The five largest groups by biomass (height they stand at, where most of it is); grey: all others.",
        gmap, group_colors, norm=BoundaryNorm(np.arange(-0.5, 6.5), 6), ticks=range(6), ticklabels=names + ["others"])
    charts["bio_map"] = map_fig(
        "Run 1: producers' biomass, year 310",
        "kg of dry matter a m2 (log scale), land and sea. Wet warm land holds the most; the dry interiors none.",
        np.maximum(ym["biomass"][-1].reshape(n, n), 1e-4), "viridis", norm=LogNorm(1e-3, 30), label="kg a m2")

    yr = lambda log: [int(r["year"]) for r in log]
    charts["biomass"] = line_chart(
        "The land fills over a century and holds",
        "Producers' biomass, kg a m2 of land. A flat line: the world stands, neither dying nor running away.",
        [(RUN_LABELS[i], yr(logs[i]), [f(r["land_biomass"]) for r in logs[i]], i, False) for i in range(2)], "year",
        fmt=lambda v, _p: f"{v:g}")
    by = [[r for r in ys if r["run"] == run] for run in runs]
    charts["groups"] = line_chart(
        "Groups fall as the founders sort, then hold",
        "Effective number of producer groups (Hill 1 over biomass). The line never rises: no new group arrives.",
        [(RUN_LABELS[i], [int(r["year"]) for r in by[i]], [f(r["groups_hill"]) for r in by[i]], i, False) for i in range(2)], "year",
        fmt=lambda v, _p: f"{v:g}")

    # who evolves: the share of biomass held by genotypes born after the sowing
    mut = []
    for i, run in enumerate(runs):
        es = list(csv.DictReader(open(os.path.join(HERE, "results", run + "_eaters.csv"))))
        tot, new = {}, {}
        for r in es:
            y = int(r["year"])
            tot[y] = tot.get(y, 0.0) + f(r["mass"])
            new[y] = new.get(y, 0.0) + (f(r["mass"]) if int(r["born"]) > 10 else 0.0)
        yy = sorted(tot)
        mut.append((RUN_LABELS[i] + ": eaters", yy, [new[y] / tot[y] for y in yy], i, False))
    for i in range(2):
        mut.append((RUN_LABELS[i] + ": producers", [int(r["year"]) for r in by[i]], [0.0 for _ in by[i]], i, True))
    charts["mutants"] = line_chart(
        "Only the eaters evolve",
        "Share of biomass held by genotypes born after the sowing (year 10). Producers stay at 0 in both runs.",
        mut, "year", fmt=lambda v, _p: f"{v:.0%}", ymax=1.0)

    l0 = logs[0]
    charts["water"] = line_chart(
        "Transpiration replaces the soil's evaporation",
        "Run 1, mm a year a land cell. Total evaporation stays near the bare ground's 1,759 mm; the runoff does not move.",
        [("soil evaporation", yr(l0), [f(r["land_evap"]) for r in l0], 0, False),
         ("transpiration", yr(l0), [f(r["transp"]) for r in l0], 2, False),
         ("to the sea", yr(l0), [f(r["to_sea"]) for r in l0], 1, False)], "year")

    m1, m2 = ms
    verdict = lambda k: "" if m1[k] == m2[k] == "yes" else (" partly" if "yes" in (m1[k], m2[k]) else " no")
    word = lambda k: "Yes" if m1[k] == m2[k] == "yes" else ("Partly" if "yes" in (m1[k], m2[k]) else "No")
    both = lambda k, fm: f"{fm(f(m1[k]))} / {fm(f(m2[k]))}"
    table = [
        ("ledgers, worst year (water, A, matter)", f"{max(f(m1['water_err']), f(m2['water_err'])):.0e}, {max(f(m1['a_err']), f(m2['a_err'])):.0e}, {max(f(m1['c_err']), f(m2['c_err'])):.0e}"),
        ("land held, least of the last 50 years", both("land_cover_min", lambda v: f"{v:.0%}")),
        ("sea held, least of the last 50 years", both("sea_cover_min", lambda v: f"{v:.0%}")),
        ("land biomass, kg a m2 (drift a year)", f"{f(m1['land_biomass']):.2f} ({f(m1['biomass_drift']):+.1%}) / {f(m2['land_biomass']):.2f} ({f(m2['biomass_drift']):+.1%})"),
        ("effective groups, last 50 years", both("groups_hill", lambda v: f"{v:.1f}")),
        ("the largest group's share", both("top_group_share", lambda v: f"{v:.0%}")),
        ("leading group against place (NMI)", both("nmi_group_place", lambda v: f"{v:.2f}")),
        ("changes of the leading genotype, last 100 years", f"{m1['leader_changes']} / {m2['leader_changes']}"),
        ("biomass of genotypes born after sowing", both("producers_mutant", lambda v: f"{v:.0%}")),
        ("eaters' biomass born after sowing", both("eaters_mutant", lambda v: f"{v:.0%}")),
        ("land evaporation against bare ground", both("et_change", lambda v: f"{v:+.1%}")),
        ("soil A:B map against e102's (correlation)", both("ab_corr_e102", lambda v: f"{v:.2f}")),
        ("a compound's distance to the nearest eater key, bits", both("key_distance", lambda v: f"{v:.1f}")),
        ("the two runs' biomass in groups the other also has", f"{f(m1['replay_matched']):.0%}"),
    ]
    summary = "".join(f"<tr><td>{k}</td><td>{v}</td></tr>" for k, v in table)
    keys = list(ms[0])
    appendix = ("<details><summary>Every reading (measure.csv)</summary><div class='tw'><table><thead><tr><th>reading</th>"
                + "".join(f"<th>{r}</th>" for r in RUN_LABELS) + "</tr></thead><tbody>"
                + "".join(f"<tr><td>{k}</td><td>{html.escape(str(m1[k]))}</td><td>{html.escape(str(m2[k]))}</td></tr>" for k in keys)
                + "</tbody></table></div></details>")

    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>e103 Evolving producers - Report</title>
<style>{CSS}</style>
</head>
<body>
<main>
<h1>e103: producers that evolve, and the small eaters</h1>
<p class="sub">Experiment report - 2026-09-26 - the redesign's second rung (#116): 256 random producer genomes on
e102's ground, two runs of 300 years</p>

<section class="tldr">
<h2>TL;DR</h2>
<p>Producers with a genome, tissue chemistry, seeds, fire and leaf-eaters were sown on the ground of rung 1. The world
stands for 300 years and the founders sort by place (3.3 and 5.5 groups). But the producers never evolve: in both runs
no genotype born after the sowing holds any biomass, because a stand never dies of age and a mutant never finds a
free slot. The eaters, which do turn over, evolve and follow the producers' keys. Next: generations inside a stand.</p>
</section>

<h2>1. Question</h2>
<p>Do many producer forms arise, hold by place and keep changing, while the world stands? If producers alone do not
diversify over this ground, the redesign's premise fails early. Five lines, set before the runs:</p>
<ol>
  <li><strong>The ledgers close</strong> - water, A, B and the living's matter, to 1e-9.</li>
  <li><strong>The world stands</strong> - half the land and a fifth of the sea held, biomass steady.</li>
  <li><strong>Forms hold by place</strong> - 5 effective groups, group against place NMI 0.2.</li>
  <li><strong>They keep changing</strong> - the leader changes 3 times in 100 years; a late group holds 1%.</li>
  <li><strong>The living change the ground</strong> - evaporation by 10%, the soil's A:B map.</li>
</ol>

<h2>2. The world</h2>
<p>A producer is a stand of one genotype a cell (up to 4 a cell). Genes of 16 bases set each organ's A and B, the
height, roots, seeds, a defence compound and its key, and plastic responses; small eaters carry detox keys.</p>
{DIAGRAM}
<p><strong>Runs.</strong> c1225, sown in year 10, run to year 310, two seeds of the living; about 1.8 hours each on
5 threads. Measured:</p>
<ul class="measures">
  <li><strong>Groups</strong> - genotypes grouped by 21 scaled traits (fixed cut), Hill number over biomass.</li>
  <li><strong>NMI</strong> - how much a cell's leading group says about its place (0 none, 1 all).</li>
  <li><strong>Born after sowing</strong> - biomass of genotypes made by mutation.</li>
  <li><strong>Key distance</strong> - bits between a compound and the nearest eater key.</li>
</ul>

<h2>3. Results</h2>
<div class="tw"><table><thead><tr><th>reading (run 1 / run 2)</th><th>value</th></tr></thead><tbody>{summary}</tbody></table></div>
<ol class="verdicts">
<li><span class="verdict{verdict('H1')}">{word('H1')}</span> The ledgers close to 7e-12 at worst.</li>
<li><span class="verdict{verdict('H2')}">{word('H2')}</span> 90% of the land and 35-41% of the sea held; biomass drifts under 0.2% a year.</li>
<li><span class="verdict{verdict('H3')}">{word('H3')}</span> Groups hold by place (NMI 0.27 in both), but run 1 has 3.3 groups, one holding 71%.</li>
<li><span class="verdict{verdict('H4')}">{word('H4')}</span> The leading genotype never changes; mutants hold 0% of the biomass.</li>
<li><span class="verdict{verdict('H5')}">{word('H5')}</span> The soil's A:B map is remade (correlation 0.31-0.35), but total evaporation moves 1.5-3%.</li>
</ol>

<h3>3.1 The world stands and sorts its founders by place</h3>
<div class="grid2">
{charts['biomass']}
{charts['groups']}
{charts['groups_map']}
{charts['bio_map']}
</div>
<p>Of 256 founders, 115-121 remain at year 310. The land fills in about a century and then holds; the groups fall
from 16-35 in the first year to 4.3 by year 100 as the founders sort, and each keeps to its region.</p>

<h3>3.2 Only the eaters evolve</h3>
<div class="grid2">
{charts['mutants']}
</div>
<p>About 116,000 producer mutants were made in each run, and all stayed in seed banks or died as seedlings. Eaters
move and replace each other in a cell every season, and 93-96% of their biomass is new genotypes. Their keys come
within 1 bit of the producers' compounds, or, in run 2, they carry none and eat the 68% of biomass that is undefended.</p>

<h3>3.3 The living remake the soil, not the water</h3>
<div class="grid2">
{charts['water']}
</div>
<p>Half of the land's evaporation now passes through leaves, but the shade takes as much from the soil's own, and the
runoff stays at 10%. The soil's chemistry is the producers' now: its A:B map correlates only 0.31-0.35 with the bare ground's.</p>

<h2>4. Discussion</h2>
<p>The failure is one law, not the premise. A stand here is immortal: its tissue turns over but the stand never dies of
age, so a slot frees only after a disaster, and the parent's own seeds, nine times the mutant's share, win it back. A
real stand is a population whose plants die and are replaced by seedlings every generation, which is how a mutant
or an immigrant enters. The eaters show the same machinery works when turnover exists.</p>
<p>What held without evolution is worth keeping: a world that stands for 300 years, forms that keep to places,
soils made by the living, eaters that track keys. The two runs share 26% of their biomass in matching groups:
which founders win is already contingent.</p>

<h2>5. Conclusion and next step</h2>
<p>The world stands, but rung 2's question is not yet answered: producers sort, they do not evolve. Next (e104):
generations inside a stand - plants die at a lifespan the genome sets, paid for in tissue, and the cell's seed bank
recruits into the space - on the same world, judged by the same five lines.</p>

<h2>Appendix: data</h2>
<p>Readings in <code>results/measure.csv</code> and <code>results/years.csv</code>, thresholds in
<code>results/provenance.csv</code>, genotypes in <code>results/*_census.csv</code> and <code>*_eaters.csv</code>. The
maps (<code>*_maps.bin</code>, <code>*_lead.bin</code>) are rebuilt by the runs. Build:
<code>uv run python experiments/e103_producers/report.py</code>.</p>
{appendix}
</main>
</body>
</html>
"""
    out = os.path.join(HERE, "report.html")
    with open(out, "w") as fh:
        fh.write(page)
    text = " ".join(page.split("<h2>TL;DR</h2>")[1].split("<h2>Appendix")[0].split())
    import re
    words = len(re.sub(r"<[^>]+>|\{[^}]*\}", " ", text.split("<figure")[0] + "".join(t.split("</figure>")[-1] for t in text.split("<figure")[1:])).split())
    print(f"wrote {out} ({os.path.getsize(out)//1024} KB), about {words} words of text")


if __name__ == "__main__":
    main()
