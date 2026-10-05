#!/usr/bin/env python3
"""Build report.html for e109 (#128): rung 2 on the small world, the producers' distances in metres.

Charts: matplotlib, exported as SVG and inlined. Diagram: hand-written SVG.
Run from the repo root: uv run python experiments/e109_metres/report.py [results_dir run ...]
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


def rows(name):
    with open(os.path.join(M.RESULTS, name)) as f:
        return list(csv.DictReader(f))


def bar_chart(title, subtitle, labels, series, xlabel="", fmt=None, line=None):
    """series: list of (label, values, slot). One group of bars per label; `line`: a dashed pass line."""
    fig, ax = plt.subplots(figsize=(6.4, 2.6))
    k = len(series)
    width = 0.8 / k
    for i, (name, values, slot) in enumerate(series):
        xs = [j + (i - (k - 1) / 2) * width for j in range(len(labels))]
        ax.bar(xs, values, width=width * 0.92, color=SERIES[slot], label=name)
    if line is not None:
        ax.axhline(line, color=INK, linewidth=1, linestyle="--")
    ax.set_xticks(range(len(labels)), labels)
    ax.set_xlabel(xlabel, loc="right")
    ax.yaxis.set_major_locator(MaxNLocator(4))
    ax.yaxis.set_major_formatter(fmt or kfmt)
    legend_above(ax, k)
    return figure(title, subtitle, to_svg(fig))


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
    fig, ax = plt.subplots(figsize=(6.4, 4.6))
    a = np.ma.masked_array(img, mask=mask) if mask is not None else img
    im = ax.imshow(a, cmap=cmap, norm=norm, interpolation="nearest", origin="lower")
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



# Hand-written mechanism diagram: a seed's distance in metres, against the cell.
DIAGRAM = """
<figure class="diagram">
<svg viewBox="0 0 720 270" role="img" aria-label="A seed falls from its stand's height while the wind carries it; the distance is in metres and a cell is 125 m" style="max-width:100%;height:auto;display:block">
<defs><marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="currentColor"/></marker>
<marker id="arra" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="var(--s1)"/></marker></defs>
<g fill="none" stroke="currentColor" stroke-width="1.4" font-size="12" font-family="system-ui, sans-serif">
  <path d="M30,190 L700,190"/>
  <path d="M40,190 L40,202 M190,190 L190,202 M340,190 L340,202 M490,190 L490,202 M640,190 L640,202"/>
  <text x="115" y="216" text-anchor="middle" fill="currentColor" stroke="none">one cell, 125 m</text>
  <path d="M46,212 L74,212 M156,212 L184,212" stroke-dasharray="2 3"/>
  <path d="M80,190 L80,96"/><circle cx="80" cy="82" r="16"/>
  <text x="104" y="74" fill="currentColor" stroke="none">a stand 30 m high</text>
  <path d="M250,30 L420,30" stroke="var(--s1)" marker-end="url(#arra)"/><text x="250" y="20" fill="var(--s1)" stroke="none">the wind, 5.5 m/s, the day's direction</text>
  <path d="M92,90 C200,100 330,140 388,184" stroke="var(--s1)" marker-end="url(#arra)"/>
  <text x="268" y="106" fill="var(--s1)" stroke="none">30% wing falls at 0.64 m/s: 260 m</text>
  <path d="M86,98 C96,130 102,160 104,184" marker-end="url(#arr)"/>
  <text x="112" y="150" fill="currentColor" stroke="none">bare, 0.01 g: 7.9 m/s, 21 m</text>
  <path d="M560,190 L560,182"/><circle cx="560" cy="178" r="4"/>
  <text x="560" y="150" text-anchor="middle" fill="currentColor" stroke="none">a grass 0.5 m high: 4 m,</text><text x="560" y="166" text-anchor="middle" fill="currentColor" stroke="none">0.1% of its seed over an edge</text>
  <text x="40" y="246" fill="currentColor" stroke="none">river: 2 km a unit of float</text>
  <text x="230" y="246" fill="currentColor" stroke="none">sea: 0.86 km by its mixing</text>
  <text x="425" y="246" fill="currentColor" stroke="none">fire: 2 km of dry fuel</text>
  <text x="580" y="246" fill="currentColor" stroke="none">eater: 300 m + wind</text>
