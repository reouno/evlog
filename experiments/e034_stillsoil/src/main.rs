//! e034: the soil barely moves (#35). e033's code, unchanged: the flow rate (argument 8, a share
//! of a cell's soil that runs downhill per step, 0.1 since e019) is run at 0 (e018's world:
//! nothing flows) and at 0.001 (a hundredth of e019's rate) in the season world (`rain flat`,
//! `winter high` 2, store 5, grow), and then `rain high` under the tiny flow: with the soil
//! staying where it falls, the rain's place can be the soil's place, and e033's question (is
//! the ridge worth holding) is asked for real. The premise (the user, after e033): what runs
//! downhill in the real world is water, not soil; the soil is roughly uniform and rich where
//! the dead and the dung lie. e019's flow moves the nutrient itself at a tenth of the drop per
//! step, 10-100x what a plant uses, and the lake in the valley and the barren ridge are that
//! shortcut's. No law is new; the results go to `experiments/e034_stillsoil/results`.
//!
//! e033: the wet ridge. e032's world (the winter by height, kept at amplitude 2) with e020's
//! rain on the mountains instead of the rain on every cell alike: `rain high`, an argument
//! since e020 (the most the air can rain on a cell per step is RES_GROWTH times its height
//! over the relief, so the bottom of the valley gets no rain and the ridge the most; the soil
//! runs downhill as before). No law is new: the two places are a trade-off now (the rain on
//! the ridge, the winter sun in the valley), and the question is what the bodies do with it.
//! `pop.csv` gets the soil per height band every 1,000 steps (`soil0`, `soil1`, `soil2`).
//!
//! e032: a winter that differs by place. e031's world (the store at 5, the yolk and breeding as
//! a decision off) with one law about the world changed, in a form that runs alone:
//!
//! - `winter high`: the season's amplitude is the cell's, by its height. A cell at height h
//!   under the season of amplitude `a` gets the sun's rate RES_GROWTH times
//!   (1 + min(1, a h / relief) sin(2 pi t / SEASON)): the bottom of the valley has no season,
//!   a cell at the relief (the highest third of the world stands from 0.57 to 1.13 of it) gets
//!   the whole of `a`, and no cell's sun goes below zero. The mean sun over a season is the
//!   same on every cell (a sine averages to nothing), so the world's matter and the sun a
//!   place gets over the year are e031's; what differs by place is the winter. `a` may exceed
//!   1 here: at 2 every cell above the mean height (half the world) goes dark at midwinter, and
//!   the world's sun at that instant is a quarter, the same as the flat season's at 0.75. The
//!   real world's premise: the winter is harsher the higher (and the farther from the equator)
//!   a place is, and animals leave it, huddle, or carry a store. `winter flat` (the default)
//!   is e031 byte for byte: the same amplitude on every cell.
//!
//! The log's `sun` is the mean of the cells' factors over the log interval (1 in every world
//! that stands: the season averages out). `pop.csv` gets, every 1,000 steps, the bodies in
//! each height band (`pop0` valley, `pop1` slope, `pop2` ridge) and of those the bodies born
//! in another band (`cross0`, `cross1`, `cross2`): where the bodies are through the season, and
//! whether they moved there. `terrain.json` records `winter`.
//!
//! e031: the child of the flesh, and breeding as a decision (not kept; `yolk` and `breed` stay
//! as arguments, 0 by default). e030's world with two laws that run alone or together:
//!
//! - `yolk`: a child is made of its parent's flesh. With half of the parent's energy the child
//!   gets the share `yolk` of the parent's fat (0: e030, the child is born with none). A child
//!   never placed lays its fat with its energy where the parent stands.
//! - `breed`: breeding is the body's decision, like moving. The policy has a fifth output,
//!   read from the gene table like the other four (its column drawn from its own stream, so the
//!   bodies and the four actions are e030's); when it wins the step's decision and the body's
//!   energy is at the threshold (2 + 0.1 mass, as before) the body stays and breeds; a body
//!   below the threshold takes the best of the four moves instead. With `breed` 0 a body
//!   breeds whenever its energy reaches the threshold (every experiment up to e030).
//!
//! `pop.csv` records every 1,000 steps the bodies alive, the share at zero energy, the fat in
//! all bodies and the mean age (the winter floor at the lineage log's resolution); the log
//! gets `breed_share` (decisions that were to breed) and `breed_denied` (of those, the share
//! made below the threshold, so nothing happened).
//!
//! e030: a store a body can spend. e029's world (the grid's side an argument, 8 by default;
//! `grow` lets the genome express it) with one law about the flesh changed:
//!
//! - The fat a body fixes from its upkeep (the flesh law, e024) is the body's own store. A body
//!   whose energy cannot pay its upkeep pays the rest from its fat; what is paid from the fat
//!   is breathed (to the air, as the burned share of the upkeep is), never fixed again, so a
//!   body living on its fat loses it at the rate of its upkeep and dies when it is gone. The
//!   flesh holds at most `store` of fat per unit of the body's mass (the weight law's mass:
//!   what the body is made of); what is fixed beyond that is breathed. The fat still goes to
//!   the eater when a cell is broken and to the ground when the body dies (e024's worth), and
//!   a child gets half its parent's energy as before, none of its fat. Nothing else changes:
//!   `store` 0 is e029 byte for byte (the fat is never spent and has no ceiling).
//!
//! The log gets `fat_spent` (fat burned by bodies short of energy, per step), `fat_over` (fat
//! breathed for want of room in the flesh, per step) and `on_fat` (the share of bodies whose
//! energy is at zero, living on their fat); `terrain.json` records `store`.
//!
//! e029: small and large bodies in one world (#28). e028's world (the digestion law off by
//! default, `digest` 1 stays an argument) with the ceiling of the body's grid raised:
//!
//! - A body grows on a grid of `side` by `side` cells, SIDE_MAX (16) at most; every experiment
//!   up to e028 grew every body on 8 by 8. The development is the same (position as morphogen
//!   input, the six gradients spanning the grid whatever its side: a pattern scales with the
//!   body it is written on, so side 8 is e028's field and a larger side samples it finer).
//!   `side` is a number (every body on that grid; 8 is e028 byte for byte) or `grow`: the
//!   genome expresses the side, read from the run without position like the density, as
//!   8 * 2^(2 sigmoid(s) - 1) rounded, 4 to 16. The world's laws do not change: the upkeep is
//!   per cell, the mass is what the cells weigh, a child costs its mass, a body lies over the
//!   world cells under its cells (up to 5 by 5 now). A child is placed within a grid's side
//!   of its parent's anchor (the larger of the two; eight sub-cells up to e028).
//!
//! The log gets `side_mean`, `side_std` and the size in cells at p10, p50, p90 and max;
//! `agents.csv`, `lineages.csv` and `bodies.jsonl` get `side` (the cells string of a body
//! is side * side characters).
//!
//! e028: what a gut digests (#32). e026's closed world (e027 ran it unchanged) with one law
//! about the gut material added:
//!
//! - The genome expresses a digestion axis `digest` d in [0, 1] per body, read from the gene
//!   network like the density (sigmoid of a sum; the table's column for it draws from its own
//!   stream). A gut takes what lies under it as before (the body still eats whatever is there),
//!   but digests plant matter (the standing plant and the fruit) at 1 - d / 2 and flesh (the
//!   dead matter on the ground, a broken cell of another body with its share of energy and
//!   fat) at 1/2 + d / 2 (DIGEST_FLOOR is the 1/2): the far ends of the axis get the whole of
//!   one food and half of the other, the middle three quarters of both (`digest` 1, the
//!   line). `digest` 2 is the sharp curve: plant at 1 - sqrt(d) / 2, flesh at
//!   1 - sqrt(1 - d) / 2, the same ends and the middle at 0.65 of both, so that a gut for
//!   both is worse than the mean of the two guts. What is taken and not digested is dung: it
//!   goes to the soil under the cell it was taken from, so the ledger holds. The axis touches
//!   nothing else (not the tooth, not the eye, not the weight).
//!
//! `digest` 0 is e026 byte for byte (the axis is expressed and logged, and does nothing). The
//! log gets `digest_mean`, `digest_std`, `flesh_guts` (the share of bodies with d over 1/2)
//! and `dung` (matter taken and not digested, per step); `agents.csv` and `lineages.csv` get
//! `digest`. `plant_intake` and `meat_intake` are what was digested; the takes from the
//! ground (`fruit_eaten`, `tree_eaten`) are what left the ground.
//!
//! e026: weather (#24). e025's closed world (the canopy, the spill, the air that rains on
//! every cell alike, mutation per base, eyes that see far, the flesh law, the weight law, the
//! ledger as f64) with one law about the world added, in two forms that run alone:
//!
//! - `cloud`: the rain falls where a slowly changing field says. The most the air can rain on a
//!   cell per step (its cap) is the cap of e025 times a weight that varies over the world at
//!   the terrain's grain (WEATHER_GRAIN cells) and over time with a memory of WEATHER_SPAN
//!   steps, and drifts east at WIND cells per step. The weight is lognormal with mean 1
//!   (exp(sigma x - sigma^2 / 2), x a unit Gaussian field), so a place's rain has a mean and a
//!   variance; the world's rain is what the bodies breathe, as before (the air empties every
//!   step when the caps add up to more than it holds). `sigma` is the amplitude (1: a wet cell
//!   gets 2.2 times its mean, a dry one a sixth, one cell in ten each).
//! - `season`: the sun's rate varies with time, RES_GROWTH times (1 + a sin(2 pi t / SEASON)),
//!   the same on every cell; `a` is the amplitude (1: the sun goes out at midwinter).
//!
//! Nothing else changes; `weather` 0 is e025 byte for byte (the field draws from its own
//! stream). The log gets `sun` (the sun's factor, mean over the log interval) and `cloud_std` (the
//! standard deviation of the rain weight over the cells); `weather.csv` records the field's
//! nodes every WEATHER_LOG steps, and `terrain.json` the spectrum used.
//!
//! Kept from e025:
//! - A block weighs by its kind, times a density the genome expresses. A hard block weighs 2,
//!   a sensor 1/2, muscle and gut 1 (KIND_MASS); the body's density, read from the gene
//!   network like the policy, from 1/2 to 2, scales every block. The mass is what the body is
//!   made of (a child costs cell_energy times its mass; a broken or dead block yields the
//!   matter it was made of), what it moves with (the work of moving is mass times distance;
//!   speed is muscle over mass; a shove needs more muscle than the shoved body's mass), and
//!   what its faces resist with (a face's hardness is the material's, 3 per hard cell or 1,
//!   times the density: light armor is weak armor). The upkeep stays per living cell.
//!   `weight` 0 is e024's law (every block 1, density 1) on the f64 ground; `kind` and
//!   `density` switch the two halves on alone. The ground and the bodies' ledger are f64 (#31).
//!
//! Kept from e024:
//! - The flesh keeps a share of what the body burns. Of the upkeep a body pays each step, a
//!   share `flesh` (1 by default) is fixed in its flesh (`fat`) instead of breathed to the
//!   air; the body cannot spend it. Whoever breaks a cell of the body gets the cell's matter
//!   plus the cell's share of the body's energy and fat; a body that dies lays its fat on the
//!   ground with the rest.
//!
//! Kept from e023:
//! - A sensor sees a distance. A body sees the row of cells one cell ahead (and behind, left,
//!   right), and one more cell per sensor block, up to `eyes` more (8 by default). What lies j
//!   cells away is seen at 1/j: the light that reaches the eye falls with the distance. The
//!   inputs are the same ten (food under the body; food and crowd in four directions; energy),
//!   summed over the range. A body with no sensor sees one cell; e022's bodies saw two, the
//!   second weighted by sensors / 8 (`eyes` 0 keeps that law). The cost of a sensor is what it
//!   was (upkeep per block): range is paid for. The knockout (e009, `sense_used`) compares
//!   every decision of a body with sensors to the same body seeing one cell.
//!
//! Riding along (#30): mutation is a chance per base (`mutation`, 2/512 by default: the same
//! mean as e021's two per child) instead of exactly two per child, so that most children are
//! near-clones and a few carry several changes. Everything else is e021.
//!
//! Arguments: steps, seed, size, patch widths (0: the uniform sun), cell energy, matter per
//! cell at the start, `relief`, `flow`, `rain` (high, flat or soil), `breath`, `shade` (the
//! rate of the canopy law, 2 by default), `spill` (the radius of the fall, 1 by default; 0 is
//! e021's law: saturation, and a held column claims nothing) and `mutation` (the per-base
//! probability; 0 is e021's two per child), `eyes` (the most cells the sensors add to the
//! range, 8 by default; 0 is e022's law), `flesh` (the share of the upkeep fixed in the
//! flesh, 1 by default; 0 is e023's law), `weight` (0, kind, density or 1; 1 by default),
//! `weather` (0, cloud or season; 0 by default) and its amplitude (sigma for the cloud, a for
//! the season; 1 by default), `digest` (0, 1 or 2; 0 by default here, e028's law not kept; 1 the
//! line, 2 the sharp curve), `side` (a number up to 16, or grow; 8 by default), `store`
//! (fat per unit of mass the flesh can hold, 5 by default here; 0: e029's law), `yolk` (the
//! share of the parent's fat a child gets, 0 by default), `breed` (0 or 1, 0 by default) and
//! `winter` (flat or high; flat by default).
//! The log gets `size_mean` (cells per body; `mass` is the weight now), `density_mean` and
//! `density_std`; `agents.csv` gets `size` and `density`, `lineages.csv` `density`. From e024
//! the log has `fat_mean` (fat per body),
//! `fat_stock` (fat in all bodies), `worth` (what a cell of a body yields to its eater, mean
//! over bodies: cell energy plus the cell's share of energy and fat) and `kill_gain` (what
//! eaters gained per cell broken); `agents.csv` gets `fat`. From e022 the log gets `fruit` (fallen per step),
//! `fruit_stock` (lying now), `fruit_eaten` (intake from fruit per step), `clones` (the share
//! of children conceived without a mutation) and `mutations` (mean per child); the per-place
//! log gets `fruit` (fallen there, by the cell of the column) and `fruit_intake`. `trees`,
//! `tree_res` and `tree_eaten` count the standing plant only (a pile of fruit is not a tree).
use std::collections::HashMap;
use std::io::Write;

// World (as e001/e003). Width and height are arguments; 64 is e006.
const RES_CAP: f32 = 8.0; // what a cell can hold; e011's runs (no regrowth lost to it at any width)
const RES_GROWTH: f32 = 0.01; // regrowth per cell of the world per step, spread over the patches
const INIT_POP_PER_CELL: f32 = 400.0 / 4096.0; // e006's 400 on 64x64
// Patchy food: one patch per PATCH_AREA cells, a Gaussian of width sigma, whose center takes a
// random step of one cell every PATCH_DRIFT steps. Peak regrowth is set so that the sum over the
// world equals uniform regrowth: RES_GROWTH * PATCH_AREA / (2 pi sigma^2), 0.10 per step at
// width 8 and 6.5 at width 1.
const PATCH_AREA: usize = 4096;
const PATCH_DRIFT: u64 = 50;
const N_PLACES: usize = 2; // kinds of place a world can have (the length of the sigma list, at most)
const NO_PLACE: u8 = N_PLACES as u8; // a cell beyond every patch
const INIT_ENERGY: f32 = 5.0;
const MUTATIONS_PER_CHILD: usize = 2;
const MAX_AGE: u32 = 3000;
// The weight law (#25): what a block weighs, by kind (empty, hard, muscle, sensor, digestive),
// times the body's density. A body's mass is the sum; e024's law weighed every block 1.
const KIND_MASS: [f32; N_KINDS] = [0.0, 2.0, 1.0, 0.5, 1.0];
// The density a genome expresses: DENSITY_RANGE^(2 sigmoid(s) - 1), from 1/2 to 2.
const DENSITY_RANGE: f32 = 2.0;
// The digestion law (#32): what the wrong food yields at the far end of the axis (the right
// food yields 1; the middle of the axis yields the mean of the two on both).
const DIGEST_FLOOR: f32 = 0.5;
const FLESH: f32 = 1.0; // default share of the upkeep fixed in the flesh (0: e023's law, all of it breathed; e024 ran 1 and 0.7)
const EYES: usize = 8; // default cap on the cells a body's sensors add to its range (0: e022's law, two cells weighted by sense)
const SPILL: usize = 1; // default radius of the fall: fruit lands on the cells within this distance (the ring of 8); 0 is e021's law
const MUTATION: f32 = MUTATIONS_PER_CHILD as f32 / N as f32; // default chance per base per copy (the same mean as two per child)

// Costs and gains, all per block.
const UPKEEP: f32 = 0.002; // per block per step
// Per body per step, besides its blocks: an individual costs the world something whatever its
// size (the world's compute is per agent). Set to the upkeep of 16 blocks; it bounds the
// population at regrowth / UPKEEP_BODY, about 5,000 on 128x128. Without it the first trial
// filled the world with 4-cell bodies (14,000 of them): plant intake is capped by the food in
// one cell whatever the body, so the smallest body was the best grazer.
const UPKEEP_BODY: f32 = 0.032;
const MOVE_COST: f32 = 0.001; // per block of mass moved per sub-cell moved (work = force x distance); nothing moved, nothing paid
const BITE: f32 = 0.02; // plant intake per digestive block per step
const CELL_ENERGY: f32 = 0.02; // energy in the matter of one cell: paid to build it, gained when it is eaten (the default; an argument)
const DECAY: f32 = 0.01; // share of the dead matter lying on a cell that rots into its soil per step (a corpse nobody eats is soil in a few hundred steps)
// The terrain: smooth noise (white noise blurred by a Gaussian of this width, in cells) scaled
// to `relief` from the lowest cell to the highest. At 16 a 128x128 world has a handful of
// basins, as it has four patches.
const RELIEF_GRAIN: f32 = 16.0;
const LEVEL: f32 = 0.125; // the most of a drop that can move in a step (soil that levels does not slosh)
const RELIEF: f32 = 64.0; // default relief, in soil
const FLOW: f32 = 0.1; // default share of a cell's soil that runs downhill per step
// The weather (#24). The cloud: a Gaussian field on a lattice of nodes WEATHER_GRAIN cells
// apart (the terrain's grain), each node an AR(1) process with a correlation time of
// WEATHER_SPAN steps (longer than a body's life, MAX_AGE 3,000, shorter than a run), the
// lattice drifting east at WIND cells per step (a cloud crosses its own width in a span).
// The season: the sun's period in steps.
const WEATHER_GRAIN: usize = 16;
const WEATHER_SPAN: f32 = 3_000.0;
const WIND: f32 = 1.0 / 200.0;
const SEASON: f32 = 20_000.0;
const WEATHER_LOG: u64 = 1_000; // the field's nodes are written every this many steps
const N_BANDS: usize = 3; // height bands under the uniform sun: valley, slope, ridge (thirds of the cells)
const SHADE: f32 = 2.0; // default rate of the canopy law (0: no shading, e020); the pilot put the
                        // threshold where trees outgrow the grazing between 1 (8-12 trees, 0.3% of
                        // the intake) and 2 (200+, 6%): saturation halves the slant, the rate restores it
const TREE: f32 = 1.0; // a cell holding this much standing matter counts as a tree (50 bites; the lawn stands at 0.03-0.05)

/// Where what a body burns goes, and how it comes back. `Soil`: to the soil under the body
/// (e019). `High` and `Flat`: to the air, which rains on every cell at most the sun's worth per
/// step (RES_GROWTH), scaled by the cell's height over the relief (`High`: the rain falls on
/// the mountains) or the same everywhere (`Flat`).
#[derive(Clone, Copy, PartialEq, Debug)]
enum Rain {
    Soil,
    Flat,
    High,
}

impl Rain {
    fn parse(s: &str) -> Rain {
        match s {
            "soil" => Rain::Soil,
            "flat" => Rain::Flat,
            "high" => Rain::High,
            _ => panic!("rain is high, flat or soil"),
        }
    }
    fn name(self) -> &'static str {
        match self {
            Rain::Soil => "soil",
            Rain::Flat => "flat",
            Rain::High => "high",
        }
    }
    /// The most that can rain on each cell per step.
    fn caps(self, height: &[f32], relief: f32) -> Vec<f32> {
        match self {
            Rain::Soil => vec![0.0; height.len()],
            Rain::Flat => vec![RES_GROWTH; height.len()],
            Rain::High => {
                assert!(relief > 0.0, "rain on the mountains needs a relief");
                height.iter().map(|&h| RES_GROWTH * h / relief).collect()
            }
        }
    }
}
const HARDNESS: u8 = 3; // a hard cell resists this much per contiguous hard cell behind the tip; other cells 1
const YOUNG: u32 = 50; // a death by damage before this age counts as a newborn's

// Genome and network (as e002/e004).
const N: usize = 512;
const PROMOTER: [u8; 3] = [0, 1, 0];
const GENE_LEN: usize = 8;
const TAG_LEN: usize = 4;
const T: usize = 40;

// Body (as e004). A body grows on a grid of `side` by `side` cells (#28): 8 by 8 in every
// experiment up to e028 (SIDE), up to SIDE_MAX here. The cells of a body of side s are stored
// row by row at stride s in the first s * s entries of a CELLS array; the rest is empty.
const SIDE: usize = 8; // the grid of e028: the default, and what `grow` grows around
const SIDE_MAX: usize = 16;
const SIDE_MIN: usize = 4;
const CELLS: usize = SIDE_MAX * SIDE_MAX;
// The side a genome expresses under `grow`: SIDE * SIDE_RANGE^(2 sigmoid(s) - 1), rounded, from
// SIDE / 2 to 2 SIDE (the form of the density, #25).
const SIDE_RANGE: f32 = 2.0;
const N_KINDS: usize = 5; // empty, hard, muscle, sensor, digestive
const HARD: usize = 1;
const MUSCLE: usize = 2;
const SENSOR: usize = 3;
const DIGESTIVE: usize = 4;
const N_MORPH: usize = 6;
// Development runs the network once without position (for the policy, the density, the
// digestion axis and the side) and then once per cell of the grid. All of these runs are
// independent; the cells are settled together as one batch.

// Space: a world cell is SUB x SUB body cells (sub-cells). Occupancy is kept per sub-cell; food
// per world cell. A body anchored at sub-cell (x, y) fills the sub-cells (x + c, y + r) of its
// world-frame grid that hold a cell, so it lies over up to 3x3 world cells.
const SUB: usize = 4;
const SUB_CELLS: usize = SUB * SUB;

// Policy: 10 inputs -> 4 actions (stay, forward, turn left, turn right), read from the same
// table (no position input). The inputs are seen from the body: food under it, food and bodies
// ahead, behind, left and right, and energy.
const N_IN: usize = 10;
const N_OUT: usize = 4;
const N_POLICY: usize = N_IN * N_OUT + N_OUT;
const K: usize = N_KINDS + N_POLICY;

// Sides of a body, and the lines that meet a neighbor on that side. In the body frame NORTH is
// the front; a facing is the world direction the front points to.
const NORTH: usize = 0;
const SOUTH: usize = 1;
const EAST: usize = 2;
const WEST: usize = 3;
const DIRS: [usize; 4] = [NORTH, SOUTH, EAST, WEST];

fn opposite(d: usize) -> usize {
    match d {
        NORTH => SOUTH,
        SOUTH => NORTH,
        EAST => WEST,
        _ => EAST,
    }
}

/// The world direction to the left of facing `d`.
fn left_of(d: usize) -> usize {
    match d {
        NORTH => WEST,
        WEST => SOUTH,
        SOUTH => EAST,
        _ => NORTH,
    }
}

/// Where cell i of a body grid of side `s` lands in the world frame when the body faces `f`:
/// the front row becomes the side of the grid that points to `f` (a rotation about the center
/// of the grid).
fn to_world(i: usize, f: usize, s: usize) -> usize {
    let (r, c) = (i / s, i % s);
    let m = s - 1;
    let (r2, c2) = match f {
        NORTH => (r, c),
        SOUTH => (m - r, m - c),
        EAST => (c, m - r),
        _ => (m - c, r),
    };
    r2 * s + c2
}

/// The inverse of `to_world`: the body-grid cell under world-frame cell i.
fn to_body(i: usize, f: usize, s: usize) -> usize {
    let (r2, c2) = (i / s, i % s);
    let m = s - 1;
    let (r, c) = match f {
        NORTH => (r2, c2),
        SOUTH => (m - r2, m - c2),
        EAST => (m - c2, r2),
        _ => (c2, m - r2),
    };
    r * s + c
}

fn rotate(cells: &[u8; CELLS], f: usize, s: usize) -> [u8; CELLS] {
    let mut out = [0u8; CELLS];
    for (i, &c) in cells.iter().enumerate().take(s * s) {
        out[to_world(i, f, s)] = c;
    }
    out
}

/// The cells a grid of side `s` holds (their indices) and their bounding box (r0, r1, c0, c1),
/// inclusive.
fn filled(cells: &[u8; CELLS], s: usize) -> ([u8; CELLS], u16, [u8; 4]) {
    let mut list = [0u8; CELLS];
    let mut n = 0u16;
    let mut bb = [s as u8, 0, s as u8, 0];
    for (i, &c) in cells.iter().enumerate().take(s * s) {
        if c != 0 {
            list[n as usize] = i as u8;
            n += 1;
            let (r, col) = ((i / s) as u8, (i % s) as u8);
            bb = [bb[0].min(r), bb[1].max(r), bb[2].min(col), bb[3].max(col)];
        }
    }
    if n == 0 {
        bb = [0; 4];
    }
    (list, n, bb)
}

