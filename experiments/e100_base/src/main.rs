//! e097: the crowd measured at its cause (#109 step 0, stage C).
//!
//! e092's crate - the default world of `foundation.md` and nothing else - with the birth path
//! instrumented. No law is added: with `probe` 0 the run is e092's bit for bit, and the probe has a
//! stream of its own besides, so it never moves a draw the bodies make.
//!
//! Half of all births fail for want of room in cells that are half empty (e092, e096), and the rule
//! that places a child is narrow: one of the four axis directions at random, 1..=`reach` sub-cells
//! along it, the first spot the child's whole rectangle fits in, `reach` being the wider of parent
//! and child - at most 24 spots, all on four rays, all within a body length. Whether the jam is the
//! world's or that rule's has never been measured.
//!
//! - **The probe** (`probe`, `probe_far`). A share `probe` of the births that find no room is
//!   measured where it failed and written to `<prefix>_room.csv`: what held each of the rule's own
//!   spots (a body, or a wall - the sea a land body cannot enter, a cell with no crown), the distance
//!   to the nearest spot the child does fit in (searched ring by ring out to `probe_far` body
//!   lengths, the diagonals the rule never tries among them, -1 if there is none), how many spots
//!   with room that ring holds and how many of them lie on the four rays, and the free sub-cells of
//!   the parent's cell and of its eight neighbours.
//! - **The ground** (with `probe`). The log gains `cells_held` (the share of the world's cells a body
//!   stands on) and `land_bare` (the share of the land's none stands on); `<prefix>_ground.csv` holds
//!   the same by habitat and medium at the end of the run. The log gains `place_k` (how far along its
//!   ray a placed child had to go) and `probed` (the failed births measured) whatever `probe` is.
//!
//! What follows is e092's description.
//!
//! e092: the yardstick (#102, stage C).
//!
//! e091's crate, unchanged, run with `crown_at` 0: the default world of `foundation.md` and nothing
//! else. It exists so that the control ladder every later stage C step is read against has a crate of
//! its own that will not move under it. No law is added or removed here; the experiment is the three
//! runs of seeds 12-14 that widen the ladder to six seeds, and the seed 9 run that checks this crate
//! reproduces e081's control.
//!
//! What follows is e091's description (its crate's, which still carries e090's header).
//!
//! e090: a mouthful of its own for the seed (#100 D + B + Fb', stage C).
//!
//! e089's crate with #100's three laws, which go in together. D: every producers' update a share
//! `seed_drift` of a cell's seed moves one cell downwind on the climate's wind (`plants.rs`), and seed
//! that lands on water sinks as the bottom's litter, so the seed leaves the grass that set it. B:
//! `seed_hard` 1, a hard tip with any force behind it opens seed, so the seed eater is no longer the
//! hunter. Fb': the fiber of grass, browse and wood is 0.8 (e089: 0.6) and `ferment` 0.005 a step (0.02),
//! so a body taking a turn every step gets 0.36 of the grass's matter and all of the seed's. The log
//! gains `seed_wet` (the seed that sank, a step, in the world's matter); `agents.csv` gains `fiber` (the
//! fiber in the gut now), which reads a body's digested share; `cells.bin` gains the seed on a cell.
//! At `seed_drift` 0 the world is e089's (the settled world's hash too).
//!
//! What follows is e089's description.
//!
//! e089: seed behind a tooth, fiber digested over time (#99 S + Fb, stage C).
//!
//! e088's crate with the bodies' side of #99. S: a gut on land takes seed (with the grass and the carrion
//! of its cell, in their proportions, `Plants::take_with_seed`) only in a body with a hard tip of force
//! `seed_hard` behind it, and such a body sees seed as food. Fb: a share of each food is fiber (FIBER_*);
//! what a gut takes less its fiber is energy at once, the fiber joins the body's gut store (`fiber`), which
//! gives `ferment` of itself as energy every step and passes `pass` of itself as dung, litter on the body's
//! cell, every turn; a dead body's fiber lies as litter. With `seed_share` and `ferment` 0 it is e088's (and
//! e081's control) exactly. The log gains `seed_intake`, `fiber_in`, `fermented`, `dung` (a step, in a body's
//! units) and `fiber_bodies`; `agents.csv` each body's lifetime `seed`, `fermented` and `dunged`.
//!
//! What follows is e088's description.
//!
//! e088: seed (#99 S, stage B).
//!
//! #99 (P2, a food web) gives plant matter a second kind: grass keeps `seed_share` of its growth as
//! seed on its cell, which sprouts into grass at `sprout` x warmth x water a step and rots at a tenth
//! of the litter's rate (`plants.rs`). This step runs the producers alone and reads the seed bank by
//! place and season. The crate is e082's with that law, its measures (`seed`, `seed_set`, `sprouted`
//! in the log, `seed` and `sprouted` in `bands.csv`) and the seed kept in the settled world's file;
//! a body does not eat seed yet. At `seed_share` 0 it is e082 exactly (the settled world's hash too).
//!
//! What follows is e082's description.
//!
//! e082: fresh under W1 (#95, `balance.md` section 17, stage C).
//!
//! e081 put the body's water into the land's (W1, W2) and found water binds every land body: a body
//! drinks little anywhere but a pool, since wet ground gives `fresh` 0.05 of a pool's drink, a share set
//! by #88 (set D) when a drink was free. Under W1 the drink is paid by the ground. This crate is e081's
//! unchanged: `fresh` and `unit` are already arguments, and the runs raise `fresh` at `unit` 9.4.
//!
//! What follows is e081's description.
//!
//! e081: drinking takes, losing gives back (#94, `balance.md` section 16, stage C).
//!
//! e080 found the stand the land's home in every season; what the land lacks is on the water's side, and
//! a body's water was a state: drinking took nothing and what a body lost went nowhere. This crate is
//! e080's with the body's water part of the land's, behind one rate, `unit` (mm of its cell's water a
//! block of a body's water is):
//!
//! - **W1, drinking takes** (`dry_turn_w`). A block drinks what its cell gives, as before, out of that
//!   cell's ground (a pool's standing water included), and a body takes only what brings it to full.
//! - **W2, losing gives back** (`settle`, `give_back`, `water_from_ground`). The dry air's and the sweat's
//!   water go to the air over the cell; a dead body's and a lost block's go into its cell's ground; a child
//!   and a start's body take their water from the ground under them (in the sea, from the sea), and on
//!   dry ground start with what it gives.
//!
//! At `unit` 0 the run is e080's exactly.
//!
//! What follows is e080's description.
//!
//! e080: a crown that takes its share of the sun's heat (#91 step 3, stage C).
//!
//! e079 built the plants' half of `balance.md` section 13 (S1 `crown_wet`, S2 `wood_rest`) and found a
//! mid-latitude stand's summer floor stops at a fill of 0.58, where a body's summer water closes only if
//! the crown also halves what it pays to cool. This crate is e079's with S3 on the body's side
//! (`refresh_air`), run on e079's world at `crown_wet` 1 and `wood_rest` 0.5:
//!
//! - **The crown's share of the sun's heat** (`crown_cool`, c3). What a body's heat reads under a crown is
//!   lowered by `min(1, c3 x shade) x (T_day - T_dark)`: T_day the cell's running mean over a day, T_dark
//!   what the cell goes toward with no sun (`night` less the lapse by its height), so the day's sun heat
//!   less the crown's share of it. It lowers the mean and leaves the day's swing; in winter the sun's heat
//!   is smaller and so is the cut, but a stand is still colder than the lawn beside it.
//!
//! At `crown_cool` 0 the run is e079's exactly.
//!
//! What follows is e078's description (e079's is in its own crate).
//!
//! e078: the shade of a crown (#91 step 1, stage C).
//!
//! #91 asks whether a stand of wood is a refuge a lawn cannot hold. e077 found the season takes the
//! mid-latitude lawn twice a year, in winter by food and in summer by heat (35-38 C against the heat
//! law's top of 30 C), and a stand within 1-5 C of the lawn beside it. This crate is e077's with the
//! crown's shade on what a body feels, as two rates read on the body's side (`refresh_air`): the
//! climate and the producers are e077's, so the settled world is the same.
//!
//! - **Shade on the heat** (`shade_heat`, k). What a body's heat reads on a cell is damped toward the
//!   cell's running mean over the day by k x shade, shade = wood / (wood + WOOD_HALF) (the share of
//!   the light the crown takes, as for the grass), at most all the way: the crown takes the top off a
//!   hot day and the bottom off a cold night.
//! - **Shade on the water** (`shade_dry`, k2). The dryness a body's soft faces lose water to is cut by
//!   k2 x shade, at most all of it.
//!
//! Both 0 is e077 (and e075's kept world) exactly. `bands.csv` gains `felt`, `over` and `under`: what
//! a body's heat read on the band's cells and its mean degrees over `warm_hi` and under `warm_lo`, over
//! every update since the last row.
//!
//! What follows is e074's description (e075-e077 are in their own crates).
//!
//! e074: the invasion test (#72, stage C's twelfth step).
//!
//! e073's world (its `wood_yield` 3e-5 kept) is the first of stage C to hold two ways of living
//! worth the test: a land browser with a tooth that takes a quarter of its food from the crowns'
//! yield, and a shore grazer without one. Whether a world can hold both is an ecological question;
//! whether evolution finds both from a random start is another, and every run so far has asked them
//! together. Ecology's test of the first is mutual invasion while rare, and this crate is its
//! instrument. It adds no law: three parameters and two files, and with none of them the run is
//! e073's exactly.
//!
//! - **The genomes of a census** (`genomes`). At the last census every body's genome is written to
//!   `<prefix>_genomes.csv` with its lineage and the medium it stood in. `pick.py` joins them to
//!   `agents.csv`, reads the kinds (e068's census by birth form) and writes the pools.
//! - **A world seeded from a pool** (`EVLOG_POOL`, `seed_n`). The start draws `seed_n` genomes from
//!   the pool instead of making random ones, and places each where its donor stood (land or water).
//!   A pool of the community with one kind's forms taken out is a world held by the others.
//! - **An injection** (`EVLOG_INJECT`, `inject_at`, `inject_n`, `inject_seed`). At `inject_at`,
//!   `inject_n` bodies of each injection pool are put in at random free spots of their donor's
//!   medium, each marked with the pool it came from (1 or 2); every descendant carries the mark, so
//!   the line is followed whatever the lineage detector does with it. Two pools separated by a
//!   colon put both lines into the same world at once, which is how the test is read: the invader
//!   and the resident's own genomes meet the same crowd, the same weather and the same luck. The
//!   draw and the placement have a stream of their own, and the matter the bodies are made of is
//!   added to the ledger the audit reads (`added`).
//!
//! What follows is e073's description.
//!
//! e073: wood a body can live on, and a cold that differs by place (#89, stage C's eleventh step).
//!
//! e072's sets are stage C's default world (`heat` 0.09, `wood_food` 0.04, `fat_weight` 0.06,
//! `store_gene` 1, `fresh` 0.05, `light` 0.7, `climb` 6e-5, `carry` 0.03). Two of them did nothing
//! there. e073 rebuilds those two, and searches them together:
//!
//! - **The crown's yield** (`wood_yield`, `plants.rs`). e072 let a gut take a share of a cell's
//!   *standing* wood: a stand of 0.6 a cell is 1,800 steps of food for the world, eaten out in the
//!   first ten thousand and back over 20,000 (`WOOD_LIFE`), so it is a windfall and not a living,
//!   and a share of the growth is no better (a stand can give up only its own cover, 1,300 of the
//!   37,000 a 1,000 steps the bodies eat). So the yield is a flow beside the stand: a stand drops
//!   `wood_yield` of browse per unit of what it stands a step, out of its cell's soil, the trunk
//!   untouched; browse uneaten rots into the soil at the litter's rate. A gut takes it with the
//!   tooth of force `wood_hard` that e072's stock share needed. Fire does not read the browse
//!   (stage B's law is left as it is; fire burns 0.06 of matter over 100,000 steps of this world).
//! - **A cold that differs by place** (`day_temp`, `climate.rs`). e072's heat reads the cell's
//!   temperature at the moment, and the day swings a land cell 20 C around its mean, so every cell
//!   is cold some of the time and none of the land is cold as a place (e071's finding). The climate
//!   now keeps `temp_day`, a running mean of a cell's temperature over the last day, and a body's
//!   heat reads `day_temp` of the way from the moment to that mean.
//!
//! Both rates 0 is e072 exactly.
//!
//! What follows is e072's description.
//!
//! e072: the balance sets, built together (#88, `balance.md`, stage C's tenth step).
//!
//! e070's world at `senses = 1` with the seven sets of the balance table built as one, each as a rate
//! whose 0 is e070 exactly. No set is judged alone; they are searched together.
//!
//! - **A. Heat** (`heat`, `body.rs`). A body holds heat. Each face of a block open to the cell under it
//!   passes heat by the difference at `heat` a degree, a hard face at `heat_hard` of that, and the fat
//!   stops `heat_fat` of it when it fills the store; the change is over the body's mass, so a heavy body
//!   follows the day slowly. Its blocks make `heat_make` of heat per unit of the upkeep they burn. Under
//!   `warm_lo` it pays `heat_spend` of energy a degree per unit of mass to warm itself back to the band,
//!   over `warm_hi` it pays `heat_sweat` of water to cool; a body that cannot pay the warming dies of
//!   cold, and one whose water runs out dies of thirst, as under the dry air. It replaces e071's cold.
//! - **B. Wood as food** (`wood_food`, `plants.rs`). A gut takes `wood_food` of a cell's wood, in
//!   proportion with the grass and the carrion, in a body with a hard tip of force `wood_hard` behind it
//!   (e010's rule applied to a plant).
//! - **C. The fat weighs** (`fat_weight`, `store_gene`). The fat adds `fat_weight` of mass per unit it
//!   holds, which the clock, the work of a move and a shove read; and the fat the flesh holds per unit
//!   of mass is read from the genome (e069's `store` alone) with `store_gene`.
//! - **D. The sea does not quench** (`fresh`). A block drinks all of `drink` over a pool, `fresh` of it
//!   over ground at full fill, and nothing over the sea, which still gives its breath.
//! - **E. Light** (`light`). A sensor block sees `light` of the way toward what the light where the body
//!   stands allows: the sun's height, less under deep water and under a stand of wood.
//! - **F. Height** (`climb`). A body that moves onto a higher cell pays `climb` per unit of mass per
//!   metre it rises, on top of e015's work.
//! - **G. The runoff carries soil** (`carry`, `climate.rs`). Water running off a land cell takes
//!   `carry` of its soil per millimetre of the ground's capacity into the cell it runs to, the sea
//!   included. It runs with the bodies only: the settled world is the one they start from.
//!
//! What follows is e070's description.
//!
//! e070: senses from sensor blocks (#84, the eighth step of stage C).
//!
//! e069 at `history = 0` (e067's world at `breath = 0.01`) with one parameter, `senses`. On, a body
//! senses only through its sensor blocks (`body.rs`, `sense`): the food under them, the food, bodies
//! and water in a direction where a sensor block looks out of the body that way (as far as one cell
//! and one more per such block), and its energy, thirst and breath if it has a sensor block at all.
//! No input is added and no price: a sensor block costs what it cost. `senses = 0` is e069 at
//! `history = 0`.
//!
//! What follows is e069's description.
//!
//! e069: life history from the genome (#83, the seventh step of stage C).
//!
//! e067 at `breath = 0.01` (its kept default) with three values of a life read from the genome
//! (`body.rs`): the energy a body breeds at per unit of mass, the share of its energy a child gets,
//! and the fat its flesh holds per unit of mass, each today's constant times x0.5 to x2. No law
//! changes: what a block is made of and costs, the matter a child needs and the ledger stay. The mate
//! distance and the mutation rate stay constants. `history = 0` is e067 at `breath = 0.01`.
//!
//! What follows is e067's description.
//!
//! e067: breath in water (#81, the fifth step of stage C, its third trade-off).
//!
//! e066 at `dry = 0.004` with the closed body priced in the water (`body.rs`, `foundation.md` section
//! 2). A block over water uses breath and each face of a soft block open to the water gives it back;
//! a block over land breathes freely (`inhale`). A body whose breath runs out dies of suffocation. A
//! child starts at its parent's breath. The body reads its breath through a column of the law table
//! of its own. `breath = 0` is e066 at `dry = 0.004`.
//!
//! What follows is e066's description.
//!
//! e066: dry air (#80, the fourth step of stage C, its second trade-off).
//!
//! e065 with the air's dryness priced on a body's blocks (`body.rs`, `foundation.md` section 2). A
//! soft block over ground that is not water loses water each turn by the faces it opens to the air
//! times the dryness there (1 minus the ground's fill, e061's moisture; the air's relative humidity
//! was measured too, and over a year a cell's mean of it spreads a third as wide over the land); a
//! hard block does not; a block over water (the sea, or a pool of standing water on land) drinks.
//! A body whose water runs out dies of thirst. A child is born with its parent's fill (e040). The
//! eye sees the water and the body reads its thirst, weighed by a column of the law table of its
//! own. `dry = 0` is e065.
//!
//! What follows is e065's description.
//!
//! e065: the water's two layers (#79, the third step of stage C, its first trade-off).
//!
//! e064 at scale 1/16 with the water open (`water = 1`, `foundation.md` section 2). A water cell has
//! a surface layer and a bottom layer; a body lighter than water (density under 1) lives at the
//! surface, a denser one on the bottom, and it touches, sees and eats only its own layer (`body.rs`).
//! A surface gut eats the algae; a bottom gut eats what sinks: the carrion and the algae's dead,
//! which now lie on the bottom as litter before they rot (`plants.rs`). Land has one layer, shared,
//! with the grass and the carrion as before. All water is open, shallow and deep; pools on land stay
//! land for a body. The start places `start` bodies per cell of the whole world. The settled world
//! is e063's (its algae's dead went to the soil); the bottom's litter builds up once the bodies
//! start. `water = 0` is e064.
//!
//! What follows is e064's description.
//!
//! e064: a body's scale of matter against the producers (#78, the second step of stage C).
//!
//! e063 with one number more, `scale` (s): every matter quantity of a body (the upkeep, the bite,
//! the work of moving, what a block is made of, the start energy, the threshold to breed, the fat
//! the flesh holds) times s. The body keeps them in its own units and s converts at the world's
//! edge (`body.rs`); the eye reads the food in the body's units (food / s), so s changes how many
//! bodies the world holds and not what a body sees. The question is the density: e063's bodies
//! (s = 1) were one per 360-530 land cells, too thin for bodies to meet.
//!
//! What follows is e063's description, unchanged but for the name of the run.
//!
//! e063: bodies on the stage-B world (#76, the first step of foundation stage C).
//!
//! e062's world as it passed stage B (a world of e061's climate with e062's producers and fire,
//! grown as e062 grew it) and e059's bodies with every law the season world kept (`body.rs`),
//! ported onto it with no new law about a body. The questions are the prototype's, #76's agreed
//! first step: what a step costs at 512 with bodies on it, how many bodies the world feeds and
//! whether it stands, and so whether stage C's runs need threads for the bodies or a window of
//! the world.
//!
//! What joins the two is the least the port needs, not a law under test:
//! - A body lives on land: a sub-cell of the sea is a wall. The water's two layers are the first
//!   of stage C's trade-offs, still to build.
//! - A gut takes from the grass standing on its world cell and from the dead lying there
//!   (`carrion`), in their proportions. Wood (its hardness against a bite is to be set), algae (in
//!   the water) and the plants' litter are not food yet.
//! - What a body spends (the upkeep its fat pays, the fat its flesh cannot hold, the work of its
//!   moves) goes to the soil of the world cell under it, as e019's did. Through the world's one
//!   air pool, which rains on the sea by the sea's share of the rain, it would drain the land:
//!   e062's smoke moved up to 1.2% of the land's matter a year, and the bodies spend about what
//!   the grass grows.
//! - The dead rot into their cell's soil at 1% a step (e017), on the producers' clock.
//! - The climate and the producers update every `tick` steps (e062); the bodies every step.
//!
//! The settled world (the climate's spin-up and e062's years of producers) is built once per
//! world and kept in `results/worlds/` (not committed), and every run of the bodies starts from it.
//!
//! Run: cargo run --release -p e064_scale -- <prefix> [key=value ...] [file.params ...]
//! `<prefix>_log.csv` is a row every 1,000 steps, `_agents.csv` every body every 10,000 steps (the
//! columns e060's census reads, with the tooth at birth, the kills apart from the dead eaten, the
//! path and the habitat), `_events.csv` and `_lineages.csv` e006's lineages, `_row.csv` the run's
//! parameters and its second half in one row.

mod body;
mod climate;
mod habitat;
mod plants;

use body::*;
use climate::{Sat, World};
use habitat::*;
use plants::{depth, Plants, LIGHT_DEPTH, WOOD_HALF};
use std::collections::{HashMap, HashSet};
use std::f64::consts::TAU;
use std::io::Write;
use std::time::Instant;

const LOG_INTERVAL: u64 = 1_000;
const LINEAGE_INTERVAL: u64 = 1_000;
const AGENT_DUMP: u64 = 10_000;
const GROWN: u32 = 300; // e060: a body this old has a diet
const TOOTH: u8 = 2; // e060: a force of 2 behind a hard tip breaks a soft face of density 1
const WORLD_VERSION: u64 = 1; // the format of a settled world's file
const WORLDS: &str = "experiments/e063_bodies/results/worlds"; // e064 reads e063's settled worlds
// e089 (#99 Fb): the share of each food that is fiber, digested over time; seed, flesh and carrion have none.
const FIBER_LEAF: f64 = 0.8; // e090 (Fb'): grass, browse and wood (e089: 0.6)
const FIBER_ALGAE: f64 = 0.3;
const FIBER_LITTER: f64 = 0.5; // the bottom's litter
const CAUSES: [&str; 7] = ["hunger", "broken", "wear", "thirst", "suffocation", "cold", "wound"];

macro_rules! params {
    ($($name:ident = $default:expr, $doc:literal;)*) => {
        #[derive(Clone, Debug)]
        pub struct Params { $(pub $name: f64,)* }
        impl Default for Params {
            fn default() -> Self { Params { $($name: $default,)* } }
        }
        impl Params {
            const NAMES: &'static [&'static str] = &[$(stringify!($name),)*];
            const DOCS: &'static [&'static str] = &[$($doc,)*];
            fn set(&mut self, key: &str, v: f64) -> bool {
                match key { $(stringify!($name) => { self.$name = v; true })* _ => false }
            }
            fn values(&self) -> Vec<f64> { vec![$(self.$name,)*] }
        }
    };
}

