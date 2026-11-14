#!/usr/bin/env python3
"""Build report.html for this experiment.

Charts and maps: matplotlib, exported as SVG and inlined. Diagram: hand-written SVG. Two looks at the map page
(shots/*.jpg) are embedded, so the page stands alone.
Run from the repo root: uv run python experiments/e118_plants/report.py
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
# The same thing has the same colour in every chart: trees (of `main`) blue, `dense` orange, the field aqua,
# litter yellow; among the sown genomes the 5.2 m line blue, the 8.5 m line orange.
TREES, DENSE, FIELD, LITTER = 0, 1, 2, 3

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
                    bbox_to_anchor=(0, 1.0), ncols=len(lines) + 2, handlelength=1.2, borderaxespad=0, columnspacing=1.2, handletextpad=0.4, markerscale=2.5)
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

# Hand-written mechanism diagram: currentColor for lines and text, var(--s1) for the height limit, the one thing
# the result hangs on. The numbers in braces come from results/main_reading.csv.
DIAGRAM = """
<figure class="diagram">
<svg viewBox="0 0 900 336" role="img" aria-label="A stand of many stems thins into one tree of a 5 m cell; light falls through crowns and then the field, all plants of a 125 m cell draw on one soil, fire runs over the field, and a tree's height stops at its genome's limit" style="max-width:100%;height:auto;display:block">
<defs><marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="currentColor"/></marker></defs>
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

  <text x="370" y="22" fill="currentColor" stroke="none" font-weight="600">What a plant takes, and what stops it</text>
  <rect x="370" y="250" width="520" height="58" fill="currentColor" fill-opacity="0.08" stroke="none"/>
  <line x1="370" y1="250" x2="890" y2="250"/>
  {tufts}
  <line x1="540" y1="250" x2="540" y2="162"/>
  <ellipse cx="540" cy="130" rx="46" ry="32" fill="currentColor" fill-opacity="0.08"/>
  <line x1="540" y1="250" x2="526" y2="268"/><line x1="540" y1="250" x2="540" y2="272"/><line x1="540" y1="250" x2="554" y2="268"/>
  <text x="712" y="276" text-anchor="middle" fill="currentColor" stroke="none">one soil a 125 m cell: every plant</text>
  <text x="712" y="294" text-anchor="middle" fill="currentColor" stroke="none">rooted in it draws on its water</text>
  <line x1="380" y1="98" x2="604" y2="98" stroke="var(--s1)" stroke-width="2"/>
  <text x="526" y="68" text-anchor="end" fill="currentColor" stroke="none">height stops at the genome's</text>
  <text x="526" y="84" text-anchor="end" fill="currentColor" stroke="none">limit: {h1} or {h2} m</text>
  <line x1="540" y1="94" x2="540" y2="46" stroke-dasharray="4 4" marker-end="url(#arr)"/>
  <text x="554" y="50" fill="currentColor" stroke="none">{kg} kg of wood could stand {could} m</text>
  <line x1="700" y1="84" x2="594" y2="122" marker-end="url(#arr)"/>
  <text x="712" y="84" fill="currentColor" stroke="none">light: the crowns first,</text>
  <text x="712" y="100" fill="currentColor" stroke="none">the tallest on top</text>
  <line x1="590" y1="152" x2="634" y2="236" stroke-dasharray="4 4" marker-end="url(#arr)"/>
  <text x="630" y="172" fill="currentColor" stroke="none">what is left,</text>
  <text x="630" y="188" fill="currentColor" stroke="none">to the field</text>
  <path d="M786,250 q-10,-17 3,-30 q1,11 9,13 q-3,-14 8,-24 q12,17 7,41 z" fill="currentColor" fill-opacity="0.25"/>
  <line x1="826" y1="232" x2="880" y2="232" marker-end="url(#arr)"/>
  <text x="768" y="176" fill="currentColor" stroke="none">fire runs over</text>
  <text x="768" y="192" fill="currentColor" stroke="none">the field</text>
