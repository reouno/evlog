#!/usr/bin/env python3
"""Build report.html for this experiment.

Charts: matplotlib, exported as SVG and inlined. Diagram: hand-written SVG.
Run from the repo root: uv run python experiments/eNNN_name/report.py
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
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#898781"]  # fixed slot order; the last is the donor world, in chrome gray

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

# ---------- data ----------

RESULTS = os.path.join(HERE, "results")
UNITS = [0, 4.7, 9.4, 28]
SEEDS = [9, 10, 11]

def rows_of(path):
    with open(path) as f:
        return list(csv.DictReader(f))


def sweep(name):
    return {r["run"]: r for r in rows_of(os.path.join(RESULTS, f"sweep_{name}.csv"))}


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
.grid2 + .grid2 { margin-top: 20px; }
.fig { margin: 0; background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 14px 14px 8px; }
.fig svg { width: 100%; height: auto; display: block; font-family: system-ui, -apple-system, "Segoe UI", sans-serif; }
figcaption strong { display: block; font-size: 15px; }
figcaption span { display: block; color: var(--ink2); font-size: 13px; min-height: 2.6em; margin-bottom: 6px; }
.diagram { margin: 12px 0; background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 12px 16px 8px; color: var(--ink); }
.diagram figcaption { color: var(--ink2); font-size: 13px; margin-top: 4px; }
.cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 16px; }
.card { margin: 0; display: flex; gap: 12px; align-items: flex-start; }
.card figcaption { font-size: 12px; color: var(--ink2); }
.card figcaption strong { color: var(--ink); font-size: 12.5px; display: inline; }
.measures { columns: 2; column-gap: 24px; max-width: none; padding-left: 20px; } .measures li { break-inside: avoid; }
table { border-collapse: collapse; font-size: 13.5px; font-variant-numeric: tabular-nums; }
th, td { padding: 6px 10px; text-align: right; border-bottom: 1px solid var(--grid); }
th:first-child, td:first-child { text-align: left; }
td { white-space: nowrap; }
th { color: var(--ink2); font-weight: 600; }
.tw { overflow-x: auto; }
details { margin: 8px 0; } summary { cursor: pointer; color: var(--ink2); }
.verdicts { list-style: none; padding: 0; margin: 12px 0 0; } .verdicts li { margin: 4px 0; }
.verdict { display: inline-block; padding: 1px 8px; border-radius: 4px; font-size: 12.5px; font-weight: 600; background: rgba(12,163,12,0.12); color: #0ca30c; }
.verdict.no { background: rgba(208,59,59,0.12); color: #e66767; }
.verdict.partly { background: rgba(250,178,25,0.15); color: #fab219; }
"""



def line_x(title, subtitle, xs, series, xlabel, ylabel=None, pct=False, band=None, markers=False):
    """series: list of (label, ys, slot)."""
    fig, ax = new_axes(xlabel)
    if band:
        ax.axhspan(band[0], band[1], color=INK, alpha=0.12, linewidth=0)
    for label, ys, slot in series:
        ax.plot(xs, ys, color=SERIES[slot], linewidth=1.6, label=label, marker="o" if markers else None, markersize=3.5)
    if ylabel:
        ax.set_ylabel(ylabel)
    ax.yaxis.set_major_formatter((lambda y, _p: f"{y:.0%}") if pct else kfmt)
    ax.yaxis.set_major_locator(MaxNLocator(4))
    ax.margins(x=0.02)
    ax.set_xticks(xs, [f"{x:g}" for x in xs])  # the runs' own values, not a scale between them
    legend_above(ax, len(series))
    return figure(title, subtitle, to_svg(fig))





