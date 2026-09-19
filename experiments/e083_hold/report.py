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
SEEDS = ["9", "10", "11"]
RUNS = [("control", 5), ("fresh 0.05", 0), ("fresh 0.2", 2)]  # (run, colour slot); the control in gray
N, LAT_LO, LAT_HI = 512, -59.4, 87.0

def rows_of(path):
    with open(path) as f:
        return list(csv.DictReader(f))


def lat_of_row(y):
    return LAT_LO + (LAT_HI - LAT_LO) * (1 - abs(2 * (y + 0.5) / N - 1))


def seed_mean(rows, key, where):
    """{x: the mean over seeds of `key`} for the rows that pass `where`, keyed by their latitude."""
    acc = defaultdict(list)
    for r in rows:
        if where(r) and r[key] not in ("", "nan"):
            acc[float(r["lat"])].append(float(r[key]))
    return {x: sum(v) / len(v) for x, v in acc.items() if len(v) == len(SEEDS)}


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





def line_lat(title, subtitle, series, ylabel=None, pct=False, band=None):
    """series: list of (label, {latitude: value}, slot), drawn along the latitude."""
    fig, ax = new_axes("latitude (degrees; north is positive)")
    if band:
        ax.axvspan(band[0], band[1], color=INK, alpha=0.14, linewidth=0)
    for label, d, slot in series:
        xs = sorted(d)
        ax.plot(xs, [d[x] for x in xs], color=SERIES[slot], linewidth=1.6, label=label)
    if ylabel:
        ax.set_ylabel(ylabel)
    ax.yaxis.set_major_formatter((lambda y, _p: f"{y:.0%}") if pct else (lambda y, _p: f"{y:g}"))
    ax.yaxis.set_major_locator(MaxNLocator(4))
    legend_above(ax, len(series))
    return figure(title, subtitle, to_svg(fig))


def leader_map(title, subtitle, cells):
    """cells: {(gx, gy): (bodies, leader's)} on the 64 x 64 map. Blue: the leader; orange: other lines."""
    from matplotlib.colors import LinearSegmentedColormap
    import numpy as np
    share = np.full((64, 64), np.nan)
    for (gx, gy), (n, a) in cells.items():
        if n >= 20:
            share[gy, gx] = a / n
    cmap = LinearSegmentedColormap.from_list("lines", [SERIES[1], "#8a8580", SERIES[0]])
    cmap.set_bad((0, 0, 0, 0))
    fig, ax = plt.subplots(figsize=(4.6, 4.6))
    ax.imshow(share, cmap=cmap, vmin=0, vmax=1, interpolation="nearest", origin="upper")
    ax.grid(False)
    marks = [(g, lat_of_row(g * 8 + 4)) for g in range(64)]
    shown = []
    for want in (-40, 0, 40):
        for half in (0, 1):
            cand = [(abs(l - want), g) for g, l in marks if (g < 32) == (half == 0)]
            shown.append(min(cand)[1])
    ax.set_yticks(sorted(shown), [f"{lat_of_row(g * 8 + 4):.0f}" for g in sorted(shown)])
    ax.set_xticks([])
    ax.set_ylabel("latitude (the map holds each twice)")
    ax.axhline(31.5, color=INK, linewidth=0.8, linestyle=":")
    gy = lambda lat: (lat - LAT_LO) / (LAT_HI - LAT_LO) * 32 - 0.5  # noqa: E731  (the upper half's rows)
    ax.add_patch(plt.Rectangle((15.5, gy(-7)), 25, gy(12) - gy(-7), fill=False, edgecolor=INK, linewidth=1.0, linestyle="--"))
    ax.text(1, 2, "upper half", color=INK, fontsize=9, va="top")
    ax.text(1, 34, "lower half", color=INK, fontsize=9, va="top")
    return figure(title, subtitle, to_svg(fig))


