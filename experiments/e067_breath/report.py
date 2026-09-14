#!/usr/bin/env python3
"""Build report.html for e067 (breath in water, foundation stage C, fifth step, #81).

Charts: matplotlib, exported as SVG and inlined. Diagram: hand-written SVG.
Run from the repo root: uv run python experiments/e067_breath/report.py
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
from matplotlib.lines import Line2D
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
    ("e066, no breath", os.path.join(ROOT, "experiments", "e066_dry", "results", "c1225_life9_dry0.004"), SERIES[0]),
    ("breath 0.003", os.path.join(HERE, "results", "c1225_life9_breath0.003"), SERIES[1]),
    ("breath 0.01", os.path.join(HERE, "results", "c1225_life9_breath0.01"), SERIES[4]),
]
CONFINED = 0.9  # a lineage lives in one medium when this share of its grown bodies stands there
COMMON = 20  # a birth shape is counted for kinds by medium when it has this many grown bodies

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
    deaths = sum(total(k) for k in ("deaths_hunger", "deaths_broken", "deaths_wear", "deaths_thirst", "deaths_suffocation"))
    d["thirst_share"] = total("deaths_thirst") / deaths
    d["suffocation_share"] = total("deaths_suffocation") / deaths
    eat = total("plant_intake") + total("meat_intake")
    d["kill_share"] = (total("meat_intake") - total("scavenged")) / eat
    d["no_room"] = total("no_room") / total("children")
    d["dumps"] = list(census.late(list(d["agents"])))
    blocks = {m: Counter() for m in MEDIA}  # summed over the second half's censuses: size, hard, open
    d["ways_lineage_m"], d["ways_lineage"], d["confined"] = [], [], []
    d["mix"] = defaultdict(Counter)  # each lineage's grown bodies by medium, over the second half's censuses
    d["density"] = defaultdict(list)
    shapes, opened = defaultdict(Counter), defaultdict(list)  # grown bodies by birth shape and medium; open >= 1 per block
    for x in d["dumps"]:
        rs = d["agents"][x]
        g = census.grown(rs)
        for r in g:
            shapes[(r["side"], r["cells"])][medium(r)] += 1
            if int(r["size"]) > 0:
                opened[medium(r)].append(open_soft(r) >= int(r["size"]))
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
        for lid, c in where.items():
            d["mix"][lid].update(c)
    d["blocks"] = blocks
    common = [c for c in shapes.values() if sum(c.values()) >= COMMON]
    n_common = sum(sum(c.values()) for c in common)
    d["shape_confined"] = sum(sum(c.values()) for c in common if max(c.values()) >= CONFINED * sum(c.values())) / max(n_common, 1)
    d["common_share"] = n_common / max(sum(sum(c.values()) for c in shapes.values()), 1)
    d["confined_mean"] = st.mean(d["confined"])
    d["open_grown"] = {m: sum(opened[m]) / max(len(opened[m]), 1) for m in MEDIA}
    d["hard_by"] = {m: blocks[m]["hard"] / max(blocks[m]["size"], 1) for m in MEDIA}
    d["open_by"] = {m: blocks[m]["open"] / max(blocks[m]["size"], 1) for m in MEDIA}
    d["gap"] = {m: d["open_by"][m] - d["open_by"]["land"] for m in MEDIA[1:]}
    d["share_by"] = {m: d["mean"]("pop_" + m) / d["mean"]("pop") for m in MEDIA}
    top = max(d["mix"], key=lambda lid: sum(d["mix"][lid].values()))
    n = sum(d["mix"][top].values())
    where, most = d["mix"][top].most_common(1)[0]
    d["top"] = {"lineage": top, "grown": n, "medium": where, "share": most / n, "of_grown": n / sum(sum(c.values()) for c in d["mix"].values())}
    return d


def span(v, fmt="{:.0%}"):
    lo, hi = min(v), max(v)
    return fmt.format(lo) if fmt.format(lo) == fmt.format(hi) else f"{fmt.format(lo)}-{fmt.format(hi)}"


def summary(runs):
    lines = [
        ("bodies (mean, lowest-highest)", lambda d: f"{d['row']['pop_mean']:,.0f} ({d['row']['pop_min']:,.0f}-{d['row']['pop_max']:,.0f})"),
        ("land / surface / bottom", lambda d: " / ".join(f"{d['share_by'][m]:.0%}" for m in MEDIA)),
        ("deaths by thirst / suffocation", lambda d: f"{d['thirst_share']:.1%} / {d['suffocation_share']:.1%}"),
        ("hard share of blocks: land / surface / bottom", lambda d: " / ".join(f"{d['hard_by'][m]:.1%}" for m in MEDIA)),
        ("open soft faces per block: land / surface / bottom", lambda d: " / ".join(f"{d['open_by'][m]:.2f}" for m in MEDIA)),
        ("  surface - land / bottom - land", lambda d: f"{d['gap']['surface']:+.2f} / {d['gap']['bottom']:+.2f}"),
        ("mean size: land / surface / bottom", lambda d: " / ".join(f"{d['blocks'][m]['size'] / max(d['blocks'][m]['n'], 1):.1f}" for m in MEDIA)),
        ("grown in lineages keeping 90% to one medium", lambda d: span(d["confined"])),
        ("largest lineage: grown (share of grown), its medium's share", lambda d: f"{d['top']['lineage']}: {d['top']['grown']:,} ({d['top']['of_grown']:.0%}), {d['top']['share']:.0%} {d['top']['medium']}"),
        ("ways per lineage / with the medium", lambda d: f"{span(d['ways_lineage'], '{}')} / {span(d['ways_lineage_m'], '{}')}"),
        ("density: land / surface / bottom", lambda d: " / ".join(f"{st.mean(d['density'][m]):.2f}" for m in MEDIA)),
        ("fill: land / surface / bottom", lambda d: " / ".join(f"{d['mean']('fill_' + m):.2f}" for m in MEDIA)),
        ("breath: land / surface / bottom", lambda d: " / ".join(f"{d['mean']('breath_' + m):.2f}" for m in MEDIA)),
        ("turns with a block in water: land / surface / bottom", lambda d: " / ".join(f"{d['mean']('drinking_' + m):.0%}" for m in MEDIA)),
        ("turns with a block over land: land / surface / bottom", lambda d: " / ".join(f"{d['mean']('inhaling_' + m):.0%}" for m in MEDIA)),
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


def kinds_chart(runs, title, subtitle):
    """Grown bodies kept to one medium, counted by lineage and by common birth shape."""
    groups = [("lineages", "confined_mean"), ("common birth shapes", "shape_confined")]
    fig, ax = plt.subplots(figsize=(6.4, 2.6))
    width = 0.8 / len(runs)
    for j, d in enumerate(runs):
        ax.bar([i - 0.4 + width * (j + 0.5) for i in range(len(groups))], [d[k] for _, k in groups], width=width * 0.92, color=d["color"], label=d["name"])
    ax.axhline(0.3, color=INK, linewidth=1, linestyle=(0, (3, 2)))
    ax.set_xticks(range(len(groups)), [g for g, _ in groups])
    ax.set_ylim(0, 1)
    ax.yaxis.set_major_locator(MaxNLocator(4))
    percent(ax)
    ax.set_ylabel("kept to one medium")
    legend_above(ax, len(runs))
    return figure(title, subtitle, to_svg(fig))


def lineage_open_chart(d, title, subtitle, n=6):
    """Open soft faces per block of the largest lineages' grown bodies, by medium."""
    by = defaultdict(lambda: defaultdict(list))
    for x in d["dumps"]:
        for r in census.grown(d["agents"][x]):
            if int(r["size"]) > 0:
                by[r["lineage"]][medium(r)].append(open_soft(r) / int(r["size"]))
    top = sorted(by, key=lambda lid: -sum(len(v) for v in by[lid].values()))[:n]
    fig, ax = plt.subplots(figsize=(6.4, 2.6))
    width = 0.8 / len(MEDIA)
    for j, m in enumerate(MEDIA):
        xs = [i - 0.4 + width * (j + 0.5) for i in range(len(top))]
        ax.bar(xs, [st.mean(by[lid][m]) if by[lid][m] else 0 for lid in top], width=width * 0.92, color=MEDIUM_COLOR[m], label=m)
    ax.set_xticks(range(len(top)), top)
    ax.set_xlabel("lineage, largest first", loc="right")
    ax.set_ylim(0, None)
    ax.yaxis.set_major_locator(MaxNLocator(4))
    ax.set_ylabel("open faces per block")
    legend_above(ax, 3)
    return figure(title, subtitle, to_svg(fig))


