#!/usr/bin/env python3
"""Build report.html for e062 (foundation stage B, #75).

Charts: matplotlib, exported as SVG and inlined. Diagram: hand-written SVG.
Run from the repo root: uv run python experiments/e062_producers/report.py
The maps (results/**/*_maps.bin) are not committed; make them with maps=1 (see README).
"""
import csv
import glob
import html
import io
import math
import os

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Patch
from matplotlib.ticker import MaxNLocator

matplotlib.use("svg")

HERE = os.path.dirname(os.path.abspath(__file__))
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4"]  # fixed slot order
PRODUCER_SLOT = {"grass": 3, "wood": 2, "algae": 0}  # the same producer, the same colour, everywhere
WORLDS = ["c1182", "c1173", "c1225", "c1221", "c1236", "c1208"]
WORLD_NAME = {"c1182": "hot, wet", "c1173": "hot, dry", "c1225": "warm, very wet", "c1221": "mild",
              "c1236": "cool", "c1208": "cold"}
GRASS_LIFE, WOOD_LIFE, ALGAE_LIFE = 2000.0, 20000.0, 500.0  # plants.rs
GRASS_HALF, WOOD_HALF, ALGAE_HALF = 0.2, 4.0, 0.1

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

HABITATS = ["land_cold_dry", "land_cold_moist", "land_cold_wet", "land_mild_dry", "land_mild_moist", "land_mild_wet",
            "land_hot_dry", "land_hot_moist", "land_hot_wet", "shallow_cold", "shallow_mild", "shallow_hot",
            "deep_cold", "deep_mild", "deep_hot"]


# ---------- data ----------

def load_rows(pattern):
    out = []
    for f in sorted(glob.glob(os.path.join(HERE, pattern))):
        with open(f) as fh:
            r = next(csv.DictReader(fh))
        d = {k: float(v) for k, v in r.items()}
        name = os.path.basename(f)[: -len("_row.csv")]
        d["id"] = name
        d["world"] = name.split("_")[0]
        # How poor a place each producer can stand in: half / (rate x life), the least light x warmth x water.
        d["need_grass"] = GRASS_HALF / (d["grass_rate"] * GRASS_LIFE)
        d["need_wood"] = WOOD_HALF / (d["wood_rate"] * WOOD_LIFE)
        d["need_algae"] = ALGAE_HALF / (d["algae_rate"] * ALGAE_LIFE)
        out.append(d)
    return out


def load_years(path):
    with open(path) as f:
        rows = list(csv.DictReader(f))
    return {k: [float(r[k]) for r in rows] for k in rows[0]}


def load_maps(path):
    """The last year's quarters (habitat, temperature, fill, grass, wood, algae), the burnt cells, the elevation."""
    b = open(path, "rb").read()
    n = int(np.frombuffer(b[4:8], "<u4")[0])
    cells, o = n * n, 8
    elev = np.frombuffer(b[o:o + 4 * cells], "<f4").reshape(n, n)
    o += 4 * cells
    quarters = []
    for _ in range(4):
        hab = np.frombuffer(b[o:o + cells], "u1").reshape(n, n)
        o += cells
        fields = []
        for _k in range(5):
            fields.append(np.frombuffer(b[o:o + 4 * cells], "<f4").reshape(n, n))
            o += 4 * cells
        quarters.append((hab, *fields))
    burnt = np.frombuffer(b[o:o + cells], "u1").reshape(n, n)
    return elev, quarters, burnt


def spearman(a, b):
    def rank(v):
        order = sorted(range(len(v)), key=lambda i: v[i])
        r = [0.0] * len(v)
        for k, i in enumerate(order):
            r[i] = k
        return r
    ra, rb = rank(a), rank(b)
    n = len(a)
    ma, mb = sum(ra) / n, sum(rb) / n
    num = sum((x - ma) * (y - mb) for x, y in zip(ra, rb))
    den = math.sqrt(sum((x - ma) ** 2 for x in ra) * sum((y - mb) ** 2 for y in rb))
    return num / den if den else 0.0