DIAGRAM = """
<figure class="diagram">
<svg viewBox="0 0 780 260" role="img" aria-label="The body's water as part of the land's water" style="max-width:100%;height:auto;display:block">
<defs><marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="currentColor"/></marker></defs>
<g fill="none" stroke="currentColor" stroke-width="1.2" font-size="12" font-family="system-ui, sans-serif">
  <rect x="300" y="10" width="180" height="56" rx="6"/>
  <text x="390" y="33" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">the air over the cell</text>
  <text x="390" y="52" text-anchor="middle" fill="currentColor" stroke="none">wind carries it, it rains</text>
  <rect x="20" y="170" width="220" height="70" rx="6"/>
  <text x="130" y="194" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">the ground and pools</text>
  <text x="130" y="213" text-anchor="middle" fill="currentColor" stroke="none">150 mm full; a pool over 500</text>
  <text x="130" y="230" text-anchor="middle" fill="currentColor" stroke="none">wet ground gives 1/20 of a pool</text>
  <rect x="540" y="170" width="220" height="70" rx="6"/>
  <text x="650" y="194" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">a body's water</text>
  <text x="650" y="213" text-anchor="middle" fill="currentColor" stroke="none">a block holds 9.4 mm of its cell</text>
  <text x="650" y="230" text-anchor="middle" fill="currentColor" stroke="none">(a sub-cell of full ground)</text>
  <line x1="240" y1="190" x2="540" y2="190" stroke="var(--s1)" marker-end="url(#arr)"/>
  <text x="390" y="180" text-anchor="middle" fill="var(--s1)" stroke="none">W1: drink, only up to full</text>
  <line x1="540" y1="222" x2="240" y2="222" marker-end="url(#arr)"/>
  <text x="390" y="240" text-anchor="middle" fill="currentColor" stroke="none">W2: the dead, lost blocks; a child takes it back</text>
  <line x1="640" y1="170" x2="470" y2="66" marker-end="url(#arr)"/>
  <text x="600" y="110" text-anchor="start" fill="currentColor" stroke="none">W2: dry air, sweat</text>
  <line x1="310" y1="66" x2="140" y2="170" marker-end="url(#arr)"/>
  <text x="180" y="110" text-anchor="end" fill="currentColor" stroke="none">rain</text>
</g>
</svg>
<figcaption>Figure 1. Before this step a body's water came from nowhere and went nowhere. Now what a body
drinks leaves its cell's ground (blue), and what it loses goes to the air or back into the ground, so the
air's, the land's and the bodies' water is conserved together.</figcaption>
</figure>
"""


def main():
    se, la = sweep("search"), sweep("ladder")
    v = lambda d, run, c: float(d[run][c])  # noqa: E731
    s_run = lambda u: f"life9_u{u:g}"  # noqa: E731
    l_run = lambda s, u: f"life{s}_u{u:g}"  # noqa: E731
    charts1 = [
        line_x("A stand's bodies go dry",
               "Mean water of land bodies in mid stands, by season (seed 9). Flat = the crowd pays nothing for its water.",
               UNITS, [(n, [v(se, s_run(u), f"water_stand_{n}") for u in UNITS], k) for k, n in enumerate(["spring", "summer", "autumn", "winter"])],
               "unit (mm of a cell a block of water is)", "water", markers=True),
        line_x("The crowd moves water from the stands to the lawn",
               "The ground's fill in mid stands and on the mid lawn in winter and spring (seed 9). At 0, the producers alone.",
               UNITS, [("stand, winter", [v(se, s_run(u), "fill_stand_winter") for u in UNITS], 3), ("stand, spring", [v(se, s_run(u), "fill_stand_spring") for u in UNITS], 0),
                       ("lawn, winter", [v(se, s_run(u), "fill_lawn_winter") for u in UNITS], 4), ("lawn, spring", [v(se, s_run(u), "fill_lawn_spring") for u in UNITS], 2)],
               "unit (mm of a cell a block of water is)", "ground fill", markers=True),
    ]
    charts2 = [
        line_x("The lawn gains in spring, not in autumn",
               "Bodies a mid lawn cell over a mid stand cell (seeds 9-11). Rising = the lawn takes a larger share of the crowd.",
               SEEDS, [("spring, control", [v(la, l_run(s, 0), "lawn_spring_share") for s in SEEDS], 5), ("spring, 9.4", [v(la, l_run(s, 9.4), "lawn_spring_share") for s in SEEDS], 2),
                       ("autumn, control", [v(la, l_run(s, 0), "lawn_autumn_share") for s in SEEDS], 3), ("autumn, 9.4", [v(la, l_run(s, 9.4), "lawn_autumn_share") for s in SEEDS], 1)],
               "seed", "lawn / stand", markers=True),
        line_x("Bodies end nearer where they were born",
               "Median cells between a grown body's birth place and where it stands, at the censuses (seeds 9-11).",
               SEEDS, [("control", [float(la[l_run(s, 0)]["travel"]) for s in SEEDS], 5), ("unit 9.4", [float(la[l_run(s, 9.4)]["travel"]) for s in SEEDS], 0)],
               "seed", "cells", markers=True),
    ]
    charts3 = [
        line_x("Fewer kinds in every seed",
               "Kinds at a census and kinds kept to a place (e068's census by birth form), censuses 36,000-100,000.",
               SEEDS, [("kinds, control", [v(la, l_run(s, 0), "kinds_at") for s in SEEDS], 5), ("kinds, 9.4", [v(la, l_run(s, 9.4), "kinds_at") for s in SEEDS], 0),
                       ("placed, control", [v(la, l_run(s, 0), "placed_at") for s in SEEDS], 3), ("placed, 9.4", [v(la, l_run(s, 9.4), "placed_at") for s in SEEDS], 1)],
               "seed", "kinds", markers=True),
    ]
    runs = [(f"seed {s}, {'control' if u == 0 else 'unit 9.4'}", la[l_run(s, u)]) for s in SEEDS for u in (0, 9.4)]
    cells = lambda r: (f"<td>{float(r['pop_land']):,.0f}</td><td>{float(r['d_thirst']):.0%}</td><td>{float(r['home']):.2f}</td>"  # noqa: E731
                       f"<td>{float(r['lawn_spring_share']):.2f}</td><td>{float(r['lawn_autumn_share']):.2f}</td><td>{float(r['water_stand_spring']):.2f}</td>"
                       f"<td>{float(r['fill_stand_winter']):.2f}</td><td>{float(r['fill_lawn_winter']):.2f}</td><td>{float(r['top_share']):.0%}</td>"
                       f"<td>{float(r['kinds_at']):.2f}</td><td>{float(r['placed_at']):.2f}</td><td>{float(r['travel']):.1f}</td>")
    table = "".join(f"<tr><td>{n}</td>{cells(r)}</tr>" for n, r in runs)
    search = "".join(f"<tr><td>seed 9, unit {u:g}</td>{cells(se[s_run(u)])}</tr>" for u in UNITS)
    cols = ["water_stand_spring", "water_stand_summer", "water_stand_autumn", "water_stand_winter", "water_lawn_spring", "water_lawn_summer",
            "water_lawn_autumn", "water_lawn_winter", "fill_stand_spring", "fill_stand_summer", "fill_stand_autumn", "fill_lawn_spring",
            "fill_lawn_summer", "fill_lawn_autumn", "d_hunger", "kills", "w_drunk", "w_air", "w_sweat", "born_dry", "w_err"]
    order = [(f"u{u:g}", se[s_run(u)]) for u in UNITS] + [(f"s{s} u{u:g}", la[l_run(s, u)]) for s in SEEDS for u in (0, 9.4)]
    appendix = ("<details><summary>Every measure of the sweeps (u: unit; s: seed of the ladder)</summary><div class='tw'><table><thead><tr><th>measure</th>"
                + "".join(f"<th>{n}</th>" for n, _ in order) + "</tr></thead><tbody>"
                + "".join(f"<tr><td>{c}</td>" + "".join(f"<td>{float(r[c]):.4g}</td>" for _, r in order) + "</tr>" for c in cols)
                + "</tbody></table></div></details>")
    page = TEMPLATE.format(CSS=CSS, DIAGRAM=DIAGRAM, TABLE=table, SEARCH=search, APPENDIX=appendix,
                           CHARTS1="".join(charts1), CHARTS2="".join(charts2), CHARTS3="".join(charts3))
    with open(os.path.join(HERE, "report.html"), "w") as f:
        f.write(page)
    print(f"report.html written; TEXT {len(TEXT.split())} words")