def deaths_chart(runs, title, subtitle):
    """Deaths by thirst (solid) and by suffocation (dashed), of all deaths over each 1,000 steps."""
    fig, ax = new_axes()
    dashed = (0, (3, 2))
    for d in runs:
        L = d["log"]
        causes = [k for k in ("deaths_hunger", "deaths_broken", "deaths_wear", "deaths_thirst", "deaths_suffocation") if k in L]
        total = [max(sum(L[k][i] for k in causes), 1) for i in range(len(L["step"]))]
        ax.plot(L["step"], [t / n for t, n in zip(L["deaths_thirst"], total)], color=d["color"], linewidth=1.6)
        if "deaths_suffocation" in L:
            ax.plot(L["step"], [s / n for s, n in zip(L["deaths_suffocation"], total)], color=d["color"], linewidth=1.6, linestyle=dashed)
    ax.set_ylim(0, None)
    ax.yaxis.set_major_locator(MaxNLocator(4))
    percent(ax)
    ax.set_ylabel("share of deaths")
    handles = [Line2D([], [], color=d["color"], linewidth=1.6, label=d["name"]) for d in runs]
    handles.append(Line2D([], [], color=INK, linewidth=1.6, linestyle=dashed, label="suffocation"))
    ax.legend(handles=handles, loc="lower left", bbox_to_anchor=(0, 1.0), ncols=4, handlelength=1.6, borderaxespad=0, columnspacing=1.2)
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
    cols = ["step", "pop", "pop_land", "pop_surface", "pop_bottom", "births", "deaths_hunger", "deaths_broken", "deaths_wear", "deaths_thirst", "deaths_suffocation",
            "fill_land", "breath_surface", "breath_bottom", "open_land", "open_surface", "open_bottom", "hard_land", "blocked", "lineages", "grass", "ms_bodies"]
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


