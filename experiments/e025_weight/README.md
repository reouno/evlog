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

The control is e024's runs at flesh 1 (`experiments/e024_flesh/results`, flat seeds 1-4,
500,000 steps): the same law up to the ground's rounding, so nothing is rerun.

Pilot (flat seed 9, 200,000 steps, one thread each, four at once, 30-40 minutes on the Mac):
`weight` 0, kind, density and 1, to see which half does what and whether the world stands (0
is the pilot's control: the fixed ledger moves seed 9's start, so e024's seed 9 is not). The
batch: `weight 1`, flat seeds 1-4, 500,000 steps, one thread each, four at once (1.5-2 hours;
a hunter-state run goes at 100-130 steps per second).

Run (from the repo root):

    bash experiments/e025_weight/run.sh 1 1 2 3 4

Arguments: `<steps> <seed> <size> <widths> <cell_energy> <matter> <relief> <flow> <rain> <breath> <shade> <spill> <mutation> <eyes> <flesh> <weight>`;
the batch uses `500000 <seed> 128 0 0.02 8 64 0.1 flat 1 2 1 0.00390625 8 1 <weight>`.

## Result

(to come)

## Conclusion

(to come)
