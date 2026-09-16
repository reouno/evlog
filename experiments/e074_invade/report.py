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

RESULTS = os.path.join(HERE, "results")
WORLDS = [("oA", "the grazer's world", 0), ("oB", "the browser's world", 1),
          ("mB", "no browsing form", 2), ("mA", "no land grass eater", 3)]
DONOR_BROWSE = 3.4  # % of all food eaten as browse in e073's kept runs, which the donor runs repeat
INJECT = 10000


def runs():
    with open(os.path.join(RESULTS, "invade.csv")) as f:
        return list(csv.DictReader(f))


def log_of(name):
    with open(os.path.join(RESULTS, "invade", name + "_log.csv")) as f:
        return list(csv.DictReader(f))


def series_of(rows, key):
    return [float(r[key]) for r in rows]


def browse_share(rows):
    return [100 * float(r["browse_intake"]) / max(float(r["plant_intake"]) + float(r["meat_intake"]), 1e-9) for r in rows]


def mean_by_world(logs, world, f, upto=None):
    """The mean over a world's runs of a per-step quantity (the runs share their steps)."""
    got = [f(rows if upto is None else [r for r in rows if int(r["step"]) <= upto]) for n, rows in logs.items() if f"_{world}_" in n]
    return [sum(v) / len(v) for v in zip(*got)]


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



def thin_chart(title, subtitle, xs, groups, ylabel):
    """groups: list of (label, [ys, ...], slot) - one thin line per run, one legend entry per group."""
    fig, ax = new_axes()
    for label, many, slot in groups:
        for i, ys in enumerate(many):
            ax.plot(xs, ys, color=SERIES[slot], linewidth=1.1, alpha=0.8, label=label if i == 0 else None)
    ax.set_ylabel(ylabel)
    ax.yaxis.set_major_formatter(kfmt)
    ax.yaxis.set_major_locator(MaxNLocator(4))
    legend_above(ax, len(groups))
    return figure(title, subtitle, to_svg(fig))


def bar_chart(title, subtitle, labels, groups, ylabel):
    """groups: list of (label, values, slot), one bar per label in each group."""
    fig, ax = plt.subplots(figsize=(6.4, 2.6))
    n = len(groups)
    width = 0.8 / n
    for i, (label, vals, slot) in enumerate(groups):
        xs = [j + (i - (n - 1) / 2) * width for j in range(len(labels))]
        ax.bar(xs, vals, width=width * 0.9, color=SERIES[slot], label=label)
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, fontsize=8.5)
    ax.set_ylabel(ylabel)
    ax.yaxis.set_major_formatter(kfmt)
    ax.yaxis.set_major_locator(MaxNLocator(4))
    legend_above(ax, n)
    return figure(title, subtitle, to_svg(fig))


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


# Hand-written mechanism diagram: what the test does, from a run's genomes to two followed lines.
DIAGRAM = """
<figure class="diagram">
<svg viewBox="0 0 760 215" role="img" aria-label="Genomes of a finished run seed a new world of one kind; two lines are injected into it and followed" style="max-width:100%;height:auto;display:block">
<defs><marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="currentColor"/></marker></defs>
<g fill="none" stroke="currentColor" stroke-width="1.2" font-size="12" font-family="system-ui, sans-serif">
  <rect x="8" y="58" width="150" height="62" rx="6"/>
  <text x="83" y="83" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">donor run</text>
  <text x="83" y="100" text-anchor="middle" fill="currentColor" stroke="none">e073's world, 100k steps</text>
  <line x1="158" y1="89" x2="196" y2="89" marker-end="url(#arr)"/>
  <text x="177" y="46" text-anchor="middle" fill="currentColor" stroke="none">2,500</text>
  <text x="177" y="60" text-anchor="middle" fill="currentColor" stroke="none">genomes</text>

  <rect x="198" y="58" width="172" height="62" rx="6"/>
  <text x="284" y="83" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">two kinds</text>
  <text x="284" y="100" text-anchor="middle" fill="currentColor" stroke="none">browser 26-36% wood</text>
  <text x="284" y="115" text-anchor="middle" fill="currentColor" stroke="none">grazer 0-3%, tooth 4-5%</text>
  <line x1="370" y1="89" x2="406" y2="89" marker-end="url(#arr)"/>
  <text x="388" y="46" text-anchor="middle" fill="currentColor" stroke="none">8,000</text>
  <text x="388" y="60" text-anchor="middle" fill="currentColor" stroke="none">seeded</text>

  <rect x="408" y="58" width="150" height="62" rx="6" stroke="var(--s1)" stroke-width="2"/>
  <text x="483" y="83" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">a world of one kind</text>
  <text x="483" y="100" text-anchor="middle" fill="currentColor" stroke="none">10,000 steps to settle</text>
  <line x1="558" y1="89" x2="606" y2="89" marker-end="url(#arr)"/>
  <text x="582" y="46" text-anchor="middle" fill="currentColor" stroke="none">100 + 100</text>
  <text x="582" y="60" text-anchor="middle" fill="currentColor" stroke="none">marked</text>

  <rect x="608" y="58" width="145" height="62" rx="6"/>
  <text x="680" y="83" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">30,000 steps</text>
  <text x="680" y="100" text-anchor="middle" fill="currentColor" stroke="none">invader vs control</text>

  <path d="M483,120 L483,160" stroke="var(--s1)" marker-end="url(#arr)"/>
  <text x="493" y="150" fill="var(--s1)" stroke="none">the way left out is back by step 2,000-4,000</text>
  <text x="493" y="168" fill="currentColor" stroke="none">(one body in twenty already carries the tooth)</text>
</g>
</svg>
<figcaption>Figure 1. The genomes of a finished run are written out and sorted into two kinds. A new world is
seeded with one kind alone and left to settle; then a hundred bodies of each kind go in, marked, and their
descendants are followed. The blue arrow is what the test did not expect: the world puts the missing way of
living back before the injection.</figcaption>
</figure>
"""


