#!/usr/bin/env python3
"""Build report.html for e075 (#90, what the flesh of kills needs to pay).

Charts: matplotlib, exported as SVG and inlined. Diagram: hand-written SVG.
Run from the repo root: uv run python experiments/e075_hunt/report.py
"""
import csv
import html
import io
import os
import statistics as st

import matplotlib
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator

matplotlib.use("svg")

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
E073 = os.path.join(ROOT, "experiments", "e073_forest", "results", "ladder")
LADDER = os.path.join(HERE, "results", "ladder")
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4"]
KIND_COLOR = {1: SERIES[0], 2: SERIES[1], 3: SERIES[3], 4: SERIES[2]}  # hard, muscle, sensor, gut
SEEDS = (9, 10, 11)
LAND = 110625

INK = "#898781"
plt.rcParams.update({
    "svg.fonttype": "none", "font.family": "sans-serif", "font.size": 9, "text.color": INK,
    "axes.edgecolor": INK, "axes.labelcolor": INK, "axes.facecolor": "none",
    "axes.spines.top": False, "axes.spines.right": False, "axes.spines.left": False,
    "axes.grid": True, "axes.grid.axis": "y", "grid.color": INK, "grid.alpha": 0.25, "grid.linewidth": 0.8,
    "xtick.color": INK, "ytick.color": INK, "ytick.left": False,
    "legend.frameon": False, "legend.fontsize": 9, "figure.facecolor": "none", "savefig.transparent": True,
})


# ---------- data ----------

def rows_of(path):
    with open(path) as f:
        return list(csv.DictReader(f))


def log_of(pre):
    return rows_of(pre + "_log.csv")


def col(rows, key, scale=1.0):
    return [float(r[key]) * scale for r in rows]


def kills_col(rows):
    """The flesh of the living per logged interval: e075's own column, else the meat less the dead."""
    if "kill_intake" in rows[0]:
        return col(rows, "kill_intake")
    return [float(r["meat_intake"]) - float(r["scavenged"]) for r in rows]


def sweep():
    """results/sweep.csv, keyed by run name."""
    return {r["name"]: r for r in rows_of(os.path.join(HERE, "results", "sweep.csv"))}


def mean_of(s, names, key, pct=False):
    v = [float(s[n][key]) for n in names if n in s]
    return st.mean(v) if v else float("nan")


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


def legend_above(ax, n):
    ax.legend(loc="lower left", bbox_to_anchor=(0, 1.0), ncols=n, handlelength=1.2, borderaxespad=0, columnspacing=1.2)


def line_chart(title, subtitle, xs, series, ymin=None, pct=False):
    fig, ax = new_axes()
    for label, ys, slot in series:
        ax.plot(xs, ys, color=SERIES[slot], linewidth=1.6, label=label)
    if ymin is not None:
        ax.set_ylim(ymin, max(v for _, ys, _ in series for v in ys) * 1.12)
    ax.yaxis.set_major_formatter((lambda y, _p: f"{y:.0%}") if pct else kfmt)
    ax.yaxis.set_major_locator(MaxNLocator(4))
    legend_above(ax, len(series))
    return figure(title, subtitle, to_svg(fig))


def figure(title, subtitle, svg):
    return f"""
<figure class="fig">
  <figcaption><strong>{html.escape(title)}</strong><span>{html.escape(subtitle)}</span></figcaption>
  {svg}
</figure>"""


def data_table(cols, rows_by_name):
    out = []
    for name, rows in rows_by_name.items():
        body = "".join("<tr>" + "".join(f"<td>{r.get(c, '')}</td>" for c in cols) + "</tr>" for r in rows)
        out.append(f"<details><summary>{html.escape(name)}</summary><div class='tw'><table><thead><tr>"
                   + "".join(f"<th>{c}</th>" for c in cols) + f"</tr></thead><tbody>{body}</tbody></table></div></details>")
    return "\n".join(out)


# ---------- the gallery of kinds ----------

