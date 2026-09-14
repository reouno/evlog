#!/usr/bin/env python3
"""Build report.html for e068 (kinds of living inside a lineage, foundation stage C, sixth step, #82).

Charts: matplotlib, exported as SVG and inlined. Diagram: hand-written SVG.
Run from the repo root after kinds.py: uv run python experiments/e068_kinds/report.py
"""
import csv
import html
import io
import os

import matplotlib
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from matplotlib.ticker import MaxNLocator

matplotlib.use("svg")

HERE = os.path.dirname(os.path.abspath(__file__))
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4"]  # fixed slot order
READING = {"body": SERIES[0], "lineage": SERIES[1], "form": SERIES[2], "medium": SERIES[3], "whole": SERIES[4]}
MEDIUM_COLOR = {"land": SERIES[3], "surface": SERIES[2], "bottom": SERIES[4], "shore": SERIES[0]}  # e067's, and the shore
KIND_COLOR = {1: SERIES[0], 2: SERIES[1], 3: SERIES[3], 4: SERIES[2]}  # hard, muscle, sensor, gut: the viewer's
RUNS = ["e065", "e066", "breath 0.003", "breath 0.01"]
LABEL = {"e065": "e065", "e066": "e066", "breath 0.003": "e067 at 0.003", "breath 0.01": "e067 at 0.01"}

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

def rows(name):
    with open(os.path.join(HERE, "results", name + ".csv")) as f:
        return list(csv.DictReader(f))


R = {r["run"]: {k: (v if k == "run" else float(v)) for k, v in r.items()} for r in rows("runs")}
K = rows("kinds")
S = rows("sizes")
W = rows("sweep")


# ---------- charts ----------

def to_svg(fig):
    buf = io.StringIO()
    fig.savefig(buf, format="svg", bbox_inches="tight", pad_inches=0.05)
    plt.close(fig)
    return buf.getvalue()


def legend_above(ax, n, **kw):
    ax.legend(loc="lower left", bbox_to_anchor=(0, 1.0), ncols=n, handlelength=1.4, borderaxespad=0, columnspacing=1.2, **kw)


def figure(title, subtitle, svg):
    return f"""
<figure class="fig">
  <figcaption><strong>{html.escape(title)}</strong><span>{html.escape(subtitle)}</span></figcaption>
  {svg}
</figure>"""


def percent(ax, axis="y"):
    (ax.yaxis if axis == "y" else ax.xaxis).set_major_formatter(lambda v, _p: f"{v:.0%}")


def grouped(title, subtitle, series, ylabel, line=None, pct=False, ncols=3, height=2.6, integer=False):
    """One group per run, one bar per series: (label, key or function of a run's row, colour)."""
    fig, ax = plt.subplots(figsize=(6.4, height))
    width = 0.8 / len(series)
    for j, (label, key, colour) in enumerate(series):
        vals = [key(R[r]) if callable(key) else R[r][key] for r in RUNS]
        ax.bar([i - 0.4 + width * (j + 0.5) for i in range(len(RUNS))], vals, width=width * 0.92, color=colour, label=label)
    if line is not None:
        ax.axhline(line, color=INK, linewidth=1, linestyle=DASHED)
    ax.set_xticks(range(len(RUNS)), [LABEL[r] for r in RUNS])
    ax.set_ylim(0, None)
    ax.yaxis.set_major_locator(MaxNLocator(4, integer=integer))
    if pct:
        percent(ax)
    ax.set_ylabel(ylabel)
    legend_above(ax, ncols)
    return figure(title, subtitle, to_svg(fig))


def sizes_chart(title, subtitle, run, lineage):
    """Birth size of a lineage's dense grown bodies, on land and in the water."""
    data = [r for r in S if r["run"] == run and r["lineage"] == lineage and r["light"] == "0"]
    bins = sorted({int(r["born_size"]) for r in data if float(r["share"]) >= 0.01})
    fig, ax = plt.subplots(figsize=(6.4, 2.6))
    for j, (where, colour) in enumerate((("land", MEDIUM_COLOR["land"]), ("water", MEDIUM_COLOR["bottom"]))):
        share = {int(r["born_size"]): float(r["share"]) for r in data if r["where"] == where}
        n = int(next(r["bodies"] for r in data if r["where"] == where))
        ax.bar([b + 2 + (j - 0.5) * 1.7 for b in bins], [share.get(b, 0) for b in bins], width=1.6, color=colour, label=f"{where} ({n:,} bodies)")
    ax.set_xlabel("blocks at birth, in fours", loc="right")
    ax.set_ylim(0, None)
    ax.yaxis.set_major_locator(MaxNLocator(4))
    percent(ax)
    ax.set_ylabel("share of its bodies")
    legend_above(ax, 2)
    return figure(title, subtitle, to_svg(fig))


