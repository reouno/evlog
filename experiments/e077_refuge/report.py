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
E075 = os.path.join(os.path.dirname(HERE), "e075_hunt", "results", "ladder")
SEEDS = (9, 10, 11)
YEAR = 11880  # steps in c1225's year; the bodies start on a whole year, so a step's phase is step / YEAR
N, LAT_LO, LAT_HI = 512, -59.4, 87.0
KIND_COLOR = {1: SERIES[0], 2: SERIES[1], 3: SERIES[3], 4: SERIES[2]}  # hard, muscle, sensor, gut
QUARTERS = ["0", "0.25 (N summer)", "0.5", "0.75 (N winter)"]


def rows_of(path):
    with open(path) as f:
        return list(csv.DictReader(f))


def quarter(mid):
    return int(((mid / YEAR + 0.125) % 1.0) * 4)


def lat_of(cell):
    return LAT_LO + (LAT_HI - LAT_LO) * (1 - abs(2 * ((cell // N) + 0.5) / N - 1))


def year_profile(bins=12):
    """e075's kept runs, steps 20,000-100,000, seeds pooled: the log in bins of the year's phase."""
    cols = ["pop_land", "pop_surface", "pop_bottom", "grass_grown", "temp_day_land"]
    acc = [[0.0] * len(cols) for _ in range(bins)]
    n = [0] * bins
    for s in SEEDS:
        for r in rows_of(os.path.join(E075, f"c1225_life{s}_both_log.csv")):
            st = int(r["step"])
            if st <= 20000:
                continue
            b = int((((st - 500) / YEAR) % 1.0) * bins)
            n[b] += 1
            for i, c in enumerate(cols):
                acc[b][i] += float(r[c])
    return [(b + 0.5) / bins for b in range(bins)], {c: [acc[b][i] / n[b] for b in range(bins)] for i, c in enumerate(cols)}


def bands():
    """e077's runs after the first year, seeds pooled: by (latitude, wood class, quarter) grown, cells, temp, bodies, rows."""
    g = {}
    for s in SEEDS:
        for r in rows_of(os.path.join(RESULTS, f"c1225_life{s}_year_bands.csv")):
            st = int(r["step"])
            if st <= 12000:
                continue
            k = (int(r["lat"]), int(r["wood_class"]), quarter(st - 500))
            v = g.setdefault(k, [0.0] * 5)
            for i, c in enumerate(("grown", "cells", "temp", "bodies")):
                v[i] += float(r[c])
            v[4] += 1
    return g


def census():
    """Per seed and census: phase, land bodies, share in a stand; and the bodies for the gallery."""
    out, bodies = {}, {}
    for s in SEEDS:
        by = {}
        for r in rows_of(os.path.join(RESULTS, f"c1225_life{s}_year_agents.csv")):
            if r["medium"] != "0":
                continue
            by.setdefault(int(r["step"]), []).append(r)
        out[s] = [((st / YEAR) % 1, len(rs), sum(float(r["crown"]) >= 1 for r in rs) / len(rs)) for st, rs in sorted(by.items())]
        last = by[max(by)]
        for where, keep in (("stand", lambda r: float(r["crown"]) >= 1),
                            ("lawn", lambda r: float(r["crown"]) < 0.1 and abs(lat_of(int(r["cell"]))) >= 20)):
            rs = [r for r in last if keep(r)]
            lin = {}
            for r in rs:
                lin.setdefault(r["lineage"], []).append(r)
            top = max(lin.values(), key=len)
            shapes = {}
            for r in top:
                shapes.setdefault((r["side"], r["cells"]), []).append(r)
            (side, cells), same = max(shapes.items(), key=lambda kv: len(kv[1]))
            r = same[0]
            bodies[(s, where)] = dict(seed=s, where=where, lineage=r["lineage"], n=len(top), of=len(rs), side=int(side), cells=cells,
                                      hard=r["hard"], muscle=r["muscle"], gut=r["digestive"],
                                      kills=sum(float(x["killed"]) for x in top) / max(1e-9, sum(float(x["plant"]) + float(x["killed"]) + float(x["scavenged"]) for x in top)),
                                      lat=sum(abs(lat_of(int(x["cell"]))) for x in top) / len(top))
    return out, bodies

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


def scatter_x(title, subtitle, groups, xlabel, pct=False):
    """groups: list of (label, xs, ys, slot)."""
    fig, ax = new_axes(xlabel)
    for label, xs, ys, slot in groups:
        ax.scatter(xs, ys, s=16, color=SERIES[slot], label=label)
    ax.yaxis.set_major_formatter((lambda y, _p: f"{y:.0%}") if pct else kfmt)
    ax.yaxis.set_major_locator(MaxNLocator(4))
    ax.set_xlim(0, 1)
    legend_above(ax, len(groups))
    return figure(title, subtitle, to_svg(fig))


DIAGRAM = """
<figure class="diagram">
<svg viewBox="0 0 780 214" role="img" aria-label="The land from south to north: seasonal lawns on both sides of a tropical belt of stands" style="max-width:100%;height:auto;display:block">
<defs><marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="currentColor"/></marker></defs>
<g fill="none" stroke="currentColor" stroke-width="1.2" font-size="12" font-family="system-ui, sans-serif">
  <text x="10" y="20" fill="currentColor" stroke="none" font-weight="600">the land, south to north</text>
  <rect x="10" y="40" width="230" height="56" rx="6"/>
  <text x="125" y="62" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">lawn, 60-20 S</text>
  <text x="125" y="80" text-anchor="middle" fill="currentColor" stroke="none">grows in its spring and autumn</text>
  <rect x="275" y="40" width="230" height="56" rx="6" stroke="var(--s1)" stroke-width="2"/>
  <text x="390" y="62" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">stands, 30 S - 20 N</text>
  <text x="390" y="80" text-anchor="middle" fill="currentColor" stroke="none">wood 1+ a cell, 25-42 C all year</text>
  <rect x="540" y="40" width="230" height="56" rx="6"/>
  <text x="655" y="62" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">lawn, 20-50 N</text>
  <text x="655" y="80" text-anchor="middle" fill="currentColor" stroke="none">grows in its spring and autumn</text>
  <line x1="240" y1="68" x2="275" y2="68" marker-start="url(#arr)" marker-end="url(#arr)"/>
  <line x1="505" y1="68" x2="540" y2="68" marker-start="url(#arr)" marker-end="url(#arr)"/>
  <text x="522" y="122" text-anchor="middle" fill="currentColor" stroke="none">~17 cells a band; a life travels 22-28</text>
  <text x="125" y="150" text-anchor="middle" fill="currentColor" stroke="none">winter: no growth (-6 to 4 C)</text>
  <text x="125" y="168" text-anchor="middle" fill="currentColor" stroke="none">summer: 35-38 C, water to cool</text>
  <text x="655" y="150" text-anchor="middle" fill="currentColor" stroke="none">winter: no growth</text>
  <text x="655" y="168" text-anchor="middle" fill="currentColor" stroke="none">summer: too hot, grass uneaten</text>
  <text x="390" y="150" text-anchor="middle" fill="var(--s1)" stroke="none">bodies here hold within 9% all year</text>
  <text x="390" y="168" text-anchor="middle" fill="var(--s1)" stroke="none">and no cooler than the lawn beside it</text>
  <text x="390" y="200" text-anchor="middle" fill="currentColor" stroke="none">the lawns' crowds rise at the equinoxes and fall at both solstices</text>
</g>
</svg>
<figcaption>Figure 1. Where the season bites. The mid-latitude lawns are lost twice a year, to cold in winter
and to heat in summer; the stands sit in the tropics beside them. The blue box is the missing condition (B):
a stand holds its own bodies but offers the lawn's nothing it lost.</figcaption>
</figure>
"""


def gallery(bodies, caption, n=2):
    cards = []
    for s in SEEDS:
        for where in ("stand", "lawn"):
            r = bodies[(s, where)]
            side, cells = r["side"], r["cells"]
            px = 88 // max(side, 1)
            rects = "".join(
                f'<rect x="{(i % side) * px}" y="{(i // side) * px}" width="{px - 1}" height="{px - 1}" fill="{KIND_COLOR[int(k)]}"/>'
                for i, k in enumerate(cells[: side * side]) if k != "0")
            name = "top line in the stands" if where == "stand" else "top line on the mid-latitude lawn"
            cards.append(f"""<figure class="card"><svg viewBox="-1 -1 89 89" width="104" height="104" role="img" aria-label="{name}, seed {s}">
<rect x="-1" y="-1" width="89" height="89" fill="var(--grid)"/>{rects}</svg>
<figcaption><strong>{name}, seed {s}</strong><br>lineage {r['lineage']}: {r['n']} of {r['of']} bodies, mean |latitude| {r['lat']:.0f}<br>
{r['hard']} hard, {r['muscle']} muscle, {r['gut']} gut; kills {r['kills']:.0%} of its food</figcaption></figure>""")
    return f"""<figure class="diagram"><div class="cards">{"".join(cards)}</div>
<figcaption>Figure {n}. {html.escape(caption)}</figcaption></figure>"""


def main():
    xs, prof = year_profile()
    g = bands()
    cen, bodies = census()
    lats = sorted({k[0] for k in g})
    mid = [l + 5 for l in lats]

    def per(k, c, q, i, div):
        v = g.get((k, c, q))
        return v[i] / v[div] if v and v[div] else float("nan")

    charts1 = [
        line_x("The land's crowd falls twice a year", "e075's kept runs by phase of the year, 3 seeds pooled; a flat line would be no season.",
               xs, [("land", prof["pop_land"], 0), ("surface", prof["pop_surface"], 1), ("bottom", prof["pop_bottom"], 2)],
               "phase of the year", "bodies"),
        line_x("While the world's grass grows nearly flat", "Grass grown a step on all land (matter units); the land's day-mean temperature is 18-24.5 C.",
               xs, [("grass grown", prof["grass_grown"], 3)], "phase of the year"),
    ]
    charts2 = [
        line_x("The lawn stops growing in winter, from 20 degrees out", "Grass grown a lawn cell per 1,000 steps by quarter. Lines apart = a season.",
               mid, [(QUARTERS[q], [per(l, 0, q, 0, 1) for l in lats], q) for q in range(4)], "latitude (degrees)"),
        line_x("Summer is too hot, winter too cold", "Mean temperature of the lawn by quarter; the shaded band is the comfort range, 15-30 C.",
               mid, [(QUARTERS[q], [per(l, 0, q, 2, 4) for l in lats], q) for q in range(4)], "latitude (degrees)", "C", band=(15, 30)),
    ]
    charts3 = [
        line_x("Lawn bodies come in the spring and autumn only", "Bodies on lawn cells, mean at a log row, by quarter.",
               mid, [(QUARTERS[q], [per(l, 0, q, 3, 4) for l in lats], q) for q in range(4)], "latitude (degrees)", "bodies"),
        line_x("Stand bodies stay put through the year", "Bodies on cells with wood of 1 or more, same rows. Lines together = no season.",
               mid, [(QUARTERS[q], [per(l, 2, q, 3, 4) for l in lats], q) for q in range(4)], "latitude (degrees)", "bodies"),
    ]
    charts4 = [
        scatter_x("The stands' share doubles at the solstices", "Share of the land's bodies on a stand, a census every 1,000 steps from 36,000.",
                  [(f"seed {s}", [p for p, _, _ in cen[s]], [sh for _, _, sh in cen[s]], i) for i, s in enumerate(SEEDS)], "phase of the year", pct=True),
        scatter_x("Because the land's crowd halves", "Land bodies at the same censuses.",
                  [(f"seed {s}", [p for p, _, _ in cen[s]], [n for _, n, _ in cen[s]], i) for i, s in enumerate(SEEDS)], "phase of the year"),
    ]
    tot = {c: [sum(v[0] for k, v in g.items() if k[1] == c and k[2] == q) for q in range(4)] for c in range(3)}
    totb = {c: [sum(v[3] for k, v in g.items() if k[1] == c and k[2] == q) for q in range(4)] for c in range(3)}
    table = "".join(
        f"<tr><td>{name}</td><td>{min(tot[c]) / max(tot[c]):.2f}</td>" + "".join(f"<td>{x:,.0f}</td>" for x in totb[c]) + "</tr>"
        for c, name in ((0, "lawn (wood under 0.1)"), (1, "thin wood (0.1-1)"), (2, "stand (1 or more)")))
    gal = gallery(bodies, "The largest lineage in the stands and on the mid-latitude lawn (20 degrees and out) at step 60,000, "
                          "its commonest body. Blue hard, orange muscle, yellow sensor, aqua gut.", n=2)
    appendix = "".join(
        f"<details><summary>seed {s}: census phase / land bodies / share on a stand</summary><div class='tw'><table><thead><tr><th>phase</th><th>land bodies</th><th>in a stand</th></tr></thead><tbody>"
        + "".join(f"<tr><td>{p:.2f}</td><td>{n:,}</td><td>{sh:.0%}</td></tr>" for p, n, sh in cen[s]) + "</tbody></table></div></details>"
        for s in SEEDS)
    page = TEMPLATE.format(CSS=CSS, DIAGRAM=DIAGRAM, GALLERY=gal, TABLE=table, APPENDIX=appendix,
                           CHARTS1="".join(charts1), CHARTS2="".join(charts2), CHARTS3="".join(charts3), CHARTS4="".join(charts4))
    with open(os.path.join(HERE, "report.html"), "w") as f:
        f.write(page)
    words = len(TEXT.split())
    print(f"report.html written; TEXT {words} words")


TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>e077 Where the season bites - Report</title>
<style>{CSS}</style>
</head>
<body>
<main>
<h1>e077: does the season take the lawn away?</h1>
<p class="sub">Experiment report - 2026-09-19 - #91 step 0: e075's kept runs read by season, and 3 measuring runs of 60,000 steps on c1225, seeds 9-11</p>

<section class="tldr">
<h2>TL;DR</h2>
<p>Yes, but not where one would look. World-wide the lawn's growth moves 22% over the year. From 20 degrees
of latitude out it is lost twice a year: to cold in winter and to heat in summer, when the grass stands
uneaten. The land's crowd falls from 5,000 to 2,900 at each solstice. The stands, in the tropics next
door, keep their bodies all year but are no cooler than the lawn. Next: a crown that buffers the heat.</p>
</section>

<h2>1. Question</h2>
<p>#91 asks whether a standing forest can be a refuge: a place worth less than the lawn most of the year
and more when the season turns. It pays when the season takes the lawn away (A) and the stand keeps what
the lawn loses (B). (B) is not built. This step measures (A) first; written after the dry run, before the
measuring runs:</p>
<ol>
  <li><strong>World-wide</strong>, the lawn's growth differs by less than a third between its best and worst quarter.</li>
  <li><strong>Poleward only</strong>: the worst quarter falls under half the best only past 40 degrees.</li>
  <li><strong>Nobody moves</strong>: the share of land bodies in a stand moves by less than 5 points over the year.</li>
</ol>

<h2>2. Method</h2>
<p>No law. e075's binary, with measures added; its log matches e075's kept run byte for byte.</p>
{DIAGRAM}
<p><strong>Runs.</strong> The dry run bins e075's logs (3 seeds, 100,000 steps) by phase of the year (11,880
steps). Then three runs of 60,000 steps, 3 cores for 25 minutes. We record:</p>
<ul class="measures">
  <li><strong>Lawn, thin wood, stand</strong> - a land cell with wood under 0.1, 0.1-1, 1 or more.</li>
  <li><strong>Bands</strong> - 10 degrees of latitude, every 1,000 steps: grass grown, temperature, bodies.</li>
  <li><strong>Census</strong> - every body and the wood under it, every 1,000 steps for two years.</li>
</ul>
{GALLERY}

<h2>3. Results</h2>
<div class="tw"><table>
<thead><tr><th>land</th><th>growth, worst/best quarter</th><th>bodies, phase 0</th><th>0.25</th><th>0.5</th><th>0.75</th></tr></thead>
<tbody>{TABLE}</tbody></table></div>
<p>Bodies are summed over the log's rows in each quarter, seeds pooled.</p>
<ol class="verdicts">
<li><span class="verdict">Yes</span> <strong>World-wide:</strong> the lawn's worst quarter grows 0.78 of its best.</li>
<li><span class="verdict partly">Partly</span> <strong>Poleward:</strong> under half from 20 degrees out, not 40, where up to 2,400 bodies live.</li>
<li><span class="verdict no">No</span> <strong>Nobody moves:</strong> the stands' share moves 30 points, but only because the lawn empties; stand bodies hold within 9%.</li>
</ol>

<h3>3.1 The land's crowd breathes twice a year</h3>
<div class="grid2">
{CHARTS1}
</div>
<p>The swing is the land's alone and has two troughs, one at each solstice. Food cannot be the cause:
standing grass is highest when the land holds fewest bodies.</p>

<h3>3.2 The mid-latitude lawn is lost to cold and then to heat</h3>
<div class="grid2">
{CHARTS2}
</div>
<p>In winter the lawn from 20 degrees out grows almost nothing. In summer it grows best, but its mean is
35-38 C, above the 30 C where a body starts paying water to cool. Either way the lawn is habitable in
its spring and autumn only.</p>

<h3>3.3 The stands keep their own; nobody comes in</h3>
<div class="grid2">
{CHARTS3}
</div>
<div class="grid2">
{CHARTS4}
</div>
<p>Stand bodies are the same in every quarter. The lawn's crowd rises and falls by births and deaths in
place: a body lives about 140 steps, 1/80 of a year, so no body could walk with the season. On seeds 9
and 11 one hunting line leads both the stands and the lawn (Figure 2): a line already spans both.</p>

<h2>4. Discussion</h2>
<p>(A) is there, in this world's conditions: a heat law with a comfort band of 15-30 C, a 75-step day, and
lives 1/80 of a year long. The season takes the mid-latitude lawn twice, and the stands are within a
life's travel of it.</p>
<p>What the stand lacks is (B). It is as hot as the lawn beside it, so in the summer it offers nothing
the lawn lost, and in winter nothing grows under it that the lawn's bodies could live on. The refuge,
if it comes, is a line kept in the stand through the bad quarter that spreads back out, not a body
that walks.</p>
<p>This does not show that a buffered crown would make such a line; only that heat, not food, is where
the stand could differ.</p>

<h2>5. Conclusion and next step</h2>
<p>The season takes the lawn away, twice a year, to cold and to heat. #91 step 1 builds (B) with the heat
first: a crown that damps the cell's temperature a body feels, as one rate, with the water held under
shade as the second, searched on seed 9 against e075's kept runs.</p>

<h2>Appendix: data</h2>
<p>The census by seed. Everything is in <code>results/*_bands.csv</code>, <code>*_agents.csv</code> and
<code>*_log.csv</code>; the dry run's scripts are <code>dryrun.py</code>, <code>profile.py</code> and
<code>census.py</code>, the measuring runs' <code>analyze.py</code>. Build with
<code>uv run python experiments/e077_refuge/report.py</code>.</p>
{APPENDIX}
</main>
</body>
</html>
"""

TEXT = TEMPLATE  # the words of the page, for the budget


if __name__ == "__main__":
    main()
