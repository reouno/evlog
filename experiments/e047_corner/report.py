#!/usr/bin/env python3
"""Build report.html for this experiment.

Charts: matplotlib, exported as SVG and inlined. Diagram: hand-written SVG.
Run from the repo root: uv run python experiments/e047_corner/report.py
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

BASE = "128_sigma0_r64_f0_flat_eyes8_flesh1_w1_season2_digest0_sidegrow_store5_yolk0_breed0_winterhigh_water0.1_leach0.01_depth0.01_mix0.2_strict_sat_hold_wear3000"


def run(law, seed):
    """law 0: e045's connect run (the control, in e045's folder); 1: corners hold (connect 2)."""
    return f"{BASE}{'_corner' if law else '_connect'}_seed{seed}"


def folder(law):
    return HERE if law else E045


LAWS = {0: ("sides (e045)", 5), 1: ("corners hold", 0)}  # name, color slot
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


def lived_births(d, i):
    """The births of log row i that were born with a block (the log's births count the children born without one)."""
    return max(d["births"][i] - d["deaths_body"][i], 1.0)


def cut_at_birth(d, i):
    """(the share of the births with a block that were cut down, the blocks not built per such birth) in log row i."""
    n = lived_births(d, i)
    return d["born_cut"][i] * d["births"][i] / n, d["not_built"][i] * d["births"][i] / n


def eaten(d, i):
    """(plant, flesh of kills, dead scavenged) eaten per step in log row i."""
    hunted = d["kill_gain"][i] * d["cells_broken"][i] / LOG
    return d["plant_intake"][i] / LOG, hunted, d["meat_intake"][i] / LOG - hunted


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
    plant, hunted, scav = (sum(x[j] for x in food) / len(food) for j in range(3))
    births = sum(lived_births(d, i) for i in idx)
    born_cut = sum(cut_at_birth(d, i)[0] * lived_births(d, i) for i in idx) / births
    not_built = sum(cut_at_birth(d, i)[1] * lived_births(d, i) for i in idx) / births
    bodies = half_mean(f, "pop")
    broken = half_mean(d, "cells_broken") / LOG
    div, wins = diversity(r, fo)
    w = floors(f)
    return dict(bodies=bodies, floors=[x["pop"] for x in w], floor=min(x["pop"] for x in w),
                births=half_mean(d, "births") / LOG, age=half_mean(f, "age_mean"), lineages=half_mean(f, "lineages"),
                broken=broken, per_body=broken / bodies, hunter=broken / bodies >= STATE_LINE,
                plant=plant, hunted=hunted, scav=scav, share=hunted / (plant + hunted + scav),
                born_cut=born_cut, not_built=not_built, size=half_mean(d, "size_p50"),
                cornered=half_mean(d, "cornered") if "cornered" in d else None,
                cut_break=half_mean(d, "cut_break"), cut_wear=half_mean(d, "cut_wear"),
                free=muscle_free(r, fo), muscle=half_mean(d, "muscle_mean"), gut=half_mean(d, "digestive_mean"),
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


def modal_body(law, seed, lid):
    """The most common grown body of a lineage at its peak: (side, cells, peak row)."""
    r, fo = run(law, seed), folder(law)
    by, bodies = lineage_rows(r, fo), load_bodies(r, fo)
    frames = list(read_frames(f"results/{r}_long.jsonl", fo))
    rows = by[lid]
    peak = max(rows, key=lambda x: int(x["size"]))
    frame = min((fr for fr in frames if any(a[4] == lid for a in fr["agents"])), key=lambda fr: abs(fr["step"] - int(peak["step"])))
    grown = 0.75 * sum(float(peak[k]) for k in KIND_COLS)
    ids = [a[2] for a in frame["agents"] if a[4] == lid]
    c = Counter(i for i in ids if sum(ch != "0" for ch in bodies[i][1]) >= grown) or Counter(ids)
    side, cells = bodies[c.most_common(1)[0][0]]
    return side, cells, peak, rows


def joints(side, cells):
    """(parts through the sides, parts through the sides or corners) of a body's cells string."""
    filled = {k for k, ch in enumerate(cells) if ch != "0"}

    def parts(nbrs):
        seen, n = set(), 0
        for k in filled:
            if k in seen:
                continue
            n += 1
            stack = [k]
            seen.add(k)
            while stack:
                p = stack.pop()
                r, c = divmod(p, side)
                for dr, dc in nbrs:
                    rr, cc = r + dr, c + dc
                    q = rr * side + cc
                    if 0 <= rr < side and 0 <= cc < side and q in filled and q not in seen:
                        seen.add(q)
                        stack.append(q)
        return n

    sides = [(0, 1), (1, 0), (0, -1), (-1, 0)]
    return parts(sides), parts(sides + [(1, 1), (1, -1), (-1, 1), (-1, -1)])


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


def seed_chart(title, subtitle, st, key, percent=False, ymax=None, hline=None, fmt=None, laws=(0, 1)):
    """One dot per seed and law: st[law][seed][key]; `hline` draws a dotted reference line."""
    fig, ax = new_axes("seed")
    for law in laws:
        dx = {0: -0.08, 1: 0.08}[law] if len(laws) > 1 else 0.0
        xs = [s + dx for s in SEEDS if st[law][s] and st[law][s][key] is not None]
        ys = [st[law][s][key] for s in SEEDS if st[law][s] and st[law][s][key] is not None]
        ax.plot(xs, ys, color=SERIES[LAWS[law][1]], linestyle="none", marker="o", markersize=7, label=LAWS[law][0])
    if hline is not None:
        ax.axhline(hline, color=INK, linewidth=1, linestyle=":")
    top = max((st[law][s][key] for law in laws for s in SEEDS if st[law][s] and st[law][s][key] is not None), default=1.0)
    ax.set_ylim(0, ymax if ymax is not None else max(top, 1e-9) * 1.15)
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
    for label, law, seed, lid, name, what in picks:
        side, cells, peak, rows = modal_body(law, seed, lid)
        span = int(rows[-1]["step"]) - int(rows[0]["step"]) + CONFIRM_STEPS
        u = 88 / side
        rects = "".join(f'<rect x="{(i % side) * u:.2f}" y="{(i // side) * u:.2f}" width="{u * 0.9:.2f}" height="{u * 0.9:.2f}" fill="{KIND_COLOR[int(k)]}"/>' for i, k in enumerate(cells) if k != "0")
        m, pl = float(peak["meat"]), float(peak["plant"])
        meat = m / (m + pl) if m + pl > 0 else 0
        p4, p8 = joints(side, cells)
        joint = "" if p4 == p8 else f"; joined through a corner ({p4} parts by the sides)"
        cards.append(f"""<figure class="card"><svg viewBox="-1 -1 89 89" width="120" height="120" role="img" aria-label="{html.escape(name)}"><rect x="-1" y="-1" width="89" height="89" fill="var(--cell)"/>{rects}<line x1="-1" y1="-0.5" x2="88" y2="-0.5" stroke="var(--ink2)" stroke-width="1.5" stroke-dasharray="3 2"/></svg>
<figcaption><strong>{html.escape(name)}</strong><br>{html.escape(label)}, lineage {lid}: {span:,} steps, {int(peak["size"]):,} agents at its peak<br>side {float(peak["side"]):.0f} (grid {side}x{side}){joint}; mass {float(peak["mass"]):.0f}: hard {float(peak["hard"]):.0f}, muscle {float(peak["muscle"]):.0f}, sensor {float(peak["sensor"]):.1f}, digestive {float(peak["digestive"]):.0f}; flesh {meat:.0%} of the intake; mean age {float(peak["age"]):.0f}<br>{html.escape(what)}</figcaption></figure>""")
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


def cells_svg(cells, x0, y0, u=24, size=22, **attrs):
    extra = " ".join(f'{k.replace("_", "-")}="{v}"' for k, v in attrs.items())
    return "".join(f'<rect x="{x0 + c * u}" y="{y0 + r * u}" width="{size}" height="{size}" rx="2" {extra}/>' for c, r in cells)


# Hand-written mechanism diagram: one genome's blocks under the two joining rules. The accent
# (var(--s1)) marks what is built; dashed outlines what is not.
_BODY = [(0, 0), (1, 0), (2, 0), (1, 1), (1, 2)]  # a T joined through its sides
_TAIL = [(2, 3), (3, 4)]  # a diagonal tail: each block touches the one before only at a corner
DIAGRAM = f"""
<figure class="fig diagram">
<svg viewBox="0 0 900 230" width="100%" role="img" aria-label="The same written body under the two rules: joined through the sides only, the diagonal tail is not built; with corners holding, the whole body is built" font-size="12" fill="currentColor" stroke="currentColor">
  <g stroke="none" fill="var(--s1)">
    {cells_svg(_BODY, 60, 40)}
    {cells_svg(_BODY + _TAIL, 520, 40)}
  </g>
  <g fill="none" stroke-width="1.2" stroke-dasharray="3 2">
    {cells_svg(_TAIL, 60, 40)}
  </g>
  <line x1="450" y1="20" x2="450" y2="210" stroke-opacity="0.3"/>
  <g stroke="none">
    <text x="60" y="28" font-weight="600">connect 1: through the sides only</text>
    <text x="178" y="126">not built:</text>
    <text x="178" y="142">touches only at a corner</text>
    <text x="60" y="190" font-weight="600">e045's law</text>
    <text x="60" y="208" font-size="11">a block joined to the rest only at a corner is cut, at birth or after a break</text>
    <text x="520" y="28" font-weight="600">connect 2: corners hold</text>
    <text x="640" y="126">built: a diagonal tail</text>
    <text x="520" y="190" font-weight="600">this experiment</text>
    <text x="520" y="208" font-size="11">blocks that touch at a corner join; the largest part so joined is the body</text>
  </g>
</svg>
<figcaption>Figure 1. One written body under the two rules. Through the sides only, a block that touches the rest at a corner is not built (dashed); with corners holding, it is.</figcaption>
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
            corner = "-" if x["cornered"] is None else f"{x['cornered']:.2%}"
            print(f"seed {s} {LAWS[law][0]:14s} {'HUNTER' if x['hunter'] else 'grazer'} broken/body {x['per_body']:.4f} kills {x['share']:.1%} "
                  f"| births cut {x['born_cut']:.2%} not built/birth {x['not_built']:.3f} cornered {corner} cut_break {x['cut_break']:.2f} cut_wear {x['cut_wear']:.3f}")
            print(f"      bodies {x['bodies']:.0f} floors {x['floors']} births {x['births']:.2f} age {x['age']:.0f} lineages {x['lineages']:.1f} "
                  f"| muscle-free {x['free']:.0%} muscle {x['muscle']:.2f} gut {x['gut']:.2f} size p50 {x['size']:.1f} "
                  f"| top {i} {share:.0%} {cells:.1f} cells {muscle:.1f} muscle {gut:.1f} gut {meat:.0%} flesh {fwd:.1f}x{side:.1f} | diversity {x['div']} of {x['wins']}")
    for law in LAWS:
        xs = [st[law][s] for s in SEEDS if st[law][s]]
        print(f"{LAWS[law][0]}: hunter worlds {sum(x['hunter'] for x in xs)} of {len(xs)}; bodies {sum(x['bodies'] for x in xs) / max(len(xs), 1):.0f}")


def main():
    st = all_stats()
    logs = {s: load_csv(f"results/{run(1, s)}_log.csv") for s in SEEDS if st[1][s]}

    charts_cut = [
        seed_chart("Births cut down, by seed", "Share of the births with a block that were cut to their largest part, second half.",
                   st, "born_cut", percent=True),
        seed_chart("Bodies joined through a corner, by seed", "Share of the living bodies that hold together only through a corner somewhere, second half (0 under the sides rule).",
                   st, "cornered", percent=True, laws=(1,)),
    ]
    charts_world = [
        seed_chart("Bodies, by seed", "Bodies alive over the second half (steps 50,000-100,000).", st, "bodies"),
        seed_chart("The flesh of kills in what the bodies eat, by seed", "Second half. Two levels, one per state: the seed picks the level.",
                   st, "share", percent=True, ymax=0.5),
    ]

    def top_text(t):
        _i, share, cells, muscle, gut, meat, _f, _s = t
        return f"{share:.0%}: {cells:.0f} cells, {muscle:.0f} muscle, {gut:.0f} gut, {meat:.0%} flesh"

    def pair(s, key, f):
        a, b = st[0][s], st[1][s]
        return f"<td>{f(a[key])} / {f(b[key])}</td>"

    state = lambda h: "hunter" if h else "grazer"
    seed_rows = "".join(
        f"<tr><td>{s}</td>{pair(s, 'born_cut', lambda v: f'{v:.1%}')}<td>{st[1][s]['cornered']:.1%}</td>{pair(s, 'hunter', state)}{pair(s, 'share', lambda v: f'{v:.0%}')}"
        f"{pair(s, 'bodies', lambda v: f'{v:,.0f}')}{pair(s, 'floor', lambda v: f'{v:,}')}{pair(s, 'div', lambda v: f'{v}')}"
        f"<td>{top_text(st[0][s]['top'])}</td><td>{top_text(st[1][s]['top'])}</td></tr>"
        for s in SEEDS if st[0][s] and st[1][s])
    tables = data_table(["step", "pop", "births", "deaths_energy", "deaths_broken", "deaths_wear", "cells_broken", "kill_gain", "plant_intake", "meat_intake",
                         "split", "outside", "born_cut", "not_built", "cut_break", "cut_wear", "cut_bodies", "cornered", "size_p50", "len_fwd", "len_side"],
                        {f"{LAWS[1][0]}, seed {s}": d for s, d in logs.items()})
    TEXT.update(TEXTS)
    TEXT["gallery"] = gallery(GALLERY, GALLERY_CAPTION) if GALLERY else ""
    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>e047 Corners hold - Report</title>
<style>{CSS}</style>
</head>
<body>
<main>
<h1>e047: Corners hold</h1>
<p class="sub">Experiment report - 2026-09-11 - blocks that touch at a corner join a body too (#50), against e045's connect runs on seeds 9-14. Answer: {TEXT["sub_answer"]}</p>

<section class="tldr">
<h2>TL;DR</h2>
<p>{TEXT["tldr"]}</p>
</section>

<h2>1. Question</h2>
<p>{TEXT["question"]}</p>
<ol>
  <li><strong>The cut at birth nearly vanishes:</strong> under 1% of the births are cut on at least five seeds.</li>
  <li><strong>Shapes hardly change:</strong> under 5% of the living bodies are joined through a corner, and the winners still fill their grids.</li>
  <li><strong>The world stands:</strong> bodies and winter floors within 15% of the control's; the hunter world on 3-5 of 6 seeds.</li>
</ol>

<h2>2. The law</h2>
<p>{TEXT["world"]}</p>
{DIAGRAM}
<p><strong>Runs.</strong> {TEXT["runs"]}</p>
<ul class="measures">
  <li><strong>births cut</strong> - the share of the births (with a block) cut to their largest part.</li>
  <li><strong>cornered</strong> - the share of the living bodies that hold together only through a corner somewhere.</li>
  <li><strong>state</strong> - the flesh of kills in what the bodies eat; blocks broken per body per step over 0.03 is a hunter world.</li>
  <li><strong>bodies, floors</strong> - bodies alive every 1,000 steps, the lowest of the five winter troughs.</li>
  <li><strong>top lineage, diversity</strong> - the lineage with the most of the last third, and the diversity number (#42).</li>
</ul>

<h2>3. Results</h2>
<p>Means over the second half (steps 50,000-100,000); each pair is sides (e045) / corners hold.</p>
<div class="tw"><table>
<thead><tr><th>seed</th><th>births cut</th><th>cornered</th><th>state</th><th>kills' share</th><th>bodies</th><th>lowest floor</th><th>diversity</th><th>top lineage of the last third, sides</th><th>corners hold</th></tr></thead>
<tbody>{seed_rows}</tbody></table></div>
<ol class="verdicts">
{TEXT["verdicts"]}
</ol>

<h3>3.1 {TEXT["h_cut"]}</h3>
<div class="grid2">
{"".join(charts_cut)}
</div>
<p>{TEXT["p_cut"]}</p>
{TEXT["gallery"]}

<h3>3.2 {TEXT["h_world"]}</h3>
<div class="grid2">
{"".join(charts_world)}
</div>
<p>{TEXT["p_world"]}</p>

<h2>4. Discussion</h2>
{TEXT["discussion"]}

<h2>5. Conclusion and next step</h2>
<p>{TEXT["conclusion"]}</p>

<h2>Appendix: data</h2>
<p>Every log step (10,000 steps) of the six runs under the law; the control's are in e045's report. The full data are in <code>results/*.csv</code>. Build this report with <code>uv run python experiments/e047_corner/report.py</code>.</p>
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
    ("corners hold, seed 11", 1, 11, 169, "the ram", "A wall of hard across the front, two rows of muscle behind it, then a row of gut: it pushes through what it meets, and wins seed 11's hunter world."),
    ("corners hold, seed 14", 1, 14, 125, "the hook", "Hard curling around the front corner over a few gut blocks, muscle behind: the leading lineage of seed 14 from step 18,000 to 77,000."),
    ("corners hold, seed 13", 1, 13, 482, "the muscle block", "Muscle two rows deep over a row of gut, in one corner of its grid: it led seed 13 from step 38,000 to 53,000."),
    ("corners hold, seed 9", 1, 9, 63, "the band with a tail", "Gut two rows deep across the grid with a short tail at one end: the leading body of seed 9's last third."),
    ("corners hold, seed 12", 1, 12, 36, "the band with stubs", "Gut two rows deep with short stubs below it, joined through its sides like every leading body."),
    ("corners hold, seed 13", 1, 13, 1, "the corner gut", "A block of gut in one corner of an 8x8 grid, alive from the first count to the end of the run."),
]
GALLERY_CAPTION = ("The usual grown body of six leading lineages under the law, front up (orange muscle, aqua gut, yellow sensor, blue hard). "
                   "None of them joins through a corner: the shapes are as compact as without the law.")

TEXTS = {
    "sub_answer": ("the world stands and the hunter world comes on the same 4 of 6 seeds, but no leading body uses a corner: 2-7% of the "
                   "living bodies hold through one, and the winners stay compact. Kept as the physics; it does not make shapes."),
    "tldr": ("Blocks that touch at a corner now join a body. The world stands on six seeds and the hunter world comes on the same four. "
             "2-7% of the living bodies hold together through a corner somewhere, but none of the 30 leading lineages' bodies does, and "
             "the winners stay compact. The joining rule did not make the rectangles; what pays did. Kept. Next: #51, moving takes a motor."),
    "question": ("Since e045 a body is the largest part its blocks make through their sides, and the bodies are all squares and "
                 "rectangles (the user). Letting a corner hold (#50) asks whether the joining rule shaped them. The rectangles came "
                 "before e045, which cut only 0.6-4.4% of the births on five seeds."),
    "world": ("Under connect 2, blocks that touch at a corner join too. At birth only the largest part so joined is built; after a "
              "break or a worn block the body keeps its largest part so joined, and the rest falls as dead matter."),
    "runs": ("e045's world, seeds 9-14, 100,000 steps under connect 2, against e045's connect runs, which connect 1 repeats byte for "
             "byte (checked on seed 9). Seven runs at once, 16 minutes. Six seeds, because the seed picks the world's state."),
    "verdicts": ("<li><span class=\"verdict no\">No</span> The cut at birth stays: 0.6-10.4% of the births on five seeds, 41% on seed "
                 "11, set by the winner's genome, not the rule.</li>"
                 "<li><span class=\"verdict partly\">Partly</span> 2-7% of the living bodies hold through a corner (over 5% on three "
                 "seeds), but none of the 30 leading lineages' bodies does; the winners stay compact.</li>"
                 "<li><span class=\"verdict partly\">Partly</span> The world stands on six seeds (lowest floor 420) and the hunter world "
                 "comes on the same four, but bodies change by -23% to +40%.</li>"),
    "h_cut": "Corners are allowed and rarely used",
    "p_cut": ("The usual body of every leading lineage is joined through its sides: allowing corners brought no diagonal limbs. The "
              "2-7% joined through a corner are rarer bodies, or bodies that lost a block and stayed in one piece. The cut at birth "
              "moves with the winning genome: seed 11's winner writes blocks apart, as seed 11's did without the law (12%)."),
    "h_world": "The world stands; the path changes, the states do not",
    "p_world": ("The hunter world comes on the same four seeds (9, 11, 12, 14), though seeds 9 and 13 sit near the line between the "
                "states (kills 30-31% of the intake). Bodies change by -23% to +40% (2,420 against 2,246 on average) with the winner: "
                "seed 14's is a gut of 11 blocks, and 3,069 bodies live there."),
    "discussion": ("<p>The joining rule never shaped the bodies. Under either rule the winners are compact: a block of gut, a band two "
                   "rows deep, or a wall of hard over rows of muscle. Every block's work pays best packed: a gut eats the cell under it, "
                   "muscle pushes by the line behind a face, hard is harder when contiguous, and a body pays 0.032 a step for being one. "
                   "A limb joined at a corner would be a block that pays for nothing.</p>"
                   "<p>What changed is the path. Every seed has a new winner, as any change to the world gives, and the number of "
                   "bodies follows the winner's size. The states did not move.</p>"
                   "<p>What this does not show: whether corners matter once a block pays for reaching out (#52), or once a step needs a "
                   "motor (#51).</p>"),
    "conclusion": ("Kept: blocks that touch at a corner join from here (connect 2), the physics the user asked for; it changes nothing "
                   "measured. Shapes need a block whose work depends on where it sits (#52). Next: #51, moving takes a motor: a body "
                   "without muscle does not step, so that sitting and moving become two different bodies."),
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
                top = sorted(by, key=lambda lid: -sum(int(x["size"]) for x in by[lid]))[:5]
                for lid in top:
                    rows = by[lid]
                    peak = max(rows, key=lambda x: int(x["size"]))
                    side, cells, _, _ = modal_body(law, s, lid)
                    p4, p8 = joints(side, cells)
                    print(f"  lineage {lid}: {sum(int(x['size']) for x in rows):,} body-samples, {int(rows[0]['step']):,}-{int(rows[-1]['step']):,}, peak {peak['size']} at {int(peak['step']):,}; "
                          f"muscle {float(peak['muscle']):.0f} gut {float(peak['digestive']):.0f} hard {float(peak['hard']):.0f}; modal body side {side} parts {p4}/{p8} cells {cells}")
                div, wins = diversity(r, fo)
                print(f"  diversity {div} of {len(wins)} winners: " + "; ".join(f"{i} {sh:.0%} {c:.1f} cells" for i, sh, c, _ in wins))
    elif len(os.sys.argv) > 1 and os.sys.argv[1] == "numbers":
        numbers()
    else:
        main()