def short(k):
    diet, tooth, roams, medium = k["kind"].split(" / ")
    return f"{diet}, {roams}, {medium}" + (", tooth" if tooth == "tooth" else "")


def kinds_chart(title, subtitle, run):
    ks = sorted((k for k in K if k["run"] == run and float(k["share"]) >= 0.02), key=lambda k: float(k["share"]))
    fig, ax = plt.subplots(figsize=(6.4, 3.0))
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


def sweep_chart(title, subtitle):
    """Kinds by birth form less the count with the medium shuffled, under each setting."""
    settings = [("90%, forms of 20 (chosen)", None), ("80%", (0.8, 20)), ("95%", (0.95, 20)), ("forms of 10", (0.9, 10)), ("forms of 50", (0.9, 50))]
    markers = ["o", "^", "v", "s", "D"]
    fig, ax = plt.subplots(figsize=(6.4, 2.6))
    for j, (label, s) in enumerate(settings):
        gains = []
        for run in RUNS:
            if s is None:
                gains.append(R[run]["form"] - R[run]["null_medium"])
            else:
                w = next(x for x in W if x["run"] == run and float(x["keep"]) == s[0] and int(x["form_min"]) == s[1])
                gains.append(float(w["form"]) - float(w["null_medium"]))
        ax.scatter([i + (j - 2) * 0.13 for i in range(len(RUNS))], gains, marker=markers[j], s=46 if s is None else 26,
                   color=READING["form"], alpha=1.0 if s is None else 0.7, label=label, zorder=3, linewidths=0)
    ax.axhline(0, color=INK, linewidth=1)
    ax.set_xticks(range(len(RUNS)), [LABEL[r] for r in RUNS])
    ax.yaxis.set_major_locator(MaxNLocator(4))
    ax.set_ylabel("kinds gained")
    legend_above(ax, 3)
    return figure(title, subtitle, to_svg(fig))


def gallery(picks, caption):
    here = {k["kind"]: k for k in K if k["run"] == "breath 0.01"}
    cards = []
    for kind, title, what in picks:
        k = here[kind]
        side, cells = int(k["side"]), k["cells"]
        u = 88 / side
        rects = "".join(f'<rect x="{(i % side) * u:.2f}" y="{(i // side) * u:.2f}" width="{u * 0.9:.2f}" height="{u * 0.9:.2f}" fill="{KIND_COLOR[int(c)]}"/>'
                        for i, c in enumerate(cells) if c != "0")
        lead = ", ".join(f"{p.split(':')[0]} {float(p.split(':')[1]):.0%}" for p in k["top_lineages"].split()[:2])
        food = ", ".join(f"{name} {float(k[col]):.0%}" for name, col in (("grass", "grass"), ("algae", "algae"), ("litter", "detritus"), ("flesh", "meat")) if float(k[col]) >= 0.05)
        opened = f", {float(k['open_born']):.2f} open faces per block" if k["open_born"] else ""
        cards.append(f"""<figure class="card"><svg viewBox="-1 -1 89 89" width="120" height="120" role="img" aria-label="{html.escape(title)}"><rect x="-1" y="-1" width="89" height="89" fill="var(--cell)"/>{rects}<line x1="-1" y1="-0.5" x2="88" y2="-0.5" stroke="var(--ink2)" stroke-width="1.5" stroke-dasharray="3 2"/></svg>
<figcaption><strong>{html.escape(title)}</strong><br>{float(k['share']):.0%} of grown bodies, at 5% in {k['censuses']} of 6 censuses; {k['forms']} forms in {k['lineages']} lineages ({lead})<br>born with {float(k['born_size']):.0f} blocks (median), density {float(k['density']):.2f}{opened}; eats {food}; kills {float(k['kills']):.0%} of its intake<br>{html.escape(what)}</figcaption></figure>""")
    return f"""<figure class="diagram"><div class="cards">{"".join(cards)}</div>
<figcaption>{html.escape(caption)}</figcaption></figure>"""


