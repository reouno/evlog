#!/usr/bin/env python3
"""Build report.html for this experiment.

Charts: matplotlib, exported as SVG and inlined. Diagram: hand-written SVG.
Run from the repo root: uv run python experiments/e028_gut/report.py
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
DIGEST_FLOOR = 0.5

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

BASE = "128_sigma0_r64_f0.1_flat_eyes8_flesh1_w1_season0.5"
# The runs: label -> (folder, run prefix, color slot). The control is e026's season pilot, this code with digest 0.
RUNS = {
    "e026 (control)": (E026, f"{BASE}_seed9", 1),
    "the line (digest 1)": (HERE, f"{BASE}_digest1_seed9", 0),
    "the sharp curve (digest 2)": (HERE, f"{BASE}_digest2_seed9", 2),
}
CONTROL, LINE, SHARP = list(RUNS)
STEPS = 100_000
# The batch: the sharp curve on seeds 1-4, 500,000 steps, against e026's season runs (this code with digest 0).
BATCH = {
    "the sharp curve": (HERE, f"{BASE}_digest2", 2),
    "e026 (control)": (E026, BASE, 1),
}
B_SHARP, B_CONTROL = list(BATCH)
SEEDS = [1, 2, 3, 4]
LAST_STEP = 500_000
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
            out[d["id"]] = d["cells"]
    return out


def read_frames(path, folder=HERE):
    with open(os.path.join(folder, path)) as f:
        for line in f:
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                return


def yields(d, law):
    k = 1 - DIGEST_FLOOR
    if law == 1:
        return 1 - k * d, 1 - k * (1 - d)
    return 1 - k * math.sqrt(d), 1 - k * math.sqrt(1 - d)


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
    top = max(v for _, ys, _ in series for v in ys)
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
        ax.scatter(xs, ys, s=sizes, color=SERIES[slot], alpha=0.6, label=label, linewidths=0)
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


def timeline_chart(title, subtitle, by, color_key="digest"):
    """Every lineage as a band: bodies over time, colored by the lineage's axis (yellow: plant side, orange: flesh side)."""
    fig, ax = new_axes(size=(13, 3.2))
    ax.set_ylabel("bodies in the lineage")
    cmap = matplotlib.colormaps["viridis"]
    for lid, rows in by.items():
        xs = [int(r["step"]) for r in rows]
        ys = [int(r["size"]) for r in rows]
        d = median(float(r[color_key]) for r in rows)
        c = cmap(d)
        ax.fill_between(xs, 0, ys, color=c, alpha=0.35, linewidth=0)
        ax.plot(xs, ys, color=c, linewidth=0.9)
    ax.set_ylim(0, None)
    ax.yaxis.set_major_locator(MaxNLocator(4))
    ax.yaxis.set_major_formatter(kfmt)
    sm = matplotlib.cm.ScalarMappable(cmap=cmap, norm=matplotlib.colors.Normalize(0, 1))
    cb = fig.colorbar(sm, ax=ax, pad=0.01, fraction=0.03)
    cb.set_label("d")
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
    peak (or at the step given), on the 8x8 grid, front up."""
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
        c = Counter(a[2] for a in frame["agents"] if a[4] == lid)
        cells = bodies[c.most_common(1)[0][0]]
        rects = "".join(f'<rect x="{(i % 8) * 11}" y="{(i // 8) * 11}" width="10" height="10" fill="{KIND_COLOR[int(k)]}"/>' for i, k in enumerate(cells) if k != "0")
        m, pl = float(peak["meat"]), float(peak["plant"])
        meat = m / (m + pl) if m + pl > 0 else 0
        cards.append(f"""<figure class="card"><svg viewBox="-1 -1 89 89" width="120" height="120" role="img" aria-label="{html.escape(name)}"><rect x="-1" y="-1" width="89" height="89" fill="var(--cell)"/>{rects}<line x1="-1" y1="-0.5" x2="88" y2="-0.5" stroke="var(--ink2)" stroke-width="1.5" stroke-dasharray="3 2"/></svg>
