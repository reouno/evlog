//! Rung 3 (#123, e110): bodies in metres and seconds, and bodies that meet.
//!
//! A body is an individual (#117 v2): it develops a form of tissues from the shared genome (`form.rs`), grows,
//! eats the producers, drinks, keeps warm, breeds and dies. e106 wrote that life in cells and updates; here no
//! law reads either. A body has a place in metres and a heading; it senses within a reach in metres, walks its
//! speed times the time, and the cell is only the grain of the ground it reads and feeds on. The update is the
//! step of integration (`body_tick` steps of 19 minutes).
//!
//! The scale (#126): a body holds about `big_s` kg of animals at any age. A grown body whose adult mass is near
//! `big_s` is one animal, a smaller kind is a flock, a clutch is carried until it holds `brood_s` of `big_s` and
//! hatches as one brood, and a body over 2 `big_s` parts in two. What it is and does is one animal's; what crosses its edge reaches the cell `s` times over.
//!
//! An update, in four passes:
//! 1. every body senses and chooses (`decide`, in parallel, reading the bodies as the last update left them): its
//!    pulls towards where food, carrion and water rise, downhill and along its last heading, a unit of chance,
//!    and the pull of the bodies it sees - if the strongest of all is a body's, it heads straight for it or
//!    straight away;
//! 2. bodies meet (`meet`, in order): a chaser follows the other through the update and arrives at a time given
//!    by their speeds and the gap (pure pursuit, a closed form); on contact one law decides what fails (pressure
//!    against strength, for the time they stay together), who is held, and what compound enters whom; then
//!    every body is moved;
//! 3. every body lives where it now stands (`live`, in parallel by the cells' rows, each touching only its own
//!    cell): heat, eating (producers, litter, carrion), water, breath, upkeep, growth, eggs, wear;
//! 4. in order: the dead become carrion, clutches hatch as broods, heavy bodies part.
//!
//! Units: masses kg of dry matter a body (one animal), A and B in g; a cell's fields stay kg (or mm) a m2, and
//! a body's flows reach them times `s / area`. Places in m, speeds in m/s, time in days (`dt`) or seconds.

use crate::form::{BodyType, Form, BACK, FAT, FLANK, FRAME, FRONT, GUT, MUSCLE, NB, NE, NI, NO, STAGES};
use crate::genome::{self, hamming};
use crate::life::{activity, q10, toughness, Cohort, Litter, Seeds, BANK, K, LEAF, SEED, WOOD};
use crate::noise::Rng;
use crate::par::{self, Shared, CHUNKS};
use crate::terrain::{Terrain, NONE};
use crate::Params;
use std::f64::consts::TAU;

const WET: f64 = 3.3; // wet over dry mass of tissue
const FAT_WET: f64 = 1.1; // of fat
const ENERGY: f64 = 1.7e7; // J a kg of dry matter
const LATENT: f64 = 2.4e6; // J a kg of water evaporated
const G: f64 = 9.8;
const SEE: usize = 8; // the nearest bodies a body reads
const ACT0: f64 = -2.2; // with no genes a body moves at a tenth of its speed
// Harm a day (e106's were an update of 3.2 hours): without breath, over its heat, and tissue lost a degree of frost.
const BREATH_HARM: f64 = 1.5;
const HEAT_HARM: f64 = 2.25;
const FROST: f64 = 0.015;
const DRINK: f64 = 0.075; // share of a cell's water a body's animals may drink a day

#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub enum Death {
    None,
    Hunger,
    Thirst,
    Heat,
    Cold,
    Breath,
    Poison,
    Age,
    Form,
    Broken,
}

pub const DEATHS: [&str; 9] = ["hunger", "thirst", "heat", "cold", "breath", "poison", "age", "form", "broken"];
pub const FOODS: [&str; 6] = ["leaf", "wood", "seed", "litter", "carrion", "kill"];

pub const CENSUS: &str = "year,id,parent,root,born,genes,bodies,animals,matter,mass,adult_mass,egg,clutch,maturity,t_opt,breadth,tolerance,n_keys,keys,ckey,cells,nv,frame,muscle,gut,nerve,fat,glue,a,b,cmp,frame_tough,density,legs,bite,mouth,eye,glue_front,hard_front,hard_back,hard_flank,tip_front,tip_back,tip_flank,ext_x,ext_y,ext_z,sea,v_top,reach,travel_km_yr,from_birth_km,ate_leaf,ate_wood,ate_seed,ate_litter,ate_carrion,ate_kill,kills,pull_one,pull_size,pull_alike,pull_fat,pull_near,pull_coming,press_one,press_size,press_alike,press_fat,press_near,press_coming";

#[derive(Clone)]
pub struct Body {
    pub id: u64,
    pub g: u32,
    pub x: f64, // m
    pub y: f64,
    pub hx: f64, // its last heading
    pub hy: f64,
    pub wa: f64, // the way chance turns it, an angle that wanders
    pub cell: u32,
    pub m: f64,   // dry tissue, kg
    pub ta: f64,  // g of A in the tissue
    pub tb: f64,  // g of B
    pub fat: f64, // kg
    pub pa: f64,  // g of A held for growth
    pub pb: f64,
    pub w: f64, // kg of water
    pub s: f64, // the animals it stands for, a whole number
    pub peak: f64,
    pub age: f64, // days
    pub stage: u8,
    pub t: f64, // C
    pub harm: f64,
    pub seed: u64,       // of its own chance
    pub bx: f64,         // where it was born, m
    pub by: f64,
    pub travel: f64,     // m walked
    pub eaten: [f64; 6], // kg eaten in its life (`FOODS`)
    pub kills: f64,      // animals its presses killed
    pub dead: Death,
    // the clutch each of its animals carries until it is laid: eggs, their dry matter, A and B (g), water
    pub carry: f64,
    pub c_m: f64,
    pub c_a: f64,
    pub c_b: f64,
    pub c_w: f64,
    pub lay: bool, // the clutch is laid this update, and hatches in the last pass
    // what its front took from another body in this update's meeting (e111, `bite`): kg, g of A, g of B an animal
    pub meal: [f64; 3],
    // the update's: set as it chooses, moves and meets, used as it lives
    pub path: f64,    // m walked
    pub work: f64,    // kg burnt moving, climbing and pressing
    pub smother: f64, // share of its breath cut by another's glue
    pub breed: bool,
    pub v_top: f64, // m/s
    pub reach: f64, // m it senses
}

impl Body {
    /// A grown body put into the world (the sowing, an injection): its tissue, fat and water, nothing eaten yet.
    #[allow(clippy::too_many_arguments)]
    fn grown(id: u64, g: u32, at: (f64, f64), cell: u32, turn: f64, seed: u64, m: f64, s: f64, fat: f64, ab: (f64, f64)) -> Body {
        Body {
            id,
            g,
            x: at.0,
            y: at.1,
            hx: turn.cos(),
            hy: turn.sin(),
            wa: turn,
            cell,
            m,
            ta: ab.0,
            tb: ab.1,
            fat,
            pa: 0.0,
            pb: 0.0,
            w: m * (WET - 1.0),
            s,
            peak: m,
            age: 0.0,
            stage: (STAGES - 1) as u8,
            t: 20.0,
            harm: 0.0,
            seed,
            bx: at.0,
            by: at.1,
            travel: 0.0,
            eaten: [0.0; 6],
            kills: 0.0,
            dead: Death::None,
            carry: 0.0,
            c_m: 0.0,
            c_a: 0.0,
            c_b: 0.0,
            c_w: 0.0,
            lay: false,
            meal: [0.0; 3],
            path: 0.0,
            work: 0.0,
            smother: 0.0,
            breed: false,
            v_top: 0.0,
            reach: 0.0,
        }
    }
    fn wet(&self) -> f64 {
        (self.m + self.c_m) * WET + self.fat * FAT_WET
    }
    pub fn target_water(&self) -> f64 {
        self.m * (WET - 1.0)
    }
}

/// A draw in [0, 1) from a body's seed and the update's number: the same whatever the threads.
fn chance(seed: u64, salt: u64) -> f64 {
    let mut z = seed ^ salt.wrapping_mul(0x9E37_79B9_7F4A_7C15);
    z = (z ^ (z >> 30)).wrapping_mul(0xBF58_476D_1CE4_E5B9);
    z = (z ^ (z >> 27)).wrapping_mul(0x94D0_49BB_1331_11EB);
    ((z ^ (z >> 31)) >> 11) as f64 / (1u64 << 53) as f64
}

/// The carrion of a cell: tissue that failed and bodies that died, kg and g a m2. `kill` is the part of `m` that
/// came from a meeting.
#[derive(Clone, Copy, Default)]
pub struct Carrion {
    pub m: f64,
    pub a: f64,
    pub b: f64,
    pub kill: f64,
}

/// What crossed the edges of the bodies in a stretch of time (cell units: kg or mm a m2, summed over cells).
#[derive(Default, Clone, Copy)]
pub struct BFlux {
    pub fixed: f64,    // matter that entered (sown)
    pub returned: f64, // respired
    pub eaten: [f64; 6],
    pub drunk: f64,
    pub evap: f64,
    pub births: f64,
    pub deaths: [f64; 9],
    pub splits: f64,
    pub moved: f64,   // km walked
    pub catches: f64, // a chaser reached the body it headed for
    pub presses: f64, // and pressed it
    pub breaks: f64,  // and a face failed
    pub killed: f64,  // animals killed in meetings
    pub torn: f64,    // tissue that failed in meetings
    pub riders: f64,  // a catcher carried by the body it holds
    pub rotted: f64,  // carrion gone to the litter
}

impl BFlux {
    pub fn add(&mut self, o: &BFlux) {
        self.fixed += o.fixed;
        self.returned += o.returned;
        for k in 0..6 {
            self.eaten[k] += o.eaten[k];
        }
        self.drunk += o.drunk;
        self.evap += o.evap;
        self.births += o.births;
        for k in 0..9 {
            self.deaths[k] += o.deaths[k];
        }
        self.splits += o.splits;
        self.moved += o.moved;
        self.catches += o.catches;
        self.presses += o.presses;
        self.breaks += o.breaks;
        self.killed += o.killed;
        self.torn += o.torn;
        self.riders += o.riders;
        self.rotted += o.rotted;
    }
}

/// What a body chose in an update.
#[derive(Clone, Copy)]
struct Plan {
    vx: f64, // m/s: its way at the speed it chose
    vy: f64,
    hx: f64,
    hy: f64,
    wa: f64,
    v: f64,
    v_top: f64,
    power: f64, // W of propulsion at full activity
    act: f64,
    len: f64,   // m
    reach: f64, // m
    tgt: u32,   // the body it heads for or away from
    chase: bool,
    press: bool,
    breed: bool,
}

