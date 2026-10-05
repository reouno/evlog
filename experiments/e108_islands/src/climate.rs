//! The sun, heat and air: e061's laws, ported, with three changes (e102, #116):
//! - winds by latitude band (easterlies, westerlies, polar easterlies) that follow the sun, and the air
//!   mixing a little across each edge, in place of one wind for the world;
//! - a temperature and a rain anomaly that differ by place and year (years are not the same year again);
//! - storms, which multiply the rain where they pass.
//! The ground's water lives here (the air takes it up and rains on it); where it goes once it is on the
//! ground is `hydro`'s.
//!
//! The small world (e108, #127; `sweep`): at 125 m a cell the wind crosses the whole world within an update, so
//! the air is not a store that shifts a cell. It enters at the windward border as sea air and is followed across
//! the world in one pass, cell after cell downwind, by the same two laws - it takes up water by its deficit and
//! rains what it cannot hold - with what it can hold lowered by the height the land lifts it. The wet side and
//! the dry side are that pass's result. The sea air also sets most of a land cell's temperature; the wind's
//! direction turns with the season, wanders from day to day and differs by year; a year's anomaly is one number
//! for the whole world, and a storm is the whole world's.

use crate::noise::{noise, normalised, Rng};
use crate::par::{self, Shared};
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
    /// The sweep: what the wind carried out of the world's air, net (the open edge of the air).
    pub wind: f64,
    /// The sweep: how far the pass is from carrying out exactly what it took up less what it rained.
    pub air_err: f64,
}

impl Flux {
    pub fn add(&mut self, o: &Flux) {
        self.sea_evap += o.sea_evap;
        self.sea_rain += o.sea_rain;
        self.land_evap += o.land_evap;
        self.land_rain += o.land_rain;
        self.wind += o.wind;
        self.air_err = self.air_err.max(o.air_err);
    }
}

