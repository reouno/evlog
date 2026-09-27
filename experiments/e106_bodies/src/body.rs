//! Rung 3, step 1 (#122, e106): bodies - individuals that develop a form of tissues from the shared genome,
//! grow, eat the producers, drink, keep warm, breed and die, and move at real speeds over the cells.
//!
//! The scale (#117 v2): a cell is ~63 km, and a run holds tens of thousands of bodies where a real land holds
//! billions of animals. So a body is one animal in everything it is and does - its form, its choices, its
//! birth and its death - and its matter counts for `s` animals in the cell's ledger (food, water, eggs, carcass).
//! A clutch makes at most `clutch_max` bodies, each standing for its share of the clutch's animals, and a body
//! that comes to stand for more than 2 `big_s` kg of animals splits in two. Distances and speeds are real.
//!
//! Units: masses kg of dry matter a body (one animal), A and B in g; a cell's fields stay kg (or mm) a m2, and
//! a body's flows reach them times `s / area`. Time in days (an update is `tick / day` of one).
//!
//! The form: an 8x8x8 grid in the body's own frame (x back to front, y left to right, mirrored, z down to up).
//! Each voxel is empty or tissue: a mix of six functions (frame, muscle, gut, nerve, fat, glue), an A share
//! (toughness) and a B share (activity). A gene of a voxel field adds its value where its condition holds; the
//! condition reads the voxel's place and the body's stage (its mass against its adult mass, in 8 steps). Size
//! is separate: the same shape at any mass, so the square-cube law is the only price of size. Physics reads a
//! summary of the form (`Form`), made once per genotype and stage.

use crate::genome::{self, hamming, squash};
use crate::life::{activity, q10, toughness, Cohort, Litter, Seeds, BANK, K, LEAF, SEED, WOOD};
use crate::noise::Rng;
use crate::par::{self, Shared, CHUNKS};
use crate::terrain::{nbrs, Terrain, NONE};
use crate::Params;
use std::f64::consts::TAU;

const SIDE: usize = 8;
const VOX: usize = SIDE * SIDE * SIDE;
pub const STAGES: usize = 8;
const WET: f64 = 3.3; // wet over dry mass of tissue
const FAT_WET: f64 = 1.1; // of fat
const ENERGY: f64 = 1.7e7; // J a kg of dry matter
const LATENT: f64 = 2.4e6; // J a kg of water evaporated
const G: f64 = 9.8;

// Genome addresses (the producers read 0..20, the small eaters 32..36).
const SCALAR: usize = 64; // body-level traits, read whatever their condition
const S_TRAITS: usize = 7;
const DETOX: usize = 80; // a gene here carries a detox key
const FIELD: usize = 96; // voxel fields, read where their condition holds
const FIELDS: usize = 9; // present, six function logits, A share, B share
const EVAL: usize = 112; // the food evaluator's weights
pub const NE: usize = 6;
const WEIGHT: usize = 128; // controller weights: the address picks the output, the condition byte the input
pub const NI: usize = 20;
pub const NO: usize = 7;

/// (name, lo, hi, log)
pub const S_RANGE: [(&str, f64, f64, bool); S_TRAITS] = [
    ("adult_mass", 1e-6, 1e4, true),
    ("egg", 1e-4, 0.3, true),
    ("clutch", 0.05, 1.0, false),
    ("maturity", 0.05, 1.0, false),
    ("t_opt", -10.0, 40.0, false),
    ("breadth", 3.0, 20.0, true),
    ("tolerance", 0.0, 4.0, false),
];

const FRAME: usize = 0;
const MUSCLE: usize = 1;
const GUT: usize = 2;
const NERVE: usize = 3;
const FAT: usize = 4;
const GLUE: usize = 5;

/// What physics reads of a form. Counts are in voxels or voxel faces; a body of dry mass m scales them by its
/// voxel side `d` (areas by d^2).
#[derive(Clone, Default)]
pub struct Form {
    pub nv: f64,
    pub frac: [f64; 6], // the share of the tissue in each function
    pub a: f64,         // A share of the tissue
    pub b: f64,         // B share
    pub frame_tough: f64,
    pub ext: [f64; 3], // extent along x, y, z
    pub front: f64,    // faces seen from the front (the y-z projection)
    pub open: f64,     // open faces
    pub soft: f64,     // open faces, each weighted by its softness
    pub fat_skin: f64, // open faces, each weighted by the fat under it
    pub eye: f64,      // open faces of active nerve
    pub legs: f64,     // share of the tissue that is muscle in columns reaching the body's bottom
    pub bite: f64,     // the front's pressure over the muscle's stress: muscle behind x the tip's hardness / front faces
    pub mouth: f64,    // gut faces on the front
    pub density: f64,  // kg a litre, wet
}

pub struct BodyType {
    pub genes: Vec<u32>,
    pub parent: u32,
    pub born: u32,
    pub tr: [f64; S_TRAITS],
    pub keys: Vec<u8>,
    pub eval: [f64; NE],
    pub w: [[f64; NI]; NO],
    pub forms: Vec<Form>, // one per stage; nv 0 is a form that cannot live
}

