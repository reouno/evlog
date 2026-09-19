//! e085 runs no world of its own: it runs e061's climate with maps=1 on stage A's passing climates
//! (`maps.sh`) and counts their regions with e084's rule (`regions.py`). The workspace takes every
//! experiment folder as a crate, so this stub is here. See `README.md`.

fn main() {
    println!("e085: bash experiments/e085_climate_regions/maps.sh, then uv run python experiments/e085_climate_regions/regions.py");
}
