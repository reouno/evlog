#!/usr/bin/env python3
"""Build report.html for e059.

Charts: matplotlib, exported as SVG and inlined. Diagram: hand-written SVG.
Run from the repo root: uv run python experiments/e059_places/report.py
(`report.py numbers` prints the measures over the second half, for the README;
`report.py lineages` prints the top lineages of every run, to pick the gallery.)
"""
import csv
import html
import io
import json
import math
import os
import re
import sys
from collections import Counter, defaultdict

import matplotlib
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator

matplotlib.use("svg")

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from diversity import KINDS, census, hill, kind_of, rarefied  # noqa: E402

SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#8a8a86", "#c9c8c0", "#7b61ff"]  # slot 5 is the control
KIND_COLOR = {1: SERIES[0], 2: SERIES[1], 3: SERIES[3], 4: SERIES[2]}

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

WIDTH = 128          # world cells across
RATE = 0.01          # RES_GROWTH: what a cell grows per step at sun 1
SUN = 0.2            # the thin world (e058)
SIGMA, PATCH = 8, 1820   # the grain of the batch: width 8, one patch per 1,820 cells
STEPS = 300_000
SEASON = 20_000
LOG = 10_000         # steps per log.csv row
CENSUS = [100_000, 200_000, 300_000]  # agents.csv is written here
SEEDS = [9, 10, 11, 12, 13, 14]
MAP_SEED = 11        # the seed whose land the maps show
LAWS = {0: ("uniform", 5), 1: ("islands", 0)}  # name, color slot
STATE_LINE = 0.03    # blocks broken per body per step: above it a hunter world (e045)
RAREFY = 120         # bodies per draw when kinds are compared across worlds (#66)
UNIFORM_DIV = dict(kinds=22, rarefied=13.2, q1=5.89, q2=3.76)   # e058's probe, seed 9, 100,000 steps
CROWDED_DIV = dict(kinds=59, rarefied=27.7, q1=16.9, q2=9.2)    # the same seed at sun 1 (e058)


def run(law, seed):
    """law 0: the thin uniform world (the control, e058's probe); 1: the food in islands."""
    sg = SIGMA if law else 0
    patch = f"_patch{PATCH}" if law else ""
    return (f"128_sigma{sg}_r64_f0_flat_eyes8_flesh1_w1_season2_digest0_sidegrow_store5_yolk0_breed0"
            f"_winterhigh_water0.1_leach0.01_depth0.01_mix0.2_sun{SUN}"
            f"_strict_sat_hold_wear3000_corner_motor_clock0.5{patch}_seed{seed}")


# ---------- data ----------

def load_csv(path):
    with open(os.path.join(HERE, path)) as f:
        rows = [r for r in csv.DictReader(f) if None not in r.values()]
    return {k: [float(r[k]) for r in rows] for k in rows[0]}


def load_rows(path):
    with open(os.path.join(HERE, path)) as f:
        return [r for r in csv.DictReader(f) if None not in r.values()]


def lineage_rows(run_):
    by = defaultdict(list)
    for r in load_rows(f"results/{run_}_lineages.csv"):
        by[int(r["lineage"])].append(r)
    return by


def load_bodies(run_):
    out = {}
    with open(os.path.join(HERE, f"results/{run_}_bodies.jsonl")) as f:
        for line in f:
            try:
                d = json.loads(line)
            except json.JSONDecodeError:
                break
            out[d["id"]] = (int(d.get("side", 8)), d["cells"])
    return out


def read_frames(path):
    with open(os.path.join(HERE, path)) as f:
        for line in f:
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                return


def exists(run_):
    """A finished run: its log has reached the last step (a run still writing has fewer rows)."""
    path = os.path.join(HERE, f"results/{run_}_log.csv")
    if not (os.path.exists(path) and os.path.getsize(path) > 200):
        return False
    with open(path) as f:
        last = f.readlines()[-1].split(",")[0]
    return last.isdigit() and int(last) >= STEPS


