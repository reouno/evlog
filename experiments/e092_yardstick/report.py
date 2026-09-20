#!/usr/bin/env python3
"""Build report.html for e092 (#102, the yardstick: the control ladder at six seeds).

Charts: matplotlib, exported as SVG and inlined. Diagram: hand-written SVG.
Run from the repo root: uv run python experiments/e092_yardstick/report.py
"""
import csv
import html
import io
import os
import re
import statistics as st

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

def rows_of(path):
    with open(os.path.join(HERE, path)) as f:
        return list(csv.DictReader(f))


def num(rows, key):
    return [float(r[key]) for r in rows]


# ---------- chart helpers ----------

def kfmt(x, _pos):
    return f"{x/1000:g}k" if abs(x) >= 1000 else f"{x:g}"


def to_svg(fig):
    buf = io.StringIO()
    fig.savefig(buf, format="svg", bbox_inches="tight", pad_inches=0.05)
    plt.close(fig)
    return buf.getvalue()


def legend_above(ax, n):
    ax.legend(loc="lower left", bbox_to_anchor=(0, 1.0), ncols=n, handlelength=1.2, borderaxespad=0, columnspacing=1.2)


def figure(title, subtitle, svg):
    return f"""
<figure class="fig">
  <figcaption><strong>{html.escape(title)}</strong><span>{html.escape(subtitle)}</span></figcaption>
  {svg}
</figure>"""


def bars(title, subtitle, labels, series, ylabel, pct=False, band=None, ylim=None):
    """series: list of (label, values, slot). One group of bars a seed."""
    fig, ax = plt.subplots(figsize=(6.4, 2.6))
    n = len(series)
    xs = list(range(len(labels)))
    w = 0.8 / n
    if band is not None:
        ax.axhspan(band[0], band[1], color=INK, alpha=0.22, label=band[2], zorder=0)
    for i, (label, values, slot) in enumerate(series):
        ax.bar([x - 0.4 + w * (i + 0.5) for x in xs], values, width=w * 0.9, color=SERIES[slot], label=label)
    ax.set_xticks(xs, labels)
    ax.set_ylabel(ylabel)
    if ylim:
        ax.set_ylim(*ylim)
    if pct:
        ax.yaxis.set_major_formatter(lambda y, _p: f"{y:.0%}")
    ax.yaxis.set_major_locator(MaxNLocator(4))
    ax.axhline(0, color=INK, linewidth=0.8)
    legend_above(ax, n + (band is not None))
    return figure(title, subtitle, to_svg(fig))


def boxes(title, subtitle, labels, values, ylabel, means=None):
    """values: list of lists, one a seed - the run's own count at each census."""
    fig, ax = plt.subplots(figsize=(6.4, 2.6))
    bp = ax.boxplot(values, tick_labels=labels, widths=0.55, patch_artist=True, showfliers=False)
    for patch in bp["boxes"]:
        patch.set_facecolor(SERIES[0])
        patch.set_alpha(0.55)
        patch.set_edgecolor(INK)
    for part in ("whiskers", "caps", "medians"):
        for line in bp[part]:
            line.set_color(INK)
    if means:
        ax.plot(range(1, len(means) + 1), means, "o", color=SERIES[1], label="the run's mean")
        legend_above(ax, 1)
    ax.set_ylabel(ylabel)
    ax.yaxis.set_major_locator(MaxNLocator(4))
    return figure(title, subtitle, to_svg(fig))


def data_table(cols, rows_by_name, every=1):
    out = []
    for name, rows in rows_by_name.items():
        body = "".join("<tr>" + "".join(f"<td>{r[c]}</td>" for c in cols) + "</tr>" for r in rows[::every])
        out.append(f"<details><summary>{html.escape(name)}</summary><div class='tw'><table><thead><tr>"
                   + "".join(f"<th>{c}</th>" for c in cols) + f"</tr></thead><tbody>{body}</tbody></table></div></details>")
    return "\n".join(out)


# ---------- page ----------

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



