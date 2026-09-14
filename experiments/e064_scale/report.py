#!/usr/bin/env python3
"""Build report.html for e064 (a body's scale of matter, foundation stage C, second step, #78).

Charts: matplotlib, exported as SVG and inlined. Diagram: hand-written SVG.
Run from the repo root: uv run python experiments/e064_scale/report.py
(`--picks` prints the bodies of the largest lineages, to choose the gallery.)
"""
import csv
import html
import io
import os
import statistics as st
import sys
from collections import Counter

import matplotlib
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from matplotlib.ticker import FixedLocator, MaxNLocator, NullLocator

matplotlib.use("svg")

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "experiments", "e060_census"))
import census  # noqa: E402  (e060's census of ways of living)

SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4"]  # fixed slot order
RUNS = ["1", "0.25", "0.0625"]
RUN_NAME = {"1": "s = 1 (e063)", "0.25": "s = 1/4", "0.0625": "s = 1/16"}
SLOT = {"1": 0, "0.25": 1, "0.0625": 2}
KIND_COLOR = {1: SERIES[0], 2: SERIES[1], 3: SERIES[3], 4: SERIES[2]}  # hard, muscle, sensor, gut: the viewer's
LAND = 110625  # land cells of c1225

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

def rows(path):
    with open(os.path.join(HERE, path)) as f:
        return list(csv.DictReader(f))


def columns(path):
    r = rows(path)
    return {k: [float(x[k]) for x in r] for k in r[0]}


def load(s):
    pre = f"results/c1225_life9_s{s}"
    d = {"log": columns(pre + "_log.csv"), "row": {k: float(v) for k, v in rows(pre + "_row.csv")[0].items()}}
    d["agents"] = census.read(os.path.join(HERE, pre + "_agents.csv"))
    d["lineages"] = rows(pre + "_lineages.csv")
    L = d["log"]
    last = L["step"][-1]
    late = [i for i, x in enumerate(L["step"]) if 2 * x > last]
    d["late"] = late
    d["mean"] = lambda k: st.mean(L[k][i] for i in late)
    total = lambda k: sum(L[k][i] for i in late)
    eat = total("plant_intake") + total("meat_intake")
    d["plant_share"] = total("plant_intake") / eat
    d["dead_share"] = total("scavenged") / eat
    d["kill_share"] = total("meat_intake") / eat - d["dead_share"]
    d["no_room"] = total("no_room") / total("children")
    d["burnt"] = total("burnt") / (len(late) * 1000 / d["row"]["year"])
    d["contacts"] = d["mean"]("contacts") / d["mean"]("pop") / 1000
    # e060's census over the dumps of the second half: ways of living per body and per lineage, and
    # the grown bodies that live by kills (over a fifth of their intake) and the teeth among them.
    dumps = list(census.late(list(d["agents"])))
    d["ways_body"] = [census.count(census.census(d["agents"][x])) for x in dumps]
    d["ways_lineage"] = [census.count(census.census_by_lineage(d["agents"][x])) for x in dumps]
    top, killers, teeth, grown = Counter(), 0, 0, 0
    for x in dumps:
        for r in census.grown(d["agents"][x]):
            grown += 1
            w = census.way(r)
            if w:
                top[w] += 1
            intake = float(r["plant"]) + float(r["meat"])
            if intake > 0 and float(r["killed"]) > 0.2 * intake:
                killers += 1
                teeth += int(r["born_bite"]) >= 2
    d["top_way_share"] = top.most_common(1)[0][1] / sum(top.values())
    d["killers"] = killers / grown
    d["killer_teeth"] = teeth / max(killers, 1)
    return d


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


def legend_above(ax, n, **kw):
    ax.legend(loc="lower left", bbox_to_anchor=(0, 1.0), ncols=n, handlelength=1.6, borderaxespad=0, columnspacing=1.2, **kw)


def figure(title, subtitle, svg):
    return f"""
<figure class="fig">
  <figcaption><strong>{html.escape(title)}</strong><span>{html.escape(subtitle)}</span></figcaption>
  {svg}
</figure>"""


def percent(ax):
    ax.yaxis.set_major_formatter(lambda y, _p: f"{y:.0%}")


