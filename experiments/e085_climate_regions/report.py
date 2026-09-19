#!/usr/bin/env python3
"""Build report.html for this experiment.

Charts: matplotlib, exported as SVG and inlined. Diagram: hand-written SVG.
Run from the repo root: uv run python experiments/eNNN_name/report.py
"""
import csv
import html
import io
import os
import re

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
TOP = ["c1288", "c1251", "c1225", "c1151", "c1255", "c1269"]  # the six with the most regions, most first
OTHERS = ["c1208", "c1221", "c1236", "c1182", "c1173"]  # the rest of e062's worlds, for the table


def rows_of(path):
    with open(path) as f:
        return list(csv.DictReader(f))


def to_svg(fig):
    buf = io.StringIO()
    fig.savefig(buf, format="svg", bbox_inches="tight", pad_inches=0.05)
    plt.close(fig)
    return buf.getvalue()


def new_axes(xlabel):
    fig, ax = plt.subplots(figsize=(6.4, 2.6))
    ax.set_xlabel(xlabel, loc="right")
    return fig, ax


def legend_above(ax, n):
    ax.legend(loc="lower left", bbox_to_anchor=(0, 1.0), ncols=n, handlelength=1.2, borderaxespad=0, columnspacing=1.2)


def figure(title, subtitle, svg):
    return f"""
<figure class="fig">
  <figcaption><strong>{html.escape(title)}</strong><span>{html.escape(subtitle)}</span></figcaption>
  {svg}
</figure>"""


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




def blocks(cid):
    """{(gx, gy): (land, region)} from `results/blocks_<id>.csv`."""
    return {(int(r["gx"]), int(r["gy"])): (int(r["land"]), int(r["region"])) for r in rows_of(os.path.join(RESULTS, f"blocks_{cid}.csv"))}


def region_image(bl, colour_of, g=64):
    """An RGBA image a block a pixel: each region in its colour, thin land in gray, the sea clear."""
    import numpy as np
    from matplotlib.colors import to_rgba
    img = np.zeros((g, g, 4))
    for (gx, gy), (land, reg) in bl.items():
        if land >= 32:
            img[gy, gx] = to_rgba(colour_of(reg)) if reg else to_rgba("#4a4845")
    return img


def effective_chart(rows):
    rows = sorted(rows, key=lambda r: -float(r["effective_0.03"]))
    fig, ax = plt.subplots(figsize=(9.6, 2.8))
    ax.set_xlabel("stage A's 34 passing climates, most regions first", loc="right")
    xs = range(len(rows))
    colour = {"c1225": SERIES[0], "c1288": SERIES[1]}
    ax.bar(xs, [float(r["effective_0.03"]) for r in rows], color=[colour.get(r["climate"], INK) for r in rows], width=0.7)
    for x, r in zip(xs, rows):
        lo, hi = sorted((float(r["effective_0.025"]), float(r["effective_0.035"])))
        ax.plot([x, x], [lo, hi], color="#ffffff", linewidth=1.0, alpha=0.7)
    ax.axhline(8, color=INK, linewidth=0.8, linestyle="--")
    ax.text(len(rows) - 0.5, 8.2, "the line set before: 8", ha="right", va="bottom", fontsize=8, color=INK)
    for x, r in zip(xs, rows):
        if r["climate"] not in colour:
            continue
        top = max(float(r[k]) for k in ("effective_0.025", "effective_0.03", "effective_0.035"))
        if r["climate"] == "c1288":  # beside the bar, clear of the line at 8
            ax.annotate(r["climate"], (x + 0.4, top), xytext=(4, 0), textcoords="offset points", ha="left", va="center", fontsize=8, color=colour[r["climate"]])
        else:
            ax.annotate(r["climate"], (x, top), xytext=(0, 4), textcoords="offset points", ha="center", va="bottom", fontsize=8, color=colour[r["climate"]])
    ax.set_xticks([])
    ax.set_ylabel("effective regions")
    ax.set_ylim(0, 9.5)
    ax.yaxis.set_major_locator(MaxNLocator(4))
    ax.margins(x=0.01)
    return figure("No climate reaches 8; c1225 is third",
                  "exp(entropy) of the regions' predicted bodies at a dense line of 0.03; the white tick spans the lines 0.025-0.035.", to_svg(fig))


