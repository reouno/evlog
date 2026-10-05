//! A body's form (#117 v2, e106; the faces and the compound are e110's): what a genome develops into, and the
//! summary physics reads of it.
//!
//! The form: an 8x8x8 grid in the body's own frame (x back to front, y left to right, mirrored, z down to up).
//! Each voxel is empty or tissue: a mix of six functions (frame, muscle, gut, nerve, fat, glue), an A share
//! (toughness), a B share (activity) and a share of compound. A gene of a voxel field adds its value where its
//! condition holds; the condition reads the voxel's place and the body's stage (its mass against its adult mass,
//! in 8 steps). Size is separate: the same shape at any mass, so the square-cube law is the only price of size.
//! Physics reads a summary of the form (`Form`), made once per genotype and stage.
//!
//! A body meets another with one of three faces - its front, its back, a side (the two sides are mirrors): each
//! face is the outermost layer of voxels that way, read as its area, how hard it is, its hardest tip and the
//! compound in it.

use crate::genome::{self, squash};
use crate::life::{activity, toughness};
use crate::noise::Rng;

const SIDE: usize = 8;
const VOX: usize = SIDE * SIDE * SIDE;
pub const STAGES: usize = 8;

// Genome addresses (the producers read 0..20, the small eaters 32..36).
const SCALAR: usize = 64; // body-level traits, read whatever their condition
pub const S_TRAITS: usize = 7;
const DETOX: usize = 80; // a gene here carries a detox key
const CKEY: usize = 82; // a gene here carries the key of the body's own compound (the first one read)
const FIELD: usize = 96; // voxel fields, read where their condition holds
const FIELDS: usize = 10; // present, six function logits, A share, B share, compound
const EVAL: usize = 112; // the food evaluator's weights
pub const NE: usize = 6;
const BEVAL: usize = 120; // the body evaluator's weights: pull, then press; the condition byte picks the reading
pub const NB: usize = 6;
const WEIGHT: usize = 128; // controller weights: the address picks the output, the condition byte the input
pub const NI: usize = 16;
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

pub const FRAME: usize = 0;
pub const MUSCLE: usize = 1;
pub const GUT: usize = 2;
pub const NERVE: usize = 3;
pub const FAT: usize = 4;
pub const GLUE: usize = 5;

pub const FRONT: usize = 0;
pub const BACK: usize = 1;
pub const FLANK: usize = 2;

const CMP_MAX: f64 = 0.05; // the largest share of a voxel's tissue that is compound

/// What physics reads of a form. Counts are in voxels or voxel faces; a body of dry mass m scales them by its
/// voxel side `d` (areas by d^2, volumes by d^3).
#[derive(Clone, Default)]
pub struct Form {
    pub nv: f64,
    pub frac: [f64; 6], // the share of the tissue in each function
    pub a: f64,         // A share of the tissue
    pub b: f64,         // B share, with what its compound binds
    pub b_act: f64,     // B share that works
    pub cmp: f64,       // compound share
    pub frame_tough: f64,
    pub ext: [f64; 3], // extent along x, y, z
    pub front: f64,    // faces seen from the front (the y-z projection)
    pub open: f64,     // open faces
    pub soft: f64,     // open faces, each weighted by its softness
    pub fat_skin: f64, // open faces, each weighted by the fat under it
    pub eye: f64,      // open faces of active nerve
    pub legs: f64,     // share of the tissue that is active muscle in columns reaching the body's bottom
    pub bite: f64,     // the front's pressure over the muscle's stress: muscle behind x the tip's hardness / front faces
    pub mouth: f64,    // gut faces on the front
    pub density: f64,  // kg a litre, wet
    // the three faces a body is met by: front, back, a side
    pub face_n: [f64; 3],    // voxels in the outermost layer that way
    pub face_hard: [f64; 3], // their mean hardness
    pub face_tip: [f64; 3],  // the hardest of them
    pub face_cmp: [f64; 3],  // their mean share of compound
    pub behind: f64,         // active muscle in the three layers behind the front, in voxels
    pub glue: f64,           // glue on the front, in voxel faces
}

pub struct BodyType {
    pub genes: Vec<u32>,
    pub parent: u32,
    pub root: u32, // the founder it descends from
    pub born: u32,
    pub tr: [f64; S_TRAITS],
    pub keys: Vec<u8>,
    pub ckey: u8,
    pub eval: [f64; NE],
    pub bev: [[f64; NB]; 2], // the body evaluator: pull, press
    pub w: [[f64; NI]; NO],
    pub forms: Vec<Form>, // one per stage; nv 0 is a form that cannot live
}

