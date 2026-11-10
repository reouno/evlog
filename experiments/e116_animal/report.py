#!/usr/bin/env python3
"""Build report.html for this experiment.

Charts: matplotlib, exported as SVG and inlined. Diagram: hand-written SVG.
Run from the repo root: uv run python experiments/eNNN_name/report.py
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
th:first-child, td:first-child { text-align: left; } td { white-space: nowrap; }
th { color: var(--ink2); font-weight: 600; }
.tw { overflow-x: auto; }
details { margin: 8px 0; } summary { cursor: pointer; color: var(--ink2); }
.verdicts { list-style: none; padding: 0; margin: 12px 0 0; } .verdicts li { margin: 4px 0; }
.verdict { display: inline-block; padding: 1px 8px; border-radius: 4px; font-size: 12.5px; font-weight: 600; background: rgba(12,163,12,0.12); color: #0ca30c; }
.verdict.no { background: rgba(208,59,59,0.12); color: #e66767; }
.verdict.partly { background: rgba(250,178,25,0.15); color: #fab219; }
"""

# Hand-written mechanism diagram. Label every arrow; currentColor for lines and text;
# var(--s1) for the one element the argument hinges on. Keep 10-15px between text and lines.
DIAGRAM = """
<figure class="diagram">
<svg viewBox="0 0 770 300" role="img" aria-label="Each animal's next decision is the earliest of a stride, its patch, ten minutes, a one-second tick near another, or another coming into sight" style="max-width:100%;height:auto;display:block">
<defs><marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="currentColor"/></marker></defs>
<g fill="none" stroke="currentColor" stroke-width="1.2" font-size="12" font-family="system-ui, sans-serif">
  <rect x="20" y="110" width="150" height="70" rx="6"/>
  <text x="95" y="140" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">event queue</text>
  <text x="95" y="158" text-anchor="middle" fill="currentColor" stroke="none">earliest decision first</text>
  <rect x="222" y="110" width="186" height="70" rx="6"/>
  <text x="315" y="140" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">one animal decides</text>
  <text x="315" y="158" text-anchor="middle" fill="currentColor" stroke="none">senses, sets velocity, bites</text>
  <line x1="170" y1="145" x2="220" y2="145" marker-end="url(#arr)"/>
  <text x="196" y="135" text-anchor="middle" fill="currentColor" stroke="none">pop</text>
  <line x1="408" y1="145" x2="483" y2="145" marker-end="url(#arr)"/>
  <text x="446" y="135" text-anchor="middle" fill="currentColor" stroke="none">earliest of</text>
  <line x1="485" y1="40" x2="485" y2="248"/>
  <line x1="485" y1="40" x2="500" y2="40"/><line x1="485" y1="88" x2="500" y2="88"/>
  <line x1="485" y1="136" x2="500" y2="136"/><line x1="485" y1="190" x2="500" y2="190"/>
  <line x1="485" y1="248" x2="500" y2="248"/>
  <rect x="500" y="20" width="255" height="40" rx="6"/>
  <text x="512" y="44" fill="currentColor" stroke="none">moving: 20 m stride / speed</text>
  <rect x="500" y="68" width="255" height="40" rx="6"/>
  <text x="512" y="92" fill="currentColor" stroke="none">standing: its patch eaten (10-600 s)</text>
  <rect x="500" y="116" width="255" height="40" rx="6"/>
  <text x="512" y="140" fill="currentColor" stroke="none">nothing happens: 600 s</text>
  <rect x="500" y="164" width="255" height="52" rx="6" stroke="var(--s1)" stroke-width="2"/>
  <text x="512" y="186" fill="currentColor" stroke="none" font-weight="600">close: a 1 s tick while a body</text>
  <text x="512" y="204" fill="currentColor" stroke="none">x1.5 or x2/3 its mass is near</text>
  <rect x="500" y="228" width="255" height="40" rx="6"/>
  <text x="512" y="252" fill="currentColor" stroke="none">meeting: another enters its sight</text>
  <polyline points="315,180 315,218 120,218 120,184" marker-end="url(#arr)"/>
  <text x="218" y="208" text-anchor="middle" fill="currentColor" stroke="none">push its next decision</text>
  <polyline points="627,268 627,288 60,288 60,184" marker-end="url(#arr)"/>
  <text x="340" y="278" text-anchor="middle" fill="currentColor" stroke="none">notice: the other's decision comes earlier</text>
</g>
</svg>
<figcaption>Figure 1. What sets an animal's next decision: whichever comes first. "Near" is within 10 body lengths + 5 m.
The one-second tick (blue) is what most of the decisions below are. A notice is one animal's decision that moves another's earlier.</figcaption>
</figure>
"""

