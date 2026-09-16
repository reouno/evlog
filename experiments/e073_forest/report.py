#!/usr/bin/env python3
"""Build report.html for e073 (#89, the crown's yield and a cold that differs by place).

Charts: matplotlib, exported as SVG and inlined. Diagram: hand-written SVG.
Run from the repo root: uv run python experiments/e073_forest/report.py
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
E072 = os.path.join(ROOT, "experiments", "e072_balance", "results")
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


def rate_chart(title, subtitle, groups, series, ylabel, pct=False):
    """A ladder: one point per wood_yield rate, drawn against an even x so 0 has a place."""
    fig, ax = plt.subplots(figsize=(6.4, 2.6))
    xs = range(len(groups))
    for label, values, slot in series:
        ax.plot(list(xs), values, color=SERIES[slot], marker="o", markersize=5, linewidth=1.6, label=label)
    ax.set_xticks(list(xs))
    ax.set_xticklabels(groups)
    ax.set_xlabel(ylabel, loc="right")
    ax.set_ylim(0, max(v for _, vs, _ in series for v in vs) * 1.2)
    ax.yaxis.set_major_formatter((lambda y, _p: f"{y:.0%}") if pct else kfmt)
    ax.yaxis.set_major_locator(MaxNLocator(4))
    ax.margins(x=0.06)
    legend_above(ax, len(series))
    return figure(title, subtitle, to_svg(fig))


def point_chart(title, subtitle, points, xlabel, ylabel):
    """points: (label, x, y, slot). Four worlds placed by what their heat costs and what they hold."""
    fig, ax = plt.subplots(figsize=(6.4, 2.6))
    for label, x, y, slot in points:
        ax.plot([x], [y], marker="o", markersize=8, color=SERIES[slot], linestyle="none", label=label)
    ax.set_xlabel(xlabel, loc="right")
    ax.set_ylabel(ylabel)
    ax.set_xlim(0, max(p[1] for p in points) * 1.25)
    ax.set_ylim(0, max(p[2] for p in points) * 1.3)
    ax.yaxis.set_major_locator(MaxNLocator(4))
    legend_above(ax, 2)
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
{int(float(r['born_size']))} blocks, {float(r['hard']):.0%} hard, {float(r['open_born']):.2f} open faces a block<br>
{where[1]:.0%} on the {where[0]}, wood {float(r['wood']):.0%} of its food, walks {float(r['travel']):.1f} cells</figcaption></figure>""")
    return f"""<figure class="diagram"><div class="cards">{"".join(cards)}</div>
<figcaption>Figure 2. {html.escape(caption)}</figcaption></figure>"""


# ---------- page ----------