DIAGRAM = """
<figure class="diagram">
<svg viewBox="0 0 780 230" role="img" aria-label="The leader's spread and the dry belt" style="max-width:100%;height:auto;display:block">
<defs><marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="currentColor"/></marker></defs>
<g fill="none" stroke="currentColor" stroke-width="1.2" font-size="12" font-family="system-ui, sans-serif">
  <rect x="10" y="60" width="190" height="80" rx="6"/>
  <text x="105" y="84" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">lower continent</text>
  <text x="105" y="103" text-anchor="middle" fill="currentColor" stroke="none">wet tropics, forest north</text>
  <text x="105" y="122" text-anchor="middle" fill="currentColor" stroke="none">the leader: 54-92%</text>
  <rect x="270" y="60" width="160" height="80" rx="6"/>
  <text x="350" y="84" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">upper south</text>
  <text x="350" y="103" text-anchor="middle" fill="currentColor" stroke="none">and tropics</text>
  <text x="350" y="122" text-anchor="middle" fill="currentColor" stroke="none">the leader spreads in</text>
  <rect x="470" y="50" width="100" height="100" rx="6" stroke="var(--s1)" stroke-width="2"/>
  <text x="520" y="80" text-anchor="middle" fill="var(--s1)" stroke="none" font-weight="600">dry belt</text>
  <text x="520" y="99" text-anchor="middle" fill="var(--s1)" stroke="none">-7 to 12 deg</text>
  <text x="520" y="118" text-anchor="middle" fill="var(--s1)" stroke="none">dryness 0.72</text>
  <text x="520" y="137" text-anchor="middle" fill="var(--s1)" stroke="none">1/3 the bodies</text>
  <rect x="610" y="60" width="160" height="80" rx="6"/>
  <text x="690" y="84" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">upper north</text>
  <text x="690" y="103" text-anchor="middle" fill="currentColor" stroke="none">soft grazers of</text>
  <text x="690" y="122" text-anchor="middle" fill="currentColor" stroke="none">other lines: 94-100%</text>
  <line x1="200" y1="100" x2="270" y2="100" marker-end="url(#arr)"/>
  <text x="235" y="160" text-anchor="middle" fill="currentColor" stroke="none">across the</text>
  <text x="235" y="176" text-anchor="middle" fill="currentColor" stroke="none">map's south edge</text>
  <line x1="430" y1="100" x2="470" y2="100" marker-end="url(#arr)"/>
  <line x1="570" y1="100" x2="610" y2="100" stroke-dasharray="4 4"/>
  <text x="590" y="185" text-anchor="middle" fill="currentColor" stroke="none">the leader stalls here: at fresh 0.05 wet ground</text>
  <text x="590" y="201" text-anchor="middle" fill="currentColor" stroke="none">gives 0.014 of a pool's drink, at 0.2 0.056</text>
</g>
</svg>
<figcaption>Figure 1. The land as the leading line meets it (control). It spreads from the lower continent across the
map's southern edge into the upper continent and stops in a dry belt near the equator (blue), where wet
ground gives almost nothing to drink. Beyond it other lines hold the upper north.</figcaption>
</figure>
"""


