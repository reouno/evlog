#!/usr/bin/env python3
"""Build report.html for this experiment.

Charts: matplotlib, exported as SVG and inlined. Diagram: hand-written SVG.
Run from the repo root: uv run python experiments/e027_room/report.py
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

# Hand-written mechanism diagram. Label every arrow; currentColor for lines and text;
# var(--s1) for the one element the argument hinges on. Keep 10-15px between text and lines.
DIAGRAM = """
<figure class="diagram">
<svg viewBox="0 0 900 250" role="img" aria-label="Three worlds: 128 cells square with 8 of matter per cell (e026), 256 square with 2 per cell (the same matter on four times the space), 128 square with 2 per cell (a quarter of the matter). The sun is 0.01 per cell per step in all three, so the big world has four times the sun; the bodies fill the room the sun makes, and in the small poor world they crowd the valley." style="max-width:100%;height:auto;display:block">
<defs><marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="currentColor"/></marker></defs>
<g fill="none" stroke="currentColor" stroke-width="1.2" font-size="12" font-family="system-ui, sans-serif">
  <text x="450" y="22" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">the sun is 0.01 a cell a step in every world; the bodies take the room the sun makes</text>
  <!-- e026 -->
  <rect x="40" y="50" width="110" height="110" rx="4"/>
  <text x="95" y="180" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">e026: 128 x 128, 8 a cell</text>
  <text x="95" y="198" text-anchor="middle" fill="currentColor" stroke="none">matter 131k, sun 164 a step</text>
  <text x="95" y="216" text-anchor="middle" fill="currentColor" stroke="none">4,600 bodies, 20% covered</text>
  <text x="95" y="234" text-anchor="middle" fill="currentColor" stroke="none">contacts 0.3-0.7 a body a step</text>
  <!-- 256 -->
  <rect x="230" y="30" width="220" height="220" rx="4" stroke="var(--s1)" stroke-width="2"/>
  <text x="340" y="130" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">256 x 256, 2 a cell</text>
  <text x="340" y="148" text-anchor="middle" fill="currentColor" stroke="none">matter 131k, sun 655 a step</text>
  <text x="340" y="166" text-anchor="middle" fill="currentColor" stroke="none">7,000 bodies twice as big, 14% covered</text>
  <text x="340" y="184" text-anchor="middle" fill="currentColor" stroke="none">contacts 0.3-0.4</text>
  <!-- 128 m2 -->
  <rect x="520" y="50" width="110" height="110" rx="4"/>
  <text x="575" y="180" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">128 x 128, 2 a cell</text>
  <text x="575" y="198" text-anchor="middle" fill="currentColor" stroke="none">matter 33k, sun 164 a step</text>
  <text x="575" y="216" text-anchor="middle" fill="currentColor" stroke="none">2,000 bodies, 11% covered</text>
  <text x="575" y="234" text-anchor="middle" fill="currentColor" stroke="none">contacts 0.4-0.6; the valley 21%</text>
  <!-- the reading -->
  <text x="780" y="90" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">room is not cells</text>
  <text x="780" y="112" text-anchor="middle" fill="currentColor" stroke="none">four times the space:</text>
  <text x="780" y="130" text-anchor="middle" fill="currentColor" stroke="none">four times the sun,</text>
  <text x="780" y="148" text-anchor="middle" fill="currentColor" stroke="none">the matter turns 4x faster,</text>
  <text x="780" y="166" text-anchor="middle" fill="currentColor" stroke="none">more and bigger bodies</text>
  <text x="780" y="196" text-anchor="middle" fill="currentColor" stroke="none">a quarter of the matter:</text>
  <text x="780" y="214" text-anchor="middle" fill="currentColor" stroke="none">half the bodies, all in the valley</text>
