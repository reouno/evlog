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

def base(rain, amp, winter):
    return f"128_sigma0_r64_f0.1_{rain}_eyes8_flesh1_w1_season{amp}_digest0_sidegrow_store5_yolk0_breed0{winter}"

HIGH = "_winterhigh"
E032 = os.path.join(HERE, "..", "e032_winter")
# The pilots on seed 9: label -> (folder, run prefix, color slot). The controls are the rain on every cell alike (e032's pilot, and its flat 0.75 world rerun with this code).
RUNS = {
    "rain high, winter high 2": (HERE, f"{base('high', 2, HIGH)}_seed9", 0),
    "rain flat, winter high 2 (e032)": (E032, f"{base('flat', 2, HIGH)}_seed9", 1),
    "rain high, flat 0.75": (HERE, f"{base('high', 0.75, '')}_seed9", 2),
    "rain flat, flat 0.75": (HERE, f"{base('flat', 0.75, '')}_seed9", 3),
}
WET, DRY, WET_FLAT, DRY_FLAT = list(RUNS)
STEPS = 100_000
BATCH = {}
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
<svg viewBox="0 0 820 300" width="100%" role="img" aria-label="The wet ridge under the winter by height" font-size="12" fill="currentColor" stroke="currentColor">
  <defs><marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0,0 L10,5 L0,10 z" stroke="none" fill="currentColor"/></marker></defs>
  <path d="M20,250 C120,250 180,240 240,200 C300,160 340,110 400,90 C460,70 520,120 580,150 C640,180 700,190 800,190" fill="none" stroke-width="2"/>
  <line x1="20" y1="250" x2="800" y2="250" stroke-width="1" stroke-dasharray="3 3" opacity="0.5"/>
  <g stroke="var(--s1)" stroke-width="1.5" opacity="0.9"><line x1="330" y1="14" x2="327" y2="26"/><line x1="330" y1="36" x2="327" y2="48"/><line x1="348" y1="14" x2="345" y2="26"/><line x1="348" y1="36" x2="345" y2="48"/><line x1="366" y1="14" x2="363" y2="26"/><line x1="366" y1="36" x2="363" y2="48"/><line x1="384" y1="14" x2="381" y2="26"/><line x1="384" y1="36" x2="381" y2="48"/><line x1="402" y1="14" x2="399" y2="26"/><line x1="402" y1="36" x2="399" y2="48"/><line x1="420" y1="14" x2="417" y2="26"/><line x1="420" y1="36" x2="417" y2="48"/><line x1="438" y1="14" x2="435" y2="26"/><line x1="438" y1="36" x2="435" y2="48"/><line x1="456" y1="14" x2="453" y2="26"/><line x1="456" y1="36" x2="453" y2="48"/><line x1="474" y1="14" x2="471" y2="26"/><line x1="474" y1="36" x2="471" y2="48"/></g>
  <text x="405" y="62" text-anchor="middle" font-size="10" fill="var(--s1)">the rain: most on the ridge, none at the bottom</text>
  <g fill="none" stroke-width="1.2">
    <rect x="60" y="184" width="110" height="52" rx="4"/>
    <rect x="600" y="40" width="110" height="52" rx="4"/>
  </g>
  <g fill="none" stroke-width="1.5">
    <path d="M66.0,210.0 L68.5,209.5 L70.9,209.0 L73.3,208.5 L75.8,208.1 L78.2,207.7 L80.7,207.3 L83.2,207.1 L85.6,206.9 L88.0,206.7 L90.5,206.7 L93.0,206.7 L95.4,206.9 L97.8,207.1 L100.3,207.3 L102.8,207.7 L105.2,208.1 L107.7,208.5 L110.1,209.0 L112.5,209.5 L115.0,210.0 L117.5,210.5 L119.9,211.0 L122.3,211.5 L124.8,211.9 L127.2,212.3 L129.7,212.7 L132.2,212.9 L134.6,213.1 L137.1,213.3 L139.5,213.3 L141.9,213.3 L144.4,213.1 L146.8,212.9 L149.3,212.7 L151.8,212.3 L154.2,211.9 L156.7,211.5 L159.1,211.0 L161.6,210.5 L164.0,210.0"/>
    <path d="M606.0,66.0 L608.5,62.6 L610.9,59.2 L613.4,56.0 L615.8,53.1 L618.2,50.4 L620.7,48.2 L623.1,46.4 L625.6,45.1 L628.0,44.3 L630.5,44.0 L633.0,44.3 L635.4,45.1 L637.9,46.4 L640.3,48.2 L642.8,50.4 L645.2,53.1 L647.6,56.0 L650.1,59.2 L652.5,62.6 L655.0,66.0 L657.5,69.4 L659.9,72.8 L662.4,76.0 L664.8,78.9 L667.2,81.6 L669.7,83.8 L672.1,85.6 L674.6,86.9 L677.0,87.7 L679.5,88.0 L682.0,87.7 L684.4,86.9 L686.9,85.6 L689.3,83.8 L691.8,81.6 L694.2,78.9 L696.6,76.0 L699.1,72.8 L701.5,69.4 L704.0,66.0"/>
  </g>
  <g stroke-width="0.8" opacity="0.5"><line x1="66" y1="210" x2="164" y2="210"/><line x1="606" y1="66" x2="704" y2="66"/></g>
  <text x="115" y="180" text-anchor="middle" font-size="10">valley: the winter sun, no rain</text>
  <text x="655" y="36" text-anchor="middle" font-size="10">ridge: the rain, no winter sun</text>
  <g fill="none" stroke-width="1" marker-end="url(#ah)"><path d="M115,236 L115,246"/><path d="M655,92 L655,150"/></g>
  <g fill="none" stroke-width="1.2" stroke-dasharray="4 3" marker-end="url(#ah)"><path d="M380,105 C330,135 280,170 235,215"/><path d="M430,95 C500,125 560,160 610,180"/></g>
  <text x="290" y="120" font-size="10">the soil runs downhill (flow 0.1)</text>
  <text x="500" y="230" font-size="10">the sun's amplitude = min(1, 2 x height / relief) (e032)</text>
  <text x="500" y="244" font-size="10">the rain's cap = 0.01 x height / relief (e020)</text>
  <text x="24" y="268" font-size="10">height 0 (the bottom of the valley)</text>
