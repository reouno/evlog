#!/usr/bin/env python3
"""Build report.html for this experiment.

Charts: matplotlib, exported as SVG and inlined. Diagram: hand-written SVG.
Run from the repo root: uv run python experiments/e031_breed/report.py
"""
import csv
import html
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
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4"]  # fixed slot order
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

BASE = "128_sigma0_r64_f0.1_flat_eyes8_flesh1_w1_season1_digest0_sidegrow_store5"
BASE75 = "128_sigma0_r64_f0.1_flat_eyes8_flesh1_w1_season0.75_digest0_sidegrow_store5"
E030 = os.path.join(HERE, "..", "e030_store")
# The pilots at amplitude 1: label -> (folder, run prefix, color slot). The control is this code with both laws off (e030's world).
RUNS = {
    "control": (HERE, f"{BASE}_yolk0_breed0_seed9", 1),
    "yolk": (HERE, f"{BASE}_yolk0.5_breed0_seed9", 3),
    "breed": (HERE, f"{BASE}_yolk0_breed1_seed9", 2),
    "yolk + breed": (HERE, f"{BASE}_yolk0.5_breed1_seed9", 0),
}
CONTROL, YOLK, BREED, BOTH = list(RUNS)
STEPS = 100_000
# The batch at amplitude 0.75, where the world stands: breed alone and both laws, seeds 1-3, 300,000 steps,
# against e030's store-5 runs (this code with both laws off).
BATCH = {
    "breed": (HERE, f"{BASE75}_yolk0_breed1", 2),
    "yolk + breed": (HERE, f"{BASE75}_yolk0.5_breed1", 0),
    "control (e030)": (E030, BASE75, 1),
}
B_BREED, B_BOTH, B_CONTROL = list(BATCH)
SEEDS = [1, 2, 3]
LAST_STEP = 300_000
SEASON = 20_000
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
    legend_above(ax, len(series))
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
<svg viewBox="0 0 820 300" width="100%" role="img" aria-label="The yolk and the decision to breed" font-size="12" fill="currentColor" stroke="currentColor">
  <defs><marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0,0 L10,5 L0,10 z" stroke="none" fill="currentColor"/></marker></defs>
  <g fill="none" stroke-width="1.2">
    <rect x="20" y="40" width="200" height="70" rx="6"/>
    <rect x="300" y="30" width="180" height="90" rx="6" stroke="var(--s1)" stroke-width="2"/>
    <rect x="300" y="190" width="180" height="70" rx="6"/>
    <rect x="600" y="80" width="200" height="90" rx="6"/>
  </g>
  <text x="120" y="60" text-anchor="middle">what the body sees</text>
  <text x="120" y="76" text-anchor="middle" font-size="10">food under it, food and bodies</text>
  <text x="120" y="89" text-anchor="middle" font-size="10">in four directions, its energy</text>
  <text x="120" y="102" text-anchor="middle" font-size="10">(not its fat, not the season)</text>
  <text x="390" y="52" text-anchor="middle" fill="var(--s1)">the decision</text>
  <text x="390" y="68" text-anchor="middle" font-size="10">five outputs from the genes:</text>
  <text x="390" y="81" text-anchor="middle" font-size="10">stay, forward, left, right,</text>
  <text x="390" y="94" text-anchor="middle" font-size="10" fill="var(--s1)">breed (the fifth, e031)</text>
  <text x="390" y="107" text-anchor="middle" font-size="10">the largest wins the step</text>
  <text x="390" y="212" text-anchor="middle">the parent</text>
  <text x="390" y="228" text-anchor="middle" font-size="10">energy at the threshold</text>
  <text x="390" y="241" text-anchor="middle" font-size="10">2 + 0.1 mass, and fat</text>
  <text x="700" y="104" text-anchor="middle">the child</text>
  <text x="700" y="120" text-anchor="middle" font-size="10">half the parent's energy</text>
  <text x="700" y="133" text-anchor="middle" font-size="10">its body's matter (0.02 a unit of mass)</text>
  <text x="700" y="146" text-anchor="middle" font-size="10" fill="var(--s1)">and yolk x the parent's fat (e031)</text>
  <text x="700" y="159" text-anchor="middle" font-size="10">placed within a grid's side</text>
  <g fill="none" stroke-width="1.2" marker-end="url(#ah)">
    <path d="M220,75 L300,75"/>
    <path d="M390,120 L390,190"/>
    <path d="M480,225 C560,225 560,125 600,125"/>
  </g>
  <text x="260" y="66" text-anchor="middle" font-size="10">ten inputs</text>
  <text x="400" y="160" text-anchor="start" font-size="10">breed wins: the body stays,</text>
  <text x="400" y="172" text-anchor="start" font-size="10">and breeds if it can</text>
  <text x="540" y="250" text-anchor="middle" font-size="10">conception</text>