def maps_chart(rows):
    eff = {r["climate"]: float(r["effective_0.03"]) for r in rows}
    fig, axes = plt.subplots(2, 3, figsize=(9.6, 6.6))
    palette = [SERIES[0], SERIES[1], SERIES[2], SERIES[3], SERIES[4], "#9b8ce8", "#6fc3df", "#c9a36b", "#d98b6a", "#8fd18f", "#e0c55a"]
    for ax, cid in zip(axes.flat, TOP):
        bl = blocks(cid)
        size = {}
        for _land, reg in bl.values():
            if reg:
                size[reg] = size.get(reg, 0) + 1
        order = {reg: i for i, reg in enumerate(sorted(size, key=lambda k: -size[k]))}
        ax.imshow(region_image(bl, lambda reg: palette[order[reg] % len(palette)]), interpolation="nearest")
        ax.set_title(f"{cid}: {eff[cid]:.2f} effective", fontsize=9, color=INK)
        ax.set_xticks([])
        ax.set_yticks([])
        ax.grid(False)
        for sp in ax.spines.values():
            sp.set_visible(False)
    fig.tight_layout()
    return figure("The six climates with the most regions",
                  "Dense land (a predicted 0.03 bodies a cell or more) in pieces of 10 blocks or more, one colour a piece; gray thin land, black sea.", to_svg(fig))


def scatter_chart(rows, key, xlabel, title, subtitle):
    fig, ax = new_axes(xlabel)
    big = [r for r in rows if r["size"] == "512"]
    for r in big:
        c = {"c1225": SERIES[0], "c1288": SERIES[1]}.get(r["climate"], INK)
        ax.scatter(float(r[key]), float(r["effective_0.03"]), s=22, color=c, alpha=0.9 if c != INK else 0.6, edgecolors="none")
        if c != INK:
            ax.annotate(r["climate"], (float(r[key]), float(r["effective_0.03"])), xytext=(6, 0), textcoords="offset points", fontsize=8, color=c, va="center")
    ax.set_ylabel("effective regions")
    ax.yaxis.set_major_locator(MaxNLocator(4))
    ax.xaxis.set_major_locator(MaxNLocator(5))
    ax.grid(True, axis="both")
    return figure(title, subtitle, to_svg(fig))


DIAGRAM = """
<figure class="diagram">
<svg viewBox="0 0 780 180" role="img" aria-label="From a climate to regions" style="max-width:100%;height:auto;display:block">
<defs><marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="currentColor"/></marker></defs>
<g fill="none" stroke="currentColor" stroke-width="1.2" font-size="12" font-family="system-ui, sans-serif">
  <rect x="10" y="20" width="170" height="80" rx="6" stroke="var(--s1)" stroke-width="2"/>
  <text x="95" y="45" text-anchor="middle" fill="var(--s1)" stroke="none" font-weight="600">stage A's climate map</text>
  <text x="95" y="64" text-anchor="middle" fill="var(--s1)" stroke="none">ground fill, temperature</text>
  <text x="95" y="83" text-anchor="middle" fill="var(--s1)" stroke="none">by quarter, 2-7 minutes</text>
  <rect x="220" y="20" width="170" height="80" rx="6"/>
  <text x="305" y="45" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">predicted bodies</text>
  <text x="305" y="64" text-anchor="middle" fill="currentColor" stroke="none">c1225's density by dryness</text>
  <text x="305" y="83" text-anchor="middle" fill="currentColor" stroke="none">and coolest quarter (e084)</text>
  <rect x="430" y="20" width="150" height="80" rx="6"/>
  <text x="505" y="45" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">dense blocks</text>
  <text x="505" y="64" text-anchor="middle" fill="currentColor" stroke="none">0.03 bodies a cell</text>
  <text x="505" y="83" text-anchor="middle" fill="currentColor" stroke="none">or more (8 x 8 cells)</text>
  <rect x="620" y="20" width="150" height="80" rx="6"/>
  <text x="695" y="45" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">regions</text>
  <text x="695" y="64" text-anchor="middle" fill="currentColor" stroke="none">connected pieces,</text>
  <text x="695" y="83" text-anchor="middle" fill="currentColor" stroke="none">10 blocks or more</text>
  <line x1="180" y1="60" x2="220" y2="60" marker-end="url(#arr)"/>
  <line x1="390" y1="60" x2="430" y2="60" marker-end="url(#arr)"/>
  <line x1="580" y1="60" x2="620" y2="60" marker-end="url(#arr)"/>
  <rect x="10" y="125" width="170" height="44" rx="6" stroke-dasharray="4 3"/>
  <text x="95" y="143" text-anchor="middle" fill="currentColor" stroke="none">e062's producers map</text>
  <text x="95" y="160" text-anchor="middle" fill="currentColor" stroke="none">(e084's input)</text>
  <line x1="95" y1="125" x2="95" y2="100" stroke-dasharray="4 3"/>
  <text x="112" y="115" fill="currentColor" stroke="none">check on c1225: 5.03 regions from either</text>
</g>
</svg>
<figcaption>Figure 1. e084's count, fed by stage A's climate alone. What changes (blue) is the input: a
climate run with no producers, cheap enough to read all 34 of stage A's passing climates.</figcaption>
</figure>
"""


