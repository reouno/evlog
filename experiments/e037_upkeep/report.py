#!/usr/bin/env python3
"""Build report.html for this experiment.

Charts: matplotlib, exported as SVG and inlined. Diagram: hand-written SVG.
Run from the repo root: uv run python experiments/e037_upkeep/report.py
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
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#8a8a86", "#c9c8c0", "#7b61ff"]  # fixed slot order; slot 5 is the control
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

BASE = "128_sigma0_r64_f0_flat_eyes8_flesh1_w1_season2_digest0_sidegrow_store5_yolk0_breed0_winterhigh_water0.1_leach0.01_depth0.01_mix0.2"


def run(k=None, seed=9):
    return f"{BASE}{'' if k is None else f'_k{k}'}_seed{seed}"


# The pilots on seed 9 in e035's season world (water 0.1, leach 0.01, depth 0.01, mix 0.2, flow 0,
# winter high 2, store 5, grow, rain flat, no ground store): label -> (folder, run prefix, color
# slot). k 1 is today's linear upkeep, the control.
RUNS = {
    "k 1 (today)": (HERE, run(), 5),
    "k 0.85": (HERE, run(0.85), 0),
    "k 0.75": (HERE, run(0.75), 1),
    "k 0.6": (HERE, run(0.6), 3),
}
E035 = os.path.join(HERE, "..", "e035_water")
# The batch on seeds 1-3: world -> (folder, run prefix by seed, color slot). The control is e035's
# batch (the same code at k 1, 300,000 steps); k 0.6 ran 300,000 steps on the Mac and k 0.75
# 200,000 on the Ubuntu box.
BATCH = {
    "k 1 (e035's batch)": (E035, lambda seed: run(None, seed), 5),
    "k 0.75": (HERE, lambda seed: run(0.75, seed), 1),
    "k 0.6": (HERE, lambda seed: run(0.6, seed), 3),
}
SEEDS = [1, 2, 3]
STEPS = 100_000
SEASON = 20_000
CELLS = 128 * 128
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
    for label, folder, run, lid, name, what, *rest in picks:
        at = rest[:1]  # the step to draw at, if given
        pick = rest[1] if len(rest) > 1 else None  # a predicate on the cells, to draw a kind of body a varied lineage holds
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
        c = Counter(i for i in ids if sum(ch != "0" for ch in bodies[i][1]) >= grown and (pick is None or pick(bodies[i][1]))) or Counter(ids)
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
<svg viewBox="0 0 900 300" width="100%" role="img" aria-label="The cost of a body" font-size="12" fill="currentColor" stroke="currentColor">
  <g fill="none" stroke-width="1.2"><path d="M60,250 L470,250"/><path d="M60,250 L60,40"/></g>
  <text x="260" y="280" text-anchor="middle" stroke="none">living cells of a body</text>
  <text x="70" y="44" font-size="10" stroke="none">upkeep a step</text>
  <g font-size="10" stroke="none" text-anchor="middle"><text x="60" y="266">0</text><text x="160" y="266">16</text><text x="260" y="266">32</text><text x="360" y="266">48</text><text x="460" y="266">64</text></g>
  <g font-size="10" stroke="none" text-anchor="end"><text x="54" y="254">0</text><text x="54" y="214">0.032</text><text x="54" y="175">0.064</text><text x="54" y="56">0.16</text></g>
  <g fill="none" stroke-width="1" stroke-dasharray="3 3"><path d="M60,210 L470,210"/></g>
  <text x="466" y="224" text-anchor="end" font-size="10" stroke="none">the per-body 0.032, paid once whatever the size</text>
  <g fill="none" stroke-width="1.6"><polyline points="60.0,210.5 460.0,52.4"/></g>
  <text x="380" y="44" text-anchor="end" font-size="10" stroke="none">k 1 (today): 0.002 a cell</text>
  <g fill="none" stroke="var(--s1)" stroke-width="1.8"><polyline points="60.0,210.5 66.2,203.0 72.5,199.1 78.8,196.0 85.0,193.3 91.2,190.8 97.5,188.5 103.8,186.4 110.0,184.4 116.2,182.5 122.5,180.7 128.8,178.9 135.0,177.2 141.2,175.6 147.5,174.0 153.8,172.4 160.0,170.9 166.2,169.5 172.5,168.0 178.8,166.6 185.0,165.3 191.2,163.9 197.5,162.6 203.8,161.3 210.0,160.1 216.2,158.8 222.5,157.6 228.8,156.4 235.0,155.2 241.2,154.0 247.5,152.8 253.8,151.7 260.0,150.6 266.2,149.4 272.5,148.3 278.8,147.2 285.0,146.2 291.2,145.1 297.5,144.0 303.8,143.0 310.0,142.0 316.2,140.9 322.5,139.9 328.8,138.9 335.0,137.9 341.2,137.0 347.5,136.0 353.8,135.0 360.0,134.1 366.2,133.1 372.5,132.2 378.8,131.2 385.0,130.3 391.2,129.4 397.5,128.5 403.8,127.5 410.0,126.6 416.2,125.8 422.5,124.9 428.8,124.0 435.0,123.1 441.2,122.2 447.5,121.4 453.8,120.5 460.0,119.7"/></g>
  <text x="330" y="154" font-size="10" fill="var(--s1)" stroke="none">k 0.6: 0.106 for 64 cells, 34% less</text>
  <g fill="none" stroke-width="1" stroke-dasharray="2 3"><path d="M160,250 L160,171"/></g>
  <circle cx="160" cy="171" r="3.5" fill="var(--s1)" stroke="none"/>
  <text x="170" y="191" font-size="10" fill="var(--s1)" stroke="none">16 cells: 0.064 under every k</text>
  <text x="520" y="60" font-size="11" stroke="none">upkeep = 0.002 x 16 x (cells / 16)^k + 0.032</text>
  <text x="520" y="90" font-size="10" stroke="none">income: at most 0.02 a step per gut block,</text>
  <text x="520" y="103" font-size="10" stroke="none">bounded by what the cell under it holds</text>
  <text x="520" y="130" font-size="10" stroke="none">what does not move: the bite, the move cost</text>
  <text x="520" y="143" font-size="10" stroke="none">(mass x distance), the weight, the per-body 0.032</text>
  <text x="520" y="170" font-size="10" stroke="none">per cell, 8 cells: 0.0060 today, 0.0066 at k 0.6</text>
  <text x="520" y="183" font-size="10" stroke="none">per cell, 64 cells: 0.0025 today, 0.0016 at k 0.6</text>
  <text x="520" y="210" font-size="10" stroke="none">the real world: about mass^0.75; a body twice</text>
  <text x="520" y="223" font-size="10" stroke="none">as heavy spends 1.7 times as much, not twice</text>
</svg>
<figcaption>Figure 1. The cost of a body. What a body pays a step against its living cells: today's line (0.002 a cell over the per-body 0.032) and the law at k 0.6 (accent). The curve pivots on 16 cells, the size the winners have held since e016, so a typical body pays what it pays today; a smaller body pays a little more and a larger one less.</figcaption>
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


def floors(f):
    """Per season window: the trough and the peak, with the valley's share at the trough."""
    out = []
    n = int(max(f["step"])) // SEASON
    for c in range(n):
        idx = [i for i, t in enumerate(f["step"]) if c * SEASON < t <= (c + 1) * SEASON]
        if not idx:
            continue
        lo = min(idx, key=lambda i: f["pop"][i])
        hi = max(idx, key=lambda i: f["pop"][i])
        out.append(dict(step=int(f["step"][lo]), pop=int(f["pop"][lo]), lin=f["lineages"][lo],
                        valley=f["pop0"][lo] / max(f["pop"][lo], 1), peak=int(f["pop"][hi])))
    return out