# ---------- chart helpers ----------

def kfmt(x, _pos):
    return f"{x/1000:g}k" if abs(x) >= 1000 else f"{x:g}"


def to_svg(fig):
    buf = io.StringIO()
    fig.savefig(buf, format="svg", bbox_inches="tight", pad_inches=0.05)
    plt.close(fig)
    return buf.getvalue()


def legend_above(ax, n):
    ax.legend(loc="lower left", bbox_to_anchor=(0, 1.0), ncols=n, handlelength=1.2, borderaxespad=0, columnspacing=1.2)


def figure(title, subtitle, svg, wide=False):
    cls = "fig wide" if wide else "fig"
    return f"""
<figure class="{cls}">
  <figcaption><strong>{html.escape(title)}</strong><span>{html.escape(subtitle)}</span></figcaption>
  {svg}
</figure>"""


def shares_over_years(path, title, subtitle):
    d = load_years(path)
    fig, ax = plt.subplots(figsize=(6.4, 2.6))
    xs = d["year"]
    ax.stackplot(xs, [d["share_grass"], d["share_wood"], d["share_algae"]], labels=["grass", "wood", "algae"],
                 colors=[SERIES[PRODUCER_SLOT[p]] for p in ("grass", "wood", "algae")], linewidth=0)
    ax.set_ylim(0, 1)
    ax.margins(x=0)
    ax.set_xlabel("year of the producers", loc="right")
    ax.yaxis.set_major_formatter(lambda y, _p: f"{y:.0%}")
    ax.yaxis.set_major_locator(MaxNLocator(4))
    legend_above(ax, 3)
    return figure(title, subtitle, to_svg(fig))


def producer_map(path, title, subtitle):
    """Two opposite quarters: each cell coloured by its larger producer, paler where little stands, burnt cells orange."""
    _, quarters, burnt = load_maps(path)
    bare, water = np.array([0.85, 0.81, 0.72]), np.array([0.12, 0.29, 0.53])
    cols = {p: np.array(matplotlib.colors.to_rgb(SERIES[PRODUCER_SLOT[p]])) for p in ("grass", "wood", "algae")}
    fig, axes = plt.subplots(1, 2, figsize=(9.6, 4.9))
    fig.subplots_adjust(left=0.01, right=0.99, top=0.93, bottom=0.08, wspace=0.04)
    for ax, qi in zip(axes, (0, 2)):
        hab, _t, _m, g, w, a = quarters[qi]
        sea = hab >= 9
        img = np.empty(g.shape + (3,))
        total = g + w + a
        land_amount = np.clip(np.sqrt((g + w) / 6.0), 0, 1)[..., None]
        land_col = np.where((g >= w)[..., None], cols["grass"], cols["wood"])
        img[:] = bare * (1 - land_amount) + land_col * land_amount
        sea_amount = np.clip(np.sqrt(a / 1.0), 0, 1)[..., None]
        sea_img = water * (1 - sea_amount) + cols["algae"] * sea_amount
        img = np.where(sea[..., None], sea_img, img)
        if qi == 0:
            img = np.where((burnt > 0)[..., None], np.array(matplotlib.colors.to_rgb(SERIES[1])), img)
        ax.imshow(img, interpolation="nearest")
        ax.set_title(f"quarter {qi + 1}" + (" (orange: burnt in the year)" if qi == 0 else ""), fontsize=9)
        ax.set_xticks([])
        ax.set_yticks([])
        ax.grid(False)
        for s in ax.spines.values():
            s.set_visible(False)
        del total
    handles = [Patch(color=SERIES[PRODUCER_SLOT["grass"]], label="grass the larger (land)"),
               Patch(color=SERIES[PRODUCER_SLOT["wood"]], label="wood the larger (land)"),
               Patch(color=SERIES[PRODUCER_SLOT["algae"]], label="algae (water)"),
               Patch(color=bare, label="bare"), Patch(color=SERIES[1], label="burnt")]
    fig.legend(handles=handles, loc="upper center", ncols=5, fontsize=8, bbox_to_anchor=(0.5, 0.05), handlelength=1.0)
    return figure(title, subtitle, to_svg(fig), wide=True)


