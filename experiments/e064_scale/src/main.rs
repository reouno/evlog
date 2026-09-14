//! e064: a body's scale of matter against the producers (#78, the second step of stage C).
//!
//! e063 with one number more, `scale` (s): every matter quantity of a body (the upkeep, the bite,
//! the work of moving, what a block is made of, the start energy, the threshold to breed, the fat
//! the flesh holds) times s. The body keeps them in its own units and s converts at the world's
//! edge (`body.rs`); the eye reads the food in the body's units (food / s), so s changes how many
//! bodies the world holds and not what a body sees. The question is the density: e063's bodies
//! (s = 1) were one per 360-530 land cells, too thin for bodies to meet.
//!
//! What follows is e063's description, unchanged but for the name of the run.
//!
//! e063: bodies on the stage-B world (#76, the first step of foundation stage C).
//!
//! e062's world as it passed stage B (a world of e061's climate with e062's producers and fire,
//! grown as e062 grew it) and e059's bodies with every law the season world kept (`body.rs`),
//! ported onto it with no new law about a body. The questions are the prototype's, #76's agreed
//! first step: what a step costs at 512 with bodies on it, how many bodies the world feeds and
//! whether it stands, and so whether stage C's runs need threads for the bodies or a window of
//! the world.
//!
//! What joins the two is the least the port needs, not a law under test:
//! - A body lives on land: a sub-cell of the sea is a wall. The water's two layers are the first
//!   of stage C's trade-offs, still to build.
//! - A gut takes from the grass standing on its world cell and from the dead lying there
//!   (`carrion`), in their proportions. Wood (its hardness against a bite is to be set), algae (in
//!   the water) and the plants' litter are not food yet.
//! - What a body spends (the upkeep its fat pays, the fat its flesh cannot hold, the work of its
//!   moves) goes to the soil of the world cell under it, as e019's did. Through the world's one
//!   air pool, which rains on the sea by the sea's share of the rain, it would drain the land:
//!   e062's smoke moved up to 1.2% of the land's matter a year, and the bodies spend about what
//!   the grass grows.
//! - The dead rot into their cell's soil at 1% a step (e017), on the producers' clock.
//! - The climate and the producers update every `tick` steps (e062); the bodies every step.
//!
//! The settled world (the climate's spin-up and e062's years of producers) is built once per
//! world and kept in `results/worlds/` (not committed), and every run of the bodies starts from it.
//!
//! Run: cargo run --release -p e064_scale -- <prefix> [key=value ...] [file.params ...]
//! `<prefix>_log.csv` is a row every 1,000 steps, `_agents.csv` every body every 10,000 steps (the
//! columns e060's census reads, with the tooth at birth, the kills apart from the dead eaten, the
//! path and the habitat), `_events.csv` and `_lineages.csv` e006's lineages, `_row.csv` the run's
//! parameters and its second half in one row.

mod body;
mod climate;
mod habitat;
mod plants;

use body::*;
use climate::{Sat, World};
use habitat::*;
use plants::Plants;
use std::collections::{HashMap, HashSet};
use std::f64::consts::TAU;
use std::io::Write;
use std::time::Instant;

const LOG_INTERVAL: u64 = 1_000;
const LINEAGE_INTERVAL: u64 = 1_000;
const AGENT_DUMP: u64 = 10_000;
const GROWN: u32 = 300; // e060: a body this old has a diet
const TOOTH: u8 = 2; // e060: a force of 2 behind a hard tip breaks a soft face of density 1
const WORLD_VERSION: u64 = 1; // the format of a settled world's file
const WORLDS: &str = "experiments/e063_bodies/results/worlds"; // e064 reads e063's settled worlds
const CAUSES: [&str; 3] = ["hunger", "broken", "wear"];

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
    grow_years = 10.0, "years of producers before the bodies come, at least (e062 judged its worlds after as many)";
    grow_steps = 200000.0, "steps of producers before the bodies come, at least";
    grass_rate = 0.006, "matter grass grows a step at full cover, the sun overhead, warm and wet";
    wood_rate = 0.0024, "the same for wood";
    algae_rate = 0.01, "the same for algae, in shallow water";
    ignite = 1e-6, "chance a strike hits a cell in an update (it catches if dry, warm and fuelled)";
    matter = 10.0, "matter a cell holds at the start, in its soil and its producers";
    // e063's bodies
    life = 1.0, "the seed of the bodies: the gene table, the genomes and every draw of their lives (the terrain's is seed)";
    steps = 100000.0, "steps of bodies (0: build the settled world and stop)";
    start = 0.0977, "bodies per land cell at the start (e006's 400 on 64x64)";
    // e064's scale
    scale = 1.0, "a body's scale of matter (#78): its upkeep, bite, moves, blocks, start energy, threshold and fat, in the world's matter";
}

/// The parameters of the bodies; every other one makes the settled world.
const BODY_KEYS: [&str; 4] = ["life", "steps", "start", "scale"];

/// What the viewer is told a cell holds (e062's units).
const VIEW_RELIEF: f64 = 64.0;
const VIEW_SEA: f64 = 3.0;
const TEMP_OFFSET: f64 = 50.0;

fn parse(args: &[String]) -> Params {
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
    for a in args {
        if a.contains('=') {
            apply(a, &mut p);
        } else {
            for line in std::fs::read_to_string(a).unwrap_or_else(|e| panic!("{a}: {e}")).lines() {
                apply(line, &mut p);
            }
        }
    }
    p
}

/// Updates per quarter and per year, and the update the producers start at.
fn clocks(p: &Params) -> (u64, u64, u64) {
    let per_quarter = ((p.year / p.tick / 4.0).round() as u64).max(1);
    let per_year = 4 * per_quarter;
    (per_quarter, per_year, (p.spinup as u64).div_ceil(per_year) * per_year)
}

fn world_hash(p: &Params) -> u64 {
    let mut h: u64 = 0xcbf29ce484222325 ^ WORLD_VERSION;
    for (name, v) in Params::NAMES.iter().zip(p.values()) {
        if !BODY_KEYS.contains(name) {
            for b in format!("{name}={v};").bytes() {
                h = (h ^ b as u64).wrapping_mul(0x100000001b3);
            }
        }
    }
    h
}

fn put(out: &mut Vec<u8>, v: &[f64]) {
    out.extend_from_slice(&(v.len() as u64).to_le_bytes());
    for x in v {
        out.extend_from_slice(&x.to_le_bytes());
    }
}

fn put_u32(out: &mut Vec<u8>, v: &[u32]) {
    out.extend_from_slice(&(v.len() as u64).to_le_bytes());
    for x in v {
        out.extend_from_slice(&x.to_le_bytes());
    }
}

struct Reader<'a> {
    b: &'a [u8],
    o: usize,
}

impl Reader<'_> {
    fn u64(&mut self) -> Option<u64> {
        let v = u64::from_le_bytes(self.b.get(self.o..self.o + 8)?.try_into().ok()?);
        self.o += 8;
        Some(v)
    }
    fn f64s(&mut self) -> Option<Vec<f64>> {
        let n = self.u64()? as usize;
        let s = self.b.get(self.o..self.o + 8 * n)?;
        self.o += 8 * n;
        Some(s.chunks_exact(8).map(|c| f64::from_le_bytes(c.try_into().unwrap())).collect())
    }
    fn u32s(&mut self) -> Option<Vec<u32>> {
        let n = self.u64()? as usize;
        let s = self.b.get(self.o..self.o + 4 * n)?;
        self.o += 4 * n;
        Some(s.chunks_exact(4).map(|c| u32::from_le_bytes(c.try_into().unwrap())).collect())
    }
}

