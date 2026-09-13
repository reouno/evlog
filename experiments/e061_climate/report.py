#!/usr/bin/env python3
"""Build report.html for e061 (foundation stage A, #74).

Charts: matplotlib, exported as SVG and inlined. Diagram: hand-written SVG.
Run from the repo root: uv run python experiments/e061_climate/report.py
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
from matplotlib.colors import ListedColormap
from matplotlib.patches import Patch
from matplotlib.ticker import MaxNLocator

matplotlib.use("svg")

HERE = os.path.dirname(os.path.abspath(__file__))
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4"]  # fixed slot order
PASS_ID = "c1221"  # a passing world with a mild mean, 11 habitats and 3 wide ones on land

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

HABITATS = ["land cold dry", "land cold moist", "land cold wet", "land mild dry", "land mild moist", "land mild wet",
            "land hot dry", "land hot moist", "land hot wet", "shallow cold", "shallow mild", "shallow hot",
            "deep cold", "deep mild", "deep hot"]
HAB_COLORS = ["#c9b27c", "#8fae6b", "#3f7f4f", "#e0c068", "#9cc255", "#2e9e4f", "#e8a33c", "#b7c93a", "#138a3a",
              "#9fd3e8", "#5fc0d8", "#3fb0b8", "#3f6fa8", "#2f5a98", "#1f4a88"]


# ---------- data ----------

def load_rows(pattern):
    out = []
    for f in sorted(glob.glob(os.path.join(HERE, pattern))):
        with open(f) as fh:
            r = next(csv.DictReader(fh))
        d = {k: float(v) for k, v in r.items()}
        d["id"] = os.path.basename(f).split("_")[0]
        d["updates_per_year"] = d["year"] / d["tick"]
        d["lat_span"] = d["lat_hi"] - d["lat_lo"]
        out.append(d)
    return out


def load_maps(path):
    """The last year's four quarters: habitat, mean temperature, mean fill, rain; and the elevation."""
    b = open(path, "rb").read()
    n = int(np.frombuffer(b[4:8], "<u4")[0])
    cells, o = n * n, 8
    elev = np.frombuffer(b[o:o + 4 * cells], "<f4").reshape(n, n)
    o += 4 * cells
    quarters = []
    for _ in range(4):
        hab = np.frombuffer(b[o:o + cells], "u1").reshape(n, n)
        o += cells
        t = np.frombuffer(b[o:o + 4 * cells], "<f4").reshape(n, n)
        o += 4 * cells
        m = np.frombuffer(b[o:o + 4 * cells], "<f4").reshape(n, n)
        o += 4 * cells
        r = np.frombuffer(b[o:o + 4 * cells], "<f4").reshape(n, n)
        o += 4 * cells
        quarters.append((hab, t, m, r))
    return elev, quarters


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


def figure(title, subtitle, svg):
    return f"""
<figure class="fig">
  <figcaption><strong>{html.escape(title)}</strong><span>{html.escape(subtitle)}</span></figcaption>
  {svg}
</figure>"""


def wide_by_grain(rows):
    fig, ax = plt.subplots(figsize=(6.4, 2.6))
    bins = [(32, 64), (64, 128), (128, 257)]
    labels = ["32-64", "64-128", "128-256"]
    width = 0.38
    for k, size in enumerate((256, 512)):
        rates = []
        for lo, hi in bins:
            sel = [r for r in rows if r["size"] == size and lo <= r["grain"] < hi]
            rates.append(sum(r["pass_wide"] for r in sel) / max(1, len(sel)))
        xs = [i + (k - 0.5) * width for i in range(len(bins))]
        ax.bar(xs, rates, width * 0.92, color=SERIES[k], label=f"{size} x {size}")
    ax.set_xticks(range(len(bins)), labels)
    ax.set_xlabel("grain: the widest feature of the terrain (cells)", loc="right")
    ax.set_ylim(0, 1)
    ax.yaxis.set_major_formatter(lambda y, _p: f"{y:.0%}")
    ax.yaxis.set_major_locator(MaxNLocator(4))
    legend_above(ax, 2)
    return figure("Width is bought by the size of the world and of its continents",
                  "Share of candidates with 3 habitats in patches 42 cells wide. Equal bars would mean neither matters.",
                  to_svg(fig))


