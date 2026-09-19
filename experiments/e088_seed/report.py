#!/usr/bin/env python3
"""Build report.html for e088 (#99 S, stage B: seed, the producers alone).

Charts: matplotlib, exported as SVG and inlined. Diagram: hand-written SVG.
Run from the repo root: uv run python experiments/eNNN_name/report.py
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

RUNS = ["s0", "s0.1", "s0.2", "s0.4"]
YEAR = 11880

DIAGRAM = """
<figure class="diagram">
<svg viewBox="0 0 720 236" role="img" aria-label="Grass sets seed, which sprouts back into grass or rots into the soil" style="max-width:100%;height:auto;display:block">
<defs><marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="currentColor"/></marker></defs>
<g fill="none" stroke="currentColor" stroke-width="1.2" font-size="12" font-family="system-ui, sans-serif">
  <rect x="20" y="86" width="130" height="54" rx="6"/>
  <text x="85" y="117" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">soil</text>
  <rect x="290" y="20" width="140" height="54" rx="6"/>
  <text x="360" y="51" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">grass (leaf)</text>
  <rect x="290" y="156" width="140" height="54" rx="6" stroke="var(--s1)" stroke-width="2"/>
  <text x="360" y="187" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">seed on the ground</text>
  <line x1="150" y1="100" x2="288" y2="52" marker-end="url(#arr)"/>
  <text x="200" y="62" text-anchor="middle" fill="currentColor" stroke="none">growth x 0.8</text>
  <line x1="150" y1="126" x2="288" y2="178" marker-end="url(#arr)"/>
  <text x="196" y="176" text-anchor="middle" fill="currentColor" stroke="none">growth x 0.2</text>
  <line x1="400" y1="154" x2="400" y2="76" marker-end="url(#arr)"/>
  <text x="410" y="112" fill="currentColor" stroke="none">sprouts 0.001 a step</text>
  <text x="410" y="127" fill="currentColor" stroke="none">x warmth x water</text>
  <line x1="430" y1="200" x2="600" y2="200" marker-end="url(#arr)"/>
  <text x="520" y="222" text-anchor="middle" fill="currentColor" stroke="none">rots 1/20,000 x warmth x water</text>
  <text x="610" y="204" fill="currentColor" stroke="none">soil</text>
  <line x1="430" y1="36" x2="600" y2="36" marker-end="url(#arr)"/>
  <text x="515" y="28" text-anchor="middle" fill="currentColor" stroke="none">dies, 1/2,000 a step</text>
  <text x="610" y="40" fill="currentColor" stroke="none">litter</text>
</g>
</svg>
<figcaption>Figure 1. The seed law at seed_share 0.2. Cold or dry ground stops setting, sprouting and rot alike, so seed waits while
leaf dies back. Fire does not burn seed. No body eats it yet.</figcaption>
</figure>
"""


def bands(run):
    with open(os.path.join(HERE, "results", "alone", f"c1225_life9_{run}_bands.csv")) as f:
        return list(csv.DictReader(f))


def band_series(run, lat):
    """Per bands step, a land cell's grass and seed and the sprouted share of the grass added, at one band."""
    acc = {}
    for r in bands(run):
        if int(r["lat"]) != lat:
            continue
        a = acc.setdefault(int(r["step"]), [0.0] * 5)
        for j, k in enumerate(["cells", "grass", "seed", "grown", "sprouted"]):
            a[j] += float(r[k])
    steps = sorted(acc)
    g = [acc[s][1] / acc[s][0] for s in steps]
    sd = [acc[s][2] / acc[s][0] for s in steps]
    sh = [acc[s][4] / max(acc[s][3] + acc[s][4], 1e-12) for s in steps]
    return steps, g, sd, sh


