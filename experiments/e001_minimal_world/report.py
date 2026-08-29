#!/usr/bin/env python3
"""Build report.html from results/seed*.csv.

Charts: matplotlib, exported as SVG and inlined. Diagram: hand-written SVG.
Run from the repo root: uv run python experiments/e001_minimal_world/report.py
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
SEEDS = [1, 2, 3]
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4"]  # fixed slot order
ACTIONS = ["stay", "n", "s", "e", "w"]
ACTION_LABEL = {"stay": "Stay", "n": "North", "s": "South", "e": "East", "w": "West"}

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


def load():
    data = {}
    for s in SEEDS:
        with open(os.path.join(HERE, "results", f"seed{s}.csv")) as f:
            rows = list(csv.DictReader(f))
        data[s] = {k: [float(r[k]) for r in rows] for k in rows[0]}
    return data


def kfmt(x, _pos):
    return f"{x/1000:g}k" if abs(x) >= 1000 else f"{x:g}"


def to_svg(fig):
    buf = io.StringIO()
    fig.savefig(buf, format="svg", bbox_inches="tight", pad_inches=0.05)
    plt.close(fig)
    return buf.getvalue()


def new_axes():
    fig, ax = plt.subplots(figsize=(6.4, 2.6))
    ax.xaxis.set_major_formatter(kfmt)
    ax.set_xlabel("step", loc="right")
    ax.margins(x=0)
    return fig, ax


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
        return [(f"Seed {s}", data[s][key], i) for i, s in enumerate(SEEDS)]

    charts = [
        line_chart("Population", "Number of living agents. Flat means the world is neither dying out nor exploding.", xs, seeds("pop"), ymin=0),
        line_chart("Average energy per agent", "An agent splits in two at 10. Around 5 means most agents are halfway to splitting.", xs, seeds("mean_energy"), ymin=0),
        line_chart("Average food per cell", "Food regrows up to 1.0. Near 0.05 means the grid is almost always eaten bare.", xs, seeds("mean_res"), ymin=0),
        line_chart("Genetic diversity", "How different agents are from each other (average spread of their genes). Near zero would mean everyone is a clone.", xs, seeds("diversity"), ymin=0),
        line_chart("Genetic drift", "How much the average genome moved since the last checkpoint (10,000 steps earlier). Zero would mean evolution stopped.", xs, seeds("drift"), ymin=0),
        line_chart("Births per 10,000 steps", "Deaths track births almost exactly, so only births are shown.", xs, seeds("births"), ymin=0),
        line_chart("Simulation speed", "Steps per second. The three runs shared one machine, so absolute values vary; all are far above what we need.", xs, seeds("steps_per_sec"), ymin=0),
    ]
    actions = []
    for s in SEEDS:
        layers = [(ACTION_LABEL[a], data[s][a], i) for i, a in enumerate(ACTIONS)]
        actions.append(stacked_area(f"What agents do - seed {s}", "Share of each action per 10,000 steps. 'Stay' vanishes early; agents keep moving.", xs, layers))

    css = f"""
