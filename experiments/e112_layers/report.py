#!/usr/bin/env python3
"""Build report.html for e112 (#125): the layers - the ground and the crowns, the set, the pilot on the islands.

Charts: matplotlib, exported as SVG and inlined. Diagram: hand-written SVG.
Run from the repo root: uv run python experiments/e112_layers/report.py
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
BARE = os.path.join(HERE, "..", "e109_metres", "results", "isles1_life1_log.csv")
CONTROL = os.path.join(HERE, "..", "e111_holds", "results", "pilot", "all140")
PILOT = os.path.join(RESULTS, "pilot")
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



def big_share(path):
    """Year -> share of the bodies' matter in genotypes whose adult mass is over 1 kg (a body census)."""
    m, big = {}, {}
    with open(path) as f:
        for r in csv.DictReader(f):
            y, x = int(r["year"]), float(r["matter"])
            m[y] = m.get(y, 0.0) + x
            if float(r["adult_mass"]) > 1.0:
                big[y] = big.get(y, 0.0) + x
    return {y: big.get(y, 0.0) / m[y] for y in m if m[y] > 0}


# Hand-written mechanism diagram: a land cell's three layers and their doors.
DIAGRAM = """
<figure class="diagram">
<svg viewBox="0 0 720 290" role="img" aria-label="A land cell has three layers: the crowns above, reached by a body whose glue holds its weight on wood that bears it; the surface; and the ground below, reached by a front that presses harder than the soil. A body meets and eats only in its layer." style="max-width:100%;height:auto;display:block">
<defs><marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="currentColor"/></marker>
<marker id="arra" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="var(--s1)"/></marker></defs>
<g fill="none" stroke="currentColor" stroke-width="1.3" font-size="12" font-family="system-ui, sans-serif">
  <rect x="20" y="16" width="330" height="70" rx="6"/>
  <text x="36" y="40" fill="currentColor" stroke="none" font-weight="600">the crowns</text>
  <text x="36" y="58" fill="currentColor" stroke="none">leaves, hanging seed, wood</text>
  <text x="36" y="75" fill="currentColor" stroke="none">no water to drink</text>
  <rect x="20" y="110" width="330" height="70" rx="6"/>
  <text x="36" y="134" fill="currentColor" stroke="none" font-weight="600">the surface</text>
  <text x="36" y="152" fill="currentColor" stroke="none">litter, leaves in reach, flesh, water</text>
  <text x="36" y="169" fill="currentColor" stroke="none">every body evolved lives here</text>
  <rect x="20" y="204" width="330" height="70" rx="6"/>
  <text x="36" y="228" fill="currentColor" stroke="none" font-weight="600">the ground</text>
  <text x="36" y="246" fill="currentColor" stroke="none">roots, stores, the seed bank</text>
  <text x="36" y="263" fill="currentColor" stroke="none">45% of the living producers, dark</text>
  <path d="M300,110 L300,88" stroke="var(--s1)" marker-end="url(#arra)"/>
  <path d="M300,182 L300,202" stroke="var(--s1)" marker-end="url(#arra)"/>
  <text x="380" y="40" fill="var(--s1)" stroke="none" font-weight="600">door up</text>
  <text x="380" y="58" fill="currentColor" stroke="none">glue under it holds its weight, and wood</text>
  <text x="380" y="75" fill="currentColor" stroke="none">bears it: 0.3 kg of wood a m2 for 10 mg</text>
  <text x="380" y="134" fill="currentColor" stroke="none" font-weight="600">one output of its controller</text>
  <text x="380" y="152" fill="currentColor" stroke="none">chooses the layer; a body meets, senses</text>
  <text x="380" y="169" fill="currentColor" stroke="none">and eats only in its own</text>
  <text x="380" y="228" fill="var(--s1)" stroke="none" font-weight="600">door down</text>
  <text x="380" y="246" fill="currentColor" stroke="none">its front presses harder than the soil</text>
  <text x="380" y="263" fill="currentColor" stroke="none">(1e5 Pa, twice when dry); digs at its power</text>
</g>
</svg>
<figcaption>Figure 1. A land cell's three layers. Blue: the doors, priced by the body's own physics. A store is digested whole and brings no A or B. A front breaks only what its gut takes in (the bite's clause, <code>tear=0</code>).</figcaption>
</figure>
"""