impl BodyType {
    pub fn new(genes: Vec<u32>, parent: u32, born: u32) -> Self {
        let mut raw = [0.0; S_TRAITS];
        let mut keys = Vec::new();
        let mut eval = [0.0; NE];
        let mut w = [[0.0; NI]; NO];
        let mut fg: Vec<(usize, Option<(usize, bool, f64)>, f64)> = Vec::new();
        for &g in &genes {
            let t = genome::target(g);
            let v = genome::value(g);
            if (SCALAR..SCALAR + S_TRAITS).contains(&t) {
                raw[t - SCALAR] += v;
            } else if t == DETOX {
                keys.push(genome::key(g));
            } else if (FIELD..FIELD + FIELDS).contains(&t) {
                fg.push((t - FIELD, genome::condition(g), v));
            } else if (EVAL..EVAL + NE).contains(&t) {
                eval[t - EVAL] += v;
            } else if (WEIGHT..WEIGHT + NO).contains(&t) {
                w[t - WEIGHT][genome::cond(g) as usize % NI] += v;
            }
        }
        let mut tr = [0.0; S_TRAITS];
        for i in 0..S_TRAITS {
            tr[i] = squash(raw[i], S_RANGE[i].1, S_RANGE[i].2, S_RANGE[i].3);
        }
        let forms = (0..STAGES).map(|s| develop(&fg, (s as f64 + 0.5) / STAGES as f64)).collect();
        BodyType { genes, parent, born, tr, keys, eval, w, forms }
    }
    pub fn adult(&self) -> f64 {
        self.tr[0]
    }
    pub fn egg(&self) -> f64 {
        self.tr[0] * self.tr[1]
    }
}

/// The form at a stage: every voxel's fields from the genes whose condition holds there, the largest connected
/// part kept, and the summary physics reads.
fn develop(fg: &[(usize, Option<(usize, bool, f64)>, f64)], stage: f64) -> Form {
    let mut on = [false; VOX];
    let mut mix = vec![[0.0f64; 6]; VOX];
    let mut sa = [0.0f64; VOX];
    let mut sb = [0.0f64; VOX];
    for z in 0..SIDE {
        for y in 0..SIDE {
            for x in 0..SIDE {
                let i = (z * SIDE + y) * SIDE + x;
                let fx = (x as f64 + 0.5) / SIDE as f64;
                let fy = (y as f64 + 0.5 - SIDE as f64 / 2.0).abs() / (SIDE as f64 / 2.0); // 0 at the middle, 1 at a side
                let fz = (z as f64 + 0.5) / SIDE as f64;
                let r = (((fx - 0.5).powi(2) + (fy * 0.5).powi(2) + (fz - 0.5).powi(2)).sqrt() / 0.75f64.sqrt()).min(1.0);
                let sig = [fx, fy, fz, r, stage, 4.0 * fx * (1.0 - fx), 4.0 * fz * (1.0 - fz), stage];
                // defaults: a round blob, an even mix, mid shares
                let mut f = [1.0 - 3.0 * r, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0];
                for &(t, c, v) in fg {
                    let holds = match c {
                        None => true,
                        Some((s, above, level)) => (sig[s] > level) == above,
                    };
                    if holds {
                        f[t] += v;
                    }
                }
                if f[0] <= 0.0 {
                    continue;
                }
                on[i] = true;
                let m = f[1..7].iter().cloned().fold(f64::MIN, f64::max);
                let e: Vec<f64> = f[1..7].iter().map(|v| (v - m).exp()).collect();
                let s: f64 = e.iter().sum();
                for k in 0..6 {
                    mix[i][k] = e[k] / s;
                }
                sa[i] = squash(f[7], 0.001, 0.1, true);
                sb[i] = squash(f[8], 0.005, 0.1, true);
            }
        }
    }
    // Keep the largest face-connected part.
    let mut label = [usize::MAX; VOX];
    let (mut best, mut best_n) = (usize::MAX, 0usize);
    let mut stack = Vec::new();
    for s in 0..VOX {
        if !on[s] || label[s] != usize::MAX {
            continue;
        }
        label[s] = s;
        stack.push(s);
        let mut cnt = 0;
        while let Some(i) = stack.pop() {
            cnt += 1;
            for j in adj(i).into_iter().flatten() {
                if on[j] && label[j] == usize::MAX {
                    label[j] = s;
                    stack.push(j);
                }
            }
        }
        if cnt > best_n {
            best = s;
            best_n = cnt;
        }
    }
    let mut f = Form::default();
    if best_n == 0 {
        return f;
    }
    for i in 0..VOX {
        on[i] = on[i] && label[i] == best;
    }
    let (mut lo, mut hi) = ([SIDE; 3], [0usize; 3]);
    let mut frame_w = 0.0;
    let mut proj_front = [false; SIDE * SIDE];
    let mut colmin = [SIDE; SIDE * SIDE]; // the lowest z of each (x, y) column
    for i in 0..VOX {
        if !on[i] {
            continue;
        }
        let (x, y, z) = (i % SIDE, (i / SIDE) % SIDE, i / (SIDE * SIDE));
        for (k, v) in [x, y, z].into_iter().enumerate() {
            lo[k] = lo[k].min(v);
            hi[k] = hi[k].max(v);
        }
        proj_front[z * SIDE + y] = true;
        colmin[y * SIDE + x] = colmin[y * SIDE + x].min(z);
        f.nv += 1.0;
        for k in 0..6 {
            f.frac[k] += mix[i][k];
        }
        f.a += sa[i];
        f.b += sb[i];
        f.frame_tough += mix[i][FRAME] * toughness(sa[i]);
        frame_w += mix[i][FRAME];
        let dens = 1.05 * (1.0 - mix[i][FAT]) + 0.9 * mix[i][FAT] + 0.9 * mix[i][FRAME] * toughness(sa[i]);
        f.density += dens;
        let hard = mix[i][FRAME] * toughness(sa[i]);
        for j in adj(i) {
            if j.is_none_or(|j| !on[j]) {
                f.open += 1.0;
                f.soft += 1.0 - hard;
                f.fat_skin += mix[i][FAT];
                f.eye += mix[i][NERVE] * activity(sb[i]);
            }
        }
    }
    let nv = f.nv;
    for k in 0..6 {
        f.frac[k] /= nv;
    }
    f.a /= nv;
    f.b /= nv;
    f.density /= nv;
    f.frame_tough = if frame_w > 0.0 { f.frame_tough / frame_w } else { 0.0 };
    for k in 0..3 {
        f.ext[k] = (hi[k] + 1 - lo[k]) as f64;
    }
    f.front = proj_front.iter().filter(|&&b| b).count() as f64;
    // Legs: muscle in the columns that reach the body's lowest layer. The front: the frontmost layer, the
    // muscle in the three layers behind it, and the hardest tip in it.
    let (mut legs, mut nfront, mut tip, mut behind, mut mouth) = (0.0, 0.0f64, 0.0f64, 0.0, 0.0);
    for i in 0..VOX {
        if !on[i] {
            continue;
        }
        let (x, y, z) = (i % SIDE, (i / SIDE) % SIDE, i / (SIDE * SIDE));
        if colmin[y * SIDE + x] == lo[2] {
            legs += mix[i][MUSCLE] * activity(sb[i]);
        }
        if x == hi[0] {
            nfront += 1.0;
            tip = tip.max(mix[i][FRAME] * toughness(sa[i]));
            mouth += mix[i][GUT];
        }
        if x + 3 > hi[0] {
            behind += mix[i][MUSCLE] * activity(sb[i]);
        }
        let _ = z;
    }
    f.legs = legs / nv;
    f.bite = behind * (0.1 + 0.9 * tip) / nfront.max(1.0);
    f.mouth = mouth;
    f
}

