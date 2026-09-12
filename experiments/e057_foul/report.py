#!/usr/bin/env python3
"""Build report.html for this experiment.

Charts: matplotlib, exported as SVG and inlined. Diagram: hand-written SVG.
Run from the repo root: uv run python experiments/e056_sun/report.py
(`report.py lineages` prints the top lineages of every run, to pick the gallery;
`report.py numbers` prints the measures over the second half, for the README.)
"""
import csv
import html
import io
import json
import math
import os
import random
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

HEAD = "128_sigma0_r64_f0_flat_eyes8_flesh1_w1_season2_digest0_sidegrow_store5_yolk0_breed0_winterhigh_water0.1_leach0.01_depth0.01_mix0.2"
TAIL = "_strict_sat_hold_wear3000_corner_motor_clock0.5"
WIDTH = 128  # world cells across
CLOCK_MASS = 16.0  # the reference mass: a body of this mass or less takes a turn every step
# The control is this crate at `foul` 0, which reproduces e055's kept batch exactly: over the six
# seeds every column of the log matches but `steps_per_sec`. It is run here so that the columns
# this experiment added (`covered`, `plant_std`, the waste) are measured on both arms.
E055 = os.path.join(os.path.dirname(HERE), "e055_span")


def run(law, seed):
    """law 0: no fouling (the control, e055's batch, which is this crate with `foul` 0); 1: fouling."""
    return f"{HEAD}{TAIL}{'' if law == 0 else FOUL_TAG}_seed{seed}"


def folder(law):
    return HERE


FOUL = 0.03
FOUL_TAG = f"_foul{FOUL}"
LAWS = {0: ("no fouling", 5), 1: ("fouling", 0)}  # name, color slot
STEPS = 100_000
SEASON = 20_000
LOG = 10_000  # steps per log.csv row
PILOT_STEPS = 20_000
PILOT_LEVELS = [0, 0.003, 0.01, 0.03]  # the pilot ran seed 9 at these, 20,000 steps
SEEDS = [9, 10, 11, 12, 13, 14]
STATE_LINE = 0.03  # blocks broken per body per step: above it a hunter world (e045: 0.045-0.079, grazer 0.012-0.018)
FLAT_TRAVEL = (2.5, 5.0)  # world cells: the median travel of a body aged 200-500 steps, measured in e048 (#64)

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


AGE_BINS = [(0, 200), (200, 500), (500, 1000), (1000, 10**9)]
AGE_NAMES = ["0-199", "200-499", "500-999", "1,000+"]


def travel(run, folder=HERE, lo=200, hi=500):
    """The median travel (world cells from its birthplace) of the bodies aged lo to hi at step 100,000."""
    xs = [float(r["travel"]) for r in agents_rows(run, folder) if lo <= int(r["age"]) < hi]
    return median(xs)


def travel_by_age(law, least=5):
    """Per age bin, (the median travel in world cells, how many bodies) of the bodies alive at step 100,000, all
    seeds together; nan where fewer than `least` bodies are that old."""
    rows = [r for s in SEEDS for r in agents_rows(run(law, s), folder(law))]
    out = []
    for lo, hi in AGE_BINS:
        xs = [float(r["travel"]) for r in rows if lo <= int(r["age"]) < hi]
        out.append((median(xs) if len(xs) >= least else float("nan"), len(xs)))
    return out


RATE = 0.01  # RES_GROWTH: what one cell grows per step in the flat world


def field_map(run, folder=HERE):
    """The regrowth of every cell at the last long frame, rebuilt from the patch centers it carries, as rows of
    WIDTH; and the rich cells (at or above the flat world's rate) as the same."""
    last = None
    for d in read_frames(f"results/{run}_long.jsonl", folder):
        last = d
    grow = [0.0] * (WIDTH * WIDTH)
    for cx, cy, sigma in last["patches"]:
        peak = RATE * GRAIN[1] / (2 * math.pi * sigma * sigma)
        r = int(math.ceil(3 * sigma))
        for dy in range(-r, r + 1):
            for dx in range(-r, r + 1):
                c = ((cy + dy) % WIDTH) * WIDTH + (cx + dx) % WIDTH
                grow[c] += peak * math.exp(-(dx * dx + dy * dy) / (2 * sigma * sigma))
    rows = lambda v: [v[y * WIDTH:(y + 1) * WIDTH] for y in range(WIDTH)]
    return rows(grow), rows([1.0 if g >= RATE else 0.0 for g in grow])


