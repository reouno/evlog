//! The genome language (#116), shared by everything that lives: four letters, genes of 16 bases.
//!
//! A gene is a u32 (2 bits a base): 4 bases name its target (one of 256 addresses, each a physical
//! quantity), 4 its condition (none, or a signal above or below a level), 8 its value. A trait is the sum of
//! the values of the genes that name it and whose condition holds, squashed into its physical range. An
//! address nothing reads is silent. Mutation: a point change, a duplication or a deletion of a gene.

use crate::noise::Rng;

/// Producer traits read at addresses 0..P_TRAITS; eater traits at EATER..EATER + E_TRAITS; the rest is silent.
pub const P_TRAITS: usize = 20;
pub const EATER: usize = 32;
pub const E_TRAITS: usize = 4;
pub const COMPOUND: usize = 16; // a producer gene here makes a compound with its own key
pub const DETOX: usize = EATER; // an eater gene here carries a detox key
// e114 (#133): the lock of a genotype's bulk, the key of the first gene read here (none: lock 0, the plain bond).
// Each kind's address sits one point change from its keys' (producers' compound 16, eaters' keys 32).
pub const LOCK: usize = 20;
pub const E_LOCK: usize = EATER + 4;
pub const SIGNALS: usize = 8;
const GENE_STEP: f64 = 2.0; // the largest value a gene adds, in the squash's units

/// (name, lo, hi, on a log scale). Alloc 0-4 are logits shared out by softmax, not squashed.
pub const P_RANGE: [(&str, f64, f64, bool); P_TRAITS] = [
    ("alloc_leaf", 0.0, 0.0, false),
    ("alloc_wood", 0.0, 0.0, false),
    ("alloc_root", 0.0, 0.0, false),
    ("alloc_store", 0.0, 0.0, false),
    ("alloc_seed", 0.0, 0.0, false),
    ("leaf_b", 0.005, 0.05, true),
    ("leaf_a", 0.001, 0.05, true),
    ("wood_b", 0.0005, 0.01, true),
    ("wood_a", 0.0005, 0.03, true),
    ("root_b", 0.003, 0.04, true),
    ("root_a", 0.001, 0.04, true),
    ("height", 0.05, 50.0, true),
    ("deep", 0.0, 1.0, false),
    ("seed_mass", 1e-7, 1e-2, true),
    ("wing", 0.0, 0.5, false),
    ("float", 0.0, 0.5, false),
    ("compound", 1e-4, 0.1, true),
    ("t_opt", -10.0, 40.0, false),
    ("breadth", 5.0, 25.0, true),
    ("shed", 0.01, 20.0, true),
];

pub const E_RANGE: [(&str, f64, f64, bool); E_TRAITS] =
    [("detox", 0.0, 0.0, false), ("t_opt", -10.0, 40.0, false), ("tolerance", 0.0, 4.0, false), ("wing", 0.0, 1.0, false)];

pub fn squash(x: f64, lo: f64, hi: f64, log: bool) -> f64 {
    let s = 1.0 / (1.0 + (-x).exp());
    if log {
        (lo.ln() + (hi.ln() - lo.ln()) * s).exp()
    } else {
        lo + (hi - lo) * s
    }
}

pub fn target(g: u32) -> usize {
    (g >> 24) as usize
}
pub fn cond(g: u32) -> u32 {
    (g >> 16) & 0xFF
}
pub fn value(g: u32) -> f64 {
    ((g & 0xFFFF) as u16 as i16) as f64 / 32768.0 * GENE_STEP
}
/// A compound or detox gene: its key is the value's low byte, its amount the high byte.
pub fn key(g: u32) -> u8 {
    (g & 0xFF) as u8
}
fn amount(g: u32) -> f64 {
    (((g >> 8) & 0xFF) as u8 as i8) as f64 / 128.0 * GENE_STEP
}

/// A condition: None, or (signal, above, level in [0, 1]).
pub fn condition(g: u32) -> Option<(usize, bool, f64)> {
    let c = cond(g);
    if c < 128 {
        None
    } else {
        Some((((c >> 4) & 7) as usize, (c >> 3) & 1 == 1, (c & 7) as f64 / 7.0))
    }
}

/// What a producer is at a moment, the traits squashed into their ranges.
#[derive(Clone, Default)]
pub struct Pheno {
    pub alloc: [f64; 5], // leaf, wood, root, store, seed
    pub leaf_b: f64,
    pub leaf_a: f64,
    pub wood_b: f64,
    pub wood_a: f64,
    pub root_b: f64,
    pub root_a: f64,
    pub height: f64,
    pub deep: f64,
    pub seed_mass: f64,
    pub wing: f64,
    pub float: f64,
    pub compound: f64, // share of new leaf mass made as compound (0 without compound genes)
    pub t_opt: f64,
    pub breadth: f64,
    pub shed: f64,
    pub keys: [u8; 8],
    pub n_keys: usize,
    pub lock: u8, // e114: its bulk's lock
}

pub struct EPheno {
    pub t_opt: f64,
    pub tolerance: f64,
    pub wing: f64,
    pub keys: Vec<u8>,
    pub lock: u8, // e114
}

pub struct Genotype {
    pub genes: Vec<u32>,
    pub parent: u32,
    pub born: u32, // year
    raw: [f64; P_TRAITS],
    keys: Vec<u8>,
    cond: Vec<(usize, bool, f64, usize, f64, u8)>, // signal, above, level, trait, value, key
    lock: u8,
    pub base: Pheno,   // with no condition holding
    pub eater: Option<EPheno>,
}

