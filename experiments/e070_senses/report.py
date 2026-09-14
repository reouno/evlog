#!/usr/bin/env python3
"""Build report.html for e070 (senses from sensor blocks, foundation stage C, eighth step, #84).

Charts: matplotlib, exported as SVG and inlined. Diagram: hand-written SVG.
Run from the repo root after senses.py: uv run python experiments/e070_senses/report.py
"""
import csv
import html
import io
import os

import matplotlib
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from matplotlib.ticker import FuncFormatter, MaxNLocator

matplotlib.use("svg")

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4"]  # fixed slot order
ARM_COLOR = {"given": SERIES[0], "senses": SERIES[1]}
ARM_LABEL = {"given": "senses given (control)", "senses": "senses from sensor blocks"}
SEED_STYLE = {9: "-", 10: (0, (4, 2)), 11: (0, (1, 1.5))}
SIDE_COLOR = {"front": SERIES[1], "back": SERIES[0], "left": SERIES[2], "right": SERIES[4]}
MEDIUM_COLOR = {"land": SERIES[3], "surface": SERIES[2], "bottom": SERIES[4], "shore": SERIES[0]}  # e067's and e068's
KIND_COLOR = {1: SERIES[0], 2: SERIES[1], 3: SERIES[3], 4: SERIES[2]}  # hard, muscle, sensor, gut: the viewer's
SEEDS = (9, 10, 11)
RUNS = [f"{arm}{s}" for s in SEEDS for arm in ("given", "senses")]
SIDES = ("front", "back", "left", "right")
LOGS = {"given9": os.path.join(ROOT, "experiments", "e067_breath", "results", "c1225_life9_breath0.01_log.csv")}
LOGS |= {f"given{s}": os.path.join(ROOT, "experiments", "e069_history", "results", f"c1225_life{s}_constants_log.csv") for s in (10, 11)}
LOGS |= {f"senses{s}": os.path.join(HERE, "results", f"c1225_life{s}_senses_log.csv") for s in SEEDS}

INK = "#898781"
plt.rcParams.update({
    "svg.fonttype": "none", "font.family": "sans-serif", "font.size": 9, "text.color": INK,
    "axes.edgecolor": INK, "axes.labelcolor": INK, "axes.facecolor": "none", "axes.spines.top": False,
    "axes.spines.right": False, "axes.spines.left": False, "axes.grid": True, "axes.grid.axis": "y",
    "grid.color": INK, "grid.alpha": 0.25, "grid.linewidth": 0.8, "xtick.color": INK, "ytick.color": INK,
    "ytick.left": False, "legend.frameon": False, "legend.fontsize": 9, "figure.facecolor": "none",
    "savefig.transparent": True,
})
DASHED = (0, (3, 2))


# ---------- data ----------

def rows(name, path=None):
    with open(path or os.path.join(HERE, "results", name + ".csv")) as f:
        return list(csv.DictReader(f))


def num(r):
    out = {}
    for k, v in r.items():
        try:
            out[k] = float(v)
        except (TypeError, ValueError):
            out[k] = v
    return out


R = {r["run"]: num(r) for r in rows("runs")}
T = [num(r) for r in rows("time")]
M = [num(r) for r in rows("media")]
K = rows("kinds")
L = {run: [num(r) for r in rows(None, path)] for run, path in LOGS.items()}


def arm(run):
    return "given" if run.startswith("given") else "senses"


def seed(run):
    return int(run.lstrip("givensn"))


# ---------- charts ----------

def to_svg(fig):
    buf = io.StringIO()
    fig.savefig(buf, format="svg", bbox_inches="tight", pad_inches=0.05)
    plt.close(fig)
    return buf.getvalue()


def legend_above(ax, n, **kw):
    ax.legend(loc="lower left", bbox_to_anchor=(0, 1.0), ncols=n, handlelength=1.8, borderaxespad=0, columnspacing=1.2, **kw)


