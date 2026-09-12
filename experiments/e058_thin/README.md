# e058 A thin world where places differ

Date: 2026-09-13 (probes done; the experiment proper is #69, not yet run)

## Status

The crate is built and two things are finished: the **thin-world probes** below, and the
**diversity measure** (`diversity.py`, #66). The experiment this crate is for - a thin world with
places that differ (#69) - is designed but not run. Read #68 before adding to it.

## Code

e057 with `foul` 0 (which is e056, which is e055) plus two changes:

- `agents.csv` carries `born_hard`, `born_muscle`, `born_sensor`, `born_digestive`: the blocks the
  body was **born** with. What a body holds now is its birth shape less what wear and teeth have
  taken, and counting damaged bodies as separate kinds inflates the diversity about twofold.
- The third column of `agents.csv` is renamed `born_size`. It has held `born_size` since e052
  despite being labelled `born_mass`; nothing read it, so nothing changes but the name.

No new law. `sun` (argument 33) is the only argument that moves in the probes.

Run: `bash experiments/e058_thin/run.sh <sun> <threads> <steps> <seeds>`

## The probes: what a thinner world does

**Why.** A body in e057's world eats the production of 3.35 cells and stands on 2.97: its own
footprint feeds it, so it has no reason to go anywhere, and every law about place gets averaged
away inside its 3-cell range (#68, rule 1). `sun` is a factor on every cell's regrowth, so
lowering it raises the ground a body must gather from without touching the body.

**Pilots** (seed 9, 40,000 steps, 3 cores, 5 minutes):

| sun | bodies | cells with a body on them | cells of production eaten per body | ratio | blocked |
|---|---|---|---|---|---|
| 1.0 | 2,940 | 56.4% | 4.0 | 1.3 | 58.0% |
| 0.5 | 1,784 | 41.0% | 7.7 | 2.0 | 54.6% |
| 0.2 | 724 | 21.0% | 20.9 | 4.4 | 33.5% |
| 0.1 | 307 | 9.0% | 46.7 | 9.7 | 18.2% |

**Probes at length** (seed 9, 100,000 steps; kinds are birth shapes, mix rounded to quarters,
rarefied to 120 bodies, #66):

| sun | bodies | ratio | travel in a life | travel by age (0-199 / 200-499 / 500-999 / 1,000+) | kinds | q1 | q2 | blocked | births refused | kills per body | floors |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 2,940 | 1.3 | 3.00 | 1.2 / 3.8 / 7.2 / 12.7 | 27.7 | 16.9 | 9.2 | 58.0% | 37.6% | 0.038 | 2,579-3,316 |
| 0.2 | 598 | 4.6 | 13.83 | 3.0 / 11.1 / 18.3 / 30.0 | 13.2 | 5.9 | 3.8 | 24.2% | 18.3% | 0.030 | 418-913 |
| 0.1 | 327 | 8.6 | 23.68 | 6.3 / 16.3 / 22.8 / 43.0 | 6.9 | 3.0 | 2.5 | 17.5% | 15.9% | 0.022 | 226-500 |

**What they say.**

1. **Bodies walk.** Travel rises three to five times at every age. The worry that a body would
   just mine the standing plant next door was wrong: at 9% coverage it still has to sweep.
2. **The jam clears.** Blocked moves 58% -> 17.5%, births refused for want of room 38% -> 16%.
3. **The world stands** through five seasons at every level tested.
4. **Diversity falls fourfold**, and predation with it. A uniform thin world has one way to make a
   living. Much of the crowded world's diversity was made by the crowd itself (#68, rule 2).

**Conclusion of the probes.** A thin world is not a law to keep; it is the first regime in which a
law about place can be crossed by a body. What it costs (diversity, predation) has to be paid for
by the places that differ. That experiment is #69.

## Not to repeat

- `AGENT_DUMP_INTERVAL` is 100,000, so a run shorter than that writes no body census: a pilot that
  needs travel or diversity has to be 100,000 steps. The thin world runs about 10 minutes for
  100,000 steps on one core, so this is cheap.
- The control has to be re-run whenever the experiment adds a column. e057's stored control had no
  `covered`; e058's needs `born_*`. Estimating the birth shape from young bodies (age under 50)
  overstated the control's diversity by a third (q1 21.6 against the measured 16.9).
