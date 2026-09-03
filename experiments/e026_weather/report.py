#!/usr/bin/env python3
"""Build report.html for e026.

Charts: matplotlib, exported as SVG and inlined. Diagram: hand-written SVG.
Run from the repo root: uv run python experiments/e026_weather/report.py
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

E025 = os.path.join(HERE, "..", "e025_weight")
# Places of a world: (id in the CSVs, name, color). Under the uniform sun a place is a height band (thirds of the cells by the
# terrain); the flat world is rained on alike (before the cloud), the bands are kept for the loaders.
BANDS = [(0, "valleys (lowest third)", SERIES[0]), (1, "slopes (middle third)", SERIES[3]), (2, "ridges (highest third)", SERIES[1])]
BASE = "128_sigma0_r64_f0.1_flat_eyes8_flesh1_w1"
CLOUD_AMP = "1"  # the amplitudes the pilots picked for the batch
SEASON_AMP = "0.5"
# Worlds of this experiment: label -> run prefix, world size, places, seeds. The control is e025's weight-1 runs (the same code
# with the weather off, byte for byte).
WORLDS = {
    f"cloud {CLOUD_AMP}": dict(run=f"{BASE}_cloud{CLOUD_AMP}", size=128, places=BANDS, seeds=[1, 2, 3, 4], uniform=True, folder=HERE),
    f"season {SEASON_AMP}": dict(run=f"{BASE}_season{SEASON_AMP}", size=128, places=BANDS, seeds=[1, 2, 3, 4], uniform=True, folder=HERE),
    "e025 (control)": dict(run=BASE, size=128, places=BANDS, seeds=[1, 2, 3, 4], uniform=True, folder=E025),
}
CLOUD, SEASON, CONTROL = list(WORLDS)
PILOT_RUN = BASE + "_{}{}_seed9"  # the pilots: seed 9, 200,000 steps, cloud 1 / 0.5 and season 1 / 0.5
PILOTS = [("cloud", "1"), ("cloud", "0.5"), ("season", "1"), ("season", "0.75"), ("season", "0.5")]
REFS = {}
WORLD_COLOR = {CLOUD: SERIES[0], SEASON: SERIES[2], CONTROL: SERIES[1]}
CELL_ENERGY = 0.02
BITE = 0.02
KIND_COLOR = {1: SERIES[0], 2: SERIES[1], 3: SERIES[3], 4: SERIES[2]}
CONFIRM_STEPS = 5000
VIEWER_WORLD = SEASON
VIEWER_SEED = 2
LAST_STEP = 500_000
WEATHER_GRAIN = 16
SEASON_STEPS = 20_000


def seeds_of(w):
    if w not in WORLDS:  # a reference world
        return [1, 2, 3, 4]
    if os.environ.get("EVLOG_SEEDS") and w != CONTROL:  # a dry run on the seeds that are done
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


def season_chart(title, subtitle, logs, t0, t1):
    """The bodies in confirmed lineages every 1,000 steps (from the lineage log; the log's 10,000 steps are half a season)
    over a window, one line per run, with the sun's factor dotted on a right axis."""
    fig, ax = new_axes()
    top = 0
    for w in [SEASON, CONTROL]:
        for k, s in enumerate(seeds_of(w)):
            run, folder = f"{WORLDS[w]['run']}_seed{s}", WORLDS[w]["folder"]
            tot = Counter()
            for r in load_rows(f"results/{run}_lineages.csv", folder):
                t = int(r["step"])
                if t0 <= t <= t1:
                    tot[t] += int(r["size"])
            xs = sorted(tot)
            ys = [tot[t] for t in xs]
            if ys:
                top = max(top, max(ys))
                ax.plot(xs, ys, color=WORLD_COLOR[w], linewidth=1.1, alpha=0.85, label=w if k == 0 else None)
    ax2 = ax.twinx()
    xs = list(range(int(t0), int(t1) + 1, 500))
    ax2.plot(xs, [1 + float(SEASON_AMP) * math.sin(2 * math.pi * t / SEASON_STEPS) for t in xs], color=INK, linestyle=":", linewidth=1, label="the sun's factor")
    ax2.set_ylim(0, 2)
    ax2.set_yticks([0, 1, 2])
    ax2.spines["right"].set_visible(False)
    ax2.tick_params(axis="y", colors=INK)
    ax2.grid(False)
    finish(ax, 0, None, top, False, 3)
    return figure(title, subtitle, to_svg(fig))


def cloud_figure(title, subtitle, run, step, sigma, size=128):
    """Two maps: the cloud's rain weight and the standing plant at one step."""
    nodes, (nx, ny) = weather_nodes(run)
    maps = soil_maps(run)
    if not nodes or step not in nodes or not maps:
        return ""
    w = cloud_field(nodes[step], nx, ny, step, size, sigma)
    soil = None
    for t, so, _ in maps:
        if t == step:
            soil = so
    if soil is None:
        return ""
    fig, axes = plt.subplots(1, 2, figsize=(6.4, 3.3))
    grid = lambda v: [v[y * size:(y + 1) * size] for y in range(size)]
    axes[0].imshow(grid([math.log2(x) for x in w]), cmap="Blues", vmin=-1.5, vmax=1.5, interpolation="nearest")
    axes[0].set_title("rain weight (log scale)", fontsize=9, color=INK)
    axes[1].imshow(grid([math.log10(max(x, 0.01)) for x in soil]), cmap="YlOrBr", vmin=-2, vmax=1, interpolation="nearest")
    axes[1].set_title("soil, 0.01 to 10 (log scale)", fontsize=9, color=INK)
    for ax in axes:
        ax.set_xticks([])
        ax.set_yticks([])
        ax.grid(False)
        for sp in ax.spines.values():
            sp.set_visible(False)
    fig.tight_layout()
    return figure(title, subtitle, to_svg(fig))


def pilot_table():
    """The pilots (seed 9, 200,000 steps, one per weather form and amplitude): medians over the second half, as an HTML table."""
    cols = []
    for mode, amp in [("", "")] + PILOTS:
        path = os.path.join(HERE if mode else E025, "results", f"{PILOT_RUN.format(mode, amp)}_log.csv")
        if not os.path.exists(path) or os.path.getsize(path) < 1000:  # a run still writing has an empty log
            continue
        log = load_csv(path)
        n = len(log["step"])
        h = slice(n // 2, n)
        med = lambda xs: statistics.median(xs[h])
        pop = log["pop"]
        label = f"{mode} {amp}" if mode else "e025 (weather off)"
        # The swing within the second half from the lineage log (every 1,000 steps: the log's 10,000 are half a season).
        tot = Counter()
        for r in load_rows(f"results/{PILOT_RUN.format(mode, amp)}_lineages.csv", HERE if mode else E025):
            if int(r["step"]) >= log["step"][-1] // 2:
                tot[int(r["step"])] += int(r["size"])
        swing = max(tot.values()) / max(min(tot.values()), 1) if tot else float("nan")
        last = int(log["step"][-1])
        dead = last < 200_000
        blank = lambda v: "-" if dead else v
        cols.append((label + (f" (died at {last:,})" if dead else ""), {k: blank(v) if k not in ("matter",) else v for k, v in dict(
            pop=f"{med(pop):,.0f} ({statistics.pstdev(pop[h]) / max(statistics.mean(pop[h]), 1):.2f})", swing=f"{swing:.1f}",
            fat=f"{med(log['fat_mean']):.2f}", fat_share=f"{med([f / m for f, m in zip(log['fat_stock'], log['matter'])]):.0%}",
            trees=f"{med(log['trees']):.0f}", sensor=f"{med(log['sensor_agents_share']):.1%}",
            biters=f"{med(log['biters_share']):.1%}", kills=f"{med([k / 10_000 for k in log['deaths_broken']]):.2f}",
            density=f"{med(log['density_mean']):.2f} &plusmn; {med(log['density_std']):.2f}", size=f"{med(log['size_mean']):.1f}",
            lineages=f"{med(log['lineages']):.0f}", matter=f"{log['matter'][-1] / log['matter'][0]:.6f}").items()}))
    if not cols:
        return ""
    rows = [("Population (cv); peak over trough, second half", "pop|swing"), ("Fat per body; fat, share of the matter", "fat|fat_share"), ("Trees", "trees"),
            ("Bodies with a sensor", "sensor"), ("Bodies with a bite; bodies killed per step", "biters|kills"), ("Density per body (mean &plusmn; spread); cells per body", "density|size"),
            ("Lineages alive", "lineages"), ("Matter at the end over the start", "matter")]
    body = "".join(f"<tr><td>{label}</td>" + "".join("<td>" + "; ".join(d[k] for k in keys.split("|")) + "</td>" for _, d in cols) + "</tr>" for label, keys in rows)
    return ("<thead><tr><th>Pilot, seed 9, 200,000 steps (median over the second half)</th>" + "".join(f"<th>{c}</th>" for c, _ in cols) + "</tr></thead><tbody>" + body + "</tbody>")


def weather_nodes(run, folder=HERE):
    """The cloud's nodes (nx by ny, row by row) every 1,000 steps: step -> list."""
    path = os.path.join(folder, "results", f"{run}_weather.csv")
    if not os.path.exists(path):
        return {}, (0, 0)
    out = {}
    with open(path) as f:
        head = f.readline()
        nx, ny = [int(x) for x in head.split("(")[1].split(",")[0].split(" by ")]
        for line in f:
            parts = line.strip().split(",")
            out[int(parts[0])] = [float(x) for x in parts[1:]]
    return out, (nx, ny)


def cloud_field(nodes, nx, ny, step, size, sigma, wind=1 / 200):
    """The rain weight of every cell at `step` from the nodes, as the code computes it (bilinear on the torus, unit variance, lognormal mean 1)."""
    drift = (wind * step) % size
    bias = 0.5 * sigma * sigma
    w = [0.0] * (size * size)
    for y in range(size):
        v = y / WEATHER_GRAIN
        j0 = int(math.floor(v)) % ny
        j1 = (j0 + 1) % ny
        fy = v - math.floor(v)
        for x in range(size):
            u = ((x - drift) % size) / WEATHER_GRAIN
            i0 = int(math.floor(u)) % nx
            i1 = (i0 + 1) % nx
            fx = u - math.floor(u)
            a, b, c, d = (1 - fx) * (1 - fy), fx * (1 - fy), (1 - fx) * fy, fx * fy
            z = (a * nodes[j0 * nx + i0] + b * nodes[j0 * nx + i1] + c * nodes[j1 * nx + i0] + d * nodes[j1 * nx + i1]) / math.sqrt(a * a + b * b + c * c + d * d)
            w[y * size + x] = math.exp(sigma * z - bias)
    return w


def cloud_soil_corr(run, folder=HERE, sigma=1.0, size=128, band_id=2, from_step=100_000):
    """How far the soil follows the cloud: the correlation over the cells of one band between the log of the rain weight and the
    soil (capped at 8) at each 100,000-step dump from `from_step`; the median over the dumps, and the list."""
    nodes, (nx, ny) = weather_nodes(run, folder)
    if not nodes:
        return float("nan"), []
    band = terrain_of(run, folder)["band"]
    cells = [c for c in range(size * size) if band[c] == band_id]
    out = []
    for t, soil, _ in soil_maps(run, folder):
        if t < from_step or t not in nodes:
            continue
        w = cloud_field(nodes[t], nx, ny, t, size, sigma)
        a = [math.log(w[c]) for c in cells]
        b = [min(soil[c], 8.0) for c in cells]
        ma, mb = statistics.mean(a), statistics.mean(b)
        sa, sb = statistics.pstdev(a), statistics.pstdev(b)
        out.append(sum((x - ma) * (y - mb) for x, y in zip(a, b)) / len(a) / (sa * sb) if sa and sb else float("nan"))
    return (statistics.median(out) if out else float("nan")), out


def cell_rain_chart(title, subtitle, world, cell, t0, t1, sigma):
    """The rain weight one cell sees over a window of steps, one line per run of the cloud world (from the nodes every 1,000 steps)."""
    fig, ax = new_axes()
    top = 0
    for k, s in enumerate(seeds_of(world)):
        run = f"{WORLDS[world]['run']}_seed{s}"
        nodes, (nx, ny) = weather_nodes(run, WORLDS[world]["folder"])
        ts = [t for t in sorted(nodes) if t0 <= t <= t1]
        ys = [cloud_field_at(nodes[t], nx, ny, t, 128, sigma, cell) for t in ts]
        if ys:
            top = max(top, max(ys))
            ax.plot(ts, ys, color=SERIES[k % len(SERIES)], linewidth=1.1, alpha=0.85, label=f"seed {s}")
    ax.axhline(1.0, color=INK, linestyle=":", linewidth=1)
    finish(ax, 0, None, top, False, 4)
    return figure(title, subtitle, to_svg(fig))


def cloud_field_at(nodes, nx, ny, step, size, sigma, cell, wind=1 / 200):
    """The rain weight of one cell (as cloud_field, for one cell)."""
    x, y = cell % size, cell // size
    drift = (wind * step) % size
    v = y / WEATHER_GRAIN
    j0 = int(math.floor(v)) % ny
    j1 = (j0 + 1) % ny
    fy = v - math.floor(v)
    u = ((x - drift) % size) / WEATHER_GRAIN
    i0 = int(math.floor(u)) % nx
    i1 = (i0 + 1) % nx
    fx = u - math.floor(u)
    a, b, c, d = (1 - fx) * (1 - fy), fx * (1 - fy), (1 - fx) * fy, fx * fy
    z = (a * nodes[j0 * nx + i0] + b * nodes[j0 * nx + i1] + c * nodes[j1 * nx + i0] + d * nodes[j1 * nx + i1]) / math.sqrt(a * a + b * b + c * c + d * d)
    return math.exp(sigma * z - 0.5 * sigma * sigma)


def cycle_swing(run, folder=HERE, first_step=250_000):
    """Peak over trough of the bodies in confirmed lineages (every 1,000 steps) within each season of the second half; the median."""
    tot = Counter()
    for r in load_rows(f"results/{run}_lineages.csv", folder):
        t = int(r["step"])
        if t >= first_step:
            tot[t] += int(r["size"])
    cyc = defaultdict(list)
    for t, v in tot.items():
        cyc[(t - first_step) // SEASON_STEPS].append(v)
    sw = [max(v) / max(min(v), 1) for v in cyc.values() if len(v) >= 15]
    return statistics.median(sw) if sw else float("nan")


def winners(run, folder=HERE, first_step=250_000):
    """The top lineage at each lineages.csv step from `first_step`: the distinct winners, and the longest hold in steps."""
    top = {}
    for r in lineage_rows(run, folder).values():
        for row in r:
            t = int(row["step"])
            if t < first_step:
                continue
            n = int(row["size"])
            if n > top.get(t, (0, None))[0]:
                top[t] = (n, row["lineage"])
    steps = sorted(top)
    if not steps:
        return 0, 0, []
    seq = [top[t][1] for t in steps]
    holds, cur, start = [], seq[0], steps[0]
    for t, l in zip(steps, seq):
        if l != cur:
            holds.append((cur, start, t))
            cur, start = l, t
    holds.append((cur, start, steps[-1] + 1000))
    longest = max(b - a for _, a, b in holds)
    return len(set(seq)), longest, holds


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
<svg viewBox="0 0 900 340" role="img" aria-label="Left: the cloud. The air holds what the bodies breathe; it rains on every cell at most 0.01 a step times a weight that a drifting field sets, so a wet cell gets more than twice its mean and a dry cell a sixth; the rain lands in the soil, the plant grows out of the soil. Right: the season. The sun's rate is 0.01 times one plus a sine of the step over 20,000; where the plant stands at the cap, fruit falls at the sun's rate.">
<g fill="none" stroke="currentColor" stroke-width="1.2" font-size="12" font-family="system-ui, sans-serif">
  <!-- the cloud -->
  <text x="225" y="24" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">the cloud: where the rain falls</text>
  <rect x="40" y="38" width="370" height="46" rx="4"/>
  <text x="225" y="56" text-anchor="middle" fill="currentColor" stroke="none">the air: what the bodies breathe (20-30 a step)</text>
  <text x="225" y="74" text-anchor="middle" fill="currentColor" stroke="none">it empties every step</text>
  <!-- the field: a lattice of nodes with a cloud blob -->
  <g stroke="none" fill="currentColor" fill-opacity="0.35">
    <circle cx="90" cy="120" r="3"/><circle cx="150" cy="120" r="3"/><circle cx="210" cy="120" r="3"/><circle cx="270" cy="120" r="3"/><circle cx="330" cy="120" r="3"/>
  </g>
  <ellipse cx="205" cy="120" rx="70" ry="24" fill="var(--s1)" fill-opacity="0.18" stroke="var(--s1)"/>
  <text x="205" y="124" text-anchor="middle" fill="var(--s1)" stroke="none">wet: weight 2.2</text>
  <text x="345" y="124" text-anchor="middle" fill="currentColor" stroke="none">dry: weight 1/6</text>
  <text x="40" y="104" fill="currentColor" stroke="none">nodes 16 cells apart, memory 3,000 steps</text>
  <path d="M 285,160 L 325,160" marker-end="url(#ah)"/>
  <text x="335" y="164" fill="currentColor" stroke="none">wind: 1 cell / 200 steps</text>
  <!-- the rain -->
  <path d="M 175,150 L 175,210" stroke="var(--s1)" stroke-width="3" marker-end="url(#ah)"/>
  <path d="M 205,150 L 205,210" stroke="var(--s1)" stroke-width="3" marker-end="url(#ah)"/>
  <path d="M 235,150 L 235,210" stroke="var(--s1)" stroke-width="3" marker-end="url(#ah)"/>
  <path d="M 300,135 L 300,210" stroke-dasharray="2 4" marker-end="url(#ah)"/>
  <path d="M 90,140 L 90,210" marker-end="url(#ah)"/>
  <text x="100" y="180" fill="currentColor" stroke="none">mean: 0.01 a step</text>
  <text x="205" y="228" text-anchor="middle" fill="currentColor" stroke="none">the rain: the cap of e025 x the weight (lognormal, mean 1)</text>
  <!-- the ground -->
  <path d="M 40,250 L 400,250"/>
  <text x="225" y="270" text-anchor="middle" fill="currentColor" stroke="none">the soil: the rain lands here and runs downhill</text>
  <text x="225" y="290" text-anchor="middle" fill="currentColor" stroke="none">the plant grows out of the soil at the sun's rate, up to the cap 8</text>
  <text x="225" y="318" text-anchor="middle" fill="currentColor" stroke="none">the world's rain is what it was; only where it falls changes</text>
  <!-- the season -->
  <text x="675" y="24" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">the season: how much sun</text>
  <path d="M 500,150 L 860,150" stroke-dasharray="4 4"/>
  <text x="860" y="143" text-anchor="end" fill="currentColor" stroke="none">0.01 (e025)</text>
  <path d="M 500,150 C 545,60 590,60 635,150 C 680,240 725,240 770,150 C 815,60 860,60 880,110" stroke="#1baf7a" stroke-width="2"/>
  <path d="M 500,250 L 860,250" marker-end="url(#ah)"/>
  <text x="680" y="270" text-anchor="middle" fill="currentColor" stroke="none">step: one cycle is 20,000 steps, seven lifetimes</text>
  <path d="M 500,250 L 500,60" marker-end="url(#ah)"/>
  <text x="515" y="72" fill="currentColor" stroke="none">the sun's rate on every cell</text>
  <text x="612" y="62" fill="#1baf7a" stroke="none">0.01 (1 + a)</text>
  <text x="702" y="245" text-anchor="middle" fill="#1baf7a" stroke="none">0.01 (1 - a): at a = 1 the sun goes out</text>
  <text x="680" y="300" text-anchor="middle" fill="currentColor" stroke="none">where the plant stands at the cap, fruit falls at the sun's rate:</text>
  <text x="680" y="318" text-anchor="middle" fill="currentColor" stroke="none">the valley's income moves with the sun; the bare ridge's does not</text>
</g>
<defs>
  <marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="currentColor"/></marker>
</defs>
</svg>
<figcaption>Figure 1. The weather. Everything is e025's world; one law about the world is added, in one of two forms per run. The cloud (left): the most the air can rain on a cell per step is e025's 0.01 times a weight from a field that changes with a memory of 3,000 steps and drifts east, so a place's rain has a mean and a variance; the air empties every step, so the world's rain is unchanged and only where it falls moves. The season (right): the sun's rate on every cell is a sine of time with a period of 20,000 steps and amplitude a. Where the lawn stands at the cap, fruit falls at the sun's rate, so the valley's income follows the sun.</figcaption>
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
        folder = WORLDS[world]["folder"]
        if run not in cache:
            cache[run] = (lineage_rows(run, folder), load_bodies(run, folder), list(read_frames(f"results/{run}_long.jsonl", folder)))
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
                by = lineage_rows(run, d["folder"])
            except FileNotFoundError:
                continue
            out = []
            for lid, rows in by.items():
                peak = max(rows, key=lambda r: int(r["size"]))
                span = int(rows[-1]["step"]) - int(rows[0]["step"]) + CONFIRM_STEPS
                out.append((span, lid, peak))
            out.sort(reverse=True)
            print(f"{w}, seed {s}")
            for span, lid, r in out[:5]:
                print(f"  lineage {lid}: {span:,} steps ({r['step']} peak), {r['size']} agents, mass {r['mass']}, hard {r['hard']}, muscle {r['muscle']}, dig {r['digestive']}, "
                      f"foot {r['foot']}, {r['len_fwd']}x{r['len_side']}, bite {r['bite']}, shell {r['shell']}, meat {r['meat']}/{r['plant']}, density {r.get('density', '-')}, age {r['age']}")



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
        logs[w] = {s: {k: v[:LAST_STEP // 10_000] for k, v in load_csv(f"results/{d['run']}_seed{s}_log.csv", d["folder"]).items()} for s in seeds_of(w)}
        events[w] = {s: load_rows(f"results/{d['run']}_seed{s}_events.csv", d["folder"]) for s in seeds_of(w)}
    for w, (run, folder, _) in REFS.items():
        # e023's runs went to 1,000,000 steps; the comparison is over the same span as these runs.
        logs[w] = {s: {k: v[:LAST_STEP // 10_000] for k, v in load_csv(f"results/{run}_seed{s}_log.csv", folder).items()} for s in seeds_of(w)}
    run_of = lambda w, s: (f"{WORLDS[w]['run']}_seed{s}", WORLDS[w]["folder"]) if w in WORLDS else (f"{REFS[w][0]}_seed{s}", REFS[w][1])
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
        # The weather: the swing of the population within the second half (peak over trough), the fat per body, the trees,
        # the movers (bodies standing outside the band they were born in), the rain's variation over time per band (the cv of
        # the rain fallen per step on each band over the second half, the largest band), the winners over the second half.
        d["pop_swing_half"] = max(pop) / max(min(pop), 1)
        d["trees"] = med(half(log, "trees"))
        pl = places[w][s]
        n_pl = min(len(pl[p]["step"]) for p in pl) if pl else 0
        d["movers"] = med([sum(pl[p]["movers"][i] for p in pl) / max(sum(pl[p]["pop"][i] for p in pl), 1) for i in range(n_pl // 2, n_pl)]) if n_pl else float("nan")
        d["rain_cv"] = max((statistics.pstdev(pl[p]["rain"][n_pl // 2:]) / max(statistics.mean(pl[p]["rain"][n_pl // 2:]), 1e-9)) for p in pl) if n_pl else float("nan")
        d["winners"], d["hold"], _ = winners(run, folder)
        d["cycle_swing"] = cycle_swing(run, folder)
        d["cloud_corr"] = cloud_soil_corr(run, folder, float(CLOUD_AMP))[0] if w == CLOUD else float("nan")
        d["lineages_end"] = per_step.get(last_step - last_step % 1000, 0)
        return d

    places = {w: {s: load_places(*run_of(w, s)) for s in seeds_of(w)} for w in WORLDS}
    S = {w: {s: summarize(w, s) for s in seeds_of(w)} for w in all_worlds}
    if os.environ.get("EVLOG_PRINT"):
        for w in all_worlds:
            for s_ in seeds_of(w):
                print(w, s_, {k: (round(v, 3) if isinstance(v, float) else v) for k, v in S[w][s_].items()})

    charts = {}
    worth_of = lambda l: l["worth"] if "worth" in l else [e / max(m, 1e-9) + CELL_ENERGY for e, m in zip(l["mean_energy"], l["mass_mean"])]
    pilot = pilot_table()
    charts["pop"] = world_chart("Population", "Bodies alive at each log step, one line per run (blue: the cloud, aqua: the season, orange: e025). A line that ends is a world that died.", logs, lambda l: l["pop"], all_worlds, WORLD_COLOR)
    charts["lineages"] = world_chart("Lineages alive", "Confirmed lineages at each log step, one line per run. One would be one body winning.", logs, lambda l: l["lineages"], all_worlds, WORLD_COLOR)
    charts["fat"] = world_chart("Fat per body", "Mean fat a body carries (what its upkeep fixed in its flesh; a store for its eater, not for itself), one line per run.", logs, lambda l: l["fat_mean"], all_worlds, WORLD_COLOR, ymin=0)
    charts["sensor"] = world_chart("Bodies with a sensor", "Share of the bodies alive with at least one sensor block, one line per run. Zero is a blind world.", logs, lambda l: l["sensor_agents_share"], all_worlds, WORLD_COLOR, ymin=0, percent=True)
    charts["kills"] = world_chart("Bodies killed per step", "Bodies whose last cell a push broke, per step, one line per run. Zero is e025's net state.", logs, lambda l: [k / 10_000 for k in l["deaths_broken"]], all_worlds, WORLD_COLOR, ymin=0)
    charts["matter"] = world_chart("The world's matter", "All the matter of the world (soil, ground, bodies, air) at each log step over what it was at the start, one line per run.", logs, lambda l: [m / l["matter"][0] for m in l["matter"]], all_worlds, WORLD_COLOR, ymin=0.995, ymax=1.005, hline=1.0)
    charts["trees"] = world_chart("Trees", "Cells whose standing plant is 1 or more (50 bites), one line per run: the world's store.", logs, lambda l: l["trees"], all_worlds, WORLD_COLOR, ymin=0)
    charts["biters"] = world_chart("Bodies with a bite", "Share of the bodies alive with a hard tip and muscle behind it, one line per run.", logs, lambda l: l["biters_share"], all_worlds, WORLD_COLOR, ymin=0, percent=True)
    charts["rain"] = cell_rain_chart(f"The rain one cell sees ({CLOUD})", "The rain weight of one cell (the world's center) over steps 300,000-340,000, one line per run: 1 is e025's rain, 2 twice it. A spell lasts a few thousand steps.", CLOUD, 64 * 128 + 64, 300_000, 340_000, float(CLOUD_AMP))
    charts["season_zoom"] = season_chart(f"Two cycles of the season ({SEASON})", "Bodies in confirmed lineages every 1,000 steps over steps 300,000-340,000 (two cycles), one line per run (aqua: the season, orange: e025); dotted: the sun's factor, right scale.", logs, 300_000, 340_000)
    mseed = VIEWER_SEED if VIEWER_SEED in seeds_of(CLOUD) else seeds_of(CLOUD)[0]
    mstep = 300_000 if len(logs[CLOUD][mseed]["step"]) >= 30 else 100_000
    charts["cloud_map"] = cloud_figure(f"The cloud and the plant ({CLOUD}, seed {mseed})", f"Left: the rain weight over the world at step {mstep:,} (blue: wet, 2 and above; white: dry, 1/2 and below); right: the soil at the same step (dark: a step of sun's worth or more; the valley's pool is dark everywhere).", f"{WORLDS[CLOUD]['run']}_seed{mseed}", mstep, float(CLOUD_AMP))
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
               + row("Population (coefficient of variation)", "pop|pop_cv", lambda v: f"{v:,.0f}" if v >= 1 else f"{v:.2f}")
               + row("Population, peak over trough within a season of 20,000 steps (median over the second half)", "cycle_swing", d2)
               + row("The ridge's soil follows the cloud (correlation over its cells, median over the dumps from 100,000)", "cloud_corr", d2)
               + row("Lineages alive (median; at the end)", "lineages|lineages_end", d1)
               + row("Distinct winners over the second half; longest hold, steps", "winners|hold", lambda v: f"{v:,.0f}")
               + row("Fat per body; fat, share of the world's matter", "fat|fat_share", lambda v: f"{v:.0%}" if v < 1 else f"{v:.1f}")
               + row("Trees (cells standing at 1 or more)", "trees", n0)
               + row("Bodies standing outside the band they were born in", "movers", p0)
               + row("Bodies with a sensor, share", "sensor_share", p1)
               + row("Bodies with a bite, share; bodies killed per step", "biters|kills", d2)
               + row("Density per body (mean); its spread over bodies", "density|density_std", d2)
               + row("Cells per body; hard blocks per body", "size|hard", d1)
               + row("Intake from other bodies, share of the food eaten", "meat_share", p0)
               + row("Matter at the end over the start", "matter_hold", lambda v: f"{v:.6f}")
               + "</tbody>")

    tables = data_table(["step", "pop", "births", "deaths_energy", "deaths_broken", "sun", "cloud_std", "rain", "regrowth", "fruit_eaten", "trees", "fat_mean", "fat_stock", "matter", "size_mean", "density_mean", "hard_mean", "sensor_agents_share", "plant_intake", "meat_intake", "lineages", "biters_share", "steps_per_sec"],
                        {f"{w}, seed {s} (every 100,000 steps)": logs[w][s] for w in all_worlds for s in seeds_of(w)}, every=10)

    text = TEXT
    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>e026 Weather - Report</title>
<style>{CSS}</style>
</head>
<body>
<main>
<h1>e026: Weather</h1>
<p class="sub">Experiment report - 2026-09-03 - e025's closed world with one law about the world added, in two forms run alone: the cloud (the rain falls where a drifting field says) and the season (the sun's rate a sine of time). The flat world, 500,000 steps, seeds 1-4, five pilots on seed 9, against e025's runs at the same code.</p>

<section class="tldr">
<h2>TL;DR</h2>
<p>{text["tldr"]}</p>
</section>

<h2>1. Question</h2>
<p>{text["question"]}</p>
<ol>
  <li><strong>The world stands.</strong> No death under either form at the amplitude the pilot picks; matter holds to 1e-6.</li>
  <li><strong>The fluctuation is felt.</strong> The cloud: the ridge's soil follows the cloud (correlation over its cells above 0.3). The season: the population moves 20% or more within a cycle.</li>
  <li><strong>No optimum holds.</strong> Lineages alive above e025's 1-5, and the top lineage changes hands over the second half in more seeds than the control.</li>
  <li><strong>Tolerance is selected.</strong> The season: more fat per body or more trees than the control. The cloud: more bodies outside their birth band, or the sensor back (e025: 0.4-6%).</li>
  <li><strong>The hunter state of e025 (four of four) is kept or changed</strong>, recorded either way.</li>
</ol>

<h2>2. The world</h2>
<p>{text["world"]}</p>
{DIAGRAM}
<p>{text["runs"]}</p>
<ul class="measures">
  <li><strong>The weather</strong>: <code>sun</code> (the sun's factor at the log step), <code>cloud_std</code> (the rain weight's spread over the cells), the rain fallen per step on each height band, the field's nodes every 1,000 steps (<code>weather.csv</code>).</li>
  <li><strong>Winners</strong>: lineages alive; the top lineage every 1,000 steps over the second half, its distinct holders and the longest hold.</li>
  <li><strong>Tolerance</strong>: fat per body, trees, bodies standing outside the band they were born in, bodies with a sensor.</li>
  <li>e025's measures otherwise: density, size, hard blocks, biters, kills, worth, meat, population, matter, events, snapshots.</li>
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
{charts["rain"]}{charts["season_zoom"]}
</div>
<p>{text["r3"]}</p>

<h3>3.4 {text["h4"]}</h3>
<div class="grid2">
{charts["lineages"]}{charts["kills"]}
</div>
{gallery(GALLERY)}
<p>{text["r4"]}</p>

<h3>3.5 {text["h5"]}</h3>
<div class="grid2">
{charts["fat"]}{charts["sensor"]}
</div>
{charts["cloud_map"]}
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
<p>Every 100,000th record; full logs in <code>results/*_log.csv</code>, lineages in <code>results/*_lineages.csv</code>, events in <code>results/*_events.csv</code>, bodies with their mass, size and density every 100,000 steps in <code>results/*_agents.csv</code>; the cloud's nodes in <code>results/*_weather.csv</code>; e025's runs (the control) in <code>../e025_weight/results</code>. Build: <code>uv run python experiments/e026_weather/report.py</code>.</p>
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
    (SEASON, 2, 1658, "the gut that holds", "Eleven guts on 2.8 cells, density 1.0, no armor, no muscle: the body of e025's net state. It holds the top place for 302,000 steps in the run with 14 holders."),
    (SEASON, 2, 1139, "the heavy body with an eye", "Four muscle, nine guts and a sensor at density 2.0: its faces resist 2, and it sees two cells. A lineage with a sensor per body for 72,000 steps.", 146_000),
    (SEASON, 3, 606, "the armored body with an eye", "Two hard, three muscle, twelve guts and a sensor at density 1.1, 20 cells: the winner of seed 3 for 423,000 steps, eyed for 125,000 of them.", 140_000),
    (SEASON, 1, 3102, "the bar tooth", "One hard cell at the front, two muscle behind, three guts, seven cells long and one wide, density 2.0: the tooth of e025 at the ceiling, one of six holders in seed 1."),
    (CLOUD, 3, 616, "the eyed column", "Seventeen guts in a column three wide and six long with a sensor, density 1.0: the prey of seed 3's tooth, eyed for 99,000 steps.", 310_000),
    (CLOUD, 4, 222, "the killer without a tooth", "Five muscle and ten guts, no hard block, density 2.0: nothing to bite with, but a face of hardness 2 that breaks the light bodies it walks into. 488,000 steps."),
    (CLOUD, 1, 1455, "the giant", "Fifty-seven cells over 7.6 by 7.7, nineteen muscle and thirty-eight guts at density 2.0, mass 115: the heaviest body of the series, living 190 steps on the dead."),
    (CLOUD, 2, 842, "the tooth", "Two hard cells, two muscle, seven guts at density 1.3, a bite of 0.9: the hunter of seed 2 for 194,000 steps beside a gut of ten cells."),
]

TEXT = {
    "tldr": "Weather is kept, both forms. The cloud (rain where a drifting field says) is felt by the soil and changes little else: 1-2 holders of the top place, as the control. The season (the sun a sine, amplitude 0.5) halves the bodies each winter, turns the winner over in two seeds of four (6 and 14 holders), and brings the eye back: lineages with a sensor per body live 72,000-125,000 steps in four runs of eight, 10,000 at most in the control. Next: room (#33, #28).",
    "question": "Every law of the world has been a fixed field, and one or two bodies win every run. #24: fluctuation is the classic reason several strategies coexist, since no optimum holds long enough to win. Two laws about the world, run alone: the air rains where a cloud says, and the sun has seasons. Hypotheses:",
    "world": "e025's closed world (128x128 on a torus, bodies of 8x8 cells in five kinds grown from the genome, the weight and flesh laws, the canopy, the spill, the air that rains on every cell alike) with one law added per run: the cloud weights the rain, or the season scales the sun.",
    "runs": "<strong>Runs.</strong> Five pilots on seed 9 (<code>cloud</code> 1 and 0.5, <code>season</code> 1, 0.75 and 0.5; 200,000 steps). Then <code>cloud</code> 1 and <code>season</code> 0.5, flat seeds 1-4, 500,000 steps, eight at once (2 hours; 52-113 steps per second). The control is e025's <code>weight 1</code> batch: the same code, weather off, byte for byte.",
    "c1": "yes", "l1": "The world stands", "v1": "No death in eight runs, matter at the end over the start 1.000000, population cv 0.04-0.11.",
    "c2": "yes", "l2": "Both are felt", "v2": "The ridge's soil follows the cloud, correlation 0.42-0.54 over its cells; the season moves the population 2.1-2.5 times within a cycle (control 1.2-1.5).",
    "c3": "partly", "l3": "The season turns the winner over; the cloud does not", "v3": "Season seeds 1 and 2: 6 and 14 holders of the top place over the second half, no hold over 29,000 steps. Cloud: 1-2 holders, as the control's 1-4.",
    "c4": "partly", "l4": "The eye and the fat; not the trees or the movers", "v4": "Lineages with a sensor per body live 72,000-125,000 steps in four runs of eight (control: 10,000 at most); fat per body 5.0-11.5 against 3.3-4.2; trees and movers unchanged.",
    "c5": "yes", "l5": "Kept: kills in eight of eight", "v5": "1.0-3.7 bodies killed a step in every run; in three runs the killing has no tooth (biters under 1%, hard 0.03-0.15).",
    "h1": "The pilots set the amplitudes", "r1": "The season at amplitude 1 kills the world in its first winter: a body's fat is its eater's store, not its own. At 0.75 the world lives through ten winters but falls to 23 bodies in each, a lottery every cycle. At 0.5 it moves 2.8 times within a cycle and keeps six lineages. Both clouds stand; the batch takes the stronger.",
    "h2": "The world stands under both", "r2": "The ledger (left) is flat at 1.000000 in every run: the weather moves matter and makes none. Population (right) is 2,053-4,777; the log samples every 10,000 steps, half a season, so the season's swing is in 3.3. The season worlds hold no fewer bodies than the control.",
    "h3": "Both are felt", "r3": "The rain one cell sees (left) swings between a sixth and three times its mean (once nine) in spells of a few thousand steps, and the ridge's soil follows (correlation 0.42-0.54; the standing plant does not, it is eaten as it grows). The season (right): the bodies halve each winter and double each summer, 2.1-2.5 times per cycle against the control's 1.2-1.5.",
    "h4": "The season turns the winner over; the cloud does not", "r4": "Lineages alive (left) are 2-7 in the weather worlds against 1-5, with 6-8 alive at the end in three runs. The top place changes hands 6 and 14 times over the second half in season seeds 1 and 2, no holder lasting 29,000 steps; the cloud's winners hold 43,000-251,000 steps, as the control's. Kills (right) go on in every run, and in three the killer has no tooth (Figure 2).",
    "h5": "Tolerance: the eye and the fat", "r5": "Fat per body (left) is 5.0-11.5 against the control's 3.3-4.2. The sensor (right): a lineage with a sensor per body lives 72,000-125,000 steps in four weather runs (cloud seed 3, season seeds 2-4) against 10,000 at most in the control; the bodies are a column of guts, an armored body and a heavy one (Figure 2). The map: wet cells dark with soil, dry cells bare.",
    "viewer": "The timeline: season seed 2, the run with 14 holders of the top place. The viewer's long view samples every 10,000 steps, half a season, so it alternates between a summer and a winter frame.",
    "discussion": "<p>The two forms do different things. The cloud moves where the rain falls and the soil records it, but the bodies live on the dead and on the valley's fruit, so a dry ridge costs a walking body little; the winners are the control's. The season moves everyone's income at once and nothing escapes it: the bodies halve each winter, and the lineage on top in summer is not the one on top in winter (14 holders in seed 2).</p><p>The eye came back where it never did: a lineage with a sensor per body for 72,000-125,000 steps in four runs of eight, once under the cloud and three times under the season. A sensor sees food and crowd up to nine cells away; where food moves in time and place, seeing it pays for the block. The pilot at amplitude 1 says the other thing: a body has no store of its own, so a season strong enough to select for one kills the world.</p><p>Not shown: whether the turnover is coexistence or a lottery each winter; the cloud on a mountain world, where rain falls on the ridges only; the amplitude between 0.5 and 0.75.</p>",
    "conclusion": "Both forms are kept (<code>weather</code> cloud 1 or season 0.5; 0 is e025). The season does what #24 asked: no optimum holds through a winter in two seeds of four, and the eye pays for the first time in the series. The cloud is felt by the world, not by the bodies. Next: room (#33 and #28: a bigger grid at the same matter, small and large bodies), where the eye's range has space to matter.",
}


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "lineages":
        top_lineages()
    else:
        main()

