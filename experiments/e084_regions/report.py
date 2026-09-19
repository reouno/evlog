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
WORLDS = [("c1225", "very wet"), ("c1208", "cold"), ("c1221", "mild"), ("c1236", "cool"), ("c1182", "hot wet"), ("c1173", "hot dry")]
N, LAT_LO, LAT_HI = 512, -59.4, 87.0

def rows_of(path):
    with open(path) as f:
        return list(csv.DictReader(f))


def lat_of_row(y):
    return LAT_LO + (LAT_HI - LAT_LO) * (1 - abs(2 * (y + 0.5) / N - 1))


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





def blocks(world):
    """{(gx, gy): (land, dry, temp, predicted, region)} from `results/blocks_<world>.csv`."""
    return {(int(r["gx"]), int(r["gy"])): (int(r["land"]), float(r["dry"]), float(r["temp"]), float(r["predicted"]), int(r["region"]))
            for r in rows_of(os.path.join(RESULTS, f"blocks_{world}.csv"))}


def region_image(bl, colour_of):
    """An RGBA 64 x 64 image: each region in its colour, thin land in gray, the sea clear."""
    import numpy as np
    from matplotlib.colors import to_rgba
    img = np.zeros((64, 64, 4))
    for (gx, gy), (land, _d, _t, _p, reg) in bl.items():
        if land < 32:
            continue
        img[gy, gx] = to_rgba(colour_of(reg)) if reg else to_rgba("#4a4845")
    return img


def calibration_chart():
    rows = rows_of(os.path.join(RESULTS, "calibration.csv"))
    fig, ax = new_axes("the ground's yearly dryness (0 wet, 1 dry)")
    for (lo, hi, label), slot in zip(((-99, 0, "coolest quarter under 0 C"), (10, 20, "10-20 C"), (20, 25, "20-25 C"), (33, 99, "33 C or more (hot all year)")), (0, 2, 3, 1)):
        pts = [((float(r["dry_lo"]) + float(r["dry_hi"])) / 2, float(r["density"])) for r in rows
               if float(r["temp_lo"]) == lo and int(r["blocks"]) >= 5]
        ax.plot([p[0] for p in pts], [p[1] for p in pts], color=SERIES[slot], linewidth=1.6, marker="o", markersize=3.5, label=label)
    ax.axhline(0.03, color=INK, linewidth=0.8, linestyle="--")
    ax.set_ylabel("bodies a land cell")
    ax.yaxis.set_major_locator(MaxNLocator(4))
    ax.margins(x=0.02)
    legend_above(ax, 2)
    return figure("Dry ground and a year with no cool season thin the bodies",
                  "c1225's control, blocks of 8 x 8 cells, mean density by class. Dashed: the line a dense block is over (0.03).", to_svg(fig))


def c1225_chart():
    bl = blocks("c1225")
    held = {}
    for r in rows_of(os.path.join(HERE, "..", "e083_hold", "results", "maps.csv")):
        if r["run"] == "control":
            key = (int(r["gx"]), int(r["gy"]))
            if key in bl and bl[key][4]:
                h = held.setdefault(bl[key][4], [0, 0])
                h[0] += int(r["leader"])
                h[1] += int(r["bodies"])
    colour = lambda reg: SERIES[0] if reg in held and held[reg][0] / held[reg][1] >= 0.4 else SERIES[1]  # noqa: E731
    fig, ax = plt.subplots(figsize=(4.6, 4.6))
    ax.imshow(region_image(bl, colour), interpolation="nearest")
    ax.grid(False)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.axhline(31.5, color=INK, linewidth=0.8, linestyle=":")
    return figure("c1225: the map's regions are the ones held apart",
                  "Regions predicted from the map alone, coloured by who holds them in the control (seed 9): blue the leading line (40% or more), orange other lines; gray thin land.", to_svg(fig))


