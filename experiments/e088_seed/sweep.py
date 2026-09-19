#!/usr/bin/env python3
"""Read e088's runs of the producers alone (#99 S): the seed bank by place and season, the spring's grass
from seed, and stage B's pass line.

Run from the repo root: `uv run python experiments/e088_seed/sweep.py`
Reads `results/alone/c1225_life9_s<share>_{log,bands}.csv`. A bands row covers the 1,000 steps before its
step; its quarter is that of its middle (0 the north's spring, 1 its summer, 2 its autumn, 3 its winter;
the run starts on a whole year). Prints, for every run:

- **the land**: grass (leaf) and seed standing, a land cell's mean over the run, against the control;
  seed set and sprouted a step;
- **stage B**: each producer's share of the standing matter (grass with its seed), its least total over the
  run, the land burnt a year and the ledger's worst drift;
- **by band and quarter** (land): seed / grass standing, and the sprouted share of the grass added
  (sprouted / (grown as leaf + sprouted)).

Writes `results/sweep.csv` (one row a run) and `results/sweep_bands.csv` (run x band x quarter).
"""
import csv
import os

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results", "alone")
YEAR = 11880
RUNS = ["s0", "s0.1", "s0.2", "s0.4"]
LAND = 110625


def rows(path):
    with open(path) as f:
        return list(csv.DictReader(f))


def quarter(step):
    return int(((step - 500) / YEAR + 0.125) % 1.0 * 4) % 4


def main():
    out, bands_out = [], []
    ctrl = None
    for run in RUNS:
        pre = os.path.join(RES, f"c1225_life9_{run}")
        log = rows(pre + "_log.csv")
        n = len(log)
        mean = lambda k: sum(float(r[k]) for r in log) / n
        grass, seed = mean("grass") / LAND, mean("seed") / LAND
        wood, algae = mean("wood"), mean("algae")
        standing = mean("grass") + mean("seed") + wood + algae
        years = int(log[-1]["step"]) / YEAR
        row = {
            "run": run,
            "grass": grass,
            "seed": seed,
            "seed_per_grass": seed / grass,
            "seed_set": mean("seed_set"),
            "sprouted": mean("sprouted"),
            "share_grass": (mean("grass") + mean("seed")) / standing,
            "share_wood": wood / standing,
            "share_algae": algae / standing,
            "min_grass": min(float(r["grass"]) for r in log),
            "min_wood": min(float(r["wood"]) for r in log),
            "min_algae": min(float(r["algae"]) for r in log),
            "burnt_a_year": sum(float(r["burnt"]) for r in log) / years,  # the log's burnt is a share of the land
            "matter_err": max(abs(float(r["matter_err"])) for r in log),
        }
        if ctrl is None:
            ctrl = row
        row["grass_vs_ctrl"] = grass / ctrl["grass"]
        row["with_seed_vs_ctrl"] = (grass + seed) / ctrl["grass"]
        out.append(row)

        acc = {}
        for r in rows(pre + "_bands.csv"):
            k = (int(r["lat"]), quarter(int(r["step"])))
            a = acc.setdefault(k, [0.0] * 6)
            a[0] += float(r["grass"])
            a[1] += float(r["seed"])
            a[2] += float(r["grown"])
            a[3] += float(r["sprouted"])
            a[4] += 1
            a[5] += float(r["cells"])
        for (lat, q), a in sorted(acc.items()):
            bands_out.append({
                "run": run, "lat": lat, "quarter": q,
                "grass": a[0] / a[5], "seed": a[1] / a[5],  # a land cell's, mean over the quarter's rows
                "seed_per_grass": a[1] / a[0] if a[0] > 0 else 0.0,
                "sprout_share": a[3] / (a[2] + a[3]) if a[2] + a[3] > 0 else 0.0,
            })

    for row in out:
        print(f"{row['run']:5} grass {row['grass']:.3f} ({row['grass_vs_ctrl']:.2f}; with seed {row['with_seed_vs_ctrl']:.2f}) "
              f"seed {row['seed']:.3f} ({row['seed_per_grass']:.2f} of grass), set {row['seed_set']:.1f} sprouted {row['sprouted']:.1f} a step")
        print(f"      shares grass {row['share_grass']:.3f} wood {row['share_wood']:.3f} algae {row['share_algae']:.3f}; "
              f"least {row['min_grass']:.0f}/{row['min_wood']:.0f}/{row['min_algae']:.0f}; burnt {row['burnt_a_year']:.3f} of the land a year; "
              f"matter err {row['matter_err']:.1e}")
    print("\nseed | grass a land cell, by band and quarter (s0.2; s0's grass after the slash)")
    for lat in sorted({b["lat"] for b in bands_out}):
        cells = sorted([b for b in bands_out if b["run"] == "s0.2" and b["lat"] == lat], key=lambda b: b["quarter"])
        c0 = sorted([b for b in bands_out if b["run"] == "s0" and b["lat"] == lat], key=lambda b: b["quarter"])
        print(f"  {lat:+4d}  " + "  ".join(f"{b['seed']:5.2f}|{b['grass']:4.2f}/{c['grass']:4.2f}" for b, c in zip(cells, c0)))
    names = ["N spring", "N summer", "N autumn", "N winter"]
    for run in RUNS[1:]:
        print(f"\n{run}: seed/grass | sprouted share of grass added, by band (rows) and quarter ({', '.join(names)})")
        for lat in sorted({b["lat"] for b in bands_out}):
            cells = [b for b in bands_out if b["run"] == run and b["lat"] == lat]
            cells.sort(key=lambda b: b["quarter"])
            print(f"  {lat:+4d}  " + "  ".join(f"{b['seed_per_grass']:5.2f}|{b['sprout_share']:4.2f}" for b in cells))

    def write(name, data):
        with open(os.path.join(HERE, "results", name), "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(data[0].keys()))
            w.writeheader()
            for d in data:
                w.writerow({k: (f"{v:.5g}" if isinstance(v, float) else v) for k, v in d.items()})

    write("sweep.csv", out)
    write("sweep_bands.csv", bands_out)


if __name__ == "__main__":
    main()