</svg>
<figcaption>Figure 1. The two laws. Breeding as a decision: the policy has a fifth output, read from the genes like the four moves; when it is the largest the body stays and breeds if its energy is at the threshold (with <code>breed</code> 0 a body breeds whenever its energy reaches the threshold, as in every experiment before). The yolk: the child is made of the share <code>yolk</code> of the parent's fat besides half its energy (with <code>yolk</code> 0 it is born with none). The threshold, the child's cost and the store (e030) do not change.</figcaption>
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

    def fine_series(key):
        return [(label, pad(list(fines[label][key]), len(fx)), slot[label]) for label in RUNS if label in fines and key in fines[label]]

    def rng(d, k, fmt="{:.2f}"):
        if k not in d:
            return "-"
        return f"{fmt.format(min(d[k]))}-{fmt.format(max(d[k]))}"

    charts_winter = [
        line_chart("Bodies every 1,000 steps", "All bodies alive, from pop.csv. Each dip is a winter with the sun out at 15,000, 35,000, ...; the floor of a dip is what lives through it.", fx, fine_series("pop"), ymin=0),
        line_chart("Lineages alive", "Lineages of 5 or more bodies every 1,000 steps. One line at the floor of a winter is a lottery.", fx, fine_series("lineages"), ymin=0),
        line_chart("Fat in all bodies", "The world's store, every 1,000 steps. The winter draws it down; what is left at the floor is what the survivors live on.", fx, fine_series("fat_stock"), ymin=0),
        line_chart("Bodies living on their fat", "Share of the bodies alive at zero energy, every 1,000 steps. Near 100% at a floor means the world is waiting on its fat.", fx, fine_series("on_fat"), ymin=0, ymax=1, percent=True),
    ]
    charts_breed = [
        line_chart("Decisions to breed", "Share of the bodies' decisions that were to breed, every 10,000 steps (bodies breeding at the threshold decide nothing: zero).", xs, series(lambda d, i: d["breed_share"][i] if "breed_share" in d else 0.0, [BREED, BOTH]), ymin=0, ymax=1, percent=True),
        line_chart("Decisions to breed made below the threshold", "Of the decisions to breed, the share the body could not carry out (it moved instead). A line falling from the start is selection on when to breed.", xs, series(lambda d, i: d["breed_denied"][i] if "breed_denied" in d else 0.0, [BREED, BOTH]), ymin=0, ymax=1, percent=True),
        line_chart("Fat per body", "Mean fat over the bodies alive, every 10,000 steps: with the yolk a newborn starts with half its parent's.", xs, series(lambda d, i: d["fat_mean"][i]), ymin=0),
        line_chart("Mean age", "Mean age of the bodies alive, every 1,000 steps (a body dies at 3,000). Old bodies at a winter floor are the ones that did not breed.", fx, fine_series("age_mean"), ymin=0),
    ]

    def summary_row(label):
        d, f = logs[label], fines[label]
        alive = [i for i, p in enumerate(d["pop"]) if p > 0]  # a world that died logs a last row of zeros
        d = {k: [v[i] for i in alive] for k, v in d.items()}
        if max(d.get("breed_share", [0])) == 0:
            d = {k: v for k, v in d.items() if k not in ("breed_share", "breed_denied")}
        w = winters(f)
        floors = [p for _, p, _, _ in w]
        lins = [l for _, _, l, _ in w]
        peaks = [p for _, _, _, p in w]
        return (f"<tr><td>{label}</td><td>{', '.join(f'{p:,}' for p in floors)}</td><td>{min(lins)}-{max(lins)}</td><td>{min(peaks):,}-{max(peaks):,}</td>"
                f"<td>{rng(d, 'fat_mean', '{:.0f}')}</td><td>{rng(d, 'on_fat', '{:.0%}')}</td><td>{rng(d, 'breed_share', '{:.0%}')}</td><td>{rng(d, 'breed_denied', '{:.0%}')}</td>"
                f"<td>{rng(d, 'deaths_energy', '{:,.0f}')}</td><td>{rng(d, 'side_mean', '{:.1f}')}</td><td>{rng(d, 'mass_p50', '{:.0f}')}</td></tr>")

    rows = "".join(summary_row(label) for label in RUNS if label in logs)
    tables = data_table(["step", "pop", "births", "deaths_energy", "fat_mean", "fat_stock", "on_fat", "fat_spent", "breed_share", "breed_denied", "side_mean", "mass_p50", "mass_p90", "sensor_agents_share", "lineages"],
                        {f"{label}, seed 9": d for label, d in logs.items()}, every=1)

    # ---- the batch ----
    blogs, blin, bfine = {}, {}, {}
    for world, (folder, run, _) in BATCH.items():
        blogs[world] = {sd: {k: v[:LAST_STEP // 10_000] for k, v in load_csv(f"results/{run}_seed{sd}_log.csv", folder).items()} for sd in SEEDS if exists(folder, f"{run}_seed{sd}")}
        blin[world] = {sd: lineage_rows(f"{run}_seed{sd}", folder) for sd in SEEDS if sd in blogs[world]}
        bfine[world] = {sd: fine(f"{run}_seed{sd}", folder, LAST_STEP, lineage_only=True) for sd in blogs[world]}  # the control has no pop.csv: one measure for all
    have_batch = bool(blogs[B_BREED])
    bsum = {}
    for world in BATCH:
        for sd, d in blogs[world].items():
            n = len(d["step"])
            h = slice(n // 2, n)
            by, f = blin[world][sd], bfine[world][sd]
            w = winters(f, first=LAST_STEP // SEASON // 2)
            spans = sorted((int(r[-1]["step"]) - int(r[0]["step"]) + CONFIRM_STEPS for r in by.values()), reverse=True)
            nw, hold, holds = winners(by, first_step=LAST_STEP // 2)
            bsum[(world, sd)] = dict(pop=median(d["pop"][h]), trough=min(p for _, p, _, _ in w) if w else 0, trough_lin=median(l for _, _, l, _ in w) if w else 0,
                                     peak=median(p for _, _, _, p in w) if w else 0, fat=median(d["fat_mean"][h]), on_fat=median(d["on_fat"][h]) if "on_fat" in d else 0.0,
                                     breed=median(d["breed_share"][h]) if "breed_share" in d else 0.0, denied=median(d["breed_denied"][h]) if "breed_denied" in d else 0.0,
                                     side=d["side_mean"][-1], side_std=d["side_std"][-1], p50=median(d["mass_p50"][h]), sensor=max(d["sensor_agents_share"]),
                                     longest=spans[0] if spans else 0, winners=nw, hold=hold, last=int(d["step"][-1]), died=int(d["step"][-1]) < LAST_STEP)
    charts_batch, brows = [], ""
    if have_batch:
        charts_batch = [
            seeds_chart("Bodies every 1,000 steps, three seeds", "Bodies in lineages of 5 or more (the measure e030 has), one line per seed and world. The floors are the winters.", bfine, lambda d, i: d["pop"][i], ymin=0),
            seeds_chart("Lineages alive, three seeds", "Lineages of 5 or more bodies every 1,000 steps, per seed and world.", bfine, lambda d, i: d["lineages"][i], ymin=0),
            seeds_chart("Decisions to breed made below the threshold", "Per seed, the worlds with the law: a falling line is selection on when to breed.", {k: v for k, v in blogs.items() if k != B_CONTROL}, lambda d, i: d["breed_denied"][i] if "breed_denied" in d else float("nan"), ymin=0, ymax=1, percent=True),
            seeds_chart("Fat per body", "Mean fat over the bodies alive, per seed and world.", blogs, lambda d, i: d["fat_mean"][i], ymin=0),
        ]
        brows = "".join((f"<tr><td>{world}, seed {sd}{' (died at ' + format(b['last'], ',') + ')' if b['died'] else ''}</td><td>{b['pop']:,.0f}</td><td>{b['trough']:,}</td><td>{b['trough_lin']:.0f}</td><td>{b['peak']:,.0f}</td>"
                         f"<td>{b['fat']:.0f}</td><td>{b['on_fat']:.0%}</td><td>{b['breed']:.0%}</td><td>{b['denied']:.0%}</td><td>{b['side']:.1f} &plusmn; {b['side_std']:.1f}</td><td>{b['p50']:.0f}</td>"
                         f"<td>{b['sensor']:.0%}</td><td>{b['longest']:,}</td><td>{b['winners']}; {b['hold']:,}</td></tr>")
                        for (world, sd), b in bsum.items())
    TEXT["question"] = ("e030 gave a body a store; the season at amplitude 1 went from death in the first winter to a lottery of 7-25 bodies each winter, because the fat is spread over thousands of young bodies with little each: "
                        "every body breeds the moment its energy reaches the threshold, and a child is born with none. This experiment writes the real world's two answers, a child provisioned from its mother's flesh and breeding that is timed, as laws of the flesh and of the body's decisions, and asks:")
    TEXT["world"] = ("e030's season world (the store at 5, the grid's side heritable) at amplitude 1: the sun a sine of 20,000 steps that goes out at midwinter, under a quarter for 4,600 steps. "
                     "The control is this code with both laws off (e030 byte for byte).")
    TEXT["runs"] = ("Three pilots on seed 9 at amplitude 1, 100,000 steps (yolk 0.5; breed; both), against the control rerun for its bodies every 1,000 steps. "
                    "Then, because amplitude 1 kills before it selects, the batch at 0.75 where the world stands: breed and both laws on seeds 1-3, 300,000 steps, against e030's store-5 runs. Every 1,000 steps pop.csv counts the bodies; every 10,000 the log records:")
    TEXT["h_winter"] = "At amplitude 1 the yolk is the control, and the decision to breed kills the world"
    TEXT["p_winter"] = ("With the yolk the floors are 8-26 bodies and the fat per body 5-6, the control's 8-22 and 7-18: the fat is shared among the same crowd. "
                        "With breeding as a decision the summer world is smaller and fatter (1,500-2,500 bodies, 12-27 of fat), and the floor is 5-9: the world dies in its second winter, alone or with the yolk.")
    TEXT["h_breed"] = "Nothing is selected about when to breed"
    TEXT["p_breed"] = ("The start's policies want to breed in a quarter to a third of their decisions whatever their energy, and 97-99% of those are below the threshold; neither share moves in two winters at amplitude 1, "
                       "nor in fifteen at 0.75 (29-48% and 98-99% in the second half of six runs). A denied decision costs nothing, and a body at the threshold breeds within a few steps anyway: the fifth output is a coin.")
    TEXT["h_batch"] = "At 0.75 the winter is the control's, with or without the yolk"
    TEXT["p_batch"] = ("Counted alike (bodies in lineages of 5 or more), the lowest floors are 498-710 with breed and 467-728 with both laws, against the control's 495-908; the lineages on the floors 4-16 against 8-17; "
                       "the fat per body 5-20 against 13-28. The bodies are e030's two kinds still, the light gut and the dense block, with one new armored mover in seed 3.")
    breed = lambda sd: (f"breed, seed {sd}", HERE, f"{BASE75}_yolk0_breed1_seed{sd}")
    both = lambda sd: (f"yolk + breed, seed {sd}", HERE, f"{BASE75}_yolk0.5_breed1_seed{sd}")
    TEXT["gallery"] = gallery([
        (*breed(1), 368, "Breed, seed 1: the light gut", "Eight guts on an 8x8 grid at density 0.8, mass 8: the sitting gut that holds seed 1 from 72,000 to the end, breeding within a few steps of its threshold like every body."),
        (*breed(2), 1117, "Breed, seed 2: the net with an eye", "Nine guts, seven muscle and a sensor spread over a 15x15 grid at density 2, mass 33: a net over many cells of ground, 104,000 steps beside a light gut."),
        (*breed(3), 1656, "Breed, seed 3: the armored mover", "Six hard blocks, ten muscle and five guts on a 5x5 grid, mass 43: the heaviest winner of the series, armor in front of muscle, 64% flesh in its intake."),
        (*both(3), 1120, "Yolk + breed, seed 3: the dense block", "Eight guts and seven muscle filling a 4x4 grid at density 2, mass 31: e030's block, 131,000 steps beside the light gut of lineage 289."),
    ], "Figure 2. Bodies of lineages that prospered at 0.75: the most common grown body of the lineage at its peak, on the grid it grew on (4x4 to 15x15, at one width), front up (the dashed edge). Blue: hard, orange: muscle, green: digestive, yellow: sensor.")
    TEXT["tldr"] = ("Neither law changes the winter. A child made of half its parent's fat shares the store among the same crowd (floors 8-26 at amplitude 1, the control's 8-22); breeding as the policy's fifth output is never selected toward a time "
                    "(98-99% of the decisions to breed are below the threshold from the first log step to the last, in six runs of 300,000 steps) and at amplitude 1 the world dies in its second winter. Not kept. "
                    "The dark winter is beyond the bodies: 131,000 of matter cannot carry 3,000 bodies through 3,000 dark steps. Next: a winter that differs by place.")
    TEXT["verdicts"] = ("<li><span class=\"verdict no\">No</span> The fat per body is 5-6 with the yolk against 7-18 without; the floors 8-26 against 8-22.</li>"
                        "<li><span class=\"verdict no\">No</span> Decisions to breed made below the threshold stay at 97-99% in every run; at amplitude 1 the floor is 5-9 and the world dies.</li>"
                        "<li><span class=\"verdict no\">No</span> Both laws die in the second winter at amplitude 1; at 0.75 their floors are 467-728 against the control's 495-908.</li>"
                        "<li><span class=\"verdict\">Yes</span> 2,000-3,400 bodies at 0.75 against e030's 1,700-3,100.</li>")
    TEXT["discussion"] = ("<p>The fifth output is not selected because nothing hangs on it. A decision to breed below the threshold costs nothing (the body moves instead), and above it the body breeds within two or three steps whether the output is a coin or a clock. "
                          "For a clock to pay, a body that holds its breeding through the autumn would have to leave more descendants than one that breeds and loses the children to the winter, and at amplitude 1 no body's descendants are counted: the floor is 5-25 bodies, a lottery. At 0.75 the floor is hundreds and the autumn's children live.</p>"
                          "<p>The arithmetic is the world's, not the bodies'. The world holds 131,000 of matter; 3,000 bodies pay 170 a step and the sun is out for 3,000 steps. A store in the bodies can carry a few hundred through, and does at 0.75; through the dark it cannot, however it is divided. "
                          "The real world's dark winters are lived by leaving (places that differ in season), by a store in the ground (seeds, roots, a standing wood nobody eats down), or by a body that pays less while it waits. The first two are laws about the world.</p>")
    TEXT["conclusion"] = ("Not kept: the yolk and the decision to breed stay as arguments (0 by default), the world is e030's. The season at amplitude 1 remains a lottery, and its answer is a world law: a winter that differs by place (the season's amplitude by height: mild in the valley, dark on the ridge), "
                          "so that leaving is an outcome a body can reach; or a store in the ground that stands through the dark.")
    for k in ["tldr", "question", "world", "runs", "verdicts", "h_winter", "p_winter", "h_breed", "p_breed", "h_batch", "p_batch", "gallery", "discussion", "conclusion"]:
        TEXT.setdefault(k, "TODO")
    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>e031 The child of the flesh, and breeding as a decision - Report</title>
<style>{CSS}</style>
</head>
<body>
<main>
<h1>e031: The child of the flesh, and breeding as a decision</h1>
<p class="sub">Experiment report - 2026-09-05 - a child made of half its parent's fat (the yolk), and breeding as the policy's fifth output, in e030's season world at amplitude 1 (the sun out at midwinter): three pilots on seed 9 and the batch on seeds 1-3 for 300,000 steps.</p>

<section class="tldr">
<h2>TL;DR</h2>
<p>{TEXT["tldr"]}</p>
</section>

<h2>1. Question</h2>
<p>{TEXT["question"]}</p>
<ol>
  <li><strong>The yolk keeps the fat in the lineage</strong> but shares it rather than concentrating it: the fat per body rises, the winter floor little.</li>
  <li><strong>Breeding as a decision concentrates the store.</strong> Selection finds bodies that do not breed when the food is low; the floor rises from 7-25 toward the hundreds the matter allows.</li>
  <li><strong>Together the lineage lives through the dark:</strong> the highest floors, and more than one lineage on them.</li>
  <li><strong>The summer world stands</strong> at e030's numbers.</li>
</ol>

<h2>2. The laws</h2>
<p>{TEXT["world"]}</p>
{DIAGRAM}
<p><strong>Runs.</strong> {TEXT["runs"]}</p>
<ul class="measures">
  <li><strong>bodies, lineages</strong> - every 1,000 steps (pop.csv; lineages of 5 or more); the winter floor is the least in each cycle of 20,000.</li>
  <li><strong>fat, on their fat, age</strong> - fat in all bodies and per body, the share at zero energy, the mean age.</li>
  <li><strong>breed, denied</strong> - decisions that were to breed, and of those the share made below the threshold.</li>
  <li>side, mass, bodies with a sensor, the longest lineage and the holders of the top place.</li>
</ul>

<h2>3. Results</h2>
<div class="tw"><table>
<thead><tr><th>Seed 9, 100,000 steps (five winters)</th><th>winter floors, in order</th><th>lineages at the floors</th><th>summer peaks</th><th>fat per body</th><th>on their fat</th><th>decisions to breed</th><th>of those, denied</th><th>starved per 10,000</th><th>side</th><th>mass p50</th></tr></thead>
<tbody>{rows}</tbody></table></div>
<ol class="verdicts">
{TEXT["verdicts"]}
</ol>

<h3>3.1 {TEXT["h_winter"]}</h3>
<div class="grid2">
{"".join(charts_winter)}
</div>
<p>{TEXT["p_winter"]}</p>

<h3>3.2 {TEXT["h_breed"]}</h3>
<div class="grid2">
{"".join(charts_breed)}
</div>
<p>{TEXT["p_breed"]}</p>

<h3>3.3 {TEXT["h_batch"]}</h3>
<div class="tw"><table>
<thead><tr><th>Amplitude 0.75, 300,000 steps (second half)</th><th>bodies</th><th>lowest winter floor (lineages of 5+)</th><th>lineages at the floors</th><th>summer peak</th><th>fat per body</th><th>on their fat</th><th>decisions to breed</th><th>denied</th><th>side at the end</th><th>mass p50</th><th>most with a sensor</th><th>longest lineage</th><th>winners; longest hold</th></tr></thead>
<tbody>{brows}</tbody></table></div>
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
<p>Every log step of the pilot runs; the full data is in <code>results/*.csv</code> and <code>../e030_store/results/</code>. Build this report with <code>uv run python experiments/e031_breed/report.py</code>.</p>
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


if __name__ == "__main__":
    main()