CSS = f"""
:root {{
  --surface: #fcfcfb; --page: #f9f9f7; --ink: #0b0b0b; --ink2: #52514e; --grid: #e1e0d9; --border: rgba(11,11,11,0.10);
  --s1: {SERIES[0]};
}}
@media (prefers-color-scheme: dark) {{
  :root:not([data-theme="light"]) {{
    --surface: #1a1a19; --page: #0d0d0d; --ink: #ffffff; --ink2: #c3c2b7; --grid: #2c2c2a; --border: rgba(255,255,255,0.10);
    --s1: #3987e5;
  }}
}}
:root[data-theme="dark"] {{
  --surface: #1a1a19; --page: #0d0d0d; --ink: #ffffff; --ink2: #c3c2b7; --grid: #2c2c2a; --border: rgba(255,255,255,0.10);
  --s1: #3987e5;
}}
* {{ box-sizing: border-box; }}
body {{ margin: 0; background: var(--page); color: var(--ink); font: 15px/1.55 system-ui, -apple-system, "Segoe UI", sans-serif; }}
main {{ max-width: 960px; margin: 0 auto; padding: 32px 20px 64px; }}
h1 {{ font-size: 26px; margin: 0 0 4px; }}
h2 {{ font-size: 19px; margin: 40px 0 8px; }}
h3 {{ font-size: 16px; margin: 24px 0 8px; }}
p, li {{ color: var(--ink); max-width: 72ch; }}
.sub {{ color: var(--ink2); margin: 0 0 24px; }}
.tldr {{ background: var(--surface); border: 1px solid var(--border); border-left: 4px solid var(--s1); border-radius: 8px; padding: 12px 18px; }}
.tldr h2 {{ margin: 0 0 6px; font-size: 15px; }}
.tldr p {{ margin: 0; }}
.grid2 {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(420px, 1fr)); gap: 20px; }}
.grid2 > .fig:only-child {{ max-width: 470px; }}
.fig {{ margin: 0; background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 14px 14px 8px; }}
.fig svg {{ width: 100%; height: auto; display: block; font-family: system-ui, -apple-system, "Segoe UI", sans-serif; }}
figcaption strong {{ display: block; font-size: 15px; }}
figcaption span {{ display: block; color: var(--ink2); font-size: 13px; min-height: 2.6em; margin-bottom: 6px; }}
.diagram {{ margin: 12px 0; background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 12px 16px 8px; color: var(--ink); }}
.diagram figcaption {{ color: var(--ink2); font-size: 13px; margin-top: 4px; }}
.cards {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); gap: 16px; }}
.card {{ margin: 0; display: flex; gap: 12px; align-items: flex-start; }}
.card figcaption {{ font-size: 12px; color: var(--ink2); }}
.card figcaption strong {{ color: var(--ink); font-size: 12.5px; }}
.measures {{ columns: 2; column-gap: 24px; max-width: none; padding-left: 20px; }} .measures li {{ break-inside: avoid; }}
table {{ border-collapse: collapse; font-size: 13.5px; font-variant-numeric: tabular-nums; }}
th, td {{ padding: 6px 12px; text-align: right; border-bottom: 1px solid var(--grid); }}
th:first-child, td:first-child {{ text-align: left; }}
th {{ color: var(--ink2); font-weight: 600; }}
.tw {{ overflow-x: auto; }}
details {{ margin: 8px 0; }} summary {{ cursor: pointer; color: var(--ink2); }}
.verdicts {{ list-style: none; padding: 0; margin: 12px 0 0; }} .verdicts li {{ margin: 4px 0; }}
.verdict {{ display: inline-block; padding: 1px 8px; border-radius: 4px; font-size: 12.5px; font-weight: 600; background: rgba(12,163,12,0.12); color: #006300; }}
.verdict.no {{ background: rgba(208,59,59,0.12); color: #a12b2b; }}
.verdict.partly {{ background: rgba(250,178,25,0.15); color: #8a5a00; }}
:root[data-theme="dark"] .verdict.partly {{ color: #fab219; }}
@media (prefers-color-scheme: dark) {{ :root:not([data-theme="light"]) .verdict.partly {{ color: #fab219; }} }}
:root[data-theme="dark"] .verdict {{ color: #0ca30c; }} :root[data-theme="dark"] .verdict.no {{ color: #e66767; }}
@media (prefers-color-scheme: dark) {{ :root:not([data-theme="light"]) .verdict {{ color: #0ca30c; }} :root:not([data-theme="light"]) .verdict.no {{ color: #e66767; }} }}
"""

