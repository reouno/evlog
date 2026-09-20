#!/usr/bin/env python3
"""Build report.html for e090 (#100 D + B + Fb', stage C: a mouthful of its own for the seed).

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
DRIFTS = ("d0", "d0.01", "d0.02", "d0.05", "d0.2")

DIAGRAM = """
<figure class="diagram">
<svg viewBox="0 0 720 280" role="img" aria-label="Grass sets seed, the wind carries it downwind onto thin ground or into the sea, and a beak opens it" style="max-width:100%;height:auto;display:block">
<defs><marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="currentColor"/></marker></defs>
<g fill="none" stroke="currentColor" stroke-width="1.2" font-size="12" font-family="system-ui, sans-serif">
  <rect x="16" y="112" width="110" height="44" rx="6"/>
  <text x="71" y="139" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">grass</text>
  <rect x="196" y="112" width="110" height="44" rx="6" stroke="var(--s1)" stroke-width="2"/>
  <text x="251" y="139" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">seed</text>
  <rect x="386" y="24" width="150" height="44" rx="6"/>
  <text x="461" y="51" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">thin ground: a bank</text>
  <rect x="386" y="112" width="150" height="44" rx="6"/>
  <text x="461" y="139" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">good ground: grass</text>
  <rect x="386" y="200" width="150" height="44" rx="6"/>
  <text x="461" y="227" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">the sea: litter</text>
  <rect x="596" y="24" width="108" height="44" rx="6"/>
  <text x="650" y="45" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">a beak</text>
  <text x="650" y="60" text-anchor="middle" fill="currentColor" stroke="none">all of it</text>
  <rect x="596" y="112" width="108" height="44" rx="6"/>
  <text x="650" y="133" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">a gut</text>
  <text x="650" y="148" text-anchor="middle" fill="currentColor" stroke="none">0.36 of it</text>
  <line x1="126" y1="134" x2="194" y2="134" marker-end="url(#arr)"/>
  <text x="160" y="126" text-anchor="middle" fill="currentColor" stroke="none">0.2</text>
  <line x1="306" y1="126" x2="384" y2="58" marker-end="url(#arr)"/>
  <line x1="306" y1="134" x2="384" y2="134" marker-end="url(#arr)"/>
  <line x1="306" y1="146" x2="384" y2="216" marker-end="url(#arr)"/>
  <text x="332" y="82" text-anchor="middle" fill="currentColor" stroke="none">the wind</text>
  <line x1="536" y1="46" x2="594" y2="46" marker-end="url(#arr)"/>
  <line x1="536" y1="134" x2="594" y2="134" marker-end="url(#arr)"/>
  <text x="565" y="126" text-anchor="middle" fill="currentColor" stroke="none">0.8 fiber</text>
  <text x="20" y="236" fill="currentColor" stroke="none">the wind: seed_drift of a cell's seed,</text>
  <text x="20" y="254" fill="currentColor" stroke="none">one cell downwind an update</text>