impl BodyType {
    /// `b_comp`: the B share of a compound (the producers' parameter).
    pub fn new(genes: Vec<u32>, parent: u32, born: u32, b_comp: f64) -> Self {
        let mut raw = [0.0; S_TRAITS];
        let mut keys = Vec::new();
        let mut ckey = None;
        let mut eval = [0.0; NE];
        let mut bev = [[0.0; NB]; 2];
        let mut w = [[0.0; NI]; NO];
        for &g in &genes {
            let t = genome::target(g);
            let v = genome::value(g);
            if (SCALAR..SCALAR + S_TRAITS).contains(&t) {
                raw[t - SCALAR] += v;
            } else if t == DETOX {
                keys.push(genome::key(g));
            } else if t == CKEY {
                ckey.get_or_insert(genome::key(g));
            } else if (EVAL..EVAL + NE).contains(&t) {
                eval[t - EVAL] += v;
            } else if (BEVAL..BEVAL + 2).contains(&t) {
                bev[t - BEVAL][genome::cond(g) as usize % NB] += v;
            } else if (WEIGHT..WEIGHT + NO).contains(&t) {
                w[t - WEIGHT][genome::cond(g) as usize % NI] += v;
            }
        }
        let mut tr = [0.0; S_TRAITS];
        for i in 0..S_TRAITS {
            tr[i] = squash(raw[i], S_RANGE[i].1, S_RANGE[i].2, S_RANGE[i].3);
        }
        let fg = field_genes(&genes);
        let forms = (0..STAGES).map(|s| develop(&fg, (s as f64 + 0.5) / STAGES as f64, b_comp)).collect();
        BodyType { genes, parent, root: parent, born, tr, keys, ckey: ckey.unwrap_or(0), eval, bev, w, forms }
    }
    pub fn adult(&self) -> f64 {
        self.tr[0]
    }
    pub fn egg(&self) -> f64 {
        self.tr[0] * self.tr[1]
    }
}

type FieldGene = (usize, Option<(usize, bool, f64)>, f64);

/// The genes of the voxel fields, in the genome's order: the field, the condition, the value.
fn field_genes(genes: &[u32]) -> Vec<FieldGene> {
    genes
        .iter()
        .filter(|&&g| (FIELD..FIELD + FIELDS).contains(&genome::target(g)))
        .map(|&g| (genome::target(g) - FIELD, genome::condition(g), genome::value(g)))
        .collect()
}

/// The voxels of a genotype's form at a stage, for the viewer: 0 empty, else 1 + the function most of the
/// voxel's tissue serves, in the order the viewer's header names them (frame, muscle, nerve, gut, fat, glue).
pub fn voxels(bt: &BodyType, stage: u8) -> Vec<u8> {
    let l = lay(&field_genes(&bt.genes), (stage as f64 + 0.5) / STAGES as f64);
    const KIND: [u8; 6] = [1, 2, 4, 3, 5, 6]; // FRAME MUSCLE GUT NERVE FAT GLUE -> hard muscle digestive sensor fat glue
    (0..VOX)
        .map(|i| {
            if !l.on[i] {
                return 0;
            }
            let top = (0..6).max_by(|&a, &b| l.mix[i][a].partial_cmp(&l.mix[i][b]).unwrap()).unwrap();
            KIND[top]
        })
        .collect()
}

/// Every voxel's fields at a stage: whether it is on, its mix of functions, its A, B and compound shares.
struct Lay {
    on: [bool; VOX],
    mix: Vec<[f64; 6]>,
    sa: [f64; VOX],
    sb: [f64; VOX],
    cm: [f64; VOX],
}