def scatter_by_world(rows, x, y, xlabel, ylabel_fmt, title, subtitle, xlog=False, ylog=False, band=None, hline=None, xfmt=None):
    fig, ax = plt.subplots(figsize=(6.4, 2.8))
    if band:
        ax.axhspan(band[0], band[1], color=SERIES[2], alpha=0.12, linewidth=0)
    if hline is not None:
        ax.axhline(hline, color=INK, linewidth=0.8, linestyle="--")
    markers = ["o", "s", "^", "D", "v", "P"]
    for k, wid in enumerate(WORLDS):
        sel = [r for r in rows if r["world"] == wid]
        ax.scatter([x(r) for r in sel], [y(r) for r in sel], s=14, marker=markers[k],
                   color=SERIES[k % 5] if k < 5 else INK, linewidths=0, label=f"{wid} {WORLD_NAME[wid]}")
    if xlog:
        ax.set_xscale("log")
    if ylog:
        ax.set_yscale("log")
    ax.set_xlabel(xlabel, loc="right")
    if xfmt:
        ax.xaxis.set_major_formatter(xfmt)
    if ylabel_fmt:
        ax.yaxis.set_major_formatter(ylabel_fmt)
    if not ylog:
        ax.yaxis.set_major_locator(MaxNLocator(4))
    ax.legend(loc="lower left", bbox_to_anchor=(0, 1.0), ncols=3, handlelength=1.0, borderaxespad=0, columnspacing=1.0, fontsize=8)
    return figure(title, subtitle, to_svg(fig))


# ---------- page ----------

CSS = f"""
:root {{
  --surface: #fcfcfb; --page: #f9f9f7; --ink: #0b0b0b; --ink2: #52514e; --grid: #e1e0d9; --border: rgba(11,11,11,0.10);
  --s1: {SERIES[0]};
}}
@media (prefers-color-scheme: dark) {{
  :root:not([data-theme="light"]) {{
    --surface: #1a1a19; --page: #0d0d0d; --ink: #ffffff; --ink2: #c3c2b7; --grid: #2c2c2a; --border: rgba(255,255,255,0.10);
    --s1: #3987e5;
  }}
}}
:root[data-theme="dark"] {{
  --surface: #1a1a19; --page: #0d0d0d; --ink: #ffffff; --ink2: #c3c2b7; --grid: #2c2c2a; --border: rgba(255,255,255,0.10);
  --s1: #3987e5;
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
.fig.wide {{ margin: 12px 0; }}
.fig svg {{ width: 100%; height: auto; display: block; font-family: system-ui, -apple-system, "Segoe UI", sans-serif; }}
figcaption strong {{ display: block; font-size: 15px; }}
figcaption span {{ display: block; color: var(--ink2); font-size: 13px; min-height: 2.6em; margin-bottom: 6px; }}
.diagram {{ margin: 12px 0; background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 12px 16px 8px; color: var(--ink); }}
.diagram figcaption {{ color: var(--ink2); font-size: 13px; margin-top: 4px; }}
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
"""

