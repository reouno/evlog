#!/usr/bin/env python3
"""Build report.html from results/seed*.csv. Standard library only.

Run from this directory: python3 report.py
"""
import csv
import glob
import html
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
SEEDS = [1, 2, 3]
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4"]  # fixed slot order
SERIES_DARK = ["#3987e5", "#d95926", "#199e70", "#c98500", "#d55181"]
ACTIONS = ["stay", "n", "s", "e", "w"]
ACTION_LABEL = {"stay": "Stay", "n": "North", "s": "South", "e": "East", "w": "West"}

W, H = 640, 260
ML, MR, MT, MB = 56, 16, 16, 36


def load():
    data = {}
    for s in SEEDS:
        with open(os.path.join(HERE, "results", f"seed{s}.csv")) as f:
            rows = list(csv.DictReader(f))
        data[s] = {k: [float(r[k]) for r in rows] for k in rows[0]}
    return data


def nice_ticks(lo, hi, n=4):
    if hi <= lo:
        hi = lo + 1
    raw = (hi - lo) / n
    mag = 10 ** int(f"{raw:e}".split("e")[1])
    for m in (1, 2, 2.5, 5, 10):
        step = m * mag
        if step >= raw:
            break
    start = int(lo / step) * step
    ticks = []
    t = start
    while True:
        if t >= lo - step * 0.001:
            ticks.append(round(t, 10))
        if t >= hi - step * 0.001:
            break
        t += step
    return ticks


def fmt(v):
    if abs(v) >= 1000:
        return f"{v/1000:g}k"
    return f"{v:g}"


def line_chart(cid, title, subtitle, xs, series, ymin=None, ymax=None, unit=""):
    """series: list of (label, ys, slot)."""
    allv = [v for _, ys, _ in series for v in ys]
    lo = min(allv) if ymin is None else ymin
    hi = max(allv) if ymax is None else ymax
    pad = (hi - lo) * 0.08 or 1
    hi += pad
    if ymin is None:
        lo -= pad
        if min(allv) >= 0 and lo < 0:
            lo = 0
    yt = nice_ticks(lo, hi)
    lo, hi = min(lo, yt[0]), max(hi, yt[-1])
    xt = [t for t in nice_ticks(xs[0], xs[-1], 5) if t <= xs[-1]]
    pw, ph = W - ML - MR, H - MT - MB

    def px(x):
        return ML + (x - xs[0]) / (xs[-1] - xs[0]) * pw

    def py(y):
        return MT + ph - (y - lo) / (hi - lo) * ph

    g = [f'<svg class="chart" viewBox="0 0 {W} {H}" data-chart="{cid}" role="img" aria-label="{html.escape(title)}">']
    for t in yt:
        g.append(f'<line class="grid" x1="{ML}" x2="{W-MR}" y1="{py(t):.1f}" y2="{py(t):.1f}"/>')
        g.append(f'<text class="tick" x="{ML-8}" y="{py(t)+4:.1f}" text-anchor="end">{fmt(t)}{unit}</text>')
    g.append(f'<line class="axis" x1="{ML}" x2="{W-MR}" y1="{MT+ph}" y2="{MT+ph}"/>')
    for t in xt:
        g.append(f'<text class="tick" x="{px(t):.1f}" y="{H-12}" text-anchor="middle">{fmt(t)}</text>')
    g.append(f'<text class="tick" x="{W-MR}" y="{H-2}" text-anchor="end">step</text>')
    for label, ys, slot in series:
        pts = " ".join(f"{px(x):.1f},{py(y):.1f}" for x, y in zip(xs, ys))
        g.append(f'<polyline class="s{slot}" points="{pts}"/>')
    # hover layer
    g.append(f'<line class="cross" x1="0" x2="0" y1="{MT}" y2="{MT+ph}" visibility="hidden"/>')
    g.append(f'<rect class="hit" x="{ML}" y="{MT}" width="{pw}" height="{ph}" fill="transparent"/>')
    g.append("</svg>")
    legend = "".join(
        f'<span class="lg"><i class="s{slot}"></i>{html.escape(label)}</span>' for label, _, slot in series
    )
    meta = {"xs": xs, "series": [[lbl, ys] for lbl, ys, _ in series], "ml": ML, "pw": pw}
    return figure(cid, title, subtitle, "\n".join(g), legend, meta)


