#!/usr/bin/env python3
"""Build report.html for e091 (#101, stage C: the crown as a place).

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


KIND_COLOR = {1: SERIES[0], 2: SERIES[1], 3: SERIES[3], 4: SERIES[2]}  # hard, muscle, sensor, gut (as the viewer)
SEEDS = ("9", "10", "11")

DIAGRAM = """
<figure class="diagram">
<svg viewBox="0 0 720 300" role="img" aria-label="A stand of wood drops half its yield into its crown as fruit and half to the floor as browse; a light body stands in the crown, a heavy one below" style="max-width:100%;height:auto;display:block">
<defs><marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="currentColor"/></marker></defs>
<g fill="none" stroke="currentColor" stroke-width="1.2" font-size="12" font-family="system-ui, sans-serif">
  <rect x="16" y="120" width="120" height="44" rx="6"/>
  <text x="76" y="141" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">a stand</text>
  <text x="76" y="156" text-anchor="middle" fill="currentColor" stroke="none">wood 3.0 a cell</text>
  <rect x="236" y="36" width="150" height="56" rx="6" stroke="var(--s1)" stroke-width="2"/>
  <text x="311" y="59" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">the crown</text>
  <text x="311" y="76" text-anchor="middle" fill="currentColor" stroke="none">fruit, soft</text>
  <rect x="236" y="192" width="150" height="56" rx="6"/>
  <text x="311" y="215" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">the floor</text>
  <text x="311" y="232" text-anchor="middle" fill="currentColor" stroke="none">browse, grass, carrion</text>
  <rect x="496" y="36" width="208" height="56" rx="6"/>
  <text x="600" y="59" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">a body of mass 30</text>
  <text x="600" y="76" text-anchor="middle" fill="currentColor" stroke="none">no tooth needed</text>
  <rect x="496" y="192" width="208" height="56" rx="6"/>
  <text x="600" y="215" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">a body of mass 75</text>
  <text x="600" y="232" text-anchor="middle" fill="currentColor" stroke="none">browse behind a tooth of 3</text>
  <line x1="136" y1="134" x2="234" y2="74" marker-end="url(#arr)"/>
  <line x1="136" y1="150" x2="234" y2="210" marker-end="url(#arr)"/>
  <text x="150" y="96" fill="currentColor" stroke="none">half the yield</text>
  <text x="150" y="196" fill="currentColor" stroke="none">half the yield</text>
  <line x1="386" y1="64" x2="494" y2="64" marker-end="url(#arr)"/>
  <line x1="386" y1="220" x2="494" y2="220" marker-end="url(#arr)"/>
  <line x1="600" y1="92" x2="600" y2="190" stroke-dasharray="4 4" marker-end="url(#arr)" marker-start="url(#arr)"/>
  <text x="588" y="136" text-anchor="end" fill="currentColor" stroke="none">mass over 10 x wood:</text>
  <text x="588" y="152" text-anchor="end" fill="currentColor" stroke="none">it comes down</text>
  <text x="20" y="278" fill="currentColor" stroke="none">the yield: 3e-5 of the standing wood a step, out of the cell's soil (e073). Uneaten fruit rots as browse does.</text>
</g>
</svg>
<figcaption>Figure 1. The three laws as one cycle. A land cell with wood 1 or more carries a crown, a place a body stands in,
holding nothing of the floor and reached by nothing on it (C1). Half of the cell's yield stays up there as fruit, soft
enough for any gut; half falls to the floor as today's browse, behind a tooth (C2). A body stands in the crown while its
mass is at most ten times the cell's wood, and comes down when it is not (C3).</figcaption>
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