</g>
</svg>
<figcaption>Figure 1. The three laws as one cycle. Grass keeps a fifth of its growth as seed (e088); a share of the seed on a cell
moves one cell downwind every producers' update (D); seed that lands where it cannot sprout waits as a bank, seed that lands
on water sinks as the bottom's litter. A hard tip with any force behind it opens seed (B) and gets all of its matter, while
grass is 0.8 fiber, so a body taking a turn every step gets 0.36 of it (Fb').</figcaption>
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


def gallery(picks, caption):
    cards = []
    for r in picks:
        side, cells = int(r["side"]), r["cells"]
        px = 88 // max(side, 1)
        rects = "".join(
            f'<rect x="{(i % side) * px}" y="{(i // side) * px}" width="{px - 1}" height="{px - 1}" fill="{KIND_COLOR[int(k)]}"/>'
            for i, k in enumerate(cells[: side * side]) if k != "0")
        where = max((("land", float(r["land"])), ("surface", float(r["surface"])), ("bottom", float(r["bottom"]))), key=lambda x: x[1])
        cards.append(f"""<figure class="card"><svg viewBox="-1 -1 89 89" width="104" height="104" role="img" aria-label="{html.escape(r['kind'])}">
<rect x="-1" y="-1" width="89" height="89" fill="var(--grid)"/>{rects}</svg>
<figcaption><strong>{html.escape(r['kind'])}</strong><br>{r['run']}, {float(r['share']):.0%} of the grown bodies<br>
{int(float(r['born_size']))} blocks, mass {float(r['mass']):.0f}, pace {float(r['pace']):.2f}<br>
{where[1]:.0%} on the {where[0]}; plant: grass {float(r['grass']):.0%}, seed {float(r['seed']):.0%}; kills {float(r['kills']):.0%} of its food</figcaption></figure>""")
    return f"""<figure class="diagram"><div class="cards">{"".join(cards)}</div>
<figcaption>Figure 2. {html.escape(caption)}</figcaption></figure>"""


GALLERY_CAPTION = ("The six largest kinds of seed 9, each its commonest birth body (hard blue, muscle orange, gut aqua, "
                   "sensor yellow). The two land kinds carry a hard tip with muscle behind it: the beak that opens seed is "
                   "the tooth that opens bodies.")

# The prose of the page. Budgets (experiment-report skill): TL;DR 80 words, question 90, world 60, runs 60,
# a verdict 30, a results paragraph 70, discussion 200, conclusion 80; TEXT 1,000 in all.
TEXT = {
    "tldr": "No. Seed given a place of its own (the wind carries it), a tool of its own (a beak) and a worth of its own "
            "(grass is 0.8 fiber) still leads no kind. It reaches 4.5% of what the world eats and two fifths of the "
            "leading land kind's plant energy, and stops there. The drift that moves it off the lawn also sends a tenth "
            "of it into the sea, which never gives it back. P2's seed track ends here.",
    "question": "e089 put seed behind a tooth and no body lived on it: a gut takes a cell's grass and seed in one "
                "mouthful, and the tooth that opens seed opens bodies. #100 answers both: the wind moves seed away from "
                "the grass that set it, any hard tip opens it, and slow fiber makes grass a poor food for a fast body.",
    "world": "Today's default world with e088's seed at 0.2, plus three laws that go in together (Figure 1). Grass keeps "
             "setting seed; the wind moves it; a beak opens it; grass is 0.8 fiber, fermented at 0.005 a step.",
    "runs": "A check with the producers alone first, at five drift rates, to price the drift and pick one: 0.02, the "
            "largest rate that still passes stage B. Then D+B+Fb' on seeds 9-11, 100,000 steps, a census every 1,000 "
            "from 36,000, as the controls. 35 minutes a run on one core.",
    "v1": "Kinds at a census 7.16 / 6.76 / 7.25 against 7.45 / 8.27 / 7.25. Kinds kept to a place rise on two seeds "
          "and fall on one.", "v1w": "no",
    "v2": "No seed-led kind on any seed, though seed gives the largest toothed land kind 40-42% of its plant energy.",
    "v2w": "no",
    "v3": "No seed-led kind to compare. Grass eaters did not grow heavier either: 44-46 against the controls' 43-50.",
    "v3w": "partly",
    "v4": "The largest line holds 64% of the land on seed 9 (control 58%) and 78% on 11 (42%). Land bodies fall 9-16%.",
    "v4w": "no",
    "h1": "The wind cannot move the seed without emptying the land",
    "p1": "Seed is light enough to travel and the world is a third land, so what leaves the lawn largely leaves for the "
          "sea, where it sinks as the bottom's litter and stays. Nothing carries it back. At 0.05 the grass halves; at "
          "0.2 the wood dies out. Stage B's line falls between 0.02 and 0.05, and that ceiling, not the bodies, sets "
          "how far seed can go.",
    "h2": "What the drift buys is a bank the grazers eat",
    "p2": "At 0.02 a cell the grass does not hold carries twice the seed it did (0.16 against 0.08), and a fifth of the "
          "land holds more seed than grass. With bodies in the world that bank is 0.09-0.12 a cell against 0.37 without "
          "them: the crowd takes the new food as fast as the wind brings it, and the kinds do not rise.",
    "h3": "Seed is worth more and still leads nobody",
    "p3": "Read by energy, seed is two fifths of the leading toothed land kind's plant food, against a fifth of its "
          "plant matter in e089. The eater is the same body: a tooth of force 2 or more is carried by 26-40% of grown "
          "bodies anyway, so the beak separated nothing. A bigger share of one diet is not a second way of living.",
    "d1": "The three laws each did what they say. The seed moved, the beak opened it, and the fiber made grass poor: "
          "bodies digest 23% of the fiber they take in and grass fell to a fifth of what they eat. What did not happen "
          "is a body that lives on seed.",
    "d2": "The reason is where the seed ends up. It piles on thin ground, but thin ground is thin for the bodies too: "
          "little grass, little water, and the same crowd walking over it. A body that could hold such a place would "
          "need to reach it and stay; at a life of 500 steps and a few cells of travel it simply eats the seed that "
          "blows past the lawn it already lives on.",
    "d3": "It does not show that seed cannot part the kinds - only that a food a body meets mixed with its ordinary "
          "meal, taken with the tool it already carries, stays a share of a diet, however much it is worth. The drift "
          "also prices a general rule: a law that moves matter one way over a world with a sea drains the land.",
    "conclusion": "D, B and Fb' are not kept, and by #100's stopping rule P2's seed track ends: two of its three stage "
                  "C slots are spent and seed has not fed a kind at either. The next piece is chosen from vision.md's "
                  "gap table - a food separated by where a body must be to take it, or the bodies' own side (parts "
                  "whose worth depends on shape).",
}

PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>e090 The Seed's Own Mouthful - Report</title>
<style>{css}</style>
</head>
<body>
<main>
<h1>e090: does a seed with a place, a tool and a worth of its own feed a kind?</h1>
<p class="sub">Experiment report - 2026-09-20 - c1225, seeds 9-11, 100,000 steps, against e081's control ladder</p>

<section class="tldr">
<h2>TL;DR</h2>
<p>{tldr}</p>
</section>

<h2>1. Question</h2>
<p>{question}</p>
<ol>
  <li><strong>More ways of living.</strong> Kinds at a census +1 over each control.</li>
  <li><strong>The foods part the kinds.</strong> A seed-led and a grass-led kind each hold 5% of the grown bodies.</li>
  <li><strong>Size follows the food.</strong> Grass-led kinds 1.3 times heavier than seed-led.</li>
  <li><strong>No harm.</strong> The largest line no higher than the control.</li>
</ol>

<h2>2. The world</h2>
<p>{world}</p>
{diagram}
<p><strong>Runs.</strong> {runs}</p>
<ul class="measures">
  <li><strong>Kinds</strong> - ways of living by birth form (e068), at a census and kept to a place.</li>
  <li><strong>Led by</strong> - the food that gives a kind the most energy: matter less the fiber it cannot digest.</li>
  <li><strong>Mass, pace</strong> - medians over a kind's grown bodies; pace is turns a step.</li>
  <li><strong>Thin ground</strong> - a cell whose grass is under a tenth of the land's mean.</li>
  <li><strong>Largest line</strong> - its share of the land's bodies at a census.</li>
</ul>

<h2>3. Results</h2>
<div class="tw"><table>
<thead><tr><th>run</th><th>kinds</th><th>kept to a place</th><th>largest line</th><th>seed-led</th><th>grass-led mass</th><th>its pace</th><th>seed eaten</th><th>bodies</th></tr></thead>
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
<div class="grid2">
{c3}
</div>
<p>{p3}</p>
{gallery}

<h2>4. Discussion</h2>
<p>{d1}</p>
<p>{d2}</p>
<p>{d3}</p>

<h2>5. Conclusion and next step</h2>
<p>{conclusion}</p>

<h2>Appendix: data</h2>
<p>The full tables are in <code>results/sweep.csv</code>, <code>results/kinds.csv</code>, <code>results/bodies.csv</code> and
<code>results/alone.csv</code>. Build with <code>uv run python experiments/e090_drift/sweep.py</code> and
<code>alone.py</code>, then <code>report.py</code>.</p>
{tables}
</main>
</body>
</html>
"""


def main():
    sw = {r["run"]: r for r in rows("sweep.csv")}
    ks = rows("kinds.csv")
    bodies = rows("bodies.csv")
    al = {r["run"]: r for r in rows("alone.csv")}
    groups = [f"seed {s}" for s in SEEDS]
    ctrl = [sw[f"control {s}"] for s in SEEDS]
    run = [sw[f"D+B+Fb {s}"] for s in SEEDS]
    f = lambda rs, k: [float(r[k]) for r in rs]  # noqa: E731
    d = lambda k: [float(al[x][k]) for x in DRIFTS]  # noqa: E731
    labels = [x[1:] for x in DRIFTS]

    # 1. The stage B check: what the drift costs and what it buys.
    c0 = [bars("What the drift takes to the sea", "Share of all the seed the grass sets that lands on water and sinks. Drift 0 is e088's world, with no drift at all.",
               labels, [("seed sunk", d("sank_share"), 1)], pct=True),
          bars("What the land is left with", "Grass standing on a land cell, the mean over two years of producers alone. Flat would mean the drift costs the land nothing.",
               labels, [("grass a cell", d("grass"), 0)])]
    c1 = [bars("The bank on ground the grass does not hold", "Seed lying on a cell whose grass is under a tenth of the land's mean. Higher means more seed away from the grass that set it.",
               labels, [("seed a thin cell", d("seed_per_thin_cell"), 2)]),
          bars("Kinds at a census", "Ways of living holding 5% of the grown bodies, the mean over the censuses. Done-when: +1 on every seed.",
               groups, [("control", f(ctrl, "kinds_at"), 0), ("D+B+Fb'", f(run, "kinds_at"), 1)])]

    # 2. Stage C: what the bodies do with the seed.
    top_land = []
    for s_ in SEEDS:
        rs = [r for r in ks if r["run"] == f"D+B+Fb {s_}" and "/ tooth /" in r["kind"] and r["kind"].endswith("land")]
        top_land.append(max(rs, key=lambda r: float(r["share"])))
    c2 = [bars("Seed of what the world's bodies eat", "Share of all the matter bodies take in, over the second half of the run. The control has no seed; e089, behind a tooth of 2, had 3%.",
               groups, [("D+B+Fb'", f(run, "eat_seed"), 2)], pct=True),
          bars("The largest toothed land kind's plant energy", "Shares of the plant energy of the kind with a tooth that holds the most land bodies. Seed would have to pass grass to lead it.",
               groups, [("grass", f(top_land, "e_grass"), 0), ("seed", f(top_land, "e_seed"), 2)], pct=True)]
    c3 = [bars("The largest line's share of the land", "Over the censuses. Done-when: no higher than the control.",
               groups, [("control", f(ctrl, "top_share"), 0), ("D+B+Fb'", f(run, "top_share"), 1)], pct=True),
          bars("Bodies on land", "The mean over the second half of the run. The drift's thinner land holds fewer of them.",
               groups, [("control", f(ctrl, "pop_land"), 0), ("D+B+Fb'", f(run, "pop_land"), 1)])]

    held = [b for b in bodies if b["run"] == "D+B+Fb 9" and float(b["share"]) >= 0.05]
    gal = gallery(sorted(held, key=lambda b: -float(b["share"]))[:6], GALLERY_CAPTION)

    names = ["control 9", "control 10", "control 11", "D+B+Fb 9", "D+B+Fb 10", "D+B+Fb 11"]
    table = "".join(
        f"<tr><td>{n}</td><td>{float(sw[n]['kinds_at']):.2f}</td><td>{float(sw[n]['placed_at']):.2f}</td><td>{float(sw[n]['top_share']):.0%}</td>"
        f"<td>{float(sw[n]['seed_led']):.0%}</td><td>{float(sw[n]['mass_grass']):.0f}</td><td>{float(sw[n]['pace_grass']):.2f}</td>"
        f"<td>{float(sw[n]['eat_seed']):.0%}</td><td>{float(sw[n]['pop']):,.0f}</td></tr>" for n in names)
    ktbl = "".join(
        f"<tr><td>{r['run']}</td><td>{html.escape(r['kind'])}</td><td>{float(r['share']):.0%}</td><td>{r['lead']}</td><td>{float(r['mass']):.0f}</td>"
        f"<td>{float(r['pace']):.2f}</td><td>{float(r['e_grass']):.0%}</td><td>{float(r['e_seed']):.0%}</td><td>{float(r['kills']):.0%}</td></tr>"
        for r in ks if float(r["share"]) >= 0.03)
    atbl = "".join(
        f"<tr><td>{r['run'][1:]}</td><td>{float(r['grass']):.3f}</td><td>{float(r['seed']):.3f}</td><td>{float(r['sank_share']):.1%}</td>"
        f"<td>{float(r['share_grass']):.2f} / {float(r['share_wood']):.2f} / {float(r['share_algae']):.2f}</td>"
        f"<td>{float(r['burnt_a_year']):.1%}</td><td>{float(r['seed_on_thin']):.1%}</td><td>{float(r['seed_per_thin_cell']):.2f}</td></tr>"
        for r in rows("alone.csv"))
    tables = ("<details><summary>Kinds holding 3% or more of a run's grown bodies</summary><div class='tw'><table><thead><tr>"
              "<th>run</th><th>kind</th><th>share</th><th>led by</th><th>mass</th><th>pace</th><th>grass of its energy</th><th>seed of its energy</th><th>kills of food</th></tr></thead>"
              f"<tbody>{ktbl}</tbody></table></div></details>"
              "<details><summary>The stage B check: the producers alone at five drift rates</summary><div class='tw'><table><thead><tr>"
              "<th>drift</th><th>grass a cell</th><th>seed a cell</th><th>seed sunk</th><th>grass / wood / algae</th><th>fire a year</th>"
              "<th>seed on thin ground</th><th>seed a thin cell</th></tr></thead>"
              f"<tbody>{atbl}</tbody></table></div></details>")

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
