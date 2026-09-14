#!/usr/bin/env python3
"""Build report.html for e071 (cold, foundation stage C, ninth step, #86).

Charts: matplotlib, exported as SVG and inlined. Diagram: hand-written SVG.
Run from the repo root after cold.py: uv run python experiments/e071_cold/report.py
"""
import csv
import html
import io
import os

import matplotlib
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.ticker import FuncFormatter, MaxNLocator

matplotlib.use("svg")

HERE = os.path.dirname(os.path.abspath(__file__))
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4"]  # fixed slot order
ARM_COLOR = {"control": SERIES[0], "cold": SERIES[1]}
ARM_LABEL = {"control": "no cold (e070, control)", "cold": "cold 0.000125"}
BAND_COLOR = {"cold": SERIES[2], "mild": SERIES[3], "hot": SERIES[4]}
KIND_COLOR = {1: SERIES[0], 2: SERIES[1], 3: SERIES[3], 4: SERIES[2]}  # hard, muscle, sensor, gut: the viewer's
SEED_STYLE = {9: "-", 10: (0, (4, 2)), 11: (0, (1, 1.5))}
SEEDS = (9, 10, 11)
RUNS = [f"{arm}{s}" for s in SEEDS for arm in ("control", "cold")]
BANDS = ("cold", "mild", "hot")
LOGS = {s: os.path.join(HERE, "results", f"c1225_life{s}_cold_log.csv") for s in SEEDS}

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
B = [num(r) for r in rows("bands")]
K = rows("kinds")
L = {s: [num(r) for r in rows(None, LOGS[s])] for s in SEEDS}


def arm(run):
    return "control" if run.startswith("control") else "cold"


def seed(run):
    return int(run.lstrip("contrld"))


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


def cold_lines(title, subtitle):
    """Energy lost to cold over the upkeep due on land, every 1,000 steps, one line per seed."""
    fig, ax = plt.subplots(figsize=(6.4, 2.8))
    for s in SEEDS:
        ax.plot([p["step"] for p in L[s]], [p["cold_land"] for p in L[s]], color=ARM_COLOR["cold"], linestyle=SEED_STYLE[s], linewidth=1.5)
    ax.set_ylim(0, None)
    ax.yaxis.set_major_locator(MaxNLocator(4))
    percent(ax)
    ax.xaxis.set_major_formatter(kfmt)
    ax.set_xlabel("step", loc="right")
    ax.set_ylabel("share of the upkeep due")
    legend_above(ax, 3, handles=[Line2D([], [], color=ARM_COLOR["cold"], linewidth=1.5, linestyle=SEED_STYLE[s], label=f"seed {s}") for s in SEEDS])
    return figure(title, subtitle, to_svg(fig))


def bands_chart(title, subtitle):
    """Cold's share of the upkeep of the grown land bodies, by temperature band, per seed."""
    fig, ax = plt.subplots(figsize=(6.4, 2.6))
    w = 0.8 / len(BANDS)
    for j, b in enumerate(BANDS):
        vals = [next(r for r in B if r["run"] == f"cold{s}" and r["band"] == b)["cold_share"] for s in SEEDS]
        ax.bar([i - 0.4 + w * (j + 0.5) for i in range(len(SEEDS))], vals, width=w * 0.92, color=BAND_COLOR[b], label=f"{b} band")
    ax.set_xticks(range(len(SEEDS)), [f"seed {s}" for s in SEEDS])
    ax.set_ylim(0, None)
    ax.yaxis.set_major_locator(MaxNLocator(4))
    percent(ax)
    ax.set_ylabel("share of the upkeep")
    legend_above(ax, 3)
    return figure(title, subtitle, to_svg(fig))