def worlds_chart():
    fig, axes = plt.subplots(2, 3, figsize=(9.6, 6.6))
    palette = [SERIES[0], SERIES[1], SERIES[2], SERIES[3], SERIES[4], "#9b8ce8", "#6fc3df", "#c9a36b"]
    for ax, (world, name) in zip(axes.flat, WORLDS):
        bl = blocks(world)
        size = {}
        for v in bl.values():
            if v[4]:
                size[v[4]] = size.get(v[4], 0) + 1
        order = {reg: i for i, reg in enumerate(sorted(size, key=lambda k: -size[k]))}
        ax.imshow(region_image(bl, lambda reg: palette[order[reg] % len(palette)]), interpolation="nearest")
        ax.set_title(f"{world} ({name})", fontsize=9, color=INK)
        ax.set_xticks([])
        ax.set_yticks([])
        ax.grid(False)
        for sp in ax.spines.values():
            sp.set_visible(False)
    fig.tight_layout()
    return figure("Six worlds, their regions",
                  "Dense land (a predicted 0.03 bodies a cell or more) in pieces of 10 blocks or more, one colour a piece; gray thin land.", to_svg(fig))


def effective_chart():
    rows = {r["world"]: r for r in rows_of(os.path.join(RESULTS, "regions.csv"))}
    lo = {r["world"]: float(r["effective"]) for r in rows_of(os.path.join(RESULTS, "regions_dense0.025.csv"))}
    hi = {r["world"]: float(r["effective"]) for r in rows_of(os.path.join(RESULTS, "regions_dense0.035.csv"))}
    fig, ax = new_axes("")
    names = [w for w, _ in WORLDS]
    xs = range(len(names))
    vals = [float(rows[w]["effective"]) for w in names]
    ax.bar(xs, vals, color=[SERIES[0] if w == "c1225" else INK for w in names], width=0.6)
    for x, w in zip(xs, names):
        ax.plot([x, x], [min(lo[w], hi[w]), max(lo[w], hi[w])], color="#ffffff", linewidth=1.2, alpha=0.7)
    ax.set_xticks(list(xs), names)
    ax.set_ylabel("effective regions")
    ax.yaxis.set_major_locator(MaxNLocator(4))
    return figure("c1225 holds the most regions of the six",
                  "exp(entropy) of the regions' predicted bodies at a dense line of 0.03; the white tick spans 0.025-0.035.", to_svg(fig))


DIAGRAM = """
<figure class="diagram">
<svg viewBox="0 0 780 170" role="img" aria-label="From a map to regions" style="max-width:100%;height:auto;display:block">
<defs><marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="currentColor"/></marker></defs>
<g fill="none" stroke="currentColor" stroke-width="1.2" font-size="12" font-family="system-ui, sans-serif">
  <rect x="10" y="30" width="170" height="80" rx="6"/>
  <text x="95" y="55" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">the producers' map</text>
  <text x="95" y="74" text-anchor="middle" fill="currentColor" stroke="none">ground fill, temperature</text>
  <text x="95" y="93" text-anchor="middle" fill="currentColor" stroke="none">by quarter, no bodies</text>
  <rect x="220" y="30" width="170" height="80" rx="6" stroke="var(--s1)" stroke-width="2"/>
  <text x="305" y="55" text-anchor="middle" fill="var(--s1)" stroke="none" font-weight="600">predicted bodies</text>
  <text x="305" y="74" text-anchor="middle" fill="var(--s1)" stroke="none">c1225's density by dryness</text>
  <text x="305" y="93" text-anchor="middle" fill="var(--s1)" stroke="none">and coolest quarter (r 0.97)</text>
  <rect x="430" y="30" width="150" height="80" rx="6"/>
  <text x="505" y="55" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">dense blocks</text>
  <text x="505" y="74" text-anchor="middle" fill="currentColor" stroke="none">0.03 bodies a cell</text>
  <text x="505" y="93" text-anchor="middle" fill="currentColor" stroke="none">or more (8 x 8 cells)</text>
  <rect x="620" y="30" width="150" height="80" rx="6"/>
  <text x="695" y="55" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">regions</text>
  <text x="695" y="74" text-anchor="middle" fill="currentColor" stroke="none">connected pieces,</text>
  <text x="695" y="93" text-anchor="middle" fill="currentColor" stroke="none">10 blocks or more</text>
  <line x1="180" y1="70" x2="220" y2="70" marker-end="url(#arr)"/>
  <line x1="390" y1="70" x2="430" y2="70" marker-end="url(#arr)"/>
  <line x1="580" y1="70" x2="620" y2="70" marker-end="url(#arr)"/>
  <text x="505" y="145" text-anchor="middle" fill="currentColor" stroke="none">a thin strip one block wide is enough to hold a boundary (e083)</text>
</g>
</svg>
<figcaption>Figure 1. Counting a world's regions without bodies. The step the argument hinges on (blue) is the
prediction: c1225's measured bodies by the ground's dryness and the coolest quarter's temperature, applied to
any world's map.</figcaption>
</figure>
"""


