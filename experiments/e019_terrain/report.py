#!/usr/bin/env python3
"""Build report.html for e019.

Charts: matplotlib, exported as SVG and inlined. Diagram: hand-written SVG.
Run from the repo root: uv run python experiments/e019_terrain/report.py
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
from matplotlib.ticker import MaxNLocator

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

E018 = os.path.join(HERE, "..", "e018_closed_cycle")
# Places of a world: (id in the CSVs, name, color). Under the uniform sun a place is a height band (thirds of the cells by the
# terrain); with drawn patches it is the patch's width (0: beyond every patch).
BANDS = [(0, "valleys (lowest third)", SERIES[0]), (1, "slopes (middle third)", SERIES[3]), (2, "ridges (highest third)", SERIES[1])]
PATCHES = [(8, "grass (width 8)", SERIES[0]), (1, "trees (width 1)", SERIES[2]), (0, "beyond the patches", INK)]
# Worlds of this experiment: label -> run prefix, world size, places, seeds, whether the sun is uniform.
WORLDS = {
    "relief 64": dict(run="128_sigma0_r64_f0.1", size=128, places=BANDS, seeds=[1, 2, 3, 4], uniform=True),
    "relief 256": dict(run="128_sigma0_r256_f0.1", size=128, places=BANDS, seeds=[1, 2, 3, 4], uniform=True),
    "flat (relief 0)": dict(run="128_sigma0_r0_f0.1", size=128, places=[], seeds=[1, 2, 3, 4], uniform=True),
    "grass and trees, relief 64": dict(run="128_sigma8-1_r64_f0.1", size=128, places=PATCHES, seeds=[1, 2, 3, 4], uniform=False),
}
UNIFORM = [w for w in WORLDS if WORLDS[w]["uniform"]]
DRAWN = "grass and trees, relief 64"
# e018's runs (the same worlds with no terrain and no flow): label -> (run prefix, folder, uniform).
REFS = {"e018 uniform sun (no flow)": ("128_sigma0", E018, True), "e018 grass and trees (no flow)": ("128_sigma8-1", E018, False)}
WORLD_COLOR = {"relief 64": SERIES[0], "relief 256": SERIES[1], "flat (relief 0)": SERIES[3], "grass and trees, relief 64": SERIES[2],
               "e018 uniform sun (no flow)": INK, "e018 grass and trees (no flow)": "#c6c4bb"}
KIND_COLOR = {1: SERIES[0], 2: SERIES[1], 3: SERIES[3], 4: SERIES[2]}
CONFIRM_STEPS = 5000
MAIN = "relief 64"
VIEWER_WORLD = "relief 64"
VIEWER_SEED = 1
LAST_STEP = 1_000_000


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


def world_chart(title, subtitle, logs, key_fn, worlds, colors, ymin=0, ymax=None, percent=False):
    """One thin line per seed, colored by world; one legend entry per world."""
    fig, ax = new_axes()
    top = 0
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
<svg viewBox="0 0 800 320" role="img" aria-label="A cross-section of the world of e019: a terrain with two ridges and a valley between them, a uniform sun of 0.01 per cell over all of it, soil pooled level in the valley as a lake with plants on every cell of it, a trickle of soil running down the slopes, and bare ridges where the sun is wasted. The flow: each step a cell gives 10% of its soil to the neighbors whose surface (height plus soil) is lower, split by the drop, never more than an eighth of a drop." style="max-width:100%;height:auto;display:block">
<g fill="none" stroke="currentColor" stroke-width="1.2" font-size="12" font-family="system-ui, sans-serif">
  <!-- the sun: the same on every cell -->
  <g stroke="#eda100" stroke-width="1.4">
    <path d="M 60,18 L 60,44 M 120,18 L 120,44 M 180,18 L 180,44 M 240,18 L 240,44 M 300,18 L 300,44 M 360,18 L 360,44 M 420,18 L 420,44 M 480,18 L 480,44 M 540,18 L 540,44 M 600,18 L 600,44 M 660,18 L 660,44 M 720,18 L 720,44" marker-end="url(#sunhead)"/>
  </g>
  <text x="400" y="62" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">sun: 0.01 per cell per step, everywhere</text>
  <text x="400" y="78" text-anchor="middle" fill="currentColor" stroke="none">a plant grows out of the soil of its cell by at most this; on a cell with no soil the sun is wasted</text>

  <!-- the ground -->
  <path d="M 40,190 L 120,120 L 200,80 L 280,130 L 340,190 L 400,235 L 460,205 L 520,150 L 600,100 L 680,140 L 760,185 L 760,320 L 40,320 Z" fill="var(--cell)" stroke="currentColor" stroke-width="1.5"/>
  <!-- the lake of soil, level -->
  <path d="M 320,170 L 340,190 L 400,235 L 460,205 L 498,170 Z" fill="#b5773a" fill-opacity="0.75" stroke="#b5773a" stroke-width="1"/>
  <!-- a trickle of soil on the slopes -->
  <path d="M 200,80 L 280,130 L 320,170" stroke="#b5773a" stroke-width="4" stroke-opacity="0.55" stroke-linecap="round"/>
  <path d="M 600,100 L 520,150 L 498,170" stroke="#b5773a" stroke-width="4" stroke-opacity="0.55" stroke-linecap="round"/>
  <!-- plants: on every cell of the lake, a few on the trickle, none on the ridges -->
  <g stroke="#1baf7a" stroke-width="2" stroke-linecap="round">
    <path d="M 330,170 L 330,160 M 350,170 L 350,158 M 370,170 L 370,160 M 390,170 L 390,157 M 410,170 L 410,160 M 430,170 L 430,158 M 450,170 L 450,160 M 470,170 L 470,158 M 490,170 L 490,161"/>
    <path d="M 262,119 L 265,110 M 296,148 L 299,139 M 540,135 L 537,126 M 508,161 L 511,152"/>
  </g>
  <!-- the flow arrows -->
  <path d="M 230,92 L 262,112" stroke="#b5773a" stroke-width="1.6" marker-end="url(#flowhead)"/>
  <path d="M 300,148 L 318,166" stroke="#b5773a" stroke-width="1.6" marker-end="url(#flowhead)"/>
  <path d="M 575,116 L 545,136" stroke="#b5773a" stroke-width="1.6" marker-end="url(#flowhead)"/>
  <!-- a body -->
  <rect x="404" y="147" width="22" height="11" rx="1.5" fill="var(--s1)" stroke="none"/>
  <path d="M 415,160 L 415,168" stroke="var(--s1)" stroke-width="1.6" marker-end="url(#bodyhead)"/>

  <!-- labels -->
  <text x="200" y="104" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">ridge</text>
  <text x="200" y="120" text-anchor="middle" fill="currentColor" stroke="none">no soil stays,</text>
  <text x="200" y="136" text-anchor="middle" fill="currentColor" stroke="none">the sun is wasted</text>
  <text x="600" y="122" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">ridge</text>
  <text x="48" y="196" fill="currentColor" stroke="none" font-weight="600">flow</text>
  <text x="48" y="212" fill="currentColor" stroke="none">each step a cell gives 10% of its soil</text>
  <text x="48" y="228" fill="currentColor" stroke="none">to the neighbors whose surface is lower,</text>
  <text x="48" y="244" fill="currentColor" stroke="none">split by the drop, at most 1/8 of a drop</text>
  <text x="48" y="260" fill="currentColor" stroke="none">(surface = height + soil, so a pool levels)</text>
  <text x="409" y="276" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">the lake</text>
  <text x="409" y="292" text-anchor="middle" fill="currentColor" stroke="none">soil pooled level over many cells; every cell of it grows 0.01 per step</text>
  <text x="409" y="308" text-anchor="middle" fill="currentColor" stroke="none">a body eats here and spends here; what it spends stays in the lake</text>
  <text x="556" y="196" fill="currentColor" stroke="none">heights are in soil: one unit</text>
  <text x="556" y="212" fill="currentColor" stroke="none">of soil raises a surface by one;</text>
  <text x="556" y="228" fill="currentColor" stroke="none">the relief (lowest to highest)</text>
  <text x="556" y="244" fill="currentColor" stroke="none">is 64 or 256, the soil 8 per cell</text>
</g>
<defs>
  <marker id="sunhead" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="#eda100"/></marker>
  <marker id="flowhead" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="#b5773a"/></marker>
  <marker id="bodyhead" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="var(--s1)"/></marker>
</defs>
</svg>
<figcaption>Figure 1. The world in cross-section. e018's closed cycle (matter is in the soil of a cell, in the plant on it, lying dead on it, or in a body; a plant grows out of its own cell's soil at most the sun's rate; what a body spends falls to the soil under it; the dead rot into it) with one law added: the ground has a height, and soil runs downhill. The surface of a cell is its height plus its soil; each step a cell gives 10% of its soil to the neighbors whose surface is lower, split by the drop to each, never more than an eighth of a drop, so that soil pools level where it collects. Only soil moves. The sun is the same on every cell, so the places are made by the water: a lake of soil in the low ground where every cell grows, a trickle on the slopes, bare ridges. With drawn patches (the fourth world) the sun is e018's grass and trees over the same terrain.</figcaption>
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
    """picks: [(world, seed, lineage id, name, what the shape does)]. The most common body of each lineage at its peak, on the 8x8 grid, front up."""
    cards = []
    cache = {}
    for world, seed, lid, name, what in picks:
        run = f"{WORLDS[world]['run']}_seed{seed}"
        if run not in cache:
            cache[run] = (lineage_rows(run), load_bodies(run), list(read_frames(f"results/{run}_long.jsonl")))
        by, bodies, frames = cache[run]
        rows = by[lid]
        peak = max(rows, key=lambda r: int(r["size"]))
        span = int(rows[-1]["step"]) - int(rows[0]["step"]) + CONFIRM_STEPS
        frame = min(frames, key=lambda fr: abs(fr["step"] - int(peak["step"])))
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
<figcaption><strong>{html.escape(name)}</strong><br>{html.escape(world)}, seed {seed}, lineage {lid}: {span:,} steps, {int(peak["size"]):,} agents at its peak, {home}{height}<br>mass {float(peak["mass"]):.0f} on {float(peak["foot"]):.1f} cells: hard {float(peak["hard"]):.0f}, muscle {float(peak["muscle"]):.0f}, digestive {float(peak["digestive"]):.0f}; dead matter {meat:.0%} of the intake<br>{html.escape(what)}</figcaption></figure>""")
    return f"""<figure class="diagram"><div class="cards">{"".join(cards)}</div>
<figcaption>Figure 2. Bodies of lineages that prospered: the most common body of the lineage at its peak, on the 8x8 grid a body grows on, front up (the dashed edge). Blue: hard, orange: muscle, green: digestive, yellow: sensor. "Cells" is the world cells the body covers; "dead matter" the share of the lineage's lifetime intake that was dead bodies; the height is the terrain under the lineage's members at its peak (relief 64 or 256).</figcaption></figure>"""


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


