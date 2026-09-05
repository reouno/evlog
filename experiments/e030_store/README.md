# e030 A store a body can spend

Date: 2026-09-05

## Purpose

The season (e026) showed the ceiling of the bodies: a body has no store of its own. Its
upkeep is fixed in its flesh as fat (e024), but the fat is its eater's, never the body's; a
body that eats less than its upkeep dies within 40-90 steps whatever it holds. So the season
at amplitude 1 kills the world in its first winter, and at 0.75 every winter is a lottery of
23-40 bodies. The real world's answer is fat: a bear or a whale carries its summer through the
winter, and a large body carries more per unit of upkeep. This experiment makes the fat the
body's own, bounded by its flesh, and asks whether a winter can then be lived through, whether
the fat is selected for, and whether size begins to pay (vision item 1; #28 said size will pay
when a body can do with size what a small body cannot).

## Hypothesis

1. **The store exists.** Bodies short of energy live on their fat: a share of the bodies at
   zero energy alive (`on_fat`), fat burned every step, deaths by starvation down.
2. **The season goes past 0.5.** At amplitude 0.75 the winter trough rises from e026's 23-40
   bodies to hundreds, and more than one lineage lives through the run.
3. **Size begins to pay.** Under `grow` the side and the size in cells rise against e029's
   `grow` world (side 4.4-14.3 by seed, 11-16 cells), or at least the winter's survivors are
   larger than the summer's bodies, because a body's store is `store` times its mass and its
   upkeep is 0.002 per cell plus 0.032 per body: a body of 16 cells holds a store for 2.9
   times the steps a body of 4 does, per unit of mass, at `store` 5 (1,400 steps against
   500 at density 1).
4. **The world changes shape.** Bodies that starve no longer feed the ground at once: fewer
   bodies, fatter, more matter in the bodies, and the air rains again (a body's fat is
   breathed when it is burned; the flesh law at 1 breathed nothing).

## Method

Code: e029 (`experiments/e029_size`) as `e030_store`, with argument 21 `store`: fat per unit
of mass the flesh can hold. 0 is e029 byte for byte (checked on seed 9 for 10,000 steps at
side 8: `agents.csv` identical, the log identical but the three added columns).

**The law.** The fat a body fixes from its upkeep (the flesh law: all of it at `flesh` 1) is
the body's own store. A body whose energy cannot pay its upkeep pays the rest from its fat;
what the fat pays is breathed (to the air, like the burned share of the upkeep), never fixed
again, so a body living on its fat loses it at its upkeep and dies when it is gone. The flesh
holds at most `store` of fat per unit of the body's mass (the weight law's mass: what the body
is made of); what is fixed beyond that is breathed. The fat still goes to the eater when a
cell is broken and to the ground when the body dies (e024's worth); a child gets half its
parent's energy, none of its fat. The policy does not see the fat (its inputs are e026's).
The ledger holds (`EVLOG_AUDIT=1`, seed 9, 10,000 steps at `store` 5: drift 3e-7 of the
matter). The log gets `fat_spent`, `fat_over` and `on_fat`.

**The world.** e026's season world (128x128, matter 8 per cell, the weight and flesh laws,
the canopy, the spill, rain on every cell alike) at amplitude 0.75, the amplitude that was a
lottery every winter: the sun falls to a quarter at midwinter and stays under a half for
6,700 steps of every 20,000. The control is e026's pilot at 0.75 (this code at `store` 0,
seed 9, 200,000 steps) and, under `grow`, e029's `grow` runs at 0.5.

**Runs.** Three pilots on seed 9, 100,000 steps (five winters), three threads each at once:
`side` 8 at `store` 1 (a store of 270 steps of upkeep for a body of mass 15) and `store` 5
(1,300 steps), and `grow` at `store` 5. Then the batch if the pilots say the world stands.

## Result

Byte check: `store` 0 at side 8 on seed 9 for 10,000 steps: `agents.csv` identical to e029,
the log identical but the three added columns. Ledger: drift 3e-7 of the matter over 10,000
steps at `store` 5 (`EVLOG_AUDIT=1`).

### The pilots (seed 9, 100,000 steps, five winters; 11 minutes each at three threads)