# A solid body in the water (short of breath), an open body in the water (it refills), and a body on land.
SOLID = [[4, 4, 4, 4, 4], [4, 2, 2, 2, 4], [4, 2, 2, 2, 4], [4, 2, 2, 2, 4], [4, 4, 4, 4, 4]]
DIAGRAM = f"""
<figure class="diagram">
<svg viewBox="0 0 760 305" role="img" aria-label="In the water every block uses breath and every open face of a soft block gives it back, so a solid body is short and an open one refills; on land every block breathes" style="max-width:100%;height:auto;display:block">
<defs><marker id="arr1" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="currentColor"/></marker></defs>
<g fill="none" stroke="currentColor" stroke-width="1.2" font-size="12" font-family="system-ui, sans-serif">
  <rect x="10" y="20" width="235" height="220" rx="6" fill="var(--water)"/>
  <text x="127" y="44" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">Water: a solid body</text>
  {blocks_svg(82, 82, SOLID, u=18)}
  {"".join(arrow(91 + 18 * k, 58, 91 + 18 * k, 78) for k in range(5))}
  <text x="127" y="200" text-anchor="middle" fill="currentColor" stroke="none">25 blocks use breath; its 20 open</text>
  <text x="127" y="218" text-anchor="middle" fill="currentColor" stroke="none">faces give it back: 5 short a turn</text>
  <rect x="262" y="20" width="235" height="220" rx="6" fill="var(--water)"/>
  <text x="379" y="44" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">Water: an open body</text>
  {blocks_svg(353, 115, [[2, 4]])}
  {arrow(365, 83, 365, 109)}{arrow(391, 83, 391, 109)}{arrow(365, 171, 365, 145)}{arrow(391, 171, 391, 145)}{arrow(321, 127, 347, 127)}{arrow(437, 127, 411, 127)}
  <text x="379" y="200" text-anchor="middle" fill="currentColor" stroke="none">2 blocks use breath; 6 open faces</text>
  <text x="379" y="218" text-anchor="middle" fill="currentColor" stroke="none">give it back: it refills</text>
  <rect x="514" y="20" width="235" height="220" rx="6"/>
  <text x="631" y="44" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">Land: any body</text>
  {blocks_svg(605, 115, [[2, 4]])}
  {arrow(617, 83, 617, 109)}{arrow(643, 83, 643, 109)}
  <text x="631" y="200" text-anchor="middle" fill="currentColor" stroke="none">every block breathes 0.1 a turn,</text>
  <text x="631" y="218" text-anchor="middle" fill="currentColor" stroke="none">and its open faces dry it (e066)</text>
  <text x="380" y="272" text-anchor="middle" fill="currentColor" stroke="none">breath = the body's breath ÷ its blocks, 1 at most; a child starts at its parent's breath</text>
  <text x="380" y="292" text-anchor="middle" fill="currentColor" stroke="none">at 0 the body suffocates; it reads its own breath; a hard block breathes through nothing</text>
</g>
</svg>
<figcaption>Figure 1. Breath, counted in blocks. Blocks: hard (blue), muscle (orange), gut (green). Water is the sea and pools of 500 mm or more, at the surface as on the bottom. The pilots set breath to 0.01 and 0.003: a solid 6x6 body wholly in water suffocates in about 300 and 1,000 turns.</figcaption>
</figure>
"""