/// A settled world in bytes: the climate's state, the producers' (their draws included) and the
/// update it stands at. Everything else is scratch or follows from the parameters.
fn world_bytes(hash: u64, update_i: u64, w: &World, pl: &Plants) -> Vec<u8> {
    let mut out = Vec::new();
    out.extend_from_slice(b"E063WRLD");
    out.extend_from_slice(&hash.to_le_bytes());
    out.extend_from_slice(&update_i.to_le_bytes());
    for v in [&w.temp, &w.vapor, &w.ground, &w.light, &w.rain_now, &pl.grass, &pl.wood, &pl.algae, &pl.litter, &pl.soil, &pl.carrion] {
        put(&mut out, v);
    }
    put_u32(&mut out, &pl.burnt_in);
    put_u32(&mut out, &pl.fire_sizes);
    let front: Vec<u32> = pl.front.iter().flat_map(|&(c, id)| [c, id]).collect();
    put_u32(&mut out, &front);
    out.extend_from_slice(&pl.air.to_le_bytes());
    out.extend_from_slice(&pl.rng.0.to_le_bytes());
    out
}

fn world_from(bytes: &[u8], hash: u64, p: &Params) -> Option<(World, Plants, u64)> {
    if bytes.get(..8)? != b"E063WRLD" {
        return None;
    }
    let mut r = Reader { b: bytes, o: 8 };
    if r.u64()? != hash {
        return None;
    }
    let update_i = r.u64()?;
    let mut w = World::new(p);
    let mut pl = Plants::new(&w, p);
    w.temp = r.f64s()?;
    w.vapor = r.f64s()?;
    w.ground = r.f64s()?;
    w.light = r.f64s()?;
    w.rain_now = r.f64s()?;
    pl.grass = r.f64s()?;
    pl.wood = r.f64s()?;
    pl.algae = r.f64s()?;
    pl.litter = r.f64s()?;
    pl.soil = r.f64s()?;
    pl.carrion = r.f64s()?;
    pl.burnt_in = r.u32s()?;
    pl.fire_sizes = r.u32s()?;
    pl.front = r.u32s()?.chunks_exact(2).map(|c| (c[0], c[1])).collect();
    pl.air = f64::from_bits(r.u64()?);
    pl.rng.0 = r.u64()?;
    Some((w, pl, update_i))
}

/// The world the bodies come to: e061's climate spun up, then e062's producers grown as e062 grew
/// them (at least `grow_years` and `grow_steps`), so that it is the world e062 judged at its end.
/// Kept in `dir` once built (None: always built).
fn settled_world(p: &Params, dir: Option<&str>) -> (World, Plants, u64) {
    let hash = world_hash(p);
    let path = dir.map(|d| format!("{d}/c{}_{hash:016x}.bin", p.seed));
    if let Some(path) = &path {
        if let Some(world) = std::fs::read(path).ok().and_then(|b| world_from(&b, hash, p)) {
            eprintln!("settled world read from {path}");
            return world;
        }
    }
    let started = Instant::now();
    let sat = Sat::new();
    let mut w = World::new(p);
    let (_, per_year, plant_start) = clocks(p);
    let mut update_i = 0u64;
    while update_i < plant_start {
        w.update(p, &sat, update_i as f64 * p.tick);
        update_i += 1;
    }
    let mut pl = Plants::new(&w, p);
    let years = (p.grow_years.max(1.0) as u64).max(((p.grow_steps / p.tick).ceil() as u64).div_ceil(per_year));
    for yr in 1..=years {
        for _ in 0..per_year {
            w.update(p, &sat, update_i as f64 * p.tick);
            pl.update(&w, p, yr as u32);
            update_i += 1;
        }
    }
    let cells = (w.n * w.n) as f64;
    eprintln!(
        "settled world built in {:.1} s: grass/wood/algae {:.2}/{:.2}/{:.2} a cell after {years} years",
        started.elapsed().as_secs_f64(),
        pl.grass.iter().sum::<f64>() / cells,
        pl.wood.iter().sum::<f64>() / cells,
        pl.algae.iter().sum::<f64>() / cells
    );
    if let (Some(path), Some(dir)) = (&path, dir) {
        std::fs::create_dir_all(dir).ok();
        let tmp = format!("{path}.tmp{}", std::process::id());
        std::fs::write(&tmp, world_bytes(hash, update_i, &w, &pl)).unwrap();
        std::fs::rename(&tmp, path).unwrap();
    }
    (w, pl, update_i)
}

/// What a log interval adds up.
#[derive(Default)]
struct Tally {
    births: u64,
    children: u64,
    sexual: u64,
    no_room: u64,
    empty: u64, // children whose genome built no block
    hunger: u64,
    wear: u64,
    cc: Counters,
    plant: f64,
    scavenged: f64,
    actions: [u64; N_OUT],
    tried: u64,
    blocked: u64,
    stalled: u64,
    shoves: u64,
    moved: u64,
    sense_n: u64,
    sense_used: u64,
    worn: u64,
    death_ages: Vec<u32>,
    fat_spent: f64,
    fat_over: f64,
    upkept: u64,
    short: u64,
    spent: f64,
    grass_grown: f64, // e064: in the world's matter
    burnt: u64,
    develops: u64,
    body_steps: u64,
    turned: u64,
    t_world: f64,
    t_bodies: f64,
    t_lineage: f64,
}

/// One log row's numbers, kept for the run's summary.
struct Point {
    step: u64,
    pop: usize,
    plant: f64,
    kills: f64,
    scavenged: f64,
    ms: [f64; 4], // a step, the world, the bodies, the lineages
    err: f64,
}

struct Sim {
    p: Params,
    sat: Sat,
    w: World,
    pl: Plants,
    g: Grid,
    occ: Occ,
    agents: Vec<Agent>,
    laws: Laws,
    rng: Rng,
    wear_rng: Rng,
    cache: HashMap<Vec<u16>, Body>, // bodies by gene list, for the gene lists alive
    threads: usize,
    update_i: u64,
    per_quarter: u64,
    per_year: u64,
    plant_start: u64,
    q: Quarter,
    hab: Vec<u8>, // the habitat of every cell in the last quarter (e061)
    land: usize,
    next_id: u64,
    step: u64,
    k: Tally,
    next_lineage: u32,
    seen: HashMap<u32, u32>,
    origin: HashMap<u32, u32>,
    lineages: HashMap<u32, usize>,
    born: Vec<(u32, u32)>, // since the viewer last took them
    dead: Vec<(u32, u8)>,
}

impl Sim {
    fn new(p: Params, w: World, pl: Plants, update_i: u64, threads: usize) -> Sim {
        let n = w.n;
        let g = Grid::new(n, n);
        let (per_quarter, per_year, plant_start) = clocks(&p);
        let life = p.life as u64;
        let mut rng = Rng(life.wrapping_mul(0x9E3779B97F4A7C15) | 1);
        let laws = Laws::new(&mut rng, life);
        let wear_rng = Rng(life.wrapping_mul(0xE7037ED1A0B428DB).wrapping_add(0xA0761D6478BD642F) | 1);
        let occ = Occ::new(g, &w.sea);
        let land = w.sea.iter().filter(|&&s| !s).count();
        let mut q = Quarter::new(n * n);
        q.add(&w, &pl, p.soil);
        let hab = q.habitats(&w);
        q.clear();
        let mut sim = Sim {
            p, sat: Sat::new(), w, pl, g, occ, agents: Vec::new(), laws, rng, wear_rng, cache: HashMap::new(), threads, update_i, per_quarter, per_year, plant_start, q, hab, land,
            next_id: 0, step: 0, k: Tally::default(), next_lineage: 1, seen: HashMap::new(), origin: HashMap::new(), lineages: HashMap::new(), born: Vec::new(), dead: Vec::new(),
        };
        sim.populate();
        sim
    }