/// The six face neighbours of a voxel, None beyond the grid.
fn adj(i: usize) -> [Option<usize>; 6] {
    let (x, y, z) = (i % SIDE, (i / SIDE) % SIDE, i / (SIDE * SIDE));
    let at = |x: usize, y: usize, z: usize| (z * SIDE + y) * SIDE + x;
    [
        (x > 0).then(|| at(x - 1, y, z)),
        (x + 1 < SIDE).then(|| at(x + 1, y, z)),
        (y > 0).then(|| at(x, y - 1, z)),
        (y + 1 < SIDE).then(|| at(x, y + 1, z)),
        (z > 0).then(|| at(x, y, z - 1)),
        (z + 1 < SIDE).then(|| at(x, y, z + 1)),
    ]
}

/// A random body genome: genes spread over the addresses bodies read (a first population, not a design).
pub fn random(rng: &mut Rng) -> Vec<u32> {
    let n = 24 + rng.below(40);
    (0..n)
        .map(|_| {
            let r = rng.f64();
            let t = if r < 0.2 {
                SCALAR + rng.below(S_TRAITS)
            } else if r < 0.25 {
                DETOX
            } else if r < 0.55 {
                FIELD + rng.below(FIELDS)
            } else if r < 0.65 {
                EVAL + rng.below(NE)
            } else {
                WEIGHT + rng.below(NO)
            } as u32;
            (t << 24) | (rng.next_u64() as u32 & 0x00FF_FFFF)
        })
        .collect()
}

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
}

pub const CENSUS: &str = "year,id,parent,born,genes,bodies,animals,matter,mass,adult_mass,egg,clutch,maturity,t_opt,breadth,tolerance,n_keys,keys,cells,nv,frame,muscle,gut,nerve,fat,glue,a,b,frame_tough,density,legs,bite,mouth,eye,ext_x,ext_y,ext_z,sea,travel_yr,from_birth,ate_leaf,ate_wood,ate_seed,ate_litter";

pub const DEATHS: [&str; 8] = ["hunger", "thirst", "heat", "cold", "breath", "poison", "age", "form"];

#[derive(Clone)]
pub struct Body {
    pub id: u64,
    pub g: u32,
    pub x: f64, // position in cells, continuous
    pub y: f64,
    pub cell: u32,
    pub m: f64,   // dry tissue, kg
    pub ta: f64,  // g of A in the tissue
    pub tb: f64,  // g of B
    pub fat: f64, // kg
    pub pa: f64,  // g of A held for growth
    pub pb: f64,
    pub w: f64, // kg of water
    pub s: f64, // the animals it stands for
    pub peak: f64,
    pub age: f64, // days
    pub stage: u8,
    pub t: f64, // C
    pub harm: f64,
    pub rng: u64,
    pub born_cell: u32,
    pub travel: f64,     // cells crossed
    pub eaten: [f64; 4], // kg eaten in its life: leaf, wood, seed, litter
    pub dead: Death,
    pub eggs: u32, // eggs laid this update, set in the parallel pass and hatched in the serial one
    pub egg_s: f64,
}

impl Body {
    fn f64(&mut self) -> f64 {
        let mut x = self.rng;
        x ^= x >> 12;
        x ^= x << 25;
        x ^= x >> 27;
        self.rng = x;
        (x.wrapping_mul(0x2545_F491_4F6C_DD1D) >> 11) as f64 / (1u64 << 53) as f64
    }
    fn wet(&self) -> f64 {
        self.m * WET + self.fat * FAT_WET
    }
    fn target_water(&self) -> f64 {
        self.m * (WET - 1.0)
    }
}

/// What crossed the edges of the bodies in a stretch of time (cell units: kg or mm a m2, summed over cells).
#[derive(Default, Clone, Copy)]
pub struct BFlux {
    pub fixed: f64,    // matter that entered (sown)
    pub returned: f64, // respired
    pub eaten: [f64; 4],
    pub drunk: f64,
    pub evap: f64,
    pub births: f64,
    pub deaths: [f64; 8],
    pub splits: f64,
    pub moved: f64, // cells crossed
}

impl BFlux {
    pub fn add(&mut self, o: &BFlux) {
        self.fixed += o.fixed;
        self.returned += o.returned;
        for k in 0..4 {
            self.eaten[k] += o.eaten[k];
        }
        self.drunk += o.drunk;
        self.evap += o.evap;
        self.births += o.births;
        for k in 0..8 {
            self.deaths[k] += o.deaths[k];
        }
        self.splits += o.splits;
        self.moved += o.moved;
    }
}

