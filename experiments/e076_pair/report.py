#!/usr/bin/env python3
"""Build report.html for this experiment.

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
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#898781"]  # fixed slot order; the last is the donor world, in chrome gray

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

ROOT = os.path.dirname(os.path.dirname(HERE))
RESULTS = os.path.join(HERE, "results")
SEEDS = (9, 10, 11)
DONOR_KILLS = 27.4  # % of all food that is the flesh of the living in e075's kept runs, which the donors repeat
KEPT_POP = 9099     # bodies in e075's kept runs
INJECT = 10000
KIND_COLOR = {1: SERIES[0], 2: SERIES[1], 3: SERIES[3], 4: SERIES[2]}  # hard, muscle, sensor, gut


def rows_of(path):
    with open(path) as f:
        return list(csv.DictReader(f))


def runs():
    return rows_of(os.path.join(RESULTS, "invade.csv"))


def log_of(name):
    return rows_of(os.path.join(RESULTS, "invade", name + "_log.csv"))


def series_of(rows, key):
    return [float(r[key]) for r in rows]


def kills_share(rows):
    return [100 * float(r["kill_intake"]) / max(float(r["plant_intake"]) + float(r["meat_intake"]), 1e-9) for r in rows]


def donor_shares(rows):
    """The donor world's share of grown bodies living the hunter's and the grazer's way, as invade.py read it."""
    return {s: next((float(r["donor_hunters"]), float(r["donor_grazers"])) for r in rows if int(r["seed"]) == s) for s in SEEDS}


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



def thin_chart(title, subtitle, xs, groups, ylabel):
    """groups: list of (label, [ys, ...], slot) - one thin line per run, one legend entry per group."""
    fig, ax = new_axes()
    for label, many, slot in groups:
        for i, ys in enumerate(many):
            ax.plot(xs, ys, color=SERIES[slot], linewidth=1.1, alpha=0.8, label=label if i == 0 else None)
    ax.set_ylabel(ylabel)
    ax.yaxis.set_major_formatter(kfmt)
    ax.yaxis.set_major_locator(MaxNLocator(4))
    legend_above(ax, len(groups))
    return figure(title, subtitle, to_svg(fig))


