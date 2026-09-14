#!/usr/bin/env python3
"""Build report.html for e069 (life history from the genome, foundation stage C, seventh step, #83).

Charts: matplotlib, exported as SVG and inlined. Diagram: hand-written SVG.
Run from the repo root after history.py: uv run python experiments/e069_history/report.py
"""
import csv
import html
import io
import math
import os

import matplotlib
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from matplotlib.ticker import FuncFormatter, MaxNLocator

matplotlib.use("svg")

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4"]  # fixed slot order
RUN_COLOR = {"e067": SERIES[0], "e069": SERIES[1]}
MEDIUM_COLOR = {"land": SERIES[3], "surface": SERIES[2], "bottom": SERIES[4], "shore": SERIES[0]}  # e067's and e068's
KIND_COLOR = {1: SERIES[0], 2: SERIES[1], 3: SERIES[3], 4: SERIES[2]}  # hard, muscle, sensor, gut: the viewer's
RUNS = ["e067", "e069"]
LABEL = {"e067": "e067 (constants)", "e069": "e069 (from the genome)"}
VALUES = ("breed", "share", "store")
CENTRE = {"breed": 0.1, "share": 0.5, "store": 5.0}
NAME = {"breed": "energy to breed per unit of mass", "share": "share of energy given to a child", "store": "fat held per unit of mass"}
LOGS = {"e067": os.path.join(ROOT, "experiments", "e067_breath", "results", "c1225_life9_breath0.01_log.csv"),
        "e069": os.path.join(HERE, "results", "c1225_life9_history_log.csv")}

INK = "#898781"
plt.rcParams.update({
    "svg.fonttype": "none", "font.family": "sans-serif", "font.size": 9, "text.color": INK,
    "axes.edgecolor": INK, "axes.labelcolor": INK, "axes.facecolor": "none", "axes.spines.top": False,
    "axes.spines.right": False, "axes.spines.left": False, "axes.grid": True, "axes.grid.axis": "y",
    "grid.color": INK, "grid.alpha": 0.25, "grid.linewidth": 0.8, "xtick.color": INK, "ytick.color": INK,
    "ytick.left": False, "legend.frameon": False, "legend.fontsize": 9, "figure.facecolor": "none",
    "savefig.transparent": True,
})
DASHED = (0, (3, 2))


# ---------- data ----------

def rows(name, path=None):
    with open(path or os.path.join(HERE, "results", name + ".csv")) as f:
        return list(csv.DictReader(f))


def num(r):
    out = {}
    for k, v in r.items():
        try:
            out[k] = float(v)
        except (TypeError, ValueError):
            out[k] = v
    return out


R = {r["run"]: num(r) for r in rows("runs")}
M = [num(r) for r in rows("media")]
G = [num(r) for r in rows("groups")]
K = rows("kinds")
L = {run: [num(r) for r in rows(None, path)] for run, path in LOGS.items()}


# ---------- charts ----------

def to_svg(fig):
    buf = io.StringIO()
    fig.savefig(buf, format="svg", bbox_inches="tight", pad_inches=0.05)
    plt.close(fig)
    return buf.getvalue()


def legend_above(ax, n, **kw):
    ax.legend(loc="lower left", bbox_to_anchor=(0, 1.0), ncols=n, handlelength=1.4, borderaxespad=0, columnspacing=1.2, **kw)


def figure(title, subtitle, svg):
    return f"""
<figure class="fig">
  <figcaption><strong>{html.escape(title)}</strong><span>{html.escape(subtitle)}</span></figcaption>
  {svg}
</figure>"""


def percent(ax, axis="y"):
    (ax.yaxis if axis == "y" else ax.xaxis).set_major_formatter(lambda v, _p: f"{v:.0%}")


kfmt = FuncFormatter(lambda x, _p: f"{x / 1000:.0f}k" if x else "0")


