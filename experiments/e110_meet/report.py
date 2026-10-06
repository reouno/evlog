#!/usr/bin/env python3
"""Build report.html for e110 (#123): bodies in metres and seconds, and bodies that meet - the pilot.

Charts: matplotlib, exported as SVG and inlined. Diagram: hand-written SVG.
Run from the repo root: uv run python experiments/e110_meet/report.py
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
RUNS = [("tick1", "update 19 min", 0), ("tick3", "64 min", 1), ("tick10", "3.2 h", 2)]
CELL_M2 = 125.0 ** 2
FOODS = ["leaf", "wood", "seed", "litter", "carrion", "kill"]


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


def line_chart(title, subtitle, series, fmt=None, ymax=None, log=False):
    """series: (label, xs, ys, slot or None for the control, dashed)."""
    fig, ax = plt.subplots(figsize=(6.4, 2.6))
    for label, xs, ys, slot, dashed in series:
        ax.plot(xs, ys, color=INK if slot is None else SERIES[slot], linewidth=1.8, label=label, linestyle="--" if dashed else "-")
    ax.set_xlabel("year (bodies sown in year 40)", loc="right")
    if log:
        ax.set_yscale("log")
    else:
        ax.set_ylim(0, ymax)
        ax.yaxis.set_major_locator(MaxNLocator(4))
    ax.yaxis.set_major_formatter(fmt or kfmt)
    ax.margins(x=0)
    legend_above(ax, len(series))
    return figure(title, subtitle, to_svg(fig))


def stacked(title, subtitle, xs, layers):
    """layers: (label, ys, slot), in kt a year."""
    fig, ax = plt.subplots(figsize=(6.4, 2.6))
    ax.stackplot(xs, [ys for _, ys, _ in layers], labels=[l for l, _, _ in layers], colors=[SERIES[s] for _, _, s in layers], linewidth=0)
    ax.set_xlabel("year (bodies sown in year 40)", loc="right")
    ax.yaxis.set_major_locator(MaxNLocator(4))
    ax.yaxis.set_major_formatter(kfmt)
    ax.margins(x=0)
    legend_above(ax, len(layers))
    return figure(title, subtitle, to_svg(fig))


# Hand-written mechanism diagram: a meeting, from the chase to the carrion.
DIAGRAM = """
<figure class="diagram">
<svg viewBox="0 0 720 230" role="img" aria-label="A chaser arrives by its speed against the other's, its front presses the face it meets, tissue that fails lies as carrion in the cell and is eaten by whoever stands there" style="max-width:100%;height:auto;display:block">
<defs><marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="currentColor"/></marker>
<marker id="arra" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="var(--s1)"/></marker></defs>
<g fill="none" stroke="currentColor" stroke-width="1.3" font-size="12" font-family="system-ui, sans-serif">
  <rect x="14" y="70" width="150" height="64" rx="6"/>
  <text x="89" y="96" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">sees (up to 500 m)</text>
  <text x="89" y="116" text-anchor="middle" fill="currentColor" stroke="none">a pull and a press</text>
  <path d="M164,102 L208,102" marker-end="url(#arr)"/>
  <rect x="210" y="70" width="150" height="64" rx="6"/>
  <text x="285" y="96" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">chases</text>
  <text x="285" y="116" text-anchor="middle" fill="currentColor" stroke="none">arrives if faster</text>
  <text x="285" y="30" text-anchor="middle" fill="currentColor" stroke="none">time = gap (v + u cos a) / (v&#178; - u&#178;)</text>
  <path d="M285,38 L285,64" stroke-dasharray="2 3"/>
  <path d="M360,102 L404,102" marker-end="url(#arr)"/>
  <rect x="406" y="70" width="150" height="64" rx="6"/>
  <text x="481" y="96" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">presses a face</text>
  <text x="481" y="116" text-anchor="middle" fill="currentColor" stroke="none">pressure &gt; strength?</text>
  <text x="520" y="54" text-anchor="middle" fill="currentColor" stroke="none">fails at power / strength, m&#179; a second</text>
  <path d="M556,102 L600,102" stroke="var(--s1)" marker-end="url(#arra)"/>
  <rect x="602" y="70" width="104" height="64" rx="6" stroke="var(--s1)" stroke-width="2"/>
  <text x="654" y="96" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">carrion</text>
  <text x="654" y="116" text-anchor="middle" fill="currentColor" stroke="none">of the cell</text>
  <path d="M654,134 L654,176 L96,176 L96,138" stroke="var(--s1)" marker-end="url(#arra)"/>
  <text x="375" y="168" text-anchor="middle" fill="var(--s1)" stroke="none">eaten by whoever stands there: 0.4-0.8% of the diet</text>
  <text x="654" y="204" text-anchor="middle" fill="currentColor" stroke="none">rots in days</text>
  <path d="M654,180 L654,190" stroke-dasharray="2 3"/>
</g>
</svg>
<figcaption>Figure 1. A meeting inside one update. The face met is the other's back if it fled, its front if it came on, a side otherwise; strength is the leaf's law. The blue path is the food web the law was built for.</figcaption>
</figure>
"""

TEXT = {
    "tldr": """Bodies now live in metres and seconds and meet by one law of contact. The machinery works: ledgers
close, catches and broken faces happen every year. The world does not stand: the eaters strip the land to a
hundredth of its producers in ten years, flesh stays under 1% of the diet, and two lines of one size hold every
island. Next is the plan's turn: what holds the eaters.""",
    "question": """Since e106 the bodies lived on a planet, in cells and updates, with nothing to eat them; on a
small world they stripped the land (e107). This pilot puts bodies on the islands with every law in metres and
seconds, and lets them meet. It asks whether that world stands, not whether a law is good.""",
    "world": """A body senses within a reach, steers by weighted pulls, and walks its speed times the time. A second
evaluator gives each body it sees a pull and a press. A body holds about <code>S</code> kg of animals: a clutch is
carried, then hatches as one brood.""",
    "runs": """<code>isles1</code> (410 km2 of land), bodies sown in year 40, to year 70, <code>S</code> 4,000 kg,
one seed, at three lengths of the bodies' update. A first pilot at <code>S</code> 400 kg was stopped in its second
year at 556,000 bodies.""",
    "v1": "Water, both nutrients and the living's matter with the carrion close to 2.4e-12.",
    "v2": "Bodies live to year 70, but the land's producers are 0.7-4% of the world without bodies and cover 21-52% of the land.",
    "v3": "Faces fail in every year of two runs (in the third the pressers die out by year 62); flesh is 0.4-0.8% of the diet.",
    "v4": "A body holds 0.36-0.71 S, so the number of bodies follows the animals' weight.",
    "v5": "The bodies' matter is 1.6 times at 64 minutes and 3.1 times at 3.2 hours (line: 1.5); the update stays 19 minutes.",
    "h31": "3.1 The eaters strip the land and then live on what is left",
    "p31": """The bodies' weight rises to 75,000-128,000 t in two to four years, eating a stock of litter nothing
else was taking, then the wood and the seed. What the producers fix falls by 64-86%, and the bodies settle at a
tenth of their peak, taking three quarters of that. A consumer that finds food by sweeping a path has no density
below which food is safe.""",
    "h32": "3.2 Bodies break each other, and nothing lives on it",
    "p32": """Catches and failed faces are counted from the first year, so the law engages. But a kill lies in the
cell for all, a gut passes 0.5% of a body's mass an update, and litter is everywhere: bodies with flesh over a
tenth of their diet never hold 0.7% of the matter.""",
    "h33": "3.3 One size, two lines, every island",
    "p33": """Of 256 founders, two are left from year 50, both on all eight islands. Bodies over 1 kg grown held up
to 38% of the matter early and none after ten years: what remains is swarms of the default 0.1 kg. A body walks
450-1,900 km a year, so the sea parts nothing.""",
    "discussion": """<p>The meeting law was to be the brake on the eaters. It is not, and thirty years of one seed
cannot say whether hunters would arise later; they can say the land does not wait for them. The plan named this
turn before the pilot: the producers' side of the cycle.</p>
<p>Read from the code and the outcome, not tested: dead matter is fully digestible and decays only once a year;
wood and the seed bank are in reach of any body; and small bodies in swarms are fed where a large one starves.</p>
<p>The scale chosen in #126 assumed 8.8-20 t of animals a km2. Here it is 180-310 t at the peak and 16-48 t on a
bare land, so what a body stands for is open again - after the eaters are held, since the weight depends on what
holds them. The three update lengths differ, but with one run each that is not separated from chance.</p>""",
    "conclusion": """The bodies' machinery stays in e110's crate; nothing goes to <code>base/</code> until a world
stands with it. The next piece is designed from the top: what, in the real world, keeps eaters from stripping the
land, and which of it this world lacks.""",
}


