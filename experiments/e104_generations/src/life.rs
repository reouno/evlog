//! Rung 2 (#116, e103): producers as evolving cohorts, and the small eaters that live on their leaves.
//!
//! A cell holds up to K producer cohorts (a stand of one genotype: the mass and the A and B of each organ -
//! leaf, wood, root, store, seed - and nutrient pools), up to E eater cohorts, a litter and a seed bank.
//! Masses are kg of dry matter a m2, nutrients g a m2 (a mean rock gives 1 g of each a year, rung 1).
//!
//! Every life step (a day): light falls through the leaves by height, carbon is paid in water drawn from the
//! soil and (deep roots) the groundwater, roots take A and B, growth follows the organs' shares, tissue is
//! lost to turnover, shedding, frost, wilting and storms; eaters eat leaves by their quality and are harmed by
//! compounds whose key they do not carry; litter decays. Fire runs on the dry land. Every `seed_every` steps
//! seeds are released and carried (locally, by the wind band, down the rivers) into seed banks, and a free
//! slot is taken by the bank's best.

use crate::climate::{zonal, Sat};
use crate::genome::{self, hamming, Genotype, Pheno, SIGNALS};
use crate::noise::Rng;
use crate::terrain::{nbrs, Terrain, NONE};
use crate::Params;
use std::f64::consts::TAU;

pub const K: usize = 4; // producer cohorts a cell
pub const E: usize = 2; // eater cohorts a cell
pub const BANK: usize = 4; // genotypes in a cell's seed bank
const NCHUNK: usize = 64; // fixed work chunks, so that the sums do not depend on the threads
const STORE_SHARE: f64 = 0.001; // A and B a kg of store (sugar and starch)
const LEAF: usize = 0;
const WOOD: usize = 1;
const ROOT: usize = 2;
const STORE: usize = 3;
const SEED: usize = 4;

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
}

#[derive(Clone, Copy)]
pub struct Cohort {
    pub g: u32,
    pub o: [Organ; 5],
    pub cmp: f64, // kg of compound in the leaves
    pub pa: f64,
    pub pb: f64,
    pub lpk: f64,    // the leaf mass it has held lately (sets the wood a leaf needs)
    pub lite: f64,   // the share of the cell's light reaching its crown
    pub damage: f64, // leaf lost lately, not to turnover
    pub h: f64,      // m
    pub age: f64,    // years since it established (e104: a cohort is an age class)
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
    fn live(&self) -> bool {
        self.g != NONE
    }
}

#[derive(Clone, Copy)]
pub struct Eater {
    pub g: u32,
    pub m: f64,
}

impl Default for Eater {
    fn default() -> Self {
        Eater { g: NONE, m: 0.0 }
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

/// What crossed the edges of the living in a stretch of time.
#[derive(Default, Clone, Copy)]
pub struct LFlux {
    pub fixed: f64,    // kg made from the air (and sown)
    pub returned: f64, // kg back to the air: respired, unused, decayed, burnt
    pub gpp: f64,
    pub resp: f64,
    pub transp: f64, // mm
    pub eaten: f64,
    pub decayed: f64,
    pub burnt: f64,
    pub burnt_cells: f64,
}

impl LFlux {
    pub fn add(&mut self, o: &LFlux) {
        self.fixed += o.fixed;
        self.returned += o.returned;
        self.gpp += o.gpp;
        self.resp += o.resp;
        self.transp += o.transp;
        self.eaten += o.eaten;
        self.decayed += o.decayed;
        self.burnt += o.burnt;
        self.burnt_cells += o.burnt_cells;
    }
}

pub struct Life {
    n: usize,
    pub co: Vec<Cohort>,
    pub ea: Vec<Eater>,
    pub lit: Vec<Litter>,
    pub bank: Vec<Seeds>,
    pub cover: Vec<f64>, // the share of the sun reaching the soil
    pub gen: Vec<Option<Box<Genotype>>>,
    pub egen: Vec<Option<Box<Genotype>>>,
    light: Vec<f64>,
    temp: Vec<f64>,
    stormy: Vec<bool>,
    acc: usize,
    rng: Rng,
    steps: u64,
    land: Vec<u32>,
    burning: Vec<bool>,
    pub transp: Vec<f64>, // mm this year, per cell
    pub burnt: Vec<f64>,  // fires this year, per cell
    pub sown: bool,
    pub secs: [f64; 5], // time spent: accumulate, cells, fire, eaters, seeds (this year)
}

/// What a cell's step reads.
struct Ctx<'a> {
    p: &'a Params,
    ter: &'a Terrain,
    sat: &'a Sat,
    gen: &'a [Option<Box<Genotype>>],
    egen: &'a [Option<Box<Genotype>>],
    light: &'a [f64],
    temp: &'a [f64],
    stormy: &'a [bool],
    dt: f64,
    debug: usize, // a cell whose life is printed each step (EVLOG_DEBUG_CELL)
    season: f64,
    season_cos: f64,
}

/// A chunk of rows, every per-cell field of it.
struct Chunk<'a> {
    lo: usize,
    ground: &'a mut [f64],
    vapor: &'a mut [f64],
    deep: &'a mut [f64],
    sa: &'a mut [f64],
    sb: &'a mut [f64],
    cover: &'a mut [f64],
    lit: &'a mut [Litter],
    co: &'a mut [Cohort],
    ea: &'a mut [Eater],
    bank: &'a mut [Seeds],
    transp: &'a mut [f64],
}

