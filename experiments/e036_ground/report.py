#!/usr/bin/env python3
"""Build report.html for this experiment.

Charts: matplotlib, exported as SVG and inlined. Diagram: hand-written SVG.
Run from the repo root: uv run python experiments/e036_ground/report.py
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

E035 = os.path.join(HERE, "..", "e035_water")
BASE = "128_sigma0_r64_f0_flat_eyes8_flesh1_w1_season2_digest0_sidegrow_store5_yolk0_breed0_winterhigh_water0.1_leach0.01_depth0.01_mix0.2"


def run(root=None, dig=None, fell=False):
    if root is None:
        return f"{BASE}_seed9"
    return f"{BASE}_root{root}_dig{dig}{'_fell' if fell else ''}_seed9"


# The pilots on seed 9 in e035's season world (water 0.1, leach 0.01, depth 0.01, mix 0.2, flow 0,
# winter high 2, store 5, grow, rain flat): label -> (folder, run prefix, color slot). Round 1 lays
# the store where the surplus grew, round 2 where the fruit falls. The control is e035's pilot.
RUNS = {
    "round 1: root 4, dig 0.5": (HERE, run(4, 0.5), 0),
    "round 1: root 1, dig 0.5": (HERE, run(1, 0.5), 3),
    "round 1: root 4, dig 0.1": (HERE, run(4, 0.1), 2),
    "round 1: root 4, dig 1": (HERE, run(4, 1), 4),
    "round 2: root 4, dig 0.5": (HERE, run(4, 0.5, True), 1),
    "round 2: root 8, dig 0.5": (HERE, run(8, 0.5, True), 7),
    "round 2: root 4, dig 0.1": (HERE, run(4, 0.1, True), 6),
    "no store (e035)": (E035, run(), 5),
}
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
<svg viewBox="0 0 900 330" width="100%" role="img" aria-label="The ground store" font-size="12" fill="currentColor" stroke="currentColor">
  <defs><marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0,0 L10,5 L0,10 z" stroke="none" fill="currentColor"/></marker>
  <marker id="ahs" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0,0 L10,5 L0,10 z" stroke="none" fill="var(--s1)"/></marker></defs>
  <text x="20" y="26" stroke="none">the sun on a cell, out of its soil</text>
  <g fill="none" stroke-width="1.2" marker-end="url(#ah)"><path d="M120,34 L120,64"/></g>
  <g fill="none" stroke-width="1.2"><rect x="30" y="70" width="180" height="46" rx="4"/></g>
  <text x="120" y="90" text-anchor="middle" font-size="10" stroke="none">the standing plant</text>
  <text x="120" y="105" text-anchor="middle" font-size="10" stroke="none">up to the cap of 8 (50 bites)</text>
  <text x="240" y="76" font-size="10" stroke="none">the growth past the cap,</text>
  <text x="240" y="88" font-size="10" stroke="none">80 a step in summer</text>
  <g fill="none" stroke-width="1.2" marker-end="url(#ah)"><path d="M212,93 L410,93"/></g>
  <g fill="none" stroke="var(--s1)" stroke-width="1.6" marker-end="url(#ahs)"><path d="M470,110 L470,150"/></g>
  <text x="480" y="128" font-size="10" fill="var(--s1)" stroke="none">round 1: into the ground of the cell it grew on</text>
  <text x="480" y="142" font-size="10" fill="var(--s1)" stroke="none">round 2: into the ground of the cell it falls on</text>
  <g fill="none" stroke-width="1.2"><rect x="410" y="70" width="140" height="40" rx="4"/></g>
  <text x="480" y="94" text-anchor="middle" font-size="10" stroke="none">the fall (e022): the ring of 8</text>
  <g fill="none" stroke="var(--s1)" stroke-width="1.6"><rect x="330" y="152" width="300" height="44" rx="4"/></g>
  <text x="480" y="170" text-anchor="middle" font-size="10" fill="var(--s1)" stroke="none">the ground store: up to root per cell (4 or 8)</text>
  <text x="480" y="185" text-anchor="middle" font-size="10" fill="var(--s1)" stroke="none">it does not rot, is not shaded, and no bite reaches it</text>
  <g fill="none" stroke-width="1.2"><rect x="640" y="70" width="160" height="40" rx="4"/></g>
  <text x="720" y="94" text-anchor="middle" font-size="10" stroke="none">fruit lying on the ground</text>
  <g fill="none" stroke-width="1" stroke-dasharray="3 3" marker-end="url(#ah)"><path d="M552,90 L636,90"/></g>
  <text x="556" y="62" font-size="10" stroke="none">what the ground cannot hold</text>
  <g fill="none" stroke-width="1.2" marker-end="url(#ah)"><path d="M720,112 L720,236"/></g>
  <text x="730" y="180" font-size="10" stroke="none">rots into the soil, 1% a step</text>
  <g fill="none" stroke-width="1.2"><rect x="330" y="240" width="300" height="46" rx="4"/></g>
  <text x="480" y="260" text-anchor="middle" font-size="10" stroke="none">a body's gut block over the cell: a bite of 0.02 from</text>
  <text x="480" y="275" text-anchor="middle" font-size="10" stroke="none">what lies there, and dig x 0.02 out of the ground</text>
  <g fill="none" stroke="var(--s1)" stroke-width="1.6" marker-end="url(#ahs)"><path d="M480,198 L480,236"/></g>
  <text x="492" y="212" font-size="10" fill="var(--s1)" stroke="none">digging: dig 0.5 pays a body's</text>
  <text x="492" y="226" font-size="10" fill="var(--s1)" stroke="none">upkeep, dig 0.1 does not</text>
  <text x="20" y="262" font-size="10" stroke="none">a body of mass 21</text>
  <text x="20" y="276" font-size="10" stroke="none">pays 0.074 a step;</text>
  <text x="20" y="290" font-size="10" stroke="none">8 gut blocks dig</text>
  <text x="20" y="304" font-size="10" stroke="none">0.08 at dig 0.5</text>
  <g fill="none" stroke-width="1.2" marker-end="url(#ah)"><path d="M150,275 L326,268"/></g>
  <text x="20" y="322" font-size="10" stroke="none">The ridge is dark for 8,000 steps of every 20,000: nothing grows there, and only what stands in the ground can be eaten.</text>
</svg>
<figcaption>Figure 1. The ground store. Everything a cell grows past the plant's cap already left the plant before this law: it fell as fruit around the cell and rotted into the soil. The law puts it in the ground instead, up to a cap per cell, where it does not rot and no bite reaches it; a gut block digs a share of a bite out of it. The accent marks the store and the digging, the two rates the experiment is about.</figcaption>
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
    """Per season window: the trough and the peak, with the ridge's bodies and store at each."""
    out = []
    n = int(max(f["step"])) // SEASON
    for c in range(n):
        idx = [i for i, t in enumerate(f["step"]) if c * SEASON < t <= (c + 1) * SEASON]
        if not idx:
            continue
        lo = min(idx, key=lambda i: f["pop"][i])
        hi = max(idx, key=lambda i: f["pop"][i])
        out.append(dict(step=int(f["step"][lo]), pop=int(f["pop"][lo]), ridge=int(f["pop2"][lo]),
                        cross=f["cross2"][lo] / max(f["pop2"][lo], 1), peak=int(f["pop"][hi]),
                        store=f.get("root2", [0] * len(f["step"]))[lo],
                        store_peak=f.get("root2", [0] * len(f["step"]))[hi]))
    return out