DIAGRAM = """
<figure class="diagram">
<svg viewBox="0 0 760 360" role="img" aria-label="Matter moves from the soil into grass, wood and algae by light, warmth and water; what dies lies as litter and rots back; fire sends dry fuel to the air and the soil; the air falls with the rain." style="max-width:100%;height:auto;display:block">
<defs><marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="currentColor"/></marker></defs>
<g fill="none" stroke="currentColor" stroke-width="1.2" font-size="12" font-family="system-ui, sans-serif">
  <rect x="20" y="160" width="140" height="60" rx="6"/>
  <text x="90" y="185" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">Soil</text>
  <text x="90" y="203" text-anchor="middle" fill="currentColor" stroke="none">10 a cell at the start</text>

  <rect x="290" y="50" width="200" height="56" rx="6" stroke="var(--s1)" stroke-width="2"/>
  <text x="390" y="73" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">Wood (land)</text>
  <text x="390" y="91" text-anchor="middle" fill="currentColor" stroke="none">half-light stand 4, life 20,000</text>
  <rect x="290" y="142" width="200" height="56" rx="6" stroke="var(--s1)" stroke-width="2"/>
  <text x="390" y="165" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">Grass (land)</text>
  <text x="390" y="183" text-anchor="middle" fill="currentColor" stroke="none">half-light stand 0.2, life 2,000</text>
  <rect x="290" y="234" width="200" height="56" rx="6"/>
  <text x="390" y="257" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">Algae (water)</text>
  <text x="390" y="275" text-anchor="middle" fill="currentColor" stroke="none">slowed by depth, life 500</text>
  <line x1="390" y1="106" x2="390" y2="140" marker-end="url(#arr)"/>
  <text x="398" y="127" fill="currentColor" stroke="none">shade</text>

  <line x1="160" y1="180" x2="288" y2="82" marker-end="url(#arr)"/>
  <line x1="160" y1="190" x2="288" y2="170" marker-end="url(#arr)"/>
  <line x1="160" y1="200" x2="288" y2="260" marker-end="url(#arr)"/>
  <text x="224" y="208" text-anchor="middle" fill="currentColor" stroke="none">grows</text>

  <rect x="600" y="100" width="140" height="56" rx="6"/>
  <text x="670" y="124" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">Litter</text>
  <text x="670" y="142" text-anchor="middle" fill="currentColor" stroke="none">rots by warmth x water</text>
  <line x1="490" y1="78" x2="598" y2="118" marker-end="url(#arr)"/>
  <line x1="490" y1="170" x2="598" y2="138" marker-end="url(#arr)"/>
  <text x="545" y="131" text-anchor="middle" fill="currentColor" stroke="none">dies</text>

  <rect x="600" y="220" width="140" height="56" rx="6"/>
  <text x="670" y="244" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">Fire</text>
  <text x="670" y="262" text-anchor="middle" fill="currentColor" stroke="none">dry, over 5 C, fuel</text>
  <line x1="670" y1="156" x2="670" y2="218" marker-end="url(#arr)"/>
  <text x="678" y="192" fill="currentColor" stroke="none">fuel</text>

  <rect x="600" y="296" width="140" height="44" rx="6"/>
  <text x="670" y="323" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">Air</text>
  <line x1="670" y1="276" x2="670" y2="294" marker-end="url(#arr)"/>
  <text x="678" y="290" fill="currentColor" stroke="none">half</text>
  <polyline points="600,332 90,332 90,222" marker-end="url(#arr)"/>
  <text x="400" y="322" text-anchor="middle" fill="currentColor" stroke="none">falls by the share of the rain</text>
  <polyline points="670,100 670,28 90,28 90,158" marker-end="url(#arr)"/>
  <text x="380" y="20" text-anchor="middle" fill="currentColor" stroke="none">rots</text>
  <path d="M290,270 C220,280 160,250 130,222" marker-end="url(#arr)"/>
  <text x="215" y="302" text-anchor="middle" fill="currentColor" stroke="none">dies, sinks</text>
</g>
</svg>
<figcaption>Figure 1. The laws of stage B, every 10 steps on each cell. Matter is only moved. A producer grows by light x warmth x water x cover. The two outlined producers differ in one material fact: most of a tree is trunk, so wood needs forty times the stand of grass to take half the light, and in return it shades the grass under it.</figcaption>
</figure>
"""


