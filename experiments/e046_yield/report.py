#!/usr/bin/env python3
"""Build report.html for this experiment.

Charts: matplotlib, exported as SVG and inlined. Diagram: hand-written SVG.
Run from the repo root: uv run python experiments/e046_yield/report.py
(`report.py lineages` prints the top lineages of every run, to pick the gallery;
`report.py numbers` prints the measures over the second half, for the README.)
"""
import csv
import html
import io
import json
import os
import re
from collections import Counter, defaultdict

import matplotlib
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator

matplotlib.use("svg")

HERE = os.path.dirname(os.path.abspath(__file__))
E045 = os.path.join(os.path.dirname(HERE), "e045_connect")  # the control runs live there
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#8a8a86", "#c9c8c0", "#7b61ff"]  # fixed slot order; slot 5 is the control
KIND_COLOR = {1: SERIES[0], 2: SERIES[1], 3: SERIES[3], 4: SERIES[2]}
CONFIRM_STEPS = 5000

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

BASE = "128_sigma0_r64_f0_flat_eyes8_flesh1_w1_season2_digest0_sidegrow_store5_yolk0_breed0_winterhigh_water0.1_leach0.01_depth0.01_mix0.2_strict_sat_hold_wear3000_connect"
YIELD = 0.5


def run(law, seed):
    """law 0: e045's connect run (the control, in e045's folder); 1: plant_yield YIELD."""
    return f"{BASE}{f'_plant{YIELD}' if law else ''}_seed{seed}"


def folder(law):
    return HERE if law else E045


LAWS = {0: ("control (e045)", 5), 1: (f"plant_yield {YIELD}", 0)}  # name, color slot
STEPS = 100_000
SEASON = 20_000
LOG = 10_000  # steps per log.csv row
SEEDS = [9, 10, 11, 12, 13, 14]
STATE_LINE = 0.03  # blocks broken per body per step: above it a hunter world (e045: 0.045-0.079, grazer 0.012-0.018)
MUSCLE_FREE = 0.5  # a lineage with a mean muscle under this is muscle-free

# ---------- data ----------

def load_csv(path, folder=HERE):
    """Read a CSV of numbers into {column: [floats]}."""
    with open(os.path.join(folder, path)) as f:
        rows = [r for r in csv.DictReader(f) if None not in r.values()]
    return {k: [float(r[k]) for r in rows] for k in rows[0]}


def load_rows(path, folder=HERE):
    with open(os.path.join(folder, path)) as f:
        return [r for r in csv.DictReader(f) if None not in r.values()]


def lineage_rows(run, folder=HERE):
    by = defaultdict(list)
    for r in load_rows(f"results/{run}_lineages.csv", folder):
        by[int(r["lineage"])].append(r)
    return by


def load_bodies(run, folder=HERE):
    out = {}
    with open(os.path.join(folder, f"results/{run}_bodies.jsonl")) as f:
        for line in f:
            try:
                d = json.loads(line)
            except json.JSONDecodeError:
                break
            out[d["id"]] = (int(d.get("side", 8)), d["cells"])
    return out


def read_frames(path, folder=HERE):
    with open(os.path.join(folder, path)) as f:
        for line in f:
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                return


def exists(run, folder=HERE):
    """A run whose log has rows (a run still writing keeps its log empty until its buffer flushes)."""
    path = os.path.join(folder, f"results/{run}_log.csv")
    return os.path.exists(path) and os.path.getsize(path) > 200


