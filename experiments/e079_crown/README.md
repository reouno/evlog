# e079: a crown that keeps its ground (#91 step 2)

Date: 2026-09-19

## Purpose

#91 asks whether a stand of wood is a refuge a lawn cannot hold. e078 read the land by a body's water
budget: heat is paid in water, water sets where land bodies live, and a stand is a crowded home because
it grows on the wettest ground, not because of its crown. In the mid-latitude summer the lawn and the
stand run dry together. `balance.md` section 13 designed the refuge as a cycle (agreed 2026-09-19):

- **S1** the crown keeps its ground wet: it cuts the evaporation from the ground under it by its shade.
  It takes vapour from the air above the stands (less rain may fall downwind); it refills the stand's
  own ground, and wood grows with the ground's fill, so a stand keeps the ground it needs. The ground's
  capacity and fire limit it (wetter ground burns less).
- **S2** wood rests in the cold: wood's death follows warmth as its growth does. It places stands at
  20-50 degrees, next to the seasonal lawns (R4); the grass under a crown loses light, so the lawn
  shrinks where stands spread, and the mosaic's share is set by wet ground and fire.
- **S3** the crown takes its share of the sun's heat off what a body feels (bodies only: step 3).

S1 and S2 change the producers, so they make a new settled world. This step builds them and reads the
producers alone, as stage B did (#75): where stands stand, the ground's fill by season, and the rain.
The bodies come in step 3, only if the producers' side of the design holds.

## Hypothesis

With S1 and S2 together (`crown_wet` 1 or 2, `wood_rest` 1), against the control (both 0, e078's world):

1. **Stands next to the seasonal lawns (R4).** Stand cells (wood 1 or more) at 20-50 degrees of
   latitude, both hemispheres, at least double, and at least half of the lawn there (wood under 0.1)
   lies within 25 cells (a grown body's travel in a life) of a stand. (The control turned out to hold
   the second clause already, 0.51, so only the first discriminates.)
2. **A wet floor in the bad season (R2's water).** A stand's mean ground fill at 20-50 degrees in its
   hemisphere's summer quarter is 0.6 or more, against the control's 0.43.

   *Corrected after the control's run and before any candidate's result.* As first written the line
   was 0.4, from section 13's "a stand's summer fill stays under 0.4". That fill is the body's water
   (`budget.py`'s `fill`), not the ground's: under e078's bodies the mid-latitude stand's ground in
   summer holds 0.47 while its bodies hold 0.20. By that budget (drink 0.005 x the ground's fill; cooling
   0.0039 a turn; dry air 0.00245 x (1 - fill)) a body's summer water closes at a ground fill of 0.85,
   and at 0.6 if S3 halves the cooling. So 0.6 is the line for the producers' part; section 13's 0.4 on
   the body's fill stays for step 3.
3. **The counterweights hold** (the design is wrong if not): the lawn at 20-50 degrees keeps at least
   half the control's cells, and the rain on it falls by less than a fifth.
4. **The parts.** S2 alone moves where stands stand and not the summer fill of a stand; S1 alone wets
   the stands there are and adds few at 20-50 degrees. Read to know which part does what; the set is
   what is judged.

## Method

e078's crate with two rates on the world's side, both 0 being e078's world (the same settled-world file
is read, the key leaves the hash at 0):

- `crown_wet` (S1, `climate.rs`): a land cell's evaporation times `1 - min(1, crown_wet x shade)`, with
  shade = wood / (wood + WOOD_HALF), the share of the light the crown takes (as for the grass).
- `wood_rest` (S2, `plants.rs`): wood's death times `1 - wood_rest x (1 - warmth)`, with the warmth
  its growth reads (0 at 5 C, 1 from 20 C).

Measures, no law: `bands.csv` gains `fill` (the ground's mean fill) and `rain` (mm a cell over the row);
`cell_map` 1 writes `_cells.bin`, every cell's ground fill, temperature and rain by quarter over the run
and its wood and grass at the end; the settled world's build prints its wood a year.

**Producers alone** (c1225, e062's draw d11): each candidate builds its settled world (e062's 17 years of
producers after the climate's spin-up) and then runs 2 years (23,760 steps) with no bodies (`start` 0).
Five candidates, named w<crown_wet>r<wood_rest>: the control w0r0, S2 alone w0r1, S1 alone w1r0, the set
w1r1 and the set with a stronger floor w2r1.

    (nohup bash experiments/e079_crown/batch.sh alone > experiments/e079_crown/results/alone.log 2>&1 < /dev/null &)

5 runs on 5 cores of the Mac, one thread each, about 6 minutes (the settled world's build is 5.3 minutes).
`sweep.py` reads them. The five asked for two more points, to pick the world for step 3 (`batch.sh alone2`,
2 cores, 6 minutes): a half rest (w1r0.5) and a floor between 1 and 2 (w1.5r1).

## Result

**The check.** With both rates 0 a 2,000-step run with bodies on seed 9 reads e078's settled world file and
its log (timing aside), bands (e078's columns) and census are byte-identical to e078's. Matter drifts by
at most 2.3e-14. Two unit tests cover the laws: a crown of shade 1/2 at `crown_wet` 1 halves its ground's
evaporation; at `wood_rest` 1 cold wood does not die and warm wood dies at the full rate.

**The producers alone** (c1225, two years after the settled world; `sweep.py`). Stands: wood 1 or more;
lawn: wood under 0.1; "mid" is 20-50 degrees in both hemispheres; the fill is the ground's, in the
hemisphere's summer / winter / equinoxes; the lawn's rain is on the control's mid lawn cells.

| run | crown_wet | wood_rest | stands | stands mid | lawn mid | stand's fill S/W/E | lawn's fill S/W/E | rain, ctl lawn | rain, land | burnt a year |
|---|---|---|---|---|---|---|---|---|---|---|
| w0r0 | 0 | 0 | 18,924 | 2,165 | 36,237 | 0.43/0.87/0.68 | 0.16/0.37/0.29 | 1,885 | 3,689 | 1.9% |
| w0r1 | 0 | 1 | 50,558 | 19,745 | 18,470 | 0.32/0.69/0.55 | 0.10/0.25/0.19 | 1,885 | 3,689 | 1.3% |
| w1r0 | 1 | 0 | 26,279 | 6,870 | 35,066 | 0.59/0.93/0.80 | 0.15/0.36/0.28 | 1,882 | 2,902 | 1.9% |
| w1r0.5 | 1 | 0.5 | 40,493 | 14,873 | 25,971 | 0.58/0.90/0.78 | 0.12/0.29/0.23 | 1,837 | 2,687 | 1.1% |
| w1r1 | 1 | 1 | 55,239 | 23,858 | 18,404 | 0.59/0.87/0.77 | 0.09/0.24/0.18 | 1,694 | 2,421 | 1.3% |
| w1.5r1 | 1.5 | 1 | 42,954 | 19,445 | 20,674 | 0.75/0.87/0.83 | 0.07/0.18/0.13 | 969 | 930 | 1.8% |
| w2r1 | 2 | 1 | 34,119 | 14,518 | 30,601 | 0.98/0.99/0.99 | 0.03/0.10/0.07 | 473 | 282 | 1.2% |

Rain in mm a year; the sea gets 372-386 in every run. Land: 110,625 cells, of them 50,845 at 20-50 degrees.

- **S2 places the stands.** Alone it multiplies the mid stands by 9 and halves the mid lawn; with S1 at
  rest 0.5 by 6.9, keeping 72% of the lawn. At rest 1 growth and death both follow the warmth, so the
  warmth cancels out of where wood settles and only light and water decide: stands reach the cold south
  (the -60 to -50 band 66-69% stands, none in the control), settling slowly (w1r1's mid stands still fall
  0.4% a year after 19 years; w1r0.5 is flat). S2 alone dries the stand's summer floor (0.43 to 0.32): the
  stands spread onto drier ground.
- **S1 wets the floor to about 0.58, and no further without the rain.** At `crown_wet` 1 a mid stand's
  summer floor is 0.58-0.59 whatever the rest. Past 1 the floor rises only as the land's rain falls: 0.75
  at 1.5 with the lawn's rain halved (-49%), 0.98 at 2 with the land's rain down 92% and a third of the
  land at full fill (33,575 cells against 330), its rain running off to the sea.
- **Why: the land's rain is its own evaporation.** The sea rains 386 mm a year and the tropical land 8,900;
  with a wind of 0.1 cells an update the sea's vapour barely reaches the land. So every millimetre a crown
  keeps in its ground is a millimetre less rain. At `crown_wet` 1 the tropics (20 S-10 N) lose 28-35% of their rain,
  yet at w1r0.5 the ground's mean fill rises in every band from 60 S to 50 N (0.40 to 0.52 at 30-20 S): at rate 1
  the land keeps its water and turns it over slower; past it the cycle leaks to the sea.
- **Fire** falls where stands spread (1.9% of the land a year to 1.1-1.3%): wetter ground and less grass.

**The hypotheses** (the set as named, w1r1; the added points in brackets):

1. Stands next to the seasonal lawns: **yes**. Mid stands x11 (x6.9 at w1r0.5). The "near" clause does not
   discriminate: the control already has 0.51 of the mid lawn within 25 cells of a stand (0.82-0.90 in the others).
2. A wet floor in the bad season: **no**. 0.59 against the line of 0.6 (0.58 at w1r0.5); only w1.5r1 (0.75)
   and w2r1 (0.98) pass, where the lawn's rain falls by half or more.
3. The counterweights: **yes at w1r1, narrowly** (the mid lawn keeps 51% of its cells, its rain falls 10%),
   **yes at w1r0.5** (72%, 3%), **no** at w1.5r1 and w2r1 (rain on the lawn -49% and -75%).
4. The parts: **partly**. S2 alone moves the stands and not the floor's wetness up (it dries it); S1 alone
   wets the floor but also triples the mid stands (6,870), more than "few".

## Conclusion

The producers' half of the refuge holds except its water. Wood that rests in the cold puts stands beside
the seasonal lawns (x7-11 at 20-50 degrees), and at `wood_rest` 0.5 the lawn keeps most of its ground.
A crown that keeps its ground wet lifts a mid-latitude stand's summer floor from 0.43 to 0.58 and stops
there: in c1225 the land's rain is the land's own evaporation, so what a crown keeps is taken from the rain,
and past `crown_wet` 1 the land's water cycle drains into the sea. `balance.md` section 13's S1 assumed the
water a crown saves stays under it; on this climate it is the rain's source. The design did not account for this.

What it changes for #91: a body's summer water in a stand closes at a floor of 0.58 only if the crown
also halves what it pays to cool (e078's budget), so step 3 turns on S3. The world for it is w1r0.5
(the same floor as w1r1 with the lawn at 72%, the lawn's rain at -3% and a settled forest); its cost
is a quarter less rain on the land (3,689 to 2,687 mm a year) with a wetter ground. Both rates stay as
arguments, 0 by default.

Conditions: c1225 (a slow wind, a land that rains its own water), one bucket of ground (150 mm) that
plants read and do not drink, e062's draw d11, a settled world of 17 years.