def regions(rich):
    """(how many connected regions of rich land, the largest in cells, the median): 4-neighbour, on the torus."""
    flat = [bool(v) for row in rich for v in row]
    seen, sizes = [False] * len(flat), []
    for i in range(len(flat)):
        if flat[i] and not seen[i]:
            stack, n, seen[i] = [i], 0, True
            while stack:
                c = stack.pop()
                n += 1
                x, y = c % WIDTH, c // WIDTH
                for nx, ny in (((x + 1) % WIDTH, y), ((x - 1) % WIDTH, y), (x, (y + 1) % WIDTH), (x, (y - 1) % WIDTH)):
                    j = ny * WIDTH + nx
                    if flat[j] and not seen[j]:
                        seen[j] = True
                        stack.append(j)
            sizes.append(n)
    sizes.sort(reverse=True)
    return len(sizes), sizes[0], sizes[len(sizes) // 2]


def plant_map(run, folder=HERE, step=STEPS):
    """The standing plant of every cell at `step` (soil.jsonl), as rows of WIDTH."""
    for d in read_frames(f"results/{run}_soil.jsonl", folder):
        if d["step"] == step:
            v = d["plant"]
            return [v[y * WIDTH:(y + 1) * WIDTH] for y in range(len(v) // WIDTH)]
    return None


LIGHT, HEAVY = 24, 48  # a body born under LIGHT of mass is light, one at HEAVY or more is heavy


def lives(run, folder=HERE, lo=STEPS // 2):
    """From deaths.csv over the second half (e052): the median life in world steps of the bodies born light (under
    LIGHT), heavy (HEAVY or more) and of all of them, and the share of the deaths that are heavy. `age` is a bin of
    50 steps: its middle stands for it."""
    rows = [r for r in load_rows(f"results/{run}_deaths.csv", folder) if int(r["step"]) > lo]
    total = sum(int(r["n"]) for r in rows) or 1

    def med(sel):
        pairs = sorted((int(r["age"]) + 25, int(r["n"])) for r in rows if sel(float(r["mass"])))
        n = sum(p[1] for p in pairs)
        if n == 0:
            return None
        c = 0
        for age, k in pairs:
            c += k
            if c >= n / 2:
                return age
    light, heavy = med(lambda m: m < LIGHT), med(lambda m: m >= HEAVY)
    return dict(light=light, heavy=heavy, all=med(lambda m: True), deaths=total,
                heavy_share=sum(int(r["n"]) for r in rows if float(r["mass"]) >= HEAVY) / total,
                ratio=(heavy / light if light and heavy else None))


def starve(d, bodies, land):
    """Starvations per body per step on the rich or the thin land, over the second half (nan where no such land)."""
    share = half_mean(d, "pop_rich")
    here = bodies * (share if land == "rich" else 1 - share)
    return half_mean(d, f"hunger_{land}") / here if here > 0 else float("nan")


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
    li = lives(r, fo)
    tl = top_lineage(r, fo)
    hunger, thirst = half_mean(d, "deaths_energy") / LOG, half_mean(d, "deaths_thirst") / LOG
    died = int(d["step"][-1]) if d["pop"][-1] == 0 else None  # the step the world died at, if it did
    floor = 0 if died else min(x["pop"] for x in w)
    return dict(bodies=bodies, floors=[x["pop"] for x in w], floor=floor, died=died, floor_txt=f"died at {died:,}" if died else f"{floor:,}",
                births=half_mean(d, "births") / LOG, age=half_mean(f, "age_mean"), lineages=half_mean(f, "lineages"),
                broken=broken, per_body=broken / bodies, hunter=broken / bodies >= STATE_LINE,
                plant=plant, hunted=hunted, scav=scav, share=hunted / (plant + hunted + scav), size=half_mean(d, "size_p50"),
                muscle=half_mean(d, "muscle_mean"), gut=half_mean(d, "digestive_mean"), speed=half_mean(d, "speed_mean"),
                moved=half_mean(d, "moved"), stalled=half_mean(d, "stalled"), blocked=half_mean(d, "blocked"),
                hunger=hunger, thirst=thirst, thirst_share=thirst / max(hunger + thirst, 1e-9),
                mass_max=half_mean(d, "mass_max"), size_p90=half_mean(d, "size_p90"),
                travel=travel(r, fo), travel_all=travel(r, fo, 0, 10**9),
                pace=half_mean(d, "pace"), turned=half_mean(d, "turned"), age_p50=half_mean(d, "age_p50"), age_p90=half_mean(d, "age_p90"),
                lives=li, life=li["all"], life_light=li["light"], life_heavy=li["heavy"], life_ratio=li["ratio"],
                mass=half_mean(d, "mass_p50"), mass_p90=half_mean(d, "mass_p90"), intake=half_mean(d, "intake_per_gut"),
                top=tl, top_cells=tl[2], div=div, wins=len(wins),
                # e057 (#56): the crowd's hold on the ground, the waste, and what the ground grows.
                covered=half_mean(d, "covered"), foul_mean=half_mean(d, "foul_mean"), foul_p90=half_mean(d, "foul_p90"),
                foul_free=half_mean(d, "foul_free"), fouled=half_mean(d, "fouled"), plant_std=half_mean(d, "plant_std"),
                denied=half_mean(d, "births_no_room"), res=half_mean(d, "mean_res"), regrowth=half_mean(d, "regrowth"),
                shaded=half_mean(d, "shaded"), stay=half_mean(d, "stay"), forward=half_mean(d, "forward"),
                gud=half_mean(d, "gud_rest"), under=half_mean(d, "under_rest"), left=half_mean(d, "left_rest"))


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


def seed_chart(title, subtitle, st, key, laws=(0, 1), percent=False, ymax=None, hline=None, fmt=None, second=None, label=None):
    """One dot per seed and law: st[law][seed][key]; `hline` draws a dotted reference line. `second` is (another key,
    its color slot, its label), drawn for the first law."""
    fig, ax = new_axes("seed")
    series = [(key, LAWS[law][1], label if label and law == laws[0] else LAWS[law][0], law) for law in laws]
    if second:
        series.append((second[0], second[1], second[2], laws[0]))
    for k, (kk, slot, label, law) in enumerate(series):
        dx = (k - (len(series) - 1) / 2) * 0.12
        pts = [(s + dx, st[law][s][kk]) for s in SEEDS if st[law][s] and st[law][s][kk] is not None]
        ax.plot([p[0] for p in pts], [p[1] for p in pts], color=SERIES[slot], linestyle="none", marker="o", markersize=7, label=label)
    if hline is not None:
        ax.axhline(hline, color=INK, linewidth=1, linestyle=":")
    vals = [st[law][s][kk] for kk, _slot, _lab, law in series for s in SEEDS if st[law][s] and st[law][s][kk] is not None] + ([hline] if hline is not None else [])
    top, low = max(vals, default=1.0), min(vals + [0.0])
    ax.set_ylim(low * 1.15, ymax if ymax is not None else max(top, 1e-9) * 1.15)
    ax.set_xticks(SEEDS)
    ax.yaxis.set_major_formatter(fmt or ((lambda y, _p: f"{y:.0%}") if percent else kfmt))
    ax.yaxis.set_major_locator(MaxNLocator(4, steps=[1, 2, 5, 10]))
    legend_above(ax, len(series))
    return figure(title, subtitle, to_svg(fig))


def travel_chart(title, subtitle):
    """The median travel of the bodies by age, both worlds."""
    fig, ax = new_axes("age at step 100,000 (steps)")
    for law in (0, 1):
        ys = [m for m, _n in travel_by_age(law)]
        ax.plot(range(len(AGE_BINS)), ys, color=SERIES[LAWS[law][1]], marker="o", markersize=6, linewidth=1.6, label=LAWS[law][0])
    ax.set_xticks(range(len(AGE_BINS)), AGE_NAMES)
    ax.margins(x=0.05)
    ax.set_ylim(0)
    ax.yaxis.set_major_locator(MaxNLocator(4, steps=[1, 2, 5, 10]))
    legend_above(ax, 2)
    return figure(title, subtitle, to_svg(fig))


def pace_chart(title, subtitle):
    """The median pace of the living bodies by mass bin, both worlds."""
    fig, ax = new_axes("the body's mass at step 100,000")
    for law in (0, 1):
        ys = [p for p, _n in pace_by_mass(law)]
        ax.plot(range(len(MASS_NAMES)), ys, color=SERIES[LAWS[law][1]], marker="o", markersize=6, linewidth=1.6, label=LAWS[law][0])
    ax.set_xticks(range(len(MASS_NAMES)), MASS_NAMES)
    ax.margins(x=0.05)
    ax.set_ylim(0, 1.05)
    ax.yaxis.set_major_locator(MaxNLocator(4, steps=[1, 2, 5, 10]))
    legend_above(ax, 2)
    return figure(title, subtitle, to_svg(fig))


def life_chart(title, subtitle, st):
    """The median life of the bodies born light and born heavy, by seed and world."""
    fig, ax = new_axes("seed")
    for k, (law, key, slot, label) in enumerate([(0, "life_light", 0, "light, clock"), (0, "life_heavy", 1, "heavy, clock"),
                                                 (1, "life_light", 5, "light, flat"), (1, "life_heavy", 6, "heavy, flat")]):
        dx = (k - 1.5) * 0.12
        pts = [(s + dx, st[law][s][key]) for s in SEEDS if st[law][s] and st[law][s][key] is not None]
        ax.plot([p[0] for p in pts], [p[1] for p in pts], color=SERIES[slot], linestyle="none", marker="o", markersize=7, label=label)
    ax.set_xticks(SEEDS)
    ax.set_ylim(0)
    ax.yaxis.set_major_formatter(kfmt)
    ax.yaxis.set_major_locator(MaxNLocator(4, steps=[1, 2, 5, 10]))
    legend_above(ax, 4)
    return figure(title, subtitle, to_svg(fig))


def time_chart(title, subtitle, lines, ylabel_pct=False, ymax=None):
    """lines: [(label, color slot, steps, values)] over the run."""
    fig, ax = new_axes()
    for label, slot, xs, ys in lines:
        ax.plot(xs, ys, color=SERIES[slot], linewidth=1.6, label=label)
    ax.set_ylim(0, ymax)
    ax.yaxis.set_major_formatter((lambda y, _p: f"{y:.0%}") if ylabel_pct else kfmt)
    ax.yaxis.set_major_locator(MaxNLocator(4, steps=[1, 2, 5, 10]))
    legend_above(ax, min(len(lines), 3))
    return figure(title, subtitle, to_svg(fig))


PLANT_CMAP = matplotlib.colors.LinearSegmentedColormap.from_list(
    "plant", [(*matplotlib.colors.to_rgb(SERIES[2]), 0.0), (*matplotlib.colors.to_rgb(SERIES[2]), 1.0)])


def map_chart(title, subtitle, grid, vmax, labels=None, slot=2):
    """One map of the 128x128 world: a value per cell, drawn in one color at rising opacity."""
    cmap = matplotlib.colors.LinearSegmentedColormap.from_list(
        "m", [(*matplotlib.colors.to_rgb(SERIES[slot]), 0.0), (*matplotlib.colors.to_rgb(SERIES[slot]), 1.0)])
    fig, ax = plt.subplots(figsize=(3.2, 3.2))
    im = ax.imshow(grid, cmap=cmap, vmin=0, vmax=vmax, interpolation="nearest")
    ax.set_xticks([]), ax.set_yticks([])
    ax.grid(False)
    for sp in ax.spines.values():
        sp.set_visible(True)
        sp.set_edgecolor(INK)
        sp.set_alpha(0.4)
    if labels:
        bar = fig.colorbar(im, ax=ax, orientation="horizontal", fraction=0.05, pad=0.04, ticks=[0, vmax])
        bar.ax.set_xticklabels(labels)
        bar.outline.set_visible(False)
        bar.ax.tick_params(length=0)
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


# Hand-written mechanism diagram: the fouling loop. The bodies lie on the ground, the ground they
# lie on holds waste, and the waste divides the light that cell can use. Numbers are the batch's
# means over the second half, no fouling -> fouling.
DIAGRAM = """
<figure class="fig diagram">
<svg viewBox="0 0 880 360" width="100%" role="img" aria-label="The fouling loop: bodies lying on a cell leave waste, the waste divides the light the cell can use, less light grows less plant, and fewer bodies leave less waste" font-size="12" fill="currentColor" stroke="currentColor">
  <defs>
    <marker id="a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0 L10 5 L0 10 z" fill="currentColor" stroke="none"/></marker>
    <marker id="b" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0 L10 5 L0 10 z" fill="var(--s1)" stroke="none"/></marker>
  </defs>
  <g stroke="none" font-weight="600">
    <text x="40" y="26">the light offered: 118 per step, the same in both worlds</text>
  </g>
  <g fill="none" stroke-width="1.6">
    <path d="M130 38 L130 96" marker-end="url(#a)"/>
    <path d="M270 130 L338 130" marker-end="url(#a)"/>
    <path d="M528 130 L596 130" marker-end="url(#a)"/>
    <path d="M700 172 L700 262 L600 262" marker-end="url(#a)"/>
    <path d="M270 262 L190 262 L190 174" stroke="var(--s1)" marker-end="url(#b)"/>
  </g>
  <g fill="none" stroke-opacity="0.45">
    <rect x="60" y="100" width="210" height="72" rx="6"/>
    <rect x="338" y="100" width="190" height="72" rx="6"/>
    <rect x="596" y="100" width="210" height="72" rx="6"/>
    <rect x="270" y="228" width="330" height="68" rx="6" stroke="var(--s1)"/>
  </g>
  <g stroke="none">
    <text x="74" y="124" font-weight="600">the cell grows</text>
    <text x="74" y="144">65.7 &#8594; 57.5 a step</text>
    <text x="74" y="162">of the light it can use</text>
    <text x="352" y="124" font-weight="600">standing plant</text>
    <text x="352" y="144">1.54 &#8594; 1.47 a cell</text>
    <text x="352" y="162">as uneven either way</text>
    <text x="610" y="124" font-weight="600">bodies</text>
    <text x="610" y="144">2,677 &#8594; 2,352</text>
    <text x="610" y="162">on 56% &#8594; 50% of the cells</text>
    <text x="284" y="252" font-weight="600" fill="var(--s1)">waste on the cell</text>
    <text x="284" y="272" fill="var(--s1)">laid 0.03 a step under a body, rots 1% a step</text>
    <text x="284" y="290" fill="var(--s1)">0.32 where no body lies, 1.71 at the 90th percentile</text>
    <text x="286" y="124">grown</text>
    <text x="544" y="124">eaten</text>
    <text x="612" y="254">they lie on it</text>
    <text x="200" y="200" fill="var(--s1)" font-weight="600">divides the light by 1 + waste</text>
    <text x="200" y="218" fill="var(--s1)">14.8 a step taken, 5.2 back as less shade</text>
  </g>
</svg>
<figcaption>Figure 1. The law is one divider on one number. Bodies lying on a cell leave waste there; the waste rots away in a few hundred steps, which is a life; and while it lies there the cell uses less of its light. The loop closes on itself: fewer bodies leave less waste, so the world settles rather than runs down. Numbers are means over the second half of seeds 9-14, no fouling to fouling.</figcaption>
</figure>
"""


SHARED = [9, 10, 11, 12, 13, 14]  # both arms ran every seed


def arm(law, key, seeds=SHARED):
    """The mean of a log column over the second half, over the seeds."""
    vals = []
    for s in seeds:
        r, fo = run(law, s), folder(law)
        if not exists(r, fo):
            continue
        v = half_mean(load_csv(f"results/{r}_log.csv", fo), key)
        if v is not None:
            vals.append(v)
    return sum(vals) / len(vals) if vals else float("nan")


def stack_chart(title, subtitle, parts):
    """One stacked bar per arm: parts is [(label, color slot, value per law)]."""
    fig, ax = new_axes("")
    xs = list(range(len(LAWS)))
    bottom = [0.0] * len(LAWS)
    for label, slot, vals in parts:
        ax.bar(xs, vals, 0.5, bottom=bottom, color=SERIES[slot], label=label)
        bottom = [b + v for b, v in zip(bottom, vals)]
    ax.set_xticks(xs, [LAWS[law][0] for law in LAWS])
    ax.margins(x=0.15)
    ax.set_ylim(0)
    ax.yaxis.set_major_formatter(kfmt)
    ax.yaxis.set_major_locator(MaxNLocator(4, steps=[1, 2, 5, 10]))
    legend_above(ax, min(len(parts), 3))
    return figure(title, subtitle, to_svg(fig))


TEXT = {}  # filled in main(); counted at the end


def all_stats():
    return {law: {s: stats(law, s) for s in SEEDS} for law in LAWS}


def fmt_opt(v, f):
    return "-" if v is None else f(v)


def pace_by_mass(law, bins=((0, 16), (16, 24), (24, 32), (32, 48), (48, 64), (64, 10**9)), least=5):
    """Per mass bin, (the median pace of the bodies alive at step 100,000, how many), all seeds together."""
    rows = [r for s in SEEDS for r in agents_rows(run(law, s), folder(law))]
    out = []
    for lo, hi in bins:
        xs = [float(r["pace"]) for r in rows if lo <= float(r["mass"]) < hi]
        out.append((median(xs) if len(xs) >= least else float("nan"), len(xs)))
    return out


MASS_NAMES = ["<16", "16-23", "24-31", "32-47", "48-63", "64+"]


def numbers():
    """The measures over the second half, per run (for the README)."""
    st = all_stats()
    for s in SEEDS:
        for law in LAWS:
            x = st[law][s]
            if not x:
                continue
            i, share, cells, muscle, gut, meat, speed = x["top"]
            print(f"seed {s} {LAWS[law][0]:12s} {'HUNTER' if x['hunter'] else 'grazer'} floor {x['floor_txt']} kills {x['share']:.1%} "
                  f"| bodies {x['bodies']:.0f} births {x['births']:.2f} age {x['age']:.0f} lineages {x['lineages']:.1f} div {x['div']}")
            print(f"      covered {fmt_opt(x['covered'], lambda v: f'{v:.3f}')} waste {fmt_opt(x['foul_mean'], lambda v: f'{v:.3f}')} "
                  f"free {fmt_opt(x['foul_free'], lambda v: f'{v:.3f}')} p90 {fmt_opt(x['foul_p90'], lambda v: f'{v:.3f}')} "
                  f"lost {fmt_opt(x['fouled'], lambda v: f'{v:.2f}')} | blocked {x['blocked']:.3f} denied {x['denied']:.3f} "
                  f"stay {x['stay']:.3f} travel {fmt_opt(x['travel'], lambda v: f'{v:.2f}')}")
            print(f"      plant {x['res']:.2f} spread {fmt_opt(x['plant_std'], lambda v: f'{v:.2f}')} regrowth {x['regrowth']:.1f} "
                  f"shaded {x['shaded']:.1f} | gud {fmt_opt(x['gud'], lambda v: f'{v:.3f}')} under {fmt_opt(x['under'], lambda v: f'{v:.3f}')} "
                  f"left {fmt_opt(x['left'], lambda v: f'{v:.4f}')}")
            print(f"      mass p50/p90 {x['mass']:.1f}/{x['mass_p90']:.1f} intake/gut {x['intake']:.4f} muscle {x['muscle']:.2f} "
                  f"gut {x['gut']:.2f} | top {i} {share:.0%} {cells:.1f} cells {meat:.0%} flesh speed {speed:.2f}")
    for law in LAWS:
        xs = [st[law][s] for s in SEEDS if st[law][s]]
        if not xs:
            continue
        mean = lambda k: sum(x[k] for x in xs if x[k] is not None) / max(len([x for x in xs if x[k] is not None]), 1)
        print(f"{LAWS[law][0]}: hunter worlds {sum(x['hunter'] for x in xs)} of {len(xs)}; bodies {mean('bodies'):.0f}; "
              f"floors {[x['floor'] for x in xs]}; covered {mean('covered'):.3f}; blocked {mean('blocked'):.3f}; denied {mean('denied'):.3f}; "
              f"plant {mean('res'):.2f}; spread {mean('plant_std'):.2f}; regrowth {mean('regrowth'):.1f}; travel {mean('travel'):.2f}; "
              f"kills {mean('share'):.1%}; mass p90 {mean('mass_p90'):.1f}; age {mean('age'):.0f}; div {[x['div'] for x in xs]}")
    for law in LAWS:
        print(f"{LAWS[law][0]} travel by age (median cells, n):", [(round(t, 2) if t == t else None, n) for t, n in travel_by_age(law)])


def main():
    st = all_stats()
    logs = {f"{LAWS[law][0]}, seed {s}": load_csv(f"results/{run(law, s)}_log.csv", folder(law)) for law in LAWS for s in SEEDS if st[law][s]}
    light = [("grown", 2, [arm(law, "regrowth") for law in LAWS]),
             ("held back by the canopy", 5, [arm(law, "shaded") for law in LAWS]),
             ("lost to the waste", 1, [arm(law, "fouled") for law in LAWS]),
             ("lost for want of soil", 3, [arm(law, "barren") for law in LAWS])]

    charts_room = [
        seed_chart("The share of the world a body lies on, by seed", "Cells with a body on them, over the second half. Lower is a crowd "
                   "with more ground between it.", st, "covered", percent=True),
        seed_chart("Births refused for want of room, by seed", "The share of births that found no free cell. A world with room would "
                   "sit near zero.", st, "denied", percent=True),
    ]
    charts_ground = [
        seed_chart("The waste on a cell, by seed", "Fouling runs only. Dots are the 90th percentile cell; the lower series is the mean "
                   "over cells with no body on them.", st, "foul_p90", laws=(1,), label="the 90th percentile cell",
                   second=("foul_free", 3, "a cell with no body on it"), fmt=lambda y, _p: f"{y:.1f}"),
        seed_chart("How unevenly the plant stands, by seed", "The spread (standard deviation) of the standing plant from cell to cell. "
                   "A rise would be ground that differs by place.", st, "plant_std", fmt=lambda y, _p: f"{y:.1f}"),
    ]
    charts_thin = [
        stack_chart("Where the light goes", "Per world step, means over the six seeds. The waste takes light; the thinner crowd gives "
                    "some back by shading less.", light),
        seed_chart("What a gut block takes, by seed", "Matter per gut block per step. A flat line is a crowd that has thinned until each "
                   "mouth earns what it did before.", st, "intake", fmt=lambda y, _p: f"{y:.4f}"),
    ]
    charts_move = [
        travel_chart("How far a body has travelled, by age", "World cells from its birthplace, median of the bodies alive at step "
                     "100,000. Higher would be bodies that leave."),
        seed_chart("The flesh of kills in what the bodies eat, by seed", "Second half. Above about 25% the world is in its hunting state.",
                   st, "share", percent=True),
    ]

    def cell(s, key, f):
        return "<td>" + " / ".join(fmt_opt(st[law][s][key] if st[law][s] else None, f) for law in LAWS) + "</td>"

    seed_rows = "".join(
        f"<tr><td>{s}</td>" + "<td>" + " / ".join("hunter" if st[law][s]["hunter"] else "grazer" for law in LAWS if st[law][s]) + "</td>"
        + f"{cell(s, 'covered', lambda v: f'{v:.0%}')}{cell(s, 'denied', lambda v: f'{v:.0%}')}"
        f"{cell(s, 'plant_std', lambda v: f'{v:.2f}')}{cell(s, 'travel', lambda v: f'{v:.2f}')}"
        f"{cell(s, 'intake', lambda v: f'{v:.4f}')}{cell(s, 'bodies', lambda v: f'{v:,.0f}')}{cell(s, 'floor_txt', str)}"
        f"{cell(s, 'share', lambda v: f'{v:.0%}')}{cell(s, 'div', lambda v: f'{v}')}</tr>"
        for s in SEEDS if st[0][s])
    tables = data_table(["step", "pop", "births", "deaths_energy", "cells_broken", "plant_intake", "meat_intake", "regrowth", "shaded",
                         "fouled", "foul_mean", "foul_p90", "foul_free", "covered", "plant_std", "mean_res", "blocked", "births_no_room",
                         "mass_p50", "mass_p90", "intake_per_gut", "muscle_mean", "digestive_mean", "age_p50"], logs)
    TEXT.update(TEXTS)
    TEXT["gallery"] = gallery(GALLERY, GALLERY_CAPTION) if GALLERY else ""
    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>e057 A worsening that falls on the one who stays - Report</title>
<style>{CSS}</style>
</head>
<body>
<main>
<h1>e057: A worsening that falls on the one who stays</h1>
<p class="sub">Experiment report - 2026-09-12 - fouling, on and off, seeds 9-14 (#56). Answer: {TEXT["sub_answer"]}</p>

<section class="tldr">
<h2>TL;DR</h2>
<p>{TEXT["tldr"]}</p>
</section>

<h2>1. Question</h2>
<p>{TEXT["question"]}</p>
<ol>
  <li><strong>The crowd lets go of the ground:</strong> fewer cells under a body, fewer moves blocked, fewer births refused.</li>
  <li><strong>The ground stops being uniform:</strong> the standing plant differs more from cell to cell.</li>
  <li><strong>Leaving pays:</strong> a body travels further in its life.</li>
  <li><strong>Predation holds:</strong> the kills' share does not fall within a world state.</li>
  <li><strong>The world stands:</strong> every winter floor above 50.</li>
</ol>

<h2>2. The world</h2>
<p>{TEXT["world"]}</p>
{DIAGRAM}
<p><strong>Runs.</strong> {TEXT["runs"]}</p>
<ul class="measures">
  <li><strong>covered</strong> - the share of the world's cells with a body lying on them.</li>
  <li><strong>waste</strong> - what a cell holds; a cell at 1 grows at half its rate.</li>
  <li><strong>plant spread</strong> - the standard deviation of the standing plant from cell to cell.</li>
  <li><strong>travel</strong> - world cells between a body's birthplace and where it is now.</li>
  <li><strong>intake per gut</strong> - matter a gut block takes per step.</li>
  <li><strong>state</strong> - hunter when more than 0.03 blocks are broken per body per step (e045).</li>
  <li><strong>kills' share, diversity</strong> - the flesh of kills in what bodies eat; the diversity number (#42).</li>
</ul>

<h2>3. Results</h2>
<p>Means over the second half (steps 50,000-100,000). Cells are no fouling / fouling on the same seed.</p>
<div class="tw"><table>
<thead><tr><th>seed</th><th>state</th><th>covered</th><th>births refused</th><th>plant spread</th><th>travel</th><th>intake per gut</th><th>bodies</th><th>lowest floor</th><th>kills' share</th><th>diversity</th></tr></thead>
<tbody>{seed_rows}</tbody></table></div>
<ol class="verdicts">
{TEXT["verdicts"]}
</ol>

<h3>3.1 {TEXT["h_room"]}</h3>
<div class="grid2">
{"".join(charts_room)}
</div>
<p>{TEXT["p_room"]}</p>

<h3>3.2 {TEXT["h_ground"]}</h3>
<div class="grid2">
{"".join(charts_ground)}
</div>
<p>{TEXT["p_ground"]}</p>

<h3>3.3 {TEXT["h_thin"]}</h3>
<div class="grid2">
{"".join(charts_thin)}
</div>
<p>{TEXT["p_thin"]}</p>

<h3>3.4 {TEXT["h_move"]}</h3>
<div class="grid2">
{"".join(charts_move)}
</div>
<p>{TEXT["p_move"]}</p>
{TEXT["gallery"]}

<h2>4. Discussion</h2>
{TEXT["discussion"]}

<h2>5. Conclusion and next step</h2>
<p>{TEXT["conclusion"]}</p>

<h2>Appendix: data</h2>
<p>Every log step (10,000 steps) of the twelve runs. The full data are in <code>results/*.csv</code>. Build this report with <code>uv run python experiments/e057_foul/report.py</code>.</p>
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
    ("no fouling, seed 13", 0, 13, 462, "the armoured hunter", "A shell across the front row, where the body meets what it bites. The biggest winner of the batch, and it holds 81% of its world."),
    ("no fouling, seed 12", 0, 12, 1845, "the hunter's frame", "The same plan on another seed: armour in front, muscle and gut behind. This is what the crowded world grows where the tooth pays."),
    ("no fouling, seed 11", 0, 11, 1186, "the lawn body", "Muscle over gut on a small frame, no armour: the fourteen-block body this world has selected since e043."),
    ("fouling, seed 9", 1, 9, 469, "the world's one body", "Muscle in front, gut behind, no armour. It holds 94% of its world - the highest share of the twelve runs, and it lives long."),
    ("fouling, seed 13", 1, 13, 225, "the hunter that stayed", "Armour and muscle on the one seed that hunted in both arms: fouling does not take the tooth away where the seed had put it."),
    ("fouling, seed 12", 1, 12, 1605, "the gut", "Its world turned from hunting to grazing under the law, and grazing here means carrying the batch's biggest stomach."),
]
GALLERY_CAPTION = ("The usual grown body of a leading lineage of six runs, front up (orange muscle, aqua gut, yellow sensor, blue hard). "
                   "The armour belongs to the hunting worlds, in both arms: fouling changed which seeds hunt, not what a hunter looks like.")

TEXTS = {
    "sub_answer": ("no, not kept. Fouling thins the crowd's hold on the ground by a tenth, but it costs the world an eighth of its food, "
                   "leaves the ground no less uniform, and no body walks further."),
    "tldr": ("Animals foul the ground they rest on, so a camp is left before its food runs out. We gave every cell waste that the bodies "
             "lying on it leave, that rots away in a few hundred steps, and that divides the light the cell can use. The waste is patchy "
             "(1.71 at the 90th percentile cell against 0.32 where no body lies) and the crowd does let go: 56% of cells under a body "
             "become 50%. But the plant stands exactly as unevenly as before, and a body's travel does not rise."),
    "question": ("Two findings ask for this law. The world is jammed - 60% of forward moves blocked, 31% of births refused - and e056 "
                 "showed a richer sun buys more bodies, not bigger ones, so the way out is a thinner crowd or places that differ. And "
                 "every law that made a grazed cell come back slowly (e041, e051) lowered every grazed cell alike: a commons. Fouling "
                 "takes only where the bodies are."),
    "world": ("One law about the ground, nothing about the bodies. A body lying on a cell lays waste there, the waste rots by 1% a step, "
              "and what a cell holds divides the light it can use. It falls on the growth and not on the bite because the world is "
              "already eaten down to what it grows: a smaller bite would only let the plant stand higher."),
    "runs": ("Pilots on seed 9 at 0, 0.003, 0.01 and 0.03, 20,000 steps: `foul` 0 reproduced e056 exactly, and 0.03 was the level where "
             "the ground under the crowd moved at all. The batch: both arms on seeds 9-14, 100,000 steps. Twelve runs, an hour on the Mac."),
    "verdicts": ("<li><span class=\"verdict\">Yes</span> Cells under a body fall from 56% to 50% and births refused for want of room "
                 "from 31% to 26%, in five of six seeds.</li>"
                 "<li><span class=\"verdict no\">No</span> The standing plant's spread from cell to cell is 2.63 without the law and "
                 "2.59 with it, although the waste's own p90 is five times what a free cell holds.</li>"
                 "<li><span class=\"verdict no\">No</span> Travel falls from 3.09 to 2.52 cells a life, and in the three seeds whose "
                 "world state did not change it moves by +2%, +3% and +13%.</li>"
                 "<li><span class=\"verdict\">Yes</span> In those same three seeds the kills' share rises: 23%&#8594;26%, 8%&#8594;8%, "
                 "30%&#8594;32%.</li>"
                 "<li><span class=\"verdict\">Yes</span> Winter floors 398-582 against 524-838, and no run died.</li>"),
    "h_room": "The crowd does let go of the ground",
    "p_room": ("This is the one thing the law delivers. A tenth of the ground the crowd was lying on is free, and a sixth of the refused "
               "births now find a cell. It is bought with food, not with room: the bodies that make the room are the ones the world can "
               "no longer feed."),
    "h_ground": "The waste is patchy; the food is not",
    "p_ground": ("The ground really is worse where the crowd is - a cell with no body on it carries 0.32 of waste against 1.71 at the "
                 "90th percentile - and none of it reaches the plant. A fouled cell grows less, but it is also the cell the crowd is "
                 "grazing, so growth and grazing fall together and what stands is unchanged."),
    "h_thin": "The crowd thins to exactly the food it lost",
    "p_thin": ("The waste takes 14.8 of the light a step; the thinner crowd hands 5.2 of it back by shading fewer cells, so the plant "
               "grown falls 12.5%. The bodies fall 12.1%. A gut block still takes 0.0018 a step. That is e038's pinned income from the "
               "other side: take food away and the crowd shrinks until each mouth earns what it did."),
    "h_move": "Nothing walks further, and the tooth is unharmed",
    "p_move": ("A body that is worse off for staying still does not leave - it dies, or it is not born. The world answers a law about "
               "place with a change in number, because a body's own range is a few cells and a lineage's is a birth. Within a matched "
               "state the kills' share holds or rises: the law does not stand between a hunter and its prey."),
    "discussion": ("<p>The law did what its arithmetic promised and it still changed nothing that matters. The waste builds where the "
                   "crowd lies, it is five times heavier there than on free ground, and it rots inside a life. The mechanism is not the "
                   "failure.</p>"
                   "<p>What fails is the link from the ground to a body. A cell under a body does not grow at all (e016), so what a body "
                   "eats is what grew on the ground it is arriving at, and the crowd covers half the world: the good ground and the bad "
                   "are never more than a cell or two apart, and grazing follows growth so closely that the plant left standing is the "
                   "same either way. A body cannot be told it should be somewhere else when everywhere is the same at the scale it can "
                   "reach.</p>"
                   "<p>Three of six seeds changed world state, two out of hunting and one into it, and every measure of a body follows "
                   "the state rather than the law - e055's warning, again. The law's own effect is the 12% of food it removes, and the "
                   "crowd absorbs that the way it absorbs a weaker sun (e046) or a stronger one (e056): in number, at a fixed income "
                   "per mouth.</p>"),
    "conclusion": ("Not kept: the season world keeps `foul` 0. Four laws have now tried to make leaving pay (e041, e049, e051, e054) and "
                   "this is the fourth to be answered in births instead of steps. The lesson to carry: a law that differs by place must "
                   "differ over more ground than a body covers, or the crowd averages it away. Next: the brain in a world where the food "
                   "runs out under the body (#58), which asks whether a body that can learn reads a worsening its reflexes cannot."),
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