def main():
    reg = rows_of(os.path.join(RESULTS, "regions.csv"))
    tr = rows_of(os.path.join(RESULTS, "transect.csv"))
    tm = rows_of(os.path.join(RESULTS, "time.csv"))
    mp = rows_of(os.path.join(RESULTS, "maps.csv"))
    west = lambda run: (lambda r: r["run"] == run and r["side"] == "upper west" and -35 <= float(r["lat"]) <= 60)  # noqa: E731
    lower = lambda r: r["run"] == "control" and r["side"] == "lower" and -35 <= float(r["lat"]) <= 60  # noqa: E731
    belt = (-7, 12)
    maps = {}
    for run in ("control", "fresh 0.2"):
        maps[run] = {(int(r["gx"]), int(r["gy"])): (int(r["bodies"]), int(r["leader"])) for r in mp if r["run"] == run}
    charts = {
        "map_c": leader_map("The control: other lines hold the upper north",
                            "Land bodies over the censuses, seed 9, by blocks of 8 x 8 cells. Blue: the leading line; orange: other lines; dashed: the dry belt.", maps["control"]),
        "map_f": leader_map("Fresh 0.2: the leader holds it too",
                            "The same map with wet ground giving a fifth of a pool's drink (e082).", maps["fresh 0.2"]),
        "bodies": line_lat("Bodies thin out in a belt",
                           "Land bodies a land cell a census along the upper continent, mean of seeds 9-11. Shaded: the dry belt.",
                           [(run, seed_mean(tr, "bodies_cell", west(run)), k) for run, k in RUNS], "bodies a cell", band=belt),
        "share": line_lat("The leader stops in it",
                          "The leading line's share of the land bodies along the upper continent, mean of seeds 9-11.",
                          [(run, seed_mean(tr, "leader_share", west(run)), k) for run, k in RUNS], pct=True, band=belt),
        "dry": line_lat("The belt is the driest ground",
                        "The run's mean ground dryness (1 = dry), the control; the lower continent at the same latitudes for comparison.",
                        [("upper continent", seed_mean(tr, "ground_dry", west("control")), 0), ("lower continent", seed_mean(tr, "ground_dry", lower), 3)],
                        "ground dryness", band=belt),
    }
    ts = defaultdict(lambda: defaultdict(list))
    for r in tm:
        if r["side"] == "upper west" and r["zone"] in ("north", "tropics"):
            ts[(r["run"], r["zone"])][int(r["from_k"])].append(float(r["leader_share"]))
    xs = sorted(ts[("control", "north")])
    series = [(label, [sum(ts[key][x]) / len(ts[key][x]) for x in xs], k) for label, key, k in
              (("north (control)", ("control", "north"), 5), ("tropics (control)", ("control", "tropics"), 3), ("north (fresh 0.2)", ("fresh 0.2", "north"), 2))]
    charts["time"] = line_x("The boundary does not move",
                            "The leader's share in the upper continent's north and tropics per 16,000 steps, mean of seeds 9-11.",
                            xs, series, "step (thousands, window start)", pct=True, markers=True)
    # the two ways of living (control, the three seeds' mean)
    def avg(side, zone, who, key):
        v = [float(r[f"{who}_{key}"]) for r in reg if r["run"] == "control" and r["side"] == side and r["zone"] == zone and r.get(f"{who}_{key}") not in (None, "")]
        return sum(v) / len(v)
    kinds = [("locals in the upper north", "upper west", "north", "loc"), ("leader in the lower north", "lower", "north", "lead"),
             ("leader in the upper tropics", "upper west", "tropics", "lead"), ("locals in the upper tropics", "upper west", "tropics", "loc")]
    cols = [("born_size", "{:.1f}"), ("born_hard", "{:.1f}"), ("born_muscle", "{:.1f}"), ("born_digestive", "{:.1f}"), ("open_soft", "{:.1f}"),
            ("meat_share", "{:.0%}"), ("kids_1000", "{:.2f}"), ("water", "{:.2f}")]
    ways = "".join(f"<tr><td>{n}</td>" + "".join(f"<td>{fmt.format(avg(sd, zn, who, c))}</td>" for c, fmt in cols) + "</tr>" for n, sd, zn, who in kinds)
    held = "".join(
        f"<tr><td>{run}</td>" + "".join(f"<td>{float(next(r for r in reg if r['run'] == run and r['seed'] == s and r['side'] == sd and r['zone'] == 'north')['leader_share']):.0%}</td>"
                                         for sd in ("upper west", "lower") for s in SEEDS) + "</tr>" for run, _ in RUNS)
    cols_a = ["bodies_cell", "leader_share", "ground_dry", "air_dry", "lead_kids_1000", "loc_kids_1000", "lead_water", "loc_water", "lead_warmed_turn", "loc_warmed_turn"]
    order = [(f"{r['run']} s{r['seed']} {r['side']} {r['zone']}", r) for r in reg if r["zone"] in ("tropics", "north")]
    appendix = ("<details><summary>Every place of every run (lead: the leader's bodies; loc: the other lines')</summary><div class='tw'><table><thead><tr><th>run, seed, place</th>"
                + "".join(f"<th>{c}</th>" for c in cols_a) + "</tr></thead><tbody>"
                + "".join(f"<tr><td>{n}</td>" + "".join(f"<td>{float(r[c]):.3g}</td>" if r.get(c) not in (None, '', 'nan') else "<td>-</td>" for c in cols_a) + "</tr>" for n, r in order)
                + "</tbody></table></div></details>")
    fill = {k.upper(): c for k, c in charts.items()}
    page = TEMPLATE.format(CSS=CSS, DIAGRAM=DIAGRAM, WAYS=ways, HELD=held, APPENDIX=appendix, **fill)
    with open(os.path.join(HERE, "report.html"), "w") as f:
        f.write(page)
    print(f"report.html written; TEXT {len(TEXT.split())} words")


HEAD_W = ("<tr><th>bodies (control, mean of seeds 9-11)</th><th>size</th><th>hard</th><th>muscle</th><th>gut</th>"
          "<th>open soft faces</th><th>meat</th><th>children / 1,000 steps</th><th>water</th></tr>")
HEAD_H = ("<tr><th>run</th><th>upper north, seed 9</th><th>10</th><th>11</th><th>lower north, seed 9</th><th>10</th><th>11</th></tr>")

TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>e083 What Holds A Region - Report</title>
<style>{CSS}</style>
</head>
<body>
<main>
<h1>e083: what holds the other lines against the leading line?</h1>
<p class="sub">Experiment report - 2026-09-19 - #96: an analysis of e081's and e082's censuses, no new runs; seeds 9-11, 100,000 steps, c1225</p>

<section class="tldr">
<h2>TL;DR</h2>
<p>A barrier of thirst. The leading line spreads over most of the land and stops in a dry belt near the
equator of the upper continent, where bodies live at a third of the density on either side. Beyond it,
other lines (soft grazers) hold the north for the whole run. Loosen water (e082) and the belt fills, the
leader crosses, and they are replaced. Next: whether a land with more such regions holds more kinds.</p>
</section>

