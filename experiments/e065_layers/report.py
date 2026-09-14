#!/usr/bin/env python3
"""Build report.html for e065 (the water's two layers, foundation stage C, third step, #79).

Charts: matplotlib, exported as SVG and inlined. Diagram: hand-written SVG.
Run from the repo root: uv run python experiments/e065_layers/report.py
(`--picks` prints the bodies of the largest lineages by medium, to choose the gallery.)
"""
import csv
import html
import io
import math
import os
import statistics as st
import sys
from collections import Counter, defaultdict

import matplotlib
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from matplotlib.ticker import FixedLocator, MaxNLocator

matplotlib.use("svg")

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "experiments", "e060_census"))
import census  # noqa: E402  (e060's census of ways of living)

SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4"]  # fixed slot order
MEDIA = ["land", "surface", "bottom"]
WALL, OPEN = SERIES[0], SERIES[1]  # e064 (the sea a wall), e065 (the water open)
MEDIUM_COLOR = {"land": SERIES[3], "surface": SERIES[2], "bottom": SERIES[4]}
KIND_COLOR = {1: SERIES[0], 2: SERIES[1], 3: SERIES[3], 4: SERIES[2]}  # hard, muscle, sensor, gut: the viewer's
E064 = os.path.join(ROOT, "experiments", "e064_scale", "results", "c1225_life9_s0.0625")
E065 = os.path.join(HERE, "results", "c1225_life9_water")
ALONE = os.path.join(HERE, "results", "c1225_life9_alone")
CONFINED = 0.9  # a lineage lives in one medium when this share of its grown bodies stands there

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
    with open(path) as f:
        return list(csv.DictReader(f))


def columns(path):
    r = rows(path)
    return {k: [float(x[k]) for x in r] for k in r[0]}


def medium(r):
    return MEDIA[int(r.get("medium", 0))]


def by_lineage_way(grown, key):
    """e060's census by lineage, with the way of living read by `key`."""
    by = defaultdict(Counter)
    for r in grown:
        w = key(r)
        if w:
            by[r["lineage"]][w] += 1
    out = Counter()
    for c in by.values():
        out[c.most_common(1)[0][0]] += sum(c.values())
    return out


def with_medium(r):
    w = census.way(r)
    return w and w + (medium(r),)


def load(pre):
    d = {"log": columns(pre + "_log.csv"), "row": {k: float(v) for k, v in rows(pre + "_row.csv")[0].items()}}
    d["agents"] = census.read(pre + "_agents.csv")
    d["lineages"] = rows(pre + "_lineages.csv")
    L = d["log"]
    last = L["step"][-1]
    late = [i for i, x in enumerate(L["step"]) if 2 * x > last]
    d["late"] = late
    d["mean"] = lambda k: st.mean(L[k][i] for i in late)
    total = lambda k: sum(L[k][i] for i in late)
    d["total"] = total
    eat = total("plant_intake") + total("meat_intake")
    d["kill_share"] = (total("meat_intake") - total("scavenged")) / eat
    d["no_room"] = total("no_room") / total("children")
    d["contacts"] = d["mean"]("contacts") / d["mean"]("pop") / 1000
    if "kills_land" in L:
        d["kills_by"] = {m: total("kills_" + m) / max(total("intake_" + m) + total("kills_" + m), 1e-12) for m in MEDIA}
    dumps = list(census.late(list(d["agents"])))
    d["dumps"] = dumps
    d["ways_body"], d["ways_lineage"], d["ways_body_m"], d["ways_lineage_m"], d["confined"] = [], [], [], [], []
    d["density"] = defaultdict(list)
    top, grown_n = Counter(), 0
    for x in dumps:
        rs = d["agents"][x]
        g = census.grown(rs)
        d["ways_body"].append(census.count(census.census(rs)))
        d["ways_lineage"].append(census.count(census.census_by_lineage(rs)))
        d["ways_body_m"].append(census.count(Counter(w for w in map(with_medium, g) if w)))
        d["ways_lineage_m"].append(census.count(by_lineage_way(g, with_medium)))
        where = defaultdict(Counter)
        for r in g:
            where[r["lineage"]][medium(r)] += 1
        d["confined"].append(sum(sum(c.values()) for c in where.values() if max(c.values()) >= CONFINED * sum(c.values())) / max(len(g), 1))
        for r in rs:
            d["density"][medium(r)].append(float(r["density"]))
        for r in g:
            w = with_medium(r)
            if w:
                top[w] += 1
                grown_n += 1
    d["top_way"] = top.most_common(1)[0]
    d["top_way_share"] = top.most_common(1)[0][1] / grown_n
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


