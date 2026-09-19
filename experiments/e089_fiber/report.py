#!/usr/bin/env python3
"""Build report.html for e089 (#99 S + Fb, stage C: seed behind a tooth, fiber digested over time).

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
.cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); gap: 16px; }
.card { margin: 0; display: flex; gap: 12px; align-items: flex-start; }
.card figcaption { font-size: 12px; color: var(--ink2); }
.card figcaption strong { color: var(--ink); font-size: 12.5px; }
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

KIND_COLOR = {1: SERIES[0], 2: SERIES[1], 3: SERIES[3], 4: SERIES[2]}  # hard, muscle, sensor, gut (as the viewer)
SEEDS = ("9", "10", "11")

DIAGRAM = """
<figure class="diagram">
<svg viewBox="0 0 720 250" role="img" aria-label="Seed is opened by a tooth; grass fiber waits in the gut, where it ferments each step or leaves as dung each turn" style="max-width:100%;height:auto;display:block">
<defs><marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="currentColor"/></marker></defs>
<g fill="none" stroke="currentColor" stroke-width="1.2" font-size="12" font-family="system-ui, sans-serif">
  <rect x="20" y="30" width="120" height="44" rx="6"/>
  <text x="80" y="57" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">seed</text>
  <rect x="20" y="150" width="120" height="44" rx="6"/>
  <text x="80" y="177" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">grass</text>
  <rect x="300" y="30" width="130" height="44" rx="6"/>
  <text x="365" y="57" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">energy</text>
  <rect x="300" y="150" width="130" height="44" rx="6" stroke="var(--s1)" stroke-width="2"/>
  <text x="365" y="177" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">fiber in the gut</text>
  <rect x="560" y="150" width="130" height="44" rx="6"/>
  <text x="625" y="177" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">litter (dung)</text>
  <line x1="140" y1="52" x2="298" y2="52" marker-end="url(#arr)"/>
  <text x="219" y="44" text-anchor="middle" fill="currentColor" stroke="none">all, with a tooth of 2</text>
  <line x1="140" y1="160" x2="298" y2="66" marker-end="url(#arr)"/>
  <text x="196" y="103" text-anchor="middle" fill="currentColor" stroke="none">0.4 at the bite</text>
  <line x1="140" y1="180" x2="298" y2="180" marker-end="url(#arr)"/>
  <text x="219" y="198" text-anchor="middle" fill="currentColor" stroke="none">0.6 as fiber</text>
  <line x1="380" y1="148" x2="380" y2="76" marker-end="url(#arr)"/>
  <text x="392" y="110" fill="currentColor" stroke="none">0.02 a step</text>
  <line x1="430" y1="172" x2="558" y2="172" marker-end="url(#arr)"/>
  <text x="494" y="164" text-anchor="middle" fill="currentColor" stroke="none">0.02 a turn</text>
  <text x="365" y="225" text-anchor="middle" fill="currentColor" stroke="none">a slow body waits more steps a turn: it digests more</text>
</g>
</svg>
<figcaption>Figure 1. The two laws. A gut takes a cell's grass, seed and carrion in their proportions; only a body with a hard tip of
force 2 takes the seed. Algae are 0.3 fiber and the bottom's litter 0.5; seed, flesh and carrion none.</figcaption>
</figure>
"""


def rows(name):
    with open(os.path.join(HERE, "results", name)) as f:
        return list(csv.DictReader(f))


def bars(title, subtitle, groups, series, pct=False):
    fig, ax = plt.subplots(figsize=(6.4, 2.6))
    n = len(series)
    width = 0.8 / n
    for i, (label, values, slot) in enumerate(series):
        xs = [x - 0.4 + width * (i + 0.5) for x in range(len(groups))]
        ax.bar(xs, values, width=width * 0.9, color=SERIES[slot], label=label)
    ax.set_xticks(range(len(groups)))
    ax.set_xticklabels(groups)
    ax.yaxis.set_major_formatter((lambda y, _p: f"{y:.0%}") if pct else kfmt)
    ax.yaxis.set_major_locator(MaxNLocator(4))
    legend_above(ax, n)
    return figure(title, subtitle, to_svg(fig))


def gallery(picks, caption):
    cards = []
    for r in picks:
        side, cells = int(r["side"]), r["cells"]
        px = 88 // max(side, 1)
        rects = "".join(
            f'<rect x="{(i % side) * px}" y="{(i // side) * px}" width="{px - 1}" height="{px - 1}" fill="{KIND_COLOR[int(k)]}"/>'
            for i, k in enumerate(cells[: side * side]) if k != "0")
        where = max((("land", float(r["land"])), ("surface", float(r["surface"])), ("bottom", float(r["bottom"]))), key=lambda x: x[1])
        cards.append(f"""<figure class="card"><svg viewBox="-1 -1 89 89" width="104" height="104" role="img" aria-label="{html.escape(r['kind'])}">
