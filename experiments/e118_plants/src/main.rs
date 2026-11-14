//! e118 (#135 rung 2): plants at metres on the map at an animal's size (`base/worlds/isles16.params`).
//!
//! The ground, the air and the water are `base/`'s (e117's map). The living are new (`plants.rs`): a field of
//! cohorts on the fine cells of 5 m and trees as things, by the base's producer law. The climate runs bare for `sow`
//! years; the ground at 5 m is then drawn from those years' rain, and founders' seed rains on it for `sow_years`.
//!
//! Run: cargo run --release -p e118_plants -- <prefix> [key=value ...] [file.params ...]
//! Writes `<prefix>_log.csv` (a row a year), `_maps.bin|json` (the last `maps_years` years' annual maps on the
//! cells of 125 m, and the static ones), `_season.bin|json` (their mean months), `_ground5.bin|json` (the ground at
//! 5 m), and every `snap_every` years after the sowing `_trees_<year>.bin` (a record a tree), `_field_<year>.bin`
//! (the field on the fine cells, a byte a layer) and `_traits_<year>.bin` (the living's traits by place, on the
//! cells of 125 m); `_snaps.json` says how to read them; `_genes.csv` the genotypes that hold trees at the end.

mod climate;
mod genome;
mod ground5;
mod hydro;
mod noise;
mod par;
mod plants;
mod terrain;

use climate::{Air, Flux, Sat, Weather};
use hydro::{HFlux, Hydro};
use plants::{LFlux, Plants, KF, LEAF, WOOD};
use std::io::Write;
use std::time::Instant;
use terrain::{Terrain, NONE};

const POOL: f64 = 500.0; // mm standing that makes a land cell a lake (e061)

macro_rules! params {
    ($($name:ident = $default:expr, $doc:literal;)*) => {
        #[derive(Clone, Debug)]
        pub struct Params { $(pub $name: f64,)* }
        impl Default for Params {
            fn default() -> Self { Params { $($name: $default,)* } }
        }
        impl Params {
            const NAMES: &'static [&'static str] = &[$(stringify!($name),)*];
            fn set(&mut self, key: &str, v: f64) -> bool {
                match key { $(stringify!($name) => { self.$name = v; true })* _ => false }
            }
            fn values(&self) -> Vec<f64> { vec![$(self.$name,)*] }
        }
    };
}