HEAD = "<tr><th>run</th><th>land bodies</th><th>thirst</th><th>stand / lawn</th><th>lawn / stand, spring</th><th>autumn</th><th>stand water, spring</th><th>stand ground, winter</th><th>lawn ground, winter</th><th>largest line</th><th>kinds</th><th>placed</th><th>travel</th></tr>"

TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>e081 Drinking takes - Report</title>
<style>{CSS}</style>
</head>
<body>
<main>
<h1>e081: what happens when drinking takes water from the ground?</h1>
<p class="sub">Experiment report - 2026-09-19 - #94: the body's water made part of the land's water; 4 runs of 60,000 steps on seed 9, then 6 of 100,000 on seeds 9-11, c1225</p>

<section class="tldr">
<h2>TL;DR</h2>
<p>The cycle works as designed: a crowd draws down the ground it stands on, a stand's bodies hold 0.32-0.39
of their water in spring instead of 0.8, and the lawn's share of the crowd in spring rises in every seed.
But water now binds every land body, bodies stay nearer their birth place, and kinds fall in all three
seeds (7.66 to 6.83). Not kept as the default world; the code stays as the base of the next water step.</p>
</section>

<h2>1. Question</h2>
<p>e080 found the stand the land's home in every season. A body's water was a state: drinking took
nothing from the ground and what a body lost went nowhere, so a crowd sat on its water for free. Put the
body's water into the land's, and before the runs we expected:</p>
<ol>
  <li><strong>The land stands:</strong> half the control's land bodies or more; thirst under 60% of deaths.</li>
  <li><strong>The home pays:</strong> a mid stand's bodies under 0.7 of their water; the stand's lead falls.</li>
  <li><strong>The lawn in autumn</strong> takes a larger share of the crowd.</li>
  <li><strong>The ground</strong> under a stand's crowd falls, most in winter and spring.</li>
  <li><strong>Kinds</strong> rise, and the largest line's share falls.</li>
  <li><strong>The water's ledger</strong> closes.</li>