pub struct Bodies {
    pub list: Vec<Body>,
    pub types: Vec<Option<Box<BodyType>>>,
    pub carrion: Vec<Carrion>,
    next_id: u64,
    rng: Rng,
    pub sown: bool,
    area: f64,   // m2 a cell
    cell_m: f64, // m a cell's side
    wrap: bool,  // the world is a torus (the planet), not land in a sea
    updates: u64,
    chunk_of_row: Vec<usize>,
    // what a body senses of each cell: kg a m2 of leaf, seed and litter within a short body's reach, of carrion,
    // and the ground's fill
    food: Vec<f64>,
    flesh: Vec<f64>,
    water: Vec<f64>,
    head: Vec<u32>, // the bodies of each cell, as a list through `next`
    next: Vec<u32>,
    trace: u64,
    pub secs: [f64; 4], // decide, meet, live, the last pass
    pub watched: bool,         // whether the viewer is told who died and who was born (`died`, `born`)
    pub died: Vec<(u32, u8)>,  // since the viewer last took them: a body, what it died of (`DEATHS`)
    pub born: Vec<(u32, u32)>, // a body, the body it came from (a brood's parent, a split's other half)
}

/// What the bodies read and write of the world in an update.
pub struct World<'a> {
    pub p: &'a Params,
    pub ter: &'a Terrain,
    pub temp: &'a [f64],
    pub light: &'a [f64],
    pub vapor: &'a mut [f64],
    pub ground: &'a mut [f64],
    pub sat: &'a crate::climate::Sat,
    pub co: &'a mut [Cohort],
    pub lit: &'a mut [Litter],
    pub bank: &'a mut [Seeds],
    pub sa: &'a mut [f64], // the soil's A and B (the water's, at sea)
    pub sb: &'a mut [f64],
    pub gen: &'a [Option<Box<genome::Genotype>>],
    pub step: f64,
    pub year: u32,
}

/// A body's size: its wet mass, a voxel's side, its height and its length.
struct Size {
    wet: f64,
    d: f64,
    d2: f64,
    height: f64,
    len: f64,
}

fn size(b: &Body, fm: &Form) -> Size {
    let wet = b.wet();
    let d = (wet / (fm.density * 1000.0) / fm.nv).cbrt();
    Size { wet, d, d2: d * d, height: fm.ext[2] * d, len: fm.ext[0] * d }
}

/// How well a body works at its heat.
fn heat_factor(t: f64, t_opt: f64, breadth: f64) -> f64 {
    (10.0 / breadth) * (-((t - t_opt) / breadth).powi(2)).exp()
}

/// A body's speed at full activity and the power that gives it: on the ground propulsion from the legs against
/// friction and the ground's roughness (a tall body steps over it); in water from all muscle against drag.
fn speed(p: &Params, fm: &Form, m: f64, sz: &Size, sea: bool, ft: f64) -> (f64, f64) {
    let power = if sea { p.muscle_power * fm.frac[MUSCLE] * activity(fm.b_act) } else { p.muscle_power * fm.legs } * m * WET * ft.min(1.5);
    let v = if sea {
        let cd = 0.05 + 0.5 * (fm.front / (fm.ext[0] * fm.ext[0])).min(1.0);
        (2.0 * power / (1000.0 * cd * fm.front * sz.d2)).cbrt()
    } else {
        power / (sz.wet * G * (p.mu_ground + p.ground_rough / sz.height.max(1e-6)))
    };
    (v, power)
}

/// What a gut passes in `dt` days, kg an animal.
fn gut_cap(p: &Params, fm: &Form, m: f64, dt: f64, ft: f64) -> f64 {
    p.gut_rate * fm.frac[GUT] * activity(fm.b_act) * m * dt * ft.min(1.5)
}

/// What a meeting reads of a body.
struct Phys {
    s: f64,
    len: f64,
    v_top: f64,
    pressure: f64,      // Pa its front puts on what it presses
    force: f64,         // N behind that
    power: f64,         // W its animals' fronts work with
    need: [f64; 3],     // Pa each face takes to fail
    hard: [f64; 3],     // the hardest tip of each face
    tip_area: [f64; 3], // m2 of each face's outermost layer
    cmp: [f64; 3],      // share of compound in it
    tip_mass: [f64; 3], // kg of it
    grip: f64,          // N its front's glue holds
    glue_area: f64,
    pull: f64, // N its muscle pulls with, standing
    drag: f64, // N to drag it over the ground
    soft_area: f64,
    key: u8,
    room: f64,  // kg its animals' guts take in this update
    mouth: f64, // share of its front that is mouth
}

fn phys(p: &Params, b: &Body, bt: &BodyType, sea: bool, v_top: f64, dt: f64) -> Phys {
    let fm = &bt.forms[b.stage as usize];
    let sz = size(b, fm);
    let d3 = sz.d2 * sz.d;
    Phys {
        room: gut_cap(p, fm, b.m, dt, heat_factor(b.t, bt.tr[4], bt.tr[5])) * b.s,
        mouth: (fm.mouth / fm.face_n[FRONT].max(1.0)).min(1.0),
        s: b.s,
        len: sz.len,
        v_top,
        pressure: p.muscle_stress * fm.bite,
        force: p.muscle_stress * fm.behind * sz.d2,
        power: p.muscle_power * fm.behind * d3 * 1000.0 * b.s,
        need: fm.face_hard.map(|h| p.bite_ref * (1.0 + p.bite_tough * h)),
        hard: fm.face_tip,
        tip_area: fm.face_n.map(|n| n * sz.d2),
        cmp: fm.face_cmp,
        tip_mass: fm.face_n.map(|n| n * d3 * 1000.0 / WET),
        grip: p.glue_stress * fm.glue * sz.d2,
        glue_area: fm.glue * sz.d2,
        pull: p.muscle_stress * if sea { fm.frac[MUSCLE] * activity(fm.b_act) } else { fm.legs } * fm.nv * sz.d2,
        drag: if sea { 0.0 } else { sz.wet * G * p.mu_ground },
        soft_area: fm.soft * sz.d2,
        key: bt.ckey,
    }
}

/// Tissue of `d` kg (dry, over all that press) fails on a body, into the carrion of the cell where they met: as
/// whole animals while it stands for more than one, the rest as a wound on those left. A body under half its
/// peak tissue is dead. Returns the animals killed and the kg that failed.
fn fail(b: &mut Body, car: &mut Carrion, vapor: &mut f64, area: f64, d: f64) -> (f64, f64) {
    let each = b.m + b.fat + b.c_m;
    let (mut animals, mut kg) = (0.0, 0.0);
    if b.s > 1.0 {
        let whole = (d / each).floor().min(b.s - 1.0);
        if whole > 0.0 {
            // with what each had just swallowed (e111, `meal`)
            let k = whole / area;
            car.m += (each + b.meal[0]) * k;
            car.a += (b.ta + b.pa + b.c_a + b.meal[1]) * k;
            car.b += (b.tb + b.pb + b.c_b + b.meal[2]) * k;
            car.kill += (each + b.meal[0]) * k;
            *vapor += (b.w + b.c_w) * k;
            b.s -= whole;
            animals = whole;
            kg = whole * each;
        }
    }
    let r = ((d - kg) / b.s).min(b.m);
    if r > 0.0 && b.m > 0.0 {
        let (q, k) = (r / b.m, b.s / area);
        let (dm, da, db) = (b.m * q, b.ta * q, b.tb * q);
        b.m -= dm;
        b.ta -= da;
        b.tb -= db;
        car.m += dm * k;
        car.a += da * k;
        car.b += db * k;
        car.kill += dm * k;
        kg += dm * b.s;
        if b.m < 0.5 * b.peak {
            b.dead = Death::Broken;
            animals += b.s;
        }
    }
    (animals, kg)
}

/// A compound enters a body, `dose` kg an animal: it harms by the distance of its key from the body's detox
/// keys (the leaf's law), and the tissue lost lies as carrion.
fn poison(b: &mut Body, bt: &BodyType, key: u8, dose: f64, p: &Params, car: &mut Carrion, area: f64) {
    if dose <= 0.0 || b.m <= 0.0 {
        return;
    }
    let best = bt.keys.iter().map(|&dk| hamming(key, dk)).min().unwrap_or(8) as f64;
    let harm = dose * 100.0 * (best - bt.tr[6]).max(0.0) / 8.0 * p.body_harm;
    if harm <= 0.0 {
        return;
    }
    b.harm += harm / b.m;
    let (q, k) = ((harm / b.m).min(0.5), b.s / area);
    let (dm, da, db) = (b.m * q, b.ta * q, b.tb * q);
    b.m -= dm;
    b.ta -= da;
    b.tb -= db;
    car.m += dm * k;
    car.a += da * k;
    car.b += db * k;
}

impl Bodies {
    pub fn new(ter: &Terrain, p: &Params) -> Self {
        let n = ter.n;
        let mut chunk_of_row = vec![0; n];
        for i in 0..CHUNKS {
            for y in n * i / CHUNKS..n * (i + 1) / CHUNKS {
                chunk_of_row[y] = i;
            }
        }
        Bodies {
            list: Vec::new(),
            types: Vec::new(),
            carrion: vec![Carrion::default(); n * n],
            next_id: 0,
            rng: Rng::new(p.life as u64 ^ 0xB0D1),
            sown: false,
            area: (p.cell_km * 1000.0).powi(2),
            cell_m: p.cell_km * 1000.0,
            wrap: p.edge <= 0.0,
            updates: 0,
            chunk_of_row,
            food: vec![0.0; n * n],
            flesh: vec![0.0; n * n],
            water: vec![0.0; n * n],
            head: vec![NONE; n * n],
            next: Vec::new(),
            trace: std::env::var("EVLOG_BODY_TRACE").ok().and_then(|v| v.parse().ok()).unwrap_or(0),
            secs: [0.0; 4],
            watched: false,
            died: Vec::new(),
            born: Vec::new(),
        }
    }

    pub fn k(&self, b: &Body) -> f64 {
        b.s / self.area
    }