Bodies and lineages every 1,000 steps are sums over the lineage log (lineages of 5 or more);
a winter floor is the least in a cycle of 20,000 steps.

| run | winter floors (bodies) | lineages at the floors | summer peaks | mass at the floors / at the peaks | on their fat | fat burned a step | fat per body | killed a step | bodies with a bite | side at the end |
|---|---|---|---|---|---|---|---|---|---|---|
| e026 control (store 0) | 218-1,064 | 1-2 | 2,941-6,046 | 17-22 / 13-22 | - | - | 6-11 | 0.74-8.06 | 0-9% | 8 |
| store 1 | 123-702 | 2-11 | 2,182-3,523 | 13-39 / 15-18 | 47-75% | 22-58 | 5-9 | 0.01-0.78 | 0-2% | 8 |
| store 5 | 615-1,071 | 3-7 | 2,007-4,897 | 27-43 / 12-28 | 56-73% | 32-69 | 6-20 | 0.04-2.02 | 1-21% | 8 |
| grow, store 5 | 517-1,136 | 2-9 | 2,228-3,544 | 16-32 / 15-27 | 48-69% | 28-65 | 10-16 | 0.06-2.24 | 1-24% | 7.3 |

The store is in use at every season: 47-75% of the bodies are at zero energy and alive on
their fat, burning 22-69 of fat a step (the sun gives 41-287 over the season); starvation
deaths fall from 15-48 a step to 2-11. The winter floors are the control's in these first five
winters, but 3-9 lineages stand on them instead of 1-2, and at `store` 5 the bodies on the
floor weigh 27-43 against 12-28 at the peak (the control's weigh the same in both seasons).
Kills fall (0.7-8 a step to 0.04-2), but at `store` 5 up to a fifth of the bodies bite, where
the control has none. Under `grow` the side falls to 6.9-7.4 in the first 30,000 steps and
stays; the cells per body are 12-25 (the control 10-24).

### The batch (grow, seeds 1-3, 300,000 steps, 15 winters; six runs at one thread, 74 minutes)

Second half unless said. The winter floors are over all 15 winters.

| run | bodies | winter floors | lineages at the floors (winters 4-15) | summer peak | mass at the floors / peaks | on their fat | side at the end | cells per body | mass p50 / p90 | density | killed a step | bodies with a bite | sensor per body (peak lineage) | starved a step | flesh in the winners' intake | rain a step | longest lineage | winners; longest hold |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| store 5, seed 1 | 3,078 | 433-1,186 | 2-11 | 3,881 | 12 / 13 | 47% | 5.6 +- 1.5 | 8 | 14 / 22 | 1.59 | 1.22 | 0% | 0.2-0.4 | 5.5 | 26-47% | 49 | 300,000 | 1; 151,000 |
| store 5, seed 2 | 1,854 | 327-760 | 6-16 | 1,529 | 30 / 29 | 46% | 4.0 +- 0.1 | 15 | 32 / 32 | 2.00 | 0.24 | 0% | 0.2-0.7 | 2.0 | 33-41% | 38 | 143,000 | 7; 60,000 |
| store 5, seed 3 | 1,702 | 473-767 | 12-22 | 1,702 | 23 / 27 | 45% | 4.5 +- 1.1 | 15 | 32 / 32 | 1.81 | 0.62 | 1% | 0-1.1 | 2.3 | 13-49% | 39 | 158,000 | 11; 19,000 |
| store 0, seed 1 | 3,751 | 443-981 | 1-2 | 4,299 | 21 / 13 | 0% | 7.2 +- 0.7 | 14 | 15 / 32 | 1.35 | 1.59 | 1% | 0-0.3 | 21.2 | 70-84% | 16 | 158,000 | 5; 57,000 |
| store 0, seed 2 | 3,388 | 25-986 | 1-2 | 4,362 | 16 / 13 | 0% | 6.6 +- 0.8 | 14 | 15 / 39 | 1.36 | 1.35 | 0% | 0-0.1 | 17.0 | 69-78% | 11 | 100,000 | 8; 45,000 |
| store 0, seed 3 | 3,133 | 18-944 | 1-8 | 4,642 | 14 / 14 | 0% | 4.8 +- 1.1 | 14 | 15 / 32 | 1.32 | 1.63 | 0% | 0-0.2 | 18.0 | 71-83% | 13 | 121,000 | 8; 70,000 |

- **The winter is no longer a lottery.** The store world's lowest floor over 45 winters is 327
  bodies, with 2-22 lineages on the floors after the third winter (seed 1: 2-11, seed 3: 12-22). The control
  falls to 18, 25, 45, 117, 180, 196 and 214 in seven winters of 45, always with 1-2 lineages;
  e026's pilot at 0.75 fell to 23 in its seventh winter.
- **Size does not pay; density does.** The side ends at 4.0-5.6 against the control's 4.8-7.2,
  the cells per body at 8-15 against 14. The mass rises in seeds 2 and 3 (median 32 against 15)
  by density: the winners there are full 4x4 blocks at density 2 (16 cells, mass 32, a store of
  160, 2,500 steps of upkeep). The store is per unit of mass and the upkeep is per cell, so
  density buys store without upkeep, paying in the work of moving and the matter of a child.
  The survivors of a winter are not heavier than the summer's bodies in the batch (12/13, 30/29,
  23/27), unlike the side-8 pilot.