def pop_chart(data):
    fig, ax = new_axes()
    for s in RUNS:
        L = data[s]["log"]
        ax.plot(L["step"], L["pop"], color=SERIES[SLOT[s]], linewidth=1.6, label=RUN_NAME[s])
    ax.set_yscale("log")
    ax.set_ylim(100, 20000)
    ax.yaxis.set_major_locator(FixedLocator([100, 1000, 10000]))
    ax.yaxis.set_minor_locator(NullLocator())
    ax.yaxis.set_major_formatter(kfmt)
    ax.set_ylabel("bodies (log scale)")
    legend_above(ax, 3)
    return figure("A smaller body buys a crowd",
                  "Bodies alive every 1,000 steps, on a log scale. Lines 4 and 16 times above e063's would be bodies that follow 1/s exactly.",
                  to_svg(fig))


def grass_chart(data, ctl):
    fig, ax = new_axes()
    ax.plot(ctl["step"], ctl["grass_grown"], color=INK, linewidth=1.2, linestyle=(0, (3, 2)), label="no bodies")
    for s in RUNS:
        L = data[s]["log"]
        ax.plot(L["step"], L["grass_grown"], color=SERIES[SLOT[s]], linewidth=1.6, label=RUN_NAME[s])
    ax.set_ylim(0, None)
    ax.yaxis.set_major_locator(MaxNLocator(4))
    ax.set_ylabel("grass grown a step")
    legend_above(ax, 4)
    return figure("Under the crowd the grass grows less",
                  "Grass grown a step on the whole world, in matter, meaned over each 1,000 steps; it rises and falls with the year. Dashed: the same world without bodies.",
                  to_svg(fig))


def kills_chart(data):
    fig, ax = new_axes()
    for s in RUNS:
        L = data[s]["log"]
        eat = [p + m for p, m in zip(L["plant_intake"], L["meat_intake"])]
        ax.plot(L["step"], [(m - v) / e if e > 0 else 0 for m, v, e in zip(L["meat_intake"], L["scavenged"], eat)], color=SERIES[SLOT[s]], linewidth=1.6, label=RUN_NAME[s])
    ax.set_ylim(0, 0.3)
    percent(ax)
    ax.yaxis.set_major_locator(MaxNLocator(4))
    legend_above(ax, 3)
    return figure("Kills rise with the crowd",
                  "Kills as a share of what the bodies took in, over each 1,000 steps; the rest is grass and the dead. Zero would be bodies that never break one another.",
                  to_svg(fig))


def ways_chart(data):
    fig, ax = plt.subplots(figsize=(6.4, 2.6))
    width = 0.36
    for j, s in enumerate(RUNS):
        for key, alpha, off in (("ways_body", 1.0, -width / 2), ("ways_lineage", 0.45, width / 2)):
            v = data[s][key]
            m = st.mean(v)
            ax.bar(j + off, m, width=width * 0.92, color=SERIES[SLOT[s]], alpha=alpha,
                   yerr=[[m - min(v)], [max(v) - m]], error_kw={"ecolor": INK, "elinewidth": 1, "capsize": 3})
    ax.set_xticks(range(len(RUNS)), [RUN_NAME[s] for s in RUNS])
    ax.set_ylim(0, 6)
    ax.yaxis.set_major_locator(MaxNLocator(4, integer=True))
    ax.set_ylabel("ways of living")
    legend_above(ax, 2, handles=[Patch(color=INK, alpha=1.0, label="among all grown bodies"), Patch(color=INK, alpha=0.45, label="within a lineage")])
    return figure("The crowd lives more ways",
                  "e060's ways of living (diet, tooth, roaming) among the grown bodies, the mean of six censuses in the second half; whiskers from the fewest to the most. One would be a world that lives one way.",
                  to_svg(fig))


def jam_chart(data):
    fig, ax = new_axes()
    for s in RUNS:
        L = data[s]["log"]
        ax.plot(L["step"], L["blocked"], color=SERIES[SLOT[s]], linewidth=1.6, label=RUN_NAME[s])
    ax.set_ylim(0, 0.8)
    percent(ax)
    ax.yaxis.set_major_locator(MaxNLocator(4))
    legend_above(ax, 3)
    return figure("The crowd jams",
                  "Share of the steps forward that another body or the sea blocked, over each 1,000 steps. e056's jammed world blocked 60%.",
                  to_svg(fig))


