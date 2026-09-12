#!/usr/bin/env python3
"""Build report.html for this experiment.

Charts: matplotlib, exported as SVG and inlined. Diagram: hand-written SVG.
Run from the repo root: uv run python experiments/e049_band/report.py
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

HEAD = "128_sigma"
TAIL = "_r64_f0_flat_eyes8_flesh1_w1_season2_digest0_sidegrow_store5_yolk0_breed0_winterhigh_water0.1_leach0.01_depth0.01_mix0.2_strict_sat_hold_wear3000_corner_motor"
WIDTH = 128  # world cells across
GRAIN = (2, 64)  # the batch's grain: patch width (sigma) and cells of the world per patch
PILOT_GRAINS = [(0, 0, "flat", 5), (2, 64, "grain 8", 0), (4, 256, "grain 16", 2)]  # sigma, patch, name, color slot


def name(sigma=0, patch=0, seed=9):
    """A run's file prefix: e048's world under the motor, with the food's width and grain (sigma 0: the flat world)."""
    return f"{HEAD}{sigma:g}{TAIL}{'_patch' + str(patch) if sigma else ''}_seed{seed}"


def run(law, seed):
    """law 0: the food in patches 8 cells apart; 1: the flat world (the same code with a uniform sun)."""
    return name(*(GRAIN if law == 0 else (0, 0)), seed)


def folder(law):
    return HERE


LAWS = {0: ("patchy", 0), 1: ("flat", 5)}  # name, color slot
STEPS = 100_000
SEASON = 20_000
LOG = 10_000  # steps per log.csv row
PILOT_STEPS = 20_000
SEEDS = [9, 10, 11, 12]
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
                rich=half_mean(d, "rich"), plant_rich=half_mean(d, "plant_rich"), plant_thin=half_mean(d, "plant_thin"),
                pop_rich=half_mean(d, "pop_rich"), hunger_rich=half_mean(d, "hunger_rich"), hunger_thin=half_mean(d, "hunger_thin"),
                starve_rich=starve(d, bodies, "rich"), starve_thin=starve(d, bodies, "thin"),
                travel=travel(r, fo), travel_all=travel(r, fo, 0, 10**9),
                pace=half_mean(d, "pace"), turned=half_mean(d, "turned"), age_p50=half_mean(d, "age_p50"), age_p90=half_mean(d, "age_p90"),
                lives=li, life=li["all"], life_light=li["light"], life_heavy=li["heavy"], life_ratio=li["ratio"],
                mass=half_mean(d, "mass_p50"), mass_p90=half_mean(d, "mass_p90"), intake=half_mean(d, "intake_per_gut"),
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


# Hand-written mechanism diagram: a line of 64 world cells across the world (12.2 px a cell), the
# regrowth each cell gets as the sum of the Gaussian patches around it (one patch per 64 cells,
# width 2, as the batch), against the flat world's rate (the dashed line, the same food per cell).
_DX0, _DX1, _DBASE, _DCELLS, _DTOP = 40, 820, 230, 64, 118  # the strip, the base line, and the height a peak may reach
_DSTEP = (_DX1 - _DX0) / _DCELLS


def _patch_line():
    """(the curve as SVG, the spans above the flat rate, px per unit of the flat rate): a line across a patchy world
    at the batch's grain, scaled so that the tallest peak is _DTOP px above the base."""
    rng = random.Random(7)
    sigma, area = GRAIN
    centers = [(rng.uniform(-6, _DCELLS + 6), rng.gauss(0, 4)) for _ in range(int(_DCELLS * 17 / area) + 12)]
    peak = area / (2 * math.pi * sigma * sigma)  # in units of the flat world's rate

    def at(x):
        return sum(peak * math.exp(-((x - cx) ** 2 + cy * cy) / (2 * sigma * sigma)) for cx, cy in centers)
    xs = [i / 4 for i in range(_DCELLS * 4 + 1)]
    ys = [at(x) for x in xs]
    unit = _DTOP / max(ys)
    path = "M" + " L".join(f"{_DX0 + x * _DSTEP:.1f},{_DBASE - y * unit:.1f}" for x, y in zip(xs, ys))
    spans, run_start = [], None
    for x, y in zip(xs, ys):
        if y >= 1 and run_start is None:
            run_start = x
        elif y < 1 and run_start is not None:
            spans.append((run_start, x))
            run_start = None
    if run_start is not None:
        spans.append((run_start, xs[-1]))
    rich = "".join(f'<rect x="{_DX0 + a * _DSTEP:.1f}" y="{_DBASE - _DTOP - 10}" width="{(b - a) * _DSTEP:.1f}" height="{_DTOP + 10}" '
                   f'fill="var(--s1)" fill-opacity="0.13" stroke="none"/>' for a, b in spans)
    return path, rich, unit