def figure(title, subtitle, svg):
    return f"""
<figure class="fig">
  <figcaption><strong>{html.escape(title)}</strong><span>{html.escape(subtitle)}</span></figcaption>
  {svg}
</figure>"""


def percent(ax, axis="y"):
    (ax.yaxis if axis == "y" else ax.xaxis).set_major_formatter(lambda v, _p: f"{v:.0%}")


kfmt = FuncFormatter(lambda x, _p: f"{x / 1000:.0f}k" if x else "0")


def arm_handles():
    return ([Line2D([], [], color=ARM_COLOR[a], linewidth=1.6, label=ARM_LABEL[a]) for a in ARM_COLOR]
            + [Line2D([], [], color=INK, linewidth=1.2, linestyle=SEED_STYLE[s], label=f"seed {s}") for s in SEEDS])


def runs_lines(title, subtitle, points, key, ylabel, pct=False, line=None, ymax=None):
    """One line per run: colour by arm, line style by seed. `points` is a list of rows with run and step."""
    fig, ax = plt.subplots(figsize=(6.4, 2.8))
    for run in RUNS:
        ps = [p for p in points if p["run"] == run]
        if ps:
            ax.plot([p["step"] for p in ps], [p[key] for p in ps], color=ARM_COLOR[arm(run)], linestyle=SEED_STYLE[seed(run)], linewidth=1.5)
    if line is not None:
        ax.axhline(line, color=INK, linewidth=1, linestyle=DASHED)
    ax.set_ylim(0, ymax)
    ax.yaxis.set_major_locator(MaxNLocator(4))
    if pct:
        percent(ax)
    elif max((p[key] for p in points), default=0) >= 1000:
        ax.yaxis.set_major_formatter(kfmt)
    ax.xaxis.set_major_formatter(kfmt)
    ax.set_xlabel("step", loc="right")
    ax.set_ylabel(ylabel)
    legend_above(ax, 3, handles=arm_handles())
    return figure(title, subtitle, to_svg(fig))


def sides_chart(title, subtitle):
    """Sensor blocks looking out per grown body, to each side, per run."""
    fig, ax = plt.subplots(figsize=(6.4, 2.8))
    width = 0.8 / len(SIDES)
    for j, side in enumerate(SIDES):
        ax.bar([i - 0.4 + width * (j + 0.5) for i in range(len(RUNS))], [R[r][f"sight_{side}"] for r in RUNS], width=width * 0.92, color=SIDE_COLOR[side], label=side)
    ax.set_xticks(range(len(RUNS)), [f"{'given' if arm(r) == 'given' else 'sensors'}\nseed {seed(r)}" for r in RUNS])
    ax.set_ylim(0, None)
    ax.yaxis.set_major_locator(MaxNLocator(4))
    ax.set_ylabel("blocks looking out, per body")
    legend_above(ax, 4)
    return figure(title, subtitle, to_svg(fig))


def seeds_chart(title, subtitle, key, ylabel, line=None, integer=False):
    """One group per seed: the control and the run with the senses from sensor blocks."""
    fig, ax = plt.subplots(figsize=(6.4, 2.6))
    for j, a in enumerate(("given", "senses")):
        ax.bar([i - 0.2 + 0.4 * j for i in range(len(SEEDS))], [R[f"{a}{s}"][key] for s in SEEDS], width=0.37, color=ARM_COLOR[a], label=ARM_LABEL[a])
    if line is not None:
        ax.axhline(line, color=INK, linewidth=1, linestyle=DASHED)
    ax.set_xticks(range(len(SEEDS)), [f"seed {s}" for s in SEEDS])
    ax.set_ylim(0, None)
    ax.yaxis.set_major_locator(MaxNLocator(4, integer=integer))
    ax.set_ylabel(ylabel)
    legend_above(ax, 2)
    return figure(title, subtitle, to_svg(fig))


def short(k):
    diet, tooth, roams, medium = k["kind"].split(" / ")
    return f"{diet}, {roams}, {medium}" + (", tooth" if tooth == "tooth" else "")