/// The grid cell next to `pos` in direction `d`, if it is inside the grid of side `s`.
fn neighbor(pos: usize, d: usize, s: usize) -> Option<usize> {
    let (r, c) = (pos / s, pos % s);
    let (r, c) = match d {
        NORTH => (r.checked_sub(1)?, c),
        SOUTH => (r + 1, c),
        EAST => (r, c + 1),
        _ => (r, c.checked_sub(1)?),
    };
    (r < s && c < s).then_some(r * s + c)
}

/// The hardness of the face of the cell at `pos` that looks against direction `into`: 3 per
/// contiguous hard cell from `pos` inward (in direction `into`), else 1 (e010's tip hardness,
/// for any cell whose face can be touched).
fn face_hardness(cells: &[u8; CELLS], pos: usize, into: usize, s: usize) -> u8 {
    if cells[pos] != HARD as u8 {
        return 1;
    }
    let mut n = 0u8;
    let mut p = Some(pos);
    while let Some(q) = p {
        if cells[q] != HARD as u8 {
            break;
        }
        n += 1;
        p = neighbor(q, into, s);
    }
    HARDNESS * n
}

/// The line (in the frame of the grid) that cell `pos` belongs to when the body moves in
/// direction d: a column for north and south, a row for east and west.
fn line_of(pos: usize, d: usize, s: usize) -> usize {
    match d {
        NORTH | SOUTH => pos % s,
        _ => pos / s,
    }
}

/// A small set of world cells: a body of side SIDE_MAX lies over at most 5x5 (3x3 up to e028).
const UNDER_MAX: usize = (SIDE_MAX / SUB + 1) * (SIDE_MAX / SUB + 1);
#[derive(Clone, Copy)]
struct CellsUnder {
    c: [usize; UNDER_MAX],
    n: usize,
}

impl Default for CellsUnder {
    fn default() -> Self {
        CellsUnder { c: [0; UNDER_MAX], n: 0 }
    }
}

impl CellsUnder {
    fn contains(&self, x: usize) -> bool {
        self.c[..self.n].contains(&x)
    }
    fn add(&mut self, x: usize) {
        if !self.contains(x) && self.n < UNDER_MAX {
            self.c[self.n] = x;
            self.n += 1;
        }
    }
    fn iter(&self) -> impl Iterator<Item = usize> + '_ {
        self.c[..self.n].iter().copied()
    }
}

// Species.
const D: usize = 6; // two agents can mate if their distance is at most D
const MIN_LINEAGE: usize = 5; // a mating-connected group of at least this size is a lineage
const LINEAGE_INTERVAL: u64 = 1_000;
const LINEAGE_CONFIRM: u32 = 5; // detections in a row a group must exist before it is a lineage
const DIST_INTERVAL: u64 = 50_000; // pairwise distance histograms

const LOG_INTERVAL: u64 = 10_000;
const LONG_INTERVAL: u64 = 5_000;
const CLIP_START: u64 = 300_000; // the runs are 500,000 steps here
const CLIP_LEN: u64 = 400;
const AGENT_DUMP_INTERVAL: u64 = 100_000;

struct Rng(u64);

impl Rng {
    fn next_u64(&mut self) -> u64 {
        let mut x = self.0;
        x ^= x >> 12;
        x ^= x << 25;
        x ^= x >> 27;
        self.0 = x;
        x.wrapping_mul(0x2545F4914F6CDD1D)
    }
    fn f32(&mut self) -> f32 {
        (self.next_u64() >> 40) as f32 / (1u64 << 24) as f32
    }
    fn below(&mut self, n: usize) -> usize {
        (self.next_u64() % n as u64) as usize
    }
    /// A unit Gaussian (Box-Muller).
    fn normal(&mut self) -> f32 {
        let u1 = self.f32().max(1e-7);
        let u2 = self.f32();
        (-2.0 * u1.ln()).sqrt() * (2.0 * std::f32::consts::PI * u2).cos()
    }
}

/// The winter (e032): the season's amplitude the same on every cell (flat) or by height (high).
#[derive(Clone, Copy, PartialEq, Debug)]
enum Winter {
    Flat,
    High,
}

impl Winter {
    fn parse(s: &str) -> Self {
        match s {
            "flat" => Winter::Flat,
            "high" => Winter::High,
            _ => panic!("winter is flat or high"),
        }
    }
    fn name(self) -> &'static str {
        match self {
            Winter::Flat => "flat",
            Winter::High => "high",
        }
    }
    /// The amplitude of each cell: `a` everywhere, or `a` times the height over the relief, at most 1.
    fn amplitudes(self, a: f32, height: &[f32], relief: f32) -> Vec<f32> {
        match self {
            Winter::Flat => vec![a; height.len()],
            Winter::High => height.iter().map(|&h| (a * h / relief).min(1.0)).collect(),
        }
    }
}

/// The weather (#24): what form, and its amplitude.
#[derive(Clone, Copy, PartialEq, Debug)]
enum Weather {
    None,
    Cloud,
    Season,
}

impl Weather {
    fn parse(s: &str) -> Weather {
        match s {
            "0" | "none" => Weather::None,
            "cloud" => Weather::Cloud,
            "season" => Weather::Season,
            _ => panic!("weather is 0, cloud or season"),
        }
    }
    fn name(self) -> &'static str {
        match self {
            Weather::None => "none",
            Weather::Cloud => "cloud",
            Weather::Season => "season",
        }
    }
}

/// The cloud: a unit Gaussian field on a lattice of nodes, each an AR(1) process, read at
/// every cell by bilinear interpolation on the torus (scaled back to unit variance, so that
/// the cell's weight is lognormal with mean 1 exactly), the lattice drifting east.
struct Cloud {
    nx: usize,
    ny: usize,
    nodes: Vec<f32>,
    sigma: f32,
    rho: f32,
    rng: Rng,
}

impl Cloud {
    fn new(g: Grid, seed: u64, sigma: f32) -> Cloud {
        let mut rng = Rng(seed.wrapping_mul(0xA0761D6478BD642F) | 1);
        let (nx, ny) = ((g.w / WEATHER_GRAIN).max(1), (g.h / WEATHER_GRAIN).max(1));
        let nodes = (0..nx * ny).map(|_| rng.normal()).collect();
        Cloud { nx, ny, nodes, sigma, rho: (-1.0 / WEATHER_SPAN).exp(), rng }
    }
    /// One step of every node (the stationary variance stays 1).
    fn advance(&mut self) {
        let k = (1.0 - self.rho * self.rho).sqrt();
        for x in self.nodes.iter_mut() {
            *x = self.rho * *x + k * self.rng.normal();
        }
    }
    /// The weight of every cell at `step` (lognormal, mean 1), into `w`.
    fn weights(&self, g: Grid, step: u64, w: &mut [f32]) {
        let drift = (WIND * step as f32) % g.w as f32;
        let gr = WEATHER_GRAIN as f32;
        let bias = 0.5 * self.sigma * self.sigma;
        for y in 0..g.h {
            let v = y as f32 / gr;
            let j0 = v.floor() as usize % self.ny;
            let j1 = (j0 + 1) % self.ny;
            let fy = v - v.floor();
            for x in 0..g.w {
                let u = ((x as f32 - drift).rem_euclid(g.w as f32)) / gr;
                let i0 = u.floor() as usize % self.nx;
                let i1 = (i0 + 1) % self.nx;
                let fx = u - u.floor();
                let n = |i: usize, j: usize| self.nodes[j * self.nx + i];
                // The four weights of the interpolation; the sum of their squares is the
                // variance of the mix, divided out so that every cell is a unit Gaussian.
                let (a, b, c, d) = ((1.0 - fx) * (1.0 - fy), fx * (1.0 - fy), (1.0 - fx) * fy, fx * fy);
                let z = (a * n(i0, j0) + b * n(i1, j0) + c * n(i0, j1) + d * n(i1, j1)) / (a * a + b * b + c * c + d * d).sqrt();
                w[g.idx(x, y)] = (self.sigma * z - bias).exp();
            }
        }
    }
}

#[derive(PartialEq)]
struct Gene {
    tag: [u8; TAG_LEN],
    product: [u8; TAG_LEN],
}

impl Gene {
    /// The 8 symbols packed into 16 bits, for sorted gene lists.
    fn key(&self) -> u16 {
        self.tag.iter().chain(&self.product).fold(0, |acc, &s| acc * 4 + s as u16)
    }
}

fn sorted_keys(genes: &[Gene]) -> Vec<u16> {
    let mut k: Vec<u16> = genes.iter().map(Gene::key).collect();
    k.sort_unstable();
    k
}

/// Distance between two genomes: number of genes in one gene list but not the other
/// (the symmetric difference of the two sorted lists, with multiplicity).
fn gene_distance(a: &[u16], b: &[u16]) -> usize {
    let (mut i, mut j, mut d) = (0, 0, 0);
    while i < a.len() && j < b.len() {
        if a[i] == b[j] {
            i += 1;
            j += 1;
        } else if a[i] < b[j] {
            i += 1;
            d += 1;
        } else {
            j += 1;
            d += 1;
        }
    }
    d + (a.len() - i) + (b.len() - j)
}

fn hamming(a: &[u8], b: &[u8]) -> usize {
    a.iter().zip(b).filter(|(x, y)| x != y).count()
}

struct Laws {
    morphogen: [[u8; TAG_LEN]; N_MORPH],
    table: Vec<[f32; K]>,
    /// What each gene product does to the body's density (#25): one more column of the table,
    /// drawn from its own stream so that the table, the genomes and the bodies are e024's.
    density: Vec<f32>,
    /// What each gene product does to the body's digestion axis (#32): one more column, from
    /// its own stream, so that everything else is e026's.
    digest: Vec<f32>,
    /// What each gene product does to the side of the body's grid (#28): one more column,
    /// from its own stream, so that everything else is e028's.
    side: Vec<f32>,
    /// What each gene product does to the fifth output of the policy, to breed (e031): one
    /// column of N_IN + 1 weights, from its own stream, so that everything else is e030's.
    breed: Vec<[f32; N_IN + 1]>,
    /// Morphogen level per context, for a grid of each side (index: the side; 0 unused): the
    /// side * side cells with position, then the policy run without (level 0).
    morph_level: Vec<[Vec<f32>; N_MORPH]>,
}

impl Laws {
    fn new(rng: &mut Rng, seed: u64) -> Self {
        let mut rng2 = Rng(seed.wrapping_mul(0x9E3779B97F4A7C15).wrapping_add(0x5851F42D4C957F2D) | 1);
        let density = (0..256).map(|_| rng2.f32() * 2.0 - 1.0).collect();
        let mut rng3 = Rng(seed.wrapping_mul(0xD1B54A32D192ED03).wrapping_add(0x9E3779B97F4A7C15) | 1);
        let digest = (0..256).map(|_| rng3.f32() * 2.0 - 1.0).collect();
        let mut rng4 = Rng(seed.wrapping_mul(0xA0761D6478BD642F).wrapping_add(0xE7037ED1A0B428DB) | 1);
        let side = (0..256).map(|_| rng4.f32() * 2.0 - 1.0).collect();
        let mut rng5 = Rng(seed.wrapping_mul(0x8CB92BA72F3D8DD7).wrapping_add(0x2545F4914F6CDD1D) | 1);
        let breed = (0..256).map(|_| std::array::from_fn(|_| rng5.f32() * 2.0 - 1.0)).collect();
        let mut morphogen = [[0u8; TAG_LEN]; N_MORPH];
        for m in morphogen.iter_mut() {
            for s in m.iter_mut() {
                *s = rng.below(4) as u8;
            }
        }
        let table = (0..256)
            .map(|_| {
                let mut row = [0.0; K];
                for v in row.iter_mut() {
                    *v = rng.f32() * 2.0 - 1.0;
                }
                row
            })
            .collect();
        // The gradients span the grid whatever its side (a pattern scales with the body it is
        // written on): side 8 is e028's field, a larger side samples the same field finer.
        let morph_level = (0..=SIDE_MAX)
            .map(|s| {
                let n = s * s;
                let mut levels: [Vec<f32>; N_MORPH] = std::array::from_fn(|_| vec![0.0f32; n + 1]);
                let c = (s as f32 - 1.0) / 2.0;
                let rmax = (2.0 * c * c).sqrt();
                for i in 0..n {
                    let x = (i % s) as f32 / (s as f32 - 1.0);
                    let y = (i / s) as f32 / (s as f32 - 1.0);
                    let dx = (i % s) as f32 - c;
                    let dy = (i / s) as f32 - c;
                    let r = (dx * dx + dy * dy).sqrt() / rmax;
                    for (m, v) in [x, 1.0 - x, y, 1.0 - y, r, 1.0 - r].into_iter().enumerate() {
                        levels[m][i] = 2.0 * v - 1.0;
                    }
                }
                levels
            })
            .collect();
        Laws { morphogen, table, density, digest, side, breed, morph_level }
    }
}

/// The side of the grid a body grows on (#28): every body on one side (8: e028), or the side
/// the genome expresses, from SIDE / 2 to 2 SIDE.
#[derive(Clone, Copy, PartialEq, Debug)]
enum Side {
    Fixed(usize),
    Grow,
}

impl Side {
    fn parse(s: &str) -> Side {
        match s {
            "grow" => Side::Grow,
            _ => {
                let n: usize = s.parse().expect("side is a number or grow");
                assert!((1..=SIDE_MAX).contains(&n), "side is 1 to {SIDE_MAX}");
                Side::Fixed(n)
            }
        }
    }
    fn name(self) -> String {
        match self {
            Side::Fixed(n) => n.to_string(),
            Side::Grow => "grow".to_string(),
        }
    }
}

fn parse_genes(genome: &[u8]) -> Vec<Gene> {
    let mut genes = Vec::new();
    let mut i = 0;
    while i + PROMOTER.len() + GENE_LEN <= genome.len() {
        if genome[i..i + PROMOTER.len()] == PROMOTER {
            let g = &genome[i + PROMOTER.len()..i + PROMOTER.len() + GENE_LEN];
            let mut tag = [0; TAG_LEN];
            let mut product = [0; TAG_LEN];
            tag.copy_from_slice(&g[..TAG_LEN]);
            product.copy_from_slice(&g[TAG_LEN..]);
            genes.push(Gene { tag, product });
        }
        i += 1;
    }
    genes
}

fn pattern_index(p: &[u8; TAG_LEN]) -> usize {
    p.iter().fold(0, |acc, &s| acc * 4 + s as usize)
}

fn bind(product: &[u8; TAG_LEN], tag: &[u8; TAG_LEN]) -> f32 {
    let m = product.iter().zip(tag).filter(|(a, b)| a == b).count();
    if m < 3 {
        return 0.0;
    }
    let sign = if product[0] < 2 { 1.0 } else { -1.0 };
    sign * (m as f32 - 2.0) / 2.0
}

fn bind_morphogen(morphogen: &[u8; TAG_LEN], tag: &[u8; TAG_LEN]) -> f32 {
    let m = morphogen.iter().zip(tag).filter(|(a, b)| a == b).count();
    if m < 2 {
        return 0.0;
    }
    let sign = if morphogen[0] < 2 { 1.0 } else { -1.0 };
    sign * m as f32 / 4.0
}

fn sigmoid(x: f32) -> f32 {
    1.0 / (1.0 + (-x).exp())
}

/// One line of a body seen from one side: how hard the tip is and the force behind it. Hardness 0 means the line is empty on that side: nothing to touch.
#[derive(Clone, Copy, Default)]
struct Tip {
    hardness: u8,
    force: u8,
}

/// The tips of every line on every side of a grid (sides and lines in the frame of the grid:
/// for NORTH and SOUTH the lines are columns from west to east, for EAST and WEST rows from
/// north to south).
fn tips_of(cells: &[u8; CELLS], s: usize) -> [[Tip; SIDE_MAX]; 4] {
    let mut tips = [[Tip::default(); SIDE_MAX]; 4];
    for side in 0..4 {
        for line in 0..s {
            // The cells of this line, from the outside in.
            let at = |k: usize| -> usize {
                match side {
                    NORTH => k * s + line,
                    SOUTH => (s - 1 - k) * s + line,
                    EAST => line * s + (s - 1 - k),
                    _ => line * s + k,
                }
            };
            let mut tip = Tip::default();
            let force = (0..s).filter(|&k| cells[at(k)] == MUSCLE as u8).count() as u8;
            if let Some(k0) = (0..s).find(|&k| cells[at(k)] != 0) {
                let hardness = if cells[at(k0)] == HARD as u8 {
                    HARDNESS * (k0..s).take_while(|&k| cells[at(k)] == HARD as u8).count() as u8
                } else {
                    1
                };
                tip = Tip { hardness, force };
            }
            tips[side][line] = tip;
        }
    }
    tips
}

#[derive(Clone)]
struct Body {
    cells: [u8; CELLS], // row by row at stride `side`, the first side * side entries
    side: u8, // the side of the grid the body grew on (#28)
    size: u16, // cells
    mass: f32, // what the cells weigh (#25): the sum of KIND_MASS by kind (or 1 each), times the density
    density: f32, // what the genome expresses (1 without the law)
    digest: f32, // the digestion axis the genome expresses (#32): 0 a plant gut, 1 a flesh gut
    by_kind: bool, // whether a block weighs by its kind
    kinds: [u16; N_KINDS],
    tips: [[Tip; SIDE_MAX]; 4], // per side, per line (the first `side` of them), in the body frame (NORTH is the front)
    extent: [u8; 2], // cells the body spans along the facing (rows) and across it (columns)
    policy: [f32; N_POLICY],
    breed: [f32; N_IN + 1], // the fifth output of the policy (e031): weights on the inputs and a bias
    n_genes: u16,
}

impl Body {
    fn new(cells: [u8; CELLS], side: usize, policy: [f32; N_POLICY], n_genes: u16, density: f32, by_kind: bool) -> Self {
        let mut b = Body { cells, side: side as u8, size: 0, mass: 0.0, density, digest: 0.5, by_kind, kinds: [0; N_KINDS], tips: [[Tip::default(); SIDE_MAX]; 4], extent: [0; 2], policy, breed: [0.0; N_IN + 1], n_genes };
        b.refresh();
        b
    }
    fn s(&self) -> usize {
        self.side as usize
    }
    /// The tips of one side, the lines the grid has.
    fn tips_on(&self, side: usize) -> &[Tip] {
        &self.tips[side][..self.s()]
    }
    /// What one block of `kind` weighs in this body, and the matter it is made of (times cell_energy).
    fn block_mass(&self, kind: u8) -> f32 {
        if kind == 0 {
            return 0.0;
        }
        self.density * if self.by_kind { KIND_MASS[kind as usize] } else { 1.0 }
    }
    /// Recompute what follows from the cells: size, mass, counts per kind, the tips of every
    /// line on every side, and the extent. Called at birth and whenever a cell breaks.
    fn refresh(&mut self) {
        self.kinds = [0; N_KINDS];
        for &c in &self.cells {
            self.kinds[c as usize] += 1;
        }
        self.size = CELLS as u16 - self.kinds[0];
        self.mass = (1..N_KINDS).map(|k| self.kinds[k] as f32 * self.block_mass(k as u8)).sum();
        self.tips = tips_of(&self.cells, self.s());
        let (_, n, bb) = filled(&self.cells, self.s());
        self.extent = if n == 0 { [0, 0] } else { [bb[1] - bb[0] + 1, bb[3] - bb[2] + 1] };
    }
    /// What the gut digests of a unit of plant matter and of flesh (#32): the line (law 1) or
    /// the sharp curve (law 2) of the axis; without the law (0), the whole of both (e026).
    fn yields(&self, law: u8) -> (f64, f64) {
        let (d, k) = (self.digest as f64, (1.0 - DIGEST_FLOOR) as f64);
        match law {
            0 => (1.0, 1.0),
            1 => (1.0 - k * d, 1.0 - k * (1.0 - d)),
            _ => (1.0 - k * d.sqrt(), 1.0 - k * (1.0 - d).sqrt()),
        }
    }
    /// Muscle over mass: a heavy body is slow (#25: armor and density weigh).
    fn speed(&self) -> f32 {
        if self.mass <= 0.0 { 0.0 } else { self.kinds[MUSCLE] as f32 / self.mass }
    }
    /// e022's sense: the weight of the second cell, sensors / 8.
    fn sense(&self) -> f32 {
        (self.kinds[SENSOR] as f32 / 8.0).min(1.0)
    }
    /// The eye's range (#26): a body sees one cell ahead, and one more cell per sensor block,
    /// up to `eyes` more. A sensor is a material that sees a distance.
    fn range(&self, eyes: usize) -> usize {
        1 + (self.kinds[SENSOR] as usize).min(eyes)
    }
    fn threshold(&self) -> f32 {
        2.0 + 0.1 * self.mass
    }
    /// Measures of shape, for the log only (no rule reads them). Bite: the largest force behind
    /// a hard tip on the front (the only side that pushes). Bite any: the same on any side
    /// (e012's bite). Shell: the mean hardness of the tips that can be touched, on all sides or
    /// on one. Open lines: lines with nothing to touch.
    fn bite(&self) -> u8 {
        self.tips_on(NORTH).iter().filter(|t| t.hardness > 1).map(|t| t.force).max().unwrap_or(0)
    }
    fn bite_any(&self) -> u8 {
        DIRS.iter().flat_map(|&d| self.tips_on(d)).filter(|t| t.hardness > 1).map(|t| t.force).max().unwrap_or(0)
    }
    fn shell_of(tips: &[Tip]) -> f32 {
        let touchable: Vec<u8> = tips.iter().filter(|t| t.hardness > 0).map(|t| t.hardness).collect();
        if touchable.is_empty() { 0.0 } else { touchable.iter().map(|&h| h as f32).sum::<f32>() / touchable.len() as f32 }
    }
    fn shell(&self) -> f32 {
        let all: Vec<Tip> = DIRS.iter().flat_map(|&d| self.tips_on(d)).copied().collect();
        Self::shell_of(&all)
    }
    fn shell_side(&self, side: usize) -> f32 {
        Self::shell_of(self.tips_on(side))
    }
    fn open_lines(&self) -> u8 {
        DIRS.iter().flat_map(|&d| self.tips_on(d)).filter(|t| t.hardness == 0).count() as u8
    }
}

/// Development (e004): the network settles once per cell (with position) and once without
/// position (for the policy). All 65 runs are batched: `level` is gene-major, so the inner
/// loops run over the contexts and vectorize. The order of floating point operations per
/// context is the one of e004, so the bodies are the same.
/// The network settled in `nctx` contexts at once: the morphogen levels per context are
/// `morph[m][c]`. Returns the levels gene-major, level[i * nctx + c]. Every context is its own
/// run (the same floating point order whatever the batch), so the policy run settled alone
/// gives what it gave in the batch of 65.
fn settle(n: usize, w: &[f32], wm: &[f32], morph: &[Vec<f32>; N_MORPH], nctx: usize) -> Vec<f32> {
    let mut level = vec![0.5f32; n * nctx];
    let mut next = vec![0.0f32; n * nctx];
    let mut acc = vec![0.0f32; nctx];
    for _ in 0..T {
        for i in 0..n {
            acc.fill(0.0);
            for j in 0..n {
                let wij = w[i * n + j];
                for (a, &l) in acc.iter_mut().zip(&level[j * nctx..(j + 1) * nctx]) {
                    *a += wij * l;
                }
            }
            for m in 0..N_MORPH {
                let wim = wm[i * N_MORPH + m];
                for (a, &l) in acc.iter_mut().zip(&morph[m][..nctx]) {
                    *a += wim * l;
                }
            }
            for (o, &a) in next[i * nctx..(i + 1) * nctx].iter_mut().zip(&acc) {
                *o = sigmoid(3.0 * a - 1.0);
            }
        }
        std::mem::swap(&mut level, &mut next);
    }
    level
}

fn develop_genes(genes: &[Gene], laws: &Laws, weight: Weight, side_law: Side) -> Body {
    let n = genes.len();
    let mut w = vec![0.0f32; n * n]; // w[i * n + j]: gene j acting on gene i
    let mut wm = vec![0.0f32; n * N_MORPH];
    for i in 0..n {
        for j in 0..n {
            w[i * n + j] = bind(&genes[j].product, &genes[i].tag);
        }
        for m in 0..N_MORPH {
            wm[i * N_MORPH + m] = bind_morphogen(&laws.morphogen[m], &genes[i].tag);
        }
    }
    let rows: Vec<&[f32; K]> = genes.iter().map(|g| &laws.table[pattern_index(&g.product)]).collect();

    // The run without position first (the policy, the density, the digestion axis and the
    // side are read from it), then the cells of the grid whose side it says.
    let no_pos: [Vec<f32>; N_MORPH] = std::array::from_fn(|_| vec![0.0f32]);
    let free = settle(n, &w, &wm, &no_pos, 1);
    let read = |column: &[f32]| -> f32 {
        let mut d = 0.0f32;
        for (i, g) in genes.iter().enumerate() {
            d += column[pattern_index(&g.product)] * free[i];
        }
        d
    };
    let side = match side_law {
        Side::Fixed(s) => s,
        Side::Grow => ((SIDE as f32 * SIDE_RANGE.powf(sigmoid(read(&laws.side)) * 2.0 - 1.0)).round() as usize).clamp(SIDE_MIN, SIDE_MAX),
    };
    let ncell = side * side;
    let level = settle(n, &w, &wm, &laws.morph_level[side], ncell);

    let mut cells = [0u8; CELLS];
    for (c, cell) in cells.iter_mut().enumerate().take(ncell) {
        let mut score = [0.0f32; N_KINDS];
        for (i, row) in rows.iter().enumerate() {
            let lv = level[i * ncell + c];
            for k in 0..N_KINDS {
                score[k] += row[k] * lv;
            }
        }
        let mut best = 0;
        for k in 1..N_KINDS {
            if score[k] > score[best] {
                best = k;
            }
        }
        *cell = best as u8;
    }
    let mut policy = [0.0f32; N_POLICY];
    for (i, row) in rows.iter().enumerate() {
        let lv = free[i];
        for k in 0..N_POLICY {
            policy[k] += row[N_KINDS + k] * lv;
        }
    }
    for p in policy.iter_mut() {
        *p = sigmoid(*p) * 2.0 - 1.0;
    }
    // The density (#25): read like the policy, from the run without position.
    let density = if weight.density { DENSITY_RANGE.powf(sigmoid(read(&laws.density)) * 2.0 - 1.0) } else { 1.0 };
    let mut body = Body::new(cells, side, policy, n as u16, density, weight.kind);
    // The digestion axis (#32): read like the density, a sigmoid of the sum.
    body.digest = sigmoid(read(&laws.digest));
    // The fifth output of the policy (e031): read like the policy, from the run without position.
    for k in 0..=N_IN {
        let mut v = 0.0f32;
        for (i, g) in genes.iter().enumerate() {
            v += laws.breed[pattern_index(&g.product)][k] * free[i];
        }
        body.breed[k] = sigmoid(v) * 2.0 - 1.0;
    }
    body
}

