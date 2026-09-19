#!/usr/bin/env python3
"""Build report.html for this experiment.

Charts: matplotlib, exported as SVG and inlined. Diagram: hand-written SVG.
Run from the repo root: uv run python experiments/e087_torpor/report.py
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

# A report is dark only (the user, 2026-09-16).
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
.cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); gap: 16px; }
.card { margin: 0; display: flex; gap: 12px; align-items: flex-start; }
.card figcaption { font-size: 12px; color: var(--ink2); }
.verdict.partly { background: rgba(250,178,25,0.15); color: #fab219; }
"""

#BODY
RUNS = [("c1225_life9_yq", "Y+Q seed 9", 0), ("c1225_life10_yq", "Y+Q seed 10", 2),
        ("c1225_life11_yq", "Y+Q seed 11", 3), ("c1225_life9_y", "Y alone seed 9", 1)]
RES = os.path.join(HERE, "results", "batch")
FROM, WINDOW = 36000, 5000
KIND_COLOR = {1: SERIES[0], 2: SERIES[1], 3: SERIES[3], 4: SERIES[2]}  # hard, muscle, sensor, gut
CLASS = ["sea", "land always fed", "seasonal land", "land never fed"]


def rows(path):
    with open(path) as f:
        return [r for r in csv.DictReader(f) if r.get("travel", "x") != ""]