    /// The first bodies: `body_founders` random genomes, `bodies0` bodies as grown adults, a share `sow_land` of
    /// them on random cells of land and the rest at sea, each standing for the whole animals nearest to `big_s`
    /// kg. Their A and B come from the soils and waters of the whole world, each cell giving in proportion to
    /// what it holds; their water from the air above them.
    pub fn sow(&mut self, p: &Params, ter: &Terrain, sa: &mut [f64], sb: &mut [f64], vapor: &mut [f64], year: u32) -> BFlux {
        let mut f = BFlux::default();
        for _ in 0..p.body_founders as usize {
            let g = crate::form::random(&mut self.rng);
            let mut bt = BodyType::new(g, NONE, year, p.b_comp);
            bt.root = self.types.len() as u32;
            self.types.push(Some(Box::new(bt)));
        }
        let n = ter.n;
        let (land, sea): (Vec<usize>, Vec<usize>) = (0..n * n).partition(|&c| !ter.sea[c]);
        let mut skip = [0usize; 3];
        let (tot_a, tot_b): (f64, f64) = (sa.iter().sum(), sb.iter().sum());
        let (mut need_a, mut need_b) = (0.0, 0.0);
        for _ in 0..p.bodies0 as usize {
            let g = self.rng.below(self.types.len()) as u32;
            let bt = self.types[g as usize].as_ref().unwrap();
            let fm = &bt.forms[STAGES - 1];
            let on_land = self.rng.f64() < p.sow_land;
            let from = if (on_land && !land.is_empty()) || sea.is_empty() { &land } else { &sea };
            let c = from[self.rng.below(from.len())];
            let (rx, ry) = (self.rng.f64(), self.rng.f64());
            let (seed, turn) = (self.rng.next_u64() | 1, TAU * self.rng.f64());
            if fm.nv == 0.0 {
                skip[0] += 1;
                continue;
            }
            let m = bt.adult();
            let s = (p.big_s / m).round().max(1.0);
            let k = s / self.area;
            let fat = 0.3 * m * (0.05 + p.fat_hold * fm.frac[FAT]);
            let (ta, tb) = (m * 1000.0 * fm.a, m * 1000.0 * fm.b);
            if need_a + ta * k > 0.1 * tot_a || need_b + tb * k > 0.1 * tot_b {
                skip[1] += 1;
                continue;
            }
            let w = m * (WET - 1.0);
            let wk = w * k;
            if wk > 0.5 * vapor[c] {
                skip[2] += 1;
                continue;
            }
            need_a += ta * k;
            need_b += tb * k;
            vapor[c] -= wk;
            f.fixed += (m + fat) * k;
            let (x, y) = (((c % n) as f64 + rx) * self.cell_m, ((c / n) as f64 + ry) * self.cell_m);
            let id = self.next_id;
            self.next_id += 1;
            self.list.push(Body::grown(id, g, (x, y), c as u32, turn, seed, m, s, fat, (ta, tb)));
        }
        let (qa, qb) = (1.0 - need_a / tot_a, 1.0 - need_b / tot_b);
        sa.iter_mut().for_each(|v| *v *= qa);
        sb.iter_mut().for_each(|v| *v *= qb);
        eprintln!("bodies sown: {} (no form {}, no soil {}, no water {})", self.list.len(), skip[0], skip[1], skip[2]);
        self.sown = true;
        f
    }

    /// A reading by injection (#130): `inject_bodies` grown bodies of one designed genome (`form::designed`), each
    /// at the place of a body standing on land, taken in the list's order at even steps. Their A and B come from
    /// the soils of the whole world and their water from the air above them, as the sown bodies' did. The world's
    /// own chance is not drawn, so a run with an injection is its control until that year.
    pub fn inject(&mut self, p: &Params, ter: &Terrain, sa: &mut [f64], sb: &mut [f64], vapor: &mut [f64], year: u32) -> BFlux {
        let mut f = BFlux::default();
        let mut bt = BodyType::new(crate::form::designed(p.inject_kind != 2.0, p.inject_kind == 3.0), NONE, year, p.b_comp);
        let g = self.types.len() as u32;
        bt.root = g;
        let fm = bt.forms[STAGES - 1].clone();
        let m = bt.adult();
        eprintln!(
            "designed body {g}: adult {m:.2} kg, voxels {}, frame {:.2} muscle {:.2} gut {:.2} fat {:.2}, legs {:.3}, bite {:.3}, mouth {:.2}, tip {:.2}, pull {:?}, press {:?}",
            fm.nv, fm.frac[FRAME], fm.frac[MUSCLE], fm.frac[GUT], fm.frac[FAT], fm.legs, fm.bite, fm.mouth, fm.face_tip[FRONT], bt.bev[0], bt.bev[1]
        );
        self.types.push(Some(Box::new(bt)));
        let at: Vec<usize> = (0..self.list.len()).filter(|&i| !ter.sea[self.list[i].cell as usize]).collect();
        let want = (p.inject_bodies as usize).min(at.len());
        let mut rng = Rng::new(p.life as u64 ^ 0x1A7E_C7ED);
        let s = (p.big_s / m).round().max(1.0);
        let k = s / self.area;
        let (tot_a, tot_b): (f64, f64) = (sa.iter().sum(), sb.iter().sum());
        let (mut need_a, mut need_b) = (0.0, 0.0);
        for q in 0..want {
            let (x, y, c) = {
                let o = &self.list[at[q * at.len() / want]];
                (o.x, o.y, o.cell)
            };
            let w = m * (WET - 1.0);
            if w * k > 0.5 * vapor[c as usize] {
                continue;
            }
            vapor[c as usize] -= w * k;
            let fat = 0.3 * m * (0.05 + p.fat_hold * fm.frac[FAT]);
            let (ta, tb) = (m * 1000.0 * fm.a, m * 1000.0 * fm.b);
            need_a += ta * k;
            need_b += tb * k;
            f.fixed += (m + fat) * k;
            let id = self.next_id;
            self.next_id += 1;
            self.list.push(Body::grown(id, g, (x, y), c, TAU * rng.f64(), rng.next_u64() | 1, m, s, fat, (ta, tb)));
        }
        let (qa, qb) = (1.0 - need_a / tot_a, 1.0 - need_b / tot_b);
        sa.iter_mut().for_each(|v| *v *= qa);
        sb.iter_mut().for_each(|v| *v *= qb);
        eprintln!("designed bodies put in: {} of {want}, {s} animals each", self.list.iter().filter(|b| b.g == g).count());
        f
    }

    /// What each cell offers the senses, and the carrion's rot into the litter over `days`. Once a climate
    /// update, before the bodies' own.
    pub fn fields(&mut self, wd: &mut World, days: f64) -> BFlux {
        let p = wd.p;
        let cells = wd.ter.n * wd.ter.n;
        let threads = (if p.body_threads > 0.0 { p.body_threads } else { p.threads }) as usize;
        let (food, flesh, water, car, lit) = (Shared::new(&mut self.food), Shared::new(&mut self.flesh), Shared::new(&mut self.water), Shared::new(&mut self.carrion), Shared::new(&mut *wd.lit));
        let (co, bank, ground, ter, temp) = (&*wd.co, &*wd.bank, &*wd.ground, wd.ter, wd.temp);
        let rot: f64 = par::pieces(threads, cells, |lo, hi| {
            let mut rotted = 0.0;
            for c in lo..hi {
                let (x, l) = (car.at(c), lit.at(c));
                if x.m > 0.0 {
                    let q = if x.m < 1e-12 { 1.0 } else { 1.0 - (-p.carrion_rot * q10(temp[c]) * days).exp() };
                    l.m += x.m * q;
                    l.a += x.a * q;
                    l.b += x.b * q;
                    rotted += x.m * q;
                    x.m *= 1.0 - q;
                    x.a *= 1.0 - q;
                    x.b *= 1.0 - q;
                    x.kill *= 1.0 - q;
                }
                let mut fsum = if p.eat_litter > 0.0 { l.m } else { 0.0 };
                for i in 0..K {
                    let y = &co[c * K + i];
                    if y.g != NONE && y.h < 2.0 {
                        fsum += y.o[LEAF].m + y.o[SEED].m;
                    }
                }
                if p.eat_bank > 0.0 && p.reach == 0.0 {
                    for j in 0..BANK {
                        fsum += bank[c * BANK + j].m;
                    }
                }
                *food.at(c) = fsum;
                *flesh.at(c) = x.m;
                *water.at(c) = if ter.sea[c] { 0.0 } else { (ground[c] / ter.cap[c]).min(2.0) };
            }
            rotted
        })
        .iter()
        .sum();
        BFlux { rotted: rot, ..BFlux::default() }
    }

    /// One update of `ticks` steps: the four passes of the module's head.
    pub fn update(&mut self, wd: &mut World, ticks: f64) -> BFlux {
        let p = wd.p;
        let n = wd.ter.n;
        let threads = (if p.body_threads > 0.0 { p.body_threads } else { p.threads }) as usize;
        let dt = ticks / p.day;
        let dts = dt * 86400.0;
        let season = TAU * wd.step / p.year;
        let nb = self.list.len();
        self.updates += 1;
        let mut f = BFlux::default();

        // 1. Every body senses and chooses.
        let t0 = std::time::Instant::now();
        self.next.clear();
        self.next.resize(nb, NONE);
        for (i, b) in self.list.iter().enumerate().rev() {
            self.next[i] = self.head[b.cell as usize];
            self.head[b.cell as usize] = i as u32;
        }
        let plans: Vec<Plan> = {
            let ax = Sense {
                p,
                ter: wd.ter,
                light: wd.light,
                types: &self.types,
                bodies: &self.list,
                head: &self.head,
                next: &self.next,
                food: &self.food,
                flesh: &self.flesh,
                water: &self.water,
                cell_m: self.cell_m,
                wrap: self.wrap,
                salt: self.updates,
                dts,
                season_sin: season.sin(),
                season_cos: season.cos(),
            };
            par::pieces(threads, nb, |lo, hi| (lo..hi).map(|i| decide(&ax, i)).collect::<Vec<Plan>>()).into_iter().flatten().collect()
        };
        for b in &self.list {
            self.head[b.cell as usize] = NONE;
        }
        let t1 = std::time::Instant::now();

        // 2. Bodies meet, and every body is moved.
        self.meet(wd, &plans, dts, &mut f);
        let t2 = std::time::Instant::now();

        // 3. Every body lives where it stands: the bodies of each chunk of rows, in their order in the list.
        let mut by_chunk: Vec<Vec<usize>> = vec![Vec::new(); CHUNKS];
        for (i, b) in self.list.iter().enumerate() {
            by_chunk[self.chunk_of_row[b.cell as usize / n]].push(i);
        }
        let ctx = Ctx { p, ter: wd.ter, temp: wd.temp, sat: wd.sat, types: &self.types, gen: wd.gen, area: self.area, trace: self.trace, dt };
        let sh = Sh {
            bodies: Shared::new(&mut self.list),
            co: Shared::new(&mut *wd.co),
            lit: Shared::new(&mut *wd.lit),
            bank: Shared::new(&mut *wd.bank),
            sa: Shared::new(&mut *wd.sa),
            sb: Shared::new(&mut *wd.sb),
            vapor: Shared::new(&mut *wd.vapor),
            ground: Shared::new(&mut *wd.ground),
            car: Shared::new(&mut self.carrion),
        };
        let fl: Vec<BFlux> = par::over(threads, &by_chunk, |list| {
            let mut f = BFlux::default();
            for &i in list {
                live(&ctx, &sh, i, &mut f);
            }
            f
        });
        for x in &fl {
            f.add(x);
        }
        let t3 = std::time::Instant::now();

        // 4. In order: the dead, the eggs, the splits.
        let old = std::mem::take(&mut self.list);
        let mut out = Vec::with_capacity(old.len() + 64);
        for mut b in old {
            let k = b.s / self.area;
            let c = b.cell as usize;
            if b.lay {
                self.hatch(p, &mut b, &mut out, wd.year, &mut f);
            }
            if b.dead != Death::None {
                let x = &mut self.carrion[c];
                x.m += (b.m + b.fat + b.c_m) * k;
                x.a += (b.ta + b.pa + b.c_a) * k;
                x.b += (b.tb + b.pb + b.c_b) * k;
                if b.dead == Death::Broken {
                    x.kill += (b.m + b.fat + b.c_m) * k;
                }
                x.m += b.meal[0] * k;
                x.a += b.meal[1] * k;
                x.b += b.meal[2] * k;
                x.kill += b.meal[0] * k;
                wd.vapor[c] += (b.w + b.c_w) * k;
                f.deaths[b.dead as usize - 1] += 1.0;
                if self.watched {
                    self.died.push((b.id as u32, b.dead as u8 - 1));
                }
                continue;
            }
            let bt = self.types[b.g as usize].as_ref().unwrap();
            if b.m * b.s > 2.0 * p.big_s && b.s >= 2.0 && bt.forms[b.stage as usize].nv > 0.0 {
                // Over twice the grain: two bodies at one place, each for half the animals, each its own way.
                let mut twin = b.clone();
                twin.s = (b.s / 2.0).floor();
                b.s -= twin.s;
                twin.id = self.next_id;
                self.next_id += 1;
                twin.seed = self.rng.next_u64() | 1;
                f.splits += 1.0;
                if self.watched {
                    self.born.push((twin.id as u32, b.id as u32));
                }
                out.push(b);
                out.push(twin);
                continue;
            }
            out.push(b);
        }
        self.list = out;
        let t4 = std::time::Instant::now();
        for (s, d) in self.secs.iter_mut().zip([t1 - t0, t2 - t1, t3 - t2, t4 - t3]) {
            *s += d.as_secs_f64();
        }
        f
    }