TEXT = {
    "tldr": """Most of the land's food is in the ground, out of reach. The layers open the ground and the crowns.
Designed bodies entered both and every line died within ten years; evolution found neither door in sixty years on
the islands, and no body eats flesh. The islands showed history instead: the same world fills with 18 kg bodies,
where e111's sowing gave 0.1 kg ones. Next: the catch, and the sea as a place.""",
    "question": """e111's land stands, but under one way of living: a 0.1 kg litter eater, no flesh, one line. 45% of
the land's living producers are roots, stores and the seed bank, unreached, and a grown body reaches 12% of the
leaves. Does a body that can enter the ground or the crowns live there, and does evolution find the way in?""",
    "world": """e111's world with three layers a land cell (Figure 1), each behind a switch: off, it is e111's world to
the digit. Three designed bodies test whether a door can be lived in: a digger of 0.1 kg, a climber of 10 mg, a
hunter that walks.""",
    "runs": """A trial world of 16 km (26 km2 of land), bodies sown in year 15, read over years 26-30: the layers, each
left out, and the designed bodies put in in year 20. Then the islands (410 km2), bodies sown in year 40, to year 100,
against e111's run, and three runs that ask why its bodies are large.""",
    "v1": "No designed line lived ten years: the digger's young starve, the climber dies of thirst, the hunter's press costs more than its gut passes.",
    "v2": "No evolved body's matter is in the ground or the crowns, on the trial world or in sixty years on the islands.",
    "v3": "Evolved bodies leave the land within the spread; a designed digger takes it to 83% of the bare world.",
    "v4": "With the switches off, and with them on and unused, the world is e111's to the digit.",
    "v5": "Flesh is 0.14% of the diet at most, nothing after year 80.",
    "h31": "3.1 The ground is the land's largest larder",
    "p31": """Roots, stores and the bank hold 0.38 kg a m2 against 0.04 in leaves. A store is sugar with almost no A
or B: a fuel, not a body. The layers changed the land by less than two realisations differ; only a designed digger
ate into it.""",
    "h32": "3.2 A door entered is not a door lived in",
    "p32": """Each designed line entered its layer and died of something the door did not price. The digger's young,
0.3-6% of an adult's mass, move a metre a day and cannot dig out of the cell their kin ate down. A climber small enough
for the crowns dries out between drinks.""",
    "h33": "3.3 On the islands: no door, no flesh, a land that stands",
    "p33": """The land stays at 81-100% of the world without bodies, above the control in every decade, while the
bodies hold 2.7 times its matter by year 100. Nobody uses a layer; litter is the whole diet from year 80.""",
    "h34": "3.4 The size of everything is set by who survives the first years",
    "p34": """Three years after the sowing the world held 48 bodies, and the line that came through was a large
founder's. Sown a year later it came through large again, with the clause and without it; e111's sowing came
through small. The ways number 2-2.6, parted by land against sea and by size; one line holds all.""",
    "discussion": """<p>A door is the price of entering a layer; living there costs more. The ground's foods are poor
in A, eaten where the digger is born, and paid for at a young body's pace; the crowns are dry. Neither cost was in the
design, and both are physics the world already has. A layer becomes a place when a body can live a life in it.</p>
<p>The islands' large bodies are the first to hold this world while litter is eaten, and they are not a law's
doing: one bottleneck of a few dozen bodies decided it for sixty years. That is what a replay that differs looks like, and a
warning: one pilot reads one history.</p>
<p>Not shown: whether the clause matters for the land on the islands (one realisation each), and whether a door is
found over centuries.</p>""",
    "conclusion": """The layers and the clause stay in this crate, on, for the next step; nothing goes to the base. The
pilot met two of #116's turns: no line lives on flesh with a place to hide (the catch itself is next to redesign),
and one line holds land and sea (the sea as a place with its own cost). The open measure (#119) read the pilot and
closes.""",
}