def pop_chart(wall, water):
    fig, ax = new_axes()
    ax.plot(wall["log"]["step"], wall["log"]["pop"], color=WALL, linewidth=1.6, label="sea a wall (e064)")
    L = water["log"]
    ax.plot(L["step"], L["pop"], color=OPEN, linewidth=1.6, label="water open: all")
    for m in MEDIA:
        ax.plot(L["step"], L["pop_" + m], color=MEDIUM_COLOR[m], linewidth=1.3, label=m)
    ax.set_ylim(0, None)
    ax.yaxis.set_major_locator(MaxNLocator(4))
    ax.yaxis.set_major_formatter(kfmt)
    ax.set_ylabel("bodies")
    legend_above(ax, 5)
    return figure("The water fills at both layers",
                  "Bodies alive every 1,000 steps: with the sea a wall (e064), and with the water open, all and by where the middle of a body stands.",
                  to_svg(fig))


def density_hist(wall, water):
    fig, ax = new_axes("density (log scale)")
    ax.xaxis.set_major_formatter(lambda x, _p: f"{2.0 ** x:g}")
    edges = [-1 + 2 * i / 40 for i in range(41)]
    lg = lambda v: [math.log2(x) for x in v]
    n_wall = len(wall["dumps"])
    ax.hist(lg(wall["density"]["land"]), bins=edges, weights=[1 / n_wall] * len(wall["density"]["land"]), histtype="step", color=WALL, linewidth=1.6, label="sea a wall (e064)")
    n = len(water["dumps"])
    data = [lg(water["density"][m]) for m in MEDIA]
    ax.hist(data, bins=edges, weights=[[1 / n] * len(v) for v in data], stacked=True, color=[MEDIUM_COLOR[m] for m in MEDIA], label=[f"open: {m}" for m in MEDIA])
    ax.axvline(0, color=INK, linewidth=1, linestyle=(0, (2, 2)))
    ax.set_xticks([-1, 0, 1])
    ax.set_xlim(-1, 1)
    ax.yaxis.set_major_locator(MaxNLocator(4))
    ax.yaxis.set_major_formatter(kfmt)
    ax.set_ylabel("bodies at a census")
    legend_above(ax, 4)
    return figure("Density splits at the density of water",
                  "Bodies by density at the censuses of the second half, per census; the water run stacked by medium. Dotted: 1, the density of water.",
                  to_svg(fig))


def density_time(wall, water):
    fig, ax = new_axes()
    ax.plot(wall["log"]["step"], wall["log"]["density_mean"], color=WALL, linewidth=1.6, label="sea a wall (e064)")
    L = water["log"]
    for m in MEDIA:
        ax.plot(L["step"], L["density_" + m], color=MEDIUM_COLOR[m], linewidth=1.4, label=f"open: {m}")
    ax.axhline(1.0, color=INK, linewidth=1, linestyle=(0, (2, 2)))
    ax.set_ylim(0.5, 2.05)
    ax.yaxis.set_major_locator(FixedLocator([0.5, 1.0, 1.5, 2.0]))
    ax.set_ylabel("mean density")
    legend_above(ax, 4)
    return figure("Nothing runs to the ceiling",
                  "Mean density of the bodies alive every 1,000 steps. A genome expresses 1/2 to 2; with the sea a wall every body ends near 2. Dotted: water.",
                  to_svg(fig))


def kills_chart(wall, water):
    fig, ax = new_axes()
    W = wall["log"]
    eat = [p + m for p, m in zip(W["plant_intake"], W["meat_intake"])]
    ax.plot(W["step"], [(m - v) / e if e > 0 else 0 for m, v, e in zip(W["meat_intake"], W["scavenged"], eat)], color=WALL, linewidth=1.6, label="sea a wall (e064)")
    L = water["log"]
    for m in MEDIA:
        ax.plot(L["step"], [k / (i + k) if i + k > 0 else 0 for i, k in zip(L["intake_" + m], L["kills_" + m])], color=MEDIUM_COLOR[m], linewidth=1.4, label=f"open: {m}")
    ax.set_ylim(0, None)
    percent(ax)
    ax.yaxis.set_major_locator(MaxNLocator(4))
    legend_above(ax, 4)
    return figure("Where bodies kill",
                  "Kills as a share of what bodies took in over each 1,000 steps, by the medium of the eater. Zero would be a medium where nobody breaks another.",
                  to_svg(fig))


def ways_chart(wall, water):
    fig, ax = plt.subplots(figsize=(6.4, 2.6))
    groups = [("all grown", "ways_body", "ways_body_m"), ("within a lineage", "ways_lineage", "ways_lineage_m")]
    width = 0.26
    for j, (name, plain, with_m) in enumerate(groups):
        for off, (d, key, color, alpha) in zip((-width, 0, width), ((wall, plain, WALL, 1.0), (water, plain, OPEN, 1.0), (water, with_m, OPEN, 0.45))):
            v = d[key]
            m = st.mean(v)
            ax.bar(j + off, m, width=width * 0.92, color=color, alpha=alpha, yerr=[[m - min(v)], [max(v) - m]], error_kw={"ecolor": INK, "elinewidth": 1, "capsize": 3})
    ax.set_xticks(range(len(groups)), [g[0] for g in groups])
    ax.set_ylim(0, None)
    ax.yaxis.set_major_locator(MaxNLocator(4, integer=True))
    ax.set_ylabel("ways of living")
    legend_above(ax, 3, handles=[Patch(color=WALL, label="sea a wall (e064)"), Patch(color=OPEN, label="water open"), Patch(color=OPEN, alpha=0.45, label="water open, medium counted")])
    return figure("Ways of living, with and without the medium",
                  "e060's ways (diet, tooth, roaming) among the grown bodies, and with the medium as a fourth part; the mean of the second half's censuses, whiskers the fewest to the most.",
                  to_svg(fig))


