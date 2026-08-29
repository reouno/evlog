# e001 Minimal world: does the simplest evolution loop keep going?

Date: 2026-08-29

## Purpose

Before anything else, find out whether the most minimal world we can write
(resources on a grid, agents with a mutable policy, birth and death driven by energy)
can run for a long time without dying out or freezing, and how much compute it costs.
Everything later builds on this loop. If it does not work, nothing else matters.

Out of scope: learning (RL), being interesting to watch, tuning.

## Hypothesis

1. The population survives 1,000,000 steps (no extinction, no runaway growth).
2. The population keeps changing: the average genome keeps drifting, and genetic diversity does not collapse to zero.
3. One step for a few hundred agents on a 64x64 grid costs well under 1 ms in release mode.

## Method

World: 64x64 torus. Each cell holds a resource that regrows linearly up to a cap.

Agent: position, energy, genome (35 floats).
The genome is a linear policy: 6 inputs (resource here and in 4 neighbors, own energy) -> 5 actions (stay, N, S, E, W), argmax.
Each step an agent eats up to a bite from its cell, pays a base cost plus a move cost, then acts.
Energy >= threshold -> split into two (child gets half, genome mutated with gaussian noise).
Energy <= 0 -> die. No max age.

Run 1,000,000 steps with seeds 1, 2, 3. Every 10,000 steps log:
population, mean energy, mean resource, action distribution,
genome diversity (mean per-gene std), genome drift (L2 distance between mean genome now and at the previous log),
births and deaths in the window, and steps per second.

Check:
- Hypothesis 1: population > 0 at the end, and it stays bounded.
- Hypothesis 2: drift stays > 0 across the whole run, diversity does not go to ~0.
- Hypothesis 3: steps per second from the log.

Run (from repo root): `cargo run --release -p e001_minimal_world -- <steps> <seed> > experiments/e001_minimal_world/results/seed<seed>.csv`

## Result

1,000,000 steps, seeds 1-3, release build, 3 runs in parallel on one machine. Logs in `results/`.

| seed | pop min / max / last | diversity min / last | drift min / median / max | steps/sec (median) |
|---|---|---|---|---|
| 1 | 499 / 543 / 517 | 0.51 / 0.73 | 0.04 / 0.34 / 2.03 | 158,800 |
| 2 | 499 / 530 / 511 | 0.44 / 0.98 | 0.25 / 0.51 / 3.80 | 90,300 |
| 3 | 497 / 526 / 512 | 0.36 / 0.64 | 0.20 / 0.42 / 2.25 | 86,300 |

(drift excludes the first window, which includes the initial random genomes)

Behavior: within ~100k steps, "stay" drops to ~0 in every seed. Agents keep moving in one direction
(seed 1: 80% west at the end). This is a sweeping-grazer strategy: move constantly, eat what has regrown.
Seeds 2 and 3 later show a mix of directions (roughly equal N/S/E/W by step 1M), that is, several lineages coexist.

Population is pinned at ~510 by resource regrowth (64*64*0.01 = 41 energy/step supply vs ~0.08/step per agent).
Mean resource level stays around 0.05-0.06: the grid is almost always eaten bare.

## Conclusion

Hypotheses 1-3 all hold.

1. No extinction, no runaway growth. Population is bounded tightly by resource supply.
2. Genome mean keeps drifting (drift never reached 0) and diversity stays between 0.36 and 0.98. Mutation plus selection alone is enough to prevent freezing at the genome level.
3. ~6-12 us per step for ~510 agents (about 15-25 ns per agent-step). Long runs are cheap; compute is not a concern at this scale.

What this changes: the minimal loop (resources, linear policy, energy-driven birth/death, mutation) is a solid base. Keep it.

Caveat, and the open question for the next experiment: the world converges to one trivial strategy (keep moving) and then only drifts. Genome drift is not the same as visible change in the world. Nothing in this world can change structurally, because the only interaction is agent-vs-resource. To get ongoing change at the world level we will need interactions between agents (competition, predation, or similar) or an environment that itself changes. That is the next thing to test.
