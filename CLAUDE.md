# CLAUDE.md

evlog: a self-evolving world that people enjoy watching.

When unsure, read `principles.md`.

## Current phase: R&D

Explore and prototype the core of the simulation (world, evolution, learning).
App, web, and monetization (ads) are ideas only. Do not build them now.

## How we work

- Start small. Expect to rebuild often and to have assumptions overturned.
- Build small, run long. The goal is to see what happens over long runs.
- Do not program the fun directly. Change rules and selection pressure, then observe what emerges.
- When a change adds compute cost, state why.

## Cost of running experiments

A batch of runs costs the machine (all cores for 1-2 hours lately) and the time until the
next decision. Before launching, say what the runs cost (cores x hours, and on which machine)
and what question each run answers. Then run the least that settles the question:

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

Every experiment must state, before starting:

- **Purpose**: why we do this
- **Hypothesis**: what we expect
- **Method**: what we verify and how (compare, measure, check feasibility, ...)

And must end with:

- **Result**: what happened, with numbers where possible
- **Conclusion**: clear answer to the hypothesis, and what it changes for the project

Record seed, parameters, and results. Use `experiments/TEMPLATE.md`.

Each experiment also ships a `report.html`. Build it with the `experiment-report` skill.

## Layout

Cargo workspace. Each experiment is its own crate: `experiments/eNNN_<name>/` with a `README.md` based on the template.
Experiments are disposable. Shared code moves to a separate crate only after it survives several experiments.

Run: `cargo run --release -p eNNN_<name>`

## Tech

- Language: Rust (strong types, fast, portable to WASM and mobile)
- Python for analysis and reports, managed with uv (`pyproject.toml` at the repo root; run scripts with `uv run python ...`)

## Conventions

- Conversation with the user: Japanese
- Everything committed (code, identifiers, comments, docs, commit messages): English. Use plain English in docs.
- Keep dependencies minimal. Start with the standard library.
