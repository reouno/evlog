#!/usr/bin/env python3
"""Build report.html for this experiment.

Charts: matplotlib, exported as SVG and inlined. Diagram: hand-written SVG.
Run from the repo root: uv run python experiments/e086_year/months.py, then uv run python experiments/e086_year/report.py
"""
import csv
import html
import io
import os

import matplotlib
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator

matplotlib.use("svg")

HERE = os.path.dirname(os.path.abspath(__file__))
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4"]  # fixed slot order

# Chart chrome that reads on both light and dark backgrounds.
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


# ---------- data ----------

def load_csv(path):
    """Read a CSV of numbers into {column: [floats]}."""
    with open(os.path.join(HERE, path)) as f:
        rows = list(csv.DictReader(f))
    return {k: [float(r[k]) for r in rows] for k in rows[0]}


# ---------- chart helpers ----------

def kfmt(x, _pos):
    return f"{x/1000:g}k" if abs(x) >= 1000 else f"{x:g}"


def to_svg(fig):
    buf = io.StringIO()
    fig.savefig(buf, format="svg", bbox_inches="tight", pad_inches=0.05)
    plt.close(fig)
    return buf.getvalue()


def new_axes(xlabel="step"):
    fig, ax = plt.subplots(figsize=(6.4, 2.6))
    ax.xaxis.set_major_formatter(kfmt)
    ax.set_xlabel(xlabel, loc="right")
    ax.margins(x=0)
    return fig, ax


def hist_chart(title, subtitle, series, bins, xlabel, density=False):
    """series: list of (label, values, slot). Overlapping histograms with a surface gap."""
    fig, ax = new_axes(xlabel)
    ax.margins(x=0.02)
    for label, values, slot in series:
        ax.hist(values, bins=bins, color=SERIES[slot], alpha=0.75, label=label, density=density,
                edgecolor="none", rwidth=0.9 if len(series) == 1 else 1.0)
    ax.yaxis.set_major_locator(MaxNLocator(4))
    ax.yaxis.set_major_formatter(kfmt)
    if density:
        ax.set_yticklabels([])  # heights are relative; the numbers mean nothing to a reader
    legend_above(ax, len(series))
    return figure(title, subtitle, to_svg(fig))


def legend_above(ax, n):
    ax.legend(loc="lower left", bbox_to_anchor=(0, 1.0), ncols=n, handlelength=1.2, borderaxespad=0, columnspacing=1.2)


def line_chart(title, subtitle, xs, series, ymin=None):
    """series: list of (label, ys, slot)."""
    fig, ax = new_axes()
    for label, ys, slot in series:
        ax.plot(xs, ys, color=SERIES[slot], linewidth=1.6, label=label)
    if ymin is not None:
        ax.set_ylim(ymin, max(v for _, ys, _ in series for v in ys) * 1.12)
    ax.yaxis.set_major_formatter(kfmt)
    ax.yaxis.set_major_locator(MaxNLocator(4))
    legend_above(ax, len(series))
    return figure(title, subtitle, to_svg(fig))


def stacked_area(title, subtitle, xs, layers):
    """layers: list of (label, ys, slot); fractions summing to ~1."""
    fig, ax = new_axes()
    ax.stackplot(xs, [ys for _, ys, _ in layers], labels=[l for l, _, _ in layers],
                 colors=[SERIES[s] for _, _, s in layers], linewidth=0)
    ax.set_ylim(0, 1)
    ax.yaxis.set_major_formatter(lambda y, _p: f"{y:.0%}")
    ax.yaxis.set_major_locator(MaxNLocator(4))
    legend_above(ax, len(layers))
    return figure(title, subtitle, to_svg(fig))


def figure(title, subtitle, svg):
    return f"""
<figure class="fig">
  <figcaption><strong>{html.escape(title)}</strong><span>{html.escape(subtitle)}</span></figcaption>
  {svg}
</figure>"""


