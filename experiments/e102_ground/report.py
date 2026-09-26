#!/usr/bin/env python3
"""Build report.html for e102 (#116 rung 1): the ground of the island.

Charts: matplotlib, exported as SVG and inlined. Diagram: hand-written SVG.
Run from the repo root: uv run python experiments/e102_ground/report.py
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


# ---------- this experiment's data ----------

def rows(path):
    with open(os.path.join(HERE, path)) as f:
        return list(csv.DictReader(f))


def bar_chart(title, subtitle, labels, series, xlabel="", pct=False, fmt=None):
    """series: list of (label, values, slot). One group of bars per label."""
    fig, ax = plt.subplots(figsize=(6.4, 2.6))
    n = len(series)
    width = 0.8 / n
    for i, (name, values, slot) in enumerate(series):
        xs = [j + (i - (n - 1) / 2) * width for j in range(len(labels))]
        ax.bar(xs, values, width=width * 0.92, color=SERIES[slot], label=name)
    ax.set_xticks(range(len(labels)), labels)
    ax.set_xlabel(xlabel, loc="right")
    ax.yaxis.set_major_locator(MaxNLocator(4, integer=not pct))
    ax.yaxis.set_major_formatter((lambda y, _p: f"{y:.0%}") if pct else (fmt or kfmt))
    legend_above(ax, n)
    return figure(title, subtitle, to_svg(fig))


# ---------- chart helpers ----------

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


def map_fig(title, subtitle, img, cmap, norm=None, label="", mask=None, overlay=None, ticks=None, ticklabels=None):
    """A world map as a PNG inside the figure (a 512x512 field is too large for SVG)."""
    fig, ax = plt.subplots(figsize=(6.4, 3.4))
    a = np.ma.masked_array(img, mask=mask) if mask is not None else img
    im = ax.imshow(a, cmap=cmap, norm=norm, interpolation="nearest")
    if overlay is not None:
        ax.imshow(np.ma.masked_array(np.ones_like(overlay, dtype=float), mask=~overlay), cmap=ListedColormap(["#1f5fff"]), interpolation="nearest")
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


def line_chart(title, subtitle, xs, series, xlabel, ylabel_fmt=None):
    fig, ax = plt.subplots(figsize=(6.4, 2.6))
    for label, ys, slot in series:
        ax.plot(xs, ys, color=SERIES[slot], linewidth=1.8, label=label)
    ax.set_xlabel(xlabel, loc="right")
    ax.set_ylim(0, None)
    ax.yaxis.set_major_locator(MaxNLocator(4))
    ax.yaxis.set_major_formatter(ylabel_fmt or kfmt)
    ax.margins(x=0)
    legend_above(ax, len(series))
    return figure(title, subtitle, to_svg(fig))


# Hand-written mechanism diagram: the two cycles of the ground.
DIAGRAM = """
<figure class="diagram">
<svg viewBox="0 0 720 255" role="img" aria-label="Water from the sea through the air, the soil and the rivers back to the sea; nutrients from the rock through the soil and the rivers to the sea" style="max-width:100%;height:auto;display:block">
<defs><marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="currentColor"/></marker>
<marker id="arra" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="var(--s1)"/></marker></defs>
<g fill="none" stroke="currentColor" stroke-width="1.4" font-size="12" font-family="system-ui, sans-serif">
  <rect x="20" y="20" width="120" height="44" rx="6"/><text x="80" y="47" text-anchor="middle" fill="currentColor" stroke="none">air</text>
  <rect x="20" y="170" width="120" height="44" rx="6"/><text x="80" y="197" text-anchor="middle" fill="currentColor" stroke="none">sea</text>
  <rect x="260" y="95" width="150" height="44" rx="6"/><text x="335" y="114" text-anchor="middle" fill="currentColor" stroke="none">soil</text><text x="335" y="130" text-anchor="middle" fill="currentColor" stroke="none">water, A, B</text>
  <rect x="260" y="190" width="150" height="40" rx="6"/><text x="335" y="215" text-anchor="middle" fill="currentColor" stroke="none">rivers and lakes</text>
  <rect x="540" y="95" width="150" height="44" rx="6" stroke="var(--s1)"/><text x="615" y="114" text-anchor="middle" fill="var(--s1)" stroke="none">rock province</text><text x="615" y="130" text-anchor="middle" fill="var(--s1)" stroke="none">5 kinds, 48 provinces</text>
  <path d="M80,164 L80,70" marker-end="url(#arr)"/><text x="88" y="120" fill="currentColor" stroke="none">evaporates</text>
  <path d="M146,42 C220,42 300,55 330,90" marker-end="url(#arr)"/><text x="215" y="36" fill="currentColor" stroke="none">rains (5.5 m/s winds by band)</text>
  <path d="M534,117 L416,117" stroke="var(--s1)" marker-end="url(#arra)"/><text x="475" y="108" text-anchor="middle" fill="var(--s1)" stroke="none">weathers</text>
  <path d="M335,145 L335,184" marker-end="url(#arr)"/><text x="323" y="168" text-anchor="end" fill="currentColor" stroke="none">runs off, leaches A &gt; B</text>
  <path d="M254,210 L146,195" marker-end="url(#arr)"/><text x="245" y="242" text-anchor="end" fill="currentColor" stroke="none">to the sea: 10% of the rain</text>
  <path d="M410,210 C490,210 490,132 418,132" marker-end="url(#arr)"/><text x="500" y="178" fill="currentColor" stroke="none">drops where it slows</text>
