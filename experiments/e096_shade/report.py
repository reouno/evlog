#!/usr/bin/env python3
"""Build report.html for e096 (#108, stage C: the shade, a cell's light as one flux).

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


# ---------- data ----------

def load_csv(path):
    """Read a CSV of numbers into {column: [floats]}."""
    with open(os.path.join(HERE, path)) as f:
        rows = list(csv.DictReader(f))
    return {k: [float(r[k]) for r in rows] for k in rows[0]}


# ---------- chart helpers ----------

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
.fig { margin: 0; background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 14px 14px 8px; }
.fig svg { width: 100%; height: auto; display: block; font-family: system-ui, -apple-system, "Segoe UI", sans-serif; }
figcaption strong { display: block; font-size: 15px; }
figcaption span { display: block; color: var(--ink2); font-size: 13px; min-height: 2.6em; margin-bottom: 6px; }
.diagram { margin: 12px 0; background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 12px 16px 8px; color: var(--ink); }
.diagram figcaption { color: var(--ink2); font-size: 13px; margin-top: 4px; }
.cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); gap: 16px; }
.card { margin: 0; display: flex; gap: 12px; align-items: flex-start; }
.card figcaption { font-size: 12px; color: var(--ink2); }
.card figcaption strong { color: var(--ink); font-size: 12.5px; }
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




KIND_COLOR = {1: SERIES[0], 2: SERIES[1], 3: SERIES[3], 4: SERIES[2], 5: "#b5d33d"}  # hard, muscle, sensor, gut, leaf
SEEDS = ("9", "10", "11", "12", "13", "14")

RUNS = ["s0g0", "s1g0", "s2g0", "s1g0.016", "s2g0.008", "s4g0.004", "s2g0.016", "s4g0.016", "s1g0.032"]
LABEL = {"s0g0": "control", "s1g0": "shade 1\nalone", "s2g0": "shade 2\nalone", "s1g0.016": "shade 1\n0.016",
         "s2g0.008": "shade 2\n0.008", "s4g0.004": "shade 4\n0.004", "s2g0.016": "shade 2\n0.016",
         "s4g0.016": "shade 4\n0.016", "s1g0.032": "shade 1\n0.032"}
KEPT = RUNS[:6]   # the runs that stood their 40,000 steps
MATS = RUNS[6:]   # stopped once they had answered

DIAGRAM = """
<figure class="diagram">
<svg viewBox="0 0 720 268" role="img" aria-label="A cell's light is one flux: the blocks standing over the cell darken a share of it, the ground grows at what is left, and the blocks divide what they darkened" style="max-width:100%;height:auto;display:block">
<defs><marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="currentColor"/></marker></defs>
<g fill="none" stroke="currentColor" stroke-width="1.2" font-size="12" font-family="system-ui, sans-serif">
  <rect x="16" y="20" width="180" height="46" rx="6"/>
  <text x="106" y="41" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">the light on a cell</text>
  <text x="106" y="58" text-anchor="middle" fill="currentColor" stroke="none">one flux, every step</text>
  <rect x="266" y="14" width="210" height="76" rx="6" stroke="var(--s1)" stroke-width="2"/>
  <text x="371" y="38" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">n blocks stand over it</text>
  <text x="371" y="55" text-anchor="middle" fill="currentColor" stroke="none">they darken min(1, shade x n/16)</text>
  <text x="371" y="72" text-anchor="middle" fill="currentColor" stroke="none">a block reads min(shade, 16/n)</text>
  <rect x="546" y="14" width="160" height="50" rx="6"/>
  <text x="626" y="35" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">a leaf block</text>
  <text x="626" y="52" text-anchor="middle" fill="currentColor" stroke="none">gain x faces x its light</text>
  <rect x="266" y="150" width="210" height="50" rx="6"/>
  <text x="371" y="171" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">the grass under them</text>
  <text x="371" y="188" text-anchor="middle" fill="currentColor" stroke="none">grows at what is left</text>
  <rect x="546" y="150" width="160" height="50" rx="6"/>
  <text x="626" y="171" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">the gut blocks</text>
  <text x="626" y="188" text-anchor="middle" fill="currentColor" stroke="none">eat that grass</text>
  <line x1="196" y1="52" x2="264" y2="52" marker-end="url(#arr)"/>
  <line x1="476" y1="40" x2="544" y2="40" marker-end="url(#arr)"/>
  <path d="M371,90 L371,148" marker-end="url(#arr)"/>
  <text x="382" y="122" fill="currentColor" stroke="none">what they did not darken</text>
  <line x1="476" y1="175" x2="544" y2="175" marker-end="url(#arr)"/>
  <text x="16" y="232" fill="currentColor" stroke="none">A cell holds 16 sub-cells. Measured: the cells bodies stand on carry 8.5-10.5 blocks, in every run.</text>
  <text x="16" y="252" fill="currentColor" stroke="none">So min(shade, 16/n) never fell far: the second body did not halve the first&apos;s income.</text>
