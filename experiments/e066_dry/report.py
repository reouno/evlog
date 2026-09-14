#!/usr/bin/env python3
"""Build report.html for e066 (dry air, foundation stage C, fourth step, #80).

Charts: matplotlib, exported as SVG and inlined. Diagram: hand-written SVG.
Run from the repo root: uv run python experiments/e066_dry/report.py
(`--summary` prints the numbers only; `--picks` prints the bodies of the largest lineages.)
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
from matplotlib.patches import Patch
from matplotlib.ticker import MaxNLocator

matplotlib.use("svg")

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "experiments", "e060_census"))
import census  # noqa: E402  (e060's census of ways of living)

SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4"]  # fixed slot order
MEDIA = ["land", "surface", "bottom"]
MEDIUM_COLOR = {"land": SERIES[3], "surface": SERIES[2], "bottom": SERIES[4]}
KIND_COLOR = {1: SERIES[0], 2: SERIES[1], 3: SERIES[3], 4: SERIES[2]}  # hard, muscle, sensor, gut: the viewer's
RUNS = [  # (name, prefix, colour)
    ("e065, no dry air", os.path.join(ROOT, "experiments", "e065_layers", "results", "c1225_life9_water"), SERIES[0]),
    ("dry 0.001", os.path.join(HERE, "results", "c1225_life9_dry0.001"), SERIES[1]),
    ("dry 0.004", os.path.join(HERE, "results", "c1225_life9_dry0.004"), SERIES[4]),
]
CONFINED = 0.9  # a lineage lives in one medium when this share of its grown bodies stands there
DRY_FEW, WET_MOST = 0.1, 0.5  # hypothesis 4: a land body in water under a tenth of its turns, or over half

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

def rows(path):
    with open(path) as f:
        return list(csv.DictReader(f))


def columns(path):
    r = rows(path)
    return {k: [float(x[k]) for x in r] for k in r[0]}


def medium(r):
    return MEDIA[int(r["medium"])]


def open_soft(r):
    """Faces of soft blocks with no block of the body beside them (e066's `open_faces`), from the cells."""
    if "open_soft" in r:
        return int(r["open_soft"])
    s, g = int(r["side"]), [int(c) for c in r["cells"]]
    n = 0
    for i, k in enumerate(g):
        if k in (0, 1):
            continue
        y, x = divmod(i, s)
        for yy, xx in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)):
            n += not (0 <= yy < s and 0 <= xx < s) or g[yy * s + xx] == 0
    return n


def with_medium(r):
    w = census.way(r)
    return w and w + (medium(r),)


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


def load(name, pre, color):
    d = {"name": name, "color": color, "log": columns(pre + "_log.csv"), "row": {k: float(v) for k, v in rows(pre + "_row.csv")[0].items()}}
    d["agents"] = census.read(pre + "_agents.csv")
    d["lineages"] = rows(pre + "_lineages.csv")
    L = d["log"]
    last = L["step"][-1]
    late = [i for i, x in enumerate(L["step"]) if 2 * x > last]
    d["mean"] = lambda k: st.mean(L[k][i] for i in late) if k in L else float("nan")
    total = lambda k: sum(L[k][i] for i in late) if k in L else 0.0
    d["total"] = total
    deaths = sum(total(k) for k in ("deaths_hunger", "deaths_broken", "deaths_wear", "deaths_thirst"))
    d["thirst_share"] = total("deaths_thirst") / deaths
    eat = total("plant_intake") + total("meat_intake")
    d["kill_share"] = (total("meat_intake") - total("scavenged")) / eat
    d["no_room"] = total("no_room") / total("children")
    d["dumps"] = list(census.late(list(d["agents"])))
    blocks = {m: Counter() for m in MEDIA}  # summed over the second half's censuses: size, hard, open
    d["ways_lineage_m"], d["ways_lineage"], d["confined"] = [], [], []
    d["far"], d["near"] = [], []  # grown land bodies: (hard share, open per block) by their turns in water
    d["density"] = defaultdict(list)
    for x in d["dumps"]:
        rs = d["agents"][x]
        g = census.grown(rs)
        for r in rs:
            m = medium(r)
            blocks[m]["n"] += 1
            blocks[m]["size"] += int(r["size"])
            blocks[m]["hard"] += int(r["hard"])
            blocks[m]["open"] += open_soft(r)
            d["density"][m].append(float(r["density"]))
        d["ways_lineage"].append(census.count(census.census_by_lineage(rs)))
        d["ways_lineage_m"].append(census.count(by_lineage_way(g, with_medium)))
        where = defaultdict(Counter)
        for r in g:
            where[r["lineage"]][medium(r)] += 1
        d["confined"].append(sum(sum(c.values()) for c in where.values() if max(c.values()) >= CONFINED * sum(c.values())) / max(len(g), 1))
        if "drank" in rs[0]:
            for r in g:
                if medium(r) == "land" and int(r["size"]) > 0:
                    wet = int(r["drank"]) / max(int(r["turns"]), 1)
                    item = (int(r["hard"]) / int(r["size"]), open_soft(r) / int(r["size"]), wet)
                    if wet < DRY_FEW:
                        d["far"].append(item)
                    elif wet > WET_MOST:
                        d["near"].append(item)
    d["blocks"] = blocks
    d["hard_by"] = {m: blocks[m]["hard"] / max(blocks[m]["size"], 1) for m in MEDIA}
    d["open_by"] = {m: blocks[m]["open"] / max(blocks[m]["size"], 1) for m in MEDIA}
    d["share_by"] = {m: d["mean"]("pop_" + m) / d["mean"]("pop") for m in MEDIA}
    return d


