# e025 What a block weighs

Date: 2026-09-03

## Purpose

Every block has weighed 1 since e005: mass is the number of cells, speed is muscle over mass,
the work of moving is mass times distance, a shove needs more muscle than the shoved body's
mass. So light-and-fast against heavy-and-sturdy exists as a trade, but only through the count
of blocks, and armor costs nothing but its upkeep. e024 ended with two bodies that could both be
right: the net (twelve guts, no armor, no muscle) in seven runs of eight, and in the hunter
state the tooth (two hard, one gut, three muscle) beside a ten-gut body, plus a 48-cell armored
hunter (9 hard, 13 muscle) that held 26,000 steps in a pilot. The issue (#25) asks for mass as
a property of the material and of the lineage, so that selection gets two more axes without a
rule naming either.

The real world's premise: materials weigh differently, and no two children of a lineage weigh
the same. Bone is heavy and gut is light; a heavy animal is slow, costly to move and hard to
push over; and density is inherited, so a lineage can drift light or heavy. Written as laws
about a block and about what a genome expresses, not about what a body does.

Before it, #31: e024 lost 0.2-1.8% of the world's matter over a run, blamed on the f32 ground
(`res`, `carrion`, `fruit`) under corpses of 30-150, e019's soil drift again. The ground
becomes an f64 here, and the ledger is audited step by step to see that the matter holds.

## Hypothesis

1. **The world stands and matter holds.** No death, matter conserved to 0.01% over 500,000
   steps (e024: 0.982-0.999), population cv under 0.10 over the second half.
2. **Mass spreads.** Bodies differ in density between and within lineages: the density's
   standard deviation over bodies stays above 0.1 (the range is 1/2 to 2) over the second
   half, and lineages alive at the end differ in mean density by 0.2 or more.
3. **Armor costs speed, so the armored body changes.** With hard blocks at 2, a hunter with
   armor is slower and dearer to move than e024's tooth (2 hard of 8 cells: mass 10 for 8
   cells, speed 0.3 instead of 0.375); either the tooth loses its armor and keeps its muscle,
   or it keeps the armor and is denser than its prey. Judged in the hunter state only.
4. **The hunter state is entered more often than one seed in four** (e024: seed 3 of 1-4 at
   flesh 1; the pilots at 0.85-1 on seed 9). If the state is a lottery of the start, the law
   should not change its odds; if light prey is what a tooth needs, it should.
5. **#19.** Lineages alive at the end at or above e024's 2-3 (1-3 at 0.7); a second winner
   that differs from the first in density or armor, not only in shape.

## Method

Code: e024 (`experiments/e024_flesh`) with the ground as an f64 (#31) and the weight law.
`weight 0` is e024's law on the f64 ground with the ledger fixed: the same table, genomes and
bodies (the density column of the table is drawn from its own stream), so the runs differ
from e024's only by the ground's rounding and by the bodies that the fix keeps at zero energy
instead of a little below.

- The ground (#31): `res`, `carrion` and `fruit` are f64 like the soil; the snapshots and
  logs stay f32. The check (flat seed 9 at flesh 1, the hunter state, 50,000 steps) found the
  matter still fell, 0.13% over 50,000 steps, and a step-by-step ledger (`EVLOG_AUDIT=1`,
  the world's matter every step with the step's events) found where: a body whose upkeep took
  its energy below zero could, in the same step, break a cell of another body and fill the
  deficit with the gain, and the deficit was never in the ledger (the body's energy counts
  from zero). In the hunter state that was 4.2e-3 of matter a step, against a loss of 4.1e-3
  (a small creation, 1.8e-4 a step, ran the other way: a parent paying the matter of a child
  it could not afford). The fix is a rule of the ledger, not a new law: a body pays what it
  has and no more - its energy stops at zero at the upkeep and at the work of moving (it dies
  at the end of the step unless it gains first, as before), and a parent that cannot pay the
  matter of the child's body makes no child (the child's energy lies where the parent stands,
  as when there is no room). After that fix the ledger still fell by 2.8e-4 a step with no
  cell broken, a constant per body: the fat takes a fixed increment every step (the upkeep,
  0.056 for a body of twelve cells) onto an f32 that has grown to 20-30, and rounding to the
  nearest f32 with a fixed increment is biased (2,000 adds of 0.056 lose 4.4e-4 in a test;
  4,400 bodies at 1e-7 a step is the 4e-4 seen). That was e024's loss in the net state too
  (0.2%; the rate grew with the fat). So the bodies' ledger, `energy` and `fat`, is an f64
  as well; the measures stay f32. Check after both fixes: 50,000 steps on seeds 9 and 3
  (seed 9 enters the hunter state at 25,000: 2.6 kills and 90 cells broken a step), the
  world's matter every step, end over start 1.000000008 and 1.000000015 (e024: 0.982-0.999
  over 500,000).