def values_chart(title, subtitle, value):
    """A value's mean over time by medium in e069, with its constant (e067) dashed."""
    fig, ax = plt.subplots(figsize=(6.4, 2.6))
    log = L["e069"]
    xs = [r["step"] for r in log]
    for m in ("land", "surface", "bottom"):
        ax.plot(xs, [r[f"{value}_{m}"] if r[f"pop_{m}"] > 0 else math.nan for r in log], color=MEDIUM_COLOR[m], linewidth=1.6, label=m)
    ax.axhline(CENTRE[value], color=INK, linewidth=1, linestyle=DASHED, label="constant (e067)")
    ax.set_ylim(CENTRE[value] * 0.5, CENTRE[value] * 2)
    ax.set_yscale("log", base=2)
    ax.set_yticks([CENTRE[value] * f for f in (0.5, 1, 2)], [f"{CENTRE[value] * f:g}" for f in (0.5, 1, 2)])
    ax.minorticks_off()
    ax.xaxis.set_major_formatter(kfmt)
    ax.set_xlabel("step", loc="right")
    ax.set_ylabel(NAME[value])
    legend_above(ax, 4)
    return figure(title, subtitle, to_svg(fig))


def log_chart(title, subtitle, key, ylabel, pct=False):
    """A log column over time in the runs that log it."""
    fig, ax = plt.subplots(figsize=(6.4, 2.6))
    for run in (r for r in RUNS if key in L[r][0]):
        ax.plot([r["step"] for r in L[run]], [r[key] for r in L[run]], color=RUN_COLOR[run], linewidth=1.6, label=LABEL[run])
    ax.set_ylim(0, None)
    ax.yaxis.set_major_locator(MaxNLocator(4))
    if pct:
        percent(ax)
    else:
        ax.yaxis.set_major_formatter(kfmt)
    ax.xaxis.set_major_formatter(kfmt)
    ax.set_xlabel("step", loc="right")
    ax.set_ylabel(ylabel)
    legend_above(ax, 2)
    return figure(title, subtitle, to_svg(fig))


def groups_chart(title, subtitle):
    """Each lineage group's water median over its land median, per value, sized by its grown bodies; the shuffle's
    largest mean gap dashed."""
    fig, ax = plt.subplots(figsize=(6.4, 2.8))
    gs = [g for g in G if g["run"] == "e069"]
    n = max((g["land"] + g["water"] for g in gs), default=1)
    for j, v in enumerate(VALUES):
        xs = [j + (i - len(gs) / 2) * 0.35 / max(len(gs), 1) for i in range(len(gs))]
        ax.scatter(xs, [math.expm1(g[v]) for g in gs], s=[12 + 120 * (g["land"] + g["water"]) / n for g in gs],
                   color=[MEDIUM_COLOR["surface"] if g["light"] else MEDIUM_COLOR["bottom"] for g in gs], alpha=0.8, linewidths=0, zorder=3)
        lim = R["e069"][f"gap_{v}_null_max"]
        ax.plot([j - 0.3, j + 0.3], [lim, lim], color=INK, linewidth=1, linestyle=DASHED)
        ax.plot([j - 0.3, j + 0.3], [-lim, -lim], color=INK, linewidth=1, linestyle=DASHED)
    ax.axhline(0, color=INK, linewidth=1)
    ax.set_xticks(range(len(VALUES)), ["breeding energy", "child's share", "fat store"])
    ax.yaxis.set_major_locator(MaxNLocator(4))
    percent(ax)
    ax.set_ylabel("water over land, less 1")
    handles = [Patch(color=MEDIUM_COLOR["surface"], label="lighter than water"), Patch(color=MEDIUM_COLOR["bottom"], label="denser")]
    legend_above(ax, 2, handles=handles)
    return figure(title, subtitle, to_svg(fig))