</svg>
<figcaption>Figure 1. Two laws already in the code, together for the first time. e032's winter: every cell's sun is a sine of the year around the same mean, with the amplitude by height (none at the bottom, the sun out at midwinter above the mean height). e020's rain: what the bodies breathe rains back by height (the most on the ridge, none at the bottom of the valley) and the soil runs downhill. The ridge has the rain and loses the winter sun; the valley has the winter sun and gets its soil only from above.</figcaption>
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
        line_chart("Bodies every 1,000 steps", "All bodies alive (pop.csv). The floor of a dip is what lives through the winter.", fx, fine_series("pop"), ymin=0),
        line_chart("The valley's share of the bodies", "Bodies in the valley over all bodies, every 1,000 steps. The valley is a third of the cells.", fx, fine_fn(lambda f: band_share(f, 0)), ymin=0, ymax=1, percent=True),
        line_chart("Bodies on the ridge born elsewhere", "Of the bodies on the ridge, the share born in the valley or on the slope, every 1,000 steps.", fx, fine_fn(lambda f: cross_share(f, 2)), ymin=0, ymax=1, percent=True),
        line_chart("Soil on the ridge", "Soil in the ridge's cells every 1,000 steps (this code's pop.csv; e032's pilot has no soil column). The lake in the valley is 70,000-100,000 in every run.", fx, fine_fn(lambda f: list(f["soil2"]), need="soil2"), ymin=0),
    ]

    def summary_row(label):
        d, f = logs[label], fines[label]
        alive = [i for i, p in enumerate(d["pop"]) if p > 0]
        d = {k: [v[i] for i in alive] for k, v in d.items()}
        w = floor_rows(f)
        fmt = lambda k, s: ", ".join(s.format(r[k]) for r in w)
        return (f"<tr><td>{label}</td><td>{fmt('pop', '{:,}')}</td><td>{fmt('lin', '{}')}</td><td>{fmt('valley', '{:.0%}')}</td><td>{fmt('ridge', '{:,}')}</td><td>{fmt('ridge_cross', '{:.0%}')}</td>"
                f"<td>{min(r['peak'] for r in w):,}-{max(r['peak'] for r in w):,}</td><td>{fmt('peak_ridge', '{:.0%}')}</td><td>{rng(d, 'biters_any_share', '{:.0%}')}</td><td>{rng(d, 'side_mean', '{:.1f}')}</td><td>{rng(d, 'mass_p50', '{:.0f}')}</td></tr>")

    rows = "".join(summary_row(label) for label in RUNS if label in logs)

    def band_rows(label):
        folder, run, _ = RUNS[label]
        pl = [r for r in load_rows(f"results/{run}_places.csv", folder) if int(r["step"]) >= STEPS // 2]
        out = ""
        for p in "012":
            rr = [r for r in pl if r["place"] == p]
            m = lambda k, s: s.format(median(float(r[k]) for r in rr))
            out += (f"<tr><td>{label if p == '0' else ''}</td><td>{BAND[int(p)]}</td><td>{m('soil', '{:,.0f}')}</td><td>{m('barren', '{:.1f}')}</td><td>{m('rain', '{:.1f}')}</td><td>{m('regrowth', '{:.1f}')}</td>"
                    f"<td>{min(int(r['pop']) for r in rr):,}-{max(int(r['pop']) for r in rr):,}</td><td>{m('mass', '{:.0f}')}</td><td>{m('muscle', '{:.1f}')}</td><td>{m('hard', '{:.1f}')}</td></tr>")
        return out

    brows = "".join(band_rows(label) for label in RUNS if label in logs)
    tables = data_table(["step", "pop", "births", "deaths_energy", "rain", "air", "soil", "barren", "fat_mean", "crossers", "biters_any_share", "side_mean", "mass_p50", "sensor_agents_share", "lineages"],
                        {f"{label}, seed 9": d for label, d in logs.items()}, every=1)
    TEXT.update(TEXTS)
    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>e033 The wet ridge - Report</title>
<style>{CSS}</style>
</head>
<body>
<main>
<h1>e033: The wet ridge</h1>
<p class="sub">Experiment report - 2026-09-05 - e020's rain on the mountains under e032's winter by height: two pilots on seed 9 (with the winter by height at 2, and with the flat winter at 0.75) against the rain on every cell alike. No batch: the pilots settle the mechanism.</p>

<section class="tldr">
<h2>TL;DR</h2>
<p>{TEXT["tldr"]}</p>
</section>

<h2>1. Question</h2>
<p>{TEXT["question"]}</p>
<ol>
  <li><strong>The ridge is worth holding:</strong> its share of the summer's bodies rises over e032's 16-24%, and more of them are born there.</li>
  <li><strong>The winter empties it less:</strong> more bodies on the ridge at midwinter than e032's 17-124, and the valley's share below 68-90%.</li>
  <li><strong>Two places, two winners:</strong> the ridge's bodies and the valley's differ more than in e032.</li>
  <li><strong>The world stands</strong> at e032's floors or above.</li>
</ol>

<h2>2. The laws</h2>
<p>{TEXT["world"]}</p>
{DIAGRAM}
<p><strong>Runs.</strong> {TEXT["runs"]}</p>
<ul class="measures">
  <li><strong>bodies, per band, born elsewhere</strong> - every 1,000 steps (pop.csv), and the soil per band.</li>
  <li><strong>soil, barren, rain, regrowth per band</strong> - at the equinoxes (places.csv): the soil standing in a band, the sun lost there for want of soil, the rain fallen and the plant grown per step.</li>
</ul>

<h2>3. Results</h2>
<div class="tw"><table>
<thead><tr><th>Seed 9, 100,000 steps (five winters)</th><th>winter floors, in order</th><th>lineages at the floors</th><th>valley share at the floors</th><th>bodies on the ridge at the floors</th><th>of those, born elsewhere</th><th>summer peaks</th><th>ridge share at the peaks</th><th>biters</th><th>side</th><th>mass p50</th></tr></thead>
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
<div class="tw"><table>
<thead><tr><th>Second half, at the equinoxes (median)</th><th>band</th><th>soil</th><th>barren (sun lost per step)</th><th>rain per step</th><th>regrowth per step</th><th>bodies</th><th>mass</th><th>muscle</th><th>hard</th></tr></thead>
<tbody>{brows}</tbody></table></div>
<p>{TEXT["p_soil"]}</p>

<h2>4. Discussion</h2>
{TEXT["discussion"]}

<h2>5. Conclusion and next step</h2>
<p>{TEXT["conclusion"]}</p>

<h2>Appendix: data</h2>
<p>Every log step of the pilot runs; the full data is in <code>results/*.csv</code> and <code>../e032_winter/results/</code>. Build this report with <code>uv run python experiments/e033_wetridge/report.py</code>.</p>
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
    "tldr": ("e020's rain on the mountains under e032's winter by height changes nothing the bodies notice: floors 553-764 against 542-825, the valley 70-79% of them against 73-85%, the ridge's winter bodies 82-95% born below against 80-92%, the ridge's summer share 17-20% against 17-19%. "
             "The ridge gets 25 of rain a step instead of 16 and holds six times the soil, and loses the same sun for want of it (27 a step, half its sun): the soil runs downhill ten times faster than the plant grows, so the rain's place is not the soil's place. Not kept; no batch."),
    "question": ("e032 made the winter a place, and the valley the refuge; no body holds the ridge through the winter, because the ridge has nothing the valley lacks. e020's rain on the mountains (the air rains on a cell by its height, the soil runs downhill) turned e019's world upside down, the ridges holding 45% of the bodies. "
                 "Under the winter by height the two laws make the places a trade-off: the rain where the sun goes out, the winter sun where no rain falls. No law is new; the question is what the bodies do with two places that each lack something."),
    "world": ("e032's world (the store, the grid's side heritable, the winter by height at amplitude 2) with rain high: the most the air can rain on a cell per step is 0.01 times its height over the relief, none at the bottom of the valley; the soil runs a tenth of the drop downhill per step (flow 0.1) as in every world since e019. "
              "rain flat winter high is e032 byte for byte."),
    "runs": ("Two pilots on seed 9, 100,000 steps (12 minutes): rain high with the winter by height at 2, and rain high with the flat winter at 0.75 (the rain alone). Controls: e032's pilot (rain flat, winter high 2) and rain flat at flat 0.75 run with this code. Measures:"),
    "verdicts": ("<li><span class=\"verdict no\">No</span> The ridge's summer share is 17-20% against 17-19%, its summer bodies 79-84% its own against 78-83%.</li>"
                 "<li><span class=\"verdict no\">No</span> 36-84 bodies on the ridge at midwinter against 13-56, born below in the same share; the valley 70-79% against 73-85%.</li>"
                 "<li><span class=\"verdict no\">No</span> The bands hold the same body in every run (mass 17-22, muscle 4-6, no hard).</li>"
                 "<li><span class=\"verdict\">Yes</span> Floors 553-764; under the flat winter 1,131-1,327 against 1,195-1,280.</li>"),
    "h_winter": "The bodies do not notice where the rain falls",
    "p_winter": ("Under the winter by height the floors, the valley's share and the ridge's refilling are e032's line for line; under the flat winter the valley holds a third at every floor in both rains. The soil on the ridge is a few thousand in the wet world and a few hundred in the dry one, against a lake of 70,000-100,000 in the valley in every run."),
    "h_soil": "The ridge's rain runs off before the plant can use it",
    "p_soil": ("The ridge gets 25 of rain a step instead of 16 and holds 2,270 of soil instead of 360, and loses the same sun for want of soil: 27.2 a step against 27.6, half of the ridge's sun. The soil moves a tenth of the drop per step where the plant grows a hundredth per cell per step: what falls on the ridge is in the valley within a few steps. "
               "The regrowth per band is the same in both rains (3.0, 4.4, 8-10): the ridge grows more per step because the crowd's bodies shade the valley's cells, not because of its soil."),
    "discussion": ("<p>e020's world was upside down under this rain because its lake drained into the air and the rain's caps set where the world's flux fell; with the canopy, the spill and the store the air holds 50-70 and the lake stands in the valley, where the flow puts it whatever the sky does. The rain is a place's only if the soil stays: "
                   "on this terrain the flow is ten times the growth, so the rain's place and the soil's place are different places, and the bodies live where the soil is.</p>"
                   "<p>The ridge will be worth something when it holds what the valley cannot use: soil that a standing plant keeps (roots: a wood holds its ground), a slower flow, or a store in the ground that stands through the dark. Each is a law about the soil, not the sky.</p>"),
    "conclusion": ("Not kept: the rain stays on every cell alike. The pilot settles the mechanism (the soil and the barren sun per band are the same in both rains), so no batch was run. Next: the soil's side of the same premise, a store in the ground that stands through the dark, or soil that a standing plant holds."),
}


if __name__ == "__main__":
    main()
