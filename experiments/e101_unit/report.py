#!/usr/bin/env python3
"""Build report.html for e101 (#113): the body's water alone, on six seeds.

Charts: matplotlib, exported as SVG and inlined. Diagram: hand-written SVG.
Run from the repo root: uv run python experiments/e101_unit/report.py
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


# ---------- this experiment's data ----------

def rows(path):
    with open(os.path.join(HERE, path)) as f:
        return list(csv.DictReader(f))


def bar_chart(title, subtitle, labels, series, xlabel="", pct=False, fmt=None):
    """series: list of (label, values, slot). One group of bars per label."""
    fig, ax = plt.subplots(figsize=(6.4, 2.6))
    n = len(series)
    width = 0.8 / n
    for i, (name, values, slot) in enumerate(series):
        xs = [j + (i - (n - 1) / 2) * width for j in range(len(labels))]
        ax.bar(xs, values, width=width * 0.92, color=SERIES[slot], label=name)
    ax.set_xticks(range(len(labels)), labels)
    ax.set_xlabel(xlabel, loc="right")
    ax.yaxis.set_major_locator(MaxNLocator(4, integer=not pct))
    ax.yaxis.set_major_formatter((lambda y, _p: f"{y:.0%}") if pct else (fmt or kfmt))
    legend_above(ax, n)
    return figure(title, subtitle, to_svg(fig))


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


# Hand-written mechanism diagram: the body's water as part of the land's.
DIAGRAM = """
<figure class="diagram">
<svg viewBox="0 50 720 175" role="img" aria-label="The body's water is taken from the ground it stands on and given back to the air and the ground" style="max-width:100%;height:auto;display:block">
<defs><marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="currentColor"/></marker>
<marker id="arra" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="var(--s1)"/></marker></defs>
<g fill="none" stroke="currentColor" stroke-width="1.4" font-size="12" font-family="system-ui, sans-serif">
  <rect x="40" y="150" width="200" height="50" rx="6"/>
  <text x="140" y="172" text-anchor="middle" fill="currentColor" stroke="none">ground and pools</text>
  <text x="140" y="189" text-anchor="middle" fill="currentColor" stroke="none">of the body's own cell</text>
  <rect x="300" y="60" width="140" height="50" rx="6"/>
  <text x="370" y="82" text-anchor="middle" fill="currentColor" stroke="none">the body</text>
  <text x="370" y="99" text-anchor="middle" fill="currentColor" stroke="none">9.4 mm a block</text>
  <rect x="520" y="150" width="160" height="50" rx="6"/>
  <text x="600" y="180" text-anchor="middle" fill="currentColor" stroke="none">the air over the cell</text>
  <path d="M150,145 C170,95 230,85 294,85" stroke="var(--s1)" stroke-width="2.2" marker-end="url(#arra)"/>
  <text x="178" y="80" text-anchor="middle" fill="var(--s1)" stroke="none">drinks up to full (W1)</text>
  <path d="M446,85 C520,85 580,110 596,145" marker-end="url(#arr)"/>
  <text x="560" y="80" text-anchor="middle" fill="currentColor" stroke="none">dry air, sweat (W2)</text>
  <path d="M340,116 C320,150 290,172 246,175" marker-end="url(#arr)"/>
  <text x="330" y="160" text-anchor="start" fill="currentColor" stroke="none">death, lost blocks (W2)</text>
  <path d="M515,190 L246,190" stroke-dasharray="4 3" marker-end="url(#arr)"/>
  <text x="380" y="214" text-anchor="middle" fill="currentColor" stroke="none">rain and runoff (the climate)</text>
