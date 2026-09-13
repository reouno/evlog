//! e062: the producers. Stage B of the foundation (#75, `foundation.md`): grass, wood and algae
//! as fields of matter, with their litter and fire, on a stage-A world (e061's climate, ported as
//! it is). No bodies.
//!
//! The climate runs alone for `spinup` updates (in whole years: e061's worlds settle in about
//! 20,000), then the producers start on every cell and run for at least `years` years and `steps`
//! steps, on the climate's clock (every `tick` steps). The laws are in `plants.rs`.
//!
//! Run: cargo run --release -p e062_producers -- <prefix> [key=value ...] [file.params ...]
//! `<prefix>_row.csv` is one row of parameters and measures, `<prefix>_years.csv` a row a year of
//! the producers, and with maps=1 `<prefix>_maps.bin` the maps of the last year.

mod climate;
mod habitat;
mod plants;

use climate::{Flux, Sat, World};
use habitat::*;
use plants::Plants;
use std::f64::consts::TAU;
use std::io::Write;
use std::time::Instant;

// ---- the pass lines of stage B (#75) ----

const PRODUCER_SHARE: f64 = 0.05; // each producer holds this share of the world's standing plant matter
const LARGER_PART: f64 = 0.5; // and is this part of the standing matter of at least one habitat
const DENSE: f64 = 0.1; // that holds at least this much of the world's mean plant matter a cell
const ALIVE: f64 = 0.01; // none falls under this share at the end of any year
const BURN_LO: f64 = 0.01; // share of the land burnt a year
const BURN_HI: f64 = 0.20;
const MATTER_ERR: f64 = 1e-9;
const PRODUCERS: [&str; 3] = ["grass", "wood", "algae"];

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
    years = 10.0, "years of producers, at least";
    steps = 200000.0, "steps of producers, at least (a world with a short year runs more years)";
    grass_rate = 0.006, "matter grass grows a step at full cover, the sun overhead, warm and wet";
    wood_rate = 0.0024, "the same for wood";
    algae_rate = 0.01, "the same for algae, in shallow water";
    ignite = 1e-6, "chance a strike hits a cell in an update (it catches if dry, warm and fuelled)";
    matter = 10.0, "matter a cell holds at the start, in its soil and its producers";
    maps = 0.0, "1: write the maps of the last year";
}

/// What the viewer is told a cell holds: the height in the units e059 drew (a relief of 64).
const VIEW_RELIEF: f64 = 64.0;
const VIEW_SEA: f64 = 3.0; // the drawn depth of the sea past the shelf
const TEMP_OFFSET: f64 = 50.0; // the temperature layer is sent as C + 50 (bytes are unsigned)