</g>
</svg>
<figcaption>Figure 1. The two cycles of the ground. Water: the sea evaporates, winds by latitude band carry the air,
the rain fills a soil whose size is set by its rock and slope, and what is over runs down one drainage network to the
sea. Nutrients: each rock province weathers A and B at its own rates; the water that leaves a soil takes mobile A far
more than bound B, and the rivers drop what they carry where they slow.</figcaption>
</figure>
"""


def main():
    m = next(csv.DictReader(open(os.path.join(HERE, "results", "measure.csv"))))
    log = list(csv.DictReader(open(M.PREFIX + "_log.csv")))
    years, y, st = M.load(M.PREFIX)
    n = int(round(len(st["sea"]) ** 0.5))
    sea = (st["sea"] > 0).reshape(n, n)
    mean = {f: v.mean(axis=0).reshape(n, n) for f, v in y.items()}
    a, b = y["a"][-1].reshape(n, n), y["b"][-1].reshape(n, n)
    rivers = (mean["discharge"] >= 20) & ~sea
    f = float

    charts = [
        map_fig("Rock provinces, and the rivers on them",
                "Each colour a kind of rock; blue: cells carrying 20 mm an update or more (the last 10 years' mean).",
                st["rock"].reshape(n, n), ListedColormap(["#c9b18a", "#6f7f6a", "#d9d4c7", "#e0a458", "#8a6f9e"]),
                norm=BoundaryNorm([-0.5, 0.5, 1.5, 2.5, 3.5, 4.5], 5), mask=sea, label="", overlay=rivers,
                ticks=[0, 1, 2, 3, 4], ticklabels=["granite-like", "basalt-like", "limestone-like", "sandstone-like", "shale-like"]),
        map_fig("Rain, a year's mean",
                "mm a year over the last 10 years, land only. The bands of the winds and the relief set it.",
                np.maximum(mean["rain"], 1), "viridis", norm=LogNorm(10, 5000), mask=sea, label="mm a year"),
        map_fig("The soil's A:B",
                "The last year's ratio, land only (log scale). Low: B-rich rock or A washed out by the rain.",
                np.maximum(a / np.maximum(b, 1e-9), 1e-3), "coolwarm", norm=LogNorm(0.01, 3), mask=sea, label="A:B"),
        map_fig("Fertility, A + B",
                "The last year's total, land only (log scale). The rivers' drops show as rich valleys and basins.",
                np.maximum(a + b, 1e-2), "magma", norm=LogNorm(0.1, 30), mask=sea, label="A + B"),
    ]
    yr = [int(r["year"]) for r in log]
    charts.append(line_chart("The land's water settles in 10 years",
                             "Rain on the land and the part the rivers bring to the sea, mm a year per land cell.",
                             yr, [("rain on land", [f(r["land_rain"]) for r in log], 0),
                                  ("runoff to the sea", [f(r["to_sea"]) for r in log], 1)], "year"))
    labels = ["whole world", "land only"]
    charts.append(bar_chart("Chemistry parts the land",
                            "Effective number of places (Hill, order 1) by e061's bands and with A:B and fertility added.",
                            labels, [("e061's bands", [f(m["places_e061"]), f(m["land_places_e061"])], 0),
                                     ("with chemistry", [f(m["places_chemistry"]), f(m["land_places_chemistry"])], 2)],
                            fmt=lambda v, _p: f"{v:g}"))
    last = y["rain"][-1].reshape(n, n) / np.maximum(mean["rain"], 1)
    charts.append(map_fig("Year 30 against the mean",
                          "Each land cell's rain in year 30 over its 10-year mean. Years differ by place, not everywhere at once.",
                          last, "BrBG", norm=LogNorm(0.6, 1.6), mask=sea, label="x mean"))

    verdict = lambda k: "" if m[k] == "yes" else " no"
    word = lambda k: "Yes" if m[k] == "yes" else "No"
    table = [("water ledger (worst year)", f"{f(m['water_err']):.0e}"), ("nutrient A ledger", f"{f(m['a_err']):.0e}"),
             ("rain on land, mm a year", f"{f(m['land_rain_mm']):,.0f}"), ("runoff to the sea, mm a year", f"{f(m['to_sea_mm']):.0f}"),
             ("land carrying 100 / 50 / 20 mm an update", f"{f(m['river_share']):.2%} / {f(m['river_share_50']):.2%} / {f(m['river_share_20']):.1%}"),
             ("land water drift a year", f"{f(m['land_water_drift']):.1%}"),
             ("A:B, p10 - p90 (span)", f"{f(m['ab_p10']):.2f} - {f(m['ab_p90']):.2f} (x{f(m['ab_span']):.0f})"),
             ("A + B, p10 - p90 (span)", f"{f(m['ab_sum_p10']):.2f} - {f(m['ab_sum_p90']):.1f} (x{f(m['fertility_span']):.0f})"),
             ("consecutive years' rain maps, correlation", f"{f(m['rain_corr_mean']):.2f}"),
             ("a year's departure kept the next year", f"{f(m['rain_anom_corr']):.2f}"),
             ("a cell's rain between years (CV, median)", f"{f(m['rain_cv_median']):.0%}"),
             ("land temperature trend, C a year", f"{f(m['temp_trend']):+.3f}"),
             ("places: e061's bands / with chemistry", f"{f(m['places_e061']):.1f} / {f(m['places_chemistry']):.1f}"),
             ("land places: e061's bands / with chemistry", f"{f(m['land_places_e061']):.1f} / {f(m['land_places_chemistry']):.1f}")]
    summary = "".join(f"<tr><td>{k}</td><td>{v}</td></tr>" for k, v in table)
    logtab = ("<details><summary>The log, a row a year</summary><div class='tw'><table><thead><tr>"
              + "".join(f"<th>{h}</th>" for h in ["year", "land C", "rain", "evap", "to sea", "rivers (20 mm)", "lakes", "water err"])
              + "</tr></thead><tbody>"
              + "".join(f"<tr><td>{r['year']}</td><td>{f(r['land_temp']):.1f}</td><td>{f(r['land_rain']):.0f}</td><td>{f(r['land_evap']):.0f}</td>"
                        f"<td>{f(r['to_sea']):.0f}</td><td>{r['rivers']}</td><td>{r['lakes']}</td><td>{f(r['water_err']):.0e}</td></tr>" for r in log)
              + "</tbody></table></div></details>")

    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>e102 The ground - Report</title>
<style>{CSS}</style>
</head>
<body>
<main>
<h1>e102: the ground of the island</h1>
<p class="sub">Experiment report - 2026-09-26 - the redesign's first rung (#116): rock, nutrients, rivers and years, one world, 30 years</p>

<section class="tldr">
<h2>TL;DR</h2>
<p>The redesigned world starts with its ground, nothing living on it. Rock provinces give two nutrients at their
own rates, water washes the mobile one away, rivers carry both down, and every year's weather differs by place. It
stands: the ledgers close to 1e-13 and the land holds 15.4 places against 6.4 by the old bands. Two lines fail as
written: the rivers are thin (10% of the rain reaches the sea) and one measure of the years read the fixed pattern.
Next: evolving producers.</p>
</section>

<h2>1. Question</h2>
<p>The redesign raises the world's freedom by a jump, every form priced by physics. Its first rung asks whether the
ground alone can differ by more than heat and water - by rock, chemistry and rivers - and whether years stop being
one year repeated. Five lines, set before the run:</p>
<ol>
  <li><strong>The ledgers close</strong> - water and both nutrients, to 1e-9.</li>
  <li><strong>Rivers reach the sea</strong> - 1% of the land at 100 mm an update, the land's water steady.</li>
  <li><strong>Chemistry differs</strong> - A:B and A + B each span x4 between the 10th and 90th percentile.</li>
  <li><strong>Years differ without drifting</strong> - consecutive rain maps correlate 0.2-0.95.</li>
  <li><strong>More places</strong> than the same bands without chemistry.</li>
</ol>

<h2>2. The world</h2>
<p>New code (<code>base/</code>): e061's sun, heat and air, plus rock, soils, a drainage network, groundwater,
two nutrients, winds by latitude band, yearly anomalies and storms.</p>
{DIAGRAM}
<p><strong>Runs.</strong> c1225's terrain and climate, 30 years, the last 10 read. Four rates were set in a pilot by
their units, not searched: the wind (5.5 m/s), a soil's evaporation (0.3 of open water), runoff rising with the
soil's fill, and pits filled to 2 m lakes. Measured:</p>
<ul class="measures">
  <li><strong>Ledgers</strong> - water and each nutrient against what crossed the edges.</li>
  <li><strong>Discharge</strong> - water leaving a cell, a river's size.</li>
  <li><strong>A:B, A + B</strong> - the soil's chemistry and fertility.</li>
  <li><strong>Year departures</strong> - each year's rain over the cell's mean.</li>
  <li><strong>Places</strong> - Hill number of area shares over banded places.</li>
</ul>

<h2>3. Results</h2>
<div class="tw"><table><thead><tr><th>measure (last 10 years)</th><th>value</th></tr></thead><tbody>{summary}</tbody></table></div>
<ol class="verdicts">
<li><span class="verdict{verdict('H1')}">{word('H1')}</span> The ledgers close: water 4e-14, nutrients under 1e-13.</li>
<li><span class="verdict{verdict('H2')}">{word('H2')}</span> Rivers reach the sea but thin: 0.14% of the land at 100 mm an update, 1.7% at 20.</li>
<li><span class="verdict{verdict('H3')}">{word('H3')}</span> Chemistry differs: A:B spans x14, A + B x19.</li>
<li><span class="verdict{verdict('H4')}">{word('H4')}</span> As written: rain maps correlate 0.98 - the fixed pattern. The departures persist 0.46 and vary 12%.</li>
<li><span class="verdict{verdict('H5')}">{word('H5')}</span> More places: 15.4 on the land against 6.4.</li>
</ol>

<h3>3.1 Rock and water part the land</h3>
<div class="grid2">
{charts[0]}
{charts[2]}
{charts[3]}
{charts[5]}
</div>
<p>The rock sets the supply: A:B is 0.40 on the granite-like rock and 0.05 on the basalt- and limestone-like. The
water sets the loss: land under 300 mm of rain keeps its mobile A (0.52), land over 1,000 mm loses it (0.09-0.13).
The rivers' load gathers where they slow: A + B is 12.0 in the old basins against 1.7 elsewhere.</p>

<h3>3.2 The water settles, and runs off thin</h3>
<div class="grid2">
{charts[1]}
{charts[4]}
</div>
<p>Most of the land's rain goes back to the air within a day: the ground heats by day and the night rains on it.
The rivers are a real network, but at 10% runoff against Earth's 35% they are streams more than rivers.</p>

<h3>3.3 Years differ by place</h3>
<div class="grid2">
{charts[6]}
</div>
<p>A wet or dry year is a region, not the world, and half of it carries into the next year. A cell's rain varies
12% between years, about half of Earth's.</p>

<h2>4. Discussion</h2>
<p>The largest change is not the rivers but the chemistry: two nutrients with different mobility, from five rocks,
already give the land more than twice the places temperature and water gave it. It is the premise of the redesign
in its smallest form - a few simple parts, and a large space of outcomes, none written in.</p>
<p>What it does not show: that producers will use the places. A:B differs by x14 on land that no plant has yet
grown on; the next rung asks whether evolving producers part themselves along it. The thin rivers and mild years
are carried there, because producers change the land's water, and nothing is tuned before they do.</p>

<h2>5. Conclusion and next step</h2>
<p>The ground stands and its new freedom is used; it is <code>base/</code>'s first rung. Next is rung 2: producers
as evolving cohorts in the shared genome language - height, composition, defence, seeds - on this ground.</p>

<h2>Appendix: data</h2>
<p>All readings in <code>results/measure.csv</code>, the place types in <code>results/places.csv</code>, thresholds
in <code>results/provenance.csv</code>. The maps (<code>results/c1225_maps.bin</code>) are rebuilt by the run in
7 minutes. Build: <code>uv run python experiments/e102_ground/report.py</code>.</p>
{logtab}
</main>
</body>
</html>
"""
    out = os.path.join(HERE, "report.html")
    with open(out, "w") as fh:
        fh.write(page)
    print(f"wrote {out} ({os.path.getsize(out)//1024} KB)")


if __name__ == "__main__":
    main()