pub struct Bodies {
    pub list: Vec<Body>,
    pub types: Vec<Option<Box<BodyType>>>,
    next_id: u64,
    rng: Rng,
    pub sown: bool,
    area: f64, // m2 a cell
    chunk_of_row: Vec<usize>,
    food: Vec<f64>, // what a body senses of each cell: kg a m2 of leaf, seed and litter within a short body's reach
    water: Vec<f64>,
    pub secs: f64,
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
    pub gen: &'a [Option<Box<genome::Genotype>>],
    pub step: f64,
    pub year: u32,
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
            next_id: 0,
            rng: Rng::new(p.life as u64 ^ 0xB0D1),
            sown: false,
            area: (p.cell_km * 1000.0).powi(2),
            chunk_of_row,
            food: vec![0.0; n * n],
            water: vec![0.0; n * n],
            secs: 0.0,
        }
    }

    pub fn k(&self, b: &Body) -> f64 {
        b.s / self.area
    }

    /// The first bodies: `body_founders` random genomes, `bodies0` bodies as grown adults on random cells of
    /// land and sea, each standing for `big_s` kg of animals. Their A and B come from the soils and waters of
    /// the whole world, each cell giving in proportion to what it holds; their water from the air above them.
    pub fn sow(&mut self, p: &Params, ter: &Terrain, sa: &mut [f64], sb: &mut [f64], vapor: &mut [f64], year: u32) -> BFlux {
        let mut f = BFlux::default();
        for _ in 0..p.body_founders as usize {
            let g = random(&mut self.rng);
            self.types.push(Some(Box::new(BodyType::new(g, NONE, year))));
        }
        let n = ter.n;
        let mut skip = [0usize; 3];
        let (tot_a, tot_b): (f64, f64) = (sa.iter().sum(), sb.iter().sum());
        let (mut need_a, mut need_b) = (0.0, 0.0);
        for _ in 0..p.bodies0 as usize {
            let g = self.rng.below(self.types.len()) as u32;
            let bt = self.types[g as usize].as_ref().unwrap();
            let fm = &bt.forms[STAGES - 1];
            if fm.nv == 0.0 {
                skip[0] += 1;
                continue;
            }
            let c = self.rng.below(n * n);
            let m = bt.adult();
            let s = p.big_s / m;
            let k = s / self.area;
            let fat = 0.3 * m * (0.05 + p.fat_hold * fm.frac[FAT]);
            let (ta, tb) = (m * 1000.0 * fm.a, m * 1000.0 * fm.b);
            if need_a + ta * k > 0.1 * tot_a || need_b + tb * k > 0.1 * tot_b {
                skip[1] += 1;
                continue;
            }
            need_a += ta * k;
            need_b += tb * k;
            let w = m * (WET - 1.0);
            let wk = w * k;
            if wk > 0.5 * vapor[c] {
                skip[2] += 1;
                continue;
            }
            vapor[c] -= wk;
            f.fixed += (m + fat) * k;
            let (x, y) = ((c % n) as f64 + self.rng.f64(), (c / n) as f64 + self.rng.f64());
            let id = self.next_id;
            self.next_id += 1;
            self.list.push(Body {
                id,
                g,
                x,
                y,
                cell: c as u32,
                m,
                ta,
                tb,
                fat,
                pa: 0.0,
                pb: 0.0,
                w,
                s,
                peak: m,
                age: 0.0,
                stage: (STAGES - 1) as u8,
                t: 20.0,
                harm: 0.0,
                rng: self.rng.next_u64() | 1,
                born_cell: c as u32,
                travel: 0.0,
                eaten: [0.0; 4],
                dead: Death::None,
                eggs: 0,
                egg_s: 0.0,
            });
        }
        let (qa, qb) = (1.0 - need_a / tot_a, 1.0 - need_b / tot_b);
        sa.iter_mut().for_each(|v| *v *= qa);
        sb.iter_mut().for_each(|v| *v *= qb);
        eprintln!("bodies sown: {} (no form {}, no soil {}, no water {})", self.list.len(), skip[0], skip[1], skip[2]);
        self.sown = true;
        f
    }

    /// One update: every body senses, decides, eats, drinks, keeps its heat, pays its upkeep, grows, lays and
    /// moves (in parallel over fixed chunks of rows, each body touching only its own cell); then, in order,
    /// the dead return to their cells, eggs hatch and heavy bodies split.
    pub fn update(&mut self, wd: &mut World) -> BFlux {
        let t0 = std::time::Instant::now();
        let p = wd.p;
        let n = wd.ter.n;
        let cells = n * n;
        let threads = (if p.body_threads > 0.0 { p.body_threads } else { p.threads }) as usize;
        // What each cell offers the senses.
        {
            let (food, water) = (Shared::new(&mut self.food), Shared::new(&mut self.water));
            let (co, lit, bank, ground, ter) = (&*wd.co, &*wd.lit, &*wd.bank, &*wd.ground, wd.ter);
            par::pieces(threads, cells, |lo, hi| {
                for c in lo..hi {
                    let mut fsum = lit[c].m;
                    for i in 0..K {
                        let x = &co[c * K + i];
                        if x.g != NONE && x.h < 2.0 {
                            fsum += x.o[LEAF].m + x.o[SEED].m;
                        }
                    }
                    for j in 0..BANK {
                        fsum += bank[c * BANK + j].m;
                    }
                    *food.at(c) = fsum;
                    *water.at(c) = if ter.sea[c] { 0.0 } else { (ground[c] / ter.cap[c]).min(2.0) };
                }
            });
        }
        // The bodies of each chunk, in their order in the list.
        let mut by_chunk: Vec<Vec<usize>> = vec![Vec::new(); CHUNKS];
        for (i, b) in self.list.iter().enumerate() {
            by_chunk[self.chunk_of_row[b.cell as usize / n]].push(i);
        }
        let season = TAU * wd.step / p.year;
        let decl = p.tilt.to_radians() * season.sin();
        let ctx = Ctx {
            p,
            ter: wd.ter,
            temp: wd.temp,
            light: wd.light,
            sat: wd.sat,
            types: &self.types,
            gen: wd.gen,
            food: &self.food,
            water: &self.water,
            area: self.area,
            trace: std::env::var("EVLOG_BODY_TRACE").ok().and_then(|v| v.parse().ok()).unwrap_or(0),
            dt: p.tick / p.day,

            season_sin: season.sin(),
            season_cos: season.cos(),
        };
        let sh = Sh {
            bodies: Shared::new(&mut self.list),
            co: Shared::new(&mut *wd.co),
            lit: Shared::new(&mut *wd.lit),
            bank: Shared::new(&mut *wd.bank),
            vapor: Shared::new(&mut *wd.vapor),
            ground: Shared::new(&mut *wd.ground),
        };
        let fl: Vec<BFlux> = par::over(threads, &by_chunk, |list| {
            let mut f = BFlux::default();
            for &i in list {
                live(&ctx, &sh, i, &mut f);
            }
            f
        });
        let mut f = BFlux::default();
        for x in &fl {
            f.add(x);
        }
        // In order: the dead, the eggs, the splits.
        let old = std::mem::take(&mut self.list);
        let mut out = Vec::with_capacity(old.len() + 64);
        for mut b in old {
            let k = b.s / self.area;
            let c = b.cell as usize;
            if b.eggs > 0 {
                self.hatch(p, &mut b, &mut out, wd.year, &mut f);
            }
            if b.dead != Death::None {
                let l = &mut wd.lit[c];
                l.m += (b.m + b.fat) * k;
                l.a += (b.ta + b.pa) * k;
                l.b += (b.tb + b.pb) * k;
                wd.vapor[c] += b.w * k;
                f.deaths[b.dead as usize - 1] += 1.0;
                continue;
            }
            let bt = self.types[b.g as usize].as_ref().unwrap();
            if b.m * b.s > 2.0 * p.big_s && bt.forms[b.stage as usize].nv > 0.0 {
                // Standing for too many animals: two bodies, each for half of them.
                b.s *= 0.5;
                let mut twin = b.clone();
                twin.id = self.next_id;
                self.next_id += 1;
                twin.rng = self.rng.next_u64() | 1;
                twin.x = (twin.x.floor() + self.rng.f64()).rem_euclid(n as f64);
                twin.y = (twin.y.floor() + self.rng.f64()).rem_euclid(n as f64);
                f.splits += 1.0;
                out.push(b);
                out.push(twin);
                continue;
            }
            out.push(b);
        }
        self.list = out;
        self.secs += t0.elapsed().as_secs_f64();
        f
    }

    /// Eggs become bodies beside their parent: at most `clutch_max` of them, each standing for its share of the
    /// clutch's animals; each carries a mutation with chance `body_mut`.
    fn hatch(&mut self, p: &Params, b: &mut Body, out: &mut Vec<Body>, year: u32, f: &mut BFlux) {
        let eggs = b.eggs as f64;
        b.eggs = 0;
        let bt = self.types[b.g as usize].as_ref().unwrap();
        let (fa, fb, e) = (bt.forms[0].a, bt.forms[0].b, bt.egg());
        let nb = eggs.min(p.clutch_max).max(1.0);
        let per = eggs / nb; // eggs of the parent's animals that each new body stands for
        for _ in 0..nb as usize {
            let mut g = b.g;
            if self.rng.f64() < p.body_mut {
                let genes = genome::mutate(&self.types[b.g as usize].as_ref().unwrap().genes, &mut self.rng);
                self.types.push(Some(Box::new(BodyType::new(genes, b.g, year))));
                g = (self.types.len() - 1) as u32;
            }
            let id = self.next_id;
            self.next_id += 1;
            // what the parent laid, for each animal of the child: tissue, yolk, A, B and water (taken in `live`)
            out.push(Body {
                id,
                g,
                x: b.x,
                y: b.y,
                cell: b.cell,
                m: e,
                ta: e * 1000.0 * fa,
                tb: e * 1000.0 * fb,
                fat: e * p.yolk,
                pa: 0.0,
                pb: 0.0,
                w: e * (WET - 1.0),
                s: b.egg_s * per,
                peak: e,
                age: 0.0,
                stage: 0,
                t: b.t,
                harm: 0.0,
                rng: self.rng.next_u64() | 1,
                born_cell: b.cell,
                travel: 0.0,
                eaten: [0.0; 4],
                dead: Death::None,
                eggs: 0,
                egg_s: 0.0,
            });
            f.births += 1.0;
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
    /// where its bodies are and what they have eaten.
    pub fn census(&self, out: &mut impl std::io::Write, ter: &Terrain, year: usize) {
        let ng = self.types.len();
        #[derive(Default, Clone)]
        struct Acc {
            n: u32,
            animals: f64,
            matter: f64,
            mass: f64,
            sea: f64,
            travel: f64,
            from_birth: f64,
            eaten: [f64; 4],
            cells: Vec<u32>,
        }
        let mut acc = vec![Acc::default(); ng];
        let n = ter.n as f64;
        for b in &self.list {
            let a = &mut acc[b.g as usize];
            a.n += 1;
            a.animals += b.s;
            a.matter += (b.m + b.fat) * b.s;
            a.mass += b.m * b.s;
            if ter.sea[b.cell as usize] {
                a.sea += b.s;
            }
            a.travel += b.travel / (b.age / 365.0).max(0.1);
            let (x0, y0) = ((b.born_cell as usize % ter.n) as f64, (b.born_cell as usize / ter.n) as f64);
            let (dx, dy) = ((b.x.floor() - x0).abs(), (b.y.floor() - y0).abs());
            a.from_birth += dx.min(n - dx) + dy.min(n - dy);
            for k in 0..4 {
                a.eaten[k] += b.eaten[k] * b.s;
            }
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
            writeln!(
                out,
                "{year},{g},{},{},{},{},{:.4e},{:.4e},{:.4e},{:.4e},{:.4e},{:.3},{:.3},{:.2},{:.2},{:.3},{},{},{},{:.0},{:.3},{:.3},{:.3},{:.3},{:.3},{:.3},{:.4},{:.4},{:.3},{:.3},{:.3},{:.3},{:.2},{:.3},{},{},{},{:.3},{:.2},{:.2},{:.3},{:.3},{:.3},{:.3}",
                bt.parent as i64 - if bt.parent == NONE { u32::MAX as i64 + 1 } else { 0 },
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
                a.cells.len(),
                fm.nv,
                fm.frac[0], fm.frac[1], fm.frac[2], fm.frac[3], fm.frac[4], fm.frac[5],
                fm.a, fm.b, fm.frame_tough, fm.density, fm.legs, fm.bite, fm.mouth, fm.eye,
                fm.ext[0], fm.ext[1], fm.ext[2],
                a.sea / a.animals,
                a.travel / a.n as f64,
                a.from_birth / a.n as f64,
                a.eaten[0] / et, a.eaten[1] / et, a.eaten[2] / et, a.eaten[3] / et
            )
            .unwrap();
        }
    }

    /// The bodies' matter (kg a m2 summed over cells), A and B (g), water (mm summed).
    pub fn totals(&self) -> (f64, f64, f64, f64) {
        let (mut m, mut a, mut b, mut w) = (0.0, 0.0, 0.0, 0.0);
        for x in &self.list {
            let k = self.k(x);
            m += (x.m + x.fat) * k;
            a += (x.ta + x.pa) * k;
            b += (x.tb + x.pb) * k;
            w += x.w * k;
        }
        (m, a, b, w)
    }
}

struct Ctx<'a> {
    p: &'a Params,
    ter: &'a Terrain,
    temp: &'a [f64],
    light: &'a [f64],
    sat: &'a crate::climate::Sat,
    types: &'a [Option<Box<BodyType>>],
    gen: &'a [Option<Box<genome::Genotype>>],
    food: &'a [f64],
    water: &'a [f64],
    area: f64,
    trace: u64,
    dt: f64, // days an update
    season_sin: f64,
    season_cos: f64,
}