def main():
    rows = load_rows("results/search/c*_row.csv")
    lines = [("each holds 5% of the plant matter", "pass_share"), ("each the larger part of a habitat", "pass_larger"),
             ("none under 1% at a year's end", "pass_alive"), ("fire burns 1-20% of the land a year", "pass_fire"),
             ("matter conserved", "pass_matter"), ("all five", "pass")]
    head = "".join(f"<th>{w}<br>{WORLD_NAME[w]}</th>" for w in WORLDS) + "<th>all (96)</th>"
    body = ""
    for name, key in lines:
        cells = "".join(f"<td>{int(sum(r[key] for r in rows if r['world'] == w))}</td>" for w in WORLDS)
        strong = ("<strong>", "</strong>") if key == "pass" else ("", "")
        body += f"<tr><td>{strong[0]}{name}{strong[1]}</td>{cells}<td>{strong[0]}{int(sum(r[key] for r in rows))}{strong[1]}</td></tr>"

    grass_part = lambda r: r["share_grass"] / max(1e-9, r["share_grass"] + r["share_wood"])
    pct = lambda y, _p: f"{y:.0%}"
    c_split = scatter_by_world(
        rows, lambda r: r["need_wood"] / r["need_grass"], grass_part, "wood's need over grass's (log)", pct,
        "Who holds the land follows the ratio of needs",
        "Grass's part of the land's standing plant matter against how much better ground wood needs. A flat cloud would mean the rates do not decide it.",
        xlog=True)
    c_fire = scatter_by_world(
        rows, lambda r: r["ignite"], lambda r: max(r["burnt"], 1e-4), "chance a strike hits a cell in an update (log)",
        lambda y, _p: f"{y * 100:g}%",
        "Lightning sets the land burnt, except where fuel is continuous",
        "Land burnt a year against the strike chance, both log (none drawn at 0.01%). Slope 1: each fire burns the same patch. Band: the pass line.",
        xlog=True, ylog=True, band=(0.01, 0.20))
    c_matter = scatter_by_world(
        rows, lambda r: r["burnt"], lambda r: r["land_matter"], "land burnt a year", pct,
        "The more that burns, the more matter the land loses",
        "The land's matter at the end over the start, against the land burnt a year. The dashed line is 95%.",
        hline=0.95, xfmt=pct)
    s_dry = shares_over_years(os.path.join(HERE, "results/pilot/c1173_years.csv"), "In the hot dry world, wood dies out",
                              "Shares of the standing plant matter in c1173 at the defaults. The wood band thinning to nothing is an extinction.")
    s_pass = shares_over_years(os.path.join(HERE, "results/search/c1236_d11_years.csv"), "In a passing world the shares settle",
                               "The cool world c1236 with draw d11. Flat bands mean each producer holds its part year to year.")
    map_pilot = producer_map(os.path.join(HERE, "results/pilot/c1221_maps.bin"), "Where each producer stands: the mild world at the defaults",
                             "c1221: wood holds the rainy belt, grass its drier margins, the dry interior is bare. Burnt patches are diamonds: a fire spreads to four neighbours.")
    pass_maps = os.path.join(HERE, "results/pass/c1225_d11_maps.bin")
    map_pass = producer_map(pass_maps, "The very wet world with draw d11, which passes",
                            "c1225: grass is the larger part of five habitats and wood of one; algae hold the warm seas.") if os.path.exists(pass_maps) else ""

    passes = "".join(
        f"<tr><td>{r['id']}</td><td>{r['share_grass']:.2f} / {r['share_wood']:.2f} / {r['share_algae']:.2f}</td>"
        f"<td>{r['larger_grass']:.0f} / {r['larger_wood']:.0f} / {r['larger_algae']:.0f}</td><td>{r['burnt']:.1%}</td>"
        f"<td>{r['land_matter']:.1%}</td><td>{r['drift_wood']:.2f}</td></tr>"
        for r in rows if r["pass"])
    draws = ""
    for d in range(16):
        sel = [r for r in rows if r["id"].endswith(f"_d{d:02d}")]
        r0 = sel[0]
        draws += (f"<tr><td>d{d:02d}</td><td>{r0['grass_rate']:.4f}</td><td>{r0['wood_rate']:.5f}</td><td>{r0['algae_rate']:.4f}</td>"
                  f"<td>{r0['ignite']:.1e}</td><td>{r0['need_wood'] / r0['need_grass']:.1f}</td><td>{int(sum(r['pass'] for r in sel))}</td></tr>")

    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>e062 The producers - Report</title>
