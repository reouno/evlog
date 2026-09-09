# e041 A plant that grows from what stands

Date: 2026-09-09

## Purpose

e040 (#37) read the world's answer to every need as "sit where the food is": a body that
must drink does not walk to the water, it sits on it, and the winner under every thirst is a
gut with no muscle. The reading (the user, 2026-09-09) is that this is not a fact about water
but about the environment: nothing in it forbids sitting. A grazed cell regrows at the sun's
rate whatever is left standing on it, so the crowd grazes every cell alike and moving never
pays. Every law that needs movement (a thirst, a reach, a store) has been tested against a
world where movement never pays, and lost to the sitter.

In the real world a lawn grows from its leaves: a place eaten to the ground stays bare for a
while, and the herd moves on. This experiment gives the world that law (#43) and tests it
together with the thirst, because the hypothesis is about two conditions at once: moving pays
when the food under a body runs out, and only then can a second need shape a route.

## Hypothesis

1. **The sitter loses.** Under a growth that follows the standing plant the food under a body
   runs out, so the movers hold the winners' share (muscle above 0, speed above the control's),
   the bodies move (forward above the control's 0.1-0.2% of decisions), and the crowd's
   footprint moves over the run.
2. **And then the thirst shapes a route.** With the two laws on, the bodies go between the
   water and the grazing: `cross2` (the ridge's bodies born in another band) above the
   control's 15-19%, the fill on the ridge above e040's 0.31-0.40, `sense_used` above the
   control's.
3. **Or the law is only a tax.** The world's income already runs through the tree crowns into
   fruit, so a law on the cells' own growth takes a few percent of the income, kills bodies,
   and leaves the sitter where it was.

## Method

Code: e040 (`experiments/e040_thirst`) as `e041_stock` with one argument more, off by default.

- **The law** (argument 37, `stock`). The light a cell can use is its light times the share it
  stands of `stock`: `max(STOCK_FLOOR, min(1, res / stock))`, with the floor at 0.1. A cell
  holding `stock` or more grows at the full rate; a cell grazed to the ground grows at a tenth
  and takes about 330 steps to stand at 1 again (e040: 100 steps). The floor is what a bare
  cell recovers by (seed, root, spore); without it a grazed cell would be dead ground for ever.
  The light a grazed cell cannot use is lost (`bare` in the log), as a dry cell's is (e035):
  the law is a tax on the world's income, not a transfer. The share is on the cell's whole
  light, its own and what its column claims from around it (e021), so a column eaten below the
  knee also loses the crown's light that falls around it as fruit (e022).
- **Checked**: `stock` 0 is e040 byte for byte (seed 8, 5,000 steps, `thirst` 0.002: every
  output file identical but the parameter line, which carries `stock`).

**The knee.** A trial (seed 8, 20,000 steps, `thirst` 0, three runs at once) put the numbers in
place before the pilot: the lawn stands at 0.03-0.05 and a tree at 1-8 (`res_max` 50-100), so at
`stock` 1 the law binds on 91-94% of the cells but takes only 0.5-1.7 of the sun's 164 per step,
because the world's income runs through the tree crowns into fruit (65-180 a step) and not
through the cells' own regrowth (3-5 a step). The world stands at every knee; the bodies fall
from 2,187 (`stock` 0) to 2,188 (0.05) and 1,494 (1). The pilot therefore runs the 2x2 of the
issue and one dose above it, at the trees' own scale.

**Runs.** Seed 9, 100,000 steps (five winters), one thread each, five at once on the Mac
(about 15 minutes), in e040's season world (`winter high` 2, water 0.1, leach 0.01, depth 0.01,
mix 0.2, flow 0, rain flat, store 5, side grow, k 1, sun 1, reach 0, thirst as below):

| run | stock | thirst |
|---|---|---|
| control (e040 byte for byte) | 0 | 0 |
| the thirst alone (e040's dose) | 0 | 0.002 |
| the law | 1 | 0 |
| the two together | 1 | 0.002 |
| the law at the trees' scale | 4 | 0 |

A batch on seeds 1-3 at 300,000 steps only if the law alone changes who wins.

Run from the repo root: `bash experiments/e041_stock/run.sh <stock> <thirst> <threads> <steps> <seeds>`.

**Measures.** The winners' shape (`lineages.csv`, `bodies.jsonl`): muscle, speed, the movers'
share, and the diversity number (#42). The world: the bodies, what it eats, the winter floors,
`bare` and `grazed` (the new columns: the light lost to the law and the share of cells below
the knee), `trees`, `fruit`, `regrowth`, the income per gut block. The movement: `forward` and
the other actions, `foot_mean`, `move_spent`, `crossers`, `cover`. The trips (`pop.csv`):
`cross0..2`, `fill0..2`, `drink0..2` per height band, and `sense_used`.

**Compute.** One multiply and one compare per cell per step: nothing measurable (the trial ran
at the control's speed).

## Result

**The pilot.** Seed 9, 100,000 steps, five runs at once, 12-13 minutes a run. Means over the
second half (steps 50,000-100,000); the floors are the five winter troughs in order; "eaten" is
plant plus meat per step; the sitter's share is the share of the bodies alive at step 100,000
held by lineages with no muscle. The control is e037's pilot byte for byte (`lineages.csv` and
`bodies.jsonl` identical, `pop.csv` identical through every column both files carry).

| run | winter floors | bodies | eaten a step | regrowth | fruit made | trees | tallest column | light lost bare | cells below the knee | muscle | speed | move cost a body | ridge born elsewhere (summer) | sitter at the end | lineages | diversity (#42) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| control (stock 0, thirst 0) | 626, 696, 724, 743, 775 | 3,674 | 116 | 8.99 | 95.7 | 239 | 38.0 | 0 | 0% | 3.13 | 0.114 | 0.00102 | 18.0% | 68% | 2 | 2 |
| thirst 0.002 | 498, 572, 651, 596, 670 | 2,459 | 125 | 10.27 | 101.4 | 410 | 58.5 | 0 | 0% | 2.74 | 0.086 | 0.00173 | 16.2% | 75% | 4 | 2 |
| stock 1 | 371, 379, 404, 413, 410 | 2,252 | 109 | 3.46 | 94.8 | 111 | 72.5 | 10.04 | 95% | 2.88 | 0.104 | 0.00093 | 16.3% | 76% | 6 | 2 |
| stock 1 + thirst 0.002 | 171, 466, 370, 337, 356 | 2,173 | 107 | 6.12 | 98.0 | 332 | 47.3 | 4.69 | 92% | 0.27 | 0.023 | 0.00085 | 15.9% | 100% | 1 | 2 |
| stock 4 | 351, 496, 348, 347, 309 | 1,857 | 91 | 3.03 | 83.8 | 74 | 78.9 | 16.78 | 98% | 3.12 | 0.102 | 0.00108 | 21.5% | 88% | 5 | 2 |

**The law binds and the world pays.** It binds on 92-98% of the cells (the lawn stands at
0.03-0.05), and takes 10.0 and 16.8 of the sun's 164 a step. The cells' own regrowth falls from
9.0 to 3.5 and 3.0 a step, the trees from 239 to 111 and 74, and the world from 3,674 bodies to
2,252 and 1,857 (-39%, -49%), with the winter floors down from 626-775 to 371-413 and 309-496.
What the world eats falls much less, from 116 to 109 and 91 a step: the crowd thins faster than
its food, and a gut block's income rises from 0.0026 to 0.0033 and 0.0030.

**Nobody leaves.** The bodies pay 0.00102 of energy a step for moving in the control and
0.00093 and 0.00108 under the law; the mean muscle (3.13 to 2.88 and 3.12) and speed (0.114 to
0.104 and 0.102) do not rise; the bodies standing in a band other than the one they were born in
fall from 9.0% of the crowd to 6.9% and 8.0%; the ridge's summer bodies born elsewhere are 16.3%
and 21.5% against the control's 18.0%. At the end of the run the sitters hold **more** of the world under the
law than in the control: 76% at `stock` 1 and 88% at `stock` 4 against 68%.

**Why: the crowd does not eat the cell it stands on.** Of the plant matter the bodies eat, 91%
is fruit lying on the ground (64.4 of 70.5 a step in the control, 96% under the law) and 9% is
standing plant. The canopy (e021) moves the light to the tall columns and the spill (e022) drops
what they cannot hold as fruit around them, and a column under a body still claims: a body
standing on a tree turns its neighbourhood's light into food at its own feet. The law throttles
the growth of a cell, which is the small flow; the fountain runs on. Fruit made barely moves
(95.7 to 94.8 and 83.8) because with fewer columns each remaining one claims more: the world
answers the law with fewer and taller trees (the tallest column 38 to 73 and 79), and the crowd
packs tighter around them (blocked moves 74% to 79-82%, cover 0.156 to 0.098).

**The two together are the strongest sitter of the five.** Under `stock` 1 with the thirst the
mean muscle is 0.27 and the speed 0.023 (a sixth and a fifth of the control's), one lineage holds
every body alive at the end, and the ridge's summer bodies born elsewhere are the lowest of the
five (15.9% against the control's 18.0%). Two needs that each cut the income select a body that spends nothing, not a body that
travels.

**The movers that do appear are scavengers, and they are booms.** The muscled winners of the
last third (24-32% of the body-steps at `stock` 1, 47% at `stock` 4, where the top lineage is 18
cells with 8 muscle) live on the dead: meat is 28-49% of their intake against the sitters' 3-14%.
Each holds for 7,000-20,000 steps and is gone. The law raises the lineage count (2 at the end in
the control, 5-6 under it) without raising the diversity number, which is 2 in every run: more
lineages, the same two shapes.

**No batch.** The rule set in the Method was a batch on seeds 1-3 only if the law alone changed
who wins. It does not: the sitter's share at the end goes up, not down, at both doses. The batch
(three runs of 300,000 steps, about 75 minutes) was not run.

## Conclusion

**Not kept** (`stock` stays an argument, 0 by default). Hypothesis 1 is answered no: the sitter
does not lose, it wins by more. Hypothesis 2 does not arise, and where it was tested the two laws
together gave the least mobile world of the five. Hypothesis 3 is answered yes: the law is a tax
that costs the world 39-49% of its bodies and half to two thirds of its trees, and buys no
movement.

The reason is not the dose. It is that the premise does not match this world: a herd leaves a
place it has emptied, and this crowd never empties the ground under it, because the ground under
it is fed from above. Since e021 and e022 the world's food is a fountain: the tall column takes
the light of the cells around it, and what it cannot hold falls as fruit at the foot of whoever
stands there. A body standing on a tree is paid for standing.

What this changes:

- **For #43.** A law on the regrowth of a cell cannot make the food under a body run out while
  91% of what the bodies eat falls from above. The next version of the premise has to act on the
  fountain: the obvious candidate is e022's exception - a column under a body still claims the
  light of its neighbours - which is the sitter's engine and was never tested on its own. Take it
  away and standing on a tree stops the fruit; the body has to step off and come back.
- **For the compound rule** (the user, 2026-09-09: a law that does not pay is usually an
  environment without its conditions). The 2x2 was the right shape and the answer is that the
  first condition was not met: the thirst was tested against a world where the food still did not
  run out. The condition to build is "the food under a body runs out", and this experiment shows
  it is not a property of the regrowth law but of the fall.
- **For the world's income.** The season world lives on 3-9 a step of standing growth and 84-101
  a step of fruit. Any law about plants that does not touch the canopy or the fall touches a
  tenth of the world.
- **Open.** One seed, 100,000 steps, two doses. Whether a knee between 0.05 and 1 would leave the
  trees alone and still empty the lawn is untested; the trial at 0.05 (20,000 steps) left the
  world at the control's population and lost 0.18 of light a step, so there is a range where the
  law is nearly free, and nothing suggests it buys movement anywhere in it.

Next: the fountain (e022's held column that still claims), then #38.