def main():
    rows = runs()
    logs = {r["run"]: log_of(r["run"]) for r in rows}
    early = [int(r["step"]) for r in logs[rows[0]["run"]] if int(r["step"]) <= INJECT]
    late = [int(r["step"]) for r in logs[rows[0]["run"]] if int(r["step"]) >= INJECT]
    f = lambda r, k: float(r[k])  # noqa: E731

    charts1 = [
        line_chart("The browse is eaten again by step 3,000",
                   "Share of all the food the bodies eat that comes from the crowns, before any injection. "
                   f"The flat line is e073's world ({DONOR_BROWSE}%). A line at zero would mean the way stayed out.",
                   early, [(name, mean_by_world(logs, w, browse_share, INJECT), slot) for w, name, slot in WORLDS]
                   + [("e073's world", [DONOR_BROWSE] * len(early), 4)]),
        line_chart("And one body in five carries a tooth",
                   "Share of the bodies with a tooth. The grazer's world starts at 4-5%, which is how many of "
                   "that kind's own bodies carry one; the browser's world starts above half and falls.",
                   early, [(name, mean_by_world(logs, w, lambda rs: series_of(rs, "tooth"), INJECT), slot)
                           for w, name, slot in WORLDS]),
    ]

    def lines_of(world, mark):
        """One line per run of that world: the bodies carrying `mark`, from the injection on."""
        out = []
        for name, rows_ in logs.items():
            if f"_{world}_" in name:
                out.append([float(r[f"inv{mark}"]) for r in rows_ if int(r["step"]) >= INJECT])
        return out

    charts2 = [
        thin_chart("In the grazer's world the browser's line grows and the grazer's dies",
                   "Six runs, each with both lines in it: a hundred bodies of each at step 10,000. "
                   "A line at zero has gone out.",
                   late, [("the browser (invader)", lines_of("oA", 2), 1), ("the grazer (control)", lines_of("oA", 1), 0)],
                   "bodies"),
        thin_chart("In the browser's world the two are harder to tell apart",
                   "The same six runs of the other world. The grazer invades on one seed of three; on the "
                   "others both lines wander or go out.",
                   late, [("the grazer (invader)", lines_of("oB", 1), 0), ("the browser (control)", lines_of("oB", 2), 1)],
                   "bodies"),
    ]

    means = []
    for w, name, _slot in WORLDS:
        rs = [r for r in rows if r["world"] == w]
        inv = "browser" if w in ("oA", "mB") else "grazer"
        ctl = "grazer" if inv == "browser" else "browser"
        means.append((name, sum(f(r, inv + "_end") for r in rs) / len(rs), sum(f(r, ctl + "_end") for r in rs) / len(rs)))
    charts3 = [
        bar_chart("The invader ends larger in all four worlds",
                  "Mean bodies of each line over the last 5,000 steps, six runs a world. Equal bars would mean "
                  "the injected kind is worth no more than the resident's own genomes.",
                  [m[0] for m in means],
                  [("the invader", [m[1] for m in means], 2), ("the resident's own genomes", [m[2] for m in means], 3)],
                  "bodies"),
        thin_chart("Every seeded world stands",
                   "Bodies alive, all 24 runs. e073's kept runs hold 7,806 on average; a run that fell to zero "
                   "would end the line.",
                   [int(r["step"]) for r in logs[rows[0]["run"]]],
                   [("a run", [series_of(rows_, "pop") for rows_ in logs.values()], 2)], "bodies"),
    ]

    table = ""
    for w, name, _slot in WORLDS:
        rs = [r for r in rows if r["world"] == w]
        inv = "browser" if w in ("oA", "mB") else "grazer"
        ctl = "grazer" if inv == "browser" else "browser"
        win = sum(f(r, inv + "_end") > f(r, ctl + "_end") for r in rs)
        loss = sum(f(r, inv + "_end") < f(r, ctl + "_end") for r in rs)
        table += (f"<tr><td>{name}</td><td>{inv}</td>"
                  f"<td>{100 * sum(f(r, 'browse_10k') for r in rs) / len(rs):.1f}%</td>"
                  f"<td>{100 * sum(f(r, 'woody_at_inject') for r in rs) / len(rs):.0f}%</td>"
                  f"<td>{sum(f(r, inv + '_end') for r in rs) / len(rs):.0f}</td>"
                  f"<td>{sum(f(r, ctl + '_end') for r in rs) / len(rs):.0f}</td>"
                  f"<td>{win} / {loss} / {6 - win - loss}</td>"
                  f"<td>{sum(f(r, 'kinds_at') for r in rs) / len(rs):.2f}</td>"
                  f"<td>{sum(f(r, 'pop_mean') for r in rs) / len(rs):.0f}</td></tr>")

    appendix = data_table(["seed", "draw", "browse_10k", "woody_at_inject", "grazer_end", "browser_end", "kinds_at", "pop_mean"],
                          {name: {k: [float(r[k]) for r in rows if r["world"] == w] for k in
                                  ("seed", "draw", "browse_10k", "woody_at_inject", "grazer_end", "browser_end", "kinds_at", "pop_mean")}
                           for w, name, _s in WORLDS}, every=1)

    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>e074 The invasion test - Report</title>
