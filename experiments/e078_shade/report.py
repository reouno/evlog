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
SEARCH = os.path.join(RESULTS, "search")
YEAR = 11880  # steps in c1225's year; the bodies start on a whole year, so a step's phase is step / YEAR
N, LAT_LO, LAT_HI = 512, -59.4, 87.0
KIND_COLOR = {1: SERIES[0], 2: SERIES[1], 3: SERIES[3], 4: SERIES[2]}  # hard, muscle, sensor, gut
QUARTERS = ["0", "0.25 (N summer)", "0.5", "0.75 (N winter)"]
RUNS = ["h0d0", "h1d0", "h2.5d0", "h5d0", "h0d2.5", "h0d5", "h1d1", "h1d5", "h2.5d2.5", "h5d1", "h5d5"]


def rows_of(path):
    with open(path) as f:
        return list(csv.DictReader(f))


def quarter(mid):
    return int(((mid / YEAR + 0.125) % 1.0) * 4)


def lat_of(cell):
    return LAT_LO + (LAT_HI - LAT_LO) * (1 - abs(2 * ((cell // N) + 0.5) / N - 1))


def bands(run):
    """A search run after the first year: by (latitude, wood class, quarter) the sums of bodies, cells, felt, over and the rows."""
    g = {}
    for r in rows_of(os.path.join(SEARCH, f"c1225_life9_{run}_bands.csv")):
        st = int(r["step"])
        if st <= 12000:
            continue
        v = g.setdefault((int(r["lat"]), int(r["wood_class"]), quarter(st - 500)), [0.0] * 5)
        for i, c in enumerate(("bodies", "cells", "felt", "over")):
            v[i] += float(r[c])
        v[4] += 1
    return g


def sweep():
    return {r["run"].replace("life9_", ""): r for r in rows_of(os.path.join(RESULTS, "sweep_search.csv"))}


def top_lines(run):
    """The largest lineage in the stands and on the mid-latitude lawn at step 60,000: its commonest body."""
    last = [r for r in rows_of(os.path.join(SEARCH, f"c1225_life9_{run}_agents.csv")) if r["step"] == "60000" and r["medium"] == "0"]
    out = {}
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
        food = sum(float(x["plant"]) + float(x["killed"]) + float(x["scavenged"]) for x in top)
        out[where] = dict(lineage=r["lineage"], n=len(top), of=len(rs), side=int(side), cells=cells, hard=r["hard"],
                          muscle=r["muscle"], gut=r["digestive"], kills=sum(float(x["killed"]) for x in top) / max(food, 1e-9))
    return out


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


def scatter_free(title, subtitle, groups, xlabel, ylabel=None):
    """groups: list of (label, xs, ys, slot); both axes free."""
    fig, ax = new_axes(xlabel)
    for label, xs, ys, slot in groups:
        ax.scatter(xs, ys, s=22, color=SERIES[slot], label=label)
    if ylabel:
        ax.set_ylabel(ylabel)
    ax.yaxis.set_major_formatter(kfmt)
    ax.yaxis.set_major_locator(MaxNLocator(4))
    ax.margins(x=0.08, y=0.15)
    legend_above(ax, len(groups))
    return figure(title, subtitle, to_svg(fig))


DIAGRAM = """
<figure class="diagram">
<svg viewBox="0 0 780 250" role="img" aria-label="The crown's shade: the day a body feels is pulled toward the day's mean, and the dry air is cut" style="max-width:100%;height:auto;display:block">
<defs><marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="currentColor"/></marker></defs>
<g fill="none" stroke="currentColor" stroke-width="1.2" font-size="12" font-family="system-ui, sans-serif">
  <rect x="10" y="20" width="200" height="64" rx="6"/>
  <text x="110" y="44" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">the cell's air</text>
  <text x="110" y="62" text-anchor="middle" fill="currentColor" stroke="none">T swings ~20 C around T_day</text>
  <rect x="10" y="150" width="200" height="64" rx="6"/>
  <text x="110" y="174" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">the crown</text>
  <text x="110" y="192" text-anchor="middle" fill="currentColor" stroke="none">shade = wood / (wood + 4)</text>
  <rect x="300" y="20" width="220" height="64" rx="6"/>
  <text x="410" y="44" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">what a body feels</text>
  <text x="410" y="62" text-anchor="middle" fill="currentColor" stroke="none">T - min(1, k x shade) x (T - T_day)</text>
  <rect x="300" y="150" width="220" height="64" rx="6"/>
  <text x="410" y="174" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">the dry air on its faces</text>
  <text x="410" y="192" text-anchor="middle" fill="currentColor" stroke="none">dryness x (1 - min(1, k2 x shade))</text>
  <rect x="600" y="20" width="170" height="194" rx="6"/>
  <text x="685" y="44" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">the body</text>
  <text x="685" y="74" text-anchor="middle" fill="currentColor" stroke="none">over 30 C: water</text>
  <text x="685" y="92" text-anchor="middle" fill="currentColor" stroke="none">to cool, per degree</text>
  <text x="685" y="122" text-anchor="middle" fill="currentColor" stroke="none">under 15 C: energy</text>
  <text x="685" y="140" text-anchor="middle" fill="currentColor" stroke="none">to warm, per degree</text>
  <text x="685" y="176" text-anchor="middle" fill="currentColor" stroke="none">soft faces lose</text>
  <text x="685" y="194" text-anchor="middle" fill="currentColor" stroke="none">water to the air</text>
  <line x1="210" y1="52" x2="300" y2="52" marker-end="url(#arr)"/>
  <text x="255" y="44" text-anchor="middle" fill="currentColor" stroke="none">T, T_day</text>
  <line x1="210" y1="170" x2="300" y2="68" marker-end="url(#arr)"/>
  <text x="232" y="122" fill="currentColor" stroke="none">k</text>
  <line x1="210" y1="182" x2="300" y2="182" marker-end="url(#arr)"/>
  <text x="255" y="174" text-anchor="middle" fill="currentColor" stroke="none">k2</text>
  <line x1="520" y1="52" x2="600" y2="52" marker-end="url(#arr)"/>
  <line x1="520" y1="182" x2="600" y2="182" marker-end="url(#arr)"/>
  <text x="410" y="112" text-anchor="middle" fill="var(--s1)" stroke="none">at most all the way: what is left is T_day,</text>
  <text x="410" y="130" text-anchor="middle" fill="var(--s1)" stroke="none">about 37 C in a 20-30 N stand in summer</text>
  <text x="390" y="240" text-anchor="middle" fill="currentColor" stroke="none">both rates 0 = e077 exactly; the climate and the plants do not change</text>
</g>
</svg>
<figcaption>Figure 1. The two rates. A crown pulls what a body's heat reads toward the day's running mean and
cuts the dry air, both by its shade. Today's stands (wood 2-3 a cell) have a shade of 0.33-0.43. The blue
line is what the argument turns on: damping cannot go below the day's mean.</figcaption>
</figure>
"""


def gallery(tops, caption, n=2):
    cards = []
    for run, label in (("h0d0", "control"), ("h5d0", "k 5"), ("h0d5", "k2 5")):
        for where in ("stand", "lawn"):
            r = tops[run][where]
            side, cells = r["side"], r["cells"]
            px = 88 // max(side, 1)
            rects = "".join(
                f'<rect x="{(i % side) * px}" y="{(i // side) * px}" width="{px - 1}" height="{px - 1}" fill="{KIND_COLOR[int(k)]}"/>'
                for i, k in enumerate(cells[: side * side]) if k != "0")
            name = f"{label}: top line in the stands" if where == "stand" else f"{label}: top line on the mid-latitude lawn"
            cards.append(f"""<figure class="card"><svg viewBox="-1 -1 89 89" width="104" height="104" role="img" aria-label="{name}">
<rect x="-1" y="-1" width="89" height="89" fill="var(--grid)"/>{rects}</svg>
<figcaption><strong>{name}</strong><br>lineage {r['lineage']}: {r['n']} of {r['of']} bodies<br>
{r['hard']} hard, {r['muscle']} muscle, {r['gut']} gut; kills {r['kills']:.0%} of its food</figcaption></figure>""")
    return f"""<figure class="diagram"><div class="cards">{"".join(cards)}</div>
<figcaption>Figure {n}. {html.escape(caption)}</figcaption></figure>"""


def main():
    g = {run: bands(run) for run in ("h0d0", "h2.5d0", "h5d0", "h0d5", "h5d5")}
    sw = sweep()
    lats = sorted({k[0] for k in g["h0d0"]})
    mid = [l + 5 for l in lats]

    def per(run, lat, c, q, i, div):
        v = g[run].get((lat, c, q))
        return v[i] / v[div] if v and v[div] else float("nan")

    NS = 1  # the north's summer
    charts1 = [
        line_x("A crown takes degrees off the north's summer", "Mean degrees over 30 C a body reads, quarter 0.25. Lawn and stand apart = the crown works.",
               mid, [("lawn", [per("h0d0", l, 0, NS, 3, 4) for l in lats], 5), ("stand, control", [per("h0d0", l, 2, NS, 3, 4) for l in lats], 0),
                     ("stand, k 2.5", [per("h2.5d0", l, 2, NS, 3, 4) for l in lats], 1), ("stand, k 5", [per("h5d0", l, 2, NS, 3, 4) for l in lats], 2)],
               "latitude (degrees)", "degrees over"),
        line_x("But not off the day's mean", "Mean of what a body reads in a stand, same quarter, band 15-30 C shaded. The two lines lie on each other.",
               mid, [("stand, control", [per("h0d0", l, 2, NS, 2, 4) for l in lats], 0), ("stand, k 5", [per("h5d0", l, 2, NS, 2, 4) for l in lats], 2)],
               "latitude (degrees)", "C", band=(15, 30)),
    ]
    xs = [0, 0.25, 0.5, 0.75]
    runs3 = (("control", "h0d0", 0), ("k 5", "h5d0", 2), ("k2 5", "h0d5", 1), ("k 5, k2 5", "h5d5", 3))
    charts2 = [
        line_x("The stands hold the same in every quarter", "Bodies in stands, summed over the log's rows in a quarter. A rise at 0.25 and 0.75 = a refuge.",
               xs, [(lab, [sum(v[0] for k, v in g[run].items() if k[1] == 2 and k[2] == q) for q in range(4)], s) for lab, run, s in runs3],
               "phase of the year", "bodies", markers=True),
        line_x("At 20-30 N the stand empties in summer anyway", "Bodies a stand cell at 20-30 N by quarter; the dip at 0.25 is the north's summer.",
               xs, [(lab, [per(run, 20, 2, q, 0, 1) for q in range(4)], s) for lab, run, s in runs3],
               "phase of the year", "bodies a cell", markers=True),
    ]
    heat = [r for r in RUNS if sw[r]["k2"] in ("0.0",)]
    dry = [r for r in RUNS if sw[r]["k2"] != "0.0"]
    charts3 = [
        scatter_free("A cooler stand does not fill at the solstices", "Each dot a run: the stands' degrees over 30 C in the hot quarter, and their bodies solstices / equinoxes.",
                     [("k2 0", [float(sw[r]["over_stand"]) for r in heat], [float(sw[r]["stand_ratio"]) for r in heat], 0),
                      ("k2 over 0", [float(sw[r]["over_stand"]) for r in dry], [float(sw[r]["stand_ratio"]) for r in dry], 1)],
                     "degrees over 30 C in a stand", "solstices / equinoxes"),
        scatter_free("The dry cut does not order the stands' bodies", "Each dot a run: k2, and the stands' bodies a quarter (mean of the four). A rising cloud = the cut feeds the stands.",
                     [(f"k {k:g}", [float(sw[r]["k2"]) for r in RUNS if float(sw[r]["k"]) == k],
                       [sum(float(x[:-1]) for x in sw[r]["stand_q"].split("/")) / 4 * 1000 for r in RUNS if float(sw[r]["k"]) == k], i)
                      for i, k in enumerate((0, 1, 2.5, 5))],
                     "k2", "bodies"),
    ]
    table = "".join(
        f"<tr><td>{float(r['k']):g}</td><td>{float(r['k2']):g}</td><td>{float(r['over_stand']):.1f}</td><td>{float(r['over_lawn']):.1f}</td>"
        f"<td>{float(r['stand_ratio']):.2f}</td><td>{float(r['land_ratio']):.2f}</td><td>{r['stand_q']}</td><td>{float(r['pop_land']):,.0f}</td>"
        f"<td>{float(r['d_thirst']):.0%}</td><td>{float(r['d_cold']):.1%}</td><td>{float(r['line_stand']):.2f}</td><td>{float(r['kinds_at']):.2f}</td><td>{float(r['placed_at']):.2f}</td></tr>"
        for r in (sw[x] for x in RUNS))
    tops = {run: top_lines(run) for run in ("h0d0", "h5d0", "h0d5")}
    gal = gallery(tops, "The largest lineage in the stands and on the mid-latitude lawn (20 degrees and out) at step 60,000, "
                        "its commonest body, in three runs. Blue hard, orange muscle, yellow sensor, aqua gut.", n=2)
    appendix = "".join(
        f"<details><summary>{run}: bodies a stand cell by latitude and quarter</summary><div class='tw'><table><thead><tr><th>latitude</th>"
        + "".join(f"<th>{q}</th>" for q in QUARTERS) + "</tr></thead><tbody>"
        + "".join(f"<tr><td>{l} to {l + 10}</td>" + "".join(f"<td>{per(run, l, 2, q, 0, 1):.3f}</td>" for q in range(4)) + "</tr>"
                  for l in lats if (l, 2, 0) in g[run])
        + "</tbody></table></div></details>" for run in g)
    page = TEMPLATE.format(CSS=CSS, DIAGRAM=DIAGRAM, GALLERY=gal, TABLE=table, APPENDIX=appendix,
                           CHARTS1="".join(charts1), CHARTS2="".join(charts2), CHARTS3="".join(charts3))
    with open(os.path.join(HERE, "report.html"), "w") as f:
        f.write(page)
    words = len(TEXT.split())
    print(f"report.html written; TEXT {words} words")


TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>e078 The crown's shade - Report</title>
<style>{CSS}</style>
</head>
<body>
<main>
<h1>e078: does a crown's shade make a stand a refuge?</h1>
<p class="sub">Experiment report - 2026-09-19 - #91 step 1: two rates of shade, 11 runs of 60,000 steps on c1225, seed 9</p>

<section class="tldr">
<h2>TL;DR</h2>
<p>No. A crown that pulls the day a body feels toward the day's mean halves a stand's degrees over 30 C
in the hot quarter, but the day's mean is itself hot: about 37 C in a 20-30 N stand in summer. The
stands lose their bodies in the bad quarter as before, and no line follows the season. Cutting the dry
air moves the stands' bodies the same in every quarter, and not in order of the rate. Next: a crown that lowers the mean, or a
heat band that fits the climate.</p>
</section>

<h2>1. Question</h2>
<p>A refuge pays when the season takes the lawn away (A, found in e077) and the stand keeps what the lawn
loses (B). The summer's loss is heat, so (B) is built as shade. Before the runs:</p>
<ol>
  <li><strong>Heat:</strong> at k 2.5 or more a stand reads under half the lawn's degrees over 30 C in the hot quarter.</li>
  <li><strong>Filling:</strong> bodies in stands rise at the solstices over the equinoxes by 1.25 or more.</li>
  <li><strong>Dry cut:</strong> alone it raises the stands' bodies in every quarter alike.</li>
  <li><strong>A line</strong> fills the stands at the solstices more than any control line does.</li>
</ol>

<h2>2. Method</h2>
<p>e077's binary with two rates read on the body's side; the climate and the plants are untouched.</p>
{DIAGRAM}
<p><strong>Runs.</strong> Seed 9, 60,000 steps: the control and ten pairs (k, k2) from 0 to 5, 11 cores for
35 minutes. A census every 1,000 steps from 36,000. The 3-seed run of a centre was not made: nothing passed (2).</p>
<ul class="measures">
  <li><strong>Stand / lawn</strong> - a land cell with wood of 1 or more / under 0.1.</li>
  <li><strong>Degrees over</strong> - mean of what a body reads minus 30 C, over every climate update.</li>
  <li><strong>S/E</strong> - bodies at the solstices over bodies at the equinoxes.</li>
  <li><strong>Line</strong> - a lineage with 5% of the land's bodies over the censuses.</li>
</ul>
{GALLERY}

<h2>3. Results</h2>
<div class="tw"><table>
<thead><tr><th>k</th><th>k2</th><th>over, stand</th><th>over, lawn</th><th>stands S/E</th><th>land S/E</th><th>stands a quarter</th><th>land bodies</th><th>thirst</th><th>cold</th><th>top line S/E</th><th>kinds</th><th>placed</th></tr></thead>
<tbody>{TABLE}</tbody></table></div>
<p>Over: in bands of 10-30 degrees, each in its lawn's hottest quarter. Deaths are shares of all deaths.</p>
<ol class="verdicts">
<li><span class="verdict partly">Partly</span> <strong>Heat:</strong> 0.45 of the lawn's at k 5, 0.50 at k 2.5.</li>
<li><span class="verdict no">No</span> <strong>Filling:</strong> the stands' S/E stays 0.96-1.04 in every run.</li>
<li><span class="verdict partly">Partly</span> <strong>Dry cut:</strong> k2 5 alone puts 23-25k in stands in every quarter (control 18-20k), but k2 2.5 puts 16-17k.</li>
<li><span class="verdict no">No</span> <strong>A line:</strong> top lines read 0.92-1.25, inside the control's 0.90-1.54.</li>
</ol>

<h3>3.1 The crown takes the swing, not the heat</h3>
<div class="grid2">
{CHARTS1}
</div>
<p>Fully damped, a body feels the day's mean, and in the bad quarter that mean is over the band from the
equator to 40 N. The stand becomes a steadier place, not a cool one.</p>

<h3>3.2 The stands do not fill when the lawn empties</h3>
<div class="grid2">
{CHARTS2}
</div>
<div class="grid2">
{CHARTS3}
</div>
<p>How many degrees a stand takes off does not order how it fills by season. Where the dry cut moves the
stands' bodies it moves them in every quarter alike, and on one seed not in order of k2.</p>

<h2>4. Discussion</h2>
<p>The heat law prices degrees outside 15-30 C, and in this world the tropics read 13-19 degrees over 30 C
in every quarter. Thirst is 42-48% of all deaths in every run. A crown that removes only the day's swing
leaves that mean in place, so a stand next to a summer lawn is still too hot to take its bodies.</p>
<p>The rates do work where they can: cold deaths fall from 1.8% to 1.1% of deaths at k 5, and k2 5 alone
holds 17% more land bodies. Kinds on one seed move 6.3-8.4 with no order by rate; this step does not judge them.</p>
<p>The conditions: c1225, a 75-step day swinging about 20 C, the band 15-30 C, grown lives of 1/20 of a year.</p>

<h2>5. Conclusion and next step</h2>
<p>Shade as a damper does not make a refuge, because what the lawn loses in summer is a mean the damper
cannot change. #91 now turns on the mean: a crown that takes its share of the sun's heat, or a heat band
that matches the climate the bodies live in. The two rates stay as arguments, 0 by default.</p>

<h2>Appendix: data</h2>
<p>Bodies a stand cell by band and quarter, five runs. Everything is in <code>results/search/*_bands.csv</code>,
<code>*_agents.csv</code> and <code>*_log.csv</code>; the table is <code>sweep.py</code>'s
<code>results/sweep_search.csv</code>. Build with <code>uv run python experiments/e078_shade/report.py</code>.</p>
{APPENDIX}
</main>
</body>
</html>
"""

TEXT = TEMPLATE  # the words of the page, for the budget


if __name__ == "__main__":
    main()