params! {
    // e061's world (c1225's values come from base/worlds/c1225.params)
    size = 512.0, "cells on a side of the world (a torus)";
    seed = 1.0, "the seed of the generated terrain";
    year = 11880.0, "steps in a year";
    day = 74.7, "steps in a day";
    tick = 10.0, "steps between two updates of the climate";
    land = 0.422, "share of the cells above the sea";
    relief = 2002.0, "m: the height of the highest land";
    grain = 158.7, "cells: the widest feature of the terrain";
    rough = 0.5, "amplitude of each finer octave of the terrain";
    lat_lo = -59.4, "degrees: the latitude of the first row (and of the last)";
    lat_hi = 87.0, "degrees: the latitude of the middle row";
    tilt = 17.8, "degrees: the axis's tilt (the seasons)";
    night = -30.0, "C: where a cell's temperature goes without sun";
    gain = 219.6, "C per unit of light";
    lapse = 6.5, "C a km of height";
    land_rate = 0.2854, "share of the way to its equilibrium a land cell goes in an update";
    sea_rate = 0.0005, "the same for the sea";
    spread = 0.2, "heat's exchange across an edge";
    wind = 0.1, "cells an update: the winds' speed";
    wind_dir = 0.0, "degrees: e061's one wind (only with wind_bands 0)";
    wind_turn = 35.8, "degrees the one wind turns with the season (only with wind_bands 0)";
    evap = 0.05, "share of the air's deficit it takes up an update (from the ground by its fill)";
    rain = 0.2825, "share of the air's excess over 80% that rains an update";
    soil = 150.0, "mm: the water a soil of mean depth on a mean rock holds";
    soil_evap = 0.3, "share of open water's evaporation a full soil gives up (e102: a soil is not a lake)";
    // e102: winds, geology, water below, nutrients, years
    wind_bands = 1.0, "1: winds by latitude band that follow the sun; 0: e061's one wind";
    mix = 0.05, "share of the vapor's difference crossing an edge an update (the air's mixing)";
    provinces = 48.0, "rock provinces on the world";
    warp = 24.0, "cells the provinces' borders wander";
    depth_slope = 20.0, "m a cell: the slope at which a soil is thin (and deposition slows)";
    beta = 2.0, "the share of a rain that runs straight off is the soil's fill to this power";
    lake_depth = 2.0, "m: a pit of the noise is filled to this depth under its spill level (a lake, not a sink)";
    recharge = 0.02, "share of the standing water that sinks to the groundwater an update";
    base_flow = 0.005, "share of the groundwater that seeps into the rivers an update";
    weather = 1.0, "nutrient a mean rock gives a cell a year at 15 C in a full soil";
    mob_a = 0.5, "how readily water takes A (mobile)";
    mob_b = 0.05, "how readily water takes B (bound)";
    deposit = 0.02, "share of what a river carries dropped on flat land a cell";
    trap = 0.5, "share of what a river carries dropped in a lake";
    sea_mix = 0.1, "the sea's mixing of its nutrients across an edge";
    bury = 0.0005, "share of the sea's nutrients buried an update";
    var_temp = 1.0, "C: the spread of a year's temperature anomaly";
    var_rain = 0.3, "the spread of a year's rain anomaly (log of the multiplier)";
    var_rho = 0.5, "the share of last year's anomaly the next keeps";
    var_grain = 128.0, "cells: the width of an anomaly";
    storms = 12.0, "storms a year over the world";
    storm_radius = 10.0, "cells: a storm's radius";
    storm_updates = 3.0, "updates a storm lasts";
    storm_rain = 4.0, "times the rain inside a storm";
    // e108: the small world (#126, #127). The defaults leave the planet as it was.
    cell_km = 63.0, "km: a cell's side";
    // e117: the map at an animal's size (#135)
    lat_span = 0.0, "1: the rows run once from lat_lo (south, row 0) to lat_hi (north), a band of latitude folded into the map; 0: there and back";
    survey = 0.0, "n > 0: print the islands the first n terrain seeds make, and stop";
    relief_pow = 1.0, "the land's heights as a share of the highest, to this power (e117: above 1 the lowlands flatten)";
    mirror = 0.0, "1: the generated ground mirrored west for east (e117: which side of an island its heights stand on)";
    track = 0.0, "mm a year the fronts bring into the air over a cell that every front reaches (e117; 0: no fronts, the sea's wet air always)";
    track_lat = 48.0, "degrees: the latitude a front reaches south to, in the mean, at the equinoxes (the storm track's edge)";
    track_shift = 8.0, "degrees the edge lies further north at midsummer and further south at midwinter";
    track_width = 5.0, "degrees: the spread of the fronts' reach about the edge";
    front_days = 1.5, "days a front lasts, in the mean";
    front_gap = 2.5, "days of clear air between two fronts, in the mean";
    dry = 0.2, "share by which the air sunk from aloft (between fronts, and south of one) is short of the sea air's water";
    snow_melt = 0.0, "mm of snow melted a day for each degree above freezing (e117; 0: no snow lies)";
    ice = 3000.0, "mm of water: snow lying deeper than this creeps to the cell below";
    // e118: plants at metres (#135 rung 2)
    h_thing = 3.0, "m: a stand that grows past this height becomes a thing, one plant with a crown (a crown about 2 m wide)";
    h_stem = 2.9, "m: the height a kg of wood stands as one stem, by its mass's fourth root (wood of 500 kg a m3 that buckles at 30 d^(2/3))";
    lai_crown = 4.0, "m2 of leaf a m2 of crown: a crown spreads as wide as its leaves need at this";
    crown_h = 0.35, "a crown's radius is at most this share of the tree's height (a branch reaches out no further)";
    steep = 0.84, "m a m: fine ground steeper than this (40 degrees) holds no soil";
    wet_reach = 10.0, "m: ground within this of a pond or a stream reaches the groundwater whatever its roots";
    wet_rise = 2.0, "m: and no higher than this over the water";
    fire_shade = 0.2, "share of the open ground's drying that fuel has in full shade (the sun dries what it reaches)";
    sow_years = 5.0, "years the founders' seed rains on every cell with soil";
    snap_every = 25.0, "years between snapshots of the trees, the field and the traits";
    fine = 0.0, "k > 0: at the end, draw the ground at k fine cells a cell from the kept years' rain (`_ground5.bin`)";
    edge = 0.0, "cells from the border over which the ground sinks under the sea (0: the world wraps as a planet)";
    span_lon = 1.0, "share of a day the world's width spans (1: a planet's longitudes; 0: one hour everywhere)";
    aspect = 0.0, "1: a slope's light follows its tilt against the sun";
    sweep = 0.0, "1: the air crosses the world within an update and is followed across it (e108); 0: the planet's air";
    wind_ms = 5.5, "m/s: the wind of the sweep";
    wind_sd = 45.0, "degrees: how far the wind's direction wanders about its season's (the sweep)";
    wind_hold = 3.0, "days a wandering of the wind lasts (the sweep)";
    var_wind = 10.0, "degrees: the spread of a year's turn of the wind (the sweep)";
    air_couple = 1.0, "m/s: the wind at which the sea air sets half of a land cell's equilibrium (the sweep)";
    rain_tau = 1000.0, "s: the time in which the air's excess water falls (cloud to rain; the sweep)";
    evap_tau = 2.0e5, "s: the time in which the air takes up its deficit from open water (the sweep)";
    lifted = 0.05, "share of the air's water in the layer a land lifts to its dew (the sweep)";
    years = 30.0, "years to run";
    maps_years = 10.0, "the last years whose annual maps are written";
    // e103: the living (#116 rung 2). Masses kg of dry matter a m2, nutrients g a m2, rates a year.
    life = 1.0, "the seed of the living (the terrain's is `seed`)";
    sow = 10.0, "the year the first producers are sown (the climate spun up before)";
    founders = 256.0, "random genomes sown (a quarter as many eaters)";
    sow_mass = 0.001, "kg of seed a genotype sown in a cell";
    threads = 4.0, "threads for the cells (climate, water and life); the results do not depend on it";
    life_every = 8.0, "updates between two life steps (about a day)";
    gpp_max = 10.0, "kg a year a full crown fixes at the mean daylight, fully active, at its optimum";
    light_ref = 0.32, "the day's mean light at the equator (the sun's height, e061)";
    sla = 10.0, "m2 of leaf a kg";
    ext = 0.5, "light's extinction a unit of leaf area (Beer's law)";
    resp = 20.0, "kg respired a year a kg of B in living tissue at 20 C (Q10 2)";
    wue = 300.0, "mm of water transpired a kg fixed, at the deficit `deficit_ref`";
    deficit_ref = 10.0, "mm: the air's deficit at which `wue` holds";
    h_water = 30.0, "m: the height at which lifting doubles the water a kg costs";
    root_draw = 1000.0, "share of the soil's water a kg of root reaches a year (a forest's roots reach it in days)";
    uptake = 2000.0, "share of the soil's A and B a kg of active root reaches a year (real roots take ~100 g a kg a year)";
    leaf_turn = 1.0, "leaves lost a year (tough ones 5x slower)";
    root_turn = 1.0, "roots lost a year (tough ones 5x slower)";
    wood_turn = 0.05, "wood lost a year (tough 5x slower)";
    store_turn = 0.1, "store lost a year";
    flush = 20.0, "store turned into leaves a year while the leaves are under half their recent mass";
    frost = 5.0, "leaves lost a year per 10 C of frost (tough ones less)";
    wilt = 5.0, "leaves lost a year when the soil meets none of the demand (tough ones less)";
    storm_fell = 0.3, "share of leaf and wood a storm fells at `h_storm` and above (tough wood less)";
    h_storm = 30.0, "m: the height at which storms fell the most";
    sigma = 1.3, "kg of wood a kg of leaf needs a m of height";
    h0 = 0.1, "m: the height of a stand with no wood";
    b_comp = 0.1, "B share of a defence compound";
    b_gene = 0.0001, "B share a seed carries a gene of its genome";
    decay = 1.0, "litter decayed a year at 20 C, wet, of mean quality";
    m_min = 1e-6, "kg: a stand below it dies";
    seed_every = 15.0, "life steps between two seed releases";
    seed_decay = 1.0, "seed bank lost a year";
    fall_seed = 7.9, "m/s: the fall of a bare seed of 0.01 g, a ball of water's density (by its mass to the 1/6)";
    fall_wing = 0.35, "m/s: the fall of a seed that is all wing (a membrane of 30 g a m2; a maple's key falls at ~1)";
    float_seed = 2000.0, "m of river a floating seed goes a unit of float before it strands (mean; a stream runs 1 km in an hour)";
    river_q = 20.0, "mm an update out of a cell: a river that carries seeds";
    m_need = 1e-5, "kg of seed reserve at which half the seedlings establish in open wet ground";
    p_mut = 0.01, "chance a seed release carries a mutant genome, the whole release (e104: 1 seed in 100)";
    lightning = 0.1, "strikes a year a km2 of land that would light dry fuel (of ~3 flashes, most come with rain)";
    fire_run = 2000.0, "m a fire runs through dry, ample fuel before the weather ends it (mean: 0.1 m/s for an afternoon)";
    fuel_half = 0.5, "kg of fuel at which fire spreads at half its chance";
    fuel_min = 0.05, "kg of fuel below which nothing burns";
    flame = 2.0, "m of flame a kg of fuel";
    eat = 100.0, "kg of leaf a kg of eater eats a year at its best (a caterpillar eats its mass in days)";
    eat_half = 0.05, "kg of good leaf at which eating is half its best";
    eat_eff = 0.3, "share of what is eaten built into eater";
    eater_a = 0.01, "A share of an eater";
    eater_b = 0.03, "B share of an eater";
    eater_resp = 3.0, "eater respired a year at 20 C";
    eater_die = 1.0, "eaters dying a year";
    eater_cold = 5.0, "eaters dying a year per 10 C of frost";
    harm = 1.0, "kg of eater killed a kg of fully foreign compound-leaf eaten, per 1% compound";
    eater_disp = 5.0, "share of eaters leaving a year at full wing";
    eater_fly = 300.0, "m a leaving eater flies (mean), and the wind carries it as far again";
    eater_mut = 0.001, "chance a leaving eater packet carries a mutant";
    lead_every = 10.0, "years between maps of each cell's leading genotype";
    life_max = 300.0, "years a stand of all-wood, fully tough wood lives (e104; 1 year with no wood)";
}

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

