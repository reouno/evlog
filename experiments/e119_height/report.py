#!/usr/bin/env python3
"""Build report.html for this experiment.

Charts and maps: matplotlib, exported as SVG and inlined. Diagram: hand-written SVG. Two looks at the map page
(shots/*.jpg) are embedded, so the page stands alone.
Run from the repo root: uv run python experiments/e119_height/report.py
"""
import base64
import csv
import html
import io
import json
import os

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import BoundaryNorm, LinearSegmentedColormap, ListedColormap, PowerNorm
from matplotlib.ticker import MaxNLocator

matplotlib.use("svg")

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results")
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4"]  # fixed slot order
# The same thing has the same colour in every chart: this run's trees blue, e118's orange, the field aqua; the four
# sown genomes with the most trees take the four first slots in the two charts that part the trees by genome.
TREES, E118, FIELD = 0, 1, 2
OLD = os.path.join(HERE, "..", "e118_plants", "results", "main")  # the run this one is read beside

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

# Maps: the ground under crowns from bare earth to pale green; warmth in the five classes of the reading.
CROWNS = LinearSegmentedColormap.from_list("crowns", ["#33312b", "#1d5a3c", "#1baf7a", "#d2f59a"])
WARMTH = ListedColormap(["#34507a", "#5f8fb5", "#c9c3a0", "#e0a04f", "#d0582f"])

TREE = np.dtype([("x", "<f4"), ("y", "<f4"), ("h", "<f4"), ("r", "<f4"), ("leaf", "<f4"), ("wood", "<f4"), ("age", "<f4"),
                 ("tough", "<f4"), ("g", "<u4"), ("born", "<u4")])
H_STEM = 4.2  # m a stem of a kg can stand, by the mass's fourth root (`h_stem`; read.py reads the trees with it)


# ---------- data ----------

def read_rows(path):
    with open(os.path.join(HERE, path)) as f:
        return list(csv.DictReader(f))


def load_world(pre):
    """The kept years' annual maps (their mean) and the static fields, loaded as `read.py` loads them."""
    m = json.load(open(pre + "_maps.json"))
    n, F, S, Y = m["n"], m["fields"], m["static"], len(m["years"])
    a = np.fromfile(pre + "_maps.bin", dtype="<f4")
    ann = a[:Y * len(F) * n * n].reshape(Y, len(F), n, n).mean(0)
    st = a[Y * len(F) * n * n:].reshape(len(S), n, n)
    return {"n": n, "years": m["years"], "ann": {k: ann[F.index(k)] for k in F}, "st": {k: st[S.index(k)] for k in S}}


def load_trees(pre, year):
    return np.fromfile(f"{pre}_trees_{year}.bin", dtype=TREE)


def crown_cover(trees, n, side):
    """The ground under crowns by 125 m cell: each tree's disc (overlaps counted twice, a cell at most whole), as read.py."""
    ci = np.clip((trees["x"] / side).astype(int), 0, n - 1)
    cj = np.clip((trees["y"] / side).astype(int), 0, n - 1)
    cover = np.zeros((n, n))
    np.add.at(cover, (cj, ci), np.pi * trees["r"].astype(float) ** 2)
    return np.minimum(cover / side ** 2, 1.0)


# ---------- chart helpers ----------

def kfmt(x, _pos):
    return f"{x/1000:g}k" if abs(x) >= 1000 else f"{x:g}"


def to_svg(fig):
    buf = io.StringIO()
    fig.savefig(buf, format="svg", bbox_inches="tight", pad_inches=0.05, dpi=200)
    plt.close(fig)
    return buf.getvalue()


def legend_above(ax, n):
    ax.legend(loc="lower left", bbox_to_anchor=(0, 1.0), ncols=n, handlelength=1.2, borderaxespad=0, columnspacing=1.2 if n < 5 else 0.8)


def figure(title, subtitle, svg):
    return f"""
<figure class="fig">
  <figcaption><strong>{html.escape(title)}</strong><span>{html.escape(subtitle)}</span></figcaption>
  {svg}
</figure>"""


def new_axes(xlabel="year", size=(6.4, 2.6)):
    fig, ax = plt.subplots(figsize=size)
    ax.set_xlabel(xlabel, loc="right")
    ax.margins(x=0)
    return fig, ax


def line_chart(title, subtitle, xs, series, yfmt=kfmt):
    """series: list of (label, ys, slot)."""
    fig, ax = new_axes()
    for label, ys, slot in series:
        ax.plot(xs, ys, color=SERIES[slot], linewidth=1.6, label=label)
    ax.set_ylim(0, max(v for _, ys, _ in series for v in ys) * 1.12)
    ax.yaxis.set_major_formatter(yfmt)
    ax.yaxis.set_major_locator(MaxNLocator(4))
    legend_above(ax, len(series))
    return figure(title, subtitle, to_svg(fig))


def stacked_area(title, subtitle, xs, layers, size=(6.4, 2.6)):
    """layers: list of (label, ys, colour); fractions summing to 1."""
    fig, ax = new_axes(size=size)
    ax.stackplot(xs, [ys for _, ys, _ in layers], labels=[l for l, _, _ in layers], colors=[c for _, _, c in layers], linewidth=0)
    ax.set_ylim(0, 1)
    ax.yaxis.set_major_formatter(lambda y, _p: f"{y:.0%}")
    ax.yaxis.set_major_locator(MaxNLocator(4))
    legend_above(ax, len(layers))
    return figure(title, subtitle, to_svg(fig))


def bar_chart(title, subtitle, labels, values, slot, xlabel):
    """Upright bars of shares (0-1), each with its number on top."""
    fig, ax = new_axes(xlabel)
    ax.margins(x=0.03)
    bars = ax.bar(labels, [100 * v for v in values], color=SERIES[slot], width=0.62)
    ax.bar_label(bars, labels=[f"{100 * v:.0f}%" for v in values], padding=2, color=INK)
    ax.set_ylim(0, 100 * max(values) * 1.18)
    ax.yaxis.set_major_locator(MaxNLocator(4))
    ax.yaxis.set_major_formatter(lambda y, _p: f"{y:g}%")
    ax.tick_params(axis="x", length=0)
    return figure(title, subtitle, to_svg(fig))


