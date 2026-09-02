#!/usr/bin/env python3
"""Build report.html for e023.

Charts: matplotlib, exported as SVG and inlined. Diagram: hand-written SVG.
Run from the repo root: uv run python experiments/e023_eyes/report.py
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

E022 = os.path.join(HERE, "..", "e022_spill")
# Places of a world: (id in the CSVs, name, color). Under the uniform sun a place is a height band (thirds of the cells by the
# terrain); the flat world is rained on alike, the bands are kept for the loaders.
BANDS = [(0, "valleys (lowest third)", SERIES[0]), (1, "slopes (middle third)", SERIES[3]), (2, "ridges (highest third)", SERIES[1])]
# Worlds of this experiment: label -> run prefix, world size, places, seeds.
WORLDS = {
    "eyes that see far": dict(run="128_sigma0_r64_f0.1_flat_eyes8", size=128, places=BANDS, seeds=[1, 2, 3, 4], uniform=True),
}
EYES = list(WORLDS)[0]
# The control: e022's flat runs, the same code at eyes 0 (two cells, the second weighted by sensors / 8).
REFS = {"e022: two cells": ("128_sigma0_r64_f0.1_flat", E022, True)}
E022_FLAT = list(REFS)[0]
WORLD_COLOR = {EYES: SERIES[0], E022_FLAT: "#b5b3ab"}
KIND_COLOR = {1: SERIES[0], 2: SERIES[1], 3: SERIES[3], 4: SERIES[2]}
CONFIRM_STEPS = 5000
VIEWER_WORLD = EYES
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
<svg viewBox="0 0 800 300" role="img" aria-label="A body seen from above on a row of world cells, facing right. In front of it the cells one to nine away are drawn as boxes whose fill fades with the distance: the first full, the second at a half, the third at a third, out to a ninth. A bracket over the first two cells marks what every body saw before; a bracket over all nine marks what a body with eight sensor blocks sees now. A pile of fruit lies on the seventh cell, seen at one seventh." style="max-width:100%;height:auto;display:block">
<g fill="none" stroke="currentColor" stroke-width="1.2" font-size="12" font-family="system-ui, sans-serif">
  <!-- the body: an 8x8 grid on two world cells, three sensor blocks on its front edge -->
  <rect x="40" y="120" width="88" height="60" rx="2" fill="currentColor" fill-opacity="0.12"/>
  <g fill="#eda100" stroke="none">
    <rect x="118" y="126" width="8" height="8"/><rect x="118" y="146" width="8" height="8"/><rect x="118" y="166" width="8" height="8"/>
  </g>
  <g fill="#1baf7a" stroke="none">
    <rect x="48" y="128" width="60" height="44" rx="1"/>
  </g>
  <text x="84" y="200" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">a body, facing right</text>
  <text x="84" y="216" text-anchor="middle" fill="currentColor" stroke="none">3 sensor blocks (yellow)</text>
  <text x="84" y="232" text-anchor="middle" fill="currentColor" stroke="none">on a gut of 15</text>
  <!-- the cells ahead: 9 boxes, fill fading with distance 1/j -->
  <g stroke="currentColor" stroke-width="1">
    <rect x="140" y="120" width="60" height="60" fill="var(--s1)" fill-opacity="1.00"/>
    <rect x="204" y="120" width="60" height="60" fill="var(--s1)" fill-opacity="0.50"/>
    <rect x="268" y="120" width="60" height="60" fill="var(--s1)" fill-opacity="0.33"/>
    <rect x="332" y="120" width="60" height="60" fill="var(--s1)" fill-opacity="0.25"/>
    <rect x="396" y="120" width="60" height="60" fill="var(--s1)" fill-opacity="0.20"/>
    <rect x="460" y="120" width="60" height="60" fill="var(--s1)" fill-opacity="0.17"/>
    <rect x="524" y="120" width="60" height="60" fill="var(--s1)" fill-opacity="0.14"/>
    <rect x="588" y="120" width="60" height="60" fill="var(--s1)" fill-opacity="0.12"/>
    <rect x="652" y="120" width="60" height="60" fill="var(--s1)" fill-opacity="0.11"/>
  </g>
  <g fill="currentColor" stroke="none" text-anchor="middle">
    <text x="170" y="200">1</text><text x="234" y="200">1/2</text><text x="298" y="200">1/3</text><text x="362" y="200">1/4</text><text x="426" y="200">1/5</text><text x="490" y="200">1/6</text><text x="554" y="200">1/7</text><text x="618" y="200">1/8</text><text x="682" y="200">1/9</text>
  </g>
  <text x="426" y="220" text-anchor="middle" fill="currentColor" stroke="none">what lies j cells away is seen at 1/j: the light reaching the eye falls with the distance</text>
  <!-- a pile of fruit on the seventh cell -->
  <g fill="#1baf7a" stroke="none">
    <circle cx="546" cy="150" r="3"/><circle cx="554" cy="144" r="3"/><circle cx="562" cy="152" r="3"/><circle cx="551" cy="158" r="3"/><circle cx="559" cy="161" r="3"/>
  </g>
  <text x="554" y="108" text-anchor="middle" fill="currentColor" stroke="none">a pile of fruit, 7 away: seen at 1/7</text>
  <!-- brackets: e022's two cells, this body's four, the cap of nine -->
  <g stroke="currentColor" stroke-width="1.2">
    <path d="M 140,66 L 140,58 L 264,58 L 264,66"/>
    <path d="M 140,40 L 140,32 L 392,32 L 392,40"/>
  </g>
  <g stroke="var(--s1)" stroke-width="1.6">
    <path d="M 140,252 L 140,260 L 712,260 L 712,252"/>
  </g>
  <text x="202" y="76" text-anchor="middle" fill="currentColor" stroke="none">e022: every body saw 2 cells (the second at sensors / 8)</text>
  <text x="266" y="50" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">this body sees 1 + 3 = 4 cells</text>
  <text x="426" y="280" text-anchor="middle" fill="var(--s1)" stroke="none" font-weight="600">range = 1 + sensor blocks, up to 9: a body of 8 sensors sees 9 cells, in each of the 4 directions</text>
</g>
</svg>
<figcaption>Figure 1. The eye. A sensor block is a material that sees a distance: a body sees the row of cells one cell ahead (and behind, left, right), as wide as itself, and one more row per sensor block, up to eight more. The four inputs per direction (food and crowd) sum what lies in each row, a row j cells away at 1/j, so a pile far off is seen dimly and a pile near is seen bright, and the same linear policy that walked into piles can walk toward them. A body with no sensor sees one cell; in e022 every body saw two, the second at sensors / 8. A sensor still costs its upkeep per block and its cell, nothing more: range is paid for with the cell that could have been gut. The knockout (e009) recomputes every decision of a body with sensors as if it had none, and counts the decisions that differ (<code>sense_used</code>). Everything else is e022: the closed world, the canopy, the spill, the crowd on the rings, mutation per base.</figcaption>
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
<figcaption><strong>{html.escape(name)}</strong><br>{html.escape(world)}, seed {seed}, lineage {lid}: {span:,} steps, {int(peak["size"]):,} agents at {"step " + format(int(peak["step"]), ",") if at else "its peak"}, {home}{height}<br>mass {float(peak["mass"]):.0f} on {float(peak["foot"]):.1f} cells: hard {float(peak["hard"]):.0f}, muscle {float(peak["muscle"]):.0f}, sensor {float(peak["sensor"]):.1f}, digestive {float(peak["digestive"]):.0f}; dead matter {meat:.0%} of the intake<br>{html.escape(what)}</figcaption></figure>""")
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



