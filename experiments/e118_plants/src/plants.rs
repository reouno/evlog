//! e118 (#135 rung 2): plants at metres - a field on the cells of 5 m, and trees and shrubs as things.
//!
//! The climate, the soil's water and its A and B stay on the cells of 125 m (`climate.rs`, `hydro.rs`). A land cell
//! of 125 m holds a block of k x k fine cells of 5 m (`ground5.rs`), and on a fine cell that has soil (not water,
//! not a cliff):
//!
//! - **the field**: up to `KF` cohorts (a stand of one genotype: the mass and the A and B of each organ - leaf, wood,
//!   root, store, seed - a m2), a litter and a seed bank, by `base/`'s producer law (`base/src/life.rs`, e103-e109);
//! - **a tree** rooted in it, at most one. A stand of the field is stems that thin as they grow: each stands as high
//!   as its wood lets one stem stand (`h_stem`), their crowns (`crown_h` of the height wide) filling the cell, so a
//!   stand is as tall as the root of its wood a m2 allows. When it has thinned to one stem a cell (about 8 m on
//!   cells of 5 m) it is one plant, its matter in kg, with a place, a height and a crown `crown_h` of its height in
//!   radius - the stand's own crowns, so nothing changes the day it is counted a tree - lying over the fine cells
//!   about it. A tree with no leaf and no store is dead and falls.
//!
//! Every plant step: light falls through the crowns over a fine cell, the tallest first, and what is left through
//! the cell's field by height; carbon is paid in water drawn from the 125 m cell's one soil by every plant rooted in
//! it (ground beside a stream or a pond reaches the groundwater whatever its roots); roots take A and B from that
//! soil; growth, turnover, frost, wilting and death are the base's. Under lying snow the field has no light and no
//! frost. Fire runs from fine cell to fine cell through dry fuel the sun reaches. Seeds fall near, or go with the
//! wind from their plant's height, in metres; a free slot is won by lottery from the cell's bank.
//!
//! **Humus** (e118): a share of the A and B that rot frees stays in the soil's organic matter of the 125 m cell and
//! comes free slowly (decades), by warmth and wetness; roots take it as it does. The land starts with an old soil's
//! humus (`old_soil`): a world sown on bare rock holds, a century on, only what its rock gave in that century.
//!
//! Left out of this rung: the small eaters of leaves, the sea's producers, seeds carried by rivers.

use crate::climate::{Sat, Weather};
use crate::genome::{self, Genotype, Pheno, SIGNALS};
use crate::ground5::{self, Ground5};
use crate::noise::Rng;
use crate::par::{self, Shared};
use crate::terrain::{Terrain, NONE};
use crate::Params;
use std::borrow::Cow;
use std::collections::VecDeque;
use std::f64::consts::{PI, TAU};

pub const KF: usize = 3; // field cohorts a fine cell
pub const BANK: usize = 3; // genotypes in a fine cell's seed bank
const STORE_SHARE: f64 = 0.001; // A and B a kg of store (sugar and starch)
pub const LEAF: usize = 0;
pub const WOOD: usize = 1;
pub const ROOT: usize = 2;
pub const STORE: usize = 3;
pub const SEED: usize = 4;
const SNOW_M: f64 = 1.0 / 300.0; // m of lying snow a mm of its water (settled snow, 300 kg a m3)

#[derive(Clone, Copy, Default)]
pub struct Organ {
    pub m: f64, // kg
    pub a: f64, // g
    pub b: f64, // g
}

impl Organ {
    fn take(&mut self, f: f64) -> Organ {
        let o = Organ { m: self.m * f, a: self.a * f, b: self.b * f };
        self.m -= o.m;
        self.a -= o.a;
        self.b -= o.b;
        o
    }
    fn share_a(&self) -> f64 {
        if self.m > 1e-15 { self.a / (self.m * 1000.0) } else { 0.0 }
    }
    fn share_b(&self) -> f64 {
        if self.m > 1e-15 { self.b / (self.m * 1000.0) } else { 0.0 }
    }
    fn times(&self, k: f64) -> Organ {
        Organ { m: self.m * k, a: self.a * k, b: self.b * k }
    }
}

/// A stand of the field (its matter a m2 of its fine cell) or the body of a tree (its matter in kg).
#[derive(Clone, Copy)]
pub struct Cohort {
    pub g: u32,
    pub o: [Organ; 5],
    pub cmp: f64, // kg of compound in the leaves
    pub pa: f64,
    pub pb: f64,
    pub lpk: f64,    // the leaf mass it has held lately (sets the wood a leaf needs)
    pub lite: f64,   // the share of the light reaching its crown
    pub damage: f64, // leaf lost lately, not to turnover
    pub h: f64,      // m
    pub age: f64,    // years since it established
}

impl Default for Cohort {
    fn default() -> Self {
        Cohort { g: NONE, o: [Organ::default(); 5], cmp: 0.0, pa: 0.0, pb: 0.0, lpk: 0.0, lite: 1.0, damage: 0.0, h: 0.0, age: 0.0 }
    }
}

impl Cohort {
    pub fn mass(&self) -> f64 {
        self.o.iter().map(|o| o.m).sum()
    }
    /// Years its plants live: set by its wood - how much of it is wood, and how tough (A) that wood is (e104).
    pub fn lifespan(&self, p: &Params) -> f64 {
        let m = self.mass();
        let woody = if m > 0.0 { self.o[WOOD].m / m } else { 0.0 };
        1.0 + p.life_max * toughness(self.o[WOOD].share_a()) * woody
    }
    pub fn live(&self) -> bool {
        self.g != NONE
    }
}

#[derive(Clone, Copy, Default)]
pub struct Litter {
    pub m: f64,
    pub a: f64,
    pub b: f64,
}

impl Litter {
    fn add(&mut self, o: Organ) {
        self.m += o.m;
        self.a += o.a;
        self.b += o.b;
    }
}

#[derive(Clone, Copy)]
pub struct Seeds {
    pub g: u32,
    pub m: f64,
    pub a: f64,
    pub b: f64,
}

impl Default for Seeds {
    fn default() -> Self {
        Seeds { g: NONE, m: 0.0, a: 0.0, b: 0.0 }
    }
}

/// A tree or a shrub: one plant.
#[derive(Clone, Copy)]
pub struct Tree {
    pub b: Cohort,    // its matter in kg, its height and its age
    pub slot: u32,    // the fine cell it is rooted in (NONE: a free place in the list)
    pub r: f64,       // m: its crown's radius
    pub absa: f64,    // m2: the light its crown took at the last step, as an area fully lit
    pub drop: Litter, // kg fallen since the last step, laid under its crown after it
    pub born: u32,    // the year it became a thing
    e0: u32,
    e1: u32, // its part of the crowns' entries
    dead: bool,
}

/// A crown over a fine cell.
#[derive(Clone, Copy)]
struct Entry {
    tree: u32,
    slot: u32,
    lai: f32,  // its leaf area over the part of the cell it covers
    frac: f32, // the part of the cell it covers
    h: f32,
    took: f32, // the share of the cell's light it took
    could: f32, // and what it would take unshaded
}

/// What crossed the edges of the living in a stretch of time, in kg.
#[derive(Default, Clone, Copy)]
pub struct LFlux {
    pub fixed: f64,    // made from the air (and sown)
    pub returned: f64, // back to the air: respired, unused, decayed, burnt
    pub gpp: f64,
    pub resp: f64,
    pub transp: f64, // litres
    pub decayed: f64,
    pub burnt: f64,
    pub burnt_cells: f64,
    pub fires: f64,
    pub grown: f64, // cohorts that became trees
    pub fallen: f64, // trees that died
}

impl LFlux {
    pub fn add(&mut self, o: &LFlux) {
        self.fixed += o.fixed;
        self.returned += o.returned;
        self.gpp += o.gpp;
        self.resp += o.resp;
        self.transp += o.transp;
        self.decayed += o.decayed;
        self.burnt += o.burnt;
        self.burnt_cells += o.burnt_cells;
        self.fires += o.fires;
        self.grown += o.grown;
        self.fallen += o.fallen;
    }
}

