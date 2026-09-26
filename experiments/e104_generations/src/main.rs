//! e104 (#116 rung 2): e103's world (base/ with producers that evolve as cohorts, the small eaters on their
//! leaves, litter, seeds and fire) with generations inside a stand: a cohort is an age class that dies at the
//! lifespan its wood sets, and a free slot is won by lottery from the seed bank.
//!
//! Rung 1 (e102): the ground with nothing living on it - terrain and sea (e061), rock provinces, soils,
//! a drainage network with lakes and groundwater, nutrients A and B that the rock gives and the water
//! carries, winds by latitude band, years that differ, storms.
//!
//! Run: cargo run --release -p base -- <prefix> [key=value ...] [file.params ...]
//! Writes `<prefix>_log.csv` (a row a year: the climate, the ledgers, the rivers), `<prefix>_maps.bin` +
//! `_maps.json` (each of the last `maps_years` years' annual maps, and the static ones), `_row.csv`.

mod climate;
mod genome;
mod hydro;
mod life;
mod noise;
mod terrain;

use climate::{Air, Flux, Sat, Weather};
use hydro::{HFlux, Hydro};
use life::{LFlux, Life, K};
use std::io::Write;
use std::time::Instant;
use terrain::Terrain;

const POOL: f64 = 500.0; // mm standing that makes a land cell a lake (e061)
const RIVER: f64 = 20.0; // mm an update run out of a cell: a river, for the log only

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
    years = 30.0, "years to run";
    maps_years = 10.0, "the last years whose annual maps are written";
    // e103: the living (#116 rung 2). Masses kg of dry matter a m2, nutrients g a m2, rates a year.
    life = 1.0, "the seed of the living (the terrain's is `seed`)";
    sow = 10.0, "the year the first producers are sown (the climate spun up before)";
    founders = 256.0, "random genomes sown (a quarter as many eaters)";
    sow_mass = 0.001, "kg of seed a genotype sown in a cell";
    threads = 4.0, "threads for the cells' life step";
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
    wind_seed = 20.0, "cells a winged seed of 0.01 g goes at full wing";
    float_seed = 50.0, "cells of river a floating seed goes at full float (mean)";
    river_q = 20.0, "mm an update out of a cell: a river that carries seeds";
    m_need = 1e-5, "kg of seed reserve at which half the seedlings establish in open wet ground";
    p_mut = 0.01, "chance a seed release carries a mutant genome, the whole release (e104: 1 seed in 100)";
    lightning = 0.05, "strikes a year a land cell";
    fire_spread = 0.8, "chance fire crosses to a dry neighbour with ample fuel";
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
    updates: usize,
}

const FIELDS: [&str; 16] = [
    "temp", "swing", "fill", "rain", "discharge", "lake", "a", "b", "biomass", "height", "lai", "litter", "eaters", "burnt", "transp", "lead",
];

impl Year {
    fn new(cells: usize) -> Self {
        let z = vec![0.0; cells];
        Year { temp: z.clone(), quarter: [z.clone(), z.clone(), z.clone(), z.clone()], fill: z.clone(), rain: z.clone(), q: z.clone(), lake: z, updates: 0 }
    }
    fn add(&mut self, t: &Terrain, air: &Air, hy: &Hydro, quarter: usize) {
        for c in 0..self.temp.len() {
            self.temp[c] += air.temp[c];
            self.quarter[quarter][c] += air.temp[c];
            self.rain[c] += air.rain_now[c];
            if !t.sea[c] {
                self.fill[c] += (air.ground[c] / t.cap[c]).min(1.0);
                self.q[c] += hy.q[c];
                if air.ground[c] - t.cap[c] >= POOL {
                    self.lake[c] += 1.0;
                }
            }
        }
        self.updates += 1;
    }
    /// The year's maps, in the order of `FIELDS`.
    fn maps(&self, hy: &Hydro, life: &Life, st: &State, p: &Params) -> Vec<Vec<f32>> {
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
            f(&st.biomass),
            f(&st.height),
            (0..cells).map(|c| (0..K).map(|i| &life.co[c * K + i]).filter(|x| x.g != terrain::NONE).map(|x| p.sla * x.o[0].m).sum::<f64>() as f32).collect(),
            life.lit.iter().map(|l| l.m as f32).collect(),
            (0..cells).map(|c| (0..life::E).map(|j| life.ea[c * life::E + j].m).sum::<f64>() as f32).collect(),
            f(&life.burnt),
            f(&life.transp),
            st.lead.iter().map(|&g| if g == terrain::NONE { -1.0 } else { g as f32 }).collect(),
        ]
    }
}