def grouped(title, subtitle, series, ylabel, line=None, pct=False, ncols=3, height=2.6, integer=False):
    """One group per run, one bar per series: (label, key or function of a run's row, colour)."""
    fig, ax = plt.subplots(figsize=(6.4, height))
    width = 0.8 / len(series)
    for j, (label, key, colour) in enumerate(series):
        vals = [key(R[r]) if callable(key) else R[r][key] for r in RUNS]
        ax.bar([i - 0.4 + width * (j + 0.5) for i in range(len(RUNS))], vals, width=width * 0.92, color=colour, label=label)
    if line is not None:
        ax.axhline(line, color=INK, linewidth=1, linestyle=DASHED)
    ax.set_xticks(range(len(RUNS)), [LABEL[r] for r in RUNS])
    ax.set_ylim(0, None)
    ax.yaxis.set_major_locator(MaxNLocator(4, integer=integer))
    if pct:
        percent(ax)
    ax.set_ylabel(ylabel)
    legend_above(ax, ncols)
    return figure(title, subtitle, to_svg(fig))


def short(k):
    diet, tooth, roams, medium = k["kind"].split(" / ")
    return f"{diet}, {roams}, {medium}" + (", tooth" if tooth == "tooth" else "")


def kinds_chart(title, subtitle, run):
    ks = sorted((k for k in K if k["run"] == run and float(k["share"]) >= 0.02), key=lambda k: float(k["share"]))
    fig, ax = plt.subplots(figsize=(6.4, 0.9 + 0.3 * len(ks)))
    for j, k in enumerate(ks):
        medium = k["kind"].split(" / ")[3]
        ax.barh(j, float(k["share"]), color=MEDIUM_COLOR[medium], alpha=1.0 if k["held"] == "True" else 0.4, height=0.72)
    ax.set_yticks(range(len(ks)), [short(k) for k in ks])
    ax.axvline(0.05, color=INK, linewidth=1, linestyle=DASHED)
    percent(ax, "x")
    ax.set_xlabel("share of the grown bodies", loc="right")
    ax.grid(axis="y", visible=False)
    ax.grid(axis="x", visible=True)
    handles = [Patch(color=MEDIUM_COLOR[m], label=m) for m in ("surface", "bottom", "land", "shore")]
    legend_above(ax, 4, handles=handles)
    return figure(title, subtitle, to_svg(fig))


def gallery(picks, caption, run="e069"):
    here = {k["kind"]: k for k in K if k["run"] == run}
    cards = []
    for kind, title, what in picks:
        k = here[kind]
        side, cells = int(k["side"]), k["cells"]
        u = 88 / side
        rects = "".join(f'<rect x="{(i % side) * u:.2f}" y="{(i // side) * u:.2f}" width="{u * 0.9:.2f}" height="{u * 0.9:.2f}" fill="{KIND_COLOR[int(c)]}"/>'
                        for i, c in enumerate(cells) if c != "0")
        food = ", ".join(f"{name} {float(k[col]):.0%}" for name, col in (("grass", "grass"), ("algae", "algae"), ("litter", "detritus"), ("flesh", "meat")) if float(k[col]) >= 0.05)
        life = f"breeds at 2 + {float(k['median_breed']):.3f} x mass, gives {float(k['median_share']):.0%}, stores {float(k['median_store']):.1f}"
        cards.append(f"""<figure class="card"><svg viewBox="-1 -1 89 89" width="120" height="120" role="img" aria-label="{html.escape(title)}"><rect x="-1" y="-1" width="89" height="89" fill="var(--cell)"/>{rects}<line x1="-1" y1="-0.5" x2="88" y2="-0.5" stroke="var(--ink2)" stroke-width="1.5" stroke-dasharray="3 2"/></svg>
<figcaption><strong>{html.escape(title)}</strong><br>{float(k['share']):.0%} of grown bodies, {k['censuses']} of 6 censuses; {k['forms']} forms in {k['lineages']} lineages<br>born with {float(k['born_size']):.0f} blocks, density {float(k['density']):.2f}; eats {food}<br>{life} (medians)<br>{html.escape(what)}</figcaption></figure>""")
    return f"""<figure class="diagram"><div class="cards">{"".join(cards)}</div>
<figcaption>{html.escape(caption)}</figcaption></figure>"""