# The text of the page: kept here to count its words against the skill's budget.
TEXT = {}

# (lineage, title, what the shape does): filled from the bodies the run at breath 0.01 made (`--picks`).
GALLERY_PICKS = [
    ("908", "A hook of muscle and gut",
     "More open faces than blocks, so in the water it breathes more than it burns. The largest lineage, at the surface and on the bottom."),
    ("1709", "An open ring at the surface",
     "Gut and muscle around a hollow: every block has a face to the water. It eats algae."),
    ("896", "A dense frame on the bottom",
     "Density 1.64 and open inside: it breathes on the bottom, crushes with muscle behind its faces, and eats what sinks."),
    ("1640", "A solid corner at the shore",
     "Muscle over a block of gut: few open faces, so it keeps a part on land or refills there. In all three media."),
    ("887", "A dense crusher of land",
     "Muscle walls its gut in: closed against the dry air, a third of its intake is kills."),
    ("1129", "A compact square of land",
     "5x5 at density 1.98, closed on every side: it lives on land and dips into the bottom's edge."),
]


def main():
    runs = [load(*r) for r in RUNS if os.path.exists(r[1] + "_row.csv")]
    if "--summary" in sys.argv:
        summary(runs)
        return
    E, B3, B10 = runs
    if "--picks" in sys.argv:
        print_picks(B10)
        return
    for d in runs:
        d["size_by"] = {m: d["blocks"][m]["size"] / max(d["blocks"][m]["n"], 1) for m in MEDIA}

    three = lambda f: (lambda d: " / ".join(f(d, m) for m in MEDIA))
    table_rows = [
        ("Bodies (mean, lowest-highest)", lambda d: f"{d['row']['pop_mean']:,.0f} ({d['row']['pop_min']:,.0f}-{d['row']['pop_max']:,.0f})"),
        ("On land / at the surface / on the bottom", three(lambda d, m: f"{d['share_by'][m]:.0%}")),
        ("Deaths by thirst; by suffocation", lambda d: f"{d['thirst_share']:.0%}; " + (f"{d['suffocation_share']:.1%}" if d is not E else "-")),
        ("Open soft faces per block: land / surface / bottom", three(lambda d, m: f"{d['open_by'][m]:.2f}")),
        ("Grown bodies with an open face per block or more", three(lambda d, m: f"{d['open_grown'][m]:.0%}")),
        ("Mean blocks: land / surface / bottom", three(lambda d, m: f"{d['size_by'][m]:.0f}")),
        ("Hard share of blocks: land / surface / bottom", three(lambda d, m: f"{d['hard_by'][m]:.1%}")),
        ("Breath: land / surface / bottom", lambda d: " / ".join(f"{d['mean']('breath_' + m):.2f}" for m in MEDIA) if d is not E else "-"),
        ("Grown bodies in lineages keeping 90% to one medium: mean (censuses)", lambda d: f"{d['confined_mean']:.0%} ({span(d['confined'])})"),
        ("Grown bodies in common birth shapes keeping 90% to one medium", lambda d: f"{d['shape_confined']:.0%}"),
        ("Largest lineage: share of grown bodies; its commonest medium", lambda d: f"{d['top']['of_grown']:.0%}; {d['top']['share']:.0%} {d['top']['medium']}"),
        ("Ways of living per lineage; with the medium", lambda d: f"{span(d['ways_lineage'], '{}')}; {span(d['ways_lineage_m'], '{}')}"),
        ("Lineages alive (top lineage's share)", lambda d: f"{d['mean']('lineages'):.1f} ({d['mean']('top_lineage'):.0%})"),
        ("Kills' share of intake", lambda d: f"{d['kill_share']:.0%}"),
        ("A step on one core, ms (the machine 1.47x slower for e067)", lambda d: f"{d['row']['ms_step']:.2f}"),
    ]
    table = "".join(f"<tr><td>{name}</td>" + "".join(f"<td>{f(d)}</td>" for d in runs) + "</tr>" for name, f in table_rows)

    charts_shape = [
        by_medium_bars(runs, "open_by", "Open faces rise most in the water",
                       "Open soft faces per block over the bodies at the second half's censuses. One height across a run's bars would be one shape for every medium.", "open faces per block"),
        by_medium_bars(runs, "size_by", "And shrink",
                       "Mean blocks of a body at the second half's censuses. A smaller body of one shape opens more faces per block.", "blocks"),
    ]
    charts_kinds = [
        kinds_chart(runs, "Shapes keep to a medium; lineages do not",
                    "Grown bodies whose lineage, or whose birth shape (20 grown bodies or more), keeps 90% of its grown bodies to one medium. Dashed: hypothesis 2's line."),
        lineage_open_chart(B10, "Inside a lineage, the water's bodies are the open ones",
                           "The six largest lineages at breath 0.01: open faces per block of their grown bodies, by medium. Equal bars would be one form in every medium."),
        mix_chart(B10, "The large lineages still span the shore",
                  "The ten largest lineages at breath 0.01 (grown bodies in brackets), by where their grown bodies stand. One colour per bar would be kinds kept to a medium."),
    ]
    charts_deaths = [
        deaths_chart(runs, "Thirst kills more; suffocation almost none",
                     "Solid: deaths by thirst; dashed: by suffocation; of all deaths over each 1,000 steps. A dashed line near zero is a water whose bodies breathe."),
    ]

    land_open = lambda d: st.median(open_soft(r) / int(r["size"]) for x in d["dumps"] for r in census.grown(d["agents"][x]) if medium(r) == "land" and int(r["size"]) > 0)
    TEXT["tldr"] = (f"In water a block now uses breath, and each soft face open to the water gives it back; e066's dry air stays on. "
                    f"The water's bodies opened: {B10['open_by']['surface']:.2f} faces per block at the surface against {B10['open_by']['land']:.2f} on land. "
                    f"Shapes keep to a medium ({B10['shape_confined']:.0%} of bodies in common shapes), but lineages still span the shore, "
                    f"each with an open form in water and a more closed one on land. Kept at breath 0.01; next step to agree in #81.")
    TEXT["question"] = ("e066's dry air priced openness on land only, and the land's answer, a filled grid, spread to the water: lineages kept to one medium "
                        "fell to 1-11%. Here the water prices the same count the other way: a soft face open to the water breathes, so a solid body "
                        "suffocates there. Written before the runs, for breath 0.01:")
    TEXT["hyp"] = ["The media part their shapes: the surface and the bottom open 0.20 or more faces per block than the land (e066 0.10 and 0.08).",
                   "Kinds by medium: 30% of grown bodies in lineages keeping 90% to one medium (e066 1-11%).",
                   "The largest lineage keeps 90% of its grown bodies to one medium.",
                   "Breath kills in the water: 5-30% of deaths by suffocation."]
    TEXT["world"] = ("e066's world and bodies at s = 1/16, with the water's two layers and dry air at 0.004. Breath is a second fill beside the water. "
                     "Water is the sea and pools; a body at the surface breathes through the water, as one on the bottom does.")
    TEXT["runs"] = ("c1225 with draw d11, seed 9, 100,000 steps, one core each, at breath 0.003 and 0.01. Control: e066's run at dry 0.004, which this "
                    "code reproduces exactly with breath 0. We record every 1,000 steps, and every body every 10,000:")
    TEXT["measures"] = [
        ("Bodies", "by medium, and deaths by thirst and by suffocation."),
        ("Shape", "open soft faces per block, size and hard share, by medium."),
        ("Breath", "a body's breath and its turns with a block over land."),
        ("Kinds", "lineages and common birth shapes keeping 90% to a medium; ways of living (e060) per lineage."),
    ]
    TEXT["v1"] = (f"the surface and the bottom open {B10['gap']['surface']:.2f} and {B10['gap']['bottom']:.2f} faces per block more than the land "
                  f"at 0.01, {B3['gap']['surface']:.2f} and {B3['gap']['bottom']:.2f} at 0.003.")
    TEXT["v2"] = f"{B10['confined_mean']:.0%} of grown bodies at 0.01 are in lineages keeping 90% to one medium (e066 {E['confined_mean']:.0%}, e065 8-23%)."
    TEXT["v3"] = f"the largest lineage at 0.01 stands {B10['top']['share']:.0%} on the {B10['top']['medium']}, the rest at the surface and on land."
    TEXT["v4"] = f"{B10['suffocation_share']:.1%} of deaths at 0.01 are by suffocation; thirst takes {B10['thirst_share']:.0%}."
    TEXT["r1"] = (f"The water's bodies became hooks, rings and lattices of gut and muscle: {B10['open_grown']['surface']:.0%} of grown bodies at the surface "
                  f"and {B10['open_grown']['bottom']:.0%} on the bottom open a face per block or more (e066 {E['open_grown']['surface']:.0%}). They breathe "
                  f"more than they burn (breath {B10['mean']('breath_surface'):.2f}) and have a block over land in {B10['mean']('inhaling_surface'):.0%} of "
                  f"their turns: they do not breathe from the shore.")
    TEXT["r2"] = (f"By shape the media part: {B10['shape_confined']:.0%} of grown bodies in common shapes keep to one medium (e066 {E['shape_confined']:.0%}). "
                  "By lineage they do not. Inside each large lineage the water's bodies open more faces and are smaller: lineage 1640 opens 0.83 per "
                  "block on land at 38 blocks, and 1.19-1.24 in the water at 23-24. A lineage is joined by mates within 6 genes, and they meet at the shore.")
    TEXT["r3"] = (f"Suffocation took {B10['suffocation_share']:.1%} of the deaths; thirst took more than in e066 ({B10['thirst_share']:.0%} against "
                  f"{E['thirst_share']:.0%}). The lineages that span the shore now carry the water's openness onto land: grown land bodies' median open "
                  f"faces per block rose from {land_open(E):.2f} to {land_open(B10):.2f}. Each medium pulls the same lineages its way.")
    TEXT["gallery"] = "The commonest birth body of six lineages at breath 0.01, at the census where each had the most grown bodies. The dashed line is the front."
    TEXT["d1"] = ("The same count priced both ways did what one price could not: shapes now differ by medium. It did not make kinds by lineage, because "
                  "the lineage is not where the difference lives. Mates within 6 genes join the open water form and the closed land form, a few genes "
                  "turn one into the other, and bodies of both meet at the shore, where the land holds both layers.")
    TEXT["d2"] = ("The price was paid in shape, as in e066, not in deaths. An open body breathes freely in the water and only the dry land prices "
                  "openness, so the water's bodies opened as far as the shore lets them. The land's bodies, in the same lineages, came out more open, "
                  "and thirst took more.")
    TEXT["d3"] = ("Not shown: other seeds and c1236, longer runs, breath without the dry air, a floating body that breathes the air, and whether the "
                  "forms would part into lineages if the shore did not join them.")
    TEXT["conclusion"] = ("Breath is kept for stage C at 0.01, with e066's dry air at 0.004, by the rule set before the runs: the water's bodies open far "
                          "more faces than the land's. In this world it parts shapes by medium but not lineages; each large lineage holds a water form "
                          "and a land form. Next, to agree in #81: counting kinds of living inside a lineage, or section 2's next row.")

    gal = gallery(B10, GALLERY_PICKS, TEXT["gallery"])
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
<title>e067 breath in water - Report</title>
<style>{CSS}</style>
</head>
<body>
<main>
<h1>e067: breath in water</h1>
<p class="sub">Experiment report - 2026-09-14 - a block in the water uses breath and a soft face open to the water gives it back, with e066's dry air, on c1225 at s = 1/16, 100,000 steps at two rates (foundation stage C, fifth step, #81)</p>

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
<li><span class="verdict">Yes</span> 1, the media part their shapes: {html.escape(TEXT["v1"])}</li>
<li><span class="verdict no">No</span> 2, kinds by medium: {html.escape(TEXT["v2"])}</li>
<li><span class="verdict no">No</span> 3, the largest lineage leaves the shore: {html.escape(TEXT["v3"])}</li>
<li><span class="verdict no">No</span> 4, breath kills in the water: {html.escape(TEXT["v4"])}</li>
</ol>