<style>{CSS}</style>
</head>
<body>
<main>
<h1>e074: can a world be held at one way of living?</h1>
<p class="sub">Experiment report - 2026-09-16 - 3 donor runs and 24 invasion runs on c1225, seeds 9-11</p>

<section class="tldr">
<h2>TL;DR</h2>
<p>No. Seed a world with the grazer alone and it browses again at the old rate by step 3,000; seed it with
the browser alone and half its land eats grass by step 10,000. The way that was left out comes back out of
the 4-5% of bodies that already carry the tooth for it. The injected line still ends larger than the
resident's own genomes injected beside it in all four worlds, and each kind does better rare in the other's
world than in its own. e073's two ways of living are a coexistence, not a lucky find. Next: a pair further
apart.</p>
</section>

<h2>1. Question</h2>
<p>Every run asks two questions at once: can the world hold two ways of living, and will evolution find
them. A negative answers neither. Ecology tests the first by mutual invasion: two ways coexist when each
grows from rare in a world the other holds. e073 gave the first pair worth the test - a land browser with a
tooth that takes a quarter of its food from the crowns, and a shore grazer without one.</p>
<ol>
  <li><strong>Mutual invasion.</strong> Each kind's injected line ends larger than the control line beside it, in both directions, on 2 seeds of 3.</li>
  <li><strong>The invader keeps its way.</strong> The browser's line still lives by wood at the end; the grazer's still does not.</li>
  <li><strong>The world stands.</strong> Matter conserved, bodies in all three media, the kinds of e073's world.</li>
  <li><strong>Reachability, measured.</strong> Whether the way left out comes back on its own, and how fast.</li>
</ol>

<h2>2. The test</h2>
<p>No law is added. A run writes out every body's genome at its last census; a new world is seeded from
those genomes instead of random ones, each body where its donor stood; and at a chosen step a hundred
bodies of two pools go in, marked, their descendants carrying the mark. Both lines enter the same world,
so the invader and its control meet the same crowd and the same luck.</p>
{DIAGRAM}
<p><strong>Runs.</strong> Three donor runs of e073's kept world (they reproduce its runs exactly), then 24
runs of 40,000 steps: four worlds - the grazer alone, the browser alone, and the community with each way
taken out form by form - times three seeds times two founder draws. Every 1,000 steps we record:</p>
<ul class="measures">
  <li><strong>Browse share</strong> - the food that comes from the crowns. e073's world: 3.4%.</li>
  <li><strong>Tooth</strong> - bodies that can bite wood at all.</li>
  <li><strong>The two lines</strong> - bodies of each mark, and what they eat.</li>
  <li><strong>Living by wood</strong> - unmarked bodies taking a fifth of their food from the crowns.</li>
  <li><strong>Kinds at a census</strong> - e068's count by birth form, stage C's measure.</li>