    /// Random genomes on random free land, `start` per land cell; a body that finds no room in
    /// eight tries is not made.
    fn populate(&mut self) {
        let g = self.g;
        let init = (self.p.start * self.land as f64).round() as usize;
        for _ in 0..init {
            let genome: Vec<u8> = (0..N).map(|_| self.rng.below(4) as u8).collect();
            let genes = parse_genes(&genome);
            let body = develop_genes(&genes, &self.laws);
            self.next_id += 1;
            let facing = self.rng.below(4) as u8;
            let mut a = Agent::new(self.next_id - 1, genome, sorted_keys(&genes), genes.iter().map(Gene::key).collect(), body, facing, INIT_ENERGY as f64, 0);
            if !a.alive {
                continue;
            }
            for _ in 0..8 {
                a.x = self.rng.below(g.sw);
                a.y = self.rng.below(g.sh);
                if a.fits(g, &self.occ.sub, FREE, NORTH, 0) {
                    a.born_at = (a.x, a.y);
                    a.born_hab = self.hab[a.here(g)];
                    self.occ.claim(g, &a, self.agents.len() as u32);
                    self.agents.push(a);
                    break;
                }
            }
        }
        self.cache = self.agents.iter().map(|a| (a.gene_ids.clone(), a.body.clone())).collect();
    }

    /// All the matter of the world: in the cells, the air, and the bodies (their energy, their fat
    /// and what their blocks are made of).
    fn matter(&self) -> f64 {
        self.pl.matter() + self.agents.iter().map(|a| a.energy.max(0.0) + a.fat + a.body.matter()).sum::<f64>() * self.p.scale
    }

    fn step(&mut self) {
        self.step += 1;
        if (self.step - 1) % self.p.tick as u64 == 0 {
            let t = Instant::now();
            self.world();
            self.k.t_world += t.elapsed().as_secs_f64();
        }
        let t = Instant::now();
        self.bodies();
        self.k.t_bodies += t.elapsed().as_secs_f64();
    }

    /// One update of the climate and the producers (e061, e062), and the habitats each quarter.
    fn world(&mut self) {
        self.w.update(&self.p, &self.sat, self.update_i as f64 * self.p.tick);
        let yr = ((self.update_i - self.plant_start) / self.per_year + 1) as u32;
        let f = self.pl.update(&self.w, &self.p, yr);
        self.k.burnt += f.caught as u64;
        self.k.grass_grown += f.grass;
        self.q.add(&self.w, &self.pl, self.p.soil);
        self.update_i += 1;
        if (self.update_i - self.plant_start) % self.per_quarter == 0 {
            self.hab = self.q.habitats(&self.w);
            self.q.clear();
        }
    }

    /// One step of every body: eat and pay, decide, act, breed; then the children are developed
    /// and placed, and the dead lie down.
    fn bodies(&mut self) {
        let Sim { p, agents, pl, occ, g, rng, wear_rng, k, hab, laws, cache, threads, next_id, born, dead, .. } = self;
        let g = *g;
        let s = p.scale; // a body's matter in the world's (e064)
        let mut newborn: Vec<Agent> = Vec::new();
        let mut pending: Vec<(Agent, Option<Vec<Gene>>, usize)> = Vec::new();
        for i in 0..agents.len() {
            if !agents[i].alive {
                continue;
            }
            // The body's clock (e052, e055): between its turns nothing it does happens.
            let a = &mut agents[i];
            a.age += 1;
            k.body_steps += 1;
            a.phase += pace(a.body.mass);
            if a.phase < 1.0 {
                continue;
            }
            a.phase -= 1.0;
            a.turns += 1;
            k.turned += 1;
            k.worn += wear_blocks(a, wear_chance(a.turns), wear_rng, g, occ, &mut pl.carrion, s, &mut k.cc) as u64;
            if !a.alive {
                continue;
            }

            // 1. Eat: every gut block takes from the world cell under it. Then the upkeep: paid
            //    from the energy and the food, fixed in the flesh as fat (at most STORE per unit
            //    of mass), and what the energy cannot pay the fat pays (e024, e030, e042).
            let mut guts = CellsUnder::default();
            let mut gut_n = [0u8; UNDER_MAX];
            for p in a.cells_held() {
                if a.wcells[p] == DIGESTIVE as u8 {
                    let (sx, sy) = a.sub_at(g, p, NORTH, 0);
                    let c = g.wcell(sx, sy);
                    guts.add(c);
                    gut_n[guts.c[..guts.n].iter().position(|&x| x == c).unwrap()] += 1;
                }
            }
            let (mut plant, mut scavenged) = (0.0f64, 0.0f64);
            for (j, c) in guts.iter().enumerate() {
                let (pg, dg) = pl.take(c, (BITE * gut_n[j] as f32) as f64 * s);
                plant += pg / s;
                scavenged += dg / s;
            }
            let eaten = plant + scavenged;
            let full = (UPKEEP * a.body.size as f32 + UPKEEP_BODY) as f64;
            let from_energy = full.min((a.energy + eaten).max(0.0));
            let gap = full - from_energy;
            let from_fat = gap.min(a.fat);
            a.short = from_fat < gap;
            a.fat += from_energy - from_fat;
            let over = (a.fat - (STORE * a.body.mass) as f64).max(0.0);
            a.fat -= over;
            a.energy += eaten - from_energy;
            a.plant += plant as f32;
            a.scavenged += scavenged as f32;
            pl.soil[a.here(g)] += (from_fat + over) * s;
            k.upkept += 1;
            k.short += a.short as u64;
            k.fat_spent += from_fat;
            k.fat_over += over;
            k.spent += from_fat + over;
            k.plant += plant;
            k.scavenged += scavenged;

            // 2. Decide (e023): food under the body; food and bodies ahead, behind, left and
            //    right as far as the eye's range, what lies j cells away at 1/j; energy. The
            //    knockout sees one cell (e009).
            let a = &agents[i];
            let range = a.body.range();
            let f = a.facing as usize;
            let dirs = [f, opposite(f), left_of(f), opposite(left_of(f))];
            let food = |c: usize| (pl.grass[c] + pl.carrion[c]) / s; // in the body's units (e064)
            let mut input = [0.0f32; N_IN];
            input[0] = a.under(g, NORTH, 0).iter().map(|c| food(c) as f32).sum();
            let mut blind = input;
            for (j, &d) in dirs.iter().enumerate() {
                let (f1, o1) = look(a, g, d, 1, &food, &occ.crowd);
                blind[1 + j] = f1;
                blind[5 + j] = o1;
                input[1 + j] = f1;
                input[5 + j] = o1;
                for r in 2..=range {
                    let (fr, ob) = look(a, g, d, r, &food, &occ.crowd);
                    input[1 + j] += fr / r as f32;
                    input[5 + j] += ob / r as f32;
                }
            }
            input[9] = (a.energy / a.body.threshold() as f64) as f32;
            blind[9] = input[9];
            let action = act(&a.body.policy, &input);
            k.actions[action] += 1;
            if a.body.kinds[SENSOR] > 0 {
                k.sense_n += 1;
                k.sense_used += (act(&a.body.policy, &blind) != action) as u64;
            }

            // 3. Act. Forward: press on whatever is in the way (e010), shove a body lighter than
            //    the force (e015), then step one sub-cell with chance speed and a second with
            //    chance speed (e048), paying the mass moved times the distance. Turn: with room
            //    and chance speed.
            if action == 1 {
                k.tried += 1;
                let d = f;
                let pressed = push(agents, i, d, g, occ, &mut pl.carrion, s, &mut k.cc);
                if agents[i].alive {
                    let mut work = 0.0f32;
                    for &(j, force) in &pressed {
                        if !agents[j].alive || agents[i].fits(g, &occ.sub, i as u32, d, 1) || force as f32 <= agents[j].body.mass {
                            continue;
                        }
                        if agents[j].fits(g, &occ.sub, j as u32, d, 1) {
                            occ.release(g, &agents[j]);
                            let (nx, ny) = g.sstep(agents[j].x, agents[j].y, d, 1);
                            agents[j].x = nx;
                            agents[j].y = ny;
                            occ.claim(g, &agents[j], j as u32);
                            k.shoves += 1;
                            work += agents[j].body.mass;
                        }
                    }
                    let mut moved = 0u32;
                    if agents[i].fits(g, &occ.sub, i as u32, d, 1) {
                        if stroke(agents[i].body.speed(), rng) {
                            occ.release(g, &agents[i]);
                            let (nx, ny) = g.sstep(agents[i].x, agents[i].y, d, 1);
                            agents[i].x = nx;
                            agents[i].y = ny;
                            moved = 1;
                            if rng.f32() < agents[i].body.speed() && agents[i].fits(g, &occ.sub, i as u32, d, 1) {
                                let (nx, ny) = g.sstep(nx, ny, d, 1);
                                agents[i].x = nx;
                                agents[i].y = ny;
                                moved = 2;
                            }
                            occ.claim(g, &agents[i], i as u32);
                        } else {
                            k.stalled += 1;
                        }
                    } else {
                        k.blocked += 1;
                    }
                    k.moved += moved as u64;
                    let a = &mut agents[i];
                    a.path += moved;
                    work += a.body.mass * moved as f32;
                    let cost = (MOVE_COST * work) as f64;
                    let paid = cost.min(a.energy.max(0.0));
                    let rest = cost - paid;
                    let from_fat = rest.min(a.fat);
                    if from_fat < rest {
                        a.short = true;
                    }
                    a.energy -= paid;
                    a.fat -= from_fat;
                    k.fat_spent += from_fat;
                    k.spent += paid + from_fat;
                    pl.soil[a.here(g)] += (paid + from_fat) * s;
                }
            } else if action >= 2 {
                let nf = if action == 2 { left_of(f) } else { opposite(left_of(f)) };
                let a = &agents[i];
                let (list, n, _) = filled(&rotate(&a.body.cells, nf, a.body.s()), a.body.s());
                let room = list[..n as usize].iter().all(|&p| {
                    let (sx, sy) = a.sub_at(g, p as usize, NORTH, 0);
                    let o = occ.sub[g.sidx(sx, sy)];
                    o == FREE || o == i as u32
                });
                if room && stroke(agents[i].body.speed(), rng) {
                    occ.release(g, &agents[i]);
                    agents[i].facing = nf as u8;
                    agents[i].reframe();
                    occ.claim(g, &agents[i], i as u32);
                }
            }
            if !agents[i].alive {
                continue;
            }

            // 4. Breed at the threshold: half the energy goes to the child; a mate within D genes
            //    among the bodies within two sub-cells of the box gives a one-point crossover.
            if agents[i].energy >= agents[i].body.threshold() as f64 {
                let mut mate = None;
                {
                    let a = &agents[i];
                    let [r0, r1, c0, c1] = a.bbox;
                    let (x0, y0) = (a.x + g.sw + c0 as usize - 2, a.y + g.sh + r0 as usize - 2);
                    'cells: for dy in 0..(r1 - r0 + 5) as usize {
                        for dx in 0..(c1 - c0 + 5) as usize {
                            let j = occ.sub[g.sidx((x0 + dx) % g.sw, (y0 + dy) % g.sh)];
                            if j == FREE || j == WALL || j as usize == i {
                                continue;
                            }
                            let m = &agents[j as usize];
                            if m.alive && a.distance(m) <= D {
                                mate = Some(j as usize);
                                break 'cells;
                            }
                        }
                    }
                }
                let mut genome = agents[i].genome.clone();
                if let Some(j) = mate {
                    let cut = rng.below(N);
                    genome[cut..].copy_from_slice(&agents[j].genome[cut..]);
                    k.sexual += 1;
                }
                let a = &mut agents[i];
                a.energy *= 0.5;
                for base in genome.iter_mut() {
                    if rng.f32() < MUTATION {
                        *base = (*base + 1 + rng.below(3) as u8) % 4;
                    }
                }
                k.children += 1;
                let genes = parse_genes(&genome);
                let gene_ids: Vec<u16> = genes.iter().map(Gene::key).collect();
                let body = cache.get(&gene_ids).cloned();
                *next_id += 1;
                let keys = sorted_keys(&genes);
                let todo = body.is_none().then_some(genes);
                let mut child = Agent::new(*next_id - 1, genome, keys, gene_ids, body.unwrap_or_else(Body::empty), rng.below(4) as u8, a.energy, a.lineage);
                child.x = a.x;
                child.y = a.y;
                pending.push((child, todo, i));
            }
        }

