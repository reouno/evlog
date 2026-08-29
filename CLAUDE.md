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

## Experiments

Every experiment must state, before starting:

- **Purpose**: why we do this
- **Hypothesis**: what we expect
- **Method**: what we verify and how (compare, measure, check feasibility, ...)

And must end with:

- **Result**: what happened, with numbers where possible
- **Conclusion**: clear answer to the hypothesis, and what it changes for the project

Record seed, parameters, and results. Use `experiments/TEMPLATE.md`.

## Tech

- Language: Rust (strong types, fast, portable to WASM and mobile)
- Python is allowed for analysis and plotting scripts

## Conventions

- Conversation with the user: Japanese
- Everything committed (code, identifiers, comments, docs, commit messages): English. Use plain English in docs.
- Keep dependencies minimal. Start with the standard library.
