#!/usr/bin/env python3
"""Build report.html for e063 (foundation stage C, first step, #76).

Charts: matplotlib, exported as SVG and inlined. Diagram: hand-written SVG.
Run from the repo root: uv run python experiments/e063_bodies/report.py
"""
import csv
import html
import io
import os
import statistics as st
import sys
from collections import Counter, defaultdict

import matplotlib
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator

matplotlib.use("svg")

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "experiments", "e060_census"))
import census  # noqa: E402  (e060's census of ways of living)

SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4"]  # fixed slot order
WORLDS = ["c1225", "c1236"]
WORLD_NAME = {"c1225": "c1225 (warm, very wet)", "c1236": "c1236 (cool)"}
WORLD_SLOT = {"c1225": 0, "c1236": 1}
KIND_COLOR = {1: SERIES[0], 2: SERIES[1], 3: SERIES[3], 4: SERIES[2]}  # hard, muscle, sensor, gut: the viewer's
HABITATS = ["land_cold_dry", "land_cold_moist", "land_cold_wet", "land_mild_dry", "land_mild_moist", "land_mild_wet",
            "land_hot_dry", "land_hot_moist", "land_hot_wet", "shallow_cold", "shallow_mild", "shallow_hot",
            "deep_cold", "deep_mild", "deep_hot"]
FOUNDATION_THIN = 9600  # foundation.md's thin world at 512 (e058's sun 0.2 scaled)

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


