# e026 Weather

Date: 2026-09-03

## Purpose

Every law of the world so far is a fixed field: the sun the same every step, the rain the same
on every cell, the flow deterministic. e013-e025 end with one body winning every run, or two
since e025 (a tooth and a gut, half a density apart). The user's reading after e021 and again
after e025 (#24): a world with no weather is dull to watch, and fluctuation is the classic
reason several strategies coexist: no optimum holds long enough to win, and bodies with some
tolerance (a store, a range, a way to move) survive what the optimum does not.

The real world's premise: places have tendencies, not certainties. It rains where the clouds
are, and clouds drift; the sun has seasons. Written as two laws about the world, one about the
air's rain and one about the sun's rate, each run alone so that the effect is attributable.
Nothing names a trait.

## Hypothesis

1. **The world stands.** No death under either form at the amplitude the pilot picks; matter
   holds to 1e-6 (the weather moves matter, it makes none).
2. **The fluctuation is felt.** The cloud: the soil of the ridge follows the cloud (the
   correlation over the ridge's cells between the log of the rain weight and the soil, at the
   100,000-step dumps, above 0.3; e025: no cloud). The season: the population moves by 20% or
   more within a cycle, peak to trough (e025: cv 0.02-0.11 over a run). The cloud's measure
   was set after the pilot: the rain per height band, the measure first written (a cv above
   0.3), averages over 21 clouds and is 0.04-0.11 by construction; the cloud is 16 cells wide
   and the band 5,461 cells.
3. **No optimum holds.** Lineages alive at the end above e025's 1-5 (median over seeds
   higher than e025's 2.5), and the top lineage changes hands more often: two or more distinct
   winners over the second half in more seeds than the control (e025: seeds 1, 2, 4 had a
   second winner beside the first; the first held).
4. **Tolerance is selected.** The season: the fat per body (the store a body carries) is
   higher than the control's in the same state, or the trees (the world's store) are more.
   The cloud: bodies born in one band living in another (`movers`) are more than the
   control's, or the sensor comes back (e025: 0.4-6% of bodies), since food now differs in
   time and place.
5. **The hunter state of e025 (four seeds of four) is kept or changed**, recorded either way:
   the share of bodies with a bite and the kills per step.

## Method

Code: e025 (`experiments/e025_weight`) with argument 17 `weather` (0, `cloud` or `season`)
and argument 18 its amplitude. `weather` 0 is e025 byte for byte (checked on flat seed 9 for
10,000 steps: every output file identical, the log except its steps-per-second column), so
e025's `weight 1` runs (flat seeds 1-4, 500,000 steps) are the control at the same code.