    /// Bodies meet. A chaser follows the body it heads for all through the update; with speed `v` after one
    /// going its own way at `u`, `gap` apart, it arrives after `gap (v + u cos a) / (v^2 - u^2)` when it is the
    /// faster (`a`: the angle of the other's way off the line between them), after `gap / (v + u)` when each
    /// heads for the other. The catches that fall inside the update are taken in the order of their times, each
    /// a contact; then every body is moved to where its update ends, and pays its way.
    fn meet(&mut self, wd: &mut World, plans: &[Plan], dts: f64, f: &mut BFlux) {
        let p = wd.p;
        let n = wd.ter.n;
        let nb = self.list.len();
        let mut catches: Vec<(f64, u32, u32)> = Vec::new();
        for (i, pl) in plans.iter().enumerate() {
            if !pl.chase || pl.tgt == NONE {
                continue;
            }
            let j = pl.tgt as usize;
            let (bi, bj, pj) = (&self.list[i], &self.list[j], &plans[j]);
            let (dx, dy) = (bj.x - bi.x, bj.y - bi.y);
            let d0 = (dx * dx + dy * dy).sqrt();
            let gap = (d0 - 0.5 * (pl.len + pj.len)).max(0.0);
            let (v, u) = (pl.v, pj.v);
            let t = if gap == 0.0 {
                0.0
            } else if pj.chase && pj.tgt == i as u32 {
                gap / (v + u).max(1e-9)
            } else if v > u {
                let cosa = if u > 1e-9 { (pj.vx * dx + pj.vy * dy) / (u * d0) } else { 0.0 };
                gap * (v + u * cosa) / (v * v - u * u)
            } else {
                f64::INFINITY
            };
            if t <= dts {
                catches.push((t, i as u32, j as u32));
            }
        }
        catches.sort_by(|a, b| a.0.partial_cmp(&b.0).unwrap().then(a.1.cmp(&b.1)));
        // When a body stops moving (held, or standing at its catch), where a catcher ends, and whom a rider rides.
        let mut stop = vec![f64::INFINITY; nb];
        let mut end: Vec<Option<(f64, f64)>> = vec![None; nb];
        let mut rides = vec![NONE; nb];
        let mut pressed = vec![0.0f64; nb]; // J each of its animals' fronts worked
        for b in self.list.iter_mut() {
            b.smother = 0.0;
        }
        for &(t, i, j) in &catches {
            let (i, j) = (i as usize, j as usize);
            if self.list[i].dead != Death::None || self.list[j].dead != Death::None || stop[i] < t {
                continue;
            }
            f.catches += 1.0;
            let (pi, pj) = (&plans[i], &plans[j]);
            // where they meet: where the chased is at that time
            let tj = t.min(stop[j]);
            let (cx, cy) = self.hold(self.list[j].x + pj.vx * tj, self.list[j].y + pj.vy * tj, n);
            let c = self.cell_of(cx, cy, n);
            stop[i] = t;
            end[i] = Some((cx, cy));
            if !pi.press {
                continue;
            }
            f.presses += 1.0;
            // the face met: its front if it came on, its back if it was going away, else a side
            let (dx, dy) = (self.list[j].x - self.list[i].x, self.list[j].y - self.list[i].y);
            let d0 = (dx * dx + dy * dy).sqrt();
            let (ux, uy) = if d0 > 1e-9 { (dx / d0, dy / d0) } else { (pi.hx, pi.hy) };
            let away = pj.hx * ux + pj.hy * uy;
            let face = if (pj.chase && pj.tgt == i as u32) || away < -0.5 { FRONT } else if away > 0.5 { BACK } else { FLANK };
            let (sea_i, sea_j) = (wd.ter.sea[self.list[i].cell as usize], wd.ter.sea[self.list[j].cell as usize]);
            let a = phys(p, &self.list[i], self.types[self.list[i].g as usize].as_ref().unwrap(), sea_i, pi.v_top, dts / 86400.0);
            let b = phys(p, &self.list[j], self.types[self.list[j].g as usize].as_ref().unwrap(), sea_j, pj.v_top, dts / 86400.0);
            let breaks = a.pressure > b.need[face];
            // a tip harder than the catcher's front returns the same force over its own area
            let hurt = b.hard[face] > a.hard[FRONT] && a.force * (0.1 + 0.9 * b.hard[face]) / b.tip_area[face].max(1e-30) > a.need[FRONT];
            // can the pressed leave? not if it is the slower; and glue anchors it, or lets the catcher ride
            let mut held = b.v_top <= a.v_top;
            let mut rider = false;
            if a.grip > 0.0 {
                if b.pull <= a.grip.min(a.drag) {
                    held = true;
                } else if a.grip >= a.drag {
                    rider = true;
                }
            }
            let bite = ((a.len + b.len) / (a.v_top + b.v_top).max(1e-3)).min(dts - t);
            let tau = if (held || rider) && !hurt { dts - t } else { bite };
            let area = self.area;
            let car = &mut self.carrion[c];
            if breaks {
                f.breaks += 1.0;
                let total = (self.list[j].m + self.list[j].fat) * b.s;
                let mut d = (a.power / b.need[face] * tau * 1000.0 / WET).min(total);
                // e111, a press is a bite: the front breaks only what its gut takes in, and swallows it; the part
                // of it that is no mouth breaks its own tip's mass in a pass, which falls as carrion
                let mut swallow = 0.0;
                if p.bite > 0.0 {
                    swallow = (a.mouth * d).min(a.room);
                    d = swallow + ((1.0 - a.mouth) * d).min((1.0 - a.mouth) * a.tip_mass[FRONT] * a.s);
                }
                let mut fell = Carrion::default();
                let (animals, kg) = fail(&mut self.list[j], &mut fell, &mut wd.vapor[c], area, d);
                let q = if kg > 0.0 { (swallow / kg).min(1.0) } else { 0.0 };
                if q > 0.0 {
                    let each = q * area / a.s; // an animal's share of what was swallowed
                    let me = &mut self.list[i];
                    me.meal[0] += fell.m * each;
                    me.meal[1] += fell.a * each;
                    me.meal[2] += fell.b * each;
                }
                car.m += fell.m * (1.0 - q);
                car.a += fell.a * (1.0 - q);
                car.b += fell.b * (1.0 - q);
                car.kill += fell.kill * (1.0 - q);
                f.killed += animals;
                f.torn += kg / area;
                self.list[i].kills += animals;
                // the compound in the tissue at the contact, on both sides, enters the other
                let (bti, btj) = (self.types[self.list[i].g as usize].as_ref().unwrap(), self.types[self.list[j].g as usize].as_ref().unwrap());
                if self.list[j].dead == Death::None {
                    let dose = a.cmp[FRONT] * a.tip_mass[FRONT] * a.s / self.list[j].s;
                    poison(&mut self.list[j], btj, a.key, dose, p, car, area);
                }
                poison(&mut self.list[i], bti, b.key, b.cmp[face] * kg / a.s, p, car, area);
            }
            if hurt {
                let total = (self.list[i].m + self.list[i].fat) * a.s;
                let d = (a.power / a.need[FRONT] * bite * 1000.0 / WET).min(total);
                let (_, kg) = fail(&mut self.list[i], car, &mut wd.vapor[c], area, d);
                f.torn += kg / area;
                let bti = self.types[self.list[i].g as usize].as_ref().unwrap();
                if self.list[i].dead == Death::None {
                    let dose = b.cmp[face] * b.tip_mass[face] * b.s / self.list[i].s;
                    poison(&mut self.list[i], bti, b.key, dose, p, car, area);
                }
            }
            pressed[i] = a.power / a.s * tau;
            if (held || rider) && !hurt {
                if rider {
                    rides[i] = j as u32;
                    f.riders += 1.0;
                } else {
                    stop[j] = stop[j].min(t);
                }
                if sea_j && a.glue_area > 0.0 {
                    self.list[j].smother = (a.glue_area * a.s / (b.soft_area * b.s).max(1e-30)).min(1.0);
                }
            }
        }
        // Every body goes to where its update ends: along its way for the time it was free; a catcher to its
        // catch; a chaser that did not arrive towards where the other ends; a rider with its carrier.
        let lin = |list: &[Body], k: usize, t: f64| (list[k].x + plans[k].vx * t, list[k].y + plans[k].vy * t);
        let mut to: Vec<(f64, f64, f64)> = Vec::with_capacity(nb); // x, y, the seconds it moved
        for i in 0..nb {
            let pl = &plans[i];
            let b = &self.list[i];
            to.push(if let Some((x, y)) = end[i] {
                (x, y, stop[i])
            } else if pl.chase && pl.tgt != NONE {
                let j = pl.tgt as usize;
                let (jx, jy) = lin(&self.list, j, dts.min(stop[j]));
                let (dx, dy) = (jx - b.x, jy - b.y);
                let d = (dx * dx + dy * dy).sqrt();
                let go = (pl.v * dts).min((d - 0.5 * (pl.len + plans[j].len)).max(0.0));
                if d > 1e-9 { (b.x + dx / d * go, b.y + dy / d * go, dts) } else { (b.x, b.y, dts) }
            } else {
                let t = dts.min(stop[i]);
                let (x, y) = lin(&self.list, i, t);
                (x, y, t)
            });
        }
        for i in 0..nb {
            if rides[i] != NONE {
                let j = rides[i] as usize;
                to[i] = (to[j].0, to[j].1, to[i].2);
            }
        }
        for i in 0..nb {
            let pl = &plans[i];
            let (x, y) = self.hold(to[i].0, to[i].1, n);
            let nc = self.cell_of(x, y, n);
            let b = &mut self.list[i];
            b.hx = pl.hx;
            b.hy = pl.hy;
            b.wa = pl.wa;
            b.breed = pl.breed;
            b.v_top = pl.v_top;
            b.reach = pl.reach;
            b.path = 0.0;
            // work: its propulsion for the time it moved, and its front's muscle for the time it pressed
            b.work = (pl.power * pl.act * to[i].2 + pressed[i]) / ENERGY;
            if b.dead != Death::None {
                continue;
            }
            let c = b.cell as usize;
            // a climb is paid by the mass lifted; a body that cannot pay stays (a rider is carried)
            let rise = (wd.ter.air[nc] - wd.ter.air[c]).max(0.0);
            let climb = if rides[i] != NONE { 0.0 } else { b.wet() * G * rise / ENERGY };
            if climb > 0.0 && climb >= b.fat {
                continue;
            }
            b.work += climb;
            // its path: the straight way, or a catcher's curve after the body it followed
            let (dx, dy) = (x - b.x, y - b.y);
            b.path = if rides[i] != NONE {
                0.0
            } else if end[i].is_some() {
                pl.v * to[i].2
            } else {
                (dx * dx + dy * dy).sqrt()
            };
            b.travel += b.path;
            f.moved += b.path / 1000.0;
            b.x = x;
            b.y = y;
            b.cell = nc as u32;
        }
    }