def kinds_chart(title, subtitle, run):
    ks = sorted((k for k in K if k["run"] == run and float(k["share"]) >= 0.02), key=lambda k: float(k["share"]))
    fig, ax = plt.subplots(figsize=(6.4, 0.9 + 0.3 * len(ks)))
    for j, k in enumerate(ks):
        medium = k["kind"].split(" / ")[3]
        ax.barh(j, float(k["share"]), color=MEDIUM_COLOR[medium], alpha=1.0 if k["held"] == "True" else 0.4, height=0.72)
    ax.set_yticks(range(len(ks)), [short(k) for k in ks])
    ax.axvline(0.05, color=INK, linewidth=1, linestyle=DASHED)
    percent(ax, "x")
    ax.set_xlabel("share of the grown bodies", loc="right")
    ax.grid(axis="y", visible=False)
    ax.grid(axis="x", visible=True)
    handles = [Patch(color=MEDIUM_COLOR[m], label=m) for m in ("surface", "bottom", "land", "shore")]
    legend_above(ax, 4, handles=handles)
    return figure(title, subtitle, to_svg(fig))


def gallery(picks, caption):
    """(run, kind, title, what the shape does): the commonest intact birth body of the kind's largest form."""
    cards = []
    for run, kind, title, what in picks:
        k = next(x for x in K if x["run"] == run and x["kind"] == kind)
        side, cells = int(k["side"]), k["cells"]
        u = 88 / side
        rects = "".join(f'<rect x="{(i % side) * u:.2f}" y="{(i // side) * u:.2f}" width="{u * 0.9:.2f}" height="{u * 0.9:.2f}" fill="{KIND_COLOR[int(c)]}"/>'
                        for i, c in enumerate(cells) if c != "0")
        food = ", ".join(f"{name} {float(k[col]):.0%}" for name, col in (("grass", "grass"), ("algae", "algae"), ("litter", "detritus"), ("flesh", "meat")) if float(k[col]) >= 0.05)
        eye = f"sensor block in {float(k['eye_feeling']):.0%}, looking out in {float(k['eye_sighted']):.0%}"
        cards.append(f"""<figure class="card"><svg viewBox="-1 -1 89 89" width="120" height="120" role="img" aria-label="{html.escape(title)}"><rect x="-1" y="-1" width="89" height="89" fill="var(--cell)"/>{rects}<line x1="-1" y1="-0.5" x2="88" y2="-0.5" stroke="var(--ink2)" stroke-width="1.5" stroke-dasharray="3 2"/></svg>
<figcaption><strong>{html.escape(title)}</strong><br>seed {seed(run)}: {float(k['share']):.0%} of grown bodies, {k['censuses']} of 6 censuses; {k['forms']} forms<br>born with {float(k['born_size']):.0f} blocks, density {float(k['density']):.2f}; eats {food}<br>{eye}<br>{html.escape(what)}</figcaption></figure>""")
    return f"""<figure class="diagram"><div class="cards">{"".join(cards)}</div>
<figcaption>{html.escape(caption)}</figcaption></figure>"""


