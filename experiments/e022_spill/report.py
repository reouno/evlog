#!/usr/bin/env python3
"""Build report.html for e022.

Charts: matplotlib, exported as SVG and inlined. Diagram: hand-written SVG.
Run from the repo root: uv run python experiments/e022_spill/report.py
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

E021 = os.path.join(HERE, "..", "e021_canopy")
# Places of a world: (id in the CSVs, name, color). Under the uniform sun a place is a height band (thirds of the cells by the
# terrain).
BANDS = [(0, "valleys (lowest third)", SERIES[0]), (1, "slopes (middle third)", SERIES[3]), (2, "ridges (highest third)", SERIES[1])]
# Worlds of this experiment: label -> run prefix, world size, places, seeds, whether the sun is uniform (always, here).
WORLDS = {
    "spill on the mountains": dict(run="128_sigma0_r64_f0.1_high", size=128, places=BANDS, seeds=[1, 2, 3, 4], uniform=True),
    "spill, half the breath": dict(run="128_sigma0_r64_f0.1_high-b0.5", size=128, places=BANDS, seeds=[1, 2, 3, 4], uniform=True),
    "spill on the flat lawn": dict(run="128_sigma0_r64_f0.1_flat", size=128, places=BANDS, seeds=[1, 2, 3, 4], uniform=True),
    "control: e021's canopy, mutation per base": dict(run="128_sigma0_r64_f0.1_high-spill0", size=128, places=BANDS, seeds=[1, 2, 3, 4], uniform=True),
}
UNIFORM = list(WORLDS)
HIGH64, HALF, FLAT, CONTROL = list(WORLDS)
# e021's runs (the same worlds and terrains with the saturating canopy and no spill, two
# mutations per child): label -> (run prefix, folder, uniform).
REFS = {"e021 mountains": ("128_sigma0_r64_f0.1_high", E021, True), "e021 half breath": ("128_sigma0_r64_f0.1_high-b0.5", E021, True), "e021 flat lawn": ("128_sigma0_r64_f0.1_flat", E021, True)}
WORLD_COLOR = {HIGH64: SERIES[0], HALF: SERIES[1], FLAT: SERIES[3], CONTROL: SERIES[2], "e021 mountains": INK, "e021 half breath": "#b5b3ab", "e021 flat lawn": "#d3d1c9"}
KIND_COLOR = {1: SERIES[0], 2: SERIES[1], 3: SERIES[3], 4: SERIES[2]}
CONFIRM_STEPS = 5000
MAIN = HIGH64
VIEWER_WORLD = HIGH64
VIEWER_SEED = 2
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
<svg viewBox="0 0 800 340" role="img" aria-label="A row of world cells in cross-section. One column stands at the cap of 8, a full tree, with a body on its base. The sun falls on every cell alike, but the cells within the tree's reach lose their sun to it, shown as arrows bending from their tops into the crown, and the crown drops what it cannot hold as fruit on the two cells beside it, where bodies stand and eat. The cells under the crown's shadow are nearly bare; the lawn beyond the reach grows as before." style="max-width:100%;height:auto;display:block">
<g fill="none" stroke="currentColor" stroke-width="1.2" font-size="12" font-family="system-ui, sans-serif">
  <!-- the sun: one arrow per cell -->
  <g stroke="#eda100" stroke-width="1.4">
    <path d="M 65,16 L 65,36 M 115,16 L 115,36 M 165,16 L 165,36 M 215,16 L 215,36 M 265,16 L 265,36 M 365,16 L 365,36 M 415,16 L 415,36 M 465,16 L 465,36 M 515,16 L 515,36 M 565,16 L 565,36" marker-end="url(#sunhead)"/>
    <path d="M 315,16 L 315,36" stroke-width="2.2" marker-end="url(#sunhead)"/>
  </g>
  <text x="150" y="56" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">sun: 0.01 per cell per step, everywhere</text>
  <!-- the light the crown takes: from the tops of the cells within reach into the crown -->
  <g stroke="currentColor" stroke-width="1.3">
    <path d="M 115,66 C 170,72 250,78 294,96" marker-end="url(#lighthead)"/>
    <path d="M 165,64 C 210,70 262,80 296,100" marker-end="url(#lighthead)"/>
    <path d="M 215,62 C 245,68 275,84 300,104" marker-end="url(#lighthead)"/>
    <path d="M 265,60 C 280,68 295,86 306,102" marker-end="url(#lighthead)"/>
    <path d="M 365,60 C 352,70 336,88 326,102" marker-end="url(#lighthead)"/>
    <path d="M 415,62 C 388,70 356,88 332,104" marker-end="url(#lighthead)"/>
    <path d="M 465,64 C 420,70 366,82 336,100" marker-end="url(#lighthead)"/>
  </g>
  <text x="348" y="150" fill="currentColor" stroke="none" font-weight="600">the full crown keeps taking the light,</text>
  <text x="348" y="166" fill="currentColor" stroke="none" font-weight="600">with a body on it</text>
  <!-- the fruit: from the crown down onto the ring -->
  <g stroke="var(--s1)" stroke-width="1.8" stroke-dasharray="5 3">
    <path d="M 298,120 C 270,150 262,200 264,238" marker-end="url(#fruithead)"/>
    <path d="M 332,120 C 360,150 368,200 366,238" marker-end="url(#fruithead)"/>
  </g>
  <text x="60" y="176" fill="var(--s1)" stroke="none" font-weight="600">what it cannot hold falls</text>
  <text x="60" y="192" fill="var(--s1)" stroke="none" font-weight="600">as fruit on the ring</text>
  <!-- the ground -->
  <path d="M 40,260 L 590,260" stroke-width="1.5"/>
  <!-- the lawn beyond the reach -->
  <g fill="#1baf7a" stroke="none">
    <rect x="50" y="254" width="30" height="6"/>
    <rect x="500" y="254" width="30" height="6"/>
    <rect x="550" y="255" width="30" height="5"/>
  </g>
  <!-- the cells in the shadow: nearly bare -->
  <g fill="#1baf7a" stroke="none">
    <rect x="100" y="258" width="30" height="2"/>
    <rect x="150" y="258" width="30" height="2"/>
    <rect x="200" y="259" width="30" height="1"/>
    <rect x="400" y="259" width="30" height="1"/>
    <rect x="450" y="258" width="30" height="2"/>
  </g>
  <text x="165" y="246" text-anchor="middle" fill="currentColor" stroke="none">in the dark</text>
  <text x="440" y="246" text-anchor="middle" fill="currentColor" stroke="none">in the dark</text>
  <!-- the ring cells: fruit lying, a body on each -->
  <g fill="var(--s1)" stroke="none">
    <circle cx="255" cy="256" r="2.6"/><circle cx="262" cy="252" r="2.6"/><circle cx="270" cy="256" r="2.6"/><circle cx="277" cy="252" r="2.6"/>
    <circle cx="355" cy="256" r="2.6"/><circle cx="362" cy="252" r="2.6"/><circle cx="370" cy="256" r="2.6"/><circle cx="377" cy="252" r="2.6"/>
  </g>
  <g fill="currentColor" fill-opacity="0.55" stroke="none">
    <rect x="252" y="236" width="26" height="11" rx="1.5"/>
    <rect x="352" y="236" width="26" height="11" rx="1.5"/>
  </g>
  <!-- the full tree, with a body on its base -->
  <rect x="300" y="40" width="30" height="220" fill="#1baf7a" stroke="none"/>
  <rect x="304" y="247" width="22" height="11" rx="1.5" fill="currentColor" fill-opacity="0.55" stroke="none"/>
  <text x="315" y="280" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">a full tree, height 8, a body on it</text>
  <text x="315" y="296" text-anchor="middle" fill="currentColor" stroke="none">the crown's light is above the body: it takes</text>
  <text x="315" y="312" text-anchor="middle" fill="currentColor" stroke="none">up to 200 suns per step, out of its soil,</text>
  <text x="315" y="328" text-anchor="middle" fill="currentColor" stroke="none">and lays them on its ring, where the crowd eats</text>
  <!-- labels: the column on the right -->
  <text x="610" y="50" fill="currentColor" stroke="none" font-weight="600">the law, per step</text>
  <text x="610" y="70" fill="currentColor" stroke="none">a column claims, from every cell</text>
  <text x="610" y="86" fill="currentColor" stroke="none">within reach, a share of its sun:</text>
  <text x="610" y="110" fill="currentColor" stroke="none">(height difference - distance</text>
  <text x="610" y="126" fill="currentColor" stroke="none">walked) / 8  x  2, whatever its</text>
  <text x="610" y="142" fill="currentColor" stroke="none">own height (no saturation), and</text>
  <text x="610" y="158" fill="currentColor" stroke="none">under a body too</text>
  <text x="610" y="182" fill="var(--s1)" stroke="none">the growth its light and soil</text>
  <text x="610" y="198" fill="var(--s1)" stroke="none">would give past the cap, or</text>
  <text x="610" y="214" fill="var(--s1)" stroke="none">under a body, falls as fruit on</text>
  <text x="610" y="230" fill="var(--s1)" stroke="none">the ring of 8, in equal shares</text>
  <text x="610" y="254" fill="currentColor" stroke="none">fruit lies on the ground: any</text>
  <text x="610" y="270" fill="currentColor" stroke="none">gut eats it, it rots into the</text>
  <text x="610" y="286" fill="currentColor" stroke="none">soil at 1% per step, and it</text>
  <text x="610" y="302" fill="currentColor" stroke="none">counts in the column it lies on</text>
  <text x="610" y="326" fill="currentColor" stroke="none">the sun is moved, never made</text>
</g>
<defs>
  <marker id="sunhead" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="#eda100"/></marker>
  <marker id="lighthead" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="currentColor"/></marker>
  <marker id="fruithead" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="var(--s1)"/></marker>
</defs>
</svg>
<figcaption>Figure 1. The spill. e021's canopy - a column of standing matter claims, from every cell within its height in cells, a share of that cell's sun equal to the height difference less the distance walked, over the cap, times the rate 2 - without its saturation: a full crown claims as hard as a bitten one, and a column under a body claims too, because what it takes is the crown's light, above the body (only the cell's own sun falls in the body's shadow, e016). A cell grows out of its soil by at most its light; the growth that would pass the cap, or that a held cell cannot make, is fruit, taken from the cell's soil and laid in equal shares on the eight cells around it. Fruit is plant matter lying on the ground beside the dead: a gut takes it in the cell's proportion, it rots into the soil at 1% per step, and it counts in the column it lies on. A full tree alone on a bare lawn takes the whole sun of the cells within five of it and a part out to eight, 200 suns per step; the cells under its shadow grow nothing, and the lawn beyond its reach grows as before. Everything else is e021: the uniform sun, the terrain with soil that runs downhill, the breath to the air and the rain by height, the height bands as places. Riding along, mutation is a chance of 2/512 per base per copy instead of exactly two per child.</figcaption>
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
        sun = [r + sh + wa + b + f for r, sh, wa, b, f in zip(log["regrowth"], log["shaded"], log["wasted"], log["barren"], log["fruit"])]
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
                 matter_hold=log["matter"][-1] / log["matter"][0], air_end=log["air"][-1], soil_end=log["soil"][-1], rain=med(half(log, "rain")),
                 top=end["top"] if end else float("nan"), top_first=st[0]["top"] if st else float("nan"), wet=end["wet"] if end else float("nan"),
                 under=end["under"] / max(end["free"], 1e-9) if end else float("nan"),
                 trees=med(half(log, "trees")), tree_res=med(half(log, "tree_res")), res_max=med(half(log, "res_max")),
                 shade=med(half(log, "shade")), tree_eaten=med(half(log, "tree_eaten")),
                 tree_share=med([t / max(e, 1e-9) for t, e in zip(half(log, "tree_eaten"), eaten[n // 2:])]),
                 biters=med(half(log, "biters_share")), biters_max=max(log["biters_share"]),
                 fruit=med(half(log, "fruit")), fruit_eaten=med(half(log, "fruit_eaten")), fruit_stock=med(half(log, "fruit_stock")),
                 fruit_share=med([f / max(e, 1e-9) for f, e in zip(half(log, "fruit_eaten"), eaten[n // 2:])]),
                 meat_share=med([m / max(p_ + m, 1e-9) for p_, m in zip(half(log, "plant_intake"), half(log, "meat_intake"))]),
                 clones=med(half(log, "clones")), mutations=med(half(log, "mutations")))
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
            d[f"trees_{p}"] = med(q["trees"][h])
            d[f"fruit_{p}"] = med(q["fruit"][h])
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
                sun = [r + sh + wa + b + f for r, sh, wa, b, f in zip(L[s]["regrowth"], L[s]["shaded"], L[s]["wasted"], L[s]["barren"], L[s].get("fruit", [0.0] * len(L[s]["step"])))]
                out.append(med([b / max(t, 1e-9) for b, t in zip(half(L[s], key), sun[len(sun) // 2:])]))
            return med(out)
        if key == "soil_end":
            return med([L[s]["soil"][-1] for s in seeds])
        if key == "tree_share":
            return med([med([t / max(e, 1e-9) for t, e in zip(half(L[s], "tree_eaten"), eaten_of(L[s])[len(L[s]["step"]) // 2:])]) for s in seeds])
        if key == "meat_share":
            return med([med([m / max(p_ + m, 1e-9) for p_, m in zip(half(L[s], "plant_intake"), half(L[s], "meat_intake"))]) for s in seeds])
        if key == "biters_max":
            return med([max(L[s]["biters_share"]) for s in seeds])
        if key == "mass":
            key = "mass_mean"
        if key not in L[1]:
            return float("nan")
        return med([med(half(L[s], key)) for s in seeds])

    logs_ref = dict(logs)
    logs_ref.update({w: rlogs[w] for w in REFS})
    all_worlds = list(WORLDS) + list(REFS)

    charts = {}
    charts["eaten"] = world_chart("Food eaten per step", "Plant, fruit and dead matter taken by guts per step, one line per run; gray: e021's runs, the same worlds with the saturating canopy and no spill (dark: mountains, mid: half breath, light: flat lawn). The sun gives 164 per step. A line that ends is a world that died.", logs_ref, eaten_of, all_worlds, WORLD_COLOR)
    charts["pop"] = world_chart("Population", "Bodies alive at each log step, one line per run; gray: e021.", logs_ref, lambda l: l["pop"], all_worlds, WORLD_COLOR)
    charts["fruit_share"] = world_chart("Intake from fruit", "Share of the food eaten that was fruit lying on the ground, per log window, one line per run. e021 had no fruit; the control drops none.", logs, lambda l: [f / max(e, 1e-9) for f, e in zip(l["fruit_eaten"], eaten_of(l))], list(WORLDS), WORLD_COLOR, percent=True, ymax=1.0)
    charts["fruit"] = world_chart("Fruit fallen per step", "Matter dropped by the columns on the cells around them per step, one line per run, of the sun's 164. A flat line is a world whose crowns are full and lit; the control drops nothing.", logs, lambda l: l["fruit"], list(WORLDS), WORLD_COLOR)
    charts["trees"] = world_chart("Trees standing", "Cells whose standing plant is 1.0 or more (50 bites; the fruit and the dead lying on a cell do not count) at each log step, one line per run; gray: e021 (6-24 in its orchard runs, 165-1,405 in its forests).", logs_ref, lambda l: l["trees"], all_worlds, WORLD_COLOR)
    charts["tree_share"] = world_chart("Intake from the trees", "Share of the food eaten that was taken from a cell whose plant stands at 1.0 or more, per log window, one line per run; gray: e021 (0.2-0.8% in the orchards, 6.5% in the forests).", logs_ref, lambda l: [t / max(e, 1e-9) for t, e in zip(l["tree_eaten"], eaten_of(l))], all_worlds, WORLD_COLOR, percent=True)
    charts["contacts"] = world_chart("Contacts per body per step", "Pairs of bodies whose cells touched, per body per step, one line per run; gray: e021 (0.008-0.093, the forests at the top).", logs_ref, lambda l: [c / max(p, 1) / 10_000 for c, p in zip(l["contacts"], l["pop"])], all_worlds, WORLD_COLOR)
    charts["meat_share"] = world_chart("Dead matter in the intake", "Share of the food eaten that was dead bodies, per log window, one line per run; gray: e021 (about 1%). A body that dies in a crowd is eaten.", logs_ref, lambda l: [m / max(p + m, 1e-9) for p, m in zip(l["plant_intake"], l["meat_intake"])], all_worlds, WORLD_COLOR, percent=True)
    charts["biters"] = world_chart("Bodies with a bite", "Share of the bodies with a hard tip on the front backed by muscle, at each log step, one line per run; gray: e021 (0.000 throughout). A line above zero is a tooth that pays for a while.", logs_ref, lambda l: l["biters_share"], all_worlds, WORLD_COLOR, percent=True)
    charts["lineages"] = world_chart("Lineages alive", "Confirmed lineages at each log step, one line per run; gray: e021 (1-5).", logs_ref, lambda l: l["lineages"], all_worlds, WORLD_COLOR)
    charts["barren"] = world_chart("Sun lost to empty soil", "Share of the sun that shone on a column whose soil had nothing left, per log window, one line per run; gray: e021. With the spill a full column with no soil takes light and wastes it.", logs_ref, lambda l: [b / max(r + sh + wa + b + f, 1e-9) for r, sh, wa, b, f in zip(l["regrowth"], l["shaded"], l["wasted"], l["barren"], l.get("fruit", [0.0] * len(l["step"])))], all_worlds, WORLD_COLOR, percent=True)
    charts["shaded"] = world_chart("Sun lost under the bodies", "Share of the sun that fell on a cell's own plant while a body stood on it, per log window, one line per run; gray: e021 (29-38%). The crown's light is above the body and is not lost.", logs_ref, lambda l: [sh / max(r + sh + wa + b + f, 1e-9) for r, sh, wa, b, f in zip(l["regrowth"], l["shaded"], l["wasted"], l["barren"], l.get("fruit", [0.0] * len(l["step"])))], all_worlds, WORLD_COLOR, percent=True)
    charts["clones"] = world_chart("Children born as clones", "Share of the children conceived with no point mutation, per log window, one line per run. At 2/512 per base the expectation is e^-2 = 13.5%; e021 had none.", logs, lambda l: l["clones"], list(WORLDS), WORLD_COLOR, percent=True)
    charts["pop_band"] = place_chart(f"Bodies by height, {HIGH64}", "Bodies standing in each height band at each log step, one line per seed. The bands are equal in cells (5,461 each). e021: the crowd on the ridges where the rain is.", places, HIGH64, lambda d: d["pop"])
    charts["maps"] = terrain_soil_figure("The terrain and the soil at the end", "Top: the terrain of seed 1 of each world (white high, black low). Bottom: soil per cell at step 1,000,000 (or the last dump before the world died), darker is more (log scale, 30 and above black).", [(w, seeds_of(w)[0]) for w in WORLDS])

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
        # A run that died at its start (one log row) has no second half: it only reports its death.
        vals = [S[w][s].get(key, float("nan")) for s in seeds_of(w) if key == "extinct_at" or not S[w][s]["extinct"]]
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
    by_band = lambda k: {w: f"{k}_0|{k}_1|{k}_2" for w in WORLDS}
    uniform_only = lambda k: {w: k for w in WORLDS}
    summary = ("<thead><tr><th>Measure (range over seeds, median over the second half unless said)</th>" + "".join(f"<th>{w}</th>" for w in WORLDS) + "".join(f"<th>{r}</th>" for r in REFS) + "</tr></thead><tbody>"
               + row("Population", "pop", n0, "pop")
               + row("Population, coefficient of variation", "pop_cv", d2, "pop_cv")
               + row("Population, largest over smallest", "pop_swing", d1, "pop_swing")
               + row("Died at step", "extinct_at", n0)
               + row("Food eaten per step", "eaten", d1, "eaten")
               + row("Food eaten, last quarter over third quarter", "steady", d2, "steady")
               + row("Fruit fallen per step", "fruit", d1)
               + row("Intake from fruit, share of the food eaten", "fruit_share", p0)
               + row("Dead matter, share of the food eaten", "meat_share", p0, "meat_share")
               + row("Trees standing (plant at 1.0 or more)", "trees", n0, "trees")
               + row("Intake from the trees, share of the food eaten", "tree_share", p0, "tree_share")
               + row("Tallest column (plant, fruit and dead)", "res_max", d1, "res_max")
               + row("Sun lost to empty soil, share of the sun", "barren", p0, "barren")
               + row("Sun lost under the bodies, share", "shaded", p0, "shaded")
               + row("Contacts per body per step", "contacts", d3, "contacts")
               + row("Bodies with a bite, share (median / peak)", "biters|biters_max", d3, "biters_share")
               + row("Lineages alive", "lineages", n0, "lineages")
               + row("Mass", "mass", d1, "mass")
               + row("Bodies: valleys / slopes / ridges", by_band("pop"), n0)
               + row("Children born as clones, share", "clones", p0)
               + row("Mutations per child", "mutations", d2)
               + row("Matter at the end over the start", "matter_hold", lambda v: f"{v:.4f}")
               + row("Steps per second", "sps", n0, "steps_per_sec")
               + "</tbody>")

    tables = data_table(["step", "place", "pop", "mass", "hard", "muscle", "digestive", "cover", "foot", "plant_intake", "meat_intake", "fruit", "fruit_intake", "dead", "carrion", "soil", "rain", "trees", "barren", "regrowth", "cells", "lineages", "movers"],
                        {f"{w}, seed {s}, {place_names(w)[p]} (every 100,000 steps)": places[w][s][p] for w in WORLDS for s in seeds_of(w) for p, _, _ in WORLDS[w]["places"] if p in places[w][s]}, every=10)
    tables += data_table(["step", "pop", "births", "deaths_energy", "mass_mean", "forward", "blocked", "foot_mean", "cover", "contacts", "regrowth", "shaded", "wasted", "barren", "rot", "spent", "flow", "rain", "air", "shade", "trees", "tree_res", "res_max", "tree_eaten", "fruit", "fruit_stock", "fruit_eaten", "clones", "mutations", "soil", "matter", "plant_intake", "meat_intake", "biters_share", "lineages", "steps_per_sec"],
                         {f"{w}, seed {s}, whole world (every 100,000 steps)": logs[w][s] for w in WORLDS for s in seeds_of(w)}, every=10)

    text = TEXT
    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>e022 The spill - Report</title>
<style>{CSS}</style>
</head>
<body>
<main>
<h1>e022: The spill</h1>
<p class="sub">Experiment report - 2026-09-01 - e021's closed world with the canopy's saturation dropped and one law added: what a column cannot hold falls as fruit on the ring of cells around it. Rain on the mountains, half the breath, and rain everywhere alike, 128x128, four seeds each, 1,000,000 steps; a control with e021's canopy; e021's runs as the reference. Mutation as a chance per base rides along.</p>

<section class="tldr">
<h2>TL;DR</h2>
<p>{text["tldr"]}</p>
</section>

<h2>1. Question</h2>
<p>{text["question"]}</p>
<ol>
  <li><strong>The world stands without saturation.</strong> No extinction, population coefficient of variation under 0.10 over the second half, matter conserved to 0.05%, in all twelve runs: light a full crown takes is fruit now, not a blight.</li>
  <li><strong>Fruit is the harvest.</strong> Intake from fruit is at least a third of the food eaten in every run, and the standing trees are eaten less than in e021's forest.</li>
  <li><strong>A crowd forms.</strong> Contacts per body per step exceed e021's forest ceiling (0.093) in every run.</li>
  <li><strong>The crowd pays for a second kind of body.</strong> By #19: in at least two seeds of four, a lineage with a different body coexists with the winner for over 100,000 steps, or the biters' share exceeds 0.01 (the first tooth since e012); dead matter is a larger share of the intake than e021's 1%.</li>
  <li><strong>The canopy pays the world more.</strong> Food eaten per step exceeds e021's in every world (mountains 83, half breath 100-109, flat 105-113).</li>
  <li><strong>The ring, not the wide fall.</strong> Fruit spread over the 24 cells within distance 2 (pilot only) makes a weaker crowd and wastes more sun.</li>
  <li><strong>Mutation per base changes the distribution, not the world.</strong> About e^-2 = 13.5% of the children are clones, and the control (e021's canopy with the per-base mutation) has e021's winners, lineage counts and income.</li>
</ol>

<h2>2. The world</h2>
<p>{text["world"]}</p>
{DIAGRAM}
<p>{text["runs"]}</p>
<ul class="measures">
  <li><strong>Fruit</strong> (<code>fruit</code>): matter fallen from the columns per step; <code>fruit_stock</code> is what lies on the ground now; <code>fruit_eaten</code> the intake taken as fruit; per height band <code>fruit</code> (fallen, by the column's cell) and <code>fruit_intake</code>.</li>
  <li><strong>Trees</strong> (<code>trees</code>): cells whose standing plant (the column less the fruit and the dead on it) is 1.0 or more (50 bites); <code>tree_res</code> the plant in them, <code>res_max</code> the tallest column of anything, <code>tree_eaten</code> the intake from tree cells.</li>
  <li><strong>The crowd</strong>: contacts per body per step, dead matter's share of the intake, the biters' share (a hard tip on the front backed by muscle), lineages alive (a mating-connected group of at least 5 that persists).</li>
  <li><strong>Mutation</strong> (<code>clones</code>, <code>mutations</code>): the share of the children conceived without a point mutation, and the mean number per child.</li>
  <li>e021's measures: sun split into grown, shaded (a cell's own sun under a body), wasted and barren; the canopy's moved sun; the air and the rain; soil, spent, rot, flow, matter; population, food eaten, moves, events; places by height band; snapshots with the terrain and the soil as layers.</li>
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
<li><span class="verdict {text["c7"]}">{text["l7"]}</span> {text["v7"]}</li>
</ol>

<h3>3.1 {text["h1"]}</h3>
<div class="grid2">
{charts["eaten"]}{charts["pop"]}
</div>
<p>{text["r1"]}</p>

<h3>3.2 {text["h2"]}</h3>
<div class="grid2">
{charts["fruit_share"]}{charts["fruit"]}
</div>
<div class="grid2">
{charts["trees"]}{charts["tree_share"]}
</div>
<div class="wide">{charts["maps"]}</div>
<p>{text["r2"]}</p>

<h3>3.3 {text["h3"]}</h3>
<div class="grid2">
{charts["contacts"]}{charts["meat_share"]}
</div>
<p>{text["r3"]}</p>

<h3>3.4 {text["h4"]}</h3>
<div class="grid2">
{charts["biters"]}{charts["lineages"]}
</div>
{gallery(GALLERY)}
<p>{text["r4"]}</p>

<h3>3.5 {text["h5"]}</h3>
<div class="grid2">
{charts["shaded"]}{charts["barren"]}
</div>
<p>{text["r5"]}</p>

<h3>3.6 {text["h6"]}</h3>
<p>{text["r6"]}</p>

<h3>3.7 {text["h7"]}</h3>
<div class="grid2">
{charts["clones"]}{charts["pop_band"]}
</div>
<p>{text["r7"]}</p>

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
<p>Every 100,000th record; full logs in <code>results/*_log.csv</code>, per place in <code>results/*_places.csv</code>, lineages in <code>results/*_lineages.csv</code>, events in <code>results/*_events.csv</code>, agents every 100,000 steps in <code>results/*_agents.csv</code>, the terrain (with the rain mode, the shade rate, the spill radius and the mutation rate) in <code>results/*_terrain.json</code>, the soil and plants of every cell every 100,000 steps in <code>results/*_soil.jsonl</code>, snapshots in <code>results/*_{{long,clip,bodies}}.jsonl</code>. Reference runs are read from <code>../e021_canopy/results</code>. Build this report with <code>uv run python experiments/e022_spill/report.py</code>.</p>
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
    ("spill on the flat lawn", 1, 1, "the frame", "Twenty-four cells around the rim of the 8x8 grid and none inside - 19 digestive, 4 hard at the corners - a hollow square 7 world cells wide, the only lineage of its run for all 1,000,000 steps (1,098 agents at its peak). The hollow is the point: the frame stands around a tree without holding it, so the tree keeps growing and dropping, and the frame's guts sit on the ring where the fruit lands. Three times the mass of e021's winner, and the first winner since e013 that is not a bar."),
    ("spill on the mountains", 2, 545, "the frame on the mountains", "Nineteen cells over 6.5 world cells, hard 1.4, alive 877,000 steps on the mountain-rain world where the crowd formed (contacts 0.69 per body per step): the same answer to the same place, a body as wide as the ring it feeds on."),
    ("spill, half the breath", 2, 608, "the armored frame", "Eighteen cells with 3.3 hard, 567,000 steps beside a bar (lineage 20, below) for 326,000 of them: in a crowd that touches 0.7 times per body per step, hard cells on the rim pay for the first time since e012 - without a tooth."),
    ("spill, half the breath", 2, 20, "the bar that shared the world", "Eleven cells, 2.6 by 7.4, e021's winner one row deeper, 326,000 steps in the same world as the armored frame before the frame took the crowd: the two bodies of the two states, side by side for a third of the run."),
    ("spill on the mountains", 3, 56, "the middle body", "Ten cells, 3 by 5.7, on 3 world cells, all 993,000 steps of a run that stayed in the mixed state (fruit 44% of the intake, contacts 0.36): between the bar and the frame, the body of a world where fruit is half the food."),
    ("spill on the mountains", 1, 44, "e021's bar, unchanged", "Seven and a half digestive cells 3.7 by 3.7, the whole run, in the one spill world that never entered the crowd state (fruit 8% of the intake, contacts 0.03, 158 trees): the same world as e021 gives the same body."),
    ("spill on the mountains", 3, 494, "the giant, briefly", "Thirty-seven cells - 23 digestive, 9.6 hard - the heaviest body of the series, 25 agents for 16,000 steps in the valleys at height 14: what a rich place lets a body afford, and what a crowd of frames does not let it keep."),
    ("control: e021's canopy, mutation per base", 3, 1, "the control's bar", "Seven digestive cells in a single row, 1 by 8, the only lineage of the control run for 1,000,000 steps: e021's canopy with mutation as a chance per base gives e021's winner, e021's income (81-84) and e021's 1-2 lineages."),
]

TEXT = {
    "question": "e021's canopy gave the closed world standing trees, a forest state and its record income, and still one kind of body and no tooth: a body eating a tree stands on it, a held cell neither grows nor claims, so a tree feeds one gut at a time. e011, the only world where teeth paid, had cells that kept producing while 45-77 bodies ate them at once. The spill writes that into the closed world: a full crown keeps taking the light it stands in, a column under a body keeps taking it too, and what a column cannot hold falls as fruit on the eight cells around it - a rich place with a radius, where a crowd eats without silencing the tree. Mutation as a chance per base (2/512, the same mean as e021's two per child) rides along, with a control that isolates it. The hypotheses:",
    "world": "Everything is e021's closed world (128x128 on a torus, matter 8 per cell at the start as plants, bodies of 8x8 cells in five kinds grown from the genome, space at the resolution of the body, a cell that costs what it holds, work = force x distance, a plant that grows out of its own cell's soil at most the sun's rate and not under a body, the dead lying where they fall, the breath to the air and the rain by height on a terrain of relief 64 with soil that runs downhill, and the canopy at rate 2: a taller column takes a shorter one's light as far as it is tall) with two changes to the canopy and one law added. The canopy no longer saturates - a full crown claims as hard as a bitten one - and a column under a body claims too, because what it takes is the crown's light, above the body. And the growth a column's light and soil would give past the cap, or under a body, falls as fruit on the ring of eight cells around it: plant matter lying on the ground, eaten by any gut, rotting into the soil at 1% per step if nobody eats it, counted in the column it lies on. The sun and the matter are only moved.",
    "runs": "<strong>Runs.</strong> The spill (radius 1, shade 2) on e021's three worlds - rain on the mountains, half of the breath to the air, rain on every cell alike - 1,000,000 steps, seeds 1-4, one thread each (eleven on one machine, flat seed 4 on a second), and a control on the mountain world at spill 0 (e021's saturating canopy, held columns claiming nothing) with the per-base mutation, four seeds on the second machine; e021's twelve runs, the same terrains seed for seed, as the reference. A pilot (seed 9, 100,000 steps) chose the ring over a fall of radius 2 and rate 2 over 1; a survey of the start (seeds 1-8 of the three worlds, 10,000 steps each) counted how often the spill world dies in its first 4,000 steps.",
    "tldr": "The spill makes the crowd: contacts per body per step are 0.22-0.76 in ten runs of eleven, two to eight times e021's forest ceiling, fruit is 44-77% of everything eaten, dead bodies 10-26% of it, and the closed world's income reaches 115-134 per step in the crowd state, a record. The crowd picks a new winner - a hollow frame of 19-24 cells around the rim of the 8x8 grid, 7 world cells wide, that stands around a tree without holding it and eats the ring, with 1-4 hard cells, three times e021's bar - in four runs, a middle body in five, and e021's bar in one; but it is one winner again (lineages 1-3), and no tooth (the biters' share peaks at 0.026 and falls back). The price is the start: with a full crown taking every neighbor's light the grazed lawn is dark, every seed crashes to a few hundred bodies by step 1,000, and one run of twelve (five of twenty-four in the survey) never recovers. Mutation per base does what it should and changes nothing else. Next: the start is the bodies' two-cell sight meeting clumped food, which is #26 (eyes that see far); the crowd is here, and the tooth is not, which is #27 and #25 (what flesh is worth, what a block weighs).",
    "c1": "no", "l1": "No: one run of twelve died at the start", "v1": "High seed 4 died at step 3,324, and a survey of the start (seeds 1-8 of the three worlds, 10,000 steps) counted 5 deaths in 24 and bottlenecks of 7-431 bodies in the survivors (e021's law never falls below 750 on the same seed). The eleven survivors stand: population cv 0.03-0.11 (flat seed 3 at 0.109, just over the 0.10 asked), food eaten last quarter over third 0.96-1.07, matter held to 0.11% at worst (flat seed 1; the columns are f32 and stand 30-40 tall). The blight is gone - the light a full crown takes is fruit now - but the start is a lottery.",
    "c2": "yes", "l2": "Yes, in ten runs of eleven", "v2": "Fruit is 44-77% of the food eaten in ten runs, 7.7% in high seed 1 (the one run that stayed in e021's state); 68-128 of fruit falls per step in those ten, of the sun's 164. The trees are eaten 2-9% of the intake, about e021's forest (6.5%), not less: the tree is the source and the ring the table, and both are eaten.",
    "c3": "yes", "l3": "Yes, in ten runs of eleven", "v3": "Contacts per body per step are 0.22-0.76 in ten runs against e021's 0.008-0.093 (its forests at the top) and the control's 0.03-0.05; high seed 1 sits at 0.029. Dead matter is 10-26% of the intake in those ten (e021: 1%): a body that dies in a crowd is eaten.",
    "c4": "maybe", "l4": "A new winner, not a second one", "v4": "The crowd picks a different body: a hollow frame of 19-24 cells around the rim of the 8x8 grid, 6.5-7 world cells wide, 17-20 of them digestive and 1-4 hard at the corners, standing around a tree without holding it, in the four runs in the crowd state (flat 1 and 4, high 2, half 2, with half 1 arriving at step 900,000), a middle body of 10-15 cells in five runs, and e021's bar of 7.5 in high seed 1. But it is one winner per run again: lineages alive 1-3 (peaks of 8-9 in half 2 and flat 2), the frame sweeps as fully as the bar did (flat seeds 1 and 4: one lineage for the whole run), and no tooth: the biters' share peaks at 0.026 (flat seed 1) and 0.008-0.013 elsewhere and every top lineage has bite 0. Hard cells pay for the first time since e012 (3.9 per body in flat seed 1), as armor on a body that is touched 0.5-0.8 times a step.",
    "c5": "yes", "l5": "Yes, in the crowd state", "v5": "The crowd-state runs eat 115 (mountains), 120 (half breath) and 105-134 (flat) per step against e021's 83, 100-109 and 105-113: the bodies' shadow falls from 29-38% of the sun to 0.5-0.7%, because a body in a crowd stands on a tree whose crown takes light above it. The mixed-state runs eat 97-111, inside or under e021's range, and high seed 1 eats 84.2, e021's income. Sun lost to empty soil is 15-34% (control 20-26%): a full column with no soil takes light and wastes it.",
    "c6": "yes", "l6": "Yes (from the pilot)", "v6": "With the fall spread over the 24 cells within distance 2, the mountain world dropped 19-25 of fruit per step against 80-120 at radius 1, ate 13-16 of it against 45-70, lost 31-34% of the sun to empty soil, and its contacts were 0.13 against 0.3-0.5. A wide fall is a lawn with extra steps; the ring is a place.",
    "c7": "yes", "l7": "Yes", "v7": "13.5% of the children are clones in every run (e^-2 = 13.5%) at 2.00 mutations per child, and the control - e021's canopy with the per-base mutation - reproduces e021's mountain world: 81-84 eaten per step (e021: 83.2-83.8), a bar of 7-8 cells, lineages 1-2, contacts 0.03-0.05, trees 7-42, dead matter 1%.",
    "h1": "The world stands, once it has survived its start",
    "r1": "Every spill run starts the same way: with every cell at the cap and fruit falling from the first step the population doubles to 4,000 by step 100 and eats 45% of the world's plants; when the stock is gone the grazed cells cannot regrow, because every full column around them takes their whole sun (7-12 per step of regrowth against e021's 90 at the same point), and all of the sun goes to fruit lying on the rings of the surviving trees, clumped, while bodies that see two cells wander the dark lawn. Every seed falls to 200-500 bodies by step 500-1,000 (half seed 1 to 11); most climb back as the far lawn regrows and the crowds find the trees, and one in five does not. After that the runs are steady: the food eaten (left) is flat to a few percent between quarters, the population (right) varies 3-11%, more than e021's 1-3%, because a crowd's food is in piles.",
    "h2": "Fruit is the harvest, and the world has two states again",
    "r2": "Fruit is half to three quarters of everything eaten (top left), and the runs split into two states by it: at 70-77% (flat 1 and 4, high 2, half 2 from step 400,000, half 1 from 900,000) the bodies' shadow is gone, the crowd is thickest and the winner is the frame; at 44-62% the world is mixed, and high seed 1 at 8% is e021's orchard. 68-128 of fruit falls per step (top right) - in the crowd state most of the sun - out of the soil under the trees. The trees (bottom left) stand 290-660 to a run, e021's forest state made permanent and its orchard state gone, and they are eaten as much as e021's forests (bottom right). In the mountain worlds the fruit falls where the soil is, not where the rain is: 48 per step in the valleys of high seed 2 against 20 on the ridges (whose rain runs down to the lake), and the bodies follow it, 474 in the valleys against 254 on the ridges - e020's height sorting turned upside down. The maps show the lakes.",
    "h3": "A crowd forms, and it eats its dead",
    "r3": "Contacts (left) jump from e021's 0.01-0.09 to 0.2-0.8 per body per step - a body in the crowd state is touched three times every four steps - and they track the fruit share run for run. Dead matter (right) is 10-26% of the intake against e021's 1%: bodies die on the rings and are eaten where they lie, the scavenging e017 was written for arriving with the crowd, and the crowd's densest runs have the most of it (26% in flat seed 4).",
    "h4": "The crowd picks a new winner, and it is still one",
    "r4": "The biters' share (left) rises above zero for the first time since e012 - 0.006 on median in flat seed 1, peaks of 0.01-0.03 in seven runs - and falls back every time: a tooth is found, and does not pay enough to keep. Lineages alive (right) stay at 1-3. What changed is the winner. Where the fruit is three quarters of the food the body is a frame: 19-24 cells around the rim of the 8x8 grid and none inside, 7 world cells wide, 17-20 of them digestive and 1-4 hard at the corners, mass three times e021's bar. The hollow is the mechanism: the frame stands around a tree without holding it (a held tree still drops fruit, but the frame's own cells would shade its ring), and its guts sit on the eight cells where the fruit lands - a body shaped like the place that feeds it. In the mixed runs a middle body of 10-15 cells wins, and where the crowd never came the bar is unchanged. The gallery shows them, with the giant of 37 cells that a valley of high seed 3 afforded for 16,000 steps.",
    "h5": "The crowd state is the richest closed world so far",
    "r5": "Sun lost under the bodies (left) falls from e021's 29-38% to under 1% in the crowd state: a body on a tree no longer shades anything the tree cannot reclaim above it. Sun lost to empty soil (right) is 15-34%, the control's 20-26%: a full column takes light whether or not it has soil, and in the mountain worlds the ridges have the rain and the valleys the soil. The income is 115-134 per step in the crowd state, e021's record (112.9) passed in three worlds, while the mixed state sits at e021's level and high seed 1 at e021's mountain income.",
    "h6": "The ring, not the wide fall (from the pilot)",
    "r6": "At radius 2 the same law makes a quarter of the fruit and a fifth of the crowd, and loses a third of the sun to empty soil. A fall spread wide is fruit lying thin where bodies already stand, which is e015's lawn under the bodies again; the ring keeps the food beside the tree, where a body must come and stay. The runs were made at radius 1.",
    "h7": "Mutation per base: the distribution, not the world",
    "r7": "Clones (left) are 13.5% of the children in every run, as the binomial says, at 2.00 mutations per child; the control's four runs are e021's mountain world in every measure the table has, so the spill's differences from e021 are the spill's. Bodies by height (right) in the mountain worlds now follow the soil to the valleys: the crowd lives on the lake, where the fruit falls out of the deepest soil, and the ridges that held e020's and e021's crowds hold a third as many.",
    "viewer": "The mountain world, seed 2, the crowd state. The food layer shows the trees standing on the lake as bright points with the fruit lying around them, and the bodies - frames 7 cells wide - clustered on the rings, touching; the terrain layer shows the crowd on the low ground; the soil layer the lake it eats from. In the clip, watch a frame stand on a tree while the ring around it refills.",
    "discussion": "<p>The law was written to make a place where a crowd eats without silencing the tree, and it does: the tree keeps taking light with a body on it, the fruit lands beside it, and the bodies come and stay, touching each other three times in four steps where e021's touched once in ten. And the crowd changed the winning body - for the first time since e013 the answer is not a bar of gut cells but a hollow frame seven world cells wide that stands around a tree and eats its ring, with hard cells at its corners - which is what #19 asks a law to do. But it changed it to another single winner. The frame sweeps a run as completely as the bar did, and the mixed-state runs settle on a middle body just as completely: the pressures are stronger, and there is still one of them. What the crowd did not buy is the tooth. Bites appear (0.01-0.03 of the bodies, in seven runs) and vanish, and every long-lived lineage has bite 0: with a cell of flesh worth 0.02, a body of 20 cells is worth 0.4 plus its energy, a few steps of fruit, so a tooth that costs its cells and its contacts loses to a gut that eats what falls. The crowd is here; the prize is not, and that is #27.</p><p>The surprise is the start. Without saturation, a full crown takes every neighbor's light, so a grazed lawn among trees is dark and the world's whole production lies in piles on the rings; a body that sees two cells and stands in the dark starves next to a pile it cannot see. e021's world survived its start because full crowns took nothing; this one survives it one time in five by the crowds finding the trees before the last bodies die. This is not a flaw of the spill but the meeting of clumped food with a body that cannot see - the premise of #26, eyes that see far, arriving as a mortality. The other surprise is where the crowd lives: not on the ridges where the rain falls but on the lake where the soil pools, because fruit is grown out of the soil under the tree, and e020's height sorting turned over.</p><p>What the experiment does not show: whether the frame is the end of the line or a stage (a frame 7 world cells wide is the widest the 8x8 grid allows - #28's ceiling is reached in one step); whether the crowd state is entered from the mixed state by chance or by history (half seed 2 flipped at 400,000, half seed 1 at 900,000, half seed 4 flipped back at 400,000); and whether a start with soil in the ground, or eyes, removes the lottery.</p>",
    "conclusion": "The spill - a full crown keeps taking the light, a column under a body keeps taking it, and what a column cannot hold falls as fruit on the ring of eight - is kept as a law of the world at radius 1, with its start marked as the open wound: a fifth of the worlds die in their first 4,000 steps, in the dark under their own trees. It gives the closed world the crowd it has lacked since e012 (contacts 0.2-0.8 per body per step), the scavenging e017 was written for (dead matter a fifth of the intake), an income of 115-134 per step in its crowd state, and a new winning body, the hollow frame of 19-24 cells around a tree, seven world cells wide, with armor at its corners - one winner still, and no tooth. Mutation per base is kept: it does what it says and changes nothing else. The next steps follow from what the crowd exposed: #26 eyes that see far, because the start kills bodies that cannot see a pile two cells away, and #27 what flesh is worth, because the crowd is here and a body is still worth less than the fruit it stands beside; #24 weather stays after them.",
}


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "lineages":
        top_lineages()
    else:
        main()
