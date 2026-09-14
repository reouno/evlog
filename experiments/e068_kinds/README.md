# e068: kinds of living inside a lineage (foundation stage C, sixth step, #82)

Date: 2026-09-14

Analysis only: no new runs. Closes #82.

## Purpose

Stage C's pass line counts kinds of living (foundation.md section 3), and e060's census reads one way
of living per lineage: every grown body counted under its lineage's commonest way. e067 found each
large lineage holding an open form in the water and a more closed form on land, joined by mates who
meet at the shore, and a count by lineage cannot see them. Before stage C adds a law, it needs a count
that can: a kind below the lineage that is a way of living, not a shape, and not the spread of one
kind's bodies over where they happened to stand (e060's reason for not counting per body).

## Hypothesis

This analysis tries candidate definitions on the same four runs it judges, so the definition chosen is
a result, not a test. The expectations it answers were set before it, by e067 and #82:

1. **e067's forms by medium are kinds of living.** A count below the lineage reads more kinds at breath
   than the same count with the medium shuffled inside each lineage, and in e065 and e066 (no forms by
   medium, e067) it does not.
2. **#82's first candidate sees them**: e060's way of living with the medium, counted over bodies.
3. **The count that sees them is not a count of shapes**: its kinds differ in what they eat or where
   they live, and it does not follow the number of forms.

## Method

Runs, all on c1225 with draw d11, seed 9, s = 1/16, 100,000 steps, read at the six censuses of the
second half (steps 50,000-100,000):

- e065, the water's two layers: `experiments/e065_layers/results/c1225_life9_water`;
- e066, dry air at 0.004: `experiments/e066_dry/results/c1225_life9_dry0.004`;
- e067, breath at 0.003 and 0.01 with that dry air: `experiments/e067_breath/results/c1225_life9_breath0.003`, `_breath0.01`.

A grown body is e060's: aged 300 steps or more, having eaten.

**What the logs hold.** `cells` in `agents.csv` is the body now, after breaks and wear: 40-50% of the
grown bodies are at their birth size. The body a genome develops (`develop_genes` reads only the genes
and the law table) is logged as the grid's side and, at birth, the blocks of each kind, the bite and
the density. e067's "common birth shapes" were read from `cells`.

**Readings** (`kinds.py`):