def windows(months, num, den):
    """Sums of two columns per WINDOW steps: (window ends, num / den)."""
    acc = {}
    for r in months:
        w = (int(r["step"]) // WINDOW + 1) * WINDOW
        a = acc.setdefault(w, [0.0, 0.0])
        a[0] += num(r)
        a[1] += den(r)
    xs = sorted(w for w in acc if w <= 100000)
    return xs, [acc[w][0] / max(acc[w][1], 1e-9) for w in xs]


def places():
    raw = open(os.path.join(HERE, "results", "places_y1200.bin"), "rb").read()
    n = int.from_bytes(raw[4:8], "little")
    return raw[8:8 + n * n]


def gallery(cls):
    """The oldest bodies at the last censuses (90,000-100,000), one per lineage."""
    cards = []
    for run, label, _ in RUNS[:3]:
        seen, picks = set(), []
        rs = [r for r in rows(os.path.join(RES, run + "_agents.csv")) if int(r["step"]) >= 90000]
        for r in sorted(rs, key=lambda r: -int(r["age"])):
            if r["lineage"] not in seen:
                seen.add(r["lineage"])
                picks.append(r)
            if len(picks) == 2:
                break
        for r in picks:
            side, cells = int(r["side"]), r["cells"]
            px = 88 // max(side, 1)
            rects = "".join(
                f'<rect x="{(i % side) * px}" y="{(i // side) * px}" width="{px - 1}" height="{px - 1}" fill="{KIND_COLOR[int(k)]}"/>'
                for i, k in enumerate(cells[: side * side]) if k != "0")
            size = int(r["size"])
            share = lambda k: int(r[k]) / max(size, 1)  # noqa: E731
            where = ["on land", "at the surface", "on the bottom"][int(r["medium"])]
            cards.append(f"""<figure class="card"><svg viewBox="-1 -1 89 89" width="104" height="104" role="img" aria-label="body of lineage {r['lineage']}">
<rect x="-1" y="-1" width="89" height="89" fill="var(--grid)"/>{rects}</svg>
<figcaption><strong>{label}, line {r['lineage']}</strong><br>{int(r['age']):,} steps old, {int(r['turns']):,} turns<br>
{size} blocks: {share('hard'):.0%} hard, {share('muscle'):.0%} muscle, {share('digestive'):.0%} gut<br>
{where} ({CLASS[cls[int(r['cell'])]]}), at {float(r['btemp']):.0f} C</figcaption></figure>""")
    return f"""<figure class="diagram"><div class="cards">{"".join(cards)}</div>
<figcaption>Figure 7. The two oldest bodies of different lines at the last censuses of each Y+Q run. Blue hard, orange muscle, aqua gut, yellow sensor. Most are small, soft bodies on the cold sea bottom that took a fraction of a turn a step; two are hard-shelled, warm and on land.</figcaption></figure>"""


DIAGRAM = """
<figure class="diagram">
<svg viewBox="0 0 720 230" role="img" aria-label="A cold body takes fewer turns, makes less heat and cools further; its fat lasts longer" style="max-width:100%;height:auto;display:block">
<defs><marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="currentColor"/></marker></defs>
<g fill="none" stroke="currentColor" stroke-width="1.2" font-size="12" font-family="system-ui, sans-serif">
  <rect x="10" y="20" width="140" height="50" rx="6"/>
  <text x="80" y="42" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">its cells</text>
  <text x="80" y="58" text-anchor="middle" fill="currentColor" stroke="none">winter -11 C</text>
  <rect x="270" y="20" width="160" height="50" rx="6"/>
  <text x="350" y="42" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">body temperature T</text>
  <text x="350" y="58" text-anchor="middle" fill="currentColor" stroke="none">band 15-30 C</text>
  <rect x="550" y="20" width="160" height="50" rx="6" stroke="var(--s1)" stroke-width="2"/>
  <text x="630" y="42" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">pace</text>
  <text x="630" y="58" text-anchor="middle" fill="currentColor" stroke="none">2.5^((T-15)/10), 0.1-1</text>
  <rect x="270" y="160" width="160" height="50" rx="6"/>
  <text x="350" y="182" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">turns</text>
  <text x="350" y="198" text-anchor="middle" fill="currentColor" stroke="none">eat, move, breed, pay</text>
  <rect x="550" y="160" width="160" height="50" rx="6"/>
  <text x="630" y="182" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">fat</text>
  <text x="630" y="198" text-anchor="middle" fill="currentColor" stroke="none">lasts up to 10x the steps</text>
  <line x1="150" y1="45" x2="268" y2="45" marker-end="url(#arr)" marker-start="url(#arr)"/>
  <text x="209" y="36" text-anchor="middle" fill="currentColor" stroke="none">heat, every step</text>
  <line x1="430" y1="45" x2="548" y2="45" marker-end="url(#arr)"/>
  <text x="489" y="36" text-anchor="middle" fill="currentColor" stroke="none">sets</text>
  <line x1="630" y1="70" x2="440" y2="165" marker-end="url(#arr)"/>
  <text x="566" y="124" text-anchor="start" fill="currentColor" stroke="none">turns a step</text>
  <line x1="330" y1="160" x2="330" y2="72" marker-end="url(#arr)"/>
  <text x="322" y="120" text-anchor="end" fill="currentColor" stroke="none">heat made, per turn</text>
  <line x1="430" y1="195" x2="548" y2="195" marker-end="url(#arr)"/>
  <text x="489" y="186" text-anchor="middle" fill="currentColor" stroke="none">spent per turn</text>
</g>
</svg>
<figcaption>Figure 1. Q, the flesh's pace follows its warmth. A cold body takes fewer turns, so it makes less heat and cools further (torpor), and it spends its fat by the turn. Paying to warm and death by cold are gone; sweating over 30 C stays.</figcaption>
</figure>
"""


def main():
    months = {run: rows(os.path.join(RES, run + "_months.csv")) for run, _, _ in RUNS}
    grown = {run: [r for r in rows(os.path.join(RES, run + "_grown.csv")) if int(r["step"]) > FROM] for run, _, _ in RUNS}
    with open(os.path.join(HERE, "results", "read_batch.csv")) as f:
        read = {r["run"]: r for r in csv.DictReader(f)}
    cls = places()

    charts1, charts2, charts3 = [], [], []
    series = []
    for run, label, slot in RUNS:
        xs, ys = windows(months[run], lambda r: float(r["lived"]), lambda r: float(r["resolved"]))
        series.append((label, ys, slot))
    charts1.append(line_chart("Grown bodies alive at the end of their winter",
                              "Share of each winter's cohort, per 5,000 steps. The pass line is 25%.", xs, series, ymin=0))
    series = []
    for run, label, slot in RUNS:
        xs, ys = windows(months[run], lambda r: float(r["winter_temp"]) * float(r["winter"]), lambda r: float(r["winter"]))
        series.append((label, ys, slot))
    fig, ax = new_axes()
    for label, ys, slot in series:
        ax.plot(xs, ys, color=SERIES[slot], linewidth=1.6, label=label)
    ax.axhline(15, color=INK, linewidth=0.8, linestyle="--")
    ax.yaxis.set_major_locator(MaxNLocator(4))
    legend_above(ax, len(series))
    charts1.append(figure("Body temperature in winter on seasonal land (C)",
                          "Mean over body-steps. Dashed: 15 C, the band's floor. Under Y alone bodies pay to stay warm.", to_svg(fig)))

    bins = list(range(300, 3100, 100))
    # p90 of grown life by place, per run: a grouped bar chart.
    fig, ax = new_axes("")
    groups = [0, 1, 2]
    width = 0.2
    for i, (run, label, slot) in enumerate(RUNS):
        vals = []
        for c in groups:
            ages = sorted(int(r["age"]) for r in grown[run] if int(r["class"]) == c)
            vals.append(ages[int(0.9 * len(ages))] if ages else 0)
        ax.bar([g + (i - 1.5) * width for g in groups], vals, width * 0.92, color=SERIES[slot], label=label)
    ax.axhline(1200, color=INK, linewidth=0.8, linestyle="--")
    ax.set_xticks(groups, [CLASS[c] for c in groups])
    ax.yaxis.set_major_formatter(kfmt)
    ax.yaxis.set_major_locator(MaxNLocator(4))
    ax.margins(x=0.02)
    legend_above(ax, 2)
    charts2.append(figure("p90 of grown age at death, by where it died",
                          "Dashed: a year. Most grown deaths are in the sea and on the land always fed.", to_svg(fig)))

    series = []
    for run, label, slot in RUNS:
        tot = lambda r: sum(float(r[f"steps_{c}"]) for c in ("sea", "fed", "seasonal", "never"))  # noqa: E731
        xs, ys = windows(months[run], lambda r: float(r["steps_seasonal"]), tot)
        series.append((label, ys, slot))
    fig, ax = new_axes()
    for label, ys, slot in series:
        ax.plot(xs, ys, color=SERIES[slot], linewidth=1.6, label=label)
    ax.set_ylim(0, 0.2)
    ax.yaxis.set_major_formatter(lambda y, _p: f"{y:.0%}")
    ax.yaxis.set_major_locator(MaxNLocator(4))
    legend_above(ax, 2)
    charts3.append(figure("Body-steps on seasonal land",
                          "Share of all body-steps, per 5,000 steps. The seasonal land is 31% of the land.", to_svg(fig)))
    causes = ["hunger", "thirst", "wound", "suffocation"]
    fig, ax = new_axes("")
    for i, (run, label, slot) in enumerate(RUNS):
        n = max(len(grown[run]), 1)
        cnt = {c: 0 for c in range(7)}
        for r in grown[run]:
            cnt[int(r["cause"])] += 1
        vals = [cnt[0] / n, cnt[3] / n, cnt[6] / n, cnt[4] / n]
        ax.bar([k + (i - 1.5) * width for k in range(4)], vals, width * 0.92, color=SERIES[slot], label=label)
    ax.set_xticks(range(4), causes)
    ax.yaxis.set_major_formatter(lambda y, _p: f"{y:.0%}")
    ax.yaxis.set_major_locator(MaxNLocator(4))
    ax.margins(x=0.02)
    legend_above(ax, 2)
    charts3.append(figure("What grown bodies die of",
                          "Share of grown deaths, 36,000-100,000. None die of cold under Q; 6% did under Y alone.", to_svg(fig)))

    ctrl = {"9": (7.45, 4.75, 0.58), "10": (8.27, 4.65, 0.63), "11": (7.25, 4.47, 0.42)}
    body = ""
    for run, label, _ in RUNS:
        r = read[run]
        seed = run.split("life")[1].split("_")[0]
        body += (f"<tr><td>{label}</td><td>{float(r['lived']):.0%}</td><td>{float(r['grown_p90']):.0f}</td>"
                 f"<td>{float(r['torpid_winter']):.0%}</td><td>{float(r['kinds_at']):.2f}</td><td>{float(r['placed_at']):.2f}</td>"
                 f"<td>{float(r['top_share']):.0%}</td><td>{float(r['pop']):,.0f}</td></tr>")
    for seed, (k, p, t) in ctrl.items():
        body += f"<tr><td>control seed {seed} (e081, year 11,880)</td><td>-</td><td>-</td><td>-</td><td>{k:.2f}</td><td>{p:.2f}</td><td>{t:.0%}</td><td>{float(read[f'c1225_life{seed}_u0']['pop']):,.0f}</td></tr>" if f"c1225_life{seed}_u0" in read else ""

    appendix = "".join(
        f"<tr><td>{label}</td><td>{float(read[run]['fat_in']):.0f}</td><td>{float(read[run]['moved']):.1f}</td><td>{float(read[run]['fed_end']):.0%}</td>"
        f"<td>{float(read[run]['grown_p50']):.0f}</td><td>{float(read[run]['grown_seasonal_p50']):.0f} / {float(read[run]['grown_seasonal_p90']):.0f}</td>"
        f"<td>{float(read[run]['torpid_fed']):.0%}</td><td>{float(read[run]['young']):.0%}</td><td>{float(read[run]['travel']):.1f}</td>"
        f"<td>{float(read[run]['err']):.1e}</td></tr>" for run, label, _ in RUNS)

    text = TEXT.format(diagram=DIAGRAM, table=body, charts1="".join(charts1), charts2="".join(charts2),
                       charts3="".join(charts3), gallery=gallery(cls), appendix=appendix)
    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>e087 Torpor - Report</title>
<style>{CSS}</style>
</head>
<body>
<main>
{text}
</main>
</body>
</html>
"""
    out = os.path.join(HERE, "report.html")
    with open(out, "w") as f:
        f.write(page)
    import re
    words = len(re.sub(r"<[^>]+>|\{\w+\}", " ", TEXT).split())
    print(f"wrote {out} ({os.path.getsize(out)//1024} KB), about {words} words of text")


TEXT = """<h1>e087: can a body live through a winter?</h1>
<p class="sub">Experiment report - 2026-09-20 - a year of 1,200 steps, and a flesh that slows when cold, on c1225, three seeds, 100,000 steps</p>

<section class="tldr">
<h2>TL;DR</h2>
<p>Yes. When cold slows the flesh, 81-84% of the grown bodies on seasonal land at a winter's start are alive at its end; 36% under the year alone. They wait torpid on their fat and do not travel. A year is still not lived: the p90 of a grown body's age at death stays at 870-930 steps. Grown bodies die of hunger, thirst and wounds in the crowd, outside the winter. Kinds kept to a place fall in every seed.</p>
</section>

<h2>1. Question</h2>
<p>A grown body lived 1/20 of a year, so no body met a season. #93 shortens the year to 1,200 steps (winter about 400) and adds Q: a cold body takes fewer turns. Its done-when, on seeds 9-11:</p>
<ol>
  <li><strong>A winter lived through:</strong> 25% or more of the cohort.</li>
  <li><strong>A year lived:</strong> grown age at death p90 of 1,200 or more.</li>
  <li><strong>The season changes behaviour:</strong> 30% of winter body-steps torpid, or travel of 15 cells.</li>
  <li><strong>No harm:</strong> kinds not below e081's lowest control seed.</li>
</ol>

<h2>2. The world</h2>
<p>Stage C's default world (e082's) at a year of 1,200 steps. Under Q, set A's paid warming and death by cold go.</p>
{diagram}
<p><strong>Runs.</strong> Y+Q on seeds 9, 10, 11 and Y alone on seed 9, 100,000 steps, read from 36,000. Controls: e081's runs at the old year. Places come from e086's map at this year.</p>
<ul class="measures">
  <li><strong>Grown</strong> - 300 steps or older.</li>
  <li><strong>Seasonal land</strong> - lean 1-11 months a year (31% of the land); its winter is its longest lean run.</li>
  <li><strong>Winter cohort</strong> - grown bodies on a seasonal cell when its winter starts; read when it ends.</li>
  <li><strong>Torpid</strong> - at most half its clock (under about 7.4 C).</li>
  <li><strong>Kinds</strong> - ways of living at a census, and those kept to a place (e068, e075).</li>