def table(name, cols, keep=lambda r: True):
    body = "".join("<tr>" + "".join(f"<td>{html.escape(r[c][:60])}</td>" for c in cols) + "</tr>" for r in rows(name) if keep(r))
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
th, td {{ padding: 6px 12px; text-align: right; border-bottom: 1px solid var(--grid); }}
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


DIAGRAM = f"""
<figure class="diagram">
<svg viewBox="0 0 760 350" role="img" aria-label="A grown body is counted under the way of living of its birth form, read over all the form's grown bodies; the null shuffles what bodies do inside a lineage" style="max-width:100%;height:auto;display:block">
<defs><marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="currentColor"/></marker></defs>
<g fill="none" stroke="currentColor" stroke-width="1.2" font-size="12" font-family="system-ui, sans-serif">
  {box(10, 20, 190, 92, "A grown body", ["aged 300+, has eaten", "its cells: after breaks"])}
  {box(285, 20, 190, 92, "Its birth signature", ["side; hard, muscle,", "sensor, gut; bite; density"])}
  {box(560, 20, 190, 92, "Its birth form", ["a signature of 20+ bodies;", "rarer: the nearest one"], accent=True)}
  <line x1="200" y1="66" x2="283" y2="66" marker-end="url(#arr)"/>{label(241, 56, "born as")}
  <line x1="475" y1="66" x2="558" y2="66" marker-end="url(#arr)"/>{label(516, 56, "grouped")}
  {box(560, 150, 190, 110, "The form's way", ["diet: its summed intake", "tooth, roaming: medians", "medium: where 90% stand,", "else the shore"])}
  <line x1="655" y1="112" x2="655" y2="148" marker-end="url(#arr)"/>{label(645, 135, "all its bodies", "end")}
  {box(285, 150, 190, 92, "A kind of living", ["5% of the grown bodies", "held: at every census"])}
  <line x1="560" y1="196" x2="477" y2="196" marker-end="url(#arr)"/>{label(518, 186, "counted")}
  {box(560, 290, 190, 52, "Null", ["shuffled inside a lineage"], dashed=True)}
  <line x1="655" y1="290" x2="655" y2="262" marker-end="url(#arr)" stroke-dasharray="4 3"/>{label(645, 280, "what bodies do", "end")}
</g>
</svg>
<figcaption>Figure 1. The census by birth form. A lineage (e060's unit) joins mates within 6 genes and can hold several forms; a form is what a child inherits. The null keeps the forms and shuffles intake, bite, travel and medium among a lineage's grown bodies of one layer.</figcaption>
</figure>
"""

# The text of the page: kept here to count its words against the skill's budget.
TEXT = {}

# (kind at breath 0.01, title, what the shape does)
GALLERY_PICKS = [
    ("plant / no tooth / roams / surface", "An open hook at the surface",
     "Gut in two rows with a muscle tail: more open faces than blocks, so it breathes in water."),
    ("plant / no tooth / roams / bottom", "A longer hook on the bottom",
     "Denser than water and open along its tail: it sinks, breathes, and eats what settles."),
    ("plant / no tooth / roams / shore", "The hook at the shore",
     "The same plan with more gut, in every medium: the largest kind."),
    ("plant / no tooth / stays / shore", "A solid square of gut",
     "No muscle and closed on every side: it sits where it was born, on land or on the bottom."),
    ("mixed / no tooth / roams / shore", "A dense crusher",
     "Muscle in front at density 1.93: its faces break lighter ones."),
    ("plant / no tooth / stays / land", "A closed block of land",
     "Solid gut kept to land, where closed bodies dry least. Such forms are many and small."),
]


