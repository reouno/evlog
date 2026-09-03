#!/usr/bin/env python3
"""Build report.html for e025.

Charts: matplotlib, exported as SVG and inlined. Diagram: hand-written SVG.
Run from the repo root: uv run python experiments/e025_weight/report.py
"""
import base64
import csv
import gzip
import html
import io
import json
import math
import os
import statistics
from collections import Counter, defaultdict

import matplotlib
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator, PercentFormatter

matplotlib.use("svg")

HERE = os.path.dirname(os.path.abspath(__file__))
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4"]  # fixed slot order
LINEAGE_PALETTE = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#7b61ff", "#00a3c4", "#c94c4c", "#6aa84f", "#b8860b", "#8e44ad", "#e67e22"]
NONE_COLOR = "#898781"

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

E024 = os.path.join(HERE, "..", "e024_flesh")
# Places of a world: (id in the CSVs, name, color). Under the uniform sun a place is a height band (thirds of the cells by the
# terrain); the flat world is rained on alike, the bands are kept for the loaders.
BANDS = [(0, "valleys (lowest third)", SERIES[0]), (1, "slopes (middle third)", SERIES[3]), (2, "ridges (highest third)", SERIES[1])]
# Worlds of this experiment: label -> run prefix, world size, places, seeds.
WORLDS = {
    "weight 1": dict(run="128_sigma0_r64_f0.1_flat_eyes8_flesh1_w1", size=128, places=BANDS, seeds=[1, 2, 3, 4], uniform=True),
}
WEIGHT = list(WORLDS)[0]
PILOT_RUN = "128_sigma0_r64_f0.1_flat_eyes8_flesh1_w{}_seed9"  # the pilots: seed 9, 200,000 steps, at weight 0, kind, density and 1
PILOTS = [("0", "every block 1"), ("kind", "kind only"), ("density", "density only"), ("1", "both")]
# The control: e024's flat runs at flesh 1, the same law with every block at 1 (on the f32 ground and the leaking ledger).
REFS = {"e024: every block 1": ("128_sigma0_r64_f0.1_flat_eyes8_flesh1", E024, True)}
E024_FLAT = list(REFS)[0]
WORLD_COLOR = {WEIGHT: SERIES[0], E024_FLAT: "#b5b3ab"}
CELL_ENERGY = 0.02
BITE = 0.02
KIND_COLOR = {1: SERIES[0], 2: SERIES[1], 3: SERIES[3], 4: SERIES[2]}
CONFIRM_STEPS = 5000
VIEWER_WORLD = WEIGHT
VIEWER_SEED = 1
LAST_STEP = 500_000


def seeds_of(w):
    if w not in WORLDS:  # a reference world
        return [1, 2, 3, 4]
    if os.environ.get("EVLOG_SEEDS"):  # a dry run on the seeds that are done
        return [int(x) for x in os.environ["EVLOG_SEEDS"].split(",")]
    return WORLDS[w]["seeds"]


def place_names(w):
    return {p: name for p, name, _ in WORLDS[w]["places"]}


def place_colors(w):
    return {p: color for p, _, color in WORLDS[w]["places"]}


# ---------- data ----------

def load_csv(path, folder=HERE):
    with open(os.path.join(folder, path)) as f:
        rows = [r for r in csv.DictReader(f) if None not in r.values()]  # a run still writing may end mid-line
    return {k: [float(r[k]) for r in rows] for k in rows[0]}


def load_rows(path, folder=HERE):
    with open(os.path.join(folder, path)) as f:
        return [r for r in csv.DictReader(f) if None not in r.values()]


def load_places(run, folder=HERE):
    """places.csv split by place: {width: {column: [values]}}."""
    rows = load_rows(f"results/{run}_places.csv", folder)
    out = {}
    for r in rows:
        if None in r.values():
            continue  # a run still writing may end mid-line
        if "cells" in r and float(r["cells"]) == 0:
            continue  # the uniform world's "beyond the patches" row: no cell, named 0 like its one place
        p = int(float(r["place"]))
        d = out.setdefault(p, defaultdict(list))
        for k, v in r.items():
            d[k].append(float(v))
    return out


def lineage_rows(run, folder=HERE):
    by = defaultdict(list)
    for r in load_rows(f"results/{run}_lineages.csv", folder):
        by[int(r["lineage"])].append(r)
    return by


def lineage_stats(run, folder=HERE):
    """Per lineage: first and last step seen as a group, max size."""
    first, last, size = {}, {}, defaultdict(int)
    for r in load_rows(f"results/{run}_lineages.csv", folder):
        i, s = int(r["lineage"]), int(r["step"])
        first.setdefault(i, s)
        last[i] = s
        size[i] = max(size[i], int(r["size"]))
    return first, last, size


def home_of(r):
    """The kind of place most of a lineage's members stand in at one detection: 0 (first width), 1 (second), or None."""
    p0, p1 = int(r["p0"]), int(r["p1"])
    if p0 + p1 == 0:
        return None
    return 0 if p0 >= p1 else 1


def lineage_places(run):
    """Per lineage: detections with home in the first kind, in the second kind, and with both kinds holding
    at least 10% of the members. A lineage that moved home has 20+ detections (20,000 steps) of each home;
    a shared one has 20+ detections with both."""
    out = {}
    for lid, rows in lineage_rows(run).items():
        h0 = sum(1 for r in rows if home_of(r) == 0)
        h1 = sum(1 for r in rows if home_of(r) == 1)
        both = sum(1 for r in rows if min(int(r["p0"]), int(r["p1"])) >= 0.1 * int(r["size"]))
        out[lid] = dict(h0=h0, h1=h1, both=both, moved=h0 >= 20 and h1 >= 20, shared=both >= 20,
                        steps=int(rows[-1]["step"]) - int(rows[0]["step"]) + CONFIRM_STEPS, agent_steps=sum(int(r["size"]) for r in rows))
    return out


def hunter_lineages(run, folder=HERE, min_steps=20_000, min_bite=2.0, key="bite"):
    out = []
    for lid, rows in lineage_rows(run, folder).items():
        h = [r for r in rows if float(r[key]) >= min_bite]
        if not h:
            continue
        span = int(h[-1]["step"]) - int(h[0]["step"]) + CONFIRM_STEPS
        if span < min_steps:
            continue
        peak = max(h, key=lambda r: int(r["size"]))
        m, p = float(peak["meat"]), float(peak["plant"])
        out.append(dict(id=lid, span=span, size=int(peak["size"]), mass=float(peak["mass"]), bite=float(peak["bite"]), diet=m / (m + p) if m + p > 0 else 0.0,
                        front=float(peak.get("shell_front", 0)), back=float(peak.get("shell_back", 0))))
    out.sort(key=lambda d: -d["span"])
    return out


def to_world(i, f):
    """Where cell i of the body grid lands in the world frame when the body faces f (the simulation's rule)."""
    r, c = divmod(i, 8)
    m = 7
    if f == 0:
        r2, c2 = r, c
    elif f == 1:
        r2, c2 = m - r, m - c
    elif f == 2:
        r2, c2 = c, m - r
    else:
        r2, c2 = m - c, r
    return r2 * 8 + c2