def jam_chart(wall, water):
    fig, ax = new_axes()
    ax.plot(wall["log"]["step"], wall["log"]["blocked"], color=WALL, linewidth=1.6, label="sea a wall (e064)")
    L = water["log"]
    for m in MEDIA:
        ax.plot(L["step"], L["blocked_" + m], color=MEDIUM_COLOR[m], linewidth=1.4, label=f"open: {m}")
    ax.set_ylim(0, 0.8)
    percent(ax)
    ax.yaxis.set_major_locator(MaxNLocator(4))
    legend_above(ax, 4)
    return figure("The jam by medium",
                  "Share of the steps forward that another body (or the sea wall) blocked over each 1,000 steps, by where the mover stands.",
                  to_svg(fig))


def food_chart(water, alone):
    fig, ax = new_axes()
    A, L = alone, water["log"]
    ax.plot(A["step"], A["algae"], color=MEDIUM_COLOR["surface"], linewidth=1.2, linestyle=(0, (3, 2)), label="algae, no bodies")
    ax.plot(L["step"], L["algae"], color=MEDIUM_COLOR["surface"], linewidth=1.6, label="algae")
    ax.plot(A["step"], A["litter_sea"], color=MEDIUM_COLOR["bottom"], linewidth=1.2, linestyle=(0, (3, 2)), label="bottom litter, no bodies")
    ax.plot(L["step"], L["litter_sea"], color=MEDIUM_COLOR["bottom"], linewidth=1.6, label="bottom litter")
    ax.set_ylim(0, None)
    ax.yaxis.set_major_locator(MaxNLocator(4))
    ax.yaxis.set_major_formatter(kfmt)
    ax.set_ylabel("matter standing")
    legend_above(ax, 2)
    return figure("What the water's bodies eat down",
                  "Algae (the surface's food) and the algae's dead on the bottom, summed over the world every 1,000 steps. Dashed: the same world without bodies.",
                  to_svg(fig))


def cost_chart(wall, water):
    fig, ax = new_axes("bodies")
    ax.margins(x=0.02)
    top = 0
    for d, color, name in ((wall, WALL, "sea a wall (e064)"), (water, OPEN, "water open")):
        L = d["log"]
        ax.scatter(L["pop"][2:], [b + g for b, g in zip(L["ms_bodies"][2:], L["ms_lineage"][2:])], s=10, color=color, label=name, linewidths=0)
        top = max(top, max(L["pop"][2:]))
    for us, dash in ((1, (2, 2)), (2, (5, 2))):
        ax.plot([0, top], [0, top * us / 1000], color=INK, linewidth=1, linestyle=(0, dash))
    ax.set_xlim(0, top * 1.05)
    ax.set_ylim(0, None)
    ax.yaxis.set_major_locator(MaxNLocator(4))
    ax.xaxis.set_major_formatter(kfmt)
    ax.set_ylabel("ms a step (bodies)")
    legend_above(ax, 2)
    return figure("A body still costs one to two microseconds",
                  "Each dot is 1,000 steps: bodies alive against what bodies and lineages cost a step on one core (the start's crash left out). Dotted: 1 µs a body; dashed: 2 µs.",
                  to_svg(fig))


def modal_body(d, lid):
    """The most common birth body of a lineage's grown bodies at the census where it has the most of them."""
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


