"""The candidates of e061's search: a Latin hypercube over the ratios of stage A (#74).

Writes results/search/candidates.txt, one run per line (the prefix, then key=value), for
    xargs -P 11 -L 1 <binary> < candidates.txt
Run from the repo root: uv run python experiments/e061_climate/search.py [n] [first_seed]
"""
import math
import os
import random
import sys

LIFE = 300.0  # steps: a grown body's life (the same constant as main.rs)
HERE = os.path.dirname(os.path.abspath(__file__))

# name: (low, high, log). Every axis is a ratio or a property of the generated world.
AXES = {
    "size": (0, 1, False),          # 256 or 512 (the lower or upper half)
    "grain": (32, 256, True),       # cells: the widest feature of the terrain (continents)
    "land": (0.2, 0.7, False),      # share of the cells above the sea
    "relief": (500, 6000, True),    # m
    "lat_span": (30, 180, False),   # degrees of latitude the rows cover
    "lat_at": (0, 1, False),        # where that span sits between the poles
    "day_life": (0.1, 1.0, True),   # a day over a life
    "year_life": (10, 100, True),   # a year over a life
    "gain": (120, 240, False),      # C the sun overhead adds: the spread from pole to equator
    "tilt": (0, 45, False),         # degrees: the season
    "land_rate": (0.02, 0.3, True), # the land's response: the spread from night to day
    "wind": (0.1, 2.0, True),       # cells an update
    "wind_turn": (0, 90, False),    # degrees the wind turns with the season
    "rain": (0.02, 0.5, True),      # share of the excess that falls in an update
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


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 300
    first = int(sys.argv[2]) if len(sys.argv) > 2 else 1000
    rng = random.Random(61)
    out = os.path.join(HERE, "results", "search")
    os.makedirs(out, exist_ok=True)
    lines = []
    for i, c in enumerate(lhs(n, rng)):
        size = 256 if c["size"] < 0.5 else 512
        span = c["lat_span"]
        lat_lo = -90 + c["lat_at"] * (180 - span)
        year = max(40, round(c["year_life"] * LIFE / 40) * 40)
        kv = {
            "size": size,
            "seed": first + i,
            "grain": round(min(c["grain"], size / 2), 1),
            "land": round(c["land"], 3),
            "relief": round(c["relief"]),
            "lat_lo": round(lat_lo, 1),
            "lat_hi": round(lat_lo + span, 1),
            "day": round(c["day_life"] * LIFE, 1),
            "year": year,
            "gain": round(c["gain"], 1),
            "tilt": round(c["tilt"], 1),
            "land_rate": round(c["land_rate"], 4),
            "wind": round(c["wind"], 3),
            "wind_turn": round(c["wind_turn"], 1),
            "rain": round(c["rain"], 4),
        }
        prefix = f"experiments/e061_climate/results/search/c{first + i}"
        lines.append(prefix + " " + " ".join(f"{k}={v}" for k, v in kv.items()))
    with open(os.path.join(out, "candidates.txt"), "w") as f:
        f.write("\n".join(lines) + "\n")
    print(f"{n} candidates -> {out}/candidates.txt")


if __name__ == "__main__":
    main()