struct Agent {
    id: u64,
    lineage: u32, // 0 = none; otherwise inherited from the mother, corrected at each detection
    x: usize,
    y: usize,
    energy: f64, // the body's ledger is f64 (#31): the fat takes a fixed increment every step, and an f32 rounds it with a bias
    age: u32,
    plant: f32, // lifetime intake from plants
    meat: f32, // lifetime intake from broken cells of other bodies
    fat: f64, // matter fixed in the flesh from the upkeep paid (the flesh law); yielded to the eater or the ground, never spent
    born_size: u16,
    breed_now: bool, // e031: this step's decision was to breed
    born_place: u8, // the place of the cell it was born in (a measure only)
    alive: bool,
    genome: Vec<u8>,
    keys: Vec<u16>, // sorted gene keys, for distances
    gene_ids: Vec<u16>, // gene keys in genome order: the body is a function of this list
    body: Body,
    facing: u8, // the world direction the front of the body points to
    // The body in the world frame: its cells rotated by the facing, the tips per world side,
    // the cells it holds (grid indices, `n_filled` of them) and their bounding box. (x, y) is
    // the sub-cell under the north-west corner of the grid.
    wcells: [u8; CELLS],
    tips: [[Tip; SIDE_MAX]; 4],
    filled: [u8; CELLS],
    n_filled: u16,
    bbox: [u8; 4],
}

impl Agent {
    fn distance(&self, other: &Agent) -> usize {
        gene_distance(&self.keys, &other.keys)
    }

    /// Recompute the world frame from the body and the facing. Called when the body is made,
    /// turns, or loses a cell.
    fn reframe(&mut self) {
        let s = self.body.s();
        self.wcells = rotate(&self.body.cells, self.facing as usize, s);
        self.tips = tips_of(&self.wcells, s);
        let (list, n, bb) = filled(&self.wcells, s);
        self.filled = list;
        self.n_filled = n;
        self.bbox = bb;
    }
    fn cells_held(&self) -> impl Iterator<Item = usize> + '_ {
        self.filled[..self.n_filled as usize].iter().map(|&p| p as usize)
    }
    /// The sub-cell under grid cell `pos`, moved k sub-cells in direction d.
    fn sub_at(&self, g: Grid, pos: usize, d: usize, k: usize) -> (usize, usize) {
        let s = self.body.s();
        g.sstep((self.x + pos % s) % g.sw, (self.y + pos / s) % g.sh, d, k)
    }
    /// The world cells under the body's bounding box, moved k sub-cells in direction d.
    fn under(&self, g: Grid, d: usize, k: usize) -> CellsUnder {
        let mut out = CellsUnder::default();
        if self.n_filled == 0 {
            return out;
        }
        let [r0, r1, c0, c1] = self.bbox;
        let (sx, sy) = self.sub_at(g, r0 as usize * self.body.s() + c0 as usize, d, k);
        let nx = (sx % SUB + (c1 - c0) as usize) / SUB + 1;
        let ny = (sy % SUB + (r1 - r0) as usize) / SUB + 1;
        for j in 0..ny {
            for i in 0..nx {
                out.add(g.idx((sx / SUB + i) % g.w, (sy / SUB + j) % g.h));
            }
        }
        out
    }
    /// The world cell under the middle of the body (its place).
    fn here(&self, g: Grid) -> usize {
        let [r0, r1, c0, c1] = self.bbox;
        let (sx, sy) = self.sub_at(g, (r0 + r1) as usize / 2 * self.body.s() + (c0 + c1) as usize / 2, NORTH, 0);
        g.wcell(sx, sy)
    }
    /// World cells under the body's cells (the footprint), a measure.
    fn foot_n(&self, g: Grid) -> u8 {
        let mut out = CellsUnder::default();
        for p in self.cells_held() {
            let (sx, sy) = self.sub_at(g, p, NORTH, 0);
            out.add(g.wcell(sx, sy));
        }
        out.n as u8
    }
    /// Whether every cell of the body, moved k sub-cells in direction d, lands on a free
    /// sub-cell or on one of its own.
    fn fits(&self, g: Grid, occ: &[u32], me: u32, d: usize, k: usize) -> bool {
        self.cells_held().all(|p| {
            let (sx, sy) = self.sub_at(g, p, d, k);
            let o = occ[g.sidx(sx, sy)];
            o == u32::MAX || o == me
        })
    }

    /// 0 = plants only, 1 = mixed, 2 = meat only, 3 = nothing eaten yet.
    fn diet_class(&self) -> usize {
        let total = self.plant + self.meat;
        if total <= 0.0 {
            3
        } else if self.meat <= 0.0 {
            0
        } else if self.plant <= 0.0 {
            2
        } else {
            1
        }
    }
}

/// The world: w x h cells of food, and sw x sh sub-cells (SUB per cell) of occupancy.
#[derive(Clone, Copy)]
struct Grid {
    w: usize,
    h: usize,
    sw: usize,
    sh: usize,
}

impl Grid {
    fn new(w: usize, h: usize) -> Self {
        Grid { w, h, sw: w * SUB, sh: h * SUB }
    }
    fn idx(&self, x: usize, y: usize) -> usize {
        y * self.w + x
    }
    fn cells(&self) -> usize {
        self.w * self.h
    }
    fn sidx(&self, sx: usize, sy: usize) -> usize {
        sy * self.sw + sx
    }
    /// The world cell a sub-cell lies in.
    fn wcell(&self, sx: usize, sy: usize) -> usize {
        self.idx(sx / SUB, sy / SUB)
    }
    /// Sub-cell (sx, sy) moved k sub-cells in direction d, on the torus.
    fn sstep(&self, sx: usize, sy: usize, d: usize, k: usize) -> (usize, usize) {
        match d {
            NORTH => (sx, (sy + self.sh - k % self.sh) % self.sh),
            SOUTH => (sx, (sy + k) % self.sh),
            EAST => ((sx + k) % self.sw, sy),
            _ => ((sx + self.sw - k % self.sw) % self.sw, sy),
        }
    }
}

/// Occupancy: the body holding each sub-cell (u32::MAX: none), and per world cell the number
/// of sub-cells held (the crowd there, what a body sees ahead).
struct Occ {
    sub: Vec<u32>,
    crowd: Vec<u16>,
}

impl Occ {
    /// Write the body's index into its sub-cells and count them in the crowd.
    fn claim(&mut self, g: Grid, a: &Agent, v: u32) {
        for p in a.cells_held() {
            let (sx, sy) = a.sub_at(g, p, NORTH, 0);
            self.sub[g.sidx(sx, sy)] = v;
            self.crowd[g.wcell(sx, sy)] += 1;
        }
    }
    fn release(&mut self, g: Grid, a: &Agent) {
        for p in a.cells_held() {
            let (sx, sy) = a.sub_at(g, p, NORTH, 0);
            self.sub[g.sidx(sx, sy)] = u32::MAX;
            self.crowd[g.wcell(sx, sy)] -= 1;
        }
    }
    fn release_one(&mut self, g: Grid, a: &Agent, pos: usize) {
        let (sx, sy) = a.sub_at(g, pos, NORTH, 0);
        self.sub[g.sidx(sx, sy)] = u32::MAX;
        self.crowd[g.wcell(sx, sy)] -= 1;
    }
    /// Rewrite the index of a body whose place in the list changed.
    fn relabel(&mut self, g: Grid, a: &Agent, v: u32) {
        for p in a.cells_held() {
            let (sx, sy) = a.sub_at(g, p, NORTH, 0);
            self.sub[g.sidx(sx, sy)] = v;
        }
    }
}

/// Counters of the contact physics, summed over a log interval.
#[derive(Default)]
struct Counters {
    contacts: u64, // pairs whose lines touched
    cells_broken: u64,
    kills: u64, // deaths by damage
    prey_age: u64,
    kills_young: u64,
    meat_intake: f32,
    meat_at: [f32; N_PLACES + 1],
    kill_gain: f32, // what eaters gained from the cells they broke (matter, energy and fat), after digestion
    dung: f64, // matter taken and not digested (#32), to the soil, summed over the interval
    dead: f64, // matter laid on the ground by the dead (cells and energy), summed over the interval
    dead_at: [f64; N_PLACES + 1],
}

/// Matter on the ground: what a cell holds as food (`res`), how much of that is dead matter
/// (`carrion`, at most `res`), and the soil of the cell (`soil`), which a plant grows out of.
/// The ground is an f64 (#31): it takes and gives 0.001-sized amounts every step, and as an
/// f32 it drifted by up to 1.8% of the world's matter over a million steps (the soil, e019)
/// and by 0.2-1.8% under the corpses of fat bodies (`res`, e024); an f64 holds it to 0.0003%.
/// The bodies stay f32: their energy is transient and returns to the ground when they die.
struct Food {
    res: Vec<f64>,
    carrion: Vec<f64>,
    fruit: Vec<f64>, // plant matter lying on the cell, fallen from a column around it (at most `res`, with `carrion`)
    soil: Vec<f64>,
}

/// What one cell did in one step of regrowth.
#[derive(Default, PartialEq, Debug)]
struct Regrown {
    added: f32, // moved from the soil to the plant
    fruit: f32, // moved from the soil to the fruit that falls around the cell (the growth past the cap, or under a body)
    shaded: f32, // sun lost because a body stands on the cell
    wasted: f32, // sun lost because the plant is at the cap
    barren: f32, // sun lost because the soil has nothing left
    rot: f32, // dead matter moved to the soil
}

impl Food {
    fn new(res: Vec<f64>, carrion: Vec<f64>, soil: Vec<f64>) -> Self {
        let fruit = vec![0.0; res.len()];
        Food { res, carrion, fruit, soil }
    }
    /// One step of cell `c` under its own sun `own` (what is left after the canopy) and the
    /// light its column took from around it, `crown`: dead matter and fruit rot into the
    /// soil, then the plant grows out of the soil by at most the light, not above the cap. A
    /// body standing on the cell shades its own sun and stops its growth (e016); the crown's
    /// light is above the body. With `spill`, the growth the light and the soil would give
    /// past the cap, or under a body, is fruit (returned; the caller lets it fall); without
    /// it, that light is wasted (e021).
    fn regrow(&mut self, c: usize, own: f32, crown: f32, held: bool, cap: f32, spill: bool) -> Regrown {
        let rot = (self.carrion[c] + self.fruit[c]) * DECAY as f64;
        self.carrion[c] -= self.carrion[c] * DECAY as f64;
        self.fruit[c] -= self.fruit[c] * DECAY as f64;
        self.res[c] -= rot;
        self.soil[c] += rot;
        let lit = if held { 0.0 } else { own };
        let sun = lit + crown;
        let room = if held { 0.0 } else { (cap as f64 - self.res[c]).max(0.0) as f32 };
        let growth = sun.min(self.soil[c] as f32);
        let added = growth.min(room);
        let (fruit, wasted) = if spill { (growth - added, 0.0) } else { (0.0, sun - sun.min(room)) };
        let barren = sun - added - fruit - wasted;
        self.soil[c] -= (added + fruit) as f64;
        self.res[c] += added as f64;
        Regrown { added, fruit, shaded: own - lit, wasted, barren, rot: rot as f32 }
    }
    /// What a body spends falls to the soil of the cell under it (Rain::Soil).
    fn spend(&mut self, c: usize, e: f64) {
        self.soil[c] += e;
    }
    /// The canopy: a taller column shades a shorter one, as far as it is tall, and takes only
    /// what it can use. A column of standing matter (`res`) claims, from every cell within
    /// Chebyshev distance `d` of it, a share of that cell's sun equal to `rate` times (the
    /// difference of the columns, less the distance walked, `d - 1`) over the cap - the
    /// slanting sun - times the column's room (`cap - res`) over the cap - saturation: a full
    /// crown intercepts nothing, and a tree bitten deep pulls hardest, so a column never
    /// gathers much more light than it can grow by. Equal columns shade each other not at all;
    /// the reach of a shadow is at most the cap in cells; a column under a body claims nothing
    /// (the plant neither grows nor gathers there, e016), though its own sun, already dark, can
    /// be claimed. Where the claims on a cell add up to more than one, they share its sun in
    /// proportion. All columns shade at once from the state at the start of the step; the sun
    /// is moved, never made or lost. `claims` is scratch. Returns the sun moved.
    ///
    /// With `spill` (e022) the saturation is dropped - a column claims at `rate` whatever its
    /// height, a full crown as hard as a bitten one - and a column under a body claims too:
    /// what it takes is the crown's light, above the body, and falls as fruit around it.
    ///
    /// `light` gets every cell's own sun after the claims on it; `crown` what each column took.
    fn shade(&self, g: Grid, grow: &[f32], rate: f32, cap: f32, crowd: &[u16], spill: bool, claims: &mut [f32], light: &mut [f32], crown: &mut [f32]) -> f32 {
        claims.iter_mut().for_each(|c| *c = 0.0);
        crown.iter_mut().for_each(|c| *c = 0.0);
        let hunger_of = |t: usize| -> f32 {
            let hc = self.res[t] as f32;
            if hc <= 0.0 || (!spill && crowd[t] > 0) {
                0.0
            } else if spill {
                rate
            } else {
                rate * (cap - hc).max(0.0) / cap
            }
        };
        let reach_max = cap.ceil() as isize;
        // Every cell on the Chebyshev ring at distance d of (x, y), on the torus.
        let ring = |x: usize, y: usize, d: isize, mut f: Box<dyn FnMut(usize) + '_>| {
            for dx in -d..=d {
                let xx = (x as isize + dx).rem_euclid(g.w as isize) as usize;
                for dy in [-d, d] {
                    f(g.idx(xx, (y as isize + dy).rem_euclid(g.h as isize) as usize));
                }
            }
            for dy in (1 - d)..d {
                let yy = (y as isize + dy).rem_euclid(g.h as isize) as usize;
                for dx in [-d, d] {
                    f(g.idx((x as isize + dx).rem_euclid(g.w as isize) as usize, yy));
                }
            }
        };
        // First every column lays its claims, then the sun is dealt out in proportion.
        for y in 0..g.h {
            for x in 0..g.w {
                let t = g.idx(x, y);
                let hc = self.res[t] as f32;
                let hunger = hunger_of(t);
                if hunger <= 0.0 {
                    continue;
                }
                for d in 1..=(hc.ceil() as isize).min(reach_max) {
                    ring(x, y, d, Box::new(|n: usize| {
                        let s = hunger * (hc - self.res[n] as f32 - (d - 1) as f32) / cap;
                        if s > 0.0 {
                            claims[n] += s;
                        }
                    }));
                }
            }
        }
        light.copy_from_slice(grow);
        let mut moved = 0.0f64;
        for y in 0..g.h {
            for x in 0..g.w {
                let t = g.idx(x, y);
                let hc = self.res[t] as f32;
                let hunger = hunger_of(t);
                if hunger <= 0.0 {
                    continue;
                }
                let mut gained = 0.0f32;
                for d in 1..=(hc.ceil() as isize).min(reach_max) {
                    ring(x, y, d, Box::new(|n: usize| {
                        let s = hunger * (hc - self.res[n] as f32 - (d - 1) as f32) / cap;
                        if s > 0.0 && grow[n] > 0.0 {
                            let give = grow[n] * s / claims[n].max(1.0);
                            light[n] -= give;
                            gained += give;
                            moved += give as f64;
                        }
                    }));
                }
                crown[t] = gained;
            }
        }
        moved as f32
    }
    /// The fall: the fruit made at each cell (`out`) lands in equal shares on the cells within
    /// `radius` of it (Chebyshev, on the torus, not the cell itself: the ring of 8 at radius 1),
    /// as plant matter lying on the ground. Returns the fruit fallen.
    fn spill(&mut self, g: Grid, out: &[f32], radius: usize) -> f32 {
        let r = radius as isize;
        let n = ((2 * radius + 1) * (2 * radius + 1) - 1) as f32;
        let mut fell = 0.0f64;
        for y in 0..g.h {
            for x in 0..g.w {
                let f = out[g.idx(x, y)];
                if f <= 0.0 {
                    continue;
                }
                let each = f / n;
                for dy in -r..=r {
                    let yy = (y as isize + dy).rem_euclid(g.h as isize) as usize;
                    for dx in -r..=r {
                        if dx == 0 && dy == 0 {
                            continue;
                        }
                        let c = g.idx((x as isize + dx).rem_euclid(g.w as isize) as usize, yy);
                        self.res[c] += each as f64;
                        self.fruit[c] += each as f64;
                    }
                }
                fell += f as f64;
            }
        }
        fell as f32
    }
    /// The air rains on the ground: every cell gets its cap, or the same share of it when the
    /// air holds less than the caps add up to (`total`). Rain lands in the soil. Returns what
    /// fell on each cell, summed by place into `at`, and the total.
    fn rain(&mut self, air: &mut f64, caps: &[f32], total: f64, place: &[u8], at: &mut [f64]) -> f64 {
        if total <= 0.0 || *air <= 0.0 {
            return 0.0;
        }
        let scale = (*air / total).min(1.0);
        let mut fell = 0.0f64;
        for (c, &cap) in caps.iter().enumerate() {
            let r = cap as f64 * scale;
            if r > 0.0 {
                self.soil[c] += r;
                at[place[c] as usize] += r;
                fell += r;
            }
        }
        *air = (*air - fell).max(0.0);
        fell
    }
    /// Soil runs downhill. The surface of a cell is its height plus its soil; a cell gives
    /// `rate` of its soil to the four neighbors whose surface is lower, split by the drop to
    /// each, and never more than LEVEL of a drop (so that pooled soil levels out and does not
    /// slosh). All cells move at once from the surfaces at the start of the step; `delta` is
    /// scratch. Returns the soil moved.
    fn flow(&mut self, g: Grid, height: &[f32], rate: f32, delta: &mut [f64]) -> f32 {
        delta.iter_mut().for_each(|d| *d = 0.0);
        let mut moved = 0.0f64;
        for y in 0..g.h {
            for x in 0..g.w {
                let c = g.idx(x, y);
                let s = self.soil[c];
                if s <= 0.0 {
                    continue;
                }
                let h = height[c] as f64 + s;
                let nb = [g.idx(x, (y + g.h - 1) % g.h), g.idx(x, (y + 1) % g.h), g.idx((x + 1) % g.w, y), g.idx((x + g.w - 1) % g.w, y)];
                let mut drop = [0.0f64; 4];
                let mut total = 0.0f64;
                for (k, &n) in nb.iter().enumerate() {
                    let d = h - (height[n] as f64 + self.soil[n]);
                    if d > 0.0 {
                        drop[k] = d;
                        total += d;
                    }
                }
                if total <= 0.0 {
                    continue;
                }
                for (k, &n) in nb.iter().enumerate() {
                    if drop[k] > 0.0 {
                        let give = (rate as f64 * s * drop[k] / total).min(drop[k] * LEVEL as f64);
                        delta[c] -= give;
                        delta[n] += give;
                        moved += give;
                    }
                }
            }
        }
        for (s, d) in self.soil.iter_mut().zip(delta.iter()) {
            *s = (*s + d).max(0.0);
        }
        moved as f32
    }
    /// Dead matter `e` lies on world cell `c`, in full (the cap bounds what a plant grows to).
    fn lay(&mut self, c: usize, e: f64, place: &[u8], cc: &mut Counters) {
        if e <= 0.0 {
            return;
        }
        self.res[c] += e;
        self.carrion[c] += e;
        cc.dead += e;
        cc.dead_at[place[c] as usize] += e;
    }
    /// A gut takes `e` from cell `c`: returns (plant, dead matter, fruit) taken, in the cell's
    /// proportions.
    fn take(&mut self, c: usize, e: f64) -> (f64, f64, f64) {
        let r = self.res[c];
        let (dead, fruit) = if r > 0.0 { (e * (self.carrion[c] / r).min(1.0), e * (self.fruit[c] / r).min(1.0)) } else { (0.0, 0.0) };
        self.res[c] -= e;
        self.carrion[c] = (self.carrion[c] - dead).max(0.0);
        self.fruit[c] = (self.fruit[c] - fruit).max(0.0);
        ((e - dead - fruit).max(0.0), dead, fruit)
    }
}

/// The weight law's switches (#25): `kind`, a block weighs KIND_MASS by its kind; `density`,
/// the genome expresses a density that scales every block of the body. Neither is e024.
#[derive(Clone, Copy, PartialEq, Debug)]
struct Weight {
    kind: bool,
    density: bool,
}

impl Weight {
    fn parse(s: &str) -> Self {
        match s {
            "0" => Weight { kind: false, density: false },
            "kind" => Weight { kind: true, density: false },
            "density" => Weight { kind: false, density: true },
            "1" => Weight { kind: true, density: true },
            _ => panic!("weight is 0, kind, density or 1"),
        }
    }
}

/// A dead body lies where it is: each cell is `cell_energy` of matter plus its share of the
/// energy and the fat the body held, on the world cell under it; a body with no cells leaves
/// its energy and fat on the cell under its anchor. Called after the body's sub-cells are released.
fn lay_body(a: &Agent, g: Grid, food: &mut Food, place: &[u8], cell_energy: f32, cc: &mut Counters) {
    let energy = a.energy.max(0.0) + a.fat;
    if a.n_filled == 0 {
        food.lay(g.wcell(a.x, a.y), energy, place, cc);
        return;
    }
    let share = energy / a.n_filled as f64;
    for p in a.cells_held() {
        let (sx, sy) = a.sub_at(g, p, NORTH, 0);
        food.lay(g.wcell(sx, sy), (cell_energy * a.body.block_mass(a.wcells[p])) as f64 + share, place, cc);
    }
}

/// Body i moves one sub-cell in direction d. Every cell of i whose next sub-cell is held by
/// another body j meets the cell of j there, face to face, as e010's push into a shared cell:
/// the softer face breaks if the muscle of i in that line exceeds its hardness (the hardness of
/// a face is 3 per contiguous hard cell behind it, else 1). A broken cell is gone and its
/// matter and share of energy and fat go to the other if it can digest. Returns, per body pressed, the
/// force against it: the muscle in the lines of i that press on it.
fn push(agents: &mut [Agent], i: usize, d: usize, g: Grid, occ: &mut Occ, place: &[u8], food: &mut Food, cell_energy: f32, digest_law: u8, c: &mut Counters) -> Vec<(usize, u8)> {
    let opp = opposite(d);
    let mut pressed: Vec<(usize, u8)> = Vec::new(); // (body in the way, force against it)
    let mut breaks: Vec<(usize, u8, usize)> = Vec::new(); // (victim, world-frame cell, eater)
    for p in agents[i].cells_held() {
        let (sx, sy) = agents[i].sub_at(g, p, d, 1);
        let j = occ.sub[g.sidx(sx, sy)];
        if j == u32::MAX || j as usize == i {
            continue;
        }
        let j = j as usize;
        // The cell of j under (sx, sy): its grid index in j's frame.
        let b = &agents[j];
        let (r, col) = ((sy + g.sh - b.y) % g.sh, (sx + g.sw - b.x) % g.sw);
        debug_assert!(r < b.body.s() && col < b.body.s());
        let q = r * b.body.s() + col;
        // A face's hardness is the material's times the body's density (#25): light armor is weak armor.
        let ha = face_hardness(&agents[i].wcells, p, opp, agents[i].body.s()) as f32 * agents[i].body.density;
        let hb = face_hardness(&b.wcells, q, d, b.body.s()) as f32 * b.body.density;
        let force = agents[i].tips[d][line_of(p, d, agents[i].body.s())].force;
        match pressed.iter_mut().find(|e| e.0 == j) {
            Some(e) => e.1 = e.1.saturating_add(force),
            None => pressed.push((j, force)),
        }
        if hb < ha && force as f32 > hb {
            breaks.push((j, q as u8, i));
        } else if ha < hb && force as f32 > ha {
            breaks.push((i, p as u8, j));
        }
    }
    c.contacts += pressed.len() as u64;
    for (victim, pos, eater) in breaks {
        let v = &mut agents[victim];
        if v.wcells[pos as usize] == 0 {
            continue;
        }
        occ.release_one(g, v, pos as usize);
        let (sx, sy) = v.sub_at(g, pos as usize, NORTH, 0);
        let under = g.wcell(sx, sy);
        let bpos = to_body(pos as usize, v.facing as usize, v.body.s());
        let share = v.energy.max(0.0) / v.body.size as f64;
        v.energy -= share;
        let fat = v.fat / v.body.size as f64;
        v.fat -= fat;
        let matter = (cell_energy * v.body.block_mass(v.body.cells[bpos])) as f64; // what the block is made of
        v.body.cells[bpos] = 0;
        v.body.refresh();
        v.reframe();
        c.cells_broken += 1;
        if v.body.size == 0 && v.alive {
            v.alive = false;
            c.kills += 1;
            c.prey_age += v.age as u64;
            if v.age < YOUNG {
                c.kills_young += 1;
            }
        }
        let e = &mut agents[eater];
        if e.body.kinds[DIGESTIVE] > 0 {
            // The digestion law (#32): the gut digests its flesh yield of the cell; the rest
            // is dung, to the soil under the eater (nothing without the law).
            let taken = share + fat + matter;
            let dung = taken * (1.0 - e.body.yields(digest_law).1);
            let gain = taken - dung;
            food.spend(e.here(g), dung);
            c.dung += dung;
            e.energy += gain;
            e.meat += gain as f32;
            c.meat_intake += gain as f32;
            c.kill_gain += gain as f32;
            c.meat_at[place[e.here(g)] as usize] += gain as f32;
        } else {
            food.lay(under, share + fat + matter, place, c);
        }
    }
    pressed
}