def gallery(d, picks, caption):
    cards = []
    for lid, title, what in picks:
        x, g, side, cells = modal_body(d, lid)
        span = [int(r["step"]) for r in d["lineages"] if r["lineage"] == lid]
        life = (max(span) - min(span) + 1000) if span else 0
        peak = max((int(r["size"]) for r in d["lineages"] if r["lineage"] == lid), default=0)
        u = 88 / side
        rects = "".join(f'<rect x="{(i % side) * u:.2f}" y="{(i // side) * u:.2f}" width="{u * 0.9:.2f}" height="{u * 0.9:.2f}" fill="{KIND_COLOR[int(k)]}"/>'
                        for i, k in enumerate(cells) if k != "0")
        mean = lambda k: st.mean(float(r[k]) for r in g)
        intake = sum(float(r["meat"]) + float(r["plant"]) for r in g)
        kills = sum(float(r["killed"]) for r in g) / max(intake, 1e-9)
        where = Counter(medium(r) for r in g).most_common(1)[0]
        cards.append(f"""<figure class="card"><svg viewBox="-1 -1 89 89" width="120" height="120" role="img" aria-label="{html.escape(title)}"><rect x="-1" y="-1" width="89" height="89" fill="var(--cell)"/>{rects}<line x1="-1" y1="-0.5" x2="88" y2="-0.5" stroke="var(--ink2)" stroke-width="1.5" stroke-dasharray="3 2"/></svg>
<figcaption><strong>{html.escape(title)}</strong><br>lineage {lid}: {life:,} steps, {peak:,} bodies at its peak, {where[1] / len(g):.0%} {where[0]}<br>grid {side}x{side}; mass {mean("mass"):.0f}, density {mean("density"):.2f}: hard {mean("hard"):.1f}, muscle {mean("muscle"):.0f}, sensor {mean("sensor"):.1f}, gut {mean("digestive"):.0f}; kills {kills:.0%} of its intake<br>{html.escape(what)}</figcaption></figure>""")
    return f"""<figure class="diagram"><div class="cards">{"".join(cards)}</div>
<figcaption>{caption}</figcaption></figure>"""


def print_picks(d):
    peaks = Counter()
    for r in d["lineages"]:
        peaks[r["lineage"]] = max(peaks[r["lineage"]], int(r["size"]))
    for lid, peak in peaks.most_common(16):
        x, g, side, cells = modal_body(d, lid)
        if not g:
            continue
        mean = lambda k: st.mean(float(r[k]) for r in g)
        intake = sum(float(r["meat"]) + float(r["plant"]) for r in g)
        where = Counter(medium(r) for r in g)
        print(f"lineage {lid}: peak {peak}, {len(g)} grown at {x}, {dict(where)}, side {side}, mass {mean('mass'):.0f} density {mean('density'):.2f} "
              f"hard {mean('hard'):.1f} muscle {mean('muscle'):.1f} sensor {mean('sensor'):.1f} gut {mean('digestive'):.1f} speed {mean('speed'):.2f} "
              f"kills {sum(float(r['killed']) for r in g) / max(intake, 1e-9):.0%} dead {sum(float(r['scavenged']) for r in g) / max(intake, 1e-9):.0%} "
              f"algae {sum(float(r['algae']) for r in g) / max(intake, 1e-9):.0%} detritus {sum(float(r['detritus']) for r in g) / max(intake, 1e-9):.0%} "
              f"tooth {st.mean(int(r['born_bite']) >= 2 for r in g):.0%} travel {st.median(float(r['travel']) for r in g):.0f}")
        for i in range(side):
            print("    " + "".join(".HMSG"[int(k)] for k in cells[i * side:(i + 1) * side]))


def data_table(runs, every=10):
    cols = ["step", "pop", "pop_land", "pop_surface", "pop_bottom", "births", "no_room", "contacts", "plant_intake", "meat_intake", "scavenged",
            "algae_intake", "detritus_intake", "density_land", "density_surface", "density_bottom", "blocked", "lineages", "algae", "litter_sea", "ms_bodies", "ms_lineage"]
    out = []
    for name, d in runs:
        L = d["log"]
        cs = [c for c in cols if c in L]
        body = "".join("<tr>" + "".join(f"<td>{L[c][i]:g}</td>" for c in cs) + "</tr>" for i in range(every - 1, len(L["step"]), every))
        out.append(f"<details><summary>{name}, every {every * 1000:,} steps</summary><div class='tw'><table><thead><tr>"
                   + "".join(f"<th>{c}</th>" for c in cs) + f"</tr></thead><tbody>{body}</tbody></table></div></details>")
    return "\n".join(out)


# ---------- page ----------