</g>
</svg>
<figcaption>Figure 1. <code>unit</code>: a block of a body's water is 9.4 mm of its cell's water (a full
sub-cell of ground holds 150 mm / 16). A body drinks out of the ground under it, and what it loses goes to the
air and the ground, so where a body can drink becomes a property of the place and the crowd drinks it down.</figcaption>
</figure>
"""

WORLDS = [("control", "control", 0), ("unit", "unit alone", 1), ("e100", "e100: unit + crown", 3)]
SEEDS = [9, 10, 11, 12, 13, 14]
TABLE = [("kinds at a census", "kinds_at", "{:.2f}"), ("kinds kept to a place", "placed_at", "{:.2f}"),
         ("the largest kind's share", "top_kind", "{:.1%}"), ("the largest line's share", "top_share", "{:.1%}"),
         ("kills' share of intake", "kills", "{:.1%}"), ("births with no room", "no_room", "{:.1%}"),
         ("bodies", "pop", "{:,.0f}"), ("travel of a grown body", "travel", "{:.1f}")]
REPLAY = [("ways holding 5%, a run", "held_a_run", "{:.1f}"), ("those ways agree", "held_agree", "{:.2f}"),
          ("their shares agree", "shares_agree", "{:.2f}"), ("the same largest way (of 6)", "same_largest_way", "{:.0f}"),
          ("the birth forms agree", "forms_agree", "{:.3f}")]


def median(v):
    v = sorted(v)
    n = len(v)
    return v[n // 2] if n % 2 else (v[n // 2 - 1] + v[n // 2]) / 2


def main():
    batch = rows("results/batch.csv")
    by = {w: {int(r["seed"]): r for r in batch if r["world"] == w} for w, _, _ in WORLDS}
    rep = {r["world"]: r for r in rows("results/replay.csv")}
    col = lambda w, k: [float(by[w][s][k]) for s in SEEDS]
    per_seed = lambda k: [(label, col(w, k), slot) for w, label, slot in WORLDS]

    charts = [
        bar_chart("Kinds at a census, seed by seed",
                  "Mean over 51 censuses of each run's second half. The control's six seeds spread 1.02.",
                  [str(s) for s in SEEDS], per_seed("kinds_at"), "seed", fmt=lambda y, _p: f"{y:g}"),
        bar_chart("Kinds kept to a place: the same median",
                  "Kinds whose bodies keep to one place (not the shore). Equal bars: the law parts no place.",
                  [str(s) for s in SEEDS], per_seed("placed_at"), "seed", fmt=lambda y, _p: f"{y:g}"),
        bar_chart("The tether: bodies stay by their water",
                  "Cells a grown body ends from where it was born. e100's set spreads them; unit alone holds them.",
                  [str(s) for s in SEEDS], per_seed("travel"), "seed", fmt=lambda y, _p: f"{y:g}"),
        bar_chart("No seed goes to one line",
                  "The largest lineage's share of the land's bodies. e100's seed 13 reached 99%.",
                  [str(s) for s in SEEDS], per_seed("top_share"), "seed", pct=True),
    ]

    summary = "".join(
        f"<tr><td>{label}</td>" + "".join(f"<td>{fmt.format(median(col(w, k)))}</td>" for w, _, _ in WORLDS)
        + f"<td>{fmt.format(max(col('control', k)) - min(col('control', k)))}</td></tr>"
        for label, k, fmt in TABLE)
    replay = "".join(
        f"<tr><td>{label}</td>" + "".join(f"<td>{fmt.format(float(rep[w][k]))}</td>" for w, _, _ in WORLDS) + "</tr>"
        for label, k, fmt in REPLAY)
    head = "".join(f"<th>{label}</th>" for _, label, _ in WORLDS)

    tables = ("<details><summary>Every run</summary><div class='tw'><table><thead><tr>"
              + "".join(f"<th>{h}</th>" for h in ["world", "seed"] + [label for label, _, _ in TABLE])
              + "</tr></thead><tbody>"
              + "".join("<tr><td>" + r["world"] + "</td><td>" + r["seed"] + "</td>"
                        + "".join(f"<td>{fmt.format(float(r[k]))}</td>" for _, k, fmt in TABLE) + "</tr>" for r in batch)
              + "</tbody></table></div></details>")

    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>e101 The body's water - Report</title>
<style>{CSS}</style>
</head>
<body>
<main>
<h1>e101: the body's water alone does no harm we can read</h1>
<p class="sub">Experiment report - 2026-09-25 - one law, six seeds, 100,000 steps on c1225</p>

<section class="tldr">
<h2>TL;DR</h2>
<p>e100 added three laws and lost 1.8 kinds on every seed. One of them, <code>unit</code> (a body's water is
part of the land's), is what the 3D set's water axis is built on, so we ran it alone. It costs 0.39 kinds at
the median, inside the control's spread of 1.02, and collapses no seed: it is kept. It tethers bodies to their
water (travel 5.2 to 3.0 cells), the opposite of e100's spreading, so e100's harm lies with the crown's half.
Next: #114, the 3D crate.</p>
</section>

<h2>1. Question</h2>
<p>Was it <code>unit</code> that cost e100 its kinds? e081 had read it on three seeds only, one of them 2.06
kinds down, and one seed beyond a six-seed spread decides nothing. The line was set before the run:</p>
<ol>
  <li><strong>Inside the spread</strong> - kinds at a census within 1.02 of the control's 7.53, no seed collapsing
  to one line: <code>unit</code> goes into the world.</li>
  <li><strong>If so, e100's harm was the crown's</strong> - shade, the crown's wet ground and wood's rest.</li>
</ol>

<h2>2. The world</h2>
<p>Stage C's default world, e092's, with one law added: e081's <code>unit</code> at 9.4. Nothing else
differs; e100's crate and command with the crown's four laws at 0.</p>
{DIAGRAM}
<p><strong>Runs.</strong> Six seeds (9-14), 100,000 steps, a census every 1,000 from 36,000: the control
ladder's own shape. Seeds 9-11 reproduce e081's runs bit for bit. Measured, each read the same way on the
control, this batch and e100's:</p>
<ul class="measures">
  <li><strong>Kinds at a census</strong> - ways of living by birth form, mean over censuses.</li>
  <li><strong>Kinds kept to a place</strong> - those whose bodies keep to one place.</li>
  <li><strong>The largest line's share</strong> - of the land's bodies; a collapse is near 100%.</li>
  <li><strong>Travel</strong> - cells a grown body ends from its birth.</li>
  <li><strong>Replay agreement</strong> - how alike the six seeds' leading ways are.</li>
</ul>

<h2>3. Results</h2>
<div class="tw"><table>
<thead><tr><th>measure (median of six seeds)</th>{head}<th>control's spread</th></tr></thead>
<tbody>{summary}</tbody></table></div>
<ol class="verdicts">
<li><span class="verdict">Yes</span> Inside the spread: 7.14 kinds against 7.53, a difference of 0.39 where the control spreads 1.02; the highest line share is 70.4%.</li>
<li><span class="verdict partly">Partly</span> e100's harm was not <code>unit</code>'s; the crown's half alone was not run, so it is the crown or the two together.</li>
</ol>

<h3>3.1 A small cost, not a collapse</h3>
<div class="grid2">
{charts[0]}
{charts[1]}
</div>
<p>Five seeds of six sit a little lower, and seed 10 (e081's -2.06) is beyond the spread alone. Kinds kept to
a place are unchanged at 4.34. The spread of the six is 1.63, wider than the control's but made of no
collapsed seed.</p>

<h3>3.2 Bodies stay by their water</h3>
<div class="grid2">
{charts[2]}
{charts[3]}
</div>
<p>A body's water is now where it drank, so it stays nearer: travel falls on five of six seeds. e100's set
did the opposite and one of its seeds went to a single line; this is e082's and e097's lesson again, that
whatever lets a lineage reach further levels the world.</p>

<h3>3.3 Replays</h3>
<div class="tw"><table>
<thead><tr><th>between the six seeds</th>{head}</tr></thead>
<tbody>{replay}</tbody></table></div>
<p>The leading way is the same in 4 of 6 seeds (control 2, e100 6); the bodies filling the ways stay as
different as before.</p>

<h2>4. Discussion</h2>
<p>The result keeps <code>unit</code> because the spread cannot tell its cost from noise, not because the
cost is shown to be zero: a ladder half as wide would read -0.39 as harm. That is decision rule 6 as written,
and the reason the next step's ledger can rest on it.</p>
<p>The crown's half was not run alone. It is a 2D stand-in for the crown the 3D set builds for real, so the
question it would answer is overtaken by the next piece.</p>

<h2>5. Conclusion and next step</h2>
<p><code>unit</code> 9.4 is kept. The default world is e092's with it, and these six runs are its control
ladder: 7.14 kinds (spread 1.63), 4.34 kept to a place (1.63). The 3D set's water axis - the drink at the
floor, the food higher up - is built on this ledger. Next is #114: the 3D crate, and whether anything lives
off the floor.</p>

<h2>Appendix: data</h2>
<p>Every run below; the full data is in <code>results/*.csv</code>, what each reading used in
<code>results/provenance.csv</code>. Build this report with
<code>uv run python experiments/e101_unit/report.py</code>.</p>
{tables}
</main>
</body>
</html>
"""
    out = os.path.join(HERE, "report.html")
    with open(out, "w") as f:
        f.write(page)
    print(f"wrote {out} ({os.path.getsize(out)//1024} KB)")


if __name__ == "__main__":
    main()
