#!/usr/bin/env python3
"""Build report.html for e113. Run from the repo root: uv run python experiments/e113_sea_catch/report.py

Reads the tables in `results/` (committed) and, for the yearly lines, `results/pilot/<run>_{log,lines}.csv`.
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
RES = os.path.join(HERE, "results")
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4"]
ALL, SOW, HUNGRY, E112 = 0, 1, 2, 3
DESIGNED = "2797"  # the designed line's root in hungry70 (provenance.csv)

INK = "#898781"
plt.rcParams.update({
    "svg.fonttype": "none", "font.family": "sans-serif", "font.size": 9, "text.color": INK, "axes.edgecolor": INK,
    "axes.labelcolor": INK, "axes.facecolor": "none", "axes.spines.top": False, "axes.spines.right": False,
    "axes.spines.left": False, "axes.grid": True, "axes.grid.axis": "y", "grid.color": INK, "grid.alpha": 0.25,
    "grid.linewidth": 0.8, "xtick.color": INK, "ytick.color": INK, "ytick.left": False, "legend.frameon": False,
    "legend.fontsize": 9, "figure.facecolor": "none", "savefig.transparent": True,
})


def rows(*path):
    with open(os.path.join(*path)) as f:
        return list(csv.DictReader(f))


def kfmt(x, _pos):
    return f"{x/1000:g}k" if abs(x) >= 1000 else f"{x:g}"


def figure(title, subtitle, fig):
    buf = io.StringIO()
    fig.savefig(buf, format="svg", bbox_inches="tight", pad_inches=0.05)
    plt.close(fig)
    return f"""
<figure class="fig">
  <figcaption><strong>{html.escape(title)}</strong><span>{html.escape(subtitle)}</span></figcaption>
  {buf.getvalue()}
