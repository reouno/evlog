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

RESULTS = os.path.join(HERE, "results")
RUNS = ["life9_c0", "life9_c0.1", "life9_c0.2", "life9_c0.4"]
C3 = [0, 0.1, 0.2, 0.4]


def rows_of(path):
    with open(path) as f:
        return list(csv.DictReader(f))


def sweep():
    return {r["run"]: r for r in rows_of(os.path.join(RESULTS, "sweep_search.csv"))}


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
    legend_above(ax, len(series))
    return figure(title, subtitle, to_svg(fig))




DIAGRAM = """
<figure class="diagram">
<svg viewBox="0 0 780 250" role="img" aria-label="The refuge's three parts and the payoff that failed" style="max-width:100%;height:auto;display:block">
<defs><marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="currentColor"/></marker></defs>
<g fill="none" stroke="currentColor" stroke-width="1.2" font-size="12" font-family="system-ui, sans-serif">
  <rect x="10" y="20" width="220" height="80" rx="6"/>
  <text x="120" y="44" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">a stand (e079's world)</text>
  <text x="120" y="63" text-anchor="middle" fill="currentColor" stroke="none">S1 wet floor, S2 rests in cold</text>
  <text x="120" y="82" text-anchor="middle" fill="currentColor" stroke="none">S3: T - c3 x shade x sun heat</text>
  <rect x="10" y="150" width="220" height="80" rx="6"/>
  <text x="120" y="174" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">the lawn beside it</text>
  <text x="120" y="193" text-anchor="middle" fill="currentColor" stroke="none">grass, full sun, drier ground</text>
  <text x="120" y="212" text-anchor="middle" fill="currentColor" stroke="none">wet ground gives 1/20 of a pool</text>
  <rect x="330" y="20" width="200" height="80" rx="6"/>
  <text x="430" y="44" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">summer</text>
  <text x="430" y="63" text-anchor="middle" fill="currentColor" stroke="none">stand: water closes (S3)</text>
  <text x="430" y="82" text-anchor="middle" fill="currentColor" stroke="none">lawn: dry and hot</text>
  <rect x="330" y="150" width="200" height="80" rx="6"/>
  <text x="430" y="174" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">spring and autumn</text>
  <text x="430" y="193" text-anchor="middle" fill="var(--s1)" stroke="none">expected: the lawn is better</text>
  <text x="430" y="212" text-anchor="middle" fill="currentColor" stroke="none">found: the stand, 3x a cell</text>
  <rect x="620" y="85" width="150" height="80" rx="6"/>
  <text x="695" y="109" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">a refuge</text>
  <text x="695" y="128" text-anchor="middle" fill="currentColor" stroke="none">lines spread out,</text>
  <text x="695" y="147" text-anchor="middle" fill="currentColor" stroke="none">then retreat</text>
  <line x1="230" y1="60" x2="330" y2="60" marker-end="url(#arr)"/>
  <text x="280" y="52" text-anchor="middle" fill="currentColor" stroke="none">holds</text>
  <line x1="230" y1="190" x2="330" y2="190" marker-end="url(#arr)"/>
  <text x="280" y="182" text-anchor="middle" fill="currentColor" stroke="none">must win</text>
  <line x1="530" y1="60" x2="620" y2="112" marker-end="url(#arr)"/>
  <line x1="530" y1="190" x2="620" y2="140" stroke="var(--s1)" stroke-dasharray="4 3" marker-end="url(#arr)"/>
  <text x="590" y="200" text-anchor="middle" fill="var(--s1)" stroke="none">R1 fails</text>
</g>
</svg>
<figcaption>Figure 1. What a refuge needs. The crown's laws make the stand hold its bodies in summer (top);
a refuge also needs a season in which the lawn is the better place (bottom, blue). On this land water keeps
the lawn thin in every season, so that half never happens.</figcaption>
</figure>
"""