def load_survey():
    """The start survey (results/start_survey.csv): 24 runs of 10,000 steps with the eye, by world and seed."""
    rows = load_rows("results/start_survey.csv")
    return rows


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
        logs[w] = {s: load_csv(f"results/{run}_seed{s}_log.csv", folder) for s in seeds_of(w)}
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
        d = dict(pop=med(pop), pop_cv=statistics.pstdev(pop) / max(statistics.mean(pop), 1), pop_swing=max(pop) / max(min(pop), 1),
                 extinct=last_step < LAST_STEP, extinct_at=last_step if last_step < LAST_STEP else float("nan"), sps=med(log["steps_per_sec"]),
                 lineages=med([per_step.get(t, 0) for t in range(1000, last_step + 1, 1000)]), ids=len(first),
                 contacts=med([c / max(p, 1) / 10_000 for c, p in zip(half(log, "contacts"), pop)]), forward=med(half(log, "forward")),
                 mass=med(half(log, "mass_mean")), hard=med(half(log, "hard_mean")), muscle=med(half(log, "muscle_mean")), foot=med(half(log, "foot_mean")),
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

    charts = {}
    charts["sensor_share"] = world_chart("Bodies with a sensor", "Share of the bodies alive that carry at least one sensor block, at each log step, one line per run; gray: e022's flat runs (the same code, every body seeing two cells). A line that stays up is an eye that pays.", logs, lambda l: l["sensor_agents_share"], all_worlds, WORLD_COLOR, percent=True)
    charts["sensor_mean"] = world_chart("Sensor blocks per body", "Mean sensor blocks per body alive, one line per run; gray: e022. With the eye a body's range is one cell plus this.", logs, lambda l: l["sensor_mean"], all_worlds, WORLD_COLOR)
    charts["sense_used"] = world_chart("The knockout: decisions the eye changed", "Of the decisions taken by bodies with a sensor, the share that would differ if the body saw one cell, per log window, one line per run; gray: e022 (there: if the second cell were not seen). Zero would be an eye nobody reads.", logs, lambda l: l["sense_used"], all_worlds, WORLD_COLOR, percent=True)
    charts["pop"] = world_chart("Population", "Bodies alive at each log step, one line per run; gray: e022. A line that ends is a world that died.", logs, lambda l: l["pop"], all_worlds, WORLD_COLOR)
    charts["eaten"] = world_chart("Food eaten per step", "Plant, fruit and dead matter taken by guts per step, one line per run; gray: e022. The sun gives 164 per step.", logs, eaten_of, all_worlds, WORLD_COLOR)
    charts["fruit_share"] = world_chart("Intake from fruit", "Share of the food eaten that was fruit lying on the rings, per log window, one line per run; gray: e022 (44-77% in its crowd state).", logs, lambda l: [f / max(e, 1e-9) for f, e in zip(l["fruit_eaten"], eaten_of(l))], all_worlds, WORLD_COLOR, percent=True, ymax=1.0)
    charts["contacts"] = world_chart("Contacts per body per step", "Pairs of bodies whose cells touched, per body per step, one line per run; gray: e022 (0.22-0.76 in the crowd state).", logs, lambda l: [c / max(p, 1) / 10_000 for c, p in zip(l["contacts"], l["pop"])], all_worlds, WORLD_COLOR)
    charts["biters"] = world_chart("Bodies with a bite", "Share of the bodies with a hard tip on the front backed by muscle, at each log step, one line per run; gray: e022 (peaks of 0.01-0.03, never kept).", logs, lambda l: l["biters_share"], all_worlds, WORLD_COLOR, percent=True)
    charts["lineages"] = world_chart("Lineages alive", "Confirmed lineages at each log step, one line per run; gray: e022 (1-3).", logs, lambda l: l["lineages"], all_worlds, WORLD_COLOR)
    charts["mass"] = world_chart("Mass per body", "Mean cells per body alive, one line per run; gray: e022 (the frame of 19-24 cells in the crowd state).", logs, lambda l: l["mass_mean"], all_worlds, WORLD_COLOR)

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
               + row("Bodies with a sensor, share (median / peak)", "sensor_share|sensor_share_max", p1)
               + row("Sensor blocks per body (median / peak)", "sensor_mean|sensor_mean_max", d2)
               + row("Decisions the eye changed, share of the sensed decisions", "sense_used", p0)
               + row("Sensed decisions per body per step", "sense_decisions", d3)
               + row("Longest lineage with a sensor per body: steps / peak agents", "eyed_steps|eyed_peak", n0)
               + row("Lineages with a sensor per body for 100,000 steps or more", "eyed_100k", n0)
               + row("Population", "pop", n0)
               + row("Population, coefficient of variation", "pop_cv", d2)
               + row("Food eaten per step", "eaten", d1)
               + row("Intake from fruit, share of the food eaten", "fruit_share", p0)
               + row("Dead matter, share of the food eaten", "meat_share", p0)
               + row("Contacts per body per step", "contacts", d2)
               + row("Bodies with a bite, share (median / peak)", "biters|biters_max", d3)
               + row("Lineages alive", "lineages", n0)
               + row("Mass", "mass", d1)
               + row("Matter at the end over the start", "matter_hold", lambda v: f"{v:.4f}")
               + row("Steps per second", "sps", n0)
               + "</tbody>")

    survey = load_survey()
    srows = "".join(f"<tr><td>{r['world']}</td><td>{r['seed']}</td><td>{int(r['peak']):,}</td><td>{int(r['bottleneck']):,}</td><td>{int(r['pop_10k']):,}</td><td>{('step ' + format(int(r['died_at']), ',')) if r['died_at'] else '-'}</td></tr>" for r in survey)
    deaths = sum(1 for r in survey if r["died_at"])
    survivors = [int(r["bottleneck"]) for r in survey if not r["died_at"]]
    survey_table = (f"<div class='tw'><table><thead><tr><th>world</th><th>seed</th><th>peak</th><th>bottleneck</th><th>bodies at 10,000</th><th>died</th></tr></thead><tbody>{srows}</tbody></table></div>"
                    f"<p>{deaths} deaths in {len(survey)} starts, bottlenecks of {min(survivors):,}-{max(survivors):,} bodies in the survivors; e022 (the same seeds and worlds, two cells): 5 deaths in 24 (high 4 and 8, half 6 and 7, flat 8), bottlenecks 7-431.</p>")

    tables = data_table(["step", "pop", "births", "deaths_energy", "mass_mean", "sensor_mean", "sensor_agents_share", "sense_decisions", "sense_used", "forward", "contacts", "regrowth", "fruit", "fruit_eaten", "plant_intake", "meat_intake", "trees", "lineages", "biters_share", "steps_per_sec"],
                        {f"{w}, seed {s} (every 100,000 steps)": logs[w][s] for w in all_worlds for s in seeds_of(w)}, every=10)

    text = TEXT
    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>e023 Eyes that see far - Report</title>