- **The cloud.** The most the air can rain on a cell per step (e025: 0.01 on every cell of
  the flat world) is multiplied by a weight that varies over the world and over time. The
  weight is `exp(sigma z - sigma^2 / 2)`, lognormal with mean 1, where z is a unit Gaussian
  field: nodes on a lattice 16 cells apart (WEATHER_GRAIN, the terrain's grain), each an
  AR(1) process with a correlation time of 3,000 steps (WEATHER_SPAN: longer than a body's
  life, MAX_AGE 3,000, shorter than a run), read at every cell by bilinear interpolation on
  the torus (scaled back to unit variance) with the lattice drifting east at 1 cell per 200
  steps (WIND: a cloud crosses its own width in a span). At `sigma` 1 one cell in ten gets 2.2
  times its mean rain and one in ten a sixth. The air holds what the bodies breathe and empties
  every step (the caps add up to 82, the air holds 20-30), so the world's rain is what it was
  and only where it falls changes: rain falls into the soil, the soil grows the plant at the
  sun's rate and runs downhill. The field's nodes are written to `weather.csv` every 1,000
  steps and its spectrum to `terrain.json`; the log gets `cloud_std` (the weight's standard
  deviation over the cells at the log step).
- **The season.** The sun's rate on every cell is `0.01 (1 + a sin(2 pi t / 20,000))`
  (SEASON 20,000 steps: 25 cycles in a run, a cycle seven lifetimes). At `a` 1 the sun goes
  out at midwinter. The sun binds where the plant stands at the cap (the valley's lawn makes
  fruit at the sun's rate: 80% of the intake in e025) and not where the soil is scarce. The
  log gets `sun` (the factor at the log step).
- Compute: the cloud costs one pass over the cells per step (16,384 multiplications and the
  interpolation); the season one multiplication per cell. Neither shows in the step rate.

Pilot (flat seed 9, 200,000 steps, two threads each, up to five at once on the Mac, 30-45
minutes each at 75-120 steps per second): `cloud` 1, `cloud` 0.5, `season` 1, `season` 0.75,
`season` 0.5, to see whether the world stands and which amplitude is felt without killing the
world. The batch: `cloud` 1 and `season` 0.5, flat seeds 1-4, 500,000 steps, one thread each,
eight at once on the Mac (about 2 hours at e025's 53-123 steps per second), against e025's
`weight 1` runs.

Run (from the repo root):

    bash experiments/e026_weather/run.sh cloud 1 500000 1 2 3 4
    bash experiments/e026_weather/run.sh season 0.5 500000 1 2 3 4

Cost of the whole: five pilots (about 3 core-hours) and the batch (8 cores for 2 hours), all
on the Mac; the control is e025's batch.

Arguments: `<steps> <seed> <size> <widths> <cell_energy> <matter> <relief> <flow> <rain> <breath> <shade> <spill> <mutation> <eyes> <flesh> <weight> <weather> <amplitude>`;
the batch uses `500000 <seed> 128 0 0.02 8 64 0.1 flat 1 2 1 0.00390625 8 1 1 <weather> <amplitude>`.

## Result

### The pilots (flat seed 9, 200,000 steps, medians over the second half)

| weather | bodies (cv); peak over trough within the second half, every 1,000 steps | lowest count | lineages | fat per body; fat, share of the matter | trees | bodies with a sensor | bodies with a bite; killed per step | density (mean +- spread); cells per body | matter |
|---|---|---|---|---|---|---|---|---|---|
| cloud 1 | 2,860 (0.05); 3.0 | 1,002 | 6 | 7.5; 16% | 267 | 3.1% | 11%; 4.1 | 1.24 +- 0.35; 17.8 | 1.000000 |
| cloud 0.5 | 2,962 (0.12); 3.1 | 1,077 | 2 | 8.1; 17% | 242 | 10.2% | 14%; 4.4 | 1.10 +- 0.07; 19.9 | 1.000000 |
| season 1 | died at step 14,803, in the first winter | 0 | - | - | - | - | - | - | 1.000000 |
| season 0.75 | 4,561 (0.24); 580 | 23 | 1 | 6.0; 20% | 202 | 0.9% | 0%; 3.6 | 1.26 +- 0.27; 13.0 | 1.000000 |
| season 0.5 | 4,633 (0.02); 2.8 | 1,980 | 5.5 | 11.4; 37% | 152 | 0.1% | 0.1%; 1.1 | 1.47 +- 0.50; 11.5 | 1.000000 |

The season at amplitude 1 kills the world in its first winter (the sun under a quarter for
3,000 steps; a body's fat is its eater's store, not its own). At 0.75 the world lives through
ten winters but falls to 23-40 bodies in each: a lottery every cycle, one lineage. At 0.5 the
population moves 2.8 times within a cycle and never under 1,980, with 5-6 lineages alive. Both
clouds stand; at amplitude 1 the ridge's soil follows the cloud (correlation 0.35-0.56 at the
two dumps; the standing plant does not, 0.04: it is eaten as it grows) and six lineages are
alive; at 0.5, two. The batch runs `cloud` 1 and `season` 0.5.

### The batch (flat seeds 1-4, 500,000 steps; e025's weight-1 runs as the control)

Eight runs, one thread each, eight at once on the Mac: 2 hours (52-113 steps per second).
Report: `report.html`. Ranges over seeds, medians over the second half unless said.

| | cloud 1 | season 0.5 | e025 (the control) |
|---|---|---|---|
| Population (cv) | 2,053-3,923 (0.04-0.06) | 2,613-4,777 (0.05-0.11) | 2,407-4,726 (0.02-0.11) |
| Peak over trough within a season of 20,000 steps (median over cycles) | 1.16-1.31 | 2.09-2.54 | 1.16-1.52 |
| The ridge's soil follows the cloud (correlation over its cells at the dumps) | 0.42-0.54 | - | - |
| Lineages alive (median; at the end) | 2-4; 2-8 | 2-7; 1-6 | 1-5; 1-4 |
| Holders of the top place over the second half; longest hold, steps | 1-2; 43,000-251,000 | 1-14; 17,000-251,000 | 1-4; 35,000-251,000 |
| Fat per body; fat, share of the matter | 4.0-11.5; 8-29% | 5.0-10.5; 12-27% | 3.3-4.2; 6-14% |
| Trees | 173-726 | 256-528 | 291-646 |
| Bodies standing outside the band they were born in | 9-12% | 7-14% | 10-13% |
| Bodies with a sensor | 0.5-13.6% | 1.5-19.3% | 0.4-6.4% |
| Longest lineage with a sensor per body, steps | 1,000-99,000 | 5,000-125,000 | 1,000-10,000 |
| Bodies with a bite; bodies killed per step | 0-48%; 1.3-3.7 | 0-45%; 1.0-3.7 | 29-47%; 2.1-3.8 |
| Density per body (mean); its spread | 1.24-1.56; 0.12-0.46 | 1.06-1.67; 0.05-0.46 | 0.95-1.52; 0.10-0.47 |
| Cells per body; hard blocks per body | 10.4-25.3; 0.10-2.08 | 8.2-21.6; 0.03-2.48 | 7.5-17.9; 0.5-2.7 |
| Matter at the end over the start | 1.000000 | 1.000000 | 1.000000-1.000001 |

The cloud. The soil records it (correlation 0.42-0.54 on the ridge at every dump; the standing
plant does not, 0.00-0.05: it is eaten as it grows) and the bodies hardly do: the population
moves as the control's, the movers are the control's, the winners hold 43,000-251,000 steps
with 1-2 holders per run (control 1-4). Seeds 2 and 3 are e025's hunter state with a tooth
(biters 46-48%); seeds 1 and 4 kill without one (biters 0-0.5%, hard 0.10-0.15, 2.1-3.7
kills a step): heavy bodies (density 1.3-1.6, 14-25 cells) whose faces resist 2 or more break
the light bodies they walk into. Seed 1's late lineages are giants of 57 cells (19 muscle, 38
guts, density 2.0, mass 115) living 190 steps on the dead.

The season. The bodies halve each winter and double each summer (2.1-2.5 times per cycle;
control 1.2-1.5, the same lineage log at 1,000 steps). The top place changes hands 6 times in
seed 1 and 14 times in seed 2 over the second half, no holder lasting 29,000 steps (control:
1-4 holders, the longest 35,000-251,000); seeds 3 and 4 have one winner for 423,000 and
500,000 steps. Lineages alive 2-7 (seed 2: 6 at the end). Fat per body 5.0-10.5 (control
3.3-4.2). The state: seeds 1, 3, 4 hunt with a tooth (biters 18-45%), seed 2 kills without one
(1.3 a step, hard 0.03).

The eye. A lineage whose bodies carry a sensor each (sensor mean 1 or more in the lineage log)
lives 99,000 steps in cloud seed 3 (lineage 616: seventeen guts in a column, three wide and six
long), 72,000 in season seed 2 (lineage 1139: four muscle, nine guts, a sensor, density 2.0),
125,000 in season seed 3 (lineage 606, the winner: two hard, three muscle, twelve guts, a
sensor) and 96,000 in season seed 4 (lineage 208: sixteen guts, a sensor); in the control the
longest is 10,000 steps. Bodies with a sensor reach 10-19% of the population in three weather
runs (control at most 6.4%).

## Conclusion

1. **The world stands: yes.** No death in eight runs, matter 1.000000, population cv 0.04-0.11.
2. **The fluctuation is felt: yes, both.** The ridge's soil follows the cloud (0.42-0.54); the
   season moves the population 2.1-2.5 times within a cycle (control 1.2-1.5).
3. **No optimum holds: partly, the season only.** Season seeds 1 and 2: 6 and 14 holders of the
   top place over the second half, no hold over 29,000 steps; seeds 3 and 4 one winner. The
   cloud: 1-2 holders, as the control. Lineages alive 2-7 against 1-5, not a clear rise.
4. **Tolerance is selected: partly.** The eye: lineages with a sensor per body for
   72,000-125,000 steps in four runs of eight (control 10,000 at most), three of them under
   the season. Fat per body 5.0-11.5 against 3.3-4.2. Trees and movers unchanged.
5. **The hunter state: kept.** Kills 1.0-3.7 a step in eight of eight; in three runs (cloud 1
   and 4, season 2) the killer has no tooth: a dense face breaks a light one.

What it changes. Both forms are kept as laws of the world (`weather` cloud 1 or season 0.5;
0 is e025). The season is the one that does what #24 asked: everyone's income moves at once,
nothing escapes it, the lineage on top in summer is not the one on top in winter, and the eye
pays for the first time in the series (a sensor sees food and crowd up to nine cells away, and
where food moves in time and place, seeing it pays for the block). The cloud moves where the
rain falls and the soil records it, but a body lives on the dead and on the valley's fruit,
so a dry ridge costs a walking body little; it is felt by the world, not by the bodies. The
season's ceiling is a fact about the bodies: a body has no store of its own (its fat is its
eater's), so a winter of 3,000 steps without sun kills the world at amplitude 1 and makes a
lottery at 0.75.

Open: whether the turnover in two season seeds is coexistence or a lottery each winter; the
cloud on a mountain world (rain on the ridges only); the season's amplitude between 0.5 and
0.75; a store a body can spend (the fat is the eater's now). Next: #33 and #28, room: a bigger
grid at the same matter and small and large bodies, where the eye's range has space to matter.
