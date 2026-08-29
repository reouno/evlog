# e005 Body world: does shape-derived function plus one predation rule make a food web?

Date: 2026-08-29

## Purpose

`vision.md`, mechanisms 1 and 2. e004 gave us bodies grown from the genome. Here the body decides
what the agent can do: mass, speed, attack, defense, and diet are all derived from the blocks, every
block costs upkeep, and one rule adds predation: you can eat what your attack beats and your gut
accepts. Nothing says who is a herbivore or a carnivore.

Two questions. Does the population split into different kinds of body (a food web), or does one body
win as in e001 and e003? And does the world keep changing instead of settling?

Out of scope: learning, sexual reproduction and species (e006), tuning for beauty.

## Hypothesis

1. **Survival.** The world runs 1,000,000 steps without extinction.
2. **Differentiation.** Bodies split into distinct types rather than one body for everyone: at the
   end of the run, several bodies coexist (no clone holds more than 50% of the population) and
   agents that eat other agents coexist with agents that eat only plants.
3. **Ongoing change.** The population's mean body keeps moving through the whole run, not only at the
   start: the distance between the mean body now and 100,000 steps earlier stays above zero at every
   point of the run, and the dominant body at 1M is not the dominant body at 500k.
4. **Cost.** Tens of thousands of steps per second.

## Method

World as e003 (64x64 torus, food regrows +0.01 per cell per step up to 1.0), agents born from a
512-symbol genome with 2 point mutations per child, split when energy passes a threshold, die at
energy 0 or at age 3,000.

Body as e004: the gene network runs once per cell of an 8x8 grid with 6 position morphogens, and a
fixed table reads each cell as empty, hard, muscle, sensor or digestive. The same table has 55 more
columns that give the movement policy, read from one more run of the network without position input.

Function from shape (all derived, nothing chosen per agent):
- `mass` = number of blocks. Upkeep 0.002 per block per step; moving costs 0.001 per block per cell.
  Split threshold = 2 + 0.1 * mass. A body with no blocks is not viable.
- `speed` = muscle / mass. A move goes 2 cells with probability `speed`.
- `sense` = min(1, sensor / 8). Weight of the second cell out in every direction of the policy's inputs.
- `bite` = 0.02 * digestive: plant intake per step from the cell. `gut` = 4 * digestive: the largest
  prey mass the agent can eat.
- `attack` = min(hard blocks in the front 3 rows, muscle blocks): teeth need force behind them.
- `defense` = hard blocks / 2.

Predation, checked once per step per agent against the agents in its cell and the 4 neighbor cells:
if `attack` > prey `defense`, prey mass <= `gut`, and the prey does not get away (it escapes with
probability prey speed minus own speed), the prey dies and the eater gains half of its energy plus
0.02 per block of its body. Agents with identical bodies do not eat each other.

Policy: 10 inputs (food here and in 4 directions, other agents in 4 directions, energy / threshold)
to 5 actions (stay, N, S, E, W), argmax. The inputs do not say whether a neighbor is prey or a threat;
whatever an agent does about neighbors has to come from its own genome, together with its body.

Rules tried before this one, 100,000 steps, seed 1:

| Rule | What happened |
|---|---|
| attack = front hard, no escape | One body in 10,000 steps: 48 hard + 16 digestive, attack 24, defense 24, immune to everyone. 11-18 distinct bodies, top clone 43-88%. |
| + escape by speed | Same. Nobody has muscle, so nobody escapes. |
| + attack = min(front hard, muscle) | Mass swings between 21 and 63, 29-188 distinct bodies, top clone 8-56%, thousands of predation deaths per 10,000 steps. Used below. |

The first two are the e001 problem in a new shape: hard blocks alone gave both the best attack and
the best defense, and the ceiling was affordable. Requiring muscle behind the bite makes armor,
attack, and speed compete for the same 64 cells.

Runs: seeds 1-3, 1,000,000 steps, 400 random genomes to start. Every 10,000 steps: population, food,
births, deaths by cause (energy, age, eaten, no body), escapes, plant and meat intake, mean and std
of mass and of each block kind, attack, speed, distinct bodies, top clone share, and the share of
agents whose lifetime intake is plants only / mixed / meat only. Every 100,000 steps: one row per
living agent (body counts, attack, speed, age, energy, plant and meat intake). Snapshots as e003
(every 5,000 steps, and every step for 400 steps at 600,000), with each agent's body.