</g>
</svg>
<figcaption>Figure 1. Distances in metres. A seed leaves from anywhere in its cell and lands where its distance takes
it: height x wind / fall speed, each packet in a gust of its own (a few go ten times the mean). What falls near stays
within a stand's height. On the planet the same rules were counted in cells of 63 km.</figcaption>
</figure>
"""

TEXT = {
    "tldr": """Every distance the living cross is now in metres, and producers stand on the islands: 96-98% of the
land, half the sea, 7-8 groups, as on the planet. But a seed goes metres, not cells of 63 km, so the land sown in
year 10 is still sorting itself after 300 years: the leading group follows place at NMI 0.12-0.13 against a line of
0.2, rising throughout. The laws go into <code>base/</code>; whether the islands make places is not settled by this
run.""",
    "question": """On the planet a seed went 20 cells of 63 km and a fire crossed to a neighbour by chance. On the
small world a cell is 125 m. With every distance set from its units, do producers still stand, sort by place and
keep changing - and are the islands' rain, height and light places to them? e104's lines, set before the runs:""",
    "world": """<code>base/</code> on the ground of e108, with five rules rewritten: seed on the wind, seed that
falls near, seed down a river and in the sea, fire, and the small eaters' flight. A cell is only where a thing
lands. No rate was searched.""",
    "runs": """<code>isles1</code> (410 km2 in eight islands), 256 producer and 64 eater genomes sown in every cell
in year 10, run to year 310, two seeds of the living; 3 hours each on Ubuntu. A 40-year pilot changed no rate. Read
as e104, plus the islands' own places; the trend of the sorting was added after the batch.""",
    "v1": "Water, both nutrients and the living's matter close to 6e-12 at worst.",
    "v2": "96% and 98% of the land and 46% and 47% of the sea at the least; biomass drifts under 0.2% a year.",
    "v3": "8.1 and 7.4 groups, but the leading group against place is 0.12 and 0.13 by the planet's bands, 0.09 by the islands' own.",
    "v4": "The leader changes 0 and 1 times; no group founded after year 160 holds 1%. Mutants hold 1.4% and 5.8% of the biomass (planet: 12%).",
    "v5": "Evaporation with transpiration is 198 and 166 mm against the bare ground's 73; the soil's A:B map correlates 0.35 and 0.44.",
    "h31": "3.1 The world stands, and is not yet settled",
    "p31": """The land fills in forty years and holds. The sea's cover falls to 23-25% by year 54, then climbs to 50%.
The groups are still falling at year 310 (17.8 and 27.8 at year 20): the count that matches the planet's is a world
on its way, not at rest.""",
    "h32": "3.2 The land is a mosaic that sorts slowly",
    "p32": """Each cell was sown with two of 256 genomes, and a low stand sends 0.1% of its seed over an edge. So
what grows where is still mostly what was sown there: 166 to 384 genotypes lead cells, in patches that coarsen
(neighbours sharing a leader: 19% to 67%). The leading group follows place a little more every decade, and no
gradient alone. Mutants spread at the same pace.""",
    "h33": "3.3 Stands dry the lee lowlands, and fire lives there",
    "p33": """With stands drawing on it, 7-10% of the soil leaves the full band (bare: 2%), and the planet's bands
count 8-10 places where the bare ground had 4.5. Fire follows the dry ground: 1.4-3.7% of the driest third burns a
year, the wettest third almost never. Transpiration is 115-153 mm of some 2,000 mm of rain; 88-90% still runs off.""",
    "discussion": """<p>The line for places failed, and the plan said a failure means the islands' climate is too
mild. The runs do not show that. They show a world that has not finished: the sorting rises through all 300 years,
the patches coarsen, the groups fall. On the planet a seed crossed 1,260 km in one release, so every form reached
every place within years; here a form reaches its place a few cells a decade.</p>
<p>Do places exist for these producers? Read after the batch: among the twenty leaders that hold over 90% of the
land, the median one has 36-40% of its ground in one of nine places of rain and temperature, and in run 1 the
better of two leaders changes with the place for 24 of 122 pairs (6 of 85 in run 2). That is a yes, and a weak
one.</p>
<p>What this does not show: where the sorting ends. 300 years cannot say whether it passes the line, and the
sowing itself - every genome everywhere at once - made the mosaic. One group leads four of the five large islands
in run 1 and all five in run 2: the sea has not parted the producers.</p>""",
    "conclusion": """Producers stand on the small world with their distances in metres, and those laws go into
<code>base/</code>. They sort and evolve at a seed's pace, far slower than on the planet, and 300 years reads a
transient. The plan's turn to the climate is not taken on this evidence. Before bodies the plan is read again: a
millennium on this ground would say where the sorting ends, and bodies that carry seed are the carrier this world
lacks.""",
}


