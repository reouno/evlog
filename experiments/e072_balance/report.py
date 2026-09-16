#!/usr/bin/env python3
"""Build report.html for e072 (#88, the balance sets built together).

Charts: matplotlib, exported as SVG and inlined. Diagram: hand-written SVG.
Run from the repo root: uv run python experiments/e072_balance/report.py
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
E070 = os.path.join(ROOT, "experiments", "e070_senses", "results")
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4"]  # fixed slot order
KIND_COLOR = {1: SERIES[0], 2: SERIES[1], 3: SERIES[3], 4: SERIES[2]}  # hard, muscle, sensor, gut
SEEDS = (9, 10, 11)

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
    with open(path) as f:
        return list(csv.DictReader(f))


def log_of(name, seed):
    pre = os.path.join(E070, f"c1225_life{seed}_senses") if name == "control" else os.path.join(HERE, "results", f"c1225_life{seed}_{name}")
    return rows_of(pre + "_log.csv")


def col(rows, key):
    return [float(r[key]) for r in rows]


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


def line_chart(title, subtitle, xs, series, ymin=None, xlabel="step", pct=False):
    fig, ax = new_axes(xlabel)
    for label, ys, slot in series:
        ax.plot(xs, ys, color=SERIES[slot], linewidth=1.6, label=label)
    if ymin is not None:
        ax.set_ylim(ymin, max(v for _, ys, _ in series for v in ys) * 1.12)
    ax.yaxis.set_major_formatter((lambda y, _p: f"{y:.0%}") if pct else kfmt)
    ax.yaxis.set_major_locator(MaxNLocator(4))
    legend_above(ax, len(series))
    return figure(title, subtitle, to_svg(fig))


def bar_chart(title, subtitle, groups, series, ylabel="", pct=False):
    """groups: x labels. series: list of (label, values, slot)."""
    fig, ax = plt.subplots(figsize=(6.4, 2.6))
    n = len(series)
    width = 0.8 / n
    xs = range(len(groups))
    for i, (label, values, slot) in enumerate(series):
        ax.bar([x + (i - (n - 1) / 2) * width for x in xs], values, width=width, color=SERIES[slot], label=label)
    ax.set_xticks(list(xs))
    ax.set_xticklabels(groups)
    ax.set_xlabel(ylabel, loc="right")
    ax.yaxis.set_major_formatter((lambda y, _p: f"{y:.0%}") if pct else kfmt)
    ax.yaxis.set_major_locator(MaxNLocator(4))
    legend_above(ax, n)
    return figure(title, subtitle, to_svg(fig))


def stacked_area(title, subtitle, xs, layers):
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


# ---------- the gallery of kinds ----------

def gallery(kinds):
    """The most common body of the largest kinds, on the grid a body grows on."""
    cards = []
    for r in kinds:
        side, cells = int(r["side"]), r["cells"]
        px = 88 // max(side, 1)
        rects = "".join(
            f'<rect x="{(i % side) * px}" y="{(i // side) * px}" width="{px - 1}" height="{px - 1}" fill="{KIND_COLOR[int(k)]}"/>'
            for i, k in enumerate(cells[: side * side]) if k != "0")
        where = max((("land", float(r["land"])), ("surface", float(r["surface"])), ("bottom", float(r["bottom"]))), key=lambda x: x[1])
        cards.append(f"""<figure class="card"><svg viewBox="-1 -1 89 89" width="104" height="104" role="img" aria-label="{html.escape(r['kind'])}">
<rect x="-1" y="-1" width="89" height="89" fill="var(--grid)"/>{rects}</svg>
<figcaption><strong>{html.escape(r['kind'])}</strong><br>{r['run']}, {float(r['share']):.0%} of the grown bodies<br>
{r['born_size']} blocks, {float(r['open_born']):.2f} open faces a block, {float(r['hard']):.0%} hard<br>
{where[1]:.0%} on the {where[0]}, kills {float(r['kills']):.0%} of its food</figcaption></figure>""")
    return f"""<figure class="diagram"><div class="cards">{"".join(cards)}</div>
