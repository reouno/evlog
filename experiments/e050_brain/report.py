#!/usr/bin/env python3
"""Build report.html for this experiment.

Charts: matplotlib, exported as SVG and inlined. Diagram: hand-written SVG.
Run from the repo root: uv run python experiments/e050_brain/report.py
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
E048 = os.path.join(os.path.dirname(HERE), "e048_motor")  # the old brain's runs in e048's world
E049 = os.path.join(os.path.dirname(HERE), "e049_band")  # the old brain's runs under band + thirst
PILOT = os.path.join(HERE, "results", "pilot")
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
BAND = 25  # steps the band takes to cross a world cell, in the batch
SUB = 4  # sub-cells to a world cell
WIDTH = 128  # world cells across
BAND_W = WIDTH // 4  # the band's width in columns


def name(band=0, thirst="", seed=9, brain=False):
    """A run's file prefix: e048's world under the motor, with the band (steps a cell, 0: none), thirst and the brain."""
    return f"{BASE}{'_thirst' + thirst if thirst else ''}{TAIL}{'_band' + str(band) if band else ''}{'_brain' if brain else ''}_seed{seed}"


def run(law, seed):
    """law 0: the old brain in e048's world (e048's motor runs); 1: the brain there; 2: the old brain under band 25 and
    thirst 0.005 (e049's batch); 3: the brain there."""
    return name(BAND if law >= 2 else 0, "0.005" if law >= 2 else "", seed, law % 2 == 1)


def folder(law):
    return {0: E048, 2: E049}.get(law, HERE)


LAWS = {0: ("old brain, e048's world", 5), 1: ("brain, e048's world", 0), 2: ("old brain, band + thirst", 6), 3: ("brain, band + thirst", 1)}  # name, color slot
BRAIN = (1, 3)
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
        for i, x in enumerate(counts(os.path.join(folder(law), f"results/{run(law, s)}_dist.csv"), measure, STEPS // 2, STEPS)):
            tot[i] += x
    return shares(tot)


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
    hunger, thirst = half_mean(d, "deaths_energy") / LOG, half_mean(d, "deaths_thirst") / LOG
    died = int(d["step"][-1]) if d["pop"][-1] == 0 else None  # the step the world died at, if it did
    floor = 0 if died else min(x["pop"] for x in w)
    eyed = half_mean(d, "eyed") if "eyed" in d else half_mean(d, "sensor_agents_share")  # the old brain's logs: bodies with a sensor
    return dict(learners=half_mean(d, "learners"), eta=half_mean(d, "eta"), base=half_mean(d, "base_share"), beta=half_mean(d, "beta"),
                hidden=half_mean(d, "hidden"), eyed=eyed, learned=half_mean(d, "learned"), memory=half_mean(d, "memory"),
                units=half_mean(d, "units"), sat=half_mean(d, "sat"), wchange=half_mean(d, "wchange"), sense=half_mean(d, "sense_used"),bodies=bodies, floors=[x["pop"] for x in w], floor=floor, died=died, floor_txt=f"died at {died:,}" if died else f"{floor:,}",
                births=half_mean(d, "births") / LOG, age=half_mean(f, "age_mean"), lineages=half_mean(f, "lineages"),
                broken=broken, per_body=broken / bodies, hunter=broken / bodies >= STATE_LINE,
                plant=plant, hunted=hunted, scav=scav, share=hunted / (plant + hunted + scav), size=half_mean(d, "size_p50"),
                muscle=half_mean(d, "muscle_mean"), gut=half_mean(d, "digestive_mean"), speed=half_mean(d, "speed_mean"),
                moved=half_mean(d, "moved"), stalled=half_mean(d, "stalled"), west=half_mean(d, "west"), in_band=half_mean(d, "in_band"),
                drift=dr, rate=rate, hunger=hunger, thirst=thirst, thirst_share=thirst / max(hunger + thirst, 1e-9),
                fill=half_mean(d, "fill_mean"), drinking=half_mean(d, "drinking"), top=top_lineage(r, fo), div=div, wins=len(wins))


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
    legend_above(ax, len(laws) if len(laws) <= 3 else 2)
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
    for law in (1, 2):
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


# Hand-written mechanism diagram: the inputs (left), the hidden units that are the sensor blocks'
# tissue (middle, with their loop), the four outputs (right); the weights that learn (the direct way
# and the hidden units' way into the outputs) in the accent; the reward and the rule below.
_IN = ["food under, and ahead / behind / left / right (5)", "bodies ahead / behind / left / right (4)", "own energy (1)",
       "pools around, own thirst (5; under thirst)", "the body ahead: size, hardness (2, new)"]
_OUT = ["stay", "forward", "turn left", "turn right"]
_IN_Y = [44, 84, 124, 164, 204]
_OUT_Y = [74, 114, 154, 194]
_HID_Y = [72, 98, 124, 150, 176, 202]


def _diagram():
    s = []
    for y in _IN_Y:
        s.append(f'<line x1="302" y1="{y + 13}" x2="402" y2="137" stroke-opacity="0.35"/>')
    for y in _OUT_Y:
        s.append(f'<line x1="462" y1="137" x2="636" y2="{y + 13}" stroke="var(--s1)" stroke-width="1.6"/>')
    for y, t in zip(_IN_Y, _IN):
        s.append(f'<rect x="16" y="{y}" width="286" height="26" rx="5" fill="none" stroke-opacity="0.6"/>'
                 f'<text x="26" y="{y + 17}" stroke="none">{t}</text>')
    for y, t in zip(_OUT_Y, _OUT):
        s.append(f'<rect x="636" y="{y}" width="120" height="26" rx="5" fill="none" stroke-opacity="0.6"/>'
                 f'<text x="696" y="{y + 17}" stroke="none" text-anchor="middle">{t}</text>')
    for y in _HID_Y:
        s.append(f'<circle cx="432" cy="{y}" r="8" fill="currentColor" fill-opacity="0.55" stroke="none"/>')
    return "".join(s)


DIAGRAM = f"""
<figure class="fig diagram">
<svg viewBox="0 -18 880 348" width="100%" role="img" aria-label="The brain: the inputs go to the four outputs directly and through up to eight hidden units, one per sensor block, that carry their state to the next step; the weights into the outputs learn from the body's energy balance" font-size="12" fill="currentColor" stroke="currentColor">
  <defs><marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0 L10 5 L0 10 z" fill="var(--s1)" stroke="none"/></marker>
  <marker id="ai" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0 L10 5 L0 10 z" fill="currentColor" stroke="none"/></marker></defs>
  {_diagram()}
  <path d="M302,40 C400,4 560,4 636,66" fill="none" stroke="var(--s1)" stroke-width="2.4" marker-end="url(#ah)"/>
  <rect x="404" y="58" width="56" height="158" rx="14" fill="none" stroke-dasharray="4 3" stroke-opacity="0.7"/>
  <path d="M452,218 C470,250 394,250 412,220" fill="none" stroke-width="1.4" marker-end="url(#ai)"/>
  <g stroke="none">
    <text x="470" y="0" text-anchor="middle">direct: starts at the old reflex's weights, learns</text>
    <text x="432" y="50" text-anchor="middle">hidden units: 1 per sensor block (0-8)</text>
    <text x="432" y="262" text-anchor="middle">state kept to the next step (memory)</text>
    <text x="340" y="246" text-anchor="middle">fixed at birth</text>
    <text x="548" y="96" text-anchor="middle" fill="var(--s1)">learns</text>
    <text x="696" y="240" text-anchor="middle">the largest wins (no noise)</text>
    <text x="16" y="292">Reward of the interval: (taken in - paid) / (taken in + paid), -1 to 1; R = the reward less its running mean (kept at rate beta).</text>
    <text x="16" y="310">At each decision the weights into the output chosen last move by eta x (the value at their other end) x R, within -1 to 1.</text>
    <text x="16" y="328">eta (0 to 0.1) and beta (0 to 1) come from the genome, 0 for half of the random genomes; a child starts from its genome's weights.</text>
  </g>
</svg>
<figcaption>Figure 1. The brain under the law. A sensor block is nerve tissue: it sees one cell farther (e026), carries one hidden unit, and pays a block's upkeep (0.002 a step) and weight (0.5). Without the law the brain is the direct way alone, fixed at birth (e049).</figcaption>
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
            print(f"      hunger {x['hunger']:.2f} thirst {x['thirst']:.2f} ({x['thirst_share']:.0%}) fill {x['fill']:.2f} drinking {x['drinking']:.2f} "
                  f"| top {i} {share:.0%} {cells:.1f} cells {muscle:.1f} muscle {gut:.1f} gut {meat:.0%} flesh speed {speed:.2f} | diversity {x['div']} of {x['wins']}")
            pc = lambda v: f"{v:.1%}"
            print(f"      brain: learners {fmt_opt(x['learners'], pc)} eta {fmt_opt(x['eta'], f4)} base {fmt_opt(x['base'], pc)} beta {fmt_opt(x['beta'], lambda v: f'{v:.2f}')} "
                  f"eyed {fmt_opt(x['eyed'], pc)} hidden {fmt_opt(x['hidden'], lambda v: f'{v:.2f}')} learned {fmt_opt(x['learned'], pc)} memory {fmt_opt(x['memory'], pc)} "
                  f"units {fmt_opt(x['units'], pc)} sat {fmt_opt(x['sat'], lambda v: f'{v:.2f}')} wchange {fmt_opt(x['wchange'], f4)} sense {fmt_opt(x['sense'], pc)}")
    for law in LAWS:
        xs = [st[law][s] for s in SEEDS if st[law][s]]
        print(f"{LAWS[law][0]}: hunter worlds {sum(x['hunter'] for x in xs)} of {len(xs)}; bodies {sum(x['bodies'] for x in xs) / max(len(xs), 1):.0f}")


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


def main():
    st = all_stats()
    logs = {f"{LAWS[law][0]}, seed {s}": load_csv(f"results/{run(law, s)}_log.csv") for law in BRAIN for s in SEEDS if st[law][s]}
    small = lambda y, _p: f"{y:.3f}".rstrip("0").rstrip(".") if y else "0"

    charts_learn = [
        time_chart("Learners among the living", "Share of the bodies whose genome learns (a learning rate above 0), every 10,000 steps. "
                   "Half of the random genomes do: above the dotted line, learning was selected.", "learners", BRAIN, hline=0.5),
        seed_chart("Decisions that learning changed", "Share of the learners' decisions that differ with the weights they were born with, "
                   "second half (a knockout every 10 steps).", st, "learned", laws=BRAIN, percent=True),
    ]
    charts_memory = [
        seed_chart("Bodies with a sensor", "Share of the bodies with a sensor block, second half. Under the brain each sensor carries a hidden "
                   "unit; the grays are the old brain on the same seed.", st, "eyed", laws=(0, 1, 2, 3), percent=True),
        seed_chart("Decisions the memory changed", "Share of the decisions of bodies with hidden units that differ when the state carried "
                   "from the last step is set to 0, second half.", st, "memory", laws=BRAIN, percent=True),
    ]
    charts_walk = [
        seed_chart("Walking west under the band", "Sub-cells a body moves west by its own actions less east, per step, second half.",
                   st, "west", laws=(2, 3), fmt=small),
        seed_chart("Thirst's share of the deaths under the band", "Deaths by thirst among the deaths by hunger and thirst, second half.",
                   st, "thirst_share", laws=(2, 3), percent=True),
    ]
    charts_world = [
        seed_chart("Bodies, by seed", "Bodies alive over the second half (steps 50,000-100,000).", st, "bodies", laws=(0, 1, 2, 3)),
        seed_chart("The flesh of kills in what the bodies eat", "Second half: the seed and the law pick the world's state.",
                   st, "share", laws=(0, 1, 2, 3), percent=True, ymax=0.6),
    ]

    def cell(s, key, f, laws):
        return "<td>" + " / ".join(fmt_opt(st[law][s][key] if st[law][s] else None, f) for law in laws) + "</td>"

    pc = lambda v: f"{v:.0%}"
    seed_rows = ""
    for s in SEEDS:
        for wname, (old, new) in (("e048's world", (0, 1)), ("band + thirst", (2, 3))):
            if not (st[old][s] and st[new][s]):
                continue
            seed_rows += (f"<tr><td>{s}</td><td>{wname}</td>{cell(s, 'learners', pc, (new,))}{cell(s, 'learned', pc, (new,))}"
                          f"{cell(s, 'eyed', pc, (old, new))}{cell(s, 'memory', pc, (new,))}"
                          f"{cell(s, 'west', lambda v: f'{v:.3f}', (old, new)) if old == 2 else '<td>-</td>'}"
                          f"{cell(s, 'thirst_share', pc, (old, new)) if old == 2 else '<td>-</td>'}{cell(s, 'bodies', lambda v: f'{v:,.0f}', (old, new))}"
                          f"{cell(s, 'floor_txt', str, (old, new))}{cell(s, 'share', pc, (old, new))}{cell(s, 'div', str, (old, new))}</tr>")
    tables = data_table(["step", "pop", "births", "deaths_energy", "deaths_thirst", "learners", "eta", "base_share", "beta", "hidden", "eyed",
                         "learned", "memory", "units", "sat", "wchange", "west", "in_band", "speed_mean", "moved", "size_p50"], logs)
    TEXT.update(TEXTS)
    TEXT["gallery"] = gallery(GALLERY, GALLERY_CAPTION) if GALLERY else ""
    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>e050 A brain that remembers and learns - Report</title>
<style>{CSS}</style>
</head>
<body>
<main>
<h1>e050: A brain that remembers and learns</h1>
<p class="sub">Experiment report - 2026-09-11 - a small recurrent brain whose output weights learn from the body's energy balance (#53), in e048's world and under e049's band with thirst, seeds 9-12, against the old brain's runs. Answer: {TEXT["sub_answer"]}</p>

<section class="tldr">
<h2>TL;DR</h2>
<p>{TEXT["tldr"]}</p>
</section>

<h2>1. Question</h2>
<p>{TEXT["question"]}</p>
<ol>
  <li><strong>Learning is selected where the world changes within a life:</strong> learners above half of the bodies under band + thirst, and above e048's world's, on three seeds of four.</li>
  <li><strong>Memory is kept:</strong> more bodies with a sensor than the old brain on the same seed, under band + thirst, on three seeds of four.</li>
  <li><strong>The brain is used:</strong> learning and memory each change at least 5% of the decisions, in both worlds.</li>
  <li><strong>Bodies walk with the band:</strong> walking west twice the old brain's, and a smaller share of deaths by thirst, on three seeds of four.</li>
  <li><strong>The world stands:</strong> every winter floor above 50.</li>
</ol>

<h2>2. The law</h2>
<p>{TEXT["world"]}</p>
{DIAGRAM}
<p><strong>Runs.</strong> {TEXT["runs"]}</p>
<ul class="measures">
  <li><strong>learners</strong> - the share of the bodies whose genome learns (a learning rate above 0); half at the random start.</li>
  <li><strong>learned</strong> - the share of the learners' decisions that differ with the weights they were born with.</li>
  <li><strong>with a sensor</strong> - the share of the bodies with a sensor block; under the brain each carries a hidden unit.</li>
  <li><strong>memory</strong> - the share of the decisions of bodies with hidden units that differ when the carried state is set to 0.</li>
  <li><strong>walking west</strong> - sub-cells a body moves west by its own actions less east, per step.</li>
  <li><strong>thirst's share</strong> - deaths by thirst among the deaths by hunger and thirst.</li>
  <li><strong>state, diversity</strong> - the flesh of kills in what bodies eat; the diversity number (#42).</li>
</ul>

<h2>3. Results</h2>
<p>Means over the second half (steps 50,000-100,000). Pairs are the old brain / the brain on the same world and seed.</p>
<div class="tw"><table>
<thead><tr><th>seed</th><th>world</th><th>learners</th><th>learned</th><th>with a sensor</th><th>memory</th><th>walking west</th><th>thirst's share</th><th>bodies</th><th>lowest floor</th><th>kills' share</th><th>diversity</th></tr></thead>
<tbody>{seed_rows}</tbody></table></div>
<ol class="verdicts">
{TEXT["verdicts"]}
</ol>

<h3>3.1 {TEXT["h_learn"]}</h3>
<div class="grid2">
{"".join(charts_learn)}
</div>
<p>{TEXT["p_learn"]}</p>

<h3>3.2 {TEXT["h_memory"]}</h3>
<div class="grid2">
{"".join(charts_memory)}
</div>
<p>{TEXT["p_memory"]}</p>

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
<p>Every log step (10,000 steps) of the eight runs under the brain; the old brain's are in e048's and e049's reports, the check's and the two pilots' in <code>results/pilot/</code>. The full data are in <code>results/*.csv</code>. Build this report with <code>uv run python experiments/e050_brain/report.py</code>.</p>
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
    ("e048's world, seed 11", 1, 11, 735, "the learning runner", "Muscle in front, gut at the back: it learns (eta 0.05) and held 57% of the last third."),
    ("e048's world, seed 11", 1, 11, 666, "the sitter beside it", "A row of muscle before two rows of gut: it barely learns (eta 0.009), and held the other 43%."),
    ("e048's world, seed 12", 1, 12, 949, "the fastest learner", "Gut across the front, muscle behind: it learns at eta 0.09, near the top of the range, 42% of the last third."),
    ("e048's world, seed 12", 1, 12, 737, "the gut that does not learn", "Two rows of gut over a stub of muscle: no learning, and 41% of the last third, beside the learner."),
    ("e048's world, seed 9", 1, 9, 848, "the hard-fronted hunter", "A hard row in front, muscle around a gut core: seed 9's hunter; one body in nine learns."),
    ("band + thirst, seed 10", 3, 10, 303, "the muscle square", "Muscle with a gut at a back corner: 77% of the last third under the band, and it does not learn."),
]
GALLERY_CAPTION = ("The usual grown body of six leading lineages under the brain, front up (orange muscle, aqua gut, yellow sensor, blue hard). "
                   "In e048's world the fast muscle blocks learn and the gut sitters beside them do not.")

TEXTS = {
    "sub_answer": ("no, under the conditions of these runs. Learning changes a quarter to three fifths of a learner's decisions, but "
                   "it is not selected where the world changes: learners fall to 1-27% under band + thirst. Memory is hardly used, and "
                   "bodies do not walk with the band. Kept as an argument."),
    "tldr": ("Bodies got a brain: hidden units in the sensor blocks that carry a state between steps, and output weights that learn "
             "from the energy balance. Learning is used (26-62% of a learner's decisions change) but not selected where the world "
             "changes: learners fall to 1-27% under band + thirst. Memory changes under 5% of decisions; nobody walks with the band. "
             "That is this brain in this world, both of our making, not a verdict on brains. Next: #54, a place that worsens."),
    "verdicts": ("<li><span class=\"verdict no\">No</span> Learners end at 1-27% of the bodies under band + thirst on all four seeds, "
                 "below e048's world on three (there: 7-95%).</li>"
                 "<li><span class=\"verdict no\">No</span> Bodies with a sensor under band + thirst: 1-10%, above the old brain's only "
                 "on seed 12 (3% to 9%).</li>"
                 "<li><span class=\"verdict partly\">Partly</span> Learning changes 26-62% of the learners' decisions; the carried "
                 "state changes 0.6-5.2%, 5% or more on one run of eight.</li>"
                 "<li><span class=\"verdict no\">No</span> Walking west is 0.98-1.35 times the old brain's; thirst's share of the "
                 "deaths is lower on one seed of four.</li>"
                 "<li><span class=\"verdict no\">No</span> e048's world stands (floors 220-520); under band + thirst two winters fall "
                 "to 37 and 1 body, though none dies (e049: one died).</li>"),
    "h_learn": "Learning is used, but not selected where the world changes",
    "p_learn": ("Half of the random genomes learn. By step 10,000 learners are above half on six runs of eight (65-99%); after that "
                "their share follows the lineage that wins. Under band + thirst every winner stopped learning; in e048's world the "
                "winners of seeds 11 and 12 learn (eta 0.05-0.09). Where it runs, learning moves the weights far: a quarter to three "
                "fifths of the decisions differ from the birth weights."),
    "h_memory": "Memory is hardly used",
    "p_memory": ("A sensor costs a block's upkeep and carries one hidden unit. The brain keeps no more sensors than the old one (seed "
                 "10 of e048's world lost its crowd of eyes, 72% to 8%). Where units exist, setting the carried state to 0 changes "
                 "0.6-5% of the decisions, and removing the units 3-17%: the units work on the present inputs, not on the past."),
    "h_walk": "Bodies do not walk with the band",
    "p_walk": ("Walking west stays at 0.008-0.013 sub-cells a step, the old brain's 0.008-0.012, 5-8% of the band's speed, "
               "and deaths by thirst stay 22-29% of the deaths. The bodies aged 1,000 steps or more drift west at 0.022-0.034 cells a "
               "step, as under the old brain (0.020-0.028): the bodies that walk are still the few that live long."),
    "h_world": "The old brain's world, with more hunting in e048's world",
    "p_world": ("Bodies are about the old brain's in both worlds. In e048's world the two grazer seeds turn to hunting (kills 4% to "
                "26% and 10% to 27% of the intake) and their bodies are faster (speed 0.25-0.30 against 0.16). Under band + thirst "
                "the winters are as hard as e049's: floors of 37 and 1 body on two seeds."),
    "discussion": ("<p>Learning did what it was built to do: it rewrote a quarter to three fifths of the decisions of the bodies that "
                   "carry it. It did not make them win where the world changes. Under band + thirst every winning lineage lost it; in "
                   "e048's world it rides on the fast muscle blocks and not on the gut sitters beside them, on two seeds. The reward "
                   "is one step's energy balance, and here that says little: a sitter's food regrows under it, and the band's water "
                   "decides who dies of thirst, which the reward does not count.</p>"
                   "<p>Memory was not used. Even with the units' sums scaled, the units sit near their bounds (mean |state| 0.5-0.9), "
                   "set by the present inputs; the few bodies that carry them use them for the present, not for the past.</p>"
                   "<p>What this does not show: that a brain is not needed. The answer hangs on our choices: one step's energy balance "
                   "as the reward, learning only into the outputs, units that are the eye's tissue, raw inputs that saturate them, "
                   "four seeds of 100,000 steps. Nor whether learning pays where a place worsens under the body (#54), or whether "
                   "thirst in the reward would teach walking.</p>"),
    "conclusion": ("Not kept as the default; it stays as the argument brain (46). Under these conditions learning is used but not "
                   "selected, memory is not used, and bodies do not walk with the band. What a brain is worth depends on what the "
                   "world asks of it, so the world comes first. Next: #54, a place that gets worse the longer a body stays (e041's "
                   "stock first), with the brain on and off."),
}
TEXTS.update({
    "question": ("The brain was a reflex: ten inputs (five more under thirst) to four actions, fixed at birth, with no memory, no "
                 "learning, and no way to tell a predator from a neighbor. In e049 the crowd followed a moving rain by births; a body "
                 "that walks with it must remember or sense where the rain went. A brain pays only where the world changes within a "
                 "life, so it is tested under e049's band with thirst and in e048's world:"),
    "world": ("Each sensor block now carries a hidden unit that keeps its state from step to step. The weights into the four actions "
              "learn: after each step, the weights into the action just taken move by the learning rate times their input times the "
              "reward, the energy balance less its running mean. Half of the random genomes do not learn."),
    "runs": ("The brain in e048's world and under band 25 with thirst 0.005, seeds 9-12, 100,000 steps, eight runs at once, "
             "against the old brain's runs of e048 and e049. Before it, a check (without the law, e049 byte for byte) and two "
             "pilots on seed 9, which added the scaling of the hidden units' sums."),
})


if __name__ == "__main__":
    if len(os.sys.argv) > 1 and os.sys.argv[1] == "lineages":
        for law in BRAIN:
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