CSS = f"""
:root {{
  --surface: #fcfcfb; --page: #f9f9f7; --ink: #0b0b0b; --ink2: #52514e; --grid: #e1e0d9; --border: rgba(11,11,11,0.10);
  --s1: {SERIES[0]}; --cell: #f1f0ea; --water: rgba(42,120,214,0.07);
}}
@media (prefers-color-scheme: dark) {{
  :root:not([data-theme="light"]) {{
    --surface: #1a1a19; --page: #0d0d0d; --ink: #ffffff; --ink2: #c3c2b7; --grid: #2c2c2a; --border: rgba(255,255,255,0.10);
    --s1: #3987e5; --cell: #262624; --water: rgba(57,135,229,0.12);
  }}
}}
:root[data-theme="dark"] {{
  --surface: #1a1a19; --page: #0d0d0d; --ink: #ffffff; --ink2: #c3c2b7; --grid: #2c2c2a; --border: rgba(255,255,255,0.10);
  --s1: #3987e5; --cell: #262624; --water: rgba(57,135,229,0.12);
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
<svg viewBox="0 0 760 300" role="img" aria-label="Land has one layer shared by every body; a water cell has a surface layer for bodies lighter than water, eating algae, and a bottom layer for denser bodies, eating what sinks" style="max-width:100%;height:auto;display:block">
<defs><marker id="arr1" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="var(--s1)"/></marker></defs>
<g fill="none" stroke="currentColor" stroke-width="1.2" font-size="12" font-family="system-ui, sans-serif">
  <rect x="20" y="30" width="220" height="220" rx="6"/>
  <text x="130" y="56" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">Land: one layer</text>
  <text x="130" y="96" text-anchor="middle" fill="currentColor" stroke="none">every body meets every body</text>
  <text x="130" y="136" text-anchor="middle" fill="currentColor" stroke="none">a gut eats grass and the dead</text>
  <text x="130" y="176" text-anchor="middle" fill="currentColor" stroke="none">a denser soft face breaks</text>
  <text x="130" y="194" text-anchor="middle" fill="currentColor" stroke="none">a lighter one (e025)</text>
  <rect x="270" y="30" width="470" height="220" rx="6" fill="var(--water)"/>
  <text x="505" y="56" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">Water: two layers</text>
  <text x="300" y="92" fill="currentColor" stroke="none" font-weight="600">Surface: density under 1</text>
  <text x="300" y="112" fill="currentColor" stroke="none">a gut eats the algae</text>
  <line x1="290" y1="140" x2="720" y2="140" stroke-dasharray="5 4"/>
  <text x="720" y="132" text-anchor="end" fill="currentColor" stroke="none">the layers never meet</text>
  <text x="300" y="186" fill="currentColor" stroke="none" font-weight="600">Bottom: density 1 or more</text>
  <text x="300" y="206" fill="currentColor" stroke="none">a gut eats the algae's dead</text>
  <text x="300" y="224" fill="currentColor" stroke="none">and the dead of the bodies</text>
  <line x1="530" y1="84" x2="530" y2="212" stroke="var(--s1)" stroke-width="2" marker-end="url(#arr1)"/>
  <text x="544" y="176" fill="currentColor" stroke="none">what dies sinks</text>
  <text x="380" y="282" text-anchor="middle" fill="currentColor" stroke="none">the price: a face resists hardness × density, so a light body is a soft one wherever it meets a denser body</text>
</g>
</svg>
<figcaption>Figure 1. The water's two layers. A body's density, fixed at birth, picks its layer in the water. The algae's dead lie on the bottom as litter before they rot (blue). Bodies spend into the soil under them, on land and in the water.</figcaption>
</figure>
"""


def mix_chart(water, n=10):
    """The medium of each large lineage's grown bodies over the second half's censuses."""
    mix, dens = defaultdict(Counter), defaultdict(list)
    for x in water["dumps"]:
        for r in census.grown(water["agents"][x]):
            mix[r["lineage"]][medium(r)] += 1
            dens[r["lineage"]].append(float(r["density"]))
    top = sorted(mix, key=lambda lid: -sum(mix[lid].values()))[:n]
    fig, ax = plt.subplots(figsize=(6.4, 2.9))
    for j, lid in enumerate(reversed(top)):
        total, left = sum(mix[lid].values()), 0.0
        for m in MEDIA:
            share = mix[lid][m] / total
            ax.barh(j, share, left=left, color=MEDIUM_COLOR[m], height=0.72, label=m if j == 0 else None)
            left += share
    labels = [f"{lid} ({st.median(dens[lid]):.2f})" for lid in reversed(top)]
    ax.set_yticks(range(len(top)), labels)
    ax.set_xlim(0, 1)
    ax.xaxis.set_major_formatter(lambda y, _p: f"{y:.0%}")
    ax.set_xlabel("share of the lineage's grown bodies", loc="right")
    ax.grid(axis="y", visible=False)
    ax.grid(axis="x", visible=True)
    legend_above(ax, 3)
    return figure("A lineage at the density of water lives everywhere",
                  "The ten largest lineages of the second half (median density in brackets), by where their grown bodies stand. One colour per bar would be kinds kept to a medium.",
                  to_svg(fig))


# The text of the page: kept here to count its words against the skill's budget.
TEXT = {}

# (lineage, title, what the shape does): filled from the bodies the run made (`--picks`).
GALLERY_PICKS = [
    ("1", "A ring of gut around a motor",
     "Gut on every edge takes food under whatever medium the body stands on; its children fall on both sides of water's density. The largest lineage, in all three media."),
    ("1179", "A frame of gut with a column of eyes",
     "Four sensors see five cells; at density 1.02 it lives mostly at the surface and eats algae."),
    ("6", "Muscle behind a toothed flank",
     "A hard block with muscle behind breaks the softest faces there are, the surface's; a fifth of its intake is kills."),
    ("1418", "A dense grazer of the land",
     "At density 1.62 no light body can break it and it cannot live at the surface: it keeps to land and eats grass."),
    ("1000", "Half muscle, between land and bottom",
     "Dense and without a hard block, it breaks lighter faces by pressing: a third of its intake is kills, a fifth the bottom's litter."),
    ("1726", "A crusher at the ceiling",
     "Density 1.96, almost all muscle and five gut blocks: half its intake is kills, on the bottom and the land."),
]


