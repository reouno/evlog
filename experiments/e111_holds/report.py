#!/usr/bin/env python3
"""Build report.html for e111 (#130): what holds the eaters - the readings, the design, its runs.

Charts: matplotlib, exported as SVG and inlined. Diagram: hand-written SVG.
Run from the repo root: uv run python experiments/e111_holds/report.py
"""
import csv
import html
import io
import os
import sys

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


RESULTS = os.path.join(HERE, "results")
CONTROL = os.path.join(HERE, "..", "e109_metres", "results", "isles1_life1_log.csv")
TICK1 = os.path.join(HERE, "..", "e110_meet", "results", "pilot", "tick1_log.csv")
CELL_M2 = 125.0 ** 2


def rows(path):
    with open(path) as f:
        return list(csv.DictReader(f))


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


def line_chart(title, subtitle, series, xlabel, fmt=None, ymax=None, log=False, logx=False):
    """series: (label, xs, ys, slot or None for the control, dashed)."""
    fig, ax = plt.subplots(figsize=(6.4, 2.6))
    for label, xs, ys, slot, dashed in series:
        ax.plot(xs, ys, color=INK if slot is None else SERIES[slot], linewidth=1.8, label=label, linestyle="--" if dashed else "-")
    ax.set_xlabel(xlabel, loc="right")
    if logx:
        ax.set_xscale("log")
    if log:
        ax.set_yscale("log")
    else:
        ax.set_ylim(0, ymax)
        ax.yaxis.set_major_locator(MaxNLocator(4))
        ax.yaxis.set_major_formatter(fmt or kfmt)
    ax.margins(x=0)
    legend_above(ax, len(series))
    return figure(title, subtitle, to_svg(fig))


def bar_chart(title, subtitle, bars, xlabel, fmt, xmax=None, mark=None):
    """bars: (label, value, slot). Horizontal, one bar a run, the first at the top."""
    fig, ax = plt.subplots(figsize=(6.4, 0.6 + 0.4 * len(bars)))
    fig.subplots_adjust(left=0.36, right=0.98)  # the runs' names stay inside the figure, so the text keeps its size
    ys = list(range(len(bars)))[::-1]
    ax.barh(ys, [v for _, v, _ in bars], color=[SERIES[s] for _, _, s in bars], height=0.62)
    ax.set_yticks(ys, [l for l, _, _ in bars])
    ax.set_xlabel(xlabel, loc="right")
    ax.set_xlim(0, xmax)
    ax.xaxis.set_major_locator(MaxNLocator(4))
    ax.xaxis.set_major_formatter(fmt)
    ax.grid(axis="y", visible=False)
    ax.grid(axis="x", visible=True)
    if mark is not None:
        ax.axvline(mark, color=INK, linewidth=1, linestyle="--")
    for y, (_, v, _) in zip(ys, bars):
        ax.text(v, y, " " + fmt(v, None), va="center", ha="left", fontsize=9)
    return figure(title, subtitle, to_svg(fig))