pub struct Plants {
    pub n: usize,  // coarse cells a side
    pub k: usize,  // fine cells a coarse cell's side
    pub nf: usize, // fine cells a side
    pub fm: f64,   // m: a fine cell's side
    pub fa: f64,   // m2: a fine cell
    pub ca: f64,   // m2: a coarse cell
    pub lands: Vec<u32>,   // the coarse cells that hold a block, in order
    pub land_of: Vec<u32>, // a coarse cell's block (NONE: sea)
    pub grows: Vec<bool>,  // a slot with soil
    pub wet: Vec<bool>,    // a slot beside water: the groundwater is within reach
    pub co: Vec<Cohort>,
    pub bank: Vec<Seeds>,
    pub lit: Vec<Litter>,
    pub tree_at: Vec<u32>,
    pub under: Vec<f32>, // the share of the light that comes through the crowns to the field
    pub sun: Vec<f32>,   // and through the field to the ground
    pub burnt_year: Vec<u16>, // the year a slot last burnt (0: never)
    pub trees: Vec<Tree>,
    free: Vec<u32>,
    entries: Vec<Entry>,
    cstart: Vec<u32>,
    cidx: Vec<u32>,
    pub cover: Vec<f64>, // coarse: the share of the sun reaching the soil (the climate's evaporation reads it)
    pub hum_a: Vec<f64>, // coarse: g of A a m2 in the soil's humus
    pub hum_b: Vec<f64>,
    pub gen: Vec<Option<Box<Genotype>>>,
    pub founders: usize,
    light: Vec<f64>,
    temp: Vec<f64>,
    snow: Vec<f64>,
    stormy: Vec<bool>,
    acc: usize,
    rng: Rng,
    pub steps: u64,
    soil: Vec<u32>, // the slots with soil
    burning: Vec<bool>,
    pub transp: Vec<f64>, // coarse: mm this year
    pub burnt: Vec<f64>,  // coarse: fine cells burnt this year
    pub secs: [f64; 6],   // time spent: crowns, light, growth, fire, seeds, the rest (this year)
}

fn q10(t: f64) -> f64 {
    2f64.powf((t.clamp(-30.0, 45.0) - 20.0) / 10.0)
}

fn activity(share: f64) -> f64 {
    share / (share + 0.01)
}

pub fn toughness(share: f64) -> f64 {
    share / (share + 0.01)
}

/// The A and B shares new tissue of each organ is built with.
fn shares(ph: &Pheno, genes: usize, p: &Params) -> [(f64, f64); 5] {
    [
        (ph.leaf_a, ph.leaf_b + ph.compound * p.b_comp),
        (ph.wood_a, ph.wood_b),
        (ph.root_a, ph.root_b),
        (STORE_SHARE, STORE_SHARE),
        (ph.leaf_a, ph.leaf_b + genes as f64 * p.b_gene),
    ]
}

/// A plant during a step, between the pass that reads its light and the one that shares the water.
struct Tmp<'a> {
    ph: Cow<'a, Pheno>,
    genes: usize,
    at: usize,    // index into `co`, or the tree's index
    tree: bool,
    scale: f64,   // its unit in kg (a fine cell's m2 for a cohort, 1 for a tree)
    pp: f64,      // kg it could fix, in its own unit
    act: f64,
    rs: f64,
    rd: f64,   // kg of root reaching the soil, and the groundwater
    ract: f64, // kg of root by its activity
    snowed: bool,
    slot: usize,
    area: f64, // m2 it stands over
}

/// What a step's length makes of the rates that are the same for every plant.
struct Rates {
    dt: f64,
    flush: f64,
    store: f64,
    damage: f64,
    lpk: f64,
}

impl Rates {
    fn new(p: &Params, dt: f64) -> Self {
        Rates { dt, flush: 1.0 - (-p.flush * dt).exp(), store: 1.0 - (-p.store_turn * dt).exp(), damage: (-12.0 * dt).exp(), lpk: (-dt).exp() }
    }
}

/// A tree's height: its genome's (where to stop growing: what stands does not shrink when a plastic genome's limit
/// falls - a stand of 8 m became trees of 1.6 m at a signal), what its wood holds up over its leaves (`sigma`), and
/// what its wood can stand as one stem (e118: `h_stem` m at a kg, by the mass's fourth root - a stem as slender as trees are, 50 d^(2/3)).
fn tree_height(p: &Params, ph: &Pheno, y: &Cohort) -> f64 {
    ph.height.max(y.h).min(p.h0 + y.o[WOOD].m / (p.sigma * y.lpk.max(1e-4))).min(p.h0 + p.h_stem * y.o[WOOD].m.sqrt().sqrt())
}

/// A stand's height (its matter a m2): the same, its wood shared among the stems whose crowns, `crown_h` of the
/// height in radius, fill the ground - so many stems while it is low, fewer as it grows. With n stems a m2, each
/// of wood w / n and height h_stem (w / n)^(1/4), and n pi (crown_h h)^2 = 1: h = h_stem^2 crown_h sqrt(pi w).
fn stand_height(p: &Params, ph: &Pheno, y: &Cohort) -> f64 {
    ph.height.max(y.h).min(p.h0 + y.o[WOOD].m / (p.sigma * y.lpk.max(1e-4))).min(p.h0 + p.h_stem * p.h_stem * p.crown_h * (PI * y.o[WOOD].m).sqrt())
}

/// One plant's carbon, growth and losses over a step: the base's law (`base/src/life.rs`). `y` holds its matter in
/// its own unit (kg a m2 for a field cohort, kg for a tree) and `scale` turns that unit into kg for the ledger.
#[allow(clippy::too_many_arguments)]
fn grow(p: &Params, k: &Rates, ph: &Pheno, genes: usize, y: &mut Cohort, gpp: f64, stress: f64, t: f64, q10t: f64, frosty: bool, stormy: bool, scale: f64, lit: &mut Litter, f: &mut LFlux) {
    let dt = k.dt;
    let sh = shares(ph, genes, p);
    let bkg = (y.o[LEAF].b + y.o[WOOD].b + y.o[ROOT].b) / 1000.0;
    let resp = p.resp * q10t * bkg * dt;
    f.gpp += gpp * scale;
    f.fixed += gpp * scale;
    let net = gpp - resp;
    // Leaves below half of what it held lately are rebuilt from the store (a spring, a regrowth).
    if y.o[LEAF].m < 0.5 * y.lpk && y.o[STORE].m > 0.0 {
        let s = y.o[STORE].take(k.flush);
        y.pa += s.a;
        y.pb += s.b;
        // this mass is built into leaves below, as if fixed now: count it out and in again
        f.returned += s.m * scale;
        f.fixed += s.m * scale;
        let (la, lb) = sh[LEAF];
        let k = (1.0f64).min(y.pa / (s.m * 1000.0 * la).max(1e-30)).min(y.pb / (s.m * 1000.0 * lb).max(1e-30));
        let use_ = s.m * k;
        y.o[LEAF].m += use_;
        y.o[LEAF].a += use_ * 1000.0 * la;
        y.o[LEAF].b += use_ * 1000.0 * lb;
        y.cmp += use_ * ph.compound;
        y.pa -= use_ * 1000.0 * la;
        y.pb -= use_ * 1000.0 * lb;
        f.returned += (s.m - use_) * scale;
    }
    if net >= 0.0 {
        let (mut ra, mut rb) = (0.0, 0.0);
        for o in 0..5 {
            ra += net * ph.alloc[o] * 1000.0 * sh[o].0;
            rb += net * ph.alloc[o] * 1000.0 * sh[o].1;
        }
        let k = 1.0f64.min(if ra > 0.0 { y.pa / ra } else { 1.0 }).min(if rb > 0.0 { y.pb / rb } else { 1.0 });
        let use_ = net * k;
        for o in 0..5 {
            let dm = use_ * ph.alloc[o];
            y.o[o].m += dm;
            y.o[o].a += dm * 1000.0 * sh[o].0;
            y.o[o].b += dm * 1000.0 * sh[o].1;
        }
        y.cmp += use_ * ph.alloc[LEAF] * ph.compound;
        y.pa = (y.pa - ra * k).max(0.0);
        y.pb = (y.pb - rb * k).max(0.0);
        f.returned += (resp + (net - use_)) * scale;
        f.resp += resp * scale;
    } else {
        // Short of carbon: the store pays, then the tissue.
        let mut deficit = -net;
        let from = deficit.min(y.o[STORE].m);
        if from > 0.0 {
            let s = y.o[STORE].take(from / y.o[STORE].m);
            y.pa += s.a;
            y.pb += s.b;
            deficit -= s.m;
        }
        if deficit > 0.0 {
            let tissue = y.o[LEAF].m + y.o[WOOD].m + y.o[ROOT].m + y.o[SEED].m;
            let k = (deficit / tissue.max(1e-30)).min(1.0);
            for o in [LEAF, WOOD, ROOT, SEED] {
                let s = y.o[o].take(k);
                y.pa += s.a;
                y.pb += s.b;
            }
            y.cmp *= 1.0 - k;
            let paid = tissue * k;
            f.returned += (gpp + from + paid) * scale;
            f.resp += (gpp + from + paid) * scale;
        } else {
            f.returned += resp * scale;
            f.resp += resp * scale;
        }
    }
    // Losses to the litter.
    let tl = toughness(y.o[LEAF].share_a());
    let tw = toughness(y.o[WOOD].share_a());
    let tr = toughness(y.o[ROOT].share_a());
    let frost = if t < 0.0 && frosty { p.frost * (-t / 10.0) * (1.0 - tl) } else { 0.0 };
    let wilt = p.wilt * (1.0 - stress) * (1.0 - tl);
    let mut fl = 1.0 - (-(p.leaf_turn * (1.0 - 0.8 * tl) + ph.shed + frost + wilt) * dt).exp();
    let mut fw = 1.0 - (-p.wood_turn * (1.0 - 0.8 * tw) * dt).exp();
    let fr = 1.0 - (-p.root_turn * (1.0 - 0.8 * tr) * dt).exp();
    let fs = k.store;
    let mut hurt = 1.0 - (-(frost + wilt) * dt).exp();
    if stormy {
        let s = p.storm_fell * (y.h / p.h_storm).powi(2).min(1.0) * (1.0 - tw);
        fl = 1.0 - (1.0 - fl) * (1.0 - s);
        fw = 1.0 - (1.0 - fw) * (1.0 - s);
        hurt += s;
    }
    lit.add(y.o[LEAF].take(fl));
    y.cmp *= 1.0 - fl;
    lit.add(y.o[WOOD].take(fw));
    lit.add(y.o[ROOT].take(fr));
    lit.add(y.o[STORE].take(fs));
    y.damage = y.damage * k.damage + hurt;
    y.lpk = y.o[LEAF].m.max(y.lpk * k.lpk);
    y.age += dt;
}

