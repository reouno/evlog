#!/usr/bin/env python3
"""Build report.html for this experiment.

Charts: matplotlib, exported as SVG and inlined. Diagram: hand-written SVG.
Run from the repo root: uv run python experiments/e038_income/report.py
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


def run(k=None, sun=None, seed=9):
    return f"{BASE}{'' if k is None else f'_k{k}'}{'' if sun is None else f'_sun{sun}'}_seed{seed}"


E037 = os.path.join(HERE, "..", "e037_upkeep")
# The pilots on seed 9 in e035's season world (water 0.1, leach 0.01, depth 0.01, mix 0.2, flow 0,
# winter high 2, store 5, grow, rain flat, no ground store): label -> (folder, run prefix, color
# slot). sun 1 is today's sun (e037's pilots, the same code), the control at each k.
RUNS = {
    "sun 1, k 1 (today)": (E037, run(), 5),
    "sun 2, k 1": (HERE, run(sun=2), 0),
    "sun 4, k 1": (HERE, run(sun=4), 1),
    "sun 1, k 0.6": (E037, run(0.6), 6),
    "sun 2, k 0.6": (HERE, run(0.6, 2), 3),
    "sun 4, k 0.6": (HERE, run(0.6, 4), 2),
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
<svg viewBox="0 0 900 290" width="100%" role="img" aria-label="The sun, the lawn and a gut block" font-size="12" fill="currentColor" stroke="currentColor">
  <text x="30" y="28" font-size="11" stroke="none">The sun's rate is an argument: 0.01 a cell a step (today), 0.02 or 0.04. Everything else is e037's world.</text>
  <g stroke-width="1.2" fill="none"><path d="M40,190 L860,190"/></g>
  <g fill="currentColor" stroke="none" opacity="0.35">
    <rect x="70" y="180" width="180" height="10"/>
    <rect x="360" y="170" width="180" height="20"/>
    <rect x="650" y="150" width="180" height="40"/>
  </g>
  <g fill="var(--s1)" stroke="none">
    <rect x="90" y="110" width="20" height="20"/><rect x="110" y="110" width="20" height="20"/><rect x="130" y="110" width="20" height="20"/>
    <rect x="380" y="110" width="20" height="20"/><rect x="400" y="110" width="20" height="20"/><rect x="420" y="110" width="20" height="20"/>
    <rect x="670" y="110" width="20" height="20"/><rect x="690" y="110" width="20" height="20"/><rect x="710" y="110" width="20" height="20"/>
  </g>
  <g fill="#eb6834" stroke="none">
    <rect x="150" y="110" width="20" height="20"/><rect x="440" y="110" width="20" height="20"/><rect x="730" y="110" width="20" height="20"/>
  </g>
  <g fill="none" stroke-width="1" stroke-dasharray="2 3">
    <path d="M120,132 L120,178"/><path d="M410,132 L410,168"/><path d="M700,132 L700,148"/>
  </g>
  <g stroke="none" font-size="10">
    <text x="90" y="100">a body: three gut blocks (accent), one muscle</text>
    <text x="380" y="100">the same body</text>
    <text x="670" y="100">the same body</text>
    <text x="130" y="160">bites up to 0.02 a step</text>
    <text x="420" y="160">from the lawn under it</text>
    <text x="710" y="140">the lawn regrows at the sun's rate</text>
  </g>
  <g stroke="none" font-size="10" text-anchor="middle">
    <text x="160" y="210">sun 1: the lawn regrows 0.01 a step</text>
    <text x="450" y="210">sun 2: 0.02</text>
    <text x="740" y="210">sun 4: 0.04</text>
  </g>
  <g stroke="none" font-size="10">
    <text x="40" y="245">the reading tested: a gut block earns what the lawn under it regrows (0.0017-0.0037 a step in e037), so more sun per cell should mean more per block</text>
    <text x="40" y="259">and a body that can afford more blocks; the other outcome is more bodies over the same lawn, each earning what it earns today (e027).</text>
  </g>
</svg>
<figcaption>Figure 1. The law under test. The sun's rate per cell is multiplied by 1, 2 or 4 (the rain's cap with it); the bite, the upkeep, the weight and the season are e037's. A gut block (accent) can take 0.02 a step, but the lawn under a body regrows at the sun's rate, so a body earns about the regrowth under its footprint. If that is what binds size, more sun per cell should let a body carry more blocks.</figcaption>
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
    charts_income = [
        line_chart("What a gut block earns", "intake_per_gut: what one gut block takes per step, mean over each 10,000 steps (log.csv; the points alternate summer and winter). The bite is 0.02. If the income is the lever, the lines rise with the sun.",
                   xs, series("intake_per_gut"), ymin=0),
        line_chart("What the world eats, per step", "Plant and flesh digested per step, one point per 10,000 steps. The sun is 1, 2 or 4 times today's, so this is the share of it the bodies reach.",
                   xs, [(label, pad(eaten(logs[label]), len(xs)), slot[label]) for label in RUNS if label in logs], ymin=0),
    ]
    charts_size = [
        line_chart("The median body", "Living cells of the median body, every 10,000 steps. A line that rises with the sun is size following the food; lines on each other mean the food is not what sets size.",
                   xs, series("size_p50"), ymin=0),
        hist_chart("Sizes at the end", "Bodies by living cells at step 100,000, all bodies alive (agents.csv). A tail to the right is what more food was meant to allow.",
                   [(label, sizes[label], None, slot[label]) for label in RUNS if label in sizes], bins=range(0, 41, 2), xlabel="living cells"),
    ]
    charts_world = [
        line_chart("Bodies", "Bodies alive every 1,000 steps (pop.csv). The dips are the winters. More sun carries more bodies; the question is whether it carries bigger ones.",
                   fx, fine_fn(lambda f: list(f["pop"])), ymin=0),
        line_chart("The 90th percentile", "Living cells of the body at the 90th percentile, every 10,000 steps. The top of the distribution, where a size that pays would show first.",
                   xs, series("size_p90"), ymin=0),
    ]
    charts_state = [
        line_chart("Bodies that bite", "Share of the bodies with a tooth (bite_any), every 10,000 steps. A hunter state is above 10%.",
                   xs, series("biters_any_share"), ymin=0, percent=True),
        line_chart("Soil per cell", "Matter in the soil, per cell (log.csv soil / 16,384). The regrowth is min(sun, soil), so the soil binds only when this nears the sun's 0.01-0.04 a step.",
                   xs, [(label, pad([v / CELLS for v in logs[label]["soil"]], len(xs)), slot[label]) for label in RUNS if label in logs], ymin=0),
    ]

    def summary_row(label):
        d, f = logs[label], fines[label]
        w = floors(f)
        half = [i for i, t in enumerate(d["step"]) if t > STEPS // 2]
        mean = lambda k: sum(d[k][i] for i in half) / len(half) if k in d else float("nan")
        fmt = lambda k, s: ", ".join(s.format(r[k]) for r in w)
        sz = sizes[label]
        q = statistics.quantiles(sz, n=10)
        winter = [i for i in half if d["sun"][i] < 1]
        summer = [i for i in half if d["sun"][i] >= 1]
        ig = lambda idx: sum(d["intake_per_gut"][i] for i in idx) / len(idx)
        return (f"<tr><td>{label}</td><td>{fmt('pop', '{:,}')}</td><td>{min(r['valley'] for r in w):.0%}-{max(r['valley'] for r in w):.0%}</td>"
                f"<td>{min(r['peak'] for r in w):,}-{max(r['peak'] for r in w):,}</td>"
                f"<td>{ig(summer):.4f} / {ig(winter):.4f}</td>"
                f"<td>{mean('size_p10'):.0f} / {mean('size_p50'):.0f} / {mean('size_p90'):.0f}</td><td>{mean('size_max'):.0f}</td>"
                f"<td>{q[0]:.0f} / {statistics.median(sz):.0f} / {q[-1]:.0f} / {max(sz)}</td>"
                f"<td>{sum(eaten(d)[i] for i in half) / len(half):.0f}</td><td>{mean('soil') / CELLS:.1f}</td><td>{mean('biters_any_share'):.0%}</td><td>{f['lineages'][-1]}</td></tr>")

    rows = "".join(summary_row(label) for label in RUNS if label in logs)

    tables = data_table(["step", "pop", "births", "deaths_energy", "plant_intake", "meat_intake", "regrowth", "barren", "dry", "size_p10", "size_p50", "size_p90", "size_max", "mass_p10", "mass_p50", "mass_p90", "mass_max", "density_mean", "fat_stock", "biters_any_share", "trees", "lineages"],
                        {f"{label}, seed 9": d for label, d in logs.items()}, every=1)
    TEXT.update(TEXTS)
    TEXT["gallery"] = gallery(GALLERY, GALLERY_CAPTION)
    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>e038 Does the income bind size? - Report</title>
<style>{CSS}</style>
</head>
<body>
<main>
<h1>e038: Does the income bind size?</h1>
<p class="sub">Experiment report - 2026-09-09 - the sun's rate per cell at 1, 2 and 4 times today's, at k 1 and k 0.6, seed 9, 100,000 steps, against e037's pilots. A test of e037's reading that the income binds size. Answer: no, the crowd pins it.</p>

<section class="tldr">
<h2>TL;DR</h2>
<p>{TEXT["tldr"]}</p>
</section>

<h2>1. Question</h2>
<p>{TEXT["question"]}</p>
<ol>
  <li><strong>The income is the lever:</strong> with twice the sun a gut block earns more (toward 0.004-0.007 a step) and the size distribution after step 40,000 moves up, most at k 0.6; at four times the sun, further.</li>
  <li><strong>Or the constraint is elsewhere:</strong> if the extra sun becomes more bodies of the same size (e027's reading), the food is not what sets size, and the next size law should not be about food.</li>
</ol>

<h2>2. The law</h2>
<p>{TEXT["world"]}</p>
{DIAGRAM}
<p><strong>Runs.</strong> {TEXT["runs"]}</p>
<ul class="measures">
  <li><strong>a gut block's income</strong> - intake_per_gut: what one gut block takes per step, mean over 10,000 steps (log.csv); summer and winter alternate.</li>
  <li><strong>size</strong> - living cells of a body: the 10th, 50th and 90th percentiles and the largest, every 10,000 steps, and every body at the end (agents.csv).</li>
  <li><strong>soil</strong> - matter in the soil per cell: whether the regrowth, min(sun, soil), is bound by the soil.</li>
  <li><strong>bodies and floors</strong> - bodies alive every 1,000 steps (pop.csv), the winter troughs and the valley's share of them.</li>
  <li><strong>eaten, biters, lineages</strong> - what the world digests per step, the share of bodies with a tooth, lineages of five or more.</li>
</ul>

<h2>3. Results</h2>
<div class="tw"><table>
<thead><tr><th>Seed 9, 100,000 steps (five winters)</th><th>winter floors, in order</th><th>valley's share at the floors</th><th>summer peaks</th><th>a gut block earns per step: summer / winter</th><th>size p10 / p50 / p90 (second half)</th><th>largest body</th><th>size at the end: p10 / p50 / p90 / max</th><th>eaten per step</th><th>soil per cell</th><th>biters</th><th>lineages at the end</th></tr></thead>
<tbody>{rows}</tbody></table></div>
<ol class="verdicts">
{TEXT["verdicts"]}
</ol>

<h3>3.1 {TEXT["h_income"]}</h3>
<div class="grid2">
{"".join(charts_income)}
</div>
<p>{TEXT["p_income"]}</p>

<h3>3.2 {TEXT["h_size"]}</h3>
<div class="grid2">
{"".join(charts_size)}
</div>
<p>{TEXT["p_size"]}</p>

<h3>3.3 {TEXT["h_world"]}</h3>
<div class="grid2">
{"".join(charts_world)}
</div>
<p>{TEXT["p_world"]}</p>

<h3>3.4 {TEXT["h_state"]}</h3>
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
<p>Every log step of the six runs (the sun 1 runs are e037's pilots); the full data is in <code>results/*.csv</code>. Build this report with <code>uv run python experiments/e038_income/report.py</code>.</p>
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
    ("sun 1, k 1 (today)", E037, run(), 1, "the gut bar", "Ten gut cells, mass 9: the grazer that has won since e016, the whole run under today's sun."),
    ("sun 2, k 1", HERE, run(sun=2), 1, "the grazer with legs", "Nine gut cells and seven muscle, 18 cells at density 1.2, the run's top lineage from start to end. Twice the sun did not make it bigger than 16-18."),
    ("sun 4, k 1", HERE, run(sun=4), 223, "the smaller grazer", "Six gut cells and nothing else, mass 5: under four times the sun the lineage that held the most body-steps is smaller than today's winner, and it peaked at 8,671 bodies."),
    ("sun 1, k 0.6", E037, run(0.6), 261, "e037's armored hunter", "Thirty-seven cells, ten hard, a bite of 1.6: the hunter of e037's pilot, at k 0.6 under today's sun, 23,000-61,000."),
    ("sun 2, k 0.6", HERE, run(0.6, 2), 236, "the hunter that held the run", "Twenty-nine cells, ten hard, eight muscle, a bite of 2.0, density 1.4: one lineage from step 14,000 to the end, the most body-steps of any run here. Twice the sun kept the hunter, not a bigger one."),
    ("sun 4, k 0.6", HERE, run(0.6, 4), 7, "the hunter under four suns", "Thirty-three cells, ten hard, a bite of 1.5, alive 5,000-83,000, then replaced by dense movers of 12-19 cells (density 2.0). The same body as under one sun; the sun did not add to it."),
]
GALLERY_CAPTION = "The most common body of the lineage at its peak, on the grid it grew on, front up (blue hard, orange muscle, yellow sensor, aqua gut). Under every sun the k 1 winner is a grazer of 6-18 cells and the k 0.6 winner an armored hunter of 29-37 cells: the bodies are the same, only their number changes."

TEXTS = {
    "tldr": ("No: the income per gut block is not what more sun moves. With two and four times the sun a gut block still earns 0.003-0.005 a step in summer; the extra sun becomes more bodies (1.3-1.5x, then 1.5-2x) of the same size or smaller, "
             "and at k 0.6 the hunters of 37 cells give way to 30-cell ones and then to dense movers. The crowd fills the food and pins the income per block. Next: a food only a big body reaches (#41), whose income the crowd cannot dilute."),
    "question": ("e037 moved the cost of a body and size did not move; the reading was that the income binds, a gut block earning a fifth of its bite from a grazed lawn because the lawn regrows at the sun's rate. "
                 "If so, more sun per cell should raise what a block earns and let a body carry more blocks. This is the test, before the tree law that assumes it."),
    "world": ("e037's season world with the sun's rate as an argument: 0.01 a cell a step (today), 0.02 or 0.04, the rain's cap with it. The bite, the upkeep (k 1 or 0.6), the weight and the winter are unchanged. The matter stays 8 a cell."),
    "runs": ("Seed 9, 100,000 steps, one thread each, four at once on the Mac, 16-26 minutes: sun 2 and 4 at k 1 and at k 0.6. The controls at sun 1 are e037's pilots on the same seed and code."),
    "verdicts": ("<li><span class=\"verdict no\">No</span> a gut block earns 0.0037-0.0046 in summer under every sun at k 1 (0.0031-0.0033 at k 0.6); the winter income doubles once, from 0.0016 to 0.0030, and stops there. The median body is 9-15 cells at k 1 under every sun.</li>"
                 "<li><span class=\"verdict\">Yes</span> the extra sun is more bodies: the winter floors go from 626-775 to 1,037-1,347 to 1,393-1,865 at k 1, and the world eats 116, 175, 209 a step, with the 90th percentile at 16-22 cells.</li>"),
    "h_income": "A gut block earns the same under every sun",
    "p_income": ("The summer lines lie on each other: whatever the sun, a block takes 0.003-0.005 a step, a quarter of its bite. Only the winter income moves, and only from sun 1 to 2. "
                 "What the world eats does rise, 1.5x at sun 2 and 1.8x at sun 4, so the sun is reaching bodies; it reaches more of them, not more per block."),
    "h_size": "Size does not follow the food",
    "p_size": ("At k 1 the median is 9, 11 and 15 cells by sun and the 90th percentile 22, 16 and 19; the winner under four suns is a 6-cell gut bar. "
               "At k 0.6 the median stays at 18-23 while the 90th percentile falls from 53 to 37 to 30 and the biters from 33% to 6%: more sun makes the hunter world smaller, not bigger."),
    "h_world": "The sun becomes bodies, denser and more numerous",
    "p_world": ("The floors double at sun 2 and rise a further 40% at sun 4; births go from 12 to 18 a step at k 1 and from 3.6 to 8.3 at k 0.6. The bodies get denser (1.5 to 1.7) and stand on less lawn (a footprint of 3.0 to 2.2 cells). "
                "e027's reading at four times the space holds on the same grid: the world converts sun into bodies at the size it has."),
    "h_state": "The soil falls but does not bind; the tooth fades",
    "p_state": ("The soil goes from 6.2 to 2.2 a cell as the matter moves into bodies, lawn and trees, still 55 times the sun's rate: regrowth was never soil-bound, and the issue's 'soil to match' was not needed. "
                "The hunter state of k 0.6 thins with the sun (33%, 29%, 6%): the dead lie thicker where more bodies are, and a mouth pays less against a gut."),
    "discussion": ("<p>The reading from e037 was half right. A gut block does earn about the regrowth under the footprint, but the regrowth under a footprint is not the sun's: it is the sun's divided by the bodies that share the lawn, and the bodies multiply until a block earns what it earns today. "
                   "More sun per cell is more bodies per cell. The income per block is pinned by the crowd, not by the sun.</p>"
                   "<p>That changes what a size law must do. A law that gives the world more food will be eaten by more small bodies. A law that gives a big body a food the small ones cannot reach is not diluted this way: the tree as a column with a reach (#41) is that law, and this result is the reason for it rather than against it. "
                   "The move cost of a big body (mass times distance) stays untested as the other candidate.</p>"
                   "<p>Not shown: one seed, 100,000 steps; the start's transient is in every run (e037), so the numbers are read after step 40,000 and the k 0.6 hunter worlds are the transient's. The world at sun 4 is 1.5 times slower per step (more bodies).</p>"),
    "conclusion": ("The income per gut block is pinned by the crowd at 0.003-0.005 a step, and more sun does not lift it; size does not follow the food. `sun` stays an argument, 1 by default. "
                   "Next: #41, a food only a big body reaches (the tree as a column, a bite up to a reach), because an income that only size reaches is the one the crowd cannot dilute; then #37 and #38."),
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