<style>{CSS}</style>
</head>
<body>
<main>
<h1>e062: Do grass, wood and algae each hold a place of their own?</h1>
<p class="sub">Experiment report - 2026-09-13 - foundation stage B (#75): three pilots and 96 candidates on six stage-A worlds, no bodies</p>

<section class="tldr">
<h2>TL;DR</h2>
<p>Sometimes. Of 96 candidates (16 draws of growth rates and lightning on six climates), 9 pass every
line of stage B, on four worlds, and no draw passes on more than two. Algae always hold the water;
grass and wood split the land only when wood needs 3-12 times the ground grass needs. The hot dry world
loses its wood and the cold world never burns. Stage C takes one draw, d11, on the very wet and the cool world.</p>
</section>

<h2>1. Question</h2>
<p>A consumer can only specialise on foods that differ. Before any body lives here, do several
producers hold places of their own on a stage-A world, and last? Grass, wood and algae share one
growth law and differ in material facts: most of a tree is trunk, and algae live in water.</p>
<ol>
  <li><strong>Each producer holds 5% of the plant matter and wins a habitat</strong> on most of six worlds.</li>
  <li><strong>Fire's reach follows the fuel's regrowth</strong> more than the lightning.</li>
  <li><strong>The land keeps 95% of its matter.</strong></li>
  <li><strong>A candidate takes under 10 minutes</strong> at 512 on one core.</li>
</ol>

<h2>2. The world</h2>
<p>e061's climate, unchanged, on six of its passing worlds, from hot and wet to cold. Every 10 steps each
cell grows its producers out of its soil by light, warmth and water, and loses them to death, rot and
fire on dry ground; the smoke falls with the rain (Figure 1).</p>
{DIAGRAM}
<p><strong>Runs.</strong> The climate is spun up for 20,000 updates, then the producers run for at least
10 years and 200,000 steps. Pilots at the defaults on three worlds, then 16 Latin-hypercube draws of the
three growth rates and the strike chance, each on all six worlds.</p>
<ul class="measures">
  <li><strong>share</strong> - a producer's part of the world's standing plant matter, last year.</li>
  <li><strong>larger part</strong> - habitats (2% of the cells, a tenth of the mean plant matter) where a producer is half the standing matter.</li>
  <li><strong>alive</strong> - its least share at the end of any year.</li>
  <li><strong>burnt</strong> - land burnt a year, second half of the run.</li>
  <li><strong>land matter</strong> - the land's matter at the end over the start.</li>
  <li><strong>need</strong> - half / (rate x life): the least light x warmth x water a producer stands on.</li>
</ul>

<h2>3. Results</h2>
<div class="tw"><table>
<thead><tr><th>Pass line (of 16 a world)</th>{head}</tr></thead>
<tbody>{body}</tbody></table></div>
<ol class="verdicts">
<li><span class="verdict no">No</span> 9 of 96 candidates pass, on 4 of 6 worlds; no draw passes on more than 2.</li>
<li><span class="verdict partly">Partly</span> Big fires only in the hot wet and the cool world (slopes 0.24 and 0.34); elsewhere the land burnt follows the lightning.</li>
<li><span class="verdict partly">Mostly</span> 84 of 96 keep 95%; the loss follows the land burnt (rank -0.92), up to 1.2% a year.</li>
<li><span class="verdict">Yes</span> 8.1 minutes a candidate on the Mac, nine at once.</li>
</ol>

<h3>3.1 Algae hold the water; the ratio of needs splits the land</h3>
<div class="grid2">{c_split}</div>
<p>Grass's part of the land follows how much better ground wood needs than grass (rank 0.90). Under a
ratio of about 3, wood fills every habitat it can stand in; over about 12, grass takes the land and wood
keeps the wettest belt. Both win a habitat in 25 candidates, all between 2.6 and 12.3. Algae were the
larger part of a water habitat in all 96.</p>
{map_pilot}
{map_pass}

<h3>3.2 The worlds at the ends fail for their own reasons</h3>
<div class="grid2">{s_dry}{s_pass}</div>
<p>In the hot dry world wood falls under 1% in 12 of 16 draws. In the hot wet world wood holds the wet
land and the dry land is nearly bare, so grass wins no habitat with enough matter in 12 of 16. The
cold world burns under 1% of its land in every draw.</p>

<h3>3.3 Fire burns too little, and its smoke drains the land</h3>
<div class="grid2">{c_fire}{c_matter}</div>
<p>All 58 fire failures burn under 1%; no candidate burns more than 11% a year. On four worlds each
fire stays a patch of hundreds of cells, so the land burnt follows the lightning. Where dry fuel is
continuous in the dry season, one fire burns up to 27,128 cells. Half of what burns goes to the air,
which rains mostly on the sea.</p>

<h2>4. Discussion</h2>
<p>The band is narrow, and it moves with the world. The same draw passes the very wet and the cool
world and fails the mild one, where wood's ground is rarer. Laws are the same in every world, so stage
C takes one draw and the worlds it passes, not the best draw for each world.</p>
<p>Two things will matter in longer runs. The smoke moves matter from the land to the sea and nothing
brings it back. And wood is not settled in every run: in two passing candidates it rose 30-33% between
the middle and the last year.</p>
<p>What this does not show. The answers hold for our choices: one growth form, warmth from 5 to 20 C,
water as the ground's fill, seeds from four neighbours, fire only on ground under a third full, plants
that change neither water nor air, ten years, six worlds, and pass lines that reject a cold world for
not burning.</p>

<h2>5. Conclusion and next step</h2>
<p>Stage B passes on 4 of 6 worlds, in 9 of 96 candidates. Stage C (#76) starts from draw d11 (grass
0.010, wood 0.0017, algae 0.0091, lightning 1.6e-6) on the very wet world c1225 and the cool world c1236,
where wood is settled and the land keeps 97-99% of its matter. Before runs longer than stage C's, the
land needs a way to get matter back from the sea.</p>

<h2>Appendix: data</h2>
<details><summary>The nine passing candidates</summary><div class="tw"><table>
<thead><tr><th>candidate</th><th>share grass / wood / algae</th><th>larger part (habitats)</th><th>burnt a year</th><th>land matter kept</th><th>wood, last year over middle</th></tr></thead>
<tbody>{passes}</tbody></table></div></details>
<details><summary>The 16 draws</summary><div class="tw"><table>
<thead><tr><th>draw</th><th>grass rate</th><th>wood rate</th><th>algae rate</th><th>strike chance</th><th>wood's need over grass's</th><th>worlds passed</th></tr></thead>
<tbody>{draws}</tbody></table></div></details>
<p>Every candidate is one row of <code>results/search/c*_d*_row.csv</code> (parameters, then measures) with a row a year in
<code>c*_d*_years.csv</code>; the pilots are in <code>results/pilot/</code>. The maps are not committed (see the README).
Build this report with <code>uv run python experiments/e062_producers/report.py</code>.</p>
</main>
</body>
</html>
"""
    out = os.path.join(HERE, "report.html")
    with open(out, "w") as f:
        f.write(page)
    print(f"wrote {out} ({os.path.getsize(out)//1024} KB)")


if __name__ == "__main__":
    main()