def main():
    sw = {r["run"]: r for r in csv.DictReader(open(os.path.join(HERE, "results", "sweep.csv")))}
    sb = list(csv.DictReader(open(os.path.join(HERE, "results", "sweep_bands.csv"))))
    charts1, charts2 = [], []

    xs, g2, sd2, _ = band_series("s0.2", 40)
    _, g0, _, _ = band_series("s0", 40)
    charts1.append(line_chart("40-50 N: the seed is flat, the grass swings",
                              "A land cell's matter at seed_share 0.2, over two years. The seed line barely moves with the season.",
                              xs, [("grass, control", g0, 0), ("grass, 0.2", g2, 1), ("seed, 0.2", sd2, 2)], ymin=0))

    def by_lat(run, q):
        rows = sorted([b for b in sb if b["run"] == run and int(b["quarter"]) == q], key=lambda b: int(b["lat"]))
        return [int(b["lat"]) + 5 for b in rows], rows

    # the hemisphere's winter: north quarter 3 for lat >= 0, quarter 1 for lat < 0; summer the other
    lats, w3 = by_lat("s0.2", 3)
    _, w1 = by_lat("s0.2", 1)
    winter = [float(a["seed_per_grass"]) if l >= 0 else float(b["seed_per_grass"]) for l, a, b in zip(lats, w3, w1)]
    summer = [float(b["seed_per_grass"]) if l >= 0 else float(a["seed_per_grass"]) for l, a, b in zip(lats, w3, w1)]
    keep = [i for i, l in enumerate(lats) if abs(l) <= 55]
    fig, ax = new_axes("latitude (degrees, band centre)")
    ax.plot([lats[i] for i in keep], [winter[i] for i in keep], color=SERIES[3], linewidth=1.6, label="own winter quarter")
    ax.plot([lats[i] for i in keep], [summer[i] for i in keep], color=SERIES[0], linewidth=1.6, label="own summer quarter")
    ax.set_ylim(0, 1.6)
    ax.yaxis.set_major_locator(MaxNLocator(4))
    legend_above(ax, 2)
    charts1.append(figure("Seed over grass, by latitude (0.2)",
                          "Above 1: more seed than leaf on the ground. Bands past 60 N hold almost no grass and are left out.",
                          to_svg(fig)))

    series = []
    for slot, run in [(0, "s0.1"), (1, "s0.2"), (2, "s0.4")]:
        xs, _, _, sh = band_series(run, 40)
        series.append((f"seed_share {run[1:]}", sh, slot))
    charts2.append(line_chart("40-50 N: the sprouted share of new grass",
                              "Seed that sprouted over all grass added. A spring flush would rise after each winter; the lines sit at the share.",
                              xs, series, ymin=0))

    rows = "".join(
        f"<tr><td>{r}</td><td>{float(sw[r]['grass']):.2f}</td><td>{float(sw[r]['seed']):.2f}</td><td>{float(sw[r]['seed_per_grass']):.2f}</td>"
        f"<td>{float(sw[r]['share_grass']):.0%} / {float(sw[r]['share_wood']):.0%} / {float(sw[r]['share_algae']):.0%}</td>"
        f"<td>{float(sw[r]['burnt_a_year']):.1%}</td><td>{float(sw[r]['matter_err']):.0e}</td></tr>" for r in RUNS)

    tbl = "".join(
        f"<tr><td>{b['run']}</td><td>{b['lat']}</td><td>{b['quarter']}</td><td>{float(b['grass']):.3f}</td><td>{float(b['seed']):.3f}</td><td>{float(b['seed_per_grass']):.2f}</td><td>{float(b['sprout_share']):.2f}</td></tr>"
        for b in sb)
    tables = ("<details><summary>By run, 10-degree band and quarter (0 north spring ... 3 north winter)</summary><div class='tw'><table><thead><tr>"
              "<th>run</th><th>lat</th><th>quarter</th><th>grass a cell</th><th>seed a cell</th><th>seed/grass</th><th>sprouted share</th></tr></thead>"
              f"<tbody>{tbl}</tbody></table></div></details>")

    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>e088 Seed - Report</title>
<style>{CSS}</style>
</head>
<body>
<main>
<h1>e088: Does grass that keeps seed make a food worth eating?</h1>
<p class="sub">Experiment report - 2026-09-20 - producers alone on c1225, seed_share 0 / 0.1 / 0.2 / 0.4, two years after a 17-year settled world</p>

<section class="tldr">
<h2>TL;DR</h2>
<p>Yes, as a steady bank: at seed_share 0.2 seed lies at 0.43 of the grass on the land, and outweighs the leaf in winter at 50 degrees.
The grass loses nothing and stage B still passes, fire at its 1% line. But the bank does not keep time: it neither piles up in autumn
nor flushes in spring. Next: e089, bodies that need a tooth to eat it.</p>
</section>