def main():
    sw = sweep()
    old = sw["e078 life9_h0d0"]
    val = lambda run, c: float(sw[run][c])  # noqa: E731
    charts1 = [
        line_x("The stand stops emptying in summer, and never fills",
               "Land bodies a mid stand cell by season (its hemisphere's own). Summer above the equinoxes = a refuge.",
               C3, [("summer", [val(r, "stand_summer") for r in RUNS], 1), ("winter", [val(r, "stand_winter") for r in RUNS], 0),
                    ("equinoxes", [val(r, "stand_equinox") for r in RUNS], 2)],
               "crown_cool (c3)", "bodies a cell", markers=True),
        line_x("At the equinoxes the stand is still the home",
               "Bodies a mid stand cell over a mid lawn cell at the equinoxes. Under 1 = the lawn is the better place.",
               C3, [("this world", [val(r, "home") for r in RUNS], 0), ("e078's world (c3 0)", [val("e078 life9_h0d0", "home")] * 4, 5)],
               "crown_cool (c3)", "stand / lawn", markers=True),
    ]
    charts2 = [
        line_x("A stand's bodies keep their water",
               "Mean water of the land bodies in mid stands and on the mid lawn, in their summer. Gray band: the line of 0.4.",
               C3, [("stand, summer", [val(r, "water_stand_summer") for r in RUNS], 0), ("lawn, summer", [val(r, "water_lawn_summer") for r in RUNS], 3),
                    ("lawn, equinoxes", [val(r, "water_lawn_equinox") for r in RUNS], 2)],
               "crown_cool (c3)", "water", band=(0.39, 0.41), markers=True),
        line_x("The winter's price",
               "Energy a body pays a turn to warm, in mid stands and on the mid lawn in their winter.",
               C3, [("stand, winter", [val(r, "warm_stand_winter") for r in RUNS], 0), ("lawn, winter", [val(r, "warm_lawn_winter") for r in RUNS], 3)],
               "crown_cool (c3)", "energy a turn", markers=True),
    ]
    charts3 = [
        line_x("A better home, fewer kinds",
               "Kinds at a census and kinds kept to a place (e068's census by birth form), censuses 36,000-60,000.",
               C3, [("kinds", [val(r, "kinds_at") for r in RUNS], 0), ("kept to a place", [val(r, "placed_at") for r in RUNS], 1)],
               "crown_cool (c3)", "kinds", markers=True),
    ]
    order = ["e078 life9_h0d0"] + RUNS
    label = {"e078 life9_h0d0": "e078's world", **{r: f"c3 {c:g}" for r, c in zip(RUNS, C3)}}
    table = "".join(
        f"<tr><td>{label[r]}</td><td>{val(r, 'water_stand_summer'):.2f}</td><td>{val(r, 'water_lawn_equinox'):.2f}</td>"
        f"<td>{val(r, 'stand_summer'):.3f}</td><td>{val(r, 'stand_equinox'):.3f}</td><td>{val(r, 'lawn_equinox'):.3f}</td>"
        f"<td>{val(r, 'stand_SE'):.2f}</td><td>{val(r, 'home'):.2f}</td><td>{val(r, 'warm_stand_winter'):.4f}</td><td>{val(r, 'd_cold'):.1%}</td>"
        f"<td>{val(r, 'kinds_at'):.2f}</td><td>{val(r, 'placed_at'):.2f}</td></tr>" for r in order)
    cols = ["water_stand_summer", "water_stand_winter", "water_stand_equinox", "water_lawn_summer", "water_lawn_winter", "water_lawn_equinox",
            "cool_stand_summer", "cool_lawn_summer", "warm_stand_winter", "warm_lawn_winter", "stand_winter", "lawn_summer", "lawn_winter",
            "pop_land", "d_thirst", "d_hunger", "kills"]
    appendix = ("<details><summary>Every measure of the sweep</summary><div class='tw'><table><thead><tr><th>measure</th>"
                + "".join(f"<th>{label[r]}</th>" for r in order) + "</tr></thead><tbody>"
                + "".join(f"<tr><td>{c}</td>" + "".join(f"<td>{val(r, c):.4g}</td>" for r in order) + "</tr>" for c in cols)
                + "</tbody></table></div></details>")
    page = TEMPLATE.format(CSS=CSS, DIAGRAM=DIAGRAM, TABLE=table, APPENDIX=appendix,
                           CHARTS1="".join(charts1), CHARTS2="".join(charts2), CHARTS3="".join(charts3))
    with open(os.path.join(HERE, "report.html"), "w") as f:
        f.write(page)
    print(f"report.html written; TEXT {len(TEXT.split())} words")


TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>e080 The crown's share - Report</title>
<style>{CSS}</style>
</head>
<body>
<main>
<h1>e080: does a stand become a refuge when its crown takes the sun?</h1>
<p class="sub">Experiment report - 2026-09-19 - #91 step 3: bodies on e079's world with a cooler crown, 4 runs of 60,000 steps on c1225, seed 9</p>

<section class="tldr">
<h2>TL;DR</h2>
<p>No. A cooler crown closes a stand body's summer water (0.77 of it against 0.40), and the stands stop
emptying in summer, but they never fill: at the equinoxes a stand already holds three times the bodies of
a lawn cell, in every run. Water keeps the lawn thin in every season, so the good season never comes to it.
A better stand makes fewer kinds. The crown's path to a refuge ends here; the next design is the land's water.</p>
</section>