<h2>1. Question</h2>
<p>e081 and e082 both lowered kinds, from opposite sides. In the control, other lines hold one region
against the leader for the whole run; at fresh 0.2 the leader takes it. The map (Figure 2) shows it is a
place, not a latitude: the upper continent's north. Three candidates:</p>
<ol>
  <li><strong>A barrier:</strong> bodies thin out where the lines meet; neither does better there.</li>
  <li><strong>The locals fit their place</strong> and out-breed the leader there.</li>
  <li><strong>First come, first held:</strong> the boundary drifts.</li>
</ol>

<h2>2. Method</h2>
{DIAGRAM}
<p><strong>Data.</strong> The land bodies of every census (36,000-100,000 steps) of nine runs: e081's control
and fresh 0.05, e082's fresh 0.2, seeds 9-11. The leader is each run's largest lineage. The map is a torus
whose latitude runs from -59 to 87 degrees twice (upper and lower half).</p>
<ul class="measures">
  <li><strong>Upper continent</strong> - the upper half's land at x 128-327.</li>
  <li><strong>Bodies a cell</strong> - land bodies a land cell a census.</li>
  <li><strong>Ground dryness</strong> - the run's mean, 0 wet to 1 dry.</li>
  <li><strong>Children</strong> - per 1,000 steps of age, bodies aged 50 or more.</li>
</ul>

<h2>3. Results</h2>
<div class="tw"><table><thead>""" + HEAD_H + """</thead><tbody>{HELD}</tbody></table></div>
<p>The leader's share of the land bodies north of 10 degrees.</p>
<ol class="verdicts">
<li><span class="verdict">Yes</span> <strong>A barrier:</strong> bodies thin to a third in the belt; the two lines have children at 4.98 and 4.75 per 1,000 steps there.</li>
<li><span class="verdict no">No</span> <strong>The locals fit:</strong> neither out-breeds the other where both live, and the leader takes the north once it can cross.</li>
<li><span class="verdict no">No</span> <strong>First come:</strong> the boundary stays in the belt for 64,000 steps on three seeds.</li>
</ol>

<h3>3.1 One region is held</h3>
<div class="grid2">
{MAP_C}
{MAP_F}
</div>

<h3>3.2 The boundary sits in a dry belt</h3>
<div class="grid2">
{BODIES}
{SHARE}
</div>
<div class="grid2">
{DRY}
{TIME}
</div>
<p>The belt is 40 rows wide, 8-10 times how far a grown body ends from its birth place. At fresh 0.05 its
ground gives a body 0.014 of a pool's drink; at 0.2, 0.056, and it fills to 0.6-0.7 of either side. Under
e081's paid drink it empties. The lower continent's north is as thin (0.017-0.020) and drier, and the leader
holds it: it leads to no dense land held by others. We read a thin place as holding a boundary only between
two dense regions.</p>

<h3>3.3 Two ways of living</h3>
<div class="tw"><table><thead>""" + HEAD_W + """</thead><tbody>{WAYS}</tbody></table></div>
<p>The upper north's lines are small soft grazers; the leader is an armored half-hunter. In the upper
tropics, where both live, both grow large guts and breed at the same rate.</p>

<h2>4. Discussion</h2>
<p>The kinds the control holds beyond the leader's come, in part, from one place of the generated land that
a line cannot cross. They are not held by a better fit: where the lines meet, neither out-breeds the other.
What holds them is few arrivals: the belt lets few of the leader's bodies reach a dense north whose lines
breed as fast.</p>
<p>This gives set D's small fresh a role it did not have when #88 set it: it turns dry land into a barrier.
It also explains e081 and e082 from one side. Water that binds empties the belt; water that frees fills it.</p>
<p>What it does not show: whether more barriers would hold more kinds. c1225 has one clear barrier and a
weaker one to the east.</p>

<h2>5. Conclusion and next step</h2>
<p>A region is held by a barrier of thirst, not by the bodies' fit. The next question is about the generated
world: does a land with more regions behind such barriers hold more kinds under the same laws? That needs a
barrier count on the worlds we have before any run.</p>

<h2>Appendix: data</h2>
<p><code>hold.py</code> writes <code>results/regions.csv</code>, <code>transect.csv</code>, <code>time.csv</code> and
<code>maps.csv</code> from the runs' censuses (not committed; e081's and e082's <code>_agents.csv</code>). Build with
<code>uv run python experiments/e083_hold/report.py</code>.</p>
{APPENDIX}
</main>
</body>
</html>
"""

TEXT = TEMPLATE  # the words of the page, for the budget


if __name__ == "__main__":
    main()
