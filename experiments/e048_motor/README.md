# e048 Moving takes a motor

Date: 2026-09-11

## Purpose

A forward action moves a body one sub-cell whenever the way is clear, whatever the body is made of.
Muscle adds only a second sub-cell (with chance muscle / mass) and the force of a push. So a body
without a motor walks: in e047, lineages with no muscle held 21-55% of the bodies. The user
(2026-09-11): moving should need blocks made for it, more of them should mean faster, and how fast
stays a matter of each body (#51).

Muscle pays when a step needs it and a cell under a body does not regrow (e016, e043: already the
world's law). A body that cannot step eats what lies under it and what falls to it, and its
children land beside it.

## Hypothesis

1. **The motor is selected.** Muscle-free lineages hold under 10% of the bodies on at least five
   of six seeds (e047: 21-55%), and speed (muscle over mass) rises above e047's 0.13-0.17 on every
   seed.
2. **Bodies move less, not more.** The motor is paid in blocks and a step happens only by chance,
   so the work of moving per body per step falls below half of e047's (0.0045-0.0098) on at least
   five seeds.
3. **The world stands, with fewer bodies.** Bodies 10-30% fewer than e047's on at least four seeds
   (a muscle block eats nothing); the lowest winter floor above 200; the hunter world on at least
   four seeds (4 in e047: a hunter carries muscle already).

## Method

Code: e047 (`experiments/e047_corner`) as `e048_motor`, with `connect` 2 by default (e047 kept it)
and one law about the body, off by default:

- **`motor`** (argument 44) **1**: every change of a body's position needs its muscle. Each
  sub-cell of a forward action happens with chance speed (muscle over mass; e047 moved the first
  whenever the way was clear and the second by chance), and a turn happens with chance speed. A
  body without muscle neither steps nor turns; it can still be shoved. The press on what is in the
  way, the shove and the work paid are unchanged, and a forward action that moved nothing costs
  nothing. Muscle stays the one motor (walking and pushing); a leg kind belongs with #52.
- **Log**: `stalled`, the share of the forward actions whose way was clear that the motor did not
  move (0 under `motor` 0); `moved`, sub-cells a body moved by its own actions per body per step.
  `agents.csv` gets `travel`, how far the body stands from where it was born, in world cells.
- **Checked**: `motor` 0 repeats e047's corner run on seed 9 in every output but the new columns,
  the timing column and the parameter line. A unit test: without the law no chance is drawn;
  under it a body with no muscle never moves and one of speed 1/4 moves a quarter of the time.

**Runs.** e047's season world with corners holding, 100,000 steps (five winters), one thread each:

| run | motor | seeds | question |
|---|---|---|---|
| control (e047's corner runs, already run) | 0 | 9-14 | the baseline |
| check | 0 | 9 | byte for byte with e047; the control's `moved` and `travel` on one seed |
| pilot | 1 | 9, 20,000 steps | does the start stand |
| motor | 1 | 9-14 | the motor (1), the moving (2), the world (3) |

Six seeds because the seed picks the world's state (e045). Run from the repo root:
`bash experiments/e048_motor/run.sh <motor> <threads> <steps> <seeds>`.

**Measures** (over the second half). The share of the bodies in muscle-free lineages (mean muscle
under 0.5), muscle and speed per body; the work of moving (`move_spent`), `moved`, `stalled`,
`blocked`; `travel` of the grown bodies; bodies, winter floors; the kills' share of the intake (the
state); the winners of the last third; diversity (#42).

**Compute.** One random draw more per clear forward action and per turn with room: well under a
percent of a step's cost.

## Result

**The runs.** The pilot (seed 9, 20,000 steps, 6 threads, 2.5 minutes) stood: 2,206-2,542 bodies,
a first winter floor of 522, muscle 8.9 per body by step 10,000. `motor` 0 on seed 9 is e047's corner
run byte for byte: every output file identical (13 files) but the new columns, the timing column and
the `"motor":0` of the parameter line. The batch: seeds 9-14, six runs at once on the Mac (with the
check for its first 9 minutes, 7 of 12 cores), 21 minutes; the slowest seed (11) ran 83 steps a
second with 2,693 bodies of 16 blocks (e047: 16 minutes; the bodies are bigger).

Means over the second half (steps 50,000-100,000); each pair is free step (e047) / motor. `travel` is
the median distance from the birthplace, in world cells, of the bodies aged 1,000 steps or more at
step 100,000 (the control's from the check run, seed 9 only):

| seed | muscle-free | speed | work of moving | stalled | travel | state | kills' share | bodies | lowest floor | diversity | top lineage of the last third, motor |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 9 | 55% / 0% | 0.14 / 0.25 | 0.0056 / 0.0034 | 38% | 38.1 / 13.1 | hunter / hunter | 31% / 32% | 2,464 / 1,937 | 505 / 422 | 2 / 2 | 325: 28 cells, 10 muscle, 10 gut, speed 0.26, 50% flesh; 67% |
| 10 | 21% / 0% | 0.13 / 0.16 | 0.0098 / 0.0028 | 54% | - / 10.2 | grazer / grazer | 13% / 4% | 2,131 / 2,085 | 537 / 558 | 1 / 2 | 677: 23 cells, 7.5 muscle, 14 gut, speed 0.17, 21% flesh; 71% |
| 11 | 44% / 0% | 0.14 / 0.16 | 0.0071 / 0.0017 | 42% | - / 13.5 | hunter / grazer | 32% / 10% | 1,976 / 2,693 | 512 / 742 | 2 / 1 | 1521: 14 cells, 5 muscle, 9 gut, speed 0.18, 20% flesh; 35% |
| 12 | 44% / 0% | 0.16 / 0.24 | 0.0053 / 0.0031 | 32% | - / 29.2 | hunter / hunter | 40% / 33% | 2,392 / 2,004 | 420 / 347 | 2 / 1 | 67: 27 cells, 9 muscle, 12 gut, speed 0.24, 42% flesh; 77% |
| 13 | 50% / 0% | 0.17 / 0.23 | 0.0068 / 0.0026 | 34% | - / 16.1 | grazer / hunter | 30% / 27% | 2,489 / 2,328 | 478 / 362 | 2 / 2 | 225: 25 cells, 9 muscle, 12 gut, speed 0.25, 32% flesh; 54% |
| 14 | 41% / 0% | 0.16 / 0.20 | 0.0045 / 0.0020 | 41% | - / 8.9 | hunter / grazer | 39% / 9% | 3,069 / 2,592 | 597 / 445 | 3 / 1 | 651: 14 cells, 5 muscle, 9 gut, speed 0.18, 16% flesh; 25% |

(The state by the blocks broken per body per step, over 0.03 a hunter world; seed 13 is at 0.029
under the free step and 0.030 under the motor, kills near 30% of the intake under both.)

- **No lineage goes without a motor.** Muscle-free lineages hold 0% of the bodies on every seed. By
  step 10,000 bodies carry 6.0-8.9 muscle blocks. At step 100,000, 6-18% of the living bodies have no
  muscle (27-54% under the free step): single damaged or mutant bodies, not lineages. Muscle per body
  4.5-8.9 against 2.8-5.2 (lower only on seed 11, whose control winner was the ram of 9.5 muscle).
  Speed rises on every seed and its spread narrows (standard deviation 0.07-0.16 against 0.12-0.19).
- **Every body moves less.** On seed 9, 0.089 sub-cells a body a step against 0.300 (0.059-0.089 on
  the six seeds). By age at step 100,000 on seed 9 a body stands half as far from its birthplace when
  young (4.7 against 8.8 cells at 100-499 steps) and a third as far when grown (13.1 against 38.1).
  The work of moving falls 39-76%, less than the distance, because bodies are heavier (size p50
  16-25 blocks against 8.6-20; gut rises too, 8.4-12.8 against 7.0-10.1). 32-54% of the forward
  actions with a clear way are stalled; the policy picks forward on 68-91% of its decisions.
- **The world.** Lowest floor 347 (seed 12). Bodies -21% to +36% (2,273 on average against 2,420),
  fewer by 10-30% on seeds 9, 12, 14. The hunter world on seeds 9, 12, 13 (13 at the line); seeds 11
  and 14 become grazer worlds (kills 10% and 9% of the intake against 32% and 39%). Births per step
  fall on five seeds (2.5-7.5 against 3.0-14.7). Lineages alive rise on three seeds (seed 14: 15.4
  against 3.9); diversity 1-2 against 1-3.
- **Winners.** Two kinds of body: hunters of 25-28 blocks with a hard front and 9-10 muscle behind
  the gut (speed 0.24-0.26; seeds 9, 12, 13), and grazers of 14-23 blocks with 5-7.5 muscle in rows
  or a triangle beside the gut (speed 0.17-0.18). Under the free step the leading bodies of five seeds
  were gut with 0-1 muscle (speed 0.00-0.06).

## Conclusion

1. **The motor is selected: yes.** No lineage is muscle-free on any seed (e047: 21-55%), and speed
   rises on all six against the control (0.16-0.25; on seeds 10 and 11 it stays inside e047's range).
2. **Bodies move less, not more: partly.** They do, and by more in distance than in work: the work
   of moving falls 39-76% but below half on four seeds, not five, because the bodies are heavier;
   the distance moved falls to about a third on seed 9.
3. **The world stands, with fewer bodies: partly.** It stands (lowest floor 347), but bodies are
   10-30% fewer on three seeds only, and the hunter world comes on three seeds, not four.

**Kept**: from here a step and a turn need the motor (`motor` 1 is the next experiment's default). It
is the physics the user asked for, and the build now says what a body does: no body walks without
muscle, and speed is a trait that differs between bodies.

What this changes:

- **The motor is the price of eating, not of travel.** A body that cannot leave the cells it has
  grazed bare (they do not regrow under it) starves, so every lineage keeps a motor; but nothing asks
  a body to go far, and every body moves about a third as far as before. The complaint that the world
  does not move is not answered by the body: it needs a world where the food moves.
- **Next**: #14's first pilot, a band of rain that crosses the world slowly, under this law. Speed
  pays when the food moves and a step needs muscle: the two conditions together.
- **Open**: why seeds 11 and 14 left the hunter world (not measured); a leg kind for walking alone
  belongs with #52.
- **Compute**: 21 minutes for six runs at once (e047: 16 minutes), from bigger bodies, not the law.
