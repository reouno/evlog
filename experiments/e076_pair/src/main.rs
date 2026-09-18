//! e076 adds no law and no instrument: it runs e075's binary (e074's invasion instruments are in that
//! crate) on stage C's default world (#92). The workspace takes every experiment folder as a crate,
//! so this stub is here. See `run.sh`, `batch.sh` and `README.md`.

fn main() {
    println!("e076 runs e075's binary: bash experiments/e076_pair/run.sh <world> <steps> <life> <name> ...");
}