def main():
    sset = {r["run"]: r for r in rows(os.path.join(RESULTS, "set.csv"))}
    des = rows(os.path.join(RESULTS, "set_designed.csv"))
    pools = {(r["run"], r["pool"]): float(r["kg_m2"]) for r in rows(os.path.join(RESULTS, "layers.csv"))}
    pil = rows(os.path.join(RESULTS, "pilot.csv"))
    ctl = rows(os.path.join(RESULTS, "control.csv"))
    pct = lambda v, _p: f"{v:.0%}"
    charts = {}
    names = [("leaves", "leaf"), ("wood", "wood"), ("roots", "root"), ("stores", "store"), ("seed bank", "bank"), ("litter", "litter")]
    charts["pools"] = bar_chart(
        "Where the land's matter is", "kg a m2 of land on the trial world with no bodies, years 26-30. Aqua: in the ground, out of every evolved body's reach.",
        [(lab, pools[("nobody", k)], 2 if k in ("root", "store", "bank") else 0) for lab, k in names], "kg a m2", lambda v, _p: f"{v:.2f}", xmax=0.55,
    )
    order = [("e111's world", "off", 1), ("the layers", "layers", 0), ("without the ground", "no_ground", 0), ("without the crowns", "no_crown", 0),
             ("old clause (tears)", "tear", 3), ("+ designed digger", "digger2", 2), ("+ designed climber", "climber2", 2), ("+ walking hunter", "hunter", 2)]
    charts["set"] = bar_chart(
        "The trial world: the land's producers", "Share of the same world without bodies, years 26-30. The layers alone sit inside the spread; the digger eats into the land.",
        [(lab, float(sset[r]["of_nobody"]), s) for lab, r, s in order], "of the world without bodies", pct, xmax=1.12,
    )
    lines = [("digger", "digger", 0), ("digger, faster", "digger2", 1), ("climber", "climber", 2), ("climber, drinks", "climber2", 3)]
    charts["designed"] = line_chart(
        "The designed lines", "Tonnes of each designed line on the trial world, put in in year 20. Zero is a line gone; the walking hunter's was gone within its first year.",
        [(lab, [20] + [int(x["year"]) for x in des if x["run"] == r], [0.0] + [float(x["matter_t"]) for x in des if x["run"] == r], s, False) for lab, r, s in lines],
        "year (bodies sown in year 15)", fmt=lambda v, _p: f"{v:g} t",
    )
    bare = {int(x["year"]): float(x["land_biomass"]) for x in rows(BARE)}
    pl, cl = rows(os.path.join(PILOT, "layers_log.csv")), rows(CONTROL + "_log.csv")
    yr = lambda log: [int(x["year"]) for x in log if 35 <= int(x["year"]) <= 100]
    col = lambda log, f: [f(x) for x in log if 35 <= int(x["year"]) <= 100]
    ofb = lambda x: float(x["land_biomass"]) / bare[int(x["year"])]
    charts["land"] = line_chart(
        "The islands: the land's producers", "Share of the same world without bodies (e109), a year at a time. 100% is a land not eaten; half was the pilot's line.",
        [("the layers", yr(pl), col(pl, ofb), 0, False), ("control (e111)", yr(cl), col(cl, ofb), 1, False)], "year (bodies sown in year 40)", fmt=pct, ymax=1.1,
    )
    kt = lambda x: float(x["body_matter"]) * CELL_M2 / 1e6
    charts["matter"] = line_chart(
        "The islands: the bodies' matter", "Thousand tonnes of animals, dry. The large bodies fill the land later and hold more of it.",
        [("the layers", yr(pl), col(pl, kt), 0, False), ("control (e111)", yr(cl), col(cl, kt), 1, False)], "year (bodies sown in year 40)",
    )
    shares = [("the layers", big_share(os.path.join(PILOT, "layers_bodies.csv")), 0, False), ("control (e111)", big_share(CONTROL + "_bodies.csv"), 1, False),
              ("sown 41, new", big_share(os.path.join(PILOT, "sow41_tear0_bodies.csv")), 2, True), ("sown 41, old", big_share(os.path.join(PILOT, "sow41_tear1_bodies.csv")), 3, True)]
    charts["big"] = line_chart(
        "The islands: matter in bodies over 1 kg", "Share of the bodies' matter, a census a year. Dashed: the same world sown in year 41, with the new clause and the old; both come through large.",
        [(lab, [y for y in sorted(d) if y <= 100], [d[y] for y in sorted(d) if y <= 100], s, dash) for lab, d, s, dash in shares], "year", fmt=pct, ymax=1.05,
    )
    mid = lambda r: int(r["census"]) - 5
    charts["ways"] = line_chart(
        "The islands: ways of living", "Effective number of groups by analysis/ways.py, a census a decade. 1 is one way; the layers' bodies part by land or sea and by size.",
        [("the layers", [mid(r) for r in pil], [float(r["ways_hill"]) for r in pil], 0, False),
         ("control (e111)", [mid(r) for r in ctl if int(r["census"]) <= 100], [float(r["ways_hill"]) for r in ctl if int(r["census"]) <= 100], 1, False)],
        "year", fmt=lambda v, _p: f"{v:g}", ymax=3.2,
    )

    def srow(name, r):
        return (f"<tr><td>trial</td><td>{name}</td><td>{float(r['of_nobody']):.0%}</td><td>{float(r['matter_t']):,.0f}</td>"
                f"<td>{100 * (float(r['ground_share']) + float(r['crown_share'])):.2f}%</td><td>-</td><td>{float(r['flesh']):.2%}</td></tr>")

    def prow(name, r):
        return (f"<tr><td>islands {r['years']}</td><td>{name}</td><td>{float(r['of_bare']):.0%}</td><td>{float(r['matter_t']):,.0f}</td>"
                f"<td>{100 * (float(r.get('ground_share') or 0) + float(r.get('crown_share') or 0)):.2f}%</td><td>{float(r['over_1kg']):.0%}</td><td>{float(r['flesh_share']):.2%}</td></tr>")

    held = lambda r: f"{float(r['held']):.2f}" if r['held'] else '-'
    cd = {r["years"]: r for r in ctl}
    summary = "".join([srow(n, sset[r]) for n, r in [("e111's world", "off"), ("<strong>the layers</strong>", "layers"), ("+ designed digger", "digger2"), ("+ designed climber", "climber2")]]
                      + [x for y in ("51-60", "91-100") for x in (prow("control (e111)", cd[y]), prow("<strong>the layers</strong>", next(r for r in pil if r["years"] == y)))])
    T = TEXT
    prov = "".join(f"<tr><td>{html.escape(r['what'])}</td><td>{html.escape(r['value'])}</td></tr>" for r in rows(os.path.join(RESULTS, "provenance.csv")))
    pt = "".join(f"<tr><td>{r['years']}</td><td>{float(r['of_bare']):.0%}</td><td>{float(r['bodies']):,.0f}</td><td>{float(r['matter_t']):,.0f}</td><td>{float(r['over_1kg']):.0%}</td><td>{float(r['flesh_share']):.2%}</td><td>{float(r['layer_food_share']):.2%}</td><td>{float(r['ways_hill']):.2f}</td><td>{held(r)}</td><td>{float(r['died_thirst']):,.0f}</td></tr>" for r in pil)
    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>e112 the layers - Report</title>
