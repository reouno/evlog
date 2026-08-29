# e003 Genome world: can selection climb the genome map when traits have costs?

Date: 2026-08-29

## Purpose

e001 showed the minimal world runs. e002 showed a DNA-like genome can produce traits. This experiment
joins them: every agent is born from a 512-symbol genome, and its traits decide how it eats, moves,
senses, breeds, and ages, each with a cost. The question is whether natural selection can find its way
through an indirect, pleiotropic map, or whether the map is too tangled to climb.

Second purpose: check that we can watch the world. The run writes snapshots that a small viewer in
the report replays (long view every 5,000 steps; one continuous clip at every step).

Out of scope: agent-agent interaction, learning, tuning of costs.

## Hypothesis

1. **Survival.** The population survives 1,000,000 steps with genome-born agents (no extinction).
2. **Selection climbs.** Traits that have a cost or benefit move away from the random-genome baseline
   (mean 0.50) by the end of the run, while the three traits the world ignores stay near 0.50 and
   move no more than drift would. Concretely: for each used trait, |mean - 0.5| at 1M steps is at least
   twice the largest |mean - 0.5| among unused traits.
3. **Diversity survives the trade-offs.** No used trait collapses to a single value (std at 1M > 0.03).
4. **Cost.** With decode at birth, the world still runs at over 20,000 steps per second.

If 2 fails while 1 holds, pleiotropy (e002) is the first suspect, and a sparse table is the next experiment.

## Method

World as e001 (64x64 torus, food regrows +0.01/step to 1.0), with these changes.

Genome and decoding as e002, except the fixed table has 43 columns: 8 traits plus 35 numbers that
become the movement policy (the linear policy of e001, weights mapped to [-1, 1]). One map, one genome.

Traits with meaning (all in [0, 1]):
- `size`: bite = 0.1 + 0.3*size per step; base cost = 0.03 + 0.06*size.
- `speed`: a move goes 2 cells with probability `speed`; each move costs 0.01 + 0.05*speed.
- `sense`: the four neighbor inputs become food at distance 1 plus `sense` times food at distance 2; costs 0.02*sense per step.
- `fertility`: split when energy >= 14 - 8*fertility (6 to 14); child gets half.
- `lifespan`: max age = 200 + 1800*lifespan steps; costs 0.02*lifespan per step.
- `metabolism`, `greed`, `boldness`: unused. They are the control group for hypothesis 2.

Children: copy of the parent genome with 2 random point mutations, decoded at birth.
Start: 300 random genomes, energy 5. Runs: seeds 1-3, 1,000,000 steps.

Every 10,000 steps log: population, mean energy, mean food, mean and std of each trait, mean gene count,
births, deaths (by energy and by age), action shares, steps per second.
Snapshots: every 5,000 steps (long view) and every step from 600,000 to 600,400 (clip): food grid and
each agent's position, size, lifespan.

Run (from repo root): `cargo run --release -p e003_genome_world -- <steps> <seed>`
Outputs go to `experiments/e003_genome_world/results/seed<seed>_{log.csv,long.jsonl,clip.jsonl}`.
The `.jsonl` snapshots (about 10 MB per seed) are not committed; re-run the seed to regenerate them before building the report.

## Result

Seeds 1-3, 1,000,000 steps each. Logs in `results/seed*_log.csv`, snapshots in `results/seed*_{long,clip}.jsonl`.

- Survival: population 368-783, ending at 718-740. No extinction.
- Speed: 35,000-40,000 steps/s with three runs sharing the machine.
- Used traits (mean at start -> at 1M, all seeds):
  speed 0.12-0.23 -> 0.01-0.03; sense 0.29-0.60 -> 0.02-0.06; size 0.35-0.57 -> 0.04-0.05;
  fertility 0.48-0.88 -> 0.94-0.98; lifespan 0.51-0.59 -> 0.41-0.45.
  Speed, sense, size and fertility settle within 30k-90k steps in seeds 1 and 2, and by 290k in seed 3.
- Unused traits at 1M: metabolism 0.44-0.59 (stays near 0.5 in all seeds); greed 0.52 / 0.88 / 0.97; boldness 0.49 / 0.68 / 0.81.
- Std at 1M: speed 0.01-0.02, sense 0.02-0.03, size 0.02-0.03, fertility 0.02-0.05, lifespan 0.07-0.10; unused traits 0.09-0.31.
- Gene count: 11-14 at start -> 16-18 at 1M, rising through the whole run.
- Deaths by age are 44% (seed 1) and 77-78% (seeds 2, 3) of all deaths in the last 100k steps.
- Food stays at 0.07-0.08 per cell: bare, as in e001.

## Conclusion

1. Survival: yes.
2. Selection climbs: yes, and fast. Every trait with a cost or benefit moves decisively and in the direction the costs
   predict. But the second half of the hypothesis fails in two of three seeds: greed and boldness, which the world
   ignores, end at 0.88-0.97 and 0.68-0.81. They are dragged along by selection on other traits (hitchhiking through
   pleiotropy, the caveat from e002). Metabolism, the third unused trait, behaves as a proper control.
3. Diversity survives: no. Speed, sense, size and fertility collapse to the edge of their range with std 0.01-0.05.
   The reason is in the costs, not in the genome: those four traits are pure cost or pure benefit in this world
   (food is always bare, so a bigger bite buys nothing; moving two cells buys nothing), so the best value is the
   boundary. Only lifespan, which trades a per-step cost against more years, settles in the middle (0.41-0.45) and keeps a spread.
4. Cost: yes.

What this changes:
- The genome map works under selection; keep it.
- A trait needs a real two-sided trade-off, or evolution just pins it. Designing traits means designing trade-offs. This is the main lesson.
- Pleiotropy is not only a theoretical worry: it moves unrelated traits by 0.3-0.5. A sparse table is the next thing to test.
- The gene-count bias from e002 shows up in the world (+5 genes over the run). Not harmful yet; keep watching.
- Snapshots and the in-report viewer work; watching the world is feasible with a log, no renderer in the simulation.