def neighbors_of(run, folder=HERE, size=128, first_step=500_000):
    """Mean over bodies of the other bodies holding a sub-cell in the 3x3 world cells around the cell under the
    middle of the body's box, per snapshot from `first_step` on; returns (steps, values). Read from long.jsonl."""
    bodies = load_bodies(run, folder)
    rotated = {}
    sw = size * 4
    steps, vals = [], []
    for fr in read_frames(f"results/{run}_long.jsonl", folder):
        if fr["step"] < first_step:
            continue
        holders = defaultdict(set)  # world cell -> bodies holding a sub-cell in it
        heres = []
        for k, (x, y, b, _d, _lin, f) in enumerate(fr["agents"]):
            key = (b, f)
            if key not in rotated:
                cells = bodies[b]
                pts = [divmod(to_world(i, f), 8) for i, v in enumerate(cells) if v != "0"]
                rs = [r for r, _ in pts]
                cs = [c for _, c in pts]
                rotated[key] = (pts, ((min(rs) + max(rs)) // 2, (min(cs) + max(cs)) // 2)) if pts else ([], (0, 0))
            pts, (mr, mc) = rotated[key]
            for r, c in pts:
                holders[(((y + r) % sw) // 4, ((x + c) % sw) // 4)].add(k)
            heres.append((k, ((y + mr) % sw) // 4, ((x + mc) % sw) // 4))
        n = 0
        for k, cy, cx in heres:
            others = set()
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    others |= holders.get(((cy + dy) % size, (cx + dx) % size), set())
            others.discard(k)
            n += len(others)
        steps.append(fr["step"])
        vals.append(n / max(len(heres), 1))
    return steps, vals


def scavenger_lineages(run, folder=HERE, min_steps=20_000):
    """Lineages that lived min_steps or more with dead matter more than half of their members' lifetime intake: (id, span, peak size, diet)."""
    out = []
    for lid, rows in lineage_rows(run, folder).items():
        h = [r for r in rows if float(r["meat"]) > float(r["plant"]) and float(r["meat"]) > 0]
        if not h:
            continue
        span = int(h[-1]["step"]) - int(h[0]["step"]) + CONFIRM_STEPS
        if span < min_steps:
            continue
        peak = max(h, key=lambda r: int(r["size"]))
        m, p = float(peak["meat"]), float(peak["plant"])
        out.append(dict(id=lid, span=span, size=int(peak["size"]), diet=m / (m + p)))
    out.sort(key=lambda d: -d["span"])
    return out


def soil_maps(run, folder=HERE):
    """The soil and the plants of every cell every 100,000 steps: [(step, soil, plant)]."""
    return [(d["step"], d["soil"], d["plant"]) for d in read_frames(f"results/{run}_soil.jsonl", folder)]


def place_map(patches, size):
    """The place of every cell (the width of the patch that gives it the most sun; 0 beyond every patch), from a frame's
    patches [x, y, sigma], as the simulation computes it. A width of 0 is the uniform sun: every cell is place 0."""
    if patches and patches[0][2] == 0:
        return [0] * (size * size)
    best = [0.0] * (size * size)
    place = [0] * (size * size)
    for cx, cy, sg in patches:
        peak = 1.0 / (sg * sg)
        r = int(math.ceil(3 * sg))
        for dy in range(-r, r + 1):
            for dx in range(-r, r + 1):
                v = peak * math.exp(-(dx * dx + dy * dy) / (2.0 * sg * sg))
                c = ((cy + dy) % size) * size + (cx + dx) % size
                if v > best[c]:
                    best[c] = v
                    place[c] = int(sg)
    return place


def here_cells(frame, bodies, size):
    """The world cell under the middle of each body's box in a long frame."""
    sw = size * 4
    out = []
    rotated = {}
    for x, y, b, _d, _lin, f in frame["agents"]:
        key = (b, f)
        if key not in rotated:
            pts = [divmod(to_world(i, f), 8) for i, v in enumerate(bodies.get(b, "")) if v != "0"]
            rs = [r for r, _ in pts] or [0]
            cs = [c for _, c in pts] or [0]
            rotated[key] = ((min(rs) + max(rs)) // 2, (min(cs) + max(cs)) // 2)
        mr, mc = rotated[key]
        out.append((((y + mr) % sw) // 4) * size + ((x + mc) % sw) // 4)
    return out


def terrain_of(run, folder=HERE):
    """The terrain of a run (written once): relief, flow, height and band of every cell."""
    with open(os.path.join(folder, f"results/{run}_terrain.json")) as f:
        return json.load(f)


def soil_stats(run, size=128, uniform=True, folder=HERE):
    """Per soil dump (every 100,000 steps): where the soil lies. top: share of the soil in the richest tenth of the cells (0.1 if
    flat); wet: share of the cells with a step of sun's worth of soil (0.01); per place (a height band under the uniform sun, a
    patch width with drawn patches) the soil per cell, its share of the world's soil, the share of the bodies standing there, and
    the shares of bare (under 1), wet and deep (8 and more) cells; under: soil under the bodies over the soil of the cells with
    no body."""
    frames = {fr["step"]: fr for fr in read_frames(f"results/{run}_long.jsonl", folder)}
    bodies = load_bodies(run, folder)
    bands = terrain_of(run, folder)["band"] if uniform else None
    out = []
    for step, soil, plant in soil_maps(run, folder):
        fr = frames.get(step)
        if fr is None:
            continue
        n = len(soil)
        srt = sorted(soil, reverse=True)
        total = sum(srt) or 1e-9
        top = sum(srt[: n // 10]) / total
        pm = bands if uniform else place_map(fr["patches"], size)
        heres = here_cells(fr, bodies, size)
        held = set(heres)
        by = {}
        for p in set(pm):
            cells = [i for i in range(n) if pm[i] == p]
            here_n = sum(1 for c in heres if pm[c] == p)
            by[p] = dict(cells=len(cells), soil=sum(soil[i] for i in cells) / len(cells), plant=sum(plant[i] for i in cells) / len(cells),
                         soil_share=sum(soil[i] for i in cells) / total, pop_share=here_n / max(len(heres), 1),
                         bare=sum(1 for i in cells if soil[i] < 1) / len(cells), wet=sum(1 for i in cells if soil[i] >= 0.01) / len(cells),
                         deep=sum(1 for i in cells if soil[i] >= 8) / len(cells))
        under = [soil[i] for i in held]
        free = [soil[i] for i in range(n) if i not in held]
        out.append(dict(step=step, top=top, mean=total / n, by=by, wet=sum(1 for s in soil if s >= 0.01) / n,
                        under=sum(under) / max(len(under), 1), free=sum(free) / max(len(free), 1)))
    return out


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
    ax.xaxis.set_major_formatter(kfmt)
    ax.set_xlabel(xlabel, loc="right")
    ax.margins(x=0)
    return fig, ax


def legend_above(ax, n):
    ax.legend(loc="lower left", bbox_to_anchor=(0, 1.0), ncols=n, handlelength=1.2, borderaxespad=0, columnspacing=1.2)


def figure(title, subtitle, svg):
    return f"""
<figure class="fig">
  <figcaption><strong>{html.escape(title)}</strong><span>{html.escape(subtitle)}</span></figcaption>
  {svg}
</figure>"""


def finish(ax, ymin, ymax, top, percent, n_legend):
    if ymin is not None:
        ax.set_ylim(ymin, max(ymax if ymax is not None else top * 1.12, ymin + 1e-9))
    fine = percent and ax.get_ylim()[1] < 0.02
    ax.yaxis.set_major_formatter((lambda y, _p: f"{y:.2%}" if fine else f"{y:.0%}") if percent else kfmt)
    ax.yaxis.set_major_locator(MaxNLocator(4))
    legend_above(ax, n_legend)


def place_chart(title, subtitle, places, world, key_fn, refs=None, ymin=0, ymax=None, percent=False):
    """One thin line per seed and place of one world, colored by place. refs: {label: (value, color)} as dashed lines."""
    fig, ax = new_axes()
    top = 0
    for p, name, color in WORLDS[world]["places"]:
        for k, s in enumerate(seeds_of(world)):
            if p not in places[world][s]:
                continue
            d = places[world][s][p]
            ys = key_fn(d)
            top = max(top, max(ys))
            ax.plot(d["step"], ys, color=color, linewidth=1.1, alpha=0.85, label=name if k == 0 else None)
    for label, (v, color) in (refs or {}).items():
        ax.axhline(v, color=color, linestyle="--", linewidth=1, label=label)
        top = max(top, v)
    finish(ax, ymin, ymax, top, percent, 3)
    return figure(title, subtitle, to_svg(fig))


def place_lines_chart(title, subtitle, series, key_fn, ymin=0, ymax=None, percent=False):
    """One place of several worlds on one chart: series = [(label, color, {seed: places dict}, place id)], one thin line per seed."""
    fig, ax = new_axes()
    top = 0
    for label, color, by_seed, p in series:
        for k, (s, pl) in enumerate(sorted(by_seed.items())):
            if p not in pl:
                continue
            d = pl[p]
            ys = key_fn(d)
            top = max(top, max(ys))
            ax.plot(d["step"], ys, color=color, linewidth=1.1, alpha=0.85, label=label if k == 0 else None)
    finish(ax, ymin, ymax, top, percent, 2)
    return figure(title, subtitle, to_svg(fig))


def terrain_soil_figure(title, subtitle, picks):
    """Two rows: the terrain of one run per world (picks: [(world, seed)]) and the soil of every cell at the end of the run, on a
    log scale; with drawn patches, the patches as rings."""
    fig, axes = plt.subplots(2, len(picks), figsize=(13, 2 * 13 / len(picks) + 0.6))
    for col, (w, seed) in enumerate(picks):
        run = f"{WORLDS[w]['run']}_seed{seed}"
        size = WORLDS[w]["size"]
        t = terrain_of(run)
        h = t["height"]
        hmax = max(h) or 1
        grid = [[h[y * size + x] / hmax for x in range(size)] for y in range(size)]
        ax = axes[0][col]
        ax.imshow(grid, cmap="gray", vmin=0, vmax=1, interpolation="nearest")
        ax.set_title(f"{w}, seed {seed}\nterrain, relief {t['relief']:g}", fontsize=8, color=INK)
        step, soil, _ = soil_maps(run)[-1]
        grid = [[math.log1p(soil[y * size + x]) for x in range(size)] for y in range(size)]
        ax = axes[1][col]
        ax.imshow(grid, cmap="YlOrBr", vmin=0, vmax=math.log1p(30), interpolation="nearest")
        fr = next(fr for fr in read_frames(f"results/{run}_long.jsonl") if fr["step"] == step)
        for cx, cy, sg in fr["patches"]:
            if sg > 0:
                ax.add_patch(plt.Circle((cx, cy), 2 * sg, fill=False, color=place_colors(w)[int(sg)], linewidth=0.9, linestyle="--"))
        ax.set_title(f"soil at step {step:,}", fontsize=8, color=INK)
    for ax in axes.flat:
        ax.set_xticks([])
        ax.set_yticks([])
        ax.grid(False)
        for sp in ax.spines.values():
            sp.set_visible(False)
    return figure(title, subtitle, to_svg(fig))


def world_chart(title, subtitle, logs, key_fn, worlds, colors, ymin=0, ymax=None, percent=False, hline=None):
    """One thin line per seed, colored by world; one legend entry per world; `hline`: a dotted reference level."""
    fig, ax = new_axes()
    top = 0
    if hline is not None:
        ax.axhline(hline, color=INK, linestyle=":", linewidth=1)
    for w in worlds:
        for k, s in enumerate(seeds_of(w)):
            ys = key_fn(logs[w][s])
            if ys is None:
                continue
            top = max(top, max(ys))
            ax.plot(logs[w][s]["step"], ys, color=colors[w], linewidth=1.1, alpha=0.85, label=w if k == 0 else None)
    finish(ax, ymin, ymax, top, percent, 3)
    return figure(title, subtitle, to_svg(fig))


def stats_chart(title, subtitle, stats, key_fn, worlds, ymin=0, ymax=None, percent=False):
    """One line per run of the soil statistics (every 100,000 steps), colored by world."""
    fig, ax = new_axes()
    top = 0
    for w in worlds:
        for k, s in enumerate(seeds_of(w)):
            st = stats[w][s]
            if not st:
                continue
            ys = [key_fn(d) for d in st]
            top = max(top, max(ys))
            ax.plot([d["step"] for d in st], ys, color=WORLD_COLOR[w], linewidth=1.1, alpha=0.85, marker="o", markersize=2.5, label=w if k == 0 else None)
    finish(ax, ymin, ymax, top, percent, 3)
    return figure(title, subtitle, to_svg(fig))


def pilot_table():
    """The pilots (seed 9, 200,000 steps, one per weight mode): medians over the second half, as an HTML table."""
    cols = []
    for mode, label in PILOTS:
        path = os.path.join(HERE, "results", f"{PILOT_RUN.format(mode)}_log.csv")
        if not os.path.exists(path) or os.path.getsize(path) < 1000:  # a run still writing has an empty log
            continue
        log = load_csv(path)
        n = len(log["step"])
        h = slice(n // 2, n)
        med = lambda xs: statistics.median(xs[h])
        q = slice(3 * n // 4, n)
        pop = log["pop"]
        cols.append((f"{label} (<code>{mode}</code>)", dict(
            density=f"{med(log['density_mean']):.2f} &plusmn; {med(log['density_std']):.2f}", size=f"{med(log['size_mean']):.1f}", mass=f"{med(log['mass_mean']):.1f}",
            speed=f"{med(log['speed_mean']):.3f}", hard=f"{med(log['hard_mean']):.2f}", muscle=f"{med(log['muscle_mean']):.2f}",
            biters=f"{med(log['biters_share']):.1%} / {statistics.median(log['biters_share'][q]):.1%}", kills=f"{med([k / 10_000 for k in log['deaths_broken']]):.2f}",
            meat=f"{med([m / max(p + m, 1e-9) for p, m in zip(log['plant_intake'], log['meat_intake'])]):.0%}",
            fat=f"{med([f / m for f, m in zip(log['fat_stock'], log['matter'])]):.0%}", air=f"{med(log['air']):.0f}",
            pop=f"{med(pop):,.0f} ({statistics.pstdev(pop[h]) / max(statistics.mean(pop[h]), 1):.2f})", lineages=f"{med(log['lineages']):.0f}",
            matter=f"{log['matter'][-1] / log['matter'][0]:.6f}")))
    if not cols:
        return ""
    rows = [("Density per body (mean &plusmn; spread)", "density"), ("Cells per body; mass", "size|mass"), ("Speed (muscle over mass)", "speed"), ("Hard; muscle blocks per body", "hard|muscle"),
            ("Bodies with a bite (median / last quarter)", "biters"), ("Bodies killed per step", "kills"), ("Intake from other bodies", "meat"), ("Fat, share of the matter; air", "fat|air"),
            ("Population (cv)", "pop"), ("Lineages alive", "lineages"), ("Matter at the end over the start", "matter")]
    body = "".join(f"<tr><td>{label}</td>" + "".join("<td>" + " / ".join(d[k] for k in keys.split("|")) + "</td>" for _, d in cols) + "</tr>" for label, keys in rows)
    return ("<thead><tr><th>Pilot, seed 9, 200,000 steps (median over the second half)</th>" + "".join(f"<th>{c}</th>" for c, _ in cols) + "</tr></thead><tbody>" + body + "</tbody>")


def color_slots(run):
    first, _, _ = lineage_stats(run)
    return {lid: k % len(LINEAGE_PALETTE) for k, lid in enumerate(sorted(first, key=first.get))}


def timeline_chart(title, subtitle, run, events):
    """Every lineage as a band: size over time, colored by confirmation order. Events as marks."""
    slot = color_slots(run)
    by = lineage_rows(run)
    fig, ax = new_axes(size=(13, 3.6))
    ax.set_ylabel("agents in the lineage")
    for lid, rows in by.items():
        xs = [int(r["step"]) for r in rows]
        ys = [int(r["size"]) for r in rows]
        ax.fill_between(xs, 0, ys, color=LINEAGE_PALETTE[slot[lid]], alpha=0.35, linewidth=0)
        ax.plot(xs, ys, color=LINEAGE_PALETTE[slot[lid]], linewidth=1.0)
    marks = {"split": ("v", SERIES[1]), "merge": ("^", SERIES[2]), "extinct": ("x", SERIES[3]), "birth": ("o", SERIES[0])}
    for ev, (m, c) in marks.items():
        xs = [int(r["step"]) for r in events if r["event"] == ev]
        ys = [int(r["size"]) for r in events if r["event"] == ev]
        if xs:
            ax.scatter(xs, ys, marker=m, s=18, color=c, label=f"{ev} ({len(xs)})", zorder=3, linewidths=1)
    ax.set_ylim(0, None)
    ax.yaxis.set_major_locator(MaxNLocator(4))
    ax.yaxis.set_major_formatter(kfmt)
    legend_above(ax, 4)
    return figure(title, subtitle, to_svg(fig))


def data_table(cols, rows_by_name, every=10):
    out = []
    for name, d in rows_by_name.items():
        cols = [c for c in cols if c in d]
        rows = "".join(
            "<tr>" + "".join(f"<td>{d[c][i]:g}</td>" for c in cols) + "</tr>"
            for i in range(0, len(d[cols[0]]), every)
        )
        out.append(f"<details><summary>{html.escape(name)}</summary><div class='tw'><table><thead><tr>"
                   + "".join(f"<th>{c}</th>" for c in cols) + f"</tr></thead><tbody>{rows}</tbody></table></div></details>")
    return "\n".join(out)



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
.grid2 > .fig:only-child {{ max-width: 470px; }}
.fig {{ margin: 0; background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 14px 14px 8px; }}
.fig svg {{ width: 100%; height: auto; display: block; font-family: system-ui, -apple-system, "Segoe UI", sans-serif; }}
figcaption strong {{ display: block; font-size: 15px; }}
figcaption span {{ display: block; color: var(--ink2); font-size: 13px; min-height: 2.6em; margin-bottom: 6px; }}
.wide {{ margin: 12px 0; }}
.diagram {{ margin: 12px 0; background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 12px 16px 8px; color: var(--ink); }}
.diagram figcaption {{ color: var(--ink2); font-size: 13px; margin-top: 4px; }}
.cards {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(215px, 1fr)); gap: 14px; margin: 6px 0 10px; }}
.card {{ margin: 0; display: flex; gap: 10px; align-items: flex-start; }} .card svg {{ flex: none; }} .card figcaption {{ font-size: 12.5px; line-height: 1.4; color: var(--ink2); }} .card strong {{ color: var(--ink); }}
.measures {{ columns: 2; column-gap: 24px; max-width: none; padding-left: 20px; }} .measures li {{ break-inside: avoid; }}
table {{ border-collapse: collapse; font-size: 13.5px; font-variant-numeric: tabular-nums; }}
th, td {{ padding: 6px 12px; text-align: right; border-bottom: 1px solid var(--grid); }}
th:first-child, td:first-child {{ text-align: left; }}
th {{ color: var(--ink2); font-weight: 600; }}
.tw {{ overflow-x: auto; }}
details {{ margin: 8px 0; }} summary {{ cursor: pointer; color: var(--ink2); }}
.verdicts {{ list-style: none; padding: 0; margin: 12px 0 0; }} .verdicts li {{ margin: 4px 0; }}
.verdict {{ display: inline-block; padding: 1px 8px; border-radius: 4px; font-size: 12.5px; font-weight: 600; background: rgba(12,163,12,0.12); color: #006300; }}
.verdict.no {{ background: rgba(208,59,59,0.12); color: #a12b2b; }}
.verdict.partly {{ background: rgba(250,178,25,0.15); color: #8a5a00; }}
:root[data-theme="dark"] .verdict.partly {{ color: #fab219; }}
@media (prefers-color-scheme: dark) {{ :root:not([data-theme="light"]) .verdict.partly {{ color: #fab219; }} }}
:root[data-theme="dark"] .verdict {{ color: #0ca30c; }} :root[data-theme="dark"] .verdict.no {{ color: #e66767; }}
@media (prefers-color-scheme: dark) {{ :root:not([data-theme="light"]) .verdict {{ color: #0ca30c; }} :root:not([data-theme="light"]) .verdict.no {{ color: #e66767; }} }}
.viewer {{ background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 14px; display: grid; grid-template-columns: 1fr; gap: 10px; }}
.viewer .canvases {{ display: grid; grid-template-columns: 2fr 1fr; gap: 10px; align-items: start; }}
.viewer canvas {{ width: 100%; height: auto; image-rendering: pixelated; border-radius: 4px; }}
.viewer .bar {{ display: flex; gap: 10px; align-items: center; font-size: 13px; color: var(--ink2); flex-wrap: wrap; }}
.viewer input[type=range] {{ flex: 1; }}
.viewer button, .viewer select {{ font: inherit; font-size: 13px; padding: 2px 10px; }}
.viewer .lin {{ display: inline-block; padding: 0 6px; border-radius: 3px; color: #fff; font-size: 12px; margin-right: 4px; }}
.viewer .sw {{ display: inline-block; width: 11px; height: 11px; border-radius: 2px; vertical-align: -1px; margin: 0 3px 0 6px; }}
.viewer .sw.dot {{ background: #666; position: relative; }} .viewer .sw.dot::after {{ content: ""; position: absolute; left: 4px; top: 4px; width: 3px; height: 3px; background: #fff; }}
.viewer .sw.front {{ background: #666; border-top: 2px solid #fff; }}
@media (max-width: 700px) {{ .viewer .canvases {{ grid-template-columns: 1fr; }} }}
"""


DIAGRAM = """
<figure class="diagram">
<svg viewBox="0 0 900 330" role="img" aria-label="Two bodies of eight cells. The light one, mass 5.5 at density 1/2, is fast, cheap to move and made of little, and its faces break under a single muscle. The heavy one, mass 20 at density 2 with two hard blocks, is slow, dear to move and made of much, and its armor resists three times harder.">
<g fill="none" stroke="currentColor" stroke-width="1.2" font-size="12" font-family="system-ui, sans-serif">
  <!-- the scale of blocks -->
  <text x="450" y="28" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">what a block weighs: its kind, times the body's density (1/2 to 2, from the genome)</text>
  <g stroke="none">
    <rect x="250" y="44" width="22" height="22" fill="#2a78d6"/><text x="282" y="60" fill="currentColor" font-size="12">hard 2</text>
    <rect x="345" y="44" width="22" height="22" fill="#eb6834"/><text x="377" y="60" fill="currentColor" font-size="12">muscle 1</text>
    <rect x="455" y="44" width="22" height="22" fill="#1baf7a"/><text x="487" y="60" fill="currentColor" font-size="12">gut 1</text>
    <rect x="545" y="44" width="22" height="22" fill="#eda100"/><text x="577" y="60" fill="currentColor" font-size="12">sensor 1/2</text>
  </g>
  <!-- the light body -->
  <text x="200" y="110" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">light: density 1/2</text>
  <g stroke="none" transform="translate(150,120)">
    <rect x="0" y="0" width="100" height="50" rx="2" fill="currentColor" fill-opacity="0.08"/>
    <rect x="4" y="4" width="20" height="20" fill="#eb6834"/><rect x="28" y="4" width="20" height="20" fill="#eb6834"/><rect x="52" y="4" width="20" height="20" fill="#1baf7a"/><rect x="76" y="4" width="20" height="20" fill="#1baf7a"/>
    <rect x="4" y="27" width="20" height="20" fill="#1baf7a"/><rect x="28" y="27" width="20" height="20" fill="#1baf7a"/><rect x="52" y="27" width="20" height="20" fill="#1baf7a"/><rect x="76" y="27" width="20" height="20" fill="#eda100"/>
  </g>
  <text x="200" y="196" text-anchor="middle" fill="currentColor" stroke="none">8 cells, mass 3.75</text>
  <text x="200" y="214" text-anchor="middle" fill="currentColor" stroke="none">speed 2/3.75 = 0.53; a move costs 0.004</text>
  <text x="200" y="232" text-anchor="middle" fill="currentColor" stroke="none">made of 0.075; a face resists 1/2: one muscle breaks it</text>
  <!-- the heavy body -->
  <text x="700" y="110" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">heavy: density 2</text>
  <g stroke="none" transform="translate(650,120)">
    <rect x="0" y="0" width="100" height="50" rx="2" fill="currentColor" fill-opacity="0.08"/>
    <rect x="4" y="4" width="20" height="20" fill="#2a78d6"/><rect x="28" y="4" width="20" height="20" fill="#2a78d6"/><rect x="52" y="4" width="20" height="20" fill="#1baf7a"/><rect x="76" y="4" width="20" height="20" fill="#1baf7a"/>
    <rect x="4" y="27" width="20" height="20" fill="#eb6834"/><rect x="28" y="27" width="20" height="20" fill="#eb6834"/><rect x="52" y="27" width="20" height="20" fill="#eb6834"/><rect x="76" y="27" width="20" height="20" fill="#1baf7a"/>
  </g>
  <text x="700" y="196" text-anchor="middle" fill="currentColor" stroke="none">8 cells, mass 22</text>
  <text x="700" y="214" text-anchor="middle" fill="currentColor" stroke="none">speed 3/22 = 0.14; a move costs 0.022</text>
  <text x="700" y="232" text-anchor="middle" fill="currentColor" stroke="none">made of 0.44; its armor resists 6 per hard block, its gut 2</text>
  <!-- what is the same -->
  <path d="M 310,145 L 590,145" stroke-dasharray="4 4"/>
  <text x="450" y="138" text-anchor="middle" fill="currentColor" stroke="none">the same upkeep: 0.002 a cell + 0.032 a step</text>
  <text x="450" y="162" text-anchor="middle" fill="currentColor" stroke="none">the same bite, the same sight: per block</text>
  <!-- the ground -->
  <path d="M 40,290 L 860,290"/>
  <text x="450" y="312" text-anchor="middle" fill="currentColor" stroke="none">the ground: a child costs its mass x 0.02 of matter; a broken or dead block gives back what it was made of</text>
  <path d="M 200,240 L 200,282" marker-end="url(#ah)"/>
  <path d="M 700,240 L 700,282" marker-end="url(#ah)"/>
</g>
<defs>
  <marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="currentColor"/></marker>
</defs>
</svg>
<figcaption>Figure 1. The weight law. Everything is e024's world with its ledger fixed; the one law added is what a block weighs. A hard block weighs 2, a sensor 1/2, muscle and gut 1, and every block of a body weighs that times the body's density, a number from 1/2 to 2 that the genome expresses like the policy and that a child inherits with mutation. Mass is what a body is made of (a child costs its mass times 0.02; a broken or dead block gives back the same), what it moves with (the work of moving is mass times distance, speed is muscle over mass, a shove needs more muscle than the shoved body's mass) and what its faces resist with (hardness times density: light armor is weak armor). The upkeep, the bite and the sight stay per block. Two bodies of eight cells: the light one is fast, cheap and soft; the heavy one slow, dear and hard.</figcaption>
</figure>
"""


def read_frames(path, folder=HERE):
    with open(os.path.join(folder, path)) as f:
        for line in f:
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                return  # a run still writing ends mid-line


def load_bodies(run, folder=HERE):
    out = {}
    with open(os.path.join(folder, f"results/{run}_bodies.jsonl")) as f:
        for line in f:
            try:
                d = json.loads(line)
            except json.JSONDecodeError:
                break  # a run still writing ends mid-line
            out[d["id"]] = d["cells"]
    return out


def pack_frames(path, confirmed_at, data, every=1, limit=None):
    """Frames packed small into `data`: food as 4-bit nibbles; agents as x, y (sub-cells, 2 bytes each), body id (3 bytes), lineage (2 bytes), facing (1 byte).
    Returns one index entry per frame (step, patches, offsets and lengths into `data`).
    A lineage id is written only once the lineage is confirmed (else 0)."""
    out = []
    used = set()
    n = 0
    for i, fr in enumerate(read_frames(path)):
        if i % every:
            continue
        food = fr["food"]
        nib = bytes((food[j] << 4) | food[j + 1] for j in range(0, len(food), 2))
        soil = fr.get("soil", [])
        snib = bytes((soil[j] << 4) | soil[j + 1] for j in range(0, len(soil), 2))
        ag = bytearray()
        for x, y, b, _d, lin, f in fr["agents"]:
            lin = lin if confirmed_at.get(lin, 10**12) <= fr["step"] else 0
            ag += bytes((x & 255, x >> 8, y & 255, y >> 8, b & 255, (b >> 8) & 255, b >> 16, lin & 255, lin >> 8, f))  # 3-byte body id: a run can have 100,000+ distinct (damaged) bodies
            used.add(b)
        out.append({"s": fr["step"], "p": fr["patches"], "fo": len(data), "fl": len(nib), "so": len(data) + len(nib), "sl": len(snib), "ao": len(data) + len(nib) + len(snib), "al": len(ag)})
        data += nib
        data += snib
        data += ag
        n += 1
        if limit and n >= limit:
            break
    return out, used


VIEWER_JS = r"""
(async function(){
  // One gzip'd blob: 4-byte header length, JSON header, then the frame bytes (a 256x256 world is 50 KB per frame raw).
  const raw = Uint8Array.from(atob(document.getElementById('frames').textContent), c => c.charCodeAt(0));
  const all = new Uint8Array(await new Response(new Blob([raw]).stream().pipeThrough(new DecompressionStream('gzip'))).arrayBuffer());
  const hlen = all[0] | (all[1] << 8) | (all[2] << 16) | (all[3] << 24);
  const data = JSON.parse(new TextDecoder().decode(all.subarray(4, 4 + hlen)));
  const bytes = all.subarray(4 + hlen);
  const bodies = data.bodies, KC = data.kindColors, PAL = data.palette, NONE = data.none;
  const terr = data.tl ? bytes.subarray(data.to, data.to + data.tl) : null; // the terrain, 16 levels, once
  const cv = document.getElementById('world'), ctx = cv.getContext('2d');
  const zv = document.getElementById('zoom'), zctx = zv.getContext('2d');
  // W x H world cells of food; SW x SH sub-cells (4 per cell) where the bodies are. S: pixels per sub-cell on the world; ZN world cells in the zoom.
  const SUB = 4, W = data.w, H = data.h, SW = W * SUB, SH = H * SUB, S = cv.width / SW, ZN = 24, ZS = zv.width / (ZN * SUB), REC = 10;
  const off = document.createElement('canvas'); off.width = W; off.height = H;
  const octx = off.getContext('2d'), img = octx.createImageData(W, H);
  ctx.imageSmoothingEnabled = false; zctx.imageSmoothingEnabled = false;
  const slider = document.getElementById('scrub'), stepLbl = document.getElementById('steplbl'), linLbl = document.getElementById('linlbl');
  const playBtn = document.getElementById('play'), mode = document.getElementById('mode'), layer = document.getElementById('layer');
  let frames = data.long, i = 0, timer = null, zx = (SW / 2 - ZN * SUB / 2) | 0, zy = (SH / 2 - ZN * SUB / 2) | 0;
  const stats = {}, rotated = {};
  function color(lin){ return lin ? PAL[data.slots[lin] || 0] : NONE; }
  // The body grid in the world frame: the front row (row 0) turned to point where the body faces (0 north, 1 south, 2 east, 3 west).
  function toWorld(k, f){ const r = k >> 3, c = k & 7, m = 7; let r2, c2;
    if (f === 0) { r2 = r; c2 = c; } else if (f === 1) { r2 = m - r; c2 = m - c; } else if (f === 2) { r2 = c; c2 = m - r; } else { r2 = m - c; c2 = r; }
    return r2 * 8 + c2; }
  // The cells a body holds in the world frame, as [column, row, kind] triples, and their bounding box.
  function rot(id, f){ const key = id + ':' + f; if (rotated[key]) return rotated[key];
    const cells = bodies[id] || '', out = [], bb = [8, -1, 8, -1];
    for (let k = 0; k < 64; k++) { const v = cells.charCodeAt(k) - 48; if (v > 0) { const w = toWorld(k, f), r = w >> 3, c = w & 7; out.push([c, r, v]);
      bb[0] = Math.min(bb[0], r); bb[1] = Math.max(bb[1], r); bb[2] = Math.min(bb[2], c); bb[3] = Math.max(bb[3], c); } }
    return rotated[key] = { cells: out, bb: bb }; }
  // Same rules as the simulation, in the body frame: per side, per line, the tip is the outermost cell; a hard tip has hardness 3 per
  // contiguous hard cell; force is the muscle in the line. Bite = largest force behind a hard tip on the front (side 0); shell = mean
  // hardness of touchable tips; extent = rows and columns the body spans.
  function stat(id){
    if (stats[id]) return stats[id];
    const cells = bodies[id] || ''; let mass = 0, sensor = 0, bite = 0, hsum = 0, hn = 0, r0 = 8, r1 = -1, c0 = 8, c1 = -1;
    for (let k = 0; k < 64; k++) { const v = cells.charCodeAt(k) - 48; if (v > 0) { mass++; r0 = Math.min(r0, k >> 3); r1 = Math.max(r1, k >> 3); c0 = Math.min(c0, k & 7); c1 = Math.max(c1, k & 7); } if (v === 3) sensor++; }
    const at = (side, line, k) => side === 0 ? k * 8 + line : side === 1 ? (7 - k) * 8 + line : side === 2 ? line * 8 + (7 - k) : line * 8 + k;
    for (let side = 0; side < 4; side++) for (let line = 0; line < 8; line++) {
      let force = 0, k0 = -1;
      for (let k = 0; k < 8; k++) { const v = cells.charCodeAt(at(side, line, k)) - 48; if (v === 2) force++; if (v > 0 && k0 < 0) k0 = k; }
      if (k0 < 0) continue;
      let h = 1;
      if (cells.charCodeAt(at(side, line, k0)) - 48 === 1) { h = 0; for (let k = k0; k < 8 && cells.charCodeAt(at(side, line, k)) - 48 === 1; k++) h += 3; }
      hsum += h; hn++;
      if (side === 0 && h > 1 && force > bite) bite = force;
    }
    return stats[id] = { mass: mass, bite: bite, shell: hn ? hsum / hn : 0, sensor: sensor, fwd: mass ? r1 - r0 + 1 : 0, side: mass ? c1 - c0 + 1 : 0 };
  }
  function foodAt(food, c){ return (c % 2 === 0) ? (food[c >> 1] >> 4) : (food[c >> 1] & 15); }
  // The ground: food in green, soil (the long view only) in brown, on their own scales (food: square root of the cap; soil: log).
  let soilLayer = false, terrLayer = false;
  function tint(v){ const g = 40 + v * 12; return terrLayer ? [g * 0.55 | 0, g * 0.6 | 0, g * 0.72 | 0] : soilLayer ? [g * 0.9 | 0, g * 0.6 | 0, g * 0.25 | 0] : [g * 0.35 | 0, g, g * 0.45 | 0]; }
  function paintFood(target, food, x0, y0, n, cell){ // x0, y0: the zoom's corner in sub-cells; cell: pixels per world cell
    const wx = Math.floor(x0 / SUB), wy = Math.floor(y0 / SUB), ox = (x0 % SUB) * cell / SUB, oy = (y0 % SUB) * cell / SUB;
    for (let y = 0; y <= n; y++) for (let x = 0; x <= n; x++) {
      const c = ((wy + y) % H) * W + ((wx + x) % W);
      const t = tint(foodAt(food, c));
      target.fillStyle = 'rgb(' + t[0] + ',' + t[1] + ',' + t[2] + ')';
      target.fillRect(x * cell - ox, y * cell - oy, cell, cell);
    }
  }
  // Each patch as a ring of radius 2 sigma around its center (on the torus: drawn up to 4 times when it wraps). Wide: blue; narrow: aqua.
  function paintPatches(fr){
    const CS = S * SUB;
    for (const [px, py, sg] of fr.p) {
      if (sg <= 0) continue; // a uniform sun has no patches
      ctx.strokeStyle = sg >= 4 ? '#2a78d6' : '#1baf7a'; ctx.lineWidth = 1.5; ctx.setLineDash([4, 4]);
      const r = Math.max(2 * sg, 1.5) * CS;
      for (const ox of [0, -W, W]) for (const oy of [0, -H, H]) {
        const cx = (px + 0.5 + ox) * CS, cy = (py + 0.5 + oy) * CS;
        if (cx + r < 0 || cy + r < 0 || cx - r > cv.width || cy - r > cv.height) continue;
        ctx.beginPath(); ctx.arc(cx, cy, r, 0, 2 * Math.PI); ctx.stroke();
      }
      ctx.setLineDash([]);
    }
  }
  function draw(){
    const fr = frames[i]; soilLayer = layer.value === 'soil' && fr.sl > 0; terrLayer = layer.value === 'terrain' && !!terr;
    const food = terrLayer ? terr : soilLayer ? bytes.subarray(fr.so, fr.so + fr.sl) : bytes.subarray(fr.fo, fr.fo + fr.fl), ag = bytes.subarray(fr.ao, fr.ao + fr.al);
    const px = img.data;
    for (let c = 0; c < W * H; c++) {
      const t = tint(foodAt(food, c));
      px[c * 4] = t[0]; px[c * 4 + 1] = t[1]; px[c * 4 + 2] = t[2]; px[c * 4 + 3] = 255;
    }
    octx.putImageData(img, 0, 0);
    ctx.drawImage(off, 0, 0, cv.width, cv.height);
    paintFood(zctx, food, zx, zy, ZN, ZS * SUB);
    const counts = {}, teeth = {}, armor = {}, eyes = {}, masses = {}, fwd = {}, side = {}; let n = 0;
    const inZoom = [], ZW = ZN * SUB;
    for (let k = 0; k < ag.length; k += REC) {
      const x = ag[k] | (ag[k + 1] << 8), y = ag[k + 2] | (ag[k + 3] << 8), id = ag[k + 4] | (ag[k + 5] << 8) | (ag[k + 6] << 16), lin = ag[k + 7] | (ag[k + 8] << 8), f = ag[k + 9];
      const st = stat(id), body = rot(id, f);
      ctx.fillStyle = color(lin);
      for (const [c, r] of body.cells) ctx.fillRect(((x + c) % SW) * S, ((y + r) % SH) * S, S, S);
      if (st.bite > 0) { ctx.fillStyle = '#fff'; const bb = body.bb; ctx.fillRect(((x + (bb[2] + bb[3]) / 2) % SW) * S - 1, ((y + (bb[0] + bb[1]) / 2) % SH) * S - 1, 2, 2); }
      const dx = (x - zx + SW) % SW, dy = (y - zy + SH) % SH;
      if (dx < ZW + 8 && dy < ZW + 8) inZoom.push([dx, dy, id, lin, f, st, body]);
      counts[lin] = (counts[lin] || 0) + 1; teeth[lin] = (teeth[lin] || 0) + st.bite; armor[lin] = (armor[lin] || 0) + st.shell; eyes[lin] = (eyes[lin] || 0) + st.sensor; masses[lin] = (masses[lin] || 0) + st.mass; fwd[lin] = (fwd[lin] || 0) + st.fwd; side[lin] = (side[lin] || 0) + st.side; n++;
    }
    // The zoom: each cell of a body on its sub-cell, the block kind inside a frame of the lineage color, a white edge on the front of the body's box.
    for (const [dx, dy, id, lin, f, st, body] of inZoom) {
      for (const [c, r, v] of body.cells) { zctx.fillStyle = color(lin); zctx.fillRect((dx + c) * ZS, (dy + r) * ZS, ZS, ZS); zctx.fillStyle = KC[v]; zctx.fillRect((dx + c) * ZS + 1, (dy + r) * ZS + 1, ZS - 2, ZS - 2); }
      const bb = body.bb, x0 = (dx + bb[2]) * ZS, y0 = (dy + bb[0]) * ZS, LW = (bb[3] - bb[2] + 1) * ZS, LH = (bb[1] - bb[0] + 1) * ZS;
      zctx.fillStyle = '#fff';
      if (f === 0) zctx.fillRect(x0, y0, LW, 2); else if (f === 1) zctx.fillRect(x0, y0 + LH - 2, LW, 2); else if (f === 2) zctx.fillRect(x0 + LW - 2, y0, 2, LH); else zctx.fillRect(x0, y0, 2, LH);
      if (st.bite > 0) { const cx = x0 + LW / 2, cy = y0 + LH / 2; zctx.fillRect(cx - 2, cy - 2, 4, 4); }
    }
    paintPatches(fr);
    zctx.strokeStyle = 'rgba(255,255,255,0.35)'; zctx.lineWidth = 1;
    const ox = (zx % SUB) * ZS, oy = (zy % SUB) * ZS;
    for (let k = 0; k <= ZN; k++) { zctx.beginPath(); zctx.moveTo(k * ZS * SUB - ox, 0); zctx.lineTo(k * ZS * SUB - ox, zv.height); zctx.stroke(); zctx.beginPath(); zctx.moveTo(0, k * ZS * SUB - oy); zctx.lineTo(zv.width, k * ZS * SUB - oy); zctx.stroke(); }
    ctx.strokeStyle = '#fff'; ctx.lineWidth = 1.5; ctx.strokeRect(zx * S, zy * S, ZW * S, ZW * S);
    stepLbl.textContent = 'step ' + fr.s.toLocaleString() + ' - ' + n + ' agents';
    const keys = Object.keys(counts).map(Number).sort((a, b) => counts[b] - counts[a]).slice(0, 12);
    linLbl.innerHTML = keys.map(l => '<span class="lin" style="background:' + color(l) + '">' + (l ? 'lineage ' + l : 'none') + ': ' + counts[l]
      + ' (mass ' + (masses[l] / counts[l]).toFixed(0) + ', ' + (fwd[l] / counts[l]).toFixed(1) + ' long x ' + (side[l] / counts[l]).toFixed(1) + ' wide, bite ' + (teeth[l] / counts[l]).toFixed(1) + ', shell ' + (armor[l] / counts[l]).toFixed(1) + ', eyes ' + (eyes[l] / counts[l]).toFixed(1) + ')</span>').join('');
  }
  function densest(){ // start the zoom where the agents are, not in the desert
    const ag = bytes.subarray(frames[0].ao, frames[0].ao + frames[0].al); const n = {}, ZW = ZN * SUB;
    for (let k = 0; k < ag.length; k += REC) { const x = ag[k] | (ag[k + 1] << 8), y = ag[k + 2] | (ag[k + 3] << 8); const key = ((x / ZW) | 0) + ',' + ((y / ZW) | 0); n[key] = (n[key] || 0) + 1; }
    const best = Object.keys(n).sort((a, b) => n[b] - n[a])[0]; if (!best) return;
    zx = +best.split(',')[0] * ZW; zy = +best.split(',')[1] * ZW;
  }
  function setMode(){ frames = data[mode.value]; i = 0; slider.max = frames.length - 1; densest(); draw(); }
  function tick(){ i = (i + 1) % frames.length; draw(); }
  const speed = document.getElementById('speed');
  function interval(){ return (mode.value === 'clip' ? 250 : 600) / +speed.value; }
  playBtn.onclick = function(){ if (timer) { clearInterval(timer); timer = null; playBtn.textContent = 'Play'; } else { timer = setInterval(tick, interval()); playBtn.textContent = 'Pause'; } };
  speed.onchange = function(){ if (timer) { clearInterval(timer); timer = setInterval(tick, interval()); } };
  slider.oninput = function(){ i = +slider.value; draw(); };
  mode.onchange = function(){ if (timer) playBtn.onclick(); setMode(); };
  layer.onchange = draw;
  cv.onclick = function(e){ const r = cv.getBoundingClientRect(); const ZW = ZN * SUB; zx = (Math.floor((e.clientX - r.left) / r.width * SW - ZW / 2) + SW) % SW; zy = (Math.floor((e.clientY - r.top) / r.height * SH - ZW / 2) + SH) % SH; draw(); };
  setMode();
})();
"""


def gallery(picks):
    """picks: [(world, seed, lineage id, name, what the shape does[, step])]. The most common body of each lineage at its peak (or at
    the step given), on the 8x8 grid, front up."""
    cards = []
    cache = {}
    for world, seed, lid, name, what, *at in picks:
        if world not in WORLDS or seed not in seeds_of(world):  # a dry run on a few seeds
            continue
        run = f"{WORLDS[world]['run']}_seed{seed}"
        if run not in cache:
            cache[run] = (lineage_rows(run), load_bodies(run), list(read_frames(f"results/{run}_long.jsonl")))
        by, bodies, frames = cache[run]
        rows = by[lid]
        peak = max(rows, key=lambda r: int(r["size"])) if not at else min(rows, key=lambda r: abs(int(r["step"]) - at[0]))
        span = int(rows[-1]["step"]) - int(rows[0]["step"]) + CONFIRM_STEPS
        frame = min((fr for fr in frames if any(a[4] == lid for a in fr["agents"])), key=lambda fr: abs(fr["step"] - int(peak["step"])))  # the nearest frame that has the lineage
        c = Counter(a[2] for a in frame["agents"] if a[4] == lid)
        cells = bodies[c.most_common(1)[0][0]]
        rects = "".join(f'<rect x="{(i % 8) * 11}" y="{(i // 8) * 11}" width="10" height="10" fill="{KIND_COLOR[int(k)]}"/>' for i, k in enumerate(cells) if k != "0")
        m, pl = float(peak["meat"]), float(peak["plant"])
        meat = m / (m + pl) if m + pl > 0 else 0
        at = [sum(int(r[k]) for r in rows) for k in ("p0", "p1", "pnone")]
        first = WORLDS[world]["places"][0][1].split(" (")[0] if WORLDS[world]["places"] else "the world"
        home = f"{at[0] / max(sum(at), 1):.0%} in the {first}" if WORLDS[world]["places"] else "a flat world"
        height = f", at height {float(peak['height']):.0f}" if "height" in peak and WORLDS[world]["uniform"] and WORLDS[world]["places"] else ""
        cards.append(f"""<figure class="card"><svg viewBox="-1 -1 89 89" width="120" height="120" role="img" aria-label="{html.escape(name)}"><rect x="-1" y="-1" width="89" height="89" fill="var(--cell)"/>{rects}<line x1="-1" y1="-0.5" x2="88" y2="-0.5" stroke="var(--ink2)" stroke-width="1.5" stroke-dasharray="3 2"/></svg>
<figcaption><strong>{html.escape(name)}</strong><br>{html.escape(world)}, seed {seed}, lineage {lid}: {span:,} steps, {int(peak["size"]):,} agents at {"step " + format(int(peak["step"]), ",") if at else "its peak"}, {home}{height}<br>mass {float(peak["mass"]):.0f} on {float(peak["foot"]):.1f} cells: hard {float(peak["hard"]):.0f}, muscle {float(peak["muscle"]):.0f}, sensor {float(peak["sensor"]):.1f}, digestive {float(peak["digestive"]):.0f}{", density " + format(float(peak["density"]), ".2f") if "density" in peak else ""}; dead matter {meat:.0%} of the intake<br>{html.escape(what)}</figcaption></figure>""")
    return f"""<figure class="diagram"><div class="cards">{"".join(cards)}</div>
<figcaption>Figure 2. Bodies of lineages that prospered: the most common body of the lineage at its peak (or at the step named), on the 8x8 grid a body grows on, front up (the dashed edge). Blue: hard, orange: muscle, green: digestive, yellow: sensor. "Cells" is the world cells the body covers; "dead matter" the share of the lineage's lifetime intake that was dead bodies; the height is the terrain under the lineage's members at its peak (relief 64). Sensor is the mean per body: the range is one cell plus that.</figcaption></figure>"""


def top_lineages():
    """Print the longest-lived lineages of every run, for the gallery."""
    for w, d in WORLDS.items():
        for s in seeds_of(w):
            run = f"{d['run']}_seed{s}"
            try:
                by = lineage_rows(run)
            except FileNotFoundError:
                continue
            out = []
            for lid, rows in by.items():
                peak = max(rows, key=lambda r: int(r["size"]))
                span = int(rows[-1]["step"]) - int(rows[0]["step"]) + CONFIRM_STEPS
                out.append((span, lid, peak))
            out.sort(reverse=True)
            print(f"{w}, seed {s}")
            for span, lid, r in out[:4]:
                print(f"  lineage {lid}: {span:,} steps ({r['step']} peak), {r['size']} agents, mass {r['mass']}, hard {r['hard']}, muscle {r['muscle']}, dig {r['digestive']}, "
                      f"foot {r['foot']}, {r['len_fwd']}x{r['len_side']}, bite {r['bite']}, meat {r['meat']}/{r['plant']}, p0 {r['p0']} p1 {r['p1']} pnone {r['pnone']}, height {r.get('height', '-')}")



def sensor_lineages(run, folder=HERE):
    """(steps, peak size, lineage id, mean sensors at the peak) of every lineage whose bodies carry a sensor on
    average (sensor >= 1 in a row of the lineage log), by the steps it spent that way."""
    out = []
    for lid, rows in lineage_rows(run, folder).items():
        eyed = [r for r in rows if float(r["sensor"]) >= 1.0]
        if not eyed:
            continue
        peak = max(eyed, key=lambda r: int(r["size"]))
        out.append((len(eyed) * 1000, int(peak["size"]), lid, float(peak["sensor"])))
    out.sort(reverse=True)
    return out


def main():
    logs, events = {}, {}
    for w, d in WORLDS.items():
        logs[w] = {s: load_csv(f"results/{d['run']}_seed{s}_log.csv") for s in seeds_of(w)}
        events[w] = {s: load_rows(f"results/{d['run']}_seed{s}_events.csv") for s in seeds_of(w)}
    for w, (run, folder, _) in REFS.items():
        # e023's runs went to 1,000,000 steps; the comparison is over the same span as these runs.
        logs[w] = {s: {k: v[:LAST_STEP // 10_000] for k, v in load_csv(f"results/{run}_seed{s}_log.csv", folder).items()} for s in seeds_of(w)}
    run_of = lambda w, s: (f"{WORLDS[w]['run']}_seed{s}", HERE) if w in WORLDS else (f"{REFS[w][0]}_seed{s}", REFS[w][1])
    all_worlds = list(WORLDS) + list(REFS)

    def med(x):
        x = [v for v in x if v == v]
        return statistics.median(x) if x else float("nan")

    def half(d, key):
        n = len(d["step"])
        return d[key][n // 2:]

    def eaten_of(d):
        return [(p + m) / 10_000 for p, m in zip(d["plant_intake"], d["meat_intake"])]

    def summarize(w, s):
        log = logs[w][s]
        run, folder = run_of(w, s)
        first, last, _ = lineage_stats(run, folder)
        per_step = Counter(int(r["step"]) for r in load_rows(f"results/{run}_lineages.csv", folder))
        last_step = int(log["step"][-1])
        pop = half(log, "pop")
        eaten = eaten_of(log)
        n = len(eaten)
        eyed = sensor_lineages(run, folder)
        hunters = hunter_lineages(run, folder, min_bite=1.0)
        q = len(log["step"]) * 3 // 4
        worth = log["worth"] if "worth" in log else [e / max(m, 1e-9) + CELL_ENERGY for e, m in zip(log["mean_energy"], log["mass_mean"])]
        broken = [b / 10_000 for b in log["cells_broken"]]
        d = dict(worth=med(worth[len(worth) // 2:]), worth_max=max(worth), kill_gain=med(half(log, "kill_gain")) if "kill_gain" in log else float("nan"),
                 fat=med(half(log, "fat_mean")) if "fat_mean" in log else 0.0, fat_share=med([f / m for f, m in zip(half(log, "fat_stock"), half(log, "matter"))]) if "fat_stock" in log else 0.0,
                 broken=med(broken[len(broken) // 2:]), kills=med([k / 10_000 for k in half(log, "deaths_broken")]),
                 kill_share=med([k / max(k + e + a, 1) for k, e, a in zip(half(log, "deaths_broken"), half(log, "deaths_energy"), half(log, "deaths_age"))]),
                 biters_q4=med(log["biters_share"][q:]), hunter_steps=hunters[0]["span"] if hunters else 0, hunter_diet=hunters[0]["diet"] if hunters else float("nan"),
                 hunter_100k=sum(1 for h in hunters if h["span"] >= 100_000), hunters=len(hunters), age=med(half(log, "prey_age_mean")),pop=med(pop), pop_cv=statistics.pstdev(pop) / max(statistics.mean(pop), 1), pop_swing=max(pop) / max(min(pop), 1),
                 extinct=last_step < LAST_STEP, extinct_at=last_step if last_step < LAST_STEP else float("nan"), sps=med(log["steps_per_sec"]),
                 lineages=med([per_step.get(t, 0) for t in range(1000, last_step + 1, 1000)]), ids=len(first),
                 contacts=med([c / max(p, 1) / 10_000 for c, p in zip(half(log, "contacts"), pop)]), forward=med(half(log, "forward")),
                 mass=med(half(log, "mass_mean")), hard=med(half(log, "hard_mean")), muscle=med(half(log, "muscle_mean")), foot=med(half(log, "foot_mean")),
                 size=med(half(log, "size_mean")) if "size_mean" in log else med(half(log, "mass_mean")), speed=med(half(log, "speed_mean")),
                 density=med(half(log, "density_mean")) if "density_mean" in log else 1.0, density_std=med(half(log, "density_std")) if "density_std" in log else 0.0,
                 eaten=med(eaten[n // 2:]), steady=med(eaten[3 * n // 4:]) / max(med(eaten[n // 2: 3 * n // 4]), 1e-9),
                 matter_hold=log["matter"][-1] / log["matter"][0],
                 trees=med(half(log, "trees")), biters=med(half(log, "biters_share")), biters_max=max(log["biters_share"]),
                 fruit_share=med([f / max(e, 1e-9) for f, e in zip(half(log, "fruit_eaten"), eaten[n // 2:])]),
                 meat_share=med([m / max(p_ + m, 1e-9) for p_, m in zip(half(log, "plant_intake"), half(log, "meat_intake"))]),
                 sensor_share=med(half(log, "sensor_agents_share")), sensor_share_max=max(log["sensor_agents_share"]),
                 sensor_mean=med(half(log, "sensor_mean")), sensor_mean_max=max(log["sensor_mean"]),
                 sense_used=med(half(log, "sense_used")), sense_decisions=med([sd / max(p, 1) / 10_000 for sd, p in zip(half(log, "sense_decisions"), pop)]),
                 eyed_steps=eyed[0][0] if eyed else 0, eyed_peak=eyed[0][1] if eyed else 0, eyed_lineages=len(eyed),
                 eyed_100k=sum(1 for e in eyed if e[0] >= 100_000))
        return d

    S = {w: {s: summarize(w, s) for s in seeds_of(w)} for w in all_worlds}
    if os.environ.get("EVLOG_PRINT"):
        for w in all_worlds:
            for s_ in seeds_of(w):
                print(w, s_, {k: (round(v, 3) if isinstance(v, float) else v) for k, v in S[w][s_].items()})

    charts = {}
    worth_of = lambda l: l["worth"] if "worth" in l else [e / max(m, 1e-9) + CELL_ENERGY for e, m in zip(l["mean_energy"], l["mass_mean"])]
    charts["worth"] = world_chart("What a cell of a body is worth", "What one cell yields to whoever breaks it (its matter 0.02, plus its share of the body's energy and fat), mean over the bodies alive, one line per run; gray: e023 (from mean energy and mass). A bite of grass is 0.02: the dotted line.", logs, worth_of, all_worlds, WORLD_COLOR, ymin=0, hline=BITE)
    charts["kill_gain"] = world_chart("What a kill paid", "Energy gained per cell broken by a push, per log window, one line per run (e023 did not log it). Above the cells' mean worth means old bodies are the ones broken; below, newborns.", logs, lambda l: l["kill_gain"] if "kill_gain" in l else None, all_worlds, WORLD_COLOR, hline=BITE)
    charts["meat_share"] = world_chart("Intake from other bodies", "Share of the food eaten that was another body, broken or dead, per log window, one line per run; gray: e023 (5-18%).", logs, lambda l: [m / max(p + m, 1e-9) for p, m in zip(l["plant_intake"], l["meat_intake"])], all_worlds, WORLD_COLOR, percent=True)
    charts["broken"] = world_chart("Cells broken per step", "Cells of living bodies broken by a push, per step, one line per run; gray: e023. Zero would be a world without teeth.", logs, lambda l: [b / 10_000 for b in l["cells_broken"]], all_worlds, WORLD_COLOR)
    charts["fat_share"] = world_chart("Fat, share of the world's matter", "The matter fixed in living bodies' flesh over all the matter of the world, at each log step, one line per run. What it holds is not in the air, so not in the rain.", logs, lambda l: [f / m for f, m in zip(l["fat_stock"], l["matter"])] if "fat_stock" in l else None, all_worlds, WORLD_COLOR, percent=True)
    pilot = pilot_table()
    charts["sensor_mean"] = world_chart("Sensor blocks per body", "Mean sensor blocks per body alive, one line per run; gray: e022. With the eye a body's range is one cell plus this.", logs, lambda l: l["sensor_mean"], all_worlds, WORLD_COLOR)
    charts["sense_used"] = world_chart("The knockout: decisions the eye changed", "Of the decisions taken by bodies with a sensor, the share that would differ if the body saw one cell, per log window, one line per run; gray: e022 (there: if the second cell were not seen). Zero would be an eye nobody reads.", logs, lambda l: l["sense_used"], all_worlds, WORLD_COLOR, percent=True)
    charts["pop"] = world_chart("Population", "Bodies alive at each log step, one line per run; gray: e022. A line that ends is a world that died.", logs, lambda l: l["pop"], all_worlds, WORLD_COLOR)
    charts["eaten"] = world_chart("Food eaten per step", "Plant, fruit and dead matter taken by guts per step, one line per run; gray: e022. The sun gives 164 per step.", logs, eaten_of, all_worlds, WORLD_COLOR)
    charts["fruit_share"] = world_chart("Intake from fruit", "Share of the food eaten that was fruit lying on the rings, per log window, one line per run; gray: e022 (44-77% in its crowd state).", logs, lambda l: [f / max(e, 1e-9) for f, e in zip(l["fruit_eaten"], eaten_of(l))], all_worlds, WORLD_COLOR, percent=True, ymax=1.0)
    charts["contacts"] = world_chart("Contacts per body per step", "Pairs of bodies whose cells touched, per body per step, one line per run; gray: e022 (0.22-0.76 in the crowd state).", logs, lambda l: [c / max(p, 1) / 10_000 for c, p in zip(l["contacts"], l["pop"])], all_worlds, WORLD_COLOR)
    charts["biters"] = world_chart("Bodies with a bite", "Share of the bodies with a hard tip on the front backed by muscle, at each log step, one line per run; gray: e022 (peaks of 0.01-0.03, never kept).", logs, lambda l: l["biters_share"], all_worlds, WORLD_COLOR, percent=True)
    charts["lineages"] = world_chart("Lineages alive", "Confirmed lineages at each log step, one line per run; gray: e022 (1-3).", logs, lambda l: l["lineages"], all_worlds, WORLD_COLOR)
    charts["mass"] = world_chart("Mass per body", "Mean mass of the bodies alive (the sum of the blocks' weights times the density), one line per run; gray: e024 (there mass is the count of cells).", logs, lambda l: l["mass_mean"], all_worlds, WORLD_COLOR)
    charts["size"] = world_chart("Cells per body", "Mean cells per body alive, one line per run; gray: e024. Mass over cells is what the body is made of.", logs, lambda l: l["size_mean"] if "size_mean" in l else l["mass_mean"], all_worlds, WORLD_COLOR)
    charts["density"] = world_chart("Density per body", "Mean density of the bodies alive (what the genome expresses, 1/2 to 2), one line per run; gray: e024 (1 by law). The dotted line is 1.", logs, lambda l: l["density_mean"] if "density_mean" in l else [1.0] * len(l["step"]), all_worlds, WORLD_COLOR, ymin=0.4, ymax=2.1, hline=1.0)
    charts["density_std"] = world_chart("Spread of the density", "Standard deviation of the density over the bodies alive, one line per run (e024: 0). Zero would be one density for the whole world.", logs, lambda l: l["density_std"] if "density_std" in l else [0.0] * len(l["step"]), all_worlds, WORLD_COLOR, ymin=0)
    charts["speed"] = world_chart("Speed per body", "Mean muscle blocks over mass (the chance of a second sub-cell per move), one line per run; gray: e024.", logs, lambda l: l["speed_mean"], all_worlds, WORLD_COLOR, ymin=0)
    charts["hard"] = world_chart("Hard blocks per body", "Mean hard blocks per body alive (each weighs 2 now), one line per run; gray: e024.", logs, lambda l: l["hard_mean"], all_worlds, WORLD_COLOR, ymin=0)
    charts["matter"] = world_chart("The world's matter", "All the matter of the world (soil, ground, bodies, air) at each log step over what it was at the start, one line per run; gray: e024 (the leaking ledger).", logs, lambda l: [m / l["matter"][0] for m in l["matter"]], all_worlds, WORLD_COLOR, ymin=0.975, ymax=1.005, hline=1.0)
    charts["kills"] = world_chart("Bodies killed per step", "Bodies whose last cell a push broke, per step, one line per run; gray: e024 (3.95 in its hunter run, 0 elsewhere).", logs, lambda l: [k / 10_000 for k in l["deaths_broken"]], all_worlds, WORLD_COLOR, ymin=0)

    vseed = VIEWER_SEED if VIEWER_SEED in events[VIEWER_WORLD] else seeds_of(VIEWER_WORLD)[0]  # a dry run may lack the viewer's seed
    viewer_run = f"{WORLDS[VIEWER_WORLD]['run']}_seed{vseed}"
    timeline = timeline_chart(f"Lineages over time ({VIEWER_WORLD}, seed {vseed})", "Each colored band is one lineage, height = agents in it; marks are events at the size they were logged with.", viewer_run, events[VIEWER_WORLD][vseed])

    first, _, _ = lineage_stats(viewer_run)
    bodies = load_bodies(viewer_run)
    data = bytearray()
    long_frames, used_l = pack_frames(f"results/{viewer_run}_long.jsonl", first, data, every=2)
    clip_frames, used_c = pack_frames(f"results/{viewer_run}_clip.jsonl", first, data, every=4, limit=50)
    heights = terrain_of(viewer_run)["height"]
    hmax = max(heights) or 1
    tq = [min(15, round(h / hmax * 15)) for h in heights]
    tnib = bytes((tq[j] << 4) | tq[j + 1] for j in range(0, len(tq), 2))
    legend = " ".join(f'<span class="sw" style="background:{KIND_COLOR[k]}"></span>{name}' for k, name in ((1, "hard"), (2, "muscle"), (3, "sensor"), (4, "digestive")))
    vw = WORLDS[VIEWER_WORLD]["size"]
    viewer_data = {"w": vw, "h": vw, "long": long_frames, "clip": clip_frames, "bodies": {str(b): bodies.get(b, "0" * 64) for b in used_l | used_c},
                   "kindColors": {str(k): v for k, v in KIND_COLOR.items()}, "palette": LINEAGE_PALETTE, "none": NONE_COLOR,
                   "slots": {str(k): v for k, v in color_slots(viewer_run).items()}, "to": len(data), "tl": len(tnib)}
    data += tnib
    header = json.dumps(viewer_data, separators=(",", ":")).encode()
    blob = base64.b64encode(gzip.compress(len(header).to_bytes(4, "little") + header + bytes(data), 9)).decode()

    def rng(w, key, fmt):
        vals = [S[w][s].get(key, float("nan")) for s in seeds_of(w) if key == "extinct_at" or not S[w][s]["extinct"]]
        vals = [v for v in vals if v == v]
        if not vals:
            return "-"
        lo, hi = min(vals), max(vals)
        return fmt(lo) if fmt(lo) == fmt(hi) else f"{fmt(lo)}-{fmt(hi)}"

    def row(label, keys, fmt):
        return f"<tr><td>{label}</td>" + "".join("<td>" + " / ".join(rng(w, k, fmt) for k in keys.split("|")) + "</td>" for w in all_worlds) + "</tr>"

    n0 = lambda v: f"{v:,.0f}"
    d1 = lambda v: f"{v:.1f}"
    d2 = lambda v: f"{v:.2f}"
    d3 = lambda v: f"{v:.3f}"
    p0 = lambda v: f"{v:.0%}"
    p1 = lambda v: f"{v:.1%}"
    summary = ("<thead><tr><th>Measure (range over seeds, median over the second half unless said)</th>" + "".join(f"<th>{w}</th>" for w in all_worlds) + "</tr></thead><tbody>"
               + row("Density per body (mean); its spread over bodies", "density|density_std", d2)
               + row("Cells per body; mass", "size|mass", d1)
               + row("Speed (muscle over mass)", "speed", d3)
               + row("Hard; muscle blocks per body", "hard|muscle", d2)
               + row("What a cell of a body is worth (a bite of grass is 0.02)", "worth", d3)
               + row("What a kill paid per cell broken", "kill_gain", d3)
               + row("Fat, share of the world's matter", "fat_share", p0)
               + row("Intake from other bodies, share of the food eaten", "meat_share", p0)
               + row("Cells broken per step; bodies killed per step", "broken|kills", d2)
               + row("Deaths by a push, share of all deaths", "kill_share", p1)
               + row("Bodies with a bite, share (median / last quarter / peak)", "biters|biters_q4|biters_max", d3)
               + row("Longest lineage with a bite of 1 or more, steps", "hunter_steps", n0)
               + row("Its intake from other bodies", "hunter_diet", p0)
               + row("Lineages with a bite for 100,000 steps or more", "hunter_100k", n0)
               + row("Population (coefficient of variation)", "pop|pop_cv", lambda v: f"{v:,.0f}" if v >= 1 else f"{v:.2f}")
               + row("Food eaten per step", "eaten", d1)
               + row("Intake from fruit, share of the food eaten", "fruit_share", p0)
               + row("Contacts per body per step", "contacts", d2)
               + row("Lineages alive", "lineages", d1)
               + row("Matter at the end over the start", "matter_hold", lambda v: f"{v:.5f}")
               + "</tbody>")

    tables = data_table(["step", "pop", "births", "deaths_energy", "deaths_broken", "cells_broken", "mass_mean", "size_mean", "density_mean", "density_std", "speed_mean", "hard_mean", "worth", "fat_stock", "matter", "contacts", "fruit_eaten", "plant_intake", "meat_intake", "lineages", "biters_share", "steps_per_sec"],
                        {f"{w}, seed {s} (every 100,000 steps)": logs[w][s] for w in all_worlds for s in seeds_of(w)}, every=10)

    text = TEXT
    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>e025 What a block weighs - Report</title>
<style>{CSS}</style>
</head>
<body>
<main>
<h1>e025: What a block weighs</h1>
<p class="sub">Experiment report - 2026-09-03 - e024's closed world with the ledger fixed (#31) and one law added: a block weighs by its kind, times a density the genome expresses. The flat world, 500,000 steps, seeds 1-4, four pilots on seed 9, against e024's same four runs.</p>

<section class="tldr">
<h2>TL;DR</h2>
<p>{text["tldr"]}</p>
</section>

<h2>1. Question</h2>
<p>{text["question"]}</p>
<ol>
  <li><strong>The world stands and matter holds.</strong> No death, matter conserved to 0.01% over 500,000 steps (e024: 0.982-0.999), population coefficient of variation under 0.10.</li>
  <li><strong>Mass spreads.</strong> The density's spread over bodies stays above 0.1 (the range is 1/2 to 2) over the second half, and lineages alive at the end differ in mean density by 0.2 or more.</li>
  <li><strong>Armor costs speed, so the armored body changes.</strong> In the hunter state the tooth either drops its armor and keeps its muscle, or keeps the armor and is denser than its prey.</li>
  <li><strong>The hunter state is entered more often than one seed in four</strong> (e024 at flesh 1: seed 3 of 1-4).</li>
  <li><strong>#19.</strong> Lineages alive at or above e024's 2-3; a second winner that differs from the first in density or armor, not only in shape.</li>
</ol>

<h2>2. The world</h2>
<p>{text["world"]}</p>
{DIAGRAM}
<p>{text["runs"]}</p>
<ul class="measures">
  <li><strong>Weight</strong>: <code>density_mean</code> and <code>density_std</code> over the bodies alive; <code>mass_mean</code> (the weight now) beside <code>size_mean</code> (cells); <code>speed_mean</code> (muscle over mass); hard and muscle blocks per body; the density of each lineage in the lineage log.</li>
  <li><strong>The ledger</strong>: the world's matter (soil, ground, bodies, air) at each log step over the start.</li>
  <li><strong>Hunters</strong>: the biters' share, cells broken and bodies killed per step; from the lineage log, the lineages with a bite and the steps they held it.</li>
  <li>e024's measures otherwise: worth, meat, fat, population, contacts, fruit, lineages, events, snapshots.</li>
</ul>

<h2>3. Results</h2>
<div class="tw"><table>{summary}</table></div>
<ol class="verdicts">
<li><span class="verdict {text["c1"]}">{text["l1"]}</span> {text["v1"]}</li>
<li><span class="verdict {text["c2"]}">{text["l2"]}</span> {text["v2"]}</li>
<li><span class="verdict {text["c3"]}">{text["l3"]}</span> {text["v3"]}</li>
<li><span class="verdict {text["c4"]}">{text["l4"]}</span> {text["v4"]}</li>
<li><span class="verdict {text["c5"]}">{text["l5"]}</span> {text["v5"]}</li>
</ol>

<h3>3.1 {text["h1"]}</h3>
<div class="tw"><table>{pilot}</table></div>
<p>{text["r1"]}</p>

<h3>3.2 {text["h2"]}</h3>
<div class="grid2">
{charts["matter"]}{charts["pop"]}
</div>
<p>{text["r2"]}</p>

<h3>3.3 {text["h3"]}</h3>
<div class="grid2">
{charts["density"]}{charts["density_std"]}
</div>
<div class="grid2">
{charts["mass"]}{charts["size"]}
</div>
<p>{text["r3"]}</p>

<h3>3.4 {text["h4"]}</h3>
<div class="grid2">
{charts["hard"]}{charts["speed"]}
</div>
{gallery(GALLERY)}
<p>{text["r4"]}</p>

<h3>3.5 {text["h5"]}</h3>
<div class="grid2">
{charts["kills"]}{charts["biters"]}
</div>
<div class="grid2">
{charts["lineages"]}{charts["meat_share"]}
</div>
<p>{text["r5"]}</p>

<div class="wide">{timeline}</div>
<div class="viewer">
  <div class="canvases">
    <canvas id="world" width="1024" height="1024"></canvas>
    <canvas id="zoom" width="480" height="480"></canvas>
  </div>
  <div class="bar">
    <button id="play">Play</button>
    <select id="mode"><option value="long">Long view: every 10,000 steps</option><option value="clip">Clip: every 4th step from 300,000</option></select>
    <select id="layer"><option value="food">Ground: food</option><option value="soil">Ground: soil (long view)</option><option value="terrain">Ground: terrain (height)</option></select>
    <select id="speed"><option value="1">Slow</option><option value="2">Normal</option><option value="4">Fast</option></select>
    <span id="steplbl"></span>
  </div>
  <div class="bar"><input id="scrub" type="range" min="0" max="0" value="0"></div>
  <div class="bar" id="linlbl"></div>
  <div class="bar" id="legend">Blocks: {legend} <span class="sw front"></span> the front (white edge) <span class="sw dot"></span> has a bite on the front</div>
  <div class="bar">Left: the whole {vw}x{vw} world at the resolution of the body ({vw * 4}x{vw * 4} sub-cells), every cell a body holds colored by its lineage (gray: none), a white dot on bodies with a bite. The ground is food (green: plant and dead matter in the cell, brighter is more), soil or terrain. Right: the 32x32 cells around the middle, bodies drawn block by block, the front edge white.</div>
</div>
<p>{text["viewer"]}</p>

<h2>4. Discussion</h2>
{text["discussion"]}

<h2>5. Conclusion and next step</h2>
<p>{text["conclusion"]}</p>

<h2>Appendix: data</h2>
<p>Every 100,000th record; full logs in <code>results/*_log.csv</code>, lineages in <code>results/*_lineages.csv</code>, events in <code>results/*_events.csv</code>, bodies with their mass, size and density every 100,000 steps in <code>results/*_agents.csv</code>; e024's runs in <code>../e024_flesh/results</code>. Build: <code>uv run python experiments/e025_weight/report.py</code>.</p>
{tables}
</main>
<script id="frames" type="application/octet-stream">{blob}</script>
<script>{VIEWER_JS}</script>
</body>
</html>
"""
    out = os.path.join(HERE, "report.html")
    with open(out, "w") as f:
        f.write(page)
    print(f"wrote {out} ({os.path.getsize(out)//1024} KB)")


# Lineages that prospered: (world, seed, lineage id, name, what the shape does).
GALLERY = [
    ("flesh 1", 3, 164, "the tooth", "Eight cells two wide on 2.5 world cells: two hard cells at the front, the gut behind them, three of muscle at the back. Half its bodies bite (the lineage's mean bite is 1.1), it moves forward in 86% of its decisions, and 81% of what it ate was other bodies. 7,139 agents at its peak, the winner of seed 3 for 488,000 steps: the only hunter lineage of the batch, in the one run that entered the hunter state.", 300_000),
    ("flesh 1", 3, 814, "the gut beside the teeth", "Ten gut cells on 2.7 world cells, no armor, alive 286,000 steps with 1,365 agents beside the tooth: the prey that is also a scavenger (59% of its intake was other bodies, mostly the dead the teeth leave). Two winners in one world, the first time a second body holds for this long against the first."),
    ("flesh 1", 1, 107, "the net", "Four pads of three gut cells at the four corners of the 8x8 box, nothing between them: twelve guts on 7.6 world cells, no armor, no muscle, no eye. The winner of seed 1 for 498,000 steps with 78% of its intake from the dead. A body that eats from four places seven cells apart at once, laid over a ground where the fat corpses lie: the body of the flat world at flesh 1 in three seeds of four.", 300_000),
    ("flesh 0.7", 2, 1, "the net, with rain", "The same four pads at flesh 0.7 (12.6 gut cells on 6.2 world cells), the winner of its run for all 500,000 steps and of every run at 0.7: 54% of its intake the dead, the rest fruit. It is e022's bar pulled apart into its corners.", 300_000),
    ("flesh 1", 1, 882, "a small body with an eye", "Thirteen cells on 3.2 world cells with one sensor, alive 204,000 steps beside the net with 428 agents: the last body of the batch that kept an eye. In a world where the food is corpses that lie for hundreds of steps, an eye that sees far pays nobody."),
    ("flesh 1", 4, 123, "the compact gut", "Fifteen gut cells in a bar and a hook on 4.6 world cells, 182,000 steps with 398 agents beside seed 4's net: e023's shape, and it loses to four pads that eat from four places with fewer guts."),
]

TEXT = {
    "question": "e022 brought the crowd and e023 the eye; the tooth appears in every run and never pays, and a cell of another body is worth what it cost: 0.02 of matter plus its share of the body's energy, 0.10-0.15 in all, five to seven bites of grass. Issue #27 asks for the worth of flesh as a law about a material with matter conserved. The real world's premise: flesh is dense because an animal is the concentrate of what it ate and burned. The law here: a share of what a body burns is fixed in its flesh instead of breathed, and goes to whoever breaks a cell of it, or to the ground when it dies. The body's own economy is unchanged; only what its cells are worth to others changes. Hypotheses:",
    "world": "Everything is e023's closed world (128x128 on a torus, matter 8 per cell at the start, bodies of 8x8 cells in five kinds grown from the genome, space at the resolution of the body, work = force x distance, a cell that costs what it holds, the dead eaten where they lie, the terrain with soil that runs downhill, the canopy, the spill, rain on every cell alike, mutation per base, a sensor block that sees one more cell) with one law changed: where the upkeep goes.",
    "runs": "<strong>Runs.</strong> A dose series first: the flat world on seed 9 for 200,000 steps at <code>flesh</code> 0.1, 0.3, 0.5, 0.7, 0.85, 0.95 and 1 (15-20 minutes each). Then the batch at the two shares that bracket the switch the dose series found: <code>flesh</code> 1 and <code>flesh</code> 0.7, seeds 1-4 each, 500,000 steps, one thread each, eight at once on one machine (12 cores, 90 minutes; 80-135 steps per second). The control is e023's flat seeds 1-4, the same code at <code>flesh 0</code> (checked byte for byte on seed 9 over 30,000 steps), compared over their first 500,000 steps.",
    "tldr": "The flesh law makes a body worth eating - a cell is worth 1-2.5 against e023's 0.15 - and the world answers by eating the dead. At every share up to 0.7, and in three seeds of four at 1, nothing bites: the winner is a net of four pads of three gut cells at the corners of its box, seven world cells apart, that eats the corpses from four places at once, meat is 56-80% of the intake, and the fat hoards a quarter to two thirds of the world's matter. The tooth comes in one seed of four at flesh 1 and in every pilot at 0.85 and above: 4,500 bodies of nine cells, half with a hard tip, four kills a step, a hunter lineage for 488,000 steps beside a gut that lasts 286,000. A cell is worth less in the hunter's world than in the net's; the two are states, entered at the start. Next: #25, what a block weighs.",
    "c1": "yes", "l1": "Yes, four to nineteen times", "v1": "A cell of a body is worth 1.09-1.19 at flesh 0.7 and 2.2-2.5 in the net state at flesh 1, against e023's 0.125-0.181 (a bite of grass is 0.02); in the hunter state it is 0.64, because nobody grows old there. The pilot's oldest bodies (age 2,400, 64 cells) carried 130-160 of fat.",
    "c2": "partly", "l2": "Meat is most of the intake, and it is the dead's", "v2": "Other bodies are 56-58% of the food eaten at 0.7 and 75-80% at 1 (e023: 9-20%), and a cell broken by a push pays 0.45-0.70 where cells are broken, twenty to thirty bites. But in seven runs of eight the bodies killed per step are 0.00: the meat is corpses. A body that starves lays its fat, and a gut eats it without a tooth.",
    "c3": "partly", "l3": "One seed of four at flesh 1, and it holds", "v3": "Seed 3 entered the hunter state at step 40,000 and kept it: 44-50% of its bodies carry a bite over the whole run, 4 bodies are killed and 310 cells broken per step, and one lineage holds a bite for 488,000 steps with 81% of its intake from other bodies. Seeds 1, 2 and 4 and all four runs at 0.7 never bite (peaks 0.4%). The dose series entered the hunter state at 0.85, 0.95 and 1 (seed 9) and never below.",
    "c4": "partly", "l4": "The world stands; the fat hoards it", "v4": "No run died, population cv is 0.02-0.05 (e023: 0.05-0.11). But the fat is not a few percent of the world's matter: 25-29% at 0.7 and 63-70% in the net state at 1, where the air holds 0.4-2 and the rain has stopped; in the hunter state it is 9%. Matter is 0.998-0.999 at the end over the start and 0.982 in the hunter run: an f32 ground under corpses of 30-150 per cell loses to rounding, e019's soil problem again.",
    "c5": "partly", "l5": "A second winner in one world; the net everywhere else", "v5": "Lineages alive 1-3 (e023: 1-2). The hunter run holds two for 286,000 steps, the tooth and a gut that lives beside it, the longest a second body has held against the first. The other seven runs have one winner each and it is the same body, the net, in every one; e023's frame that sees is gone, and the eye with it (a sensor on 0.2-7% of the bodies).",
    "h1": "A cell is worth up to a hundred bites, and the dead lie everywhere",
    "r1": "The dose (left): the intake from other bodies climbs with the share from 23% to 72% while the bodies with a bite stay at zero up to 0.7 and jump to 17-26% from 0.85, and the fat takes 2-16% of the world's matter. The worth of a cell (right) is 1.1-1.2 at 0.7 and climbs to 2.2-2.5 in the net state at 1 as the bodies age on a ground of corpses; the hunter run (the low blue line) sits at 0.64 with the same law, because its bodies die at 124 steps on average. What a cell is worth is not what decides whether it is bitten.",
    "h2": "Meat is most of the intake, and it is the dead's",
    "r2": "Other bodies (left) are 56-58% of the food at 0.7 and 75-80% at 1, in the net state and the hunter state alike; e023's 9-20% is the gray band. What a kill pays (right) is 0.45 per cell in the hunter run, steady, twenty bites for one push; at 0.7 the line jumps between 0.1 and 0.9 because a cell is broken every few thousand steps. The meat is the same in both states; who takes it differs: a net over a corpse, or a tooth in a living body.",
    "h3": "The tooth: one world in four, and it holds",
    "r3": "Biters (left) are a flat zero in seven runs and 44-50% in seed 3 from step 40,000 to the end; cells broken (right) are 300 a step there and under 0.2 everywhere else. The bodies (Figure 2) show the two answers to the same law: the net, four pads of three guts at the corners of its box, and the tooth, two hard cells at the front of a gut with muscle behind, two wide on two and a half cells. The tooth's world is 4,500 bodies of nine cells; the net's is 3,500 of twelve. The pilot at flesh 1 also grew a 48-cell body with 9 hard, 13 muscle and a bite of 2 that held 26,000 steps beside a smaller winner: the armored hunter exists in the space, and did not win.",
    "h4": "The world stands; the fat hoards it",
    "r4": "Population (top left) is flat at 3,300-4,500 in every run, twice e023's, with no death. The fat's share of the world's matter (top right) is the story: 25-29% at 0.7, 63-70% in the net state at 1, and 9% in the hunter state, where the teeth keep the fat moving. In the net state the air holds 0.4-2 and the rain is gone: nothing is breathed, the corpses rot where they fall, and the world's matter sits in living flesh. Fruit (bottom left) is 35% of the intake at 0.7 and 20% at 1; contacts (bottom right) are 0.7-1.0 at 0.7, the crowd on the rings, and 0.1-0.7 at 1.",
    "h5": "Winners: the net, and in one world the tooth beside a gut",
    "r5": "Lineages (left) are 1-3, and in the hunter run two hold together for 286,000 steps: the tooth and the gut that lives beside it, the first second body since e021 that is not the first body on other ground. Mass (right) marks the states: 11-13 cells in the net state, 9 in the hunter's, where a body of 15 is eaten before it grows. The frame that sees is not among the winners; the eye is on 0.2-7% of the bodies, because corpses do not move and lie for hundreds of steps.",
    "viewer": "The flat world at flesh 1, seed 3, the hunter state: bodies with a white dot are the teeth, and the ground under the crowd is bright with what they leave.",
    "discussion": "<p>The law was written as a material, and it worked as one: a cell of a body is worth four to nineteen times what it was. Selection then took the cheapest route to that worth, which is not a tooth. A body that starves lays its fat on the ground, and a gut on that cell eats it at the same rate as grass; a body that puts three guts in each corner of its box eats from four cells at once. The net is that body, and it wins at every share up to 0.7 and in three seeds of four at 1. e008 and e017 found the prize on a body was not the lever; this experiment says why: with the dead eaten where they lie, the prize is paid to whoever waits. Hunting pays only where the corpses are too few - the hunter state, where the teeth kill bodies at 124 steps of age and the fat never accumulates.</p><p>The two states are the surprise. Under one law and one share the world sits either in the net state - 70% of its matter in living flesh, no breath, no rain, one winner - or in the hunter state - 9% in flesh, 300 cells broken a step, the air fed by the work of moving, two winners. Which one a run enters is decided in the first 40,000 steps: the pilots at 0.85-1 all entered the hunter state at the start's crash, seed 3 at step 40,000, and seeds 1, 2 and 4 never. A cell is worth less in the hunter's world (0.64) than in the net's (2.4), so the worth of a cell is not what makes the tooth pay; the state does, and the state is a lottery of the start, like e022's. Weather (#24) is the kind of law that could move a world between them.</p><p>What this does not show: why the switch sits between 0.7 and 0.85 (the air falls from 71 to 45 across it; the grass may be what runs short first), whether the net state ever tips into the hunter state after the start, and what the mountain worlds do. The matter drifts by 0.2-1.8% over 500,000 steps where corpses of 30-150 lie on an f32 ground (e023: 0.03%); the fix is an f64 ground, as e019's soil, before the next experiment. The runs are 500,000 steps, not a million; the states were settled by 100,000 in every run.</p>",
    "conclusion": "The flesh law is kept: a share of what a body burns stays in its flesh and goes to whoever breaks a cell of it, matter conserved. It made a body worth eating and it made the world eat its dead. The tooth pays in a state the world enters at the start and keeps, where the meat is not left lying, and there the world has two winners and four kills a step: the most there has been to watch. The default share is set to 1 (nothing a body burns is lost but the work of moving), the share where the hunter state exists. Next: #25, what a block weighs - a heavy armored hunter and a light net are now two bodies that could both be right - after the ground is made an f64; then #24, weather, which could move a world between its two states.",
}


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "lineages":
        top_lineages()
    else:
        main()