- The weight law (#25), two halves with one switch each:
  - `kind`: a block weighs by its kind, `KIND_MASS` = hard 2, muscle 1, sensor 1/2, gut 1.
  - `density`: the genome expresses a density from 1/2 to 2 (2^(2 sigmoid(s) - 1), s read
    from the settled gene levels of the run without position, like the policy; each gene
    product's weight on it is one more column of the law table). Every block of the body
    weighs its kind's mass times the density. Heritable: a child's density comes from its
    genome, mutated like everything else.
  - Mass is what a body is made of, moves with and resists with: a child costs `cell_energy`
    times its mass; a broken or dead block lays `cell_energy` times its own mass (plus the
    cell's share of energy and fat, per cell as before); the work of moving is mass times
    distance; speed is muscle blocks over mass; a shove needs more muscle than the shoved
    body's mass; the reproduction threshold is 2 + 0.1 mass. A face's hardness (3 per hard
    cell, else 1) is multiplied by the body's density: light armor is weak armor (the
    issue's watch-out), a dense soft face resists a single muscle. Muscle force, bite and
    sight stay per block: strength of material scales with its density, what a block does at
    its surface does not. The upkeep stays per living cell (a block burns to live; the weight
    is paid in moving).
  - Argument 16 `weight`: `0` (e024), `kind`, `density`, `1` (both; the default). Tag `_w<x>`.
  - New log columns: `size_mean` (cells per body; `mass_*` are the weight now), `density_mean`,
    `density_std`; `agents.csv` gets `size` and `density`; `lineages.csv` gets `density`.
  - Compute: none added (a sum over five kinds per body at birth and per break).

The control is `weight 0` at the same code, flat seeds 1-4, 500,000 steps (the fixed ledger
moves a seed's start, so e024's runs at flesh 1, `experiments/e024_flesh/results`, are a
second reference, not the control); the report draws e024's runs in gray.

Pilot (flat seed 9, 200,000 steps, one thread each, four at once, 30-40 minutes on the Mac):
`weight` 0, kind, density and 1, to see which half does what and whether the world stands (0
is the pilot's control: the fixed ledger moves seed 9's start, so e024's seed 9 is not). The
batch: `weight 1` and `weight 0`, flat seeds 1-4 each, 500,000 steps, one thread each, eight
at once on the Mac (about 2 hours: 70-115 steps per second in the pilots).

Run (from the repo root):

    bash experiments/e025_weight/run.sh 1 1 2 3 4
    bash experiments/e025_weight/run.sh 0 1 2 3 4

Arguments: `<steps> <seed> <size> <widths> <cell_energy> <matter> <relief> <flow> <rain> <breath> <shade> <spill> <mutation> <eyes> <flesh> <weight>`;
the batch uses `500000 <seed> 128 0 0.02 8 64 0.1 flat 1 2 1 0.00390625 8 1 <weight>`.

## Result

### The pilots (flat seed 9, 200,000 steps, medians over the second half)

| weight | bodies with a bite | bodies killed per step | cells broken per step | density (mean +- spread) | cells per body; mass | speed | hard; muscle per body | intake from other bodies | fat, share of the matter | air | bodies | lineages | matter |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 (every block 1) | 22% | 4.0 | 248 | 1 | 25; 25 | 0.076 | 3.4; 4.2 | 72% | 15% | 25 | 2,660 | 2 | 1.000000 |
| kind | 14% | 5.2 | 190 | 1 | 16; 18 | 0.049 | 1.8; 2.6 | 74% | 20% | 17 | 3,650 | 2 | 1.000000 |
| density | 34% | 2.1 | 251 | 1.38 +- 0.18 | 11; 16 | 0.091 | 1.3; 1.7 | 75% | 18% | 21 | 4,657 | 2 | 1.000000 |
| 1 (both) | 0.0% | 0.83 | 39 | 1.41 +- 0.47 | 11; 16 | 0.028 | 0.06; 0.6 | 72% | 43% | 8 | 4,515 | 6 | 1.000000 |

All four entered the hunter state at the start (the control at step 25,000, the rest by
10,000). Each half alone keeps it: `kind` with fewer hard blocks (1.8 against 3.4) and smaller
bodies, `density` with bodies that drift heavy (1.38, rising to 1.52 at 200,000) and more
biters. Both together end the tooth (0.0% with a bite, 0.06 hard blocks per body) but not the
killing: 0.8 bodies a step die to pushes without a hard tip, because a face's hardness is the
material's times the density and a light body's soft face (1/2) breaks under a single muscle.
The density's spread is 0.47, three times the density-only pilot's, and six lineages are
alive against two everywhere else. The matter holds to 1e-6 in all four (e024: 0.982-0.999).
The batch runs `weight 1` and, as the control at the same code, `weight 0`, flat seeds 1-4,
500,000 steps, eight at once (the fixed ledger moves a seed's start, so e024's runs are not
the control for the state a seed enters).

### The batch (flat seeds 1-4, 500,000 steps; e024's flesh-1 runs as a second reference)

Eight runs, one thread each, eight at once on the Mac: 2 hours (53-123 steps per second).
Report: `report.html`. Ranges over seeds, medians over the second half unless said.

| | weight 1 | weight 0 (the control) | e024 flesh 1 (leaking ledger) |
|---|---|---|---|
| The state entered (by 50,000 steps, kept to the end) | hunter, 4 of 4 | net, 4 of 4 | net 3, hunter 1 |
| Bodies with a bite (median) | 29-47% | 0.0% | 0 / 46% |
| Bodies killed per step; cells broken per step | 2.1-3.8; 166-358 | 0.00; 0 | 0.00 / 3.95; 310 |
| Density per body (mean); its spread over bodies | 0.95-1.52; 0.10-0.47 | 1; 0 | 1; 0 |
| Bodies under density 0.8 at the end; at 1.8 and above | 0-0.7%; 0-51% | - | - |
| Cells per body; mass | 7.5-17.9; 11.5-19.4 | 11.8-11.9; the same | 11.7-11.8 / 8.8 |
| Speed (muscle over mass) | 0.087-0.242 | 0.001-0.002 | - |
| Hard; muscle blocks per body | 0.5-2.7; 1.2-5.0 | 0.01-0.03; 0.01-0.03 | 0.01-0.02 / 1.35; 0.00-0.03 / 2.14 |
| Hunters' density against their prey's (at the end) | 1.36 / 1.21, 1.76 / 1.40, 0.89 / 0.98, 2.00 / 1.33 | - | - |
| Worth of a cell | 0.46-1.18 | 2.19-2.50 | 2.2-2.5 / 0.64 |
| Fat, share of the world's matter; air | 6-14%; 22-27 | 57-68%; 0-2 | 63-70%; 0.4-2 / 9%; 20-23 |
| Intake from other bodies | 72-74% | 75-80% | 78-79% / 75% |
| Population (cv) | 2,407-4,726 (0.02-0.11) | 3,304-3,610 (0.02-0.03) | 3,313-3,812 (0.02) / 4,509 (0.05) |
| Bodies with a sensor | 0.4-6.4% | 0.2-0.9% | 0.5-7% |
| Lineages alive | 1-5 | 1-3 | 2-3 / 2 |
| Matter at the end over the start | 1.000000-1.000001 | 1.000000 | 0.998 / 0.982 |

The states. Every control run is e024's net state: the winner is a body of eleven to twelve
guts on 3-4 world cells (a bar with a hook; e024's four-pad net lives beside it for 491,000
steps in seed 2 and loses), no armor, no muscle, no cell ever broken, the air empty and the
fat holding two thirds of the matter. Every `weight 1` run is the hunter state from its first 50,000 steps:
a bite on 29-47% of the bodies, 2-4 kills a step, the fat at 6-14%, the air at 22-27. The
pilot on seed 9 was the exception (no bite, 0.8 kills a step): five seeds of five with the
law kill; zero of four without it.

The bodies (report, Figure 2). Seed 2: the tooth of e024 with four guts behind it at density
1.7-1.8 (lineage 4, the winner for 500,000 steps) beside a ten-gut body at 1.2 (lineage 377,
468,000 steps). Seed 1: a ten-gut body at 1.16 (467,000 steps) beside a tooth at 1.2 (268,000)
and, early, nets of ten guts spread over 7x7 cells at density 2.0 that live 400 steps. Seed 4:
a nine-gut bar at 1.06, the lightest winner, for 500,000 steps, and teeth of six cells at the
ceiling of 2 (79,000 steps; 51% of the run's bodies sit at 2 at the end). Seed 3 took the other
route: density 0.9-1.1, bodies of 17-29 cells with 3-4 hard and 4-5 muscle blocks, one winner
at a time (lineages of 205,000-211,000 steps). Nobody is light: no run ends with more than
0.7% of its bodies under 0.8.

The density by role (agents at the end): the bodies with a bite are denser than the rest in
seeds 1, 2 and 4 (1.36 / 1.21, 1.76 / 1.40, 2.00 / 1.33) and lighter in seed 3 (0.89 / 0.98,
where the hunters are the big armored bodies). The hunters are 6-10 cells at speed 0.16-0.29
in seeds 1, 2 and 4, and 18 cells at 0.36 in seed 3; the rest move at 0.02-0.12.

## Conclusion

1. **The world stands and matter holds: yes.** No death, population cv 0.02-0.11 (seed 3 at
   0.11), matter 1.000000-1.000001 in all eight runs; e024: 0.982-0.999. #31 is closed: the
   drift was two leaks of the ledger (a deficit filled by a kill, and f32 rounding of the fat's
   fixed increment), not the ground.
2. **Mass spreads: yes.** The density's spread over bodies is 0.10-0.47 (seed 3 at the floor);
   the two largest lineages differ by 0.5-0.9 in seeds 1, 2 and 4 (a tooth at 1.7-2.0, a gut at
   1.1-1.2).
3. **Armor costs speed and the tooth changes: partly.** The tooth keeps its armor (1.4-4.4
   hard blocks on the hunters) and gets dense, denser than its prey in three seeds; in seed 3
   it is a big armored body lighter than its prey. Both routes to resistance are taken.
4. **The hunter state is entered more often than one seed in four: yes.** Four of four (five of
   five with the pilot) against zero of four at the same code without the law and one of four in
   e024.
5. **#19: partly.** Lineages 1-5 (control 1-3); a second winner that differs from the first in
   density and armor holds 268,000-500,000 steps in three seeds; seed 3 has one winner.

What it changes. The weight law is kept, both halves (`weight` 1 by default: hard 2, muscle 1,
gut 1, sensor 1/2, times a density from 1/2 to 2 that the genome expresses). It ended the
lottery of the start: e024's world sat in the net state unless the start happened to put it in
the hunter state; with a block that weighs the hunter state is the state, in every seed. The
reason is not a rule about teeth but that hardness became a property of the whole body: a
light body's soft face breaks under a single muscle, so muscle pays from the start and the
prey answers with density, which costs matter and speed. The world now holds two kinds of
body at once, and for the first time since e013 a second winner that differs from the first in
a material property, not only in shape.

Open: whether the net state can be entered at all under the law (the pilot came close), why
seed 3 took hard blocks instead of density, the mountain worlds, and the eye, which is gone
again (a sensor on 0.4-6% of the bodies). Next: #24, weather, which now has two kinds of body
to move between; then #28, small and large bodies in one world.
