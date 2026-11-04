# e114: the chemistry of matter - a key opens a lock (#133)

Date: 2026-11-05

## Purpose

At year 200 of e113 the bodies eat litter, 99.8% of their diet, and one founder's line holds every island and the
sea. The dead are the one food that asks nothing of a body: one pool a cell, which loses its compound and its
toughness and rots at a fixed rate; every other food is two numbers, its A and its B. The plan check of 2026-11-05
(#116) takes the turn "what litter is worth" as a general part instead of a value: the chemistry of matter. The
design, its cycles and the reasons are #133, agreed by the user on 2026-11-05. The crate is e113's, copied; every run
has e113's `all` on (`road worth reach bite ground crown floor press_work sight cover`, `tear=0`).

## Hypothesis

Written before the runs (#133):

1. **The world stands with it**: a rot that slows with a lock and is partly done by the living does not starve the
   land's soil.
2. **Locks spread**: producers drift away from the plain bond, and more than one lock holds a share of their mass.
3. **Litter is not one food**: the bodies' litter is split by lock, and bodies differ in the keys they carry.
4. **The sea parts by food** (pilot): if sea producers' locks drift apart from the land's, a body of the sea and a body
   of the land need different keys, and `held` by island rises.

## Method

One law behind one switch, `lock` (0: e113's world). The address map gains a lock for each kind, one point change
from its keys' address (`genome::LOCK` 20 for producers, `E_LOCK` 36 for the small eaters, 84 for bodies); the first
gene read there sets the genotype's lock, none the plain bond, 0.

- **A key opens a lock** (`genome::fit`): the share of a bulk a set of keys takes apart is 1 less an eighth for each
  bit the nearest key (or the plain bond, which all can break) lies from the lock past the tolerance - the curve a
  compound's harm already follows.
- **Digestion**: a body digests a plant food's working part as before and its bulk as before times the fit
  (`body.rs`); of flesh, the tough part times the fit. The keys are its detox keys: one key opens a compound and a fibre.
- **The dead keep what they were made of** (`life::Litter`): four slots a cell, each of one lock, with mass, A, B,
  compound and its key. Tissue joins its lock's slot, an empty one, or the nearest lock's; carrion takes the lock of
  the larger part. A mouth needs the pressure its A sets (not the softest tissue's), and its compound harms.
- **The rot is the living's**: the small eaters eat litter by the same rule as leaves (its working part, toughness,
  fit, compound), and the abiotic rot of a slot is times its fit to the plain bond alone (slower by its lock's
  distance). What a small eater digests and does not keep is mineral, to the soil; half its waste is dung of the
  lock it mostly ate.

**Decided while building, against the issue's text** (to be noted on #133): the issue said "no gene: lock 0" but not
whether lock 0 needs a key. Here the plain bond is open to all, so with no lock gene anywhere the world starts as
e113's and a lock is a distance from it: this avoids a world where nothing digests a bulk until a key evolves. The
issue cut the abiotic rot "to a floor"; a floor would be a new number set by hand, so the abiotic rot is instead
slowed by the same fit (no new rate).

**Gate**, on e111's trial world (16 km, 128 cells, bodies sown in year 15; `gate.sh`), Ubuntu, two threads each,
three runs at once, under an hour, under 6 core-hours:

| run | arguments on top of e113's `all` | asks |
|---|---|---|
| `off` | `lock=0`, to year 40 | is it e113's gate `all` to the digit (every log column but timing and e114's own) |
| `lock` | `lock=1`, to year 40 | does the world stand |
| `lock80` | `lock=1`, to year 80 | do locks spread, given time |

**Passed if** `off` is e113's `all` to the digit; ledgers under 1e-9; with `lock` the land at year 30 is at least half
of e112's `nobody` and bodies live at year 40; in `lock80` at least two producer locks each hold 10% of the producers'
mass at some census (`_census.csv`, `lock`). If the world stands but locks do not spread, the pilot still runs (the
islands are 25 times larger and run longer), and that is written down before it.

**Pilot** (after the gate, lines written here before it runs): `isles1` to year 100, Ubuntu, six threads, about 10
hours; control e113 `all`.

**Stop early if:**

- `bodies` < 10 at 190080

For the gate (bodies sown in year 15; the step is the end of year 16, at 11,880 steps a year).

## Result

## Conclusion