# Hand-written mechanism diagram: the roads of a mouthful under the design.
DIAGRAM = """
<figure class="diagram">
<svg viewBox="0 0 720 250" role="img" aria-label="Of a mouthful of plant food the working part is digested at once and the bulk passes as dung; what the gut digests and does not keep of its nutrients goes to the soil, and the producers take it up" style="max-width:100%;height:auto;display:block">
<defs><marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="currentColor"/></marker>
<marker id="arra" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="var(--s1)"/></marker></defs>
<g fill="none" stroke="currentColor" stroke-width="1.3" font-size="12" font-family="system-ui, sans-serif">
  <rect x="14" y="84" width="90" height="60" rx="6"/>
  <text x="59" y="109" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">litter</text>
  <text x="59" y="128" text-anchor="middle" fill="currentColor" stroke="none">1.5% B</text>
  <path d="M104,114 L196,114" marker-end="url(#arr)"/>
  <text x="148" y="102" text-anchor="middle" fill="currentColor" stroke="none">a mouthful</text>
  <rect x="198" y="84" width="150" height="60" rx="6"/>
  <text x="273" y="109" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">a gut</text>
  <text x="273" y="128" text-anchor="middle" fill="currentColor" stroke="none">holds its own mass</text>
  <path d="M348,100 L420,58" marker-end="url(#arr)"/>
  <text x="384" y="50" text-anchor="end" fill="currentColor" stroke="none">working part: B / 3%</text>
  <rect x="422" y="24" width="130" height="56" rx="6"/>
  <text x="487" y="48" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">digested at once</text>
  <text x="487" y="66" text-anchor="middle" fill="currentColor" stroke="none">kept: body, eggs</text>
  <path d="M552,52 L606,52" stroke="var(--s1)" marker-end="url(#arra)"/>
  <rect x="608" y="24" width="98" height="56" rx="6" stroke="var(--s1)" stroke-width="2"/>
  <text x="657" y="48" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">the soil</text>
  <text x="657" y="66" text-anchor="middle" fill="currentColor" stroke="none">A, B not kept</text>
  <path d="M348,128 L420,172" marker-end="url(#arr)"/>
  <text x="376" y="184" text-anchor="end" fill="currentColor" stroke="none">bulk: the rest</text>
  <rect x="422" y="150" width="130" height="56" rx="6"/>
  <text x="487" y="174" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">dung</text>
  <text x="487" y="192" text-anchor="middle" fill="currentColor" stroke="none">0.4-6% digested</text>
  <path d="M487,206 L487,232 L59,232 L59,150" marker-end="url(#arr)"/>
  <text x="280" y="224" text-anchor="middle" fill="currentColor" stroke="none">back to the litter, for the rot and the next gut</text>
  <path d="M657,80 L657,114 L608,114" stroke="var(--s1)" marker-end="url(#arra)"/>
  <text x="596" y="118" text-anchor="end" fill="var(--s1)" stroke="none">the producers take it up</text>
</g>
</svg>
<figcaption>Figure 1. A mouthful of plant food under the design. Before it, the whole mouthful was digested and what the gut did not keep of its A and B went back into a litter that had no matter left to rot. Blue: the road the land turned out to hang on.</figcaption>
</figure>
"""

TEXT = {
    "tldr": """e110's bodies ate the land bare. Readings on a small trial world say one thing carries them: the
dead matter, free and digested whole. With a food worth its working part only and a gut's leavings sent to the
soil, the land stands - 93% of the world without bodies on the trial world, 78% on the islands, where it was 1%.
No hunter lives with its prey yet: the next step is places to hide.""",
    "question": """What holds eaters in a world that stands? First readings with no new law: switches that take a
food out of reach, a hunter designed by hand and put in, and the arithmetic of a body's day. Then one design of
four parts, agreed before code, and its runs.""",
    "world": """Four laws, each behind a switch. A plant food's working part is digested at once and its bulk
only as the rot digests it (worth). What a gut does not keep goes to the soil (road). Wood is reached by height
and fallen seed lies in the ground (reach). A front breaks what its gut takes in (bite).""",
    "runs": """A trial world of 16 km (26 km2 of land), bodies sown in year 15, read over years 26-30: nine
readings, then the design all on, each law left out, and four designed hunters. Then the islands
(<code>isles1</code>, 410 km2 of land) for 30 years with bodies. One run each, all on one machine.""",
    "v1": "A 0.1 kg body pays its day on 0.04 g of food a m2; the land holds 800 g of producers.",
    "v2": "With litter no food the bodies fall to a hundredth and the land stands at 98%.",
    "v3": "At ten times the decay the land is 26%: bodies pass litter in days.",
    "v4": "Wood and the seed bank out of reach keep the cover (81% against 53%), and the producers still halve.",
    "v5": "It breaks every body in a year, eats 3% of what it kills, and starves.",
    "v6": "93% of the world without bodies on the trial world, 78% on the islands after 30 years.",
    "v7": "Without the worth the land is 27%, without the road 69%; without the reach 88%, inside the spread of two runs.",
    "v8": "A front that breaks empties the world, hungry or not; a soft front that only swallows fails on its prey.",
    "h31": "3.1 A body's economy has no floor, and the dead are free",
    "p31": """The thinnest food a body can live on is ten thousand times below what the land holds, so whatever
is free is eaten to nothing. Only one switch leaves the land standing: litter no food. The body left then is
another one - 18 to 250 kg, strong-mouthed, eating wood and seed.""",
    "h32": "3.2 The land hangs on what the dead are worth and where their nutrients go",
    "p32": """With only litter eaten the producers still halved: the nutrients a gut passed went back into a
litter with no matter left, which could not rot. Under the design the eaters turn the litter over instead of
removing it, and the world fixes more with them than without. I expected the worth to matter least of the four;
it matters most.""",
    "h33": "3.3 On the islands the land stands, and is not settled",
    "p33": """Where e110 left a hundredth of the producers, the design leaves 78% after 30 years. But against
the world without bodies the land loses about a point a year, and the bodies still grow. It is not the nutrients;
the cause is not separated.""",
    "h34": "3.4 No hunter lives with its prey",
    "p34": """Every designed hunter with a front that breaks emptied the trial world within a year and starved,
with the bite law or without, hunting always or only when hungry. On the islands every body presses others, and
flesh is 0.1% of the diet.""",
    "discussion": """<p>The real land is green partly because most dead matter is worth little to an animal and
goes back to the soil. That alone was missing here, and it was enough for the land. It was not what I had ranked
first: the readings showed where the nutrients went, not how much the eaters' number hangs on what they digest.</p>
<p>The bite law bounds what a mouth swallows, but a front that can break is mostly not mouth, and that part tears
17 times what the gut takes. And a prey that is slower is caught every time: no law gives it a place where the
hunter is not.</p>
<p>Not shown: where the islands settle (30 years, one seed), and anything about size or lines - one line of
0.1 kg sacks, 65% gut, still holds every island.</p>""",
    "conclusion": """The four laws stay as the bodies' code. Next in the plan is the layered cell: the ground
and the crowns as places a body can enter, where seed and roots are food and the caught can hide. The bite's
clause for a front that is no mouth is settled with it. A body keeps standing for 4,000 kg of animals.""",
}


