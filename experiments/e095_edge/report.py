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

def pctfmt(ax):
    """A percent axis, with a decimal where whole percents would print the same tick twice."""
    lo, hi = ax.get_ylim()
    digits = 0 if hi - lo > 0.04 else 1
    return lambda y, _p: f"{y:.{digits}%}"


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




KIND_COLOR = {1: SERIES[0], 2: SERIES[1], 3: SERIES[3], 4: SERIES[2], 5: "#b5d33d", 6: "#a08ce0"}  # hard, muscle, sensor, gut, leaf, leg
SEEDS = ("9", "10", "11", "12", "13", "14")

DIAGRAM = """
<figure class="diagram">
<svg viewBox="0 0 720 330" role="img" aria-label="A spike concentrates the muscle behind its line for a break; a leg adds to the motor for each face it has open to the air; both pay for the faces they open" style="max-width:100%;height:auto;display:block">
<defs><marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="currentColor"/></marker></defs>
<g fill="none" stroke="currentColor" stroke-width="1.2" font-size="12" font-family="system-ui, sans-serif">
  <rect x="16" y="20" width="200" height="54" rx="6"/>
  <text x="116" y="42" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">the muscle on a line</text>
  <text x="116" y="59" text-anchor="middle" fill="currentColor" stroke="none">1-3 blocks of a body of 27</text>
  <rect x="270" y="20" width="200" height="54" rx="6" stroke="var(--s1)" stroke-width="2"/>
  <text x="370" y="42" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">a spike</text>
  <text x="370" y="59" text-anchor="middle" fill="currentColor" stroke="none">a hard tip, nothing beside it</text>
  <rect x="524" y="20" width="186" height="54" rx="6"/>
  <text x="617" y="42" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">the break</text>
  <text x="617" y="59" text-anchor="middle" fill="currentColor" stroke="none">harder face first, then force</text>
  <path d="M216,47 L268,47" marker-end="url(#arr)"/>
  <path d="M470,47 L522,47" marker-end="url(#arr)"/>
  <text x="478" y="36" fill="currentColor" stroke="none">x3</text>
  <text x="16" y="100" fill="currentColor" stroke="none">a soft face resists 1, one hard block 3, two 6:</text>
  <text x="16" y="116" fill="currentColor" stroke="none">the comparison decides, not the force</text>

  <rect x="16" y="150" width="200" height="54" rx="6"/>
  <text x="116" y="172" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">a leg block</text>
  <text x="116" y="189" text-anchor="middle" fill="currentColor" stroke="none">a muscle&apos;s mass and upkeep</text>
  <rect x="270" y="150" width="200" height="54" rx="6" stroke="var(--s1)" stroke-width="2"/>
  <text x="370" y="172" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">its faces open to the air</text>
  <text x="370" y="189" text-anchor="middle" fill="currentColor" stroke="none">1 each; walled in, none</text>
  <rect x="524" y="150" width="186" height="54" rx="6"/>
  <text x="617" y="172" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">the motor</text>
  <text x="617" y="189" text-anchor="middle" fill="currentColor" stroke="none">(muscle + legs) / mass, max 1</text>
  <path d="M216,177 L268,177" marker-end="url(#arr)"/>
  <path d="M470,177 L522,177" marker-end="url(#arr)"/>
  <rect x="270" y="242" width="200" height="54" rx="6"/>
  <text x="370" y="264" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">what a face costs</text>
  <text x="370" y="281" text-anchor="middle" fill="currentColor" stroke="none">water, heat, a tooth, room</text>
  <path d="M370,204 L370,240" marker-end="url(#arr)"/>
  <path d="M370,96 L370,148" marker-end="url(#arr)"/>
  <text x="390" y="126" fill="currentColor" stroke="none">both laws read the same edge</text>
  <text x="16" y="320" fill="currentColor" stroke="none">Neither block is new matter: the spike is the hard block in a shape, the leg trades a grid cell for speed.</text>
</g>
</svg>
<figcaption>Figure 1. The two laws as one piece. Both read a block&apos;s edge - the faces with nothing of the body beside them,
which only a genome sets. A spike counts the muscle behind its line three times over for a break; a leg adds to the
motor for each face it has open. Both pay for those faces in water, heat and blocks a tooth can reach, and the motor
is a chance per sub-cell, so it is worth nothing over 1.</figcaption>
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
    ax.yaxis.set_major_formatter(pctfmt(ax) if pct else kfmt)
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
    ax.yaxis.set_major_locator(MaxNLocator(4))
    ax.yaxis.set_major_formatter(pctfmt(ax) if pct else kfmt)
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
legs {float(r['leg_motor']):.0%} of its motor, travel {float(r['travel']):.0f} cells<br>
of its food: plants {float(r['plant']):.0%}, kills {float(r['kills']):.0%}</figcaption></figure>""")
    return f"""<figure class="diagram"><div class="cards">{"".join(cards)}</div>
<figcaption>Figure 2. {html.escape(caption)}</figcaption></figure>"""


