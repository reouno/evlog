#!/usr/bin/env python3
"""Build report.html for e094 (#106: why no way of living lasts).

Charts: matplotlib, exported as SVG and inlined. Diagram: hand-written SVG.
Run from the repo root: uv run python experiments/eNNN_name/report.py
"""
import csv
import html
import io
import os
import statistics as st
from collections import Counter

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






SEEDS = ("9", "10", "11", "12", "13", "14")
RUNS = [f"control {s}" for s in SEEDS] + [f"light {s}" for s in SEEDS]

DIAGRAM = """
<figure class="diagram">
<svg viewBox="0 0 720 260" role="img" aria-label="A way of living's share wanders across the five per cent line over sixty-five censuses, so an AND over all of them reports one" style="max-width:100%;height:auto;display:block">
<defs><marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="currentColor"/></marker></defs>
<g fill="none" stroke="currentColor" stroke-width="1.2" font-size="12" font-family="system-ui, sans-serif">
  <line x1="60" y1="190" x2="660" y2="190"/>
  <line x1="60" y1="40" x2="60" y2="190"/>
  <text x="52" y="44" text-anchor="end" fill="currentColor" stroke="none">share</text>
  <text x="360" y="212" text-anchor="middle" fill="currentColor" stroke="none">65 censuses, 64,000 steps, 5.4 years</text>
  <line x1="60" y1="130" x2="660" y2="130" stroke="var(--s1)" stroke-width="1.6" stroke-dasharray="6 4"/>
  <text x="668" y="134" text-anchor="end" fill="var(--s1)" stroke="none" font-size="11" transform="translate(0,-14)">the 5% line</text>
  <path d="M60,105 C100,70 130,150 165,120 C200,92 225,160 260,140 C295,122 320,95 355,112 C390,128 415,155 450,135 C485,116 510,80 545,100 C580,118 615,140 655,118" stroke-width="1.8"/>
  <rect x="215" y="126" width="60" height="30" rx="4" stroke="none" fill="var(--s1)" fill-opacity="0.13"/>
  <rect x="405" y="126" width="60" height="30" rx="4" stroke="none" fill="var(--s1)" fill-opacity="0.13"/>
  <text x="245" y="176" text-anchor="middle" fill="currentColor" stroke="none" font-size="11">dips</text>
  <text x="435" y="176" text-anchor="middle" fill="currentColor" stroke="none" font-size="11">dips</text>
  <text x="80" y="62" fill="currentColor" stroke="none">one way of living, its forms in the world the whole time</text>
  <text x="60" y="242" fill="currentColor" stroke="none">at a census: it counts 63 times out of 65. Held at EVERY census: it counts 0 times.</text>
</g>
</svg>
<figcaption>Figure 1. What the measure does. A way of living's share of the grown bodies swings by 61% of its own size
from census to census. Counting it at a census gives what the world holds; asking it to stand over 5% at every one of
65 censuses is an AND over 65 draws, and two dips are enough to fail it. Four fifths of the failures are a dip like
these, with the way&apos;s birth forms still in the world, and five sixths of them come back to the line later.</figcaption>
</figure>
"""


def rows(name):
    with open(os.path.join(HERE, "results", name)) as f:
        return list(csv.DictReader(f))


def bars(title, subtitle, groups, series, pct=False, rotate=False):
    fig, ax = plt.subplots(figsize=(6.4, 2.6))
    n = len(series)
    width = 0.8 / n
    for i, (label, values, slot) in enumerate(series):
        xs = [x - 0.4 + width * (i + 0.5) for x in range(len(groups))]
        ax.bar(xs, values, width=width * 0.9, color=SERIES[slot], label=label)
    ax.set_xticks(range(len(groups)))
    ax.set_xticklabels(groups, rotation=30 if rotate else 0, ha="right" if rotate else "center", fontsize=8 if rotate else 9)
    ax.yaxis.set_major_formatter((lambda y, _p: f"{y:.0%}") if pct else kfmt)
    ax.yaxis.set_major_locator(MaxNLocator(4))
    legend_above(ax, n)
    return figure(title, subtitle, to_svg(fig))


