# e042 A body pays what it owes

Date: 2026-09-10

## Purpose

The viewer's card (2026-09-10) showed a body of 18 hard blocks and 18 guts, no muscle, sitting
on one spot at zero energy and zero fat for 454 steps. It owed 0.104 a step and ate 0.034. The
reason is in the upkeep lines, the same in e030-e041 (#46):

```
from_energy = min(full, energy + eaten)
from_fat    = min(full - from_energy, fat)        // store > 0
fat        += from_energy * flesh - from_fat
dies at the end of the step if energy <= 0 and fat <= 0
```

What the energy, this step's food and the fat cannot pay is dropped, and with `flesh` 1 the food
paid into the upkeep is fixed as fat in the same step, so a body that eats anything in a step
passes the death test. In e041's season world (seed 96, steps 10,000-20,000) 19% of the
body-steps could not pay in full, 98% of those lived on, and 19.5% of the upkeep owed went
unpaid. The work of moving has the same gap: it is paid from the energy only, so a body at
zero energy moves for free.

e030 kept the store on "45-75% of the bodies are at zero energy and alive on their fat" and
"starvation deaths fall from 17-21 a step to 2-6". Part of that is this gap, and every
experiment since (the winter floors, the sitter that wins, "size does not pay") stands on it.
This experiment takes the gap away and asks what of the world was the store and what was the
gap.

## Hypothesis

1. **The world stands, smaller.** Under `strict` the bodies alive and the winter floors fall by
   about the unpaid share of the upkeep (a fifth), and the share of bodies at zero energy falls
   well below the control's.
2. **The subsidy went to big bodies that eat a fraction of their upkeep, so the bodies get
   smaller.** The median size of the bodies falls under `strict`.
3. **The store is still worth keeping.** Under `strict`, `store` 5 holds higher winter floors
   than `store` 0: a fat that pays the upkeep of a body with no food still bridges the winter.

## Method

Code: e041 (`experiments/e041_stock`) as `e042_strict` with one argument more, off by default.

- **The law** (argument 38, `strict`). A body that cannot pay its upkeep in full (energy, then
  this step's food, then fat) dies of hunger at the end of the step. The work of moving is paid
  from the energy and then from the fat (breathed, as the fat paid into the upkeep is), and a
  body that cannot pay it dies the same way. Nothing else changes: the fat fixed from the food
  still counts as the store.
- **Log.** `short` (the share of body-steps whose upkeep was not paid in full), `unpaid` (the
  share of the upkeep owed that was not paid), `move_free` (the work of moving not paid, per
  body per step). Counted under either law, so the control measures its own gap.
- **Checked**: `strict` 0 is e041 byte for byte (seed 8, 5,000 steps: every output file
  identical but the parameter line and the three new log columns; and the pilot's control on
  seed 9 against e041's control: every file identical, the log in its first 145 columns but
  `steps_per_sec`); matter is conserved under `strict` 1 (`EVLOG_AUDIT=1`, seed 8, 10,000 steps:
  the largest step 3e-6 and the drift 1.3e-4 on 140,000, against 1e-6 and 1.3e-4 at `strict` 0).

**Runs.** Seed 9 and 10, 100,000 steps (five winters), one thread each, five at once on the Mac
(28 minutes), in e041's season world (`winter high` 2, water 0.1, leach 0.01, depth 0.01,
mix 0.2, flow 0, rain flat, side grow, k 1, sun 1, reach 0, thirst 0, stock 0):

| run | strict | store | seeds | question |
|---|---|---|---|---|
| control (e041 byte for byte) | 0 | 5 | 9, 10 | how big is the gap over a whole run |
| strict | 1 | 5 | 9, 10 | does the world stand, and what wins (1, 2) |
| strict without the store | 1 | 0 | 9 | is the store still worth keeping (3) |

A batch on seeds 1-3 at 300,000 steps only if `strict` changes who wins.

Run from the repo root: `bash experiments/e042_strict/run.sh <strict> <store> <threads> <steps> <seeds>`.

**Measures.** The world: bodies, the winter floors, the share at zero energy (`on_fat`),
starvation deaths a step, `short`, `unpaid`, `move_free`, fat burned. The bodies: size (median
and the 90th percentile), muscle, speed, move cost, the sitter's share at the end, lineages,
the diversity number (#42).

**Compute.** One compare and a few additions a body a step: nothing measurable.

## Result

**The pilot.** Seeds 9 and 10, 100,000 steps, five runs at once, 28 minutes. Means over the
second half (steps 50,000-100,000): the bodies and the share at zero energy from `pop.csv`
(every 1,000 steps), the rest from the log (every 10,000). The floors are the five winter
troughs. "Flesh" is the share of what is eaten that is the dead and broken cells. "Top lineage"
is the lineage holding the most body-steps of the last third. (e041's README gave the log's
bodies, 3,674 for this control, which samples two phases of the season; the `pop.csv` mean is
3,085.)

| run | winter floors | bodies | eaten a step | flesh | at zero energy | starvation deaths a step | upkeep unpaid | moving a body, paid / not paid | median size (p10-p90) | mass | muscle | top lineage of the last third | lineages at the end | diversity (#42) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| control, seed 9 | 626, 696, 724, 743, 775 | 3,085 | 116 | 39% | 57% | 8.9 | 17.9% | 0.00102 / 0.00077 | 9.0 (3.0-21.8) | 17.2 | 3.13 | sitter (10 gut), 53% | 2 | 2 |
| control, seed 10 | 743, 862, 1,017, 912, 947 | 3,447 | 106 | 31% | 54% | 9.4 | 5.9% | 0.00081 / 0.00091 | 5.2 (2.4-13.4) | 11.9 | 1.50 | sitter (7 gut), 49% | 8 | 3 |
| strict, seed 9 | 605, 549, 698, 644, 612 | 2,020 | 109 | 36% | 43% | 5.1 | 0.1% | 0.00280 / 0.00001 | 12.4 (3.8-16.0) | 19.9 | 4.33 | mover (7 muscle, 6 gut), 47% | 9 | 2 |
| strict, seed 10 | 699, 757, 707, 663, 771 | 2,764 | 115 | 36% | 46% | 11.3 | 0.2% | 0.00291 / 0.00001 | 10.0 (3.0-15.8) | 15.5 | 3.01 | mover (6 muscle, 4 gut), 51% | 2 | 2 |
| strict, no store, seed 9 | 684, 666, 678, 623, 649 | 2,943 | 251 | 68% | 0% | 18.5 | 0.3% | 0.00327 / 0.00002 | 16.0 (7.6-17.8) | 24.8 | 3.31 | sitter (13 gut), 44% | 9 | 2 |

Under `strict` the unpaid upkeep is the last step of the bodies that die.

**The gap in the control.** 17.4% (seed 9) and 5.6% (seed 10) of the body-steps could not pay
their upkeep in full over the second half, and 17.9% and 5.9% of the upkeep owed went unpaid;
in the first 10,000 steps 29% and 35% of the body-steps were short. Of the work of moving,
43% and 53% was never paid: a body at zero energy (half the world at any time) moved for
nothing. Seed 96's 19.5% (#46, steps 10,000-20,000) sits inside this range.

**The world stands, smaller.** On both seeds, with 35% and 20% fewer bodies and winter floors
13% and 20% lower (means 622 against 713 and 719 against 896). What the world eats does not
fall: 109 and 115 a step against 116 and 106. The share of bodies at zero energy falls from 57%
and 54% to 43% and 46%: nearly half the bodies still live at zero energy, on a fat that now pays
in full (the fat per body 18.5 against 7.9 on seed 9, 7.4 against 9.2 on seed 10). Starvation
deaths and births go either way by seed (5.1 and 7.0 a step against 8.9 and 11.2 on seed 9,
11.3 and 14.0 against 9.4 and 11.0 on seed 10).

**The bodies get bigger, and move more.** The median body grows from 9.0 to 12.4 cells and from
5.2 to 10.0, the mass from 17.2 to 19.9 and from 11.9 to 15.5. On seed 9 the largest bodies go
too (the 90th percentile from 21.8 to 16.0 cells): the sizes close in on 10-16 cells. The mean
muscle rises from 3.13 to 4.33 and from 1.50 to 3.01, the speed from 0.114 to 0.149 and from
0.128 to 0.141, the decisions to move forward from 58.5% to 70.1% and from 64.1% to 71.0%. The
work of moving, paid or not, rises from 0.0018 to 0.0028 and from 0.0017 to 0.0029 a body a step
(1.6 and 1.7 times); what the bodies pay for it rises 2.7 and 3.6 times, since nothing is free.

**A mover takes the top.** In both controls the top lineage of the last third is a gut with no
muscle (lineage 1: ten gut cells, 53%; lineage 3: seven, 49%). Under `strict` it is a mover
(lineage 465: 13.9 cells, 7 muscle, 6 gut on a 4x4 grid, 44% flesh, 47%; lineage 178: 10 cells,
6 muscle, 4 gut, 44% flesh, 51%), each beside a sitting gut (lineage 118: six cells, 42%;
lineage 90: eight gut cells, 45%). The same two kinds were the control's on seed 9, with the
order reversed; on seed 10 the control's second kind was a set of small movers of 4-8 cells
(2-4 muscle). The sitters' share of the bodies alive at the end falls from 68% to 48% on seed 9
and stays at 51% on seed 10. The lineages at the end go 2 to 9 and 8 to 2; the diversity number
is 2 in both `strict` runs (the controls 2 and 3).

**Without the store.** With `store` 0 the fat is never spent (e029's law), so the upkeep a body
pays is fixed in its flesh and none of it is breathed, and the matter runs through the dead.
Under `strict` that world stands as well as the store's: floors 623-684 (mean 660 against the
store's 622), more bodies (2,943 against 2,020), none at zero energy (with no store a body at zero
energy dies), and a fast turnover (18.5 deaths and 20.4 births a step). It eats 251 a step, 68%
of it flesh (171), against 109 and 36%. The bodies are big (median 16 cells, the 10th percentile
7.6) and the top lineage is a sitting gut of 13 cells at 57% flesh. Diversity 2.

**No batch.** The rule in the Method was a batch on seeds 1-3 only if `strict` changed who wins,
and on seed 10 it moves the top from a sitter to a mover. It was not run: whether `strict` is
kept does not depend on who wins (it removes a gap in the ledger that e030 already described as
closed), and the next experiment's control runs under `strict` and will show whether the mover's
lead lasts past 100,000 steps (e037 found a pilot's winner that was the start's transient).

## Conclusion

1. **The world stands, smaller: yes.** 20-35% fewer bodies on the same food, floors 13-20%
   lower, and fewer bodies at zero energy (43-46% against 54-57%).
2. **The bodies get smaller: no, the opposite.** The median body grows by 3.4 and 4.8 cells, and
   the muscle, the speed and the moving rise with it. The gap paid most to a body that ate less
   than it owed and did not move.
3. **The store is still worth keeping for the winter: no, not in this world.** Without the
   forgiveness a world without the store holds the same floors on seed 9. What the store decides
   is where the matter cycles (the air, or the dead) and how big the bodies are. It stays at 5:
   one seed, and e030's case for it was the flat winter, where the valley's refuge does not exist.

**Kept**: the season world is `strict` 1 from here (the next experiment's default; the argument's
default here stays 0, e041 byte for byte).

What this changes:

- **For the results since e030.** Everything about bodies at zero energy - e030's store
  ("45-75% of the bodies alive on their fat"), the winter floors, the sitter that wins, "size does
  not pay" - was measured with 6-18% of the upkeep forgiven and free moves at zero energy. The
  direction of several of them holds (the world stands, the sitter still exists), but the sitter's
  lead and the small bodies were partly the gap's.
- **For movement.** #43 and #37 looked for a reason to move in the environment and found none;
  part of what made sitting free was the ledger. Under `strict` the mover leads without a new law.
- **Next**: #45 (the canopy's fall and its saturation, unbundled) under `strict`, then #47
  (ageing), #38, #5.