def seeds_chart(title, subtitle, key, ylabel, line=None, integer=False):
    """One group per seed: the control and the run with cold."""
    fig, ax = plt.subplots(figsize=(6.4, 2.6))
    for j, a in enumerate(("control", "cold")):
        ax.bar([i - 0.2 + 0.4 * j for i in range(len(SEEDS))], [R[f"{a}{s}"][key] for s in SEEDS], width=0.37, color=ARM_COLOR[a], label=ARM_LABEL[a])
    if line is not None:
        ax.axhline(line, color=INK, linewidth=1, linestyle=DASHED)
    ax.set_xticks(range(len(SEEDS)), [f"seed {s}" for s in SEEDS])
    ax.set_ylim(0, max(ax.get_ylim()[1], 1.15 * (line or 0)))
    ax.yaxis.set_major_locator(MaxNLocator(4, integer=integer))
    ax.set_ylabel(ylabel)
    legend_above(ax, 2)
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
        cold = f"cold {float(k['cold_share']):.0%} of its upkeep; {float(k['open_now']):.2f} open soft faces per block; on land {float(k['land']):.0%}"
        cards.append(f"""<figure class="card"><svg viewBox="-1 -1 89 89" width="120" height="120" role="img" aria-label="{html.escape(title)}"><rect x="-1" y="-1" width="89" height="89" fill="var(--cell)"/>{rects}<line x1="-1" y1="-0.5" x2="88" y2="-0.5" stroke="var(--ink2)" stroke-width="1.5" stroke-dasharray="3 2"/></svg>
<figcaption><strong>{html.escape(title)}</strong><br>seed {seed(run)}: {float(k['share']):.0%} of grown bodies, {k['censuses']} of 6 censuses; {k['forms']} forms<br>born with {float(k['born_size']):.0f} blocks, density {float(k['density']):.2f}; eats {food}<br>{cold}<br>{html.escape(what)}</figcaption></figure>""")
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


U = 24
BX, BY = 54, 60  # the body's grid corner; the cold cell spans x 30-126, the warm one 126-222
BODY = [".HHH.", ".MMM.", "GGGG.", "GGGG.", ".GG.."]
# The open faces of its soft blocks over the cold cell (columns 0-2): (x1, y1, x2, y2) of each edge.
COLD_FACES = [(54, 108, 54, 132), (54, 108, 78, 108), (54, 132, 54, 156), (54, 156, 78, 156), (78, 156, 78, 180),
              (78, 180, 102, 180), (102, 180, 126, 180), (126, 156, 126, 180), (78, 84, 78, 108)]


def body_svg():
    fill = {"H": KIND_COLOR[1], "M": KIND_COLOR[2], "G": KIND_COLOR[4]}
    out = ['<rect x="30" y="48" width="96" height="144" fill="var(--cell)" stroke-dasharray="4 3"/>',
           '<rect x="126" y="48" width="96" height="144" fill="none" stroke-dasharray="4 3"/>']
    for r, row in enumerate(BODY):
        for c, ch in enumerate(row):
            if ch != ".":
                out.append(f'<rect x="{BX + c * U + 1}" y="{BY + r * U + 1}" width="{U - 2}" height="{U - 2}" fill="{fill[ch]}" stroke="none"/>')
    out += [f'<line x1="{a}" y1="{b}" x2="{c}" y2="{d}" stroke="var(--s1)" stroke-width="3"/>' for a, b, c, d in COLD_FACES]
    return "".join(out)


DIAGRAM = f"""
<figure class="diagram">
<svg viewBox="0 0 760 290" role="img" aria-label="Open faces of soft blocks over a cell colder than 20 C lose energy by the difference; the body pays it from energy and fat or dies of cold" style="max-width:100%;height:auto;display:block">
<defs><marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="currentColor"/></marker></defs>
<g fill="none" stroke="currentColor" stroke-width="1.2" font-size="12" font-family="system-ui, sans-serif">
  {label(126, 36, "hard front: loses nothing")}
  {body_svg()}
  {label(78, 212, "cell at 2 C")}
  {label(174, 212, "cell at 30 C")}
  {label(126, 240, "9 open soft faces over the cold cell")}
  {label(126, 258, "16 blocks, upkeep 0.064 a turn")}
  <line x1="228" y1="110" x2="282" y2="110" marker-end="url(#arr)"/>
  {label(255, 100, "T &lt; 20 C")}
  {box(286, 30, 240, 136, "Heat lost a turn", ["each open soft face over a cell", "at T under 20 C: 0.000125 x (20 - T)", "times (1 - the fat's fill of its store)", "a hard face: nothing", "here 9 x 18 x 0.000125 = 0.020 (32%)"], accent=True)}
  <line x1="526" y1="72" x2="586" y2="72" marker-end="url(#arr)"/>
  {label(556, 62, "energy")}
  {box(590, 30, 160, 84, "Paid", ["from energy, then fat", "into the soil under it"])}
  <line x1="670" y1="114" x2="670" y2="160" marker-end="url(#arr)" stroke-dasharray="4 3"/>
  {label(678, 142, "cannot pay", "start")}
  {box(590, 164, 160, 66, "Dies of cold", ["a cause of its own"])}
  {box(286, 196, 270, 80, "Scale, set on e070's bodies", ["the median land body at -6 C", "loses its upkeep again"], dashed=True)}
</g>
</svg>
<figcaption>Figure 1. The cold law. A body is as warm as 20 C. Each face of a gut, muscle or sensor block with nothing of its body beside it (blue edges) loses energy by how much colder its cell is; a hard face loses nothing, and the fat insulates by the share of the store it fills. No reading is added.</figcaption>
</figure>
"""