struct Storm {
    x: f64, // in the sweep: the direction its wind blows to, in degrees
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
    // the sweep: this year's turn of the wind, its wandering now, and a storm's own direction
    w_now: f64,
    w_to: f64,
    wobble: f64,
    pub storm_dir: Option<f64>,
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
            w_now: 0.0,
            w_to: 0.0,
            wobble: 0.0,
            storm_dir: None,
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
        if p.sweep != 0.0 {
            // A small world lies inside one anomaly: one number for its warmth, one for its rain, one for its wind.
            let (zt, zr, zw) = (self.rng.normal(), self.rng.normal(), self.rng.normal());
            self.t_to.iter_mut().for_each(|v| *v = p.var_rho * *v + fresh * zt);
            self.r_to.iter_mut().for_each(|v| *v = p.var_rho * *v + fresh * zr);
            self.w_to = p.var_rho * self.w_to + fresh * zw;
            return;
        }
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
        let whole = p.sweep != 0.0;
        let mut stormy = 1.0;
        if whole {
            // The wind: the year's turn comes in over a quarter, the wandering keeps `wind_hold` days; a storm is
            // the whole world's, with a wind of its own.
            self.w_now += k * (self.w_to - self.w_now);
            let rho = (-(p.tick / p.day) / p.wind_hold).exp();
            self.wobble = rho * self.wobble + (1.0 - rho * rho).sqrt() * self.rng.normal();
            for _ in 0..self.rng.poisson(p.storms * p.tick / p.year) {
                self.storms.push(Storm { x: self.rng.f64() * 360.0, y: 0.0, left: p.storm_updates as u32 });
                self.storms_seen += 1;
            }
            self.storm_dir = self.storms.first().map(|s| s.x);
            if self.storm_dir.is_some() {
                stormy = p.storm_rain;
            }
        }
        {
            let (tn, rn, rf, hit) = (Shared::new(&mut self.t_now), Shared::new(&mut self.r_now), Shared::new(&mut self.rain_f), Shared::new(&mut self.hit));
            let (tt, rt) = (&self.t_to, &self.r_to);
            par::pieces(p.threads as usize, tt.len(), |lo, hi| {
                for c in lo..hi {
                    *tn.at(c) += k * (tt[c] - *tn.at(c));
                    *rn.at(c) += k * (rt[c] - *rn.at(c));
                    *rf.at(c) = (p.var_rain * *rn.at(c)).exp() * stormy;
                    *hit.at(c) = stormy != 1.0;
                }
            });
        }
        if whole {
            for s in &mut self.storms {
                s.left -= 1;
            }
            self.storms.retain(|s| s.left > 0);
            return;
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

    /// The sweep: degrees the wind is turned from its season's direction, by the year and by its wandering.
    pub fn wind_dev(&self, p: &Params) -> f64 {
        p.var_wind * self.w_now + p.wind_sd * self.wobble
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
    // the sweep: the air's water over each cell as the last pass left it (what `vapor` has over it since was
    // added by the living), and the share of its lifted layer a cell's height wrings out
    col: Vec<f64>,
    lift: Vec<f64>,
    // scratch
    h0: Vec<f64>,
    sin_lo: Vec<f64>,
    sin_hi: Vec<f64>,
    cos_lo: Vec<f64>,
    cos_hi: Vec<f64>,
    theta: Vec<f64>,
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

/// What a cell gains from its four edges: k x (the neighbour's value - its own), each edge's flow reckoned from
/// the same two values in the same order as its neighbour reckons it, so the edges pass exact amounts.
#[inline]
fn exchange(n: usize, x: usize, y: usize, v: &[f64], k: f64) -> f64 {
    let c = y * n + x;
    let r = y * n + if x + 1 == n { 0 } else { x + 1 };
    let l = y * n + if x == 0 { n - 1 } else { x - 1 };
    let d = (if y + 1 == n { 0 } else { y + 1 }) * n + x;
    let u = (if y == 0 { n - 1 } else { y - 1 }) * n + x;
    // the flow into c across an edge (a, b) is k (v[b] - v[a]) with (a, b) = (c, r) or (c, d), and minus the
    // flow into l or u across their own edge
    k * (v[r] - v[c]) + k * (v[d] - v[c]) - k * (v[c] - v[l]) - k * (v[c] - v[u])
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
            col: vapor.clone(),
            lift: t.air.iter().map(|&h| 1.0 - (-SAT_K * p.lapse / 1000.0 * h).exp()).collect(),
            vapor,
            ground,
            light: vec![0.0; cells],
            rain_now: vec![0.0; cells],
            rate: t.sea.iter().map(|&s| if s { p.sea_rate } else { p.land_rate }).collect(),
            inv_cap: t.sea.iter().map(|&s| if s { p.sea_rate / p.land_rate } else { 1.0 }).collect(),
            h0: vec![0.0; n],
            sin_lo: vec![0.0; n],
            sin_hi: vec![0.0; n],
            cos_lo: vec![0.0; n],
            cos_hi: vec![0.0; n],
            theta: vec![0.0; cells],
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
            let h0 = (TAU * (step / p.day + p.span_lon * x as f64 / n as f64) + PI).rem_euclid(TAU) - PI;
            self.h0[x] = h0;
            self.sin_lo[x] = h0.sin();
            self.sin_hi[x] = (h0 + span).sin();
            self.cos_lo[x] = h0.cos();
            self.cos_hi[x] = (h0 + span).cos();
        }
        // The sweep: the sea air's temperature (the sea's mean), and how much of a land cell's equilibrium it sets.
        let aspect = p.aspect != 0.0;
        let (sea_sum, sea_n) = (0..cells).filter(|&c| t.sea[c]).fold((0.0, 0usize), |(s, k), c| (s + self.temp[c], k + 1));
        let t_air = sea_sum / sea_n.max(1) as f64;
        let couple = if p.sweep != 0.0 { p.wind_ms / (p.wind_ms + p.air_couple) } else { 0.0 };
        let lapse = p.lapse / 1000.0;
        let threads = p.threads as usize;
        let wxr = &*wx;
        {
            let (light, temp, theta) = (Shared::new(&mut self.light), Shared::new(&mut self.temp), Shared::new(&mut self.theta));
            let (h0s, slo, shi, rate) = (&self.h0, &self.sin_lo, &self.sin_hi, &self.rate);
            let (clo, chi) = (&self.cos_lo, &self.cos_hi);
            par::pieces(threads, n, |ylo, yhi| {
                for y in ylo..yhi {
                    let (a, b) = (t.lat[y].sin() * sd, t.lat[y].cos() * cd);
                    let rise = if a >= b { f64::INFINITY } else if a <= -b { -1.0 } else { (-a / b).acos() };
                    let sin_rise = if rise.is_finite() && rise > 0.0 { rise.sin() } else { 0.0 };
                    for x in 0..n {
                        let c = y * n + x;
                        let (lo0, hi0) = (h0s[x], h0s[x] + span);
                        let q = if aspect {
                            // The lit part of the update - its length and the sums of the hour's sine and cosine
                            // over it - gives the sun's mean direction (up, east, north); the light is what of it
                            // falls along the ground's normal.
                            let (mut dl, mut ss, mut cc) = (0.0, 0.0, 0.0);
                            if rise.is_infinite() {
                                (dl, ss, cc) = (span, shi[x] - slo[x], chi[x] - clo[x]);
                            } else if rise >= 0.0 {
                                let cos_rise = rise.cos();
                                for noon in [0.0, TAU] {
                                    let (lo, s_lo, c_lo) = if lo0 > noon - rise { (lo0, slo[x], clo[x]) } else { (noon - rise, -sin_rise, cos_rise) };
                                    let (hi, s_hi, c_hi) = if hi0 < noon + rise { (hi0, shi[x], chi[x]) } else { (noon + rise, sin_rise, cos_rise) };
                                    if hi > lo {
                                        dl += hi - lo;
                                        ss += s_hi - s_lo;
                                        cc += c_hi - c_lo;
                                    }
                                }
                            }
                            let (sphi, cphi) = (t.lat[y].sin(), t.lat[y].cos());
                            let (up, east, north) = (a * dl + b * ss, cd * cc, cphi * sd * dl - sphi * cd * ss);
                            ((up * t.nz[c] + east * t.nx[c] + north * t.ny[c]) / span).max(0.0)
                        } else if rise.is_infinite() {
                            a + b * (shi[x] - slo[x]) / span
                        } else if rise < 0.0 {
                            0.0
                        } else {
                            let mut sum = 0.0;
                            for noon in [0.0, TAU] {
                                let (lo, s_lo) = if lo0 > noon - rise { (lo0, slo[x]) } else { (noon - rise, -sin_rise) };
                                let (hi, s_hi) = if hi0 < noon + rise { (hi0, shi[x]) } else { (noon + rise, sin_rise) };
                                if hi > lo {
                                    sum += a * (hi - lo) + b * (s_hi - s_lo);
                                }
                            }
                            (sum / span).max(0.0)
                        };
                        *light.at(c) = q;
                        let eq = if couple > 0.0 && !t.sea[c] {
                            (1.0 - couple) * (p.night + p.gain * q) + couple * t_air - lapse * t.air[c] + wxr.temp(c, p)
                        } else {
                            p.night + p.gain * q - lapse * t.air[c] + wxr.temp(c, p)
                        };
                        let v = *temp.at(c) + rate[c] * (eq - *temp.at(c));
                        *temp.at(c) = v;
                        *theta.at(c) = v + lapse * t.air[c];
                    }
                }
            });
        }
        // Heat crosses each edge by the difference of potential temperature (each edge's flow computed alike from
        // both sides, so what one cell gives the other takes).
        {
            let k = 0.25 * p.spread;
            let temp = Shared::new(&mut self.temp);
            let (theta, inv_cap) = (&self.theta, &self.inv_cap);
            par::pieces(threads, n, |ylo, yhi| {
                for y in ylo..yhi {
                    for x in 0..n {
                        let c = y * n + x;
                        let d = exchange(n, x, y, theta, k);
                        *temp.at(c) += d * inv_cap[c];
                    }
                }
            });
        }

        if p.sweep != 0.0 {
            return self.sweep(p, t, sat, wx, season, t_air, cover);
        }
        // The air takes up water where it can and rains what it cannot hold; this year's anomaly and the
        // storms change how much of the excess falls.
        let parts = {
            let (vapor, ground, rain_now) = (Shared::new(&mut self.vapor), Shared::new(&mut self.ground), Shared::new(&mut self.rain_now));
            let temp = &self.temp;
            par::pieces(threads, cells, |lo, hi| {
                let mut f = Flux::default();
                for c in lo..hi {
                    let s = sat.at(temp[c]);
                    let v = *vapor.at(c);
                    let rk = (p.rain * wxr.rain_f[c]).min(1.0);
                    if t.sea[c] {
                        let e = p.evap * (s - v).max(0.0);
                        let v1 = v + e;
                        let r = rk * (v1 - RAIN_RH * s).max(0.0);
                        *vapor.at(c) = v1 - r;
                        *rain_now.at(c) = r;
                        f.sea_evap += e;
                        f.sea_rain += r;
                    } else {
                        // A soil gives up `soil_evap` of what open water would, by its fill; water standing on it all.
                        let g = *ground.at(c);
                        let open = if g > t.cap[c] { 1.0 } else { p.soil_evap * g / t.cap[c] * cover[c] };
                        let e = (p.evap * (s - v).max(0.0) * open).min(g);
                        let v1 = v + e;
                        let r = rk * (v1 - RAIN_RH * s).max(0.0);
                        *vapor.at(c) = v1 - r;
                        *ground.at(c) = g - e + r;
                        *rain_now.at(c) = r;
                        f.land_evap += e;
                        f.land_rain += r;
                    }
                }
                f
            })
        };
        let mut f = Flux::default();
        for x in &parts {
            f.add(x);
        }

        // The winds: each row's air shifts along the row by its band's wind (linear, so nothing is lost).
        if p.wind_bands != 0.0 {
            let moved = Shared::new(&mut self.moved);
            let vapor = &self.vapor;
            par::pieces(threads, n, |ylo, yhi| {
                for y in ylo..yhi {
                    let u = zonal(p, t.lat[y], decl);
                    let sx = -u; // the air here now is the air that was upwind
                    let f0 = sx.floor();
                    let fx = sx - f0;
                    let ix = (f0 as i64).rem_euclid(n as i64) as usize;
                    for x in 0..n {
                        let x0 = (x + ix) % n;
                        let x1 = (x0 + 1) % n;
                        *moved.at(y * n + x) = (1.0 - fx) * vapor[y * n + x0] + fx * vapor[y * n + x1];
                    }
                }
            });
        } else {
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
        // The air's own mixing across each edge (what carries water across the bands), from the moved air into
        // the vapor.
        {
            let m = 0.25 * p.mix;
            let vapor = Shared::new(&mut self.vapor);
            let moved = &self.moved;
            par::pieces(threads, n, |ylo, yhi| {
                for y in ylo..yhi {
                    for x in 0..n {
                        let c = y * n + x;
                        *vapor.at(c) = moved[c] + if m > 0.0 { exchange(n, x, y, moved, m) } else { 0.0 };
                    }
                }
            });
        }
        f
    }

    /// The small world's air (e108): followed across the world in one pass, upwind cells first.
    ///
    /// A cell's air is what its two upwind neighbours send it, by the wind's share along each axis (at the
    /// windward border: sea air, as wet as the open sea keeps it). Over the cell it gains what the living gave
    /// the air since the last pass, takes up water by its deficit against the ground's own temperature, and rains
    /// its excess over what it can hold: the sea air's holding, less the share of its lifted layer that the
    /// cell's height wrings out. A column's gain or loss over one crossing is the ground's `per` times over,
    /// the crossings in an update. The pass is one after another, so it does not depend on the threads.
    fn sweep(&mut self, p: &Params, t: &Terrain, sat: &Sat, wx: &Weather, season: f64, t_air: f64, cover: &[f64]) -> Flux {
        let n = t.n;
        let secs = p.tick / p.day * 86400.0;
        let dx = p.cell_km * 1000.0;
        let deg = wx.storm_dir.unwrap_or(p.wind_dir + p.wind_turn * season + wx.wind_dev(p));
        let (a, b) = (p.wind_ms * deg.to_radians().cos(), p.wind_ms * deg.to_radians().sin());
        let (east, north) = (a >= 0.0, b >= 0.0);
        let (a, b) = (a.abs(), b.abs());
        let (pa, pb) = (a / (a + b), b / (a + b));
        let tc = dx / (a + b); // s the air spends over a cell
        let per = secs / tc; // crossings an update
        let ke = 1.0 - (-tc / p.evap_tau).exp();
        let kr = 1.0 - (-tc / p.rain_tau).exp();
        let s0 = sat.at(t_air + wx.temp(0, p));
        let c0 = RAIN_RH * s0;
        let v_in = c0 + (s0 - c0) * ke / (ke + kr); // where the open sea's taking up and raining balance
        let mut f = Flux::default();
        let (mut gained, mut inflow, mut outflow, mut dv) = (0.0, 0.0, 0.0, 0.0);
        for j in 0..n {
            let y = if north { j } else { n - 1 - j };
            let below = if j == 0 { None } else { Some(if north { y - 1 } else { y + 1 }) };
            for i in 0..n {
                let x = if east { i } else { n - 1 - i };
                let c = y * n + x;
                let vw = if i == 0 { v_in } else { self.col[y * n + if east { x - 1 } else { x + 1 }] };
                let vs = match below {
                    None => v_in,
                    Some(yb) => self.col[yb * n + x],
                };
                let added = self.vapor[c] - self.col[c];
                let mut v = pa * vw + pb * vs + added / per;
                let hold = c0 * (1.0 - (p.lifted * wx.rain_f[c]).min(1.0) * self.lift[c]);
                let r = (v - hold).max(0.0) * kr;
                let d = (sat.at(self.temp[c]) - v).max(0.0) * ke;
                let e = if t.sea[c] {
                    d
                } else {
                    // A soil gives up `soil_evap` of what open water would, by its fill; water standing on it all.
                    let g = self.ground[c];
                    let open = if g > t.cap[c] { 1.0 } else { p.soil_evap * g / t.cap[c] * cover[c] };
                    (d * open).min(g / per)
                };
                v += e - r;
                let (eg, rg) = (e * per, r * per);
                if t.sea[c] {
                    f.sea_evap += eg;
                    f.sea_rain += rg;
                } else {
                    self.ground[c] += rg - eg;
                    f.land_evap += eg;
                    f.land_rain += rg;
                }
                self.rain_now[c] = rg;
                gained += eg - rg + added;
                dv += v - self.vapor[c];
                self.col[c] = v;
                self.vapor[c] = v;
                if i == 0 {
                    inflow += a * v_in;
                }
                if j == 0 {
                    inflow += b * v_in;
                }
                if i == n - 1 {
                    outflow += a * v;
                }
                if j == n - 1 {
                    outflow += b * v;
                }
            }
        }
        // What crossed the borders, as the ground's mm: it is what the pass took up less what it rained.
        let (inflow, outflow) = (inflow * secs / dx, outflow * secs / dx);
        f.air_err = (gained - (outflow - inflow)).abs() / inflow.max(1.0);
        // The ledger holds the water over the cells as `vapor`: the wind's net take is what closes it.
        f.wind = f.sea_evap - f.sea_rain + f.land_evap - f.land_rain - dv;
        f
    }
}
