#!/usr/bin/env python3
"""Build report.html for this experiment.

Charts and maps: matplotlib, exported as SVG and inlined. Diagram: hand-written SVG. The six looks at the map
page (shots/*.jpg) are embedded, so the page stands alone.
Run from the repo root: uv run python experiments/e117_map/report.py
"""
import base64
import csv
import datetime
import html
import io
import json
import os

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap, ListedColormap, LogNorm, Normalize, PowerNorm
from matplotlib.ticker import MaxNLocator

matplotlib.use("svg")

HERE = os.path.dirname(os.path.abspath(__file__))
PRE = os.path.join(HERE, "results", "map")
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4"]  # fixed slot order

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

# Maps: from dry earth through water to pale, lighter as it gets wetter; snow from slate to white over bare land.
WATER = LinearSegmentedColormap.from_list("water", ["#4a3819", "#7d6128", "#3f9a8c", "#6fb4f5", "#e6f3ff"])
SNOW = LinearSegmentedColormap.from_list("snow", ["#5d6f86", "#ffffff"])
BARE = ListedColormap(["#45423a"])


# ---------- data ----------

def read_rows(path):
    with open(os.path.join(HERE, path)) as f:
        return list(csv.DictReader(f))


def load_world():
    """The kept years' annual maps, the static fields and the twelve mean months, loaded as `read.py` loads them."""
    m = json.load(open(PRE + "_maps.json"))
    n, F, S, Y = m["n"], m["fields"], m["static"], len(m["years"])
    a = np.fromfile(PRE + "_maps.bin", dtype="<f4")
    ann = a[:Y * len(F) * n * n].reshape(Y, len(F), n, n).mean(0)
    st = a[Y * len(F) * n * n:].reshape(len(S), n, n)
    sj = json.load(open(PRE + "_season.json"))
    mo = np.fromfile(PRE + "_season.bin", dtype="<f4").reshape(12, len(sj["fields"]), n, n)
    return {
        "n": n, "years": m["years"], "start": sj["start_day"],
        "ann": {k: ann[F.index(k)] for k in F}, "st": {k: st[S.index(k)] for k in S},
        "mo": {k: mo[:, sj["fields"].index(k)] for k in sj["fields"]},
    }


def day_name(day, short=False):
    d = datetime.date(2001, 1, 1) + datetime.timedelta(days=int(day) % 365)
    return f"{d.day} {d.strftime('%b' if short else '%B')}"


def span(start, first, last):
    """The calendar days of months first..last (months are twelfths of the year from `start`)."""
    return f"{day_name(start + first * 365 / 12)} - {day_name(int(start + (last + 1) * 365 / 12) - 1)}"


# ---------- chart helpers ----------

def kfmt(x, _pos):
    return f"{x/1000:g}k" if abs(x) >= 1000 else f"{x:g}"


def to_svg(fig):
    buf = io.StringIO()
    fig.savefig(buf, format="svg", bbox_inches="tight", pad_inches=0.05)
    plt.close(fig)
    return buf.getvalue()


def legend_above(ax, n):
    ax.legend(loc="lower left", bbox_to_anchor=(0, 1.0), ncols=n, handlelength=1.2, borderaxespad=0, columnspacing=1.2)


def figure(title, subtitle, svg):
    return f"""
<figure class="fig">
  <figcaption><strong>{html.escape(title)}</strong><span>{html.escape(subtitle)}</span></figcaption>
  {svg}
</figure>"""