</g>
</svg>
<figcaption>Figure 1. The law as one cycle. The light of a cell stops being granted to everything standing in it. The blocks over
the cell darken a share of it and divide exactly that share among themselves; the ground grows at the rest, and the grass is
what the gut blocks eat. The two lines at the bottom are the result: the law&apos;s own term is the block count of a cell, and
that count is a constant of this world.</figcaption>
</figure>
"""


def rows(name):
    with open(os.path.join(HERE, "results", name)) as f:
        return list(csv.DictReader(f))


def bars(title, subtitle, groups, series, pct=False, rule=None):
    fig, ax = plt.subplots(figsize=(6.4, 2.8))
    n = len(series)
    width = 0.8 / n
    for i, (label, values, slot) in enumerate(series):
        xs = [x - 0.4 + width * (i + 0.5) for x in range(len(groups))]
        ax.bar(xs, values, width=width * 0.9, color=SERIES[slot], label=label)
    if rule is not None:
        ax.axhline(rule[0], color=INK, linewidth=1.0, linestyle="--")
        ax.text(len(groups) - 0.45, rule[0], rule[1], color=INK, fontsize=8, ha="right", va="bottom")
    ax.set_xticks(range(len(groups)))
    ax.set_xticklabels(groups, fontsize=8)
    ax.yaxis.set_major_formatter((lambda y, _p: f"{y:.0%}") if pct else kfmt)
    ax.yaxis.set_major_locator(MaxNLocator(4))
    legend_above(ax, n)
    return figure(title, subtitle, to_svg(fig))


def scatter(title, subtitle, points, xlabel, ylabel, band=None):
    """points: list of (label, xs, ys, slot)."""
    fig, ax = plt.subplots(figsize=(6.4, 2.8))
    if band:
        ax.axhspan(band[0], band[1], color=INK, alpha=0.15)
    for label, xs, ys, slot in points:
        ax.scatter(xs, ys, s=18, color=SERIES[slot], label=label)
    ax.set_xlabel(xlabel, loc="right")
    ax.set_ylabel(ylabel)
    ax.set_ylim(0, 16)
    ax.xaxis.set_major_formatter(kfmt)
    ax.yaxis.set_major_locator(MaxNLocator(4))
    legend_above(ax, len(points))
    return figure(title, subtitle, to_svg(fig))


def term_chart(title, subtitle, seen):
    """What a block's share of its cell's light does as the cell fills, at each `shade` of the ladder,
    with the band of block counts every run actually stood at."""
    fig, ax = plt.subplots(figsize=(6.4, 2.8))
    ns = [n / 4 for n in range(4, 129)]
    for i, sh in enumerate((1.0, 2.0, 4.0)):
        ax.plot(ns, [min(sh, 16 / n) / sh for n in ns], color=SERIES[i], linewidth=1.6, label=f"shade {sh:g}")
    ax.axvspan(seen[0], seen[1], color=INK, alpha=0.18)
    ax.text(seen[1] + 0.6, 0.86, "where the runs stood", color=INK, fontsize=8)
    ax.set_xlabel("blocks standing over the cell", loc="right")
    ax.yaxis.set_major_formatter(lambda y, _p: f"{y:.0%}")
    ax.yaxis.set_major_locator(MaxNLocator(4))
    legend_above(ax, 3)
    return figure(title, subtitle, to_svg(fig))


def gallery(picks, caption):
    cards = []
    for r in picks:
        side, cells = int(r["side"]), r["cells"]
        px = 88 // max(side, 1)
        rects = "".join(
            f'<rect x="{(i % side) * px}" y="{(i // side) * px}" width="{px - 1}" height="{px - 1}" fill="{KIND_COLOR[int(k)]}"/>'
            for i, k in enumerate(cells[: side * side]) if k != "0")
        cards.append(f"""<figure class="card"><svg viewBox="-1 -1 89 89" width="104" height="104" role="img" aria-label="{html.escape(r['kind'])}">
