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

def base(amp, winter):
    return f"128_sigma0_r64_f0.1_flat_eyes8_flesh1_w1_season{amp}_digest0_sidegrow_store5_yolk0_breed0{winter}"

HIGH = "_winterhigh"
E031 = os.path.join(HERE, "..", "e031_breed")
# The pilots on seed 9: label -> (folder, run prefix, color slot). The control is e031's rerun at flat 1 (this code, winter flat).
RUNS = {
    "flat 1 (e031)": (E031, f"{base(1, '')}_seed9", 1),
    "high 1": (HERE, f"{base(1, HIGH)}_seed9", 3),
    "high 2": (HERE, f"{base(2, HIGH)}_seed9", 0),
    "high 3": (HERE, f"{base(3, HIGH)}_seed9", 2),
}
CONTROL, HIGH1, HIGH2, HIGH3 = list(RUNS)
STEPS = 100_000
# The batch: the winter by height at the amplitude the pilots picked against the flat season at the same world sun at midwinter (0.75), seeds 1-3, 300,000 steps.
BATCH = {
    "high 2": (HERE, base(2, HIGH), 0),
    "high 3": (HERE, base(3, HIGH), 2),
    "flat 0.75": (HERE, base(0.75, ""), 1),
}
B_HIGH2, B_HIGH3, B_FLAT = list(BATCH)
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
<svg viewBox="0 0 820 300" width="100%" role="img" aria-label="The winter by height" font-size="12" fill="currentColor" stroke="currentColor">
  <defs><marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0,0 L10,5 L0,10 z" stroke="none" fill="currentColor"/></marker></defs>
  <path d="M20,250 C120,250 180,240 240,200 C300,160 340,110 400,90 C460,70 520,120 580,150 C640,180 700,190 800,190" fill="none" stroke-width="2"/>
  <line x1="20" y1="250" x2="800" y2="250" stroke-width="1" stroke-dasharray="3 3" opacity="0.5"/>
  <text x="24" y="268" font-size="10">height 0 (the bottom of the valley)</text>
  <text x="400" y="80" text-anchor="middle" font-size="10">the ridge, at the relief and above</text>
  <g fill="none" stroke-width="1.2">
    <rect x="60" y="184" width="110" height="52" rx="4"/>
    <rect x="240" y="120" width="110" height="52" rx="4"/>
    <rect x="600" y="40" width="110" height="52" rx="4" stroke="var(--s1)" stroke-width="2"/>
  </g>
  <g fill="none" stroke-width="1.5">
    <path d="M66.0,210.0 L68.5,209.5 L70.9,209.0 L73.3,208.5 L75.8,208.1 L78.2,207.7 L80.7,207.3 L83.2,207.1 L85.6,206.9 L88.0,206.7 L90.5,206.7 L93.0,206.7 L95.4,206.9 L97.8,207.1 L100.3,207.3 L102.8,207.7 L105.2,208.1 L107.7,208.5 L110.1,209.0 L112.5,209.5 L115.0,210.0 L117.5,210.5 L119.9,211.0 L122.3,211.5 L124.8,211.9 L127.2,212.3 L129.7,212.7 L132.2,212.9 L134.6,213.1 L137.1,213.3 L139.5,213.3 L141.9,213.3 L144.4,213.1 L146.8,212.9 L149.3,212.7 L151.8,212.3 L154.2,211.9 L156.7,211.5 L159.1,211.0 L161.6,210.5 L164.0,210.0"/>
    <path d="M246.0,146.0 L248.4,144.3 L250.9,142.6 L253.3,141.0 L255.8,139.5 L258.2,138.2 L260.7,137.1 L263.1,136.2 L265.6,135.5 L268.1,135.1 L270.5,135.0 L272.9,135.1 L275.4,135.5 L277.9,136.2 L280.3,137.1 L282.8,138.2 L285.2,139.5 L287.6,141.0 L290.1,142.6 L292.6,144.3 L295.0,146.0 L297.4,147.7 L299.9,149.4 L302.4,151.0 L304.8,152.5 L307.2,153.8 L309.7,154.9 L312.1,155.8 L314.6,156.5 L317.1,156.9 L319.5,157.0 L321.9,156.9 L324.4,156.5 L326.9,155.8 L329.3,154.9 L331.8,153.8 L334.2,152.5 L336.6,151.0 L339.1,149.4 L341.6,147.7 L344.0,146.0"/>
    <path d="M606.0,66.0 L608.5,62.6 L610.9,59.2 L613.4,56.0 L615.8,53.1 L618.2,50.4 L620.7,48.2 L623.1,46.4 L625.6,45.1 L628.0,44.3 L630.5,44.0 L633.0,44.3 L635.4,45.1 L637.9,46.4 L640.3,48.2 L642.8,50.4 L645.2,53.1 L647.6,56.0 L650.1,59.2 L652.5,62.6 L655.0,66.0 L657.5,69.4 L659.9,72.8 L662.4,76.0 L664.8,78.9 L667.2,81.6 L669.7,83.8 L672.1,85.6 L674.6,86.9 L677.0,87.7 L679.5,88.0 L682.0,87.7 L684.4,86.9 L686.9,85.6 L689.3,83.8 L691.8,81.6 L694.2,78.9 L696.6,76.0 L699.1,72.8 L701.5,69.4 L704.0,66.0" stroke="var(--s1)"/>
  </g>
  <g stroke-width="0.8" opacity="0.5"><line x1="66" y1="210" x2="164" y2="210"/><line x1="246" y1="146" x2="344" y2="146"/><line x1="606" y1="66" x2="704" y2="66"/></g>
  <text x="115" y="180" text-anchor="middle" font-size="10">valley: a mild season</text>
  <text x="295" y="116" text-anchor="middle" font-size="10">slope: half the season</text>
  <text x="655" y="36" text-anchor="middle" font-size="10" fill="var(--s1)">ridge: the sun goes out at midwinter</text>
  <g fill="none" stroke-width="1" marker-end="url(#ah)"><path d="M115,236 L115,246"/><path d="M295,172 L295,182"/><path d="M655,92 L655,150"/></g>
  <text x="124" y="258" font-size="9">the cell</text>
  <text x="640" y="120" font-size="10">one year: 20,000 steps</text>
  <text x="640" y="134" font-size="10">the line is the cell's sun,</text>
  <text x="640" y="148" font-size="10">the mean the same everywhere</text>
  <text x="500" y="230" font-size="10">amplitude of a cell = min(1, a x height / relief)</text>
  <text x="500" y="244" font-size="10">a = 2: dark above the mean height (half the cells)</text>
