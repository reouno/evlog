#!/usr/bin/env python3
"""Build report.html for e108 (#127): the ground on the small world.

Charts: matplotlib, exported as SVG and inlined. Diagram: hand-written SVG.
Run from the repo root: uv run python experiments/e108_islands/report.py
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
    fig, ax = plt.subplots(figsize=(6.4, 4.6))
    a = np.ma.masked_array(img, mask=mask) if mask is not None else img
    im = ax.imshow(a, cmap=cmap, norm=norm, interpolation="nearest", origin="lower")
    if overlay is not None:
        ax.imshow(np.ma.masked_array(np.ones_like(overlay, dtype=float), mask=~overlay), cmap=ListedColormap(["#4da3ff"]), interpolation="nearest", origin="lower")
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


# Hand-written mechanism diagram: the air's pass over an island.
DIAGRAM = """
<figure class="diagram">
<svg viewBox="0 0 720 250" role="img" aria-label="Sea air enters at the windward border, climbs an island, rains on the high ground and leaves dry on the lee" style="max-width:100%;height:auto;display:block">
<defs><marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="currentColor"/></marker>
<marker id="arra" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="var(--s1)"/></marker></defs>
<g fill="none" stroke="currentColor" stroke-width="1.4" font-size="12" font-family="system-ui, sans-serif">
  <path d="M20,205 L250,205 L330,150 L400,95 L450,120 L520,205 L700,205"/>
  <path d="M20,205 L250,205 M520,205 L700,205" stroke-dasharray="3 4"/>
  <text x="60" y="225" fill="currentColor" stroke="none">sea, 20.8 C</text><text x="600" y="225" fill="currentColor" stroke="none">sea</text>
  <text x="372" y="172" text-anchor="middle" fill="currentColor" stroke="none">island</text><text x="372" y="188" text-anchor="middle" fill="currentColor" stroke="none">2 km, 13 C colder on top</text>
  <path d="M30,60 L225,60" stroke="var(--s1)" marker-end="url(#arra)"/><text x="30" y="46" fill="var(--s1)" stroke="none">sea air enters at the border, 5.5 m/s</text>
  <path d="M235,60 C300,55 350,40 395,36" stroke="var(--s1)" marker-end="url(#arra)"/><text x="255" y="24" fill="var(--s1)" stroke="none">lifted: holds less</text>
  <path d="M405,38 C470,45 520,60 590,62" stroke="var(--s1)" marker-end="url(#arra)"/><text x="500" y="36" fill="var(--s1)" stroke="none">sinks: holds more, dry</text>
  <path d="M340,58 L340,128" marker-end="url(#arr)" stroke-dasharray="2 4"/><path d="M385,50 L385,92" marker-end="url(#arr)" stroke-dasharray="2 4"/><path d="M430,56 L430,100" marker-end="url(#arr)" stroke-dasharray="2 4"/>
  <text x="452" y="84" fill="currentColor" stroke="none">rain: the excess</text><text x="452" y="100" fill="currentColor" stroke="none">falls in 1,000 s</text>
  <path d="M130,200 L130,74" marker-end="url(#arr)"/><text x="138" y="140" fill="currentColor" stroke="none">takes up water</text>
  <path d="M492,172 L575,200" marker-end="url(#arr)"/><text x="540" y="168" fill="currentColor" stroke="none">streams: 96% of the rain</text>