struct Sh {
    bodies: Shared<Body>,
    co: Shared<Cohort>,
    lit: Shared<Litter>,
    bank: Shared<Seeds>,
    vapor: Shared<f64>,
    ground: Shared<f64>,
}

/// A food within reach: which it is, kg a m2 of it in the cell, its A and B shares, the pressure it takes, and
/// the harm of its compounds to this body a kg.
struct Food {
    kind: usize, // 0 leaf, 1 wood, 2 seed, 3 litter
    src: usize,  // the cohort, or the bank slot
    dens: f64, // within reach
    full: f64, // all of it in the cell
    a: f64,
    b: f64,
    need: f64,
    tox: f64,
}

/// One body's update.
fn live(x: &Ctx, sh: &Sh, i: usize, f: &mut BFlux) {
    let p = x.p;
    let b = sh.bodies.at(i);
    let bt = x.types[b.g as usize].as_ref().unwrap();
    let fm = &bt.forms[b.stage as usize];
    if fm.nv == 0.0 {
        b.dead = Death::Form;
        return;
    }
    let n = x.ter.n;
    let c = b.cell as usize;
    let sea = x.ter.sea[c];
    let k = b.s / x.area;
    let dt = x.dt;
    let dts = dt * 86400.0;
    let (t_opt, breadth) = (bt.tr[4], bt.tr[5]);

    // The body's size.
    let wet = b.wet();
    let vol = wet / (fm.density * 1000.0);
    let d = (vol / fm.nv).cbrt(); // m: a voxel's side
    let d2 = d * d;
    let height = fm.ext[2] * d;
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
    let ft = (10.0 / breadth) * (-((tb - t_opt) / breadth).powi(2)).exp();

    // Senses and the controller.
    let fill = x.water[c];
    let light = x.light[c];
    let eye_m = (fm.eye * d2).sqrt() * p.sense_k * (0.2 + 0.8 * (light / 0.5).min(1.0)); // m of sight
    let (fx, fy) = (b.x - b.x.floor(), b.y - b.y.floor());
    let edge = [fy, 1.0 - fy, 1.0 - fx, fx]; // share of the cell to the edge towards up, down, right, left
    let nb = nbrs(n, c);
    let mut inp = [0.0; NI];
    inp[0] = 1.0;
    inp[1] = (b.fat / fat_cap.max(1e-30)).min(2.0);
    inp[2] = (b.w / b.target_water()).min(2.0);
    inp[3] = b.harm.min(1.0);
    inp[4] = ((tb - t_opt) / breadth).clamp(-2.0, 2.0) / 2.0;
    inp[5] = b.stage as f64 / (STAGES - 1) as f64;
    inp[6] = (light / 0.5).min(1.0);
    let ls = if x.ter.lat[c / n] >= 0.0 { 1.0 } else { -1.0 };
    inp[7] = x.season_sin * ls;
    inp[8] = x.season_cos * ls;
    let fd = |v: f64| ((v.max(1e-6)).log10() + 3.0) / 3.0;
    inp[9] = fd(x.food[c]);
    inp[10] = fill;
    inp[11] = if sea { 1.0 } else { 0.0 };
    for j in 0..4 {
        let see = (1.0 - edge[j] * x.p.cell_km * 1000.0 / eye_m.max(1e-9)).clamp(0.0, 1.0);
        inp[12 + j] = see * (fd(x.food[nb[j]]) - inp[9]);
        inp[16 + j] = see * (x.water[nb[j]] - fill);
    }
    let mut out = [0.0; NO];
    for o in 0..NO {
        let w = &bt.w[o];
        out[o] = (0..NI).map(|j| w[j] * inp[j]).sum();
    }
    let dir = (0..5).max_by(|&a, &b| out[a].partial_cmp(&out[b]).unwrap()).unwrap(); // 4 is stay
    let act = 1.0 / (1.0 + (-out[5]).exp());
    let breed = 1.0 + out[6] > 0.0; // with no genes, a body breeds when it can

    // Speed and the path of the update: on the ground propulsion from the legs against friction and the ground's
    // roughness (a tall body steps over it); in water from all muscle against drag.
    let power = if sea { p.muscle_power * fm.frac[MUSCLE] * activity(fm.b) } else { p.muscle_power * fm.legs } * b.m * WET * ft.min(1.5);
    let v = if sea {
        let cd = 0.05 + 0.5 * (fm.front / (fm.ext[0] * fm.ext[0])).min(1.0);
        (2.0 * power / (1000.0 * cd * fm.front * d2)).cbrt()
    } else {
        power / (wet * G * (p.mu_ground + p.ground_rough / height.max(1e-6)))
    };
    let path = v * act * dts; // m
    let work = power * act * dts / ENERGY; // kg

    // Eating: what is within reach, whether the mouth can break it, and whether the body takes it.
    let mut foods: Vec<Food> = Vec::with_capacity(12);
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
                foods.push(Food { kind: 0, src: j, dens: o.m * reach, full: o.m, a: o.share_a(), b: o.share_b(), need: p.bite_ref * (1.0 + p.bite_tough * toughness(o.share_a())), tox: tox_of(y.cmp, o.m, ph) });
            }
            if reach > 0.0 && y.o[SEED].m > 1e-12 {
                let o = y.o[SEED];
                foods.push(Food { kind: 2, src: j, dens: o.m * reach, full: o.m, a: o.share_a(), b: o.share_b(), need: p.bite_ref * (1.0 + p.bite_tough * toughness(o.share_a())), tox: 0.0 });
            }
            if !sea && y.o[WOOD].m > 1e-12 {
                let o = y.o[WOOD];
                foods.push(Food { kind: 1, src: j, dens: o.m, full: o.m, a: o.share_a(), b: o.share_b(), need: p.bite_ref * p.wood_hard * (1.0 + p.bite_tough * toughness(o.share_a())), tox: 0.0 });
            }
        }
        if !sea || !floating {
            let l = sh.lit.at(c);
            if l.m > 1e-12 {
                let (la, lb) = (l.a / (l.m * 1000.0), l.b / (l.m * 1000.0));
                foods.push(Food { kind: 3, src: 0, dens: l.m, full: l.m, a: la, b: lb, need: p.bite_ref, tox: 0.0 });
            }
        }
        if !sea {
            for j in 0..BANK {
                let e = sh.bank.at(c * BANK + j);
                if e.g != NONE && e.m > 1e-12 {
                    let (sa, sb) = (e.a / (e.m * 1000.0), e.b / (e.m * 1000.0));
                    foods.push(Food { kind: 2, src: 100 + j, dens: e.m, full: e.m, a: sa, b: sb, need: p.bite_ref * (1.0 + p.bite_tough * toughness(sa)), tox: 0.0 });
                }
            }
        }
    }
    let mouth_w = fm.mouth.sqrt() * d; // m
    let gut_cap = p.gut_rate * fm.frac[GUT] * activity(fm.b) * b.m * dt * ft.min(1.5); // kg this update
    let retention = fm.frac[GUT] / (fm.frac[GUT] + p.retain);
    let eff = p.assim / (1.0 + 0.1 * bt.keys.len() as f64);
    let fill_share = (b.fat / fat_cap.max(1e-30)).min(2.0);
    let sweep = mouth_w * path.max(d); // m2 swept (a body standing still still reaches what is under it)
    let mut want = [0.0; 12];
    let mut total = 0.0;
    for (j, fo) in foods.iter().enumerate().take(12) {
        let bite = 1.0 / (1.0 + (fo.need / pressure.max(1.0)).powi(4));
        let feat = [1.0, fo.b / 0.03, bite, fo.tox, fd(fo.dens), fill_share];
        let s: f64 = 1.0 + (0..NE).map(|q| bt.eval[q] * feat[q]).sum::<f64>(); // with no genes, it takes all it can
        if s <= 0.0 || bite < 1e-3 {
            continue;
        }
        want[j] = fo.dens * bite * sweep;
        total += want[j];
    }
    if total > 0.0 && gut_cap > 0.0 {
        let scale = (gut_cap / total).min(1.0);
        let (mut gm, mut ga, mut gb, mut dung, mut harm) = (0.0, 0.0, 0.0, 0.0, 0.0);
        for (j, fo) in foods.iter().enumerate().take(12) {
            if want[j] <= 0.0 {
                continue;
            }
            // what this animal takes, and the cell loses s times over (at most half of what is there)
            let per = want[j] * scale;
            let frac = (per * k / fo.full).min(0.5 * fo.dens / fo.full);
            let (m, a, bb) = match (fo.kind, fo.src) {
                (3, _) => {
                    let l = sh.lit.at(c);
                    let o = (l.m * frac, l.a * frac, l.b * frac);
                    l.m -= o.0;
                    l.a -= o.1;
                    l.b -= o.2;
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
                (kind, s) => {
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
            f.eaten[fo.kind] += m;
            b.eaten[fo.kind] += m / k;
            harm += m / k * fo.tox * p.body_harm;
            // digested: the soft part, and the tough part as far as the gut holds it
            let tough = toughness(fo.a);
            let dig = (1.0 - tough) + tough * retention;
            gm += m / k * dig;
            ga += a / k;
            gb += bb / k;
            dung += m / k * (1.0 - dig);
        }
        let kept = gm * eff;
        b.fat += kept;
        f.returned += (gm - kept) * k;
        // A and B held up to what a tenth of its tissue holds; the rest, and what was not digested, to the litter
        let cap_a = 0.1 * b.ta.max(1e-6) + 1.0 * b.m;
        let cap_b = 0.1 * b.tb.max(1e-6) + 1.0 * b.m;
        let ka = ga.min((cap_a - b.pa).max(0.0));
        let kb = gb.min((cap_b - b.pb).max(0.0));
        b.pa += ka;
        b.pb += kb;
        let l = sh.lit.at(c);
        l.m += dung * k;
        l.a += (ga - ka) * k;
        l.b += (gb - kb) * k;
        if harm > 0.0 {
            b.harm += harm / b.m;
            let lost = shrink(b, harm.min(0.5 * b.m), sh, c, k);
            sh.lit.at(c).m += lost * k;
        }
    }

    // Water: drink from wet ground and pools (not the sea); lose it through soft open skin to dry air, and to
    // cooling. In water nothing is lost, and breath comes through the soft open skin.
    let target = b.target_water();
    if sea {
        let need = upkeep_rate * dt;
        let supply = p.breath * fm.soft * d2 * dt;
        if supply < need {
            b.harm += 0.2 * (1.0 - supply / need.max(1e-30));
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
        let avail = (*g * 0.01).max(0.0) / k; // kg for each of its animals: at most 1% of the cell's water an update
        let drink = (target - b.w).max(0.0).min(avail).min(0.5 * target * dt * 4.0);
        b.w += drink;
        *g -= drink * k;
        f.drunk += drink * k;
        if b.w < 0.5 * target {
            b.dead = Death::Thirst;
        }
    }

    // Upkeep and work, from the fat; short of fat, the tissue burns.
    let cost = upkeep_rate * dt + work;
    if b.id < x.trace && b.age < 30.0 {
        eprintln!(
            "trace {} age {:.1} sea {} m {:.3e}/{:.3e} fat {:.2}cap w {:.2}tgt t {:.1} env {:.1} topt {:.1}/{:.1} act {:.2} v {:.3} path {:.0}m upkeep {:.2e} work {:.2e} gutcap {:.2e} foods {} pressure {:.1e} height {:.3} mouth {:.1} harm {:.2} dir {}",
            b.id, b.age, sea as u8, b.m, bt.adult(), b.fat / fat_cap, b.w / target, tb, t_env, t_opt, breadth, act, v, path, upkeep_rate * dt, work, gut_cap, foods.len(), pressure, height, fm.mouth, b.harm, dir
        );
    }
    b.fat -= cost;
    f.returned += cost * k;
    if b.fat < 0.0 {
        // what the fat could not pay is paid by the tissue, as far as it goes
        let lack = -b.fat;
        b.fat = 0.0;
        f.returned -= lack * k;
        f.returned += shrink(b, lack, sh, c, k) * k;
    }
    if b.fat > fat_cap {
        // more than it can hold is burnt
        f.returned += (b.fat - fat_cap) * k;
        b.fat = fat_cap;
    }

    // Growth towards its adult mass, from the fat, with A and B at its tissue's shares.
    let adult = bt.adult();
    if b.m < adult && b.fat > 0.2 * fat_cap {
        let dm = (p.grow_rate * activity(fm.b) * ft.min(1.5) * b.m * dt).min(adult - b.m).min(b.fat / 1.3);
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

    // Breeding: when grown past its maturity and it chooses to, a share of its fat goes into eggs.
    let grown = (b.m / egg).max(1.0).ln() / span;
    if breed && grown >= bt.tr[3] && b.fat > 0.5 * fat_cap && b.dead == Death::None {
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
            b.eggs = eggs as u32;
            b.egg_s = b.s;
        }
    }

    // Wear, cold, damage.
    b.age += dt;
    let lifespan = p.body_life + p.body_life_frame * fm.frac[FRAME] * fm.frame_tough;
    if tb < -2.0 {
        let lost = shrink(b, 0.002 * (-2.0 - tb) * b.m, sh, c, k);
        sh.lit.at(c).m += lost * k;
        if b.m < 0.5 * b.peak {
            b.dead = Death::Cold;
        }
    }
    if tb > t_hi + 5.0 {
        b.harm += 0.3;
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
    if b.dead != Death::None {
        return;
    }

    // Moving: towards the chosen neighbour, or wandering within its cell; climbing is paid.
    let dist = path / (p.cell_km * 1000.0); // cells
    if dist > 0.0 {
        if dir < 4 {
            let (dx, dy) = [(0.0, -1.0), (0.0, 1.0), (1.0, 0.0), (-1.0, 0.0)][dir];
            let (nx, ny) = ((b.x + dx * dist).rem_euclid(n as f64), (b.y + dy * dist).rem_euclid(n as f64));
            let nc = (ny as usize).min(n - 1) * n + (nx as usize).min(n - 1);
            if nc != c {
                let rise = (x.ter.air[nc] - x.ter.air[c]).max(0.0);
                let climb = wet * G * rise / ENERGY;
                if climb < b.fat {
                    b.fat -= climb;
                    f.returned += climb * k;
                    b.x = nx;
                    b.y = ny;
                    b.cell = nc as u32;
                    b.travel += 1.0;
                    f.moved += 1.0;
                }
            } else {
                b.x = nx;
                b.y = ny;
            }
        } else {
            let (cx, cy) = (b.x.floor(), b.y.floor());
            let a = TAU * b.f64();
            b.x = cx + (b.x - cx + dist * a.cos()).clamp(0.0, 0.999_999);
            b.y = cy + (b.y - cy + dist * a.sin()).clamp(0.0, 0.999_999);
        }
    }
}

/// Tissue lost (burnt for energy, or harmed away): its A and B go to the litter of the cell; the mass lost is
/// returned for the caller to send to the air or the litter.
fn shrink(b: &mut Body, lost: f64, sh: &Sh, c: usize, k: f64) -> f64 {
    let q = (lost / b.m.max(1e-30)).clamp(0.0, 1.0);
    let (dm, da, db) = (b.m * q, b.ta * q, b.tb * q);
    b.m -= dm;
    b.ta -= da;
    b.tb -= db;
    let l = sh.lit.at(c);
    l.a += da * k;
    l.b += db * k;
    dm
}