def main():
    read = {r["run"]: r for r in rows(os.path.join(RESULTS, "read.csv"))}
    sset = {r["run"]: r for r in rows(os.path.join(RESULTS, "set.csv"))}
    pil = {r["run"]: r for r in rows(os.path.join(RESULTS, "pilot.csv"))}
    bench = rows(os.path.join(RESULTS, "bench.csv"))
    pct = lambda v, _p: f"{v:.0%}"
    tons = lambda v, _p: f"{v:,.0f} t"
    charts = {}
    b0 = [x for x in bench if x["body"] == "no genes" and x["act"] == "0.10"]
    charts["thin"] = line_chart(
        "The thinnest food a body lives on", "g of soft food a m2 that pays a day, by adult mass (log scales). The land holds 800 g of producers: far above every point.",
        [("a body with no genes", [float(x["adult_kg"]) for x in b0], [1000 * float(x["thinnest_kg_m2"]) for x in b0], 0, False)],
        "adult mass, kg", log=True, logx=True,
    )
    lev = [("e110's world", "base", 1), ("litter no food", "nolitter", 0), ("decay x10", "decay10", 1), ("wood, bank out of reach", "noreach", 1), ("both of those", "decay10_noreach", 1)]
    charts["levers"] = bar_chart(
        "Readings: the land's producers", "Share of the same world without bodies, years 26-30. A bar at 100% is a land not eaten; dashed: half.",
        [(lab, float(read[r]["land_of_control"]), s) for lab, r, s in lev], "of the world without bodies", pct, xmax=1.15, mark=0.5,
    )
    order = [("e110's world", "e110", 1), ("the design, all four", "all", 0), ("without the road", "no_road", 2), ("without the worth", "no_worth", 2), ("without the reach", "no_reach", 2)]
    charts["set"] = bar_chart(
        "The design: the land's producers", "Share of the world without bodies, years 26-30, with all four laws and with each left out.",
        [(lab, float(sset[r]["land_of_control"]), s) for lab, r, s in order], "of the world without bodies", pct, xmax=1.15, mark=0.5,
    )
    charts["setm"] = bar_chart(
        "The design: the bodies' matter", "Tonnes of animals on the trial world, years 26-30. Fewer bodies is a food worth less.",
        [(lab, float(sset[r]["matter_t"]), s) for lab, r, s in order], "tonnes, dry", tons, xmax=7600,
    )
    ctl, t1, al = rows(CONTROL), rows(TICK1), rows(os.path.join(RESULTS, "pilot", "all_log.csv"))
    yrs = lambda log: [int(x["year"]) for x in log if 35 <= int(x["year"]) <= 70]
    col = lambda log, f: [f(x) for x in log if 35 <= int(x["year"]) <= 70]
    charts["land"] = line_chart(
        "The islands: the land's producers", "kg a m2 of land. Dashed: the same world without bodies (e109). The gap that opens is the land not yet settled.",
        [("the design", yrs(al), col(al, lambda x: float(x["land_biomass"])), 0, False), ("e110", yrs(t1), col(t1, lambda x: float(x["land_biomass"])), 1, False),
         ("no bodies", yrs(ctl), col(ctl, lambda x: float(x["land_biomass"])), None, True)], "year (bodies sown in year 40)",
    )
    kt = lambda x: float(x["body_matter"]) * CELL_M2 / 1e6
    charts["matter"] = line_chart(
        "The islands: the bodies' matter", "Thousand tonnes of animals, dry. e110's bodies peak and crash with the land; the design's still rise.",
        [("the design", yrs(al), col(al, kt), 0, False), ("e110", yrs(t1), col(t1, kt), 1, False)], "year (bodies sown in year 40)",
    )
    hl = {r: rows(os.path.join(RESULTS, "set", f"{r}_log.csv")) for r in ("all", "all_hunter", "all_hunter3", "all_hunter4")}
    ty = lambda log: [int(x["year"]) for x in log if int(x["year"]) >= 15]
    tm = lambda log: [float(x["body_matter"]) * CELL_M2 / 1000 for x in log if int(x["year"]) >= 15]
    charts["hunters"] = line_chart(
        "The trial world: a hunter put in in year 20", "Tonnes of all bodies, by the hunter's front. Zero is a world emptied; the soft-mouthed hunters died and left the others.",
        [("no hunter", ty(hl["all"]), tm(hl["all"]), 0, False), ("breaks", ty(hl["all_hunter"]), tm(hl["all_hunter"]), 1, False),
         ("breaks, hungry", ty(hl["all_hunter3"]), tm(hl["all_hunter3"]), 3, True), ("soft mouth", ty(hl["all_hunter4"]), tm(hl["all_hunter4"]), 2, False)],
        "year (bodies sown in year 15)",
    )
    fl = lambda x: (float(x["ate_carrion"]) + float(x["ate_kill"])) / max(sum(float(x["ate_" + k]) for k in ("leaf", "wood", "seed", "litter", "carrion", "kill")), 1e-30)
    after = lambda log: [x for x in log if 41 <= int(x["year"]) <= 70]
    charts["flesh"] = line_chart(
        "The islands: flesh in the diet", "Share of all the bodies eat that is carrion or kills. Rung 3's line for a food web is 10%.",
        [("the design", [int(x["year"]) for x in after(al)], [fl(x) for x in after(al)], 0, False), ("e110", [int(x["year"]) for x in after(t1)], [fl(x) for x in after(t1)], 1, False)],
        "year (bodies sown in year 40)", fmt=lambda y, _p: f"{y:.1%}",
    )

    def trow(world, name, r):
        f = lambda k, fmt: (fmt.format(float(r[k])) if r.get(k, "") != "" else "-")
        return f"<tr><td>{world}</td><td>{name}</td><td>{f('land_of_control', '{:.0%}')}</td><td>{f('land_cover', '{:.0%}')}</td><td>{f('matter_t', '{:,.0f}')}</td><td>{f('flesh_share', '{:.2%}')}</td></tr>"

    summary = "".join([
        trow("trial", "e110's world", read["base"]), trow("trial", "litter no food", read["nolitter"]), trow("trial", "decay x10", read["decay10"]),
        trow("trial", "wood and seed bank out of reach", read["noreach"]), trow("trial", "a designed hunter put in", read["hunter"]),
        trow("trial", "<strong>the design, all four</strong>", sset["all"]), trow("trial", "without the road", sset["no_road"]), trow("trial", "without the worth", sset["no_worth"]),
        trow("trial", "without the reach", sset["no_reach"]), trow("trial", "the design + the hunter", sset["all_hunter"]), trow("trial", "the design + a soft-mouthed hunter", sset["all_hunter4"]),
        trow("islands", "e110", pil["tick1"]), trow("islands", "<strong>the design</strong>", pil["all"]),
    ])
    T = TEXT
    prov = "".join(f"<tr><td>{html.escape(r['what'])}</td><td>{html.escape(r['value'])}</td></tr>" for r in rows(os.path.join(RESULTS, "provenance.csv")))
    bt = "".join(
        f"<tr><td>{x['body']}</td><td>{x['act']}</td><td>{float(x['adult_kg']):g}</td><td>{float(x['km_day']):.1f}</td><td>{float(x['sweep_m2_day_kg']):,.0f}</td><td>{float(x['gut_kg_day_kg']):.2f}</td><td>{float(x['upkeep_kg_day_kg']) + float(x['work_kg_day_kg']):.3f}</td><td>{1000 * float(x['thinnest_kg_m2']):.3g}</td></tr>"
        for x in bench
    )
    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>e111 what holds the eaters - Report</title>
