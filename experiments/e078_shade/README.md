# e078: the shade of a crown (#91 step 1)

Date: 2026-09-19

## Purpose

#91 asks whether a stand of wood is a refuge a lawn cannot hold. Named together (#87): **a refuge pays
when the season takes the lawn away (A) and the stand keeps what the lawn loses (B).** e077 found (A):
from 20 degrees of latitude out the season takes the lawn twice a year, in winter by food and in summer
by heat (35-38 C against the heat law's top of 30 C). It found no (B): a stand is within 1-5 C of the
lawn beside it. This step builds (B) with the heat first, as the issue agreed: the crown damps the day
a body feels, and cuts the dry air it loses water to.

## Hypothesis

1. **The crown keeps the heat off.** At `shade_heat` 2.5 or more, in the hot quarter the stands at 10-30
   degrees charge a body under half the degrees over 30 C that the lawn in the same band does (the
   control: within a quarter of each other).
2. **The stand fills when the lawn empties.** The land's bodies in stands rise at the solstices against
   the equinoxes (a ratio over 1.25, where e077 had them flat within 9%), so the land's crowd dips less
   at the solstices.
3. **The dry cut alone makes a place, not a refuge.** `shade_dry` alone raises the stands' bodies in every
   quarter by about the same share; the seasonal rise of (2) needs the heat.
4. **A line follows the season.** Under the centre, a lineage holding 5% of the land's bodies (over all
   censuses) has more bodies in stands at the solstices than at the equinoxes by more than any line
   of the control, and its bodies on the mid-latitude lawn return in the equinoxes. (Set after reading
   the measure on e077's runs and before the search: there the line with the largest ratio already has
   0.90 / 1.54 / 1.26 on seeds 10 / 11 / 9, since lines rise and fall over the two years read.)
5. Stage C's measure does not fall at the centre: kinds at a census and kinds kept to a place at or over
   e075's kept runs (7.67 and 4.78, seeds 9-11, 100,000 steps).

## Method

The e077 binary with the two rates, read on the body's side in `refresh_air` (the climate and the
producers are e077's, the settled world is the same):

- `shade_heat` (k): what a body's heat reads on a cell is `T - min(1, k x shade) x (T - T_day)`, with
  shade = wood / (wood + WOOD_HALF) (the share of the light the crown takes, as for the grass) and
  `T_day` the cell's running mean over a day (e073's).
- `shade_dry` (k2): the dryness the soft faces lose water to is cut by `min(1, k2 x shade)`.

Both 0 is e077 exactly (the log of a 2,000-step run of seed 9 is byte-identical to e077's, timing
columns aside). `bands.csv` gains `felt`, `over` and `under`: what a body's heat read on a band's cells
and its mean degrees over 30 C and under 15 C, over every climate update since the last row (a row
alone sees three hours of the 75-step day).

**Search** (seed 9, 60,000 steps, a census every 1,000 steps from 36,000, as e077): the control (0, 0)
and ten candidates of (k, k2): heat alone 1 / 2.5 / 5, dry alone 2.5 / 5, both 1/1, 2.5/2.5, 5/5, 1/5,
5/1. Today's stands (wood 2-3 a cell) have a shade of 0.33-0.43, so k 2.5 takes most of the day's swing
in a stand and k 5 all of it; thin wood (0.1-1) gets up to a fifth.

    (nohup bash experiments/e078_shade/batch.sh search 60000 9 > experiments/e078_shade/results/search.log 2>&1 < /dev/null &)

11 runs on 11 cores, one thread each, about 40 minutes on the Mac. Then the centre on seeds 9-11 at
100,000 steps (3 cores, about 50 minutes), against e075's kept runs.

The 3-seed run of the centre was **not run**: no candidate made the stand fill in the bad quarter
(hypothesis 2), so there is no centre to keep and nothing for stage C's measure to judge.

## Result

**The check.** With both rates 0 the log of a 2,000-step run of seed 9 is byte-identical to e077's.
Matter drifts by at most 3.5e-14 over the 11 search runs. Each run took 32-39 minutes (11 at once).

**The search** (seed 9, 60,000 steps; `sweep.py`; bands after the first year, censuses 36,000-60,000).
"Over" is the mean degrees over 30 C a body's heat reads, in each band of 10-30 degrees in the quarter
its lawn is hottest. "S/E" is bodies at the solstices over bodies at the equinoxes.

