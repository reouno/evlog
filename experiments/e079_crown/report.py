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
N, LAT_LO, LAT_HI, BLOCK = 512, -59.4, 87.0, 4
# One color per run in every chart; the world picked for step 3 (w1r0.5) is the first slot.
RUN_COLOR = {"w0r0": 5, "w0r1": 1, "w1r0": 2, "w1r0.5": 0, "w1r1": 3, "w1.5r1": 4}
LABEL = {"w0r0": "control", "w0r1": "S2 alone", "w1r0": "S1 alone", "w1r0.5": "S1 1, S2 0.5",
         "w1r1": "S1 1, S2 1", "w1.5r1": "S1 1.5, S2 1", "w2r1": "S1 2, S2 1"}
ORDER = ["w0r0", "w0r1", "w1r0", "w1r0.5", "w1r1", "w1.5r1", "w2r1"]


def rows_of(path):
    with open(path) as f:
        return list(csv.DictReader(f))


def sweep():
    return {r["run"]: r for r in rows_of(os.path.join(RESULTS, "sweep_alone.csv"))}


def bands():
    g = {}
    for r in rows_of(os.path.join(RESULTS, "sweep_alone_bands.csv")):
        g.setdefault(r["run"], []).append(r)
    return g


def maps():
    g = {}
    for r in rows_of(os.path.join(RESULTS, "sweep_alone_maps.csv")):
        g.setdefault(r["run"], []).append(r)
    return g


def settling(run):
    """(year, stand cells at 20-50 degrees) in each year of the settled world's build (`sweep.py` read the build's log)."""
    return list(enumerate((int(v) for v in sweep()[run]["settling_mid"].split()), start=1))


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
        ax.plot(xs, ys, color=SERIES[slot], linewidth=1.6, label=label, marker="o" if markers else None, markersize=3.5)
    if ylabel:
        ax.set_ylabel(ylabel)
    ax.yaxis.set_major_formatter((lambda y, _p: f"{y:.0%}") if pct else kfmt)
    ax.yaxis.set_major_locator(MaxNLocator(4))
    ax.margins(x=0.02)
    legend_above(ax, len(series))
    return figure(title, subtitle, to_svg(fig))




def map_chart(title, subtitle, rows):
    """A run's land in blocks of 4 x 4 cells: yellow lawn to aqua stand by the stands' share; the sea left empty."""
    import numpy as np
    from matplotlib.colors import LinearSegmentedColormap
    nb = N // BLOCK
    img = np.full((nb, nb), np.nan)
    for r in rows:
        if float(r["land"]) >= 0.5:
            img[int(r["by"]), int(r["bx"])] = float(r["stand"])
    cmap = LinearSegmentedColormap.from_list("stand", [SERIES[3], SERIES[2]])
    cmap.set_bad((0, 0, 0, 0))
    fig, ax = plt.subplots(figsize=(4.6, 4.6))
    ax.imshow(img, cmap=cmap, vmin=0, vmax=1, interpolation="nearest")
    ax.grid(False)
    ticks = [0, 16, 32, 48, 64, 96, 127]
    ax.set_yticks(ticks, [f"{lat_of_row(t * BLOCK + 2):.0f}" for t in ticks])
    ax.set_xticks([])
    for side in ("bottom", "left"):
        ax.spines[side].set_visible(False)
    return figure(title, subtitle, to_svg(fig))


def scatter_labeled(title, subtitle, pts, xlabel, ylabel, hline=None):
    """pts: list of (label, x, y, slot, (dx, dy) label offset in points)."""
    fig, ax = new_axes(xlabel)
    if hline is not None:
        ax.axhline(hline, color=INK, linewidth=1, linestyle="--")
    for label, x, y, slot, off in pts:
        ax.scatter([x], [y], s=26, color=SERIES[slot])
        ax.annotate(label, (x, y), xytext=off, textcoords="offset points", color=INK, fontsize=8.5,
                    ha="right" if off[0] < 0 else "left")
    ax.set_ylabel(ylabel)
    ax.yaxis.set_major_locator(MaxNLocator(4))
    ax.xaxis.set_major_formatter(kfmt)
    ax.margins(x=0.12, y=0.12)
    return figure(title, subtitle, to_svg(fig))