<figcaption>Figure 2. The largest kinds' commonest bodies, on the grid a body grows on. Blue: hard, orange: muscle, yellow: sensor,
green: gut. The control's kinds are open and small whatever they do; the sets' land kinds are walled and large, its shore kinds are
not.</figcaption></figure>"""


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
.cards {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(255px, 1fr)); gap: 14px; margin: 6px 0 10px; }}
.card {{ margin: 0; display: flex; gap: 10px; align-items: flex-start; }} .card svg {{ flex: none; }}
.card figcaption {{ font-size: 12.5px; line-height: 1.4; color: var(--ink2); }} .card strong {{ color: var(--ink); font-size: 13px; }}
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
<svg viewBox="0 0 720 268" role="img" aria-label="A body's heat and its water, and why a closed body wins the cold and loses the heat"
     style="max-width:100%;height:auto;display:block">
<defs><marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
<path d="M0,0 L10,5 L0,10 z" fill="currentColor"/></marker></defs>
<g fill="none" stroke="currentColor" stroke-width="1.2" font-size="12" font-family="system-ui, sans-serif">
  <text x="0" y="14" fill="currentColor" stroke="none" font-weight="600">A body of 22 open faces</text>
  <text x="380" y="14" fill="currentColor" stroke="none" font-weight="600">The same body walled in, 6 open faces</text>

  <rect x="40" y="30" width="96" height="70" rx="6"/>
  <text x="88" y="60" text-anchor="middle" fill="currentColor" stroke="none">body 21 C</text>
  <text x="88" y="78" text-anchor="middle" fill="currentColor" stroke="none" font-size="11">upkeep makes +3</text>
  <rect x="420" y="30" width="96" height="70" rx="6" stroke="var(--s1)" stroke-width="2"/>
  <text x="468" y="60" text-anchor="middle" fill="currentColor" stroke="none">body 30 C</text>
  <text x="468" y="78" text-anchor="middle" fill="currentColor" stroke="none" font-size="11">upkeep makes +12</text>

  <line x1="136" y1="48" x2="250" y2="48" marker-end="url(#arr)"/>
  <text x="193" y="41" text-anchor="middle" fill="currentColor" stroke="none" font-size="11">heat out</text>
  <line x1="516" y1="48" x2="612" y2="48" marker-end="url(#arr)"/>
  <text x="564" y="41" text-anchor="middle" fill="currentColor" stroke="none" font-size="11">little heat out</text>

  <rect x="250" y="30" width="96" height="70" rx="6" stroke-dasharray="4 3"/>
  <text x="298" y="70" text-anchor="middle" fill="currentColor" stroke="none">cell 18 C</text>
  <rect x="612" y="30" width="96" height="70" rx="6" stroke-dasharray="4 3"/>
  <text x="660" y="70" text-anchor="middle" fill="currentColor" stroke="none">cell 18 C</text>

  <line x1="88" y1="100" x2="88" y2="150" marker-end="url(#arr)"/>
  <text x="96" y="128" fill="currentColor" stroke="none" font-size="11">under 15 C: pays energy</text>
  <line x1="468" y1="100" x2="468" y2="150" marker-end="url(#arr)"/>
  <text x="476" y="128" fill="currentColor" stroke="none" font-size="11">over 30 C: pays water</text>

  <rect x="20" y="150" width="300" height="46" rx="6"/>
  <text x="170" y="178" text-anchor="middle" fill="currentColor" stroke="none">cold night: 1.7 upkeeps a turn</text>
  <rect x="400" y="150" width="300" height="46" rx="6"/>
  <text x="550" y="178" text-anchor="middle" fill="currentColor" stroke="none">cold night: 0.2 upkeeps a turn</text>
  <rect x="20" y="206" width="300" height="46" rx="6"/>
  <text x="170" y="234" text-anchor="middle" fill="currentColor" stroke="none">hot noon: 1.4x the dry air's water</text>
  <rect x="400" y="206" width="300" height="46" rx="6" stroke="var(--s1)" stroke-width="2"/>
  <text x="550" y="234" text-anchor="middle" fill="currentColor" stroke="none">hot noon: 2.1x, through 6 faces</text>
</g>
</svg>
<figcaption>Figure 1. The heat is what gives the land two sides. A body's own upkeep holds it above the cell it stands on, the more so the
fewer faces it leaves open, and those same faces are how it sheds heat as water. Closing up wins the cold night and loses the hot
noon.</figcaption>
</figure>
"""