def diagram(values, seeds):
    """The ruler: where the six controls of one world fall, against the line a law had to clear."""
    lo = min(values) - 0.3
    hi = max(max(values) + 0.3, lo + 1.6)
    x = lambda v: 70 + (v - lo) / (hi - lo) * 580  # noqa: E731
    ticks = [t for t in range(int(lo) + 1, int(hi) + 1)]
    tick_svg = "".join(
        f'<line x1="{x(t):.0f}" y1="106" x2="{x(t):.0f}" y2="114"/>'
        f'<text x="{x(t):.0f}" y="132" text-anchor="middle" fill="currentColor" stroke="none">{t}</text>'
        for t in ticks)
    dots = "".join(f'<circle cx="{x(v):.0f}" cy="110" r="5" fill="var(--s1)" stroke="none"/>' for v in values)
    a, b = x(min(values)), x(max(values))
    c, d = x(min(values)), x(min(values) + 1)
    return f"""
<figure class="diagram">
<svg viewBox="0 0 720 210" role="img" aria-label="The six control runs of one world spread wider than the one kind a law had to add" style="max-width:100%;height:auto;display:block">
<defs><marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="currentColor"/></marker></defs>
<g fill="none" stroke="currentColor" stroke-width="1.2" font-size="12" font-family="system-ui, sans-serif">
  <line x1="60" y1="110" x2="670" y2="110"/>
  {tick_svg}
  {dots}
  <line x1="{a:.0f}" y1="62" x2="{b:.0f}" y2="62" stroke="var(--s1)" stroke-width="2" marker-start="url(#arr)" marker-end="url(#arr)"/>
  <line x1="{a:.0f}" y1="66" x2="{a:.0f}" y2="102" stroke="var(--s1)" stroke-dasharray="3 3"/>
  <line x1="{b:.0f}" y1="66" x2="{b:.0f}" y2="102" stroke="var(--s1)" stroke-dasharray="3 3"/>
  <text x="{(a + b) / 2:.0f}" y="48" text-anchor="middle" fill="currentColor" stroke="none">one world, six seeds: {max(values) - min(values):.2f} kinds apart</text>
  <line x1="{c:.0f}" y1="166" x2="{d:.0f}" y2="166" marker-start="url(#arr)" marker-end="url(#arr)"/>
  <text x="{(c + d) / 2:.0f}" y="158" text-anchor="middle" fill="currentColor" stroke="none">+1 kind: what a law had to add</text>
  <text x="60" y="200" fill="currentColor" stroke="none" font-size="11">each dot is a 100,000-step run of the same world with a different seed</text>
  <text x="670" y="200" text-anchor="end" fill="currentColor" stroke="none" font-size="11">kinds at a census</text>
</g>
</svg>
<figcaption>Figure 1. The ruler and the thing measured. Six runs of one world, nothing added, land {min(values):.2f}-{max(values):.2f} kinds apart; the pass line asked a law for one kind more than its own control. An effect that size cannot be told from the next seed.</figcaption>
</figure>
"""

ROOT = os.path.dirname(os.path.dirname(HERE))
E081 = os.path.join(ROOT, "experiments", "e081_drink", "results", "ladder", "c1225_life9_u0")
E092 = os.path.join(HERE, "results", "ladder", "c1225_life9_ctl")
PRIOR = [("e089 S+Fb", "e089_fiber", "S+Fb"), ("e090 D+B+Fb", "e090_drift", "D+B+Fb"), ("e091 crown", "e091_crown", "crown")]


def effects():
    """The three laws rejected on seeds 9-11 since e087: each seed's count, and its control's."""
    out = []
    for label, folder, run in PRIOR:
        rows = {r["run"]: r for r in rows_of(os.path.join("..", folder, "results", "sweep.csv"))}
        law = [float(rows[f"{run} {s}"]["kinds_at"]) for s in (9, 10, 11)]
        ctl = [float(rows[f"control {s}"]["kinds_at"]) for s in (9, 10, 11)]
        out.append((label, [a - b for a, b in zip(law, ctl)], law))
    return out


def reproduces():
    """e092's seed 9 against e081's, column for column (the clocks aside)."""
    if not os.path.exists(E092 + "_row.csv"):
        return -1, 0, 0
    a = list(csv.DictReader(open(E092 + "_log.csv")))
    b = list(csv.DictReader(open(E081 + "_log.csv")))
    shared = [k for k in a[0] if k in b[0] and not k.startswith("ms_")]
    n = min(len(a), len(b))
    bad = sum(a[i][k] != b[i][k] for i in range(n) for k in shared)
    return bad, len(shared), n