def main():
    rows = rows_of(os.path.join(RESULTS, "regions.csv"))
    names = dict(WORLDS)
    table = "".join(
        f"<tr><td>{r['world']} ({names[r['world']]})</td><td>{int(r['land_cells']):,}</td><td>{int(r['room']):,}</td><td>{int(r['regions_5pct'])}</td>"
        f"<td>{float(r['effective']):.2f}</td><td>{float(r['largest']):.0%}</td></tr>" for r in sorted(rows, key=lambda r: -float(r["effective"])))
    cal = rows_of(os.path.join(RESULTS, "calibration.csv"))
    temps = sorted({(float(r["temp_lo"]), float(r["temp_hi"])) for r in cal})
    drys = sorted({(float(r["dry_lo"]), float(r["dry_hi"])) for r in cal})
    val = {(float(r["dry_lo"]), float(r["temp_lo"])): (float(r["density"]), int(r["blocks"])) for r in cal}
    appendix = ("<details><summary>The calibration: c1225's land bodies a land cell by the ground's yearly dryness (rows) and the coolest quarter's temperature (columns); blocks in brackets</summary><div class='tw'><table><thead><tr><th>dryness</th>"
                + "".join(f"<th>{'under ' + format(hi, 'g') if lo < -90 else (format(lo, 'g') + ' +' if hi > 90 else format(lo, 'g') + '-' + format(hi, 'g'))} C</th>" for lo, hi in temps) + "</tr></thead><tbody>"
                + "".join(f"<tr><td>{lo:g}-{min(hi, 1):g}</td>" + "".join(f"<td>{val[(lo, t)][0]:.3f} ({val[(lo, t)][1]})</td>" for t, _ in temps) + "</tr>" for lo, hi in drys)
                + "</tbody></table></div></details>")
    page = TEMPLATE.format(CSS=CSS, DIAGRAM=DIAGRAM, TABLE=table, APPENDIX=appendix, CAL=calibration_chart(), C1225=c1225_chart(),
                           WORLDS=worlds_chart(), EFFECTIVE=effective_chart())
    with open(os.path.join(HERE, "report.html"), "w") as f:
        f.write(page)
    print(f"report.html written; TEXT {len(TEXT.split())} words")


HEAD = "<tr><th>world</th><th>land cells</th><th>predicted bodies</th><th>regions (5%+)</th><th>effective regions</th><th>largest</th></tr>"

TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>e084 Regions Of A World - Report</title>
<style>{CSS}</style>
</head>
<body>
<main>
<h1>e084: how many regions does a world hold apart?</h1>
<p class="sub">Experiment report - 2026-09-19 - #97: six worlds' producers-only maps read for the regions a line could hold against another; no bodies run</p>

<section class="tldr">
<h2>TL;DR</h2>
<p>A world's map predicts where bodies will be thin (correlation 0.97 on c1225): dry ground and a year with no
cool quarter. Its dense land falls into regions, and on c1225 they are the regions held apart by different
lines. Of the six worlds we have, c1225 holds the most (5.0 effective; the next 2.2). So there is no better
world among them, and the bodies step was not run. Next: count regions over stage A's climates.</p>
</section>