    /// A place held inside the world: the border is sea (or the world wraps, as a planet).
    fn hold(&self, x: f64, y: f64, n: usize) -> (f64, f64) {
        let side = n as f64 * self.cell_m;
        if self.wrap { (x.rem_euclid(side), y.rem_euclid(side)) } else { (x.clamp(0.0, side - 1e-6), y.clamp(0.0, side - 1e-6)) }
    }

    fn cell_of(&self, x: f64, y: f64, n: usize) -> usize {
        ((y / self.cell_m) as usize).min(n - 1) * n + ((x / self.cell_m) as usize).min(n - 1)
    }

    /// A clutch is laid and hatches as one brood at its parent's place, standing for all its eggs; it carries a
    /// mutation with chance `body_mut`.
    fn hatch(&mut self, p: &Params, b: &mut Body, out: &mut Vec<Body>, year: u32, f: &mut BFlux) {
        let eggs = b.carry;
        (b.carry, b.c_m, b.c_a, b.c_b, b.c_w, b.lay) = (0.0, 0.0, 0.0, 0.0, 0.0, false);
        let mut g = b.g;
        if self.rng.f64() < p.body_mut {
            let parent = self.types[b.g as usize].as_ref().unwrap();
            let (genes, root) = (genome::mutate(&parent.genes, &mut self.rng), parent.root);
            let mut bt = BodyType::new(genes, b.g, year, p.b_comp);
            bt.root = root;
            self.types.push(Some(Box::new(bt)));
            g = (self.types.len() - 1) as u32;
        }
        // what the parent carried, for each animal of the brood: tissue, yolk, A, B and water (taken in `live`),
        // built at the parent's shares
        let bt = self.types[b.g as usize].as_ref().unwrap();
        let (fa, fb, e) = (bt.forms[0].a, bt.forms[0].b, bt.egg());
        let id = self.next_id;
        self.next_id += 1;
        out.push(Body {
            id,
            g,
            x: b.x,
            y: b.y,
            hx: b.hx,
            hy: b.hy,
            wa: b.wa,
            cell: b.cell,
            m: e,
            ta: e * 1000.0 * fa,
            tb: e * 1000.0 * fb,
            fat: e * p.yolk,
            pa: 0.0,
            pb: 0.0,
            w: e * (WET - 1.0),
            s: eggs * b.s,
            peak: e,
            age: 0.0,
            stage: 0,
            t: b.t,
            harm: 0.0,
            seed: self.rng.next_u64() | 1,
            bx: b.x,
            by: b.y,
            travel: 0.0,
            eaten: [0.0; 6],
            kills: 0.0,
            dead: Death::None,
            carry: 0.0,
            c_m: 0.0,
            c_a: 0.0,
            c_b: 0.0,
            c_w: 0.0,
            lay: false,
            meal: [0.0; 3],
            path: 0.0,
            work: 0.0,
            smother: 0.0,
            breed: false,
            v_top: 0.0,
            reach: 0.0,
        });
        f.births += 1.0;
        if self.watched {
            self.born.push((id as u32, b.id as u32));
        }
    }

    /// Genotypes no body carries are dropped (their ids stay unique).
    pub fn collect(&mut self) -> usize {
        let mut live = vec![false; self.types.len()];
        for b in &self.list {
            live[b.g as usize] = true;
        }
        for (t, l) in self.types.iter_mut().zip(&live) {
            if !l {
                *t = None;
            }
        }
        live.iter().filter(|&&l| l).count()
    }

    /// A row a body genotype alive: its bodies, the animals and matter they stand for, its traits and adult form,
    /// where its bodies are, what they have eaten and whom they pull towards and press.
    pub fn census(&self, out: &mut impl std::io::Write, ter: &Terrain, year: usize) {
        let ng = self.types.len();
        #[derive(Default, Clone)]
        struct Acc {
            n: u32,
            animals: f64,
            matter: f64,
            mass: f64,
            sea: f64,
            v_top: f64,
            reach: f64,
            travel: f64,
            from_birth: f64,
            eaten: [f64; 6],
            kills: f64,
            cells: Vec<u32>,
        }
        let mut acc = vec![Acc::default(); ng];
        for b in &self.list {
            let a = &mut acc[b.g as usize];
            a.n += 1;
            a.animals += b.s;
            a.matter += (b.m + b.fat) * b.s;
            a.mass += b.m * b.s;
            if ter.sea[b.cell as usize] {
                a.sea += b.s;
            }
            a.v_top += b.v_top;
            a.reach += b.reach;
            a.travel += b.travel / 1000.0 / (b.age / 365.0).max(0.1);
            a.from_birth += ((b.x - b.bx).powi(2) + (b.y - b.by).powi(2)).sqrt() / 1000.0;
            for k in 0..6 {
                a.eaten[k] += b.eaten[k] * b.s;
            }
            a.kills += b.kills;
            a.cells.push(b.cell);
        }
        for (g, a) in acc.iter_mut().enumerate() {
            if a.n == 0 {
                continue;
            }
            a.cells.sort_unstable();
            a.cells.dedup();
            let bt = self.types[g].as_ref().unwrap();
            let fm = &bt.forms[STAGES - 1];
            let et: f64 = a.eaten.iter().sum::<f64>().max(1e-30);
            let keys: Vec<String> = bt.keys.iter().map(|k| format!("{k:02x}")).collect();
            let nf = a.n as f64;
            let none = |v: u32| v as i64 - if v == NONE { u32::MAX as i64 + 1 } else { 0 };
            write!(
                out,
                "{year},{g},{},{},{},{},{},{:.4e},{:.4e},{:.4e},{:.4e},{:.4e},{:.3},{:.3},{:.2},{:.2},{:.3},{},{},{:02x},{},{:.0},{:.3},{:.3},{:.3},{:.3},{:.3},{:.3},{:.4},{:.4},{:.4},{:.3},{:.3},{:.3},{:.3},{:.2},{:.3},{:.2},{:.3},{:.3},{:.3},{:.3},{:.3},{:.3},{},{},{},{:.3},{:.3},{:.1},{:.2},{:.3},{:.3},{:.3},{:.3},{:.3},{:.3},{:.3},{:.1}",
                none(bt.parent),
                none(bt.root),
                bt.born,
                bt.genes.len(),
                a.n,
                a.animals,
                a.matter,
                a.mass / a.animals,
                bt.adult(),
                bt.egg(),
                bt.tr[2],
                bt.tr[3],
                bt.tr[4],
                bt.tr[5],
                bt.tr[6],
                bt.keys.len(),
                keys.join("-"),
                bt.ckey,
                a.cells.len(),
                fm.nv,
                fm.frac[0], fm.frac[1], fm.frac[2], fm.frac[3], fm.frac[4], fm.frac[5],
                fm.a, fm.b, fm.cmp, fm.frame_tough, fm.density, fm.legs, fm.bite, fm.mouth, fm.eye, fm.glue,
                fm.face_hard[0], fm.face_hard[1], fm.face_hard[2], fm.face_tip[0], fm.face_tip[1], fm.face_tip[2],
                fm.ext[0], fm.ext[1], fm.ext[2],
                a.sea / a.animals,
                a.v_top / nf,
                a.reach / nf,
                a.travel / nf,
                a.from_birth / nf,
                a.eaten[0] / et, a.eaten[1] / et, a.eaten[2] / et, a.eaten[3] / et, a.eaten[4] / et, a.eaten[5] / et,
                a.kills
            )
            .unwrap();
            for row in &bt.bev {
                for v in row {
                    write!(out, ",{v:.3}").unwrap();
                }
            }
            writeln!(out).unwrap();
        }
    }

    /// A row a founder's line on an island (0: the sea): its bodies, animals and matter.
    pub fn lines(&self, out: &mut impl std::io::Write, island: &[u16], year: usize) {
        let mut acc: std::collections::BTreeMap<(u32, u16), (u32, f64, f64)> = std::collections::BTreeMap::new();
        for b in &self.list {
            let root = self.types[b.g as usize].as_ref().unwrap().root;
            let e = acc.entry((root, island[b.cell as usize])).or_default();
            e.0 += 1;
            e.1 += b.s;
            e.2 += (b.m + b.fat) * b.s;
        }
        for ((root, isle), (n, animals, matter)) in acc {
            writeln!(out, "{year},{root},{isle},{n},{animals},{matter:.4e}").unwrap();
        }
    }

    /// The bodies' matter and the carrion's (kg a m2 summed over cells), A and B (g), water (mm summed).
    pub fn totals(&self) -> (f64, f64, f64, f64) {
        let (mut m, mut a, mut b, mut w) = (0.0, 0.0, 0.0, 0.0);
        for x in &self.list {
            let k = self.k(x);
            m += (x.m + x.fat + x.c_m + x.meal[0]) * k;
            a += (x.ta + x.pa + x.c_a + x.meal[1]) * k;
            b += (x.tb + x.pb + x.c_b + x.meal[2]) * k;
            w += (x.w + x.c_w) * k;
        }
        for x in &self.carrion {
            m += x.m;
            a += x.a;
            b += x.b;
        }
        (m, a, b, w)
    }
}

/// What a body reads as it chooses.
struct Sense<'a> {
    p: &'a Params,
    ter: &'a Terrain,
    light: &'a [f64],
    types: &'a [Option<Box<BodyType>>],
    bodies: &'a [Body],
    head: &'a [u32],
    next: &'a [u32],
    food: &'a [f64],
    flesh: &'a [f64],
    water: &'a [f64],
    cell_m: f64,
    wrap: bool,
    salt: u64,
    dts: f64,
    season_sin: f64,
    season_cos: f64,
}

/// A vector no longer than one.
fn cap(v: (f64, f64)) -> (f64, f64) {
    let l = (v.0 * v.0 + v.1 * v.1).sqrt();
    if l > 1.0 { (v.0 / l, v.1 / l) } else { v }
}