:root {{
  --surface: #fcfcfb; --page: #f9f9f7; --ink: #0b0b0b; --ink2: #52514e; --grid: #e1e0d9; --border: rgba(11,11,11,0.10);
  --s1: {SERIES[0]};
}}
@media (prefers-color-scheme: dark) {{
  :root:not([data-theme="light"]) {{
    --surface: #1a1a19; --page: #0d0d0d; --ink: #ffffff; --ink2: #c3c2b7; --grid: #2c2c2a; --border: rgba(255,255,255,0.10);
    --s1: #3987e5;
  }}
}}
:root[data-theme="dark"] {{
  --surface: #1a1a19; --page: #0d0d0d; --ink: #ffffff; --ink2: #c3c2b7; --grid: #2c2c2a; --border: rgba(255,255,255,0.10);
  --s1: #3987e5;
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
.fig {{ margin: 0; background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 14px 14px 8px; }}
.fig svg {{ width: 100%; height: auto; display: block; font-family: system-ui, -apple-system, "Segoe UI", sans-serif; }}
figcaption strong {{ display: block; font-size: 15px; }}
figcaption span {{ display: block; color: var(--ink2); font-size: 13px; min-height: 2.6em; margin-bottom: 6px; }}
.diagram {{ margin: 12px 0; background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 12px 16px 8px; color: var(--ink); }}
.diagram figcaption {{ color: var(--ink2); font-size: 13px; margin-top: 4px; }}
.measures {{ columns: 2; column-gap: 24px; max-width: none; padding-left: 20px; }} .measures li {{ break-inside: avoid; }}
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
"""

    diagram = """
<figure class="diagram">
<svg viewBox="0 0 720 302" role="img" aria-label="One step for one agent: it eats from its cell, sees nearby food, its genome picks a move, and its energy decides whether it splits or dies." style="max-width:100%;height:auto;display:block">
<defs><marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="currentColor"/></marker></defs>
<g fill="none" stroke="currentColor" stroke-width="1.2" font-size="12" font-family="system-ui, sans-serif">
  <!-- cell -->
  <rect x="20" y="100" width="150" height="58" rx="6"/>
  <text x="95" y="122" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">Cell: food</text>
  <text x="95" y="140" text-anchor="middle" fill="currentColor" stroke="none" opacity="0.75">0 to 1.0</text>
  <path d="M60,100 C60,70 130,70 130,100" marker-end="url(#arr)"/>
  <text x="95" y="72" text-anchor="middle" fill="currentColor" stroke="none" opacity="0.75">regrows +0.01 / step</text>
  <!-- agent -->
  <rect x="290" y="100" width="150" height="58" rx="6" stroke="var(--s1)" stroke-width="2"/>
  <text x="365" y="122" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">Agent: energy</text>
  <text x="365" y="140" text-anchor="middle" fill="currentColor" stroke="none" opacity="0.75">pays 0.05 / step</text>
  <!-- eat -->
  <line x1="170" y1="129" x2="288" y2="129" marker-end="url(#arr)"/>
  <text x="229" y="122" text-anchor="middle" fill="currentColor" stroke="none">eats up to 0.2</text>
  <!-- split / die -->
  <rect x="540" y="30" width="160" height="58" rx="6"/>
  <text x="620" y="52" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">Splits in two</text>
  <text x="620" y="70" text-anchor="middle" fill="currentColor" stroke="none" opacity="0.75">child = copy + small noise</text>
  <line x1="440" y1="112" x2="538" y2="66" marker-end="url(#arr)"/>
  <text x="480" y="78" text-anchor="middle" fill="currentColor" stroke="none">energy &#8805; 10</text>
  <rect x="540" y="110" width="160" height="38" rx="6"/>
  <text x="620" y="134" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">Dies</text>
  <line x1="440" y1="129" x2="538" y2="129" marker-end="url(#arr)"/>
  <text x="489" y="122" text-anchor="middle" fill="currentColor" stroke="none">energy &#8804; 0</text>
  <!-- genome / action -->
  <rect x="290" y="215" width="150" height="50" rx="6"/>
  <text x="365" y="236" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">Genome</text>
  <text x="365" y="253" text-anchor="middle" fill="currentColor" stroke="none" opacity="0.75">35 numbers, inherited</text>
  <line x1="365" y1="158" x2="365" y2="213" marker-end="url(#arr)"/>
  <text x="375" y="190" fill="currentColor" stroke="none">sees food here + 4 neighbors,</text>
  <text x="375" y="204" fill="currentColor" stroke="none">and own energy</text>
  <!-- plus-shaped "what it sees" icon -->
  <g transform="translate(300,170)">
    <rect x="14" y="0" width="13" height="13"/><rect x="0" y="14" width="13" height="13"/>
    <rect x="14" y="14" width="13" height="13" fill="var(--s1)" opacity="0.6"/>
    <rect x="28" y="14" width="13" height="13"/><rect x="14" y="28" width="13" height="13"/>
  </g>
  <rect x="540" y="215" width="160" height="50" rx="6"/>
  <text x="620" y="236" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">Action</text>
  <text x="620" y="253" text-anchor="middle" fill="currentColor" stroke="none" opacity="0.75">stay / N / S / E / W</text>
  <line x1="440" y1="240" x2="538" y2="240" marker-end="url(#arr)"/>
  <text x="489" y="233" text-anchor="middle" fill="currentColor" stroke="none">picks one</text>
  <path d="M700,240 C716,240 716,292 620,292 L95,292 C60,292 60,200 95,160" marker-end="url(#arr)" stroke-dasharray="4 3"/>
  <text x="400" y="281" text-anchor="middle" fill="currentColor" stroke="none" opacity="0.75">moving costs 0.03 more and lands the agent on a new cell</text>
</g>
</svg>
<figcaption>Figure 1. One step, one agent. Food is the only thing agents interact with; they never touch each other. Whatever eats well enough to split, spreads.</figcaption>
</figure>
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

<section class="tldr">
<h2>TL;DR</h2>
<p>The simplest world we could build (food on a grid, creatures that eat, split, and die, with random mutation) ran for a million steps without dying out or exploding, kept evolving, and cost almost nothing to compute. We will keep it as the base.
The catch: after about 100,000 steps the creatures all settle on one trick, "keep walking", and the world stops looking different. Next we need something that pushes the world into new shapes, such as creatures interacting with each other.</p>
</section>

<h2>1. Question</h2>
<p>Everything we plan to build sits on one loop: creatures eat, reproduce with small random changes, and die. Before adding anything, we need to know if that loop alone holds up. Three things to check:</p>
<ol>
  <li><strong>Survival.</strong> Does the population last 1,000,000 steps without dying out or growing without limit?</li>
  <li><strong>Ongoing evolution.</strong> Do the creatures keep changing, or do they all become identical and stuck?</li>
  <li><strong>Cost.</strong> Is a long run cheap enough to be practical?</li>
</ol>

<h2>2. The world</h2>
<p>A 64 x 64 grid that wraps around at the edges. Each cell grows food. Creatures ("agents") stand on cells, and each step every agent goes through the loop in Figure 1.</p>
{diagram}
<p>Agents have no learning and no memory. The genome is a fixed list of 35 numbers that turns what the agent sees into one of five moves. A child gets the parent's numbers plus small random noise. Nobody tells the agents what to do; whatever works, spreads.</p>
<p><strong>Runs.</strong> Three runs from different random starts (seed 1, 2, 3), 1,000,000 steps each, starting with 200 random agents. Every 10,000 steps we record:</p>
<ul class="measures">
  <li><strong>Population</strong> - agents alive.</li>
  <li><strong>Energy</strong> - average fuel per agent (split at 10, die at 0).</li>
  <li><strong>Food per cell</strong> - average, from 0 (bare) to 1 (full).</li>
  <li><strong>Diversity</strong> - how different agents' genomes are from each other; 0 means all clones.</li>
  <li><strong>Drift</strong> - how far the average genome moved since the last record; 0 means evolution stopped.</li>
  <li><strong>Births</strong> per 10,000 steps (deaths match births almost exactly).</li>
  <li><strong>Actions</strong> - share of stay / N / S / E / W.</li>
  <li><strong>Speed</strong> - simulation steps per second.</li>
</ul>

<h2>3. Results</h2>
<div class="tw"><table>
<thead><tr><th>Seed</th><th>Population min / max / final</th><th>Diversity min / final</th><th>Drift min / median / max</th><th>Steps per second</th></tr></thead>
<tbody>{summary(data)}</tbody></table></div>
<ol class="verdicts">
<li><span class="verdict">Yes</span> Survival: all three runs stayed between about 500 and 540 agents.</li>
<li><span class="verdict">Yes</span> Ongoing evolution: the average genome kept moving and diversity never collapsed.</li>
<li><span class="verdict">Yes</span> Cost: about 100,000 steps per second with ~500 agents. A million steps takes seconds.</li>
</ol>

<h3>3.1 The population is stable and the grid is eaten bare</h3>
<div class="grid2">
{"".join(charts[:2])}
{"".join(charts[2:4])}
</div>
<p>Population settles at ~510 in every run; that number is set by how fast food regrows. Food sits near 0.05 out of 1.0: agents eat it almost as soon as it appears. Diversity stays well above zero.</p>

<h3>3.2 Evolution slows but never stops, and agents live longer over time</h3>
<div class="grid2">
{"".join(charts[4:6])}
</div>
<p>Drift is large at first (the random starting genomes are quickly replaced) and then stays clearly above zero. Births fall from 10,000-19,000 per 10,000 steps to 3,000-7,000: agents end up living three to six times longer. In every run the drop lines up with the change in behavior shown next.</p>

<h3>3.3 Everyone learns the same trick: keep walking</h3>
<div class="grid2">
{"".join(actions)}
{charts[6]}
</div>
<p>Within about 100,000 steps "stay" disappears. In seed 1 almost everyone walks west; in seeds 2 and 3, groups walking in different directions end up sharing the grid. The speed chart is for reference: the three runs shared one machine.</p>

<h2>4. Discussion</h2>
<p>The loop works: no collapse, no explosion, evolution keeps going, and compute is not a concern. That is the result we needed, and this loop stays as the base.</p>
<p>But the world is not interesting to watch. Once "keep walking" wins, the genes keep drifting while the world looks the same. The reason is visible in Figure 1: the only arrow into an agent comes from food. Agents never interact with each other, so nothing can push the world into a new shape. Genetic drift is not the same as visible change.</p>
<p>One thing we did not expect: turnover drops several-fold when the population shifts from one shared direction to a mix of directions. We have not looked into why; it is noted here as a lead, not a finding.</p>

<h2>5. Conclusion and next step</h2>
<p>Keep the minimal loop. Next, add something that lets the world change shape: interaction between agents (competition, predators) or an environment that changes on its own, and test whether that produces change we can actually see.</p>

<h2>Appendix: data</h2>
<p>Every 100,000th record is shown; the full data is in <code>results/seed*.csv</code>. Build this report with <code>uv run python experiments/e001_minimal_world/report.py</code>.</p>
{table(data)}
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