DIAGRAM = """
<figure class="diagram">
<svg viewBox="0 0 740 286" role="img" aria-label="A stand of wood turns soil into a trunk and, beside it, into browse a body can take" style="max-width:100%;height:auto;display:block">
<defs><marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="currentColor"/></marker></defs>
<g fill="none" stroke="currentColor" stroke-width="1.2" font-size="12" font-family="system-ui, sans-serif">
  <rect x="24" y="112" width="120" height="56" rx="6"/>
  <text x="84" y="136" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">soil</text>
  <text x="84" y="154" text-anchor="middle" fill="currentColor" stroke="none">7.1 a cell</text>

  <rect x="262" y="24" width="180" height="56" rx="6"/>
  <text x="352" y="48" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">standing wood</text>
  <text x="352" y="66" text-anchor="middle" fill="currentColor" stroke="none">0.6 a cell, lives 20,000</text>

  <rect x="262" y="196" width="180" height="56" rx="6" stroke="var(--s1)" stroke-width="2"/>
  <text x="352" y="220" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">browse</text>
  <text x="352" y="238" text-anchor="middle" fill="currentColor" stroke="none">0.02 a cell, eaten as it falls</text>

  <rect x="540" y="112" width="176" height="56" rx="6"/>
  <text x="628" y="136" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">a body with a tooth</text>
  <text x="628" y="154" text-anchor="middle" fill="currentColor" stroke="none">force 2 behind a hard tip</text>

  <line x1="146" y1="126" x2="258" y2="60" marker-end="url(#arr)"/>
  <text x="150" y="48" text-anchor="middle" fill="currentColor" stroke="none">grows, capped by its shade</text>

  <line x1="146" y1="154" x2="258" y2="214" marker-end="url(#arr)" stroke="var(--s1)"/>
  <text x="186" y="208" text-anchor="middle" fill="currentColor" stroke="none">drops, from the same soil</text>

  <line x1="352" y1="84" x2="352" y2="192" marker-end="url(#arr)" stroke-dasharray="4 3" stroke="var(--s1)"/>
  <text x="366" y="142" text-anchor="start" fill="currentColor" stroke="none">the stand sets the rate</text>

  <line x1="446" y1="214" x2="536" y2="156" marker-end="url(#arr)"/>
  <text x="488" y="212" text-anchor="middle" fill="currentColor" stroke="none">eaten</text>

  <polyline points="258,244 100,244 100,174" marker-end="url(#arr)" stroke-dasharray="4 3"/>
  <text x="186" y="262" text-anchor="middle" fill="currentColor" stroke="none">uneaten, it rots back</text>
</g>
</svg>
<figcaption>Figure 1. e072 let a gut bite a share of the standing wood, and the forest was eaten out in 12,000 steps. Here the
stand drops browse instead, at a rate per unit of what it stands, taken from the same soil the trunk grows out of. The
trunk itself is never touched, so the stand keeps its shade and keeps yielding.</figcaption>
</figure>
"""