params! {
    // e061's climate (its defaults, but the size: stage A decided on 512)
    size = 512.0, "cells on a side of the world (a torus)";
    seed = 1.0, "the seed of the generated terrain";
    year = 20000.0, "steps in a year";
    day = 60.0, "steps in a day (a fifth of a life of 300 steps)";
    tick = 10.0, "steps between two updates of the climate and the producers";
    land = 0.35, "share of the cells above the sea";
    relief = 3000.0, "m: the height of the highest land";
    grain = 64.0, "cells: the widest feature of the terrain";
    rough = 0.5, "amplitude of each finer octave of the terrain over the one before";
    lat_lo = -60.0, "degrees: the latitude of the first row (and of the last)";
    lat_hi = 60.0, "degrees: the latitude of the middle row";
    tilt = 23.0, "degrees: the tilt of the axis (0: no seasons)";
    night = -30.0, "C: what a cell goes toward with no sun";
    gain = 180.0, "C: what the sun overhead adds to that";
    lapse = 6.5, "C per km of height";
    land_rate = 0.1, "share of the way to its equilibrium a land cell goes in an update";
    sea_rate = 0.0005, "the same for the sea (its heat capacity is land_rate / sea_rate times the land's)";
    spread = 0.2, "share of the difference with its neighbors a land cell takes in an update";
    wind = 0.5, "cells the air moves in an update";
    wind_dir = 0.0, "degrees: where the wind blows to on average (0 along +x, 90 along +y)";
    wind_turn = 45.0, "degrees: how far the wind turns with the season";
    evap = 0.05, "share of the air's deficit a wet cell fills in an update";
    rain = 0.1, "share of the air's excess over 80% of saturation that falls in an update";
    flow = 0.25, "share of the standing water that runs downhill in an update";
    soil = 150.0, "mm of water the ground holds before water stands on it";
    // e062's producers
    spinup = 20000.0, "climate updates before the producers start (rounded up to whole years)";
    grow_years = 10.0, "years of producers before the bodies come, at least (e062 judged its worlds after as many)";
    grow_steps = 200000.0, "steps of producers before the bodies come, at least";
    grass_rate = 0.006, "matter grass grows a step at full cover, the sun overhead, warm and wet";
    wood_rate = 0.0024, "the same for wood";
    algae_rate = 0.01, "the same for algae, in shallow water";
    ignite = 1e-6, "chance a strike hits a cell in an update (it catches if dry, warm and fuelled)";
    matter = 10.0, "matter a cell holds at the start, in its soil and its producers";
    // e063's bodies
    life = 1.0, "the seed of the bodies: the gene table, the genomes and every draw of their lives (the terrain's is seed)";
    steps = 100000.0, "steps of bodies (0: build the settled world and stop)";
    start = 0.0977, "bodies per land cell at the start (e006's 400 on 64x64)";
    // e064's scale, stage C's from here (#79)
    scale = 0.0625, "a body's scale of matter (#78): its upkeep, bite, moves, blocks, start energy, threshold and fat, in the world's matter";
    // e065's water
    water = 1.0, "1: the water's two layers are open to bodies and the algae's dead lie on the bottom (#79); 0: the sea is a wall (e064)";
    // e066's dry air
    dry = 0.004, "water a soft block loses a turn per face open to the air, times the dryness there (1 - the ground's fill), in blocks of water (0: e065; e067 runs at e066's 0.004)";
    drink = 0.1, "water a block over water gives a turn, in blocks of water";
    // e067's breath
    breath = 0.01, "breath a block over water uses a turn, and a face of a soft block open to the water gives back, in blocks of breath (0: e066; e067 kept 0.01)";
    inhale = 0.1, "breath a block over land gives a turn, in blocks of breath";
    // e069's life history
    history = 0.0, "1: the energy to breed per unit of mass, the child's share and the fat per unit of mass are read from the genome (#83); 0: today's constants (e067)";
    // e070's senses
    senses = 1.0, "1: a body senses only through its sensor blocks, by where they look out of it (#84, kept by e070); 0: every body sees around it and reads its fills (e069)";
    // e072's balance sets (#88), every rate 0 being e070
    heat = 0.0, "set A: heat a face of a block open to its cell passes a turn per degree of difference (0: a body has no heat)";
    warm_lo = 15.0, "set A: C, under this a body pays energy to warm itself back to it";
    warm_hi = 30.0, "set A: C, over this it pays water to cool itself back to it";
    heat_make = 1000.0, "set A: heat (degrees x mass) a body makes per unit of the upkeep it burns, so that it sits heat_make x upkeep / open faces over its cell";
    heat_hard = 0.25, "set A: share of a soft face's heat that a hard face passes";
    heat_fat = 0.75, "set A: share of the passing the fat stops when it fills the body's store";
    heat_spend = 0.0035, "set A: energy a body pays to warm itself a degree per unit of mass";
    heat_sweat = 0.003, "set A: water (of its fill) a body pays to cool itself a degree per unit of mass, over its open soft faces";
    wood_food = 0.0, "set B: share of a cell's wood a gut may take, in a body whose tooth reaches wood_hard (0: wood is not food)";
    wood_hard = 3.0, "set B: the force behind a hard tip a body needs to bite wood";
    fat_weight = 0.0, "set C: mass a unit of fat adds to a body (0: the fat weighs nothing)";
    store_gene = 0.0, "set C: 1, the fat the flesh holds per unit of mass is read from the genome (e069's store alone); 0: the constant";
    fresh = 0.0, "set D: share of `drink` that ground at full fill gives; a pool gives all of it and the sea none (0: any water quenches, e066)";
    light = 0.0, "set E: how far a sensor block's reach follows the light where the body stands (0: it always sees its full reach)";
    climb = 0.0, "set F: energy a body pays per unit of mass per metre it rises when it moves (0: height is free)";
    carry = 0.0, "set G: share of a cell's soil the water running off it takes along, per millimetre of the ground's capacity (0: the soil stays)";
    // e073's two laws (#89), both 0 being e072
    wood_yield = 0.0, "e073: browse a stand of wood drops a step per unit of what it stands, out of its cell's soil (0: no crown yields)";
    day_temp = 0.0, "e073: how far a body's heat reads the day's running mean of its cell's temperature instead of the moment (0: the moment, e072)";
    // e075's flesh (#90), both 0 being e073's kept world
    flesh_bite = 0.0, "e075: share of what a torn body still holds (its energy and its fat) that the gut which broke a block of it takes besides the block (0: only the block, e073)";
    frail = 0.0, "e075: the share of its birth blocks a body must keep to live; under it it dies of its wounds and lies where it fell (0: it lives to its last block, e073)";
    // The disturbance of #88's stability check, on the chosen candidates only
    cull_at = 0.0, "the step at which the largest lineage is cut (0: never)";
    cull = 0.5, "the share of its bodies the cut takes";
    // e074's invasion test (#72). None of it is a law: with no pool file and inject_at 0 the run is e073's.
    genomes = 0.0, "1: write every body's genome at the last census to <prefix>_genomes.csv (#72)";
    seed_n = 0.0, "bodies drawn from the seed pool (EVLOG_POOL) at the start (0: `start` random genomes per open cell)";
    inject_at = 0.0, "the step at which the injection pool's bodies are put into the world (0: never)";
    inject_n = 0.0, "how many bodies of the injection pool (EVLOG_INJECT) are put in";
    inject_seed = 1.0, "the seed of the draw and the placement of the injected bodies: a stream of its own, so the resident world is the same run under every injection";
    // e077's measures (#91), no law
    census = 10000.0, "steps between censuses of every body (agents.csv)";
    census_from = 0.0, "censuses before this step are skipped (the one at `census` multiples from here)";
    // e078's shade (#91 step 1), both 0 being e077 (and e075's kept world)
    shade_heat = 0.0, "e078: how far a crown damps what a body's heat reads toward the day's mean, times the shade (wood / (wood + WOOD_HALF)), at most all the way (0: no damping)";
    shade_dry = 0.0, "e078: how far a crown cuts the dryness a body loses water to, times the shade, at most all of it (0: no cut)";
    // e079's crown (#91 step 2), both 0 being e078's world. They make the settled world.
    crown_wet = 0.0, "e079 (S1): how far a crown cuts the evaporation from the ground under it, times the shade, at most all of it (0: no cut)";
    wood_rest = 0.0, "e079 (S2): how far wood's death follows the warmth its growth reads (1: a trunk does not die in the cold; 0: one rate all year)";
    cell_map = 0.0, "e079: 1, write every cell's ground fill, temperature and rain by quarter over the run, and its wood and grass at the end, to <prefix>_cells.bin (a measure)";
    // e080's crown (#91 step 3), 0 being e079
    crown_cool = 0.0, "e080 (S3): the share of the day's sun heat (the day's mean less the cell's dark equilibrium) a crown takes off what a body's heat reads, times the shade, at most all of it (0: none)";
    // e081's water (#94), 0 being e080
    unit = 0.0, "e081 (W1, W2): mm of its cell's water a block of a body's water is; a body drinks out of the ground and pools under it and what it loses goes to the air and the ground (0: its water is free, e080)";
    // e088's seed (#99 S), 0 being e082. It makes the settled world.
    seed_share = 0.0, "e088: the share of the grass's growth set as seed instead of leaf (0: no seed, e082's world)";
    sprout = 0.001, "e088: the share of the seed on a cell that sprouts into grass a step, warm and wet (read only with seed_share)";
    // e089's bodies (#99 S and Fb), both off being e088
    // e090's drift (#100 D), 0 being e088's world
    seed_drift = 0.0, "e090 (D): the share of a cell's seed that moves one cell downwind in a producers' update (0: the seed stays where it was set, e088)";
    seed_hard = 2.0, "e089 (S): the force behind a hard tip a body needs to take seed (read only with seed_share)";
    ferment = 0.0, "e089 (Fb): the share of the fiber in a gut that becomes energy a step (0: no fiber, a food is energy at the bite)";
    pass = 0.02, "e089 (Fb): the share of the fiber in a gut that leaves as dung a turn (read only with ferment)";
    // e097's room probe (#109 step 0), no law: with `probe` 0 nothing of it runs and the world is
    // e092's control bit for bit (the probe has a stream of its own besides, as e059's columns do).
    reach = 1.0, "e097 (#109 step 1): body lengths out to which a child looks for room - the rule's reach, times the wider of parent and child (1: today's rule)";
    ring = 0.0, "e097 (#109 step 1): 1, the search walks every spot at a distance before it goes further out, the diagonals among them; 0: the four axis rays (today's rule)";
    probe = 0.0, "e097 (#109): the share of failed births measured - what their tried spots hit, and how far off the nearest spot with room for the child is - written to <prefix>_room.csv (0: no probe)";
    probe_far = 8.0, "e097 (#109): body lengths out to which the probe looks for a spot with room (read only with probe)";
    // e091's crown (#101). All three run with the bodies: the settled world keeps neither the browse
    // the crowns drop nor their fruit, so a run starts with empty crowns whatever they are.
    crown_at = 0.0, "e091 (C1): the wood at which a land cell carries a crown, a place a body stands in over the floor (0: no crowns, e081's control)";
    fruit_fall = 0.5, "e091 (C2): the share of a crown's drop that falls to the floor as browse instead of staying up as fruit (read only with crown_at)";
    hold = 10.0, "e091 (C3): the mass a crown holds per unit of its cell's wood; a heavier body stands on the floor (read only with crown_at)";
}

/// e079: the settled world's keys added after e078; at 0 they leave its hash, so e078's world is read.
/// e088: `seed_share` too, and `sprout` is read only with it.
const NEW_WORLD_KEYS: [&str; 4] = ["crown_wet", "wood_rest", "seed_share", "seed_drift"];

/// The parameters of the bodies; every other one makes the settled world.
const BODY_KEYS: [&str; 55] = [
    "life", "steps", "start", "scale", "water", "dry", "drink", "breath", "inhale", "history", "senses",
    // e072's sets, the runoff's soil among them: they all run with the bodies, from the settled world
    "heat", "warm_lo", "warm_hi", "heat_make", "heat_hard", "heat_fat", "heat_spend", "heat_sweat",
    "wood_food", "wood_hard", "fat_weight", "store_gene", "fresh", "light", "climb", "carry",
    // e073's two laws, e075's flesh (#90) and e074's injection (#72)
    "wood_yield", "day_temp", "flesh_bite", "frail", "cull_at", "cull", "genomes", "seed_n", "inject_at", "inject_n", "inject_seed",
    "census", "census_from", "shade_heat", "shade_dry", "cell_map", "crown_cool", "unit",
    // e089's
    "seed_hard", "ferment", "pass",
    // e091's (#101): the crown is a place the bodies live in; the settled world is the control's
    "crown_at", "fruit_fall", "hold",
    // e097's probe (#109): a measure that runs with the bodies, so it leaves the settled world alone
    "reach", "ring", "probe", "probe_far",
];

/// What the viewer is told a cell holds (e062's units).
const VIEW_RELIEF: f64 = 64.0;
const VIEW_SEA: f64 = 3.0;
const TEMP_OFFSET: f64 = 50.0;

fn parse(args: &[String]) -> Params {
    let mut p = Params::default();
    let apply = |s: &str, p: &mut Params| {
        let s = s.split('#').next().unwrap().trim();
        if s.is_empty() {
            return;
        }
        let (k, v) = s.split_once('=').unwrap_or_else(|| panic!("not key=value: {s}"));
        let v: f64 = v.trim().parse().unwrap_or_else(|_| panic!("not a number: {s}"));
        assert!(p.set(k.trim(), v), "no parameter named {}", k.trim());
    };
    for a in args {
        if a.contains('=') {
            apply(a, &mut p);
        } else {
            for line in std::fs::read_to_string(a).unwrap_or_else(|e| panic!("{a}: {e}")).lines() {
                apply(line, &mut p);
            }
        }
    }
    p
}

/// The genomes a world is seeded with and the genomes injected into it (#72). Each line of a pool
/// file is `medium,genome`: the medium its donor stood in (0 land, 1 surface, 2 bottom) and the
/// genome as N digits. `pick.py` writes them out of a run's census.
#[derive(Default)]
struct Pools {
    seed: Vec<(u8, Vec<u8>)>,
    inject: Vec<Vec<(u8, Vec<u8>)>>, // one per mark: EVLOG_INJECT is a colon-separated list of files
}

fn read_pool(path: &str) -> Vec<(u8, Vec<u8>)> {
    let text = std::fs::read_to_string(path).unwrap_or_else(|e| panic!("{path}: {e}"));
    let mut out = Vec::new();
    for line in text.lines().skip(1) {
        let (m, g) = line.split_once(',').unwrap_or_else(|| panic!("not medium,genome: {line}"));
        assert_eq!(g.len(), N, "a genome is {N} bases");
        out.push((m.parse().unwrap(), g.bytes().map(|b| b - b'0').collect()));
    }
    assert!(!out.is_empty(), "{path}: no genomes");
    out
}

/// A free spot for a body (#72): `sea` asks for a cell of the medium its donor stood in, so that a
/// land form is not dropped in the sea, and `None` takes any cell. The caller pushes the body at
/// `at`, where the occupancy has just been told it stands.
#[allow(clippy::too_many_arguments)]
fn place(a: &mut Agent, g: Grid, occ: &mut Occ, w: &World, hab: &[u8], at: u32, sea: Option<bool>, tries: usize, rng: &mut Rng) -> bool {
    for _ in 0..tries {
        a.x = rng.below(g.sw);
        a.y = rng.below(g.sh);
        if sea.is_some_and(|want| w.sea[a.here(g)] != want) {
            continue;
        }
        if a.fits(g, occ, FREE, NORTH, 0) {
            a.born_at = (a.x, a.y);
            a.born_hab = hab[a.here(g)];
            a.layer = occ.layer_for(g, a, NORTH, 0); // e091: a light body starts in the crown over it
            occ.claim(g, a, at);
            return true;
        }
    }
    false
}

/// Updates per quarter and per year, and the update the producers start at.
fn clocks(p: &Params) -> (u64, u64, u64) {
    let per_quarter = ((p.year / p.tick / 4.0).round() as u64).max(1);
    let per_year = 4 * per_quarter;
    (per_quarter, per_year, (p.spinup as u64).div_ceil(per_year) * per_year)
}

/// e079: the quarter of the year an update falls in, counted from the producers' start (a whole
/// year): 0 and 2 the equinoxes, 1 the north's summer and 3 its winter, each centred on its day.
fn season_of(p: &Params, since_start: u64) -> usize {
    let phase = since_start as f64 * p.tick / p.year;
    (((phase + 0.125) % 1.0) * 4.0) as usize % 4
}

fn world_hash(p: &Params) -> u64 {
    let mut h: u64 = 0xcbf29ce484222325 ^ WORLD_VERSION;
    for (name, v) in Params::NAMES.iter().zip(p.values()) {
        if !BODY_KEYS.contains(name) && !(NEW_WORLD_KEYS.contains(name) && v == 0.0) && !(*name == "sprout" && p.seed_share == 0.0) {
            for b in format!("{name}={v};").bytes() {
                h = (h ^ b as u64).wrapping_mul(0x100000001b3);
            }
        }
    }
    h
}

fn put(out: &mut Vec<u8>, v: &[f64]) {
    out.extend_from_slice(&(v.len() as u64).to_le_bytes());
    for x in v {
        out.extend_from_slice(&x.to_le_bytes());
    }
}

fn put_u32(out: &mut Vec<u8>, v: &[u32]) {
    out.extend_from_slice(&(v.len() as u64).to_le_bytes());
    for x in v {
        out.extend_from_slice(&x.to_le_bytes());
    }
}

struct Reader<'a> {
    b: &'a [u8],
    o: usize,
}

impl Reader<'_> {
    fn u64(&mut self) -> Option<u64> {
        let v = u64::from_le_bytes(self.b.get(self.o..self.o + 8)?.try_into().ok()?);
        self.o += 8;
        Some(v)
    }
    fn f64s(&mut self) -> Option<Vec<f64>> {
        let n = self.u64()? as usize;
        let s = self.b.get(self.o..self.o + 8 * n)?;
        self.o += 8 * n;
        Some(s.chunks_exact(8).map(|c| f64::from_le_bytes(c.try_into().unwrap())).collect())
    }
    fn u32s(&mut self) -> Option<Vec<u32>> {
        let n = self.u64()? as usize;
        let s = self.b.get(self.o..self.o + 4 * n)?;
        self.o += 4 * n;
        Some(s.chunks_exact(4).map(|c| u32::from_le_bytes(c.try_into().unwrap())).collect())
    }
}

/// A settled world in bytes: the climate's state, the producers' (their draws included) and the
/// update it stands at. Everything else is scratch or follows from the parameters.
fn world_bytes(hash: u64, update_i: u64, w: &World, pl: &Plants) -> Vec<u8> {
    let mut out = Vec::new();
    out.extend_from_slice(b"E063WRLD");
    out.extend_from_slice(&hash.to_le_bytes());
    out.extend_from_slice(&update_i.to_le_bytes());
    for v in [&w.temp, &w.vapor, &w.ground, &w.light, &w.rain_now, &pl.grass, &pl.wood, &pl.algae, &pl.litter, &pl.soil, &pl.carrion] {
        put(&mut out, v);
    }
    put_u32(&mut out, &pl.burnt_in);
    put_u32(&mut out, &pl.fire_sizes);
    let front: Vec<u32> = pl.front.iter().flat_map(|&(c, id)| [c, id]).collect();
    put_u32(&mut out, &front);
    out.extend_from_slice(&pl.air.to_le_bytes());
    out.extend_from_slice(&pl.rng.0.to_le_bytes());
    put(&mut out, &pl.seed); // e088: after the rest, so that a file without it reads as no seed
    out
}

fn world_from(bytes: &[u8], hash: u64, p: &Params) -> Option<(World, Plants, u64)> {
    if bytes.get(..8)? != b"E063WRLD" {
        return None;
    }
    let mut r = Reader { b: bytes, o: 8 };
    if r.u64()? != hash {
        return None;
    }
    let update_i = r.u64()?;
    let mut w = World::new(p);
    let mut pl = Plants::new(&w, p);
    w.temp = r.f64s()?;
    w.vapor = r.f64s()?;
    w.ground = r.f64s()?;
    w.light = r.f64s()?;
    w.rain_now = r.f64s()?;
    pl.grass = r.f64s()?;
    pl.wood = r.f64s()?;
    pl.algae = r.f64s()?;
    pl.litter = r.f64s()?;
    pl.soil = r.f64s()?;
    pl.carrion = r.f64s()?;
    pl.burnt_in = r.u32s()?;
    pl.fire_sizes = r.u32s()?;
    pl.front = r.u32s()?.chunks_exact(2).map(|c| (c[0], c[1])).collect();
    pl.air = f64::from_bits(r.u64()?);
    pl.rng.0 = r.u64()?;
    if let Some(seed) = r.f64s() {
        pl.seed = seed;
    }
    // e073: the day's running mean is not kept in the file (it settles inside a day of the run).
    w.temp_day.copy_from_slice(&w.temp);
    w.temp_read.copy_from_slice(&w.temp);
    Some((w, pl, update_i))
}

/// The world the bodies come to: e061's climate spun up, then e062's producers grown as e062 grew
/// them (at least `grow_years` and `grow_steps`), so that it is the world e062 judged at its end.
/// Kept in `dir` once built (None: always built).
fn settled_world(p: &Params, dir: Option<&str>) -> (World, Plants, u64) {
    let hash = world_hash(p);
    let path = dir.map(|d| format!("{d}/c{}_{hash:016x}.bin", p.seed));
    if let Some(path) = &path {
        if let Some(world) = std::fs::read(path).ok().and_then(|b| world_from(&b, hash, p)) {
            eprintln!("settled world read from {path}");
            return world;
        }
    }
    let started = Instant::now();
    let sat = Sat::new();
    // e062's world: the algae's dead go to the soil while it grows (e065's bottom starts with the bodies).
    // e072: the settled world is built with the runoff carrying nothing (set G runs with the bodies).
    let p = &Params { water: 0.0, carry: 0.0, ..p.clone() };
    let mut w = World::new(p);
    let (_, per_year, plant_start) = clocks(p);
    let mut update_i = 0u64;
    let mut no_soil: Vec<f64> = Vec::new();
    while update_i < plant_start {
        w.update(p, &sat, update_i as f64 * p.tick, &mut no_soil, &[]);
        update_i += 1;
    }
    let mut pl = Plants::new(&w, p);
    let years = (p.grow_years.max(1.0) as u64).max(((p.grow_steps / p.tick).ceil() as u64).div_ceil(per_year));
    for yr in 1..=years {
        for _ in 0..per_year {
            w.update(p, &sat, update_i as f64 * p.tick, &mut pl.soil, &pl.wood);
            pl.update(&w, p, yr as u32);
            update_i += 1;
        }
        // e079: how the stands settle, a line a year (the new laws may settle slower than e062's).
        let n = w.n;
        let (mut land, mut wood, mut stands, mut mid) = (0usize, 0.0f64, 0usize, 0usize);
        for c in 0..n * n {
            if w.sea[c] {
                continue;
            }
            land += 1;
            wood += pl.wood[c];
            if pl.wood[c] >= 1.0 {
                stands += 1;
                mid += (20.0..50.0).contains(&w.lat_sin[c / n].asin().to_degrees().abs()) as usize;
            }
        }
        let (grass, seed): (f64, f64) = (0..n * n).filter(|&c| !w.sea[c]).map(|c| (pl.grass[c], pl.seed[c])).fold((0.0, 0.0), |a, b| (a.0 + b.0, a.1 + b.1));
        eprintln!(
            "settling year {yr}: wood {:.3} a land cell, {stands} stand cells, {mid} of them at 20-50 degrees, grass {:.3}, seed {:.3}",
            wood / land.max(1) as f64,
            grass / land.max(1) as f64,
            seed / land.max(1) as f64
        );
    }
    let cells = (w.n * w.n) as f64;
    eprintln!(
        "settled world built in {:.1} s: grass/wood/algae {:.2}/{:.2}/{:.2} a cell after {years} years",
        started.elapsed().as_secs_f64(),
        pl.grass.iter().sum::<f64>() / cells,
        pl.wood.iter().sum::<f64>() / cells,
        pl.algae.iter().sum::<f64>() / cells
    );
    if let (Some(path), Some(dir)) = (&path, dir) {
        std::fs::create_dir_all(dir).ok();
        let tmp = format!("{path}.tmp{}", std::process::id());
        std::fs::write(&tmp, world_bytes(hash, update_i, &w, &pl)).unwrap();
        std::fs::rename(&tmp, path).unwrap();
    }
    (w, pl, update_i)
}

/// Whether cell `c` is water for a body (the sea, or a pool of standing water on land as the algae
/// and the habitats count one), and how dry it is, 0 over water (e066): the air's, 1 minus its vapor
/// over what it holds at the cell's temperature, and the ground's, 1 minus its fill. The law reads
/// the ground's: over a year on c1225's land a cell's mean of the air's spreads a third as wide.
/// e081 (W2): water given back where a body stands, into its cell's ground or, in the sea, the sea.
/// Returns the mm given the ground and the sea.
fn give_to(w: &mut World, c: usize, mm: f64) -> (f64, f64) {
    if w.sea[c] {
        (0.0, mm)
    } else {
        w.ground[c] += mm;
        (mm, 0.0)
    }
}

/// e081 (W2): the water a body's lost blocks held (a wear, a bite, a part cut loose) goes into the
/// ground under it, and its booking follows its water (a fill of so many blocks).
fn settle(a: &mut Agent, g: Grid, w: &mut World, unit: f64) -> (f64, f64) {
    let now = a.water.max(0.0) as f64 * a.body.size as f64;
    let spill = (a.held - now) * unit;
    a.held = now;
    give_to(w, a.here(g), spill)
}

/// e081 (W2): a dead body's water goes into its cell's ground (the sea's, in the sea).
fn give_back(a: &mut Agent, g: Grid, w: &mut World, unit: f64) -> (f64, f64) {
    let mm = a.held * unit;
    a.held = 0.0;
    give_to(w, a.here(g), mm)
}

/// e081 (W2): a body put into the world (a child, the start's) takes the water its fill holds from the
/// ground under it, or from the sea; on ground that holds less it starts with what there is. Returns
/// the mm taken from the ground and from the sea.
fn water_from_ground(a: &mut Agent, g: Grid, w: &mut World, unit: f64) -> (f64, f64) {
    let c = a.here(g);
    let size = a.body.size as f64;
    let need = a.water.max(0.0) as f64 * size * unit;
    let (ground, sea) = if w.sea[c] {
        (0.0, need)
    } else {
        let t = need.min(w.ground[c].max(0.0));
        w.ground[c] -= t;
        (t, 0.0)
    };
    if size > 0.0 && ground + sea < need {
        a.water = ((ground + sea) / (size * unit)) as f32;
    }
    a.held = (ground + sea) / unit;
    (ground, sea)
}