def value_bars(title, subtitle, labels, values, slot, xlabel, fmt):
    """Upright bars of a quantity, each with its number on top."""
    fig, ax = new_axes(xlabel)
    ax.margins(x=0.03)
    bars = ax.bar(labels, values, color=SERIES[slot], width=0.62)
    ax.bar_label(bars, labels=[fmt(v) for v in values], padding=2, color=INK)
    ax.set_ylim(0, max(values) * 1.18)
    ax.yaxis.set_major_locator(MaxNLocator(4))
    ax.tick_params(axis="x", length=0)
    return figure(title, subtitle, to_svg(fig))


def class_chart(title, subtitle, groups, slot, xlabel):
    """Lying bars in groups: groups is a list of (group name, [(class, share 0-1)])."""
    fig, ax = plt.subplots(figsize=(6.4, 3.9))
    ax.grid(axis="y", visible=False)
    ax.grid(axis="x", visible=True)
    ys, names, vals, y = [], [], [], 0.0
    for gname, rows in groups:
        ax.text(0, y - 0.72, gname, color=INK, fontsize=9, fontweight="bold", va="center", ha="left")
        for name, v in rows:
            ys.append(y), names.append(name), vals.append(100 * v)
            y += 1
        y += 1.1
    bars = ax.barh(ys, vals, color=SERIES[slot], height=0.66)
    ax.bar_label(bars, labels=[f"{v:.1f}%" for v in vals], padding=3, color=INK)
    ax.set_yticks(ys, names)
    ax.set_ylim(max(ys) + 0.6, -1.25)
    ax.set_xlim(0, max(vals) * 1.15)
    ax.xaxis.set_major_locator(MaxNLocator(4))
    ax.xaxis.set_major_formatter(lambda x, _p: f"{x:g}%")
    ax.set_xlabel(xlabel, loc="right")
    ax.tick_params(axis="y", length=0)
    ax.spines["bottom"].set_visible(False)
    return figure(title, subtitle, to_svg(fig))


def map_chart(title, subtitle, w, field, cmap, norm, ticks, labels, extend="neither"):
    """One field on the land, north up, the sea left blank."""
    n, land = w["n"], w["st"]["sea"] < 0.5
    km = n * 0.125
    lat = w["st"]["lat"]
    fig, ax = plt.subplots(figsize=(6.4, 5.5))
    ax.grid(False)
    im = ax.imshow(np.ma.masked_where(~land, field), origin="lower", cmap=cmap, norm=norm, extent=(0, km, 0, km), interpolation="nearest")
    c = (np.arange(n) + 0.5) * 0.125
    ax.contour(c, c, land.astype(float), levels=[0.5], colors=INK, linewidths=0.5)
    for y in (km / 4, km / 2, 3 * km / 4):  # the four latitude bands of the reading
        ax.axhline(y, color=INK, linewidth=0.6, alpha=0.5, linestyle=(0, (4, 4)))
    lo, hi = float(lat[0, 0]), float(lat[-1, 0])
    edge = lambda y: lo - (hi - lo) / (2 * (n - 1)) + (hi - lo + (hi - lo) / (n - 1)) * y / km
    ax.set_yticks([0, km / 4, km / 2, 3 * km / 4, km], [f"{edge(y):.0f} N" for y in (0, km / 4, km / 2, 3 * km / 4, km)])
    ax.set_xticks([0, 4, 8, 12, 16])
    ax.set_xlabel("km, west to east", loc="right")
    ax.set_aspect("equal")
    cb = fig.colorbar(im, ax=ax, fraction=0.035, pad=0.03, extend=extend, ticks=ticks)
    cb.outline.set_visible(False)
    cb.ax.minorticks_off()
    cb.ax.tick_params(length=0)
    cb.ax.set_yticklabels(labels)
    return figure(title, subtitle, to_svg(fig))


def wood_height_chart(title, subtitle, trees, lines, sample=6000, size=(6.4, 3.4)):
    """Each tree's height against its wood (a sample), and the height a stem of that wood could stand."""
    rng = np.random.default_rng(1)
    pick = trees[rng.choice(len(trees), size=min(sample, len(trees)), replace=False)]
    fig, ax = new_axes("wood of a tree, kg (log scale)", size=size)
    ax.set_xscale("log")
    rest = ~np.isin(pick["g"], [g for g, _, _ in lines])
    dots = lambda sel, colour, alpha: ax.scatter(pick["wood"][sel], pick["h"][sel], s=5, color=colour, alpha=alpha, linewidths=0, rasterized=True)
    others = dots(rest, INK, 0.6)  # drawn first, under the lines
    named = [dots(pick["g"] == g, SERIES[slot], 0.55) for g, _, slot in lines]
    ws = np.geomspace(trees["wood"].min(), trees["wood"].max(), 80)
    curve, = ax.plot(ws, H_STEM * ws ** 0.25, color="#c3c2b7", linewidth=1.6)
    ax.set_xlim(trees["wood"].min() * 0.9, trees["wood"].max() * 1.1)
    ax.set_ylim(0, H_STEM * trees["wood"].max() ** 0.25 * 1.05)
    ax.yaxis.set_major_locator(MaxNLocator(4))
    ax.yaxis.set_major_formatter(lambda y, _p: f"{y:g} m")
    ax.xaxis.set_major_formatter(lambda x, _p: f"{x:,g}")
    ax.minorticks_off()
    leg = ax.legend(named + [others, curve], [label for _, label, _ in lines] + ["others", "what its wood could stand"], loc="lower left",
                    bbox_to_anchor=(0, 1.0), ncols=3, handlelength=1.2, borderaxespad=0, columnspacing=1.2, handletextpad=0.4, markerscale=2.5)
    for h in leg.legend_handles:
        h.set_alpha(1)
    return figure(title, subtitle, to_svg(fig))


def table(headers, rows):
    return ("<div class='tw'><table><thead><tr>" + "".join(f"<th>{html.escape(h)}</th>" for h in headers)
            + "</tr></thead><tbody>"
            + "".join("<tr>" + "".join(f"<td>{html.escape(str(v))}</td>" for v in r) + "</tr>" for r in rows)
            + "</tbody></table></div>")


def folded(name, body, shown=False):
    return f"<details{' open' if shown else ''}><summary>{html.escape(name)}</summary>{body}</details>"