def span(v, fmt="{:.0%}"):
    lo, hi = min(v), max(v)
    return fmt.format(lo) if fmt.format(lo) == fmt.format(hi) else f"{fmt.format(lo)}-{fmt.format(hi)}"


def summary(runs):
    lines = [
        ("bodies (mean, lowest-highest)", lambda d: f"{d['row']['pop_mean']:,.0f} ({d['row']['pop_min']:,.0f}-{d['row']['pop_max']:,.0f})"),
        ("land / surface / bottom", lambda d: " / ".join(f"{d['share_by'][m]:.0%}" for m in MEDIA)),
        ("deaths by thirst", lambda d: f"{d['thirst_share']:.1%}"),
        ("hard share of blocks: land / surface / bottom", lambda d: " / ".join(f"{d['hard_by'][m]:.1%}" for m in MEDIA)),
        ("open soft faces per block: land / surface / bottom", lambda d: " / ".join(f"{d['open_by'][m]:.2f}" for m in MEDIA)),
        ("mean size: land / surface / bottom", lambda d: " / ".join(f"{d['blocks'][m]['size'] / max(d['blocks'][m]['n'], 1):.1f}" for m in MEDIA)),
        ("grown in lineages keeping 90% to one medium", lambda d: span(d["confined"])),
        ("ways per lineage / with the medium", lambda d: f"{span(d['ways_lineage'], '{}')} / {span(d['ways_lineage_m'], '{}')}"),
        ("density: land / surface / bottom", lambda d: " / ".join(f"{st.mean(d['density'][m]):.2f}" for m in MEDIA)),
        ("fill: land / surface / bottom", lambda d: " / ".join(f"{d['mean']('fill_' + m):.2f}" for m in MEDIA)),
        ("turns with a block in water: land / surface / bottom", lambda d: " / ".join(f"{d['mean']('drinking_' + m):.0%}" for m in MEDIA)),
        ("grown land bodies far (<10% wet) / near (>50%): n", lambda d: f"{len(d['far'])} / {len(d['near'])}"),
        ("  their hard share", lambda d: f"{st.mean(x[0] for x in d['far']):.1%} / {st.mean(x[0] for x in d['near']):.1%}" if d["far"] and d["near"] else "-"),
        ("  their open faces per block", lambda d: f"{st.mean(x[1] for x in d['far']):.2f} / {st.mean(x[1] for x in d['near']):.2f}" if d["far"] and d["near"] else "-"),
        ("kills' share of intake", lambda d: f"{d['kill_share']:.0%}"),
        ("lineages (top share)", lambda d: f"{d['mean']('lineages'):.1f} ({d['mean']('top_lineage'):.0%})"),
        ("moves blocked; no room", lambda d: f"{d['mean']('blocked'):.0%}; {d['no_room']:.0%}"),
        ("grass standing", lambda d: f"{d['mean']('grass'):,.0f}"),
        ("ms a step", lambda d: f"{d['row']['ms_step']:.2f}"),
    ]
    for name, f in lines:
        print(f"{name}: " + " | ".join(f(d) for d in runs))


# ---------- charts ----------

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


def percent(ax, digits=0):
    ax.yaxis.set_major_formatter(lambda y, _p: f"{y:.{digits}%}")