def main():
    s = sweep()
    ladder = [("0", [f"life{x}_sets" for x in SEEDS]),
              ("3e-5", [f"life{x}_y3e-5h3" for x in SEEDS]),
              ("1e-4", [f"life{x}_y1e-4" for x in SEEDS]),
              ("3e-4", [f"life{x}_yield" for x in SEEDS])]
    groups = [g for g, _ in ladder]
    get = lambda key: [mean_of(s, ns, key) for _, ns in ladder]  # noqa: E731

    charts = []
    # 3.1 the stand
    xs = col(log_of(os.path.join(E072, "c1225_life9_sets")), "step")
    stand = [("e072: a share of the stock", col(log_of(os.path.join(E072, "c1225_life9_sets")), "wood", 1 / LAND), 1),
             ("e073: the crown's yield", col(log_of(os.path.join(HERE, "results/ladder/c1225_life9_y3e-5")), "wood", 1 / LAND), 0)]
    charts.append(line_chart("The forest stands, or it does not", "Standing wood on a land cell, seed 9. Flat means the stand pays its own death; a fall to zero means it was eaten.", xs, stand, ymin=0))
    charts.append(line_chart("What the crowns hold", "Browse waiting on a land cell under the kept rate, seed 9, and the grass beside it. Zero would mean the bodies take it as fast as it falls.",
                             xs, [("browse", col(log_of(os.path.join(HERE, "results/ladder/c1225_life9_y3e-5")), "browse", 1 / LAND), 0),
                                  ("grass", col(log_of(os.path.join(HERE, "results/ladder/c1225_life9_y3e-5")), "grass", 1 / LAND), 2)], ymin=0))
    # 3.2 the rate decides
    charts.append(rate_chart("A rich flow makes one winner", "The largest kind's share of the grown bodies, mean of three seeds. Higher means the world is one animal.",
                             groups, [("largest kind", get("top_kind"), 1)], "wood_yield", pct=True))
    charts.append(rate_chart("And it costs the rest", "Kinds present at a census, and those keeping 90% of their bodies to one medium. The controls are the left-hand points.",
                             groups, [("kinds at a census", get("kinds_at"), 0), ("of them, kept to a place", get("placed_at"), 2)], "wood_yield"))
    charts.append(rate_chart("A thin patchy food is walked to", "Cells a body crosses in a life, median over the grown. The control walks 3.5; a food rich everywhere is sat on.",
                             groups, [("cells a life", get("travel"), 3)], "wood_yield"))
    charts.append(rate_chart("What wood feeds", "Browse as a share of everything eaten, and the tooth's share of the grown bodies. At zero, wood was 0.1% of the food.",
                             groups, [("browse of all food", get("browse_share"), 0), ("bodies with a tooth", get("tooth"), 1)], "wood_yield", pct=True))
    # 3.3 the cold
    charts.append(point_chart("The day's mean is a smaller tax, not a place",
                              "Seed 9 at 50,000 steps. If the mean were a place and not a discount, its point would sit above the heat that costs the same.",
                              [("the default (heat 0.09)", float(s["life9_ctrl50"]["warm_land"]), float(s["life9_ctrl50"]["kinds_at"]), 1),
                               ("day_temp 1", float(s["life9_d00"]["warm_land"]), float(s["life9_d00"]["kinds_at"]), 0),
                               ("heat 0.045, read at the moment", float(s["life9_heat0.045"]["warm_land"]), float(s["life9_heat0.045"]["kinds_at"]), 2),
                               ("heat 0.02, read at the moment", float(s["life9_heat0.02"]["warm_land"]), float(s["life9_heat0.02"]["kinds_at"]), 3)],
                              "warming paid a 1,000 steps", "kinds at a census"))
    # 3.4 the world stands
    pop = [(f"seed {x}", col(log_of(os.path.join(HERE, f"results/ladder/c1225_life{x}_y3e-5h3")), "pop"), i) for i, x in enumerate(SEEDS)]
    cut_path = os.path.join(HERE, "results/ladder/c1225_life9_y3e-5cut")
    cut = log_of(cut_path) if os.path.exists(cut_path + "_log.csv") else None
    if cut and len(cut) == len(pop[0][1]):
        pop.append(("seed 9, largest lineage halved at 50k", col(cut, "pop"), 4))
    charts.append(line_chart("The world stands under the kept rate", "Bodies alive, every 1,000 steps. The cut run loses half of its largest lineage at step 50,000.",
                             col(log_of(os.path.join(HERE, "results/ladder/c1225_life9_y3e-5")), "step"), pop, ymin=0))

    # the gallery: the kinds the kept rate holds, against the control's
    kinds_rows = rows_of(os.path.join(HERE, "results", "kinds.csv"))
    want = [("life9_sets", 1), ("life10_sets", 1), ("life10_y3e-5h3", 2), ("life11_y3e-5h3", 1), ("life9_yield", 2)]
    picks = []
    for run, n in want:
        rs = [r for r in kinds_rows if r["run"] == run and r["held"] == "True"]
        rs.sort(key=lambda r: -float(r["wood"]))
        picks += rs[:n]
    gal = gallery(picks[:8], "The commonest birth body of kinds held at every census. Blue: hard, orange: muscle, yellow: sensor, green: gut. "
                             "The default world's kinds (life*_sets) carry no tooth and eat no wood; the kept rate's (life*_y3e-5h3) carry one and walk "
                             "the farthest of any kind stage C has held; the richest rate's (life9_yield) fills the world and stops walking.")

    rows = [("kinds at a census", "kinds_at", "{:.2f}"), ("of them, kept to a place", "placed_at", "{:.2f}"),
            ("kinds held at every census", "kinds_held", "{:.2f}"), ("the leanest census of six", "lean", "{:.2f}"),
            ("largest kind's share", "top_kind", "{:.0%}"), ("kinds living by wood (of 3 seeds)", "by_wood", "{:.2f}"),
            ("kinds kept to a band off the world's", "off_band", "{:.2f}"), ("cells a body walks in a life", "travel", "{:.2f}"),
            ("bodies alive", "pop", "{:.0f}"), ("of them on land", "pop_land", "{:.0f}"),
            ("standing wood a land cell", "wood_stand", "{:.3f}"), ("browse a land cell", "browse_stand", "{:.3f}"),
            ("browse of all food", "browse_share", "{:.1%}"), ("bodies with a tooth", "tooth", "{:.0%}"),
            ("open soft faces a block, on land", "open_land", "{:.2f}")]
    arms = [("control (e072)", [f"life{x}_sets" for x in SEEDS]),
            ("wood_yield 3e-5", [f"life{x}_y3e-5h3" for x in SEEDS]),
            ("wood_yield 3e-4", [f"life{x}_yield" for x in SEEDS]),
            ("day_temp 1", [f"life{x}_cold" for x in SEEDS])]
    head = "".join(f"<th>{html.escape(a)}</th>" for a, _ in arms)
    body = "".join("<tr><td>" + html.escape(label) + "</td>"
                   + "".join(f"<td>{fmt.format(mean_of(s, ns, key))}</td>" for _, ns in arms) + "</tr>"
                   for label, key, fmt in rows)

    tables = data_table(["name", "day_temp", "wood_yield", "wood_food", "wood_hard", "kinds_at", "placed_at", "kinds_held",
                         "top_kind", "travel", "by_wood", "off_band", "pop", "browse_share", "wood_stand", "tooth"],
                        {"Every run of e073, and e072's three controls": sorted(s.values(), key=lambda r: r["name"])})

    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>e073 The crown's yield - Report</title>
