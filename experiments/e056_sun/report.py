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
# The control (sun 1) is e055's kept batch: this crate is e055 byte for byte, and its sun 1 pilot
# reproduced e055's clock 0.5 pilot number for number, so the runs are not made twice.
E055 = os.path.join(os.path.dirname(HERE), "e055_span")


def name(tag, seed=9):
    """A run's file prefix: e055's world under the clock, with the sun's tag ("", "_sun2", "_sun4")."""
    return f"{HEAD}{tag}{TAIL}_seed{seed}"


def run(law, seed):
    """law 0: sun 1 (the control, e055's batch); 1: sun 2; 2: sun 4."""
    return name("" if law == 0 else f"_sun{SUNS[law]}", seed)


def folder(law):
    return E055 if law == 0 else HERE


SUNS = {0: 1, 1: 2, 2: 4}
LAWS = {0: ("sun 1", 5), 1: ("sun 2", 0), 2: ("sun 4", 1)}  # name, color slot
STEPS = 100_000
SEASON = 20_000
LOG = 10_000  # steps per log.csv row
PILOT_STEPS = 20_000
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
                top=tl, top_cells=tl[2], div=div, wins=len(wins))


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


def seed_chart(title, subtitle, st, key, laws=(0, 1, 2), percent=False, ymax=None, hline=None, fmt=None, second=None, label=None):
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


# Hand-written mechanism diagram: the matter loop. The sun is a rate on the soil a cell still
# holds, so the light can only grow what the ground has; the numbers are sun 1 -> sun 4, means over
# the second half of seeds 9-11.
DIAGRAM = """
<figure class="fig diagram">
<svg viewBox="0 0 880 350" width="100%" role="img" aria-label="The matter loop: soil grows plants, plants feed bodies, bodies rot back to soil; the sun is a rate on the soil a cell still holds, and light that falls on soil-less ground is lost" font-size="12" fill="currentColor" stroke="currentColor">
  <g stroke="none" font-weight="600">
    <text x="40" y="28">the light offered: 114 per step at sun 1 &#8594; 453 at sun 4</text>
  </g>
  <g fill="none" stroke-width="1.6">
    <path d="M170 40 L170 150"/>
    <path d="M230 175 L400 175" marker-end="url(#a)"/>
    <path d="M560 175 L640 175" marker-end="url(#a)"/>
    <path d="M720 250 L720 305 L170 305 L170 250" marker-end="url(#a)"/>
    <path d="M300 160 L300 95" marker-end="url(#a)"/>
    <path d="M300 190 L300 232" stroke="var(--s1)" marker-end="url(#b)"/>
  </g>
  <defs>
    <marker id="a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0 L10 5 L0 10 z" fill="currentColor" stroke="none"/></marker>
    <marker id="b" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0 L10 5 L0 10 z" fill="var(--s1)" stroke="none"/></marker>
  </defs>
  <g fill="none" stroke-opacity="0.45">
    <rect x="60" y="150" width="170" height="95" rx="6"/>
    <rect x="400" y="150" width="160" height="95" rx="6"/>
    <rect x="640" y="150" width="180" height="95" rx="6"/>
  </g>
  <g stroke="none">
    <text x="72" y="172" font-weight="600">free soil</text>
    <text x="72" y="192">70,186 &#8594; 10,639</text>
    <text x="72" y="210">half of all the matter</text>
    <text x="72" y="228">&#8594; a fourteenth of it</text>
    <text x="412" y="172" font-weight="600">standing plant</text>
    <text x="412" y="192">21,244 &#8594; 20,970</text>
    <text x="412" y="210">the canopy and the lawn</text>
    <text x="652" y="172" font-weight="600">bodies</text>
    <text x="652" y="192">2,766 &#8594; 4,540 of them</text>
    <text x="652" y="210">their fat store:</text>
    <text x="652" y="228">39,694 &#8594; 96,591</text>
    <text x="243" y="168">grown 67.0 &#8594; 88.5</text>
    <text x="573" y="168">eaten</text>
    <text x="400" y="325">rot, breath and rain carry it back</text>
    <text x="314" y="88">lost to the canopy&#39;s shade</text>
    <text x="314" y="106">39% of the light &#8594; 31%</text>
    <text x="314" y="230" fill="var(--s1)" font-weight="600">lost for want of soil</text>
    <text x="314" y="248" fill="var(--s1)">2% of the light &#8594; 50%</text>
  </g>
</svg>
<figcaption>Figure 1. The matter is conserved: 140,139 in every run, whatever the sun. The sun (argument 33) is a rate on what soil a cell still holds, so raising it moves matter out of the ground faster - and once the ground is empty the extra light grows nothing. Numbers are sun 1 to sun 4, means over the second half of seeds 9-11.</figcaption>
</figure>
"""


