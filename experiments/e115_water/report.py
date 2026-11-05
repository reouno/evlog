#!/usr/bin/env python3
"""Build report.html for this experiment.

Charts: matplotlib, exported as SVG and inlined. Diagram: hand-written SVG.
Run from the repo root: uv run python experiments/e115_water/report.py
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
    """Read a CSV into a list of rows (dicts of strings)."""
    with open(os.path.join(HERE, path)) as f:
        return list(csv.DictReader(f))


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


def line_chart(title, subtitle, xs, series, ymin=None, xlabel="year", ncol=3):
    """series: list of (label, ys, slot)."""
    fig, ax = new_axes(xlabel)
    for label, ys, slot in series:
        ax.plot(xs, ys, color=SERIES[slot], linewidth=1.6, label=label)
    if ymin is not None:
        ax.set_ylim(ymin, max(v for _, ys, _ in series for v in ys) * 1.12)
    ax.yaxis.set_major_formatter(kfmt)
    ax.yaxis.set_major_locator(MaxNLocator(4))
    legend_above(ax, ncol)
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



DIAGRAM = """
<figure class="diagram">
<svg viewBox="0 0 720 250" role="img" aria-label="Ground water drawn by roots into living tissue; a mouthful of tissue or litter brings water to a body; litter's water follows the ground's wetness" style="max-width:100%;height:auto;display:block">
<defs><marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="currentColor"/></marker></defs>
<g fill="none" stroke="currentColor" stroke-width="1.2" font-size="12" font-family="system-ui, sans-serif">
  <rect x="10" y="150" width="170" height="56" rx="6"/>
  <text x="95" y="174" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">ground, groundwater</text>
  <text x="95" y="192" text-anchor="middle" fill="currentColor" stroke="none">wet or dry by place</text>
  <rect x="10" y="20" width="170" height="56" rx="6"/>
  <text x="95" y="44" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">living tissue</text>
  <text x="95" y="62" text-anchor="middle" fill="currentColor" stroke="none">4 kg/kg x working part</text>
  <rect x="280" y="150" width="190" height="56" rx="6" stroke="var(--s1)" stroke-width="2"/>
  <text x="375" y="174" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">litter</text>
  <text x="375" y="192" text-anchor="middle" fill="currentColor" stroke="none">its make x the ground's wetness</text>
  <rect x="560" y="85" width="150" height="56" rx="6"/>
  <text x="635" y="109" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">body</text>
  <text x="635" y="127" text-anchor="middle" fill="currentColor" stroke="none">keeps up to its target</text>
  <line x1="95" y1="148" x2="95" y2="78" marker-end="url(#arr)"/>
  <text x="105" y="117" fill="currentColor" stroke="none">roots draw</text>
  <line x1="180" y1="178" x2="278" y2="178" marker-end="url(#arr)"/>
  <text x="229" y="168" text-anchor="middle" fill="currentColor" stroke="none">wets</text>
  <line x1="180" y1="48" x2="558" y2="100" marker-end="url(#arr)"/>
  <text x="330" y="58" fill="currentColor" stroke="none">a leaf eaten: about 1% of the diet</text>
  <line x1="470" y1="170" x2="558" y2="130" marker-end="url(#arr)"/>
  <text x="520" y="178" fill="currentColor" stroke="none">99%</text>
  <path d="M635,141 L635,236 L95,236 L95,208" stroke-dasharray="4 4" marker-end="url(#arr)"/>
  <text x="360" y="228" text-anchor="middle" fill="currentColor" stroke="none">drinks, and the rest back to the ground</text>
