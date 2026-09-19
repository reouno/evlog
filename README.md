# evlog

A world that evolves on its own, for people to watch. Research and development stage.

- `principles.md` - purpose and rules that do not change. Read this first.
- `vision.md` - the ideal, today's world against it, and the next piece of work.
- `foundation.md` - how the world is built and searched, and today's default world.
- `CLAUDE.md` - how we work, and when each document is read and changed.
- `experiments/` - one folder per experiment: code, `README.md` from purpose to conclusion, `results/`, and
  `report.html` with charts and a plain-English write-up.

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