SHARED = [9, 10, 11]  # the seeds run at all three suns


def arm(law, key, seeds=SHARED):
    """The mean of a log column over the second half, over the seeds run at every sun."""
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
    """One stacked bar per sun: parts is [(label, color slot, value per law)]."""
    fig, ax = new_axes("the sun")
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
            print(f"seed {s} {LAWS[law][0]:16s} {'HUNTER' if x['hunter'] else 'grazer'} floor {x['floor_txt']} kills {x['share']:.1%} "
                  f"| bodies {x['bodies']:.0f} floors {x['floors']} births {x['births']:.2f} age {x['age']:.0f} lineages {x['lineages']:.1f}")
            print(f"      pace {x['pace']:.3f} turned {x['turned']:.3f} | mass p50/p90/max {x['mass']:.1f}/{x['mass_p90']:.1f}/{x['mass_max']:.0f} "
                  f"size p50/p90 {x['size']:.1f}/{x['size_p90']:.1f} intake/gut {x['intake']:.4f}")
            print(f"      life p50 {fmt_opt(x['life'], str)} light {fmt_opt(x['life_light'], str)} heavy {fmt_opt(x['life_heavy'], str)} "
                  f"ratio {fmt_opt(x['life_ratio'], lambda v: f'{v:.2f}')} heavy share {x['lives']['heavy_share']:.1%} | hunger {x['hunger']:.2f} "
                  f"moved {x['moved']:.4f} muscle {x['muscle']:.2f} gut {x['gut']:.2f}")
            print(f"      top {i} {share:.0%} {cells:.1f} cells {muscle:.1f} muscle {gut:.1f} gut {meat:.0%} flesh speed {speed:.2f} "
                  f"| diversity {x['div']} of {x['wins']}")
    for law in LAWS:
        xs = [st[law][s] for s in SEEDS if st[law][s]]
        if not xs:
            continue
        mean = lambda k: sum(x[k] for x in xs) / len(xs)
        print(f"{LAWS[law][0]}: hunter worlds {sum(x['hunter'] for x in xs)} of {len(xs)}; bodies {mean('bodies'):.0f}; "
              f"floors {[x['floor'] for x in xs]}; mass p90 {[round(x['mass_p90'], 1) for x in xs]}; pace {mean('pace'):.3f}; "
              f"intake {mean('intake'):.4f}; age {mean('age'):.0f}; div {[x['div'] for x in xs]}")
    for law in LAWS:
        print(f"{LAWS[law][0]} pace by mass (median, n):", [(round(p, 3), n) for p, n in pace_by_mass(law)])