        // The children with a new gene list are developed, one development per list, on the threads.
        let mut jobs: Vec<(&[u16], &[Gene])> = Vec::new();
        for (a, genes, _) in &pending {
            if let Some(gs) = genes {
                if !jobs.iter().any(|(ids, _)| *ids == a.gene_ids.as_slice()) {
                    jobs.push((&a.gene_ids, gs));
                }
            }
        }
        k.develops += jobs.len() as u64;
        let n_threads = (*threads).min(jobs.len() / 2);
        let laws: &Laws = laws;
        let developed: Vec<Body> = if n_threads < 2 {
            jobs.iter().map(|(_, gs)| develop_genes(gs, laws)).collect()
        } else {
            let chunk = jobs.len().div_ceil(n_threads);
            std::thread::scope(|sc| {
                let hs: Vec<_> = jobs.chunks(chunk).map(|c| sc.spawn(move || c.iter().map(|(_, gs)| develop_genes(gs, laws)).collect::<Vec<Body>>())).collect();
                hs.into_iter().flat_map(|h| h.join().unwrap()).collect()
            })
        };
        for ((ids, _), b) in jobs.iter().zip(developed) {
            cache.insert(ids.to_vec(), b);
        }

        // Each child is placed at the first anchor with room, one to a grid's side of sub-cells
        // from the parent's anchor in the four directions, and the parent pays the matter of its
        // body. Without room or matter the child is never made and what it was given lies down.
        for (mut a, genes, parent) in pending.drain(..) {
            if genes.is_some() {
                a.set_body(cache[&a.gene_ids].clone());
            }
            if !a.alive {
                k.empty += 1;
                newborn.push(a);
                continue;
            }
            let (px, py) = (agents[parent].x, agents[parent].y);
            let reach = agents[parent].body.s().max(a.body.s());
            let start = rng.below(4);
            let mut spot = None;
            'search: for t in 0..4 {
                let d = DIRS[(start + t) % 4];
                for kk in 1..=reach {
                    let (cx, cy) = g.sstep(px, py, d, kk);
                    a.x = cx;
                    a.y = cy;
                    if a.fits(g, &occ.sub, FREE, NORTH, 0) {
                        spot = Some((cx, cy));
                        break 'search;
                    }
                }
            }
            let afford = agents[parent].energy >= a.body.matter();
            match spot {
                Some((cx, cy)) if afford => {
                    a.x = cx;
                    a.y = cy;
                    a.born_at = (cx, cy);
                    a.born_hab = hab[a.here(g)];
                    occ.claim(g, &a, (agents.len() + newborn.len()) as u32);
                    agents[parent].energy -= a.body.matter();
                    k.cc.born_cut += (a.body.cut > 0) as u64;
                    k.cc.not_built += a.body.cut as u64;
                    k.births += 1;
                    born.push((a.id as u32, agents[parent].id as u32));
                    newborn.push(a);
                }
                _ => {
                    k.no_room += 1;
                    lay(&mut pl.carrion, g.wcell(px, py), a.energy + a.fat, s, &mut k.cc);
                }
            }
        }
        agents.append(&mut newborn);

        // The dead leave their sub-cells and lie where they are; the list is compacted.
        for a in agents.iter_mut() {
            let cause = if !a.alive && a.worn_out {
                k.wear += 1;
                Some(2)
            } else if !a.alive {
                Some(1) // broken to its last block, or born without one
            } else if (a.energy <= 0.0 && a.fat <= 0.0) || a.short {
                k.hunger += 1;
                Some(0)
            } else {
                None
            };
            if let Some(cause) = cause {
                if a.born_size > 0 {
                    dead.push((a.id as u32, cause));
                    k.death_ages.push(a.age);
                }
                occ.release(g, a);
                a.alive = false;
                lay_body(a, g, &mut pl.carrion, s, &mut k.cc);
            }
        }
        agents.retain(|a| a.alive);
        for (i, a) in agents.iter().enumerate() {
            occ.relabel(g, a, i as u32);
        }
    }

    /// Lineages (e006): groups connected by possible mating, single linkage at distance D, with
    /// their births, splits, merges and extinctions. As e059, less its per-place columns.
    fn detect(&mut self, events: &mut dyn Write, lineages_csv: &mut dyn Write) {
        let step = self.step;
        {
            let live: HashSet<&[u16]> = self.agents.iter().map(|a| a.gene_ids.as_slice()).collect();
            self.cache.retain(|ids, _| live.contains(ids.as_slice()));
        }
        let Sim { agents, lineages, seen, origin, next_lineage, .. } = self;
        let n = agents.len();
        let mut parent: Vec<usize> = (0..n).collect();
        fn find(p: &mut [usize], mut i: usize) -> usize {
            while p[i] != i {
                p[i] = p[p[i]];
                i = p[i];
            }
            i
        }
        let mut reps: HashMap<&[u16], usize> = HashMap::new();
        let mut uniq: Vec<usize> = Vec::new();
        for i in 0..n {
            match reps.get(agents[i].keys.as_slice()) {
                Some(&r) => parent[i] = r,
                None => {
                    reps.insert(agents[i].keys.as_slice(), i);
                    uniq.push(i);
                }
            }
        }
        for a in 0..uniq.len() {
            for b in a + 1..uniq.len() {
                let (i, j) = (uniq[a], uniq[b]);
                if agents[i].distance(&agents[j]) <= D {
                    let (ri, rj) = (find(&mut parent, i), find(&mut parent, j));
                    if ri != rj {
                        parent[ri] = rj;
                    }
                }
            }
        }
        drop(reps);
        let mut members: HashMap<usize, Vec<usize>> = HashMap::new();
        for i in 0..n {
            let r = find(&mut parent, i);
            members.entry(r).or_default().push(i);
        }
        let mut groups: Vec<Vec<usize>> = members.into_values().filter(|m| m.len() >= MIN_LINEAGE).collect();
        groups.sort_by_key(|m| (std::cmp::Reverse(m.len()), agents[m[0]].id));
        let mut before: HashMap<u32, usize> = HashMap::new();
        for a in agents.iter() {
            *before.entry(a.lineage).or_default() += 1;
        }
        let mut now: HashMap<u32, usize> = HashMap::new();
        let mut assigned: Vec<(u32, Vec<usize>)> = Vec::new();
        for m in groups {
            let mut votes: HashMap<u32, usize> = HashMap::new();
            for &i in &m {
                if agents[i].lineage != 0 {
                    *votes.entry(agents[i].lineage).or_default() += 1;
                }
            }
            let best = |confirmed: bool| votes.iter().filter(|(id, _)| lineages.contains_key(id) == confirmed).max_by_key(|(id, c)| (**c, std::cmp::Reverse(**id))).map(|(id, _)| *id);
            let inherited = best(true).or_else(|| best(false)).unwrap_or(0);
            let id = if inherited != 0 && !now.contains_key(&inherited) {
                inherited
            } else {
                let id = *next_lineage;
                *next_lineage += 1;
                origin.insert(id, inherited);
                id
            };
            now.insert(id, m.len());
            assigned.push((id, m));
        }
        seen.retain(|id, _| now.contains_key(id));
        let mut ids: Vec<u32> = now.keys().copied().collect();
        ids.sort_unstable();
        for id in ids {
            let size = now[&id];
            let c = seen.entry(id).or_insert(0);
            *c += 1;
            if *c == LINEAGE_CONFIRM && !lineages.contains_key(&id) {
                let from = origin.remove(&id).unwrap_or(0);
                writeln!(events, "{step},{},{id},{from},{size}", if from == 0 { "birth" } else { "split" }).unwrap();
                lineages.insert(id, size);
            }
        }
        let mut into: HashMap<(u32, u32), usize> = HashMap::new();
        for (id, m) in &assigned {
            for &i in m {
                if agents[i].lineage != *id {
                    *into.entry((agents[i].lineage, *id)).or_default() += 1;
                }
                agents[i].lineage = *id;
            }
            if !lineages.contains_key(id) {
                continue;
            }
            let sz = m.len() as f64;
            let sum = |f: &dyn Fn(&Agent) -> f64| m.iter().map(|&i| f(&agents[i])).sum::<f64>() / sz;
            let shapes: HashSet<(u8, [u8; CELLS])> = m.iter().map(|&i| (agents[i].body.side, agents[i].body.cells)).collect();
            writeln!(
                lineages_csv,
                "{step},{id},{},{:.2},{:.2},{:.2},{:.2},{:.2},{:.2},{:.3},{:.0},{:.2},{:.2},{}",
                m.len(),
                sum(&|a| a.body.mass as f64),
                sum(&|a| a.body.kinds[HARD] as f64),
                sum(&|a| a.body.kinds[MUSCLE] as f64),
                sum(&|a| a.body.kinds[SENSOR] as f64),
                sum(&|a| a.body.kinds[DIGESTIVE] as f64),
                sum(&|a| a.body.bite_any() as f64),
                sum(&|a| (a.body.bite_any() >= TOOTH) as u8 as f64),
                sum(&|a| a.age as f64),
                sum(&|a| a.plant as f64),
                sum(&|a| a.meat() as f64),
                shapes.len()
            )
            .unwrap();
        }
        let mut carriers: HashMap<u32, usize> = HashMap::new();
        for a in agents.iter() {
            *carriers.entry(a.lineage).or_default() += 1;
        }
        let mut gone: Vec<u32> = lineages.keys().filter(|id| !carriers.contains_key(id)).copied().collect();
        gone.sort();
        for id in gone {
            let size = lineages.remove(&id).unwrap();
            let target = into.iter().filter(|((old, _), _)| *old == id).max_by_key(|((_, new), c)| (**c, std::cmp::Reverse(*new)));
            match target {
                Some(((_, new), _)) if before.get(&id).copied().unwrap_or(0) > 0 => writeln!(events, "{step},merge,{id},{new},{size}").unwrap(),
                _ => writeln!(events, "{step},extinct,{id},0,{size}").unwrap(),
            }
        }
        for (id, size) in &now {
            if let Some(s) = lineages.get_mut(id) {
                *s = *size;
            }
        }
    }

    const LOG_HEADER: &'static str = "step,pop,grown,births,children,sexual,no_room,empty,deaths_hunger,deaths_broken,deaths_wear,cells_broken,contacts,\
        plant_intake,meat_intake,kill_gain,scavenged,stay,forward,left,right,blocked,stalled,shoves,moved,turned,sense_used,\
        mass_p10,mass_p50,mass_p90,size_mean,hard_mean,muscle_mean,sensor_mean,digestive_mean,side_mean,density_mean,speed_mean,tooth,born_tooth,\
        fat_mean,on_fat,short,age_death_p50,age_death_p90,worn,cut_break,cut_wear,lineages,top_lineage,shapes,\
        pop_cold,pop_mild,pop_hot,pop_dry,pop_moist,pop_wet,travel_p50,path_mean,\
        grass,grass_grown,wood,algae,litter,carrion,air,soil_land,spent,matter,matter_err,burnt,land_temp,develops,ms_step,ms_world,ms_bodies,ms_lineage,ms_wall";

    /// The log's row for the interval of `steps` steps that ended now, and the tally reset.
    fn log_row(&mut self, steps: u64, matter0: f64, wall: f64) -> (String, Point) {
        let k = std::mem::take(&mut self.k);
        let (g, agents) = (self.g, &self.agents);
        let pop = agents.len();
        let n = pop.max(1) as f64;
        let per = steps.max(1) as f64;
        let mean = |f: &dyn Fn(&Agent) -> f64| agents.iter().map(f).sum::<f64>() / n;
        let quantile = |v: &mut Vec<f64>, q: f64| {
            v.sort_by(f64::total_cmp);
            v.get(((v.len().max(1) - 1) as f64 * q) as usize).copied().unwrap_or(0.0)
        };
        let mut masses: Vec<f64> = agents.iter().map(|a| a.body.mass as f64).collect();
        let (m10, m50, m90) = (quantile(&mut masses, 0.1), quantile(&mut masses, 0.5), quantile(&mut masses, 0.9));
        let grown: Vec<&Agent> = agents.iter().filter(|a| a.age >= GROWN).collect();
        let mut travel: Vec<f64> = grown.iter().map(|a| a.travel(g) as f64).collect();
        let travel_p50 = quantile(&mut travel, 0.5);
        let path_mean = grown.iter().map(|a| a.path as f64 / SUB as f64).sum::<f64>() / grown.len().max(1) as f64;
        let mut ages: Vec<f64> = k.death_ages.iter().map(|&a| a as f64).collect();
        let (a50, a90) = (quantile(&mut ages, 0.5), quantile(&mut ages, 0.9));
        let (mut temp_band, mut wet_band) = ([0usize; 3], [0usize; 3]);
        for a in agents {
            let h = self.hab[a.here(g)] as usize;
            if h < 9 {
                temp_band[h / 3] += 1;
                wet_band[h % 3] += 1;
            } else {
                temp_band[(h - 9) % 3] += 1;
                wet_band[2] += 1;
            }
        }
        let mut carriers: HashMap<u32, usize> = HashMap::new();
        for a in agents {
            *carriers.entry(a.lineage).or_default() += 1;
        }
        let top = self.lineages.keys().map(|id| carriers.get(id).copied().unwrap_or(0)).max().unwrap_or(0) as f64 / n;
        let shapes = agents.iter().map(|a| (a.body.side, a.body.cells)).collect::<HashSet<_>>().len();
        let (w, pl) = (&self.w, &self.pl);
        let sum = |v: &[f64]| v.iter().sum::<f64>();
        let soil_land: f64 = (0..w.n * w.n).filter(|&c| !w.sea[c]).map(|c| pl.soil[c]).sum();
        let land_temp = (0..w.n * w.n).filter(|&c| !w.sea[c]).map(|c| w.temp[c]).sum::<f64>() / self.land.max(1) as f64;
        let matter = self.matter();
        let err = (matter - matter0).abs() / matter0;
        let decisions = k.actions.iter().sum::<u64>().max(1) as f64;
        let ms = [(k.t_world + k.t_bodies + k.t_lineage) * 1000.0 / per, k.t_world * 1000.0 / per, k.t_bodies * 1000.0 / per, k.t_lineage * 1000.0 / per];
        let kill_gain = k.cc.kill_gain / k.cc.cells_broken.max(1) as f64;
        let mut s = format!(
            "{},{pop},{},{},{},{},{},{},{},{},{},{},{},{:.3},{:.3},{kill_gain:.4},{:.3}",
            self.step,
            grown.len(),
            k.births,
            k.children,
            k.sexual,
            k.no_room,
            k.empty,
            k.hunger,
            k.cc.kills,
            k.wear,
            k.cc.cells_broken,
            k.cc.contacts,
            k.plant * self.p.scale,
            (k.cc.kill_gain + k.scavenged) * self.p.scale,
            k.scavenged * self.p.scale
        );
        for a in k.actions {
            s.push_str(&format!(",{:.3}", a as f64 / decisions));
        }
        s.push_str(&format!(
            ",{:.3},{:.3},{},{:.4},{:.4},{:.3},{m10:.1},{m50:.1},{m90:.1},{:.2},{:.2},{:.2},{:.2},{:.2},{:.2},{:.3},{:.3},{:.3},{:.3}",
            k.blocked as f64 / k.tried.max(1) as f64,
            k.stalled as f64 / k.tried.max(1) as f64,
            k.shoves,
            k.moved as f64 / per / n,
            k.turned as f64 / k.body_steps.max(1) as f64,
            k.sense_used as f64 / k.sense_n.max(1) as f64,
            mean(&|a| a.body.size as f64),
            mean(&|a| a.body.kinds[HARD] as f64),
            mean(&|a| a.body.kinds[MUSCLE] as f64),
            mean(&|a| a.body.kinds[SENSOR] as f64),
            mean(&|a| a.body.kinds[DIGESTIVE] as f64),
            mean(&|a| a.body.side as f64),
            mean(&|a| a.body.density as f64),
            mean(&|a| a.body.speed() as f64),
            mean(&|a| (a.body.bite_any() >= TOOTH) as u8 as f64),
            mean(&|a| (a.born_bite >= TOOTH) as u8 as f64),
        ));
        s.push_str(&format!(
            ",{:.3},{:.3},{:.4},{a50:.0},{a90:.0},{},{},{},{},{top:.3},{shapes}",
            mean(&|a| a.fat),
            mean(&|a| (a.energy <= 0.0) as u8 as f64),
            k.short as f64 / k.upkept.max(1) as f64,
            k.worn,
            k.cc.cut_break,
            k.cc.cut_wear,
            self.lineages.len()
        ));
        for v in temp_band.iter().chain(&wet_band) {
            s.push_str(&format!(",{v}"));
        }
        s.push_str(&format!(
            ",{travel_p50:.2},{path_mean:.2},{:.0},{:.4},{:.0},{:.0},{:.0},{:.1},{:.1},{soil_land:.0},{:.3},{matter:.3},{err:.2e},{:.5},{land_temp:.2},{},{:.3},{:.3},{:.3},{:.3},{:.3}",
            sum(&pl.grass),
            k.grass_grown / per,
            sum(&pl.wood),
            sum(&pl.algae),
            sum(&pl.litter),
            sum(&pl.carrion),
            pl.air,
            k.spent * self.p.scale / per,
            k.burnt as f64 / self.land.max(1) as f64,
            k.develops,
            ms[0],
            ms[1],
            ms[2],
            ms[3],
            wall * 1000.0 / per
        ));
        let point = Point { step: self.step, pop, plant: k.plant, kills: k.cc.kill_gain, scavenged: k.scavenged, ms, err };
        (s, point)
    }

    const AGENT_HEADER: &'static str = "step,id,lineage,age,turns,mass,size,side,density,born_size,born_mass,born_hard,born_muscle,born_sensor,born_digestive,born_bite,\
        hard,muscle,sensor,digestive,bite,bite_any,shell,speed,energy,fat,plant,meat,killed,scavenged,travel,path,worn,pace,place,born_place,temp,moist,height,cells";

    /// Every body, for e060's census: `place` is the habitat of the cell under it (e061's 15).
    fn agent_rows(&self, out: &mut dyn Write) {
        let (g, w) = (self.g, &self.w);
        for a in &self.agents {
            let (b, c) = (&a.body, a.here(g));
            writeln!(
                out,
                "{},{},{},{},{},{:.2},{},{},{:.3},{},{:.2},{},{},{},{},{},{},{},{},{},{},{},{:.2},{:.3},{:.3},{:.3},{:.3},{:.3},{:.3},{:.3},{:.2},{:.2},{},{:.3},{},{},{:.1},{:.3},{:.0},{}",
                self.step,
                a.id,
                a.lineage,
                a.age,
                a.turns,
                b.mass,
                b.size,
                b.side,
                b.density,
                a.born_size,
                a.born_mass,
                a.born_kinds[HARD],
                a.born_kinds[MUSCLE],
                a.born_kinds[SENSOR],
                a.born_kinds[DIGESTIVE],
                a.born_bite,
                b.kinds[HARD],
                b.kinds[MUSCLE],
                b.kinds[SENSOR],
                b.kinds[DIGESTIVE],
                b.bite(),
                b.bite_any(),
                b.shell(),
                b.speed(),
                a.energy,
                a.fat,
                a.plant,
                a.meat(),
                a.killed,
                a.scavenged,
                a.travel(g),
                a.path as f32 / SUB as f32,
                a.worn,
                pace(b.mass),
                self.hab[c],
                a.born_hab,
                w.temp[c],
                (w.ground[c] / self.p.soil).min(1.0),
                w.elev[c],
                b.cells[..b.s() * b.s()].iter().map(|&k| (b'0' + k) as char).collect::<String>()
            )
            .unwrap();
        }
    }

    /// The viewer's cell layers, in the order of `layer_specs`.
    fn layers(&self) -> Vec<Vec<f64>> {
        let (w, pl, p) = (&self.w, &self.pl, &self.p);
        let cells = w.n * w.n;
        let water = (0..cells)
            .map(|c| {
                if w.sea[c] {
                    1.0 + VIEW_SEA * (-w.elev[c] / SHALLOW).min(1.0)
                } else {
                    let s = w.ground[c] - p.soil;
                    if s > 10.0 { 1.0 + s / 1000.0 / p.relief * VIEW_RELIEF } else { 0.0 }
                }
            })
            .collect();
        let plant = (0..cells).map(|c| pl.grass[c] + pl.wood[c]).collect();
        let temp = w.temp.iter().map(|t| t + TEMP_OFFSET).collect();
        let moisture = (0..cells).map(|c| if w.sea[c] { 1.0 } else { (w.ground[c] / p.soil).min(1.0) }).collect();
        let hab = self.hab.iter().map(|&h| h as f64).collect();
        let mut fire = vec![0.0f64; cells];
        for &(c, _) in &pl.front {
            fire[c as usize] = 1.0;
        }
        vec![water, plant, pl.soil.clone(), temp, moisture, w.rain_now.clone(), w.light.clone(), hab, pl.grass.clone(), pl.wood.clone(), pl.algae.clone(), pl.litter.clone(), fire, pl.carrion.clone()]
    }
}