impl Plants {
    pub fn new(ter: &Terrain, p: &Params, g: &Ground5) -> Self {
        let n = ter.n;
        let k = g.n / n;
        let nf = g.n;
        let f2 = k * k;
        let lands: Vec<u32> = (0..n * n).filter(|&c| !ter.sea[c]).map(|c| c as u32).collect();
        let mut land_of = vec![NONE; n * n];
        for (b, &c) in lands.iter().enumerate() {
            land_of[c as usize] = b as u32;
        }
        let slots = lands.len() * f2;
        let mut pl = Plants {
            n,
            k,
            nf,
            fm: g.cell_m,
            fa: g.cell_m * g.cell_m,
            ca: (p.cell_km * 1000.0).powi(2),
            lands,
            land_of,
            grows: vec![false; slots],
            wet: vec![false; slots],
            co: vec![Cohort::default(); slots * KF],
            bank: vec![Seeds::default(); slots * BANK],
            lit: vec![Litter::default(); slots],
            tree_at: vec![NONE; slots],
            under: vec![1.0; slots],
            sun: vec![1.0; slots],
            burnt_year: vec![0; slots],
            trees: Vec::new(),
            free: Vec::new(),
            entries: Vec::new(),
            cstart: vec![0; slots + 1],
            cidx: Vec::new(),
            cover: vec![1.0; n * n],
            hum_a: vec![0.0; n * n],
            hum_b: vec![0.0; n * n],
            gen: Vec::new(),
            founders: 0,
            light: vec![0.0; n * n],
            temp: vec![0.0; n * n],
            snow: vec![0.0; n * n],
            stormy: vec![false; n * n],
            acc: 0,
            rng: Rng::new(p.life as u64 ^ 0x11FE),
            steps: 0,
            soil: Vec::new(),
            burning: vec![false; slots],
            transp: vec![0.0; n * n],
            burnt: vec![0.0; n * n],
            secs: [0.0; 6],
        };
        // Soil: land that is not water and not a cliff. Beside water: within `wet_reach` of a pond or a stream and
        // no more than `wet_rise` over its surface.
        let h = |i: usize, j: usize| g.height[j * nf + i] as f64;
        for s in 0..slots {
            let (i, j) = pl.ij(s);
            if g.kind[j * nf + i] != ground5::LAND {
                continue;
            }
            let mut steep: f64 = 0.0;
            for (di, dj) in [(1i64, 0i64), (-1, 0), (0, 1), (0, -1)] {
                let (a, b) = (i as i64 + di, j as i64 + dj);
                if a >= 0 && b >= 0 && (a as usize) < nf && (b as usize) < nf {
                    steep = steep.max((h(i, j) - h(a as usize, b as usize)).abs() / g.cell_m);
                }
            }
            pl.grows[s] = steep <= p.steep;
        }
        let reach = (p.wet_reach / g.cell_m).round() as i64;
        for j in 0..nf {
            for i in 0..nf {
                let kd = g.kind[j * nf + i];
                if kd != ground5::POND && kd != ground5::STREAM {
                    continue;
                }
                let level = (g.height[j * nf + i] + g.water[j * nf + i]) as f64;
                for dj in -reach..=reach {
                    for di in -reach..=reach {
                        let (a, b) = (i as i64 + di, j as i64 + dj);
                        if a < 0 || b < 0 || a as usize >= nf || b as usize >= nf {
                            continue;
                        }
                        if let Some(s) = pl.slot(a as usize, b as usize) {
                            if pl.grows[s] && h(a as usize, b as usize) <= level + p.wet_rise {
                                pl.wet[s] = true;
                            }
                        }
                    }
                }
            }
        }
        pl.soil = (0..slots).filter(|&s| pl.grows[s]).map(|s| s as u32).collect();
        pl
    }

    /// The height at which a stand has thinned to one stem a fine cell: its crown as wide as the cell.
    pub fn h_thing(&self, p: &Params) -> f64 {
        (self.fa / PI).sqrt() / p.crown_h
    }

    /// A slot's fine cell (column, row).
    pub fn ij(&self, s: usize) -> (usize, usize) {
        let f2 = self.k * self.k;
        let c = self.lands[s / f2] as usize;
        let l = s % f2;
        ((c % self.n) * self.k + l % self.k, (c / self.n) * self.k + l / self.k)
    }

    /// The slot of a fine cell, if its coarse cell is land.
    pub fn slot(&self, i: usize, j: usize) -> Option<usize> {
        let b = self.land_of[(j / self.k) * self.n + i / self.k];
        if b == NONE { None } else { Some(b as usize * self.k * self.k + (j % self.k) * self.k + i % self.k) }
    }

    /// The slot a thing lands in, (dx, dy) m from a point of slot `s`'s cell; None off the land.
    fn land(&mut self, s: usize, dx: f64, dy: f64) -> Option<usize> {
        let (i, j) = self.ij(s);
        let x = (i as f64 + self.rng.f64() + dx / self.fm).floor();
        let y = (j as f64 + self.rng.f64() + dy / self.fm).floor();
        if x < 0.0 || y < 0.0 || x >= self.nf as f64 || y >= self.nf as f64 {
            return None;
        }
        self.slot(x as usize, y as usize).filter(|&d| self.grows[d])
    }

    /// Every update: the light, heat, snow and storms the next plant step reads.
    pub fn accumulate(&mut self, light: &[f64], temp: &[f64], snow: &[f64], hit: &[bool]) {
        for c in 0..light.len() {
            self.light[c] += light[c];
            self.temp[c] += temp[c];
            self.snow[c] += snow[c];
            self.stormy[c] |= hit[c];
        }
        self.acc += 1;
    }

