#!/usr/bin/env python3
"""Build report.html for e093 (#103, stage C: a block that eats the light).

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

DIAGRAM = """
<figure class="diagram">
<svg viewBox="0 0 720 300" role="img" aria-label="A leaf block takes matter from the soil of its cell by its faces open to the air and the light there, and pays for those faces in water, heat and broken blocks" style="max-width:100%;height:auto;display:block">
<defs><marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="currentColor"/></marker></defs>
<g fill="none" stroke="currentColor" stroke-width="1.2" font-size="12" font-family="system-ui, sans-serif">
  <rect x="16" y="18" width="190" height="48" rx="6"/>
  <text x="111" y="40" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">the sun</text>
  <text x="111" y="57" text-anchor="middle" fill="currentColor" stroke="none">0.25 of full over a day</text>
  <rect x="16" y="206" width="190" height="48" rx="6"/>
  <text x="111" y="228" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">the cell&apos;s soil</text>
  <text x="111" y="245" text-anchor="middle" fill="currentColor" stroke="none">12 a cell; the grass too</text>
  <rect x="270" y="102" width="200" height="72" rx="6" stroke="var(--s1)" stroke-width="2"/>
  <text x="370" y="126" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">a leaf block</text>
  <text x="370" y="143" text-anchor="middle" fill="currentColor" stroke="none">0.016 x faces x light</text>
  <text x="370" y="160" text-anchor="middle" fill="currentColor" stroke="none">upkeep 0.002 a step</text>
  <rect x="540" y="26" width="170" height="50" rx="6"/>
  <text x="625" y="48" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">it pays for a face</text>
  <text x="625" y="65" text-anchor="middle" fill="currentColor" stroke="none">water, heat, a tooth</text>
  <rect x="540" y="200" width="170" height="50" rx="6"/>
  <text x="625" y="222" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">a gut block it is not</text>
  <text x="625" y="239" text-anchor="middle" fill="currentColor" stroke="none">0.003-0.005 a step</text>
  <path d="M111,66 L111,128 L268,128" marker-end="url(#arr)"/>
  <text x="120" y="120" fill="currentColor" stroke="none">the light where it stands</text>
  <path d="M111,206 L111,150 L268,150" marker-end="url(#arr)"/>
  <text x="120" y="168" fill="currentColor" stroke="none">the matter it gains</text>
  <path d="M370,102 L370,51 L538,51" marker-end="url(#arr)"/>
  <text x="378" y="41" fill="currentColor" stroke="none">every face it opens</text>
  <path d="M370,174 L370,225 L538,225" marker-end="url(#arr)"/>
  <text x="378" y="215" fill="currentColor" stroke="none">the grid cell it takes</text>
  <text x="16" y="288" fill="currentColor" stroke="none">One block, one sub-cell, whatever its shape: spreading buys faces, not room.</text>