fn air_at(w: &World, sat: &Sat, soil: f64, c: usize) -> (bool, f64, f64) {
    if w.sea[c] || w.ground[c] - soil >= POOL {
        return (true, 0.0, 0.0);
    }
    (false, (1.0 - w.vapor[c] / sat.at(w.temp[c])).clamp(0.0, 1.0), 1.0 - (w.ground[c] / soil).min(1.0))
}

/// What a log interval adds up.
#[derive(Default)]
struct Tally {
    births: u64,
    children: u64,
    sexual: u64,
    no_room: u64,
    place_k: u64, // e097 (#109): sub-cells along its ray at which a child found room, summed
    place_n: u64, // e097: children placed, the divisor of place_k
    probed: u64,  // e097: failed births the probe measured
    empty: u64, // children whose genome built no block
    hunger: u64,
    wear: u64,
    thirst: u64, // e066
    suffocation: u64, // e067
    cold: u64, // e072 (set A): deaths
    wound: u64, // e075 (#90): dead under the frail line
    warmed_by: [f64; N_MEDIA], // e072 (set A): energy paid to warm, by medium
    cooled_by: [f64; N_MEDIA], // e072 (set A): water paid to cool, by medium
    w_drunk: f64, // e081 (W1): mm the bodies took out of the ground
    w_air: f64,   // e081 (W2): mm their soft faces gave to the air
    w_sweat: f64, // e081 (W2): mm they sweated into the air
    w_dead: f64,  // e081 (W2): mm the dead gave the ground (the sea's in the sea)
    w_born: f64,  // e081 (W2): mm the children took from the ground (the sea's in the sea)
    w_spill: f64, // e081 (W2): mm lost blocks gave the ground
    born_dry: u64, // e081: children born with less than their parent's fill
    upkeep_by: [f64; N_MEDIA], // e072: the upkeep due, by medium
    wood: f64, // e072 (set B): what bodies took from the wood, in their units
    browse: f64, // e073: the part of it that was the crowns' yield
    climbed: f64, // e072 (set F): energy paid to rise
    ate_sea: f64, // #88: matter taken out of the water
    spent_land: f64, // #88: what bodies laid down on land
    spent_sea: f64,
    carried: f64, // e072 (set G): soil the runoff took along
    to_sea: f64,  // of it, what reached the sea
    inhaled_by: [u64; N_MEDIA], // e067: turns with a block over land, by medium
    drank_by: [u64; N_MEDIA], // e066: turns with a block in water, by medium
    turns_by: [u64; N_MEDIA],
    cc: Counters,
    plant: f64,
    scavenged: f64,
    actions: [u64; N_OUT],
    tried: u64,
    blocked: u64,
    stalled: u64,
    shoves: u64,
    moved: u64,
    sense_n: u64,
    sense_used: u64,
    worn: u64,
    death_ages: Vec<u32>,
    fat_spent: f64,
    fat_over: f64,
    upkept: u64,
    short: u64,
    spent: f64,
    grass_grown: f64, // e064: in the world's matter
    seed_set: f64,    // e088: in the world's matter
    seed_wet: f64,    // e090: seed that drifted onto water and sank, in the world's matter
    fruit_intake: f64, // e091 (#101 C2): what guts took from the crowns, in a body's units
    climbs: u64,       // e091 (#101 C1): times a body changed between a crown and the floor
    seed_eaten: f64,  // e089: in a body's units, as `plant`
    fiber_in: f64,
    fermented: f64,
    dung: f64,
    sprouted: f64,
    algae: f64,       // e065: of `plant`, in a body's units
    detritus: f64,
    intake_by: [f64; N_MEDIA], // e065: what bodies took from the world (not kills), on land, at the surface, on the bottom
    tried_by: [u64; N_MEDIA],
    blocked_by: [u64; N_MEDIA],
    placed_by: [u64; N_MEDIA], // children with a body, by the parent's medium
    no_room_by: [u64; N_MEDIA],
    burnt: u64,
    develops: u64,
    body_steps: u64,
    turned: u64,
    t_world: f64,
    t_bodies: f64,
    t_lineage: f64,
}

/// e097 (#109 step 0): one birth that found no room, measured. A row of `<prefix>_room.csv`.
struct RoomRow {
    step: u64,
    medium: u8,
    hab: u8,
    reach: u8,
    blocks: u16,
    hit_body: u16, // of the spots the rule tried, those a body held
    hit_wall: u16, // those a wall held (the sea a land body cannot enter, a cell with no crown)
    near: i32,     // sub-cells to the nearest spot the child fits in, -1 if none within the probe's reach
    ring: u32,     // spots with room at that distance
    axis: u32,     // of them, those on the four rays the rule searches
    free_here: u32,   // free sub-cells of the 16 in the parent's cell, in the child's layer
    free_around: u32, // the same over its eight neighbours (of 128)
}

impl RoomRow {
    fn row(&self) -> String {
        format!(
            "{},{},{},{},{},{},{},{},{},{},{},{}",
            self.step, self.medium, self.hab, self.reach, self.blocks, self.hit_body, self.hit_wall, self.near, self.ring, self.axis, self.free_here, self.free_around
        )
    }
}

/// e097: whether the child fits with its anchor (dx, dy) sub-cells from the parent's. It moves the
/// child to look, and the caller leaves it wherever the last look put it (a failed birth is laid
/// down at its parent's cell, never at its own anchor).
fn fit_at(a: &mut Agent, g: Grid, occ: &Occ, px: usize, py: usize, dx: i64, dy: i64) -> bool {
    a.x = (px as i64 + dx).rem_euclid(g.sw as i64) as usize;
    a.y = (py as i64 + dy).rem_euclid(g.sh as i64) as usize;
    a.fits(g, occ, FREE, NORTH, 0)
}

/// e097 (#109 step 1): the i-th of the 8r spots at distance r of the parent, walked around the
/// square clockwise from its top left corner; `n` is 2r, the spots on a side.
fn ring_offset(r: i64, i: i64, n: i64) -> (i64, i64) {
    let t = i % n;
    match i / n {
        0 => (-r + t, -r),
        1 => (r, -r + t),
        2 => (r - t, r),
        _ => (-r, r - t),
    }
}

/// e097 (#109 step 0): what a birth that found no room hit, and whether room was there to find. It
/// walks the rule's own spots to say what held each of them, then looks outward ring by ring - every
/// spot at the same distance, the diagonals the rule never tries among them - and stops at the first
/// distance with room. Nothing here touches the world or any stream the bodies draw from.
fn probe_room(a: &mut Agent, g: Grid, occ: &Occ, px: usize, py: usize, reach: usize, far: usize, step: u64, medium: u8, hab: u8) -> RoomRow {
    let (mut hit_body, mut hit_wall) = (0u16, 0u16);
    for d in DIRS {
        for kk in 1..=reach {
            let (cx, cy) = g.sstep(px, py, d, kk);
            a.x = cx;
            a.y = cy;
            let layer = occ.layer_for(g, a, NORTH, 0);
            let (mut body, mut wall) = (false, false);
            for pos in a.cells_held() {
                let (sx, sy) = a.sub_at(g, pos, NORTH, 0);
                match occ.at(g, sx, sy, layer) {
                    FREE => {}
                    WALL => wall = true,
                    _ => body = true,
                }
            }
            hit_wall += wall as u16;
            hit_body += (!wall && body) as u16;
        }
    }
    let (mut near, mut ring, mut axis) = (-1i32, 0u32, 0u32);
    for r in 1..=(far * reach) as i64 {
        for dx in -r..=r {
            for dy in [-r, r] {
                if fit_at(a, g, occ, px, py, dx, dy) {
                    ring += 1;
                    axis += (dx == 0) as u32;
                }
            }
        }
        for dy in -r + 1..=r - 1 {
            for dx in [-r, r] {
                if fit_at(a, g, occ, px, py, dx, dy) {
                    ring += 1;
                    axis += (dy == 0) as u32;
                }
            }
        }
        if ring > 0 {
            near = r as i32;
            break;
        }
    }
    a.x = px;
    a.y = py;
    let layer = occ.layer_for(g, a, NORTH, 0);
    let free = |dx: i64, dy: i64| -> u32 {
        let x0 = (px as i64 / SUB as i64 + dx).rem_euclid(g.w as i64) as usize * SUB;
        let y0 = (py as i64 / SUB as i64 + dy).rem_euclid(g.h as i64) as usize * SUB;
        (0..SUB_CELLS).filter(|i| occ.at(g, x0 + i % SUB, y0 + i / SUB, layer) == FREE).count() as u32
    };
    let free_around = (-1..=1i64).flat_map(|dy| (-1..=1i64).map(move |dx| (dx, dy))).filter(|&(dx, dy)| dx != 0 || dy != 0).map(|(dx, dy)| free(dx, dy)).sum();
    RoomRow { step, medium, hab, reach: reach as u8, blocks: a.body.size, hit_body, hit_wall, near, ring, axis, free_here: free(0, 0), free_around }
}

/// One log row's numbers, kept for the run's summary.
struct Point {
    step: u64,
    pop: usize,
    plant: f64,
    kills: f64,
    scavenged: f64,
    ms: [f64; 4], // a step, the world, the bodies, the lineages
    err: f64,
    pop_by: [usize; N_MEDIA], // e065: on land, at the surface, on the bottom; e091: in a crown
}

struct Sim {
    p: Params,
    sat: Sat,
    w: World,
    pl: Plants,
    g: Grid,
    occ: Occ,
    agents: Vec<Agent>,
    laws: Laws,
    rng: Rng,
    wear_rng: Rng,
    probe_rng: Rng, // e097 (#109): the probe's own stream, so a run with it is the run without it
    room: Vec<RoomRow>, // e097: the failed births it measured, since the last log row
    cache: HashMap<Vec<u16>, Body>, // bodies by gene list, for the gene lists alive
    threads: usize,
    update_i: u64,
    per_quarter: u64,
    per_year: u64,
    plant_start: u64,
    q: Quarter,
    hab: Vec<u8>, // the habitat of every cell in the last quarter (e061)
    wet: Vec<bool>,     // e066: water for a body: the sea and the pools
    dryness: Vec<f32>,  // e066: the law's dryness, 1 - the ground's fill (0 over water)
    drink_at: Vec<f32>, // e072 (set D): the share of `drink` a block over the cell gets
    vis: Vec<f32>,      // e072 (set E): the light a body standing on the cell sees by, 0 to 1
    air_sum: Vec<f64>,    // e066: the air's dryness over each cell, summed over the updates of the run
    ground_sum: Vec<f64>, // e066: the same for the ground's (1 - its fill)
    air_n: u64,
    land: usize,
    next_id: u64,
    step: u64,
    k: Tally,
    next_lineage: u32,
    seen: HashMap<u32, u32>,
    origin: HashMap<u32, u32>,
    lineages: HashMap<u32, usize>,
    born: Vec<(u32, u32)>, // since the viewer last took them
    dead: Vec<(u32, u8)>,
    pools: Pools, // e074 (#72): the genomes to seed with and the genomes to inject
    added: f64,   // e074 (#72): the matter the injected bodies brought, which the ledger reads
    felt_sum: Vec<f64>, // e078: what a body's heat reads on each cell, summed over the updates since the last band row
    over_sum: Vec<f64>, // e078: the degrees it was over `warm_hi`, summed the same way
    under_sum: Vec<f64>, // e078: and under `warm_lo`
    band_n: u32,        // e078: the updates since then
    fill_sum: Vec<f64>, // e079: the ground's fill on each land cell, summed as felt_sum
    rain_sum: Vec<f64>, // e079: the rain on each cell (mm), summed as felt_sum
    season: Option<Seasons>, // e079 (`cell_map`): every cell by quarter, over the run
    wsea: f64,  // e081: mm of water the bodies gave the sea, less what they took from it, over the run
    wclim: f64, // e081: mm the air and the land took in from the sea (its evaporation less its rain and the runoff)
    w0: f64,    // e081: the air's, the land's and the bodies' water at the start
}

/// e079 (`cell_map`): each cell's ground fill, temperature and rain summed by quarter of the year
/// (centred on the equinoxes, 0 and 2, and the solstices, 1 the north's summer, as e078's sweep).
struct Seasons {
    fill: Vec<[f64; 4]>,
    temp: Vec<[f64; 4]>,
    rain: Vec<[f64; 4]>,
    n: [u32; 4],
}

impl Sim {
    fn new(p: Params, w: World, pl: Plants, update_i: u64, threads: usize) -> Sim {
        Sim::with_pools(p, w, pl, update_i, threads, Pools::default())
    }

    fn with_pools(p: Params, w: World, pl: Plants, update_i: u64, threads: usize, pools: Pools) -> Sim {
        let n = w.n;
        let g = Grid::new(n, n);
        let (per_quarter, per_year, plant_start) = clocks(&p);
        let life = p.life as u64;
        let mut rng = Rng(life.wrapping_mul(0x9E3779B97F4A7C15) | 1);
        let mut laws = Laws::new(&mut rng, life);
        laws.history = p.history > 0.0; // e069
        laws.store_gene = p.store_gene > 0.0; // e072 (set C)
        let wear_rng = Rng(life.wrapping_mul(0xE7037ED1A0B428DB).wrapping_add(0xA0761D6478BD642F) | 1);
        let mut occ = Occ::new(g, &w.sea, p.water > 0.0);
        if p.crown_at > 0.0 {
            occ.set_crowns(g, &pl.wood, p.crown_at, p.hold); // e091 (C1): the crowns the settled world stands with
        }
        let land = w.sea.iter().filter(|&&s| !s).count();
        let mut q = Quarter::new(n * n);
        q.add(&w, &pl, p.soil);
        let hab = q.habitats(&w);
        q.clear();
        let mut sim = Sim {
            p, sat: Sat::new(), w, pl, g, occ, agents: Vec::new(), laws, rng, wear_rng, probe_rng: Rng(life.wrapping_mul(0x8EBC6AF09C88C6E3).wrapping_add(0x589965CC75374CC3) | 1), room: Vec::new(), cache: HashMap::new(), threads, update_i, per_quarter, per_year, plant_start, q, hab,
            wet: vec![false; n * n], dryness: vec![0.0; n * n], drink_at: vec![0.0; n * n], vis: vec![1.0; n * n], air_sum: vec![0.0; n * n], ground_sum: vec![0.0; n * n], air_n: 0, land,
            next_id: 0, step: 0, k: Tally::default(), next_lineage: 1, seen: HashMap::new(), origin: HashMap::new(), lineages: HashMap::new(), born: Vec::new(), dead: Vec::new(),
            pools, added: 0.0, felt_sum: vec![0.0; n * n], over_sum: vec![0.0; n * n], under_sum: vec![0.0; n * n], band_n: 0,
            fill_sum: vec![0.0; n * n], rain_sum: vec![0.0; n * n], season: None, wsea: 0.0, wclim: 0.0, w0: 0.0,
        };
        if sim.p.cell_map > 0.0 {
            sim.season = Some(Seasons { fill: vec![[0.0; 4]; n * n], temp: vec![[0.0; 4]; n * n], rain: vec![[0.0; 4]; n * n], n: [0; 4] });
        }
        sim.refresh_air(false);
        sim.populate();
        sim.w0 = sim.water_all();
        sim.wsea = 0.0; // what the start's sea bodies took from the sea is in w0
        sim
    }

    /// Where a body drinks and how dry each cell is (e066), from the climate as it stands; `count`
    /// adds the air's and the ground's dryness to their sums over the run.
    fn refresh_air(&mut self, count: bool) {
        let (fresh, light) = (self.p.fresh, self.p.light);
        let (shade_heat, shade_dry) = (self.p.shade_heat, self.p.shade_dry);
        let crown_cool = self.p.crown_cool;
        let lapse = self.p.lapse / 1000.0;
        for c in 0..self.w.n * self.w.n {
            let (wet, air, ground) = air_at(&self.w, &self.sat, self.p.soil, c);
            self.wet[c] = wet;
            self.dryness[c] = ground as f32;
            // e072 (set D): the sea gives nothing to drink, a pool all of it, wet ground a share by its
            // fill. With `fresh` 0 any water quenches (e066).
            self.drink_at[c] = if fresh <= 0.0 {
                wet as u8 as f32
            } else if self.w.sea[c] {
                0.0
            } else if wet {
                1.0
            } else {
                (fresh * (1.0 - ground)) as f32
            };
            // e072 (set E): the light a body sees by, the sun's height less the water's depth and the
            // shade of the wood standing there.
            if light > 0.0 {
                let lit = self.w.light[c] / (1.0 + depth(&self.w, &self.p, c).unwrap_or(0.0) / LIGHT_DEPTH) * (1.0 - self.pl.wood[c] / (self.pl.wood[c] + WOOD_HALF));
                self.vis[c] = (1.0 - light * (1.0 - lit.clamp(0.0, 1.0))) as f32;
            }
            if count {
                self.air_sum[c] += air;
                self.ground_sum[c] += ground;
            }
            // e078 (#91): the crown over a cell damps the day a body feels there toward its mean and
            // cuts the dryness it loses water to, both by the shade. The climate's own `temp_read` is
            // made again every update, so this is taken once from it and never piles up.
            let wood = self.pl.wood[c];
            if wood > 0.0 && (shade_heat > 0.0 || shade_dry > 0.0) {
                let shade = wood / (wood + WOOD_HALF);
                let damp = (shade_heat * shade).min(1.0);
                self.w.temp_read[c] -= damp * (self.w.temp_read[c] - self.w.temp_day[c]);
                self.dryness[c] *= (1.0 - (shade_dry * shade).min(1.0)) as f32;
            }
            // e080 (S3): the crown takes its share of the day's sun heat off what a body feels, a cooler
            // mean under it (taken from the climate's `temp_read` of this update, as e078's).
            if wood > 0.0 && crown_cool > 0.0 {
                let share = (crown_cool * wood / (wood + WOOD_HALF)).min(1.0);
                let dark = self.p.night - lapse * self.w.air[c];
                self.w.temp_read[c] -= share * (self.w.temp_day[c] - dark).max(0.0);
            }
            if count {
                self.felt_sum[c] += self.w.temp_read[c];
                self.over_sum[c] += (self.w.temp_read[c] - self.p.warm_hi).max(0.0);
                self.under_sum[c] += (self.p.warm_lo - self.w.temp_read[c]).max(0.0);
                // e079: the ground's fill and the rain, for the band rows and the map by season
                let fill = if self.w.sea[c] { 1.0 } else { (self.w.ground[c] / self.p.soil).min(1.0) };
                self.fill_sum[c] += fill;
                self.rain_sum[c] += self.w.rain_now[c];
                if let Some(se) = self.season.as_mut() {
                    let q = season_of(&self.p, self.update_i - self.plant_start);
                    se.fill[c][q] += fill;
                    se.temp[c][q] += self.w.temp[c];
                    se.rain[c][q] += self.w.rain_now[c];
                }
            }
        }
        if count {
            self.band_n += 1;
            if let Some(se) = self.season.as_mut() {
                se.n[season_of(&self.p, self.update_i - self.plant_start)] += 1;
            }
        }
        self.air_n += count as u64;
    }

    /// Random genomes on random free sub-cells, `start` per cell open to bodies (land, and the
    /// water when it is open); a body that finds no room in eight tries is not made. With a seed
    /// pool (#72) the genomes are drawn from it instead, `seed_n` of them, and each is placed where
    /// its donor stood: a world seeded with what a run had come to, and not with random bodies.
    fn populate(&mut self) {
        let g = self.g;
        let open = if self.p.water > 0.0 { g.cells() } else { self.land };
        let pool = std::mem::take(&mut self.pools.seed);
        let init = if pool.is_empty() { (self.p.start * open as f64).round() as usize } else { self.p.seed_n as usize };
        for _ in 0..init {
            let (sea, genome) = if pool.is_empty() {
                (None, (0..N).map(|_| self.rng.below(4) as u8).collect::<Vec<u8>>())
            } else {
                let d = &pool[self.rng.below(pool.len())];
                (Some(d.0 > 0), d.1.clone())
            };
            let genes = parse_genes(&genome);
            let body = develop_genes(&genes, &self.laws);
            self.next_id += 1;
            let facing = self.rng.below(4) as u8;
            let mut a = Agent::new(self.next_id - 1, genome, sorted_keys(&genes), genes.iter().map(Gene::key).collect(), body, facing, INIT_ENERGY as f64, 0);
            a.temp = (0.5 * (self.p.warm_lo + self.p.warm_hi)) as f32; // e072 (set A)
            if !a.alive {
                continue;
            }
            let tries = if sea.is_some() { 64 } else { 8 };
            let Sim { rng, occ, w, hab, agents, p, wsea, .. } = self;
            if place(&mut a, g, occ, w, hab, agents.len() as u32, sea, tries, rng) {
                if p.unit > 0.0 && p.dry > 0.0 {
                    *wsea -= water_from_ground(&mut a, g, w, p.unit).1;
                }
                agents.push(a);
            }
        }
        self.pools.seed = pool;
        self.cache = self.agents.iter().map(|a| (a.gene_ids.clone(), a.body.clone())).collect();
    }

    /// All the matter of the world: in the cells, the air, and the bodies (their energy, their fat
    /// and what their blocks are made of).
    fn matter(&self) -> f64 {
        self.pl.matter() + self.agents.iter().map(|a| a.energy.max(0.0) + a.fat + a.fiber + a.body.matter()).sum::<f64>() * self.p.scale
    }

    /// e081: all the water of the air, the land and the bodies (the sea is outside it).
    fn water_all(&self) -> f64 {
        self.w.water() + self.agents.iter().map(|a| a.held).sum::<f64>() * self.p.unit
    }

    /// e081: how far the water of the air, the land and the bodies is from what the sea's exchanges
    /// and the bodies' left it, over the run, as a share of it.
    fn water_err(&self) -> f64 {
        (self.water_all() - (self.w0 + self.wclim - self.wsea)).abs() / self.w0.max(1e-12)
    }

    fn step(&mut self) {
        self.step += 1;
        if self.p.cull_at > 0.0 && self.step == self.p.cull_at as u64 {
            self.cut();
        }
        if self.p.inject_at > 0.0 && self.step == self.p.inject_at as u64 {
            self.inject();
        }
        if (self.step - 1) % self.p.tick as u64 == 0 {
            let t = Instant::now();
            self.world();
            self.k.t_world += t.elapsed().as_secs_f64();
        }
        let t = Instant::now();
        self.bodies();
        self.k.t_bodies += t.elapsed().as_secs_f64();
    }

    /// #72's injection: `inject_n` bodies of the injection pool are put into the world where their
    /// donors stood, each marked an invader, at full water and breath and the energy a body starts
    /// with. The draw and the placement run on a stream of their own, so the resident world up to
    /// this step is the same run whatever is injected; the matter the bodies bring is added to
    /// `added`, which the ledger reads, since it comes from outside the world.
    fn inject(&mut self) {
        let g = self.g;
        let pools = std::mem::take(&mut self.pools.inject);
        let mut rng = Rng((self.p.inject_seed as u64).wrapping_mul(0x2545F4914F6CDD1D) | 1);
        let mut put = vec![0; pools.len()];
        for (i, pool) in pools.iter().enumerate() {
            for _ in 0..self.p.inject_n as usize {
                let d = &pool[rng.below(pool.len())];
                let (sea, genome) = (d.0 > 0, d.1.clone());
                let genes = parse_genes(&genome);
                let body = develop_genes(&genes, &self.laws);
                self.next_id += 1;
                let facing = rng.below(4) as u8;
                let mut a = Agent::new(self.next_id - 1, genome, sorted_keys(&genes), genes.iter().map(Gene::key).collect(), body, facing, INIT_ENERGY as f64, 0);
                a.temp = (0.5 * (self.p.warm_lo + self.p.warm_hi)) as f32;
                a.invader = i as u8 + 1;
                if !a.alive {
                    continue;
                }
                let Sim { occ, w, hab, agents, added, p, wsea, .. } = self;
                if place(&mut a, g, occ, w, hab, agents.len() as u32, Some(sea), 256, &mut rng) {
                    *added += (a.energy + a.body.matter()) * p.scale;
                    if p.unit > 0.0 && p.dry > 0.0 {
                        *wsea -= water_from_ground(&mut a, g, w, p.unit).1;
                    }
                    agents.push(a);
                    put[i] += 1;
                }
            }
        }
        self.pools.inject = pools;
        eprintln!("injected {put:?} bodies of {} each at step {}", self.p.inject_n, self.step);
    }

