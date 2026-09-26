//! The sun, heat and air: e061's laws, ported, with three changes (e102, #116):
//! - winds by latitude band (easterlies, westerlies, polar easterlies) that follow the sun, and the air
//!   mixing a little across each edge, in place of one wind for the world;
//! - a temperature and a rain anomaly that differ by place and year (years are not the same year again);
//! - storms, which multiply the rain where they pass.
//! The ground's water lives here (the air takes it up and rains on it); where it goes once it is on the
//! ground is `hydro`'s.

use crate::noise::{noise, normalised, Rng};
use crate::terrain::Terrain;
use crate::Params;
use std::f64::consts::{PI, TAU};

const SAT_20: f64 = 25.0; // mm of water a column of air holds at 20 C
const SAT_K: f64 = 0.065; // per C: warm air holds more (about 7% a degree)
const RAIN_RH: f64 = 0.8; // the air rains above this share of what it can hold

/// What a column of air can hold at a temperature, from a table.
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
}

impl Flux {
    pub fn add(&mut self, o: &Flux) {
        self.sea_evap += o.sea_evap;
        self.sea_rain += o.sea_rain;
        self.land_evap += o.land_evap;
        self.land_rain += o.land_rain;
    }
}

struct Storm {
    x: f64,
    y: f64,
    left: u32,
}

/// The year's weather: where this year is warmer or wetter than the mean, and the storms.
pub struct Weather {
    rng: Rng,
    t_now: Vec<f64>,
    t_to: Vec<f64>,
    r_now: Vec<f64>,
    r_to: Vec<f64>,
    storms: Vec<Storm>,
    pub rain_f: Vec<f64>, // this update's multiplier of the rain
    pub hit: Vec<bool>,   // under a storm this update (e103: storms fell tall stands)
    pub storms_seen: u64,
}

impl Weather {
    pub fn new(p: &Params, cells: usize) -> Self {
        let mut w = Weather {
            rng: Rng::new(p.seed as u64 ^ 0x57_0A_4D),
            t_now: vec![0.0; cells],
            t_to: vec![0.0; cells],
            r_now: vec![0.0; cells],
            r_to: vec![0.0; cells],
            storms: Vec::new(),
            rain_f: vec![1.0; cells],
            hit: vec![false; cells],
            storms_seen: 0,
        };
        w.new_year(p);
        w
    }

    /// A new year's anomaly: `var_rho` of last year's, and the rest a fresh smooth field.
    pub fn new_year(&mut self, p: &Params) {
        let n = p.size as usize;
        let fresh = (1.0 - p.var_rho * p.var_rho).max(0.0).sqrt();
        let ft = normalised(noise(n, self.rng.next_u64(), p.var_grain, 0.5, p.var_grain / 4.0));
        let fr = normalised(noise(n, self.rng.next_u64(), p.var_grain, 0.5, p.var_grain / 4.0));
        for c in 0..self.t_to.len() {
            self.t_to[c] = p.var_rho * self.t_to[c] + fresh * ft[c];
            self.r_to[c] = p.var_rho * self.r_to[c] + fresh * fr[c];
        }
    }

    /// One update: the anomaly moves toward the year's (over a quarter of a year), storms come and go.
    fn update(&mut self, p: &Params) {
        let n = p.size as usize;
        let k = (p.tick / (p.year / 4.0)).min(1.0);
        for c in 0..self.t_now.len() {
            self.t_now[c] += k * (self.t_to[c] - self.t_now[c]);
            self.r_now[c] += k * (self.r_to[c] - self.r_now[c]);
            self.rain_f[c] = (p.var_rain * self.r_now[c]).exp();
            self.hit[c] = false;
        }
        for _ in 0..self.rng.poisson(p.storms * p.tick / p.year) {
            self.storms.push(Storm { x: self.rng.f64() * n as f64, y: self.rng.f64() * n as f64, left: p.storm_updates as u32 });
            self.storms_seen += 1;
        }
        let r = p.storm_radius;
        let ri = r.ceil() as i64;
        for s in &mut self.storms {
            for dy in -ri..=ri {
                for dx in -ri..=ri {
                    if ((dx * dx + dy * dy) as f64) <= r * r {
                        let x = (s.x as i64 + dx).rem_euclid(n as i64) as usize;
                        let y = (s.y as i64 + dy).rem_euclid(n as i64) as usize;
                        self.rain_f[y * n + x] *= p.storm_rain;
                        self.hit[y * n + x] = true;
                    }
                }
            }
            s.left -= 1;
        }
        self.storms.retain(|s| s.left > 0);
    }

