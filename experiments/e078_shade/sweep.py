#!/usr/bin/env python3
"""Read e078's runs (#91 step 1): what the crown's shade kept, where and when.

Run from the repo root: `uv run python experiments/e078_shade/sweep.py [--every 10000] <dir> ...`
For every run in the directories given it prints the two rates and:

- **the heat under the crown** (hypothesis 1): in each band of 10-30 degrees (both hemispheres), in
  the quarter where its lawn is hottest, the degrees over 30 C a body's heat reads in a stand and on
  the lawn (`over`), pooled over the bands; the rows after the first year.
- **the stand by season** (2, 3): the land's bodies in stands and on the whole land, solstices
  (quarters centred on phase 0.25 and 0.75) over equinoxes (0 and 0.5).
- **the lines** (4): at the census (every 1,000 steps from 36,000), the lineages holding 5% of the
  land's bodies over all the censuses together; for each, its bodies in stands and on the mid-latitude lawn (20 degrees and out,
  wood under 0.1), solstices over equinoxes. The line with the largest stand ratio is printed.
- **stage C's measure** (5): kinds at a census and kinds kept to a place, e075's `sweep.read_run`
  (e068's census by birth form). `--every 10000` reads only the censuses at multiples of 10,000, as
  e075's kept runs had them.

Writes `results/sweep_<dir name>.csv`.
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
EDGE = (-30, -20, 10, 20)  # bands of 10-30 degrees, by their lower edge
LINE = 0.05  # a lineage's share of the land's bodies at a census to be read as a line
CAUSES = ("hunger", "thirst", "cold", "broken", "wound")


def quarter(step):
    """0 and 2 are the equinoxes, 1 (the north's summer) and 3 the solstices."""
    return int(((step / YEAR + 0.125) % 1.0) * 4)


def lat_of(cell):
    return LAT_LO + (LAT_HI - LAT_LO) * (1 - abs(2 * ((cell // N) + 0.5) / N - 1))


def rows_of(path):
    with open(path) as f:
        return list(csv.DictReader(f))


def ratio(by_q):
    eq = by_q[0] + by_q[2]
    return (by_q[1] + by_q[3]) / eq if eq else float("nan")


def bands(pre):
    """Heat under the crown in the hot quarter, and the stand's bodies by season."""
    acc = defaultdict(lambda: [0.0, 0.0, 0])  # (lat, class, quarter) -> over, bodies, rows
    for r in rows_of(pre + "_bands.csv"):
        s = int(r["step"])
        if s <= 12000:
            continue
        v = acc[(int(r["lat"]), int(r["wood_class"]), quarter(s - 500))]
        v[0] += float(r.get("over", "nan"))
        v[1] += float(r["bodies"])
        v[2] += 1
    mean = lambda k: acc[k][0] / acc[k][2] if acc[k][2] else float("nan")  # noqa: E731
    stand, lawn = [], []
    for lat in EDGE:
        hot = max(range(4), key=lambda q: mean((lat, 0, q)))
        stand.append(mean((lat, 2, hot)))
        lawn.append(mean((lat, 0, hot)))
    by_q = lambda cls: [sum(v[1] for k, v in acc.items() if k[2] == q and k[1] in cls) for q in range(4)]  # noqa: E731
    return {"over_stand": st.mean(stand), "over_lawn": st.mean(lawn),
            "stand_ratio": ratio(by_q({2})), "land_ratio": ratio(by_q({0, 1, 2})),
            "stand_q": "/".join(f"{x / 1000:.0f}k" for x in by_q({2}))}


def lines(pre):
    """The lineages holding 5% of the land's bodies at a census: stand and mid-latitude lawn by season."""
    per = defaultdict(lambda: defaultdict(lambda: [[0] * 4, [0] * 4, 0]))  # step -> lineage -> stand, lawn, all
    with open(pre + "_agents.csv") as f:
        for r in csv.DictReader(f):
            if r["medium"] != "0":
                continue
            s, crown = int(r["step"]), float(r["crown"])
            v = per[s][r["lineage"]]
            q = quarter(s)
            v[0][q] += crown >= 1
            v[1][q] += crown < 0.1 and abs(lat_of(int(r["cell"]))) >= 20
            v[2] += 1
    # A line holds 5% of the land's bodies averaged over every census, so that one alive in a single
    # quarter is not read as following the season.
    held = defaultdict(int)
    for by in per.values():
        for k, v in by.items():
            held[k] += v[2]
    land = sum(held.values())
    big = {k for k, n in held.items() if n >= LINE * land}
    out = []
    for k in big:
        stand, lawn = [0] * 4, [0] * 4
        for by in per.values():
            if k in by:
                stand = [a + b for a, b in zip(stand, by[k][0])]
                lawn = [a + b for a, b in zip(lawn, by[k][1])]
        n_q = [sum(1 for s in per if quarter(s) == q) for q in range(4)]  # censuses a quarter
        stand = [x / max(n, 1) for x, n in zip(stand, n_q)]
        lawn = [x / max(n, 1) for x, n in zip(lawn, n_q)]
        out.append((k, ratio(stand), ratio(lawn), stand, lawn))
    out.sort(key=lambda t: -(t[1] if t[1] == t[1] else 0))
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


def main():
    args = sys.argv[1:]
    every = 0
    if args and args[0] == "--every":
        every, args = int(args[1]), args[2:]
    for d in args:
        pres = sorted(os.path.join(d, f[: -len("_agents.csv")]) for f in os.listdir(d) if f.endswith("_agents.csv"))
        rows = []
        for pre in pres:
            name = os.path.basename(pre).replace("c1225_", "")
            with open(pre + "_row.csv") as f:
                row = next(csv.DictReader(f))
            out = {"run": name, "k": float(row.get("shade_heat", 0)), "k2": float(row.get("shade_dry", 0))}
            with tempfile.TemporaryDirectory() as tmp:
                src = filtered(pre, every, tmp) if every else pre
                kinds_row, _ = e075.read_run(name, src)
            out.update({"kinds_at": kinds_row["kinds_at"], "placed_at": kinds_row["placed_at"], "kills": kinds_row["kills"],
                        "pop": kinds_row["pop"]})
            out.update(log_extra(pre))
            out.update(bands(pre))
            ls = lines(pre)
            top = ls[0] if ls else ("-", float("nan"), float("nan"), [0] * 4, [0] * 4)
            out.update({"lines": len(ls), "line": top[0], "line_stand": top[1], "line_lawn": top[2],
                        "line_stand_q": "/".join(f"{x:.0f}" for x in top[3]), "line_lawn_q": "/".join(f"{x:.0f}" for x in top[4])})
            rows.append(out)
        print(f"\n{d}")
        print(f"{'run':>18} {'k':>4} {'k2':>4} {'kinds':>5} {'place':>5} {'kills':>6} {'pop':>6} {'land':>5} {'thirst':>6} {'cold':>5} {'hungr':>5}"
              f" {'overS':>5} {'overL':>5} {'standS/E':>8} {'landS/E':>7} {'stand by quarter':>18} {'lines':>5} {'lineS/E':>7} {'lawnS/E':>7}  line stand/lawn by quarter")
        for r in rows:
            print(f"{r['run']:>18} {r['k']:>4g} {r['k2']:>4g} {r['kinds_at']:>5.2f} {r['placed_at']:>5.2f} {r['kills']:>6.1%} {r['pop']:>6.0f} {r['pop_land']:>5.0f}"
                  f" {r['d_thirst']:>6.1%} {r['d_cold']:>5.1%} {r['d_hunger']:>5.1%} {r['over_stand']:>5.2f} {r['over_lawn']:>5.2f}"
                  f" {r['stand_ratio']:>8.2f} {r['land_ratio']:>7.2f} {r['stand_q']:>18} {r['lines']:>5} {r['line_stand']:>7.2f} {r['line_lawn']:>7.2f}"
                  f"  {r['line_stand_q']} | {r['line_lawn_q']}")
        out = os.path.join(HERE, "results", f"sweep_{os.path.basename(os.path.normpath(d))}{'_' + str(every) if every else ''}.csv")
        with open(out, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0]))
            w.writeheader()
            w.writerows(rows)
        print(f"-> {out}")


if __name__ == "__main__":
    main()