<h2>1. Question</h2>
<p>e083 found a region held against the leading line by a thin strip of land between two dense ones. If kinds
follow such regions, the generated world matters. Before any bodies:</p>
<ol>
  <li><strong>A map without bodies</strong> says where bodies will be thin, and its regions are the held ones.</li>
  <li><strong>Worlds differ</strong> in their regions.</li>
  <li><strong>Kinds follow the regions</strong>, tested with bodies only on a world with more regions than c1225.</li>
</ol>

<h2>2. Method</h2>
{DIAGRAM}
<p><strong>Maps.</strong> e062's producers with draw d11 on the five other worlds with stage A/B params (5
cores for 6 minutes); c1225's map is e062's. The calibration is e081's control on c1225, seeds 9-11. The
rule was set on c1225 before the other worlds were read.</p>
<ul class="measures">
  <li><strong>Dryness</strong> - 1 minus the ground's fill, the year's mean.</li>
  <li><strong>Coolest quarter</strong> - the block's lowest quarterly mean temperature.</li>
  <li><strong>Effective regions</strong> - exp(entropy) of the regions' predicted bodies.</li>
  <li><strong>Largest</strong> - the biggest region's share of them.</li>
</ul>

<h2>3. Results</h2>
<div class="tw"><table><thead>""" + HEAD + """</thead><tbody>{TABLE}</tbody></table></div>
<ol class="verdicts">
<li><span class="verdict">Yes</span> <strong>A map says where bodies are thin:</strong> correlation 0.97; on c1225 its regions are the ones held apart.</li>
<li><span class="verdict">Yes</span> <strong>Worlds differ:</strong> 0 to 5.0 effective regions.</li>
<li><span class="verdict partly">Not run</span> <strong>Kinds follow regions:</strong> no world holds more regions than c1225.</li>
</ol>

<h3>3.1 The map predicts the bodies</h3>
<div class="grid2">
{CAL}
{C1225}
</div>
<p>Cold winters thin the bodies, and so does a year that never cools below 33 C: every quarter costs water to
cool. The strip that holds e083's boundary is such a place, a block or two wide.</p>

<h3>3.2 c1225 holds the most</h3>
{WORLDS}
<div class="grid2" style="margin-top:20px">
{EFFECTIVE}
</div>
<p>A wet world is one dense land; a dry one has none. c1225 is between, with a few blocks hot all year, and
its dense land breaks into pieces. c1182 is as dry on the mean and keeps its dense land in one piece: the land's
shape counts too.</p>

<h2>4. Discussion</h2>
<p>The regions a line can hold are a property of the generated world, readable from the climate and
producers before any body is placed. That gives stage A a measure it lacked.</p>
<p>c1225 was chosen in stage B for its producers. It is also the most divided of the six, so the kinds stage C
has measured on it are not those of a poor land.</p>
<p>What it does not show: whether kinds rise with regions across worlds. That needs a world with more regions
than c1225. The calibration is c1225's; a world much colder or hotter is read through classes with few blocks.</p>

<h2>5. Conclusion and next step</h2>
<p>A world's regions can be counted from its map, and c1225 holds the most of our six. The next step is to
count them over stage A's passing climates (34), to find a world with more regions, then its producers and
bodies against c1225.</p>

<h2>Appendix: data</h2>
<p><code>regions.py</code> writes <code>results/regions.csv</code> (and at other dense lines), <code>blocks_*.csv</code>
and <code>calibration.csv</code>. The maps (<code>results/maps/*_maps.bin</code>, 24 MB each) are not committed; <code>maps.sh</code>
rebuilds them. Build with
<code>uv run python experiments/e084_regions/report.py</code>.</p>
{APPENDIX}
</main>
</body>
</html>
"""

TEXT = TEMPLATE  # the words of the page, for the budget


if __name__ == "__main__":
    main()