</g>
</svg>
<figcaption>Figure 1. The law as one cycle. A leaf block gains matter for each of its faces open to the air, times the light
on the cell it stands over, out of that cell&apos;s soil - the store the grass grows out of. It pays the block&apos;s upkeep, it
pays in water, heat and broken blocks for every face it opens, and it is a grid cell that is not a gut. The last line is
what the batch turned on: the room a body takes is its block count, not its outline.</figcaption>
</figure>
"""


def rows(name):
    with open(os.path.join(HERE, "results", name)) as f:
        return list(csv.DictReader(f))


def bars(title, subtitle, groups, series, pct=False):
    fig, ax = plt.subplots(figsize=(6.4, 2.6))
    n = len(series)
    width = 0.8 / n
    for i, (label, values, slot) in enumerate(series):
        xs = [x - 0.4 + width * (i + 0.5) for x in range(len(groups))]
        ax.bar(xs, values, width=width * 0.9, color=SERIES[slot], label=label)
    ax.set_xticks(range(len(groups)))
    ax.set_xticklabels(groups)
    ax.yaxis.set_major_formatter((lambda y, _p: f"{y:.0%}") if pct else kfmt)
    ax.yaxis.set_major_locator(MaxNLocator(4))
    legend_above(ax, n)
    return figure(title, subtitle, to_svg(fig))


def rate_chart(title, subtitle, rates, series, pct=False, ylabel="light_gain, a face in full light"):
    """The rate ladder: one point a run, the rate on a log axis with the control at the left."""
    fig, ax = plt.subplots(figsize=(6.4, 2.6))
    xs = range(len(rates))
    for label, values, slot in series:
        ax.plot(xs, values, color=SERIES[slot], linewidth=1.6, marker="o", markersize=4, label=label)
    ax.set_xticks(list(xs))
    ax.set_xticklabels(["off"] + [f"{r:g}" for r in rates[1:]], fontsize=8)
    ax.set_xlabel(ylabel, loc="right")
    ax.yaxis.set_major_formatter((lambda y, _p: f"{y:.0%}") if pct else kfmt)
    ax.yaxis.set_major_locator(MaxNLocator(4))
    legend_above(ax, len(series))
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


GALLERY_CAPTION = ("Seed 11's six largest kinds, each its commonest birth body (hard blue, muscle orange, gut aqua, "
                   "leaf lime). The light-led one is a hollow frame with its guts along one edge; every other kind "
                   "is a filled rectangle.")

# The prose of the page. Budgets (experiment-report skill): TL;DR 80 words, question 90, world 60, runs 60,
# a verdict 30, a results paragraph 70, discussion 200, conclusion 80; TEXT 1,000 in all.
TEXT = {
    "tldr": "Not kept. A block that gains matter through its faces open to the air makes a kind on three seeds of "
            "six, and gives this world its first bodies that are not rectangles - hollow frames and bars, 1.6 open "
            "faces a block against 0.94. But they all live in the water, and where they win the crowd is twice as "
            "thick, not thinner. The ways of living do not rise. A face is not room.",
    "question": "Ten laws in a row were absorbed by a crowd that denies half of all births, so the crowd was ranked "
                "the thing to break next. Light looked like the way: it falls on a body's outline, which only its "
                "genome sets, so a body living by it should need more room per unit of food. Every counterweight - "
                "water lost, heat lost, a face a tooth can break - was already in the world.",
    "world": "Today's default world with one block kind added (Figure 1). A leaf block is soft, weighs and costs what "
             "a muscle does, and each step takes 0.016 per face open to the air, times the light on its cell, out of "
             "that cell's soil. With the rate at 0 no body develops one and the world is the control's, bit for bit.",
    "runs": "A rate ladder first: eight rates on seed 9, 40,000 steps, to find where a leaf block is worth a grid "
            "cell at all. Then the rate it picked, 0.016, on seeds 9-14 for 100,000 steps, against the six-seed "
            "control ladder, a census every 1,000 steps from 36,000. Six runs at once on one core each, 1.5 hours.",
    "v1": "On three seeds of six, holding 15.5%, 14.1% and 5.9% of the grown bodies. On the other three no light-led "
          "kind reaches the 5% line, though 6-11% of their bodies are light-led one by one.", "v1w": "partly",
    "v2": "Their blocks have 1.38-1.62 faces open to the air, against 0.94-1.06 for the world's bodies and 0.94 in "
          "the control. The world's own packing barely moves.", "v2w": "",
    "v3": "Bodies a cell 1.05 against the control's 1.04, births with no room 46.9% against 46.8%. Where the "
          "light-led kinds stand it is 1.76-2.18 bodies a cell: they pack it tighter.", "v3w": "no",
    "v4": "Kinds at a census 7.02 against 7.53, kinds kept to a place 3.74 against 4.35. Both falls are inside the "
          "control ladder's own spread of 1.02 and 1.24.", "v4w": "no",
    "v5": "Every run stood 100,000 steps, the ledger drifts by 4.5e-14, the grass on a land cell is 0.185 against "
          "0.176, and the largest line's 62.6% sits inside a control spread of 35.5%.", "v5w": "",
    "h1": "The rate has no middle",
    "p1": "Under 0.008 a face earns less than the block's own upkeep and the leaf blocks that appear are mutations "
          "nobody keeps. One step up from 0.016 the light is the whole world: bodies of 11 blocks, two a cell, and "
          "the ways of living halve. Nothing in the law makes a face earn less as the crowd grows, so there is no "
          "rate at which it settles - only the one where it happens to match a gut.",
    "h2": "It parts kinds on half the seeds, and never on land",
    "p2": "Where a light-led kind exists it is a water kind: 97-99% of its bodies in one layer, surface or bottom, "
          "and it does not travel. On land an open face is a water bill - the dry air takes from every one of them "
          "each turn - so the counterweights bind, and they bind hard enough to push the whole way of living into "
          "the water, where a face costs nothing and gives breath back.",
    "h3": "The shape changes, and that is new",
    "p3": "These are the first bodies in this world whose grid is not a filled rectangle. The law rewards outline, "
          "and the genome answers with a hollow frame or a bar one block wide. It is the first kind parted by the "
          "shape a genome develops rather than by what the body holds - which is what P3 was for - and it costs "
          "nothing in the ledger or the world's size.",
    "h4": "The crowd does not thin",
    "p4": "This is the piece's own wrong-if. A spread body was meant to need more room, but a block claims one "
          "sub-cell whatever sits around it, so spreading buys faces and no room at all. The light-led kinds are "
          "small, they sit still, and their food does not need a cell of grass, so they stand twice as thick as "
          "the world does.",
    "d1": "The premise was wrong in a way the world could have told us: room in this world is counted in blocks, not "
          "in outline. Any law that pays per face will make thinner bodies and more of them. To thin a crowd a law "
          "has to make one body's income fall when another arrives, and nothing here does: the light on a cell is "
          "not shared, it is granted to each face that stands there.",
    "d2": "What did work is the other half of the piece. A material whose worth is set by the shape a genome "
          "develops parts kinds - where its counterweights leave it somewhere to live. That is P2's law from the "
          "other side: a food feeds a kind when what it takes to reach it is something a body is born with, and "
          "when the place where that thing pays is a place. Here the thing is the open face and the place is the "
          "water.",
    "d3": "It does not show what bodies shading each other would do. That was left out on purpose, and it is the one "
          "change that makes the light a flux a cell's bodies share instead of an income each draws.",
    "conclusion": "Not kept: a kind on three seeds of six, no rise in the ways of living, and a crowd that thickens "
                  "where the law wins. The rate stays out of the default world. What it leaves behind is a measured "
                  "reason the crowd is not broken this way, and the first shapes in this world that are not "
                  "rectangles. The next piece of P3 should make the light a flux the bodies on a cell share.",
}

PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>e093 A Block That Eats the Light - Report</title>
<style>{css}</style>
</head>
<body>
<main>
<h1>e093: does a part whose worth is set by shape make new kinds, and thin the crowd?</h1>
<p class="sub">Experiment report - 2026-09-20 - c1225, a rate ladder on seed 9 and six seeds at 100,000 steps, against e092's control ladder</p>

<section class="tldr">
<h2>TL;DR</h2>
<p>{tldr}</p>
</section>

<h2>1. Question</h2>
<p>{question}</p>
<ol>
  <li><strong>A kind of its own.</strong> A kind taking most of its matter from the light, at 5% of the grown bodies, on most seeds.</li>
  <li><strong>Shape.</strong> Its blocks measurably more open than the world's.</li>
  <li><strong>The crowd.</strong> Bodies a cell falls where they win, and births with no room fall with it.</li>
  <li><strong>Ways of living.</strong> Kinds at a census and kept to a place over the control's distribution.</li>
  <li><strong>No harm.</strong> The world stands, the ledger holds, the grass is not driven out.</li>
</ol>

<h2>2. The world</h2>
<p>{world}</p>
{diagram}
<p><strong>Runs.</strong> {runs}</p>
<ul class="measures">
  <li><strong>Kinds</strong> - ways of living by birth form (e068), at a census and kept to a place.</li>
  <li><strong>Led by the light</strong> - a kind whose grown bodies took half or more of their life's matter from it.</li>
  <li><strong>Open faces a block</strong> - faces of a body's soft blocks with no block of its own beside them, over its blocks.</li>
  <li><strong>Bodies a cell</strong> - bodies at a census over the world cells holding one.</li>
  <li><strong>No room</strong> - births that failed because nothing would fit.</li>
  <li><strong>Light's share</strong> - what leaf blocks took, over everything the world's bodies ate.</li>
</ul>

<h2>3. Results</h2>
<div class="tw"><table>
<thead><tr><th>run</th><th>kinds</th><th>kept to a place</th><th>light-led kinds</th><th>bodies in them</th><th>open faces a block</th><th>bodies a cell</th><th>no room</th><th>bodies</th></tr></thead>
<tbody>{table}</tbody></table></div>
<ol class="verdicts">
<li><span class="verdict {v1w}">{v1w_label}</span> {v1}</li>
<li><span class="verdict {v2w}">{v2w_label}</span> {v2}</li>
<li><span class="verdict {v3w}">{v3w_label}</span> {v3}</li>
<li><span class="verdict {v4w}">{v4w_label}</span> {v4}</li>
<li><span class="verdict {v5w}">{v5w_label}</span> {v5}</li>
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
{gallery}

<h3>3.4 {h4}</h3>
<div class="grid2">
{c3}
</div>
<p>{p4}</p>

<h2>4. Discussion</h2>
<p>{d1}</p>
<p>{d2}</p>
<p>{d3}</p>

<h2>5. Conclusion and next step</h2>
<p>{conclusion}</p>

<h2>Appendix: data</h2>
<p>The full tables are in <code>results/ladder.csv</code>, <code>results/batch.csv</code>, <code>results/kinds.csv</code>
and <code>results/bodies.csv</code>. Build with <code>uv run python experiments/e093_leaf/ladder.py</code> and
<code>sweep.py</code>, then <code>report.py</code>.</p>
{tables}
</main>
</body>
</html>
"""