fn main() {
    let args: Vec<String> = std::env::args().skip(1).collect();
    let prefix = args.first().expect("usage: e062_producers <prefix> [key=value ...] [file.params ...]").clone();
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
    for a in &args[1..] {
        if a.contains('=') {
            apply(a, &mut p);
        } else {
            for line in std::fs::read_to_string(a).unwrap_or_else(|e| panic!("{a}: {e}")).lines() {
                apply(line, &mut p);
            }
        }
    }
    if let Some(dir) = std::path::Path::new(&prefix).parent() {
        std::fs::create_dir_all(dir).ok();
    }

    let started = Instant::now();
    let sat = Sat::new();
    let mut w = World::new(&p);
    let n = w.n;
    let cells = n * n;
    let per_quarter = ((p.year / p.tick / 4.0).round() as usize).max(1);
    let per_year = 4 * per_quarter;
    let spin_years = (p.spinup as usize).div_ceil(per_year);
    let years = (p.years.max(1.0) as usize).max(((p.steps / p.tick).ceil() as usize).div_ceil(per_year));
    let land_cells = w.sea.iter().filter(|&&s| !s).count().max(1) as f64;
    let sea_cells = (cells as f64 - land_cells).max(1.0);

    // The climate alone, until it has settled.
    let mut update_i: u64 = 0;
    for _ in 0..spin_years * per_year {
        w.update(&p, &sat, update_i as f64 * p.tick);
        update_i += 1;
    }
    let spin_seconds = started.elapsed().as_secs_f64();
    eprintln!("spun up {spin_years} years ({update_i} updates) in {spin_seconds:.1} s; producers for {years} years");
    let first_update = update_i;
    let water0 = w.water();
    let mut pl = Plants::new(&w, &p);
    let matter0 = pl.matter();
    let matter_on = |pl: &Plants, w: &World, sea: bool| (0..cells).filter(|&c| w.sea[c] == sea).map(|c| pl.soil[c] + pl.grass[c] + pl.wood[c] + pl.algae[c] + pl.litter[c]).sum::<f64>();
    let land_matter0 = matter_on(&pl, &w, false) / land_cells;

    // The viewer: nothing unless EVLOG_VIEW is set. Its clock starts with the producers.
    let view_height = |e: f64| if e >= 0.0 { e / p.relief * VIEW_RELIEF } else { -VIEW_SEA * (-e / SHALLOW).min(1.0) };
    let height_view: Vec<f32> = w.elev.iter().map(|&e| view_height(e) as f32).collect();
    let band = vec![0u8; cells];
    let mut json = String::from("{");
    for (name, v) in Params::NAMES.iter().zip(p.values()) {
        let key = if *name == "relief" { "relief_m" } else { name };
        json.push_str(&format!("\"{key}\":{v},"));
    }
    json.push_str(&format!("\"relief\":{VIEW_RELIEF},\"water_rain\":1,\"water_evap\":1,\"depth\":1,\"temperature_offset\":{TEMP_OFFSET},\"habitats\":[{}]}}", HAB_NAMES.iter().map(|h| format!("\"{h}\"")).collect::<Vec<_>>().join(",")));
    let mut view = viewer::View::from_env(
        &prefix,
        viewer::Init {
            experiment: "e062_producers",
            w: n,
            h: n,
            sub: 4,
            height: &height_view,
            band: &band,
            layers: vec![
                viewer::LayerSpec::new("water", (1.0 + VIEW_SEA) as f32, viewer::Scale::Sqrt),
                viewer::LayerSpec::new("plant", 16.0, viewer::Scale::Sqrt),
                viewer::LayerSpec::new("soil", 20.0, viewer::Scale::Sqrt),
                viewer::LayerSpec::new("temperature", 100.0, viewer::Scale::Linear),
                viewer::LayerSpec::new("moisture", 1.0, viewer::Scale::Linear),
                viewer::LayerSpec::new("rain", 2.0, viewer::Scale::Sqrt),
                viewer::LayerSpec::new("light", 1.0, viewer::Scale::Linear),
                viewer::LayerSpec::new("habitat", 255.0, viewer::Scale::Linear),
                viewer::LayerSpec::new("grass", 4.0, viewer::Scale::Sqrt),
                viewer::LayerSpec::new("wood", 16.0, viewer::Scale::Sqrt),
                viewer::LayerSpec::new("algae", 2.0, viewer::Scale::Sqrt),
                viewer::LayerSpec::new("litter", 8.0, viewer::Scale::Sqrt),
                viewer::LayerSpec::new("fire", 1.0, viewer::Scale::Linear),
            ],
            globals: vec!["season", "year"],
            blocks: vec!["empty"],
            deaths: vec![],
            births: false,
            params: json,
        },
    );

    let mut years_csv = String::from("year,habitats,grass,wood,algae,litter,soil_land,soil_sea,air,share_grass,share_wood,share_algae,grown_grass,grown_wood,grown_algae,burnt,fires,largest_fire,land_matter,sea_matter,land_temp,rain_land,matter_err,water_err\n");
    let mut q = Quarter::new(cells);
    let mut last_map = vec![255u8; cells];
    let mut middle: Option<(Vec<Vec<u8>>, [f64; 3])> = None;
    let mut min_share = [f64::INFINITY; 3];
    let (mut burnt_late, mut late_years, mut fires_late, mut largest_late) = (0.0f64, 0usize, 0usize, 0u32);
    let mut flux_all = Flux::default();
    let mut row_measures = String::new();
    let mut maps_out: Vec<u8> = Vec::new();
    let produce_started = Instant::now();

    for yr in 1..=years {
        let mut maps: Vec<Vec<u8>> = Vec::with_capacity(4);
        let mut flux = Flux::default();
        let mut grown = [0.0f64; 3];
        let fire_start = pl.fire_sizes.len();
        let (mut hc, mut hg, mut hw, mut ha) = ([0.0f64; N_HAB], [0.0f64; N_HAB], [0.0f64; N_HAB], [0.0f64; N_HAB]);
        let mut temp_land = 0.0f64;
        let mut detail: Vec<u8> = Vec::new();
        for _quarter in 0..4 {
            q.clear();
            for _ in 0..per_quarter {
                let step = update_i as f64 * p.tick;
                flux.add(&w.update(&p, &sat, step));
                let g = pl.update(&w, &p, yr as u32);
                grown[0] += g.grass;
                grown[1] += g.wood;
                grown[2] += g.algae;
                q.add(&w, &pl, p.soil);
                update_i += 1;
                if let Some(v) = view.as_mut() {
                    let at = ((update_i - first_update) as f64 * p.tick) as u64;
                    if v.wants(at) {
                        let water: Vec<f64> = (0..cells)
                            .map(|c| {
                                if w.sea[c] {
                                    1.0 + VIEW_SEA * (-w.elev[c] / SHALLOW).min(1.0)
                                } else {
                                    let s = w.ground[c] - p.soil;
                                    if s > 10.0 { 1.0 + s / 1000.0 / p.relief * VIEW_RELIEF } else { 0.0 }
                                }
                            })
                            .collect();
                        let plant: Vec<f64> = (0..cells).map(|c| pl.grass[c] + pl.wood[c]).collect();
                        let temp: Vec<f64> = w.temp.iter().map(|t| t + TEMP_OFFSET).collect();
                        let moisture: Vec<f64> = (0..cells).map(|c| if w.sea[c] { 1.0 } else { (w.ground[c] / p.soil).min(1.0) }).collect();
                        let hab: Vec<f64> = last_map.iter().map(|&h| h as f64).collect();
                        let mut fire = vec![0.0f64; cells];
                        for &(c, _) in &pl.front {
                            fire[c as usize] = 1.0;
                        }
                        let t = step + p.tick;
                        v.frame(at, &[&water, &plant, &pl.soil, &temp, &moisture, &w.rain_now, &w.light, &hab, &pl.grass, &pl.wood, &pl.algae, &pl.litter, &fire], &[(TAU * t / p.year).sin() as f32, (t / p.year).fract() as f32], |_push| {});
                    }
                    v.tick(at);
                }
            }
            let map = q.habitats(&w);
            let u = q.updates.max(1) as f64;
            for c in 0..cells {
                let h = map[c] as usize;
                hc[h] += 1.0;
                hg[h] += q.grass[c] / u;
                hw[h] += q.wood[c] / u;
                ha[h] += q.algae[c] / u;
                if !w.sea[c] {
                    temp_land += q.temp[c] / u;
                }
            }
            if p.maps > 0.0 && yr == years {
                detail.extend_from_slice(&map);
                for v in [&q.temp, &q.moist, &q.grass, &q.wood, &q.algae] {
                    for x in v.iter() {
                        detail.extend_from_slice(&((x / u) as f32).to_le_bytes());
                    }
                }
            }
            last_map = map.clone();
            maps.push(map);
        }

        // The year's row.
        flux_all.add(&flux);
        let tot = [hg.iter().sum::<f64>(), hw.iter().sum::<f64>(), ha.iter().sum::<f64>()];
        let standing = (tot[0] + tot[1] + tot[2]).max(1e-300);
        let share = tot.map(|t| t / standing);
        let end = [pl.grass.iter().sum::<f64>(), pl.wood.iter().sum::<f64>(), pl.algae.iter().sum::<f64>()];
        let end_all = (end[0] + end[1] + end[2]).max(1e-300);
        for k in 0..3 {
            min_share[k] = min_share[k].min(end[k] / end_all);
        }
        let burnt = (0..cells).filter(|&c| !w.sea[c] && pl.burnt_in[c] == yr as u32).count() as f64 / land_cells;
        let fires = pl.fire_sizes.len() - fire_start;
        let largest = pl.fire_sizes[fire_start..].iter().copied().max().unwrap_or(0);
        if 2 * yr > years {
            burnt_late += burnt;
            late_years += 1;
            fires_late += fires;
            largest_late = largest_late.max(largest);
        }
        let matter_err = (pl.matter() - matter0).abs() / matter0;
        let water_err = (w.water() - water0 - (flux_all.sea_evap - flux_all.sea_rain - flux_all.runoff)).abs() / (w.water() + flux_all.sea_evap + flux_all.land_rain).max(1.0);
        let habitats = shares(&maps).iter().filter(|&&s| s >= SHARE).count();
        let (litter, soil_land, soil_sea) = (
            pl.litter.iter().sum::<f64>(),
            (0..cells).filter(|&c| !w.sea[c]).map(|c| pl.soil[c]).sum::<f64>(),
            (0..cells).filter(|&c| w.sea[c]).map(|c| pl.soil[c]).sum::<f64>(),
        );
        let steps_year = per_year as f64 * p.tick;
        let land_temp = temp_land / (4.0 * land_cells);
        let rain_land = flux.land_rain / land_cells;
        years_csv.push_str(&format!(
            "{yr},{habitats},{:.1},{:.1},{:.1},{litter:.1},{soil_land:.1},{soil_sea:.1},{:.3},{:.4},{:.4},{:.4},{:.3e},{:.3e},{:.3e},{burnt:.4},{fires},{largest},{:.3},{:.3},{land_temp:.2},{rain_land:.1},{matter_err:.2e},{water_err:.2e}\n",
            end[0],
            end[1],
            end[2],
            pl.air,
            share[0],
            share[1],
            share[2],
            grown[0] / cells as f64 / steps_year,
            grown[1] / cells as f64 / steps_year,
            grown[2] / cells as f64 / steps_year,
            matter_on(&pl, &w, false) / land_cells,
            matter_on(&pl, &w, true) / sea_cells,
        ));
        eprintln!(
            "year {yr}: grass/wood/algae {:.2}/{:.2}/{:.2} a cell (shares {:.2}/{:.2}/{:.2}), litter {:.2}, burnt {:.3} of the land in {fires} fires (largest {largest}), land matter {:.2}, err {matter_err:.1e}",
            end[0] / cells as f64,
            end[1] / cells as f64,
            end[2] / cells as f64,
            share[0],
            share[1],
            share[2],
            litter / cells as f64,
            burnt,
            matter_on(&pl, &w, false) / land_cells,
        );

        if yr == (years / 2).max(1) {
            middle = Some((maps.clone(), end));
        }
        if yr == years {
            let sh = shares(&maps);
            let widths = median_widths(&maps, n);
            let wide = (0..N_HAB).filter(|&h| sh[h] >= SHARE && widths[h] >= WIDE).count();
            let ch = change(&maps);
            let (mid_maps, mid_end) = middle.as_ref().unwrap();
            let stand = agree(&maps, mid_maps);
            let mean_density = standing / (4.0 * cells as f64);
            let mut larger = [0usize; 3];
            for h in 0..N_HAB {
                let all = hg[h] + hw[h] + ha[h];
                if sh[h] >= SHARE && all / hc[h] >= DENSE * mean_density {
                    for (k, part) in [hg[h], hw[h], ha[h]].iter().enumerate() {
                        if part / all >= LARGER_PART {
                            larger[k] += 1;
                        }
                    }
                }
            }
            let fire = burnt_late / late_years.max(1) as f64;
            let pass_share = share.iter().all(|&s| s >= PRODUCER_SHARE);
            let pass_larger = larger.iter().all(|&k| k >= 1);
            let pass_alive = min_share.iter().all(|&s| s >= ALIVE);
            let pass_fire = (BURN_LO..=BURN_HI).contains(&fire);
            let pass_matter = matter_err < MATTER_ERR;
            let produce_seconds = produce_started.elapsed().as_secs_f64();
            row_measures = format!(
                "{habitats},{wide},{ch:.4},{stand:.4},{:.4},{:.4},{:.4},{:.4},{:.4},{:.4},{},{},{},{fire:.4},{:.1},{largest_late},{matter_err:.2e},{:.3},{:.3},{:.3},{:.3},{},{},{},{},{},{},{land_temp:.2},{rain_land:.1},{spin_seconds:.1},{produce_seconds:.1},{:.3},{years}",
                share[0],
                share[1],
                share[2],
                min_share[0],
                min_share[1],
                min_share[2],
                larger[0],
                larger[1],
                larger[2],
                fires_late as f64 / late_years.max(1) as f64,
                end[0] / mid_end[0].max(1e-300),
                end[1] / mid_end[1].max(1e-300),
                end[2] / mid_end[2].max(1e-300),
                matter_on(&pl, &w, false) / land_cells / land_matter0,
                pass_share as u8,
                pass_larger as u8,
                pass_alive as u8,
                pass_fire as u8,
                pass_matter as u8,
                (pass_share && pass_larger && pass_alive && pass_fire && pass_matter) as u8,
                produce_seconds * 1000.0 / (update_i - first_update) as f64,
            );
            for h in 0..N_HAB {
                let all = hg[h] + hw[h] + ha[h];
                let d = |x: f64| if all > 0.0 { x / all } else { 0.0 };
                row_measures.push_str(&format!(",{:.4},{:.4},{:.3},{:.3},{:.3}", sh[h], all / hc[h].max(1.0), d(hg[h]), d(hw[h]), d(ha[h])));
            }
            if p.maps > 0.0 {
                maps_out.extend_from_slice(b"E062");
                maps_out.extend_from_slice(&(n as u32).to_le_bytes());
                for &e in &w.elev {
                    maps_out.extend_from_slice(&(e as f32).to_le_bytes());
                }
                maps_out.extend_from_slice(&detail);
                for c in 0..cells {
                    maps_out.push((pl.burnt_in[c] == yr as u32) as u8);
                }
                for v in [&pl.litter, &pl.soil] {
                    for x in v.iter() {
                        maps_out.extend_from_slice(&(*x as f32).to_le_bytes());
                    }
                }
            }
        }
    }

    let mut header: Vec<String> = Params::NAMES.iter().map(|s| s.to_string()).collect();
    for m in ["habitats", "wide", "change", "stand"] {
        header.push(m.to_string());
    }
    for pre in ["share", "min_share", "larger"] {
        for pr in PRODUCERS {
            header.push(format!("{pre}_{pr}"));
        }
    }
    for m in ["burnt", "fires", "largest_fire", "matter_err", "drift_grass", "drift_wood", "drift_algae", "land_matter", "pass_share", "pass_larger", "pass_alive", "pass_fire", "pass_matter", "pass", "land_temp", "rain_land", "spin_seconds", "produce_seconds", "ms_per_update", "years_run"] {
        header.push(m.to_string());
    }
    for h in HAB_NAMES {
        for m in ["share", "density", "grass", "wood", "algae"] {
            header.push(format!("{m}_{h}"));
        }
    }
    let values = p.values().iter().map(|v| format!("{v}")).collect::<Vec<_>>().join(",");
    std::fs::write(format!("{prefix}_row.csv"), format!("{}\n{values},{row_measures}\n", header.join(","))).unwrap();
    std::fs::write(format!("{prefix}_years.csv"), years_csv).unwrap();
    if p.maps > 0.0 {
        std::fs::File::create(format!("{prefix}_maps.bin")).unwrap().write_all(&maps_out).unwrap();
    }
    let _ = Params::DOCS;
    eprintln!("done: {prefix} in {:.1} s ({:.3} ms a producer update)", started.elapsed().as_secs_f64(), produce_started.elapsed().as_secs_f64() * 1000.0 / (update_i - first_update).max(1) as f64);
}

