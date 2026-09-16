#!/usr/bin/env python3
"""The candidates of e073's search (#89): the crown's yield crossed with the cold that differs by place.

Writes results/search/candidates.txt, one run per line (the prefix, then key=value), for
    xargs -P 11 -L 1 ./target/release/e073_forest < candidates.txt
Run from the repo root: uv run python experiments/e073_forest/search.py [steps] [seed]

Not a hypercube: two laws, and the question is whether each pays alone and whether they pay together
("Y pays when A and B"). The rates come from `dryrun.py`:

- `wood_yield` 3e-5 / 1e-4 / 3e-4 offers 5% / 18% / 54% of what e072's bodies eat, and in the richest
  tenth of the land a cell yields 0.12 / 0.38 / 1.15 a 1,000 steps against the 1.06 of grass it grows.
- `wood_food` (e072's share of the standing stock) is 0.04 in the default. The whole standing forest is
  1,800 steps of food for the world, and at 0.04 it is eaten to a tenth by step 12,000, so the runs
  that ask what a stand yields turn it off. d09 keeps it on to show what it costs the yield, and d10 is
  the issue's other option: a windfall large enough to pay for the tooth that takes it.
- `day_temp` 1 is the day's mean, 0 the moment (e072). The dry run: the moment stands 20 C from the
  mean on a median land cell, and by the moment every land cell is cold between a third and three
  quarters of the year, where by the mean a third of the land is never cold.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
WORLD = "c1225"
PARAMS = "experiments/e062_producers/results/worlds/c1225.params"
D11 = "grass_rate=0.009983 wood_rate=0.0017 algae_rate=0.009112 ignite=1.613e-06"
SETS = "heat=0.09 wood_food=0.04 fat_weight=0.06 store_gene=1 fresh=0.05 light=0.7 climb=6e-5 carry=0.03"

# (day_temp, wood_yield, wood_food, wood_hard, what it answers)
RUNS = [
    (1.0, 0.0, 0.04, 3, "the cold by place alone, on the default world"),
    (0.0, 0.0, 0.0, 3, "the forest left standing, no new law: the wood control"),
    (1.0, 0.0, 0.0, 3, "the forest standing and the cold by place"),
    (0.0, 1e-4, 0.0, 3, "the crown's yield alone, a fifth of what is eaten"),
    (0.0, 3e-4, 0.0, 3, "the crown's yield alone, half of what is eaten"),
    (1.0, 3e-5, 0.0, 3, "both, the yield a twentieth"),
    (1.0, 1e-4, 0.0, 3, "both, the yield a fifth"),
    (1.0, 3e-4, 0.0, 3, "both, the yield half"),
    (1.0, 3e-4, 0.0, 2, "the same with e060's tooth: has a tooth one use or two"),
    (1.0, 3e-4, 0.04, 3, "the same with the default's share of the standing stock still on"),
    (0.0, 0.0, 0.3, 3, "the windfall large enough to pay for the tooth that takes it"),
]


def main():
    steps = int(sys.argv[1]) if len(sys.argv) > 1 else 50000
    seed = int(sys.argv[2]) if len(sys.argv) > 2 else 9
    out = os.path.join(HERE, "results", "search")
    os.makedirs(out, exist_ok=True)
    lines = []
    for i, (day, yld, food, hard, why) in enumerate(RUNS):
        prefix = f"experiments/e073_forest/results/search/{WORLD}_life{seed}_d{i:02d}"
        kv = f"day_temp={day:g} wood_yield={yld:g} wood_food={food:g} wood_hard={hard:g}"
        lines.append(f"{prefix} {PARAMS} {D11} {SETS} life={seed} steps={steps} {kv}")
        print(f"  d{i:02d}: day_temp {day:g}, wood_yield {yld:g}, wood_food {food:g}, wood_hard {hard} - {why}")
    with open(os.path.join(out, "candidates.txt"), "w") as f:
        f.write("\n".join(lines) + "\n")
    print(f"\n{len(lines)} candidates x {steps} steps on seed {seed} -> {out}/candidates.txt")


if __name__ == "__main__":
    main()
