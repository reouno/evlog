//! base: the world's code (#116). Each experiment copies this crate and changes what it tests; what the
//! world keeps comes back here (CLAUDE.md, Layout).
//!
//! Rung 1 (e102): the ground with nothing living on it - terrain and sea (e061), rock provinces, soils,
//! a drainage network with lakes and groundwater, nutrients A and B that the rock gives and the water
//! carries, winds by latitude band, years that differ, storms.
//!
//! Run: cargo run --release -p base -- <prefix> [key=value ...] [file.params ...]
//! Writes `<prefix>_log.csv` (a row a year: the climate, the ledgers, the rivers), `<prefix>_maps.bin` +
//! `_maps.json` (each of the last `maps_years` years' annual maps, and the static ones), `_row.csv`.

mod climate;
mod hydro;
mod noise;
mod terrain;

use climate::{Air, Flux, Sat, Weather};
use hydro::{HFlux, Hydro};
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

const FIELDS: [&str; 8] = ["temp", "swing", "fill", "rain", "discharge", "lake", "a", "b"];

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
        vec![
            self.temp.iter().map(|v| (v / u) as f32).collect(),
            swing,
            self.fill.iter().map(|v| (v / u) as f32).collect(),
            self.rain.iter().map(|v| *v as f32).collect(),
            self.q.iter().map(|v| (v / u) as f32).collect(),
            self.lake.iter().map(|v| (v / u) as f32).collect(),
            hy.a.iter().map(|v| *v as f32).collect(),
            hy.b.iter().map(|v| *v as f32).collect(),
        ]
    }
}

fn main() {
    let args: Vec<String> = std::env::args().skip(1).collect();
    let prefix = args.first().expect("usage: base <prefix> [key=value ...] [file.params ...]").clone();
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
    let w0 = air.water() + hy.water();
    let (mut sea_net, mut na, mut nb) = (0.0f64, 0.0f64, 0.0f64); // what the open edges added
    let upy = (p.year / p.tick).round() as usize;
    let mut log = std::fs::File::create(format!("{prefix}_log.csv")).unwrap();
    writeln!(log, "step,year,land_temp,land_rain,land_evap,sea_evap,sea_rain,to_sea,water,water_err,a,b,a_err,b_err,weathered_a,weathered_b,river_a,river_b,buried_a,buried_b,rivers,lakes,storms,land_water,ms_step").unwrap();
    let mut kept: Vec<(usize, Vec<Vec<f32>>)> = Vec::new();
    let years = p.years as usize;
    for yr in 0..years {
        if yr > 0 {
            wx.new_year(&p);
        }
        let ty = Instant::now();
        let mut year = Year::new(cells);
        let (mut fl, mut hf) = (Flux::default(), HFlux::default());
        for u in 0..upy {
            let step = (yr * upy + u) as f64 * p.tick;
            let f = air.update(&p, &ter, &sat, &mut wx, step);
            let h = hy.update(&p, &ter, &mut air.ground, &air.temp, &air.rain_now);
            fl.add(&f);
            hf.add(&h);
            year.add(&ter, &air, &hy, (u * 4 / upy).min(3));
        }
        sea_net += fl.sea_evap - fl.sea_rain - hf.to_sea;
        na += hf.weathered_a - hf.buried_a;
        nb += hf.weathered_b - hf.buried_b;
        let w = air.water() + hy.water();
        let (a, b) = hy.nutrients();
        let werr = (w - (w0 + sea_net)).abs() / w.max(1.0);
        let aerr = (a - na).abs() / a.max(1e-12);
        let berr = (b - nb).abs() / b.max(1e-12);
        let lf = land as f64;
        let u = year.updates as f64;
        let land_temp = (0..cells).filter(|&c| !ter.sea[c]).map(|c| year.temp[c]).sum::<f64>() / u / lf;
        let rivers = (0..cells).filter(|&c| !ter.sea[c] && year.q[c] / u >= RIVER).count();
        let lakes = (0..cells).filter(|&c| !ter.sea[c] && year.lake[c] / u >= 0.5).count();
        let ms = ty.elapsed().as_secs_f64() * 1000.0 / (upy as f64 * p.tick);
        writeln!(
            log,
            "{},{},{:.3},{:.1},{:.1},{:.6e},{:.6e},{:.1},{:.6e},{:.3e},{:.6e},{:.6e},{:.3e},{:.3e},{:.6e},{:.6e},{:.6e},{:.6e},{:.6e},{:.6e},{},{},{},{:.6e},{:.3}",
            (yr + 1) * upy * p.tick as usize, yr + 1, land_temp, fl.land_rain / lf, fl.land_evap / lf, fl.sea_evap, fl.sea_rain, hf.to_sea / lf,
            w, werr, a, b, aerr, berr, hf.weathered_a, hf.weathered_b, hf.river_a, hf.river_b, hf.buried_a, hf.buried_b,
            rivers, lakes, wx.storms_seen, air.ground.iter().sum::<f64>() + hy.water(), ms
        )
        .unwrap();
        log.flush().unwrap();
        eprintln!("year {:>3}: land {:.1} C, rain {:.0} mm, rivers {rivers}, lakes {lakes}, water err {werr:.1e}, A err {aerr:.1e}, {:.1} s", yr + 1, land_temp, fl.land_rain / lf, ty.elapsed().as_secs_f64());
        if yr + (p.maps_years as usize) >= years {
            kept.push((yr + 1, year.maps(&hy)));
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