# Every sentence of the report's prose, so that its words can be counted against the skill's budgets.
TEXT = {
    "tldr": """A decision costs about 1 us, but the placeholder mind decides far more often than hoped: 2,366
times an animal-day in the first population, 7,583 in the second, against 27-274 hoped. Almost all of the second's
decisions are the one-second tick taken beside a body of another size. 1e4 animals cost 2.6-5.6 core-hours a year.
Next: pace that tick by how fast the other closes, and find why a decision's cost grows with N.""",
    "question": """e115's body was some 300,000 small animals and a step 44 minutes, so nothing on the screen was an
animal. #135 rebuilds the world at an animal's size: one body one animal from 1 kg, grass a field, time continuous.
This crate holds no law to keep; it asks what that size costs and how it looks.""",
    "h1": "Decisions paced by events cost 1e4-1e5 an animal-year at a few us each: 1e4 animals run a year in well under a core-hour.",
    "h2": "At a fixed density, the cost an animal-year is flat in N.",
    "h3": "Animals at their own size over 5 m ground read as animals on a landscape.",
    "world": """An island with a hill and trees on 5 m cells; grass regrows, worked out when read. An
animal has a mass (1-200 kg), energy and a linear controller from its senses to a velocity and a bite, which kills at
contact anything under 2/3 its mass. It decides at its own time from one queue (Figure 1).""",
    "runs": """Ubuntu, one thread each, seed 1. Benches: 1k, 10k and 30k fixed animals at 400 a km2, bites and
deaths off, 60 days (10k and 30k stopped after 6 days and 1). live: 300 founders on 9.6 km2 of land for two years.
live2: the same after the second look's fixes, one year. Four viewer recordings.""",
    "m1": "decisions an animal-day - the cost driver; 27-274 was hoped.",
    "m2": "close share - decisions taken as the one-second tick.",
    "m3": "us a decision - wall time of one decision.",
    "m4": "notices a decision - other animals whose next decision it moves.",
    "m5": "animal-years a core-hour - what one core affords.",
    "v1": "hypothesis 1: a decision costs about 1 us, but 2,366-7,583 decisions an animal-day is 9-28 times the hope.",
    "v2": "hypothesis 2: from 1k to 30k at one density a decision rises from 1.65 to 5.5 us, as notices rise 0.3 to 1.6.",
    "v3": "hypothesis 3: near the eye an animal reads as an animal on 5 m ground; in the first look grass tufts hid it from 200 m.",
    "r1": """The count an animal-day barely moves with N, but a bench is a world of endless chases: with bites off,
a hunter follows its prey at a tick a second for 60 days, so 37-51% of all decisions are ticks, and no bench number is
the cost of a living world. What grows is the price of each decision, with the notices it sends.""",
    "r2": """Both islands hold a population. live peaks at 1,696 on day 150 and then holds at 926-1,470; live2,
whose animals crop while walking and less from a short sward, holds at 186-291 until day 150 and rises to 394. In
both, hunters fall to 1-2 within a year: a placeholder mind that does not search does not live on flesh.""",
    "r3": """The second look's fixes tripled the count, and not through its short walking legs: 97% of live2's
decisions are ticks, against 5% in live. The tick fires beside any body 1.5 times heavier or a third lighter, hunter or
not, and the second look lengthened bodies (0.25 to 0.4 m kg^-1/3), widening that radius. Whether that or the new
grazing gait does it is not separated.""",
    "gallery": "No gallery of bodies: every animal is the same placeholder shape, a trunk on four legs.",
    "d1": """The price of a decision is not the problem; how often it is taken is. At these rates a world of 1e4
animals for 300 years costs 771 (live) to 1,669 (live2) core-hours on one thread. Most of the excess is the fixed
one-second tick, taken beside a grazer of another size as beside a hunter. A tick paced by the time the other takes to
close would leave grazers side by side on their own clocks.""",
    "d2": """Hypothesis 2 fails at the notices, which grow with N at a fixed density. Why is not known; the meeting
test on 50 m buckets is the place to look before the next crate.""",
    "d3": """What this does not show: the cost of a mind that searches or learns, of climate or water, or of several
threads. live and live2 are one seed each.""",
    "conclusion": """No for the count, no for the scaling, partly for the screen. A decision is cheap, so the world at
an animal's size is affordable only if the mind decides less often: pace the near tick by how fast a threat closes,
find why notices grow with N, and plan for several threads.""",
}


def words():
    return sum(len(v.split()) for v in TEXT.values())


def t(k):
    return html.escape(" ".join(TEXT[k].split()))


def load_sum(name):
    with open(os.path.join(HERE, f"results/{name}_sum.csv")) as f:
        return {r["what"]: float(r["value"]) for r in csv.DictReader(f)}


def rolling(ys, n=10):
    out = []
    for i in range(len(ys)):
        w = ys[max(0, i - n + 1):i + 1]
        out.append(sum(w) / len(w))
    return out