fn layer_specs() -> Vec<viewer::LayerSpec> {
    use viewer::{LayerSpec, Scale};
    vec![
        LayerSpec::new("water", (1.0 + VIEW_SEA) as f32, Scale::Sqrt),
        LayerSpec::new("plant", 16.0, Scale::Sqrt),
        LayerSpec::new("soil", 20.0, Scale::Sqrt),
        LayerSpec::new("temperature", 100.0, Scale::Linear),
        LayerSpec::new("moisture", 1.0, Scale::Linear),
        LayerSpec::new("rain", 2.0, Scale::Sqrt),
        LayerSpec::new("light", 1.0, Scale::Linear),
        LayerSpec::new("habitat", 255.0, Scale::Linear),
        LayerSpec::new("grass", 4.0, Scale::Sqrt),
        LayerSpec::new("wood", 16.0, Scale::Sqrt),
        LayerSpec::new("algae", 2.0, Scale::Sqrt),
        LayerSpec::new("litter", 8.0, Scale::Sqrt),
        LayerSpec::new("fire", 1.0, Scale::Linear),
        LayerSpec::new("carrion", 16.0, Scale::Sqrt),
    ]
}

fn main() {
    let args: Vec<String> = std::env::args().skip(1).collect();
    let prefix = args.first().expect("usage: e064_scale <prefix> [key=value ...] [file.params ...]").clone();
    let p = parse(&args[1..]);
    if let Some(dir) = std::path::Path::new(&prefix).parent() {
        std::fs::create_dir_all(dir).ok();
    }
    let started = Instant::now();
    let (w, pl, update_i) = settled_world(&p, Some(WORLDS));
    if p.steps <= 0.0 {
        return;
    }
    let threads: usize = std::env::var("EVLOG_THREADS").ok().and_then(|s| s.parse().ok()).unwrap_or_else(|| std::thread::available_parallelism().map(|n| n.get()).unwrap_or(1)).max(1);
    let mut sim = Sim::new(p.clone(), w, pl, update_i, threads);
    eprintln!("{} bodies on {} land cells", sim.agents.len(), sim.land);

    let open = |name: &str| std::io::BufWriter::new(std::fs::File::create(format!("{prefix}_{name}")).unwrap());
    let mut log = open("log.csv");
    writeln!(log, "{}", Sim::LOG_HEADER).unwrap();
    let mut agents_csv = open("agents.csv");
    writeln!(agents_csv, "{}", Sim::AGENT_HEADER).unwrap();
    let mut events = open("events.csv");
    writeln!(events, "step,event,lineage,other,size").unwrap();
    let mut lineages_csv = open("lineages.csv");
    writeln!(lineages_csv, "step,lineage,size,mass,hard,muscle,sensor,digestive,bite_any,tooth,age,plant,meat,shapes").unwrap();

    // The viewer: nothing unless EVLOG_VIEW is set. Its clock is the bodies' step.
    let n = sim.w.n;
    let height_view: Vec<f32> = sim.w.elev.iter().map(|&e| if e >= 0.0 { e / p.relief * VIEW_RELIEF } else { -VIEW_SEA * (-e / SHALLOW).min(1.0) } as f32).collect();
    let band = vec![0u8; n * n];
    let mut json = String::from("{");
    for (name, v) in Params::NAMES.iter().zip(p.values()) {
        let key = if *name == "relief" { "relief_m" } else { name };
        json.push_str(&format!("\"{key}\":{v},"));
    }
    json.push_str(&format!(
        "\"relief\":{VIEW_RELIEF},\"water_rain\":1,\"water_evap\":1,\"depth\":1,\"temperature_offset\":{TEMP_OFFSET},\"store\":{STORE},\"max_age\":0,\"habitats\":[{}]}}",
        HAB_NAMES.iter().map(|h| format!("\"{h}\"")).collect::<Vec<_>>().join(",")
    ));
    let mut view = viewer::View::from_env(
        &prefix,
        viewer::Init {
            experiment: "e064_scale",
            w: n,
            h: n,
            sub: SUB,
            height: &height_view,
            band: &band,
            layers: layer_specs(),
            globals: vec!["season", "year", "pop"],
            blocks: vec!["empty", "hard", "muscle", "sensor", "digestive"],
            deaths: CAUSES.to_vec(),
            births: true,
            params: json,
        },
    );

    let matter0 = sim.matter();
    let steps = p.steps as u64;
    let mut points: Vec<Point> = Vec::new();
    let mut last = Instant::now();
    for step in 1..=steps {
        sim.step();
        if step % LINEAGE_INTERVAL == 0 {
            let t = Instant::now();
            sim.detect(&mut events, &mut lineages_csv);
            sim.k.t_lineage += t.elapsed().as_secs_f64();
        }
        if let Some(v) = view.as_mut() {
            for (child, parent) in sim.born.drain(..) {
                v.born(step, child, parent);
            }
            for (id, cause) in sim.dead.drain(..) {
                v.died(step, id, cause);
            }
            if v.wants(step) {
                let layers = sim.layers();
                let refs: Vec<&[f64]> = layers.iter().map(|l| l.as_slice()).collect();
                let t = sim.update_i as f64 * p.tick;
                v.frame(step, &refs, &[(TAU * t / p.year).sin() as f32, (t / p.year).fract() as f32, sim.agents.len() as f32], |push| {
                    for a in &sim.agents {
                        let s = a.body.s();
                        let diet = match (a.plant > 0.0, a.meat() > 0.0) {
                            (false, false) => 3,
                            (true, false) => 0,
                            (false, true) => 2,
                            _ => 1,
                        };
                        push(viewer::AgentIn { id: a.id as u32, lineage: a.lineage, x: a.x as u16, y: a.y as u16, facing: a.facing, diet, fill: 1.0, energy: a.energy as f32, ripe: a.body.threshold(), fat: (a.fat / (STORE * a.body.mass).max(1e-6) as f64) as f32, age: a.age, born: a.born_size, side: a.body.side, cells: &a.body.cells[..s * s] });
                    }
                });
            }
            v.tick(step);
        } else {
            sim.born.clear();
            sim.dead.clear();
        }
        if step % AGENT_DUMP == 0 {
            sim.agent_rows(&mut agents_csv);
        }
        let extinct = sim.agents.is_empty() && p.start > 0.0; // start=0: the world alone, the control
        if step % LOG_INTERVAL == 0 || extinct {
            let (line, point) = sim.log_row((step - 1) % LOG_INTERVAL + 1, matter0, last.elapsed().as_secs_f64());
            last = Instant::now();
            writeln!(log, "{line}").unwrap();
            if step % (10 * LOG_INTERVAL) == 0 || extinct {
                eprintln!(
                    "step {step}: {} bodies, {} lineages, {:.2} ms a step (world {:.2}, bodies {:.2}, lineages {:.2}), matter err {:.1e}",
                    point.pop, sim.lineages.len(), point.ms[0], point.ms[1], point.ms[2], point.ms[3], point.err
                );
            }
            points.push(point);
        }
        if extinct {
            eprintln!("extinct at step {step}");
            break;
        }
    }

    // The run in one row: its parameters and the second half of it.
    let last_step = points.last().map_or(0, |q| q.step);
    let late: Vec<&Point> = points.iter().filter(|q| 2 * q.step > last_step).collect();
    let m = late.len().max(1) as f64;
    let avg = |f: &dyn Fn(&Point) -> f64| late.iter().map(|q| f(q)).sum::<f64>() / m;
    let pop_mean = avg(&|q| q.pop as f64);
    let eaten = late.iter().map(|q| q.plant + q.kills + q.scavenged).sum::<f64>().max(1e-300);
    let mut header: Vec<String> = Params::NAMES.iter().map(|s| s.to_string()).collect();
    for h in ["steps_run", "pop_end", "pop_mean", "pop_min", "pop_max", "kills_share", "dead_share", "ms_step", "ms_world", "ms_bodies", "ms_lineage", "us_per_body", "matter_err", "seconds"] {
        header.push(h.to_string());
    }
    let values = p.values().iter().map(|v| format!("{v}")).collect::<Vec<_>>().join(",");
    let row = format!(
        "{values},{last_step},{},{pop_mean:.1},{},{},{:.4},{:.4},{:.3},{:.3},{:.3},{:.3},{:.2},{:.2e},{:.0}",
        sim.agents.len(),
        late.iter().map(|q| q.pop).min().unwrap_or(0),
        late.iter().map(|q| q.pop).max().unwrap_or(0),
        late.iter().map(|q| q.kills).sum::<f64>() / eaten,
        late.iter().map(|q| q.scavenged).sum::<f64>() / eaten,
        avg(&|q| q.ms[0]),
        avg(&|q| q.ms[1]),
        avg(&|q| q.ms[2]),
        avg(&|q| q.ms[3]),
        avg(&|q| q.ms[2]) * 1000.0 / pop_mean.max(1.0),
        points.iter().map(|q| q.err).fold(0.0, f64::max),
        started.elapsed().as_secs_f64()
    );
    std::fs::write(format!("{prefix}_row.csv"), format!("{}\n{row}\n", header.join(","))).unwrap();
    let _ = Params::DOCS;
    eprintln!("done: {prefix} in {:.0} s", started.elapsed().as_secs_f64());
}