<rect x="-1" y="-1" width="89" height="89" fill="var(--grid)"/>{rects}</svg>
<figcaption><strong>{html.escape(r['kind'])}</strong><br>{float(r['share']):.0%} of the grown bodies, {int(float(r['born_size']))} blocks<br>
{float(r['open_block']):.2f} open faces a block, {float(r['water']):.0%} in water<br>
of its food: light {float(r['light']):.0%}, plants {float(r['plant']):.0%}, kills {float(r['kills']):.0%}</figcaption></figure>""")
    return f"""<figure class="diagram"><div class="cards">{"".join(cards)}</div>
<figcaption>Figure 2. {html.escape(caption)}</figcaption></figure>"""


GALLERY_CAPTION = ("The six largest kinds at shade 1, light_gain 0.016 (hard blue, muscle orange, gut aqua, leaf lime). "
                   "The light-led one is an open frame at the water's surface; the rest are the filled rectangles this "
                   "world always grows.")

# The prose of the page. Budgets (experiment-report skill): TL;DR 80 words, question 90, world 60, runs 60,
# a verdict 30, a results paragraph 70, discussion 200, conclusion 80; TEXT 1,000 in all.
TEXT = {
    "tldr": "Not kept, and the track stops here. Making a cell's light one flux does transfer it: the bodies take "
            "54-91% of the light where they stand, the grass under them falls by a third, and a kind lives by the "
            "light. The crowd does not move. The reason is a number nobody had measured: the cells bodies stand on "
            "carry 8.5-10.5 blocks in every run, so a law priced by density has nothing to bite on.",
    "question": "Half of all births in this world fail for want of room, and twelve laws in a row have been absorbed "
                "by that crowd. This was the only law in sight that makes one body's income fall when another "
                "arrives: the light of a cell, until now granted in full to everything standing in it, becomes one "
                "flux that the blocks over the cell share, leaving the ground what they did not take.",
    "world": "Today's default world with two laws, both off at zero. A leaf block (e093) gains matter through its "
             "faces open to the air. The shade makes the cell's light one flux: n blocks over a cell darken "
             "min(1, shade x n/16) of it, the grass and algae grow at the rest, and each block reads min(shade, 16/n) "
             "of the light of its own footprint.",
    "runs": "Nine runs on seed 9, 40,000 steps, one core each. Three hold the sparse income at e093's kept rate to "
            "read the sharing alone; two run the shade with no leaf, which is subtraction with nobody to take what "
            "was taken; three run rates that made a mat of e093's world. The control is this crate with both laws "
            "off, which reproduces the old control body for body.",
    "v1": "No. Births with no room 46.0-48.8% against the control's 50.3%, moves blocked 48.8-53.0% against 52.6%, "
          "bodies a cell 1.04-1.06 against 1.06 - and the shade with no leaf moves them just as far.", "v1w": "no",
    "v2": "Partly. A light-led kind holds 7.7% of the grown bodies at shade 1 and 5.6% at shade 2, on this seed. "
          "99% of those bodies live in the water, as in e093 and e095.", "v2w": "partly",
    "v3": "No. Kinds at a census 5.86-7.24 against the control's 8.14 on the same seed; kept to a place 3.48-4.00 "
          "against 4.95. No rung is above the control.", "v3w": "no",
    "v4": "Yes for the ledger and the world - it stands at every rung, matter closes to 5e-14, the step costs what it "
          "did - but the grass under the bodies falls by a quarter to a third.", "v4w": "partly",
    "h1": "The law engaged: the bodies take the light and the ground loses it",
    "p1": "This is the transfer the piece was built for, and it is large. Where bodies stand, more than half the "
          "light - nine tenths at shade 4 - now goes to them, and the grass standing there falls to two thirds of "
          "the grass on land they leave alone. The world eats a fifth less plant matter than the control does.",
    "h2": "And the income it was meant to move did not move",
    "p2": "A gut block takes 0.0034-0.0037 a step at every rung, against 0.0035 in the control. The world shrinks "
          "with its pasture - bodies and plant fall together, by a fifth - but each body eats what it always ate. "
          "That is e057's result from the other side: take food away and you buy number, not a way of living.",
    "h3": "The crowd is not a density, so the crowd did not feel it",
    "p3": "A cell holds 16 sub-cells. The cells bodies stand on hold 8.5-10.5 blocks in the control, in the shade "
          "runs and in the mats at four times the population: the world answers a lost income by standing on other "
          "cells, not thicker. Half of all births fail in cells that are half empty, so the jam is a packing "
          "problem, not a density.",
    "h4": "The law's own term had no room to fall",
    "p4": "A block's share of its cell's light is min(shade, 16/n). Over the band of block counts every run actually "
          "stood at, that term varies by about a fifth. The second body was supposed to halve the first's income; it "
          "took a fifth of it. The light-led kinds still stand 1.6-1.9 bodies a cell against the world's 1.05.",
    "d1": "The piece was designed around a per-cell density because a per-body rule looked too rare to fire: a cell "
          "holds 1.04 bodies. The measurement says both units were wrong. Blocks per cell is a constant of this "
          "world, near nine, whatever the population; bodies per cell moves only where the light-led crowd packs.",
    "d2": "What binds is placement: a body is a rigid grid that needs contiguous free sub-cells, and it fails to be "
          "born in a cell that is half empty. No law that prices mean density can reach that. It is also why e093's "
          "light had no middle - and why sharing the flux did not give it one: at a sparse income of 0.032 the world "
          "becomes the same mat of 11-block bodies, kinds down to 3.4-4.5.",
    "d3": "What the runs do not show: whether a wider ladder or six seeds would find a rung where the crowd moves. "
          "The track's stopping rule was declared before the runs - world and plant falling together with the income "
          "pinned - and it fired at every rung, so the batch was not run.",
    "conclusion": "P3 is spent. Its three steps each built bodies this world had never grown - hollow frames, bars, "
                  "legged swimmers, an open sunlit frame - and none of them built a way of living or thinned the "
                  "crowd. The next piece is not another single law but a set that replaces the world: 3D bodies, "
                  "with a food only a tall body reaches, so that the same cell is one environment to a large body "
                  "and another to a small one.",
}


PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>e096 the shade - Report</title>
<style>{css}</style>
</head>
<body>
<main>
<h1>e096: does sharing the light thin the crowd?</h1>
<p class="sub">Experiment report - 2026-09-21 - nine runs on seed 9, 40,000 steps, stage C's default world</p>

<section class="tldr">
<h2>TL;DR</h2>
<p>{tldr}</p>
</section>

<h2>1. Question</h2>
<p>{question}</p>
<ol>
  <li><strong>The crowd thins.</strong> Bodies a cell, births with no room and moves blocked all fall.</li>
  <li><strong>A kind of its own.</strong> A light-led kind holds 5% of the grown bodies, and where it stands is recorded.</li>
  <li><strong>Ways of living rise.</strong> Kinds at a census and kinds kept to a place go up.</li>
  <li><strong>No harm.</strong> The world stands, the ledger holds, the grass is not driven out from under the bodies.</li>
</ol>

<h2>2. The world</h2>
<p>{world}</p>
{diagram}
<p><strong>Runs.</strong> {runs}</p>
<ul class="measures">
  <li><strong>Of its light they take</strong> - the share of a cell's light the blocks over it darken, meaned over the cells that carry a body.</li>
  <li><strong>Blocks over such a cell</strong> - how many blocks stand on a cell that carries any. A cell holds 16 sub-cells.</li>
  <li><strong>Intake a gut block</strong> - the plant matter one gut block takes a step. This is what a law about the crowd must move.</li>
  <li><strong>No room</strong> - births that failed because nothing would fit; <strong>blocked</strong> - moves that hit something.</li>
  <li><strong>Kinds</strong> - ways of living by birth form (e068), at a census and kept to a place.</li>
  <li><strong>Led by the light</strong> - a kind whose grown bodies took half or more of their life's matter from it.</li>
</ul>

<h2>3. Results</h2>
<div class="tw"><table>
<thead><tr><th>run</th><th>of its light they take</th><th>blocks over such a cell</th><th>intake a gut block</th><th>no room</th><th>bodies a cell</th><th>kinds</th><th>light-led kinds</th><th>bodies</th></tr></thead>
<tbody>{table}</tbody></table></div>
<ol class="verdicts">
<li><span class="verdict {v1w}">{v1w_label}</span> <strong>The crowd thins:</strong> {v1}</li>
<li><span class="verdict {v2w}">{v2w_label}</span> <strong>A kind of its own:</strong> {v2}</li>
<li><span class="verdict {v3w}">{v3w_label}</span> <strong>Ways of living rise:</strong> {v3}</li>
<li><span class="verdict {v4w}">{v4w_label}</span> <strong>No harm:</strong> {v4}</li>
</ol>

<h3>3.1 {h1}</h3>
<div class="grid2">
{c0}
</div>
<p>{p1}</p>

<h3>3.2 {h2}</h3>
<div class="grid2">
{c1}
</div>
<p>{p2}</p>

<h3>3.3 {h3}</h3>
<div class="grid2">
{c2}
</div>
<p>{p3}</p>

<h3>3.4 {h4}</h3>
<div class="grid2">
{c3}
</div>
<p>{p4}</p>
{gallery}

<h2>4. Discussion</h2>
<p>{d1}</p>
<p>{d2}</p>
<p>{d3}</p>

<h2>5. Conclusion and next step</h2>
<p>{conclusion}</p>

<h2>Appendix: data</h2>
<p>The full tables are in <code>results/ladder.csv</code>, <code>results/ladder_kinds.csv</code> and
<code>results/bodies.csv</code>. Build with <code>uv run python experiments/e096_shade/ladder.py</code> and
<code>sweep.py --ladder</code>, then <code>report.py</code>.</p>
{tables}
</main>
</body>
</html>
"""