</g>
</svg>
<figcaption>Figure 1. The air's pass. The wind crosses the 64 km world within one update, so the air is followed
from the windward border across every cell, upwind first. It takes up water by its deficit and rains what it cannot
hold; what it can hold falls with the height the land lifts it, for the twentieth of its water in the lifted layer.
The same sea air sets 85% of a land cell's temperature.</figcaption>
</figure>
"""


def bands_chart(m):
    los = [0, 100, 300, 600, 1000]
    labels = ["0-100 m", "100-300", "300-600", "600-1,000", "over 1,000"]
    return bar_chart("Rain rises with height, and differs at one height",
                     "A year's rain on the land of each height band: the 10th, 50th and 90th percentile, mm.",
                     labels, [("driest tenth", [float(m[f"h{h}_rain_p10"]) for h in los], 1),
                              ("median", [float(m[f"h{h}_rain_p50"]) for h in los], 0),
                              ("wettest tenth", [float(m[f"h{h}_rain_p90"]) for h in los], 2)], xlabel="height")


def main():
    m = next(csv.DictReader(open(os.path.join(HERE, "results", "measure.csv"))))
    isl = [r for r in csv.DictReader(open(os.path.join(HERE, "results", "islands.csv"))) if float(r["km2"]) >= M.BIG]
    log = list(csv.DictReader(open(M.PREFIX + "_log.csv")))
    n, years, y, st = M.load(M.PREFIX)
    sea = (st["sea"] > 0).reshape(n, n)
    mean = {f: v.mean(axis=0).reshape(n, n) for f, v in y.items()}
    streams = (mean["discharge"] >= M.STREAM) & ~sea
    f = float

    charts = [
        map_fig("Eight islands, and their streams",
                "Height in m; blue: cells carrying 0.1 m3/s or more. North is up, the wind blows to the lower left.",
                np.maximum(st["elev"].reshape(n, n), 0), "terrain", norm=None, mask=sea, label="m", overlay=streams),
        map_fig("Rain, a year's mean",
                "mm a year over the last 10 years, sea included (log scale). It sits on the high ground.",
                np.maximum(mean["rain"], 1), "viridis", norm=LogNorm(50, 6000), label="mm a year"),
        map_fig("Temperature, a year's mean",
                "C, land only. It follows height: 6.5 C a km under the sea air.",
                mean["temp"], "coolwarm", mask=sea, label="C"),
        map_fig("Light, a year's mean",
                "The sun's mean height on each slope, land only: slopes that face it get twice the light.",
                mean["light"], "magma", mask=sea, label="light"),
        bands_chart(m),
        bar_chart("The windward lowland is wetter than the lee",
                  "A year's rain on the land under 200 m of each large island, upwind half and downwind half, mm.",
                  [f"{f(r['km2']):.0f} km2" for r in isl],
                  [("windward half", [f(r["low_windward_rain"]) for r in isl], 0), ("lee half", [f(r["low_lee_rain"]) for r in isl], 1)], xlabel="island"),
        line_chart("Years differ, and nearly all the rain runs off",
                   "Rain on the land and what the streams bring to the sea, mm a year. The first ten years the sea warms.",
                   [int(r["year"]) for r in log], [("rain on land", [f(r["land_rain"]) for r in log], 0),
                                                    ("runoff to the sea", [f(r["to_sea"]) for r in log], 1)], "year"),
        bar_chart("By the planet's bands the land is one place in four",
                  "Effective number of places on the land (Hill, order 1), by climate alone and with chemistry.",
                  ["climate bands", "with chemistry"],
                  [("the planet (e102)", [6.4, 15.4], 3), ("the small world", [f(m["land_places_e061"]), f(m["land_places_chemistry"])], 0)],
                  fmt=lambda v, _p: f"{v:g}"),
    ]

    verdict = lambda k: "" if m[k] == "yes" else " no"
    word = lambda k: "Yes" if m[k] == "yes" else "No"
    table = [("ledgers: water / A / the air's pass (worst year)", f"{f(m['water_err']):.0e} / {f(m['a_err']):.0e} / {f(m['air_err']):.0e}"),
             ("land, km2 (islands over 20 km2)", f"{f(m['land_km2']):.0f} ({m['islands_big']})"),
             ("sea between the large islands, km", f"{f(m['sea_narrowest_km']):.1f} - {f(m['sea_widest_km']):.1f}"),
             ("rain on land / runoff, mm a year", f"{f(m['land_rain_mm']):,.0f} / {f(m['to_sea_mm']):,.0f} ({f(m['runoff_ratio']):.0%})"),
             ("land carrying 0.1 / 1 m3/s", f"{f(m['stream_share']):.1%} / {f(m['river_share']):.2%}"),
             ("rain across the land, p10 - p90", f"{f(m['rain_p10']):.0f} - {f(m['rain_p90']):,.0f} mm"),
             ("rain against height, correlation", f"{f(m['rain_height_corr']):.2f}"),
             ("windward over lee lowland rain (median island)", f"x{f(m['low_windward_over_lee']):.1f}"),
             ("year's mean temperature, p5 - p95", f"{f(m['temp_p5']):.1f} - {f(m['temp_p95']):.1f} C"),
             ("light on a slope, p5 - p95", f"{f(m['light_p5']):.2f} - {f(m['light_p95']):.2f}"),
             ("soil in the wet band (fill over 2/3)", f"{f(m['fill_wet']):.0%}"),
             ("A:B / A + B, p90 over p10", f"x{f(m['ab_span']):.0f} / x{f(m['fertility_span']):.0f}"),
             ("a cell's rain between years (CV, median)", f"{f(m['rain_cv_median']):.0%}"),
             ("places on the land: climate bands / with chemistry", f"{f(m['land_places_e061']):.1f} / {f(m['land_places_chemistry']):.1f}")]
    summary = "".join(f"<tr><td>{k}</td><td>{v}</td></tr>" for k, v in table)
    isltab = ("<details><summary>The islands of 20 km2 and more</summary><div class='tw'><table><thead><tr>"
              + "".join(f"<th>{h}</th>" for h in ["km2", "peak m", "coldest C", "rain mean", "windward low", "lee low", "A:B median", "stream cells"])
              + "</tr></thead><tbody>"
              + "".join(f"<tr><td>{f(r['km2']):.0f}</td><td>{f(r['peak_m']):.0f}</td><td>{f(r['temp_min']):.1f}</td><td>{f(r['rain_mean']):.0f}</td>"
                        f"<td>{f(r['low_windward_rain']):.0f}</td><td>{f(r['low_lee_rain']):.0f}</td><td>{f(r['ab_median']):.2f}</td><td>{r['streams']}</td></tr>" for r in isl)
              + "</tbody></table></div></details>")
    logtab = ("<details><summary>The log, a row a year</summary><div class='tw'><table><thead><tr>"
              + "".join(f"<th>{h}</th>" for h in ["year", "land C", "rain", "evap", "to sea", "streams", "lakes", "water err"])
              + "</tr></thead><tbody>"
              + "".join(f"<tr><td>{r['year']}</td><td>{f(r['land_temp']):.1f}</td><td>{f(r['land_rain']):.0f}</td><td>{f(r['land_evap']):.0f}</td>"
                        f"<td>{f(r['to_sea']):.0f}</td><td>{r['rivers']}</td><td>{r['lakes']}</td><td>{f(r['water_err']):.0e}</td></tr>" for r in log)
              + "</tbody></table></div></details>")

    text = TEXT
    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>e108 The ground on the small world - Report</title>
<style>{CSS}</style>
</head>
<body>
<main>
<h1>e108: the ground on the small world</h1>
<p class="sub">Experiment report - 2026-10-05 - rung 1 again, on the chosen scale (#127): islands in a sea, climate from height, wind and season; one world, 30 years</p>

<section class="tldr">
<h2>TL;DR</h2>
<p>{text['tldr']}</p>
</section>

<h2>1. Question</h2>
<p>{text['question']}</p>
<ol>
  <li><strong>The ledgers close</strong> - water, both nutrients and the air's pass, to 1e-9.</li>
  <li><strong>Streams reach the sea</strong> - 1% of the land at 0.1 m3/s, the land's water steady.</li>
  <li><strong>Chemistry differs</strong> - A:B and A + B each span x4.</li>
  <li><strong>Years differ without drifting</strong> - consecutive rain maps correlate 0.2-0.95.</li>
  <li><strong>Places</strong> - at least the planet's 15.4 by its own bands.</li>
</ol>

<h2>2. The world</h2>
<p>{text['world']}</p>
{DIAGRAM}
<p><strong>Runs.</strong> {text['runs']}</p>
<ul class="measures">
  <li><strong>Ledgers</strong> - water and each nutrient against what crossed the edges.</li>
  <li><strong>Discharge</strong> - water leaving a cell; 74 mm an update is 0.1 m3/s.</li>
  <li><strong>Windward and lee</strong> - each island's lowland, halved along the wind.</li>
  <li><strong>Places</strong> - Hill number of area shares over e102's bands.</li>
</ul>

<h2>3. Results</h2>
<div class="tw"><table><thead><tr><th>measure (last 10 years)</th><th>value</th></tr></thead><tbody>{summary}</tbody></table></div>
<ol class="verdicts">
<li><span class="verdict{verdict('H1')}">{word('H1')}</span> {text['v1']}</li>
<li><span class="verdict{verdict('H2')}">{word('H2')}</span> {text['v2']}</li>
<li><span class="verdict{verdict('H3')}">{word('H3')}</span> {text['v3']}</li>
<li><span class="verdict{verdict('H4')}">{word('H4')}</span> {text['v4']}</li>
<li><span class="verdict{verdict('H5')}">{word('H5')}</span> {text['v5']}</li>
</ol>

<h3>3.1 Rain is where the land is high</h3>
<div class="grid2">
{charts[0]}
{charts[1]}
{charts[4]}
{charts[5]}
</div>
<p>{text['r1']}</p>

<h3>3.2 Height sets the heat, a slope its light</h3>
<div class="grid2">
{charts[2]}
{charts[3]}
</div>
<p>{text['r2']}</p>

<h3>3.3 The land keeps none of its rain, and the planet's bands see one place</h3>
<div class="grid2">
{charts[6]}
{charts[7]}
</div>
<p>{text['r3']}</p>

<h2>4. Discussion</h2>
<p>{text['d1']}</p>
<p>{text['d2']}</p>

<h2>5. Conclusion and next step</h2>
<p>{text['conclusion']}</p>

<h2>Appendix: data</h2>
<p>All readings in <code>results/measure.csv</code>, the islands in <code>results/islands.csv</code>, the place types
in <code>results/places.csv</code>, thresholds in <code>results/provenance.csv</code>. The maps
(<code>results/isles1_maps.bin</code>) are rebuilt by the run in 7 minutes. Build:
<code>uv run python experiments/e108_islands/report.py</code>.</p>
{isltab}
{logtab}
</main>
</body>
</html>
"""
    out = os.path.join(HERE, "report.html")
    with open(out, "w") as fh:
        fh.write(page)
    words = {k: len(v.split()) for k, v in TEXT.items()}
    print(f"wrote {out} ({os.path.getsize(out)//1024} KB); words {sum(words.values())}: {words}")