def runs_lines(runs, key, title, subtitle, ylabel, pct=False, floor0=True):
    """One line per run of a log column (or a function of the log)."""
    fig, ax = new_axes()
    for d in runs:
        L = d["log"]
        y = key(L) if callable(key) else L.get(key)
        if y is None:
            continue
        ax.plot(L["step"], y, color=d["color"], linewidth=1.6, label=d["name"])
    if floor0:
        ax.set_ylim(0, None)
    ax.yaxis.set_major_locator(MaxNLocator(4))
    if pct:
        percent(ax)
    else:
        ax.yaxis.set_major_formatter(kfmt)
    ax.set_ylabel(ylabel)
    legend_above(ax, len(runs))
    return figure(title, subtitle, to_svg(fig))


def by_medium_bars(runs, key, title, subtitle, ylabel, pct=False):
    """Grouped bars: one group per medium, one bar per run."""
    fig, ax = plt.subplots(figsize=(6.4, 2.6))
    width = 0.8 / len(runs)
    for j, d in enumerate(runs):
        vals = [d[key][m] for m in MEDIA]
        ax.bar([i - 0.4 + width * (j + 0.5) for i in range(len(MEDIA))], vals, width=width * 0.92, color=d["color"], label=d["name"])
    ax.set_xticks(range(len(MEDIA)), MEDIA)
    ax.set_ylim(0, None)
    ax.yaxis.set_major_locator(MaxNLocator(4))
    if pct:
        percent(ax)
    ax.set_ylabel(ylabel)
    legend_above(ax, len(runs))
    return figure(title, subtitle, to_svg(fig))


def mix_chart(d, title, subtitle, n=10):
    """The medium of each large lineage's grown bodies over the second half's censuses."""
    mix = defaultdict(Counter)
    for x in d["dumps"]:
        for r in census.grown(d["agents"][x]):
            mix[r["lineage"]][medium(r)] += 1
    top = sorted(mix, key=lambda lid: -sum(mix[lid].values()))[:n]
    fig, ax = plt.subplots(figsize=(6.4, 2.9))
    for j, lid in enumerate(reversed(top)):
        total, left = sum(mix[lid].values()), 0.0
        for m in MEDIA:
            share = mix[lid][m] / total
            ax.barh(j, share, left=left, color=MEDIUM_COLOR[m], height=0.72, label=m if j == 0 else None)
            left += share
    ax.set_yticks(range(len(top)), [f"{lid} ({sum(mix[lid].values()):,})" for lid in reversed(top)])
    ax.set_xlim(0, 1)
    ax.xaxis.set_major_formatter(lambda y, _p: f"{y:.0%}")
    ax.set_xlabel("share of the lineage's grown bodies", loc="right")
    ax.grid(axis="y", visible=False)
    ax.grid(axis="x", visible=True)
    legend_above(ax, 3)
    return figure(title, subtitle, to_svg(fig))