def main():
    runs = rows_of(os.path.join(HERE, "results", "runs.csv"))
    media = rows_of(os.path.join(HERE, "results", "media.csv"))
    kinds = rows_of(os.path.join(HERE, "results", "kinds.csv"))
    times = rows_of(os.path.join(HERE, "results", "time.csv"))
    by = {(r["arm"], int(r["seed"])): r for r in runs}

    def arm(a, key):
        return st.mean(float(by[(a, s)][key]) for s in SEEDS)

    charts = []
    # 3.1 kinds at each census, and how evenly the world is held
    census = sorted({int(r["step"]) for r in times if int(r["step"]) >= 50000})
    for a, slot in (("control", 0), ("sets", 1)):
        ys = [st.mean(float(r["kinds"]) for r in times if r["arm"] == a and int(r["step"]) == c and r["kinds"]) for c in census]
        charts.append((a, ys))
    charts_html = [line_chart(
        "Kinds of living at each census", "Mean over seeds 9-11 of the ways of living holding 5% of the grown bodies. Flat and equal would mean the sets changed nothing.",
        census, [(name, ys, slot) for (name, ys), slot in zip(charts, (0, 1))], ymin=0)]

    share = []
    for a, slot in (("control", 0), ("sets", 1)):
        share.append((a, [max(float(r["share"]) for r in kinds if r["arm"] == a and int(r["seed"]) == s) for s in SEEDS], slot))
    charts_html.append(bar_chart(
        "The largest kind's share of the world", "Share of the grown bodies in the largest way of living, by seed. Lower is a world no one kind runs.",
        [f"seed {s}" for s in SEEDS], share, pct=True))

    # 3.2 the bodies part by medium
    for key, title, sub, pct in (
        ("open", "Open soft faces per block", "Grown bodies by medium, mean over seeds 9-11. A face with no block beside it dries, breathes and passes heat.", False),
        ("hard", "Hard blocks per block", "The share of a body made of hard blocks, by medium. Hard weighs twice and breathes nothing; it had almost no use in e070.", True)):
        series = [(a, [st.mean(float(r[key]) for r in media if r["arm"] == a and r["medium"] == m) for m in ("land", "surface", "bottom")], slot)
                  for a, slot in (("control", 0), ("sets", 1))]
        charts_html.append(bar_chart(title, sub, ["land", "surface", "bottom"], series, pct=pct))

    # 3.3 where the crowd lives and what kills it
    log_c, log_s = log_of("control", 9), log_of("sets", 9)
    xs = col(log_s, "step")
    charts_html.append(line_chart(
        "Bodies on land", "Seed 9. The sea gives no drink under the sets, so the land carries the crowd it used to share.",
        xs, [("control", col(log_c, "pop_land"), 0), ("sets", col(log_s, "pop_land"), 1)], ymin=0))
    deaths = ["hunger", "thirst", "suffocation", "broken", "cold"]
    tot = [sum(float(r[f"deaths_{d}"]) for d in deaths) or 1 for r in log_s]
    charts_html.append(stacked_area(
        "What kills a body, under the sets", "Seed 9, share of the deaths in each interval. In e070 hunger takes 69% and thirst 26%; nothing dies of cold.",
        xs, [(d, [float(r[f"deaths_{d}"]) / t for r, t in zip(log_s, tot)], i) for i, d in enumerate(deaths[:4])]))

    # 3.4 the cut, and the matter pump
    def lineage_sizes(name, lineage=1136):
        by = {}
        for r in rows_of(os.path.join(HERE, "results", f"c1225_life9_{name}_lineages.csv")):
            if int(r["lineage"]) == lineage:
                by[int(r["step"])] = int(r["size"])
        return by
    cut_l, base_l = lineage_sizes("cut"), lineage_sizes("sets")
    win = [s for s in sorted(set(cut_l) | set(base_l)) if 44000 <= s <= 70000]
    charts_html.append(line_chart(
        "The cut lineage's bodies", "Seed 9. Half of the lineage that held 46% of the world was killed at step 50,000; it is back over the uncut run by 54,000 and then splits.",
        win, [("the cut world", [cut_l.get(s, 0) for s in win], 1), ("the same world uncut", [base_l.get(s, 0) for s in win], 2)], ymin=0))
    charts_html.append(line_chart(
        "The land's soil", "Seed 9, matter in the soil of the land's cells. Rising means the bodies are pumping the sea's matter ashore.",
        xs, [("control", col(log_c, "soil_land"), 0), ("sets", col(log_s, "soil_land"), 1)]))

    # the gallery: the largest kinds of the control and of the sets
    pick = ([r for r in kinds if r["run"] == "control9"][:2] + [r for r in kinds if r["run"] == "sets9"][:3]
            + [r for r in kinds if r["run"] == "sets10"][:2] + [r for r in kinds if r["run"] == "control10"][:1])

    table_rows = [
        ("kinds held at every census (9 / 10 / 11)", lambda a: " / ".join(f"{float(by[(a, s)]['form_held']):.0f}" for s in SEEDS)),
        ("kinds at a census", lambda a: f"{arm(a, 'form'):.2f}"),
        ("the same with the medium shuffled", lambda a: f"{arm(a, 'null_medium'):.2f}"),
        ("kinds keeping 90% of their bodies to one medium", lambda a: " / ".join(f"{float(by[(a, s)]['held_one_medium']):.0f}" for s in SEEDS)),
        ("the largest kind's share", lambda a: f"{max(float(r['share']) for r in kinds if r['arm'] == a):.0%}"),
        ("the largest lineage's share", lambda a: f"{arm(a, 'top_lineage'):.0%}"),
        ("bodies", lambda a: f"{arm(a, 'pop'):,.0f}"),
        ("bodies on land / surface / bottom", lambda a: " / ".join(f"{arm(a, 'pop_' + m):,.0f}" for m in ("land", "surface", "bottom"))),
        ("land bodies: open soft faces per block", lambda a: f"{arm(a, 'land_open'):.2f}"),
        ("land bodies: hard share", lambda a: f"{arm(a, 'land_hard'):.1%}"),
        ("land bodies: blocks", lambda a: f"{arm(a, 'land_blocks'):.1f}"),
        ("land bodies: the store read from the genome", lambda a: f"{arm(a, 'land_store'):.2f}"),
        ("deaths by thirst / by cold", lambda a: f"{arm(a, 'deaths_thirst'):.0%} / {arm(a, 'deaths_cold'):.1%}"),
        ("moves blocked", lambda a: f"{arm(a, 'blocked'):.0%}"),
        ("a step on one core", lambda a: f"{arm(a, 'ms_step'):.1f} ms"),
    ]
    body = "".join(f"<tr><td>{html.escape(name)}</td><td>{f('control')}</td><td>{f('sets')}</td></tr>" for name, f in table_rows)

    appendix = ""
    for name, rs in (("Runs", runs), ("Kinds", kinds), ("By medium", media)):
        cols = list(rs[0])[:14]
        trs = "".join("<tr>" + "".join(f"<td>{html.escape(str(r[c])[:28])}</td>" for c in cols) + "</tr>" for r in rs)
        appendix += (f"<details><summary>{name}</summary><div class='tw'><table><thead><tr>"
                     + "".join(f"<th>{html.escape(c)}</th>" for c in cols) + f"</tr></thead><tbody>{trs}</tbody></table></div></details>")

    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>e072 balance sets - Report</title>