def data_table(cols, rows_by_name, every=10):
    """Collapsed tables for the appendix. rows_by_name: {name: {col: [values]}}."""
    out = []
    for name, d in rows_by_name.items():
        rows = "".join(
            "<tr>" + "".join(f"<td>{d[c][i]:g}</td>" for c in cols) + "</tr>"
            for i in range(0, len(d[cols[0]]), every)
        )
        out.append(f"<details><summary>{html.escape(name)}</summary><div class='tw'><table><thead><tr>"
                   + "".join(f"<th>{c}</th>" for c in cols) + f"</tr></thead><tbody>{rows}</tbody></table></div></details>")
    return "\n".join(out)


# ---------- page ----------

# A report is dark only (the user, 2026-09-16): one palette, no light branch.
CSS = """
:root {
  color-scheme: dark;
  --surface: #1a1a19; --page: #0d0d0d; --ink: #ffffff; --ink2: #c3c2b7; --grid: #2c2c2a; --border: rgba(255,255,255,0.10);
  --s1: #3987e5;
}
* { box-sizing: border-box; }
body { margin: 0; background: var(--page); color: var(--ink); font: 15px/1.55 system-ui, -apple-system, "Segoe UI", sans-serif; }
main { max-width: 960px; margin: 0 auto; padding: 32px 20px 64px; }
h1 { font-size: 26px; margin: 0 0 4px; }
h2 { font-size: 19px; margin: 40px 0 8px; }
h3 { font-size: 16px; margin: 24px 0 8px; }
p, li { color: var(--ink); max-width: 72ch; }
.sub { color: var(--ink2); margin: 0 0 24px; }
.tldr { background: var(--surface); border: 1px solid var(--border); border-left: 4px solid var(--s1); border-radius: 8px; padding: 12px 18px; }
.tldr h2 { margin: 0 0 6px; font-size: 15px; }
.tldr p { margin: 0; }
.grid2 { display: grid; grid-template-columns: repeat(auto-fit, minmax(420px, 1fr)); gap: 20px; }
.grid2 > .fig:only-child { max-width: 470px; }
.fig { margin: 0; background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 14px 14px 8px; }
.fig svg { width: 100%; height: auto; display: block; font-family: system-ui, -apple-system, "Segoe UI", sans-serif; }
figcaption strong { display: block; font-size: 15px; }
figcaption span { display: block; color: var(--ink2); font-size: 13px; min-height: 2.6em; margin-bottom: 6px; }
.diagram { margin: 12px 0; background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 12px 16px 8px; color: var(--ink); }
.diagram figcaption { color: var(--ink2); font-size: 13px; margin-top: 4px; }
.measures { columns: 2; column-gap: 24px; max-width: none; padding-left: 20px; } .measures li { break-inside: avoid; }
table { border-collapse: collapse; font-size: 13.5px; font-variant-numeric: tabular-nums; }
th, td { padding: 6px 12px; text-align: right; border-bottom: 1px solid var(--grid); }
th:first-child, td:first-child { text-align: left; }
th { color: var(--ink2); font-weight: 600; }
.tw { overflow-x: auto; }
details { margin: 8px 0; } summary { cursor: pointer; color: var(--ink2); }
.verdicts { list-style: none; padding: 0; margin: 12px 0 0; } .verdicts li { margin: 4px 0; }
.verdict { display: inline-block; padding: 1px 8px; border-radius: 4px; font-size: 12.5px; font-weight: 600; background: rgba(12,163,12,0.12); color: #0ca30c; }
.verdict.no { background: rgba(208,59,59,0.12); color: #e66767; }
.verdict.partly { background: rgba(250,178,25,0.15); color: #fab219; }
"""