fn q10(t: f64) -> f64 {
    2f64.powf((t.clamp(-30.0, 45.0) - 20.0) / 10.0)
}

fn activity(share: f64) -> f64 {
    share / (share + 0.01)
}

fn toughness(share: f64) -> f64 {
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

impl Life {
    pub fn new(ter: &Terrain, p: &Params) -> Self {
        let n = ter.n;
        let cells = n * n;
        Life {
            n,
            co: vec![Cohort::default(); cells * K],
            ea: vec![Eater::default(); cells * E],
            lit: vec![Litter::default(); cells],
            bank: vec![Seeds::default(); cells * BANK],
            cover: vec![1.0; cells],
            gen: Vec::new(),
            egen: Vec::new(),
            light: vec![0.0; cells],
            temp: vec![0.0; cells],
            stormy: vec![false; cells],
            acc: 0,
            rng: Rng::new(p.life as u64 ^ 0x11FE),
            steps: 0,
            land: (0..cells).filter(|&c| !ter.sea[c]).map(|c| c as u32).collect(),
            burning: vec![false; cells],
            transp: vec![0.0; cells],
            burnt: vec![0.0; cells],
            sown: false,
            secs: [0.0; 5],
        }
    }

    /// Every update: the light, heat and storms the next life step reads.
    pub fn accumulate(&mut self, light: &[f64], temp: &[f64], hit: &[bool]) {
        let t0 = std::time::Instant::now();
        for c in 0..self.light.len() {
            self.light[c] += light[c];
            self.temp[c] += temp[c];
            self.stormy[c] |= hit[c];
        }
        self.acc += 1;
        self.secs[0] += t0.elapsed().as_secs_f64();
    }

    pub fn due(&self, p: &Params) -> bool {
        self.acc >= p.life_every as usize
    }

    /// The first population: `founders` random genomes, two sown in every cell, and random eaters.
    pub fn sow(&mut self, p: &Params, sa: &mut [f64], sb: &mut [f64], year: u32) -> LFlux {
        let mut f = LFlux::default();
        for _ in 0..p.founders as usize {
            let g = genome::random(&mut self.rng, false);
            self.gen.push(Some(Box::new(Genotype::new(g, NONE, year, false))));
        }
        for _ in 0..(p.founders as usize / 4).max(1) {
            let g = genome::random(&mut self.rng, true);
            self.egen.push(Some(Box::new(Genotype::new(g, NONE, year, true))));
        }
        let cells = self.n * self.n;
        for c in 0..cells {
            for j in 0..2 {
                let g = self.rng.below(self.gen.len()) as u32;
                let ph = &self.gen[g as usize].as_ref().unwrap().base;
                let m = p.sow_mass;
                let a = (m * 1000.0 * ph.leaf_a).min(0.5 * sa[c]);
                let b = (m * 1000.0 * ph.leaf_b).min(0.5 * sb[c]);
                sa[c] -= a;
                sb[c] -= b;
                self.bank[c * BANK + j] = Seeds { g, m, a, b };
                f.fixed += m;
            }
            let g = self.rng.below(self.egen.len()) as u32;
            let m = (1e-4f64).min(0.5 * sa[c] / (1000.0 * p.eater_a)).min(0.5 * sb[c] / (1000.0 * p.eater_b));
            if m > 1e-9 {
                sa[c] -= m * 1000.0 * p.eater_a;
                sb[c] -= m * 1000.0 * p.eater_b;
                self.ea[c * E] = Eater { g, m };
                f.fixed += m;
            }
        }
        self.establish(p, &vec![1.0; cells]);
        self.sown = true;
        f
    }

    /// One life step, after `life_every` updates of the climate.
    #[allow(clippy::too_many_arguments)]
    pub fn step(&mut self, p: &Params, ter: &Terrain, sat: &Sat, ground: &mut [f64], vapor: &mut [f64], deep: &mut [f64], sa: &mut [f64], sb: &mut [f64], q: &[f64], step: f64) -> LFlux {
        let n = self.n;
        let cells = n * n;
        let k = self.acc as f64;
        let t0 = std::time::Instant::now();
        for c in 0..cells {
            self.light[c] /= k;
            self.temp[c] /= k;
        }
        let dt = p.life_every * p.tick / p.year;
        let phase = TAU * step / p.year;
        let ctx = Ctx {
            p,
            ter,
            sat,
            gen: &self.gen,
            egen: &self.egen,
            light: &self.light,
            temp: &self.temp,
            stormy: &self.stormy,
            dt,
            debug: std::env::var("EVLOG_DEBUG_CELL").ok().and_then(|v| v.parse().ok()).unwrap_or(usize::MAX),
            season: phase.sin(),
            season_cos: phase.cos(),
        };
        // The cells, in parallel over fixed chunks of rows.
        let per = cells / NCHUNK;
        let mut chunks: Vec<Chunk> = Vec::with_capacity(NCHUNK);
        {
            let mut it_g = ground.chunks_mut(per);
            let mut it_v = vapor.chunks_mut(per);
            let mut it_d = deep.chunks_mut(per);
            let mut it_a = sa.chunks_mut(per);
            let mut it_b = sb.chunks_mut(per);
            let mut it_c = self.cover.chunks_mut(per);
            let mut it_l = self.lit.chunks_mut(per);
            let mut it_o = self.co.chunks_mut(per * K);
            let mut it_e = self.ea.chunks_mut(per * E);
            let mut it_s = self.bank.chunks_mut(per * BANK);
            let mut it_t = self.transp.chunks_mut(per);
            for i in 0..NCHUNK {
                chunks.push(Chunk {
                    lo: i * per,
                    ground: it_g.next().unwrap(),
                    vapor: it_v.next().unwrap(),
                    deep: it_d.next().unwrap(),
                    sa: it_a.next().unwrap(),
                    sb: it_b.next().unwrap(),
                    cover: it_c.next().unwrap(),
                    lit: it_l.next().unwrap(),
                    co: it_o.next().unwrap(),
                    ea: it_e.next().unwrap(),
                    bank: it_s.next().unwrap(),
                    transp: it_t.next().unwrap(),
                });
            }
        }
        let threads = (p.threads as usize).max(1);
        let mut work: Vec<Vec<(usize, Chunk)>> = (0..threads).map(|_| Vec::new()).collect();
        for (i, ch) in chunks.into_iter().enumerate() {
            work[i % threads].push((i, ch));
        }
        let ctx = &ctx;
        let mut out: Vec<(usize, LFlux)> = std::thread::scope(|s| {
            let hs: Vec<_> = work
                .into_iter()
                .map(|list| {
                    s.spawn(move || {
                        list.into_iter()
                            .map(|(i, ch)| {
                                let mut f = LFlux::default();
                                chunk_step(ctx, ch, &mut f);
                                (i, f)
                            })
                            .collect::<Vec<_>>()
                    })
                })
                .collect();
            hs.into_iter().flat_map(|h| h.join().unwrap()).collect()
        });
        out.sort_by_key(|(i, _)| *i);
        let mut f = LFlux::default();
        for (_, o) in &out {
            f.add(o);
        }
        let decl = p.tilt.to_radians() * phase.sin();
        let t1 = std::time::Instant::now();
        self.secs[1] += (t1 - t0).as_secs_f64();
        self.fire(p, ter, ground, sa, sb, &mut f);
        let t2 = std::time::Instant::now();
        self.secs[2] += (t2 - t1).as_secs_f64();
        self.eaters_move(p, ter, decl);
        let t3 = std::time::Instant::now();
        self.secs[3] += (t3 - t2).as_secs_f64();
        self.steps += 1;
        if self.steps % (p.seed_every as u64) == 0 {
            self.seeds(p, ter, q, decl);
            let fill: Vec<f64> = (0..cells).map(|c| if ter.sea[c] { 1.0 } else { (ground[c] / ter.cap[c]).min(1.0) }).collect();
            self.establish(p, &fill);
        }
        self.secs[4] += t3.elapsed().as_secs_f64();
        for c in 0..cells {
            self.light[c] = 0.0;
            self.temp[c] = 0.0;
            self.stormy[c] = false;
        }
        self.acc = 0;
        f
    }

    /// Lightning, and fire spreading over dry land with fuel.
    fn fire(&mut self, p: &Params, ter: &Terrain, ground: &[f64], sa: &mut [f64], sb: &mut [f64], f: &mut LFlux) {
        let n = self.n;
        let dt = p.life_every * p.tick / p.year;
        let strikes = self.rng.poisson(p.lightning * self.land.len() as f64 * dt);
        let fuel = |life: &Life, c: usize| life.lit[c].m + (0..K).map(|i| &life.co[c * K + i]).filter(|x| x.live() && x.h < 2.0).map(|x| x.o[LEAF].m).sum::<f64>();
        let dry = |c: usize| 1.0 - (ground[c] / ter.cap[c]).min(1.0);
        let mut burned = Vec::new();
        for _ in 0..strikes {
            let c0 = self.land[self.rng.below(self.land.len())] as usize;
            if self.burning[c0] || self.rng.f64() > dry(c0) || fuel(self, c0) < p.fuel_min {
                continue;
            }
            let mut front = vec![c0];
            self.burning[c0] = true;
            while let Some(c) = front.pop() {
                burned.push(c);
                for m in nbrs(n, c) {
                    if ter.sea[m] || self.burning[m] {
                        continue;
                    }
                    let fu = fuel(self, m);
                    if fu < p.fuel_min {
                        continue;
                    }
                    if self.rng.f64() < p.fire_spread * dry(m) * fu / (fu + p.fuel_half) {
                        self.burning[m] = true;
                        front.push(m);
                    }
                }
            }
        }
        for &c in &burned {
            let fu = fuel(self, c);
            let flame = p.flame * fu;
            let l = std::mem::take(&mut self.lit[c]);
            let mut ash = Organ { m: l.m, a: l.a, b: l.b };
            for i in 0..K {
                let x = &mut self.co[c * K + i];
                if !x.live() {
                    continue;
                }
                if x.h < flame {
                    for o in [LEAF, WOOD, SEED] {
                        let t = x.o[o].take(1.0);
                        ash.m += t.m;
                        ash.a += t.a;
                        ash.b += t.b;
                    }
                    x.cmp = 0.0;
                    x.damage = 1.0;
                } else {
                    let t = x.o[LEAF].take(0.5);
                    x.cmp *= 0.5;
                    ash.m += t.m;
                    ash.a += t.a;
                    ash.b += t.b;
                    x.damage += 0.5;
                }
            }
            sa[c] += ash.a;
            sb[c] += ash.b;
            f.returned += ash.m;
            f.burnt += ash.m;
            f.burnt_cells += 1.0;
            self.burnt[c] += 1.0;
            self.burning[c] = false;
        }
    }

    /// Eaters spread on the wind; a share of what leaves may carry a mutation.
    fn eaters_move(&mut self, p: &Params, ter: &Terrain, decl: f64) {
        let n = self.n;
        let dt = p.life_every * p.tick / p.year;
        for c in 0..n * n {
            for j in 0..E {
                let e = self.ea[c * E + j];
                if e.g == NONE {
                    continue;
                }
                let wing = self.egen[e.g as usize].as_ref().unwrap().eater.as_ref().unwrap().wing;
                let out = e.m * (1.0 - (-p.eater_disp * wing * dt).exp());
                if out < 1e-9 {
                    continue;
                }
                self.ea[c * E + j].m -= out;
                let mut g = e.g;
                if self.rng.f64() < p.eater_mut {
                    let genes = genome::mutate(&self.egen[g as usize].as_ref().unwrap().genes, &mut self.rng);
                    let year = self.year(p);
                    self.egen.push(Some(Box::new(Genotype::new(genes, g, year, true))));
                    g = (self.egen.len() - 1) as u32;
                }
                let d = if self.rng.f64() < 0.5 {
                    nbrs(n, c)[self.rng.below(4)]
                } else {
                    let y = c / n;
                    let s = if zonal(p, ter.lat[y], decl) >= 0.0 { 1i64 } else { -1 };
                    let dx = s * (1 + self.rng.below(5) as i64);
                    y * n + ((c % n) as i64 + dx).rem_euclid(n as i64) as usize
                };
                self.eater_arrive(p, d, g, out);
            }
        }
    }

    fn eater_arrive(&mut self, p: &Params, c: usize, g: u32, m: f64) {
        let slots = &mut self.ea[c * E..c * E + E];
        if let Some(s) = slots.iter_mut().find(|s| s.g == g) {
            s.m += m;
            return;
        }
        if let Some(s) = slots.iter_mut().find(|s| s.g == NONE) {
            *s = Eater { g, m };
            return;
        }
        let (i, small) = slots.iter().enumerate().map(|(i, s)| (i, s.m)).fold((0, f64::MAX), |a, b| if b.1 < a.1 { b } else { a });
        let (dead_m, keep) = if m > small { (small, true) } else { (m, false) };
        if keep {
            slots[i] = Eater { g, m };
        }
        self.lit[c].add(Organ { m: dead_m, a: dead_m * 1000.0 * p.eater_a, b: dead_m * 1000.0 * p.eater_b });
    }

    fn year(&self, p: &Params) -> u32 {
        (self.steps as f64 * p.life_every * p.tick / p.year) as u32 + p.sow as u32
    }

    /// Seeds leave their parents: some stay, some go with the wind, some down the rivers.
    fn seeds(&mut self, p: &Params, ter: &Terrain, q: &[f64], decl: f64) {
        let n = self.n;
        let year = self.year(p);
        for c in 0..n * n {
            for i in 0..K {
                let x = self.co[c * K + i];
                if !x.live() || x.o[SEED].m < 1e-12 {
                    continue;
                }
                let s = self.co[c * K + i].o[SEED].take(1.0);
                let ph = self.gen[x.g as usize].as_ref().unwrap().base.clone();
                let mut rest = s;
                // e104: a release carries a mutant genome with chance `p_mut`, as a whole, and goes out as any other.
                let mut rg = x.g;
                if self.rng.f64() < p.p_mut {
                    let genes = genome::mutate(&self.gen[x.g as usize].as_ref().unwrap().genes, &mut self.rng);
                    self.gen.push(Some(Box::new(Genotype::new(genes, x.g, year, false))));
                    rg = (self.gen.len() - 1) as u32;
                }
                let pw = ph.wing / (ph.wing + 0.1);
                let pf = if !ter.sea[c] && q[c] >= p.river_q { ph.float / (ph.float + 0.1) } else { 0.0 };
                let mut wind = scale(&mut rest, pw);
                let flt = scale(&mut rest, pf);
                // the wind: three packets along the band's wind, spread across it
                let d = (1.0 + p.wind_seed * ph.wing * (1e-5 / ph.seed_mass).cbrt()).min(100.0);
                let y = c / n;
                let sgn = if zonal(p, ter.lat[y], decl) >= 0.0 { 1.0 } else { -1.0 };
                for j in 0..3 {
                    let part = if j == 2 { std::mem::take(&mut wind) } else { scale(&mut wind, 1.0 / (3 - j) as f64) };
                    let dx = sgn * d * (0.5 + self.rng.f64());
                    let dy = d * (self.rng.f64() - 0.5);
                    let tx = ((c % n) as i64 + dx.round() as i64).rem_euclid(n as i64) as usize;
                    let ty = (y as i64 + dy.round() as i64).rem_euclid(n as i64) as usize;
                    self.deposit(ty * n + tx, rg, part);
                }
                // the river: down the network, until the river drops it or the sea takes it
                if flt.m > 0.0 {
                    let steps = (p.float_seed * ph.float * -(1.0 - self.rng.f64()).ln()) as usize + 1;
                    let mut at = c;
                    for _ in 0..steps {
                        let d = ter.down[at];
                        if d == NONE {
                            break;
                        }
                        at = d as usize;
                        if ter.sea[at] {
                            break;
                        }
                    }
                    self.deposit(at, rg, flt);
                }
                // what falls near: most in the cell, some over its edges
                let nb = nbrs(n, c);
                for (j, &m) in nb.iter().enumerate() {
                    let part = scale(&mut rest, 0.075 / (1.0 - 0.075 * j as f64));
                    self.deposit(m, rg, part);
                }
                self.deposit(c, rg, rest);
            }
        }
    }

    fn deposit(&mut self, c: usize, g: u32, s: Organ) {
        if s.m <= 0.0 {
            return;
        }
        let slots = &mut self.bank[c * BANK..c * BANK + BANK];
        if let Some(e) = slots.iter_mut().find(|e| e.g == g) {
            e.m += s.m;
            e.a += s.a;
            e.b += s.b;
            return;
        }
        if let Some(e) = slots.iter_mut().find(|e| e.g == NONE) {
            *e = Seeds { g, m: s.m, a: s.a, b: s.b };
            return;
        }
        let (i, small) = slots.iter().enumerate().map(|(i, e)| (i, e.m)).fold((0, f64::MAX), |a, b| if b.1 < a.1 { b } else { a });
        if s.m > small {
            let old = slots[i];
            slots[i] = Seeds { g, m: s.m, a: s.a, b: s.b };
            self.lit[c].add(Organ { m: old.m, a: old.a, b: old.b });
        } else {
            self.lit[c].add(s);
        }
    }

    /// A free slot is taken by the bank's best (its seeds' number x their chance in this cell's shade and
    /// dryness); with no free slot, seedlings outweighing the weakest stand take its place.
    fn establish(&mut self, p: &Params, fill: &[f64]) {
        let n = self.n;
        for c in 0..n * n {
            loop {
                let free = (0..K).find(|&i| !self.co[c * K + i].live());
                let cov = self.cover[c].max(1e-9);
                // Each bank genotype: its seeds' number x their chance in this cell's shade and dryness.
                let mut cand = [(0usize, 0.0f64, 0.0f64); BANK]; // entry, score, survival
                let mut nc = 0;
                for j in 0..BANK {
                    let e = self.bank[c * BANK + j];
                    if e.g == NONE {
                        continue;
                    }
                    let ph = &self.gen[e.g as usize].as_ref().unwrap().base;
                    let reserve = ph.seed_mass * (1.0 - ph.wing - ph.float);
                    let need = p.m_need / cov * (1.0 + 2.0 * (1.0 - fill[c]));
                    let surv = reserve / (reserve + need);
                    cand[nc] = (j, e.m / ph.seed_mass * surv, surv);
                    nc += 1;
                }
                if nc == 0 {
                    break;
                }
                let cand = &cand[..nc];
                // e104: a free slot is won by lottery on the scores; a full cell by the heaviest seedlings.
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
                    None => *cand.iter().max_by(|a, b| (self.bank[c * BANK + a.0].m * a.2).partial_cmp(&(self.bank[c * BANK + b.0].m * b.2)).unwrap()).unwrap(),
                };
                let (j, surv) = (pick.0, pick.2);
                let e = self.bank[c * BANK + j];
                let slot = match free {
                    Some(i) => i,
                    None => {
                        let (i, small) = (0..K).map(|i| (i, self.co[c * K + i].mass())).fold((0, f64::MAX), |a, b| if b.1 < a.1 { b } else { a });
                        if e.m * surv <= small {
                            break;
                        }
                        let old = std::mem::take(&mut self.co[c * K + i]);
                        self.bury(c, &old);
                        i
                    }
                };
                self.bank[c * BANK + j] = Seeds::default();
                let mut s = Organ { m: e.m, a: e.a, b: e.b };
                let lost = scale(&mut s, 1.0 - surv);
                self.lit[c].add(lost);
                let mut x = Cohort { g: e.g, ..Default::default() };
                let half = scale(&mut s, 0.5);
                x.o[LEAF] = half;
                x.o[ROOT] = s;
                x.lpk = half.m;
                self.co[c * K + slot] = x;
                if free.is_none() {
                    break;
                }
            }
        }
    }

    fn bury(&mut self, c: usize, x: &Cohort) {
        if !x.live() {
            return;
        }
        for o in x.o {
            self.lit[c].add(o);
        }
        self.lit[c].a += x.pa;
        self.lit[c].b += x.pb;
    }

    /// Genotypes nothing carries any more are dropped (their ids stay unique).
    pub fn collect(&mut self) -> (usize, usize) {
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
        let mut elive = vec![false; self.egen.len()];
        for e in &self.ea {
            if e.g != NONE {
                elive[e.g as usize] = true;
            }
        }
        for (g, l) in self.gen.iter_mut().zip(&live) {
            if !l {
                *g = None;
            }
        }
        for (g, l) in self.egen.iter_mut().zip(&elive) {
            if !l {
                *g = None;
            }
        }
        (live.iter().filter(|&&l| l).count(), elive.iter().filter(|&&l| l).count())
    }

    /// The living's matter (kg), A and B (g).
    pub fn totals(&self, p: &Params) -> (f64, f64, f64) {
        let (mut m, mut a, mut b) = (0.0, 0.0, 0.0);
        for x in &self.co {
            if x.live() {
                for o in &x.o {
                    m += o.m;
                    a += o.a;
                    b += o.b;
                }
                a += x.pa;
                b += x.pb;
            }
        }
        for e in &self.ea {
            if e.g != NONE {
                m += e.m;
                a += e.m * 1000.0 * p.eater_a;
                b += e.m * 1000.0 * p.eater_b;
            }
        }
        for l in &self.lit {
            m += l.m;
            a += l.a;
            b += l.b;
        }
        for s in &self.bank {
            m += s.m;
            a += s.a;
            b += s.b;
        }
        (m, a, b)
    }
}