def main():
    ms = rows("measure.csv")
    ys = rows("years.csv")
    isl = rows("islands.csv")
    f = float
    runs = [m["run"] for m in ms]
    if len(ms) == 1:  # a pilot: one run shown twice
        ms, runs = ms * 2, runs * 2
    m1, m2 = ms
    logs = [list(csv.DictReader(open(os.path.join(M.RESULTS, r + "_log.csv")))) for r in runs]

    # the maps of run 1
    prefix = os.path.join(M.RESULTS, runs[0])
    _, ym, st = M.load_maps(prefix)
    n = int(round(len(st["sea"]) ** 0.5))
    sea = (st["sea"] > 0).reshape(n, n)
    yy, xx = np.nonzero(~sea)
    box = (slice(max(yy.min() - 10, 0), yy.max() + 11), slice(max(xx.min() - 10, 0), xx.max() + 11))
    lyears, lead, none = M.load_lead(prefix)
    cen = [r for r in csv.DictReader(open(prefix + "_census.csv")) if int(r["year"]) == lyears[-1]]
    x, w = vectors(cen)
    g = group(x, w)
    lm = lead[-1].reshape(n, n)
    idg = {int(cen[i]["id"]): int(g[i]) for i in range(len(cen))}
    cells = {}
    for v in lm[~sea]:
        gi = idg.get(int(v))
        if gi is not None:
            cells[gi] = cells.get(gi, 0) + 1
    top = [gi for gi, _ in sorted(cells.items(), key=lambda t: -t[1])[:5]]
    gmap = np.full((n, n), -1.0)
    for (yi, xi) in zip(yy, xx):
        gi = idg.get(int(lm[yi, xi]))
        if gi is not None:
            gmap[yi, xi] = top.index(gi) if gi in top else 5
    names = [f"{f(cen[gi]['h_real']):.1f} m, {f(cen[gi]['t_opt']):.0f} C" for gi in top]
    group_colors = ListedColormap(SERIES + ["#5a5955"])
    mean = {k: v.mean(axis=0).reshape(n, n) for k, v in ym.items()}

    charts = {}
    charts["groups_map"] = map_fig(
        f"Run 1: the leading group on each land cell, year {lyears[-1]}",
        "The five groups leading the most cells (the height they stand at, their temperature optimum); grey: all others.",
        np.ma.masked_array(gmap, mask=gmap < 0)[box], group_colors, norm=BoundaryNorm(np.arange(-0.5, 6.5), 6), ticks=range(6), ticklabels=names + ["others"])
    charts["fill_map"] = map_fig(
        "Run 1: how full the soil stands, the last ten years",
        "The soil's water as a share of what it holds, land only. Bare, 98% of the land stood over two thirds.",
        mean["fill"][box], "YlGnBu", mask=sea[box], label="fill")
    labels = ["planet's", "islands'", "rain", "temp", "light", "A:B", "fertility", "island"]
    keys = ["place", "isles", "rain", "temp", "light", "ab", "fertility", "island"]
    charts["nmi"] = bar_chart(
        "What the leading group follows",
        "NMI of a cell's leading group against the planet's bands, the islands' (rain x temp x light), each alone. Dashed: 0.2.",
        labels, [(RUN_LABELS[i], [f(ms[i][f"nmi_group_{k}"]) for k in keys], i) for i in range(2)], fmt=lambda v, _p: f"{v:g}", line=M.NMI)

    yr = lambda log: [int(r["year"]) for r in log]
    by = [[r for r in ys if r["run"] == run] for run in runs]
    tr = [[r for r in rows("trend.csv") if r["run"] == run] for run in runs]
    charts["trend"] = line_chart(
        "The sorting rises for 300 years and has not arrived",
        "NMI of a land cell's leading group against the planet's bands, every 30 years. The line is 0.2, the top of the chart.",
        [(RUN_LABELS[i], [int(r["year"]) for r in tr[i]], [f(r["nmi_group_place"]) for r in tr[i]], i, False) for i in range(2)], "year",
        fmt=lambda v, _p: f"{v:g}", ymax=0.2)
    charts["groups"] = line_chart(
        "Groups of producers over time",
        "Effective number of producer groups (Hill 1 over biomass). The line is 5.",
        [(RUN_LABELS[i], [int(r["year"]) for r in by[i]], [f(r["groups_hill"]) for r in by[i]], i, False) for i in range(2)], "year",
        fmt=lambda v, _p: f"{v:g}")
    charts["mutants"] = line_chart(
        "Producers born after the sowing",
        "Share of producer biomass held by genotypes born after year 10. On the planet: 12% at year 310 (e104).",
        [(RUN_LABELS[i], [int(r["year"]) for r in by[i]], [f(r["mutant_share"]) for r in by[i]], i, False) for i in range(2)], "year",
        fmt=lambda v, _p: f"{v:.1%}")
    charts["cover"] = line_chart(
        "The land is held; the sea's cover dips and climbs back",
        "Share of cells holding producers: land (solid) and sea (dashed). The lines are 50% and 20%.",
        [(f"{RUN_LABELS[i]}: land", yr(logs[i]), [f(r["land_cover"]) for r in logs[i]], i, False) for i in range(2)]
        + [(f"{RUN_LABELS[i]}: sea", yr(logs[i]), [f(r["sea_cover"]) for r in logs[i]], i, True) for i in range(2)], "year",
        fmt=lambda v, _p: f"{v:.0%}")
    l0 = logs[0]
    charts["water"] = line_chart(
        "Stands draw water, and most rain still runs off",
        "Run 1, mm a year a land cell: what the soil gives the air, what stands transpire, what reaches the sea.",
        [("soil evaporation", yr(l0), [f(r["land_evap"]) for r in l0], 0, False),
         ("transpiration", yr(l0), [f(r["transp"]) for r in l0], 2, False),
         ("to the sea", yr(l0), [f(r["to_sea"]) for r in l0], 1, False)], "year")

    verdict = lambda k: "" if m1[k] == m2[k] == "yes" else (" partly" if "yes" in (m1[k], m2[k]) else " no")
    word = lambda k: "Yes" if m1[k] == m2[k] == "yes" else ("Partly" if "yes" in (m1[k], m2[k]) else "No")
    both = lambda k, fm: f"{fm(f(m1[k]))} / {fm(f(m2[k]))}"
    pct, d1, d2 = (lambda v: f"{v:.0%}"), (lambda v: f"{v:.1f}"), (lambda v: f"{v:.2f}")
    table = [
        ("ledgers, worst year (water, A, matter)", f"{max(f(m1['water_err']), f(m2['water_err'])):.0e}, {max(f(m1['a_err']), f(m2['a_err'])):.0e}, {max(f(m1['c_err']), f(m2['c_err'])):.0e}"),
        ("land held, least of the last 50 years", both("land_cover_min", pct)),
        ("sea held, least of the last 50 years", both("sea_cover_min", pct)),
        ("land biomass, kg a m2 (drift a year)", f"{f(m1['land_biomass']):.2f} ({f(m1['biomass_drift']):+.1%}) / {f(m2['land_biomass']):.2f} ({f(m2['biomass_drift']):+.1%})"),
        ("effective groups, last 50 years", both("groups_hill", d1)),
        ("leading group against the planet's bands (NMI)", both("nmi_group_place", d2)),
        ("leading group against rain x temperature x light (NMI)", both("nmi_group_isles", d2)),
        ("leader's temperature optimum against the cell's temperature (r)", both("corr_topt_temp", d2)),
        ("biomass of genotypes born after sowing", both("producers_mutant", lambda v: f"{v:.1%}")),
        ("soil under 1/3 full / 1/3 to 2/3 (bare: 0.5% / 1.5%)", f"{f(m1['fill_dry']):.0%} / {f(m1['fill_mid']):.0%}, {f(m2['fill_dry']):.0%} / {f(m2['fill_mid']):.0%}"),
        ("places on the land by the planet's bands (bare: 4.5)", both("land_places", d1)),
        ("land burnt a year: driest third / wettest third", f"{f(m1['burnt_dry_third']):.1%} / {f(m1['burnt_wet_third']):.2%}, {f(m2['burnt_dry_third']):.1%} / {f(m2['burnt_wet_third']):.2%}"),
        ("runoff's share of the rain (bare: 96%)", both("runoff_ratio", pct)),
        ("transpiration, mm a year", both("transp_mm", lambda v: f"{v:.0f}")),
        ("the two runs' biomass in groups the other also has", pct(f(m1["replay_matched"])) if "replay_matched" in m1 else "-"),
    ]
    summary = "".join(f"<tr><td>{k}</td><td>{v}</td></tr>" for k, v in table)
    keys_all = list(ms[0])
    appendix = ("<details><summary>Every reading (measure.csv)</summary><div class='tw'><table><thead><tr><th>reading</th>"
                + "".join(f"<th>{r}</th>" for r in RUN_LABELS) + "</tr></thead><tbody>"
                + "".join(f"<tr><td>{k}</td><td>{html.escape(str(m1[k]))}</td><td>{html.escape(str(m2[k]))}</td></tr>" for k in keys_all)
                + "</tbody></table></div></details>")
    isltab = ("<details><summary>The large islands (islands.csv)</summary><div class='tw'><table><thead><tr>"
              + "".join(f"<th>{h}</th>" for h in ["run", "km2", "groups (by cells)", "top group", "its share", "biomass", "height m", "fill", "burnt a year"])
              + "</tr></thead><tbody>"
              + "".join(f"<tr><td>{r['run']}</td><td>{f(r['km2']):.0f}</td><td>{f(r['groups_hill']):.1f}</td><td>{r['top_group']}</td><td>{f(r['top_share']):.0%}</td>"
                        f"<td>{f(r['biomass']):.2f}</td><td>{f(r['height']):.1f}</td><td>{f(r['fill']):.2f}</td><td>{f(r['burnt']):.2%}</td></tr>" for r in isl)
              + "</tbody></table></div></details>")

    T = TEXT
    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>e109 Distances in metres - Report</title>
