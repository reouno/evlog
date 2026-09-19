#!/usr/bin/env python3
"""Read e082's runs (#95) beside e081's: under W1, does wet ground that gives more of a pool's drink loosen
the tether? e081's reading (below) with `fresh` added as a column.

Run from the repo root:
`uv run python experiments/e082_fresh/sweep.py [--every 10000] <dir or run prefix> ...`
"Mid" is 20-50 degrees of latitude in both hemispheres, and every season is the hemisphere's own
(the north's spring is quarter 0, its summer 1, its autumn 2; the south's the other way round).
Stand: wood 1 or more on the cell; lawn: under 0.1. For every run (e080's reading, by four seasons):

- **the land empties?** the land's bodies and thirst's share of deaths over the second half;
- **the home holds?** bodies a mid stand cell over a mid lawn cell at the equinoxes (`bands.csv`, after
  the first year), and the water of the land's bodies in mid stands (the censuses from 36,000);
- **the lawn in autumn**: bodies a mid lawn cell over a mid stand cell in autumn (e080's control 0.40
  for the equinoxes' autumn half);
- **the ground under the crowd**: the ground's fill in mid stands and on the mid lawn by season, against
  the control (the producers alone: at unit 0 no body touches the water);
- **the lines and kinds**: kinds at a census and kinds kept to a place (e075's `sweep.read_run`), the
  largest lineage's share of the land's bodies over the censuses, travel;
- **the water's flows** (mm a step over the world, second half): drunk, to the air, sweated, and the
  ledger's largest error.

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
SEASONS = ("spring", "summer", "autumn", "winter")


def quarter(step):
    """0 and 2 are the equinoxes, 1 (the north's summer) and 3 the solstices."""
    return int(((step / YEAR + 0.125) % 1.0) * 4)


def season(q, north):
    return SEASONS[q if north else (q + 2) % 4]


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
    fill = defaultdict(lambda: [0.0, 0.0])  # (class, season) -> the ground's fill x cells, cells
    for r in rows_of(pre + "_bands.csv"):
        s, lat = int(r["step"]), int(r["lat"])
        if s <= 12000 or lat not in MID_N + MID_S:
            continue
        c = {"0": "lawn", "2": "stand"}.get(r["wood_class"])
        if c is None:
            continue
        se = season(quarter(s - 500), lat >= 0)
        v = acc[(c, se)]
        v[0] += float(r["bodies"])
        v[1] += float(r["cells"])
        f = fill[(c, se)]
        f[0] += float(r["fill"]) * float(r["cells"])
        f[1] += float(r["cells"])
    per = {k: v[0] / v[1] if v[1] else float("nan") for k, v in acc.items()}
    out = {f"{c}_{se}": per.get((c, se), float("nan")) for c in ("stand", "lawn") for se in SEASONS}
    out.update({f"fill_{c}_{se}": fill[(c, se)][0] / max(fill[(c, se)][1], 1) for c in ("stand", "lawn") for se in SEASONS})
    eq = lambda c: (acc[(c, "spring")][0] + acc[(c, "autumn")][0]) / max(acc[(c, "spring")][1] + acc[(c, "autumn")][1], 1)
    out["home"] = eq("stand") / eq("lawn")  # over 1: the stand is the richer place at the equinoxes
    out["lawn_autumn_share"] = out["lawn_autumn"] / out["stand_autumn"]
    out["lawn_spring_share"] = out["lawn_spring"] / out["stand_spring"]
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
    out["lines"] = len(big)
    out["top_share"] = st.mean(max(v[1] for v in by.values()) / sum(v[1] for v in by.values()) for by in per.values())
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
    for c in ("drunk", "air", "sweat"):
        out[f"w_{c}"] = st.mean(float(r.get(f"water_{c}", 0)) for r in half)
    out["born_dry"] = sum(float(r.get("born_dry", 0)) for r in half) / max(sum(float(r["births"]) for r in half), 1)
    out["w_err"] = max(float(r.get("water_err", 0)) for r in rows)
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
            out = {"run": name, "unit": float(row.get("unit", 0)), "fresh": float(row["fresh"])}
            with tempfile.TemporaryDirectory() as tmp:
                src = filtered(pre, every, tmp) if every else pre
                kinds_row, _ = e075.read_run(name, src)
            out.update({k: kinds_row[k] for k in ("kinds_at", "placed_at", "kills", "pop", "travel")})
            out.update(log_extra(pre))
            out.update(bands(pre))
            out.update(census(pre))
            rows.append(out)
    print(f"{'run':>14} {'unit':>5} {'fresh':>5} {'land':>5} {'thirst':>6} {'home':>5} {'lawn/st aut':>11} {'spr':>5}"
          f" {'water st Sp/S/A/W':>20} {'lawn':>20} {'fill st Sp/S/A/W':>20} {'lawn':>20}"
          f" {'top':>5} {'kinds':>5} {'place':>5} {'trav':>5} {'drunk':>6} {'air':>6} {'sweat':>6} {'bdry':>5} {'err':>7}")
    for r in rows:
        four = lambda key: "/".join(f"{r[f'{key}_{se}']:.2f}" for se in SEASONS)
        print(f"{r['run']:>14} {r['unit']:>5g} {r['fresh']:>5g} {r['pop_land']:>5.0f} {r['d_thirst']:>6.1%} {r['home']:>5.2f} {r['lawn_autumn_share']:>11.2f} {r['lawn_spring_share']:>5.2f}"
              f" {four('water_stand'):>20} {four('water_lawn'):>20} {four('fill_stand'):>20} {four('fill_lawn'):>20}"
              f" {r['top_share']:>5.0%} {r['kinds_at']:>5.2f} {r['placed_at']:>5.2f} {float(r['travel']):>5.1f}"
              f" {r['w_drunk']:>6.1f} {r['w_air']:>6.1f} {r['w_sweat']:>6.1f} {r['born_dry']:>5.1%} {r['w_err']:>7.1e}")
    first = args[0] if os.path.isdir(args[0]) else os.path.dirname(args[0])
    dst = os.path.join(HERE, "results", f"sweep_{os.path.basename(os.path.normpath(first))}{'_' + str(every) if every else ''}.csv")
    with open(dst, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(f"-> {dst}")


if __name__ == "__main__":
    main()