/// Split off a share of an organ-like packet.
fn scale(o: &mut Organ, f: f64) -> Organ {
    o.take(f.clamp(0.0, 1.0))
}

fn chunk_step(x: &Ctx, ch: Chunk, f: &mut LFlux) {
    let len = ch.ground.len();
    for j in 0..len {
        let c = ch.lo + j;
        cell(
            x,
            c,
            &mut ch.ground[j],
            &mut ch.vapor[j],
            &mut ch.deep[j],
            &mut ch.sa[j],
            &mut ch.sb[j],
            &mut ch.cover[j],
            &mut ch.lit[j],
            &mut ch.co[j * K..j * K + K],
            &mut ch.ea[j * E..j * E + E],
            &mut ch.bank[j * BANK..j * BANK + BANK],
            &mut ch.transp[j],
            f,
        );
    }
}

#[allow(clippy::too_many_arguments)]
fn cell(
    x: &Ctx,
    c: usize,
    ground: &mut f64,
    vapor: &mut f64,
    deep: &mut f64,
    sa: &mut f64,
    sb: &mut f64,
    cover: &mut f64,
    lit: &mut Litter,
    co: &mut [Cohort],
    ea: &mut [Eater],
    bank: &mut [Seeds],
    transp: &mut f64,
    f: &mut LFlux,
) {
    let p = x.p;
    let dt = x.dt;
    let sea = x.ter.sea[c];
    let n = x.ter.n;
    let q = x.light[c];
    let t = x.temp[c];
    let fill = if sea { 1.0 } else { (*ground / x.ter.cap[c]).min(1.0) };
    let q10t = q10(t);

    // The seed bank ages.
    let sd = 1.0 - (-p.seed_decay * dt).exp();
    for e in bank.iter_mut() {
        if e.g != NONE {
            let mut o = Organ { m: e.m, a: e.a, b: e.b };
            lit.add(o.take(sd));
            *e = if o.m < 1e-12 {
                lit.add(o);
                Seeds::default()
            } else {
                Seeds { g: e.g, m: o.m, a: o.a, b: o.b }
            };
        }
    }

    let ls = if x.ter.lat[c / n] >= 0.0 { 1.0 } else { -1.0 };
    let mut sig = [0.0; SIGNALS];
    sig[0] = 0.5 + 0.5 * x.season * ls;
    sig[1] = 0.5 + 0.5 * x.season_cos * ls;
    sig[2] = ((t + 20.0) / 60.0).clamp(0.0, 1.0);
    sig[3] = fill;

    // Phenotypes, heights, and the light through the leaves, tallest first.
    let mut ph: [Pheno; K] = Default::default();
    let mut ngenes = [0usize; K];
    let mut order = [0usize; K];
    let mut live = 0;
    for i in 0..K {
        let y = &mut co[i];
        if !y.live() {
            continue;
        }
        let gt = x.gen[y.g as usize].as_ref().unwrap();
        let mass = y.mass();
        sig[4] = y.lite;
        sig[5] = ((mass / 1e-4).max(1.0).ln() / (1e5f64).ln()).clamp(0.0, 1.0);
        sig[6] = if mass > 0.0 { y.o[STORE].m / mass } else { 0.0 };
        sig[7] = (10.0 * y.damage).min(1.0);
        ph[i] = gt.pheno(&sig);
        ngenes[i] = gt.genes.len();
        y.h = if sea { 0.0 } else { ph[i].height.min(p.h0 + y.o[WOOD].m / (p.sigma * y.lpk.max(1e-4))) };
        order[live] = i;
        live += 1;
    }
    order[..live].sort_by(|&a, &b| co[b].h.partial_cmp(&co[a].h).unwrap().then(a.cmp(&b)));
    let mut absb = [0.0; K];
    let mut above = 0.0;
    for &i in &order[..live] {
        let lai = p.sla * co[i].o[LEAF].m;
        co[i].lite = (-p.ext * above).exp();
        absb[i] = co[i].lite * (1.0 - (-p.ext * lai).exp());
        above += lai;
    }
    *cover = (-p.ext * above).exp();

    // Carbon, paid in water; nutrients by the roots.
    let mut pp = [0.0; K];
    let mut act = [0.0; K];
    for &i in &order[..live] {
        let y = &co[i];
        let bact = if y.o[LEAF].m > 1e-15 { ((y.o[LEAF].b - y.cmp * 1000.0 * p.b_comp).max(0.0)) / (y.o[LEAF].m * 1000.0) } else { 0.0 };
        act[i] = activity(bact);
        let w = ph[i].breadth;
        let ft = 10.0 / w * (-((t - ph[i].t_opt) / w).powi(2)).exp();
        pp[i] = p.gpp_max * (q / p.light_ref) * absb[i] * act[i] * ft * dt;
    }
    let mut stress = [1.0; K];
    let mut gpp = pp;
    if !sea && live > 0 {
        let d = (x.sat.at(t) - *vapor).max(0.0);
        let ratio = (d / p.deficit_ref).clamp(0.2, 3.0);
        let (mut rs, mut rd) = (0.0, 0.0);
        for &i in &order[..live] {
            rs += co[i].o[ROOT].m * (1.0 - ph[i].deep);
            rd += co[i].o[ROOT].m * ph[i].deep;
        }
        let avail_g = ground.max(0.0) * (p.root_draw * rs * dt).min(1.0);
        let avail_d = deep.max(0.0) * (p.root_draw * rd * dt).min(1.0);
        let (mut used_g, mut used_d) = (0.0, 0.0);
        for &i in &order[..live] {
            let need = pp[i] * p.wue * ratio * (1.0 + co[i].h / p.h_water);
            let r = co[i].o[ROOT].m;
            let sg = if rs > 0.0 { avail_g * r * (1.0 - ph[i].deep) / rs } else { 0.0 };
            let sdp = if rd > 0.0 { avail_d * r * ph[i].deep / rd } else { 0.0 };
            let supply = sg + sdp;
            if need > 0.0 {
                let used = need.min(supply);
                gpp[i] = pp[i] * used / need;
                stress[i] = (supply / need).min(1.0);
                if supply > 0.0 {
                    used_g += used * sg / supply;
                    used_d += used * sdp / supply;
                }
            }
        }
        *ground -= used_g;
        *deep -= used_d;
        *vapor += used_g + used_d;
        f.transp += used_g + used_d;
        *transp += used_g + used_d;
    }
    {
        let mut ract = [0.0; K];
        let mut rt = 0.0;
        for &i in &order[..live] {
            ract[i] = co[i].o[ROOT].m * activity(co[i].o[ROOT].share_b());
            rt += ract[i];
        }
        if rt > 0.0 {
            let fo = (p.uptake * rt * dt).min(1.0);
            let (oa, ob) = (*sa * fo, *sb * fo);
            for &i in &order[..live] {
                let y = &mut co[i];
                let cap = 50.0 * (y.mass() + 0.01);
                let ta = (oa * ract[i] / rt).min((cap - y.pa).max(0.0));
                let tb = (ob * ract[i] / rt).min((cap - y.pb).max(0.0));
                y.pa += ta;
                y.pb += tb;
                *sa -= ta;
                *sb -= tb;
            }
        }
    }

    // Respiration, growth, and what is lost.
    let stormy = x.stormy[c];
    for &i in &order[..live] {
        let y = &mut co[i];
        let sh = shares(&ph[i], ngenes[i], p);
        let bkg = (y.o[LEAF].b + y.o[WOOD].b + y.o[ROOT].b) / 1000.0;
        let resp = p.resp * q10t * bkg * dt;
        f.gpp += gpp[i];
        f.fixed += gpp[i];
        let net = gpp[i] - resp;
        // Leaves below half of what it held lately are rebuilt from the store (a spring, a regrowth).
        if y.o[LEAF].m < 0.5 * y.lpk && y.o[STORE].m > 0.0 {
            let from = y.o[STORE].m * (1.0 - (-p.flush * dt).exp());
            let s = y.o[STORE].take(from / y.o[STORE].m);
            y.pa += s.a;
            y.pb += s.b;
            // this mass is built into leaves below, as if fixed now: count it out and in again
            f.returned += s.m;
            f.fixed += s.m;
            let (la, lb) = sh[LEAF];
            let k = (1.0f64).min(y.pa / (s.m * 1000.0 * la).max(1e-30)).min(y.pb / (s.m * 1000.0 * lb).max(1e-30));
            let use_ = s.m * k;
            y.o[LEAF].m += use_;
            y.o[LEAF].a += use_ * 1000.0 * la;
            y.o[LEAF].b += use_ * 1000.0 * lb;
            y.cmp += use_ * ph[i].compound;
            y.pa -= use_ * 1000.0 * la;
            y.pb -= use_ * 1000.0 * lb;
            f.returned += s.m - use_;
        }
        if net >= 0.0 {
            let (mut ra, mut rb) = (0.0, 0.0);
            for o in 0..5 {
                ra += net * ph[i].alloc[o] * 1000.0 * sh[o].0;
                rb += net * ph[i].alloc[o] * 1000.0 * sh[o].1;
            }
            let k = 1.0f64.min(if ra > 0.0 { y.pa / ra } else { 1.0 }).min(if rb > 0.0 { y.pb / rb } else { 1.0 });
            let use_ = net * k;
            for o in 0..5 {
                let dm = use_ * ph[i].alloc[o];
                y.o[o].m += dm;
                y.o[o].a += dm * 1000.0 * sh[o].0;
                y.o[o].b += dm * 1000.0 * sh[o].1;
            }
            y.cmp += use_ * ph[i].alloc[LEAF] * ph[i].compound;
            y.pa = (y.pa - ra * k).max(0.0);
            y.pb = (y.pb - rb * k).max(0.0);
            f.returned += resp + (net - use_);
            f.resp += resp;
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
                f.returned += gpp[i] + from + paid;
                f.resp += gpp[i] + from + paid;
            } else {
                f.returned += resp;
                f.resp += resp;
            }
        }
        // Losses to the litter.
        let tl = toughness(y.o[LEAF].share_a());
        let tw = toughness(y.o[WOOD].share_a());
        let tr = toughness(y.o[ROOT].share_a());
        // The day's mean, not its minimum: e061's day swings ~30 C, so every summer night would freeze.
        let frost = if t < 0.0 { p.frost * (-t / 10.0) * (1.0 - tl) } else { 0.0 };
        let wilt = p.wilt * (1.0 - stress[i]) * (1.0 - tl);
        let mut fl = 1.0 - (-(p.leaf_turn * (1.0 - 0.8 * tl) + ph[i].shed + frost + wilt) * dt).exp();
        let mut fw = 1.0 - (-p.wood_turn * (1.0 - 0.8 * tw) * dt).exp();
        let fr = 1.0 - (-p.root_turn * (1.0 - 0.8 * tr) * dt).exp();
        let fs = 1.0 - (-p.store_turn * dt).exp();
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
        y.damage = y.damage * (-12.0 * dt).exp() + hurt;
        y.lpk = y.o[LEAF].m.max(y.lpk * (-dt).exp());
    }

    // The small eaters.
    for e in ea.iter_mut() {
        if e.g == NONE {
            continue;
        }
        let ep = x.egen[e.g as usize].as_ref().unwrap().eater.as_ref().unwrap();
        let fte = (-((t - ep.t_opt) / 10.0).powi(2)).exp();
        let nk = ep.keys.len() as f64;
        let mut w = [0.0; K];
        let mut tox = [0.0; K];
        let mut denom = p.eat_half;
        for &i in &order[..live] {
            let y = &co[i];
            if y.o[LEAF].m < 1e-12 {
                continue;
            }
            let d = y.cmp / y.o[LEAF].m;
            let nkeys = ph[i].n_keys;
            for kk in 0..nkeys {
                let best = ep.keys.iter().map(|&dk| hamming(ph[i].keys[kk], dk)).min().unwrap_or(8) as f64;
                tox[i] += d / nkeys as f64 * (best - ep.tolerance).max(0.0) / 8.0 / 0.01;
            }
            let palat = act[i] * (1.0 - toughness(y.o[LEAF].share_a()));
            w[i] = palat * (-3.0 * tox[i]).exp();
            denom += w[i] * y.o[LEAF].m;
        }
        let (mut im, mut ia, mut ib, mut harm) = (0.0, 0.0, 0.0, 0.0);
        for &i in &order[..live] {
            let y = &mut co[i];
            if w[i] <= 0.0 {
                continue;
            }
            let want = p.eat * e.m * fte * dt * w[i] * y.o[LEAF].m / denom;
            let k = (want / y.o[LEAF].m).min(0.5);
            let o = y.o[LEAF].take(k);
            y.cmp *= 1.0 - k;
            y.damage += k;
            im += o.m;
            ia += o.a;
            ib += o.b;
            harm += o.m * tox[i] * p.harm;
        }
        f.eaten += im;
        let eff = p.eat_eff * (1.0 - 0.15 * ep.tolerance) / (1.0 + 0.1 * nk);
        let grow = (eff * im).min(ib / (1000.0 * p.eater_b)).min(ia / (1000.0 * p.eater_a));
        e.m += grow;
        let waste = im - grow;
        lit.m += 0.5 * waste;
        lit.a += ia - grow * 1000.0 * p.eater_a;
        lit.b += ib - grow * 1000.0 * p.eater_b;
        f.returned += 0.5 * waste;
        // respiration and death
        let r = 1.0 - (-p.eater_resp * q10t * (1.0 + 0.1 * nk) * dt).exp();
        let cold = if t < 0.0 { p.eater_cold * (-t / 10.0) } else { 0.0 };
        let die = 1.0 - (-(p.eater_die + cold) * dt).exp();
        let resp = e.m * r;
        let dead = (e.m * die + harm).min(e.m - resp);
        f.returned += resp;
        lit.m += dead;
        lit.a += (resp + dead) * 1000.0 * p.eater_a;
        lit.b += (resp + dead) * 1000.0 * p.eater_b;
        e.m -= resp + dead;
        if e.m < 1e-9 {
            lit.m += e.m;
            lit.a += e.m * 1000.0 * p.eater_a;
            lit.b += e.m * 1000.0 * p.eater_b;
            *e = Eater::default();
        }
    }

    // Cohorts gone below a seedling's mass die, and those past their lifespan (e104).
    for y in co.iter_mut() {
        if !y.live() {
            continue;
        }
        y.age += dt;
        if y.mass() < p.m_min || y.age >= y.lifespan(p) {
            for o in y.o {
                lit.add(o);
            }
            lit.a += y.pa;
            lit.b += y.pb;
            *y = Cohort::default();
        }
    }

    if c == x.debug {
        eprintln!("cell {c} q {q:.3} t {t:.1} fill {fill:.2} ground {:.1} sa {:.3} sb {:.3} lit {:.5}", *ground, *sa, *sb, lit.m);
        for i in 0..K {
            let y = &co[i];
            if y.live() {
                eprintln!("  g {} leaf {:.2e} wood {:.2e} root {:.2e} store {:.2e} seed {:.2e} pa {:.2e} pb {:.2e} h {:.2} pp {:.2e} gpp {:.2e} act {:.2} stress {:.2} alloc {:?} topt {:.1} br {:.1} shed {:.2}",
                    y.g, y.o[0].m, y.o[1].m, y.o[2].m, y.o[3].m, y.o[4].m, y.pa, y.pb, y.h, pp[i], gpp[i], act[i], stress[i], ph[i].alloc.map(|v| (v * 100.0).round() / 100.0), ph[i].t_opt, ph[i].breadth, ph[i].shed);
            }
        }
    }
    // The litter decays by warmth, wetness and its own A:B.
    if lit.m > 1e-15 {
        let la = lit.a / (lit.m * 1000.0);
        let lb = lit.b / (lit.m * 1000.0);
        let qual = 2.0 * lb / (lb + 0.005) / (1.0 + la / 0.01);
        let k = 1.0 - (-p.decay * q10t * fill * qual * dt).exp();
        let o = Organ { m: lit.m * k, a: lit.a * k, b: lit.b * k };
        lit.m -= o.m;
        lit.a -= o.a;
        lit.b -= o.b;
        *sa += o.a;
        *sb += o.b;
        f.returned += o.m;
        f.decayed += o.m;
    } else if lit.a > 0.0 || lit.b > 0.0 || lit.m != 0.0 {
        *sa += lit.a;
        *sb += lit.b;
        f.returned += lit.m;
        *lit = Litter::default();
    }
}