def bars(title, subtitle, groups, series, pct=False, ylabel=None):
    """Grouped bars: one group per world, one bar per measure."""
    fig, ax = plt.subplots(figsize=(6.4, 2.6))
    n = len(series)
    width = 0.8 / n
    for i, (label, values, slot) in enumerate(series):
        xs = [x - 0.4 + width * (i + 0.5) for x in range(len(groups))]
        ax.bar(xs, values, width=width * 0.9, color=SERIES[slot], label=label)
    ax.set_xticks(range(len(groups)))
    ax.set_xticklabels(groups)
    if ylabel:
        ax.set_xlabel(ylabel, loc="right")
    ax.yaxis.set_major_formatter((lambda y, _p: f"{y:.0%}") if pct else kfmt)
    ax.yaxis.set_major_locator(MaxNLocator(4))
    legend_above(ax, n)
    return figure(title, subtitle, to_svg(fig))


def gallery(picks, caption, n=2):
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
{int(float(r['born_size']))} blocks, {float(r['hard']):.0%} hard, {float(r['open_born']):.2f} open faces a block<br>
{where[1]:.0%} on the {where[0]}, wood {float(r['wood']):.0%} of its food, walks {float(r['travel']):.1f} cells</figcaption></figure>""")
    return f"""<figure class="diagram"><div class="cards">{"".join(cards)}</div>
<figcaption>Figure {n}. {html.escape(caption)}</figcaption></figure>"""




# ---------- page ----------

# A report is dark only (the user, 2026-09-16).
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

DIAGRAM = """
<figure class="diagram">
<svg viewBox="0 78 740 184" role="img" aria-label="A break takes one block; the tear takes a share of what the prey holds; under the frail line the prey dies and lies as carrion" style="max-width:100%;height:auto;display:block">
<defs><marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="currentColor"/></marker></defs>
<g fill="none" stroke="currentColor" stroke-width="1.2" font-size="12" font-family="system-ui, sans-serif">
  <rect x="24" y="92" width="150" height="62" rx="6"/>
  <text x="99" y="118" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">a body with a gut</text>
  <text x="99" y="136" text-anchor="middle" fill="currentColor" stroke="none">presses forward</text>

  <rect x="300" y="92" width="170" height="62" rx="6"/>
  <text x="385" y="112" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">the prey</text>
  <text x="385" y="130" text-anchor="middle" fill="currentColor" stroke="none">35 blocks, holds 8.3</text>
  <text x="385" y="147" text-anchor="middle" fill="currentColor" stroke="none">in energy and fat</text>

  <line x1="174" y1="108" x2="298" y2="108" marker-end="url(#arr)"/>
  <text x="236" y="100" text-anchor="middle" fill="currentColor" stroke="none">one block: 0.29</text>
  <line x1="298" y1="138" x2="176" y2="138" marker-end="url(#arr)" stroke="var(--s1)" stroke-width="2"/>
  <text x="237" y="174" text-anchor="middle" fill="var(--s1)" stroke="none">the tear: 0.4 of the 8.3</text>

  <rect x="300" y="196" width="170" height="48" rx="6"/>
  <text x="385" y="216" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">carrion where it fell</text>
  <text x="385" y="234" text-anchor="middle" fill="currentColor" stroke="none">the whole body, at once</text>
  <line x1="385" y1="156" x2="385" y2="194" marker-end="url(#arr)"/>
  <text x="480" y="180" text-anchor="middle" fill="currentColor" stroke="none">the frail line</text>

  <rect x="540" y="92" width="176" height="62" rx="6"/>
  <text x="628" y="112" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">the plants beside them</text>
  <text x="628" y="130" text-anchor="middle" fill="currentColor" stroke="none">0.167 a turn to a body</text>
  <text x="628" y="147" text-anchor="middle" fill="currentColor" stroke="none">that sits and grazes</text>
