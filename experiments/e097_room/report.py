#!/usr/bin/env python3
"""Build report.html for e097 (#109): the crowd measured at its cause.

Charts: matplotlib, exported as SVG and inlined. Diagram: hand-written SVG.
Run from the repo root: uv run python experiments/e097_room/report.py
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




# ---------- this experiment's data ----------

def rows(path):
    with open(os.path.join(HERE, path)) as f:
        return list(csv.DictReader(f))


def room_rows(start=20000):
    return [r for r in rows("results/c1225_life9_probe_room.csv") if int(r["step"]) >= start]


def log_series(path, key, upto=None):
    xs, ys = [], []
    with open(path) as f:
        for r in csv.DictReader(f):
            if upto is None or int(r["step"]) <= upto:
                xs.append(int(r["step"]))
                ys.append(float(r[key]))
    return xs, ys


def bar_chart(title, subtitle, labels, series, xlabel="", pct=False):
    """series: list of (label, values, slot). One group of bars per label."""
    fig, ax = plt.subplots(figsize=(6.4, 2.6))
    n = len(series)
    width = 0.8 / n
    for i, (name, values, slot) in enumerate(series):
        xs = [j + (i - (n - 1) / 2) * width for j in range(len(labels))]
        ax.bar(xs, values, width=width * 0.92, color=SERIES[slot], label=name)
    ax.set_xticks(range(len(labels)), labels)
    ax.set_xlabel(xlabel, loc="right")
    ax.yaxis.set_major_locator(MaxNLocator(4))
    ax.yaxis.set_major_formatter((lambda y, _p: f"{y:.0%}") if pct else kfmt)
    legend_above(ax, n)
    return figure(title, subtitle, to_svg(fig))


def step_chart(title, subtitle, xs, series, xlabel, pct=False, ylabel_fmt=None):
    fig, ax = plt.subplots(figsize=(6.4, 2.6))
    for label, ys, slot in series:
        ax.plot(xs, ys, color=SERIES[slot], linewidth=1.8, marker="o", markersize=4, label=label)
    ax.set_xticks(range(len(xs)), xs)
    ax.set_xlabel(xlabel, loc="right")
    ax.yaxis.set_major_locator(MaxNLocator(4))
    ax.yaxis.set_major_formatter((lambda y, _p: f"{y:.0%}") if pct else (ylabel_fmt or kfmt))
    legend_above(ax, len(series))
    return figure(title, subtitle, to_svg(fig))


def scatter_chart(title, subtitle, groups, xlabel, ylabel):
    fig, ax = plt.subplots(figsize=(6.4, 2.6))
    for label, xs, ys, slot in groups:
        ax.scatter(xs, ys, s=34, color=SERIES[slot], label=label)
    ax.set_xlabel(xlabel, loc="right")
    ax.set_ylabel(ylabel)
    ax.xaxis.set_major_formatter(lambda x, _p: f"{x:.0%}")
    ax.yaxis.set_major_locator(MaxNLocator(4))
    legend_above(ax, len(groups))
    return figure(title, subtitle, to_svg(fig))


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

# Hand-written mechanism diagram: the birth rule, its 24 spots, and the ring it never looks at.
DIAGRAM = """
<figure class="diagram">
<svg viewBox="0 0 720 250" role="img" aria-label="The birth rule searches four rays; the room is on the ring it never looks at" style="max-width:100%;height:auto;display:block">
<defs><marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="currentColor"/></marker></defs>
<g fill="none" stroke="currentColor" stroke-width="1.2" font-size="12" font-family="system-ui, sans-serif">
  <rect x="55" y="55" width="130" height="130" rx="4" stroke-dasharray="3 3" opacity="0.5"/>
  <circle cx="120" cy="120" r="7" fill="currentColor" stroke="none"/>
  <text x="120" y="204" text-anchor="middle" fill="currentColor" stroke="none">parent</text>
  <g stroke-width="2">
    <line x1="128" y1="120" x2="180" y2="120" marker-end="url(#arr)"/>
    <line x1="112" y1="120" x2="60" y2="120" marker-end="url(#arr)"/>
    <line x1="120" y1="112" x2="120" y2="60" marker-end="url(#arr)"/>
    <line x1="120" y1="128" x2="120" y2="180" marker-end="url(#arr)"/>
  </g>
  <text x="120" y="40" text-anchor="middle" fill="currentColor" stroke="none">4 rays, 1 body length: 24 spots</text>
  <g stroke="var(--s1)" stroke-width="2"><rect x="365" y="55" width="130" height="130" rx="4"/></g>
  <circle cx="430" cy="120" r="7" fill="currentColor" stroke="none"/>
  <text x="430" y="204" text-anchor="middle" fill="currentColor" stroke="none">parent</text>
  <g fill="var(--s1)" stroke="none">
    <circle cx="365" cy="55" r="4"/><circle cx="398" cy="55" r="4"/><circle cx="463" cy="55" r="4"/><circle cx="495" cy="55" r="4"/>
    <circle cx="365" cy="88" r="4"/><circle cx="495" cy="88" r="4"/><circle cx="365" cy="152" r="4"/><circle cx="495" cy="152" r="4"/>
    <circle cx="365" cy="185" r="4"/><circle cx="398" cy="185" r="4"/><circle cx="463" cy="185" r="4"/><circle cx="495" cy="185" r="4"/>
  </g>
  <text x="430" y="40" text-anchor="middle" fill="var(--s1)" stroke="none">the same ring: 8r spots, 98% never tried</text>
  <line x1="200" y1="120" x2="350" y2="120" marker-end="url(#arr)"/>
  <text x="275" y="112" text-anchor="middle" fill="currentColor" stroke="none">35% of failed</text>
  <text x="275" y="134" text-anchor="middle" fill="currentColor" stroke="none">births fit here</text>
  <line x1="560" y1="120" x2="700" y2="120" marker-end="url(#arr)"/>
  <text x="630" y="112" text-anchor="middle" fill="currentColor" stroke="none">jam 47% - 33%</text>
  <text x="630" y="134" text-anchor="middle" fill="currentColor" stroke="none">kinds 7.5 - 5.0</text>
