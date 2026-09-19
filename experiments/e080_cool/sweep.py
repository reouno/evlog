#!/usr/bin/env python3
"""Read e080's runs (#91 step 3): does a stand at 20-50 degrees fill in its summer when the crown takes
its share of the sun?

Run from the repo root:
`uv run python experiments/e080_cool/sweep.py [--every 10000] <dir or run prefix> ...`
"Mid" is 20-50 degrees of latitude in both hemispheres, and every season is the hemisphere's own
(summer is quarter 1 in the north and 3 in the south; the equinoxes are 0 and 2). Stand: wood 1 or more
on the cell; lawn: under 0.1. For every run:

- **the body's water** (hypothesis 1): from the censuses (every 1,000 steps from 36,000), the land's bodies
  in mid stands and on the mid lawn by season: their water, and the water paid to cool and the energy paid
  to warm a turn;
- **the stand by season** (2, 3): from `bands.csv` after the first year, bodies a mid stand cell and a mid
  lawn cell by season; summer over the equinoxes for the stands, and stand over lawn at the equinoxes;
- **the winter** (4): energy to warm a turn in mid stands in winter, and deaths by cause (second half);
- **stage C's measure** (5): kinds at a census and kinds kept to a place (e075's `sweep.read_run`);
  `--every 10000` reads only the censuses at multiples of 10,000, as e075's kept runs had them;
- **the lines**: lineages holding 5% of the land's bodies over the censuses, their bodies in mid stands
  in summer over the equinoxes; the largest ratio is printed.

Writes `results/sweep_<first dir name>.csv`.
"""
import csv
import os
import statistics as st
import sys
import tempfile
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "experiments", "e075_hunt"))
import sweep as e075  # noqa: E402  (its read_run: kinds at a census, kinds kept to a place, the log)

YEAR = 11880
N, LAT_LO, LAT_HI = 512, -59.4, 87.0
MID_N, MID_S = (20, 30, 40), (-50, -40, -30)  # bands.csv's 10-degree bands by their lower edge
LINE = 0.05
CAUSES = ("hunger", "thirst", "cold", "broken", "wound")
SEASONS = ("summer", "winter", "equinox")


def quarter(step):
    """0 and 2 are the equinoxes, 1 (the north's summer) and 3 the solstices."""
    return int(((step / YEAR + 0.125) % 1.0) * 4)


def season(q, north):
    if q in (0, 2):
        return "equinox"
    return "summer" if (q == 1) == north else "winter"