<figcaption><strong>{html.escape(name)}</strong><br>{html.escape(label)}, lineage {lid}: {span:,} steps, {int(peak["size"]):,} agents at {"step " + format(int(peak["step"]), ",") if at else "its peak"}<br>digest {float(peak["digest"]):.2f}, density {float(peak["density"]):.2f}; mass {float(peak["mass"]):.0f} on {float(peak["foot"]):.1f} cells: hard {float(peak["hard"]):.0f}, muscle {float(peak["muscle"]):.0f}, sensor {float(peak["sensor"]):.1f}, digestive {float(peak["digestive"]):.0f}; flesh {meat:.0%} of the intake<br>{html.escape(what)}</figcaption></figure>""")
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
<figure class="diagram">
<svg viewBox="0 0 900 250" role="img" aria-label="A gut block takes 0.02 a step from the cell under it, plant and flesh alike. The genome expresses a digestion axis d from 0 to 1. The gut digests plant at 1 minus d over 2 and flesh at one half plus d over 2; what it does not digest is dung, which goes to the soil of the cell. In the season world 70 percent of the intake is flesh: the dead lie where the bodies are." style="max-width:100%;height:auto;display:block">
<defs><marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="currentColor"/></marker></defs>
<g fill="none" stroke="currentColor" stroke-width="1.2" font-size="12" font-family="system-ui, sans-serif">
  <!-- the cell -->
  <rect x="30" y="60" width="150" height="130" rx="4"/>
  <text x="105" y="82" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">the cell under the gut</text>
  <text x="105" y="104" text-anchor="middle" fill="currentColor" stroke="none">plant and fruit</text>
  <text x="105" y="126" text-anchor="middle" fill="currentColor" stroke="none">dead matter (flesh)</text>
  <text x="105" y="148" text-anchor="middle" fill="currentColor" stroke="none">soil</text>
  <text x="105" y="176" text-anchor="middle" fill="currentColor" stroke="none">a broken cell of a body: flesh</text>
  <!-- the gut -->
  <rect x="330" y="60" width="200" height="130" rx="4" stroke="var(--s1)" stroke-width="2"/>
  <text x="430" y="82" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">the gut, axis d in [0, 1]</text>
  <text x="430" y="104" text-anchor="middle" fill="currentColor" stroke="none">expressed by the genome,</text>
  <text x="430" y="122" text-anchor="middle" fill="currentColor" stroke="none">inherited, mutates</text>
  <text x="430" y="150" text-anchor="middle" fill="currentColor" stroke="none">plant yield 1 - d / 2</text>
  <text x="430" y="168" text-anchor="middle" fill="currentColor" stroke="none">flesh yield 1/2 + d / 2</text>
  <!-- the body -->
  <rect x="690" y="60" width="180" height="70" rx="4"/>
  <text x="780" y="84" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">the body's energy</text>
  <text x="780" y="106" text-anchor="middle" fill="currentColor" stroke="none">upkeep, children, fat</text>
  <!-- arrows -->
  <line x1="180" y1="110" x2="328" y2="110" marker-end="url(#arr)"/>
  <text x="254" y="100" text-anchor="middle" fill="currentColor" stroke="none">takes 0.02 a step, in</text>
  <text x="254" y="126" text-anchor="middle" fill="currentColor" stroke="none">the cell's proportions</text>
  <line x1="530" y1="95" x2="688" y2="95" marker-end="url(#arr)"/>
  <text x="609" y="85" text-anchor="middle" fill="currentColor" stroke="none">digested</text>
  <path d="M430,190 L430,225 L105,225 L105,192" marker-end="url(#arr)"/>
  <text x="268" y="215" text-anchor="middle" fill="currentColor" stroke="none">the rest is dung: to the soil of the cell (the ledger holds)</text>
  <!-- the world's flesh -->
  <text x="780" y="165" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">where the flesh comes from</text>
  <text x="780" y="185" text-anchor="middle" fill="currentColor" stroke="none">the world eats its dead (e024):</text>
  <text x="780" y="203" text-anchor="middle" fill="currentColor" stroke="none">70% of the intake is dead matter,</text>
  <text x="780" y="221" text-anchor="middle" fill="currentColor" stroke="none">lying where the bodies are</text>
</g>
</svg>
<figcaption>Figure 1. The digestion law. A gut still takes what lies under it; the axis decides how much of each food becomes energy. The line (digest 1) gives the middle three quarters of both; the sharp curve (digest 2) gives it 0.65 of both, so a gut for both is worse than the mean of the two guts. No body chooses its food: it eats where it stands.</figcaption>
</figure>
"""