def main():
    rows = rows_of(os.path.join(RESULTS, "regions.csv"))
    by = {r["climate"]: r for r in rows}

    def tr(r):
        return (f"<tr><td>{r['climate']}</td><td>{float(r['land_share']):.2f}</td><td>{float(r['land_temp']):.1f} C</td>"
                f"<td>{float(r['dryness']):.2f}</td><td>{float(r['coolest']):.1f} C</td><td>{int(r['room']):,}</td>"
                f"<td>{int(r['regions_5pct'])}</td><td>{float(r['effective_0.03']):.2f}</td><td>{int(r['masses'])}</td></tr>")
    table = "".join(tr(r) for r in rows[:10]) + "".join(tr(by[c]) for c in OTHERS)
    appendix = ("<details><summary>All 34 climates (effective regions at the dense lines 0.025 / 0.03 / 0.035)</summary><div class='tw'><table><thead>"
                "<tr><th>climate</th><th>size</th><th>land share</th><th>rain on land (mm)</th><th>regions</th><th>0.025</th><th>0.03</th><th>0.035</th><th>largest</th><th>regions sharing a land mass</th></tr></thead><tbody>"
                + "".join(f"<tr><td>{r['climate']}</td><td>{r['size']}</td><td>{float(r['land_share']):.2f}</td><td>{float(r['rain_land']):,.0f}</td><td>{r['regions']}</td>"
                          f"<td>{float(r['effective_0.025']):.2f}</td><td>{float(r['effective_0.03']):.2f}</td><td>{float(r['effective_0.035']):.2f}</td>"
                          f"<td>{float(r['largest']):.0%}</td><td>{r['regions_sharing_a_mass']}</td></tr>" for r in rows)
                + "</tbody></table></div></details>")
    land = scatter_chart(rows, "land_share", "land share of the world", "A small land holds more regions",
                         "30 climates at 512 cells; rank correlation -0.57. A flat cloud would mean the land share does not matter.")
    dry = scatter_chart(rows, "dryness", "the land's mean yearly dryness (0 wet, 1 dry)", "The dryness does not predict the count",
                        "The same climates; rank correlation -0.06. Above 0.85 no block is dense.")
    page = TEMPLATE.format(CSS=CSS, DIAGRAM=DIAGRAM, TABLE=table, APPENDIX=appendix, EFFECTIVE=effective_chart(rows),
                           MAPS=maps_chart(rows), LAND=land, DRY=dry)
    with open(os.path.join(HERE, "report.html"), "w") as f:
        f.write(page)
    words = len(TEXT.split())
    print(f"report.html written; TEXT {words} words")


HEAD = ("<tr><th>climate</th><th>land share</th><th>land temp</th><th>dryness</th><th>coolest quarter</th>"
        "<th>predicted bodies</th><th>regions (5%+)</th><th>effective regions</th><th>land masses</th></tr>")


TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>e085 Regions Over Climates - Report</title>
<style>{CSS}</style>
</head>
<body>
<main>
<h1>e085: does any of stage A's climates hold more regions than c1225?</h1>
<p class="sub">Experiment report - 2026-09-19 - #98: e084's region count over stage A's 34 passing climates, from the climate alone; no bodies run</p>

<section class="tldr">
<h2>TL;DR</h2>
<p>Counting regions needs only stage A's climate: on c1225 its map gives the producers map's regions (5.03
either way). Over stage A's 34 passing climates none holds 8 effective regions, the line set for the bodies step;
the most, c1288, holds 7.5, and c1225 is third. More regions come with a small, cold land, not with dryness. So
the bodies step was not run; next is a proposal for testing whether kinds follow regions at all.</p>
</section>