def stacked_bars(title, subtitle, groups, layers, pct=True):
    fig, ax = plt.subplots(figsize=(6.4, 2.6))
    base = [0.0] * len(groups)
    for label, values, slot in layers:
        ax.bar(range(len(groups)), values, bottom=base, width=0.55, color=SERIES[slot], label=label)
        base = [b + v for b, v in zip(base, values)]
    ax.set_xticks(range(len(groups)))
    ax.set_xticklabels(groups)
    ax.yaxis.set_major_formatter((lambda y, _p: f"{y:.0%}") if pct else kfmt)
    ax.yaxis.set_major_locator(MaxNLocator(4))
    legend_above(ax, len(layers))
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
<figcaption><strong>{html.escape(r['kind'])}</strong><br>{float(r['share']):.0%} of the grown bodies, {float(r['crown']):.0%} of them in a crown<br>
{int(float(r['born_size']))} blocks, mass {float(r['mass']):.0f}, {float(r['travel']):.0f} cells from its birth<br>
plant: grass {float(r['grass']):.0%}, fruit {float(r['fruit']):.0%}; kills {float(r['kills']):.0%} of its food</figcaption></figure>""")
    return f"""<figure class="diagram"><div class="cards">{"".join(cards)}</div>
<figcaption>Figure 2. {html.escape(caption)}</figcaption></figure>"""


GALLERY_CAPTION = ("The six largest kinds of seed 9, each its commonest birth body (hard blue, muscle orange, gut aqua, "
                   "sensor yellow). Only the second one uses the crowns, and only a quarter of its bodies are up there "
                   "at any time; it is the same toothed roamer that eats the floor's browse.")

# The prose of the page. Budgets (experiment-report skill): TL;DR 80 words, question 90, world 60, runs 60,
# a verdict 30, a results paragraph 70, discussion 200, conclusion 80; TEXT 1,000 in all.
TEXT = {
    "tldr": "No. A crown over a stand of wood is a place bodies live in - 3-5% of the grown ones, on fruit no body "
            "below can reach - but no kind lives there. Bodies climb because damage or hunger has made them light, "
            "not because they were born light, so the crown sorts a stage of a life and nothing is inherited. Kinds "
            "fall. P2 ends here by its stopping rule.",
    "question": "Three stage C slots on a food parted by what is mixed into a mouthful fed no kind. What parts kinds "
                "in this world is where a body must be: three of the four media hold their own. So give the land a "
                "second place - the crown over a stand, with the yield that today falls to the floor, open only to a "
                "body light enough for a branch.",
    "world": "Today's default world with three laws that go in together (Figure 1): the crown is a layer of its own, "
             "half the stand's yield stays up in it as fruit, and a branch holds a body of at most ten times its "
             "cell's wood.",
    "runs": "Seeds 9-11, 100,000 steps, a census every 1,000 from 36,000, against e081's control ladder. A pilot on "
            "seed 9 first, to see whether anything stands in the crowns at all. 100 minutes a run, three at once on "
            "one core each. With the crown off the run reproduces the control column for column.",
    "v1": "Kinds at a census 6.84 / 6.59 / 7.29 against 7.45 / 8.27 / 7.26. Kinds kept to a place 3.02 / 2.80 / 3.33, "
          "all three under the line.", "v1w": "no",
    "v2": "No fruit-led kind on any seed. No birth form of 50 bodies or more stands 90% of them in a crown; the most "
          "crown-bound reach 68%.", "v2w": "no",
    "v3": "No fruit-led kind to compare. The places themselves sort by size: a crown's body weighs 36-37 against the "
          "floor's 47-50, the 1.3x asked for.", "v3w": "partly",
    "v4": "The world stands, the ledger holds at 4e-14, the largest line is no higher (55 / 62 / 43%). But the land's "
          "kinds halve, from 21-31% of the grown bodies to 11-16%.", "v4w": "partly",
    "h1": "The crowns are lived in, by bodies unlike the floor's",
    "p1": "About 300 bodies stand up there at any time. They are lighter, they fight more (70-81% carry a tooth that "
          "opens wood, against 41-47% below) and they end their lives 20-26 cells from where they were born against "
          "the floor's 4-7. Fruit is a third of what they eat and grass an eighth: the crown feeds them, and a hunter "
          "on the floor cannot touch them.",
    "h2": "But the door is damage, not birth",
    "p2": "A crown's body is born at mass 44-48 and weighs 36-37 when it is counted: it has lost nine blocks, where a "
          "floor body has lost none. They sit at 91% of the mass their branch holds. A ceiling on mass prices "
          "something that moves within a life - blocks broken, fat spent - so it sorts bodies by what has happened to "
          "them, and no form can be bound to the place.",
    "h3": "Kinds fall, and two thirds of the fall is the measure",
    "p3": "A kind keeps to a place when 90% of its bodies stand in one medium. A body that climbs and comes down "
          "breaks that for its whole form, so the land's forms are read as keeping to nothing. Counted again with the "
          "crown read as land, kinds kept to a place come back to 3.9-4.1 of the control's 4.5-4.8, and kinds at a "
          "census do not move: that fall is the world's.",
    "h4": "Splitting the yield did not add food",
    "p4": "The crowns drop the same 2.01 of the world's matter a step in both worlds. The control's bodies eat 78-84% "
          "of it off the floor; here they eat 70-76%, 0.6 up in the crowns and 0.9 below. The place is new, the meal "
          "is the same one divided, and the half behind the door feeds 3-5% of the bodies.",
    "d1": "The crown works as a place. It holds a crowd of its own, with its own food, its own hunters and no way up "
          "for the heavy - the first thing in this world that a body crosses far to use. What it cannot do is hold a "
          "line, because the key to the door is a number that moves while a body lives.",
    "d2": "That is the sentence three experiments have now written from different sides. A food feeds a new kind when "
          "what it takes to reach it is something a body is born with: browse needed a tooth and made a kind (e073), "
          "the water's layers need a density and hold theirs. Seed needed a mouthful nobody could separate, and a "
          "tool half the world already carried. The crown needs a mass that damage hands out.",
    "d3": "It does not show that a place cannot part kinds - only that this door cannot. The same three laws with the "
          "ceiling read on a body's birth mass, or on a part it is born with, would test it directly, and the crate "
          "is built. Nor does it price a crown worth more: the stands' whole yield is 2.6% of what the world eats, "
          "and no split of that is a living.",
    "conclusion": "Not kept. By #101's stopping rule P2 ends, three stage C slots spent. Two things it leaves: the "
                  "crown is the first place in this world whose bodies travel (20-26 cells against 4-7), and the "
                  "lesson above, which the next piece can use. The next piece is chosen from vision.md's gap table: "
                  "P3, parts whose worth depends on shape, or what is left of P1.",
}

PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>e091 The Crown as a Place - Report</title>
<style>{css}</style>
</head>
<body>
<main>
<h1>e091: does a food a body must climb to feed a kind of its own?</h1>
<p class="sub">Experiment report - 2026-09-20 - c1225, seeds 9-11, 100,000 steps, against e081's control ladder</p>

<section class="tldr">
<h2>TL;DR</h2>
<p>{tldr}</p>
</section>

<h2>1. Question</h2>
<p>{question}</p>
<ol>
  <li><strong>More ways of living.</strong> Kinds at a census +1 over each control.</li>
  <li><strong>The foods part the kinds.</strong> A fruit-led and a grass-led kind each hold 5% of the grown bodies.</li>
  <li><strong>Size follows the food.</strong> Grass-led kinds 1.3 times heavier than fruit-led.</li>
  <li><strong>No harm.</strong> The largest line no higher than the control, and the floor's kinds not lost.</li>
</ol>

<h2>2. The world</h2>
<p>{world}</p>
{diagram}
<p><strong>Runs.</strong> {runs}</p>
<ul class="measures">
  <li><strong>Kinds</strong> - ways of living by birth form (e068), at a census and kept to a place.</li>
  <li><strong>Led by</strong> - the plant food that gives a kind's grown bodies the most matter.</li>
  <li><strong>The crown</strong> - a fourth medium beside land, surface and bottom.</li>
  <li><strong>Blocks lost</strong> - a body's birth mass less its mass now, in mass units.</li>
  <li><strong>Travel</strong> - cells between where a body was born and where it stands.</li>
  <li><strong>Largest line</strong> - its share of the bodies standing on land, the crowns' among them.</li>
</ul>

<h2>3. Results</h2>
<div class="tw"><table>
<thead><tr><th>run</th><th>kinds</th><th>kept to a place</th><th>largest line</th><th>fruit-led</th><th>in crowns</th><th>fruit eaten</th><th>browse eaten</th><th>bodies</th></tr></thead>
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
<p>The full tables are in <code>results/sweep.csv</code>, <code>results/kinds.csv</code>, <code>results/bodies.csv</code>,
<code>results/places.csv</code>, <code>results/forms.csv</code> and <code>results/measure.csv</code>. Build with
<code>uv run python experiments/e091_crown/sweep.py</code> and <code>places.py</code>, then <code>report.py</code>.</p>
{tables}
</main>
</body>
</html>
"""


