# e113: the sea as a place and the catch (#132)

Date: 2026-11-01

## Purpose

e112 left one line on one food: litter, 99.9% of the diet, flesh 0.14% at most, one size a world, 2.0-2.6 ways, and
the two largest ways are one body, on land and at sea. #116's two turns were met; the plan check of 2026-11-01 takes
them as one piece. The design, with its cycles and the reason for each law, is #132. The crate is e112's, copied, with
`ground=1 crown=1 tear=0` on in every run.

## Hypothesis

Written before the runs:

1. **A hunter lives** once a press is paid for what it breaks: the designed line is alive 10 years after it is put
   in, over half of its diet flesh.
2. **It does not empty the world**: with `sight` and `cover` what it finds is bounded by what it sees, and the other
   bodies are alive at the end; `hunter_press`, with no such bound, takes more of them.
3. **The sea is a place** (pilot): the deep floor is thin, islands hold their own lines, the ways at sea and on land
   are different bodies.
4. **Parted islands hold different sizes** (pilot): each has its own bottleneck, and two ways over 5% of the matter
   stand a decade apart in adult mass.

5. **A crash stays local** (added after the gate, before the pilot): a hunter that empties one island does not empty
   the world, because the sea stands between the islands.

Hypotheses 3 to 5 were to be read only if part 1 passed. It did not; the user chose on 2026-11-01 to run the pilot all
the same (see Part 2).

## Method

The laws, each behind a switch (0: e112's world): `floor`, `press_work`, `sight`, `cover` (`body.rs`, #132).

**Part 1, the gate**, on e112's trial world (`gate.sh`, 16 km, bodies sown in year 15, to year 40; a designed hunter
put in in year 20). Ubuntu, two threads each, six at once: about 30 minutes, under 6 core-hours.

| run | arguments on top of e112's `layers` | asks |
|---|---|---|
| `off` | none | is it e112's `layers` to the digit, over its 30 years |
| `all` | all four on | does the world stand with them |
| `hunter` | `all`, `inject_year=20 inject_kind=5` | does a hunter live, hypotheses 1 and 2 |
| `hunter_press` | `press_work=1`, the hunter | the press alone, nothing to limit what it finds |
| `hunter_nosight` | `press_work=1 floor=1`, the hunter | what `sight` and `cover` change |
| `no_floor` | `all` without `floor` | what `floor` does |

**Passed if** `off` is the same to the digit; `all` stands (ledgers under 1e-9, the land at least half of e112's
`nobody`); `hunter` meets hypotheses 1 and 2. If not, the traces say what the line died of, and the pilot does not run.

