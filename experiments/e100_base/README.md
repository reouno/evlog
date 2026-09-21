# e100: the new default world and its control ladder (#112)

Date: 2026-09-21

## Purpose

e099 found that five laws had been rejected for a difference smaller than the difference between two
seeds of the same world, two of them thrown out together with a third that did the harm. The user's
decision (#112): the ones that are unreadable on every seed go back into the default world, and with
them the one kept for what it adds to the world rather than for what the count says.

This experiment **defines that world and measures its control ladder**, because every later judgement
is read against the ladder, not against the last result.

## The world

e097's world - e072's sets at the rates #88 kept, e073's crown yield, e075's tear and frail line -
plus:

| law | value | e099's reading, against its own control |
|---|---|---|
| e078: a crown damps what a body's heat reads, and cuts its drying | `shade_heat` 2.5, `shade_dry` 2.5 | kinds +0.04, kept to a place -0.40 |
| e079: a crown keeps the ground under it; wood rests in the cold | `crown_wet` 1, `wood_rest` 0.5 | -0.08, -0.12 |
| e081 (W1, W2): a body's water is part of the land's, and conserved | `unit` 9.4 | -0.12 / -2.06 / -0.31, -1.02 / -0.20 / -0.24 |

The ladder's own spread is 1.02 kinds at a census and 1.24 kept to a place (e092), so the first two
are inside it on every seed. The third is beyond it on one seed of three and is kept for what it adds:
the body's water becomes part of the land's ledger and is conserved, which makes where a body can
drink a property of the place (e081: "the code is right physics and stays as the base of the next
water step").

Left out, by the same decision: `fresh` 0.2 (e082 - the mechanism that levels the world, one line over
every band, the family of e097's widened birth rule) and the seed laws (e089, e090 - taken in the same
mouthful as the grass, and `seed_drift` carries the land's matter into the sea). Not carried in this
crate and decided with the 3D set: e093's light block, e095's spike and leg, e087's torpor.

## Method

The crate is e097's unchanged, so nothing about the laws themselves is new code; only `run.sh` differs.
**Checked**: with `shade_heat`, `shade_dry`, `crown_wet`, `wood_rest` and `unit` all 0 this crate and
e092's write identical `agents.csv`, `bands.csv`, `events.csv` and `lineages.csv` on c1225, life 99,
2,000 steps, and identical log rows but for e097's four measure columns and the timings.

The ladder: six seeds (9-14), 100,000 steps, a census every 1,000 from 36,000 - e092's own shape.

    (nohup bash experiments/e100_base/batch.sh > experiments/e100_base/results/batch.log 2>&1 < /dev/null &)

Read by `sweep.py` (e092's, pointed at this ladder): kinds at a census, kinds kept to a place, the
largest kind's and the largest line's share, the kills' share, bodies, travel and the jam, with the
median and the spread over the six seeds. What each reading used goes to `results/provenance.csv`.

**Stop early if:**

- `pop` < 500 at 20000

**Cost.** Six runs at once, one core each, 100,000 steps: about 1.5 hours on this Mac, six of twelve
cores left free. It buys the yardstick every later step is measured against; without it no result on
this world can be read.

## Result

Six seeds, 100,000 steps, every ledger at most 7e-14; the world stands (bodies 7,707-9,596 against the
old ladder's 7,860-9,470). Read by `sweep.py` beside e092's ladder, the same reader on both:

| seed | kinds at a census | kinds kept to a place | the largest line's share | travel |
|---|---|---|---|---|
| | old -> new | old -> new | old -> new | old -> new |
| 9 | 7.45 -> 5.98 | 4.75 -> 2.31 | 58.0% -> 46.3% | |
| 10 | 8.27 -> 5.57 | 4.65 -> 2.35 | 62.8% -> 61.4% | |
| 11 | 7.25 -> 6.59 | 4.47 -> 3.33 | 42.3% -> 58.2% | |
| 12 | 7.76 -> 5.45 | 4.24 -> 1.86 | 51.7% -> 62.5% | |
| 13 | 7.27 -> **3.67** | 3.75 -> **0.43** | 77.7% -> **99.1%** | |
| 14 | 7.61 -> 6.55 | 3.51 -> 3.00 | 44.9% -> 65.0% | |
| **median (spread)** | **7.53 (1.02) -> 5.77 (2.92)** | **4.35 (1.24) -> 2.33 (2.90)** | 51.7% -> 62.0% | **5.25 (2.0) -> 9.5 (27.8)** |

**The set costs 1.76 kinds at the median and every seed loses** (-0.66 to -3.60), so this is not one
bad seed. Kinds kept to a place fall by nearly half. **The spread nearly triples on both measures**,
which matters as much as the median: a ladder that spreads 2.92 kinds can read almost nothing.

**The signature is travel.** A grown body went 5.25 cells in the old world and 9.5 here, and the spread
goes from 2.0 to 27.8: on seed 13 a body travels 32.8 cells and **one line holds 99.1% of the land's
bodies**. That is e082's mechanism exactly ("the more a body moves, the more one line spreads over
every place") and e097's from the other side: whatever lets a lineage reach further levels the world.
The jam eases with it (births with no room 47% -> 39%), which e097 already showed is paid for in kinds.

A mechanism that would produce it: `shade_dry` and `crown_wet` together make a stand a place where a
body loses less water and the ground under it stays wet, so stands become watering places scattered
over the land and a body can cross the dry ground between them. `unit` is the other candidate - e099
read it alone on three seeds at -0.12 / **-2.06** / -0.31 - but on its own it shortened travel (e081's
tether), so it does not explain a doubling.

## Conclusion

**The new world is worse than the one it replaces, and it is not adopted as the default.**
`foundation.md` keeps e092's ladder as the control until a world beats it.

**What the result says about the rule, not just the world.** Decision rule 6 (`principles.md`) stands -
a law whose effect cannot be read should not be thrown away - but this run shows two things it did not
say:

1. **"Could not be read" has to mean "on the six-seed ladder".** e078's shade and e079's crown were
   each run on **one seed for 60,000 steps**; e099 read them there and found nothing, and that was not
   evidence of no harm. A law read on one seed has not been read.
2. **Laws that are each unreadable are not unreadable together.** The project already knows the
   converse ("a law added alone meets a world without its counterweights", e066-e072); this is the
   same sentence running the other way, and the set is 1.76 kinds worse than any of its parts measured
   alone.

What it does not say: nothing here rescues `crown_cool`, `history` or the widened birth rule, which
harm on their own; and nothing here says e093's light block or e095's spike and leg (both read on the
full six-seed ladder, -0.51 and -0.24) are harmful. Those two remain the candidates the rule was
written for.

**Open, and the cheapest way to close it**: which of the two halves did this. One more ladder with
`unit` 0 - the shade and the crown alone, six seeds - separates them in 1.2 hours.