def main():
    st = all_stats()
    logs = {f"{LAWS[law][0]}, seed {s}": load_csv(f"results/{run(law, s)}_log.csv", folder(law)) for law in LAWS for s in SEEDS if st[law][s]}
    light = [("grown", 2, [arm(law, "regrowth") for law in LAWS]),
             ("held back by the canopy", 5, [arm(law, "shaded") for law in LAWS]),
             ("lost for want of soil", 1, [arm(law, "barren") for law in LAWS])]
    held = [("free soil", 5, [arm(law, "soil") for law in LAWS]),
            ("standing plant", 2, [arm(law, "tree_res") for law in LAWS]),
            ("fruit and carrion", 3, [arm(law, "fruit_stock") + arm(law, "carrion") for law in LAWS]),
            ("the bodies' fat", 1, [arm(law, "fat_stock") for law in LAWS])]
    held.append(("the bodies themselves", 0, [arm(law, "matter") - sum(p[2][i] for p in held) for i, law in enumerate(LAWS)]))

    charts_light = [
        stack_chart("Where the light goes", "Per world step, means over the second half of seeds 9-11. A world that used four times the "
                    "light would have a bar four times as tall.", light),
        stack_chart("Where the world's matter sits", "The same 140,139 of matter in every run; only its place differs.", held),
    ]
    charts_size = [
        seed_chart("The 90th percentile of the mass, by seed", "Bodies alive over the second half. Rising with the sun is the hypothesis.",
                   st, "mass_p90"),
        seed_chart("The winning lineage's body, by seed", "Blocks in the mean body of the lineage holding the most body-steps of the last "
                   "third.", st, "top_cells"),
    ]
    charts_many = [
        seed_chart("Bodies, by seed", "Bodies alive over the second half (steps 50,000-100,000).", st, "bodies"),
        seed_chart("What a gut block takes, by seed", "Matter per gut block per step. A flat line is a crowd that eats whatever the sun "
                   "offers.", st, "intake", fmt=lambda y, _p: f"{y:.4f}"),
    ]
    charts_world = [
        seed_chart("The lowest winter floor, by seed", "The smallest population of any season. The dotted line is the floor the hypothesis "
                   "asked for.", st, "floor", hline=50),
        seed_chart("The flesh of kills in what the bodies eat, by seed", "Second half. Above about 25% the world is in its hunting state.",
                   st, "share", percent=True),
    ]

    def cell(s, key, f):
        return "<td>" + " / ".join(fmt_opt(st[law][s][key] if st[law][s] else None, f) for law in LAWS) + "</td>"

    seed_rows = "".join(
        f"<tr><td>{s}</td>" + "<td>" + " / ".join("hunter" if st[law][s]["hunter"] else "grazer" for law in LAWS if st[law][s]) + "</td>"
        + f"{cell(s, 'mass_p90', lambda v: f'{v:.1f}')}{cell(s, 'size_p90', lambda v: f'{v:.1f}')}"
        f"{cell(s, 'top_cells', lambda v: f'{v:.1f}')}{cell(s, 'intake', lambda v: f'{v:.4f}')}"
        f"{cell(s, 'bodies', lambda v: f'{v:,.0f}')}{cell(s, 'floor_txt', str)}{cell(s, 'share', lambda v: f'{v:.0%}')}"
        f"{cell(s, 'div', lambda v: f'{v}')}</tr>"
        for s in SEEDS if st[0][s])
    tables = data_table(["step", "pop", "births", "deaths_energy", "cells_broken", "plant_intake", "meat_intake", "regrowth", "shaded",
                         "barren", "soil", "tree_res", "fat_stock", "mass_p50", "mass_p90", "mass_max", "size_p50", "size_p90",
                         "intake_per_gut", "muscle_mean", "digestive_mean", "pace", "age_p50", "age_p90"], logs)
    TEXT.update(TEXTS)
    TEXT["gallery"] = gallery(GALLERY, GALLERY_CAPTION) if GALLERY else ""
    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>e056 More sun under the clock - Report</title>
<style>{CSS}</style>
</head>
<body>
<main>
<h1>e056: More sun under the clock</h1>
<p class="sub">Experiment report - 2026-09-12 - e055's world run at one, two and four suns, seeds 9-14 (#65). Answer: {TEXT["sub_answer"]}</p>

<section class="tldr">
<h2>TL;DR</h2>
<p>{TEXT["tldr"]}</p>
</section>

<h2>1. Question</h2>
<p>{TEXT["question"]}</p>
<ol>
  <li><strong>Size rises with the sun:</strong> the winners' blocks and the 90th percentile of the mass rise from sun 1 to 2 to 4, within a world state.</li>
  <li><strong>Or it is still number:</strong> the bodies rise with the sun and the size does not - the ceiling is the income, and the clock did not lift it.</li>
  <li><strong>The world stands:</strong> every winter floor above 50.</li>
</ol>

<h2>2. The world</h2>
<p>{TEXT["world"]}</p>
{DIAGRAM}
<p><strong>Runs.</strong> {TEXT["runs"]}</p>
<ul class="measures">
  <li><strong>mass p90, size p90</strong> - the 90th percentile of a body's mass and of its blocks.</li>
  <li><strong>winner's body</strong> - blocks in the mean body of the lineage holding the most body-steps of the last third.</li>
  <li><strong>intake per gut</strong> - matter a gut block takes per step.</li>
  <li><strong>grown, shaded, barren</strong> - the light a step, split into what became plant, what the canopy held back, and what fell on soil-less ground.</li>
  <li><strong>state</strong> - hunter when more than 0.03 blocks are broken per body per step (e045).</li>
  <li><strong>kills' share, diversity</strong> - the flesh of kills in what bodies eat; the diversity number (#42).</li>