    pub fn temp(&self, c: usize, p: &Params) -> f64 {
        p.var_temp * self.t_now[c]
    }
}

pub struct Air {
    pub temp: Vec<f64>,   // C
    pub vapor: Vec<f64>,  // mm of water in the air over the cell
    pub ground: Vec<f64>, // mm of water in and on the ground (land only)
    pub light: Vec<f64>,
    pub rain_now: Vec<f64>, // mm fallen in the last update
    rate: Vec<f64>,
    inv_cap: Vec<f64>,
    // scratch
    h0: Vec<f64>,
    sin_lo: Vec<f64>,
    sin_hi: Vec<f64>,
    theta: Vec<f64>,
    dtemp: Vec<f64>,
    moved: Vec<f64>,
}

/// The wind along the rows at a latitude (cells an update, + toward larger x): easterlies in the tropics,
/// westerlies in the middle latitudes, polar easterlies, the bands shifted toward the summer pole.
pub fn zonal(p: &Params, lat: f64, decl: f64) -> f64 {
    if p.wind_bands == 0.0 {
        return p.wind;
    }
    let l = (lat - 0.5 * decl).to_degrees().abs();
    let step = |a: f64, b: f64, v: f64| ((v - a) / (b - a)).clamp(0.0, 1.0);
    let s = |t: f64| t * t * (3.0 - 2.0 * t);
    // -1 below 25, +1 from 35 to 55, -1 beyond 65
    let g = -1.0 + 2.0 * s(step(25.0, 35.0, l)) - 2.0 * s(step(55.0, 65.0, l));
    p.wind * g
}

impl Air {
    pub fn new(p: &Params, t: &Terrain) -> Self {
        let n = t.n;
        let cells = n * n;
        let sat = Sat::new();
        let temp: Vec<f64> = (0..cells).map(|c| p.night + p.gain * 0.25 * t.lat[c / n].cos() - p.lapse / 1000.0 * t.air[c]).collect();
        let vapor: Vec<f64> = temp.iter().map(|&x| 0.5 * sat.at(x)).collect();
        let ground: Vec<f64> = (0..cells).map(|c| if t.sea[c] { 0.0 } else { 0.5 * t.cap[c] }).collect();
        Air {
            temp,
            vapor,
            ground,
            light: vec![0.0; cells],
            rain_now: vec![0.0; cells],
            rate: t.sea.iter().map(|&s| if s { p.sea_rate } else { p.land_rate }).collect(),
            inv_cap: t.sea.iter().map(|&s| if s { p.sea_rate / p.land_rate } else { 1.0 }).collect(),
            h0: vec![0.0; n],
            sin_lo: vec![0.0; n],
            sin_hi: vec![0.0; n],
            theta: vec![0.0; cells],
            dtemp: vec![0.0; cells],
            moved: vec![0.0; cells],
        }
    }

    pub fn water(&self) -> f64 {
        self.vapor.iter().sum::<f64>() + self.ground.iter().sum::<f64>()
    }