    pub fn due(&self, p: &Params) -> bool {
        self.acc >= p.life_every as usize
    }

    /// An old soil's humus: `old_soil` years of what a cell's rock gives, by the depth of its soil. What it adds to
    /// the land's A and B comes back for the ledger.
    pub fn old_soil(&mut self, p: &Params, ter: &Terrain) -> (f64, f64) {
        let (mut a, mut b) = (0.0, 0.0);
        for &c in &self.lands {
            let c = c as usize;
            let r = &crate::terrain::ROCKS[ter.rock[c] as usize];
            let deep = ter.cap[c] / (p.soil * r.hold).max(1e-9);
            self.hum_a[c] = p.old_soil * p.weather * r.a * deep;
            self.hum_b[c] = p.old_soil * p.weather * r.b * deep;
            a += self.hum_a[c];
            b += self.hum_b[c];
        }
        (a, b)
    }

    /// The founders: `founders` random genomes. Their seed rains on every cell with soil for `sow_years`.
    pub fn found(&mut self, p: &Params, year: u32) {
        for _ in 0..p.founders as usize {
            let g = genome::random(&mut self.rng, false);
            self.gen.push(Some(Box::new(Genotype::new(g, NONE, year, false))));
        }
        self.founders = self.gen.len();
    }

    /// A founder's seed on every cell with soil, its A and B taken from the soil.
    fn sow(&mut self, p: &Params, sa: &mut [f64], sb: &mut [f64], f: &mut LFlux) {
        let f2 = self.k * self.k;
        for q in 0..self.soil.len() {
            let s = self.soil[q] as usize;
            let c = self.lands[s / f2] as usize;
            let g = self.rng.below(self.founders) as u32;
            let ph = &self.gen[g as usize].as_ref().unwrap().base;
            let m = p.sow_mass;
            let k = self.fa / self.ca;
            let a = (m * 1000.0 * ph.leaf_a).min(0.5 * sa[c] / k);
            let b = (m * 1000.0 * ph.leaf_b).min(0.5 * sb[c] / k);
            sa[c] -= a * k;
            sb[c] -= b * k;
            f.fixed += m * self.fa;
            self.deposit(s, g, Organ { m, a, b });
        }
    }

    /// The crowns over the fine cells: each tree's cells, then each cell's crowns.
    fn crowns(&mut self, p: &Params) {
        self.entries.clear();
        let fa = self.fa;
        for ti in 0..self.trees.len() {
            let t = self.trees[ti];
            if t.slot == NONE {
                continue;
            }
            let e0 = self.entries.len() as u32;
            let area = p.sla * t.b.o[LEAF].m;
            let (i, j) = self.ij(t.slot as usize);
            let disc = PI * t.r * t.r;
            if disc <= fa {
                self.entries.push(Entry { tree: ti as u32, slot: t.slot, lai: (area / disc) as f32, frac: (disc / fa) as f32, h: t.b.h as f32, took: 0.0, could: 0.0 });
            } else {
                // its own cell whole, and the rest of the disc shared among the cells about it, the nearer the more
                let rr = t.r / self.fm;
                let ri = (rr + 0.5) as i64;
                let mut ring = 0.0;
                for dj in -ri..=ri {
                    for di in -ri..=ri {
                        let own = di == 0 && dj == 0;
                        let w = if own { 1.0 } else { (rr + 0.5 - ((di * di + dj * dj) as f64).sqrt()).clamp(0.0, 1.0) };
                        if w <= 0.0 {
                            continue;
                        }
                        let (a, b) = (i as i64 + di, j as i64 + dj);
                        if a < 0 || b < 0 || a as usize >= self.nf || b as usize >= self.nf {
                            continue;
                        }
                        if let Some(s) = self.slot(a as usize, b as usize) {
                            self.entries.push(Entry { tree: ti as u32, slot: s as u32, lai: 0.0, frac: w as f32, h: t.b.h as f32, took: 0.0, could: 0.0 });
                            if !own {
                                ring += w;
                            }
                        }
                    }
                }
                let k = if ring > 0.0 { ((disc / fa - 1.0) / ring).min(1.0) } else { 0.0 };
                let mut cells = 0.0;
                for e in &mut self.entries[e0 as usize..] {
                    if e.slot != t.slot {
                        e.frac = (e.frac as f64 * k) as f32;
                    }
                    cells += e.frac as f64;
                }
                let lai = (area / (cells.max(1e-9) * fa)) as f32;
                for e in &mut self.entries[e0 as usize..] {
                    e.lai = lai;
                }
            }
            self.trees[ti].e0 = e0;
            self.trees[ti].e1 = self.entries.len() as u32;
        }
        // each cell's crowns, by a counting sort
        let slots = self.grows.len();
        self.cstart.iter_mut().for_each(|v| *v = 0);
        for e in &self.entries {
            self.cstart[e.slot as usize + 1] += 1;
        }
        for s in 0..slots {
            self.cstart[s + 1] += self.cstart[s];
        }
        self.cidx.clear();
        self.cidx.resize(self.entries.len(), 0);
        let mut at: Vec<u32> = self.cstart[..slots].to_vec();
        for (q, e) in self.entries.iter().enumerate() {
            self.cidx[at[e.slot as usize] as usize] = q as u32;
            at[e.slot as usize] += 1;
        }
    }

    /// The light through the crowns over each fine cell, the tallest first; what each tree took.
    fn light(&mut self, p: &Params, threads: usize) {
        let slots = self.grows.len();
        {
            let (ent, under) = (Shared::new(&mut self.entries), Shared::new(&mut self.under));
            let (cstart, cidx) = (&self.cstart, &self.cidx);
            par::pieces(threads, slots, |lo, hi| {
                let mut ord: Vec<u32> = Vec::new();
                for s in lo..hi {
                    let (a, b) = (cstart[s] as usize, cstart[s + 1] as usize);
                    if a == b {
                        *under.at(s) = 1.0;
                        continue;
                    }
                    ord.clear();
                    ord.extend_from_slice(&cidx[a..b]);
                    ord.sort_by(|&x, &y| ent.at(y as usize).h.partial_cmp(&ent.at(x as usize).h).unwrap().then(x.cmp(&y)));
                    let mut through = 1.0f64;
                    for &q in &ord {
                        let e = ent.at(q as usize);
                        let took = e.frac as f64 * (1.0 - (-p.ext * e.lai as f64).exp());
                        e.took = (through * took) as f32;
                        e.could = took as f32;
                        through *= 1.0 - took;
                    }
                    *under.at(s) = through as f32;
                }
            });
        }
        for t in &mut self.trees {
            if t.slot == NONE {
                continue;
            }
            let (mut took, mut could) = (0.0, 0.0);
            for e in &self.entries[t.e0 as usize..t.e1 as usize] {
                took += e.took as f64;
                could += e.could as f64;
            }
            t.absa = took * self.fa;
            t.b.lite = if could > 0.0 { took / could } else { 1.0 };
        }
    }

