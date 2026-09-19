# e083: what holds the other lines against the leading line? (#96)

Date: 2026-09-19

Analysis only: no new runs.

## Purpose

e081 (water that binds a body) and e082 (water that frees it) both lowered kinds against the control. In
the control the line that leads the land does not hold everywhere: other lines hold a region through the
whole run on all three seeds, and at `fresh` 0.2 the leader takes it. What holds that region is where kinds
come from on this land, and the next design should start from it (`balance.md` section 18).

A first look at the maps, made while filing #96, corrects section 18's framing. The world is a torus, and
latitude runs from -59 to 87 degrees twice (rows 0-255 and 256-511), so each latitude has two lands. The
region the other lines hold is the **north of the upper continent** (10-55 degrees), with a boundary near
5-10 degrees at the same place on all three seeds. The leader holds the same latitudes on the lower
continent. So it is a place, not a latitude.

## Hypothesis

Three candidates, each with what would show it:

1. **A barrier.** Bodies are thin where the two meet (a trough in bodies a land cell, dry or high ground),
   the leader's bodies do as well as the locals' where both live, and at `fresh` 0.2 the trough fills.
2. **The locals fit their place.** The upper north differs from the lower north at the same latitude
   (drier, colder or higher), the locals' bodies do better there than the leader's (children a step,
   water, energy), and their traits fit it (fewer open soft faces where it is dry, more fat where it is
   cold). At 0.2 that axis stops paying.
3. **First come, first held.** No trough and no advantage; the boundary drifts through the run.

## Method

Runs (c1225, seeds 9-11, 100,000 steps, censuses every 1,000 steps from 36,000): e081's ladder (the control,
`unit` 0; and `unit` 9.4 at `fresh` 0.05) and e082's ladder (`unit` 9.4 at `fresh` 0.2). Land bodies only.

- **Leader**: the lineage with the most land bodies over a run's censuses; **locals**: every other line.
- **Regions**: the half of the map (upper: rows 0-255, lower: 256-511) and the latitude. The upper north is
  the upper half at 10 degrees or more; the lower north the same latitudes in the lower half.
- **The land and its climate**: `_dryness.csv` (the run's mean air and ground dryness and the land's share on
  a 128 x 128 map), and at each body's cell the census's temperature, ground fill, height and crown.
- **The boundary**: along the upper continent from its tropics to its north, by strips of 8 rows: bodies a
  land cell, the leader's share, the ground's dryness, height and temperature where bodies stand.
- **How the bodies do**, leader against locals in the same strips and regions: children per 1,000 steps of
  age (bodies aged 50 or more), water, energy, fat, body heat, energy paid to warm and water to cool per
  turn; their traits at birth (size, hard, muscle, digestive, sensor), open soft faces, store, meat's share.
- **The boundary in time**: the leader's share in the upper north per 16,000 steps.

Read with `uv run python experiments/e083_hold/hold.py` (writes `results/*.csv`).

## Result

`hold.py` reads the nine runs in about a minute.

**The held region.** In the control the leader holds 0-6% of the upper west's north (10-55 degrees; e081's
0.05: 0%), and 91-92% of the lower half's north on seeds 9 and 10 (54% on seed 11, where no line leads the lower
continent alone). At `fresh` 0.2 it holds 48-85% of the upper west's north.

**A trough on the way.** Along the upper west from its south to its north (strips of 8 rows, bodies a land
cell a census, seeds 9 / 10 / 11):

| latitude | control | leader's share | ground dryness | fresh 0.05 | fresh 0.2 | leader's share at 0.2 |
|---|---|---|---|---|---|---|
| -29 | 0.055 / 0.051 / 0.045 | 54 / 75 / 19% | 0.54 | 0.039 / 0.038 / 0.039 | 0.036 / 0.037 / 0.037 | 88 / 83 / 63% |
| -11 | 0.038 / 0.034 / 0.031 | 68 / 73 / 24% | 0.69 | 0.016 / 0.015 / 0.017 | 0.034 / 0.032 / 0.032 | 88 / 88 / 58% |
| -2 | 0.020 / 0.016 / 0.012 | 54 / 62 / 38% | 0.71 | 0.001 / 0.001 / 0.001 | 0.026 / 0.024 / 0.026 | 86 / 87 / 64% |
| 3 | 0.018 / 0.014 / 0.010 | 32 / 46 / 18% | 0.72 | 0.002 / 0.002 / 0.001 | 0.023 / 0.020 / 0.024 | 88 / 89 / 66% |
| 7 | 0.020 / 0.019 / 0.017 | 12 / 14 / 3% | 0.72 | 0.006 / 0.004 / 0.007 | 0.025 / 0.021 / 0.025 | 89 / 84 / 61% |
| 12 | 0.025 / 0.027 / 0.028 | 6 / 3 / 3% | 0.69 | 0.014 / 0.011 / 0.015 | 0.028 / 0.025 / 0.028 | 91 / 89 / 54% |
| 21 | 0.043 / 0.047 / 0.044 | 3 / 0 / 0% | 0.62 | 0.030 / 0.022 / 0.029 | 0.030 / 0.029 / 0.032 | 88 / 89 / 52% |
| 39 | 0.052 / 0.052 / 0.052 | 7 / 0 / 0% | 0.48 | 0.040 / 0.027 / 0.043 | 0.034 / 0.036 / 0.038 | 78 / 83 / 49% |