| k | k2 | over, stand | over, lawn | stands' bodies S/E | land's bodies S/E | stands' bodies a quarter | land bodies | deaths: thirst / cold | kinds / placed |
|---|---|---|---|---|---|---|---|---|---|
| 0 | 0 | 17.4 | 19.0 | 0.97 | 0.69 | 18-20k | 4,138 | 48% / 1.8% | 7.08 / 4.44 |
| 1 | 0 | 13.5 | 18.9 | 1.00 | 0.70 | 16-17k | 3,631 | 47% / 1.5% | 7.16 / 4.00 |
| 2.5 | 0 | 9.4 | 18.9 | 1.04 | 0.71 | 18-20k | 4,007 | 47% / 1.3% | 7.64 / 4.72 |
| 5 | 0 | 8.5 | 18.7 | 0.99 | 0.67 | 17-18k | 4,163 | 46% / 1.1% | 7.48 / 4.36 |
| 0 | 2.5 | 17.4 | 19.0 | 1.00 | 0.69 | 16-17k | 4,033 | 45% / 1.7% | 8.44 / 4.00 |
| 0 | 5 | 17.4 | 19.0 | 0.99 | 0.71 | 23-25k | 4,840 | 46% / 2.2% | 7.36 / 4.80 |
| 1 | 1 | 13.5 | 18.9 | 1.00 | 0.72 | 21-22k | 4,283 | 45% / 1.6% | 6.92 / 3.80 |
| 1 | 5 | 13.5 | 18.9 | 1.04 | 0.78 | 22-25k | 4,752 | 42% / 1.9% | 6.32 / 3.24 |
| 2.5 | 2.5 | 9.4 | 18.9 | 1.02 | 0.73 | 15-17k | 3,422 | 45% / 1.5% | 7.12 / 4.04 |
| 5 | 1 | 8.5 | 18.8 | 1.03 | 0.72 | 13-15k | 3,216 | 43% / 1.3% | 6.84 / 3.84 |
| 5 | 5 | 8.5 | 18.8 | 0.96 | 0.67 | 14-15k | 3,504 | 45% / 1.1% | 7.28 / 4.40 |

- **The crown keeps the swing off, not the heat.** At k 5 a stand's degrees over 30 C in the hot
  quarter fall from 17.4 to 8.5, and cold deaths from 1.8% to 1.1% of deaths. But fully damped, what a
  body feels is the day's mean, and that is over the band: a stand at 20-30 N in the north's summer is
  still 6.8 degrees over 30 C, a day's mean of about 37 C. In the tropics the lawn reads 13-19 degrees
  over 30 C in every quarter; the heat law's band sits well below where the bodies live (thirst is
  42-48% of all deaths in every run).
- **The stands empty in the bad quarter with the lawn.** At 20 N a stand holds 0.10 bodies a cell in
  the equinoxes and 0.03 in the north's summer without shade, 0.04 at k 5, 0.05 at k 5 / k2 5. No run
  moves the stands' S/E ratio out of 0.96-1.04 or the land's out of 0.67-0.78.
- **The dry cut moves the stands alike in every quarter, but not in order.** k2 5 alone puts 23-25k bodies
  a quarter in stands against 18-20k, the same in every quarter (S/E 0.99), and 17% more bodies on the
  land (4,840); k2 2.5 alone puts 16-17k, and with the heat damper the stands hold 14-25k in no order
  of k2. On one seed the dry cut's size is not read.
- **No line follows the season.** Every run's largest line has a stand S/E of 0.92-1.25, inside the
  control's own spread (0.90-1.54 on e077's three seeds).
- Kinds on this one seed run 6.3-8.4 at a census and 3.2-4.8 kept to a place, around the control's
  7.08 / 4.44, with no order by k or k2.

## Conclusion

1. **Yes at k 5, borderline at 2.5**: the stand's degrees over 30 C are 0.45 and 0.50 of the lawn's
   (control 0.92).
2. **No**: the stands' bodies are flat by season at every (k, k2) (S/E 0.96-1.04), and so is the land's dip.
3. **Partly**: where the dry cut moves the stands' bodies it moves them alike in every quarter (a place,
   not a refuge), but k2 2.5 lowers them and k2 5 raises them, so the size is not read on one seed.
4. **No**: no line follows the season more than the control's lines do.
5. Not judged: no centre was run on three seeds.

**The crown's shade as built here does not make a refuge**, in the conditions of this world (c1225, a
75-step day that swings a cell about 20 C around its mean, the heat law's comfort band of 15-30 C, a
grown body living about 1/20 of a year). Damping the day toward its mean cannot cool a place whose
mean is itself over the band, and in the bad quarter the stand's day's mean is: at 20-30 N in the
north's summer it is about 37 C. What the lawn loses in summer is a mean the crown does not change.

For #91 this moves (B) from the swing to the mean: either the crown takes its share of the sun's heat
(a stand cooler on average, not only steadier), or the heat law's band is out of step with the
climate the bodies live in (the tropics read 13-19 degrees over it in every quarter, and thirst is
nearly half of all deaths). Which to test first is the next decision; the two rates stay as arguments
(both 0 by default).

**Correction (same day, `budget.py`).** "Degrees over 30 C" is the cell's reading. A body holds 22-29 C in
every zone and season by sweating: what the heat costs it is water, 0.002-0.0045 of its fill a turn where it
is warm, as much as wet ground gives to drink. That, not the band's place, is why thirst is nearly half of all
deaths and why stands (the wettest ground) are crowded homes. #91's next step is designed as a cycle in
`balance.md` section 13.