DIAGRAM = """
<figure class="diagram">
<svg viewBox="0 0 780 270" role="img" aria-label="The land's water and its wood: the crown cuts its ground's evaporation, and wood rests in the cold" style="max-width:100%;height:auto;display:block">
<defs><marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="currentColor"/></marker>
<marker id="arr1" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="var(--s1)"/></marker></defs>
<g fill="none" stroke="currentColor" stroke-width="1.2" font-size="12" font-family="system-ui, sans-serif">
  <rect x="250" y="12" width="250" height="52" rx="6"/>
  <text x="375" y="34" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">the air over the land</text>
  <text x="375" y="52" text-anchor="middle" fill="currentColor" stroke="none">wind 0.1 cells an update</text>
  <rect x="250" y="180" width="250" height="52" rx="6"/>
  <text x="375" y="202" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">the ground</text>
  <text x="375" y="220" text-anchor="middle" fill="currentColor" stroke="none">holds 150 mm; its fill</text>
  <rect x="10" y="100" width="190" height="80" rx="6"/>
  <text x="105" y="124" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">wood</text>
  <text x="105" y="143" text-anchor="middle" fill="currentColor" stroke="none">grows: sun x warmth x fill</text>
  <text x="105" y="161" text-anchor="middle" fill="currentColor" stroke="none">dies: 1 - rest x (1 - warmth)</text>
  <rect x="590" y="12" width="180" height="52" rx="6"/>
  <text x="680" y="34" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">the sea</text>
  <text x="680" y="52" text-anchor="middle" fill="currentColor" stroke="none">rains 386 mm a year</text>
  <line x1="330" y1="64" x2="330" y2="180" marker-end="url(#arr)"/>
  <text x="322" y="96" text-anchor="end" fill="currentColor" stroke="none">rain</text>
  <line x1="420" y1="180" x2="420" y2="64" stroke="var(--s1)" stroke-width="2" marker-end="url(#arr1)"/>
  <text x="432" y="112" fill="var(--s1)" stroke="none">evaporation</text>
  <text x="432" y="130" fill="var(--s1)" stroke="none">x (1 - crown_wet x shade)</text>
  <line x1="590" y1="38" x2="500" y2="38" stroke-dasharray="4 3" marker-end="url(#arr)"/>
  <text x="545" y="30" text-anchor="middle" fill="currentColor" stroke="none">little</text>
  <line x1="500" y1="206" x2="680" y2="206"/>
  <line x1="680" y1="206" x2="680" y2="64" marker-end="url(#arr)"/>
  <text x="590" y="198" text-anchor="middle" fill="currentColor" stroke="none">runoff when full</text>
  <line x1="250" y1="206" x2="130" y2="180" marker-end="url(#arr)"/>
  <text x="188" y="214" text-anchor="middle" fill="currentColor" stroke="none">fill</text>
  <line x1="200" y1="152" x2="415" y2="152" stroke-dasharray="4 3" marker-end="url(#arr)"/>
  <text x="265" y="144" text-anchor="middle" fill="currentColor" stroke="none">shade</text>
  <text x="375" y="260" text-anchor="middle" fill="currentColor" stroke="none">shade = wood / (wood + 4); both rates 0 = e078's world</text>
</g>
</svg>
<figcaption>Figure 1. The two laws on c1225's land. S1 (crown_wet) cuts what a crown's ground gives to the air;
S2 (wood_rest) stops wood dying in a cold it cannot grow in. The blue arrow is what the result turns on:
the land's rain is mostly this evaporation coming back down.</figcaption>
</figure>
"""