def main():
    sw = {r["run"]: r for r in rows("sweep.csv")}
    ks = rows("kinds.csv")
    bodies = rows("bodies.csv")
    pl = {(r["run"], r["place"]): r for r in rows("places.csv")}
    ms = rows("measure.csv")
    forms = rows("forms.csv")
    groups = [f"seed {s}" for s in SEEDS]
    ctrl = [sw[f"control {s}"] for s in SEEDS]
    run = [sw[f"crown {s}"] for s in SEEDS]
    f = lambda rs, k: [float(r[k]) for r in rs]  # noqa: E731
    crowned10 = sorted((float(r["in_crowns"]) for r in forms), reverse=True)[:10]
    place = lambda w, k: [float(pl[(f"crown {s}", w)][k]) for s in SEEDS]  # noqa: E731

    # 3.1 who lives in the crowns
    c0 = [bars("Bodies standing in a crown", "Share of the grown bodies at a census. Zero would mean the crowns are not worth living in.",
               groups, [("in a crown", place("crown", "share"), 2)], pct=True),
          bars("How far a body ends from its birth", "Median cells between birth and the census, by where the body stands. The world's bodies have not moved far since e049.",
               groups, [("on the floor", place("floor", "travel"), 0), ("in a crown", place("crown", "travel"), 2)])]

    # 3.2 the door
    c1 = [bars("What a body weighs, born and now", "Median mass, the mean over the three seeds. A crown holds ten times its cell's wood, 30-45 on the stands bodies stand in.",
               ["on the floor", "in a crown"],
               [("at birth", [sum(place(w, "born_mass")) / 3 for w in ("floor", "crown")], 0),
                ("at the census", [sum(place(w, "mass")) / 3 for w in ("floor", "crown")], 2)]),
          bars("The ten forms most in the crowns", "Of the birth forms with 50 grown bodies or more, all three seeds. A form keeps to a place at 90%; none of these reaches 70%.",
               [f"{i + 1}" for i in range(10)], [("in a crown", crowned10, 2)], pct=True)]

    # 3.3 the kinds, and the measure
    c2 = [bars("Kinds at a census", "Ways of living holding 5% of the grown bodies, the mean over the censuses. Done-when: +1 on every seed.",
               groups, [("control", f(ctrl, "kinds_at"), 0), ("crown", f(run, "kinds_at"), 1)]),
          bars("Kinds kept to a place", "The same kinds, counting those whose bodies keep 90% to one medium. The third bar reads the crown as land.",
               groups, [("control", [float(r["placed_control"]) for r in ms], 0), ("crown", [float(r["placed"]) for r in ms], 1),
                        ("crown as land", [float(r["placed_merged"]) for r in ms], 3)])]

    # 3.4 the yield
    yielded = [2.012, 2.004, 2.005]
    eaten_c = [1.610, 1.703, 1.580]
    c3 = [stacked_bars("The crowns' yield the bodies eat", "Shares of what the stands drop a step (2.01 of the world's matter in every run). The rest rots into the soil.",
                       ["control 9", "crown 9", "control 10", "crown 10", "control 11", "crown 11"],
                       [("browse, on the floor", [eaten_c[0] / yielded[0], 0.842 / yielded[0], eaten_c[1] / yielded[1], 0.876 / yielded[1], eaten_c[2] / yielded[2], 0.895 / yielded[2]], 0),
                        ("fruit, in the crowns", [0.0, 0.571 / yielded[0], 0.0, 0.592 / yielded[1], 0.0, 0.636 / yielded[2]], 2)]),
          stacked_bars("What a body eats, by where it stands", "Shares of a body's lifetime intake, the mean over the three seeds. What is missing of the 100% is carrion and the water's foods.",
                       ["on the floor", "in a crown"],
                       [(n, [sum(place(w, n)) / 3 for w in ("floor", "crown")], i)
                        for i, n in enumerate(("grass", "fruit", "browse", "kills"))])]

    held = [b for b in bodies if b["run"] == "crown 9" and float(b["share"]) >= 0.05]
    gal = gallery(sorted(held, key=lambda b: -float(b["share"]))[:6], GALLERY_CAPTION)

    names = ["control 9", "control 10", "control 11", "crown 9", "crown 10", "crown 11"]
    table = "".join(
        f"<tr><td>{n}</td><td>{float(sw[n]['kinds_at']):.2f}</td><td>{float(sw[n]['placed_at']):.2f}</td><td>{float(sw[n]['top_share']):.0%}</td>"
        f"<td>{float(sw[n]['fruit_led']):.0%}</td>" + ("<td>-</td><td>-</td>" if n.startswith("control") else
        f"<td>{float(sw[n]['in_crowns']):.1%}</td><td>{float(sw[n]['eat_fruit']):.1%}</td>") +
        f"<td>{float(sw[n]['eat_browse']):.1%}</td><td>{float(sw[n]['pop']):,.0f}</td></tr>" for n in names)
    ktbl = "".join(
        f"<tr><td>{r['run']}</td><td>{html.escape(r['kind'])}</td><td>{float(r['share']):.0%}</td><td>{r['lead']}</td><td>{float(r['mass']):.0f}</td>"
        f"<td>{float(r['crown']):.0%}</td><td>{float(r['grass']):.0%}</td><td>{float(r['fruit']):.0%}</td><td>{float(r['kills']):.0%}</td></tr>"
        for r in ks if float(r["share"]) >= 0.03)
    ptbl = "".join(
        f"<tr><td>{r['run']}</td><td>{r['place']}</td><td>{float(r['share']):.1%}</td><td>{float(r['born_mass']):.1f}</td><td>{float(r['mass']):.1f}</td>"
        f"<td>{float(r['lost']):.1f}</td><td>{float(r['travel']):.1f}</td><td>{float(r['age']):.0f}</td><td>{float(r['tooth']):.0%}</td>"
        f"<td>{float(r['wood']):.2f}</td></tr>" for r in rows("places.csv"))
    tables = ("<details><summary>Kinds holding 3% or more of a run's grown bodies</summary><div class='tw'><table><thead><tr>"
              "<th>run</th><th>kind</th><th>share</th><th>led by</th><th>mass</th><th>in a crown</th><th>grass of its plant</th><th>fruit of it</th><th>kills of food</th></tr></thead>"
              f"<tbody>{ktbl}</tbody></table></div></details>"
              "<details><summary>The grown bodies by where they stand</summary><div class='tw'><table><thead><tr>"
              "<th>run</th><th>place</th><th>share</th><th>born mass</th><th>mass now</th><th>lost</th><th>travel</th><th>age</th>"
              "<th>tooth of 3</th><th>wood on its cell</th></tr></thead>"
              f"<tbody>{ptbl}</tbody></table></div></details>")

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
