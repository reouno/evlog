//! What e106 shows the viewer (#124). Nothing happens unless EVLOG_VIEW is set, and a run that is watched
//! writes the same results as one that is not.
//!
//! A body is sent as its 8x8x8 voxels, each the function most of its tissue serves, at its middle; the
//! browser draws it as wide as `view_size` cells a kg^(1/3) of its mass - a body of 400 kg a third of a cell of
//! 63 km, some 50,000 times its size, and a small one smaller by the same rule. Its record adds its mass, the
//! animals it stands for and its lifespan.

use crate::body::{self, Bodies, Body};
use crate::climate::Air;
use crate::life::{Life, K};
use crate::terrain::{Terrain, NONE};
use crate::Params;
use std::collections::HashMap;
use std::f64::consts::TAU;

const SUB: usize = 64; // positions a cell's side is cut into on the wire
const RELIEF: f64 = 64.0; // the highest land, in cells, as drawn
const SEA: f64 = 3.0; // the deepest sea, as the viewer's water layer draws it
const SHALLOW: f64 = 200.0; // m of sea drawn as its deepest
const TEMP_OFFSET: f64 = 50.0;
const SIZE: f64 = 0.05; // cells a body is drawn wide, a kg^(1/3) of its mass

pub struct Watch {
    view: viewer::View,
    shapes: HashMap<(u32, u8), Vec<u8>>,
}

fn layer_specs() -> Vec<viewer::LayerSpec> {
    use viewer::{LayerSpec, Scale};
    vec![
        LayerSpec::new("water", (1.0 + SEA) as f32, Scale::Sqrt),
        LayerSpec::new("plant", 32.0, Scale::Sqrt), // kg a m2 of producers on land
        LayerSpec::new("temperature", 140.0, Scale::Linear),
        LayerSpec::new("moisture", 1.0, Scale::Linear),
        LayerSpec::new("rain", 20.0, Scale::Sqrt),
        LayerSpec::new("light", 1.0, Scale::Linear),
        LayerSpec::new("grass", 4.0, Scale::Sqrt), // stands under 2 m: what a short body reaches
        LayerSpec::new("wood", 32.0, Scale::Sqrt), // stands of 2 m and more
        LayerSpec::new("algae", 2.0, Scale::Sqrt), // producers in the sea
        LayerSpec::new("litter", 8.0, Scale::Sqrt),
    ]
}

impl Watch {
    pub fn open(prefix: &str, p: &Params, ter: &Terrain) -> Option<Watch> {
        let n = ter.n;
        let height: Vec<f32> = ter.elev.iter().map(|&e| if e >= 0.0 { e / p.relief * RELIEF } else { -SEA * (-e / SHALLOW).min(1.0) } as f32).collect();
        let band = vec![0u8; n * n];
        // The run's parameters, with the few the browser reads by name made to mean what it reads:
        // `relief` is the drawn one, and `weather` (the rock's weathering here) would read as a season law.
        let mut json = String::from("{");
        for (name, v) in Params::NAMES.iter().zip(p.values()) {
            let key = match *name {
                "relief" => "relief_m",
                "weather" => "weathering",
                k => k,
            };
            json.push_str(&format!("\"{key}\":{v},"));
        }
        json.push_str(&format!("\"relief\":{RELIEF},\"water_rain\":1,\"water_evap\":1,\"depth\":1,\"temperature_offset\":{TEMP_OFFSET},\"max_age\":0,\"view_size\":{SIZE}}}"));
        let view = viewer::View::from_env_ext(
            prefix,
            viewer::Init {
                experiment: "e106_bodies",
                w: n,
                h: n,
                sub: SUB,
                height: &height,
                band: &band,
                layers: layer_specs(),
                globals: vec!["season", "year", "pop"],
                blocks: vec!["empty", "hard", "muscle", "sensor", "digestive", "fat", "glue"],
                deaths: body::DEATHS.to_vec(),
                births: true,
                params: json,
            },
            viewer::Ext {
                voxels: true,
                fields: vec![("mass", "f32", None), ("animals", "f32", None), ("lifespan", "u16", None)],
                diets: vec!["leaf", "wood", "seed", "litter", "nothing yet"],
            },
        )?;
        Some(Watch { view, shapes: HashMap::new() })
    }

