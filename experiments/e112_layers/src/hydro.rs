//! The water on and under the ground, and the nutrients it carries (e102, #116).
//!
//! Water: a soil holds `cap` (its rock and depth); a basin holds `lake_cap` more before it spills; what
//! stands sinks slowly into the groundwater, which seeps back into the rivers; what is over a cell's
//! holding runs down the drainage network, all the way to the sea within the update.
//!
//! Nutrients A and B: the rock gives them (faster warm and wet); water leaving a cell takes a share of
//! each by its mobility; the rivers drop part where the land is flat and most in lakes, and the rest
//! enters the sea at the mouth, where it spreads and is slowly buried.

use crate::par::{self, Shared};
use crate::terrain::{Terrain, NONE, ROCKS};
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
        let threads = p.threads as usize;
        let n = t.n;
        let cells = n * n;
        let per = p.weather * p.tick / p.year; // a mean rock's nutrient an update
        let mut f = HFlux::default();
        // Standing water sinks; the rock weathers.
        {
            let (g, deep, a, b) = (Shared::new(ground), Shared::new(&mut self.deep), Shared::new(&mut self.a), Shared::new(&mut self.b));
            for x in par::pieces(threads, cells, |lo, hi| {
                let mut f = HFlux::default();
                for c in (lo..hi).filter(|&c| !t.sea[c]) {
                    let standing = *g.at(c) - t.cap[c];
                    if standing > 0.0 {
                        let s = p.recharge * standing;
                        *g.at(c) -= s;
                        *deep.at(c) += s;
                    }
                    let warm = (1.0 + (temp[c] - 15.0) / 15.0).clamp(0.0, 2.0);
                    let wet = (*g.at(c) / t.cap[c]).min(1.0);
                    let r = &ROCKS[t.rock[c] as usize];
                    let (wa, wb) = (per * r.a * warm * wet, per * r.b * warm * wet);
                    *a.at(c) += wa;
                    *b.at(c) += wb;
                    f.weathered_a += wa;
                    f.weathered_b += wb;
                }
                f
            }) {
                f.add(&x);
            }
        }
        // Down the network, upstream first, each group of basins on its own: what is over a cell's holding runs on,
        // with the groundwater's seep. What reaches the sea is added after, in the groups' order.
        let mouths = {
            let (g, deep, q, a, b) = (Shared::new(ground), Shared::new(&mut self.deep), Shared::new(&mut self.q), Shared::new(&mut self.a), Shared::new(&mut self.b));
            let (inflow, in_a, in_b) = (Shared::new(&mut self.inflow), Shared::new(&mut self.in_a), Shared::new(&mut self.in_b));
            par::over(threads, &t.groups, |group| {
                let mut out_sea: Vec<(u32, f64, f64)> = Vec::new();
                let mut f = HFlux::default();
                for &c in group {
                    let c = c as usize;
                    let hold = t.cap[c] + t.lake_cap[c];
                    // Of this update's rain, the share that falls where the ground is already wet runs straight off
                    // (a cell is not one bucket: its wet parts spill first), fill^beta.
                    let fill = (*g.at(c) / t.cap[c]).min(1.0);
                    let fb = if p.beta == 2.0 { fill * fill } else { fill.powf(p.beta) };
                    let quick = (rain[c] * fb).min(*g.at(c));
                    *g.at(c) -= quick;
                    let own = (*g.at(c) - hold).max(0.0) + quick; // what this cell's own water gives, not the river's
                    let mut gg = *g.at(c) + *inflow.at(c);
                    let mut out = (gg - hold).max(0.0);
                    gg -= out;
                    out += quick;
                    let seep = p.base_flow * *deep.at(c);
                    *deep.at(c) -= seep;
                    out += seep;
                    *g.at(c) = gg;
                    *q.at(c) = out;
                    // What the water brings, part of it dropped here: most in a lake, some where the land is flat.
                    let drop = if t.lake_cap[c] > 1.0 { p.trap } else { p.deposit / (1.0 + t.slope[c] / p.depth_slope) };
                    let (mut ca, mut cb) = (*in_a.at(c), *in_b.at(c));
                    *a.at(c) += ca * drop;
                    *b.at(c) += cb * drop;
                    ca *= 1.0 - drop;
                    cb *= 1.0 - drop;
                    // What it takes from this soil, by the share of the soil's own water that leaves and the mobility
                    // (the river passing through a cell does not wash its soil).
                    let lw = (own + seep) / (t.cap[c] + own + seep);
                    let (la, lb) = (*a.at(c) * (p.mob_a * lw).min(1.0), *b.at(c) * (p.mob_b * lw).min(1.0));
                    *a.at(c) -= la;
                    *b.at(c) -= lb;
                    ca += la;
                    cb += lb;
                    let d = t.down[c];
                    debug_assert!(d != NONE);
                    let d = d as usize;
                    if t.sea[d] {
                        f.to_sea += out;
                        f.river_a += ca;
                        f.river_b += cb;
                        out_sea.push((d as u32, ca, cb));
                    } else {
                        *inflow.at(d) += out;
                        *in_a.at(d) += ca;
                        *in_b.at(d) += cb;
                    }
                    *inflow.at(c) = 0.0;
                    *in_a.at(c) = 0.0;
                    *in_b.at(c) = 0.0;
                }
                (f, out_sea)
            })
        };
        for (x, out_sea) in &mouths {
            f.add(x);
            for &(d, ca, cb) in out_sea {
                self.a[d as usize] += ca;
                self.b[d as usize] += cb;
            }
        }
        // The sea: what the rivers bring spreads across the edges between sea cells, and a share is buried.
        {
            let m = 0.25 * p.sea_mix;
            let (sa, sb) = (Shared::new(&mut self.scratch_a), Shared::new(&mut self.scratch_b));
            let (a, b) = (&self.a, &self.b);
            par::pieces(threads, n, |ylo, yhi| {
                for y in ylo..yhi {
                    for x in 0..n {
                        let c = y * n + x;
                        if t.sea[c] {
                            *sa.at(c) = a[c] + sea_exchange(t, n, x, y, a, m);
                            *sb.at(c) = b[c] + sea_exchange(t, n, x, y, b, m);
                        }
                    }
                }
            });
        }
        {
            let (a, b) = (Shared::new(&mut self.a), Shared::new(&mut self.b));
            let (sa, sb) = (&self.scratch_a, &self.scratch_b);
            for x in par::pieces(threads, cells, |lo, hi| {
                let mut f = HFlux::default();
                for c in (lo..hi).filter(|&c| t.sea[c]) {
                    let (ba, bb) = (sa[c] * p.bury, sb[c] * p.bury);
                    *a.at(c) = sa[c] - ba;
                    *b.at(c) = sb[c] - bb;
                    f.buried_a += ba;
                    f.buried_b += bb;
                }
                f
            }) {
                f.add(&x);
            }
        }
        f
    }
}

/// What a sea cell gains across its edges with other sea cells, each edge's flow reckoned alike from both sides.
#[inline]
fn sea_exchange(t: &Terrain, n: usize, x: usize, y: usize, v: &[f64], m: f64) -> f64 {
    let c = y * n + x;
    let r = y * n + if x + 1 == n { 0 } else { x + 1 };
    let l = y * n + if x == 0 { n - 1 } else { x - 1 };
    let d = (if y + 1 == n { 0 } else { y + 1 }) * n + x;
    let u = (if y == 0 { n - 1 } else { y - 1 }) * n + x;
    let mut s = 0.0;
    if t.sea[r] {
        s += m * (v[r] - v[c]);
    }
    if t.sea[d] {
        s += m * (v[d] - v[c]);
    }
    if t.sea[l] {
        s -= m * (v[c] - v[l]);
    }
    if t.sea[u] {
        s -= m * (v[c] - v[u]);
    }
    s
}