    /// The disturbance of #88's stability check: the largest lineage loses `cull` of its bodies, which
    /// lie down where they stand (their matter stays in the world). The world is watched from here.
    fn cut(&mut self) {
        let Sim { agents, occ, pl, g, rng, k, p, dead, w, wsea, .. } = self;
        let g = *g;
        let mut count: HashMap<u32, usize> = HashMap::new();
        for a in agents.iter() {
            *count.entry(a.lineage).or_default() += 1;
        }
        let Some((top, held)) = count.into_iter().max_by_key(|&(_, v)| v) else { return };
        let mut cut = 0u64;
        for a in agents.iter_mut() {
            if a.lineage == top && rng.f64() < p.cull {
                dead.push((a.id as u32, 1));
                occ.release(g, a);
                a.alive = false;
                lay_body(a, g, &mut pl.carrion, p.scale, &mut k.cc);
                pl.litter[a.here(g)] += a.fiber * p.scale; // e089 (Fb)
                a.fiber = 0.0;
                if p.unit > 0.0 {
                    let (ground, sea) = give_back(a, g, w, p.unit);
                    k.w_dead += ground + sea;
                    *wsea += sea;
                }
                cut += 1;
            }
        }
        agents.retain(|a| a.alive);
        for (i, a) in agents.iter().enumerate() {
            occ.relabel(g, a, i as u32);
        }
        eprintln!("cut at step {}: lineage {top} lost {cut} of its {held} bodies", self.step);
    }

    /// One update of the climate and the producers (e061, e062), and the habitats each quarter.
    fn world(&mut self) {
        let fx = self.w.update(&self.p, &self.sat, self.update_i as f64 * self.p.tick, &mut self.pl.soil, &self.pl.wood);
        self.wclim += fx.sea_evap - fx.sea_rain - fx.runoff;
        let yr = ((self.update_i - self.plant_start) / self.per_year + 1) as u32;
        self.k.carried += fx.carried;
        self.k.to_sea += fx.to_sea;
        let f = self.pl.update(&self.w, &self.p, yr);
        // e091 (C1): a crown comes with the wood and goes with it; the bodies left in one come down
        // at their turn.
        if self.p.crown_at > 0.0 {
            self.occ.set_crowns(self.g, &self.pl.wood, self.p.crown_at, self.p.hold);
        }
        // The dryness is read every update, with dry air or without (its map over the run, e066).
        self.refresh_air(true);
        self.k.burnt += f.caught as u64;
        self.k.grass_grown += f.grass;
        self.k.seed_set += f.seed;
        self.k.seed_wet += f.seed_wet;
        self.k.sprouted += f.sprout;
        self.q.add(&self.w, &self.pl, self.p.soil);
        self.update_i += 1;
        if (self.update_i - self.plant_start) % self.per_quarter == 0 {
            self.hab = self.q.habitats(&self.w);
            self.q.clear();
        }
    }

    /// One step of every body: eat and pay, decide, act, breed; then the children are developed
    /// and placed, and the dead lie down.
    fn bodies(&mut self) {
        let Sim { p, w, agents, pl, occ, g, rng, wear_rng, probe_rng, room, step: now, k, hab, wet: wet_cells, dryness, drink_at, vis, laws, cache, threads, next_id, born, dead, wsea, .. } = self;
        let g = *g;
        let s = p.scale; // a body's matter in the world's (e064)
        let open = p.water > 0.0; // the water's two layers (e065)
        let dry_on = p.dry > 0.0; // the dry air (e066)
        let unit = if dry_on { p.unit } else { 0.0 }; // e081: the body's water in the land's
        let breath_on = p.breath > 0.0; // breath in the water (e067)
        let senses_on = p.senses > 0.0; // the senses of the sensor blocks (e070)
        // e072's sets: heat (A), wood as food (B), the fat's weight (C), the light (E), the height (F).
        let heat_on = p.heat > 0.0;
        let wood_on = p.wood_food > 0.0 || p.wood_yield > 0.0; // e073: the stock share, the crown's yield, or both
        let browse_on = p.wood_yield > 0.0;
        let wood_hard = p.wood_hard as u8;
        let light_on = p.light > 0.0;
        let climb_on = p.climb > 0.0;
        let frail = p.frail; // e075 (#90): the share of its birth blocks a body must keep to live
        let seed_on = p.seed_share > 0.0; // e089 (S): seed is food behind a tooth of `seed_hard`
        let seed_hard = p.seed_hard as u8;
        let fiber_on = p.ferment > 0.0; // e089 (Fb): fiber is digested over time
        let crown_on = p.crown_at > 0.0; // e091 (#101): the crown is a place, with a food of its own
        let (probe, probe_far) = (p.probe, (p.probe_far as usize).max(1)); // e097 (#109): a measure, no law
        let (far, ring_on) = ((p.reach as usize).max(1), p.ring > 0.0); // e097 (#109 step 1): the birth rule
        let now = *now;
        let mut newborn: Vec<Agent> = Vec::new();
        let mut pending: Vec<(Agent, Option<Vec<Gene>>, usize)> = Vec::new();
        for i in 0..agents.len() {
            if !agents[i].alive {
                continue;
            }
            // The body's clock (e052, e055): between its turns nothing it does happens.
            let a = &mut agents[i];
            a.age += 1;
            k.body_steps += 1;
            // e089 (Fb): the gut's fiber ferments every step, turn or not.
            if fiber_on && a.fiber > 0.0 {
                let f = a.fiber * p.ferment;
                a.fiber -= f;
                a.energy += f;
                a.fermented += f as f32;
                k.fermented += f;
            }
            a.phase += pace(a.mass());
            if a.phase < 1.0 {
                continue;
            }
            a.phase -= 1.0;
            a.turns += 1;
            k.turned += 1;
            k.worn += wear_blocks(a, wear_chance(a.turns), wear_rng, g, occ, &mut pl.carrion, s, &mut k.cc) as u64;
            if !a.alive {
                continue;
            }
            // e091 (C1, C3): the crown a body stands in holds it while it is light enough and while
            // the stand stands. A body whose place is no longer the one it holds changes layer if
            // there is room in the other; else it keeps standing where it is and tries again next turn.
            if crown_on {
                let want = occ.layer_for(g, &agents[i], NORTH, 0);
                if want != agents[i].layer {
                    let a = &mut agents[i];
                    occ.release(g, a);
                    if a.fits_in(g, occ, i as u32, want, NORTH, 0) {
                        a.layer = want;
                        k.climbs += 1;
                    }
                    occ.claim(g, a, i as u32);
                }
            }
            let a = &mut agents[i];

            // 1. Eat: every gut block takes from the world cell under it. Then the upkeep: paid
            //    from the energy and the food, fixed in the flesh as fat (at most the body's store
            //    per unit of mass, e069), and what the energy cannot pay the fat pays (e024, e030, e042).
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
            // In the water a gut takes its layer's food (e065): the algae at the surface, what sank
            // on the bottom.
            let (layer, medium) = (a.layer, occ.medium(g, a));
            let up = layer == CROWN; // e091 (C2): in a crown a gut reaches the fruit and nothing of the floor
            let (mut plant, mut scavenged, mut wet) = (0.0f64, 0.0f64, 0.0f64);
            let (mut wood, mut browsed, mut from_sea) = (0.0f64, 0.0f64, 0.0f64);
            let mut fruits = 0.0f64;
            // e072 (set B): a body with a hard tip of force `wood_hard` behind it bites wood too.
            let bites_wood = wood_on && a.body.bite_any() >= wood_hard;
            let bites_seed = seed_on && a.body.bite_any() >= seed_hard; // e089 (S)
            let (mut seeds, mut fiber_in) = (0.0f64, 0.0f64);
            for (j, c) in guts.iter().enumerate() {
                let bite = (BITE * gut_n[j] as f32) as f64 * s;
                let (pg, dg) = if up {
                    let fr = pl.take_fruit(c, bite);
                    fruits += fr / s;
                    (fr, 0.0)
                } else if !(open && w.sea[c]) {
                    if bites_seed {
                        let (gr, dd, wd, br, sd) = pl.take_with_seed(c, bite, bites_wood, p.wood_food);
                        wood += (wd + br) / s;
                        browsed += br / s;
                        seeds += sd / s;
                        fiber_in += FIBER_LEAF * (gr + wd + br) / s;
                        (gr + wd + br + sd, dd)
                    } else if bites_wood {
                        let (gr, dd, wd, br) = pl.take_with_wood(c, bite, p.wood_food);
                        wood += (wd + br) / s;
                        browsed += br / s;
                        fiber_in += FIBER_LEAF * (gr + wd + br) / s;
                        (gr + wd + br, dd)
                    } else {
                        let (gr, dd) = pl.take(c, bite);
                        fiber_in += FIBER_LEAF * gr / s;
                        (gr, dd)
                    }
                } else if layer == SURFACE {
                    let al = pl.take_algae(c, bite);
                    fiber_in += FIBER_ALGAE * al / s;
                    (al, 0.0)
                } else {
                    let (li, dd) = pl.take_bottom(c, bite);
                    fiber_in += FIBER_LITTER * li / s;
                    (li, dd)
                };
                plant += pg / s;
                scavenged += dg / s;
                if open && w.sea[c] {
                    wet += pg / s;
                    from_sea += (pg + dg) / s; // #88: the matter a body takes out of the water
                }
            }
            a.fruit += fruits as f32;
            k.fruit_intake += fruits;
            if layer == SURFACE {
                a.algae += wet as f32;
                k.algae += wet;
            } else if layer == BOTTOM {
                a.detritus += wet as f32;
                k.detritus += wet;
            }
            let eaten = plant + scavenged;
            k.intake_by[medium] += eaten;
            // e089 (Fb): a turn passes a share of the gut's fiber as dung, litter on its cell (in the water,
            // on the bottom); what it takes in, less its fiber, is energy now, and the fiber joins the gut.
            if !fiber_on {
                fiber_in = 0.0;
            }
            if fiber_on {
                let dung = a.fiber * p.pass;
                a.fiber -= dung;
                a.dunged += dung as f32;
                k.dung += dung;
                pl.litter[a.here(g)] += dung * s;
                a.fiber += fiber_in;
                k.fiber_in += fiber_in;
            }
            a.seed += seeds as f32;
            k.seed_eaten += seeds;
            let eaten = eaten - fiber_in;
            let full = (UPKEEP * a.body.size as f32 + UPKEEP_BODY) as f64;
            let from_energy = full.min((a.energy + eaten).max(0.0));
            let gap = full - from_energy;
            let from_fat = gap.min(a.fat);
            a.short = from_fat < gap;
            a.fat += from_energy - from_fat;
            let over = (a.fat - (a.body.store * a.body.mass) as f64).max(0.0);
            a.fat -= over;
            a.energy += eaten - from_energy;
            a.plant += plant as f32;
            a.scavenged += scavenged as f32;
            a.wood += wood as f32;
            a.load = (p.fat_weight * a.fat) as f32; // e072 (set C): what the fat weighs from here
            let here = a.here(g);
            pl.soil[here] += (from_fat + over) * s;
            // #88: the channel between the land and the sea, what a body takes in the water and lays down.
            k.ate_sea += from_sea;
            k.wood += wood;
            k.browse += browsed;
            if w.sea[here] {
                k.spent_sea += from_fat + over;
            } else {
                k.spent_land += from_fat + over;
            }
            k.upkept += 1;
            k.short += a.short as u64;
            k.fat_spent += from_fat;
            k.fat_over += over;
            k.spent += from_fat + over;
            k.plant += plant;
            k.scavenged += scavenged;
            k.upkeep_by[medium] += full;

            // The air (e066): soft blocks over dry ground lose water by their open faces, blocks
            // in water drink.
            // e081 (W1, W2): out of the ground under it, and back to the air, after what its lost blocks
            // held has gone into the ground.
            if dry_on && unit > 0.0 {
                let (ground, sea) = settle(a, g, w, unit);
                k.w_spill += ground + sea;
                *wsea += sea;
                let (drank, got, given) = dry_turn_w(a, g, wet_cells, dryness, drink_at, p.dry as f32, p.drink as f32, unit, &mut w.ground, &mut w.vapor);
                k.w_drunk += got;
                k.w_air += given;
                a.drank += drank as u32;
                k.drank_by[medium] += drank as u64;
            } else if dry_on {
                let drank = dry_turn(a, g, wet_cells, dryness, drink_at, p.dry as f32, p.drink as f32);
                a.drank += drank as u32;
                k.drank_by[medium] += drank as u64;
            }
            // Breath (e067): blocks over water use it and soft faces open to the water give it
            // back; blocks over land breathe the air.
            if breath_on {
                let inhaled = breath_turn(a, g, wet_cells, p.breath as f32, p.inhale as f32);
                a.inhaled += inhaled as u32;
                k.inhaled_by[medium] += inhaled as u64;
            }
            // The heat (e072, set A): the faces pass it, the upkeep makes it, and out of its band the
            // body pays energy to warm or water to cool itself back to the band's edge. What it pays in
            // energy goes to the soil under it, as its moves do; a body that cannot pay dies of cold.
            if heat_on {
                // It goes `heat` x what it passes over its mass of the way to the temperature it would
                // hold on these cells: their mean plus the offset its own upkeep makes. The share is at
                // most all of the way, so a light body follows its cells and never overshoots them.
                let mass = a.mass().max(1e-6) as f64;
                let (pass, seen) = heat_flux(a, g, &w.temp_read, p.heat_hard, p.heat_fat);
                if pass > 0.0 {
                    let target = seen + p.heat_make * full / pass;
                    let r = (p.heat * pass / mass).min(1.0);
                    a.temp += (r * (target - a.temp as f64)) as f32;
                }
                if (a.temp as f64) < p.warm_lo {
                    let want = p.heat_spend * (p.warm_lo - a.temp as f64) * mass;
                    let paid = want.min(a.energy.max(0.0));
                    let from_fat = (want - paid).min(a.fat);
                    a.cold_short = !a.short && paid + from_fat < want;
                    a.energy -= paid;
                    a.fat -= from_fat;
                    a.temp += ((paid + from_fat) / (p.heat_spend * mass)) as f32;
                    a.warmed += (paid + from_fat) as f32;
                    k.warmed_by[medium] += paid + from_fat;
                    k.fat_spent += from_fat;
                    k.spent += paid + from_fat;
                    pl.soil[here] += (paid + from_fat) * s;
                    if w.sea[here] {
                        k.spent_sea += paid + from_fat;
                    } else {
                        k.spent_land += paid + from_fat;
                    }
                } else if (a.temp as f64) > p.warm_hi {
                    // The water it sweats leaves through its open soft faces: a closed body pays more
                    // for every degree it shifts, and cannot shed the heat its own upkeep makes.
                    let per = p.heat_sweat * mass / a.body.open_soft.max(1) as f64;
                    let want = per * (a.temp as f64 - p.warm_hi);
                    let paid = want.min(a.water.max(0.0) as f64);
                    a.water -= paid as f32;
                    // e081 (W2): the sweat goes to the air over the body.
                    if unit > 0.0 {
                        let blocks = paid * a.body.size as f64;
                        a.held -= blocks;
                        w.vapor[here] += blocks * unit;
                        k.w_sweat += blocks * unit;
                    }
                    a.temp -= (paid / per) as f32;
                    a.cooled += paid as f32;
                    k.cooled_by[medium] += paid;
                }
            }
            k.turns_by[medium] += 1;

            // 2. Decide (e023): food under the body; food and bodies ahead, behind, left and
            //    right as far as the eye's range, what lies j cells away at 1/j; energy. The
            //    knockout sees one cell (e009).
            let a = &agents[i];
            let f = a.facing as usize;
            let layer = a.layer;
            // e073: browse lies on the ground as the grass does, so a body whose tooth can take it
            // sees it. The standing wood is not sensed, as in e072: a tree is not read as food.
            let sees_browse = browse_on && a.body.bite_any() >= wood_hard;
            let sees_seed = seed_on && a.body.bite_any() >= seed_hard; // e089: seed lies on the ground as browse does
            let food = |c: usize| {
                // in the body's units (e064), of its own layer in the water (e065), of the crown it
                // stands in on land (e091)
                if layer == CROWN {
                    pl.fruit[c] / s
                } else if !(open && w.sea[c]) {
                    let browse = if sees_browse { pl.browse[c] } else { 0.0 };
                    let seed = if sees_seed { pl.seed[c] } else { 0.0 };
                    (pl.grass[c] + pl.carrion[c] + browse + seed) / s
                } else if layer == SURFACE {
                    pl.algae[c] / s
                } else {
                    (pl.litter[c] + pl.carrion[c]) / s
                }
            };
            // e066: the water in sight, as the food is seen, and the thirst.
            let water = |c: usize| if wet_cells[c] { 1.0 } else { 0.0 };
            // e070: what the body registers, through its sensor blocks when `senses` is on.
            // e072 (set E): the light where it stands is how far its sensor blocks reach.
            let lit = if light_on { vis[a.here(g)] } else { 1.0 };
            let r = sense(a, g, &food, &water, &occ.crowd, senses_on, lit);
            let (wsee, wsee_blind) = if dry_on { (Some(&r.water), Some(&r.water_blind)) } else { (None, None) };
            let short_of_breath = breath_on.then_some(r.breath); // e067
            let action = act(&a.body.policy, &a.body.water_policy, &a.body.breath_policy, &r.input, wsee, short_of_breath);
            k.actions[action] += 1;
            if a.body.kinds[SENSOR] > 0 {
                k.sense_n += 1;
                k.sense_used += (act(&a.body.policy, &a.body.water_policy, &a.body.breath_policy, &r.blind, wsee_blind, short_of_breath) != action) as u64;
            }

            // 3. Act. Forward: press on whatever is in the way (e010), shove a body lighter than
            //    the force (e015), then step one sub-cell with chance speed and a second with
            //    chance speed (e048), paying the mass moved times the distance. Turn: with room
            //    and chance speed.
            if action == 1 {
                k.tried += 1;
                k.tried_by[medium] += 1;
                let d = f;
                let pressed = push(agents, i, d, g, occ, &mut pl.carrion, s, p.flesh_bite, &mut k.cc);
                if agents[i].alive {
                    let mut work = 0.0f32;
                    for &(j, force) in &pressed {
                        if !agents[j].alive || agents[i].fits(g, occ, i as u32, d, 1) || force as f32 <= agents[j].mass() {
                            continue;
                        }
                        if agents[j].fits(g, occ, j as u32, d, 1) {
                            occ.release(g, &agents[j]);
                            let (nx, ny) = g.sstep(agents[j].x, agents[j].y, d, 1);
                            agents[j].x = nx;
                            agents[j].y = ny;
                            agents[j].layer = occ.layer_for(g, &agents[j], NORTH, 0); // e091: shoved into a crown, or out of one
                            occ.claim(g, &agents[j], j as u32);
                            k.shoves += 1;
                            work += agents[j].mass();
                        }
                    }
                    let mut moved = 0u32;
                    if agents[i].fits(g, occ, i as u32, d, 1) {
                        if stroke(agents[i].body.speed(), rng) {
                            occ.release(g, &agents[i]);
                            let (nx, ny) = g.sstep(agents[i].x, agents[i].y, d, 1);
                            agents[i].x = nx;
                            agents[i].y = ny;
                            moved = 1;
                            if rng.f32() < agents[i].body.speed() && agents[i].fits(g, occ, i as u32, d, 1) {
                                let (nx, ny) = g.sstep(nx, ny, d, 1);
                                agents[i].x = nx;
                                agents[i].y = ny;
                                moved = 2;
                            }
                            // e091 (C1, C3): the layer it lands in, which `fits` has just tested.
                            agents[i].layer = occ.layer_for(g, &agents[i], NORTH, 0);
                            occ.claim(g, &agents[i], i as u32);
                        } else {
                            k.stalled += 1;
                        }
                    } else {
                        k.blocked += 1;
                        k.blocked_by[medium] += 1;
                    }
                    k.moved += moved as u64;
                    let a = &mut agents[i];
                    a.path += moved;
                    work += a.mass() * moved as f32;
                    // e072 (set F): what it lifted itself, the rise from the cell it left to the one it
                    // stands on, in the body's units. Only on land: the water carries a body's weight.
                    let there = a.here(g);
                    let rise = if climb_on && moved > 0 && !w.sea[here] && !w.sea[there] { (w.elev[there] - w.elev[here]).max(0.0) } else { 0.0 };
                    let cost = (MOVE_COST * work) as f64 + p.climb * a.mass() as f64 * rise;
                    let paid = cost.min(a.energy.max(0.0));
                    let rest = cost - paid;
                    let from_fat = rest.min(a.fat);
                    if from_fat < rest {
                        a.short = true;
                    }
                    a.energy -= paid;
                    a.fat -= from_fat;
                    k.fat_spent += from_fat;
                    k.spent += paid + from_fat;
                    k.climbed += p.climb * a.mass() as f64 * rise;
                    pl.soil[there] += (paid + from_fat) * s;
                    if w.sea[there] {
                        k.spent_sea += paid + from_fat;
                    } else {
                        k.spent_land += paid + from_fat;
                    }
                }
            } else if action >= 2 {
                let nf = if action == 2 { left_of(f) } else { opposite(left_of(f)) };
                let a = &agents[i];
                let (list, n, _) = filled(&rotate(&a.body.cells, nf, a.body.s()), a.body.s());
                let room = list[..n as usize].iter().all(|&p| {
                    let (sx, sy) = a.sub_at(g, p as usize, NORTH, 0);
                    let o = occ.at(g, sx, sy, a.layer);
                    o == FREE || o == i as u32
                });
                if room && stroke(agents[i].body.speed(), rng) {
                    let (facing, layer) = (agents[i].facing, agents[i].layer);
                    occ.release(g, &agents[i]);
                    agents[i].facing = nf as u8;
                    agents[i].reframe();
                    // e091: turning can move the middle of the body to another cell, and with it the
                    // layer it belongs in. If the body does not fit there it stays as it was.
                    if crown_on {
                        let want = occ.layer_for(g, &agents[i], NORTH, 0);
                        if want != layer {
                            if agents[i].fits_in(g, occ, i as u32, want, NORTH, 0) {
                                agents[i].layer = want;
                                k.climbs += 1;
                            } else {
                                agents[i].facing = facing;
                                agents[i].reframe();
                            }
                        }
                    }
                    occ.claim(g, &agents[i], i as u32);
                }
            }
            if !agents[i].alive {
                continue;
            }

            // 4. Breed at the threshold: the body's share of the energy goes to the child (e069; half
            //    before); a mate within D genes among the bodies within two sub-cells of the box gives
            //    a one-point crossover.
            if agents[i].energy >= agents[i].body.threshold() as f64 {
                let mut mate = None;
                {
                    let a = &agents[i];
                    let [r0, r1, c0, c1] = a.bbox;
                    let (x0, y0) = (a.x + g.sw + c0 as usize - 2, a.y + g.sh + r0 as usize - 2);
                    'cells: for dy in 0..(r1 - r0 + 5) as usize {
                        for dx in 0..(c1 - c0 + 5) as usize {
                            let j = occ.at(g, (x0 + dx) % g.sw, (y0 + dy) % g.sh, a.layer);
                            if j == FREE || j == WALL || j as usize == i {
                                continue;
                            }
                            let m = &agents[j as usize];
                            if m.alive && a.distance(m) <= D {
                                mate = Some(j as usize);
                                break 'cells;
                            }
                        }
                    }
                }
                let mut genome = agents[i].genome.clone();
                if let Some(j) = mate {
                    let cut = rng.below(N);
                    genome[cut..].copy_from_slice(&agents[j].genome[cut..]);
                    k.sexual += 1;
                }
                let a = &mut agents[i];
                let given = a.energy * a.body.share as f64;
                a.energy -= given;
                for base in genome.iter_mut() {
                    if rng.f32() < MUTATION {
                        *base = (*base + 1 + rng.below(3) as u8) % 4;
                    }
                }
                k.children += 1;
                let genes = parse_genes(&genome);
                let gene_ids: Vec<u16> = genes.iter().map(Gene::key).collect();
                let body = cache.get(&gene_ids).cloned();
                *next_id += 1;
                let keys = sorted_keys(&genes);
                let todo = body.is_none().then_some(genes);
                let mut child = Agent::new(*next_id - 1, genome, keys, gene_ids, body.unwrap_or_else(Body::empty), rng.below(4) as u8, given, a.lineage);
                child.x = a.x;
                child.y = a.y;
                child.water = a.water; // e066: its parent's fill (e040)
                child.breath = a.breath; // e067: its parent's breath
                child.temp = a.temp; // e072 (set A): its parent's warmth
                child.invader = a.invader; // e074 (#72): the injected line is followed by its descendants
                pending.push((child, todo, i));
            }
        }