/// The fields at a stage, with only the largest face-connected part kept.
fn lay(fg: &[FieldGene], stage: f64) -> Lay {
    let mut l = Lay { on: [false; VOX], mix: vec![[0.0f64; 6]; VOX], sa: [0.0; VOX], sb: [0.0; VOX], cm: [0.0; VOX] };
    for z in 0..SIDE {
        for y in 0..SIDE {
            for x in 0..SIDE {
                let i = (z * SIDE + y) * SIDE + x;
                let fx = (x as f64 + 0.5) / SIDE as f64;
                let fy = (y as f64 + 0.5 - SIDE as f64 / 2.0).abs() / (SIDE as f64 / 2.0); // 0 at the middle, 1 at a side
                let fz = (z as f64 + 0.5) / SIDE as f64;
                let r = (((fx - 0.5).powi(2) + (fy * 0.5).powi(2) + (fz - 0.5).powi(2)).sqrt() / 0.75f64.sqrt()).min(1.0);
                let sig = [fx, fy, fz, r, stage, 4.0 * fx * (1.0 - fx), 4.0 * fz * (1.0 - fz), stage];
                // defaults: a round blob, an even mix, mid shares, no compound
                let mut f = [0.0; FIELDS];
                f[0] = 1.0 - 3.0 * r;
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
                l.on[i] = true;
                let m = f[1..7].iter().cloned().fold(f64::MIN, f64::max);
                let e: Vec<f64> = f[1..7].iter().map(|v| (v - m).exp()).collect();
                let s: f64 = e.iter().sum();
                for k in 0..6 {
                    l.mix[i][k] = e[k] / s;
                }
                l.sa[i] = squash(f[7], 0.001, 0.1, true);
                l.sb[i] = squash(f[8], 0.005, 0.1, true);
                l.cm[i] = (CMP_MAX * f[9]).clamp(0.0, CMP_MAX);
            }
        }
    }
    // Keep the largest face-connected part.
    let mut label = [usize::MAX; VOX];
    let (mut best, mut best_n) = (usize::MAX, 0usize);
    let mut stack = Vec::new();
    for s in 0..VOX {
        if !l.on[s] || label[s] != usize::MAX {
            continue;
        }
        label[s] = s;
        stack.push(s);
        let mut cnt = 0;
        while let Some(i) = stack.pop() {
            cnt += 1;
            for j in adj(i).into_iter().flatten() {
                if l.on[j] && label[j] == usize::MAX {
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
    if best_n > 0 {
        for i in 0..VOX {
            l.on[i] = l.on[i] && label[i] == best;
        }
    }
    l
}

/// The form at a stage: every voxel's fields from the genes whose condition holds there, the largest connected
/// part kept, and the summary physics reads.
fn develop(fg: &[FieldGene], stage: f64, b_comp: f64) -> Form {
    let Lay { on, mix, sa, sb, cm } = lay(fg, stage);
    let mut f = Form::default();
    if !on.iter().any(|&o| o) {
        return f;
    }
    let hard = |i: usize| mix[i][FRAME] * toughness(sa[i]);
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
        f.b_act += sb[i];
        f.cmp += cm[i];
        f.frame_tough += hard(i);
        frame_w += mix[i][FRAME];
        f.density += 1.05 * (1.0 - mix[i][FAT]) + 0.9 * mix[i][FAT] + 0.9 * hard(i);
        for j in adj(i) {
            if j.is_none_or(|j| !on[j]) {
                f.open += 1.0;
                f.soft += 1.0 - hard(i);
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
    f.b_act /= nv;
    f.cmp /= nv;
    f.b = f.b_act + f.cmp * b_comp;
    f.density /= nv;
    f.frame_tough = if frame_w > 0.0 { f.frame_tough / frame_w } else { 0.0 };
    for k in 0..3 {
        f.ext[k] = (hi[k] + 1 - lo[k]) as f64;
    }
    f.front = proj_front.iter().filter(|&&b| b).count() as f64;
    // Legs: muscle in the columns that reach the body's lowest layer. The faces: the outermost layer each way.
    // The front also has the muscle in the three layers behind it, its gut (a mouth) and its glue.
    let mut legs = 0.0;
    for i in 0..VOX {
        if !on[i] {
            continue;
        }
        let (x, y) = (i % SIDE, (i / SIDE) % SIDE);
        if colmin[y * SIDE + x] == lo[2] {
            legs += mix[i][MUSCLE] * activity(sb[i]);
        }
        for (k, at) in [x == hi[0], x == lo[0], y == hi[1]].into_iter().enumerate() {
            if at {
                f.face_n[k] += 1.0;
                f.face_hard[k] += hard(i);
                f.face_tip[k] = f.face_tip[k].max(hard(i));
                f.face_cmp[k] += cm[i];
            }
        }
        if x == hi[0] {
            f.mouth += mix[i][GUT];
            f.glue += mix[i][GLUE];
        }
        if x + 3 > hi[0] {
            f.behind += mix[i][MUSCLE] * activity(sb[i]);
        }
    }
    for k in 0..3 {
        f.face_hard[k] /= f.face_n[k].max(1.0);
        f.face_cmp[k] /= f.face_n[k].max(1.0);
    }
    f.legs = legs / nv;
    f.bite = f.behind * (0.1 + 0.9 * f.face_tip[FRONT]) / f.face_n[FRONT].max(1.0);
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
            } else if r < 0.27 {
                CKEY
            } else if r < 0.55 {
                FIELD + rng.below(FIELDS)
            } else if r < 0.63 {
                EVAL + rng.below(NE)
            } else if r < 0.73 {
                BEVAL + rng.below(2)
            } else {
                WEIGHT + rng.below(NO)
            } as u32;
            (t << 24) | (rng.next_u64() as u32 & 0x00FF_FFFF)
        })
        .collect()
}