def table(name, cols, keep=lambda r: True):
    body = "".join("<tr>" + "".join(f"<td>{html.escape(str(r.get(c, ''))[:60])}</td>" for c in cols) + "</tr>" for r in rows(name) if keep(r))
    return (f"<details><summary>results/{name}.csv</summary><div class='tw'><table><thead><tr>"
            + "".join(f"<th>{c}</th>" for c in cols) + f"</tr></thead><tbody>{body}</tbody></table></div></details>")


# ---------- page ----------

CSS = f"""
:root {{
  --surface: #fcfcfb; --page: #f9f9f7; --ink: #0b0b0b; --ink2: #52514e; --grid: #e1e0d9; --border: rgba(11,11,11,0.10);
  --s1: {SERIES[0]}; --cell: #f1f0ea;
}}
@media (prefers-color-scheme: dark) {{
  :root:not([data-theme="light"]) {{
    --surface: #1a1a19; --page: #0d0d0d; --ink: #ffffff; --ink2: #c3c2b7; --grid: #2c2c2a; --border: rgba(255,255,255,0.10);
    --s1: #3987e5; --cell: #262624;
  }}
}}
:root[data-theme="dark"] {{
  --surface: #1a1a19; --page: #0d0d0d; --ink: #ffffff; --ink2: #c3c2b7; --grid: #2c2c2a; --border: rgba(255,255,255,0.10);
  --s1: #3987e5; --cell: #262624;
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
@media (max-width: 480px) {{ .grid2 {{ grid-template-columns: 1fr; }} }}
.grid2 > .fig:only-child {{ max-width: 470px; }}
.fig {{ margin: 0; background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 14px 14px 8px; }}
.fig svg {{ width: 100%; height: auto; display: block; font-family: system-ui, -apple-system, "Segoe UI", sans-serif; }}
figcaption strong {{ display: block; font-size: 15px; }}
figcaption span {{ display: block; color: var(--ink2); font-size: 13px; min-height: 2.6em; margin-bottom: 6px; }}
.diagram {{ margin: 12px 0; background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 12px 16px 8px; color: var(--ink); }}
.diagram figcaption {{ color: var(--ink2); font-size: 13px; margin-top: 4px; }}
.cards {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 16px; }}
.card {{ margin: 0; display: grid; grid-template-columns: 120px 1fr; gap: 12px; align-items: start; }}
.card figcaption {{ font-size: 12.5px; color: var(--ink2); margin: 0; }} .card figcaption strong {{ display: inline; font-size: 13px; color: var(--ink); }}
.measures {{ columns: 2; column-gap: 24px; max-width: none; padding-left: 20px; }} .measures li {{ break-inside: avoid; }}
@media (max-width: 640px) {{ .measures {{ columns: 1; }} }}
table {{ border-collapse: collapse; font-size: 13.5px; font-variant-numeric: tabular-nums; }}
th, td {{ padding: 6px 12px; text-align: right; border-bottom: 1px solid var(--grid); }}
th:first-child, td:first-child {{ text-align: left; }}
th {{ color: var(--ink2); font-weight: 600; }}
.tw {{ overflow-x: auto; }}
details {{ margin: 8px 0; }} summary {{ cursor: pointer; color: var(--ink2); }}
.verdicts {{ list-style: none; padding: 0; margin: 12px 0 0; }} .verdicts li {{ margin: 4px 0; }}
.verdict {{ display: inline-block; padding: 1px 8px; border-radius: 4px; font-size: 12.5px; font-weight: 600; background: rgba(12,163,12,0.12); color: #006300; }}
.verdict.no {{ background: rgba(208,59,59,0.12); color: #a12b2b; }}
:root[data-theme="dark"] .verdict {{ color: #0ca30c; }} :root[data-theme="dark"] .verdict.no {{ color: #e66767; }}
@media (prefers-color-scheme: dark) {{ :root:not([data-theme="light"]) .verdict {{ color: #0ca30c; }} :root:not([data-theme="light"]) .verdict.no {{ color: #e66767; }} }}
"""