    /// One plant step, after `life_every` updates of the climate.
    #[allow(clippy::too_many_arguments)]
    pub fn step(&mut self, p: &Params, ter: &Terrain, sat: &Sat, wx: &Weather, ground: &mut [f64], vapor: &mut [f64], deep: &mut [f64], sa: &mut [f64], sb: &mut [f64], step: f64, year: u32) -> LFlux {
        let t0 = std::time::Instant::now();
        let kacc = self.acc as f64;
        for c in 0..self.light.len() {
            self.light[c] /= kacc;
            self.temp[c] /= kacc;
            self.snow[c] /= kacc;
        }
        let threads = (p.threads as usize).max(1);
        let dt = p.life_every * p.tick / p.year;
        let phase = TAU * step / p.year;
        self.crowns(p);
        let t1 = std::time::Instant::now();
        self.light(p, threads);
        let t2 = std::time::Instant::now();
        let mut f = LFlux::default();
        let (grown, fallen) = self.growth(p, ter, sat, ground, vapor, deep, sa, sb, dt, phase, threads, &mut f);
        // a stand thinned to one stem a cell is a tree: the whole of it
        for (s, i) in grown {
            if self.tree_at[s] != NONE {
                continue;
            }
            let y = std::mem::take(&mut self.co[s * KF + i]);
            let mut b = Cohort { g: y.g, cmp: y.cmp * self.fa, pa: y.pa * self.fa, pb: y.pb * self.fa, lpk: y.lpk * self.fa, lite: y.lite, damage: y.damage, h: y.h, age: y.age, ..Default::default() };
            for o in 0..5 {
                b.o[o] = y.o[o].times(self.fa);
            }
            let r = (p.crown_h * b.h).max(0.3);
            let t = Tree { b, slot: s as u32, r, absa: 0.0, drop: Litter::default(), born: year, e0: 0, e1: 0, dead: false };
            let id = match self.free.pop() {
                Some(id) => {
                    self.trees[id as usize] = t;
                    id
                }
                None => {
                    self.trees.push(t);
                    (self.trees.len() - 1) as u32
                }
            };
            self.tree_at[s] = id;
            f.grown += 1.0;
        }
        // what fell from the trees is laid under their crowns; the dead fall whole
        for id in fallen {
            let t = &mut self.trees[id as usize];
            for o in t.b.o {
                t.drop.add(o);
            }
            t.drop.a += t.b.pa;
            t.drop.b += t.b.pb;
            t.dead = true;
            f.fallen += 1.0;
        }
        for ti in 0..self.trees.len() {
            let t = self.trees[ti];
            if t.slot == NONE {
                continue;
            }
            if t.drop.m > 0.0 || t.drop.a > 0.0 || t.drop.b > 0.0 {
                let own = [Entry { tree: 0, slot: t.slot, lai: 0.0, frac: 1.0, h: 0.0, took: 0.0, could: 0.0 }];
                let es = if t.e1 > t.e0 { &self.entries[t.e0 as usize..t.e1 as usize] } else { &own[..] };
                let cells: f64 = es.iter().filter(|e| self.grows[e.slot as usize]).map(|e| e.frac as f64).sum();
                let mut laid = false;
                if cells > 1e-6 {
                    for e in es {
                        if self.grows[e.slot as usize] {
                            let k = e.frac as f64 / (cells * self.fa);
                            let l = &mut self.lit[e.slot as usize];
                            l.m += t.drop.m * k;
                            l.a += t.drop.a * k;
                            l.b += t.drop.b * k;
                            laid = true;
                        }
                    }
                }
                if !laid {
                    let l = &mut self.lit[t.slot as usize];
                    l.m += t.drop.m / self.fa;
                    l.a += t.drop.a / self.fa;
                    l.b += t.drop.b / self.fa;
                }
                self.trees[ti].drop = Litter::default();
            }
            if t.dead {
                self.tree_at[t.slot as usize] = NONE;
                self.trees[ti].slot = NONE;
                self.trees[ti].e0 = 0;
                self.trees[ti].e1 = 0;
                self.free.push(ti as u32);
            }
        }
        let t3 = std::time::Instant::now();
        self.fire(p, ter, ground, sa, sb, dt, year, &mut f);
        let t4 = std::time::Instant::now();
        self.steps += 1;
        if self.steps % (p.seed_every as u64) == 0 {
            self.seeds(p, ter, wx, phase.sin(), year);
            if year < p.sow as u32 + p.sow_years as u32 {
                self.sow(p, sa, sb, &mut f);
            }
            self.establish(p, ter, ground, dt * p.seed_every);
        }
        let t5 = std::time::Instant::now();
        for c in 0..self.light.len() {
            self.light[c] = 0.0;
            self.temp[c] = 0.0;
            self.snow[c] = 0.0;
            self.stormy[c] = false;
        }
        self.acc = 0;
        self.secs[0] += (t1 - t0).as_secs_f64();
        self.secs[1] += (t2 - t1).as_secs_f64();
        self.secs[2] += (t3 - t2).as_secs_f64();
        self.secs[3] += (t4 - t3).as_secs_f64();
        self.secs[4] += (t5 - t4).as_secs_f64();
        self.secs[5] += t5.elapsed().as_secs_f64();
        f
    }

