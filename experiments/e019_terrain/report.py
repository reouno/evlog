#!/usr/bin/env python3
"""Build report.html for e018.

Charts: matplotlib, exported as SVG and inlined. Diagram: hand-written SVG.
Run from the repo root: uv run python experiments/e018_closed_cycle/report.py
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

E017 = os.path.join(HERE, "..", "e017_dead_body_food")
# Worlds of this experiment: label -> (run prefix, world size, widths, seeds). Places are named by their width; a width of 0 is the
# uniform sun (one place, every cell).
WORLDS = {
    "8 per cell": ("128_sigma8-1", 128, (8, 1), [1, 2, 3, 4]),
    "4 per cell": ("128_sigma8-1-m4", 128, (8, 1), [1, 2, 3, 4]),
    "1 per cell": ("128_sigma8-1-m1", 128, (8, 1), [1, 2, 3, 4]),
    "uniform sun, 8 per cell": ("128_sigma0", 128, (0,), [1, 2, 3, 4]),
}
DRAWN = ["8 per cell", "4 per cell", "1 per cell"]  # grass and trees
# e017's grass and trees, seeds 1-4 (the same world with the sun regrowing every cell whatever its soil): label -> (run prefix, folder, widths).
REFS = {"e017 (no soil)": ("128_sigma8-1", E017, (8, 1))}
PLACE_NAME = {8: "grass (width 8)", 4: "shrubs (width 4)", 2: "edge (width 2)", 1: "trees (width 1)", 0: "beyond the patches"}
PLACE_COLOR = {8: SERIES[0], 4: SERIES[3], 2: SERIES[1], 1: SERIES[2], 0: INK}
WORLD_COLOR = {"8 per cell": SERIES[0], "4 per cell": SERIES[3], "1 per cell": SERIES[1], "uniform sun, 8 per cell": SERIES[2], "e017 (no soil)": INK}
KIND_COLOR = {1: SERIES[0], 2: SERIES[1], 3: SERIES[3], 4: SERIES[2]}
CONFIRM_STEPS = 5000
MAIN = "8 per cell"
VIEWER_WORLD = "8 per cell"
VIEWER_SEED = 1
LAST_STEP = 1_000_000


def seeds_of(w):
    if os.environ.get("EVLOG_SEEDS"):  # a dry run on the seeds that are done
        return [int(x) for x in os.environ["EVLOG_SEEDS"].split(",")]
    return WORLDS[w][3] if w in WORLDS else [1, 2, 3, 4]


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


def soil_stats(run, size=128, folder=HERE):
    """Per soil dump (every 100,000 steps): how rough the soil is and where it lies. top: share of the soil in the richest tenth of
    the cells (0.1 if flat); per place (by width) the soil per cell and the share of bare cells (soil under 1); under: soil under
    the bodies over the soil of the cells with no body; plants likewise."""
    frames = {fr["step"]: fr for fr in read_frames(f"results/{run}_long.jsonl", folder)}
    bodies = load_bodies(run, folder)
    out = []
    for step, soil, plant in soil_maps(run, folder):
        fr = frames.get(step)
        if fr is None:
            continue
        n = len(soil)
        srt = sorted(soil, reverse=True)
        total = sum(srt) or 1e-9
        top = sum(srt[: n // 10]) / total
        pm = place_map(fr["patches"], size)
        by = {}
        for p in set(pm):
            cells = [i for i in range(n) if pm[i] == p]
            by[p] = dict(cells=len(cells), soil=sum(soil[i] for i in cells) / len(cells), plant=sum(plant[i] for i in cells) / len(cells),
                         bare=sum(1 for i in cells if soil[i] < 1) / len(cells), rich=sum(1 for i in cells if soil[i] >= 8) / len(cells))
        held = set(here_cells(fr, bodies, size))
        under = [soil[i] for i in held]
        free = [soil[i] for i in range(n) if i not in held]
        out.append(dict(step=step, top=top, mean=total / n, by=by, under=sum(under) / max(len(under), 1), free=sum(free) / max(len(free), 1),
                        std=math.sqrt(sum((v - total / n) ** 2 for v in soil) / n), rough=sum(abs(soil[i] - soil[(i // size) * size + (i + 1) % size]) for i in range(n)) / n / (total / n)))
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


def place_chart(title, subtitle, places, world, key_fn, refs=None, ymin=0, ymax=None, percent=False, beyond=False):
    """One thin line per seed and place, colored by place, for one world (with the cells beyond every patch when `beyond`).
    refs: {label: (value, color)} as dashed lines."""
    fig, ax = new_axes()
    top = 0
    for p in list(WORLDS[world][2]) + ([0] if beyond else []):
        for k, s in enumerate(seeds_of(world)):
            if p not in places[world][s]:
                continue
            d = places[world][s][p]
            ys = key_fn(d)
            top = max(top, max(ys))
            ax.plot(d["step"], ys, color=PLACE_COLOR[p], linewidth=1.1, alpha=0.85, label=PLACE_NAME[p] if k == 0 else None)
    for label, (v, color) in (refs or {}).items():
        ax.axhline(v, color=color, linestyle="--", linewidth=1, label=label)
        top = max(top, v)
    finish(ax, ymin, ymax, top, percent, 2)
    return figure(title, subtitle, to_svg(fig))


def narrow_chart(title, subtitle, places, worlds, key_fn, ymin=0, ymax=None, percent=False, refs=None):
    """The narrow place of several worlds on one chart: one thin line per seed, colored by world."""
    fig, ax = new_axes()
    top = 0
    for w in worlds:
        p = WORLDS[w][2][1]
        for k, s in enumerate(seeds_of(w)):
            d = places[w][s][p]
            ys = key_fn(d)
            top = max(top, max(ys))
            ax.plot(d["step"], ys, color=WORLD_COLOR[w], linewidth=1.1, alpha=0.85, label=f"{PLACE_NAME[p].split(' (')[0]} (width {p})" if k == 0 else None)
    for label, (v, color) in (refs or {}).items():
        ax.axhline(v, color=color, linestyle="--", linewidth=1, label=label)
        top = max(top, v)
    finish(ax, ymin, ymax, top, percent, 2)
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


def sides_chart(title, subtitle, places, world, place):
    """Hardness of the front, the back and the sides on one place, one line per seed and side."""
    fig, ax = new_axes()
    top = 0
    for key, color, label in (("shell_front", SERIES[1], "front"), ("shell_back", SERIES[0], "back")):
        for k, s in enumerate(seeds_of(world)):
            d = places[world][s][place]
            ys = d[key]
            top = max(top, max(ys))
            ax.plot(d["step"], ys, color=color, linewidth=1.1, alpha=0.85, label=label if k == 0 else None)
    finish(ax, 0, None, top, False, 2)
    return figure(title, subtitle, to_svg(fig))


def soil_map_figure(title, subtitle, picks):
    """The soil of every cell at the end of one run per world (picks: [(world, seed)]), on a log scale, the patches as rings."""
    fig, axes = plt.subplots(1, len(picks), figsize=(13, 13 / len(picks) + 0.4))
    axes = list(axes) if len(picks) > 1 else [axes]
    for ax, (w, seed) in zip(axes, picks):
        run = f"{WORLDS[w][0]}_seed{seed}"
        size = WORLDS[w][1]
        step, soil, _ = soil_maps(run)[-1]
        grid = [[math.log1p(soil[y * size + x]) for x in range(size)] for y in range(size)]
        ax.imshow(grid, cmap="YlOrBr", vmin=0, vmax=math.log1p(30), interpolation="nearest")
        fr = next(fr for fr in read_frames(f"results/{run}_long.jsonl") if fr["step"] == step)
        for cx, cy, sg in fr["patches"]:
            if sg > 0:
                ax.add_patch(plt.Circle((cx, cy), 2 * sg, fill=False, color=PLACE_COLOR[int(sg)], linewidth=0.9, linestyle="--"))
        ax.set_title(f"{w}, seed {seed}", fontsize=9, color=INK)
        ax.set_xticks([])
        ax.set_yticks([])
        ax.grid(False)
        for sp in ax.spines.values():
            sp.set_visible(False)
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
<svg viewBox="0 0 800 330" role="img" aria-label="The closed cycle of matter in e018: soil, plant, body and dead matter, with what moves between them per step. A plant grows out of the soil of its cell by at most the sun (0.1 per step on the grass, 6.5 on a tree cell), not above the cap and not under a body. A gut eats 0.02 per cell per step from the plant and the dead matter under it. What a body spends (0.002 per cell and 0.032 per body per step, and the work of moving) falls to the soil under it. A body that dies lays its cells and energy where it lies; dead matter rots into the soil at 1% per step. The total is fixed." style="max-width:100%;height:auto;display:block">
<g fill="none" stroke="currentColor" stroke-width="1.2" font-size="12" font-family="system-ui, sans-serif">
  <rect x="40" y="40" width="150" height="54" rx="6"/>
  <text x="115" y="62" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">plant</text>
  <text x="115" y="80" text-anchor="middle" fill="currentColor" stroke="none">on the cell, at most 8</text>
  <rect x="40" y="230" width="150" height="54" rx="6" stroke="var(--s1)" stroke-width="2"/>
  <text x="115" y="252" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">soil</text>
  <text x="115" y="270" text-anchor="middle" fill="currentColor" stroke="none">of the cell, unbounded</text>
  <rect x="560" y="40" width="150" height="54" rx="6"/>
  <text x="635" y="62" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">body</text>
  <text x="635" y="80" text-anchor="middle" fill="currentColor" stroke="none">cells (0.02 each) + energy</text>
  <rect x="560" y="230" width="150" height="54" rx="6"/>
  <text x="635" y="252" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">dead matter</text>
  <text x="635" y="270" text-anchor="middle" fill="currentColor" stroke="none">lying on the cell (e017)</text>

  <path d="M 100,230 L 100,96" stroke="var(--s1)" stroke-width="2" marker-end="url(#arrow)"/>
  <text x="112" y="118" fill="currentColor" stroke="none" font-weight="600">sun</text>
  <text x="112" y="134" fill="currentColor" stroke="none">at most the patch's rate per step</text>
  <text x="112" y="150" fill="currentColor" stroke="none">(0.1 on the grass, 6.5 on a tree),</text>
  <text x="112" y="166" fill="currentColor" stroke="none">never above 8, not under a body,</text>
  <text x="112" y="182" fill="currentColor" stroke="none">never more than the soil holds</text>

  <path d="M 192,60 L 556,60" stroke="currentColor" marker-end="url(#arrow)"/>
  <text x="374" y="52" text-anchor="middle" fill="currentColor" stroke="none">eat: 0.02 per gut cell per step from the cell under it</text>

  <path d="M 558,94 L 194,228" stroke="currentColor" marker-end="url(#arrow)"/>
  <text x="380" y="190" fill="currentColor" stroke="none"><tspan font-weight="600">spend:</tspan> 0.002 per cell + 0.032 per body</text>
  <text x="380" y="206" fill="currentColor" stroke="none">per step, and the work of moving,</text>
  <text x="380" y="222" fill="currentColor" stroke="none">fall to the soil under the body</text>

  <path d="M 620,96 L 620,226" stroke="currentColor" marker-end="url(#arrow)"/>
  <text x="672" y="134" fill="currentColor" stroke="none">die: cells and energy</text>
  <text x="672" y="150" fill="currentColor" stroke="none">lie where the body was</text>
  <path d="M 660,226 L 660,96" stroke="currentColor" stroke-dasharray="4 3" marker-end="url(#arrow)"/>
  <text x="672" y="194" fill="currentColor" stroke="none">eat (the next</text>
  <text x="672" y="210" fill="currentColor" stroke="none">gut there)</text>

  <path d="M 556,270 L 194,270" stroke="currentColor" marker-end="url(#arrow)"/>
  <text x="374" y="262" text-anchor="middle" fill="currentColor" stroke="none">rot: 1% of what lies on the cell per step</text>

  <text x="40" y="312" fill="currentColor" stroke="none">the total is what the world started with: 8 per cell in plants (131,000) plus 5 in each of the 1,600 first bodies; or 4, or 1 per cell.</text>
</g>
<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="currentColor"/></marker></defs>
</svg>
<figcaption>Figure 1. The closed cycle. Matter is in one of four places and moves between them along the arrows; nothing enters and nothing leaves (upkeep and the work of moving were heat in e017 and now fall to the soil). The arrow the argument hinges on is the sun: a plant grows out of its own cell's soil, so the sun sets how fast a cell can give and the soil how much, and a cell keeps what was spent and died on it until the sun draws it out again. Everything else is e017: space at the resolution of the body, facing, e010's contact rule, work = force x distance, a cell held by a body does not regrow, a dead body is food where it lies, two kinds of place (or a uniform sun of 0.01 on every cell).</figcaption>
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
  let soilLayer = false;
  function tint(v){ const g = 40 + v * 12; return soilLayer ? [g * 0.9 | 0, g * 0.6 | 0, g * 0.25 | 0] : [g * 0.35 | 0, g, g * 0.45 | 0]; }
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
    const fr = frames[i]; soilLayer = layer.value === 'soil' && fr.sl > 0;
    const food = soilLayer ? bytes.subarray(fr.so, fr.so + fr.sl) : bytes.subarray(fr.fo, fr.fo + fr.fl), ag = bytes.subarray(fr.ao, fr.ao + fr.al);
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
        run = f"{WORLDS[world][0]}_seed{seed}"
        widths = WORLDS[world][2]
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
        p0, p1 = sum(int(r["p0"]) for r in rows), sum(int(r["p1"]) for r in rows)
        home = f"{p0 / max(p0 + p1, 1):.0%} on {PLACE_NAME[widths[0]].split(' (')[0]}"
        cards.append(f"""<figure class="card"><svg viewBox="-1 -1 89 89" width="120" height="120" role="img" aria-label="{html.escape(name)}"><rect x="-1" y="-1" width="89" height="89" fill="var(--cell)"/>{rects}<line x1="-1" y1="-0.5" x2="88" y2="-0.5" stroke="var(--ink2)" stroke-width="1.5" stroke-dasharray="3 2"/></svg>