def stacked_area(cid, title, subtitle, xs, layers):
    """layers: list of (label, ys, slot); ys are fractions summing to ~1."""
    pw, ph = W - ML - MR, H - MT - MB

    def px(x):
        return ML + (x - xs[0]) / (xs[-1] - xs[0]) * pw

    def py(y):
        return MT + ph - y * ph

    g = [f'<svg class="chart" viewBox="0 0 {W} {H}" data-chart="{cid}" role="img" aria-label="{html.escape(title)}">']
    for t in (0, 0.25, 0.5, 0.75, 1.0):
        g.append(f'<line class="grid" x1="{ML}" x2="{W-MR}" y1="{py(t):.1f}" y2="{py(t):.1f}"/>')
        g.append(f'<text class="tick" x="{ML-8}" y="{py(t)+4:.1f}" text-anchor="end">{int(t*100)}%</text>')
    base = [0.0] * len(xs)
    for label, ys, slot in layers:
        top = [b + y for b, y in zip(base, ys)]
        up = " ".join(f"{px(x):.1f},{py(y):.1f}" for x, y in zip(xs, top))
        down = " ".join(f"{px(x):.1f},{py(y):.1f}" for x, y in reversed(list(zip(xs, base))))
        g.append(f'<polygon class="a{slot}" points="{up} {down}"/>')
        base = top
    for t in [t for t in nice_ticks(xs[0], xs[-1], 5) if t <= xs[-1]]:
        g.append(f'<text class="tick" x="{px(t):.1f}" y="{H-12}" text-anchor="middle">{fmt(t)}</text>')
    g.append(f'<text class="tick" x="{W-MR}" y="{H-2}" text-anchor="end">step</text>')
    g.append(f'<line class="cross" x1="0" x2="0" y1="{MT}" y2="{MT+ph}" visibility="hidden"/>')
    g.append(f'<rect class="hit" x="{ML}" y="{MT}" width="{pw}" height="{ph}" fill="transparent"/>')
    g.append("</svg>")
    legend = "".join(
        f'<span class="lg"><i class="s{slot}"></i>{html.escape(label)}</span>' for label, _, slot in layers
    )
    meta = {"xs": xs, "series": [[lbl, ys] for lbl, ys, _ in layers], "ml": ML, "pw": pw, "pct": True}
    return figure(cid, title, subtitle, "\n".join(g), legend, meta)


def figure(cid, title, subtitle, svg, legend, meta):
    import json
    return f"""
<figure class="fig" id="{cid}">
  <figcaption><strong>{html.escape(title)}</strong><span>{html.escape(subtitle)}</span></figcaption>
  <div class="legend">{legend}</div>
  <div class="wrap">{svg}<div class="tip" hidden></div></div>
  <script type="application/json" class="meta">{json.dumps(meta)}</script>
</figure>"""


def table(data):
    cols = ["step", "pop", "mean_energy", "mean_res", "diversity", "drift", "births", "deaths", "steps_per_sec"]
    out = []
    for s in SEEDS:
        d = data[s]
        rows = "".join(
            "<tr>" + "".join(f"<td>{d[c][i]:g}</td>" for c in cols) + "</tr>"
            for i in range(0, len(d["step"]), 10)
        )
        out.append(f"<details><summary>Seed {s} (every 100,000 steps)</summary><div class='tw'><table><thead><tr>"
                   + "".join(f"<th>{c}</th>" for c in cols) + f"</tr></thead><tbody>{rows}</tbody></table></div></details>")
    return "\n".join(out)