TEXT = {
    "tldr": "The planet is replaced by 64 km of sea holding 410 km2 of islands, and the ground is rebuilt on it, the air followed across the world in one pass. It stands: every ledger closes, streams run from every island, the chemistry parts the land. By the planet's bands it holds 4.5 places, not 15.4 - no cold ground, and bare soil that is full everywhere. Whether rain x15 and 10 C of height are places is the producers' to show next.",
    "question": "On a planet a body stood for millions of animals, so a small world was chosen (#126). The ground's laws read the planet's size in several places. Rewritten for cells of 125 m, does the ground still stand and make places, and do e102's two faults - rain recycled over the land, mild years - remain? Five lines, e102's:",
    "world": "<code>base/</code> copied. A border of sea; one latitude and one hour; a slope's light by its tilt; the sea air setting most of a land cell's temperature; a wind that turns with season, year and day; and the air's pass.",
    "runs": "Sixteen terrain seeds, one chosen for five islands over 20 km2 (964 to 2,002 m high). One world, 30 years, nothing living on it, 7 minutes on four threads; the last 10 years read. Every rewritten rate was set from its units before the run and none changed after it.",
    "v1": "All close: water 3e-13, the air's pass 1e-13.",
    "v2": "6.8% of the land carries 0.1 m3/s; the land's water drifts -0.6% a year.",
    "v3": "A:B spans x9, A + B x68.",
    "v4": "As written: rain maps correlate 0.99, the fixed pattern. A cell's rain varies 17% between years; the trend is the world-wide anomaly.",
    "v5": "4.5 places on the land by the planet's bands, against 15.4.",
    "r1": "Height explains most of the rain (correlation 0.91), but not all: lowland of one height differs elevenfold, and the upwind half of an island's lowland gets twice the downwind half's. The wet side is weaker than designed - the excess takes 5.5 km to fall, half an island, so it lands on the crest.",
    "r2": "The land is mild because its air is the sea's: a cell's seasons differ by 6.6 C, and 13 C separates shore from summit. Light is the sharper difference at this grain - neighbouring slopes get 0.13 and 0.30.",
    "r3": "On the planet the land rained 90% of its water back; here 96% runs off, since what the land gives the air leaves with the wind. It gives little - 73 mm a year - so bare soil stays full. The planet's bands part temperature at 5 and 20 C and soil water in thirds: this land sits in one of each.",
    "d1": "The count fails for two reasons that more land or more height would not mend. A cold band needs ground over 2.4 km, a few per cent of any island. Moisture bands need something to draw the soil down, and on a mild humid island only plants can: the drier lowlands get 53-250 mm a year.",
    "d2": "So the judgement moves to the next rung. If producers sort by rain, height and light, and the soil's fill then differs, these are places. If not, the remedy is the climate's - the sea air's share of a cell's temperature, the latitude - not the land's size. One world was run; no storm came in 30 years.",
    "conclusion": "The ground stands on the small world and goes into <code>base/</code>. The planet's water fault is gone and years vary more. Places are not shown by the old count. Next: producers on these islands, their distances rewritten in metres.",
}


if __name__ == "__main__":
    main()
