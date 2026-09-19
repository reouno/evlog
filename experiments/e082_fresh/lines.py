#!/usr/bin/env python3
"""Where the leading line lives: its share of the land's bodies in each 10-degree band (e082, #95).

For each ladder run (e081's control and fresh 0.05, e082's fresh 0.2; seeds 9-11), the land's bodies of
every census are pooled, the lineage with the most is the leading line, and its share of each band's
bodies is written out. Bands holding under 3% of the bodies are left out.

Run from the repo root: `uv run python experiments/e082_fresh/lines.py`
Writes `results/top_by_band.csv` (run, seed, band's lower edge in degrees, share, bodies).
"""
import csv
import os
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
EXP = os.path.dirname(HERE)
N, LAT_LO, LAT_HI = 512, -59.4, 87.0
RUNS = {"control": "e081_drink/results/ladder/c1225_life{s}_u0",
        "fresh 0.05": "e081_drink/results/ladder/c1225_life{s}_u9.4",
        "fresh 0.2": "e082_fresh/results/ladder/c1225_life{s}_u9.4_f0.2"}


def lat_of(cell):
    return LAT_LO + (LAT_HI - LAT_LO) * (1 - abs(2 * ((cell // N) + 0.5) / N - 1))


def main():
    out = []
    for run, pat in RUNS.items():
        for s in (9, 10, 11):
            lines, bands = Counter(), defaultdict(Counter)
            with open(os.path.join(EXP, pat.format(s=s) + "_agents.csv")) as f:
                for r in csv.DictReader(f):
                    if r["medium"] != "0":
                        continue
                    b = int(lat_of(int(r["cell"])) // 10 * 10)
                    lines[r["lineage"]] += 1
                    bands[b][r["lineage"]] += 1
            top = lines.most_common(1)[0][0]
            total = sum(lines.values())
            for b in sorted(bands):
                n = sum(bands[b].values())
                if n >= 0.03 * total:
                    out.append({"run": run, "seed": s, "band": b, "share": bands[b][top] / n, "bodies": n})
            print(run, s, " ".join(f"{r['band']}:{r['share']:.0%}" for r in out if r["run"] == run and r["seed"] == s))
    dst = os.path.join(HERE, "results", "top_by_band.csv")
    with open(dst, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0]))
        w.writeheader()
        w.writerows(out)
    print(f"-> {dst}")


if __name__ == "__main__":
    main()