    /// Carbon, water, A and B, growth and death, block by block: the cohorts that became things and the trees that
    /// died come back for the caller to move.
    #[allow(clippy::too_many_arguments)]
    fn growth(&mut self, p: &Params, ter: &Terrain, sat: &Sat, ground: &mut [f64], vapor: &mut [f64], deep: &mut [f64], sa: &mut [f64], sb: &mut [f64], dt: f64, phase: f64, threads: usize, f: &mut LFlux) -> (Vec<(usize, usize)>, Vec<u32>) {
        let f2 = self.k * self.k;
        let (fa, ca) = (self.fa, self.ca);
        let (season, season_cos) = (phase.sin(), phase.cos());
        let (co, bank, lit, sun, trees) = (Shared::new(&mut self.co), Shared::new(&mut self.bank), Shared::new(&mut self.lit), Shared::new(&mut self.sun), Shared::new(&mut self.trees));
        let (ground, vapor, deep, sa, sb) = (Shared::new(ground), Shared::new(vapor), Shared::new(deep), Shared::new(sa), Shared::new(sb));
        let (cover, transp) = (Shared::new(&mut self.cover), Shared::new(&mut self.transp));
        let (hum_a, hum_b) = (Shared::new(&mut self.hum_a), Shared::new(&mut self.hum_b));
        let (lands, grows, wet, tree_at, under, gen) = (&self.lands, &self.grows, &self.wet, &self.tree_at, &self.under, &self.gen);
        let (light, temp, snow, stormy) = (&self.light, &self.temp, &self.snow, &self.stormy);
        let n = self.n;
        let rates = Rates::new(p, dt);
        let rates = &rates;
        let h_thing = self.h_thing(p);
        let parts = par::pieces(threads, lands.len(), |lo, hi| {
            let mut f = LFlux::default();
            let mut grown: Vec<(usize, usize)> = Vec::new();
            let mut fallen: Vec<u32> = Vec::new();
            let mut tmp: Vec<Tmp> = Vec::new();
            for b in lo..hi {
                let c = lands[b] as usize;
                let (q, t) = (light[c], temp[c]);
                let fill = (*ground.at(c) / ter.cap[c]).min(1.0);
                let q10t = q10(t);
                let depth = snow[c] * SNOW_M;
                let ls = if ter.lat[c / n] >= 0.0 { 1.0 } else { -1.0 };
                let mut sig = [0.0; SIGNALS];
                sig[0] = 0.5 + 0.5 * season * ls;
                sig[1] = 0.5 + 0.5 * season_cos * ls;
                sig[2] = ((t + 20.0) / 60.0).clamp(0.0, 1.0);
                sig[3] = fill;
                tmp.clear();
                let (mut rs, mut rd, mut rt) = (0.0, 0.0, 0.0);
                let mut open = 0.0;
                // the light, and what each plant could fix with it
                for l in 0..f2 {
                    let s = b * f2 + l;
                    if !grows[s] {
                        open += 1.0;
                        continue;
                    }
                    let first = tmp.len();
                    let has_tree = tree_at[s] != NONE;
                    for i in 0..KF {
                        let y = co.at(s * KF + i);
                        if !y.live() {
                            continue;
                        }
                        let gt = gen[y.g as usize].as_ref().unwrap();
                        let mass = y.mass();
                        sig[4] = y.lite;
                        sig[5] = ((mass / 1e-4).max(1.0).ln() / (1e5f64).ln()).clamp(0.0, 1.0);
                        sig[6] = if mass > 0.0 { y.o[STORE].m / mass } else { 0.0 };
                        sig[7] = (10.0 * y.damage).min(1.0);
                        let ph = gt.pheno_cow(&sig);
                        y.h = stand_height(p, &ph, y);
                        if has_tree {
                            y.h = y.h.min(h_thing);
                        }
                        tmp.push(Tmp { ph, genes: gt.genes.len(), at: s * KF + i, tree: false, scale: fa, pp: 0.0, act: 0.0, rs: 0.0, rd: 0.0, ract: 0.0, snowed: y.h < depth, slot: s, area: fa });
                    }
                    // the field's own layers under the crowns, the tallest first
                    tmp[first..].sort_by(|x, y| co.at(y.at).h.partial_cmp(&co.at(x.at).h).unwrap().then(x.at.cmp(&y.at)));
                    let mut above = 0.0;
                    let through = under[s] as f64;
                    for x in &mut tmp[first..] {
                        let y = co.at(x.at);
                        let mut absb = 0.0;
                        if !x.snowed {
                            let lai = p.sla * y.o[LEAF].m;
                            y.lite = through * (-p.ext * above).exp();
                            absb = y.lite * (1.0 - (-p.ext * lai).exp());
                            above += lai;
                        }
                        let bact = if y.o[LEAF].m > 1e-15 { ((y.o[LEAF].b - y.cmp * 1000.0 * p.b_comp).max(0.0)) / (y.o[LEAF].m * 1000.0) } else { 0.0 };
                        x.act = activity(bact);
                        let w = x.ph.breadth;
                        let ft = 10.0 / w * (-((t - x.ph.t_opt) / w).powi(2)).exp();
                        x.pp = p.gpp_max * (q / p.light_ref) * absb * x.act * ft * dt;
                        let root = y.o[ROOT].m * fa;
                        x.rs = root * (1.0 - x.ph.deep);
                        x.rd = if wet[s] { root } else { root * x.ph.deep };
                        x.ract = root * activity(y.o[ROOT].share_b());
                    }
                    let ground_light = through * (-p.ext * above).exp();
                    *sun.at(s) = ground_light as f32;
                    open += ground_light;
                    if has_tree {
                        let ti = tree_at[s] as usize;
                        let tr = trees.at(ti);
                        let y = &mut tr.b;
                        let gt = gen[y.g as usize].as_ref().unwrap();
                        let crown = (PI * tr.r * tr.r).max(1.0);
                        let mass = y.mass() / crown;
                        sig[4] = y.lite;
                        sig[5] = ((mass / 1e-4).max(1.0).ln() / (1e5f64).ln()).clamp(0.0, 1.0);
                        sig[6] = if mass > 0.0 { y.o[STORE].m / y.mass() } else { 0.0 };
                        sig[7] = (10.0 * y.damage).min(1.0);
                        let ph = gt.pheno_cow(&sig);
                        y.h = tree_height(p, &ph, y);
                        tr.r = (p.crown_h * y.h).max(0.3);
                        let bact = if y.o[LEAF].m > 1e-15 { ((y.o[LEAF].b - y.cmp * 1000.0 * p.b_comp).max(0.0)) / (y.o[LEAF].m * 1000.0) } else { 0.0 };
                        let act = activity(bact);
                        let w = ph.breadth;
                        let ft = 10.0 / w * (-((t - ph.t_opt) / w).powi(2)).exp();
                        let pp = p.gpp_max * (q / p.light_ref) * tr.absa * act * ft * dt;
                        let root = y.o[ROOT].m;
                        let rsh = root * (1.0 - ph.deep);
                        let rdp = if wet[s] { root } else { root * ph.deep };
                        let ract = root * activity(y.o[ROOT].share_b());
                        tmp.push(Tmp { ph, genes: gt.genes.len(), at: ti, tree: true, scale: 1.0, pp, act, rs: rsh, rd: rdp, ract, snowed: false, slot: s, area: PI * tr.r * tr.r });
                    }
                }
                for x in &tmp {
                    rs += x.rs;
                    rd += x.rd;
                    rt += x.ract;
                }
                *cover.at(c) = open / f2 as f64;
                // the litter decays by warmth, wetness and its own A:B - before the roots take up, in the same step: what
                // rot frees among roots is theirs, not the next five days' rain's (the base let it lie a step in the soil)
                let (mut da, mut db) = (0.0, 0.0);
                for l in 0..f2 {
                    let s = b * f2 + l;
                    let li = lit.at(s);
                    if li.m > 1e-15 {
                        let la = li.a / (li.m * 1000.0);
                        let lb = li.b / (li.m * 1000.0);
                        let qual = 2.0 * lb / (lb + 0.005) / (1.0 + la / 0.01);
                        let k = 1.0 - (-p.decay * q10t * fill * qual * dt).exp();
                        let o = Organ { m: li.m * k, a: li.a * k, b: li.b * k };
                        li.m -= o.m;
                        li.a -= o.a;
                        li.b -= o.b;
                        da += o.a;
                        db += o.b;
                        f.returned += o.m * fa;
                        f.decayed += o.m * fa;
                    } else if li.a > 0.0 || li.b > 0.0 || li.m != 0.0 {
                        da += li.a;
                        db += li.b;
                        f.returned += li.m * fa;
                        *li = Litter::default();
                    }
                }
                // a share of what rot frees stays in the humus; the humus comes free by warmth and wetness
                let (da, db) = (da * fa / ca, db * fa / ca);
                let free = 1.0 - (-p.humus * q10t * fill * dt).exp();
                let (ha, hb) = (*hum_a.at(c) * free, *hum_b.at(c) * free);
                *hum_a.at(c) += p.humify * da - ha;
                *hum_b.at(c) += p.humify * db - hb;
                *sa.at(c) += (1.0 - p.humify) * da + ha;
                *sb.at(c) += (1.0 - p.humify) * db + hb;
                // the water of the cell's one soil, by root; A and B by active root
                let d = (sat.at(t) - *vapor.at(c)).max(0.0);
                let ratio = (d / p.deficit_ref).clamp(0.2, 3.0);
                let avail_g = ground.at(c).max(0.0) * ca * (p.root_draw * rs / ca * dt).min(1.0);
                let avail_d = deep.at(c).max(0.0) * ca * (p.root_draw * rd / ca * dt).min(1.0);
                let (mut used_g, mut used_d) = (0.0, 0.0);
                let fo = (p.uptake * rt / ca * dt).min(1.0);
                let (oa, ob) = (*sa.at(c) * ca * fo, *sb.at(c) * ca * fo);
                let (mut ta_sum, mut tb_sum) = (0.0, 0.0);
                for x in &tmp {
                    let y: &mut Cohort = if x.tree { &mut trees.at(x.at).b } else { co.at(x.at) };
                    let pp_kg = x.pp * x.scale;
                    let need = pp_kg * p.wue * ratio * (1.0 + y.h / p.h_water);
                    let sg = if rs > 0.0 { avail_g * x.rs / rs } else { 0.0 };
                    let sdp = if rd > 0.0 { avail_d * x.rd / rd } else { 0.0 };
                    let supply = sg + sdp;
                    let (mut gpp, mut stress) = (x.pp, 1.0);
                    if need > 0.0 {
                        let used = need.min(supply);
                        gpp = x.pp * used / need;
                        stress = (supply / need).min(1.0);
                        if supply > 0.0 {
                            used_g += used * sg / supply;
                            used_d += used * sdp / supply;
                        }
                    }
                    if rt > 0.0 {
                        let cap = 50.0 * (y.mass() * x.scale + 0.01 * x.area);
                        let ta = (oa * x.ract / rt).min((cap - y.pa * x.scale).max(0.0));
                        let tb = (ob * x.ract / rt).min((cap - y.pb * x.scale).max(0.0));
                        y.pa += ta / x.scale;
                        y.pb += tb / x.scale;
                        ta_sum += ta;
                        tb_sum += tb;
                    }
                    if x.tree {
                        let tr = trees.at(x.at);
                        let (y, drop) = (&mut tr.b, &mut tr.drop);
                        grow(p, rates, &x.ph, x.genes, y, gpp, stress, t, q10t, true, stormy[c], 1.0, drop, &mut f);
                        // a tree with no leaf and no store has nothing to grow a leaf from: it is dead, and falls
                        if y.mass() < p.m_min || y.age >= y.lifespan(p) || y.o[LEAF].m + y.o[STORE].m < p.bare * y.mass() {
                            fallen.push(x.at as u32);
                        }
                    } else {
                        grow(p, rates, &x.ph, x.genes, y, gpp, stress, t, q10t, !x.snowed, stormy[c], fa, lit.at(x.slot), &mut f);
                        if y.mass() < p.m_min || y.age >= y.lifespan(p) {
                            let l = lit.at(x.slot);
                            for o in y.o {
                                l.add(o);
                            }
                            l.a += y.pa;
                            l.b += y.pb;
                            *y = Cohort::default();
                        } else if y.h >= h_thing && tree_at[x.slot] == NONE {
                            grown.push((x.slot, x.at % KF));
                        }
                    }
                }
                *ground.at(c) -= used_g / ca;
                *deep.at(c) -= used_d / ca;
                *vapor.at(c) += (used_g + used_d) / ca;
                *transp.at(c) += (used_g + used_d) / ca;
                f.transp += used_g + used_d;
                *sa.at(c) -= ta_sum / ca;
                *sb.at(c) -= tb_sum / ca;
            }
            (f, grown, fallen)
        });
        let (mut grown, mut fallen) = (Vec::new(), Vec::new());
        for (x, g, d) in parts {
            f.add(&x);
            grown.extend(g);
            fallen.extend(d);
        }
        (grown, fallen)
    }