</svg>
<figcaption>Figure 1. The law. Every cell's sun is a sine of the year (20,000 steps) around the same mean; the amplitude is the cell's, <code>a</code> times its height over the relief and at most 1, so the bottom of the valley has no season and the ridge goes dark at midwinter. Nothing else changes: the rain falls on every cell alike, the soil runs downhill, the store is the body's (e030). With <code>winter flat</code> the amplitude is <code>a</code> on every cell (e031).</figcaption>
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

    def fine_fn(fn, labels=None):
        return [(label, pad(fn(fines[label]), len(fx)), slot[label]) for label in (labels or RUNS) if label in fines and "pop0" in fines[label]]

    def rng(d, k, fmt="{:.2f}"):
        if k not in d:
            return "-"
        return f"{fmt.format(min(d[k]))}-{fmt.format(max(d[k]))}"

    winters_bands = [(15_000 + c * SEASON, 5_000) for c in range(STEPS // SEASON)]
    charts_winter = [
        line_chart("Bodies every 1,000 steps", "All bodies alive (pop.csv). The sun is out on the ridge at 15,000, 35,000, ...; the floor of a dip is what lives through the winter.", fx, fine_series("pop"), ymin=0),
        line_chart("Lineages alive", "Lineages of 5 or more bodies every 1,000 steps. One line at a floor is a lottery.", fx, fine_series("lineages"), ymin=0),
        line_chart("Bodies in the valley, high 2", "Bodies standing in each height band (thirds of the cells), every 1,000 steps, in the pilot at amplitude 2.", fx, [(BAND[b], pad(list(fines[HIGH2][f"pop{b}"]), len(fx)), [2, 3, 1][b]) for b in range(3)] if HIGH2 in fines else [], ymin=0),
        line_chart("The ridge's share of the bodies", "Bodies on the ridge over all bodies, every 1,000 steps. The ridge is a third of the cells; the flat world is not counted by band.", fx, fine_fn(lambda f: band_share(f, 2)), ymin=0, ymax=0.4, percent=True),
    ]
    charts_move = [
        line_chart("Bodies on the ridge born elsewhere", "Of the bodies standing on the ridge, the share born in the valley or on the slope, every 1,000 steps: the ridge's bodies in winter came from below.", fx, fine_fn(lambda f: cross_share(f, 2)), ymin=0, ymax=1, percent=True),
        line_chart("Bodies in the valley born elsewhere", "The same for the valley: the valley's bodies are the valley's own.", fx, fine_fn(lambda f: cross_share(f, 0)), ymin=0, ymax=1, percent=True),
        line_chart("Bodies living on their fat", "Share of the bodies alive at zero energy, every 1,000 steps.", fx, fine_series("on_fat"), ymin=0, ymax=1, percent=True),
        line_chart("Biters", "Share of the bodies that can bite, every 10,000 steps (log).", xs, series(lambda d, i: d["biters_any_share"][i]), ymin=0, percent=True),
    ]

    def summary_row(label):
        d, f = logs[label], fines[label]
        alive = [i for i, p in enumerate(d["pop"]) if p > 0]
        d = {k: [v[i] for i in alive] for k, v in d.items()}
        w = floor_rows(f)
        fmt = lambda k, s: ", ".join(s.format(r[k]) for r in w) if w and r_ok(w, k) else "-"
        return (f"<tr><td>{label}</td><td>{fmt('pop', '{:,}')}</td><td>{fmt('lin', '{}')}</td><td>{fmt('valley', '{:.0%}')}</td><td>{fmt('ridge', '{:,}')}</td><td>{fmt('ridge_cross', '{:.0%}')}</td>"
                f"<td>{min(r['peak'] for r in w):,}-{max(r['peak'] for r in w):,}</td><td>{fmt('peak_ridge', '{:.0%}')}</td><td>{rng(d, 'fat_mean', '{:.0f}')}</td><td>{rng(d, 'biters_any_share', '{:.0%}')}</td><td>{rng(d, 'side_mean', '{:.1f}')}</td><td>{rng(d, 'mass_p50', '{:.0f}')}</td></tr>")

    def r_ok(w, k):
        return not (isinstance(w[0][k], float) and w[0][k] != w[0][k])

    rows = "".join(summary_row(label) for label in RUNS if label in logs)
    tables = data_table(["step", "pop", "births", "deaths_energy", "sun", "fat_mean", "on_fat", "crossers", "biters_any_share", "speed_mean", "side_mean", "mass_p50", "sensor_agents_share", "lineages"],
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
            spans = sorted((int(r[-1]["step"]) - int(r[0]["step"]) + CONFIRM_STEPS for r in by.values()), reverse=True)
            nw, hold, holds = winners(by, first_step=LAST_STEP // 2)
            bsum[(world, sd)] = dict(pop=median(d["pop"][h]), trough=min(r["pop"] for r in w) if w else 0, trough_med=median(r["pop"] for r in w) if w else 0, trough_lin=median(r["lin"] for r in w) if w else 0,
                                     valley=median(r["valley"] for r in w) if w else float("nan"), ridge=median(r["ridge"] for r in w) if w else 0, ridge_cross=median(r["ridge_cross"] for r in w) if w else float("nan"),
                                     peak=median(r["peak"] for r in w) if w else 0, peak_ridge=median(r["peak_ridge"] for r in w) if w else float("nan"),
                                     fat=median(d["fat_mean"][h]), biters=max(d["biters_any_share"][h]), meat=median(d["meat_intake"][i] / (d["meat_intake"][i] + d["plant_intake"][i]) for i in range(n // 2, n)),
                                     side=d["side_mean"][-1], side_std=d["side_std"][-1], p50=median(d["mass_p50"][h]), sensor=max(d["sensor_agents_share"]),
                                     longest=spans[0] if spans else 0, winners=nw, hold=hold, last=int(d["step"][-1]), died=int(d["step"][-1]) < LAST_STEP)
    charts_batch, brows = [], ""
    if have_batch:
        pc = lambda x: "-" if x != x else f"{x:.0%}"
        charts_batch = [
            seeds_chart("Bodies every 1,000 steps, three seeds", "All bodies alive, one line per seed and world. The floors are the winters.", bfine, lambda d, i: d["pop"][i], ymin=0),
            seeds_chart("Lineages alive, three seeds", "Lineages of 5 or more bodies every 1,000 steps, per seed and world.", bfine, lambda d, i: d["lineages"][i], ymin=0),
            seeds_chart("The valley's share of the bodies", "Bodies in the valley over all bodies, every 1,000 steps, per seed and world. The valley is a third of the cells.", bfine, lambda d, i: d["pop0"][i] / d["pop"][i] if d["pop"][i] > 0 else float("nan"), ymin=0, ymax=1, percent=True),
            seeds_chart("Bodies on the ridge born elsewhere", "Of the bodies on the ridge, the share born in another band, every 1,000 steps, per seed and world.", bfine, lambda d, i: d["cross2"][i] / d["pop2"][i] if d["pop2"][i] > 0 else float("nan"), ymin=0, ymax=1, percent=True),
        ]
        brows = "".join((f"<tr><td>{world}, seed {sd}{' (died at ' + format(b['last'], ',') + ')' if b['died'] else ''}</td><td>{b['pop']:,.0f}</td><td>{b['trough']:,}</td><td>{b['trough_med']:,.0f}</td><td>{b['trough_lin']:.0f}</td><td>{pc(b['valley'])}</td><td>{b['ridge']:,.0f}</td><td>{pc(b['ridge_cross'])}</td><td>{b['peak']:,.0f}</td><td>{pc(b['peak_ridge'])}</td>"
                         f"<td>{b['fat']:.0f}</td><td>{b['biters']:.0%}</td><td>{b['meat']:.0%}</td><td>{b['side']:.1f} &plusmn; {b['side_std']:.1f}</td><td>{b['p50']:.0f}</td>"
                         f"<td>{b['sensor']:.0%}</td><td>{b['longest']:,}</td><td>{b['winners']}; {b['hold']:,}</td></tr>")
                        for (world, sd), b in bsum.items())
    TEXT.update(TEXTS)
    TEXT["gallery"] = gallery(GALLERY, GALLERY_CAPTION) if have_batch and GALLERY else ""
    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>e032 A winter that differs by place - Report</title>
<style>{CSS}</style>
</head>
<body>
<main>
<h1>e032: A winter that differs by place</h1>
<p class="sub">Experiment report - 2026-09-05 - the season's amplitude by the cell's height (no season at the bottom of the valley, the sun out at midwinter on the ridge), in e031's world with the store: three pilots on seed 9 at amplitudes 1, 2 and 3, and the batch on seeds 1-3 for 300,000 steps against the flat season at the same world sun.</p>

<section class="tldr">
<h2>TL;DR</h2>
<p>{TEXT["tldr"]}</p>
</section>

<h2>1. Question</h2>
<p>{TEXT["question"]}</p>
<ol>
  <li><strong>The world stands through the dark winter.</strong> With the amplitude by height the floors are in the hundreds with several lineages, where the flat season at amplitude 1 is a lottery of 7-25 bodies.</li>
  <li><strong>The bodies are in the valley at midwinter and on the ridge in summer,</strong> and the ridge's summer bodies come from below: migration as an outcome.</li>
  <li><strong>More than one winner:</strong> the places with different winters hold different bodies.</li>
</ol>

<h2>2. The law</h2>
<p>{TEXT["world"]}</p>
{DIAGRAM}
<p><strong>Runs.</strong> {TEXT["runs"]}</p>
<ul class="measures">
  <li><strong>bodies, lineages</strong> - every 1,000 steps (pop.csv; lineages of 5 or more); the winter floor is the least in each cycle of 20,000.</li>
  <li><strong>bodies per band, born elsewhere</strong> - the bodies standing in the valley, on the slope and on the ridge (thirds of the cells by height), and of those the bodies born in another band.</li>
  <li>fat per body, on their fat, biters, flesh in the intake, side, mass, the longest lineage and the holders of the top place.</li>
</ul>

<h2>3. Results</h2>
<div class="tw"><table>
<thead><tr><th>Seed 9, 100,000 steps (five winters)</th><th>winter floors, in order</th><th>lineages at the floors</th><th>valley share at the floors</th><th>bodies on the ridge at the floors</th><th>of those, born elsewhere</th><th>summer peaks</th><th>ridge share at the peaks</th><th>fat per body</th><th>biters</th><th>side</th><th>mass p50</th></tr></thead>
<tbody>{rows}</tbody></table></div>
<ol class="verdicts">
{TEXT["verdicts"]}
</ol>

<h3>3.1 {TEXT["h_winter"]}</h3>
<div class="grid2">
{"".join(charts_winter)}
</div>
<p>{TEXT["p_winter"]}</p>

<h3>3.2 {TEXT["h_move"]}</h3>
<div class="grid2">
{"".join(charts_move)}
</div>
<p>{TEXT["p_move"]}</p>

<h3>3.3 {TEXT["h_batch"]}</h3>
<div class="tw"><table>
<thead><tr><th>300,000 steps (second half, eight winters)</th><th>bodies</th><th>lowest floor</th><th>median floor</th><th>lineages at the floors</th><th>valley share at the floors</th><th>ridge bodies at the floors</th><th>of those, born elsewhere</th><th>summer peak</th><th>ridge share at the peak</th><th>fat per body</th><th>most biters</th><th>flesh in the intake</th><th>side at the end</th><th>mass p50</th><th>most with a sensor</th><th>longest lineage</th><th>winners; longest hold</th></tr></thead>
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
<p>Every log step of the pilot runs; the full data is in <code>results/*.csv</code> and <code>../e031_breed/results/</code>. Build this report with <code>uv run python experiments/e032_winter/report.py</code>.</p>
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


TEXTS = {
    "tldr": ("The season's amplitude by height (no season at the bottom of the valley, the sun out at midwinter above the mean height) makes the dark winter a place, and the world stands: floors of 673-1,230 bodies with 2-10 lineages at amplitude 2, "
             "364-476 at 3, where the flat season at 1 is a lottery of 8-22. The valley holds 68-90% of the bodies at every floor, the ridge's winter bodies are 58-100% born below, and the ridge is refilled every summer: migration as an outcome. "
             "In one seed of three the crowd in the valley brings the tooth back (24-37% biters) and two kinds of body live 260,000 steps together. Kept: the season world is winter high at 2 from here."),
    "question": ("The season at amplitude 1 is a lottery of 7-25 bodies each winter with a store (e030), and no law of the body lifts it (e031): the world's matter cannot carry its bodies through 3,000 dark steps. "
                 "The real world's dark winters are somewhere: the higher a place, the harsher its winter, and the animals leave it. Every season so far was the same on every cell, so leaving had nowhere to go. This experiment writes the winter as a law of the place and asks:"),
    "world": ("e031's world (the store at 5, the grid's side heritable, breeding at the threshold) with the season's amplitude a cell's: a times its height over the relief, at most 1. On this terrain (heights 0-72, mean 32, relief 64) amplitude 2 darkens the 44% of the cells above the mean height at midwinter and leaves the world a quarter of its sun, "
              "the flat season's at 0.75; amplitude 3 darkens 72%. The mean sun over a year is the same on every cell."),
    "runs": ("Three pilots on seed 9 at amplitudes 1, 2 and 3 (100,000 steps, 12 minutes), against e031's flat season at 1. Then the batch: high 2 and high 3 on seeds 1-3 for 300,000 steps against the flat season at 0.75, the same world sun at midwinter (nine runs at one thread, 60 minutes). Measures:"),
    "verdicts": ("<li><span class=\"verdict\">Yes</span> Floors 673-1,230 at 2 and 364-476 at 3, with 2-10 lineages; flat 1: 8-22 with 0-2. The pilot at 3 holds 296-310 in every winter: a place's capacity, not a lottery.</li>"
                 "<li><span class=\"verdict\">Yes</span> The valley holds 68-90% of the floor's bodies, the ridge 17-124 of which 58-100% were born below; every summer the ridge is refilled to 16-24% of the peak.</li>"
                 "<li><span class=\"verdict partly\">One seed of three</span> A flesh column with a tooth and a light gut, 260,000 steps together, biters 24-37% of the world; elsewhere e030's two bodies, spread over every band.</li>"),
    "h_winter": "The dark winter is a place, and the world lives in the valley",
    "p_winter": ("At amplitude 1 the ridge's mean amplitude is 0.8 and the world barely notices (floors 1,666-2,216). At 2 the floors are 542-825 in the pilot and 673-1,230 in the batch, at 3 296-310 and 364-476: the valley's bodies at midwinter are what the valley's sun feeds, "
                 "and the count returns within 5% every winter. The flat season at the same world sun (0.75) holds 779-1,351 with 6-22 lineages over every band; the winter by height holds as many in a third of the space with fewer lineages."),
    "h_move": "The bodies leave the ridge in autumn and come back in summer",
    "p_move": ("The ridge's bodies at midwinter (17-124) are 58-100% born in the valley or on the slope; its summer bodies are 75-80% its own. In the flat world 34-50% of the ridge's bodies are born elsewhere at every season. "
               "The wave is the whole world's: at the equinox every large lineage stands in all three bands, no lineage is a place's. The ridge's bodies carry more hard and muscle than the valley's in three runs of six (high 2 seed 3: hard 7.5 against 3.6, biters 29% against 14%)."),
    "h_batch": "Three seeds: the same floors, and the tooth back in one",
    "p_batch": ("In high 2 seed 1 the bodies that can bite are 24-37% of the world through the second half (the flat world 0-3%, e030 and e031 under grow: none): a column of muscle and gut at density 2 eating 47-54% flesh held the top place from 40,000 to the end in three kin lineages, "
                "beside a light gut wedge (13-16% flesh) alive 277,000 steps. High 2 seed 3 is held all 300,000 steps by a bar of 15-17 guts with hard blocks in a third of its members; the other seeds are e030's light gut and dense block."),
    "discussion": ("<p>The winter's arithmetic did not change: the world's matter and the sun over a year are e031's. What changed is where the dark is. A body in the valley at midwinter has a sun of 0.55-1 and lives; a body on the ridge has none and dies or walks downhill after the food it sees. "
                   "The floor is the valley's capacity, so it is the same every winter, and the crowd it makes (two thirds of the bodies in a third of the cells) is the first crowd since e025: in one seed the tooth pays there, at 24-37% of the bodies for 150,000 steps.</p>"
                   "<p>No body holds the ridge through the winter and no lineage belongs to a place, because the valley is the best place at every season but the summer: the ridge has nothing the valley lacks. That is the next law's work, not this one's: e020's rain on the mountains (the soil is on the ridge, the winter sun in the valley) makes the two places a trade-off.</p>"),
    "conclusion": ("Kept: the season world is winter high at amplitude 2 from here (the argument's default stays flat, e031 byte for byte). The dark winter is somewhere, the bodies leave it, and the crowd it makes brought the tooth back once. "
                   "Next: the rain on the mountains under this winter (rain high, already an argument), so that the wet ground is where the sun goes out, and a body that carries its store uphill in spring is an outcome to watch for."),
}
_h2 = lambda sd: (f"high 2, seed {sd}", HERE, f"{base(2, HIGH)}_seed{sd}")
_h3 = lambda sd: (f"high 3, seed {sd}", HERE, f"{base(3, HIGH)}_seed{sd}")
GALLERY = [
    (*_h2(1), 2807, "The flesh column", "Muscle over gut in one column at density 2, mass 14: the third kin lineage of the column that held seed 1 from 40,000 to the end, 54% flesh in its intake, a third of its members with a hard block."),
    (*_h2(1), 407, "The light gut wedge", "Six guts at density 1.1, mass 7: the sitting gut that lived 277,000 steps beside the column, 16% flesh."),
    (*_h2(3), 1, "The bar of guts", "Two rows of guts at density 0.8, mass 22: the start's lineage, alive all 300,000 steps of seed 3; a third of its members carry hard blocks."),
    (*_h3(3), 1623, "The dense block with a tooth", "Muscle and gut filling a 4x4 grid at density 2, mass 28, one hard block at the front: e030's block, 128,000 steps at amplitude 3."),
]
GALLERY_CAPTION = "Figure 2. Bodies of lineages that prospered: the most common grown body of the lineage at its peak, on the grid it grew on, front up (the dashed edge). Blue: hard, orange: muscle, green: digestive, yellow: sensor."


if __name__ == "__main__":
    main()