def box(x, y, w, h, title, lines, accent=False, dashed=False):
    stroke = ' stroke="var(--s1)" stroke-width="2"' if accent else ' stroke-dasharray="4 3"' if dashed else ""
    out = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6"{stroke}/>',
           f'<text x="{x + w / 2}" y="{y + 22}" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">{title}</text>']
    for i, line in enumerate(lines):
        out.append(f'<text x="{x + w / 2}" y="{y + 42 + 17 * i}" text-anchor="middle" fill="currentColor" stroke="none">{line}</text>')
    return "".join(out)


def label(x, y, text, anchor="middle"):
    return f'<text x="{x}" y="{y}" text-anchor="{anchor}" fill="currentColor" stroke="none">{text}</text>'


DIAGRAM = f"""
<figure class="diagram">
<svg viewBox="0 0 760 330" role="img" aria-label="The genome's gene network sets three values of a life, which decide when a body breeds, what its child gets, and how much fat it keeps" style="max-width:100%;height:auto;display:block">
<defs><marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="currentColor"/></marker></defs>
<g fill="none" stroke="currentColor" stroke-width="1.2" font-size="12" font-family="system-ui, sans-serif">
  {box(10, 110, 180, 92, "Genome", ["genes settle a network", "(no position)"])}
  {box(285, 10, 200, 76, "Energy to breed", ["2 + b x mass", "b: 0.05-0.2 (was 0.1)"], accent=True)}
  {box(285, 118, 200, 76, "Child's share", ["s of the energy", "s: 0.25-1 (was 0.5)"], accent=True)}
  {box(285, 226, 200, 76, "Fat store", ["up to f x mass", "f: 2.5-10 (was 5)"], accent=True)}
  <line x1="190" y1="140" x2="283" y2="52" marker-end="url(#arr)"/>
  <line x1="190" y1="156" x2="283" y2="156" marker-end="url(#arr)"/>
  <line x1="190" y1="172" x2="283" y2="262" marker-end="url(#arr)"/>
  {label(240, 140, "column")}
  {box(570, 40, 180, 110, "A birth", ["child gets s x energy;", "parent pays its blocks", "from the rest", "(no room: it lies down)"])}
  <line x1="485" y1="48" x2="568" y2="80" marker-end="url(#arr)"/>{label(526, 42, "when")}
  <line x1="485" y1="156" x2="568" y2="116" marker-end="url(#arr)"/>{label(530, 178, "how much")}
  {box(570, 206, 180, 96, "Hunger", ["upkeep paid into fat;", "fat pays what energy", "cannot; over f: soil"])}
  <line x1="485" y1="264" x2="568" y2="254" marker-end="url(#arr)"/>{label(526, 244, "buffer")}
</g>
</svg>
<figcaption>Figure 1. Three values a child inherits. Each is its old constant times 2 to a power from -1 to 1, read from its own column of the gene table. What a block costs, upkeep and wear stay laws.</figcaption>
</figure>
"""

