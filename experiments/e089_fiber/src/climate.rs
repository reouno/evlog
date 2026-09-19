//! e061's climate, ported as it is: generated terrain and sea, the sun with a day and a year, heat,
//! water taken up by the air, carried by one wind and rained, standing water running downhill.
//!
//! e073 (#89) adds one field and one rate: the climate keeps `temp_day`, a running mean of each
//! cell's temperature over the last day, and `temp_read` is what a body's heat reads, `day_temp` of
//! the way from the moment to that mean. At `day_temp` 0 it is the moment, as in e072.

use crate::plants::WOOD_HALF;
use crate::Params;
use std::f64::consts::TAU;

const SAT_20: f64 = 25.0; // mm of water a column of air holds at 20 C
const SAT_K: f64 = 0.065; // per C: warm air holds more (about 7% a degree)
const RAIN_RH: f64 = 0.8; // the air rains above this share of what it can hold
const LEVEL: f64 = 0.125; // e019/e035: the most of a drop that moves in one update (a pool levels, it does not slosh)

pub struct Rng(pub u64);

impl Rng {
    pub fn new(seed: u64) -> Self {
        Rng(seed.wrapping_mul(0x9E37_79B9_7F4A_7C15) | 1)
    }
    pub fn next_u64(&mut self) -> u64 {
        let mut x = self.0;
        x ^= x >> 12;
        x ^= x << 25;
        x ^= x >> 27;
        self.0 = x;
        x.wrapping_mul(0x2545_F491_4F6C_DD1D)
    }
    pub fn f64(&mut self) -> f64 {
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
pub struct Sat {
    lo: f64,
    per: f64,
    v: Vec<f64>,
}

impl Sat {
    pub fn new() -> Self {
        let (lo, hi, per) = (-150.0, 150.0, 4.0);
        let v = (0..=((hi - lo) * per) as usize).map(|i| SAT_20 * (SAT_K * (lo + i as f64 / per - 20.0)).exp()).collect();
        Sat { lo, per, v }
    }
    pub fn at(&self, t: f64) -> f64 {
        let u = ((t - self.lo) * self.per).clamp(0.0, (self.v.len() - 2) as f64);
        let i = u as usize;
        self.v[i] + (self.v[i + 1] - self.v[i]) * (u - i as f64)
    }
}

/// The water that crosses the edges of the land and the air in an update.
#[derive(Default, Clone, Copy)]
pub struct Flux {
    pub sea_evap: f64,
    pub sea_rain: f64,
    pub land_evap: f64,
    pub land_rain: f64,
    pub runoff: f64,
    pub carried: f64, // e072 (set G): matter the running water took out of the soil it crossed
    pub to_sea: f64,  // of it, what reached the sea
}

impl Flux {
    pub fn add(&mut self, o: &Flux) {
        self.sea_evap += o.sea_evap;
        self.sea_rain += o.sea_rain;
        self.land_evap += o.land_evap;
        self.land_rain += o.land_rain;
        self.runoff += o.runoff;
        self.carried += o.carried;
        self.to_sea += o.to_sea;
    }
}

pub struct World {
    pub n: usize,
    pub elev: Vec<f64>, // m above the sea; negative under it (its depth)
    pub sea: Vec<bool>,
    pub air: Vec<f64>,     // m: the height of the surface the air lies on (0 over the sea)
    pub rate: Vec<f64>,    // share of the way to the equilibrium in an update
    pub inv_cap: Vec<f64>, // 1 on land, sea_rate / land_rate on the sea
    pub lat_sin: Vec<f64>,
    pub lat_cos: Vec<f64>,
    pub temp: Vec<f64>,   // C
    pub temp_day: Vec<f64>, // e073: the running mean of temp over the last day
    pub temp_read: Vec<f64>, // e073: what a body's heat reads (day_temp of the way to temp_day)
    pub vapor: Vec<f64>,  // mm of water in the air over the cell
    pub ground: Vec<f64>, // mm of water in and on the ground (land only)
    pub light: Vec<f64>,
    pub rain_now: Vec<f64>, // mm fallen in the last update
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
    pub fn new(p: &Params) -> Self {
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
            temp_day: temp.clone(),
            temp_read: temp.clone(),
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

    pub fn water(&self) -> f64 {
        self.vapor.iter().sum::<f64>() + self.ground.iter().sum::<f64>()
    }

    /// One update of the climate over the steps [step, step + tick). e072 (set G): the water running
    /// off a cell takes `p.carry` of its soil for every millimetre of the ground's capacity it carries,
    /// into the cell it runs to, the sea included; with `carry` 0 the soil is not read and stays where
    /// it lies (e070). e079 (S1): `wood` is the wood standing on each cell, whose crown cuts the
    /// ground's evaporation by `p.crown_wet` x its shade (empty: no wood, as while the climate spins up).
    pub fn update(&mut self, p: &Params, sat: &Sat, step: f64, soil: &mut [f64], wood: &[f64]) -> Flux {
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
        // e073 (#89): the day's running mean, and what a body's heat reads. One pass a climate
        // update (one every `tick` steps), against the per-step pass over every body's blocks.
        let w_day = (p.tick / p.day).min(1.0);
        for c in 0..cells {
            self.temp_day[c] += w_day * (self.temp[c] - self.temp_day[c]);
            self.temp_read[c] = self.temp[c] + p.day_temp * (self.temp_day[c] - self.temp[c]);
        }

        // The air takes up water where it can and rains what it cannot hold.
        let mut f = Flux::default();
        let crown_wet = p.crown_wet > 0.0 && !wood.is_empty();
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
                let mut e = p.evap * (s - v).max(0.0) * (g / p.soil).min(1.0);
                if crown_wet {
                    // e079 (S1): the floor under a crown gives up less of its water.
                    let wd = wood[c];
                    e *= 1.0 - (p.crown_wet * wd / (wd + WOOD_HALF)).min(1.0);
                }
                let e = e.min(g);
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
                        // e072 (set G): the water takes soil along, into the cell below or into the sea.
                        if p.carry > 0.0 {
                            let took = (p.carry * give / p.soil).min(1.0) * soil[c].max(0.0);
                            soil[c] -= took;
                            soil[m] += took;
                            f.carried += took;
                            f.to_sea += if self.sea[m] { took } else { 0.0 };
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