def load(world):
    pre = f"results/{world}_life9"
    log = rows(pre + "_log.csv")
    d = {"log": {k: [float(r[k]) for r in log] for k in log[0]}, "row": {k: float(v) for k, v in rows(pre + "_row.csv")[0].items()}}
    d["agents"] = census.read(os.path.join(HERE, pre + "_agents.csv"))
    d["lineages"] = rows(pre + "_lineages.csv")
    e62 = rows(f"../e062_producers/results/search/{world}_d11_years.csv")
    d["e062"] = e62
    ctl = rows(f"results/{world}_control_log.csv")  # the same world without bodies, the same steps
    d["control"] = {k: [float(r[k]) for r in ctl] for k in ctl[0]}
    steps = d["log"]["step"]
    last = steps[-1]
    late = [i for i, s in enumerate(steps) if 2 * s > last]
    d["late"] = late
    L = d["log"]
    eat = sum(L["plant_intake"][i] + L["meat_intake"][i] for i in late)
    scav = sum(L["scavenged"][i] for i in late)
    d["plant_share"] = sum(L["plant_intake"][i] for i in late) / eat
    d["dead_share"] = scav / eat
    d["kill_share"] = sum(L["meat_intake"][i] for i in late) / eat - d["dead_share"]
    year = d["row"]["year"]
    d["burn63"] = sum(L["burnt"][i] for i in late) / (len(late) * 1000 / year)
    d["burn62"] = st.mean(float(r["burnt"]) for r in e62[len(e62) // 2:])
    C = d["control"]
    d["burn_ctl"] = sum(C["burnt"][i] for i in late) / (len(late) * 1000 / year)
    d["ctl"] = lambda k: st.mean(C[k][i] for i in late)
    d["grass62"] = float(e62[-1]["grass"])
    d["wood62"] = float(e62[-1]["wood"])
    mean = lambda k: st.mean(L[k][i] for i in late)
    d["mean"] = mean
    bands = [mean(k) for k in ["pop_cold", "pop_mild", "pop_hot", "pop_dry", "pop_moist", "pop_wet"]]
    d["bands"] = [b / mean("pop") for b in bands]
    # e060's census over the dumps of the second half: ways of living per body and per lineage.
    dumps = [s for s in census.late(list(d["agents"]))]
    d["ways_body"] = [census.count(census.census(d["agents"][s])) for s in dumps]
    d["ways_lineage"] = [census.count(census.census_by_lineage(d["agents"][s])) for s in dumps]
    top = Counter()
    for s in dumps:
        for r in census.grown(d["agents"][s]):
            w = census.way(r)
            if w:
                top[w] += 1
    d["top_way"], n_top = top.most_common(1)[0]
    d["top_way_share"] = n_top / sum(top.values())
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


def legend_above(ax, n):
    ax.legend(loc="lower left", bbox_to_anchor=(0, 1.0), ncols=n, handlelength=1.6, borderaxespad=0, columnspacing=1.2)


def figure(title, subtitle, svg):
    return f"""
<figure class="fig">
  <figcaption><strong>{html.escape(title)}</strong><span>{html.escape(subtitle)}</span></figcaption>
  {svg}
</figure>"""


def cost_chart(data):
    fig, ax = new_axes()
    for w in WORLDS:
        L = data[w]["log"]
        c = SERIES[WORLD_SLOT[w]]
        ax.plot(L["step"][1:], L["ms_world"][1:], color=c, linewidth=1.6, label=f"{w} world")
        ax.plot(L["step"][1:], L["ms_bodies"][1:], color=c, linewidth=1.6, linestyle=(0, (3, 2)), label=f"{w} bodies")
    ax.set_ylim(0, 2.0)
    ax.yaxis.set_major_locator(MaxNLocator(4))
    ax.set_ylabel("ms a step")
    legend_above(ax, 4)
    return figure("A step costs the world's update, not the bodies'",
                  "Wall time a step on one core, meaned over each 1,000 steps (the first, the crash of the start, is left out). Dashed under solid: the bodies are the smaller part.",
                  to_svg(fig))


def per_body_chart(data):
    fig, ax = new_axes("bodies")
    ax.margins(x=0.02)
    top = 0
    for w in WORLDS:
        L = data[w]["log"]
        ax.scatter(L["pop"][1:], L["ms_bodies"][1:], s=10, color=SERIES[WORLD_SLOT[w]], label=w, linewidths=0)
        top = max(top, max(L["pop"][1:]))
    ax.plot([0, top], [0, top * 1e-3], color=INK, linewidth=1, linestyle=(0, (2, 2)), label="1 µs a body")
    ax.set_xlim(0, top * 1.05)
    ax.set_ylim(0, 1.2)
    ax.yaxis.set_major_locator(MaxNLocator(4))
    ax.set_ylabel("ms a step (bodies)")
    legend_above(ax, 3)
    return figure("A body costs about a microsecond",
                  "Each dot is 1,000 steps: the bodies alive at its end against what the bodies cost a step (the start's crash left out). Dots on the dashed line cost one microsecond a body.",
                  to_svg(fig))


def pop_chart(data):
    fig, ax = new_axes()
    for w in WORLDS:
        L = data[w]["log"]
        ax.plot(L["step"], L["pop"], color=SERIES[WORLD_SLOT[w]], linewidth=1.6, label=WORLD_NAME[w])
    ax.set_ylim(0, 1000)
    ax.yaxis.set_major_locator(MaxNLocator(4))
    ax.set_ylabel("bodies")
    legend_above(ax, 2)
    return figure("The world feeds about 300 bodies",
                  f"Bodies alive every 1,000 steps. foundation.md costed stage C at {FOUNDATION_THIN:,} (a thin world); a line at zero would be a dead world.",
                  to_svg(fig))


def grass_chart(data):
    fig, ax = new_axes()
    for w in WORLDS:
        L = data[w]["log"]
        C = data[w]["control"]
        ax.plot(L["step"], [g / c for g, c in zip(L["grass"], C["grass"])], color=SERIES[WORLD_SLOT[w]], linewidth=1.6, label=w)
    ax.set_ylim(0, 1)
    ax.yaxis.set_major_formatter(lambda y, _p: f"{y:.0%}")
    ax.yaxis.set_major_locator(MaxNLocator(4))
    legend_above(ax, 2)
    return figure("300 bodies hold the grass at a fifth",
                  "The world's standing grass with bodies over the same world without them (the control), step by step. 100% would be bodies that change nothing.",
                  to_svg(fig))


def flesh_chart(data):
    fig, ax = new_axes()
    for w in WORLDS:
        L = data[w]["log"]
        c = SERIES[WORLD_SLOT[w]]
        eat = [p + m for p, m in zip(L["plant_intake"], L["meat_intake"])]
        ax.plot(L["step"], [(m - s) / e if e > 0 else 0 for m, s, e in zip(L["meat_intake"], L["scavenged"], eat)], color=c, linewidth=1.6, label=f"{w} kills")
        ax.plot(L["step"], [s / e if e > 0 else 0 for s, e in zip(L["scavenged"], eat)], color=c, linewidth=1.6, linestyle=(0, (3, 2)), label=f"{w} the dead")
    ax.axhline(0.25, color=INK, linewidth=1, linestyle=(0, (2, 2)))
    ax.set_ylim(0, 0.3)
    ax.yaxis.set_major_formatter(lambda y, _p: f"{y:.0%}")
    ax.yaxis.set_major_locator(MaxNLocator(4))
    legend_above(ax, 4)
    return figure("The bodies live on grass",
                  "Kills and the dead as a share of what the bodies took in over each 1,000 steps; the rest is grass. The dotted line is a hunter world's 25% (e045).",
                  to_svg(fig))


def modal_body(d, lid):
    """The most common birth body of a lineage's grown bodies at the dump where it has the most of them."""
    best = None
    for s, rs in d["agents"].items():
        g = [r for r in census.grown(rs) if r["lineage"] == lid]
        if best is None or len(g) > len(best[1]):
            best = (s, g)
    s, g = best
    c = Counter((r["side"], r["cells"]) for r in g if int(r["size"]) == int(r["born_size"])) or Counter((r["side"], r["cells"]) for r in g)
    (side, cells), _ = c.most_common(1)[0]
    return s, g, int(side), cells


def gallery(data, picks, caption):
    cards = []
    for w, lid, title, what in picks:
        d = data[w]
        s, g, side, cells = modal_body(d, lid)
        span = [int(r["step"]) for r in d["lineages"] if r["lineage"] == lid]
        life = (max(span) - min(span) + 1000) if span else 0
        peak = max((int(r["size"]) for r in d["lineages"] if r["lineage"] == lid), default=0)
        u = 88 / side
        rects = "".join(f'<rect x="{(i % side) * u:.2f}" y="{(i // side) * u:.2f}" width="{u * 0.9:.2f}" height="{u * 0.9:.2f}" fill="{KIND_COLOR[int(k)]}"/>'
                        for i, k in enumerate(cells) if k != "0")
        mean = lambda k: st.mean(float(r[k]) for r in g)
        meat = sum(float(r["meat"]) for r in g) / max(sum(float(r["meat"]) + float(r["plant"]) for r in g), 1e-9)
        cards.append(f"""<figure class="card"><svg viewBox="-1 -1 89 89" width="120" height="120" role="img" aria-label="{html.escape(title)}"><rect x="-1" y="-1" width="89" height="89" fill="var(--cell)"/>{rects}<line x1="-1" y1="-0.5" x2="88" y2="-0.5" stroke="var(--ink2)" stroke-width="1.5" stroke-dasharray="3 2"/></svg>
<figcaption><strong>{html.escape(title)}</strong><br>{w}, lineage {lid}: {life:,} steps, {peak:,} bodies at its peak<br>grid {side}x{side}; mass {mean("mass"):.0f}: hard {mean("hard"):.1f}, muscle {mean("muscle"):.0f}, sensor {mean("sensor"):.1f}, gut {mean("digestive"):.0f}; speed {mean("speed"):.2f}; flesh {meat:.0%}; {st.median(float(r["travel"]) for r in g):.0f} cells from its birthplace<br>{html.escape(what)}</figcaption></figure>""")
    return f"""<figure class="diagram"><div class="cards">{"".join(cards)}</div>
<figcaption>{caption}</figcaption></figure>"""


def data_table(data, every=10):
    cols = ["step", "pop", "grown", "births", "deaths_hunger", "deaths_broken", "plant_intake", "meat_intake", "scavenged", "mass_p50", "muscle_mean", "digestive_mean", "tooth", "lineages", "travel_p50", "grass", "wood", "ms_world", "ms_bodies"]
    out = []
    for w in WORLDS:
        L = data[w]["log"]
        body = "".join("<tr>" + "".join(f"<td>{L[c][i]:g}</td>" for c in cols) + "</tr>" for i in range(every - 1, len(L["step"]), every))
        out.append(f"<details><summary>{WORLD_NAME[w]}, every {every * 1000:,} steps</summary><div class='tw'><table><thead><tr>"
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
<svg viewBox="0 0 760 270" role="img" aria-label="The climate and the producers update every 10 steps; the bodies every step eat the grass and the dead, and return what they spend and what they are to the soil" style="max-width:100%;height:auto;display:block">
<defs><marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="currentColor"/></marker>
<marker id="arr1" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="var(--s1)"/></marker></defs>
<g fill="none" stroke="currentColor" stroke-width="1.2" font-size="12" font-family="system-ui, sans-serif">
  <rect x="20" y="30" width="170" height="64" rx="6"/>
  <text x="105" y="56" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">Climate (e061)</text>
  <text x="105" y="76" text-anchor="middle" fill="currentColor" stroke="none">every 10 steps</text>
  <rect x="290" y="30" width="190" height="64" rx="6"/>
  <text x="385" y="56" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">Producers and fire (e062)</text>
  <text x="385" y="76" text-anchor="middle" fill="currentColor" stroke="none">grass, wood, algae, litter</text>
  <line x1="190" y1="80" x2="288" y2="80" marker-end="url(#arr)"/>
  <text x="240" y="52" text-anchor="middle" fill="currentColor" stroke="none">light, warmth</text>
  <text x="240" y="66" text-anchor="middle" fill="currentColor" stroke="none">and water</text>
  <rect x="560" y="30" width="180" height="64" rx="6" stroke-dasharray="4 3"/>
  <text x="650" y="56" text-anchor="middle" fill="currentColor" stroke="none">wood, algae, litter</text>
  <text x="650" y="76" text-anchor="middle" fill="currentColor" stroke="none">not food yet</text>
  <line x1="480" y1="62" x2="558" y2="62" stroke-dasharray="4 3"/>
  <rect x="290" y="176" width="190" height="64" rx="6" stroke="var(--s1)" stroke-width="2"/>
  <text x="385" y="202" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">Bodies (e059's laws)</text>
  <text x="385" y="222" text-anchor="middle" fill="currentColor" stroke="none">every step, on land only</text>
  <line x1="385" y1="94" x2="385" y2="174" stroke="var(--s1)" stroke-width="2" marker-end="url(#arr1)"/>
  <text x="397" y="140" fill="currentColor" stroke="none">grass, bitten 0.02 a gut block</text>
  <rect x="20" y="176" width="170" height="64" rx="6"/>
  <text x="105" y="202" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">Soil and carrion</text>
  <text x="105" y="222" text-anchor="middle" fill="currentColor" stroke="none">the dead rot 1% a step</text>
  <line x1="288" y1="196" x2="192" y2="196" marker-end="url(#arr)"/>
  <text x="240" y="186" text-anchor="middle" fill="currentColor" stroke="none">spent, dead</text>
  <line x1="192" y1="222" x2="288" y2="222" marker-end="url(#arr)"/>
  <text x="240" y="240" text-anchor="middle" fill="currentColor" stroke="none">the dead eaten</text>
  <polyline points="105,174 105,134 250,134 330,96" marker-end="url(#arr)"/>
  <text x="178" y="124" text-anchor="middle" fill="currentColor" stroke="none">growth</text>
  <rect x="560" y="176" width="180" height="64" rx="6"/>
  <text x="650" y="202" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">The sea</text>
  <text x="650" y="222" text-anchor="middle" fill="currentColor" stroke="none">a wall to bodies</text>
  <line x1="558" y1="208" x2="482" y2="208" stroke-dasharray="4 3"/>
</g>
</svg>
<figcaption>Figure 1. The join. The world is e062's; the bodies are e059's. Grass is the only food the plants give (blue), what a body spends and what it is return to the soil under it, and the sea blocks a body's way.</figcaption>
</figure>
"""

# The text of the page: kept here to count its words against the skill's budget.
TEXT = {}


def main():
    data = {w: load(w) for w in WORLDS}
    a, b = data["c1225"], data["c1236"]
    ma, mb = a["mean"], b["mean"]
    row = lambda w: data[w]["row"]
    minutes = lambda w: row(w)["ms_step"] * 300_000 / 60_000

    charts_cost = [cost_chart(data), per_body_chart(data)]
    charts_pop = [pop_chart(data), grass_chart(data)]
    charts_eat = [flesh_chart(data)]

    # Table: second half of each run.
    def cells(fmt):
        return "".join(f"<td>{fmt(w)}</td>" for w in WORLDS)
    table_rows = [
        ("Bodies (mean, lowest-highest)", lambda w: f"{row(w)['pop_mean']:.0f} ({row(w)['pop_min']:.0f}-{row(w)['pop_max']:.0f})"),
        ("Land cells per body", lambda w: f"{(110625 if w == 'c1225' else 168035) / row(w)['pop_mean']:.0f}"),
        ("Lineages (top lineage's share)", lambda w: f"{data[w]['mean']('lineages'):.1f} ({data[w]['mean']('top_lineage'):.0%})"),
        ("A step: world + bodies (ms)", lambda w: f"{row(w)['ms_world']:.2f} + {row(w)['ms_bodies']:.2f}"),
        ("The world alone, no bodies (ms a step)", lambda w: f"{data[w]['ctl']('ms_step'):.2f}"),
        ("A body (µs a step)", lambda w: f"{row(w)['us_per_body']:.2f}"),
        ("300,000 steps on one core (min)", lambda w: f"{minutes(w):.0f}"),
        ("Intake: grass / kills / the dead", lambda w: f"{data[w]['plant_share']:.0%} / {data[w]['kill_share']:.0%} / {data[w]['dead_share']:.0%}"),
        ("Ways of living: per body / per lineage", lambda w: " / ".join(str(min(v)) if min(v) == max(v) else f"{min(v)}-{max(v)}" for v in (data[w]["ways_body"], data[w]["ways_lineage"]))),
        ("Grown bodies living the commonest way", lambda w: f"{data[w]['top_way_share']:.0%}"),
        ("Grown bodies' median distance from birth (cells)", lambda w: f"{data[w]['mean']('travel_p50'):.0f}"),
        ("Bodies in cold / mild / hot habitats", lambda w: " / ".join(f"{x:.0%}" for x in data[w]["bands"][:3])),
        ("Grass / litter / wood standing, of the control's", lambda w: " / ".join(f"{data[w]['mean'](k) / data[w]['ctl'](k):.0%}" for k in ("grass", "litter", "wood"))),
        ("Land burnt a year: control → with bodies", lambda w: f"{data[w]['burn_ctl']:.1%} → {data[w]['burn63']:.1%}"),
        ("Matter drift (largest)", lambda w: f"{row(w)['matter_err']:.0e}"),
    ]
    table = "".join(f"<tr><td>{name}</td>{cells(f)}</tr>" for name, f in table_rows)

    cold = [data[w]["bands"][0] for w in WORLDS]
    TEXT["tldr"] = (f"On e062's two worlds a step with bodies costs {row('c1225')['ms_step']:.2f} and {row('c1236')['ms_step']:.2f} ms on one core, "
                    f"{row('c1225')['ms_world'] / row('c1225')['ms_step']:.0%}-{row('c1236')['ms_world'] / row('c1236')['ms_step']:.0%} of it the world: "
                    "stage C needs neither threads nor a window. But the world feeds only about 300 bodies, 30 times fewer than foundation.md assumed, "
                    "and they live one way: roaming grass eaters without a tooth. Even so they hold the grass at a fifth of the world without them and halve its fires. "
                    "Next: set how much a body draws against what the plants grow.")
    TEXT["question"] = ("#76's first step: port the bodies onto the world that passed stage B and measure a step before choosing between threads and a "
                        "window of the world. The cost turns on how many bodies the world feeds, and e062's grass grows a twentieth of e059's sun. "
                        "Written before the runs:")
    TEXT["hyp"] = ["The world feeds 500-3,000 bodies.",
                   "A step costs at most 16 ms, so 300,000 steps take under 1.5 hours on one core.",
                   "The world stands 100,000 steps and its matter holds to 1e-9.",
                   "The cold habitats hold under 5% of the bodies."]
    TEXT["world"] = ("e062's climate, producers and fire, unchanged but for a field of the dead, and e059's bodies with every law its season "
                     "world kept; no law is new. Three choices join them: bodies live on land, a gut eats grass and the dead, and what a body "
                     "spends goes to the soil under it.")
    TEXT["runs"] = ("One pilot per world, seed 9, 100,000 steps (8.4 and 7.6 years), one thread each on the Mac, from 8,438 and 14,072 random "
                    "bodies, and a control of each world without bodies. Each world is grown once as e062 grew it. Every 1,000 steps we record:")
    TEXT["measures"] = [
        ("Bodies", "alive, and grown (300 steps or older, e060)."),
        ("Cost", "wall time a step, split into the world's update, the bodies and the lineages."),
        ("Intake", "what the bodies took in: grass, the blocks they broke (kills), the dead."),
        ("Ways of living", "e060's census on the grown bodies: diet, tooth, roaming."),
        ("Grass and fire", "standing grass, litter and wood, and the land burnt, against the control."),
        ("Matter", "the world's total against its start."),
    ]
    TEXT["v1"] = f"{ma('pop'):.0f} and {mb('pop'):.0f} bodies on average in the second half, lowest {row('c1225')['pop_min']:.0f} and {row('c1236')['pop_min']:.0f}."
    TEXT["v2"] = f"{row('c1225')['ms_step']:.2f} and {row('c1236')['ms_step']:.2f} ms a step: 300,000 steps take {minutes('c1225'):.0f} minutes."
    TEXT["v3"] = f"no world falls under {min(row(w)['pop_min'] for w in WORLDS):.0f} bodies; matter drifts by {max(row(w)['matter_err'] for w in WORLDS):.0e} at most."
    TEXT["v4"] = f"cold habitats hold {cold[0]:.0%} and {cold[1]:.0%}; the hot land (c1225) and the mild wet land (c1236) hold most."
    TEXT["r1"] = ("The world's update costs about a millisecond a step at 512, with or without bodies; the bodies add about a microsecond each over "
                  "150-900 of them. At this density a stage-C run is the world's cost, and seeds run side by side on one core each.")
    TEXT["r2"] = ("The random start crashes within 1,000 steps and the world settles at about 300 bodies, one per 360-530 land cells. Few as they "
                  "are, they hold the grass at a fifth of the control's: grass that grows by its own cover grows slowly once bitten down, so a "
                  "few roaming mouths are enough.")
    TEXT["r3"] = ("Nine in ten grown bodies live one way on both worlds, and counted per lineage there is one. Kills are 2-5% of the intake and "
                  "under 3% of the bodies carry a tooth: in a world this thin a body rarely meets another.")
    TEXT["gallery"] = "The commonest birth body of each world's two largest lineages, at the census where each had the most grown bodies. The dashed line is the front."
    TEXT["d1"] = ("Why so few: the bodies keep e059's economy, set against a sun of 0.01 a cell, while e062's grass grows 0.0004-0.0006 a land cell. "
                  "A body lives on hundreds of cells, far thinner than e058's thin world, where #68's rule 2 already cost most of the ways of living: "
                  "the crowd makes the niches. No trade-off of foundation.md can be judged at this density.")
    TEXT["d2"] = ("Stage B's balance does not hold under grazers: against the control, 300 bodies hold the grass at a fifth and the litter at a "
                  "third, halve the land that burns, and lower the wood, which nothing eats, by a sixth. Stage B's fire line was judged without anything eating the fuel.")
    TEXT["d3"] = ("What this does not show: one seed a world and 100,000 steps; the cost of a crowd (e059 measured 5 µs a body at 128); and the "
                  "three choices of the join, which were not varied.")
    TEXT["conclusion"] = ("Stage C runs one core a seed, with no threads and no window: at 512 the world costs a millisecond a step. The open number is "
                          "the density. How much a body draws against what the plants grow sets how many bodies live, and at 300 there is one way of "
                          "living. Next: make that ratio a parameter and find where the world holds a crowd, before the trade-offs are built.")

    picks = GALLERY_PICKS
    gal = gallery(data, picks, TEXT["gallery"])

    words = sum(len((" ".join(v) if isinstance(v, list) and v and isinstance(v[0], str) else " ".join(" ".join(x) for x in v) if isinstance(v, list) else v).split()) for v in TEXT.values())
    words += sum(len(p[3].split()) for p in picks)
    print(f"TEXT: {words} words")

    hyp = "".join(f"<li>{html.escape(h)}</li>" for h in TEXT["hyp"])
    measures = "".join(f"<li><strong>{html.escape(k)}</strong> - {html.escape(v)}</li>" for k, v in TEXT["measures"])
    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>e063 bodies on the stage-B world - Report</title>
<style>{CSS}</style>
</head>
<body>
<main>
<h1>e063: bodies on the stage-B world</h1>
<p class="sub">Experiment report - 2026-09-14 - e059's bodies on e062's worlds c1225 and c1236, one pilot each, 100,000 steps (foundation stage C, first step, #76)</p>

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
<thead><tr><th>Second half of the run</th><th>{WORLD_NAME["c1225"]}</th><th>{WORLD_NAME["c1236"]}</th></tr></thead>
<tbody>{table}</tbody></table></div>
<ol class="verdicts">
<li><span class="verdict no">No</span> 1, 500-3,000 bodies: {html.escape(TEXT["v1"])}</li>
<li><span class="verdict">Yes</span> 2, cheap: {html.escape(TEXT["v2"])}</li>
<li><span class="verdict">Yes</span> 3, it stands: {html.escape(TEXT["v3"])}</li>
<li><span class="verdict no">No</span> 4, under 5% cold: {html.escape(TEXT["v4"])}</li>
</ol>

<h3>3.1 The cost is the world's</h3>
<div class="grid2">{"".join(charts_cost)}</div>
<p>{html.escape(TEXT["r1"])}</p>

<h3>3.2 The world feeds about 300 bodies, and they hold the grass down</h3>
<div class="grid2">{"".join(charts_pop)}</div>
<p>{html.escape(TEXT["r2"])}</p>

<h3>3.3 One way of living</h3>
<div class="grid2">{"".join(charts_eat)}</div>
<p>{html.escape(TEXT["r3"])}</p>
{gal}

<h2>4. Discussion</h2>
<p>{html.escape(TEXT["d1"])}</p>
<p>{html.escape(TEXT["d2"])}</p>
<p>{html.escape(TEXT["d3"])}</p>

<h2>5. Conclusion and next step</h2>
<p>{html.escape(TEXT["conclusion"])}</p>

<h2>Appendix: data</h2>
<p>Rows of <code>results/&lt;world&gt;_life9_log.csv</code>; bodies are in <code>_agents.csv</code> every 10,000 steps, lineages in <code>_lineages.csv</code> and <code>_events.csv</code>, the run in one row in <code>_row.csv</code>. Build this report with <code>uv run python experiments/e063_bodies/report.py</code>.</p>
{data_table(data)}
</main>
</body>
</html>
"""
    out = os.path.join(HERE, "report.html")
    with open(out, "w") as f:
        f.write(page)
    print(f"wrote {out} ({os.path.getsize(out)//1024} KB)")


# (world, lineage, title, what the shape does): filled from the bodies the runs made.
GALLERY_PICKS = [
    ("c1225", "1", "Mouth first",
     "A front row of gut and seven muscles down one side: every step forward lays the guts on grass not yet bitten, pushed by a soft face."),
    ("c1225", "2", "Gut on one side, motor on the other",
     "Guts on the front and left, muscle on the right, and three sensors between them: it sees four cells ahead."),
    ("c1236", "31", "Small and quick",
     "Thirteen blocks, a row of gut over a knot of muscle: the lightest and the fastest of the four."),
    ("c1236", "44", "Motor in front, cup of gut behind",
     "Two rows of muscle lead; the gut is a cup at the back and eats the cells the body has just walked onto."),
]

if __name__ == "__main__":
    main()