GALLERY_CAPTION = ("Seed 13's three leg-built kinds (top) and its three largest (bottom), each its commonest birth "
                   "body: hard blue, muscle orange, gut aqua, leg violet. The leg-built ones are open frames and "
                   "bars with legs down a face; the largest are filled rectangles.")

# The prose of the page. Budgets (experiment-report skill): TL;DR 80 words, question 90, world 60, runs 60,
# a verdict 30, a results paragraph 70, discussion 200, conclusion 80; TEXT 1,000 in all.
TEXT = {
    "tldr": "Neither is kept. A spike multiplies the force behind a tip, and force is not what limits a break in "
            "this world, so from 0.5 to 8 it buys 1-2% of the flesh and no kind. A leg pays only where it touches "
            "the outside, and it builds bodies - open, roaming water plant eaters with legs down one face - that "
            "hold 3-5% of the grown bodies on half the seeds and never hold the line.",
    "question": "e093 put the first shape-material in this world: a block that gains by its open faces parted a "
                "kind, but only in the water, where a face is free. On land a body that sticks out pays in water, "
                "is easy meat, and is slow to place in a jam. So two laws were built together, each rewarding an "
                "edge in a different way - a spike to make sticking out dangerous, a leg to make it quick - to see "
                "whether they pay each other's bills.",
    "world": "Today's default world with two laws added (Figure 1). A spike is the hard block the world already "
             "has: at the front of its line with nothing beside it, it counts that line's muscle three times over "
             "for a break. A leg is a new block kind of a muscle's mass, adding to the motor for each face it has "
             "open to the air. At 0 the world is the control's, bit for bit.",
    "runs": "A ladder for each law first: six rates on seed 9, 40,000 steps. Then the pair at the rates they "
            "picked - spike 2, leg 1 - on seeds 9-14 for 100,000 steps against the six-seed control ladder, a "
            "census every 1,000 steps from 36,000. Six runs at once on one core each, 1.5 hours.",
    "v1": "No kind, on any seed, for either material. The best a kind takes through a spike is 13% of its flesh; "
          "the nearest leg kind holds 4.98% of the grown bodies.", "v1w": "no",
    "v2": "The five leg-built kinds carry 1.29 open faces a block against 0.90 for the other 63, and their legs "
          "sit on the boundary. The world's own packing does not move.", "v2w": "partly",
    "v3": "Kinds at a census 7.29 against 7.53 and kept to a place 4.03 against 4.35, both inside the control "
          "ladder's own spread of 1.02 and 1.24.", "v3w": "no",
    "v4": "Every run stood 100,000 steps, the ledger drifts by 3e-14, grass on a land cell 0.179 against 0.176, "
          "and the largest line holds 51.3% against the control's 54.9%.", "v4w": "",
    "h1": "The spike does not depend on its rate",
    "p1": "A force counted 1.5 times over and one counted 9 times over buy the same 1-2% of the flesh. What rises "
          "with the rate is the shape, not what it earns: spikes a grown body go 0.08 to 0.19. The break rule is "
          "why. It asks first that the pusher's face be harder than the victim's, and the prey here are soft, so "
          "a line's 1-3 muscle was already enough.",
    "h2": "The leg works, and the jam sets its top",
    "p2": "Up to rate 2 the motor and the travel rise together. At 4 the law turns over: legs replace muscle, the "
          "motor reaches 0.504 - and the travel falls below the control's while 62% of moves are blocked. The "
          "body it buys is too spread to place. Rate 1 keeps the most ways of living, which is why the pair ran "
          "there.",
    "h3": "It builds a body, not a way of living",
    "p3": "Legs go where the law pays: 1.76 blocks a body with 1.93 faces open. On three seeds of six that makes "
          "kinds whose motor is half legs, travelling 17 cells where the rest manage 4. They hold 3.0 to 4.98% of "
          "the grown bodies. A material can change what a body looks like without changing what it lives on - and "
          "kinds are counted by what a body lives on.",
    "h4": "And it lives in the water",
    "p4": "Nine in ten of those bodies stand in a water layer, and every one of the five kinds is a plant eater "
          "with no tooth that roams. This is the third law whose open bodies end there. On land a face loses water "
          "every turn; in the water it costs nothing and gives breath back. Until something pays for an open face "
          "on land, a shape law is a water law.",
    "d1": "The spike was designed as a cycle - what it takes, what refills it, what limits it - and it still had "
          "nothing to do, because the cycle was plugged into a mechanism whose arithmetic was never read. A break "
          "needs a harder face first; force was slack. Designing a law as a cycle is not enough: the term it "
          "multiplies has to be the term that binds.",
    "d2": "The leg is the second material whose worth is set by the shape a genome develops, and the second to "
          "build bodies that are not rectangles. Both times the bodies are real and the kinds are not. What parts "
          "a kind in this world is still a food, or a place a body must be born able to reach; how a body is "
          "built follows that, and does not lead it.",
    "d3": "Neither law was asked to thin the crowd - e093 settled that a law paying per unit of edge cannot - and "
          "neither did. What is not shown is what a spike would do in a world with armour worth having, which is "
          "a world this one has never been.",
    "conclusion": "Not kept. Both rates stay out of the default world. The leg leaves a measured body and a top "
                  "set by the jam; the spike leaves a rule about designing laws. P3 has one candidate left - "
                  "bodies that shade each other and the cell under them, which turns the light into a flux the "
                  "bodies on a cell share, and is the only law in sight that makes one body's income fall when "
                  "another arrives.",
}

PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>e095 The Spike and the Leg - Report</title>
<style>{css}</style>
</head>
<body>
<main>
<h1>e095: two materials that work only at a body&apos;s edge</h1>
<p class="sub">Experiment report - 2026-09-21 - c1225, two rate ladders on seed 9 and six seeds at 100,000 steps, against e092's control ladder</p>

<section class="tldr">
<h2>TL;DR</h2>
<p>{tldr}</p>
</section>

<h2>1. Question</h2>
<p>{question}</p>
<ol>
  <li><strong>A kind of its own, for each material.</strong> A kind taking most of its flesh through a spike, and a kind the legs move, each at 5% of the grown bodies on most seeds.</li>
  <li><strong>Shape.</strong> Those kinds measurably not rectangles, with their spikes and legs where the law pays.</li>
  <li><strong>Ways of living.</strong> Kinds at a census over the control's distribution.</li>
  <li><strong>No harm.</strong> The world stands, the ledger holds, the largest line no higher, the grass not driven out.</li>
</ol>

<h2>2. The world</h2>
<p>{world}</p>
{diagram}
<p><strong>Runs.</strong> {runs}</p>
<ul class="measures">
  <li><strong>Kinds</strong> - ways of living by birth form (e068), at a census and kept to a place.</li>
  <li><strong>Led by the spike</strong> - a kind whose grown bodies took half or more of their flesh through one.</li>
  <li><strong>The legs move it</strong> - half or more of a kind's motor from its legs, and twice the run's median travel.</li>
  <li><strong>Open faces a block</strong> - faces of a body's soft blocks with no block of its own beside them, over its blocks.</li>
  <li><strong>Spikes a body</strong> - hard blocks at the front of a line with nothing beside them, read off the birth grid.</li>
  <li><strong>The jam</strong> - births that found no room, and moves that were blocked.</li>