/// What one body senses and chooses.
fn decide(x: &Sense, i: usize) -> Plan {
    let p = x.p;
    let b = &x.bodies[i];
    let mut pl = Plan { vx: 0.0, vy: 0.0, hx: b.hx, hy: b.hy, wa: b.wa, v: 0.0, v_top: 0.0, power: 0.0, act: 0.0, len: 0.0, reach: 0.0, tgt: NONE, chase: false, press: false, breed: false };
    let bt = x.types[b.g as usize].as_ref().unwrap();
    let fm = &bt.forms[b.stage as usize];
    if fm.nv == 0.0 || b.dead != Death::None {
        return pl;
    }
    let n = x.ter.n;
    let c = b.cell as usize;
    let sea = x.ter.sea[c];
    let sz = size(b, fm);
    let (t_opt, breadth) = (bt.tr[4], bt.tr[5]);
    let (v_top, power) = speed(p, fm, b.m, &sz, sea, heat_factor(b.t, t_opt, breadth));
    let light = x.light[c];
    // its reach: its eyes' side times the light, at least its own length, at most `sense_max`
    let reach = ((fm.eye * sz.d2).sqrt() * p.sense_k * (0.2 + 0.8 * (light / 0.5).min(1.0))).max(sz.len).min(p.sense_max);
    // which way the fields rise within its reach
    let side = n as f64 * x.cell_m;
    let at = |dx: f64, dy: f64| {
        let (px, py) = if x.wrap { ((b.x + dx).rem_euclid(side), (b.y + dy).rem_euclid(side)) } else { ((b.x + dx).clamp(0.0, side - 1e-6), (b.y + dy).clamp(0.0, side - 1e-6)) };
        ((py / x.cell_m) as usize).min(n - 1) * n + ((px / x.cell_m) as usize).min(n - 1)
    };
    let (ce, cw, cs, cn) = (at(reach, 0.0), at(-reach, 0.0), at(0.0, reach), at(0.0, -reach));
    let fd = |v: f64| ((v.max(1e-6)).log10() + 3.0) / 3.0;
    let u_food = cap((fd(x.food[ce]) - fd(x.food[cw]), fd(x.food[cs]) - fd(x.food[cn])));
    let u_flesh = cap((fd(x.flesh[ce]) - fd(x.flesh[cw]), fd(x.flesh[cs]) - fd(x.flesh[cn])));
    let u_water = cap((x.water[ce] - x.water[cw], x.water[cs] - x.water[cn]));
    let u_down = cap(((x.ter.air[cw] - x.ter.air[ce]) / 50.0, (x.ter.air[cn] - x.ter.air[cs]) / 50.0)); // a fall of 50 m is a full pull
    // the nearest bodies within its reach: the cells around its own, ring by ring, until none farther can be nearer
    let mut seen = [(f64::MAX, NONE); SEE];
    let rmax = (reach / x.cell_m).ceil() as i64;
    let (cx, cy) = ((c % n) as i64, (c / n) as i64);
    for r in 0..=rmax {
        for yy in (cy - r).max(0)..=(cy + r).min(n as i64 - 1) {
            let rim = yy == cy - r || yy == cy + r;
            let mut xx = cx - r;
            while xx <= cx + r {
                if xx >= 0 && xx < n as i64 {
                    let mut j = x.head[yy as usize * n + xx as usize];
                    while j != NONE {
                        let o = &x.bodies[j as usize];
                        let d2 = (o.x - b.x).powi(2) + (o.y - b.y).powi(2);
                        if j as usize != i && d2 <= reach * reach && o.dead == Death::None {
                            let mut e = (d2, j);
                            for slot in seen.iter_mut() {
                                if e.0 < slot.0 || (e.0 == slot.0 && e.1 < slot.1) {
                                    std::mem::swap(&mut e, slot);
                                }
                            }
                        }
                        j = x.next[j as usize];
                    }
                }
                xx += if rim || r == 0 { 1 } else { 2 * r };
            }
        }
        if seen[SEE - 1].1 != NONE && seen[SEE - 1].0 <= (r as f64 * x.cell_m).powi(2) {
            break;
        }
    }
    // each of them pulls it, towards or away, and it would press it or not: the body evaluator
    let fat_cap = b.m * (0.05 + p.fat_hold * fm.frac[FAT]);
    let fill = (b.fat / fat_cap.max(1e-30)).min(2.0);
    let (mut best, mut best_pull, mut best_press, mut count) = (NONE, 0.0f64, false, 0.0);
    for &(d2, j) in &seen {
        if j == NONE {
            break;
        }
        count += 1.0;
        let o = &x.bodies[j as usize];
        let d = d2.sqrt();
        let alike = if o.g == b.g {
            1.0
        } else if x.types[o.g as usize].as_ref().unwrap().parent == b.g || bt.parent == o.g {
            0.5
        } else {
            0.0
        };
        let coming = if d > 1e-9 { (o.hx * (b.x - o.x) + o.hy * (b.y - o.y)) / d } else { 0.0 };
        let feat = [1.0, ((o.m / b.m).log10() / 3.0).clamp(-1.0, 1.0), alike, fill, 1.0 - d / reach, coming];
        let pull: f64 = (0..NB).map(|q| bt.bev[0][q] * feat[q]).sum();
        if pull.abs() > best_pull.abs() {
            best = j;
            best_pull = pull;
            best_press = (0..NB).map(|q| bt.bev[1][q] * feat[q]).sum::<f64>() > 0.0;
        }
    }
    // the controller: what it reads of itself and its place gives a weight to each way it senses
    let mut inp = [0.0; NI];
    inp[0] = 1.0;
    inp[1] = fill;
    inp[2] = (b.w / b.target_water()).min(2.0);
    inp[3] = b.harm.min(1.0);
    inp[4] = ((b.t - t_opt) / breadth).clamp(-2.0, 2.0) / 2.0;
    inp[5] = b.stage as f64 / (STAGES - 1) as f64;
    inp[6] = (light / 0.5).min(1.0);
    let ls = if x.ter.lat[c / n] >= 0.0 { 1.0 } else { -1.0 };
    inp[7] = x.season_sin * ls;
    inp[8] = x.season_cos * ls;
    inp[9] = fd(x.food[c]);
    inp[10] = x.water[c];
    inp[11] = if sea { 1.0 } else { 0.0 };
    inp[12] = fd(x.flesh[c]);
    inp[13] = (-best_pull).max(0.0).min(4.0);
    inp[14] = best_pull.max(0.0).min(4.0);
    inp[15] = count / SEE as f64;
    let mut out = [0.0; NO];
    for o in 0..NO {
        let w = &bt.w[o];
        out[o] = (0..NI).map(|j| w[j] * inp[j]).sum();
    }
    let act = 1.0 / (1.0 + (-(out[5] + ACT0)).exp());
    // chance turns it: an angle that wanders, keeping its way for about `turn_s` whatever the update's length
    let gauss = (-2.0 * (1.0 - chance(b.seed, x.salt)).ln()).sqrt() * (TAU * chance(b.seed ^ 0x5DEE_CE66, x.salt)).cos();
    pl.wa = (b.wa + (2.0 * x.dts / p.turn_s).sqrt() * gauss).rem_euclid(TAU);
    let (rx, ry) = (pl.wa.cos(), pl.wa.sin());
    let (mut sx, mut sy, mut strongest) = (rx, ry, 1.0f64); // a unit of chance
    for (w, u) in [(out[0], u_food), (out[1], u_flesh), (out[2], u_water), (out[3], u_down), (out[4], (b.hx, b.hy))] {
        sx += w * u.0;
        sy += w * u.1;
        strongest = strongest.max(w.abs() * (u.0 * u.0 + u.1 * u.1).sqrt());
    }
    if best != NONE && best_pull.abs() > strongest {
        // a body's pull is the strongest of all: straight for it, or straight away
        let o = &x.bodies[best as usize];
        let (dx, dy) = (o.x - b.x, o.y - b.y);
        let d = (dx * dx + dy * dy).sqrt();
        let (ux, uy) = if d > 1e-9 { (dx / d, dy / d) } else { (rx, ry) };
        pl.tgt = best;
        pl.chase = best_pull > 0.0;
        pl.press = pl.chase && best_press;
        let sign = if pl.chase { 1.0 } else { -1.0 };
        pl.hx = sign * ux;
        pl.hy = sign * uy;
    } else {
        let l = (sx * sx + sy * sy).sqrt();
        (pl.hx, pl.hy) = if l > 1e-9 { (sx / l, sy / l) } else { (rx, ry) };
    }
    pl.v_top = v_top;
    pl.v = v_top * act;
    pl.vx = pl.hx * pl.v;
    pl.vy = pl.hy * pl.v;
    pl.power = power;
    pl.act = act;
    pl.len = sz.len;
    pl.reach = reach;
    pl.breed = 1.0 + out[6] > 0.0; // with no genes, a body breeds when it can
    pl
}

struct Ctx<'a> {
    p: &'a Params,
    ter: &'a Terrain,
    temp: &'a [f64],
    sat: &'a crate::climate::Sat,
    types: &'a [Option<Box<BodyType>>],
    gen: &'a [Option<Box<genome::Genotype>>],
    area: f64,
    trace: u64,
    dt: f64, // days an update
}

struct Sh {
    bodies: Shared<Body>,
    co: Shared<Cohort>,
    lit: Shared<Litter>,
    bank: Shared<Seeds>,
    sa: Shared<f64>,
    sb: Shared<f64>,
    vapor: Shared<f64>,
    ground: Shared<f64>,
    car: Shared<Carrion>,
}

/// A food within reach: which it is, kg a m2 of it in the cell, its A and B shares, the pressure it takes, and
/// the harm of its compounds to this body a kg.
#[derive(Clone, Copy, Default)]
struct Food {
    kind: usize, // 0 leaf, 1 wood, 2 seed, 3 litter, 4 carrion
    src: usize,  // the cohort, or 100 + the bank slot
    dens: f64,   // within reach
    full: f64,   // all of it in the cell
    a: f64,
    b: f64,
    need: f64,
    tox: f64,
}

const MAX_FOODS: usize = 3 * K + BANK + 2;