def change_by_tilt(rows):
    fig, ax = plt.subplots(figsize=(6.4, 2.6))
    ax.axhspan(0.10, 0.50, color=SERIES[2], alpha=0.12, linewidth=0)
    ax.scatter([r["tilt"] for r in rows], [r["change"] for r in rows], s=9, color=SERIES[0], linewidths=0)
    ax.set_xlabel("tilt of the axis (degrees)", loc="right")
    ax.set_ylim(0, 1)
    ax.yaxis.set_major_formatter(lambda y, _p: f"{y:.0%}")
    ax.yaxis.set_major_locator(MaxNLocator(4))
    return figure("The tilt sets how much of the world changes in a year",
                  "Share of cells whose habitat is not the same in all four quarters; the band is the pass line (10-50%).",
                  to_svg(fig))


def stand_by_updates(rows, spin):
    fig, ax = plt.subplots(figsize=(6.4, 2.6))
    ax.axhline(0.90, color=INK, linewidth=0.8, linestyle="--")
    ax.scatter([r["updates_per_year"] for r in rows], [r["stand"] for r in rows], s=9, color=SERIES[0], linewidths=0, label="20 years")
    if spin:
        ax.scatter([r["updates_per_year"] for r in spin], [r["stand"] for r in spin], s=22, color=SERIES[1], linewidths=0, label="80 years (reruns)")
    ax.set_xscale("log")
    ax.set_xlabel("climate updates in a year (10 steps each)", loc="right")
    ax.xaxis.set_major_locator(matplotlib.ticker.FixedLocator([300, 600, 1000, 2000, 3000]))
    ax.xaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
    ax.xaxis.set_major_formatter(kfmt)
    ax.yaxis.set_major_locator(MaxNLocator(4))
    legend_above(ax, 2)
    return figure("What does not stand is still spinning up",
                  "Agreement of the last year's habitat maps with the middle year's; the dashed line is the pass line (90%).",
                  to_svg(fig))