</ul>

<h2>3. Results</h2>
<div class="tw"><table>
<thead><tr><th>run</th><th>winter lived</th><th>grown p90</th><th>torpid in winter</th><th>kinds</th><th>kept to a place</th><th>largest line</th><th>bodies</th></tr></thead>
<tbody>{table}</tbody></table></div>
<ol class="verdicts">
<li><span class="verdict">Yes</span> 1. A winter lived through: 81-84% of the cohort (Y alone 36%).</li>
<li><span class="verdict no">No</span> 2. A year lived: p90 869-926 steps against 1,200.</li>
<li><span class="verdict">Yes</span> 3. The season changes behaviour: 96% of winter body-steps torpid. Travel over the winter is 1-2 cells.</li>
<li><span class="verdict no">No</span> 4. No harm: kinds kept to a place 1.90-3.86 against 4.47; kinds at a census fall on seeds 10 and 11.</li>
</ol>

<h3>3.1 The winter is waited out, not escaped</h3>
<div class="grid2">
{charts1}
</div>
<p>Under Q a body in winter sits near -10 C, takes a tenth of its turns and spends a tenth of its fat. It enters with about 150 steps of fasting and so holds for about 1,500 steps, longer than any winter. The survivors end 1-2 cells from where they began; the spring comes to them.</p>