        // The children with a new gene list are developed, one development per list, on the threads.
        let mut jobs: Vec<(&[u16], &[Gene])> = Vec::new();
        for (a, genes, _) in &pending {
            if let Some(gs) = genes {
                if !jobs.iter().any(|(ids, _)| *ids == a.gene_ids.as_slice()) {
                    jobs.push((&a.gene_ids, gs));
                }
            }
        }
        k.develops += jobs.len() as u64;
        let n_threads = (*threads).min(jobs.len() / 2);
        let laws: &Laws = laws;
        let developed: Vec<Body> = if n_threads < 2 {
            jobs.iter().map(|(_, gs)| develop_genes(gs, laws)).collect()
        } else {
            let chunk = jobs.len().div_ceil(n_threads);
            std::thread::scope(|sc| {
                let hs: Vec<_> = jobs.chunks(chunk).map(|c| sc.spawn(move || c.iter().map(|(_, gs)| develop_genes(gs, laws)).collect::<Vec<Body>>())).collect();
                hs.into_iter().flat_map(|h| h.join().unwrap()).collect()
            })
        };
        for ((ids, _), b) in jobs.iter().zip(developed) {
            cache.insert(ids.to_vec(), b);
        }

        // Each child is placed at the first anchor with room, one to a grid's side of sub-cells
        // from the parent's anchor in the four directions, and the parent pays the matter of its
        // body. Without room or matter the child is never made and what it was given lies down.
        for (mut a, genes, parent) in pending.drain(..) {
            if genes.is_some() {
                a.set_body(cache[&a.gene_ids].clone());
            }
            if !a.alive {
                k.empty += 1;
                newborn.push(a);
                continue;
            }
            let (px, py) = (agents[parent].x, agents[parent].y);
            let pm = occ.medium(g, &agents[parent]);
            k.placed_by[pm] += 1;
            // e097 (#109 step 1): the rule's reach is `reach` body lengths, and with `ring` the
            // search walks every spot at a distance - the diagonals included - before going further
            // out. At reach 1 with no ring it is the rule as it always was.
            let reach = far * agents[parent].body.s().max(a.body.s());
            let start = rng.below(4);
            let mut spot = None;
            let mut at = 0; // e097 (#109): the sub-cells from its parent at which it found room
            if ring_on {
                'ring: for r in 1..=reach as i64 {
                    let n = 2 * r;
                    for j in 0..4 * n {
                        let (dx, dy) = ring_offset(r, (j + start as i64 * n) % (4 * n), n);
                        if fit_at(&mut a, g, occ, px, py, dx, dy) {
                            spot = Some((a.x, a.y));
                            at = r as usize;
                            break 'ring;
                        }
                    }
                }
            } else {
                'search: for t in 0..4 {
                    let d = DIRS[(start + t) % 4];
                    for kk in 1..=reach {
                        let (cx, cy) = g.sstep(px, py, d, kk);
                        a.x = cx;
                        a.y = cy;
                        if a.fits(g, occ, FREE, NORTH, 0) {
                            spot = Some((cx, cy));
                            at = kk;
                            break 'search;
                        }
                    }
                }
            }
            let afford = agents[parent].energy >= a.body.matter();
            match spot {
                Some((cx, cy)) if afford => {
                    a.x = cx;
                    a.y = cy;
                    a.born_at = (cx, cy);
                    a.born_hab = hab[a.here(g)];
                    a.layer = occ.layer_for(g, &a, NORTH, 0); // e091: the child's own mass says where it stands
                    occ.claim(g, &a, (agents.len() + newborn.len()) as u32);
                    agents[parent].energy -= a.body.matter();
                    agents[parent].kids += 1;
                    k.cc.born_cut += (a.body.cut > 0) as u64;
                    k.cc.not_built += a.body.cut as u64;
                    k.births += 1;
                    k.place_k += at as u64; // e097 (#109): how far out the rule had to go
                    k.place_n += 1;
                    // e081 (W2): the child's water comes out of the ground under it.
                    if unit > 0.0 {
                        let fill = a.water;
                        let (ground, sea) = water_from_ground(&mut a, g, w, unit);
                        k.w_born += ground + sea;
                        *wsea -= sea;
                        k.born_dry += (a.water < fill) as u64;
                    }
                    born.push((a.id as u32, agents[parent].id as u32));
                    newborn.push(a);
                }
                _ => {
                    k.no_room += 1;
                    k.no_room_by[pm] += 1;
                    // e097 (#109 step 0): a sample of the births with no room is measured where it failed.
                    if probe > 0.0 && spot.is_none() && probe_rng.f32() < probe as f32 {
                        k.probed += 1;
                        room.push(probe_room(&mut a, g, occ, px, py, reach, probe_far, now, pm as u8, hab[g.wcell(px, py)]));
                    }
                    lay(&mut pl.carrion, g.wcell(px, py), a.energy + a.fat, s, &mut k.cc);
                }
            }
        }
        agents.append(&mut newborn);

        // The dead leave their sub-cells and lie where they are; the list is compacted.
        for a in agents.iter_mut() {
            let cause = if !a.alive && a.worn_out {
                k.wear += 1;
                Some(2)
            } else if !a.alive {
                Some(1) // broken to its last block, or born without one
            } else if frail > 0.0 && (a.body.size as f64) < frail * a.born_size as f64 {
                k.wound += 1;
                Some(6)
            } else if a.cold_short {
                k.cold += 1;
                Some(5)
            } else if (a.energy <= 0.0 && a.fat <= 0.0) || a.short {
                k.hunger += 1;
                Some(0)
            } else if dry_on && a.water <= 0.0 {
                k.thirst += 1;
                Some(3)
            } else if breath_on && a.breath <= 0.0 {
                k.suffocation += 1;
                Some(4)
            } else {
                None
            };
            if let Some(cause) = cause {
                if a.born_size > 0 {
                    dead.push((a.id as u32, cause));
                    k.death_ages.push(a.age);
                }
                occ.release(g, a);
                a.alive = false;
                lay_body(a, g, &mut pl.carrion, s, &mut k.cc);
                // e089 (Fb): the fiber in its gut lies as litter
                pl.litter[a.here(g)] += a.fiber * s;
                k.dung += a.fiber;
                a.fiber = 0.0;
                if unit > 0.0 {
                    let (ground, sea) = give_back(a, g, w, unit);
                    k.w_dead += ground + sea;
                    *wsea += sea;
                }
            }
        }
        agents.retain(|a| a.alive);
        for (i, a) in agents.iter().enumerate() {
            occ.relabel(g, a, i as u32);
        }
    }

    /// Lineages (e006): groups connected by possible mating, single linkage at distance D, with
    /// their births, splits, merges and extinctions. As e059, less its per-place columns.
    fn detect(&mut self, events: &mut dyn Write, lineages_csv: &mut dyn Write) {
        let step = self.step;
        {
            let live: HashSet<&[u16]> = self.agents.iter().map(|a| a.gene_ids.as_slice()).collect();
            self.cache.retain(|ids, _| live.contains(ids.as_slice()));
        }
        let Sim { agents, lineages, seen, origin, next_lineage, .. } = self;
        let n = agents.len();
        let mut parent: Vec<usize> = (0..n).collect();
        fn find(p: &mut [usize], mut i: usize) -> usize {
            while p[i] != i {
                p[i] = p[p[i]];
                i = p[i];
            }
            i
        }
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
                if agents[i].distance(&agents[j]) <= D {
                    let (ri, rj) = (find(&mut parent, i), find(&mut parent, j));
                    if ri != rj {
                        parent[ri] = rj;
                    }
                }
            }
        }
        drop(reps);
        let mut members: HashMap<usize, Vec<usize>> = HashMap::new();
        for i in 0..n {
            let r = find(&mut parent, i);
            members.entry(r).or_default().push(i);
        }
        let mut groups: Vec<Vec<usize>> = members.into_values().filter(|m| m.len() >= MIN_LINEAGE).collect();
        groups.sort_by_key(|m| (std::cmp::Reverse(m.len()), agents[m[0]].id));
        let mut before: HashMap<u32, usize> = HashMap::new();
        for a in agents.iter() {
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
            let best = |confirmed: bool| votes.iter().filter(|(id, _)| lineages.contains_key(id) == confirmed).max_by_key(|(id, c)| (**c, std::cmp::Reverse(**id))).map(|(id, _)| *id);
            let inherited = best(true).or_else(|| best(false)).unwrap_or(0);
            let id = if inherited != 0 && !now.contains_key(&inherited) {
                inherited
            } else {
                let id = *next_lineage;
                *next_lineage += 1;
                origin.insert(id, inherited);
                id
            };
            now.insert(id, m.len());
            assigned.push((id, m));
        }
        seen.retain(|id, _| now.contains_key(id));
        let mut ids: Vec<u32> = now.keys().copied().collect();
        ids.sort_unstable();
        for id in ids {
            let size = now[&id];
            let c = seen.entry(id).or_insert(0);
            *c += 1;
            if *c == LINEAGE_CONFIRM && !lineages.contains_key(&id) {
                let from = origin.remove(&id).unwrap_or(0);
                writeln!(events, "{step},{},{id},{from},{size}", if from == 0 { "birth" } else { "split" }).unwrap();
                lineages.insert(id, size);
            }
        }
        let mut into: HashMap<(u32, u32), usize> = HashMap::new();
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
            let sz = m.len() as f64;
            let sum = |f: &dyn Fn(&Agent) -> f64| m.iter().map(|&i| f(&agents[i])).sum::<f64>() / sz;
            let shapes: HashSet<(u8, [u8; CELLS])> = m.iter().map(|&i| (agents[i].body.side, agents[i].body.cells)).collect();
            writeln!(
                lineages_csv,
                "{step},{id},{},{:.2},{:.2},{:.2},{:.2},{:.2},{:.2},{:.3},{:.0},{:.2},{:.2},{}",
                m.len(),
                sum(&|a| a.body.mass as f64),
                sum(&|a| a.body.kinds[HARD] as f64),
                sum(&|a| a.body.kinds[MUSCLE] as f64),
                sum(&|a| a.body.kinds[SENSOR] as f64),
                sum(&|a| a.body.kinds[DIGESTIVE] as f64),
                sum(&|a| a.body.bite_any() as f64),
                sum(&|a| (a.body.bite_any() >= TOOTH) as u8 as f64),
                sum(&|a| a.age as f64),
                sum(&|a| a.plant as f64),
                sum(&|a| a.meat() as f64),
                shapes.len()
            )
            .unwrap();
        }
        let mut carriers: HashMap<u32, usize> = HashMap::new();
        for a in agents.iter() {
            *carriers.entry(a.lineage).or_default() += 1;
        }
        let mut gone: Vec<u32> = lineages.keys().filter(|id| !carriers.contains_key(id)).copied().collect();
        gone.sort();
        for id in gone {
            let size = lineages.remove(&id).unwrap();
            let target = into.iter().filter(|((old, _), _)| *old == id).max_by_key(|((_, new), c)| (**c, std::cmp::Reverse(*new)));
            match target {
                Some(((_, new), _)) if before.get(&id).copied().unwrap_or(0) > 0 => writeln!(events, "{step},merge,{id},{new},{size}").unwrap(),
                _ => writeln!(events, "{step},extinct,{id},0,{size}").unwrap(),
            }
        }
        for (id, size) in &now {
            if let Some(s) = lineages.get_mut(id) {
                *s = *size;
            }
        }
    }

    const LOG_HEADER: &'static str = "step,pop,grown,births,children,sexual,no_room,empty,deaths_hunger,deaths_broken,deaths_wear,cells_broken,contacts,\
        plant_intake,meat_intake,kill_gain,scavenged,stay,forward,left,right,blocked,stalled,shoves,moved,turned,sense_used,\
        mass_p10,mass_p50,mass_p90,size_mean,hard_mean,muscle_mean,sensor_mean,digestive_mean,side_mean,density_mean,speed_mean,tooth,born_tooth,\
        fat_mean,on_fat,short,age_death_p50,age_death_p90,worn,cut_break,cut_wear,lineages,top_lineage,shapes,\
        pop_cold,pop_mild,pop_hot,pop_dry,pop_moist,pop_wet,travel_p50,path_mean,\
        grass,grass_grown,wood,algae,litter,carrion,air,soil_land,spent,matter,matter_err,burnt,land_temp,develops,ms_step,ms_world,ms_bodies,ms_lineage,ms_wall,\
        pop_land,pop_surface,pop_bottom,pop_crown,light_share,density_p10,density_p50,density_p90,density_land,density_surface,density_bottom,density_crown,\
        algae_intake,detritus_intake,intake_land,intake_surface,intake_bottom,intake_crown,kills_land,kills_surface,kills_bottom,kills_crown,\
        blocked_land,blocked_surface,blocked_bottom,blocked_crown,no_room_land,no_room_surface,no_room_bottom,no_room_crown,litter_sea,\
        deaths_thirst,fill_land,fill_surface,fill_bottom,fill_crown,drinking_land,drinking_surface,drinking_bottom,drinking_crown,open_land,open_surface,open_bottom,open_crown,\
        hard_land,hard_surface,hard_bottom,hard_crown,dry_air_p10,dry_air_p50,dry_air_p90,dry_ground_p10,dry_ground_p50,dry_ground_p90,pool_share,\
        deaths_suffocation,breath_land,breath_surface,breath_bottom,breath_crown,inhaling_land,inhaling_surface,inhaling_bottom,inhaling_crown,\
        breed_land,breed_surface,breed_bottom,breed_crown,share_land,share_surface,share_bottom,share_crown,store_land,store_surface,store_bottom,store_crown,fat_fill,\
        feeling,sighted,sight_front,sight_back,sight_left,sight_right,\
        deaths_cold,warm_land,warm_surface,warm_bottom,warm_crown,cool_land,cool_surface,cool_bottom,cool_crown,btemp_land,btemp_surface,btemp_bottom,btemp_crown,\
        wood_intake,climbed,ate_sea,spent_land,spent_sea,matter_land,matter_sea,carried,carried_to_sea,\
        browse,browse_intake,temp_day_land,\
        inv1,inv1_land,inv1_grown,inv2,inv2_land,inv2_grown,\
        deaths_wound,kill_intake,flesh_intake,blocks_kept,\
        water_drunk,water_air,water_sweat,water_dead,water_born,water_spill,born_dry,water_bodies,water_err,\
        seed,seed_set,sprouted,seed_wet,seed_intake,fiber_in,fermented,dung,fiber_bodies,\
        fruit,fruit_intake,climbs,\
        place_k,probed,cells_held,land_bare";

    /// The log's row for the interval of `steps` steps that ended now, and the tally reset.
    fn log_row(&mut self, steps: u64, matter0: f64, wall: f64) -> (String, Point) {
        let k = std::mem::take(&mut self.k);
        let (g, agents) = (self.g, &self.agents);
        let pop = agents.len();
        let n = pop.max(1) as f64;
        let per = steps.max(1) as f64;
        let mean = |f: &dyn Fn(&Agent) -> f64| agents.iter().map(f).sum::<f64>() / n;
        let quantile = |v: &mut Vec<f64>, q: f64| {
            v.sort_by(f64::total_cmp);
            v.get(((v.len().max(1) - 1) as f64 * q) as usize).copied().unwrap_or(0.0)
        };
        let mut masses: Vec<f64> = agents.iter().map(|a| a.body.mass as f64).collect();
        let (m10, m50, m90) = (quantile(&mut masses, 0.1), quantile(&mut masses, 0.5), quantile(&mut masses, 0.9));
        let grown: Vec<&Agent> = agents.iter().filter(|a| a.age >= GROWN).collect();
        let mut travel: Vec<f64> = grown.iter().map(|a| a.travel(g) as f64).collect();
        let travel_p50 = quantile(&mut travel, 0.5);
        let path_mean = grown.iter().map(|a| a.path as f64 / SUB as f64).sum::<f64>() / grown.len().max(1) as f64;
        let mut ages: Vec<f64> = k.death_ages.iter().map(|&a| a as f64).collect();
        let (a50, a90) = (quantile(&mut ages, 0.5), quantile(&mut ages, 0.9));
        let (mut temp_band, mut wet_band) = ([0usize; 3], [0usize; 3]);
        for a in agents {
            let h = self.hab[a.here(g)] as usize;
            if h < 9 {
                temp_band[h / 3] += 1;
                wet_band[h % 3] += 1;
            } else {
                temp_band[(h - 9) % 3] += 1;
                wet_band[2] += 1;
            }
        }
        let mut carriers: HashMap<u32, usize> = HashMap::new();
        for a in agents {
            *carriers.entry(a.lineage).or_default() += 1;
        }
        let top = self.lineages.keys().map(|id| carriers.get(id).copied().unwrap_or(0)).max().unwrap_or(0) as f64 / n;
        let shapes = agents.iter().map(|a| (a.body.side, a.body.cells)).collect::<HashSet<_>>().len();
        let (w, pl) = (&self.w, &self.pl);
        let sum = |v: &[f64]| v.iter().sum::<f64>();
        let soil_land: f64 = (0..w.n * w.n).filter(|&c| !w.sea[c]).map(|c| pl.soil[c]).sum();
        let land_temp = (0..w.n * w.n).filter(|&c| !w.sea[c]).map(|c| w.temp[c]).sum::<f64>() / self.land.max(1) as f64;
        let matter = self.matter();
        let err = (matter - matter0 - self.added).abs() / matter0; // e074: the injected bodies came from outside
        let decisions = k.actions.iter().sum::<u64>().max(1) as f64;
        let ms = [(k.t_world + k.t_bodies + k.t_lineage) * 1000.0 / per, k.t_world * 1000.0 / per, k.t_bodies * 1000.0 / per, k.t_lineage * 1000.0 / per];
        let kill_gain = k.cc.kill_gain / k.cc.cells_broken.max(1) as f64;
        let mut s = format!(
            "{},{pop},{},{},{},{},{},{},{},{},{},{},{},{:.3},{:.3},{kill_gain:.4},{:.3}",
            self.step,
            grown.len(),
            k.births,
            k.children,
            k.sexual,
            k.no_room,
            k.empty,
            k.hunger,
            k.cc.kills,
            k.wear,
            k.cc.cells_broken,
            k.cc.contacts,
            k.plant * self.p.scale,
            (k.cc.kill_gain + k.scavenged) * self.p.scale,
            k.scavenged * self.p.scale
        );
        for a in k.actions {
            s.push_str(&format!(",{:.3}", a as f64 / decisions));
        }
        s.push_str(&format!(
            ",{:.3},{:.3},{},{:.4},{:.4},{:.3},{m10:.1},{m50:.1},{m90:.1},{:.2},{:.2},{:.2},{:.2},{:.2},{:.2},{:.3},{:.3},{:.3},{:.3}",
            k.blocked as f64 / k.tried.max(1) as f64,
            k.stalled as f64 / k.tried.max(1) as f64,
            k.shoves,
            k.moved as f64 / per / n,
            k.turned as f64 / k.body_steps.max(1) as f64,
            k.sense_used as f64 / k.sense_n.max(1) as f64,
            mean(&|a| a.body.size as f64),
            mean(&|a| a.body.kinds[HARD] as f64),
            mean(&|a| a.body.kinds[MUSCLE] as f64),
            mean(&|a| a.body.kinds[SENSOR] as f64),
            mean(&|a| a.body.kinds[DIGESTIVE] as f64),
            mean(&|a| a.body.side as f64),
            mean(&|a| a.body.density as f64),
            mean(&|a| a.body.speed() as f64),
            mean(&|a| (a.body.bite_any() >= TOOTH) as u8 as f64),
            mean(&|a| (a.born_bite >= TOOTH) as u8 as f64),
        ));
        s.push_str(&format!(
            ",{:.3},{:.3},{:.4},{a50:.0},{a90:.0},{},{},{},{},{top:.3},{shapes}",
            mean(&|a| a.fat),
            mean(&|a| (a.energy <= 0.0) as u8 as f64),
            k.short as f64 / k.upkept.max(1) as f64,
            k.worn,
            k.cc.cut_break,
            k.cc.cut_wear,
            self.lineages.len()
        ));
        for v in temp_band.iter().chain(&wet_band) {
            s.push_str(&format!(",{v}"));
        }
        s.push_str(&format!(
            ",{travel_p50:.2},{path_mean:.2},{:.0},{:.4},{:.0},{:.0},{:.0},{:.1},{:.1},{soil_land:.0},{:.3},{matter:.3},{err:.2e},{:.5},{land_temp:.2},{},{:.3},{:.3},{:.3},{:.3},{:.3}",
            sum(&pl.grass),
            k.grass_grown / per,
            sum(&pl.wood),
            sum(&pl.algae),
            sum(&pl.litter),
            sum(&pl.carrion),
            pl.air,
            k.spent * self.p.scale / per,
            k.burnt as f64 / self.land.max(1) as f64,
            k.develops,
            ms[0],
            ms[1],
            ms[2],
            ms[3],
            wall * 1000.0 / per
        ));
        // e065: where the bodies live, how dense they are, and what each medium takes and meets.
        let (mut pop_by, mut dens_by) = ([0usize; N_MEDIA], [0.0f64; N_MEDIA]);
        for a in agents {
            let m = self.occ.medium(g, a);
            pop_by[m] += 1;
            dens_by[m] += a.body.density as f64;
        }
        let mut dens: Vec<f64> = agents.iter().map(|a| a.body.density as f64).collect();
        let (d10, d50, d90) = (quantile(&mut dens, 0.1), quantile(&mut dens, 0.5), quantile(&mut dens, 0.9));
        let light = agents.iter().filter(|a| a.body.layer() == SURFACE).count() as f64 / n; // e065: by density, crown or not
        let litter_sea: f64 = (0..w.n * w.n).filter(|&c| w.sea[c]).map(|c| pl.litter[c]).sum();
        s.push_str(&format!(",{},{},{},{},{light:.4},{d10:.3},{d50:.3},{d90:.3}", pop_by[0], pop_by[1], pop_by[2], pop_by[3]));
        for m in 0..N_MEDIA {
            s.push_str(&format!(",{:.3}", dens_by[m] / pop_by[m].max(1) as f64));
        }
        s.push_str(&format!(",{:.3},{:.3}", k.algae * self.p.scale, k.detritus * self.p.scale));
        for v in k.intake_by.iter().chain(&k.cc.kill_by) {
            s.push_str(&format!(",{:.3}", v * self.p.scale));
        }
        for m in 0..N_MEDIA {
            s.push_str(&format!(",{:.3}", k.blocked_by[m] as f64 / k.tried_by[m].max(1) as f64));
        }
        for m in 0..N_MEDIA {
            s.push_str(&format!(",{:.3}", k.no_room_by[m] as f64 / k.placed_by[m].max(1) as f64));
        }
        s.push_str(&format!(",{litter_sea:.0}"));
        // e066: the bodies' water and the blocks the air prices, by medium; the air's dryness and the
        // ground's over the land that is not water, spread over the cells at this step; the pools.
        let (mut fill_by, mut open_by, mut hard_by, mut size_by) = ([0.0f64; N_MEDIA], [0.0f64; N_MEDIA], [0.0f64; N_MEDIA], [0.0f64; N_MEDIA]);
        for a in agents {
            let m = self.occ.medium(g, a);
            fill_by[m] += a.water as f64;
            open_by[m] += a.body.open_soft as f64;
            hard_by[m] += a.body.kinds[HARD] as f64;
            size_by[m] += a.body.size as f64;
        }
        s.push_str(&format!(",{}", k.thirst));
        for m in 0..N_MEDIA {
            s.push_str(&format!(",{:.4}", fill_by[m] / pop_by[m].max(1) as f64));
        }
        for m in 0..N_MEDIA {
            s.push_str(&format!(",{:.4}", k.drank_by[m] as f64 / k.turns_by[m].max(1) as f64));
        }
        for m in 0..N_MEDIA {
            s.push_str(&format!(",{:.4}", open_by[m] / size_by[m].max(1.0)));
        }
        for m in 0..N_MEDIA {
            s.push_str(&format!(",{:.4}", hard_by[m] / size_by[m].max(1.0)));
        }
        let (mut air, mut ground, mut pools) = (Vec::new(), Vec::new(), 0usize);
        for c in (0..w.n * w.n).filter(|&c| !w.sea[c]) {
            let (wet, dry_air, dry_ground) = air_at(w, &self.sat, self.p.soil, c);
            if wet {
                pools += 1;
            } else {
                air.push(dry_air);
                ground.push(dry_ground);
            }
        }
        for v in [&mut air, &mut ground] {
            let (q10, q50, q90) = (quantile(&mut *v, 0.1), quantile(&mut *v, 0.5), quantile(&mut *v, 0.9));
            s.push_str(&format!(",{q10:.4},{q50:.4},{q90:.4}"));
        }
        s.push_str(&format!(",{:.5}", pools as f64 / self.land.max(1) as f64));
        // e067: the bodies' breath and the share of turns with a block over land, by medium.
        let mut breath_by = [0.0f64; N_MEDIA];
        for a in agents {
            breath_by[self.occ.medium(g, a)] += a.breath as f64;
        }
        s.push_str(&format!(",{}", k.suffocation));
        for m in 0..N_MEDIA {
            s.push_str(&format!(",{:.4}", breath_by[m] / pop_by[m].max(1) as f64));
        }
        for m in 0..N_MEDIA {
            s.push_str(&format!(",{:.4}", k.inhaled_by[m] as f64 / k.turns_by[m].max(1) as f64));
        }
        // e069: the values of a life by medium, and how full the fat is of the body's store.
        let mut life_by = [[0.0f64; N_MEDIA]; 3];
        for a in agents {
            let m = self.occ.medium(g, a);
            life_by[0][m] += a.body.breed as f64;
            life_by[1][m] += a.body.share as f64;
            life_by[2][m] += a.body.store as f64;
        }
        for v in &life_by {
            for m in 0..N_MEDIA {
                s.push_str(&format!(",{:.4}", v[m] / pop_by[m].max(1) as f64));
            }
        }
        s.push_str(&format!(",{:.4}", mean(&|a| a.fat / (a.body.store * a.body.mass).max(1e-6) as f64)));
        // e070: bodies with a sensor block, bodies with one looking out of them, and the blocks
        // looking out to the front, back, left and right.
        s.push_str(&format!(",{:.4},{:.4}", mean(&|a| (a.body.kinds[SENSOR] > 0) as u8 as f64), mean(&|a| a.body.sight.iter().any(|&v| v > 0) as u8 as f64)));
        for j in 0..4 {
            s.push_str(&format!(",{:.3}", mean(&|a| a.body.sight[j] as f64)));
        }
        // e072: what each set costs and moves. The warming is over the upkeep due, the cooling is fills
        // a turn, and the last columns are the land's and the sea's matter and what the runoff carried.
        s.push_str(&format!(",{}", k.cold));
        for m in 0..N_MEDIA {
            s.push_str(&format!(",{:.4}", k.warmed_by[m] / k.upkeep_by[m].max(1e-12)));
        }
        for m in 0..N_MEDIA {
            s.push_str(&format!(",{:.5}", k.cooled_by[m] / k.turns_by[m].max(1) as f64));
        }
        let mut temp_by = [0.0f64; N_MEDIA];
        for a in agents {
            temp_by[self.occ.medium(g, a)] += a.temp as f64;
        }
        for m in 0..N_MEDIA {
            s.push_str(&format!(",{:.2}", temp_by[m] / pop_by[m].max(1) as f64));
        }
        let (mut m_land, mut m_sea) = (0.0f64, 0.0f64);
        for c in 0..w.n * w.n {
            let v = pl.soil[c] + pl.grass[c] + pl.wood[c] + pl.browse[c] + pl.fruit[c] + pl.algae[c] + pl.litter[c] + pl.carrion[c];
            if w.sea[c] {
                m_sea += v;
            } else {
                m_land += v;
            }
        }
        s.push_str(&format!(
            ",{:.4},{:.4},{:.4},{:.4},{:.4},{m_land:.0},{m_sea:.0},{:.4},{:.4}",
            k.wood * self.p.scale,
            k.climbed * self.p.scale / per,
            k.ate_sea * self.p.scale / per,
            k.spent_land * self.p.scale / per,
            k.spent_sea * self.p.scale / per,
            k.carried / per,
            k.to_sea / per
        ));
        // e073: the browse the crowns are holding, what bodies took of it, and the land's day mean.
        let day_land = (0..w.n * w.n).filter(|&c| !w.sea[c]).map(|c| w.temp_day[c]).sum::<f64>() / self.land.max(1) as f64;
        s.push_str(&format!(",{:.1},{:.4},{day_land:.2}", sum(&pl.browse), k.browse * self.p.scale));
        // e074 (#72): the injected lines, followed by the mark their descendants carry.
        for mark in 1..=2u8 {
            let inv: Vec<&Agent> = agents.iter().filter(|a| a.invader == mark).collect();
            let land = inv.iter().filter(|a| self.occ.medium(g, a) == 0).count();
            let grown = inv.iter().filter(|a| a.age >= GROWN).count();
            s.push_str(&format!(",{},{land},{grown}", inv.len()));
        }
        // e075 (#90): the dead of their wounds, what the flesh of the living gave (`kill_intake`,
        // in the world's matter, which the log never held as a total before), what the tear itself
        // gave of it, and how much of its birth body a standing body still has.
        s.push_str(&format!(
            ",{},{:.3},{:.3},{:.4}",
            k.wound,
            k.cc.kill_gain * self.p.scale,
            k.cc.flesh_gain * self.p.scale,
            mean(&|a| a.body.size as f64 / a.born_size.max(1) as f64)
        ));
        // e081 (#94): the bodies' water flows, mm a step over the world, what they hold, and the ledger.
        s.push_str(&format!(
            ",{:.4},{:.4},{:.4},{:.4},{:.4},{:.4},{},{:.1},{:.2e}",
            k.w_drunk / per,
            k.w_air / per,
            k.w_sweat / per,
            k.w_dead / per,
            k.w_born / per,
            k.w_spill / per,
            k.born_dry,
            agents.iter().map(|a| a.held).sum::<f64>() * self.p.unit,
            self.water_err()
        ));
        // e088: the seed lying on the land, and what the grass set and what sprouted, a step.
        let seed: f64 = (0..w.n * w.n).filter(|&c| !w.sea[c]).map(|c| pl.seed[c]).sum();
        s.push_str(&format!(",{seed:.1},{:.4},{:.4},{:.4}", k.seed_set / per, k.sprouted / per, k.seed_wet / per));
        // e089: in a body's units a step, as `plant_intake`: seed eaten, fiber taken in, fermented, passed
        // as dung (the dead's included), and the fiber in the guts now.
        s.push_str(&format!(
            ",{:.3},{:.3},{:.3},{:.3},{:.1}",
            k.seed_eaten / per,
            k.fiber_in / per,
            k.fermented / per,
            k.dung / per,
            agents.iter().map(|a| a.fiber).sum::<f64>()
        ));
        // e091 (#101): the fruit standing in the crowns, what guts took from them (a body's units a
        // step, as `plant_intake`) and the times a body climbed or came down.
        s.push_str(&format!(",{:.1},{:.3},{}", pl.fruit.iter().sum::<f64>(), k.fruit_intake / per, k.climbs));
        // e097 (#109): how far out a placed child had to go, the failed births the probe measured, and
        // the ground itself - the share of the world's cells a body stands on, and of the land's none does.
        let held = (0..w.n * w.n).filter(|&c| self.occ.held(c)).count();
        let bare = (0..w.n * w.n).filter(|&c| !w.sea[c] && !self.occ.held(c)).count();
        s.push_str(&format!(
            ",{:.2},{},{:.4},{:.4}",
            k.place_k as f64 / k.place_n.max(1) as f64,
            k.probed,
            held as f64 / (w.n * w.n) as f64,
            bare as f64 / self.land.max(1) as f64
        ));
        let point = Point { step: self.step, pop, plant: k.plant, kills: k.cc.kill_gain, scavenged: k.scavenged, ms, err, pop_by };
        (s, point)
    }

    const AGENT_HEADER: &'static str = "step,id,lineage,age,turns,mass,size,side,density,born_size,born_mass,born_hard,born_muscle,born_sensor,born_digestive,born_bite,\
        hard,muscle,sensor,digestive,bite,bite_any,shell,speed,energy,fat,plant,meat,killed,scavenged,travel,path,worn,pace,place,born_place,temp,moist,height,medium,algae,detritus,water,drank,open_soft,breath,inhaled,breed,share,store,kids,btemp,warmed,cooled,wood,load,invader,cell,crown,seed,fermented,dunged,fiber,fruit,cells";

    /// e077 (#91): the land by 10-degree band of latitude and by the wood standing on a cell (lawn
    /// under 0.1, thin 0.1-1, stand from 1), with the grass grown on it since the last row, the
    /// grass and wood standing, the mean temperature now and the land's bodies on it. Resets the
    /// grass grown. e078 adds what a body's heat read there (`felt`) and its mean degrees over
    /// `warm_hi` (`over`) and under `warm_lo` (`under`), over the updates since the last row.
    fn band_rows(&mut self, step: u64, out: &mut dyn Write) {
        const BANDS: usize = 15; // -60 to 90
        let n = self.w.n;
        let mut acc = vec![[0.0f64; 13]; BANDS * 3];
        let key = |c: usize, w: &World, wood: f64| {
            let lat = w.lat_sin[c / n].asin().to_degrees();
            let b = (((lat + 60.0) / 10.0).floor().max(0.0) as usize).min(BANDS - 1);
            b * 3 + if wood < 0.1 { 0 } else if wood < 1.0 { 1 } else { 2 }
        };
        for c in 0..n * n {
            if self.w.sea[c] {
                continue;
            }
            let k = key(c, &self.w, self.pl.wood[c]);
            let r = &mut acc[k];
            r[0] += 1.0;
            r[1] += self.pl.grown[c];
            r[2] += self.pl.grass[c];
            r[3] += self.pl.wood[c];
            r[4] += self.w.temp[c];
            // e078: what a body's heat read there, and the degrees over the band's top and under its
            // bottom (what the heat law prices), over every update since the last row (a row alone
            // would see three hours of a day)
            let m = self.band_n.max(1) as f64;
            r[6] += self.felt_sum[c] / m;
            r[7] += self.over_sum[c] / m;
            r[8] += self.under_sum[c] / m;
            // e079: the ground's mean fill, and the rain over the row (mm)
            r[9] += self.fill_sum[c] / m;
            r[10] += self.rain_sum[c];
            // e088: the seed lying now, and what sprouted since the last row
            r[11] += self.pl.seed[c];
            r[12] += self.pl.sprouted[c];
        }
        for a in &self.agents {
            if self.occ.medium(self.g, a) == 0 || a.layer == CROWN {
                let c = a.here(self.g);
                acc[key(c, &self.w, self.pl.wood[c])][5] += 1.0;
            }
        }
        for (k, r) in acc.iter().enumerate() {
            if r[0] > 0.0 {
                writeln!(out, "{step},{},{},{},{:.4},{:.2},{:.2},{:.2},{},{:.2},{:.3},{:.3},{:.4},{:.3},{:.2},{:.4}", (k / 3 * 10) as i64 - 60, k % 3, r[0], r[1], r[2], r[3], r[4] / r[0], r[5], r[6] / r[0], r[7] / r[0], r[8] / r[0], r[9] / r[0], r[10] / r[0], r[11], r[12]).unwrap();
            }
        }
        self.pl.grown.iter_mut().for_each(|v| *v = 0.0);
        self.pl.sprouted.iter_mut().for_each(|v| *v = 0.0);
        self.felt_sum.iter_mut().for_each(|v| *v = 0.0);
        self.over_sum.iter_mut().for_each(|v| *v = 0.0);
        self.under_sum.iter_mut().for_each(|v| *v = 0.0);
        self.band_n = 0;
        self.fill_sum.iter_mut().for_each(|v| *v = 0.0);
        self.rain_sum.iter_mut().for_each(|v| *v = 0.0);
    }

    /// e079 (`cell_map`): every cell as little-endian f32s after "E079CELL" and the side (u32): its
    /// height (m), latitude, wood and grass now, then its ground fill, temperature and rain (mm an
    /// update) by quarter (0-3, as `season_of`), means over the run, and the year it last burnt.
    fn cell_map(&self) -> Option<Vec<u8>> {
        let se = self.season.as_ref()?;
        let n = self.w.n;
        let mut out = Vec::from(&b"E090CELL"[..]); // e090: e079's, with the seed after the grass
        out.extend_from_slice(&(n as u32).to_le_bytes());
        let mut put = |f: &dyn Fn(usize) -> f64| {
            for c in 0..n * n {
                out.extend_from_slice(&(f(c) as f32).to_le_bytes());
            }
        };
        put(&|c| self.w.elev[c]);
        put(&|c| self.w.lat_sin[c / n].asin().to_degrees());
        put(&|c| self.pl.wood[c]);
        put(&|c| self.pl.grass[c]);
        put(&|c| self.pl.seed[c]); // e090 (#100 D)
        for q in 0..4 {
            let m = se.n[q].max(1) as f64;
            put(&|c| se.fill[c][q] / m);
        }
        for q in 0..4 {
            let m = se.n[q].max(1) as f64;
            put(&|c| se.temp[c][q] / m);
        }
        for q in 0..4 {
            let m = se.n[q].max(1) as f64;
            put(&|c| se.rain[c][q] / m);
        }
        put(&|c| self.pl.burnt_in[c] as f64);
        Some(out)
    }

    /// Every body, for e060's census: `place` is the habitat of the cell under it (e061's 15).
    fn agent_rows(&self, out: &mut dyn Write) {
        let (g, w) = (self.g, &self.w);
        for a in &self.agents {
            let (b, c) = (&a.body, a.here(g));
            writeln!(
                out,
                "{},{},{},{},{},{:.2},{},{},{:.3},{},{:.2},{},{},{},{},{},{},{},{},{},{},{},{:.2},{:.3},{:.3},{:.3},{:.3},{:.3},{:.3},{:.3},{:.2},{:.2},{},{:.3},{},{},{:.1},{:.3},{:.0},{},{:.3},{:.3},{:.3},{},{},{:.3},{},{:.4},{:.4},{:.3},{},{:.2},{:.4},{:.4},{:.3},{:.2},{},{},{:.3},{:.3},{:.3},{:.3},{:.4},{:.3},{}",
                self.step,
                a.id,
                a.lineage,
                a.age,
                a.turns,
                b.mass,
                b.size,
                b.side,
                b.density,
                a.born_size,
                a.born_mass,
                a.born_kinds[HARD],
                a.born_kinds[MUSCLE],
                a.born_kinds[SENSOR],
                a.born_kinds[DIGESTIVE],
                a.born_bite,
                b.kinds[HARD],
                b.kinds[MUSCLE],
                b.kinds[SENSOR],
                b.kinds[DIGESTIVE],
                b.bite(),
                b.bite_any(),
                b.shell(),
                b.speed(),
                a.energy,
                a.fat,
                a.plant,
                a.meat(),
                a.killed,
                a.scavenged,
                a.travel(g),
                a.path as f32 / SUB as f32,
                a.worn,
                pace(a.mass()),
                self.hab[c],
                a.born_hab,
                w.temp[c],
                (w.ground[c] / self.p.soil).min(1.0),
                w.elev[c],
                self.occ.medium(g, a),
                a.algae,
                a.detritus,
                a.water,
                a.drank,
                b.open_soft,
                a.breath,
                a.inhaled,
                b.breed,
                b.share,
                b.store,
                a.kids,
                a.temp,
                a.warmed,
                a.cooled,
                a.wood,
                a.load,
                a.invader,
                c,
                self.pl.wood[c],
                a.seed,
                a.fermented,
                a.dunged,
                a.fiber,
                a.fruit,
                b.cells[..b.s() * b.s()].iter().map(|&k| (b'0' + k) as char).collect::<String>()
            )
            .unwrap();
        }
    }

    /// Every body's genome at a census (#72), for `pick.py`: the bases as digits, with the lineage
    /// and the medium the body stood in, so that a pool can put a form back where its donors were.
    fn genome_rows(&self, out: &mut dyn Write) {
        let g = self.g;
        for a in &self.agents {
            writeln!(
                out,
                "{},{},{},{},{},{}",
                self.step,
                a.id,
                a.lineage,
                self.occ.medium(g, a),
                a.invader,
                a.genome.iter().map(|&b| (b'0' + b) as char).collect::<String>()
            )
            .unwrap();
        }
    }

    /// The viewer's cell layers, in the order of `layer_specs`.
    fn layers(&self) -> Vec<Vec<f64>> {
        let (w, pl, p) = (&self.w, &self.pl, &self.p);
        let cells = w.n * w.n;
        let water = (0..cells)
            .map(|c| {
                if w.sea[c] {
                    1.0 + VIEW_SEA * (-w.elev[c] / SHALLOW).min(1.0)
                } else {
                    let s = w.ground[c] - p.soil;
                    if s > 10.0 { 1.0 + s / 1000.0 / p.relief * VIEW_RELIEF } else { 0.0 }
                }
            })
            .collect();
        let plant = (0..cells).map(|c| pl.grass[c] + pl.wood[c]).collect();
        let temp = w.temp.iter().map(|t| t + TEMP_OFFSET).collect();
        let moisture = (0..cells).map(|c| if w.sea[c] { 1.0 } else { (w.ground[c] / p.soil).min(1.0) }).collect();
        let hab = self.hab.iter().map(|&h| h as f64).collect();
        let dryness = (0..cells).map(|c| air_at(w, &self.sat, p.soil, c).2).collect();
        let mut fire = vec![0.0f64; cells];
        for &(c, _) in &pl.front {
            fire[c as usize] = 1.0;
        }
        vec![water, plant, pl.soil.clone(), temp, moisture, w.rain_now.clone(), w.light.clone(), hab, pl.grass.clone(), pl.wood.clone(), pl.algae.clone(), pl.litter.clone(), fire, pl.carrion.clone(), dryness, pl.browse.clone(), pl.seed.clone(), pl.fruit.clone()]
    }
}