    /// One update of the climate over the steps [step, step + tick).
    /// `cover`: the share of the sun that reaches the soil under the leaves (e103), which scales its evaporation.
    pub fn update(&mut self, p: &Params, t: &Terrain, sat: &Sat, wx: &mut Weather, step: f64, cover: &[f64]) -> Flux {
        wx.update(p);
        let n = t.n;
        let cells = n * n;
        let season = (TAU * (step + 0.5 * p.tick) / p.year).sin();
        let decl = p.tilt.to_radians() * season;
        let (sd, cd) = (decl.sin(), decl.cos());
        // The light: the sun's height averaged over the update, worked out exactly (e061).
        let span = TAU * p.tick / p.day;
        for x in 0..n {
            let h0 = (TAU * (step / p.day + x as f64 / n as f64) + PI).rem_euclid(TAU) - PI;
            self.h0[x] = h0;
            self.sin_lo[x] = h0.sin();
            self.sin_hi[x] = (h0 + span).sin();
        }
        let lapse = p.lapse / 1000.0;
        for y in 0..n {
            let (a, b) = (t.lat[y].sin() * sd, t.lat[y].cos() * cd);
            let rise = if a >= b { f64::INFINITY } else if a <= -b { -1.0 } else { (-a / b).acos() };
            let sin_rise = if rise.is_finite() && rise > 0.0 { rise.sin() } else { 0.0 };
            for x in 0..n {
                let c = y * n + x;
                let (lo0, hi0) = (self.h0[x], self.h0[x] + span);
                let q = if rise.is_infinite() {
                    a + b * (self.sin_hi[x] - self.sin_lo[x]) / span
                } else if rise < 0.0 {
                    0.0
                } else {
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
                let eq = p.night + p.gain * q - lapse * t.air[c] + wx.temp(c, p);
                let v = self.temp[c] + self.rate[c] * (eq - self.temp[c]);
                self.temp[c] = v;
                self.theta[c] = v + lapse * t.air[c];
            }
        }
        // Heat crosses each edge by the difference of potential temperature.
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

        // The air takes up water where it can and rains what it cannot hold; this year's anomaly and the
        // storms change how much of the excess falls.
        let mut f = Flux::default();
        for c in 0..cells {
            let s = sat.at(self.temp[c]);
            let v = self.vapor[c];
            let rk = (p.rain * wx.rain_f[c]).min(1.0);
            if t.sea[c] {
                let e = p.evap * (s - v).max(0.0);
                let v1 = v + e;
                let r = rk * (v1 - RAIN_RH * s).max(0.0);
                self.vapor[c] = v1 - r;
                self.rain_now[c] = r;
                f.sea_evap += e;
                f.sea_rain += r;
            } else {
                // A soil gives up `soil_evap` of what open water would, by its fill; water standing on it all.
                let g = self.ground[c];
                let open = if g > t.cap[c] { 1.0 } else { p.soil_evap * g / t.cap[c] * cover[c] };
                let e = (p.evap * (s - v).max(0.0) * open).min(g);
                let v1 = v + e;
                let r = rk * (v1 - RAIN_RH * s).max(0.0);
                self.vapor[c] = v1 - r;
                self.ground[c] = g - e + r;
                self.rain_now[c] = r;
                f.land_evap += e;
                f.land_rain += r;
            }
        }

        // The winds: each row's air shifts along the row by its band's wind (linear, so nothing is lost).
        for y in (0..n).filter(|_| p.wind_bands != 0.0) {
            let u = zonal(p, t.lat[y], decl);
            let sx = -u; // the air here now is the air that was upwind
            let f0 = sx.floor();
            let fx = sx - f0;
            let ix = (f0 as i64).rem_euclid(n as i64) as usize;
            for x in 0..n {
                let x0 = (x + ix) % n;
                let x1 = (x0 + 1) % n;
                self.moved[y * n + x] = (1.0 - fx) * self.vapor[y * n + x0] + fx * self.vapor[y * n + x1];
            }
        }
        if p.wind_bands == 0.0 {
            // e061's one wind turning with the season, along both axes
            let ang = (p.wind_dir + p.wind_turn * season).to_radians();
            let (sx, sy) = (-p.wind * ang.cos(), -p.wind * ang.sin());
            let (fx0, fy0) = (sx.floor(), sy.floor());
            let (fx, fy) = (sx - fx0, sy - fy0);
            let ix = (fx0 as i64).rem_euclid(n as i64) as usize;
            let iy = (fy0 as i64).rem_euclid(n as i64) as usize;
            for y in 0..n {
                let y0 = (y + iy) % n * n;
                let y1 = (y + iy + 1) % n * n;
                for x in 0..n {
                    let x0 = (x + ix) % n;
                    let x1 = (x + ix + 1) % n;
                    self.moved[y * n + x] = (1.0 - fx) * (1.0 - fy) * self.vapor[y0 + x0] + fx * (1.0 - fy) * self.vapor[y0 + x1]
                        + (1.0 - fx) * fy * self.vapor[y1 + x0] + fx * fy * self.vapor[y1 + x1];
                }
            }
        }
        std::mem::swap(&mut self.vapor, &mut self.moved);
        // The air's own mixing across each edge (what carries water across the bands).
        if p.mix > 0.0 {
            self.dtemp.iter_mut().for_each(|d| *d = 0.0);
            let m = 0.25 * p.mix;
            for y in 0..n {
                let yd = if y + 1 == n { 0 } else { y + 1 };
                for x in 0..n {
                    let c = y * n + x;
                    let r = y * n + if x + 1 == n { 0 } else { x + 1 };
                    let d = yd * n + x;
                    let fr = m * (self.vapor[r] - self.vapor[c]);
                    let fd = m * (self.vapor[d] - self.vapor[c]);
                    self.dtemp[c] += fr + fd;
                    self.dtemp[r] -= fr;
                    self.dtemp[d] -= fd;
                }
            }
            for c in 0..cells {
                self.vapor[c] += self.dtemp[c];
            }
        }
        f
    }
}