/// A year's sums per cell, and its annual maps.
struct Year {
    temp: Vec<f64>,
    quarter: [Vec<f64>; 4],
    fill: Vec<f64>,
    rain: Vec<f64>,
    q: Vec<f64>,
    lake: Vec<f64>,
    light: Vec<f64>,
    month: Vec<f64>, // e117: twelve months of `MONTHLY`, a field after a field
    updates: usize,
}

/// A month's maps (e117): the mean temperature, the rain and snow fallen (mm), the soil's mean fill, the mean snow
/// lying (mm of water) and the mean water run out of the cell an update. The year starts at the spring equinox.
const MONTHLY: [&str; 5] = ["temp", "rain", "fill", "snow", "flow"];


impl Year {
    fn new(cells: usize) -> Self {
        let z = vec![0.0; cells];
        Year { temp: z.clone(), quarter: [z.clone(), z.clone(), z.clone(), z.clone()], fill: z.clone(), rain: z.clone(), q: z.clone(), lake: z.clone(), light: z, month: vec![0.0; 12 * MONTHLY.len() * cells], updates: 0 }
    }
    fn add(&mut self, t: &Terrain, air: &Air, hy: &Hydro, quarter: usize, month: usize, threads: usize) {
        let cells = t.sea.len();
        let mo = par::Shared::new(&mut self.month);
        let m0 = month * MONTHLY.len() * cells;
        let (temp, qt, rain, fill, q, lake, light) = (
            par::Shared::new(&mut self.temp),
            par::Shared::new(&mut self.quarter[quarter]),
            par::Shared::new(&mut self.rain),
            par::Shared::new(&mut self.fill),
            par::Shared::new(&mut self.q),
            par::Shared::new(&mut self.lake),
            par::Shared::new(&mut self.light),
        );
        par::pieces(threads, t.sea.len(), |lo, hi| {
            for c in lo..hi {
                *temp.at(c) += air.temp[c];
                *qt.at(c) += air.temp[c];
                *rain.at(c) += air.rain_now[c];
                *light.at(c) += air.light[c];
                *mo.at(m0 + c) += air.temp[c];
                *mo.at(m0 + cells + c) += air.rain_now[c];
                if !t.sea[c] {
                    *mo.at(m0 + 2 * cells + c) += (air.ground[c] / t.cap[c]).min(1.0);
                    *mo.at(m0 + 3 * cells + c) += air.snow[c];
                    *mo.at(m0 + 4 * cells + c) += hy.q[c];
                    *fill.at(c) += (air.ground[c] / t.cap[c]).min(1.0);
                    *q.at(c) += hy.q[c];
                    if air.ground[c] - t.cap[c] >= POOL {
                        *lake.at(c) += 1.0;
                    }
                }
            }
        });
        self.updates += 1;
    }
    /// The year's months, in the order of `MONTHLY`: means over a month's updates, the rain its sum.
    fn season(&self) -> Vec<f32> {
        let cells = self.temp.len();
        let per = self.updates as f64 / 12.0;
        let k = MONTHLY.len();
        (0..12 * k * cells).map(|i| (self.month[i] / if (i / cells) % k == 1 { 1.0 } else { per }) as f32).collect()
    }
    /// The climate's part of the year's maps, in the order of `FIELDS`' first eight.
    fn maps(&self, hy: &Hydro) -> Vec<Vec<f32>> {
        let u = self.updates as f64;
        let qn = u / 4.0;
        let cells = self.temp.len();
        let swing: Vec<f32> = (0..cells)
            .map(|c| {
                let m: Vec<f64> = self.quarter.iter().map(|v| v[c] / qn).collect();
                (m.iter().cloned().fold(f64::MIN, f64::max) - m.iter().cloned().fold(f64::MAX, f64::min)) as f32
            })
            .collect();
        let f = |v: &[f64]| v.iter().map(|x| *x as f32).collect::<Vec<f32>>();
        vec![
            self.temp.iter().map(|v| (v / u) as f32).collect(),
            swing,
            self.fill.iter().map(|v| (v / u) as f32).collect(),
            self.rain.iter().map(|v| *v as f32).collect(),
            self.q.iter().map(|v| (v / u) as f32).collect(),
            self.lake.iter().map(|v| (v / u) as f32).collect(),
            f(&hy.a),
            f(&hy.b),
            self.light.iter().map(|v| (v / u) as f32).collect(),
        ]
    }
}