<style>{CSS}</style>
</head>
<body>
<main>
<h1>e072: seven laws at once, instead of one law at a time</h1>
<p class="sub">Experiment report - 2026-09-16 - 22 combinations searched on one seed, then the best on three seeds for 100,000 steps</p>

<section class="tldr">
<h2>TL;DR</h2>
<p>Nine experiments added one law each, and nine times the land's bodies moved one way together. Built as a set, seven counterweights
part the world: the land holds closed, armed, bigger bodies and the water open soft ones, every seed keeps a kind that lives on land
alone, and no kind holds a third of the world. The only measure that did not move is the one the decision rule used, the same kinds held
at every census. The proposal is to keep the sets and judge by the kinds at a census and the kinds kept to a place.</p>
</section>

<h2>1. Question</h2>
<p>A law added alone meets a world without its counterweights. The balance table (<code>balance.md</code>) found four of a body's axes
one-sided: hard blocks have no use, the fat no weight, the blind beat the sighted, the shore is free. Seven laws were built together to
give every side somewhere that pays.</p>
<ol>
  <li><strong>The world holds more kinds.</strong> More ways of living held at every census than e070's 3.</li>
  <li><strong>A kind keeps to a place.</strong> A way of living that keeps 90% of its bodies to one medium; e070 has none.</li>
  <li><strong>The worlds stand.</strong> 100,000 steps with bodies in all three media, and a world that returns after a disturbance.</li>
</ol>

<h2>2. The world</h2>
<p>e070's world with seven rates, every one of them 0 being e070 exactly: a body that holds heat and pays to stay in its band (A), wood
only a hard tooth can bite (B), fat that weighs (C), a sea that gives no drink (D), sight that ends with the light (E), a rise that costs
to climb (F), runoff that carries soil (G). A dry run over e070's censuses put each rate where its law bites.</p>
{DIAGRAM}
<p><strong>Runs.</strong> A Latin hypercube of 22 combinations on c1225, seed 9, 50,000 steps, then the centre of the four best on seeds
9, 10 and 11 for 100,000 steps, against e070's runs on the same seeds, plus one run where half of the largest lineage is cut at step
50,000. Read over the six censuses of each run's second half:</p>
<ul class="measures">
  <li><strong>Kinds of living</strong> - a birth form's diet, tooth, roaming and medium; a kind counts when it holds 5% of the grown bodies.</li>
  <li><strong>Held at every census</strong> - the same kinds present in all six; turnover breaks it.</li>
  <li><strong>Kept to a place</strong> - 90% of a kind's bodies in one medium, not spread over the shore.</li>
  <li><strong>Open soft faces per block</strong> - how open a body is: what dries, breathes and passes heat.</li>
  <li><strong>Deaths by cause</strong> - hunger, thirst, suffocation, a broken body, cold.</li>
  <li><strong>The land's soil</strong> - whether the bodies pump the sea's matter ashore.</li>