fn layer_specs() -> Vec<viewer::LayerSpec> {
    use viewer::{LayerSpec, Scale};
    vec![
        LayerSpec::new("water", (1.0 + VIEW_SEA) as f32, Scale::Sqrt),
        LayerSpec::new("plant", 16.0, Scale::Sqrt),
        LayerSpec::new("soil", 20.0, Scale::Sqrt),
        // Wide enough for a land cell at noon: at a cap of 100 (-50 to +50 C) 15% of the cells sat
        // at the cap at step 42,000 of the balance world, and the map read 50 C over all of them.
        LayerSpec::new("temperature", 140.0, Scale::Linear),
        LayerSpec::new("moisture", 1.0, Scale::Linear),
        LayerSpec::new("rain", 2.0, Scale::Sqrt),
        LayerSpec::new("light", 1.0, Scale::Linear),
        LayerSpec::new("habitat", 255.0, Scale::Linear),
        LayerSpec::new("grass", 4.0, Scale::Sqrt),
        LayerSpec::new("wood", 16.0, Scale::Sqrt),
        LayerSpec::new("algae", 2.0, Scale::Sqrt),
        LayerSpec::new("litter", 8.0, Scale::Sqrt),
        LayerSpec::new("fire", 1.0, Scale::Linear),
        LayerSpec::new("carrion", 16.0, Scale::Sqrt),
        LayerSpec::new("dryness", 1.0, Scale::Linear),
        LayerSpec::new("browse", 4.0, Scale::Sqrt), // e073: what the crowns dropped
        LayerSpec::new("seed", 4.0, Scale::Sqrt), // e090: the seed bank, which drifts downwind (#100 D)
        LayerSpec::new("fruit", 1.0, Scale::Sqrt), // e091: what the crowns hold (#101 C2)
    ]
}