- **Two kinds of body in every seed.** A light sitting gut (6-10 guts on a 6x7 grid, density 1,
  mass 8-12; with a sensor in seeds 2 and 3) and a dense block (4x4 full, density 2, 5-10
  muscle, mass 17-31). Seed 1's light gut is alive for the whole run and holds the top place
  151,000 steps, with the blocks as second winners for 43,000-92,000 steps each; seed 3's gut
  with an eye lives 153,000 steps beside the blocks.
- **The cycle moves from the ground to the air.** Starvation deaths fall from 17-21 a step to
  2-6, so the control's winners eat 70-84% flesh (the starved, lying where the crowd is) and
  the store's 13-49%. The air holds 42-61 against 14-21 and rains 38-49 a step against 11-16;
  the fat holds 25-36% of the matter against 16-19%. The world holds 1,700-3,100 bodies
  against 3,100-3,750.
- **The tooth stays gone** in the `grow` world (0-1% bite in both), though the side-8 pilot at
  `store` 5 had it (1-21%). Kills are 0.24-1.22 a step against 1.35-1.63.

### The season at amplitude 1 (grow, store 5, seed 9, 100,000 steps; a pilot after the batch)

Where e026's world died at step 14,803 in its first winter, the store world lives through five:
2,074-3,961 bodies at the log steps, 51-65% on their fat. But each winter is a lottery: the
floors are 7, 24, 25, 14 and 7 bodies (in lineages of 5 or more) with 1-2 lineages, and the
top place changes every winter. A store of 1,300 steps of upkeep does not span a winter whose
sun is under a quarter for 6,700 steps.

## Conclusion

1. **The store exists: yes.** 45-75% of the bodies are at zero energy and alive on their fat at
   every season; starvation deaths fall from 17-21 a step to 2-6.
2. **The season goes past 0.5: yes.** The lowest winter floor over 45 winters is 327 bodies
   with 2-22 lineages on the floors, against the control's 18-45 with 1-2.
3. **Size begins to pay: no.** The side falls to 4.0-5.6 (the control 4.8-7.2) and the mass
   rises by density, not by cells: the store is per unit of mass and mass is free of upkeep,
   so a dense 4x4 block is the store's body. A store per cell would make the block and the net
   equal; a cost that falls with size is still the premise the world lacks.
4. **The world changes shape: yes.** Fewer bodies (1,700-3,100 against 3,100-3,750), the cycle
   through the air instead of the dead (rain 3x, the winners eat 13-49% flesh against 70-84%).

Kept, at `store` 5 (the next experiment's base runs it; `store` 0 stays the argument for
e029's world). The world holds two kinds of body in every seed (the light gut, the dense block)
and 2-22 lineages through a winter that was a lottery: by #19's count the law works. What it
does not do is make size pay; that needs a cost that falls with size, or food a small body
cannot reach. The season at amplitude 1 stands now, as a lottery of 7-25 bodies each winter (the pilot above): that winter is the next question, then the cloud on a mountain world (vision).