def spread(v):
    return max(v) - min(v)


def main():
    ladder = rows_of("results/ladder.csv")
    census = rows_of("results/census.csv")
    seeds = [int(float(r["seed"])) for r in ladder]
    labels = [f"seed {s}" for s in seeds]
    kinds_at = num(ladder, "kinds_at")
    placed = num(ladder, "placed_at")
    per_census = [[float(r["kinds"]) for r in census if int(float(r["seed"])) == s] for s in seeds]
    old, new = kinds_at[:3], kinds_at
    eff = effects()
    bad, cols, rows_n = reproduces()
    band = (-spread(new) / 2, spread(new) / 2, "the control's own spread")

    charts = [
        bars("Kinds at a census, by seed", "Six runs of the same world, nothing added. The bar is the run's mean over 65 censuses.",
             labels, [("kinds at a census", kinds_at, 0)], "kinds", ylim=(0, max(kinds_at) * 1.25)),
        boxes("The count moves from census to census", "Box: the middle half of a run's censuses; the line, its median. A flat box would mean a settled count.",
              labels, per_census, "kinds at a census"),
        bars("The rejected effects against the control's spread", "Each law less its own control, by seed. Inside the band the effect is smaller than the seeds' own noise.",
             ["seed 9", "seed 10", "seed 11"], [(lab, v, i) for i, (lab, v, _) in enumerate(eff)], "kinds", band=band),
        bars("Kinds kept to a place", "Of the kinds held at a census, how many keep to one medium. The second measure a step is judged on.",
             labels, [("kinds kept to a place", placed, 2)], "kinds", ylim=(0, max(placed) * 1.3)),
        bars("Which world each seed falls into", "The kills' share of what bodies eat, and the largest line's share of the land's bodies.",
             labels, [("kills' share of intake", num(ladder, "kills"), 1),
                      ("the largest line's share", num(ladder, "top_share"), 3)], "share", pct=True),
        bars("The crowd is the same in every seed", "Moves blocked and children born with no room, over the second half of each run.",
             labels, [("moves blocked", num(ladder, "blocked"), 4),
                      ("births with no room", num(ladder, "no_room"), 0)], "share", pct=True, ylim=(0, 0.65)),
    ]

    summary = "".join(
        f"<tr><td>seed {s}</td><td>{r['kinds_at']:.2f}</td><td>{r['placed_at']:.2f}</td><td>{r['top_kind']:.0%}</td>"
        f"<td>{r['top_share']:.0%}</td><td>{r['kills']:.0%}</td><td>{r['pop']:.0f}</td><td>{r['travel']:.1f}</td>"
        f"<td>{r['blocked']:.0%}</td><td>{r['no_room']:.0%}</td></tr>"
        for s, r in ((int(float(r["seed"])), {k: float(v) for k, v in r.items() if k not in ("ways", "world_band", "name")}) for r in ladder))
    med = lambda v: st.median(v)  # noqa: E731
    summary += (f"<tr><td><strong>median</strong></td><td>{med(kinds_at):.2f}</td><td>{med(placed):.2f}</td>"
                f"<td>{med(num(ladder, 'top_kind')):.0%}</td><td>{med(num(ladder, 'top_share')):.0%}</td>"
                f"<td>{med(num(ladder, 'kills')):.0%}</td><td>{med(num(ladder, 'pop')):.0f}</td>"
                f"<td>{med(num(ladder, 'travel')):.1f}</td><td>{med(num(ladder, 'blocked')):.0%}</td>"
                f"<td>{med(num(ladder, 'no_room')):.0%}</td></tr>")
    summary += (f"<tr><td><strong>spread</strong></td><td>{spread(kinds_at):.2f}</td><td>{spread(placed):.2f}</td>"
                f"<td>{spread(num(ladder, 'top_kind')):.0%}</td><td>{spread(num(ladder, 'top_share')):.0%}</td>"
                f"<td>{spread(num(ladder, 'kills')):.0%}</td><td>{spread(num(ladder, 'pop')):.0f}</td>"
                f"<td>{spread(num(ladder, 'travel')):.1f}</td><td>{spread(num(ladder, 'blocked')):.0%}</td>"
                f"<td>{spread(num(ladder, 'no_room')):.0%}</td></tr>")

    biggest = max((abs(v), lab, s) for lab, vs, _ in eff for v, s in zip(vs, (9, 10, 11)))
    law_spread = [spread(law) for _, _, law in eff]
    inside = sum(abs(v) <= spread(new) / 2 for _, vs, _ in eff for v in vs)
    tables = data_table(["seed", "step", "kinds", "placed"], {"Kinds at each census": census}, every=3)

    checkline = (f"{cols} columns of the log agreed on all {rows_n} rows (the clocks aside)." if bad == 0
                 else "the check run is missing." if bad < 0
                 else f"{bad} cells of {cols} columns x {rows_n} rows differ.")

    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>e092 The yardstick - Report</title>