def density_chart(data):
    fig, ax = new_axes()
    for s in RUNS:
        L = data[s]["log"]
        ax.plot(L["step"], L["density_mean"], color=SERIES[SLOT[s]], linewidth=1.6, label=RUN_NAME[s])
    ax.axhline(2.0, color=INK, linewidth=1, linestyle=(0, (2, 2)))
    ax.set_ylim(0.5, 2.1)
    ax.yaxis.set_major_locator(FixedLocator([0.5, 1.0, 1.5, 2.0]))
    ax.set_ylabel("mean density")
    legend_above(ax, 3)
    return figure("In the jam every body is as dense as it can be",
                  "Mean density of the bodies alive, every 1,000 steps. A genome expresses 1/2 to 2 (dotted: the ceiling); a denser soft face breaks a lighter one when pressed.",
                  to_svg(fig))


def cost_chart(data):
    fig, ax = new_axes("bodies")
    ax.margins(x=0.02)
    top = 0
    for s in RUNS:
        L = data[s]["log"]
        ax.scatter(L["pop"][1:], [b + g for b, g in zip(L["ms_bodies"][1:], L["ms_lineage"][1:])], s=10, color=SERIES[SLOT[s]], label=RUN_NAME[s], linewidths=0)
        top = max(top, max(L["pop"][1:]))
    for us, dash in ((1, (2, 2)), (2, (5, 2))):
        ax.plot([0, top], [0, top * us / 1000], color=INK, linewidth=1, linestyle=(0, dash))
    ax.set_xlim(0, top * 1.05)
    ax.set_ylim(0, None)
    ax.yaxis.set_major_locator(MaxNLocator(4))
    ax.set_ylabel("ms a step (bodies)")
    legend_above(ax, 3)
    return figure("A body costs one to two microseconds",
                  "Each dot is 1,000 steps: the bodies alive at its end against what the bodies and their lineages cost a step on one core (the start's crash left out). Dotted: 1 µs a body; dashed: 2 µs.",
                  to_svg(fig))


def modal_body(d, lid):
    """The most common birth body of a lineage's grown bodies at the dump where it has the most of them."""
    best = None
    for x, rs in d["agents"].items():
        g = [r for r in census.grown(rs) if r["lineage"] == lid]
        if best is None or len(g) > len(best[1]):
            best = (x, g)
    x, g = best
    if not g:
        return x, g, 0, ""
    c = Counter((r["side"], r["cells"]) for r in g if int(r["size"]) == int(r["born_size"])) or Counter((r["side"], r["cells"]) for r in g)
    (side, cells), _ = c.most_common(1)[0]
    return x, g, int(side), cells


def gallery(data, picks, caption):
    cards = []
    for s, lid, title, what in picks:
        d = data[s]
        x, g, side, cells = modal_body(d, lid)
        span = [int(r["step"]) for r in d["lineages"] if r["lineage"] == lid]
        life = (max(span) - min(span) + 1000) if span else 0
        peak = max((int(r["size"]) for r in d["lineages"] if r["lineage"] == lid), default=0)
        u = 88 / side
        rects = "".join(f'<rect x="{(i % side) * u:.2f}" y="{(i // side) * u:.2f}" width="{u * 0.9:.2f}" height="{u * 0.9:.2f}" fill="{KIND_COLOR[int(k)]}"/>'
                        for i, k in enumerate(cells) if k != "0")
        mean = lambda k: st.mean(float(r[k]) for r in g)
        meat = sum(float(r["meat"]) for r in g) / max(sum(float(r["meat"]) + float(r["plant"]) for r in g), 1e-9)
        cards.append(f"""<figure class="card"><svg viewBox="-1 -1 89 89" width="120" height="120" role="img" aria-label="{html.escape(title)}"><rect x="-1" y="-1" width="89" height="89" fill="var(--cell)"/>{rects}<line x1="-1" y1="-0.5" x2="88" y2="-0.5" stroke="var(--ink2)" stroke-width="1.5" stroke-dasharray="3 2"/></svg>
<figcaption><strong>{html.escape(title)}</strong><br>{RUN_NAME[s]}, lineage {lid}: {life:,} steps, {peak:,} bodies at its peak<br>grid {side}x{side}; mass {mean("mass"):.0f}, density {mean("density"):.2f}: hard {mean("hard"):.1f}, muscle {mean("muscle"):.0f}, sensor {mean("sensor"):.1f}, gut {mean("digestive"):.0f}; flesh {meat:.0%}; {st.median(float(r["travel"]) for r in g):.0f} cells from its birthplace<br>{html.escape(what)}</figcaption></figure>""")
    return f"""<figure class="diagram"><div class="cards">{"".join(cards)}</div>
<figcaption>{caption}</figcaption></figure>"""