# The prose of the page. Budgets (experiment-report skill): TL;DR 80 words, question 90, world 60, runs 60,
# a verdict 30, a results paragraph 70, discussion 200, conclusion 80; TEXT 1,000 in all.
TEXT = {
    "tldr": "The ways of living do not turn over - the measure turns them off. A way's share of the grown bodies "
            "swings by 61% of its own size, so asking it to stand over 5% at every one of 65 censuses reports 1 for "
            "a world that holds 8 ways in the mean and loses none of them. Four fifths of the failures are a dip; "
            "five sixths come back. Stage C's pass line has to be re-read.",
    "question": "Stage C's pass line asks for four kinds holding 5% of the grown bodies for five years. The six-seed "
                "ladder reads 7.53 kinds at a census and 1 held at every census. Those two numbers say opposite "
                "things about the same world, and the second is the one the pass line is written against. Before "
                "spending another batch we wanted to know which it is: the ways turn over, they flicker, or there "
                "are too few bodies to read a 5% share.",
    "world": "Nothing was built and nothing was run. This reads the twelve censuses already on disk - the six-seed "
             "control ladder and e093's six - with e068's reading unchanged, so every number is comparable with "
             "every experiment since. A way's label never moves; what moves is how many bodies its birth forms have "
             "at a census (Figure 1).",
    "runs": "Twelve runs, the second half of each: 65 censuses every 1,000 steps from 36,000 to 100,000, which is "
            "5.4 years at a year of 11,880 steps and about 120 grown lifetimes. Ten minutes on one core. The "
            "censuses were restored from the archives to read and compressed again afterwards.",
    "v1": "751 stretches at the line end across the twelve runs. 609 of them - 81% - end with the way's forms still "
          "in the world and only their share under 5%.", "v1w": "",
    "v2": "632 of the 751 - 84% - stand over the line again later. Only 187 fall on a census where the largest "
          "lineage changed.", "v2w": "",
    "v3": "Resampling each census's grown bodies from its own composition gives 7.26 kinds at a census and 1.0 held, "
          "the same numbers. The swing is in the world, not in the sample.", "v3w": "no",
    "v4": "A way's share swings by 61% of its mean and the four quarters of the year explain a tenth of it. The "
          "flicker is drift, not the season.", "v4w": "no",
    "h1": "A way loses the line and comes back",
    "p1": "This is the whole finding in one picture: the shares wander, and the 5% line cuts through the middle of "
          "where they wander. Seventeen ways cross the line in a run, each in three or four stretches, each over it "
          "for 17 of the 65 censuses at the median - and not one of them over it in as many as 59. Nothing is being "
          "driven out; a number is crossing a threshold.",
    "h2": "It is not the sample and it is not the season",
    "p2": "Both alternatives are ruled out. A 5% share is read off 2,000-4,000 grown bodies, so the count is not "
          "short of bodies, and resampling reproduces it exactly. The year explains a tenth of the swing, which "
          "leaves drift in a finite population, or a cycle of the world's own - predator against prey. Nothing here "
          "separates those two.",
    "h3": "The line and the conjunction make the 1",
    "p3": "Every other way of asking the question gives a different answer about the same runs. The world holds 8 "
          "ways at 5% in the mean and 16 ever reach it. Held in 90% of the censuses instead of all of them: 3. At a "
          "3% line: 5. At a 10% line nothing is held at all. The 1 is a property of the conjunction, not of the "
          "world.",
    "d1": "This number has stood in every sweep since e068, beside the ones that decided, and it could not have "
          "moved: no law changes an AND over 65 draws of a wandering share. The number that does move with the world "
          "- kinds at a census - stayed at 7.3 through eleven rejected laws, and that reading stands. What we lose "
          "is the claim that stage C is far from its first pass line: on 90% of the censuses it scores 3 of the 4.",
    "d2": "The rest of the gap is untouched. The world holds about 8 ways of living against an ideal near 20, the "
          "largest line still holds 42-78% of the land's bodies, and nearly half of all births still fail for want "
          "of room. Those are the numbers to work on, and none of them is a measurement artefact.",
    "d3": "It does not show why a share swings by 61% of itself. Drift in a finite population and a predator-prey "
          "cycle would both look like this at one census every 1,000 steps, and telling them apart needs the "
          "lineages read against each other over time, not another law.",
    "conclusion": "Drop `kinds_held` from stage C's measures. Judge a piece on kinds at a census (7.26 today) and on "
                  "ways at 5% of the grown bodies in the mean (8.0 today); keep 'held' only as 'in 90% of the "
                  "censuses' (3.0). Re-read the pass line of #76 the same way. Then P3's remaining set - the spike "
                  "and the leg - is judged on numbers a law can actually move.",
}

PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>e094 Why No Way of Living Lasts - Report</title>
<style>{css}</style>
</head>
<body>
<main>
<h1>e094: is one way of living all this world keeps, or is that the measure?</h1>
<p class="sub">Experiment report - 2026-09-21 - no runs: twelve finished censuses, 65 each, read again</p>

<section class="tldr">
<h2>TL;DR</h2>
<p>{tldr}</p>
</section>

<h2>1. Question</h2>
<p>{question}</p>
<ol>
  <li><strong>They flicker, they are not driven out.</strong> A stretch at the line ends with its forms still in the world.</li>
  <li><strong>And they come back.</strong> The same way stands over the line again later.</li>
  <li><strong>It is the sample.</strong> Too few grown bodies to read a 5% share.</li>
  <li><strong>It is the season.</strong> The year moves the shares across the line.</li>
</ol>

<h2>2. What was read</h2>
<p>{world}</p>
{diagram}
<p><strong>Runs.</strong> {runs}</p>
<ul class="measures">
  <li><strong>A form</strong> - a lineage and the body its genes develop (e068).</li>
  <li><strong>A way of living</strong> - what a form's grown bodies do: diet, tooth, roaming, medium.</li>
  <li><strong>A kind</strong> - a way holding 5% of the grown bodies at a census.</li>
  <li><strong>A stretch</strong> - consecutive censuses in which one way holds the line.</li>
  <li><strong>The null</strong> - each census's bodies resampled from its own composition, 20 draws.</li>
  <li><strong>The season</strong> - the share of a way's swing lying between the year's quarters.</li>
</ul>

<h2>3. Results</h2>
<div class="tw"><table>
<thead><tr><th>run</th><th>kinds at a census</th><th>held at every census</th><th>ways at 5% in the mean</th><th>ways that ever reach it</th><th>stretch, median</th><th>stretch, p90</th><th>held in 90%</th><th>share swing</th></tr></thead>
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

<h2>4. Discussion</h2>
<p>{d1}</p>
<p>{d2}</p>
<p>{d3}</p>

<h2>5. Conclusion and next step</h2>
<p>{conclusion}</p>