<h2>1. Question</h2>
<p>e079 gave the stand a wet floor and put stands beside the seasonal lawns. By e078's budget a body's
summer water there closes only if the crown also halves its cooling. This step adds that (S3) and asks,
with bodies, before the runs:</p>
<ol>
  <li><strong>Water:</strong> a mid stand's bodies hold 0.4 of their water in summer.</li>
  <li><strong>Filling:</strong> bodies a mid stand cell in summer over the equinoxes, 1.25 or more.</li>
  <li><strong>Refuge, not home:</strong> at the equinoxes the lawn holds more bodies a cell than the stand.</li>
  <li><strong>Winter's price:</strong> warming in winter stands rises; cold deaths stay under 5%.</li>
  <li><strong>Kinds</strong> do not fall.</li>
</ol>

<h2>2. Method</h2>
<p>e079's crate with one rate on the body's side; 0 is e079 exactly.</p>
{DIAGRAM}
<p><strong>Runs.</strong> Seed 9, 60,000 steps, on e079's world (crown_wet 1, wood_rest 0.5): c3 0, 0.1, 0.2
and 0.4, which cut a mid stand's summer mean by about 3, 6 and 12 C. Four cores, 24 minutes. e078's control
is the old world. No 3-seed run: nothing passed 2 and 3.</p>
<ul class="measures">
  <li><strong>Mid</strong> - 20-50 degrees; seasons are the hemisphere's own.</li>
  <li><strong>Stand / lawn</strong> - wood of 1 or more / under 0.1 on the cell.</li>
  <li><strong>Water</strong> - a body's water over what it holds, at the censuses.</li>
  <li><strong>Kinds</strong> - e068's census by birth form, 36,000-60,000.</li>
</ul>

<h2>3. Results</h2>
<div class="tw"><table>
<thead><tr><th>run</th><th>stand water, summer</th><th>lawn water, equinoxes</th><th>stand a cell, summer</th><th>stand a cell, equinoxes</th><th>lawn a cell, equinoxes</th><th>stand S/E</th><th>stand / lawn</th><th>warm, winter stand</th><th>cold deaths</th><th>kinds</th><th>placed</th></tr></thead>
<tbody>{TABLE}</tbody></table></div>
<ol class="verdicts">
<li><span class="verdict">Yes</span> <strong>Water:</strong> already 0.40 at c3 0 (e078: 0.20); 0.77 at c3 0.4.</li>
<li><span class="verdict no">No</span> <strong>Filling:</strong> 1.01 at best, against 1.25.</li>
<li><span class="verdict no">No</span> <strong>Refuge, not home:</strong> the stand holds 2.96-3.28 times the lawn's bodies a cell.</li>
<li><span class="verdict">Yes</span> <strong>Winter's price:</strong> warming 2.5-fold at c3 0.4; cold deaths 3.7%.</li>
<li><span class="verdict no">No</span> <strong>Kinds:</strong> 7.00 to 3.72 at c3 0.4.</li>
</ol>

<h3>3.1 The stand holds its summer, and was already the home</h3>
<div class="grid2">
{CHARTS1}
</div>
<p>The plants' half alone moves the mid-latitude crowd into the stands: 66% of the bodies on stand or lawn,
against 16% in e078's world. S3 then only fills the summer dip of a place that was already full.</p>

<h3>3.2 The water closes in the stand, not on the lawn</h3>
<div class="grid2">
{CHARTS2}
</div>
<p>The lawn's bodies hold half their water in spring and autumn in every run. The crown's price comes due in
winter, as designed.</p>

<h3>3.3 A better home makes one winner</h3>
<div class="grid2">
{CHARTS3}
</div>
<p>At c3 0.1 one lineage holds 73% of the land's bodies, as e073's rich crown food made one winner.</p>

<h2>4. Discussion</h2>
<p>Section 13 read the lawn's good season as food per body (4.0 against 2.7). That number is high on the
lawn only because water keeps bodies off it; per cell the lawn is the poor place all year.</p>
<p>A refuge needs two places that trade places over the year. The crown can only improve the place bodies
already prefer. The half that is missing is a season in which the open land is livable, and that is set by
where a body drinks: wet ground gives a twentieth of a pool, and pools are rare.</p>
<p>The conditions: c1225, one seed at 60,000 steps, the heat band 15-30 C, a grown body living a twentieth of a year.</p>

<h2>5. Conclusion and next step</h2>
<p>The crown's three laws make the stand a better home, not a refuge, and cost kinds; they are not kept.
The next step is a design, not a run: the land's water in the good season, the savanna's pattern of open
land wet in one season and permanent water the refuge in the other.</p>

<h2>Appendix: data</h2>
<p>The runs' <code>results/search/*_bands.csv</code>, <code>*_log.csv</code> and <code>*_row.csv</code> are
committed; the censuses (<code>*_agents.csv</code>) are not. <code>sweep.py</code> writes
<code>results/sweep_search.csv</code>. Build with <code>uv run python experiments/e080_cool/report.py</code>.</p>
{APPENDIX}
</main>
</body>
</html>
"""

TEXT = TEMPLATE  # the words of the page, for the budget


if __name__ == "__main__":
    main()