# The text of the page: kept here to count its words against the skill's budget.
TEXT = {
    "tldr": ("Cold on e070's world: a body is as warm as 20 C, and each open soft face over a colder cell loses energy by the "
             "difference. It takes 22-24% of the land's upkeep and 5% of the deaths, but the same share in every temperature band: "
             "the day, not the place, makes the land cold. Land bodies close up a little and do not fatten; kinds held fall to 2, 2 "
             "and 3 (3, 3, 3). Not kept."),
    "question": ("The foundation pairs each difference of the world with a law about a material. Its cold row: a block facing a colder "
                 "cell loses energy by the difference, and hard blocks and fat insulate, so compact, armored or fat bodies should do "
                 "better in cold places and winters. c1225's land spans -6 to 65 C at a census and its mean swings 29 C over a year. "
                 "Set before the runs, on seeds 9-11:"),
    "hyp": ["The land closes up or fattens: grown land bodies open at most 0.77 soft faces per block, or their fat fills at least 0.104 of the store, on two of three seeds (the controls: 0.87 and 0.069).",
            "Forms part by medium: a kind held at every census keeps 90% of its bodies to one medium, on two of three seeds (the controls: none).",
            "The world keeps its kinds: kinds held at every census average at least the controls' 3.0. If so, and every world stands, cold becomes the default."],
    "world": ("e070's world with one law more (Figure 1). The body pays the cold after its upkeep, from its energy and then its fat, "
              "into the soil; one that cannot pay dies of cold. No reading is added: a body does not sense the temperature."),
    "runs": ("c1225, seeds 9, 10 and 11, 100,000 steps on one core (32-38 minutes); the controls are e070's runs. With cold at 0 the "
             "crate reproduced e070's first 10,000 steps exactly. The scale was set on e070's bodies, with no runs. Over the second half:"),
    "measures": [
        ("Cold's share", "energy lost to cold over the upkeep due."),
        ("Open soft faces per block", "faces of gut, muscle and sensor blocks with nothing of the body beside them."),
        ("Fat fill", "a body's fat over the most its store holds."),
        ("Temperature band", "e061's cold (under 5 C), mild and hot (20 C and over), by the cell's quarter mean."),
        ("Kinds by birth form", "e068's census: kinds holding 5% of the grown bodies, held at every census."),
    ],
    "v0": "the lowest count is 6,117-7,023 bodies, against 6,395-7,241.",
    "v1": "open soft faces per block 0.75, 0.79 and 0.78 (line 0.77); fat fill 0.056-0.071 (line 0.104).",
    "v2": "no kind held at every census keeps 90% of its bodies to one medium, on any seed.",
    "v3": "2, 2 and 3 kinds held (mean 2.33), against 3, 3 and 3.",
    "h1": "3.1 Cold is a tax on all the land, set by the night",
    "r1": ("A grown land body pays 15-23% of its upkeep to cold in every band, the cold band barely more; the water pays 2-3%. In the "
           "controls half the land's bodies in every band stand under 20 C at a census, the coldest tenth at -4 to -8 C. The day "
           "swings a cell more than the bands differ, so every body on land meets the cold several times a life."),
    "h2": "3.2 The land closes up a little, and nothing fattens",
    "r2": ("Land bodies open 0.04-0.13 fewer soft faces per block than their controls and hold a few more hard blocks (5-7% against "
           "2-5%), in every band alike; the share of them in each band does not move. The fat fills 6-7% of the store with or "
           "without cold, so it takes about 7% off the loss."),
    "h3": "3.3 One kind fewer held on two seeds, the same at a census",
    "r3": ("On seed 9 the dense mixed roamer misses the 5% line at one census of six, and on seed 10 the gut that stays does; at a "
           "census both arms average 3.44 kinds. No kind keeps to one medium, and one lineage holds 55%, 79% and 91% of the grown "
           "bodies (73%, 76% and 67% without cold)."),
    "gallery": "The commonest intact birth body of each kind on seed 9 with cold that holds 5% at three censuses or more. The dashed line is the front.",
    "d1": ("The foundation expected cold places and winters. At a body's scale this world has neither as a place: the day is 60 steps, "
           "a fifth of a life, and swings a land cell from below 0 to over 50 C. A cold met every night is a tax on being on land, as "
           "dry air is, and the bodies answer it the same way: they close up."),
    "d2": ("The fat cannot answer, because a body fills its store only with what it pays in upkeep from its energy. Hard blocks weigh "
           "twice a soft block and feed nothing, and rose only to 5-7% of the land's blocks."),
    "d3": ("Not shown: a cold that differs by place (the day averaged out), a colder world (c1236), a body that senses the temperature, "
           "other scales and body temperatures, and longer runs. The loss in kinds held is one kind missing one census on two seeds."),
    "conclusion": ("Not kept, by the rule set before the runs (2.33 kinds held against 3.0); e070 stays stage C's control. Proposed "
                   "next: (a) the same law read against each cell's temperature averaged over the last day, so the cold differs by place "
                   "and season; (b) a body's heat as a state that a heavier body keeps longer; (c) leave cold and build section 2's "
                   "other rows. Recommended: (a)."),
}
GALLERY_PICKS = [  # (run, kind, title, what the shape does)
    ("cold9", "plant / no tooth / roams / shore", "A hard front, muscle, a tail of gut",
     "The commonest kind walks mostly in the water, where cold costs little; its narrow gut tail is all open faces."),
    ("cold9", "plant / no tooth / stays / shore", "A bar of gut with a tail",
     "No muscle: it sits where it was born, 73% of its bodies on the bottom eating litter."),
    ("cold9", "mixed / no tooth / roams / shore", "Muscle wrapped round a square of gut",
     "Its muscle breaks what lies ahead: kills are 31% of its food. Half its bodies stand on land."),
    ("cold9", "plant / no tooth / stays / land", "A solid square of gut",
     "The most closed body, on land eating grass. Closed as it is, it pays the most cold, since it never leaves the land."),
]
VERDICTS = [(True, "0, every world stands", "v0"), (False, "1, the land closes up or fattens", "v1"),
            (False, "2, forms part by medium", "v2"), (False, "3, the world keeps its kinds", "v3")]