def main():
    logs, events, places = {}, {}, {}
    for w, d in WORLDS.items():
        seeds = seeds_of(w)
        logs[w] = {s: load_csv(f"results/{d['run']}_seed{s}_log.csv") for s in seeds}
        events[w] = {s: load_rows(f"results/{d['run']}_seed{s}_events.csv") for s in seeds}
        places[w] = {s: load_places(f"{d['run']}_seed{s}") for s in seeds}
    rlogs = {w: {s: load_csv(f"results/{run}_seed{s}_log.csv", folder) for s in [1, 2, 3, 4]} for w, (run, folder, _) in REFS.items()}
    rplaces = {w: {s: load_places(f"{run}_seed{s}", folder) for s in [1, 2, 3, 4]} for w, (run, folder, _) in REFS.items()}
    STATS = {w: {s: soil_stats(f"{WORLDS[w]['run']}_seed{s}", WORLDS[w]["size"], WORLDS[w]["uniform"]) for s in seeds_of(w)} for w in WORLDS}

    def med(x):
        x = [v for v in x if v == v]
        return statistics.median(x) if x else float("nan")

    def half(d, key):
        n = len(d["step"])
        return d[key][n // 2:]

    def quarters(d, key):
        n = len(d["step"])
        return d[key][n // 2: 3 * n // 4], d[key][3 * n // 4:]

    def eaten_of(d):
        return [(p + m) / 10_000 for p, m in zip(d["plant_intake"], d["meat_intake"])]

    def summarize(w, s):
        log = logs[w][s]
        run = f"{WORLDS[w]['run']}_seed{s}"
        pl = places[w][s]
        st = STATS[w][s]
        first, last, _ = lineage_stats(run)
        per_step = Counter(int(r["step"]) for r in load_rows(f"results/{run}_lineages.csv"))
        last_step = int(log["step"][-1])
        pop = half(log, "pop")
        sun = [r + sh + wa + b for r, sh, wa, b in zip(log["regrowth"], log["shaded"], log["wasted"], log["barren"])]
        eaten = eaten_of(log)
        n = len(eaten)
        end = st[-1] if st else None
        d = dict(pop=med(pop), pop_min=min(log["pop"]), pop_cv=statistics.pstdev(pop) / max(statistics.mean(pop), 1), pop_swing=max(pop) / max(min(pop), 1),
                 extinct=last_step < LAST_STEP, extinct_at=last_step if last_step < LAST_STEP else float("nan"), sps=med(log["steps_per_sec"]),
                 lineages=med([per_step.get(t, 0) for t in range(1000, last_step + 1, 1000)]), ids=len(first),
                 contacts=med([c / max(p, 1) / 10_000 for c, p in zip(half(log, "contacts"), pop)]), forward=med(half(log, "forward")),
                 mass=med(half(log, "mass_mean")), hard=med(half(log, "hard_mean")), muscle=med(half(log, "muscle_mean")), foot=med(half(log, "foot_mean")),
                 eaten=med(eaten[n // 2:]), eaten_q3=med(eaten[n // 2: 3 * n // 4]), eaten_q4=med(eaten[3 * n // 4:]),
                 steady=med(eaten[3 * n // 4:]) / max(med(eaten[n // 2: 3 * n // 4]), 1e-9),
                 barren=med([b / max(t, 1e-9) for b, t in zip(half(log, "barren"), sun[len(sun) // 2:])]), barren_abs=med(half(log, "barren")),
                 shaded=med([b / max(t, 1e-9) for b, t in zip(half(log, "shaded"), sun[len(sun) // 2:])]), regrowth=med(half(log, "regrowth")),
                 spent=med(half(log, "spent")), flow=med(half(log, "flow")), soil_cells=med(half(log, "soil_cells")), deep=med(half(log, "deep")),
                 matter_hold=log["matter"][-1] / log["matter"][0],
                 top=end["top"] if end else float("nan"), top_first=st[0]["top"] if st else float("nan"), wet=end["wet"] if end else float("nan"),
                 under=end["under"] / max(end["free"], 1e-9) if end else float("nan"))
        if end:
            for p, e in end["by"].items():
                d[f"soilend_{p}"] = e["soil"]
                d[f"soilshare_{p}"] = e["soil_share"]
                d[f"popshare_{p}"] = e["pop_share"]
                d[f"bare_{p}"] = e["bare"]
                d[f"wet_{p}"] = e["wet"]
            if WORLDS[w]["uniform"] and WORLDS[w]["places"]:
                d["low_soil"] = end["by"].get(0, {}).get("soil_share", 0) + end["by"].get(1, {}).get("soil_share", 0)
                d["low_pop"] = end["by"].get(0, {}).get("pop_share", 0) + end["by"].get(1, {}).get("pop_share", 0)
        for p, _, _ in WORLDS[w]["places"]:
            if p not in pl:
                continue
            q = pl[p]
            m = len(q["step"])
            h = slice(m // 2, m)
            d[f"pop_{p}"] = med(q["pop"][h])
            d[f"mass_{p}"] = med(q["mass"][h])
            d[f"digestive_{p}"] = med(q["digestive"][h])
            d[f"lineages_{p}"] = med(q["lineages"][h])
            d[f"eaten_{p}"] = med([(a_ + b_) / 10_000 for a_, b_ in zip(q["plant_intake"][h], q["meat_intake"][h])])
            d[f"barren_{p}"] = med(q["barren"][h])
            d[f"regrowth_{p}"] = med(q["regrowth"][h])
            d[f"soilcell_{p}"] = med([so / c for so, c in zip(q["soil"][h], q["cells"][h])])
        if not WORLDS[w]["uniform"]:
            d["trees_pop"] = d.get("pop_1", float("nan"))
            d["trees_eaten"] = d.get("eaten_1", float("nan"))
            d["grass_pop"] = d.get("pop_8", float("nan"))
            d["grass_eaten"] = d.get("eaten_8", float("nan"))
        return d

    S = {w: {s: summarize(w, s) for s in seeds_of(w)} for w in WORLDS}

    def rsum(w, key):
        """A reference world's value: median over seeds of the median over the second half."""
        L = rlogs[w]
        seeds = [1, 2, 3, 4]
        if key == "contacts":
            return med([med([c / max(p, 1) / 10_000 for c, p in zip(half(L[s], "contacts"), half(L[s], "pop"))]) for s in seeds])
        if key == "eaten":
            return med([med(eaten_of(L[s])[len(L[s]["step"]) // 2:]) for s in seeds])
        if key == "steady":
            out = []
            for s in seeds:
                e = eaten_of(L[s])
                n = len(e)
                out.append(med(e[3 * n // 4:]) / max(med(e[n // 2: 3 * n // 4]), 1e-9))
            return med(out)
        if key == "pop_cv":
            return med([statistics.pstdev(half(L[s], "pop")) / statistics.mean(half(L[s], "pop")) for s in seeds])
        if key == "pop_swing":
            return med([max(half(L[s], "pop")) / min(half(L[s], "pop")) for s in seeds])
        if key in ("barren", "shaded"):
            out = []
            for s in seeds:
                sun = [r + sh + wa + b for r, sh, wa, b in zip(L[s]["regrowth"], L[s]["shaded"], L[s]["wasted"], L[s]["barren"])]
                out.append(med([b / max(t, 1e-9) for b, t in zip(half(L[s], key), sun[len(sun) // 2:])]))
            return med(out)
        if key in ("trees_pop", "trees_eaten", "grass_pop", "grass_eaten"):
            if REFS[w][2]:
                return float("nan")
            p = 1 if key.startswith("trees") else 8
            col = "pop" if key.endswith("pop") else "eaten"
            out = []
            for s in seeds:
                q = rplaces[w][s].get(p)
                if not q:
                    continue
                m = len(q["step"])
                h = slice(m // 2, m)
                out.append(med(q["pop"][h]) if col == "pop" else med([(a_ + b_) / 10_000 for a_, b_ in zip(q["plant_intake"][h], q["meat_intake"][h])]))
            return med(out)
        if key == "mass":
            key = "mass_mean"
        if key not in L[1]:
            return float("nan")
        return med([med(half(L[s], key)) for s in seeds])

    logs_ref = dict(logs)
    logs_ref.update({w: rlogs[w] for w in REFS})
    all_worlds = list(WORLDS) + list(REFS)
    ref_u = "e018 uniform sun (no flow)"
    ref_d = "e018 grass and trees (no flow)"

    charts = {}
    charts["eaten"] = world_chart("Food eaten per step", "Plant and dead matter taken by guts per step, one line per run; gray: e018's uniform sun (dark) and grass and trees (light), where nothing flowed. The sun gives 164 per step in every world. A line that ends is a world that died.", logs_ref, eaten_of, all_worlds, WORLD_COLOR)
    charts["pop"] = world_chart("Population", "Bodies alive at each log step, one line per run; gray: e018's runs of the same worlds without the flow.", logs_ref, lambda l: l["pop"], all_worlds, WORLD_COLOR)
    charts["barren"] = world_chart("Sun lost to empty soil", "Share of the sun that shone on a cell whose soil had nothing left, per log window, one line per run; gray: e018. Under the uniform sun this is the ridges; with drawn patches, a patch standing on high ground.", logs_ref, lambda l: [b / max(r + sh + wa + b, 1e-9) for r, sh, wa, b in zip(l["regrowth"], l["shaded"], l["wasted"], l["barren"])], all_worlds, WORLD_COLOR, percent=True)
    charts["soil_cells"] = world_chart("Cells with soil", "Share of the cells holding at least a step of sun's worth of soil (0.01), at each log step, one line per run: the area of the world that can grow a plant this step. Under a uniform sun the food supply is this share times 164, less what bodies stand on.", logs, lambda l: l["soil_cells"], list(WORLDS), WORLD_COLOR, percent=True, ymax=1.0)
    charts["soil_band"] = place_chart("Soil per cell by height, relief 64", "Matter in the soil per cell of each height band (thirds of the cells by the terrain), at each log step, one line per seed. The world started with 8 per cell in plants and none in the soil.", places, "relief 64", lambda d: [so / c for so, c in zip(d["soil"], d["cells"])])
    charts["pop_band"] = place_chart("Bodies by height, relief 64", "Bodies standing in each height band at each log step, one line per seed. The bands are equal in cells (5,461 each).", places, "relief 64", lambda d: d["pop"])
    charts["soil_band256"] = place_chart("Soil per cell by height, relief 256", "The same at four times the relief: the lake is deeper and covers a third of the world instead of two thirds.", places, "relief 256", lambda d: [so / c for so, c in zip(d["soil"], d["cells"])])
    charts["pop_band256"] = place_chart("Bodies by height, relief 256", "Bodies standing in each height band at each log step, one line per seed.", places, "relief 256", lambda d: d["pop"])
    charts["eaten_band"] = place_chart("Food eaten per step by height, relief 64", "Plant and dead matter eaten per step by the bodies standing in each band, one line per seed. Each band gets 54.6 of sun per step.", places, "relief 64", lambda d: [(a + b) / 10_000 for a, b in zip(d["plant_intake"], d["meat_intake"])])
    charts["top"] = stats_chart("Where the soil lies: the richest tenth of the cells", "Share of the world's soil held by its richest tenth of cells, every 100,000 steps, one line per run. 10% is a flat world; a lake that covers two thirds of the world reads about 30%, one that covers a third about 60%.", STATS, lambda d: d["top"], list(WORLDS), percent=True, ymax=1.0)
    charts["under"] = stats_chart("Soil under the bodies over soil elsewhere", "Mean soil of the cells with a body on them over the mean of the cells without, every 100,000 steps, one line per run. Above 1, bodies stand where the soil is: on the lake.", STATS, lambda d: d["under"] / max(d["free"], 1e-9), list(WORLDS), ymin=0)
    charts["maps"] = terrain_soil_figure("The terrain and the soil at the end", "Top: the terrain of seed 1 of each world (white high, black low; the flat world is all one height). Bottom: soil per cell at step 1,000,000 (or the last dump before the world died), darker is more (log scale, 30 and above black); dashed rings are the patches at that step in the grass and trees world (blue: grass, aqua: trees, radius two widths).", [(w, 1) for w in WORLDS])
    charts["lineages"] = world_chart("Lineages alive", "Confirmed lineages at each log step, one line per run; gray: e018 (uniform sun 1; grass and trees 2).", logs_ref, lambda l: l["lineages"], all_worlds, WORLD_COLOR)
    charts["trees"] = place_lines_chart("Bodies on the trees", "Bodies standing on the tree patches (width 1) at each log step, one line per seed: the grass and trees world over the terrain, and e018's without it (gray). e017, where the sun regrew every cell whatever its soil: 37.", [(DRAWN, WORLD_COLOR[DRAWN], places[DRAWN], 1), (ref_d, INK, rplaces[ref_d], 1)], lambda d: d["pop"])
    charts["grass"] = place_lines_chart("Food eaten on the grass per step", "Plant and dead matter eaten per step by the bodies on the grass patches (width 8), one line per seed: over the terrain, and e018's without it (gray). e017: 32.", [(DRAWN, WORLD_COLOR[DRAWN], places[DRAWN], 8), (ref_d, INK, rplaces[ref_d], 8)], lambda d: [(a + b) / 10_000 for a, b in zip(d["plant_intake"], d["meat_intake"])])

    vseed = VIEWER_SEED if VIEWER_SEED in events[VIEWER_WORLD] else seeds_of(VIEWER_WORLD)[0]  # a dry run may lack the viewer's seed
    viewer_run = f"{WORLDS[VIEWER_WORLD]['run']}_seed{vseed}"
    timeline = timeline_chart(f"Lineages over time ({VIEWER_WORLD}, seed {vseed})", "Each colored band is one lineage, height = agents in it; marks are events at the size they were logged with.", viewer_run, events[VIEWER_WORLD][vseed])

    first, _, _ = lineage_stats(viewer_run)
    bodies = load_bodies(viewer_run)
    data = bytearray()
    long_frames, used_l = pack_frames(f"results/{viewer_run}_long.jsonl", first, data, every=2)
    clip_frames, used_c = pack_frames(f"results/{viewer_run}_clip.jsonl", first, data, every=4, limit=50)
    # The terrain as a static layer: 16 levels of height, packed like the food.
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
        vals = [S[w][s].get(key, float("nan")) for s in seeds_of(w)]
        vals = [v for v in vals if v == v]
        if not vals:
            return "-"
        lo, hi = min(vals), max(vals)
        return fmt(lo) if fmt(lo) == fmt(hi) else f"{fmt(lo)}-{fmt(hi)}"

    def row(label, keys, fmt, refkey=None):
        """keys: one key (or several separated by "|", one range each) for every world, or {world: keys}."""
        cells = ""
        for w in WORLDS:
            k = keys.get(w, "") if isinstance(keys, dict) else keys
            cells += "<td>" + (" / ".join(rng(w, kk, fmt) for kk in k.split("|")) if k else "-") + "</td>"
        f_ = lambda v: "-" if v != v else fmt(v)
        refs = "".join(f"<td>{f_(rsum(r, refkey))}</td>" if refkey else "<td>-</td>" for r in REFS)
        return f"<tr><td>{label}</td>{cells}{refs}</tr>"

    n0 = lambda v: f"{v:,.0f}"
    d1 = lambda v: f"{v:.1f}"
    d2 = lambda v: f"{v:.2f}"
    d3 = lambda v: f"{v:.3f}"
    p0 = lambda v: f"{v:.0%}"
    by_band = lambda k: {w: f"{k}_0|{k}_1|{k}_2" for w in UNIFORM if WORLDS[w]["places"]} | {DRAWN: f"{k}_8|{k}_1|{k}_0"}
    uniform_only = lambda k: {w: k for w in UNIFORM if WORLDS[w]["places"]}
    summary = ("<thead><tr><th>Measure (range over seeds, median over the second half unless said)</th>" + "".join(f"<th>{w}</th>" for w in WORLDS) + "".join(f"<th>{r}</th>" for r in REFS) + "</tr></thead><tbody>"
               + row("Population", "pop", n0, "pop")
               + row("Population, coefficient of variation", "pop_cv", d2, "pop_cv")
               + row("Population, largest over smallest", "pop_swing", d1, "pop_swing")
               + row("Died at step", "extinct_at", n0)
               + row("Food eaten per step", "eaten", d1, "eaten")
               + row("Food eaten, last quarter over third quarter", "steady", d2, "steady")
               + row("Sun lost to empty soil, share of the sun", "barren", p0, "barren")
               + row("Sun lost to bodies standing on cells, share", "shaded", p0, "shaded")
               + row("Cells with soil (0.01 or more), share", "soil_cells", p0)
               + row("Soil per cell at the end: valleys / slopes / ridges (grass / trees / beyond)", by_band("soilend"), d1)
               + row("Bodies: valleys / slopes / ridges (grass / trees / beyond)", by_band("pop"), n0)
               + row("Soil in the lowest two thirds of the cells at the end, share", uniform_only("low_soil"), p0)
               + row("Bodies in the lowest two thirds at the end, share", uniform_only("low_pop"), p0)
               + row("Bodies on the trees", {DRAWN: "trees_pop"}, n0, "trees_pop")
               + row("Eaten on the trees per step", {DRAWN: "trees_eaten"}, d1, "trees_eaten")
               + row("Richest tenth of the cells, share of the soil at the end", "top", p0)
               + row("Soil under the bodies over soil elsewhere, at the end", "under", d2)
               + row("Soil moved per step", "flow", d1)
               + row("Matter at the end over the start", "matter_hold", lambda v: f"{v:.4f}")
               + row("Lineages alive", "lineages", n0, "lineages")
               + row("Mass", "mass", d1, "mass")
               + row("Contacts per body per step", "contacts", d3, "contacts")
               + row("Steps per second", "sps", n0, "steps_per_sec")
               + "</tbody>")

    tables = data_table(["step", "place", "pop", "mass", "hard", "muscle", "digestive", "cover", "foot", "plant_intake", "meat_intake", "dead", "carrion", "soil", "barren", "regrowth", "cells", "lineages", "movers"],
                        {f"{w}, seed {s}, {place_names(w)[p]} (every 100,000 steps)": places[w][s][p] for w in WORLDS for s in seeds_of(w) for p, _, _ in WORLDS[w]["places"] if p in places[w][s]}, every=10)
    tables += data_table(["step", "pop", "births", "deaths_energy", "mass_mean", "forward", "blocked", "foot_mean", "cover", "contacts", "regrowth", "shaded", "wasted", "barren", "rot", "spent", "flow", "soil_cells", "deep", "soil", "matter", "plant_intake", "meat_intake", "lineages", "steps_per_sec"],
                         {f"{w}, seed {s}, whole world (every 100,000 steps)": logs[w][s] for w in WORLDS for s in seeds_of(w)}, every=10)

    text = TEXT
    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>e019 Matter that flows: a terrain the soil runs down - Report</title>
<style>{CSS}</style>
</head>
<body>
<main>
<h1>e019: Matter that flows: a terrain the soil runs down</h1>
<p class="sub">Experiment report - 2026-08-31 - e018's closed world with one law added: the ground has a height, and soil runs downhill. A uniform sun over a terrain of relief 64 and 256, a flat world with the same flow, and grass and trees over the relief 64 terrain, 128x128, four seeds each, 1,000,000 steps</p>

<section class="tldr">
<h2>TL;DR</h2>
<p>{text["tldr"]}</p>
</section>

<h2>1. Question</h2>
<p>{text["question"]}</p>
<ol>
  <li><strong>The flow ends the fall.</strong> Under the uniform sun at relief 64 the food eaten per step is steady over the second half (the medians of the third and fourth quarters within 10%; e018's uniform world fell from 110 to 50-105 and was still falling) and so is the sun lost to empty soil; the population is 1,400-1,800 with a coefficient of variation under 0.10.</li>
  <li><strong>The places are the valleys.</strong> At relief 64 the lowest two thirds of the cells hold over 95% of the soil and over 90% of the bodies and the ridges are bare (soil under 0.1 per cell); at relief 256 the lake covers about a third of the world and holds 500-700 bodies. The richest tenth of the cells holds about 30% of the soil at relief 64 and about 60% at relief 256: the soil map is the terrain upside down.</li>
  <li><strong>A lake is not a tree.</strong> No cell grows faster than the sun, so no valley cell becomes a rich cell: the bodies on the lake are e018's small movers (mass 6-9), contacts under 0.05 per body per step, 1-2 lineages alive per run (e018's uniform world: 1). The terrain alone under a uniform sun does not make more winners; it makes the world stand.</li>
  <li><strong>The flow gives the grass back but not the trees.</strong> With the drawn sun at relief 64 the grass eats 28-34 per step (e018: 23-26, e017: 36) and holds 500-650 bodies; the trees stay empty (0-10 bodies) because a tree cell's 6.5 of sun empties a cell faster than its neighbors' soil runs in.</li>
  <li><strong>Leveling alone makes a lawn.</strong> With no terrain (relief 0) and the same flow, over 95% of the cells hold soil, the world eats 100-120 per step and holds 1,800-2,200 bodies, one lineage; e018's trails do not form.</li>
  <li><strong>The world holds.</strong> Matter is conserved to 0.1%, and the flow costs under 10% of the step time.</li>
</ol>

<h2>2. The world</h2>
<p>{text["world"]}</p>
{DIAGRAM}
<p>{text["runs"]}</p>
<ul class="measures">
  <li><strong>Flow</strong> (<code>flow</code>): soil moved per step. <strong>Cells with soil</strong> (<code>soil_cells</code>): share of the cells holding 0.01 or more, a step of sun's worth; <code>deep</code>: 8 or more, a full plant's worth.</li>
  <li><strong>Places by height</strong>: under the uniform sun the place of a cell is its band (the lowest third of the cells by the terrain, the middle third, the highest third), so the per-place log (population, body means, intake, soil, barren sun, lineages, movers) reads by height. With drawn patches the places are the patches, as before. Each agent and lineage also carries the terrain height under it.</li>
  <li><strong>The terrain</strong> (<code>terrain.json</code>, once per run): height and band of every cell. <strong>The soil map</strong> (<code>soil.jsonl</code>, every 100,000 steps): the share of the soil in the richest tenth of the cells, the soil per cell and its share per place, the share of the bodies standing in each place, the shares of bare (under 1) and wet (0.01 or more) cells, and the soil under the bodies over the soil elsewhere.</li>
  <li>e018's measures: sun split into grown, shaded, wasted and barren; soil, spent, rot, matter; population, food eaten, dead matter, contacts, moves, lineages and events, snapshots (now with the terrain as a layer).</li>
</ul>

<h2>3. Results</h2>
<div class="tw"><table>{summary}</table></div>
<ol class="verdicts">
<li><span class="verdict {text["c1"]}">{text["l1"]}</span> {text["v1"]}</li>
<li><span class="verdict {text["c2"]}">{text["l2"]}</span> {text["v2"]}</li>
<li><span class="verdict {text["c3"]}">{text["l3"]}</span> {text["v3"]}</li>
<li><span class="verdict {text["c4"]}">{text["l4"]}</span> {text["v4"]}</li>
<li><span class="verdict {text["c5"]}">{text["l5"]}</span> {text["v5"]}</li>
<li><span class="verdict {text["c6"]}">{text["l6"]}</span> {text["v6"]}</li>
</ol>

<h3>3.1 {text["h1"]}</h3>
<div class="grid2">
{charts["eaten"]}{charts["soil_cells"]}
</div>
<div class="grid2">
{charts["barren"]}{charts["pop"]}
</div>
<p>{text["r1"]}</p>

<h3>3.2 {text["h2"]}</h3>
<div class="wide">{charts["maps"]}</div>
<div class="grid2">
{charts["soil_band"]}{charts["pop_band"]}
</div>
<div class="grid2">
{charts["soil_band256"]}{charts["pop_band256"]}
</div>
<div class="grid2">
{charts["top"]}{charts["under"]}
</div>
<p>{text["r2"]}</p>

<h3>3.3 {text["h3"]}</h3>
<div class="grid2">
{charts["eaten_band"]}{charts["lineages"]}
</div>
<p>{text["r3"]}</p>

<h3>3.4 {text["h4"]}</h3>
<div class="grid2">
{charts["grass"]}{charts["trees"]}
</div>
<p>{text["r4"]}</p>

<h3>3.5 {text["h5"]}</h3>
{gallery(GALLERY)}
<p>{text["r5"]}</p>

<h3>3.6 Watching the world</h3>
<div class="wide">{timeline}</div>
<div class="viewer">
  <div class="canvases">
    <canvas id="world" width="1024" height="1024"></canvas>
    <canvas id="zoom" width="480" height="480"></canvas>
  </div>
  <div class="bar">
    <button id="play">Play</button>
    <select id="mode"><option value="long">Long view: every 10,000 steps</option><option value="clip">Clip: every 4th step from 600,000</option></select>
    <select id="layer"><option value="food">Ground: food</option><option value="soil">Ground: soil (long view)</option><option value="terrain">Ground: terrain (height)</option></select>
    <select id="speed"><option value="1">Slow</option><option value="2">Normal</option><option value="4">Fast</option></select>
    <span id="steplbl"></span>
  </div>
  <div class="bar"><input id="scrub" type="range" min="0" max="0" value="0"></div>
  <div class="bar" id="linlbl"></div>
  <div class="bar" id="legend">Blocks: {legend} <span class="sw front"></span> the front (white edge) <span class="sw dot"></span> has a bite on the front</div>
  <div class="bar">Left: the whole {vw}x{vw} world at the resolution of the body ({vw * 4}x{vw * 4} sub-cells), every cell a body holds colored by its lineage (gray: none), a white dot on bodies with a bite. The ground is food (green: plant and dead matter in one) or, with the selector, the soil (brown, log scale; the long view only) or the terrain (blue-gray, lighter is higher). Click to move the white box. Right: the box at 24x24 world cells, each body drawn cell by cell where it stands, turned the way it faces, with a white edge on its front. Labels: agents per lineage, then mean mass, cells spanned along x across the facing, bite, shell, and sensor cells. {VIEWER_WORLD}, seed {vseed}.</div>
</div>
<p>{text["viewer"]}</p>

<h2>4. Discussion</h2>
{text["discussion"]}

<h2>5. Conclusion and next step</h2>
<p>{text["conclusion"]}</p>

<h2>Appendix: data</h2>
<p>Every 100,000th record; full logs in <code>results/*_log.csv</code>, per place in <code>results/*_places.csv</code>, lineages in <code>results/*_lineages.csv</code>, events in <code>results/*_events.csv</code>, agents every 100,000 steps in <code>results/*_agents.csv</code>, the terrain in <code>results/*_terrain.json</code>, the soil and plants of every cell every 100,000 steps in <code>results/*_soil.jsonl</code>, snapshots in <code>results/*_{{long,clip,bodies}}.jsonl</code>. Reference runs are read from <code>../e018_closed_cycle/results</code>. Build this report with <code>uv run python experiments/e019_terrain/report.py</code>.</p>
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
    ("relief 64", 1, 1, "the bar on the lake", "Six digestive cells in a row 1 deep and 7 wide over 2.6 world cells: the one lineage of seed 1 for the whole run, 1,616 agents at its peak, half of them in the valleys and half on the slopes, none on the ridges. e018's mower with a shore to stop at."),
    ("relief 64", 3, 1, "the block", "Ten digestive cells 2 deep and 6 wide over 2.8 world cells, the one lineage of seed 3 for the whole run (1,337 at its peak): the largest body of the uniform worlds, in the run whose lake is the smallest (54% of the cells, 56 eaten per step)."),
    ("relief 256", 1, 67, "the second bar, higher up", "Eight digestive cells 2 by 8 over 3.4 world cells, 324,000 steps beside lineage 2 at 127 agents: the one second lineage of the deep-lake worlds, the same body as the first, its members standing higher (height 71 against 59) on a lake whose surface is one height."),
    ("relief 256", 2, 8, "the thin bar", "Seven digestive cells in a single row of 8, the whole width of the grid as a front, over 2.8 world cells: the one lineage of seed 2 from step 5,000 to the end, 600 agents at its peak, every one of them in the valleys, where the lake is."),
    ("flat (relief 0)", 1, 2, "the lawn's bar", "Seven digestive cells 1 by 8 over 2.9 world cells, the one lineage of the flat world (2,177 agents at its peak), spread evenly over the three thirds of a world whose soil is 8.1 on every cell. The same body as in the lake, in a world with no edge."),
    ("grass and trees, relief 64", 4, 17, "the block on the drifting grass", "Eight digestive cells 3 by 3 over 2.5 world cells, 447,000 steps and 546 agents at its peak on the grass: e016-e018's wedge in a world where the grass eats 13 per step and the population falls to 25 when the patches climb out of the lake."),
]


TEXT = {
    "question": "e018 closed the cycle of matter and the world got poorer: a plant that grows only out of its own cell's soil makes the sun a pump that empties each cell once, after which the world eats what its bodies spend, a third of the sun falls on empty cells, the trees lose their bodies, lineages fall to 1-3, and under a uniform sun the soil weaves into the bodies' trails while the food supply falls through the run. Matter moved only inside a body. This experiment adds the real world's other mover (issue #22): the ground has a height, and soil runs downhill. A terrain of smooth noise, a relief in soil units, a surface that is height plus soil, and each step a tenth of a cell's soil given to the lower neighbors by the drop, never more than an eighth of a drop, so that soil pools level. The sun is uniform: the places are the valleys, drawn by the flow. Sixteen runs: the uniform sun at relief 64 and 256, a flat world with the same flow (leveling alone), and e018's grass and trees over the relief 64 terrain, four seeds each. The hypotheses:",
    "world": "Everything is e018's (128x128 on a torus, matter 8 per cell at the start as plants, bodies of 8x8 cells in five kinds grown from the genome, space at the resolution of the body, a facing, e010's contact rule, a cell that costs what it holds, 0.032 per body per step, work = force x distance, a cell held by a body does not regrow, a dead body is food where it lies, a plant grows out of its own cell's soil at most the sun's rate, what a body spends falls to the soil under it, the dead rot into it) with a height per cell and the flow added (Figure 1). Two new arguments: the relief (0: flat) and the flow (0: e018; 0.1 here, since 0.01 and 1 gave the same world in the pilot). Under the uniform sun the place of a cell is its height band, thirds of the cells by the terrain: valleys, slopes, ridges.",
    "runs": "<strong>Runs.</strong> The uniform sun at relief 64 and 256 and with no terrain (relief 0), twelve runs at once on one machine, one thread each, 40-60 minutes; grass and trees (widths 8 and 1) over the relief 64 terrain, four runs on a second machine. 1,000,000 steps, seeds 1-4. A pilot (seed 9, 100,000 steps, five worlds) came first and fixed the flow at 0.1. Reference: e018's uniform sun and grass and trees at 8 per cell, seeds 1-4, where nothing flowed. We record e018's measures and:",
    "tldr": "Soil that runs downhill and levels makes the closed world stand: in all twelve uniform-sun runs the food eaten is the same in the last quarter as in the third (0.99-1.01), the population's coefficient of variation is 0.01-0.03 and nothing dies or declines, where e018's world fell through the run. The terrain draws the places without a patch: at relief 64 the soil pools into a level lake over the lowest two thirds of the cells (100% of the soil, 99-100% of the bodies, ridges at 0.0), at relief 256 into a third of the world, and the soil map is the terrain upside down. But a lake is not a tree: no cell grows faster than the uniform sun, so the lake is one wide place, the same bar of 6-10 gut cells wins it as wins the flat lawn, and lineages stay at 1-2 (#19 unchanged). The flat world with the same flow is a lawn of 8.1 per cell that eats 101-106 per step, so leveling alone is the cure and the terrain is the shape, bought with the ridges' share of the sun (34-46% lost). Over the drawn sun the terrain is fatal: it takes the soil away from where the patches put the sun, two worlds of four die and the others swing 5x as the patches drift on and off the lake; a rich place in a closed world is where the sun and the soil meet. Matter drifts by up to 1.8% from f32 rounding in the soil (an f64 soil holds it to 0.0003%). From here the sun is uniform, the soil is an f64, and the next place law is written on height (#14).",
    "c1": "yes", "l1": "Yes", "v1": "At relief 64 the food eaten per step is 56-71 over the second half and the same in the last quarter as in the third (0.99-1.01; it settles by step 100,000, seed 1 reading 75, 72, 71, 71, 71 at the 100,000-step marks); e018's uniform world went from 110 to 50-105 and was still falling. The sun lost to empty soil is flat (52-75 per step, the ridges). Population 1,126-1,458 (asked 1,400-1,800) with a coefficient of variation of 0.01-0.03 (asked under 0.10) and a swing of 1.0-1.1x. At relief 256 the same holds at 26-31 eaten and 478-618 bodies. No uniform-sun world died, declined or swung.",
    "c2": "yes", "l2": "Yes", "v2": "At relief 64 the lowest two thirds of the cells hold 100% of the soil at the end (valleys 19.2-21.5 per cell, slopes 3.5-5.6, ridges 0.0) and 99-100% of the bodies (698-733 in the valleys, 431-711 on the slopes, 0-14 on the ridges); the richest tenth of the cells holds 32-35% of the soil (asked about 30%). At relief 256 the lake is 25-30% of the cells at 25.4-25.5 per cell and holds every body (478-613, asked 500-700), the richest tenth 63-70% (asked about 60%), the soil under bodies 3.7-4.5 times the soil elsewhere. Figure 3.2: the soil map is the terrain upside down, a level lake with a sharp shore.",
    "c3": "yes", "l3": "Yes", "v3": "The winner of every uniform world is a bar of 6-10 digestive cells, 1-2 rows deep and 5-8 wide, mass 6.8-9.1 over 2.6-3.5 world cells, no hard cell and no bite (Figure 2). Contacts 0.006-0.089 per body per step (asked under 0.05; e018: 0.03). Lineages alive 1 at relief 64, 1-2 at 256, 1 on the flat world (asked 1-2); the one second lineage (relief 256, seed 1) has the same body and lives 324,000 steps at 127 agents standing higher on the lake. The ridges hold 0-14 bodies on 5,461 cells.",
    "c4": "no", "l4": "No: the terrain takes the soil from the sun", "v4": "Two of the four grass and trees worlds died (steps 53,181 and 257,596) and the other two swung 5x and more (cv 0.26-0.91; 333 and 293 bodies with lows of 58 and 25). The grass eats 13-17 per step (asked 28-34; e018: 22-26; e017: 36) with 255-308 bodies (e018: 393-453), 35-46 of its 82 of sun falling on empty soil (e018: 17-26): the patches drift over the terrain, and on the lake the grass holds 500 bodies (seed 1 at step 250,000, 27 barren), on the ridges 99 (step 750,000, 116 barren); the worlds that died are the seeds whose patches started on high ground. The trees hold 8-18 bodies at the median (e018: 0-20) and 27-40 only while a tree patch lies on the lake.",
    "c5": "yes", "l5": "Yes", "v5": "With no terrain the soil levels to 8.1-8.2 on every cell (the richest tenth holds 10%, no cell under 0.01), the world eats 101-106 per step (asked 100-120), steady (0.99-1.00), and holds 1,954-2,149 bodies (asked 1,800-2,200; cv 0.01) in one lineage, a bar of 7 gut cells; the sun is lost only to bodies standing on cells (35-39%). e018's trails do not form.",
    "c6": "partly", "l6": "Holds, with a rounding drift", "v6": "Matter at the end over the start is 0.9905-0.9964 at relief 64, 1.0021-1.0059 at 256, 0.9822-0.9896 on the flat world and 0.9996-1.0000 with the drawn sun (asked 0.1%): an f32 soil that receives and gives 0.001-sized amounts a million times drifts, and a copy of the code with an f64 soil holds matter to 0.4 of 139,737 over 50,000 steps where the f32 runs lose 62-115. 624-696 steps per second at relief 64 with twelve runs on one machine, 424-510 on the flat world with 2,000 bodies, 1,020-1,248 at relief 256; e018's uniform world ran 616-1,000 with six to ten runs sharing.",
    "h1": "The flow ends the fall",
    "r1": "In e018 the uniform world locked its matter into the trails of its walking bodies, one cell wide, and the cells between the trails wasted the sun; the food supply fell through the run. With soil that levels, a cell that gets more than its neighbors gives to them, so a trail spreads out as fast as it is laid, every cell with soil grows its 0.01 per step, and the world's income is the sun on the wet cells minus the cells bodies stand on: 101-106 per step on the flat world (100% of the cells wet, 35-39% shaded), 56-71 at relief 64 (54-66% wet: the ridges' third of the sun is lost), 26-31 at relief 256 (25-30% wet). The population follows the income: 1,954-2,149, 1,126-1,458, 478-618, each with a coefficient of variation of 0.01-0.03, and nothing moves after step 100,000. This is the first closed world of the series that stands (principle 4): e018 at 8 per cell swung 2-4x, its scarce world died, its uniform world declined.",
    "h2": "The places are the valleys, and the map is the terrain upside down",
    "r2": "The soil runs to the low ground and pools there level: at relief 64 a lake over the lowest two thirds of the cells (19-22 per cell in the valleys, 4-6 on the slopes, which the lake covers in part, 0.0 on the ridges), at relief 256 a deeper lake over a third (25 per cell, the rest bare). Its shore is one height: the surface of a cell is its height plus its soil, and soil moves until the surfaces agree, so the lake fills every basin to the same level and the soil map is the terrain cut at that level (Figure 3.2; the flat world's map is one color at 8.1). Every body lives in the lake, 99-100% of them in the lowest two thirds, 0-14 on the 5,461 ridge cells; the soil under the bodies is 1.6-2.0 times the soil elsewhere at relief 64 and 3.7-4.5 at 256 because the bodies are where the soil is, on a lake whose soil is everywhere the same. The richest tenth of the cells holds 32-35% and 63-70% of the soil: not a peak, a step. What the flow moves per step (66-77 at relief 64, 28-37 at 256, 110-131 on the flat world) is what bodies spend, spreading out from under them.",
    "h3": "A lake is one place, and the same bar wins it",
    "r3": "No cell grows faster than the uniform sun, 0.01 per step, whatever its soil, so the lake is a wide place, not a rich one: inside it every cell is the same as every other, and the body that wins it is the body that wins the flat lawn, a bar of 6-10 gut cells 1-2 rows deep and 5-8 wide (Figure 2), walking forward a third to a half of its decisions to leave the cells it has eaten. Contacts 0.006-0.089 per body per step, no tooth, no armor. Lineages alive are 1 at relief 64, 1-2 at 256 and 1 on the flat world (e018's uniform world: 1; its grass and trees: 2); the one second lineage has the same body. Judged by #19, the terrain under a uniform sun changes nothing: the world has one optimum and reaches it. Food eaten by band (left) says why: the valleys eat 35-38 per step at relief 64, the slopes 22-36 (the part of them the lake covers) and the ridges 0-0.5; two of the three bands are the same place and the third is empty.",
    "h4": "Over the drawn sun the terrain is fatal",
    "r4": "e018's grass and trees put the sun where the patches drift; the water puts the soil where the ground is low; where the two part, nothing grows. The grass eats 13-17 per step against e018's 22-26 (left), with 35-46 of its 82 of sun falling on empty soil, and its bodies go from 500 when the patch lies on the lake to 99 when it has drifted onto a ridge; two worlds of four die within 260,000 steps (their patches started on high ground: 119 bodies at step 10,000 in seed 3) and the other two live between 25 and 500. The trees (right) are the same story at a smaller scale: 27-40 bodies while a tree patch lies on the lake, 0 otherwise, 8-18 at the median. The flow does not give the trees back because the flow moves a tenth of a cell's soil per step and a tree cell's sun takes 6.5: even on the lake the tree's cell empties in a step and refills at the lake's pace. A rich place in a closed world is where the sun and the soil meet, and a drifting patch over a fixed terrain meets the soil by luck.",
    "h5": "The bodies",
    "r5": "One body everywhere: a bar of digestive cells, 1-2 rows deep, 5-8 wide, mass 6-10, the whole width of the grid as its front, walking forward a third to a half of its decisions. It is e018's mower, and it wins the flat lawn, the shallow lake and the deep lake alike, because in all three the food is 0.01 per cell per step on a level ground and the best body is the one that grazes the widest strip and moves on. In the grass and trees world the block of 8-9 gut cells of e016-e018 wins the grass (3 by 3, 447,000 steps in seed 4), the trees hold no lineage of their own, and nothing has a bite. The second lineage of relief 256 seed 1 is the bar again, standing higher on the lake for 324,000 steps.",
    "viewer": "Relief 64, seed 1. With the ground as terrain the lake's shape is visible under the bodies: they fill the low ground (dark) and stop at a line, and the high ground (light) is empty. Switch the ground to soil and the lake appears as it is, one shade over its whole area with a hard edge, brown where the terrain is dark; switch to food and the plants are a lawn on the lake and nothing beyond it. The bodies are one lineage of bars from step 74,000 on (lineage 1, blue), walking forward 47% of their decisions; the long view shows nothing change after step 100,000, which is the point.",
    "discussion": "<p>The law does the two things it was written for. Soil with a height of its own levels, and a world whose soil levels stands: every cell that has soil grows, the sun on the wet cells is the world's steady income, and twelve runs of twelve hold their population to within a few percent for a million steps where e018's fell and swung. And the terrain draws the places without a patch: a lake filling the basins to one height, a shore, a desert above it, the map the terrain upside down. That is the first shape this world has had that no one drew, and it is worth watching.</p><p>What it did not do is make more winners, and the reason is exact. A lake is one place. The sun is 0.01 on every cell, so no cell in the lake is richer than another however deep the soil under it; the lake is the flat lawn with an edge, and the flat lawn's bar wins it. The ridges are a second place in the sense that nobody lives there, which is no place at all: matter moves downhill and in bodies, a body gets nothing for carrying it up, and so the high ground is a desert and the low ground a lawn. Judged by #19 (count the winners) e019 is level with e018: 1-2 lineages. Judged by principle 4 (the long run) it is the first closed world that passes.</p><p>The drawn-sun world is the sharpest lesson. e011-e018's patches were a stand-in for places: they put the sun where they drifted and the world's rich places followed them. In a closed world with a flow the soil goes where the ground says, and a patch that drifts off the lake shines on nothing; two worlds died of it and the others swung 5x. A rich place in a closed world is where the sun and the soil meet. The uniform sun has that for free, on the lake, and the drawn one only by luck. So the sun is uniform from here and the shape of the world comes from the ground.</p><p>Two smaller things. The flow rate did not matter (0.01, 0.1 and 1 gave the same world in the pilot), because what sets the lake is the volume of soil and the shape of the ground, and the rate only sets how fast it gets there; one knob less. And an f32 soil that takes and gives 0.001-sized amounts a million times drifts by up to 1.8%, which over months would not be a rounding error any more; the soil is an f64 from the next commit, verified to 0.0003% over 50,000 steps.</p><p>The terrain leaves every cell with a coordinate the real world's places vary along: height, where warm and cold, wet and dry, the plants that grow and the animals that can live there all change. The next law (#14, places that differ) can be written on it, as a law about the world, and the question it has to answer is what a body can find on the high ground that it cannot find in the lake. Not a stronger sun up there: that is a patch again. Something the lake does not have.</p>",
    "conclusion": "Soil that runs downhill and levels makes the closed world stand: food eaten steady to 1% between the third and fourth quarters, population within 1-3%, in all twelve uniform-sun runs (e018: falling, swinging 2-4x, dying when scarce), because every cell with soil grows and a trail spreads as fast as it is laid. The terrain draws the places without a patch: a level lake over the low ground holding 100% of the soil and 99-100% of the bodies, bare ridges, the soil map the terrain upside down. A lake is one place: the same bar of 6-10 gut cells wins it as wins the flat lawn (101-106 eaten per step, 100% of the cells wet), lineages stay at 1-2, and the terrain costs the world the ridges' share of the sun (56-71 eaten at relief 64, 26-31 at 256). Over the drawn sun the terrain is fatal: the patches put the sun where they drift and the water puts the soil in the basins, two worlds of four die and the rest swing 5x; a rich place in a closed world is where the sun and the soil meet. The flow stays, with or without a terrain; the sun is uniform from here; the soil becomes an f64 (matter drifted up to 1.8% from f32 rounding); the next law is a place law written on height (#14): what the high ground has that the lake does not.",
}

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "lineages":
        top_lineages()
    else:
        main()