#[cfg(test)]
mod tests {
    use super::*;

    fn small() -> Params {
        let mut p = Params::default();
        p.size = 32.0;
        p.grain = 16.0;
        p
    }

    /// A world of land, warm, lit and with its ground at `fill`, everywhere.
    fn flat_land(p: &Params, fill: f64) -> World {
        let mut w = World::new(p);
        let cells = w.n * w.n;
        w.sea = vec![false; cells];
        w.elev = vec![100.0; cells];
        w.ground = vec![fill * p.soil; cells];
        w.temp = vec![25.0; cells];
        w.light = vec![0.3; cells];
        w.rain_now = vec![0.0; cells];
        w
    }

    /// e061's climate is unchanged: the water adds up to what the sea gave less what it took back.
    #[test]
    fn water_is_conserved() {
        let p = small();
        let sat = Sat::new();
        let mut w = World::new(&p);
        let start = w.water();
        let mut net = 0.0;
        for i in 0..3000 {
            let f = w.update(&p, &sat, i as f64 * p.tick);
            net += f.sea_evap - f.sea_rain - f.runoff;
        }
        let end = w.water();
        assert!((end - start - net).abs() < 1e-6 * (end + start), "water {start} -> {end}, net from the sea {net}");
    }

    /// Growth, death, rot, fire and the air's fall move matter and never make or lose it.
    #[test]
    fn matter_is_conserved() {
        let mut p = small();
        p.ignite = 0.01;
        p.rain = 0.3;
        let sat = Sat::new();
        let mut w = World::new(&p);
        for i in 0..2000 {
            w.update(&p, &sat, i as f64 * p.tick);
        }
        let mut pl = Plants::new(&w, &p);
        let start = pl.matter();
        let (mut burnt, mut fell, mut grown) = (0.0, 0.0, 0.0);
        for i in 2000..6000 {
            w.update(&p, &sat, i as f64 * p.tick);
            // Dry half the land now and then, so that it burns.
            if i % 500 == 0 {
                for c in 0..w.ground.len() / 2 {
                    w.ground[c] = w.ground[c].min(10.0);
                }
            }
            let f = pl.update(&w, &p, 1 + i as u32 / 2000);
            burnt += f.burnt;
            fell += f.fell;
            grown += f.grass + f.wood + f.algae;
        }
        assert!(grown > 0.0 && burnt > 0.0 && fell > 0.0, "grown {grown}, burnt {burnt}, fell {fell}");
        assert!((pl.matter() - start).abs() < 1e-9 * start, "matter {start} -> {}", pl.matter());
    }