<h2>1. Question</h2>
<p>P2 (#99) adds foods that need different mouths. Its first law, seed, changes the producers, so it is run without bodies first:
is there a seed bank to eat, where and when?</p>
<ol>
  <li><strong>A bank by season.</strong> Seed is largest in the lean quarter, a third of the grass or more there.</li>
  <li><strong>The spring's grass from seed.</strong> A quarter or more of the grass added in spring at 30-60 degrees.</li>
  <li><strong>The grass holds.</strong> Leaf within 15% of the control.</li>
  <li><strong>Stage B passes.</strong> Each producer 5% of the standing matter, none dies out, fire 1-20% of the land a year.</li>
</ol>

<h2>2. The world</h2>
<p>Today's default world (e082) on c1225, with one law on the grass (Figure 1).</p>
{DIAGRAM}
<p><strong>Runs.</strong> Four runs, one per seed_share. Each grows its producers 17 years from the climate's spin-up, then runs 2 years (23,760 steps) with no bodies. Six minutes a run on one core.</p>
<ul class="measures">
  <li><strong>Seed / grass</strong> - seed over leaf standing on the land, by 10-degree band and quarter.</li>
  <li><strong>Sprouted share</strong> - sprouted seed over all grass added (leaf grown plus sprouted).</li>
  <li><strong>Stage B</strong> - shares of standing matter, least totals, land burnt a year, the ledger.</li>
</ul>

<h2>3. Results</h2>
<div class="tw"><table>
<thead><tr><th>run</th><th>grass a land cell</th><th>seed</th><th>seed/grass</th><th>grass / wood / algae</th><th>fire a year</th><th>matter err</th></tr></thead>
<tbody>{rows}</tbody></table></div>
<ol class="verdicts">
<li><span class="verdict partly">Partly</span> Seed outweighs leaf in the lean quarter (1.44 at 50 N), but the seed itself is flat over the year (0.43-0.46 at 40 N).</li>
<li><span class="verdict no">No</span> The sprouted share equals seed_share in every season (0.17-0.22 at 0.2); no spring flush.</li>
<li><span class="verdict">Yes</span> Leaf at 0.99 of the control; the seed's matter comes from the soil (-15%) and wood (-8%).</li>
<li><span class="verdict">Yes</span> Grass 64%, wood 22%, algae 14%, none dies out; fire 1.0% a year, on the line.</li>
</ol>

<h3>3.1 Seed waits while the leaf dies back</h3>
<div class="grid2">
{"".join(charts1)}
</div>
<p>Setting, sprouting and rot all follow warmth and water, so the bank settles at growth over the sprout rate in every season. The
winter food is seed only because the leaf dies in the cold and the seed does not.</p>

<h3>3.2 The seed does not wait for spring</h3>
<div class="grid2">
{"".join(charts2)}
</div>
<p>A grain waits about 1,000 steps where it is warm and wet, a third of a quarter, so most seed sprouts in the season it was set.</p>

<h2>4. Discussion</h2>
<p>The bank is large because it turns over slowly, not because much is set: 12.6 a step goes to seed against about 50 to leaf.
A seed eater lives on that flow, a fifth of the grass's; the standing bank is what lets it outlast a winter.</p>
<p>A bank that keeps time would need seed that sprouts on a cue of its own, such as after a cold spell. #99 does not ask for it:
seed is to be a food behind a tooth that lasts through a lean season, and it is that already.</p>
<p>Without bodies this does not show whether grazers take the leaf before it sets seed, the design's first way to fail.</p>

<h2>5. Conclusion and next step</h2>
<p>Seed at 0.2 is a steady, lean-season food and costs the producers little. Stage C (e089) keeps 0.2 and adds the bodies'
side: a tooth of force 2 opens seed, and fiber is digested over time.</p>

<h2>Appendix: data</h2>
<p>Every run's band x quarter numbers; the logs are in <code>results/alone/</code>. Build this report with <code>uv run python experiments/e088_seed/sweep.py</code> then <code>uv run python experiments/e088_seed/report.py</code>.</p>
{tables}
</main>
</body>
</html>
"""
    import re
    words = len(re.sub(r"<[^>]+>", " ", page.split("<h2>Appendix")[0].split("</style>")[1]).split())
    out = os.path.join(HERE, "report.html")
    with open(out, "w") as f:
        f.write(page)
    print(f"wrote {out} ({os.path.getsize(out)//1024} KB, about {words} words before the appendix)")


if __name__ == "__main__":
    main()