def print_picks(data):
    for s in RUNS[1:]:
        d = data[s]
        peaks = Counter()
        for r in d["lineages"]:
            peaks[r["lineage"]] = max(peaks[r["lineage"]], int(r["size"]))
        for lid, peak in peaks.most_common(10):
            x, g, side, cells = modal_body(d, lid)
            if not g:
                continue
            mean = lambda k: st.mean(float(r[k]) for r in g)
            meat = sum(float(r["meat"]) for r in g) / max(sum(float(r["meat"]) + float(r["plant"]) for r in g), 1e-9)
            print(f"s={s} lineage {lid}: peak {peak}, {len(g)} grown at {x}, side {side}, mass {mean('mass'):.0f} density {mean('density'):.2f} "
                  f"hard {mean('hard'):.1f} muscle {mean('muscle'):.1f} sensor {mean('sensor'):.1f} gut {mean('digestive'):.1f} speed {mean('speed'):.2f} "
                  f"flesh {meat:.0%} killed {sum(float(r['killed']) for r in g) / max(sum(float(r['meat']) + float(r['plant']) for r in g), 1e-9):.0%} tooth {st.mean(int(r['born_bite']) >= 2 for r in g):.0%}")
            for i in range(side):
                print("    " + "".join(".HMSG"[int(k)] for k in cells[i * side:(i + 1) * side]))


