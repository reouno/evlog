//! e061: the climate. Stage A of the foundation (#74, `foundation.md`): the environment alone.
//!
//! Generated from the seed: a height map and a sea level, over a span of latitude (land, sea,
//! islands and lakes are results). Laws: the sun with a day and a year; heat, going toward what
//! the sun gives less what the height takes and spreading to the neighbors by capacity; water,
//! taken up by the air by temperature, carried by one wind that turns with the season, raining
//! where the air holds more than it can (it has risen or cooled), soaking into the ground and
//! running downhill to the sea. No producers and no bodies.
//!
//! The climate updates every `tick` steps of the bodies' clock (10): a year of 20,000 steps is
//! 2,000 updates. A cell's habitat, read every quarter of a year, is its medium (land, shallow
//! water, deep water) x its temperature band x, on land, its moisture band: 15 habitats.
//!
//! Run: cargo run --release -p e061_climate -- <prefix> [key=value ...] [file.params ...]
//! `<prefix>_row.csv` is one row of parameters and measures, `<prefix>_years.csv` a row a year,
//! and with maps=1 `<prefix>_maps.bin` the maps of the last and the middle year.

use std::collections::VecDeque;
use std::f64::consts::TAU;
use std::io::Write;
use std::time::Instant;

// ---- the measures (what we read off the world, not laws of it) ----

const LIFE: f64 = 300.0; // steps: a grown body's life (e055: 275-425 for the heavy)
const TRAVEL: usize = 14; // cells a body travels in a life (e058: 3 in the crowd, 14 in a thin world)
const WIDE: usize = 3 * TRAVEL; // a patch a body cannot average away (#68 rule 1)
const SHARE: f64 = 0.02; // a habitat counts when it holds this share of the cells
const COLD: f64 = 5.0; // C: the quarter's mean under which nothing grows (the base of growing degree days)
const HOT: f64 = 20.0; // C
const DRY: f64 = 1.0 / 3.0; // the ground's mean fill
const WET: f64 = 2.0 / 3.0;
const SHALLOW: f64 = 200.0; // m: the sea over the shelf, where light can reach the bottom's layer
const POOL: f64 = 500.0; // mm of standing water that makes a land cell a lake
const N_HAB: usize = 15;
const HAB_NAMES: [&str; N_HAB] = [
    "land_cold_dry", "land_cold_moist", "land_cold_wet",
    "land_mild_dry", "land_mild_moist", "land_mild_wet",
    "land_hot_dry", "land_hot_moist", "land_hot_wet",
    "shallow_cold", "shallow_mild", "shallow_hot",
    "deep_cold", "deep_mild", "deep_hot",
];

// ---- laws with no search axis ----

const SAT_20: f64 = 25.0; // mm of water a column of air holds at 20 C
const SAT_K: f64 = 0.065; // per C: warm air holds more (about 7% a degree)
const RAIN_RH: f64 = 0.8; // the air rains above this share of what it can hold
const LEVEL: f64 = 0.125; // e019/e035: the most of a drop that moves in one update (a pool levels, it does not slosh)