def main():
    sw, bd, mp = sweep(), bands(), maps()
    lats = [int(r["lat"]) + 5 for r in bd["w0r0"]]

    def col(run, c):
        return [float(r[c]) for r in bd[run]]

    charts1 = [
        line_x("Resting wood spreads the stands out of the tropics",
               "Share of each 10-degree band's land that is stand (wood 1 or more). The control holds stands only from 30 S to 30 N.",
               lats, [(LABEL[r], col(r, "stand"), RUN_COLOR[r]) for r in ("w0r0", "w0r1", "w1r0", "w1r0.5", "w1r1")],
               "latitude (degrees)", pct=True),
        line_x("And takes the lawn where it goes",
               "Share of each band's land that is lawn (wood under 0.1). S1 alone leaves the lawn nearly where it was.",
               lats, [(LABEL[r], col(r, "lawn"), RUN_COLOR[r]) for r in ("w0r0", "w0r1", "w1r0", "w1r0.5", "w1r1")],
               "latitude (degrees)", pct=True),
    ]
    charts_map = [
        map_chart("The control", "Each square 4 x 4 cells: yellow lawn, aqua stand; ticks give the latitude (the middle rows are the north pole).", mp["w0r0"]),
        map_chart("S1 1, S2 0.5: the world for step 3", "Same map. The stands close over the south and reach 20-50 degrees in both hemispheres.", mp["w1r0.5"]),
    ]
    # labels placed apart: four worlds sit near a floor of 0.58
    off = {"w1r0": (4, 8), "w1r0.5": (6, -12), "w1r1": (-6, 8), "w0r0": (6, -3), "w0r1": (6, -3), "w1.5r1": (6, -3), "w2r1": (6, -3)}
    pts = [(LABEL[r], float(sw[r]["rain_land"]), float(sw[r]["fill_stand_summer"]), RUN_COLOR.get(r, 5), off[r]) for r in ORDER]
    charts2 = [
        scatter_labeled("The floor gets wetter only as the rain goes",
                        "Each dot a run: rain on the land, and a 20-50 degree stand's ground fill in its summer. Dashed: the line of 0.6.",
                        pts, "rain on the land (mm a year)", "stand's summer fill", hline=0.6),
        line_x("A crown's water is taken from the tropics' rain",
               "Rain a year by band of latitude on land. The sea gets 386 mm; the tropical land rains its own evaporation.",
               lats, [(LABEL[r], col(r, "rain"), RUN_COLOR[r]) for r in ("w0r0", "w1r0", "w1r0.5", "w1.5r1")],
               "latitude (degrees)", "mm a year"),
    ]
    charts3 = [
        line_x("At rate 1 the ground is wetter with less rain",
               "Mean ground fill a year by band on land. Above the control = the land keeps more water than it did.",
               lats, [(LABEL[r], col(r, "fill"), RUN_COLOR[r]) for r in ("w0r0", "w1r0", "w1r0.5", "w1.5r1")],
               "latitude (degrees)", "fill"),
        line_x("A half rest settles; a full one is still falling",
               "Stand cells at 20-50 degrees in each year of the settled world's build. A flat line = settled.",
               [y for y, _ in settling("w1r0.5")],
               [(LABEL[r], [v for _, v in settling(r)], RUN_COLOR[r]) for r in ("w0r1", "w1r0", "w1r0.5", "w1r1", "w1.5r1")],
               "year of the build", "stand cells", markers=True),
    ]
    table = "".join(
        f"<tr><td>{LABEL[r]}</td><td>{int(sw[r]['stands_mid']):,}</td><td>{int(sw[r]['lawn_mid']):,}</td>"
        f"<td>{float(sw[r]['fill_stand_summer']):.2f}</td><td>{float(sw[r]['fill_stand_winter']):.2f}</td><td>{float(sw[r]['fill_lawn_summer']):.2f}</td>"
        f"<td>{float(sw[r]['rain_ctl_lawn']):,.0f}</td><td>{float(sw[r]['rain_land']):,.0f}</td><td>{float(sw[r]['burnt']):.1%}</td></tr>"
        for r in ORDER)
    appendix = ("<details><summary>By band of latitude: stand and lawn shares, rain, fill</summary><div class='tw'><table><thead><tr><th>run</th><th>band</th>"
                "<th>land cells</th><th>stand</th><th>lawn</th><th>rain</th><th>fill</th></tr></thead><tbody>"
                + "".join(f"<tr><td>{LABEL[r]}</td><td>{x['lat']}</td><td>{x['land']}</td><td>{float(x['stand']):.2f}</td><td>{float(x['lawn']):.2f}</td>"
                          f"<td>{float(x['rain']):,.0f}</td><td>{float(x['fill']):.2f}</td></tr>" for r in ORDER for x in bd[r] if int(x["land"]))
                + "</tbody></table></div></details>")
    page = TEMPLATE.format(CSS=CSS, DIAGRAM=DIAGRAM, TABLE=table, APPENDIX=appendix,
                           CHARTS1="".join(charts1), CHARTSMAP="".join(charts_map), CHARTS2="".join(charts2), CHARTS3="".join(charts3))
    with open(os.path.join(HERE, "report.html"), "w") as f:
        f.write(page)
    words = len(TEXT.split())
    print(f"report.html written; TEXT {words} words")


TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>e079 A crown that keeps its ground - Report</title>
<style>{CSS}</style>
</head>
<body>
<main>
<h1>e079: can a crown keep its ground wet, and where do stands stand?</h1>
<p class="sub">Experiment report - 2026-09-19 - #91 step 2: two laws on the producers, seven worlds of c1225 without bodies</p>

<section class="tldr">
<h2>TL;DR</h2>
<p>Wood that rests in the cold puts stands next to the seasonal lawns: seven to eleven times the stand cells
at 20-50 degrees. A crown that cuts its ground's evaporation wets a stand's summer floor from 0.43 to 0.58,
and no further: on this climate the land's rain is its own evaporation, so a stronger cut takes the rain
and drains the land into the sea. Next: bodies on the half-rest world, where the crown must also halve a
body's cooling.</p>
</section>