/// The annual maps on the cells of 125 m: the climate's nine, then the living's (a m2 of the cell's soil).
const FIELDS: [&str; 16] = ["temp", "swing", "fill", "rain", "discharge", "lake", "a", "b", "light", "field", "wood", "crown", "height", "litter", "burnt", "transp"];

/// The living summed over each cell of 125 m and over the land.
struct Survey {
    field: Vec<f64>,  // kg of field a m2 of soil
    wood: Vec<f64>,   // kg of trees a m2 of soil
    crown: Vec<f64>,  // share of the soil under crowns that take half the light or more
    height: Vec<f64>, // m: the tallest tree
    litter: Vec<f64>, // kg a m2 of soil
    soil: Vec<f64>,   // fine cells with soil
    all: [f64; 3],    // kg of field, of trees, of litter on the land
    soil_all: f64,
    crown_all: f64,
    trees: usize,
    h_mean: f64,
    h_max: f64,
    age_mean: f64,
    mutant: f64, // share of the living mass in genotypes born after the sowing
}

fn survey(pl: &Plants, p: &Params) -> Survey {
    let cells = pl.n * pl.n;
    let f2 = pl.k * pl.k;
    let z = vec![0.0; cells];
    let mut s = Survey { field: z.clone(), wood: z.clone(), crown: z.clone(), height: z.clone(), litter: z.clone(), soil: z, all: [0.0; 3], soil_all: 0.0, crown_all: 0.0, trees: 0, h_mean: 0.0, h_max: 0.0, age_mean: 0.0, mutant: 0.0 };
    let (mut live, mut new) = (0.0, 0.0);
    for q in 0..pl.grows.len() {
        if !pl.grows[q] {
            continue;
        }
        let c = pl.lands[q / f2] as usize;
        s.soil[c] += 1.0;
        s.litter[c] += pl.lit[q].m;
        if pl.under[q] < 0.5 {
            s.crown[c] += 1.0;
        }
        for i in 0..KF {
            let x = &pl.co[q * KF + i];
            if x.live() {
                let m = x.mass();
                s.field[c] += m;
                live += m * pl.fa;
                if x.g as usize >= pl.founders {
                    new += m * pl.fa;
                }
            }
        }
    }
    for t in &pl.trees {
        if t.slot == NONE {
            continue;
        }
        let c = pl.lands[t.slot as usize / f2] as usize;
        let m = t.b.mass();
        s.wood[c] += m / pl.fa;
        s.height[c] = s.height[c].max(t.b.h);
        s.trees += 1;
        s.h_mean += t.b.h;
        s.h_max = s.h_max.max(t.b.h);
        s.age_mean += t.b.age;
        live += m;
        if t.b.g as usize >= pl.founders {
            new += m;
        }
    }
    for c in 0..cells {
        if s.soil[c] > 0.0 {
            s.all[0] += s.field[c] * pl.fa;
            s.all[1] += s.wood[c] * pl.fa;
            s.all[2] += s.litter[c] * pl.fa;
            s.soil_all += s.soil[c];
            s.crown_all += s.crown[c];
            s.field[c] /= s.soil[c];
            s.wood[c] /= s.soil[c];
            s.litter[c] /= s.soil[c];
            s.crown[c] /= s.soil[c];
        }
    }
    if s.trees > 0 {
        s.h_mean /= s.trees as f64;
        s.age_mean /= s.trees as f64;
    }
    s.mutant = new / live.max(1e-30);
    let _ = p;
    s
}