# The text of the page: kept here to count its words against the skill's budget.
TEXT = {
    "tldr": ("The energy to breed, the child's share and the fat store are now read from the genome on e067's "
             "world. In 100,000 steps they barely move: medians 0.099, 0.48 and 6.0 against the constants 0.1, 0.5 and 5. Inside a "
             "lineage the water and the land differ by 3%. Kinds held at every census fall from 4 to 2 as one lineage takes 52%. "
             "Not kept for now; seeds would tell the values from the run's changed course."),
    "question": ("Principle 2 asks that traits come out of what a child inherits with variation. Three values of how a body lives were "
                 "constants we wrote: it breeds at 2 + 0.1 x its mass, gives a child half its energy, and holds 5 fat per unit of mass. "
                 "e067's lineages hold an open water form and a closed land form, which could not part in how they breed or store. "
                 "Set before the run:"),
    "hyp": ["The media part in life history: inside a lineage the water's median of a value differs from the land's by 15% or more, beyond a shuffle of the medium.",
            "The store runs up: fat costs nothing to hold, so the median store reaches 8.",
            "The world keeps its kinds: 3 or more held by birth form at every census (e067: 4)."],
    "world": ("e067's world at breath 0.01, unchanged but for three columns of the gene table. Each value is its old constant times 2 "
              "to a power from -1 to 1. Random genomes start at x0.81-1.25. The mate distance and the mutation rate stay fixed."),
    "runs": ("c1225, seed 9, 100,000 steps on one core (28 minutes). Control: e067's run, reused. With the values held at the constants "
             "the crate reproduced e067's first 10,000 steps exactly. Over the second half we read:"),
    "measures": [
        ("Values", "each body's three values, by the medium it stands in."),
        ("Water over land", "inside each lineage group with 20+ grown bodies in both, against five shuffles of the medium."),
        ("Kinds by birth form", "e068's census: kinds holding 5% of the grown bodies, held at every census."),
        ("Fat fill", "fat over the body's store; low means the store rarely binds."),
    ],
    "v1": "2.4%, 3.3% and 3.2% for breed, share and store, in 17 groups holding 74% of the grown bodies: above the shuffle's 0.7%, far under 15%.",
    "v2": "the median store is 5.97 (x1.19); it reached 5.55 by step 10,000 and stayed.",
    "v3": "2 kinds held (e067 4); 4.2 at a census against 4.0 with the medium shuffled.",
    "h1": "3.1 The values barely move",
    "r1": ("The breeding energy and the share stay at their start. Only the store rises, and it rose in the first 10,000 steps, while "
           "the start's bodies starved from 17,000 to 11,000. Fat is free to hold here, but it fills 5-12% of a store, so there is little "
           "to select. Dense bodies on land hold the most (7.8 against 6.0), a difference between their few lineages."),
    "h2": "3.2 Inside a lineage the water and the land live alike",
    "r2": ("Every lineage group sits within a few percent of zero on every value. The water's grown bodies have placed more children "
           "(3.4 against 2.4 on land) and are older (median 739 steps against 540), with the same values: food and room set how often "
           "a body breeds, not the energy it waits for."),
    "h3": "3.3 One lineage in every medium, and two kinds held",
    "r3": ("Lineage 957 holds 52% of the grown bodies, 23% on land, 49% at the surface and 29% on the bottom. Its forms keep to no "
           "medium: the roaming algae and litter eaters e067 held as kinds are shore kinds here. Two dense land kinds reach 5% in five "
           "of six censuses, and the land holds 1,278 grown bodies a census (e067 779)."),
    "gallery": "The commonest intact birth body of the largest form of four kinds in e069, with the kind's median values. The dashed line is the front.",
    "d1": ("Selection on these values is weak over 100,000 steps. A child differs from its parents by about two bases, the start holds "
           "values within 25% of the constants, and in a world where half the children find no room, when a body breeds is set by "
           "the crowd more than by the energy it waits for."),
    "d2": ("The fall in kinds comes with a different winner more than with different values: lineage 957 breeds at the constants' "
           "energy and share within 5%, and its water forms did not sort by medium as lineage 908's did in e067. Reading the values changed every body at the "
           "start, and so the course of the run. One seed cannot tell that from an effect of the values."),
    "d3": ("Not shown: other seeds, c1236, longer runs, a price on fat (it has no weight and no upkeep), and the mate distance and "
           "mutation rate from the genome."),
    "conclusion": ("Not kept as stage C's default for now, by the rule set before the run: 2 kinds held, under the line of 3. The values "
                   "barely moved and did not part the media. Proposed next on #83: the same pair on two more seeds (4 runs, 4 cores for "
                   "30 minutes), which also gives stage C its first spread over seeds; then #84, senses from sensor blocks."),
}
# (kind in e069, title, what the shape does)
GALLERY_PICKS = [
    ("plant / no tooth / roams / shore", "An open cup of gut",
     "Gut on top, muscle below: most blocks face the outside, so it breathes in water and eats as it roams."),
    ("plant / no tooth / stays / shore", "A solid square of gut",
     "No muscle: it sits where it was born, on land or on the bottom."),
    ("plant / no tooth / stays / land", "Gut walled in muscle",
     "A ring of muscle closes the gut to the dry air; at density 2 its faces break lighter ones."),
    ("mixed / no tooth / stays / land", "Muscle in front at density 2",
     "Ten muscles press on what it meets and break it: kills are 31% of its intake."),
]
VERDICTS = [(False, "1, the media part in life history", "v1"), (False, "2, the store runs up", "v2"), (False, "3, the world keeps its kinds", "v3")]