</g>
</svg>
<figcaption>Figure 1. What a body gains by pressing into another. A break takes one block with its share of the prey's
energy and fat (0.29, about one turn of a full gut's feeding). The tear adds a share of everything the prey still
holds. Under the frail line a prey that has lost enough blocks dies and its whole store lies in the cell, for
whoever stands there. The plants are what all of it has to beat.</figcaption>
</figure>
"""


WORLDS = [("control", "y3e-5h3", 0), ("the tear 0.4", "tear", 1), ("the set 0.15/0.75", "set", 2), ("both 0.4/0.5", "both", 3)]
SEEDS = (9, 10, 11)


def pre_of(suf, seed):
    d = E073 if suf == "y3e-5h3" else LADDER
    return os.path.join(d, f"c1225_life{seed}_{suf}")


def half_of(rows):
    return [r for r in rows if int(r["step"]) >= int(rows[-1]["step"]) / 2]


def world_stats():
    """Per world, the mean over the three seeds of what the report shows."""
    s = sweep()
    out = {}
    for label, suf, slot in WORLDS:
        v = {}
        for seed in SEEDS:
            rows = log_of(pre_of(suf, seed))
            h = half_of(rows)
            m = lambda k: st.mean(float(r[k]) for r in h)  # noqa: E731
            w = s[f"life{seed}_{suf}"]
            causes = ("hunger", "broken", "wear", "thirst", "suffocation", "cold", "wound")
            tot = sum(st.mean(float(r.get(f"deaths_{c}", 0)) for r in h) for c in causes)
            for k, x in [("gain", m("kill_gain")), ("kills", float(w["kills"])), ("tear", float(w["tear"])),
                         ("kinds", float(w["kinds_at"])), ("placed", float(w["placed_at"])), ("hunt", float(w["by_kills"]) > 0),
                         ("topk", float(w["top_kills"])), ("pop", m("pop")), ("size", m("size_mean")),
                         ("hard", m("hard_mean") / m("size_mean")), ("age", m("age_death_p50")), ("ms", m("ms_step")),
                         ("bottom", m("pop_bottom"))] + [(c, st.mean(float(r.get(f"deaths_{c}", 0)) for r in h) / tot) for c in causes]:
                v.setdefault(k, []).append(x)
        out[label] = {k: (sum(x) if k == "hunt" else st.mean(x)) for k, x in v.items()}
    return out


def main():
    W = world_stats()
    logs = {label: log_of(pre_of(suf, 9)) for label, suf, _ in WORLDS}
    xs = [float(r["step"]) for r in logs["control"]]
    charts = []

    charts.append(line_chart(
        "The flesh of the living, as a share of what the world eats",
        "Seed 9, per 1,000 steps. e060 calls a world a hunter world over 25%. The control never gets there.",
        xs, [(label, [a / max(b + c, 1e-9) for a, b, c in
                      zip(kills_col(logs[label]), col(logs[label], "plant_intake"), col(logs[label], "meat_intake"))], slot)
             for label, _, slot in WORLDS], pct=True))

    charts.append(line_chart(
        "What one break gives its breaker",
        "Seed 9, matter per block broken, in a body's units. A full gut takes 0.32 a turn, so 0.30 is one turn of grazing.",
        xs, [(label, col(logs[label], "kill_gain"), slot) for label, _, slot in WORLDS]))

    charts.append(bars(
        "Kinds at a census, and the kinds kept to one medium",
        "Mean of three seeds. Left bar: kinds holding 5% of the grown bodies at a census. Right: those of them that keep 90% of their bodies to the land, the surface or the bottom.",
        [l for l, _, _ in WORLDS],
        [("kinds at a census", [W[l]["kinds"] for l, _, _ in WORLDS], 0),
         ("kept to a medium", [W[l]["placed"] for l, _, _ in WORLDS], 4)]))

    charts.append(bars(
        "What kills a body",
        "Mean of three seeds, share of the deaths. 'wound' is a body under the frail line; 'broken' is one taken to its last block.",
        [l for l, _, _ in WORLDS],
        [("thirst", [W[l]["thirst"] for l, _, _ in WORLDS], 0),
         ("hunger", [W[l]["hunger"] for l, _, _ in WORLDS], 1),
         ("wound", [W[l]["wound"] for l, _, _ in WORLDS], 2),
         ("broken", [W[l]["broken"] for l, _, _ in WORLDS], 3)], pct=True))

    charts.append(line_chart(
        "The crowd", "Seed 9, bodies alive. The set holds more bodies than the control, not fewer.",
        xs, [(label, col(logs[label], "pop"), slot) for label, _, slot in WORLDS], ymin=0))

    charts.append(line_chart(
        "The body the world settles on", "Seed 9, blocks per body. Under the tear a body is smaller: a big body is a meal.",
        xs, [(label, col(logs[label], "size_mean"), slot) for label, _, slot in WORLDS], ymin=0))

    # The gallery: the biggest land kind of the control and of the kept set, and a flesh kind.
    kinds_rows = rows_of(os.path.join(HERE, "results", "kinds.csv"))
    def pick(run, key):
        rs = [r for r in kinds_rows if r["run"] == run]
        return max(rs, key=key)
    picks = [pick("life9_y3e-5h3", lambda r: float(r["share"]) * (float(r["land"]) > 0.8)),
             pick("life9_both", lambda r: float(r["share"]) * (float(r["land"]) > 0.8)),
             pick("life9_both", lambda r: float(r["share"]) * (float(r["kills"]) > 0.5)),
             pick("life9_both", lambda r: float(r["share"]) * (float(r["bottom"]) > 0.8))]
    gal = gallery(picks, "Four birth bodies: the control's browser, the set's hunting browser, a flesh eater of "
                         "the shore, a bottom feeder. Blue hard, orange muscle, aqua gut, yellow sensor.", n=2)

    def row(label):
        w = W[label]
        return (f"<tr><td>{html.escape(label)}</td><td>{w['gain']:.2f}</td><td>{w['kills']:.0%}</td><td>{w['tear']:.0%}</td>"
                f"<td>{w['kinds']:.2f}</td><td>{w['placed']:.2f}</td><td>{w['hunt']:.0f} of 3</td><td>{w['topk']:.0%}</td>"
                f"<td>{w['pop']:,.0f}</td><td>{w['size']:.1f}</td><td>{w['hard']:.1%}</td><td>{w['age']:.0f}</td><td>{w['ms']:.1f}</td></tr>")
    table = "".join(row(l) for l, _, _ in WORLDS)

    tables = data_table(["step", "pop", "kill_intake", "flesh_intake", "plant_intake", "meat_intake", "kill_gain",
                         "deaths_wound", "deaths_broken", "deaths_hunger", "cells_broken", "contacts", "size_mean", "blocks_kept"],
                        {f"Seed 9, {l}": [r for i, r in enumerate(logs[l]) if i % 10 == 0] for l, _, _ in WORLDS})

    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>e075 What the flesh of kills needs to pay - Report</title>
<style>{CSS}</style>
</head>
<body>
<main>
<h1>e075: a bite too small to be a meal</h1>
<p class="sub">Experiment report - 2026-09-17 - 11 candidates on one seed, then three worlds on three seeds, 100,000 steps</p>

<section class="tldr">
<h2>TL;DR</h2>
<p>The issue this answers said the world had no predation. It had, at 8-13%: the 0% was a per-block
gain read as a total. What the world could not do was take a meal - one break is 2.9% of a prey. Two
laws fix that together: a gut that tears a body takes a share of what it holds, and a body dies of
its wounds. Then a quarter of the world's food is the flesh of the living and the land's browser
hunts.</p>
</section>

<h2>1. Question</h2>
<p>Nothing in this series has made a second way of living except the flesh of other bodies, and no
kind of stage C lives by it. The dry run said why: a body is worth 9.1 and a break takes 0.29 of it,
one turn of grazing, so a body that hunts eats a third less than one that sits. The cost was never
the barrier - moving costs 0.002 a turn against an upkeep of 0.10.</p>
<ol>
  <li><strong>A kind that lives by killing</strong>, holding 5% of a census, on 2 seeds of 3.</li>
  <li><strong>Stage C's measure does not fall</strong>: 6.61 kinds at a census, 3.89 kept to a place.</li>
  <li><strong>The world stands</strong>: matter conserved, all three media, the control's crowd.</li>
</ol>

<h2>2. The world</h2>
<p>Stage C's default world with two rates, each 0 being that world exactly. <strong>The
tear</strong>: a gut that breaks a block off a body takes with it that share of what the body still
holds - a predator eats through the wound, not the scale it tore off. <strong>The frail line</strong>:
a body dies when its blocks fall under that share of its birth body, and its store lies where it
fell.</p>
{DIAGRAM}
<p><strong>Runs.</strong> Seeds 9-11 on world c1225, 100,000 steps, 45 minutes a run on one core. A
search of 11 candidates on seed 9 at 50,000 steps set the rates; three went to three seeds against
the control. Every 1,000 steps we record:</p>
<ul class="measures">
  <li><strong>the kills' share</strong> - the flesh of living bodies over all that is eaten; the dead are counted apart.</li>
  <li><strong>the gain a break</strong> - matter per block broken.</li>
  <li><strong>kinds at a census</strong> - birth forms holding 5% of the grown bodies, by diet, tooth and roaming.</li>
  <li><strong>kept to a place</strong> - of those, the ones 90% in one medium.</li>
  <li><strong>deaths by cause</strong> - thirst, hunger, wounds, broken to the last block.</li>
  <li><strong>the body</strong> - blocks, the share hard, the median age at death.</li>
</ul>

<h2>3. Results</h2>
<div class="tw"><table>
<thead><tr><th>World</th><th>gain a break</th><th>kills</th><th>of it, the tear</th><th>kinds at a census</th><th>kept to a place</th><th>hunter kinds</th><th>top kind's kills</th><th>bodies</th><th>blocks</th><th>hard</th><th>age at death</th><th>ms a step</th></tr></thead>
<tbody>{table}</tbody></table></div>
<ol class="verdicts">
<li><span class="verdict">Yes</span> A kind that lives by killing: 2 seeds of 3 under both laws (46% on the third), 3 of 3 under the tear alone.</li>
<li><span class="verdict partly">Partly</span> Stage C's measure: it rises under both laws (7.67 and 4.78), but the tear alone drops the kinds kept to a place to 3.56.</li>
<li><span class="verdict">Yes</span> The world stands: matter to 6.0e-14, all three media in all 12 runs, and 9,099 bodies against 8,433.</li>
</ol>

<h3>3.1 The tear makes flesh a food; the frail line alone takes it away</h3>
<div class="grid2">
{charts[0]}
{charts[1]}
</div>
<p>A break is worth 0.30 in the control and 1.01 with both laws, and 88% of that is the tear. The
frail line on its own lowers the kills' share below the control: the prey dies before it is eaten and
its store lies in the cell for whoever stands there, which is usually a body that does not hunt.</p>

<h3>3.2 Only the pair raises both of stage C's numbers</h3>
<div class="grid2">
{charts[2]}
{charts[3]}
</div>
<p>The tear alone buys the flesh and loses the place; the frail line alone holds the place and leaves
the kills at 19%. Together the kinds at a census go to 7.67 and those kept to a medium to 4.78, above
the control on every seed. Wounds take 12.7% of the deaths, and the deaths from being taken to the
last block nearly stop.</p>

<h3>3.3 The world that comes out is fuller and made of smaller bodies</h3>
<div class="grid2">
{charts[4]}
{charts[5]}
</div>
<p>A big body is now a meal, and the bodies settle 20% smaller (28.1 blocks against 34.9) with more
hard blocks (9.9% against 7.3%) and shorter lives (78 steps against 91). The crowd is larger, and a
third more of it lives on the bottom.</p>

<h3>3.4 The land's browser hunts</h3>
{gal}
<p>A blue block resists a break three times over on the face it shows, and an orange one is the force
behind it. Under the control the biggest land kind takes 24-34% of its food from the crowns and 9-19%
from kills; under the two laws the same shape takes 46-52% from kills and 15-24% from wood. Pure
flesh eaters stay at 2-4% of the grown bodies.</p>

<h2>4. Discussion</h2>
<p>The question was set by a number that was wrong. "Kills are 0.0%" came from dividing a per-block
gain by the intake; the world had been eating the living at 8-13% since e072. What was missing was
not the price of hunting but the size of the mouthful: a prey was 35 mouthfuls that walked away
between them, and a body that chased them ate a third less than one that sat on grass.</p>
<p>The two laws are one mechanism read from opposite ends. The tear says what a wound gives the body
that made it; the frail line says what a wound costs the body that took it. Each alone moves one of
stage C's two numbers and spoils the other, which is what #87 asked the search to look for: a law is
kept as a set or not at all.</p>
<p>What this does not show: the rates between 0.15 and 0.4 were never run on three seeds, so 0.4 is
where the region was entered, not its centre. Nor whether the hunter and the browser invade each
other - e074's instrument is in this crate for that. A pure carnivore still holds 4% of this
crowd.</p>

<h2>5. Conclusion and next step</h2>
<p>Kept as a set: a tear of 0.4 with a frail line of 0.5 is stage C's default world from here. The
next step is #72's paired invasion on the pair that is now far apart - the hunting browser and the
shore's grazer - and then #91, whether a standing forest is a refuge a lawn cannot hold.</p>

<h2>Appendix: data</h2>
<p>Every tenth logged row of seed 9, one table per world; the full data is in <code>results/</code>
(<code>ladder/</code> the three worlds, <code>search/</code> the 11 candidates, <code>sweep.csv</code>
and <code>kinds.csv</code> what the tables read). Build this report with
<code>uv run python experiments/e075_hunt/report.py</code>.</p>
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