def main():
    logs = {r: rows(os.path.join(RESULTS, "pilot", f"{r}_log.csv")) for r, _, _ in RUNS}
    sizes = rows(os.path.join(RESULTS, "sizes.csv"))
    pilot = rows(os.path.join(RESULTS, "pilot.csv"))
    control = rows(CONTROL)
    yr = lambda log: [int(x["year"]) for x in log if int(x["year"]) >= 35]
    col = lambda log, f: [f(x) for x in log if int(x["year"]) >= 35]
    kt = lambda x, k: float(x[k]) * CELL_M2 / 1e6
    charts = {}
    charts["land"] = line_chart(
        "The land's producers", "kg a m2 of land. Dashed: the same world without bodies (e109). A line at the dashed one would be a land not eaten.",
        [(lab, yr(logs[r]), col(logs[r], lambda x: float(x["land_biomass"])), s, False) for r, lab, s in RUNS]
        + [("no bodies", [int(x["year"]) for x in control if 35 <= int(x["year"]) <= 70], [float(x["land_biomass"]) for x in control if 35 <= int(x["year"]) <= 70], None, True)],
    )
    charts["matter"] = line_chart(
        "The bodies' matter", "Thousand tonnes of animals, dry. A flat line after the peak is what the eaten land carries.",
        [(lab, yr(logs[r]), col(logs[r], lambda x: kt(x, "body_matter")), s, False) for r, lab, s in RUNS],
    )
    charts["gpp"] = line_chart(
        "What the producers fix", "Thousand tonnes a year, land and sea. A fall is the eaters cutting their own food's source.",
        [(lab, yr(logs[r]), col(logs[r], lambda x: kt(x, "gpp")), s, False) for r, lab, s in RUNS],
    )
    t1 = [x for x in logs["tick1"] if int(x["year"]) >= 40]
    charts["diet"] = stacked(
        "What the bodies eat (update 19 min)", "Thousand tonnes a year by food. Flesh (carrion and kills) is the thin top band.",
        [int(x["year"]) for x in t1],
        [("litter", [kt(x, "ate_litter") for x in t1], 0), ("wood", [kt(x, "ate_wood") for x in t1], 1), ("leaf and seed", [kt(x, "ate_leaf") + kt(x, "ate_seed") for x in t1], 2),
         ("flesh", [kt(x, "ate_carrion") + kt(x, "ate_kill") for x in t1], 4)],
    )
    after = lambda log: [x for x in log if int(x["year"]) >= 41]
    charts["breaks"] = line_chart(
        "Faces that failed", "Contacts a year in which pressure passed a face's strength. Zero is a world where no body breaks another.",
        [(lab, [int(x["year"]) for x in after(logs[r])], [float(x["breaks"]) for x in after(logs[r])], s, False) for r, lab, s in RUNS],
    )
    prun = lambda r: [x for x in pilot if x["run"] == r]
    charts["flesh"] = line_chart(
        "Flesh in the diet", "Share of all the bodies eat that is carrion or kills. The run's hypothesis for a food web was 10%.",
        [(lab, [int(x["year"]) for x in prun(r)], [float(x["flesh_share"]) for x in prun(r)], s, False) for r, lab, s in RUNS],
        fmt=lambda y, _p: f"{y:.1%}",
    )
    srun = lambda r: [x for x in sizes if x["run"] == r]
    charts["lines"] = line_chart(
        "Founders' lines alive", "Of 256 genomes sown. One line is a world of one founder's descendants.",
        [(lab, [int(x["year"]) for x in srun(r)], [int(x["lines"]) for x in srun(r)], s, False) for r, lab, s in RUNS],
    )
    charts["big"] = line_chart(
        "Matter in bodies over 1 kg grown", "Share of the bodies' matter. Zero is a world of one size, the default 0.1 kg.",
        [(lab, [int(x["year"]) for x in srun(r)], [float(x["over_1kg"]) for x in srun(r)], s, False) for r, lab, s in RUNS],
        fmt=lambda y, _p: f"{y:.0%}",
    )

    def last(r, k, n=10):
        v = prun(r)[-n:]
        return sum(float(x[k]) for x in v) / len(v)

    peak = lambda r, k: max(float(x[k]) for x in prun(r))
    srow = lambda name, f: "<tr><td>" + name + "</td>" + "".join(f"<td>{f(r)}</td>" for r, _, _ in RUNS) + "</tr>"
    yv = lambda r, y, k: next(float(x[k]) for x in sizes if x["run"] == r and int(x["year"]) == y)
    summary = "".join([
        srow("bodies, the peak", lambda r: f"{peak(r, 'bodies'):,.0f}"),
        srow("bodies, the last ten years", lambda r: f"{last(r, 'bodies'):,.0f}"),
        srow("their matter, the peak (t)", lambda r: f"{peak(r, 'matter_t'):,.0f}"),
        srow("their matter, the last ten years (t)", lambda r: f"{last(r, 'matter_t'):,.0f}"),
        srow("a body holds (kg; S = 4,000)", lambda r: f"{last(r, 'kg_a_body'):,.0f}"),
        srow("the land's producers (kg a m2; no bodies: 1.75-1.83)", lambda r: f"{last(r, 'land_biomass'):.3f}"),
        srow("the land they cover", lambda r: f"{last(r, 'land_cover'):.0%}"),
        srow("eaten of the producers' fixing", lambda r: f"{last(r, 'eaten_of_gpp'):.0%}"),
        srow("flesh in the diet", lambda r: f"{last(r, 'flesh_share'):.1%}"),
        srow("faces failed, year 45 / year 70", lambda r: f"{next(float(x['breaks']) for x in prun(r) if x['year'] == '45'):,.0f} / {float(prun(r)[-1]['breaks']):,.0f}"),
        srow("founders' lines, year 41 / year 70", lambda r: f"{yv(r, 41, 'lines'):.0f} / {yv(r, 70, 'lines'):.0f}"),
        srow("a year: the dearest / the last ten (s)", lambda r: f"{peak(r, 's_year'):.0f} / {last(r, 's_year'):.0f}"),
        srow("worst ledger", lambda r: f"{max(float(x['err']) for x in prun(r)):.1e}"),
    ])
    T = TEXT
    prov = "".join(f"<tr><td>{html.escape(r['what'])}</td><td>{html.escape(r['value'])}</td></tr>" for r in rows(os.path.join(RESULTS, "provenance.csv")))
    p1 = rows(os.path.join(RESULTS, "pilot1", "pilot.csv"))
    first = "".join(
        f"<tr><td>{x['run']}</td><td>{x['year']}</td><td>{int(x['bodies']):,}</td><td>{float(x['matter_t']):,.0f}</td><td>{float(x['kg_a_body']):.0f}</td><td>{float(x['eaten_of_gpp']):.0%}</td><td>{float(x['s_year']):,.0f}</td></tr>"
        for x in p1
    )
    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>e110 bodies that meet - Report</title>