/// The traits read by place: the field's and the trees', each the mean of its genotypes' by mass.
const TRAITS: [&str; 10] = ["leaf_a", "leaf_b", "shed", "height", "deep", "t_opt", "breadth", "seed_mass", "alloc_wood", "alloc_store"];

fn trait_values(ph: &genome::Pheno) -> [f64; 10] {
    [ph.leaf_a, ph.leaf_b, ph.shed, ph.height, ph.deep, ph.t_opt, ph.breadth, ph.seed_mass.ln(), ph.alloc[1], ph.alloc[3]]
}

/// A snapshot: the trees, the field on the fine cells, the traits by place.
fn snapshot(prefix: &str, year: usize, pl: &Plants, sv: &Survey) {
    let f2 = pl.k * pl.k;
    let w = |name: &str| std::io::BufWriter::new(std::fs::File::create(format!("{prefix}_{name}_{year}.bin")).unwrap());
    // the trees: x, y, height, crown radius, leaf, wood, age (f32), genotype, the year it became a thing (u32)
    let mut out = w("trees");
    for t in &pl.trees {
        if t.slot == NONE {
            continue;
        }
        let (i, j) = pl.ij(t.slot as usize);
        for v in [(i as f64 + 0.5) * pl.fm, (j as f64 + 0.5) * pl.fm, t.b.h, t.r, t.b.o[LEAF].m, t.b.o[WOOD].m, t.b.age] {
            out.write_all(&(v as f32).to_le_bytes()).unwrap();
        }
        out.write_all(&t.b.g.to_le_bytes()).unwrap();
        out.write_all(&t.born.to_le_bytes()).unwrap();
    }
    out.flush().unwrap();
    // the field: leaf (kg a m2 x 100), height (m x 50), litter (kg a m2 x 50), light under the crowns (x 255), years
    // since it burnt (255: never, or no soil)
    let cells = pl.nf * pl.nf;
    let mut layers = vec![vec![0u8; cells]; 5];
    layers[3].iter_mut().for_each(|v| *v = 255);
    layers[4].iter_mut().for_each(|v| *v = 255);
    for q in 0..pl.grows.len() {
        let (i, j) = pl.ij(q);
        let c = j * pl.nf + i;
        layers[3][c] = (pl.under[q] * 255.0) as u8;
        if !pl.grows[q] {
            continue;
        }
        let (mut leaf, mut h) = (0.0, 0.0f64);
        for k in 0..KF {
            let x = &pl.co[q * KF + k];
            if x.live() {
                leaf += x.o[LEAF].m;
                if x.o[LEAF].m > 0.01 {
                    h = h.max(x.h);
                }
            }
        }
        layers[0][c] = (leaf * 100.0).min(255.0) as u8;
        layers[1][c] = (h * 50.0).min(255.0) as u8;
        layers[2][c] = (pl.lit[q].m * 50.0).min(255.0) as u8;
        if pl.burnt_year[q] > 0 {
            layers[4][c] = (year as i64 - pl.burnt_year[q] as i64).clamp(0, 254) as u8;
        }
    }
    let mut out = w("field");
    for l in &layers {
        out.write_all(l).unwrap();
    }
    out.flush().unwrap();
    // the traits by place: the field's ten, the trees' ten, then field, wood, crown, trees a cell
    let nc = pl.n * pl.n;
    let nt = TRAITS.len();
    let mut tr = vec![0.0f64; (2 * nt + 4) * nc];
    let mut wsum = vec![0.0f64; 2 * nc];
    for q in 0..pl.grows.len() {
        let c = pl.lands[q / f2] as usize;
        for k in 0..KF {
            let x = &pl.co[q * KF + k];
            if x.live() {
                let m = x.mass();
                let v = trait_values(&pl.gen[x.g as usize].as_ref().unwrap().base);
                for (a, v) in v.iter().enumerate() {
                    tr[a * nc + c] += m * v;
                }
                wsum[c] += m;
            }
        }
    }
    for t in &pl.trees {
        if t.slot == NONE {
            continue;
        }
        let c = pl.lands[t.slot as usize / f2] as usize;
        let m = t.b.mass();
        let v = trait_values(&pl.gen[t.b.g as usize].as_ref().unwrap().base);
        for (a, v) in v.iter().enumerate() {
            tr[(nt + a) * nc + c] += m * v;
        }
        wsum[nc + c] += m;
        tr[(2 * nt + 3) * nc + c] += 1.0;
    }
    for c in 0..nc {
        for a in 0..nt {
            tr[a * nc + c] = if wsum[c] > 0.0 { tr[a * nc + c] / wsum[c] } else { f64::NAN };
            tr[(nt + a) * nc + c] = if wsum[nc + c] > 0.0 { tr[(nt + a) * nc + c] / wsum[nc + c] } else { f64::NAN };
        }
        tr[2 * nt * nc + c] = sv.field[c];
        tr[(2 * nt + 1) * nc + c] = sv.wood[c];
        tr[(2 * nt + 2) * nc + c] = sv.crown[c];
    }
    let mut out = w("traits");
    for v in &tr {
        out.write_all(&(*v as f32).to_le_bytes()).unwrap();
    }
    out.flush().unwrap();
}