</ul>

<h2>3. Results</h2>
<p>Means over the second half (steps 50,000-100,000). Cells are sun 1 / sun 2 / sun 4 on the same seed; sun 4 ran on seeds 9-11.</p>
<div class="tw"><table>
<thead><tr><th>seed</th><th>state</th><th>mass p90</th><th>size p90</th><th>winner's body</th><th>intake per gut</th><th>bodies</th><th>lowest floor</th><th>kills' share</th><th>diversity</th></tr></thead>
<tbody>{seed_rows}</tbody></table></div>
<ol class="verdicts">
{TEXT["verdicts"]}
</ol>

<h3>3.1 {TEXT["h_light"]}</h3>
<div class="grid2">
{"".join(charts_light)}
</div>
<p>{TEXT["p_light"]}</p>

<h3>3.2 {TEXT["h_size"]}</h3>
<div class="grid2">
{"".join(charts_size)}
</div>
<p>{TEXT["p_size"]}</p>

<h3>3.3 {TEXT["h_many"]}</h3>
<div class="grid2">
{"".join(charts_many)}
</div>
<p>{TEXT["p_many"]}</p>

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
<p>Every log step (10,000 steps) of the fifteen runs. The full data are in <code>results/*.csv</code> (sun 1 is e055's batch, in <code>experiments/e055_span/results</code>). Build this report with <code>uv run python experiments/e056_sun/report.py</code>.</p>
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
    ("sun 1, seed 13", 0, 13, 462, "the big hunter", "A shell across the front row over a body of muscle and gut: armour where it meets what it bites, on the biggest frame of the batch."),
    ("sun 1, seed 12", 0, 12, 1845, "the wide hunter", "The same plan on a squarer frame, 40% of its intake flesh: what sun 1 grows when the world hunts."),
    ("sun 2, seed 11", 1, 11, 557, "the muscled grazer", "Almost all muscle on a 4x4 frame, speed 0.34: the fastest of the six, and the biggest winner under sun 2."),
    ("sun 2, seed 10", 1, 10, 112, "the thin hunter", "A narrow column on a wide grid, half its intake flesh: it hunts, and dies at a mean age of 182 steps."),
    ("sun 4, seed 10", 2, 10, 2226, "the lawn body", "Muscle and gut in equal parts on a 4x4 frame: what the crowd wins with when the ground is grazed flat."),
    ("sun 4, seed 11", 2, 11, 2102, "the lawn body again", "A different seed, the same frame, more gut than muscle - and it lives to a mean age of 1,744 steps."),
]
GALLERY_CAPTION = ("The usual grown body of the leading lineage of six runs, front up (orange muscle, aqua gut, yellow sensor, blue hard). "
                   "Down the list the sun rises and the winners shrink: the big frames belong to the poorest world.")

TEXTS = {
    "sub_answer": ("no. Four times the light grows 1.3 times the plant and 64% more bodies, and the winners get smaller, not bigger. "
                   "The sun stays 1."),
    "tldr": ("e038 found a body's size capped by the income a gut takes from crowded ground, and extra sun buying more bodies rather "
             "than bigger ones. e055's clock made a big body cheap per unit of mass, so the question was worth asking again. It is still "
             "number: mass p90 falls from 46 to 38 from sun 1 to sun 4, a gut block still takes 0.0019-0.0022 of matter a step, and half "
             "the extra light falls on ground with no soil left to grow from."),
    "question": ("The world has one size axis, the clock (e055): a body of mass m takes (16/m)^0.5 turns a world step, so its upkeep comes "
                 "to about m^0.5 instead of m. That changes the cost side of e038's arithmetic, which measured the ceiling on size as the "
                 "income a gut block can take. With being big now cheap, does a richer world buy size instead of number?"),
    "world": ("No new law: one argument moves. The sun multiplies every cell's regrowth rate, and the rain's cap with it, so a world that "
              "burns twice as much can rain it back. What it does not multiply is the matter: the 140,139 units of this world are the same "
              "at every sun, and a cell can only grow what its own soil holds."),
    "runs": ("Pilots on seed 9, 20,000 steps, at suns 1, 2 and 4: the sun 1 pilot reproduced e055's number for number, so the sun 1 control "
             "is e055's kept batch and was not run again. The batch: sun 2 on seeds 9-14 and sun 4 on seeds 9-11, 100,000 steps. Nine runs, "
             "30 minutes on the Mac."),
    "verdicts": ("<li><span class=\"verdict no\">No</span> Mass p90 is 46.3 / 44.2 / 37.7 over the seeds run at every sun, and within a "
                 "state the winners hold flat or shrink: 19.4 / 19.5 / 14.3 blocks in the grazing worlds.</li>"
                 "<li><span class=\"verdict yes\">Yes</span> Bodies rise 44% at sun 2 and 64% at sun 4 - far short of the light - with the "
                 "intake per gut block pinned at 0.0019-0.0022.</li>"
                 "<li><span class=\"verdict yes\">Yes</span> Winter floors 886-2,201 against the control's 524-838, and no run died.</li>"),
    "h_light": "Four times the light grows 1.3 times the plant",
    "p_light": ("The sun is a rate, and it acts on the soil a cell still holds. Raising it pulls matter out of the ground faster than the "
                "world returns it: the free soil falls from half of everything to a fourteenth, and light landing on empty ground grows "
                "nothing - 2% of it at sun 1, 50% at sun 4. What leaves the soil is standing in the crowd's fat, which more than doubles."),
    "h_size": "The bodies do not grow",
    "p_size": ("Nothing rises with the sun. The two worlds where the sun made the biggest difference to the winner are the two where the "
               "state changed - a hunting world grows a bigger body than a grazing one at any sun - and in the three grazing worlds run at "
               "sun 4, the winner is the fourteen-block body this world has been selecting since e043."),
    "h_many": "The crowd takes the extra food, and thins it back out",
    "p_many": ("A gut block takes the same 0.002 of matter a step under one sun and under four. That is e038's result again under a law "
               "that was supposed to have changed it: what a body earns is set by how often it reaches ground that has something on it, "
               "and more light means more mouths on the same ground rather than more on each mouth."),
    "h_world": "A richer world is safer, and stops hunting",
    "p_world": ("Winter floors double and then triple, and the mean age rises from 795 steps to 1,420: plenty is a buffer against the "
                "winter. Hunting goes the other way. Three of six worlds hunt at sun 1, two of six at sun 2 and none of the three at "
                "sun 4 - with prey this cheap to catch and plants this cheap to eat, the tooth stops paying. Three seeds cannot settle "
                "that last one."),
    "discussion": ("<p>We raised the wrong dial. The sun sets the rate at which soil becomes plant; the world's income is the matter "
                   "cycling through it, and that is fixed. Past sun 2 the extra light falls on cells with nothing to grow: the plant grown "
                   "per step is 87.8 at sun 2 and 88.5 at sun 4.</p>"
                   "<p>What did arrive went to number. The crowd grazes every cell back to where a gut block earns 0.002 a step, so a "
                   "body's income is a property of the crowd and not of the sun - e038's result, from before the clock existed. The clock "
                   "made a big body cheaper to run; it did not make food easier to reach, and reach is what binds.</p>"
                   "<p>And plenty is not what these bodies lack: room is. Before the sun is touched, 60% of the forward moves a body tries "
                   "fail because the way is taken and 29% of its children find no free cell; at sun 2 that becomes 63% and 34%. More matter "
                   "would buy what this light bought. What is missing is something that thins the crowd or tells one cell from another.</p>"),
    "conclusion": ("Not kept: the season world stays at sun 1. Two experiments have now tried to grow a bigger body by enriching the world "
                   "(e038, e056) and both bought numbers instead - and the richer the world, the less it hunts: blocks broken per body per "
                   "step are 0.019 / 0.022 / 0.006 at sun 1, 2 and 4. Next: fouling (#56), a worsening that falls on the body that stays "
                   "put - the crowd making its own patchiness in a world where every cell is alike - and then the brain (#58)."),
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