#[cfg(test)]
mod tests {
    use super::*;

    /// A small world that spins up and grows in a moment.
    fn small() -> Params {
        let mut p = Params::default();
        p.size = 32.0;
        p.grain = 16.0;
        p.land = 0.6;
        p.year = 400.0;
        p.spinup = 400.0;
        p.grow_years = 2.0;
        p.grow_steps = 0.0;
        p.ignite = 1e-3;
        p.start = 0.3;
        p
    }

    /// A world read back from its bytes goes on exactly as the one that was written.
    #[test]
    fn a_settled_world_is_read_back_as_it_was() {
        let p = small();
        let (mut w, mut pl, u) = settled_world(&p, None);
        let bytes = world_bytes(world_hash(&p), u, &w, &pl);
        let (mut w2, mut pl2, u2) = world_from(&bytes, world_hash(&p), &p).unwrap();
        assert_eq!(u, u2);
        let mut other = p.clone();
        other.grass_rate *= 2.0;
        assert!(world_from(&bytes, world_hash(&other), &other).is_none());
        let sat = Sat::new();
        for i in 0..300 {
            let t = (u + i) as f64 * p.tick;
            w.update(&p, &sat, t);
            pl.update(&w, &p, 3);
            w2.update(&p, &sat, t);
            pl2.update(&w2, &p, 3);
        }
        let bits = |v: &[f64]| v.iter().map(|x| x.to_bits()).collect::<Vec<_>>();
        assert_eq!(bits(&w.temp), bits(&w2.temp));
        assert_eq!(bits(&pl.grass), bits(&pl2.grass));
        assert_eq!(bits(&pl.litter), bits(&pl2.litter));
        assert_eq!(pl.fire_sizes, pl2.fire_sizes);
    }