Run (from repo root): `cargo run --release -p e005_body_world -- <steps> <seed>`
Outputs: `results/seed<seed>_{log.csv,agents.csv,long.jsonl,clip.jsonl,bodies.jsonl}`.
The `.jsonl` files are not committed; re-run the seed to regenerate them before building the report.

## Result

Seeds 1-3, 1,000,000 steps each, three runs sharing one machine. Logs in `results/seed*_log.csv`,
per-agent rows every 100,000 steps in `results/seed*_agents.csv`.

- Survival: population 190-540 throughout, 249 / 219 / 212 at the end. Mean mass 21-64 blocks,
  swinging by 20-40 blocks within a run.
- Speed: median 1,526 / 1,519 / 1,730 steps/s (range 800-5,700). Births are 10,000-30,000 per
  10,000 steps, that is 1-3 developments per step at 0.22 ms each.
- Distinct bodies alive: 29-188 (seed 1), 34-122 (seed 2), 1-181 (seed 3). Biggest clone: 8-74%,
  7-65%, 5-100%; above 50% in 4, 4 and 24 of the 100 log windows. At 1M: 20%, 64%, 44%.
- Two body types recur in every seed. Armored grazer: 38-48 hard, 0-1 muscle, 15-22 digestive,
  attack 0, defense 19-24. Omnivore: 21-28 hard, 20-23 muscle, 16-19 digestive, attack 20-22.
  Dominant body (hard, muscle, sensor, digestive) at 500k -> 1M:
  seed 1 (14,3,0,17) -> (38,0,1,15); seed 2 (48,0,0,15) -> (44,0,0,17); seed 3 (42,0,0,22) -> (44,0,0,20).
- Diet at 1M: agents that have eaten meat 25% / 10% / 7% (range over the run 2-55%); meat-only
  agents at most 0.4% at any time. Meat is 1.9-4.1% of all energy eaten in the last 100k steps.
- Deaths in the last 100k steps: eaten 54% / 53% / 26%, starved 45% / 46% / 73%, old age about 1%.
  Escapes are 2-7% of encounters that would otherwise be a kill.
- Body drift (distance between the mean body and the mean body 100k steps earlier, in blocks):
  minimum 1.26 / 0.41 / 0.66, median 6.4 / 6.2 / 8.9, maximum 20-29.
- Seed 3, step 810,000: one omnivore body (22 hard, 23 muscle, 3 sensor, 16 digestive) is the entire
  population (1 distinct body). By 910,000 there are 47 distinct bodies again.
- Sensor blocks: population mean never above 3. Genes per genome: 6-9 at start, 14-16 at 1M.

## Conclusion

1. Survival: yes.
2. Differentiation: partly. Every seed has the same two kinds of body, the armored grazer and the
   omnivore with teeth, and they coexist for the whole run with 7-25% of agents having eaten meat at
   the end. But no pure carnivore appears (meat is 2-4% of energy; kills are mostly newborns with
   little energy), and seed 2 ends with one clone at 64%.
3. Ongoing change: yes. The mean body never stops moving (at least 0.4-1.3 blocks per 100k steps,
   typically 6-9), armor is built up and stripped away, and one seed shows a full takeover by a
   predator body followed by re-diversification. This is the first run in the project that does not
   settle on one strategy.
4. Cost: no. 1,500 steps/s. Development at every birth is the cost.

What this changes:
- The rule set works and is kept: e004 bodies, derived function, one predation rule with muscle
  behind the bite, escape by speed.
- The decisive step was a trade-off, not a cost: attack from hard blocks alone let one immune body win
  in 10,000 steps, whatever the upkeep. Cost constants scale the population; the shape of the
  trade-offs decides what evolves. Same lesson as e003, now confirmed on shapes.
- The predator-prey arms race keeps the world from settling, as hoped in `vision.md`.
- Open: no pure carnivores, because prey is worth little. Worth testing prey that grows (energy stored
  in the body), but only after e006.
- Open: sensors are useless as the policy is set up (neighbor inputs do not distinguish prey from
  threat). Leave until behavior matters more.
- Open: speed. Development at 0.22 ms per birth dominates. A cheaper sigmoid or a thread pool for
  births should bring the world back to tens of thousands of steps/s; do this before e006's longer runs.
- The gene-count bias is back (+7 genes per genome over the run). Still watching.