def main():
    c, h = R["e067"], R["e069"]
    table_rows = [
        ("Bodies: mean (lowest-highest)", lambda r: f"{r['pop']:,.0f} ({r['pop_min']:,.0f}-{r['pop_max']:,.0f})"),
        ("Grown bodies a census", lambda r: f"{r['grown']:,.0f}"),
        ("Energy to breed per unit of mass: median (10-90%)", lambda r: f"{r['breed']:.3f} ({r['breed_p10']:.3f}-{r['breed_p90']:.3f})"),
        ("Child's share", lambda r: f"{r['share']:.2f} ({r['share_p10']:.2f}-{r['share_p90']:.2f})"),
        ("Fat per unit of mass", lambda r: f"{r['store']:.1f} ({r['store_p10']:.1f}-{r['store_p90']:.1f})"),
        ("Water over land inside lineages: breed, share, store (shuffled max)",
         lambda r: "-" if r["run"] == "e067" else ", ".join(f"{r[f'gap_{v}']:.1%}" for v in VALUES) + " (" + ", ".join(f"{r[f'gap_{v}_null_max']:.1%}" for v in VALUES) + ")"),
        ("<strong>Kinds by birth form</strong>: mean (lowest-highest); held", lambda r: f"{r['form']:.1f} ({r['form_low']:.0f}-{r['form_high']:.0f}); {r['form_held']:.0f}"),
        ("Medium shuffled: mean; held", lambda r: f"{r['null_medium']:.1f}; {r['null_medium_held']:.0f}"),
        ("Kinds per lineage (e060)", lambda r: f"{r['lineage_e060']:.1f}"),
        ("Lineages alive (top lineage's share)", lambda r: f"{r['lineages']:.1f} ({r['top_lineage']:.0%})"),
        ("Births per body per 1,000 steps; median age at death", lambda r: f"{r['births_per_body']:.2f}; {r['age_death_p50']:.0f}"),
        ("Deaths: hunger / thirst / broken / suffocation", lambda r: f"{r['deaths_hunger']:.0%} / {r['deaths_thirst']:.0%} / {r['deaths_broken']:.0%} / {r['deaths_suffocation']:.1%}"),
        ("Moves blocked; children with no room", lambda r: f"{r['blocked']:.0%}; {r['no_room']:.0%}"),
        ("Kills' share of intake", lambda r: f"{r['kills']:.0%}"),
    ]
    tbl = "".join(f"<tr><td>{name}</td>" + "".join(f"<td>{f(R[run])}</td>" for run in RUNS) + "</tr>" for name, f in table_rows)

    charts_values = [values_chart(f"The {NAME[v]} over the run", "Mean over the bodies in each medium; dashed, e067's constant. A line on the dashes is a value selection leaves where we put it.", v) for v in VALUES]
    charts_fill = [log_chart("Fat fills a small part of the store", "Mean fat over each body's store. A line far under 100% is a store that rarely binds.", "fat_fill", "fat over the store", pct=True)]
    charts_groups = [groups_chart("Inside a lineage, the water against the land",
                                  "Each dot is a lineage group with 20+ grown bodies in both; its water median over its land median. Dashed: the largest mean gap with the medium shuffled.")]
    charts_count = [
        grouped("Kinds by birth form", "Mean kinds holding 5% of the grown bodies over six censuses, and the same with the medium shuffled inside lineages. Dashed: stage C's 4.",
                [("by birth form", "form", SERIES[2]), ("medium shuffled", "null_medium", SERIES[3]), ("per lineage (e060)", "lineage_e060", SERIES[1])], "kinds", line=4),
        kinds_chart("e069's kinds", "Grown bodies by kind over six censuses, coloured by medium. Solid: held at every census. Dashed: 5%.", "e069"),
    ]

    count = lambda v: len((" ".join(v) if isinstance(v, list) and v and isinstance(v[0], str) else " ".join(" ".join(t) for t in v) if isinstance(v, list) else v).split())
    words = sum(count(v) for v in TEXT.values()) + sum(len(p[2].split()) for p in GALLERY_PICKS)
    print(f"TEXT: {words} words")
    for k, v in TEXT.items():
        print(f"  {k}: {count(v)}")

    t = lambda k: html.escape(TEXT.get(k, "TODO"))
    gal = gallery(GALLERY_PICKS, TEXT.get("gallery", "")) if GALLERY_PICKS else ""
    hyp = "".join(f"<li>{html.escape(x)}</li>" for x in TEXT.get("hyp", []))
    measures = "".join(f"<li><strong>{html.escape(k)}</strong> - {html.escape(v)}</li>" for k, v in TEXT.get("measures", []))
    verdicts = "".join(f"<li><span class=\"verdict{'' if yes else ' no'}\">{'Yes' if yes else 'No'}</span> {html.escape(head)}: {t(key)}</li>" for yes, head, key in VERDICTS)
    head = "".join(f"<th>{html.escape(LABEL[r])}</th>" for r in RUNS)
    appendix = "\n".join([
        table("media", ["run", "medium", "grown", "breed", "breed_p10", "breed_p90", "share", "share_p10", "share_p90", "store", "store_p10", "store_p90", "fat_fill", "kids"]),
        table("groups", ["run", "lineage", "light", "land", "water", "breed", "share", "store"]),
        table("kinds", ["run", "kind", "share", "censuses", "held", "forms", "lineages", "born_size", "density", "median_breed", "median_share", "median_store", "grass", "algae", "detritus", "meat", "land", "surface", "bottom"]),
        table("lineages", ["run", "lineage", "grown", "land", "surface", "bottom", "breed", "share", "store", "born_size", "density"]),
    ])
    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>e069 life history from the genome - Report</title>