fn main() {
    let args: Vec<String> = std::env::args().skip(1).collect();
    let prefix = args.first().expect("usage: e118_plants <prefix> [key=value ...] [file.params ...]").clone();
    let p = parse(&args[1..]);
    if let Some(dir) = std::path::Path::new(&prefix).parent() {
        std::fs::create_dir_all(dir).unwrap();
    }
    let t0 = Instant::now();
    let ter = Terrain::new(&p);
    let n = ter.n;
    let cells = n * n;
    let land = ter.sea.iter().filter(|&&s| !s).count();
    eprintln!("terrain: {n}x{n}, {land} land cells, {:.1} s", t0.elapsed().as_secs_f64());
    let sat = Sat::new();
    let mut wx = Weather::new(&p, cells);
    let mut air = Air::new(&p, &ter);
    let mut hy = Hydro::new(&ter);
    let mut pl: Option<Plants> = None;
    let bare_cover = vec![1.0; cells];
    let ca = (p.cell_km * 1000.0).powi(2);
    let w0 = air.water() + hy.water();
    let (mut sea_net, mut na, mut nb) = (0.0f64, 0.0f64, 0.0f64); // what the open edges added
    let mut cm = 0.0f64; // the living's matter: fixed less returned
    let upy = (p.year / p.tick).round() as usize;
    let mut log = std::fs::File::create(format!("{prefix}_log.csv")).unwrap();
    writeln!(log, "step,year,land_temp,land_rain,land_evap,to_sea,water_err,a_err,b_err,c_err,field,wood,litter,trees,crown,tree_h,tree_h_max,tree_age,gpp,resp,transp,decayed,burnt,burnt_cells,fires,grown,fallen,genotypes,mutant_share,secs,secs_plants").unwrap();
    let mut kept: Vec<(usize, Vec<Vec<f32>>)> = Vec::new();
    let mut months: Vec<Vec<f32>> = Vec::new();
    let mut snaps: Vec<usize> = Vec::new();
    let mut rain_sum = vec![0.0f64; cells];
    let years = p.years as usize;
    let sow = p.sow as usize;
    for yr in 0..years {
        if yr > 0 {
            wx.new_year(&p);
        }
        if yr == sow {
            // the ground at an animal's grain, from the bare years' rain; the founders
            let t5 = Instant::now();
            let rain: Vec<f64> = rain_sum.iter().map(|v| v / sow.max(1) as f64).collect();
            let g5 = ground5::Ground5::new(&ter, p.cell_km, p.fine as usize, &rain, p.seed as u64 ^ 0x5EED, p.threads as usize);
            g5.write(&prefix);
            let mut x = Plants::new(&ter, &p, &g5);
            x.found(&p, yr as u32);
            eprintln!(
                "ground5 and plants: {}x{} cells of {} m, {} with soil ({:.1} km2), {} beside water, in {:.1} s",
                g5.n, g5.n, g5.cell_m, x.grows.iter().filter(|&&v| v).count(), x.grows.iter().filter(|&&v| v).count() as f64 * x.fa / 1e6, x.wet.iter().filter(|&&v| v).count(), t5.elapsed().as_secs_f64()
            );
            pl = Some(x);
        }
        let ty = Instant::now();
        let mut year = Year::new(cells);
        let (mut fl, mut hf, mut lf) = (Flux::default(), HFlux::default(), LFlux::default());
        if let Some(x) = pl.as_mut() {
            x.transp.iter_mut().for_each(|v| *v = 0.0);
            x.burnt.iter_mut().for_each(|v| *v = 0.0);
            x.secs = [0.0; 6];
        }
        let mut secs_plants = 0.0;
        for u in 0..upy {
            let step = (yr * upy + u) as f64 * p.tick;
            let f = air.update(&p, &ter, &sat, &mut wx, step, pl.as_ref().map_or(&bare_cover, |x| &x.cover));
            let h = hy.update(&p, &ter, &mut air.ground, &air.temp, &air.wet_now);
            fl.add(&f);
            hf.add(&h);
            if let Some(x) = pl.as_mut() {
                let t1 = Instant::now();
                x.accumulate(&air.light, &air.temp, &air.snow, &wx.hit);
                if x.due(&p) {
                    let l = x.step(&p, &ter, &sat, &wx, &mut air.ground, &mut air.vapor, &mut hy.deep, &mut hy.a, &mut hy.b, step, yr as u32);
                    lf.add(&l);
                }
                secs_plants += t1.elapsed().as_secs_f64();
            }
            year.add(&ter, &air, &hy, (u * 4 / upy).min(3), (u * 12 / upy).min(11), p.threads as usize);
        }
        if yr < sow {
            for c in 0..cells {
                rain_sum[c] += year.rain[c];
            }
        }
        sea_net += fl.sea_evap - fl.sea_rain - fl.wind - hf.to_sea;
        na += hf.weathered_a - hf.buried_a;
        nb += hf.weathered_b - hf.buried_b;
        cm += lf.fixed - lf.returned;
        let (lm, la, lb) = pl.as_ref().map_or((0.0, 0.0, 0.0), |x| x.totals());
        let w = air.water() + hy.water();
        let (a, b) = hy.nutrients();
        let (a, b) = (a + la / ca, b + lb / ca);
        let werr = (w - (w0 + sea_net)).abs() / w.max(1.0);
        let aerr = (a - na).abs() / a.max(1e-12);
        let berr = (b - nb).abs() / b.max(1e-12);
        let cerr = (lm - cm).abs() / lm.max(1e-12);
        let lfn = land as f64;
        let u = year.updates as f64;
        let land_temp = (0..cells).filter(|&c| !ter.sea[c]).map(|c| year.temp[c]).sum::<f64>() / u / lfn;
        let mut maps = year.maps(&hy);
        let secs = ty.elapsed().as_secs_f64();
        match pl.as_mut() {
            Some(x) => {
                let ng = x.collect();
                let sv = survey(x, &p);
                let soil_m2 = sv.soil_all * x.fa;
                writeln!(
                    log,
                    "{},{},{:.3},{:.1},{:.1},{:.1},{:.3e},{:.3e},{:.3e},{:.3e},{:.5},{:.5},{:.5},{},{:.4},{:.3},{:.2},{:.2},{:.6e},{:.6e},{:.1},{:.6e},{:.6e},{},{},{},{},{},{:.5},{:.1},{:.1}",
                    (yr + 1) * upy * p.tick as usize, yr + 1, land_temp, fl.land_rain / lfn, fl.land_evap / lfn, hf.to_sea / lfn, werr, aerr, berr, cerr,
                    sv.all[0] / soil_m2, sv.all[1] / soil_m2, sv.all[2] / soil_m2, sv.trees, sv.crown_all / sv.soil_all, sv.h_mean, sv.h_max, sv.age_mean,
                    lf.gpp, lf.resp, lf.transp / (lfn * ca), lf.decayed, lf.burnt, lf.burnt_cells, lf.fires, lf.grown, lf.fallen, ng, sv.mutant, secs, secs_plants
                )
                .unwrap();
                eprintln!(
                    "year {:>3}: land {:.1} C, rain {:.0} mm, evap {:.0}, transp {:.0}; field {:.3} kg/m2, wood {:.3}, litter {:.3}; trees {} (h {:.1} m, to {:.1}, age {:.1}), crowns {:.3}; grown {}, fallen {}, fires {} over {} cells; genotypes {ng}, new {:.3}; errs w {werr:.0e} A {aerr:.0e} C {cerr:.0e}; {secs:.1} s (plants {secs_plants:.1}: crowns {:.1}, light {:.1}, growth {:.1}, fire {:.1}, seeds {:.1})",
                    yr + 1, land_temp, fl.land_rain / lfn, fl.land_evap / lfn, lf.transp / (lfn * ca), sv.all[0] / soil_m2, sv.all[1] / soil_m2, sv.all[2] / soil_m2,
                    sv.trees, sv.h_mean, sv.h_max, sv.age_mean, sv.crown_all / sv.soil_all, lf.grown, lf.fallen, lf.fires, lf.burnt_cells, sv.mutant, x.secs[0], x.secs[1], x.secs[2], x.secs[3], x.secs[4]
                );
                let f = |v: &[f64]| v.iter().map(|x| *x as f32).collect::<Vec<f32>>();
                maps.extend([f(&sv.field), f(&sv.wood), f(&sv.crown), f(&sv.height), f(&sv.litter), f(&x.burnt), f(&x.transp)]);
                let since = yr + 1 - sow;
                if since % (p.snap_every as usize).max(1) == 0 || yr + 1 == years {
                    snapshot(&prefix, yr + 1, x, &sv);
                    snaps.push(yr + 1);
                }
            }
            None => {
                writeln!(log, "{},{},{:.3},{:.1},{:.1},{:.1},{:.3e},{:.3e},{:.3e},0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,{:.1},0", (yr + 1) * upy * p.tick as usize, yr + 1, land_temp, fl.land_rain / lfn, fl.land_evap / lfn, hf.to_sea / lfn, werr, aerr, berr, secs).unwrap();
                eprintln!("year {:>3}: land {:.1} C, rain {:.0} mm, evap {:.0}, to sea {:.0}; bare; errs w {werr:.0e} A {aerr:.0e}; {secs:.1} s", yr + 1, land_temp, fl.land_rain / lfn, fl.land_evap / lfn, hf.to_sea / lfn);
                let z = vec![0.0f32; cells];
                maps.extend(std::iter::repeat(z).take(7));
            }
        }
        log.flush().unwrap();
        if yr + (p.maps_years as usize) >= years {
            kept.push((yr + 1, maps));
            months.push(year.season());
        }
    }
    // The maps: the kept years' annual fields, then the static ones.
    let statics: Vec<(&str, Vec<f32>)> = vec![
        ("elev", ter.elev.iter().map(|&v| v as f32).collect()),
        ("sea", ter.sea.iter().map(|&s| if s { 1.0 } else { 0.0 }).collect()),
        ("rock", ter.rock.iter().map(|&r| r as f32).collect()),
        ("cap", ter.cap.iter().map(|&v| v as f32).collect()),
        ("lake_cap", ter.lake_cap.iter().map(|&v| v as f32).collect()),
        ("slope", ter.slope.iter().map(|&v| v as f32).collect()),
        ("lat", (0..cells).map(|c| ter.lat[c / n].to_degrees() as f32).collect()),
    ];
    let mut bin = std::io::BufWriter::new(std::fs::File::create(format!("{prefix}_maps.bin")).unwrap());
    for (_, maps) in &kept {
        for m in maps {
            for v in m {
                bin.write_all(&v.to_le_bytes()).unwrap();
            }
        }
    }
    for (_, m) in &statics {
        for v in m {
            bin.write_all(&v.to_le_bytes()).unwrap();
        }
    }
    bin.flush().unwrap();
    let q = |v: &[&str]| v.iter().map(|s| format!("\"{s}\"")).collect::<Vec<_>>().join(",");
    std::fs::write(
        format!("{prefix}_maps.json"),
        format!(
            "{{\"n\":{n},\"years\":[{}],\"fields\":[{}],\"static\":[{}],\"dtype\":\"float32\"}}\n",
            kept.iter().map(|(y, _)| y.to_string()).collect::<Vec<_>>().join(","),
            q(&FIELDS),
            q(&statics.iter().map(|(s, _)| *s).collect::<Vec<_>>())
        ),
    )
    .unwrap();
    if !months.is_empty() {
        let mut bin = std::io::BufWriter::new(std::fs::File::create(format!("{prefix}_season.bin")).unwrap());
        for i in 0..months[0].len() {
            let v = months.iter().map(|m| m[i]).sum::<f32>() / months.len() as f32;
            bin.write_all(&v.to_le_bytes()).unwrap();
        }
        std::fs::write(format!("{prefix}_season.json"), format!("{{\"n\":{n},\"months\":12,\"fields\":[{}],\"start_day\":79,\"dtype\":\"float32\"}}\n", q(&MONTHLY))).unwrap();
    }
    if let Some(x) = pl.as_ref() {
        std::fs::write(
            format!("{prefix}_snaps.json"),
            format!(
                "{{\"years\":[{}],\"sow\":{sow},\"founders\":{},\"n\":{n},\"fine\":{},\"cell_m\":{},\"trees\":[\"x:f32\",\"y:f32\",\"height:f32\",\"crown_r:f32\",\"leaf:f32\",\"wood:f32\",\"age:f32\",\"genotype:u32\",\"born:u32\"],\"field\":[\"leaf x100\",\"height x50\",\"litter x50\",\"light under crowns x255\",\"years since fire (255 never)\"],\"traits\":[{}],\"traits_layout\":\"field's traits, trees' traits, then field, wood, crown, trees; float32 on n x n; seed_mass is its natural log\"}}\n",
                snaps.iter().map(|y| y.to_string()).collect::<Vec<_>>().join(","),
                x.founders,
                x.nf,
                x.fm,
                q(&TRAITS)
            ),
        )
        .unwrap();
        // the genotypes that hold trees at the end
        let mut held: std::collections::BTreeMap<u32, (usize, f64)> = std::collections::BTreeMap::new();
        for t in x.trees.iter().filter(|t| t.slot != NONE) {
            let e = held.entry(t.b.g).or_insert((0, 0.0));
            e.0 += 1;
            e.1 += t.b.mass();
        }
        let mut out = std::io::BufWriter::new(std::fs::File::create(format!("{prefix}_genes.csv")).unwrap());
        writeln!(out, "id,parent,born,genes,trees,tree_kg,{},alloc_leaf,alloc_root,alloc_seed,wing,conditional", TRAITS.join(",")).unwrap();
        for (g, (k, m)) in &held {
            let gt = x.gen[*g as usize].as_ref().unwrap();
            let ph = &gt.base;
            let v = trait_values(ph);
            writeln!(
                out,
                "{g},{},{},{},{k},{m:.3},{},{:.4},{:.4},{:.4},{:.4},{}",
                if gt.parent == NONE { -1 } else { gt.parent as i64 },
                gt.born,
                gt.genes.len(),
                v.iter().map(|x| format!("{x:.5}")).collect::<Vec<_>>().join(","),
                ph.alloc[0],
                ph.alloc[2],
                ph.alloc[4],
                ph.wing,
                gt.conditional() as u8
            )
            .unwrap();
        }
    }
    let mut row = std::fs::File::create(format!("{prefix}_row.csv")).unwrap();
    writeln!(row, "{}", Params::NAMES.join(",")).unwrap();
    writeln!(row, "{}", p.values().iter().map(|v| format!("{v}")).collect::<Vec<_>>().join(",")).unwrap();
    eprintln!("done: {prefix} in {:.0} s", t0.elapsed().as_secs_f64());
}