def main():
    wall, water = load(E064), load(E065)
    if "--picks" in sys.argv:
        print_picks(water)
        return
    alone = columns(ALONE + "_log.csv")
    late = water["late"]
    alone_mean = lambda k: st.mean(alone[k][i] for i in late)
    W, E = wall, water
    tot = E["total"]
    minutes = lambda d: d["row"]["ms_step"] * 300_000 / 60_000
    ways = lambda v: str(min(v)) if min(v) == max(v) else f"{min(v)}-{max(v)}"
    share = {m: E["mean"]("pop_" + m) / E["mean"]("pop") for m in MEDIA}
    eat = tot("plant_intake") + tot("meat_intake")
    grass = tot("plant_intake") - tot("algae_intake") - tot("detritus_intake")
    kills = tot("meat_intake") - tot("scavenged")
    w_eat = W["total"]("plant_intake") + W["total"]("meat_intake")
    confined = lambda d: f"{min(d['confined']):.0%}-{max(d['confined']):.0%}"

    table_rows = [
        ("Bodies (mean, lowest-highest)", lambda d: f"{d['row']['pop_mean']:,.0f} ({d['row']['pop_min']:,.0f}-{d['row']['pop_max']:,.0f})"),
        ("On land / at the surface / on the bottom", lambda d: " / ".join(f"{d['mean']('pop_' + m) / d['mean']('pop'):.0%}" for m in MEDIA) if d is E else "100% / - / -"),
        ("Contacts per body a step", lambda d: f"{d['contacts']:.3f}"),
        ("Intake: grass / algae / algae's dead / kills / the dead",
         lambda d: f"{grass / eat:.0%} / {tot('algae_intake') / eat:.0%} / {tot('detritus_intake') / eat:.0%} / {kills / eat:.0%} / {tot('scavenged') / eat:.0%}" if d is E
         else f"{W['total']('plant_intake') / w_eat:.0%} / - / - / {W['kill_share']:.0%} / {W['total']('scavenged') / w_eat:.0%}"),
        ("Kills' share of intake: land / surface / bottom", lambda d: " / ".join(f"{d['kills_by'][m]:.0%}" for m in MEDIA) if d is E else f"{W['kill_share']:.0%} / - / -"),
        ("Mean density: all; land / surface / bottom", lambda d: f"{d['mean']('density_mean'):.2f}; " + (" / ".join(f"{d['mean']('density_' + m):.2f}" for m in MEDIA) if d is E else "- / - / -")),
        ("Bodies lighter than water", lambda d: f"{d['mean']('light_share'):.0%}" if d is E else f"{sum(x < 1 for x in W['density']['land']) / len(W['density']['land']):.0%}"),
        ("Grown bodies in lineages keeping 90% in one medium", lambda d: confined(d) if d is E else "100%"),
        ("Ways of living, all / per lineage; with the medium", lambda d: f"{ways(d['ways_body'])} / {ways(d['ways_lineage'])}" + (f"; {ways(d['ways_body_m'])} / {ways(d['ways_lineage_m'])}" if d is E else "")),
        ("Lineages alive (top lineage's share)", lambda d: f"{d['mean']('lineages'):.1f} ({d['mean']('top_lineage'):.0%})"),
        ("Moves blocked; children with no room", lambda d: f"{d['mean']('blocked'):.0%}; {d['no_room']:.0%}"),
        ("Standing, of the world alone: grass / algae / bottom litter", lambda d: f"{d['mean']('grass') / alone_mean('grass'):.1%} / " + (f"{d['mean']('algae') / alone_mean('algae'):.1%} / {d['mean']('litter_sea') / alone_mean('litter_sea'):.1%}" if d is E else "100% / -")),
        (f"Grass grown a step (alone {alone_mean('grass_grown'):.1f})", lambda d: f"{d['mean']('grass_grown'):.1f}"),
        ("A step: world + bodies + lineages (ms)", lambda d: f"{d['row']['ms_world']:.2f} + {d['row']['ms_bodies']:.2f} + {d['row']['ms_lineage']:.2f}"),
        ("300,000 steps on one core (min)", lambda d: f"{minutes(d):.0f}"),
    ]
    table = "".join(f"<tr><td>{name}</td><td>{f(W)}</td><td>{f(E)}</td></tr>" for name, f in table_rows)
    for name, f in table_rows:
        print(f"{name}: {f(W)} | {f(E)}")

    charts_fill = [pop_chart(W, E), food_chart(E, alone)]
    charts_density = [density_hist(W, E), mix_chart(E)]
    charts_ways = [ways_chart(W, E), kills_chart(W, E)]
    charts_cost = [jam_chart(W, E), cost_chart(W, E)]

    TEXT["tldr"] = (f"A water cell got a surface layer for bodies lighter than water and a bottom layer for denser ones. "
                    f"The crowd moved in ({share['surface']:.0%} at the surface, {share['bottom']:.0%} on the bottom), and density came off its ceiling "
                    f"(mean {E['mean']('density_mean'):.2f}, e064 {W['mean']('density_mean'):.2f}). But the largest lineages sit at the density of water and live "
                    f"in all three media, and the world holds no more bodies. Kept; next, a trade-off between land and water that density cannot cross.")
    TEXT["question"] = ("e064's crowd lived on land, jammed, and every body was as dense as a genome allows, since a denser soft face breaks a lighter one. "
                        "foundation.md's first trade-off prices density: a body lighter than water lives at the surface, a denser one on the bottom, "
                        "each touching and eating only its layer. Written before the run:")
    TEXT["hyp"] = ["The water fills at both layers: 2-5 times e064's bodies, each layer with 10% or more.",
                   "Density splits around 1: the surface just under it, land and bottom near the ceiling of 2.",
                   "Kinds by medium: 90% of grown bodies in lineages that keep to one medium.",
                   "Land's jam within 10 points of e064's; under 50 ms a step."]
    TEXT["world"] = ("e064's world and bodies at s = 1/16, the sea opened. A body's density, fixed at birth, picks its layer; the layers never meet. "
                     "Land keeps one layer, shared.")
    TEXT["runs"] = ("c1225 with draw d11, seed 9, 100,000 steps, one core. Control: e064's s = 1/16 run, the sea a wall; with the water closed this code "
                    "reproduces it exactly. The world without bodies, under the new law, gives the producers' stands. Every 1,000 steps we record:")
    TEXT["measures"] = [
        ("Bodies", "alive and by medium: land, surface, bottom (where a body's middle stands)."),
        ("Density", "its spread, and each lineage's medium."),
        ("Intake", "grass, algae, the algae's dead, kills and the dead, by medium."),
        ("Ways of living", "e060's census (diet, tooth, roaming), with and without the medium."),
        ("The crowd", "moves blocked and children with no room."),
        ("Producers and cost", "standing against the world alone; wall time a step."),
    ]
    TEXT["v1"] = f"{share['surface']:.0%} at the surface and {share['bottom']:.0%} on the bottom, but {E['row']['pop_mean']:,.0f} bodies against e064's {W['row']['pop_mean']:,.0f}."
    TEXT["v2"] = f"the surface sits at {E['mean']('density_surface'):.2f}; land and bottom at {E['mean']('density_land'):.2f} and {E['mean']('density_bottom'):.2f}, not near 2."
    TEXT["v3"] = f"{confined(E)} of grown bodies are in lineages that keep 90% to one medium."
    TEXT["v4"] = f"land's moves blocked {E['mean']('blocked_land'):.0%} against {W['mean']('blocked'):.0%}; a step {E['row']['ms_step']:.0f} ms."
    TEXT["r1"] = (f"More ground did not buy more bodies. Every producer grows by its own stand, and the crowd eats all three down: the algae stand at "
                  f"{E['mean']('algae') / alone_mean('algae'):.0%} of the world alone, the bottom's litter at {E['mean']('litter_sea') / alone_mean('litter_sea'):.0%}, "
                  f"the grass at {E['mean']('grass') / alone_mean('grass'):.1%} (e064: {W['mean']('grass') / alone_mean('grass'):.0%}). The water feeds "
                  f"{(tot('algae_intake') + tot('detritus_intake')) / eat:.0%} of the intake, and land holds fewer bodies than before.")
    TEXT["r2"] = ("Density splits in two groups, not three. The largest lineages sit at 1.00: denser than anything at the surface, and a mutation from the bottom, "
                  "so their children land in either layer and on the shore. Dense lineages (1.2-1.95) keep to land and the bottom, where they are the harder faces.")
    TEXT["r3"] = (f"Counting the medium as part of a way of living gives {ways(E['ways_lineage_m'])} ways per lineage, but mostly because one lineage spans the media. "
                  f"Kills follow density: {E['kills_by']['surface']:.0%} of the surface's intake, where every face is soft and similar, "
                  f"{E['kills_by']['land']:.0%} on land, where dense and light bodies meet.")
    TEXT["r4"] = (f"The jam eases where bodies spread: {E['mean']('blocked_bottom'):.0%} of moves blocked on the bottom, {E['mean']('blocked_land'):.0%} on land, "
                  f"children with no room {E['no_room']:.0%} (e064 {W['no_room']:.0%}). A body still costs one to two microseconds; lineage detection fell to "
                  f"{E['row']['ms_lineage']:.2f} ms a step.")
    TEXT["gallery"] = "The commonest birth body of six lineages, at the census where each had the most grown bodies. The dashed line is the front."
    TEXT["d1"] = ("The price works: once a light body has a place of its own, density stops being free armor and the ceiling no longer binds. "
                  "But a layer picked by a threshold on one gene-expressed number makes the threshold itself the best place to be. A lineage at 1.00 "
                  "is the hardest thing at the surface and one mutation from the bottom, so it lives in both, and on land too.")
    TEXT["d2"] = ("Kinds kept to a medium need a trade-off a body cannot cross by one small change: a medium that asks for different blocks, not a different "
                  "density. foundation.md's next row, dry air (soft blocks lose water out of the water), is one. The number of bodies is set by producers "
                  "that grow from their stand, and opening a pasture spreads the same grazing over more ground.")
    TEXT["d3"] = ("Not shown: other seeds, c1236, runs past 100,000 steps (the bodies fell from 7,800 at 30,000 steps to about 5,300), and pools, which "
                  "stay land for a body.")
    TEXT["conclusion"] = ("The water's two layers are kept for stage C: both layers fill and density is priced. They do not make kinds by medium, because "
                          "density at the water's own value lets one lineage live everywhere. Next, to agree in #79: dry air, the land-water "
                          "trade-off that asks for armor, not density.")

    gal = gallery(E, GALLERY_PICKS, TEXT["gallery"])
    words = sum(len((" ".join(v) if isinstance(v, list) and v and isinstance(v[0], str) else " ".join(" ".join(t) for t in v) if isinstance(v, list) else v).split()) for v in TEXT.values())
    words += sum(len(p[2].split()) for p in GALLERY_PICKS)
    print(f"TEXT: {words} words")
    for k, v in TEXT.items():
        n = len((" ".join(v) if isinstance(v, list) and v and isinstance(v[0], str) else " ".join(" ".join(t) for t in v) if isinstance(v, list) else v).split())
        print(f"  {k}: {n}")

    hyp = "".join(f"<li>{html.escape(h)}</li>" for h in TEXT["hyp"])
    measures = "".join(f"<li><strong>{html.escape(k)}</strong> - {html.escape(v)}</li>" for k, v in TEXT["measures"])
    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>e065 the water's two layers - Report</title>