<style>{CSS}</style>
</head>
<body>
<main>
<h1>e111: what holds the eaters</h1>
<p class="sub">Experiment report - 2026-10-07 - readings, a design of four laws and its runs (#130): 19 runs on a trial world, one of 70 years on the islands</p>

<section class="tldr">
<h2>TL;DR</h2>
<p>{T['tldr']}</p>
</section>

<h2>1. Question</h2>
<p>{T['question']}</p>
<ol>
  <li><strong>A body's economy has no floor</strong> - the thinnest food it lives on is far below what the land holds.</li>
  <li><strong>Litter carries the eaters</strong> - with litter no food the land stays within 20% of a world without bodies.</li>
  <li><strong>A faster rot does not hold them.</strong></li>
  <li><strong>Wood and the seed bank out of reach protect what regrows</strong> - the land stays above half.</li>
  <li><strong>A designed hunter does not live on flesh.</strong></li>
  <li><strong>The design holds the land</strong> - half of the world without bodies or more, on the trial world and for 30 years on the islands.</li>
  <li><strong>Each law carries part of it.</strong></li>
  <li><strong>A hunter's line lives with its prey</strong> under the design.</li>
</ol>

<h2>2. The world</h2>
<p>{T['world']}</p>
{DIAGRAM}
<p><strong>Runs.</strong> {T['runs']}</p>
<ul class="measures">
  <li><strong>The land's producers</strong> - kg of plants a m2 of land, against the same world with no bodies.</li>
  <li><strong>A and B</strong> - the world's two nutrients; B is what a tissue works with.</li>
  <li><strong>Matter</strong> - dry weight of the animals the bodies stand for.</li>
  <li><strong>Flesh</strong> - carrion and kills eaten, of everything eaten.</li>
</ul>

<h2>3. Results</h2>
<div class="tw"><table><thead><tr><th>world</th><th>run</th><th>land's producers, of no bodies</th><th>land covered</th><th>bodies' matter (t)</th><th>flesh in the diet</th></tr></thead><tbody>{summary}</tbody></table></div>
<ol class="verdicts">
<li><span class="verdict">Yes</span> {T['v1']}</li>
<li><span class="verdict">Yes</span> {T['v2']}</li>
<li><span class="verdict">Yes</span> {T['v3']}</li>
<li><span class="verdict partly">Partly</span> {T['v4']}</li>
<li><span class="verdict no">No</span> {T['v5']}</li>
<li><span class="verdict">Yes</span> {T['v6']}</li>
<li><span class="verdict partly">Partly</span> {T['v7']}</li>
<li><span class="verdict no">No</span> {T['v8']}</li>
</ol>

<h3>{T['h31']}</h3>
<div class="grid2">
{charts['thin']}
{charts['levers']}
</div>
<p>{T['p31']}</p>

<h3>{T['h32']}</h3>
<div class="grid2">
{charts['set']}
{charts['setm']}
</div>
<p>{T['p32']}</p>

<h3>{T['h33']}</h3>
<div class="grid2">
{charts['land']}
{charts['matter']}
</div>
<p>{T['p33']}</p>

<h3>{T['h34']}</h3>
<div class="grid2">
{charts['hunters']}
{charts['flesh']}
</div>
<p>{T['p34']}</p>

<h2>4. Discussion</h2>
{T['discussion']}

<h2>5. Conclusion and next step</h2>
<p>{T['conclusion']}</p>

<h2>Appendix: data</h2>
<p>Readings in <code>results/read.csv</code>, <code>set.csv</code>, <code>pilot.csv</code> and <code>designed.csv</code> (written by
<code>read.py</code>), the logs in <code>results/read/</code>, <code>set/</code> and <code>pilot/</code>; the censuses stay on the Ubuntu machine.
Build: <code>uv run python experiments/e111_holds/report.py</code>.</p>
<div class="tw"><table><thead><tr><th>what was read</th><th>value</th></tr></thead><tbody>{prov}</tbody></table></div>
<details><summary>A body's day by adult mass (<code>bench</code>)</summary><div class="tw"><table><thead><tr><th>body</th><th>share of its speed</th><th>adult mass (kg)</th><th>km a day</th><th>m2 swept a kg a day</th><th>gut passes (of its mass a day)</th><th>upkeep + work</th><th>thinnest food (g a m2)</th></tr></thead><tbody>{bt}</tbody></table></div></details>
</main>
</body>
</html>
"""
    out = os.path.join(HERE, "report.html")
    with open(out, "w") as fh:
        fh.write(page)
    words = len(" ".join(str(v) for v in T.values()).split())
    print(f"wrote {out} ({os.path.getsize(out)//1024} KB), {words} words of text")
    for k, v in T.items():
        print(f"  {k}: {len(str(v).split())}")


if __name__ == "__main__":
    main()