impl Genotype {
    pub fn new(genes: Vec<u32>, parent: u32, born: u32, eater: bool) -> Self {
        let mut raw = [0.0; P_TRAITS];
        let mut keys = Vec::new();
        let mut cond = Vec::new();
        let mut ecount = [0.0f64; E_TRAITS];
        let mut ekeys = Vec::new();
        let mut lock = None;
        for &g in &genes {
            let t = target(g);
            if t == if eater { E_LOCK } else { LOCK } {
                lock.get_or_insert(key(g));
                continue;
            }
            if eater {
                // Eaters read their addresses unconditionally in rung 2.
                if t == DETOX {
                    ekeys.push(key(g));
                } else if (EATER..EATER + E_TRAITS).contains(&t) {
                    ecount[t - EATER] += value(g);
                }
                continue;
            }
            if t >= P_TRAITS {
                continue;
            }
            let (v, k) = if t == COMPOUND { (amount(g), key(g)) } else { (value(g), 0) };
            match condition(g) {
                None => {
                    raw[t] += v;
                    if t == COMPOUND {
                        keys.push(k);
                    }
                }
                Some((s, above, level)) => cond.push((s, above, level, t, v, k)),
            }
        }
        let e = eater.then(|| EPheno {
            t_opt: squash(ecount[1], E_RANGE[1].1, E_RANGE[1].2, false),
            tolerance: squash(ecount[2], E_RANGE[2].1, E_RANGE[2].2, false),
            wing: squash(ecount[3], E_RANGE[3].1, E_RANGE[3].2, false),
            keys: ekeys,
            lock: lock.unwrap_or(0),
        });
        let mut gt = Genotype { genes, parent, born, raw, keys, cond, lock: lock.unwrap_or(0), base: Pheno::default(), eater: e };
        if !eater {
            gt.base = gt.decode(&gt.raw, &gt.keys);
        }
        gt
    }

    pub fn conditional(&self) -> bool {
        !self.cond.is_empty()
    }

    /// The phenotype under these signals (each in [0, 1]).
    pub fn pheno(&self, sig: &[f64; SIGNALS]) -> Pheno {
        if self.cond.is_empty() {
            return self.base.clone();
        }
        let mut raw = self.raw;
        let mut keys = self.keys.clone();
        let mut any = false;
        for &(s, above, level, t, v, k) in &self.cond {
            if (sig[s] > level) == above {
                raw[t] += v;
                if t == COMPOUND {
                    keys.push(k);
                }
                any = true;
            }
        }
        if !any {
            return self.base.clone();
        }
        self.decode(&raw, &keys)
    }

    fn decode(&self, raw: &[f64; P_TRAITS], keys: &[u8]) -> Pheno {
        let q = |i: usize| squash(raw[i], P_RANGE[i].1, P_RANGE[i].2, P_RANGE[i].3);
        let m = raw[..5].iter().cloned().fold(f64::MIN, f64::max);
        let e: Vec<f64> = raw[..5].iter().map(|x| (x - m).exp()).collect();
        let s: f64 = e.iter().sum();
        let mut k = [0u8; 8];
        let n_keys = keys.len().min(8);
        k[..n_keys].copy_from_slice(&keys[..n_keys]);
        Pheno {
            alloc: [e[0] / s, e[1] / s, e[2] / s, e[3] / s, e[4] / s],
            leaf_b: q(5),
            leaf_a: q(6),
            wood_b: q(7),
            wood_a: q(8),
            root_b: q(9),
            root_a: q(10),
            height: q(11),
            deep: q(12),
            seed_mass: q(13),
            wing: q(14),
            float: q(15),
            compound: if n_keys > 0 { q(16) } else { 0.0 },
            t_opt: q(17),
            breadth: q(18),
            shed: q(19),
            keys: k,
            n_keys,
            lock: self.lock,
        }
    }
}

/// A random genome whose genes name the addresses its kind reads (a first population, not a design).
pub fn random(rng: &mut Rng, eater: bool) -> Vec<u32> {
    let n = if eater { 4 + rng.below(9) } else { 12 + rng.below(21) };
    (0..n)
        .map(|_| {
            let t = if eater { EATER + rng.below(E_TRAITS) } else { rng.below(P_TRAITS) } as u32;
            (t << 24) | (rng.next_u64() as u32 & 0x00FF_FFFF)
        })
        .collect()
}

/// One mutation: a point change (7 in 10), a duplication or a deletion of a gene.
pub fn mutate(genes: &[u32], rng: &mut Rng) -> Vec<u32> {
    let mut g = genes.to_vec();
    let r = rng.f64();
    if r < 0.7 || g.len() < 2 {
        let i = rng.below(g.len());
        let b = rng.below(16) * 2;
        let old = (g[i] >> b) & 3;
        let new = (old + 1 + rng.below(3) as u32) & 3;
        g[i] = (g[i] & !(3 << b)) | (new << b);
    } else if r < 0.85 {
        let i = rng.below(g.len());
        g.insert(i + 1, g[i]);
    } else {
        g.remove(rng.below(g.len()));
    }
    g
}

pub fn hamming(a: u8, b: u8) -> u32 {
    (a ^ b).count_ones()
}

/// e114 (#133), a key opens a lock: how much of a bulk with this lock these keys take apart, 0 to 1. The plain
/// bond (lock 0) is open to all, so a lock's distance from it is how far it is from being opened without a key;
/// past the tolerance each bit of distance closes an eighth, the curve a compound's harm follows.
pub fn fit(lock: u8, keys: &[u8], tolerance: f64) -> f64 {
    let d = keys.iter().map(|&k| hamming(lock, k)).fold(lock.count_ones(), u32::min) as f64;
    1.0 - ((d - tolerance).max(0.0) / 8.0).min(1.0)
}