</g>
</svg>
<figcaption>Figure 1. A tissue holds water by its working part, filled by the roots. A mouthful brings its water. Litter (blue) is wet only where the ground is, so food is a drink mostly where drinking is easy.</figcaption>
</figure>
"""


def main():
    P = os.path.join(HERE, "results", "pilot")
    E = os.path.join(HERE, "..", "e114_chemistry", "results", "pilot")
    runs = {"e114 seed 2": (E, "lock_l2", 0, "--"), "water seed 2": (P, "water_l2", 0, "-"),
            "e114 seed 3": (E, "lock_l3", 1, "--"), "water seed 3": (P, "water_l3", 1, "-")}
    logs = {n: [r for r in load_csv(os.path.join(d, f + "_log.csv")) if float(r["year"]) >= 41] for n, (d, f, _, _) in runs.items()}

    def share(r, pre, key):
        v = {k: float(r[k]) for k in r if k.startswith(pre)}
        return float(r[pre + key]) / (sum(v.values()) or 1.0)

    def lines(title, sub, fn, ylog=False, pct=True):
        fig, ax = new_axes("year")
        for n, (_, _, slot, ls) in runs.items():
            ax.plot([float(r["year"]) for r in logs[n]], [fn(r) for r in logs[n]], color=SERIES[slot], ls=ls, lw=1.6, label=n)
        ax.xaxis.set_major_locator(MaxNLocator(integer=True))
        if ylog:
            ax.set_yscale("log")
        else:
            ax.set_ylim(0, None)
            ax.yaxis.set_major_locator(MaxNLocator(4))
        ax.yaxis.set_major_formatter((lambda y, _p: f"{y:.0%}" if y >= 0.1 or y == 0 else f"{y:.1%}") if pct else kfmt)
        legend_above(ax, 4)
        return figure(title, sub, to_svg(fig))

    c_thirst = lines("Thirst's share of the deaths", "Solid: with water in matter; dashed: e114. Lower is thirst easing.", lambda r: share(r, "died_", "thirst"))
    c_leaf = lines("The leaf's share of the diet", "A rise would be the living eaten more; the rest is nearly all litter.", lambda r: share(r, "ate_", "leaf"))
    c_bod = lines("Bodies on the islands", "Sown in year 40. Dashed: e114, the same life seed.", lambda r: float(r["bodies"]), pct=False)

    wet = load_csv(os.path.join(HERE, "results", "pilot_wet.csv"))
    def place(run, k):
        rows = [r for r in wet if r["run"] == run]
        return [float(r["wet"]) for r in rows], [float(r[k] or 0) for r in rows]

    fig, ax = new_axes("ground's fill")
    xs, days = place("water_l2", "of_animal_days")
    _, th = place("water_l2", "of_thirst")
    ax.bar([x - 0.022 for x in xs], days, width=0.04, color=SERIES[2], label="of the time spent")
    ax.bar([x + 0.022 for x in xs], th, width=0.04, color=SERIES[3], label="of the thirst deaths")
    ax.set_ylim(0, 1)
    ax.yaxis.set_major_formatter(lambda y, _p: f"{y:.0%}")
    ax.yaxis.set_major_locator(MaxNLocator(4))
    legend_above(ax, 2)
    c_where = figure("Where seed 2's bodies live and where they die of thirst", "Years 46-60. Left: dry ground. Bars that matched would mean thirst is not about place.", to_svg(fig))

    fig, ax = new_axes("ground's fill")
    for run, slot in (("water_l2", 0), ("water_l3", 1)):
        xs, fw = place(run, "food_water_of_water")
        ax.plot(xs, fw, color=SERIES[slot], lw=1.6, marker="o", ms=3, label=run.replace("water_l", "water seed "))
    ax.set_ylim(0, 0.6)
    ax.yaxis.set_major_formatter(lambda y, _p: f"{y:.0%}")
    ax.yaxis.set_major_locator(MaxNLocator(4))
    legend_above(ax, 2)
    c_fw = figure("Food's share of the water a body takes in", "Years 46-60, by the ground where the body is. Flat would mean food waters dry and wet ground alike.", to_svg(fig))

    def at(n, y, fn):
        return fn([r for r in logs[n] if int(float(r["year"])) == y][0])

    summ = ""
    for n in runs:
        summ += (f"<tr><td>{n}</td><td>{int(at(n, 60, lambda r: float(r['bodies']))):,}</td><td>{at(n, 60, lambda r: float(r['land_biomass'])):.2f}</td>"
                 f"<td>{at(n, 60, lambda r: share(r, 'ate_', 'leaf')):.2%}</td><td>{at(n, 60, lambda r: share(r, 'died_', 'thirst')):.0%}</td>"
                 f"<td>{at(n, 60, lambda r: (lambda fw, d: fw / (fw + d) if fw + d else 0)(float(r.get('food_water', 0) or 0), float(r['body_drunk']))):.0%}</td>"
                 f"<td>{at(n, 60, lambda r: float(r['p_locked'])):.0e}</td></tr>")

    cols = ["year", "bodies", "land_biomass", "body_drunk", "p_locked"]
    tables = data_table(cols, {n: {k: [float(r[k]) for r in rows] for k in cols} for n, rows in logs.items()}, every=2)

    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>e115 Water in Matter - Report</title>
<style>{CSS}</style>
</head>
<body>
<main>
<h1>e115: does water in matter turn the eaters to the living?</h1>
<p class="sub">Experiment report - 2026-11-05 - a gate on the trial world, two life seeds on the islands to year 60</p>

<section class="tldr">
<h2>TL;DR</h2>
<p>Living tissue now holds water, and a mouthful brings it. Thirst eases (36% of the deaths against 44%, and 4% against 24%), and food brings 15-39% of the bodies' water. But the leaf stays about 1% of the diet, no body enters the crowns, and locks hold less than before. Food waters the wet ground, where the bodies already live. Next: the door itself, height around a plant.</p>
</section>

<h2>1. Question</h2>
<p>In e114 the living were 93% of the food on land and the bodies ate litter for 97.8% of their diet. A plan check found every way to the living priced in something a body cannot pay, and no food carrying water while thirst was the first cause of death.</p>
<ol>
  <li><strong>The world stands</strong> with water in matter.</li>
  <li><strong>The living are eaten</strong> more, most where it is dry.</li>
  <li><strong>Thirst eases.</strong></li>
  <li><strong>The doors open</strong>: bodies in the crowns, locks rise.</li>
</ol>

<h2>2. The world</h2>
<p>e114's world, with one switch and one constant: 4 kg of water a kg of dry tissue that is all working part. No organ is named.</p>
{DIAGRAM}
<p><strong>Runs.</strong> A gate on the 16 km trial world (off is e114 to the digit), then life seeds 2 and 3 on the 64 km islands to year 60, each against e114's run of the same seed, on one machine.</p>
<ul class="measures">
  <li><strong>leaf of the diet</strong> - living leaf over all eaten.</li>
  <li><strong>food of the water</strong> - water in food over all a body takes in.</li>
  <li><strong>ground's fill</strong> - soil water over what it holds, where the body is.</li>
  <li><strong>locked share</strong> - producers' mass on a locked genotype.</li>
</ul>

<h2>3. Results</h2>
<div class="tw"><table><thead><tr><th>Year 60</th><th>bodies</th><th>land</th><th>leaf of the diet</th><th>thirst of the deaths</th><th>food of the water</th><th>locked share</th></tr></thead><tbody>{summ}</tbody></table></div>
<ol class="verdicts">
<li><span class="verdict">Yes</span> The world stands: more land than e114 in both seeds, 1.2x and 0.75x its bodies.</li>
<li><span class="verdict no">No</span> The living are eaten: the leaf at 1.02% and 0.49%, under e114's 1.26% and 0.53%.</li>
<li><span class="verdict">Yes</span> Thirst eases: 36% against 44%, 4% against 24%.</li>
<li><span class="verdict no">No</span> The doors open: no body in the crowns; locks 1,000 times rarer.</li>
</ol>

<h3>3.1 Thirst eases; the diet does not move</h3>
<div class="grid2">
{c_thirst}
{c_leaf}
</div>
<p>Water in food takes a share of the deaths from thirst in both seeds without changing what the bodies eat. Litter stays 99% of the diet in all four runs.</p>

<h3>3.2 The thirsty die on dry ground, where food brings little water</h3>
<div class="grid2">
{c_where}
{c_fw}
</div>
<p>In seed 2, 95% of the thirst deaths are on ground under a tenth full, where bodies spend 2% of their time. On the driest tenth food brings 2% and 5% of the water (seeds 2 and 3), on the wettest 27% and 54%. A litter's water follows the ground, and the leaves that hold water whatever the ground are mostly out of reach.</p>

<div class="grid2">
{c_bod}
</div>

<h2>4. Discussion</h2>
<p>The piece did what it was built to do: every mouthful is also a drink, priced by what the matter is. It did not do what it was for. Eating the living pays most where it is dry, but a body there reaches a few leaves, and its matter is the dead, which are dry there too.</p>
<p>The doors are the binding term. A median body reaches 14% of the leaves, and none lives in the crowns where the rest hang. Water was what a climber lacked in e112. No body went up here to try again.</p>
<p>In seed 3, thirst is rare, and three quarters of it falls on the wettest ground, where most bodies crowd. That is the rate a crowd can drink, not dry ground.</p>

<h2>5. Conclusion and next step</h2>
<p>Water in matter stays in the crate, on. It eases thirst and leaves the world standing, but it does not part the diet. The living stay behind height and the crown. The next gap is the door itself: height as a continuous axis around a plant, set aside in the plan check.</p>

<h2>Appendix: data</h2>
<p>The islands every two years from year 41. The full logs are in <code>results/gate/</code> and <code>results/pilot/</code>. The readings are in <code>results/gate.csv</code>, <code>results/pilot.csv</code>, <code>results/*_wet.csv</code> and <code>results/provenance.csv</code>. Build this report with <code>uv run python experiments/e115_water/report.py</code>.</p>
{tables}
</main>
</body>
</html>
"""
    out = os.path.join(HERE, "report.html")
    with open(out, "w") as f:
        f.write(page)
    import re
    prose = page.split("<h2>Appendix")[0].split('<section class="tldr">')[1]
    prose = re.sub(r"<svg.*?</svg>|<table.*?</table>", " ", prose, flags=re.S)
    words = len(re.sub(r"<[^>]+>", " ", prose).split())
    print(f"wrote {out} ({os.path.getsize(out)//1024} KB), ~{words} words of prose")


if __name__ == "__main__":
    main()