<style>{CSS}</style>
</head>
<body>
<main>
<h1>e092: how wide is the ruler we have been measuring with?</h1>
<p class="sub">Experiment report - 2026-09-20 - six runs of the same world, no law added (#102)</p>

<section class="tldr">
<h2>TL;DR</h2>
<p>The same world, run six times with nothing changed but the seed, counts between {min(new):.2f} and
{max(new):.2f} ways of living - a spread of {spread(new):.2f}, as wide as the effects we have been rejecting,
and every large one of those belongs to the one seed whose control counts highest. None of the three laws
raised the count on any seed; what cannot be read is the size of the fall on any one of them. From here a
step runs on six seeds and is read as a distribution.</p>
</section>

<h2>1. Question</h2>
<p>Ten laws have been proposed since e075 and none was kept. Each was run on three seeds and asked for one
more kind of living on every seed. Nobody had measured what the count does when <em>nothing</em> changes.</p>
<ol>
  <li><strong>Does this build reproduce the old control?</strong> The crates have grown since those runs; if
  their control has drifted, the ladder cannot be extended at all.</li>
  <li><strong>Is the seeds' own spread as large as the effects we reject?</strong> If it is, the three-seed
  pass line was noise, and the judging has to change.</li>
</ol>

<h2>2. The world and the runs</h2>
<p>Nothing new is built here. The world is stage C's default: c1225's climate, its three producers, bodies of
four block kinds with the trade-offs kept since e072 - heat paid in water, wood eaten behind a hard tip, the
flesh of kills, height, light. Every 1,000 steps from step 36,000 a run writes down every
grown body; a kind is a birth form holding 5% of them at that census (e068).</p>
{diagram(kinds_at, seeds)}
<p><strong>Runs.</strong> Six seeds - 9, 10 and 11 from e081's ladder, 12, 13 and 14 run here - 100,000 steps
each, one thread, 52-73 minutes a run with four at once; a seventh run repeats seed 9 as the check. We read:</p>
<ul class="measures">
  <li><strong>kinds at a census</strong> - ways of living, averaged over the 65 censuses of a run.</li>
  <li><strong>kinds kept to a place</strong> - of those kinds, how many keep to one medium.</li>
  <li><strong>the largest line's share</strong> - one lineage's hold on the land; a world with one winner is near 1.</li>
  <li><strong>the kills' share</strong> - how much of what bodies eat is other bodies: which world state the seed fell into.</li>
  <li><strong>the crowd</strong> - the share of moves blocked and of children born with no room.</li>
</ul>

<h2>3. Results</h2>
<div class="tw"><table>
<thead><tr><th>Seed</th><th>kinds</th><th>placed</th><th>top kind</th><th>top line</th><th>kills</th><th>bodies</th><th>travel</th><th>blocked</th><th>no room</th></tr></thead>
<tbody>{summary}</tbody></table></div>
<ol class="verdicts">
<li><span class="verdict{"" if bad == 0 else " no"}">{"Yes" if bad == 0 else "No"}</span> 1. This crate reproduces e081's control:
{checkline}</li>
<li><span class="verdict">Yes</span> 2. The control's own spread is {spread(new):.2f} kinds, wider than
{inside} of the 9 rejected effects and than the +1 kind the pass line asked for.</li>
</ol>

<h3>3.1 The same world counts {min(new):.1f} to {max(new):.1f} ways of living</h3>
<div class="grid2">
{charts[0]}
{charts[1]}
</div>
<p>The seed decides the count as much as a law does, and within a run it is not steady either: half of a
run's censuses lie {st.median([st.quantiles(v, n=4)[2] - st.quantiles(v, n=4)[0] for v in per_census]):.1f}
kinds apart, so only the mean over the 65 is worth quoting. Three seeds gave a range of {spread(old):.2f};
the three new ones all fall inside it, so six seeds give the same {spread(new):.2f} around a median of
{st.median(new):.2f}. The range is the world's, not a shortage of runs.</p>

<h3>3.2 The effects we rejected sit inside that spread</h3>
<div class="grid2">
{charts[2]}
{charts[3]}
</div>
<p>Every large effect belongs to seed 10 - {biggest[0]:.2f}, 1.69 and 1.51 kinds - and seed 10 is the seed
whose control counts highest of the six. Pairing a law with a control on its own seed does not cancel that
draw, it adds one to the other: each law's own three runs spread {min(law_spread):.2f}-{max(law_spread):.2f},
about as wide as the control's six. The second measure is no steadier than the first: kinds kept to a place
spreads {spread(placed):.2f} over six seeds, where three suggested 0.27. e091's fall of 1.6 clears even that,
on all three seeds; its fall in the count never did.</p>

<h3>3.3 What does not move with the seed</h3>
<div class="grid2">
{charts[4]}
{charts[5]}
</div>
<p>The crowd is the same in every world: {min(num(ladder, 'blocked')):.0%}-{max(num(ladder, 'blocked')):.0%}
of moves blocked and {min(num(ladder, 'no_room')):.0%}-{max(num(ladder, 'no_room')):.0%} of children born with
nowhere to go. That is nearly half of every birth, against the 24-33% recorded in e070, and it is the one
number no seed argues with. What the seed does decide is the world state: the largest line holds
{min(num(ladder, 'top_share')):.0%} of the land in one world and {max(num(ladder, 'top_share')):.0%} in
another, and the kills' share is the only other measure that holds still.</p>

<h2>4. Discussion</h2>
<p>The count of ways of living is a mean of 65 noisy censuses in a world whose trajectory the seed re-draws.
Pairing a law with a control on the same seed does not remove that: the law changes the trajectory, so the
pair is no longer the same world. What survives is the categorical reading - is there a kind led by the new
food, does a form keep to the new place - which decided e089, e090 and e091 and is not noise-limited.</p>
<p>This does not say the rejected laws worked: none of the three raised the count on any of the nine pairs,
so the direction is consistent even where the size is not. It says those experiments could not have told
half a kind of law from half a kind of draw,
and that a law which changes the count by one kind is not worth looking for at this crowd: half of all births
already fail for want of room, and that is the same in every seed.</p>
<p>What it costs: every stage C step now runs six times instead of three, about two hours a batch on the Mac
instead of one. That is the price of a reading that means something.</p>

<h2>5. Conclusion and next step</h2>
<p>The ladder is six seeds wide and kept (<code>results/ladder</code>). A stage C step is read against its
distribution - median and spread - and never as "+1 kind on every seed"; a piece meant to replace the world is
judged on its own measures and becomes the new control. Next is #103, the first piece of P3: a block that eats
the light, which is also the first law aimed at the crowd these runs found in every seed.</p>

<h2>Appendix: data</h2>
<p>One row a run in <code>results/ladder.csv</code>, one a kind in <code>results/kinds.csv</code>, one a census
below and in <code>results/census.csv</code> (every third census shown). The runs are
<code>results/ladder/c1225_life{{12,13,14,9}}_ctl_*</code>; seeds 9-11 are e081's. Build this report with
<code>uv run python experiments/e092_yardstick/report.py</code>.</p>
{tables}
</main>
</body>
</html>
"""
    out = os.path.join(HERE, "report.html")
    with open(out, "w") as f:
        f.write(page)
    prose = " ".join(m[1] for m in re.findall(r"<(p|li)(?:\s[^>]*)?>(.*?)</\1>",
                                              page.split("<h1>")[1].split("<h2>Appendix")[0], re.S))
    print(f"wrote {out} ({os.path.getsize(out)//1024} KB, "
          f"{len(re.sub(r'<[^>]+>', ' ', prose).split())} words of prose; the budget is 1,000)")


if __name__ == "__main__":
    main()