</ul>

<h2>3. Results</h2>
<div class="tw"><table>
<thead><tr><th>run</th><th>kinds</th><th>kept to a place</th><th>spike kinds</th><th>leg kinds</th><th>legs&apos; share of the motor</th><th>flesh through a spike</th><th>open faces a block</th><th>no room</th><th>bodies</th></tr></thead>
<tbody>{table}</tbody></table></div>
<ol class="verdicts">
<li><span class="verdict {v1w}">{v1w_label}</span> {v1}</li>
<li><span class="verdict {v2w}">{v2w_label}</span> {v2}</li>
<li><span class="verdict {v3w}">{v3w_label}</span> {v3}</li>
<li><span class="verdict {v4w}">{v4w_label}</span> {v4}</li>
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
and <code>results/bodies.csv</code>. Build with <code>uv run python experiments/e095_edge/ladder.py</code> and
<code>sweep.py</code>, then <code>report.py</code>.</p>
{tables}
</main>
</body>
</html>
"""


def main():
    lad = rows("ladder.csv")
    spike_lad = [r for r in lad if r["law"] == "spike"]
    leg_lad = [r for r in lad if r["law"] == "leg"]
    bat = {(r["run"], r["seed"]): r for r in rows("batch.csv")}
    bods = rows("bodies.csv")
    groups = [f"seed {s}" for s in SEEDS]
    ctrl = [bat[("control", s)] for s in SEEDS]
    edge = [bat[("edge", s)] for s in SEEDS]
    f = lambda rs, k: [float(r[k]) for r in rs]  # noqa: E731
    srates = [float(r["rate"]) for r in spike_lad]
    krates = [float(r["rate"]) for r in leg_lad]

    # 3.1 the spike's ladder
    c0 = [rate_chart("What a spike is worth, by rate", "One run a point, seed 9 at 40,000 steps. A law that bound would rise to the right.",
                     srates, [("flesh taken through a spike", f(spike_lad, "sharp_share"), 0),
                              ("blocks broken by a spike", f(spike_lad, "sharp_broke"), 2)], pct=True,
                     ylabel="spike, extra force behind a tip"),
          rate_chart("The shape, at the same runs", "Grown bodies carrying a spike. The rate buys the shape and not what it earns.",
                     srates, [("grown bodies with a spike", f(spike_lad, "spiked"), 1)], pct=True,
                     ylabel="spike, extra force behind a tip")]

    # 3.2 the leg's ladder and its top
    c1 = [rate_chart("What the legs buy, by rate", "Seed 9 at 40,000 steps. The motor is a chance of a step per sub-cell; the control sits at 0.209.",
                     krates, [("motor", f(leg_lad, "speed_mean"), 0)],
                     ylabel="leg, per face open to the air"),
          rate_chart("And what the jam takes back", "Travel in a grown life. Above rate 2 it falls below the control's 4.89 cells, with 62% of moves blocked.",
                     krates, [("travel in a life, cells", f(leg_lad, "travel_p50"), 1)],
                     ylabel="leg, per face open to the air")]

    # 3.3 what the batch built
    c2 = [bars("The legs' share of the motor", "Mean over the grown bodies of each run. Zero in every control run: no body has a leg block.",
               groups, [("the pair", f(edge, "leg_motor"), 1)], pct=True),
          bars("Open faces a block", "Faces of a body's soft blocks with nothing of its own beside them, over its blocks. A filled rectangle of 25 sits near 0.8.",
               groups, [("control", f(ctrl, "open_all"), 0), ("the pair, all bodies", f(edge, "open_all"), 1)])]

    # 3.4 the water, and the kinds that did not come
    c3 = [bars("Flesh taken through a spike", "Share of what the run's grown bodies took from kills that came in through a spike. Half would be a kind living by it.",
               groups, [("the pair", f(edge, "sharp_flesh"), 0)], pct=True),
          bars("Ways of living", "Kinds at a census and kinds kept to a place, per seed. The control ladder spreads 1.02 and 1.24 on its own.",
               groups, [("control, at a census", f(ctrl, "kinds_at"), 0), ("the pair, at a census", f(edge, "kinds_at"), 1),
                        ("control, kept to a place", f(ctrl, "placed_at"), 3), ("the pair, kept to a place", f(edge, "placed_at"), 2)])]

    # Seed 13's three leg-built kinds beside its three largest, so the reader can see both shapes.
    s13 = sorted([b for b in bods if b["seed"] == "13"], key=lambda b: -float(b["share"]))
    legged = [b for b in s13 if float(b["leg_motor"]) >= 0.4][:3]
    gal = gallery(legged + [b for b in s13 if b not in legged][:3], GALLERY_CAPTION)

    table = "".join(
        f"<tr><td>{name} {s}</td><td>{float(r['kinds_at']):.2f}</td><td>{float(r['placed_at']):.2f}</td>"
        f"<td>{int(float(r['by_spike']))}</td><td>{int(float(r['by_leg']))}</td><td>{float(r['leg_motor']):.1%}</td>"
        f"<td>{float(r['sharp_flesh']):.1%}</td><td>{float(r['open_all']):.2f}</td>"
        f"<td>{float(r['no_room']):.1%}</td><td>{float(r['pop']):,.0f}</td></tr>"
        for name, rs in (("control", ctrl), ("the pair", edge)) for s, r in zip(SEEDS, rs))
    ltbl = "".join(
        f"<tr><td>{r['law']}</td><td>{float(r['rate']):g}</td><td>{float(r['pop']):,.0f}</td>"
        f"<td>{float(r['sharp_share']):.1%}</td><td>{float(r['spiked']):.1%}</td><td>{float(r['leg_open']):.2f}</td>"
        f"<td>{float(r['leg_led']):.1%}</td><td>{float(r['speed_mean']):.3f}</td><td>{float(r['travel_p50']):.2f}</td>"
        f"<td>{float(r['blocked']):.1%}</td></tr>" for r in lad)
    btbl = "".join(
        f"<tr><td>{r['seed']}</td><td>{html.escape(r['kind'])}</td><td>{float(r['share']):.1%}</td>"
        f"<td>{int(float(r['born_size']))}</td><td>{float(r['open_block']):.2f}</td><td>{float(r['leg_motor']):.0%}</td>"
        f"<td>{float(r['sharp']):.0%}</td><td>{float(r['plant']):.0%}</td><td>{float(r['kills']):.0%}</td>"
        f"<td>{float(r['water']):.0%}</td><td>{float(r['travel']):.1f}</td></tr>"
        for r in sorted(bods, key=lambda b: -float(b["leg_motor"])) if float(r["share"]) >= 0.03)
    tables = ("<details><summary>The two rate ladders, seed 9</summary><div class='tw'><table><thead><tr>"
              "<th>law</th><th>rate</th><th>bodies</th><th>flesh through a spike</th><th>bodies with a spike</th>"
              "<th>leg faces</th><th>bodies the legs move</th><th>motor</th><th>travel</th><th>moves blocked</th>"
              f"</tr></thead><tbody>{ltbl}</tbody></table></div></details>"
              "<details><summary>Kinds holding 3% or more of a run's grown bodies, with the pair on</summary>"
              "<div class='tw'><table><thead><tr><th>seed</th><th>kind</th><th>share</th><th>blocks</th>"
              "<th>open faces a block</th><th>legs' share of the motor</th><th>flesh through a spike</th>"
              "<th>plants</th><th>kills</th><th>in water</th><th>travel</th>"
              f"</tr></thead><tbody>{btbl}</tbody></table></div></details>")

    LABEL = {"": "Yes", "no": "No", "partly": "Partly"}
    labels_v = {f"v{i}w_label": LABEL[TEXT[f"v{i}w"]] for i in (1, 2, 3, 4)}
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