def shot(name):
    with open(os.path.join(HERE, "shots", name + ".jpg"), "rb") as f:
        return "data:image/jpeg;base64," + base64.b64encode(f.read()).decode()


def pair(a, b):
    """Two looks: (file, alt text, caption) twice."""
    cells = "".join(f'<div><img src="{shot(f)}" alt="{html.escape(alt)}"><span class="when">{cap}</span></div>' for f, alt, cap in (a, b))
    return f'<figure class="fig shots"><div class="pair">{cells}</div></figure>'


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
th:first-child, td:first-child { text-align: left; } td { white-space: nowrap; }
th { color: var(--ink2); font-weight: 600; }
.tw { overflow-x: auto; margin: 0 0 12px; }
details { margin: 8px 0; } summary { cursor: pointer; color: var(--ink2); }
.verdicts { list-style: none; padding: 0; margin: 12px 0 0; } .verdicts li { margin: 4px 0; }
.verdict { display: inline-block; padding: 1px 8px; border-radius: 4px; font-size: 12.5px; font-weight: 600; background: rgba(12,163,12,0.12); color: #0ca30c; }
.verdict.no { background: rgba(208,59,59,0.12); color: #e66767; }
.verdict.partly { background: rgba(250,178,25,0.15); color: #fab219; }
.shots { margin: 0 0 16px; padding-bottom: 10px; }
.pair { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.pair img { width: 100%; height: auto; display: block; border-radius: 4px; }
.when { display: block; color: var(--ink2); font-size: 13px; margin-top: 6px; }
"""

# Hand-written mechanism diagram: currentColor for lines and text, var(--s1) for the height law, the one thing
# this experiment changes. Its numbers are the world's parameters (`sigma`, `h_stem`, `crown_h`).
DIAGRAM = """
<figure class="diagram">
<svg viewBox="0 0 900 336" role="img" aria-label="A stand of many stems thins into one tree of a 5 m cell; light falls through crowns and then the field, all plants of a 125 m cell draw on one soil, fire runs over the field, and a tree's height is what its wood can stand, no longer stopped at a number in its genome" style="max-width:100%;height:auto;display:block">
<defs><marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="currentColor"/></marker>
<marker id="arrb" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="var(--s1)"/></marker></defs>
<g fill="none" stroke="currentColor" stroke-width="1.2" font-size="12" font-family="system-ui, sans-serif">
  <text x="20" y="22" fill="currentColor" stroke="none" font-weight="600">A stand of the field thins into a tree</text>
  <line x1="20" y1="250" x2="310" y2="250"/>
  <line x1="30" y1="250" x2="30" y2="258"/><line x1="120" y1="250" x2="120" y2="258"/><line x1="210" y1="250" x2="210" y2="258"/><line x1="300" y1="250" x2="300" y2="258"/>
  <text x="75" y="276" text-anchor="middle" fill="currentColor" stroke="none">5 m</text>
  <text x="165" y="276" text-anchor="middle" fill="currentColor" stroke="none">5 m</text>
  <text x="255" y="276" text-anchor="middle" fill="currentColor" stroke="none">5 m</text>
  {stems}
  <text x="75" y="205" text-anchor="middle" fill="currentColor" stroke="none">many stems</text>
  <text x="165" y="162" text-anchor="middle" fill="currentColor" stroke="none">fewer, taller</text>
  <line x1="255" y1="250" x2="255" y2="162"/>
  <ellipse cx="255" cy="128" rx="44" ry="34" fill="currentColor" fill-opacity="0.08"/>
  <text x="255" y="132" text-anchor="middle" fill="currentColor" stroke="none">r = 0.35 h</text>
  <text x="255" y="62" text-anchor="middle" fill="currentColor" stroke="none">one stem a cell:</text>
  <text x="255" y="78" text-anchor="middle" fill="currentColor" stroke="none">a tree</text>
  <line x1="40" y1="300" x2="292" y2="300" marker-end="url(#arr)"/>
  <text x="166" y="322" text-anchor="middle" fill="currentColor" stroke="none">the stand's wood grows</text>

  <text x="370" y="22" fill="currentColor" stroke="none" font-weight="600">What a plant takes, and what its height is</text>
  <rect x="370" y="250" width="520" height="58" fill="currentColor" fill-opacity="0.08" stroke="none"/>
  <line x1="370" y1="250" x2="890" y2="250"/>
  {tufts}
  <line x1="540" y1="250" x2="540" y2="132"/>
  <ellipse cx="540" cy="100" rx="46" ry="32" fill="currentColor" fill-opacity="0.08"/>
  <line x1="540" y1="250" x2="526" y2="268"/><line x1="540" y1="250" x2="540" y2="272"/><line x1="540" y1="250" x2="554" y2="268"/>
  <text x="712" y="276" text-anchor="middle" fill="currentColor" stroke="none">one soil a 125 m cell: every plant</text>
  <text x="712" y="294" text-anchor="middle" fill="currentColor" stroke="none">rooted in it draws on its water</text>
  <line x1="500" y1="247" x2="500" y2="72" stroke="var(--s1)" stroke-width="2" marker-start="url(#arrb)" marker-end="url(#arrb)"/>
  <text x="486" y="96" text-anchor="end" fill="currentColor" stroke="none">a height is the lesser of</text>
  <text x="486" y="112" text-anchor="end" fill="currentColor" stroke="none">what the wood holds up</text>
  <text x="486" y="128" text-anchor="end" fill="currentColor" stroke="none">over its leaves and what</text>
  <text x="486" y="144" text-anchor="end" fill="currentColor" stroke="none">it can stand as a stem</text>
  <line x1="510" y1="196" x2="596" y2="196" stroke-dasharray="4 4" stroke-opacity="0.7"/>
  <text x="486" y="192" text-anchor="end" fill="currentColor" stroke="none" fill-opacity="0.75">e118: a number in the</text>
  <text x="486" y="208" text-anchor="end" fill="currentColor" stroke="none" fill-opacity="0.75">genome stopped it here</text>
  <line x1="700" y1="54" x2="592" y2="88" marker-end="url(#arr)"/>
  <text x="712" y="54" fill="currentColor" stroke="none">light: the crowns first,</text>
  <text x="712" y="70" fill="currentColor" stroke="none">the tallest on top</text>
  <line x1="588" y1="118" x2="666" y2="236" stroke-dasharray="4 4" marker-end="url(#arr)"/>
  <text x="640" y="150" fill="currentColor" stroke="none">what is left,</text>
  <text x="650" y="166" fill="currentColor" stroke="none">to the field</text>
  <path d="M786,250 q-10,-17 3,-30 q1,11 9,13 q-3,-14 8,-24 q12,17 7,41 z" fill="currentColor" fill-opacity="0.25"/>
  <line x1="826" y1="232" x2="880" y2="232" marker-end="url(#arr)"/>
  <text x="768" y="176" fill="currentColor" stroke="none">fire runs over</text>
  <text x="768" y="192" fill="currentColor" stroke="none">the field</text>
</g>
</svg>
<figcaption>Figure 1. Left, as in e118: a stand of the field is many stems; as its wood grows the stems thin, and at one
stem a 5 m cell the stand is a tree, with a place and a crown 0.35 of its height in radius. Right: light falls through
the crowns over a cell, then through its field; every plant of a 125 m cell draws on one soil; fire runs over grass and
litter. The one law changed (blue): a height is the lesser of what the wood holds up over its leaves (1.3 kg of wood a
kg of leaf a m) and what it can stand as a stem (4.2 m at a kg, by the wood's fourth root). e118 also stopped it at a
number in the genome (dashed), sown about 1.6 m.</figcaption>
</figure>
"""


def diagram():
    stems = "".join(f'<line x1="{x}" y1="250" x2="{x}" y2="233"/><circle cx="{x}" cy="227" r="5.5" fill="currentColor" fill-opacity="0.08"/>'
                    for x in (40, 52, 64, 76, 88, 100, 112))
    stems += "".join(f'<line x1="{x}" y1="250" x2="{x}" y2="206"/><circle cx="{x}" cy="192" r="13.5" fill="currentColor" fill-opacity="0.08"/>'
                     for x in (137, 165, 193))
    tufts = '<g stroke-opacity="0.75">' + "".join(
        f'<line x1="{x}" y1="250" x2="{x - 3}" y2="241"/><line x1="{x}" y1="250" x2="{x + 3}" y2="241"/>'
        for x in range(384, 884, 14) if abs(x - 540) > 10 and abs(x - 500) > 9 and not 776 < x < 820) + "</g>"
    return DIAGRAM.format(stems=stems, tufts=tufts)


# Every sentence of the report's prose, so that its words can be counted against the skill's budgets.
TEXT = {
    "tldr": """e118's land stayed a thicket because a number in the genome stopped a tree's height. With a height
that is what the wood can stand, the same sowing makes three times the wood within 30 years: crowns stand over 23.5%
of the land, 19% of its cells are closed woods and 46% open ground, and the tallest tree is 57.0 m. Four of six lines
pass: no floor is dark, rain does not place the wood. Kept for rung 3.""",
    "question": """Animals will live among these plants. In e118 the land was a thicket under 10 m for 500 years,
though old trees held wood for 16 m: a height was the least of three things, one of them a number in the genome. We
took the number out and expected, in 120 years of the same sowing:""",
    "h1": "It stands with every ledger closed.",
    "h2": "Crowns stand over 20-70% of the land.",
    "h3": "Old trees are tall: half of those that have stood 50 years are over 12 m, the tallest over 20 m.",
    "h4": "A wood's floor is dark: under closed woods the field holds under half of the open ground's.",
    "h5": "Open ground remains on a fifth of the cells or more, and it burns more than the wooded ground or is colder.",
    "h6": "Water places wood: the lowlands' wettest third holds 1.5 times the driest third's or more.",
    "world": """e118's world with one law changed (Figure 1, blue). The field lives on 5 m cells; a stand thinned to
one stem a cell is a tree, a thing with a place and a crown. The same 256 genomes are sown in year 10; a genome
keeps its height number and nothing reads it.""",
    "runs": """One run, main, on Ubuntu, six threads, terrain seed 23, 100 minutes: 10 bare years, then 120 with
plants. It is read at year 130, its maps as the mean of years 121-130, beside e118's main. We read:""",
    "m1": "ground under crowns - the share of the ground under the trees' discs; 0 is no tree.",
    "m2": "closed wood, open ground - a 125 m cell with crowns over half of it or more; one with crowns over less than 5%.",
    "m3": "field - all that is not a tree: grass and stands of many stems.",
    "m4": "what the wood could stand - 4.2 m at a kg, by the wood's fourth root.",
    "m5": "sown genome - one of the 256 of year 10; its trees are a line.",
    "v1": "hypothesis 1: 120 years of plants, and the worst ledger error is 1e-10, in matter.",
    "v2": "hypothesis 2: crowns stand over 23.5% of the land; e118 had 5.7%.",
    "v3": "hypothesis 3: 61% of the trees that have stood 50 years are over 12 m, and the tallest is 57.0 m.",
    "v4": "hypothesis 4: the field under closed woods holds x0.63 of the open ground's, asked under half.",
    "v5": "hypothesis 5: 46% of the cells are open ground, 3.2 C colder than the wooded ones; they burn no more.",
    "v6": "hypothesis 6: the lowlands' wettest third holds x0.7 of the driest third's wood.",
    "r1": """The wood is 0.93 kg a m2 thirty years after the sowing and stays: 1.03 at year 130, three times e118's,
which was still rising. Only the tallest tree goes on growing. A year of plants takes 49 s against 44: taller trees
did not cost more.""",
    "r2": """The land has parted, where e118's trees were spread thin. Woods stand in the warm south and on the
heights; the lowlands north of 59 N are 8.4% under crowns. Under closed woods the field holds 0.87 kg a m2 against
1.38 on open ground: crowns over 80% of a closed wood's ground take 25% of its light.""",
    "r3": """Open ground is first the cold: 79% of the cells under 9 C are open. Fire lowers the wood, 0.70 kg a
m2 where 2% or more burns a year against 2.26 where nothing burns, but leaves most burnt cells wooded. Rain does not
order the lowlands, because the wet ones are the cold north; within the two northern bands the wet third does hold more,
x1.4 and x3.4.""",
    "r4": """Trees now lie on the curve. Trees of 50 years hold 128 kg of wood and stand 13.4 m.
Two sown genomes are tall and hold 69% of the wood with 35% of the trees; two stay low, 99% of their trees under 12.1 m, with 44% of the trees. 11.3% of the trees fall a year, and what was born after the sowing is 2.4% of the living
mass.""",
    "g1": "From just above the crowns, year 130: large trees over small ones, a stream between them.",
    "g2": "The same slope from above: a closed wood, scattered large trees, and young trees in rows on the 5 m grid.",
    "d1": """The genome's limit bound e118's wood, not the climate or the time: on the same map the same sowing,
without it, makes woods. What bounds the wood now is a tree's life and its leaves. A tenth of the trees fall a
year, so few grow old and a wood holds 3 kg of wood a m2. A tree of 9 m carries 3 kg of leaf on a crown of 31 m2,
so the floor keeps its light.""",
    "d2": """For animals neither is a fault: open ground with a field to graze on nearly half of the land, closed
woods on a fifth, and food under the trees too.""",
    "d3": """Holds under one sowing of 256 genomes, one terrain seed, 120 years, nothing grazing. Not built: soil
and water finer than 125 m (the woods' straight edges), trees born off the 5 m grid, a fire front that is round.""",
    "conclusion": """Yes, yes, yes, no, yes, no. A height that is what the wood can stand turns the thicket into
woods and open ground within 30 years. The floor that is not dark and the rain that does not place the wood are
left as they are. Next is rung 3: animals and their minds on this land, built in stages, its design agreed first.""",
}


def words():
    return sum(len(v.split()) for v in TEXT.values())


def t(k):
    return html.escape(" ".join(TEXT[k].split()))


def measure(k):
    name, what = t(k).split(" - ", 1)
    return f"<li><strong>{name}</strong> - {what}</li>"


def check(facts):
    """Every number the prose gives that the result files hold: stop the build if the two have parted."""
    prose = " ".join(" ".join(v.split()) for v in TEXT.values())
    for what, said in facts:
        assert said in prose, f"TEXT no longer says {said!r} ({what})"


def main():
    pre = os.path.join(RES, "main")
    w = load_world(pre)
    n, land = w["n"], w["st"]["sea"] < 0.5
    reading = read_rows("results/main_reading.csv")
    before = read_rows("../e118_plants/results/main_reading.csv")
    prov = read_rows("results/provenance.csv")
    log = read_rows("results/main_log.csv")
    blog = read_rows("../e118_plants/results/main_log.csv")
    snaps = json.load(open(pre + "_snaps.json"))
    g5 = json.load(open(pre + "_ground5.json"))
    sow, last, nt = snaps["sow"], snaps["years"][-1], len(snaps["traits"])
    side = g5["cell_m"] * (g5["n"] // n)

    f = lambda r, k: float(r[k])
    row = lambda rows, part: next(r for r in rows if r["part"] == part)
    starts = lambda rows, part: [r for r in rows if r["part"].startswith(part)]
    R, B = row(reading, "land"), row(before, "land")
    assert next(r["value"] for r in prov if r["what"] == "run") == "main" and int(next(r["value"] for r in prov if r["what"].startswith("snapshot"))) == last

    # the trees of the last snapshot, and the ground under their crowns as read.py counts it; e118's the same way
    trees = load_trees(pre, last)
    cover = crown_cover(trees, n, side)
    tr = np.fromfile(f"{pre}_traits_{last}.bin", dtype="<f4").reshape(2 * nt + 4, n, n)
    soil = land & (np.isfinite(tr[0]) | (w["ann"]["field"] > 0) | (w["ann"]["wood"] > 0))
    assert abs(cover[soil].mean() - f(R, "cover")) < 1e-6 and len(trees) == int(R["trees"]), "the trees no longer give the reading's cover"
    btrees = load_trees(OLD, last)  # not committed (7 MB): e118's snapshot of the same year
    bcover = crown_cover(btrees, n, side)
    assert len(btrees) == int(B["trees"]), "e118's trees are not the ones its reading counted"

    # the sown genomes with the most trees at the end, and each snapshot's trees by them
    ids, counts = np.unique(trees["g"], return_counts=True)
    top = [int(g) for g in ids[np.argsort(-counts)][:4]]
    share = {int(g): c / len(trees) for g, c in zip(ids, counts)}
    genes = {int(r["id"]): r for r in read_rows("results/main_genes.csv")}
    assert all(genes[g]["parent"] == "-1" for g in top), "one of the four largest genotypes was not sown"
    stand = {g: float(np.median(trees["h"][trees["g"] == g])) for g in top}
    p99 = {g: float(np.percentile(trees["h"][trees["g"] == g], 99)) for g in top}
    wshare = {g: float(trees["wood"][trees["g"] == g].sum() / trees["wood"].sum()) for g in top}
    tall = sorted(top, key=lambda g: -p99[g])[:2]
    low = [g for g in top if g not in tall]
    by_year = {y: load_trees(pre, y) for y in snaps["years"]}
    lines = {g: [float((by_year[y]["g"] == g).mean()) for y in snaps["years"]] for g in top}
    others = [1 - sum(lines[g][i] for g in top) for i in range(len(snaps["years"]))]

    ages = starts(reading, "a tree for")
    stood = starts(reading, "trees stood")[0]
    plant = [r for r in log if int(r["year"]) > sow]
    bplant = [r for r in blog if int(r["year"]) > sow]
    at = lambda rows, y: next(r for r in rows if int(r["year"]) == y)
    secs = lambda rows: sum(f(r, "secs") for r in rows) / len(rows)
    warm = starts(reading, "year's mean C")
    fire = starts(reading, "burnt % a year")
    cls = starts(reading, "crowns over % of the ground")
    bands = starts(reading, "height ")
    lows = [r for r in starts(reading, "lowland ") if r["part"].endswith("N")]
    wetdry = [r for r in starts(reading, "lowland ") if r["part"].endswith("wet over dry")]
    wet, dry = row(reading, "lowland wettest third"), row(reading, "lowland driest third")
    opn, wdd, clo = row(reading, "open ground"), row(reading, "wooded"), row(reading, "closed woods")
    cold = row(reading, "cold (under 9 C)")
    TR, TB = row(reading, "trees"), row(before, "trees")
    fallen = f(TR, "fall_a_year") / f(TR, "trees")
    young = np.median(trees["h"]), np.median(trees["leaf"]), np.pi * np.median(trees["r"]) ** 2
    check([
        ("years of plants", f"{last - sow} years"),
        ("the worst ledger error", f"{max(f(R, k) for k in ('water_err', 'a_err', 'b_err', 'c_err')):.0e}, in matter" if f(R, "c_err") >= max(f(R, k) for k in ("water_err", "a_err", "b_err")) else "matter is not the worst"),
        ("the ground under crowns", f"over {f(R, 'cover'):.1%} of the land"),
        ("e118's", f"e118 had {f(B, 'cover'):.1%}"),
        ("closed woods", f"{f(clo, 'cells') / (f(opn, 'cells') + f(wdd, 'cells')):.0%} of its cells are closed woods"),
        ("open ground", f"{f(opn, 'cells') / (f(opn, 'cells') + f(wdd, 'cells')):.0%} open ground"),
        ("open ground again", f"{f(opn, 'cells') / (f(opn, 'cells') + f(wdd, 'cells')):.0%} of the cells are open ground"),
        ("the tallest tree", f"the tallest tree is {f(R, 'tree_h_max'):.1f} m"),
        ("the tallest again", f"the tallest is {f(R, 'tree_h_max'):.1f} m"),
        ("old trees over 12 m", f"{f(stood, 'over_tall'):.0%} of the trees that have stood 50 years are over 12 m"),
        ("the floor", f"x{f(clo, 'field') / f(opn, 'field'):.2f} of the open ground's"),
        ("colder", f"{f(wdd, 'temp') - f(opn, 'temp'):.1f} C colder"),
        ("burning alike", "they burn no more" if f(opn, "burnt") < f(wdd, "burnt") * 1.1 else "open ground burns more"),
        ("wet over dry", f"x{f(wet, 'wood') / f(dry, 'wood'):.1f} of the driest third's wood"),
        ("wood thirty years after the sowing", f"The wood is {f(at(log, sow + 30), 'wood'):.2f} kg a m2 thirty years"),
        ("wood at the end", f"{f(R, 'wood'):.2f} at year {last}"),
        ("three times e118's", "three times e118's" if 2.7 < f(R, "wood") / f(B, "wood") < 3.3 else "not three times"),
        ("a year's cost", f"takes {secs(plant):.0f} s against {secs(bplant):.0f}"),
        ("the northern lowlands", f"north of 59 N are {f(lows[-1], 'cover'):.1%} under crowns"),
        ("the field under closed woods", f"holds {f(clo, 'field'):.2f} kg a m2 against {f(opn, 'field'):.2f} on open ground"),
        ("a closed wood's cover and light", f"crowns over {f(clo, 'cover'):.0%} of a closed wood's ground take {f(clo, 'crown'):.0%} of its light"),
        ("cold cells open", f"{f(cold, 'open_share'):.0%} of the cells under 9 C are open"),
        ("wood where it burns", f"{f(fire[-1], 'wood'):.2f} kg a m2 where 2% or more burns a year against {f(fire[0], 'wood'):.2f} where nothing burns"),
        ("most burnt cells wooded", "leaves most burnt cells wooded" if f(row(reading, "burnt 2% a year or more, not cold"), "open_share") < 0.5 else "burnt cells are open"),
        ("the northern bands", f"x{f(wetdry[2], 'wood'):.1f} and x{f(wetdry[3], 'wood'):.1f}"),
        ("old trees", f"hold {f(ages[3], 'wood'):.0f} kg of wood and stand {f(ages[3], 'height'):.1f} m"),
        ("the tall lines", f"hold {wshare[tall[0]] + wshare[tall[1]]:.0%} of the wood with {share[tall[0]] + share[tall[1]]:.0%} of the trees"),
        ("the low lines", f"99% of their trees under {max(p99[g] for g in low):.1f} m, with {share[low[0]] + share[low[1]]:.0%} of the trees"),
        ("trees falling", f"{fallen:.1%} of the trees fall a year"),
        ("born after the sowing", f"{f(plant[-1], 'mutant_share'):.1%} of the living mass"),
        ("a common tree", f"A tree of {young[0]:.0f} m carries {young[1]:.0f} kg of leaf on a crown of {young[2]:.0f} m2"),
        ("a wood's wood", f"a wood holds {f(wdd, 'wood'):.0f} kg of wood a m2"),
        ("the founders", f"The same {snaps['founders']} genomes are sown in year {sow}"),
        ("the bare years", f"{sow} bare years, then {last - sow} with"),
        ("the terrain", f"terrain seed {read_rows('results/main_row.csv')[0]['seed']},"),
        ("the kept years", f"years {w['years'][0]}-{w['years'][-1]}"),
    ])

    years = [int(r["year"]) for r in log]
    col = lambda rows, k, by=1.0: [float(r[k]) * by for r in rows]
    name = lambda g: f"genome {g}"
    c_land = [
        line_chart("Trees' wood, kg a m2 of the land", f"Plants are sown in year {sow} in both runs. A flat line is a store that has filled; a rising one is still filling.",
                   years, [("e119", col(log, "wood"), TREES), ("e118", col(blog, "wood"), E118)]),
        line_chart("The tallest tree, m", "e118's stops where its genomes' limits are; without the limit the tallest tree is still growing at the end.",
                   years, [("e119", col(log, "tree_h_max"), TREES), ("e118", col(blog, "tree_h_max"), E118)]),
    ]
    norm = lambda: PowerNorm(0.5, 0, 1.0)
    c_place = [
        map_chart(f"Ground under crowns, year {last}", "Share of each 125 m cell under the trees' discs (a tree's disc is 0.35 of its height in radius). Dark land has no tree.",
                  w, cover, CROWNS, norm(), [0, 0.05, 0.2, 0.5, 1], ["0%", "5%", "20%", "50%", "100%"]),
        map_chart(f"The same in e118, year {last}", "The same map, sowing and scale, with a tree's height stopped at its genome's limit.",
                  w, bcover, CROWNS, norm(), [0, 0.05, 0.2, 0.5, 1], ["0%", "5%", "20%", "50%", "100%"]),
    ]
    cname = ("under 5%", "5-20%", "20-50%", "over 50%")
    c_floor = [
        value_bars("The field by the ground under crowns, kg a m2", "The 125 m cells in four classes. A dark floor would be a last bar under half of the first.",
                   cname, [f(r, "field") for r in cls], FIELD, "share of a cell's ground under crowns", lambda v: f"{v:.2f}"),
    ]
    c_class = [
        class_chart("Ground under crowns by warmth, fire and rain", "Equal bars within a group would mean that it does not place the trees.", [
            ("the year's mean temperature", [(nm, f(r, "cover")) for nm, r in zip(("under 9 C", "9-11 C", "11-13 C", "13-15 C", "over 15 C"), warm)]),
            ("share of the ground that burns a year", [(nm, f(r, "cover")) for nm, r in zip(("none", "under 2%", "2% or more"), fire)]),
            ("the lowlands by rain", [(f"wettest third ({wet['rain']} mm)", f(wet, "cover")), (f"driest third ({dry['rain']} mm)", f(dry, "cover"))]),
        ], TREES, "share of the ground under crowns"),
    ]
    c_height = [
        wood_height_chart(f"Each tree's height against its wood, year {last}", "A dot is a tree (6,000 of them). On the curve its wood stands as high as a stem can; below it, it has more leaf to hold up.",
                          trees, [(g, name(g), i) for i, g in enumerate(top)]),
        stacked_area("The trees by sown genome", "Share of the trees at each of the twelve snapshots. All four named were sown in year 10; a new line would grow out of 'others'.",
                     snaps["years"], [(name(g), lines[g], SERIES[i]) for i, g in enumerate(top)] + [("others", others, INK)], size=(6.4, 3.4)),
    ]

    pct = lambda v, d=1: f"{100 * float(v):.{d}f}%"
    both = lambda k, fmt: [fmt(R[k]), fmt(B[k])]
    summary = [
        ["field, kg a m2"] + both("field", lambda v: f"{float(v):.2f}"),
        ["litter, kg a m2"] + both("litter", lambda v: f"{float(v):.2f}"),
        ["trees' wood, kg a m2"] + both("wood", lambda v: f"{float(v):.2f}"),
        ["trees"] + both("trees", lambda v: f"{int(v):,}"),
        ["ground under crowns"] + both("cover", pct),
        [f"light taken by crowns (years {w['years'][0]}-{w['years'][-1]})"] + both("crown", pct),
        ["125 m cells that are closed woods / open ground", f"{f(clo, 'cells') / soil.sum():.0%} / {f(opn, 'cells') / soil.sum():.0%}",
         f"{(bcover[soil] >= 0.5).mean():.0%} / {(bcover[soil] < 0.05).mean():.0%}"],
        ["tallest tree, m"] + both("tree_h_max", lambda v: f"{float(v):.1f}"),
        ["median tree, m", f"{np.median(trees['h']):.1f}", f"{np.median(btrees['h']):.1f}"],
        ["trees falling a year"] + [f"{f(x, 'fall_a_year'):,.0f} ({f(x, 'fall_a_year') / f(x, 'trees'):.1%})" for x in (TR, TB)],
        ["genotypes with a tree"] + [x["genotypes"] for x in (TR, TB)],
        ["born after the sowing, of the living mass"] + [pct(x[-1]["mutant_share"]) for x in (log, blog)],
        ["a year of plants on six threads, s"] + [f"{secs(x):.0f}" for x in (plant, bplant)],
        ["worst ledger error (matter)"] + both("c_err", lambda v: f"{float(v):.0e}"),
    ]
    age_rows = [[r["part"].replace("a tree for ", "").replace("50-200", "over 50"), f"{int(r['trees']):,}", f"{f(r, 'height'):.1f}", f"{f(r, 'wood'):.0f}",
                 f"{H_STEM * f(r, 'wood') ** 0.25:.1f}"] for r in ages]

    tables = folded("How the run was read (results/provenance.csv)", table(["what", "value"], [[r["what"], r["value"]] for r in prov]), shown=True)
    tables += folded("Open ground, wooded ground and closed woods (results/main_reading.csv)", table(
        ["", "125 m cells", "under crowns", "light taken by crowns", "trees' wood, kg a m2", "field, kg a m2", "year's mean, C", "rain, mm", "burns a year"],
        [[r["part"], r["cells"], pct(r["cover"]), pct(r["crown"]), f"{f(r, 'wood'):.2f}", f"{f(r, 'field'):.2f}", f"{f(r, 'temp'):.1f}", r["rain"], pct(r["burnt"], 2)] for r in (opn, wdd, clo)])
        + table(["cells that are", "125 m cells", "under crowns", "open ground among them", "their share of the open ground"],
                [[r["part"], r["cells"], pct(r["cover"]), pct(r["open_share"], 0), pct(r["of_open"], 0)] for r in (cold, row(reading, "burnt 2% a year or more, not cold"), row(reading, "neither"))]))
    tables += folded("By height", table(
        ["land at", "125 m cells", "under crowns", "trees' wood, kg a m2", "field, kg a m2", "tallest tree, m"],
        [[r["part"].replace("height ", ""), r["cells"], pct(r["cover"]), f"{f(r, 'wood'):.2f}", f"{f(r, 'field'):.2f}", f"{f(r, 'tree_h_max'):.1f}"] for r in bands]))
    tables += folded("Lowlands by latitude", table(
        ["lowlands at", "125 m cells", "rain, mm", "under crowns", "trees' wood, kg a m2", "field, kg a m2", "burns a year", "wood, wettest third over driest"],
        [[r["part"].replace("lowland ", "").replace("N", " N"), r["cells"], r["rain"], pct(r["cover"]), f"{f(r, 'wood'):.2f}", f"{f(r, 'field'):.2f}", pct(r["burnt"], 2), f"x{f(x, 'wood'):.1f}"]
         for r, x in zip(lows, wetdry)]))
    tables += folded("By warmth, by fire and by the ground under crowns", table(
        ["class", "125 m cells", "under crowns", "trees' wood, kg a m2", "field, kg a m2", "burns a year"],
        [[r["part"].replace("-50 to 9", "under 9").replace("15 to 50", "over 15").replace("-1 to 0.01", "none").replace("2 to 101", "2 or more").replace("-1 to 5", "under 5").replace("50 to 101", "over 50"),
          r["cells"], pct(r["cover"]), f"{f(r, 'wood'):.2f}", f"{f(r, 'field'):.2f}", pct(r["burnt"], 2)] for r in warm + fire + cls]))
    tables += folded("Traits north and south (the mean of the genotypes by mass)", table(
        ["", "leaf A", "shed a year", "optimum, C", "share to wood"],
        [[r["part"].replace(" traits", ",").replace("N", " N"), pct(r["leaf_a"], 2), f"{f(r, 'shed'):.2f}", f"{f(r, 't_opt'):.1f}", f"{f(r, 'alloc_wood'):.2f}"]
         for r in starts(reading, "field traits") + starts(reading, "trees traits")]))
    tables += folded("The four sown genomes with the most trees", table(
        ["", "of the trees", "of the wood", "median height, m", "1% are over, m"],
        [[name(g), f"{share[g]:.0%}", f"{wshare[g]:.0%}", f"{stand[g]:.1f}", f"{p99[g]:.1f}"] for g in top]))
    tables += folded("The trees by sown genome at each snapshot", table(
        ["year", "trees"] + [name(g) for g in top] + ["others"],
        [[y, f"{len(by_year[y]):,}"] + [f"{lines[g][i]:.0%}" for g in top] + [f"{others[i]:.0%}"] for i, y in enumerate(snaps["years"])]))
    for nm, rows in (("e119 main", log), ("e118 main", blog)):
        tables += folded(f"{nm}, every tenth year", table(
            ["year", "field", "litter", "trees' wood", "trees", "light taken by crowns", "tallest, m", "fallen in the year", "fine cells burnt"],
            [[r["year"], f"{f(r, 'field'):.2f}", f"{f(r, 'litter'):.2f}", f"{f(r, 'wood'):.2f}", f"{int(r['trees']):,}", pct(r["crown"]), f"{f(r, 'tree_h_max'):.1f}",
              f"{int(r['fallen']):,}", f"{int(r['burnt_cells']):,}"] for r in rows if int(r["year"]) % 10 == 0 and int(r["year"]) > sow]))

    gallery = pair(("wood_near", "A wood seen from just above its crowns: large trees stand over small ones, with a stream between them", t("g1")),
                   ("wood_above", "The same slope from above: a closed wood in a hollow, scattered large trees, and young trees in regular rows", t("g2")))

    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>e119 A Height the Wood Can Stand - Report</title>
<style>{CSS}</style>
</head>
<body>
<main>
<h1>e119: does a height the wood can stand turn the thicket into woods and open ground?</h1>
<p class="sub">Experiment report - 2026-11-15 - rung 2 of #135 corrected: 120 years of plants on the 16 km map of islands, terrain seed 23, one run read beside e118's</p>

<section class="tldr">
<h2>TL;DR</h2>
<p>{t("tldr")}</p>
</section>

<h2>1. Question</h2>
<p>{t("question")}</p>
<ol>
  <li>{t("h1")}</li>
  <li>{t("h2")}</li>
  <li>{t("h3")}</li>
  <li>{t("h4")}</li>
  <li>{t("h5")}</li>
  <li>{t("h6")}</li>
</ol>

<h2>2. The world</h2>
<p>{t("world")}</p>
{diagram()}
<p><strong>Runs.</strong> {t("runs").replace("main,", "<code>main</code>,").replace("e118's main", "e118's <code>main</code>")}</p>
<ul class="measures">
  {measure("m1")}
  {measure("m2")}
  {measure("m3")}
  {measure("m4")}
  {measure("m5")}
</ul>

<h2>3. Results</h2>
{table([f"year {last}", "e119", "e118"], summary)}
{table(["e119: a tree for (years)", "trees", "median height, m", "median wood, kg", "a stem of that wood could stand, m"], age_rows)}
<ol class="verdicts">
<li><span class="verdict">Yes</span> {t("v1")}</li>
<li><span class="verdict">Yes</span> {t("v2")}</li>
<li><span class="verdict">Yes</span> {t("v3")}</li>
<li><span class="verdict no">No</span> {t("v4")}</li>
<li><span class="verdict">Yes</span> {t("v5")}</li>
<li><span class="verdict no">No</span> {t("v6")}</li>
</ol>

<h3>3.1 Three times the wood within thirty years, and then level</h3>
<div class="grid2">
{"".join(c_land)}
</div>
<p>{t("r1")}</p>

<h3>3.2 The land parted into woods and open ground; no floor is dark</h3>
<div class="grid2">
{"".join(c_place)}
</div>
<div class="grid2" style="margin-top:20px">
{"".join(c_floor)}
</div>
<p>{t("r2")}</p>

<h3>3.3 Open ground is the cold; rain does not place the wood</h3>
<div class="grid2">
{"".join(c_class)}
</div>
<p>{t("r3")}</p>

<h3>3.4 A height follows its wood, and two tall lines hold most of it</h3>
<div class="grid2">
{"".join(c_height)}
</div>
<p>{t("r4")}</p>

<h3>3.5 On the screen</h3>
{gallery}

<h2>4. Discussion</h2>
<p>{t("d1")}</p>
<p>{t("d2")}</p>
<p>{t("d3")}</p>

<h2>5. Conclusion and next step</h2>
<p>{t("conclusion")}</p>

<h2>Appendix: data</h2>
<p>The tables above are <code>results/main_reading.csv</code> and e118's, written by each experiment's
<code>read.py</code>; the charts are drawn from <code>results/main_log.csv</code>, <code>results/main_maps.bin</code> and
the trees' snapshots <code>results/main_trees_*.bin</code> of both experiments with the same classes (the snapshots are
not committed). The looks are the viewer's map page (<code>viewer map</code>), whose panel is in Japanese. Build this
report with <code>uv run python experiments/e119_height/report.py</code>.</p>
{tables}
</main>
</body>
</html>
"""
    out = os.path.join(HERE, "report.html")
    with open(out, "w") as fh:
        fh.write(page)
    print(f"wrote {out} ({os.path.getsize(out)//1024} KB), TEXT {words()} words")
    assert words() <= 1000, "the prose is over the skill's budget of 1,000 words"
    for k, v in TEXT.items():
        print(f"  {k}: {len(v.split())}")


if __name__ == "__main__":
    main()
