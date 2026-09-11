#!/usr/bin/env python3
"""Build report.html for this experiment.

Charts: matplotlib, exported as SVG and inlined. Diagram: hand-written SVG.
Run from the repo root: uv run python experiments/e052_clock/report.py
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

BASE = "128_sigma0_r64_f0_flat_eyes8_flesh1_w1_season2_digest0_sidegrow_store5_yolk0_breed0_winterhigh_water0.1_leach0.01_depth0.01_mix0.2"
TAIL = "_strict_sat_hold_wear3000_corner_motor"
TAGS = {0: "", 1: "_clock0.25", 2: "_pace0.84"}  # what each law adds to a run's file name


def name(tag="", seed=9):
    """A run's file prefix: e048's world plus the law's tag."""
    return f"{BASE}{TAIL}{tag}_seed{seed}"


def run(law, seed):
    """law 0: no clock (e048's world, run again here for the new measures); 1: the clock at 0.25;
    2: the control for the slowdown alone, every body at 0.84 turns a step whatever it weighs."""
    return name(TAGS[law], seed)


def folder(law):
    return HERE


LAWS = {0: ("no clock", 5), 1: ("clock 0.25", 0), 2: ("flat pace 0.84", 1)}  # name, color slot
STEPS = 100_000
SEASON = 20_000
LOG = 10_000  # steps per log.csv row
SEEDS = [9, 10, 11, 12]
STATE_LINE = 0.03  # blocks broken per body per step: above it a hunter world (e045: 0.045-0.079, grazer 0.012-0.018)
GROWN = 1000  # a body this old or older is grown, for `travel`
LIGHT, HEAVY = 24, 48  # a body born under LIGHT of mass is light, one at HEAVY or more is heavy
CLOCK_MASS = 16  # the mass whose clock is the world's step (main.rs)

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