def month_chart(title, subtitle, start, series, ymax=None):
    """series: list of (label, twelve values, slot). The axis is the calendar, in days from the run's first month:
    a month of the run (a twelfth of the year from `start`) is drawn at its middle."""
    fig, ax = plt.subplots(figsize=(6.4, 2.8))
    for label, ys, slot in series:
        ax.plot([(i + 0.5) * 365 / 12 for i in range(12)], ys, color=SERIES[slot], linewidth=1.6, marker="o", markersize=3, label=label)
    firsts = [datetime.date(2001, (2 + k) % 12 + 1, 1) for k in range(1, 13)]  # 1 April ... 1 March
    ax.set_xlim(0, 365)
    ax.set_xticks([(d.timetuple().tm_yday - 1 - start) % 365 for d in firsts], [d.strftime("%b") for d in firsts])
    ax.set_xlabel(f"calendar month (tick: its first day), from {day_name(start)}", loc="right")
    ax.set_ylim(0, ymax if ymax else max(v for _, ys, _ in series for v in ys) * 1.12)
    ax.yaxis.set_major_locator(MaxNLocator(4))
    ax.yaxis.set_major_formatter(kfmt)
    legend_above(ax, len(series))
    return figure(title, subtitle, to_svg(fig))


def map_chart(title, subtitle, w, field, cmap, norm, ticks, extend="neither", shown=None):
    """One field on the land, north up, the sea left blank. `shown`: cells drawn (the rest of the land is bare)."""
    n, land = w["n"], w["st"]["sea"] < 0.5
    km = n * 0.125
    lat = w["st"]["lat"]
    fig, ax = plt.subplots(figsize=(6.4, 5.5))
    ax.grid(False)
    if shown is not None:
        ax.imshow(np.ma.masked_where(~land, np.zeros((n, n))), origin="lower", cmap=BARE, extent=(0, km, 0, km), interpolation="nearest")
    cells = land if shown is None else land & shown
    im = ax.imshow(np.ma.masked_where(~cells, field), origin="lower", cmap=cmap, norm=norm, extent=(0, km, 0, km), interpolation="nearest")
    c = (np.arange(n) + 0.5) * 0.125
    ax.contour(c, c, land.astype(float), levels=[0.5], colors=INK, linewidths=0.5)
    for y in (km / 4, km / 2, 3 * km / 4):  # the four latitude bands of the table
        ax.axhline(y, color=INK, linewidth=0.6, alpha=0.5, linestyle=(0, (4, 4)))
    lo, hi = float(lat[0, 0]), float(lat[-1, 0])
    edge = lambda y: lo - (hi - lo) / (2 * (n - 1)) + (hi - lo + (hi - lo) / (n - 1)) * y / km
    ax.set_yticks([0, km / 4, km / 2, 3 * km / 4, km], [f"{edge(y):.0f} N" for y in (0, km / 4, km / 2, 3 * km / 4, km)])
    ax.set_xticks([0, 4, 8, 12, 16])
    ax.set_xlabel("km, west to east", loc="right")
    ax.set_aspect("equal")
    cb = fig.colorbar(im, ax=ax, fraction=0.035, pad=0.03, extend=extend, ticks=ticks)
    cb.outline.set_visible(False)
    cb.ax.minorticks_off()
    cb.ax.tick_params(length=0)
    cb.ax.set_yticklabels([f"{t:,g}" for t in ticks])
    return figure(title, subtitle, to_svg(fig))


def table(headers, rows):
    return ("<div class='tw'><table><thead><tr>" + "".join(f"<th>{html.escape(h)}</th>" for h in headers)
            + "</tr></thead><tbody>"
            + "".join("<tr>" + "".join(f"<td>{html.escape(str(v))}</td>" for v in r) + "</tr>" for r in rows)
            + "</tbody></table></div>")


def folded(name, body, shown=False):
    return f"<details{' open' if shown else ''}><summary>{html.escape(name)}</summary>{body}</details>"


def shot(name):
    with open(os.path.join(HERE, "shots", name + ".jpg"), "rb") as f:
        return "data:image/jpeg;base64," + base64.b64encode(f.read()).decode()