def main():
    b01, b003, e65, e66 = R["breath 0.01"], R["breath 0.003"], R["e065"], R["e066"]

    table_rows = [
        ("Grown bodies a census; forms", lambda r: f"{r['grown']:,.0f}; {r['forms']:.0f}"),
        ("Kinds per body, with the medium (medium shuffled)", lambda r: f"{r['body_medium']:.1f} ({r['body_medium_null']:.1f})"),
        ("Kinds per lineage (e060)", lambda r: f"{r['lineage_e060']:.1f}"),
        ("Kinds by modal form (all shuffled)", lambda r: f"{r['modal_form']:.1f} ({r['modal_form_null']:.1f})"),
        ("<strong>Kinds by birth form</strong>: mean (lowest-highest)", lambda r: f"{r['form']:.1f} ({r['form_low']:.0f}-{r['form_high']:.0f})"),
        ("Held at every census", lambda r: f"{r['form_held']:.0f}"),
        ("By birth form, medium shuffled: mean; held", lambda r: f"{r['null_medium']:.1f}; {r['null_medium_held']:.0f}"),
        ("By birth form, all shuffled: mean; held", lambda r: f"{r['null_whole']:.1f}; {r['null_whole_held']:g}"),
        ("Grown bodies in forms kept 90% to one medium", lambda r: f"{r['sorted']:.0%}"),
        ("e067's measure: common current shapes kept 90% to one medium", lambda r: f"{r['confined_shape']:.0%}"),
        ("The same on birth signatures (medium shuffled)", lambda r: f"{r['confined_signature']:.0%} ({r['confined_signature_null']:.0%})"),
    ]
    tbl = "".join(f"<tr><td>{name}</td>" + "".join(f"<td>{f(R[run])}</td>" for run in RUNS) + "</tr>" for name, f in table_rows)

    charts_count = [
        grouped("By birth form, breath adds kinds the shuffle takes away",
                "Mean kinds holding 5% of the grown bodies over six censuses. A bar as high as its shuffled neighbours is a count the forms do not make. Dashed: stage C's 4.",
                [("per body, with the medium", "body_medium", READING["body"]), ("per lineage (e060)", "lineage_e060", READING["lineage"]),
                 ("by birth form", "form", READING["form"]), ("form, medium shuffled", "null_medium", READING["medium"]),
                 ("form, all shuffled", "null_whole", READING["whole"])], "kinds", line=4, height=2.9),
        grouped("Held at every census: 4 kinds at breath 0.01",
                "Kinds at 5% in all six censuses of the second half (2.5 years). Stage C's line asks for 4 over 5 years.",
                [("by birth form", "form_held", READING["form"]), ("medium shuffled", "null_medium_held", READING["medium"]),
                 ("all shuffled", "null_whole_held", READING["whole"])], "kinds held", line=4, height=2.9, integer=True),
    ]
    charts_forms = [
        sizes_chart("e066: two forms in one lineage, in both media", "Lineage 1's dense grown bodies by birth size. Two humps are two forms; the same humps on land and in water would be forms not sorted by medium.", "e066", "1"),
        sizes_chart("Breath 0.01: the large form keeps to land", "Lineage 1640's dense grown bodies by birth size. On land a hump at 48-51 blocks; in the water the small forms.", "breath 0.01", "1640"),
    ]
    charts_kinds = [
        kinds_chart("Breath 0.01: kinds in the water, at the shore, and small ones on land",
                    "Grown bodies by kind over six censuses, coloured by medium. Solid: held at every census. Dashed: 5%.", "breath 0.01"),
        sweep_chart("The gain by medium under other lines",
                    "Kinds by birth form less the count with the medium shuffled. Above zero, forms add kinds by medium."),
    ]
    charts_fix = [
        grouped("e067's shapes by medium were partly damage",
                "Grown bodies in shapes or signatures of 20+ bodies that keep 90% to one medium. Current shapes include blocks lost to breaks.",
                [("current shapes (e067)", "confined_shape", READING["body"]), ("birth signatures", "confined_signature", READING["form"]),
                 ("signatures, medium shuffled", "confined_signature_null", READING["medium"])], "kept to one medium", pct=True),
    ]

    TEXT["tldr"] = (f"Each grown body is now counted under the way of living of its birth form, the body its genes develop, read over all such bodies. "
                    f"Breath adds kinds by medium: {b01['form']:.1f} kinds at 0.01, {b01['null_medium']:.1f} with the medium shuffled inside lineages; "
                    f"e065 and e066 gain none. The kinds are the largest lineage's water forms, not its land forms. Per body every run reads 5-7. "
                    f"Stage C counts by birth form; next #83.")
    TEXT["question"] = ("Stage C passes on kinds of living, and e060 counts one way of living per lineage. e067 found open water forms and closed land "
                        "forms inside each large lineage, which that count cannot see. #82 asked for a kind below the lineage that is a way of living, "
                        "not a shape and not where a body happened to stand. Candidates were tried on the runs they judge; e067 and #82 set what to expect:")
    TEXT["hyp"] = ["e067's forms by medium are kinds: a count below the lineage reads more at breath than with the medium shuffled inside lineages, and not in e065 or e066.",
                   "#82's first candidate sees them: e060's way with the medium, counted per body.",
                   "The count is not of shapes: its kinds differ in food or place and do not follow the number of forms."]
    TEXT["world"] = ("No runs. A birth form is a signature (side; blocks of each kind, bite and density at birth) with 20 or more grown bodies; "
                     "rarer bodies join the nearest form of their lineage and layer. The logged cells are the body after breaks.")
    TEXT["runs"] = ("e065; e066 at dry 0.004; e067 at breath 0.003 and 0.01: c1225, seed 9, the six censuses of the second half, 2,800-3,300 "
                    "grown bodies each. Nulls shuffle five times. We compare:")
    TEXT["measures"] = [
        ("Per body", "e060's way of living with the medium the body stands in."),
        ("Per lineage", "e060: each body under its lineage's commonest way."),
        ("By birth form", "each body under its form's way (Figure 1)."),
        ("Nulls", "the same with the medium, or all a body does, shuffled inside lineages."),
        ("Kept to a medium", "e067's measure, on current shapes and on birth signatures."),
    ]
    TEXT["v1"] = (f"by birth form {b01['form']:.1f} kinds at 0.01 and {b003['form']:.1f} at 0.003, against {b01['null_medium']:.1f} and {b003['null_medium']:.1f} "
                  f"shuffled; e065 {e65['form']:.1f} and {e65['null_medium']:.1f}, e066 {e66['form']:.1f} and {e66['null_medium']:.1f}.")
    TEXT["v2"] = (f"{e65['body_medium']:.1f}, {e66['body_medium']:.1f}, {b003['body_medium']:.1f} and {b01['body_medium']:.1f} kinds, highest in e066; "
                  "a shuffle of the medium moves none by more than 0.2.")
    TEXT["v3"] = (f"{b01['forms']:.0f} forms make {b01['form']:.1f} kinds at 0.01; its held kinds at the surface eat 87% algae, on the bottom 88% litter.")
    TEXT["r1"] = ("Per body the medium multiplies e060's parts by three, giving 5-7 in every run at the shuffle. Under a form's commonest way, forms "
                  "that straddle a cut split, and e066 reads 6.7 against 3.2 shuffled. Read over all a form's bodies, with 90% asked for a medium, "
                  "e065 and e066 sit at their shuffles and breath gains 1.1-1.9 kinds.")
    TEXT["r2"] = ("Forms inside a lineage are not new. e065's largest lineage is born at 24-27 or 36-39 blocks in the same proportions on land and in "
                  "water. e066's is born at 48-51 blocks in 65% of its dense land bodies and 39% of its water bodies. Breath sharpens that: "
                  "lineage 1640's is 35% against 7%.")
    TEXT["r3"] = ("Four kinds hold at every census at breath 0.01: two at the shore, the surface's algae eaters born at 18 blocks and the bottom's "
                  "litter eaters at 23, most of them lineage 908. A dense flesh eater at the shore holds 5% in five censuses. Forms kept to land "
                  "hold 3-4% each, 49-block bodies of many small lineages.")
    TEXT["r4"] = ("e067 read 85% from current shapes, a measure that gives 58% in e065. By birth signature it is 64%, and 33% in e066. The gain by "
                  "medium stands with forms from 10 or 50 bodies and at a 95% line; at 80% e066 gains most, as more of its forms keep 80% to a medium.")
    TEXT["gallery"] = "The commonest intact birth body of the largest form of six kinds at breath 0.01. The dashed line is the front."
    TEXT["d1"] = ("A lineage joins mates within 6 genes, so it is too coarse a unit for a kind: the largest lineage of every run holds two or more "
                  "birth forms. A form is what a child inherits. Reading its way over all its bodies keeps e060's point that one body's diet, "
                  "tooth or range partly records where it stood and what broke it.")
    TEXT["d2"] = ("Breath made the water's forms kinds and left the land's closed forms inside shore kinds. The large lineages' land bodies are "
                  "born in forms that also live in the water, so the land price (dry air) sorts fewer forms than the water price (breath).")
    TEXT["d3"] = ("Not shown: other seeds, c1236, runs long enough for the pass line's 5 years, forms that differ in the place of their blocks but "
                  "not in their counts, and whether a kind is held by the world or by the seed (#72's invasion).")
    TEXT["conclusion"] = ("Stage C counts kinds of living by birth form from here, with the pass line's numbers: at least 4 kinds held at 5% of the "
                          "grown bodies for 5 years, on 4 seeds of 6, beside the count by lineage and the shuffled count. Breath 0.01 holds 4 over "
                          "2.5 years. Next: #83, life-history values from the genome.")

    count = lambda v: len((" ".join(v) if isinstance(v, list) and v and isinstance(v[0], str) else " ".join(" ".join(t) for t in v) if isinstance(v, list) else v).split())
    words = sum(count(v) for v in TEXT.values()) + sum(len(p[2].split()) for p in GALLERY_PICKS)
    print(f"TEXT: {words} words")
    for k, v in TEXT.items():
        print(f"  {k}: {count(v)}")

    gal = gallery(GALLERY_PICKS, TEXT["gallery"])
    hyp = "".join(f"<li>{html.escape(h)}</li>" for h in TEXT["hyp"])
    measures = "".join(f"<li><strong>{html.escape(k)}</strong> - {html.escape(v)}</li>" for k, v in TEXT["measures"])
    head = "".join(f"<th>{html.escape(LABEL[r])}</th>" for r in RUNS)
    appendix = "\n".join([
        table("counts", ["run", "step", "body_medium", "lineage", "form", "null_medium", "null_whole"]),
        table("kinds", ["run", "kind", "share", "censuses", "forms", "lineages", "top_lineages", "born_size", "density", "open_born", "grass", "algae", "detritus", "meat", "kills", "land", "surface", "bottom"]),
        table("sweep", ["run", "keep", "form_min", "form", "form_held", "null_medium", "null_medium_held", "null_whole", "null_whole_held"]),
        table("apart", ["run", "part", "groups", "balanced", "at_0.8", "null"]),
    ])
    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>e068 kinds of living inside a lineage - Report</title>
