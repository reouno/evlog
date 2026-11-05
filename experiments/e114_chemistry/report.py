#!/usr/bin/env python3
"""Build report.html for this experiment.

Charts: matplotlib, exported as SVG and inlined. Diagram: hand-written SVG.
Run from the repo root: uv run python experiments/e114_chemistry/report.py
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
    """Read a CSV into a list of rows (dicts of strings)."""
    with open(os.path.join(HERE, path)) as f:
        return list(csv.DictReader(f))


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


def line_chart(title, subtitle, xs, series, ymin=None, xlabel="year", ncol=3):
    """series: list of (label, ys, slot)."""
    fig, ax = new_axes(xlabel)
    for label, ys, slot in series:
        ax.plot(xs, ys, color=SERIES[slot], linewidth=1.6, label=label)
    if ymin is not None:
        ax.set_ylim(ymin, max(v for _, ys, _ in series for v in ys) * 1.12)
    ax.yaxis.set_major_formatter(kfmt)
    ax.yaxis.set_major_locator(MaxNLocator(4))
    legend_above(ax, ncol)
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
.verdict.partly { background: rgba(250,178,25,0.15); color: #fab219; }
"""


DIAGRAM = """
<figure class="diagram">
<svg viewBox="0 0 720 232" role="img" aria-label="Dead tissue keeps its lock and toughness in litter slots; the rot wears it soft and slower the farther its lock is from the plain bond" style="max-width:100%;height:auto;display:block">
<defs><marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="currentColor"/></marker></defs>
<g fill="none" stroke="currentColor" stroke-width="1.2" font-size="12" font-family="system-ui, sans-serif">
  <rect x="10" y="20" width="160" height="56" rx="6"/>
  <text x="90" y="44" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">living tissue</text>
  <text x="90" y="62" text-anchor="middle" fill="currentColor" stroke="none">a lock (gene), an A share</text>
  <rect x="280" y="20" width="190" height="56" rx="6"/>
  <text x="375" y="44" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">litter: 4 slots a cell</text>
  <text x="375" y="62" text-anchor="middle" fill="currentColor" stroke="none">apart by toughness + lock bits</text>
  <rect x="590" y="20" width="120" height="56" rx="6"/>
  <text x="650" y="53" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">soil</text>
  <rect x="280" y="140" width="190" height="56" rx="6" stroke="var(--s1)" stroke-width="2"/>
  <text x="375" y="164" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">share still whole</text>
  <text x="375" y="182" text-anchor="middle" fill="currentColor" stroke="none">1 on arrival, worn by the rot</text>
  <rect x="590" y="140" width="120" height="56" rx="6"/>
  <text x="650" y="164" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">body</text>
  <text x="650" y="182" text-anchor="middle" fill="currentColor" stroke="none">mouth, gut keys</text>
  <line x1="170" y1="48" x2="278" y2="48" marker-end="url(#arr)"/>
  <text x="224" y="38" text-anchor="middle" fill="currentColor" stroke="none">dies</text>
  <line x1="470" y1="48" x2="588" y2="48" marker-end="url(#arr)"/>
  <text x="529" y="38" text-anchor="middle" fill="currentColor" stroke="none">rot, slower</text>
  <text x="529" y="66" text-anchor="middle" fill="currentColor" stroke="none">by its lock</text>
  <line x1="375" y1="76" x2="375" y2="138" marker-end="url(#arr)"/>
  <text x="385" y="112" fill="currentColor" stroke="none">the rot wears it</text>
  <line x1="470" y1="168" x2="588" y2="168" marker-end="url(#arr)"/>
  <text x="529" y="158" text-anchor="middle" fill="currentColor" stroke="none">soft to a mouth</text>
  <path d="M90,76 L90,222 L650,222 L650,198" stroke-dasharray="4 4" marker-end="url(#arr)"/>
  <text x="100" y="208" fill="currentColor" stroke="none">eaten alive: under 1% of the diet</text>
</g>
</svg>
<figcaption>Figure 1. A key opens a lock: a gut digests a bulk as far as its keys fit the lock. Dead tissue keeps its lock and A; the rot wears it soft (blue), slower the farther its lock lies from the plain bond.</figcaption>
</figure>
"""


def col(rows, k, f=float):
    return [f(r[k]) for r in rows]