<style>{CSS}</style>
</head>
<body>
<main>
<h1>e073: wood a body can live on, and a cold that differs by place</h1>
<p class="sub">Experiment report - 2026-09-16 - 31 runs on c1225, seeds 9-11, stage C's default world</p>

<section class="tldr">
<h2>TL;DR</h2>
<p>A stand of wood now drops browse and keeps its trunk, so wood becomes a living: a land kind takes a third of its
food from it. The rate decides the world. Rich, and one browser holds 61% of the bodies and sits still; thin, and the
world holds more kinds than the control (6.61 against 5.78), more of them kept to a place, and its bodies walk 6.1
cells in a life against 3.5. The thin rate is kept. Reading the temperature as a day's mean is not: it buys nothing a
smaller heat does not.</p>
</section>

<h2>1. Question</h2>
<p>e072 built seven laws together and kept them as stage C's default world. Two of them did nothing there. Wood was
0.0-0.3% of what any kind ate, and the heat never parted the temperature bands, because it reads a cell's
temperature at the moment and a day swings a land cell about 20 C around its own mean. This experiment rebuilds
both and searches them together.</p>
<ol>
  <li><strong>A kind lives by wood.</strong> Some rate holds a kind taking a fifth or more of its food from wood, and
  that kind keeps to the land.</li>
  <li><strong>A kind keeps to a temperature band that is not the world's own.</strong> 82% of the bodies stand in the
  hot band, so keeping to <em>that</em> counts for nothing.</li>
  <li><strong>The two need each other.</strong> Each law holds more kinds with the other than alone.</li>
</ol>