def summary(data):
    rows = []
    for s in SEEDS:
        d = data[s]
        pop, div, drift, sps = d["pop"], d["diversity"], d["drift"][1:], d["steps_per_sec"]
        med = sorted(sps)[len(sps) // 2]
        rows.append(
            f"<tr><td>{s}</td><td>{int(min(pop))} / {int(max(pop))} / {int(pop[-1])}</td>"
            f"<td>{min(div):.2f} / {div[-1]:.2f}</td><td>{min(drift):.2f} / {sorted(drift)[len(drift)//2]:.2f} / {max(drift):.2f}</td>"
            f"<td>{med:,.0f}</td></tr>"
        )
    return "".join(rows)


def main():
    data = load()
    xs = data[1]["step"]

    def seeds(key):
        return [(f"Seed {s}", data[s][key], i + 1) for i, s in enumerate(SEEDS)]

    charts = [
        line_chart("pop", "Population", "Number of living agents. Flat means the world is neither dying out nor exploding.", xs, seeds("pop"), ymin=0),
        line_chart("energy", "Average energy per agent", "An agent splits in two at 10. Around 5 means most agents are halfway to splitting.", xs, seeds("mean_energy"), ymin=0),
        line_chart("res", "Average food per cell", "Food regrows up to 1.0. Near 0.05 means the grid is almost always eaten bare.", xs, seeds("mean_res"), ymin=0),
        line_chart("div", "Genetic diversity", "How different agents are from each other (average spread of their genes). Near zero would mean everyone is a clone.", xs, seeds("diversity"), ymin=0),
        line_chart("drift", "Genetic drift", "How much the average genome moved since the last checkpoint (10,000 steps earlier). Zero would mean evolution stopped.", xs, seeds("drift"), ymin=0),
        line_chart("births", "Births per 10,000 steps", "Deaths track births almost exactly, so only births are shown.", xs, seeds("births"), ymin=0),
        line_chart("sps", "Simulation speed", "Steps per second. The three runs shared one machine, so absolute values vary; all are far above what we need.", xs, seeds("steps_per_sec"), ymin=0),
    ]
    actions = []
    for s in SEEDS:
        layers = [(ACTION_LABEL[a], data[s][a], i + 1) for i, a in enumerate(ACTIONS)]
        actions.append(stacked_area(f"act{s}", f"What agents do - seed {s}", "Share of each action per 10,000 steps. 'Stay' vanishes early; agents keep moving.", xs, layers))

    css = f"""
:root {{
  --surface: #fcfcfb; --page: #f9f9f7; --ink: #0b0b0b; --ink2: #52514e; --muted: #898781;
  --grid: #e1e0d9; --axis: #c3c2b7; --border: rgba(11,11,11,0.10);
  --s1: {SERIES[0]}; --s2: {SERIES[1]}; --s3: {SERIES[2]}; --s4: {SERIES[3]}; --s5: {SERIES[4]};
}}
@media (prefers-color-scheme: dark) {{
  :root:not([data-theme="light"]) {{
    --surface: #1a1a19; --page: #0d0d0d; --ink: #ffffff; --ink2: #c3c2b7; --muted: #898781;
    --grid: #2c2c2a; --axis: #383835; --border: rgba(255,255,255,0.10);
    --s1: {SERIES_DARK[0]}; --s2: {SERIES_DARK[1]}; --s3: {SERIES_DARK[2]}; --s4: {SERIES_DARK[3]}; --s5: {SERIES_DARK[4]};
  }}
}}
:root[data-theme="dark"] {{
  --surface: #1a1a19; --page: #0d0d0d; --ink: #ffffff; --ink2: #c3c2b7; --muted: #898781;
  --grid: #2c2c2a; --axis: #383835; --border: rgba(255,255,255,0.10);
  --s1: {SERIES_DARK[0]}; --s2: {SERIES_DARK[1]}; --s3: {SERIES_DARK[2]}; --s4: {SERIES_DARK[3]}; --s5: {SERIES_DARK[4]};
}}
* {{ box-sizing: border-box; }}
body {{ margin: 0; background: var(--page); color: var(--ink); font: 15px/1.55 system-ui, -apple-system, "Segoe UI", sans-serif; }}
main {{ max-width: 960px; margin: 0 auto; padding: 32px 20px 64px; }}
h1 {{ font-size: 26px; margin: 0 0 4px; }}
h2 {{ font-size: 19px; margin: 40px 0 8px; }}
p, li {{ color: var(--ink); max-width: 72ch; }}
.sub {{ color: var(--ink2); margin: 0 0 24px; }}
.grid2 {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(420px, 1fr)); gap: 20px; }}
.fig {{ margin: 0; background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 14px 14px 8px; }}
figcaption strong {{ display: block; font-size: 15px; }}
figcaption span {{ display: block; color: var(--ink2); font-size: 13px; min-height: 2.6em; }}
.legend {{ display: flex; flex-wrap: wrap; gap: 4px 14px; font-size: 12.5px; color: var(--ink2); margin: 6px 0 2px; }}
.lg i {{ display: inline-block; width: 10px; height: 10px; border-radius: 2px; margin-right: 6px; vertical-align: -1px; }}
.wrap {{ position: relative; }}
.chart {{ width: 100%; height: auto; display: block; }}
.grid {{ stroke: var(--grid); stroke-width: 1; }}
.axis {{ stroke: var(--axis); stroke-width: 1; }}
.tick {{ fill: var(--muted); font-size: 11px; font-variant-numeric: tabular-nums; }}
polyline {{ fill: none; stroke-width: 2; stroke-linejoin: round; }}
.cross {{ stroke: var(--ink2); stroke-width: 1; stroke-dasharray: 3 3; pointer-events: none; }}
.s1 {{ stroke: var(--s1); background: var(--s1); }} .s2 {{ stroke: var(--s2); background: var(--s2); }}
.s3 {{ stroke: var(--s3); background: var(--s3); }} .s4 {{ stroke: var(--s4); background: var(--s4); }}
.s5 {{ stroke: var(--s5); background: var(--s5); }}
.a1 {{ fill: var(--s1); }} .a2 {{ fill: var(--s2); }} .a3 {{ fill: var(--s3); }} .a4 {{ fill: var(--s4); }} .a5 {{ fill: var(--s5); }}
polygon {{ stroke: var(--surface); stroke-width: 1; }}
.tip {{ position: absolute; pointer-events: none; background: var(--surface); border: 1px solid var(--border); border-radius: 6px;
  padding: 6px 10px; font-size: 12px; color: var(--ink); box-shadow: 0 2px 8px rgba(0,0,0,0.12); white-space: nowrap; }}
.tip b {{ display: block; color: var(--ink2); font-weight: 500; margin-bottom: 2px; }}
.tip i {{ display: inline-block; width: 8px; height: 8px; border-radius: 2px; margin-right: 6px; }}
table {{ border-collapse: collapse; font-size: 13.5px; font-variant-numeric: tabular-nums; }}
th, td {{ padding: 6px 12px; text-align: right; border-bottom: 1px solid var(--grid); }}
th:first-child, td:first-child {{ text-align: left; }}
th {{ color: var(--ink2); font-weight: 600; }}
.tw {{ overflow-x: auto; }}
details {{ margin: 8px 0; }} summary {{ cursor: pointer; color: var(--ink2); }}
.verdicts {{ list-style: none; padding: 0; margin: 12px 0 0; }} .verdicts li {{ margin: 4px 0; }}
.verdict {{ display: inline-block; padding: 1px 8px; border-radius: 4px; font-size: 12.5px; font-weight: 600; background: rgba(12,163,12,0.12); color: #006300; }}
:root[data-theme="dark"] .verdict {{ color: #0ca30c; }}
@media (prefers-color-scheme: dark) {{ :root:not([data-theme="light"]) .verdict {{ color: #0ca30c; }} }}
dl {{ display: grid; grid-template-columns: max-content 1fr; gap: 4px 16px; max-width: 72ch; }}
dt {{ font-weight: 600; }} dd {{ margin: 0; color: var(--ink2); }}
"""

    js = """
document.querySelectorAll('.fig').forEach(fig => {
  const meta = JSON.parse(fig.querySelector('.meta').textContent);
  const svg = fig.querySelector('svg'), hit = fig.querySelector('.hit'), cross = fig.querySelector('.cross');
  const tip = fig.querySelector('.tip'), wrap = fig.querySelector('.wrap');
  const colors = ['--s1','--s2','--s3','--s4','--s5'];
  const xs = meta.xs;
  hit.addEventListener('mousemove', e => {
    const r = svg.getBoundingClientRect();
    const fx = (e.clientX - r.left) / r.width * svg.viewBox.baseVal.width;
    const t = Math.min(1, Math.max(0, (fx - meta.ml) / meta.pw));
    let i = Math.round(t * (xs.length - 1));
    const px = meta.ml + (xs[i] - xs[0]) / (xs[xs.length-1] - xs[0]) * meta.pw;
    cross.setAttribute('x1', px); cross.setAttribute('x2', px); cross.setAttribute('visibility', 'visible');
    const cs = getComputedStyle(document.documentElement);
    tip.innerHTML = '<b>step ' + xs[i].toLocaleString() + '</b>' + meta.series.map((s, k) => {
      const v = s[1][i];
      const txt = meta.pct ? (v*100).toFixed(1) + '%' : (Number.isInteger(v) ? v.toLocaleString() : v.toFixed(3));
      return '<div><i style="background:' + cs.getPropertyValue(colors[k]) + '"></i>' + s[0] + ': ' + txt + '</div>';
    }).join('');
    tip.hidden = false;
    const wr = wrap.getBoundingClientRect();
    let left = e.clientX - wr.left + 14, top = e.clientY - wr.top - 10;
    if (left + tip.offsetWidth > wr.width) left = e.clientX - wr.left - tip.offsetWidth - 14;
    tip.style.left = left + 'px'; tip.style.top = top + 'px';
  });
  hit.addEventListener('mouseleave', () => { tip.hidden = true; cross.setAttribute('visibility', 'hidden'); });
});
"""

    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>e001 Minimal World - Report</title>
<style>{css}</style>
</head>
<body>
<main>
<h1>e001: Does the simplest evolving world keep going?</h1>
<p class="sub">Experiment report - 2026-08-29 - three runs of 1,000,000 steps each</p>

<h2>What we built</h2>
<p>A tiny world on a 64 x 64 grid that wraps around at the edges. Every cell grows food slowly, up to a limit.
Small creatures ("agents") live on the grid. Each step, an agent eats some of the food where it stands, pays a small
cost for being alive (and a little more if it moves), and then decides to stay or move one cell north, south, east, or west.</p>
<p>Agents have no brain to speak of: a short list of 35 numbers (the "genome") decides how they react to the food around them and to their own hunger.
When an agent has eaten enough, it splits in two. The child gets a slightly randomized copy of the parent's numbers. When an agent runs out of energy, it dies.
Nobody tells the agents what to do. Whatever works, spreads.</p>

<h2>What we wanted to know</h2>
<ol>
  <li>Does the population survive a long run (1,000,000 steps) without dying out or growing without limit?</li>
  <li>Does evolution keep going, or does everyone end up identical and stuck?</li>
  <li>How fast is it? Is a long run cheap enough to be practical?</li>
</ol>
<p>We ran the world three times with different random starting points ("seed 1, 2, 3") and took a snapshot every 10,000 steps.</p>

<h2>Summary</h2>
<div class="tw"><table>
<thead><tr><th>Seed</th><th>Population min / max / final</th><th>Diversity min / final</th><th>Drift min / median / max</th><th>Steps per second</th></tr></thead>
<tbody>{summary(data)}</tbody></table></div>
<ol class="verdicts">
<li><span class="verdict">Yes</span> The population survived in all three runs and stayed between about 500 and 540.</li>
<li><span class="verdict">Yes</span> Evolution never stopped: the average genome kept moving and diversity never collapsed.</li>
<li><span class="verdict">Yes</span> About 100,000 simulation steps per second with ~500 agents. A million steps takes seconds.</li>
</ol>

<h2>Charts</h2>
<div class="grid2">
{"".join(charts[:2])}
</div>
<p>Population settles quickly at around 510 in every run. That number is set by how fast food regrows: the grid can only feed so many. Average energy hovers around 5, halfway to the splitting threshold of 10.</p>
<div class="grid2">
{"".join(charts[2:4])}
</div>
<p>Food stays near 0.05 out of a possible 1.0: the agents eat everything almost as soon as it grows. Diversity stays well above zero in all runs, so the agents never become clones of each other.</p>
<div class="grid2">
{"".join(charts[4:6])}
</div>
<p>Drift is large in the first checkpoint (the random starting genomes are quickly replaced), then stays clearly above zero for the whole run. Evolution slows down, but never stops. Births (and deaths, which match them) start at 10,000-19,000 per 10,000 steps and later fall to 3,000-7,000:
agents live three to six times longer than at the start. In each run the drop happens when the population changes from "everyone walks the same way" to a mix of directions (see the next charts).</p>
<div class="grid2">
{"".join(actions)}
{charts[6]}
</div>
<p>This is the most telling chart. Within about 100,000 steps, "stay" disappears in every run. The winning strategy is to keep walking and eat whatever has regrown.
In seed 1 almost everyone walks west. In seeds 2 and 3, several groups walking in different directions end up sharing the world.</p>

<h2>What it means</h2>
<p>The simplest possible version of this world works: it does not die, it does not blow up, and it keeps evolving, at almost no computing cost.
This loop is a solid foundation and we will keep it.</p>
<p>But there is a catch. Once the agents discover "keep walking", nothing new happens. The genes keep drifting, but the world looks the same.
The reason is simple: agents only interact with food, never with each other, so there is nothing to push the world into new shapes.
The next experiment should add interaction between agents (competition, predators, or similar) or an environment that changes on its own,
and check whether that produces change we can actually see.</p>

<h2>Glossary</h2>
<dl>
<dt>Step</dt><dd>One tick of the world clock. Every agent acts once per step.</dd>
<dt>Seed</dt><dd>The random starting point of a run. Different seeds give different starting agents.</dd>
<dt>Population</dt><dd>Number of agents alive at the checkpoint.</dd>
<dt>Energy</dt><dd>An agent's fuel. Eating adds to it, living and moving spend it. At 10 the agent splits; at 0 it dies.</dd>
<dt>Food per cell</dt><dd>How much food is on an average cell, from 0 (bare) to 1 (full).</dd>
<dt>Diversity</dt><dd>How spread out the agents' genomes are. 0 would mean all agents are identical.</dd>
<dt>Drift</dt><dd>How far the average genome moved since the previous checkpoint. 0 would mean evolution has stopped.</dd>
</dl>

<h2>Data</h2>
<p>Every 100,000th checkpoint is shown; the full data is in <code>results/seed*.csv</code>.</p>
{table(data)}
</main>
<script>{js}</script>
</body>
</html>
"""
    out = os.path.join(HERE, "report.html")
    with open(out, "w") as f:
        f.write(page)
    print(f"wrote {out} ({os.path.getsize(out)//1024} KB)")


if __name__ == "__main__":
    main()
