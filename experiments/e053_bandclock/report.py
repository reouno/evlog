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
import re
from collections import Counter, defaultdict

import matplotlib
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator

matplotlib.use("svg")

HERE = os.path.dirname(os.path.abspath(__file__))
PILOT = os.path.join(HERE, "results", "pilot")
E052 = os.path.join(os.path.dirname(HERE), "e052_clock")  # the same laws without the band were run there
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
BAND = 50  # steps the band takes to cross a world cell, in the batch
SUB = 4  # sub-cells to a world cell
WIDTH = 128  # world cells across
BAND_W = WIDTH // 4  # the band's width in columns


def name(band=0, clock="", seed=9):
    """A run's file prefix: e048's world under the motor, with the band (steps a cell, 0: none) and the clock."""
    return f"{BASE}{TAIL}{'_band' + str(band) if band else ''}{'_clock' + clock if clock else ''}_seed{seed}"


def run(law, seed):
    """law 0: the band alone (e049's law at 50 steps a cell); 1: the band under the clock at 0.25; 2 and 3: e052's
    runs of the same seeds without the band, without and with the clock."""
    return name(BAND if law < 2 else 0, "0.25" if law in (1, 3) else "", seed)


def folder(law):
    return HERE if law < 2 else E052


LAWS = {0: ("band", 5), 1: ("band + clock", 0), 2: ("no band", 6), 3: ("no band + clock", 2)}  # name, color slot
PILOTS = [(100, "0.25", 2), (50, "0.25", 0), (100, "", 3)]  # band, clock, color slot
STEPS = 100_000
SEASON = 20_000
LOG = 10_000  # steps per log.csv row
SEEDS = [9, 10, 11, 12]
STATE_LINE = 0.03  # blocks broken per body per step: above it a hunter world (e045: 0.045-0.079, grazer 0.012-0.018)
GROWN = 1000  # a body this old or older is grown, for `drift`
QUARTER = SUB / BAND / 4  # a quarter of the band's speed, in sub-cells a step (hypothesis): 0.04

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


def drift(run, folder=HERE):
    """(median drift in world cells west, median drift over age in cells a step) of the bodies aged GROWN or more at
    step 100,000; (None, None) where the run did not record drift (the control)."""
    rows = [r for r in agents_rows(run, folder) if "drift" in r and int(r["age"]) >= GROWN]
    if not rows:
        return None, None
    return median(float(r["drift"]) for r in rows), median(float(r["drift"]) / int(r["age"]) for r in rows)


AGE_BINS = [(0, 100), (100, 500), (500, 1000), (1000, 2000), (2000, 10**9)]
AGE_NAMES = ["0-99", "100-499", "500-999", "1,000-1,999", "2,000+"]
AGE_MID = [50, 300, 750, 1500, 2500]


def drift_by_age(law, least=5):
    """Per age bin, (the median drift in world cells west, how many bodies) of the bodies alive at step 100,000, all
    seeds together; the median is nan where fewer than `least` bodies are that old."""
    rows = [r for s in SEEDS for r in agents_rows(run(law, s), folder(law))]
    out = []
    for lo, hi in AGE_BINS:
        xs = [float(r["drift"]) for r in rows if lo <= int(r["age"]) < hi]
        out.append((median(xs) if len(xs) >= least else float("nan"), len(xs)))
    return out


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


def counts(path, measure, lo, hi):
    """dist.csv's `measure` summed over the log rows lo < step <= hi, by the columns behind the band's front."""
    tot = [0.0] * WIDTH
    if os.path.exists(path):
        with open(path) as f:
            for r in csv.DictReader(f):
                if r["measure"] == measure and lo < int(r["step"]) <= hi:
                    tot[int(r["value"])] += float(r["count"])
    return tot


def shares(xs):
    s = sum(xs) or 1.0
    return [x / s for x in xs]