def habitat_maps(path, title, subtitle):
    _, quarters = load_maps(path)
    cmap = ListedColormap(HAB_COLORS)
    fig, axes = plt.subplots(1, 4, figsize=(9.6, 2.7))
    fig.subplots_adjust(left=0.01, right=0.99, top=0.92, bottom=0.02, wspace=0.06)
    for q, ax in enumerate(axes):
        ax.imshow(quarters[q][0], cmap=cmap, vmin=-0.5, vmax=14.5, interpolation="nearest")
        ax.set_title(f"quarter {q + 1}", fontsize=9)
        ax.set_xticks([])
        ax.set_yticks([])
        ax.grid(False)
        for s in ax.spines.values():
            s.set_visible(False)
    handles = [Patch(color=c, label=h) for c, h in zip(HAB_COLORS, HABITATS)]
    fig.legend(handles=handles, loc="upper center", ncols=5, fontsize=8, bbox_to_anchor=(0.5, 0.0), handlelength=1.0, columnspacing=1.0)
    return f"""
<figure class="fig wide">
  <figcaption><strong>{html.escape(title)}</strong><span>{html.escape(subtitle)}</span></figcaption>
  {to_svg(fig)}
</figure>"""


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
<svg viewBox="0 0 760 320" role="img" aria-label="The sun heats the cells, the air takes up water by temperature and rains it on the ground, the wind moves the air, and each quarter a cell's habitat is read from its temperature, its water and its medium." style="max-width:100%;height:auto;display:block">
<defs><marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="currentColor"/></marker></defs>
<g fill="none" stroke="currentColor" stroke-width="1.2" font-size="12" font-family="system-ui, sans-serif">
  <rect x="20" y="30" width="150" height="56" rx="6"/>
  <text x="95" y="54" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">Sun</text>
  <text x="95" y="72" text-anchor="middle" fill="currentColor" stroke="none">day x year x latitude</text>

  <rect x="250" y="30" width="210" height="56" rx="6"/>
  <text x="355" y="54" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">Temperature</text>
  <text x="355" y="72" text-anchor="middle" fill="currentColor" stroke="none">-6.5 C a km; the sea 200x slower</text>
  <line x1="170" y1="58" x2="248" y2="58" marker-end="url(#arr)"/>
  <text x="209" y="50" text-anchor="middle" fill="currentColor" stroke="none">light</text>

  <rect x="250" y="165" width="210" height="74" rx="6"/>
  <text x="355" y="187" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">Air (water vapour)</text>
  <text x="355" y="205" text-anchor="middle" fill="currentColor" stroke="none">25 mm at 20 C, more when warm</text>
  <text x="355" y="223" text-anchor="middle" fill="currentColor" stroke="none">moved by one wind that turns</text>
  <line x1="355" y1="86" x2="355" y2="163" marker-end="url(#arr)"/>
  <text x="363" y="130" fill="currentColor" stroke="none">what it can hold</text>

  <rect x="20" y="175" width="150" height="56" rx="6"/>
  <text x="95" y="199" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">Sea</text>
  <text x="95" y="217" text-anchor="middle" fill="currentColor" stroke="none">below the sea level</text>
  <line x1="170" y1="195" x2="248" y2="195" marker-end="url(#arr)"/>
  <text x="209" y="187" text-anchor="middle" fill="currentColor" stroke="none">evaporation</text>

  <rect x="560" y="175" width="180" height="56" rx="6"/>
  <text x="650" y="199" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">Ground water</text>
  <text x="650" y="217" text-anchor="middle" fill="currentColor" stroke="none">holds 150 mm, the rest runs</text>
  <line x1="460" y1="195" x2="558" y2="195" marker-end="url(#arr)"/>
  <text x="510" y="187" text-anchor="middle" fill="currentColor" stroke="none">rain over 80%</text>
  <line x1="558" y1="218" x2="462" y2="218" marker-end="url(#arr)"/>
  <text x="510" y="236" text-anchor="middle" fill="currentColor" stroke="none">evaporation</text>
  <path d="M650,231 C650,300 95,300 95,233" marker-end="url(#arr)"/>
  <text x="372" y="305" text-anchor="middle" fill="currentColor" stroke="none">standing water runs downhill to the sea</text>

  <rect x="560" y="22" width="180" height="72" rx="6" stroke="var(--s1)" stroke-width="2"/>
  <text x="650" y="46" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">Habitat, each quarter</text>
  <text x="650" y="64" text-anchor="middle" fill="currentColor" stroke="none">medium x temperature band</text>
  <text x="650" y="80" text-anchor="middle" fill="currentColor" stroke="none">x moisture band (land)</text>
  <line x1="460" y1="58" x2="558" y2="58" marker-end="url(#arr)"/>
  <text x="510" y="50" text-anchor="middle" fill="currentColor" stroke="none">5 C / 20 C</text>
  <line x1="650" y1="173" x2="650" y2="96" marker-end="url(#arr)"/>
  <text x="658" y="138" fill="currentColor" stroke="none">1/3, 2/3 full</text>