| reading | each grown body is counted under |
|---|---|
| per body, with the medium (#82's first candidate) | its own way (e060) and the medium it stands in |
| per lineage (e060) | its lineage's commonest way |
| modal form (#82's second candidate, as far as the logs allow) | its birth form's commonest way with the medium |
| born apart (tried, dropped) | its own way and medium, where its birth traits tell it from its lineage's largest group |
| **by birth form** (chosen) | its form's way, read over all the form's grown bodies |

**A birth form** is a birth signature (side; hard, muscle, sensor and gut blocks; bite; density) with
20 or more grown bodies over the six censuses. Every other grown body joins the nearest form of its
lineage and layer by its birth traits (log size, share of each kind, bite, density, side, each scaled
to unit spread). A body's layer is where its signature's bodies stand in the water: `density` is
printed to three decimals and many lineages sit at 1.000, where some bodies float and some sink.

**A form's way of living** is read over all its grown bodies: the diet from their summed intake
(e060's thirds of flesh), the tooth and the roaming from their medians (`bite_any` of 2 or more,
`travel` of 8 cells or more), and the medium where 90% of them stand (e067's line), else "shore". A
kind holds 5% of the grown bodies at a census (e060's share); it is **held** when it does so at all six.

**Nulls.** What bodies do (intake, bite, travel, medium) is shuffled among the grown bodies of each
lineage and layer, five times: the medium alone, or all of it. The count under a null is what the forms'
grain reads when a lineage's forms do not differ.

**Checks.** The medium's line at 80% and 95%, forms from 10 and from 50 bodies. e067's measure (grown
bodies in shapes of 20 or more that keep 90% to one medium) on current shapes and on birth signatures,
with the medium shuffled. The born-apart test: balanced leave-one-out 5-nearest-neighbour accuracy on
birth traits, a group living one way against its lineage's largest group, 400 bodies of each at most.

Run from the repo root: `uv run python experiments/e068_kinds/kinds.py` (16 s on one core), then
`report.py`. It writes `results/runs.csv` (a row per run), `counts.csv` (each census), `kinds.csv`
(each kind: share, forms, lineages, birth size and openness, food, where it stands, the commonest
intact birth body of its largest form), `sizes.csv` (birth size by medium in the three largest
lineages), `sweep.csv` and `apart.csv`. Cost: a minute of one core, no runs.

## Result

Second half of each run.

| | e065 | e066 | e067 breath 0.003 | e067 breath 0.01 |
|---|---|---|---|---|
| grown bodies a census; forms | 3,291; 321 | 2,834; 178 | 3,162; 295 | 2,862; 351 |
| kinds per body with the medium (medium shuffled) | 5.0 (5.1) | 6.7 (6.5) | 6.2 (6.1) | 6.0 (6.0) |
| kinds per lineage (e060) | 1.8 | 1.5 | 2.7 | 2.5 |
| kinds by modal form (all shuffled) | 3.8 (3.8) | 6.7 (3.2) | 5.5 (4.2) | 5.5 (4.7) |
| **kinds by birth form**: mean (lowest-highest) | 2.5 (1-6) | 4.5 (3-6) | 6.2 (5-7) | 6.2 (5-8) |
| held at every census | 1 | 2 | 3 | 4 |
| by birth form, medium shuffled: mean; held | 2.2; 1 | 4.6; 2 | 4.3; 2 | 5.1; 3 |
| by birth form, all shuffled: mean; held | 2.1; 1 | 2.8; 2 | 4.2; 2 | 4.6; 1.4 |
| grown bodies in forms kept 90% to one medium | 22% | 21% | 37% | 43% |
| e067's measure on current shapes | 58% | 32% | 86% | 85% |
| the same on birth signatures (medium shuffled) | 17% (5%) | 33% (4%) | 44% (13%) | 64% (28%) |

**1. Per body, the medium adds combinations, not kinds.** Three media over e060's parts give 5.0-6.7
kinds in every run, highest in e066, and shuffling the medium inside lineages moves none by more than
0.2. Each run passes stage C's line of 4 that way. Counted under a form's commonest way, a form whose
bodies straddle a cut (diet at a third, travel at 8 cells) splits between ways: e066 reads 6.7 against
3.2 shuffled.

**2. Lineages hold forms in every run; breath sorts them by medium.** The share of a large lineage's
dense grown bodies born at each size, on land and in the water:

- e065, lineage 1: born at 36-39 blocks 70% on land, 72% in the water (the rest at 24-27): two forms,
  not sorted.
- e066, lineage 1: born at 48-51 blocks 65% on land, 39% in the water (the rest mostly 36-39).
- breath 0.01, lineage 1640: born at 48-51 blocks 35% on land, 7% in the water; in the water 24-31
  blocks (47%). Lineage 908: 20-23 blocks 57% in the water, 33% on land, and 48-51 blocks 14% on land.

Being born apart does not single out forms kept to a medium. The birth traits tell a group living in
another medium from its lineage's largest group (balanced accuracy 0.8 or more) in 35%, 77%, 55% and
64% of such groups, most in e066; a group with another tooth in every one; a group that roams where the
largest stays in 12%, 57%, 41% and 37% (shuffled 0.49-0.51). A threshold on a birth trait (density at 1,
muscle behind roaming) makes groups born apart without making kinds, so this reading was dropped.

**3. By birth form, breath adds kinds by medium.** 6.2 kinds at both rates against 4.3 and 5.1 with the
medium shuffled; e065 2.5 against 2.2, e066 4.5 against 4.6. e066's forms add kinds by tooth and
roaming instead (2.8 with all shuffled): a toothed sitter at the shore holds 5% in five censuses.

The kinds at breath 0.01, over the six censuses:

| kind (none has a tooth) | share | censuses at 5% | forms | lineages (leading) | born, blocks | open faces per block at birth | food |
|---|---|---|---|---|---|---|---|
| plant, roams, shore | 27% | 6 | 39 | 20 (908 54%, 1640 22%) | 24 | 1.22 | algae 53%, litter 24%, flesh 14% |
| plant, stays, shore | 21% | 6 | 29 | 13 (908 47%, 964 24%) | 29 | 1.16 | litter 38%, algae 27%, flesh 17%, grass 17% |
| plant, roams, surface | 14% | 6 | 32 | 13 (908 51%, 1941 12%) | 18 | 1.29 | algae 87%, flesh 12% |
| plant, roams, bottom | 9% | 6 | 24 | 22 (908 88%) | 23 | 1.13 | litter 88%, flesh 12% |
| mixed, roams, shore | 7% | 5 | 36 | 35 (1950 22%) | 25, density 1.93 | 1.00 | flesh 48% (kills 41% of intake) |
| plant, stays, surface | 5% | 1 | 18 | 14 (1709 43%) | 33 | 1.29 | algae 87% |
| mixed, roams, land | 4% | 3 | 25 | 25 (2344 25%) | 49 | 0.63 | grass 56%, flesh 42% |
| plant, stays, land | 3% | 2 | 47 | 43 (1711 26%) | 49 | 0.57 | grass 74%, flesh 25% |

The water forms of lineage 908 are kinds: born small and open, eating algae at the surface and litter
on the bottom, held at every census. The land's closed forms are not: the forms kept to land hold 3-4%
each and belong to many small lineages born at 49 blocks, while the land bodies of the large lineages
stand in forms that also live in the water ("shore").

**4. Thresholds.** Kinds by birth form less the count with the medium shuffled (e065, e066, 0.003, 0.01):
+0.3, -0.1, +1.9, +1.1 as chosen; with the medium's line at 80% +0.5, +2.6, +0.7, +0.3; at 95% -0.1,
-0.3, +1.0, +0.4; forms from 10 bodies +0.1, +0.9, +2.6, +1.2; from 50 +0.2, 0.0, +1.3, +1.3. The breath
runs gain more than e065 and e066 under 4 of the 5 settings. At 80% e066 gains most: 33% of its grown
bodies are in signatures keeping 90% to a medium, and more keep 80%.

**5. e067 corrected.** e067's 85% was read from current shapes, a measure that reads 58% in e065. By
birth signature it is 64% at breath 0.01, 44% at 0.003, 33% in e066 and 17% in e065 (28%, 13%, 4% and
5% with the medium shuffled). The shapes still part by medium, less than e067 said. The correction is at
the top of e067's README and report, and in foundation.md.

## Conclusion

1. **e067's forms by medium are kinds of living: yes, the water's.** By birth form, breath 0.01 holds
   6.2 kinds, 1.1 more than with the medium shuffled inside lineages (0.003: 1.9 more); e065 0.3 more,
   e066 0.1 fewer. The kinds are lineage 908's surface and bottom forms. The closed land forms are not
   kinds: 3-4% each.
2. **#82's first candidate sees them: no.** Per body with the medium every run reads 5.0-6.7, at its
   shuffle, and e066 reads the most.
3. **Not a count of shapes: yes.** 178-351 forms make 2.5-6.2 kinds; at breath 0.01 the held kinds eat
   algae (87%) at the surface, litter (88%) on the bottom, and a mix at the shore.

**What stage C is counted with.** Kinds of living by birth form (`kinds.py`), in place of the count by
lineage. The pass line keeps its numbers, read with this count: at least 4 kinds on 4 seeds of 6, each
at 5% of the grown bodies at every census for 5 years. Each run reports beside it the count by lineage
and the count with what bodies do shuffled inside lineages, which reads how many kinds the forms' grain
makes when forms do not differ (up to one held kind here). Breath 0.01 holds 4 kinds over 2.5 years;
the 5 years need runs of 200,000 steps. foundation.md section 3 is updated. Nothing new needs logging:
the birth columns carry the forms.

**What this cannot say.** One world (c1225), one seed, 2.5 years of censuses, and the four runs the
definition was chosen on. The reading hangs on the medium's line (at 80% e066 gains the most), on forms
made of block counts (two bodies with the same blocks in other places are one form), on the tooth read
from the body after breaks, on e060's cuts for diet and roaming, and on the lineage and layer that bound
the shuffle. Whether a kind is held by the world or by the seed is #72's invasion test.
