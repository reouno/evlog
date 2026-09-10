#!/usr/bin/env python3
"""Build report.html for this experiment.

Charts: matplotlib, exported as SVG and inlined. Diagram: hand-written SVG.
Run from the repo root: uv run python experiments/e045_connect/report.py
(`report.py lineages` prints the top lineages of every run, to pick the gallery;
`report.py numbers` prints the measures over the second half, for the README.)
"""
import csv
import html
import io
import json
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

BASE = "128_sigma0_r64_f0_flat_eyes8_flesh1_w1_season2_digest0_sidegrow_store5_yolk0_breed0_winterhigh_water0.1_leach0.01_depth0.01_mix0.2_strict_sat_hold_wear3000"


def run(connect=0, seed=9):
    return f"{BASE}{'_connect' if connect else ''}_seed{seed}"


# e044's season world with wear 3,000 (strict, sat, hold, winter high 2, water 0.1, leach 0.01,
# depth 0.01, mix 0.2, flow 0, rain flat, side grow, store 5): label -> (run prefix, color slot,
# line style). connect 0 is e044's wear run byte for byte.
RUNS = {
    "control, seed 9": (run(0, 9), 5, "-"),
    "connect, seed 9": (run(1, 9), 0, "-"),
    "control, seed 10": (run(0, 10), 5, "--"),
    "connect, seed 10": (run(1, 10), 0, "--"),
}
STEPS = 100_000
SEASON = 20_000
LOG = 10_000  # steps per log.csv row
SEEDS = [9, 10, 11, 12, 13, 14]  # 9 and 10: the runs above; 11-14: the batch (the law changed who wins on both)

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


def exists(run, folder=HERE):
    """A run whose log has rows (a run still writing keeps its log empty until its buffer flushes)."""
    path = os.path.join(folder, f"results/{run}_log.csv")
    return os.path.exists(path) and os.path.getsize(path) > 200