<style>{CSS}</style>
</head>
<body>
<main>
<h1>e109: producers on the small world, their distances in metres</h1>
<p class="sub">Experiment report - 2026-10-05 - rung 2 again, on the chosen scale (#128): the islands of e108, two runs of 300 years</p>

<section class="tldr">
<h2>TL;DR</h2>
<p>{T.get('tldr', '')}</p>
</section>

<h2>1. Question</h2>
<p>{T.get('question', '')}</p>
<ol>
  <li><strong>The ledgers close</strong> - to 1e-9.</li>
  <li><strong>The world stands</strong> - half the land and a fifth of the sea, the last 50 years.</li>
  <li><strong>Forms hold by place</strong> - 5 effective groups; leading group against place NMI 0.2, by the planet's
  bands and by the islands' own (rain x temperature x light).</li>
  <li><strong>They keep changing</strong> - the leader changes 3 times in 100 years; a group founded after year 160 holds 1%.</li>
  <li><strong>The living change the ground</strong> - evaporation off the bare ground's by 10%; soil A:B map under 0.8.</li>
</ol>

<h2>2. The world</h2>
<p>{T.get('world', '')}</p>
{DIAGRAM}
<p><strong>Runs.</strong> {T.get('runs', '')}</p>
<ul class="measures">
  <li><strong>Group</strong> - genotypes within a fixed distance of a leader in trait space.</li>
  <li><strong>Leading group</strong> - the group of the heaviest genotype in a cell.</li>
  <li><strong>NMI</strong> - how much one label tells of another; 0 none, 1 all.</li>
  <li><strong>Fill</strong> - the soil's water over what it can hold.</li>
</ul>

<h2>3. Results</h2>
<div class="tw"><table><thead><tr><th>reading (run 1 / run 2)</th><th>value</th></tr></thead><tbody>{summary}</tbody></table></div>
<ol class="verdicts">
<li><span class="verdict{verdict('H1')}">{word('H1')}</span> {T.get('v1', '')}</li>
<li><span class="verdict{verdict('H2')}">{word('H2')}</span> {T.get('v2', '')}</li>
<li><span class="verdict{verdict('H3')}">{word('H3')}</span> {T.get('v3', '')}</li>
<li><span class="verdict{verdict('H4')}">{word('H4')}</span> {T.get('v4', '')}</li>
<li><span class="verdict{verdict('H5')}">{word('H5')}</span> {T.get('v5', '')}</li>
</ol>

<h3>{T.get('h31', '3.1')}</h3>
<div class="grid2">
{charts['cover']}
{charts['groups']}
</div>
<p>{T.get('p31', '')}</p>

<h3>{T.get('h32', '3.2')}</h3>
<div class="grid2">
{charts['groups_map']}
{charts['nmi']}
{charts['trend']}
{charts['mutants']}
</div>
<p>{T.get('p32', '')}</p>

<h3>{T.get('h33', '3.3')}</h3>
<div class="grid2">
{charts['fill_map']}
{charts['water']}
</div>
<p>{T.get('p33', '')}</p>

<h2>4. Discussion</h2>
{T.get('discussion', '')}

<h2>5. Conclusion and next step</h2>
<p>{T.get('conclusion', '')}</p>

<h2>Appendix: data</h2>
<p>Readings in <code>results/measure.csv</code>, <code>results/years.csv</code> and <code>results/islands.csv</code>,
thresholds in <code>results/provenance.csv</code>; the trend and the leaders' reading in <code>results/trend.csv</code> and
<code>results/leaders.csv</code> (<code>sorting.py</code>). The censuses live on disk as <code>.zst</code> and the maps are
rebuilt by the runs. Build: <code>uv run python experiments/e109_metres/report.py</code>.</p>
<div class="tw"><table><thead><tr><th>reading</th><th>run</th><th>census years</th><th>thresholds</th></tr></thead><tbody>
{"".join(f"<tr><td>{r['reading']}</td><td>{r['run']}</td><td>{r['census_years']}</td><td style='text-align:left'>{html.escape(r['thresholds'])}</td></tr>" for r in rows("provenance.csv"))}
</tbody></table></div>
{isltab}
{appendix}
</main>
</body>
</html>
"""
    out = os.path.join(HERE, "report.html" if M.RESULTS == os.path.join(HERE, "results") else "report_pilot.html")
    with open(out, "w") as fh:
        fh.write(page)
    words = len(" ".join(str(v) for v in T.values()).split())
    print(f"wrote {out} ({os.path.getsize(out)//1024} KB), {words} words of text")


if __name__ == "__main__":
    main()