</g>
</svg>
<figcaption>Figure 1. Three worlds on seed 9. The big world has four times the sun on the same matter, so the matter turns over four times faster and the bodies fill the room; the poor world has half the bodies and they crowd the valley, where the food is. Contacts per body are the same in all three.</figcaption>
</figure>
"""


RUNS = [
    ("e026: 128, matter 8", "../e026_weather/results/128_sigma0_r64_f0.1_flat_eyes8_flesh1_w1_season0.5_seed9_log.csv", 1),
    ("256, matter 2", "results/256_sigma0-m2_r64_f0.1_flat_eyes8_flesh1_w1_season0.5_seed9_log.csv", 0),
    ("128, matter 2", "results/128_sigma0-m2_r64_f0.1_flat_eyes8_flesh1_w1_season0.5_seed9_log.csv", 2),
]


def main():
    data = {}
    for label, path, slot in RUNS:
        d = load_csv(path)
        n = 10  # the first 100,000 steps of every run
        data[label] = ({k: v[:n] for k, v in d.items()}, slot)
    xs = data[RUNS[0][0]][0]["step"]
    series = lambda f: [(label, [f(d, i) for i in range(len(d["step"]))], slot) for label, (d, slot) in data.items()]
    charts = [
        line_chart("Contacts per body per step", "Bodies whose lines touched, per body and step. A quarter of e026's would be the room four times the space should give.", xs, series(lambda d, i: d["contacts"][i] / max(d["pop"][i], 1) / 10_000), ymin=0),
        line_chart("Share of the world under a body", "World cells with a body on them, over all cells. In the poor world the valley alone is at 21%.", xs, series(lambda d, i: d["cover"][i]), ymin=0),
        line_chart("Sight that changes a decision", "sense_used: the share of a sensing body's decisions that seeing changed (the knockout). Flat would mean room buys the eye nothing.", xs, series(lambda d, i: d["sense_used"][i]), ymin=0),
        line_chart("Bodies", "Bodies alive at each log step. The big world holds more bodies on the same matter: four times the sun turns it over faster.", xs, series(lambda d, i: d["pop"][i]), ymin=0),
    ]
    rows = "".join(f"<tr><td>{label}</td><td>{min(d['pop']):,.0f}-{max(d['pop']):,.0f}</td><td>{min(d['size_mean']):.0f}-{max(d['size_mean']):.0f}</td><td>{min(d['regrowth']):.0f}-{max(d['regrowth']):.0f}</td>"
                   f"<td>{min(c / max(p, 1) / 1e4 for c, p in zip(d['contacts'], d['pop'])):.2f}-{max(c / max(p, 1) / 1e4 for c, p in zip(d['contacts'], d['pop'])):.2f}</td><td>{min(d['cover']):.0%}-{max(d['cover']):.0%}</td><td>{min(d['blocked']):.0%}-{max(d['blocked']):.0%}</td>"
                   f"<td>{min(d['sense_used']):.2f}-{max(d['sense_used']):.2f}</td><td>{min(d['sensor_agents_share']):.1%}-{max(d['sensor_agents_share']):.1%}</td><td>{min(d['deaths_broken']) / 1e4:.1f}-{max(d['deaths_broken']) / 1e4:.1f}</td><td>{min(d['steps_per_sec']):.0f}-{max(d['steps_per_sec']):.0f}</td></tr>"
                   for label, (d, _) in data.items())
    tables = data_table(["step", "pop", "size_mean", "regrowth", "contacts", "cover", "blocked", "sense_used", "sensor_agents_share", "deaths_broken", "lineages", "steps_per_sec"], {f"{label}, seed 9": d for label, (d, _) in data.items()}, every=1)

    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>e027 Room - Report</title>
<style>{CSS}</style>
</head>
<body>
<main>
<h1>e027: Does a bigger or a poorer world give the bodies room?</h1>
<p class="sub">Experiment report - 2026-09-04 - two pilots on seed 9, 100,000 steps, in e026's season world: 256x256 at the same matter, and 128x128 at a quarter of it, against e026's pilot.</p>

<section class="tldr">
<h2>TL;DR</h2>
<p>No. Four times the space is four times the sun, so the same matter turns over four times faster and the bodies fill the room (1.4 times as many, twice as big); a quarter of the matter halves the bodies and they crowd the valley (21% of its cells under a body, e026's whole-world figure). Contacts per body are 0.3-0.6 in all three worlds and sight changes no more decisions. Room is not a property of the grid or the matter; the bodies make their own crowd where the food is. The slow question (does the eye win with room) is not run. Next: #32, what a gut digests.</p>
</section>

<h2>1. Question</h2>
<p>The user's reading after e025 (#33): the world is too crowded for the eye and for flight to matter, since a body bumps into food or another body wherever it goes. e026's season made the eye pay; a world with room is its real test. Two laws about the world could give room. The fast question first, per the rule that experiments stay short:</p>
<ol>
  <li><strong>A bigger grid at the same matter gives room.</strong> Contacts per body fall to a quarter, the share of the world under a body to a quarter, and sight changes more decisions.</li>
  <li><strong>Less matter at the same grid gives room.</strong> The same.</li>
  <li><strong>The world stands</strong> in both.</li>
  <li><strong>The cost of 256 is 4x per step.</strong></li>
</ol>

<h2>2. The world</h2>
<p>e026's season world (the sun a sine of 20,000 steps at amplitude 0.5, the weight and flesh laws, the canopy, the spill, rain on every cell alike) with the arguments changed: the grid 256 with 2 of matter per cell, or the grid 128 with 2 per cell. No new law.</p>
{DIAGRAM}
<p><strong>Runs.</strong> Seed 9, 100,000 steps, one run each on all threads (39 and 10 minutes), against e026's season pilot on seed 9. Every 10,000 steps the log records:</p>
<ul class="measures">
  <li><strong>contacts</strong> - pairs of bodies whose lines touched, per body and step; the crowd.</li>
  <li><strong>cover</strong> - the share of the world's cells under a body; <strong>blocked</strong> - the share of moves that met a body.</li>
  <li><strong>sense_used</strong> - the share of a sensing body's decisions that seeing changed (the knockout of e009).</li>
  <li>bodies, cells per body, regrowth, bodies with a sensor, kills, steps per second.</li>
</ul>

<h2>3. Results</h2>
<div class="tw"><table>
<thead><tr><th>Seed 9, 100,000 steps (range over the log)</th><th>bodies</th><th>cells per body</th><th>regrowth a step</th><th>contacts a body a step</th><th>under a body</th><th>moves blocked</th><th>sense_used</th><th>with a sensor</th><th>killed a step</th><th>steps a second</th></tr></thead>
<tbody>{rows}</tbody></table></div>
<ol class="verdicts">
<li><span class="verdict no">No</span> A bigger grid gives room: contacts 0.29-0.44 against 0.34-0.67, the world 13-16% covered, sight unchanged; the extra sun fills the space with bodies.</li>
<li><span class="verdict no">No</span> Less matter gives room: contacts 0.36-0.60; the valley holds 65% of the bodies with 21% of its cells under one.</li>
<li><span class="verdict">Yes</span> Both worlds stand: no death; 5,500-7,900 and 1,560-2,320 bodies.</li>
<li><span class="verdict partly">Less than 4x, but too much</span> 33-48 steps a second on 12 threads (e026: 73-114 on 2); a 300,000-step run would take 2 hours alone.</li>
</ol>

<h3>3.1 The bodies fill whatever room the sun makes, and crowd where the food is</h3>
<div class="grid2">
{"".join(charts)}
</div>
<p>Contacts (top left) sit at 0.3-0.6 per body in all three worlds: the big world's fall by a third, not to a quarter. The cover (top right) shows why: the big world's bodies are twice as big and 1.4 times as many, because four times the sun turns the same matter over four times faster (regrowth 86-120 a step against 17-25). The poor world is 11% covered as a whole and 21% in its valley, where 65% of its bodies stand. Sight (bottom left) changes 0.16-0.23 of decisions everywhere.</p>

<h2>4. Discussion</h2>
<p>Room is not cells and not matter. The sun is a rate per cell, so space is income, and the bodies grow into it; take the matter away and the bodies keep to the valley's lawn, where the food is, and leave the rest empty. In every world the crowd is where the food is, and a body's contacts happen there. If room is to be given, it is by spreading the food (the terrain and the rain), not the grid. Not shown: whether the eye wins in a world that is truly sparse (a mountain world where the rain falls only on the ridges, or the season world at a larger amplitude with a store a body can spend).</p>

<h2>5. Conclusion and next step</h2>
<p>#33 is closed with this note: the grid and the matter are not the lever; the eye's test stays the season world as it is. The 256 grid is kept as an argument (2-3x the cost per step), not as the world. Next: #32, what a gut digests, a property of the gut material like the density, in the season world; then #28, the body's grid (the cloud's giants of 57 cells sit near the ceiling of 64).</p>

<h2>Appendix: data</h2>
<p>Every log step of the three runs; the full data is in <code>results/*.csv</code> and <code>../e026_weather/results/</code>. Build this report with <code>uv run python experiments/e027_room/report.py</code>.</p>
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
