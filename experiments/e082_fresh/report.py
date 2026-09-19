#!/usr/bin/env python3
"""Build report.html for this experiment.

Charts: matplotlib, exported as SVG and inlined. Diagram: hand-written SVG.
Run from the repo root: uv run python experiments/eNNN_name/report.py
"""
import csv
import html
import io
import os
from collections import defaultdict

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
FRESH = [0.05, 0.2, 0.5]  # at unit 9.4; 0.05 is e081's run
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
        dash = "--" if label.startswith("control") else "-"  # the control is one run, drawn flat across the x axis
        ax.plot(xs, ys, color=SERIES[slot], linewidth=1.6, label=label, linestyle=dash, marker="o" if markers and dash == "-" else None, markersize=3.5)
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
<svg viewBox="0 0 780 250" role="img" aria-label="Wet ground's drink under W1" style="max-width:100%;height:auto;display:block">
<defs><marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="currentColor"/></marker>
<marker id="arr1" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="var(--s1)"/></marker></defs>
<g fill="none" stroke="currentColor" stroke-width="1.2" font-size="12" font-family="system-ui, sans-serif">
  <rect x="300" y="10" width="180" height="56" rx="6"/>
  <text x="390" y="33" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">the air over the cell</text>
  <text x="390" y="52" text-anchor="middle" fill="currentColor" stroke="none">the wind carries it off</text>
  <rect x="20" y="160" width="220" height="70" rx="6"/>
  <text x="130" y="184" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">the ground under the crowd</text>
  <text x="130" y="203" text-anchor="middle" fill="currentColor" stroke="none">150 mm full; a pool gives all</text>
  <text x="130" y="220" text-anchor="middle" fill="currentColor" stroke="none">of a drink, the sea none</text>
  <rect x="540" y="160" width="220" height="70" rx="6"/>
  <text x="650" y="184" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">a body's water</text>
  <text x="650" y="203" text-anchor="middle" fill="currentColor" stroke="none">drinks only up to full;</text>
  <text x="650" y="220" text-anchor="middle" fill="currentColor" stroke="none">a block holds 9.4 mm (e081)</text>
  <line x1="240" y1="195" x2="540" y2="195" stroke="var(--s1)" stroke-width="2" marker-end="url(#arr1)"/>
  <text x="390" y="165" text-anchor="middle" fill="var(--s1)" stroke="none" font-weight="600">wet ground's drink: fresh x its fill</text>
  <text x="390" y="183" text-anchor="middle" fill="var(--s1)" stroke="none">of a pool's, 0.05 to 0.2 and 0.5</text>
  <text x="390" y="215" text-anchor="middle" fill="currentColor" stroke="none">paid out of the ground (W1)</text>
  <line x1="640" y1="160" x2="470" y2="66" marker-end="url(#arr)"/>
  <text x="600" y="105" text-anchor="start" fill="currentColor" stroke="none">dry air, sweat</text>
  <line x1="310" y1="66" x2="140" y2="160" marker-end="url(#arr)"/>
  <text x="180" y="105" text-anchor="end" fill="currentColor" stroke="none">rain, runoff</text>