    /// Bodies eat, pay, move, break, breed and die on the producers' world, which burns and rots,
    /// and the world's matter neither grows nor shrinks, at a body's full scale and at a sixteenth.
    #[test]
    fn matter_is_conserved_with_bodies() {
        for scale in [1.0, 0.0625] {
            conserved_at(scale);
        }
    }

    fn conserved_at(scale: f64) {
        let mut p = small();
        p.scale = scale;
        let (w, pl, u) = settled_world(&p, None);
        let mut sim = Sim::new(p, w, pl, u, 1);
        assert!(sim.agents.len() > 50, "{} bodies", sim.agents.len());
        let start = sim.matter();
        let (mut births, mut eaten) = (0u64, 0.0f64);
        for step in 1..=3_000u64 {
            sim.step();
            births += sim.k.births;
            sim.k.births = 0;
            if step % LINEAGE_INTERVAL == 0 {
                sim.detect(&mut std::io::sink(), &mut std::io::sink());
            }
            if step % 100 == 0 {
                let m = sim.matter();
                assert!((m - start).abs() < 1e-9 * start, "step {step}: matter {start} -> {m}");
            }
        }
        eaten += sim.k.plant + sim.k.scavenged;
        assert!(births > 0 && eaten > 0.0, "births {births}, eaten {eaten}");
        // Nobody stands on the sea.
        for a in &sim.agents {
            for q in a.cells_held() {
                let (sx, sy) = a.sub_at(sim.g, q, NORTH, 0);
                assert!(!sim.w.sea[sim.g.wcell(sx, sy)]);
            }
        }
    }