def main():
    logs = {label: load_csv(f"results/{run}_log.csv", folder) for label, (folder, run, _) in RUNS.items() if exists(folder, run)}
    fines = {label: fine(run, folder, STEPS) for label, (folder, run, _) in RUNS.items() if label in logs}
    slot = {label: s for label, (_, _, s) in RUNS.items()}
    xs = max((d["step"] for d in logs.values()), key=len)
    fx = max((d["step"] for d in fines.values()), key=len)

    def pad(ys, n):
        return ys + [float("nan")] * (n - len(ys))

    def series(key, labels=None):
        return [(label, pad(list(logs[label][key]), len(xs)), slot[label]) for label in (labels or RUNS) if label in logs and key in logs[label]]

    def fine_fn(fn, need="pop", labels=None):
        return [(label, pad(fn(fines[label]), len(fx)), slot[label]) for label in (labels or RUNS) if label in fines and need in fines[label]]

    store_total = lambda f: [f["root0"][i] + f["root1"][i] + f["root2"][i] for i in range(len(f["step"]))]
    charts_pipe = [
        line_chart("What the ground holds", "The store in the ground of all 16,384 cells, every 1,000 steps. Full would be 65,536 at root 4 and 131,072 at root 8; the control has no store.",
                   fx, fine_fn(store_total, need="root0"), ymin=0),
        line_chart("Laid and dug, per step", "Matter put into the ground and matter dug out of it, per step, in the two runs that differ most (log.csv, one point per 10,000 steps). The lines lie on each other when the store is a pipe.",
                   xs, [("laid (round 2, dig 0.5)", pad(list(logs["round 2: root 4, dig 0.5"]["stored"]), len(xs)), 1),
                        ("dug (round 2, dig 0.5)", pad(list(logs["round 2: root 4, dig 0.5"]["dug"]), len(xs)), 0),
                        ("laid (round 2, dig 0.1)", pad(list(logs["round 2: root 4, dig 0.1"]["stored"]), len(xs)), 6),
                        ("dug (round 2, dig 0.1)", pad(list(logs["round 2: root 4, dig 0.1"]["dug"]), len(xs)), 2)], ymin=0),
    ]
    charts_ridge = [
        line_chart("Bodies on the ridge", "Bodies standing in the top third of the world by height, every 1,000 steps. The dips are the winters, when the ridge is dark.",
                   fx, fine_fn(lambda f: list(f["pop2"]), need="pop2"), ymin=0),
        line_chart("The store on the ridge", "What the ground of the ridge's 5,461 cells holds, every 1,000 steps. It has to stand through a winter to be of any use.",
                   fx, fine_fn(lambda f: list(f["root2"]), need="root2"), ymin=0),
    ]
    charts_cost = [
        line_chart("Sun lost for want of soil", "Sun that fell on a cell with nothing left in its soil, per step, of the 164 the world gets. Rising means the soil is not being fed.",
                   xs, series("barren"), ymin=0),
        line_chart("Bodies every 1,000 steps", "All bodies alive. The floor of a dip is what lives through the winter; e035's pilot is the control.",
                   fx, fine_fn(lambda f: list(f["pop"])), ymin=0),
    ]

    def summary_row(label):
        d, f = logs[label], fines[label]
        w = floors(f)
        half = [i for i, t in enumerate(d["step"]) if t > STEPS // 2]
        mean = lambda k: sum(d[k][i] for i in half) / len(half) if k in d else float("nan")
        n = lambda x: "-" if x != x else f"{x:,.0f}"
        fmt = lambda k, s: ", ".join(s.format(r[k]) for r in w)
        stock = d["root_stock"][-1] if "root_stock" in d else float("nan")
        laid = f"{mean('stored'):.2f} / {mean('dug'):.2f}" if "stored" in d else "-"
        return (f"<tr><td>{label}</td><td>{fmt('pop', '{:,}')}</td><td>{min(r['ridge'] for r in w)}-{max(r['ridge'] for r in w)}</td>"
                f"<td>{min(r['cross'] for r in w):.0%}-{max(r['cross'] for r in w):.0%}</td>"
                f"<td>{min(r['peak'] for r in w):,}-{max(r['peak'] for r in w):,}</td>"
                f"<td>{min(r['store'] for r in w):,.0f}-{max(r['store'] for r in w):,.0f}</td>"
                f"<td>{laid}</td><td>{n(stock)}</td><td>{mean('fruit'):.0f}</td><td>{mean('barren'):.0f}</td></tr>")

    rows = "".join(summary_row(label) for label in RUNS if label in logs)

    # One winter of the ridge, in the run with the deepest store that a body can live on.
    trace_label = "round 2: root 8, dig 0.5"
    tf = fines[trace_label]
    trace = "".join(f"<tr><td>{int(tf['step'][i]):,}</td><td>{int(tf['pop'][i]):,}</td><td>{int(tf['pop2'][i]):,}</td><td>{tf['root2'][i]:,.0f}</td><td>{tf['root0'][i]:,.0f}</td></tr>"
                    for i in range(len(tf["step"])) if 60_000 <= tf["step"][i] <= 80_000 and int(tf["step"][i]) % 2000 == 0)

    tables = data_table(["step", "pop", "births", "deaths_energy", "plant_intake", "regrowth", "rain", "soil", "barren", "dry", "water", "root_stock", "stored", "dug", "fruit", "fruit_stock", "fruit_eaten", "trees", "fat_stock", "biters_any_share", "mass_p50", "lineages"],
                        {f"{label}, seed 9": d for label, d in logs.items()}, every=1)
    TEXT.update(TEXTS)
    TEXT["gallery"] = gallery(GALLERY, GALLERY_CAPTION)
    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>e036 A store in the ground - Report</title>
<style>{CSS}</style>
</head>
<body>
<main>
<h1>e036: A store in the ground</h1>
<p class="sub">Experiment report - 2026-09-06 - plant matter kept in the ground of a cell, filled by the growth past the plant's cap and dug out slowly: seven pilots on seed 9 in the season world against e035's. No batch: no body wintered on the ridge.</p>

<section class="tldr">
<h2>TL;DR</h2>
<p>{TEXT["tldr"]}</p>
</section>

<h2>1. Question</h2>
<p>{TEXT["question"]}</p>
<ol>
  <li><strong>The store fills and stands:</strong> the summer's surplus is large, and the crowd can only dig a share of a bite out of the cells it stands on.</li>
  <li><strong>The ridge is held through the winter</strong> where the store pays a body's upkeep (dig 0.5: 0.08 a step against 0.074), and a lineage becomes the ridge's.</li>
  <li><strong>The two rates are in tension:</strong> a store fast enough to winter on is eaten in summer.</li>
  <li><strong>A store is matter out of the cycle:</strong> the world's floors fall with what is locked up unless the ridge's winter pays for it.</li>
</ol>

<h2>2. The law</h2>
<p>{TEXT["world"]}</p>
{DIAGRAM}
<p><strong>Runs.</strong> {TEXT["runs"]}</p>
<ul class="measures">
  <li><strong>bodies and store per band</strong> - every 1,000 steps (pop.csv): the winter floors, the ridge's bodies, the share of them born in another band, what the ground holds where.</li>
  <li><strong>laid and dug</strong> - per step (log.csv): matter put into the ground and taken out of it; the store standing at the end.</li>
  <li><strong>fruit, barren</strong> - per step: what still falls as fruit, and the sun lost on cells whose soil is empty.</li>
  <li><strong>bodies</strong> - the median body per band at the equinoxes (places.csv) and the lineages that held the most agent-steps.</li>
</ul>

<h2>3. Results</h2>
<div class="tw"><table>
<thead><tr><th>Seed 9, 100,000 steps (five winters)</th><th>winter floors, in order</th><th>ridge's bodies at the floors</th><th>of those, born in another band</th><th>summer peaks</th><th>ridge's store at the floors</th><th>laid / dug per step</th><th>store standing at the end</th><th>fruit fallen per step</th><th>sun lost for want of soil, per step (of 164)</th></tr></thead>
<tbody>{rows}</tbody></table></div>
<ol class="verdicts">
{TEXT["verdicts"]}
</ol>

<h3>3.1 {TEXT["h_pipe"]}</h3>
<div class="grid2">
{"".join(charts_pipe)}
</div>
<p>{TEXT["p_pipe"]}</p>

<h3>3.2 {TEXT["h_ridge"]}</h3>
<div class="grid2">
{"".join(charts_ridge)}
</div>
<div class="tw"><table>
<thead><tr><th>One winter, root 8 and dig 0.5 (round 2)</th><th>bodies</th><th>on the ridge</th><th>store on the ridge</th><th>store in the valley</th></tr></thead>
<tbody>{trace}</tbody></table></div>
<p>{TEXT["p_ridge"]}</p>

<h3>3.3 {TEXT["h_cost"]}</h3>
<div class="grid2">
{"".join(charts_cost)}
</div>
<p>{TEXT["p_cost"]}</p>
{TEXT["gallery"]}

<h2>4. Discussion</h2>
{TEXT["discussion"]}

<h2>5. Conclusion and next step</h2>
<p>{TEXT["conclusion"]}</p>

<h2>Appendix: data</h2>
<p>Every log step of the seven pilots; the full data is in <code>results/*.csv</code> and <code>../e035_water/results/</code>. Build this report with <code>uv run python experiments/e036_ground/report.py</code>.</p>
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
    ("round 2, root 4, dig 0.5", HERE, run(4, 0.5, True), 755, "the gut that digs", "Fourteen gut blocks spread over an 8-grid and no muscle: it sits over a wide patch and takes both the bite and the digging."),
    ("round 2, root 8, dig 0.5", HERE, run(8, 0.5, True), 473, "the dense mover", "A full 4x4 block at density 2: nine muscle behind seven gut cells, the kind that has won since e025, unchanged by the store."),
    ("round 2, root 4, dig 0.1", HERE, run(4, 0.1, True), 216, "the gut net", "A full 5x5 of gut, mass 31: where the ground gives only a tenth of a bite, what wins is all mouth and covers more cells."),
    ("no store (e035)", E035, run(), 1, "the control's sitting gut", "The same light gut that held e035's world for 100,000 steps: the store changes what a cell gives, not what wins."),
]
GALLERY_CAPTION = "The most common body of the lineage at its peak, on the grid it grew on, front up (blue hard, orange muscle, yellow sensor, aqua gut). The four lineages that held the most agent-steps in their runs are e035's two kinds - a spread gut and a dense block that moves - in both worlds."


TEXTS = {
    "tldr": ("A cell's ground was given a store: the growth past the plant's cap, which falls as fruit today, kept where it does not rot and dug out at a share of a bite. "
             "It does not make the ridge liveable in the dark. What is laid is dug the same step (22.6 and 22.6 at root 4), the ground stays 1-16% full, and a store slow enough to stand cannot pay a body's upkeep. Not kept, and no batch was run."),
    "question": ("Since e032 the ridge is dark for 8,000 steps of every 20,000, and it is refilled from below every summer: 72-92% of the bodies standing there at the winter floor were born in another band. "
                 "In the real world a dark place still feeds animals out of what the summer left in the ground - seeds, roots, tubers, bark. Does a store in the ground make the ridge a place a lineage holds through the winter, and does the world's floor rise?"),
    "world": ("e035's world with one law. What a cell grows past the plant's cap of 8 goes into the ground, up to root per cell, instead of falling as fruit; it does not rot and no bite reaches it. "
              "A gut block digs dig x 0.02 out of it per step, besides its bite. Round 2 lays it in the ground of the cell the fruit falls on."),
    "runs": ("Seed 9, 100,000 steps (five winters), one thread each, 25 minutes a round. Round 1 brackets the two rates with the store laid where the surplus grew: root 4 at dig 0.5, 0.1 and 1, and root 1 at dig 0.5. "
             "Round 2 lays it where the fruit falls: root 4 at dig 0.5 and 0.1, root 8 at dig 0.5. Control: e035's pilot. Measures:"),
    "verdicts": ("<li><span class=\"verdict no\">No</span> The ground stays 1-16% full (394-10,972 of the 65,536 a root of 4 could hold), and what is laid is dug the same step in all seven runs.</li>"
                 "<li><span class=\"verdict no\">No</span> 33-91 bodies on the ridge at the floors against the control's 36-63, and 74-100% of them born in another band against 72-92%. No lineage is the ridge's.</li>"
                 "<li><span class=\"verdict\">Yes</span> dig 0.5 pays 0.08 a step and is dug out by the autumn; dig 0.1 leaves 1,570-2,561 standing on the ridge and pays 0.016 against an upkeep of 0.074.</li>"
                 "<li><span class=\"verdict partly\">Partly</span> The floors are 528-828 against 626-775, within one seed's spread; but the sun lost for want of soil doubles, 8.8 to 20 a step.</li>"),
    "h_pipe": "The store is a pipe, not a store",
    "p_pipe": ("Fill and drain are the same number in every run, to two decimals, and the ground never fills: 1-5% of what it could hold in round 1, up to 16% in round 2. "
               "The surplus goes in and comes straight out, because the crowd stands on every cell that has anything in it. A stock builds only where the digging is too slow to matter, at dig 0.1."),
    "h_ridge": "The ridge's winter is what it was",
    "p_ridge": ("The store carries the ridge's crowd for two or three thousand steps of the eight thousand dark ones, then it is gone, and the floor is the control's. "
                "Wintering even 100 bodies there costs 59,000 - 42% of the 140,186 of matter in the whole world - so the ground of 5,461 cells cannot be the answer whatever its cap."),
    "h_cost": "The store costs the world sun",
    "p_cost": ("Taking the surplus out of the fall costs the soil. What fell on the ring of 8 and rotted into the soil that the lake mixes now sits in the ground of one cell, so the sun lost on cells with an empty soil rises from 8.8 a step to 11-20, "
               "and the standing trees fall from 239 to 52-134. Nothing in the winter pays that back."),
    "discussion": ("<p>The tension is arithmetic, not a matter of finding the rate. A store the crowd can reach is eaten at the rate the crowd can eat, and the only stores that stand are the ones nobody can live on. Round 2 says the placement is not the fix either: spreading the store over the ring of 8 raised what the ground holds fourfold and left the winter as it was.</p>"
                   "<p>The dark is simply too long for a ground store. Eight thousand steps at 0.074 a body is 590 per body wintered, and matter in the ground is matter not circulating - the world already loses twice the sun for want of soil with 3,990-10,972 locked up.</p>"
                   "<p>Not shown: a store bodies cannot reach without a trait that costs them something in summer, and a shorter dark. The store did not change what wins either, except at dig 1, where a ground that gives a whole bite of its own halves the median body (mass 10.5 against 17.6): a body fed from below does not need to walk.</p>"),
    "conclusion": ("Not kept. root and dig stay in the code as arguments, 0 by default, and the season world is e035's. Issue #36 is answered: the ground cannot hold a winter. "
                   "Wintering in place is a question of what a body can carry, not of what the ground keeps - e030's fat at store 5 pays 1,400 steps of the 8,000 dark ones. Next: a body that needs water (#37), and the rain on the ridge under the carrier (#38)."),
}


if __name__ == "__main__":
    main()