/// One body's life over an update, where it stands.
fn live(x: &Ctx, sh: &Sh, i: usize, f: &mut BFlux) {
    let p = x.p;
    let b = sh.bodies.at(i);
    if b.dead != Death::None {
        return;
    }
    let bt = x.types[b.g as usize].as_ref().unwrap();
    let fm = &bt.forms[b.stage as usize];
    if fm.nv == 0.0 {
        b.dead = Death::Form;
        return;
    }
    let c = b.cell as usize;
    let sea = x.ter.sea[c];
    let k = b.s / x.area;
    let dt = x.dt;
    let dts = dt * 86400.0;
    let (t_opt, breadth) = (bt.tr[4], bt.tr[5]);
    let Size { wet, d, d2, height, .. } = size(b, fm);
    let fat_cap = b.m * (0.05 + p.fat_hold * fm.frac[FAT]);

    // Its heat: made by its upkeep, lost through its open surface (less through fat), cooled by water when hot.
    // It goes towards that balance at the pace its mass allows: a large body evens out the day, a small one
    // follows it.
    let t_env = x.temp[c];
    let bkg = b.tb / 1000.0;
    let upkeep_rate = p.body_resp * bkg * q10(b.t); // kg a day
    let skin = fm.open * d2 * (1.0 - 0.8 * fm.fat_skin / fm.open.max(1e-9));
    let h = if sea { p.heat_water } else { p.heat_air };
    let heat_w = upkeep_rate * ENERGY / 86400.0;
    let t_hi = t_opt + breadth;
    let t_eq = t_env + heat_w / (h * skin.max(1e-12));
    let tau = 3500.0 * wet / (h * skin.max(1e-12)); // s
    let mut tb = t_eq + (b.t - t_eq) * (-dts / tau).exp();
    let mut cool = 0.0;
    if tb > t_hi && !sea {
        // held at its limit by water carrying away what flows in, as far as its water allows
        let hot = tb;
        cool = h * skin * (t_eq - t_hi).max(0.0) * dts / LATENT;
        tb = t_hi;
        let can = (b.w - 0.5 * b.target_water()).max(0.0);
        if cool > can {
            tb = t_hi + (1.0 - can / cool) * (hot - t_hi);
            cool = can;
        }
    }
    b.t = tb;
    let ft = heat_factor(tb, t_opt, breadth);

    // Eating: what is within reach where it stands, whether the mouth can break it, and whether the body takes it.
    let mut foods = [Food::default(); MAX_FOODS];
    let mut nf = 0;
    let pressure = p.muscle_stress * fm.bite;
    let tox_of = |cmp: f64, m: f64, gt: &genome::Pheno| -> f64 {
        if m < 1e-15 || gt.n_keys == 0 {
            return 0.0;
        }
        let dd = cmp / m;
        let mut t = 0.0;
        for kk in 0..gt.n_keys {
            let best = bt.keys.iter().map(|&dk| hamming(gt.keys[kk], dk)).min().unwrap_or(8) as f64;
            t += dd / gt.n_keys as f64 * (best - bt.tr[6]).max(0.0) / 8.0 / 0.01;
        }
        t
    };
    let need_of = |a: f64| p.bite_ref * (1.0 + p.bite_tough * toughness(a));
    {
        let floating = fm.density < 1.0;
        for j in 0..K {
            let y = sh.co.at(c * K + j);
            if y.g == NONE {
                continue;
            }
            // leaves and seeds hang from the ground to the stand's height: a short body reaches the share below it
            let reach = if sea { if floating { 1.0 } else { 0.0 } } else { (height / y.h.max(1e-3)).min(1.0) };
            let ph = &x.gen[y.g as usize].as_ref().unwrap().base;
            if reach > 0.0 && y.o[LEAF].m > 1e-12 {
                let o = y.o[LEAF];
                foods[nf] = Food { kind: 0, src: j, dens: o.m * reach, full: o.m, a: o.share_a(), b: o.share_b(), need: need_of(o.share_a()), tox: tox_of(y.cmp, o.m, ph) };
                nf += 1;
            }
            if reach > 0.0 && y.o[SEED].m > 1e-12 {
                let o = y.o[SEED];
                foods[nf] = Food { kind: 2, src: j, dens: o.m * reach, full: o.m, a: o.share_a(), b: o.share_b(), need: need_of(o.share_a()), tox: 0.0 };
                nf += 1;
            }
            // e111, reach: wood stands from the ground to the stand's height, as its leaves hang
            let wood_reach = if p.reach > 0.0 { reach } else { 1.0 };
            if !sea && p.eat_wood > 0.0 && wood_reach > 0.0 && y.o[WOOD].m > 1e-12 {
                let o = y.o[WOOD];
                foods[nf] = Food { kind: 1, src: j, dens: o.m * wood_reach, full: o.m, a: o.share_a(), b: o.share_b(), need: p.wood_hard * need_of(o.share_a()), tox: 0.0 };
                nf += 1;
            }
        }
        if !sea || !floating {
            // what lies on the ground, or on the sea's bottom
            let l = sh.lit.at(c);
            if l.m > 1e-12 && p.eat_litter > 0.0 {
                foods[nf] = Food { kind: 3, src: 0, dens: l.m, full: l.m, a: l.a / (l.m * 1000.0), b: l.b / (l.m * 1000.0), need: p.bite_ref, tox: 0.0 };
                nf += 1;
            }
            let e = sh.car.at(c);
            if e.m > 1e-12 {
                let ea = e.a / (e.m * 1000.0);
                foods[nf] = Food { kind: 4, src: 0, dens: e.m, full: e.m, a: ea, b: e.b / (e.m * 1000.0), need: need_of(ea), tox: 0.0 };
                nf += 1;
            }
        }
        // e111, reach: fallen seed lies in the ground, where a body on it does not reach
        if !sea && p.eat_bank > 0.0 && p.reach == 0.0 {
            for j in 0..BANK {
                let e = sh.bank.at(c * BANK + j);
                if e.g != NONE && e.m > 1e-12 {
                    let ea = e.a / (e.m * 1000.0);
                    foods[nf] = Food { kind: 2, src: 100 + j, dens: e.m, full: e.m, a: ea, b: e.b / (e.m * 1000.0), need: need_of(ea), tox: 0.0 };
                    nf += 1;
                }
            }
        }
    }
    let mouth_w = fm.mouth.sqrt() * d; // m
    let gut_cap = gut_cap(p, fm, b.m, dt, ft); // kg this update
    let retention = fm.frac[GUT] / (fm.frac[GUT] + p.retain);
    let eff = p.assim / (1.0 + 0.1 * bt.keys.len() as f64);
    let fill_share = (b.fat / fat_cap.max(1e-30)).min(2.0);
    let sweep = mouth_w * b.path.max(d); // m2 swept (a body standing still still reaches what is under it)
    let fd = |v: f64| ((v.max(1e-6)).log10() + 3.0) / 3.0;
    let mut want = [0.0; MAX_FOODS];
    let mut total = 0.0;
    for (j, fo) in foods[..nf].iter().enumerate() {
        let bite = 1.0 / (1.0 + (fo.need / pressure.max(1.0)).powi(4));
        let feat = [1.0, fo.b / 0.03, bite, fo.tox, fd(fo.dens), fill_share];
        let s: f64 = 1.0 + (0..NE).map(|q| bt.eval[q] * feat[q]).sum::<f64>(); // with no genes, it takes all it can
        if s <= 0.0 || bite < 1e-3 {
            continue;
        }
        want[j] = fo.dens * bite * sweep;
        total += want[j];
    }
    // What it takes in: first the meal its front took from another body in this update's meeting (e111), then
    // what its mouth swept, as far as its gut has room. Each mouthful: kg, g of A, g of B, its kind, its harm, and
    // the food's A and B shares.
    let mut got = [(0.0f64, 0.0f64, 0.0f64, 0usize, 0.0f64, 0.0f64, 0.0f64); MAX_FOODS + 1];
    let mut ng = 0;
    let mut intake = 0.0;
    if b.meal[0] > 0.0 {
        got[ng] = (b.meal[0], b.meal[1], b.meal[2], 5, 0.0, b.meal[1] / (b.meal[0] * 1000.0), b.meal[2] / (b.meal[0] * 1000.0));
        ng += 1;
        intake += b.meal[0];
        f.eaten[5] += b.meal[0] * k;
        b.eaten[5] += b.meal[0];
        b.meal = [0.0; 3];
    }
    let room = (gut_cap - intake).max(0.0);
    if total > 0.0 && room > 0.0 {
        let scale = (room / total).min(1.0);
        for (j, fo) in foods[..nf].iter().enumerate() {
            if want[j] <= 0.0 {
                continue;
            }
            // what this animal takes, and the cell loses s times over (at most half of what is there)
            let per = want[j] * scale;
            let frac = (per * k / fo.full).min(0.5 * fo.dens / fo.full);
            let kind = fo.kind;
            let (m, a, bb) = match (fo.kind, fo.src) {
                (3, _) => {
                    let l = sh.lit.at(c);
                    let o = (l.m * frac, l.a * frac, l.b * frac);
                    l.m -= o.0;
                    l.a -= o.1;
                    l.b -= o.2;
                    o
                }
                (4, _) => {
                    let e = sh.car.at(c);
                    let o = (e.m * frac, e.a * frac, e.b * frac);
                    // the part of it that was killed is counted apart
                    let killed = e.kill * frac;
                    f.eaten[5] += killed;
                    b.eaten[5] += killed / k;
                    f.eaten[4] -= killed;
                    b.eaten[4] -= killed / k;
                    e.m -= o.0;
                    e.a -= o.1;
                    e.b -= o.2;
                    e.kill -= killed;
                    o
                }
                (2, s) if s >= 100 => {
                    let e = sh.bank.at(c * BANK + s - 100);
                    let o = (e.m * frac, e.a * frac, e.b * frac);
                    e.m -= o.0;
                    e.a -= o.1;
                    e.b -= o.2;
                    o
                }
                (_, s) => {
                    let y = sh.co.at(c * K + s);
                    let organ = [LEAF, WOOD, SEED][kind];
                    let o = y.o[organ].take(frac);
                    if kind == 0 {
                        y.cmp *= 1.0 - frac;
                        y.damage += frac;
                    }
                    (o.m, o.a, o.b)
                }
            };
            f.eaten[kind] += m;
            b.eaten[kind] += m / k;
            got[ng] = (m / k, a / k, bb / k, kind, fo.tox, fo.a, fo.b);
            ng += 1;
            intake += m / k;
        }
    }
    if ng > 0 && intake > 0.0 {
        // e111, worth: of a plant food the working part (in proportion to its B) is digested at once, and of the
        // bulk what the rot would take in the time the gut holds it - its fill over what passes
        let held = p.gut_hold * fm.frac[GUT] * b.m / (intake / dt) / (p.year / p.day); // years
        let bulk = 1.0 - (-p.decay * q10(tb) * held).exp();
        let (mut gm, mut ga, mut gb, mut dung, mut da, mut harm) = (0.0, 0.0, 0.0, 0.0, 0.0, 0.0);
        for &(m, a, bb, kind, tox, share_a, share_b) in &got[..ng] {
            harm += m * tox * p.body_harm;
            let dig = if p.worth > 0.0 && kind < 4 {
                let work = (share_b / p.b_work).min(1.0);
                work + (1.0 - work) * bulk
            } else {
                // flesh, and every food in e110's world: the soft part, and the tough part as far as the gut holds it
                let tough = toughness(share_a);
                (1.0 - tough) + tough * retention
            };
            // a food's B is its working part, freed whole; with the worth law its A goes with its matter
            let free = if p.worth > 0.0 { dig } else { 1.0 };
            gm += m * dig;
            ga += a * free;
            gb += bb;
            dung += m * (1.0 - dig);
            da += a * (1.0 - free);
        }
        let kept = gm * eff;
        b.fat += kept;
        f.returned += (gm - kept) * k;
        // A and B held up to what a tenth of its tissue holds. What is digested and not kept: into the litter
        // (e110), or to the soil where it stands (e111, road: a body's waste is mineral). What is not digested is
        // dung, litter with the A that goes with it.
        let cap_a = 0.1 * b.ta.max(1e-6) + 1.0 * b.m;
        let cap_b = 0.1 * b.tb.max(1e-6) + 1.0 * b.m;
        let ka = ga.min((cap_a - b.pa).max(0.0));
        let kb = gb.min((cap_b - b.pb).max(0.0));
        b.pa += ka;
        b.pb += kb;
        let l = sh.lit.at(c);
        l.m += dung * k;
        l.a += da * k;
        if p.road > 0.0 {
            *sh.sa.at(c) += (ga - ka) * k;
            *sh.sb.at(c) += (gb - kb) * k;
        } else {
            l.a += (ga - ka) * k;
            l.b += (gb - kb) * k;
        }
        if harm > 0.0 {
            b.harm += harm / b.m;
            let lost = shrink(b, harm.min(0.5 * b.m), sh, c, k, false);
            sh.lit.at(c).m += lost * k;
        }
    }

    // Water: drink from wet ground and pools (not the sea); lose it through soft open skin to dry air, and to
    // cooling. In water nothing is lost, and breath comes through the soft open skin another's glue has left free.
    let target = b.target_water();
    if sea {
        let need = upkeep_rate * dt;
        let supply = p.breath * fm.soft * d2 * dt * (1.0 - b.smother);
        if supply < need {
            b.harm += BREATH_HARM * dt * (1.0 - supply / need.max(1e-30));
            if b.harm > 1.0 {
                b.dead = Death::Breath;
            }
        }
    } else {
        let deficit = (x.sat.at(t_env) - *sh.vapor.at(c)).max(0.0);
        let lose = (p.skin_loss * fm.soft * d2 * deficit * dt + cool).min(b.w);
        b.w -= lose;
        *sh.vapor.at(c) += lose * k;
        f.evap += lose * k;
        let g = sh.ground.at(c);
        let avail = (*g * DRINK * dt).max(0.0) / k; // kg for each of its animals
        let drink = (target - b.w).max(0.0).min(avail).min(2.0 * target * dt);
        b.w += drink;
        *g -= drink * k;
        f.drunk += drink * k;
        if b.w < 0.5 * target {
            b.dead = Death::Thirst;
        }
    }

    // Upkeep and work, from the fat; short of fat, the tissue burns.
    let cost = upkeep_rate * dt + b.work;
    if b.id < x.trace && b.age < 30.0 {
        eprintln!(
            "trace {} age {:.1} sea {} m {:.3e}/{:.3e} s {} fat {:.2}cap w {:.2}tgt t {:.1} env {:.1} topt {:.1}/{:.1} v {:.3} path {:.0}m upkeep {:.2e} work {:.2e} gutcap {:.2e} foods {} pressure {:.1e} height {:.3} mouth {:.1} harm {:.2}",
            b.id, b.age, sea as u8, b.m, bt.adult(), b.s, b.fat / fat_cap, b.w / target, tb, t_env, t_opt, breadth, b.v_top, b.path, upkeep_rate * dt, b.work, gut_cap, nf, pressure, height, fm.mouth, b.harm
        );
    }
    b.fat -= cost;
    f.returned += cost * k;
    if b.fat < 0.0 {
        // what the fat could not pay is paid by the tissue, as far as it goes
        let lack = -b.fat;
        b.fat = 0.0;
        f.returned -= lack * k;
        f.returned += shrink(b, lack, sh, c, k, p.road > 0.0) * k;
    }
    if b.fat > fat_cap {
        // more than it can hold is burnt
        f.returned += (b.fat - fat_cap) * k;
        b.fat = fat_cap;
    }

    // Growth towards its adult mass, from the fat, with A and B at its tissue's shares (a wound regrows so).
    let adult = bt.adult();
    if b.m < adult && b.fat > 0.2 * fat_cap {
        let dm = (p.grow_rate * activity(fm.b_act) * ft.min(1.5) * b.m * dt).min(adult - b.m).min(b.fat / 1.3);
        let need_a = dm * 1000.0 * fm.a;
        let need_b = dm * 1000.0 * fm.b;
        let q = 1.0f64.min(if need_a > 0.0 { b.pa / need_a } else { 1.0 }).min(if need_b > 0.0 { b.pb / need_b } else { 1.0 });
        let dm = dm * q;
        b.m += dm;
        b.ta += dm * 1000.0 * fm.a;
        b.tb += dm * 1000.0 * fm.b;
        b.pa -= dm * 1000.0 * fm.a;
        b.pb -= dm * 1000.0 * fm.b;
        b.fat -= 1.3 * dm;
        f.returned += 0.3 * dm * k;
        b.peak = b.peak.max(b.m);
    }
    let egg = bt.egg();
    let span = (adult / egg).ln().max(1e-9);
    b.stage = ((b.m / egg).max(1.0).ln() / span * STAGES as f64).clamp(0.0, (STAGES - 1) as f64) as u8;

    // Breeding: when grown past its maturity and it chooses to, a share of its fat goes into eggs, which it
    // carries; the clutch is laid when its animals' clutches together hold `brood_s` of the grain, so that a
    // brood is a body worth its place in the list (a compute rule).
    let grown = (b.m / egg).max(1.0).ln() / span;
    if b.breed && grown >= bt.tr[3] && b.fat > 0.5 * fat_cap && b.dead == Death::None {
        let fm0 = &bt.forms[0];
        let each = egg * (1.0 + p.yolk);
        let spend = bt.tr[2] * b.fat;
        let mut eggs = (spend / (1.2 * each)).floor();
        eggs = eggs.min((b.pa / (egg * 1000.0 * fm0.a).max(1e-30)).floor()).min((b.pb / (egg * 1000.0 * fm0.b).max(1e-30)).floor());
        eggs = eggs.min((b.w - 0.6 * target).max(0.0) / (egg * (WET - 1.0))).floor();
        if eggs >= 1.0 && fm0.nv > 0.0 {
            b.fat -= eggs * each * 1.2;
            f.returned += eggs * each * 0.2 * k;
            b.pa -= eggs * egg * 1000.0 * fm0.a;
            b.pb -= eggs * egg * 1000.0 * fm0.b;
            b.w -= eggs * egg * (WET - 1.0);
            b.carry += eggs;
            b.c_m += eggs * each;
            b.c_a += eggs * egg * 1000.0 * fm0.a;
            b.c_b += eggs * egg * 1000.0 * fm0.b;
            b.c_w += eggs * egg * (WET - 1.0);
        }
    }
    b.lay = b.carry > 0.0 && b.c_m * b.s >= p.brood_s * p.big_s;

    // Wear, cold, damage.
    b.age += dt;
    let lifespan = p.body_life + p.body_life_frame * fm.frac[FRAME] * fm.frame_tough;
    if tb < -2.0 {
        let lost = shrink(b, FROST * dt * (-2.0 - tb) * b.m, sh, c, k, false);
        sh.lit.at(c).m += lost * k;
        if b.m < 0.5 * b.peak {
            b.dead = Death::Cold;
        }
    }
    if tb > t_hi + 5.0 {
        b.harm += HEAT_HARM * dt;
        if b.harm > 1.0 {
            b.dead = Death::Heat;
        }
    }
    b.harm *= (-dt).exp();
    if b.dead == Death::None {
        if b.age > lifespan {
            b.dead = Death::Age;
        } else if b.m < 0.5 * b.peak {
            b.dead = if b.harm > 0.5 { Death::Poison } else { Death::Hunger };
        }
    }
}