    /// Called after every update of the bodies: who died and who was born go out with the next frame,
    /// and on a frame's step the world does.
    pub fn update(&mut self, step: u64, p: &Params, ter: &Terrain, air: &Air, life: &Life, bodies: &mut Bodies) {
        for (id, cause) in bodies.died.drain(..) {
            self.view.died(step, id, cause);
        }
        for (child, parent) in bodies.born.drain(..) {
            self.view.born(step, child, parent);
        }
        if self.view.wants(step) {
            let layers = layers(p, ter, air, life);
            let refs: Vec<&[f64]> = layers.iter().map(|l| l.as_slice()).collect();
            let t = step as f64 / p.year;
            let globals = [(TAU * t).sin() as f32, t.fract() as f32, bodies.list.len() as f32];
            if self.shapes.len() > 100_000 {
                self.shapes.clear();
            }
            let shapes = &mut self.shapes;
            self.view.frame_ext(step, &refs, &globals, |push| {
                for b in &bodies.list {
                    let bt = bodies.types[b.g as usize].as_ref().unwrap();
                    let cells = shapes.entry((b.g, b.stage)).or_insert_with(|| body::voxels(bt, b.stage));
                    let (a, extra) = record(b, bt, p, cells);
                    push(a, &extra);
                }
            });
        }
        self.view.tick(step);
    }
}

/// One body as the viewer reads it: its growth from egg to adult (the gauge `energy` against `ripe`, the
/// maturity at which it breeds, both of 16), its fat against what it can hold, its water against what it
/// should hold, its age in days, and what it has mostly eaten.
fn record<'a>(b: &Body, bt: &body::BodyType, p: &Params, cells: &'a [u8]) -> (viewer::AgentIn<'a>, Vec<u8>) {
    let fm = &bt.forms[b.stage as usize];
    let egg = bt.egg();
    let span = (bt.adult() / egg).ln().max(1e-9);
    let grown = ((b.m / egg).max(1.0).ln() / span).clamp(0.0, 1.0);
    let fat_cap = b.m * (0.05 + p.fat_hold * fm.frac[4]);
    let eaten: f64 = b.eaten.iter().sum();
    let diet = if eaten <= 0.0 { 4 } else { (0..4).max_by(|&i, &j| b.eaten[i].partial_cmp(&b.eaten[j]).unwrap()).unwrap() as u8 };
    let lifespan = p.body_life + p.body_life_frame * fm.frac[0] * fm.frame_tough;
    let n = (1u32 << 16) as f64;
    let a = viewer::AgentIn {
        id: b.id as u32,
        lineage: if bt.root == NONE { 0 } else { bt.root + 1 },
        x: ((b.x * SUB as f64) % n) as u16,
        y: ((b.y * SUB as f64) % n) as u16,
        facing: b.facing,
        diet,
        fill: (b.w / b.target_water().max(1e-30)) as f32,
        energy: (16.0 * grown) as f32,
        ripe: (16.0 * bt.tr[3]) as f32,
        fat: (b.fat / fat_cap.max(1e-30)) as f32,
        age: b.age as u32,
        born: fm.nv as u16,
        side: 8,
        cells,
    };
    let mut extra = Vec::with_capacity(10);
    extra.extend_from_slice(&((b.m + b.fat) as f32).to_le_bytes());
    extra.extend_from_slice(&(b.s as f32).to_le_bytes());
    extra.extend_from_slice(&(lifespan.min(65535.0) as u16).to_le_bytes());
    (a, extra)
}

/// The cell layers, in the order of `layer_specs`.
fn layers(p: &Params, ter: &Terrain, air: &Air, life: &Life) -> Vec<Vec<f64>> {
    let cells = ter.n * ter.n;
    let mut v = vec![vec![0.0; cells]; 10];
    for c in 0..cells {
        let (mut all, mut short, mut tall) = (0.0, 0.0, 0.0);
        for i in 0..K {
            let x = &life.co[c * K + i];
            if x.g == NONE {
                continue;
            }
            let m = x.mass();
            all += m;
            if x.h < 2.0 {
                short += m;
            } else {
                tall += m;
            }
        }
        if ter.sea[c] {
            v[0][c] = 1.0 + SEA * (-ter.elev[c] / SHALLOW).min(1.0);
            v[3][c] = 1.0;
            v[8][c] = all;
        } else {
            let s = air.ground[c] - ter.cap[c];
            v[0][c] = if s > 10.0 { 1.0 + s / 1000.0 / p.relief * RELIEF } else { 0.0 };
            v[1][c] = all;
            v[3][c] = (air.ground[c] / ter.cap[c]).min(1.0);
            v[6][c] = short;
            v[7][c] = tall;
        }
        v[2][c] = air.temp[c] + TEMP_OFFSET;
        v[4][c] = air.rain_now[c];
        v[5][c] = air.light[c];
        v[9][c] = life.lit[c].m;
    }
    v
}
