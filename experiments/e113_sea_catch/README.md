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

- `bodies` < 10 at 4000

Only a world without bodies stops a run (the rule is read from a step after both worlds' sowing has settled; `step` is
the log's).

## Result

## Conclusion