/// The terrain: a height per cell and, under the uniform sun, the band of each cell (the third
/// of the cells it falls in by height: 0 valley, 1 slope, 2 ridge). White noise from the seed's
/// own stream, blurred by a Gaussian of RELIEF_GRAIN on the torus, scaled to [0, relief].
struct Terrain {
    height: Vec<f32>,
    band: Vec<u8>,
}

impl Terrain {
    fn new(g: Grid, seed: u64, relief: f32) -> Self {
        let mut rng = Rng(seed.wrapping_mul(0x94D049BB133111EB) | 1);
        let noise: Vec<f32> = (0..g.cells()).map(|_| rng.f32()).collect();
        let r = (3.0 * RELIEF_GRAIN).ceil() as isize;
        let kernel: Vec<f32> = (-r..=r).map(|k| (-(k * k) as f32 / (2.0 * RELIEF_GRAIN * RELIEF_GRAIN)).exp()).collect();
        // Separable blur: along x, then along y.
        let mut tmp = vec![0.0f32; g.cells()];
        for y in 0..g.h {
            for x in 0..g.w {
                let mut acc = 0.0;
                for (i, k) in kernel.iter().enumerate() {
                    let xx = (x as isize + i as isize - r).rem_euclid(g.w as isize) as usize;
                    acc += k * noise[g.idx(xx, y)];
                }
                tmp[g.idx(x, y)] = acc;
            }
        }
        let mut height = vec![0.0f32; g.cells()];
        for y in 0..g.h {
            for x in 0..g.w {
                let mut acc = 0.0;
                for (i, k) in kernel.iter().enumerate() {
                    let yy = (y as isize + i as isize - r).rem_euclid(g.h as isize) as usize;
                    acc += k * tmp[g.idx(x, yy)];
                }
                height[g.idx(x, y)] = acc;
            }
        }
        let lo = height.iter().copied().fold(f32::INFINITY, f32::min);
        let hi = height.iter().copied().fold(f32::NEG_INFINITY, f32::max);
        for h in height.iter_mut() {
            *h = if hi > lo { (*h - lo) / (hi - lo) * relief } else { 0.0 };
        }
        // The mean height is normalized to half the relief (the peaks may stand above it), so
        // that the rain caps of every seed add up to the same income: in e020 the seed's mean
        // height (0.44-0.56 of the relief) set what the world eats. Geography, not a law.
        let mean = height.iter().sum::<f32>() / height.len().max(1) as f32;
        if mean > 0.0 {
            let s = 0.5 * relief / mean;
            height.iter_mut().for_each(|h| *h *= s);
        }
        // Bands: thirds of the cells by height (by rank, so a flat world is split too).
        let mut order: Vec<usize> = (0..g.cells()).collect();
        order.sort_by(|&a, &b| height[a].partial_cmp(&height[b]).unwrap().then(a.cmp(&b)));
        let mut band = vec![0u8; g.cells()];
        for (rank, &c) in order.iter().enumerate() {
            band[c] = (rank * N_BANDS / g.cells()) as u8;
        }
        Terrain { height, band }
    }
}

/// Food patches: centers on the torus, the width of each (patch k has sigmas[k % sigmas.len()]),
/// the regrowth field they make, and the place of each cell: the kind (index in the sigma list)
/// of the patch that gives the cell the most regrowth, NO_PLACE beyond every patch. Recomputed
/// when the patches move.
struct Patches {
    centers: Vec<(usize, usize)>,
    sigmas: Vec<f32>,
    grow: Vec<f32>,
    place: Vec<u8>,
    bands: Vec<u8>, // the place of each cell under the uniform sun: its height band
    rng: Rng, // own stream, as e007-e011
}

impl Patches {
    fn new(g: Grid, seed: u64, sigmas: Vec<f32>, bands: Vec<u8>) -> Self {
        let mut rng = Rng(seed.wrapping_mul(0xD1B54A32D192ED03) | 1);
        let n = (g.cells() / PATCH_AREA).max(1);
        let centers = (0..n).map(|_| (rng.below(g.w), rng.below(g.h))).collect();
        let mut p = Patches { centers, sigmas, grow: vec![0.0; g.cells()], place: vec![NO_PLACE; g.cells()], bands, rng };
        p.field(g);
        p
    }
    fn uniform(&self) -> bool {
        self.sigmas[0] == 0.0
    }
    fn sigma_of(&self, k: usize) -> f32 {
        self.sigmas[k % self.sigmas.len()]
    }
    fn field(&mut self, g: Grid) {
        self.grow.iter_mut().for_each(|v| *v = 0.0);
        self.place.iter_mut().for_each(|v| *v = NO_PLACE);
        // A width of 0: the sun is uniform, RES_GROWTH on every cell, and the place of a cell
        // is its height band.
        if self.uniform() {
            self.grow.iter_mut().for_each(|v| *v = RES_GROWTH);
            self.place.copy_from_slice(&self.bands);
            return;
        }
        let mut best = vec![0.0f32; g.cells()]; // the largest single contribution to each cell
        for (k, &(cx, cy)) in self.centers.iter().enumerate() {
            let sigma = self.sigma_of(k);
            let kind = (k % self.sigmas.len()) as u8;
            let peak = RES_GROWTH * PATCH_AREA as f32 / (2.0 * std::f32::consts::PI * sigma * sigma);
            let r = (3.0 * sigma).ceil() as isize; // beyond 3 sigma the Gaussian is below 1.2% of the peak
            for dy in -r..=r {
                for dx in -r..=r {
                    let x = (cx as isize + dx).rem_euclid(g.w as isize) as usize;
                    let y = (cy as isize + dy).rem_euclid(g.h as isize) as usize;
                    let d2 = (dx * dx + dy * dy) as f32;
                    let c = g.idx(x, y);
                    let v = peak * (-d2 / (2.0 * sigma * sigma)).exp();
                    self.grow[c] += v;
                    if v > best[c] {
                        best[c] = v;
                        self.place[c] = kind;
                    }
                }
            }
        }
    }
    fn drift(&mut self, g: Grid) {
        for c in self.centers.iter_mut() {
            match self.rng.below(4) {
                0 => c.1 = (c.1 + g.h - 1) % g.h,
                1 => c.1 = (c.1 + 1) % g.h,
                2 => c.0 = (c.0 + 1) % g.w,
                _ => c.0 = (c.0 + g.w - 1) % g.w,
            }
        }
        self.field(g);
    }
}

fn act(policy: &[f32; N_POLICY], input: &[f32; N_IN]) -> usize {
    act_value(policy, input).0
}

fn act_value(policy: &[f32; N_POLICY], input: &[f32; N_IN]) -> (usize, f32) {
    let mut best = 0;
    let mut best_v = f32::NEG_INFINITY;
    for o in 0..N_OUT {
        let mut v = policy[N_IN * N_OUT + o];
        for i in 0..N_IN {
            v += policy[o * N_IN + i] * input[i];
        }
        if v > best_v {
            best_v = v;
            best = o;
        }
    }
    (best, best_v)
}

/// The cells of a body of side `s`, row by row (s * s characters).
fn cells_str(cells: &[u8; CELLS], s: usize) -> String {
    cells.iter().take(s * s).map(|&k| (b'0' + k) as char).collect()
}

struct Snapshots {
    long: std::io::BufWriter<std::fs::File>,
    clip: std::io::BufWriter<std::fs::File>,
    bodies: std::io::BufWriter<std::fs::File>,
    ids: HashMap<(u8, [u8; CELLS]), u32>,
}

impl Snapshots {
    /// Food is written on a square-root scale of the cap (a wide patch holds 0.02-0.1 per cell,
    /// a narrow one up to 8; a linear scale showed only the narrow ones). The patches are written
    /// as center and width so that the viewer can draw each place.
    /// The soil (long frames only) is written on a log scale, 4 ln(1 + soil), 15 at most (a
    /// cell under a crowd can hold many times the cap).
    fn write_frame(&mut self, clip: bool, step: u64, food: &Food, patches: &Patches, agents: &[Agent]) {
        let f = if clip { &mut self.clip } else { &mut self.long };
        write!(f, "{{\"step\":{step},\"food\":[").unwrap();
        for (i, r) in food.res.iter().enumerate() {
            if i > 0 {
                f.write_all(b",").unwrap();
            }
            write!(f, "{}", ((*r as f32 / RES_CAP).min(1.0).sqrt() * 15.0).round() as u8).unwrap();
        }
        if !clip {
            write!(f, "],\"soil\":[").unwrap();
            for (i, s) in food.soil.iter().enumerate() {
                if i > 0 {
                    f.write_all(b",").unwrap();
                }
                write!(f, "{}", ((1.0 + *s as f32).ln() * 4.0).round().min(15.0) as u8).unwrap();
            }
        }
        write!(f, "],\"patches\":[").unwrap();
        for (k, &(x, y)) in patches.centers.iter().enumerate() {
            if k > 0 {
                f.write_all(b",").unwrap();
            }
            write!(f, "[{x},{y},{}]", patches.sigma_of(k)).unwrap();
        }
        write!(f, "],\"agents\":[").unwrap();
        let mut first = true;
        for a in agents.iter().filter(|a| a.alive) {
            if !first {
                f.write_all(b",").unwrap();
            }
            first = false;
            let next_id = self.ids.len() as u32;
            let id = *self.ids.entry((a.body.side, a.body.cells)).or_insert_with(|| {
                writeln!(self.bodies, "{{\"id\":{next_id},\"side\":{},\"cells\":\"{}\"}}", a.body.side, cells_str(&a.body.cells, a.body.s())).unwrap();
                next_id
            });
            write!(f, "[{},{},{id},{},{},{}]", a.x, a.y, a.diet_class(), a.lineage, a.facing).unwrap();
        }
        writeln!(f, "]}}").unwrap();
    }
}

fn mean_std(vals: impl Iterator<Item = f32> + Clone) -> (f32, f32) {
    let n = vals.clone().count().max(1) as f32;
    let mean = vals.clone().sum::<f32>() / n;
    let var = vals.map(|v| (v - mean) * (v - mean)).sum::<f32>() / n;
    (mean, var.sqrt())
}

