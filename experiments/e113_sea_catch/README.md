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

Hypotheses 3 and 4 are read only if part 1 passes.

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
pilot` and `analysis/ways.py`. A third run, the hunter put in in year 70 (5 hours), only if neither history makes
flesh. Lines, written before the run:

- Stands: ledgers under 1e-9; the land at least half of the bare world's over the last decade.
- The sea is a place: `held` by island at least 0.2 over each of the last two decades (e112: 0.03-0.27), and the
  largest ways at sea and on land differ in make or size (e112: the same body).
- The catch: flesh at least 1% of the diet over a decade (e112: 0.14%). Rung 3's line remains 10%.
- Size: two ways, each at least 5% of the matter, a decade apart in adult mass (e112: 2.8% and 2.1% at the second).

Compute: no new search. `sight` reads a length per body and searches the same 500 m at most; a body with small eyes
searches further than before only if a long body is in the world. Any cost beyond that is the number of bodies.

**Stop early if:**

- `bodies` < 10 at 540000

For the pilot (bodies sown in year 40 or 41; the step is year 45). Only a world without bodies stops a run.

## Result

### Part 1, the gate: not passed; the pilot has not run

Ubuntu, 2026-11-01. Read by `gate.py` (`results/gate.csv`, `gate_line.csv`, `provenance.csv`). Two runs were added
after the first six, to ask whether the crash is the dose or the hunger: `hunter_few` (`inject_bodies=5`) and
`hunter_hungry` (`inject_kind=3`, which hunts when its fat is low). Ledgers 3e-13 at most in all eight.

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

Why, by arithmetic: this hunter passes 34% of its weight a day and keeps about half, so it can double in about a
week at any size. In `off` the bodies double in about 15 years. Nothing in the world slows the first as the second
thins: `bench` puts its reach at 1,137 m in full light before the 500 m cap (a 0.03 m body at 341 m, a 0.1 m body at
500 m), and at full speed it crosses this 16 km world in under 2 hours.

**`sight` and `cover` as designed bite very little.** Today's eye is already far past the cap, so setting the 0.1 m body
at today's reach left most bodies seen at 500 m. That was visible in `bench` before the runs. Evolved prey never
flee in a year, and the sea did not hold prey either. The trial world is also too small to test the piece's hypothesis
(that a crash on one island is not a crash of the world): a hunter crosses it in hours.

## Conclusion

Part 1 only, under this world's conditions. The starving of e112 was the press's price. Under it there is a second
wall, as #116's turn said: a slower body is caught every time and nothing limits what a hunter finds, so a hunter that pays grows
far faster than its prey and the world has no place it does not reach. What the islands do about it is not yet read.
`vision.md` is updated when the piece ends.