def main():
    G = os.path.join(HERE, "results", "gate")
    P = os.path.join(HERE, "results", "pilot")
    gate = {r: load_csv(os.path.join(G, r + "_log.csv")) for r in ("off", "lock", "no_lit_eat", "make", "worn", "worn80")}
    nobody = {int(r["year"]): float(r["land_biomass"]) for r in load_csv(os.path.join(HERE, "..", "e112_layers", "results", "read", "nobody_log.csv"))}
    pil = {"e113 seed 1": load_csv(os.path.join(HERE, "..", "e113_sea_catch", "results", "pilot", "all_log.csv"))}
    for n, f in (("law seed 1", "lock"), ("e113 seed 2", "off_l2"), ("law seed 2", "lock_l2"), ("e113 seed 3", "off_l3"), ("law seed 3", "lock_l3")):
        pil[n] = load_csv(os.path.join(P, f + "_log.csv"))
    names = {"off": "e113 (law off)", "lock": "first design", "no_lit_eat": "one pile", "make": "kept by make", "worn": "worn soft by rot"}

    def land(run):
        rows = [r for r in gate[run] if 15 <= float(r["year"]) <= 30]
        return [float(r["year"]) for r in rows], [float(r["land_biomass"]) / nobody[int(float(r["year"]))] for r in rows]

    charts1 = []
    xs, _ = land("off")
    charts1.append(line_chart("Land against the world without bodies", "Trial world; 1 is the land of a world never sown with bodies. Bodies are sown in year 15.",
                              xs, [(names[r], land(r)[1], i) for i, r in enumerate(("off", "lock", "no_lit_eat", "make", "worn"))], ymin=0))
    bxs = [float(r["year"]) for r in gate["off"] if float(r["year"]) >= 15]
    ser = [(names[r], [float(r2["bodies"]) for r2 in gate[r] if float(r2["year"]) >= 15], i) for i, r in enumerate(("off", "lock", "no_lit_eat", "make", "worn"))]
    charts1.append(line_chart("Bodies on the trial world", "Sown 300 in year 15. Zero is a world whose animals died out.", bxs, ser, ymin=0))

    # islands: bodies by seed, law (solid) against e113 (dashed)
    fig, ax = new_axes("year")
    for i, s in enumerate((1, 2, 3)):
        for n, ls in ((f"e113 seed {s}", "--"), (f"law seed {s}", "-")):
            rows = [r for r in pil[n] if 40 <= float(r["year"]) <= 60]
            ax.plot([float(r["year"]) for r in rows], [max(float(r["bodies"]), 0.5) for r in rows], color=SERIES[i], ls=ls, lw=1.6, label=n)
    ax.set_yscale("log")
    ax.set_ylim(0.5, 1e5)
    legend_above(ax, 3)
    c_isl = figure("Bodies on the islands", "Solid: with the law; dashed: e113. Sown in year 40; a line at the floor is none.", to_svg(fig))

    fig, ax = new_axes("year")
    for i, s in enumerate((2, 3)):
        for n, ls in ((f"e113 seed {s}", "--"), (f"law seed {s}", "-")):
            rows = [r for r in pil[n] if 15 <= float(r["year"]) <= 60]
            ax.plot([float(r["year"]) for r in rows], [max(float(r["p_locked"]), 1e-12) for r in rows], color=SERIES[i + 1], ls=ls, lw=1.4, label=n)
    ax.set_yscale("log")
    ax.set_ylim(1e-12, 1)
    ax.axhline(0.1, color=INK, lw=0.8, ls=":")
    legend_above(ax, 2)
    c_lock = figure("Producers' mass on a locked genotype", "Share, log scale; dotted: the 10% a lock was to reach. Dashed: the same genes where nothing reads a lock.", to_svg(fig))

    def at(rows, y, k):
        for r in rows:
            if int(float(r["year"])) == y:
                return r[k]
        return ""

    trial = ""
    for r in ("off", "lock", "no_lit_eat", "make", "worn"):
        trial += f"<tr><td>{names[r]}</td><td>{float(at(gate[r], 30, 'land_biomass')) / nobody[30]:.2f}</td><td>{int(float(at(gate[r], 40, 'bodies'))):,}</td></tr>"
    isl = ""
    for s in (1, 2, 3):
        a, b = pil[f"e113 seed {s}"], pil[f"law seed {s}"]
        isl += f"<tr><td>seed {s}</td><td>{int(float(at(a, 60, 'bodies'))):,}</td><td>{int(float(at(b, 60, 'bodies'))):,}</td><td>{float(max(float(r['p_locked']) for r in b if float(r['year']) >= 15)):.0e}</td></tr>"

    tables = data_table(["year", "bodies", "land_biomass", "p_locked", "p_lock_cohorts"],
                        {n: {k: [float(r[k]) for r in rows if float(r["year"]) >= 15] for k in ("year", "bodies", "land_biomass", "p_locked", "p_lock_cohorts")} for n, rows in pil.items() if "p_locked" in rows[0]}, every=5)

    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>e114 Chemistry of Matter - Report</title>
<style>{CSS}</style>
</head>
<body>
<main>
<h1>e114: does a chemistry of keys and locks part the food?</h1>
<p class="sub">Experiment report - 2026-11-05 - three gates on the trial world, a pilot on the islands, two more life seeds</p>

<section class="tldr">
<h2>TL;DR</h2>
<p>The world stands with the chemistry in two seeds of three, once the rot softens the dead, at 63-77% of e113's bodies. Locks are born and pay a little, but never pass 2e-5 of the producers' mass: the bodies hardly eat living plants, so a plant's defence is not paid for. e113's animals lived on litter softened by a rule. Next: why a living plant costs a body more than the dead.</p>
</section>