def half(d, lo=STEPS // 2, hi=STEPS):
    return [i for i, t in enumerate(d["step"]) if lo < t <= hi]


def half_mean(d, key, lo=STEPS // 2, hi=STEPS):
    """The mean of a column over the rows with lo < step <= hi."""
    idx = half(d, lo, hi)
    return sum(d[key][i] for i in idx) / len(idx) if idx else float("nan")


def lived_births(d, i):
    """The births of log row i that were born with a block (the log's births count the children born without one)."""
    return max(d["births"][i] - d["deaths_body"][i], 1.0)


def cut_at_birth(d, i):
    """(the share of the births with a block that were cut down, the blocks not built per such birth) in log row i."""
    n = lived_births(d, i)
    return d["born_cut"][i] * d["births"][i] / n, d["not_built"][i] * d["births"][i] / n


def born_size(run, lo=STEPS // 2):
    """The mean size at birth of the bodies that lived and died after step lo (deaths.csv bins it by 4: the middle of the bin)."""
    n = s = 0
    for r in load_rows(f"results/{run}_deaths.csv"):
        if int(r["step"]) > lo:
            n += int(r["n"])
            s += int(r["n"]) * (int(r["size"]) + 1.5)
    return s / max(n, 1)


def eaten(d, i):
    """(plant, flesh of kills, dead scavenged) eaten per step in log row i."""
    hunted = d["kill_gain"][i] * d["cells_broken"][i] / LOG
    return d["plant_intake"][i] / LOG, hunted, d["meat_intake"][i] / LOG - hunted


def cut_stats(run, d):
    """The measures of the cut over the second half."""
    idx = half(d)
    births = sum(lived_births(d, i) for i in idx)
    born_cut = sum(cut_at_birth(d, i)[0] * lived_births(d, i) for i in idx) / births
    not_built = sum(cut_at_birth(d, i)[1] * lived_births(d, i) for i in idx) / births
    size = born_size(run)
    m = lambda k: half_mean(d, k)
    food = [eaten(d, i) for i in idx]
    plant, hunted, scav = (sum(f[j] for f in food) / len(food) for j in range(3))
    return dict(born_cut=born_cut, not_built=not_built, written=not_built / (size + not_built), size=size,
                split=m("split"), outside=m("outside"), broken=m("cells_broken") / LOG, cut_break=m("cut_break"),
                cut_wear=m("cut_wear"), cut_bodies=m("cut_bodies"), worn=m("worn"),
                plant=plant, hunted=hunted, scav=scav, hunted_share=hunted / (plant + hunted + scav))


def seed_stats(connect, seed):
    """One seed under one law, over the second half: the flesh of kills' share of the intake, bodies, the
    lowest winter floor, the top lineage of the last third, the diversity number. None if the run is missing."""
    r = run(connect, seed)
    if not exists(r):
        return None
    d, f = load_csv(f"results/{r}_log.csv"), fine(r)
    food = [eaten(d, i) for i in half(d)]
    div, wins = diversity(r)
    return dict(share=sum(x[1] for x in food) / sum(sum(x) for x in food), bodies=half_mean(f, "pop"),
                floor=min(x["pop"] for x in floors(f)), top=top_lineage(r), div=div, wins=len(wins),
                cut=half_mean(d, "cut_break") / max(half_mean(d, "cells_broken") / LOG, 1e-9), born_cut=cut_stats(r, d)["born_cut"])


# ---------- the diversity number (#42), copied from e039 ----------
# The winners of a window are the lineages holding at least WIN_SHARE of its body-steps. Two
# winners are the same body when their sizes are within SIZE_FACTOR and the mixes of their blocks
# differ by at most MIX_DIST in sum; single linkage on that relation, the number of groups.
WIN_SHARE = 0.05
SIZE_FACTOR = 1.5
MIX_DIST = 0.4
KIND_COLS = ["hard", "muscle", "sensor", "digestive"]
PLACE_COL = {"world": "size", "valley": "p0", "slope": "p1", "ridge": "pnone"}


def same_body(a, b):
    """Two mean bodies (counts by kind) are the same shape."""
    sa, sb = sum(a), sum(b)
    if sa <= 0 or sb <= 0:
        return False
    if max(sa, sb) > SIZE_FACTOR * min(sa, sb):
        return False
    return sum(abs(x / sa - y / sb) for x, y in zip(a, b)) <= MIX_DIST


def diversity(run, folder=HERE, place="world", window=None):
    """(diversity, winners): the groups of winner bodies, and the winners, over `window` steps."""
    rows = load_rows(f"results/{run}_lineages.csv", folder)
    if not rows:
        return 0, []
    steps = [int(r["step"]) for r in rows]
    lo, hi = window or (max(steps) - (max(steps) - min(steps)) // 3, max(steps))
    col = PLACE_COL[place]
    total, shape = defaultdict(float), defaultdict(lambda: [0.0] * len(KIND_COLS))
    for r in rows:
        if not lo <= int(r["step"]) <= hi:
            continue
        n = float(r[col])
        if n <= 0:
            continue
        i = int(r["lineage"])
        total[i] += n
        for j, k in enumerate(KIND_COLS):
            shape[i][j] += n * float(r[k])
    body_steps = sum(total.values())
    if body_steps <= 0:
        return 0, []
    win = sorted((i for i, n in total.items() if n >= WIN_SHARE * body_steps), key=lambda i: -total[i])
    mean = {i: [x / total[i] for x in shape[i]] for i in win}
    groups = []
    for i in win:
        hit = [g for g in groups if any(same_body(mean[i], mean[j]) for j in g)]
        if hit:
            merged = [i] + [j for g in hit for j in g]
            groups = [g for g in groups if g not in hit] + [merged]
        else:
            groups.append([i])
    return len(groups), [(i, total[i] / body_steps, sum(mean[i]), mean[i]) for i in win]


def fine(run, folder=HERE, last_step=STEPS):
    """Every 1,000 steps (pop.csv): the bodies alive and their mean age; lineages of 5 or more."""
    lin = Counter()
    for rows in lineage_rows(run, folder).values():
        for r in rows:
            if int(r["step"]) <= last_step:
                lin[int(r["step"])] += 1
    d = load_csv(f"results/{run}_pop.csv", folder)
    keep = [i for i, t in enumerate(d["step"]) if t <= last_step]
    out = {k: [v[i] for i in keep] for k, v in d.items()}
    out["lineages"] = [lin[int(t)] for t in out["step"]]
    return out


def floors(f):
    """Per season window: the trough (bodies, lineages) and the peak."""
    out = []
    for c in range(int(max(f["step"])) // SEASON):
        idx = [i for i, t in enumerate(f["step"]) if c * SEASON < t <= (c + 1) * SEASON]
        if not idx:
            continue
        lo = min(idx, key=lambda i: f["pop"][i])
        hi = max(idx, key=lambda i: f["pop"][i])
        out.append(dict(step=int(f["step"][lo]), pop=int(f["pop"][lo]), lin=f["lineages"][lo], peak=int(f["pop"][hi])))
    return out


def top_lineage(run, folder=HERE):
    """The lineage holding the most body-steps of the last third: (id, share, mean cells, muscle, gut, flesh share, length, width)."""
    rows = load_rows(f"results/{run}_lineages.csv", folder)
    steps = [int(r["step"]) for r in rows]
    lo = max(steps) - (max(steps) - min(steps)) // 3
    total, muscle, gut, cells, meat, plant, fwd, side = (defaultdict(float) for _ in range(8))
    for r in rows:
        if int(r["step"]) < lo:
            continue
        i, n = int(r["lineage"]), float(r["size"])
        total[i] += n
        muscle[i] += n * float(r["muscle"])
        gut[i] += n * float(r["digestive"])
        cells[i] += n * sum(float(r[k]) for k in KIND_COLS)
        meat[i] += n * float(r["meat"])
        plant[i] += n * float(r["plant"])
        fwd[i] += n * float(r["len_fwd"])
        side[i] += n * float(r["len_side"])
    i = max(total, key=total.get)
    all_n = sum(total.values())
    return (i, total[i] / all_n, cells[i] / total[i], muscle[i] / total[i], gut[i] / total[i], meat[i] / max(meat[i] + plant[i], 1e-9),
            fwd[i] / total[i], side[i] / total[i])


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
    if xlabel == "seed":
        ax.xaxis.set_major_locator(MaxNLocator(integer=True))
        ax.margins(x=0.06)
    return fig, ax


def legend_above(ax, n):
    ax.legend(loc="lower left", bbox_to_anchor=(0, 1.0), ncols=n, handlelength=1.8, borderaxespad=0, columnspacing=1.2)


def line_chart(title, subtitle, series, ymin=None, ymax=None, percent=False, xlabel="step", fmt=None, ncols=2, markers=False, msize=3):
    """series: list of (label, xs, ys, slot, line style)."""
    fig, ax = new_axes(xlabel)
    for label, xs, ys, slot, ls in series:
        ax.plot(xs, ys, color=SERIES[slot], linewidth=1.6, label=label, linestyle=ls, marker="o" if markers else None, markersize=msize)
    top = max((v for _, _, ys, _, _ in series for v in ys if v == v), default=1.0)
    if ymin is not None:
        ax.set_ylim(ymin, ymax if ymax is not None else top * 1.15)
    ax.yaxis.set_major_formatter(fmt or ((lambda y, _p: f"{y:.0%}") if percent else kfmt))
    ax.yaxis.set_major_locator(MaxNLocator(4, steps=[1, 2, 5, 10]))  # no 2.5 step: a 2.5% tick would read "2%"
    legend_above(ax, ncols)
    return figure(title, subtitle, to_svg(fig))


def figure(title, subtitle, svg):
    return f"""
<figure class="fig">
  <figcaption><strong>{html.escape(title)}</strong><span>{html.escape(subtitle)}</span></figcaption>
  {svg}
</figure>"""


def data_table(cols, rows_by_name, every=1):
    """Collapsed tables for the appendix. rows_by_name: {name: {col: [values]}}."""
    out = []
    for name, d in rows_by_name.items():
        cs = [c for c in cols if c in d]
        rows = "".join("<tr>" + "".join(f"<td>{d[c][i]:g}</td>" for c in cs) + "</tr>" for i in range(0, len(d[cs[0]]), every))
        out.append(f"<details><summary>{html.escape(name)}</summary><div class='tw'><table><thead><tr>"
                   + "".join(f"<th>{c}</th>" for c in cs) + f"</tr></thead><tbody>{rows}</tbody></table></div></details>")
    return "\n".join(out)


def gallery(picks, caption):
    """picks: [(label, run, lineage id, name, what the shape does)]. The most common grown body of each lineage
    at its peak, on the grid it grew on (drawn at the same width whatever the side), front up."""
    cards = []
    cache = {}
    for label, run, lid, name, what in picks:
        if run not in cache:
            cache[run] = (lineage_rows(run), load_bodies(run), list(read_frames(f"results/{run}_long.jsonl")))
        by, bodies, frames = cache[run]
        rows = by[lid]
        peak = max(rows, key=lambda r: int(r["size"]))
        span = int(rows[-1]["step"]) - int(rows[0]["step"]) + CONFIRM_STEPS
        frame = min((fr for fr in frames if any(a[4] == lid for a in fr["agents"])), key=lambda fr: abs(fr["step"] - int(peak["step"])))
        # The most common body among the grown ones (at least three quarters of the lineage's
        # mean cells at its peak): a lineage in bloom is mostly newborns of one or two cells.
        grown = 0.75 * sum(float(peak[k]) for k in KIND_COLS)
        ids = [a[2] for a in frame["agents"] if a[4] == lid]
        c = Counter(i for i in ids if sum(ch != "0" for ch in bodies[i][1]) >= grown) or Counter(ids)
        side, cells = bodies[c.most_common(1)[0][0]]
        u = 88 / side
        rects = "".join(f'<rect x="{(i % side) * u:.2f}" y="{(i // side) * u:.2f}" width="{u * 0.9:.2f}" height="{u * 0.9:.2f}" fill="{KIND_COLOR[int(k)]}"/>' for i, k in enumerate(cells) if k != "0")
        m, pl = float(peak["meat"]), float(peak["plant"])
        meat = m / (m + pl) if m + pl > 0 else 0
        cards.append(f"""<figure class="card"><svg viewBox="-1 -1 89 89" width="120" height="120" role="img" aria-label="{html.escape(name)}"><rect x="-1" y="-1" width="89" height="89" fill="var(--cell)"/>{rects}<line x1="-1" y1="-0.5" x2="88" y2="-0.5" stroke="var(--ink2)" stroke-width="1.5" stroke-dasharray="3 2"/></svg>
<figcaption><strong>{html.escape(name)}</strong><br>{html.escape(label)}, lineage {lid}: {span:,} steps, {int(peak["size"]):,} agents at its peak<br>side {float(peak["side"]):.0f} (grid {side}x{side}); mass {float(peak["mass"]):.0f}: hard {float(peak["hard"]):.0f}, muscle {float(peak["muscle"]):.0f}, sensor {float(peak["sensor"]):.1f}, digestive {float(peak["digestive"]):.0f}; flesh {meat:.0%} of the intake; mean age {float(peak["age"]):.0f}<br>{html.escape(what)}</figcaption></figure>""")
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
th:first-child, td:first-child {{ text-align: left; white-space: nowrap; }}
th {{ color: var(--ink2); font-weight: 600; }}
.tw {{ overflow-x: auto; margin: 8px 0; }}
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


def cells_svg(cells, x0, y0, u=24, size=22, **attrs):
    extra = " ".join(f'{k.replace("_", "-")}="{v}"' for k, v in attrs.items())
    return "".join(f'<rect x="{x0 + c * u}" y="{y0 + r * u}" width="{size}" height="{size}" rx="2" {extra}/>' for c, r in cells)


# Hand-written mechanism diagram. Label every arrow; currentColor for lines and text;
# var(--s1) for the one element the argument hinges on (the part that stays the body).
# Keep 10-15px between text and lines.
DIAGRAM = f"""
<figure class="fig diagram">
<svg viewBox="0 0 900 250" width="100%" role="img" aria-label="At birth only the largest part joined through the sides is built; after a break the largest part stays the body and the part cut off falls to the ground as dead matter" font-size="12" fill="currentColor" stroke="currentColor">
  <g stroke="none" fill="var(--s1)">
    {cells_svg([(0, 0), (1, 0), (2, 0), (1, 1), (1, 2)], 40, 50)}
    {cells_svg([(0, 0), (1, 0), (0, 1), (1, 1)], 500, 50)}
  </g>
  <g fill="none" stroke-width="1.2" stroke-dasharray="3 2">
    {cells_svg([(4, 1), (4, 2), (2, 3)], 40, 50)}
    {cells_svg([(3, 0), (3, 1), (4, 1)], 500, 50)}
  </g>
  <g fill="none" stroke-width="1.2">
    {cells_svg([(2, 1)], 500, 50)}
    <path d="M552,78 l14,14 M566,78 l-14,14"/>
    <path d="M559,138 L551,156 L567,156 Z" fill="currentColor"/>
  </g>
  <line x1="440" y1="20" x2="440" y2="230" stroke-opacity="0.3"/>
  <g stroke="none">
    <text x="40" y="38" fill="var(--s1)" font-weight="600">built: the largest part</text>
    <text x="186" y="104">not built, not paid</text>
    <text x="124" y="146">a corner holds nothing</text>
    <text x="40" y="192" font-weight="600">At birth</text>
    <text x="40" y="210" font-size="11">only the part whose blocks join through their sides,</text>
    <text x="40" y="225" font-size="11">the largest, is made; the parent pays for it alone</text>
    <text x="500" y="38" fill="var(--s1)" font-weight="600">stays the body: the largest part</text>
    <text x="630" y="70">cut off: falls to the ground</text>
    <text x="630" y="86" font-size="11">dead matter, with its share of</text>
    <text x="630" y="100" font-size="11">the body's energy and fat</text>
    <text x="578" y="152" font-size="11">a bite breaks the bridge;</text>
    <text x="578" y="166" font-size="11">the breaker eats that block</text>
    <text x="500" y="192" font-weight="600">A break (or a worn block)</text>
    <text x="500" y="210" font-size="11">once the step's breaks are done, a body in parts keeps</text>
    <text x="500" y="225" font-size="11">the largest (then the heavier, then the first in grid order)</text>
  </g>
</svg>
<figcaption>Figure 1. A body is what holds together. Blocks join through their sides, not their corners. At birth only the largest part is built; when a break or a worn block leaves a body in parts, the largest stays the body and the rest falls to the ground as dead matter, where anyone may eat it.</figcaption>
</figure>
"""


TEXT = {}  # filled in main(); counted at the end


def load_all():
    logs = {label: load_csv(f"results/{r}_log.csv") for label, (r, _, _) in RUNS.items() if exists(r)}
    fines = {label: fine(r) for label, (r, _, _) in RUNS.items() if label in logs}
    stats = {label: cut_stats(RUNS[label][0], d) for label, d in logs.items()}
    return logs, fines, stats


def numbers():
    """The measures over the second half, per run (for the README)."""
    logs, fines, stats = load_all()
    for label, d in logs.items():
        f, s = fines[label], stats[label]
        r = RUNS[label][0]
        m = lambda k: half_mean(d, k)
        w = floors(f)
        i, share, cells, muscle, gut, meat, fwd, side = top_lineage(r)
        div, wins = diversity(r)
        print(f"{label}: births cut {s['born_cut']:.2%} not built/birth {s['not_built']:.3f} (born size {s['size']:.1f}: {s['written']:.2%} of the blocks written) "
              f"| split {s['split']:.2%} outside {s['outside']:.2%} | broken/step {s['broken']:.1f} cut after break {s['cut_break']:.2f} "
              f"({s['cut_break'] / max(s['broken'], 1e-9):.1%} of broken) after wear {s['cut_wear']:.3f} (worn {s['worn']:.2f}) bodies cut {s['cut_bodies']:.2f}")
        print(f"   eaten plant {s['plant']:.1f} hunted {s['hunted']:.1f} scavenged {s['scav']:.1f} hunted share {s['hunted_share']:.1%} "
              f"| deaths broken/step {m('deaths_broken') / LOG:.2f} hunger/step {m('deaths_energy') / LOG:.2f}")
        print(f"   floors {[x['pop'] for x in w]} bodies {half_mean(f, 'pop'):.0f} births {m('births') / LOG:.2f} mean age {half_mean(f, 'age_mean'):.0f} "
              f"lineages {half_mean(f, 'lineages'):.1f} | size p50 {m('size_p50'):.1f} len {m('len_fwd'):.2f}x{m('len_side'):.2f} "
              f"muscle {m('muscle_mean'):.2f} gut {m('digestive_mean'):.2f} | top {i} {share:.0%} {cells:.1f} cells {muscle:.1f} muscle {gut:.1f} gut "
              f"{meat:.0%} flesh {fwd:.1f}x{side:.1f} | diversity {div} of {len(wins)}")


def main():
    logs, fines, stats = load_all()
    style = {label: (slot, ls) for label, (_, slot, ls) in RUNS.items()}
    control = [label for label in RUNS if label.startswith("control") and label in logs]
    connect = [label for label in RUNS if label.startswith("connect") and label in logs]

    def log_series(labels, fn):
        return [(label, logs[label]["step"], [fn(logs[label], i) for i in range(len(logs[label]["step"]))], *style[label]) for label in labels]

    def fine_series(key):
        return [(label, fines[label]["step"], fines[label][key], *style[label]) for label in RUNS if label in fines]

    split_series = [(label, logs[label]["step"], logs[label]["split"], *style[label]) for label in control]
    charts_cut = [
        line_chart("Bodies in pieces, without the law", "Share of the living bodies not joined through their sides, every 10,000 steps (control runs).",
                   split_series, ymin=0, percent=True, markers=True),
        line_chart("Births cut down, under the law", "Share of the births with a block that were cut to their largest part, every 10,000 steps.",
                   log_series(connect, lambda d, i: cut_at_birth(d, i)[0]), ymin=0, percent=True, markers=True),
    ]
    charts_fight = [
        line_chart("Blocks cut off per block broken", "Blocks that fell off a body after a break, over the blocks broken, every 10,000 steps. Zero: a break never cuts a body.",
                   log_series(connect, lambda d, i: d["cut_break"][i] / max(d["cells_broken"][i] / LOG, 1e-9)), ymin=0, ymax=0.6, percent=True, markers=True),
        line_chart("Blocks cut off per block worn", "Blocks that fell off a body after wear, over the blocks worn, every 10,000 steps. Same scale as the chart beside it.",
                   log_series(connect, lambda d, i: d["cut_wear"][i] / max(d["worn"][i], 1e-9)), ymin=0, ymax=0.6, percent=True, markers=True),
    ]
    charts_world = [
        line_chart("Bodies", "Bodies alive every 1,000 steps; the dips are the winters.", fine_series("pop"), ymin=0),
        line_chart("The flesh of kills in what the bodies eat", "Share of the intake that is the blocks the eaters broke (not the dead they found), every 10,000 steps.",
                   log_series([label for label in RUNS if label in logs], lambda d, i: eaten(d, i)[1] / sum(eaten(d, i))), ymin=0, ymax=0.5, percent=True, markers=True),
    ]
    by_seed = {c: {s: seed_stats(c, s) for s in SEEDS} for c in (0, 1)}
    chart_seeds = line_chart(
        "The flesh of kills, by seed", "Share of the intake that is the flesh of kills over the second half, every seed under both laws.",
        [(name, [s + dx for s in SEEDS if by_seed[c][s]], [by_seed[c][s]["share"] for s in SEEDS if by_seed[c][s]], slot, "none")
         for c, name, slot, dx in ((0, "control", 5, -0.08), (1, "connect", 0, 0.08))],
        ymin=0, ymax=0.5, percent=True, xlabel="seed", markers=True, msize=7)

    def top_text(t):
        _i, share, cells, muscle, gut, meat, _f, _s = t
        return f"{share:.0%}: {cells:.0f} cells, {muscle:.0f} muscle, {gut:.0f} gut, {meat:.0%} flesh"

    seed_rows = "".join(
        f"<tr><td>{s}</td><td>{a['share']:.0%} / {b['share']:.0%}</td><td>{a['bodies']:,.0f} / {b['bodies']:,.0f}</td>"
        f"<td>{a['floor']:,} / {b['floor']:,}</td><td>{a['div']} / {b['div']}</td><td>{top_text(a['top'])}</td><td>{top_text(b['top'])}</td></tr>"
        for s in SEEDS for a, b in [(by_seed[0][s], by_seed[1][s])] if a and b)

    def cut_row(label):
        s = stats[label]
        law = label.startswith("connect")
        na = "<td>-</td>"
        return (f"<tr><td>{label}</td>"
                + (f"<td>{s['born_cut']:.1%}</td><td>{s['written']:.1%}</td>" if law else na * 2)
                + (na * 2 if law else f"<td>{s['split']:.1%}</td><td>{s['outside']:.1%}</td>")
                + f"<td>{s['broken']:.0f}</td>" + (f"<td>{s['cut_break']:.1f}</td><td>{s['cut_wear']:.2f}</td>" if law else na * 2)
                + f"<td>{s['plant']:.0f}</td><td>{s['hunted']:.0f}</td><td>{s['scav']:.0f}</td><td>{s['hunted_share']:.0%}</td></tr>")

    def world_row(label):
        d, f = logs[label], fines[label]
        r = RUNS[label][0]
        w = floors(f)
        m = lambda k: half_mean(d, k)
        div, wins = diversity(r)
        i, share, cells, muscle, gut, meat, fwd, side = top_lineage(r)
        return (f"<tr><td>{label}</td><td>{min(x['pop'] for x in w):,}-{max(x['pop'] for x in w):,}</td><td>{half_mean(f, 'pop'):,.0f}</td>"
                f"<td>{m('births') / LOG:.1f}</td><td>{half_mean(f, 'lineages'):.1f}</td>"
                f"<td>{share:.0%}: {cells:.0f} cells, {muscle:.0f} muscle, {gut:.0f} gut, {meat:.0%} flesh</td><td>{div} of {len(wins)}</td></tr>")

    cut_rows = "".join(cut_row(label) for label in RUNS if label in logs)
    world_rows = "".join(world_row(label) for label in RUNS if label in logs)
    tables = data_table(["step", "pop", "births", "deaths_energy", "deaths_broken", "deaths_wear", "cells_broken", "kill_gain", "plant_intake", "meat_intake",
                         "split", "outside", "born_cut", "not_built", "cut_break", "cut_wear", "cut_bodies", "size_p50", "len_fwd", "len_side", "lineages"],
                        {label: d for label, d in logs.items()})
    TEXT.update(TEXTS)
    TEXT["gallery"] = gallery(GALLERY, GALLERY_CAPTION) if GALLERY else ""
    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>e045 A body is what holds together - Report</title>
<style>{CSS}</style>
</head>
<body>
<main>
<h1>e045: A body is what holds together</h1>
<p class="sub">Experiment report - 2026-09-11 - a body is the largest part its blocks make through their sides (#48), at birth and after every break or worn block, against e044's wear runs on seeds 9 and 10. Answer: {TEXT["sub_answer"]}</p>

<section class="tldr">
<h2>TL;DR</h2>
<p>{TEXT["tldr"]}</p>
</section>

<h2>1. Question</h2>
<p>{TEXT["question"]}</p>
<ol>
  <li><strong>Little is cut at birth:</strong> under 10% of the births are cut down, losing under 2% of the blocks their genomes write.</li>
  <li><strong>Fights cut, wear hardly:</strong> the blocks cut off after a break are at least a tenth of the blocks broken, and more than those cut off after wear.</li>
  <li><strong>The world stands:</strong> bodies and floors within 15%, the same plan on top, and the flesh of kills within 5 points of the control's share of the intake.</li>
</ol>

<h2>2. The law</h2>
<p>{TEXT["world"]}</p>
{DIAGRAM}
<p><strong>Runs.</strong> {TEXT["runs"]}</p>
<ul class="measures">
  <li><strong>births cut</strong> - the share of the births (with a block) cut to their largest part, and the share of the blocks written that were not built.</li>
  <li><strong>in pieces</strong> - without the law, the share of the living bodies not joined through their sides, and of the blocks outside the largest part.</li>
  <li><strong>cut off</strong> - blocks that fell off a body per step after a break and after wear, against the blocks broken per step.</li>
  <li><strong>eaten</strong> - per step: plant, the flesh of kills (the blocks the eater broke), the dead scavenged.</li>
  <li><strong>bodies, floors, births</strong> - bodies alive every 1,000 steps, the five winter troughs, births a step.</li>
  <li><strong>lineages, top lineage, diversity</strong> - lineages of 5 or more, the one with the most of the last third, and the diversity number (#42).</li>
</ul>

<h2>3. Results</h2>
<p>Means over the second half (steps 50,000-100,000); intake and blocks per step.</p>
<div class="tw"><table>
<thead><tr><th>run</th><th>births cut</th><th>blocks not built</th><th>bodies in pieces</th><th>blocks outside</th><th>broken</th><th>cut off after a break</th><th>after wear</th><th>plant</th><th>kills</th><th>dead</th><th>kills' share</th></tr></thead>
<tbody>{cut_rows}</tbody></table></div>
<div class="tw"><table>
<thead><tr><th>run</th><th>winter floors</th><th>bodies</th><th>births a step</th><th>lineages alive</th><th>top lineage of the last third</th><th>diversity (#42)</th></tr></thead>
<tbody>{world_rows}</tbody></table></div>
<ol class="verdicts">
{TEXT["verdicts"]}
</ol>

<h3>3.1 {TEXT["h_cut"]}</h3>
<div class="grid2">
{"".join(charts_cut)}
</div>
<p>{TEXT["p_cut"]}</p>

<h3>3.2 {TEXT["h_fight"]}</h3>
<div class="grid2">
{"".join(charts_fight)}
</div>
<p>{TEXT["p_fight"]}</p>

<h3>3.3 {TEXT["h_world"]}</h3>
<div class="grid2">
{"".join(charts_world)}
</div>
<p>{TEXT["p_world"]}</p>
<div class="grid2">
{chart_seeds}
</div>
<div class="tw"><table>
<thead><tr><th>seed</th><th>kills' share (control / connect)</th><th>bodies</th><th>lowest winter floor</th><th>diversity</th><th>top lineage of the last third, control</th><th>connect</th></tr></thead>
<tbody>{seed_rows}</tbody></table></div>
<p>{TEXT["p_seeds"]}</p>
{TEXT["gallery"]}

<h2>4. Discussion</h2>
{TEXT["discussion"]}

<h2>5. Conclusion and next step</h2>
<p>{TEXT["conclusion"]}</p>

<h2>Appendix: data</h2>
<p>Every log step (10,000 steps) of the four runs; the full data are in <code>results/*.csv</code>. Build this report with <code>uv run python experiments/e045_connect/report.py</code>.</p>
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
    ("control, seed 9", run(0, 9), 705, "the grazer", "Muscle in front, gut behind, filling a 4x4 grid: no block is the only link between two others, so a bite takes one block and no more."),
    ("connect, seed 9", run(1, 9), 865, "the armored hunter", "A hard front row and hard corners over gut and muscle on a 6x6 grid: seed 9's winner under the law, in the hunter world."),
    ("control, seed 10", run(0, 10), 575, "the light gut", "A band of gut across the front of an 8x8 grid, no muscle: it wins seed 10's hunter world without the law, beside the hunters."),
    ("control, seed 10", run(0, 10), 438, "a hunter beside it", "Muscle in front, sensors and gut behind, filling a 4x4 grid: 81% of what it eats is flesh."),
    ("connect, seed 10", run(1, 10), 964, "the grazer under the law", "Gut filling a 4x4 grid (some bodies carry muscle); its bodies live near 1,500 steps. Seed 10 settles as a grazer world."),
    ("connect, seed 10", run(1, 10), 859, "the sitter under the law", "A block of gut in one corner of a 9x9 grid, no muscle, mass 11: the light gut again, in one piece."),
]
GALLERY_CAPTION = "The most common grown body of each lineage at its peak, front up (orange muscle, aqua gut, yellow sensor, blue hard); the numbers are the lineage's means at its peak. The grazer world is won by a compact grazer; the hunter world by an armored hunter (seed 9) or a light gut beside hunters (seed 10)."

TEXTS = {
    "sub_answer": ("little is cut at birth, a break rarely cuts, and the world stands on six seeds with about a tenth fewer bodies. "
                   "The hunter world comes on 4 of 6 seeds under both laws. Kept."),
    "tldr": ("Every block a genome wrote was part of the body, touching or not. Now a body is its largest part joined through the "
             "sides, and a part cut off by a break or a worn block falls as dead matter. Few births are cut (under 5% on five seeds), "
             "and a break drops 3-6% more blocks than it breaks. The world stands on six seeds with 4-18% fewer bodies; the hunter "
             "world still comes on 4 of 6. Kept. Next: #49."),
    "question": ("A body grows on a grid of side 4-16, and every block its genome wrote was part of it, touching or not: two groups of "
                 "blocks at the two ends of the grid moved, ate and paid as one. In e044's wear runs 6-10% of the living bodies were in "
                 "pieces. A block should hold only to the blocks beside it (#48). What does that cut, at birth and in fights, and does "
                 "the world still stand?"),
    "world": ("A body is the largest part its blocks make through their sides; a corner holds nothing. At birth only that part is built, "
              "and the parent pays for it alone. When a break or a worn block leaves a body in parts, the largest stays the body and "
              "the rest falls as dead matter, not to the breaker."),
    "runs": ("e044's world with wear 3,000, seeds 9 and 10, 100,000 steps: the control (e044's wear run, byte for byte) and the law. "
             "The law changed who wins on both seeds, so seeds 11-14 ran under both laws too. Twelve runs, 15-17 minutes each."),
    "verdicts": ("<li><span class=\"verdict partly\">Partly</span> On five seeds 0.6-4.4% of the births are cut, losing under 1% of the "
                 "blocks written. On seed 11 the winning lineage writes parts: 12% of the births, 5.2% of the blocks.</li>"
                 "<li><span class=\"verdict no\">No</span> A break drops 3.0-6.4% more blocks than it breaks, under a tenth on every "
                 "seed; still more than wear drops, on all six.</li>"
                 "<li><span class=\"verdict partly\">Partly</span> The world stands on six seeds (lowest floor 345) with 4-18% fewer "
                 "bodies. The hunter world comes on 4 of 6 under both laws; the plan on top changes on four.</li>"),
    "h_cut": "Little is cut at birth; most pieces came from damage",
    "p_cut": ("Without the law 6-10% of the living bodies are in pieces. Under it 0.9-3.4% of the births are cut down, and they lose "
              "0.2-0.4% of the blocks their genomes write: most of the pieces came from a break or a worn block that left two parts."),
    "h_fight": "A break rarely cuts; a worn block often does",
    "p_fight": ("A break drops 5-6% more blocks than it breaks: a push breaks blocks on the surface, and a surface block is rarely the "
                "only link between two parts. A worn block can be any block, and where bodies get old (seed 10 under the law) each one "
                "drops 0.42 more."),
    "h_world": "The world stands; the seed, not the law, picks its state",
    "p_world": ("Every run starts as a hunter world, the ungrazed start. Seeds 9 and 10 swap: without the law seed 9 settles as a grazer "
                "world by step 50,000 and seed 10 keeps its hunters; under it, the reverse. Each state's share of kills is the same under "
                "both laws, near 16% and near 35%."),
    "p_seeds": ("Over six seeds the hunter world holds on four under both laws: seeds 11, 12 and 14 keep it and 13 stays a grazer world. "
                "The law costs bodies on every seed, 4-18% and 11% on average, the four that keep their state included."),
    "discussion": ("<p>The law is small where it acts. Bodies born in pieces were rare; most pieces came from damage. A push breaks "
                   "surface blocks, which rarely hold two parts together, so a bite cuts little more than it breaks. Wear takes any "
                   "block, and in an old body a worn block is often the only link: it drops 0.3-0.4 more.</p>"
                   "<p>The world has two states after the ungrazed start, and the seed picks one: kills near 16% or near 35% of the "
                   "intake. The law did not change the odds (4 of 6 hunter worlds under both), so a law meant to bring predation must be "
                   "judged over several seeds.</p>"
                   "<p>What this does not show: why the law costs a tenth of the bodies. One reading is that a body in pieces spread its "
                   "gut over more ground; that was not measured. The plan on top changes on four seeds, as a new path of the same world "
                   "does.</p>"),
    "conclusion": ("Kept: a body is what holds together from here (connect 1; 0 keeps e044 byte for byte). The world stands on six seeds "
                   "and the odds of the hunter world are unchanged. Next: #49, plant matter harder to digest than flesh, judged by how "
                   "many of six seeds settle as a hunter world and by the kills' share in each state; these connect runs are its "
                   "control."),
}


if __name__ == "__main__":
    if len(os.sys.argv) > 1 and os.sys.argv[1] == "lineages":
        for label, (r, _, _) in RUNS.items():
            if not exists(r):
                continue
            print(label)
            by = lineage_rows(r)
            top = sorted(by, key=lambda lid: -sum(int(x["size"]) for x in by[lid]))[:6]
            for lid in top:
                rows = by[lid]
                peak = max(rows, key=lambda x: int(x["size"]))
                cells = sum(float(peak[k]) for k in KIND_COLS)
                print(f"  lineage {lid}: {sum(int(x['size']) for x in rows):,} body-samples, {int(rows[0]['step']):,}-{int(rows[-1]['step']):,}, peak {peak['size']} at {int(peak['step']):,}; cells {cells:.0f} mass {float(peak['mass']):.0f} hard {float(peak['hard']):.0f} muscle {float(peak['muscle']):.0f} sensor {float(peak['sensor']):.1f} gut {float(peak['digestive']):.0f} side {float(peak['side']):.0f} len {float(peak['len_fwd']):.1f}x{float(peak['len_side']):.1f} age {float(peak['age']):.0f} meat {float(peak['meat']) / max(float(peak['meat']) + float(peak['plant']), 1e-9):.2f}")
            div, wins = diversity(r)
            print(f"  diversity {div} of {len(wins)} winners: " + "; ".join(f"{i} {s:.0%} {c:.1f} cells" for i, s, c, _ in wins))
    elif len(os.sys.argv) > 1 and os.sys.argv[1] == "numbers":
        numbers()
    else:
        main()