<style>{CSS}</style>
</head>
<body>
<main>
<h1>e110: bodies in metres and seconds, and bodies that meet</h1>
<p class="sub">Experiment report - 2026-10-06 - rung 3's pilot on the islands (#123): three runs of 70 years, bodies sown in year 40</p>

<section class="tldr">
<h2>TL;DR</h2>
<p>{T['tldr']}</p>
</section>

<h2>1. Question</h2>
<p>{T['question']}</p>
<ol>
  <li><strong>The ledgers close</strong> - to 1e-9, with the carrion.</li>
  <li><strong>The world stands</strong> - bodies alive in year 70, producers on half the land.</li>
  <li><strong>Meetings happen</strong> - catches, failed faces and kills every year; flesh is eaten.</li>
  <li><strong>The grain holds</strong> - a body holds 0.2-2 S.</li>
  <li><strong>The update may be lengthened</strong> - levels within a factor 1.5 at 64 minutes and 3.2 hours.</li>
</ol>

<h2>2. The world</h2>
<p>{T['world']}</p>
{DIAGRAM}
<p><strong>Runs.</strong> {T['runs']}</p>
<ul class="measures">
  <li><strong>Matter</strong> - dry weight of the animals the bodies stand for.</li>
  <li><strong>Failed face</strong> - a contact where the front's pressure passed the face's strength.</li>
  <li><strong>Flesh</strong> - carrion and kills eaten, of everything eaten.</li>
  <li><strong>Founder's line</strong> - the descendants of one sown genome.</li>
