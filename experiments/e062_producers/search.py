"""The worlds and candidates of e062's search (#75, stage B).

Writes results/worlds/c<seed>.params, the climate of each chosen stage-A world (e061's row, the
climate's keys only), and results/search/candidates.txt, one run per line, for
    xargs -P 10 -L 1 ./target/release/e062_producers < candidates.txt
The same draws of the producers' axes run on every world, so a draw can be judged across worlds.
Run from the repo root: uv run python experiments/e062_producers/search.py [draws]
"""
import csv
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
STAGE_A = os.path.join(HERE, "..", "e061_climate", "results", "search")

# Six of e061's 30 passing worlds at 512, chosen to span the climates of the land
# (mean temperature C / rain mm a year): hot and wet, hot and dry, warm and very wet, mild,
# cool, cold.
WORLDS = [1182, 1173, 1225, 1221, 1236, 1208]
CLIMATE = ["size", "seed", "year", "day", "tick", "land", "relief", "grain", "rough", "lat_lo", "lat_hi",
           "tilt", "night", "gain", "lapse", "land_rate", "sea_rate", "spread", "wind", "wind_dir",
           "wind_turn", "evap", "rain", "flow", "soil"]

# name: (low, high, log). A decade around each default.
AXES = {
    "grass_rate": (0.002, 0.02, True),
    "wood_rate": (0.0008, 0.008, True),
    "algae_rate": (0.003, 0.03, True),
    "ignite": (1e-8, 1e-5, True),
}


def lhs(n, rng):
    """n points, each axis cut into n strata, one point in each, strata shuffled per axis."""
    cols = {}
    for name, (lo, hi, log) in AXES.items():
        us = [(i + rng.random()) / n for i in range(n)]
        rng.shuffle(us)
        if log:
            cols[name] = [math.exp(math.log(lo) + u * (math.log(hi) - math.log(lo))) for u in us]
        else:
            cols[name] = [lo + u * (hi - lo) for u in us]
    return [{k: cols[k][i] for k in AXES} for i in range(n)]


def write_worlds():
    out = os.path.join(HERE, "results", "worlds")
    os.makedirs(out, exist_ok=True)
    for s in WORLDS:
        with open(os.path.join(STAGE_A, f"c{s}_row.csv")) as f:
            row = next(csv.DictReader(f))
        assert row["pass"] == "1", f"c{s} did not pass stage A"
        with open(os.path.join(out, f"c{s}.params"), "w") as f:
            f.write(f"# e061 candidate c{s}: land {row['land_temp']} C, rain on land {row['rain_land']} mm a year\n")
            for k in CLIMATE:
                f.write(f"{k}={row[k]}\n")


def main():
    draws = int(sys.argv[1]) if len(sys.argv) > 1 else 16
    write_worlds()
    rng = random.Random(62)
    out = os.path.join(HERE, "results", "search")
    os.makedirs(out, exist_ok=True)
    lines = []
    for i, c in enumerate(lhs(draws, rng)):
        kv = " ".join(f"{k}={v:.4g}" for k, v in c.items())
        for s in WORLDS:
            prefix = f"experiments/e062_producers/results/search/c{s}_d{i:02d}"
            lines.append(f"{prefix} experiments/e062_producers/results/worlds/c{s}.params {kv}")
    with open(os.path.join(out, "candidates.txt"), "w") as f:
        f.write("\n".join(lines) + "\n")
    print(f"{len(lines)} candidates ({draws} draws x {len(WORLDS)} worlds) -> {out}/candidates.txt")


if __name__ == "__main__":
    main()