_DPATH, _DRICH, _DUNIT = _patch_line()
_DFLAT = _DBASE - _DUNIT

DIAGRAM = f"""
<figure class="fig diagram">
<svg viewBox="0 0 880 336" width="100%" role="img" aria-label="A line across the world: the food's regrowth comes in patches about 8 cells apart, each carrying the regrowth of 64 cells, against the flat world's even rate" font-size="12" fill="currentColor" stroke="currentColor">
  <defs><marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0 L10 5 L0 10 z" fill="currentColor" stroke="none"/></marker></defs>
  <g stroke="none">
    <text x="{_DX0}" y="24" font-weight="600">regrowth of a cell, along a line of 64 world cells</text>
    <text x="{_DX1}" y="24" text-anchor="end">patch: width 2, one per 64 cells</text>
  </g>
  {_DRICH}
  <line x1="{_DX0}" y1="{_DBASE}" x2="{_DX1}" y2="{_DBASE}" stroke-opacity="0.35"/>
  <line x1="{_DX0}" y1="{_DFLAT:.1f}" x2="{_DX1}" y2="{_DFLAT:.1f}" stroke-opacity="0.6" stroke-dasharray="4 3"/>
  <path d="{_DPATH}" fill="none" stroke-width="1.8" stroke="var(--s1)"/>
  <g stroke="none">
    <text x="{_DX0}" y="{_DBASE + 22}">shaded: rich land, 37% of the cells</text>
    <text x="{_DX1}" y="{_DBASE + 22}" text-anchor="end">between: thin land, where a body starves 1.2-1.4 times as often</text>
  </g>
  <line x1="{_DX0}" y1="{_DBASE + 42}" x2="{_DX0 + 26}" y2="{_DBASE + 42}" stroke-opacity="0.6" stroke-dasharray="4 3"/>
  <line x1="{_DX0 + 8 * _DSTEP:.0f}" y1="{_DBASE + 68}" x2="{_DX0 + 16 * _DSTEP:.0f}" y2="{_DBASE + 68}" stroke-width="1.6" marker-end="url(#ah)"/>
  <g stroke="none">
    <text x="{_DX0 + 34}" y="{_DBASE + 46}">the flat world of every experiment since e019: this rate on every cell, and the same food in all</text>
    <text x="{_DX0 + 17 * _DSTEP:.0f}" y="{_DBASE + 72}">8 cells to the next patch: 133 steps at full speed, against a life of 200-300 steps</text>
    <text x="{_DX0}" y="{_DBASE + 98}">A cell under a body does not grow, so a body that stays empties its patch; the patch comes back at the world's own rate.</text>
  </g>
</svg>
<figcaption>Figure 1. The law: the world's regrowth, until now spread evenly over every cell, is laid down in Gaussian patches about 8 cells apart. The sum over the world is unchanged - only where the food lands.</figcaption>
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
            print(f"seed {s} {LAWS[law][0]:8s} {'HUNTER' if x['hunter'] else 'grazer'} floor {x['floor_txt']} kills {x['share']:.1%} "
                  f"| bodies {x['bodies']:.0f} floors {x['floors']} births {x['births']:.2f} age {x['age']:.0f} lineages {x['lineages']:.1f}")
            print(f"      travel p50 {fmt_opt(x['travel'], lambda v: f'{v:.2f}')} (all ages {fmt_opt(x['travel_all'], lambda v: f'{v:.2f}')}) "
                  f"moved {x['moved']:.4f} stalled {x['stalled']:.2f} blocked {x['blocked']:.2f} speed {x['speed']:.3f} muscle {x['muscle']:.2f} gut {x['gut']:.2f}")
            print(f"      rich {x['rich']:.3f} plant rich/thin {x['plant_rich']:.2f}/{x['plant_thin']:.2f} pop_rich {x['pop_rich']:.3f} "
                  f"starve thin/rich {1000 * x['starve_thin']:.2f}/{1000 * x['starve_rich']:.2f} per 1,000 body-steps "
                  f"({x['starve_thin'] / x['starve_rich']:.2f}x)" if x['starve_rich'] == x['starve_rich'] else "")
            print(f"      hunger {x['hunger']:.2f} age p50/p90 {x['age_p50']:.0f}/{x['age_p90']:.0f} mass p50 {x['mass']:.1f} "
                  f"size p50 {x['size']:.1f} intake/gut {x['intake']:.4f} | top {i} {share:.0%} {cells:.1f} cells {muscle:.1f} muscle "
                  f"{gut:.1f} gut {meat:.0%} flesh speed {speed:.2f} | diversity {x['div']} of {x['wins']}")
    for law in LAWS:
        xs = [st[law][s] for s in SEEDS if st[law][s]]
        if not xs:
            continue
        mean = lambda k: sum(x[k] for x in xs) / len(xs)
        print(f"{LAWS[law][0]}: hunter worlds {sum(x['hunter'] for x in xs)} of {len(xs)}; bodies {mean('bodies'):.0f}; "
              f"floors {[x['floor'] for x in xs]}; travel {[round(x['travel'], 2) if x['travel'] else None for x in xs]}; "
              f"moved {mean('moved'):.4f}; age {mean('age'):.0f}; intake {mean('intake'):.4f}; div {[x['div'] for x in xs]}")
    for law in LAWS:
        print(f"{LAWS[law][0]} travel by age (median, n):", [(round(m, 2), n) for m, n in travel_by_age(law)])


def main():
    st = all_stats()
    logs = {f"{LAWS[law][0]}, seed {s}": load_csv(f"results/{run(law, s)}_log.csv") for law in LAWS for s in SEEDS if st[law][s]}
    small = lambda y, _p: f"{y:.3f}".rstrip("0").rstrip(".") if y else "0"
    grow, rich = field_map(run(0, SEEDS[0]))
    n_reg, big_reg, mid_reg = regions(rich)
    grain_log = load_csv(f"results/{run(0, SEEDS[0])}_log.csv")
    flat_log = load_csv(f"results/{run(1, SEEDS[0])}_log.csv")

    charts_land = [
        map_chart("Where the food falls, seed 9", "The regrowth of every cell of the 128x128 world, rebuilt from the patch centers at step "
                  "100,000. The flat world is the pale end of this scale on every cell.",
                  grow, 4 * RATE, labels=["nothing", "4 times the flat world's rate"]),
        time_chart("The standing plant, rich land and thin", "Seed 9, per cell. The flat world's line is what one cell held before; a gap "
                   "between the two is a world worth crossing.",
                   [("rich land", 0, grain_log["step"], grain_log["plant_rich"]),
                    ("thin land", 2, grain_log["step"], grain_log["plant_thin"]),
                    ("flat world", 5, flat_log["step"], flat_log["mean_res"])]),
    ]
    charts_uneven = [
        seed_chart("Bodies standing on the rich land, by seed", "Second half. The rich land is 37% of the world, so the dotted line is a "
                   "crowd that ignores it.", st, "pop_rich", laws=(0,), percent=True, hline=0.37, ymax=0.75),
        seed_chart("Starving on the thin land and the rich, by seed", "Bodies that starve per 1,000 body-steps, second half, in the patchy "
                   "world.", st, "starve_thin", laws=(0,), fmt=lambda y, _p: f"{1000 * y:.1f}",
                   second=("starve_rich", 2, "rich land"), label="thin land"),
    ]
    charts_walk = [
        travel_chart("How far a body stands from where it was born", "Median travel in world cells of the bodies alive at step 100,000, "
                     "by age, four seeds together."),
        map_chart("The rich land, seed 9", f"The cells that grow at or above the flat world's rate: 37% of the world in {n_reg} connected "
                  f"regions, the largest {big_reg:,} cells. A life's travel fits inside one.", rich, 1, slot=0),
    ]
    charts_world = [
        seed_chart("Bodies, by seed", "Bodies alive over the second half (steps 50,000-100,000).", st, "bodies", laws=(0, 1)),
        seed_chart("The lowest winter floor, by seed", "The smallest population of any season. The dotted line is the floor the "
                   "hypothesis asked for.", st, "floor", laws=(0, 1), hline=50),
        seed_chart("The flesh of kills in what the bodies eat, by seed", "Second half.", st, "share", laws=(0, 1), percent=True),
    ]

    def pair(s, key, f, laws=(0, 1)):
        return "<td>" + " / ".join(fmt_opt(st[law][s][key] if st[law][s] else None, f) for law in laws) + "</td>"

    seed_rows = "".join(
        f"<tr><td>{s}</td>{pair(s, 'travel', lambda v: f'{v:.1f}')}{pair(s, 'moved', lambda v: f'{v:.3f}')}"
        f"{pair(s, 'age', lambda v: f'{v:,.0f}')}{pair(s, 'intake', lambda v: f'{v:.4f}')}"
        f"{pair(s, 'bodies', lambda v: f'{v:,.0f}')}{pair(s, 'floor_txt', str)}{pair(s, 'share', lambda v: f'{v:.0%}')}"
        f"{pair(s, 'div', lambda v: f'{v}')}</tr>"
        for s in SEEDS if all(st[law][s] for law in LAWS))
    land_rows = "".join(
        f"<tr><td>{s}</td><td>{st[0][s]['rich']:.0%}</td><td>{st[0][s]['plant_rich']:.2f} / {st[0][s]['plant_thin']:.2f}</td>"
        f"<td>{st[0][s]['pop_rich']:.0%}</td><td>{1000 * st[0][s]['starve_thin']:.2f} / {1000 * st[0][s]['starve_rich']:.2f}</td>"
        f"<td>{st[0][s]['starve_thin'] / st[0][s]['starve_rich']:.2f}x</td></tr>"
        for s in SEEDS if st[0][s])
    tables = data_table(["step", "pop", "births", "deaths_energy", "cells_broken", "plant_intake", "meat_intake", "mean_res",
                         "rich", "plant_rich", "plant_thin", "pop_rich", "hunger_rich", "hunger_thin",
                         "muscle_mean", "speed_mean", "moved", "stalled", "blocked", "age_p50", "size_p50"], logs)
    TEXT.update(TEXTS)
    TEXT["gallery"] = gallery(GALLERY, GALLERY_CAPTION) if GALLERY else ""
    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>e054 The grain of the food - Report</title>
<style>{CSS}</style>
</head>
<body>
<main>
<h1>e054: The grain of the food</h1>
<p class="sub">Experiment report - 2026-09-12 - the same food, laid in patches a body could cross, seeds 9-12 (#64). Answer: {TEXT["sub_answer"]}</p>

<section class="tldr">
<h2>TL;DR</h2>
<p>{TEXT["tldr"]}</p>
</section>

<h2>1. Question</h2>
<p>{TEXT["question"]}</p>
<ol>
  <li><strong>Bodies travel:</strong> the median travel of a body aged 200-500 steps above the flat world's 2.5-5 cells, on three seeds of four.</li>
  <li><strong>The crowd is uneven, and the thin land is where hunger kills:</strong> more standing plant on the rich land, and starvation falling on the thin land above its share of the bodies.</li>
  <li><strong>The world stands:</strong> every winter floor above 50.</li>
</ol>

<h2>2. The world</h2>
<p>{TEXT["world"]}</p>
{DIAGRAM}
<p><strong>Runs.</strong> {TEXT["runs"]}</p>
<ul class="measures">
  <li><strong>travel</strong> - how far a body stands from where it was born, in world cells (median, bodies aged 200-500 steps).</li>
  <li><strong>moved</strong> - sub-cells a body moves by its own actions, per step (4 sub-cells to a cell).</li>
  <li><strong>rich land</strong> - the cells whose regrowth is at or above the flat world's rate; the rest is thin.</li>
  <li><strong>starving</strong> - bodies that starve per 1,000 body-steps, on the thin land and on the rich.</li>
  <li><strong>intake per gut</strong> - matter a gut block takes per step: how well the world feeds a body.</li>
  <li><strong>kills' share, diversity</strong> - the flesh of kills in what bodies eat; the diversity number (#42).</li>
</ul>

<h2>3. Results</h2>
<p>Means over the second half (steps 50,000-100,000). Pairs are the patchy world / the flat world, on the same seed.</p>
<div class="tw"><table>
<thead><tr><th>seed</th><th>travel</th><th>moved</th><th>mean age</th><th>intake per gut</th><th>bodies</th><th>lowest floor</th><th>kills' share</th><th>diversity</th></tr></thead>
<tbody>{seed_rows}</tbody></table></div>
<ol class="verdicts">
{TEXT["verdicts"]}
</ol>

<h3>3.1 {TEXT["h_land"]}</h3>
<div class="grid2">
{"".join(charts_land)}
</div>
<p>{TEXT["p_land"]}</p>

<h3>3.2 {TEXT["h_uneven"]}</h3>
<div class="grid2">
{"".join(charts_uneven)}
</div>
<div class="tw"><table>
<thead><tr><th>seed</th><th>rich land</th><th>standing plant rich / thin</th><th>bodies on the rich land</th><th>starving thin / rich</th><th>thin over rich</th></tr></thead>
<tbody>{land_rows}</tbody></table></div>
<p>{TEXT["p_uneven"]}</p>

<h3>3.3 {TEXT["h_walk"]}</h3>
<div class="grid2">
{"".join(charts_walk)}
</div>
<p>{TEXT["p_walk"]}</p>

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
<p>Every log step (10,000 steps) of the eight runs. The full data are in <code>results/*.csv</code>. Build this report with <code>uv run python experiments/e054_grain/report.py</code>.</p>
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
    ("patchy, seed 9", 0, 9, 995, "the four by four", "Two rows of muscle over two of gut, no armor: the 4x4 form leads three of the four patchy worlds."),
    ("patchy, seed 10", 0, 10, 537, "the small gut", "Thirteen blocks and the slowest winner here (speed 0.19): on rich land a body pays for muscle it does not need."),
    ("patchy, seed 12", 0, 12, 775, "the wide gut", "Five by five, 14 gut to 8 muscle: the biggest winner of the patchy worlds, and still unarmored."),
    ("flat, seed 9", 1, 9, 325, "the armored hunter", "Seven blocks of armor in front of muscle and gut: half its intake is flesh, in a world the flat food made hunt."),
    ("flat, seed 12", 1, 12, 67, "the long hold", "The same armored front, 91,000 steps and 77% of the last third: no patchy world grew anything like it."),
    ("flat, seed 10", 1, 10, 677, "the flat grazer", "Twenty-three blocks, mostly gut, no armor: what wins a flat world that does not hunt."),
]
GALLERY_CAPTION = ("The usual grown body of six leading lineages, front up (orange muscle, aqua gut, yellow sensor, blue hard). Not one "
                   "winner of the patchy worlds carries armor, and they are smaller: 14-22 blocks against 23-28 flat.")

TEXTS = {
    "sub_answer": ("no. The patches merge into ribbons 35 cells across, so a body is born on the rich land and never has to leave it; "
                   "travel falls. Not kept."),
    "tldr": ("The world's food has always been spread evenly over every cell. Here the same food falls in patches about 8 cells apart - "
             "a distance a body could walk within its life. The land becomes uneven as asked (37% of it rich, twice the standing plant, "
             "the crowd gathering on it) and the world stands. But bodies travel less, not more, and the world grows 15% less food. "
             "Not kept."),
    "question": ("Measured in e048's world: the crowd eats the world down to its regrowth, and every place is equally thin - no bare "
                 "cells anywhere, the standing plant 0.9-1.7 of a cap of 8. A body walks 2.5-5 cells of a 128-cell world in a life "
                 "because nothing asks it to go anywhere. The machinery for uneven food has been in the code since e011, but at a grain "
                 "of 64 cells - further than any body can cross."),
    "world": ("One argument: the cells of the world per food patch. The regrowth of the world, until now the same on every cell, is laid "
              "down in Gaussian patches about 8 cells apart, each carrying the food of 64 cells and drifting one cell every 50 steps. "
              "The world grows exactly as much as before; only where it lands changes."),
    "runs": ("Pilots on seed 9, 20,000 steps, at grains of 8 and 16 cells against the flat world. Both stood, and the batch took grain 8, "
             "the one a body can cross within a life: seeds 9-12, 100,000 steps, patchy and flat on the same seeds, eight runs at once on "
             "the Mac, 25 minutes."),
    "verdicts": ("<li><span class=\"verdict no\">No</span> Travel is below the flat world's on three seeds of four, and lower at every "
                 "age: 0.6-8.5 cells against 1.3-11.6.</li>"
                 "<li><span class=\"verdict yes\">Yes</span> Twice the standing plant on the rich 37% of the land, 54-58% of the bodies "
                 "standing on it, and 1.2-1.4 times the starvation per body-step on the thin land.</li>"
                 "<li><span class=\"verdict yes\">Yes</span> Winter floors 365-704 against the flat world's 347-742, and no run "
                 "died.</li>"),
    "h_land": "The world becomes a mosaic",
    "p_land": ("The flat world is one even green: wherever a body stands, the ground gives the same 0.03 a step, a seventh of what its "
               "guts could take. The patchy world has somewhere to be - and somewhere not to be, 61% of it. Nothing else about the world "
               "changed, and the sum of the regrowth is the same in both."),
    "h_uneven": "The crowd gathers on the rich land, and starves off it",
    "p_uneven": ("Half again as many bodies stand on the rich land as its area would give, and they are fed better: a body on the thin "
                 "land starves 1.2-1.4 times as often. That is the pressure the law was meant to create, and it is there - but a body "
                 "does not have to walk to answer it, because its parents can be born on the rich land instead."),
    "h_walk": "Nothing walks: a patch is a place to hold",
    "p_walk": ("This is the finding. At every age the patchy world's bodies stand nearer their birthplace than the flat world's, and they "
               "move less per step. Rebuilt from the patch centers, the rich land is not islands: 37% of the world in 39-46 connected "
               "regions, the largest 35 cells across. A life's travel fits inside one."),
    "h_world": "The world stands, with fewer bodies and no tooth",
    "p_world": ("The patchy world holds 8% fewer bodies because it grows 15% less food: a cell can only grow what its own soil holds, and "
                "a patch draws 2.5 times the rate out of its cells, losing 7.6 a step to ground with nothing left. Hunting ends where it "
                "had been: no hunter world of four, against two flat."),
    "discussion": ("<p>The grain was chosen against a life's walk - 8 cells, 133 steps at full speed against a life of 200-300. That was "
                   "the wrong measure. Patches of width 2 laid one per 64 cells overlap into connected ribbons tens of cells across, so a "
                   "body born on the rich land grazes its way through a life without ever reaching an edge. What would make a body cross "
                   "is a patch smaller than a life's grazing, not a spacing shorter than a life's walk.</p>"
                   "<p>The second finding was not asked for: concentrating the same sun costs the world food, because the soil of a cell "
                   "is local. At 2.5 times the rate a patch runs its own cells dry, and a tenth of the sun falls on ground with nothing "
                   "left to grow from. Any law that gathers the light has to move the soil with it, or it is only a weaker sun.</p>"
                   "<p>What this does not show: what a sharper grain does (patches a body eats out within a life), whether patches that "
                   "move faster than a body lives would drag it along, and what a thirsty or slower-living body would do in this same "
                   "mosaic.</p>"),
    "conclusion": ("Not kept: the grain stays an argument at 4,096. The law does make the world uneven, and the crowd answers it by "
                   "gathering - but by being born on the rich land, not by walking to it, and the world pays 15% of its food for the "
                   "difference. Next: a grain small enough that a body eats out its patch within a life, and a soil that can supply it."),
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
