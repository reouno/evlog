#!/usr/bin/env python3
"""Build report.html for this experiment.

Charts: matplotlib, exported as SVG and inlined. Diagram: hand-written SVG.
Run from the repo root: uv run python experiments/e051_leave/report.py
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
E048 = os.path.join(os.path.dirname(HERE), "e048_motor")  # neither law: the old brain, stock 0
E050 = os.path.join(os.path.dirname(HERE), "e050_brain")  # the brain alone, in e048's world
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

BASE = "128_sigma0_r64_f0_flat_eyes8_flesh1_w1_season2_digest0_sidegrow_store5_yolk0_breed0_winterhigh_water0.1_leach0.01_depth0.01_mix0.2"
TAIL = "_strict_sat_hold_wear3000_corner_motor"
STOCKS = {0: "", 1: "", 2: "1", 3: "1", 4: "4", 5: "4"}  # the knee of each law ("": no stock law)


def name(stock="", seed=9, brain=False):
    """A run's file prefix: e048's world with `stock` (the knee, "" for none) and the brain."""
    return f"{BASE}{'_stock' + stock if stock else ''}{TAIL}{'_brain' if brain else ''}_seed{seed}"


def run(law, seed):
    """law 0: neither law (e048's motor runs); 1: the brain alone (e050's runs in e048's world); 2 and 3: `stock` 1
    with the old brain and with the brain; 4 and 5: `stock` 4, the same."""
    return name(STOCKS[law], seed, law % 2 == 1)


def folder(law):
    return {0: E048, 1: E050}.get(law, HERE)


LAWS = {0: ("neither law", 5), 1: ("brain alone", 6), 2: ("stock 1", 3), 3: ("stock 1 + brain", 0),
        4: ("stock 4", 1), 5: ("stock 4 + brain", 2)}  # name, color slot
BRAIN = (1, 3, 5)
OLD = (0, 2, 4)
STEPS = 100_000
SEASON = 20_000
LOG = 10_000  # steps per log.csv row
SEEDS = [9, 10, 11, 12]
STATE_LINE = 0.03  # blocks broken per body per step: above it a hunter world (e045: 0.045-0.079, grazer 0.012-0.018)
GROWN = 1000  # a body this old or older is grown, for `travel`
BOTH = 0.05  # the giving-up densities are compared over the log rows where learners and the rest each hold this share

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
    """The rows with lo < step <= hi, but the row a world writes as it dies (no bodies left)."""
    return [i for i, t in enumerate(d["step"]) if lo < t <= hi and d["pop"][i] > 0]


def half_mean(d, key, lo=STEPS // 2, hi=STEPS):
    """The mean of a column over the rows with lo < step <= hi (None if the log has no such column)."""
    if key not in d:
        return None
    idx = half(d, lo, hi)
    return sum(d[key][i] for i in idx) / len(idx) if idx else float("nan")


def eaten(d, i):
    """(plant, flesh of kills, dead scavenged) eaten per step in log row i."""
    hunted = d["kill_gain"][i] * d["cells_broken"][i] / LOG
    return d["plant_intake"][i] / LOG, hunted, d["meat_intake"][i] / LOG - hunted


def median(xs):
    xs = sorted(xs)
    return xs[len(xs) // 2] if xs else None


def agents_rows(run, folder=HERE):
    """The bodies alive at step 100,000 (agents.csv is written there), or none."""
    path = os.path.join(folder, f"results/{run}_agents.csv")
    if not os.path.exists(path):
        return []
    with open(path) as f:
        return [r for r in csv.DictReader(f) if int(r["step"]) == STEPS]


def travel(run, folder=HERE):
    """(median distance from the birthplace in world cells, how many) of the bodies aged GROWN or more at step 100,000."""
    xs = [float(r["travel"]) for r in agents_rows(run, folder) if int(r["age"]) >= GROWN]
    return median(xs), len(xs)


def gud(d):
    """Over the log rows of the second half where learners and the rest each hold at least BOTH of the bodies: the mean
    food left on a cell as a gut moves off it and under the guts as the body acts, learners and the rest. None where
    the log has no such rows (the old brain; a run won by one group)."""
    if "gud_learn" not in d:
        return None
    idx = [i for i in half(d) if BOTH <= d["learners"][i] <= 1 - BOTH]
    if not idx:
        return None
    m = lambda k: sum(d[k][i] for i in idx) / len(idx)
    return dict(learn=m("gud_learn"), rest=m("gud_rest"), under_learn=m("under_learn"), under_rest=m("under_rest"),
                left_learn=m("left_learn"), left_rest=m("left_rest"), rows=len(idx))


def stats(law, seed):
    """One run over the second half, or None if it is missing."""
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
    died = int(d["step"][-1]) if d["pop"][-1] == 0 else None  # the step the world died at, if it did
    floor = 0 if died else min(x["pop"] for x in w)
    tr, grown = travel(r, fo)
    # Under the old brain the genome still carries a learning rate, but nothing learns: no learners, one group.
    brain = law in BRAIN
    g = gud(d) if brain else None
    mind = lambda k: half_mean(d, k) if brain else None
    return dict(learners=mind("learners"), eta=mind("eta"), learned=mind("learned"), memory=mind("memory"),
                eyed=half_mean(d, "eyed"), bodies=bodies, floors=[x["pop"] for x in w], floor=floor, died=died,
                floor_txt=f"died at {died:,}" if died else f"{floor:,}", births=half_mean(d, "births") / LOG,
                age=half_mean(f, "age_mean"), lineages=half_mean(f, "lineages"), broken=broken, per_body=broken / bodies,
                hunter=broken / bodies >= STATE_LINE, plant=plant, hunted=hunted, scav=scav, share=hunted / (plant + hunted + scav),
                size=half_mean(d, "size_p50"), muscle=half_mean(d, "muscle_mean"), gut=half_mean(d, "digestive_mean"),
                speed=half_mean(d, "speed_mean"), moved=half_mean(d, "moved"), stalled=half_mean(d, "stalled"),
                blocked=half_mean(d, "blocked"), forward=half_mean(d, "forward"), stay=half_mean(d, "stay"),
                bare=half_mean(d, "bare"), grazed=half_mean(d, "grazed"), trees=half_mean(d, "trees"),
                tree_eaten=half_mean(d, "tree_eaten"), regrowth=half_mean(d, "regrowth"), mean_res=half_mean(d, "mean_res"),
                travel=tr, grown=grown, gud=g, gud_learn=g and g["learn"], gud_ratio=g and g["learn"] / g["rest"], gud_rest=(g["rest"] if g else half_mean(d, "gud_rest")),
                under_rest=(g["under_rest"] if g else half_mean(d, "under_rest")), left_rest=(g["left_rest"] if g else half_mean(d, "left_rest")),
                top=top_lineage(r, fo), div=div, wins=len(wins))


# ---------- the diversity number (#42), copied from e039 ----------
# The winners of a window are the lineages holding at least WIN_SHARE of its body-steps. Two
# winners are the same body when their sizes are within SIZE_FACTOR and the mixes of their blocks
# differ by at most MIX_DIST in sum; single linkage on that relation, the number of groups.
WIN_SHARE = 0.05
SIZE_FACTOR = 1.5
MIX_DIST = 0.4
KIND_COLS = ["hard", "muscle", "sensor", "digestive"]


def same_body(a, b):
    """Two mean bodies (counts by kind) are the same shape."""
    sa, sb = sum(a), sum(b)
    if sa <= 0 or sb <= 0:
        return False
    if max(sa, sb) > SIZE_FACTOR * min(sa, sb):
        return False
    return sum(abs(x / sa - y / sb) for x, y in zip(a, b)) <= MIX_DIST


def diversity(run, folder=HERE):
    """(diversity, winners): the groups of winner bodies, and the winners, over the last third."""
    rows = load_rows(f"results/{run}_lineages.csv", folder)
    if not rows:
        return 0, []
    steps = [int(r["step"]) for r in rows]
    lo, hi = max(steps) - (max(steps) - min(steps)) // 3, max(steps)
    total, shape = defaultdict(float), defaultdict(lambda: [0.0] * len(KIND_COLS))
    for r in rows:
        if not lo <= int(r["step"]) <= hi:
            continue
        n = float(r["size"])
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
        ax.margins(x=0.08)
    return fig, ax


def legend_above(ax, n):
    ax.legend(loc="lower left", bbox_to_anchor=(0, 1.0), ncols=n, handlelength=1.8, borderaxespad=0, columnspacing=1.2)


def seed_chart(title, subtitle, st, key, laws=(0, 1, 2, 3), percent=False, ymax=None, hline=None, fmt=None):
    """One dot per seed and law: st[law][seed][key]; `hline` draws a dotted reference line."""
    fig, ax = new_axes("seed")
    for k, law in enumerate(laws):
        dx = (k - (len(laws) - 1) / 2) * 0.12
        pts = [(s + dx, st[law][s][key]) for s in SEEDS if st[law][s] and st[law][s][key] is not None]
        ax.plot([p[0] for p in pts], [p[1] for p in pts], color=SERIES[LAWS[law][1]], linestyle="none", marker="o", markersize=7, label=LAWS[law][0])
    if hline is not None:
        ax.axhline(hline, color=INK, linewidth=1, linestyle=":")
    vals = [st[law][s][key] for law in laws for s in SEEDS if st[law][s] and st[law][s][key] is not None] + ([hline] if hline is not None else [])
    top, low = max(vals, default=1.0), min(vals + [0.0])
    ax.set_ylim(low * 1.15, ymax if ymax is not None else max(top, 1e-9) * 1.15)
    ax.set_xticks(SEEDS)
    ax.yaxis.set_major_formatter(fmt or ((lambda y, _p: f"{y:.0%}") if percent else kfmt))
    ax.yaxis.set_major_locator(MaxNLocator(4, steps=[1, 2, 5, 10]))
    legend_above(ax, len(laws))
    return figure(title, subtitle, to_svg(fig))


def ratio_chart(title, subtitle, st, key, laws, own=False):
    """One dot per seed and law: st[law][seed][key] over the same seed and brain without the law (law 0 or 1), or,
    with `own`, the value itself; the dotted line at 1."""
    fig, ax = new_axes("seed")
    vals = []
    for k, law in enumerate(laws):
        dx = (k - (len(laws) - 1) / 2) * 0.12
        base = 0 if law in OLD else 1
        pts = []
        for s in SEEDS:
            x, b = st[law][s], st[base][s]
            if not x or x[key] is None:
                continue
            v = x[key] if own else (x[key] / b[key] if b and b[key] else None)
            if v is not None and v == v:
                pts.append((s + dx, v))
        vals += [p[1] for p in pts]
        ax.plot([p[0] for p in pts], [p[1] for p in pts], color=SERIES[LAWS[law][1]], linestyle="none", marker="o", markersize=7, label=LAWS[law][0])
    ax.axhline(1, color=INK, linewidth=1, linestyle=":")
    ax.set_ylim(0, max(vals + [1.0]) * 1.15)
    ax.set_xticks(SEEDS)
    ax.yaxis.set_major_formatter(lambda y, _p: f"{y:g}x")
    ax.yaxis.set_major_locator(MaxNLocator(4, steps=[1, 2, 5, 10]))
    legend_above(ax, len(laws))
    return figure(title, subtitle, to_svg(fig))


def time_chart(title, subtitle, key, laws, hline=None):
    """One line per run of a log column every 10,000 steps (a share), colored by law."""
    fig, ax = new_axes("step")
    for law in laws:
        first = True
        for s in SEEDS:
            r, fo = run(law, s), folder(law)
            if not exists(r, fo):
                continue
            d = load_csv(f"results/{r}_log.csv", fo)
            ax.plot(d["step"], d[key], color=SERIES[LAWS[law][1]], linewidth=1.5, alpha=0.9, label=LAWS[law][0] if first else None)
            first = False
    if hline is not None:
        ax.axhline(hline, color=INK, linewidth=1, linestyle=":")
    ax.set_ylim(0, 1)
    ax.yaxis.set_major_formatter(lambda y, _p: f"{y:.0%}")
    ax.yaxis.set_major_locator(MaxNLocator(4, steps=[1, 2, 5, 10]))
    legend_above(ax, len(laws))
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
    for name_, d in rows_by_name.items():
        cs = [c for c in cols if c in d]
        rows = "".join("<tr>" + "".join(f"<td>{d[c][i]:g}</td>" for c in cs) + "</tr>" for i in range(0, len(d[cs[0]]), every))
        out.append(f"<details><summary>{html.escape(name_)}</summary><div class='tw'><table><thead><tr>"
                   + "".join(f"<th>{c}</th>" for c in cs) + f"</tr></thead><tbody>{rows}</tbody></table></div></details>")
    return "\n".join(out)


def gallery(picks, caption):
    """picks: [(label, law, seed, lineage id, name, what the shape does)]. The most common grown body of each lineage
    at its peak, on the grid it grew on (drawn at the same width whatever the side), front up."""
    cards = []
    for label, law, seed, lid, title, what in picks:
        side, cells, peak, rows = modal_body(law, seed, lid)
        span = int(rows[-1]["step"]) - int(rows[0]["step"]) + CONFIRM_STEPS
        u = 88 / side
        rects = "".join(f'<rect x="{(i % side) * u:.2f}" y="{(i // side) * u:.2f}" width="{u * 0.9:.2f}" height="{u * 0.9:.2f}" fill="{KIND_COLOR[int(k)]}"/>' for i, k in enumerate(cells) if k != "0")
        m, pl = float(peak["meat"]), float(peak["plant"])
        meat = m / (m + pl) if m + pl > 0 else 0
        speed = float(peak["muscle"]) / max(float(peak["mass"]), 1e-9)
        cards.append(f"""<figure class="card"><svg viewBox="-1 -1 89 89" width="120" height="120" role="img" aria-label="{html.escape(title)}"><rect x="-1" y="-1" width="89" height="89" fill="var(--cell)"/>{rects}<line x1="-1" y1="-0.5" x2="88" y2="-0.5" stroke="var(--ink2)" stroke-width="1.5" stroke-dasharray="3 2"/></svg>
<figcaption><strong>{html.escape(title)}</strong><br>{html.escape(label)}, lineage {lid}: {span:,} steps, {int(peak["size"]):,} agents at its peak<br>grid {side}x{side}; mass {float(peak["mass"]):.0f}: hard {float(peak["hard"]):.0f}, muscle {float(peak["muscle"]):.0f}, sensor {float(peak["sensor"]):.1f}, digestive {float(peak["digestive"]):.0f}; speed {speed:.2f}; flesh {meat:.0%} of the intake; mean age {float(peak["age"]):.0f}<br>{html.escape(what)}</figcaption></figure>""")
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
    --s1: {SERIES[0]}; --cell: #262624;
  }}
}}
:root[data-theme="dark"] {{
  --surface: #1a1a19; --page: #0d0d0d; --ink: #ffffff; --ink2: #c3c2b7; --grid: #2c2c2a; --border: rgba(255,255,255,0.10);
  --s1: {SERIES[0]}; --cell: #262624;
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
th, td {{ padding: 6px 10px; text-align: right; border-bottom: 1px solid var(--grid); }}
td {{ white-space: nowrap; }}
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


# Hand-written mechanism diagram: the light a cell grows by (its own and its crown's) passes the
# law's gate (the accent), the rest is lost; the plant is eaten by the guts of a body on the cell,
# which stops its growth; when the body moves on, the food it leaves is the giving-up density.
DIAGRAM = """
<figure class="fig diagram">
<svg viewBox="0 0 880 236" width="100%" role="img" aria-label="The light a cell grows by passes the stock law: it is used in the share the plant stands of the knee, at least a tenth, and the rest is lost; the plant is eaten by the guts of a body standing on it, which stops its growth; the food a body leaves when it moves on is the giving-up density" font-size="12" fill="currentColor" stroke="currentColor">
  <defs><marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0 L10 5 L0 10 z" fill="var(--s1)" stroke="none"/></marker>
  <marker id="ai" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0 L10 5 L0 10 z" fill="currentColor" stroke="none"/></marker></defs>
  <rect x="16" y="24" width="236" height="46" rx="6" fill="none" stroke-opacity="0.6"/>
  <rect x="16" y="112" width="236" height="46" rx="6" fill="none" stroke-opacity="0.6"/>
  <path d="M252,47 L318,80" fill="none" stroke-width="1.4" marker-end="url(#ai)"/>
  <path d="M252,135 L318,104" fill="none" stroke-width="1.4" marker-end="url(#ai)"/>
  <rect x="320" y="64" width="196" height="56" rx="10" fill="none" stroke="var(--s1)" stroke-width="2.2"/>
  <path d="M516,92 L576,92" fill="none" stroke="var(--s1)" stroke-width="2" marker-end="url(#ah)"/>
  <path d="M418,120 L418,170" fill="none" stroke-width="1.4" stroke-dasharray="4 3" marker-end="url(#ai)"/>
  <rect x="578" y="66" width="132" height="52" rx="6" fill="none" stroke-opacity="0.6"/>
  <path d="M710,92 L748,92" fill="none" stroke-width="1.4" marker-end="url(#ai)"/>
  <rect x="750" y="66" width="114" height="52" rx="6" fill="none" stroke-opacity="0.6"/>
  <path d="M807,118 L807,176" fill="none" stroke-width="1.4" marker-end="url(#ai)"/>
  <g stroke="none">
    <text x="26" y="43">the cell's own sun, less what</text>
    <text x="26" y="60">the crowns of taller cells take</text>
    <text x="26" y="131">its crown: sun from the cells around,</text>
    <text x="26" y="148">as far as its column is tall</text>
    <text x="418" y="87" text-anchor="middle" fill="var(--s1)">used: x min(1, res / stock)</text>
    <text x="418" y="105" text-anchor="middle" fill="var(--s1)">never below 0.1</text>
    <text x="546" y="84" text-anchor="middle">grows</text>
    <text x="418" y="190" text-anchor="middle">the rest is lost (bare)</text>
    <text x="644" y="88" text-anchor="middle">the plant on</text>
    <text x="644" y="104" text-anchor="middle">the cell (res)</text>
    <text x="729" y="84" text-anchor="middle">eaten</text>
    <text x="807" y="88" text-anchor="middle">the guts of</text>
    <text x="807" y="104" text-anchor="middle">a body on it</text>
    <text x="644" y="140" text-anchor="middle">no growth while a</text>
    <text x="644" y="156" text-anchor="middle">body stands on it</text>
    <text x="864" y="196" text-anchor="end">it moves on: the food it leaves</text>
    <text x="864" y="213" text-anchor="end">is the giving-up density</text>
  </g>
</svg>
<figcaption>Figure 1. What stock changes. A gut eats up to 0.02 a step. At stock 1 a standing tree (1 or more) is untouched and a bare cell stands at 1 again in about 330 steps at full sun (100 without the law); at 4 every tree below 4 grows slower too.</figcaption>
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
    f4 = lambda v: f"{v:.4f}"
    f2 = lambda v: f"{v:.2f}"
    pc = lambda v: f"{v:.1%}"
    for s in SEEDS:
        for law in LAWS:
            x = st[law][s]
            if not x:
                continue
            i, share, cells, muscle, gut, meat, speed = x["top"]
            print(f"seed {s} {LAWS[law][0]:14s} {'HUNTER' if x['hunter'] else 'grazer'} floor {x['floor_txt']} floors {x['floors']} broken/body {x['per_body']:.4f} kills {x['share']:.1%} "
                  f"| bodies {x['bodies']:.0f} births {x['births']:.2f} age {x['age']:.0f} lineages {x['lineages']:.1f} size p50 {x['size']:.1f}")
            print(f"      moved {x['moved']:.4f} stalled {x['stalled']:.2f} blocked {x['blocked']:.2f} forward {x['forward']:.2f} stay {x['stay']:.3f} speed {x['speed']:.3f} "
                  f"muscle {x['muscle']:.2f} gut {x['gut']:.2f} | travel {fmt_opt(x['travel'], lambda v: f'{v:.1f}')} of {x['grown']}")
            print(f"      bare {x['bare']:.2f} grazed {fmt_opt(x['grazed'], pc)} trees {x['trees']:.0f} tree_eaten {x['tree_eaten']:.1f} regrowth {x['regrowth']:.1f} mean_res {x['mean_res']:.3f} "
                  f"plant {x['plant']:.1f} hunted {x['hunted']:.1f} scav {x['scav']:.1f}")
            g = x["gud"]
            gtxt = (f"gud learn {g['learn']:.3f} rest {g['rest']:.3f} under learn {g['under_learn']:.3f} rest {g['under_rest']:.3f} "
                    f"left learn {g['left_learn']:.4f} rest {g['left_rest']:.4f} ({g['rows']} rows)") if g else f"gud rest {fmt_opt(x['gud_rest'], f2)} under rest {fmt_opt(x['under_rest'], f2)}"
            print(f"      brain: learners {fmt_opt(x['learners'], pc)} eta {fmt_opt(x['eta'], f4)} learned {fmt_opt(x['learned'], pc)} memory {fmt_opt(x['memory'], pc)} | {gtxt}")
            print(f"      top {i} {share:.0%} {cells:.1f} cells {muscle:.1f} muscle {gut:.1f} gut {meat:.0%} flesh speed {speed:.2f} | diversity {x['div']} of {x['wins']}")
    for law in LAWS:
        xs = [st[law][s] for s in SEEDS if st[law][s]]
        print(f"{LAWS[law][0]}: hunter worlds {sum(x['hunter'] for x in xs)} of {len(xs)}; bodies {sum(x['bodies'] for x in xs) / max(len(xs), 1):.0f}")


def main():
    st = all_stats()
    logs = {f"{LAWS[law][0]}, seed {s}": load_csv(f"results/{run(law, s)}_log.csv") for law in (2, 3, 4, 5) for s in SEEDS if st[law][s]}

    charts_leave = [
        ratio_chart("Moving, against the same seed without the law", "Sub-cells a body moves by its own actions per step, second half, "
                    "over the same seed and brain without it. Above the dotted line the law made bodies move more.", st, "moved", (2, 4, 3, 5)),
        ratio_chart("Grown bodies' travel, against the same seed without it", "Median distance from the birthplace of the bodies aged "
                    "1,000 steps or more at step 100,000, over the same seed and brain without the law.", st, "travel", (2, 4, 3, 5)),
    ]
    charts_learn = [
        time_chart("Learners among the living", "Share of the bodies whose genome learns (a learning rate above 0), every 10,000 steps. "
                   "Half of the random genomes do: above the dotted line, learning was selected.", "learners", BRAIN, hline=0.5),
        seed_chart("Learners, second half", "The same share, averaged over steps 50,000-100,000, with and without the law on the same "
                   "seed.", st, "learners", laws=BRAIN, percent=True, hline=0.5),
    ]
    charts_gud = [
        ratio_chart("Food left by learners, over the rest's", "The giving-up density of the learners over the rest's in the same run, "
                    "over the rows where each holds 5% of the bodies. Above the line learners leave more food.", st, "gud_ratio", (3, 5), own=True),
    ]
    charts_world = [
        ratio_chart("Bodies, against the same seed without the law", "Bodies alive over the second half, over the same seed and brain "
                    "without the law. Below the line the law costs the world bodies.", st, "bodies", (2, 4, 3, 5)),
        seed_chart("Lowest winter", "The fewest bodies alive in any winter under the law; the dotted line is the hypothesis's 50.",
                   st, "floor", laws=(2, 4, 3, 5), hline=50),
    ]

    def cell(s, key, f, laws):
        return "<td>" + " / ".join(fmt_opt(st[law][s][key] if st[law][s] else None, f) for law in laws) + "</td>"

    pc = lambda v: f"{v:.0%}"
    seed_rows = ""
    for s in SEEDS:
        for bname, laws in (("old", OLD), ("brain", BRAIN)):
            if not st[laws[0]][s]:
                continue
            seed_rows += (f"<tr><td>{s}</td><td>{bname}</td>{cell(s, 'moved', lambda v: f'{v:.3f}', laws)}"
                          f"{cell(s, 'travel', lambda v: f'{v:.1f}', laws)}"
                          f"{cell(s, 'learners', pc, laws) if bname == 'brain' else '<td>-</td>'}"
                          f"{cell(s, 'gud_ratio', lambda v: f'{v:.2f}', laws[1:]) if bname == 'brain' else '<td>-</td>'}"
                          f"{cell(s, 'bodies', lambda v: f'{v:,.0f}', laws)}{cell(s, 'floor_txt', str, laws)}"
                          f"{cell(s, 'share', pc, laws)}{cell(s, 'div', str, laws)}</tr>")
    tables = data_table(["step", "pop", "births", "deaths_energy", "learners", "eta", "learned", "memory", "moved", "stalled", "blocked",
                         "speed_mean", "muscle_mean", "bare", "grazed", "trees", "tree_eaten", "regrowth", "under_learn", "under_rest",
                         "gud_learn", "gud_rest", "left_learn", "left_rest", "size_p50"], logs)
    TEXT.update(TEXTS)
    TEXT["gallery"] = gallery(GALLERY, GALLERY_CAPTION) if GALLERY else ""
    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>e051 A place that gets worse the longer a body stays - Report</title>
<style>{CSS}</style>
</head>
<body>
<main>
<h1>e051: A place that gets worse the longer a body stays</h1>
<p class="sub">Experiment report - 2026-09-12 - e041's stock law (a grazed cell comes back slowly) with and without e050's brain, in e048's world, seeds 9-12, against the runs without it. Answer: {TEXT["sub_answer"]}</p>

<section class="tldr">
<h2>TL;DR</h2>
<p>{TEXT["tldr"]}</p>
</section>

<h2>1. Question</h2>
<p>{TEXT["question"]}</p>
<ol>
  <li><strong>Bodies go farther under the law:</strong> with the old brain, more moving and grown bodies farther from their birthplace than without it, on three seeds of four.</li>
  <li><strong>Learning is selected where the place worsens:</strong> learners above half, and above the brain alone's, on three seeds of four.</li>
  <li><strong>Learners leave sooner:</strong> they leave more food on the cell they move off than the rest, on three seeds where both hold 5%.</li>
  <li><strong>The world stands:</strong> every winter floor above 50.</li>
</ol>

<h2>2. The law</h2>
<p>{TEXT["world"]}</p>
{DIAGRAM}
<p><strong>Runs.</strong> {TEXT["runs"]}</p>
<ul class="measures">
  <li><strong>moved</strong> - sub-cells a body moves by its own actions, per step.</li>
  <li><strong>travel</strong> - how far a body aged 1,000 steps or more stands from its birthplace (median, world cells).</li>
  <li><strong>learners</strong> - the share of the bodies whose genome learns; half at the random start.</li>
  <li><strong>giving-up density</strong> - the food on a cell when the last of a body's guts moves off it.</li>
  <li><strong>lowest floor</strong> - the fewest bodies alive in any winter.</li>
  <li><strong>state, diversity</strong> - the flesh of kills in what bodies eat; the diversity number (#42).</li>
</ul>

<h2>3. Results</h2>
<p>Means over the second half (steps 50,000-100,000). Each cell is without the law / stock 1 / stock 4 on the same seed and brain; food left is the learners' giving-up density over the rest's, at stock 1 / stock 4.</p>
<div class="tw"><table>
<thead><tr><th>seed</th><th>brain</th><th>moved</th><th>travel</th><th>learners</th><th>food left, learners over rest</th><th>bodies</th><th>lowest floor</th><th>kills' share</th><th>diversity</th></tr></thead>
<tbody>{seed_rows}</tbody></table></div>
<ol class="verdicts">
{TEXT["verdicts"]}
</ol>

<h3>3.1 {TEXT["h_leave"]}</h3>
<div class="grid2">
{"".join(charts_leave)}
</div>
<p>{TEXT["p_leave"]}</p>

<h3>3.2 {TEXT["h_learn"]}</h3>
<div class="grid2">
{"".join(charts_learn)}
</div>
<p>{TEXT["p_learn"]}</p>

<h3>3.3 {TEXT["h_gud"]}</h3>
<div class="grid2">
{"".join(charts_gud)}
</div>
<p>{TEXT["p_gud"]}</p>

<h3>3.4 {TEXT["h_world"]}</h3>
<div class="grid2">
{"".join(charts_world)}
</div>
<p>{TEXT["p_world"]}</p>
{TEXT["gallery"]}

<h2>4. Discussion</h2>
{TEXT["discussion"]}

<h2>5. Conclusion and next step</h2>
<p>{TEXT["conclusion"]}</p>

<h2>Appendix: data</h2>
<p>Every log step (10,000 steps) of the eight runs under the law; the runs without it are in e048's and e050's reports, the check's and the pilots' in <code>results/pilot/</code>. The full data are in <code>results/*.csv</code>. Build this report with <code>uv run python experiments/e051_leave/report.py</code>.</p>
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
    ("knee 1, old brain, seed 9", 2, 9, 334, "the leader of a hunter world", "Muscle across the front and down one side, eyes and gut in its corner."),
    ("knee 1, brain, seed 11", 3, 11, 525, "the learning hunter", "Three rows of muscle and a gut at each back corner: it learns fast (eta 0.07) and lives on flesh."),
    ("knee 1, brain, seed 12", 3, 12, 920, "the gut square", "Gut rows front and back around a band of muscle: half of the last third, and few of it learn."),
    ("knee 4, brain, seed 9", 5, 9, 151, "the leader of a world of 490", "Three rows of muscle over a block of gut: half of the last third."),
    ("knee 4, brain, seed 10", 5, 10, 351, "the gut plate", "Muscle in the middle of a plate of gut: 62% of the last third."),
    ("knee 4, old brain, seed 11", 4, 11, 628, "the runner", "Three rows of muscle before a row of gut: light and quick."),
]
GALLERY_CAPTION = ("The usual grown body of six leading lineages under the law, front up (orange muscle, aqua gut, yellow sensor, blue hard). "
                   "The one that learns fast is a hunter.")

TEXTS = {
    "sub_answer": ("partly, under these runs' conditions. At knee 1 the law is a tax that moves nothing; at 4 bodies move more in a "
                   "world of a quarter to half of the bodies. Learning is selected at neither. Kept as an argument."),
    "tldr": ("A grazed cell now comes back slowly: it uses its light in the share it stands of a knee. At knee 1 the world loses "
             "13-44% of its bodies and nothing moves more. At 4 bodies move 1.1-1.8 times as much in a world of 24-46% of the bodies, "
             "and two first winters fall below 50. Learners stay below half in seven runs of eight; where learning is kept, it rides "
             "on hunters. Next: #55, life history."),
    "question": ("In e050 a brain that learns was used but not selected; in e048's world a sitter's food regrows under it. e041's "
                 "stock law makes a grazed cell come back slowly, so the damage outlasts the grazer. Leaving should pay when a spot "
                 "comes back slowly and the body can learn, so the law runs with and without e050's brain, at knees 1 and 4:"),
    "world": ("The light a cell grows by is used in the share it stands of the knee, never below a tenth; the rest is lost. At knee 1 "
              "standing trees, which give 77-81% of the plant eaten, are untouched; at 4 every bitten tree grows slower too."),
    "runs": ("Knees 1 and 4, the old brain and the brain, seeds 9-12, 100,000 steps: 16 runs in two batches of eight (15 and 12 "
             "minutes), against e048's and e050's runs without the law. Before them, a check (no law: e050 byte for byte) and pilots "
             "at both knees on seed 9."),
    "verdicts": ("<li><span class=\"verdict partly\">At 4 only</span> At knee 1 moving is within 4% on three seeds of four; at 4 it "
                 "is 1.11-1.82 times, and grown bodies go farther on three.</li>"
                 "<li><span class=\"verdict no\">No</span> Learners are above half on one run of eight (knee 1, seed 11) and at "
                 "1-16% at knee 4.</li>"
                 "<li><span class=\"verdict partly\">Narrowly</span> At knee 1 learners leave more food on three seeds, by 3%, 5% "
                 "and 50%; the 50% is seed 11, whose learners hunt.</li>"
                 "<li><span class=\"verdict partly\">At 1 only</span> Lowest winters 133-365 at knee 1; 47-117 at 4, two below 50, "
                 "none dead.</li>"),
    "h_leave": "Bodies go farther only where the law slows the trees",
    "p_leave": ("At knee 1 the law takes a third of the growth from the ground between the trees, and bodies move as before. At 4 it "
                "slows every bitten tree and the world falls to 24-46% of its bodies; they move more with no more muscle (speed "
                "0.17-0.22), and their moves are blocked 29-41% of the time against 36-58%. These runs do not separate the law from "
                "the thinner crowd."),
    "h_learn": "Learning is not selected at either knee",
    "p_learn": ("Learners follow the lineage that wins, as in e050: above half at step 10,000 on six runs of eight, then down. Where "
                "learning is kept (knee 1, seed 11), the lineages that learn fastest (eta 0.07) hunt. In e048's world, 5 of the 6 "
                "fast-learning lineages of this experiment and e050 take 51-72% of their food from flesh."),
    "h_gud": "Learners leave more food, clearly only where they hunt",
    "p_gud": ("The giving-up density is the food on a cell when a body's last gut leaves it. At knee 1 learners leave more than the "
              "rest on three seeds, by 3%, 5% and 50%, and leave cells more often on three. The large gap is seed 11, where learners "
              "hunt and the plant is not their main food. At 4 learners are too few to compare on two seeds."),
    "h_world": "A tax at knee 1, a thin world at 4",
    "p_world": ("At knee 1 the world holds 56-87% of its bodies and every winter stays above 130. At 4 the law takes 47-59 of the "
                "light a step and the plant grows 60% less; the world holds 24-46% of its bodies, and every first winter is its "
                "lowest, 47-117. Diversity stays at 1-2 at both knees."),
    "discussion": ("<p>A slow return worsens a place for the next visitor, not for the one who stays. A body eats down the cell under "
                   "it whatever the law, since a held cell does not grow; the law only sets how fast the cell comes back once the body "
                   "has left. At knee 1 that is a tax on the ground between the trees; at 4 it thins the world until the crowd has "
                   "room to move.</p>"
                   "<p>Learning found its use on hunters, in e050 and here. A hunter's intake jumps with each kill and each chase, "
                   "while a grazer's food barely changes within its life. A brain may need a world where the food runs more than one "
                   "where the grass is slow.</p>"
                   "<p>What this does not show: that a worsening place gives no reason to leave, or that a brain is not needed. The "
                   "answers hang on our choices: trees as the food, a knee on the light, one step's energy as the reward, two knees, "
                   "four seeds of 100,000 steps, and at knee 4 a thinner crowd we did not control for.</p>"),
    "conclusion": ("Not kept as the default; stock stays as the argument 37. Under these conditions a slow return is a tax at knee 1 "
                   "and a thin world at 4, and learning is selected at neither. Next: #55, life history, since a body must live long "
                   "enough to follow a change itself (e049). Open: a worsening that falls on the stayer (fouling), and a density "
                   "control for knee 4."),
}


if __name__ == "__main__":
    if len(os.sys.argv) > 1 and os.sys.argv[1] == "lineages":
        for law in (2, 3, 4, 5):
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