<h2>Appendix: data</h2>
<p>The full tables are in <code>results/holds.csv</code> (a row a run), <code>results/spells.csv</code> (a row a
stretch), <code>results/events.csv</code> (a row an end) and <code>results/census.csv</code>. Build with
<code>uv run python experiments/e094_hold/hold.py</code>, then <code>report.py</code>.</p>
{tables}
</main>
</body>
</html>
"""


def main():
    hold = {r["run"]: r for r in rows("holds.csv")}
    spells = rows("spells.csv")
    events = rows("events.csv")
    shares = [r for r in rows("shares.csv") if r["run"] == "control 9"]
    f = lambda k: [float(hold[r][k]) for r in RUNS]  # noqa: E731
    groups = [r.replace("control ", "c").replace("light ", "l") for r in RUNS]

    # 3.1 the flicker itself
    ways = sorted({r["way"] for r in shares},
                  key=lambda w: -sum(float(r["share"]) for r in shares if r["way"] == w))[:4]
    steps = sorted({int(r["step"]) for r in shares})
    byway = {w: [next((float(r["share"]) for r in shares if r["way"] == w and int(r["step"]) == s), 0.0)
                 for s in steps] for w in ways}
    fig, ax = new_axes()
    for i, w in enumerate(ways):
        ax.plot(steps, byway[w], color=SERIES[i], linewidth=1.4, label=w.replace(" / no tooth", "").replace(" / ", " "))
    ax.axhline(0.05, color="#898781", linewidth=1.2, linestyle="--")
    ax.yaxis.set_major_formatter(lambda y, _p: f"{y:.0%}")
    ax.yaxis.set_major_locator(MaxNLocator(4))
    legend_above(ax, 2)
    c0 = [figure("The four largest ways of seed 9, census by census",
                 "Share of the grown bodies; the dashes are the 5% line. A flat line over the dashes would be a kind that holds.",
                 to_svg(fig)),
          hist_chart("How long a way holds the line", "Stretches of consecutive censuses, all twelve runs. A run is 65 censuses, so 65 would be a kind that never dips.",
                     [("stretches", [float(s["censuses"]) for s in spells], 1)], bins=range(1, 30), xlabel="censuses in a row")]

    # 3.2 the null and the season
    c1 = [bars("Kinds at a census, real and resampled", "The null draws each census's bodies again from its own composition, 20 times. Equal bars mean the count is not short of bodies.",
               groups, [("as measured", f("kinds_at"), 0), ("resampled", f("null_at"), 1)], rotate=True),
          bars("What the year explains of a way's swing", "Between-quarter share of the variance of a way's share. 1 would mean the swing is the season and nothing else.",
               groups, [("the year", f("season"), 2)], pct=True, rotate=True)]

    # 3.3 the line and the conjunction
    c2 = [bars("The same runs, counted four ways", "Medians over the twelve runs. Only the last bar is an AND over all 65 censuses.",
               ["at a census", "at 5% in the mean", "held in 90%", "held in every"],
               [("kinds", [st.median(f("kinds_at")), st.median(f("ways_mean5")),
                           st.median(f("almost_0.05")), st.median(f("kinds_held"))], 0)]),
          bars("And at three lines", "The same twelve runs at a 3%, 5% and 10% share. The line moves the count as much as any law has.",
               ["3%", "5%", "10%"],
               [("at a census", [st.median(f("at_0.03")), st.median(f("kinds_at")), st.median(f("at_0.1"))], 0),
                ("held in 90%", [st.median(f("almost_0.03")), st.median(f("almost_0.05")), st.median(f("almost_0.1"))], 2),
                ("held in every", [st.median(f("held_0.03")), st.median(f("kinds_held")), st.median(f("held_0.1"))], 1)])]

    table = "".join(
        f"<tr><td>{r}</td><td>{float(hold[r]['kinds_at']):.2f}</td><td>{int(float(hold[r]['kinds_held']))}</td>"
        f"<td>{int(float(hold[r]['ways_mean5']))}</td><td>{int(float(hold[r]['ways_seen']))}</td>"
        f"<td>{float(hold[r]['spell_med']):.0f}</td><td>{float(hold[r]['spell_p90']):.0f}</td>"
        f"<td>{float(hold[r]['almost_0.05']):.0f}</td><td>{float(hold[r]['share_cv']):.2f}</td></tr>" for r in RUNS)
    why = Counter(e["why"] for e in events)
    etbl = "".join(
        f"<tr><td>{k}</td><td>{v}</td><td>{v / len(events):.0%}</td>"
        f"<td>{sum(e['comes_back'] == '1' for e in events if e['why'] == k)}</td>"
        f"<td>{sum(e['top_changed'] == '1' for e in events if e['why'] == k)}</td></tr>" for k, v in why.items())
    stbl = "".join(
        f"<tr><td>{n}</td><td>{sum(1 for s in spells if int(s['censuses']) == n)}</td></tr>"
        for n in sorted({int(s["censuses"]) for s in spells})[:15])
    tables = ("<details><summary>What ended a stretch, all twelve runs</summary><div class='tw'><table><thead><tr>"
              "<th>why</th><th>ends</th><th>share</th><th>comes back later</th><th>on a change of the largest lineage</th>"
              f"</tr></thead><tbody>{etbl}</tbody></table></div></details>"
              "<details><summary>How many stretches of each length</summary><div class='tw'><table><thead><tr>"
              f"<th>censuses in a row</th><th>stretches</th></tr></thead><tbody>{stbl}</tbody></table></div></details>")

    LABEL = {"": "Yes", "no": "No", "partly": "Partly"}
    labels_v = {f"v{i}w_label": LABEL[TEXT[f"v{i}w"]] for i in (1, 2, 3, 4)}
    page = PAGE.format(css=CSS, diagram=DIAGRAM, c0="".join(c0), c1="".join(c1), c2="".join(c2),
                       table=table, tables=tables, **TEXT, **labels_v)
    import re
    words = len(re.sub(r"<[^>]+>", " ", page.split("<h2>Appendix")[0].split("</style>")[1]).split())
    out = os.path.join(HERE, "report.html")
    with open(out, "w") as fh:
        fh.write(page)
    print(f"wrote {out} ({os.path.getsize(out)//1024} KB, about {words} words before the appendix)")


if __name__ == "__main__":
    main()
