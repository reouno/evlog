#!/usr/bin/env python3
"""Build report.html for e021.

Charts: matplotlib, exported as SVG and inlined. Diagram: hand-written SVG.
Run from the repo root: uv run python experiments/e021_canopy/report.py
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

E020 = os.path.join(HERE, "..", "e020_rain")
# Places of a world: (id in the CSVs, name, color). Under the uniform sun a place is a height band (thirds of the cells by the
# terrain).
BANDS = [(0, "valleys (lowest third)", SERIES[0]), (1, "slopes (middle third)", SERIES[3]), (2, "ridges (highest third)", SERIES[1])]
# Worlds of this experiment: label -> run prefix, world size, places, seeds, whether the sun is uniform (always, here).
WORLDS = {
    "canopy on the mountains": dict(run="128_sigma0_r64_f0.1_high", size=128, places=BANDS, seeds=[1, 2, 3, 4], uniform=True),
    "canopy, half the breath": dict(run="128_sigma0_r64_f0.1_high-b0.5", size=128, places=BANDS, seeds=[1, 2, 3, 4], uniform=True),
    "canopy on the flat lawn": dict(run="128_sigma0_r64_f0.1_flat", size=128, places=BANDS, seeds=[1, 2, 3, 4], uniform=True),
}
UNIFORM = list(WORLDS)
HIGH64, HALF, FLAT = list(WORLDS)
# e020's runs (the same worlds without the canopy; the terrains differ by the mean-height
# normalization, so they are read as ranges): label -> (run prefix, folder, uniform).
REFS = {"e020 mountains (no canopy)": ("128_sigma0_r64_f0.1_high", E020, True), "e020 half breath (no canopy)": ("128_sigma0_r64_f0.1_high-b0.5", E020, True)}
WORLD_COLOR = {HIGH64: SERIES[0], HALF: SERIES[1], FLAT: SERIES[3], "e020 mountains (no canopy)": INK, "e020 half breath (no canopy)": "#c6c4bb"}
KIND_COLOR = {1: SERIES[0], 2: SERIES[1], 3: SERIES[3], 4: SERIES[2]}
CONFIRM_STEPS = 5000
MAIN = HIGH64
VIEWER_WORLD = HIGH64
VIEWER_SEED = 3
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
<svg viewBox="0 0 800 340" role="img" aria-label="A row of world cells in cross-section, each with a green column of standing plant matter. Most columns are a grazed lawn a few hundredths tall. One column stands at height 4: a growing tree. The sun falls on every cell alike, but the cells within the tree's reach lose part of their sun to it, shown as arrows bending from their tops to the tree's crown; the cell beside the tree grows in the dark. A second column stands at the cap of 8: a full crown that intercepts nothing, a standing larder, with a body biting its base." style="max-width:100%;height:auto;display:block">
<g fill="none" stroke="currentColor" stroke-width="1.2" font-size="12" font-family="system-ui, sans-serif">
  <!-- the sun: one arrow per cell -->
  <g stroke="#eda100" stroke-width="1.4">
    <path d="M 65,16 L 65,36 M 115,16 L 115,36 M 165,16 L 165,36 M 215,16 L 215,36 M 265,16 L 265,36 M 365,16 L 365,36 M 415,16 L 415,36 M 465,16 L 465,36 M 515,16 L 515,36 M 565,16 L 565,36" marker-end="url(#sunhead)"/>
    <path d="M 315,16 L 315,36" stroke-width="2.2" marker-end="url(#sunhead)"/>
  </g>
  <text x="300" y="56" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">sun: 0.01 per cell per step, everywhere</text>
  <!-- the light the canopy takes: curved arrows from the shaded cells' tops to the growing tree's crown -->
  <g stroke="var(--s1)" stroke-width="1.5">
    <path d="M 165,64 C 200,70 260,80 296,104" marker-end="url(#lighthead)"/>
    <path d="M 215,62 C 240,68 275,82 300,102" marker-end="url(#lighthead)"/>
    <path d="M 265,60 C 280,68 295,84 306,100" marker-end="url(#lighthead)"/>
    <path d="M 365,60 C 352,70 336,86 326,100" marker-end="url(#lighthead)"/>
    <path d="M 415,62 C 390,70 352,88 332,104" marker-end="url(#lighthead)"/>
  </g>
  <text x="190" y="90" fill="var(--s1)" stroke="none" font-weight="600">the canopy takes the light</text>
  <!-- the ground -->
  <path d="M 40,260 L 590,260" stroke-width="1.5"/>
  <!-- lawn columns (grazed to 0.03-0.05) -->
  <g fill="#1baf7a" stroke="none">
    <rect x="50" y="254" width="30" height="6"/>
    <rect x="100" y="254" width="30" height="6"/>
    <rect x="150" y="255" width="30" height="5"/>
    <rect x="200" y="256" width="30" height="4"/>
    <rect x="400" y="255" width="30" height="5"/>
    <rect x="450" y="254" width="30" height="6"/>
  </g>
  <!-- the cell in the dark beside the tree: nearly bare -->
  <rect x="250" y="258" width="30" height="2" fill="#1baf7a" stroke="none"/>
  <text x="258" y="244" text-anchor="middle" fill="currentColor" stroke="none">in the dark</text>
  <!-- the growing tree: height 4 of 8 -->
  <rect x="300" y="150" width="30" height="110" fill="#1baf7a" stroke="none"/>
  <text x="290" y="280" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">a growing tree</text>
  <text x="290" y="296" text-anchor="middle" fill="currentColor" stroke="none">height 4, room 4: claims</text>
  <text x="290" y="312" text-anchor="middle" fill="currentColor" stroke="none">from every cell it overtops,</text>
  <text x="290" y="328" text-anchor="middle" fill="currentColor" stroke="none">gathers tens of suns</text>
  <!-- the full tree: at the cap, with a body biting it -->
  <rect x="500" y="40" width="30" height="220" fill="#1baf7a" stroke="none"/>
  <rect x="524" y="238" width="26" height="11" rx="1.5" fill="var(--s1)" stroke="none"/>
  <text x="510" y="280" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">a full tree, height 8</text>
  <text x="510" y="296" text-anchor="middle" fill="currentColor" stroke="none">the crown saturated: a larder</text>
  <text x="510" y="312" text-anchor="middle" fill="currentColor" stroke="none">of 400 bites; a bite opens room,</text>
  <text x="510" y="328" text-anchor="middle" fill="currentColor" stroke="none">and the bitten tree pulls hardest</text>
  <!-- labels: the column on the right -->
  <text x="610" y="50" fill="currentColor" stroke="none" font-weight="600">the law, per step</text>
  <text x="610" y="70" fill="currentColor" stroke="none">a column claims, from every cell</text>
  <text x="610" y="86" fill="currentColor" stroke="none">within reach, a share of its sun:</text>
  <text x="610" y="110" fill="var(--s1)" stroke="none">(height difference - distance</text>
  <text x="610" y="126" fill="var(--s1)" stroke="none">walked) / 8  x  2 x room / 8</text>
  <text x="610" y="150" fill="currentColor" stroke="none">slant: the shadow fades by a</text>
  <text x="610" y="166" fill="currentColor" stroke="none">cap-worth per cell, reach at most 8</text>
  <text x="610" y="190" fill="currentColor" stroke="none">saturation: room = 8 - height;</text>
  <text x="610" y="206" fill="currentColor" stroke="none">a full crown claims nothing, so a</text>
  <text x="610" y="222" fill="currentColor" stroke="none">column never takes much more</text>
  <text x="610" y="238" fill="currentColor" stroke="none">than it can grow by</text>
  <text x="610" y="262" fill="currentColor" stroke="none">claims past a cell's whole sun</text>
  <text x="610" y="278" fill="currentColor" stroke="none">share it in proportion; a column</text>
  <text x="610" y="294" fill="currentColor" stroke="none">under a body claims nothing;</text>
  <text x="610" y="310" fill="currentColor" stroke="none">the sun is moved, never made</text>
</g>
<defs>
  <marker id="sunhead" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="#eda100"/></marker>
  <marker id="lighthead" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="var(--s1)"/></marker>
</defs>
</svg>
<figcaption>Figure 1. The canopy law. The matter standing on a cell (its plant, and the dead lying on it) is a column; a taller column takes, from every cell within Chebyshev reach, a share of that cell's sun equal to the height difference less the distance walked, over the cap - times the rate (2) and the column's own room over the cap. The taken light lands in the taker's regrowth budget for the step, where the soil feeds it (a plant still grows out of its own cell's soil). Everything else is e020's world unchanged: the uniform sun, the terrain with soil that runs downhill, the breath to the air and the rain by height, a cell held by a body that neither grows nor gathers. The worlds: the canopy on e020's mountain-rain world, on its half-breath world, and on its flat-rain lawn.</figcaption>
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
                 under=end["under"] / max(end["free"], 1e-9) if end else float("nan"),
                 trees=med(half(log, "trees")), tree_res=med(half(log, "tree_res")), res_max=med(half(log, "res_max")),
                 shade=med(half(log, "shade")), tree_eaten=med(half(log, "tree_eaten")),
                 tree_share=med([t / max(e, 1e-9) for t, e in zip(half(log, "tree_eaten"), eaten[n // 2:])]),
                 biters=med(half(log, "biters_share")))
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
    refhigh, refhalf = list(REFS)

    charts = {}
    charts["eaten"] = world_chart("Food eaten per step", "Plant and dead matter taken by guts per step, one line per run; gray: e020's mountain-rain world (dark) and half-breath world (light), the same laws without the canopy. The sun gives 164 per step; the mean height is normalized, so the rain's caps add up to 82 in every seed. A line that ends is a world that died.", logs_ref, eaten_of, all_worlds, WORLD_COLOR)
    charts["pop"] = world_chart("Population", "Bodies alive at each log step, one line per run; gray: e020 without the canopy.", logs_ref, lambda l: l["pop"], all_worlds, WORLD_COLOR)
    charts["barren"] = world_chart("Sun lost to empty soil", "Share of the sun that shone on a cell whose soil had nothing left, per log window, one line per run; gray: e020 without the canopy (10-29% in the mountain-rain world, all of it in the valleys).", logs_ref, lambda l: [b / max(r + sh + wa + b, 1e-9) for r, sh, wa, b in zip(l["regrowth"], l["shaded"], l["wasted"], l["barren"])], all_worlds, WORLD_COLOR, percent=True)
    charts["soil_cells"] = world_chart("Cells with soil", "Share of the cells holding at least a step of sun's worth of soil (0.01), at each log step, one line per run: the area of the world that can grow a plant this step.", logs, lambda l: l["soil_cells"], list(WORLDS), WORLD_COLOR, percent=True, ymax=1.0)
    charts["air"] = world_chart("Matter in the air", "What bodies have burned and the rain has not yet returned, at each log step, one line per run. The world holds 139,700 in all; a line that climbs and levels is a store forming in the air; one that stays at zero is air that empties every step.", logs, lambda l: l["air"], list(WORLDS), WORLD_COLOR)
    charts["soil_total"] = world_chart("Matter in the soil", "Soil of the whole world at each log step, one line per run; gray: e020 without the canopy (2,200-7,300 in the mountain-rain world, 135,900-136,300 with half the breath). A line that falls is the lake draining into the air.", logs_ref, lambda l: l["soil"], all_worlds, WORLD_COLOR)
    charts["rain"] = world_chart("Rain per step", "Matter fallen from the air on the whole world per step, one line per run. With rain on the mountains the caps add up to 82 per step; a flat line at 82 means the air is never short. With rain everywhere alike the caps add up to 164 and the line is what the bodies burned.", logs, lambda l: l["rain"], list(WORLDS), WORLD_COLOR)
    charts["soil_band"] = place_chart(f"Soil per cell by height, {HIGH64}", "Matter in the soil per cell of each height band (thirds of the cells by the terrain), at each log step, one line per seed. e020 ended near zero everywhere but a remnant pool on the valley floor.", places, HIGH64, lambda d: [so / c for so, c in zip(d["soil"], d["cells"])])
    charts["pop_band"] = place_chart(f"Bodies by height, {HIGH64}", "Bodies standing in each height band at each log step, one line per seed. The bands are equal in cells (5,461 each). e020: 658-670 on the ridges, 268-484 in the valleys.", places, HIGH64, lambda d: d["pop"])
    charts["pop_band_half"] = place_chart(f"Bodies by height, {HALF}", "Bodies standing in each height band at each log step, one line per seed: half of what a body burns rains on the mountains, half falls to the soil under it.", places, HALF, lambda d: d["pop"])
    charts["soil_band_half"] = place_chart(f"Soil per cell by height, {HALF}", "Matter in the soil per cell of each height band, one line per seed: whether a lake survives when half of the breath still falls to the ground.", places, HALF, lambda d: [so / c for so, c in zip(d["soil"], d["cells"])])
    charts["pop_band_flat"] = place_chart(f"Bodies by height, {FLAT}", "Bodies standing in each height band at each log step, one line per seed.", places, FLAT, lambda d: d["pop"])
    charts["eaten_band"] = place_chart(f"Food eaten per step by height, {HIGH64}", "Plant and dead matter eaten per step by the bodies standing in each band, one line per seed. Each band gets 54.6 of sun per step; the rain's caps give the ridges about 37, the slopes 27 and the valleys 18.", places, HIGH64, lambda d: [(a + b) / 10_000 for a, b in zip(d["plant_intake"], d["meat_intake"])])
    charts["rain_band"] = place_chart(f"Rain per step by height, {HIGH64}", "Matter fallen on the cells of each band per step, one line per seed. The cap of a cell is the sun's worth (0.01) times its height over the relief.", places, HIGH64, lambda d: d["rain"])
    charts["top"] = stats_chart("Where the soil lies: the richest tenth of the cells", "Share of the world's soil held by its richest tenth of cells, every 100,000 steps, one line per run. 10% is soil spread evenly.", STATS, lambda d: d["top"], list(WORLDS), percent=True, ymax=1.0)
    charts["under"] = stats_chart("Soil under the bodies over soil elsewhere", "Mean soil of the cells with a body on them over the mean of the cells without, every 100,000 steps, one line per run. Above 1, bodies stand where the soil is; e020's mountain-rain world: 1.2-1.5.", STATS, lambda d: d["under"] / max(d["free"], 1e-9), list(WORLDS), ymin=0)
    charts["maps"] = terrain_soil_figure("The terrain and the soil at the end", "Top: the terrain of seed 1 of each world (white high, black low). Bottom: soil per cell at step 1,000,000 (or the last dump before the world died), darker is more (log scale, 30 and above black).", [(w, seeds_of(w)[0]) for w in WORLDS])
    charts["lineages"] = world_chart("Lineages alive", "Confirmed lineages at each log step, one line per run; gray: e020's worlds without the canopy (1-2).", logs_ref, lambda l: l["lineages"], all_worlds, WORLD_COLOR)
    charts["trees"] = world_chart("Trees standing", "Cells holding at least 1.0 of matter (50 bites; the grazed lawn stands at 0.03-0.05) at each log step, one line per run. e020 had none once the start's stock was eaten.", logs, lambda l: l["trees"], list(WORLDS), WORLD_COLOR)
    charts["tree_share"] = world_chart("Intake from the trees", "Share of the food eaten that was taken from a cell standing at 1.0 or more, per log window, one line per run: the trees as a harvest, not a dead store.", logs, lambda l: [t / max(e, 1e-9) for t, e in zip(l["tree_eaten"], eaten_of(l))], list(WORLDS), WORLD_COLOR, percent=True)
    charts["tree_res"] = world_chart("Matter standing in the trees", "Matter in the cells at 1.0 or more at each log step, one line per run; the world holds 139,700 in all.", logs, lambda l: l["tree_res"], list(WORLDS), WORLD_COLOR)
    charts["shade_moved"] = world_chart("Sun moved by the canopy", "Light taken from shorter columns by taller ones per step, one line per run, of the sun's 164.", logs, lambda l: l["shade"], list(WORLDS), WORLD_COLOR)
    charts["trees_band"] = place_chart(f"Trees by height, {HIGH64}", "Cells at 1.0 or more in each height band at each log step, one line per seed.", places, HIGH64, lambda d: d["trees"])
    charts["contacts"] = world_chart("Contacts per body per step", "Pairs of bodies whose cells touched, per body per step, one line per run; gray: e020 without the canopy (0.009-0.042).", logs_ref, lambda l: [c / max(p, 1) / 10_000 for c, p in zip(l["contacts"], l["pop"])], all_worlds, WORLD_COLOR)

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
               + row("Trees standing (cells at 1.0 or more)", "trees", n0)
               + row("Trees: valleys / slopes / ridges", by_band("trees"), n0)
               + row("Intake from the trees, share of the food eaten", "tree_share", p0)
               + row("Matter standing in the trees", "tree_res", n0)
               + row("Tallest cell", "res_max", d1)
               + row("Sun moved by the canopy, per step", "shade", d1)
               + row("Lineages alive", "lineages", n0, "lineages")
               + row("Mass", "mass", d1, "mass")
               + row("Bodies with a bite, share", "biters", d3, "biters_share")
               + row("Contacts per body per step", "contacts", d3, "contacts")
               + row("Steps per second", "sps", n0, "steps_per_sec")
               + "</tbody>")

    tables = data_table(["step", "place", "pop", "mass", "hard", "muscle", "digestive", "cover", "foot", "plant_intake", "meat_intake", "dead", "carrion", "soil", "rain", "trees", "barren", "regrowth", "cells", "lineages", "movers"],
                        {f"{w}, seed {s}, {place_names(w)[p]} (every 100,000 steps)": places[w][s][p] for w in WORLDS for s in seeds_of(w) for p, _, _ in WORLDS[w]["places"] if p in places[w][s]}, every=10)
    tables += data_table(["step", "pop", "births", "deaths_energy", "mass_mean", "forward", "blocked", "foot_mean", "cover", "contacts", "regrowth", "shaded", "wasted", "barren", "rot", "spent", "flow", "rain", "air", "shade", "trees", "tree_res", "res_max", "tree_eaten", "soil_cells", "deep", "soil", "matter", "plant_intake", "meat_intake", "lineages", "steps_per_sec"],
                         {f"{w}, seed {s}, whole world (every 100,000 steps)": logs[w][s] for w in WORLDS for s in seeds_of(w)}, every=10)

    text = TEXT
    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>e021 The tall plant takes the light - Report</title>
<style>{CSS}</style>
</head>
<body>
<main>
<h1>e021: The tall plant takes the light</h1>
<p class="sub">Experiment report - 2026-09-01 - e020's closed world with one law added: a taller plant shades a shorter one, as far as it is tall, and takes only the light it can use. The canopy on the mountain-rain world, on the half-breath world and on the flat-rain lawn, 128x128, four seeds each, 1,000,000 steps; e020's runs without the canopy as the reference</p>

<section class="tldr">
<h2>TL;DR</h2>
<p>{text["tldr"]}</p>
</section>

<h2>1. Question</h2>
<p>{text["question"]}</p>
<ol>
  <li><strong>Trees stand.</strong> Cells holding at least 1.0 of matter (50 bites; the grazed lawn stands at 0.03-0.05) persist through the second half of every run - tens to hundreds per world (e020: none once the start's stock was eaten) - and some reach the cap. They stand where soil meets few bodies: in the mountain-rain world on the valley floors and rivers, where 10-29% of e020's sun fell on empty ground.</li>
  <li><strong>The trees are eaten.</strong> Intake from tree cells is at least 5% of the world's intake in the mountain-rain world: the trees are a harvest, not a dead store, and the world eats within 15% of e020's income.</li>
  <li><strong>A crowd forms at the trees.</strong> Contacts per body per step rise above e020's 0.009-0.042 in every run: bodies waiting at a tree the way e011's crowds shared a rich cell.</li>
  <li><strong>A second kind of body lives on the trees.</strong> By #19: in at least two seeds of four, a lineage whose intake is mostly from tree cells coexists with the lawn bar for over 100,000 steps, with a different body (larger, or toothed - a biters' share over 0.01 would be the first tooth since e012). This is the hypothesis the law is for; it has failed in every world since e013.</li>
  <li><strong>The world stands.</strong> No extinction, population coefficient of variation under 0.10 over the second half, matter conserved to 0.05%, in all twelve runs. The canopy moves sun, it does not destroy it; trees can starve the lawn locally but the trees themselves are food.</li>
  <li><strong>The rate is not a dial.</strong> Doubling the shade rate (pilot only) changes how sharp the canopy is, not what kind of world forms.</li>
</ol>

<h2>2. The world</h2>
<p>{text["world"]}</p>
{DIAGRAM}
<p>{text["runs"]}</p>
<ul class="measures">
  <li><strong>Trees</strong> (<code>trees</code>): cells holding at least 1.0 of standing matter (50 bites), also per height band in <code>places.csv</code>. <strong>Their stock</strong> (<code>tree_res</code>): the matter standing in them; <code>res_max</code> is the tallest cell.</li>
  <li><strong>The harvest</strong> (<code>tree_eaten</code>): intake taken from cells standing at 1.0 or more at the bite. <strong>The canopy</strong> (<code>shade</code>): sun moved from shorter columns to taller ones per step. The shade rate is in <code>terrain.json</code>.</li>
  <li><strong>Places by height</strong>: the place of a cell is its band (the lowest third of the cells by the terrain, the middle third, the highest third), so the per-place log (population, body means, intake, soil, rain, barren sun, lineages, movers) reads by height. Each agent and lineage also carries the terrain height under it.</li>
  <li><strong>The soil map</strong> (<code>soil.jsonl</code>, every 100,000 steps): the share of the soil in the richest tenth of the cells, the soil per cell and its share per place, the share of the bodies standing in each place, the shares of bare and wet cells, and the soil under the bodies over the soil elsewhere.</li>
  <li>e020's measures: the air and the rain; sun split into grown, shaded, wasted and barren; soil, spent, rot, flow, matter; population, food eaten, dead matter, contacts, moves, lineages and events; places by height band; snapshots with the terrain and the soil as layers.</li>
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
{charts["trees"]}{charts["trees_band"]}
</div>
<div class="wide">{charts["maps"]}</div>
<p>{text["r1"]}</p>

<h3>3.2 {text["h2"]}</h3>
<div class="grid2">
{charts["tree_share"]}{charts["tree_res"]}
</div>
<div class="grid2">
{charts["shade_moved"]}{charts["barren"]}
</div>
<p>{text["r2"]}</p>

<h3>3.3 {text["h3"]}</h3>
<div class="grid2">
{charts["contacts"]}{charts["under"]}
</div>
<p>{text["r3"]}</p>

<h3>3.4 {text["h4"]}</h3>
<div class="grid2">
{charts["lineages"]}{charts["pop_band"]}
</div>
{gallery(GALLERY)}
<p>{text["r4"]}</p>

<h3>3.5 {text["h5"]}</h3>
<div class="grid2">
{charts["eaten"]}{charts["pop"]}
</div>
<div class="grid2">
{charts["air"]}{charts["soil_total"]}
</div>
<p>{text["r5"]}</p>

<h3>3.6 {text["h6"]}</h3>
<p>{text["r6"]}</p>


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
<p>Every 100,000th record; full logs in <code>results/*_log.csv</code>, per place in <code>results/*_places.csv</code>, lineages in <code>results/*_lineages.csv</code>, events in <code>results/*_events.csv</code>, agents every 100,000 steps in <code>results/*_agents.csv</code>, the terrain (with the rain mode) in <code>results/*_terrain.json</code>, the soil and plants of every cell every 100,000 steps in <code>results/*_soil.jsonl</code>, snapshots in <code>results/*_{{long,clip,bodies}}.jsonl</code>. Reference runs are read from <code>../e020_rain/results</code>. Build this report with <code>uv run python experiments/e021_canopy/report.py</code>.</p>
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
    ("canopy on the mountains", 3, 1, "the bar of the forest world", "Eight digestive cells 2 by 8, the main lineage of the one mountain seed that lives in the forest state, alive all 1,000,000 steps (1,663 agents at its peak): the same mower as e019's lawn and e020's ridges, now grazing between 200-1,400 standing trees."),
    ("canopy on the mountains", 3, 81, "the heavy bar above the trees", "Ten digestive cells, the heaviest winner of the series (mass 10.3), living 395,000 steps beside lineage 1 and standing highest (mean height 39.5, where the forest is thickest, 125 trees on the ridges): where cells hold 50-400 bites, a bigger gut pays."),
    ("canopy on the mountains", 1, 90, "the thin bar of the low ground", "Six digestive cells in a single row, a cell lighter than the main line, 415,000 steps at height 26 against the main line's 36: e020's height sorting unchanged - the thin rain of the valleys still keeps the small variant."),
    ("canopy on the flat lawn", 3, 35, "the second bar of the lawn forest", "Nine digestive cells 1.4 rows deep, living 921,000 steps beside the main lineage (mass 9.1 against 7.6) in the flat world that holds 217-458 trees on its lake - the longest coexistence of two lineages since e012."),
    ("canopy, half the breath", 4, 23, "the long bar", "Nine to ten digestive cells, 2.2 rows by 7.7 columns, the main lineage of half seed 4 for 997,000 steps (1,882 agents): the richest world still grows the biggest bars, and this seed keeps five lineages alive at once at its peak."),
    ("canopy, half the breath", 4, 261, "the squat bar", "Seven to eight digestive cells folded 3 rows deep by 4.3 wide, living 396,000 steps in the same world and seed as the long bar: two shapes of the same organ sharing one world, which the count of lineages alone would hide."),
]


TEXT = {
    "question": "Since e013 one kind of body, a bar of 6-10 gut cells, has won every run, and lineages alive have stayed at 1-2. The last world with several winners at once was e011, and its premise was a cell that holds more than one bite: crowds around rich cells made size, armor and teeth worth their cost. A closed world has had no way to such a cell, because no cell grows faster than the sun (0.01 per step, half a bite): every place is a thin lawn and the best body is the smallest bar that reaches wet ground. The real world's way from thin sunlight to a concentrated meal is the tree: a plant that is not eaten grows tall and takes the light of its neighbors. e021 writes that as a law of the world - the matter standing on a cell is a column, and a taller column takes a shorter one's light, as far as it is tall, but only as much as it can use - and asks whether the world grows trees, whether the trees gather crowds, and whether a crowd is finally worth biting into. Alongside it one piece of geography: each seed's terrain is normalized to a mean height of half the relief, so that every seed's rain adds up to the same income (in e020 the seeds spread 73-94 with their terrains). The hypotheses, written before the runs:",
    "world": "Everything is e020's closed world (128x128 on a torus, matter 8 per cell at the start as plants, bodies of 8x8 cells in five kinds grown from the genome, space at the resolution of the body, a facing, e010's contact rule, a cell that costs what it holds, 0.032 per body per step, work = force x distance, a cell held by a body does not regrow, a dead body is food where it lies, a plant grows out of its own cell's soil at most its light, the dead rot into the soil, a terrain of relief 64 with its mean height normalized to 32, soil that runs downhill and levels, a uniform sun, the breath to the air and the rain by height) with the canopy added (Figure 1): before anything grows, every column of standing matter takes a share of the sun of the cells it overtops, and the taken light lands in its own regrowth budget. One new argument, the shade rate (2 by default; 0 is e020). The place of a cell is its height band, thirds of the cells by the terrain: valleys, slopes, ridges. A cell is called a tree here when it holds at least 1.0 of matter, 50 bites, about 25 times what the grazed lawn stands at.",
    "runs": "<strong>Runs.</strong> The canopy at rate 2 on e020's three worlds - rain on the mountains with all of the breath to the air, with half of it, and rain on every cell alike - at relief 64 and flow 0.1, twelve runs at once on one machine, one thread each, 1,000,000 steps, seeds 1-4. Reference: e020's twelve runs of the same worlds without the canopy, read as ranges (the normalization rescales each seed's heights, so seeds do not match one to one). Three pilots (seed 9, 100,000 steps) shaped the law itself: a shadow stopped at the four neighbors gathers at most five suns, less than one body's upkeep, and stays marginal (7-27 trees, 0.2-0.5% of the intake); the full slant without saturation starves every world dead in 700-3,200 steps, because a column at the cap throws away the light it hoards; with saturation the world stands, and the rate has a threshold - trees lose the race against grazing at 1 and win it at 2. We record e020's measures and:",
    "tldr": "The canopy works, and the world it makes has two states. Every run keeps standing trees - cells of 50 to 400 bites in a world whose lawn stands at a fiftieth of one - but most runs hold a sparse orchard of 6-24 of them (0.2-0.8% of the intake), while three runs live in a forest: 165-1,405 tree cells, 6.5% of the intake harvested from them, contacts twice e020's ceiling, and booms the grazers mow back down. The forest arrived after step 700,000 twice, so the orchard runs read as not-yet rather than never. The canopy also pays: the flat worlds eat 105-113 per step against e020's 100-103, because a tree overtopping a grazed or held cell takes light that the bodies' own shadow was wasting, and the forest seed eats 112.9, the most of any closed world so far. Nothing grew a tooth (biters 0.000 everywhere) and every winner is still a gut bar - but lineages alive reach 3-5 in four runs, flat seed 3 holds two lineages for 921,000 steps (the longest coexistence since e012), and the heaviest winner of the series (mass 10.3) stands exactly where the forest is. Next: the spill - a full crown that drops what it catches as fruit - so that a tree feeds a crowd instead of being silenced by the body that eats it.",
    "c1": "yes", "l1": "Yes, in two states", "v1": "Every run keeps cells at 1.0 or more through the whole run and the tallest reaches the cap in 8 of 12; but the count is bimodal, an orchard of 6-24 in most runs against a forest in three: high seed 3 holds 165-1,405 over the run (a boom of 1,405 at step 400,000 grazed to 165 by 600,000, then 200-250), flat seed 3 holds 217-458, half seed 3 flips at step 800,000 from 4-10 to 300-477, and high seed 2 touches 172 and falls back. Where: not the valleys as guessed - in the mountain worlds the trees stand where the rain is (high seed 3 at the end: 37 valleys / 94 slopes / 125 ridges), on the flat lawn they stand on the lake (44 / 39 / 2).",
    "c2": "no", "l2": "Only in the forest", "v2": "Intake from tree cells is 5.47-7.40 per step, 6.5% of the food eaten, in the two full-run forests, and 0.2-0.8% in the orchard runs - the 5% asked arrives only with the forest state. The unasked result is the income: the flat worlds eat 105.4-112.9 against e020's 100.4-103.3, because the canopy takes light that the standing bodies' shadow was destroying (shaded sun falls from 36-38% to 29-35%), and the high worlds eat 83.2-83.8 - the seed spread of e020 (72.8-94.3) collapsed by the normalization, the level held by the canopy.",
    "c3": "no", "l3": "Only in the forest", "v3": "Contacts per body per step span 0.008-0.093: the orchard runs sit inside e020's 0.009-0.042, and only the forests rise above it - high seed 3 at 0.093 (twice e020's ceiling and its own orchard neighbors' 0.019-0.047), flat seed 3 at 0.042, half seed 3 at 0.027 after its flip. A crowd needs the forest, and the forest is episodic.",
    "c4": "no", "l4": "No - but the deepest coexistence since e012", "v4": "No tooth in any run (biters 0.000, hard 0.0-0.2), no lineage provably fed mostly on trees, and every winner is a gut bar; mass still rises with height in all four high seeds. But lineages alive reach 3 (median) in high seeds 1 and 3 and 5 in half seed 4 (e020: 1-2), and the coexistences are long: flat seed 3 holds two lineages for 921,000 steps at different masses (9.1 against 7.6), high seed 3 holds three with the heaviest winner of the series (lineage 81, mass 10.3, 395,000 steps) standing where the forest is, and half seed 4 turns over four lineages of two different bar shapes (2.2 x 7.7 and 3.0 x 4.3).",
    "c5": "yes", "l5": "Yes", "v5": "No extinction in twelve runs; population coefficient of variation 0.007-0.028, food eaten last quarter over third quarter 0.990-1.011. Matter holds to 0.01% in the orchard runs and 0.04-0.08% in the forests (the plants are f32, and rounding grows with the standing heights; the soil and the air are f64). The two failed pilot forms mark the boundaries: reach without saturation starves every world in 700-3,200 steps, saturation without reach is marginal.",
    "c6": "no", "l6": "No: a threshold", "v6": "Answered by the pilot before the runs: at rate 1 the trees lose the race against the grazing (8-12 standing, 0.3% of the intake, no larder full), at rate 2 they win it (204 standing, 6.4%). Saturation halves the slant's strength and the rate restores it; the committed default is 2. The runs did not vary the rate further.",
    "h1": "Trees stand, and the world has two states",
    "r1": "The trees chart (left) is really a chart of states: nine runs wander between 5 and 30 trees, and three sit far above, with high seed 3's boom to 1,405 - a twelfth of the world under trees - grazed back to 200 within 200,000 steps. The flips are sudden: half seed 3 spends 800,000 steps as an orchard and 100,000 as a forest, and stays one. By height (right), the mountain forests stand on the rain: ridges and slopes hold five of every six trees, while e020's picture put all the matter in the valleys. The maps (below) show why the guess missed: the valley floors are where the bodies are not, but also where the rain is not, and a tree grows only as fast as its cell's soil feeds it; the ridge, wet with rain and grazed thin, is where an ungrazed cell can outgrow its neighbors fastest.",
    "h2": "The trees are a harvest in the forest, and the canopy raises the world's income",
    "r2": "In the forest runs 6.5% of everything eaten comes out of tree cells (left), against 0.2-0.8% in the orchards: the trees are grazed like everything else, in gulps of up to 400 bites. The stock chart (right) shows the standing wealth - 1,500 of matter in high seed 3's trees, against 14-100 in the orchards. The surprise is in the barren chart: the canopy does not cost the world income, it adds some. A column overtopping a held cell claims sun that the body standing there would have blanked, so the flat worlds eat 3-10% more than e020's and the bodies' shadow falls by 3-6 points of the sun. The moved light itself is small - 5-8 per step of 164 in the orchards, 17-18 in the forests.",
    "h3": "A crowd forms only in the forest",
    "r3": "Contacts (left) separate the two states more cleanly than the tree count: the orchard runs lie in e020's band, and the forests stand above it, high seed 3 doubled. But 0.093 of a contact per body per step is still a tenth of e011's crowds, and none of it is a bite: the crowd waits at the trees, eats, and disperses. The soil-under-bodies chart (right) shows the mountain worlds' bodies still standing under the rain rather than on a store (1.2-1.5).",
    "h4": "One kind of body still - sorted by height, now also by state",
    "r4": "Lineages alive (left) reach 3 in the forest seed and 5 in half seed 4, against e020's 1-2, and the long coexistences are all where trees are: the 921,000-step pair of the flat forest, the mass-10.3 third lineage of the mountain forest standing at height 39.5. The bodies by height (right) keep e020's grading in every seed. The gallery below shows what coexists: bars of 6 to 10 gut cells, thin and long or folded squat, sorted by the thickness of the rain and the richness of the state - kin of one winner, not other kinds. Nothing needs a tooth to eat a tree, and nothing grew one.",
    "h5": "The world stands, in both states",
    "r5": "Twelve runs, no extinction, the food eaten flat to 1% between quarters (left), the population's coefficient of variation at most 0.028 even through the forest booms (right). The closed cycle absorbs the new law the way it absorbed the rain: the stores shift (a forest holds up to 1,500 standing; the air and the lake hold the rest), the flows rebalance, and the world goes on. The forest booms are the only new dynamics visible at the world scale - and they are the first world-scale dynamics under a uniform sun that are not damped noise.",
    "h6": "The rate is a threshold (from the pilot)",
    "r6": "At rate 1 the canopy exists and does nothing that matters: trees hover under a dozen, harvest under half a percent. At rate 2 the same law makes forests. The threshold is where a tree's gathered light outruns the grazing pressure on it; the runs were made at 2 and the rate was not varied further. Unlike e019's flow rate (which did not matter across two orders of magnitude), the canopy has a scale the world can feel - which is worth remembering when a law seems inert: its strength may sit just under a threshold.",
    "viewer": "The mountain forest, seed 3. The food layer shows the trees as bright green points standing in the thin lawn of the ridges - watch them thicken into groves and get mown back; the terrain layer shows the crowd living on the high ground; the soil layer shows the rivers running from under it. From step 237,000 the world is lineage 1 with lineage 80 beside it from 570,000 and lineage 81 - the heavy bar - above both from 750,000: three bars of one family, sharing a forest.",
    "discussion": "<p>The law does what it was written for, but in a state the world only sometimes occupies. A tree is a runaway - it must gather light faster than bodies eat it, and whether any cell ever gets the head start is a matter of local accident: three seeds of twelve found it, twice after step 700,000. Once found, the forest is stable in the aggregate (flat seed 3 holds 200-450 trees for 900,000 steps) while every individual tree booms and is mown. The world under a uniform sun now has weather of its own making. That is one answer to #19's question in miniature: more winners need more states, and the canopy gives the world a second one.</p><p>The income result was not asked for and matters most. In every closed world since e016, the population's own shadow has been the binding waste - bodies stand on a third of the sun. The canopy is the first law that recovers any of it, because a tree is taller than the body next to it and takes the light that the held cell would blank. The flat forest eats 112.9 per step, the record for a closed world, with a third of its matter standing in trees; richness and structure arrived together, where e020 found them traded (its richest world had no places).</p><p>What the canopy did not do is convert the crowd into an arms race. Contacts double in the forest but stay at a tenth of e011's, and the reason is in the law: a body eating a tree stands on it, and a held cell neither grows nor claims. A tree is therefore silent exactly while it is being eaten - it feeds one body at a time, in gulps, and the crowd disperses between gulps. e011's rich cells fed 45-77 bodies standing on one cell at once; nothing in this world feeds more than the body that got there first. The missing piece is not a bigger store but a store that feeds its surroundings while it stands.</p><p>Which is what the spill is (vision, next step 2, written before this experiment): a full crown that keeps catching the light it stands in and drops what it cannot hold onto the cells around it. Pilot 2 showed exactly that flow - full columns hoarding the whole neighborhood's sun - as a famine, because the hoard was destroyed; sent to the forest floor as fruit instead, it is a rich place with a radius, fed by the canopy, eaten by a crowd that never touches the tree. The two failed pilots turn out to be the map: between the blight (take and destroy) and the orchard (take only for yourself) sits the tree that gives it back.</p>",
    "conclusion": "The canopy - a taller column takes a shorter one's light, as far as it is tall, as much as it can use - is kept as a law of the world at rate 2. It gives the closed world standing stores of 50-400 bites where no cell could hold more than half of one, a second state (the forest, episodic, self-made), an income above the lawn's (112.9 per step, the closed-world record, with the bodies' shadow partly recovered), and the deepest coexistence in nine experiments: 3-5 lineages in four runs, two lineages for 921,000 steps, the heaviest winner of the series standing in the thickest forest. It did not bring back teeth: a tree is silenced by the body that eats it, so the forest feeds one gut at a time. Next, the spill: a full crown that drops what it catches as fruit on its neighbors, so a tree feeds a crowd - e011's rich cell, rebuilt inside a closed world by two laws about light and one about falling.",

}

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "lineages":
        top_lineages()
    else:
        main()