def lat_of(cell):
    return LAT_LO + (LAT_HI - LAT_LO) * (1 - abs(2 * ((cell // N) + 0.5) / N - 1))


def rows_of(path):
    with open(path) as f:
        return list(csv.DictReader(f))


def cls(crown):
    return "stand" if crown >= 1 else "lawn" if crown < 0.1 else "thin"


def bands(pre):
    """Bodies a cell in mid stands and on the mid lawn by season, after the first year."""
    acc = defaultdict(lambda: [0.0, 0.0])  # (class, season) -> bodies, cells
    for r in rows_of(pre + "_bands.csv"):
        s, lat = int(r["step"]), int(r["lat"])
        if s <= 12000 or lat not in MID_N + MID_S:
            continue
        c = {"0": "lawn", "2": "stand"}.get(r["wood_class"])
        if c is None:
            continue
        v = acc[(c, season(quarter(s - 500), lat >= 0))]
        v[0] += float(r["bodies"])
        v[1] += float(r["cells"])
    per = {k: v[0] / v[1] if v[1] else float("nan") for k, v in acc.items()}
    out = {f"{c}_{se}": per.get((c, se), float("nan")) for c in ("stand", "lawn") for se in SEASONS}
    out["stand_SE"] = out["stand_summer"] / out["stand_equinox"]
    out["stand_WE"] = out["stand_winter"] / out["stand_equinox"]
    out["home"] = out["stand_equinox"] / out["lawn_equinox"]  # over 1: the stand is the richer place at the equinoxes
    return out


def census(pre):
    """From the censuses: the land's bodies in mid stands and on the mid lawn by season, and the lines."""
    acc = defaultdict(lambda: [0, 0.0, 0.0, 0.0])  # (class, season) -> bodies, water, cooled/turn, warmed/turn
    per = defaultdict(lambda: defaultdict(lambda: [defaultdict(int), 0]))  # step -> lineage -> (season -> in mid stands), all
    with open(pre + "_agents.csv") as f:
        for r in csv.DictReader(f):
            if r["medium"] != "0":
                continue
            s, lat = int(r["step"]), lat_of(int(r["cell"]))
            c = cls(float(r["crown"]))
            mid = 20 <= abs(lat) < 50
            se = season(quarter(s), lat >= 0)
            line = per[s][r["lineage"]]
            line[1] += 1
            if not mid:
                continue
            if c == "stand":
                line[0][se] += 1
            v = acc[(c, se)]
            turns = max(1, int(r["turns"]))
            v[0] += 1
            v[1] += float(r["water"])
            v[2] += float(r["cooled"]) / turns
            v[3] += float(r["warmed"]) / turns
    out = {}
    for c in ("stand", "lawn"):
        for se in SEASONS:
            v = acc[(c, se)]
            n = max(v[0], 1)
            out[f"n_{c}_{se}"] = v[0]
            out[f"water_{c}_{se}"] = v[1] / n if v[0] else float("nan")
            out[f"cool_{c}_{se}"] = v[2] / n if v[0] else float("nan")
            out[f"warm_{c}_{se}"] = v[3] / n if v[0] else float("nan")
    # Lines: 5% of the land's bodies over every census; mid stands in summer over the equinoxes, per census.
    held = defaultdict(int)
    for by in per.values():
        for k, v in by.items():
            held[k] += v[1]
    land = sum(held.values())
    big = [k for k, n in held.items() if n >= LINE * land]
    # censuses a season: the equinoxes are two quarters for both hemispheres, a summer one quarter each
    n_q = [sum(1 for s in per if quarter(s) == q) for q in range(4)]
    n_se = {"summer": (n_q[1] + n_q[3]) / 2, "equinox": n_q[0] + n_q[2]}
    ratios = []
    for k in big:
        tot = defaultdict(int)
        for by in per.values():
            if k in by:
                for se, n in by[k][0].items():
                    tot[se] += n
        eq = tot["equinox"] / max(n_se["equinox"], 1)
        ratios.append((k, (tot["summer"] / max(n_se["summer"], 1)) / eq if eq else float("nan")))
    ratios.sort(key=lambda t: -(t[1] if t[1] == t[1] else 0))
    out["lines"] = len(big)
    out["line"], out["line_SE"] = ratios[0] if ratios else ("-", float("nan"))
    return out


def filtered(pre, every, tmp):
    """A copy of the run with only the censuses at multiples of `every` (and the log and row linked)."""
    base = os.path.join(tmp, os.path.basename(pre))
    with open(pre + "_agents.csv") as f, open(base + "_agents.csv", "w") as g:
        g.write(f.readline())
        for line in f:
            if int(line[: line.index(",")]) % every == 0:
                g.write(line)
    for part in ("_log.csv", "_row.csv"):
        os.symlink(os.path.abspath(pre + part), base + part)
    return base


def log_extra(pre):
    rows = rows_of(pre + "_log.csv")
    half = [r for r in rows if int(r["step"]) >= int(rows[-1]["step"]) / 2]
    deaths = {c: sum(float(r.get(f"deaths_{c}", 0)) for r in half) for c in CAUSES}
    total = max(sum(deaths.values()), 1)
    out = {f"d_{c}": deaths[c] / total for c in CAUSES}
    out["pop_land"] = st.mean(float(r["pop_land"]) for r in half)
    return out


def prefixes(arg):
    if os.path.isdir(arg):
        return sorted(os.path.join(arg, f[: -len("_agents.csv")]) for f in os.listdir(arg) if f.endswith("_agents.csv"))
    return [arg]


def main():
    args = sys.argv[1:]
    every = 0
    if args and args[0] == "--every":
        every, args = int(args[1]), args[2:]
    rows = []
    for arg in args:
        for pre in prefixes(arg):
            name = os.path.basename(pre).replace("c1225_", "")
            if "e078" in pre:
                name = "e078 " + name
            with open(pre + "_row.csv") as f:
                row = next(csv.DictReader(f))
            out = {"run": name, "c3": float(row.get("crown_cool", 0)), "wet": float(row.get("crown_wet", 0)), "rest": float(row.get("wood_rest", 0))}
            with tempfile.TemporaryDirectory() as tmp:
                src = filtered(pre, every, tmp) if every else pre
                kinds_row, _ = e075.read_run(name, src)
            out.update({"kinds_at": kinds_row["kinds_at"], "placed_at": kinds_row["placed_at"], "kills": kinds_row["kills"], "pop": kinds_row["pop"]})
            out.update(log_extra(pre))
            out.update(bands(pre))
            out.update(census(pre))
            rows.append(out)
    print(f"{'run':>16} {'c3':>4} {'kinds':>5} {'place':>5} {'land':>5} {'thirst':>6} {'cold':>5}"
          f" {'water S/W/E stand':>18} {'lawn':>15} {'cool S st/lw':>13} {'warm W st/lw':>13}"
          f" {'stand/cell S/W/E':>17} {'lawn/cell S/W/E':>17} {'S/E':>5} {'home':>5} {'lineS/E':>7}")
    for r in rows:
        print(f"{r['run']:>16} {r['c3']:>4g} {r['kinds_at']:>5.2f} {r['placed_at']:>5.2f} {r['pop_land']:>5.0f} {r['d_thirst']:>6.1%} {r['d_cold']:>5.1%}"
              f"   {r['water_stand_summer']:.2f}/{r['water_stand_winter']:.2f}/{r['water_stand_equinox']:.2f}"
              f"  {r['water_lawn_summer']:.2f}/{r['water_lawn_winter']:.2f}/{r['water_lawn_equinox']:.2f}"
              f"  {r['cool_stand_summer']:.4f}/{r['cool_lawn_summer']:.4f} {r['warm_stand_winter']:.4f}/{r['warm_lawn_winter']:.4f}"
              f"  {r['stand_summer']:.3f}/{r['stand_winter']:.3f}/{r['stand_equinox']:.3f}"
              f"  {r['lawn_summer']:.3f}/{r['lawn_winter']:.3f}/{r['lawn_equinox']:.3f}"
              f" {r['stand_SE']:>5.2f} {r['home']:>5.2f} {r['line_SE']:>7.2f}")
    first = args[0] if os.path.isdir(args[0]) else os.path.dirname(args[0])
    dst = os.path.join(HERE, "results", f"sweep_{os.path.basename(os.path.normpath(first))}{'_' + str(every) if every else ''}.csv")
    with open(dst, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(f"-> {dst}")


if __name__ == "__main__":
    main()