def main():
    lad = {r["run"].replace(" ", ""): r for r in rows("ladder.csv")}
    kin = {r["run"]: r for r in rows("ladder_kinds.csv")}
    bods = [b for b in rows("bodies.csv") if b["run"] == "s1g0.016"]
    f = lambda rs, k: [float(lad[r][k]) for r in rs]  # noqa: E731
    fk = lambda rs, k: [float(kin[r][k]) for r in rs]  # noqa: E731
    kept = [LABEL[r] for r in KEPT]
    every = [LABEL[r] for r in RUNS]
    ctl = lad["s0g0"]

    # 3.1 the law engaged
    c0 = [bars("The share of a cell's light the bodies take", "Meaned over the cells that carry a body. Zero is the old law, where the light was granted to everyone standing in it.",
               every, [("taken from the ground", f(RUNS, "shaded"), 1)], pct=True),
          bars("The grass standing, under the bodies and away from them", "Matter a land cell, over the second half of each run. Equal bars would mean the bodies cost the grass nothing.",
               every, [("where they stand", f(RUNS, "grass_under"), 2), ("where they do not", f(RUNS, "grass_free"), 0)])]

    # 3.2 the income
    c1 = [bars("What one gut block takes a step", "The crowd's own income. A law about who gets the flux would move this bar; a subtraction leaves it where it is.",
               every, [("intake a gut block", f(RUNS, "gut_income"), 1)],
               rule=(float(ctl["gut_income"]), "control")),
          bars("The world and its pasture, against the control", "Bodies and the plant matter the world eats a step, each as a share of the control's, over the six runs that stood their 40,000 steps. Falling together is e057's fingerprint.",
               kept, [("bodies", [x / float(ctl["pop"]) for x in f(KEPT, "pop")], 0),
                      ("plant eaten", [x / float(ctl["plant_step"]) for x in f(KEPT, "plant_step")], 2)], pct=True)]

    # 3.3 the crowd
    c2 = [bars("The jam", "Births that found no room and moves that were blocked. This is what the piece was meant to move; the dashed line is the control's no room.",
               every, [("no room", f(RUNS, "no_room"), 1), ("moves blocked", f(RUNS, "blocked"), 3)], pct=True,
               rule=(float(ctl["no_room"]), "control, no room")),
          scatter("Blocks over a cell that carries any", "One point a run, against its bodies. A cell holds 16 sub-cells. The band is 8.5-10.5, where every run sat.",
                  [("the runs that stood", f(KEPT, "pop"), f(KEPT, "blocks_cell"), 0),
                   ("the mats, stopped early", f(MATS, "pop"), f(MATS, "blocks_cell"), 1)],
                  "bodies in the world", "blocks a cell", band=(8.5, 10.5))]

    # 3.4 the term and the kinds
    c3 = [term_chart("What a block's share does as its cell fills", "min(shade, 16/n) over its value on an empty cell. The law's middle is the fall on the right of the band.",
                     (8.5, 10.5)),
          bars("Ways of living", "Kinds at a census and kinds kept to a place, read off each run's own censuses. The mats are read over fewer censuses.",
               every, [("kinds at a census", fk(RUNS, "kinds_at"), 0), ("kept to a place", fk(RUNS, "placed_at"), 2)])]

    gal = gallery(sorted(bods, key=lambda b: -float(b["share"]))[:6], GALLERY_CAPTION)

    table = "".join(
        f"<tr><td>{LABEL[r].replace(chr(10), ' ')}</td><td>{float(lad[r]['shaded']):.1%}</td>"
        f"<td>{float(lad[r]['blocks_cell']):.1f}</td><td>{float(lad[r]['gut_income']):.4f}</td>"
        f"<td>{float(lad[r]['no_room']):.1%}</td><td>{float(lad[r]['per_cell']):.2f}</td>"
        f"<td>{float(kin[r]['kinds_at']):.2f}</td><td>{int(float(kin[r]['by_light']))}</td>"
        f"<td>{float(lad[r]['pop']):,.0f}</td></tr>" for r in RUNS)
    ltbl = "".join(
        f"<tr><td>{LABEL[r].replace(chr(10), ' ')}</td><td>{float(lad[r]['pop']):,.0f}</td>"
        f"<td>{float(lad[r]['size_mean']):.1f}</td><td>{float(lad[r]['leaf_mean']):.2f}</td>"
        f"<td>{float(lad[r]['light_share']):.1%}</td><td>{float(lad[r]['leaf_led']):.1%}</td>"
        f"<td>{float(lad[r]['blocked']):.1%}</td><td>{float(lad[r]['grass']):,.0f}</td>"
        f"<td>{int(float(lad[r]['step'])):,}</td></tr>" for r in RUNS)
    ktbl = "".join(
        f"<tr><td>{LABEL[r].replace(chr(10), ' ')}</td><td>{float(kin[r]['kinds_at']):.2f}</td>"
        f"<td>{float(kin[r]['placed_at']):.2f}</td><td>{float(kin[r]['top_kind']):.1%}</td>"
        f"<td>{int(float(kin[r]['by_light']))}</td><td>{float(kin[r]['in_light']):.1%}</td>"
        f"<td>{float(kin[r]['water_led']):.0%}</td><td>{float(kin[r]['per_cell_light']):.2f}</td>"
        f"<td>{int(float(kin[r]['censuses']))}</td></tr>" for r in RUNS)
    tables = ("<details><summary>The ladder, read off the logs (seed 9)</summary><div class='tw'><table><thead><tr>"
              "<th>run</th><th>bodies</th><th>blocks a body</th><th>leaf blocks</th><th>light's share of intake</th>"
              "<th>bodies led by it</th><th>moves blocked</th><th>grass standing</th><th>steps</th></tr></thead>"
              f"<tbody>{ltbl}</tbody></table></div></details>"
              "<details><summary>The ways of living of each run, off its own censuses</summary><div class='tw'>"
              "<table><thead><tr><th>run</th><th>kinds at a census</th><th>kept to a place</th><th>largest kind</th>"
              "<th>light-led kinds</th><th>bodies in them</th><th>of those in water</th>"
              "<th>bodies a cell where they stand</th><th>censuses</th></tr></thead>"
              f"<tbody>{ktbl}</tbody></table></div></details>")

    VERDICT = {"": "Yes", "no": "No", "partly": "Partly"}
    labels_v = {f"v{i}w_label": VERDICT[TEXT[f"v{i}w"]] for i in (1, 2, 3, 4)}
    page = PAGE.format(css=CSS, diagram=DIAGRAM, c0="".join(c0), c1="".join(c1), c2="".join(c2), c3="".join(c3),
                       gallery=gal, table=table, tables=tables, **TEXT, **labels_v)
    import re
    words = len(re.sub(r"<[^>]+>", " ", page.split("<h2>Appendix")[0].split("</style>")[1]).split())
    out = os.path.join(HERE, "report.html")
    with open(out, "w") as fh:
        fh.write(page)
    print(f"wrote {out} ({os.path.getsize(out)//1024} KB, about {words} words before the appendix)")


if __name__ == "__main__":
    main()