def tradeoff_chart():
    xs = [i / 100 for i in range(101)]
    fig, ax = new_axes("d, the digestion axis", size=(6.4, 2.6))
    ax.margins(x=0.02)
    for law, name, style in [(1, "the line", "-"), (2, "the sharp curve", "--")]:
        ax.plot(xs, [yields(d, law)[0] for d in xs], color=SERIES[3], linestyle=style, linewidth=1.6, label=f"plant, {name}")
        ax.plot(xs, [yields(d, law)[1] for d in xs], color=SERIES[1], linestyle=style, linewidth=1.6, label=f"flesh, {name}")
    ax.set_ylim(0, 1.1)
    ax.yaxis.set_major_locator(MaxNLocator(4))
    legend_above(ax, 2)
    return figure("What a gut digests, by its axis", "The share of a unit of plant (yellow) and of flesh (orange) that becomes energy. Solid: the line; dashed: the sharp curve. The ends are the same; the curves differ in the middle.", to_svg(fig))


TEXT = {}  # filled in main(); counted at the end


def main():
    logs = {label: {k: v[:STEPS // 10_000] for k, v in load_csv(f"results/{run}_log.csv", folder).items()} for label, (folder, run, _) in RUNS.items()}
    lineages = {label: lineage_rows(run, folder) for label, (folder, run, _) in RUNS.items()}
    xs = logs[CONTROL]["step"]
    slot = {label: s for label, (_, _, s) in RUNS.items()}

    def series(f, labels=None):
        return [(label, [f(logs[label], i) for i in range(len(logs[label]["step"]))], slot[label]) for label in (labels or RUNS)]

    per_step = lambda d, k, i: d[k][i] / 10_000
    charts_axis = [
        line_chart("The axis over the bodies", "Mean of d over the bodies alive, with one standard deviation shaded. A neutral axis stays near 0.5 with a narrow band; selection moves the mean or widens the band.", xs,
                   series(lambda d, i: d["digest_mean"][i], [LINE, SHARP]), ymin=0, ymax=1,
                   bands=[([m - s for m, s in zip(logs[l]["digest_mean"], logs[l]["digest_std"])], [m + s for m, s in zip(logs[l]["digest_mean"], logs[l]["digest_std"])], slot[l]) for l in [LINE, SHARP]]),
    ]
    charts_world = [
        line_chart("Bodies", "Bodies alive at each log step. The law costs the world what the guts do not digest.", xs, series(lambda d, i: d["pop"][i]), ymin=0),
        line_chart("Flesh in the intake", "The share of what the bodies digested that was flesh (dead matter and broken cells). The control's world eats its dead.", xs,
                   series(lambda d, i: d["meat_intake"][i] / max(d["meat_intake"][i] + d["plant_intake"][i], 1e-9)), ymin=0, ymax=1, percent=True),
    ]
    # Lineages: d against the flesh share of the lineage's intake, one point per lineage row (every 1,000 steps), sized by bodies.
    def lineage_points(label):
        pts = []
        for rows in lineages[label].values():
            for r in rows:
                m, p = float(r["meat"]), float(r["plant"])
                if m + p > 0:
                    pts.append((float(r["digest"]), m / (m + p), int(r["size"])))
        return pts
    scat = []
    for label in [LINE, SHARP]:
        pts = lineage_points(label)
        scat.append((label, [x for x, _, _ in pts], [y for _, y, _ in pts], [max(n / 40, 2) for _, _, n in pts], slot[label]))
    charts_lineages = [
        scatter_chart("Lineages: the axis against the diet", "One point per lineage and log step, sized by bodies. A flesh gut (d near 1) that eats mostly flesh would sit top right; a plant gut bottom left.", scat, "d, the digestion axis", "flesh share of the intake"),
    ]

    def rng(d, k, f=lambda v: v, fmt="{:.2f}"):
        if k not in d:
            return "-"
        vals = [f(v) for v in d[k]]
        return f"{fmt.format(min(vals))}-{fmt.format(max(vals))}"

    def summary_row(label):
        d = logs[label]
        meat = [m / max(m + p, 1e-9) for m, p in zip(d["meat_intake"], d["plant_intake"])]
        intake = [(m + p) / 1e4 for m, p in zip(d["meat_intake"], d["plant_intake"])]
        kills = [k / 1e4 for k in d["deaths_broken"]]
        by = lineages[label]
        spans = sorted((int(r[-1]["step"]) - int(r[0]["step"]) + CONFIRM_STEPS for r in by.values()), reverse=True)
        return (f"<tr><td>{label}</td><td>{rng(d, 'pop', fmt='{:,.0f}')}</td><td>{min(intake):.0f}-{max(intake):.0f}</td><td>{min(meat):.0%}-{max(meat):.0%}</td>"
                f"<td>{rng(d, 'dung', fmt='{:.0f}')}</td><td>{rng(d, 'digest_mean')}</td><td>{rng(d, 'digest_std')}</td>"
                f"<td>{rng(d, 'flesh_guts', fmt='{:.0%}')}</td><td>{min(kills):.2f}-{max(kills):.2f}</td><td>{rng(d, 'biters_share', fmt='{:.1%}')}</td><td>{rng(d, 'lineages', fmt='{:.0f}')}</td><td>{spans[0]:,}</td></tr>")

    rows = "".join(summary_row(label) for label in RUNS)
    tables = data_table(["step", "pop", "plant_intake", "meat_intake", "dung", "digest_mean", "digest_std", "flesh_guts", "deaths_broken", "biters_share", "lineages", "sensor_agents_share", "size_mean", "soil", "carrion", "steps_per_sec"],
                        {f"{label}, seed 9": d for label, d in logs.items()}, every=1)

    # ---- the batch ----
    blogs, blin = {}, {}
    for world, (folder, run, _) in BATCH.items():
        blogs[world] = {sd: {k: v[:LAST_STEP // 10_000] for k, v in load_csv(f"results/{run}_seed{sd}_log.csv", folder).items()} for sd in SEEDS if exists(folder, f"{run}_seed{sd}")}
        blin[world] = {sd: lineage_rows(f"{run}_seed{sd}", folder) for sd in SEEDS if exists(folder, f"{run}_seed{sd}")}
    have_batch = bool(blogs[B_SHARP])
    bsum = {}
    for world in BATCH:
        for sd, d in blogs[world].items():
            n = len(d["step"])
            h = slice(n // 2, n)
            by = blin[world][sd]
            spans = sorted((int(r[-1]["step"]) - int(r[0]["step"]) + CONFIRM_STEPS for r in by.values()), reverse=True)
            per_step = Counter(int(r["step"]) for rows in by.values() for r in rows)
            nw, hold, holds = winners(by)
            meat = [m / max(m + p_, 1e-9) for m, p_ in zip(d["meat_intake"][h], d["plant_intake"][h])]
            bsum[(world, sd)] = dict(pop=median(d["pop"][h]), pop_min=min(d["pop"]), meat=median(meat), kills=median(k / 1e4 for k in d["deaths_broken"][h]),
                                     biters=median(d["biters_share"][h]), sensor=max(d["sensor_agents_share"]),
                                     d_end=d["digest_mean"][-1] if "digest_mean" in d else float("nan"), d_min=min(d["digest_mean"]) if "digest_mean" in d else float("nan"),
                                     d_std=median(d["digest_std"][h]) if "digest_std" in d else float("nan"), flesh=max(d["flesh_guts"][n // 4:]) if "flesh_guts" in d else float("nan"),
                                     lineages=median(per_step.get(t, 0) for t in range(LAST_STEP // 2, LAST_STEP + 1, 1000)), longest=spans[0] if spans else 0,
                                     winners=nw, hold=hold, holds=holds, last=int(d["step"][-1]), dung=median(d["dung"][h]) if "dung" in d else 0.0)
    charts_batch, timelines, brows = [], [], ""
    if have_batch:
        charts_batch = [
            seeds_chart("The axis, four seeds", "Mean d over the bodies, one line per seed of the sharp curve. Falling lines are selection toward the plant gut.", blogs, lambda d, i: d["digest_mean"][i] if "digest_mean" in d else float("nan"), ymin=0, ymax=1),
            seeds_chart("Bodies on the flesh side, four seeds", "The share of bodies with d over 0.5. A flesh lineage would show as a rise that holds.", blogs, lambda d, i: d["flesh_guts"][i] if "flesh_guts" in d else float("nan"), ymin=0, ymax=1, percent=True),
            seeds_chart("Bodies", "Bodies alive, one line per seed and world. The law's cost to the world is the gap.", blogs, lambda d, i: d["pop"][i], ymin=0),
            seeds_chart("Flesh in the intake", "The share of the digested matter that was flesh, per seed. The control's world eats its dead.", blogs, lambda d, i: d["meat_intake"][i] / max(d["meat_intake"][i] + d["plant_intake"][i], 1e-9), ymin=0, ymax=1, percent=True),
            seeds_chart("Bodies with a sensor", "The share of bodies carrying a sensor block, per seed. e026's season brought the eye; the law's thinner world keeps it longer in one seed.", blogs, lambda d, i: d["sensor_agents_share"][i], ymin=0, ymax=1, percent=True),
            seeds_chart("Bodies killed per step", "Deaths by a broken body per step. Zero would mean no body breaks another.", blogs, lambda d, i: d["deaths_broken"][i] / 1e4, ymin=0),
        ]
        timelines = [timeline_chart(f"Lineages of the sharp curve, seed {sd}", "Bodies in every confirmed lineage over the run, colored by the lineage's axis d (dark: plant gut, yellow: flesh gut). Seed 2: one winner for 460,000 steps; seed 3: 27 holders of the top place, d falling to 0.1.", blin[B_SHARP][sd]) for sd in [2, 3] if sd in blin[B_SHARP]]
        brows = "".join((f"<tr><td>{world}, seed {sd}</td><td>{b['pop']:,.0f}</td><td>{b['pop_min']:,.0f}</td><td>{b['meat']:.0%}</td><td>{b['d_end']:.2f}</td><td>{b['d_std']:.2f}</td><td>{b['flesh']:.0%}</td>"
                         f"<td>{b['kills']:.2f}</td><td>{b['biters']:.1%}</td><td>{b['sensor']:.1%}</td><td>{b['lineages']:.0f}</td><td>{b['longest']:,}</td><td>{b['winners']}; {b['hold']:,}</td></tr>").replace("nan%", "-").replace("nan", "-")
                        for (world, sd), b in bsum.items())
    TEXT["question"] = ("The user's premise after e025 (#32): guts differ, a cow's takes grass and a cat's takes meat. So far every gut takes plant, fruit and dead matter alike, "
                        "and the split between grazers and hunters is the tooth's alone. This experiment gives the gut material one heritable number that says what it digests well, "
                        "and asks by #19's rule whether a plant lineage and a flesh lineage then win together:")
    TEXT["world"] = ("e026's season world (128x128, the sun a sine of 20,000 steps at amplitude 0.5, the weight and flesh laws, the canopy, the spill, rain on every cell alike), "
                     "with one law about the gut material added and nothing else changed. The control is e026 itself: this code with the law off is e026 byte for byte.")
    TEXT["runs"] = ("Two pilots on seed 9, 100,000 steps, all threads (11 minutes each): the line and the sharp curve, against e026's pilot on seed 9. "
                    "Then the sharp curve on seeds 1-4, 500,000 steps, one thread each (about 2 hours), against e026's four season runs. Every 10,000 steps the log records:")
    TEXT["h_axis"] = "The line leaves the axis where it was; the sharp curve moves it to the plant side"
    TEXT["p_axis"] = ("Under the line the mean of d stays at 0.5 and the spread at 0.07 for 100,000 steps: the axis is neutral. Under the sharp curve it falls to 0.28 in 60,000 steps, "
                      "the spread halves, and no body is on the flesh side after 50,000. The line's yield of a mixed diet is a straight line in d whose slope is the flesh share minus the plant share, "
                      "and the world settles at the diet where that is nothing. The sharp curve has a slope, and the diet is mostly plant.")
    TEXT["h_world"] = "Either law costs the world two thirds of its bodies, because the world eats its dead"
    TEXT["p_world"] = ("In the control 70% of what the bodies digest is flesh: their own dead, eaten where they fell, so the intake is 1.5-2.5 times the sun. "
                       "A middle gut leaves a quarter of every pass in the soil, the cycle decays, the intake halves and the matter sits in the soil (110k of 140k, control 56-103k), "
                       "where only the sun's rate turns it back into plants.")
    TEXT["h_lineages"] = "Every lineage eats a mix; none is a flesh gut"
    TEXT["p_lineages"] = ("No lineage of either pilot passes d 0.65, and the flesh share of a lineage's intake follows its gut, not its place: the plant guts of the sharp curve digest a third flesh, the middle guts of the line half. "
                          "A body's diet is the world's mix wherever it stands.")
    sharp = lambda sd: (f"the sharp curve, seed {sd}", HERE, f"{BASE}_digest2_seed{sd}")
    if have_batch:
        TEXT["gallery"] = gallery([
            (*sharp(2), 1, "The seed 2 winner at step 400,000, with an eye", "Fifteen guts around a hollow and one sensor; no muscle, so it never moves: it eats the six cells under it and waits for the plant. The eye sees where the crowd is.", 400_000),
            (*sharp(1), 1123, "The seed 1 winner, dense", "Ten guts in two rows at density 1.4: heavy for its size, so a light body cannot shove it off its cells. No muscle: it sits."),
            (*sharp(4), 826, "The seed 4 winner", "Twelve guts along the front and one flank; four cells of ground under it. Nothing moves it and it moves nowhere."),
            (*sharp(3), 33, "The seed 3 holder", "A triangle of fourteen guts on three cells: the most gut per cell of ground of the six, in the seed where the top place changed hands 27 times."),
            (*sharp(3), 2972, "Seed 3, light and near the plant end", "Seven guts at density 0.64 and d 0.09: a child costs half what the dense winners cost, and it digests nine tenths of the plant."),
            ("the line, seed 9", HERE, f"{BASE}_digest1_seed9", 95, "The line's winner, a middle gut", "Ten guts at d 0.49: three quarters of everything, and 42% of what it digested was flesh. The line gave it no reason to be anything else."),
        ], "Figure 2. Bodies of lineages that prospered: the most common body of the lineage at its peak, on the 8x8 grid a body grows on, front up (the dashed edge). Blue: hard, orange: muscle, green: digestive, yellow: sensor. \"Flesh\" is the share of the lineage's lifetime digested intake that was dead matter or broken cells.")
    TEXT["tldr"] = ("A heritable digestion axis on the gut, as the issue's line, is neutral: the world eats its dead, so every gut eats a mix, and on that mix the line has no slope. "
                    "As a sharp curve it is selected, but one way: all four seeds go to the plant gut (d 0.15-0.32), no flesh gut appears, kills stop, the winners lose their muscle and sit. "
                    "Either form costs the world two thirds of its bodies, since what a gut leaves goes to the soil. Not kept. Next: #28, the body's grid.")
    TEXT["verdicts"] = ("<li><span class=\"verdict partly\">Partly</span> The line: no (d 0.46-0.52, spread 0.07). The sharp curve: yes, toward the plant gut only (d 0.15-0.32 at the end in four seeds, spread 0.04-0.07).</li>"
                        "<li><span class=\"verdict no\">No</span> No flesh lineage in any run: bodies over d 0.5 are 0-5% at the end; the top lineages sit at d 0.09-0.33.</li>"
                        "<li><span class=\"verdict no\">No</span> The world stands but at a third of the control: 1,060-1,410 bodies against 2,610-4,780.</li>"
                        "<li><span class=\"verdict no\">No</span> The bite is gone (0-0.1% of bodies) and kills fall to 0.00-0.13 a step (control 0.99-3.67).</li>")
    TEXT["h_batch"] = "Four seeds go to the plant gut, and the winners stop moving"
    TEXT["p_batch"] = ("Every seed's mean d falls and stays under 0.35; the flesh side is a transient of a few thousand steps at most (22% once in seed 1). "
                       "With flesh worth half, nobody breaks anybody: kills are 0.00-0.13 a step, and with nobody to flee or hunt the winners drop their muscle "
                       "(0.02-0.13 per body in three seeds, control 1.4-4.3; speed 0.001-0.005 against 0.06-0.12). The eye is e026's, a little more (a sensor on 4-50% of bodies, control 1.5-19%).")
    TEXT["p_timelines"] = ("Seed 2 is one lineage for the whole run, seed 3 is 27 holders of the top place while d falls from 0.24 to 0.09 and the density from 1.0 to 0.6: "
                           "the plant end is reached by lighter bodies. Both kinds of run are e026's (1-14 holders); the law changes the winner, not the number of winners.")
    TEXT["discussion"] = ("<p>The gut's chemistry cannot sort what the ground does not. The flesh of this world is its own dead, lying where the bodies stand, so a body's diet is the world's mix "
                          "wherever it eats; with the line, the mix the world settles into is the one where the axis is flat. A flesh gut would need flesh to lie apart from the plants, "
                          "which takes a place (#14) or a hunter that carries its prey. The sharp curve shows the axis works as a material: it is selected, and it pulls the density with it.</p>"
                          "<p>The cost is the law's second half. A gut that leaves a quarter of every pass in the soil breaks the cycle that fed e026 (an intake of 1.5-2.5 times the sun, most of it the dead); "
                          "the matter piles in the soil, and the plants draw on it only at the sun's rate. A world of plant guts is a lawn with sitting bodies on it: no kills, no muscle, more trees (580-1,000 against 260-530).</p>"
                          "<p>Not shown: the dung left as dead matter, or a floor above one half; either softens the cost, neither gives the flesh gut a place to live.</p>")
    TEXT["conclusion"] = ("Not kept. #32's answer is that a digestion axis is a working material property (the sharp curve selects it) but has nothing to split in a world whose flesh is its own dead, "
                          "and its dung starves the world. The split between grazers and hunters stays with the tooth and the state of the world. Next: #28, small and large bodies in one world.")
    for k in ["tldr", "question", "world", "runs", "verdicts", "h_axis", "p_axis", "h_world", "p_world", "h_lineages", "p_lineages", "gallery", "h_batch", "p_batch", "p_timelines", "discussion", "conclusion"]:
        TEXT.setdefault(k, "TODO")
    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>e028 What a gut digests - Report</title>
<style>{CSS}</style>
</head>
<body>
<main>
<h1>e028: What a gut digests</h1>
<p class="sub">Experiment report - 2026-09-04 - a heritable digestion axis on the gut material in e026's season world: two pilots on seed 9 (the line and a sharp curve) and the sharp curve on seeds 1-4 for 500,000 steps, against e026's runs.</p>

<section class="tldr">
<h2>TL;DR</h2>
<p>{TEXT["tldr"]}</p>
</section>

<h2>1. Question</h2>
<p>{TEXT["question"]}</p>
<ol>
  <li><strong>The axis is selected.</strong> The bodies leave the middle: the spread of d grows past the control's and lineages sit near 0 or 1.</li>
  <li><strong>Two kinds of winner.</strong> A plant lineage and a flesh lineage hold top places in one run for 100,000 steps or more.</li>
  <li><strong>The world stands</strong> at a population within 25% of e026's.</li>
  <li><strong>The tooth follows the gut.</strong> Flesh-side lineages carry more bite; kills per step are e026's or more.</li>
</ol>

<h2>2. The law</h2>
<p>{TEXT["world"]}</p>
{DIAGRAM}
<div class="grid2">{tradeoff_chart()}</div>
<p><strong>Runs.</strong> {TEXT["runs"]}</p>
<ul class="measures">
  <li><strong>digest_mean, digest_std</strong> - the axis over the bodies alive: its mean and spread.</li>
  <li><strong>flesh_guts</strong> - the share of bodies with d over 0.5.</li>
  <li><strong>dung</strong> - matter taken and not digested, per step.</li>
  <li><strong>intake</strong> - plant and flesh digested per step; <strong>flesh share</strong> - the flesh's part of it.</li>
  <li><strong>lineages</strong> - each lineage's d, bite, guts and diet every 1,000 steps; the longest lineage in steps.</li>
  <li>bodies, kills per step, bodies with a bite.</li>
</ul>

<h2>3. Results</h2>
<div class="tw"><table>
<thead><tr><th>Seed 9, 100,000 steps (range over the log)</th><th>bodies</th><th>intake a step</th><th>flesh share</th><th>dung a step</th><th>d mean</th><th>d spread</th><th>flesh side</th><th>killed a step</th><th>with a bite</th><th>lineages</th><th>longest lineage</th></tr></thead>
<tbody>{rows}</tbody></table></div>
<ol class="verdicts">
{TEXT["verdicts"]}
</ol>

<h3>3.1 {TEXT["h_axis"]}</h3>
<div class="grid2">
{"".join(charts_axis)}
</div>
<p>{TEXT["p_axis"]}</p>

<h3>3.2 {TEXT["h_world"]}</h3>
<div class="grid2">
{"".join(charts_world)}
</div>
<p>{TEXT["p_world"]}</p>

<h3>3.3 {TEXT["h_lineages"]}</h3>
<div class="grid2">
{"".join(charts_lineages)}
</div>
<p>{TEXT["p_lineages"]}</p>

<h3>3.4 {TEXT["h_batch"]}</h3>
<div class="tw"><table>
<thead><tr><th>500,000 steps (second half unless said)</th><th>bodies</th><th>fewest</th><th>flesh share</th><th>d at the end</th><th>d spread</th><th>flesh side, most</th><th>killed a step</th><th>with a bite</th><th>with a sensor, most</th><th>lineages</th><th>longest lineage</th><th>winners; longest hold</th></tr></thead>
<tbody>{brows}</tbody></table></div>
<div class="grid2">
{"".join(charts_batch)}
</div>
<p>{TEXT["p_batch"]}</p>
{"".join(timelines)}
<p>{TEXT["p_timelines"]}</p>
{TEXT["gallery"]}

<h2>4. Discussion</h2>
{TEXT["discussion"]}

<h2>5. Conclusion and next step</h2>
<p>{TEXT["conclusion"]}</p>

<h2>Appendix: data</h2>
<p>Every log step of the three runs; the full data is in <code>results/*.csv</code> and <code>../e026_weather/results/</code>. Build this report with <code>uv run python experiments/e028_gut/report.py</code>.</p>
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