<style>{CSS}</style>
</head>
<body>
<main>
<h1>e068: kinds of living inside a lineage</h1>
<p class="sub">Experiment report - 2026-09-14 - analysis only: the censuses of e065, e066 and e067 on c1225, seed 9, counted by birth form (foundation stage C, sixth step, #82)</p>

<section class="tldr">
<h2>TL;DR</h2>
<p>{html.escape(TEXT["tldr"])}</p>
</section>

<h2>1. Question</h2>
<p>{html.escape(TEXT["question"])}</p>
<ol>{hyp}</ol>

<h2>2. The census</h2>
<p>{html.escape(TEXT["world"])}</p>
{DIAGRAM}
<p><strong>Runs.</strong> {html.escape(TEXT["runs"])}</p>
<ul class="measures">{measures}</ul>

<h2>3. Results</h2>
<div class="tw"><table>
<thead><tr><th>Second half of the run</th>{head}</tr></thead>
<tbody>{tbl}</tbody></table></div>
<ol class="verdicts">
<li><span class="verdict">Yes</span> 1, e067's forms by medium are kinds: {html.escape(TEXT["v1"])}</li>
<li><span class="verdict no">No</span> 2, per body with the medium sees them: {html.escape(TEXT["v2"])}</li>
<li><span class="verdict">Yes</span> 3, not a count of shapes: {html.escape(TEXT["v3"])}</li>
</ol>

<h3>3.1 Only by birth form does breath add kinds</h3>
<div class="grid2">{"".join(charts_count)}</div>
<p>{html.escape(TEXT["r1"])}</p>

<h3>3.2 Lineages hold forms; breath sorts them by medium</h3>
<div class="grid2">{"".join(charts_forms)}</div>
<p>{html.escape(TEXT["r2"])}</p>

<h3>3.3 The water's forms are kinds, the land's are not</h3>
<div class="grid2">{charts_kinds[0]}</div>
<p>{html.escape(TEXT["r3"])}</p>
{gal}

<h3>3.4 e067 corrected, and other lines</h3>
<div class="grid2">{charts_fix[0]}{charts_kinds[1]}</div>
<p>{html.escape(TEXT["r4"])}</p>

<h2>4. Discussion</h2>
<p>{html.escape(TEXT["d1"])}</p>
<p>{html.escape(TEXT["d2"])}</p>
<p>{html.escape(TEXT["d3"])}</p>

<h2>5. Conclusion and next step</h2>
<p>{html.escape(TEXT["conclusion"])}</p>

<h2>Appendix: data</h2>
<p>Every census's counts, every kind, the thresholds moved and the born-apart test (balanced nearest-neighbour accuracy on birth traits, 0.5 = none) are in <code>experiments/e068_kinds/results/</code>; birth sizes by medium in <code>sizes.csv</code>, one row per run in <code>runs.csv</code>. Build with <code>uv run python experiments/e068_kinds/kinds.py</code>, then <code>report.py</code>.</p>
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