def half(d, lo=STEPS // 2, hi=STEPS):
    return [i for i, t in enumerate(d["step"]) if lo < t <= hi and d["pop"][i] > 0]


def half_mean(d, key, lo=STEPS // 2, hi=STEPS):
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


def agents_rows(run_, step=STEPS):
    path = os.path.join(HERE, f"results/{run_}_agents.csv")
    if not os.path.exists(path):
        return []
    with open(path) as f:
        return [r for r in csv.DictReader(f) if int(r["step"]) == step]


AGE_BINS = [(0, 200), (200, 500), (500, 1000), (1000, 10 ** 9)]
AGE_NAMES = ["0-199", "200-499", "500-999", "1,000+"]


def travel(run_, lo=0, hi=10 ** 9):
    xs = [float(r["travel"]) for r in agents_rows(run_) if lo <= int(r["age"]) < hi]
    return median(xs)


def travel_by_age(law, least=5):
    """Per age bin, the median travel of the bodies alive at the last census, all seeds together."""
    rows = [r for s in SEEDS if exists(run(law, s)) for r in agents_rows(run(law, s))]
    out = []
    for lo, hi in AGE_BINS:
        xs = [float(r["travel"]) for r in rows if lo <= int(r["age"]) < hi]
        out.append((median(xs) if len(xs) >= least else float("nan"), len(xs)))
    return out


# ---------- diversity (#66): kinds over birth shapes ----------

def kinds_of(rows):
    c = Counter()
    for r in rows:
        k = kind_of([int(float(r["born_" + j])) for j in KINDS])
        if k:
            c[k] += 1
    return c


def div_of(rows):
    """(kinds, kinds rarefied to RAREFY bodies, q1, q2) over birth shapes; rarefied is None if too few."""
    c = kinds_of(rows)
    if not c:
        return dict(kinds=0, rarefied=None, q1=0.0, q2=0.0, n=0)
    q = hill(c)
    return dict(kinds=len(c), rarefied=rarefied(c, m=RAREFY), q1=q[1], q2=q[2], n=sum(c.values()))


def by_land(run_, step=STEPS):
    """The bodies of the last census split by the land they were born on."""
    rows = agents_rows(run_, step)
    return ([r for r in rows if r.get("born_rich") == "1"], [r for r in rows if r.get("born_rich") == "0"])


def mix_of(rows):
    """(the mean share of each kind of block in the birth shape, the mean birth size)."""
    if not rows:
        return [float("nan")] * len(KINDS), float("nan")
    tots = [sum(float(r["born_" + j]) for j in KINDS) for r in rows]
    out = [sum(float(r["born_" + k]) / t for r, t in zip(rows, tots) if t > 0) / len(rows) for k in KINDS]
    return out, sum(float(r["born_size"]) for r in rows) / len(rows)


# ---------- the land ----------

def field_map(run_):
    """The regrowth of every cell at the last long frame, rebuilt from the patch centres it carries, as rows of
    WIDTH; and the rich cells (at or above the thin world's own rate) the same way."""
    last = None
    for d in read_frames(f"results/{run_}_long.jsonl"):
        last = d
    grow = [RATE * SUN] * (WIDTH * WIDTH)
    if last and last.get("patches"):
        grow = [0.0] * (WIDTH * WIDTH)
        for cx, cy, sigma in last["patches"]:
            peak = RATE * SUN * PATCH / (2 * math.pi * sigma * sigma)
            r = int(math.ceil(3 * sigma))
            for dy in range(-r, r + 1):
                for dx in range(-r, r + 1):
                    c = ((cy + dy) % WIDTH) * WIDTH + (cx + dx) % WIDTH
                    grow[c] += peak * math.exp(-(dx * dx + dy * dy) / (2 * sigma * sigma))
    rows = lambda v: [v[y * WIDTH:(y + 1) * WIDTH] for y in range(WIDTH)]
    return rows(grow), rows([1.0 if g >= RATE * SUN else 0.0 for g in grow])


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


def plant_map(run_, step=STEPS):
    """The standing plant of every cell at `step` (soil.jsonl), as rows of WIDTH."""
    for d in read_frames(f"results/{run_}_soil.jsonl"):
        if d["step"] == step:
            v = d["plant"]
            return [v[y * WIDTH:(y + 1) * WIDTH] for y in range(len(v) // WIDTH)]
    return None


SUB = 4  # sub-cells per world cell


_frames = {}


def long_frames(run_, half_only=True):
    """The snapshot frames of a run (cached), from the second half by default."""
    if run_ not in _frames:
        _frames[run_] = list(read_frames(f"results/{run_}_long.jsonl"))
    return [d for d in _frames[run_] if not half_only or d["step"] >= STEPS // 2]


def segregation(run_, centres=None, last=6):
    """How much the lineages are cut up by place: the chance two bodies of one region share a lineage, over the
    chance any two bodies do. 1.0 is a crowd mixed through the world. A region is the nearest of the nine patch
    centres; the uniform runs are cut by the same nine centres their island run had."""
    wi = wn = ai = an = 0
    for d in long_frames(run_)[-last:]:
        cs = d["patches"] or centres
        if not cs:
            return None
        by, tot, allc, n = defaultdict(Counter), Counter(), Counter(), 0
        for a in d["agents"]:
            x, y = a[0] / SUB, a[1] / SUB
            reg = min(range(len(cs)), key=lambda k: min((x - cs[k][0]) % WIDTH, (cs[k][0] - x) % WIDTH) ** 2
                      + min((y - cs[k][1]) % WIDTH, (cs[k][1] - y) % WIDTH) ** 2)
            by[reg][a[4]] += 1
            tot[reg] += 1
            allc[a[4]] += 1
            n += 1
        wi += sum(v * (v - 1) for c in by.values() for v in c.values())
        wn += sum(m * (m - 1) for m in tot.values())
        ai += sum(v * (v - 1) for v in allc.values())
        an += n * (n - 1)
    return (wi / wn) / (ai / an) if wn and ai else None


# ---------- one run ----------

def fine(run_):
    """Every 1,000 steps (pop.csv): the bodies alive; lineages of 5 or more."""
    lin = Counter()
    for rows in lineage_rows(run_).values():
        for r in rows:
            lin[int(r["step"])] += 1
    d = load_csv(f"results/{run_}_pop.csv")
    d["lineages"] = [lin[int(t)] for t in d["step"]]
    return d


def floors(f):
    """Per season window: the trough and the peak of the population."""
    out = []
    for c in range(int(max(f["step"])) // SEASON):
        idx = [i for i, t in enumerate(f["step"]) if c * SEASON < t <= (c + 1) * SEASON]
        if not idx:
            continue
        lo = min(idx, key=lambda i: f["pop"][i])
        hi = max(idx, key=lambda i: f["pop"][i])
        out.append(dict(step=int(f["step"][lo]), pop=int(f["pop"][lo]), peak=int(f["pop"][hi])))
    return out


def top_lineage(run_):
    """The lineage holding the most body-steps of the last third: (id, share, mean cells)."""
    rows = load_rows(f"results/{run_}_lineages.csv")
    steps = [int(r["step"]) for r in rows]
    lo = max(steps) - (max(steps) - min(steps)) // 3
    total, cells = defaultdict(float), defaultdict(float)
    for r in rows:
        if int(r["step"]) < lo:
            continue
        i, n = int(r["lineage"]), float(r["size"])
        total[i] += n
        cells[i] += n * sum(float(r[k]) for k in KINDS)
    i = max(total, key=total.get)
    return i, total[i] / sum(total.values()), cells[i] / total[i]


def starve(d, bodies, land):
    """Starvations per body per step on the rich or the thin land (nan where there is no such land)."""
    share = half_mean(d, "pop_rich")
    here = bodies * (share if land == "rich" else 1 - share)
    return half_mean(d, f"hunger_{land}") / here if here > 0 else float("nan")


def stats(law, seed):
    r = run(law, seed)
    if not exists(r):
        return None
    d, f = load_csv(f"results/{r}_log.csv"), fine(r)
    idx = half(d)
    food = [eaten(d, i) for i in idx]
    plant, hunted, scav = (sum(x[j] for x in food) / len(food) for j in range(3))
    bodies = half_mean(f, "pop")
    broken = half_mean(d, "cells_broken") / LOG
    w = floors(f)
    died = int(d["step"][-1]) if d["pop"][-1] == 0 else None
    floor = 0 if died else min(x["pop"] for x in w)
    centres = None
    if law == 0 and exists(run(1, seed)):
        fr = long_frames(run(1, seed))
        centres = fr[-1]["patches"] if fr else None
    rich_rows, thin_rows = by_land(r)
    all_div = div_of(agents_rows(r))
    mix_all, size_all = mix_of(agents_rows(r))
    mix_rich, size_rich = mix_of(rich_rows)
    mix_thin, size_thin = mix_of(thin_rows)
    return dict(
        bodies=bodies, floor=floor, died=died, floor_txt=f"died at {died:,}" if died else f"{floor:,}",
        floors=[x["pop"] for x in w], peak=max(x["peak"] for x in w),
        births=half_mean(d, "births") / LOG, lineages=half_mean(f, "lineages"), broken=broken, per_body=broken / bodies,
        hunter=broken / bodies >= STATE_LINE, share=hunted / (plant + hunted + scav),
        regrowth=half_mean(d, "regrowth"), barren=half_mean(d, "barren"),
        barren_share=half_mean(d, "barren") / (RATE * SUN * WIDTH * WIDTH),
        blocked=half_mean(d, "blocked"), denied=half_mean(d, "births_no_room"), moved=half_mean(d, "moved"),
        covered=half_mean(d, "covered"), age=half_mean(d, "age_p50"),
        rich=half_mean(d, "rich"), pop_rich=half_mean(d, "pop_rich"),
        plant_rich=half_mean(d, "plant_rich"), plant_thin=half_mean(d, "plant_thin"),
        hunger_rich=half_mean(d, "hunger_rich"), hunger_thin=half_mean(d, "hunger_thin"),
        travel=travel(r), travel_grown=travel(r, 200, 500),
        starve_rich=starve(d, bodies, "rich"), starve_thin=starve(d, bodies, "thin"),
        starve_ratio=(starve(d, bodies, "thin") / starve(d, bodies, "rich")) if starve(d, bodies, "rich") else float("nan"),
        kinds=all_div["kinds"], rarefied=all_div["rarefied"], q1=all_div["q1"], q2=all_div["q2"],
        born_size=size_all, mix=mix_all,
        size_rich=size_rich, size_thin=size_thin, mix_rich=mix_rich, mix_thin=mix_thin,
        n_rich=len(rich_rows), n_thin=len(thin_rows),
        muscle_gap=(mix_thin[1] - mix_rich[1]) if thin_rows and rich_rows else float("nan"),
        gut_gap=(mix_thin[3] - mix_rich[3]) if thin_rows and rich_rows else float("nan"),
        div_rich=div_of(rich_rows), div_thin=div_of(thin_rows),
        top=top_lineage(r), segregation=segregation(r, centres),
        div_at=[div_of(agents_rows(r, c)) for c in CENSUS],
    )


def all_stats():
    return {law: {s: stats(law, s) for s in SEEDS} for law in LAWS}


def arm(st, law, key):
    vals = [st[law][s][key] for s in SEEDS if st[law][s] and st[law][s][key] is not None]
    return sum(vals) / len(vals) if vals else float("nan")


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


def figure(title, subtitle, svg):
    return f"""
<figure class="fig">
  <figcaption><strong>{html.escape(title)}</strong><span>{html.escape(subtitle)}</span></figcaption>
  {svg}
</figure>"""


def seed_chart(title, subtitle, st, key, laws=(0, 1), percent=False, ymax=None, hline=None, hlabel=None, fmt=None):
    """One dot per seed and arm: st[law][seed][key]; `hline` draws a dotted reference line."""
    fig, ax = new_axes("seed")
    for k, law in enumerate(laws):
        dx = (k - (len(laws) - 1) / 2) * 0.12
        pts = [(s + dx, st[law][s][key]) for s in SEEDS if st[law][s] and st[law][s][key] is not None]
        ax.plot([p[0] for p in pts], [p[1] for p in pts], color=SERIES[LAWS[law][1]], linestyle="none",
                marker="o", markersize=7, label=LAWS[law][0])
    if hline is not None:
        ax.axhline(hline, color=INK, linewidth=1, linestyle=":", label=hlabel)
    vals = [st[law][s][key] for law in laws for s in SEEDS if st[law][s] and st[law][s][key] is not None]
    vals += [hline] if hline is not None else []
    ax.set_ylim(min(vals + [0.0]) * 1.15, ymax if ymax is not None else max(vals, default=1.0) * 1.2)
    ax.set_xticks(SEEDS)
    ax.yaxis.set_major_formatter(fmt or ((lambda y, _p: f"{y:.0%}") if percent else kfmt))
    ax.yaxis.set_major_locator(MaxNLocator(4, steps=[1, 2, 5, 10]))
    legend_above(ax, len(laws) + (1 if hlabel else 0))
    return figure(title, subtitle, to_svg(fig))


def travel_chart(title, subtitle):
    fig, ax = new_axes(f"age at step {STEPS // 1000},000 (steps)".replace("300,000", "300,000"))
    for law in LAWS:
        ys = [m for m, _n in travel_by_age(law)]
        ax.plot(range(len(AGE_BINS)), ys, color=SERIES[LAWS[law][1]], marker="o", markersize=6, linewidth=1.6,
                label=LAWS[law][0])
    ax.set_xticks(range(len(AGE_BINS)), AGE_NAMES)
    ax.margins(x=0.05)
    ax.set_ylim(0)
    ax.yaxis.set_major_locator(MaxNLocator(4, steps=[1, 2, 5, 10]))
    legend_above(ax, 2)
    return figure(title, subtitle, to_svg(fig))


def census_chart(title, subtitle, st, key):
    """One line per arm: the mean over seeds of a diversity number at each census."""
    fig, ax = new_axes()
    for law in LAWS:
        ys = []
        for i, _c in enumerate(CENSUS):
            vals = [st[law][s]["div_at"][i][key] for s in SEEDS if st[law][s] and st[law][s]["div_at"][i][key] is not None]
            ys.append(sum(vals) / len(vals) if vals else float("nan"))
        ax.plot(CENSUS, ys, color=SERIES[LAWS[law][1]], marker="o", markersize=6, linewidth=1.6, label=LAWS[law][0])
    ax.axhline(CROWDED_DIV[key], color=INK, linewidth=1, linestyle=":", label="the crowded world (sun 1)")
    ax.set_ylim(0)
    ax.yaxis.set_major_locator(MaxNLocator(4, steps=[1, 2, 5, 10]))
    legend_above(ax, 3)
    return figure(title, subtitle, to_svg(fig))


def floor_chart(title, subtitle):
    """The season troughs over the run, mean over the seeds, one line per arm."""
    fig, ax = new_axes("season")
    for law in LAWS:
        cols = defaultdict(list)
        for s in SEEDS:
            if not exists(run(law, s)):
                continue
            for k, w in enumerate(floors(fine(run(law, s)))):
                cols[k].append(w["pop"])
        xs = sorted(cols)
        ax.plot([x + 1 for x in xs], [min(cols[x]) for x in xs], color=SERIES[LAWS[law][1]],
                marker="o", markersize=5, linewidth=1.6, label=LAWS[law][0])
    ax.axhline(50, color=INK, linewidth=1, linestyle=":", label="50 bodies")
    ax.set_ylim(0)
    ax.margins(x=0.03)
    ax.yaxis.set_major_formatter(kfmt)
    ax.yaxis.set_major_locator(MaxNLocator(4, steps=[1, 2, 5, 10]))
    legend_above(ax, 3)
    return figure(title, subtitle, to_svg(fig))


def time_chart(title, subtitle, lines, ylabel_pct=False, ymax=None):
    fig, ax = new_axes()
    for label, slot, xs, ys in lines:
        ax.plot(xs, ys, color=SERIES[slot], linewidth=1.4, label=label)
    ax.set_ylim(0, ymax)
    ax.yaxis.set_major_formatter((lambda y, _p: f"{y:.0%}") if ylabel_pct else kfmt)
    ax.yaxis.set_major_locator(MaxNLocator(4, steps=[1, 2, 5, 10]))
    legend_above(ax, min(len(lines), 3))
    return figure(title, subtitle, to_svg(fig))


def map_chart(title, subtitle, grid, vmax, labels=None, slot=2):
    """One map of the 128x128 world: a value per cell, in one color at rising opacity."""
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


def mix_chart(title, subtitle, st):
    """The mean birth shape of the bodies born on the rich land and on the thin, all seeds of the island arm."""
    fig, ax = new_axes("")
    rows_rich = [r for s in SEEDS if st[1][s] for r in by_land(run(1, s))[0]]
    rows_thin = [r for s in SEEDS if st[1][s] for r in by_land(run(1, s))[1]]
    mr, sr = mix_of(rows_rich)
    mt, stn = mix_of(rows_thin)
    xs = list(range(len(KINDS)))
    ax.bar([x - 0.2 for x in xs], mr, 0.38, color=SERIES[2], label=f"born on the rich land (n={len(rows_rich):,})")
    ax.bar([x + 0.2 for x in xs], mt, 0.38, color=SERIES[1], label=f"born on the thin land (n={len(rows_thin):,})")
    ax.set_xticks(xs, ["hard", "muscle", "sensor", "gut"])
    ax.set_ylim(0)
    ax.yaxis.set_major_formatter(lambda y, _p: f"{y:.0%}")
    ax.yaxis.set_major_locator(MaxNLocator(4, steps=[1, 2, 5, 10]))
    legend_above(ax, 2)
    return figure(title, subtitle + f" Mean birth size {sr:.0f} against {stn:.0f} blocks.", to_svg(fig))


def data_table(cols, rows_by_name, every=1):
    out = []
    for name_, d in rows_by_name.items():
        cs = [c for c in cols if c in d]
        rows = "".join("<tr>" + "".join(f"<td>{d[c][i]:g}</td>" for c in cs) + "</tr>"
                       for i in range(0, len(d[cs[0]]), every))
        out.append(f"<details><summary>{html.escape(name_)}</summary><div class='tw'><table><thead><tr>"
                   + "".join(f"<th>{c}</th>" for c in cs) + f"</tr></thead><tbody>{rows}</tbody></table></div></details>")
    return "\n".join(out)


def modal_body(law, seed, lid):
    """The most common grown body of a lineage at its peak: (side, cells, peak row, rows)."""
    r = run(law, seed)
    by, bodies = lineage_rows(r), load_bodies(r)
    frames = list(read_frames(f"results/{r}_long.jsonl"))
    rows = by[lid]
    peak = max(rows, key=lambda x: int(x["size"]))
    frame = min((fr for fr in frames if any(a[4] == lid for a in fr["agents"])), key=lambda fr: abs(fr["step"] - int(peak["step"])))
    grown = 0.75 * sum(float(peak[k]) for k in KINDS)
    ids = [a[2] for a in frame["agents"] if a[4] == lid]
    c = Counter(i for i in ids if sum(ch != "0" for ch in bodies[i][1]) >= grown) or Counter(ids)
    side, cells = bodies[c.most_common(1)[0][0]]
    return side, cells, peak, rows


def gallery(picks, caption):
    cards = []
    for label, law, seed, lid, title, what in picks:
        side, cells, peak, rows = modal_body(law, seed, lid)
        span = int(rows[-1]["step"]) - int(rows[0]["step"]) + 5000
        u = 88 / side
        rects = "".join(f'<rect x="{(i % side) * u:.2f}" y="{(i // side) * u:.2f}" width="{u * 0.9:.2f}" '
                        f'height="{u * 0.9:.2f}" fill="{KIND_COLOR[int(k)]}"/>'
                        for i, k in enumerate(cells) if k != "0")
        m, pl = float(peak["meat"]), float(peak["plant"])
        meat = m / (m + pl) if m + pl > 0 else 0
        speed = float(peak["muscle"]) / max(float(peak["mass"]), 1e-9)
        cards.append(f"""<figure class="card"><svg viewBox="-1 -1 89 89" width="120" height="120" role="img" aria-label="{html.escape(title)}"><rect x="-1" y="-1" width="89" height="89" fill="var(--cell)"/>{rects}<line x1="-1" y1="-0.5" x2="88" y2="-0.5" stroke="var(--ink2)" stroke-width="1.5" stroke-dasharray="3 2"/></svg>
<figcaption><strong>{html.escape(title)}</strong><br>{html.escape(label)}, lineage {lid}: {span:,} steps, {int(peak["size"]):,} agents at its peak<br>grid {side}x{side}; mass {float(peak["mass"]):.0f}: hard {float(peak["hard"]):.0f}, muscle {float(peak["muscle"]):.0f}, sensor {float(peak["sensor"]):.1f}, gut {float(peak["digestive"]):.0f}; speed {speed:.2f}; flesh {meat:.0%} of the intake<br>{html.escape(what)}</figcaption></figure>""")
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


def diagram(st):
    """The mechanism: the same light laid in patches, how much of the world is rich, and what the crowd does with it."""
    keys = ["rich", "pop_rich", "plant_rich", "plant_thin", "travel", "blocked", "rarefied", "barren_share"]
    u = {k: arm(st, 0, k) for k in keys}
    i = {k: arm(st, 1, k) for k in keys}
    return f"""
<figure class="fig diagram">
<svg viewBox="0 0 880 330" width="100%" role="img" aria-label="The same light laid in nine Gaussian heaps concentrates it onto a third of the world, which breaks into islands, and the crowd gathers on them" font-size="12" fill="currentColor" stroke="currentColor">
  <defs>
    <marker id="a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0 L10 5 L0 10 z" fill="currentColor" stroke="none"/></marker>
    <marker id="b" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0 L10 5 L0 10 z" fill="var(--s1)" stroke="none"/></marker>
  </defs>
  <g stroke="none" font-weight="600">
    <text x="40" y="26">the light offered: {RATE * SUN * WIDTH * WIDTH:.1f} per step, the same in both worlds</text>
  </g>
  <g fill="none" stroke-width="1.6">
    <path d="M150 38 L150 82" marker-end="url(#a)"/>
    <path d="M296 138 L352 138" stroke="var(--s1)" marker-end="url(#b)"/>
    <path d="M616 138 L672 138" marker-end="url(#a)"/>
    <path d="M765 190 L765 258 L688 258" marker-end="url(#a)"/>
  </g>
  <g fill="none" stroke-opacity="0.45">
    <rect x="40" y="88" width="250" height="100" rx="6"/>
    <rect x="358" y="88" width="252" height="100" rx="6" stroke="var(--s1)"/>
    <rect x="678" y="88" width="174" height="100" rx="6"/>
    <rect x="200" y="222" width="480" height="76" rx="6"/>
  </g>
  <g stroke="none">
    <text x="54" y="112" font-weight="600">9 heaps of light, width {SIGMA}</text>
    <text x="54" y="134">one per {PATCH:,} cells, {math.sqrt(PATCH):.0f} cells apart</text>
    <text x="54" y="156">each centre wanders a cell</text>
    <text x="54" y="176">every 50 steps</text>
    <text x="372" y="112" font-weight="600" fill="var(--s1)">{i['rich']:.0%} of the world is rich</text>
    <text x="372" y="134" fill="var(--s1)">its peak grows {PATCH / (2 * math.pi * SIGMA * SIGMA):.1f}x a cell's old rate</text>
    <text x="372" y="156" fill="var(--s1)">3 islands on average, 42 cells across</text>
    <text x="372" y="176" fill="var(--s1)">{i['barren_share']:.0%} of the light lost for want of soil</text>
    <text x="692" y="112" font-weight="600">the crowd gathers</text>
    <text x="692" y="134">{i['pop_rich']:.0%} of the bodies</text>
    <text x="692" y="156">stand on them</text>
    <text x="692" y="176">plant {i['plant_rich']:.2f} against {i['plant_thin']:.2f}</text>
    <text x="216" y="248" font-weight="600">each island holds its own crowd</text>
    <text x="216" y="270">travel {u['travel']:.1f} &#8594; {i['travel']:.1f} cells a life, blocked {u['blocked']:.0%} &#8594; {i['blocked']:.0%}</text>
    <text x="216" y="290">kinds of body {u['rarefied']:.1f} &#8594; {i['rarefied']:.1f}, rarefied to {RAREFY} bodies</text>
    <text x="300" y="128">heaped</text>
    <text x="622" y="128">grazed</text>
  </g>
</svg>
<figcaption>Figure 1. Nothing is added to the world: the same light is laid down in nine Gaussian heaps instead of evenly, so a third of the cells carry nearly all of it. Because the heaps are narrow the rich land falls into islands rather than a web, and the crowd gathers on them without being told to. Numbers are means over the second half, the uniform thin world to the islands.</figcaption>
</figure>
"""


TEXT = {}


def fmt_opt(v, f):
    return "-" if v is None else f(v)


def numbers():
    """The measures over the second half, for the README."""
    st = all_stats()
    for law in LAWS:
        for s in SEEDS:
            x = st[law][s]
            if not x:
                print(f"{LAWS[law][0]:8s} seed {s}: missing")
                continue
            print(f"{LAWS[law][0]:8s} seed {s}: bodies {x['bodies']:.0f} floor {x['floor_txt']:>12s} "
                  f"travel {x['travel']:5.2f} blocked {x['blocked']:.0%} denied {x['denied']:.0%} "
                  f"kills/body {x['per_body']:.4f} share {x['share']:.0%} {'HUNTER' if x['hunter'] else 'grazer'} "
                  f"kinds {x['kinds']:3d} rar {fmt_opt(x['rarefied'], lambda v: f'{v:.1f}')} q1 {x['q1']:.2f} q2 {x['q2']:.2f} "
                  f"size {x['born_size']:.1f} regrow {x['regrowth']:.1f} barren {x['barren_share']:.1%}")
        print()
    for law in LAWS:
        print(f"{LAWS[law][0]}: " + ", ".join(
            f"{k} {arm(st, law, k):.4g}" for k in ["bodies", "floor", "travel", "blocked", "denied", "moved", "per_body",
                                                   "share", "kinds", "rarefied", "q1", "q2", "born_size", "regrowth",
                                                   "barren_share", "rich", "pop_rich", "age", "lineages",
                                                   "starve_rich", "starve_thin", "segregation"]))
    print("\nby the land a body was born on (islands arm):")
    for s in SEEDS:
        x = st[1][s]
        if not x:
            continue
        print(f"  seed {s}: rich n={x['n_rich']:4d} size {x['size_rich']:.1f} mix " + " ".join(f"{v:.2f}" for v in x['mix_rich'])
              + f" q1 {x['div_rich']['q1']:.2f} | thin n={x['n_thin']:4d} size {x['size_thin']:.1f} mix "
              + " ".join(f"{v:.2f}" for v in x['mix_thin']) + f" q1 {x['div_thin']['q1']:.2f}")
    print("\nthe rich land at the last frame (islands arm):")
    for s in SEEDS:
        if not exists(run(1, s)):
            continue
        _grow, rich = field_map(run(1, s))
        n, big, med = regions(rich)
        share = sum(sum(r) for r in rich) / (WIDTH * WIDTH)
        print(f"  seed {s}: rich {share:.1%}, {n} regions, largest {big:,} cells ({math.sqrt(big):.0f} across), median {med:,}")
    print("\ndiversity at each census (mean over seeds):")
    for law in LAWS:
        for key in ["kinds", "rarefied", "q1", "q2"]:
            ys = []
            for i, _c in enumerate(CENSUS):
                vals = [st[law][s]["div_at"][i][key] for s in SEEDS if st[law][s] and st[law][s]["div_at"][i][key] is not None]
                ys.append(sum(vals) / len(vals) if vals else float("nan"))
            print(f"  {LAWS[law][0]:8s} {key:9s} " + " ".join(f"{y:6.2f}" for y in ys))


def main():
    st = all_stats()
    logs = {f"{LAWS[law][0]}, seed {s}": load_csv(f"results/{run(law, s)}_log.csv") for law in LAWS for s in SEEDS if st[law][s]}
    seed0 = MAP_SEED if st[1].get(MAP_SEED) else next(s for s in SEEDS if st[1][s])
    grow, rich = field_map(run(1, seed0))
    n_reg, big, med = regions(rich)
    plant = plant_map(run(1, seed0))
    plant_flat = plant_map(run(0, seed0))

    charts_land = [
        map_chart(f"What the ground grows, seed {seed0}", f"The regrowth of every cell at step {STEPS:,}, rebuilt from the nine patch "
                  "centres. White ground grows almost nothing.", grow, max(max(r) for r in grow),
                  labels=["nothing", "10x the old rate"], slot=3),
        map_chart(f"The plant standing on it, seed {seed0}", "The same world, the plant actually standing. The crowd grazes the islands "
                  "down, so they show as rims rather than blocks.", plant, 8.0, labels=["bare", "a full cell"], slot=2),
    ]
    charts_div = [
        seed_chart("Kinds of body, by seed", f"Birth shapes, rarefied to {RAREFY} bodies so that worlds of different population compare. "
                   "The dotted line is the crowded world (sun 1, seed 9).", st, "rarefied",
                   hline=CROWDED_DIV["rarefied"], hlabel="crowded world", fmt=lambda y, _p: f"{y:.0f}"),
        census_chart("The effective number of common kinds, over the run",
                     "q1 = exp(Shannon) over birth shapes, mean of the seeds. Both worlds lose kinds as they settle.",
                     st, "q1"),
    ]
    charts_move = [
        seed_chart("How cut up the lineages are, by seed", "The chance two bodies of one island share a lineage, over the chance any "
                   "two bodies do. The uniform runs are cut by the same nine centres. 1.0 is a crowd mixed through the world.",
                   st, "segregation", hline=1.0, hlabel="mixed through the world", fmt=lambda y, _p: f"{y:.1f}"),
        travel_chart("How far a body has travelled, by age", "World cells from its birthplace, median of the bodies alive at the last "
                     "census. Lower is a body that stays where it was born."),
    ]
    charts_sort = [
        mix_chart("The body born on the rich land and the body born on the thin", "Mean share of each kind of block in the birth shape, "
                  "every island run together.", st),
    ]
    charts_world = [
        floor_chart("The bodies left at the end of each winter", "The lowest population of every season, in the worst seed of each "
                    "world. The dotted line is 50 bodies, the mark a world has to clear to be called standing."),
    ]

    def cell(s, key, f):
        return "<td>" + " / ".join(fmt_opt(st[law][s][key] if st[law][s] else None, f) for law in LAWS) + "</td>"

    seed_rows = "".join(
        f"<tr><td>{s}</td>"
        + "<td>" + " / ".join("hunter" if st[law][s]["hunter"] else "grazer" for law in LAWS if st[law][s]) + "</td>"
        + f"{cell(s, 'bodies', lambda v: f'{v:,.0f}')}{cell(s, 'floor_txt', str)}"
        f"{cell(s, 'travel', lambda v: f'{v:.2f}')}{cell(s, 'blocked', lambda v: f'{v:.0%}')}"
        f"{cell(s, 'kinds', lambda v: f'{v:.0f}')}{cell(s, 'rarefied', lambda v: f'{v:.1f}')}"
        f"{cell(s, 'q1', lambda v: f'{v:.1f}')}{cell(s, 'q2', lambda v: f'{v:.1f}')}"
        f"{cell(s, 'born_size', lambda v: f'{v:.0f}')}{cell(s, 'share', lambda v: f'{v:.0%}')}</tr>"
        for s in SEEDS if st[0][s] and st[1][s])
    tables = data_table(["step", "pop", "births", "deaths_energy", "cells_broken", "plant_intake", "meat_intake", "regrowth",
                         "barren", "rich", "plant_rich", "plant_thin", "pop_rich", "hunger_rich", "hunger_thin", "mean_res",
                         "blocked", "births_no_room", "moved", "mass_p50", "mass_p90", "muscle_mean", "digestive_mean",
                         "age_p50"], logs)
    TEXT.update(TEXTS)
    TEXT["gallery"] = gallery(GALLERY, GALLERY_CAPTION) if GALLERY else ""
    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>e059 Islands of food - Report</title>
<style>{CSS}</style>
</head>
<body>
<main>
<h1>e059: Islands of food</h1>
<p class="sub">Experiment report - 2026-09-13 - the same light laid in heaps, in the thin world, seeds 9-12 (#69). Answer: {TEXT["sub_answer"]}</p>

<section class="tldr">
<h2>TL;DR</h2>
<p>{TEXT["tldr"]}</p>
</section>

<h2>1. Question</h2>
<p>{TEXT["question"]}</p>
<ol>
  <li><strong>Diversity rises:</strong> more kinds of body than the thin uniform world's.</li>
  <li><strong>Bodies sort by place:</strong> the body born on the rich land differs from the one born on the thin.</li>
  <li><strong>Predation returns</strong> where the crowd gathers.</li>
  <li><strong>Travel stays high:</strong> a body still ends its life far from where it was born.</li>
  <li><strong>The world stands</strong> and the soil feeds the patches.</li>
</ol>

<h2>2. The world</h2>
<p>{TEXT["world"]}</p>
{diagram(st)}
<p><strong>Runs.</strong> {TEXT["runs"]}</p>
<ul class="measures">
  <li><strong>rich land</strong> - cells that grow at or above the thin world's own rate; the rest is thin.</li>
  <li><strong>kinds</strong> - birth shapes on a grid over size and block mix (#66), rarefied to {RAREFY} bodies.</li>
  <li><strong>q1, q2</strong> - the effective number of common and of abundant kinds.</li>
  <li><strong>travel</strong> - world cells between a body's birthplace and where it is now.</li>
  <li><strong>blocked</strong> - forward moves another body was in the way of.</li>
  <li><strong>state</strong> - hunter when more than 0.03 blocks are broken per body per step (e045).</li>
  <li><strong>barren</strong> - light lost because the cell's soil had nothing left.</li>
  <li><strong>floor</strong> - the lowest population of a season; the world stands while it holds.</li>
</ul>

<h2>3. Results</h2>
<p>Means over the second half (steps {STEPS // 2:,}-{STEPS:,}). Cells are the uniform thin world / the islands on the same seed.</p>
<div class="tw"><table>
<thead><tr><th>seed</th><th>state</th><th>bodies</th><th>lowest floor</th><th>travel</th><th>blocked</th><th>kinds</th><th>rarefied</th><th>q1</th><th>q2</th><th>born size</th><th>kills' share</th></tr></thead>
<tbody>{seed_rows}</tbody></table></div>
<ol class="verdicts">
{TEXT["verdicts"]}
</ol>

<h3>3.1 {TEXT["h_land"]}</h3>
<div class="grid2">
{"".join(charts_land)}
</div>
<p>{TEXT["p_land"]}</p>

<h3>3.2 {TEXT["h_div"]}</h3>
<div class="grid2">
{"".join(charts_div)}
</div>
<p>{TEXT["p_div"]}</p>

<h3>3.3 {TEXT["h_move"]}</h3>
<div class="grid2">
{"".join(charts_move)}
</div>
<p>{TEXT["p_move"]}</p>

<h3>3.4 {TEXT["h_sort"]}</h3>
<div class="grid2">
{"".join(charts_sort)}
</div>
<p>{TEXT["p_sort"]}</p>

<h3>3.5 {TEXT["h_world"]}</h3>
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
<p>Every log step ({LOG:,} steps) of the {len(logs)} runs. The full data are in <code>results/*.csv</code>. Build this report with <code>uv run python experiments/e059_places/report.py</code>.</p>
{tables}
</main>
</body>
</html>
"""
    with open(os.path.join(HERE, "report.html"), "w") as f:
        f.write(page)
    words = sum(len(re.sub(r"<[^>]+>", " ", html.unescape(v)).split()) for k, v in TEXT.items() if k != "gallery")
    print(f"wrote report.html ({os.path.getsize(os.path.join(HERE, 'report.html'))//1024} KB); TEXT {words} words")
    print(f"the rich land of seed {seed0}: {n_reg} regions, largest {big:,} cells ({math.sqrt(big):.0f} across), median {med:,}; "
          f"flat plant mean {sum(sum(r) for r in plant_flat) / (WIDTH * WIDTH):.2f}")


GALLERY = []
GALLERY_CAPTION = ""

TEXTS = {
    "sub_answer": ("not kept, but the first law here to move diversity - and it does it by cutting the crowd up, not by making it "
                   "travel."),
    "tldr": ("The same light, laid in nine heaps instead of evenly, gives a third of the world nearly all the food. The crowd piles "
             "onto it and stops walking: 9.8 cells a life becomes 2.9. Yet the effective number of common kinds rises from 5.5 to "
             "10.4, on five seeds of six. What rises with it is neither travel nor local adaptation: two bodies on one island share a "
             "lineage 2.2 times as often as any two, against 1.1 in the flat world. The price is a quarter of the world's food."),
    "question": ("e058 thinned the world so that a body must gather from more ground than it stands on. Bodies did walk, three to five "
                 "times further, and the jam cleared - but diversity fell fourfold, because much of it was made by the crowd. So the "
                 "thin world is the regime, not the law. The law is the grain of the food, laid coarse enough that a body cannot cover "
                 "it in a life."),
    "world": ("No new law. The world's regrowth has always been laid down as Gaussian heaps; here they are narrow enough to "
              "concentrate the light 4.5 times, which breaks the rich land into islands instead of the web e054 got. The total light "
              "is unchanged. Two measures are new: the land a body stands on, and the land it was born on."),
    "runs": ("Pilots on seed 9, 100,000 steps: three grains at one concentration showed the rich land is a web at any scale; three "
             "concentrations at one spacing found the setting that makes islands. The batch: islands and the thin uniform world, seeds "
             "9-14, 300,000 steps. Twelve runs, 90 minutes on the Mac."),
    "verdicts": ("<li><span class=\"verdict\">Yes</span> q1 rises 5.53 &#8594; 10.37, on five seeds of six; kinds rarefied to 120 "
                 "bodies 13.4 &#8594; 17.8, on four of six.</li>"
                 "<li><span class=\"verdict no\">No</span> The rich land and the thin grow the same body on four seeds of six, and "
                 "only 9% of bodies are born on the thin land at all.</li>"
                 "<li><span class=\"verdict no\">No</span> Kills per body fall on every seed, 0.0172 &#8594; 0.0093; the control's "
                 "one hunter world grazes here.</li>"
                 "<li><span class=\"verdict no\">No</span> Travel falls 9.75 &#8594; 2.94 cells a life, at every age.</li>"
                 "<li><span class=\"verdict partly\">Partly</span> No run died, but the worst winter floor is 27 against 72, and "
                 "8.5% of the light falls where the soil has nothing left.</li>"),
    "h_land": "A third of the world grows almost all of the food",
    "p_land": ("Where a heap falls, a cell grows up to ten times what it grew under the flat sun; between them the ground is nearly "
               "bare. What stands there is another matter: the crowd grazes the islands down to 1.67 of plant against 0.71 on the thin "
               "land, so the rich land is not a larder but a faster conveyor."),
    "h_div": "Twice the common kinds, and four times the spread between seeds",
    "p_div": ("The first law here to move the diversity number, and the first to make the outcome unreliable: the control's six seeds "
              "land between 11.7 and 15.6 rarefied kinds, the islands' between 6.4 and 28.9. Both worlds shed kinds as they settle, "
              "the islands keeping about 1.4 times the control's."),
    "h_move": "The crowd is cut into pieces, and it stops walking",
    "p_move": ("Two bodies on one island share a lineage 2.2 times as often as any two of that world; the flat runs, cut by the same "
               "nine centres, read 1.1 - no clustering at all. That is where the kinds come from, and it arrives with bodies that "
               "travel a third as far, because everything worth eating is under them."),
    "h_sort": "The rich land and the thin land grow the same body",
    "p_sort": ("A place that differs only in how much of one food it holds is not a second way of making a living. Where a difference "
               "does show, on two seeds of six, it is the same one: the body born on the thin land carries more muscle and less gut. "
               "Nine bodies in ten are born on the rich land, and their children there too."),
    "h_world": "The price is a quarter of the food and half the winter margin",
    "p_world": ("A heap stands on the same cells for thousands of steps and a cell grows only what its own soil holds, so 8.5% of the "
                "light falls where nothing is left to grow it. The world makes 15.5 of plant a step against 20.6, and the winters cut "
                "closer: 27 bodies left in the worst season against 72."),
    "discussion": ("<p>The experiment was designed around walking. e058 had made a world a body could cross, and the idea was to put a "
                   "place difference across it that was too big to be averaged away. The bodies answered by not crossing anything: the "
                   "food moved to a third of the world, and they moved onto it and stayed. Every measure of movement is down.</p>"
                   "<p>What went up was diversity, through a door we were not watching. Nine heaps of light make nine crowds, and a "
                   "lineage that wins one does not thereby win the others: a body's neighbours are twice as likely to be its relatives "
                   "as in the flat world. Kinds are made by keeping populations apart, and here the way to keep them apart was to "
                   "concentrate what they eat.</p>"
                   "<p>It is not cheap enough. The separation is paid for in food: the light lands on soil that cannot keep up, and a "
                   "quarter of the world's growth is gone. The next law should buy separation with something other than the harvest.</p>"),
    "conclusion": ("Not kept: the season world keeps its uniform sun. But the measure has moved for the first time, and it names what "
                   "to build next. Diversity here is bought neither by travel nor by bodies fitting a place, but by cutting the crowd "
                   "into pieces that keep different lines. Next: a separation that costs the world no food, and a second kind of place "
                   "rather than a second amount of the same one (#14)."),
}


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "numbers":
        numbers()
    elif len(sys.argv) > 1 and sys.argv[1] == "lineages":
        for law in LAWS:
            for s in SEEDS:
                r = run(law, s)
                if not exists(r):
                    continue
                by = lineage_rows(r)
                top = sorted(by, key=lambda lid: -sum(int(x["size"]) for x in by[lid]))[:5]
                print(f"{LAWS[law][0]}, seed {s}")
                for lid in top:
                    rows = by[lid]
                    peak = max(rows, key=lambda x: int(x["size"]))
                    side, cells, _, _ = modal_body(law, s, lid)
                    print(f"  lineage {lid}: {sum(int(x['size']) for x in rows):,} body-samples, "
                          f"{int(rows[0]['step']):,}-{int(rows[-1]['step']):,}, peak {peak['size']} at {int(peak['step']):,}; "
                          f"muscle {float(peak['muscle']):.0f} gut {float(peak['digestive']):.0f} hard {float(peak['hard']):.0f}; "
                          f"side {side} cells {cells}")
    else:
        main()