def sizes_at_end(run, folder=HERE):
    """The living cells of every body at the last dump (agents.csv)."""
    rows = load_rows(f"results/{run}_agents.csv", folder)
    last = max(int(r["step"]) for r in rows)
    return [int(r["size"]) for r in rows if int(r["step"]) == last]


def main():
    logs = {label: load_csv(f"results/{run}_log.csv", folder) for label, (folder, run, _) in RUNS.items() if exists(folder, run)}
    fines = {label: fine(run, folder, STEPS) for label, (folder, run, _) in RUNS.items() if label in logs}
    sizes = {label: sizes_at_end(run, folder) for label, (folder, run, _) in RUNS.items() if label in logs}
    slot = {label: s for label, (_, _, s) in RUNS.items()}
    xs = max((d["step"] for d in logs.values()), key=len)
    fx = max((d["step"] for d in fines.values()), key=len)

    def pad(ys, n):
        return ys + [float("nan")] * (n - len(ys))

    def series(key, labels=None):
        return [(label, pad(list(logs[label][key]), len(xs)), slot[label]) for label in (labels or RUNS) if label in logs and key in logs[label]]

    def fine_fn(fn, need="pop", labels=None):
        return [(label, pad(fn(fines[label]), len(fx)), slot[label]) for label in (labels or RUNS) if label in fines and need in fines[label]]

    eaten = lambda d: [(d["plant_intake"][i] + d["meat_intake"][i]) / 10_000 for i in range(len(d["step"]))]
    blogs = {world: {seed: load_csv(f"results/{runf(seed)}_log.csv", folder) for seed in SEEDS if exists(folder, runf(seed))} for world, (folder, runf, _) in BATCH.items()}
    bfines = {world: {seed: fine(runf(seed), folder, 300_000) for seed in blogs[world]} for world, (folder, runf, _) in BATCH.items()}
    bsizes = {world: {seed: sizes_at_end(runf(seed), folder) for seed in blogs[world]} for world, (folder, runf, _) in BATCH.items()}
    charts_batch = [
        seeds_chart("The median body, seeds 1-3", "Living cells of the median body every 10,000 steps, one line per seed, colored by k. e035's batch is the control (k 1); k 0.75 ran 200,000 steps.",
                    blogs, lambda d, i: d["size_p50"][i]),
        seeds_chart("Bodies that bite, seeds 1-3", "Share of the bodies with a tooth, one line per seed. A hunter state is above 10%; the control has it in one seed of three (e035).",
                    blogs, lambda d, i: d["biters_any_share"][i], percent=True),
    ]
    charts_size = [
        line_chart("The median body", "Living cells of the median body, every 10,000 steps (log.csv). A line that rises as k falls is size paying; lines on each other mean the upkeep is not what sets size.",
                   xs, series("size_p50"), ymin=0),
        hist_chart("Sizes at the end", "Bodies by living cells at step 100,000, all bodies alive (agents.csv). A tail to the right is what the law was meant to allow.",
                   [(label, sizes[label], None, slot[label]) for label in RUNS if label in sizes], bins=range(0, 41, 2), xlabel="living cells"),
    ]
    charts_spread = [
        line_chart("The largest body", "Living cells of the largest body alive, every 10,000 steps. The ceiling a lineage reaches, whatever the median does.",
                   xs, series("size_max"), ymin=0),
        line_chart("The median mass", "Mass (weight, the sum of the blocks' densities) of the median body, every 10,000 steps. Mass can rise without size if the cells get denser (e030).",
                   xs, series("mass_p50"), ymin=0),
    ]
    charts_world = [
        line_chart("Bodies", "Bodies alive every 1,000 steps (pop.csv). The dips are the winters; the floors are what the valley carries through the dark.",
                   fx, fine_fn(lambda f: list(f["pop"])), ymin=0),
        line_chart("What the world eats, per step", "Plant and flesh digested per step (log.csv, one point per 10,000 steps). The sun is the same in every run, so this is the share of it the bodies reach.",
                   xs, [(label, pad(eaten(logs[label]), len(xs)), slot[label]) for label in RUNS if label in logs], ymin=0),
    ]
    charts_state = [
        line_chart("Bodies that bite", "Share of the bodies with a tooth (bite_any), every 10,000 steps. A hunter state is above 10%.",
                   xs, series("biters_any_share"), ymin=0, percent=True),
        line_chart("Lineages", "Lineages of five or more bodies, every 1,000 steps. One line near 1 is a world with a single winner.",
                   fx, fine_fn(lambda f: list(f["lineages"]), need="lineages"), ymin=0),
    ]

    def summary_row(label):
        d, f = logs[label], fines[label]
        w = floors(f)
        half = [i for i, t in enumerate(d["step"]) if t > STEPS // 2]
        mean = lambda k: sum(d[k][i] for i in half) / len(half) if k in d else float("nan")
        fmt = lambda k, s: ", ".join(s.format(r[k]) for r in w)
        sz = sizes[label]
        q = statistics.quantiles(sz, n=10)
        return (f"<tr><td>{label}</td><td>{fmt('pop', '{:,}')}</td><td>{min(r['valley'] for r in w):.0%}-{max(r['valley'] for r in w):.0%}</td>"
                f"<td>{min(r['peak'] for r in w):,}-{max(r['peak'] for r in w):,}</td>"
                f"<td>{mean('size_p10'):.0f} / {mean('size_p50'):.0f} / {mean('size_p90'):.0f}</td><td>{mean('size_max'):.0f}</td>"
                f"<td>{q[0]:.0f} / {statistics.median(sz):.0f} / {q[-1]:.0f} / {max(sz)}</td>"
                f"<td>{mean('mass_p50'):.1f}</td><td>{sum(eaten(d)[i] for i in half) / len(half):.0f}</td><td>{mean('biters_any_share'):.0%}</td><td>{f['lineages'][-1]}</td></tr>")

    rows = "".join(summary_row(label) for label in RUNS if label in logs)

    def batch_row(world, seed):
        d, f, sz = blogs[world][seed], bfines[world][seed], bsizes[world][seed]
        last = int(max(d["step"]))
        w = floors(f)
        half = [i for i, t in enumerate(d["step"]) if t > 100_000]
        mean = lambda k: sum(d[k][i] for i in half) / len(half)
        q = statistics.quantiles(sz, n=10)
        return (f"<tr><td>{world}, seed {seed} ({last // 1000}k)</td><td>{min(r['pop'] for r in w):,}-{max(r['pop'] for r in w):,}</td><td>{min(r['valley'] for r in w):.0%}-{max(r['valley'] for r in w):.0%}</td>"
                f"<td>{min(r['peak'] for r in w):,}-{max(r['peak'] for r in w):,}</td>"
                f"<td>{mean('size_p10'):.0f} / {mean('size_p50'):.0f} / {mean('size_p90'):.0f}</td><td>{mean('size_max'):.0f}</td>"
                f"<td>{q[0]:.0f} / {statistics.median(sz):.0f} / {q[-1]:.0f} / {max(sz)}</td>"
                f"<td>{mean('mass_p50'):.1f}</td><td>{sum(eaten(d)[i] for i in half) / len(half):.0f}</td><td>{mean('biters_any_share'):.0%}</td><td>{f['lineages'][-1]}</td></tr>")

    brows = "".join(batch_row(world, seed) for world in BATCH for seed in blogs[world])
    tables = data_table(["step", "pop", "births", "deaths_energy", "plant_intake", "meat_intake", "regrowth", "barren", "dry", "size_p10", "size_p50", "size_p90", "size_max", "mass_p10", "mass_p50", "mass_p90", "mass_max", "density_mean", "fat_stock", "biters_any_share", "trees", "lineages"],
                        {f"{label}, seed 9": d for label, d in logs.items()}, every=1)
    TEXT.update(TEXTS)
    TEXT["gallery"] = gallery(GALLERY, GALLERY_CAPTION)
    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>e037 The cost of a body - Report</title>
<style>{CSS}</style>
</head>
<body>
<main>
<h1>e037: The cost of a body</h1>
<p class="sub">Experiment report - 2026-09-09 - an upkeep that does not scale one for one with the cells of a body: four pilots on seed 9 in the season world (k 1 against 0.85, 0.75 and 0.6), then seeds 1-3 at k 0.6 and 0.75 against e035's batch. Not kept.</p>

<section class="tldr">
<h2>TL;DR</h2>
<p>{TEXT["tldr"]}</p>
</section>

<h2>1. Question</h2>
<p>{TEXT["question"]}</p>
<ol>
  <li><strong>Size spreads:</strong> the median body grows past 11-16 cells and the spread widens, more so the smaller k.</li>
  <li><strong>Fewer, bigger bodies:</strong> the floors and peaks fall with k, and what the world eats stays near 116 a step.</li>
  <li><strong>The crowd and the tooth survive:</strong> the floors stay in the valley and the biters keep their range.</li>
  <li><strong>Or size is not the upkeep's:</strong> if nothing moves at k 0.6, what keeps bodies small is elsewhere.</li>
</ol>

<h2>2. The law</h2>
<p>{TEXT["world"]}</p>
{DIAGRAM}
<p><strong>Runs.</strong> {TEXT["runs"]}</p>
<ul class="measures">
  <li><strong>size</strong> - living cells of a body: the 10th, 50th and 90th percentiles and the largest, every 10,000 steps (log.csv), and every body at the end (agents.csv).</li>
  <li><strong>mass</strong> - the weight of a body, cells times their densities; the median every 10,000 steps.</li>
  <li><strong>bodies and floors</strong> - bodies alive every 1,000 steps (pop.csv), the winter troughs and the valley's share of them.</li>
  <li><strong>eaten, biters, lineages</strong> - what the world digests per step, the share of bodies with a tooth, lineages of five or more.</li>
</ul>

<h2>3. Results</h2>
<div class="tw"><table>
<thead><tr><th>Seed 9, 100,000 steps (five winters)</th><th>winter floors, in order</th><th>valley's share at the floors</th><th>summer peaks</th><th>size p10 / p50 / p90 (second half)</th><th>largest body (second half)</th><th>size at the end: p10 / p50 / p90 / max</th><th>median mass</th><th>eaten per step</th><th>biters</th><th>lineages at the end</th></tr></thead>
<tbody>{rows}</tbody></table></div>
<ol class="verdicts">
{TEXT["verdicts"]}
</ol>

<h3>3.1 {TEXT["h_size"]}</h3>
<div class="grid2">
{"".join(charts_size)}
</div>
<p>{TEXT["p_size"]}</p>

<h3>3.2 {TEXT["h_spread"]}</h3>
<div class="grid2">
{"".join(charts_spread)}
</div>
<p>{TEXT["p_spread"]}</p>

<h3>3.3 {TEXT["h_batch"]}</h3>
<div class="tw"><table>
<thead><tr><th>Seeds 1-3 (means after step 100,000)</th><th>winter floors</th><th>valley's share at the floors</th><th>summer peaks</th><th>size p10 / p50 / p90</th><th>largest body</th><th>size at the end: p10 / p50 / p90 / max</th><th>median mass</th><th>eaten per step</th><th>biters</th><th>lineages at the end</th></tr></thead>
<tbody>{brows}</tbody></table></div>
<div class="grid2">
{"".join(charts_batch)}
</div>
<p>{TEXT["p_batch"]}</p>

<h3>3.4 {TEXT["h_world"]}</h3>
<div class="grid2">
{"".join(charts_world)}
</div>
<p>{TEXT["p_world"]}</p>

<h3>3.5 {TEXT["h_state"]}</h3>
<div class="grid2">
{"".join(charts_state)}
</div>
<p>{TEXT["p_state"]}</p>
{TEXT["gallery"]}

<h2>4. Discussion</h2>
{TEXT["discussion"]}

<h2>5. Conclusion and next step</h2>
<p>{TEXT["conclusion"]}</p>

<h2>Appendix: data</h2>
<p>Every log step of the four pilots; the full data is in <code>results/*.csv</code>. Build this report with <code>uv run python experiments/e037_upkeep/report.py</code>.</p>
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


GALLERY = [
    ("k 1 (today)", HERE, run(), 1, "the gut bar", "Ten gut cells and nothing else, mass 9: the grazer that has won since e016. It pays 0.052 a step and takes up to 0.2; it neither moves much nor resists anything."),
    ("k 1 (today)", HERE, run(), 352, "the dense mover", "Six muscle behind eight gut cells at density 2: e025's kind, 13 cells and mass 27. Heavy cells, not more of them, is how a body grows under a linear upkeep."),
    ("k 0.6", HERE, run(0.6), 128, "the grazer that stayed", "Fourteen gut cells, no tooth, 16 cells: the control's grazer at the pivot size, alive the whole run alongside the hunters below."),
    ("k 0.6", HERE, run(0.6), 261, "the armored hunter", "The lineage's mean body is 37 cells at density 0.78 with a bite of 1.6; this one is a full 8x8 of armor in front, muscle behind and a gut between. Big and light: the cheap cells go into armor and a mouth, not into weight.", 50_000, lambda cells: cells.count("1") >= 8 and cells.count("2") >= 8),
    ("k 0.6", HERE, run(0.6), 712, "the bigger hunter", "The lineage's mean is 44 cells, nineteen of them hard, a bite of 2.6; the third hunter lineage of the run, each larger than the one before. Size is now an axis the arms race runs along."),
    ("k 0.85", HERE, run(0.85), 298, "the hunter at k 0.85", "Thirty-eight cells with two hard, seventeen muscle, eighteen gut and a bite of 0.6: the same kind appears with a gentler slope, but held 18,000 steps, not the run."),
]
GALLERY_CAPTION = "The most common body of the lineage at its peak, on the grid it grew on, front up (blue hard, orange muscle, yellow sensor, aqua gut). Under today's upkeep the winners are 10-13 cells; at k 0.6 a 16-cell grazer and 37-44-cell armored hunters hold the run together."

TEXTS = {
    "tldr": ("Not kept. An upkeep that scales as (cells / 16)^k does not make size pay: on seeds 1-3 at k 0.6 the median body is 15-16 cells and the 90th percentile 21-25 after 300,000 steps, the control's numbers, with 0-1% biters. "
             "Seed 9's pilot said otherwise for 100,000 steps (median 22, a third of the bodies armored hunters of 37-44 cells): the start's transient, which seeds 1-3 lose by step 60,000. "
             "What binds size is the income: a gut block earns 0.003 a step, an eighth of its bite."),
    "question": ("Since e015 a body pays 0.002 per cell plus 0.032 per body a step; its income is 0.02 per gut block at most, bounded by the lawn under it. Every winner since e016 is 11-16 cells. "
                 "The real world's premise is missing: metabolism scales as about mass^0.75, so the cost per unit of mass falls with size and large animals exist. This experiment gives the upkeep that slope and asks whether size pays, and what the world pays for it."),
    "world": ("e035's season world with one law. The upkeep of the cells becomes 0.002 x 16 x (cells / 16)^k, over the per-body 0.032 as before; k 1 is today's law byte for byte. "
              "The curve pivots on 16 cells: a body of 8 pays 6-11% more, one of 64 pays 15-34% less, by k. Nothing else moves."),
    "runs": ("Seed 9, 100,000 steps, one thread each, four at once on the Mac, 19 minutes: k 1 (the control), 0.85, 0.75 and 0.6. "
             "Then seeds 1-3 at k 0.6 for 300,000 steps (72 minutes on the Mac) and at k 0.75 for 200,000 on the Ubuntu box, against e035's batch at k 1."),
    "verdicts": ("<li><span class=\"verdict no\">No</span> at 300,000 steps: seeds 1-3 at k 0.6 have a median of 15-16 cells and a 90th percentile of 21-25, the control's 13-16 and 16-28. Only seed 9's 100,000 steps said yes.</li>"
                 "<li><span class=\"verdict no\">No</span> the floors are the control's (496-882 against 328-921) and so is what the world eats, 119-130 a step against 106-133.</li>"
                 "<li><span class=\"verdict\">Yes</span> but empty: the world is the control's. The tooth is at 0-1% at k 0.6; the control holds a hunter state in one seed.</li>"
                 "<li><span class=\"verdict\">Yes</span> size is not the upkeep's: at k 0.6 the 32nd cell costs 0.0009 a step, under half of today's, and the 16-cell body wins 3 of 3.</li>"),
    "h_size": "On seed 9, size pays for 100,000 steps",
    "p_size": ("The pilot is the case for the law: at k 0.6 the median body is 22 cells against 9, a fifth of the bodies at the end have 40 cells or more (3% today), and three armored hunter lineages of 37-44 cells succeed each other from step 23,000 on, beside a 16-cell grazer. "
               "k 0.75 barely moves the median; k 0.85 moves it in waves."),
    "h_spread": "Big and light, while it lasts",
    "p_spread": ("The largest body is 81-121 cells in every run, so the ceiling was never the law. On seed 9 the k 0.6 bodies are made of light cells (density 1.05 against 1.43): the cheap cells buy armor and a mouth, not weight. "
                 "With the batch read, this is what the start allows, not what selection keeps."),
    "h_batch": "On seeds 1-3 the world returns to 16 cells",
    "p_batch": ("Every seed at k 0.6 opens like the pilot - median 21-26 cells, 90th percentile 46-64 in the first 40,000 steps - and is at 16 by step 60,000, where it stays (seed 3: 16 at every percentile, density 2.0, e025's dense block). "
                "k 0.75 is the control too. The pilot's hunter world is the start's transient, held longer on seed 9; whether a seed can keep it is open."),
    "h_world": "The world's bill is the transient's",
    "p_world": ("On seed 9 the peaks halve and births fall from 11.2 to 3.5 a step while the bodies are big, and the world eats 16% less: it eats its dead (e024) and the dead are fewer. "
                "On seeds 1-3 after step 100,000 none of this remains."),
    "h_state": "Where the ceiling is: the lawn, not the bill",
    "p_state": ("A gut block earns 0.0024-0.0036 a step in every run, an eighth of its bite, and less the wider the body stands (0.0023 at a footprint of 4.6 cells in seed 9's big world, 0.0036 at 2.4 in the control): a body strips the lawn under itself, and more gut over the same lawn shares the same regrowth. "
                "The marginal cell's cost was halved; its income is what the cell under it regrows, not 0.02."),
    "discussion": ("<p>The law did what it says: on seed 9 a 40-cell body pays a fifth less and a world of armored hunters and grazers holds for 100,000 steps. The batch says that is the world every seed passes through at the start, when the lawn is whole and a wide body earns over every cell it covers, and leaves once the crowd has grazed the world down to 0.003 a step per gut block. "
                   "From then on the 16-cell body wins under a curve that favors a bigger one by 15-34%.</p>"
                   "<p>So the ceiling on size is the income: intake is regrowth under the footprint, and regrowth per cell is the sun's and the soil's, so a body cannot earn more by being wider once the world is grazed. "
                   "The real world's large animals eat what small ones cannot (tall trees, tough grass, large prey): the premise still missing is a food a big body reaches and a small one does not.</p>"
                   "<p>Not shown: whether seed 9's hunter world outlasts 100,000 steps (seeds 1-3 lost theirs by 60,000), and what the weight law costs a big body. The compute of a big-bodied world is per cell: the batch ran 40% slower per step while the bodies were large.</p>"),
    "conclusion": ("Not kept: k stays an argument, 1 by default, and the season world is e035's. Size does not pay under a sub-linear upkeep because the limit is the income, a gut block's 0.003 a step from a grazed lawn, not the bill. "
                   "Next: a food only a big body reaches - the canopy's trees (e021) are the candidate already in the world - then #37 (a body that needs water) and #38 (the rain on the ridge)."),
}


if __name__ == "__main__":
    if len(os.sys.argv) > 1 and os.sys.argv[1] == "lineages":
        for label, (folder, run, _) in RUNS.items():
            if not exists(folder, run):
                continue
            print(label)
            by = lineage_rows(run, folder)
            top = sorted(by, key=lambda lid: -sum(int(r["size"]) for r in by[lid]))[:5]
            for lid in top:
                rows = by[lid]
                peak = max(rows, key=lambda r: int(r["size"]))
                cells = sum(float(peak[k]) for k in ("hard", "muscle", "sensor", "digestive"))
                print(f"  lineage {lid}: {sum(int(r['size']) for r in rows):,} bodies-samples, {int(rows[0]['step']):,}-{int(rows[-1]['step']):,}, peak {peak['size']} at {int(peak['step']):,}; cells {cells:.0f} mass {float(peak['mass']):.0f} hard {float(peak['hard']):.0f} muscle {float(peak['muscle']):.0f} sensor {float(peak['sensor']):.1f} gut {float(peak['digestive']):.0f} side {float(peak['side']):.0f} density {float(peak['density']):.2f} bite {float(peak['bite_any']):.2f} meat {float(peak['meat']):.2f}")
    else:
        main()
