# e073: wood a body can live on, and a cold that differs by place (stage C's eleventh step, #89)

Date: 2026-09-16

## Purpose

e072 built the seven balance sets together and the user kept them as stage C's default world (#88).
Two of the seven did nothing there, and both were meant to part the land from itself:

- **wood as food** was 0.0-0.3% of what any kind ate, and
- **the heat** never parted the temperature bands (5-7% of the land's bodies in the cold band, as in
  the controls), because it reads a cell's temperature at the moment and the day swings it by tens of
  degrees (e071's finding).

This rebuilds those two on the default world and searches them together, as #87 asks of a law that
needs a condition: a body eats wood where a forest stands, and a forest stands where the cold lets it.

## The dry run, before any of it was built

`dryrun.py` (no runs of the bodies: c1225's terrain rebuilt as `climate.rs` builds it, e063's settled
world for the standing wood, the climate's temperature run alone in numpy for two years, and e072's
three runs for what the bodies did). It settled which shape each law takes.

**Wood is patchy enough** (#68 rule 1). A body covers 1.8-5.7 cells in a life. Averaged over a window
of 6 cells the standing wood still spreads 1.91 times its own mean (p50 0.04, p90 2.37 a cell), and
over 48 cells 1.67; the grass spreads 0.71 and does not move with the window. Wood is the first food
of stage C whose grain a body cannot average away.

**But a stand cannot be eaten, at either of the issue's first two rates.**

| what is taken | what it offers a 1,000 steps | against the 37,000 the bodies eat |
|---|---|---|
| the whole standing forest, once | 66,600 | 1.8 thousand steps of food, and then it is gone |
| `wood_food` 0.04 (the default) | - | eaten to a tenth of its stand by step 12,000, then 0.06% of the intake |
| the most of its *growth* a stand can give up | 1,300 | 3.5%, and only if every stand is grazed to its limit |

The last row is the ceiling on the issue's option (b). A stand holds where its growth answers its
death, `R L s/(s+H) = s`, so `R L = s + H`: the share of its growth it can give up before it falls is
exactly its own cover, `s/(s+H)`. That is 9% on a mean land cell and 49% on the richest tenth, and
over the whole land 1,300 a 1,000 steps. Wood cannot be a living off its stock or off its growth.

**So the yield is built as a third thing, a flow beside the stand** (the law below). At `wood_yield`
3e-4 it offers 20,000 a 1,000 steps, and in the richest tenth of the land a cell yields 1.15 against
the 1.06 of grass the same cell grows: in a forest, browse matches the grass; on the lawn there is
none.

**The day's mean is a place; the moment is not.** Over a year of c1225's climate, the moment stands
20 C from the day's mean on a median land cell (p90 23 C). By the moment, **every** land cell is cold
(under `warm_lo` 15 C) between a third and three quarters of the year - none is cold as a place and
none is spared. By the day's mean, 37% of the land is cold one day in ten or less and the rest is cold
by the season: the spread between places goes from 0.31 of its mean to 0.88. Both are broad (neither
moves when averaged over 48 cells), so what the mean adds is not grain but place.

## The two laws

Each as a rate whose 0 is e072 exactly (`main.rs`'s header has them in full).

- **The crown's yield** (`wood_yield`, `plants.rs`). A stand of wood drops `wood_yield` of `browse`
  per unit of what it stands a step, out of its cell's soil and beside its own growth; the trunk is
  not touched, so the stand keeps its shade and its fire. Browse uneaten rots into the soil at the
  litter's rate (warmth x water), so it keeps where the ground is cold or dry. A gut takes it with
  the hard tip of force `wood_hard` that e072's stock share needed, and a body whose tooth can take
  it sees it, as it sees the grass. Fire does not read the browse (stage B's law is left alone; fire
  burns 0.06 of matter over 100,000 steps of this world).
- **A cold that differs by place** (`day_temp`, `climate.rs`). The climate keeps `temp_day`, a running
  mean of each cell's temperature over the last day (a weight of `tick`/`day` an update), and a body's
  heat reads `day_temp` of the way from the moment to that mean. It costs one pass over the cells per
  climate update, one every ten steps, against the per-step pass over every body's blocks.

## Hypothesis

Written before the runs, with the conditions named together (#87): **a kind lives by wood when a
forest stands (A) and when what it stands yields a flow (B); and a kind keeps to a temperature band
when the cold is a property of the place (C) and something else pays there (A).**

Against e072's runs on the same seeds (the controls: 5.78 kinds at a census, the leanest of six 5 / 4
/ 6, 2 / 2 / 1 kinds keeping 90% of their bodies to one medium, none keeping to a temperature band,
wood 0.0-0.3% of any kind's food):

1. **A kind lives by wood.** At least one combination holds a kind that takes 20% or more of its food
   from browse, and that kind keeps 90% of its grown bodies to the land.
2. **A kind keeps to a temperature band.** Under `day_temp` 1, at least one combination holds a kind
   that keeps 90% of its grown bodies to one of the cold / mild / hot bands, which no control does.
3. **The two need each other.** The yield holds more kinds at a census with `day_temp` 1 than with 0,
   and the cold holds more with the yield than without it.
4. **The worlds stand.** Every combination keeps bodies in all three media through 50,000 steps and
   conserves matter.

## Method

Code: `experiments/e073_forest`, e072's crate with the two rates. Tests: the crowns drop browse out of
the soil, the trunk is not touched and the browse rots (matter holds); a tooth makes the browse food;
the day's mean swings less than the moment and `day_temp` 0 / 0.5 / 1 read the moment, half way and
the mean; matter is conserved with all nine rates on at once, where each leaves its mark.

**The check**: with both rates 0 the first 10,000 steps must equal e072's run for seed 9
(`c1225_life9_sets`) in every column of the log but the wall times, in every body of the census at
step 10,000, in every lineage row and in every event.

**The search** (`search.py`): 11 runs on c1225 with e062's draw d11, seed 9, 50,000 steps each, the
default world's sets under them. Not a hypercube - two laws, crossed:

| run | `day_temp` | `wood_yield` | `wood_food` | `wood_hard` | what it answers |
|---|---|---|---|---|---|
| d00 | 1 | 0 | 0.04 | 3 | the cold by place alone, on the default world |
| d01 | 0 | 0 | 0 | 3 | the forest left standing, no new law: the wood control |
| d02 | 1 | 0 | 0 | 3 | the forest standing and the cold |
| d03 | 0 | 1e-4 | 0 | 3 | the yield alone, a fifth of what is eaten |
| d04 | 0 | 3e-4 | 0 | 3 | the yield alone, half of it |
| d05 | 1 | 3e-5 | 0 | 3 | both, the yield a twentieth |
| d06 | 1 | 1e-4 | 0 | 3 | both, the yield a fifth |
| d07 | 1 | 3e-4 | 0 | 3 | both, the yield half |
| d08 | 1 | 3e-4 | 0 | 2 | the same with e060's tooth: has a tooth one use or two |
| d09 | 1 | 3e-4 | 0.04 | 3 | the same with the default's share of the standing stock still on |
| d10 | 0 | 0 | 0.3 | 3 | the windfall large enough to pay for the tooth that takes it |

    uv run python experiments/e073_forest/search.py 50000 9
    xargs -P 11 -L 1 ./target/release/e073_forest < experiments/e073_forest/results/search/candidates.txt

The control is e072's `c1225_life9_sets` read over the same window (steps 25,000-50,000).

Read with `sweep.py`: the kinds by birth form at a census and held at every census (e068's `kinds.py`),
how many keep 90% of their bodies to one medium and how many to one temperature band, the browse's
share of each kind's food, the standing wood and browse, the deaths by cause, and the land's matter.

**Then** three seeds (9-11) at 100,000 steps at what the search picks, judged against e072's runs on
the same seeds by stage C's measure (#88): the kinds at a census, the leanest census of the six, and
the kinds kept to a place.

**Decision rule, set before the runs.** The laws are kept as stage C's default if, on the three seeds
at 100,000 steps, a kind lives by wood (20% or more of its food from browse) on at least two seeds
**and** the kinds at a census do not fall below the controls' 5.78. `day_temp` is kept if a kind keeps
90% of its grown bodies to one temperature band on at least two seeds. The two are judged apart: the
search says whether they need each other.

**Cost, before the runs.** The search is 11 runs of 50,000 steps on 11 local cores, one round, about
45 minutes (a step is 23.5 ms on this world). Round two is 3 runs of 100,000 steps, about 50 minutes
on 3 cores. Nothing on the Ubuntu box: 11 runs fit locally.

## Result

(to be written)

## Conclusion

(to be written)