def pair(a, b, caption):
    """Two looks at one place: (file, its date, alt text) twice, and a caption."""
    cells = "".join(f'<div><span class="when">{html.escape(when)}</span><img src="{shot(f)}" alt="{html.escape(alt)}"></div>'
                    for f, when, alt in (a, b))
    return f'<figure class="fig shots"><div class="pair">{cells}</div><figcaption><span>{caption}</span></figcaption></figure>'


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
th:first-child, td:first-child { text-align: left; } td { white-space: nowrap; }
th { color: var(--ink2); font-weight: 600; }
.tw { overflow-x: auto; margin: 0 0 12px; }
details { margin: 8px 0; } summary { cursor: pointer; color: var(--ink2); }
.verdicts { list-style: none; padding: 0; margin: 12px 0 0; } .verdicts li { margin: 4px 0; }
.verdict { display: inline-block; padding: 1px 8px; border-radius: 4px; font-size: 12.5px; font-weight: 600; background: rgba(12,163,12,0.12); color: #0ca30c; }
.verdict.no { background: rgba(208,59,59,0.12); color: #e66767; }
.verdict.partly { background: rgba(250,178,25,0.15); color: #fab219; }
.shots { margin: 0 0 16px; }
.pair { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
.pair img { width: 100%; height: auto; display: block; border-radius: 4px; }
.when { display: block; color: var(--ink2); font-size: 13px; margin-bottom: 4px; }
.shots figcaption span { min-height: 0; margin: 8px 0 4px; max-width: 80ch; }
"""

# Hand-written mechanism diagram: currentColor for lines and text, var(--s1) for the storm track's edge, the one
# thing the year hangs on. The three numbers in braces come from results/map_reading.csv.
DIAGRAM = """
<figure class="diagram">
<svg viewBox="0 0 830 306" role="img" aria-label="Wet sea air under a front rains on an island's windward slope and comes down short of water; the storm track's edge lies north of most of the map at midsummer and south of all of it at midwinter" style="max-width:100%;height:auto;display:block">
<defs><marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="currentColor"/></marker></defs>
<g fill="none" stroke="currentColor" stroke-width="1.2" font-size="12" font-family="system-ui, sans-serif">
  <text x="20" y="22" fill="currentColor" stroke="none" font-weight="600">West to east across the high island, under a front</text>
  <polygon points="150,260 240,110 330,215 430,245 450,260" fill="currentColor" fill-opacity="0.08"/>
  <line x1="20" y1="260" x2="150" y2="260"/><line x1="450" y1="260" x2="490" y2="260"/>
  <text x="24" y="282" fill="currentColor" stroke="none">sea</text>
  <text x="252" y="205" text-anchor="middle" fill="currentColor" stroke="none">summit {top} m</text>
  <line x1="20" y1="158" x2="138" y2="158" marker-end="url(#arr)"/>
  <text x="79" y="128" text-anchor="middle" fill="currentColor" stroke="none">wet sea air</text>
  <text x="79" y="144" text-anchor="middle" fill="currentColor" stroke="none">under a front</text>
  <path d="M150,158 Q200,70 250,70" marker-end="url(#arr)"/>
  <text x="112" y="92" text-anchor="middle" fill="currentColor" stroke="none">lifted and cooled</text>
  <g stroke-opacity="0.75">
    <line x1="188" y1="128" x2="184" y2="140"/><line x1="200" y1="112" x2="196" y2="124"/>
    <line x1="176" y1="150" x2="172" y2="162"/><line x1="192" y1="152" x2="188" y2="164"/>
    <line x1="212" y1="104" x2="208" y2="116"/><line x1="206" y1="132" x2="202" y2="144"/>
    <line x1="178" y1="176" x2="174" y2="188"/><line x1="220" y1="120" x2="217" y2="130"/>
  </g>
  <text x="70" y="200" fill="currentColor" stroke="none">rain falls on</text>
  <text x="70" y="216" fill="currentColor" stroke="none">the way up</text>
  <path d="M262,72 Q330,80 352,168" marker-end="url(#arr)"/>
  <text x="348" y="86" fill="currentColor" stroke="none">comes down</text>
  <text x="348" y="102" fill="currentColor" stroke="none">short of water</text>
  <line x1="374" y1="184" x2="482" y2="184" marker-end="url(#arr)"/>
  <text x="428" y="152" text-anchor="middle" fill="currentColor" stroke="none">fronts refill it</text>
  <text x="428" y="168" text-anchor="middle" fill="currentColor" stroke="none">within a few km</text>
  <text x="170" y="282" text-anchor="middle" fill="currentColor" stroke="none">west lowlands: {west} mm a year</text>
  <text x="400" y="282" text-anchor="middle" fill="currentColor" stroke="none">east lowlands: {east} mm</text>

  <text x="520" y="22" fill="currentColor" stroke="none" font-weight="600">The storm track's edge through the year</text>
  <rect x="556" y="50" width="150" height="200" rx="4"/>
  <text x="548" y="54" text-anchor="end" fill="currentColor" stroke="none">64 N</text>
  <text x="548" y="254" text-anchor="end" fill="currentColor" stroke="none">44 N</text>
  <text x="631" y="72" text-anchor="middle" fill="currentColor" stroke="none" font-weight="600">the map</text>
  <text x="631" y="102" text-anchor="middle" fill="currentColor" stroke="none">rain in every season</text>
  <text x="631" y="165" text-anchor="middle" fill="currentColor" stroke="none">dry summer,</text>
  <text x="631" y="181" text-anchor="middle" fill="currentColor" stroke="none">wet winter</text>
  <text x="631" y="275" text-anchor="middle" fill="currentColor" stroke="none">south of the map</text>
  <g stroke="var(--s1)" stroke-width="2">
    <line x1="556" y1="130" x2="712" y2="130"/>
    <line x1="556" y1="210" x2="712" y2="210" stroke-dasharray="5 4"/>
    <line x1="556" y1="290" x2="712" y2="290"/>
  </g>
  <text x="720" y="134" fill="currentColor" stroke="none">midsummer, 56 N</text>
  <text x="720" y="214" fill="currentColor" stroke="none">equinoxes, 48 N</text>
  <text x="720" y="294" fill="currentColor" stroke="none">midwinter, 40 N</text>
</g>
</svg>
<figcaption>Figure 1. Left: the air is followed west to east. Under a front it arrives wet, rains as a slope lifts it
(a slope is crossed in 200-400 s, the rain falls in 200 s) and comes down short of water. Right: a front lasts 1.5 days,
2.5 clear days follow, and each reaches south to about the track's edge (blue): 48 N, 8 degrees further north at
midsummer and south at midwinter. Rows it does not reach lie under sunk air, a fifth short of the sea's, where it
rains nowhere.</figcaption>
</figure>
"""

# Every sentence of the report's prose, so that its words can be counted against the skill's budgets.
TEXT = {
    "tldr": """A 16 km map of islands across 44-64 N now has places and a year. Fronts reach the south in winter
and stay north in summer: the south's lowlands get 7% of their rain in summer and their soil falls to 0.28 of its
fill; the north has rain in every season and four months of snow. A lee is about twice as dry as the windward
side, not five times. Nothing lives here yet. Next: plants at metres.""",
    "question": """#135 rebuilds the world at an animal's size; its first rung is the map. On a first look the
season changed and the user could not tell what differed, so the year's water was added.""",
    "h1": "Latitude and the westerlies give at least 10 C north to south, a windward side five times wetter than the lee, and a snow line.",
    "h2": "A 5 m ground drawn once from the coarse one reads as a landscape an animal could walk.",
    "h3": "A place looks different in January and August, and in north and south.",
    "world": """128 x 128 cells of 125 m, a fifth land, latitudes 44-64 N from south to north, a year of 365
days, wind from the west-south-west. The air is followed across the map (Figure 1). Rain on freezing land lies as snow
and melts by the degrees above freezing. The 5 m ground is drawn once, at the end.""",
    "runs": """One run on Ubuntu, six threads, terrain seed 23: twenty bare years, the last ten kept, 95 s. Lowlands
are land under 300 m. Months run from the spring equinox, so summer is 20 June - 18 September. We read:""",
    "m1": "rain - mm a year, a quarter or a month.",
    "m2": "soil's fill - the share of the soil's water store that is full; 1 is soaked.",
    "m3": "months of snow - months whose mean pack is over 5 mm of water; 0 is no snow line.",
    "m4": "west against east - an island's lowland rain on each side of its summit; equal means no lee.",
    "v1": """hypothesis 1: 11.4 C north to south (asked 10) and a snow line, but windward lowlands get twice the
lee's rain on three islands, 7.5 times on one (asked 5).""",
    "v2": """hypothesis 2: as far as watched (the user: "the terrain looks good"): 49 km2 of land, 1.0 km2 of
ponds and 15 km of streams, still straight down smooth slopes.""",
    "v3": """hypothesis 3: the south's lowlands get 7% of their rain in summer, the north's 19%. Whether the eye
sees it on the page is the user's to say.""",
    "gallery": "No gallery of bodies: nothing lives on the map yet.",
    "r1": """Height is the strongest contrast: 2,176 mm falls over 1,200 m, and the high island's rain runs
from 28 to 2,734 mm. The lee is weaker than asked because it is narrow: the fronts refill air that a slope has wrung
within a few km, so only lowland close behind a height stays dry. Snow lies four months on the north's lowlands, five
on the summits, never in the south.""",
    "r2": """In winter the fronts reach every row and rain is nearly even from south to north. In summer they stay
north and the south's lowlands get 36 mm in three months. The ground follows the air: the south's soil is back at
0.95 by winter, and the north's stays at 0.87 through summer. Before the fronts existed this map had no dry season,
and a south wetter than its north.""",
    "r3": """The dry season is a place as well as a time: in summer the southern lowlands and the lees empty, while
the heights above them stay wetter. Water leaves the land the same way: the two driest months each
carry 3% of the year's run-off, and on the map page 476 of 2,980 stream cells are dry beds in mid August, against 175
in January.""",
    "g1": """The whole map. In January the northern islands and the summits are white and the south is green; in
August the south's lowlands are straw.""",
    "g2": """A southern valley at 48.6 N. Green in January; in August the slopes are straw and the
brook from the pond to the beach is a dry bed.""",
    "g3": """A northern hill at 60.3 N: under snow in February, green in July. Green is where a month is warm and
its soil wet; no plants exist.""",
    "d1": """The design asked for a lee five times drier and got two. That is a matter of scale more than of
tuning: these islands are a few km across and a front refills the air within a few km, so a rain shadow here is a
strip behind a height, not a side of an island. Places on this map differ mostly by height, latitude and season.""",
    "d2": """The reading holds under bare ground, one terrain seed and ten years. Plants will draw the soil down
further, and shade it. Years already differ: the land's rain runs from 437 to 1,045 mm over the ten.""",
    "d3": """Not built: weather on the screen (a front is a day and a half of rain in the run; the page draws mean
months), snow that cools its ground, erosion, and the sun's tilt on the page. One thing in base/'s law was noticed and
left: a year's warmth anomaly reaches a land cell twice, so the land's years differ by up to 1.85 times the sea's.""",
    "conclusion": """Partly, yes, yes. The map has a dry-summer south, a snowy north, wet heights and narrow
lees, and its 5 m ground reads as a landscape. Whether the year is seen on the page is the user's to say. The crate's
laws go to base/; the next rung, plants at metres, copies it.""",
}


def words():
    return sum(len(v.split()) for v in TEXT.values())


def t(k):
    return html.escape(" ".join(TEXT[k].split()))


def measure(k):
    name, what = t(k).split(" - ", 1)
    return f"<li><strong>{name}</strong> - {what}</li>"


def check(facts):
    """Every number the prose gives that the result files hold: stop the build if the two have parted."""
    prose = " ".join(" ".join(v.split()) for v in TEXT.values())
    for what, said in facts:
        assert said in prose, f"TEXT no longer says {said!r} ({what})"


def main():
    w = load_world()
    n, start = w["n"], w["start"]
    land, elev = w["st"]["sea"] < 0.5, w["st"]["elev"]
    reading = read_rows("results/map_reading.csv")
    prov = read_rows("results/provenance.csv")
    low_m = float(next(r["value"] for r in prov if r["what"].startswith("lowland")))
    lying = float(next(r["value"] for r in prov if r["what"].startswith("snow lies")))
    low = [r for r in reading if r["part"].startswith("lowland")]
    heights = [r for r in reading if r["part"].startswith("height")]
    isles = [r for r in reading if r["part"].startswith("island")]
    log = [r for r in read_rows("results/map_log.csv") if int(r["year"]) in w["years"]]
    ground = json.load(open(PRE + "_ground5.json"))
    count = dict(zip(ground["kinds"], ground["counts"]))
    cell2 = ground["cell_m"] ** 2 / 1e6
    flow = w["mo"]["flow"][:, land].sum(1)
    runoff = flow / flow.sum()

    f = lambda r, k: float(r[k])
    check([
        ("north to south, C", f"{f(low[0], 'temp') - f(low[-1], 'temp'):.1f} C"),
        ("the south's summer share of its rain", f"get {f(low[0], 'rain_summer') / f(low[0], 'rain'):.0%}"),
        ("the north's", f"north's {f(low[-1], 'rain_summer') / f(low[-1], 'rain'):.0%}"),
        ("the south's summer rain", f"{f(low[0], 'rain_summer'):.0f} mm in three months"),
        ("the south's fill, summer", f"{f(low[0], 'fill_summer'):.2f} of its fill"),
        ("the south's fill, winter", f"back at {f(low[0], 'fill_winter'):.2f}"),
        ("the north's fill, summer", f"stays at {f(low[-1], 'fill_summer'):.2f}"),
        ("rain on the summits", f"{f(heights[-1], 'rain'):,.0f} mm falls over 1,200 m"),
        ("the high island's driest and wettest cell", f"from {f(isles[0], 'rain_driest'):.0f} to {f(isles[0], 'rain_wettest'):,.0f} mm"),
        ("the years' rain", f"from {min(f(r, 'land_rain') for r in log):,.0f} to {max(f(r, 'land_rain') for r in log):,.0f} mm"),
        ("the 5 m land", f"{(count['land'] + count['pond'] + count['stream']) * cell2:.0f} km2 of land"),
        ("its ponds", f"{count['pond'] * cell2:.1f} km2 of ponds"),
        ("its streams", f"{count['stream'] * ground['cell_m'] / 1000:.0f} km of streams"),
        ("stream cells", f"of {count['stream']:,} stream cells"),
        ("the driest months' run-off", f"each carry {sorted(runoff)[1]:.0%}"),
        ("summer's days", f"summer is {span(start, 3, 5)}"),
    ])

    # the twelve months of each band's lowlands, as read.py parts them: four bands of 32 rows, north first
    bands = []
    for slot, lo in enumerate((96, 64, 32, 0)):
        sel = land.copy()
        sel[:lo] = False
        sel[lo + n // 4:] = False
        sel &= elev < low_m
        name = low[lo // (n // 4)]["part"].replace("lowland ", "").replace("N", " N")
        bands.append((name, sel, slot))
    by_month = lambda k: [(name, [float(v) for v in w["mo"][k][:, sel].mean(1)], slot) for name, sel, slot in bands]

    c_year = [
        month_chart("Rain by month in the lowlands, mm", "One line a band of latitude. A line that falls to zero is a dry season; a flat one is rain all year.",
                    start, by_month("rain")),
        month_chart("Soil's fill by month in the lowlands", "1 is soaked soil. A dip is ground that dries through the summer; a flat line near 1 never dries.",
                    start, by_month("fill"), ymax=1.05),
    ]
    c_place = [
        map_chart("Rain in a year, mm", "Land only, north up, the wind from the left. Pale is wet. Dashed lines part the four bands of latitude.",
                  w, w["ann"]["rain"], WATER, PowerNorm(0.5, 0, 2500), [100, 500, 1000, 2000], extend="max"),
        map_chart("Snow lying in late winter, mm of water", f"Mean pack of {span(start, 11, 11)} where it is over {lying:g} mm. Dark land is bare of snow.",
                  w, w["mo"]["snow"][11], SNOW, LogNorm(lying, 2000), [5, 50, 500, 2000], extend="max", shown=w["mo"]["snow"][11] > lying),
    ]
    c_dry = [
        map_chart("Rain of the summer quarter, mm", f"{span(start, 3, 5)}, on its own scale. Dark land had a summer with almost no rain.",
                  w, w["mo"]["rain"][3:6].sum(0), WATER, PowerNorm(0.5, 0, 450), [10, 50, 150, 300], extend="max"),
        map_chart("Soil's fill at the height of the dry season", f"Mean of {span(start, 4, 4)}. 1 is soaked soil, 0 is empty: dark is dry ground.",
                  w, w["mo"]["fill"][4], WATER, Normalize(0, 1), [0, 0.25, 0.5, 0.75, 1]),
    ]

    lowland_rows = [[r["part"].replace("lowland ", "").replace("N", " N"), f"{f(r, 'temp'):.1f}",
                     f"{f(r, 'temp_winter'):.1f} / {f(r, 'temp_summer'):.1f}", f"{f(r, 'rain'):,.0f}",
                     ", ".join(r[k] for k in ("rain_spring", "rain_summer", "rain_autumn", "rain_winter")),
                     f"{f(r, 'fill_summer'):.2f} / {f(r, 'fill_winter'):.2f}", f"{f(r, 'snow_months'):.1f}"] for r in low]
    isle_rows = [[f"{r['part'].split()[1]} km2, summit {int(r['part'].split()[4]):,} m", f"{f(r, 'rain_west'):,.0f}", r["rain_east"],
                  r["rain_driest"], f"{f(r, 'rain_wettest'):,.0f}"] for r in isles]

    month_names = [span(start, i, i) for i in range(12)]
    tables = folded("How the maps were read (results/provenance.csv)", table(["what", "value"], [[r["what"], r["value"]] for r in prov]), shown=True)
    tables += folded("By height (results/map_reading.csv)", table(
        ["land at", "cells", "mean C", "rain mm", "months of snow"],
        [[r["part"].replace("height ", ""), r["cells"], f"{f(r, 'temp'):.1f}", f"{f(r, 'rain'):,.0f}", f"{f(r, 'snow_months'):.1f}"] for r in heights]))
    for k, name, fmt in (("rain", "Rain by month, mm", "{:.0f}"), ("fill", "Soil's fill by month", "{:.2f}"),
                         ("temp", "Temperature by month, C", "{:.1f}"), ("snow", "Snow lying by month, mm of water (mean pack)", "{:.0f}")):
        series = by_month(k)
        tables += folded(f"{name}, lowlands by band", table(
            ["month"] + [s[0] for s in series], [[month_names[i]] + [fmt.format(s[1][i]) for s in series] for i in range(12)]))
    tables += folded("The land's run-off by month", table(["month", "share of the year"], [[month_names[i], f"{runoff[i]:.0%}"] for i in range(12)]))
    tables += folded("The kept years (results/map_log.csv)", table(
        ["year", "land's mean C", "land's rain mm"], [[r["year"], f"{f(r, 'land_temp'):.1f}", f"{f(r, 'land_rain'):,.0f}"] for r in log]))

    gallery = "".join([
        pair(("map_january", "21 January", "The whole map in January: white northern islands and summits, a green south"),
             ("map_august", "14 August", "The whole map in August: the south's lowlands are straw"), t("g1")),
        pair(("south_january", "21 January", "A southern valley in January: green slopes, a pond and a brook running to a beach"),
             ("south_august", "14 August", "The same valley in August: straw slopes and a dry stream bed"), t("g2")),
        pair(("north_february", "5 February", "A northern hill in February under snow"),
             ("north_july", "15 July", "The same hill in July, green"), t("g3")),
    ])

    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>e117 The Map - Report</title>
<style>{CSS}</style>
</head>
<body>
<main>
<h1>e117: does a map at an animal's size have places and a year?</h1>
<p class="sub">Experiment report - 2026-11-14 - rung 1 of #135: one run of twenty bare years on a 16 km map of islands, terrain seed 23</p>

<section class="tldr">
<h2>TL;DR</h2>
<p>{t("tldr")}</p>
</section>

<h2>1. Question</h2>
<p>{t("question")}</p>
<ol>
  <li><strong>Places.</strong> {t("h1")}</li>
  <li><strong>A walkable ground.</strong> {t("h2")}</li>
  <li><strong>A year that is seen</strong> (added 2026-11-14). {t("h3")}</li>
</ol>

<h2>2. The world</h2>
<p>{t("world")}</p>
{DIAGRAM.format(top=f"{int(isles[0]['part'].split()[4]):,}", west=isles[0]["rain_west"], east=isles[0]["rain_east"])}
<p><strong>Runs.</strong> {t("runs")}</p>
<ul class="measures">
  {measure("m1")}
  {measure("m2")}
  {measure("m3")}
  {measure("m4")}
</ul>

<h2>3. Results</h2>
{table(["lowlands at", "mean C", "winter / summer C", "rain mm", "spring, summer, autumn, winter", "soil's fill, summer / winter", "months of snow"], lowland_rows)}
{table(["island", "lowland rain west of the summit, mm", "east of it, mm", "driest cell", "wettest cell"], isle_rows)}
<ol class="verdicts">
<li><span class="verdict partly">Partly</span> {t("v1")}</li>
<li><span class="verdict">Yes</span> {t("v2")}</li>
<li><span class="verdict">Yes</span> {t("v3")}</li>
</ol>
<p>{t("gallery")}</p>

<h3>3.1 Places differ by height and latitude; a lee is a strip behind a height</h3>
<div class="grid2">
{"".join(c_place)}
</div>
<p>{t("r1")}</p>

<h3>3.2 The south has a rainless summer, the north rain in every season</h3>
<div class="grid2">
{"".join(c_year)}
</div>
<p>{t("r2")}</p>

<h3>3.3 The dry season has a place on the map</h3>
<div class="grid2">
{"".join(c_dry)}
</div>
<p>{t("r3")}</p>

<h3>3.4 On the map page, the same place twice</h3>
{gallery}

<h2>4. Discussion</h2>
<p>{t("d1")}</p>
<p>{t("d2")}</p>
<p>{t("d3")}</p>

<h2>5. Conclusion and next step</h2>
<p>{t("conclusion")}</p>

<h2>Appendix: data</h2>
<p>The tables above are <code>results/map_reading.csv</code>, written by <code>read.py</code> from the mean of years
{w["years"][0]}-{w["years"][-1]}; the maps and charts are drawn from <code>results/map_maps.bin</code> and
<code>results/map_season.bin</code> with the same bands and thresholds. The stream counts are the README's, from the map page.
The looks are the viewer's map page (<code>viewer map</code>), whose panel is in Japanese. Build this report with
<code>uv run python experiments/e117_map/report.py</code>.</p>
{tables}
</main>
</body>
</html>
"""
    out = os.path.join(HERE, "report.html")
    with open(out, "w") as fh:
        fh.write(page)
    print(f"wrote {out} ({os.path.getsize(out)//1024} KB), TEXT {words()} words")
    for k, v in TEXT.items():
        print(f"  {k}: {len(v.split())}")


if __name__ == "__main__":
    main()