# Hand-written mechanism diagram. Label every arrow; currentColor for lines and text;
# var(--s1) for the one element the argument hinges on. Keep 10-15px between text and lines.
DIAGRAM = """
<figure class="diagram">
<svg viewBox="0 0 720 210" role="img" aria-label="On a log scale of steps, a grown life of 500-570 steps sits beside the lean spell of 400 steps at a year of 1,200, and far below the lean spell of 3,960 steps at today's year" style="max-width:100%;height:auto;display:block">
<g fill="none" stroke="currentColor" stroke-width="1.2" font-size="12" font-family="system-ui, sans-serif">
  <line x1="40" y1="110" x2="690" y2="110"/>
  <text x="40" y="202" fill="currentColor" stroke="none">steps, log scale</text>
  <!-- the world, above the axis -->
  <text x="40" y="22" fill="currentColor" stroke="none" font-weight="600">the world</text>
  <line x1="85" y1="104" x2="85" y2="116"/>
  <text x="85" y="92" text-anchor="middle" fill="currentColor" stroke="none">day 75</text>
  <line x1="273" y1="70" x2="273" y2="116" stroke="var(--s1)" stroke-width="2"/>
  <text x="273" y="45" text-anchor="middle" fill="currentColor" stroke="none">lean spell 400</text>
  <text x="273" y="60" text-anchor="middle" fill="currentColor" stroke="none">(year 1,200)</text>
  <line x1="397" y1="80" x2="397" y2="116" stroke="var(--s1)" stroke-width="2"/>
  <text x="397" y="68" text-anchor="middle" fill="currentColor" stroke="none">year 1,200</text>
  <line x1="531" y1="70" x2="531" y2="116"/>
  <text x="531" y="45" text-anchor="middle" fill="currentColor" stroke="none">lean spell 3,960</text>
  <text x="531" y="60" text-anchor="middle" fill="currentColor" stroke="none">(year 11,880)</text>
  <line x1="654" y1="80" x2="654" y2="116"/>
  <text x="654" y="68" text-anchor="middle" fill="currentColor" stroke="none">year 11,880</text>
  <!-- a body, below the axis -->
  <text x="40" y="185" fill="currentColor" stroke="none" font-weight="600">a body</text>
  <rect x="299" y="104" width="14" height="12" fill="var(--s1)" stroke="none"/>
  <line x1="306" y1="118" x2="306" y2="140"/>
  <text x="306" y="156" text-anchor="middle" fill="currentColor" stroke="none">grown life 500-570</text>
  <line x1="85" y1="118" x2="85" y2="140"/>
  <text x="85" y="156" text-anchor="middle" fill="currentColor" stroke="none">half the dead: 75</text>
</g>
</svg>
<figcaption>Figure 1. The time scales on one log axis. Today a place's winter lasts seven grown lives; at a year of 1,200 steps it is shorter than one, and the day still fits sixteen times into the year.</figcaption>
</figure>
"""


YEARS = [11880, 2400, 1200, 600]
SLOT = {11880: 0, 2400: 1, 1200: 2, 600: 3}


def rows_by_year():
    with open(os.path.join(HERE, "results", "months.csv")) as f:
        return {int(r["year"]): r for r in csv.DictReader(f) if r["bar"] == "0.25"}


def stage_rows():
    out = {}
    for y in YEARS:
        with open(os.path.join(HERE, "results", f"c1225_d11_y{y}_row.csv")) as f:
            out[y] = next(csv.DictReader(f))
    return out


def spell_chart():
    with open(os.path.join(HERE, "results", "spells.csv")) as f:
        rows = list(csv.DictReader(f))
    fig, ax = new_axes("lean spell, steps (log)")
    for y in YEARS[:3]:
        rs = [r for r in rows if int(r["year"]) == y]
        tot = sum(int(r["cells"]) for r in rs) or 1
        xs, ys, acc = [], [], 0
        for r in rs:
            acc += int(r["cells"])
            xs.append(int(r["steps"]))
            ys.append(acc / tot)
        ax.plot(xs, ys, color=SERIES[SLOT[y]], linewidth=1.6, marker="o", markersize=3, drawstyle="steps-post", label=f"year {y:,}")
    ax.axvspan(500, 570, color=SERIES[4], alpha=0.45, linewidth=0)
    ax.text(620, 0.06, "grown life", color=INK, fontsize=9)
    ax.set_xscale("log")
    ax.xaxis.set_major_formatter(kfmt)
    ax.set_ylim(0, 1.02)
    ax.yaxis.set_major_formatter(lambda v, _p: f"{v:.0%}")
    ax.yaxis.set_major_locator(MaxNLocator(4))
    legend_above(ax, 3)
    return figure("A place's winter shortens with the year",
                  "Share of seasonal land whose longest lean spell is at most the length. Left of the band: a winter a grown body can outlive.",
                  to_svg(fig))