def bar_chart(title, subtitle, labels, groups, ylabel):
    """groups: list of (label, values, slot), one bar per label in each group."""
    fig, ax = plt.subplots(figsize=(6.4, 2.6))
    n = len(groups)
    width = 0.8 / n
    for i, (label, vals, slot) in enumerate(groups):
        xs = [j + (i - (n - 1) / 2) * width for j in range(len(labels))]
        ax.bar(xs, vals, width=width * 0.9, color=SERIES[slot], label=label)
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, fontsize=8.5)
    ax.set_ylabel(ylabel)
    ax.yaxis.set_major_formatter(kfmt)
    ax.yaxis.set_major_locator(MaxNLocator(4))
    legend_above(ax, n)
    return figure(title, subtitle, to_svg(fig))


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
.grid2 + .grid2 { margin-top: 20px; }
.fig { margin: 0; background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 14px 14px 8px; }
.fig svg { width: 100%; height: auto; display: block; font-family: system-ui, -apple-system, "Segoe UI", sans-serif; }
figcaption strong { display: block; font-size: 15px; }
figcaption span { display: block; color: var(--ink2); font-size: 13px; min-height: 2.6em; margin-bottom: 6px; }
.diagram { margin: 12px 0; background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 12px 16px 8px; color: var(--ink); }
.diagram figcaption { color: var(--ink2); font-size: 13px; margin-top: 4px; }
.cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 16px; }
.card { margin: 0; display: flex; gap: 12px; align-items: flex-start; }
.card figcaption { font-size: 12px; color: var(--ink2); }
.card figcaption strong { color: var(--ink); font-size: 12.5px; display: inline; }
.measures { columns: 2; column-gap: 24px; max-width: none; padding-left: 20px; } .measures li { break-inside: avoid; }
table { border-collapse: collapse; font-size: 13.5px; font-variant-numeric: tabular-nums; }
th, td { padding: 6px 10px; text-align: right; border-bottom: 1px solid var(--grid); }
th:first-child, td:first-child { text-align: left; }
td { white-space: nowrap; }
th { color: var(--ink2); font-weight: 600; }
.tw { overflow-x: auto; }
details { margin: 8px 0; } summary { cursor: pointer; color: var(--ink2); }
.verdicts { list-style: none; padding: 0; margin: 12px 0 0; } .verdicts li { margin: 4px 0; }
.verdict { display: inline-block; padding: 1px 8px; border-radius: 4px; font-size: 12.5px; font-weight: 600; background: rgba(12,163,12,0.12); color: #0ca30c; }
.verdict.no { background: rgba(208,59,59,0.12); color: #e66767; }
.verdict.partly { background: rgba(250,178,25,0.15); color: #fab219; }
"""


# Hand-written mechanism diagram: the test, and the one thing it found.
DIAGRAM = """
<figure class="diagram">
<svg viewBox="0 0 780 190" role="img" aria-label="Genomes of a finished run seed a world of one kind; two marked lines are injected into it and followed" style="max-width:100%;height:auto;display:block">
<defs><marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="currentColor"/></marker>
<marker id="arrb" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="var(--s1)"/></marker></defs>
<g fill="none" stroke="currentColor" stroke-width="1.2" font-size="12" font-family="system-ui, sans-serif">
  <rect x="8" y="48" width="140" height="62" rx="6"/>
  <text x="78" y="73" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">donor run</text>
  <text x="78" y="90" text-anchor="middle" fill="currentColor" stroke="none">e075's world, 100k</text>
  <line x1="148" y1="79" x2="186" y2="79" marker-end="url(#arr)"/>
  <text x="167" y="22" text-anchor="middle" fill="currentColor" stroke="none">1,400-2,300</text>
  <text x="167" y="36" text-anchor="middle" fill="currentColor" stroke="none">genomes</text>

  <rect x="188" y="48" width="206" height="62" rx="6"/>
  <text x="291" y="68" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">two kinds</text>
  <text x="291" y="85" text-anchor="middle" fill="currentColor" stroke="none">hunter: tooth, kills 45-53%</text>
  <text x="291" y="101" text-anchor="middle" fill="currentColor" stroke="none">grazer: no tooth, kills 6-12%</text>
  <line x1="394" y1="79" x2="430" y2="79" marker-end="url(#arr)"/>
  <text x="412" y="22" text-anchor="middle" fill="currentColor" stroke="none">9,000</text>
  <text x="412" y="36" text-anchor="middle" fill="currentColor" stroke="none">seeded</text>

  <rect x="432" y="48" width="150" height="62" rx="6" stroke="var(--s1)" stroke-width="2"/>
  <text x="507" y="73" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">a world of one kind</text>
  <text x="507" y="90" text-anchor="middle" fill="currentColor" stroke="none">10,000 steps alone</text>
  <line x1="582" y1="79" x2="620" y2="79" marker-end="url(#arr)"/>
  <text x="601" y="22" text-anchor="middle" fill="currentColor" stroke="none">100 + 100</text>
  <text x="601" y="36" text-anchor="middle" fill="currentColor" stroke="none">marked</text>

  <rect x="622" y="48" width="150" height="62" rx="6"/>
  <text x="697" y="73" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">30,000 steps</text>
  <text x="697" y="90" text-anchor="middle" fill="currentColor" stroke="none">invader vs control</text>

  <path d="M507,110 L507,158" stroke="var(--s1)" stroke-width="2" marker-end="url(#arrb)"/>
  <text x="494" y="140" text-anchor="end" fill="var(--s1)" stroke="none">grazers with no tooth: no hunter in 40,000 steps</text>
  <text x="494" y="158" text-anchor="end" fill="currentColor" stroke="none">(a tooth in one grazer of eight: back by 20,000)</text>
  <text x="520" y="140" fill="currentColor" stroke="none">hunters: grazers back</text>
  <text x="520" y="158" fill="currentColor" stroke="none">within 10,000</text>
</g>
</svg>
<figcaption>Figure 1. The genomes of a finished run are sorted into two kinds. A new world is seeded with one
kind alone and left for 10,000 steps; then a hundred bodies of each kind go in, marked, and their descendants
are followed. The blue arrow is the answer to #92: what the world of one kind makes on its own.</figcaption>
</figure>
"""


def gallery(bodies, caption, n=2):
    """One birth body of each kind of the donor runs, drawn on its grid, with the kind's median walk."""
    walk = {(k["run"], t): float(k[f"{t}_travel"]) for k in rows_of(os.path.join(RESULTS, "kinds.csv")) for t in ("A", "B")}
    cards = []
    for r in bodies:
        side, cells = int(r["side"]), r["cells"]
        px = 88 // max(side, 1)
        rects = "".join(
            f'<rect x="{(i % side) * px}" y="{(i // side) * px}" width="{px - 1}" height="{px - 1}" fill="{KIND_COLOR[int(k)]}"/>'
            for i, k in enumerate(cells[: side * side]) if k != "0")
        who = "the hunter" if r["tag"] == "B" else "the grazer"
        seed = r["run"].split("_")[1].replace("life", "seed ")
        cards.append(f"""<figure class="card"><svg viewBox="-1 -1 89 89" width="104" height="104" role="img" aria-label="{who}, {seed}">
<rect x="-1" y="-1" width="89" height="89" fill="var(--grid)"/>{rects}</svg>
<figcaption><strong>{who}, {seed}</strong><br>{html.escape(r['way'])}<br>
{int(r['born_size'])} blocks: {r['born_hard']} hard, {r['born_muscle']} muscle, {r['born_digestive']} gut<br>
bite {r['born_bite']}; the kind walks {walk[(r['run'], r['tag'])]:.1f} cells</figcaption></figure>""")
    return f"""<figure class="diagram"><div class="cards">{"".join(cards)}</div>
<figcaption>Figure {n}. {html.escape(caption)}</figcaption></figure>"""


def marker_chart(title, subtitle, xs, series, ylabel, pct=True):
    """series: list of (label, ys, slot, dashed) - a line with a dot at each census."""
    fig, ax = new_axes()
    for label, ys, slot, dashed in series:
        ax.plot(xs, ys, color=SERIES[slot], linewidth=1.6, label=label, marker=None if dashed else "o", markersize=4,
                linestyle="--" if dashed else "-")
    ax.set_ylim(0, max(v for _, ys, _, _ in series for v in ys) * 1.15)
    ax.set_ylabel(ylabel)
    if pct:
        ax.yaxis.set_major_formatter(lambda y, _p: f"{y:.0f}%")
    ax.yaxis.set_major_locator(MaxNLocator(4))
    ax.margins(x=0.03)
    legend_above(ax, len(series))
    return figure(title, subtitle, to_svg(fig))


def main():
    rows = runs()
    logs = {r["run"]: log_of(r["run"]) for r in rows}
    donors = donor_shares(rows)
    f = lambda r, k: float(r[k])  # noqa: E731
    first = logs[rows[0]["run"]]
    early = [int(r["step"]) for r in first if int(r["step"]) <= INJECT]
    late = [int(r["step"]) for r in first if int(r["step"]) >= INJECT]
    steps = [int(r["step"]) for r in first]
    censuses = [10000, 20000, 30000, 40000]
    tags = ["at_inject", "20k", "30k", "end"]

    def run_of(seed, world, draw=1):
        return next(r for r in rows if int(r["seed"]) == seed and r["world"] == world and int(r["draw"]) == draw)

    def upto(name, n):
        return [r for r in logs[name] if int(r["step"]) <= n]

    def mean_draws(seed, world, key):
        rs = [r for r in rows if int(r["seed"]) == seed and r["world"] == world]
        return sum(f(r, key) for r in rs) / len(rs)

    # 3.1 What came back before the injection (the two draws are one run up to step 10,000).
    charts1 = [
        line_chart("In the grazer's world, bodies eat each other from the start",
                   f"Share of all the food that is the flesh of the living, before any injection. The flat line is "
                   f"the donor world ({DONOR_KILLS}%). Killing needs no tooth: a soft face breaks under any push.",
                   early, [(f"seed {s}", kills_share(upto(run_of(s, "oA")["run"], INJECT)), 2 + i) for i, s in enumerate(SEEDS)]
                   + [("donor world", [DONOR_KILLS] * len(early), 5)], ymin=0),
        marker_chart("The hunter's way comes back only where a tooth was already there",
                     "Grown residents living the hunter's way (a tooth, roaming, a third of their food flesh, on "
                     "the land), mean of two draws. Seeds 9 and 11 lie together at zero. Dashed: the donor world.",
                     censuses, [(f"seed {s}", [100 * mean_draws(s, "oA", f"res_hunters_{t}") for t in tags], 2 + i, False)
                                for i, s in enumerate(SEEDS)]
                     + [("donor", [100 * sum(d[0] for d in donors.values()) / 3] * 4, 5, True)], "of the residents"),
    ]
    charts1b = [
        marker_chart("In the hunter's world the grazer's way is back by step 10,000",
                     "Grown bodies of the residents living the grazer's way (a plant eater with no tooth that stays, "
                     "out of the surface), mean of the two draws. Dashed: the donor world.",
                     censuses, [(f"seed {s}", [100 * mean_draws(s, "oB", f"res_grazers_{t}") for t in tags], 2 + i, False)
                                for i, s in enumerate(SEEDS)]
                     + [("donor", [100 * sum(d[1] for d in donors.values()) / 3] * 4, 5, True)], "of the residents"),
        thin_chart("Without a hunter the crowd doubles",
                   f"Bodies alive in the grazer's worlds, one line per run. e075's kept runs hold {KEPT_POP:,}. "
                   "The injection is at step 10,000.",
                   steps, [(f"seed {s}", [series_of(logs[r["run"]], "pop") for r in rows if int(r["seed"]) == s and r["world"] == "oA"], 2 + i)
                           for i, s in enumerate(SEEDS)], "bodies"),
    ]

    def lines_of(world, mark, seed=None):
        return [[float(r[f"inv{mark}"]) for r in logs[n] if int(r["step"]) >= INJECT]
                for n in logs if f"_{world}_" in n and (seed is None or f"life{seed}_" in n)]

    charts2 = [
        thin_chart("The grazer's world: the hunter's line booms, then wins or dies",
                   "Six runs, each with both lines in it, a hundred bodies of each at step 10,000. A line at zero has gone out.",
                   late, [("the hunter (invader)", lines_of("oA", 2), 1), ("the grazer (control)", lines_of("oA", 1), 0)],
                   "bodies"),
        thin_chart("The hunter's world: the grazer's line takes it over",
                   "The six runs of the other world. The hunter's own genomes shrink in the world they came from.",
                   late, [("the grazer (invader)", lines_of("oB", 1), 0), ("the hunter (control)", lines_of("oB", 2), 1)],
                   "bodies"),
    ]
    labels, hunter, grazer = [], [], []
    for world in ("oA", "oB"):
        for s in SEEDS:
            labels.append(f"{'grazers' if world == 'oA' else 'hunters'}\nseed {s}")
            hunter.append(mean_draws(s, world, "hunter_end"))
            grazer.append(mean_draws(s, world, "grazer_end"))
    charts3 = [
        bar_chart("Each line against the other, by the world it entered",
                  "Mean bodies over the last 5,000 steps, two draws a bar. In a world of grazers the hunter's line is "
                  "the invader; in a world of hunters the grazer's is. Equal bars: the invader is worth no more.",
                  labels, [("the hunter's line", hunter, 1), ("the grazer's line", grazer, 0)], "bodies"),
    ]

    PAGE = build_page(rows, donors, charts1, charts1b, charts2, charts3, f)
    out = os.path.join(HERE, "report.html")
    with open(out, "w") as fh:
        fh.write(PAGE)
    print(f"wrote {out} ({os.path.getsize(out)//1024} KB)")


def build_page(rows, donors, charts1, charts1b, charts2, charts3, f):
    bodies = rows_of(os.path.join(RESULTS, "bodies.csv"))
    gal = gallery(bodies, "The two kinds of each donor world, one birth body each. Blue hard, orange muscle, aqua gut. "
                          "The hunter's hard front row is its tooth; the grazer of seeds 9 and 11 has no muscle at all.", n=2)
    return TEMPLATE.format(CSS=CSS, DIAGRAM=DIAGRAM, GALLERY=gal, TABLE=table_of(rows, f),
                           CHARTS1="".join(charts1), CHARTS1B="".join(charts1b), CHARTS2="".join(charts2),
                           CHARTS3="".join(charts3), APPENDIX=appendix_of(rows))


def table_of(rows, f):
    out = ""
    for s in SEEDS:
        for world, name, inv, ctl in (("oA", "grazers", "hunter", "grazer"), ("oB", "hunters", "grazer", "hunter")):
            rs = [r for r in rows if int(r["seed"]) == s and r["world"] == world]
            if not rs:
                continue
            key = "res_hunters" if world == "oA" else "res_grazers"
            back = "yes" if rs[0]["back_at_inject"] != "-" else "no"
            invs = " / ".join(f"{f(r, inv + '_end'):,.0f}" for r in rs)
            ctls = " / ".join(f"{f(r, ctl + '_end'):,.0f}" for r in rs)
            out += (f"<tr><td>{s}</td><td>{name}</td><td>{f(rs[0], 'kills_10k'):.0%}</td><td>{back}</td>"
                    f"<td>{f(rs[0], key + '_at_inject'):.1%}</td><td>{sum(f(r, key + '_end') for r in rs) / len(rs):.1%}</td>"
                    f"<td>{invs}</td><td>{ctls}</td><td>{sum(f(r, 'pop_mean') for r in rs) / len(rs):,.0f}</td></tr>")
    return out


def appendix_of(rows):
    cols = ["draw", "kills_10k", "res_hunters_at_inject", "res_hunters_end", "res_grazers_at_inject", "res_grazers_end",
            "hunter_end", "grazer_end", "hunter_kills", "grazer_kills", "kinds_at", "pop_mean", "pop_min"]
    return data_table(cols, {f"seed {r['seed']}, {'the grazer' if r['world'] == 'oA' else 'the hunter'}'s world":
                             {k: [float(x[k]) for x in rows if x["seed"] == r["seed"] and x["world"] == r["world"]] for k in cols}
                             for r in rows}, every=1)


TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>e076 The hunter and the grazer - Report</title>
<style>{CSS}</style>
</head>
<body>
<main>
<h1>e076: can a world of grazers make a hunter?</h1>
<p class="sub">Experiment report - 2026-09-18 - 3 donor runs and 12 invasion runs on c1225, seeds 9-11</p>

<section class="tldr">
<h2>TL;DR</h2>
<p>Not when no grazer carries a tooth. Toothless grazers eat flesh again within a thousand steps, yet in
40,000 steps at most 0.1% of them live as hunters. A hundred injected hunters take half the same world
and bring its doubled crowd back to the kept level. Where one grazer in eight has a tooth, the hunter
returns in 20,000 steps; a hunter's world grows grazers in under 10,000. Next: #91, the forest as a
refuge.</p>
</section>

<h2>1. Question</h2>
<p>e074 could not hold a world at one way of living. The missing way came back in ten lives, because one
body in twenty already carried its tooth. e075 made a pair further apart: a land hunter with a tooth,
and a shore grazer that on two seeds has neither a tooth nor muscle. Does the gap between what a world
can hold and what evolution finds in it open for this pair?</p>
<ol>
  <li><strong>The gap.</strong> A grazer's world eats flesh again by step 10,000, but has no hunter kind.</li>
  <li><strong>No gap the other way.</strong> A hunter's world has a grazer kind by step 10,000.</li>
  <li><strong>The hunter invades.</strong> In the grazer's world its line ends above the grazer's own, on 2 seeds of 3.</li>
  <li><strong>The world stands.</strong> Matter conserved, all three media, the crowd within a fifth of 9,099.</li>
</ol>

<h2>2. The test</h2>
<p>No law is added. A finished run writes out every body's genome; a new world is seeded from those of
one kind, each body where its donor stood; at step 10,000 a hundred bodies of both kinds go in, marked,
and every descendant carries the mark.</p>
{DIAGRAM}
<p><strong>Runs.</strong> Three donor runs of e075's kept world (they reproduce it exactly), then 12 runs
of 40,000 steps: the grazer's world and the hunter's world, times three seeds, times two founder draws.
We record:</p>
<ul class="measures">
  <li><strong>Kills</strong> - the flesh of the living, as a share of all food.</li>
  <li><strong>The other way</strong> - residents living the other kind's way, one body at a time.</li>
  <li><strong>Kinds</strong> - e068's count by birth form, at the census of step 10,000.</li>
  <li><strong>The two lines</strong> - bodies of each mark, and what they eat.</li>
</ul>
{GALLERY}

<h2>3. Results</h2>
<div class="tw"><table>
<thead><tr><th>seed</th><th>world of</th><th>kills, 10k</th><th>other way a kind, 10k</th>
<th>residents living it, 10k</th><th>end</th><th>invader's line</th><th>control's line</th><th>bodies</th></tr></thead>
<tbody>{TABLE}</tbody></table></div>
<ol class="verdicts">
<li><span class="verdict">Yes</span> <strong>The gap:</strong> kills are back at 16-23% on 3 seeds of 3; no hunter kind at step 10,000 on 3 of 3.</li>
<li><span class="verdict">Yes</span> <strong>No gap the other way:</strong> a grazer kind at step 10,000 on 3 seeds of 3 (95-197 bodies).</li>
<li><span class="verdict">Yes</span> <strong>The hunter invades:</strong> 5,305 against 487 and 5,640 against 0; on seed 10, 0 against 1,218.</li>
<li><span class="verdict">Yes</span> <strong>The world stands:</strong> matter to 4.7e-14, all three media, 8,077-10,521 bodies after the injection.</li>
</ol>

<h3>3.1 Killing comes back at once; the hunter only where a tooth was there</h3>
<div class="grid2">
{CHARTS1}
</div>
<p>Killing needs no tooth: bodies that sit in a crowd break each other's soft faces. The hunter needs a
tooth and muscle. Seed 10's grazer carries a tooth in 13% of its bodies, and its world has as many
hunters as the donor by step 20,000. Seeds 9 and 11's grazer is all gut: its residents never pass 1.6%
with a tooth, and at most 0.1% live the hunter's way at any census.</p>

<h3>3.2 The other direction is quick, and a world without a hunter is twice as crowded</h3>
<div class="grid2">
{CHARTS1B}
</div>
<p>A hunter's world drops half its teeth and grows grazers within 10,000 steps: losing a part is quick.
The toothless grazer's world doubles to 17,788 and 20,030 bodies. The kept world's 9,099 is a world
with a predator in it.</p>

<h3>3.3 Where the world had no hunter, the injected one takes half of it</h3>
<div class="grid2">
{CHARTS2}
</div>
<div class="grid2">
{CHARTS3}
</div>
<p>On seeds 9 and 11 a hundred hunters are 4,000-7,200 bodies 2,000 steps later and hold half the world to
the end, keeping a tooth in 48-71% of their bodies. On seed 10, where the residents already hunt, the
injected line booms and is gone by step 32,000. The grazer beats the hunter's own genomes in the
hunter's world on 3 seeds of 3.</p>

<h2>4. Discussion</h2>
<p>For this pair the gap opens, and in one direction. The same world that lets a hundred hunters take
half of it does not make a hunter out of its own toothless grazers in 10,000 steps, nor in the 30,000
after. A hunter's world makes grazers in under 10,000. What decides it is not how much the way pays but
whether the population carries its parts: a tooth in one body in eight is found in 20,000 steps; a
tooth and muscle in none is not found in 40,000.</p>
<p>That qualifies e074's lesson. "Do not read a seed's outcome as reachability" holds for close pairs; a
world that has lost a part - through a bottleneck, a seeded start or a long spell of grazing - can stay
without a way it would hold. The injection, with its control beside it, is what tells the two apart.</p>
<p>It does not show whether a longer run without the injection makes the hunter in the end (only 10,000
steps were free of it), nor how rare a tooth may be before it is lost.</p>

<h2>5. Conclusion and next step</h2>
<p>A hunter is held by this world and not found from toothless grazers: what evolution reaches is set by
the parts the population carries. The hunter also holds the crowd, at half what grazers alone reach.
Before rejecting a law because a way did not appear, seed the world with the kinds it is meant to favour.
Next is #91: is a standing forest a refuge a lawn cannot hold.</p>

<h2>Appendix: data</h2>
<p>Every run, by seed and world. The full data is in <code>results/invade.csv</code> and
<code>results/kinds_invade.csv</code>, the logs in <code>results/invade/</code>; the pools, the kinds and
the bodies are rebuilt by <code>pick.py</code> from the donor runs. Build this report with
<code>uv run python experiments/e076_pair/report.py</code>.</p>
{APPENDIX}
</main>
</body>
</html>
"""


if __name__ == "__main__":
    main()
