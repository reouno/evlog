#!/usr/bin/env python3
"""The candidates of e072's search (#88): a Latin hypercube over the rates of the seven balance sets.

Writes results/search/candidates.txt, one run per line (the prefix, then key=value), for
    xargs -P 11 -L 1 ./target/release/e072_balance < candidates.txt
Run from the repo root: uv run python experiments/e072_balance/search.py [draws] [steps] [seed]

Every rate 0 is e070, so the sampled combinations sit inside a box whose corner is e070's world. The
ranges come from `dryrun.py`, each set at the scale where its law starts to bite:

- heat (A): the warming takes 0.14-1.4 of the land's upkeep over the decade, the cooling 0.2-2.2 of what
  the dry air takes; the water's bodies pay a twentieth of that.
- wood_food (B): the wood a land cell stands is about nine times the grazed grass, so the share offers
  from a fifth to five times the grass.
- fat_weight (C): a full store weighs a tenth of the body at 0.02 and one and a half at 0.3.
- fresh (D): a block over median ground drinks from a third of what the body loses to the air to seven
  times it; pools are 0.24% of the land.
- light (E): how far the reach follows the light, from a tenth of the way to all of it.
- climb (F): the median rise between two land cells costs from a tenth of a sub-cell of moving to four.
- carry (G): a probe of 2,000 steps at carry 1e-4 moved 5 of soil a 1,000 steps downhill, 0.2 of it into
  the sea, so the range moves 150-15,000 a 1,000 steps against the 318,000 the land's soil holds and the
  1,700 a 1,000 steps the bodies pump onto the land.
"""
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
WORLD = "c1225"
PARAMS = "experiments/e062_producers/results/worlds/c1225.params"
D11 = "grass_rate=0.009983 wood_rate=0.0017 algae_rate=0.009112 ignite=1.613e-06"

# name: (low, high, log)
AXES = {
    "heat": (0.03, 0.3, True),
    "wood_food": (0.02, 0.5, True),
    "fat_weight": (0.02, 0.3, True),
    "fresh": (0.02, 0.5, True),
    "light": (0.1, 1.0, True),
    "climb": (1e-5, 3e-4, True),
    "carry": (0.003, 0.3, True),
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
    draws = int(sys.argv[1]) if len(sys.argv) > 1 else 22
    steps = int(sys.argv[2]) if len(sys.argv) > 2 else 50000
    seed = int(sys.argv[3]) if len(sys.argv) > 3 else 9
    rng = random.Random(72)
    out = os.path.join(HERE, "results", "search")
    os.makedirs(out, exist_ok=True)
    lines = []
    for i, c in enumerate(lhs(draws, rng)):
        kv = " ".join(f"{k}={v:.4g}" for k, v in c.items())
        prefix = f"experiments/e072_balance/results/search/{WORLD}_life{seed}_d{i:02d}"
        lines.append(f"{prefix} {PARAMS} {D11} life={seed} steps={steps} store_gene=1 {kv}")
    with open(os.path.join(out, "candidates.txt"), "w") as f:
        f.write("\n".join(lines) + "\n")
    print(f"{len(lines)} candidates x {steps} steps on seed {seed} -> {out}/candidates.txt")


if __name__ == "__main__":
    main()