**Part 2, the pilot**, on `isles1` (`pilot.sh`, to year 100, all four on, sown in year 40 and in year 41; about 10
hours on six threads, Ubuntu). Controls: e112's `layers` and `sow41_tear0`, also from Ubuntu. Read with `control.py
pilot` and `analysis/ways.py`.

**Changed after the gate, by the user's decision of 2026-11-01.** The gate said the pilot does not run. It was not the
world starving that failed the gate but a hunter too strong for a world it can cross in hours, which the trial world
cannot read further. So the pilot runs, with the third run always and with a different purpose: `hungry70`, kind 3
put in on the largest island alone in year 70 (`inject_island=1`, a reading argument added for this: the default puts
the line on every island at once, which could not test a crash on one). Three runs at once, two threads each, about
15 hours in all, six cores:

| run | arguments on top of `pilot.sh` | asks |
|---|---|---|
| `all` | `years=100 tear=0 ground=1 crown=1 floor=1 press_work=1 sight=1 cover=1 threads=2` | is the sea a place; does flesh evolve where a press pays |
| `sow41` | the same, `body_sow=41` | the same in a second history; size by history |
| `hungry70` | the same as `all`, `inject_year=70 inject_kind=3 inject_island=1` | does a crash stay on its island |

`hungry70` is `all` up to year 70, which is checked first. e112's `sow41_tear0` ends at year 61, so `sow41` has a
control only up to there. The hypothesis 5 line is read from `_lines.csv`, and its failure says the sea does not part
the world even for a hunter. Lines, written before the run:

- Stands: ledgers under 1e-9; the land at least half of the bare world's over the last decade.
- The sea is a place: `held` by island at least 0.2 over each of the last two decades (e112: 0.03-0.27), and the
  largest ways at sea and on land differ in make or size (e112: the same body).
- The catch: flesh at least 1% of the diet over a decade (e112: 0.14%). Rung 3's line remains 10%.
- Size: two ways, each at least 5% of the matter, a decade apart in adult mass (e112: 2.8% and 2.1% at the second).
- A crash stays local (`hungry70`): island 1's bodies fall under half of `all`'s within ten years of the injection (if
  not, there was no crash to test), while the matter on all other islands, not of the designed line, stays at least
  half of `all`'s at years 75, 80, 90 and 100. Also read: the year the line first stands on each other island.

Compute: no new search. `sight` reads a length per body and searches the same 500 m at most; a body with small eyes
searches further than before only if a long body is in the world. Any cost beyond that is the number of bodies.

**Stop early if:**

- `bodies` < 10 at 540000

For the pilot (bodies sown in year 40 or 41; the step is year 45). Only a world without bodies stops a run. A
`hungry70` with no bodies left is ended by hand, since nothing can come back.

## Result

### Part 1, the gate: not passed; the pilot has not run

Ubuntu, 2026-11-01. Read by `gate.py` (`results/gate.csv`, `gate_line.csv`, `provenance.csv`). Two runs were added
after the first six, to ask whether the crash is the dose or the hunger: `hunter_few` (`inject_bodies=5`) and
`hunter_hungry` (`inject_kind=3`, which hunts when its fat is low). Ledgers 3e-13 at most in all eight. `analysis/audit.py` does not read this crate's
output (it looks for an `_agents.csv` census), so the audit was not done; the ledgers and `off`'s match stand for it.

- `off` is e112's `layers` to the digit (103 columns, 30 years).
- `all` stands: land 78% of `nobody` at year 30, 7,410 bodies at year 40 (`off` 92%, 2,526); no press lands, flesh 0.00%.
- **A press paid for what it breaks makes a hunter pay, and it empties the world in a year.**

| run | bodies, year 20 | year 21 | the world afterwards | the designed line |
|---|---|---|---|---|
| `hunter` (50) | 2,462 | 1 | none from year 22 | gone by year 22 |
| `hunter_few` (5) | 2,462 | 13 | none from year 27 | 48 bodies in year 23, gone by year 27 |
| `hunter_hungry` (50) | 2,462 | 197 | 2,493 in year 40, all of the line | alive at year 40, flesh 0.2% of the diet |
| `hunter_press` (50) | 851 | 2 | none from year 22 | gone by year 22 |
| `hunter_nosight` (50) | 718 | 4 | 148 in year 40, not of the line | gone by year 22 |

So hypothesis 1 is half right (the line grows on flesh, 52% of `hunter_few`'s diet in year 21, then has nothing to
eat) and hypothesis 2 is wrong: a tenth of the dose does the same, hunting only when hungry does the same, and the
only world with bodies at year 40 is the one its own line took over, gone back to litter.

Why, by arithmetic: this hunter passes 34% of its weight a day and keeps about half, so by that arithmetic (not
measured: the log is yearly) it can double in about a week at any size. In `off` the bodies double in about 11 years
(754 to 2,526 over years 20-40). Nothing in the world slows the first as the second
thins: `bench` puts its reach at 1,137 m in full light before the 500 m cap (a 0.03 m body at 341 m, a 0.1 m body at
500 m), and at full speed it crosses this 16 km world in under 2 hours.

**`sight` and `cover` as designed bite very little.** Today's eye is already far past the cap, so setting the 0.1 m body
at today's reach left most bodies seen at 500 m. That was visible in `bench` before the runs. The sea did not
save the prey either. Whether prey would learn to flee was not read: this prey met a full hunter with no time. The trial world is also too small to test the piece's hypothesis
(that a crash on one island is not a crash of the world): a hunter crosses it in hours.

### Part 2, the pilot: a hunter evolves, the sea is still not a place

Ubuntu, 2026-11-01, `isles1` to year 100, three runs at once on two threads each: `all` 11.3 hours, `sow41` 13.6,
`hungry70` 10.8. Read by `control.py` (`results/pilot_<run>.csv`, `_ways.csv`) and `crash.py` (`results/crash.csv`,
`crash_reach.csv`, `hunters.csv`, `flesh_eaters.csv`); thresholds in `results/provenance.csv`. `hungry70` is `all` to
the digit up to year 70, so these are two histories, not three: **the runs that make hunters share their first 70
years.** Ledgers 5e-12 at most. No audit, as in part 1.

| last decade, years 91-100 | `all` | `sow41` | `hungry70` | e112 `layers` | line |
|---|---|---|---|---|---|
| land of the bare world | 78% | 83% | 81% | 81% | at least 50%: **met** |
| flesh of the diet | 0.55% | 0.00% | 0.55% | 0.00% | at least 1%: **not met** |
| `held` by island, 81-90 / 91-100 | 0.08 / 0.13 | 0.11 / 0.07 | 0.07 / 0.07 | 0.15 / 0.24 | at least 0.2 in both: **not met** |
| ways (Hill) | 3.22 | 2.32 | 2.29 | 2.38 | - |
| size spread (Hill, `hill_size`) | 1.46 | 1.82 | 1.34 | 1.26 | - |
| bodies, mean | 33,583 | 51,124 | 32,609 | 44,222 | - |

**A hunter evolves and lives with its prey.** In `all`, genotypes with over half their lifetime diet in kills appear
in year 76 (one body) and stand at 1,090 bodies, 1,334 t, 2.7% of the matter at year 100, on ten land masses and at
sea, beside 33,000 others. They grow about 38-fold from year 83 to 100 (a doubling in about three years) and have been
flat at 1,235-1,334 t since year 97. The hunter's way at year 100: 18.4 kg, frame 0.36, muscle 0.31, gut 0.13, front
tip 0.35, kill 90% of the diet; the same founder's line as its prey, whose way is 18.4 kg, gut 0.56, muscle 0.19.
Kills rise to 0.79% of the world's diet in year 98. `hungry70` has the same outcome by its own descent after year 70
(1,087 bodies at year 100, none of the designed line). `sow41` has no genotype over 10% flesh at any census.

So in one history of two the catch is lived in. The world stays standing with it for 25 years; the run ends before it
is known whether this settles, keeps growing or crashes. No factorial was run: this is all four laws together, and
which of them it needs was not read. e112, without them, had none over 60 years.

**The sea is still not a place.** `held` is lower than e112's in all three, and the two largest ways of `all` are still
one body, on land and at sea: 18.4 kg, gut 0.56 and 12% at sea, 540 km a year (63% of the matter); gut 0.65 and 73% at
sea, 1,793 km a year (22%). `floor` lowered the share of bodies at sea only from 33% to 24-27%. What they live on out
there was not read beyond litter being 99% of the diet.

**Two sizes stand, not by island.** Two ways over 5% of the matter a decade apart at year 100, in all three: 18.4 and
0.57 kg in `all` (63% and 7.7%) and `hungry70` (80% and 6.9%), 18.4 and 244 kg in `sow41` (72% and 22%). This meets the
written line, but `held` says they are not parted by island, which was the hypothesis. Each small or large way has the
make of the largest: a change of size alone. Why it pays was not read.

**The designed hunter on one island.** Put on island 1 alone in year 70, it stands on eight land masses and the sea
within two years: the sea does not hold it. Kills that year are 20.6 million animals against 9,321 in `all`. It dies
of hunger by year 74, at 75% kills in its diet.

By the line as written there was **no crash to test**: island 1's bodies never fall under half of `all`'s (0.74 at the
least, year 74), its matter least 0.69 (year 74), and the other islands' matter is 0.89-1.08 of `all`'s at years 75,
80, 90 and 100. The line was written in bodies and matter, and that hid what happened. A body is a cohort, and
**animals** say otherwise: at year 72, 3.9 million on island 1 against `all`'s 64 million, and on the other islands 6.0
against 22.6 million, while the matter stands (animal counts swing widely in `all` itself, 61 to 920 million on those
islands between years 75 and 85, so only the first years' gap is read). Animals fell far more than matter, which reads as the young eaten on every island
at once and the adults left (not measured directly), and the world came back within about ten years, not because the sea held the hunter but because
the hunter starved. This differs from the trial world, where the same body took the world over. Why was not read.

## Conclusion

Under this world's conditions, on one seed:

1. **A hunter lives: yes, when evolved; no, when designed.** The designed line dies in four years; the evolved one
   stands 25 years to the run's end, in one history of two. Flesh remains under 1% and far under rung 3's 10%.
2. **It does not empty the world: yes on `isles1`, so far.** But `sight` and `cover` have not been shown to be why, and
   the trial world says otherwise. The 25 years end with hunters flat, and a run to year 100 cannot say what follows.
3. **The sea is a place: no.** Bodies cross it, and live on it as one body with those on land. `floor` did not change this.
4. **Parted islands hold different sizes: no as stated.** Two sizes do stand, in each run, but not by island.
5. **A crash stays local: no.** A hunter on one island reached the others within two years. The world held because it starved.

`press_work` is kept: a press priced by what it breaks replaces a price recorded as wrong in e112. `floor`, `sight` and
`cover` stay in the crate, on, with no effect shown. Rows changed in `vision.md`: C size, F ways, F food web, the lessons
and the direction.