<figcaption><strong>{html.escape(name)}</strong><br>{html.escape(world)}, seed {seed}, lineage {lid}: {span:,} steps, {int(peak["size"]):,} agents at its peak, {home}<br>mass {float(peak["mass"]):.0f} on {float(peak["foot"]):.1f} cells: hard {float(peak["hard"]):.0f}, muscle {float(peak["muscle"]):.0f}, digestive {float(peak["digestive"]):.0f}; dead matter {meat:.0%} of the intake<br>{html.escape(what)}</figcaption></figure>""")
    return f"""<figure class="diagram"><div class="cards">{"".join(cards)}</div>
<figcaption>Figure 2. Bodies of lineages that prospered: the most common body of the lineage at its peak, on the 8x8 grid a body grows on, front up (the dashed edge). Blue: hard, orange: muscle, green: digestive, yellow: sensor. "Cells" is the world cells the body covers; "dead matter" the share of the lineage's lifetime intake that was dead bodies.</figcaption></figure>"""


def main():
    logs, events, places = {}, {}, {}
    for w, (run, _, _, _) in WORLDS.items():
        seeds = seeds_of(w)
        logs[w] = {s: load_csv(f"results/{run}_seed{s}_log.csv") for s in seeds}
        events[w] = {s: load_rows(f"results/{run}_seed{s}_events.csv") for s in seeds}
        places[w] = {s: load_places(f"{run}_seed{s}") for s in seeds}
    rlogs = {w: {s: load_csv(f"results/{run}_seed{s}_log.csv", folder) for s in [1, 2, 3, 4]} for w, (run, folder, _) in REFS.items()}
    rplaces = {w: {s: load_places(f"{run}_seed{s}", folder) for s in [1, 2, 3, 4]} for w, (run, folder, _) in REFS.items()}
    STATS = {w: {s: soil_stats(f"{WORLDS[w][0]}_seed{s}", WORLDS[w][1]) for s in seeds_of(w)} for w in WORLDS}

    def med(x):
        x = [v for v in x if v == v]
        return statistics.median(x) if x else float("nan")

    def half(d, key):
        n = len(d["step"])
        return d[key][n // 2:]

    def summarize(w, s):
        log = logs[w][s]
        run = f"{WORLDS[w][0]}_seed{s}"
        widths = WORLDS[w][2]
        pl = places[w][s]
        st = STATS[w][s]
        first, last, _ = lineage_stats(run)
        per_step = Counter(int(r["step"]) for r in load_rows(f"results/{run}_lineages.csv"))
        last_step = int(log["step"][-1])
        pop = half(log, "pop")
        sun = [r + sh + wa + b for r, sh, wa, b in zip(log["regrowth"], log["shaded"], log["wasted"], log["barren"])]
        end = st[-1] if st else None
        d = dict(pop=med(pop), pop_min=min(log["pop"]), pop_cv=statistics.pstdev(pop) / max(statistics.mean(pop), 1), pop_swing=max(pop) / max(min(pop), 1),
                 extinct=last_step < LAST_STEP, extinct_at=last_step if last_step < LAST_STEP else float("nan"), sps=med(log["steps_per_sec"]),
                 lineages=med([per_step.get(t, 0) for t in range(1000, last_step + 1, 1000)]), ids=len(first),
                 contacts=med([c / max(p, 1) / 10_000 for c, p in zip(half(log, "contacts"), pop)]), forward=med(half(log, "forward")),
                 happened=med([(1 - b) * f for b, f in zip(half(log, "blocked"), half(log, "forward"))]),
                 mass=med(half(log, "mass_mean")), hard=med(half(log, "hard_mean")), muscle=med(half(log, "muscle_mean")), foot=med(half(log, "foot_mean")),
                 eaten=med([(pl_ + m) / 10_000 for pl_, m in zip(half(log, "plant_intake"), half(log, "meat_intake"))]),
                 meat_share=med([m / max(pl_ + m, 1e-9) for pl_, m in zip(half(log, "plant_intake"), half(log, "meat_intake"))]),
                 barren=med([b / max(t, 1e-9) for b, t in zip(half(log, "barren"), sun[len(sun) // 2:])]), barren_abs=med(half(log, "barren")),
                 shaded=med([b / max(t, 1e-9) for b, t in zip(half(log, "shaded"), sun[len(sun) // 2:])]), regrowth=med(half(log, "regrowth")),
                 spent=med(half(log, "spent")), rot=med(half(log, "rot")), dead=med(half(log, "dead")), carrion=med(half(log, "carrion")),
                 matter_start=log["matter"][0], matter_end=log["matter"][-1], matter_hold=log["matter"][-1] / log["matter"][0],
                 soil_share=med([so / m for so, m in zip(half(log, "soil"), half(log, "matter"))]),
                 top=end["top"] if end else float("nan"), top_first=st[0]["top"] if st else float("nan"), rough=end["rough"] if end else float("nan"),
                 under=end["under"] / max(end["free"], 1e-9) if end else float("nan"), soil_mean=end["mean"] if end else float("nan"))
        if end:
            for p in (8, 1, 0):
                if p in end["by"]:
                    d[f"soil_{p}"] = end["by"][p]["soil"]
                    d[f"bare_{p}"] = end["by"][p]["bare"]
                    d[f"rich_{p}"] = end["by"][p]["rich"]
                    d[f"plant_{p}"] = end["by"][p]["plant"]
        for k, p in zip(("a", "b"), widths):
            if p not in pl:
                continue
            q = pl[p]
            n = len(q["step"])
            h = slice(n // 2, n)
            d[f"pop_{k}"] = med(q["pop"][h])
            d[f"mass_{k}"] = med(q["mass"][h])
            d[f"hard_{k}"] = med(q["hard"][h])
            d[f"digestive_{k}"] = med(q["digestive"][h])
            d[f"meat_{k}"] = sum(q["meat_intake"][h]) / max(sum(q["plant_intake"][h]) + sum(q["meat_intake"][h]), 1)
            d[f"lineages_{k}"] = med(q["lineages"][h])
            d[f"foot_{k}"] = med(q["foot"][h])
            d[f"eaten_{k}"] = med([(a_ + b_) / 10_000 for a_, b_ in zip(q["plant_intake"][h], q["meat_intake"][h])])
            if "barren" in q:
                d[f"barren_{k}"] = med(q["barren"][h])
                d[f"regrowth_{k}"] = med(q["regrowth"][h])
                d[f"soilcell_{k}"] = med([so / c for so, c in zip(q["soil"][h], q["cells"][h])])
        return d

    S = {w: {s: summarize(w, s) for s in seeds_of(w)} for w in WORLDS}

    def rplace(w, p, key):
        """A reference world's per-place value: median over seeds of the median over the second half."""
        if p not in rplaces[w][1] or key not in rplaces[w][1][p]:
            return float("nan")
        return med([med(rplaces[w][s][p][key][len(rplaces[w][s][p][key]) // 2:]) for s in [1, 2, 3, 4]])

    def rsum(w, key):
        if key == "contacts_per":
            return med([med([c / max(p, 1) / 10_000 for c, p in zip(half(rlogs[w][s], "contacts"), half(rlogs[w][s], "pop"))]) for s in [1, 2, 3, 4]])
        if key == "eaten":
            return med([med([(pl_ + m) / 10_000 for pl_, m in zip(half(rlogs[w][s], "plant_intake"), half(rlogs[w][s], "meat_intake"))]) for s in [1, 2, 3, 4]])
        if key == "pop_cv":
            return med([statistics.pstdev(half(rlogs[w][s], "pop")) / statistics.mean(half(rlogs[w][s], "pop")) for s in [1, 2, 3, 4]])
        if key == "pop_swing":
            return med([max(half(rlogs[w][s], "pop")) / min(half(rlogs[w][s], "pop")) for s in [1, 2, 3, 4]])
        if key == "happened":
            return med([med([(1 - b) * f for b, f in zip(half(rlogs[w][s], "blocked"), half(rlogs[w][s], "forward"))]) for s in [1, 2, 3, 4]])
        if key == "pop_b":
            return rplace(w, REFS[w][2][1], "pop")
        if key == "eaten_b":
            return med([med([(a_ + b_) / 10_000 for a_, b_ in zip(half(rplaces[w][s][1], "plant_intake"), half(rplaces[w][s][1], "meat_intake"))]) for s in [1, 2, 3, 4]])
        if key not in rlogs[w][1]:
            return float("nan")
        return med([med(half(rlogs[w][s], key)) for s in [1, 2, 3, 4]])

    # e017's runs on the population and intake charts, as a gray world.
    logs_ref = dict(logs)
    logs_ref.update({w: rlogs[w] for w in REFS})
    all_worlds = list(WORLDS) + list(REFS)

    charts = {}
    charts["pop"] = world_chart("Population", "Bodies alive at each log step, one line per run; gray: e017's runs of the grass and trees world, where the sun regrew every cell whatever its soil. A line that ends is a world that died.", logs_ref, lambda l: l["pop"], all_worlds, WORLD_COLOR)
    charts["eaten"] = world_chart("Food eaten per step", "Plant and dead matter taken by guts per step, one line per run; gray: e017. The sun gives 164 per step in every world; what is eaten is what the soil let grow where bodies could reach it.", logs_ref, lambda l: [(p + m) / 10_000 for p, m in zip(l["plant_intake"], l["meat_intake"])], all_worlds, WORLD_COLOR)
    charts["barren"] = world_chart("Sun lost to empty soil", "Share of the sun that shone on a cell whose soil had nothing left (barren), per log window, one line per run. Zero is e017's world: there the soil was never a bound.", logs, lambda l: [b / max(r + sh + wa + b, 1e-9) for r, sh, wa, b in zip(l["regrowth"], l["shaded"], l["wasted"], l["barren"])], list(WORLDS), WORLD_COLOR, percent=True)
    charts["soil_place"] = place_chart("Soil per cell by place, 8 per cell", "Matter in the soil per cell of the place, at each log step, one line per seed. Gray: beyond every patch, where the patches passed and left their soil. The world started with 8 per cell in plants and none in the soil.", places, MAIN, lambda d: [so / c for so, c in zip(d["soil"], d["cells"])], beyond=True)
    charts["barren_place"] = place_chart("Sun lost to empty soil by place, 8 per cell", "Barren sun per step on the grass and on the trees, one line per seed (each kind of place gets 82 of sun per step). A tree cell gets 6.5 per step and empties its soil in a step or two.", places, MAIN, lambda d: d["barren"])
    charts["top"] = stats_chart("Where the soil lies: the richest tenth of the cells", "Share of the world's soil held by its richest tenth of cells, every 100,000 steps, one line per run. 10% is a flat world; a line that rises is matter piling up in places.", STATS, lambda d: d["top"], list(WORLDS), percent=True, ymax=1.0)
    charts["under"] = stats_chart("Soil under the bodies over soil elsewhere", "Mean soil of the cells with a body on them over the mean of the cells without, every 100,000 steps, one line per run. 1 is a world where bodies stand anywhere; above 1, bodies stand on the rich cells.", STATS, lambda d: d["under"] / max(d["free"], 1e-9), list(WORLDS), ymin=0)
    charts["maps"] = soil_map_figure("The soil at the end", "Soil per cell at step 1,000,000 (or the last dump before the world died), one run per world, seed 1, darker is more (log scale, 30 and above black); dashed rings are the patches at that step (blue: grass, aqua: trees, radius two widths).", [(w, 1) for w in WORLDS])
    charts["lineages"] = world_chart("Lineages alive", "Confirmed lineages at each log step. e017: 2-4; e012: 6-15.", logs, lambda l: l["lineages"], list(WORLDS), WORLD_COLOR)

    viewer_run = f"{WORLDS[VIEWER_WORLD][0]}_seed{VIEWER_SEED}"
    timeline = timeline_chart(f"Lineages over time ({VIEWER_WORLD}, seed {VIEWER_SEED})", "Each colored band is one lineage, height = agents in it; marks are events at the size they were logged with.", viewer_run, events[VIEWER_WORLD][VIEWER_SEED])

    first, _, _ = lineage_stats(viewer_run)
    bodies = load_bodies(viewer_run)
    data = bytearray()
    long_frames, used_l = pack_frames(f"results/{viewer_run}_long.jsonl", first, data, every=2)
    clip_frames, used_c = pack_frames(f"results/{viewer_run}_clip.jsonl", first, data, every=4, limit=50)
    legend = " ".join(f'<span class="sw" style="background:{KIND_COLOR[k]}"></span>{name}' for k, name in ((1, "hard"), (2, "muscle"), (3, "sensor"), (4, "digestive")))
    vw = WORLDS[VIEWER_WORLD][1]
    viewer_data = {"w": vw, "h": vw, "long": long_frames, "clip": clip_frames, "bodies": {str(b): bodies.get(b, "0" * 64) for b in used_l | used_c},
                   "kindColors": {str(k): v for k, v in KIND_COLOR.items()}, "palette": LINEAGE_PALETTE, "none": NONE_COLOR,
                   "slots": {str(k): v for k, v in color_slots(viewer_run).items()}}
    header = json.dumps(viewer_data, separators=(",", ":")).encode()
    blob = base64.b64encode(gzip.compress(len(header).to_bytes(4, "little") + header + bytes(data), 9)).decode()

    def rng(w, key, fmt):
        vals = [S[w][s].get(key, float("nan")) for s in seeds_of(w)]
        vals = [v for v in vals if v == v]
        if not vals:
            return "-"
        lo, hi = min(vals), max(vals)
        return fmt(lo) if fmt(lo) == fmt(hi) else f"{fmt(lo)}-{fmt(hi)}"

    def row(label, key, fmt, refkey=None):
        keys = key.split("|")  # several keys: one range each, separated by " / "
        cells = "".join("<td>" + " / ".join(rng(w, k, fmt) for k in keys) + "</td>" for w in WORLDS)
        f_ = lambda v: "-" if v != v else fmt(v)
        refs = "".join(f"<td>{f_(rsum(r, refkey))}</td>" if refkey else "<td>-</td>" for r in REFS)
        return f"<tr><td>{label}</td>{cells}{refs}</tr>"

    n0 = lambda v: f"{v:,.0f}"
    d1 = lambda v: f"{v:.1f}"
    d2 = lambda v: f"{v:.2f}"
    p0 = lambda v: f"{v:.0%}"
    summary = ("<thead><tr><th>Measure (range over seeds, median over the second half unless said)</th>" + "".join(f"<th>{w}</th>" for w in WORLDS) + "".join(f"<th>{r}</th>" for r in REFS) + "</tr></thead><tbody>"
               + row("Population", "pop", n0, "pop")
               + row("Population, coefficient of variation", "pop_cv", d2, "pop_cv")
               + row("Population, largest over smallest", "pop_swing", d1, "pop_swing")
               + row("Died at step", "extinct_at", n0)
               + row("Food eaten per step", "eaten", d1, "eaten")
               + row("Sun lost to empty soil, share of the sun", "barren", p0)
               + row("Sun lost to bodies standing on cells, share", "shaded", p0)
               + row("Bodies on the trees", "pop_b", n0, "pop_b")
               + row("Eaten on the trees per step", "eaten_b", d1, "eaten_b")
               + row("Soil per cell at the end: grass / trees / beyond", "soil_8|soil_1|soil_0", d1)
               + row("Grass cells bare at the end (soil under 1), share", "bare_8", p0)
               + row("Richest tenth of the cells, share of the soil at the end", "top", p0)
               + row("Soil under the bodies over soil elsewhere, at the end", "under", d2)
               + row("Matter at the end over the start", "matter_hold", lambda v: f"{v:.4f}")
               + row("Lineages alive", "lineages", n0, "lineages")
               + row("Steps per second", "sps", n0, "steps_per_sec")
               + "</tbody>")

    tables = data_table(["step", "place", "pop", "mass", "hard", "muscle", "digestive", "cover", "foot", "plant_intake", "meat_intake", "dead", "carrion", "soil", "barren", "regrowth", "cells", "lineages", "movers"],
                        {f"{w}, seed {s}, {PLACE_NAME[p]} (every 100,000 steps)": places[w][s][p] for w in WORLDS for s in seeds_of(w) for p in WORLDS[w][2] if p in places[w][s]}, every=10)
    tables += data_table(["step", "pop", "births", "deaths_energy", "mass_mean", "forward", "blocked", "foot_mean", "cover", "contacts", "regrowth", "shaded", "wasted", "barren", "rot", "spent", "dead", "carrion", "soil", "matter", "plant_intake", "meat_intake", "lineages", "steps_per_sec"],
                         {f"{w}, seed {s}, whole world (every 100,000 steps)": logs[w][s] for w in WORLDS for s in seeds_of(w)}, every=10)

    text = TEXT
    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>e018 A closed cycle through the soil - Report</title>
<style>{CSS}</style>
</head>
<body>
<main>
<h1>e018: A closed cycle through the soil</h1>
<p class="sub">Experiment report - 2026-08-31 - e017's world with one law added: matter does not vanish; a plant grows out of the soil of its cell, what a body spends falls to the soil under it, the dead rot into it. Grass and trees at 128x128 with 8, 4 and 1 per cell at the start, and a uniform sun at 8 per cell, four seeds each, 1,000,000 steps</p>

<section class="tldr">
<h2>TL;DR</h2>
<p>{text["tldr"]}</p>
</section>

<h2>1. Question</h2>
<p>{text["question"]}</p>
<ol>
  <li><strong>The soil binds where the sun is strong.</strong> With the drawn sun at e017's total (8 per cell), 20-40% of the sun is barren (it shines on a cell whose soil is empty), most of it on the trees, which hold 5-15 bodies (e017: 33-42); the world eats 20-30 per step (e017: 35-54) and holds 400-600 bodies (e017: 652-795).</li>
  <li><strong>The map remembers.</strong> The soil is rough, not flat: the richest tenth of the cells holds over 30% of the soil in every run (10% if flat), at least a fifth of the grass cells are bare (under 1) while the grass holds 5 or more per cell, and the matter the patches swept lies behind them as soil, 8 or more per cell beyond the patches.</li>
  <li><strong>Boom and bust at a scarce total.</strong> At 1 per cell the soil binds everywhere (60-90% of the sun barren), the population is 100-300 and swings: its coefficient of variation over the second half is above 0.15 and its largest value over its smallest above 2 in at least three seeds of four (e017: 0.03-0.09 and 1.18-1.60). At 8 per cell the swing stays in e017's range.</li>
  <li><strong>The soil does not make places.</strong> With a uniform sun, the richest tenth of the cells holds 30-40% of the soil at the end as at step 100,000 (roughness, not places), the soil under bodies is within 10% of the soil elsewhere, and the world is a lawn of about 2,000 small movers with one or two lineages. If the soil concentrates instead (over 50% in the richest tenth, bodies on the rich cells), this law can draw the patches.</li>
  <li><strong>The winners and the world.</strong> Lineages alive 1-4 and e017's wedge of eight gut cells winning the grass at 8 per cell; the bodies of the trees gone with the trees' food; matter conserved to within 1%; no extinction, at least 200 steps per second with six runs sharing a machine.</li>
</ol>

<h2>2. The world</h2>
<p>{text["world"]}</p>
{DIAGRAM}
<p>{text["runs"]}</p>
<ul class="measures">
  <li><strong>Sun</strong>: the regrowth field (164 per step over the world, 82 per kind of place), split each step into what grew (<code>regrowth</code>), what fell on a cell with a body on it (<code>shaded</code>), on a plant at the cap (<code>wasted</code>), or on empty soil (<code>barren</code>).</li>
  <li><strong>Soil</strong> (<code>soil</code>): matter in the soil, whole world and per place; <strong>spent</strong>: what bodies returned to it per step; <strong>rot</strong>: dead matter that returned to it per step. <strong>Matter</strong>: soil, plants, dead matter and bodies (energy and cells) added up; conservation is read from its end over its start.</li>
  <li><strong>The soil map</strong> (<code>soil.jsonl</code>, every 100,000 steps): the share of the soil in the richest tenth of the cells, the mean absolute difference between neighboring cells over the mean, the soil per cell and the share of bare cells (under 1) per place, and the soil under the bodies (the cell under the middle of each body) over the soil elsewhere.</li>
  <li>e017's measures: population, food eaten, dead matter laid and lying, contacts, moves, per place (population, body means, intake, lineages), hunter and scavenger lineages, lineage events, snapshots (now with the soil).</li>
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
{charts["barren"]}{charts["eaten"]}
</div>
<p>{text["r1"]}</p>

<h3>3.2 {text["h2"]}</h3>
<div class="wide">{charts["maps"]}</div>
<div class="grid2">
{charts["soil_place"]}{charts["barren_place"]}
</div>
<p>{text["r2"]}</p>

<h3>3.3 {text["h3"]}</h3>
<div class="grid2">
{charts["pop"]}{charts["lineages"]}
</div>
<p>{text["r3"]}</p>

<h3>3.4 {text["h4"]}</h3>
<div class="grid2">
{charts["top"]}{charts["under"]}
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
    <select id="layer"><option value="food">Ground: food</option><option value="soil">Ground: soil (long view)</option></select>
    <select id="speed"><option value="1">Slow</option><option value="2">Normal</option><option value="4">Fast</option></select>
    <span id="steplbl"></span>
  </div>
  <div class="bar"><input id="scrub" type="range" min="0" max="0" value="0"></div>
  <div class="bar" id="linlbl"></div>
  <div class="bar" id="legend">Blocks: {legend} <span class="sw front"></span> the front (white edge) <span class="sw dot"></span> has a bite on the front</div>
  <div class="bar">Left: the whole {vw}x{vw} world at the resolution of the body ({vw * 4}x{vw * 4} sub-cells), every cell a body holds colored by its lineage (gray: none), a white dot on bodies with a bite. The ground is food (green: plant and dead matter in one) or, with the selector, the soil (brown, log scale; the long view only); dashed rings are the patches (blue: grass, width 8; aqua: trees, width 1; radius two widths). Click to move the white box. Right: the box at 24x24 world cells, each body drawn cell by cell where it stands, turned the way it faces, with a white edge on its front. Labels: agents per lineage, then mean mass, cells spanned along x across the facing, bite, shell, and sensor cells. {VIEWER_WORLD}, seed {VIEWER_SEED}.</div>
</div>
<p>{text["viewer"]}</p>

<h2>4. Discussion</h2>
{text["discussion"]}

<h2>5. Conclusion and next step</h2>
<p>{text["conclusion"]}</p>

<h2>Appendix: data</h2>
<p>Every 100,000th record; full logs in <code>results/*_log.csv</code>, per place in <code>results/*_places.csv</code>, lineages in <code>results/*_lineages.csv</code>, events in <code>results/*_events.csv</code>, agents every 100,000 steps in <code>results/*_agents.csv</code>, the soil and plants of every cell every 100,000 steps in <code>results/*_soil.jsonl</code>, snapshots in <code>results/*_{{long,clip,bodies}}.jsonl</code>. Reference runs are read from <code>../e017_dead_body_food/results</code>. Build this report with <code>uv run python experiments/e018_closed_cycle/report.py</code>.</p>
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
    ("8 per cell", 1, 138, "the wedge, still", "Eight or nine digestive cells in a corner of the grid over 2.1 world cells: e016's and e017's winner, holding the grass from step 241,000 to the end with 616 agents at its peak. It eats the cell it stands on down and walks on; the soil under it keeps what it spent."),
    ("8 per cell", 4, 166, "the slab", "Fourteen digestive cells, 3.6 rows by 5.2 columns, over 3.4 world cells: the largest winner of the sixteen runs, 372,000 steps and 526 agents at its peak. Three cells under it means three cells' plants at once when the soil has let them grow."),
    ("8 per cell", 4, 46, "the wall with a rim", "Eleven digestive cells and 2.4 hard ones in a row 7 cells wide over 3.8 world cells, 439,000 steps at 336 agents: the one body of the runs with hard cells to speak of. The hard cells are the two ends of its front row with no muscle behind them: not a bite (a bite is force behind a hard tip), a face that a push does not break."),
    ("4 per cell", 1, 162, "the block at half the matter", "Ten or eleven digestive cells, 3.9 by 3.7, over 2.8 world cells, 417,000 steps and 418 agents at its peak: the same body as at 8 per cell in a world with half the soil, where 80 of the 164 of sun fall on empty cells."),
    ("1 per cell", 3, 53, "the survivor", "Six or seven digestive cells, 2 rows by 3 columns, over 2.2 world cells, the smallest winner: it held the one run at 1 per cell that did not die, 865,000 steps, 412 agents at its peak and 32 at its lowest. A small body costs 0.045 per step where a block costs 0.05, and lives through the bust."),
    ("uniform sun, 8 per cell", 2, 2, "the mower", "Eight or nine digestive cells in a bar 2 rows deep and 8 wide, over 3.3 world cells, the one lineage of the uniform world for the whole run (1,854 agents at its peak). It walks forward 42% of its decisions with the whole width of the grid as its front, and its trails are the weave in the soil map."),
]


TEXT = {
    "question": "e017 showed the premise \"matter that does not vanish\" without a memory: a dead body is food where it lies, worth what it cost (2-3% of the food), eaten within a few dozen steps, and the sun regrows every cell at the same rate whatever happened on it. This experiment closes the cycle (issue #20): matter is in the soil of a cell, in the plant on it, lying dead on it, or in a body, and nothing else; a plant grows out of its own cell's soil at most the sun's rate; what a body spends falls to the soil under it; the dead rot into it at 1% per step. The sun bounds the speed, the soil bounds the amount, and the total is what the world started with. Sixteen runs: the grass and trees world at 8 per cell (e017's total), 4 and 1 per cell, and a uniform sun at 8 per cell, four seeds each. The hypotheses:",
    "world": "Everything is e017's (128x128 on a torus, drifting food patches of two widths or a uniform sun, bodies of 8x8 cells in five kinds grown from the genome, space at the resolution of the body, a facing per body, e010's contact rule, a cell that costs what it holds, 0.032 per body per step, work = force x distance, a cell held by a body does not regrow, a dead body is food where it lies) with the soil added under the food of every cell and the cycle closed (Figure 1). Two arguments: the matter per cell at the start (plants at the cap and empty soil at 8, e017's start; plants at 4 or 1 and empty soil below it) and the patch widths, where a width of 0 is a uniform sun of 0.01 on every cell.",
    "runs": "<strong>Runs.</strong> Grass and trees (widths 8 and 1, two patches of each) at 8, 4 and 1 per cell, and the uniform sun at 8 per cell, seeds 1-4 each, one thread per run, six to ten at a time on two machines, 1,000,000 steps (5-30 minutes per run). The 4 per cell runs were added when the first two at 1 per cell died. A pilot (seed 9, 100,000 steps, all three worlds) came first. Reference: e017's runs of the grass and trees world, seeds 1-4, where the sun regrew every cell whatever its soil. We record e017's measures and:",
    "tldr": "The cycle closes and the map remembers: matter is conserved to 0.01% (0.8% under the uniform sun, f32 rounding of a million small additions), the soil keeps the trails of the patches and of the bodies, and the richest tenth of the cells holds 43-87% of it. But a plant that grows only out of its own cell's soil makes a poorer world: the sun draws the soil out of a patch faster than bodies return it, so the food the world eats equals what its bodies spend (23-26 per step at 8 per cell against 164 of sun, e017: 36), a third of the sun falls on empty cells, the trees lose their bodies (0-20, e017: 37) because a tree cell's 6.5 of sun empties its soil in a step, the population swings 2-4x (e017: 1.4x), lineages alive fall to 1-3 (e017: 4), and at 1 per cell three worlds of four die. Under a uniform sun the soil weaves into the trails of the walking bodies in three seeds of four and the food supply falls through the run. Seventy percent of the world's matter lies beyond the patches as soil that the drifting sun releases slowly, so the next law must move matter without bodies: water, a terrain the soil flows down, so that rich places are where matter collects and the sun can shine everywhere (#22).",
    "c1": "yes", "l1": "Yes", "v1": "At 8 per cell, 26-39% of the sun falls on cells whose soil is empty (17-26 per step on the grass, 20-42 on the trees, of 82 each), the world eats 22.9-26.4 per step (asked 20-30; e017: 35.6) and holds 414-482 bodies (asked 400-600; e017: 673). The trees hold 0-20 bodies (asked 5-15; e017: 37) and feed 0.5-1.6 per step (e017: 2.7): a tree cell gets 6.5 of sun per step, its soil holds a step of that, and the twenty bodies on it return 1 per step. What grows is what is returned: regrowth equals what bodies spent, 22-26 per step, in every run of every drawn world.",
    "c2": "yes", "l2": "Yes", "v2": "The richest tenth of the cells holds 43-46% of the soil at the end of the 8 per cell runs (36-38% at step 100,000; 10% if flat), 31-48% of the grass cells are bare (soil under 1) while the grass holds 4.9-10.6 per cell, and the cells beyond the patches hold 7.6-9.9 per cell, 70% of the world's matter, where the patches passed eating the plants and leaving the soil (Figure 3.2: the trails are dark, the patches' present places are pale, eaten down to the soil).",
    "c3": "partly", "l3": "Yes, and the scarce world dies", "v3": "At 1 per cell the soil binds everywhere (76-87% of the sun barren), the population is 100-172 with a coefficient of variation of 0.37-0.58 and swings of 10x or more (asked 0.15 and 2; e017: 0.06 and 1.4), and three worlds of four die (steps 304,308, 803,008 and 941,817; the fourth ends at 60 bodies). At 4 per cell the swing is 3.1-4.9x (cv 0.25-0.34) and the world stands; at 8 per cell it is 2.3-4.2x (cv 0.17-0.25), three to four times e017's, not e017's range as asked. A closed world of this kind swings at every total and dies when the total is small.",
    "c4": "no", "l4": "No: trails, not places", "v4": "In three seeds of four the soil concentrates, but into lines: the richest tenth of the cells holds 60-87% of the soil at the end (34-56% at step 100,000), 51-72% of the cells are bare, the soil under bodies is 1.4-2.4 times the soil elsewhere, and the map is a weave of the trails of the walking bodies (Figure 3.2, right), one cell wide, because a body that walks straight lays what it spends along its path and the sun draws the cells between the paths down to nothing. The sun lost to empty soil rises through the run from 5-10 to 34-77 per step, and the food eaten falls from 110-115 to 50-105. In the fourth seed nothing moves (36%, 1.01, barren 5). One lineage in every seed, a bar of 6-9 gut cells 2 rows deep and 5-8 wide walking forward 28-42% of the time.",
    "c5": "partly", "l5": "Fewer winners", "v5": "Lineages alive are 2 at 8 per cell, 1-3 at 4, 1 at 1 and 1 under the uniform sun (e017: 4; asked 1-4). A block of 9-14 gut cells wins the grass in every drawn run (Figure 2: the wedge, a slab of 14, and one wall with a hard rim on its side), the trees hold no lineage of their own, and the bodies of the scarce world are smaller (6-7 cells). Matter at the end is 0.9999-1.0002 of the start (the parent's leak) and 0.9923-1.0017 under the uniform sun (f32 rounding over 1,110-2,188 bodies). No extinction at 8 or 4 per cell; three of four at 1. 616-4,553 steps per second.",
    "h1": "The world lives on what its bodies return",
    "r1": "The sun gives 164 per step and the world at 8 per cell eats 23-26 of it, because a plant grows only out of the soil of its cell and the soil of a cell under the sun holds what was spent and died on it: a few steps' worth on a tree cell, a few hundred on a grass cell. The patch drains its own soil into plants faster than the bodies on it return matter, and from then on the loop runs at the bodies' rate: regrowth equals what was spent, in every run. A third of the sun falls on bare cells at 8 per cell, half at 4, four fifths at 1. The trees suffer most: a cell that was worth 6.5 per step in e017 is worth what twenty bodies spend on it, 1 per step, so the bodies of the trees are gone and with them e017's 7-12% of dead matter in the intake.",
    "h2": "The map remembers, and most of the matter lies where no sun is",
    "r2": "The soil maps (Figure 3.2) are the history of the run: the patches' trails are dark, their present places pale, the cells they never visited still hold their 8 as plants. Beyond the patches lies 70% of the world's matter, 7.6-9.9 per cell, as soil that will grow nothing until a patch drifts back over it. On the grass 31-48% of the cells are bare next to cells of 10 and more (the graves and the resting places): the richest tenth of the cells holds 43-46% of the soil. The soil under the bodies is 0.6-2.0 times the soil elsewhere: bodies stand where the plants are, and the plants are where the soil was just drawn out.",
    "h3": "The closed world swings, and dies when the total is small",
    "r3": "A population that eats what it returns has no fixed carrying capacity: a boom eats the standing plants down, the bodies starve and die where they stand, the dead rot into the soil at 1% per step, and the sun draws the soil back out at its own pace, so the bust lasts as long as the loop. At 8 per cell the population swings 2.3-4.2x over the second half (e017: 1.4x), at 4 per cell 3.1-4.9x, at 1 per cell 10x and more, and three worlds of four at 1 per cell die at 304,308, 803,008 and 941,817 steps. Lineages alive fall to 1-3 (e017: 4) as each bust ends a lineage or two.",
    "h4": "Under a uniform sun the soil weaves into trails",
    "r4": "With 0.01 of sun on every cell the world starts as a lawn of 2,000 bodies and, in three seeds of four, slowly locks its matter into lines: the one lineage of each run is a bar of 6-9 gut cells, 2 rows deep and 5-8 wide, that walks forward a third of its decisions, and the cells it walks along keep what it spends while the cells between them are drawn down to nothing. The richest tenth of the cells goes from 34-56% of the soil to 60-87%, the soil under bodies to 1.4-2.4 times the soil elsewhere, the sun lost to empty cells from 5-10 to 34-77 per step, and the food eaten from 110-115 to 50-105 per step, still falling at 1,000,000 steps. Bodies stand on the rich cells because the rich cells are their own trails. This is not a place (a trail is one cell wide and as long as a walk) and it is not a lawn: it is a world writing its own movements into its ground and eating less every year.",
    "h5": "The same block wins, and the trees hold nobody",
    "r5": "A block of 9-14 gut cells wins the grass in every drawn run, as in e016 and e017: the wedge, the slab of 14 (the largest winner of the sixteen runs), and one wall with 2.4 hard cells on its side, a face a push does not break. The survivor of the one scarce world that stood is the smallest body, 6-7 cells, and the mower of the uniform world is a bar 2 by 8. Nothing has a bite. The trees, which held tortoises and hunters in e011-e012 and forty grazers in e017, hold 0-20 bodies of the grass lineage passing through.",
    "viewer": "8 per cell, seed 1. With the ground as food the world looks like e017's, sparser: wedges on the grass with room between them, a handful of bodies on each tree. Switch the ground to soil and the run's history appears: the dark trails of the four patches over the pale cells they stand on now, dots of 10 and more where bodies died, and the plants of the never-visited cells still in place. The long view shows the wedge (lineage 138 from step 241,000, after lineages 38 and 158) holding the grass, and the population falling to 158 at step 210,000 and climbing back.",
    "discussion": "<p>The law does what it says: nothing is created or lost, the ground keeps what was spent and died on it, and the maps are the memory the premise asked for. What it changes is the world's budget. When a plant can grow only out of its own cell's soil, the sun stops being the world's income and becomes a pump that empties each cell into plants once; after that a cell gives back what bodies put in it, and the world eats what its bodies spend. The patches, which were the world's rich places, become the places the sun drains fastest: a tree cell that fed forty bodies on 6.5 per step feeds twenty on 1, and the regime of the trees, the one place in this world where bodies met, is gone. Judged by #19's rule, the closed cycle as it stands has fewer winners than the open world, not more.</p><p>What surprised us: the swing. e017's population moved 1.4x over half a million steps; the closed world moves 2-5x at every total, and dies at the small one, because the loop has a delay in it (a death returns to the soil at 1% per step, the sun draws the soil back out at its rate) and no reserve outside it. And the uniform world's weave: with the same sun everywhere, matter goes where the bodies walk, and a straight-walking body lays down lines that the sun cannot draw out as fast as the body lays them; the ground becomes a record of the walks and the world eats less every year. Principle 4 (the long run) fails in both: the scarce world dies, the uniform world declines.</p><p>What this does not show is a closed world with a flow. The real world's matter moves without bodies: water carries it downhill, a river delta is rich because a continent drains into it, and the sun shines everywhere. Here matter moves only in a body, so 70% of it lies where the patches were and grows nothing. The missing premise is not more sun and not more matter; it is a world whose ground moves matter on its own, so that rich places are where matter collects and the poor places are where it drains from. A terrain (a height per cell) and soil that spills downhill at a rate would give that, at one more f32 per cell, and would let the sun be uniform: the places would be the valleys, drawn by the water, not by the sun.</p>",
    "conclusion": "The closed cycle conserves matter (to 0.01%), makes the map remember (the richest tenth of the cells holds 43-87% of the soil; the trails of the patches and of the bodies are visible in the maps), and makes a poorer and swingier world: the food eaten equals what bodies return (23-26 per step of 164 of sun at 8 per cell, e017: 36), a third of the sun falls on empty cells, the trees lose their bodies, the population swings 2-4x, lineages fall to 1-3 (e017: 4), three scarce worlds of four die, and under a uniform sun the soil weaves into the walks and the food supply falls through the run. The soil stays in the code as the memory of the world; whether the cycle stays closed depends on the next law, which must move matter without bodies: a terrain that the soil flows down, so that rich places are where matter collects, the sun can shine everywhere, and what a patch drains comes back from above.",
}

if __name__ == "__main__":
    main()
