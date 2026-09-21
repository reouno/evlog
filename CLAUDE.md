# CLAUDE.md

evlog: a self-evolving world that people enjoy watching.

When unsure, read `principles.md`.

## Current phase: R&D

Explore and prototype the core of the simulation (world, evolution, learning).
App, web, and monetization (ads) are ideas only. Do not build them now.

## How we work

- Build the world whole, then search it (`foundation.md`): keep laws, generated terrain and emergent
  outcomes apart, and search parameters in stages from the cheapest layer. Do not test one law at a
  time in a world that lacks its conditions. Expect to rebuild often and to have assumptions overturned.
- Choose the next step from `vision.md` (the ideal against today, by layer), not as a fix of the last result, and
  fill the largest gap as one piece of several laws designed as cycles. Every result updates `vision.md`.
- Run long. The goal is to see what happens over long runs.
- Do not program the fun directly. Change rules and selection pressure, then observe what emerges.
- When a change adds compute cost, state why.

## Documents

One fact lives in one place; the others point to it. History lives in the experiments' READMEs and in git, never
in the documents below. A new document needs a role none of these has.

**A document maintained forever must not grow**: each stays under 120 lines - check when you edit one. Update by
rewriting the rows a result changed, never by appending; a row that wants a paragraph gives the paragraph to an
experiment's README and keeps the one sentence that decides the next step (`vision.md` reached 307 lines of it).

| document | holds | read it | change it when | never change it for |
|---|---|---|---|---|
| `principles.md` | purpose, principles, decision rules | when unsure what is allowed or what matters | the user agrees to a change of direction | an experiment's result |
| `vision.md` | the ideal, today against it by layer, lessons that hold across experiments, the next piece | before choosing or designing a step | after every experiment: the rows its result changes (today, gap, ranking; the ideal or the next piece when the result says so) | a record of what happened |
| `foundation.md` | how the world is built: laws, generated and emergent parts, material trade-offs, stages and measures, today's default world | before designing or building a law | a law or measure is kept or removed, or the method changes | a result that kept nothing |
| `CLAUDE.md` | how we work | every session | the way of working changes | project facts |
| GitHub issues | tasks, and a piece's design while it runs | when starting or resuming work | the work is planned, changes or ends | - |
| `experiments/eNNN_*/README.md` | one experiment, from purpose to conclusion | when its result is needed | while it runs; afterwards only to correct it | - |
| `README.md` | what the repo is and how to run it | - | the layout changes | results |

## Cost of running experiments

A batch costs the machine (all cores for 1-2 hours lately) and the time until the next decision. Before launching,
say what the runs cost (cores x hours, on which machine) and what question each answers. Run the least that
settles it:

- A law test that can be judged by "does the world stand, and what wins" needs a pilot and
  a handful of seeds, not twelve. Add seeds or worlds only when the first result is unclear.
- Prefer a short run (100k-300k steps, a few minutes) to settle whether a change works at all,
  and a long batch only for the measures that need it (shape trends settle by 300-500k steps).
- Leave cores free: at most 11 of the 12 local cores, fewer when the user is working.
- A run that is needed is run without hesitation. A run that is only "for completeness" is not.

## R&D stance

- The key question is "what can be realized". Do not drift into side discussions or local optimization.
- No unnecessary tuning or micro-optimization of algorithms or code. Complexity without a reason is a loss.

## Experiments

Every experiment states before starting - **Purpose** (why), **Hypothesis** (what we expect), **Method** (what we
verify and how) and **Stop early if**: each rule a log column, a threshold and a step (`- pop < 500 at 20000`), read
by `watch.py`, and only failed preconditions (the world does not stand, the mechanism never engages), never the
measure it is judged by. It ends with **Result** (numbers where possible) and **Conclusion** (the answer to the
hypothesis and the rows of `vision.md` it changes). Record seed, parameters and results; use `experiments/TEMPLATE.md`.

A law that needs a behavior is tested in a world where that behavior already pays: name the two conditions together
("Y pays when A and B") and run the minimal combination, not a factorial. Naming them is not enough - the world is a
web of cycles. Before proposing a change, write what it takes from whom, what refills it, which feedback limits it,
and the balance it should settle into (who wins where and when). Add and remove parts together so the design holds.

Each experiment also ships a `report.html`. Build it with the `experiment-report` skill,
and keep it inside the skill's word budgets: a report is read only if it is short.

## Measuring

Fix as shared code only what decides **how a body is classified** - it has changed twice in thirty experiments.
What a particular law means stays in that experiment's `sweep.py` and is not built out.

- `analysis/` holds the schema of a census, the audit of a run and how two replays of one world are compared
  (`replay.py`, #112), and depends on no experiment.
- **A census column no reader has classified stops the reading** (`analysis/schema.py`): when a crate writes
  something new, the analysis fails loudly instead of counting the world wrong in silence. The blocks a birth form
  is parted by come off the census's own columns, so a new kind of block rewrites no line of analysis.
- Every sweep writes `results/provenance.csv` - the window it read and every threshold it classified by - and
  its report prints it. What a README or a report says about a reading is quoted from that file, never from
  memory (e094 said 65 censuses where the reader takes 51).
- After a batch, before reading anything: `uv run python analysis/audit.py <results dir>`.

## Layout

Cargo workspace. Each experiment is its own crate: `experiments/eNNN_<name>/` with a `README.md` based on the template.
Experiments are disposable, but `analysis/`, `experiments/e060_census/census.py` and `experiments/e068_kinds/kinds.py`
are not: every reading since e068 goes through them. Shared code moves out of an experiment only after it survives
several of them.

Run: `cargo run --release -p eNNN_<name>`

The world is watched in 3D through `viewer/` (see its README): an experiment writes frames in three
lines and the browser draws them, live or as a replay. Nothing happens unless EVLOG_VIEW is set, and
a new law reaches the viewer by adding its layer or field to `Init` (the header says what a world holds).

## Tech

- Language: Rust (strong types, fast, portable to WASM and mobile)
- Python for analysis and reports, managed with uv (`pyproject.toml` at the repo root; run scripts with `uv run python ...`)

## Conventions

- Conversation with the user: Japanese
- Everything committed (code, identifiers, comments, docs, commit messages): English. Use plain English in docs.
- Keep dependencies minimal. Start with the standard library.