<h2>1. Question</h2>
<p>A refuge needs a stand that keeps its water when the summer takes the lawn's (e078). Two laws were
designed for it as a cycle, and they change the plants, so the plants are read alone first. Before the runs,
with both laws on:</p>
<ol>
  <li><strong>Placement:</strong> stand cells at 20-50 degrees at least double.</li>
  <li><strong>Floor:</strong> a stand's summer ground fill there reaches 0.6.</li>
  <li><strong>Counterweights:</strong> the lawn there keeps half its cells, and its rain falls under a fifth.</li>
  <li><strong>Parts:</strong> S2 alone places stands, S1 alone wets them.</li>
</ol>

<h2>2. Method</h2>
<p>e078's world with two rates on the plants' side; both 0 reads e078's world file unchanged.</p>
{DIAGRAM}
<p><strong>Runs.</strong> Each world builds 17 years of plants on c1225, then runs two years with no bodies:
the control, each law alone, and four pairs. Seven runs, one core each, 6 minutes.</p>
<ul class="measures">
  <li><strong>Stand / lawn</strong> - land cell with wood of 1 or more / under 0.1.</li>
  <li><strong>Mid</strong> - 20-50 degrees, both hemispheres.</li>
  <li><strong>Summer fill</strong> - the ground's mean fill in the hemisphere's summer quarter.</li>
  <li><strong>Lawn's rain</strong> - on the control's mid lawn cells.</li>
</ul>

<h2>3. Results</h2>
<div class="tw"><table>
<thead><tr><th>world</th><th>stands mid</th><th>lawn mid</th><th>stand fill, summer</th><th>stand fill, winter</th><th>lawn fill, summer</th><th>lawn's rain</th><th>land's rain</th><th>burnt a year</th></tr></thead>
<tbody>{TABLE}</tbody></table></div>
<p>Rain in mm a year. S1 is crown_wet, S2 wood_rest.</p>
<ol class="verdicts">
<li><span class="verdict">Yes</span> <strong>Placement:</strong> 23,858 mid stand cells against 2,165.</li>
<li><span class="verdict no">No</span> <strong>Floor:</strong> 0.59; only the worlds that lose half the lawn's rain pass.</li>
<li><span class="verdict">Yes</span> <strong>Counterweights:</strong> narrowly, 51% of the lawn and 10% less rain on it (72% and 3% at a half rest).</li>
<li><span class="verdict partly">Partly</span> <strong>Parts:</strong> S1 alone also triples the mid stands; S2 alone dries their floor to 0.32.</li>
</ol>

<h3>3.1 Resting wood puts stands beside the lawns</h3>
<div class="grid2">
{CHARTS1}
</div>
<div class="grid2">
{CHARTSMAP}
</div>
<p>At a full rest a trunk grows and dies only while warm, so warmth cancels out of where it settles and the
stands reach the cold south. A half rest keeps most of the mid lawn.</p>

<h3>3.2 The floor gets wet only by taking the rain</h3>
<div class="grid2">
{CHARTS2}
</div>
<div class="grid2">
{CHARTS3}
</div>
<p>At rate 1 the land keeps its water and turns it over more slowly. Past 1, full stands shed their rain to
the sea (a third of the land at full fill at rate 2) and the lawn dries.</p>

<h2>4. Discussion</h2>
<p>The design assumed the water a crown saves stays under it. Here it is the rain's source: the wind moves
0.1 cells an update, so the land's air is the land's own evaporation. That is what caps the floor near 0.58.</p>
<p>Real forests send water up through their leaves as well as keeping their floor shaded. Here plants read
the ground's fill and never drink it, so one bucket cannot hold both.</p>
<p>The conditions: c1225's slow wind, one 150 mm bucket, a settled world of 17 years.</p>

<h2>5. Conclusion and next step</h2>
<p>The plants' half of the refuge holds except its water. A body's summer water in a stand at a 0.58 floor
closes only if the crown also halves its cooling (e078's budget), so step 3 turns on S3, on the half-rest
world. Both rates stay as arguments, 0 by default.</p>

<h2>Appendix: data</h2>
<p>By band, all seven worlds. The runs' <code>results/alone/*_bands.csv</code> and <code>*_log.csv</code>
are committed; the per-cell maps (<code>*_cells.bin</code>) and the build logs are not, and <code>sweep.py</code>
reduces them to <code>results/sweep_alone*.csv</code>. Build with <code>uv run python experiments/e079_crown/report.py</code>.</p>
{APPENDIX}
</main>
</body>
</html>
"""

TEXT = TEMPLATE  # the words of the page, for the budget


if __name__ == "__main__":
    main()
