//! The water on and under the ground, and the nutrients it carries (e102, #116).
//!
//! Water: a soil holds `cap` (its rock and depth); a basin holds `lake_cap` more before it spills; what
//! stands sinks slowly into the groundwater, which seeps back into the rivers; what is over a cell's
//! holding runs down the drainage network, all the way to the sea within the update.
//!
//! Nutrients A and B: the rock gives them (faster warm and wet); water leaving a cell takes a share of
//! each by its mobility; the rivers drop part where the land is flat and most in lakes, and the rest
//! enters the sea at the mouth, where it spreads and is slowly buried.

use crate::terrain::{nbrs, Terrain, NONE, ROCKS};
use crate::Params;

#[derive(Default, Clone, Copy)]
pub struct HFlux {
    pub to_sea: f64,     // mm of water run into the sea
    pub weathered_a: f64,
    pub weathered_b: f64,
    pub buried_a: f64,
    pub buried_b: f64,
    pub river_a: f64, // nutrient the rivers brought to the sea
    pub river_b: f64,
}

impl HFlux {
    pub fn add(&mut self, o: &HFlux) {
        self.to_sea += o.to_sea;
        self.weathered_a += o.weathered_a;
        self.weathered_b += o.weathered_b;
        self.buried_a += o.buried_a;
        self.buried_b += o.buried_b;
        self.river_a += o.river_a;
        self.river_b += o.river_b;
    }
}

pub struct Hydro {
    pub deep: Vec<f64>, // mm of groundwater
    pub q: Vec<f64>,    // mm run out of the cell in the last update (a river's discharge)
    pub a: Vec<f64>,    // nutrient A in the soil (land) or in the water (sea)
    pub b: Vec<f64>,
    inflow: Vec<f64>,
    in_a: Vec<f64>,
    in_b: Vec<f64>,
    scratch_a: Vec<f64>,
    scratch_b: Vec<f64>,
}

impl Hydro {
    pub fn new(t: &Terrain) -> Self {
        let cells = t.n * t.n;
        let z = vec![0.0; cells];
        Hydro {
            deep: z.clone(),
            q: z.clone(),
            a: z.clone(),
            b: z.clone(),
            inflow: z.clone(),
            in_a: z.clone(),
            in_b: z.clone(),
            scratch_a: z.clone(),
            scratch_b: z,
        }
    }

    pub fn water(&self) -> f64 {
        self.deep.iter().sum()
    }

    pub fn nutrients(&self) -> (f64, f64) {
        (self.a.iter().sum(), self.b.iter().sum())
    }

    /// One update, after the air's. `ground` is the air's (the soil's water and what stands on it),
    /// `temp` the cells' temperature.
    pub fn update(&mut self, p: &Params, t: &Terrain, ground: &mut [f64], temp: &[f64], rain: &[f64]) -> HFlux {
        let mut f = HFlux::default();
        let per = p.weather * p.tick / p.year; // a mean rock's nutrient an update
        // Standing water sinks; the rock weathers.
        for &c in &t.order {
            let c = c as usize;
            let standing = ground[c] - t.cap[c];
            if standing > 0.0 {
                let s = p.recharge * standing;
                ground[c] -= s;
                self.deep[c] += s;
            }
            let warm = (1.0 + (temp[c] - 15.0) / 15.0).clamp(0.0, 2.0);
            let wet = (ground[c] / t.cap[c]).min(1.0);
            let r = &ROCKS[t.rock[c] as usize];
            let (wa, wb) = (per * r.a * warm * wet, per * r.b * warm * wet);
            self.a[c] += wa;
            self.b[c] += wb;
            f.weathered_a += wa;
            f.weathered_b += wb;
        }
        // Down the network, upstream first: what is over a cell's holding runs on, with the groundwater's seep.
        for &c in &t.order {
            let c = c as usize;
            let hold = t.cap[c] + t.lake_cap[c];
            // Of this update's rain, the share that falls where the ground is already wet runs straight off
            // (a cell is not one bucket: its wet parts spill first), fill^beta.
            let quick = (rain[c] * (ground[c] / t.cap[c]).min(1.0).powf(p.beta)).min(ground[c]);
            ground[c] -= quick;
            let own = (ground[c] - hold).max(0.0) + quick; // what this cell's own water gives, not the river's
            let mut g = ground[c] + self.inflow[c];
            let mut out = (g - hold).max(0.0);
            g -= out;
            out += quick;
            let seep = p.base_flow * self.deep[c];
            self.deep[c] -= seep;
            out += seep;
            ground[c] = g;
            self.q[c] = out;
            // What the water brings, part of it dropped here: most in a lake, some where the land is flat.
            let drop = if t.lake_cap[c] > 1.0 { p.trap } else { p.deposit / (1.0 + t.slope[c] / p.depth_slope) };
            let (mut ca, mut cb) = (self.in_a[c], self.in_b[c]);
            self.a[c] += ca * drop;
            self.b[c] += cb * drop;
            ca *= 1.0 - drop;
            cb *= 1.0 - drop;
            // What it takes from this soil, by the share of the soil's own water that leaves and the mobility
            // (the river passing through a cell does not wash its soil).
            let lw = (own + seep) / (t.cap[c] + own + seep);
            let (la, lb) = (self.a[c] * (p.mob_a * lw).min(1.0), self.b[c] * (p.mob_b * lw).min(1.0));
            self.a[c] -= la;
            self.b[c] -= lb;
            ca += la;
            cb += lb;
            let d = t.down[c];
            debug_assert!(d != NONE);
            let d = d as usize;
            if t.sea[d] {
                f.to_sea += out;
                self.a[d] += ca;
                self.b[d] += cb;
                f.river_a += ca;
                f.river_b += cb;
            } else {
                self.inflow[d] += out;
                self.in_a[d] += ca;
                self.in_b[d] += cb;
            }
            self.inflow[c] = 0.0;
            self.in_a[c] = 0.0;
            self.in_b[c] = 0.0;
        }
        // The sea: what the rivers bring spreads, and a share is buried.
        let n = t.n;
        let m = 0.25 * p.sea_mix;
        self.scratch_a.iter_mut().for_each(|v| *v = 0.0);
        self.scratch_b.iter_mut().for_each(|v| *v = 0.0);
        for c in 0..n * n {
            if !t.sea[c] {
                continue;
            }
            let nb = nbrs(n, c);
            for &o in &nb[1..3] {
                // down and right: each edge once
                if t.sea[o] {
                    let da = m * (self.a[o] - self.a[c]);
                    let db = m * (self.b[o] - self.b[c]);
                    self.scratch_a[c] += da;
                    self.scratch_a[o] -= da;
                    self.scratch_b[c] += db;
                    self.scratch_b[o] -= db;
                }
            }
        }
        for c in 0..n * n {
            if t.sea[c] {
                self.a[c] += self.scratch_a[c];
                self.b[c] += self.scratch_b[c];
                let (ba, bb) = (self.a[c] * p.bury, self.b[c] * p.bury);
                self.a[c] -= ba;
                self.b[c] -= bb;
                f.buried_a += ba;
                f.buried_b += bb;
            }
        }
        f
    }
}