fn main() {
    let args: Vec<String> = std::env::args().collect();
    let steps: u64 = args.get(1).and_then(|s| s.parse().ok()).unwrap_or(1_000_000);
    let seed: u64 = args.get(2).and_then(|s| s.parse().ok()).unwrap_or(1);
    let size: usize = args.get(3).and_then(|s| s.parse().ok()).unwrap_or(128);
    // Patch widths, a comma-separated list: patch k has the k-th width, cycling. "8,1" is one
    // world with both kinds of place; "8" is e010's world, "1" is e011's width 1.
    // A width of 0 (alone) makes the sun uniform.
    let sigmas: Vec<f32> = args.get(4).map(String::as_str).unwrap_or("8,1").split(',').map(|s| s.parse().expect("patch width")).collect();
    assert!(!sigmas.is_empty() && sigmas.len() <= N_PLACES, "one or two patch widths");
    assert!(sigmas[0] > 0.0 || sigmas.len() == 1, "a uniform sun is one place");
    // What a cell is made of: paid to build it, food when the body dies (0.02 by default).
    let cell_energy: f32 = args.get(5).and_then(|s| s.parse().ok()).unwrap_or(CELL_ENERGY);
    // Matter per cell at the start: plants up to the cap, the rest soil (the cap by default:
    // e017's start).
    let matter0: f32 = args.get(6).and_then(|s| s.parse().ok()).unwrap_or(RES_CAP);
    // The terrain's relief (lowest cell to highest, in soil; 0: flat) and the share of a
    // cell's soil that runs downhill per step (0: e018, nothing flows).
    let relief: f32 = args.get(7).and_then(|s| s.parse().ok()).unwrap_or(RELIEF);
    let flow_rate: f32 = args.get(8).and_then(|s| s.parse().ok()).unwrap_or(FLOW);
    assert!((0.0..=1.0).contains(&flow_rate), "flow is a share, 0 to 1");
    // Where what a body burns goes: to the air, raining back on the mountains (high) or on
    // every cell alike (flat), or to the soil under the body (soil: e019).
    let rain = Rain::parse(args.get(9).map(String::as_str).unwrap_or("high"));
    // The share of what a body burns that goes to the air; the rest falls to the soil under the
    // body as in e019 (1 by default: all of it is breath; with rain "soil" nothing goes to the air).
    let breath: f32 = if rain == Rain::Soil { 0.0 } else { args.get(10).and_then(|s| s.parse().ok()).unwrap_or(1.0) };
    assert!((0.0..=1.0).contains(&breath), "breath is a share, 0 to 1");
    let breath_tag = if breath == 1.0 || rain == Rain::Soil { String::new() } else { format!("-b{breath}") };
    // The rate of the canopy law (0: no shading, e020).
    let shade_rate: f32 = args.get(11).and_then(|s| s.parse().ok()).unwrap_or(SHADE);
    assert!(shade_rate >= 0.0, "shade is a rate, 0 or more");
    let shade_tag = if shade_rate == SHADE { String::new() } else { format!("-s{shade_rate}") };
    // The radius of the fall (1: the ring of 8 cells; 0: no spill and e021's saturating canopy).
    let spill: usize = args.get(12).and_then(|s| s.parse().ok()).unwrap_or(SPILL);
    let spill_tag = if spill == SPILL { String::new() } else { format!("-spill{spill}") };
    // The chance per base of a point mutation in a child (0: exactly two per child, e021).
    let mutation: f32 = args.get(13).and_then(|s| s.parse().ok()).unwrap_or(MUTATION);
    assert!((0.0..=1.0).contains(&mutation), "mutation is a probability");
    let mut_tag = if mutation == MUTATION { String::new() } else if mutation == 0.0 { "-mutfixed".to_string() } else { format!("-mut{mutation}") };
    // The eye (#26): the most cells a body's sensor blocks can add to its range of one cell,
    // one per block (8 by default: a body of 8 sensors sees 9 cells). 0 is e022's law (every
    // body sees two cells, the second weighted by sensors / 8).
    let eyes: usize = args.get(14).and_then(|s| s.parse().ok()).unwrap_or(EYES);
    let eyes_tag = format!("_eyes{eyes}");
    // The flesh law (#27): the share of the upkeep fixed in the flesh. 0 is e023's law.
    let flesh: f32 = args.get(15).and_then(|s| s.parse().ok()).unwrap_or(FLESH);
    assert!((0.0..=1.0).contains(&flesh), "flesh is a share, 0 to 1");
    let flesh_tag = format!("_flesh{flesh}");
    // The weight law (#25): 0 (every block weighs 1, e024), kind, density, or 1 (both; the default).
    let weight_arg = args.get(16).map(String::as_str).unwrap_or("1");
    let weight = Weight::parse(weight_arg);
    let weight_tag = format!("_w{weight_arg}");
    // The weather (#24): 0 (e025), cloud (the rain's caps weighted by a drifting field) or
    // season (the sun's rate a sine of time), and its amplitude.
    let weather = Weather::parse(args.get(17).map(String::as_str).unwrap_or("0"));
    let amplitude: f32 = args.get(18).and_then(|s| s.parse().ok()).unwrap_or(1.0);
    let winter_arg = args.get(24).map(String::as_str).unwrap_or("flat");
    assert!(amplitude >= 0.0 && (weather != Weather::Season || amplitude <= 1.0 || winter_arg == "high"), "the amplitude is a sigma (cloud) or a share 0 to 1 (season; more under winter high)");
    let weather_tag = match weather {
        Weather::None => String::new(),
        _ => format!("_{}{amplitude}", weather.name()),
    };
    // The digestion law (#32): 1 (the line), 2 (the sharp curve), 0 (e026: every gut digests all of everything).
    let digest_law: u8 = args.get(19).and_then(|s| s.parse().ok()).unwrap_or(0); // 0 by default here: e028 did not keep the law
    assert!(digest_law <= 2, "digest is 0, 1 or 2");
    let digest_tag = format!("_digest{digest_law}");
    // The side of the grid a body grows on (#28): a number (8: e028 byte for byte) or grow (the
    // genome expresses it, 4 to 16).
    let side_law = Side::parse(args.get(20).map(String::as_str).unwrap_or("8"));
    let side_tag = format!("_side{}", side_law.name());
    // The store (e030): the fat the flesh can hold per unit of mass, and spend when the energy
    // is short. 0 is e029's law: the fat is the eater's, never spent, without a ceiling.
    let store: f32 = args.get(21).and_then(|s| s.parse().ok()).unwrap_or(5.0); // 5 by default: e030 kept the law
    assert!(store >= 0.0, "store is fat per unit of mass, 0 or more");
    let store_tag = format!("_store{store}");
    // The yolk (e031): the share of the parent's fat a child is made of (0: e030).
    let yolk: f32 = args.get(22).and_then(|s| s.parse().ok()).unwrap_or(0.0);
    assert!((0.0..=1.0).contains(&yolk), "yolk is a share, 0 to 1");
    let yolk_tag = format!("_yolk{yolk}");
    // Breeding as a decision (e031): 1 gives the policy its fifth output; 0 breeds at the threshold.
    let breed_law: u8 = args.get(23).and_then(|s| s.parse().ok()).unwrap_or(0);
    assert!(breed_law <= 1, "breed is 0 or 1");
    let breed_tag = format!("_breed{breed_law}");
    // The winter (e032): flat (the season's amplitude the same on every cell, e031) or high (the
    // cell's amplitude is a times its height over the relief, at most 1).
    let winter = Winter::parse(args.get(24).map(String::as_str).unwrap_or("flat"));
    assert!(winter == Winter::Flat || relief > 0.0, "a winter by height needs a relief");
    let winter_tag = match winter { Winter::Flat => String::new(), Winter::High => "_winterhigh".to_string() };
    let sigma_name = sigmas.iter().map(|s| format!("{s}")).collect::<Vec<_>>().join("-");
    let cap = RES_CAP;
    let sexual = true;
    let d = D;
    let g = Grid::new(size, size);
    let (w, h) = (g.w, g.h);
    let mut rng = Rng(seed.wrapping_mul(0x9E3779B97F4A7C15) | 1);
    let laws = Laws::new(&mut rng, seed);
    let terrain = Terrain::new(g, seed, relief);
    let mut patches = Patches::new(g, seed, sigmas.clone(), terrain.band.clone());
    let uniform = patches.uniform();
    let init_pop = (INIT_POP_PER_CELL * (w * h) as f32).round() as usize;
    let cell_tag = if cell_energy == CELL_ENERGY { String::new() } else { format!("-cell{cell_energy}") };
    let matter_tag = if matter0 == RES_CAP { String::new() } else { format!("-m{matter0}") };
    let prefix = format!("experiments/e034_stillsoil/results/{size}_sigma{sigma_name}{cell_tag}{matter_tag}_r{relief}_f{flow_rate}_{}{breath_tag}{shade_tag}{spill_tag}{mut_tag}{eyes_tag}{flesh_tag}{weight_tag}{weather_tag}{digest_tag}{side_tag}{store_tag}{yolk_tag}{breed_tag}{winter_tag}_seed{seed}", rain.name());
    let open = |name: &str| std::io::BufWriter::new(std::fs::File::create(format!("{prefix}_{name}")).unwrap());
    let mut log = open("log.csv");
    let mut snaps = Snapshots { long: open("long.jsonl"), clip: open("clip.jsonl"), bodies: open("bodies.jsonl"), ids: HashMap::new() };
    // The soil and the plants of every cell, every AGENT_DUMP_INTERVAL, at two decimals (the
    // long frames carry the soil on a coarse log scale, for the viewer).
    let mut soil_jsonl = open("soil.jsonl");
    // The terrain, once: the height and the band of every cell.
    {
        let mut f = open("terrain.json");
        let list = |v: &[f32]| v.iter().map(|x| format!("{x:.2}")).collect::<Vec<_>>().join(",");
        let bands = terrain.band.iter().map(|b| b.to_string()).collect::<Vec<_>>().join(",");
        writeln!(f, "{{\"relief\":{relief},\"flow\":{flow_rate},\"rain\":\"{}\",\"breath\":{breath},\"shade\":{shade_rate},\"spill\":{spill},\"mutation\":{mutation},\"grain\":{RELIEF_GRAIN},\"weather\":\"{}\",\"amplitude\":{amplitude},\"weather_grain\":{WEATHER_GRAIN},\"weather_span\":{WEATHER_SPAN},\"wind\":{WIND},\"season\":{SEASON},\"digest\":{digest_law},\"digest_floor\":{DIGEST_FLOOR},\"side\":\"{}\",\"side_max\":{SIDE_MAX},\"store\":{store},\"yolk\":{yolk},\"breed\":{breed_law},\"winter\":\"{}\",\"height\":[{}],\"band\":[{bands}]}}", rain.name(), weather.name(), side_law.name(), winter.name(), list(&terrain.height)).unwrap();
    }
    // The air: what bodies burn, until it rains. The most that can fall on each cell per step,
    // and the sum of it.
    let mut air = 0.0f64;
    let rain_caps0 = rain.caps(&terrain.height, relief);
    let mut rain_caps = rain_caps0.clone();
    let mut rain_total: f64 = rain_caps.iter().map(|&c| c as f64).sum();
    // The weather: the cloud's weight per cell (1 everywhere without it) and the season's
    // factor on the sun (1 without it); `sun_now` is the sun of every cell this step.
    let mut cloud = if weather == Weather::Cloud { Some(Cloud::new(g, seed, amplitude)) } else { None };
    let mut cloud_w = vec![1.0f32; w * h];
    let mut cloud_std = 0.0f32;
    let mut sun_factor = 1.0f32;
    let amp_at = winter.amplitudes(amplitude, &terrain.height, relief); // the season's amplitude per cell (e032)
    let mut sun_acc = 0.0f64; // the sun's factor summed over the log interval (a log step is half a season: the instant would always read 1)
    let mut sun_now = vec![RES_GROWTH; w * h];
    let mut weather_csv = if cloud.is_some() { Some(open("weather.csv")) } else { None };
    if let (Some(f), Some(c)) = (weather_csv.as_mut(), cloud.as_ref()) {
        writeln!(f, "step,nodes ({} by {}, row by row)", c.nx, c.ny).unwrap();
    }

    // A place is named by its width in the output (0: beyond every patch); under the uniform
    // sun by its height band (0: valley, 1: slope, 2: ridge).
    let place_name = |p: u8| if uniform { p as f32 } else if p == NO_PLACE { 0.0 } else { sigmas[p as usize] };
    let mut agents_csv = open("agents.csv");
    // bite: force behind a hard tip on the front; bite_any: on any side. shell_front, shell_back,
    // shell_side: mean hardness of the touchable tips on that side (side: left and right together).
    // foot: world cells under the body's cells; len_fwd / len_side: cells the body spans along / across the facing.
    writeln!(agents_csv, "step,mass,born_mass,hard,muscle,sensor,digestive,bite,shell,open,speed,age,energy,plant,meat,lineage,place,born_place,bite_any,shell_front,shell_back,shell_side,foot,len_fwd,len_side,height,fat,size,density,digest,side").unwrap();
    let mut events = open("events.csv");
    writeln!(events, "step,event,lineage,other,size").unwrap(); // other: parent of a split, target of a merge
    let mut lineages_csv = open("lineages.csv");
    // p0, p1: members in the first and second kind of place (by the width list); pnone: beyond every patch.
    writeln!(lineages_csv, "step,lineage,size,mass,hard,muscle,sensor,digestive,bite,shell,open,bodies,age,plant,meat,p0,p1,pnone,bite_any,shell_front,shell_back,shell_side,foot,len_fwd,len_side,height,density,digest,side").unwrap();
    let mut dist_csv = open("dist.csv");
    let mut pop_csv = open("pop.csv"); // e031: the bodies every LINEAGE_INTERVAL, for the winter floor
    writeln!(pop_csv, "step,pop,on_fat,fat_stock,age_mean,pop0,pop1,pop2,cross0,cross1,cross2,soil0,soil1,soil2").unwrap();
    writeln!(dist_csv, "step,measure,value,count").unwrap();
    // Per place, every LOG_INTERVAL: the population and body means of the agents standing there,
    // the share of its cells covered by bodies, the intake eaten there, the lineages present,
    // and the movers (born in the other kind of place).
    let mut places_csv = open("places.csv");
    writeln!(places_csv, "step,place,pop,mass,hard,muscle,sensor,digestive,bite,shell,biters,cover,plant_intake,meat_intake,lineages,movers,foot,shell_front,shell_back,dead,carrion,soil,barren,regrowth,cells,rain,trees,fruit,fruit_intake").unwrap();

    let mut food = Food::new(vec![matter0.min(cap) as f64; w * h], vec![0.0; w * h], vec![(matter0 - cap).max(0.0) as f64; w * h]);
    let mut next_id = 0u64;
    // Occupancy per sub-cell: the index of the body holding it (u32::MAX: none), kept current
    // by every move, turn, break, birth and death, and relabeled when the list of bodies is
    // compacted at the end of a step.
    let mut occ = Occ { sub: vec![u32::MAX; g.sw * g.sh], crowd: vec![0; w * h] };
    let mut agents: Vec<Agent> = Vec::with_capacity(init_pop);
    for _ in 0..init_pop {
        let genome: Vec<u8> = (0..N).map(|_| rng.below(4) as u8).collect();
        let genes = parse_genes(&genome);
        let body = develop_genes(&genes, &laws, weight, side_law);
        next_id += 1;
        let facing = rng.below(4) as u8;
        let mut a = Agent {
            id: next_id - 1, lineage: 0, x: 0, y: 0, energy: INIT_ENERGY as f64, age: 0, plant: 0.0, meat: 0.0, fat: 0.0, born_size: body.size, breed_now: false, born_place: NO_PLACE,
            alive: body.size > 0, keys: sorted_keys(&genes), gene_ids: genes.iter().map(Gene::key).collect(), genome, body, facing,
            wcells: [0; CELLS], tips: [[Tip::default(); SIDE_MAX]; 4], filled: [0; CELLS], n_filled: 0, bbox: [0; 4],
        };
        a.reframe();
        if !a.alive {
            continue;
        }
        // A random sub-cell with room for the body; a body that finds none in eight tries is not made.
        for _ in 0..8 {
            a.x = rng.below(g.sw);
            a.y = rng.below(g.sh);
            if a.fits(g, &occ.sub, u32::MAX, NORTH, 0) {
                a.born_place = patches.place[a.here(g)];
                occ.claim(g, &a, agents.len() as u32);
                agents.push(a);
                break;
            }
        }
    }
    // Bodies by ordered gene list. The body is a pure function of the list (same list, same
    // floating point order, same body), so a child whose list any living agent already has is not
    // developed again. Entries are dropped when nobody living carries the list.
    let mut cache: HashMap<Vec<u16>, Body> = agents.iter().map(|a| (a.gene_ids.clone(), a.body.clone())).collect();
    let mut develops = 0u64;
    // Threads for development (EVLOG_THREADS; default: all cores). Runs sharing a machine should
    // split the cores between them: the total work is the same, threads only shorten one run.
    let threads: usize = std::env::var("EVLOG_THREADS").ok().and_then(|s| s.parse().ok()).unwrap_or_else(|| std::thread::available_parallelism().map(|n| n.get()).unwrap_or(1)).max(1);
    let mut next_lineage = 1u32;
    let mut seen: HashMap<u32, u32> = HashMap::new(); // id -> detections in a row as a group
    let mut origin: HashMap<u32, u32> = HashMap::new(); // provisional id -> id it split from (0 = none)
    let mut lineages: HashMap<u32, usize> = HashMap::new(); // confirmed id -> size at the last detection

    writeln!(
        log,
        "step,pop,mean_energy,mean_res,mean_genes,births,deaths_energy,deaths_age,deaths_broken,deaths_body,cells_broken,plant_intake,meat_intake,\
         stay,forward,left,right,steps_per_sec,mass_mean,mass_std,hard_mean,hard_std,muscle_mean,muscle_std,sensor_mean,sensor_std,\
         digestive_mean,digestive_std,bite_mean,bite_std,speed_mean,speed_std,distinct_bodies,top_body_share,\
         diet_plants,diet_mixed,diet_meat,diet_none,births_with_neighbor,sexual_births,lineages,top_lineage_share,no_lineage_share,\
         sensor_agents_share,sense_decisions,sense_used,res_std,res_above_half,regrowth,develops,\
         prey_age_mean,meat_per_cell,kills_young_share,meat_majority,contacts,shell_mean,open_mean,full_share,damaged_share,biters_share,\
         mass_p10,mass_p50,mass_p90,mass_max,occupied_cells,cover,wasted,intake_per_gut,crossers,pop_none,\
         blocked,shoves,turns_blocked,births_no_room,foot_mean,len_fwd,len_side,bite_any_mean,biters_any_share,shell_front,shell_back,shell_side,pushes,move_spent,shaded,dead,carrion,soil,matter,barren,rot,spent,flow,soil_cells,deep,air,rain,shade,trees,tree_res,res_max,tree_eaten,fruit,fruit_stock,fruit_eaten,clones,mutations,fat_mean,fat_stock,worth,kill_gain,size_mean,density_mean,density_std,sun,cloud_std,digest_mean,digest_std,flesh_guts,dung,side_mean,side_std,size_p10,size_p50,size_p90,size_max,fat_spent,fat_over,on_fat,breed_share,breed_denied"
    )
    .unwrap();

    let mut births = 0u64;
    let mut sexual_births = 0u64;
    let mut births_with_neighbor = 0u64;
    let mut births_no_room = 0u64; // children not born for want of a free cell next to the parent
    let mut deaths = [0u64; 4]; // energy, age, broken (no cells left), body (born without cells)
    let mut cc = Counters::default(); // the contact physics
    let mut plant_intake = 0.0f32;
    let mut plant_at = [0.0f32; N_PLACES + 1]; // intake by the place of the eater
    let mut actions = [0u64; N_OUT];
    let mut moves_tried = 0u64; // forward actions
    let mut blocked = 0u64; // of those, moves that did not happen (the way stayed taken)
    let mut shoves = 0u64; // bodies moved by a push
    let mut pushes = 0u64; // forward actions that pressed on at least one body
    let mut move_spent = 0.0f64; // energy paid for moving, summed over the log interval
    let mut turns_blocked = 0u64; // turns that did not happen (no room for the turned body)
    let mut sense_decisions = 0u64; // moves decided by an agent with at least one sensor block
    let mut sense_used = 0u64; // of those, moves that differ from what the agent would do with sense = 0
    let mut regrowth = 0.0f64; // food actually added (the cap wastes the rest), summed over the log interval
    let mut wasted = 0.0f64; // regrowth lost to the cap (a full cell does not grow)
    let mut shaded = 0.0f64; // regrowth lost to bodies standing on cells (a plant under a body does not grow)
    let mut barren = 0.0f64; // regrowth lost for want of soil
    let mut barren_at = [0.0f64; N_PLACES + 1];
    let mut regrowth_at = [0.0f64; N_PLACES + 1];
    let mut rot = 0.0f64; // dead matter returned to the soil
    let mut spent = 0.0f64; // what living bodies returned to the soil (upkeep and the work of moving)
    let mut breed_decisions = 0u64; // e031: decisions that were to breed, over the log interval
    let mut breed_denied = 0u64; // of those, made below the threshold
    let mut fat_spent = 0.0f64; // the store (e030): fat burned by bodies short of energy, over the log interval
    let mut fat_over = 0.0f64; // fat breathed for want of room in the flesh, over the log interval
    let mut flowed = 0.0f64; // soil that ran downhill, summed over the log interval
    let mut rained = 0.0f64; // rain fallen, summed over the log interval
    let mut rain_at = [0.0f64; N_PLACES + 1];
    let mut shade_moved = 0.0f64; // sun moved to taller columns, summed over the log interval
    let mut tree_eaten = 0.0f64; // intake from cells holding TREE or more, summed over the log interval
    let mut delta = vec![0.0f64; w * h]; // scratch for the flow
    let mut light = vec![0.0f32; w * h]; // the sun of each cell after the canopy
    let mut crown = vec![0.0f32; w * h]; // the light each column took from around it
    let mut claims = vec![0.0f32; w * h]; // scratch for the canopy
    let mut fruit_out = vec![0.0f32; w * h]; // the fruit each cell made this step, before it falls
    let mut fruit_fallen = 0.0f64; // fruit fallen, summed over the log interval
    let mut fruit_at = [0.0f64; N_PLACES + 1]; // by the cell of the column that made it
    let mut fruit_eaten = 0.0f64; // intake from fruit, summed over the log interval
    let mut fruit_eaten_at = [0.0f64; N_PLACES + 1];
    let mut children = 0usize; // children conceived over the log interval (placed or not)
    let mut mutations = 0usize; // point mutations in them
    let mut clones = 0usize; // children conceived without one
    let mut last_time = std::time::Instant::now();
    let trace = std::env::var("EVLOG_TRACE").is_ok();

    // The ledger (EVLOG_AUDIT=1): the world's matter every step, with the step's events, to
    // stderr. Found the deficit leak above; costs a sum over the ground per step.
    let audit = std::env::var("EVLOG_AUDIT").is_ok();
    let (mut audit_prev, mut audit_kills, mut audit_broken, mut audit_births) = (0.0f64, 0u64, 0u64, 0u64);
    for step in 1..=steps {
        if step % PATCH_DRIFT == 0 {
            patches.drift(g);
        }
        // The air rains on the ground (into the soil), then the dead rot into the soil and the
        // plants grow out of it: by at most the sun, not above the cap (dead matter can lie
        // above it, and then nothing grows), and not on a cell held by a body (e016).
        if let Some(c) = cloud.as_mut() {
            c.advance();
            c.weights(g, step, &mut cloud_w);
            rain_total = 0.0;
            for i in 0..w * h {
                rain_caps[i] = rain_caps0[i] * cloud_w[i];
                rain_total += rain_caps[i] as f64;
            }
            if step % WEATHER_LOG == 0 {
                if let Some(f) = weather_csv.as_mut() {
                    writeln!(f, "{step},{}", c.nodes.iter().map(|x| format!("{x:.3}")).collect::<Vec<_>>().join(",")).unwrap();
                }
            }
        }
        if weather == Weather::Season {
            let phase = (2.0 * std::f32::consts::PI * step as f32 / SEASON).sin();
            let mut acc = 0.0f64;
            for i in 0..w * h {
                let f = 1.0 + amp_at[i] * phase;
                sun_now[i] = patches.grow[i] * f;
                acc += f as f64;
            }
            sun_factor = (acc / (w * h) as f64) as f32;
        }
        sun_acc += sun_factor as f64;
        let sun_ref: &[f32] = if weather == Weather::Season { &sun_now } else { &patches.grow };
        rained += food.rain(&mut air, &rain_caps, rain_total, &patches.place, &mut rain_at);
        // The canopy moves the light to the taller columns, then every cell grows under what
        // light it has left.
        if shade_rate > 0.0 {
            shade_moved += food.shade(g, sun_ref, shade_rate, cap, &occ.crowd, spill > 0, &mut claims, &mut light, &mut crown) as f64;
        } else {
            light.copy_from_slice(sun_ref);
            crown.iter_mut().for_each(|c| *c = 0.0);
        }
        for c in 0..w * h {
            let r = food.regrow(c, light[c], crown[c], occ.crowd[c] > 0, cap, spill > 0);
            let p = patches.place[c] as usize;
            regrowth += r.added as f64;
            regrowth_at[p] += r.added as f64;
            shaded += r.shaded as f64;
            wasted += r.wasted as f64;
            barren += r.barren as f64;
            barren_at[p] += r.barren as f64;
            rot += r.rot as f64;
            fruit_at[p] += r.fruit as f64;
            fruit_out[c] = r.fruit;
        }
        // Then the fruit falls around the columns that made it.
        if spill > 0 {
            fruit_fallen += food.spill(g, &fruit_out, spill) as f64;
        }
        // A trace of the world's stores every 100 steps, for the start (EVLOG_TRACE=1).
        if trace && step % 100 == 0 {
            let res: f64 = food.res.iter().map(|&r| r as f64).sum();
            let fruit: f64 = food.fruit.iter().map(|&r| r as f64).sum();
            let soil: f64 = food.soil.iter().sum();
            let pop = agents.iter().filter(|a| a.alive).count();
            eprintln!("trace step {step} pop {pop} plants {res:.0} fruit {fruit:.0} soil {soil:.0} air {air:.0} eaten {:.1} fruit_eaten {:.1} fruit_fallen {:.1} regrowth {:.1} barren {:.1} shaded {:.1} shade {:.1}",
                (plant_intake as f64 + cc.meat_intake as f64) / (step % LOG_INTERVAL).max(1) as f64, fruit_eaten / (step % LOG_INTERVAL).max(1) as f64, fruit_fallen / (step % LOG_INTERVAL).max(1) as f64,
                regrowth / (step % LOG_INTERVAL).max(1) as f64, barren / (step % LOG_INTERVAL).max(1) as f64, shaded / (step % LOG_INTERVAL).max(1) as f64, shade_moved / (step % LOG_INTERVAL).max(1) as f64);
        }
        // Then the soil runs downhill.
        if flow_rate > 0.0 {
            flowed += food.flow(g, &terrain.height, flow_rate, &mut delta) as f64;
        }
        // The world cells the body would newly lie over after moving k world cells in
        // direction d (those under its box moved k * SUB sub-cells, less those under it now
        // and those one cell before): the food there and the crowd (sub-cells held by
        // bodies, in world cells) there. The row of cells k cells ahead, as wide as the body.
        let look = |a: &Agent, d: usize, k: usize, res: &[f64], occ: &Occ| -> (f32, f32) {
            let now = a.under(g, NORTH, 0);
            let before = if k > 1 { a.under(g, d, (k - 1) * SUB) } else { now };
            let mut food = 0.0;
            let mut others = 0.0;
            for c in a.under(g, d, k * SUB).iter() {
                if now.contains(c) || before.contains(c) {
                    continue;
                }
                food += res[c] as f32;
                others += occ.crowd[c] as f32 / SUB_CELLS as f32;
            }
            (food, others)
        };

        let mut newborn = Vec::new();
        let mut pending: Vec<(Agent, Option<Vec<Gene>>, usize)> = Vec::new(); // child, genes to develop, parent
        for i in 0..agents.len() {
            if !agents[i].alive {
                continue;
            }

            // 1. Eat: each digestive cell eats from the world cell under it, plant and dead
            //    matter alike; the gut digests its yield of each (#32: by the axis; without
            //    the law, all of both) and the rest is dung, to the soil of the cell.
            let a = &mut agents[i];
            a.age += 1;
            let size = a.body.size as f32; // the upkeep is per living cell; the weight is paid in moving
            let (plant_yield, flesh_yield) = a.body.yields(digest_law);
            let mut eaten = 0.0f64; // digested
            let mut dead_eaten = 0.0f32; // digested, of the dead matter
            let mut guts = CellsUnder::default();
            let mut gut_n = [0u8; UNDER_MAX];
            for p in a.cells_held() {
                if a.wcells[p] == DIGESTIVE as u8 {
                    let (sx, sy) = a.sub_at(g, p, NORTH, 0);
                    let c = g.wcell(sx, sy);
                    guts.add(c);
                    gut_n[guts.c[..guts.n].iter().position(|&x| x == c).unwrap()] += 1;
                }
            }
            for (k, c) in guts.iter().enumerate() {
                let e = food.res[c].min((BITE * gut_n[k] as f32) as f64);
                if food.res[c] - food.carrion[c] - food.fruit[c] >= TREE as f64 {
                    tree_eaten += e;
                }
                let (plant, dead, fruit) = food.take(c, e);
                // The dung is what the yields leave (nothing without the law: the take is digested whole).
                let dung = (plant + fruit) * (1.0 - plant_yield) + dead * (1.0 - flesh_yield);
                food.spend(c, dung);
                cc.dung += dung;
                eaten += e - dung;
                dead_eaten += (dead * flesh_yield) as f32;
                plant_at[patches.place[c] as usize] += (plant * plant_yield) as f32 + (fruit * plant_yield) as f32;
                cc.meat_at[patches.place[c] as usize] += (dead * flesh_yield) as f32;
                fruit_eaten += fruit as f32 as f64; // rounded as e026 did
                fruit_eaten_at[patches.place[c] as usize] += fruit as f32 as f64;
            }
            // Upkeep: the breath share goes to the air, the rest to the soil under the body (all
            // of it with rain "soil"); all of it, or what the body has left.
            let full = (UPKEEP * size + UPKEEP_BODY) as f64;
            let from_energy = full.min((a.energy + eaten).max(0.0));
            // The store (e030): what the energy cannot pay, the fat pays; what the fat pays is
            // breathed, not fixed again. Without the law the fat pays nothing.
            let from_fat = if store > 0.0 { (full - from_energy).min(a.fat) } else { 0.0 };
            let upkeep = from_energy + from_fat;
            // The flesh law (#27): a share `flesh` of the upkeep paid from the energy is fixed in
            // the body's flesh (`fat`); the rest is breathed as before. With the store the flesh
            // holds at most `store` per unit of mass, and what is fixed beyond that is breathed.
            let fixed = from_energy * flesh as f64;
            a.fat += fixed - from_fat;
            let over = if store > 0.0 { (a.fat - (store * a.body.mass) as f64).max(0.0) } else { 0.0 };
            a.fat -= over;
            let burned = upkeep - fixed + over;
            fat_spent += from_fat;
            fat_over += over;
            if breath < 1.0 {
                food.spend(a.here(g), burned * (1.0 - breath) as f64);
            }
            air += burned * breath as f64;
            spent += upkeep;
            // A body pays what it has and no more: its energy stops at zero (it dies at the end
            // of the step unless it gains first). e024 let it go below zero and a kill in the
            // same step filled the deficit with matter the ledger had counted: 0.2-1.8% of the
            // world's matter over a run, most of the drift blamed on the f32 ground (#31).
            a.energy += eaten - from_energy;
            a.plant += eaten as f32 - dead_eaten;
            a.meat += dead_eaten;
            plant_intake += eaten as f32 - dead_eaten;
            cc.meat_intake += dead_eaten;

            // 2. Decide: the world seen from the body. Food under it; food and bodies ahead,
            //    behind, left, right, as far as the eye's range, what lies j cells away seen
            //    at 1/j (the light that reaches the eye falls with the distance); energy.
            //    `blind` is the same body with no sensor (one cell), the knockout (e009).
            //    With eyes 0, e022's law: two cells, the second weighted by sense.
            let a = &agents[i];
            let s = a.body.sense();
            let range = a.body.range(eyes);
            let thr = a.body.threshold();
            let f = a.facing as usize;
            let dirs = [f, opposite(f), left_of(f), opposite(left_of(f))];
            let here: f32 = a.under(g, NORTH, 0).iter().map(|c| food.res[c] as f32).sum();
            let mut input = [0.0f32; N_IN];
            let mut blind = [0.0f32; N_IN];
            input[0] = here;
            blind[0] = here;
            for (k, &d) in dirs.iter().enumerate() {
                let (food1, others1) = look(a, d, 1, &food.res, &occ);
                blind[1 + k] = food1;
                blind[5 + k] = others1;
                if eyes == 0 {
                    let (food2, others2) = look(a, d, 2, &food.res, &occ);
                    input[1 + k] = food1 + s * food2;
                    input[5 + k] = others1 + s * others2;
                } else {
                    input[1 + k] = food1;
                    input[5 + k] = others1;
                    for j in 2..=range {
                        let (fj, oj) = look(a, d, j, &food.res, &occ);
                        input[1 + k] += fj / j as f32;
                        input[5 + k] += oj / j as f32;
                    }
                }
            }
            input[9] = (a.energy / thr as f64) as f32;
            blind[9] = input[9];
            let (mut action, best_v) = act_value(&a.body.policy, &input);
            // Breeding as a decision (e031): the fifth output; when it wins, the body stays and
            // breeds this step if it can (below). Counted apart from the four moves.
            let mut breed_now = false;
            if breed_law == 1 {
                let mut v = a.body.breed[N_IN];
                for i in 0..N_IN {
                    v += a.body.breed[i] * input[i];
                }
                // A body that cannot breed (energy below the threshold) takes the best of the
                // four moves instead: the first form stood still on a denied decision, 44% of
                // all decisions at the start, and the world died in its first winter.
                if v > best_v {
                    breed_decisions += 1;
                    if a.energy >= thr as f64 {
                        breed_now = true;
                        action = 0;
                    } else {
                        breed_denied += 1;
                    }
                }
            }
            actions[action] += 1;
            if a.body.kinds[SENSOR] > 0 {
                sense_decisions += 1;
                if act(&a.body.policy, &blind) != action {
                    sense_used += 1;
                }
            }
            agents[i].breed_now = breed_now;

            // 3. Act. Forward: one sub-cell along the facing. Every cell of the body whose next
            //    sub-cell is held by another body presses on it (the contact physics); a body
            //    still in the way is shoved one sub-cell if the muscle pressing on it exceeds
            //    its mass and it has room; then the move happens if the way is clear, and a
            //    second sub-cell follows with probability speed if that way is clear too. The
            //    mover pays for the mass it moved (its own and what it shoved) times the
            //    distance; a forward action that moved nothing costs nothing. Turn: the grid
            //    rotates about its center; the turn happens if the sub-cells it would newly
            //    hold are free.
            if action == 1 {
                moves_tried += 1;
                let d = f;
                let pressed = push(&mut agents, i, d, g, &mut occ, &patches.place, &mut food, cell_energy, digest_law, &mut cc);
                if agents[i].alive {
                    if !pressed.is_empty() {
                        pushes += 1;
                    }
                    let mut work = 0.0f32; // mass moved times sub-cells moved
                    for &(j, force) in &pressed {
                        if !agents[j].alive || agents[i].fits(g, &occ.sub, i as u32, d, 1) || force as f32 <= agents[j].body.mass {
                            continue;
                        }
                        if agents[j].fits(g, &occ.sub, j as u32, d, 1) {
                            occ.release(g, &agents[j]);
                            let (nx, ny) = g.sstep(agents[j].x, agents[j].y, d, 1);
                            agents[j].x = nx;
                            agents[j].y = ny;
                            occ.claim(g, &agents[j], j as u32);
                            shoves += 1;
                            work += agents[j].body.mass;
                        }
                    }
                    let mut moved = 0;
                    if agents[i].fits(g, &occ.sub, i as u32, d, 1) {
                        occ.release(g, &agents[i]);
                        let (nx, ny) = g.sstep(agents[i].x, agents[i].y, d, 1);
                        agents[i].x = nx;
                        agents[i].y = ny;
                        moved = 1;
                        if rng.f32() < agents[i].body.speed() && agents[i].fits(g, &occ.sub, i as u32, d, 1) {
                            let (nx, ny) = g.sstep(nx, ny, d, 1);
                            agents[i].x = nx;
                            agents[i].y = ny;
                            moved = 2;
                        }
                        occ.claim(g, &agents[i], i as u32);
                    } else {
                        blocked += 1;
                    }
                    work += agents[i].body.mass * moved as f32;
                    let cost = MOVE_COST * work;
                    // The work of moving: the breath share goes to the air, the rest to the soil
                    // under the body where it stands now.
                    let paid = (cost as f64).min(agents[i].energy.max(0.0));
                    if breath < 1.0 {
                        food.spend(agents[i].here(g), paid * (1.0 - breath) as f64);
                    }
                    air += paid * breath as f64;
                    spent += paid;
                    agents[i].energy -= paid;
                    move_spent += paid;
                }
            } else if action >= 2 {
                let nf = if action == 2 { left_of(f) } else { opposite(left_of(f)) };
                let a = &agents[i];
                let (list, n, _) = filled(&rotate(&a.body.cells, nf, a.body.s()), a.body.s());
                if list[..n as usize].iter().all(|&p| {
                    let (sx, sy) = a.sub_at(g, p as usize, NORTH, 0);
                    let o = occ.sub[g.sidx(sx, sy)];
                    o == u32::MAX || o == i as u32
                }) {
                    occ.release(g, &agents[i]);
                    agents[i].facing = nf as u8;
                    agents[i].reframe();
                    occ.claim(g, &agents[i], i as u32);
                } else {
                    turns_blocked += 1;
                }
            }
            if !agents[i].alive {
                continue;
            }

            // 4. Reproduce. The parent pays (half of its energy goes to the child). In sexual
            //    mode it first looks for a mate within distance D among the bodies touching the
            //    ring around its 2x2 block; the child is a one-point crossover of the two
            //    genomes. Without a mate the child is a copy, as in e005. Then 2 point
            //    mutations. The child is placed once its body is known (below).
            if agents[i].energy >= thr as f64 && (breed_law == 0 || agents[i].breed_now) {
                let mut mate = None;
                let mut neighbor = false;
                if sexual {
                    // Bodies within two sub-cells of the parent's box.
                    let a = &agents[i];
                    let [r0, r1, c0, c1] = a.bbox;
                    let (x0, y0) = (a.x + g.sw + c0 as usize - 2, a.y + g.sh + r0 as usize - 2);
                    'cells: for dy in 0..(r1 - r0 + 5) as usize {
                        for dx in 0..(c1 - c0 + 5) as usize {
                            let j = occ.sub[g.sidx((x0 + dx) % g.sw, (y0 + dy) % g.sh)];
                            if j == u32::MAX || j as usize == i {
                                continue;
                            }
                            let p = &agents[j as usize];
                            if p.alive {
                                neighbor = true;
                                if agents[i].distance(p) <= d {
                                    mate = Some(j as usize);
                                    break 'cells;
                                }
                            }
                        }
                    }
                }
                if neighbor {
                    births_with_neighbor += 1;
                }
                let mut genome = agents[i].genome.clone();
                if let Some(j) = mate {
                    let cut = rng.below(N);
                    genome[cut..].copy_from_slice(&agents[j].genome[cut..]);
                    sexual_births += 1;
                }
                let a = &mut agents[i];
                a.energy *= 0.5;
                // The yolk (e031): the child is made of the share `yolk` of the parent's fat.
                let yolk_fat = a.fat * yolk as f64;
                a.fat -= yolk_fat;
                // Mutation: a chance per base (most children copy their parent; some carry
                // several changes), or exactly MUTATIONS_PER_CHILD at random positions (e021).
                let mut n_mut = 0usize;
                if mutation > 0.0 {
                    for base in genome.iter_mut() {
                        if rng.f32() < mutation {
                            *base = (*base + 1 + rng.below(3) as u8) % 4;
                            n_mut += 1;
                        }
                    }
                } else {
                    for _ in 0..MUTATIONS_PER_CHILD {
                        let pos = rng.below(N);
                        genome[pos] = (genome[pos] + 1 + rng.below(3) as u8) % 4;
                        n_mut += 1;
                    }
                }
                children += 1;
                mutations += n_mut;
                clones += (n_mut == 0) as usize;
                // The body is a function of the gene list alone. A mutation outside the genes
                // (most of them) gives the parent's body without developing it again.
                let genes = parse_genes(&genome);
                let gene_ids: Vec<u16> = genes.iter().map(Gene::key).collect();
                let body = cache.get(&gene_ids).cloned(); // the birth body of this gene list (the parent's may be damaged)
                next_id += 1;
                let keys = sorted_keys(&genes);
                let todo = body.is_none().then_some(genes);
                pending.push((Agent {
                    id: next_id - 1, lineage: a.lineage, x: a.x, y: a.y, energy: a.energy, age: 0, plant: 0.0, meat: 0.0, fat: yolk_fat, born_size: 0, breed_now: false, born_place: NO_PLACE, alive: true,
                    keys, gene_ids, genome, body: body.unwrap_or_else(|| Body::new([0; CELLS], SIDE, [0.0; N_POLICY], 0, 1.0, weight.kind)), facing: rng.below(4) as u8,
                    wcells: [0; CELLS], tips: [[Tip::default(); SIDE_MAX]; 4], filled: [0; CELLS], n_filled: 0, bbox: [0; 4],
                }, todo, i));
            }
        }
        // Develop the children with a new gene list, one development per distinct list, on all
        // cores. The children keep their birth order, so the result is the same as developing
        // them one by one in the loop.
        let mut jobs: Vec<(&[u16], &[Gene])> = Vec::new();
        for (a, genes, _) in &pending {
            if let Some(g) = genes {
                if !jobs.iter().any(|(k, _)| *k == a.gene_ids.as_slice()) {
                    jobs.push((&a.gene_ids, g));
                }
            }
        }
        develops += jobs.len() as u64;
        let mut developed: Vec<Body> = Vec::with_capacity(jobs.len());
        let n_threads = threads.min(jobs.len() / 2); // at least two developments per thread
        if n_threads < 2 {
            developed.extend(jobs.iter().map(|(_, g)| develop_genes(g, &laws, weight, side_law)));
        } else {
            let chunk = jobs.len().div_ceil(n_threads);
            let laws = &laws;
            let parts: Vec<Vec<Body>> = std::thread::scope(|sc| {
                let handles: Vec<_> = jobs.chunks(chunk).map(|c| sc.spawn(move || c.iter().map(|(_, g)| develop_genes(g, laws, weight, side_law)).collect::<Vec<Body>>())).collect();
                handles.into_iter().map(|h| h.join().unwrap()).collect()
            });
            developed.extend(parts.into_iter().flatten());
        }
        for ((k, _), b) in jobs.iter().zip(developed) {
            cache.insert(k.to_vec(), b);
        }
        // Place each child: the first anchor where its cells find free sub-cells, one to a
        // grid's side of sub-cells (the larger of the parent's and the child's; eight, two
        // world cells, up to e028) from the parent's anchor in the four directions (from a
        // random one). Without room the child is lost with the energy the parent gave it (as
        // a child born without cells, e013).
        for (mut a, genes, parent) in pending.drain(..) {
            if genes.is_some() {
                a.body = cache[&a.gene_ids].clone();
            }
            a.born_size = a.body.size;
            a.alive = a.body.size > 0;
            if !a.alive {
                deaths[3] += 1;
                newborn.push(a);
                continue;
            }
            a.reframe();
            let (px, py) = (agents[parent].x, agents[parent].y);
            let reach = agents[parent].body.s().max(a.body.s());
            let start = rng.below(4);
            let mut spot = None;
            'search: for t in 0..4 {
                let d = DIRS[(start + t) % 4];
                for k in 1..=reach {
                    let (cx, cy) = g.sstep(px, py, d, k);
                    a.x = cx;
                    a.y = cy;
                    if a.fits(g, &occ.sub, u32::MAX, NORTH, 0) {
                        spot = Some((cx, cy));
                        break 'search;
                    }
                }
            }
            // The parent pays the matter of the child's body from what it has left; a parent
            // that cannot (a small body with a big child) makes no child, as without room.
            let afford = agents[parent].energy >= (cell_energy * a.body.mass) as f64;
            match spot {
                Some((cx, cy)) if afford => {
                    a.x = cx;
                    a.y = cy;
                    a.born_place = patches.place[a.here(g)];
                    occ.claim(g, &a, (agents.len() + newborn.len()) as u32);
                    agents[parent].energy -= (cell_energy * a.body.mass) as f64; // the matter of the child's body
                    newborn.push(a);
                }
                _ => {
                    // The child is never made; what the parent gave it lies where the parent stands.
                    births_no_room += 1;
                    food.lay(g.wcell(px, py), a.energy + a.fat, &patches.place, &mut cc);
                }
            }
        }
        births += newborn.len() as u64;
        agents.append(&mut newborn);
        // The dead leave their sub-cells; the list is compacted and the survivors relabeled.
        for a in agents.iter_mut() {
            let dead = if !a.alive {
                true
            } else if a.energy <= 0.0 && !(store > 0.0 && a.fat > 0.0) {
                // With the store a body at zero energy lives on its fat until that is gone.
                deaths[0] += 1;
                true
            } else if a.age > MAX_AGE {
                deaths[1] += 1;
                true
            } else {
                false
            };
            if dead {
                occ.release(g, a);
                a.alive = false;
                lay_body(a, g, &mut food, &patches.place, cell_energy, &mut cc);
            }
        }
        agents.retain(|a| a.alive);
        for (i, a) in agents.iter().enumerate() {
            occ.relabel(g, a, i as u32);
        }
        if audit {
            let m = food.soil.iter().sum::<f64>() + food.res.iter().sum::<f64>() + air
                + agents.iter().map(|a| a.energy.max(0.0) as f64 + a.fat as f64 + cell_energy as f64 * a.body.mass as f64).sum::<f64>();
            eprintln!("AUDIT {step} {m:.6} {:.6} kills {} broken {} births {} deaths {:?}", m - audit_prev, cc.kills - audit_kills, cc.cells_broken - audit_broken, births - audit_births, deaths);
            audit_prev = m;
            audit_kills = cc.kills;
            audit_broken = cc.cells_broken;
            audit_births = births;
        }

        if step % LINEAGE_INTERVAL == 0 {
            let n = agents.len().max(1) as f64;
            // Per height band (e032): the bodies standing there, and of those the ones born in another band.
            let (mut at, mut cross) = ([0usize; N_BANDS], [0usize; N_BANDS]);
            for a in agents.iter() {
                let b = terrain.band[a.here(g)] as usize;
                at[b] += 1;
                if a.born_place != NO_PLACE && a.born_place as usize != b {
                    cross[b] += 1;
                }
            }
            let mut soil_at = [0.0f64; N_BANDS]; // e033: the soil per band
            for c in 0..w * h {
                soil_at[terrain.band[c] as usize] += food.soil[c];
            }
            writeln!(pop_csv, "{step},{},{:.4},{:.1},{:.0},{},{},{},{},{},{},{:.0},{:.0},{:.0}", agents.len(), agents.iter().filter(|a| a.energy <= 0.0).count() as f64 / n, agents.iter().map(|a| a.fat).sum::<f64>(), agents.iter().map(|a| a.age as f64).sum::<f64>() / n,
                at[0], at[1], at[2], cross[0], cross[1], cross[2], soil_at[0], soil_at[1], soil_at[2]).unwrap();
        }
        if step % LINEAGE_INTERVAL == 0 {
            let live: std::collections::HashSet<&[u16]> = agents.iter().map(|a| a.gene_ids.as_slice()).collect();
            cache.retain(|k, _| live.contains(k.as_slice()));
        }
        // Lineages: groups connected by possible mating (single linkage at distance D).
        if step % LINEAGE_INTERVAL == 0 {
            let n = agents.len();
            let mut parent: Vec<usize> = (0..n).collect();
            fn find(p: &mut Vec<usize>, mut i: usize) -> usize {
                while p[i] != i {
                    p[i] = p[p[i]];
                    i = p[i];
                }
                i
            }
            // Agents with the same gene list are at distance 0, so one representative per list is
            // enough: link the representatives, then attach the copies. Same groups as all pairs.
            let mut reps: HashMap<&[u16], usize> = HashMap::new();
            let mut uniq: Vec<usize> = Vec::new();
            for i in 0..n {
                match reps.get(agents[i].keys.as_slice()) {
                    Some(&r) => parent[i] = r,
                    None => {
                        reps.insert(agents[i].keys.as_slice(), i);
                        uniq.push(i);
                    }
                }
            }
            for a in 0..uniq.len() {
                for b in a + 1..uniq.len() {
                    let (i, j) = (uniq[a], uniq[b]);
                    if agents[i].distance(&agents[j]) <= d {
                        let (ri, rj) = (find(&mut parent, i), find(&mut parent, j));
                        if ri != rj {
                            parent[ri] = rj;
                        }
                    }
                }
            }
            let mut members: HashMap<usize, Vec<usize>> = HashMap::new();
            for i in 0..n {
                let r = find(&mut parent, i);
                members.entry(r).or_default().push(i);
            }
            let mut groups: Vec<Vec<usize>> = members.into_values().filter(|m| m.len() >= MIN_LINEAGE).collect();
            groups.sort_by_key(|m| (std::cmp::Reverse(m.len()), agents[m[0]].id));
            // Each group keeps the id most of its members inherited (confirmed ids first), unless a bigger group took it;
            // then it gets a provisional id. An id becomes a lineage (event: birth, or split from
            // the id it wanted) once its group has existed LINEAGE_CONFIRM detections in a row.
            // Members of groups smaller than MIN_LINEAGE keep their id. A lineage whose carriers
            // were all relabeled into another group has merged into it; one whose carriers all
            // died is extinct.
            let mut before: HashMap<u32, usize> = HashMap::new();
            for a in &agents {
                *before.entry(a.lineage).or_default() += 1;
            }
            let mut now: HashMap<u32, usize> = HashMap::new();
            let mut assigned: Vec<(u32, Vec<usize>)> = Vec::new();
            for m in groups {
                let mut votes: HashMap<u32, usize> = HashMap::new();
                for &i in &m {
                    if agents[i].lineage != 0 {
                        *votes.entry(agents[i].lineage).or_default() += 1;
                    }
                }
                // A confirmed lineage id wins over a provisional one, so that a provisional group
                // that rejoins its lineage dissolves into it instead of renaming it.
                let best = |confirmed: bool| votes.iter().filter(|(id, _)| lineages.contains_key(id) == confirmed).max_by_key(|(id, c)| (**c, std::cmp::Reverse(**id))).map(|(id, _)| *id);
                let inherited = best(true).or_else(|| best(false)).unwrap_or(0);
                let id = if inherited != 0 && !now.contains_key(&inherited) {
                    inherited
                } else {
                    let id = next_lineage;
                    next_lineage += 1;
                    origin.insert(id, inherited);
                    id
                };
                now.insert(id, m.len());
                assigned.push((id, m));
            }
            seen.retain(|id, _| now.contains_key(id));
            let mut ids: Vec<u32> = now.keys().copied().collect();
            ids.sort_unstable(); // HashMap order differs between processes; the log should not
            for id in ids {
                let size = now[&id];
                let n = seen.entry(id).or_insert(0);
                *n += 1;
                if *n == LINEAGE_CONFIRM && !lineages.contains_key(&id) {
                    let from = origin.remove(&id).unwrap_or(0);
                    let event = if from == 0 { "birth" } else { "split" };
                    writeln!(events, "{step},{event},{id},{from},{size}").unwrap();
                    lineages.insert(id, size);
                }
            }
            let mut into: HashMap<(u32, u32), usize> = HashMap::new(); // (old id, new id) -> relabeled
            for (id, m) in &assigned {
                for &i in m {
                    if agents[i].lineage != *id {
                        *into.entry((agents[i].lineage, *id)).or_default() += 1;
                    }
                    agents[i].lineage = *id;
                }
                if !lineages.contains_key(id) {
                    continue;
                }
                let sz = m.len() as f32;
                let mut kinds = [0.0f32; N_KINDS];
                let (mut mass, mut bite, mut shell, mut open) = (0.0f32, 0.0f32, 0.0f32, 0.0f32);
                let (mut age, mut plant, mut meat) = (0.0f32, 0.0f32, 0.0f32);
                let (mut bite_any, mut s_front, mut s_back, mut s_side, mut foot, mut long, mut wide, mut height) = (0.0f32, 0.0f32, 0.0f32, 0.0f32, 0.0f32, 0.0f32, 0.0f32, 0.0f32);
                let (mut density, mut digest, mut side_sum) = (0.0f32, 0.0f32, 0.0f32);
                let mut bodies: HashMap<(u8, &[u8; CELLS]), usize> = HashMap::new();
                let mut at = [0usize; N_PLACES + 1];
                for &i in m {
                    at[patches.place[agents[i].here(g)] as usize] += 1;
                    for k in 0..N_KINDS {
                        kinds[k] += agents[i].body.kinds[k] as f32;
                    }
                    let b = &agents[i].body;
                    mass += b.mass;
                    density += b.density;
                    digest += b.digest;
                    side_sum += b.side as f32;
                    bite += b.bite() as f32;
                    shell += b.shell();
                    open += b.open_lines() as f32;
                    bite_any += b.bite_any() as f32;
                    s_front += b.shell_side(NORTH);
                    s_back += b.shell_side(SOUTH);
                    s_side += 0.5 * (b.shell_side(EAST) + b.shell_side(WEST));
                    foot += agents[i].foot_n(g) as f32;
                    long += b.extent[0] as f32;
                    wide += b.extent[1] as f32;
                    height += terrain.height[agents[i].here(g)];
                    age += agents[i].age as f32;
                    plant += agents[i].plant;
                    meat += agents[i].meat;
                    *bodies.entry((agents[i].body.side, &agents[i].body.cells)).or_insert(0) += 1;
                }
                writeln!(lineages_csv, "{step},{id},{},{:.1},{:.1},{:.1},{:.1},{:.1},{:.1},{:.2},{:.1},{},{:.0},{:.2},{:.2},{},{},{},{:.1},{:.2},{:.2},{:.2},{:.2},{:.2},{:.2},{:.1},{:.3},{:.3},{:.2}", m.len(), mass / sz,
                    kinds[HARD] / sz, kinds[MUSCLE] / sz, kinds[SENSOR] / sz, kinds[DIGESTIVE] / sz, bite / sz, shell / sz, open / sz, bodies.len(), age / sz, plant / sz, meat / sz,
                    at[0], at[1], at[N_PLACES], bite_any / sz, s_front / sz, s_back / sz, s_side / sz, foot / sz, long / sz, wide / sz, height / sz, density / sz, digest / sz, side_sum / sz).unwrap();
            }
            let mut carriers: HashMap<u32, usize> = HashMap::new();
            for a in &agents {
                *carriers.entry(a.lineage).or_default() += 1;
            }
            let mut gone: Vec<u32> = lineages.keys().filter(|id| !carriers.contains_key(id)).copied().collect();
            gone.sort();
            for id in gone {
                let size = lineages.remove(&id).unwrap();
                let target = into.iter().filter(|((old, _), _)| *old == id).max_by_key(|((_, new), c)| (**c, std::cmp::Reverse(*new)));
                match target {
                    Some(((_, new), _)) if before.get(&id).copied().unwrap_or(0) > 0 => {
                        writeln!(events, "{step},merge,{id},{new},{size}").unwrap();
                    }
                    _ => writeln!(events, "{step},extinct,{id},0,{size}").unwrap(),
                }
            }
            for (id, size) in &now {
                if let Some(s) = lineages.get_mut(id) {
                    *s = *size;
                }
            }
        }
        // Pairwise distance histograms over all living pairs, three measures.
        if step % DIST_INTERVAL == 0 {
            let mut h = [vec![0u64; N + 1], vec![0u64; 128], vec![0u64; CELLS + 1]];
            for i in 0..agents.len() {
                for j in i + 1..agents.len() {
                    let (a, b) = (&agents[i], &agents[j]);
                    h[0][hamming(&a.genome, &b.genome)] += 1;
                    h[1][gene_distance(&a.keys, &b.keys).min(127)] += 1;
                    h[2][a.body.cells.iter().zip(&b.body.cells).filter(|(x, y)| x != y).count()] += 1;
                }
            }
            for (name, hist) in ["hamming", "genes", "body"].iter().zip(&h) {
                for (v, &c) in hist.iter().enumerate() {
                    if c > 0 {
                        writeln!(dist_csv, "{step},{name},{v},{c}").unwrap();
                    }
                }
            }
        }
        if step % LONG_INTERVAL == 0 {
            snaps.write_frame(false, step, &food, &patches, &agents);
        }
        if step % AGENT_DUMP_INTERVAL == 0 {
            let list = |v: &[f32]| v.iter().map(|x| format!("{x:.2}")).collect::<Vec<_>>().join(",");
            let soil32: Vec<f32> = food.soil.iter().map(|&x| x as f32).collect();
            let res32: Vec<f32> = food.res.iter().map(|&x| x as f32).collect();
            writeln!(soil_jsonl, "{{\"step\":{step},\"soil\":[{}],\"plant\":[{}]}}", list(&soil32), list(&res32)).unwrap();
            for a in &agents {
                let k = &a.body.kinds;
                let b = &a.body;
                write!(agents_csv, "{step},{:.2},{},{},{},{},{},{},{:.2},{},{:.3},{},{:.2},{:.2},{:.2},{},{},{},{},{:.2},{:.2},{:.2},{},{},{},{:.1}",
                    b.mass, a.born_size, k[HARD], k[MUSCLE], k[SENSOR], k[DIGESTIVE], b.bite(), b.shell(), b.open_lines(), b.speed(), a.age, a.energy, a.plant, a.meat, a.lineage,
                    place_name(patches.place[a.here(g)]), place_name(a.born_place), b.bite_any(), b.shell_side(NORTH), b.shell_side(SOUTH), 0.5 * (b.shell_side(EAST) + b.shell_side(WEST)),
                    a.foot_n(g), b.extent[0], b.extent[1], terrain.height[a.here(g)]).unwrap();
                write!(agents_csv, ",{:.3},{},{:.3},{:.3},{}", a.fat, b.size, b.density, b.digest, b.side).unwrap();
                writeln!(agents_csv).unwrap();
            }
        }
        if step >= CLIP_START && step < CLIP_START + CLIP_LEN {
            snaps.write_frame(true, step, &food, &patches, &agents);
        }

        if step % LOG_INTERVAL == 0 || agents.is_empty() {
            let now = std::time::Instant::now();
            let sps = LOG_INTERVAL as f64 / (now - last_time).as_secs_f64();
            last_time = now;
            let pop = agents.len().max(1) as f32;
            let mean_energy = (agents.iter().map(|a| a.energy).sum::<f64>() / pop as f64) as f32;
            let mean_res = (food.res.iter().sum::<f64>() / (w * h) as f64) as f32;
            let mean_genes = agents.iter().map(|a| a.body.n_genes as f32).sum::<f32>() / pop;
            let total_actions = actions.iter().sum::<u64>().max(1) as f64;
            write!(
                log,
                "{step},{},{mean_energy:.3},{mean_res:.3},{mean_genes:.2},{births},{},{},{},{},{},{plant_intake:.1},{:.1}",
                agents.len(),
                deaths[0],
                deaths[1],
                cc.kills,
                deaths[3],
                cc.cells_broken,
                cc.meat_intake
            )
            .unwrap();
            for a in actions {
                write!(log, ",{:.3}", a as f64 / total_actions).unwrap();
            }
            write!(log, ",{sps:.0}").unwrap();
            let (m, s) = mean_std(agents.iter().map(|a| a.body.mass as f32));
            write!(log, ",{m:.2},{s:.2}").unwrap();
            for k in [HARD, MUSCLE, SENSOR, DIGESTIVE] {
                let (m, s) = mean_std(agents.iter().map(|a| a.body.kinds[k] as f32));
                write!(log, ",{m:.2},{s:.2}").unwrap();
            }
            let (m, s) = mean_std(agents.iter().map(|a| a.body.bite() as f32));
            write!(log, ",{m:.2},{s:.2}").unwrap();
            let (m, s) = mean_std(agents.iter().map(|a| a.body.speed()));
            write!(log, ",{m:.3},{s:.3}").unwrap();
            let mut counts: HashMap<(u8, &[u8; CELLS]), usize> = HashMap::new();
            for a in &agents {
                *counts.entry((a.body.side, &a.body.cells)).or_insert(0) += 1;
            }
            let top = counts.values().max().copied().unwrap_or(0) as f32 / pop;
            write!(log, ",{},{top:.3}", counts.len()).unwrap();
            let mut diet = [0usize; 4];
            for a in &agents {
                diet[a.diet_class()] += 1;
            }
            for d in diet {
                write!(log, ",{:.3}", d as f32 / pop).unwrap();
            }
            let mut carriers: HashMap<u32, usize> = HashMap::new();
            for a in &agents {
                *carriers.entry(a.lineage).or_default() += 1;
            }
            let top_lineage = lineages.keys().map(|id| carriers.get(id).copied().unwrap_or(0)).max().unwrap_or(0) as f32 / pop;
            let no_lineage = agents.iter().filter(|a| !lineages.contains_key(&a.lineage)).count() as f32 / pop;
            let sensor_agents = agents.iter().filter(|a| a.body.kinds[SENSOR] > 0).count() as f32 / pop;
            let (_, res_std) = mean_std(food.res.iter().map(|&r| r as f32));
            let res_above_half = food.res.iter().filter(|&&r| r > 0.5 * cap as f64).count() as f32 / (w * h) as f32;
            write!(log, ",{births_with_neighbor},{sexual_births},{},{top_lineage:.3},{no_lineage:.3},{sensor_agents:.3},{sense_decisions},{:.3},{res_std:.3},{res_above_half:.3},{:.2},{develops}",
                lineages.len(), if sense_decisions > 0 { sense_used as f64 / sense_decisions as f64 } else { 0.0 }, regrowth / LOG_INTERVAL as f64).unwrap();
            // Deaths by damage in this window: mean age, share before YOUNG. Energy per broken
            // cell. Agents that got most of their food from other bodies. And shape: mean shell
            // hardness, open lines, full squares, damaged bodies, bodies with a bite.
            let kills = cc.kills.max(1) as f64;
            let meat_majority = agents.iter().filter(|a| a.meat > a.plant && a.meat > 0.0).count() as f32 / pop;
            let shell_mean = agents.iter().map(|a| a.body.shell()).sum::<f32>() / pop;
            let open_mean = agents.iter().map(|a| a.body.open_lines() as f32).sum::<f32>() / pop;
            let full = agents.iter().filter(|a| a.body.size as usize == a.body.s() * a.body.s()).count() as f32 / pop;
            let damaged = agents.iter().filter(|a| a.body.size < a.born_size).count() as f32 / pop;
            let biters = agents.iter().filter(|a| a.body.bite() > 0).count() as f32 / pop;
            write!(log, ",{:.0},{:.3},{:.3},{meat_majority:.3},{},{shell_mean:.2},{open_mean:.2},{full:.3},{damaged:.3},{biters:.3}",
                cc.prey_age as f64 / kills, cc.meat_intake as f64 / cc.cells_broken.max(1) as f64, cc.kills_young as f64 / kills, cc.contacts).unwrap();
            // Size distribution (quantiles of mass), space (cells covered, share of the world
            // covered), regrowth lost to the cap, and plant intake per digestive cell per step.
            let mut masses: Vec<f32> = agents.iter().map(|a| a.body.mass).collect();
            masses.sort_by(f32::total_cmp);
            let q = |f: f32| masses.get(((masses.len() - 1) as f32 * f) as usize).copied().unwrap_or(0.0);
            // Space: sub-cells held (occupied_cells) and their share of the world (cover), and
            // per place the sub-cells held there over the sub-cells of the place.
            let covered = occ.crowd.iter().map(|&c| c as usize).sum::<usize>();
            let mut place_cells = [0usize; N_PLACES + 1];
            let mut place_held = [0usize; N_PLACES + 1];
            for (c, &p) in patches.place.iter().enumerate() {
                place_cells[p as usize] += SUB_CELLS;
                place_held[p as usize] += occ.crowd[c] as usize;
            }
            let guts = agents.iter().map(|a| a.body.kinds[DIGESTIVE] as f64).sum::<f64>().max(1.0);
            // Crossers: agents standing in a kind of place other than the one they were born in
            // (both a patch; a body beyond every patch is on its way). Then the same measures per place.
            let place_of = |a: &Agent| patches.place[a.here(g)];
            let crossers = agents.iter().filter(|a| { let p = place_of(a); p != NO_PLACE && a.born_place != NO_PLACE && p != a.born_place }).count() as f32 / pop;
            let pop_none = agents.iter().filter(|a| place_of(a) == NO_PLACE).count();
            write!(log, ",{:.1},{:.1},{:.1},{:.1},{covered},{:.3},{:.2},{:.4},{crossers:.3},{pop_none}", q(0.1), q(0.5), q(0.9), masses.last().copied().unwrap_or(0.0),
                covered as f32 / (g.sw * g.sh) as f32, wasted / LOG_INTERVAL as f64, plant_intake as f64 / LOG_INTERVAL as f64 / guts).unwrap();
            // Facing and space: blocked moves and shoves per forward action, blocked turns per
            // turn action, births without room per birth; the footprint and extent; the front.
            let tried = moves_tried.max(1) as f64;
            let turns = (actions[2] + actions[3]).max(1) as f64;
            let mean = |f: &dyn Fn(&Agent) -> f32| agents.iter().map(|a| f(a)).sum::<f32>() / pop;
            write!(log, ",{:.3},{:.3},{:.3},{:.3},{:.2},{:.2},{:.2},{:.2},{:.3},{:.2},{:.2},{:.2}",
                blocked as f64 / tried, shoves as f64 / tried, turns_blocked as f64 / turns, births_no_room as f64 / (births + births_no_room).max(1) as f64,
                mean(&|a| a.foot_n(g) as f32), mean(&|a| a.body.extent[0] as f32), mean(&|a| a.body.extent[1] as f32),
                mean(&|a| a.body.bite_any() as f32), mean(&|a| (a.body.bite_any() > 0) as u8 as f32),
                mean(&|a| a.body.shell_side(NORTH)), mean(&|a| a.body.shell_side(SOUTH)), mean(&|a| 0.5 * (a.body.shell_side(EAST) + a.body.shell_side(WEST)))).unwrap();
            // The cost law: pushes per forward action and the energy paid for moving per body per step.
            // Matter: dead matter laid per step and the dead matter lying uneaten now.
            let carrion_stock = food.carrion.iter().map(|&c| c as f64).sum::<f64>();
            let mut carrion_at = [0.0f64; N_PLACES + 1];
            for (c, &p) in patches.place.iter().enumerate() {
                carrion_at[p as usize] += food.carrion[c] as f64;
            }
            // The closed cycle: matter in the soil, the total (soil, plants, dead matter, bodies:
            // energy and cells), regrowth lost for want of soil, dead matter rotted into the
            // soil and what bodies returned to it, per step.
            let soil_stock = food.soil.iter().sum::<f64>();
            let mut soil_at = [0.0f64; N_PLACES + 1];
            let mut cells_at = [0usize; N_PLACES + 1];
            for (c, &p) in patches.place.iter().enumerate() {
                soil_at[p as usize] += food.soil[c];
                cells_at[p as usize] += 1;
            }
            let in_bodies = agents.iter().map(|a| a.energy.max(0.0) as f64 + a.fat as f64 + cell_energy as f64 * a.body.mass as f64).sum::<f64>();
            // The weight law: cells per body, and the density's mean and spread.
            let size_mean = agents.iter().map(|a| a.body.size as f32).sum::<f32>() / pop;
            let (density_mean, density_std) = mean_std(agents.iter().map(|a| a.body.density));
            // The digestion law: the axis's mean and spread, and the share of bodies on the flesh side.
            let (digest_mean, digest_std) = mean_std(agents.iter().map(|a| a.body.digest));
            let flesh_guts = agents.iter().filter(|a| a.body.digest > 0.5).count() as f32 / pop;
            // The flesh law: fat per body, fat in all bodies, what a cell of a body would yield
            // to its eater (mean over bodies), and what eaters gained per cell broken.
            let fat_stock = agents.iter().map(|a| a.fat as f64).sum::<f64>();
            let fat_mean = fat_stock / pop as f64;
            let worth = (agents.iter().filter(|a| a.body.size > 0).map(|a| (a.energy.max(0.0) + a.fat + (cell_energy * a.body.mass) as f64) / a.body.size as f64).sum::<f64>() / pop as f64) as f32;
            let kill_gain = cc.kill_gain / cc.cells_broken.max(1) as f32;
            let matter = soil_stock + food.res.iter().map(|&r| r as f64).sum::<f64>() + in_bodies + air;
            // The flow: soil moved per step, cells with a step of sun's worth of soil (0.01) and
            // with a full plant's worth (the cap).
            let soil_cells = food.soil.iter().filter(|&&s| s >= RES_GROWTH as f64).count() as f32 / (w * h) as f32;
            let deep = food.soil.iter().filter(|&&s| s >= cap as f64).count() as f32 / (w * h) as f32;
            // The canopy: sun moved to taller columns per step, cells standing at TREE or more
            // and the matter in them, the tallest column, and the intake taken from tree cells.
            // A tree is a cell whose standing plant (the column less the dead and the fruit lying
            // on it) is TREE or more; a pile of fruit is not a tree.
            let plant_of = |c: usize| (food.res[c] - food.carrion[c] - food.fruit[c]) as f32;
            let trees = (0..w * h).filter(|&c| plant_of(c) >= TREE).count();
            let tree_res = (0..w * h).filter(|&c| plant_of(c) >= TREE).map(|c| plant_of(c) as f64).sum::<f64>();
            let res_max = food.res.iter().copied().fold(0.0f64, f64::max) as f32;
            // The spill: fruit fallen per step, lying now, and eaten per step; the mutation law:
            // the share of the children born as clones and the mean mutations per child.
            let fruit_stock = food.fruit.iter().map(|&f| f as f64).sum::<f64>();
            if cloud.is_some() {
                let m = cloud_w.iter().sum::<f32>() / (w * h) as f32;
                cloud_std = (cloud_w.iter().map(|&x| (x - m) * (x - m)).sum::<f32>() / (w * h) as f32).sqrt();
            }
            let children_n = children.max(1) as f64;
            write!(log, ",{:.3},{:.5},{:.2},{:.4},{:.2},{soil_stock:.1},{matter:.1},{:.3},{:.4},{:.3},{:.3},{soil_cells:.3},{deep:.3},{air:.1},{:.3},{:.3},{trees},{tree_res:.1},{res_max:.2},{:.3},{:.3},{fruit_stock:.1},{:.3},{:.3},{:.2},{fat_mean:.4},{fat_stock:.1},{worth:.4},{kill_gain:.4},{size_mean:.2},{density_mean:.3},{density_std:.3},{:.4},{cloud_std:.4},{digest_mean:.3},{digest_std:.3},{flesh_guts:.3},{:.4}", pushes as f64 / tried, move_spent / LOG_INTERVAL as f64 / pop as f64, shaded / LOG_INTERVAL as f64,
                cc.dead / LOG_INTERVAL as f64, carrion_stock, barren / LOG_INTERVAL as f64, rot / LOG_INTERVAL as f64, spent / LOG_INTERVAL as f64, flowed / LOG_INTERVAL as f64, rained / LOG_INTERVAL as f64,
                shade_moved / LOG_INTERVAL as f64, tree_eaten / LOG_INTERVAL as f64, fruit_fallen / LOG_INTERVAL as f64, fruit_eaten / LOG_INTERVAL as f64, clones as f64 / children_n, mutations as f64 / children_n, sun_acc / LOG_INTERVAL as f64, cc.dung / LOG_INTERVAL as f64).unwrap();
            // The side of the grid (#28) and the distribution of size in cells (the issue's judge).
            let (side_mean, side_std) = mean_std(agents.iter().map(|a| a.body.side as f32));
            let mut sizes: Vec<u16> = agents.iter().map(|a| a.body.size).collect();
            sizes.sort_unstable();
            let sq = |f: f32| sizes.get(((sizes.len().max(1) - 1) as f32 * f) as usize).copied().unwrap_or(0);
            // The store: fat burned and fat breathed per step, and the bodies living on their fat.
            let on_fat = agents.iter().filter(|a| a.energy <= 0.0).count() as f32 / pop;
            let decisions = actions.iter().sum::<u64>().max(1) as f64;
            writeln!(log, ",{side_mean:.2},{side_std:.2},{},{},{},{},{:.4},{:.4},{on_fat:.4},{:.4},{:.4}", sq(0.1), sq(0.5), sq(0.9), sizes.last().copied().unwrap_or(0), fat_spent / LOG_INTERVAL as f64, fat_over / LOG_INTERVAL as f64, breed_decisions as f64 / decisions, breed_denied as f64 / breed_decisions.max(1) as f64).unwrap();
            sun_acc = 0.0;
            for p in 0..=N_PLACES as u8 {
                if !uniform && p < NO_PLACE && p as usize >= sigmas.len() {
                    continue;
                }
                let here: Vec<&Agent> = agents.iter().filter(|a| place_of(a) == p).collect();
                let n = here.len().max(1) as f32;
                let mean = |f: &dyn Fn(&Agent) -> f32| here.iter().map(|a| f(a)).sum::<f32>() / n;
                let present: std::collections::HashSet<u32> = here.iter().map(|a| a.lineage).filter(|l| lineages.contains_key(l)).collect();
                let movers = here.iter().filter(|a| a.born_place != NO_PLACE && a.born_place != p).count();
                let trees_here = patches.place.iter().enumerate().filter(|&(c, &q)| q == p && plant_of(c) >= TREE).count();
                writeln!(places_csv, "{step},{},{},{:.2},{:.2},{:.2},{:.2},{:.2},{:.2},{:.2},{:.3},{:.3},{:.1},{:.1},{},{movers},{:.2},{:.2},{:.2},{:.4},{:.2},{:.1},{:.4},{:.4},{},{:.4},{trees_here},{:.4},{:.1}", place_name(p), here.len(),
                    mean(&|a| a.body.mass as f32), mean(&|a| a.body.kinds[HARD] as f32), mean(&|a| a.body.kinds[MUSCLE] as f32), mean(&|a| a.body.kinds[SENSOR] as f32),
                    mean(&|a| a.body.kinds[DIGESTIVE] as f32), mean(&|a| a.body.bite() as f32), mean(&|a| a.body.shell()), mean(&|a| (a.body.bite() > 0) as u8 as f32),
                    place_held[p as usize] as f32 / place_cells[p as usize].max(1) as f32, plant_at[p as usize], cc.meat_at[p as usize], present.len(),
                    mean(&|a| a.foot_n(g) as f32), mean(&|a| a.body.shell_side(NORTH)), mean(&|a| a.body.shell_side(SOUTH)),
                    cc.dead_at[p as usize] / LOG_INTERVAL as f64, carrion_at[p as usize], soil_at[p as usize], barren_at[p as usize] / LOG_INTERVAL as f64,
                    regrowth_at[p as usize] / LOG_INTERVAL as f64, cells_at[p as usize], rain_at[p as usize] / LOG_INTERVAL as f64,
                    fruit_at[p as usize] / LOG_INTERVAL as f64, fruit_eaten_at[p as usize]).unwrap();
            }
            plant_at = [0.0; N_PLACES + 1];
            cc = Counters::default();
            births = 0;
            sexual_births = 0;
            births_with_neighbor = 0;
            births_no_room = 0;
            deaths = [0; 4];
            plant_intake = 0.0;
            actions = [0; N_OUT];
            moves_tried = 0;
            blocked = 0;
            shoves = 0;
            pushes = 0;
            move_spent = 0.0;
            turns_blocked = 0;
            sense_decisions = 0;
            sense_used = 0;
            regrowth = 0.0;
            wasted = 0.0;
            shaded = 0.0;
            barren = 0.0;
            barren_at = [0.0; N_PLACES + 1];
            regrowth_at = [0.0; N_PLACES + 1];
            rot = 0.0;
            spent = 0.0;
            fat_spent = 0.0;
            fat_over = 0.0;
            breed_decisions = 0;
            breed_denied = 0;
            flowed = 0.0;
            rained = 0.0;
            rain_at = [0.0; N_PLACES + 1];
            shade_moved = 0.0;
            tree_eaten = 0.0;
            fruit_fallen = 0.0;
            fruit_at = [0.0; N_PLACES + 1];
            fruit_eaten = 0.0;
            fruit_eaten_at = [0.0; N_PLACES + 1];
            children = 0;
            mutations = 0;
            clones = 0;
            develops = 0;
            if agents.is_empty() {
                eprintln!("extinct at step {step}");
                break;
            }
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn rotation_is_a_bijection_and_turns_the_front() {
        for f in DIRS {
            for s in SIDE_MIN..=SIDE_MAX {
                for i in 0..s * s {
                    assert_eq!(to_body(to_world(i, f, s), f, s), i);
                }
            }
        }
        // A tooth: a hard tip in the front row with muscle behind it, in column 2.
        let mut cells = [0u8; CELLS];
        cells[2] = HARD as u8;
        cells[SIDE + 2] = MUSCLE as u8;
        cells[2 * SIDE + 2] = MUSCLE as u8;
        let b = Body::new(cells, SIDE, [0.0; N_POLICY], 0, 1.0, false);
        assert_eq!(b.bite(), 2);
        assert_eq!(b.tips[NORTH][2].hardness, HARDNESS);
        // Facing east, the tooth is on the world's east side, in row 2 (the body's left is north).
        let w = rotate(&cells, EAST, SIDE);
        let t = tips_of(&w, SIDE);
        assert_eq!(t[EAST][2].hardness, HARDNESS);
        assert_eq!(t[EAST][2].force, 2);
        assert_eq!(t[NORTH][2].hardness, 0);
        // Facing south: on the south side, column 5 (mirrored).
        let t = tips_of(&rotate(&cells, SOUTH, SIDE), SIDE);
        assert_eq!(t[SOUTH][5].hardness, HARDNESS);
        // Facing west: the west side, row 5.
        let t = tips_of(&rotate(&cells, WEST, SIDE), SIDE);
        assert_eq!(t[WEST][5].hardness, HARDNESS);
        // The tooth spans three rows along the facing and one across.
        assert_eq!(b.extent, [3, 1]);
        // The face of the hard tip, seen from the front: one hard cell behind it; the muscle
        // behind the tip is soft (1) and the tip's face from the side is hard too.
        assert_eq!(face_hardness(&cells, 2, SOUTH, SIDE), HARDNESS);
        assert_eq!(face_hardness(&cells, SIDE + 2, SOUTH, SIDE), 1);
        cells[SIDE + 2] = HARD as u8;
        assert_eq!(face_hardness(&cells, 2, SOUTH, SIDE), 2 * HARDNESS);
        assert_eq!(face_hardness(&cells, SIDE + 2, NORTH, SIDE), 2 * HARDNESS);
    }

    fn agent_with(cells: [u8; CELLS], x: usize, y: usize, facing: usize) -> Agent {
        let mut a = Agent {
            id: 0, lineage: 0, x, y, energy: 1.0, age: 0, plant: 0.0, meat: 0.0, fat: 0.0, born_size: 0, breed_now: false, born_place: NO_PLACE, alive: true,
            genome: Vec::new(), keys: Vec::new(), gene_ids: Vec::new(), body: Body::new(cells, SIDE, [0.0; N_POLICY], 0, 1.0, false), facing: facing as u8,
            wcells: [0; CELLS], tips: [[Tip::default(); SIDE_MAX]; 4], filled: [0; CELLS], n_filled: 0, bbox: [0; 4],
        };
        a.reframe();
        a
    }

    #[test]
    fn bodies_hold_their_own_sub_cells_and_lie_over_world_cells() {
        let g = Grid::new(8, 8);
        // A three-cell corner body (cells (0,0), (0,1), (1,0)) anchored at sub-cell (6, 6) facing north.
        let mut cells = [0u8; CELLS];
        cells[0] = DIGESTIVE as u8;
        cells[1] = DIGESTIVE as u8;
        cells[SIDE] = HARD as u8;
        let a = agent_with(cells, 6, 6, NORTH);
        assert_eq!(a.n_filled, 3);
        assert_eq!(a.bbox, [0, 1, 0, 1]);
        // It lies over world cells (1,1), (1,2)... no: sub-cells (6,6), (7,6), (6,7) are all in world cell (1,1).
        assert_eq!(a.foot_n(g), 1);
        let under = a.under(g, NORTH, 0);
        assert_eq!((under.n, under.c[0]), (1, g.idx(1, 1)));
        // One sub-cell east: (7,6), (8,6), (7,7): world cells (1,1) and (2,1).
        let b = agent_with(cells, 7, 6, NORTH);
        assert_eq!(b.foot_n(g), 2);
        assert_eq!(b.under(g, NORTH, 0).n, 2);
        // Moved one world cell east, the box lies over (2,1) and (3,1); the new cell is (3,1).
        let ahead = b.under(g, EAST, SUB);
        assert!(ahead.contains(g.idx(2, 1)) && ahead.contains(g.idx(3, 1)) && ahead.n == 2);
        // Occupancy: claim, fits, release.
        let mut occ = Occ { sub: vec![u32::MAX; g.sw * g.sh], crowd: vec![0; g.cells()] };
        occ.claim(g, &a, 0);
        assert_eq!(occ.crowd[g.idx(1, 1)], 3);
        assert_eq!(occ.sub[g.sidx(7, 6)], 0);
        assert!(a.fits(g, &occ.sub, 0, EAST, 1)); // its own cells do not block it
        assert!(!b.fits(g, &occ.sub, 1, NORTH, 0)); // another body cannot stand on it
        assert!(b.fits(g, &occ.sub, 1, EAST, 1)); // one sub-cell further east it can
        occ.release(g, &a);
        assert_eq!(occ.crowd[g.idx(1, 1)], 0);
        // The torus: a body at the far east edge wraps.
        let c = agent_with(cells, g.sw - 1, 0, NORTH);
        assert_eq!(c.sub_at(g, 1, NORTH, 0), (0, 0));
        assert_eq!(c.foot_n(g), 2);
    }

    #[test]
    fn a_dead_body_is_food_where_it_lies() {
        let g = Grid::new(8, 8);
        let place = vec![NO_PLACE; g.cells()];
        let mut food = Food::new(vec![0.0; g.cells()], vec![0.0; g.cells()], vec![0.0f64; g.cells()]);
        let mut c = Counters::default();
        // Three cells anchored at sub-cell (7, 4): sub-cells (7,4), (8,4) and (7,5), in world
        // cells (1,1), (2,1) and (1,1).
        let mut cells = [0u8; CELLS];
        cells[0] = DIGESTIVE as u8;
        cells[1] = DIGESTIVE as u8;
        cells[SIDE] = HARD as u8;
        let mut a = agent_with(cells, 7, 4, NORTH);
        a.energy = 0.3;
        lay_body(&a, g, &mut food, &place, 0.02, &mut c);
        // Each cell: 0.02 of matter and 0.1 of energy.
        assert!((food.res[g.idx(1, 1)] - 0.24).abs() < 1e-6);
        assert!((food.res[g.idx(2, 1)] - 0.12).abs() < 1e-6);
        assert!((c.dead - 0.36).abs() < 1e-6);
        assert_eq!(food.carrion[g.idx(1, 1)], food.res[g.idx(1, 1)]);
        // A body with no cells leaves its energy under its anchor; one with no energy leaves nothing.
        let mut b = agent_with([0u8; CELLS], 3, 3, NORTH);
        b.energy = 1.0;
        lay_body(&b, g, &mut food, &place, 0.02, &mut c);
        assert_eq!(food.res[g.idx(0, 0)], 1.0);
        b.energy = -0.5;
        lay_body(&b, g, &mut food, &place, 0.02, &mut c);
        assert_eq!(food.res[g.idx(0, 0)], 1.0);
        // A gut takes plant and dead matter in the cell's proportion.
        food.res[g.idx(0, 0)] = 2.0; // 1.0 of it dead
        let (plant, dead, fruit) = food.take(g.idx(0, 0), 0.5);
        assert!((plant - 0.25).abs() < 1e-6 && (dead - 0.25).abs() < 1e-6 && fruit == 0.0);
        assert!((food.res[g.idx(0, 0)] - 1.5).abs() < 1e-6 && (food.carrion[g.idx(0, 0)] - 0.75).abs() < 1e-6);
    }

    #[test]
    fn a_plant_grows_out_of_the_soil_and_the_dead_rot_into_it() {
        let mut food = Food::new(vec![0.0; 4], vec![0.0; 4], vec![0.05f64, 0.0, 1.0, 1.0]);
        let cap = 8.0;
        // Soil 0.05 under a sun of 0.1: the plant grows 0.05 and the other 0.05 of sun is barren.
        assert_eq!(food.regrow(0, 0.1, 0.0, false, cap, false), Regrown { added: 0.05, barren: 0.05, ..Default::default() });
        assert!((food.res[0] - 0.05).abs() < 1e-6 && food.soil[0] < 1e-9);
        // No soil: the whole sun is barren.
        assert_eq!(food.regrow(1, 0.1, 0.0, false, cap, false), Regrown { barren: 0.1, ..Default::default() });
        // A body on the cell: shaded, nothing moves.
        assert_eq!(food.regrow(2, 0.1, 0.0, true, cap, false), Regrown { shaded: 0.1, ..Default::default() });
        assert_eq!((food.res[2], food.soil[2]), (0.0, 1.0));
        // At the cap the sun is wasted and the soil stays.
        food.res[2] = cap as f64;
        assert_eq!(food.regrow(2, 0.1, 0.0, false, cap, false), Regrown { wasted: 0.1, ..Default::default() });
        // Dead matter rots by DECAY per step into the soil and leaves the food; the sun then
        // grows the plant out of the soil. The total on the cell is unchanged.
        food.res[3] = 2.0;
        food.carrion[3] = 2.0;
        let r = food.regrow(3, 0.1, 0.0, false, cap, false);
        assert!((r.rot - 0.02).abs() < 1e-6 && (r.added - 0.1).abs() < 1e-6);
        assert!((food.carrion[3] - 1.98).abs() < 1e-6 && (food.res[3] - 2.08).abs() < 1e-6 && (food.soil[3] - 0.92).abs() < 1e-6);
        assert!((food.res[3] as f64 + food.soil[3] - 3.0).abs() < 1e-6);
        // What a body spends falls to the soil.
        food.spend(1, 0.05);
        assert!((food.soil[1] - 0.05).abs() < 1e-6);
    }

    #[test]
    fn soil_runs_downhill_and_levels_where_it_pools() {
        let g = Grid::new(4, 1);
        let mut delta = vec![0.0f64; 4];
        // A slope: heights 3, 2, 1, 0 (the torus joins cell 3 back to cell 0, a wall of 3).
        // Soil on the top cell runs to the one cell below it (the other neighbors are higher or
        // itself): a share `rate` per step, capped at an eighth of the drop.
        let height = vec![3.0, 2.0, 1.0, 0.0];
        let mut food = Food::new(vec![0.0; 4], vec![0.0; 4], vec![1.0f64, 0.0, 0.0, 0.0]);
        let moved = food.flow(g, &height, 0.5, &mut delta);
        // The drop to cell 1 is 2 (surface 4 against 2), to cell 3 it is 4 (surface 0): 0.5 of
        // the soil split 1:2, 0.167 and 0.333, both under an eighth of their drop.
        assert!((moved - 0.5).abs() < 1e-6);
        assert!((food.soil[0] - 0.5).abs() < 1e-6 && (food.soil[1] - 1.0 / 6.0).abs() < 1e-6 && (food.soil[3] - 1.0 / 3.0).abs() < 1e-6);
        assert!((food.soil.iter().sum::<f64>() - 1.0).abs() < 1e-6);
        // Flat ground: soil piled on one cell spreads to its neighbors and levels; no cell gives
        // more than an eighth of the drop, so nothing overshoots.
        let flat = vec![0.0; 4];
        let mut food = Food::new(vec![0.0; 4], vec![0.0; 4], vec![8.0f64, 0.0, 0.0, 0.0]);
        for _ in 0..200 {
            food.flow(g, &flat, 1.0, &mut delta);
            let max = food.soil.iter().copied().fold(0.0f64, f64::max);
            assert!(food.soil.iter().all(|&s| s >= 0.0) && max <= 8.0);
        }
        assert!(food.soil.iter().all(|&s| (s - 2.0).abs() < 1e-3), "{:?}", food.soil);
        assert!((food.soil.iter().sum::<f64>() - 8.0).abs() < 1e-4);
        // A basin: heights 2, 0, 0, 2. Two of soil on one low cell levels over the two low cells
        // (1 each, surface 1) and none climbs the rims (surface 2).
        let basin = vec![2.0, 0.0, 0.0, 2.0];
        let mut food = Food::new(vec![0.0; 4], vec![0.0; 4], vec![0.0f64, 2.0, 0.0, 0.0]);
        for _ in 0..200 {
            food.flow(g, &basin, 1.0, &mut delta);
        }
        assert!((food.soil[1] - 1.0).abs() < 1e-3 && (food.soil[2] - 1.0).abs() < 1e-3 && food.soil[0] == 0.0 && food.soil[3] == 0.0, "{:?}", food.soil);
        // At a small rate the soil creeps: the share per step, whatever the drop.
        let mut food = Food::new(vec![0.0; 4], vec![0.0; 4], vec![1.0f64, 0.0, 0.0, 0.0]);
        let moved = food.flow(g, &height, 0.01, &mut delta);
        assert!((moved - 0.01).abs() < 1e-6);
    }

    #[test]
    fn the_air_rains_on_the_mountains_at_most_the_sun_per_step() {
        // Heights 0, 32, 64 at relief 64: the caps are 0, half the sun, the sun.
        let height = vec![0.0f32, 32.0, 64.0];
        let caps = Rain::High.caps(&height, 64.0);
        assert!((caps[0] - 0.0).abs() < 1e-9 && (caps[1] - 0.005).abs() < 1e-9 && (caps[2] - 0.01).abs() < 1e-9);
        assert!(Rain::Flat.caps(&height, 64.0).iter().all(|&c| (c - 0.01).abs() < 1e-9));
        assert!(Rain::Soil.caps(&height, 64.0).iter().all(|&c| c == 0.0));
        let total: f64 = caps.iter().map(|&c| c as f64).sum();
        let place = vec![0u8, 1, 2];
        let mut at = [0.0f64; N_PLACES + 1];
        // Plenty in the air: every cell gets its cap, and the rest stays in the air.
        let mut food = Food::new(vec![0.0; 3], vec![0.0; 3], vec![0.0f64; 3]);
        let mut air = 1.0f64;
        let fell = food.rain(&mut air, &caps, total, &place, &mut at);
        assert!((fell - 0.015).abs() < 1e-9 && (air - 0.985).abs() < 1e-9);
        assert!(food.soil[0] == 0.0 && (food.soil[1] - 0.005).abs() < 1e-9 && (food.soil[2] - 0.01).abs() < 1e-9);
        assert!((at[1] - 0.005).abs() < 1e-9 && (at[2] - 0.01).abs() < 1e-9);
        // Less in the air than the caps add up to: the same share of its cap for every cell, and the air is empty.
        let mut air = 0.003f64;
        let fell = food.rain(&mut air, &caps, total, &place, &mut at);
        assert!((fell - 0.003).abs() < 1e-9 && air == 0.0);
        assert!((food.soil[1] - 0.006).abs() < 1e-9 && (food.soil[2] - 0.012).abs() < 1e-9);
        // Nothing in the air: nothing falls.
        assert_eq!(food.rain(&mut air, &caps, total, &place, &mut at), 0.0);
    }

    #[test]
    fn the_tall_plant_takes_the_light() {
        let g = Grid::new(32, 32);
        let n = g.cells();
        let grow = vec![0.01f32; n];
        let mut light = vec![0.0f32; n];
        let mut claims = vec![0.0f32; n];
        let mut crown = vec![0.0f32; n];
        let crowd = vec![0u16; n];
        let bare = |mut res: Vec<f64>, put: &[(usize, usize, f64)]| {
            for &(x, y, h) in put {
                res[g.idx(x, y)] = h;
            }
            res
        };
        // A half-grown tree (4) alone on a bare lawn shades as far as it is tall, at half
        // strength (room 4 of 8): the ring at distance d (8d cells) gives (4 - (d - 1)) / 8 *
        // 4 / 8 of its sun each, so the tree gathers 0.01 * sum(8d * (5 - d) / 16, d = 1..4) =
        // 0.10 on top of its own sun: ten suns, never much more than it can grow by.
        let food = Food::new(bare(vec![0.0; n], &[(16, 16, 4.0)]), vec![0.0; n], vec![0.0f64; n]);
        let moved = food.shade(g, &grow, 1.0, 8.0, &crowd, false, &mut claims, &mut light, &mut crown);
        assert!((moved - 0.10).abs() < 1e-5, "{moved}");
        assert!((light[g.idx(16, 16)] + crown[g.idx(16, 16)] - 0.11).abs() < 1e-5);
        // The neighbor at distance 1 keeps three quarters of its sun, at distance 4 fifteen
        // sixteenths, past the reach all of it.
        assert!((light[g.idx(17, 16)] - 0.01 * (1.0 - 4.0 / 16.0)).abs() < 1e-7);
        assert!((light[g.idx(20, 16)] - 0.01 * (1.0 - 1.0 / 16.0)).abs() < 1e-7);
        assert!((light[g.idx(21, 16)] - 0.01).abs() < 1e-9);
        // The sun is moved, never made.
        assert!((light.iter().zip(&crown).map(|(&l, &c)| (l + c) as f64).sum::<f64>() - 0.01 * n as f64).abs() < 1e-4);
        // A full crown intercepts nothing: the tree at the cap is a standing larder.
        let food = Food::new(bare(vec![0.0; n], &[(16, 16, 8.0)]), vec![0.0; n], vec![0.0f64; n]);
        assert_eq!(food.shade(g, &grow, 1.0, 8.0, &crowd, false, &mut claims, &mut light, &mut crown), 0.0);
        assert!(light.iter().all(|&l| (l - 0.01).abs() < 1e-9));
        // Equal columns shade each other not at all (the start of a run: every cell at the cap).
        let food = Food::new(vec![8.0; n], vec![0.0; n], vec![0.0f64; n]);
        assert_eq!(food.shade(g, &grow, 1.0, 8.0, &crowd, false, &mut claims, &mut light, &mut crown), 0.0);
        // A column under a body claims nothing; its own sun can still be claimed.
        let food = Food::new(bare(vec![0.0; n], &[(16, 16, 4.0), (17, 16, 2.0)]), vec![0.0; n], vec![0.0f64; n]);
        let mut held = vec![0u16; n];
        held[g.idx(17, 16)] = 1;
        food.shade(g, &grow, 1.0, 8.0, &held, false, &mut claims, &mut light, &mut crown);
        // The held column at (17,16) takes nothing (its light stays 0.01 plus nothing), and
        // still loses to the taller free tree: share (4 - 2) / 8 * 4 / 8.
        assert!((light[g.idx(17, 16)] - 0.01 * (1.0 - 2.0 / 16.0)).abs() < 1e-7);
        // Two half trees with a bare cell between them split its sun evenly.
        let food = Food::new(bare(vec![0.0; n], &[(15, 16, 4.0), (17, 16, 4.0)]), vec![0.0; n], vec![0.0f64; n]);
        food.shade(g, &grow, 1.0, 8.0, &crowd, false, &mut claims, &mut light, &mut crown);
        assert!((light[g.idx(15, 16)] - light[g.idx(17, 16)]).abs() < 1e-6);
        assert!(light[g.idx(16, 16)] < 0.01);
        // Rate 0 is e020: nothing moves.
        let moved = food.shade(g, &grow, 0.0, 8.0, &crowd, false, &mut claims, &mut light, &mut crown);
        assert_eq!(moved, 0.0);
        assert!(light.iter().all(|&l| (l - 0.01).abs() < 1e-9));
    }

    #[test]
    fn a_full_crown_keeps_taking_the_light_and_drops_fruit_around_it() {
        let g = Grid::new(32, 32);
        let n = g.cells();
        let grow = vec![0.01f32; n];
        let mut light = vec![0.0f32; n];
        let mut crown = vec![0.0f32; n];
        let mut claims = vec![0.0f32; n];
        let crowd = vec![0u16; n];
        let t = g.idx(16, 16);
        let mut res = vec![0.0f64; n];
        res[t] = 8.0;
        // A full tree alone on a bare lawn, with the spill: it claims at the rate whatever its
        // height, so the ring at distance d (8d cells) gives (9 - d) / 8 of its sun each and
        // the tree gathers 0.01 * sum(d * (9 - d), d = 1..8) = 1.20: 120 suns, the whole reach.
        let mut food = Food::new(res.clone(), vec![0.0; n], vec![10.0f64; n]);
        let moved = food.shade(g, &grow, 1.0, 8.0, &crowd, true, &mut claims, &mut light, &mut crown);
        assert!((moved - 1.20).abs() < 1e-4, "{moved}");
        assert!((crown[t] - 1.20).abs() < 1e-4);
        assert!(light[g.idx(17, 16)].abs() < 1e-9, "the ring is dark");
        assert!((light[g.idx(24, 16)] - 0.01 * 7.0 / 8.0).abs() < 1e-7, "at the edge of the reach, an eighth");
        // The sun is moved, never made.
        assert!((light.iter().zip(&crown).map(|(&l, &c)| (l + c) as f64).sum::<f64>() - 0.01 * n as f64).abs() < 1e-4);
        // At the cap the tree cannot grow: its own sun and the crown's light become fruit,
        // out of its soil.
        let r = food.regrow(t, light[t], crown[t], false, 8.0, true);
        assert!((r.fruit - 1.21).abs() < 1e-4 && r.added == 0.0 && r.wasted == 0.0 && r.barren.abs() < 1e-6, "{r:?}");
        assert!((food.soil[t] - (10.0 - 1.21)).abs() < 1e-4);
        // The fruit falls on the ring of 8, as matter lying on the ground.
        let mut out = vec![0.0f32; n];
        out[t] = r.fruit;
        let fell = food.spill(g, &out, 1);
        assert!((fell - 1.21).abs() < 1e-5);
        for (dx, dy) in [(-1i32, -1i32), (0, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (0, 1), (1, 1)] {
            let c = g.idx((16 + dx) as usize, (16 + dy) as usize);
            assert!((food.res[c] - 1.21 / 8.0).abs() < 1e-6 && (food.fruit[c] - 1.21 / 8.0).abs() < 1e-6);
        }
        assert_eq!(food.res[t], 8.0);
        let matter = food.soil.iter().sum::<f64>() + food.res.iter().map(|&r| r as f64).sum::<f64>();
        assert!((matter - 10.0 * n as f64 - 8.0).abs() < 1e-3, "matter is conserved: {matter}");
        // A gut takes plant, dead matter and fruit in the cell's proportions.
        let c = g.idx(17, 16);
        food.res[c] = 1.21 / 8.0 * 2.0; // as much plant again as fruit
        let (plant, dead, fruit) = food.take(c, 0.1);
        assert!((plant - 0.05).abs() < 1e-6 && dead == 0.0 && (fruit - 0.05).abs() < 1e-6);
        // A column under a body claims too (the crown's light is above the body) and, unable
        // to grow, drops all of it as fruit; only its own sun falls in the body's shadow.
        let mut held = vec![0u16; n];
        held[t] = 3;
        let mut food = Food::new(res.clone(), vec![0.0; n], vec![10.0f64; n]);
        let moved = food.shade(g, &grow, 1.0, 8.0, &held, true, &mut claims, &mut light, &mut crown);
        assert!((moved - 1.20).abs() < 1e-4);
        let r = food.regrow(t, light[t], crown[t], true, 8.0, true);
        assert!((r.fruit - 1.20).abs() < 1e-4 && (r.shaded - 0.01).abs() < 1e-7 && r.added == 0.0, "{r:?}");
        // A half tree under a body: the same, its own growth stopped.
        let mut res4 = vec![0.0f64; n];
        res4[t] = 4.0;
        let mut food = Food::new(res4, vec![0.0; n], vec![10.0f64; n]);
        food.shade(g, &grow, 1.0, 8.0, &held, true, &mut claims, &mut light, &mut crown);
        let r = food.regrow(t, light[t], crown[t], true, 8.0, true);
        assert!(r.added == 0.0 && r.fruit > 0.0 && (r.fruit - crown[t]).abs() < 1e-6, "{r:?}");
        // And free, it grows by all of it (room 4) and drops nothing.
        let mut food = Food::new(food.res.clone(), vec![0.0; n], vec![10.0f64; n]);
        food.shade(g, &grow, 1.0, 8.0, &crowd, true, &mut claims, &mut light, &mut crown);
        let r = food.regrow(t, light[t], crown[t], false, 8.0, true);
        assert!(r.fruit == 0.0 && (r.added - (light[t] + crown[t])).abs() < 1e-6, "{r:?}");
        // Without soil the light is barren, as ever: nothing is made from nothing.
        let mut food = Food::new(res.clone(), vec![0.0; n], vec![0.0f64; n]);
        food.shade(g, &grow, 1.0, 8.0, &crowd, true, &mut claims, &mut light, &mut crown);
        let r = food.regrow(t, light[t], crown[t], false, 8.0, true);
        assert!(r.fruit == 0.0 && r.added == 0.0 && (r.barren - 1.21).abs() < 1e-4, "{r:?}");
        // Fruit rots into the soil like the dead.
        let mut food = Food::new(vec![1.0; n], vec![0.0; n], vec![0.0f64; n]);
        food.fruit[t] = 1.0;
        let r = food.regrow(t, 0.0, 0.0, false, 8.0, true);
        assert!((r.rot - DECAY).abs() < 1e-7 && (food.fruit[t] - (1.0 - DECAY as f64)).abs() < 1e-6 && (food.soil[t] - DECAY as f64).abs() < 1e-7);
    }

    #[test]
    fn a_gut_digests_by_its_axis_and_the_rest_is_dung() {
        // #32: the same kill, eaten by a flesh gut (d 1), a plant gut (d 0) and the middle: the
        // eater gains its flesh yield of the cell, the rest goes to the soil under it, and the
        // matter holds. Without the law every gut gains all of it (e026).
        for (law, d, yield_) in [(1, 1.0, 1.0), (1, 0.0, DIGEST_FLOOR), (1, 0.5, (1.0 + DIGEST_FLOOR) / 2.0), (0, 0.0, 1.0), (2, 0.0, DIGEST_FLOOR), (2, 0.5, 1.0 - (1.0 - DIGEST_FLOOR) * 0.5f32.sqrt())] {
            let g = Grid::new(8, 8);
            let place = vec![NO_PLACE; g.cells()];
            let mut c = Counters::default();
            let mut food = Food::new(vec![0.0; g.cells()], vec![0.0; g.cells()], vec![0.0f64; g.cells()]);
            let mut tooth = [0u8; CELLS];
            tooth[2] = HARD as u8;
            tooth[SIDE + 2] = MUSCLE as u8;
            tooth[2 * SIDE + 2] = MUSCLE as u8;
            tooth[3 * SIDE + 2] = DIGESTIVE as u8;
            let mut hunter = agent_with(tooth, 0, 8, EAST);
            hunter.body.digest = d;
            let mut soft = [0u8; CELLS];
            soft[0] = DIGESTIVE as u8;
            soft[1] = DIGESTIVE as u8;
            let mut prey = agent_with(soft, 8, 10, NORTH);
            prey.fat = 0.4;
            let mut agents = vec![hunter, prey];
            let mut occ = Occ { sub: vec![u32::MAX; g.sw * g.sh], crowd: vec![0; g.cells()] };
            occ.claim(g, &agents[0], 0);
            occ.claim(g, &agents[1], 1);
            let before = agents[0].energy + agents[1].energy + agents[1].fat + (CELL_ENERGY * 2.0) as f64;
            push(&mut agents, 0, EAST, g, &mut occ, &place, &mut food, CELL_ENERGY, law, &mut c);
            let taken = (CELL_ENERGY + 0.5 + 0.2) as f64;
            let gain = taken * yield_ as f64;
            assert!((agents[0].energy - (1.0 + gain)).abs() < 1e-6, "law {law} d {d}: {}", agents[0].energy);
            assert!((food.soil.iter().sum::<f64>() - (taken - gain)).abs() < 1e-6, "law {law} d {d}: soil");
            assert!((c.dung - (taken - gain)).abs() < 1e-6);
            let after = agents[0].energy + agents[1].energy + agents[1].fat + CELL_ENERGY as f64 + food.soil.iter().sum::<f64>();
            assert!((after - before).abs() < 1e-6, "law {law} d {d}: {before} {after}");
        }
        // The yields: the far ends get all of one food and half of the other, the middle three quarters of both.
        let mut b = Body::new([0; CELLS], SIDE, [0.0; N_POLICY], 0, 1.0, true);
        for (d, plant, flesh) in [(0.0, 1.0, 0.5), (1.0, 0.5, 1.0), (0.5, 0.75, 0.75)] {
            b.digest = d;
            assert_eq!(b.yields(1), (plant, flesh));
            assert_eq!(b.yields(0), (1.0, 1.0));
        }
        // The sharp curve: the same ends, the middle at 1 - sqrt(1/2) / 2 (0.65) of both.
        for (d, plant, flesh) in [(0.0, 1.0, 0.5), (1.0, 0.5, 1.0), (0.5, 1.0 - 0.5 * 0.5f64.sqrt(), 1.0 - 0.5 * 0.5f64.sqrt())] {
            b.digest = d;
            let (p, f) = b.yields(2);
            assert!((p - plant).abs() < 1e-9 && (f - flesh).abs() < 1e-9, "sharp d {d}: {p} {f}");
        }
    }

    #[test]
    fn the_flesh_is_worth_what_the_body_lived_through() {
        // The fat a body fixed from its upkeep goes with its cells: a broken cell yields its
        // share of the fat with the matter and the energy, and a dead body lays all of it.
        let g = Grid::new(8, 8);
        let place = vec![NO_PLACE; g.cells()];
        let mut c = Counters::default();
        let mut food = Food::new(vec![0.0; g.cells()], vec![0.0; g.cells()], vec![0.0f64; g.cells()]);
        let mut tooth = [0u8; CELLS];
        tooth[2] = HARD as u8;
        tooth[SIDE + 2] = MUSCLE as u8;
        tooth[2 * SIDE + 2] = MUSCLE as u8;
        tooth[3 * SIDE + 2] = DIGESTIVE as u8; // a hunter with a gut
        let hunter = agent_with(tooth, 0, 8, EAST);
        let mut soft = [0u8; CELLS];
        soft[0] = DIGESTIVE as u8;
        soft[1] = DIGESTIVE as u8;
        let mut prey = agent_with(soft, 8, 10, NORTH);
        prey.fat = 0.4; // two cells: 0.2 each
        let mut agents = vec![hunter, prey];
        let mut occ = Occ { sub: vec![u32::MAX; g.sw * g.sh], crowd: vec![0; g.cells()] };
        occ.claim(g, &agents[0], 0);
        occ.claim(g, &agents[1], 1);
        push(&mut agents, 0, EAST, g, &mut occ, &place, &mut food, CELL_ENERGY, 0, &mut c);
        // The cell's matter, half the prey's energy (1.0) and half its fat.
        let gain = CELL_ENERGY + 0.5 + 0.2;
        assert!((agents[0].energy - (1.0 + gain) as f64).abs() < 1e-6 && (agents[0].meat - gain).abs() < 1e-6);
        assert!((c.kill_gain - gain).abs() < 1e-6);
        assert!((agents[1].fat - 0.2).abs() < 1e-6 && (agents[1].energy - 0.5).abs() < 1e-6);
        assert_eq!(food.res.iter().sum::<f64>(), 0.0);
        // The prey dies where it stands: its last cell, its energy and its fat lie on the ground.
        occ.release(g, &agents[1]);
        lay_body(&agents[1], g, &mut food, &place, CELL_ENERGY, &mut c);
        assert!((food.res.iter().sum::<f64>() - (CELL_ENERGY + 0.5 + 0.2) as f64).abs() < 1e-6);
        assert!((c.dead - (CELL_ENERGY as f64 + 0.7)).abs() < 1e-6);
    }

    #[test]
    fn a_block_weighs_by_its_kind_and_density() {
        // The weight law (#25): a hard block weighs 2, a sensor 1/2, the rest 1, times the
        // body's density; the mass is what the body is made of, moves with, and is worth.
        let mut cells = [0u8; CELLS];
        cells[2] = HARD as u8;
        cells[SIDE + 2] = MUSCLE as u8;
        cells[2 * SIDE + 2] = SENSOR as u8;
        cells[3 * SIDE + 2] = DIGESTIVE as u8;
        let plain = Body::new(cells, SIDE, [0.0; N_POLICY], 0, 1.0, false);
        assert_eq!((plain.size, plain.mass), (4, 4.0));
        let kind = Body::new(cells, SIDE, [0.0; N_POLICY], 0, 1.0, true);
        assert_eq!((kind.size, kind.mass), (4, 4.5));
        assert!((kind.speed() - 1.0 / 4.5).abs() < 1e-6);
        let dense = Body::new(cells, SIDE, [0.0; N_POLICY], 0, 2.0, true);
        assert_eq!(dense.mass, 9.0);
        assert_eq!(dense.block_mass(HARD as u8), 4.0);
        assert_eq!(dense.block_mass(0), 0.0);
        // A push against a dense soft body: its face is 1 x 2 = 2, and a force of 2 does not
        // break it; a light one (1/2) breaks under a single muscle.
        let g = Grid::new(8, 8);
        let place = vec![NO_PLACE; g.cells()];
        let mut tooth = [0u8; CELLS];
        tooth[2] = HARD as u8;
        tooth[SIDE + 2] = MUSCLE as u8;
        tooth[2 * SIDE + 2] = MUSCLE as u8;
        let mut soft = [0u8; CELLS];
        soft[0] = DIGESTIVE as u8;
        soft[1] = DIGESTIVE as u8;
        for (density, broken) in [(2.0, 0), (1.0, 1), (0.5, 1)] {
            let hunter = agent_with(tooth, 0, 8, EAST);
            let mut prey = agent_with(soft, 8, 10, NORTH);
            prey.body = Body::new(soft, SIDE, [0.0; N_POLICY], 0, density, true);
            prey.reframe();
            let mut agents = vec![hunter, prey];
            let mut occ = Occ { sub: vec![u32::MAX; g.sw * g.sh], crowd: vec![0; g.cells()] };
            occ.claim(g, &agents[0], 0);
            occ.claim(g, &agents[1], 1);
            let mut c = Counters::default();
            let mut food = Food::new(vec![0.0; g.cells()], vec![0.0; g.cells()], vec![0.0f64; g.cells()]);
            push(&mut agents, 0, EAST, g, &mut occ, &place, &mut food, CELL_ENERGY, 0, &mut c);
            assert_eq!(c.cells_broken, broken, "density {density}");
            if broken == 1 {
                // The broken block lies on the ground as the matter it was made of (its mass
                // times the cell energy) plus half the prey's energy.
                let matter = food.res.iter().sum::<f64>();
                assert!((matter - (CELL_ENERGY * density + 0.5) as f64).abs() < 1e-6, "density {density}: {matter}");
            }
        }
        // A muscle of one breaks the light body's face (1/2) but not the plain one (1).
        let mut weak = [0u8; CELLS];
        weak[2] = HARD as u8;
        weak[SIDE + 2] = MUSCLE as u8;
        for (density, broken) in [(1.0, 0), (0.5, 1)] {
            let hunter = agent_with(weak, 0, 8, EAST);
            let mut prey = agent_with(soft, 8, 10, NORTH);
            prey.body = Body::new(soft, SIDE, [0.0; N_POLICY], 0, density, true);
            prey.reframe();
            let mut agents = vec![hunter, prey];
            let mut occ = Occ { sub: vec![u32::MAX; g.sw * g.sh], crowd: vec![0; g.cells()] };
            occ.claim(g, &agents[0], 0);
            occ.claim(g, &agents[1], 1);
            let mut c = Counters::default();
            let mut food = Food::new(vec![0.0; g.cells()], vec![0.0; g.cells()], vec![0.0f64; g.cells()]);
            push(&mut agents, 0, EAST, g, &mut occ, &place, &mut food, CELL_ENERGY, 0, &mut c);
            assert_eq!(c.cells_broken, broken, "density {density}");
        }
    }

    #[test]
    fn a_push_meets_face_to_face() {
        let g = Grid::new(8, 8);
        // A tooth (hard tip, two muscle behind, column 2) facing east at anchor (0, 8): its tip
        // is at sub-cell (7, 10) (row 2 of the grid becomes column 7 when facing east).
        let mut tooth = [0u8; CELLS];
        tooth[2] = HARD as u8;
        tooth[SIDE + 2] = MUSCLE as u8;
        tooth[2 * SIDE + 2] = MUSCLE as u8;
        let hunter = agent_with(tooth, 0, 8, EAST);
        assert_eq!(hunter.wcells[2 * SIDE + 7], HARD as u8);
        // A soft body of two digestive cells right in front of it, at sub-cells (8, 10) and (9, 10).
        let mut soft = [0u8; CELLS];
        soft[0] = DIGESTIVE as u8;
        soft[1] = DIGESTIVE as u8;
        let prey = agent_with(soft, 8, 10, NORTH);
        let mut agents = vec![hunter, prey];
        let mut occ = Occ { sub: vec![u32::MAX; g.sw * g.sh], crowd: vec![0; g.cells()] };
        occ.claim(g, &agents[0], 0);
        occ.claim(g, &agents[1], 1);
        let place = vec![NO_PLACE; g.cells()];
        let mut c = Counters::default();
        let mut food = Food::new(vec![0.0; g.cells()], vec![0.0; g.cells()], vec![0.0f64; g.cells()]);
        let pressed = push(&mut agents, 0, EAST, g, &mut occ, &place, &mut food, CELL_ENERGY, 0, &mut c);
        // One body pressed with force 2 (two muscle cells in the line); the soft cell broke and
        // was eaten by nobody (the hunter has no digestive cell): it lies on the world cell it
        // was in, (2, 2), with half the prey's energy; the prey lost a cell.
        assert_eq!(pressed, vec![(1, 2)]);
        assert_eq!((c.contacts, c.cells_broken), (1, 1));
        assert_eq!(agents[1].body.size, 1);
        assert!((food.res[g.idx(2, 2)] - (CELL_ENERGY + 0.5) as f64).abs() < 1e-6);
        assert_eq!(food.carrion[g.idx(2, 2)], food.res[g.idx(2, 2)]);
        assert!((agents[1].energy - 0.5).abs() < 1e-6);
        assert_eq!(occ.sub[g.sidx(8, 10)], u32::MAX);
        assert_eq!(occ.crowd[g.idx(2, 2)], 1);
        // The way is clear now: the hunter fits one sub-cell east.
        assert!(agents[0].fits(g, &occ.sub, 0, EAST, 1));
        // The same push against a hard wall (hardness 3, the hunter's force 2): the wall holds
        // and, the tip being no softer, nothing breaks.
        let mut wall = [0u8; CELLS];
        wall[0] = HARD as u8;
        let w = agent_with(wall, 8, 10, NORTH);
        occ.release(g, &agents[1]);
        agents[1] = w;
        occ.claim(g, &agents[1], 1);
        let pressed = push(&mut agents, 0, EAST, g, &mut occ, &place, &mut food, CELL_ENERGY, 0, &mut c);
        assert_eq!(pressed, vec![(1, 2)]);
        assert_eq!(c.cells_broken, 1);
        assert!(!agents[0].fits(g, &occ.sub, 0, EAST, 1));
    }
}