<style>{CSS}</style>
</head>
<body>
<main>
<h1>e023: Eyes that see far</h1>
<p class="sub">Experiment report - 2026-09-02 - e022's closed world with one law changed: a sensor block sees one more cell, what lies j cells away seen at 1/j. The flat world, 1,000,000 steps, seeds 1-4, against e022's same four runs.</p>

<section class="tldr">
<h2>TL;DR</h2>
<p>{text["tldr"]}</p>
</section>

<h2>1. Question</h2>
<p>{text["question"]}</p>
<ol>
  <li><strong>Eyes pay now.</strong> The sensor share of the population rises above e022's (1-7% on median in its flat runs) and sensor lineages last: a lineage with a sensor per body lives 100,000 steps in at least two seeds of four.</li>
  <li><strong>The knockout says the eye is used.</strong> The share of the sensed decisions the eye changes exceeds e022's 11-14% where sensor lineages last.</li>
  <li><strong>The start survives.</strong> In the survey of the start (seeds 1-8 of the three worlds, 10,000 steps) fewer than e022's 5 of 24 die and the bottlenecks are shallower than 7-431.</li>
  <li><strong>The world stands and keeps its crowd.</strong> Population coefficient of variation under 0.10, matter conserved, fruit over a third of the intake, contacts at or above e022's 0.22-0.76.</li>
  <li><strong>The tooth stays unpaid.</strong> No biter lineage lasts: an eye alone does not make a hunter.</li>