def batch_profile(law, measure):
    """A profile over the second half, the seeds' counts added."""
    tot = [0.0] * WIDTH
    for s in SEEDS:
        for i, x in enumerate(counts(os.path.join(HERE, f"results/{run(law, s)}_dist.csv"), measure, STEPS // 2, STEPS)):
            tot[i] += x
    return shares(tot)


def pilot_profile(band, clock, measure):
    """A pilot's profile over its 20,000 steps (seed 9)."""
    return shares(counts(os.path.join(PILOT, f"{name(band, clock, 9)}_dist.csv"), measure, 0, 20_000))


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
    dr, rate = drift(r, fo)
    li = lives(r, fo)
    hunger, thirst = half_mean(d, "deaths_energy") / LOG, half_mean(d, "deaths_thirst") / LOG
    died = int(d["step"][-1]) if d["pop"][-1] == 0 else None  # the step the world died at, if it did
    floor = 0 if died else min(x["pop"] for x in w)
    return dict(bodies=bodies, floors=[x["pop"] for x in w], floor=floor, died=died, floor_txt=f"died at {died:,}" if died else f"{floor:,}",
                births=half_mean(d, "births") / LOG, age=half_mean(f, "age_mean"), lineages=half_mean(f, "lineages"),
                broken=broken, per_body=broken / bodies, hunter=broken / bodies >= STATE_LINE,
                plant=plant, hunted=hunted, scav=scav, share=hunted / (plant + hunted + scav), size=half_mean(d, "size_p50"),
                muscle=half_mean(d, "muscle_mean"), gut=half_mean(d, "digestive_mean"), speed=half_mean(d, "speed_mean"),
                moved=half_mean(d, "moved"), stalled=half_mean(d, "stalled"), west=half_mean(d, "west"), in_band=half_mean(d, "in_band"),
                drift=dr, rate=rate, hunger=hunger, thirst=thirst, thirst_share=thirst / max(hunger + thirst, 1e-9),
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


def seed_chart(title, subtitle, st, key, laws=(0, 1, 2), percent=False, ymax=None, hline=None, fmt=None):
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


def profile_chart(title, subtitle, lines, ymax=None):
    """lines: [(label, color slot, shares by the columns behind the band's front)]; the band's columns shaded."""
    fig, ax = new_axes("columns behind the band's front (world cells)")
    ax.axvspan(0, BAND_W, color=INK, alpha=0.12, linewidth=0)
    ax.text(BAND_W / 2, 0.97, "under the band", transform=ax.get_xaxis_transform(), ha="center", va="top", color=INK, fontsize=8)
    for label, slot, ys in lines:
        ax.plot(range(WIDTH), [y * 100 for y in ys], color=SERIES[slot], linewidth=1.6, label=label)
    ax.axhline(100 / WIDTH, color=INK, linewidth=1, linestyle=":")
    ax.set_xlim(0, WIDTH - 1)
    ax.set_ylim(0, ymax or 1.3 * max(max(ys) for _l, _s, ys in lines) * 100)  # room above the peaks for the label
    ax.yaxis.set_major_formatter(lambda y, _p: f"{y:.1f}%")
    ax.yaxis.set_major_locator(MaxNLocator(4, steps=[1, 2, 5, 10]))
    legend_above(ax, len(lines))
    return figure(title, subtitle, to_svg(fig))


def drift_chart(title, subtitle):
    """The median drift of the bodies by age, both band conditions, against a quarter of the band's way."""
    fig, ax = new_axes("age at step 100,000 (steps)")
    for law in (0, 1):
        ys = [m for m, _n in drift_by_age(law)]
        ax.plot(range(len(AGE_BINS)), ys, color=SERIES[LAWS[law][1]], marker="o", markersize=6, linewidth=1.6, label=LAWS[law][0])
    ax.plot(range(len(AGE_BINS)), [m * QUARTER / SUB for m in AGE_MID], color=INK, linestyle=":", linewidth=1.2, label="a quarter of the band's way")
    ax.axhline(0, color=INK, linewidth=0.8)
    ax.set_xticks(range(len(AGE_BINS)), AGE_NAMES)
    ax.margins(x=0.05)
    ax.yaxis.set_major_locator(MaxNLocator(4, steps=[1, 2, 5, 10]))
    legend_above(ax, 3)
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


# Hand-written mechanism diagram: the world's 128 columns as one strip (6.25 px a column, west on the
# left), the band of 32 columns (the accent), and below it the water of a cell along the strip: about
# 4 WET under the band, evaporating behind it with a time constant of 100 steps (4 columns at 25 steps
# a column), below WET (a plant slows) about 140 steps after the band has passed.
_X0, _X1, _FRONT, _BACK, _BASE, _UNIT = 40, 840, 260, 460, 215, 15.0


def _water_path():
    pts = []
    for x in range(_X0, _X1 + 1, 4):
        if x < _FRONT:
            level = 0.0
        elif x <= _BACK:
            level = 4.0 * (1 - math.exp(-(x - _FRONT) / 3))
        else:
            level = 4.0 * math.exp(-(x - _BACK) / 12.5)
        pts.append(f"{x},{_BASE - _UNIT * level:.1f}")
    return "M" + " L".join(pts)


_RAIN = "".join(f'<line x1="{x}" y1="54" x2="{x - 4}" y2="72"/>' for x in range(276, 456, 14))

DIAGRAM = f"""
<figure class="fig diagram">
<svg viewBox="0 0 880 266" width="100%" role="img" aria-label="The band of rain: a quarter of the world's columns gets all the sky's rain and moves west one column every 50 steps; under it the water stands at about 4 WET, behind it the water evaporates and falls below WET, where a plant slows, about 140 steps after the band has passed" font-size="12" fill="currentColor" stroke="currentColor">
  <defs><marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0 L10 5 L0 10 z" fill="var(--s1)" stroke="none"/></marker></defs>
  <g stroke="none">
    <text x="{_X0}" y="22" font-weight="600">west</text>
    <text x="{_X1}" y="22" font-weight="600" text-anchor="end">east</text>
    <text x="470" y="44">moves west, a column every 50 steps</text>
  </g>
  <line x1="450" y1="40" x2="266" y2="40" stroke="var(--s1)" stroke-width="1.8" marker-end="url(#ah)"/>
  <g stroke="var(--s1)" stroke-width="1.5">{_RAIN}</g>
  <rect x="{_X0}" y="82" width="{_X1 - _X0}" height="34" fill="currentColor" fill-opacity="0.07" stroke="none"/>
  <rect x="{_FRONT}" y="82" width="{_BACK - _FRONT}" height="34" fill="var(--s1)" fill-opacity="0.28" stroke="none"/>
  <g stroke="none">
    <text x="50" y="104">dry: rained on next</text>
    <text x="272" y="104">all the rain, 4 a cell</text>
    <text x="472" y="104">left behind: drying</text>
    <text x="{_X0}" y="146">water in a cell</text>
    <text x="272" y="142">about 4 WET under the band</text>
    <text x="500" y="170">evaporates 1% a step: below WET ~140 steps after</text>
    <text x="{_X1}" y="190" text-anchor="end">WET: a plant grows at full light above this</text>
    <text x="{_X0}" y="242">A body lives 175-275 steps (the median at death), while the band moves 4-6 columns.</text>
    <text x="{_X0}" y="259">The clock: a body of mass m takes (16 / m)^0.25 turns a step (0.78-0.86 here); between turns nothing happens to it.</text>
  </g>
  <line x1="{_X0}" y1="{_BASE}" x2="{_X1}" y2="{_BASE}" stroke-opacity="0.35"/>
  <line x1="{_X0}" y1="{_BASE - _UNIT}" x2="{_X1}" y2="{_BASE - _UNIT}" stroke-opacity="0.6" stroke-dasharray="4 3"/>
  <path d="{_water_path()}" fill="none" stroke-width="1.8"/>
</svg>
<figcaption>Figure 1. The two laws run together: the band of rain (a quarter of the world, a column every 50 steps; the world gets as much water as before, on the band alone) and the clock (a body's own time scaling with its mass, so eating, upkeep, wear and breeding all wait for its turn).</figcaption>
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
            f4 = lambda v: f"{v:.4f}"
            print(f"seed {s} {LAWS[law][0]:15s} {'HUNTER' if x['hunter'] else 'grazer'} {x['floor_txt']} broken/body {x['per_body']:.4f} kills {x['share']:.1%} "
                  f"| bodies {x['bodies']:.0f} floors {x['floors']} births {x['births']:.2f} age {x['age']:.0f} lineages {x['lineages']:.1f} size p50 {x['size']:.1f}")
            print(f"      west {fmt_opt(x['west'], f4)} in_band {fmt_opt(x['in_band'], f4)} drift {fmt_opt(x['drift'], lambda v: f'{v:.1f}')} "
                  f"rate {fmt_opt(x['rate'], f4)} | moved {x['moved']:.4f} stalled {x['stalled']:.2f} speed {x['speed']:.3f} muscle {x['muscle']:.2f} gut {x['gut']:.2f}")
            print(f"      pace {x['pace']:.3f} turned {x['turned']:.3f} age p50/p90 {x['age_p50']:.0f}/{x['age_p90']:.0f} life p50 {fmt_opt(x['life'], str)} "
                  f"light {fmt_opt(x['life_light'], str)} heavy {fmt_opt(x['life_heavy'], str)} ratio {fmt_opt(x['life_ratio'], lambda v: f'{v:.2f}')} "
                  f"mass p50/p90 {x['mass']:.1f}/{x['mass_p90']:.1f} intake/gut {x['intake']:.4f}")
            print(f"      hunger {x['hunger']:.2f} | top {i} {share:.0%} {cells:.1f} cells {muscle:.1f} muscle {gut:.1f} gut {meat:.0%} flesh "
                  f"speed {speed:.2f} | diversity {x['div']} of {x['wins']}")
    for law in LAWS:
        xs = [st[law][s] for s in SEEDS if st[law][s]]
        print(f"{LAWS[law][0]}: hunter worlds {sum(x['hunter'] for x in xs)} of {len(xs)}; bodies {sum(x['bodies'] for x in xs) / max(len(xs), 1):.0f}")


def main():
    st = all_stats()
    logs = {f"{LAWS[law][0]}, seed {s}": load_csv(f"results/{run(law, s)}_log.csv") for law in (0, 1) for s in SEEDS if st[law][s]}
    small = lambda y, _p: f"{y:.3f}".rstrip("0").rstrip(".") if y else "0"

    charts_walk = [
        seed_chart("Walking west, by seed", "Sub-cells a body moves west by its own actions less east, per step, second half. The dotted line is "
                   "a quarter of the band's speed.", st, "west", laws=(0, 1), hline=QUARTER, fmt=small),
        drift_chart("How far west of its birthplace a body stands", "Median drift in world cells of the bodies alive at step 100,000, by age, "
                    "four seeds together. Walking with the band would be four times the dotted line."),
    ]
    charts_life = [
        seed_chart("The mean age of the living, by seed", "Second half. The two right-hand dots are e052's runs of the same seeds without the "
                   "band: there the clock doubled to quadrupled the age.", st, "age", laws=(0, 1, 2, 3)),
        seed_chart("What a gut takes, by seed", "Matter per gut block per step, second half: how well the world feeds a body.",
                   st, "intake", laws=(0, 1), fmt=lambda y, _p: f"{y:.4f}"),
    ]
    charts_world = [
        profile_chart("Where the bodies stand", "Share of the body-steps by the columns behind the band's front, second half, four seeds "
                      "together. The dotted line is a crowd spread evenly.",
                      [(LAWS[law][0], LAWS[law][1], batch_profile(law, "band_bodies")) for law in (0, 1)]),
        seed_chart("Bodies, by seed", "Bodies alive over the second half (steps 50,000-100,000).", st, "bodies", laws=(0, 1)),
        seed_chart("The flesh of kills in what the bodies eat, by seed", "Second half: under the band the clock turns three worlds of four "
                   "to hunting.", st, "share", laws=(0, 1), percent=True, ymax=0.45),
    ]

    def pair(s, key, f, laws=(0, 1)):
        return "<td>" + " / ".join(fmt_opt(st[law][s][key] if st[law][s] else None, f) for law in laws) + "</td>"

    seed_rows = "".join(
        f"<tr><td>{s}</td>{pair(s, 'west', lambda v: f'{v:.4f}')}{pair(s, 'in_band', lambda v: f'{v:.0%}')}"
        f"{pair(s, 'rate', lambda v: f'{v:.4f}')}{pair(s, 'age', lambda v: f'{v:,.0f}')}{pair(s, 'intake', lambda v: f'{v:.4f}')}"
        f"{pair(s, 'bodies', lambda v: f'{v:,.0f}')}{pair(s, 'floor_txt', str)}{pair(s, 'share', lambda v: f'{v:.0%}')}"
        f"{pair(s, 'div', lambda v: f'{v}')}</tr>"
        for s in SEEDS if all(st[law][s] for law in (0, 1)))
    tables = data_table(["step", "pop", "births", "deaths_energy", "deaths_wear", "cells_broken", "plant_intake", "meat_intake",
                         "muscle_mean", "speed_mean", "moved", "stalled", "west", "in_band", "pace", "age_p50", "size_p50"], logs)
    TEXT.update(TEXTS)
    TEXT["gallery"] = gallery(GALLERY, GALLERY_CAPTION) if GALLERY else ""
    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>e053 The band under the clock - Report</title>
<style>{CSS}</style>
</head>
<body>
<main>
<h1>e053: The band under the clock</h1>
<p class="sub">Experiment report - 2026-09-12 - e049's moving rain run under e052's clock, seeds 9-12 (#59). Answer: {TEXT["sub_answer"]}</p>

<section class="tldr">
<h2>TL;DR</h2>
<p>{TEXT["tldr"]}</p>
</section>

<h2>1. Question</h2>
<p>{TEXT["question"]}</p>
<ol>
  <li><strong>The body walks, not only the lineage:</strong> walking west at a quarter of the band's speed or more, and above the control's, on three seeds of four.</li>
  <li><strong>The long-lived are the crowd now:</strong> the bodies aged 1,000 steps or more drift west at half the band's speed, and there are many of them.</li>
  <li><strong>The world stands:</strong> every winter floor above 50.</li>
  <li><strong>The brain pays where a life is long:</strong> learners a larger share than without the clock (run only if (1) or (2) holds).</li>
</ol>

<h2>2. The world</h2>
<p>{TEXT["world"]}</p>
{DIAGRAM}
<p><strong>Runs.</strong> {TEXT["runs"]}</p>
<ul class="measures">
  <li><strong>walking west</strong> - sub-cells a body moves west by its own actions less east, per step; the band moves 0.08.</li>
  <li><strong>under the band</strong> - the share of the body-steps on the band's columns (a quarter of the world).</li>
  <li><strong>drift rate</strong> - how far west of its birthplace a body aged 1,000 steps or more stands, over its age (median), in cells a step; the band moves 0.02.</li>
  <li><strong>mean age</strong> - the age of the living, in world steps.</li>
  <li><strong>intake per gut</strong> - matter a gut block takes per step.</li>
  <li><strong>kills' share, diversity</strong> - the flesh of kills in what bodies eat; the diversity number (#42).</li>
</ul>

<h2>3. Results</h2>
<p>Means over the second half (steps 50,000-100,000). Pairs are the band alone / the band under the clock, on the same seed.</p>
<div class="tw"><table>
<thead><tr><th>seed</th><th>walking west</th><th>under the band</th><th>drift rate</th><th>mean age</th><th>intake per gut</th><th>bodies</th><th>lowest floor</th><th>kills' share</th><th>diversity</th></tr></thead>
<tbody>{seed_rows}</tbody></table></div>
<ol class="verdicts">
{TEXT["verdicts"]}
</ol>

<h3>3.1 {TEXT["h_walk"]}</h3>
<div class="grid2">
{"".join(charts_walk)}
</div>
<p>{TEXT["p_walk"]}</p>

<h3>3.2 {TEXT["h_life"]}</h3>
<div class="grid2">
{"".join(charts_life)}
</div>
<p>{TEXT["p_life"]}</p>

<h3>3.3 {TEXT["h_world"]}</h3>
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
<p>Every log step (10,000 steps) of the eight runs; the pilots are in <code>results/pilot/</code> and the runs without the band in e052's folder. The full data are in <code>results/*.csv</code>. Build this report with <code>uv run python experiments/e053_bandclock/report.py</code>.</p>
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
    ("band, seed 9", 0, 9, 597, "the four by four", "Two rows of gut behind two of muscle: the shape that won three of the four control worlds."),
    ("band, seed 10", 0, 10, 377, "the gut", "Seven by seven, 21 blocks of gut and 7 of muscle: the biggest winner here, and the slowest (speed 0.19)."),
    ("band, seed 11", 0, 11, 260, "the same body again", "Sixteen blocks, half muscle, half gut, no armor: it held seed 11 for 40,000 steps."),
    ("band + clock, seed 9", 1, 9, 541, "the heavy grazer", "Five by five, 13 gut to 10 muscle: under the clock the winners are half again as heavy (mass 50 against 34)."),
    ("band + clock, seed 11", 1, 11, 310, "the runner", "Ten muscle to five gut, speed 0.32: the fastest winner, in a world the clock turned to hunting."),
    ("band + clock, seed 12", 1, 12, 744, "muscle at the corners", "Muscle on the front corners and the middle gut: 36% of the last third at speed 0.29."),
]
GALLERY_CAPTION = ("The usual grown body of six leading lineages, front up (orange muscle, aqua gut, yellow sensor, blue hard). No winner "
                   "carries armor; under the clock they are bigger, and the fastest ones live where the world hunts.")

TEXTS = {
    "sub_answer": ("no. Under the band the clock buys no long lives, so no body outlives the rain's going, and walking west reaches "
                   "3-5% of the band's speed. Not kept."),
    "tldr": ("e049's moving rain is followed by births, not by walking, because a body lives about 200 steps. e052's clock made lives "
             "two to four times longer, so here the two run together: the band at 50 steps a column, with and without the clock, seeds "
             "9-12. Under the band the clock lengthens no lives at all - the deaths are hunger, and a body that takes 0.8 of a turn "
             "eats 0.8 as much. Not kept. Next: a band over a richer world."),
    "question": ("e049 moved the rain across the world and the crowd followed it by being born under it: a body lives about 200 steps, "
                 "and the band stands over a cell for 1,600. e052's clock, which scales a body's own time with its mass, raised the "
                 "mean age of the living from 278-739 to 874-1,432 in a world without the band. Walking should pay when the food moves "
                 "(A) and the body outlives the change (B). This runs A and B together for the first time:"),
    "world": ("No new law: two arguments of the same code are turned on together. The sky's rain falls on a north-south band a quarter "
              "of the world wide that moves west a column every 50 steps, and a body of mass m takes (16 / m)^0.25 turns a world step - "
              "0.78-0.86 for the bodies of this world. Everything a body does waits for its turn."),
    "runs": ("Pilots on seed 9, 20,000 steps: the band at 100 and 50 steps a column under the clock, and at 100 without it. The batch: "
             "band 50 with and without the clock, seeds 9-12, 100,000 steps, eight at once on the Mac, 20 minutes. The runs without the "
             "band in the age chart are e052's, on the same seeds."),
    "verdicts": ("<li><span class=\"verdict no\">No</span> Walking west is above the control's on all four seeds, but reaches 3-5% of "
                 "the band's speed where a quarter was asked; the oldest bodies drift less than the control's, not more.</li>"
                 "<li><span class=\"verdict no\">No</span> The clock lengthens no lives here: the mean age of the living is 380-818 "
                 "against 368-683, where without the band the same law reached 874-1,432.</li>"
                 "<li><span class=\"verdict yes\">Yes</span> Winter floors 91-179 and no run died, against 16-122 and one world of "
                 "eight dead under e049's band alone.</li>"
                 "<li><span class=\"verdict no\">Not run</span> The brain needs a life long enough to use what it learns. This world "
                 "has none, so the question cannot be asked in it.</li>"),
    "h_walk": "The crowd does not walk after the rain, clock or no clock",
    "p_walk": ("Walking west is above the control's on every seed, and that is the whole of the effect: 0.0025-0.0042 sub-cells a step "
               "against 0.0019-0.0025, where the band moves 0.08. The bodies that live longest are the ones that could walk, and under "
               "the clock they stand nearer their birthplace than the control's (2.8 cells against 3.8 at 1,000-1,999 steps of age). "
               "The crowd also falls further behind the band, because it moves less."),
    "h_life": "The clock buys no long lives where the deaths are hunger",
    "p_life": ("This is the finding. Without the band the same law doubled to quadrupled the mean age of the living and wear killed for "
               "the first time; under the band nothing moves, and no body dies of wear. What kills is hunger, 2.0-3.1 deaths a log "
               "interval, and the clock makes it worse: the intake per gut falls by 20-30%, because a body eats on its turns and the "
               "ground under the crowd is already thin."),
    "h_world": "A world that stands, packed into the band, and hunting",
    "p_world": ("The pair stands better than the band alone: no run died, where e049's faster band fell to 16 bodies and killed one "
                "world of eight. Half the crowd's body-steps are spent on the quarter of the land under the rain, and there the clock "
                "makes it hunt - three hunter worlds of four against two, the opposite of what the clock did without the band, where "
                "it ended hunting on all four seeds."),
    "discussion": ("<p>A long life turned out to belong to a rich world, not to the law we wrote. The clock only lets a body spread its "
                   "eating and its paying over more steps; what it lives to depends on what else kills it. Where food renews everywhere, "
                   "the slowed body is fed and grows old enough to wear out. Where the rain stands on a quarter of the land and the crowd "
                   "is packed under it, the same body starves as young as before.</p>"
                   "<p>So the two conditions we wanted work against each other. The moving food (A) is what keeps this world poor, and a "
                   "poor world does not grow the long lives (B) that would let a body follow the food itself. A world with both has to be "
                   "gentler than this one: a wider band, or more sun.</p>"
                   "<p>What this does not show: whether a richer world under a moving band grows long lives; why the band and the clock "
                   "together raise hunting (the crowd is denser and the bodies bigger, but contact was not measured); what a brain would "
                   "do where lives are long.</p>"),
    "conclusion": ("Not kept: nothing was added, and the combination does not make bodies walk. The finding is about conditions rather "
                   "than laws - before a law can rest on \"bodies live long\", the world has to be one where they do. Next for #59: the "
                   "band over a richer world (more sun, or a band over half the land), and one pilot to ask whether lives lengthen there "
                   "at all; only then is walking worth asking again."),
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
