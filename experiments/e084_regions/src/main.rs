//! e084 runs no world of its own: it reads e062's producers-only maps (`regions.py`) and, for bodies, runs
//! e082's binary on another world (`batch.sh`). The workspace takes every experiment folder as a crate, so
//! this stub is here. See `README.md`.

fn main() {
    println!("e084: uv run python experiments/e084_regions/regions.py");
}