    /// Lightning, and fire running from fine cell to fine cell over dry fuel the sun reaches: `fire_run` m (a draw
    /// about it) through dry, ample, sunlit fuel before the weather ends it, less far through damp, thin or shaded.
    #[allow(clippy::too_many_arguments)]
    fn fire(&mut self, p: &Params, ter: &Terrain, ground: &[f64], sa: &mut [f64], sb: &mut [f64], dt: f64, year: u32, f: &mut LFlux) {
        if self.soil.is_empty() {
            return;
        }
        let f2 = self.k * self.k;
        let strikes = self.rng.poisson(p.lightning * self.soil.len() as f64 * self.fa / 1e6 * dt);
        let fuel = |pl: &Plants, s: usize| pl.lit[s].m + (0..KF).map(|i| &pl.co[s * KF + i]).filter(|x| x.live() && x.h < 2.0).map(|x| x.o[LEAF].m).sum::<f64>();
        let dry = |pl: &Plants, s: usize| {
            let c = pl.lands[s / f2] as usize;
            if pl.snow[c] > 1.0 { 0.0 } else { (1.0 - (ground[c] / ter.cap[c]).min(1.0)) * (p.fire_shade + (1.0 - p.fire_shade) * pl.sun[s] as f64) }
        };
        let mut burned = Vec::new();
        for _ in 0..strikes {
            let s0 = self.soil[self.rng.below(self.soil.len())] as usize;
            if self.burning[s0] || self.rng.f64() > dry(self, s0) || fuel(self, s0) < p.fuel_min {
                continue;
            }
            f.fires += 1.0;
            let mut front = VecDeque::from([(s0, p.fire_run * -(1.0 - self.rng.f64()).ln())]);
            self.burning[s0] = true;
            while let Some((s, left)) = front.pop_front() {
                burned.push(s);
                let (i, j) = self.ij(s);
                for (di, dj) in [(1i64, 0i64), (-1, 0), (0, 1), (0, -1)] {
                    let (a, b) = (i as i64 + di, j as i64 + dj);
                    if a < 0 || b < 0 || a as usize >= self.nf || b as usize >= self.nf {
                        continue;
                    }
                    let Some(m) = self.slot(a as usize, b as usize) else { continue };
                    if !self.grows[m] || self.burning[m] {
                        continue;
                    }
                    let fu = fuel(self, m);
                    if fu < p.fuel_min {
                        continue;
                    }
                    let cost = self.fm / (dry(self, m) * fu / (fu + p.fuel_half)).max(1e-9);
                    if cost <= left {
                        self.burning[m] = true;
                        front.push_back((m, left - cost));
                    }
                }
            }
        }
        for &s in &burned {
            let c = self.lands[s / f2] as usize;
            let flame = p.flame * fuel(self, s);
            let l = std::mem::take(&mut self.lit[s]);
            let mut ash = Organ { m: l.m * self.fa, a: l.a * self.fa, b: l.b * self.fa };
            let fa = self.fa;
            let mut burn = |x: &mut Cohort, scale: f64| {
                if !x.live() {
                    return;
                }
                if x.h < flame {
                    for o in [LEAF, WOOD, SEED] {
                        let t = x.o[o].take(1.0);
                        ash.m += t.m * scale;
                        ash.a += t.a * scale;
                        ash.b += t.b * scale;
                    }
                    x.cmp = 0.0;
                    x.damage = 1.0;
                } else {
                    let t = x.o[LEAF].take(0.5);
                    x.cmp *= 0.5;
                    ash.m += t.m * scale;
                    ash.a += t.a * scale;
                    ash.b += t.b * scale;
                    x.damage += 0.5;
                }
            };
            for i in 0..KF {
                burn(&mut self.co[s * KF + i], fa);
            }
            if self.tree_at[s] != NONE {
                burn(&mut self.trees[self.tree_at[s] as usize].b, 1.0);
            }
            sa[c] += ash.a / self.ca;
            sb[c] += ash.b / self.ca;
            f.returned += ash.m;
            f.burnt += ash.m;
            f.burnt_cells += 1.0;
            self.burnt[c] += 1.0;
            self.burnt_year[s] = year.min(65535) as u16;
            self.burning[s] = false;
        }
    }

    /// Seeds leave their parents: some fall near, some go with the wind from their plant's height.
    fn seeds(&mut self, p: &Params, ter: &Terrain, wx: &Weather, season: f64, year: u32) {
        let f2 = self.k * self.k;
        let ball = |m: f64| p.fall_seed * (m / 1e-5).powf(1.0 / 6.0);
        for q in 0..self.soil.len() {
            let s = self.soil[q] as usize;
            let c = self.lands[s / f2] as usize;
            let (u, v) = wx.wind(p, ter.lat[c / self.n], season);
            for i in 0..KF {
                let x = self.co[s * KF + i];
                if !x.live() || x.o[SEED].m < 1e-12 {
                    continue;
                }
                let mut rest = self.co[s * KF + i].o[SEED].take(1.0);
                let (wing, seed_mass) = {
                    let ph = &self.gen[x.g as usize].as_ref().unwrap().base;
                    (ph.wing, ph.seed_mass)
                };
                let rg = self.mutant(p, x.g, year);
                let pw = wing / (wing + 0.1);
                let mut wind = rest.take(pw.clamp(0.0, 1.0));
                let fall = (1.0 / ball(seed_mass).powi(2) + wing / (p.fall_wing * p.fall_wing)).powf(-0.5);
                let secs = x.h / fall;
                for j in 0..3 {
                    let part = if j == 2 { std::mem::take(&mut wind) } else { wind.take(1.0 / (3 - j) as f64) };
                    let along = secs * -(1.0 - self.rng.f64()).ln();
                    let across = along * (self.rng.f64() - 0.5);
                    match self.land(s, along * u - across * v, along * v + across * u) {
                        Some(at) => self.deposit(at, rg, part),
                        None => self.lit[s].add(part),
                    }
                }
                // what falls near lands within about the stand's height of it: that share crosses each edge
                let near = (x.h / (PI * self.fm)).min(0.2);
                for (j, (dx, dy)) in [(1.0, 0.0), (-1.0, 0.0), (0.0, 1.0), (0.0, -1.0)].into_iter().enumerate() {
                    let part = rest.take((near / (1.0 - near * j as f64)).clamp(0.0, 1.0));
                    let (ci, cj) = self.ij(s);
                    let (a, b) = (ci as f64 + dx, cj as f64 + dy);
                    let at = if a < 0.0 || b < 0.0 || a >= self.nf as f64 || b >= self.nf as f64 { None } else { self.slot(a as usize, b as usize).filter(|&d| self.grows[d]) };
                    match at {
                        Some(at) => self.deposit(at, rg, part),
                        None => self.lit[s].add(part),
                    }
                }
                self.deposit(s, rg, rest);
            }
            let ti = self.tree_at[s];
            if ti == NONE {
                continue;
            }
            let t = self.trees[ti as usize];
            if t.b.o[SEED].m < 1e-9 {
                continue;
            }
            let mut rest = self.trees[ti as usize].b.o[SEED].take(1.0);
            let (wing, seed_mass) = {
                let ph = &self.gen[t.b.g as usize].as_ref().unwrap().base;
                (ph.wing, ph.seed_mass)
            };
            let rg = self.mutant(p, t.b.g, year);
            let pw = wing / (wing + 0.1);
            let fall = (1.0 / ball(seed_mass).powi(2) + wing / (p.fall_wing * p.fall_wing)).powf(-0.5);
            let secs = t.b.h / fall;
            // sixteen packets from points under its crown, the winged share of each carried by a gust of its own
            for j in 0..16 {
                let part = if j == 15 { std::mem::take(&mut rest) } else { rest.take(1.0 / (16 - j) as f64) };
                let (a, d) = (TAU * self.rng.f64(), t.r * self.rng.f64().sqrt());
                let (mut dx, mut dy) = (d * a.cos(), d * a.sin());
                if self.rng.f64() < pw {
                    let along = secs * -(1.0 - self.rng.f64()).ln();
                    let across = along * (self.rng.f64() - 0.5);
                    dx += along * u - across * v;
                    dy += along * v + across * u;
                }
                let k = 1.0 / self.fa;
                match self.land(s, dx, dy) {
                    Some(at) => self.deposit(at, rg, part.times(k)),
                    None => self.lit[s].add(part.times(k)),
                }
            }
        }
    }