def table(name, cols, keep=lambda r: True):
    body = "".join("<tr>" + "".join(f"<td>{html.escape(str(r.get(c, ''))[:60])}</td>" for c in cols) + "</tr>" for r in rows(name) if keep(r))
    return (f"<details><summary>results/{name}.csv</summary><div class='tw'><table><thead><tr>"
            + "".join(f"<th>{c}</th>" for c in cols) + f"</tr></thead><tbody>{body}</tbody></table></div></details>")


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
@media (max-width: 480px) {{ .grid2 {{ grid-template-columns: 1fr; }} }}
.grid2 > .fig:only-child {{ max-width: 470px; }}
.fig {{ margin: 0; background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 14px 14px 8px; }}
.fig svg {{ width: 100%; height: auto; display: block; font-family: system-ui, -apple-system, "Segoe UI", sans-serif; }}
figcaption strong {{ display: block; font-size: 15px; }}
figcaption span {{ display: block; color: var(--ink2); font-size: 13px; min-height: 2.6em; margin-bottom: 6px; }}
.diagram {{ margin: 12px 0; background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 12px 16px 8px; color: var(--ink); }}
.diagram figcaption {{ color: var(--ink2); font-size: 13px; margin-top: 4px; }}
.cards {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 16px; }}
.card {{ margin: 0; display: grid; grid-template-columns: 120px 1fr; gap: 12px; align-items: start; }}
.card figcaption {{ font-size: 12.5px; color: var(--ink2); margin: 0; }} .card figcaption strong {{ display: inline; font-size: 13px; color: var(--ink); }}
.measures {{ columns: 2; column-gap: 24px; max-width: none; padding-left: 20px; }} .measures li {{ break-inside: avoid; }}
@media (max-width: 640px) {{ .measures {{ columns: 1; }} }}
table {{ border-collapse: collapse; font-size: 13.5px; font-variant-numeric: tabular-nums; }}
th, td {{ padding: 6px 10px; text-align: right; border-bottom: 1px solid var(--grid); }}
th:first-child, td:first-child {{ text-align: left; }}
th {{ color: var(--ink2); font-weight: 600; }}
.tw {{ overflow-x: auto; }}
details {{ margin: 8px 0; }} summary {{ cursor: pointer; color: var(--ink2); }}
.verdicts {{ list-style: none; padding: 0; margin: 12px 0 0; }} .verdicts li {{ margin: 4px 0; }}
.verdict {{ display: inline-block; padding: 1px 8px; border-radius: 4px; font-size: 12.5px; font-weight: 600; background: rgba(12,163,12,0.12); color: #006300; }}
.verdict.no {{ background: rgba(208,59,59,0.12); color: #a12b2b; }}
:root[data-theme="dark"] .verdict {{ color: #0ca30c; }} :root[data-theme="dark"] .verdict.no {{ color: #e66767; }}
@media (prefers-color-scheme: dark) {{ :root:not([data-theme="light"]) .verdict {{ color: #0ca30c; }} :root:not([data-theme="light"]) .verdict.no {{ color: #e66767; }} }}
"""


def box(x, y, w, h, title, lines, accent=False, dashed=False):
    stroke = ' stroke="var(--s1)" stroke-width="2"' if accent else ' stroke-dasharray="4 3"' if dashed else ""
    out = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6"{stroke}/>',
           f'<text x="{x + w / 2}" y="{y + 22}" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">{title}</text>']
    for i, line in enumerate(lines):
        out.append(f'<text x="{x + w / 2}" y="{y + 42 + 17 * i}" text-anchor="middle" fill="currentColor" stroke="none">{line}</text>')
    return "".join(out)


def label(x, y, text, anchor="middle"):
    return f'<text x="{x}" y="{y}" text-anchor="{anchor}" fill="currentColor" stroke="none">{text}</text>'


def body_svg(x0, y0, u):
    """The diagram's body: 6x6, front at the top. S: sensor, M: muscle, G: gut."""
    grid = [".MSMM.", ".GGGS.", ".GSGG.", ".GGGG.", ".M..M.", "......"]
    fill = {"M": KIND_COLOR[2], "S": KIND_COLOR[3], "G": KIND_COLOR[4]}
    out = [f'<rect x="{x0}" y="{y0}" width="{6 * u}" height="{6 * u}" fill="var(--cell)" stroke="none"/>']
    for r, row in enumerate(grid):
        for c, ch in enumerate(row):
            if ch != ".":
                out.append(f'<rect x="{x0 + c * u + 1}" y="{y0 + r * u + 1}" width="{u - 2}" height="{u - 2}" fill="{fill[ch]}" stroke="none"/>')
    out.append(f'<line x1="{x0}" y1="{y0 - 1}" x2="{x0 + 6 * u}" y2="{y0 - 1}" stroke-dasharray="3 2"/>')
    return "".join(out)


U = 24
X0, Y0 = 60, 76
DIAGRAM = f"""
<figure class="diagram">
<svg viewBox="0 0 760 312" role="img" aria-label="A body senses only through its sensor blocks: a sensor block that looks out of the body sees that way, a walled-in one sees nothing, and a body without one reads nothing" style="max-width:100%;height:auto;display:block">
<defs><marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="currentColor"/></marker></defs>
<g fill="none" stroke="currentColor" stroke-width="1.2" font-size="12" font-family="system-ui, sans-serif">
  {body_svg(X0, Y0, U)}
  {label(X0 - 8, Y0 + 4, "front", "end")}
  <line x1="{X0 + 2.5 * U}" y1="{Y0 - 4}" x2="{X0 + 2.5 * U}" y2="24" marker-end="url(#arr)"/>
  {label(X0 + 2.5 * U + 8, 32, "sees 2 cells ahead", "start")}
  <line x1="{X0 + 5 * U + 2}" y1="{Y0 + 1.5 * U}" x2="{X0 + 6 * U + 44}" y2="{Y0 + 1.5 * U}" marker-end="url(#arr)"/>
  {label(X0 + 6 * U + 22, Y0 + 1.5 * U - 10, "2 cells")}
  {label(X0 + 3 * U, Y0 + 6 * U + 22, "middle sensor walled in: sees nothing")}
  {label(X0 + 3 * U, Y0 + 6 * U + 40, "back and left: dark (read 0)")}
  {box(300, 20, 220, 150, "What it registers", ["front, right: food, bodies, water", "out to 2 cells, j cells away at 1/j", "back, left: 0", "food under its sensor blocks", "energy, thirst, breath: has one"], accent=True)}
  <line x1="{X0 + 6 * U + 50}" y1="{Y0 + 60}" x2="298" y2="{Y0 + 60}" marker-end="url(#arr)"/>
  {label(262, Y0 + 52, "sight")}
  {box(570, 20, 180, 66, "Policy", ["e069's weights, from genes"])}
  <line x1="520" y1="53" x2="568" y2="53" marker-end="url(#arr)"/>
  {label(544, 45, "16")}
  {box(570, 120, 180, 66, "Action", ["stay, forward, left, right"])}
  <line x1="660" y1="86" x2="660" y2="118" marker-end="url(#arr)"/>
  {label(668, 107, "best of 4", "start")}
  {box(300, 220, 450, 80, "senses = 0 (e069, the controls)", ["every side sees 1 + all sensor blocks, the food under the whole body,", "and every body reads its energy, thirst and breath"], dashed=True)}
</g>
</svg>
<figcaption>Figure 1. With senses from sensor blocks, a sensor block sees out of the side where nothing of its body lies beyond it, one cell and one more per such block (up to 8). A body without a sensor block reads nothing and acts on its weights' biases. Nothing is added or priced.</figcaption>
</figure>
"""

# The text of the page: kept here to count its words against the skill's budget.
TEXT = {
    "tldr": ("A body now senses only through its sensor blocks: the food, bodies and water where one looks out of the body, and its "
             "own fills only if it has one. On three seeds the bodies do not buy sight (2-4% look out); the blind walk straight and "
             "outbreed the few that see. Every seed ends with the same three shore kinds: 3 held against 4, 3.4 at a census against "
             "6.1. Kept by the pre-set rule, at its edge."),
    "question": ("Principle 2: what a body can do comes out of its blocks. Its senses did not: every body saw one cell around it and "
                 "read its energy, thirst and breath, whatever it was built of, and each new law added an input by hand. A sensor block "
                 "only made the eye reach further, and 83-93% of the controls' grown bodies held none. Set before the runs, on seeds 9-11:"),
    "hyp": ["The sensor blocks come back: half the grown bodies have one looking out, on two of three seeds (the controls: 6-13%).",
            "They look ahead: blocks looking out to the front at least 1.5 times those to the back, on two of three seeds.",
            "The world keeps its kinds: kinds by birth form held at every census average 3.0 or more (the controls: 4.0). If so, and every world stands, the senses of the sensor blocks become the default."],
    "world": ("e069's world with the values of a life constant (e067's), and one change in what a body reads (Figure 1). The readings "
              "and the weights that turn them into actions are e069's; only which body reads what changes. A sensor block keeps its "
              "weight, upkeep and softness."),
    "runs": ("c1225, seeds 9, 10 and 11, 100,000 steps on one core (34-36 minutes). The controls are e067's run and e069's constants "
             "runs. With the senses given, the crate reproduced e069's first 10,000 steps exactly. Over the second half:"),
    "measures": [
        ("Looking out", "grown bodies with a sensor block that has nothing of its body beyond it on some side."),
        ("Kinds by birth form", "e068's census: kinds holding 5% of the grown bodies, held at every census."),
        ("Distance from birth", "cells between where a grown body stands and where it was born."),
        ("Children per 1,000 steps", "children a body placed, over its age."),
    ],
    "v0": "the lowest count is 6,395-7,241 bodies, against 6,009-8,108 in the controls.",
    "v1": "4.3%, 2.2% and 2.2% of the grown bodies look out, under the controls' 6-13%.",
    "v2": "front against back: 0.10 and 0.08, 0.03 and 0.04, 0.03 and 0.02 blocks a body.",
    "v3": "3, 3 and 3 kinds held (mean 3.00, the line), against 4, 3 and 5.",
    "h1": "3.1 The bodies do not buy sight",
    "r1": ("Sensor blocks fall in the first 3,000 steps, as in the controls, and never return. The few bodies that keep one looking "
           "out barely move (a median 0 cells from birth) and place 1.7-2.5 children per 1,000 steps, against 3.8-4.5 for the blind. "
           "Where every body sees (the controls of seeds 10 and 11) the split is 2.7-3.0 against 3.0-3.2."),
    "h2": "3.2 The blind walk straight",
    "r2": ("A body that reads nothing acts on its weights' biases: forward in 85-90% of its decisions, and turns halve. Over about the "
           "same path the grown bodies end 22-28 cells from their birth, against 8-10. The number of bodies and the deaths by thirst "
           "barely change."),
    "h3": "3.3 Three kinds, all at the shore, on every seed",
    "r3": ("Every seed holds the same three: a roaming plant eater (55-65% of the grown bodies), a dense roaming mixed eater (13-21%) "
           "and a gut that stays (8-11%). No kind keeps to one medium, so shuffling the medium changes little (3.2 against 3.4). The "
           "controls' surface and bottom roamers and their sitters are gone, and one lineage holds 67-76%."),
    "gallery": "The commonest intact birth body of each kind held on seed 9 with senses from sensor blocks, and one kind of the control that is gone. The dashed line is the front.",
    "d1": ("With the senses given, every body turned toward what it saw whether that paid or not, and the world held sitters and "
           "roamers kept to the surface, the bottom or the land. Given the choice, the bodies drop the sense: a body that reads nothing "
           "walks straight and places more children. The kinds of one medium came with senses no body chose."),
    "d2": ("Why a sensor block does not pay is not shown. Candidates: its readings reach the actions through weights the same genes set, "
           "at random at the start; the grazed food is even at a body's scale (#64); and a body lives about 150 steps, a short walk "
           "in which to meet a difference it could see."),
    "d3": ("Not shown: c1236, longer runs, a start from bodies that already see, and a world where walking blind costs more. The rule "
           "was met at its edge; the finer counts say the world holds fewer kinds."),
    "conclusion": ("Kept as stage C's default by the rule set before the runs: every world stood and 3.00 kinds were held at every census, "
                   "the line. From here a body senses through its sensor blocks. Proposed next: section 2's next row (cold) on this world, "
                   "judged on the same seeds against these runs; or, since the rule was met at its edge, keep the given senses until a "
                   "law makes walking blind cost."),
}
GALLERY_PICKS = [  # (run, kind, title, what the shape does)
    ("senses9", "plant / no tooth / roams / shore", "Muscle pulling a tail of gut",
     "No sensor block: it reads nothing and walks straight, eating algae, litter and grass wherever its line takes it."),
    ("senses9", "mixed / no tooth / roams / shore", "A block of muscle in front",
     "Ten muscles press on what lies ahead and break it: kills are a third of what it eats."),
    ("senses9", "plant / no tooth / stays / shore", "A solid square of gut",
     "No muscle: it sits where it was born. Its kind holds the most sensor blocks (16%)."),
    ("given9", "plant / no tooth / roams / surface", "Gone: the algae roamer",
     "The control's surface kind: a row of gut with muscle at one end, 94% of its bodies at the surface."),
]
VERDICTS = [(True, "0, every world stands", "v0"), (False, "1, the sensor blocks come back", "v1"),
            (False, "2, they look ahead", "v2"), (True, "3, the world keeps its kinds", "v3")]


def main():
    table_rows = [
        ("Bodies: mean (lowest)", lambda r: f"{r['pop']:,.0f} ({r['pop_min']:,.0f})"),
        ("Grown bodies with a sensor block; one looking out", lambda r: f"{r['feeling']:.0%}; {r['sighted']:.0%}"),
        ("Blocks looking out per body: front / back", lambda r: f"{r['sight_front']:.2f} / {r['sight_back']:.2f}"),
        ("<strong>Kinds by birth form held</strong>", lambda r: f"{r['form_held']:.0f}"),
        ("Kinds at a census: mean (lowest-highest)", lambda r: f"{r['form']:.1f} ({r['form_low']:.0f}-{r['form_high']:.0f})"),
        ("Medium shuffled: mean", lambda r: f"{r['null_medium']:.1f}"),
        ("Kinds per lineage (e060)", lambda r: f"{r['lineage_e060']:.1f}"),
        ("Lineages alive (top lineage)", lambda r: f"{r['lineages']:.0f} ({r['top_lineage']:.0%})"),
        ("Stay / forward / turn", lambda r: f"{r['stay']:.0%} / {r['forward']:.0%} / {r['left'] + r['right']:.0%}"),
        ("Moves blocked; children with no room", lambda r: f"{r['blocked']:.0%}; {r['no_room']:.0%}"),
        ("Deaths: hunger / thirst / suffocation", lambda r: f"{r['deaths_hunger']:.0%} / {r['deaths_thirst']:.0%} / {r['deaths_suffocation']:.1%}"),
        ("Kills' share of intake", lambda r: f"{r['kills']:.0%}"),
        ("Blocks a body (mean)", lambda r: f"{r['size_mean']:.0f}"),
    ]
    head = "".join(f"<th>seed {seed(r)}, {'given' if arm(r) == 'given' else 'sensors'}</th>" for r in RUNS)
    tbl = "".join(f"<tr><td>{name}</td>" + "".join(f"<td>{f(R[run])}</td>" for run in RUNS) + "</tr>" for name, f in table_rows)

    charts_eye = [
        runs_lines("Grown bodies with a sensor block looking out", "At each census (hypothesis 1 asked for 50%). Orange under blue: when every sense needs a sensor block, fewer bodies keep one.", T, "sighted", "share of grown bodies", pct=True),
        sides_chart("Where the sensor blocks look out", "Blocks looking out to each side, per grown body, second half. A front bar 1.5 times the back would be an eye facing the way the body moves."),
    ]
    charts_count = [
        seeds_chart("Kinds held at every census, by seed", "Kinds holding 5% of the grown bodies at all six censuses of the second half. Dashed: stage C's 4.", "form_held", "kinds held", line=4, integer=True),
        seeds_chart("Kinds at a census, by seed", "Mean kinds by birth form over the six censuses; the spread between seeds is what a gap within a pair is judged against.", "form", "kinds", line=4),
    ]
    charts_life = [
        runs_lines("How far the grown bodies end from their birth", "Median distance in cells, every 1,000 steps. Orange above blue: bodies that walk straight.", [{"run": run, **p} for run in RUNS for p in L[run]], "travel_p50", "cells"),
        runs_lines("Decisions to step forward", "Share of decisions, every 1,000 steps. A blind body acts on its biases alone.", [{"run": run, **p} for run in RUNS for p in L[run]], "forward", "share of decisions", pct=True, ymax=1),
    ]

    t = lambda k: html.escape(TEXT.get(k, "TODO"))
    count = lambda v: len((" ".join(v) if isinstance(v, list) and v and isinstance(v[0], str) else " ".join(" ".join(t) for t in v) if isinstance(v, list) else v).split())
    words = sum(count(v) for v in TEXT.values()) + sum(len(p[3].split()) for p in GALLERY_PICKS)
    print(f"TEXT: {words} words")
    for k, v in TEXT.items():
        print(f"  {k}: {count(v)}")

    gal = gallery(GALLERY_PICKS, TEXT.get("gallery", "")) if GALLERY_PICKS else ""
    hyp = "".join(f"<li>{html.escape(x)}</li>" for x in TEXT.get("hyp", []))
    measures = "".join(f"<li><strong>{html.escape(k)}</strong> - {html.escape(v)}</li>" for k, v in TEXT.get("measures", []))
    verdicts = "".join(f"<li><span class=\"verdict{'' if yes else ' no'}\">{'Yes' if yes else 'No'}</span> {html.escape(head_)}: {t(key)}</li>" for yes, head_, key in VERDICTS)
    appendix = "\n".join([
        table("runs", ["run", "form_held", "form", "null_medium", "lineage_e060", "feeling", "sighted", "sensors", "born_sensors", "sight_front", "sight_back", "sight_left", "sight_right", "pop", "stay", "forward", "sense_used", "ms_step"]),
        table("media", ["run", "medium", "bodies", "feeling", "sighted", "sight_front", "sight_back", "sight_left", "sight_right"]),
        table("kinds", ["run", "kind", "share", "censuses", "held", "forms", "lineages", "born_size", "density", "eye_feeling", "eye_sighted", "eye_sight_front", "eye_sight_back", "grass", "algae", "detritus", "meat", "land", "surface", "bottom"]),
    ])
    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>e070 senses from sensor blocks - Report</title>
<style>{CSS}</style>
</head>
<body>
<main>
<h1>e070: senses from sensor blocks</h1>
<p class="sub">Experiment report - 2026-09-15 - e067's world where a body senses only through its sensor blocks; c1225, seeds 9-11, 100,000 steps (foundation stage C, eighth step, #84)</p>

<section class="tldr">
<h2>TL;DR</h2>
<p>{t("tldr")}</p>
</section>

<h2>1. Question</h2>
<p>{t("question")}</p>
<ol>{hyp}</ol>

<h2>2. The world</h2>
<p>{t("world")}</p>
{DIAGRAM}
<p><strong>Runs.</strong> {t("runs")}</p>
<ul class="measures">{measures}</ul>

<h2>3. Results</h2>
<div class="tw"><table>
<thead><tr><th>Second half of the run</th>{head}</tr></thead>
<tbody>{tbl}</tbody></table></div>
<ol class="verdicts">{verdicts}</ol>

<h3>{t("h1")}</h3>
<div class="grid2">{"".join(charts_eye)}</div>
<p>{t("r1")}</p>

<h3>{t("h2")}</h3>
<div class="grid2">{"".join(charts_life)}</div>
<p>{t("r2")}</p>

<h3>{t("h3")}</h3>
<div class="grid2">{"".join(charts_count)}</div>
<p>{t("r3")}</p>
{gal}

<h2>4. Discussion</h2>
<p>{t("d1")}</p>
<p>{t("d2")}</p>
<p>{t("d3")}</p>

<h2>5. Conclusion and next step</h2>
<p>{t("conclusion")}</p>

<h2>Appendix: data</h2>
<p>One row per run in <code>runs.csv</code>; the sensor blocks by medium, at every census and per kind are in <code>experiments/e070_senses/results/</code>. Build with <code>uv run python experiments/e070_senses/senses.py</code>, then <code>report.py</code>.</p>
{appendix}
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