</g>
</svg>
<figcaption>Figure 1. A child is placed at the first spot it fits, searched along four axis rays out to one body
length: 24 spots. Every spot a failed birth tried was held by another body, and at the nearest distance with
room, 98% of the spots that fit lie off those rays. Letting the search walk the whole ring, out to two body
lengths, relieves the jam - and costs ways of living.</figcaption>
</figure>
"""

RUNGS = ["control", "ring r1", "rays r2", "ring r2", "rays r4"]
SEEDS = [9, 10, 11, 12, 13, 14]
CTL_LOG = os.path.join(os.path.dirname(os.path.dirname(HERE)), "experiments", "e081_drink", "results", "ladder", "c1225_life9_u0_log.csv")

TABLE = [("kinds at a census", "kinds_at", "{:.2f}"), ("kinds kept to a place", "placed_at", "{:.2f}"),
         ("the largest kind's share", "top_kind", "{:.1%}"), ("the largest line's share", "top_share", "{:.1%}"),
         ("kills' share of intake", "kills", "{:.1%}"), ("births with no room", "no_room", "{:.1%}"),
         ("moves blocked", "blocked", "{:.1%}"), ("bodies", "pop", "{:,.0f}"),
         ("travel of a grown body", "travel", "{:.1f}")]


def median(v):
    v = sorted(v)
    n = len(v)
    return v[n // 2] if n % 2 else (v[n // 2 - 1] + v[n // 2]) / 2


def main():
    room = room_rows()
    near = [int(r["near"]) / int(r["reach"]) for r in room]
    ladder = {r["run"]: r for r in rows("results/ladder.csv")}
    batch = rows("results/batch.csv")
    ctl = [r for r in batch if r["run"] == "control"]
    run = [r for r in batch if r["run"] == "ring2"]

    # 1. how far the nearest spot with room is, as a cumulative share
    xs = [i / 4 for i in range(1, 33)]
    cum = [sum(1 for v in near if 0 < v <= x) / len(near) for x in xs]
    charts = [figure("Room is there, just off the rays",
                     "Share of failed births with a spot that fits within x body lengths. The rule itself reaches 1.",
                     _cum_svg(xs, cum))]

    # 2. the parent's cell is half empty
    charts.append(hist_chart("The cells they fail in are half empty",
                             "Free sub-cells of the 16 a cell holds, in the parent's cell at a failed birth. 16 would be an empty cell.",
                             [("failed births", [int(r["free_here"]) for r in room], 0)], bins=range(0, 18), xlabel="free sub-cells"))

    # 3. the jam by rung, and 4. what it costs
    charts.append(step_chart("Every rung relieves the jam",
                             "Births that find no room, seed 9 at 40,000 steps. Flat would mean the search was not the constraint.",
                             RUNGS, [("births with no room", [float(ladder[k]["no_room"]) for k in RUNGS], 1)], "rung", pct=True))
    charts.append(step_chart("And every rung costs ways of living",
                             "Kinds at a census on the same runs. The control ladder's six seeds spread 1.02 kinds.",
                             RUNGS, [("kinds at a census", [float(ladder[k]["kinds_at"]) for k in RUNGS], 2),
                                     ("kinds kept to a place", [float(ladder[k]["placed_at"]) for k in RUNGS], 3)], "rung",
                             ylabel_fmt=lambda y, _p: f"{y:.0f}"))

    # 5. the trade, run by run
    charts.append(scatter_chart("The trade, one point a run",
                                "Jam against kinds: the ladder's rungs at 40,000 steps and the batch's twelve runs at 100,000.",
                                [("control, six seeds", [float(r["no_room"]) for r in ctl], [float(r["kinds_at"]) for r in ctl], 0),
                                 ("ring r2, six seeds", [float(r["no_room"]) for r in run], [float(r["kinds_at"]) for r in run], 1),
                                 ("ladder rungs, seed 9", [float(ladder[k]["no_room"]) for k in RUNGS], [float(ladder[k]["kinds_at"]) for k in RUNGS], 2)],
                                "births with no room", "kinds"))

    # 6, 7. the batch, seed by seed
    charts.append(bar_chart("Fewer kinds on every seed",
                            "Kinds at a census over 51 censuses of each run's second half.",
                            [str(s) for s in SEEDS],
                            [("control", [float(r["kinds_at"]) for r in ctl], 0), ("ring r2", [float(r["kinds_at"]) for r in run], 1)], "seed"))
    charts.append(bar_chart("One kind takes twice the world",
                            "The largest kind's share of the grown bodies. Higher is a world parted into fewer ways of living.",
                            [str(s) for s in SEEDS],
                            [("control", [float(r["top_kind"]) for r in ctl], 0), ("ring r2", [float(r["top_kind"]) for r in run], 1)], "seed", pct=True))

    # 8. the plant pays
    cx, cy = log_series(CTL_LOG, "grass", upto=100000)
    rx, ry = log_series(os.path.join(HERE, "results", "batch", "c1225_life9_ring2_log.csv"), "grass")
    charts.append(line_chart("The grass pays for the births that now succeed",
                             "Grass standing in the world, seed 9. A flat pair would mean the extra children cost the world nothing.",
                             cx, [("control", cy, 0), ("ring r2", ry[:len(cx)], 1)], ymin=0))

    summary = "".join(
        f"<tr><td>{label}</td><td>{fmt.format(median([float(r[k]) for r in ctl]))}</td>"
        f"<td>{fmt.format(median([float(r[k]) for r in run]))}</td>"
        f"<td>{fmt.format(median([float(r[k]) for r in run]) - median([float(r[k]) for r in ctl]))}</td>"
        f"<td>{fmt.format(max(float(r[k]) for r in ctl) - min(float(r[k]) for r in ctl))}</td></tr>"
        for label, k, fmt in TABLE)

    tables = ("<details><summary>The batch, run by run</summary><div class='tw'><table><thead><tr>"
              + "".join(f"<th>{h}</th>" for h in ["run", "seed"] + [label for label, _, _ in TABLE])
              + "</tr></thead><tbody>"
              + "".join("<tr><td>" + r["run"] + "</td><td>" + r["seed"] + "</td>"
                        + "".join(f"<td>{fmt.format(float(r[k]))}</td>" for _, k, fmt in TABLE) + "</tr>" for r in batch)
              + "</tbody></table></div></details>"
              + "<details><summary>The ladder, rung by rung (seed 9, 40,000 steps)</summary><div class='tw'><table><thead><tr>"
              + "".join(f"<th>{h}</th>" for h in ["rung", "births with no room", "moves blocked", "placed at", "kinds", "kept to a place", "largest kind", "bodies", "ms a step"])
              + "</tr></thead><tbody>"
              + "".join(f"<tr><td>{k}</td><td>{float(ladder[k]['no_room']):.1%}</td><td>{float(ladder[k]['blocked']):.1%}</td>"
                        f"<td>{float(ladder[k]['place_k']):.2f}</td><td>{float(ladder[k]['kinds_at']):.2f}</td>"
                        f"<td>{float(ladder[k]['placed_at']):.2f}</td><td>{float(ladder[k]['top_kind']):.1%}</td>"
                        f"<td>{float(ladder[k]['pop']):,.0f}</td><td>{float(ladder[k]['ms_step']):.1f}</td></tr>" for k in RUNGS)
              + "</tbody></table></div></details>")

    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>e097 The room a birth cannot find - Report</title>
<style>{CSS}</style>
</head>
<body>
<main>
<h1>e097: half of all births fail in a world nine tenths empty</h1>
<p class="sub">Experiment report - 2026-09-21 - one instrumented run, four rungs, and a six-seed batch on c1225</p>

<section class="tldr">
<h2>TL;DR</h2>
<p>Twelve laws in a row were absorbed by the crowd, so we measured the crowd. The jam is not the world's:
a body stands on a tenth of the cells, and three failed births in four had a spot that fits within two body
lengths, almost always off the four rays the rule searches. Widening the search relieves the jam (47% of
births to 33%) and costs ways of living (7.53 kinds to 5.01). The narrow rule was holding the lines apart:
room is the next piece's background, not one of its axes.</p>
</section>

<h2>1. Question</h2>
<p>A child is placed at the first spot its whole rectangle fits, looked for along four axis directions out
to one body length - 24 spots. Nearly half of all births fail there, in cells that are half empty, and
every ecological law we have tried since has been swallowed by that jam. Is it the world's, or the rule's?</p>
<ol>
  <li><strong>What a failed birth hits.</strong> Bodies, or walls - the sea and the crownless cells?</li>
  <li><strong>Whether room exists.</strong> Within one body length, two, four, eight - or nowhere?</li>
  <li><strong>Whether relieving it changes who wins,</strong> or only how many bodies there are.</li>
</ol>

<h2>2. The world</h2>
<p>Stage C's default world: a 512x512 torus with climate, water, producers and bodies built of blocks on a
grid of side 4 to 16, at a sixteenth of the world's matter. Nothing in it changed. A measure was added to
the birth path (a sample of failed births, with their own random stream, measured where they failed), and
then two knobs: how far a child looks, and whether it looks at every spot at that distance or only along
the four rays.</p>
{DIAGRAM}
<p><strong>Runs.</strong> Step 0: one instrumented run, seed 9, 40,000 steps, 14,800 failed births measured.
Step 1: four rungs of the two knobs, same seed and length. Then the rung that relieves the jam most within
two body lengths, on the six seeds of the control ladder, 100,000 steps, against that ladder. Measured:</p>
<ul class="measures">
  <li><strong>What the tried spots hit</strong> - a body, or a wall.</li>
  <li><strong>Distance to the nearest spot with room</strong> - searched ring by ring, in body lengths.</li>
  <li><strong>Of that ring's spots, those on the four rays</strong> - 4 of 8r, if the rule could see them.</li>
  <li><strong>Free sub-cells here and around</strong> - of the 16 a cell holds.</li>
  <li><strong>Births with no room, moves blocked</strong> - the jam itself.</li>
  <li><strong>Kinds at a census, kinds kept to a place</strong> - ways of living, by birth form.</li>
  <li><strong>The largest kind's and the largest line's share</strong> - dominance.</li>
  <li><strong>Bodies, travel, grass standing</strong> - what the world does under it.</li>
</ul>

<h2>3. Results</h2>
<div class="tw"><table>
<thead><tr><th>measure (median of six seeds)</th><th>control</th><th>ring r2</th><th>effect</th><th>control's spread</th></tr></thead>
<tbody>{summary}</tbody></table></div>
<ol class="verdicts">
<li><span class="verdict">Yes</span> The tried spots are held by bodies: 100% of them, and not once by a wall.</li>
<li><span class="verdict">Yes</span> Room is there: within one body length for 35% of failures, two for 75%, four for 97%.</li>
<li><span class="verdict">Yes</span> It is off the rays: 98% of the spots with room at the nearest distance are ones the rule never tries.</li>
<li><span class="verdict no">No</span> Relieving it does not buy ways of living: 7.53 kinds to 5.01, against a control spread of 1.02.</li>
</ol>

<h3>3.1 The jam is the rule's, not the world's</h3>
<div class="grid2">
{charts[0]}
{charts[1]}
</div>
<p>A failed birth stands in a cell with 4 of its 16 sub-cells free and 5 more free in each neighbour. What
it cannot find is not empty ground but empty ground shaped like its own rigid grid and reached by one of
24 spots. Only 3 failures in 10,000 had nowhere to go within eight body lengths.</p>

<h3>3.2 Relief is real, and so is its price</h3>
<div class="grid2">
{charts[2]}
{charts[3]}
</div>
<p>The four rungs walk down the curve step 0 measured, and the ways of living fall with every one of them.
The shape alone (the same distance, the whole ring) already does both.</p>

<h3>3.3 The batch: the same trade on all six seeds</h3>
<div class="grid2">
{charts[4]}
{charts[5]}
{charts[6]}
{charts[7]}
</div>
<p>The largest line's share does not move outside the control's own band, so the world is not taken over by
one lineage; it is parted into fewer ways. Travel halves as well: with room next door, nothing sends a body
away. The grass is what pays for the children that now live.</p>

<h2>4. Discussion</h2>
<p>We went looking for a lid and found a wall between neighbours. The narrow birth rule kept a lineage
where its parent stood, and that limit on dispersal was holding the world's ways of living apart - the same
thing e083 found places doing. Let a child be laid anywhere within two body lengths and the winner spreads
fastest of all.</p>
<p>What it does not show: nothing here says a world with more room must hold fewer ways. It says this
world does, with rigid rectangular bodies placed whole, over 100,000 steps and six seeds. A body that bends,
that grows into a space, or that chooses where its children go might trade differently - the last of those
is a trait, and this piece was about laws of the world.</p>
<p>The cost of the relief is also ecological, not just accounting: the children that used to be laid down as
carrion are now bodies that eat, and the grass standing falls by a third.</p>

<h2>5. Conclusion and next step</h2>
<p>The crowd track closes. The jam was the birth rule's, it can be relieved, and relieving it costs ways of
living - so room is the background of the next piece, not one of its axes. Next is the set that replaces the
world: 3D bodies with a food only a tall body reaches.</p>

<h2>Appendix: data</h2>
<p>Medians over six seeds above; every run below. The full data is in <code>results/*.csv</code>, and what
each reading used - windows, censuses, thresholds - in <code>results/provenance.csv</code>. Build this report
with <code>uv run python experiments/e097_room/report.py</code>.</p>
{tables}
</main>
</body>
</html>
"""
    out = os.path.join(HERE, "report.html")
    with open(out, "w") as f:
        f.write(page)
    print(f"wrote {out} ({os.path.getsize(out)//1024} KB)")


def _cum_svg(xs, ys):
    fig, ax = plt.subplots(figsize=(6.4, 2.6))
    ax.plot(xs, ys, color=SERIES[0], linewidth=1.8)
    ax.axvline(1, color=SERIES[1], linewidth=1.2, linestyle="--")
    ax.text(1.12, 0.12, "the rule's own reach", color=SERIES[1], fontsize=9)
    ax.set_xlabel("body lengths", loc="right")
    ax.set_ylim(0, 1.02)
    ax.yaxis.set_major_locator(MaxNLocator(4))
    ax.yaxis.set_major_formatter(lambda y, _p: f"{y:.0%}")
    ax.margins(x=0)
    return to_svg(fig)


if __name__ == "__main__":
    main()