/// Each cell's living at a moment: its biomass, the tallest stand, and the genotype holding the most.
struct State {
    biomass: Vec<f64>,
    height: Vec<f64>,
    lead: Vec<u32>,
}

fn state(life: &Life, cells: usize) -> State {
    let mut s = State { biomass: vec![0.0; cells], height: vec![0.0; cells], lead: vec![terrain::NONE; cells] };
    for c in 0..cells {
        let mut best = 0.0;
        for i in 0..K {
            let x = &life.co[c * K + i];
            if x.g == terrain::NONE {
                continue;
            }
            let m = x.mass();
            s.biomass[c] += m;
            s.height[c] = s.height[c].max(x.h);
            if m > best {
                best = m;
                s.lead[c] = x.g;
            }
        }
    }
    s
}

/// A row a genotype that holds any of the living (producers, then eaters).
fn census(out: &mut impl Write, eout: &mut impl Write, life: &Life, ter: &Terrain, st: &State, year: usize, p: &Params) {
    let cells = ter.n * ter.n;
    let ng = life.gen.len();
    let (mut land, mut sea, mut hm, mut cnt, mut lead) = (vec![0.0; ng], vec![0.0; ng], vec![0.0; ng], vec![0u32; ng], vec![0u32; ng]);
    let (mut am, mut lsm) = (vec![0.0; ng], vec![0.0; ng]);
    for c in 0..cells {
        for i in 0..K {
            let x = &life.co[c * K + i];
            if x.g == terrain::NONE {
                continue;
            }
            let g = x.g as usize;
            let m = x.mass();
            if ter.sea[c] {
                sea[g] += m;
            } else {
                land[g] += m;
            }
            hm[g] += m * x.h;
            am[g] += m * x.age;
            lsm[g] += m * x.lifespan(p);
            cnt[g] += 1;
        }
        if st.lead[c] != terrain::NONE {
            lead[st.lead[c] as usize] += 1;
        }
    }
    let total: f64 = land.iter().sum::<f64>() + sea.iter().sum::<f64>();
    for g in 0..ng {
        let m = land[g] + sea[g];
        if cnt[g] == 0 || (m < 1e-7 * total && lead[g] == 0) {
            continue;
        }
        let gt = life.gen[g].as_ref().unwrap();
        let b = &gt.base;
        let keys: Vec<String> = b.keys[..b.n_keys].iter().map(|k| format!("{k:02x}")).collect();
        writeln!(
            out,
            "{year},{g},{},{},{},{:.6e},{:.6e},{},{},{:.4},{:.3},{:.3},{:.4},{:.4},{:.4},{:.4},{:.4},{:.5},{:.5},{:.5},{:.5},{:.5},{:.5},{:.4},{:.4},{:.4e},{:.4},{:.4},{:.5},{:.3},{:.3},{:.4},{},{},{}",
            gt.parent as i64 - if gt.parent == terrain::NONE { u32::MAX as i64 + 1 } else { 0 },
            gt.born,
            gt.genes.len(),
            land[g],
            sea[g],
            cnt[g],
            lead[g],
            hm[g] / m.max(1e-30),
            am[g] / m.max(1e-30),
            lsm[g] / m.max(1e-30),
            b.alloc[0], b.alloc[1], b.alloc[2], b.alloc[3], b.alloc[4],
            b.leaf_b, b.leaf_a, b.wood_b, b.wood_a, b.root_b, b.root_a,
            b.height, b.deep, b.seed_mass, b.wing, b.float, b.compound, b.t_opt, b.breadth, b.shed,
            b.n_keys, keys.join("-"), gt.conditional() as u8
        )
        .unwrap();
    }
    let ne = life.egen.len();
    let (mut em, mut ec) = (vec![0.0; ne], vec![0u32; ne]);
    for e in &life.ea {
        if e.g != terrain::NONE {
            em[e.g as usize] += e.m;
            ec[e.g as usize] += 1;
        }
    }
    let etot: f64 = em.iter().sum();
    for g in 0..ne {
        if ec[g] == 0 || em[g] < 1e-7 * etot {
            continue;
        }
        let gt = life.egen[g].as_ref().unwrap();
        let e = gt.eater.as_ref().unwrap();
        let keys: Vec<String> = e.keys.iter().map(|k| format!("{k:02x}")).collect();
        writeln!(
            eout,
            "{year},{g},{},{},{},{:.6e},{},{:.3},{:.3},{:.3},{},{}",
            gt.parent as i64 - if gt.parent == terrain::NONE { u32::MAX as i64 + 1 } else { 0 },
            gt.born,
            gt.genes.len(),
            em[g],
            ec[g],
            e.t_opt,
            e.tolerance,
            e.wing,
            e.keys.len(),
            keys.join("-")
        )
        .unwrap();
    }
}