def data_table(data, every=10):
    cols = ["step", "pop", "grown", "births", "no_room", "deaths_hunger", "deaths_broken", "contacts", "plant_intake", "meat_intake", "scavenged",
            "tooth", "density_mean", "blocked", "lineages", "travel_p50", "grass", "grass_grown", "ms_bodies", "ms_lineage"]
    out = []
    for s in RUNS:
        L = data[s]["log"]
        body = "".join("<tr>" + "".join(f"<td>{L[c][i]:g}</td>" for c in cols) + "</tr>" for i in range(every - 1, len(L["step"]), every))
        out.append(f"<details><summary>{RUN_NAME[s]}, every {every * 1000:,} steps</summary><div class='tw'><table><thead><tr>"
                   + "".join(f"<th>{c}</th>" for c in cols) + f"</tr></thead><tbody>{body}</tbody></table></div></details>")
    return "\n".join(out)


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
.verdict.partly {{ background: rgba(250,178,25,0.15); color: #8a5a00; }}
:root[data-theme="dark"] .verdict.partly {{ color: #fab219; }}
@media (prefers-color-scheme: dark) {{ :root:not([data-theme="light"]) .verdict.partly {{ color: #fab219; }} }}
:root[data-theme="dark"] .verdict {{ color: #0ca30c; }} :root[data-theme="dark"] .verdict.no {{ color: #e66767; }}
@media (prefers-color-scheme: dark) {{ :root:not([data-theme="light"]) .verdict {{ color: #0ca30c; }} :root:not([data-theme="light"]) .verdict.no {{ color: #e66767; }} }}
"""

DIAGRAM = """
<figure class="diagram">
<svg viewBox="0 0 760 250" role="img" aria-label="A body keeps its economy in its own units; the scale s converts matter where it crosses between the body and the world" style="max-width:100%;height:auto;display:block">
<defs><marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="currentColor"/></marker>
<marker id="arr1" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="var(--s1)"/></marker></defs>
<g fill="none" stroke="currentColor" stroke-width="1.2" font-size="12" font-family="system-ui, sans-serif">
  <rect x="20" y="20" width="210" height="210" rx="6"/>
  <text x="125" y="46" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">A body (e063's laws)</text>
  <text x="125" y="64" text-anchor="middle" fill="currentColor" stroke="none">in its own units</text>
  <text x="125" y="104" text-anchor="middle" fill="currentColor" stroke="none">upkeep 0.002 a block</text>
  <text x="125" y="122" text-anchor="middle" fill="currentColor" stroke="none">+ 0.032 a step</text>
  <text x="125" y="156" text-anchor="middle" fill="currentColor" stroke="none">bite 0.02 a gut block</text>
  <text x="125" y="190" text-anchor="middle" fill="currentColor" stroke="none">breeds at 2 + 0.1 mass</text>
  <rect x="530" y="20" width="210" height="210" rx="6"/>
  <text x="635" y="46" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">The world (e062)</text>
  <text x="635" y="64" text-anchor="middle" fill="currentColor" stroke="none">in matter</text>
  <text x="635" y="104" text-anchor="middle" fill="currentColor" stroke="none">grass grows by its cover</text>
  <text x="635" y="156" text-anchor="middle" fill="currentColor" stroke="none">the dead rot 1% a step</text>
  <text x="635" y="190" text-anchor="middle" fill="currentColor" stroke="none">into the soil</text>
  <line x1="528" y1="60" x2="232" y2="60" stroke="var(--s1)" stroke-width="2" marker-end="url(#arr1)"/>
  <text x="380" y="48" text-anchor="middle" fill="currentColor" stroke="none">bite: takes 0.02 × s, gains it ÷ s</text>
  <line x1="528" y1="108" x2="232" y2="108" stroke-dasharray="4 3" marker-end="url(#arr)"/>
  <text x="380" y="96" text-anchor="middle" fill="currentColor" stroke="none">eye: reads the food ÷ s</text>
  <line x1="232" y1="160" x2="528" y2="160" stroke="var(--s1)" stroke-width="2" marker-end="url(#arr1)"/>
  <text x="380" y="148" text-anchor="middle" fill="currentColor" stroke="none">upkeep and moves: × s to the soil</text>
  <line x1="232" y1="208" x2="528" y2="208" stroke="var(--s1)" stroke-width="2" marker-end="url(#arr1)"/>
  <text x="380" y="196" text-anchor="middle" fill="currentColor" stroke="none">the dead: × s to the carrion</text>
</g>
</svg>
<figcaption>Figure 1. The scale. A body keeps e063's economy in its own units; s converts matter only where it crosses to the world (blue). At s = 1/16 a body lives the same life on a sixteenth of the grass. Weight, wear and the clock do not scale.</figcaption>
</figure>
"""

# The text of the page: kept here to count its words against the skill's budget.
TEXT = {}


def main():
    data = {s: load(s) for s in RUNS}
    if "--picks" in sys.argv:
        print_picks(data)
        return
    ctl = columns("results/c1225_control_log.csv")
    late = data["1"]["late"]
    ctl_mean = lambda k: st.mean(ctl[k][i] for i in late)
    ctl_burnt = sum(ctl["burnt"][i] for i in late) / (len(late) * 1000 / data["1"]["row"]["year"])
    row = lambda s: data[s]["row"]
    mean = lambda s, k: data[s]["mean"](k)
    minutes = lambda s: row(s)["ms_step"] * 300_000 / 60_000
    ways = lambda v: str(min(v)) if min(v) == max(v) else f"{min(v)}-{max(v)}"
    one, q, x = data["1"], data["0.25"], data["0.0625"]

    charts_pop = [pop_chart(data), grass_chart(data, ctl)]
    charts_meet = [kills_chart(data), ways_chart(data)]
    charts_jam = [jam_chart(data), density_chart(data)]
    charts_cost = [cost_chart(data)]

    def cells(fmt):
        return "".join(f"<td>{fmt(s)}</td>" for s in RUNS)
    table_rows = [
        ("Bodies (mean, lowest-highest)", lambda s: f"{row(s)['pop_mean']:,.0f} ({row(s)['pop_min']:,.0f}-{row(s)['pop_max']:,.0f})"),
        ("Land cells per body", lambda s: f"{LAND / row(s)['pop_mean']:.0f}"),
        ("Contacts per body a step", lambda s: f"{data[s]['contacts']:.3f}"),
        ("Intake: grass / kills / the dead", lambda s: f"{data[s]['plant_share']:.0%} / {data[s]['kill_share']:.1%} / {data[s]['dead_share']:.0%}"),
        ("Bodies with a tooth", lambda s: f"{mean(s, 'tooth'):.1%}"),
        ("Ways of living: all grown / within a lineage", lambda s: f"{ways(data[s]['ways_body'])} / {ways(data[s]['ways_lineage'])}"),
        ("Grown bodies living the commonest way", lambda s: f"{data[s]['top_way_share']:.0%}"),
        ("Lineages alive (top lineage's share)", lambda s: f"{mean(s, 'lineages'):.1f} ({mean(s, 'top_lineage'):.0%})"),
        ("Density; grid side; speed", lambda s: f"{mean(s, 'density_mean'):.2f}; {mean(s, 'side_mean'):.1f}; {mean(s, 'speed_mean'):.2f}"),
        ("Moves blocked; children with no room", lambda s: f"{mean(s, 'blocked'):.0%}; {data[s]['no_room']:.0%}"),
        ("Grown body's distance from birth (median, cells)", lambda s: f"{mean(s, 'travel_p50'):.0f}"),
        ("Grass standing / grown a step, of the control's", lambda s: f"{mean(s, 'grass') / ctl_mean('grass'):.0%} / {mean(s, 'grass_grown') / ctl_mean('grass_grown'):.0%}"),
        (f"Land burnt a year (control {ctl_burnt:.2%})", lambda s: f"{data[s]['burnt']:.2%}"),
        ("A step: world + bodies + lineages (ms)", lambda s: f"{row(s)['ms_world']:.2f} + {row(s)['ms_bodies']:.2f} + {row(s)['ms_lineage']:.2f}"),
        ("300,000 steps on one core (min)", lambda s: f"{minutes(s):.0f}"),
    ]
    table = "".join(f"<tr><td>{name}</td>{cells(f)}</tr>" for name, f in table_rows)
    grown_share = lambda s: mean(s, "grass_grown") / ctl_mean("grass_grown")

    TEXT["tldr"] = (f"One factor s on every matter quantity of a body, on e062's world c1225: s = 1/4 holds {row('0.25')['pop_mean']:,.0f} bodies and s = 1/16 "
                    f"holds {row('0.0625')['pop_mean']:,.0f}, {row('0.0625')['pop_mean'] / row('1')['pop_mean']:.0f} times e063's. At 1/16 bodies meet, kills are "
                    f"{x['kill_share']:.0%} of the intake and each lineage lives {ways(x['ways_lineage'])} ways instead of one. The crowd jams, pins every body's density "
                    f"at its ceiling, and costs {row('0.0625')['ms_step']:.0f} ms a step. Next: choose stage C's s and build its first trade-off.")
    TEXT["question"] = ("e063's bodies lived one per 360 land cells, one way: they keep e059's economy against grass that grows a twentieth of e059's sun, "
                        "and no trade-off can be judged in a world so thin. #78 multiplies every matter quantity of a body by one factor s. Written before the runs:")
    TEXT["hyp"] = ["More bodies, far fewer than 1/s: 500-900 at s = 1/4 and 600-2,000 at 1/16, since smaller bodies graze grass that grows by its own cover lower.",
                   "Bodies meet more, but kills stay under 10% of the intake and each lineage lives one way.",
                   "Still cheap: under 2 µs a body, and 300,000 steps under an hour at s = 1/16."]
    TEXT["world"] = ("e063's world and bodies with one number more. A body keeps its economy in its own units and s converts matter where it crosses to "
                     "the world; the eye reads food in the body's units, so s changes the crowd and not what a body sees.")
    TEXT["runs"] = ("c1225 with draw d11, seed 9, 100,000 steps from e063's settled world, one core each: s = 1/4 and 1/16, and s = 1, which "
                    "reproduced e063's files exactly. The control is the world without bodies. Every 1,000 steps we record:")
    TEXT["measures"] = [
        ("Bodies", "alive, grown (300 steps or older), and their lineages."),
        ("Contact", "bodies pressed a step; the kills' and the dead's share of the intake."),
        ("Ways of living", "e060's census of the grown bodies: diet, tooth, roaming."),
        ("The crowd", "moves blocked, children with no room, density, distance from birth."),
        ("Grass and fire", "grass standing and grown, land burnt, against the control."),
        ("Cost", "wall time a step: the world, the bodies, the lineages."),
    ]
    TEXT["v1"] = (f"{row('0.25')['pop_mean']:,.0f} bodies at s = 1/4, inside; {row('0.0625')['pop_mean']:,.0f} at 1/16, "
                  f"{row('0.0625')['pop_mean'] / row('1')['pop_mean']:.1f} times e063's, more than 1/s.")
    TEXT["v2"] = f"kills {x['kill_share']:.0%} of the intake and {ways(x['ways_lineage'])} ways within a lineage at s = 1/16; e063's: {one['kill_share']:.0%} and one."
    TEXT["v3"] = f"{min(row(s)['us_per_body'] for s in RUNS):.1f}-{max(row(s)['us_per_body'] for s in RUNS):.1f} µs a body; 300,000 steps take {minutes('0.0625'):.0f} minutes at s = 1/16."
    TEXT["r1"] = (f"Smaller bodies do graze the grass lower, and it grows less: {grown_share('0.0625'):.0%} of the control's at s = 1/16, "
                  f"{grown_share('1'):.0%} at s = 1. But the crowd eats as much matter a step as e063's bodies: it takes two thirds of the grass "
                  "that grows before it dies or burns, and eats its own dead.")
    TEXT["r2"] = (f"Contacts per body rise {x['contacts'] / one['contacts']:.1f} times at s = 1/16, and the kills and the ways of living rise with them. "
                  f"The kills are not a tooth's: {x['killers']:.0%} of the grown bodies take over a fifth of their intake from kills, "
                  f"and {x['killer_teeth']:.0%} of those carry a tooth.")
    TEXT["r3"] = (f"At s = 1/16, {mean('0.0625', 'blocked'):.0%} of the moves are blocked and {x['no_room']:.0%} of the children find no room. "
                  f"In the jam density is weapon and armor, and every body sits near the ceiling, paying in speed "
                  f"({mean('0.0625', 'speed_mean'):.2f} against {mean('1', 'speed_mean'):.2f}).")
    TEXT["r4"] = (f"A body costs one to two microseconds at every scale; at {row('0.0625')['pop_mean']:,.0f} bodies they are "
                  f"{row('0.0625')['ms_bodies'] / row('0.0625')['ms_step']:.0%} of a step. The lineages' detection grows with the square of the gene "
                  "lists alive and is the part to watch.")
    TEXT["gallery"] = "The commonest birth body of large lineages at s = 1/4 and 1/16, at the census where each had the most grown bodies. The dashed line is the front."
    TEXT["d1"] = ("The mechanism in the hypothesis was half right. The grass grows less under smaller bodies, but the number of bodies followed the scale, "
                  "not the grass: at 1/16 less of the grass dies to litter and fire, and more than a quarter of what the bodies eat is one another.")
    TEXT["d2"] = ("The crowd makes niches (#68's rule 2) and jams, as e056's did. The density ceiling of 2, e025's choice, now binds, and the crowd's "
                  "kills come from density. foundation.md's first trade-off, the water's two layers, puts a price on density (a light body reaches the "
                  "surface), which is where this crowd would feel it.")
    TEXT["d3"] = ("Not shown: c1236, other seeds, runs past 100,000 steps, a scale between 1/4 and 1/16, another density range. The random start and "
                  "e063's join (land only, grass and the dead as food) were not varied.")
    TEXT["conclusion"] = (f"One scale on a body's matter sets the density, and at s = 1/16 stage C first holds lineages that live different ways. It costs a jam, "
                          f"a pinned density and {minutes('0.0625'):.0f} minutes a run, which still allows 6 seeds on 2 worlds in about an hour. "
                          "Next, to agree in #78: s = 1/16 for stage C, and the water's two layers as its first trade-off.")

    picks = GALLERY_PICKS
    gal = gallery(data, picks, TEXT["gallery"])

    words = sum(len((" ".join(v) if isinstance(v, list) and v and isinstance(v[0], str) else " ".join(" ".join(t) for t in v) if isinstance(v, list) else v).split()) for v in TEXT.values())
    words += sum(len(p[3].split()) for p in picks)
    print(f"TEXT: {words} words")

    hyp = "".join(f"<li>{html.escape(h)}</li>" for h in TEXT["hyp"])
    measures = "".join(f"<li><strong>{html.escape(k)}</strong> - {html.escape(v)}</li>" for k, v in TEXT["measures"])
    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>e064 a body's scale of matter - Report</title>
<style>{CSS}</style>
</head>
<body>
<main>
<h1>e064: a body's scale of matter</h1>
<p class="sub">Experiment report - 2026-09-14 - every matter quantity of a body times s = 1, 1/4 and 1/16 on e062's world c1225, 100,000 steps each (foundation stage C, second step, #78)</p>

<section class="tldr">
<h2>TL;DR</h2>
<p>{html.escape(TEXT["tldr"])}</p>
</section>

<h2>1. Question</h2>
<p>{html.escape(TEXT["question"])}</p>
<ol>{hyp}</ol>

<h2>2. The world</h2>
<p>{html.escape(TEXT["world"])}</p>
{DIAGRAM}
<p><strong>Runs.</strong> {html.escape(TEXT["runs"])}</p>
<ul class="measures">{measures}</ul>

<h2>3. Results</h2>
<div class="tw"><table>
<thead><tr><th>Second half of the run</th>{"".join(f"<th>{RUN_NAME[s]}</th>" for s in RUNS)}</tr></thead>
<tbody>{table}</tbody></table></div>
<ol class="verdicts">
<li><span class="verdict partly">Partly</span> 1, far fewer than 1/s: {html.escape(TEXT["v1"])}</li>
<li><span class="verdict no">No</span> 2, still one way: {html.escape(TEXT["v2"])}</li>
<li><span class="verdict">Yes</span> 3, still cheap: {html.escape(TEXT["v3"])}</li>
</ol>

<h3>3.1 A smaller body buys a crowd, though the grass grows less</h3>
<div class="grid2">{"".join(charts_pop)}</div>
<p>{html.escape(TEXT["r1"])}</p>

<h3>3.2 The crowd meets, kills and lives more ways</h3>
<div class="grid2">{"".join(charts_meet)}</div>
<p>{html.escape(TEXT["r2"])}</p>
{gal}

<h3>3.3 The crowd jams, and density is its weapon</h3>
<div class="grid2">{"".join(charts_jam)}</div>
<p>{html.escape(TEXT["r3"])}</p>

<h3>3.4 A body still costs about a microsecond</h3>
<div class="grid2">{"".join(charts_cost)}</div>
<p>{html.escape(TEXT["r4"])}</p>

<h2>4. Discussion</h2>
<p>{html.escape(TEXT["d1"])}</p>
<p>{html.escape(TEXT["d2"])}</p>
<p>{html.escape(TEXT["d3"])}</p>

<h2>5. Conclusion and next step</h2>
<p>{html.escape(TEXT["conclusion"])}</p>

<h2>Appendix: data</h2>
<p>Rows of <code>results/c1225_life9_s&lt;s&gt;_log.csv</code>; bodies are in <code>_agents.csv</code> every 10,000 steps, lineages in <code>_lineages.csv</code> and <code>_events.csv</code>, the run in one row in <code>_row.csv</code>; the world without bodies in <code>c1225_control_*</code>. Build this report with <code>uv run python experiments/e064_scale/report.py</code>.</p>
{data_table(data)}
</main>
</body>
</html>
"""
    out = os.path.join(HERE, "report.html")
    with open(out, "w") as f:
        f.write(page)
    print(f"wrote {out} ({os.path.getsize(out)//1024} KB)")


# (scale, lineage, title, what the shape does): filled from the bodies the runs made.
GALLERY_PICKS = [
    ("0.25", "20", "Gut in front, motor behind",
     "Three rows of gut lead and five of muscle push: each step lays the guts on grass not yet bitten. The fastest here, it lives on grass."),
    ("0.25", "96", "Gut and a flank of eyes",
     "A knot of sensors on one flank sees five cells; denser than most at 1/4, it takes a seventh of its intake from kills."),
    ("0.0625", "2540", "Half motor, half gut, as dense as it gets",
     "Two rows of muscle over two of gut at density 2: the crowd's plain build, a sixth of its intake from kills."),
    ("0.0625", "1859", "A crusher without a tooth",
     "Muscle over three quarters of the grid and a corner of gut: at density 2 it breaks the lighter bodies it presses, and most of its intake is kills."),
    ("0.0625", "725", "Muscle on two sides",
     "Muscle across the front and down one flank, gut in the corner they cover; dense, it takes a quarter of its intake from kills."),
    ("0.0625", "705", "All gut, standing still",
     "Forty-nine gut blocks and almost no muscle: it hardly moves and eats the grass and the dead where it stands."),
]

if __name__ == "__main__":
    main()