def dist_chart():
    with open(os.path.join(HERE, "results", "dist.csv")) as f:
        rows = list(csv.DictReader(f))
    fig, ax = new_axes("cells over land to a place fed that month")
    for y in YEARS[:3]:
        rs = sorted(((int(r["dist"]), int(r["count"])) for r in rows if int(r["year"]) == y))
        tot = sum(c for _, c in rs)
        xs, ys, acc = [], [], 0
        for d, c in rs:
            acc += c
            if d <= 80:
                xs.append(d)
                ys.append(acc / tot)
        ax.plot(xs, ys, color=SERIES[SLOT[y]], linewidth=1.6, label=f"year {y:,}")
    ax.axvline(9, color=INK, linewidth=1, linestyle="--")
    ax.text(10, 0.05, "eye's reach, 9", color=INK, fontsize=9)
    ax.set_ylim(0, 1)
    ax.yaxis.set_major_formatter(lambda v, _p: f"{v:.0%}")
    ax.yaxis.set_major_locator(MaxNLocator(4))
    legend_above(ax, 3)
    return figure("A fed place lies 9-15 cells away",
                  "Share of lean place-months with a fed place within the distance. A curve at 100% on the left would mean no travel is needed.",
                  to_svg(fig))


def map_chart():
    import numpy as np
    from matplotlib.colors import LinearSegmentedColormap
    m = np.loadtxt(os.path.join(HERE, "results", "lean_map.csv"), delimiter=",")
    land = np.ma.masked_less(m, 0)
    cmap = LinearSegmentedColormap.from_list("lean", ["#1baf7a", "#eda100", "#eb6834"])
    cmap.set_bad(color="#2a78d6", alpha=0.25)
    fig, ax = plt.subplots(figsize=(4.6, 4.6))
    im = ax.imshow(land, cmap=cmap, vmin=0, vmax=12, interpolation="nearest")
    ax.set_xticks([])
    ax.set_yticks([])
    ax.grid(False)
    cb = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.03, ticks=[0, 4, 8, 12])
    cb.outline.set_visible(False)
    cb.ax.tick_params(colors=INK)
    return figure("Where the winter falls, at a year of 1,200",
                  "Lean months a year on c1225's land (4x4 blocks); sea in blue. Green is fed all year, orange never.",
                  to_svg(fig))


TEXT = {}


