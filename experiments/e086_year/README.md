# e086: the year against a life (stage A and B at a shorter year, #93)

Date: 2026-09-19

## Purpose

P1 (#93, `vision.md` section 5) starts from one ratio: a grown body lives 500-570 steps, 1/20 of c1225's year of
11,880 steps, so no body meets a season. The year is a parameter of the sun, and the cheapest layer goes first
(`foundation.md`): does c1225 with its producers (draw d11) still pass stages A and B at a shorter year, and what is
its season to a body at each year: how long a place's lean spell lasts in steps, and how far the nearest place fed
in that month lies. The answers choose the year the bodies step of #93 is built on.

## Hypothesis

1. **Stage A holds.** A land cell follows the sun in about 35 steps and the sea holds its yearly mean, so at a
   year of 2,400, 1,200 or 600 steps the climate still holds 5 habitats of 2% of the cells, 3 of them wide, and
   10-50% of the cells change habitat in a year.
2. **Stage B holds, but for the fire's line.** Every rate is per step (or per update), so the producers stand as
   before; fire burns the same land per step and so a tenth as much per year at a tenth of the year.
3. **A lean spell fits in a grown life at a year of about 1,200.** A seasonal place is lean for about a third of
   its year, so its lean spell is 300-600 steps against a grown life of 500-570.
4. **A fed place is within reach in the lean month.** The terrain (heights, coasts) puts a place fed in a lean
   month within 25 cells of most lean places, 100 steps at a body's full speed.

## Method

- **Code.** e062's binary as `e086_year`, every law and rate unchanged, with one output added for the last year:
  `<prefix>_months.bin`, for each of 12 months every cell's mean temperature, its lowest temperature (the nights)
  and its growing index: on land what a grazed stand of grass regrows at per unit of it (light x warmth x the
  ground's fill x the light the wood leaves, `plants.rs`), in water the algae's.
- **Runs.** c1225 (`e062_producers/results/worlds/c1225.params`) with draw d11, `maps=1`, at `year` 11,880 (the
  control), 2,400, 1,200 and 600 steps; the day stays 74.7 steps. Years are multiples of 120 steps so that
  the stage's quarters and months fall on the sun's. Each run spins the climate up 20,000 updates and runs the
  producers at least 200,000 steps (17 to 334 years). `run.sh <year>`; the four at once on the Mac, 20:39-20:44 on
  2026-09-19 (about 5 minutes each, 0.35 core-hours in all).
- **Check.** The control's row equals e062's `pass/c1225_d11_row.csv` in every column but the three timings.
- **Measures** (`months.py`, bar 0.25; 0.1 and 0.5 as checks). A land month is *lean* when its growing index
  is under a quarter of the land's median yearly index. A place is *seasonal* when it is lean in 1-11 months; its
  *spell* is its longest run of lean months, in steps. The *distance* is the steps over land (4 neighbours) from a
  seasonal place in one of its lean months to the nearest land fed that month.

**Wrong if** the climate fails stage A at a shorter year (then the year cannot be moved alone), or a seasonal
place's spell does not shorten with the year (then the season is the ground's and not the sun's).

## Result

Stage A and B (each run's `_row.csv`; fire per 11,880 steps is the yearly share times 11,880 / year):

| year | habitats | wide | change | agree | grass / wood / algae | burnt a year | burnt per 11,880 steps | pass |
|---|---|---|---|---|---|---|---|---|
| 11,880 | 12 | 4 | 0.40 | 0.997 | 0.55 / 0.29 / 0.17 | 0.0145 | 0.0145 | all |
| 2,400 | 12 | 4 | 0.35 | 0.995 | 0.54 / 0.31 / 0.15 | 0.0020 | 0.0099 | all but fire |
| 1,200 | 12 | 4 | 0.35 | 0.992 | 0.54 / 0.32 / 0.15 | 0.0010 | 0.0099 | all but fire |
| 600 | 14 | 4 | 0.35 | 0.980 | 0.55 / 0.32 / 0.14 | 0.0004 | 0.0079 | all but fire |

The season to a body (`results/months.csv`, bar 0.25):

| year | always fed | seasonal | never fed | spell p50 / p90 (steps) | distance p25 / p50 / p75 (cells) | within 10 / 25 / 50 cells | lean month mean / low (C) |
|---|---|---|---|---|---|---|---|
| 11,880 | 62% | 22% | 15% | 3,960 / 7,920 | 4 / 9 / 16 | 58% / 91% / 99% | -9.6 / -24.9 |
| 2,400 | 62% | 25% | 14% | 800 / 2,000 | 4 / 10 / 19 | 53% / 87% / 97% | -10.8 / -24.8 |
| 1,200 | 62% | 31% | 7% | 400 / 1,000 | 6 / 15 / 37 | 38% / 67% / 81% | -11.4 / -24.8 |
| 600 | 22% | 76% | 2% | 50 / 400 | 8 / 19 / 39 | 33% / 61% / 83% | -2.3 / -15.9 |

- **The spell is a third of the year.** At every year down to 1,200 a seasonal place is lean for about four
  months running, so the spell shortens with the year: 3,960 steps at 11,880, 400 at 1,200 (500 and 400 at the
  bars 0.1 and 0.5). Its worst month grows nothing (under 5 C): the lean season is the winter, a month's mean at
  -11 C and its nights at -25 C.
- **At 600 the day and the year mix.** A month of 50 steps is shorter than a day of 75, so the months catch nights
  and days; three quarters of the land turns "seasonal" with spells of 50 steps. A year of eight days has no
  season a body could tell from the day.
- **The fed place is 9-15 cells away.** Over land, half the lean place-months have a place fed that month within
  9-15 cells. It grows from 9 to 15 between 2,400 and 1,200, where more of the land is seasonal (31% against 22-25%)
  and less is never fed (7% against 14-15%); why the never-fed land shrinks was not measured.
- **The day on land swings 25-35 C** between a month's mean and its lowest (the nights toward -30 C).
- Rain on land per step is the same at every year (0.31-0.36 mm a step); the producers' shares move by 0.01-0.03.

## Conclusion

1. Stage A holds at 2,400, 1,200 and 600: **yes**.
2. Stage B holds but for the fire's yearly line: **yes**. Per step the fire burns 0.8-1.0% of the land per
   11,880 steps against the control's 1.45%; a world with another year reads the line per 11,880 steps.
3. A lean spell fits in a grown life at 1,200: **yes**. The spell is 400 steps (p90 1,000) against a grown life of
   500-570; at 2,400 it is 800, longer than a grown life.
4. A fed place within 25 cells of most lean places: **partly**. 67% at 1,200 (91% at the control's year), the
   median 15 cells: beyond the eye's 9 cells, and twice what today's grown bodies travel in a life (8 cells).

The year for #93's bodies is **1,200 steps**: 16 days a year, the winter a spell a grown body can live through,
the producers as they stand. 600 is rejected (the season is lost in the day), 2,400 keeps the winter longer than a
grown life. Rows of `vision.md` this changes: E (life against the year: the lean spell at 1,200; travel against the
places: the distance), and a lesson in section 4 (the season is a third of the year at any year; the distance is
the terrain's). The bodies' side of the design is in #93.