/// Tissue lost (burnt for energy, or harmed away): its A and B go to the litter of the cell, or to its soil
/// (`soil`: e111's road, tissue a body burns is digested); the mass lost is returned for the caller to send to
/// the air or the litter.
fn shrink(b: &mut Body, lost: f64, sh: &Sh, c: usize, k: f64, soil: bool) -> f64 {
    let q = (lost / b.m.max(1e-30)).clamp(0.0, 1.0);
    let (dm, da, db) = (b.m * q, b.ta * q, b.tb * q);
    b.m -= dm;
    b.ta -= da;
    b.tb -= db;
    if soil {
        *sh.sa.at(c) += da * k;
        *sh.sb.at(c) += db * k;
    } else {
        let l = sh.lit.at(c);
        l.a += da * k;
        l.b += db * k;
    }
    dm
}

/// A reading (#130), no world run: what one grown animal earns and pays a day at each adult mass, on land at its
/// best heat, by `live`'s and `speed`'s own arithmetic - how fast it goes, the ground its mouth sweeps, what its
/// gut can pass, its upkeep and its work, and the thinnest food it can live on (kg a m2 of soft food it breaks:
/// where what it keeps of a day's sweep pays the day). Three bodies: the form with no genes at the tenth of its
/// speed it moves with no genes, the same at full speed, and the designed body (`form::designed`) at full speed.
pub fn bench(p: &Params) {
    let dt = p.body_tick / p.day;
    let dts = dt * 86400.0;
    let none = BodyType::new(Vec::new(), NONE, 0, p.b_comp);
    let made = BodyType::new(crate::form::designed(true, false), NONE, 0, p.b_comp);
    let act0 = 1.0 / (1.0 + (-ACT0).exp());
    println!("body,act,adult_kg,height_m,v_top,km_day,mouth_m,sweep_m2_day,sweep_m2_day_kg,gut_kg_day_kg,upkeep_kg_day_kg,work_kg_day_kg,thinnest_kg_m2,days_to_fill_at_0.1");
    for (name, bt, act) in [("no genes", &none, act0), ("no genes", &none, 1.0), ("designed", &made, 1.0)] {
        let fm = &bt.forms[STAGES - 1];
        for e in -3..=3 {
            let m = 10f64.powi(e);
            let b = Body::grown(0, 0, (0.0, 0.0), 0, 0.0, 1, m, 1.0, 0.0, (m * 1000.0 * fm.a, m * 1000.0 * fm.b));
            let sz = size(&b, fm);
            let ft = heat_factor(bt.tr[4], bt.tr[4], bt.tr[5]);
            let (v_top, power) = speed(p, fm, m, &sz, false, ft);
            let path = v_top * act * dts;
            let mouth_w = fm.mouth.sqrt() * sz.d;
            let sweep = mouth_w * path.max(sz.d) / dt; // m2 a day
            let gut = p.gut_rate * fm.frac[GUT] * activity(fm.b_act) * m * ft.min(1.5); // kg a day
            let upkeep = p.body_resp * m * fm.b; // kg a day at 20 C
            let work = power * act * 86400.0 / ENERGY;
            let bite = 1.0 / (1.0 + (p.bite_ref / (p.muscle_stress * fm.bite).max(1.0)).powi(4));
            let eff = p.assim / (1.0 + 0.1 * bt.keys.len() as f64);
            let cost = upkeep + work;
            let thinnest = if gut * eff > cost { cost / (bite * sweep * eff).max(1e-30) } else { f64::INFINITY };
            let fill = (0.1 * bite * sweep).min(gut) * eff - cost; // kg a day kept on 0.1 kg a m2
            let fat_cap = m * (0.05 + p.fat_hold * fm.frac[FAT]);
            println!(
                "{name},{act:.2},{m:e},{:.4},{v_top:.3},{:.2},{mouth_w:.4},{sweep:.3e},{:.3e},{:.3},{:.4},{:.4},{thinnest:.3e},{:.1}",
                sz.height,
                v_top * act * 86.4,
                sweep / m,
                gut / m,
                upkeep / m,
                work / m,
                if fill > 0.0 { fat_cap / fill } else { f64::INFINITY }
            );
        }
    }
}