</ul>

<h2>3. Results</h2>
<div class="tw"><table>
<thead><tr><th>Second half, seeds 9-11</th><th>control (e070)</th><th>the sets</th></tr></thead>
<tbody>{body}</tbody></table></div>
<ol class="verdicts">
<li><span class="verdict no">No</span> More kinds held at every census: 4, 3 and 2 against 3, 3 and 3, both averaging 3.00.</li>
<li><span class="verdict">Yes</span> A kind keeps to a place: 2, 2 and 1 kinds keep to one medium, against none on any control seed.</li>
<li><span class="verdict">Yes</span> The worlds stand: 5,955 bodies at the lowest, and the halved lineage is back over the uncut run in 4,000 steps.</li>
</ol>

<h3>3.1 More kinds at every census, but not the same ones</h3>
<div class="grid2">
{charts_html[0]}
{charts_html[1]}
</div>
<p>Every census of the sets holds 4 to 8 kinds where the control holds 3 or 4, and the leanest of the six holds 5, 4 and 6 against 3, 3
and 3. What fails is identity: five kinds on seed 9 sit at 4-5% of the grown bodies and cross the line between censuses. An even world
loses that intersection exactly because it is even.</p>

<h3>3.2 The land and the water hold different bodies</h3>
<div class="grid2">
{charts_html[2]}
{charts_html[3]}
</div>
<p>In e070 a body was the same body everywhere, a third more open in the water than on land. Under the sets the land's bodies close to
0.64 faces a block and arm to 11.9% hard, while the water's stay at 1.24 and 1.5%. Hard blocks, useless in nine earlier runs, are worth
building; two seeds of three grow a land kind that eats other bodies.</p>

<h3>3.3 Thirst moves the crowd ashore</h3>
<div class="grid2">
{charts_html[4]}
{charts_html[5]}
</div>
<p>Dropping the sea's drink makes thirst 60% of the deaths and nearly doubles the land's crowd, at the cost of 45% of the surface's. The
heat kills 2.4% outright and is paid all the time: the land's bodies spend 6-8% of their upkeep warming. Wood is not eaten at this rate,
so the tooth that appears is for other bodies.</p>

<h3>3.4 The world returns, and the pump slows</h3>
<div class="grid2">
{charts_html[6]}
{charts_html[7]}
</div>
<p>The cut lineage is back over its uncut size in 4,000 steps, and the world's bodies never leave their band (9,500-12,600); by step
61,000 the recovered lineage has split into three of 1,320, 787 and 463 bodies. The soil still moves from the sea to the land, but the
runoff halves the rate: 6.5-7.3% of the land's matter over 90,000 steps where e070 gained 13-14%.</p>

{gallery(pick)}

<h2>4. Discussion</h2>
<p>The balance table's claim was that a law added alone meets a world without its counterweights, and that is what the runs show from the
other side: the same heat that e071 rejected as a flat tax on the land becomes the thing that places a kind, once the sea stops quenching
and the fat has a weight to carry. Ranked over the 22 combinations, the heat is what puts a kind in one medium; nothing else does.</p>
<p>Two of the seven did nothing. Wood at this rate is 0.1% of what bodies eat, because a cell's standing wood is eaten out in the first
few thousand steps and grows back over 20,000. The climb is too small to show against a body that travels 25 sub-cells in its life. The
runoff is a brake, not a cure: it would need a rate ten times larger to answer the bodies' pump, and at that rate it strips the uplands.</p>
<p>What the report does not show: the cool world c1236, runs past 100,000 steps, the rates apart from each other, and the invasion test
that would say whether two kinds can each come back from rare.</p>

<h2>5. Conclusion and next step</h2>
<p>By the rule written before the runs the sets are not kept: the kinds held at every census stayed at 3.00. Every other measure moved.
The proposal is to keep the sets, judge stage C from here by the kinds at a census and the kinds kept to a place, and spend the next
experiment on the two counterweights that did nothing.</p>

<h2>Appendix: data</h2>
<p>Every number here comes from <code>results/*.csv</code> (runs, kinds, by medium, per census) and the run logs. Build this report with
<code>uv run python experiments/e072_balance/report.py</code>.</p>
{appendix}
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