- **The boundary sits in a dry belt.** Near the equator (about -7 to 12 degrees, 40 rows, 8-10 times the 4-6
  cells a grown body ends from its birth place) the upper west's ground is the driest on the map (dryness
  0.69-0.72; the lower continent's tropics 0.26), and it holds 0.010-0.020 bodies a land cell against about
  0.05 on either side. The leader's share falls through 50% inside it, on all three seeds.
- **Water sets the belt's depth.** At 0.05 under W1 the belt is empty (0.001-0.002 bodies a cell) and the
  leader holds nothing north of it; at 0.2 it holds 0.020-0.025 against 0.034-0.038 on either side (0.6-0.7
  of them, against 0.3 in the control), and the leader holds both sides. At `fresh` 0.05 a cell of dryness
  0.72 gives a body 0.014 of a pool's drink, and at 0.2 0.056: the belt is a barrier of thirst.
- **Thin alone does not hold.** The lower continent's north is as thin (0.017-0.020 bodies a land cell) and
  drier (0.78), and the leader holds it on seeds 9 and 10: it leads to no dense land held by other lines (its
  bodies stand in a highland forest, 1,240 m, crown 1.7). The belt lies between the leader's lands and a dense
  north (0.045-0.057 bodies a cell). Our reading: a thin place holds a boundary between two dense regions,
  where few of the leader's bodies arrive against many locals that breed as fast.
- **The boundary does not move.** In the control the leader's share in the upper west's north stays at 0-17%
  per 16,000 steps from 36,000 to 100,000, while its share in the upper west's tropics (the belt and its south side) climbs to 75-98% by the
  last window. At 0.2 its share in the north climbs through the run (seed 11: 3% to 86%).
- **The two lines are two ways of living.** Averages over the three seeds (control):

| bodies | size | hard | muscle | gut | open soft faces | meat | children / 1,000 steps | water |
|---|---|---|---|---|---|---|---|---|
| locals in the upper north | 27.5 | 2.2 | 7.1 | 17.8 | 18.9 | 43% | 5.06 | 0.52 |
| leader in the lower north | 33.5 | 7.9 | 12.6 | 12.9 | 15.0 | 51% | 4.69 | 0.64 |
| leader in the upper west's tropics | 39.7 | 6.7 | 10.3 | 22.0 | 19.4 | 42% | 4.98 | 0.36 |
| locals in the upper west's tropics | 49.1 | 5.2 | 10.3 | 33.1 | 23.5 | 39% | 4.75 | 0.29 |

  The locals of the upper north are small, soft grazers; the leader is an armored half-hunter. Where both
  live (the upper west's tropics: the belt and its south side) their bodies have children at about the same rate (4.98 and 4.75 per 1,000
  steps), and there both grow large guts.
- **The upper east** (the upper half's land east of the continent, reached from the far south) is held by
  locals too (the leader 1-3% in its north, 3-30% in its tropics) and has a shallower trough at the same
  latitudes (0.016-0.028 against 0.035-0.048).

**The hypotheses:**

1. A barrier: **yes**. Bodies thin to 0.3 of either side in a dry belt, the leader's and the locals' bodies do
   alike where both live, and at 0.2 the trough fills to 0.6-0.7 and the leader crosses.
2. The locals fit their place: **not needed**. The upper north's locals are another way of living, but where
   the two meet neither out-breeds the other, and the leader takes the north once it can cross.
3. First come, first held: **no**. The boundary stays in the belt for 64,000 steps on three seeds while the
   leader fills the belt's other side.

## Conclusion

The region the other lines hold is held by a barrier of thirst: a dry belt near the equator on the upper
continent, 8-10 lives of travel wide, where wet ground at `fresh` 0.05 gives almost nothing to drink and
bodies live at a third of the density on either side. The leader's spread stalls in it. Tighten water (W1)
and the belt empties; loosen it (`fresh` 0.2) and it fills to two thirds, the leader crosses, and the upper
north's grazers are replaced. So the kinds the control holds beyond the leader's come, in part, from a place
of the generated land that a line cannot cross, not from a law of the bodies.

What it changes: set D's small `fresh` has a second role, which it did not have when #88 set it: it makes
dry land a barrier. And kinds on this land follow the regions it holds behind barriers. c1225 has one clear
barrier (and a weaker one to the east). The next question is about the generated world: whether a land with
more such regions holds more kinds under the same laws (`balance.md` section 19).

Conditions: c1225, seeds 9-11, censuses 36,000-100,000; a grown body ends 4-6 cells from its birth place.
