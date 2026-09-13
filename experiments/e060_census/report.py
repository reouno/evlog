#!/usr/bin/env python3
"""Build report.html for e060, the census of ways of living (#71).

Charts: matplotlib, exported as SVG and inlined. Diagram: hand-written SVG.
Run from the repo root after census.py (both passes): uv run python experiments/e060_census/report.py
The gallery reads e055's compressed snapshots through `zstd -dc`.
"""
import csv
import glob
import html
import io
import json
import os
import statistics
import subprocess
import sys
from collections import Counter, defaultdict

import matplotlib
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.ticker import MaxNLocator

matplotlib.use("svg")

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import census as C  # noqa: E402

SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4"]
KIND_COLOR = {1: SERIES[0], 2: SERIES[1], 3: SERIES[3], 4: SERIES[2]}
INK = "#898781"
plt.rcParams.update({
    "svg.fonttype": "none", "font.family": "sans-serif", "font.size": 9, "text.color": INK,
    "axes.edgecolor": INK, "axes.labelcolor": INK, "axes.facecolor": "none", "axes.spines.top": False,
    "axes.spines.right": False, "axes.spines.left": False, "axes.grid": True, "axes.grid.axis": "y",
    "grid.color": INK, "grid.alpha": 0.25, "grid.linewidth": 0.8, "xtick.color": INK, "ytick.color": INK,
    "ytick.left": False, "legend.frameon": False, "legend.fontsize": 9, "figure.facecolor": "none",
    "savefig.transparent": True,
})


# ---------- data ----------

def rows(name):
    with open(os.path.join(HERE, "results", f"{name}.csv")) as f:
        return list(csv.DictReader(f))


def num(x):
    return float(x) if x not in ("", None) else None


def ranks(v):
    order = sorted(range(len(v)), key=lambda i: v[i])
    r = [0.0] * len(v)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and v[order[j + 1]] == v[order[i]]:
            j += 1
        for k in range(i, j + 1):
            r[order[k]] = (i + j) / 2
        i = j + 1
    return r


def spearman(x, y):
    rx, ry = ranks(x), ranks(y)
    mx, my = statistics.mean(rx), statistics.mean(ry)
    cov = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    return cov / (sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry)) ** 0.5


def pair_groups(pairs):
    """One entry per law and control: (class, what, law, control, verdict, verdict per lineage, seed rows)."""
    by = defaultdict(list)
    for r in pairs:
        by[(r["law"], r["control"])].append(r)
    return [(rs[0]["class"], rs[0]["what"], law, control, rs[0]["verdict"], rs[0]["verdict_lineage"], rs)
            for (law, control), rs in by.items()]


