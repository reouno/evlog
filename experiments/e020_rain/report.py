#!/usr/bin/env python3
"""Build report.html for e020.

Charts: matplotlib, exported as SVG and inlined. Diagram: hand-written SVG.
Run from the repo root: uv run python experiments/e020_rain/report.py
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

E019 = os.path.join(HERE, "..", "e019_terrain")
# Places of a world: (id in the CSVs, name, color). Under the uniform sun a place is a height band (thirds of the cells by the
# terrain).
BANDS = [(0, "valleys (lowest third)", SERIES[0]), (1, "slopes (middle third)", SERIES[3]), (2, "ridges (highest third)", SERIES[1])]
# Worlds of this experiment: label -> run prefix, world size, places, seeds, whether the sun is uniform (always, here).
WORLDS = {
    "rain on the mountains, relief 64": dict(run="128_sigma0_r64_f0.1_high", size=128, places=BANDS, seeds=[1, 2, 3, 4], uniform=True),
    "half the breath to the air, relief 64": dict(run="128_sigma0_r64_f0.1_high-b0.5", size=128, places=BANDS, seeds=[1, 2, 3, 4], uniform=True),
    "rain everywhere alike, relief 64": dict(run="128_sigma0_r64_f0.1_flat", size=128, places=BANDS, seeds=[1, 2, 3, 4], uniform=True),
}
UNIFORM = list(WORLDS)
HIGH64, HALF, FLAT = list(WORLDS)
# e019's runs (the same terrains where what a body burns fell to the soil under it): label -> (run prefix, folder, uniform).
REFS = {"e019 relief 64 (to the soil)": ("128_sigma0_r64_f0.1", E019, True), "e019 relief 256 (to the soil)": ("128_sigma0_r256_f0.1", E019, True)}
WORLD_COLOR = {HIGH64: SERIES[0], HALF: SERIES[1], FLAT: SERIES[3], "e019 relief 64 (to the soil)": INK, "e019 relief 256 (to the soil)": "#c6c4bb"}
KIND_COLOR = {1: SERIES[0], 2: SERIES[1], 3: SERIES[3], 4: SERIES[2]}
CONFIRM_STEPS = 5000
MAIN = HIGH64
VIEWER_WORLD = HIGH64
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
<svg viewBox="0 0 800 340" role="img" aria-label="A cross-section of the world of e020: a terrain with two ridges and a valley between them under a uniform sun; the air above it as one pool that receives what bodies burn (breath rising from the bodies) and rains on the ground, more the higher the ground: up to 0.01 per cell per step on the peaks, almost nothing on the valley floor. The ridges hold a thin soil with plants and bodies; the valley, e019's lake, has drained into the air; soil trickles down the slopes." style="max-width:100%;height:auto;display:block">
<g fill="none" stroke="currentColor" stroke-width="1.2" font-size="12" font-family="system-ui, sans-serif">
  <!-- the sun: the same on every cell -->
  <g stroke="#eda100" stroke-width="1.4">
    <path d="M 60,14 L 60,34 M 160,14 L 160,34 M 260,14 L 260,34 M 360,14 L 360,34 M 460,14 L 460,34 M 560,14 L 560,34 M 660,14 L 660,34 M 760,14 L 760,34" marker-end="url(#sunhead)"/>
  </g>
  <text x="400" y="50" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">sun: 0.01 per cell per step, everywhere; a plant grows out of its cell's soil by at most this</text>
  <!-- the air -->
  <rect x="40" y="58" width="720" height="26" rx="4" fill="var(--cell)" stroke="currentColor" stroke-dasharray="4 3"/>
  <text x="400" y="75" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">the air: one pool; what a body burns (upkeep, the work of moving) rises here</text>
  <!-- rain: dense on the ridges, sparse in the valley -->
  <g stroke="var(--s1)" stroke-width="1.5">
    <path d="M 100,92 L 100,112 M 130,92 L 130,106 M 160,92 L 160,102 M 190,92 L 190,102 M 220,92 L 220,110 M 250,92 L 250,120" marker-end="url(#rainhead)"/>
    <path d="M 430,92 L 430,116 M 460,92 L 460,106 M 490,92 L 490,100 M 520,92 L 520,102 M 550,92 L 550,112" marker-end="url(#rainhead)"/>
    <path d="M 340,92 L 340,124" stroke-dasharray="2 4"/>
  </g>
  <!-- breath rising from the bodies -->
  <g stroke="currentColor" stroke-width="1.2" stroke-dasharray="3 3">
    <path d="M 172,102 L 172,92 M 500,96 L 500,92 M 415,150 L 415,92" marker-end="url(#breathhead)"/>
  </g>
  <!-- the ground: two ridges, a valley between them, the right edge stepping down to the label column -->
  <path d="M 40,215 L 110,128 L 180,112 L 250,152 L 300,202 L 350,238 L 405,212 L 455,162 L 510,108 L 555,138 L 590,178 L 590,340 L 40,340 Z" fill="var(--cell)" stroke="currentColor" stroke-width="1.5"/>
  <!-- thin soil on the ridges and slopes, none on the valley floor -->
  <path d="M 110,128 L 180,112 L 250,152 L 300,202" stroke="#b5773a" stroke-width="4" stroke-opacity="0.6" stroke-linecap="round"/>
  <path d="M 405,212 L 455,162 L 510,108 L 555,138" stroke="#b5773a" stroke-width="4" stroke-opacity="0.6" stroke-linecap="round"/>
  <!-- plants: dense on the ridges, sparse below -->
  <g stroke="#1baf7a" stroke-width="2" stroke-linecap="round">
    <path d="M 120,124 L 120,114 M 145,117 L 145,107 M 200,116 L 200,106 M 230,140 L 230,130 M 270,168 L 272,159"/>
    <path d="M 470,148 L 472,138 M 490,128 L 490,118 M 530,120 L 530,110 M 550,134 L 550,124 M 425,200 L 427,191"/>
    <path d="M 352,236 L 352,230"/>
  </g>
  <!-- the flow arrows -->
  <path d="M 262,162 L 292,190" stroke="#b5773a" stroke-width="1.6" marker-end="url(#flowhead)"/>
  <path d="M 448,172 L 416,204" stroke="#b5773a" stroke-width="1.6" marker-end="url(#flowhead)"/>
  <!-- bodies on the ridges and one on a slope -->
  <rect x="160" y="104" width="22" height="9" rx="1.5" fill="var(--s1)" stroke="none"/>
  <rect x="489" y="98" width="22" height="9" rx="1.5" fill="var(--s1)" stroke="none"/>
  <rect x="404" y="152" width="22" height="9" rx="1.5" fill="var(--s1)" stroke="none"/>

  <!-- labels: the column on the right -->
  <text x="610" y="106" fill="var(--s1)" stroke="none" font-weight="600">rain</text>
  <text x="610" y="122" fill="currentColor" stroke="none">at most 0.01 x height / relief</text>
  <text x="610" y="138" fill="currentColor" stroke="none">per cell per step; what cannot</text>
  <text x="610" y="154" fill="currentColor" stroke="none">fall stays in the air</text>
  <text x="610" y="182" fill="currentColor" stroke="none" font-weight="600">breath</text>
  <text x="610" y="198" fill="currentColor" stroke="none">e019 dropped it under the</text>
  <text x="610" y="214" fill="currentColor" stroke="none">body; the dead still lie and</text>
  <text x="610" y="230" fill="currentColor" stroke="none">rot where they fell</text>
  <text x="610" y="258" fill="currentColor" stroke="none" font-weight="600">flow</text>
  <text x="610" y="274" fill="currentColor" stroke="none">e019's: soil runs downhill</text>
  <text x="610" y="290" fill="currentColor" stroke="none">and levels; rain not caught</text>
  <text x="610" y="306" fill="currentColor" stroke="none">by the sun runs to the valley</text>
  <!-- labels: inside the ground -->
  <text x="165" y="190" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">ridge</text>
  <text x="165" y="206" text-anchor="middle" fill="currentColor" stroke="none">rain near the sun's rate:</text>
  <text x="165" y="222" text-anchor="middle" fill="currentColor" stroke="none">a thin soil, plants, bodies</text>
  <text x="330" y="266" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">the valley (e019's lake)</text>
  <text x="330" y="282" text-anchor="middle" fill="currentColor" stroke="none">its soil drained into the air through the bodies; what it</text>
  <text x="330" y="298" text-anchor="middle" fill="currentColor" stroke="none">gets now is the dead, the runoff and a little rain.</text>
  <text x="330" y="314" text-anchor="middle" fill="currentColor" stroke="none">"flat": the same rain everywhere; "soil": e019; "half": both</text>
</g>
<defs>
  <marker id="sunhead" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="#eda100"/></marker>
  <marker id="rainhead" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="var(--s1)"/></marker>
  <marker id="breathhead" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="currentColor"/></marker>
  <marker id="flowhead" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="#b5773a"/></marker>
</defs>
</svg>
<figcaption>Figure 1. The world in cross-section. e019's closed world (matter is in the soil of a cell, in the plant on it, lying dead on it, or in a body; a plant grows out of its own cell's soil at most the sun's rate; the ground has a height and soil runs downhill and levels; the dead rot where they fell) with one law changed: what a body burns goes to the air, not to the soil under it, and the air rains on the ground, on every cell at most the sun's worth per step times the cell's height over the relief; what cannot fall stays in the air. Rain lands in the soil, where the sun draws it into the plant or the flow carries it downhill. The high ground gets an income that does not come from the soil, and the world's idle store moves from the lake to the air. The controls: the same air raining on every cell alike ("flat"), half of the breath to the air and half to the soil under the body ("half"), and e019 ("soil").</figcaption>
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
                 matter_hold=log["matter"][-1] / log["matter"][0], air_end=log["air"][-1], soil_end=log["soil"][-1], rain=med(half(log, "rain")),
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
        if key == "soil_end":
            return med([L[s]["soil"][-1] for s in seeds])
        if key == "mass":
            key = "mass_mean"
        if key not in L[1]:
            return float("nan")
        return med([med(half(L[s], key)) for s in seeds])

    logs_ref = dict(logs)
    logs_ref.update({w: rlogs[w] for w in REFS})
    all_worlds = list(WORLDS) + list(REFS)
    ref64, ref256 = list(REFS)

    charts = {}
    charts["eaten"] = world_chart("Food eaten per step", "Plant and dead matter taken by guts per step, one line per run; gray: e019 at relief 64 (dark) and 256 (light), where what a body burned fell to the soil under it. The sun gives 164 per step in every world; the rain's caps add up to 82 with rain on the mountains. A line that ends is a world that died.", logs_ref, eaten_of, all_worlds, WORLD_COLOR)
    charts["pop"] = world_chart("Population", "Bodies alive at each log step, one line per run; gray: e019's runs of the same terrains.", logs_ref, lambda l: l["pop"], all_worlds, WORLD_COLOR)
    charts["barren"] = world_chart("Sun lost to empty soil", "Share of the sun that shone on a cell whose soil had nothing left, per log window, one line per run; gray: e019. In e019 this is the ridges' third of the sun.", logs_ref, lambda l: [b / max(r + sh + wa + b, 1e-9) for r, sh, wa, b in zip(l["regrowth"], l["shaded"], l["wasted"], l["barren"])], all_worlds, WORLD_COLOR, percent=True)
    charts["soil_cells"] = world_chart("Cells with soil", "Share of the cells holding at least a step of sun's worth of soil (0.01), at each log step, one line per run: the area of the world that can grow a plant this step.", logs, lambda l: l["soil_cells"], list(WORLDS), WORLD_COLOR, percent=True, ymax=1.0)
    charts["air"] = world_chart("Matter in the air", "What bodies have burned and the rain has not yet returned, at each log step, one line per run. The world holds 139,700 in all; a line that climbs and levels is a store forming in the air; one that stays at zero is air that empties every step.", logs, lambda l: l["air"], list(WORLDS), WORLD_COLOR)
    charts["soil_total"] = world_chart("Matter in the soil", "Soil of the whole world at each log step, one line per run; gray: e019, where the soil held 135,000 of the 139,700 at the end. A line that falls is the lake draining into the air.", logs_ref, lambda l: l["soil"], all_worlds, WORLD_COLOR)
    charts["rain"] = world_chart("Rain per step", "Matter fallen from the air on the whole world per step, one line per run. With rain on the mountains the caps add up to 82 per step; a flat line at 82 means the air is never short. With rain everywhere alike the caps add up to 164 and the line is what the bodies burned.", logs, lambda l: l["rain"], list(WORLDS), WORLD_COLOR)
    charts["soil_band"] = place_chart(f"Soil per cell by height, {HIGH64}", "Matter in the soil per cell of each height band (thirds of the cells by the terrain), at each log step, one line per seed. e019 ended at 19-22 in the valleys, 4-6 on the slopes, 0 on the ridges.", places, HIGH64, lambda d: [so / c for so, c in zip(d["soil"], d["cells"])])
    charts["pop_band"] = place_chart(f"Bodies by height, {HIGH64}", "Bodies standing in each height band at each log step, one line per seed. The bands are equal in cells (5,461 each). e019: 0-14 on the ridges.", places, HIGH64, lambda d: d["pop"])
    charts["pop_band_half"] = place_chart(f"Bodies by height, {HALF}", "Bodies standing in each height band at each log step, one line per seed: half of what a body burns rains on the mountains, half falls to the soil under it.", places, HALF, lambda d: d["pop"])
    charts["soil_band_half"] = place_chart(f"Soil per cell by height, {HALF}", "Matter in the soil per cell of each height band, one line per seed: whether a lake survives when half of the breath still falls to the ground.", places, HALF, lambda d: [so / c for so, c in zip(d["soil"], d["cells"])])
    charts["pop_band_flat"] = place_chart(f"Bodies by height, {FLAT}", "Bodies standing in each height band at each log step, one line per seed.", places, FLAT, lambda d: d["pop"])
    charts["eaten_band"] = place_chart(f"Food eaten per step by height, {HIGH64}", "Plant and dead matter eaten per step by the bodies standing in each band, one line per seed. Each band gets 54.6 of sun per step; the rain's caps give the ridges about 37, the slopes 27 and the valleys 18.", places, HIGH64, lambda d: [(a + b) / 10_000 for a, b in zip(d["plant_intake"], d["meat_intake"])])
    charts["rain_band"] = place_chart(f"Rain per step by height, {HIGH64}", "Matter fallen on the cells of each band per step, one line per seed. The cap of a cell is the sun's worth (0.01) times its height over the relief.", places, HIGH64, lambda d: d["rain"])
    charts["top"] = stats_chart("Where the soil lies: the richest tenth of the cells", "Share of the world's soil held by its richest tenth of cells, every 100,000 steps, one line per run. 10% is soil spread evenly; e019's lake read 32-35% at relief 64 and 63-70% at 256.", STATS, lambda d: d["top"], list(WORLDS), percent=True, ymax=1.0)
    charts["under"] = stats_chart("Soil under the bodies over soil elsewhere", "Mean soil of the cells with a body on them over the mean of the cells without, every 100,000 steps, one line per run. Above 1, bodies stand where the soil is; e019: 1.6-2.0 at relief 64, 3.7-4.5 at 256.", STATS, lambda d: d["under"] / max(d["free"], 1e-9), list(WORLDS), ymin=0)
    charts["maps"] = terrain_soil_figure("The terrain and the soil at the end", "Top: the terrain of seed 1 of each world (white high, black low). Bottom: soil per cell at step 1,000,000 (or the last dump before the world died), darker is more (log scale, 30 and above black).", [(w, seeds_of(w)[0]) for w in WORLDS])
    charts["lineages"] = world_chart("Lineages alive", "Confirmed lineages at each log step, one line per run; gray: e019 (1 at relief 64, 1-2 at 256).", logs_ref, lambda l: l["lineages"], all_worlds, WORLD_COLOR)

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
    by_band = lambda k: {w: f"{k}_0|{k}_1|{k}_2" for w in WORLDS}
    uniform_only = lambda k: {w: k for w in WORLDS}
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
               + row("Rain per step", "rain", d1)
               + row("Matter in the air at the end", "air_end", n0)
               + row("Matter in the soil at the end", "soil_end", n0, "soil_end")
               + row("Soil per cell at the end: valleys / slopes / ridges", by_band("soilend"), d1)
               + row("Bodies: valleys / slopes / ridges", by_band("pop"), n0)
               + row("Eaten per step: valleys / slopes / ridges", by_band("eaten"), d1)
               + row("Mass: valleys / slopes / ridges", by_band("mass"), d1)
               + row("Bodies in the lowest two thirds at the end, share", uniform_only("low_pop"), p0)
               + row("Richest tenth of the cells, share of the soil at the end", "top", p0)
               + row("Soil under the bodies over soil elsewhere, at the end", "under", d2)
               + row("Soil moved per step", "flow", d1)
               + row("Matter at the end over the start", "matter_hold", lambda v: f"{v:.4f}")
               + row("Lineages alive", "lineages", n0, "lineages")
               + row("Mass", "mass", d1, "mass")
               + row("Contacts per body per step", "contacts", d3, "contacts")
               + row("Steps per second", "sps", n0, "steps_per_sec")
               + "</tbody>")

    tables = data_table(["step", "place", "pop", "mass", "hard", "muscle", "digestive", "cover", "foot", "plant_intake", "meat_intake", "dead", "carrion", "soil", "rain", "barren", "regrowth", "cells", "lineages", "movers"],
                        {f"{w}, seed {s}, {place_names(w)[p]} (every 100,000 steps)": places[w][s][p] for w in WORLDS for s in seeds_of(w) for p, _, _ in WORLDS[w]["places"] if p in places[w][s]}, every=10)
    tables += data_table(["step", "pop", "births", "deaths_energy", "mass_mean", "forward", "blocked", "foot_mean", "cover", "contacts", "regrowth", "shaded", "wasted", "barren", "rot", "spent", "flow", "rain", "air", "soil_cells", "deep", "soil", "matter", "plant_intake", "meat_intake", "lineages", "steps_per_sec"],
                         {f"{w}, seed {s}, whole world (every 100,000 steps)": logs[w][s] for w in WORLDS for s in seeds_of(w)}, every=10)

    text = TEXT
    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>e020 The breath rises and the rain falls on the mountains - Report</title>
<style>{CSS}</style>
</head>
<body>
<main>
<h1>e020: The breath rises and the rain falls on the mountains</h1>
<p class="sub">Experiment report - 2026-08-31 - e019's closed world with one law changed: what a body burns goes to the air, and the air rains on the mountains. Rain by height at relief 64, half the breath to the air and half to the soil, and the same rain on every cell alike, 128x128, four seeds each, 1,000,000 steps; e019's relief 64 and 256 as the reference</p>

<section class="tldr">
<h2>TL;DR</h2>
<p>{text["tldr"]}</p>
</section>

<h2>1. Question</h2>
<p>{text["question"]}</p>
<ol>
  <li><strong>The high ground lives.</strong> With rain on the mountains at relief 64 the ridges (the highest third of the cells) hold 400-700 bodies at the end (e019: 0-14) and eat 25-35 per step (e019: 0.4); the slopes 20-30 and the valleys 15-25, so that the food eaten falls with height the way the rain does, and bodies stand at every height.</li>
  <li><strong>The store moves to the air.</strong> The lake's soil drains: the soil holds under 40,000 of the world's 139,700 by step 200,000 (e019: 135,000 at the end), the air holds 60,000-100,000, and the rain falls at its cap over the second half. Matter is conserved to 0.01%.</li>
  <li><strong>The world stands, with the air as its store.</strong> Food eaten and population steady over the second half (quarter medians within 10%, coefficient of variation under 0.10), no extinction, in all four seeds; the world eats 75-95 per step (e019 at relief 64: 56-71) and holds 1,500-2,000 bodies.</li>
  <li><strong>The relief stops setting the world's income.</strong> At relief 256 the world eats within 15% of what it eats at relief 64 (e019: 26-31 against 56-71), because the rain field has the same shape at every relief.</li>
  <li><strong>Rain on every cell alike has no store and swings.</strong> The flat control drains the lake too, but no cell's income exceeds the sun, so the air empties every step and the matter has nowhere to sit but in plants and bodies: the population overshoots and falls 2x or more (coefficient of variation over 0.20) or the world dies in at least one seed of four.</li>
  <li><strong>The same body wins at every height.</strong> Judged by #19 the law by itself does not make more winners: a bar of 6-10 gut cells is the top body in every band, lineages alive 1-2, contacts under 0.1 per body per step, no bite. If a band's top body differs from the lake's (in mass, muscle or extent) in three seeds of four, that is the first place effect under the uniform sun.</li>
</ol>

<h2>2. The world</h2>
<p>{text["world"]}</p>
{DIAGRAM}
<p>{text["runs"]}</p>
<ul class="measures">
  <li><strong>Air</strong> (<code>air</code>): matter in the air at the log step, what bodies burned and the rain has not returned. <strong>Rain</strong> (<code>rain</code>): matter fallen on the ground per step; per place in <code>places.csv</code>. The rain mode and the breath share are in <code>terrain.json</code>.</li>
  <li><strong>Places by height</strong>: the place of a cell is its band (the lowest third of the cells by the terrain, the middle third, the highest third), so the per-place log (population, body means, intake, soil, rain, barren sun, lineages, movers) reads by height. Each agent and lineage also carries the terrain height under it.</li>
  <li><strong>The soil map</strong> (<code>soil.jsonl</code>, every 100,000 steps): the share of the soil in the richest tenth of the cells, the soil per cell and its share per place, the share of the bodies standing in each place, the shares of bare and wet cells, and the soil under the bodies over the soil elsewhere.</li>
  <li>e019's measures: sun split into grown, shaded, wasted and barren; soil, spent, rot, flow, matter; population, food eaten, dead matter, contacts, moves, lineages and events, snapshots with the terrain and the soil as layers.</li>
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
{charts["pop_band"]}{charts["eaten_band"]}
</div>
<div class="grid2">
{charts["rain_band"]}{charts["soil_band"]}
</div>
<p>{text["r1"]}</p>

<h3>3.2 {text["h2"]}</h3>
<div class="grid2">
{charts["air"]}{charts["soil_total"]}
</div>
<div class="grid2">
{charts["rain"]}{charts["barren"]}
</div>
<div class="wide">{charts["maps"]}</div>
<p>{text["r2"]}</p>

<h3>3.3 {text["h3"]}</h3>
<div class="grid2">
{charts["eaten"]}{charts["pop"]}
</div>
<div class="grid2">
{charts["pop_band_half"]}{charts["soil_band_half"]}
</div>
<p>{text["r3"]}</p>

<h3>3.4 {text["h4"]}</h3>
<div class="grid2">
{charts["lineages"]}{charts["under"]}
</div>
<p>{text["r4"]}</p>

<h3>3.5 {text["h5"]}</h3>
{gallery(GALLERY)}
<p>{text["r5"]}</p>


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
<p>Every 100,000th record; full logs in <code>results/*_log.csv</code>, per place in <code>results/*_places.csv</code>, lineages in <code>results/*_lineages.csv</code>, events in <code>results/*_events.csv</code>, agents every 100,000 steps in <code>results/*_agents.csv</code>, the terrain (with the rain mode) in <code>results/*_terrain.json</code>, the soil and plants of every cell every 100,000 steps in <code>results/*_soil.jsonl</code>, snapshots in <code>results/*_{{long,clip,bodies}}.jsonl</code>. Reference runs are read from <code>../e019_terrain/results</code>. Build this report with <code>uv run python experiments/e020_rain/report.py</code>.</p>
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
    ("rain on the mountains, relief 64", 1, 57, "the bar on the mountain", "Eight digestive cells 2 by 8 over 3.2 world cells, the main lineage of seed 1 from step 262,000 (1,333 agents at its peak), half of it standing on the ridges at a mean height of 34: e019's mower, moved uphill to where the rain is."),
    ("rain on the mountains, relief 64", 1, 76, "the lower bar", "Seven digestive cells, a cell lighter and a row thinner, living 520,000 steps beside lineage 57 at 401 agents, its members standing lower (height 30 against 34, only 118 of 401 on the ridges): the first second lineage that holds a lower band of the same slope."),
    ("rain on the mountains, relief 64", 2, 86, "the valley body", "Six digestive cells, the smallest body of the run, 126 agents for 49,000 steps with 121 of them in the valleys at a mean height of 21, under a main lineage of mass 8.7 standing at 38: where the rain is thin, a cheaper body pays."),
    ("rain on the mountains, relief 64", 3, 29, "the outrigger", "A front row of digestive cells with one cell trailing six rows behind it, spanning 7.8 cells along the facing: the deepest footprint of the mountain worlds, walking forward 53% of its decisions, the main lineage of seed 3 for 734,000 steps (1,796 agents)."),
    ("half the breath to the air, relief 64", 3, 1, "the bar of the full world", "Eight digestive cells 2 by 6 over 2.8 world cells, the one lineage of seed 3 from step 5,000 to the end (2,177 agents): the world where the lake keeps the store, the rain feeds the ridges, 99% of the cells are wet and the whole sun less shading is eaten. The same body at every height."),
    ("rain everywhere alike, relief 64", 2, 1, "the thin bar of the lawn", "Six digestive cells in a single row of 8, mass 5.6, the one lineage of its seed for the whole run (2,310 agents at its peak), spread evenly over the bands: rain that falls everywhere alike puts the world back on e019's flat lawn, terrain and all."),
]


TEXT = {
    "question": "e019 made the closed world stand and left it with one place: at the end of its runs 97% of the matter lies idle in the soil of a level lake, the plants on the lake are grazed to the ground, and the ridges hold no soil, no plant and no body, because matter reaches a cell only through the soil and soil runs off the high ground. No law about the high ground (cold, slope, the plants there) can act until something is up there for a body. This experiment gives the high ground an income that does not come from the soil, the real world's way: what a body burns leaves it as breath, the air is everywhere, and the rain falls on the mountains and runs back down. What a body burns (its upkeep and the work of its moving) goes to one pool of air; each step the air rains on every cell at most the sun's worth (0.01) times the cell's height over the relief, and what cannot fall stays in the air; rain lands in the soil, where the sun draws it into the plant or the flow carries it downhill; the dead still lie where they fell. Twelve runs at relief 64: all of the breath to the air, half of it (the other half to the soil under the body, as in e019), and the same air raining on every cell alike; e019's runs are the reference. The hypotheses, written before the pilot:",
    "world": "Everything is e019's (128x128 on a torus, matter 8 per cell at the start as plants, bodies of 8x8 cells in five kinds grown from the genome, space at the resolution of the body, a facing, e010's contact rule, a cell that costs what it holds, 0.032 per body per step, work = force x distance, a cell held by a body does not regrow, a dead body is food where it lies, a plant grows out of its own cell's soil at most the sun's rate, the dead rot into the soil, a terrain of relief 64 in soil units, soil that runs downhill and levels, a uniform sun) with the air added (Figure 1): what a body burns rises to the air instead of falling to the soil under it, and the air rains on the ground by height. Two new arguments: the rain (high: by height; flat: the same everywhere; soil: e019) and the breath (the share of what a body burns that goes to the air; the rest falls to the soil under the body). The place of a cell is its height band, thirds of the cells by the terrain: valleys, slopes, ridges.",
    "runs": "<strong>Runs.</strong> Rain on the mountains with all of the breath to the air, with half of it, and rain on every cell alike, all at relief 64 and flow 0.1, twelve runs at once on one machine, one thread each, 1,000,000 steps, seeds 1-4. A pilot (seed 9, 100,000 steps) came first: it showed the relief no longer matters with all of the breath in the air (relief 256 is the same world to 0.1%), so the relief 256 runs were dropped for the half-breath world. Reference: e019's uniform sun at relief 64 and 256, seeds 1-4, where everything a body burned fell to the soil under it. We record e019's measures and:",
    "tldr": "The high ground lives: with the breath in the air and the rain falling by height, the ridges that held 0-14 bodies in e019 hold 658-670, the world eats 73-94 per step (e019: 56-71) with no extinction and no swing, and the world's idle store moves from the lake's soil to the air within 10,000 steps, the soil map turning from a lake into rivers that run from under the crowds back to the valley floor. The bodies sort by height, a little: mass rises from the valleys to the ridges in all four runs (7.1-8.0 to 7.7-9.1 at birth), the thin valleys keep the smaller variants and, twice, a second lineage that stands lower, so a place law under a uniform sun has its first visible effect on bodies; but every winner is still a gut bar, nothing bites, and lineages stay at 1-2. Half the breath to the air is the best world of the series: the lake keeps the store, the rain feeds the ridges, 99-100% of the cells are wet, nothing but shading is lost (102.9-109.1 eaten per step of the sun's 164) and 2,000-2,300 bodies live evenly at every height, but the bands then differ in nothing and one body wins them all. Rain that falls everywhere alike does not swing as predicted: it quietly rebuilds e019's flat lawn with the terrain moot. The store, it turns out, sits wherever the draw is capped: in the lake when the breath falls back locally, in the air when the rain is the bottleneck.",
    "c1": "yes", "l1": "Yes", "v1": "With all of the breath in the air the ridges hold 658-670 bodies at the end (e019: 0-14) and eat 34-36 per step (asked 25-35; e019: 0.0-0.5), the slopes 507-653 bodies and 26.0-35.1, the valleys 268-484 and 13.4-25.0: the food eaten falls with height exactly the way the rain does (Figure 3.1), and every band holds bodies in every seed. The soil under the bodies over the soil elsewhere is 1.2-1.5 (e019: 1.6-2.0 at this relief): bodies no longer stand on the store, they stand under the rain.",
    "c2": "yes", "l2": "Yes", "v2": "The lake drains into the air within about 10,000 steps (asked by 200,000): the soil holds 2,239-7,262 at the end of the run (e019: 135,550-136,970 of the world's 139,700) and the air 129,319-134,672, an idle store the viewer cannot see but the log can. The rain then falls at its cap every step: 72.4-92.5 per step, the cap being 164 times each terrain's mean height over the relief, which the seeds draw at 0.44-0.56. Matter holds to 0.02% over the million steps (e019's f32 runs: up to 1.8%).",
    "c3": "yes", "l3": "Yes", "v3": "Food eaten per step is 72.8-94.3 over the second half (asked 75-95), the last quarter 0.998-1.000 of the third, the population 1,442-1,778 (asked 1,500-2,000) with a coefficient of variation of 0.009-0.019 and a swing of 1.04-1.07x; no extinction in any run. The spread over seeds is the terrain's: a seed whose ground stands higher on average catches more rain (seed 2 at a mean of 0.56 of the relief eats 94.3, seed 1 at 0.44 eats 72.8), which is new; in e019 the seeds agreed to 10% because every lake drew the same sun.",
    "c4": "yes", "l4": "Yes, by the pilot", "v4": "At relief 256 the pilot's world is the same as relief 64 to 0.1% (78.3 against 78.2 eaten, 1,547 against 1,487 bodies, 690 against 673 on the ridges at step 100,000): the rain cap is height over relief, so the rain field has the same shape whatever the relief, and the lake, which the relief used to set, is gone. The relief 256 runs were dropped; the seed 9 numbers stand as the answer.",
    "c5": "no", "l5": "No: it rebuilds the lawn", "v5": "Rain on every cell alike neither swings nor dies: 100.4-103.3 eaten per step, 1,928-2,226 bodies, coefficient of variation 0.008-0.019, in all four runs. The prediction missed where the store would sit: every cell gets 0.0061-0.0062 per step from the air and draws the difference to the sun's 0.01 from the soil under it, so the lake drains only until the population has grown to where the cells bodies stand on cap the draw at what the rain returns, and the lake then sits untouched (136,019-136,511 at the end) as a passive store. The world is e019's flat lawn with the terrain moot: the bands differ by 1-4% in bodies and the air empties every step.",
    "c6": "no", "l6": "No: the bodies sort by height", "v6": "The caveat came true, three seeds of four and more. Mass at birth rises from the valleys to the ridges in all four mountain-rain runs (7.29/7.48/8.19, 8.04/8.97/9.05, 7.07/7.38/7.67, 8.03/7.98/8.17): the same lineage's smaller variants (6-cell bars) hold a third of the valleys and the full 8-9-cell bars nearly all of the ridges. Twice a second lineage stands lower for 309,000-520,000 steps (seed 1's lineage 76 at height 30 under the main line's 34; seed 2's lineage 86 with 121 of its 126 agents in the valleys at height 21 under a main line at 38). But every winner is a gut bar with no muscle, no hard cell and no bite, contacts are 0.009-0.042 per body per step, and lineages alive stay 1-2 (half: 1-4, flat: 1).",
    "h1": "The high ground lives, and the rain draws the world",
    "r1": "With the breath in the air, the map of life is the map of the rain. Bodies stand in every band (Figure 3.1 left), most where the rain cap is highest, and the food eaten per band tracks the rain per band to within the runoff (the ridges eat 34-36 of their 39-45 of rain; the valleys eat 13-25, their own 11-17 of rain plus what runs down to them). e019's picture is exactly inverted: there the lowest two thirds held 99-100% of the bodies and the ridges 0-14; here the ridges are the crowded band (658-670) and the valleys the thin one (268-484). The soil per cell is thin everywhere (0.02-0.55, against a lake of 19-22): what the maps show now is not a store but a flow, soil in transit from under the crowds downhill.",
    "h2": "The store moves from the lake to the air",
    "r2": "The lake drains through the bodies into the air in the first 10,000 steps and stays there: the air holds 129,000-135,000 of the world's 139,700 for the rest of the run (left), the soil 2,200-7,300 (right), and the rain falls at its cap every step, 72-93 per step by the seed's terrain. What the ground keeps is rivers: rain that lands where a body stands is not drawn by the sun (a held cell does not grow), so it runs downhill, 221-536 of soil moved per step against e019's 66-77, and the last soil maps (Figure 3.2 bottom) show veins running from the ridges down to a thin remnant pool on the valley floor. The sun lost to empty soil falls from e019's 34-46% to 10-29%, all of it now in the valleys, at the bottom of the rain.",
    "h3": "Half the breath makes the best world, and erases the bands",
    "r3": "Sending half of what a body burns to the air and dropping half under the body keeps both stores: the lake stays at 135,900-136,300 of soil (the air empties every step, 51-55), the ridges get 25-28 of rain per step, 99-100% of the cells hold soil, and the world eats 102.9-109.1 per step, the whole sun less the 33-38% shaded by bodies standing on cells, with 2,002-2,268 bodies; nothing but shading is wasted in a closed world for the first time. But abundance erases the places: the three bands hold the same 666-757 bodies each, eat the same 35.5-37.9, and grow the same body, and lineages alive are 1 (seed 1 turns over through 4). Rain on every cell alike (right: its soil by band) reaches nearly the same world by a different route, e019's lawn with the lake untouched below it; the bands differ only where the ridges run 1.5-2.7 of barren sun. Richness is bought with sameness: the closed world eats most when no place differs from another.",
    "h4": "One winner still, but it lives at a height",
    "r4": "Lineages alive stay at 1-2 with the breath in the air (left), 1-4 with half, 1 with rain everywhere: judged by #19's count the law does not multiply winners. What it does, for the first time under a uniform sun, is give the one winner a height: mass at birth rises from the valleys to the ridges in all four mountain-rain runs, the small variants of the winning bar persist in the thin valleys, and twice a second lineage holds the lower ground for 309,000-520,000 steps against a main lineage on the ridges. The soil under the bodies over the soil elsewhere (right) reads the same change: e019's 1.6-4.5 (bodies stand on the lake, the store) falls to 1.2-1.5 (bodies stand under the rain, and the store is over their heads).",
    "h5": "The bodies",
    "r5": "Every winner is still a bar of digestive cells, 6-9 of them, 1-2 rows deep, walking forward a third to a half of its decisions; nothing has a tooth and contacts stay at 0.005-0.123 per body per step. What is new is where each bar lives and how big it is there: the full-size bar on the ridges, the lighter variants and the second lineages below it, and in seed 3 a bar trailing an outrigger cell six rows behind its front, the deepest footprint of the series, walking forward 53% of its decisions. The half-breath and flat worlds grow the same bars with no height structure at all.",
    "viewer": "Rain on the mountains, seed 1. The terrain layer shows the bodies standing on the high ground (light) and thinning toward the valleys (dark), the reverse of e019's viewer; the soil layer shows rivers, veins of brown running downhill from under the crowds, with a small pool at the valley floor where e019 had the lake; the food layer is a thin even green over the heights. From step 262,000 the world is lineage 57 (blue) with lineage 76 living below it from step 485,000 (the second color, lower on the slopes); nothing else changes, which is the point: the closed world stands with its store in the sky.",
    "discussion": "<p>The law does what it was written for: the high ground lives, on an income the soil cannot hold. The world's shape is no longer where matter pools but where it falls, the map of life inverts to match, and the store that made the closed world stand in e019 survives the move from the lake into the air, invisible but steady, with the population's coefficient of variation still under 0.02 over a million steps. The closed cycle now has two honest pools, the ground's and the sky's, and the choice of route (breath against dung) decides which one holds the world's wealth.</p><p>The bodies answered, faintly but in every seed: mass sorts by height. The mechanism is visible in the numbers: a cell of rain in the valleys carries a quarter of a ridge cell's rain, a bar of eight gut cells cannot fill there and a bar of six can, so the thin band keeps the small variant alive and, twice, a whole lineage of it. That is the first time a place under the uniform sun shaped a body, and it is the pattern #14 wants, at a tenth of the strength wanted: the same bar, graded, not a different body. The gradient is one axis of income; a body that differs in kind seems to need a place that differs in kind, not in amount.</p><p>The half-breath world is the surprise. It was added as a control on the store and turned out to be the strongest world of the series: both stores, rivers, every cell wet, the whole sun (less shading) eaten, no waste, no swing. But its abundance is uniform, its bands hold identical bodies at identical densities, and its lineage count is e019's. The comparison of the three worlds is clean: rain by height buys places at the cost of a fifth of the food (the valleys' barren sun); rain everywhere and half-breath buy food at the cost of every place; e019's soil-only route bought a lake and a desert. A closed world seems to trade productivity against difference, and the interesting worlds are the poorer ones.</p><p>Two things to carry forward. The rain cap by height means each seed's mean terrain height sets its income, so terrains should be normalized (or the spread accepted as geography) in later experiments. And the failed prediction about the flat world is worth keeping: the store sits wherever the draw is capped, and shading, the population's own shadow, is enough of a cap to preserve a lake nobody draws on. The population regulates the world's store through where it stands, without a rule saying so.</p>",
    "conclusion": "The breath in the air and the rain on the mountains give the high ground life: 658-670 bodies on ridges that held 0-14, the food eaten falling with height the way the rain does, the world steady to 2% for a million steps with its store in the air, and the soil map turned from a lake into rivers. The bodies sort by height, a little: the winning bar is born a cell or two heavier on the ridges than in the valleys in all four seeds, and second lineages twice held the lower ground for hundreds of thousands of steps, the first place effect on bodies under a uniform sun; but one kind of body still wins everything, so #14's question is only opened, not answered. Half the breath to the air is the best world yet by food and stability (102.9-109.1 eaten, both stores, no waste but shading) and the worst by places (none differ); rain everywhere alike rebuilds the flat lawn. Kept from here: the air and the rain by height as the route for what a body burns (the closed world's second pool), with the note that a place law made of amounts grades bodies where a place law made of kinds might split them. The next law on the height axis should make the high ground differ in kind: what grows there, what it costs to stand there, not only how much falls.",
}

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "lineages":
        top_lineages()
    else:
        main()