    /// A gut takes the grass and the dead in their proportions, and the dead rot into the soil.
    #[test]
    fn a_gut_takes_both_foods_and_the_dead_rot() {
        let p = small();
        let (w, mut pl, _) = settled_world(&p, None);
        let c = (0..w.n * w.n).find(|&c| !w.sea[c]).unwrap();
        pl.grass[c] = 3.0;
        pl.carrion[c] = 1.0;
        let (plant, dead) = pl.take(c, 0.4);
        assert!((plant - 0.3).abs() < 1e-12 && (dead - 0.1).abs() < 1e-12);
        assert!((pl.grass[c] - 2.7).abs() < 1e-12 && (pl.carrion[c] - 0.9).abs() < 1e-12);
        let (g, d) = (pl.grass[c], pl.carrion[c]);
        assert_eq!(pl.take(c, 10.0), (g, d));
        assert_eq!((pl.grass[c], pl.carrion[c]), (0.0, 0.0));
        pl.carrion[c] = 1.0;
        let soil = pl.soil[c];
        let before = pl.matter();
        pl.update(&w, &p, 3);
        assert!((pl.carrion[c] - 0.99f64.powi(10)).abs() < 1e-12);
        assert!(pl.soil[c] > soil);
        assert!((pl.matter() - before).abs() < 1e-9 * before);
    }
}