def half(d, lo=STEPS // 2, hi=STEPS):
    return [i for i, t in enumerate(d["step"]) if lo < t <= hi]


def half_mean(d, key, lo=STEPS // 2, hi=STEPS):
    """The mean of a column over the rows with lo < step <= hi."""
    idx = half(d, lo, hi)
    return sum(d[key][i] for i in idx) / len(idx) if idx else float("nan")


def eaten(d, i):
    """(plant taken, plant digested, flesh of kills, dead scavenged) per step in log row i. The log's
    dung is the plant taken and not digested (with digest 0 the flesh leaves none), per step already."""
    hunted = d["kill_gain"][i] * d["cells_broken"][i] / LOG
    plant = d["plant_intake"][i] / LOG
    return plant + d["dung"][i], plant, hunted, d["meat_intake"][i] / LOG - hunted


def muscle_free(run, folder, lo=STEPS // 2, hi=STEPS):
    """The share of the bodies (in lineages of 5 or more) whose lineage has a mean muscle under MUSCLE_FREE, lo < step <= hi."""
    tot = free = 0.0
    for r in load_rows(f"results/{run}_lineages.csv", folder):
        if lo < int(r["step"]) <= hi:
            n = float(r["size"])
            tot += n
            free += n if float(r["muscle"]) < MUSCLE_FREE else 0.0
    return free / max(tot, 1e-9)


def stats(law, seed):
    """One run over the second half, or None if it is missing."""
    r, fo = run(law, seed), folder(law)
    if not exists(r, fo):
        return None
    d, f = load_csv(f"results/{r}_log.csv", fo), fine(r, fo)
    idx = half(d)
    food = [eaten(d, i) for i in idx]
    taken, plant, hunted, scav = (sum(x[j] for x in food) / len(food) for j in range(4))
    bodies = half_mean(f, "pop")
    broken = half_mean(d, "cells_broken") / LOG
    div, wins = diversity(r, fo)
    w = floors(f)
    return dict(bodies=bodies, floors=[x["pop"] for x in w], floor=min(x["pop"] for x in w),
                births=half_mean(d, "births") / LOG, age=half_mean(f, "age_mean"), lineages=half_mean(f, "lineages"),
                broken=broken, per_body=broken / bodies, contacts=half_mean(d, "contacts") / LOG / bodies,
                taken=taken, plant=plant, dung=taken - plant, hunted=hunted, scav=scav,
                share=hunted / (plant + hunted + scav), share_taken=hunted / (taken + hunted + scav),
                free=muscle_free(r, fo), muscle=half_mean(d, "muscle_mean"), gut=half_mean(d, "digestive_mean"),
                size=half_mean(d, "size_p50"), hunter=broken / bodies >= STATE_LINE,
                top=top_lineage(r, fo), div=div, wins=len(wins))


# ---------- the diversity number (#42), copied from e039 ----------
# The winners of a window are the lineages holding at least WIN_SHARE of its body-steps. Two
# winners are the same body when their sizes are within SIZE_FACTOR and the mixes of their blocks
# differ by at most MIX_DIST in sum; single linkage on that relation, the number of groups.
WIN_SHARE = 0.05
SIZE_FACTOR = 1.5
MIX_DIST = 0.4
KIND_COLS = ["hard", "muscle", "sensor", "digestive"]
PLACE_COL = {"world": "size", "valley": "p0", "slope": "p1", "ridge": "pnone"}


def same_body(a, b):
    """Two mean bodies (counts by kind) are the same shape."""
    sa, sb = sum(a), sum(b)
    if sa <= 0 or sb <= 0:
        return False
    if max(sa, sb) > SIZE_FACTOR * min(sa, sb):
        return False
    return sum(abs(x / sa - y / sb) for x, y in zip(a, b)) <= MIX_DIST


def diversity(run, folder=HERE, place="world", window=None):
    """(diversity, winners): the groups of winner bodies, and the winners, over `window` steps."""
    rows = load_rows(f"results/{run}_lineages.csv", folder)
    if not rows:
        return 0, []
    steps = [int(r["step"]) for r in rows]
    lo, hi = window or (max(steps) - (max(steps) - min(steps)) // 3, max(steps))
    col = PLACE_COL[place]
    total, shape = defaultdict(float), defaultdict(lambda: [0.0] * len(KIND_COLS))
    for r in rows:
        if not lo <= int(r["step"]) <= hi:
            continue
        n = float(r[col])
        if n <= 0:
            continue
        i = int(r["lineage"])
        total[i] += n
        for j, k in enumerate(KIND_COLS):
            shape[i][j] += n * float(r[k])
    body_steps = sum(total.values())
    if body_steps <= 0:
        return 0, []
    win = sorted((i for i, n in total.items() if n >= WIN_SHARE * body_steps), key=lambda i: -total[i])
    mean = {i: [x / total[i] for x in shape[i]] for i in win}
    groups = []
    for i in win:
        hit = [g for g in groups if any(same_body(mean[i], mean[j]) for j in g)]
        if hit:
            merged = [i] + [j for g in hit for j in g]
            groups = [g for g in groups if g not in hit] + [merged]
        else:
            groups.append([i])
    return len(groups), [(i, total[i] / body_steps, sum(mean[i]), mean[i]) for i in win]


def fine(run, folder=HERE, last_step=STEPS):
    """Every 1,000 steps (pop.csv): the bodies alive and their mean age; lineages of 5 or more."""
    lin = Counter()
    for rows in lineage_rows(run, folder).values():
        for r in rows:
            if int(r["step"]) <= last_step:
                lin[int(r["step"])] += 1
    d = load_csv(f"results/{run}_pop.csv", folder)
    keep = [i for i, t in enumerate(d["step"]) if t <= last_step]
    out = {k: [v[i] for i in keep] for k, v in d.items()}
    out["lineages"] = [lin[int(t)] for t in out["step"]]
    return out


def floors(f):
    """Per season window: the trough (bodies, lineages) and the peak."""
    out = []
    for c in range(int(max(f["step"])) // SEASON):
        idx = [i for i, t in enumerate(f["step"]) if c * SEASON < t <= (c + 1) * SEASON]
        if not idx:
            continue
        lo = min(idx, key=lambda i: f["pop"][i])
        hi = max(idx, key=lambda i: f["pop"][i])
        out.append(dict(step=int(f["step"][lo]), pop=int(f["pop"][lo]), lin=f["lineages"][lo], peak=int(f["pop"][hi])))
    return out


def top_lineage(run, folder=HERE):
    """The lineage holding the most body-steps of the last third: (id, share, mean cells, muscle, gut, flesh share, length, width)."""
    rows = load_rows(f"results/{run}_lineages.csv", folder)
    steps = [int(r["step"]) for r in rows]
    lo = max(steps) - (max(steps) - min(steps)) // 3
    total, muscle, gut, cells, meat, plant, fwd, side = (defaultdict(float) for _ in range(8))
    for r in rows:
        if int(r["step"]) < lo:
            continue
        i, n = int(r["lineage"]), float(r["size"])
        total[i] += n
        muscle[i] += n * float(r["muscle"])
        gut[i] += n * float(r["digestive"])
        cells[i] += n * sum(float(r[k]) for k in KIND_COLS)
        meat[i] += n * float(r["meat"])
        plant[i] += n * float(r["plant"])
        fwd[i] += n * float(r["len_fwd"])
        side[i] += n * float(r["len_side"])
    i = max(total, key=total.get)
    all_n = sum(total.values())
    return (i, total[i] / all_n, cells[i] / total[i], muscle[i] / total[i], gut[i] / total[i], meat[i] / max(meat[i] + plant[i], 1e-9),
            fwd[i] / total[i], side[i] / total[i])


# ---------- chart helpers ----------

def kfmt(x, _pos):
    return f"{x/1000:g}k" if abs(x) >= 1000 else f"{x:g}"


def to_svg(fig):
    buf = io.StringIO()
    fig.savefig(buf, format="svg", bbox_inches="tight", pad_inches=0.05)
    plt.close(fig)
    return buf.getvalue()


def new_axes(xlabel="step", size=(6.4, 2.6)):
    fig, ax = plt.subplots(figsize=size)
    if xlabel == "step":
        ax.xaxis.set_major_formatter(kfmt)
    ax.set_xlabel(xlabel, loc="right")
    ax.margins(x=0)
    if xlabel == "seed":
        ax.xaxis.set_major_locator(MaxNLocator(integer=True))
        ax.margins(x=0.06)
    return fig, ax


def legend_above(ax, n):
    ax.legend(loc="lower left", bbox_to_anchor=(0, 1.0), ncols=n, handlelength=1.8, borderaxespad=0, columnspacing=1.2)


def line_chart(title, subtitle, series, ymin=None, ymax=None, percent=False, xlabel="step", fmt=None, ncols=2, markers=False, msize=3):
    """series: list of (label, xs, ys, slot, line style)."""
    fig, ax = new_axes(xlabel)
    for label, xs, ys, slot, ls in series:
        ax.plot(xs, ys, color=SERIES[slot], linewidth=1.6, label=label, linestyle=ls, marker="o" if markers else None, markersize=msize)
    top = max((v for _, _, ys, _, _ in series for v in ys if v == v), default=1.0)
    if ymin is not None:
        ax.set_ylim(ymin, ymax if ymax is not None else top * 1.15)
    ax.yaxis.set_major_formatter(fmt or ((lambda y, _p: f"{y:.0%}") if percent else kfmt))
    ax.yaxis.set_major_locator(MaxNLocator(4, steps=[1, 2, 5, 10]))  # no 2.5 step: a 2.5% tick would read "2%"
    legend_above(ax, ncols)
    return figure(title, subtitle, to_svg(fig))


def seed_chart(title, subtitle, st, key, percent=False, ymax=None, hline=None, fmt=None):
    """One dot per seed and law: st[law][seed][key]; `hline` draws a dotted reference line."""
    series = [(LAWS[law][0], [s + dx for s in SEEDS if st[law][s]], [st[law][s][key] for s in SEEDS if st[law][s]], LAWS[law][1], "none")
              for law, dx in ((0, -0.08), (1, 0.08))]
    fig, ax = new_axes("seed")
    for label, xs, ys, slot, ls in series:
        ax.plot(xs, ys, color=SERIES[slot], linestyle=ls, marker="o", markersize=7, label=label)
    if hline is not None:
        ax.axhline(hline, color=INK, linewidth=1, linestyle=":")
    top = max((v for _, _, ys, _, _ in series for v in ys), default=1.0)
    ax.set_ylim(0, ymax if ymax is not None else top * 1.15)
    ax.yaxis.set_major_formatter(fmt or ((lambda y, _p: f"{y:.0%}") if percent else kfmt))
    ax.yaxis.set_major_locator(MaxNLocator(4, steps=[1, 2, 5, 10]))
    legend_above(ax, 2)
    return figure(title, subtitle, to_svg(fig))


def figure(title, subtitle, svg):
    return f"""
<figure class="fig">
  <figcaption><strong>{html.escape(title)}</strong><span>{html.escape(subtitle)}</span></figcaption>
  {svg}
</figure>"""


def data_table(cols, rows_by_name, every=1):
    """Collapsed tables for the appendix. rows_by_name: {name: {col: [values]}}."""
    out = []
    for name, d in rows_by_name.items():
        cs = [c for c in cols if c in d]
        rows = "".join("<tr>" + "".join(f"<td>{d[c][i]:g}</td>" for c in cs) + "</tr>" for i in range(0, len(d[cs[0]]), every))
        out.append(f"<details><summary>{html.escape(name)}</summary><div class='tw'><table><thead><tr>"
                   + "".join(f"<th>{c}</th>" for c in cs) + f"</tr></thead><tbody>{rows}</tbody></table></div></details>")
    return "\n".join(out)


def gallery(picks, caption):
    """picks: [(label, law, seed, lineage id, name, what the shape does)]. The most common grown body of each lineage
    at its peak, on the grid it grew on (drawn at the same width whatever the side), front up."""
    cards = []
    cache = {}
    for label, law, seed, lid, name, what in picks:
        r, fo = run(law, seed), folder(law)
        if r not in cache:
            cache[r] = (lineage_rows(r, fo), load_bodies(r, fo), list(read_frames(f"results/{r}_long.jsonl", fo)))
        by, bodies, frames = cache[r]
        rows = by[lid]
        peak = max(rows, key=lambda x: int(x["size"]))
        span = int(rows[-1]["step"]) - int(rows[0]["step"]) + CONFIRM_STEPS
        frame = min((fr for fr in frames if any(a[4] == lid for a in fr["agents"])), key=lambda fr: abs(fr["step"] - int(peak["step"])))
        # The most common body among the grown ones (at least three quarters of the lineage's
        # mean cells at its peak): a lineage in bloom is mostly newborns of one or two cells.
        grown = 0.75 * sum(float(peak[k]) for k in KIND_COLS)
        ids = [a[2] for a in frame["agents"] if a[4] == lid]
        c = Counter(i for i in ids if sum(ch != "0" for ch in bodies[i][1]) >= grown) or Counter(ids)
        side, cells = bodies[c.most_common(1)[0][0]]
        u = 88 / side
        rects = "".join(f'<rect x="{(i % side) * u:.2f}" y="{(i // side) * u:.2f}" width="{u * 0.9:.2f}" height="{u * 0.9:.2f}" fill="{KIND_COLOR[int(k)]}"/>' for i, k in enumerate(cells) if k != "0")
        m, pl = float(peak["meat"]), float(peak["plant"])
        meat = m / (m + pl) if m + pl > 0 else 0
        cards.append(f"""<figure class="card"><svg viewBox="-1 -1 89 89" width="120" height="120" role="img" aria-label="{html.escape(name)}"><rect x="-1" y="-1" width="89" height="89" fill="var(--cell)"/>{rects}<line x1="-1" y1="-0.5" x2="88" y2="-0.5" stroke="var(--ink2)" stroke-width="1.5" stroke-dasharray="3 2"/></svg>
<figcaption><strong>{html.escape(name)}</strong><br>{html.escape(label)}, lineage {lid}: {span:,} steps, {int(peak["size"]):,} agents at its peak<br>side {float(peak["side"]):.0f} (grid {side}x{side}); mass {float(peak["mass"]):.0f}: hard {float(peak["hard"]):.0f}, muscle {float(peak["muscle"]):.0f}, sensor {float(peak["sensor"]):.1f}, digestive {float(peak["digestive"]):.0f}; flesh {meat:.0%} of the intake; mean age {float(peak["age"]):.0f}<br>{html.escape(what)}</figcaption></figure>""")
    return f"""<figure class="diagram"><div class="cards">{"".join(cards)}</div>
<figcaption>{caption}</figcaption></figure>"""


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
th:first-child, td:first-child {{ text-align: left; white-space: nowrap; }}
th {{ color: var(--ink2); font-weight: 600; }}
.tw {{ overflow-x: auto; margin: 8px 0; }}
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


def box(x, y, w, h, label, sub=None, accent=False):
    stroke = ' stroke="var(--s1)" stroke-width="2"' if accent else ""
    fill = ' fill="var(--s1)"' if accent else ' fill="currentColor"'
    t = f'<text x="{x + w / 2}" y="{y + (h / 2 + 4 if sub is None else h / 2 - 3)}" text-anchor="middle" stroke="none"{fill} font-weight="600">{label}</text>'
    if sub:
        t += f'<text x="{x + w / 2}" y="{y + h / 2 + 12}" text-anchor="middle" stroke="none" fill="currentColor" font-size="11">{sub}</text>'
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="none"{stroke}/>{t}'


# Hand-written mechanism diagram. Label every arrow; currentColor for lines and text;
# var(--s1) for the one element the argument hinges on (what the body keeps of each food).
# Keep 10-15px between text and lines.
DIAGRAM = f"""
<figure class="fig diagram">
<svg viewBox="0 0 900 250" width="100%" role="img" aria-label="A gut digests half of the plant matter it takes and the rest goes as dung to the soil of the cell, where the plant grows again by the light; the flesh of a kill or of the dead is digested whole" font-size="12" fill="currentColor" stroke="currentColor">
  <defs><marker id="ar" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="currentColor" stroke="none"/></marker></defs>
  <g fill="none" stroke-width="1.2">
    {box(20, 40, 170, 46, "plant matter", "standing plant, fruit, ground")}
    {box(330, 40, 110, 46, "a gut block")}
    {box(570, 40, 150, 46, "the body's energy", accent=True)}
    {box(330, 170, 110, 46, "soil of the cell")}
    {box(760, 40, 130, 46, "flesh", "a broken block, the dead")}
    <path d="M190,63 L328,63" marker-end="url(#ar)"/>
    <path d="M440,63 L568,63" marker-end="url(#ar)"/>
    <path d="M385,86 L385,168" marker-end="url(#ar)"/>
    <path d="M330,193 L105,193 L105,88" marker-end="url(#ar)"/>
    <path d="M760,63 L722,63" marker-end="url(#ar)"/>
  </g>
  <g stroke="none">
    <text x="204" y="54">a bite, 0.02</text>
    <text x="204" y="80" font-size="11">per gut block a step</text>
    <text x="452" y="54" fill="var(--s1)" font-weight="600">plant_yield: 0.5</text>
    <text x="452" y="80" font-size="11">digested</text>
    <text x="397" y="124">the rest: dung</text>
    <text x="397" y="140" font-size="11">(0.5 of the bite)</text>
    <text x="120" y="182" font-size="11">grows again by the light</text>
    <text x="741" y="28" text-anchor="middle" fill="var(--s1)" font-weight="600">all of it</text>
    <text x="570" y="112" font-size="11">pays the upkeep (0.002 a block, 0.032 a body),</text>
    <text x="570" y="127" font-size="11">a share fixed as fat, the rest breathed</text>
  </g>
</svg>
<figcaption>Figure 1. Plant matter is harder to digest than flesh, for every gut. A gut keeps half of the plant it takes; the other half falls as dung to the soil of the cell, where the plant grows again by the light. The flesh of a kill or of the dead is kept whole, so a block of flesh carries twice the plant it was made of.</figcaption>
</figure>
"""


TEXT = {}  # filled in main(); counted at the end


def all_stats():
    return {law: {s: stats(law, s) for s in SEEDS} for law in LAWS}


def numbers():
    """The measures over the second half, per run (for the README)."""
    st = all_stats()
    for s in SEEDS:
        for law in LAWS:
            x = st[law][s]
            if not x:
                continue
            i, share, cells, muscle, gut, meat, fwd, side = x["top"]
            print(f"seed {s} {LAWS[law][0]:16s} {'HUNTER' if x['hunter'] else 'grazer'} broken/body/step {x['per_body']:.4f} ({x['broken']:.0f}/step) contacts/body {x['contacts']:.3f} "
                  f"| taken {x['taken']:.1f} plant digested {x['plant']:.1f} dung {x['dung']:.1f} kills {x['hunted']:.1f} dead {x['scav']:.1f} "
                  f"kills' share {x['share']:.1%} of digested, {x['share_taken']:.1%} of taken")
            print(f"      bodies {x['bodies']:.0f} floors {x['floors']} births {x['births']:.2f} age {x['age']:.0f} lineages {x['lineages']:.1f} "
                  f"| muscle-free {x['free']:.0%} muscle {x['muscle']:.2f} gut {x['gut']:.2f} size p50 {x['size']:.1f} "
                  f"| top {i} {share:.0%} {cells:.1f} cells {muscle:.1f} muscle {gut:.1f} gut {meat:.0%} flesh {fwd:.1f}x{side:.1f} | diversity {x['div']} of {x['wins']}")
    for law in LAWS:
        xs = [st[law][s] for s in SEEDS if st[law][s]]
        print(f"{LAWS[law][0]}: hunter worlds {sum(x['hunter'] for x in xs)} of {len(xs)}; bodies {sum(x['bodies'] for x in xs) / max(len(xs), 1):.0f}")


def main():
    st = all_stats()
    logs = {s: load_csv(f"results/{run(1, s)}_log.csv") for s in SEEDS if st[1][s]}

    charts_world = [
        seed_chart("Bodies, by seed", "Bodies alive over the second half (steps 50,000-100,000).", st, "bodies"),
        seed_chart("The lowest winter floor, by seed", "The fewest bodies alive in any of the five winters.", st, "floor"),
    ]
    charts_state = [
        seed_chart("Blocks broken per body per step, by seed", "Second half. Above the dotted line (0.03) a hunter world, below it a grazer world; the yield does not enter it.",
                   st, "per_body", hline=STATE_LINE, fmt=lambda y, _p: f"{y:g}"),
        seed_chart("The flesh of kills in what the bodies digest, by seed", "Second half. Two levels under both laws, one per state: the seed picks the level, not the law.",
                   st, "share", percent=True, ymax=0.5),
    ]
    charts_sit = [
        seed_chart("Bodies in muscle-free lineages, by seed", "Share of the bodies whose lineage has a mean muscle under 0.5, second half.", st, "free", percent=True, ymax=1.0),
        seed_chart("Gut blocks per body, by seed", "The mean number of gut blocks in a living body, second half.", st, "gut", fmt=lambda y, _p: f"{y:g}"),
    ]

    def top_text(t):
        _i, share, cells, muscle, gut, meat, _f, _s = t
        return f"{share:.0%}: {cells:.0f} cells, {muscle:.0f} muscle, {gut:.0f} gut, {meat:.0%} flesh"

    def pair(s, key, f):
        a, b = st[0][s], st[1][s]
        return f"<td>{f(a[key])} / {f(b[key])}</td>"

    state = lambda h: "hunter" if h else "grazer"
    seed_rows = "".join(
        f"<tr><td>{s}</td>{pair(s, 'hunter', state)}{pair(s, 'per_body', lambda v: f'{v:.3f}')}{pair(s, 'share', lambda v: f'{v:.0%}')}"
        f"{pair(s, 'free', lambda v: f'{v:.0%}')}{pair(s, 'gut', lambda v: f'{v:.1f}')}{pair(s, 'bodies', lambda v: f'{v:,.0f}')}{pair(s, 'floor', lambda v: f'{v:,}')}"
        f"<td>{top_text(st[1][s]['top'])}</td></tr>"
        for s in SEEDS if st[0][s] and st[1][s])
    food_rows = "".join(
        f"<tr><td>{s}</td>{pair(s, 'taken', lambda v: f'{v:.0f}')}{pair(s, 'plant', lambda v: f'{v:.0f}')}{pair(s, 'hunted', lambda v: f'{v:.0f}')}"
        f"{pair(s, 'scav', lambda v: f'{v:.0f}')}{pair(s, 'share_taken', lambda v: f'{v:.0%}')}{pair(s, 'contacts', lambda v: f'{v:.2f}')}{pair(s, 'births', lambda v: f'{v:.1f}')}</tr>"
        for s in SEEDS if st[0][s] and st[1][s])
    tables = data_table(["step", "pop", "births", "deaths_energy", "deaths_broken", "deaths_wear", "cells_broken", "kill_gain", "plant_intake", "meat_intake",
                         "dung", "contacts", "muscle_mean", "digestive_mean", "size_p50"],
                        {f"{LAWS[1][0]}, seed {s}": d for s, d in logs.items()})
    TEXT.update(TEXTS)
    TEXT["gallery"] = gallery(GALLERY, GALLERY_CAPTION) if GALLERY else ""
    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>e046 Plant matter is harder to digest than flesh - Report</title>
<style>{CSS}</style>
</head>
<body>
<main>
<h1>e046: Plant matter is harder to digest than flesh</h1>
<p class="sub">Experiment report - 2026-09-11 - every gut digests half of the plant it takes and all of the flesh (#49), against e045's connect runs on seeds 9-14. Answer: {TEXT["sub_answer"]}</p>

<section class="tldr">
<h2>TL;DR</h2>
<p>{TEXT["tldr"]}</p>
</section>

<h2>1. Question</h2>
<p>{TEXT["question"]}</p>
<ol>
  <li><strong>The world stands:</strong> six seeds through five winters (no floor under 100 bodies), with 20-50% fewer bodies.</li>
  <li><strong>More hunter worlds:</strong> at least 5 of 6 seeds settle as a hunter world (blocks broken per body per step over 0.03), against 4 of 6.</li>
  <li><strong>Fewer sitters:</strong> muscle-free lineages hold fewer of the bodies than in the control, within each state.</li>
</ol>

<h2>2. The law</h2>
<p>{TEXT["world"]}</p>
{DIAGRAM}
<p><strong>Runs.</strong> {TEXT["runs"]}</p>
<ul class="measures">
  <li><strong>state</strong> - blocks broken per body per step over the second half; over 0.03 a hunter world.</li>
  <li><strong>contacts</strong> - pairs whose blocks met in a push, per body per step.</li>
  <li><strong>eaten</strong> - per step: plant taken and digested, the flesh of kills (the blocks the eater broke), the dead scavenged.</li>
  <li><strong>kills' share</strong> - the flesh of kills over what is digested, and over what is taken.</li>
  <li><strong>muscle-free, gut</strong> - the share of the bodies whose lineage has a mean muscle under 0.5; gut blocks per body.</li>
  <li><strong>bodies, floors, births</strong> - bodies alive every 1,000 steps, the five winter troughs, births a step.</li>
  <li><strong>top lineage, diversity</strong> - the lineage with the most of the last third, and the diversity number (#42).</li>
</ul>

<h2>3. Results</h2>
<p>Means over the second half (steps 50,000-100,000); each cell is control / plant_yield {YIELD}.</p>
<div class="tw"><table>
<thead><tr><th>seed</th><th>state</th><th>broken per body per step</th><th>kills' share of the digested</th><th>muscle-free</th><th>gut blocks per body</th><th>bodies</th><th>lowest floor</th><th>top lineage of the last third, plant_yield {YIELD}</th></tr></thead>
<tbody>{seed_rows}</tbody></table></div>
<div class="tw"><table>
<thead><tr><th>seed</th><th>plant taken</th><th>plant digested</th><th>kills</th><th>dead</th><th>kills' share of the taken</th><th>contacts per body</th><th>births a step</th></tr></thead>
<tbody>{food_rows}</tbody></table></div>
<ol class="verdicts">
{TEXT["verdicts"]}
</ol>

<h3>3.1 {TEXT["h_world"]}</h3>
<div class="grid2">
{"".join(charts_world)}
</div>
<p>{TEXT["p_world"]}</p>

<h3>3.2 {TEXT["h_state"]}</h3>
<div class="grid2">
{"".join(charts_state)}
</div>
<p>{TEXT["p_state"]}</p>

<h3>3.3 {TEXT["h_sit"]}</h3>
<div class="grid2">
{"".join(charts_sit)}
</div>
<p>{TEXT["p_sit"]}</p>
{TEXT["gallery"]}

<h2>4. Discussion</h2>
{TEXT["discussion"]}

<h2>5. Conclusion and next step</h2>
<p>{TEXT["conclusion"]}</p>

<h2>Appendix: data</h2>
<p>Every log step (10,000 steps) of the six runs under the law; the control's are in e045's report. The full data are in <code>results/*.csv</code>. Build this report with <code>uv run python experiments/e046_yield/report.py</code>.</p>
{tables}
</main>
</body>
</html>
"""
    out = os.path.join(HERE, "report.html")
    with open(out, "w") as f:
        f.write(page)
    words = sum(len(re.sub(r"<[^>]+>", " ", html.unescape(v)).split()) for k, v in TEXT.items() if k != "gallery")
    print(f"wrote {out} ({os.path.getsize(out)//1024} KB); TEXT {words} words")


GALLERY = [
    ("plant_yield 0.5, seed 9", 1, 9, 31, "the big gut", "Gut blocks filling a 7x7 grid, no muscle: a bite under every block, and it sits. 60% of the last third."),
    ("plant_yield 0.5, seed 9", 1, 9, 158, "the hunter beside it", "Mostly muscle on a 4x4 grid, gut at one front corner: 85% of what it eats is flesh."),
    ("plant_yield 0.5, seed 13", 1, 13, 121, "the big gut, seed 13", "Gut and sensors on a 7x7 grid, no muscle: the winner of seed 13's hunter world, 70% of the last third."),
    ("plant_yield 0.5, seed 10", 1, 10, 73, "the small hunter", "Muscle and gut on a 4x4 grid, 70% flesh: the plan of the control's hunters, unchanged by the law."),
    ("plant_yield 0.5, seed 11", 1, 11, 377, "the grazer world's winner", "Gut filling a 4x4 grid (some bodies carry muscle); its bodies live 1,300 steps. Seed 11 settles as a grazer world."),
]
GALLERY_CAPTION = ("The most common grown body of each lineage at its peak, front up (orange muscle, aqua gut, yellow sensor, blue hard); "
                   "the numbers are the lineage's means at its peak. In the hunter worlds under the law a big gut without muscle lives beside small hunters.")

TEXTS = {
    "sub_answer": ("the world stands at half its bodies, the seed still picks the state (5 of 6 hunter worlds against 4), and within a state "
                   "the flesh of kills is the same share of what the bodies digest. The sitter answers with a bigger gut. Not kept."),
    "tldr": ("Every gut now digests half of the plant it takes and all of the flesh. On six seeds the world stands at half its bodies "
             "(floors 125-233). Hunter worlds come on 5 of 6 seeds against 4, but within a state the flesh of kills is the same share of "
             "what is digested (28-36% against 30-37%). The sitter grows its gut instead (12-19 gut blocks against 7-12), and muscle-free "
             "lineages hold more of the bodies. Not kept. Next: #14."),
    "question": ("Every gut digested all it took, plant or flesh, and lineages without muscle held 21-47% of the bodies in e045. Real plant "
                 "eaters digest 30-60% of what they eat, flesh eaters 80-90% (#49). If plant matter yields half and flesh all of itself, "
                 "a block of flesh carries twice the plant it was made of. Does hunting then pay against sitting?"),
    "world": ("A gut digests a share plant_yield of the plant matter it takes (the standing plant, the fruit, the ground store) and all of "
              "the flesh (a broken block, the dead), the same for every gut. The rest of the plant is dung, to the soil of the cell, where "
              "the plant grows again."),
    "runs": ("e045's world, seeds 9-14, 100,000 steps: plant_yield 0.5 against e045's connect runs, which this binary repeats byte for "
             "byte at 1 (checked on seed 9). Seven runs at once, 11-18 minutes. The state is read from the blocks broken per body per step, "
             "which the yield does not enter."),
    "verdicts": ("<li><span class=\"verdict partly\">Partly</span> The world stands on six seeds (lowest floor 125) with 38-58% fewer "
                 "bodies; two seeds lose more than half.</li>"
                 "<li><span class=\"verdict partly\">Partly</span> Five of six seeds settle as a hunter world against four, but three seeds "
                 "swap states; within a state the kills' share of the digested holds (28-36% against 30-37%).</li>"
                 "<li><span class=\"verdict no\">No</span> Muscle-free lineages hold more of the bodies in the hunter worlds, 34-64% against "
                 "24-47%; on three seeds the winner is a gut of 22-25 blocks without muscle.</li>"),
    "h_world": "The world stands at half",
    "p_world": ("Half of every bite goes back to the soil, and the bodies digest 73 a step against 126. The bodies fall by about as "
                "much, 48% on average, and the winter floors by 51-71%, the lowest 125 on seed 9. The plant left uneaten stands: trees "
                "cover 27-31% of the cells against 3-16%."),
    "h_state": "The seed still picks the state; the balance within it holds",
    "p_state": ("Seeds 10 and 13 become hunter worlds and seed 11 a grazer world: one more hunter world in six is what the seed alone "
                "does (e045 swapped two under a law that changed nothing about hunting). In a hunter world a body gets as much from kills "
                "as before, 0.015-0.031 a step against 0.016-0.024, and meets others about as often (0.36-0.56 contacts a step against "
                "0.44-0.69)."),
    "h_sit": "The sitter answers with a bigger gut",
    "p_sit": ("A body takes 2.1-2.6 times the plant it took, with more gut blocks on all six seeds. On seeds 9, 10 and 13 the lineage "
              "with the most of the last third holds 22-25 gut blocks on average, on a 7- to 9-wide grid, without muscle, beside small "
              "hunters of 12-15 blocks."),
    "discussion": ("<p>Why the balance holds. The crowd sets what a bite brings (e038): with half the yield the bodies thin out until a "
                   "gut breaks even again, and a grazer then lives as it did. A kill is worth what it was (flesh is digested whole) and a "
                   "hunter meets others as often, so its income is unchanged too. For the bodies the law acts like a weaker sun: fewer "
                   "of the same kinds. The plant they leave stands as forest.</p>"
                   "<p>Why the gut grows. A body pays 0.032 a step for being one, the upkeep of 16 blocks. When a gut block earns less, "
                   "more of them are needed to carry that cost, and a big gut becomes the cheaper answer to poor food. Real grazers show "
                   "the same (the Jarman-Bell principle); here it comes out of the costs.</p>"
                   "<p>What this does not show: plant_yield 0.3 was not run. At 0.5 the balance within a state did not move, and the "
                   "reason above says a lower yield thins the world again (floors near 100) with bigger guts still. Hunting could pay in "
                   "a world whose places differ, where the crowd cannot even out what a bite brings (#14).</p>"),
    "conclusion": ("Not kept: plant_yield stays 1; the argument stays in the binary for later combinations. Plant matter harder to digest "
                   "halves the world and grows the sitter's gut; it does not move the balance between hunting and grazing within a "
                   "state, and the seed still picks the state. Next: #14, the regions, designed in the issue first, with #38 as its "
                   "first pilot."),
}


if __name__ == "__main__":
    if len(os.sys.argv) > 1 and os.sys.argv[1] == "lineages":
        for law in LAWS:
            for s in SEEDS:
                r, fo = run(law, s), folder(law)
                if not exists(r, fo):
                    continue
                print(f"{LAWS[law][0]}, seed {s}")
                by = lineage_rows(r, fo)
                top = sorted(by, key=lambda lid: -sum(int(x["size"]) for x in by[lid]))[:6]
                for lid in top:
                    rows = by[lid]
                    peak = max(rows, key=lambda x: int(x["size"]))
                    cells = sum(float(peak[k]) for k in KIND_COLS)
                    print(f"  lineage {lid}: {sum(int(x['size']) for x in rows):,} body-samples, {int(rows[0]['step']):,}-{int(rows[-1]['step']):,}, peak {peak['size']} at {int(peak['step']):,}; cells {cells:.0f} mass {float(peak['mass']):.0f} hard {float(peak['hard']):.0f} muscle {float(peak['muscle']):.0f} sensor {float(peak['sensor']):.1f} gut {float(peak['digestive']):.0f} side {float(peak['side']):.0f} len {float(peak['len_fwd']):.1f}x{float(peak['len_side']):.1f} age {float(peak['age']):.0f} meat {float(peak['meat']) / max(float(peak['meat']) + float(peak['plant']), 1e-9):.2f}")
                div, wins = diversity(r, fo)
                print(f"  diversity {div} of {len(wins)} winners: " + "; ".join(f"{i} {sh:.0%} {c:.1f} cells" for i, sh, c, _ in wins))
    elif len(os.sys.argv) > 1 and os.sys.argv[1] == "numbers":
        numbers()
    else:
        main()