</ul>

<h2>3. Results</h2>
<div class="tw"><table><thead><tr><th>the last ten years unless said</th>{"".join(f"<th>{lab}</th>" for _, lab, _ in RUNS)}</tr></thead><tbody>{summary}</tbody></table></div>
<ol class="verdicts">
<li><span class="verdict">Yes</span> {T['v1']}</li>
<li><span class="verdict no">No</span> {T['v2']}</li>
<li><span class="verdict partly">Partly</span> {T['v3']}</li>
<li><span class="verdict">Yes</span> {T['v4']}</li>
<li><span class="verdict no">No</span> {T['v5']}</li>
</ol>

<h3>{T['h31']}</h3>
<div class="grid2">
{charts['land']}
{charts['matter']}
{charts['gpp']}
{charts['diet']}
</div>
<p>{T['p31']}</p>

<h3>{T['h32']}</h3>
<div class="grid2">
{charts['breaks']}
{charts['flesh']}
</div>
<p>{T['p32']}</p>

<h3>{T['h33']}</h3>
<div class="grid2">
{charts['lines']}
{charts['big']}
</div>
<p>{T['p33']}</p>

<h2>4. Discussion</h2>
{T['discussion']}

<h2>5. Conclusion and next step</h2>
<p>{T['conclusion']}</p>

<h2>Appendix: data</h2>
<p>Readings in <code>results/pilot.csv</code> and <code>results/sizes.csv</code> (written by <code>pilot.py</code>), the
logs and the lines in <code>results/pilot/</code>; the body censuses stay on the Ubuntu machine. Build:
<code>uv run python experiments/e110_meet/report.py</code>.</p>
<div class="tw"><table><thead><tr><th>what was read</th><th>value</th></tr></thead><tbody>{prov}</tbody></table></div>
<details><summary>The first pilot (S = 400 kg), stopped in its second year</summary><div class="tw"><table><thead><tr><th>run</th><th>year</th><th>bodies</th><th>matter (t)</th><th>kg a body</th><th>eaten of fixing</th><th>a year (s)</th></tr></thead><tbody>{first}</tbody></table></div></details>
</main>
</body>
</html>
"""
    out = os.path.join(HERE, "report.html")
    with open(out, "w") as fh:
        fh.write(page)
    words = len(" ".join(str(v) for v in T.values()).split())
    print(f"wrote {out} ({os.path.getsize(out)//1024} KB), {words} words of text")


if __name__ == "__main__":
    main()
