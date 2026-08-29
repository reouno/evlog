# evlog

A world that evolves on its own, for people to watch. Research and development stage.

- `principles.md` - purpose and rules that do not change. Read this first.
- `vision.md` - where we are heading now. Changes as we learn.
- `CLAUDE.md` - how we work in this repo.
- `experiments/` - one folder per experiment: code, `README.md` with hypothesis and conclusion, `results/`, and `report.html` with charts and a plain-English write-up.

## Experiments so far

| # | Question | Answer |
|---|---|---|
| e001 | Does the simplest evolution loop survive a long run? | Yes, cheaply. But the world stops changing once one strategy wins. |
| e002 | Can a DNA-like string produce traits that vary, mutate in small steps, and cannot be read by hand? | Yes. Caveat: every gene touches every trait. |
| e003 | Can selection climb that genome map when traits have costs? | Yes, fast. But traits without a two-sided trade-off pin at the edge, and unrelated traits get dragged along. |
| e004 | Can the gene network grow a body on a grid? | Yes: position fed in as morphogens gives connected, varied bodies at 0.2 ms each, heritable under mutation. Bodies are dense by default; mutations move regions, not blocks. |

## Running

Rust workspace, one crate per experiment:

```
cargo run --release -p e001_minimal_world -- 1000000 1
```

Reports are built with Python (matplotlib) managed by uv:

```
uv sync
uv run python experiments/e001_minimal_world/report.py
```

Work is tracked in GitHub issues.