def main():
    r = rows_by_year()
    st = stage_rows()
    charts_season = [spell_chart(), map_chart()]
    charts_travel = [dist_chart()]

    def burnt_std(y):
        return float(st[y]["burnt"]) * 11880 / y

    summary = "".join(
        f"<tr><td>{y:,}</td><td>{st[y]['habitats']}</td><td>{st[y]['wide']}</td><td>{float(st[y]['change']):.2f}</td>"
        f"<td>{burnt_std(y):.2%}</td><td>{float(r[y]['seasonal']):.0%}</td><td>{int(r[y]['spell_p50_steps']):,} / {int(r[y]['spell_p90_steps']):,}</td>"
        f"<td>{r[y]['dist_p50']}</td><td>{float(r[y]['within_25']):.0%}</td><td>{float(r[y]['lean_temp_p50']):.0f}</td></tr>"
        for y in YEARS)
    appendix = "".join(
        f"<tr><td>{y:,}</td><td>{float(st[y]['stand']):.3f}</td><td>{float(st[y]['share_grass']):.2f} / {float(st[y]['share_wood']):.2f} / {float(st[y]['share_algae']):.2f}</td>"
        f"<td>{st[y]['larger_grass']} / {st[y]['larger_wood']} / {st[y]['larger_algae']}</td><td>{float(st[y]['burnt']):.4f}</td><td>{float(st[y]['rain_land']) / y:.2f}</td>"
        f"<td>{float(r[y]['always_fed']):.0%} / {float(r[y]['never_fed']):.0%}</td><td>{r[y]['dist_p25']} / {r[y]['dist_p75']}</td><td>{float(r[y]['lean_low_p50']):.0f}</td><td>{float(r[y]['night_drop_p50']):.0f}</td></tr>"
        for y in YEARS)

    TEXT["tldr"] = ("A year of 1,200 steps puts the winter inside a grown life. c1225 with its producers still passes "
                    "stages A and B at that year (fire's yearly line aside), and a seasonal place is lean for 400 steps "
                    "against a grown life of 500-570, where today it is lean for 3,960. A place fed in the lean month is "
                    "15 cells away. Next: the bodies on this world, with the flesh slowing in the cold (#93).")
    TEXT["question"] = ("P1 (#93) starts from a ratio: a grown body lives 1/20 of c1225's year, so no body meets a season. "
                        "The year is the sun's parameter; the cheapest layer goes first. At a shorter year, does the world still "
                        "stand, and how long and how far is its winter to a body?")
    TEXT["world"] = ("e062's climate and producers on c1225, every law and rate per step unchanged; only the year moves. "
                     "The last year is written by month: temperature, night low and the grass's growing index.")
    TEXT["runs"] = ("Years of 11,880 (control), 2,400, 1,200 and 600 steps; the day stays 75. Each run spins the climate "
                    "20,000 updates and grows producers 200,000 steps; about 5 minutes each on the Mac.")
    TEXT["v"] = [
        ("", "Stage A holds: 12-14 habitats, 4 wide, 35% of cells change habitat in a year."),
        ("", "Stage B holds but for fire's yearly line; per 11,880 steps it burns 0.8-1.0% against 1.45%."),
        ("", "At 1,200 the lean spell is 400 steps (p90 1,000), under a grown life of 500-570."),
        ("partly", "A fed place within 25 cells for 67% of lean place-months at 1,200; the median, 15, is beyond the eye's 9."),
    ]
    TEXT["r1"] = ("At every year down to 1,200 a seasonal place is lean for about four months running, so its spell "
                  "falls with the year. The lean months are the winter: nothing grows under 5 C, and a lean month "
                  "averages -11 C. At 600 a month is shorter than a day, so day and season mix.")
    TEXT["r2"] = ("Half the lean place-months have a fed place within 9-15 cells over land, set by the terrain and not "
                  "by the year. A grown body today travels 8 cells in its life: the refuge is within its legs' reach "
                  "(60 steps at full speed), not within its eyes'.")
    TEXT["disc"] = ("The world's winter is a third of its year at any year length, so the year alone sets whether a body "
                    "meets it. That makes the year a lever with little side cost: the habitats and the producers' shares stay.\n"
                    "What the world does not give is a way through the winter. Its nights fall toward -30 C and a lean "
                    "month averages -11 C; today a body under 15 C pays energy to warm itself, so a winter of 400 steps "
                    "costs a body of 25 blocks about three times its upkeep, and a grown body holds 90-300 steps of fat. The bodies' side of "
                    "#93 is a law of the flesh: its pace follows its warmth, so the cold slows a body and its fat lasts.\n"
                    "Not shown: whether bodies move toward the fed places. No sense reads the season.")
    TEXT["concl"] = ("The year for #93's bodies is 1,200 steps: sixteen days a year, a winter shorter than a grown life, the "
                     "producers as they stand. 600 loses the season in the day; 2,400 keeps the winter longer than a life. "
                     "Next: stage C on this world with the cycle design in #93.")
    words = sum(len(v.split()) for k, v in TEXT.items() if k != "v") + sum(len(t.split()) for _, t in TEXT["v"])
    print("words", words)

    def verdict(kind):
        return {"": '<span class="verdict">Yes</span>', "partly": '<span class="verdict partly">Partly</span>',
                "no": '<span class="verdict no">No</span>'}[kind]

    disc = "".join(f"<p>{html.escape(p)}</p>" for p in TEXT["disc"].split("\n"))
    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>e086 The year - Report</title>