<style>{CSS}</style>
</head>
<body>
<main>
<h1>e069: life history from the genome</h1>
<p class="sub">Experiment report - 2026-09-15 - e067's world with the energy to breed, the child's share and the fat store read from the genome; c1225, seed 9, 100,000 steps (foundation stage C, seventh step, #83)</p>

<section class="tldr">
<h2>TL;DR</h2>
<p>{t("tldr")}</p>
</section>

<h2>1. Question</h2>
<p>{t("question")}</p>
<ol>{hyp}</ol>

<h2>2. The world</h2>
<p>{t("world")}</p>
{DIAGRAM}
<p><strong>Runs.</strong> {t("runs")}</p>
<ul class="measures">{measures}</ul>

<h2>3. Results</h2>
<div class="tw"><table>
<thead><tr><th>Second half of the run</th>{head}</tr></thead>
<tbody>{tbl}</tbody></table></div>
<ol class="verdicts">{verdicts}</ol>

<h3>{t("h1")}</h3>
<div class="grid2">{charts_values[0]}{charts_values[1]}</div>
<div class="grid2">{charts_values[2]}{charts_fill[0]}</div>
<p>{t("r1")}</p>

<h3>{t("h2")}</h3>
<div class="grid2">{charts_groups[0]}</div>
<p>{t("r2")}</p>

<h3>{t("h3")}</h3>
<div class="grid2">{"".join(charts_count)}</div>
<p>{t("r3")}</p>
{gal}

<h2>4. Discussion</h2>
<p>{t("d1")}</p>
<p>{t("d2")}</p>
<p>{t("d3")}</p>

<h2>5. Conclusion and next step</h2>
<p>{t("conclusion")}</p>

<h2>Appendix: data</h2>
<p>The values by medium, each lineage group's water over land (log ratios) and every kind with its median values are in <code>experiments/e069_history/results/</code>; one row per run in <code>runs.csv</code>. Build with <code>uv run python experiments/e069_history/history.py</code>, then <code>report.py</code>.</p>
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