fn main() {
    let args: Vec<String> = std::env::args().skip(1).collect();
    let prefix = args.first().expect("usage: e104_generations <prefix> [key=value ...] [file.params ...]").clone();
    let p = parse(&args[1..]);
    if let Some(dir) = std::path::Path::new(&prefix).parent() {
        std::fs::create_dir_all(dir).unwrap();
    }
    let t0 = Instant::now();
    let ter = Terrain::new(&p);
    let n = ter.n;
    let cells = n * n;
    let land = ter.sea.iter().filter(|&&s| !s).count();
    eprintln!("terrain: {n}x{n}, {land} land cells, {} in basins, {:.1} s", ter.lake_cap.iter().filter(|&&v| v > 1.0).count(), t0.elapsed().as_secs_f64());
    let sat = Sat::new();
    let mut wx = Weather::new(&p, cells);
    let mut air = Air::new(&p, &ter);
    let mut hy = Hydro::new(&ter);
    let mut life = Life::new(&ter, &p);
    let w0 = air.water() + hy.water();
    let (mut sea_net, mut na, mut nb) = (0.0f64, 0.0f64, 0.0f64); // what the open edges added
    let mut cm = 0.0f64; // the living's matter: fixed less returned
    let upy = (p.year / p.tick).round() as usize;
    let mut log = std::fs::File::create(format!("{prefix}_log.csv")).unwrap();
    writeln!(log, "step,year,land_temp,land_rain,land_evap,sea_evap,sea_rain,to_sea,water,water_err,a,b,a_err,b_err,weathered_a,weathered_b,river_a,river_b,buried_a,buried_b,rivers,lakes,storms,land_water,land_biomass,sea_biomass,land_cover,sea_cover,land_height,litter,eaters,eater_cells,gpp,resp,transp,eaten,decayed,burnt,burnt_cells,genotypes,eater_genotypes,leading,mutant_share,matter,c_err,ms_step").unwrap();
    let mut cen = std::io::BufWriter::new(std::fs::File::create(format!("{prefix}_census.csv")).unwrap());
    writeln!(cen, "year,id,parent,born,genes,mass_land,mass_sea,cells,lead_cells,h_real,age,lifespan,alloc_leaf,alloc_wood,alloc_root,alloc_store,alloc_seed,leaf_b,leaf_a,wood_b,wood_a,root_b,root_a,height,deep,seed_mass,wing,float,compound,t_opt,breadth,shed,n_keys,keys,conditional").unwrap();
    let mut ecen = std::io::BufWriter::new(std::fs::File::create(format!("{prefix}_eaters.csv")).unwrap());
    writeln!(ecen, "year,id,parent,born,genes,mass,cells,t_opt,tolerance,wing,n_keys,keys").unwrap();
    let mut leadbin = std::io::BufWriter::new(std::fs::File::create(format!("{prefix}_lead.bin")).unwrap());
    let mut lead_years: Vec<usize> = Vec::new();
    let mut kept: Vec<(usize, Vec<Vec<f32>>)> = Vec::new();
    let years = p.years as usize;
    for yr in 0..years {
        if yr > 0 {
            wx.new_year(&p);
        }
        let ty = Instant::now();
        let mut year = Year::new(cells);
        let (mut fl, mut hf, mut lf) = (Flux::default(), HFlux::default(), LFlux::default());
        life.transp.iter_mut().for_each(|v| *v = 0.0);
        life.burnt.iter_mut().for_each(|v| *v = 0.0);
        if yr == p.sow as usize {
            lf.add(&life.sow(&p, &mut hy.a, &mut hy.b, yr as u32));
        }
        for u in 0..upy {
            let step = (yr * upy + u) as f64 * p.tick;
            let f = air.update(&p, &ter, &sat, &mut wx, step, &life.cover);
            let h = hy.update(&p, &ter, &mut air.ground, &air.temp, &air.rain_now);
            fl.add(&f);
            hf.add(&h);
            if life.sown {
                life.accumulate(&air.light, &air.temp, &wx.hit);
                if life.due(&p) {
                    let l = life.step(&p, &ter, &sat, &mut air.ground, &mut air.vapor, &mut hy.deep, &mut hy.a, &mut hy.b, &hy.q, step);
                    lf.add(&l);
                }
            }
            year.add(&ter, &air, &hy, (u * 4 / upy).min(3));
        }
        sea_net += fl.sea_evap - fl.sea_rain - hf.to_sea;
        na += hf.weathered_a - hf.buried_a;
        nb += hf.weathered_b - hf.buried_b;
        cm += lf.fixed - lf.returned;
        let (lm, la, lb) = life.totals(&p);
        let w = air.water() + hy.water();
        let (a, b) = hy.nutrients();
        let (a, b) = (a + la, b + lb);
        let werr = (w - (w0 + sea_net)).abs() / w.max(1.0);
        let aerr = (a - na).abs() / a.max(1e-12);
        let berr = (b - nb).abs() / b.max(1e-12);
        let cerr = (lm - cm).abs() / lm.max(1e-12);
        let lfn = land as f64;
        let sfn = (cells - land) as f64;
        let u = year.updates as f64;
        let land_temp = (0..cells).filter(|&c| !ter.sea[c]).map(|c| year.temp[c]).sum::<f64>() / u / lfn;
        let rivers = (0..cells).filter(|&c| !ter.sea[c] && year.q[c] / u >= RIVER).count();
        let lakes = (0..cells).filter(|&c| !ter.sea[c] && year.lake[c] / u >= 0.5).count();
        let st = state(&life, cells);
        let (mut lbio, mut sbio, mut lcov, mut scov, mut lh) = (0.0, 0.0, 0usize, 0usize, 0.0);
        for c in 0..cells {
            if ter.sea[c] {
                sbio += st.biomass[c];
                scov += (st.biomass[c] > 0.001) as usize;
            } else {
                lbio += st.biomass[c];
                lcov += (st.biomass[c] > 0.01) as usize;
                lh += st.biomass[c] * st.height[c];
            }
        }
        let emass: f64 = life.ea.iter().map(|e| e.m).sum();
        let ecells = (0..cells).filter(|&c| (0..life::E).any(|j| life.ea[c * life::E + j].g != terrain::NONE)).count();
        let (ng, neg) = if life.sown { life.collect() } else { (0, 0) };
        let mutant: f64 = life.co.iter().filter(|x| x.g != terrain::NONE && life.gen[x.g as usize].as_ref().is_some_and(|g| g.born > p.sow as u32)).map(|x| x.mass()).sum();
        let mutant_share = mutant / (lbio + sbio).max(1e-30);
        let mut leads: Vec<u32> = st.lead.iter().cloned().filter(|&g| g != terrain::NONE).collect();
        leads.sort_unstable();
        leads.dedup();
        let ms = ty.elapsed().as_secs_f64() * 1000.0 / (upy as f64 * p.tick);
        writeln!(
            log,
            "{},{},{:.3},{:.1},{:.1},{:.6e},{:.6e},{:.1},{:.6e},{:.3e},{:.6e},{:.6e},{:.3e},{:.3e},{:.6e},{:.6e},{:.6e},{:.6e},{:.6e},{:.6e},{},{},{},{:.6e},{:.5},{:.5},{:.4},{:.4},{:.3},{:.5},{:.4e},{},{:.6e},{:.6e},{:.1},{:.6e},{:.6e},{:.6e},{},{},{},{},{:.6e},{:.6e},{:.3e},{:.3}",
            (yr + 1) * upy * p.tick as usize, yr + 1, land_temp, fl.land_rain / lfn, fl.land_evap / lfn, fl.sea_evap, fl.sea_rain, hf.to_sea / lfn,
            w, werr, a, b, aerr, berr, hf.weathered_a, hf.weathered_b, hf.river_a, hf.river_b, hf.buried_a, hf.buried_b,
            rivers, lakes, wx.storms_seen, air.ground.iter().sum::<f64>() + hy.water(),
            lbio / lfn, sbio / sfn, lcov as f64 / lfn, scov as f64 / sfn, lh / lbio.max(1e-30), life.lit.iter().map(|l| l.m).sum::<f64>() / cells as f64,
            emass / cells as f64, ecells, lf.gpp, lf.resp, lf.transp / lfn, lf.eaten, lf.decayed, lf.burnt, lf.burnt_cells, ng, neg, leads.len(), mutant_share, lm, cerr, ms
        )
        .unwrap();
        log.flush().unwrap();
        eprintln!(
            "year {:>3}: land {:.1} C, rain {:.0} mm, evap {:.0}, transp {:.0}, to sea {:.0}, land bio {:.3}, cover {:.2}/{:.2}, h {:.1}, eaters {:.2e}, burnt {}, genotypes {ng}/{neg}, leading {}, mutants {mutant_share:.3}, errs w {werr:.0e} A {aerr:.0e} C {cerr:.0e}, {:.1} s",
            yr + 1, land_temp, fl.land_rain / lfn, fl.land_evap / lfn, lf.transp / lfn, hf.to_sea / lfn, lbio / lfn, lcov as f64 / lfn, scov as f64 / sfn, lh / lbio.max(1e-30), emass / cells as f64, lf.burnt_cells, leads.len(), ty.elapsed().as_secs_f64()
        );
        eprintln!("  life secs: accumulate {:.1}, cells {:.1}, fire {:.1}, eaters {:.1}, seeds {:.1}", life.secs[0], life.secs[1], life.secs[2], life.secs[3], life.secs[4]);
        life.secs = [0.0; 5];
        if life.sown {
            census(&mut cen, &mut ecen, &life, &ter, &st, yr + 1, &p);
            cen.flush().unwrap();
            ecen.flush().unwrap();
            let from_sow = yr + 1 - p.sow as usize;
            if from_sow % (p.lead_every as usize) == 0 || yr + (p.maps_years as usize) >= years {
                for &g in &st.lead {
                    leadbin.write_all(&g.to_le_bytes()).unwrap();
                }
                lead_years.push(yr + 1);
            }
        }
        if yr + (p.maps_years as usize) >= years {
            kept.push((yr + 1, year.maps(&hy, &life, &st, &p)));
        }
    }
    leadbin.flush().unwrap();
    std::fs::write(format!("{prefix}_lead.json"), format!("{{\"n\":{n},\"years\":[{}],\"dtype\":\"uint32\",\"none\":{}}}\n", lead_years.iter().map(|y| y.to_string()).collect::<Vec<_>>().join(","), terrain::NONE)).unwrap();
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
    let mut row = std::fs::File::create(format!("{prefix}_row.csv")).unwrap();
    writeln!(row, "{}", Params::NAMES.join(",")).unwrap();
    writeln!(row, "{}", p.values().iter().map(|v| format!("{v}")).collect::<Vec<_>>().join(",")).unwrap();
    eprintln!("done: {prefix} in {:.0} s", t0.elapsed().as_secs_f64());
}