    /// The genotype a release carries: with chance `p_mut` a mutant, as a whole (e104).
    fn mutant(&mut self, p: &Params, g: u32, year: u32) -> u32 {
        if self.rng.f64() >= p.p_mut {
            return g;
        }
        let genes = genome::mutate(&self.gen[g as usize].as_ref().unwrap().genes, &mut self.rng);
        self.gen.push(Some(Box::new(Genotype::new(genes, g, year, false))));
        (self.gen.len() - 1) as u32
    }

    fn deposit(&mut self, s: usize, g: u32, o: Organ) {
        if o.m <= 0.0 {
            return;
        }
        let slots = &mut self.bank[s * BANK..s * BANK + BANK];
        if let Some(e) = slots.iter_mut().find(|e| e.g == g) {
            e.m += o.m;
            e.a += o.a;
            e.b += o.b;
            return;
        }
        if let Some(e) = slots.iter_mut().find(|e| e.g == NONE) {
            *e = Seeds { g, m: o.m, a: o.a, b: o.b };
            return;
        }
        let (i, small) = slots.iter().enumerate().map(|(i, e)| (i, e.m)).fold((0, f64::MAX), |a, b| if b.1 < a.1 { b } else { a });
        if o.m > small {
            let old = slots[i];
            slots[i] = Seeds { g, m: o.m, a: o.a, b: o.b };
            self.lit[s].add(Organ { m: old.m, a: old.a, b: old.b });
        } else {
            self.lit[s].add(o);
        }
    }

    /// A free slot of a cell is taken by the bank's best (its seeds' number x their chance in this cell's shade and
    /// dryness); with no free slot, seedlings outweighing the weakest stand take its place.
    /// The bank ages by the time since the last release, here.
    fn establish(&mut self, p: &Params, ter: &Terrain, ground: &[f64], since: f64) {
        let f2 = self.k * self.k;
        let sd = 1.0 - (-p.seed_decay * since).exp();
        for q in 0..self.soil.len() {
            let s = self.soil[q] as usize;
            if (0..BANK).all(|j| self.bank[s * BANK + j].g == NONE) {
                continue;
            }
            for j in 0..BANK {
                let e = self.bank[s * BANK + j];
                if e.g != NONE {
                    let mut o = Organ { m: e.m, a: e.a, b: e.b };
                    self.lit[s].add(o.take(sd));
                    self.bank[s * BANK + j] = if o.m < 1e-12 {
                        self.lit[s].add(o);
                        Seeds::default()
                    } else {
                        Seeds { g: e.g, m: o.m, a: o.a, b: o.b }
                    };
                }
            }
            let c = self.lands[s / f2] as usize;
            let fill = (ground[c] / ter.cap[c]).min(1.0);
            loop {
                let free = (0..KF).find(|&i| !self.co[s * KF + i].live());
                let cov = (self.sun[s] as f64).max(1e-9);
                let mut cand = [(0usize, 0.0f64, 0.0f64); BANK]; // entry, score, survival
                let mut nc = 0;
                for j in 0..BANK {
                    let e = self.bank[s * BANK + j];
                    if e.g == NONE {
                        continue;
                    }
                    let ph = &self.gen[e.g as usize].as_ref().unwrap().base;
                    let reserve = ph.seed_mass * (1.0 - ph.wing - ph.float);
                    let need = p.m_need / cov * (1.0 + 2.0 * (1.0 - fill));
                    let surv = reserve / (reserve + need);
                    cand[nc] = (j, e.m / ph.seed_mass * surv, surv);
                    nc += 1;
                }
                if nc == 0 {
                    break;
                }
                let cand = &cand[..nc];
                let pick = match free {
                    Some(_) => {
                        let total: f64 = cand.iter().map(|x| x.1).sum();
                        let mut r = self.rng.f64() * total;
                        let mut k = nc - 1;
                        for (i, x) in cand.iter().enumerate() {
                            if r < x.1 {
                                k = i;
                                break;
                            }
                            r -= x.1;
                        }
                        cand[k]
                    }
                    None => *cand.iter().max_by(|a, b| (self.bank[s * BANK + a.0].m * a.2).partial_cmp(&(self.bank[s * BANK + b.0].m * b.2)).unwrap()).unwrap(),
                };
                let (j, surv) = (pick.0, pick.2);
                let e = self.bank[s * BANK + j];
                let slot = match free {
                    Some(i) => i,
                    None => {
                        let (i, small) = (0..KF).map(|i| (i, self.co[s * KF + i].mass())).fold((0, f64::MAX), |a, b| if b.1 < a.1 { b } else { a });
                        if e.m * surv <= small {
                            break;
                        }
                        let old = std::mem::take(&mut self.co[s * KF + i]);
                        for o in old.o {
                            self.lit[s].add(o);
                        }
                        self.lit[s].a += old.pa;
                        self.lit[s].b += old.pb;
                        i
                    }
                };
                self.bank[s * BANK + j] = Seeds::default();
                let mut o = Organ { m: e.m, a: e.a, b: e.b };
                let lost = o.take(1.0 - surv);
                self.lit[s].add(lost);
                let mut x = Cohort { g: e.g, ..Default::default() };
                let half = o.take(0.5);
                x.o[LEAF] = half;
                x.o[ROOT] = o;
                x.lpk = half.m;
                self.co[s * KF + slot] = x;
                if free.is_none() {
                    break;
                }
            }
        }
    }

    /// Genotypes nothing carries any more are dropped (their ids stay unique); how many live.
    pub fn collect(&mut self) -> usize {
        let mut live = vec![false; self.gen.len()];
        for x in &self.co {
            if x.g != NONE {
                live[x.g as usize] = true;
            }
        }
        for s in &self.bank {
            if s.g != NONE {
                live[s.g as usize] = true;
            }
        }
        for t in &self.trees {
            if t.slot != NONE {
                live[t.b.g as usize] = true;
            }
        }
        // the founders stay while they are sown
        for (i, (g, l)) in self.gen.iter_mut().zip(&live).enumerate() {
            if !l && i >= self.founders {
                *g = None;
            }
        }
        live.iter().filter(|&&l| l).count()
    }

    /// The living's matter (kg), A and B (g).
    pub fn totals(&self) -> (f64, f64, f64) {
        let (mut m, mut a, mut b) = (0.0, 0.0, 0.0);
        let fa = self.fa;
        for x in &self.co {
            if x.live() {
                for o in &x.o {
                    m += o.m * fa;
                    a += o.a * fa;
                    b += o.b * fa;
                }
                a += x.pa * fa;
                b += x.pb * fa;
            }
        }
        for l in &self.lit {
            m += l.m * fa;
            a += l.a * fa;
            b += l.b * fa;
        }
        for s in &self.bank {
            m += s.m * fa;
            a += s.a * fa;
            b += s.b * fa;
        }
        for t in &self.trees {
            if t.slot != NONE {
                for o in &t.b.o {
                    m += o.m;
                    a += o.a;
                    b += o.b;
                }
                a += t.b.pa + t.drop.a;
                b += t.b.pb + t.drop.b;
                m += t.drop.m;
            }
        }
        a += self.hum_a.iter().sum::<f64>() * self.ca;
        b += self.hum_b.iter().sum::<f64>() * self.ca;
        (m, a, b)
    }
}