<style>{CSS}</style>
</head>
<body>
<main>
<h1>e086: a year a body can live through</h1>
<p class="sub">Experiment report - 2026-09-19 - stages A and B of c1225 at years of 11,880, 2,400, 1,200 and 600 steps</p>

<section class="tldr">
<h2>TL;DR</h2>
<p>{html.escape(TEXT["tldr"])}</p>
</section>

<h2>1. Question</h2>
<p>{html.escape(TEXT["question"])}</p>
<ol>
  <li><strong>Stage A holds</strong> at a shorter year: the land follows the sun within 35 steps.</li>
  <li><strong>Stage B holds</strong>, but fire's line per year falls with the year.</li>
  <li><strong>The winter fits in a grown life</strong> at a year of about 1,200.</li>
  <li><strong>A fed place is within 25 cells</strong> of most lean places.</li>
</ol>

<h2>2. The world</h2>
<p>{html.escape(TEXT["world"])}</p>
{DIAGRAM}
<p><strong>Runs.</strong> {html.escape(TEXT["runs"])}</p>
<ul class="measures">
  <li><strong>Lean month</strong> - a land month whose growing index is under a quarter of the land's median.</li>
  <li><strong>Seasonal place</strong> - lean in 1-11 months of its year.</li>
  <li><strong>Lean spell</strong> - a place's longest run of lean months, in steps.</li>
  <li><strong>Distance</strong> - cells over land from a lean place to the nearest place fed that month.</li>
</ul>

<h2>3. Results</h2>
<div class="tw"><table>
<thead><tr><th>Year</th><th>Habitats</th><th>Wide</th><th>Change</th><th>Burnt / 11,880 steps</th><th>Seasonal land</th><th>Spell p50 / p90</th><th>Distance p50</th><th>Within 25</th><th>Lean month C</th></tr></thead>
<tbody>{summary}</tbody></table></div>
<ol class="verdicts">
{"".join(f"<li>{verdict(k)} {html.escape(t)}</li>" for k, t in TEXT["v"])}
</ol>

<h3>3.1 The winter is a third of the year, at any year</h3>
<div class="grid2">
{"".join(charts_season)}
</div>
<p>{html.escape(TEXT["r1"])}</p>

<h3>3.2 The refuge is within the legs' reach, not the eyes'</h3>
<div class="grid2">
{"".join(charts_travel)}
</div>
<p>{html.escape(TEXT["r2"])}</p>

<h2>4. Discussion</h2>
{disc}

<h2>5. Conclusion and next step</h2>
<p>{html.escape(TEXT["concl"])}</p>

<h2>Appendix: data</h2>
<details><summary>More measures by year</summary><div class="tw"><table>
<thead><tr><th>Year</th><th>Agree</th><th>Grass / wood / algae</th><th>Larger part</th><th>Burnt a year</th><th>Rain mm a step</th><th>Always / never fed</th><th>Distance p25 / p75</th><th>Lean night low C</th><th>Night drop C</th></tr></thead>
<tbody>{appendix}</tbody></table></div></details>
<p>The rows are in <code>results/*_row.csv</code>, the monthly measures in <code>results/months.csv</code> (bars 0.1 and 0.5 too), <code>spells.csv</code>, <code>dist.csv</code> and <code>lean_map.csv</code>. Build: <code>uv run python experiments/e086_year/months.py</code> (needs the runs' <code>_months.bin</code>), then <code>uv run python experiments/e086_year/report.py</code>.</p>
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
