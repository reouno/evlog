#!/usr/bin/env python3
"""The candidates of e075's search (#90): the tear crossed with the frail line.

Writes results/search/candidates.txt, one run per line (the prefix, then key=value), for
    xargs -P 11 -L 1 ./target/release/e075_hunt < candidates.txt
Run from the repo root: uv run python experiments/e075_hunt/search.py [steps] [seed]

Not a hypercube: two laws, and the question is whether flesh pays alone under either and whether it
pays under both ("Y pays when A and B"). The rates come from `dryrun.py`, on e073's kept world:

- a break gives 0.29 today, 0.9 turns of a full gut's feeding, and one break takes about 17 presses;
  a whole body is worth 9.1 and a break is 2.9% of it.
- `flesh_bite` 0.05 / 0.15 / 0.4 of what a prey still holds adds 0.41 / 1.24 / 3.32 to a break: 2.2 /
  4.8 / 11.3 turns of feeding. A sitter takes 0.167 a turn from plants, so the tear is what decides
  whether a break can beat grass.
- `frail` 0.5 / 0.75 / 0.9 of the birth blocks kills 5% / 15% / 26% of the standing crowd at once (a
  transient of the first steps) and lets a prey of 35 blocks die after 18 / 9 / 3 breaks.
- the last run asks the crowd's side of it (#90's condition B): the same rates with the crown's
  yield off, which is the thicker, less travelled crowd of e072.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
WORLD = "c1225"
PARAMS = "experiments/e062_producers/results/worlds/c1225.params"
D11 = "grass_rate=0.009983 wood_rate=0.0017 algae_rate=0.009112 ignite=1.613e-06"
SETS = "heat=0.09 wood_food=0 fat_weight=0.06 store_gene=1 fresh=0.05 light=0.7 climb=6e-5 carry=0.03"
KEPT = "wood_hard=3 day_temp=0"

# (flesh_bite, frail, wood_yield, what it answers)
RUNS = [
    (0.0, 0.0, 3e-5, "the control: e073's kept world, one break one block"),
    (0.05, 0.0, 3e-5, "the tear alone, a break worth 2.2 turns of feeding"),
    (0.15, 0.0, 3e-5, "the tear alone, 4.8 turns"),
    (0.4, 0.0, 3e-5, "the tear alone, 11.3 turns"),
    (0.0, 0.5, 3e-5, "the frail line alone, a prey dead after half its blocks"),
    (0.0, 0.75, 3e-5, "the frail line alone, dead after a quarter of them"),
    (0.05, 0.75, 3e-5, "both, the smallest tear that can pay"),
    (0.15, 0.5, 3e-5, "both, the middle tear and the far line"),
    (0.15, 0.75, 3e-5, "both, the middle of the set"),
    (0.4, 0.5, 3e-5, "both, the largest tear against the far line"),
    (0.15, 0.75, 0.0, "the middle of the set in the thicker crowd (no crown's yield)"),
]


def main():
    steps = int(sys.argv[1]) if len(sys.argv) > 1 else 50000
    seed = int(sys.argv[2]) if len(sys.argv) > 2 else 9
    out = os.path.join(HERE, "results", "search")
    os.makedirs(out, exist_ok=True)
    lines = []
    for i, (flesh, frail, yld, why) in enumerate(RUNS):
        prefix = f"experiments/e075_hunt/results/search/{WORLD}_life{seed}_d{i:02d}"
        kv = f"flesh_bite={flesh:g} frail={frail:g} wood_yield={yld:g}"
        lines.append(f"{prefix} {PARAMS} {D11} {SETS} {KEPT} life={seed} steps={steps} {kv}")
        print(f"  d{i:02d}: flesh_bite {flesh:<5g} frail {frail:<5g} wood_yield {yld:<6g} - {why}")
    with open(os.path.join(out, "candidates.txt"), "w") as f:
        f.write("\n".join(lines) + "\n")
    print(f"\n{len(lines)} candidates x {steps} steps on seed {seed} -> {out}/candidates.txt")


if __name__ == "__main__":
    main()