<rect x="-1" y="-1" width="89" height="89" fill="var(--grid)"/>{rects}</svg>
<figcaption><strong>{html.escape(r['kind'])}</strong><br>{r['run']}, {float(r['share']):.0%} of the grown bodies<br>
{int(float(r['born_size']))} blocks, mass {float(r['mass']):.0f}, pace {float(r['pace']):.2f}<br>
{where[1]:.0%} on the {where[0]}; plant: grass {float(r['grass']):.0%}, seed {float(r['seed']):.0%}; kills {float(r['kills']):.0%} of its food</figcaption></figure>""")
    return f"""<figure class="diagram"><div class="cards">{"".join(cards)}</div>
<figcaption>Figure 2. {html.escape(caption)}</figcaption></figure>"""


def main():
    sw = {r["run"]: r for r in rows("sweep.csv")}
    ks = rows("kinds.csv")
    bodies = rows("bodies.csv")
    groups = [f"seed {s}" for s in SEEDS]
    ctrl = [sw[f"control {s}"] for s in SEEDS]
    sfb = [sw[f"S+Fb {s}"] for s in SEEDS]
    f = lambda rs, k: [float(r[k]) for r in rs]  # noqa: E731

    c1 = [bars("Kinds at a census", "Ways of living holding 5% of the grown bodies, the mean over the censuses. Done-when: +1 on every seed.",
               groups, [("control", f(ctrl, "kinds_at"), 0), ("S+Fb", f(sfb, "kinds_at"), 1)]),
          bars("The largest line's share of the land", "Over the censuses. Done-when: no higher than the control.",
               groups, [("control", f(ctrl, "top_share"), 0), ("S+Fb", f(sfb, "top_share"), 1)], pct=True)]

    # The food of the toothed land kinds: the largest kind with a tooth that lives on land, by run.
    tooth = []
    for s in SEEDS:
        k = max((r for r in ks if r["run"] == f"S+Fb {s}" and "/ tooth /" in r["kind"] and r["kind"].endswith("land")), key=lambda r: float(r["share"]))
        kills = float(k["kills"])
        tooth.append({"grass": (1 - kills) * float(k["grass"]), "seed": (1 - kills) * float(k["seed"]), "kills": kills})
    c2 = [bars("What the largest toothed land kind eats (S+Fb)",
               "Shares of its food; the rest is carrion and browse. A seed-led kind would have seed above grass.",
               groups, [("grass", [t["grass"] for t in tooth], 0), ("seed", [t["seed"] for t in tooth], 2), ("kills", [t["kills"] for t in tooth], 1)], pct=True),
          bars("Grass eaters grow heavier under fiber", "Median mass of the grown bodies of grass-led kinds held at a census.",
               groups, [("control", f(ctrl, "mass_grass"), 0), ("S+Fb", f(sfb, "mass_grass"), 1)])]

    held = [b for b in bodies if b["run"] == "S+Fb 9" and float(b["share"]) >= 0.05]
    gal = gallery(sorted(held, key=lambda b: -float(b["share"]))[:6],
                  "The six largest kinds of S+Fb on seed 9, each its commonest birth body (hard blue, muscle orange, gut aqua, sensor yellow). "
                  "The toothed land kind has a hard row on one side and muscle on the other: a hard tip with force behind it, which opens seed and bodies alike.")

    names = ["control 9", "control 10", "control 11", "S 9", "S+Fb 9", "S+Fb 10", "S+Fb 11"]
    table = "".join(
        f"<tr><td>{n}</td><td>{float(sw[n]['kinds_at']):.2f}</td><td>{float(sw[n]['placed_at']):.2f}</td><td>{float(sw[n]['top_share']):.0%}</td>"
        f"<td>{float(sw[n]['seed_led']):.0%}</td><td>{float(sw[n]['mass_grass']):.0f}</td><td>{float(sw[n]['pace_grass']):.2f}</td>"
        f"<td>{float(sw[n]['eat_seed']):.0%}</td><td>{float(sw[n]['pop']):,.0f}</td></tr>" for n in names)
    ktbl = "".join(
        f"<tr><td>{r['run']}</td><td>{html.escape(r['kind'])}</td><td>{float(r['share']):.0%}</td><td>{r['lead']}</td><td>{float(r['mass']):.0f}</td>"
        f"<td>{float(r['pace']):.2f}</td><td>{float(r['grass']):.0%}</td><td>{float(r['seed']):.0%}</td><td>{float(r['kills']):.0%}</td></tr>"
        for r in ks if float(r["share"]) >= 0.03)
    tables = ("<details><summary>Kinds holding 3% or more of a run's grown bodies</summary><div class='tw'><table><thead><tr>"
              "<th>run</th><th>kind</th><th>share</th><th>led by</th><th>mass</th><th>pace</th><th>grass of plant</th><th>seed of plant</th><th>kills of food</th></tr></thead>"
              f"<tbody>{ktbl}</tbody></table></div></details>")

    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>e089 Seed and Fiber - Report</title>
<style>{CSS}</style>
</head>
<body>
<main>
<h1>e089: Do seed behind a tooth and slow fiber make more ways of living?</h1>
<p class="sub">Experiment report - 2026-09-20 - c1225, seeds 9-11, 100,000 steps, against e081's control ladder</p>

<section class="tldr">
<h2>TL;DR</h2>
<p>No. No kind lives on seed: the tooth that opens it is the hunter's, and a gut takes seed only mixed with the grass
around it (seed is 3% of what bodies eat). Kinds fall on two seeds of three and the largest line grows on two. Fiber did
one thing: grass eaters grew 14-27% heavier and slower. Next: redesign seed's mouthful, or stop P2's seed.</p>
</section>

<h2>1. Question</h2>
<p>P2 (#99) adds plant foods that need different mouths and guts. e088 made a seed bank of 0.43 of the grass. Do bodies part
into seed eaters and grass eaters?</p>
<ol>
  <li><strong>More ways of living.</strong> Kinds at a census +1 over each control.</li>
  <li><strong>The foods part the kinds.</strong> A seed-led and a grass-led kind each hold 5% of the grown bodies.</li>
  <li><strong>Size follows the food.</strong> Grass-led kinds 1.3 times heavier than seed-led.</li>
  <li><strong>No harm.</strong> The largest line no higher than the control.</li>
</ol>

<h2>2. The world</h2>
<p>Today's default world with e088's seed at 0.2 and two laws for the bodies (Figure 1).</p>
{DIAGRAM}
<p><strong>Runs.</strong> S+Fb on seeds 9-11 and S alone on seed 9, 100,000 steps, a census every 1,000 steps from 36,000,
as the controls. 38-49 minutes a run on one core.</p>
<ul class="measures">
  <li><strong>Kinds</strong> - ways of living by birth form (e068), at a census and kept to a place.</li>
  <li><strong>Led by</strong> - the plant food that gives a kind the most of its plant matter.</li>
  <li><strong>Mass, pace</strong> - medians over a kind's grown bodies; pace is turns a step.</li>
  <li><strong>Largest line</strong> - its share of the land's bodies at a census.</li>
</ul>

<h2>3. Results</h2>
<div class="tw"><table>
<thead><tr><th>run</th><th>kinds</th><th>kept to a place</th><th>largest line</th><th>seed-led</th><th>grass-led mass</th><th>its pace</th><th>seed eaten</th><th>bodies</th></tr></thead>
<tbody>{table}</tbody></table></div>
<ol class="verdicts">
<li><span class="verdict no">No</span> Kinds 6.96 / 6.20 / 7.39 against 7.45 / 8.27 / 7.25.</li>
<li><span class="verdict no">No</span> No seed-led kind on any seed.</li>
<li><span class="verdict partly">Not testable</span> No seed-led kind; grass eaters grew heavier (52-57 against 43-50).</li>
<li><span class="verdict no">No</span> The largest line 75% on seed 9 (58%) and 53% on 11 (42%).</li>
</ol>

<h3>3.1 The ways of living do not rise</h3>
<div class="grid2">
{"".join(c1)}
</div>
<p>S alone on seed 9 is worse still: kinds 6.29, kept to a place 2.55, the largest line 75%. Fiber brings the kinds kept to a
place back, not the count.</p>

<h3>3.2 Seed goes to the hunters, and the grass eaters grow</h3>
<div class="grid2">
{"".join(c2)}
</div>
<p>The kinds that take seed are the toothed hunters of the control; seed is a side dish of their grass and kills. Under fiber
the slow body gets more of the grass, and grass eaters answer by weight, with no rule about size.</p>
{gal}

<h2>4. Discussion</h2>
<p>A gut takes a cell's foods in their proportions. Where seed lies it lies with the grass that set it, so no body can take
seed without the grass, and one that can take it also takes flesh with the same tooth. Seed never becomes a mouthful of its
own, which is what e075 found makes a food a way of living.</p>
<p>Fiber did what its law says: a heavy, slow body digests more of the same grass. The grass eaters took that route, but it
made them one kind heavier, not two kinds.</p>
<p>This does not show that seed cannot part the kinds; it shows that seed mixed into grass cannot.</p>

<h2>5. Conclusion and next step</h2>
<p>S and Fb are not kept under these conditions. #99 has two stage C experiments left. Seed needs a mouthful apart from the
grass (where or when it lies, or how it is taken), or P2 moves to another food.</p>

<h2>Appendix: data</h2>
<p>The full tables are in <code>results/sweep.csv</code>, <code>results/kinds.csv</code> and <code>results/bodies.csv</code>. Build with
<code>uv run python experiments/e089_fiber/sweep.py</code> then <code>uv run python experiments/e089_fiber/report.py</code>.</p>
{tables}
</main>
</body>
</html>
"""
    import re
    words = len(re.sub(r"<[^>]+>", " ", page.split("<h2>Appendix")[0].split("</style>")[1]).split())
    out = os.path.join(HERE, "report.html")
    with open(out, "w") as fh:
        fh.write(page)
    print(f"wrote {out} ({os.path.getsize(out)//1024} KB, about {words} words before the appendix)")


if __name__ == "__main__":
    main()