def numbers():
    runs, pairs, ways, sweep = rows("runs"), rows("pairs"), rows("ways"), rows("sweep")
    known = [r for r in runs if r["state"]]
    k = [num(r["kills_share"]) for r in known]
    N = {"runs": len(runs), "known": len(known)}
    N["rho_body"] = spearman(k, [num(r["ways"]) for r in known])
    N["rho_lineage"] = spearman(k, [num(r["ways_lineage"]) for r in known])
    for st in ("grazer", "hunter"):
        rs = [r for r in known if r["state"] == st]
        N[st + "_n"] = len(rs)
        N[st + "_body"] = statistics.mean(num(r["ways"]) for r in rs)
        N[st + "_lineage"] = statistics.mean(num(r["ways_lineage"]) for r in rs)
    N["low_kills"] = statistics.mean(num(r["ways"]) for r in known if num(r["kills_share"]) < 0.1)
    N["high_kills"] = statistics.mean(num(r["ways"]) for r in known if num(r["kills_share"]) >= 0.3)
    N["body_min"] = min(num(r["ways"]) for r in runs)
    N["body_max"] = max(num(r["ways"]) for r in runs)
    N["lin_min"] = min(num(r["ways_lineage"]) for r in runs)
    N["lin_max"] = max(num(r["ways_lineage"]) for r in runs)
    N["gap"] = statistics.mean(num(r["ways"]) - num(r["ways_lineage"]) for r in runs)
    groups = pair_groups(pairs)
    axis = [g for g in groups if g[0] == "axis"]
    other = [g for g in groups if g[0] != "axis"]
    N["axis_n"], N["other_n"] = len(axis), len(other)
    N["axis_body"] = sum(g[4] == "more" for g in axis)
    N["axis_lineage"] = sum(g[5] == "more" for g in axis)
    N["other_body"] = sum(g[4] != "more" for g in other)
    N["other_lineage"] = sum(g[5] != "more" for g in other)
    N["other_lineage_more"] = [g[2] for g in other if g[5] == "more"]
    holds = [int(s["frame holds"]) for s in sweep]
    N["sweep_min"], N["sweep_max"], N["settings"] = min(holds), max(holds), len(sweep)
    big = [w for w in ways if num(w["share"]) >= C.SHARE]
    tooth = [num(w["top_lineage_share"]) for w in big if "/ tooth" in w["way"]]
    N["tooth_top"] = statistics.median(tooth)
    by_run = defaultdict(dict)
    for w in big:
        if w.get("travel"):
            by_run[(w["run"], w["seed"])][w["way"]] = num(w["age"])
    ratio = [d[w] / d[w[:-5] + "stays"] for d in by_run.values() for w in d if w.endswith("roams") and w[:-5] + "stays" in d]
    N["roam_age"] = statistics.median(ratio)
    run = {(r["run"], r["seed"]): r for r in runs}
    isl = [run[("e059 islands", str(s))] for s in range(9, 15)]
    uni = [run[("e059 thin uniform", str(s))] for s in range(9, 15)]
    for key, rs in (("isl", isl), ("uni", uni)):
        N[key + "_body"] = statistics.mean(num(r["ways"]) for r in rs)
        N[key + "_lineage"] = statistics.mean(num(r["ways_lineage"]) for r in rs)
        N[key + "_hunter"] = sum(r["state"] == "hunter" for r in rs)
    # one lineage of the crowded world at sun 1, seed 9 (e058 is e055 byte for byte, with the birth shape)
    g = C.grown(C.load("e058 sun 1", 9)[100_000])
    lin = [r for r in g if r["lineage"] == "593"]
    N["l593_share"] = len(lin) / len(g)
    N["l593_ways"] = C.count(C.census(C.load("e058 sun 1", 9)[100_000]))
    fl = sorted(C.flesh_share(r) for r in lin)
    N["l593_q1"], N["l593_q3"] = fl[len(fl) // 4], fl[3 * len(fl) // 4]
    soft = [r for r in lin if not C.has_tooth(r)]
    N["l593_born_muscle"] = statistics.mean(float(r["born_muscle"]) for r in soft)
    N["l593_muscle"] = statistics.mean(float(r["muscle"]) for r in soft)
    return N, runs, pairs, groups, sweep, g


# ---------- charts ----------

def to_svg(fig):
    buf = io.StringIO()
    fig.savefig(buf, format="svg", bbox_inches="tight", pad_inches=0.05)
    plt.close(fig)
    return buf.getvalue()


def figure(title, subtitle, svg):
    return f"""
<figure class="fig">
  <figcaption><strong>{html.escape(title)}</strong><span>{html.escape(subtitle)}</span></figcaption>
  {svg}
</figure>"""


def legend_above(ax, n, handles=None):
    ax.legend(handles=handles, loc="lower left", bbox_to_anchor=(0, 1.0), ncols=n, handlelength=1.2, borderaxespad=0,
              columnspacing=1.2)


def scatter(title, subtitle, known, key, ylabel):
    fig, ax = plt.subplots(figsize=(6.4, 2.8))
    for st, slot in (("grazer", 2), ("hunter", 1)):
        rs = [r for r in known if r["state"] == st]
        ax.scatter([100 * num(r["kills_share"]) for r in rs], [num(r[key]) for r in rs], s=16, alpha=0.7,
                   color=SERIES[slot], edgecolors="none", label=f"{st} world ({len(rs)} runs)")
    ax.axvline(100 * C.HUNTER, color=INK, linewidth=0.8, linestyle="--")
    ax.set_xlabel("kills' share of what the world eats (%)", loc="right")
    ax.set_ylabel(ylabel)
    ax.set_ylim(0, 10.5)
    ax.yaxis.set_major_locator(MaxNLocator(4, integer=True))
    legend_above(ax, 2)
    return figure(title, subtitle, to_svg(fig))


def flesh_hist(title, subtitle, g):
    fig, ax = plt.subplots(figsize=(6.4, 2.6))
    lin = [C.flesh_share(r) for r in g if r["lineage"] == "593"]
    rest = [C.flesh_share(r) for r in g if r["lineage"] != "593"]
    bins = [i / 20 for i in range(21)]
    ax.hist(lin, bins=bins, color=SERIES[0], alpha=0.8, label=f"lineage 593 ({len(lin)} bodies)", edgecolor="none")
    ax.hist(rest, bins=bins, color=SERIES[2], alpha=0.6, label=f"every other lineage ({len(rest)})", edgecolor="none")
    for x in C.FLESH:
        ax.axvline(x, color=INK, linewidth=0.8, linestyle="--")
    ax.set_xlabel("flesh share of a grown body's lifetime intake", loc="right")
    ax.yaxis.set_major_locator(MaxNLocator(4))
    legend_above(ax, 2)
    return figure(title, subtitle, to_svg(fig))


def muscle_bars(title, subtitle, g):
    groups = [("593, tooth", [r for r in g if r["lineage"] == "593" and C.has_tooth(r)]),
              ("593, no tooth", [r for r in g if r["lineage"] == "593" and not C.has_tooth(r)]),
              ("others, no tooth", [r for r in g if r["lineage"] != "593" and not C.has_tooth(r)])]
    fig, ax = plt.subplots(figsize=(6.4, 2.6))
    xs = range(len(groups))
    for off, col, slot, label in ((-0.2, "born_muscle", 0, "muscle blocks at birth"), (0.2, "muscle", 1, "muscle blocks now")):
        ax.bar([x + off for x in xs], [statistics.mean(float(r[col]) for r in rs) for _, rs in groups], 0.38,
               color=SERIES[slot], label=label)
    ax.set_xticks(list(xs), [f"{name} (n={len(rs)})" for name, rs in groups])
    ax.yaxis.set_major_locator(MaxNLocator(4))
    legend_above(ax, 2)
    return figure(title, subtitle, to_svg(fig))


def diff_dots(title, subtitle, groups):
    fig, ax = plt.subplots(figsize=(4.8, 5.6))
    labels = []
    colors = {"same": SERIES[0], "g>h": SERIES[1], "h>g": SERIES[2], "?": INK}
    for i, (cls, what, law, control, v, vl, rs) in enumerate(groups):
        y = len(groups) - 1 - i
        labels.append((y, f"{law}  |  {control.split(' ', 1)[1]}"))
        for r in rs:
            a, b = r["law_state"], r["control_state"]
            kind = "?" if not a or not b else "same" if a == b else f"{b[0]}>{a[0]}"
            ax.scatter(num(r["law_ways"]) - num(r["control_ways"]), y, s=22, color=colors[kind], alpha=0.85,
                       edgecolors="none")
        if i < len(groups) - 1 and groups[i + 1][0] != cls and cls == "axis":
            ax.axhline(y - 0.5, color=INK, linewidth=0.8)
    ax.axvline(0, color=INK, linewidth=0.8)
    ax.set_yticks([y for y, _ in labels], [t for _, t in labels], fontsize=8)
    ax.grid(axis="x", alpha=0.25)
    ax.grid(axis="y", alpha=0)
    ax.set_xlabel("ways of living per body, law minus control (one dot per seed)", loc="right")
    handles = [Line2D([], [], marker="o", linestyle="", color=c, label=l) for l, c in
               (("same state", colors["same"]), ("into a hunter world", colors["g>h"]),
                ("out of a hunter world", colors["h>g"]), ("no kill log (e010-e012)", colors["?"]))]
    legend_above(ax, 2, handles)
    return figure(title, subtitle, to_svg(fig))


def e059_bars(title, subtitle, runs, key, ylabel):
    run = {(r["run"], r["seed"]): r for r in runs}
    seeds = list(range(9, 15))
    fig, ax = plt.subplots(figsize=(6.4, 2.6))
    for off, name, slot in ((-0.2, "e059 thin uniform", 0), (0.2, "e059 islands", 1)):
        ax.bar([i + off for i in range(len(seeds))], [num(run[(name, str(s))][key]) or 0 for s in seeds], 0.38,
               color=SERIES[slot], label=name.split(" ", 1)[1])
    ax.set_xticks(range(len(seeds)), [f"seed {s}" for s in seeds])
    ax.set_ylabel(ylabel)
    ax.yaxis.set_major_locator(MaxNLocator(4))
    legend_above(ax, 2)
    return figure(title, subtitle, to_svg(fig))


# ---------- gallery: the birth body most common in a lineage at step 100,000 ----------

def zlines(path):
    proc = subprocess.Popen(["zstd", "-dc", path], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
    yield from proc.stdout


def modal_bodies(seed, lineages):
    pre = glob.glob(os.path.join(C.EXP, "e055_span", "results", f"*_corner_motor_clock0.5_seed{seed}_long.jsonl.zst"))[0]
    last = None
    for line in zlines(pre):
        last = line
    frame = json.loads(last)
    ids = {lid: [a[2] for a in frame["agents"] if str(a[4]) == lid] for lid in lineages}
    need = {i for v in ids.values() for i in v}
    bodies = {}
    for line in zlines(pre.replace("_long.", "_bodies.")):
        d = json.loads(line)
        if d["id"] in need:
            bodies[d["id"]] = (int(d["side"]), d["cells"])
    return {lid: Counter(bodies[i] for i in ids[lid] if i in bodies).most_common(1)[0][0] for lid in lineages}


GALLERY = [(9, "593", "A hard front row with muscle behind it: the push breaks the face it meets."),
           (9, "850", "Gut around a knot of muscle, no hard block: nothing to break with or to resist."),
           (11, "1567", "Gut with muscle in one corner, the grazer world's commonest body."),
           (11, "1186", "Two rows of muscle before two rows of gut: a grazer that walks.")]


def gallery():
    cards = []
    shapes = {}
    for seed in {s for s, _, _ in GALLERY}:
        shapes.update({(seed, lid): b for lid, b in modal_bodies(seed, [l for s, l, _ in GALLERY if s == seed]).items()})
    for seed, lid, what in GALLERY:
        side, cells = shapes[(seed, lid)]
        rows_ = C.load("e055 clock 0.5", seed)[100_000]
        g = C.grown(rows_)
        lin = [r for r in g if r["lineage"] == lid]
        n_ways = C.count(C.census(lin)) if lin else 0
        u = 88 / side
        rects = "".join(f'<rect x="{(i % side) * u:.2f}" y="{(i // side) * u:.2f}" width="{u * 0.9:.2f}" '
                        f'height="{u * 0.9:.2f}" fill="{KIND_COLOR[int(ch)]}"/>' for i, ch in enumerate(cells) if ch != "0")
        cards.append(f"""<figure class="card"><svg viewBox="-1 -1 89 89" width="120" height="120" role="img" aria-label="lineage {lid}"><rect x="-1" y="-1" width="89" height="89" fill="var(--cell)"/>{rects}<line x1="-1" y1="-0.5" x2="88" y2="-0.5" stroke="var(--ink2)" stroke-width="1.5" stroke-dasharray="3 2"/></svg>
<figcaption><strong>Seed {seed}, lineage {lid}</strong><br>{len(lin) / len(g):.0%} of the grown bodies; flesh {statistics.median(C.flesh_share(r) for r in lin):.2f} (median); tooth {statistics.mean(C.has_tooth(r) for r in lin):.0%}; roams {statistics.mean(float(r['travel']) >= C.ROAM for r in lin):.0%}; its members fall into {n_ways} ways of living<br>{html.escape(what)}</figcaption></figure>""")
    return "".join(cards)


# ---------- page ----------

CSS = f"""
:root {{ --surface: #fcfcfb; --page: #f9f9f7; --ink: #0b0b0b; --ink2: #52514e; --grid: #e1e0d9; --border: rgba(11,11,11,0.10); --s1: {SERIES[0]}; --cell: #f1f0ea; }}
@media (prefers-color-scheme: dark) {{ :root:not([data-theme="light"]) {{ --surface: #1a1a19; --page: #0d0d0d; --ink: #ffffff; --ink2: #c3c2b7; --grid: #2c2c2a; --border: rgba(255,255,255,0.10); --s1: #3987e5; --cell: #262624; }} }}
:root[data-theme="dark"] {{ --surface: #1a1a19; --page: #0d0d0d; --ink: #ffffff; --ink2: #c3c2b7; --grid: #2c2c2a; --border: rgba(255,255,255,0.10); --s1: #3987e5; --cell: #262624; }}
* {{ box-sizing: border-box; }}
body {{ margin: 0; background: var(--page); color: var(--ink); font: 15px/1.55 system-ui, -apple-system, "Segoe UI", sans-serif; }}
main {{ max-width: 960px; margin: 0 auto; padding: 32px 20px 64px; }}
h1 {{ font-size: 26px; margin: 0 0 4px; }} h2 {{ font-size: 19px; margin: 40px 0 8px; }} h3 {{ font-size: 16px; margin: 24px 0 8px; }}
p, li {{ color: var(--ink); max-width: 72ch; }}
.sub {{ color: var(--ink2); margin: 0 0 24px; }}
.tldr {{ background: var(--surface); border: 1px solid var(--border); border-left: 4px solid var(--s1); border-radius: 8px; padding: 12px 18px; }}
.tldr h2 {{ margin: 0 0 6px; font-size: 15px; }} .tldr p {{ margin: 0; }}
.grid2 {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(420px, 1fr)); gap: 20px; }}
@media (max-width: 480px) {{ .grid2 {{ grid-template-columns: 1fr; }} }}
.grid2 > .fig:only-child {{ max-width: 560px; }}
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
.verdict.partly {{ background: rgba(250,178,25,0.15); color: #8a5a00; }}
:root[data-theme="dark"] .verdict.partly {{ color: #fab219; }}
@media (prefers-color-scheme: dark) {{ :root:not([data-theme="light"]) .verdict.partly {{ color: #fab219; }} }}
:root[data-theme="dark"] .verdict {{ color: #0ca30c; }} :root[data-theme="dark"] .verdict.no {{ color: #e66767; }}
@media (prefers-color-scheme: dark) {{ :root:not([data-theme="light"]) .verdict {{ color: #0ca30c; }} :root:not([data-theme="light"]) .verdict.no {{ color: #e66767; }} }}
"""

DIAGRAM = """
<figure class="diagram">
<svg viewBox="0 0 720 230" role="img" aria-label="A grown body is sorted by diet, tooth and range into one of twelve ways of living, counted per body and per lineage" style="max-width:100%;height:auto;display:block">
<defs><marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="currentColor"/></marker></defs>
<g fill="none" stroke="currentColor" stroke-width="1.2" font-size="12" font-family="system-ui, sans-serif">
  <rect x="10" y="62" width="130" height="56" rx="6"/>
  <text x="75" y="86" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">a grown body</text>
  <text x="75" y="104" text-anchor="middle" fill="currentColor" stroke="none">age 300 or more</text>
  <line x1="140" y1="80" x2="208" y2="30" marker-end="url(#arr)"/>
  <line x1="140" y1="90" x2="208" y2="90" marker-end="url(#arr)"/>
  <line x1="140" y1="100" x2="208" y2="150" marker-end="url(#arr)"/>
  <rect x="210" y="10" width="200" height="40" rx="6"/>
  <text x="310" y="35" text-anchor="middle" fill="currentColor" stroke="none">diet: flesh share &lt;1/3, mid, &gt;2/3</text>
  <rect x="210" y="70" width="200" height="40" rx="6"/>
  <text x="310" y="95" text-anchor="middle" fill="currentColor" stroke="none">tooth: hard tip, force 2 or more</text>
  <rect x="210" y="130" width="200" height="40" rx="6"/>
  <text x="310" y="155" text-anchor="middle" fill="currentColor" stroke="none">range: 8 cells from birthplace</text>
  <line x1="410" y1="30" x2="478" y2="80" marker-end="url(#arr)"/>
  <line x1="410" y1="90" x2="478" y2="90" marker-end="url(#arr)"/>
  <line x1="410" y1="150" x2="478" y2="100" marker-end="url(#arr)"/>
  <rect x="480" y="62" width="100" height="56" rx="6"/>
  <text x="530" y="86" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">1 of 12</text>
  <text x="530" y="104" text-anchor="middle" fill="currentColor" stroke="none">ways</text>
  <line x1="580" y1="80" x2="618" y2="45" marker-end="url(#arr)"/>
  <line x1="580" y1="100" x2="618" y2="135" marker-end="url(#arr)"/>
  <rect x="620" y="20" width="92" height="46" rx="6"/>
  <text x="666" y="40" text-anchor="middle" fill="currentColor" stroke="none">per body</text>
  <text x="666" y="56" text-anchor="middle" fill="currentColor" stroke="none">5% of grown</text>
  <rect x="620" y="112" width="92" height="46" rx="6" stroke="var(--s1)" stroke-width="2"/>
  <text x="666" y="132" text-anchor="middle" fill="currentColor" stroke="none">per lineage</text>
  <text x="666" y="148" text-anchor="middle" fill="currentColor" stroke="none">its commonest</text>
  <rect x="210" y="186" width="200" height="36" rx="6" stroke-dasharray="4 3"/>
  <text x="310" y="209" text-anchor="middle" fill="currentColor" stroke="none">world log: kills' share of intake</text>
  <line x1="410" y1="204" x2="618" y2="204" marker-end="url(#arr)"/>
  <text x="514" y="196" text-anchor="middle" fill="currentColor" stroke="none">25% or more: hunter world</text>
</g>
</svg>
<figcaption>Figure 1. The census. Each grown body answers three questions; a world's count is taken per body, or with every body counted under its lineage's commonest way. The world's state is read from its log, apart from the bodies.</figcaption>
</figure>
"""


def summary_rows(groups):
    by = defaultdict(list)
    for g in groups:
        by[(g[0], g[2][:4])].append(g)
    out = []
    for (cls, exp), gs in by.items():
        seeds = sorted({int(r["seed"]) for g in gs for r in g[6]})
        moved = Counter()
        for g in gs:
            for tok in g[6][0]["state_changes"].replace(" x", "x").split():
                a, n = tok.split("x")
                moved[a] += int(n)
        laws = "; ".join(f"{g[2].split(' ', 1)[1]} vs {g[3]}" for g in gs)
        hb = sum(C.holds(cls, g[4]) for g in gs)
        hl = sum(C.holds(cls, g[5]) for g in gs)
        seed_txt = f"{seeds[0]}-{seeds[-1]}" if len(seeds) > 1 else str(seeds[0])
        out.append(f"<tr><td>{exp}: {html.escape(laws)}</td><td>{cls}</td><td>{seed_txt}</td>"
                   f"<td>{' / '.join(g[4] for g in gs)}</td><td>{' / '.join(g[5] for g in gs)}</td>"
                   f"<td>{moved.get('g>h', 0)} / {moved.get('h>g', 0)}</td><td>{hb} / {hl} of {len(gs)}</td></tr>")
    return "".join(out)


def appendix(pairs, sweep):
    body = "".join(
        f"<tr><td>{html.escape(r['law'])}</td><td>{html.escape(r['control'])}</td><td>{r['seed']}</td>"
        f"<td>{num(r['law_ways']):.1f} / {num(r['control_ways']):.1f}</td>"
        f"<td>{num(r['law_ways_lineage']):.1f} / {num(r['control_ways_lineage']):.1f}</td>"
        f"<td>{num(r['law_q1']):.2f} / {num(r['control_q1']):.2f}</td>"
        f"<td>{100 * num(r['law_kills_share']):.0f}% / {100 * num(r['control_kills_share']):.0f}%</td></tr>" for r in pairs)
    t1 = ("<details><summary>Every pair and seed: ways per body, per lineage, q1, kills' share (law / control)</summary>"
          "<div class='tw'><table><thead><tr><th>law</th><th>control</th><th>seed</th><th>per body</th><th>per lineage</th>"
          f"<th>q1</th><th>kills</th></tr></thead><tbody>{body}</tbody></table></div></details>")
    keys = [k for k in sweep[0] if k not in ("setting", "frame holds")]
    head = "".join(f"<th>{html.escape(s['setting'])}</th>" for s in sweep)
    body = "".join(f"<tr><td>{html.escape(k)}</td>" + "".join(f"<td>{s[k]}</td>" for s in sweep) + "</tr>" for k in keys)
    body += "<tr><td><strong>frame holds</strong></td>" + "".join(f"<td><strong>{s['frame holds']}</strong></td>" for s in sweep) + "</tr>"
    t2 = ("<details><summary>The frame test per body under other thresholds (census.py sweep)</summary>"
          f"<div class='tw'><table><thead><tr><th>pair</th>{head}</tr></thead><tbody>{body}</tbody></table></div></details>")
    return t1 + t2


def texts(N):
    more = " and ".join(N["other_lineage_more"])
    return {
        "tldr": (f"A way of living is a grown body's diet, tooth and range. Counted per body, worlds hold {N['body_min']:.0f}-"
                 f"{N['body_max']:.0f} ways, and the count follows the kills' share of the food (rank correlation "
                 f"{N['rho_body']:.2f}). Counted per lineage, every world holds {N['lin_min']:.0f}-{N['lin_max']:.0f}: the rest "
                 f"is spread inside one lineage. The laws read as new axes added none ({N['axis_lineage']} of {N['axis_n']} pairs), "
                 f"so that reading of the series is dropped. e059 added shapes, not ways."),
        "question": ("vision.md made ways of living the measure and proposed a frame from ecology: the ways that coexist are at "
                     "most the independent limiting factors, each with a trade-off. Before any new law, the frame is checked on the "
                     "runs we have, and a one-seed count that doubted e059 is redone on every seed."),
        "world": ("No new runs. Each grown body falls into one of twelve ways of living. A world's count is the ways holding 5% "
                  "of its grown bodies, per body or with each body counted under its lineage's commonest way. The kills' share "
                  "of the intake comes from the log."),
        "runs": (f"{N['axis_n'] + N['other_n']} law-control pairs from e010-e059 (same code, same seeds, 1-6 seeds), at the "
                 f"census steps of each run's second half, plus e045, e055 and e058: {N['runs']} runs, 14 seconds on one core. "
                 f"Every threshold was also moved ({N['settings']} settings)."),
        "v1": (f"<span class=\"verdict no\">No</span> Axis laws hold more ways in {N['axis_body']} of {N['axis_n']} pairs per "
               f"body (e025, e032, both by bringing kills), {N['axis_lineage']} of {N['axis_n']} per lineage."),
        "v2": (f"<span class=\"verdict\">Yes</span> No other law adds ways: {N['other_body']} of {N['other_n']} pairs per body, "
               f"{N['other_lineage']} of {N['other_n']} per lineage ({more} by one)."),
        "v3": (f"<span class=\"verdict no\">No</span> e059's islands: {N['isl_body']:.1f} ways per body against "
               f"{N['uni_body']:.1f}, {N['isl_lineage']:.1f} per lineage against {N['uni_lineage']:.1f}."),
        "p_kills": (f"Worlds whose kills are under a tenth of the intake hold {N['low_kills']:.1f} ways per body; at 30% or "
                    f"more, {N['high_kills']:.1f}. The share runs evenly from 0 to 40%, so a hunter world is a degree, not a "
                    f"second state. Per lineage the slope is weak (rank correlation {N['rho_lineage']:.2f}): "
                    f"{N['grazer_lineage']:.1f} ways in grazer worlds, {N['hunter_lineage']:.1f} in hunter worlds."),
        "p_spread": (f"In e055 seed 9, the world with {N['l593_ways']} ways, lineage 593 holds {N['l593_share']:.0%} of the grown "
                     f"bodies and leads every way. Its flesh share runs {N['l593_q1']:.2f}-{N['l593_q3']:.2f} between quartiles, "
                     f"one hump cut into three diets. Its toothless members were born with {N['l593_born_muscle']:.1f} muscle "
                     f"blocks and keep {N['l593_muscle']:.1f}: the tooth was broken off. Roamers are {N['roam_age']:.1f} times "
                     f"older than stayers."),
        "p_laws": ("e025 put all four seeds into hunter worlds and e028 took three of four out; e046, e051, e054, e056 and e057 "
                   "moved seeds both ways, so their verdicts split. Within one state, a difference of one or two ways is the "
                   "size of the scatter between seeds of one world."),
        "p_e059": (f"Plant eaters without a tooth are 66-95% of the grown bodies on the islands and 64-92% in the uniform world. "
                   f"What changed is that they stay: 38-71% against 10-32%. Hunter worlds: {N['isl_hunter']} of 6 island "
                   f"runs, {N['uni_hunter']} of 6 uniform runs."),
        "discussion": ("<p>The frame predicted that laws adding a limiting factor would hold more ways of living. Counted per "
                       "lineage, none did. Per body, weight (e025) and the winter by height (e032) did, by raising the flesh of "
                       "kills, the one second food these worlds have; season, cloud and a second kind of place did not. The series "
                       "cannot be read as axes added and axes missed, and that reading is dropped.</p>"
                       "<p>The bound itself stands untested: no world held more than three kinds, and none had more than two "
                       "foods. The per-body count is the spread of a kind: members eat what lay near them, lose a tooth to a "
                       "break, and range further the longer they live. A viewer sees that spread, but selection acts on kinds.</p>"
                       "<p>What this cannot show: a lineage joins bodies by gene lists, so the per-lineage count is a lower bound "
                       "(e032 seed 3 holds a 70-block hunter and a 17-block gut in one lineage). No run records the tooth a body "
                       "was born with, its kills apart from scavenging, or the path it walked.</p>"),
        "conclusion": ("Count ways of living per kind; per body the count measures the spread of one kind. Per kind, every world "
                       "so far holds one to three, and none of the laws tested added one. The frame's reading of the series is "
                       "dropped; its bound stands untested. Next, #72: put a second kind into a world held by one, to learn "
                       "whether a world can hold two before asking evolution to find them."),
        "gallery": ("The birth body most common in four leading lineages at step 100,000, front up (blue hard, orange muscle, "
                    "yellow sensor, aqua gut). Seed 9 is a hunter world, seed 11 a grazer world."),
    }


def main():
    N, runs, pairs, groups, sweep, g593 = numbers()
    T = texts(N)
    words = sum(len(html.unescape(v).split()) for v in T.values())
    known = [r for r in runs if r["state"]]
    charts_kills = [
        scatter("Per body, more kills, more ways",
                "One dot per run and seed. A flat cloud would mean the count does not depend on how much of the food is kills.",
                known, "ways", "ways per body"),
        scatter("Per lineage, one to three everywhere",
                "The same runs, each body counted under its lineage's commonest way.", known, "ways_lineage", "ways per lineage"),
    ]
    charts_spread = [
        flesh_hist("One lineage, one diet, cut three ways",
                   "e055 seed 9 at step 100,000. Dashed lines are the diet cuts; one hump across them is one diet.", g593),
        muscle_bars("The toothless were born with the muscle",
                    "Mean muscle blocks, at birth and now. A tooth is a hard tip with muscle behind it; breaks remove the muscle.",
                    g593),
    ]
    chart_laws = diff_dots("A law moves the count by moving the kills",
                           "Axis laws above the line. A dot right of zero is a seed where the law holds more ways per body.",
                           groups)
    charts_e059 = [
        e059_bars("e059: shape kinds rose on some seeds", "Kinds of birth shape, rarefied to 120 bodies, mean of 200k and 300k.",
                  runs, "kinds_rarefied", "shape kinds"),
        e059_bars("e059: ways of living did not", "Ways per body, same runs and steps.", runs, "ways", "ways per body"),
    ]
    table = summary_rows(groups)
    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>e060 A census of ways of living - Report</title>
<style>{CSS}</style>
</head>
<body>
<main>
<h1>e060: A census of ways of living</h1>
<p class="sub">Experiment report - 2026-09-13 - analysis of existing runs, e010-e059 (#71). No new runs.</p>

<section class="tldr">
<h2>TL;DR</h2>
<p>{T["tldr"]}</p>
</section>

<h2>1. Question</h2>
<p>{T["question"]}</p>
<ol>
  <li><strong>The laws read as new axes</strong> (e012 places, e025 weight, e026 season and cloud, e032 winter by height) hold more ways of living than their controls.</li>
  <li><strong>The other laws</strong> (more of one food, an axis overlapping the old one, no trade-off) hold no more.</li>
</ol>

<h2>2. The census</h2>
<p>{T["world"]}</p>
{DIAGRAM}
<p><strong>Runs.</strong> {T["runs"]}</p>
<ul class="measures">
  <li><strong>ways per body</strong> - ways holding 5% of the grown bodies.</li>
  <li><strong>ways per lineage</strong> - the same, each body under its lineage's commonest way; a lower bound.</li>
  <li><strong>kills' share</strong> - the flesh of kills over all the world ate, second half of the run.</li>
  <li><strong>state</strong> - hunter world at 25% or more; e010-e012 have no kill log.</li>
  <li><strong>verdict</strong> - more or fewer when a seed differs by one way or more; the majority of seeds.</li>
</ul>

<h2>3. Results</h2>
<div class="tw"><table>
<thead><tr><th>law vs control</th><th>class</th><th>seeds</th><th>per body</th><th>per lineage</th><th>seeds into / out of hunter worlds</th><th>frame holds (body / lineage)</th></tr></thead>
<tbody>{table}</tbody></table></div>
<ol class="verdicts">
<li>{T["v1"]}</li>
<li>{T["v2"]}</li>
<li>{T["v3"]}</li>
</ol>
<p>Every verdict above holds under the thresholds moved in the appendix: the frame holds on {N["sweep_min"]}-{N["sweep_max"]} of 27 pairs per body across {N["settings"]} settings.</p>

<h3>3.1 The count follows the kills, per body only</h3>
<div class="grid2">{"".join(charts_kills)}</div>
<p>{T["p_kills"]}</p>

<h3>3.2 Most of the count is spread inside one lineage</h3>
<div class="grid2">{"".join(charts_spread)}</div>
<p>{T["p_spread"]}</p>
<figure class="diagram"><div class="cards">{gallery()}</div><figcaption>{T["gallery"]}</figcaption></figure>

<h3>3.3 Laws move the count by moving the kills</h3>
<div class="grid2">{chart_laws}</div>
<p>{T["p_laws"]}</p>

<h3>3.4 e059, corrected: more shapes, not more ways</h3>
<div class="grid2">{"".join(charts_e059)}</div>
<p>{T["p_e059"]}</p>

<h2>4. Discussion</h2>
{T["discussion"]}

<h2>5. Conclusion and next step</h2>
<p>{T["conclusion"]}</p>

<h2>Appendix: data</h2>
<p>The full census is in <code>results/runs.csv</code>, <code>results/pairs.csv</code>, <code>results/ways.csv</code> and <code>results/sweep.csv</code>. Build: <code>uv run python experiments/e060_census/census.py</code>, <code>census.py sweep</code>, then <code>report.py</code>.</p>
{appendix(pairs, sweep)}
</main>
</body>
</html>
"""
    out = os.path.join(HERE, "report.html")
    with open(out, "w") as f:
        f.write(page)
    print(f"wrote {out} ({os.path.getsize(out) // 1024} KB); TEXT {words} words")
    for k, v in N.items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
