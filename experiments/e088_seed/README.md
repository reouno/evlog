# e088: grass that keeps part of its growth as seed (#99 S, stage B)

Date: 2026-09-20

## Purpose

P2 (#99, `vision.md` section 5) gives the world a food web. Its first law, S, is on the producers' side: grass
puts a share of its growth into seed that lies on the ground, waits through cold and dry spells, and becomes
the spring's grass. Later (e089) only a body with a hard tip takes it. The cycle (what S takes, what refills it,
what limits it, the balance expected, how it is wrong) is written in #99 and not repeated here.

A law of the producers makes a new settled world, so stage B is run first (`foundation.md`): the producers
alone, no bodies. It answers whether seed makes a bank worth eating, where and when, before any body is
built to eat it, and whether stage B still passes.

## Hypothesis

With `seed_share` 0.2 (0.1 and 0.4 around it), against the control (0, today's default world):

1. **A bank by season.** Seed on the land is the largest in each hemisphere's lean quarter (winter at
   mid-latitudes), when grass stops growing, and there it is at least a third of the grass standing; where
   grass grows all year it is about a tenth.
2. **The spring's grass comes from seed.** At 30-60 degrees, in each hemisphere's spring quarter, a quarter or
   more of the grass added (grown as leaf or sprouted) is seed that sprouted.
3. **The grass holds.** Grass standing on the land (leaf) within 15% of the control's at 0.2, and grass with
   its seed not below it.
4. **Stage B still passes** (`foundation.md` section 3): grass, wood and algae each 5% or more of the standing
   matter, none dies out, fire burns 1-20% of the land a year, matter is conserved.

**Wrong if** the seed bank stays under a few percent of the grass everywhere (seed sprouts as fast as it is
set, so there is nothing to eat), or the grass fails.

## Method

e082's crate (today's default world) with the law in `plants.rs`, two keys, both on the world's side:

- `seed_share`: grass's growth goes `1 - seed_share` to leaf and `seed_share` to `seed` on its cell.
- `sprout` (0.001): a share of the seed sprouts into grass a step, times warmth x the ground's fill (the
  growth's two factors). Seed rots into the soil at a tenth of the litter's rate (also warmth x fill) and does
  not burn. In a place warm and wet all year a grain waits about 1,000 steps and seed stands at about a tenth
  of the grass; where it is cold or dry it waits for the warm and the wet. `sprout` is a first value, not
  searched.

At `seed_share` 0 the world is e082's and its settled world's hash is e082's. A unit test checks the law
(cold seed waits, warm seed sprouts and rots, matter kept, the file keeps the seed).

Measures, no law: the log gains `seed` (on the land), `seed_set` and `sprouted` (a step); `bands.csv` (every
1,000 steps, by 10-degree band and wood class) gains `seed` and `sprouted`.

**Runs** (c1225 with e062's draw d11, life 9): each builds its settled world (e062's 200,000 steps of
producers after the climate's spin-up; the control's is read) and then runs 2 years (23,760 steps) with no
bodies (`start` 0). Four runs, named s<seed_share>: s0, s0.1, s0.2, s0.4.

    (nohup bash experiments/e088_seed/batch.sh > experiments/e088_seed/results/batch.log 2>&1 < /dev/null &)

4 runs on 4 cores of the Mac, one thread each, about 7 minutes. `sweep.py` reads them.

## Result

4 runs, 6.4 minutes each (the settled world 5.5 of them; the control read e082's). Numbers are a land cell's
means over the 2 years; `sweep.py` prints them, `results/sweep.csv` and `results/sweep_bands.csv` hold them.

**The check.** At `seed_share` 0 the run read e082's settled world by its hash, and its matter drifts by 3e-14.
The unit test passes.

| run | grass (leaf) | seed | seed / grass | set / sprouted a step | wood | soil on land | fire a year |
|---|---|---|---|---|---|---|---|
| s0 | 1.140 | 0 | 0 | 0 / 0 | 66,020 | 314,695 | 1.9% |
| s0.1 | 1.147 | 0.244 | 0.21 | 6.4 / 6.1 | 61,937 | 283,799 | 1.8% |
| s0.2 | 1.129 | 0.481 | 0.43 | 12.6 / 12.0 | 60,654 | 268,066 | 1.0% |
| s0.4 | 1.118 | 0.959 | 0.86 | 25.2 / 24.0 | 55,162 | 233,118 | 1.5% |

**1. A bank, but not a seasonal one.** At 0.2 the seed on a land cell hardly moves over the year: at 40 N
0.43-0.46 in every quarter, at 0 degrees 0.54-0.55. Setting and sprouting both follow warmth x water, so the
bank settles at the grass's growth over the sprout rate, the same in every season. What moves is the grass:
it dies back in the cold while the seed waits. So seed is the larger food in the lean quarter only relative to
the grass: seed / grass in the winter quarter is 0.75 at 40 N, 1.44 at 50 N, 0.54 at 40 S and 0.74 at 50 S,
against 0.49-0.57 in summer there. In the tropics it is 0.29-0.33 all year, not the tenth expected (the
ground's fill slows the sprouting). Holds in part: at least a third of the grass in the lean quarter, but no
peak in the seed itself.

**2. No spring flush: fails.** The sprouted share of the grass added is 0.17-0.22 in every band and quarter at
0.2 (0.09-0.11 at 0.1, 0.36-0.44 at 0.4): it equals `seed_share`. The seed does not wait for spring; it
sprouts about as fast as it is set, in the same season.

**3. The grass holds.** Leaf standing is 0.99 of the control at 0.2 (0.98 at 0.4), leaf and seed 1.41. The
seed's matter comes out of the soil (land soil -15%) and the wood (-8%, -16% at 0.4).

**4. Stage B still passes, fire at its edge.** At 0.2 grass (with seed) holds 64% of the standing matter, wood
22%, algae 14%; none dies out; matter drifts by at most 5e-14. Fire burns 1.0% of the land a year against the
control's 1.9%; it does not follow the share (1.8%, 1.0%, 1.5%), so two years of strikes are noisy, but 0.2
sits on the line of 1%.

## Conclusion

Partly. Seed makes a bank worth eating: at 0.2 it is 0.43 of the grass on the land, everywhere grass grows,
and more than the grass in the lean quarter at 50 degrees. The grass does not lose, and stage B passes. But
the bank is steady, not seasonal: it does not pile up at the end of the growing season or flush in spring.
The hypothesis's "wrong if" (the bank under a few percent of the grass) is not met without grazers; whether
grazers take the leaf before it sets seed is stage C's question.

For stage C (e089), `seed_share` 0.2 as #99 planned: it passes stage B, and 0.4 costs wood twice as much.
A seasonal pulse would need seed that sprouts on a cue other than the growth's own (after a cold spell, say);
it is not needed for what #99 asks of seed (a food behind a tooth that outlasts the grass in a lean season),
and is left out.

`vision.md` rows changed: B (kinds of plant food: seed exists on the producers' side, not yet a food), and
section 4 (the seed bank follows the growth's factors, so it does not keep time).