def wet_hard_chart(d, title, subtitle):
    """Grown land bodies by the share of their turns with a block in water: their mean hard share and open faces."""
    edges = [0, 0.1, 0.25, 0.5, 0.75, 1.0001]
    groups = [[] for _ in edges[:-1]]
    for x in d["dumps"]:
        for r in census.grown(d["agents"][x]):
            if medium(r) != "land" or int(r["size"]) == 0:
                continue
            wet = int(r["drank"]) / max(int(r["turns"]), 1)
            k = next(i for i in range(len(edges) - 1) if wet < edges[i + 1])
            groups[k].append((int(r["hard"]) / int(r["size"]), open_soft(r) / int(r["size"])))
    fig, ax = plt.subplots(figsize=(6.4, 2.6))
    labels = [f"{edges[i]:.0%}-{min(edges[i + 1], 1):.0%}\n({len(g):,})" for i, g in enumerate(groups)]
    ax.bar(range(len(groups)), [st.mean(h for h, _ in g) if g else 0 for g in groups], width=0.6, color=MEDIUM_COLOR["land"])
    ax.set_xticks(range(len(groups)), labels)
    ax.set_ylim(0, None)
    ax.yaxis.set_major_locator(MaxNLocator(4))
    percent(ax)
    ax.set_ylabel("hard share of blocks")
    ax.set_xlabel("turns with a block in water (grown land bodies)", loc="right")
    return figure(title, subtitle, to_svg(fig))


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
        span_ = [int(r["step"]) for r in d["lineages"] if r["lineage"] == lid]
        life = (max(span_) - min(span_) + 1000) if span_ else 0
        peak = max((int(r["size"]) for r in d["lineages"] if r["lineage"] == lid), default=0)
        u = 88 / side
        rects = "".join(f'<rect x="{(i % side) * u:.2f}" y="{(i // side) * u:.2f}" width="{u * 0.9:.2f}" height="{u * 0.9:.2f}" fill="{KIND_COLOR[int(k)]}"/>'
                        for i, k in enumerate(cells) if k != "0")
        mean = lambda k: st.mean(float(r[k]) for r in g)
        intake = sum(float(r["meat"]) + float(r["plant"]) for r in g)
        kills = sum(float(r["killed"]) for r in g) / max(intake, 1e-9)
        where = Counter(medium(r) for r in g).most_common(1)[0]
        wet = st.mean(int(r["drank"]) / max(int(r["turns"]), 1) for r in g)
        cards.append(f"""<figure class="card"><svg viewBox="-1 -1 89 89" width="120" height="120" role="img" aria-label="{html.escape(title)}"><rect x="-1" y="-1" width="89" height="89" fill="var(--cell)"/>{rects}<line x1="-1" y1="-0.5" x2="88" y2="-0.5" stroke="var(--ink2)" stroke-width="1.5" stroke-dasharray="3 2"/></svg>
<figcaption><strong>{html.escape(title)}</strong><br>lineage {lid}: {life:,} steps, {peak:,} bodies at its peak, {where[1] / len(g):.0%} {where[0]}<br>grid {side}x{side}; mass {mean("mass"):.0f}, density {mean("density"):.2f}: hard {mean("hard"):.1f}, muscle {mean("muscle"):.0f}, sensor {mean("sensor"):.1f}, gut {mean("digestive"):.0f}; open faces {st.mean(open_soft(r) for r in g):.0f}; in water {wet:.0%} of its turns; kills {kills:.0%} of its intake<br>{html.escape(what)}</figcaption></figure>""")
    return f"""<figure class="diagram"><div class="cards">{"".join(cards)}</div>
<figcaption>{caption}</figcaption></figure>"""


def print_picks(d):
    peaks = Counter()
    for r in d["lineages"]:
        peaks[r["lineage"]] = max(peaks[r["lineage"]], int(r["size"]))
    for lid, peak in peaks.most_common(20):
        x, g, side, cells = modal_body(d, lid)
        if not g:
            continue
        mean = lambda k: st.mean(float(r[k]) for r in g)
        intake = sum(float(r["meat"]) + float(r["plant"]) for r in g)
        where = Counter(medium(r) for r in g)
        print(f"lineage {lid}: peak {peak}, {len(g)} grown at {x}, {dict(where)}, side {side}, mass {mean('mass'):.0f} density {mean('density'):.2f} "
              f"hard {mean('hard'):.1f} muscle {mean('muscle'):.1f} sensor {mean('sensor'):.1f} gut {mean('digestive'):.1f} open {st.mean(open_soft(r) for r in g):.1f} "
              f"wet {st.mean(int(r['drank']) / max(int(r['turns']), 1) for r in g):.0%} fill {mean('water'):.2f} "
              f"kills {sum(float(r['killed']) for r in g) / max(intake, 1e-9):.0%} algae {sum(float(r['algae']) for r in g) / max(intake, 1e-9):.0%} "
              f"detritus {sum(float(r['detritus']) for r in g) / max(intake, 1e-9):.0%} travel {st.median(float(r['travel']) for r in g):.0f}")
        for i in range(side):
            print("    " + "".join(".HMSG"[int(k)] for k in cells[i * side:(i + 1) * side]))


