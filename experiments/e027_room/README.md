# e027 Room

Date: 2026-09-04

## Purpose

The user's reading after e025 (#33): the world is too crowded for the eye and for flight to
matter. Wherever a body goes it bumps into food or another body (contacts 0.3-0.7 per body
per step, 15-30% of the world under a body), so seeing far buys nothing and fleeing buys
nothing. e026's season made the eye pay for the first time; a world with room is its real
test. The issue's options are laws about the world: a bigger grid at the same matter, or less
matter per cell at the same grid.

Per the rule set after e026 (experiments must stay short; decide the content by what has to
be verified), this experiment asks only the fast question: does either change give the bodies
room? The slow question (does selection follow, does the eye win) is asked only if it does.

## Hypothesis

1. **A bigger grid at the same matter gives room.** 256x256 with 2 per cell (the matter of
   128x128 with 8): contacts per body per step fall to a quarter of e026's (0.1 or under),
   the share of the world under a body to a quarter (about 5%), and the knockout
   (`sense_used`, the share of a sensing body's decisions that seeing changes) rises.
2. **Less matter at the same grid gives room.** 128x128 with 2 per cell: the same.
3. **The world stands** in both (no death, the population steady).
4. **The cost of 256 is 4x per step** (the ground loops are per cell).

## Method

Code: e026 (`experiments/e026_weather`) unchanged, as `e027_room`; both worlds are e026's
arguments (`size` 256 or 128, `matter` 2). The base is the season world (`season` 0.5),
where the eye lives; the comparison is e026's season pilot on seed 9 (128, matter 8).

Two pilots on flat seed 9, 100,000 steps, all threads: `256 ... 2 ... season 0.5` (39
minutes) and `128 ... 2 ... season 0.5` (10 minutes). Measures from the log: contacts per
body per step, `cover` (the share of the world's cells under a body), `blocked` (the share of
moves that met a body), `sense_used`, bodies with a sensor, size, kills, regrowth; from
`places.csv` the population and cover by height band.

Run (from the repo root):

    ./target/release/e027_room 100000 9 256 0 0.02 2 64 0.1 flat 1 2 1 0.00390625 8 1 1 season 0.5
    ./target/release/e027_room 100000 9 128 0 0.02 2 64 0.1 flat 1 2 1 0.00390625 8 1 1 season 0.5

## Result

Seed 9, 100,000 steps; ranges over the log steps (every 10,000).

| | 256, matter 2 | 128, matter 2 | 128, matter 8 (e026) |
|---|---|---|---|
| Cells; matter at the start | 65,536; 131k | 16,384; 33k | 16,384; 131k |
| Sun per step (0.01 a cell) | 655 | 164 | 164 |
| Bodies | 5,500-7,900 | 1,560-2,320 | 2,660-4,850 |
| Cells per body | 20-25 | 12-20 | 11-20 |
| Regrowth per step | 86-120 | 15-23 | 17-25 |
| Contacts per body per step | 0.29-0.44 | 0.36-0.60 | 0.34-0.67 |
| Share of the world under a body | 13-16% | 10-12% | 19-22% |
| Under a body, by band (valley / slope / ridge, at 100,000) | - | 21% / 7% / 5% | - |
| Moves that met a body | 41-59% | 59-69% | 64-80% |
| `sense_used` | 0.16-0.22 | 0.17-0.23 | 0.21-0.25 |
| Bodies with a sensor | 0.9-3.7% | 0.8-10.9% | 0.1-1.7% |
| Bodies killed per step | 4-10 | 0.4-1.1 | 0.9-3.2 |
| Steps per second (12 threads) | 33-48 | 145-198 | 73-114 (2 threads) |

The bigger grid: four times the cells at the same matter is four times the sun, so the same
matter turns over four times faster (regrowth 86-120 a step against 17-25), and the bodies
take the room: 1.4 times as many, twice as big, 4-10 killed a step. Contacts fall by a third,
not to a quarter; `sense_used` does not rise. The quarter of the matter: half the bodies, not a
quarter, and they stand where the food is: the valley holds 65% of them with 21% of its cells
under a body (the whole of e026's world: 19-22%), the slopes and ridges 5-7%. Contacts per
body are e026's. Both worlds stand (no death; the 256 world's population falls from 7,900 to
5,500 over the run as its bodies grow).

## Conclusion

1. **A bigger grid gives room: no.** Contacts 0.29-0.44 (e026 0.34-0.67), cover 13-16%,
   `sense_used` unchanged; the extra sun fills the space with bodies.
2. **Less matter gives room: no.** Contacts 0.36-0.60; the bodies crowd the valley (21%
   under a body there) and leave the rest empty.
3. **The world stands: yes**, both.
4. **The cost of 256 is 4x: less than that, but too much.** 2-3x slower per step at 12 threads
   (33-48 against 73-114 at 2 threads); a 300,000-step run would take 2 hours alone.

What it changes. Room is not a property of the grid or of the matter: the bodies make their
own crowd where the food is, and free space stays empty. Contacts per body sit at 0.3-0.6 in
all three worlds. So #33's premise (the eye fails for want of room) is not settled by cells
or matter; if room is to be given, it is by spreading the food (the terrain and the rain, not
the grid), and the eye's test is the season's world as it is. #33 is closed with this note;
the 256 grid is kept as an argument, not as the world. The slow question is not run.

Next: #32, what a gut digests (a property of the gut material, cheap, in the season world),
then #28 (the body's grid: the cloud's giants of 57 cells sit near the ceiling of 64).
