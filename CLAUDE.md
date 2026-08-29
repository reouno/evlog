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

Each experiment also ships a `report.html` in its folder: charts and a plain-English write-up
for a reader who does not know the code or the algorithms. Self-contained (inline SVG, no external assets).

## Layout

Cargo workspace. Each experiment is its own crate: `experiments/eNNN_<name>/` with a `README.md` based on the template.
Experiments are disposable. Shared code moves to a separate crate only after it survives several experiments.

Run: `cargo run --release -p eNNN_<name>`

## Tech

- Language: Rust (strong types, fast, portable to WASM and mobile)
- Python is allowed for analysis and plotting scripts

## Conventions

- Conversation with the user: Japanese
- Everything committed (code, identifiers, comments, docs, commit messages): English. Use plain English in docs.
- Keep dependencies minimal. Start with the standard library.
