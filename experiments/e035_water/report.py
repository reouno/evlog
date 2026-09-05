#!/usr/bin/env python3
"""Build report.html for this experiment.

Charts: matplotlib, exported as SVG and inlined. Diagram: hand-written SVG.
Run from the repo root: uv run python experiments/e035_water/report.py
"""
import csv
import html
import statistics
import io
import json
import math
import os
import re
from collections import Counter, defaultdict

import matplotlib
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator

matplotlib.use("svg")

HERE = os.path.dirname(os.path.abspath(__file__))
E026 = os.path.join(HERE, "..", "e026_weather")
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#8a8a86", "#c9c8c0", "#7b61ff"]  # fixed slot order; slots 5 and 6 are the controls
KIND_COLOR = {1: SERIES[0], 2: SERIES[1], 3: SERIES[3], 4: SERIES[2]}
CONFIRM_STEPS = 5000
SIDE_MAX = 16

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

def base(flow, rain, water=""):
    return f"128_sigma0_r64_f{flow}_{rain}_eyes8_flesh1_w1_season2_digest0_sidegrow_store5_yolk0_breed0_winterhigh{water}_seed9"

E032 = os.path.join(HERE, "..", "e032_winter")
E034 = os.path.join(HERE, "..", "e034_stillsoil")
# The pilots on seed 9 (winter high 2, store 5, grow, rain flat): label -> (folder, run prefix, color slot). The controls are e032's
# pilot (flow 0.1, no water; its pop.csv has no soil columns) and e034's still-soil pilots.
RUNS = {
    "water 0.1, leach 0.01 (round 1: no surface)": (HERE, base("0", "flat", "_water0.1_leach0.01"), 4),
    "water 0.1, no leach, flow 0.1 (round 1)": (HERE, base("0.1", "flat", "_water0.1_leach0"), 3),
    "water 0.1, leach 0.01, depth 0.01": (HERE, base("0", "flat", "_water0.1_leach0.01_depth0.01"), 0),
    "water 0.2, leach 0.01, depth 0.01": (HERE, base("0", "flat", "_water0.2_leach0.01_depth0.01"), 2),
    "water 0.1, leach 0.01, depth 0.01, mix 0.05": (HERE, base("0", "flat", "_water0.1_leach0.01_depth0.01_mix0.05"), 1),
    "water 0.1, leach 0.01, depth 0.01, mix 0.2": (HERE, base("0", "flat", "_water0.1_leach0.01_depth0.01_mix0.2"), 7),
    "no water, flow 0.1 (e032)": (E032, base("0.1", "flat"), 5),
    "no water, flow 0.001 (e034)": (E034, base("0.001", "flat"), 6),
}
STEPS = 100_000
# The batch: the water world the pilots picked (water 0.1, leach 0.01, depth 0.01, mix 0.2, flow 0) against e032's batch (flow 0.1, no water), seeds 1-3, 300,000 steps.
BATCH = {
    "water, mix 0.2": (HERE, "128_sigma0_r64_f0_flat_eyes8_flesh1_w1_season2_digest0_sidegrow_store5_yolk0_breed0_winterhigh_water0.1_leach0.01_depth0.01_mix0.2", 0),
    "no water, flow 0.1 (e032)": (E032, "128_sigma0_r64_f0.1_flat_eyes8_flesh1_w1_season2_digest0_sidegrow_store5_yolk0_breed0_winterhigh", 5),
}
B_WATER, B_E032 = list(BATCH)
SEEDS = [1, 2, 3]
LAST_STEP = 300_000
SEASON = 20_000
BAND = ["valley", "slope", "ridge"]
LINEAGE_PALETTE = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#7b61ff", "#00a3c4", "#c94c4c", "#6aa84f", "#b8860b", "#8e44ad", "#e67e22"]


# ---------- data ----------

def load_csv(path, folder=HERE):
    """Read a CSV of numbers into {column: [floats]}."""
    with open(os.path.join(folder, path)) as f:
        rows = [r for r in csv.DictReader(f) if None not in r.values()]
    return {k: [float(r[k]) for r in rows] for k in rows[0]}


def load_rows(path, folder=HERE):
    with open(os.path.join(folder, path)) as f:
        return [r for r in csv.DictReader(f) if None not in r.values()]


def lineage_rows(run, folder=HERE):
    by = defaultdict(list)
    for r in load_rows(f"results/{run}_lineages.csv", folder):
        by[int(r["lineage"])].append(r)
    return by


def load_bodies(run, folder=HERE):
    out = {}
    with open(os.path.join(folder, f"results/{run}_bodies.jsonl")) as f:
        for line in f:
            try:
                d = json.loads(line)
            except json.JSONDecodeError:
                break
            out[d["id"]] = (int(d.get("side", 8)), d["cells"])
    return out


def read_frames(path, folder=HERE):
    with open(os.path.join(folder, path)) as f:
        for line in f:
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                return



def lineage_stats(run, folder=HERE):
    """Per lineage: first and last step seen as a group, max size."""
    first, last, size = {}, {}, defaultdict(int)
    for r in load_rows(f"results/{run}_lineages.csv", folder):
        i, t = int(r["lineage"]), int(r["step"])
        first.setdefault(i, t)
        last[i] = t
        size[i] = max(size[i], int(r["size"]))
    return first, last, size


def winners(by, first_step=250_000):
    """The top lineage at each lineages.csv step from `first_step`: the distinct winners, the longest hold in steps, the holds."""
    top = {}
    for rows in by.values():
        for row in rows:
            t = int(row["step"])
            if t < first_step:
                continue
            n = int(row["size"])
            if n > top.get(t, (0, None))[0]:
                top[t] = (n, int(row["lineage"]))
    steps = sorted(top)
    if not steps:
        return 0, 0, []
    seq = [top[t][1] for t in steps]
    holds, cur, start = [], seq[0], steps[0]
    for t, l in zip(steps, seq):
        if l != cur:
            holds.append((cur, start, t))
            cur, start = l, t
    holds.append((cur, start, steps[-1] + 1000))
    return len(set(seq)), max(b - a for _, a, b in holds), holds