def main():
    dash = lambda v, fmt: "-" if v == 0 else fmt.format(v)
    table_rows = [
        ("Bodies: mean (lowest)", lambda r: f"{r['pop']:,.0f} ({r['pop_min']:,.0f})"),
        ("<strong>Cold's share of the upkeep: land / surface / bottom</strong>", lambda r: "-" if r["logcold_land"] == 0 else f"{r['logcold_land']:.0%} / {r['logcold_surface']:.1%} / {r['logcold_bottom']:.1%}"),
        ("Deaths: hunger / thirst / cold", lambda r: f"{r['deaths_hunger']:.0%} / {r['deaths_thirst']:.0%} / {dash(r['deaths_cold'], '{:.1%}')}"),
        ("<strong>Land: open soft faces per block</strong>", lambda r: f"{r['land_open']:.2f}"),
        ("Land: hard share; blocks a body", lambda r: f"{r['land_hard']:.1%}; {r['land_blocks']:.0f}"),
        ("Land: fat fill (median)", lambda r: f"{r['land_fill']:.3f}"),
        ("<strong>Kinds by birth form held</strong>", lambda r: f"{r['form_held']:.0f}"),
        ("Kinds at a census: mean (lowest-highest)", lambda r: f"{r['form']:.1f} ({r['form_low']:.0f}-{r['form_high']:.0f})"),
        ("Medium shuffled: mean", lambda r: f"{r['null_medium']:.1f}"),
        ("Kinds per lineage (e060)", lambda r: f"{r['lineage_e060']:.1f}"),
        ("Lineages alive (top lineage)", lambda r: f"{r['lineages']:.0f} ({r['top_lineage']:.0%})"),
        ("Moves blocked; children with no room", lambda r: f"{r['blocked']:.0%}; {r['no_room']:.0%}"),
        ("Kills' share of intake", lambda r: f"{r['kills']:.0%}"),
        ("Grown bodies with a sensor block looking out", lambda r: f"{r['sighted']:.0%}"),
        ("A step on one core", lambda r: f"{r['ms_step']:.1f} ms"),
    ]
    head = "".join(f"<th>seed {seed(r)}, {arm(r)}</th>" for r in RUNS)
    tbl = "".join(f"<tr><td>{name}</td>" + "".join(f"<td>{f(R[run])}</td>" for run in RUNS) + "</tr>" for name, f in table_rows)

    charts_tax = [
        cold_lines("Energy lost to cold on land", "Over the upkeep due, every 1,000 steps, in the runs with cold. A line at zero would be a law that never bites."),
        bands_chart("Cold's share by temperature band", "Grown land bodies in the runs with cold, by the band of the cell under them. Equal bars: the band does not set what a body pays."),
    ]
    charts_shape = [
        seeds_chart("Open soft faces per block on land", "Grown land bodies, second half. Lower is a more closed body. Dashed: hypothesis 1's line (0.77).", "land_open", "faces per block", line=0.77),
        seeds_chart("The fat's fill of the store on land", "Median over the grown land bodies. Dashed: hypothesis 1's line (0.104). Equal bars: the fat does not answer.", "land_fill", "share of the store", line=0.104),
    ]
    charts_count = [
        seeds_chart("Kinds held at every census, by seed", "Kinds holding 5% of the grown bodies at all six censuses of the second half. Dashed: the rule's mean of 3.", "form_held", "kinds held", line=3, integer=True),
        seeds_chart("Kinds at a census, by seed", "Mean kinds by birth form over the six censuses. Both arms average 3.44.", "form", "kinds"),
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
        table("runs", ["run", "form_held", "form", "null_medium", "lineage_e060", "held_one_medium", "land_open", "land_hard", "land_fill", "land_blocks", "land_cold", "land_mild", "land_hot", "pop", "pop_land", "logcold_land", "deaths_cold", "ms_step"]),
        table("media", ["run", "medium", "bodies", "open", "hard", "fat_fill", "blocks", "born_blocks", "temp", "cold_share"]),
        table("bands", ["run", "band", "bodies", "open", "hard", "fat_fill", "blocks", "born_blocks", "temp", "cold_share"]),
        table("kinds", ["run", "kind", "share", "censuses", "held", "forms", "born_size", "density", "open_now", "hard_now", "fat_fill", "cold_share", "land", "surface", "bottom", "band_cold", "band_mild", "band_hot", "grass", "algae", "detritus", "meat"]),
    ])
    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>e071 cold - Report</title>
<style>{CSS}</style>
</head>
<body>
<main>
<h1>e071: cold</h1>
<p class="sub">Experiment report - 2026-09-15 - e070's world where open soft faces lose energy to colder cells; c1225, seeds 9-11, 100,000 steps (foundation stage C, ninth step, #86)</p>

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
<div class="grid2">{"".join(charts_tax)}</div>
<p>{t("r1")}</p>

<h3>{t("h2")}</h3>
<div class="grid2">{"".join(charts_shape)}</div>
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
<p>One row per run in <code>runs.csv</code>; the grown bodies by medium, by temperature band on land, at every census and per kind are in <code>experiments/e071_cold/results/</code>. The scale's dry run is <code>dryrun.py</code>. Build with <code>uv run python experiments/e071_cold/cold.py</code>, then <code>report.py</code>.</p>
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
