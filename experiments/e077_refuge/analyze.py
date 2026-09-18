"""#91 step 0: e077's instrumented runs. Where and when the season takes the lawn, and who stands in a stand."""
import csv, sys
from collections import defaultdict
from pathlib import Path

RES = Path(__file__).parent / "results"
YEAR = 11880
SEEDS = [9, 10, 11]
FROM = 12000  # past the first year
CLASS = ["lawn", "thin", "stand"]
QN = ["q0 (ph 0)", "q1 (ph .25)", "q2 (ph .5)", "q3 (ph .75)"]

def quarter(mid):
    return int(((mid / YEAR + 0.125) % 1.0) * 4)

def bands(seed):
    with open(RES / f"c1225_life{seed}_year_bands.csv") as f:
        return list(csv.DictReader(f))

def main():
    # grown per cell and bodies, by (lat, class, quarter), seeds pooled
    g = defaultdict(lambda: [0.0, 0.0, 0.0, 0])  # grown, cells, bodies, rows
    for seed in SEEDS:
        for r in bands(seed):
            s = int(r["step"])
            if s <= FROM:
                continue
            k = (int(r["lat"]), int(r["wood_class"]), quarter(s - 500))
            v = g[k]
            v[0] += float(r["grown"]); v[1] += float(r["cells"]); v[2] += float(r["bodies"]); v[3] += 1
    lats = sorted({k[0] for k in g})
    print("grass grown a lawn cell per 1,000 steps by quarter (seeds pooled); bodies on the lawn and in the stands")
    print(f"{'lat':>4} {'cells':>6}" + "".join(f"{q:>12}" for q in QN) + "  worst/best   bodies lawn by quarter        bodies in stands by quarter")
    tot = [[0.0] * 4 for _ in range(3)]; totb = [[0.0] * 4 for _ in range(3)]
    for lat in lats:
        row = []
        for q in range(4):
            v = g.get((lat, 0, q))
            row.append(v[0] / v[1] if v and v[1] else float("nan"))
        cells = g[(lat, 0, 0)][1] / max(1, g[(lat, 0, 0)][3]) if (lat, 0, 0) in g else 0
        bl = [g[(lat, 0, q)][2] / g[(lat, 0, q)][3] if (lat, 0, q) in g else 0 for q in range(4)]
        bs = [g[(lat, 2, q)][2] / g[(lat, 2, q)][3] if (lat, 2, q) in g else 0 for q in range(4)]
        ok = [x for x in row if x == x]
        print(f"{lat:>4} {cells:6.0f}" + "".join(f"{x:12.3f}" for x in row) + f"  {min(ok) / max(ok) if ok and max(ok) > 0 else float('nan'):9.2f}   "
              + " ".join(f"{x:6.0f}" for x in bl) + "   " + " ".join(f"{x:6.0f}" for x in bs))
    for c in range(3):
        for q in range(4):
            gr = sum(v[0] for k, v in g.items() if k[1] == c and k[2] == q)
            n = sum(v[3] for k, v in g.items() if k[1] == c and k[2] == q and k[0] == lats[0]) or 1
            tot[c][q] = gr
            totb[c][q] = sum(v[2] for k, v in g.items() if k[1] == c and k[2] == q)
    print("\nthe whole land by class: grass grown, and bodies, summed over rows, by quarter")
    for c in range(3):
        print(f"{CLASS[c]:>6} grown " + " ".join(f"{x:10.0f}" for x in tot[c]) + f"  worst/best {min(tot[c]) / max(tot[c]):.2f}   bodies " + " ".join(f"{x:9.0f}" for x in totb[c]))

    # the census: share of land bodies in a stand, by phase
    print("\ncensus every 1,000 steps from 36,000: land bodies, and the share on thin wood and in a stand")
    for seed in SEEDS:
        by = defaultdict(lambda: [0, 0, 0])
        with open(RES / f"c1225_life{seed}_year_agents.csv") as f:
            for r in csv.DictReader(f):
                if r["medium"] != "0":
                    continue
                w = float(r["crown"])
                by[int(r["step"])][0 if w < 0.1 else 1 if w < 1 else 2] += 1
        line = []
        for s in sorted(by):
            n = sum(by[s])
            line.append(f"{(s / YEAR) % 1:.2f}:{n}/{by[s][1] / n:.2f}/{by[s][2] / n:.2f}")
        print(f"seed {seed}: " + "  ".join(line))

main()
