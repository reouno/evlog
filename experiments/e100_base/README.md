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

(pending: the ladder is running)

## Conclusion

(pending)
