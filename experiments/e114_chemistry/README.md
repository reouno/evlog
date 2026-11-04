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

### The gate: not passed

Ubuntu, 2026-11-05, read by `gate.py` (`results/gate.csv`, `gate_locks.csv`, `provenance.csv`). Ledgers 1.6e-13 at
most in all six runs. `analysis/audit.py` does not read this crate's output (as in e113), so it was not run.

- **`off` is e113's gate `all` to the digit**: 103 log columns (all but timing and e114's own), 40 years.
- **With `lock` the world does not stand.** The land falls to 47% of `nobody` by year 15, before any body is sown, and
  to 33% at year 30; of the 300 bodies sown in year 15, 3 are left at year 30 and none at year 35.
- **No lock appears.** Every producer genotype in `lock80` holds the plain bond at every census to year 80, though all
  84 genotypes alive at year 80 are mutants: on this small world a gene landing on the lock's address is too rare, so
  the locks themselves were not tested.

Since no lock appeared, every key fitted, and the fall is the design's two other clauses. Two readings switch each off
(`lit_eat`, `lit_keep`; `split.sh`, added after the gate):

| run | small eaters eat litter | litter keeps toughness and compound | land of `nobody`, year 15 / 30 | bodies, year 40 |
|---|---|---|---|---|
| `lock` | yes | yes | 0.47 / 0.33 | 0 |
| `no_lit_keep` | yes | no | 0.47 / 0.39 | 2,040 |
| `no_lit_eat` | no | yes | 1.00 / 0.99 | 37 |
| `neither` | no | no | 1.00 / 0.87 | 6,020 |
| e113 `all` (`off`) | - | - | 1.00 / 0.78 | 7,410 |

1. **The small eaters on litter take the land.** Fed by the litter as well, they weigh 7.2 times more by year 15
   (7.4e-4 against 1.0e-4 kg a m2) and graze the leaves down: one eater eats both, and nothing in the world prices
   eating both. The soil's B rises fourfold (0.60 against 0.15 g a m2), so the land is not starved of nutrients but eaten.
2. **A litter that keeps its toughness feeds no body.** With the small eaters off it, the land stands, but the bodies
   stay at 7-37. Until locks part it, all of a cell's litter is one slot (lock 0): leaf, wood and root mixed, so the
   whole of it takes the pressure its mixed A sets. Whether the compound adds to this was not parted.

### The revision, written before its gate

Proposed to the user on 2026-11-05 and corrected by them: the dead must not be parted by a rule ("leaf and
seed soft, wood and root hard") but by what they are made of, so that a parting can come out of the matter or not.

- **The litter is kept by its make** (`Litter::pick`): how far two pieces lie apart is what a mouth and a key read
  of them, the toughness their A sets plus an eighth for each bit between their locks. An arrival takes an empty
  slot; with none it joins the nearest, unless the two nearest slots lie closer to each other than it lies to any,
  and then those two merge and it takes the freed slot. A cell keeps its four most distinct pieces; no organ is named,
  and leaf and wood lie together when a producer makes them alike. Four is the compute's limit (as before), not a
  number of kinds. Parts that arrive without their mass (a pool's A and B, a body's lost A) join the largest slot of
  their lock.
- **The small eaters are off litter** (`lit_eat` now 0): their eating stays one budget shared by leaves and litter,
  but a world where litter feeds them grows them sevenfold and they graze the land down. Who rots the dead is its
  own piece later, with what limits a decomposer; until then the rot is abiotic, slowed by the lock as before.
- **Gate again** (`gate2.sh`, same world and lines as above): `off2` (`lock=0`, e113 to the digit), `make`
  (`lock=1`, to year 40), `make80` (`lock=1`, to year 80). Ubuntu, two threads each, three at once, under an hour.
  Compared with the gate's `no_lit_eat` (the same but one litter slot for all lock-0 matter: 37 bodies at year 40).

### The gate again: the land stands, the bodies starve

Ubuntu, 2026-11-05, `gate.py`. Ledgers 1.6e-13 at most.

- **`off2` is e113's gate `all` to the digit** (103 columns, 40 years).
- **The land stands**: `make` holds 0.97 of `nobody` at year 20 and 1.00 at year 30.
- **The bodies starve**: of 300 sown, 23 at year 16, 5 at year 20, none at year 25; every death a cause is given for
  is hunger. With one slot for all lock-0 matter (`no_lit_eat`) 25 were left at year 20. So the mixing was not what
  kept them from the litter (the diagnosis above was wrong): a litter as tough as the tissue it came from is food they
  cannot live on. In e113 they lived on litter at the softest tissue's pressure, 99.8% of their diet: the world's
  animals stand on litter that loses its toughness by rule, the stand-in for a rot that softens.
- **No lock appears** in `make80` to year 80 (every producer on the plain bond).

### The rot softens, written before its gate

Agreed with the user on 2026-11-05. Each slot keeps the share of it still whole (`Slot::whole`): tissue, carrion and
dung arrive whole (1), mixed by mass, and the rot wears it at the rot's own rate (the slot's decay, slower by its
lock), so fresh litter is as tough to a mouth as the tissue it came from and old litter soft: the pressure a mouth
needs is the toughness its A sets times the share still whole. No new rate; one number a slot. The gut is as before.
Gate `gate3.sh`: `off3`, `worn`, `worn80`, the same world and lines; compared with `make`.

### The gate a third time: passed but for the locks

Ubuntu, 2026-11-05, `gate.py`. Ledgers 1.6e-13 at most. `off3` is e113's gate `all` to the digit (103 columns, 40
years). With `worn` the land holds 0.97 of `nobody` at year 30 and 834 bodies live at year 40 (6,690 at year 80 in
`worn80`), on litter 99.8% of their diet (e113 `all`: 7,410 at year 40). Hunger is still the main death: 59 in year 30.
**No lock appears** in `worn80` to year 80: the producers' locked share of mass is under 5e-5 at every year. Whether
locked genotypes are born and lost, or never born, the log did not say (its share was rounded to four places); it now
writes the shares in full and `p_lock_cohorts`, the live cohorts of a locked genotype.

As stated before the gate, the pilot runs though locks did not spread.

### The pilot, written before its run

`pilot.sh lock lock=1`: `isles1` to year 100, e113's `all` with the chemistry on, Ubuntu, one run on six threads,
about 10 hours (6 cores x 10 h). Control: e113's pilot `all`, the same machine.

- **The world stands**: the land at year 70 at least half of e113 `all`'s, and bodies alive at year 100.
- **Locks are born** (precondition of the rest): `p_lock_cohorts` above 0 in some year after year 10.
- **Locks spread** (hypothesis 2): at least two producer locks each hold 10% of the producers' mass at some census.
- Hypotheses 3 and 4 are read only if locks spread: bodies' litter split by lock (`lit_locked` over 10%), bodies of
  different keys (`b_keys`), and `held` by island against e113 `all`'s.

**Stop early if:**

- `bodies` < 10 at 498960

(sown in year 40; the step is the end of year 41.)

## Conclusion