</ol>

<h2>2. The world</h2>
<p>{text["world"]}</p>
{DIAGRAM}
<p>{text["runs"]}</p>
<ul class="measures">
  <li><strong>The eye</strong>: <code>sensor_agents_share</code> (bodies with a sensor block), <code>sensor_mean</code> (blocks per body: the range is one cell plus it), <code>sense_decisions</code> (decisions taken by bodies with a sensor) and <code>sense_used</code> (of those, the share that differ from the same body seeing one cell: the knockout).</li>
  <li><strong>Sensor lineages</strong>: from the lineage log, the steps a lineage spends with a mean of one sensor or more per body, and its peak size then.</li>
  <li><strong>The start</strong>: the survey's peak, bottleneck (fewest bodies after the peak) and death step over 10,000 steps, from a trace every 100 steps.</li>
  <li><strong>The crowd</strong>: contacts per body per step, fruit's and dead matter's share of the intake, the biters' share, lineages alive, mass.</li>
  <li>e022's measures otherwise: population, food eaten, fruit, trees, sun, soil, matter, events, snapshots.</li>
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
<div class="grid2">
{charts["sensor_share"]}{charts["sensor_mean"]}
</div>
<p>{text["r1"]}</p>

<h3>3.2 {text["h2"]}</h3>
<div class="grid2">
{charts["sense_used"]}{charts["mass"]}
</div>
{gallery(GALLERY)}
<p>{text["r2"]}</p>