<h2>1. Question</h2>
<p>In e113 the bodies ate litter, 99.8% of their diet, and one founder's line held the world. The dead were the one food that asked nothing. Instead of giving litter a value, e114 gives all matter a general chemistry: a tissue's bulk carries a lock, and a gut digests it as far as its keys fit.</p>
<ol>
  <li><strong>The world stands</strong> with it.</li>
  <li><strong>Locks spread</strong>: two or more each hold 10% of the producers' mass.</li>
  <li><strong>Litter is not one food</strong>: bodies differ in keys (read only if 2).</li>
  <li><strong>The sea parts by food</strong> (read only if 2).</li>
</ol>

<h2>2. The world</h2>
<p>e113's world, with the lock behind one switch. A lock is a gene, one point mutation from a compound gene. The plain bond, lock 0, is open to all.</p>
{DIAGRAM}
<p><strong>Runs.</strong> Three gates on the 16 km trial world (bodies sown in year 15), each revising the design. Then the 64 km islands to year 100, and life seeds 2 and 3 to year 60, each against e113.</p>
<ul class="measures">
  <li><strong>land</strong> - plant mass on land over a world never sown with bodies.</li>
  <li><strong>bodies</strong> - animals alive.</li>
  <li><strong>locked share</strong> - producers' mass on a genotype with a lock.</li>
</ul>

<h2>3. Results</h2>
<div class="grid2">
<div class="tw"><table><thead><tr><th>Trial world</th><th>land, y30</th><th>bodies, y40</th></tr></thead><tbody>{trial}</tbody></table></div>
<div class="tw"><table><thead><tr><th>Islands</th><th>e113 bodies, y60</th><th>law bodies, y60</th><th>locked share, most</th></tr></thead><tbody>{isl}</tbody></table></div>
</div>
<ol class="verdicts">
<li><span class="verdict partly">Partly</span> The world stands: in two seeds of three, with 63-77% of e113's bodies at year 60.</li>
<li><span class="verdict no">No</span> Locks spread: under 2e-5 of the producers' mass to year 60.</li>
<li><span class="verdict partly">Not read</span> Hypotheses 3 and 4: they needed locks.</li>
</ol>

<h3>3.1 The first design took the land; a litter as hard as its tissue fed nobody</h3>
<div class="grid2">
{"".join(charts1)}
</div>
<p>Small eaters fed by litter grew sevenfold and grazed the leaves down before any body was sown. Taking them off it saved the land but not the bodies. Keeping the dead apart by what they are made of did not help either. Only a rot that wears the dead soft brought the bodies back.</p>

<h3>3.2 On the islands the law's world stands in two seeds of three</h3>
<div class="grid2">
{c_isl}
{c_lock}
</div>
<p>Both worlds pass a bottleneck of a few dozen bodies after the sowing. In seed 1 the law's world fell to none and e113's held 33. Locks are born every decade and pay a little: their share is 100-1,000 times that of the same genes where nothing reads a lock. They are still nowhere near 10%.</p>

<h2>4. Discussion</h2>
<p>The gates found a rule the old world stood on. In e113 dead tissue lost its toughness at death, so litter was the softest food in the world. Given its tissue's toughness, it fed no body. Worn soft by its own rot, it feeds three quarters as many.</p>
<p>A lock is a plant's defence, and a defence pays only when the living are eaten. The bodies eat living plants for under 1% of their diet, so there is almost nothing for a lock to defend against. A second possible reason was not read: a lock gene is most often born from a compound gene, and loses that compound.</p>
<p>The user corrected one revision: the dead were first to be parted by organ (leaf soft, wood hard). They are parted by their make instead, so that a parting can come out of the matter or not.</p>

<h2>5. Conclusion and next step</h2>
<p>The chemistry stays in the crate, and the soft litter rule is gone. The bodies still eat the dead alone. The next step reads, from the laws' own arithmetic, what a living leaf, stem, root or seed costs a body against the dead. Locks can matter only once living plants are eaten.</p>

<h2>Appendix: data</h2>
<p>Island runs every five years from year 15, when the producers stand. The full logs are in <code>results/gate/</code> and <code>results/pilot/</code>; the gate's readings in <code>results/gate.csv</code> and <code>results/provenance.csv</code>. Build this report with <code>uv run python experiments/e114_chemistry/report.py</code>.</p>
{tables}
</main>
</body>
</html>
"""
    out = os.path.join(HERE, "report.html")
    with open(out, "w") as f:
        f.write(page)
    import re
    prose = page.split("<h2>Appendix")[0].split('<section class="tldr">')[1]
    prose = re.sub(r"<svg.*?</svg>|<table.*?</table>", " ", prose, flags=re.S)
    words = len(re.sub(r"<[^>]+>", " ", prose).split())
    print(f"wrote {out} ({os.path.getsize(out)//1024} KB), ~{words} words of prose")


if __name__ == "__main__":
    main()