def lives(run, folder=HERE, lo=STEPS // 2):
    """From deaths.csv over the second half: how long a body lives, in world steps, by the mass it was born with.
    Returns the median life of the bodies born light (under LIGHT), heavy (HEAVY or more) and of all of them, the
    share of the deaths that are heavy, and the median life per mass bin of 8 (bins holding 2% of the deaths or more).
    `age` is a bin of 50 steps: its middle stands for it."""
    rows = [r for r in load_rows(f"results/{run}_deaths.csv", folder) if int(r["step"]) > lo]
    total = sum(int(r["n"]) for r in rows) or 1

    def median(sel):
        pairs = sorted((int(r["age"]) + 25, int(r["n"])) for r in rows if sel(float(r["mass"])))
        n = sum(p[1] for p in pairs)
        if n == 0:
            return None
        c = 0
        for age, k in pairs:
            c += k
            if c >= n / 2:
                return age
    by = {}
    for b in range(0, 129, 8):
        share = sum(int(r["n"]) for r in rows if b <= float(r["mass"]) < b + 8) / total
        if share >= 0.02:
            by[b] = (median(lambda m, b=b: b <= m < b + 8), share)
    light, heavy = median(lambda m: m < LIGHT), median(lambda m: m >= HEAVY)
    return dict(light=light, heavy=heavy, all=median(lambda m: True), by=by, deaths=total,
                heavy_share=sum(int(r["n"]) for r in rows if float(r["mass"]) >= HEAVY) / total,
                ratio=(heavy / light if light and heavy else None))


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
    li = lives(r, fo)
    return dict(pace=half_mean(d, "pace"), turned=half_mean(d, "turned"), lives=li, life=li["all"],
                life_light=li["light"], life_heavy=li["heavy"], life_ratio=li["ratio"], heavy_share=li["heavy_share"],
                mass=half_mean(d, "mass_p50"), mass_p10=half_mean(d, "mass_p10"), mass_p90=half_mean(d, "mass_p90"),
                mass_mean=half_mean(d, "mass_mean"), age_p50=half_mean(d, "age_p50"), age_p90=half_mean(d, "age_p90"),
                bodies=bodies, floors=[x["pop"] for x in w], floor=floor, died=died,
                floor_txt=f"died at {died:,}" if died else f"{floor:,}", births=half_mean(d, "births") / LOG,
                age=half_mean(f, "age_mean"), lineages=half_mean(f, "lineages"), broken=broken, per_body=broken / bodies,
                hunter=broken / bodies >= STATE_LINE, plant=plant, hunted=hunted, scav=scav, share=hunted / (plant + hunted + scav),
                size=half_mean(d, "size_p50"), muscle=half_mean(d, "muscle_mean"), gut=half_mean(d, "digestive_mean"),
                speed=half_mean(d, "speed_mean"), moved=half_mean(d, "moved"), stalled=half_mean(d, "stalled"),
                blocked=half_mean(d, "blocked"), forward=half_mean(d, "forward"), stay=half_mean(d, "stay"),
                trees=half_mean(d, "trees"), tree_eaten=half_mean(d, "tree_eaten"), regrowth=half_mean(d, "regrowth"),
                mean_res=half_mean(d, "mean_res"), intake=half_mean(d, "intake_per_gut"), travel=tr, grown=grown,
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
        base = 0  # the same seed without the clock
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


def life_chart(title, subtitle, laws=(0, 1, 2)):
    """Median life in world steps by the mass at birth, the seeds pooled (the deaths of the second half)."""
    fig, ax = new_axes("mass at birth")
    for law in laws:
        rows = []
        for s in SEEDS:
            r = run(law, s)
            if exists(r, folder(law)):
                rows += [x for x in load_rows(f"results/{r}_deaths.csv", folder(law)) if int(x["step"]) > STEPS // 2]
        if not rows:
            continue
        total = sum(int(x["n"]) for x in rows)
        pts = []
        for b in range(0, 129, 8):
            sel = sorted((int(x["age"]) + 25, int(x["n"])) for x in rows if b <= float(x["mass"]) < b + 8)
            n = sum(k for _, k in sel)
            if n < 0.02 * total:
                continue
            c = 0
            for age, k in sel:
                c += k
                if c >= n / 2:
                    pts.append((b + 4, age))
                    break
        ax.plot([p[0] for p in pts], [p[1] for p in pts], color=SERIES[LAWS[law][1]], marker="o", markersize=5, linewidth=1.8, label=LAWS[law][0])
    ax.set_ylim(0, None)
    ax.yaxis.set_major_formatter(kfmt)
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


# Hand-written mechanism diagram: ten world steps as a row of boxes for each of two bodies. The
# light body takes a turn in every step (the accent), the heavy one in seven of ten; what a body
# does happens on its turns, and the world's clocks run in every step.
TURNS_HEAVY = [1, 2, 4, 5, 7, 8, 9]  # the steps a body of mass 64 takes a turn in (phase at 0.71 a step)
BOXES = "".join(
    f'<rect x="{250 + i * 40}" y="{y}" width="32" height="30" rx="4" fill="{fill}" stroke="{stroke}" stroke-width="1.6" fill-opacity="{op}"/>'
    for y, turns in ((44, list(range(10))), (124, TURNS_HEAVY))
    for i in range(10)
    for fill, stroke, op in [("var(--s1)", "var(--s1)", "0.85") if i in turns else ("none", "currentColor", "0.4")]
)
DIAGRAM = f"""
<figure class="fig diagram">
<svg viewBox="0 0 880 226" width="100%" role="img" aria-label="Ten world steps as a row of boxes for two bodies: a body of mass 16 takes a turn in every step, a body of mass 64 in seven steps of ten; on a turn a body eats, pays its upkeep, ages, decides, acts and breeds, and between its turns the world's sun, regrowth, season and rain run on and other bodies can push it" font-size="12" fill="currentColor" stroke="currentColor">
  {BOXES}
  <g stroke="none">
    <text x="16" y="52">a body of mass 16</text>
    <text x="16" y="69" fill="var(--s1)">a turn every step</text>
    <text x="16" y="132">a body of mass 64</text>
    <text x="16" y="149" fill="var(--s1)">(16/64)^0.25 = 0.71 of a turn a step</text>
    <text x="250" y="36" font-size="11">ten steps of the world</text>
    <text x="672" y="52">on a turn: it eats, pays its</text>
    <text x="672" y="69">upkeep, ages, decides, acts, breeds</text>
    <text x="672" y="132">between turns: the world runs on</text>
    <text x="672" y="149">(sun, regrowth, season, rain), and</text>
    <text x="672" y="166">another body can push, break or eat it</text>
    <text x="250" y="196" font-size="11">Kleiber: the upkeep of a body comes to about mass^3/4 a step, its life and the time to a child to about mass^1/4 steps - none of them written as a rule.</text>
  </g>
</svg>
<figcaption>Figure 1. What the clock changes. A body of mass m takes (16 / m)^0.25 turns per world step, at most one: mass 16 takes one every step, mass 64 seven steps in ten, mass 256 one step in two.</figcaption>
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
    pc = lambda v: f"{v:.1%}"
    f1 = lambda v: f"{v:.1f}"
    for s in SEEDS:
        for law in LAWS:
            x = st[law][s]
            if not x:
                continue
            i, share, cells, muscle, gut, meat, speed = x["top"]
            print(f"seed {s} {LAWS[law][0]:11s} {'HUNTER' if x['hunter'] else 'grazer'} floor {x['floor_txt']} floors {x['floors']} kills {x['share']:.1%} "
                  f"| bodies {x['bodies']:.0f} births {x['births']:.2f} age {x['age']:.0f} lineages {x['lineages']:.1f} pace {x['pace']:.3f} turned {x['turned']:.3f}")
            print(f"      mass p10/p50/p90 {x['mass_p10']:.1f}/{x['mass']:.1f}/{x['mass_p90']:.1f} mean {x['mass_mean']:.1f} size p50 {x['size']:.1f} muscle {x['muscle']:.2f} gut {x['gut']:.2f} "
                  f"speed {x['speed']:.3f} moved {x['moved']:.4f} stalled {x['stalled']:.2f} travel {fmt_opt(x['travel'], f1)} of {x['grown']}")
            li = x["lives"]
            bins = " ".join(f"{b}-{b + 7}:{v[0]}({v[1]:.0%})" for b, v in sorted(li["by"].items()) if v[0])
            print(f"      life p50 {fmt_opt(x['life'], str)} light {fmt_opt(li['light'], str)} heavy {fmt_opt(li['heavy'], str)} heavy over light {fmt_opt(x['life_ratio'], lambda v: f'{v:.2f}')} "
                  f"heavy {pc(li['heavy_share'])} of {li['deaths']:,} deaths | by mass at birth {bins}")
            print(f"      trees {x['trees']:.0f} tree_eaten {x['tree_eaten']:.1f} regrowth {x['regrowth']:.1f} intake/gut {x['intake']:.4f} mean_res {x['mean_res']:.3f} "
                  f"plant {x['plant']:.1f} hunted {x['hunted']:.1f} scav {x['scav']:.1f}")
            print(f"      top {i} {share:.0%} {cells:.1f} cells {muscle:.1f} muscle {gut:.1f} gut {meat:.0%} flesh speed {speed:.2f} | diversity {x['div']} of {x['wins']}")
    for law in LAWS:
        xs = [st[law][s] for s in SEEDS if st[law][s]]
        print(f"{LAWS[law][0]}: hunter worlds {sum(x['hunter'] for x in xs)} of {len(xs)}; bodies {sum(x['bodies'] for x in xs) / max(len(xs), 1):.0f}")


def main():
    st = all_stats()
    logs = {f"{LAWS[law][0]}, seed {s}": load_csv(f"results/{run(law, s)}_log.csv") for law in LAWS for s in SEEDS if st[law][s]}

    charts_life = [
        life_chart("How long a body lives, by the mass it was born with", "Median life in world steps of the bodies that died over the "
                   "second half, by the mass at birth in bins of 8, the four seeds pooled (bins holding 2% of the deaths or more)."),
        seed_chart("The life of the heavy over the life of the light", "Median life of the bodies born at mass 48 or more over that of "
                   "the bodies born under 24. Above the dotted line the heavy live longer.", st, "life_ratio", laws=(0, 1, 2),
                   hline=1, fmt=lambda y, _p: f"{y:g}x"),
    ]
    charts_size = [
        ratio_chart("The mass of the living, against the same seed without the clock", "The 90th percentile of the mass of the living, "
                    "second half, over the same seed without the law. Above the line the law made bodies heavier.", st, "mass_p90", (1, 2)),
        seed_chart("The middle mass", "The median mass of the living, averaged over steps 50,000-100,000.", st, "mass", laws=(0, 1, 2)),
    ]
    charts_world = [
        ratio_chart("Bodies, against the same seed without the clock", "Bodies alive over the second half, over the same seed without "
                    "the law. Below the line the law costs the world bodies.", st, "bodies", (1, 2)),
        seed_chart("Lowest winter", "The fewest bodies alive in any winter; the dotted line is the hypothesis's 50.", st, "floor",
                   laws=(0, 1, 2), hline=50),
    ]

    def cell(s, key, f, laws=(0, 1, 2)):
        return "<td>" + " / ".join(fmt_opt(st[law][s][key] if st[law][s] else None, f) for law in laws) + "</td>"

    pc = lambda v: f"{v:.0%}"
    seed_rows = ""
    for s in SEEDS:
        if not st[0][s]:
            continue
        seed_rows += (f"<tr><td>{s}</td>{cell(s, 'pace', lambda v: f'{v:.2f}')}"
                      f"{cell(s, 'mass', lambda v: f'{v:.0f}')}{cell(s, 'mass_p90', lambda v: f'{v:.0f}')}"
                      f"{cell(s, 'life_light', str)}{cell(s, 'life_heavy', str)}"
                      f"{cell(s, 'bodies', lambda v: f'{v:,.0f}')}{cell(s, 'floor_txt', str)}"
                      f"{cell(s, 'share', pc)}{cell(s, 'div', str)}</tr>")
    tables = data_table(["step", "pop", "births", "deaths_energy", "pace", "turned", "mass_p10", "mass_p50", "mass_p90", "size_p50",
                         "moved", "stalled", "blocked", "speed_mean", "muscle_mean", "digestive_mean", "age_p50", "age_p90",
                         "trees", "tree_eaten", "regrowth", "intake_per_gut"], logs)
    TEXT.update(TEXTS)
    TEXT["gallery"] = gallery(GALLERY, GALLERY_CAPTION) if GALLERY else ""
    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>e052 A time that scales with size - Report</title>
<style>{CSS}</style>
</head>
<body>
<main>
<h1>e052: A time that scales with size</h1>
<p class="sub">Experiment report - 2026-09-12 - a body's own clock runs slower the more it weighs, in e048's world, seeds 9-12, against the same seeds without it. Answer: {TEXT["sub_answer"]}</p>

<section class="tldr">
<h2>TL;DR</h2>
<p>{TEXT["tldr"]}</p>
</section>

<h2>1. Question</h2>
<p>{TEXT["question"]}</p>
<ol>
  <li><strong>The law acts:</strong> bodies born at mass 48 or more die older than bodies born under 24, on three seeds of four; without the clock there is no such difference.</li>
  <li><strong>Size pays:</strong> the mass of the living (90th percentile, second half) is above the same seed's without the law, on three seeds of four.</li>
  <li><strong>Different sizes at once:</strong> the diversity number (#42) is above the control's on two seeds or more and below it on none.</li>
  <li><strong>The world stands:</strong> every winter floor above 50.</li>
</ol>

<h2>2. The law</h2>
<p>{TEXT["world"]}</p>
{DIAGRAM}
<p><strong>Runs.</strong> {TEXT["runs"]}</p>
<ul class="measures">
  <li><strong>pace</strong> - the turns a living body gets per world step (1 without the law).</li>
  <li><strong>mass</strong> - what a body's blocks weigh, by kind and density; the median and the 90th percentile of the living.</li>
  <li><strong>life</strong> - the steps a body lived when it died, by the mass it was born with.</li>
  <li><strong>lowest floor</strong> - the fewest bodies alive in any winter.</li>
  <li><strong>moved</strong> - sub-cells a body moves by its own actions, per step.</li>
  <li><strong>state, diversity</strong> - the flesh of kills in what bodies eat; the diversity number (#42).</li>
</ul>

<h2>3. Results</h2>
<p>Means over the second half (steps 50,000-100,000). Each cell is without the clock / with it / at a flat pace on the same seed; the lives are medians in world steps over the deaths of the second half.</p>
<div class="tw"><table>
<thead><tr><th>seed</th><th>pace</th><th>mass p50</th><th>mass p90</th><th>life, born light</th><th>life, born heavy</th><th>bodies</th><th>lowest floor</th><th>kills' share</th><th>diversity</th></tr></thead>
<tbody>{seed_rows}</tbody></table></div>
<ol class="verdicts">
{TEXT["verdicts"]}
</ol>

<h3>3.1 {TEXT["h_life"]}</h3>
<div class="grid2">
{"".join(charts_life)}
</div>
<p>{TEXT["p_life"]}</p>

<h3>3.2 {TEXT["h_size"]}</h3>
<div class="grid2">
{"".join(charts_size)}
</div>
<p>{TEXT["p_size"]}</p>

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
<p>Every log step (10,000 steps) of the eight runs, with and without the clock. The full data are in <code>results/*.csv</code>. Build this report with <code>uv run python experiments/e052_clock/report.py</code>.</p>
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
    ("no clock, seed 9", 0, 9, 325, "the hunter the clock removes", "Hard blocks across the front, muscle down one side, gut behind: 67% of the last third, half of its food flesh."),
    ("clock 0.25, seed 9", 1, 9, 313, "the small grazer that replaces it", "Two rows of muscle over two of gut on a 4x4 grid: 30% of the last third, 19% flesh, no armor."),
    ("clock 0.25, seed 10", 1, 10, 920, "the gut plate", "Muscle in front of a plate of gut: 49% of the last third."),
    ("clock 0.25, seed 12", 1, 12, 1419, "the heaviest winner", "Two rows of muscle before three of gut, mass 50 against the control's 37: 82% of the last third."),
]
GALLERY_CAPTION = ("The usual grown body of four leading lineages, front up (orange muscle, aqua gut, yellow sensor, blue hard). "
                   "Under the clock no winner carries armor, and the heaviest of them is a gut.")

TEXTS = {
    "sub_answer": ("no, under these runs' conditions: the clock buys long lives and a fuller world, not bodies of different sizes, "
                   "and it costs the world its hunters. Kept as an argument."),
    "tldr": ("A body's own time now runs slower the more it weighs: mass 16 takes a turn every step, mass 64 seven steps in ten. "
             "Bodies live two to four times as long, wear kills for the first time, and the world holds 8-37% more of them. But the "
             "masses do not spread, diversity falls to 1 on every seed, and the hunters disappear - which the same slowdown applied "
             "to every body alike does not do. Kept as an argument, not as the default."),
    "question": ("What follows a change in this world is the lineage, not the body: a body lives about 200 steps, so a moving rain is "
                 "followed by births (e049) and learning rides on hunters (e050, e051). In the real world every clock of a body runs "
                 "at about mass^-1/4. This law gives a body of mass m that many turns a step, and asks:"),
    "world": ("A body of mass m takes (16 / m)^0.25 turns a world step, at most one. Everything it does happens on its turns - "
              "eating, paying its upkeep, ageing by wear, deciding, acting, breeding - and the world's clocks do not scale: the sun, "
              "the regrowth, the season and the rain run per step, and another body can push, break or eat it between its turns."),
    "runs": ("Seeds 9-12, 100,000 steps: the clock at 0.25, the same world without it (e048's motor runs byte for byte, run again for "
             "the new measures), and a control at a flat pace of 0.84 - the same slowdown for every body, whatever it weighs - added "
             "when the batch came back. Twelve runs, 26 and 25 minutes in two batches. Before them a check (clock 0: e048 byte for "
             "byte) and a pilot."),
    "verdicts": ("<li><span class=\"verdict partly\">Lives only</span> Lives lengthen (the mean age of the living 278-739 to "
                 "874-1,432 on three seeds; deaths by wear 0.6-534 to 281-1,837 a log interval), but bodies born heavy already "
                 "outlived bodies born light without the law (1.4-4.3 times), so the clock did not make that difference.</li>"
                 "<li><span class=\"verdict no\">No</span> The 90th percentile of the mass is above the control's on one seed of "
                 "four, and the flat pace moves the masses as much.</li>"
                 "<li><span class=\"verdict no\">No</span> The diversity number is 1 on all four seeds, against 2, 2, 1, 1.</li>"
                 "<li><span class=\"verdict\">Yes</span> Winter floors 465-776 against 347-742, with 8-37% more bodies.</li>"),
    "h_life": "Bodies live two to four times as long, and wear bites for the first time",
    "p_life": ("The clock binds at 0.78-0.88 turns a step. The mean age of the living rises from 317, 739 and 278 to 1,328, 1,432 and "
               "874 on seeds 9, 11 and 12 (seed 10 was already old: 1,329 to 1,337), and the 90th percentile of the age at death from "
               "580-863 to 1,163-3,835 on those three. Wear, which took 0.6-3 deaths a log interval on the two hunter seeds, now "
               "takes 281-1,367. But the bodies born heavy outlived the bodies born light without the law too: the clock lengthens "
               "lives, it does not sort them by size."),
    "h_size": "The masses do not spread",
    "p_size": ("The median mass rises on two seeds (41 to 47, 37 to 50) and the 90th percentile on one (54 to 72); on seeds 9 and 11 "
               "nothing moves, and the flat pace moves them as much. Under the clock the winner is a gut with muscle and no armor on "
               "every seed, and the diversity number is 1 everywhere: up to six lineages hold 5% of the last third, but they are the "
               "same body."),
    "h_world": "A fuller world without hunters",
    "p_world": ("The world holds 2,569 bodies on average against 2,180, and every winter floor is higher. The flat pace gives 2,338: "
                "about half of the gain is the slowdown itself. The hunters are not: at a flat pace hunter worlds come on three seeds "
                "of four (one seed turns hunter that was not), under the clock on none, and the share of the living with a bite falls "
                "from 40-47% to 0.1-0.6%."),
    "discussion": ("<p>A slower body is a cheaper body: its upkeep, intake, moves and ageing all fall with its pace, so the same food "
                   "feeds more bodies and each lives longer. The flat-pace control says about half of that is the slowdown itself.</p>"
                   "<p>Scaling time by size, though, is a tax on the hunter. A grazer's income is set by the world's clock - the plant "
                   "grows per step whatever the body does - while a hunter's income is made of its own actions, and the heavier a "
                   "hunter is (armor, mass) the fewer turns it gets. Under the clock no winning lineage carries a hard block and "
                   "hunter worlds vanish; under the same slowdown for every body they come back. This is the first law of the series "
                   "that removes predation through the price of time rather than through what the world feeds.</p>"
                   "<p>What this does not show: that a time scaling with size is wrong, or that long-lived bodies are worthless. The "
                   "answers hang on our choices - the mass whose clock is the world's step (16), the exponent (0.25, so the bodies "
                   "here span 0.78-0.88 and none is slow enough to be another kind of animal), e048's world with no brain, four seeds "
                   "of 100,000 steps.</p>"),
    "conclusion": ("Not kept as the default; the clock stays as argument 47. Under these conditions it buys lives and bodies, not "
                   "sizes, and it costs the world its hunters. What the behavior track asked for now exists as an argument: bodies "
                   "that live long enough to meet a change themselves. Next: e049's moving rain under the clock, with and without "
                   "e050's brain - does a body that lives four times as long follow the band itself, instead of being followed by "
                   "births?"),
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