</g>
</svg>
<figcaption>Figure 1. Left: a stand of the field is many stems, each as high as its wood lets one stem stand (4.2 m at a
kg, by the wood's fourth root). As the wood grows the stems thin, and at one stem a 5 m cell the stand is a tree, with a
place and a crown 0.35 of its height in radius. Right: light falls through the crowns over a cell, then through its
field; every plant of a 125 m cell draws on one soil; fire runs from fine cell to fine cell over grass and litter, and
shaded fuel dries a fifth as fast. A tree's height is the lesser of what its wood can stand and its genome's limit (blue).</figcaption>
</figure>
"""


def diagram(h1, h2, kg, could):
    stems = "".join(f'<line x1="{x}" y1="250" x2="{x}" y2="233"/><circle cx="{x}" cy="227" r="5.5" fill="currentColor" fill-opacity="0.08"/>'
                    for x in (40, 52, 64, 76, 88, 100, 112))
    stems += "".join(f'<line x1="{x}" y1="250" x2="{x}" y2="206"/><circle cx="{x}" cy="192" r="13.5" fill="currentColor" fill-opacity="0.08"/>'
                     for x in (137, 165, 193))
    tufts = '<g stroke-opacity="0.75">' + "".join(
        f'<line x1="{x}" y1="250" x2="{x - 3}" y2="241"/><line x1="{x}" y1="250" x2="{x + 3}" y2="241"/>'
        for x in range(384, 884, 14) if abs(x - 540) > 10 and not 776 < x < 820) + "</g>"
    return DIAGRAM.format(stems=stems, tufts=tufts, h1=h1, h2=h2, kg=kg, could=could)


# Every sentence of the report's prose, so that its words can be counted against the skill's budgets.
TEXT = {
    "tldr": """Plants now grow at metres on the 16 km map: a field on 5 m cells, and trees as things. After 120
years every ledger closes, but the land is a thicket with young trees, not woods and open ground: crowns stand over
5.7% of it. A tree's wood grows and its height does not: height is its genome's limit, and two sown genomes are 94% of
the trees. Kept as it is for the next rung.""",
    "question": """An animal lives among plants of its own size, so the producers, cohorts on 125 m cells, are
rebuilt at metres; nothing eats them yet. We expected the climate to place wood and open ground:""",
    "h1": "It stands 100 years with every ledger closed.",
    "h2": "Crowns cover 20-70% of the land; wet windward ground holds three times the wood of the lee and the south's lowlands.",
    "h3": "There is a tree line.",
    "h4": "Leaves differ between north and south.",
    "h5": "The trees at year 100 are not the sown ones.",
    "world": """The field lives on fine cells of 5 m. A stand of it is many stems; thinned to one stem a cell it
is a tree, a thing with a place, a height and a crown (Figure 1). In year 10, 256 random genomes are sown on every
cell with soil.""",
    "runs": """Two runs on Ubuntu, six threads, terrain seed 23, 90 minutes each: 10 bare years, then 120 with
plants. main is read at year 130, its maps as the mean of years 121-130. dense, the first long run, packed a new
tree's leaves into a narrow crown. We read:""",
    "m1": "ground under crowns - the share of the ground under the trees' discs; 0 is no tree.",
    "m2": "light taken by crowns - the share of the land's light the trees take; the field has the rest.",
    "m3": "field - all that is not a tree: grass and stands of many stems.",
    "m4": "what the wood could stand - 4.2 m at a kg, by the wood's fourth root; a tree under it is held by its genome.",
    "m5": "sown genome - one of the 256 of year 10; its trees are a line.",
    "v1": "hypothesis 1: 120 years of plants, and the worst ledger error is 1e-10, in matter.",
    "v2": """hypothesis 2: crowns stand over 5.7% of the ground (asked 20-70%), and the lowlands' wettest and
driest thirds hold the same wood, 0.28 kg a m2.""",
    "v3": """hypothesis 3: by cold. Crowns stand over 9.5% of the ground at 1,200-1,400 m and 1.0% above, and
over 0.1% of the lowlands north of 59 N.""",
    "v4": """hypothesis 4: the field's optimum is 12.8 C in the south and 11.9 C in the north, and it sheds
0.44 and 0.45 of its leaves a year.""",
    "v5": """hypothesis 5: as lives yes, as lines no. 0.6% of the trees were trees by year 30, but two of the
256 sown genomes are 94% of them.""",
    "r1": """The field fills the land within thirty years and then holds. What still moves is the trees' wood: it
doubled in the last 60 years and is still rising, so year 130 is a transient. Stands of 0.5-5 m hold 64% of the fine
cells, with trees among them: a thicket, where a closed wood with a dark floor was expected.""",
    "r2": """Trees stand where it is warm and where fire does not come: crowns are over 11.0% of the ground where
the year's mean is above 15 C and 0.6% under 9 C, over 6.7% where nothing burns and 2.1% where 2% or more burns a year.
Water does not place them: the lowlands' driest third gets 311 mm a year, the wettest 870 mm, and they hold the same
wood.""",
    "r3": """Trees of over 50 years hold 304 kg of wood and stand 8.5 m, as trees of 20-50 years do with 89 kg; a
stem of 304 kg could stand 17.5 m. Height stops at the genome's limit, 5.2 and 8.5 m for the two lines; wood goes
on growing. A taller wood needs a taller line, and what was born after the sowing is 1.3%
of the living mass.""",
    "r4": """In dense a stand counted a tree had its leaves packed into a crown a seventh of its cell, and its
light halved. The run ended with 252,065 trees whose crowns stood over 0.9% of the ground; 44% had a leaf at the
winter's end, against 98% in main. A tree's crown is now its height's, as the stand's was: nothing changes the day a
stand is counted a tree.""",
    "g1": "From a walker's height at year 130: a wood reads as a wood.",
    "g2": "From above: the wood's edges are straight lines 125 m apart, where the soil's cells differ.",
    "d1": """What bounds the wood is not the climate but what was sown and how a height is made. Two founders'
lines became the trees, and 120 years is a few tree lives: too short for a taller line to be born and spread. Under
crowns as thin as theirs (a leaf area of 1-2) the field keeps most of its light, so no floor goes dark and no wood
closes.""",
    "d2": """The reading holds under one sowing of 256 genomes, one terrain seed, 120 years and nothing grazing.
long, 500 years of the same world, is running.""",
    "d3": """Not built: soil and water finer than 125 m (the woods' straight edges), a fire front that is round
(scars are diamonds), small eaters of leaves, the sea's producers.""",
    "conclusion": """Yes, no, yes, no, and lives but not lines. Plants at metres stand, and what they make in 120
years is a thicket with young trees, bounded by two sown lines' height limits and not by the climate. The laws stay in
this crate for the next rung and go to base/ when animals stand on them.""",
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
    dense = read_rows("results/dense_reading.csv")
    prov = read_rows("results/provenance.csv")
    log = read_rows("results/main_log.csv")
    dlog = read_rows("results/dense_log.csv")
    snaps = json.load(open(pre + "_snaps.json"))
    g5 = json.load(open(pre + "_ground5.json"))
    sow, last, nt = snaps["sow"], snaps["years"][-1], len(snaps["traits"])
    side = g5["cell_m"] * (g5["n"] // n)

    f = lambda r, k: float(r[k])
    row = lambda rows, part: next(r for r in rows if r["part"] == part)
    starts = lambda rows, part: [r for r in rows if r["part"].startswith(part)]
    R, D = row(reading, "land"), row(dense, "land")
    assert next(r["value"] for r in prov if r["what"] == "run") == "main" and int(next(r["value"] for r in prov if r["what"].startswith("snapshot"))) == last

    # the trees of the last snapshot, and the ground under their crowns as read.py counts it
    trees = load_trees(pre, last)
    cover = crown_cover(trees, n, side)
    tr = np.fromfile(f"{pre}_traits_{last}.bin", dtype="<f4").reshape(2 * nt + 4, n, n)
    soil = land & (np.isfinite(tr[0]) | (w["ann"]["field"] > 0) | (w["ann"]["wood"] > 0))
    assert abs(cover[soil].mean() - f(R, "cover")) < 1e-6 and len(trees) == int(R["trees"]), "the trees no longer give the reading's cover"

    # the sown genomes with the most trees at the end, and each snapshot's trees by them
    ids, counts = np.unique(trees["g"], return_counts=True)
    top = [int(g) for g in ids[np.argsort(-counts)][:4]]
    share = {int(g): c / len(trees) for g, c in zip(ids, counts)}
    genes = {int(r["id"]): r for r in read_rows("results/main_genes.csv")}
    assert all(genes[g]["parent"] == "-1" for g in top), "one of the four largest genotypes was not sown"
    stand = {g: float(np.median(trees["h"][trees["g"] == g])) for g in top}
    by_year = {y: load_trees(pre, y) for y in snaps["years"]}
    lines = {g: [float((by_year[y]["g"] == g).mean()) for y in snaps["years"]] for g in top}
    others = [1 - sum(lines[g][i] for g in top) for i in range(len(snaps["years"]))]

    ages = starts(reading, "a tree for")
    old, mid, young = ages[3], ages[2], ages[1]
    plant = [r for r in log if int(r["year"]) > sow]
    half = plant[len(plant) // 2]
    classes = row(reading, "field stands by height (share of fine cells)")
    stands = [("no leaf", f(classes, "no_leaf")), ("under 0.5 m", f(classes, "under_0.5_m")), ("0.5-2 m", f(classes, "0.5-2_m")),
              ("2-5 m", f(classes, "2-5_m")), ("over 5 m", f(classes, "over_5_m"))]
    fp = pre + f"_field_{last}.bin"  # 51 MB and not committed: when it is here, the reading's row is checked against it
    if os.path.exists(fp):
        k, nn = g5["n"] // n, g5["n"] ** 2
        fb = np.fromfile(fp, dtype=np.uint8)
        leaf5, tall5, lit5 = fb[:nn] / 100, fb[nn:2 * nn] / 25, fb[2 * nn:3 * nn] / 50
        s5 = np.kron(land, np.ones((k, k), bool)).ravel() & ((leaf5 > 0) | (lit5 > 0) | (tall5 > 0))
        mid5 = ((tall5[s5] >= 0.5) & (tall5[s5] < 5)).mean()
        assert abs(mid5 - stands[2][1] - stands[3][1]) < 1e-3, "the field's snapshot no longer gives the reading's stands"

    warm = starts(reading, "year's mean C")
    fire = starts(reading, "burnt % a year")
    bands = starts(reading, "height ")
    lows = [r for r in starts(reading, "lowland ") if r["part"].endswith("N")]
    wet, dry = row(reading, "lowland wettest third"), row(reading, "lowland driest third")
    ft = starts(reading, "field traits")
    check([
        ("years of plants", f"{last - sow} years"),
        ("the worst ledger error", f"{max(f(R, k) for k in ('water_err', 'a_err', 'b_err', 'c_err')):.0e}, in matter" if f(R, "c_err") >= max(f(R, k) for k in ("water_err", "a_err", "b_err")) else "matter is not the worst"),
        ("the ground under crowns", f"over {f(R, 'cover'):.1%} of"),
        ("the two largest sown genomes", f"{share[top[0]] + share[top[1]]:.0%} of"),
        ("wood on the wettest lowlands", f"{f(wet, 'wood'):.2f} kg a m2"),
        ("wood on the driest", f"{f(dry, 'wood'):.2f} kg a m2"),
        ("rain on the driest third", f"gets {f(dry, 'rain'):.0f} mm"),
        ("rain on the wettest", f"wettest {f(wet, 'rain'):.0f} mm"),
        ("under crowns in the last band under the line", f"{f(bands[-2], 'cover'):.1%} of the ground at 1,200-1,400 m"),
        ("above it", f"{f(bands[-1], 'cover'):.1%} above"),
        ("the northern lowlands", f"over {f(lows[-1], 'cover'):.1%} of the lowlands north of 59 N"),
        ("the field's optimum, south", f"{f(ft[0], 't_opt'):.1f} C in the south"),
        ("north", f"{f(ft[1], 't_opt'):.1f} C in the north"),
        ("the field's shedding", f"{f(ft[0], 'shed'):.2f} and {f(ft[1], 'shed'):.2f} of its leaves"),
        ("the first trees", f"{f(row(reading, 'trees'), 'first_share'):.1%} of the trees were trees by year {sow + 20}"),
        ("the founders", f"In year {sow}, {snaps['founders']} random genomes"),
        ("the bare years", f"{sow} bare years, then {last - sow} with"),
        ("the terrain", f"terrain seed {read_rows('results/main_row.csv')[0]['seed']},"),
        ("wood, last year against half way", f"doubled in the last {last - int(half['year']) + 1} years" if 1.9 < f(R, "wood") / f(half, "wood") < 2.1 else "wood did not double"),
        ("stands of 0.5-5 m", f"hold {stands[2][1] + stands[3][1]:.0%} of the fine cells"),
        ("warmest class", f"over {f(warm[-1], 'cover'):.1%} of the ground where the year's mean is above 15 C"),
        ("coldest class", f"{f(warm[0], 'cover'):.1%} under 9 C"),
        ("where nothing burns", f"over {f(fire[0], 'cover'):.1%} where nothing burns"),
        ("where much burns", f"{f(fire[-1], 'cover'):.1%} where 2% or more burns"),
        ("the oldest trees' wood", f"hold {f(old, 'wood'):.0f} kg of wood and stand {f(old, 'height'):.1f} m"),
        ("the middle trees' wood", f"with {f(mid, 'wood'):.0f} kg"),
        ("what that wood could stand", f"could stand {H_STEM * f(old, 'wood') ** 0.25:.1f} m"),
        ("the two lines as they stand", f"{stand[top[0]]:.1f} and {stand[top[1]]:.1f} m for the two lines"),
        ("born after the sowing", f"{f(plant[-1], 'mutant_share'):.1%} of the living mass"),
        ("dense's trees", f"{int(D['trees']):,} trees"),
        ("dense's cover", f"over {f(D, 'cover'):.1%} of the ground; 44%"),
        ("main's trees in leaf", f"against {(trees['leaf'] > 0.01).mean():.0%} in main"),
        ("the kept years", f"years {w['years'][0]}-{w['years'][-1]}"),
    ])

    years = [int(r["year"]) for r in log]
    col = lambda rows, k, by=1.0: [float(r[k]) * by for r in rows]
    name = lambda g: f"genome {g}"
    c_land = [
        line_chart("Field, litter and trees' wood, kg a m2 of the land", f"Plants are sown in year {sow}. A flat line is a store that has filled; a rising one is still filling.",
                   years, [("field", col(log, "field"), FIELD), ("litter", col(log, "litter"), LITTER), ("trees' wood", col(log, "wood"), TREES)]),
        bar_chart(f"The field's stands by height, year {last}", "Share of the fine cells with soil. A wood's dark floor would be a tall bar at 'no leaf' or 'under 0.5 m'.",
                  [s[0] for s in stands], [s[1] for s in stands], FIELD, "height of the field's stand on a 5 m cell"),
    ]
    c_place = [
        map_chart(f"Ground under crowns, year {last}", "Share of each 125 m cell under the trees' discs (a tree's disc is 0.35 of its height in radius). Dark land has no tree.",
                  w, cover, CROWNS, PowerNorm(0.5, 0, 0.6), [0, 0.05, 0.2, 0.5], ["0%", "5%", "20%", "50%"], extend="max"),
        map_chart("The year's mean temperature, C", f"Mean of years {w['years'][0]}-{w['years'][-1]}, in the five classes of the bars below. Read it against the map on the left.",
                  w, w["ann"]["temp"], WARMTH, BoundaryNorm([-50, 9, 11, 13, 15, 50], 5), [9, 11, 13, 15], ["9", "11", "13", "15"]),
    ]
    c_class = [
        class_chart("Ground under crowns by warmth, fire and rain", "Equal bars within a group would mean that it does not place the trees.", [
            ("the year's mean temperature", [(nm, f(r, "cover")) for nm, r in zip(("under 9 C", "9-11 C", "11-13 C", "13-15 C", "over 15 C"), warm)]),
            ("share of the ground that burns a year", [(nm, f(r, "cover")) for nm, r in zip(("none", "under 2%", "2% or more"), fire)]),
            ("the lowlands by rain", [(f"wettest third ({wet['rain']} mm)", f(wet, "cover")), (f"driest third ({dry['rain']} mm)", f(dry, "cover"))]),
        ], TREES, "share of the ground under crowns"),
    ]
    c_height = [
        wood_height_chart(f"Each tree's height against its wood, year {last}", "A dot is a tree (6,000 of them). On the curve, wood limits the height; in a flat row under it, the genome does.",
                          trees, [(top[0], name(top[0]), 0), (top[1], name(top[1]), 1)]),
        stacked_area("The trees by sown genome", "Share of the trees at each of the twelve snapshots. All four named were sown in year 10; a new line would grow out of 'others'.",
                     snaps["years"], [(name(g), lines[g], SERIES[i]) for i, g in enumerate(top)] + [("others", others, INK)], size=(6.4, 3.4)),
    ]
    c_dense = [
        line_chart("Light taken by crowns, main against dense", "Share of the land's light. The two runs differ only in how wide a new tree's crown is.",
                   years, [("main", col(log, "crown", 100), TREES), ("dense", col(dlog, "crown", 100), DENSE)], yfmt=lambda y, _p: f"{y:g}%"),
    ]

    pct = lambda v, d=1: f"{100 * float(v):.{d}f}%"
    both = lambda k, fmt: [fmt(R[k]), fmt(D[k])]
    TR, TD = row(reading, "trees"), row(dense, "trees")
    summary = [
        ["field, kg a m2"] + both("field", lambda v: f"{float(v):.2f}"),
        ["litter, kg a m2"] + both("litter", lambda v: f"{float(v):.2f}"),
        ["trees' wood, kg a m2"] + both("wood", lambda v: f"{float(v):.2f}"),
        ["trees"] + both("trees", lambda v: f"{int(v):,}"),
        ["ground under crowns"] + both("cover", pct),
        [f"light taken by crowns (years {w['years'][0]}-{w['years'][-1]})"] + both("crown", pct),
        ["tallest tree, m"] + both("tree_h_max", lambda v: f"{float(v):.1f}"),
        ["trees falling a year"] + [f"{f(x, 'fall_a_year'):,.0f} ({f(x, 'fall_a_year') / f(x, 'trees'):.1%})" for x in (TR, TD)],
        ["trees that were trees by year 30"] + [pct(x["first_share"]) for x in (TR, TD)],
        ["genotypes with a tree"] + [x["genotypes"] for x in (TR, TD)],
        ["born after the sowing, of the living mass"] + [pct(x[-1]["mutant_share"]) for x in (log, dlog)],
        ["worst ledger error (matter)"] + both("c_err", lambda v: f"{float(v):.0e}"),
    ]
    age_rows = [[r["part"].replace("a tree for ", "").replace("50-200", "over 50"), f"{int(r['trees']):,}", f"{f(r, 'height'):.1f}", f"{f(r, 'wood'):.0f}",
                 f"{H_STEM * f(r, 'wood') ** 0.25:.1f}"] for r in ages]

    north = land.copy()
    north[:3 * n // 4] = False
    lowland = float(next(r["value"] for r in prov if r["what"].startswith("lowland")))
    north &= soil & (w["st"]["elev"] < lowland)
    tables = folded("How the run was read (results/provenance.csv)", table(["what", "value"], [[r["what"], r["value"]] for r in prov]), shown=True)
    tables += folded("By height (results/main_reading.csv)", table(
        ["land at", "125 m cells", "under crowns", "trees' wood, kg a m2", "field, kg a m2", "tallest tree, m"],
        [[r["part"].replace("height ", ""), r["cells"], pct(r["cover"]), f"{f(r, 'wood'):.2f}", f"{f(r, 'field'):.2f}", f"{f(r, 'tree_h_max'):.1f}"] for r in bands]))
    tables += folded("Lowlands by latitude", table(
        ["lowlands at", "125 m cells", "rain, mm", "under crowns", "trees' wood, kg a m2", "field, kg a m2", "burns a year"],
        [[r["part"].replace("lowland ", "").replace("N", " N"), r["cells"], r["rain"], pct(r["cover"]), f"{f(r, 'wood'):.2f}", f"{f(r, 'field'):.2f}", pct(r["burnt"], 2)] for r in lows])
        + f"<p>The lowlands north of 59 N have a mean of {w['ann']['temp'][north].mean():.1f} C over years {w['years'][0]}-{w['years'][-1]}.</p>")
    tables += folded("By warmth and by fire", table(
        ["class", "125 m cells", "under crowns", "trees' wood, kg a m2", "field, kg a m2"],
        [[r["part"].replace("-50 to 9", "under 9").replace("15 to 50", "over 15").replace("-1 to 0.01", "none").replace("2 to 101", "2 or more"),
          r["cells"], pct(r["cover"]), f"{f(r, 'wood'):.2f}", f"{f(r, 'field'):.2f}"] for r in warm + fire]))
    tables += folded("Traits north and south (the mean of the genotypes by mass)", table(
        ["", "leaf A", "shed a year", "optimum, C", "height limit, m", "share to wood"],
        [[r["part"].replace(" traits", ",").replace("N", " N"), pct(r["leaf_a"], 2), f"{f(r, 'shed'):.2f}", f"{f(r, 't_opt'):.1f}", f"{f(r, 'height'):.1f}", f"{f(r, 'alloc_wood'):.2f}"]
         for r in starts(reading, "field traits") + starts(reading, "trees traits")]))
    tables += folded("The trees by sown genome at each snapshot", table(
        ["year", "trees"] + [f"{name(g)} (stands {stand[g]:.1f} m)" for g in top] + ["others"],
        [[y, f"{len(by_year[y]):,}"] + [f"{lines[g][i]:.0%}" for g in top] + [f"{others[i]:.0%}"] for i, y in enumerate(snaps["years"])]))
    for nm, rows in (("main", log), ("dense", dlog)):
        tables += folded(f"{nm}, every tenth year (results/{nm}_log.csv)", table(
            ["year", "field", "litter", "trees' wood", "trees", "light taken by crowns", "tallest, m", "fallen in the year", "fine cells burnt"],
            [[r["year"], f"{f(r, 'field'):.2f}", f"{f(r, 'litter'):.2f}", f"{f(r, 'wood'):.2f}", f"{int(r['trees']):,}", pct(r["crown"]), f"{f(r, 'tree_h_max'):.1f}",
              f"{int(r['fallen']):,}", f"{int(r['burnt_cells']):,}"] for r in rows if int(r["year"]) % 10 == 0 and int(r["year"]) > sow]))

    gallery = pair(("wood_near", "A wood seen from a walker's height: crowns close together over a slope", t("g1")),
                   ("wood_above", "The same hill from above: trees fill blocks with straight edges, with open ground between", t("g2")))

    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>e118 Plants at Metres - Report</title>
<style>{CSS}</style>
</head>
<body>
<main>
<h1>e118: do plants at metres make woods and open ground, placed by the climate?</h1>
<p class="sub">Experiment report - 2026-11-14 - rung 2 of #135: 120 years of plants on the 16 km map of islands, terrain seed 23, one run read and one kept as a lesson</p>

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
</ol>

<h2>2. The world</h2>
<p>{t("world")}</p>
{diagram(f"{f(young, 'height'):.1f}", f"{f(old, 'height'):.1f}", f"{f(old, 'wood'):.0f}", f"{H_STEM * f(old, 'wood') ** 0.25:.1f}")}
<p><strong>Runs.</strong> {t("runs").replace("main is", "<code>main</code> is").replace("dense,", "<code>dense</code>,")}</p>
<ul class="measures">
  {measure("m1")}
  {measure("m2")}
  {measure("m3")}
  {measure("m4")}
  {measure("m5")}
</ul>

<h2>3. Results</h2>
{table([f"year {last}", "main", "dense"], summary)}
{table(["main: a tree for (years)", "trees", "median height, m", "median wood, kg", "a stem of that wood could stand, m"], age_rows)}
<ol class="verdicts">
<li><span class="verdict">Yes</span> {t("v1")}</li>
<li><span class="verdict no">No</span> {t("v2")}</li>
<li><span class="verdict">Yes</span> {t("v3")}</li>
<li><span class="verdict no">No</span> {t("v4")}</li>
<li><span class="verdict partly">Partly</span> {t("v5")}</li>
</ol>

<h3>3.1 The land is a thicket with young trees in it</h3>
<div class="grid2">
{"".join(c_land)}
</div>
<p>{t("r1")}</p>

<h3>3.2 Warmth and fire place the trees; water does not</h3>
<div class="grid2">
{"".join(c_place)}
</div>
<div class="grid2" style="margin-top:20px">
{"".join(c_class)}
</div>
<p>{t("r2")}</p>

<h3>3.3 A tree's wood grows and its height does not</h3>
<div class="grid2">
{"".join(c_height)}
</div>
<p>{t("r3")}</p>

<h3>3.4 The first long run: a narrow crown halves a new tree's light</h3>
<div class="grid2">
{"".join(c_dense)}
</div>
<p>{t("r4").replace("In dense", "In <code>dense</code>").replace("in main", "in <code>main</code>")}</p>

<h3>3.5 On the screen</h3>
{gallery}

<h2>4. Discussion</h2>
<p>{t("d1")}</p>
<p>{t("d2").replace("long,", "<code>long</code>,")}</p>
<p>{t("d3")}</p>

<h2>5. Conclusion and next step</h2>
<p>{t("conclusion")}</p>

<h2>Appendix: data</h2>
<p>The tables above are <code>results/main_reading.csv</code> and <code>results/dense_reading.csv</code>, written by
<code>read.py</code>; the charts are drawn from <code>results/*_log.csv</code>, <code>results/main_maps.bin</code> and the
trees' snapshots <code>results/main_trees_*.bin</code> with the same classes. The share of <code>dense</code>'s trees in
leaf is the README's (its snapshots are not kept here). The looks are the viewer's map page (<code>viewer map</code>),
whose panel is in Japanese. Build this report with <code>uv run python experiments/e118_plants/report.py</code>.</p>
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