<h3>3.1 The water's bodies open up</h3>
<div class="grid2">{"".join(charts_shape)}</div>
<p>{html.escape(TEXT["r1"])}</p>
{gal}

<h3>3.2 Shapes keep to a medium, lineages do not</h3>
<div class="grid2">{"".join(charts_kinds)}</div>
<p>{html.escape(TEXT["r2"])}</p>

<h3>3.3 Thirst pays, not suffocation</h3>
<div class="grid2">{"".join(charts_deaths)}</div>
<p>{html.escape(TEXT["r3"])}</p>

<h2>4. Discussion</h2>
<p>{html.escape(TEXT["d1"])}</p>
<p>{html.escape(TEXT["d2"])}</p>
<p>{html.escape(TEXT["d3"])}</p>

<h2>5. Conclusion and next step</h2>
<p>{html.escape(TEXT["conclusion"])}</p>

<h2>Appendix: data</h2>
<p>Rows of <code>results/c1225_life9_breath0.01_log.csv</code> and <code>_breath0.003_log.csv</code>; bodies (with their breath, turns over land, water and open faces) in <code>_agents.csv</code> every 10,000 steps, lineages in <code>_lineages.csv</code> and <code>_events.csv</code>, the run in one row in <code>_row.csv</code>, the dryness over the run in <code>_dryness.csv</code>; the check with <code>breath = 0</code> in <code>c1225_life9_check_*</code>; the control in <code>experiments/e066_dry/results/c1225_life9_dry0.004_*</code>. Build this report with <code>uv run python experiments/e067_breath/report.py</code>.</p>
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