<style>{CSS}</style>
</head>
<body>
<main>
<h1>e065: the water's two layers</h1>
<p class="sub">Experiment report - 2026-09-14 - a surface layer for bodies lighter than water and a bottom layer for denser ones, on e062's world c1225 at s = 1/16, 100,000 steps (foundation stage C, third step, #79)</p>

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
<thead><tr><th>Second half of the run</th><th>sea a wall (e064)</th><th>water open (e065)</th></tr></thead>
<tbody>{table}</tbody></table></div>
<ol class="verdicts">
<li><span class="verdict partly">Partly</span> 1, the water fills: {html.escape(TEXT["v1"])}</li>
<li><span class="verdict partly">Partly</span> 2, density splits: {html.escape(TEXT["v2"])}</li>
<li><span class="verdict no">No</span> 3, kinds by medium: {html.escape(TEXT["v3"])}</li>
<li><span class="verdict partly">Partly</span> 4, land and cost: {html.escape(TEXT["v4"])}</li>
</ol>

<h3>3.1 The water fills, and the world holds as many bodies as before</h3>
<div class="grid2">{"".join(charts_fill)}</div>
<p>{html.escape(TEXT["r1"])}</p>

<h3>3.2 Density splits at the density of water</h3>
<div class="grid2">{"".join(charts_density)}</div>
<p>{html.escape(TEXT["r2"])}</p>
{gal}