<h3>3.2 A year is not lived, because grown bodies die in the crowd</h3>
<div class="grid2">
{charts2}
</div>
<p>Q lengthens grown life on seasonal land (seed 9: median 478 to 608) and shortens it on the land always fed (p90 984 to 753). Most grown deaths are in the sea and on the land always fed, of hunger, thirst and wounds: there the crowd ends a grown life.</p>

<h3>3.3 Q doubles the use of seasonal land</h3>
<div class="grid2">
{charts3}
</div>
<p>A body that can wait makes the seasonal land a home: 13% of body-steps against 7%. Grown bodies still die of hunger, thirst and wounds, and none of cold.</p>

<h3>3.4 The oldest bodies</h3>
{gallery}

<h2>4. Discussion</h2>
<p>Q works as designed: the cold now slows a body instead of taxing it, and waiting is the answer to the winter. Nothing asks a body to leave, and none does. A cohort enters with about ten times the fat a torpid winter takes, so F (the store filling from the surplus) would not change this result.</p>
<p>The done-when assumed the winter was what ended a grown life. It is not: grown bodies die of hunger, thirst and wounds wherever they live, as before. e037 and e038 found the crowd pins a body's income at the world's regrowth. A longer life needs a world where a grown body is not at that edge.</p>
<p>Kinds kept to a place fall on all three seeds. Y alone falls too on its one seed (kinds 5.78), so part of the loss is the year's. This batch cannot split the two.</p>

<h2>5. Conclusion and next step</h2>
<p>Keep Q's mechanism; P1 is not done (criteria 2 and 4 fail). Y and Q do not become the default world. The gap left is the crowd: a grown body's income, not the season, sets its life. The next step is chosen from <code>vision.md</code>: one redesign within P1's budget, or P2 first.</p>

<h2>Appendix: data</h2>
<p>Steps 36,000-100,000. Fat: steps of fasting at full pace when a cohort starts. Travel: grown bodies' distance from birth at a census. Full data in <code>results/batch/*_months.csv</code> and <code>_grown.csv</code>; build with <code>uv run python experiments/e087_torpor/report.py</code>.</p>
<details><summary>More measures</summary><div class="tw"><table>
<thead><tr><th>run</th><th>fat at winter start</th><th>moved in winter</th><th>on fed land after</th><th>grown p50</th><th>seasonal p50 / p90</th><th>torpid, fed land</th><th>dead by 75 steps</th><th>travel</th><th>ledger error</th></tr></thead>
<tbody>{appendix}</tbody></table></div></details>
"""


if __name__ == "__main__":
    main()