</g>
</svg>
<figcaption>Figure 1. The one change (blue): ground away from pools gives more of a pool's drink. Under e081's
cycle a crowd pays for it out of the ground it stands on, so a crowd that drinks more draws its ground down
faster, until the drink falls to what it loses.</figcaption>
</figure>
"""


def main():
    se, la = sweep("search"), sweep("ladder")
    v = lambda d, run, c: float(d[run][c])  # noqa: E731
    s_run = lambda f: "life9_u9.4" if f == 0.05 else f"life9_u9.4_f{f:g}"  # noqa: E731
    l_run = lambda s, w: {"control": f"life{s}_u0", 0.05: f"life{s}_u9.4", 0.2: f"life{s}_u9.4_f0.2"}[w]  # noqa: E731
    ctrl = lambda c: [v(se, "life9_u0", c)] * len(FRESH)  # noqa: E731
    over = lambda c: [v(se, s_run(f), c) for f in FRESH]  # noqa: E731
    X = "fresh (share of a pool's drink wet ground gives)"
    charts = {
        "travel": line_x("Bodies end farther from where they were born",
                         "Median cells between a grown body's birth place and where it stands (seed 9). Dashed: water free (e081's control).",
                         FRESH, [("unit 9.4", over("travel"), 0), ("control", ctrl("travel"), 5)], X, "cells", markers=True),
        "lawn": line_x("The lawn takes a larger share of the crowd",
                       "Bodies a mid lawn cell over a mid stand cell (seed 9). Rising = the crowd leaves the stands.",
                       FRESH, [("spring", over("lawn_spring_share"), 2), ("autumn", over("lawn_autumn_share"), 1),
                               ("control, spring", ctrl("lawn_spring_share"), 5)], X, "lawn / stand", markers=True),
        "top": line_x("One line takes the land",
                      "The largest lineage's share of the land's bodies over the censuses (seed 9).",
                      FRESH, [("unit 9.4", over("top_share"), 0), ("control", ctrl("top_share"), 5)], X, pct=True, markers=True),
    }
    lad = lambda c, w: [v(la, l_run(s, w), c) for s in SEEDS]  # noqa: E731
    three = lambda c: [("control", lad(c, "control"), 5), ("fresh 0.05", lad(c, 0.05), 0), ("fresh 0.2", lad(c, 0.2), 2)]  # noqa: E731
    charts.update({
        "l_kinds": line_x("Kinds on three seeds", "Kinds at a census, censuses 36,000-100,000, unit 9.4 (the control: water free).",
                          SEEDS, three("kinds_at"), "seed", "kinds", markers=True),
        "l_placed": line_x("Kinds kept to a place on three seeds", "Kinds whose bodies stay in one place, censuses 36,000-100,000.",
                           SEEDS, three("placed_at"), "seed", "kinds", markers=True),
    })
    names = [("control (water free)", lambda s: l_run(s, "control")), ("fresh 0.05 (e081)", lambda s: l_run(s, 0.05)), ("fresh 0.2", lambda s: l_run(s, 0.2))]
    cells = lambda r: (f"<td>{float(r['pop_land']):,.0f}</td><td>{float(r['d_thirst']):.0%}</td><td>{float(r['home']):.2f}</td>"  # noqa: E731
                       f"<td>{float(r['lawn_spring_share']):.2f}</td><td>{float(r['lawn_autumn_share']):.2f}</td><td>{float(r['water_stand_spring']):.2f}</td>"
                       f"<td>{float(r['water_lawn_summer']):.2f}</td><td>{float(r['top_share']):.0%}</td>"
                       f"<td>{float(r['kinds_at']):.2f}</td><td>{float(r['placed_at']):.2f}</td><td>{float(r['travel']):.1f}</td>")
    table = "".join(f"<tr><td>seed {s}, {n}</td>{cells(la[f(s)])}</tr>" for s in SEEDS for n, f in names)
    search = (f"<tr><td>seed 9, control (water free)</td>{cells(se['life9_u0'])}</tr>"
              + "".join(f"<tr><td>seed 9, fresh {f:g}</td>{cells(se[s_run(f)])}</tr>" for f in FRESH))
    cols = ["water_stand_spring", "water_stand_summer", "water_stand_autumn", "water_stand_winter", "water_lawn_spring", "water_lawn_summer",
            "water_lawn_autumn", "water_lawn_winter", "fill_stand_spring", "fill_stand_summer", "fill_stand_autumn", "fill_stand_winter",
            "fill_lawn_spring", "fill_lawn_summer", "fill_lawn_autumn", "fill_lawn_winter", "d_hunger", "kills", "w_drunk", "w_air", "w_sweat", "born_dry", "w_err"]
    order = ([("s9 control", se["life9_u0"])] + [(f"s9 f{f:g}", se[s_run(f)]) for f in FRESH]
             + [(f"s{s} {w if w == 'control' else 'f' + format(w, 'g')}", la[l_run(s, w)]) for s in SEEDS for w in ("control", 0.05, 0.2)])
    appendix = ("<details><summary>Every measure of the sweeps (s: seed; f: fresh at unit 9.4; the ladder is 100,000 steps)</summary><div class='tw'><table><thead><tr><th>measure</th>"
                + "".join(f"<th>{n}</th>" for n, _ in order) + "</tr></thead><tbody>"
                + "".join(f"<tr><td>{c}</td>" + "".join(f"<td>{float(r[c]):.4g}</td>" for _, r in order) + "</tr>" for c in cols)
                + "</tbody></table></div></details>")
    bands = defaultdict(lambda: defaultdict(list))  # run -> band -> the seeds' shares
    for r in rows_of(os.path.join(RESULTS, "top_by_band.csv")):
        bands[r["run"]][int(r["band"])].append(float(r["share"]))
    xs = sorted(set.intersection(*(set(b) for b in bands.values())))
    charts["bands"] = line_x("The leading line's share, band by band",
                             "The leading line's share of each 10-degree band's land bodies, the mean of seeds 9-11. Flat = one line everywhere.",
                             xs, [(run, [sum(bands[run][x]) / len(bands[run][x]) for x in xs], k)
                                  for run, k in (("control", 5), ("fresh 0.05", 0), ("fresh 0.2", 2))],
                             "latitude band (lower edge, degrees; north is positive)", pct=True, markers=True)
    fill = {k.upper(): c for k, c in charts.items()}
    page = TEMPLATE.format(CSS=CSS, DIAGRAM=DIAGRAM, TABLE=table, SEARCH=search, APPENDIX=appendix, **fill)
    with open(os.path.join(HERE, "report.html"), "w") as f:
        f.write(page)
    print(f"report.html written; TEXT {len(TEXT.split())} words")


HEAD = "<tr><th>run</th><th>land bodies</th><th>thirst</th><th>stand / lawn</th><th>lawn / stand, spring</th><th>autumn</th><th>stand water, spring</th><th>lawn water, summer</th><th>largest line</th><th>kinds</th><th>placed</th><th>travel</th></tr>"

TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>e082 Fresh Under W1 - Report</title>
<style>{CSS}</style>
</head>
<body>
<main>
<h1>e082: does a drink from wet ground loosen the tether?</h1>
<p class="sub">Experiment report - 2026-09-19 - #95: wet ground gives more of a pool's drink, paid out of the ground; 2 runs of 60,000 steps on seed 9, then 3 of 100,000 on seeds 9-11, c1225</p>

<section class="tldr">
<h2>TL;DR</h2>
<p>Yes. At fresh 0.2 bodies end 14.8 cells from their birth place instead of 3.1, and the open lawn
carries the crowd in spring and autumn. But one line then spreads over every latitude band: it holds 79%
of the land's bodies, and kinds fall in all three seeds (6.83 to 6.29). Not kept. Water can move the crowd
between stand and lawn, but it does not keep lines apart.</p>
</section>

<h2>1. Question</h2>
<p>e081 made a body's water part of the land's. Water then bound every body and tied it to where it was
born. Wet ground gave a twentieth of a pool's drink, a share set when drinking was free. Now the ground
pays for the drink, so we raised the share and expected:</p>
<ol>
  <li><strong>The land stands:</strong> half the control's bodies; thirst under 60% of deaths.</li>
  <li><strong>The lawn's wet season</strong> carries more of the crowd.</li>
  <li><strong>The tether loosens:</strong> bodies end farther from their birth place.</li>
  <li><strong>Kinds</strong> do not fall.</li>
</ol>

<h2>2. Method</h2>
<p>e081's code unchanged; <code>fresh</code> is already a parameter.</p>
{DIAGRAM}
<p><strong>Runs.</strong> Unit 9.4 (e081's). Seed 9 at 60,000 steps with fresh 0.2 and 0.5 beside e081's
0.05 and its control (water free); then fresh 0.2 on seeds 9-11 at 100,000 steps against e081's ladder.
Censuses every 1,000 steps from 36,000. 2 cores for 30 minutes, then 3 for 46.</p>
<ul class="measures">
  <li><strong>Mid</strong> - 20-50 degrees; seasons are the hemisphere's own.</li>
  <li><strong>Stand / lawn</strong> - wood of 1 or more / under 0.1 on the cell.</li>
  <li><strong>Lawn / stand</strong> - bodies a lawn cell over a stand cell.</li>
  <li><strong>Travel</strong> - a grown body's cells from its birth place.</li>
  <li><strong>Largest line</strong> - the biggest lineage's share of the land's bodies.</li>
  <li><strong>Kinds</strong> - e068's census by birth form.</li>
</ul>

<h2>3. Results</h2>
<div class="tw"><table>
<thead>""" + HEAD + """</thead>
<tbody>{TABLE}</tbody></table></div>
<ol class="verdicts">
<li><span class="verdict">Yes</span> <strong>The land stands:</strong> 95% of the control's land bodies; thirst 45% of deaths.</li>
<li><span class="verdict">Yes</span> <strong>The lawn's wet season:</strong> spring 0.43 to 0.67, and autumn 0.41 to 0.65, in every seed.</li>
<li><span class="verdict">Yes</span> <strong>The tether loosens:</strong> travel 3.1 to 14.8 cells.</li>
<li><span class="verdict no">No</span> <strong>Kinds:</strong> 6.83 to 6.29, falling in every seed.</li>
</ol>

<h3>3.1 Bodies go farther, and the lawn fills</h3>
<div class="grid2">
{TRAVEL}
{LAWN}
</div>
<p>Bodies drink twice as much (3,900 mm a step over the world against 1,700) and the stand's lead over the
lawn at the equinoxes falls from 2.42 to 1.51. The stand's ground is lower in every season; the lawn's
holds, and its bodies are wetter in summer.</p>

<h3>3.2 One line spreads over every band</h3>
<div class="grid2">
{BANDS}
{TOP}
</div>
<p>With water free or tight, the line that leads the tropics holds 4-20% of the bodies at 40-50 degrees
north, where other lines live. At fresh 0.2 it holds 45-74% there. The leader is a large mover that eats
half meat (seed 9: 39 blocks, 15 of them muscle).</p>

<h3>3.3 Fewer kinds</h3>
<div class="grid2">
{L_KINDS}
{L_PLACED}
</div>

<h2>4. Discussion</h2>
<p>e081 tied bodies to their ground and e082 freed them, and both lower kinds against the control, from
opposite sides. Tied bodies crowd the ground they drink from; free bodies carry one line everywhere.</p>
<p>What keeps lines apart on this land is distance against how far a line spreads. When bodies end 3-5
cells from their birth place, the north's mid-latitudes keep lines of their own; at 14.8 the leading line
reaches them within the run. Water can move the crowd between stand and lawn, but no setting here makes a
place another line cannot reach.</p>
<p>The conditions: c1225, three seeds at 100,000 steps, a block of water worth 9.4 mm of a cell, a grown
body living a twentieth of a year.</p>

<h2>5. Conclusion and next step</h2>
<p><code>fresh</code> stays 0.05 and the body's water stays free in stage C's default world. For #91, the
water track ends here: it moves the crowd but holds no line in a place. The next step is a design, not a
run: what makes a line's spread cost it where it goes.</p>

<h2>Appendix: data</h2>
<p>The search on seed 9 (60,000 steps):</p>
<div class="tw"><table><thead>""" + HEAD + """</thead><tbody>{SEARCH}</tbody></table></div>
<p>The runs' <code>results/*/*_bands.csv</code>, <code>*_log.csv</code> and <code>*_row.csv</code> are
committed; the censuses are not. <code>sweep.py</code> writes <code>results/sweep_search.csv</code> and
<code>sweep_ladder.csv</code>; <code>lines.py</code> writes <code>results/top_by_band.csv</code>. Build with
<code>uv run python experiments/e082_fresh/report.py</code>.</p>
{APPENDIX}
</main>
</body>
</html>
"""

TEXT = TEMPLATE  # the words of the page, for the budget


if __name__ == "__main__":
    main()