def main():
    lad = rows("ladder.csv")
    bat = {(r["run"], r["seed"]): r for r in rows("batch.csv")}
    bods = rows("bodies.csv")
    groups = [f"seed {s}" for s in SEEDS]
    ctrl = [bat[("control", s)] for s in SEEDS]
    lit = [bat[("light", s)] for s in SEEDS]
    f = lambda rs, k: [float(r[k]) for r in rs]  # noqa: E731
    rates = [float(r["rate"]) for r in lad]

    # 3.1 the rate ladder
    c0 = [rate_chart("What the light is worth, by rate", "One run a point, seed 9 at 40,000 steps. Both would be flat at zero if leaf blocks never paid.",
                     rates, [("light's share of what is eaten", f(lad, "light_share"), 0),
                             ("grown bodies led by the light", f(lad, "leaf_led"), 2)], pct=True),
          rate_chart("What the rate does to the crowd", "Bodies a cell at the same runs. The control sits at 1.07; two a cell is a world of mats.",
                     rates, [("bodies a cell", f(lad, "per_cell"), 1)])]

    # 3.2 the kinds it makes
    c1 = [bars("Grown bodies in light-led kinds", "Kinds over the 5% line whose bodies took half their matter from the light. Zero means no kind lives by it.",
               groups, [("light 0.016", f(lit, "in_light"), 2)], pct=True),
          bars("Where the light-led kinds stand", "Share of their grown bodies in water, against every body of the run. A kind on land would sit near the orange bar.",
               groups, [("all the run's bodies", [1 - float(r["land_share"]) for r in lit], 1),
                        ("the light-led kinds", [float(r["water_led"]) for r in lit], 2)], pct=True)]

    # 3.3 the shape
    c2 = [bars("Open faces a block", "Faces of a body's soft blocks with nothing of its own beside them, over its blocks. A filled rectangle of 25 sits near 0.8.",
               groups, [("control", f(ctrl, "open_all"), 0), ("light, all bodies", f(lit, "open_all"), 1),
                        ("light, the light-led kinds", f(lit, "open_light"), 2)]),
          bars("Blocks a body is born with", "Median over the grown bodies. The light-led kinds are not bigger; they are differently arranged.",
               groups, [("control", f(ctrl, "born_med"), 0), ("light", f(lit, "born_med"), 1)])]

    # 3.4 the crowd
    c3 = [bars("Bodies a cell", "Bodies at a census over the cells holding one. The third bar counts only the cells the light-led kinds stand on.",
               groups, [("control", f(ctrl, "per_cell"), 0), ("light", f(lit, "per_cell"), 1),
                        ("where the light-led stand", f(lit, "per_cell_light"), 2)]),
          bars("The jam", "Births that found no room and moves that were blocked, over the second half of each run. This is what the piece was meant to move.",
               groups, [("control, no room", f(ctrl, "no_room"), 0), ("light, no room", f(lit, "no_room"), 1),
                        ("control, blocked", f(ctrl, "blocked"), 3), ("light, blocked", f(lit, "blocked"), 2)], pct=True)]

    gal = gallery(sorted([b for b in bods if b["seed"] == "11"], key=lambda b: -float(b["share"]))[:6], GALLERY_CAPTION)

    table = "".join(
        f"<tr><td>{name} {s}</td><td>{float(r['kinds_at']):.2f}</td><td>{float(r['placed_at']):.2f}</td>"
        f"<td>{int(float(r['by_light']))}</td><td>{float(r['in_light']):.1%}</td><td>{float(r['open_all']):.2f}</td>"
        f"<td>{float(r['per_cell']):.2f}</td><td>{float(r['no_room']):.1%}</td><td>{float(r['pop']):,.0f}</td></tr>"
        for name, rs in (("control", ctrl), ("light", lit)) for s, r in zip(SEEDS, rs))
    ltbl = "".join(
        f"<tr><td>{float(r['rate']):g}</td><td>{float(r['pop']):,.0f}</td><td>{float(r['size_mean']):.1f}</td>"
        f"<td>{float(r['leaf_mean']):.2f}</td><td>{float(r['light_share']):.1%}</td><td>{float(r['leaf_led']):.1%}</td>"
        f"<td>{float(r['per_cell']):.2f}</td><td>{float(r['blocked']):.1%}</td><td>{int(float(r['step'])):,}</td></tr>" for r in lad)
    btbl = "".join(
        f"<tr><td>{r['seed']}</td><td>{html.escape(r['kind'])}</td><td>{float(r['share']):.0%}</td>"
        f"<td>{int(float(r['born_size']))}</td><td>{float(r['open_block']):.2f}</td><td>{float(r['light']):.0%}</td>"
        f"<td>{float(r['plant']):.0%}</td><td>{float(r['kills']):.0%}</td><td>{float(r['water']):.0%}</td>"
        f"<td>{float(r['travel']):.1f}</td></tr>" for r in bods if float(r["share"]) >= 0.05)
    tables = ("<details><summary>The rate ladder, seed 9</summary><div class='tw'><table><thead><tr>"
              "<th>light_gain</th><th>bodies</th><th>blocks a body</th><th>leaf blocks</th><th>light's share</th>"
              "<th>bodies led by it</th><th>bodies a cell</th><th>moves blocked</th><th>steps</th></tr></thead>"
              f"<tbody>{ltbl}</tbody></table></div></details>"
              "<details><summary>Kinds holding 5% or more of a run's grown bodies, with the light on</summary>"
              "<div class='tw'><table><thead><tr><th>seed</th><th>kind</th><th>share</th><th>blocks</th>"
              "<th>open faces a block</th><th>light</th><th>plants</th><th>kills</th><th>in water</th><th>travel</th>"
              f"</tr></thead><tbody>{btbl}</tbody></table></div></details>")

    LABEL = {"": "Yes", "no": "No", "partly": "Partly"}
    labels_v = {f"v{i}w_label": LABEL[TEXT[f"v{i}w"]] for i in (1, 2, 3, 4, 5)}
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