<style>{CSS}</style>
</head>
<body>
<main>
<h1>e112: the layers</h1>
<p class="sub">Experiment report - 2026-10-27 - the ground and the crowns as places a body enters (#125): ten runs on a trial world, a pilot of 60 years on the islands and three runs beside it</p>

<section class="tldr">
<h2>TL;DR</h2>
<p>{T['tldr']}</p>
</section>

<h2>1. Question</h2>
<p>{T['question']}</p>
<ol>
  <li><strong>Each door can be lived in</strong> - a designed line lives in its layer to year 30.</li>
  <li><strong>Evolution has not found a door</strong> in fifteen years on the trial world.</li>
  <li><strong>The land is not eaten from below.</strong></li>
  <li><strong>With the switches off the world is e111's</strong> to the digit.</li>
  <li><strong>On the islands a door is used and flesh is over 1% of the diet</strong> (the pilot's lines, written before it).</li>
</ol>

<h2>2. The world</h2>
<p>{T['world']}</p>
{DIAGRAM}
<p><strong>Runs.</strong> {T['runs']}</p>
<ul class="measures">
  <li><strong>The land's producers</strong> - kg of plants a m2 of land, against the same world with no bodies.</li>
  <li><strong>Matter</strong> - dry weight of the animals the bodies stand for.</li>
  <li><strong>In a layer</strong> - share of the bodies' matter in the ground or the crowns.</li>
  <li><strong>Flesh</strong> - carrion and kills, of everything eaten.</li>
  <li><strong>Ways</strong> - groups of genotypes that differ by diet, place, size, range or make (<code>analysis/ways.py</code>).</li>
</ul>

<h2>3. Results</h2>
<div class="tw"><table><thead><tr><th>world</th><th>run</th><th>land's producers, of no bodies</th><th>bodies' matter (t)</th><th>in a layer</th><th>over 1 kg</th><th>flesh in the diet</th></tr></thead><tbody>{summary}</tbody></table></div>
<ol class="verdicts">
<li><span class="verdict no">No</span> {T['v1']}</li>
<li><span class="verdict">Yes</span> {T['v2']}</li>
<li><span class="verdict partly">Partly</span> {T['v3']}</li>
<li><span class="verdict">Yes</span> {T['v4']}</li>
<li><span class="verdict no">No</span> {T['v5']}</li>
</ol>

<h3>{T['h31']}</h3>
<div class="grid2">
{charts['pools']}
{charts['set']}
</div>
<p>{T['p31']}</p>

<h3>{T['h32']}</h3>
<div class="grid2">
{charts['designed']}
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
{charts['big']}
{charts['ways']}
</div>
<p>{T['p34']}</p>

<h2>4. Discussion</h2>
{T['discussion']}

<h2>5. Conclusion and next step</h2>
<p>{T['conclusion']}</p>

<h2>Appendix: data</h2>
<p>Readings in <code>results/read.csv</code>, <code>layers.csv</code>, <code>set.csv</code>, <code>set_designed.csv</code>, <code>control.csv</code> and
<code>pilot.csv</code> (written by <code>read.py</code>, <code>set.py</code> and <code>control.py</code>), the logs in <code>results/read/</code>, <code>set/</code>
and <code>pilot/</code>; the yearly censuses and the traces stay on the Ubuntu machine.
Build: <code>uv run python experiments/e112_layers/report.py</code>.</p>
<details><summary>The pilot by decade</summary><div class="tw"><table><thead><tr><th>years</th><th>land, of bare</th><th>bodies</th><th>matter (t)</th><th>over 1 kg</th><th>flesh</th><th>layer foods</th><th>ways</th><th>held by island</th><th>dead of thirst a year</th></tr></thead><tbody>{pt}</tbody></table></div></details>
<details><summary>What was read (<code>results/provenance.csv</code>)</summary><div class="tw"><table><thead><tr><th>what was read</th><th>value</th></tr></thead><tbody>{prov}</tbody></table></div></details>
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