</ol>

<h2>2. Method</h2>
<p>e080's crate with one rate, <code>unit</code>; 0 is e080 exactly (checked byte for byte).</p>
{DIAGRAM}
<p><strong>Runs.</strong> The default world. Seed 9 at 60,000 steps with unit 0, 4.7, 9.4 and 28 mm (half,
one and three times a sub-cell of full ground); then the anchor 9.4 against the control on seeds 9-11 at
100,000 steps. Censuses every 1,000 steps from 36,000. 4 cores for 30 minutes, then 6 for 70.</p>
<ul class="measures">
  <li><strong>Mid</strong> - 20-50 degrees; seasons are the hemisphere's own.</li>
  <li><strong>Stand / lawn</strong> - wood of 1 or more / under 0.1 on the cell.</li>
  <li><strong>Stand / lawn (bodies)</strong> - bodies a cell, spring and autumn together.</li>
  <li><strong>Ground</strong> - the ground's water over its 150 mm.</li>
  <li><strong>Travel</strong> - a grown body's cells from its birth place.</li>
  <li><strong>Kinds</strong> - e068's census by birth form.</li>
</ul>

<h2>3. Results</h2>
<div class="tw"><table>
<thead>""" + HEAD + """</thead>
<tbody>{TABLE}</tbody></table></div>
<ol class="verdicts">
<li><span class="verdict">Yes</span> <strong>The land stands:</strong> 88-95% of the control's land bodies; thirst 52%.</li>
<li><span class="verdict">Yes</span> <strong>The home pays:</strong> stand water in spring 0.32-0.39 against 0.8; the stand's lead 2.79 to 2.42.</li>
<li><span class="verdict no">No</span> <strong>The lawn in autumn:</strong> 0.43 to 0.41. It gains in spring instead, 0.28 to 0.43.</li>
<li><span class="verdict">Yes</span> <strong>The ground:</strong> a stand's winter ground 0.88 to 0.77.</li>
<li><span class="verdict no">No</span> <strong>Kinds:</strong> 7.66 to 6.83, falling in every seed; the largest line moves both ways.</li>
<li><span class="verdict">Yes</span> <strong>The ledger:</strong> 1.8e-11 at most.</li>
</ol>

<h3>3.1 The crowd pays for its water, and moves it</h3>
<div class="grid2">
{CHARTS1}
</div>
<p>Bodies drink about 1,700 mm a step over the world and sweat 1,450 of it back into the air, which the wind
carries off the stands. The lawn's ground ends wetter than with the producers alone, and the pools lose a
fifth of their cells.</p>

<h3>3.2 The lawn gets spring, and the bodies stay put</h3>
<div class="grid2">
{CHARTS2}
</div>
<p>Every land body holds half the water it did (0.28 against 0.58), because a crowd sits on the ground it
has drawn down. A body short of water everywhere does not travel; it walks as much but ends nearer home.</p>

<h3>3.3 Fewer kinds</h3>
<div class="grid2">
{CHARTS3}
</div>

<h2>4. Discussion</h2>
<p>The design expected water to bind the stand and free the lawn's autumn. It binds everywhere instead: the
crowd lowers the drink under itself wherever it sits, so the lawn's advantage comes only in spring, when its
ground holds 0.38 against the stand's 0.61.</p>
<p>The commute (drink in the stand, eat on the lawn) did not appear. Bodies walk as much as before and end
nearer their birth place: we read it as a tether, where a trip away from the ground a body drinks from does
not pay.</p>
<p>The conditions: c1225, three seeds at 100,000 steps, wet ground giving a twentieth of a pool, one unit of
water per block, a grown body living a twentieth of a year.</p>

<h2>5. Conclusion and next step</h2>
<p>The cycle is right and closes section 3's open loop, but on this land it costs kinds, so it is not kept
as the default world. The next step is a design (balance.md section 17): a season in which the open land
has water to drink, on top of this cycle.</p>

<h2>Appendix: data</h2>
<p>The search on seed 9 (60,000 steps):</p>
<div class="tw"><table><thead>""" + HEAD + """</thead><tbody>{SEARCH}</tbody></table></div>
<p>The runs' <code>results/*/*_bands.csv</code>, <code>*_log.csv</code> and <code>*_row.csv</code> are
committed; the censuses are not. <code>sweep.py</code> writes <code>results/sweep_search.csv</code> and
<code>sweep_ladder.csv</code>. Build with <code>uv run python experiments/e081_drink/report.py</code>.</p>
{APPENDIX}
</main>
</body>
</html>
"""

TEXT = TEMPLATE  # the words of the page, for the budget


if __name__ == "__main__":
    main()