<h2>2. The world</h2>
<p>Arithmetic ruled out both shapes first. The whole standing forest is 1,800 steps of food for the world, once. And
a stand holds only where its growth answers its death, so the share of its growth it can give up before it falls is
exactly its own shade: 1,300 a 1,000 steps over the whole land, against the 37,000 the bodies eat. So the yield is
built as a third thing.</p>
{DIAGRAM}
<p>The second law keeps a running mean of each cell's temperature over the last day, which the body's heat reads
instead of the moment. By that mean 37% of the land is never cold; by the moment, every land cell is cold between a
third and three quarters of the year.</p>
<p><strong>Runs.</strong> 11 combinations on seed 9 at 50,000 steps; then, on seeds 9-11 at 100,000 steps, the two
laws apart and together, a ladder over the yield's rate, two probes with a weaker heat, and one stability cut. With
both rates 0 the first 10,000 steps equal e072's run in every shared column and row. We measure:</p>
<ul class="measures">
  <li><strong>Kinds at a census</strong> - ways of living holding 5% of the grown bodies (stage C's measure).</li>
  <li><strong>Kept to a place</strong> - of those, the ones 90% in one medium.</li>
  <li><strong>Largest kind's share</strong> - high means one kind holds the world.</li>
  <li><strong>Browse of all food</strong> - zero means the law feeds nobody.</li>
  <li><strong>Standing wood a cell</strong> - zero means the forest was eaten.</li>
  <li><strong>Cells walked in a life</strong> - median over the grown.</li>
  <li><strong>Warming paid</strong> - what the heat costs the land.</li>
</ul>

<h2>3. Results</h2>
<div class="tw"><table>
<thead><tr><th>Mean of seeds 9-11</th>{head}</tr></thead>
<tbody>{body}</tbody></table></div>
<ol class="verdicts">
<li><span class="verdict">Yes</span> A kind lives by wood: at 3e-5 every seed holds a land kind with a tooth taking
24-34% of its food from it, and on two of the three that kind roams.</li>
<li><span class="verdict no">No</span> No kind anywhere keeps to a band off the world's own; the cold band holds 2-3% of
the bodies in all 31 runs.</li>
<li><span class="verdict partly">Partly</span> The cold lifts the rich yield's kinds from 3.11 to 4.28 at a census, but
the thin yield needs no help and the cold alone is matched by a smaller heat.</li>
</ol>

<h3>3.1 The forest stands under a flow and falls under a bite</h3>
<div class="grid2">
{charts[0]}
{charts[1]}
</div>
<p>The stand a body bites is gone before the run has settled, and what grows back is a tenth of it. The stand that
drops a flow is untouched at 0.60 a cell, and the browse waiting on a cell settles at a tenth of the grass: the
bodies take it about as fast as it falls, which is what a living means.</p>

<h3>3.2 The rate decides whether the food is walked to or sat on</h3>
<div class="grid2">
{charts[2]}
{charts[3]}
{charts[4]}
{charts[5]}
</div>
<p>Wood is patchy: averaged over the six cells a body crosses in a life it still spreads twice its own mean, where
the grass spreads 0.7. A thin yield is therefore a reason to leave, and at 3e-5 the bodies walk 6.1 cells against the
control's 3.5 while no kind holds more of the world than the control's largest. Make the same food rich and the
patches touch: one browser holds 61%, walks 1.2 cells, and the kinds halve.</p>

<h3>3.3 The day's mean buys nothing a smaller heat does not</h3>
<div class="grid2">
{charts[6]}
{charts[7]}
</div>
<p>Reading the day's mean lowers what the land pays to warm itself from 0.090 to 0.016 and the deaths by cold from
3.0% to 0.7%. A plain heat of 0.045 read at the moment pays 0.019 and holds the same kinds. Over 100,000 steps the
mean also re-opens the land's bodies, from 0.64 open faces a block to 0.81, undoing the closing e072 bought.</p>

{gal}

<h2>4. Discussion</h2>
<p>The lesson is about rates, not about wood. Stage C has been adding laws that differ by place and watching the
crowd average them away. A food that differs by place does part the crowd - but only while it is thin enough that
one cell cannot keep a body. The same law at ten times the rate is a subsidy, and a subsidy has one winner.</p>
<p>That the bodies walk is worth its own line. Five experiments have tried to buy movement with a law - a band of
rain, a memory, a stock that returns slowly, a clock that scales with size - and every one of them left the crowd
sitting. A patchy food too thin to live on in one place did it in one run, and nothing in the law mentions
movement.</p>
<p>What this does not show: one world, one terrain, 100,000 steps, and one shape of yield. The rate that works sits
between a twentieth and a fifth of what the world eats, and we have three points on that ladder. Whether a forest
can also be a refuge in a season - the reason the cold was built - is untested, because the cold never became a
place.</p>

<h2>5. Conclusion and next step</h2>
<p><strong>The crown's yield is kept at 3e-5</strong>, with the standing stock no longer edible and the tooth left as
it was: it is the first law of stage C that adds a way of living instead of closing one, and the first that makes the
crowd move. <strong>The
day's mean is not kept</strong>: it is a discount on the heat wearing the clothes of a place. The next question the
cold raised is still open, and now has a tool - a forest that stands through a season a lawn cannot.</p>

<h2>Appendix: data</h2>
<p>Every run's summary is in <code>results/sweep.csv</code> and every kind in <code>results/kinds.csv</code>; the
logs are in <code>results/</code>. Build this report with <code>uv run python experiments/e073_forest/report.py</code>.</p>
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