macro_rules! params {
    ($($name:ident = $default:expr, $doc:literal;)*) => {
        #[derive(Clone, Debug)]
        struct Params { $($name: f64,)* }
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
    size = 256.0, "cells on a side of the world (a torus)";
    seed = 1.0, "the seed of the generated terrain";
    years = 20.0, "years to run";
    year = 20000.0, "steps in a year";
    day = 60.0, "steps in a day (a fifth of a life of 300 steps)";
    tick = 10.0, "steps between two updates of the climate";
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
    maps = 0.0, "1: write the maps of the last and the middle year";
}

struct Rng(u64);

impl Rng {
    fn new(seed: u64) -> Self {
        Rng(seed.wrapping_mul(0x9E37_79B9_7F4A_7C15) | 1)
    }
    fn next_u64(&mut self) -> u64 {
        let mut x = self.0;
        x ^= x >> 12;
        x ^= x << 25;
        x ^= x >> 27;
        self.0 = x;
        x.wrapping_mul(0x2545_F491_4F6C_DD1D)
    }
    fn f64(&mut self) -> f64 {
        (self.next_u64() >> 11) as f64 / (1u64 << 53) as f64
    }
}

fn fade(t: f64) -> f64 {
    t * t * t * (t * (t * 6.0 - 15.0) + 10.0)
}

/// Octaves of smooth lattice noise on the torus: the first with a lattice point every `grain`
/// cells, each next with twice as many points at `rough` of the amplitude, down to 2 cells.
fn noise(n: usize, seed: u64, grain: f64, rough: f64) -> Vec<f64> {
    let mut rng = Rng::new(seed);
    let mut h = vec![0.0f64; n * n];
    let mut k = ((n as f64 / grain).round() as usize).max(1);
    let mut amp = 1.0;
    while n / k >= 2 {
        let lattice: Vec<f64> = (0..k * k).map(|_| rng.f64() * 2.0 - 1.0).collect();
        let spacing = n as f64 / k as f64;
        let axis: Vec<(usize, usize, f64)> = (0..n)
            .map(|i| {
                let u = i as f64 / spacing;
                let f = u.floor();
                let i0 = (f as usize) % k;
                (i0, (i0 + 1) % k, fade(u - f))
            })
            .collect();
        for (y, &(y0, y1, fy)) in axis.iter().enumerate() {
            for (x, &(x0, x1, fx)) in axis.iter().enumerate() {
                let a = lattice[y0 * k + x0] + (lattice[y0 * k + x1] - lattice[y0 * k + x0]) * fx;
                let b = lattice[y1 * k + x0] + (lattice[y1 * k + x1] - lattice[y1 * k + x0]) * fx;
                h[y * n + x] += amp * (a + (b - a) * fy);
            }
        }
        k *= 2;
        amp *= rough;
    }
    h
}

/// What a column of air can hold at a temperature, from a table (an exp per cell per update
/// was a sixth of the run).
struct Sat {
    lo: f64,
    per: f64,
    v: Vec<f64>,
}

impl Sat {
    fn new() -> Self {
        let (lo, hi, per) = (-150.0, 150.0, 4.0);
        let v = (0..=((hi - lo) * per) as usize).map(|i| SAT_20 * (SAT_K * (lo + i as f64 / per - 20.0)).exp()).collect();
        Sat { lo, per, v }
    }
    fn at(&self, t: f64) -> f64 {
        let u = ((t - self.lo) * self.per).clamp(0.0, (self.v.len() - 2) as f64);
        let i = u as usize;
        self.v[i] + (self.v[i + 1] - self.v[i]) * (u - i as f64)
    }
}

/// The water that crosses the edges of the land and the air in an update.
#[derive(Default, Clone, Copy)]
struct Flux {
    sea_evap: f64,
    sea_rain: f64,
    land_evap: f64,
    land_rain: f64,
    runoff: f64,
}

impl Flux {
    fn add(&mut self, o: &Flux) {
        self.sea_evap += o.sea_evap;
        self.sea_rain += o.sea_rain;
        self.land_evap += o.land_evap;
        self.land_rain += o.land_rain;
        self.runoff += o.runoff;
    }
}

struct World {
    n: usize,
    elev: Vec<f64>, // m above the sea; negative under it (its depth)
    sea: Vec<bool>,
    air: Vec<f64>,     // m: the height of the surface the air lies on (0 over the sea)
    rate: Vec<f64>,    // share of the way to the equilibrium in an update
    inv_cap: Vec<f64>, // 1 on land, sea_rate / land_rate on the sea
    lat_sin: Vec<f64>,
    lat_cos: Vec<f64>,
    temp: Vec<f64>,   // C
    vapor: Vec<f64>,  // mm of water in the air over the cell
    ground: Vec<f64>, // mm of water in and on the ground (land only)
    light: Vec<f64>,
    rain_now: Vec<f64>, // mm fallen in the last update
    // scratch
    cos_h: Vec<f64>, // the hour angle at the start of the update, per column, in [-pi, pi)
    sin_lo: Vec<f64>,
    sin_hi: Vec<f64>,
    theta: Vec<f64>,
    dtemp: Vec<f64>,
    moved: Vec<f64>,
    surf: Vec<f64>,
    dground: Vec<f64>,
}

impl World {
    fn new(p: &Params) -> Self {
        let n = p.size as usize;
        let cells = n * n;
        let h = noise(n, p.seed as u64, p.grain, p.rough);
        let mut sorted = h.clone();
        sorted.sort_by(|a, b| a.partial_cmp(b).unwrap());
        let level = sorted[(((1.0 - p.land) * cells as f64) as usize).min(cells - 1)];
        let top = sorted[cells - 1];
        let elev: Vec<f64> = h.iter().map(|&v| (v - level) / (top - level) * p.relief).collect();
        let sea: Vec<bool> = elev.iter().map(|&e| e < 0.0).collect();
        let air: Vec<f64> = elev.iter().map(|&e| e.max(0.0)).collect();
        let rate: Vec<f64> = sea.iter().map(|&s| if s { p.sea_rate } else { p.land_rate }).collect();
        let inv_cap: Vec<f64> = sea.iter().map(|&s| if s { p.sea_rate / p.land_rate } else { 1.0 }).collect();
        // The rows run from lat_lo to lat_hi and back: no edge, every latitude twice.
        let lat: Vec<f64> = (0..n).map(|y| (p.lat_lo + (p.lat_hi - p.lat_lo) * (1.0 - (2.0 * (y as f64 + 0.5) / n as f64 - 1.0).abs())).to_radians()).collect();
        let sat = Sat::new();
        let temp: Vec<f64> = (0..cells).map(|c| p.night + p.gain * 0.25 * lat[c / n].cos() - p.lapse / 1000.0 * air[c]).collect();
        let vapor: Vec<f64> = temp.iter().map(|&t| 0.5 * sat.at(t)).collect();
        let ground: Vec<f64> = sea.iter().map(|&s| if s { 0.0 } else { 0.5 * p.soil }).collect();
        World {
            n,
            elev,
            sea,
            air,
            rate,
            inv_cap,
            lat_sin: lat.iter().map(|l| l.sin()).collect(),
            lat_cos: lat.iter().map(|l| l.cos()).collect(),
            temp,
            vapor,
            ground,
            light: vec![0.0; cells],
            rain_now: vec![0.0; cells],
            cos_h: vec![0.0; n],
            sin_lo: vec![0.0; n],
            sin_hi: vec![0.0; n],
            theta: vec![0.0; cells],
            dtemp: vec![0.0; cells],
            moved: vec![0.0; cells],
            surf: vec![0.0; cells],
            dground: vec![0.0; cells],
        }
    }

    fn water(&self) -> f64 {
        self.vapor.iter().sum::<f64>() + self.ground.iter().sum::<f64>()
    }

    /// One update of the climate over the steps [step, step + tick).
    fn update(&mut self, p: &Params, sat: &Sat, step: f64) -> Flux {
        let n = self.n;
        let cells = n * n;
        let season = (TAU * (step + 0.5 * p.tick) / p.year).sin();
        let decl = p.tilt.to_radians() * season;
        let (sd, cd) = (decl.sin(), decl.cos());
        // The light is the sun's height averaged over the update, worked out exactly: sampled
        // once an update, a day of 6 updates painted each longitude with its own share of noon
        // and the sea kept it as stripes. The hour angle runs over [h0, h0 + span) at column x.
        let span = TAU * p.tick / p.day;
        for x in 0..n {
            let h0 = (TAU * (step / p.day + x as f64 / n as f64) + std::f64::consts::PI).rem_euclid(TAU) - std::f64::consts::PI;
            self.cos_h[x] = h0;
            self.sin_lo[x] = h0.sin();
            self.sin_hi[x] = (h0 + span).sin();
        }
        let lapse = p.lapse / 1000.0;

        // The sun, and each cell toward its equilibrium.
        for y in 0..n {
            let (a, b) = (self.lat_sin[y] * sd, self.lat_cos[y] * cd);
            // The sun is up while cos(hour) > -a / b: from -rise to rise around each noon.
            let rise = if a >= b { f64::INFINITY } else if a <= -b { -1.0 } else { (-a / b).acos() };
            let sin_rise = if rise.is_finite() && rise > 0.0 { rise.sin() } else { 0.0 };
            for x in 0..n {
                let c = y * n + x;
                let (lo0, hi0) = (self.cos_h[x], self.cos_h[x] + span);
                let q = if rise.is_infinite() {
                    a + b * (self.sin_hi[x] - self.sin_lo[x]) / span
                } else if rise < 0.0 {
                    0.0
                } else {
                    // Noon at 0 and at 2 pi can both fall inside [lo0, hi0), as lo0 is in [-pi, pi).
                    let mut sum = 0.0;
                    for noon in [0.0, TAU] {
                        let (lo, s_lo) = if lo0 > noon - rise { (lo0, self.sin_lo[x]) } else { (noon - rise, -sin_rise) };
                        let (hi, s_hi) = if hi0 < noon + rise { (hi0, self.sin_hi[x]) } else { (noon + rise, sin_rise) };
                        if hi > lo {
                            sum += a * (hi - lo) + b * (s_hi - s_lo);
                        }
                    }
                    (sum / span).max(0.0)
                };
                self.light[c] = q;
                let eq = p.night + p.gain * q - lapse * self.air[c];
                let t = self.temp[c] + self.rate[c] * (eq - self.temp[c]);
                self.temp[c] = t;
                self.theta[c] = t + lapse * self.air[c];
            }
        }
        // Heat crosses each edge by the difference of potential temperature (so a mountain stays
        // cold), and a cell warms by what it gets over its capacity (so the sea hardly moves).
        self.dtemp.iter_mut().for_each(|d| *d = 0.0);
        let k = 0.25 * p.spread;
        for y in 0..n {
            let yd = if y + 1 == n { 0 } else { y + 1 };
            for x in 0..n {
                let c = y * n + x;
                let r = y * n + if x + 1 == n { 0 } else { x + 1 };
                let d = yd * n + x;
                let fr = k * (self.theta[r] - self.theta[c]);
                let fd = k * (self.theta[d] - self.theta[c]);
                self.dtemp[c] += fr + fd;
                self.dtemp[r] -= fr;
                self.dtemp[d] -= fd;
            }
        }
        for c in 0..cells {
            self.temp[c] += self.dtemp[c] * self.inv_cap[c];
        }

        // The air takes up water where it can and rains what it cannot hold.
        let mut f = Flux::default();
        for c in 0..cells {
            let s = sat.at(self.temp[c]);
            let v = self.vapor[c];
            if self.sea[c] {
                let e = p.evap * (s - v).max(0.0);
                let v1 = v + e;
                let r = p.rain * (v1 - RAIN_RH * s).max(0.0);
                self.vapor[c] = v1 - r;
                self.rain_now[c] = r;
                f.sea_evap += e;
                f.sea_rain += r;
            } else {
                let g = self.ground[c];
                let e = (p.evap * (s - v).max(0.0) * (g / p.soil).min(1.0)).min(g);
                let v1 = v + e;
                let r = p.rain * (v1 - RAIN_RH * s).max(0.0);
                self.vapor[c] = v1 - r;
                self.ground[c] = g - e + r;
                self.rain_now[c] = r;
                f.land_evap += e;
                f.land_rain += r;
            }
        }

        // The wind: the air over a cell now is the air that was upwind of it (one shift for the
        // whole world, bilinear, so nothing is lost).
        let ang = (p.wind_dir + p.wind_turn * season).to_radians();
        let (sx, sy) = (-p.wind * ang.cos(), -p.wind * ang.sin());
        let (fx0, fy0) = (sx.floor(), sy.floor());
        let (fx, fy) = (sx - fx0, sy - fy0);
        let ix = (fx0 as i64).rem_euclid(n as i64) as usize;
        let iy = (fy0 as i64).rem_euclid(n as i64) as usize;
        let (w00, w01, w10, w11) = ((1.0 - fx) * (1.0 - fy), fx * (1.0 - fy), (1.0 - fx) * fy, fx * fy);
        for y in 0..n {
            let y0 = (y + iy) % n * n;
            let y1 = (y + iy + 1) % n * n;
            for x in 0..n {
                let x0 = (x + ix) % n;
                let x1 = (x + ix + 1) % n;
                self.moved[y * n + x] = w00 * self.vapor[y0 + x0] + w01 * self.vapor[y0 + x1] + w10 * self.vapor[y1 + x0] + w11 * self.vapor[y1 + x1];
            }
        }
        std::mem::swap(&mut self.vapor, &mut self.moved);

        // Standing water runs to the lower neighbors by the drop of the surface, into the sea at
        // the coast (e035's carrier, with the water's own depth counting).
        for c in 0..cells {
            self.surf[c] = if self.sea[c] { 0.0 } else { self.elev[c] + (self.ground[c] - p.soil).max(0.0) / 1000.0 };
        }
        self.dground.iter_mut().for_each(|d| *d = 0.0);
        for y in 0..n {
            let (yu, yd) = (if y == 0 { n - 1 } else { y - 1 }, if y + 1 == n { 0 } else { y + 1 });
            for x in 0..n {
                let c = y * n + x;
                if self.sea[c] {
                    continue;
                }
                let standing = self.ground[c] - p.soil;
                if standing <= 0.0 {
                    continue;
                }
                let (xl, xr) = (if x == 0 { n - 1 } else { x - 1 }, if x + 1 == n { 0 } else { x + 1 });
                let nb = [yu * n + x, yd * n + x, y * n + xr, y * n + xl];
                let h = self.surf[c];
                let mut drop = [0.0f64; 4];
                let mut total = 0.0;
                for (k, &m) in nb.iter().enumerate() {
                    let d = h - self.surf[m];
                    if d > 0.0 {
                        drop[k] = d;
                        total += d;
                    }
                }
                if total <= 0.0 {
                    continue;
                }
                for (k, &m) in nb.iter().enumerate() {
                    if drop[k] > 0.0 {
                        let give = (p.flow * standing * drop[k] / total).min(drop[k] * 1000.0 * LEVEL);
                        self.dground[c] -= give;
                        if self.sea[m] {
                            f.runoff += give;
                        } else {
                            self.dground[m] += give;
                        }
                    }
                }
            }
        }
        for c in 0..cells {
            if !self.sea[c] {
                self.ground[c] += self.dground[c];
            }
        }
        f
    }
}

/// What a quarter of a year adds up per cell.
struct Quarter {
    temp: Vec<f64>,
    moist: Vec<f64>,
    rain: Vec<f64>,
    pool: Vec<u32>,
    updates: u32,
}

impl Quarter {
    fn new(cells: usize) -> Self {
        Quarter { temp: vec![0.0; cells], moist: vec![0.0; cells], rain: vec![0.0; cells], pool: vec![0; cells], updates: 0 }
    }
    fn clear(&mut self) {
        self.temp.iter_mut().for_each(|v| *v = 0.0);
        self.moist.iter_mut().for_each(|v| *v = 0.0);
        self.rain.iter_mut().for_each(|v| *v = 0.0);
        self.pool.iter_mut().for_each(|v| *v = 0);
        self.updates = 0;
    }
    fn add(&mut self, w: &World, soil: f64) {
        for c in 0..w.temp.len() {
            self.temp[c] += w.temp[c];
            self.rain[c] += w.rain_now[c];
            if !w.sea[c] {
                let g = w.ground[c];
                self.moist[c] += (g / soil).min(1.0);
                if g - soil >= POOL {
                    self.pool[c] += 1;
                }
            }
        }
        self.updates += 1;
    }
    /// The quarter's habitat map (see `HAB_NAMES`), and whether each land cell was a lake.
    fn habitats(&self, w: &World) -> Vec<u8> {
        let u = self.updates.max(1) as f64;
        (0..w.temp.len())
            .map(|c| {
                let t = self.temp[c] / u;
                let tb = if t < COLD { 0 } else if t < HOT { 1 } else { 2 };
                if w.sea[c] {
                    if -w.elev[c] < SHALLOW { 9 + tb } else { 12 + tb }
                } else if 2 * self.pool[c] > self.updates {
                    9 + tb
                } else {
                    let m = self.moist[c] / u;
                    let mb = if m < DRY { 0 } else if m < WET { 1 } else { 2 };
                    (tb * 3 + mb) as u8
                }
            })
            .collect()
    }
}

/// The patches of one habitat map: (habitat, width, cells) for every 8-connected patch, where the
/// width is the side of the largest square that fits inside it (2 d - 1 for the deepest cell's
/// chessboard distance d to another habitat).
fn patches(map: &[u8], n: usize) -> Vec<(u8, usize, usize)> {
    let cells = n * n;
    let nb8 = |c: usize| {
        let (x, y) = (c % n, c / n);
        let xs = [(x + n - 1) % n, x, (x + 1) % n];
        let ys = [(y + n - 1) % n, y, (y + 1) % n];
        let mut out = [0usize; 8];
        let mut i = 0;
        for &yy in &ys {
            for &xx in &xs {
                if xx != x || yy != y {
                    out[i] = yy * n + xx;
                    i += 1;
                }
            }
        }
        out
    };
    let mut dist = vec![u32::MAX; cells];
    let mut queue = VecDeque::new();
    for c in 0..cells {
        if nb8(c).iter().any(|&m| map[m] != map[c]) {
            dist[c] = 1;
            queue.push_back(c);
        }
    }
    if queue.is_empty() {
        return vec![(map[0], n, cells)];
    }
    while let Some(c) = queue.pop_front() {
        for m in nb8(c) {
            if map[m] == map[c] && dist[m] == u32::MAX {
                dist[m] = dist[c] + 1;
                queue.push_back(m);
            }
        }
    }
    let mut seen = vec![false; cells];
    let mut out = Vec::new();
    let mut stack = Vec::new();
    for s in 0..cells {
        if seen[s] {
            continue;
        }
        seen[s] = true;
        stack.push(s);
        let (mut area, mut deepest) = (0usize, 0u32);
        while let Some(c) = stack.pop() {
            area += 1;
            deepest = deepest.max(dist[c]);
            for m in nb8(c) {
                if !seen[m] && map[m] == map[s] {
                    seen[m] = true;
                    stack.push(m);
                }
            }
        }
        out.push((map[s], (2 * deepest as usize - 1).min(n), area));
    }
    out
}

/// The width of the patch a cell of each habitat lies in, at the median over the cells.
fn median_widths(maps: &[Vec<u8>], n: usize) -> [usize; N_HAB] {
    let mut by: Vec<Vec<(usize, usize)>> = vec![Vec::new(); N_HAB];
    for m in maps {
        for (h, width, area) in patches(m, n) {
            by[h as usize].push((width, area));
        }
    }
    let mut out = [0usize; N_HAB];
    for (h, ps) in by.iter_mut().enumerate() {
        ps.sort();
        let total: usize = ps.iter().map(|p| p.1).sum();
        let mut acc = 0;
        for &(width, area) in ps.iter() {
            acc += area;
            if 2 * acc >= total {
                out[h] = width;
                break;
            }
        }
    }
    out
}

fn shares(maps: &[Vec<u8>]) -> [f64; N_HAB] {
    let mut s = [0.0; N_HAB];
    let total = maps.iter().map(|m| m.len()).sum::<usize>() as f64;
    for m in maps {
        for &h in m {
            s[h as usize] += 1.0;
        }
    }
    s.iter_mut().for_each(|v| *v /= total);
    s
}

/// Share of cells whose habitat is not the same in every quarter.
fn change(maps: &[Vec<u8>]) -> f64 {
    let cells = maps[0].len();
    (0..cells).filter(|&c| maps.iter().any(|m| m[c] != maps[0][c])).count() as f64 / cells as f64
}

/// What changes: the share of the cells whose temperature band, moisture band (land in every
/// quarter) or medium is not the same in every quarter.
fn change_parts(maps: &[Vec<u8>]) -> (f64, f64, f64) {
    let temp = |h: u8| if h < 9 { h / 3 } else { (h - 9) % 3 };
    let medium = |h: u8| if h < 9 { 0 } else if h < 12 { 1 } else { 2 };
    let cells = maps[0].len();
    let (mut t, mut m, mut d) = (0usize, 0usize, 0usize);
    for c in 0..cells {
        let h0 = maps[0][c];
        t += maps.iter().any(|mp| temp(mp[c]) != temp(h0)) as usize;
        d += maps.iter().any(|mp| medium(mp[c]) != medium(h0)) as usize;
        m += (maps.iter().all(|mp| mp[c] < 9) && maps.iter().any(|mp| mp[c] % 3 != h0 % 3)) as usize;
    }
    (t as f64 / cells as f64, m as f64 / cells as f64, d as f64 / cells as f64)
}

/// Share of (cell, quarter) that agree between two years.
fn agree(a: &[Vec<u8>], b: &[Vec<u8>]) -> f64 {
    let mut same = 0usize;
    let mut total = 0usize;
    for (ma, mb) in a.iter().zip(b) {
        same += ma.iter().zip(mb).filter(|(x, y)| x == y).count();
        total += ma.len();
    }
    same as f64 / total as f64
}

/// What the viewer is told a cell holds: the height in the units e059 drew (a relief of 64).
const VIEW_RELIEF: f64 = 64.0;
const VIEW_SEA: f64 = 3.0; // the drawn depth of the sea past the shelf
const TEMP_OFFSET: f64 = 50.0; // the temperature layer is sent as C + 50 (bytes are unsigned)

fn main() {
    let args: Vec<String> = std::env::args().skip(1).collect();
    let prefix = args.first().expect("usage: e061_climate <prefix> [key=value ...] [file.params ...]").clone();
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
    let years = p.years as usize;
    let per_quarter = ((p.year / p.tick / 4.0).round() as usize).max(1);
    let day_updates = ((p.day / p.tick).round() as usize).max(1);
    let land_cells = w.sea.iter().filter(|&&s| !s).count().max(1) as f64;
    let water0 = w.water();

    // The viewer: nothing unless EVLOG_VIEW is set.
    // The sea floor is drawn at most VIEW_SEA units down (its real depth is in the habitats): drawn
    // to scale, the eye's target sat on a floor thousands of metres under the water's surface.
    let view_height = |e: f64| if e >= 0.0 { e / p.relief * VIEW_RELIEF } else { -VIEW_SEA * (-e / SHALLOW).min(1.0) };
    let height_view: Vec<f32> = w.elev.iter().map(|&e| view_height(e) as f32).collect();
    let water_max = (1.0 + VIEW_SEA) as f32;
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
            experiment: "e061_climate",
            w: n,
            h: n,
            sub: 4,
            height: &height_view,
            band: &band,
            layers: vec![
                viewer::LayerSpec::new("water", water_max, viewer::Scale::Sqrt),
                viewer::LayerSpec::new("temperature", 100.0, viewer::Scale::Linear),
                viewer::LayerSpec::new("moisture", 1.0, viewer::Scale::Linear),
                viewer::LayerSpec::new("humidity", 1.0, viewer::Scale::Linear),
                viewer::LayerSpec::new("rain", 2.0, viewer::Scale::Sqrt),
                viewer::LayerSpec::new("light", 1.0, viewer::Scale::Linear),
                viewer::LayerSpec::new("habitat", 255.0, viewer::Scale::Linear),
            ],
            globals: vec!["season", "year"],
            blocks: vec!["empty"],
            deaths: vec![],
            births: false,
            params: json,
        },
    );

    let mut years_csv = String::from("year,habitats,change,agree_prev,land_temp,sea_temp,pole_gap,day_swing,season_swing,rain_land,evap_land,runoff_land,lakes,dry,moist,wet,water_err");
    for h in HAB_NAMES {
        years_csv.push_str(&format!(",{h}"));
    }
    years_csv.push('\n');

    let mut q = Quarter::new(cells);
    let (mut tmin, mut tmax) = (w.temp.clone(), w.temp.clone());
    let mut last_map = vec![255u8; cells];
    let mut prev_year: Option<Vec<Vec<u8>>> = None;
    let mut middle: Option<Vec<Vec<u8>>> = None;
    let mut flux_all = Flux::default();
    let mut update_i: u64 = 0;
    let mut row_measures = String::new();
    let mut maps_out: Vec<u8> = Vec::new();

    for yr in 1..=years {
        let mut maps: Vec<Vec<u8>> = Vec::with_capacity(4);
        let mut qtemp: Vec<Vec<f64>> = Vec::with_capacity(4);
        let mut flux = Flux::default();
        let (mut swing_sum, mut swing_days) = (0.0f64, 0usize);
        let (mut lakes, mut dry, mut moist, mut wet) = (0.0f64, 0.0f64, 0.0f64, 0.0f64);
        let mut qmaps_detail: Vec<(Vec<f32>, Vec<f32>, Vec<f32>)> = Vec::new();
        for _quarter in 0..4 {
            q.clear();
            for _ in 0..per_quarter {
                let step = update_i as f64 * p.tick;
                let fl = w.update(&p, &sat, step);
                flux.add(&fl);
                q.add(&w, p.soil);
                for c in 0..cells {
                    tmin[c] = tmin[c].min(w.temp[c]);
                    tmax[c] = tmax[c].max(w.temp[c]);
                }
                update_i += 1;
                if update_i as usize % day_updates == 0 {
                    let mut s = 0.0;
                    for c in 0..cells {
                        if !w.sea[c] {
                            s += tmax[c] - tmin[c];
                        }
                        tmin[c] = w.temp[c];
                        tmax[c] = w.temp[c];
                    }
                    swing_sum += s / land_cells;
                    swing_days += 1;
                }
                if let Some(v) = view.as_mut() {
                    let at = (update_i as f64 * p.tick) as u64;
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
                        let temp: Vec<f64> = w.temp.iter().map(|t| t + TEMP_OFFSET).collect();
                        let moisture: Vec<f64> = (0..cells).map(|c| if w.sea[c] { 1.0 } else { (w.ground[c] / p.soil).min(1.0) }).collect();
                        let humidity: Vec<f64> = (0..cells).map(|c| w.vapor[c] / sat.at(w.temp[c])).collect();
                        let hab: Vec<f64> = last_map.iter().map(|&h| h as f64).collect();
                        let frac = (at as f64 / p.year).fract() as f32;
                        v.frame(at, &[&water, &temp, &moisture, &humidity, &w.rain_now, &w.light, &hab], &[(TAU * at as f64 / p.year).sin() as f32, frac], |_push| {});
                    }
                    v.tick(at);
                }
            }
            let map = q.habitats(&w);
            let u = q.updates.max(1) as f64;
            for c in 0..cells {
                if w.sea[c] {
                    continue;
                }
                if map[c] >= 9 {
                    lakes += 1.0;
                } else {
                    match map[c] % 3 {
                        0 => dry += 1.0,
                        1 => moist += 1.0,
                        _ => wet += 1.0,
                    }
                }
            }
            qtemp.push(q.temp.iter().map(|t| t / u).collect());
            if p.maps > 0.0 && yr == years {
                qmaps_detail.push((
                    q.temp.iter().map(|t| (t / u) as f32).collect(),
                    q.moist.iter().map(|m| (m / u) as f32).collect(),
                    q.rain.iter().map(|&r| r as f32).collect(),
                ));
            }
            last_map = map.clone();
            maps.push(map);
        }

        // The year's row.
        let sh = shares(&maps);
        let habitats = sh.iter().filter(|&&s| s >= SHARE).count();
        let ch = change(&maps);
        let agree_prev = prev_year.as_ref().map(|py| agree(&maps, py)).unwrap_or(f64::NAN);
        let mean_t = |sea: bool| {
            let (mut s, mut k) = (0.0f64, 0.0f64);
            for qt in &qtemp {
                for c in 0..cells {
                    if w.sea[c] == sea {
                        s += qt[c];
                        k += 1.0;
                    }
                }
            }
            s / k.max(1.0)
        };
        let rows: Vec<f64> = (0..n).map(|y| qtemp.iter().map(|qt| qt[y * n..(y + 1) * n].iter().sum::<f64>()).sum::<f64>() / (4 * n) as f64).collect();
        let pole_gap = rows.iter().copied().fold(f64::MIN, f64::max) - rows.iter().copied().fold(f64::MAX, f64::min);
        let season_swing = (0..cells)
            .filter(|&c| !w.sea[c])
            .map(|c| {
                let v = qtemp.iter().map(|qt| qt[c]);
                v.clone().fold(f64::MIN, f64::max) - v.fold(f64::MAX, f64::min)
            })
            .sum::<f64>()
            / land_cells;
        flux_all.add(&flux);
        let water_err = (w.water() - water0 - (flux_all.sea_evap - flux_all.sea_rain - flux_all.runoff)).abs() / (w.water() + flux_all.sea_evap + flux_all.land_rain).max(1.0);
        let lq = 4.0 * land_cells;
        let day_swing = swing_sum / swing_days.max(1) as f64;
        let line = format!(
            "{yr},{habitats},{ch:.4},{agree_prev:.4},{:.2},{:.2},{pole_gap:.2},{day_swing:.2},{season_swing:.2},{:.1},{:.1},{:.1},{:.4},{:.4},{:.4},{:.4},{water_err:.2e}",
            mean_t(false),
            mean_t(true),
            flux.land_rain / land_cells,
            flux.land_evap / land_cells,
            flux.runoff / land_cells,
            lakes / (4 * cells) as f64,
            dry / lq,
            moist / lq,
            wet / lq,
        );
        years_csv.push_str(&line);
        for s in sh {
            years_csv.push_str(&format!(",{s:.4}"));
        }
        years_csv.push('\n');
        eprintln!("year {yr}: habitats {habitats}, change {ch:.3}, agree {agree_prev:.3}, land {:.1} C, sea {:.1} C, rain on land {:.0} mm, lakes {:.4}, dry/moist/wet {:.2}/{:.2}/{:.2}, err {water_err:.1e}", mean_t(false), mean_t(true), flux.land_rain / land_cells, lakes / (4 * cells) as f64, dry / lq, moist / lq, wet / lq);

        if yr == (years / 2).max(1) {
            middle = Some(maps.clone());
        }
        if yr == years {
            let widths = median_widths(&maps, n);
            let wide = (0..N_HAB).filter(|&h| sh[h] >= SHARE && widths[h] >= WIDE).count();
            let stand = middle.as_ref().map(|m| agree(&maps, m)).unwrap_or(f64::NAN);
            let pass_share = habitats >= 5;
            let pass_wide = wide >= 3;
            let pass_change = (0.10..=0.50).contains(&ch);
            let pass_stand = stand >= 0.90;
            let seconds = started.elapsed().as_secs_f64();
            row_measures = format!(
                "{habitats},{wide},{ch:.4},{stand:.4},{},{},{},{},{},{:.4},{:.2},{:.2},{pole_gap:.2},{day_swing:.2},{season_swing:.2},{:.1},{:.4},{:.4},{:.4},{:.4},{water_err:.2e},{seconds:.1},{:.3},{:.4},{:.4}",
                pass_share as u8,
                pass_wide as u8,
                pass_change as u8,
                pass_stand as u8,
                (pass_share && pass_wide && pass_change && pass_stand) as u8,
                land_cells / cells as f64,
                mean_t(false),
                mean_t(true),
                flux.land_rain / land_cells,
                lakes / (4 * cells) as f64,
                dry / lq,
                moist / lq,
                wet / lq,
                seconds * 1000.0 / update_i as f64,
                p.day / LIFE,
                p.year / LIFE,
            );
            let (ct, cm, cd) = change_parts(&maps);
            let wide_land = (0..9).filter(|&h| sh[h] >= SHARE && widths[h] >= WIDE).count();
            row_measures.push_str(&format!(",{ct:.4},{cm:.4},{cd:.4},{wide_land}"));
            for s in sh {
                row_measures.push_str(&format!(",{s:.4}"));
            }
            for wd in widths {
                row_measures.push_str(&format!(",{wd}"));
            }
            if p.maps > 0.0 {
                maps_out.extend_from_slice(b"E061");
                maps_out.extend_from_slice(&(n as u32).to_le_bytes());
                for &e in &w.elev {
                    maps_out.extend_from_slice(&(e as f32).to_le_bytes());
                }
                for (qi, (t, m, r)) in qmaps_detail.iter().enumerate() {
                    maps_out.extend_from_slice(&maps[qi]);
                    for v in t.iter().chain(m).chain(r) {
                        maps_out.extend_from_slice(&v.to_le_bytes());
                    }
                }
                for m in middle.as_ref().unwrap() {
                    maps_out.extend_from_slice(m);
                }
            }
        }
        prev_year = Some(maps);
    }

    let mut header: Vec<String> = Params::NAMES.iter().map(|s| s.to_string()).collect();
    for m in ["habitats", "wide", "change", "stand", "pass_share", "pass_wide", "pass_change", "pass_stand", "pass", "land_share", "land_temp", "sea_temp", "pole_gap", "day_swing", "season_swing", "rain_land", "lakes", "dry", "moist", "wet", "water_err", "seconds", "ms_per_update", "day_over_life", "year_over_life", "change_temp", "change_moist", "change_medium", "wide_land"] {
        header.push(m.to_string());
    }
    for h in HAB_NAMES {
        header.push(format!("share_{h}"));
    }
    for h in HAB_NAMES {
        header.push(format!("width_{h}"));
    }
    let values = p.values().iter().map(|v| format!("{v}")).collect::<Vec<_>>().join(",");
    std::fs::write(format!("{prefix}_row.csv"), format!("{}\n{values},{row_measures}\n", header.join(","))).unwrap();
    std::fs::write(format!("{prefix}_years.csv"), years_csv).unwrap();
    if p.maps > 0.0 {
        std::fs::File::create(format!("{prefix}_maps.bin")).unwrap().write_all(&maps_out).unwrap();
    }
    let _ = Params::DOCS;
    eprintln!("done: {prefix} in {:.1} s ({:.3} ms an update)", started.elapsed().as_secs_f64(), started.elapsed().as_secs_f64() * 1000.0 / update_i.max(1) as f64);
}