def data_table(runs, every=10):
    cols = ["step", "pop", "pop_land", "pop_surface", "pop_bottom", "births", "deaths_hunger", "deaths_broken", "deaths_wear", "deaths_thirst",
            "fill_land", "drinking_land", "hard_land", "open_land", "density_land", "density_surface", "density_bottom", "blocked", "lineages", "grass", "ms_bodies"]
    out = []
    for d in runs:
        L = d["log"]
        cs = [c for c in cols if c in L]
        body = "".join("<tr>" + "".join(f"<td>{L[c][i]:g}</td>" for c in cs) + "</tr>" for i in range(every - 1, len(L["step"]), every))
        out.append(f"<details><summary>{html.escape(d['name'])}, every {every * 1000:,} steps</summary><div class='tw'><table><thead><tr>"
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


def blocks_svg(x0, y0, grid, u=26):
    """A small body: grid rows of kinds (0 empty, 1 hard, 2 muscle, 4 gut), block u px, the viewer's colours."""
    out = []
    for r, line in enumerate(grid):
        for c, k in enumerate(line):
            if k:
                out.append(f'<rect x="{x0 + c * u}" y="{y0 + r * u}" width="{u - 2}" height="{u - 2}" rx="2" fill="{KIND_COLOR[k]}" stroke="none"/>')
    return "".join(out)


def arrow(x1, y1, x2, y2):
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" marker-end="url(#arr1)"/>'


# A soft pair on dry ground (six open faces), a gut walled in by hard blocks, and a body over water.
DIAGRAM = f"""
<figure class="diagram">
<svg viewBox="0 0 760 290" role="img" aria-label="A soft body on dry ground loses water through every face open to the air; a gut walled in by hard blocks loses nothing; every block over water drinks" style="max-width:100%;height:auto;display:block">
<defs><marker id="arr1" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="currentColor"/></marker></defs>
<g fill="none" stroke="currentColor" stroke-width="1.2" font-size="12" font-family="system-ui, sans-serif">
  <rect x="10" y="20" width="235" height="200" rx="6"/>
  <text x="127" y="44" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">Dry ground: a soft body</text>
  {blocks_svg(88, 100, [[2, 4]])}
  {arrow(100, 96, 100, 70)}{arrow(126, 96, 126, 70)}{arrow(100, 128, 100, 154)}{arrow(126, 128, 126, 154)}{arrow(84, 112, 58, 112)}{arrow(142, 112, 168, 112)}
  <text x="127" y="180" text-anchor="middle" fill="currentColor" stroke="none">6 open faces, each losing</text>
  <text x="127" y="198" text-anchor="middle" fill="currentColor" stroke="none">dry × (1 − the ground's fill) a turn</text>
  <rect x="262" y="20" width="235" height="200" rx="6"/>
  <text x="379" y="44" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">Dry ground: an armored body</text>
  {blocks_svg(340, 70, [[0, 1, 0], [1, 4, 1], [0, 1, 0]])}
  <text x="379" y="180" text-anchor="middle" fill="currentColor" stroke="none">hard blocks lose nothing; the gut</text>
  <text x="379" y="198" text-anchor="middle" fill="currentColor" stroke="none">has no face open to the air</text>
  <rect x="514" y="20" width="235" height="200" rx="6" fill="var(--water)"/>
  <text x="631" y="44" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">Water: the sea or a pool</text>
  {blocks_svg(605, 100, [[2, 4]])}
  {arrow(617, 70, 617, 96)}{arrow(643, 70, 643, 96)}
  <text x="631" y="180" text-anchor="middle" fill="currentColor" stroke="none">nothing is lost; every block</text>
  <text x="631" y="198" text-anchor="middle" fill="currentColor" stroke="none">drinks 0.1 a turn</text>
  <text x="380" y="252" text-anchor="middle" fill="currentColor" stroke="none">fill = the body's water ÷ its blocks, 1 at most; a child starts at its parent's fill</text>
  <text x="380" y="272" text-anchor="middle" fill="currentColor" stroke="none">at 0 the body dies of thirst; it sees water as it sees food, and reads its own thirst</text>
</g>
</svg>
<figcaption>Figure 1. The dry air, counted in blocks of water. Blocks: hard (blue), muscle (orange), gut (green). The pilots set dry to 0.004 and 0.001: a body of e065 (25 blocks, 24 open soft faces) on the driest tenth of the land dries out in about 270 and 1,100 turns.</figcaption>
</figure>
"""


# The text of the page: kept here to count its words against the skill's budget.
TEXT = {}

# (lineage, title, what the shape does): filled from the bodies the run at dry 0.004 made (`--picks`).
GALLERY_PICKS = [
    ("1", "A solid square of gut over muscle",
     "Only its rim is open to the air; it eats algae, the bottom's litter and grass. The largest lineage, in all three media."),
    ("1384", "A ring of gut around a motor",
     "e065's ring, closed up: gut on the rim, muscle inside, 23 open faces for 32 blocks. At the surface and on the bottom."),
    ("1120", "A heavy grazer kept to land",
     "66 blocks at density 1.83, a block in water in 9% of its turns, half full of water. The one lineage that keeps to land."),
    ("1048", "A solid square of gut",
     "No muscle: it stays where it was born, on the bottom and the shore, and eats the litter that sinks."),
    ("1220", "An open frame at the surface",
     "41 open faces cost nothing in water: it stays there, a block in water in 98% of its turns."),
    ("1146", "A dense crusher on the bottom",
     "Density 1.93 with muscle behind its faces: half of what it eats is kills."),
]


def main():
    runs = [load(*r) for r in RUNS if os.path.exists(r[1] + "_row.csv")]
    if "--summary" in sys.argv:
        summary(runs)
        return
    E, D1, D4 = runs
    if "--picks" in sys.argv:
        print_picks(D4)
        return
    for d in runs:
        d["size_by"] = {m: d["blocks"][m]["size"] / max(d["blocks"][m]["n"], 1) for m in MEDIA}

    wet_turns = lambda d: f"{d['mean']('fill_land'):.2f}; {d['mean']('drinking_land'):.0%}" if d is not E else "-"
    table_rows = [
        ("Bodies (mean, lowest-highest)", lambda d: f"{d['row']['pop_mean']:,.0f} ({d['row']['pop_min']:,.0f}-{d['row']['pop_max']:,.0f})"),
        ("On land / at the surface / on the bottom", lambda d: " / ".join(f"{d['share_by'][m]:.0%}" for m in MEDIA)),
        ("Deaths by thirst", lambda d: f"{d['thirst_share']:.0%}" if d is not E else "-"),
        ("Hard share of blocks: land / surface / bottom", lambda d: " / ".join(f"{d['hard_by'][m]:.1%}" for m in MEDIA)),
        ("Open soft faces per block: land / surface / bottom", lambda d: " / ".join(f"{d['open_by'][m]:.2f}" for m in MEDIA)),
        ("Mean blocks: land / surface / bottom", lambda d: " / ".join(f"{d['size_by'][m]:.0f}" for m in MEDIA)),
        ("Land: fill; turns with a block in water", wet_turns),
        ("Grown bodies in lineages keeping 90% to one medium", lambda d: span(d["confined"])),
        ("Ways of living per lineage; with the medium", lambda d: f"{span(d['ways_lineage'], '{}')}; {span(d['ways_lineage_m'], '{}')}"),
        ("Mean density: land / surface / bottom", lambda d: " / ".join(f"{st.mean(d['density'][m]):.2f}" for m in MEDIA)),
        ("Lineages alive (top lineage's share)", lambda d: f"{d['mean']('lineages'):.1f} ({d['mean']('top_lineage'):.0%})"),
        ("Kills' share of intake", lambda d: f"{d['kill_share']:.0%}"),
        ("Moves blocked; children with no room", lambda d: f"{d['mean']('blocked'):.0%}; {d['no_room']:.0%}"),
        ("A step on one core (ms)", lambda d: f"{d['row']['ms_step']:.2f}"),
    ]
    table = "".join(f"<tr><td>{name}</td>" + "".join(f"<td>{f(d)}</td>" for d in runs) + "</tr>" for name, f in table_rows)

    share_land = lambda L: [a / b if b else 0 for a, b in zip(L["pop_land"], L["pop"])]
    thirst = lambda L: [t / max(h + b + w + t, 1) for h, b, w, t in zip(L["deaths_hunger"], L["deaths_broken"], L["deaths_wear"], L["deaths_thirst"])] if "deaths_thirst" in L else None
    charts_thirst = [
        runs_lines(runs, share_land, "The land's share of the bodies falls",
                   "Bodies whose middle stands on land, of all bodies, every 1,000 steps. A line on e065's would be a land that thirst does not reach.", "share on land", pct=True),
        runs_lines(runs[1:], thirst, "One death in five is by thirst at 0.004",
                   "Deaths by thirst, of all deaths, over each 1,000 steps. Zero would be a land where every body finds water in time.", "share of deaths", pct=True),
    ]
    charts_shape = [
        by_medium_bars(runs, "open_by", "Bodies close up in every medium",
                       "Open soft faces per block, summed over the bodies at the second half's censuses. The water loses nothing, so a lower bar there is not the loss's doing.", "open faces per block"),
        by_medium_bars(runs, "size_by", "And grow",
                       "Mean blocks of a body at the second half's censuses. A bigger body of the same shape has fewer open faces per block.", "blocks"),
    ]
    charts_kinds = [
        mix_chart(D4, "At 0.004 the large lineages still span the shore",
                  "The ten largest lineages of the second half (grown bodies in brackets), by where their grown bodies stand. One colour per bar would be kinds kept to a medium."),
        wet_hard_chart(D4, "Only the bodies far from water carry a little more armor",
                       "Grown land bodies at 0.004 by the share of their turns with a block in water (bodies in brackets): their mean share of hard blocks."),
    ]

    TEXT["tldr"] = (f"A soft block over dry ground now loses water through every face it opens to the air; hard blocks and blocks in water lose nothing. "
                    f"At the stronger rate {D4['thirst_share']:.0%} of deaths are by thirst and land holds {D4['share_by']['land']:.0%} of the bodies (e065 {E['share_by']['land']:.0%}). "
                    f"But bodies answered with shape, not armor: they filled their grids and grew, in every medium, and kinds kept to one medium did not appear. "
                    f"Not kept; next, a price on the solid body in water.")
    TEXT["question"] = ("e065's layers made no kinds kept to one medium: a lineage at the density of water lived in all three. foundation.md's second trade-off "
                        "asks for different blocks instead: a soft block facing dry air loses water, a hard one does not, and nothing is lost in water. "
                        "Written before the runs, for the stronger rate:")
    TEXT["hyp"] = ["The land's bodies change their blocks (hard 10% or more, or 0.60 open faces per block or fewer); the water's stay within 0.05.",
                   "Kinds by medium: 50% of grown bodies in lineages keeping 90% to one medium.",
                   "Thirst thins the land: its share 15-35%, 5-30% of deaths by thirst.",
                   "Grown land bodies rarely in water carry twice the hard share of those mostly in water."]
    TEXT["world"] = ("e065's world and bodies at s = 1/16, with the water's two layers. Dryness is 1 minus the ground's fill: over a year its mean spreads three "
                     "times wider over the land than the air's humidity. On land a body drinks at the sea's edge; pools are 0.25% of the land.")
    TEXT["runs"] = ("c1225 with draw d11, seed 9, 100,000 steps, one core each, at dry 0.001 and 0.004. Control: e065's run, which this code reproduces "
                    "exactly with dry 0. Every 1,000 steps we record:")
    TEXT["measures"] = [
        ("Bodies", "by medium, and deaths by thirst."),
        ("Blocks", "hard share, open soft faces per block and size, by medium."),
        ("Water", "a body's fill and its turns with a block in water."),
        ("Kinds", "lineages keeping 90% to a medium; ways of living (e060) per lineage."),
        ("The crowd", "moves blocked and children with no room."),
    ]
    TEXT["v1"] = (f"on land open faces per block fell to {D4['open_by']['land']:.2f} and hard blocks rose to {D4['hard_by']['land']:.1%}; "
                  f"the surface and bottom fell to {D4['open_by']['surface']:.2f} and {D4['open_by']['bottom']:.2f}.")
    TEXT["v2"] = f"{span(D4['confined'])} of grown bodies are in lineages keeping 90% to one medium (e065 {span(E['confined'])})."
    TEXT["v3"] = f"land holds {D4['share_by']['land']:.0%} of the bodies, and {D4['thirst_share']:.0%} of deaths are by thirst."
    far = st.mean(x[0] for x in D4["far"])
    near = st.mean(x[0] for x in D4["near"])
    TEXT["v4"] = f"bodies rarely in water carry {far:.1%} hard blocks, those mostly in water {near:.1%}: the direction, not twice."
    TEXT["r1"] = (f"Land bodies hold under half their water (fill {D4['mean']('fill_land'):.2f}) and have a block in water in {D4['mean']('drinking_land'):.0%} of their turns. "
                  "They do not crowd onto wet ground or the shore: the ground under them is drier than under e065's. They live away from the water and pay for it.")
    TEXT["r2"] = ("The loss is paid per open face, and the cheap way to have fewer is a full grid, not a shell: a 6x6 square of gut and muscle opens 24 faces "
                  "for 36 blocks, and every block still eats or moves. A hard block weighs twice a soft one and does nothing else. Filling the grid makes size "
                  "pay, by perimeter over area.")
    TEXT["r3"] = ("A solid body loses nothing in the water, so nothing stops the land's answer from spreading: the large lineages span the shore and carry it to "
                  "the surface and the bottom. One lineage keeps to land (66 blocks, density 1.83); open frames keep to the surface, where openness is free.")
    TEXT["gallery"] = "The commonest birth body of six lineages at dry 0.004, at the census where each had the most grown bodies. The dashed line is the front."
    TEXT["d1"] = ("The trade-off was meant to ask for armor, but armor is the dear way to close a face: it adds weight and takes the place of a gut or a muscle. "
                  "The bodies closed their faces with the blocks they had.")
    TEXT["d2"] = ("A trade-off priced on one side only is answered by a body good on both. In e065 each layer priced the other's answer; here only the land "
                  "pays. Kinds kept to a medium need the water to price the solid body: for example a soft face that takes from the water what the body burns, "
                  "so that a closed body starves there while an open one dries on land.")
    TEXT["d3"] = ("At 0.001 a body dries out in over a thousand turns and the land's blocks did not change; its differences at the surface, which loses nothing, "
                  "are that run's path. Not shown: other seeds and c1236, longer runs, the air's humidity as the dryness, drinking from wet ground.")
    TEXT["conclusion"] = ("Dry air is not kept as stage C's default, by the rule set before the runs: the land's blocks did not change apart from the water's. "
                          "In this world, at these rates, it thins the land and makes bodies solid and larger everywhere, with no kinds by medium. "
                          "Next, to agree in #80: a law that prices the solid body in water, run together with the dry air.")

    gal = gallery(D4, GALLERY_PICKS, TEXT["gallery"])
    count = lambda v: len((" ".join(v) if isinstance(v, list) and v and isinstance(v[0], str) else " ".join(" ".join(t) for t in v) if isinstance(v, list) else v).split())
    words = sum(count(v) for v in TEXT.values()) + sum(len(p[2].split()) for p in GALLERY_PICKS)
    print(f"TEXT: {words} words")
    for k, v in TEXT.items():
        print(f"  {k}: {count(v)}")

    hyp = "".join(f"<li>{html.escape(h)}</li>" for h in TEXT["hyp"])
    measures = "".join(f"<li><strong>{html.escape(k)}</strong> - {html.escape(v)}</li>" for k, v in TEXT["measures"])
    head = "".join(f"<th>{html.escape(d['name'])}</th>" for d in runs)
    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>e066 dry air - Report</title>
<style>{CSS}</style>
</head>
<body>
<main>
<h1>e066: dry air</h1>
<p class="sub">Experiment report - 2026-09-14 - a soft block over dry ground loses water through its open faces, on e065's world c1225 at s = 1/16, 100,000 steps at two rates (foundation stage C, fourth step, #80)</p>

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
<thead><tr><th>Second half of the run</th>{head}</tr></thead>
<tbody>{table}</tbody></table></div>
<ol class="verdicts">
<li><span class="verdict no">No</span> 1, the land's blocks alone: {html.escape(TEXT["v1"])}</li>
<li><span class="verdict no">No</span> 2, kinds by medium: {html.escape(TEXT["v2"])}</li>
<li><span class="verdict">Yes</span> 3, thirst thins the land: {html.escape(TEXT["v3"])}</li>
<li><span class="verdict partly">Partly</span> 4, two ways on land: {html.escape(TEXT["v4"])}</li>
</ol>

<h3>3.1 Thirst thins the land</h3>
<div class="grid2">{"".join(charts_thirst)}</div>
<p>{html.escape(TEXT["r1"])}</p>

<h3>3.2 Bodies close up with the blocks they have</h3>
<div class="grid2">{"".join(charts_shape)}</div>
<p>{html.escape(TEXT["r2"])}</p>
{gal}

<h3>3.3 The land's answer spreads to the water</h3>
<div class="grid2">{"".join(charts_kinds)}</div>
<p>{html.escape(TEXT["r3"])}</p>

<h2>4. Discussion</h2>
<p>{html.escape(TEXT["d1"])}</p>
<p>{html.escape(TEXT["d2"])}</p>
<p>{html.escape(TEXT["d3"])}</p>

<h2>5. Conclusion and next step</h2>
<p>{html.escape(TEXT["conclusion"])}</p>

<h2>Appendix: data</h2>
<p>Rows of <code>results/c1225_life9_dry0.004_log.csv</code> and <code>_dry0.001_log.csv</code>; bodies (with their water, turns in water and open faces) in <code>_agents.csv</code> every 10,000 steps, lineages in <code>_lineages.csv</code> and <code>_events.csv</code>, the run in one row in <code>_row.csv</code>, the dryness over the run in <code>_dryness.csv</code>; the year without bodies in <code>c1225_life9_air_*</code>, the check with <code>dry = 0</code> in <code>c1225_life9_check_*</code>; the control in <code>experiments/e065_layers/results/c1225_life9_water_*</code>. Build this report with <code>uv run python experiments/e066_dry/report.py</code>.</p>
{data_table(runs)}
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