</figure>"""


def chart(title, subtitle, series, xlabel="year", fmt=kfmt, log=False, ymin=None):
    """series: (label, xs, ys, slot, dashed)."""
    if log:
        fmt = lambda y, _p: f"{y / 1e6:g}M"
    fig, ax = plt.subplots(figsize=(6.4, 2.6))
    for label, xs, ys, slot, dashed in series:
        ax.plot(xs, ys, color=SERIES[slot], linewidth=1.6, label=label, linestyle="--" if dashed else "-")
    ax.set_xlabel(xlabel, loc="right")
    ax.margins(x=0)
    if log:
        ax.set_yscale("log")
    else:
        ax.yaxis.set_major_locator(MaxNLocator(4))
    if ymin is not None:
        ax.set_ylim(bottom=ymin)
    ax.yaxis.set_major_formatter(fmt)
    ax.legend(loc="lower left", bbox_to_anchor=(0, 1.0), ncols=len(series), handlelength=1.6, borderaxespad=0, columnspacing=1.2)
    return figure(title, subtitle, fig)


def animals(run, keep):
    out = {}
    for r in rows(RES, "pilot", run + "_lines.csv"):
        if keep(r) and r["root"] != DESIGNED:
            y = int(r["year"])
            out[y] = out.get(y, 0.0) + float(r["animals"])
    return out


CSS = """
:root { color-scheme: dark; --surface: #1a1a19; --page: #0d0d0d; --ink: #ffffff; --ink2: #c3c2b7; --grid: #2c2c2a; --border: rgba(255,255,255,0.10); --s1: #3987e5; }
* { box-sizing: border-box; }
body { margin: 0; background: var(--page); color: var(--ink); font: 15px/1.55 system-ui, -apple-system, "Segoe UI", sans-serif; }
main { max-width: 960px; margin: 0 auto; padding: 32px 20px 64px; }
h1 { font-size: 26px; margin: 0 0 4px; } h2 { font-size: 19px; margin: 40px 0 8px; } h3 { font-size: 16px; margin: 24px 0 8px; }
p, li { color: var(--ink); max-width: 72ch; }
.sub { color: var(--ink2); margin: 0 0 24px; }
.tldr { background: var(--surface); border: 1px solid var(--border); border-left: 4px solid var(--s1); border-radius: 8px; padding: 12px 18px; }
.tldr h2 { margin: 0 0 6px; font-size: 15px; } .tldr p { margin: 0; }
.grid2 { display: grid; grid-template-columns: repeat(auto-fit, minmax(min(420px, 100%), 1fr)); gap: 20px; }
.fig { margin: 0; background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 14px 14px 8px; }
.fig svg { width: 100%; height: auto; display: block; font-family: system-ui, -apple-system, "Segoe UI", sans-serif; }
figcaption strong { display: block; font-size: 15px; }
figcaption span { display: block; color: var(--ink2); font-size: 13px; min-height: 2.6em; margin-bottom: 6px; }
.diagram { margin: 12px 0; background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 12px 16px 8px; color: var(--ink); }
.diagram figcaption { color: var(--ink2); font-size: 13px; margin-top: 4px; }
.measures { columns: 2; column-gap: 24px; max-width: none; padding-left: 20px; } .measures li { break-inside: avoid; }
table { border-collapse: collapse; font-size: 13.5px; font-variant-numeric: tabular-nums; }
th, td { padding: 6px 12px; text-align: right; border-bottom: 1px solid var(--grid); }
th:first-child, td:first-child { text-align: left; } th { color: var(--ink2); font-weight: 600; }
.tw { overflow-x: auto; } details { margin: 8px 0; } summary { cursor: pointer; color: var(--ink2); }
.verdicts { list-style: none; padding: 0; margin: 12px 0 0; } .verdicts li { margin: 4px 0; }
.verdict { display: inline-block; padding: 1px 8px; border-radius: 4px; font-size: 12.5px; font-weight: 600; background: rgba(12,163,12,0.12); color: #0ca30c; }
.verdict.no { background: rgba(208,59,59,0.12); color: #e66767; }
.verdict.partly { background: rgba(250,178,25,0.15); color: #fab219; }
"""

DIAGRAM = """
<figure class="diagram">
<svg viewBox="0 0 720 190" role="img" aria-label="Four laws act on three parts of a body's life: reaching food at sea, paying for a press, and finding another body." style="max-width:100%;height:auto;display:block">
<defs><marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="currentColor"/></marker></defs>
<g fill="none" stroke="currentColor" stroke-width="1.2" font-size="12" font-family="system-ui, sans-serif">
  <rect x="15" y="20" width="200" height="58" rx="6"/>
  <text x="115" y="44" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">sight, cover</text>
  <text x="115" y="62" text-anchor="middle" fill="currentColor" stroke="none">seen by length, hidden by leaves</text>
  <rect x="260" y="20" width="200" height="58" rx="6" stroke="var(--s1)" stroke-width="2"/>
  <text x="360" y="44" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">press_work</text>
  <text x="360" y="62" text-anchor="middle" fill="currentColor" stroke="none">paid for what breaks, not for time</text>
  <rect x="505" y="20" width="200" height="58" rx="6"/>
  <text x="605" y="44" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">hunter's gut</text>
  <text x="605" y="62" text-anchor="middle" fill="currentColor" stroke="none">keeps what it swallows</text>
  <line x1="215" y1="49" x2="258" y2="49" marker-end="url(#arr)"/>
  <line x1="460" y1="49" x2="503" y2="49" marker-end="url(#arr)"/>
  <text x="237" y="38" text-anchor="middle" fill="currentColor" stroke="none">finds</text>
  <text x="482" y="38" text-anchor="middle" fill="currentColor" stroke="none">kills</text>
  <rect x="15" y="115" width="200" height="58" rx="6"/>
  <text x="115" y="139" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">floor</text>
  <text x="115" y="157" text-anchor="middle" fill="currentColor" stroke="none">food reached thins with depth</text>
  <rect x="505" y="115" width="200" height="58" rx="6"/>
  <text x="605" y="139" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">litter eater</text>
  <text x="605" y="157" text-anchor="middle" fill="currentColor" stroke="none">99% of the world's diet</text>
  <line x1="215" y1="144" x2="503" y2="144" marker-end="url(#arr)"/>
  <text x="360" y="134" text-anchor="middle" fill="currentColor" stroke="none">thins its food in open water</text>
  <line x1="605" y1="115" x2="605" y2="80" marker-end="url(#arr)"/>
  <text x="615" y="102" fill="currentColor" stroke="none">prey</text>
</g>
</svg>
<figcaption>Figure 1. The four laws, each behind a switch. The press's price is the one the catch hinges on.</figcaption>
</figure>
"""


def main():
    logs = {r: rows(RES, "pilot", r + "_log.csv") for r in ("all", "sow41", "hungry70")}
    dec = {r: rows(RES, f"pilot_{r}.csv") for r in ("all", "sow41", "hungry70")}
    e112 = rows(HERE, "..", "e112_layers", "results", "pilot.csv")
    hunters = rows(RES, "hunters.csv")
    names = [("all", "all", ALL), ("sow41", "sow41", SOW), ("hungry70", "hungry70", HUNGRY)]

    def yearly(run, key, y0=45):
        p = [(int(x["year"]), float(x[key])) for x in logs[run] if int(x["year"]) >= y0]
        return [a for a, _ in p], [b for _, b in p]

    def hunt(run, key):
        p = [(int(x["year"]), float(x[key])) for x in hunters if x["run"] == run]
        return [a for a, _ in p], [b for _, b in p]

    def decade(table, key):
        p = [(int(x["census"]) if "census" in x else 0, float(x[key])) for x in table if x[key] != ""]
        return [a for a, _ in p], [b for _, b in p]

    pct = lambda y, _p: f"{100 * y:g}%"
    c_matter = chart("Hunters' matter", "Genotypes with over half their lifetime diet in kills. Zero would mean no line lives on flesh; sow41 has none.",
                     [("all", *hunt("all", "matter_t"), ALL, False), ("hungry70", *hunt("hungry70", "matter_t"), HUNGRY, False)])
    c_kill = chart("Kills in the world's diet", "The line asked for 1% over a decade. A flat line at zero is e112's world.",
                   [("all", *hunt("all", "kill_of_diet"), ALL, False), ("hungry70", *hunt("hungry70", "kill_of_diet"), HUNGRY, False)], fmt=pct)
    c_bodies = chart("Bodies in the world", "A fall to zero would be a world emptied. The two runs with hunters end lower than the one without.",
                     [(n, *yearly(r, "bodies", 60), s, False) for r, n, s in names])
    c_held = chart("Held by island", "How far the ways differ by island, at each decade's census. The line asked for 0.2; e112 dashed.",
                   [(n, *decade(dec[r], "held"), s, False) for r, n, s in names] + [("e112", [50 + 10 * i for i in range(len(e112))], [float(x["held"]) for x in e112], E112, True)], xlabel="year (census)")
    one = lambda r: r["island"] == "1"
    other = lambda r: r["island"] not in ("0", "1")
    a1, h1, ao, ho = animals("all", one), animals("hungry70", one), animals("all", other), animals("hungry70", other)
    ys = list(range(68, 79))
    c_an1 = chart("Animals on island 1, where the hunter was put", "Log scale; year 70 is the injection. Together would mean no effect.",
                  [("all", ys, [a1[y] for y in ys], ALL, False), ("hungry70, without the line", ys, [h1[y] for y in ys], HUNGRY, False)], log=True)
    c_ano = chart("Animals on the other islands", "The same on the land the hunter was not put on. A local crash would leave these lines together.",
                  [("all", ys, [ao[y] for y in ys], ALL, False), ("hungry70, without the line", ys, [ho[y] for y in ys], HUNGRY, False)], log=True)

    def last(table, k, f="{:.2f}", scale=1.0):
        return f.format(float(table[-1][k]) * scale)
    table = "".join(
        f"<tr><td>{n}</td><td>{last(t, 'of_bare', '{:.0f}%', 100)}</td><td>{last(t, 'flesh_share', '{:.2f}%', 100)}</td><td>{float(t[-2]['held']):.2f} / {float(t[-1]['held']):.2f}</td><td>{last(t, 'ways_hill')}</td><td>{last(t, 'hill_size')}</td><td>{float(t[-1]['bodies']):,.0f}</td></tr>"
        for n, t in [("all", dec["all"]), ("sow41", dec["sow41"]), ("hungry70", dec["hungry70"]), ("e112 layers", e112)])

    ways = ""
    for r in ("all", "sow41", "hungry70"):
        for x in rows(RES, f"pilot_{r}_ways.csv"):
            ways += f"<tr><td>{r}</td><td>{100 * float(x['share']):.1f}%</td><td>{float(x['adult_mass']):.3g}</td><td>{100 * float(x['sea']):.0f}%</td><td>{float(x['travel_km_yr']):,.0f}</td><td>{float(x['frame']):.2f}</td><td>{float(x['muscle']):.2f}</td><td>{float(x['gut']):.2f}</td><td>{float(x['ate_litter']):.2f}</td><td>{float(x['ate_kill']):.2f}</td></tr>"

    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>e113 Sea and Catch</title>
<style>{CSS}</style>
</head>
<body>
<main>
<h1>e113: the sea as a place, and the catch</h1>
<p class="sub">Experiment report - 2026-11-01 - a gate on the trial world, then three runs on the islands to year 100</p>

<section class="tldr">
<h2>TL;DR</h2>
<p>With a press paid for what it breaks, a hunter evolves unaided and lives 25 years beside its prey, 2.7% of the matter, without emptying the world, in one history of two. The sea is still not a place: one body lives on land and at sea. The run ends before the hunter's fate is known.</p>
</section>

<h2>1. Question</h2>
<p>e112 left one line on one food. Would a sea that parts islands and a catch that pays, together, change that?</p>
<ol>
  <li><strong>A hunter lives.</strong></li>
  <li><strong>It does not empty the world.</strong></li>
  <li><strong>The sea is a place.</strong></li>
  <li><strong>Parted islands hold different sizes.</strong></li>
  <li><strong>A crash stays local</strong> (added before the pilot).</li>
</ol>

<h2>2. The world</h2>
<p>e112's world with four new laws. None names a hunter, a refuge or a size.</p>
{DIAGRAM}
<p><strong>Runs.</strong> <code>isles1</code>, one seed, to year 100. <code>all</code>; <code>sow41</code>, sown a year later; <code>hungry70</code>, <code>all</code> with 50 designed hunters on the largest island in year 70. The gate had failed (a hunter emptied the trial world in a year); the user chose to run these anyway. We read:</p>
<ul class="measures">
  <li><strong>Hunter</strong> - a genotype with over half its lifetime diet in kills.</li>
  <li><strong>Held</strong> - how far ways differ by island, 0 to 1.</li>
  <li><strong>Way</strong> - a group by diet, place, size, range and make (<code>analysis/ways.py</code>).</li>
  <li><strong>Animals</strong> - a body is a cohort of them.</li>
</ul>

<h2>3. Results</h2>
<div class="tw"><table>
<thead><tr><th>Years 91-100</th><th>Land, of bare</th><th>Flesh</th><th>Held, last two</th><th>Ways</th><th>Size spread</th><th>Bodies</th></tr></thead>
<tbody>{table}</tbody></table></div>
<ol class="verdicts">
<li><span class="verdict partly">Partly</span> A hunter lives: evolved yes, 25 years to the end; designed no, starved in four. Flesh 0.55%, under the 1% line.</li>
<li><span class="verdict partly">So far</span> It does not empty the world: 33,000 bodies at year 100. Which law holds it is unread.</li>
<li><span class="verdict no">No</span> The sea is a place: held 0.07-0.13 against the 0.2 line, lower than e112.</li>
<li><span class="verdict no">No</span> Parted islands hold sizes: two sizes stand in every run, 13-32x apart, but not by island.</li>
<li><span class="verdict no">No</span> A crash stays local: the hunter stood on eight land masses within two years.</li>
</ol>

<h3>3.1 A hunter evolves and stays</h3>
<div class="grid2">{c_matter}{c_kill}</div>
<p>The first hunter is one body in year 76. Matter then doubles about every three years, and has been flat since year 97. It is the same founder's line as its prey: a frame of 0.36 and a gut of 0.13 against their 0.10 and 0.56. <code>hungry70</code> shares <code>all</code>'s first 70 years, so these are one history; <code>sow41</code> has none.</p>

<h3>3.2 The world stands; the sea does not part it</h3>
<div class="grid2">{c_bodies}{c_held}</div>
<p>The two largest ways of <code>all</code> are one body at 18.4 kg: 12% at sea with a gut of 0.56, and 73% at sea with 0.65. <code>floor</code> moved the share of bodies at sea only from 33% to 24-27%.</p>

<h3>3.3 A hunter on one island hits all of them, then starves</h3>
<div class="grid2">{c_an1}{c_ano}</div>
<p>The line as written, in bodies and matter, read "no crash to test": island 1's matter never fell under 0.69 of <code>all</code>'s. A body is a cohort, and the animals show it: at year 72, 3.9 million against 64 million on island 1, and 6.0 against 22.6 on the others. Animals fell far more than matter, which reads as the young eaten, everywhere; that was not measured directly.</p>

<h2>4. Discussion</h2>
<p>The designed hunter failed the gate and the evolved one lives. The designed body is a strong killer that takes its food down and starves; the evolved body arrives as one mutant among the prey it can already eat, and grows about a hundred times slower than the gate's arithmetic said a hunter could. Why was not read.</p>
<p>The world held the designed hunter by its starving, not by the sea. Nothing shows <code>sight</code> or <code>cover</code> doing anything, and all four laws ran together, so the hunter cannot yet be credited to one.</p>
<p>It does not show a food web. Flesh is 0.55%, one founder's line holds everything, and litter is still 99% of the diet. Animal counts swing tenfold in <code>all</code> alone, so only the first years' gap is read.</p>

<h2>5. Conclusion and next step</h2>
<p>The catch can be lived in, and the sea is still no place. The press's price is kept; <code>floor</code>, <code>sight</code> and <code>cover</code> stay on, with no effect shown. Next is the hunter's fate, which needs the run carried past year 100.</p>

<h2>Appendix: data</h2>
<p>Thresholds are in <code>results/provenance.csv</code>; the rest in <code>results/*.csv</code>. Build with <code>uv run python experiments/e113_sea_catch/report.py</code>.</p>
<details><summary>The ways at year 100 over 1% of the matter</summary><div class='tw'><table><thead><tr><th>run</th><th>share</th><th>adult kg</th><th>at sea</th><th>km a year</th><th>frame</th><th>muscle</th><th>gut</th><th>litter</th><th>kill</th></tr></thead><tbody>{ways}</tbody></table></div></details>
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