    /// A fire takes the fuel and the share of the wood the fuel stands for, and stops at wet ground.
    #[test]
    fn fire_stops_at_wet_ground() {
        let mut p = small();
        p.ignite = 0.0;
        let mut w = flat_land(&p, 0.1);
        let n = w.n;
        w.light = vec![0.0; n * n];
        for y in 0..n {
            w.ground[y * n + 16] = p.soil; // a wet column at x = 16
        }
        let mut pl = Plants::new(&w, &p);
        for c in 0..n * n {
            pl.grass[c] = 5.0;
            pl.soil[c] -= 4.5;
        }
        let start = pl.matter();
        let lit = 5 * n + 3;
        pl.fire_sizes.push(0);
        pl.front.push((lit as u32, 0));
        for _ in 0..200 {
            pl.update(&w, &p, 1);
        }
        let burnt: Vec<usize> = (0..n * n).filter(|&c| pl.burnt_in[c] == 1).collect();
        assert!(burnt.len() > 100, "burnt {}", burnt.len());
        assert!(burnt.iter().all(|&c| c % n != 16), "a fire crossed wet ground");
        let c = burnt[burnt.len() / 2];
        assert_eq!(pl.grass[c], 0.0);
        // 1 x (1 - 5 / 6) = 0.167, less what of the wood died before the fire came (0.05% an update)
        assert!(pl.wood[c] > 0.12 && pl.wood[c] < 0.167, "wood left {}", pl.wood[c]);
        assert!((pl.matter() - start).abs() < 1e-9 * start);
    }

    /// A producer reaches a cell only from its neighbors, one cell an update at most.
    #[test]
    fn grass_spreads_from_its_neighbors() {
        let p = small();
        let w = flat_land(&p, 1.0);
        let n = w.n;
        let mut pl = Plants::new(&w, &p);
        for c in 0..n * n {
            pl.soil[c] += pl.grass[c] + pl.wood[c];
            pl.grass[c] = 0.0;
            pl.wood[c] = 0.0;
        }
        let (x0, y0) = (10usize, 10usize);
        pl.grass[y0 * n + x0] = 1.0;
        pl.soil[y0 * n + x0] -= 1.0;
        for k in 1..=5usize {
            pl.update(&w, &p, 1);
            for y in 0..n {
                for x in 0..n {
                    let d = x.abs_diff(x0).min(n - x.abs_diff(x0)) + y.abs_diff(y0).min(n - y.abs_diff(y0));
                    let g = pl.grass[y * n + x];
                    assert!(if d > k { g == 0.0 } else { true }, "grass {g} at distance {d} after {k} updates");
                }
            }
        }
        assert!(pl.grass[y0 * n + x0 + 3] > 0.0);
    }
}