def scatter_n(title, subtitle, ns, ys, ylabel_fmt=None, ylim0=True):
    fig, ax = new_axes("animals (N, log scale)")
    ax.plot(ns, ys, color=SERIES[2], linewidth=1.6, marker="o", markersize=5, label="benches, 400 a km2")
    ax.set_xscale("log")
    ax.set_xticks(ns, [f"{n/1000:.0f}k" for n in ns])
    ax.minorticks_off()
    ax.margins(x=0.08)
    if ylim0:
        ax.set_ylim(0, max(ys) * 1.15)
    ax.yaxis.set_major_locator(MaxNLocator(4))
    ax.yaxis.set_major_formatter(ylabel_fmt or kfmt)
    legend_above(ax, 1)
    return figure(title, subtitle, to_svg(fig))


def day_chart(title, subtitle, series, pct=False):
    fig, ax = new_axes("day")
    for label, xs, ys, slot in series:
        ax.plot(xs, ys, color=SERIES[slot], linewidth=1.4, label=label)
    ax.set_ylim(0, (1.1 if pct else max(v for _, _, ys, _ in series for v in ys) * 1.12))
    ax.yaxis.set_major_locator(MaxNLocator(4))
    ax.yaxis.set_major_formatter((lambda y, _p: f"{y:.0%}") if pct else kfmt)
    legend_above(ax, len(series))
    return figure(title, subtitle, to_svg(fig))


def main():
    logs = {n: load_csv(f"results/{n}_log.csv") for n in
            ("bench1k", "bench10k", "bench30k", "live", "live2", "look_close", "look_lapse", "look2_close", "look2_lapse")}
    sums = {n: load_sum(n) for n in ("bench1k", "live", "live2", "look_close", "look_lapse", "look2_close", "look2_lapse")}

    # one row of the summary per run, every number from its log (whole run) or its summary
    rows = {}
    for n, d in logs.items():
        dec = sum(d["decisions"])
        animal_days = sum(dd / r for dd, r in zip(d["decisions"], d["dec_per_animal_day"]))
        rows[n] = {
            "days": round(sums[n]["days"]) if n in sums else len(d["day"]),
            "animals": (f"{d['animals'][0]:,.0f}" if n.startswith("bench")
                        else f"{min(d['animals']):,.0f}-{max(d['animals']):,.0f}"),
            "dpad": dec / animal_days,
            "close": sum(d["close"]) / dec,
            "us": sum(u * x for u, x in zip(d["us_per_decision"], d["decisions"])) / dec,
            "notices": sum(d["notices"]) / dec,
            "ay_ch": (animal_days / 365) / (sum(d["secs"]) / 3600),
        }
    for n, s in sums.items():  # the summaries hold the whole-run numbers; prefer them where they exist
        rows[n]["dpad"] = s["decisions_per_animal_day"]
        rows[n]["us"] = s["us_per_decision"]
        rows[n]["ay_ch"] = s["animal_years_per_core_hour"]
    note = {"bench10k": " (stopped)", "bench30k": " (stopped)"}
    table_rows = "".join(
        f"<tr><td>{n}{note.get(n, '')}</td><td>{r['days']}</td><td>{r['animals']}</td><td>{r['dpad']:,.0f}</td>"
        f"<td>{r['close']:.0%}</td><td>{r['us']:.2f}</td><td>{r['notices']:.2g}</td><td>{r['ay_ch']:,.0f}</td></tr>"
        for n, r in rows.items())

    ns = [logs[n]["animals"][0] for n in ("bench1k", "bench10k", "bench30k")]
    b = [rows[n] for n in ("bench1k", "bench10k", "bench30k")]
    c_bench = [
        scatter_n("Decisions an animal-day against N", "Flat would mean each animal decides as often in a large world as in a small one.",
                  ns, [r["dpad"] for r in b]),
        scatter_n("Microseconds a decision against N", "Flat would mean hypothesis 2 holds; a rise is the cost of the notices a decision sends.",
                  ns, [r["us"] for r in b], ylabel_fmt=lambda y, _p: f"{y:g}"),
    ]
    L, L2 = logs["live"], logs["live2"]
    c_pop = [
        day_chart("Animals on the island", "300 founders each; a line that holds above zero is a population that stands.",
                  [("live", L["day"], L["animals"], 0), ("live2 (second look)", L2["day"], L2["animals"], 1)]),
        day_chart("Hunters among them", "Animals whose genes make them bite; near zero means flesh does not feed this mind.",
                  [("live", L["day"], L["hunters"], 0), ("live2 (second look)", L2["day"], L2["hunters"], 1)]),
    ]
    c_cost = [
        day_chart("Decisions an animal-day", "10-day mean. The hope was 27-274; every line far above it is the mind deciding too often.",
                  [("live", L["day"], rolling(L["dec_per_animal_day"]), 0),
                   ("live2 (second look)", L2["day"], rolling(L2["dec_per_animal_day"]), 1)]),
        day_chart("Share of decisions that are the 1 s tick", "Daily. Near 100% means almost every decision is taken beside a body of another size.",
                  [("live", L["day"], [c / d for c, d in zip(L["close"], L["decisions"])], 0),
                   ("live2 (second look)", L2["day"], [c / d for c, d in zip(L2["close"], L2["decisions"])], 1)], pct=True),
    ]

    cols = ["day", "animals", "hunters", "mass_mean", "births", "hunger", "killed", "dec_per_animal_day", "close", "us_per_decision"]
    tables = data_table(cols, {"live (every 30th day)": L, "live2 (every 30th day)": L2}, every=30)
    tables += data_table(cols, {"bench10k (every day)": logs["bench10k"], "bench30k (its one day)": logs["bench30k"]}, every=1)
    tables += data_table(cols, {"bench1k (every 10th day)": logs["bench1k"]}, every=10)

    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>e116 Animal Scale - Report</title>