def median(x):
    x = sorted(v for v in x if v == v)
    return x[len(x) // 2] if x else float("nan")


def exists(folder, run):
    """A run whose log has rows (a run still writing keeps its log empty until its buffer flushes)."""
    path = os.path.join(folder, f"results/{run}_log.csv")
    return os.path.exists(path) and os.path.getsize(path) > 200


# ---------- chart helpers ----------

def kfmt(x, _pos):
    return f"{x/1000:g}k" if abs(x) >= 1000 else f"{x:g}"


def to_svg(fig):
    buf = io.StringIO()
    fig.savefig(buf, format="svg", bbox_inches="tight", pad_inches=0.05)
    plt.close(fig)
    return buf.getvalue()


def new_axes(xlabel="step", size=(6.4, 2.6)):
    fig, ax = plt.subplots(figsize=size)
    if xlabel == "step":
        ax.xaxis.set_major_formatter(kfmt)
    ax.set_xlabel(xlabel, loc="right")
    ax.margins(x=0)
    return fig, ax


def legend_above(ax, n):
    ax.legend(loc="lower left", bbox_to_anchor=(0, 1.0), ncols=n, handlelength=1.2, borderaxespad=0, columnspacing=1.2)


def line_chart(title, subtitle, xs, series, ymin=None, ymax=None, percent=False, xlabel="step", bands=None):
    """series: list of (label, ys, slot). bands: list of (lo, hi, slot) shaded around a series."""
    fig, ax = new_axes(xlabel)
    for lo, hi, slot in bands or []:
        ax.fill_between(xs, lo, hi, color=SERIES[slot], alpha=0.15, linewidth=0)
    for label, ys, slot in series:
        ax.plot(xs, ys, color=SERIES[slot], linewidth=1.6, label=label)
    top = max((v for _, ys, _ in series for v in ys if v == v), default=1.0)
    if ymin is not None:
        ax.set_ylim(ymin, ymax if ymax is not None else top * 1.12)
    ax.yaxis.set_major_formatter((lambda y, _p: f"{y:.0%}") if percent else kfmt)
    ax.yaxis.set_major_locator(MaxNLocator(4))
    legend_above(ax, min(len(series), 4))
    return figure(title, subtitle, to_svg(fig))


def hist_chart(title, subtitle, series, bins, xlabel):
    """series: list of (label, values, weights, slot)."""
    fig, ax = new_axes(xlabel)
    ax.margins(x=0.02)
    for label, values, weights, slot in series:
        ax.hist(values, bins=bins, weights=weights, color=SERIES[slot], alpha=0.7, label=label, edgecolor="none")
    ax.yaxis.set_major_locator(MaxNLocator(4))
    ax.yaxis.set_major_formatter(kfmt)
    legend_above(ax, len(series))
    return figure(title, subtitle, to_svg(fig))


def scatter_chart(title, subtitle, series, xlabel, ylabel):
    """series: list of (label, xs, ys, sizes, slot)."""
    fig, ax = new_axes(xlabel)
    ax.margins(x=0.05)
    ax.set_ylabel(ylabel)
    for label, xs, ys, sizes, slot in series:
        ax.scatter(xs, ys, s=sizes, color=SERIES[slot], alpha=0.6, label=label, linewidths=0, rasterized=True)
    ax.yaxis.set_major_locator(MaxNLocator(4))
    legend_above(ax, len(series))
    return figure(title, subtitle, to_svg(fig))


def seeds_chart(title, subtitle, logs_by_world, key_fn, ymin=0, ymax=None, percent=False):
    """One line per seed, colored by world (the first seed carries the legend)."""
    fig, ax = new_axes()
    top = 0
    for world, (folder, run, slot) in BATCH.items():
        for k, (seed, d) in enumerate(logs_by_world.get(world, {}).items()):
            ys = [key_fn(d, i) for i in range(len(d["step"]))]
            if not ys or all(v != v for v in ys):  # a world without the measure
                continue
            top = max(top, max(ys))
            ax.plot(d["step"], ys, color=SERIES[slot], linewidth=1.2, alpha=0.85, label=world if k == 0 else None)
    ax.set_ylim(ymin, ymax if ymax is not None else top * 1.12)
    ax.yaxis.set_major_formatter((lambda y, _p: f"{y:.0%}") if percent else kfmt)
    ax.yaxis.set_major_locator(MaxNLocator(4))
    legend_above(ax, len(BATCH))
    return figure(title, subtitle, to_svg(fig))


def timeline_chart(title, subtitle, by, color_key="side", lo=4, hi=16):
    """Every lineage as a band: bodies over time, colored by the lineage's side (dark: small grid, yellow: large)."""
    fig, ax = new_axes(size=(13, 3.2))
    ax.set_ylabel("bodies in the lineage")
    cmap = matplotlib.colormaps["viridis"]
    for lid, rows in by.items():
        if max(int(r["size"]) for r in rows) < 20:
            continue
        xs = [int(r["step"]) for r in rows]
        ys = [int(r["size"]) for r in rows]
        d = median(float(r[color_key]) for r in rows)
        c = cmap((d - lo) / (hi - lo))
        ax.fill_between(xs, 0, ys, color=c, alpha=0.35, linewidth=0, rasterized=True)
        ax.plot(xs, ys, color=c, linewidth=0.9, rasterized=True)
    ax.set_ylim(0, None)
    ax.yaxis.set_major_locator(MaxNLocator(4))
    ax.yaxis.set_major_formatter(kfmt)
    sm = matplotlib.cm.ScalarMappable(cmap=cmap, norm=matplotlib.colors.Normalize(lo, hi))
    cb = fig.colorbar(sm, ax=ax, pad=0.01, fraction=0.03)
    cb.set_label("side")
    cb.outline.set_visible(False)
    cb.ax.tick_params(colors=INK)
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
        cols = [c for c in cols if c in d]
        rows = "".join(
            "<tr>" + "".join(f"<td>{d[c][i]:g}</td>" for c in cols) + "</tr>"
            for i in range(0, len(d[cols[0]]), every)
        )
        out.append(f"<details><summary>{html.escape(name)}</summary><div class='tw'><table><thead><tr>"
                   + "".join(f"<th>{c}</th>" for c in cols) + f"</tr></thead><tbody>{rows}</tbody></table></div></details>")
    return "\n".join(out)


def gallery(picks, caption):
    """picks: [(label, folder, run, lineage id, name, what the shape does[, step])]. The most common body of each lineage at its
    peak (or at the step given), on the grid it grew on (side by side cells, drawn at the same width whatever the side), front up."""
    cards = []
    cache = {}
    for label, folder, run, lid, name, what, *at in picks:
        if run not in cache:
            cache[run] = (lineage_rows(run, folder), load_bodies(run, folder), list(read_frames(f"results/{run}_long.jsonl", folder)))
        by, bodies, frames = cache[run]
        rows = by[lid]
        peak = max(rows, key=lambda r: int(r["size"])) if not at else min(rows, key=lambda r: abs(int(r["step"]) - at[0]))
        span = int(rows[-1]["step"]) - int(rows[0]["step"]) + CONFIRM_STEPS
        frame = min((fr for fr in frames if any(a[4] == lid for a in fr["agents"])), key=lambda fr: abs(fr["step"] - int(peak["step"])))
        # The most common body among the grown ones (at least three quarters of the lineage's
        # mean cells at its peak): a lineage in bloom is mostly newborns of one or two cells.
        grown = 0.75 * sum(float(peak[k]) for k in ("hard", "muscle", "sensor", "digestive"))
        ids = [a[2] for a in frame["agents"] if a[4] == lid]
        c = Counter(i for i in ids if sum(ch != "0" for ch in bodies[i][1]) >= grown) or Counter(ids)
        side, cells = bodies[c.most_common(1)[0][0]]
        u = 88 / side
        rects = "".join(f'<rect x="{(i % side) * u:.2f}" y="{(i // side) * u:.2f}" width="{u * 0.9:.2f}" height="{u * 0.9:.2f}" fill="{KIND_COLOR[int(k)]}"/>' for i, k in enumerate(cells) if k != "0")
        m, pl = float(peak["meat"]), float(peak["plant"])
        meat = m / (m + pl) if m + pl > 0 else 0
        cards.append(f"""<figure class="card"><svg viewBox="-1 -1 89 89" width="120" height="120" role="img" aria-label="{html.escape(name)}"><rect x="-1" y="-1" width="89" height="89" fill="var(--cell)"/>{rects}<line x1="-1" y1="-0.5" x2="88" y2="-0.5" stroke="var(--ink2)" stroke-width="1.5" stroke-dasharray="3 2"/></svg>
<figcaption><strong>{html.escape(name)}</strong><br>{html.escape(label)}, lineage {lid}: {span:,} steps, {int(peak["size"]):,} agents at {"step " + format(int(peak["step"]), ",") if at else "its peak"}<br>side {float(peak["side"]):.0f} (grid {side}x{side}), density {float(peak["density"]):.2f}; mass {float(peak["mass"]):.0f} on {float(peak["foot"]):.1f} cells: hard {float(peak["hard"]):.0f}, muscle {float(peak["muscle"]):.0f}, sensor {float(peak["sensor"]):.1f}, digestive {float(peak["digestive"]):.0f}; flesh {meat:.0%} of the intake<br>{html.escape(what)}</figcaption></figure>""")
    return f"""<figure class="diagram"><div class="cards">{"".join(cards)}</div>
<figcaption>{caption}</figcaption></figure>"""


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

# Hand-written mechanism diagram. Label every arrow; currentColor for lines and text;
# var(--s1) for the one element the argument hinges on. Keep 10-15px between text and lines.




DIAGRAM = """
<figure class="fig diagram">
<svg viewBox="0 0 820 360" width="100%" role="img" aria-label="Water as the carrier" font-size="12" fill="currentColor" stroke="currentColor">
  <defs><marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0,0 L10,5 L0,10 z" stroke="none" fill="currentColor"/></marker>
  <marker id="ahs" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0,0 L10,5 L0,10 z" stroke="none" fill="var(--s1)"/></marker></defs>
  <text x="20" y="30" stroke="none">the sky: 1 of water on every cell per step; 1% of a cell's water evaporates per step</text>
  <g stroke="var(--s1)" stroke-width="1.5" opacity="0.9"><line x1="70" y1="44" x2="67" y2="56"/><line x1="70" y1="66" x2="67" y2="78"/><line x1="230" y1="44" x2="227" y2="56"/><line x1="230" y1="66" x2="227" y2="78"/><line x1="390" y1="44" x2="387" y2="56"/><line x1="390" y1="66" x2="387" y2="78"/><line x1="550" y1="44" x2="547" y2="56"/><line x1="550" y1="66" x2="547" y2="78"/><line x1="710" y1="44" x2="707" y2="56"/><line x1="710" y1="66" x2="707" y2="78"/></g>
  <path d="M20,290 C120,290 180,280 240,240 C300,200 340,150 400,130 C460,110 520,160 580,190 C640,220 700,230 800,230" fill="none" stroke-width="2"/>
  <g fill="none" stroke="var(--s1)" stroke-width="1.6" marker-end="url(#ahs)"><path d="M385,122 C340,150 295,185 250,222"/><path d="M420,132 C470,150 530,178 585,196"/></g>
  <text x="140" y="118" font-size="10" fill="var(--s1)" stroke="none">water runs downhill:</text>
  <text x="140" y="132" font-size="10" fill="var(--s1)" stroke="none">0.1 of a cell's water a step, by the drop</text>
  <g fill="none" stroke-width="1.2"><rect x="600" y="92" width="196" height="50" rx="4"/></g>
  <text x="698" y="110" text-anchor="middle" font-size="10" stroke="none">a plant grows under its sun</text>
  <text x="698" y="124" text-anchor="middle" font-size="10" stroke="none">x min(1, water / 100), out of its soil</text>
  <text x="698" y="138" text-anchor="middle" font-size="10" stroke="none">the rest of the sun is dry</text>
  <g fill="none" stroke-width="1" stroke-dasharray="3 3" marker-end="url(#ah)"><path d="M330,215 C290,232 250,248 215,262"/></g>
  <text x="250" y="258" font-size="10" stroke="none">the soil goes with the water: leach x water x soil</text>
  <text x="250" y="272" font-size="10" stroke="none">(0.001 of the soil a step at leach 0.01)</text>
  <text x="580" y="256" font-size="10" stroke="none">the ridge: 53 of water per cell, half its sun;</text>
  <text x="580" y="270" font-size="10" stroke="none">its soil stays, leached slowly, mixed at half</text>
  <g fill="none" stroke-width="1.2"><rect x="30" y="240" width="150" height="34" rx="4"/></g>
  <text x="105" y="261" text-anchor="middle" font-size="10" stroke="none">the crowd eats and breathes</text>
  <g stroke-width="1.2" fill="none"><path d="M60,308 L120,308" marker-end="url(#ah)"/><path d="M120,314 L60,314" marker-end="url(#ah)"/></g>
  <text x="130" y="315" font-size="10" stroke="none">the mixing: wet neighbors exchange mix x the difference of their soil (0.2 a step in the lake)</text>
  <text x="20" y="334" font-size="10" stroke="none">the breath rains back as soil on every cell alike (unchanged)</text>
  <text x="20" y="350" font-size="10" stroke="none">the valley: the water pools level (165 per cell at water 0.1; depth 0.01, so a pool spreads), the plants grow in full</text>
</svg>
<figcaption>Figure 1. The carrier is water. The sky wets every cell alike and the water runs to the low ground, pools level and evaporates, so the ridge is dry and the valley wet; a plant uses only the share of its sun that its water allows. The soil is laid where the dead rot and the breath rains; it moves with the water that leaves a cell (the leaching, a hundredth of the old flow) and mixes between wet neighbors (the mixing). The accent marks where the water goes.</figcaption>
</figure>
"""

TEXT = {}  # filled in main(); counted at the end


def agents_at(run, step, folder=HERE):
    return [r for r in load_rows(f"results/{run}_agents.csv", folder) if int(r["step"]) == step]


def fine(run, folder, last_step, lineage_only=False):
    """Every 1,000 steps: the bodies alive (pop.csv from e031; the lineage log's sums for e030's control), lineages of 5 or more, and (pop.csv) the share on their fat, the fat and the mean age."""
    by = lineage_rows(run, folder)
    lin, lsum = Counter(), Counter()
    for rows in by.values():
        for r in rows:
            t = int(r["step"])
            if t <= last_step:
                lin[t] += 1
                lsum[t] += int(r["size"])
    path = os.path.join(folder, f"results/{run}_pop.csv")
    if os.path.exists(path) and not lineage_only:
        d = load_csv(f"results/{run}_pop.csv", folder)
        keep = [i for i, t in enumerate(d["step"]) if t <= last_step]
        out = {k: [v[i] for i in keep] for k, v in d.items()}
    else:
        steps = sorted(lsum)
        out = {"step": [float(t) for t in steps], "pop": [float(lsum[t]) for t in steps]}
    out["lineages"] = [lin[int(t)] for t in out["step"]]
    return out


def winters(f, first=0):
    """Per cycle of the season from `first`: (trough step, bodies at the trough, lineages at the trough, peak bodies)."""
    out = []
    n = int(max(f["step"])) // SEASON
    for c in range(first, n):
        idx = [i for i, t in enumerate(f["step"]) if c * SEASON < t <= (c + 1) * SEASON]
        if not idx:
            continue
        lo = min(idx, key=lambda i: f["pop"][i])
        hi = max(idx, key=lambda i: f["pop"][i])
        out.append((int(f["step"][lo]), int(f["pop"][lo]), f["lineages"][lo], int(f["pop"][hi])))
    return out


def band_share(f, b):
    return [f[f"pop{b}"][i] / f["pop"][i] if f["pop"][i] > 0 else float("nan") for i in range(len(f["step"]))]


def cross_share(f, b):
    return [f[f"cross{b}"][i] / f[f"pop{b}"][i] if f[f"pop{b}"][i] > 0 else float("nan") for i in range(len(f["step"]))]


def floor_rows(f, first=0):
    """Per winter from `first`: (trough step, bodies, lineages, valley share of the bodies, ridge bodies, share of the ridge's bodies born elsewhere, peak bodies, ridge share at the peak)."""
    out = []
    n = int(max(f["step"])) // SEASON
    for c in range(first, n):
        idx = [i for i, t in enumerate(f["step"]) if c * SEASON < t <= (c + 1) * SEASON]
        if not idx:
            continue
        lo = min(idx, key=lambda i: f["pop"][i])
        hi = max(idx, key=lambda i: f["pop"][i])
        has = "pop0" in f
        out.append(dict(step=int(f["step"][lo]), pop=int(f["pop"][lo]), lin=f["lineages"][lo],
                        valley=f["pop0"][lo] / max(f["pop"][lo], 1) if has else float("nan"),
                        ridge=int(f["pop2"][lo]) if has else 0,
                        ridge_cross=f["cross2"][lo] / max(f["pop2"][lo], 1) if has else float("nan"),
                        peak=int(f["pop"][hi]), peak_ridge=f["pop2"][hi] / max(f["pop"][hi], 1) if has else float("nan")))
    return out


def main():
    logs = {label: {k: v[:STEPS // 10_000] for k, v in load_csv(f"results/{run}_log.csv", folder).items()} for label, (folder, run, _) in RUNS.items() if exists(folder, run)}
    fines = {label: fine(run, folder, STEPS) for label, (folder, run, _) in RUNS.items() if label in logs}
    slot = {label: s for label, (_, _, s) in RUNS.items()}
    xs = max((d["step"] for d in logs.values()), key=len)

    def pad(ys, n):
        return ys + [float("nan")] * (n - len(ys))

    def series(f, labels=None, src=None):
        src = src or logs
        return [(label, pad([f(src[label], i) for i in range(len(src[label]["step"]))], len(xs)), slot[label]) for label in (labels or RUNS) if label in src]

    fx = max((d["step"] for d in fines.values()), key=len)

    def fine_series(key, labels=None):
        return [(label, pad(list(fines[label][key]), len(fx)), slot[label]) for label in (labels or RUNS) if label in fines and key in fines[label]]

    def fine_fn(fn, need="pop0", labels=None):
        return [(label, pad(fn(fines[label]), len(fx)), slot[label]) for label in (labels or RUNS) if label in fines and need in fines[label]]

    def rng(d, k, fmt="{:.2f}"):
        if k not in d:
            return "-"
        return f"{fmt.format(min(d[k]))}-{fmt.format(max(d[k]))}"

    charts_winter = [
        line_chart("Bodies every 1,000 steps", "All bodies alive (pop.csv). The floor of a dip is what lives through the winter; e032's pilot is the control.", fx, fine_series("pop"), ymin=0),
        line_chart("The valley's share of the bodies", "Bodies in the valley over all bodies, every 1,000 steps. The valley is a third of the cells; a third would mean the bodies do not prefer it.", fx, fine_fn(lambda f: band_share(f, 0)), ymin=0, ymax=1, percent=True),
    ]
    charts_soil = [
        line_chart("Soil in the valley", "Soil in the valley's cells every 1,000 steps (pop.csv from e033's code on; e032's pilot has no soil column). Flat would mean the soil stays where it started, 43,700 per band.", fx, fine_fn(lambda f: list(f["soil0"]), need="soil0"), ymin=0),
        line_chart("Soil on the ridge", "Soil in the ridge's cells every 1,000 steps. Rising means the ridge holds what the valley eats.", fx, fine_fn(lambda f: list(f["soil2"]), need="soil2"), ymin=0),
    ]

    def summary_row(label):
        d, f = logs[label], fines[label]
        alive = [i for i, p in enumerate(d["pop"]) if p > 0]
        d = {k: [v[i] for i in alive] for k, v in d.items()}
        w = floor_rows(f)
        fmt = lambda k, s: ", ".join(s.format(r[k]) for r in w)
        half = [i for i, t in enumerate(d["step"]) if t > STEPS // 2]
        mean = lambda k: sum(d[k][i] for i in half) / len(half)
        dry_s = f"{mean('dry'):.0f}" if "dry" in d else "-"
        return (f"<tr><td>{label}</td><td>{fmt('pop', '{:,}')}</td><td>{fmt('lin', '{}')}</td><td>{fmt('valley', '{:.0%}')}</td>"
                f"<td>{min(r['peak'] for r in w):,}-{max(r['peak'] for r in w):,}</td><td>{fmt('peak_ridge', '{:.0%}')}</td><td>{mean('plant_intake') / 10_000:.0f}</td><td>{mean('barren'):.0f}</td><td>{dry_s}</td><td>{mean('soil'):,.0f}</td><td>{mean('fat_stock'):,.0f}</td></tr>")

    rows = "".join(summary_row(label) for label in RUNS if label in logs)

    def band_rows(label):
        folder, run, _ = RUNS[label]
        pl = [r for r in load_rows(f"results/{run}_places.csv", folder) if int(r["step"]) >= STEPS // 2]
        band = json.load(open(os.path.join(folder, f"results/{run}_terrain.json")))["band"]
        soil = list(read_frames(f"results/{run}_soil.jsonl", folder))[-1]["soil"]
        out = ""
        for p in "012":
            rr = [r for r in pl if r["place"] == p]
            m = lambda k, s: s.format(statistics.median(float(r[k]) for r in rr))
            v = sorted((x for x, b in zip(soil, band) if b == int(p)), reverse=True)
            tot = sum(v)
            has_water = "water" in rr[0]
            out += (f"<tr><td>{label if p == '0' else ''}</td><td>{BAND[int(p)]}</td><td>{m('water', '{:.0f}') if has_water else '-'}</td><td>{m('dry', '{:.1f}') if has_water else '-'}</td><td>{tot:,.0f}</td><td>{sum(1 for x in v if x < 0.01) / len(v):.0%}</td>"
                    f"<td>{m('barren', '{:.1f}')}</td><td>{min(int(r['pop']) for r in rr):,}-{max(int(r['pop']) for r in rr):,}</td></tr>")
        return out

    brows = "".join(band_rows(label) for label in RUNS if label in logs)
    tables = data_table(["step", "pop", "births", "deaths_energy", "plant_intake", "regrowth", "rain", "air", "soil", "soil_cells", "deep", "barren", "dry", "water", "leached", "fat_stock", "biters_any_share", "side_mean", "mass_p50", "lineages"],
                        {f"{label}, seed 9": d for label, d in logs.items()}, every=1)
    # ---- the batch ----
    blogs, blin, bfine = {}, {}, {}
    for world, (folder, run, _) in BATCH.items():
        blogs[world] = {sd: {k: v[:LAST_STEP // 10_000] for k, v in load_csv(f"results/{run}_seed{sd}_log.csv", folder).items()} for sd in SEEDS if exists(folder, f"{run}_seed{sd}")}
        blin[world] = {sd: lineage_rows(f"{run}_seed{sd}", folder) for sd in SEEDS if sd in blogs[world]}
        bfine[world] = {sd: fine(f"{run}_seed{sd}", folder, LAST_STEP) for sd in blogs[world]}
    have_batch = all(blogs[w] for w in BATCH)
    bsum = {}
    for world in BATCH:
        for sd, d in blogs[world].items():
            n = len(d["step"])
            h = slice(n // 2, n)
            by, f = blin[world][sd], bfine[world][sd]
            w = floor_rows(f, first=LAST_STEP // SEASON // 2)
            nw, hold, holds = winners(by, first_step=LAST_STEP // 2)
            bsum[(world, sd)] = dict(pop=median(d["pop"][h]), trough=min(r["pop"] for r in w) if w else 0, trough_med=median(r["pop"] for r in w) if w else 0, trough_lin=median(r["lin"] for r in w) if w else 0,
                                     valley=median(r["valley"] for r in w) if w else float("nan"), peak=median(r["peak"] for r in w) if w else 0, peak_ridge=median(r["peak_ridge"] for r in w) if w else float("nan"),
                                     eaten=sum(d["plant_intake"][h]) / len(d["plant_intake"][h]) / 10_000, barren=sum(d["barren"][h]) / len(d["barren"][h]), dry=sum(d["dry"][h]) / len(d["dry"][h]) if "dry" in d else float("nan"), soil=sum(d["soil"][h]) / len(d["soil"][h]),
                                     biters=max(d["biters_any_share"][h]), p50=median(d["mass_p50"][h]), sensor=max(d["sensor_agents_share"]), winners=nw, hold=hold, last=int(d["step"][-1]), died=int(d["step"][-1]) < LAST_STEP)
    charts_batch, brows_batch = [], ""
    if have_batch:
        pc = lambda x: "-" if x != x else f"{x:.0%}"
        dr = lambda x: "-" if x != x else f"{x:.0f}"
        charts_batch = [
            seeds_chart("Bodies every 1,000 steps, three seeds", "All bodies alive, one line per seed and world. The floors are the winters.", bfine, lambda d, i: d["pop"][i], ymin=0),
            seeds_chart("Lineages alive, three seeds", "Lineages of 5 or more bodies every 1,000 steps, per seed and world.", bfine, lambda d, i: d["lineages"][i], ymin=0),
            seeds_chart("The ridge's share of the bodies", "Bodies on the ridge over all bodies, every 1,000 steps, per seed and world. The ridge is a third of the cells.", bfine, lambda d, i: d["pop2"][i] / d["pop"][i] if d["pop"][i] > 0 else float("nan"), ymin=0, ymax=0.6, percent=True),
            seeds_chart("Soil on the ridge", "Soil in the ridge's cells every 1,000 steps, per seed (this code and e033's on; e032's batch has no soil column).", bfine, lambda d, i: d["soil2"][i] if "soil2" in d else float("nan"), ymin=0),
        ]
        brows_batch = "".join((f"<tr><td>{world}, seed {sd}{' (died at ' + format(b['last'], ',') + ')' if b['died'] else ''}</td><td>{b['pop']:,.0f}</td><td>{b['trough']:,}</td><td>{b['trough_med']:,.0f}</td><td>{b['trough_lin']:.0f}</td><td>{pc(b['valley'])}</td><td>{b['peak']:,.0f}</td><td>{pc(b['peak_ridge'])}</td>"
                               f"<td>{b['eaten']:.0f}</td><td>{b['barren']:.0f}</td><td>{dr(b['dry'])}</td><td>{b['soil']:,.0f}</td><td>{b['biters']:.0%}</td><td>{b['p50']:.0f}</td><td>{b['sensor']:.0%}</td><td>{b['winners']}; {b['hold']:,}</td></tr>")
                              for (world, sd), b in bsum.items())
    TEXT.update(TEXTS)
    TEXT["gallery"] = gallery(GALLERY, GALLERY_CAPTION) if have_batch and GALLERY else ""
    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>e035 Water that flows - Report</title>
<style>{CSS}</style>
</head>
<body>
<main>
<h1>e035: Water that flows</h1>
<p class="sub">Experiment report - 2026-09-05 - the flow of the soil at 0, 0.0001 and 0.001 instead of 0.1, and the rain on the mountains under a still soil: five pilots on seed 9 in the season world against the flow-0.1 pilots of e032 and e033. No batch: the pilots settle where the soil goes.</p>

<section class="tldr">
<h2>TL;DR</h2>
<p>{TEXT["tldr"]}</p>
</section>

<h2>1. Question</h2>
<p>{TEXT["question"]}</p>
<ol>
  <li><strong>The fall does not return:</strong> with the soil still (flow 0) the world stands at e032's floors, because the bodies move with the season and lay their dead where they live.</li>
  <li><strong>The lake is the bodies' now:</strong> the soil lies where the bodies die; the valley keeps most of it, the ridge holds thousands instead of 300.</li>
  <li><strong>A tiny flow (0.001) is a still soil:</strong> the same world as flow 0.</li>
  <li><strong>The ridge's rain is the ridge's soil:</strong> under a still soil the ridge holds more soil than the valley, loses less sun for want of it, and its summer share rises over 17-20%.</li>
</ol>

<h2>2. The laws</h2>
<p>{TEXT["world"]}</p>
{DIAGRAM}
<p><strong>Runs.</strong> {TEXT["runs"]}</p>
<ul class="measures">
  <li><strong>bodies and soil per band</strong> - every 1,000 steps (pop.csv): the winter floors, the valley's share, where the soil is.</li>
  <li><strong>water, dry, barren per band</strong> - at the equinoxes (places.csv): the water per cell (100 is wet), the sun lost in a band to dryness and for want of soil, per step.</li>
  <li><strong>bare cells, richest cells</strong> - from the last soil map: the share of a band's cells with less than a step of sun's worth of soil (0.01), and the share of its soil in its richest 1% of cells.</li>
  <li><strong>eaten, soil, fat</strong> - the log's plant intake per step, the soil and the fat in the bodies over the second half; in the batch also the lineages, the eye, the biters and the top lineages.</li>
</ul>

<h2>3. Results</h2>
<div class="tw"><table>
<thead><tr><th>Seed 9, 100,000 steps (five winters)</th><th>winter floors, in order</th><th>lineages of 5+ at the floors</th><th>valley share at the floors</th><th>summer peaks</th><th>ridge share at the peaks</th><th>eaten per step</th><th>sun lost for want of soil, per step (of 164)</th><th>sun lost to dryness, per step</th><th>soil</th><th>fat in bodies</th></tr></thead>
<tbody>{rows}</tbody></table></div>
<ol class="verdicts">
{TEXT["verdicts"]}
</ol>

<h3>3.1 {TEXT["h_winter"]}</h3>
<div class="grid2">
{"".join(charts_winter)}
</div>
<p>{TEXT["p_winter"]}</p>

<h3>3.2 {TEXT["h_soil"]}</h3>
<div class="grid2">
{"".join(charts_soil)}
</div>
<div class="tw"><table>
<thead><tr><th>At the end (soil) and the second half's equinoxes (median)</th><th>band</th><th>water per cell (wet: 100)</th><th>dry (sun lost per step)</th><th>soil</th><th>bare cells</th><th>barren (sun lost per step)</th><th>bodies</th></tr></thead>
<tbody>{brows}</tbody></table></div>
<p>{TEXT["p_soil"]}</p>

<h3>3.3 {TEXT["h_batch"]}</h3>
<div class="tw"><table>
<thead><tr><th>Seeds 1-3, 300,000 steps; second half (winters 8-15)</th><th>bodies (median)</th><th>lowest floor</th><th>floor (median)</th><th>lineages of 5+ at the floors</th><th>valley share at the floors</th><th>summer peak (median)</th><th>ridge share at the peaks</th><th>eaten per step (mean)</th><th>barren</th><th>dry</th><th>soil</th><th>biters (max)</th><th>mass p50</th><th>bodies with an eye (max)</th><th>top lineages; longest hold</th></tr></thead>
<tbody>{brows_batch}</tbody></table></div>
<div class="grid2">
{"".join(charts_batch)}
</div>
<p>{TEXT["p_batch"]}</p>
{TEXT["gallery"]}

<h2>4. Discussion</h2>
{TEXT["discussion"]}

<h2>5. Conclusion and next step</h2>
<p>{TEXT["conclusion"]}</p>

<h2>Appendix: data</h2>
<p>Every log step of the pilot runs; the full data is in <code>results/*.csv</code>, <code>../e032_winter/results/</code> and <code>../e034_stillsoil/results/</code>. Build this report with <code>uv run python experiments/e035_water/report.py</code>.</p>
{tables}
</main>
</body>
</html>
"""
    out = os.path.join(HERE, "report.html")
    with open(out, "w") as f:
        f.write(page)
    words = sum(len(re.sub(r"<[^>]+>", " ", html.unescape(v)).split()) for k, v in TEXT.items() if k != "gallery")
    print(f"wrote {out} ({os.path.getsize(out)//1024} KB); TEXT {words} words")


W_RUN = "128_sigma0_r64_f0_flat_eyes8_flesh1_w1_season2_digest0_sidegrow_store5_yolk0_breed0_winterhigh_water0.1_leach0.01_depth0.01_mix0.2"
C_RUN = "128_sigma0_r64_f0.1_flat_eyes8_flesh1_w1_season2_digest0_sidegrow_store5_yolk0_breed0_winterhigh"
GALLERY = [
    ("water, seed 1", HERE, f"{W_RUN}_seed1", 1749, "the sitting gut", "A light body of gut cells on a 10-grid: it sits where the plant is and eats what falls; no muscle to speak of, nothing to break."),
    ("water, seed 1", HERE, f"{W_RUN}_seed1", 1381, "the dense mover", "A full 4x4 block at density 2: eight muscle behind seven gut cells, heavy enough to hold its cell in the crowd; half its intake is flesh from the dead."),
    ("water, seed 2", HERE, f"{W_RUN}_seed2", 1037, "the big mover with eyes", "A 15-grid body of 51 mass: fifteen muscle, nine gut, two sensors that see three cells; the largest winner since e029, in the world where the soil is everywhere."),
    ("water, seed 3", HERE, f"{W_RUN}_seed3", 3899, "the biter", "A dense 4x4 with two hard cells and a bite of 1.8: a tooth that rises at 279,000 in the seed with 4-16 lineages at the floors."),
    ("e032, seed 1", E032, f"{C_RUN}_seed1", 2807, "e032's hunter", "The control's hunter: a 11-grid body of 15 mass with a bite of 2.1 and 71% flesh in its intake, the winner of e032's seed 1 from 268,000."),
]
GALLERY_CAPTION = "The most common body of the lineage at its peak, on the grid it grew on, front up (blue hard, orange muscle, yellow sensor, aqua gut). The water world's winners are e032's kinds: a light sitting gut and a dense block that moves; the block grows large and gets eyes in seed 2."

TEXTS = {
    "tldr": ("The carrier is water now. Water rains on every cell, runs downhill, pools level and evaporates, so the ridge's plants get half their sun and the valley's all; the soil lies where it is laid, leaches with the water that leaves a cell, and mixes between wet neighbors. "
             "With all three the world stands at e032's floors (720-874 and 659-736 against 716-792 and 673-738 in two seeds of three, 70% in the third), eats 10% more, and the soil is uniform and uphill (5-8 per cell everywhere, the ridge holding the most). Without the mixing the lake does not feed a stripped cell and the world runs at 60%. Kept."),
    "question": ("e019's soil flow moved the nutrient itself; e034 showed a still soil piles where nothing eats and the crowd's valley starves. The premise: what flows is water, the soil stays where the dead lie and leaches a little, a plant needs both. "
                 "Does a world with water as the carrier stand, are wet and dry places, and which part of the old flow was the crowd living on?"),
    "world": ("e034's world with water: 1 per cell per step from the sky, 1% evaporates, the share water runs to lower neighbors by the surface's drop (depth 0.01 of height per unit), a plant grows under its sun times min(1, water/100). The soil moves only with the water (leach, in proportion) and by mixing between wet neighbors (mix of the difference, times the drier's wetness). flow 0; water 0 is e034 byte for byte."),
    "runs": ("Seed 9, 100,000 steps, in three rounds (13-20 minutes each): the water on the terrain alone (round 1: leach 0.01 and 0.03, water 0.2, and water on the old flow), the water's surface (round 2), the mixing at 0.05 and 0.2 (round 3). Then seeds 1-3 for 300,000 steps at water 0.1, leach 0.01, depth 0.01, mix 0.2 against e032's batch (45 minutes). Measures:"),
    "verdicts": ("<li><span class=\"verdict\">Yes</span> Floors 720-874 and 659-736 against e032's 716-792 and 673-738; 745-814 against 1,055-1,230 in seed 1. With the mixing; 60% without it.</li>"
                 "<li><span class=\"verdict partly\">Partly</span> The ridge gets half its sun (25 of dry sun a step in the world) and is emptied every winter as before; but its summer share rises to 29-34% (19-25%), because its soil is the most, not the least.</li>"
                 "<li><span class=\"verdict\">Yes</span> The wetness on the old flow: 80% of the floors. The leaching alone: 60%, the soil in the pits, then on the shore. The mixing: 100%. The old flow was the lake's mixing, and the crowd lived on that.</li>"
                 "<li><span class=\"verdict no\">No</span> Water 0.2 (the ridge at a third of its sun) gave floors of 377-592 rising against 394-514 without the mixing; not run with it. Dryness costs 25 a step and the uniform soil gives back 30.</li>"),
    "h_winter": "Three rounds on seed 9: the pits, the shore, the lake that shares",
    "p_winter": ("On the terrain alone the water piles in one-cell pits and the leached soil with it: the richest 1% of the valley's cells hold 81% of its soil, the world runs at 60%, and at leach 0.03 it dies. With the water's surface the pool spreads and so does the soil, but a level lake does not flow, so a cell the crowd strips is refilled by the rain alone: the valley loses 31 of its sun a step for want of soil with a median cell of 9. "
                 "The mixing refills it from its neighbors: barren falls from 77 to 9 and the floors are 626-775 (e032's pilot: 542-825)."),
    "h_soil": "The soil is uniform, and uphill",
    "p_soil": ("With the mixing no cell is bare and none holds more than 15: the valley's cells 5, the ridge's 8, and the ridge holds the most (44,000-46,000 against the valley's 25,000-27,000) because the crowd eats the valley's soil and the mixing brings it back from where nothing eats. "
               "A soil spread thin feeds more sun than a lake: a cell uses 0.01 a step whatever it holds, so e032's 14 per cell in the valley and 0.06 on the ridge is worse than 5-8 everywhere."),
    "h_batch": "The batch: e032's floors, more eaten, the ridge used in summer",
    "p_batch": ("Over the last eight winters the water world eats 73-79 a step against 63-74, losing 9-24 for want of soil (40-52) and 25 to dryness. The ridge's summer share is 29-34% against 19-25%; the valley's winter share is the same. "
                "Bodies with an eye reach 29-35% in two seeds (e032: 10-24%). The winners are e032's kinds in every seed; seed 3 ends with 4-16 lineages at the floors and a biter rising (23%). Seed 1's floor is 70% of e032's, whose control held a hunter state of 1,100 at the floor."),
    "discussion": ("<p>The premise held once the carrier was whole. Water gives the places: dry by height, wet in the pools, a plant that uses only the sun its water allows. The soil is the matter, laid where the dead rot and the breath rains, and the crowd lives on the part of the old law that was never about running downhill: the lake's mixing. Leaching alone builds pits and deltas; a lake that shares its soil builds a uniform ground, which feeds every cell's sun where the lake fed a third of them.</p>"
                   "<p>The soil is uphill now: the ridge holds the most because nothing eats there half the year, and the bodies use it in summer and leave it in winter, as in e032. The ridge is still not a place a body holds through the winter; the ground store (vision item 2) is the law for that.</p>"
                   "<p>Not shown: whether a body should need water (a reason to move, later), a drier world with the mixing, and the mixing's rate, which has no anchor beyond a lake that mixes faster than a plant grows (0.05 gave 80%). The rain of matter still falls alike; with water as the carrier, the rain on the ridge (e033) could be asked again.</p>"),
    "conclusion": ("Kept: the season world is water 0.1, leach 0.01, depth 0.01, mix 0.2, flow 0 from here. It stands at e032's floors with wet and dry places, a uniform soil, and the ridge used every summer. Next: the ground store that stands through the dark (vision item 2), and whether a body needs water."),
}


if __name__ == "__main__":
    main()