<h3>3.3 {text["h3"]}</h3>
{survey_table}
<p>{text["r3"]}</p>

<h3>3.4 {text["h4"]}</h3>
<div class="grid2">
{charts["pop"]}{charts["fruit_share"]}
</div>
<div class="grid2">
{charts["contacts"]}{charts["eaten"]}
</div>
<p>{text["r4"]}</p>

<h3>3.5 {text["h5"]}</h3>
<div class="grid2">
{charts["biters"]}{charts["lineages"]}
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
    <select id="mode"><option value="long">Long view: every 10,000 steps</option><option value="clip">Clip: every 4th step from 600,000</option></select>
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
<p>Every 100,000th record; full logs in <code>results/*_log.csv</code>, lineages in <code>results/*_lineages.csv</code>, events in <code>results/*_events.csv</code>, the start survey in <code>results/start_survey.csv</code>; e022's runs in <code>../e022_spill/results</code>. Build: <code>uv run python experiments/e023_eyes/report.py</code>.</p>
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
    ("eyes that see far", 4, 1, "the frame that sees", "A frame of 22 cells open at the back, 7 by 7 world cells, with 3 sensor blocks and 4 of muscle on average where e022's frame had 1-4 of armor at the corners: the only lineage of its run for 1,000,000 steps, a sensor per body for 695,000 of them, in the crowd state (fruit 75% of the intake, contacts 0.69). It sees the piles three to four cells off and walks (forward 66% of its decisions) from ring to ring.", 1_000_000),
    ("eyes that see far", 2, 24, "the frame that grew eyes late", "The winner of seed 2 for all 1,000,000 steps: until step 750,000 a body of 11 cells with a third of a sensor, then a frame of 22 cells, 7.8 by 7.7, with 4 sensors and 2 muscle, and the run enters the crowd state with it (fruit 48% to 77%). A sensor per body for 261,000 steps: e022's longest was 23,000.", 1_000_000),
    ("eyes that see far", 2, 1053, "the giant with eight eyes", "Twenty-three cells - 15 gut, 8 sensors, no armor - alive 69,000 steps with 329 agents at its peak, beside the winner: a body that sees nine cells in every direction, the range's cap, and did not keep the crowd's rings for itself."),
    ("eyes that see far", 1, 286, "the bar, blind", "Ten gut cells 2.5 by 6.5, no sensor (0.1 per body), the winner of seed 1 for 881,000 steps in the mixed state (fruit 53%, contacts 0.39): e022's bar, and the eye does not pay for it. Where the fruit is half the intake, a body walks into the piles as before."),
    ("eyes that see far", 3, 279, "the lawn's row", "Seven gut cells in a single row, 1.3 by 7.8, no sensor, the winner of seed 3 for 904,000 steps: the run fell out of the crowd state at step 500,000 (fruit 21%, contacts 0.11, 2,200 bodies of 7.6 cells) and became e021's lawn, where there is nothing to see."),
    ("eyes that see far", 3, 755, "a body of eyes", "Fourteen sensor blocks on a gut of 12, 37 agents for 19,000 steps around step 510,000: the far end of what the law allows, a body that spends half its cells on sight, and could not pay for them on the lawn."),
]

TEXT = {
    "question": "e022's spill put the world's food in piles on the rings around the trees, and its start showed what that costs a body that sees two cells: the lawn under the crowns goes dark, the production lies clumped on the rings, and the bodies wander the dark lawn and starve - one world in five dies before step 4,000. In the standing world the same limit holds: a body finds a pile by walking into it. Issue #26 writes the eye as a law about a material: a sensor block sees a distance, the cost stays the upkeep per block, and range is paid for. e009 found eyes do not pay when there is nothing to see; there is something to see now. Hypotheses:",
    "world": "Everything is e022's closed world (128x128 on a torus, matter 8 per cell at the start, bodies of 8x8 cells in five kinds grown from the genome, space at the resolution of the body, work = force x distance, a cell that costs what it holds, the dead eaten where they lie, the terrain with soil that runs downhill, the canopy, the spill at radius 1, rain on every cell alike, mutation per base) with one law changed: what a sensor block is.",
    "runs": "<strong>Runs.</strong> The flat world (rain on every cell alike, relief 64) for 1,000,000 steps, seeds 1-4, two threads each, four at once on one machine (8 cores, 107 minutes; 145-250 steps per second). The control is e022's flat seeds 1-4: the same code at <code>eyes 0</code> (checked byte for byte on seed 9 over 10,000 steps), so nothing was rerun. Before the batch: a pilot (seed 9, 100,000 steps) and a survey of the start, 24 runs of 10,000 steps (seeds 1-8 of the three worlds: rain on the mountains, half the breath, the flat lawn), six at once, five minutes.",
    "tldr": "The eye pays where the crowd is. In two seeds of four the winning body carries a sensor per body for 261,000 and 695,000 steps (e022's longest: 23,000), and it is the frame of the crowd state with 3-4 sensors and 2-4 muscle where e022's frame had armor at the corners: a frame that sees the next ring and walks to it. In the other two seeds the world is a mixed state or a lawn, the winner is the blind bar, and the eye does not pay - there is nothing to see. The start's deaths fall from 5 to 2 in 24, its bottlenecks barely. No tooth: an eye alone does not make a hunter. Next: #27, what flesh is worth, with a body that can see the prey.",
    "c1": "yes", "l1": "Yes, in two seeds of four", "v1": "Seed 4 carries a sensor on 74% of its bodies over the second half (3.0 blocks per body) and seed 2 on 60% over its last quarter (4.3 per body); the winners of both hold a sensor per body for 695,000 and 261,000 steps, against e022's best of 23,000 (its flat runs: 1-7% of the bodies, 0.1-0.4 blocks per body, no lineage with a sensor per body for 100,000 steps). Seeds 1 and 3 stay at 3% and 0.7%.",
    "c2": "partly", "l2": "Partly", "v2": "The eye changes 16-21% of the sensed decisions in seeds 1-3 (e022: 11-14%) and 10% in seed 4, the run where nearly every body has one. In seed 4 the eye is on 74% of the bodies and changes one decision in ten; a body that carries three sensors for 700,000 steps is using them, but the knockout's share does not rise with the range.",
    "c3": "partly", "l3": "Fewer deaths, the same bottleneck", "v3": "2 deaths in 24 starts (flat seed 6 at step 4,804, half seed 8 at 5,346) against e022's 5, in different seeds; the survivors pass through 33-418 bodies against 7-431. The eye saves three worlds in twenty-four and does not lift the floor: the piles are found, the boom to 4,000 bodies by step 100 and the crash are the same.",
    "c4": "partly", "l4": "Three of four", "v4": "Matter is conserved (0.9997-0.9999) and no run died; population cv is 0.04-0.12 (seeds 1 and 2 at 0.11-0.12, over the bound). Fruit is 53-75% of the intake and contacts 0.32-0.69 in seeds 1, 2 and 4; seed 3 fell out of the crowd state at step 500,000 to a lawn of 2,200 bodies of 7.6 cells (fruit 21%, contacts 0.11), a state e022's flat runs never entered.",
    "c5": "yes", "l5": "Yes", "v5": "The biters' share is 0.000 on median in every run with peaks of 0.003-0.011 (e022: 0.003-0.026), no biter lineage lasts, and dead matter is 5-18% of the intake, e022's 10-26%. The frame that sees has muscle and no armor; it walks to fruit, not to bodies.",
    "h1": "The eye pays where the crowd is",
    "r1": "The sensor share (left) tells two stories. In seed 4 it climbs from 25% at the start to 57% by step 400,000 and 75% by the end, on one lineage, and in seed 2 it jumps to 60-84% at step 750,000 when the winner grows eyes and the run enters the crowd state; in seeds 1 and 3, and in all four of e022's runs, it decays from the start's 10-25% to a few percent and stays there. Sensor blocks per body (right) say the same: 3 per body in seed 4 and 4 in seed 2's last quarter, against 0.1-0.4 everywhere else. The eye is selected in the state where the food lies in piles a few cells apart and nowhere else.",
    "h2": "The frame that sees walks from ring to ring, and reads its eyes one decision in ten",
    "r2": "The knockout (left) is flat at 10-21% in every run and does not climb with the range: seed 4's frame, three sensors on nearly every body, changes one decision in ten by its eyes, e022's 11-14% with the second cell. The eye is not read more often; it is read farther. Mass (right) marks the states: 20-22 cells in the crowd state (seed 4, seed 2 late), 10-12 in the mixed, 7.6 on the lawn. The bodies (Figure 2) show what the eye bought: e022's frame had 1-4 hard cells at its corners and 0.1-0.3 muscle; the frame that sees has 0.2 hard, 2-4 muscle and 3-4 sensors, and moves forward in 66% of its decisions. It traded its armor for sight and legs.",
    "h3": "The start: fewer deaths, the same bottleneck",
    "r3": "The survey counts 2 deaths against 5 and bottlenecks of 33-418 against 7-431. The eye does not change the shape of the start - every world booms to 4,000-4,700 bodies by step 100 and crashes to a few hundred by step 1,000 - it changes who finds the rings during the crash. Three worlds in twenty-four are saved by it; the lottery stays.",
    "h4": "The world stands; one run fell to the lawn",
    "r4": "Population (top left) holds at 1,050-2,200 with no death and matter conserved; seeds 1 and 2 swing 5-10% more than the bound. The fruit share (top right) and contacts (bottom left) show three runs in the crowd or mixed state (fruit 53-75%, contacts 0.32-0.69) and seed 3 leaving it at step 500,000 for a lawn (fruit 21%, contacts 0.11), a state none of e022's four flat runs entered: the crowd state is a state, not a law, and a run can fall out of it. Food eaten (bottom right) is 96-114 per step, e022's 97-134: the eye does not raise the world's income, it moves who eats it.",
    "h5": "No tooth",
    "r5": "Biters (left) peak at 0.3-1.1% and fall back every time; lineages (right) stay at 1-2. A body that sees far and has legs walks to the fruit, because a body of 20 cells is worth 0.4 plus its energy and a pile of fruit is worth more: the eye removes one of the reasons a hunter could not exist and leaves the other, what flesh is worth (#27).",
    "viewer": "The flat world, seed 4, the frame that sees. The food layer shows the trees as bright points with fruit around them, and the frames - 7 cells wide, yellow sensor blocks on their edges - standing on the rings and moving between them.",
    "discussion": "<p>The law was written as a material, and selection read it as one: a sensor block that sees one cell more is kept on the body that has something to see, the frame in the crowd state, and dropped by the bar in the mixed state and the row on the lawn. e009's finding holds in the closed world - eyes do not pay when there is nothing to see - with its other half now shown: when the food lies in piles a few cells apart, a body pays for three or four of them and keeps them for 700,000 steps. The surprise is what the eye replaced. e022's frame armored its corners; the frame that sees has no armor, three sensors, and four muscle. In a crowd that touches 0.7 times per body per step, the body that came out is not the one that can take a push but the one that sees the next ring and gets there first.</p><p>The knockout did not climb with the range. Seed 4's frame reads its eyes in one decision in ten, less than e022's bodies read their second cell. The eye of a linear policy is a gradient, not a map: it tips a body toward a pile it would otherwise have missed, in the tenth decision where the two cells ahead are empty and the pile is at four. That tenth decision is worth three cells of gut, or the eye would not have been kept.</p><p>What this does not show: whether the crowd state is the eye's doing or its cause. Seed 2's eyes came with its crowd state at step 750,000, and seed 3 lost both at 500,000; the eye and the crowd select each other, and four runs cannot say which comes first. The start's lottery is not the eye's to fix: the crash is the boom's, and the eye only decides who finds the rings after it. The mountain worlds were not run; the flat result was clear enough, and the ring is the same on a slope.</p>",
    "conclusion": "The eye is kept as a law about a material: a sensor block sees one more cell, seen at 1/distance, range paid for with the cell. It pays in the crowd state and nowhere else, which is the right answer for a law and the first block since e011 whose worth depends on the state of the world. The frame that sees - no armor, four muscle, three eyes - is the body of the crowd now. Next is #27, what flesh is worth: a body that can see prey exists, a body worth eating does not, and the tooth is still unpaid. Then #25, what a block weighs; #24, weather, with a crowd and an eye for it to work on.",
}


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "lineages":
        top_lineages()
    else:
        main()