#[cfg(test)]
mod tests {
    use super::*;

    /// The wind moves the air and the rain moves it to the ground; the sea is the only source
    /// and sink, so the land and the air add up to what the sea gave less what it took back.
    #[test]
    fn water_is_conserved() {
        let mut p = Params::default();
        p.size = 32.0;
        p.grain = 16.0;
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

    /// Averaged over a day, the light at the equator at the equinox is 1/pi, and under the
    /// midnight sun at the pole it is sin(tilt), whatever the length of an update.
    #[test]
    fn daily_light() {
        for tick in [7.0, 10.0, 25.0] {
            let mut p = Params::default();
            p.size = 8.0;
            p.day = 60.0;
            p.tick = tick;
            p.year = 1e12; // the season stands still at the equinox
            let sat = Sat::new();
            let mut w = World::new(&p);
            w.lat_sin = vec![0.0; 8];
            w.lat_cos = vec![1.0; 8];
            let updates = 600;
            let mut sum = 0.0;
            for i in 0..updates {
                w.update(&p, &sat, i as f64 * tick);
                sum += w.light[3];
            }
            let mean = sum / updates as f64;
            assert!((mean - 1.0 / std::f64::consts::PI).abs() < 0.01, "tick {tick}: {mean}");
        }
        let mut p = Params::default();
        p.size = 8.0;
        p.year = 4.0 * 1e12; // a quarter of the way: the solstice, held
        let sat = Sat::new();
        let mut w = World::new(&p);
        w.lat_sin = vec![1.0; 8];
        w.lat_cos = vec![0.0; 8];
        w.update(&p, &sat, 1e12);
        assert!((w.light[0] - p.tilt.to_radians().sin()).abs() < 1e-6, "{}", w.light[0]);
    }

    /// A patch's width is the side of the largest square inside it.
    #[test]
    fn widths_of_a_square() {
        let n = 16;
        let mut map = vec![0u8; n * n];
        for y in 4..11 {
            for x in 2..9 {
                map[y * n + x] = 1;
            }
        }
        let ps = patches(&map, n);
        let square = ps.iter().find(|p| p.0 == 1).unwrap();
        assert_eq!((square.1, square.2), (7, 49));
    }
}