fn main() {
    let args: Vec<String> = std::env::args().skip(1).collect();
    let prefix = args.first().expect("usage: e070_senses <prefix> [key=value ...] [file.params ...]").clone();
    let p = parse(&args[1..]);
    if let Some(dir) = std::path::Path::new(&prefix).parent() {
        std::fs::create_dir_all(dir).ok();
    }
    let started = Instant::now();
    let (w, pl, update_i) = settled_world(&p, Some(WORLDS));
    if p.steps <= 0.0 {
        return;
    }
    let threads: usize = std::env::var("EVLOG_THREADS").ok().and_then(|s| s.parse().ok()).unwrap_or_else(|| std::thread::available_parallelism().map(|n| n.get()).unwrap_or(1)).max(1);
    // e074 (#72): the pools come by their own names, not as numbers; with neither the run is e073's.
    let pools = Pools {
        seed: std::env::var("EVLOG_POOL").ok().map_or_else(Vec::new, |f| read_pool(&f)),
        inject: std::env::var("EVLOG_INJECT").ok().map_or_else(Vec::new, |f| f.split(':').map(read_pool).collect()),
    };
    assert!(pools.inject.len() <= 2, "at most two injection pools (the log follows two marks)");
    eprintln!("pools: {} to seed with, {:?} to inject", pools.seed.len(), pools.inject.iter().map(Vec::len).collect::<Vec<_>>());
    let mut sim = Sim::with_pools(p.clone(), w, pl, update_i, threads, pools);
    eprintln!("{} bodies on {} land cells", sim.agents.len(), sim.land);

    let open = |name: &str| std::io::BufWriter::new(std::fs::File::create(format!("{prefix}_{name}")).unwrap());
    let mut log = open("log.csv");
    writeln!(log, "{}", Sim::LOG_HEADER).unwrap();
    let mut agents_csv = open("agents.csv");
    writeln!(agents_csv, "{}", Sim::AGENT_HEADER).unwrap();
    let mut bands_csv = open("bands.csv");
    writeln!(bands_csv, "step,lat,wood_class,cells,grown,grass,wood,temp,bodies,felt,over,under,fill,rain,seed,sprouted").unwrap();
    let mut events = open("events.csv");
    writeln!(events, "step,event,lineage,other,size").unwrap();
    // e097 (#109 step 0): a row per failed birth the probe measured, written as they come.
    let mut room_csv = (p.probe > 0.0).then(|| {
        let mut f = open("room.csv");
        writeln!(f, "step,medium,hab,reach,blocks,hit_body,hit_wall,near,ring,axis,free_here,free_around").unwrap();
        f
    });
    let mut lineages_csv = open("lineages.csv");
    writeln!(lineages_csv, "step,lineage,size,mass,hard,muscle,sensor,digestive,bite_any,tooth,age,plant,meat,shapes").unwrap();

    // The viewer: nothing unless EVLOG_VIEW is set. Its clock is the bodies' step.
    let n = sim.w.n;
    let height_view: Vec<f32> = sim.w.elev.iter().map(|&e| if e >= 0.0 { e / p.relief * VIEW_RELIEF } else { -VIEW_SEA * (-e / SHALLOW).min(1.0) } as f32).collect();
    let band = vec![0u8; n * n];
    let mut json = String::from("{");
    for (name, v) in Params::NAMES.iter().zip(p.values()) {
        let key = if *name == "relief" { "relief_m" } else { name };
        json.push_str(&format!("\"{key}\":{v},"));
    }
    json.push_str(&format!(
        "\"relief\":{VIEW_RELIEF},\"water_rain\":1,\"water_evap\":1,\"depth\":1,\"temperature_offset\":{TEMP_OFFSET},\"store\":{STORE},\"max_age\":0,\"habitats\":[{}]}}",
        HAB_NAMES.iter().map(|h| format!("\"{h}\"")).collect::<Vec<_>>().join(",")
    ));
    let mut view = viewer::View::from_env(
        &prefix,
        viewer::Init {
            experiment: "e070_senses",
            w: n,
            h: n,
            sub: SUB,
            height: &height_view,
            band: &band,
            layers: layer_specs(),
            globals: vec!["season", "year", "pop"],
            blocks: vec!["empty", "hard", "muscle", "sensor", "digestive"],
            deaths: CAUSES.to_vec(),
            births: true,
            params: json,
        },
    );

    let matter0 = sim.matter();
    let steps = p.steps as u64;
    let mut points: Vec<Point> = Vec::new();
    let mut last = Instant::now();
    for step in 1..=steps {
        sim.step();
        if step % LINEAGE_INTERVAL == 0 {
            let t = Instant::now();
            sim.detect(&mut events, &mut lineages_csv);
            sim.k.t_lineage += t.elapsed().as_secs_f64();
        }
        if let Some(v) = view.as_mut() {
            for (child, parent) in sim.born.drain(..) {
                v.born(step, child, parent);
            }
            for (id, cause) in sim.dead.drain(..) {
                v.died(step, id, cause);
            }
            if v.wants(step) {
                let layers = sim.layers();
                let refs: Vec<&[f64]> = layers.iter().map(|l| l.as_slice()).collect();
                let t = sim.update_i as f64 * p.tick;
                v.frame(step, &refs, &[(TAU * t / p.year).sin() as f32, (t / p.year).fract() as f32, sim.agents.len() as f32], |push| {
                    for a in &sim.agents {
                        let s = a.body.s();
                        let diet = match (a.plant > 0.0, a.meat() > 0.0) {
                            (false, false) => 3,
                            (true, false) => 0,
                            (false, true) => 2,
                            _ => 1,
                        };
                        push(viewer::AgentIn { id: a.id as u32, lineage: a.lineage, x: a.x as u16, y: a.y as u16, facing: a.facing, diet, fill: a.water.min(a.breath), energy: a.energy as f32, ripe: a.body.threshold(), fat: (a.fat / (a.body.store * a.body.mass).max(1e-6) as f64) as f32, age: a.age, born: a.born_size, side: a.body.side, cells: &a.body.cells[..s * s] });
                    }
                });
            }
            v.tick(step);
        } else {
            sim.born.clear();
            sim.dead.clear();
        }
        if step % LOG_INTERVAL == 0 {
            sim.band_rows(step, &mut bands_csv);
        }
        match room_csv.as_mut() {
            Some(f) => {
                for r in sim.room.drain(..) {
                    writeln!(f, "{}", r.row()).unwrap();
                }
            }
            None => sim.room.clear(),
        }
        if (step % AGENT_DUMP == 0 && p.census == AGENT_DUMP as f64) || (p.census != AGENT_DUMP as f64 && step % p.census as u64 == 0 && step >= p.census_from as u64) {
            sim.agent_rows(&mut agents_csv);
            if p.genomes > 0.0 && step == steps {
                let mut f = open("genomes.csv");
                writeln!(f, "step,id,lineage,medium,invader,genome").unwrap();
                sim.genome_rows(&mut f);
            }
        }
        let extinct = sim.agents.is_empty() && p.start > 0.0; // start=0: the world alone, the control
        if step % LOG_INTERVAL == 0 || extinct {
            let (line, point) = sim.log_row((step - 1) % LOG_INTERVAL + 1, matter0, last.elapsed().as_secs_f64());
            last = Instant::now();
            writeln!(log, "{line}").unwrap();
            log.flush().unwrap(); // #105: the log is what a running batch is watched by, so it goes to disk now
            if step % (10 * LOG_INTERVAL) == 0 || extinct {
                eprintln!(
                    "step {step}: {} bodies, {} lineages, {:.2} ms a step (world {:.2}, bodies {:.2}, lineages {:.2}), matter err {:.1e}",
                    point.pop, sim.lineages.len(), point.ms[0], point.ms[1], point.ms[2], point.ms[3], point.err
                );
            }
            points.push(point);
        }
        if extinct {
            eprintln!("extinct at step {step}");
            break;
        }
    }

    // The run in one row: its parameters and the second half of it.
    let last_step = points.last().map_or(0, |q| q.step);
    let late: Vec<&Point> = points.iter().filter(|q| 2 * q.step > last_step).collect();
    let m = late.len().max(1) as f64;
    let avg = |f: &dyn Fn(&Point) -> f64| late.iter().map(|q| f(q)).sum::<f64>() / m;
    let pop_mean = avg(&|q| q.pop as f64);
    let eaten = late.iter().map(|q| q.plant + q.kills + q.scavenged).sum::<f64>().max(1e-300);
    let mut header: Vec<String> = Params::NAMES.iter().map(|s| s.to_string()).collect();
    // e066: the spread over the land of each cell's dryness over the run, the air's and the ground's.
    let spread = |sum: &[f64]| {
        let mut v: Vec<f64> = (0..n * n).filter(|&c| !sim.w.sea[c]).map(|c| sum[c] / sim.air_n.max(1) as f64).collect();
        v.sort_by(f64::total_cmp);
        let q = |x: f64| v[((v.len() - 1) as f64 * x) as usize];
        format!("{:.4},{:.4},{:.4}", q(0.1), q(0.5), q(0.9))
    };
    let (air_spread, ground_spread) = (spread(&sim.air_sum), spread(&sim.ground_sum));
    for h in ["steps_run", "pop_end", "pop_mean", "pop_min", "pop_max", "kills_share", "dead_share", "ms_step", "ms_world", "ms_bodies", "ms_lineage", "us_per_body", "matter_err", "seconds", "pop_land", "pop_surface", "pop_bottom",
              "dry_air_p10", "dry_air_p50", "dry_air_p90", "dry_ground_p10", "dry_ground_p50", "dry_ground_p90"] {
        header.push(h.to_string());
    }
    let values = p.values().iter().map(|v| format!("{v}")).collect::<Vec<_>>().join(",");
    let row = format!(
        "{values},{last_step},{},{pop_mean:.1},{},{},{:.4},{:.4},{:.3},{:.3},{:.3},{:.3},{:.2},{:.2e},{:.0},{:.1},{:.1},{:.1}",
        sim.agents.len(),
        late.iter().map(|q| q.pop).min().unwrap_or(0),
        late.iter().map(|q| q.pop).max().unwrap_or(0),
        late.iter().map(|q| q.kills).sum::<f64>() / eaten,
        late.iter().map(|q| q.scavenged).sum::<f64>() / eaten,
        avg(&|q| q.ms[0]),
        avg(&|q| q.ms[1]),
        avg(&|q| q.ms[2]),
        avg(&|q| q.ms[3]),
        avg(&|q| q.ms[2]) * 1000.0 / pop_mean.max(1.0),
        points.iter().map(|q| q.err).fold(0.0, f64::max),
        started.elapsed().as_secs_f64(),
        avg(&|q| q.pop_by[0] as f64),
        avg(&|q| q.pop_by[1] as f64),
        avg(&|q| q.pop_by[2] as f64)
    ) + &format!(",{air_spread},{ground_spread}");
    std::fs::write(format!("{prefix}_row.csv"), format!("{}\n{row}\n", header.join(","))).unwrap();
    // e066: the map of the dryness over the run, in blocks of 4 x 4 cells: the land's share of the
    // block, and the mean over its land of the air's dryness and the ground's.
    let mut map = String::from("x,y,land,air,ground\n");
    for by in 0..n / 4 {
        for bx in 0..n / 4 {
            let cells: Vec<usize> = (0..16).map(|i| (4 * by + i / 4) * n + 4 * bx + i % 4).filter(|&c| !sim.w.sea[c]).collect();
            let per = (cells.len().max(1) as u64 * sim.air_n.max(1)) as f64;
            let (air, ground) = (cells.iter().map(|&c| sim.air_sum[c]).sum::<f64>() / per, cells.iter().map(|&c| sim.ground_sum[c]).sum::<f64>() / per);
            map.push_str(&format!("{bx},{by},{:.3},{air:.4},{ground:.4}\n", cells.len() as f64 / 16.0));
        }
    }
    std::fs::write(format!("{prefix}_dryness.csv"), map).unwrap();
    // e097 (#109 step 0): the ground at the end of the run, by habitat and medium - the cells a body
    // stands on, of the cells there are. What a failed birth's neighbourhood is measured against.
    if p.probe > 0.0 {
        let mut rows = String::from("hab,name,sea,cells,held\n");
        for h in 0..HAB_NAMES.len() {
            for sea in [false, true] {
                let cells: Vec<usize> = (0..n * n).filter(|&c| sim.hab[c] as usize == h && sim.w.sea[c] == sea).collect();
                if cells.is_empty() {
                    continue;
                }
                let held = cells.iter().filter(|&&c| sim.occ.held(c)).count();
                rows.push_str(&format!("{h},{},{},{},{held}\n", HAB_NAMES[h], sea as u8, cells.len()));
            }
        }
        std::fs::write(format!("{prefix}_ground.csv"), rows).unwrap();
    }
    if let Some(bytes) = sim.cell_map() {
        std::fs::write(format!("{prefix}_cells.bin"), bytes).unwrap();
    }
    let _ = Params::DOCS;
    eprintln!("done: {prefix} in {:.0} s", started.elapsed().as_secs_f64());
}

#[cfg(test)]
mod tests {
    use super::*;

    /// A small world that spins up and grows in a moment.
    fn small() -> Params {
        let mut p = Params::default();
        p.size = 32.0;
        p.grain = 16.0;
        p.land = 0.6;
        p.year = 400.0;
        p.spinup = 400.0;
        p.grow_years = 2.0;
        p.grow_steps = 0.0;
        p.ignite = 1e-3;
        p.start = 0.3;
        p
    }

    /// A world read back from its bytes goes on exactly as the one that was written.
    #[test]
    fn a_settled_world_is_read_back_as_it_was() {
        let p = small();
        let (mut w, mut pl, u) = settled_world(&p, None);
        let bytes = world_bytes(world_hash(&p), u, &w, &pl);
        let (mut w2, mut pl2, u2) = world_from(&bytes, world_hash(&p), &p).unwrap();
        assert_eq!(u, u2);
        let mut other = p.clone();
        other.grass_rate *= 2.0;
        assert!(world_from(&bytes, world_hash(&other), &other).is_none());
        let sat = Sat::new();
        let (mut soil1, mut soil2) = (pl.soil.clone(), pl2.soil.clone());
        for i in 0..300 {
            let t = (u + i) as f64 * p.tick;
            w.update(&p, &sat, t, &mut soil1, &[]);
            pl.update(&w, &p, 3);
            w2.update(&p, &sat, t, &mut soil2, &[]);
            pl2.update(&w2, &p, 3);
        }
        let bits = |v: &[f64]| v.iter().map(|x| x.to_bits()).collect::<Vec<_>>();
        assert_eq!(bits(&w.temp), bits(&w2.temp));
        assert_eq!(bits(&pl.grass), bits(&pl2.grass));
        assert_eq!(bits(&pl.litter), bits(&pl2.litter));
        assert_eq!(pl.fire_sizes, pl2.fire_sizes);
    }

    /// Bodies eat, pay, move, break, breed and die on the producers' world, which burns and rots,
    /// e097 (#109 step 1): the ring the search walks holds every spot at its distance, each once -
    /// the four the rays try among them, and the 8r - 4 they never do.
    #[test]
    fn the_ring_holds_every_spot_at_its_distance() {
        for r in 1..7i64 {
            let n = 2 * r;
            let mut spots: Vec<(i64, i64)> = (0..4 * n).map(|i| ring_offset(r, i, n)).collect();
            assert_eq!(spots.len(), 8 * r as usize);
            assert!(spots.iter().all(|&(x, y)| x.abs().max(y.abs()) == r), "a spot off the ring at r={r}");
            for &(dx, dy) in &[(0, -r), (0, r), (-r, 0), (r, 0)] {
                assert!(spots.contains(&(dx, dy)), "the rays' own spot is not on the ring at r={r}");
            }
            spots.sort();
            spots.dedup();
            assert_eq!(spots.len(), 8 * r as usize, "a spot walked twice at r={r}");
        }
    }

    /// and the world's matter neither grows nor shrinks, at a body's full scale and at a sixteenth,
    /// with the water closed and open, under dry air, where some die of thirst, with breath in the
    /// water, where some suffocate, with the values of a life read from the genome (e069), with the
    /// senses of the sensor blocks (e070), and with e072's seven sets, e073's two and e075's two
    /// (the tear and the frail line) on at once.
    #[test]
    fn matter_is_conserved_with_bodies() {
        for (scale, water, dry, breath, history, senses, sets) in [
            (1.0, 0.0, 0.0, 0.0, 0.0, 0.0, false),
            (0.0625, 0.0, 0.0, 0.0, 0.0, 0.0, false),
            (0.0625, 1.0, 0.0, 0.0, 0.0, 0.0, false),
            (0.0625, 1.0, 0.01, 0.0, 0.0, 0.0, false),
            (0.0625, 1.0, 0.01, 0.03, 0.0, 0.0, false),
            (0.0625, 1.0, 0.01, 0.03, 1.0, 0.0, false),
            (0.0625, 1.0, 0.01, 0.03, 0.0, 1.0, false),
            (0.0625, 1.0, 0.01, 0.03, 0.0, 1.0, true),
        ] {
            conserved_at(scale, water, dry, breath, history, senses, sets);
        }
    }

    #[allow(clippy::too_many_arguments)]
    fn conserved_at(scale: f64, water: f64, dry: f64, breath: f64, history: f64, senses: f64, sets: bool) {
        let mut p = small();
        p.scale = scale;
        p.water = water;
        p.dry = dry;
        p.breath = breath;
        p.history = history;
        p.senses = senses;
        if sets {
            // e072's seven sets at once, each well over the rate its dry run would give.
            p.heat = 0.05;
            p.wood_food = 0.05;
            p.fat_weight = 0.2;
            p.store_gene = 1.0;
            p.fresh = 0.3;
            p.light = 1.0;
            p.climb = 1e-4;
            p.carry = 0.05;
            // e073's two on top of them, each well over the rate its dry run would give.
            p.wood_yield = 0.002;
            p.day_temp = 1.0;
            // e075's two (#90), well over the rates the search will look at.
            p.flesh_bite = 0.2;
            p.frail = 0.8;
            // e089 (#99): seed behind a tooth and fiber digested over time, both well over the planned rates.
            p.seed_share = 0.4;
            p.seed_hard = 1.0;
            p.ferment = 0.05;
            p.pass = 0.1;
            // e090 (#100 D): the seed drifts, well over the rates the runs look at.
            p.seed_drift = 0.3;
            // e091 (#101): the crown is a place, its fruit a food, and a light body climbs into it.
            p.crown_at = 0.5;
            p.fruit_fall = 0.5;
            p.hold = 20.0;
        }
        let (w, pl, u) = settled_world(&p, None);
        let mut sim = Sim::new(p, w, pl, u, 1);
        assert!(sim.agents.len() > 50, "{} bodies", sim.agents.len());
        assert_eq!(sim.agents.iter().any(|a| a.body.share != body::SHARE), history > 0.0);
        assert_eq!(sim.agents.iter().any(|a| a.body.store != body::STORE), history > 0.0 || sets);
        if water > 0.0 {
            let mut by = [0usize; N_MEDIA];
            for a in &sim.agents {
                by[sim.occ.medium(sim.g, a)] += 1;
            }
            assert!(by[..3].iter().all(|&n| n > 0), "bodies on land, at the surface, on the bottom: {by:?}");
        }
        let start = sim.matter();
        let (mut births, mut eaten) = (0u64, 0.0f64);
        for step in 1..=3_000u64 {
            sim.step();
            births += sim.k.births;
            sim.k.births = 0;
            if step % LINEAGE_INTERVAL == 0 {
                sim.detect(&mut std::io::sink(), &mut std::io::sink());
            }
            if step % 100 == 0 {
                let m = sim.matter();
                assert!((m - start).abs() < 1e-9 * start, "step {step}: matter {start} -> {m}");
            }
        }
        eaten += sim.k.plant + sim.k.scavenged;
        assert!(births > 0 && eaten > 0.0, "births {births}, eaten {eaten}");
        if sets {
            // Every set left its mark: heat paid, wood eaten, the fat carried, a climb paid, soil carried.
            assert!(sim.k.warmed_by.iter().chain(&sim.k.cooled_by).sum::<f64>() > 0.0, "the heat cost nothing");
            assert!(sim.k.wood > 0.0, "no wood was eaten");
            assert!(sim.k.browse > 0.0, "no crown's yield was eaten");
            assert!(sim.w.temp_read.iter().zip(&sim.w.temp).any(|(r, t)| r != t), "the heat still reads the moment");
            assert!(sim.agents.iter().any(|a| a.load > 0.0), "no body carries its fat");
            assert!(sim.k.climbed > 0.0, "no body paid for a rise");
            assert!(sim.k.carried > 0.0, "the runoff carried no soil");
            // e075 (#90): the tear fed a gut and bodies died of their wounds, not to their last block.
            assert!(sim.k.cc.flesh_gain > 0.0, "no tear opened a body");
            assert!(sim.k.wound > 0, "nobody died of its wounds");
            assert!(sim.agents.iter().all(|a| a.body.size as f64 >= 0.8 * a.born_size as f64), "a body lives under the frail line");
            // e089: seed was eaten, fiber fermented and passed as dung.
            assert!(sim.k.seed_eaten > 0.0, "no seed was eaten");
            assert!(sim.k.fermented > 0.0 && sim.k.dung > 0.0, "fermented {}, dung {}", sim.k.fermented, sim.k.dung);
            // e090 (D): the seed drifted, and some of it sank in the water.
            assert!(sim.k.seed_wet > 0.0, "no seed drifted onto water");
            // e091 (#101): bodies stood in the crowns, climbed and came down, and ate their fruit.
            assert!(sim.agents.iter().any(|a| a.layer == CROWN), "no body stands in a crown");
            assert!(sim.k.climbs > 0, "no body ever changed layer");
            assert!(sim.k.fruit_intake > 0.0, "no fruit was eaten");
            // The occupancy holds: every body is in the layer it says it is and in no other, so a
            // crown's body meets nothing of the floor and the floor's meets nothing of the crown.
            for (i, a) in sim.agents.iter().enumerate() {
                for q in a.cells_held() {
                    let (sx, sy) = a.sub_at(sim.g, q, NORTH, 0);
                    assert_eq!(sim.occ.at(sim.g, sx, sy, a.layer), i as u32, "body {i} is not where it stands");
                    for l in 0..LAYERS {
                        assert!(l == a.layer || sim.occ.at(sim.g, sx, sy, l) != i as u32 || (a.layer != CROWN && l != CROWN), "body {i} holds two places");
                    }
                }
            }
        }
        assert_eq!(sim.k.thirst > 0, dry > 0.0, "deaths by thirst: {}", sim.k.thirst);
        assert_eq!(sim.k.suffocation > 0, breath > 0.0, "deaths by suffocation: {}", sim.k.suffocation);
        // With the water closed nobody stands on the sea.
        if water == 0.0 {
            for a in &sim.agents {
                for q in a.cells_held() {
                    let (sx, sy) = a.sub_at(sim.g, q, NORTH, 0);
                    assert!(!sim.w.sea[sim.g.wcell(sx, sy)]);
                }
            }
        }
    }

    /// e081 (W1, W2): with the body's water in the land's, the air's, the land's and the bodies' water
    /// moves only by the sea's exchanges and the bodies' in the sea, while bodies drink, dry, sweat,
    /// break, are born and die, and the matter is still conserved.
    #[test]
    fn the_bodies_water_is_part_of_the_land_s() {
        let mut p = small();
        (p.dry, p.breath, p.heat, p.fresh, p.flesh_bite, p.frail) = (0.01, 0.03, 0.05, 0.3, 0.2, 0.8);
        p.unit = 9.4;
        let (w, pl, u) = settled_world(&p, None);
        let mut sim = Sim::new(p, w, pl, u, 1);
        assert!(sim.w0 > 0.0 && sim.agents.iter().all(|a| a.held > 0.0 || a.water == 0.0));
        let start = sim.matter();
        let mut k = [0.0f64; 6];
        for step in 1..=3_000u64 {
            sim.step();
            if step % 100 == 0 {
                let err = sim.water_err();
                assert!(err < 1e-10, "step {step}: the water is off by {err:e}");
                let m = sim.matter();
                assert!((m - start).abs() < 1e-9 * start, "step {step}: matter {start} -> {m}");
                for (v, x) in k.iter_mut().zip([sim.k.w_drunk, sim.k.w_air, sim.k.w_sweat, sim.k.w_dead, sim.k.w_born, sim.k.w_spill]) {
                    *v += x;
                }
                sim.k = Tally::default();
            }
        }
        assert!(k.iter().all(|&v| v > 0.0), "drunk, air, sweat, dead, born, spilled: {k:?}");
        assert!(sim.w.ground.iter().all(|&v| v > -1e-9), "a ground below empty");
    }

    /// #72's instruments: a pool taken from a run seeds a new world, each body in the medium its
    /// donor stood in; an injected body is marked, its children carry the mark, and the matter it
    /// brought is in the ledger.
    #[test]
    fn a_pool_seeds_the_world_and_an_injection_is_followed() {
        let mut p = small();
        p.water = 1.0;
        p.scale = 0.0625;
        let (w, pl, u) = settled_world(&p, None);

        // A run of the world as it is, and the genomes of the bodies that bred in it: the pool.
        let mut donor = Sim::new(p.clone(), w, pl, u, 1);
        for _ in 0..1_000 {
            donor.step();
        }
        let pool: Vec<(u8, Vec<u8>)> = donor.agents.iter().filter(|a| a.kids > 0).map(|a| (donor.occ.medium(donor.g, a) as u8, a.genome.clone())).collect();
        assert!(pool.len() >= 10, "{} bodies bred", pool.len());
        let mut lines = String::from("medium,genome\n");
        for (m, genome) in &pool {
            lines.push_str(&format!("{m},{}\n", genome.iter().map(|&b| (b'0' + b) as char).collect::<String>()));
        }
        let file = std::env::temp_dir().join("e074_pool_test.csv");
        std::fs::write(&file, &lines).unwrap();
        assert_eq!(read_pool(file.to_str().unwrap()), pool);

        // A world seeded with the pool, and the same pool injected into it a few steps in.
        p.seed_n = 300.0;
        p.inject_at = 10.0;
        p.inject_n = 40.0;
        let (w, pl, u) = settled_world(&p, None);
        let pools = Pools { seed: pool.clone(), inject: vec![pool.clone()] };
        let mut sim = Sim::with_pools(p.clone(), w, pl, u, 1, pools);
        assert!(sim.agents.len() > 30, "{} bodies", sim.agents.len());
        for a in &sim.agents {
            let sea = sim.w.sea[a.here(sim.g)];
            assert!(pool.iter().any(|d| d.1 == a.genome && (d.0 > 0) == sea), "a body of the pool stands in the wrong medium");
        }

        let start = sim.matter();
        let (mut saw, mut saw_child) = (false, false);
        for step in 1..=2_000u64 {
            sim.step();
            let born_since = (step - p.inject_at as u64) as u32;
            saw |= sim.agents.iter().any(|a| a.invader > 0);
            saw_child |= sim.agents.iter().any(|a| a.invader > 0 && a.age < born_since);
            if step == p.inject_at as u64 {
                let marked = sim.agents.iter().filter(|a| a.invader > 0).count();
                assert!(marked > 0 && marked <= p.inject_n as usize, "{marked} marked of {}", p.inject_n);
                assert!(sim.added > 0.0, "the injected bodies brought no matter");
            }
            if step % LINEAGE_INTERVAL == 0 {
                sim.detect(&mut std::io::sink(), &mut std::io::sink());
            }
            let m = sim.matter();
            assert!((m - start - sim.added).abs() < 1e-9 * start, "step {step}: matter {start} -> {m}, added {}", sim.added);
        }
        // The mark reached bodies that were not injected: the line is followed by its descendants,
        // whether it lasts (this world is 32 cells a side and the line may die in it) or not.
        assert!(saw, "the injected bodies were never in the world");
        assert!(saw_child, "no child of the injected line carried the mark");
    }

    /// A gut takes the grass and the dead in their proportions, and the dead rot into the soil.
    #[test]
    fn a_gut_takes_both_foods_and_the_dead_rot() {
        let p = small();
        let (w, mut pl, _) = settled_world(&p, None);
        let c = (0..w.n * w.n).find(|&c| !w.sea[c]).unwrap();
        pl.grass[c] = 3.0;
        pl.carrion[c] = 1.0;
        let (plant, dead) = pl.take(c, 0.4);
        assert!((plant - 0.3).abs() < 1e-12 && (dead - 0.1).abs() < 1e-12);
        assert!((pl.grass[c] - 2.7).abs() < 1e-12 && (pl.carrion[c] - 0.9).abs() < 1e-12);
        let (g, d) = (pl.grass[c], pl.carrion[c]);
        assert_eq!(pl.take(c, 10.0), (g, d));
        assert_eq!((pl.grass[c], pl.carrion[c]), (0.0, 0.0));
        pl.carrion[c] = 1.0;
        let soil = pl.soil[c];
        let before = pl.matter();
        pl.update(&w, &p, 3);
        assert!((pl.carrion[c] - 0.99f64.powi(10)).abs() < 1e-12);
        assert!(pl.soil[c] > soil);
        assert!((pl.matter() - before).abs() < 1e-9 * before);
    }

