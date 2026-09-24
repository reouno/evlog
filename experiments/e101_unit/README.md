# e101: the body's water alone, on six seeds (#113)

Date: 2026-09-25

## Purpose

e100 put three laws back into the world at once and lost 1.8 kinds on every seed. Two of them - e078's
shade and e079's crown ground and wood rest - are 2D stand-ins for what the 3D set makes real (a crown
that is a place). The third is not: **e081's `unit` (a body's water is part of the land's, and
conserved) is the ledger the 3D set's water axis is built on** (H3 in #5: ground water is at the floor,
so the higher a body feeds the further it is from its drink). It has never been read on six seeds -
e081 ran three (kinds -0.12 / -2.06 / -0.31 against its own control) - and we should know whether it
harms before building on it.

## Hypothesis

`unit` alone is inside the ladder's spread: e081 found it shortens travel (a body tethered to its
water), the opposite of e100's signature (travel doubled, one line over every place), so the harm in
e100 was the crown's half.

## Method

No crate: e100's binary and `run.sh`, with `shade_heat`, `shade_dry`, `crown_wet` and `wood_rest` set
back to 0 after its `back=` line, so the only law differing from e092's control is `unit` 9.4
(checked: a 300-step trial's row file carries the four at 0 and `unit` 9.4). e100's README shows the
crate reproduces e092's control bit for bit with all five at 0.

Six seeds (9-14), 100,000 steps, a census every 1,000 from 36,000 - the control ladder's shape, so it
is read straight against e092's ladder (and e100's beside it).

    (nohup bash experiments/e101_unit/batch.sh > experiments/e101_unit/results/batch.log 2>&1 < /dev/null &)

Read by `sweep.py` (e100's reader, pointed at this ladder): kinds at a census, kinds kept to a place,
the largest kind's and line's share, the kills' share, bodies, travel, the jam; and by
`analysis/replay.py` (the ways holding 5%, their shares, whether the largest way is the same, the
birth forms). Provenance in `results/provenance.csv`.

**Decides:** inside the spread (kinds at a census within 1.02 of 7.53 at the median, no seed collapsing
to one line) - `unit` goes into the world by decision rule 6 and H3 is built on it. Beyond it - `unit`
stays out, and H3 binds a body to the floor another way (a block in a cell with water drinks, one
without does not, no ledger).

**Stop early if:**

- `pop` < 500 at 20000

**Cost.** Six runs at once, one core each: about 1.2 hours on this Mac, six of twelve cores left free.

## Result

Six seeds, 100,000 steps; `analysis/audit.py` passes every run. **Seeds 9-11 are e081's `u9.4` runs bit for
bit** (182 log columns x 100 rows equal), so e081's three readings are three of these six. Read by `sweep.py`
beside the control ladder (e092's) and e100's set, the same reader on all three (`results/sweep.txt`):

| measure, median (spread) over six seeds | control | e100: unit + crown | **unit alone** |
|---|---|---|---|
| kinds at a census | 7.53 (1.02) | 5.77 (2.92) | **7.14 (1.63)** |
| kinds kept to a place | 4.35 (1.24) | 2.33 (2.90) | **4.34 (1.63)** |
| the largest kind's share | 14.8% | 27.0% | 15.6% |
| the largest line's share (highest seed) | 54.9% (77.7%) | 62.0% (99.1%) | 59.4% (70.4%) |
| kills' share of intake | 27.8% | 32.0% | 25.6% |
| births with no room | 46.8% | 39.1% | 45.2% |
| bodies | 8,809 | 8,512 | 7,722 |
| travel of a grown body | 5.2 (2.0) | 9.5 (27.8) | **3.0 (3.2)** |

Seed by seed, kinds at a census against the control: -0.12, **-2.05**, -0.31, -0.29, +0.57, -0.86. Five of
six are lower, and one (seed 10, e081's -2.06) is beyond the spread; the median is 0.39 lower, inside it.
Kinds kept to a place do not move (4.35 -> 4.34). No seed collapses: the largest line tops out at 70.4%, under
the control's own 77.7%.

**Replays** (`analysis/replay.py`, `results/replay.csv`): the ways holding 5% agree 0.66 (control 0.60, e100
0.38), their shares 0.77 (0.77), the largest way is the same in 4 of 6 seeds (2 of 6; e100 6 of 6), the birth
forms 0.038 (0.035). `unit` makes the world a little more convergent in its leading way, not less various.

**The signature is the tether, not the spread.** A grown body travels 3.0 cells against 5.2: its water is
where it drank, so it stays near it (e081). e100's set doubled travel (9.5, and 32.8 on its collapsed seed);
`unit` alone does the opposite, so the spreading that levelled e100's world is the crown's half - shade, the
crown's wet ground and wood's rest - or what it does together with `unit`.

## Conclusion

**Hypothesis confirmed: `unit` alone is inside the ladder's spread, and it is kept** (decision rule 6, by the
line set before the run). The default world is now e092's with `unit` 9.4, and **these six runs are its control
ladder**: kinds at a census 7.14 (spread 1.63), kept to a place 4.34 (1.63). The 3D set's water axis (H3: the
drink is at the floor, the food higher up) is built on this ledger.

What it does not say: that `unit` is free. Five seeds of six sit lower, and a law read as "inside the spread"
at -0.39 would be read as harm by a ladder half as wide; the rule keeps it because the spread cannot tell, not
because the cost is shown to be zero. And the crown's half is not shown to harm alone - only that the harm in
e100 is not `unit`'s. That half is a 2D stand-in for the crown the 3D set makes real, so it is not re-run here.

`vision.md`: G (water) - a body's water is part of the land's; F rows - the ladder and the replay numbers are
this batch's; section 5 - #113 done, #114 next.