<h2>1. Question</h2>
<p>e084 counted the regions a land holds apart from its producers map, and c1225 held the most of our six worlds.
To test whether kinds rise with regions we need a world with clearly more. Stage A passed 34 climates.</p>
<ol>
  <li><strong>The climate alone</strong> gives c1225's regions (no producers needed).</li>
  <li><strong>One to three climates</strong> hold 8 effective regions or more, with middling dryness and a large land.</li>
  <li><strong>Kinds follow the regions</strong>, run only on such a climate.</li>
</ol>

<h2>2. Method</h2>
{DIAGRAM}
<p>e061's climate with maps on the 34 climates, 20 years each as in the search (10 cores, 11 minutes, 1.5
core-hours). e084's rule and calibration unchanged. One check beyond the plan: c1288's producers (draw d11, 5
minutes).</p>
<ul class="measures">
  <li><strong>Effective regions</strong> - exp(entropy) of the regions' predicted bodies.</li>
  <li><strong>Dryness</strong> - 1 minus the ground's fill, the year's mean.</li>
  <li><strong>Coolest quarter</strong> - the lowest quarterly mean temperature.</li>
  <li><strong>Land masses</strong> - connected land holding the regions.</li>
</ul>

<h2>3. Results</h2>
<div class="tw"><table><thead>""" + HEAD + """</thead><tbody>{TABLE}</tbody></table></div>
<p class="sub" style="margin-top:6px">The ten climates with the most regions, then the rest of the worlds e062 ran.</p>
<ol class="verdicts">
<li><span class="verdict">Yes</span> <strong>The climate alone gives c1225's regions:</strong> 8 regions, 5.03 effective, from either map; block dryness agrees at 0.999.</li>
<li><span class="verdict no">No</span> <strong>A few hold 8 or more:</strong> none does; the most, c1288, holds 7.53, and the regions follow a small, cold land, not the dryness.</li>
<li><span class="verdict partly">Not run</span> <strong>Kinds follow regions:</strong> the condition was not met.</li>
</ol>

<h3>3.1 No climate reaches the line</h3>
{EFFECTIVE}
<p>c1225 is third of 34. Most climates hold one or two regions and four hold none. The count is stable across the
dense lines for the top two.</p>

<h3>3.2 The most divided lands</h3>
{MAPS}
<p>c1288's regions lie on five land masses, and its two largest masses hold three and five regions: it is broken by
the sea and, inside a land, by the cold. c1225's are on one continent.</p>

<h3>3.3 What makes regions: a small, cold land</h3>
<div class="grid2">
{LAND}
{DRY}
</div>
<p>Land share -0.57, coolest quarter -0.45, relief +0.36; dryness -0.06 and rain -0.09. A small land breaks into
islands and narrow pieces; a cold one breaks where the winter thins the bodies.</p>

<h2>4. Discussion</h2>
<p>I expected e084's dividing strip, middling dry ground that is hot all year, to be what makes many regions.
Across climates it is not: the most divided lands are small and cold. c1225 is divided by dryness and heat, c1288
by the sea and by cold, so the two are divided differently, not more and less of the same.</p>
<p>c1288's producers hold with d11 (grass 47%, wood 42%, algae 10%, fire 3.4% of the land a year) but wood is the
larger part of no habitat, so it fails one of stage B's lines. Its regions do not change with producers.</p>
<p>What this does not show: whether kinds follow regions. It also counts a region held by the sea as held, though
stage C's bodies live in water too.</p>

<h2>5. Conclusion and next step</h2>
<p>Stage A made no climate with clearly more regions than c1225; the most holds 1.5 times as many. The count needs
only a climate run, so a search aimed at regions is cheap. Whether it is worth doing depends on the untested claim
that kinds follow regions, which is the proposed next step (<code>balance.md</code> section 21).</p>

<h2>Appendix: data</h2>
<p><code>regions.py</code> writes <code>results/regions.csv</code>, <code>check.csv</code>, <code>blocks_*.csv</code> and
prints <code>regions.txt</code>. The maps (<code>results/maps/*_maps.bin</code>, 4-16 MB each) are not committed;
<code>maps.sh</code> rebuilds them. Build with <code>uv run python experiments/e085_climate_regions/report.py</code>.</p>
{APPENDIX}
</main>
</body>
</html>
"""

TEXT = re.sub(r"<[^>]+>|\{[A-Z]+\}", " ", TEMPLATE[TEMPLATE.index("<main>"):])  # the words of the page, for the budget


if __name__ == "__main__":
    main()