<style>{CSS}</style>
</head>
<body>
<main>
<h1>e116: what does a world at the size of an animal cost?</h1>
<p class="sub">Experiment report - 2026-11-11 - a speed prototype for #135: three benches, two populations, four recordings, seed 1</p>

<section class="tldr">
<h2>TL;DR</h2>
<p>{t("tldr")}</p>
</section>

<h2>1. Question</h2>
<p>{t("question")}</p>
<ol>
  <li><strong>Cheap decisions.</strong> {t("h1")}</li>
  <li><strong>Flat in N.</strong> {t("h2")}</li>
  <li><strong>Animals on screen.</strong> {t("h3")}</li>
</ol>

<h2>2. The world</h2>
<p>{t("world")}</p>
{DIAGRAM}
<p><strong>Runs.</strong> {t("runs")} Every simulated day we record:</p>
<ul class="measures">
  <li><strong>{t("m1").split(" - ")[0]}</strong> - {t("m1").split(" - ")[1]}</li>
  <li><strong>{t("m2").split(" - ")[0]}</strong> - {t("m2").split(" - ")[1]}</li>
  <li><strong>{t("m3").split(" - ")[0]}</strong> - {t("m3").split(" - ")[1]}</li>
  <li><strong>{t("m4").split(" - ")[0]}</strong> - {t("m4").split(" - ")[1]}</li>
  <li><strong>{t("m5").split(" - ")[0]}</strong> - {t("m5").split(" - ")[1]}</li>
</ul>

<h2>3. Results</h2>
<div class="tw"><table>
<thead><tr><th>run</th><th>days</th><th>animals</th><th>decisions an animal-day</th><th>close share</th><th>us a decision</th><th>notices a decision</th><th>animal-years a core-hour</th></tr></thead>
<tbody>{table_rows}</tbody></table></div>
<ol class="verdicts">
<li><span class="verdict no">No</span> {t("v1")}</li>
<li><span class="verdict no">No</span> {t("v2")}</li>
<li><span class="verdict partly">Partly</span> {t("v3")}</li>
</ol>
<p>{t("gallery")}</p>

<h3>3.1 A decision is cheap, but its price grows with N</h3>
<div class="grid2">
{"".join(c_bench)}
</div>
<p>{t("r1")}</p>

<h3>3.2 A population holds; hunters do not</h3>
<div class="grid2">
{"".join(c_pop)}
</div>
<p>{t("r2")}</p>

<h3>3.3 The second look decides three times as often, nearly all of it the one-second tick</h3>
<div class="grid2">
{"".join(c_cost)}
</div>
<p>{t("r3")}</p>

<h2>4. Discussion</h2>
<p>{t("d1")}</p>
<p>{t("d2")}</p>
<p>{t("d3")}</p>

<h2>5. Conclusion and next step</h2>
<p>{t("conclusion")}</p>

<h2>Appendix: data</h2>
<p>Rows of the daily logs; the full data is in <code>results/*_log.csv</code> (one row a day) and
<code>results/*_sum.csv</code> (whole-run totals). In the table above, bench10k and bench30k rows come from their logs, the rest
from the summaries; "animals" is the founders for a bench and the range over the run otherwise. The recordings
(<code>look*</code>) are in the table for their cost only. Build this report with
<code>uv run python experiments/e116_animal/report.py</code>.</p>
{tables}
</main>
</body>
</html>
"""
    out = os.path.join(HERE, "report.html")
    with open(out, "w") as f:
        f.write(page)
    print(f"wrote {out} ({os.path.getsize(out)//1024} KB), TEXT {words()} words")


if __name__ == "__main__":
    main()