</ul>

<h2>3. Results</h2>
<div class="tw"><table>
<thead><tr><th>seeded world</th><th>invader</th><th>browse at 10k</th><th>living by wood at 10k</th>
<th>invader's line</th><th>control line</th><th>won / lost / both gone</th><th>kinds</th><th>bodies</th></tr></thead>
<tbody>{table}</tbody></table></div>
<ol class="verdicts">
<li><span class="verdict partly">Partly</span> <strong>Mutual invasion:</strong> the browser beats its control on 3 seeds of 3, the grazer on 1 of 3; the means favour the invader in all four worlds.</li>
<li><span class="verdict partly">Partly</span> <strong>Keeps its way:</strong> the grazer's lines stay grass eaters; the browser's keep tooth and wood on 2 seeds of 3.</li>
<li><span class="verdict">Yes</span> <strong>The world stands:</strong> 6,895-9,215 bodies, all three media, 6.74 kinds against the donor world's 6.61.</li>
<li><span class="verdict no">No</span> <strong>The world holds still:</strong> the way left out is back at e073's rate in 2,000-4,000 steps, in every world.</li>
</ol>

<h3>3.1 A world will not stay at one way of living</h3>
<div class="grid2">
{"".join(charts1)}
</div>
<p>Seven to thirteen lives, and nothing is invented on the way: the grazer kind carries a tooth in one
body of twenty. The test's premise - a resident world holding still while a rare invader is watched -
cannot be built here, because the world puts back whatever is taken out before the injection.</p>

<h3>3.2 The injected line still outgrows the resident's own genomes</h3>
<div class="grid2">
{"".join(charts2)}
</div>
<div class="grid2">
{"".join(charts3)}
</div>
<p>Read across the two one-kind worlds, the same genomes show what coexistence asks for: the browser's line
ends at 1,105 bodies when rare in the grazer's world and 567 in its own, the grazer's at 717 and 0. But a
line of a hundred in eight thousand is a lottery ticket - both lines are gone in 7 runs of 24, and two
founder draws of one world can end at 0 and 2,748.</p>

<h2>4. Discussion</h2>
<p>The question #72 was written for is answered, by the measurement it did not intend to make. For this pair
there is no gap between what the world holds and what evolution finds: either way of living re-forms from
the other's genomes in ten lives. e010's teeth - worth ten to one and found once in twelve million births -
have no counterpart here, because the browse needs no invention, only a tooth that one body in twenty
already has.</p>
<p>What survives of the invasion test is its paired form. The injecting is worth doing when the control goes
in beside it: the same world, the same step, the same weather. With that, the invader's line is the larger
one in all four worlds and in 12 runs of 24 against 5. Without it, a single injection would have read as a
result either way, since a rare line rides the world's own swings between 6,900 and 9,200 bodies.</p>
<p>It does not show that the two would coexist for a million steps, nor that a pair further apart - a
hunter and a grazer - behaves the same way. That is where the gap between ecology and evolution may
finally open.</p>

<h2>5. Conclusion and next step</h2>
<p>e073's browser and grazer are a coexistence the world rebuilds on its own, not a seed's luck. Stage C
should stop reading a seed's outcome as a reachability answer for close pairs, and should judge an invasion
by paired means over several founder draws. The next step is the pair the test was really built for: a
hunter and a grazer, where the way of living needs more than a tooth that is already there.</p>

<h2>Appendix: data</h2>
<p>Every run, by world. The full data is in <code>results/invade.csv</code> and the logs in
<code>results/invade/</code>; the pools and the censuses are rebuilt by
<code>pick.py</code> from the donor runs. Build this report with
<code>uv run python experiments/e074_invade/report.py</code>.</p>
{appendix}
</main>
</body>
</html>
"""
    out = os.path.join(HERE, "report.html")
    with open(out, "w") as fh:
        fh.write(page)
    print(f"wrote {out} ({os.path.getsize(out)//1024} KB)")


if __name__ == "__main__":
    main()