    /// e073: a stand of wood drops browse per unit of what it stands, out of its cell's soil, and
    /// the trunk is not touched; browse uneaten rots into the soil as the litter does. Matter holds.
    #[test]
    fn the_crowns_drop_browse_and_it_rots() {
        let mut p = small();
        let (w, mut pl, _) = settled_world(&p, None);
        let c = (0..w.n * w.n).find(|&c| !w.sea[c] && pl.wood[c] > 0.1).unwrap();
        let (wood, browse0, before) = (pl.wood[c], pl.browse[c], pl.matter());
        p.wood_yield = 0.001;
        pl.update(&w, &p, 3);
        // What the crowns dropped: the rate over the stand and the update, less what rotted away.
        assert!(pl.browse[c] > browse0, "the crowns dropped nothing: {} -> {}", browse0, pl.browse[c]);
        assert!(pl.browse[c] <= p.wood_yield * p.tick * wood + 1e-12);
        assert!((pl.matter() - before).abs() < 1e-9 * before, "matter moved");
        // The stand itself only grew and died as it would with no yield at all.
        let (w2, mut pl2, _) = settled_world(&p, None);
        p.wood_yield = 0.0;
        pl2.update(&w2, &p, 3);
        assert!((pl.wood[c] - pl2.wood[c]).abs() < 1e-12, "the yield felled the trunk");
        // With nothing eating it, browse rots into the soil where the ground is warm and wet.
        let held = pl.browse[c];
        p.wood_yield = 0.0;
        for _ in 0..200 {
            pl.update(&w, &p, 3);
        }
        assert!(pl.browse[c] < held, "browse never rots: {held} -> {}", pl.browse[c]);
    }

    /// e091 (#101 C2): a cell with a crown keeps `1 - fruit_fall` of its drop up there as fruit and
    /// lets the rest down as browse; a cell under `crown_at` drops all of it as browse, as in e073.
    /// Fruit uneaten rots into the soil, and matter holds through all of it.
    #[test]
    fn the_crown_keeps_its_yield_and_the_floor_gets_what_falls() {
        let mut p = small();
        p.crown_at = 1.0;
        p.fruit_fall = 0.25;
        let (w, mut pl, _) = settled_world(&p, None); // settled with no yield: nothing has dropped yet
        p.wood_yield = 0.001;
        let stand = (0..w.n * w.n).find(|&c| !w.sea[c] && pl.wood[c] >= 1.0).unwrap();
        let lawn = (0..w.n * w.n).find(|&c| !w.sea[c] && pl.wood[c] > 0.01 && pl.wood[c] < 1.0).unwrap();
        let (wood, before) = (pl.wood[stand], pl.matter());
        pl.update(&w, &p, 3);
        let drop = p.wood_yield * p.tick * wood;
        assert!((pl.fruit[stand] - 0.75 * drop).abs() < 1e-6 * drop, "the crown kept {} of {drop}", pl.fruit[stand]);
        assert!((pl.browse[stand] - 0.25 * drop).abs() < 1e-6 * drop, "the floor got {}", pl.browse[stand]);
        assert_eq!(pl.fruit[lawn], 0.0, "a cell with no crown keeps nothing up");
        assert!(pl.browse[lawn] > 0.0);
        assert!((pl.matter() - before).abs() < 1e-9 * before, "matter moved");
        // A gut in the crown takes the fruit and nothing else of the cell; what is left rots away.
        let (held, grass) = (pl.fruit[stand], pl.grass[stand]);
        let took = pl.take_fruit(stand, held / 2.0);
        assert!((took - held / 2.0).abs() < 1e-12 && (pl.fruit[stand] - held / 2.0).abs() < 1e-12);
        assert_eq!(pl.grass[stand], grass);
        p.wood_yield = 0.0;
        let left = pl.fruit[stand];
        for _ in 0..200 {
            pl.update(&w, &p, 3);
        }
        assert!(pl.fruit[stand] < left, "fruit never rots: {left} -> {}", pl.fruit[stand]);
    }

    /// e073: the climate keeps a running mean of a cell's temperature over the last day, and what a
    /// body reads is `day_temp` of the way from the moment to it. At 0 it is the moment exactly.
    #[test]
    fn the_day_s_mean_lags_the_moment() {
        let mut p = small();
        p.day_temp = 0.0;
        let (mut w, _, _) = settled_world(&p, None);
        let sat = climate::Sat::new();
        let mut soil = vec![0.0; w.n * w.n];
        let c = (0..w.n * w.n).find(|&c| !w.sea[c]).unwrap();
        let (mut lo, mut hi) = (f64::INFINITY, f64::NEG_INFINITY);
        let (mut lo_day, mut hi_day) = (f64::INFINITY, f64::NEG_INFINITY);
        for i in 0..400 {
            w.update(&p, &sat, i as f64 * p.tick, &mut soil, &[]);
            assert_eq!(w.temp_read[c], w.temp[c], "day_temp 0 is the moment");
            if i > 200 {
                lo = lo.min(w.temp[c]);
                hi = hi.max(w.temp[c]);
                lo_day = lo_day.min(w.temp_day[c]);
                hi_day = hi_day.max(w.temp_day[c]);
            }
        }
        assert!(hi_day - lo_day < hi - lo, "the mean swings as wide as the moment");
        p.day_temp = 1.0;
        w.update(&p, &sat, 400.0 * p.tick, &mut soil, &[]);
        assert!((w.temp_read[c] - w.temp_day[c]).abs() < 1e-12, "day_temp 1 is the day's mean");
        p.day_temp = 0.5;
        w.update(&p, &sat, 401.0 * p.tick, &mut soil, &[]);
        assert!((w.temp_read[c] - 0.5 * (w.temp[c] + w.temp_day[c])).abs() < 1e-12, "day_temp 0.5 is half way");
    }

    /// e078 (#91): a crown damps what a body's heat reads toward the day's mean and cuts the dryness,
    /// both by its shade and at most all the way; a cell without wood is left as it was.
    #[test]
    fn a_crown_damps_the_day_and_the_dry() {
        let p = small();
        let (w, pl, u) = settled_world(&p, None);
        let mut sim = Sim::new(p, w, pl, u, 1);
        let land: Vec<usize> = (0..sim.w.n * sim.w.n).filter(|&c| !sim.w.sea[c] && !sim.wet[c] && sim.dryness[c] > 0.0).collect();
        let (c, bare) = (land[0], land[1]);
        sim.pl.wood[c] = WOOD_HALF; // a shade of one half
        sim.pl.wood[bare] = 0.0;
        let read = sim.w.temp_read.clone();
        let (moment, mean, dry) = (read[c], sim.w.temp_day[c], sim.dryness[c]);
        assert!((moment - mean).abs() > 1e-6, "the moment is the day's mean");
        let with = |sim: &mut Sim, k: f64, k2: f64| {
            sim.w.temp_read.copy_from_slice(&read);
            sim.p.shade_heat = k;
            sim.p.shade_dry = k2;
            sim.refresh_air(false);
            (sim.w.temp_read[c], sim.dryness[c], sim.w.temp_read[bare], sim.dryness[bare])
        };
        let (t, d, tb, db) = with(&mut sim, 0.0, 0.0);
        assert_eq!((t, d), (moment, dry), "rates 0 change nothing");
        let (t1, d1, tb1, db1) = with(&mut sim, 1.0, 1.0);
        assert!((t1 - 0.5 * (moment + mean)).abs() < 1e-12, "k 1 under a shade of 1/2 is half way");
        assert!((d1 - 0.5 * dry).abs() < 1e-6, "k2 1 under a shade of 1/2 halves the dryness");
        assert_eq!((tb1, db1), (tb, db), "a bare cell is left as it was");
        let (t3, d3, _, _) = with(&mut sim, 3.0, 3.0);
        assert!((t3 - mean).abs() < 1e-12 && d3 == 0.0, "at most all the way");
    }

    /// e072 (set B): a gut with a hard enough tooth takes the grass, the dead and its share of the
    /// wood in their proportions; the share is what stands between wood and a body without the tooth.
    #[test]
    fn a_tooth_makes_the_wood_food() {
        let p = small();
        let (w, mut pl, _) = settled_world(&p, None);
        let c = (0..w.n * w.n).find(|&c| !w.sea[c]).unwrap();
        pl.grass[c] = 1.0;
        pl.carrion[c] = 1.0;
        pl.wood[c] = 8.0;
        // At a share of 0.25 the wood offers 2 against the grass's 1 and the dead's 1: half a bite.
        let (grass, dead, wood, browse) = pl.take_with_wood(c, 0.4, 0.25);
        assert!((grass - 0.1).abs() < 1e-12 && (dead - 0.1).abs() < 1e-12 && (wood - 0.2).abs() < 1e-12 && browse == 0.0);
        assert!((pl.wood[c] - 7.8).abs() < 1e-12);
        // A bite larger than what is offered takes all of the offer and no more.
        let (grass, dead, wood, _) = pl.take_with_wood(c, 100.0, 0.25);
        assert!((grass - 0.9).abs() < 1e-12 && (dead - 0.9).abs() < 1e-12 && (wood - 7.8 * 0.25).abs() < 1e-12);
        assert!(pl.wood[c] > 5.0 && pl.grass[c].abs() < 1e-12);
        // The tooth is e010's rule: the muscle behind a hard tip, on any side of the body. A hard tip
        // with three muscles behind it bites wood at wood_hard 3; two of them, or no hard tip, do not.
        let line = |muscles: usize, tip: bool| {
            let mut cells = [0u8; body::CELLS];
            cells[0] = if tip { HARD as u8 } else { MUSCLE as u8 };
            for q in 1..=muscles {
                cells[q * SIDE] = MUSCLE as u8;
            }
            Body::new(cells, SIDE, [0.0; N_POLICY], 0, 1.0).bite_any()
        };
        assert_eq!(line(3, true), 3);
        assert_eq!(line(2, true), 2);
        assert_eq!(line(3, false), 0);
    }

    /// e072 (set G): the water running off a land cell takes some of its soil into the cell below,
    /// and into the sea at the coast; nothing is made or lost.
    #[test]
    fn the_runoff_carries_soil() {
        let mut p = small();
        p.carry = 0.05;
        let (mut w, mut pl, u) = settled_world(&p, None);
        let sat = Sat::new();
        // Fill the land's ground so that water stands on it and runs.
        for c in 0..w.n * w.n {
            if !w.sea[c] {
                w.ground[c] = p.soil + 400.0;
            }
        }
        let before: f64 = pl.soil.iter().sum();
        let land_before: f64 = (0..w.n * w.n).filter(|&c| !w.sea[c]).map(|c| pl.soil[c]).sum();
        let mut carried = 0.0;
        for i in 0..20 {
            carried += w.update(&p, &sat, (u + i) as f64 * p.tick, &mut pl.soil, &pl.wood).carried;
        }
        let after: f64 = pl.soil.iter().sum();
        let land_after: f64 = (0..w.n * w.n).filter(|&c| !w.sea[c]).map(|c| pl.soil[c]).sum();
        assert!(carried > 0.0, "the runoff carried nothing");
        assert!((after - before).abs() < 1e-9 * before, "soil {before} -> {after}");
        assert!(land_after < land_before, "the land kept all its soil: {land_before} -> {land_after}");
        // With carry 0 the soil does not move at all (e070).
        let (mut w0, mut pl0, u0) = settled_world(&small(), None);
        for c in 0..w0.n * w0.n {
            if !w0.sea[c] {
                w0.ground[c] = p.soil + 400.0;
            }
        }
        let keep = pl0.soil.clone();
        for i in 0..20 {
            w0.update(&small(), &sat, (u0 + i) as f64 * p.tick, &mut pl0.soil, &pl0.wood);
        }
        assert_eq!(keep, pl0.soil);
    }

    /// In the water the surface takes the algae and the bottom what sank (the algae's litter and
    /// the carrion), and with the water open the algae's dead lie on the bottom as litter.
    #[test]
    fn the_water_feeds_each_layer_its_own() {
        let p = small();
        let (w, mut pl, _) = settled_world(&p, None);
        let c = (0..w.n * w.n).filter(|&c| w.sea[c]).max_by(|&a, &b| w.temp[a].total_cmp(&w.temp[b])).unwrap();
        pl.algae[c] = 0.5;
        pl.litter[c] = 3.0;
        pl.carrion[c] = 1.0;
        assert!((pl.take_algae(c, 0.2) - 0.2).abs() < 1e-12 && (pl.algae[c] - 0.3).abs() < 1e-12);
        let (litter, dead) = pl.take_bottom(c, 0.4);
        assert!((litter - 0.3).abs() < 1e-12 && (dead - 0.1).abs() < 1e-12);
        let left = pl.algae[c];
        assert_eq!((pl.take_algae(c, 1.0), pl.algae[c]), (left, 0.0));
        pl.algae[c] = 1.0;
        let lit = pl.litter[c];
        let mut closed = Plants::new(&w, &p);
        (closed.grass, closed.wood, closed.algae, closed.litter, closed.soil) = (pl.grass.clone(), pl.wood.clone(), pl.algae.clone(), pl.litter.clone(), pl.soil.clone());
        let before = pl.matter();
        pl.update(&w, &p, 3);
        assert!(pl.litter[c] > lit, "{} -> {}", lit, pl.litter[c]);
        assert!((pl.matter() - before).abs() < 1e-9 * before);
        closed.update(&w, &Params { water: 0.0, ..p.clone() }, 3);
        // The same rot from the same litter: what differs is the algae's dead of an update.
        assert!((pl.litter[c] - closed.litter[c] - p.tick / plants::ALGAE_LIFE).abs() < 1e-12);
    }

    /// e079 (S1): a crown cuts what its ground gives to the air, by its shade; with no crown or at
    /// `crown_wet` 0 the ground dries as before.
    #[test]
    fn a_crown_keeps_its_ground_wet() {
        let p = Params { crown_wet: 1.0, ..small() };
        let (w0, pl, u) = settled_world(&p, None);
        let sat = Sat::new();
        let cells = w0.n * w0.n;
        let land: Vec<usize> = (0..cells).filter(|&c| !w0.sea[c]).collect();
        let bare = vec![0.0; cells];
        let crowned = vec![4.0; cells]; // a shade of one half
        let mut soil = pl.soil.clone();
        let (mut a, mut b, mut c0) = (World::new(&p), World::new(&p), World::new(&p));
        for w in [&mut a, &mut b, &mut c0] {
            (w.temp, w.vapor, w.ground) = (w0.temp.clone(), w0.vapor.clone(), w0.ground.clone());
        }
        let fa = a.update(&p, &sat, u as f64 * p.tick, &mut soil.clone(), &bare);
        let fb = b.update(&p, &sat, u as f64 * p.tick, &mut soil, &crowned);
        let fc = c0.update(&Params { crown_wet: 0.0, ..p.clone() }, &sat, u as f64 * p.tick, &mut pl.soil.clone(), &crowned);
        assert!(fa.land_evap > 0.0, "the land gave nothing to the air");
        assert!((fb.land_evap - 0.5 * fa.land_evap).abs() < 1e-9 * fa.land_evap, "evaporation {} against {} bare", fb.land_evap, fa.land_evap);
        assert_eq!(fa.land_evap, fc.land_evap);
        assert!(land.iter().map(|&c| b.ground[c]).sum::<f64>() > land.iter().map(|&c| a.ground[c]).sum::<f64>());
    }

    /// e079 (S2): at `wood_rest` 1 wood does not die where it is too cold to grow, and dies at the
    /// full rate where it is warm; at 0 it dies at one rate in both.
    #[test]
    fn wood_rests_in_the_cold() {
        let p = small();
        let (mut w, pl0, _) = settled_world(&p, None);
        let cells = w.n * w.n;
        let land: Vec<usize> = (0..cells).filter(|&c| !w.sea[c]).collect();
        let (cold, warm) = (land[0], land[1]);
        w.light = vec![0.0; cells]; // no growth anywhere: what changes is the death
        w.temp[cold] = plants::WARM_FROM - 10.0;
        w.temp[warm] = plants::WARM_FULL + 5.0;
        for (rest, cold_dies) in [(1.0, false), (0.0, true)] {
            let p = Params { wood_rest: rest, ..p.clone() };
            let mut pl = Plants::new(&w, &p);
            (pl.wood, pl.soil) = (pl0.wood.clone(), pl0.soil.clone());
            pl.wood[cold] = 2.0;
            pl.wood[warm] = 2.0;
            let before = pl.matter();
            pl.update(&w, &p, 3);
            assert_eq!(pl.wood[cold] < 2.0, cold_dies, "wood_rest {rest}: cold wood {}", pl.wood[cold]);
            assert!((pl.wood[warm] - 2.0 * (1.0 - p.tick / plants::WOOD_LIFE)).abs() < 1e-12, "warm wood {}", pl.wood[warm]);
            assert!((pl.matter() - before).abs() < 1e-9 * before);
        }
    }

    /// e080 (S3): a crown lowers what a body's heat reads by its share of the day's sun heat, the day's
    /// mean over the cell's dark equilibrium; a bare cell and `crown_cool` 0 are left as they were.
    #[test]
    fn a_crown_takes_its_share_of_the_sun() {
        let p = small();
        let (w, pl, u) = settled_world(&p, None);
        let mut sim = Sim::new(p, w, pl, u, 1);
        let land: Vec<usize> = (0..sim.w.n * sim.w.n).filter(|&c| !sim.w.sea[c]).collect();
        let (c, bare) = (land[0], land[1]);
        sim.pl.wood[c] = WOOD_HALF; // a shade of one half
        sim.pl.wood[bare] = 0.0;
        let read = sim.w.temp_read.clone();
        let sun = sim.w.temp_day[c] - (sim.p.night - sim.p.lapse / 1000.0 * sim.w.air[c]);
        assert!(sun > 1.0, "no sun heat on the cell: {sun}");
        let with = |sim: &mut Sim, c3: f64| {
            sim.w.temp_read.copy_from_slice(&read);
            sim.p.crown_cool = c3;
            sim.refresh_air(false);
            (sim.w.temp_read[c], sim.w.temp_read[bare])
        };
        assert_eq!(with(&mut sim, 0.0), (read[c], read[bare]), "0 changes nothing");
        let (t, tb) = with(&mut sim, 0.2);
        assert!((read[c] - t - 0.1 * sun).abs() < 1e-9, "0.2 under a shade of 1/2 takes a tenth: {} against {}", read[c] - t, 0.1 * sun);
        assert_eq!(tb, read[bare], "a bare cell is left as it was");
        let (t4, _) = with(&mut sim, 4.0);
        assert!((read[c] - t4 - sun).abs() < 1e-9, "at most all of it");
    }

    /// e088: grass sets seed as it grows; seed waits in the cold (neither sprouts nor rots) and in the
    /// warm it sprouts into grass and rots into the soil; matter is conserved, and the settled world's
    /// file keeps the seed. At `seed_share` 0 the hash is e082's whatever `sprout` is.
    #[test]
    fn grass_sets_seed_that_waits_for_the_warm() {
        assert_eq!(world_hash(&small()), world_hash(&Params { sprout: 0.5, ..small() }));
        assert_ne!(world_hash(&small()), world_hash(&Params { seed_share: 0.2, ..small() }));
        let p = Params { seed_share: 0.2, ..small() };
        let (mut w, pl0, u) = settled_world(&p, None);
        assert!(pl0.seed.iter().sum::<f64>() > 0.0, "no seed set in the settled world");
        let bytes = world_bytes(world_hash(&p), u, &w, &pl0);
        let (_, pl2, _) = world_from(&bytes, world_hash(&p), &p).unwrap();
        assert_eq!(pl0.seed, pl2.seed);
        let cells = w.n * w.n;
        let land: Vec<usize> = (0..cells).filter(|&c| !w.sea[c] && depth(&w, &p, c).is_none()).collect();
        let (cold, warm) = (land[0], land[1]);
        w.light = vec![0.0; cells]; // no growth: what changes is the seed's
        w.temp[cold] = plants::WARM_FROM - 10.0;
        w.temp[warm] = plants::WARM_FULL + 5.0;
        w.ground[warm] = p.soil;
        let mut pl = Plants::new(&w, &p);
        (pl.grass, pl.soil, pl.seed) = (pl0.grass.clone(), pl0.soil.clone(), vec![0.0; cells]);
        pl.seed[cold] = 1.0;
        pl.seed[warm] = 1.0;
        let (grass_warm, before) = (pl.grass[warm], pl.matter());
        let f = pl.update(&w, &p, 3);
        assert_eq!(pl.seed[cold], 1.0, "cold seed changed");
        let sprout = p.sprout * p.tick;
        assert!((f.sprout - sprout).abs() < 1e-12, "sprouted {}", f.sprout);
        assert!((pl.seed[warm] - (1.0 - sprout) * (1.0 - plants::SEED_ROT * p.tick)).abs() < 1e-12, "warm seed {}", pl.seed[warm]);
        assert!((pl.grass[warm] - (grass_warm * (1.0 - p.tick / plants::GRASS_LIFE) + sprout)).abs() < 1e-12);
        assert!((pl.matter() - before).abs() < 1e-9 * before, "matter {} -> {}", before, pl.matter());
    }


    /// e090 (D, #100): a share of a cell's seed moves one cell downwind an update. The shift makes and
    /// loses nothing, it goes the way the wind blows, and seed carried onto water sinks as the bottom's
    /// litter. At `seed_drift` 0 the settled world is e089's (its hash too).
    #[test]
    fn seed_drifts_downwind_and_sinks_in_the_water() {
        let base = Params { seed_share: 0.2, ..small() };
        assert_eq!(world_hash(&base), world_hash(&Params { seed_drift: 0.0, ..base.clone() }));
        assert_ne!(world_hash(&base), world_hash(&Params { seed_drift: 0.1, ..base.clone() }));
        let p = Params { seed_drift: 0.25, ..base };
        let (mut w, pl0, _) = settled_world(&p, None);
        let cells = w.n * w.n;
        let n = w.n;
        w.light = vec![0.0; cells]; // nothing grows, and in the cold nothing sprouts or rots either
        w.temp = vec![plants::WARM_FROM - 10.0; cells];
        w.wind_to = (1.0, 0.0); // due +x, a whole cell
        let land: Vec<usize> = (0..cells).filter(|&c| !w.sea[c] && depth(&w, &p, c).is_none()).collect();
        let c = *land.iter().find(|&&c| !w.sea[(c / n) * n + (c % n + 1) % n]).unwrap();
        let down = (c / n) * n + (c % n + 1) % n;
        let mut pl = Plants::new(&w, &p);
        (pl.grass, pl.soil, pl.seed) = (pl0.grass.clone(), pl0.soil.clone(), vec![0.0; cells]);
        pl.seed[c] = 1.0;
        let before = pl.matter();
        pl.update(&w, &p, 3);
        assert!((pl.seed[c] - 0.75).abs() < 1e-12, "upwind cell keeps {}", pl.seed[c]);
        assert!((pl.seed[down] - 0.25).abs() < 1e-12, "downwind cell takes {}", pl.seed[down]);
        assert!((pl.matter() - before).abs() < 1e-12 * before, "matter {} -> {}", before, pl.matter());

        // Onto the water: what drifts in sinks as the bottom's litter, and nothing is lost.
        let up = *land.iter().find(|&&m| w.sea[(m / n) * n + (m % n + 1) % n]).unwrap(); // the last land cell upwind of the sea
        let sea = (up / n) * n + (up % n + 1) % n;
        let mut pl = Plants::new(&w, &p);
        (pl.grass, pl.soil, pl.seed) = (pl0.grass.clone(), pl0.soil.clone(), vec![0.0; cells]);
        pl.seed[up] = 1.0;
        pl.algae = vec![0.0; cells]; // nothing of the algae dies onto the bottom
        let (litter, before) = (pl.litter[sea], pl.matter());
        let f = pl.update(&w, &p, 3);
        assert_eq!(pl.seed[sea], 0.0, "seed lies on the water");
        assert!((pl.litter[sea] - litter - 0.25).abs() < 1e-12, "the bottom's litter {}", pl.litter[sea] - litter);
        assert!((f.seed_wet - 0.25).abs() < 1e-12, "sank {}", f.seed_wet);
        assert!((pl.matter() - before).abs() < 1e-12 * before, "matter {} -> {}", before, pl.matter());
    }

    /// e089 (Fb): a gut's fiber gives `ferment` of itself as energy every step and passes `pass` of itself
    /// as litter every turn, so a body taking a turn every step digests ferment / (ferment + pass) of it
    /// and a slow body more; with `ferment` 0 all of a food is energy at the bite.
    #[test]
    fn a_slow_body_digests_more_of_its_fiber() {
        let digested = |pace: f64| {
            let (ferment, pass) = (0.02, 0.02);
            let (mut fiber, mut got, mut phase) = (1.0f64, 0.0f64, 0.0f64);
            for _ in 0..20_000 {
                let f = fiber * ferment;
                fiber -= f;
                got += f;
                phase += pace;
                if phase >= 1.0 {
                    phase -= 1.0;
                    fiber -= fiber * pass;
                }
            }
            got
        };
        assert!((digested(1.0) - 0.5).abs() < 0.01, "{}", digested(1.0));
        assert!(digested(0.5) > 0.64 && digested(0.1) > 0.88, "{} {}", digested(0.5), digested(0.1));
    }

}
