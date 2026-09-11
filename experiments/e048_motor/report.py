#!/usr/bin/env python3
"""Build report.html for this experiment.

Charts: matplotlib, exported as SVG and inlined. Diagram: hand-written SVG.
Run from the repo root: uv run python experiments/e048_motor/report.py
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
E047 = os.path.join(os.path.dirname(HERE), "e047_corner")  # the control runs live there
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

BASE = "128_sigma0_r64_f0_flat_eyes8_flesh1_w1_season2_digest0_sidegrow_store5_yolk0_breed0_winterhigh_water0.1_leach0.01_depth0.01_mix0.2_strict_sat_hold_wear3000_corner"


def run(law, seed):
    """law 0: e047's corner run (the control, in e047's folder; motor 0 repeats it here on seed 9); 1: the motor."""
    return f"{BASE}{'_motor' if law else ''}_seed{seed}"


def folder(law):
    return HERE if law else E047


LAWS = {0: ("free step (e047)", 5), 1: ("motor", 0)}  # name, color slot
STEPS = 100_000
SEASON = 20_000
LOG = 10_000  # steps per log.csv row
SEEDS = [9, 10, 11, 12, 13, 14]
STATE_LINE = 0.03  # blocks broken per body per step: above it a hunter world (e045: 0.045-0.079, grazer 0.012-0.018)
MUSCLE_FREE = 0.5  # a lineage with a mean muscle under this is muscle-free
GROWN = 1000  # a body this old or older is grown, for `travel`

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
    """The mean of a column over the rows with lo < step <= hi (None if the log has no such column)."""
    if key not in d:
        return None
    idx = half(d, lo, hi)
    return sum(d[key][i] for i in idx) / len(idx) if idx else float("nan")


def lived_births(d, i):
    """The births of log row i that were born with a block (the log's births count the children born without one)."""
    return max(d["births"][i] - d["deaths_body"][i], 1.0)


def eaten(d, i):
    """(plant, flesh of kills, dead scavenged) eaten per step in log row i."""
    hunted = d["kill_gain"][i] * d["cells_broken"][i] / LOG
    return d["plant_intake"][i] / LOG, hunted, d["meat_intake"][i] / LOG - hunted


def muscle_free(run, folder, lo=STEPS // 2, hi=STEPS):
    """The share of the bodies (in lineages of 5 or more) whose lineage has a mean muscle under MUSCLE_FREE, lo < step <= hi."""
    tot = free = 0.0
    for r in load_rows(f"results/{run}_lineages.csv", folder):
        if lo < int(r["step"]) <= hi:
            n = float(r["size"])
            tot += n
            free += n if float(r["muscle"]) < MUSCLE_FREE else 0.0
    return free / max(tot, 1e-9)


def travel(run, folder=HERE, lo=STEPS // 2):
    """The median distance from the birthplace (world cells) of the living bodies aged GROWN or more in the dumps after lo
    (agents.csv is written at step 100,000); None where the run did not record it."""
    path = os.path.join(folder, f"results/{run}_agents.csv")
    if not os.path.exists(path):
        return None
    with open(path) as f:
        rows = csv.DictReader(f)
        if not rows.fieldnames or "travel" not in rows.fieldnames:
            return None
        xs = sorted(float(r["travel"]) for r in rows if int(r["step"]) > lo and int(r["age"]) >= GROWN)
    return xs[len(xs) // 2] if xs else None


AGE_BINS = [(0, 100), (100, 500), (500, 1000), (1000, 2000), (2000, 10**9)]
AGE_NAMES = ["0-99", "100-499", "500-999", "1,000-1,999", "2,000+"]


def travel_by_age(run, folder=HERE):
    """Per age bin, the median distance from the birthplace (world cells) of the bodies alive at step 100,000."""
    with open(os.path.join(folder, f"results/{run}_agents.csv")) as f:
        rows = [r for r in csv.DictReader(f) if int(r["step"]) == STEPS]
    out = []
    for lo, hi in AGE_BINS:
        xs = sorted(float(r["travel"]) for r in rows if lo <= int(r["age"]) < hi)
        out.append(xs[len(xs) // 2] if xs else None)
    return out


def age_chart(title, subtitle, seed):
    """Travel by age on one seed, both laws (the control's from the check run, motor 0 here)."""
    fig, ax = new_axes("age at step 100,000 (steps)")
    for law in LAWS:
        ys = travel_by_age(run(law, seed))
        ax.plot(range(len(AGE_BINS)), ys, color=SERIES[LAWS[law][1]], marker="o", markersize=6, linewidth=1.6, label=LAWS[law][0])
    ax.set_xticks(range(len(AGE_BINS)), AGE_NAMES)
    ax.margins(x=0.05)
    ax.set_ylim(0, None)
    ax.yaxis.set_major_locator(MaxNLocator(4, steps=[1, 2, 5, 10]))
    legend_above(ax, 2)
    return figure(title, subtitle, to_svg(fig))


def stats(law, seed):
    """One run over the second half, or None if it is missing. The control's `moved`, `stalled` and `travel` come from
    the check run (motor 0 here), which exists on seed 9 only."""
    r, fo = run(law, seed), folder(law)
    if not exists(r, fo):
        return None
    d, f = load_csv(f"results/{r}_log.csv", fo), fine(r, fo)
    idx = half(d)
    food = [eaten(d, i) for i in idx]
    plant, hunted, scav = (sum(x[j] for x in food) / len(food) for j in range(3))
    bodies = half_mean(f, "pop")
    broken = half_mean(d, "cells_broken") / LOG
    div, wins = diversity(r, fo)
    w = floors(f)
    moving = d
    if law == 0:
        moving = load_csv(f"results/{r}_log.csv", HERE) if exists(r, HERE) else {}
    return dict(bodies=bodies, floors=[x["pop"] for x in w], floor=min(x["pop"] for x in w),
                births=half_mean(d, "births") / LOG, age=half_mean(f, "age_mean"), lineages=half_mean(f, "lineages"),
                broken=broken, per_body=broken / bodies, hunter=broken / bodies >= STATE_LINE,
                plant=plant, hunted=hunted, scav=scav, share=hunted / (plant + hunted + scav), size=half_mean(d, "size_p50"),
                free=muscle_free(r, fo), muscle=half_mean(d, "muscle_mean"), gut=half_mean(d, "digestive_mean"),
                speed=half_mean(d, "speed_mean"), speed_std=half_mean(d, "speed_std"), forward=half_mean(d, "forward"),
                blocked=half_mean(d, "blocked"), move_spent=half_mean(d, "move_spent"), turns_blocked=half_mean(d, "turns_blocked"),
                moved=half_mean(moving, "moved"), stalled=half_mean(moving, "stalled"),
                travel=travel(r, fo) if law else travel(r, HERE),
                top=top_lineage(r, fo), div=div, wins=len(wins))


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
    """The lineage holding the most body-steps of the last third: (id, share, mean cells, muscle, gut, flesh share, speed)."""
    rows = load_rows(f"results/{run}_lineages.csv", folder)
    steps = [int(r["step"]) for r in rows]
    lo = max(steps) - (max(steps) - min(steps)) // 3
    total, muscle, gut, cells, meat, plant, mass = (defaultdict(float) for _ in range(7))
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
        mass[i] += n * float(r["mass"])
    i = max(total, key=total.get)
    all_n = sum(total.values())
    return (i, total[i] / all_n, cells[i] / total[i], muscle[i] / total[i], gut[i] / total[i], meat[i] / max(meat[i] + plant[i], 1e-9),
            muscle[i] / max(mass[i], 1e-9))


def modal_body(law, seed, lid):
    """The most common grown body of a lineage at its peak: (side, cells, peak row)."""
    r, fo = run(law, seed), folder(law)
    by, bodies = lineage_rows(r, fo), load_bodies(r, fo)
    frames = list(read_frames(f"results/{r}_long.jsonl", fo))
    rows = by[lid]
    peak = max(rows, key=lambda x: int(x["size"]))
    frame = min((fr for fr in frames if any(a[4] == lid for a in fr["agents"])), key=lambda fr: abs(fr["step"] - int(peak["step"])))
    grown = 0.75 * sum(float(peak[k]) for k in KIND_COLS)
    ids = [a[2] for a in frame["agents"] if a[4] == lid]
    c = Counter(i for i in ids if sum(ch != "0" for ch in bodies[i][1]) >= grown) or Counter(ids)
    side, cells = bodies[c.most_common(1)[0][0]]
    return side, cells, peak, rows


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


def seed_chart(title, subtitle, st, key, percent=False, ymax=None, hline=None, fmt=None, laws=(0, 1)):
    """One dot per seed and law: st[law][seed][key]; `hline` draws a dotted reference line."""
    fig, ax = new_axes("seed")
    for law in laws:
        dx = {0: -0.08, 1: 0.08}[law] if len(laws) > 1 else 0.0
        xs = [s + dx for s in SEEDS if st[law][s] and st[law][s][key] is not None]
        ys = [st[law][s][key] for s in SEEDS if st[law][s] and st[law][s][key] is not None]
        ax.plot(xs, ys, color=SERIES[LAWS[law][1]], linestyle="none", marker="o", markersize=7, label=LAWS[law][0])
    if hline is not None:
        ax.axhline(hline, color=INK, linewidth=1, linestyle=":")
    top = max((st[law][s][key] for law in laws for s in SEEDS if st[law][s] and st[law][s][key] is not None), default=1.0)
    ax.set_ylim(0, ymax if ymax is not None else max(top, 1e-9) * 1.15)
    ax.yaxis.set_major_formatter(fmt or ((lambda y, _p: f"{y:.0%}") if percent else kfmt))
    ax.yaxis.set_major_locator(MaxNLocator(4, steps=[1, 2, 5, 10]))
    legend_above(ax, 2)
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
    """picks: [(label, law, seed, lineage id, name, what the shape does)]. The most common grown body of each lineage
    at its peak, on the grid it grew on (drawn at the same width whatever the side), front up."""
    cards = []
    for label, law, seed, lid, name, what in picks:
        side, cells, peak, rows = modal_body(law, seed, lid)
        span = int(rows[-1]["step"]) - int(rows[0]["step"]) + CONFIRM_STEPS
        u = 88 / side
        rects = "".join(f'<rect x="{(i % side) * u:.2f}" y="{(i // side) * u:.2f}" width="{u * 0.9:.2f}" height="{u * 0.9:.2f}" fill="{KIND_COLOR[int(k)]}"/>' for i, k in enumerate(cells) if k != "0")
        m, pl = float(peak["meat"]), float(peak["plant"])
        meat = m / (m + pl) if m + pl > 0 else 0
        speed = float(peak["muscle"]) / max(float(peak["mass"]), 1e-9)
        cards.append(f"""<figure class="card"><svg viewBox="-1 -1 89 89" width="120" height="120" role="img" aria-label="{html.escape(name)}"><rect x="-1" y="-1" width="89" height="89" fill="var(--cell)"/>{rects}<line x1="-1" y1="-0.5" x2="88" y2="-0.5" stroke="var(--ink2)" stroke-width="1.5" stroke-dasharray="3 2"/></svg>
<figcaption><strong>{html.escape(name)}</strong><br>{html.escape(label)}, lineage {lid}: {span:,} steps, {int(peak["size"]):,} agents at its peak<br>grid {side}x{side}; mass {float(peak["mass"]):.0f}: hard {float(peak["hard"]):.0f}, muscle {float(peak["muscle"]):.0f}, sensor {float(peak["sensor"]):.1f}, digestive {float(peak["digestive"]):.0f}; speed {speed:.2f}; flesh {meat:.0%} of the intake; mean age {float(peak["age"]):.0f}<br>{html.escape(what)}</figcaption></figure>""")
    return f"""<figure class="diagram"><div class="cards">{"".join(cards)}</div>
<figcaption>{caption}</figcaption></figure>"""


# ---------- page ----------

CSS = f"""
:root {{
  --surface: #fcfcfb; --page: #f9f9f7; --ink: #0b0b0b; --ink2: #52514e; --grid: #e1e0d9; --border: rgba(11,11,11,0.10);
  --s1: {SERIES[1]}; --cell: #f1f0ea;
}}
@media (prefers-color-scheme: dark) {{
  :root:not([data-theme="light"]) {{
    --surface: #1a1a19; --page: #0d0d0d; --ink: #ffffff; --ink2: #c3c2b7; --grid: #2c2c2a; --border: rgba(255,255,255,0.10);
    --s1: {SERIES[1]}; --cell: #262624;
  }}
}}
:root[data-theme="dark"] {{
  --surface: #1a1a19; --page: #0d0d0d; --ink: #ffffff; --ink2: #c3c2b7; --grid: #2c2c2a; --border: rgba(255,255,255,0.10);
  --s1: {SERIES[1]}; --cell: #262624;
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


def cells_svg(cells, x0, y0, u=20, size=18, **attrs):
    extra = " ".join(f'{k.replace("_", "-")}="{v}"' for k, v in attrs.items())
    return "".join(f'<rect x="{x0 + c * u}" y="{y0 + r * u}" width="{size}" height="{size}" rx="2" {extra}/>' for c, r in cells)


# Hand-written mechanism diagram: a forward action under the two laws, for a body of six blocks with one
# muscle (speed 1/6, e047's mean was 0.13-0.17) and for a body with none. The accent (var(--s1), the
# muscle's color) marks the motor.
_BODY = [(0, 0), (1, 0), (2, 0), (1, 1), (2, 1)]  # five gut blocks, front to the right
_MUSCLE = [(0, 1)]


def _panel(x, title, first, second, mean, bare, blocked_mark):
    arrow = 'marker-end="url(#ah)"'
    bare_line = (f'<line x1="{x + 72}" y1="165" x2="{x + 122}" y2="165" stroke-width="1.5" {arrow}/>' if not blocked_mark else
                 f'<path d="M{x + 90} 157 l16 16 M{x + 106} 157 l-16 16" stroke-width="2" fill="none"/>')
    return f"""
  <g stroke="none">
    <text x="{x}" y="26" font-weight="600">{title}</text>
  </g>
  <g stroke="none" fill="currentColor" fill-opacity="0.28">{cells_svg(_BODY, x, 52)}</g>
  <g stroke="none" fill="var(--s1)">{cells_svg(_MUSCLE, x, 52)}</g>
  <line x1="{x + 72}" y1="60" x2="{x + 122}" y2="60" stroke-width="1.5" {arrow} {'' if first[1] else 'stroke-dasharray="4 3"'}/>
  <line x1="{x + 72}" y1="84" x2="{x + 122}" y2="84" stroke-width="1.5" stroke-dasharray="4 3" {arrow}/>
  <g stroke="none">
    <text x="{x + 134}" y="64">{first[0]}</text>
    <text x="{x + 134}" y="88">2nd sub-cell: chance speed</text>
    <text x="{x}" y="126">a clear forward moves <tspan font-weight="600">{mean}</tspan> sub-cells on average</text>
  </g>
  <g stroke="none" fill="currentColor" fill-opacity="0.28">{cells_svg(_BODY + [(0, 1)], x, 148)}</g>
  {bare_line}
  <g stroke="none">
    <text x="{x + 134}" y="169">{bare}</text>
  </g>"""


DIAGRAM = f"""
<figure class="fig diagram">
<svg viewBox="0 0 900 236" width="100%" role="img" aria-label="A forward action under the two laws: in e047 the first sub-cell of a clear way is always taken and a body without muscle walks; under the motor every sub-cell happens with chance speed, muscle over mass, and a body without muscle stays" font-size="12" fill="currentColor" stroke="currentColor">
  <defs><marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0 L10 5 L0 10 z" fill="currentColor" stroke="none"/></marker></defs>
  {_panel(30, "motor 0: e047's free step", ("1st sub-cell: always, if the way is clear", True), None, "1.17", "no muscle: walks all the same", False)}
  <line x1="450" y1="14" x2="450" y2="196" stroke-opacity="0.3"/>
  {_panel(480, "motor 1: this experiment", ("1st sub-cell: chance speed", False), None, "0.19", "no muscle: speed 0, never steps or turns", True)}
  <g stroke="none"><text x="30" y="222" font-size="11">speed = muscle / mass: here one muscle block (orange) of six, 1/6. A turn needs the motor too under the law.</text></g>
</svg>
<figcaption>Figure 1. A forward action under the two laws. Solid arrows always happen, dashed ones with chance speed. The press on a body in the way, the shove and the price of moving (mass times distance) do not change.</figcaption>
</figure>
"""


TEXT = {}  # filled in main(); counted at the end


def all_stats():
    return {law: {s: stats(law, s) for s in SEEDS} for law in LAWS}


def fmt_opt(v, f):
    return "-" if v is None else f(v)


def numbers():
    """The measures over the second half, per run (for the README)."""
    st = all_stats()
    for s in SEEDS:
        for law in LAWS:
            x = st[law][s]
            if not x:
                continue
            i, share, cells, muscle, gut, meat, speed = x["top"]
            print(f"seed {s} {LAWS[law][0]:16s} {'HUNTER' if x['hunter'] else 'grazer'} broken/body {x['per_body']:.4f} kills {x['share']:.1%} "
                  f"| bodies {x['bodies']:.0f} floors {x['floors']} births {x['births']:.2f} age {x['age']:.0f} lineages {x['lineages']:.1f} size p50 {x['size']:.1f}")
            print(f"      muscle-free {x['free']:.0%} muscle {x['muscle']:.2f} gut {x['gut']:.2f} speed {x['speed']:.3f} (sd {x['speed_std']:.3f}) "
                  f"| forward {x['forward']:.2f} blocked {x['blocked']:.2f} stalled {fmt_opt(x['stalled'], lambda v: f'{v:.2f}')} turns blocked {x['turns_blocked']:.2f} "
                  f"moved {fmt_opt(x['moved'], lambda v: f'{v:.3f}')} move_spent {x['move_spent']:.4f} travel {fmt_opt(x['travel'], lambda v: f'{v:.1f}')}")
            print(f"      top {i} {share:.0%} {cells:.1f} cells {muscle:.1f} muscle {gut:.1f} gut {meat:.0%} flesh speed {speed:.2f} | diversity {x['div']} of {x['wins']}")
    for law in LAWS:
        xs = [st[law][s] for s in SEEDS if st[law][s]]
        print(f"{LAWS[law][0]}: hunter worlds {sum(x['hunter'] for x in xs)} of {len(xs)}; bodies {sum(x['bodies'] for x in xs) / max(len(xs), 1):.0f}")


def main():
    st = all_stats()
    logs = {s: load_csv(f"results/{run(1, s)}_log.csv") for s in SEEDS if st[1][s]}
    small = lambda y, _p: f"{y:.3f}".rstrip("0").rstrip(".") if y else "0"

    charts_motor = [
        seed_chart("Bodies in muscle-free lineages, by seed", "Share of the bodies whose lineage carries under half a muscle block on average, second half.",
                   st, "free", percent=True, ymax=1.0),
        seed_chart("Speed, by seed", "Muscle over mass per body, second half: under the law, the chance that a stroke of the motor happens.",
                   st, "speed", fmt=lambda y, _p: f"{y:.2f}"),
    ]
    charts_move = [
        seed_chart("The work of moving, by seed", "Energy paid for moving per body per step, second half: mass times the sub-cells moved.",
                   st, "move_spent", fmt=small),
        age_chart("How far a body stands from where it was born, seed 9", "Median distance in world cells of the bodies alive at step 100,000, by their age. A flat line would be a body that never leaves.", 9),
    ]
    charts_world = [
        seed_chart("Bodies, by seed", "Bodies alive over the second half (steps 50,000-100,000).", st, "bodies"),
        seed_chart("The flesh of kills in what the bodies eat, by seed", "Second half. Two levels, one per state: the seed picks the level.",
                   st, "share", percent=True, ymax=0.5),
    ]

    def top_text(t):
        _i, share, cells, muscle, gut, meat, speed = t
        return f"{share:.0%}: {cells:.0f} cells, {muscle:.0f} muscle, {gut:.0f} gut, speed {speed:.2f}, {meat:.0%} flesh"

    def pair(s, key, f):
        a, b = st[0][s], st[1][s]
        return f"<td>{f(a[key])} / {f(b[key])}</td>"

    state = lambda h: "hunter" if h else "grazer"
    seed_rows = "".join(
        f"<tr><td>{s}</td>{pair(s, 'free', lambda v: f'{v:.0%}')}{pair(s, 'speed', lambda v: f'{v:.2f}')}{pair(s, 'move_spent', lambda v: f'{v:.4f}')}"
        f"{pair(s, 'bodies', lambda v: f'{v:,.0f}')}{pair(s, 'floor', lambda v: f'{v:,}')}{pair(s, 'hunter', state)}{pair(s, 'share', lambda v: f'{v:.0%}')}"
        f"{pair(s, 'div', lambda v: f'{v}')}<td>{top_text(st[0][s]['top'])}</td><td>{top_text(st[1][s]['top'])}</td></tr>"
        for s in SEEDS if st[0][s] and st[1][s])
    tables = data_table(["step", "pop", "births", "deaths_energy", "deaths_broken", "deaths_wear", "cells_broken", "plant_intake", "meat_intake",
                         "muscle_mean", "speed_mean", "speed_std", "forward", "blocked", "stalled", "moved", "move_spent", "turns_blocked", "size_p50"],
                        {f"{LAWS[1][0]}, seed {s}": d for s, d in logs.items()})
    TEXT.update(TEXTS)
    TEXT["gallery"] = gallery(GALLERY, GALLERY_CAPTION) if GALLERY else ""
    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>e048 Moving takes a motor - Report</title>
<style>{CSS}</style>
</head>
<body>
<main>
<h1>e048: Moving takes a motor</h1>
<p class="sub">Experiment report - 2026-09-11 - every change of a body's position needs its muscle (#51), against e047's corner runs on seeds 9-14. Answer: {TEXT["sub_answer"]}</p>

<section class="tldr">
<h2>TL;DR</h2>
<p>{TEXT["tldr"]}</p>
</section>

<h2>1. Question</h2>
<p>{TEXT["question"]}</p>
<ol>
  <li><strong>The motor is selected:</strong> muscle-free lineages hold under 10% of the bodies on at least five seeds, and speed rises above e047's 0.13-0.17 on every seed.</li>
  <li><strong>Bodies move less, not more:</strong> the work of moving per body per step falls below half of e047's on at least five seeds.</li>
  <li><strong>The world stands, with fewer bodies:</strong> 10-30% fewer on at least four seeds, the lowest winter floor above 200, the hunter world on at least four.</li>
</ol>

<h2>2. The law</h2>
<p>{TEXT["world"]}</p>
{DIAGRAM}
<p><strong>Runs.</strong> {TEXT["runs"]}</p>
<ul class="measures">
  <li><strong>muscle-free</strong> - the share of the bodies in lineages whose mean muscle is under half a block.</li>
  <li><strong>speed</strong> - muscle over mass, per body; under the law, the chance of a stroke.</li>
  <li><strong>work of moving</strong> - energy paid for moving per body per step (mass times sub-cells).</li>
  <li><strong>travel</strong> - how far a body aged 1,000 steps or more stands from its birthplace (median).</li>
  <li><strong>state</strong> - the flesh of kills in what the bodies eat; blocks broken per body per step over 0.03 is a hunter world.</li>
  <li><strong>top lineage, diversity</strong> - the lineage with the most of the last third, and the diversity number (#42).</li>
</ul>

<h2>3. Results</h2>
<p>Means over the second half (steps 50,000-100,000); each pair is free step (e047) / motor.</p>
<div class="tw"><table>
<thead><tr><th>seed</th><th>muscle-free</th><th>speed</th><th>work of moving</th><th>bodies</th><th>lowest floor</th><th>state</th><th>kills' share</th><th>diversity</th><th>top lineage of the last third, free step</th><th>motor</th></tr></thead>
<tbody>{seed_rows}</tbody></table></div>
<ol class="verdicts">
{TEXT["verdicts"]}
</ol>

<h3>3.1 {TEXT["h_motor"]}</h3>
<div class="grid2">
{"".join(charts_motor)}
</div>
<p>{TEXT["p_motor"]}</p>
{TEXT["gallery"]}

<h3>3.2 {TEXT["h_move"]}</h3>
<div class="grid2">
{"".join(charts_move)}
</div>
<p>{TEXT["p_move"]}</p>

<h3>3.3 {TEXT["h_world"]}</h3>
<div class="grid2">
{"".join(charts_world)}
</div>
<p>{TEXT["p_world"]}</p>

<h2>4. Discussion</h2>
{TEXT["discussion"]}

<h2>5. Conclusion and next step</h2>
<p>{TEXT["conclusion"]}</p>

<h2>Appendix: data</h2>
<p>Every log step (10,000 steps) of the six runs under the law; the control's are in e047's report. The full data are in <code>results/*.csv</code>. Build this report with <code>uv run python experiments/e048_motor/report.py</code>.</p>
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
    ("motor, seed 12", 1, 12, 67, "the ram with a motor", "A wall of hard at the front, two rows of gut, three rows of muscle behind: it pushes by the line and steps a quarter of its tries. It held seed 12 from step 9,000 to the end."),
    ("motor, seed 9", 1, 9, 325, "the armored hunter", "Hard across the front and down the sides, gut inside, four rows of muscle at the back: half of what it eats is flesh."),
    ("motor, seed 11", 1, 11, 1521, "the pusher", "Two rows of muscle in front of two rows of gut, no hard: a grazer that steps a fifth of its tries."),
    ("motor, seed 13", 1, 13, 419, "the sandwich", "Gut at the front and the back, two rows of muscle between: a 16-block grazer, the second body of seed 13."),
    ("motor, seed 10", 1, 10, 382, "the runner", "Muscle over most of its grid, a few gut blocks and an eye at the front corner: speed 0.23, alive from step 24,000 to the end."),
    ("motor, seed 10", 1, 10, 677, "the two triangles", "Gut in one triangle of its grid, muscle in the other, an eye on the line between: the winner of seed 10's grazer world."),
]
GALLERY_CAPTION = ("The usual grown body of six leading lineages under the law, front up (orange muscle, aqua gut, yellow sensor, blue hard). "
                   "Every one carries a motor; the hunters are heavier and faster than the grazers.")

TEXTS = {
    "sub_answer": ("every lineage carries a motor on all six seeds and speed rises on each, but the bodies move about a third as far. "
                   "The world stands; it has fewer bodies on three seeds, and the hunter world on three. Kept."),
    "tldr": ("A body now needs muscle to step or turn: each sub-cell happens with chance muscle over mass. On all six seeds no lineage "
             "is muscle-free (e047: 21-55% of the bodies), and speed rises on every seed. Every body carries a motor and moves less: on "
             "seed 9 a body moves 0.09 sub-cells a step against 0.30, and grown bodies stand 13 world cells from their birthplace "
             "against 38. Kept. Next: #14, a band of rain that makes moving pay."),
    "question": ("Until now a clear forward moved any body one sub-cell, whatever it was made of; muscle only added a second sub-cell "
                 "and the force of a push. So a body without a motor walked, and muscle-free lineages held 21-55% of the bodies in "
                 "e047. The user asked that moving need blocks made for it, more of them faster (#51). Muscle should pay when a step "
                 "needs it and a grazed cell under a body does not regrow, which is already the world's law."),
    "world": ("Under motor 1 every change of position needs the motor. Each sub-cell of a forward action happens with chance speed, "
              "muscle over mass, and so does a turn. A body without muscle neither steps nor turns, though it can be shoved. The "
              "press, the shove and the price of moving are unchanged; a forward that moves nothing costs nothing."),
    "runs": ("e047's world with corners holding, seeds 9-14, 100,000 steps under motor 1, against e047's corner runs, which motor 0 "
             "repeats byte for byte (checked on seed 9; that run also gives the control's distances). Six runs at once, 21 minutes. "
             "Six seeds, because the seed picks the world's state."),
    "verdicts": ("<li><span class=\"verdict\">Yes</span> No lineage is muscle-free on any seed (e047: 21-55% of the bodies), and "
                 "speed rises on all six against the control, to 0.16-0.25.</li>"
                 "<li><span class=\"verdict partly\">Partly</span> The work of moving falls 39-76% on every seed, but below half on "
                 "four, not five: bodies are heavier. Distance falls more: 0.09 sub-cells a step against 0.30 (seed 9).</li>"
                 "<li><span class=\"verdict partly\">Partly</span> The world stands (lowest floor 347), but bodies change by -21% to "
                 "+36%, 10-30% fewer on three seeds, and the hunter world comes on three, not four.</li>"),
    "h_motor": "Every body carries a motor",
    "p_motor": ("Lineages without muscle are gone within the first half-winter: by step 10,000 bodies carry 6-9 muscle blocks. The "
                "6-18% of the bodies alive at the end with no muscle are single bodies (damaged or mutant), not lineages. Speed rises "
                "and its spread narrows (standard deviation 0.07-0.16 against 0.12-0.19): the free step's mix of motorless bodies and "
                "a few fast ones becomes one range of motors."),
    "h_move": "Every body moves less",
    "p_move": ("On seed 9 a body moves 0.09 sub-cells a step against 0.30, and stands half as far from its birthplace when young and "
               "a third as far when grown. Bodies are heavier (16-25 blocks against 9-20), so the work of moving falls less than the "
               "distance. A third to half of the forward tries with a clear way are stalled; the policy still asks for forward "
               "68-91% of the time."),
    "h_world": "The world stands; the hunter world comes on three seeds",
    "p_world": ("Bodies fall on seeds 9, 12 and 14 (16-21%) and change little or rise on the others (seed 11: +36%): 2,273 against "
                "2,420 on average. Seeds 11 and 14 lose the hunter world: kills fall to 9-10% of the intake, and their winners are "
                "14-block grazers with 5 muscle. Seed 13 sits at the line between the states under both laws."),
    "discussion": ("<p>The motor is selected fast and everywhere, but not because moving pays more than before. A body without muscle "
                   "can no longer leave the cells it has grazed bare, which do not regrow under it: a motor is the price of eating at "
                   "all. What the law buys is a body that says whether it moves. The hunters carry 9-10 muscle blocks at speed "
                   "0.24-0.26, the grazers 5-7.5 at 0.17-0.18.</p>"
                   "<p>It does not answer the complaint that the world does not move. Bodies moved 0.30 sub-cells a step under the free "
                   "step and 0.06-0.09 now. Nothing asks them to go far: food regrows everywhere at the sun's rate, so a slow motor "
                   "reaches enough of it. Speed should pay only where the food moves, which is what #14's band of rain gives.</p>"
                   "<p>What this does not show: why two hunter worlds became grazer worlds (a slower hunter, or prey that now carry "
                   "muscle, is not measured), and whether a leg kind would split walking from pushing (#52).</p>"),
    "conclusion": ("Kept: from here a step and a turn need the motor (motor 1 is the next experiment's default). It is the physics "
                   "the user asked for, and the build now says what a body does: no body walks without muscle, and speed is a trait "
                   "that differs. The world moves a third as far, so a reason to move is the missing condition. Next: #14, a band of "
                   "rain that crosses the world slowly, under this law."),
}


if __name__ == "__main__":
    if len(os.sys.argv) > 1 and os.sys.argv[1] == "lineages":
        for law in LAWS:
            for s in SEEDS:
                r, fo = run(law, s), folder(law)
                if not exists(r, fo):
                    continue
                print(f"{LAWS[law][0]}, seed {s}")
                by = lineage_rows(r, fo)
                top = sorted(by, key=lambda lid: -sum(int(x["size"]) for x in by[lid]))[:5]
                for lid in top:
                    rows = by[lid]
                    peak = max(rows, key=lambda x: int(x["size"]))
                    side, cells, _, _ = modal_body(law, s, lid)
                    print(f"  lineage {lid}: {sum(int(x['size']) for x in rows):,} body-samples, {int(rows[0]['step']):,}-{int(rows[-1]['step']):,}, peak {peak['size']} at {int(peak['step']):,}; "
                          f"muscle {float(peak['muscle']):.0f} gut {float(peak['digestive']):.0f} hard {float(peak['hard']):.0f} speed {float(peak['muscle']) / float(peak['mass']):.2f}; modal body side {side} cells {cells}")
                div, wins = diversity(r, fo)
                print(f"  diversity {div} of {len(wins)} winners: " + "; ".join(f"{i} {sh:.0%} {c:.1f} cells" for i, sh, c, _ in wins))
    elif len(os.sys.argv) > 1 and os.sys.argv[1] == "numbers":
        numbers()
    else:
        main()