<h3>3.3 Ways of living span the media, and kills follow density</h3>
<div class="grid2">{"".join(charts_ways)}</div>
<p>{html.escape(TEXT["r3"])}</p>

<h3>3.4 The jam eases, and a step costs the same</h3>
<div class="grid2">{"".join(charts_cost)}</div>
<p>{html.escape(TEXT["r4"])}</p>

<h2>4. Discussion</h2>
<p>{html.escape(TEXT["d1"])}</p>
<p>{html.escape(TEXT["d2"])}</p>
<p>{html.escape(TEXT["d3"])}</p>

<h2>5. Conclusion and next step</h2>
<p>{html.escape(TEXT["conclusion"])}</p>

<h2>Appendix: data</h2>
<p>Rows of <code>results/c1225_life9_water_log.csv</code>; bodies (with their medium) in <code>_agents.csv</code> every 10,000 steps, lineages in <code>_lineages.csv</code> and <code>_events.csv</code>, the run in one row in <code>_row.csv</code>; the world without bodies in <code>c1225_life9_alone_*</code>, the check with the water closed in <code>c1225_life9_check_*</code>; the control in <code>experiments/e064_scale/results/c1225_life9_s0.0625_*</code>. Build this report with <code>uv run python experiments/e065_layers/report.py</code>.</p>
{data_table([("sea a wall (e064)", W), ("water open (e065)", E)])}
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