</g>
</svg>
<figcaption>Figure 1. The laws of stage A. Every 10 steps each cell goes toward the temperature its light and height give; its air takes up water from the sea or the wet ground and rains what it cannot hold, so it rains where air rises (a colder, higher cell) or cools. The wind moves the air. A habitat is read from the quarter's means.</figcaption>
</figure>
"""


def main():
    rows = load_rows("results/search/c*_row.csv")
    spin = load_rows("results/spinup/c*_row.csv")
    pilot = load_rows("results/pilot/default_row.csv")[0]
    by_id = {r["id"]: r for r in rows}

    def rate(sel, key):
        return sum(r[key] for r in sel) / max(1, len(sel))

    groups = [("256 x 256", [r for r in rows if r["size"] == 256]), ("512 x 512", [r for r in rows if r["size"] == 512]), ("all", rows)]
    lines = [("5 habitats of 2%", "pass_share"), ("3 of them 42 cells wide", "pass_wide"), ("10-50% change in a year", "pass_change"),
             ("year 20 agrees with year 10 on 90%", "pass_stand"), ("all four", "pass")]
    table_rows = "".join(
        f"<tr><td>{name}</td>" + "".join(f"<td>{int(sum(r[key] for r in sel))} ({rate(sel, key):.0%})</td>" for _, sel in groups) + "</tr>"
        for name, key in lines)
    counts = "".join(f"<th>{g} (n={len(sel)})</th>" for g, sel in groups)

    rho = {a: {m: spearman([r[a] for r in rows], [r[m] for r in rows]) for m in ("wide", "change", "stand")}
           for a in ("size", "grain", "tilt", "land", "updates_per_year")}

    charts_width = [wide_by_grain(rows)]
    charts_time = [change_by_tilt(rows), stand_by_updates(rows, spin)]
    maps_default = habitat_maps(os.path.join(HERE, "results/pilot/default_maps.bin"),
                                "The default world (256 x 256) through its last year",
                                "Rows run from 60 S (top and bottom) to 60 N (middle); the wind blows east. 12 habitats, and only the deep hot sea is 42 cells wide.") \
        if os.path.exists(os.path.join(HERE, "results/pilot/default_maps.bin")) else ""
    maps_pass = ""
    if PASS_ID and os.path.exists(os.path.join(HERE, f"results/pass/{PASS_ID}_maps.bin")):
        maps_pass = habitat_maps(os.path.join(HERE, f"results/pass/{PASS_ID}_maps.bin"), f"A world that passes all four lines ({PASS_ID})",
                                 "512 cells, terrain grain 154, 41% land, latitude 82 S to 71 N, tilt 14: 11 habitats, 6 of them wide, 3 on land.")

    spin_rows = "".join(
        f"<tr><td>{r['id']}</td><td>{r['size']:.0f}</td><td>{r['updates_per_year']:.0f}</td><td>{by_id[r['id']]['stand']:.3f}</td><td>{r['stand']:.3f}</td></tr>"
        for r in spin if r["id"] in by_id)

    appendix = "".join(
        f"<tr><td>{r['id']}</td><td>{r['size']:.0f}</td><td>{r['grain']:.0f}</td><td>{r['land']:.2f}</td><td>{r['tilt']:.0f}</td><td>{r['updates_per_year']:.0f}</td>"
        f"<td>{r['habitats']:.0f}</td><td>{r['wide']:.0f}</td><td>{r['wide_land']:.0f}</td><td>{r['change']:.2f}</td><td>{r['stand']:.3f}</td></tr>"
        for r in rows if r["pass"])

    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>e061 The climate - Report</title>
<style>{CSS}</style>
</head>
<body>
<main>
<h1>e061: Does the climate alone make places a body can tell apart?</h1>
<p class="sub">Experiment report - 2026-09-13 - foundation stage A (#74): a default world and a search of {len(rows)} candidates, 20 years each, no plants, no bodies</p>

<section class="tldr">
<h2>TL;DR</h2>
<p>The climate alone makes places. Of 300 generated worlds, 294 hold at least five habitats of 2%, and
34 pass all four lines of stage A: enough habitats, three of them wider than three lives of travel,
10-50% changing in a year, and a map that stands. 30 of the 34 are 512 cells wide, so the world is 512
from here. Next, stage B puts producers on these worlds, on a slow clock: per cell per step, a 512
world is too slow to search.</p>
</section>

<h2>1. Question</h2>
<p>Before anything lives on it, does the physical world make places a body can tell apart: wide
enough that a body cannot average them away, changing with the seasons, and not drifting? This is
the cheapest layer of the foundation, so it is searched widely, and it decides the world's size.</p>
<ol>
  <li><strong>At Earth-like ratios the laws make 5 habitats of 2%,</strong> without tuning.</li>
  <li><strong>The width line decides the size:</strong> 256 fails it, 512 passes.</li>
  <li><strong>The tilt sets the change.</strong></li>
  <li><strong>The map stands,</strong> except where lakes are still filling.</li>
</ol>

<h2>2. The world</h2>
<p>A torus with generated terrain and sea; its rows run from one latitude to another and back. Every
10 steps the sun heats each cell, the air takes up water by temperature, the wind carries it, and it
rains where the air cannot hold it. Each quarter a cell's habitat is read (Figure 1).</p>
{DIAGRAM}
<p><strong>Runs.</strong> The default world (256, 20 years), then a Latin hypercube of 300 candidates
over 14 axes (size 256 or 512, terrain grain, land share, relief, latitude, day, year, sun, tilt, land
response, wind, its turn, rain), 20 years each. Seven that did not stand were rerun for 80 years.</p>
<ul class="measures">
  <li><strong>habitats</strong> - of 15, those holding 2% of the cells over the last year.</li>
  <li><strong>wide</strong> - habitats whose median cell lies in a patch 42 cells wide (the largest square inside it).</li>
  <li><strong>change</strong> - cells whose habitat is not the same in all four quarters.</li>
  <li><strong>stand</strong> - agreement of the last year's four maps with the middle year's.</li>
</ul>

<h2>3. Results</h2>
<div class="tw"><table>
<thead><tr><th>Pass line</th>{counts}</tr></thead>
<tbody>{table_rows}</tbody></table></div>
<ol class="verdicts">
<li><span class="verdict">Yes</span> 294 of 300 worlds hold 5 or more habitats of 2%; the default world holds 12.</li>
<li><span class="verdict">Yes</span> 90 of 150 worlds of 512 pass the width line, 24 of 150 of 256; the terrain's grain matters as much as the size.</li>
<li><span class="verdict">Yes</span> Change follows the tilt (rank correlation 0.66); 95 of 134 worlds tilted 10-30 degrees pass.</li>
<li><span class="verdict no">No</span> Lakes are not the cause: a short year fails to stand, and all 7 reruns stand at 80 years.</li>
</ol>

{maps_default}

<h3>3.1 Width is bought by size and continents</h3>
<div class="grid2">{"".join(charts_width)}</div>
<p>The wide habitats are the deep sea and dry land. A wet or moist land habitat is wide in at most 8
worlds of 300: the rain falls on windward coasts and in belts, so wet land comes in strips. Only at 512
with continents about 128 cells or wider does land hold several habitats a body cannot cross in a life.</p>

<h3>3.2 The tilt sets the change; a short year only needs longer to settle</h3>
<div class="grid2">{"".join(charts_time)}</div>
<p>Change fails by excess four times as often as by lack (100 against 25): a strong tilt moves most
cells across a temperature band every year. Stand is not drift. It follows the climate updates run,
not the years: with 1,000 updates a year or more, 141 of 144 stand. The sea and the ground water need
10,000-20,000 updates to settle.</p>
{maps_pass}

<h2>4. Discussion</h2>
<p>The day's length, the rain rate, the wind speed, the relief and the sun's strength hardly change
whether a world passes (each 0.13 or less). They change what it is like: passing worlds run from -6 C
to 31 C on land and from 26 to 3,700 mm of rain a year. The lines count places; they do not ask for a
mild world. Stage B will, through what grows.</p>
<p>The widths matter for stage C too. The wide land is dry land. Wet land is a coast or a belt a few
cells wide, so a law about wet and dry ground will be felt by bodies near a coast and averaged away by
the rest, unless bodies travel less than the 14 cells assumed here.</p>
<p>What this does not show: the habitats come from our thresholds (5 and 20 C, a third and two thirds
of the ground's fill) and quarter means; the sea's depth follows the land's relief, so a low relief
makes a shallow sea; there is no ice, snow or erosion.</p>

<h2>5. Conclusion and next step</h2>
<p>Stage A passes. The world is 512 with continents of about 128 cells or more, a tilt of 10-30
degrees, and a spin-up of about 20,000 climate updates before anything is judged. The 34 passing worlds
are stage B's starting set. Its first problem is compute: e059's world cost 3 ms a step at 128, which
is 48 ms at 512, so the producers go on a slow clock like the climate.</p>

<h2>Appendix: data</h2>
<details><summary>The candidates that pass all four lines</summary><div class="tw"><table>
<thead><tr><th>id</th><th>size</th><th>grain</th><th>land</th><th>tilt</th><th>updates a year</th><th>habitats</th><th>wide</th><th>wide on land</th><th>change</th><th>stand</th></tr></thead>
<tbody>{appendix}</tbody></table></div></details>
<details><summary>The 80-year reruns</summary><div class="tw"><table>
<thead><tr><th>id</th><th>size</th><th>updates a year</th><th>stand at 20 years</th><th>stand at 80 years</th></tr></thead>
<tbody>{spin_rows}</tbody></table></div></details>
<p>Rank correlations with the measures: {html.escape(str({a: {m: round(v, 2) for m, v in d.items()} for a, d in rho.items()}))}.
Every candidate is one row of <code>results/search/c*_row.csv</code> (parameters, then measures) with a row a year in <code>c*_years.csv</code>.
Build this report with <code>uv run python experiments/e061_climate/report.py</code>.</p>
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
