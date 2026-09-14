//! The bodies of the season world, ported from e059 (`experiments/e059_places/src/main.rs`) with
//! the laws its default world kept and nothing else:
//!
//! - a genome of 512 bases develops a body of blocks (hard, muscle, sensor, gut) on a grid whose
//!   side the genome expresses, 4 to 16 (e004, e028); the reflex policy is read from the same run;
//! - a block weighs by its kind (hard 2, sensor 1/2, the rest 1) times a density the genome
//!   expresses, 1/2 to 2, and a face's hardness is the material's times the density (e025);
//! - blocks join through their sides and corners, and a body is its largest part, at birth and
//!   after every break and worn block (e045, e047);
//! - a body holds its own sub-cells, four to a world cell a side (e014), and meets another face to
//!   face: the softer face breaks when the muscle behind the pressing line exceeds it, and a gut
//!   takes what it broke (e010); a shove moves a body lighter than the force (e015);
//! - a move costs the mass moved times the distance (e015) and needs its muscle: each sub-cell and
//!   each turn happens with chance muscle over mass (e048);
//! - the upkeep paid from the energy is fixed in the flesh as fat, at most 5 per unit of mass, and
//!   the fat pays what the energy cannot; a body that cannot pay its upkeep or its moves dies
//!   (e024, e030, e042);
//! - every block may fail each turn with a chance that doubles every 300 turns of the body's age,
//!   half of them by 3,000 (e044);
//! - a body of mass m takes (16 / m)^0.5 turns a step, at most one (e052, e055);
//! - a sensor block sees one cell further, up to 8, what lies j cells away at 1/j (e023);
//! - a child is a crossover with a mate within 6 genes, mutated at 2 in 512 per base (e006, e021).
//!
//! Laws e059 carried as arguments at 0 (the digestion axis, the yolk, breeding as a decision,
//! thirst, the reach, the brain, the band of rain, fouling, the ground store) are not ported.
//! Two things change with the world: the sea is a wall (`WALL`), and what a body breaks and does
//! not eat, and what it leaves when it dies, lies as `carrion` on its world cell.
//!
//! e064 (#78) adds one number, a body's scale of matter `s`. A body keeps its energy, fat, blocks,
//! upkeep, bite, moves and threshold in its own units, and s turns them into the world's matter
//! wherever matter crosses between the two: what a gut takes, what a body spends, what lies dead.
//! A body lives the same life and draws s of the world's matter, a smaller animal on the same
//! pasture. A block's weight, its wear and the clock are not matter and do not scale.

pub const CELL_ENERGY: f32 = 0.02; // the matter of a block of mass 1: paid to build it, gained when it is eaten
pub const INIT_ENERGY: f32 = 5.0;
pub const UPKEEP: f32 = 0.002; // per block per step
pub const UPKEEP_BODY: f32 = 0.032; // per body per step, besides its blocks (e016: the world's compute is per body)
pub const MOVE_COST: f32 = 0.001; // per unit of mass moved per sub-cell (work = force x distance)
pub const BITE: f32 = 0.02; // what a gut block takes a step
pub const STORE: f32 = 5.0; // fat the flesh holds per unit of mass (e030)
pub const WEAR: f64 = 3_000.0; // a block's median life in turns (e044)
pub const WEAR_SPANS: f64 = 10.0; // the chance doubles every tenth of it
pub const CLOCK: f32 = 0.5; // the exponent of a body's pace on its mass (e055)
pub const CLOCK_MASS: f32 = 16.0; // a body this heavy or lighter takes a turn every step
pub const EYES: usize = 8; // the most cells sensor blocks add to the range (e023)
pub const MUTATION: f32 = 2.0 / N as f32; // chance per base per copy (e021's two per child on average)
pub const HARDNESS: u8 = 3; // a hard block resists this much per contiguous hard block behind the face; other blocks 1
pub const KIND_MASS: [f32; N_KINDS] = [0.0, 2.0, 1.0, 0.5, 1.0]; // empty, hard, muscle, sensor, gut (e025)
pub const DENSITY_RANGE: f32 = 2.0; // the density a genome expresses: DENSITY_RANGE^(2 sigmoid(s) - 1)

// Genome and network (e002, e004).
pub const N: usize = 512;
const PROMOTER: [u8; 3] = [0, 1, 0];
const GENE_LEN: usize = 8;
const TAG_LEN: usize = 4;
const T: usize = 40;

// Body (e004, e028). The cells of a body of side s are stored row by row at stride s in the first
// s * s entries of a CELLS array.
pub const SIDE: usize = 8; // what the side grows around
pub const SIDE_MAX: usize = 16;
const SIDE_MIN: usize = 4;
pub const CELLS: usize = SIDE_MAX * SIDE_MAX;
const SIDE_RANGE: f32 = 2.0;
pub const N_KINDS: usize = 5;
pub const HARD: usize = 1;
pub const MUSCLE: usize = 2;
pub const SENSOR: usize = 3;
pub const DIGESTIVE: usize = 4;
const N_MORPH: usize = 6;

// Space: a world cell is SUB x SUB sub-cells; occupancy per sub-cell, food per world cell.
pub const SUB: usize = 4;
pub const SUB_CELLS: usize = SUB * SUB;

// Policy: 10 inputs -> 4 actions (stay, forward, turn left, turn right). The inputs: food under the
// body; food and bodies ahead, behind, left and right; energy over the threshold to breed.
pub const N_IN: usize = 10;
pub const N_OUT: usize = 4;
pub const N_POLICY: usize = N_IN * N_OUT + N_OUT;
const K: usize = N_KINDS + N_POLICY;

pub const NORTH: usize = 0;
pub const SOUTH: usize = 1;
pub const EAST: usize = 2;
pub const WEST: usize = 3;
pub const DIRS: [usize; 4] = [NORTH, SOUTH, EAST, WEST];

// Lineages (e006).
pub const D: usize = 6; // two bodies can mate if their gene lists differ by at most D
pub const MIN_LINEAGE: usize = 5;
pub const LINEAGE_CONFIRM: u32 = 5;

pub struct Rng(pub u64);

impl Rng {
    pub fn next_u64(&mut self) -> u64 {
        let mut x = self.0;
        x ^= x >> 12;
        x ^= x << 25;
        x ^= x >> 27;
        self.0 = x;
        x.wrapping_mul(0x2545F4914F6CDD1D)
    }
    pub fn f32(&mut self) -> f32 {
        (self.next_u64() >> 40) as f32 / (1u64 << 24) as f32
    }
    /// 53 bits: the wear's chance starts at 1.6e-6, 27 steps of an f32's 2^-24.
    pub fn f64(&mut self) -> f64 {
        (self.next_u64() >> 11) as f64 / (1u64 << 53) as f64
    }
    pub fn below(&mut self, n: usize) -> usize {
        (self.next_u64() % n as u64) as usize
    }
}

pub fn opposite(d: usize) -> usize {
    match d {
        NORTH => SOUTH,
        SOUTH => NORTH,
        EAST => WEST,
        _ => EAST,
    }
}

/// The world direction to the left of facing `d`.
pub fn left_of(d: usize) -> usize {
    match d {
        NORTH => WEST,
        WEST => SOUTH,
        SOUTH => EAST,
        _ => NORTH,
    }
}

/// Where cell i of a grid of side `s` lands in the world frame when the body faces `f`.
fn to_world(i: usize, f: usize, s: usize) -> usize {
    let (r, c) = (i / s, i % s);
    let m = s - 1;
    let (r2, c2) = match f {
        NORTH => (r, c),
        SOUTH => (m - r, m - c),
        EAST => (c, m - r),
        _ => (m - c, r),
    };
    r2 * s + c2
}

/// The inverse of `to_world`.
fn to_body(i: usize, f: usize, s: usize) -> usize {
    let (r2, c2) = (i / s, i % s);
    let m = s - 1;
    let (r, c) = match f {
        NORTH => (r2, c2),
        SOUTH => (m - r2, m - c2),
        EAST => (m - c2, r2),
        _ => (c2, m - r2),
    };
    r * s + c
}

pub fn rotate(cells: &[u8; CELLS], f: usize, s: usize) -> [u8; CELLS] {
    let mut out = [0u8; CELLS];
    for (i, &c) in cells.iter().enumerate().take(s * s) {
        out[to_world(i, f, s)] = c;
    }
    out
}

/// The cells a grid of side `s` holds (their indices) and their bounding box (r0, r1, c0, c1).
pub fn filled(cells: &[u8; CELLS], s: usize) -> ([u8; CELLS], u16, [u8; 4]) {
    let mut list = [0u8; CELLS];
    let mut n = 0u16;
    let mut bb = [s as u8, 0, s as u8, 0];
    for (i, &c) in cells.iter().enumerate().take(s * s) {
        if c != 0 {
            list[n as usize] = i as u8;
            n += 1;
            let (r, col) = ((i / s) as u8, (i % s) as u8);
            bb = [bb[0].min(r), bb[1].max(r), bb[2].min(col), bb[3].max(col)];
        }
    }
    if n == 0 {
        bb = [0; 4];
    }
    (list, n, bb)
}

fn neighbor(pos: usize, d: usize, s: usize) -> Option<usize> {
    let (r, c) = (pos / s, pos % s);
    let (r, c) = match d {
        NORTH => (r.checked_sub(1)?, c),
        SOUTH => (r + 1, c),
        EAST => (r, c + 1),
        _ => (r, c.checked_sub(1)?),
    };
    (r < s && c < s).then_some(r * s + c)
}

/// The parts of a grid (e045, e047): each block labeled by its part, blocks joined through their
/// sides and corners, numbered from 1 in grid order. Returns the labels and the number of parts.
pub fn parts_of(cells: &[u8; CELLS], s: usize) -> ([u8; CELLS], usize) {
    let mut label = [0u8; CELLS];
    let mut n = 0usize;
    let mut stack: Vec<usize> = Vec::new();
    for start in 0..s * s {
        if cells[start] == 0 || label[start] != 0 {
            continue;
        }
        n += 1;
        label[start] = n as u8;
        stack.push(start);
        while let Some(p) = stack.pop() {
            let (r, c) = ((p / s) as i32, (p % s) as i32);
            for dr in -1..=1 {
                for dc in -1..=1 {
                    let (rr, cc) = (r + dr, c + dc);
                    if (dr == 0 && dc == 0) || rr < 0 || cc < 0 || rr >= s as i32 || cc >= s as i32 {
                        continue;
                    }
                    let q = rr as usize * s + cc as usize;
                    if cells[q] != 0 && label[q] == 0 {
                        label[q] = n as u8;
                        stack.push(q);
                    }
                }
            }
        }
    }
    (label, n)
}

/// The part a body keeps: the most blocks, then the heavier, then the first in grid order.
fn kept_part(cells: &[u8; CELLS], s: usize, label: &[u8; CELLS], n: usize) -> u8 {
    let mut size = vec![0u16; n + 1];
    let mut mass = vec![0.0f32; n + 1];
    for i in 0..s * s {
        let l = label[i] as usize;
        if l > 0 {
            size[l] += 1;
            mass[l] += KIND_MASS[cells[i] as usize];
        }
    }
    let mut best = 0usize;
    for l in 1..=n {
        if best == 0 || size[l] > size[best] || (size[l] == size[best] && mass[l] > mass[best]) {
            best = l;
        }
    }
    best as u8
}

/// Clear every block of a grid outside the part a body keeps (at birth). Returns the blocks cleared.
fn keep_largest(cells: &mut [u8; CELLS], s: usize) -> u16 {
    let (label, n) = parts_of(cells, s);
    if n < 2 {
        return 0;
    }
    let keep = kept_part(cells, s, &label, n);
    let mut cut = 0u16;
    for (cell, &l) in cells.iter_mut().zip(&label).take(s * s) {
        if l != 0 && l != keep {
            *cell = 0;
            cut += 1;
        }
    }
    cut
}

/// The hardness of the face of the cell at `pos` that looks against direction `into` (e010).
fn face_hardness(cells: &[u8; CELLS], pos: usize, into: usize, s: usize) -> u8 {
    if cells[pos] != HARD as u8 {
        return 1;
    }
    let mut n = 0u8;
    let mut p = Some(pos);
    while let Some(q) = p {
        if cells[q] != HARD as u8 {
            break;
        }
        n += 1;
        p = neighbor(q, into, s);
    }
    HARDNESS * n
}

/// The line (in the frame of the grid) cell `pos` belongs to when the body moves in direction d.
fn line_of(pos: usize, d: usize, s: usize) -> usize {
    match d {
        NORTH | SOUTH => pos % s,
        _ => pos / s,
    }
}

/// A small set of world cells: a body of side SIDE_MAX lies over at most 5x5.
pub const UNDER_MAX: usize = (SIDE_MAX / SUB + 1) * (SIDE_MAX / SUB + 1);

#[derive(Clone, Copy)]
pub struct CellsUnder {
    pub c: [usize; UNDER_MAX],
    pub n: usize,
}

impl Default for CellsUnder {
    fn default() -> Self {
        CellsUnder { c: [0; UNDER_MAX], n: 0 }
    }
}

impl CellsUnder {
    pub fn contains(&self, x: usize) -> bool {
        self.c[..self.n].contains(&x)
    }
    pub fn add(&mut self, x: usize) {
        if !self.contains(x) && self.n < UNDER_MAX {
            self.c[self.n] = x;
            self.n += 1;
        }
    }
    pub fn iter(&self) -> impl Iterator<Item = usize> + '_ {
        self.c[..self.n].iter().copied()
    }
}

#[derive(PartialEq)]
pub struct Gene {
    tag: [u8; TAG_LEN],
    product: [u8; TAG_LEN],
}

impl Gene {
    pub fn key(&self) -> u16 {
        self.tag.iter().chain(&self.product).fold(0, |acc, &s| acc * 4 + s as u16)
    }
}

pub fn sorted_keys(genes: &[Gene]) -> Vec<u16> {
    let mut k: Vec<u16> = genes.iter().map(Gene::key).collect();
    k.sort_unstable();
    k
}

/// The number of genes in one list but not the other (with multiplicity).
pub fn gene_distance(a: &[u16], b: &[u16]) -> usize {
    let (mut i, mut j, mut d) = (0, 0, 0);
    while i < a.len() && j < b.len() {
        if a[i] == b[j] {
            i += 1;
            j += 1;
        } else if a[i] < b[j] {
            i += 1;
            d += 1;
        } else {
            j += 1;
            d += 1;
        }
    }
    d + (a.len() - i) + (b.len() - j)
}

/// What a gene product does: to each kind of block and to the policy (the table), to the density
/// and to the side (their own columns, from their own streams, as in e059).
pub struct Laws {
    morphogen: [[u8; TAG_LEN]; N_MORPH],
    table: Vec<[f32; K]>,
    density: Vec<f32>,
    side: Vec<f32>,
    morph_level: Vec<[Vec<f32>; N_MORPH]>,
}

impl Laws {
    pub fn new(rng: &mut Rng, seed: u64) -> Self {
        let mut rng2 = Rng(seed.wrapping_mul(0x9E3779B97F4A7C15).wrapping_add(0x5851F42D4C957F2D) | 1);
        let density = (0..256).map(|_| rng2.f32() * 2.0 - 1.0).collect();
        let mut rng4 = Rng(seed.wrapping_mul(0xA0761D6478BD642F).wrapping_add(0xE7037ED1A0B428DB) | 1);
        let side = (0..256).map(|_| rng4.f32() * 2.0 - 1.0).collect();
        let mut morphogen = [[0u8; TAG_LEN]; N_MORPH];
        for m in morphogen.iter_mut() {
            for s in m.iter_mut() {
                *s = rng.below(4) as u8;
            }
        }
        let table = (0..256)
            .map(|_| {
                let mut row = [0.0; K];
                for v in row.iter_mut() {
                    *v = rng.f32() * 2.0 - 1.0;
                }
                row
            })
            .collect();
        // The gradients span the grid whatever its side: a pattern scales with its body.
        let morph_level = (0..=SIDE_MAX)
            .map(|s| {
                let n = s * s;
                let mut levels: [Vec<f32>; N_MORPH] = std::array::from_fn(|_| vec![0.0f32; n + 1]);
                let c = (s as f32 - 1.0) / 2.0;
                let rmax = (2.0 * c * c).sqrt();
                for i in 0..n {
                    let x = (i % s) as f32 / (s as f32 - 1.0);
                    let y = (i / s) as f32 / (s as f32 - 1.0);
                    let dx = (i % s) as f32 - c;
                    let dy = (i / s) as f32 - c;
                    let r = (dx * dx + dy * dy).sqrt() / rmax;
                    for (m, v) in [x, 1.0 - x, y, 1.0 - y, r, 1.0 - r].into_iter().enumerate() {
                        levels[m][i] = 2.0 * v - 1.0;
                    }
                }
                levels
            })
            .collect();
        Laws { morphogen, table, density, side, morph_level }
    }
}

pub fn parse_genes(genome: &[u8]) -> Vec<Gene> {
    let mut genes = Vec::new();
    let mut i = 0;
    while i + PROMOTER.len() + GENE_LEN <= genome.len() {
        if genome[i..i + PROMOTER.len()] == PROMOTER {
            let g = &genome[i + PROMOTER.len()..i + PROMOTER.len() + GENE_LEN];
            let mut tag = [0; TAG_LEN];
            let mut product = [0; TAG_LEN];
            tag.copy_from_slice(&g[..TAG_LEN]);
            product.copy_from_slice(&g[TAG_LEN..]);
            genes.push(Gene { tag, product });
        }
        i += 1;
    }
    genes
}

fn pattern_index(p: &[u8; TAG_LEN]) -> usize {
    p.iter().fold(0, |acc, &s| acc * 4 + s as usize)
}

fn bind(product: &[u8; TAG_LEN], tag: &[u8; TAG_LEN]) -> f32 {
    let m = product.iter().zip(tag).filter(|(a, b)| a == b).count();
    if m < 3 {
        return 0.0;
    }
    let sign = if product[0] < 2 { 1.0 } else { -1.0 };
    sign * (m as f32 - 2.0) / 2.0
}

fn bind_morphogen(morphogen: &[u8; TAG_LEN], tag: &[u8; TAG_LEN]) -> f32 {
    let m = morphogen.iter().zip(tag).filter(|(a, b)| a == b).count();
    if m < 2 {
        return 0.0;
    }
    let sign = if morphogen[0] < 2 { 1.0 } else { -1.0 };
    sign * m as f32 / 4.0
}

fn sigmoid(x: f32) -> f32 {
    1.0 / (1.0 + (-x).exp())
}

/// One line of a body seen from one side: how hard its tip is and the muscle behind it. Hardness
/// 0: nothing on the line to touch.
#[derive(Clone, Copy, Default)]
pub struct Tip {
    pub hardness: u8,
    pub force: u8,
}

fn tips_of(cells: &[u8; CELLS], s: usize) -> [[Tip; SIDE_MAX]; 4] {
    let mut tips = [[Tip::default(); SIDE_MAX]; 4];
    for side in 0..4 {
        for line in 0..s {
            let at = |k: usize| -> usize {
                match side {
                    NORTH => k * s + line,
                    SOUTH => (s - 1 - k) * s + line,
                    EAST => line * s + (s - 1 - k),
                    _ => line * s + k,
                }
            };
            let mut tip = Tip::default();
            let force = (0..s).filter(|&k| cells[at(k)] == MUSCLE as u8).count() as u8;
            if let Some(k0) = (0..s).find(|&k| cells[at(k)] != 0) {
                let hardness = if cells[at(k0)] == HARD as u8 { HARDNESS * (k0..s).take_while(|&k| cells[at(k)] == HARD as u8).count() as u8 } else { 1 };
                tip = Tip { hardness, force };
            }
            tips[side][line] = tip;
        }
    }
    tips
}

#[derive(Clone)]
pub struct Body {
    pub cells: [u8; CELLS],
    pub side: u8,
    pub size: u16,
    pub mass: f32,
    pub density: f32,
    pub kinds: [u16; N_KINDS],
    pub tips: [[Tip; SIDE_MAX]; 4],
    pub extent: [u8; 2], // cells along the facing and across it
    pub policy: [f32; N_POLICY],
    pub n_genes: u16,
    pub cut: u16, // blocks the genome wrote that were not built (outside the largest part)
}

impl Body {
    pub fn new(cells: [u8; CELLS], side: usize, policy: [f32; N_POLICY], n_genes: u16, density: f32) -> Self {
        let mut b = Body { cells, side: side as u8, size: 0, mass: 0.0, density, kinds: [0; N_KINDS], tips: [[Tip::default(); SIDE_MAX]; 4], extent: [0; 2], policy, n_genes, cut: 0 };
        b.refresh();
        b
    }
    pub fn empty() -> Self {
        Body::new([0; CELLS], SIDE, [0.0; N_POLICY], 0, 1.0)
    }
    pub fn s(&self) -> usize {
        self.side as usize
    }
    fn tips_on(&self, side: usize) -> &[Tip] {
        &self.tips[side][..self.s()]
    }
    /// What a block of `kind` weighs in this body (and the matter it is made of, over CELL_ENERGY).
    pub fn block_mass(&self, kind: u8) -> f32 {
        self.density * KIND_MASS[kind as usize]
    }
    /// The matter a block of `kind` is made of, and the whole body's, in f64: priced in f32 as a
    /// body and laid down block by block, the ledger drifted by 4e-9 a block.
    pub fn block_matter(&self, kind: u8) -> f64 {
        CELL_ENERGY as f64 * self.density as f64 * KIND_MASS[kind as usize] as f64
    }
    pub fn matter(&self) -> f64 {
        (1..N_KINDS).map(|k| self.kinds[k] as f64 * self.block_matter(k as u8)).sum()
    }
    pub fn refresh(&mut self) {
        self.kinds = [0; N_KINDS];
        for &c in &self.cells {
            self.kinds[c as usize] += 1;
        }
        self.size = CELLS as u16 - self.kinds[0];
        self.mass = (1..N_KINDS).map(|k| self.kinds[k] as f32 * self.block_mass(k as u8)).sum();
        self.tips = tips_of(&self.cells, self.s());
        let (_, n, bb) = filled(&self.cells, self.s());
        self.extent = if n == 0 { [0, 0] } else { [bb[1] - bb[0] + 1, bb[3] - bb[2] + 1] };
    }
    /// Muscle over mass.
    pub fn speed(&self) -> f32 {
        if self.mass <= 0.0 { 0.0 } else { self.kinds[MUSCLE] as f32 / self.mass }
    }
    /// The eye's range: one cell, and one more per sensor block up to EYES.
    pub fn range(&self) -> usize {
        1 + (self.kinds[SENSOR] as usize).min(EYES)
    }
    pub fn threshold(&self) -> f32 {
        2.0 + 0.1 * self.mass
    }
    /// For the logs only: the largest force behind a hard tip on the front, on any side, and the
    /// mean hardness of the tips that can be touched.
    pub fn bite(&self) -> u8 {
        self.tips_on(NORTH).iter().filter(|t| t.hardness > 1).map(|t| t.force).max().unwrap_or(0)
    }
    pub fn bite_any(&self) -> u8 {
        DIRS.iter().flat_map(|&d| self.tips_on(d)).filter(|t| t.hardness > 1).map(|t| t.force).max().unwrap_or(0)
    }
    pub fn shell(&self) -> f32 {
        let touchable: Vec<u8> = DIRS.iter().flat_map(|&d| self.tips_on(d)).filter(|t| t.hardness > 0).map(|t| t.hardness).collect();
        if touchable.is_empty() { 0.0 } else { touchable.iter().map(|&h| h as f32).sum::<f32>() / touchable.len() as f32 }
    }
}

/// The network settled in `nctx` contexts at once (e004); every context its own run.
fn settle(n: usize, w: &[f32], wm: &[f32], morph: &[Vec<f32>; N_MORPH], nctx: usize) -> Vec<f32> {
    let mut level = vec![0.5f32; n * nctx];
    let mut next = vec![0.0f32; n * nctx];
    let mut acc = vec![0.0f32; nctx];
    for _ in 0..T {
        for i in 0..n {
            acc.fill(0.0);
            for j in 0..n {
                let wij = w[i * n + j];
                for (a, &l) in acc.iter_mut().zip(&level[j * nctx..(j + 1) * nctx]) {
                    *a += wij * l;
                }
            }
            for m in 0..N_MORPH {
                let wim = wm[i * N_MORPH + m];
                for (a, &l) in acc.iter_mut().zip(&morph[m][..nctx]) {
                    *a += wim * l;
                }
            }
            for (o, &a) in next[i * nctx..(i + 1) * nctx].iter_mut().zip(&acc) {
                *o = sigmoid(3.0 * a - 1.0);
            }
        }
        std::mem::swap(&mut level, &mut next);
    }
    level
}

/// Development: the run without position gives the policy, the density and the side; then the
/// cells of the grid of that side are settled together, and only the largest part is built.
pub fn develop_genes(genes: &[Gene], laws: &Laws) -> Body {
    let n = genes.len();
    let mut w = vec![0.0f32; n * n];
    let mut wm = vec![0.0f32; n * N_MORPH];
    for i in 0..n {
        for j in 0..n {
            w[i * n + j] = bind(&genes[j].product, &genes[i].tag);
        }
        for m in 0..N_MORPH {
            wm[i * N_MORPH + m] = bind_morphogen(&laws.morphogen[m], &genes[i].tag);
        }
    }
    let rows: Vec<&[f32; K]> = genes.iter().map(|g| &laws.table[pattern_index(&g.product)]).collect();
    let no_pos: [Vec<f32>; N_MORPH] = std::array::from_fn(|_| vec![0.0f32]);
    let free = settle(n, &w, &wm, &no_pos, 1);
    let read = |column: &[f32]| -> f32 {
        let mut d = 0.0f32;
        for (i, g) in genes.iter().enumerate() {
            d += column[pattern_index(&g.product)] * free[i];
        }
        d
    };
    let side = ((SIDE as f32 * SIDE_RANGE.powf(sigmoid(read(&laws.side)) * 2.0 - 1.0)).round() as usize).clamp(SIDE_MIN, SIDE_MAX);
    let ncell = side * side;
    let level = settle(n, &w, &wm, &laws.morph_level[side], ncell);
    let mut cells = [0u8; CELLS];
    for (c, cell) in cells.iter_mut().enumerate().take(ncell) {
        let mut score = [0.0f32; N_KINDS];
        for (i, row) in rows.iter().enumerate() {
            let lv = level[i * ncell + c];
            for k in 0..N_KINDS {
                score[k] += row[k] * lv;
            }
        }
        let mut best = 0;
        for k in 1..N_KINDS {
            if score[k] > score[best] {
                best = k;
            }
        }
        *cell = best as u8;
    }
    let cut = keep_largest(&mut cells, side);
    let mut policy = [0.0f32; N_POLICY];
    for (i, row) in rows.iter().enumerate() {
        for k in 0..N_POLICY {
            policy[k] += row[N_KINDS + k] * free[i];
        }
    }
    for p in policy.iter_mut() {
        *p = sigmoid(*p) * 2.0 - 1.0;
    }
    let density = DENSITY_RANGE.powf(sigmoid(read(&laws.density)) * 2.0 - 1.0);
    let mut body = Body::new(cells, side, policy, n as u16, density);
    body.cut = cut;
    body
}

pub struct Agent {
    pub id: u64,
    pub lineage: u32, // 0: none; inherited from the mother, corrected at each detection
    pub x: usize, // the sub-cell under the north-west corner of the grid
    pub y: usize,
    pub energy: f64,
    pub age: u32,
    pub plant: f32, // lifetime intake from plants
    pub scavenged: f32, // from the dead lying on the ground
    pub killed: f32, // from blocks it broke off other bodies
    pub fat: f64,
    pub born_size: u16,
    pub born_mass: f32,
    pub born_kinds: [u16; N_KINDS],
    pub born_bite: u8, // the tooth it was born with: the force behind a hard tip on any side
    pub born_at: (usize, usize),
    pub born_hab: u8, // the habitat of the cell it was born on
    pub turns: u32,
    pub phase: f32,
    pub path: u32, // sub-cells it moved by its own actions
    pub alive: bool,
    pub short: bool, // this step's upkeep or moves were not paid in full
    pub worn: u16,
    pub worn_out: bool,
    pub genome: Vec<u8>,
    pub keys: Vec<u16>, // sorted gene keys, for distances
    pub gene_ids: Vec<u16>, // gene keys in genome order: the body is a function of this list
    pub body: Body,
    pub facing: u8,
    // The body in the world frame: its cells rotated by the facing, the tips per world side, the
    // cells it holds (grid indices, `n_filled` of them) and their bounding box.
    pub wcells: [u8; CELLS],
    pub tips: [[Tip; SIDE_MAX]; 4],
    pub filled: [u8; CELLS],
    pub n_filled: u16,
    pub bbox: [u8; 4],
}

impl Agent {
    #[allow(clippy::too_many_arguments)]
    pub fn new(id: u64, genome: Vec<u8>, keys: Vec<u16>, gene_ids: Vec<u16>, body: Body, facing: u8, energy: f64, lineage: u32) -> Agent {
        let mut a = Agent {
            id, lineage, x: 0, y: 0, energy, age: 0, plant: 0.0, scavenged: 0.0, killed: 0.0, fat: 0.0, born_size: 0, born_mass: 0.0, born_kinds: [0; N_KINDS], born_bite: 0, born_at: (0, 0), born_hab: 0,
            turns: 0, phase: 0.0, path: 0, alive: false, short: false, worn: 0, worn_out: false, genome, keys, gene_ids, body: Body::empty(), facing,
            wcells: [0; CELLS], tips: [[Tip::default(); SIDE_MAX]; 4], filled: [0; CELLS], n_filled: 0, bbox: [0; 4],
        };
        a.set_body(body);
        a
    }
    /// The body it is born with.
    pub fn set_body(&mut self, body: Body) {
        self.born_size = body.size;
        self.born_mass = body.mass;
        self.born_kinds = body.kinds;
        self.born_bite = body.bite_any();
        self.alive = body.size > 0;
        self.body = body;
        self.reframe();
    }
    pub fn distance(&self, other: &Agent) -> usize {
        gene_distance(&self.keys, &other.keys)
    }
    pub fn meat(&self) -> f32 {
        self.killed + self.scavenged
    }
    /// Recompute the world frame from the body and the facing.
    pub fn reframe(&mut self) {
        let s = self.body.s();
        self.wcells = rotate(&self.body.cells, self.facing as usize, s);
        self.tips = tips_of(&self.wcells, s);
        let (list, n, bb) = filled(&self.wcells, s);
        self.filled = list;
        self.n_filled = n;
        self.bbox = bb;
    }
    pub fn cells_held(&self) -> impl Iterator<Item = usize> + '_ {
        self.filled[..self.n_filled as usize].iter().map(|&p| p as usize)
    }
    /// How far the body stands from where it was born, in world cells.
    pub fn travel(&self, g: Grid) -> f32 {
        let (bx, by) = self.born_at;
        let dx = self.x.abs_diff(bx).min(g.sw - self.x.abs_diff(bx));
        let dy = self.y.abs_diff(by).min(g.sh - self.y.abs_diff(by));
        ((dx * dx + dy * dy) as f32).sqrt() / SUB as f32
    }
    /// The sub-cell under grid cell `pos`, moved k sub-cells in direction d.
    pub fn sub_at(&self, g: Grid, pos: usize, d: usize, k: usize) -> (usize, usize) {
        let s = self.body.s();
        g.sstep((self.x + pos % s) % g.sw, (self.y + pos / s) % g.sh, d, k)
    }
    /// The world cells under the body's bounding box, moved k sub-cells in direction d.
    pub fn under(&self, g: Grid, d: usize, k: usize) -> CellsUnder {
        let mut out = CellsUnder::default();
        if self.n_filled == 0 {
            return out;
        }
        let [r0, r1, c0, c1] = self.bbox;
        let (sx, sy) = self.sub_at(g, r0 as usize * self.body.s() + c0 as usize, d, k);
        let nx = (sx % SUB + (c1 - c0) as usize) / SUB + 1;
        let ny = (sy % SUB + (r1 - r0) as usize) / SUB + 1;
        for j in 0..ny {
            for i in 0..nx {
                out.add(g.idx((sx / SUB + i) % g.w, (sy / SUB + j) % g.h));
            }
        }
        out
    }
    /// The world cell under the middle of the body.
    pub fn here(&self, g: Grid) -> usize {
        let [r0, r1, c0, c1] = self.bbox;
        let (sx, sy) = self.sub_at(g, (r0 + r1) as usize / 2 * self.body.s() + (c0 + c1) as usize / 2, NORTH, 0);
        g.wcell(sx, sy)
    }
    /// Whether every cell of the body, moved k sub-cells in direction d, lands on a free sub-cell
    /// or on one of its own.
    pub fn fits(&self, g: Grid, occ: &[u32], me: u32, d: usize, k: usize) -> bool {
        self.cells_held().all(|p| {
            let (sx, sy) = self.sub_at(g, p, d, k);
            let o = occ[g.sidx(sx, sy)];
            o == FREE || o == me
        })
    }
}

/// The world: w x h cells, and sw x sh sub-cells (SUB per cell) of occupancy.
#[derive(Clone, Copy)]
pub struct Grid {
    pub w: usize,
    pub h: usize,
    pub sw: usize,
    pub sh: usize,
}

impl Grid {
    pub fn new(w: usize, h: usize) -> Self {
        Grid { w, h, sw: w * SUB, sh: h * SUB }
    }
    pub fn idx(&self, x: usize, y: usize) -> usize {
        y * self.w + x
    }
    pub fn cells(&self) -> usize {
        self.w * self.h
    }
    pub fn sidx(&self, sx: usize, sy: usize) -> usize {
        sy * self.sw + sx
    }
    pub fn wcell(&self, sx: usize, sy: usize) -> usize {
        self.idx(sx / SUB, sy / SUB)
    }
    pub fn sstep(&self, sx: usize, sy: usize, d: usize, k: usize) -> (usize, usize) {
        match d {
            NORTH => (sx, (sy + self.sh - k % self.sh) % self.sh),
            SOUTH => (sx, (sy + k) % self.sh),
            EAST => ((sx + k) % self.sw, sy),
            _ => ((sx + self.sw - k % self.sw) % self.sw, sy),
        }
    }
}

pub const FREE: u32 = u32::MAX;
/// A sub-cell of the sea. No body stands there: in this first step of stage C the bodies live on
/// land (the water's two layers are a trade-off still to build).
pub const WALL: u32 = u32::MAX - 1;

/// Occupancy: the body holding each sub-cell (FREE, WALL, or its index), and per world cell the
/// sub-cells bodies hold (the crowd there, what a body sees).
pub struct Occ {
    pub sub: Vec<u32>,
    pub crowd: Vec<u16>,
}

impl Occ {
    pub fn new(g: Grid, sea: &[bool]) -> Self {
        let mut sub = vec![FREE; g.sw * g.sh];
        for sy in 0..g.sh {
            for sx in 0..g.sw {
                if sea[g.wcell(sx, sy)] {
                    sub[g.sidx(sx, sy)] = WALL;
                }
            }
        }
        Occ { sub, crowd: vec![0; g.cells()] }
    }
    pub fn claim(&mut self, g: Grid, a: &Agent, v: u32) {
        for p in a.cells_held() {
            let (sx, sy) = a.sub_at(g, p, NORTH, 0);
            self.sub[g.sidx(sx, sy)] = v;
            self.crowd[g.wcell(sx, sy)] += 1;
        }
    }
    pub fn release(&mut self, g: Grid, a: &Agent) {
        for p in a.cells_held() {
            let (sx, sy) = a.sub_at(g, p, NORTH, 0);
            self.sub[g.sidx(sx, sy)] = FREE;
            self.crowd[g.wcell(sx, sy)] -= 1;
        }
    }
    fn release_one(&mut self, g: Grid, a: &Agent, pos: usize) {
        let (sx, sy) = a.sub_at(g, pos, NORTH, 0);
        self.sub[g.sidx(sx, sy)] = FREE;
        self.crowd[g.wcell(sx, sy)] -= 1;
    }
    pub fn relabel(&mut self, g: Grid, a: &Agent, v: u32) {
        for p in a.cells_held() {
            let (sx, sy) = a.sub_at(g, p, NORTH, 0);
            self.sub[g.sidx(sx, sy)] = v;
        }
    }
}

/// Counters of the contact physics and the dead, summed over a log interval.
#[derive(Default)]
pub struct Counters {
    pub contacts: u64,
    pub cells_broken: u64,
    pub kills: u64, // bodies broken to their last block
    pub kill_gain: f64, // what guts gained from the blocks they broke
    pub dead: f64, // matter laid on the ground by the dead
    pub cut_break: u64,
    pub cut_wear: u64,
    pub cut_bodies: u64,
    pub born_cut: u64,
    pub not_built: u64,
}

/// Dead matter `e`, in a body's units at scale `s`, lies on world cell `c` as the world's matter.
pub fn lay(carrion: &mut [f64], c: usize, e: f64, s: f64, cc: &mut Counters) {
    if e <= 0.0 {
        return;
    }
    carrion[c] += e * s;
    cc.dead += e * s;
}

/// A dead body lies where it is: each block is the matter it was made of plus its share of the
/// body's energy and fat, on the world cell under it (a body with no block, under its anchor).
/// Called after its sub-cells are released.
pub fn lay_body(a: &Agent, g: Grid, carrion: &mut [f64], s: f64, cc: &mut Counters) {
    let energy = a.energy.max(0.0) + a.fat;
    if a.n_filled == 0 {
        lay(carrion, g.wcell(a.x, a.y), energy, s, cc);
        return;
    }
    let share = energy / a.n_filled as f64;
    for p in a.cells_held() {
        let (sx, sy) = a.sub_at(g, p, NORTH, 0);
        lay(carrion, g.wcell(sx, sy), a.body.block_matter(a.wcells[p]) + share, s, cc);
    }
}

/// Body i moves one sub-cell in direction d, and every cell of it whose next sub-cell another body
/// holds meets that body's cell face to face (e010): the softer face breaks if the muscle of the
/// pressing line exceeds its hardness. A broken block goes, with its share of energy and fat, to a
/// breaker with a gut, else to the ground. A body the breaks cut in parts keeps its largest part.
/// Returns, per body pressed, the force against it. The sea presses nothing.
pub fn push(agents: &mut [Agent], i: usize, d: usize, g: Grid, occ: &mut Occ, carrion: &mut [f64], s: f64, c: &mut Counters) -> Vec<(usize, u8)> {
    let opp = opposite(d);
    let mut pressed: Vec<(usize, u8)> = Vec::new();
    let mut breaks: Vec<(usize, u8, usize)> = Vec::new(); // (victim, world-frame cell, eater)
    for p in agents[i].cells_held() {
        let (sx, sy) = agents[i].sub_at(g, p, d, 1);
        let j = occ.sub[g.sidx(sx, sy)];
        if j == FREE || j == WALL || j as usize == i {
            continue;
        }
        let j = j as usize;
        let b = &agents[j];
        let (r, col) = ((sy + g.sh - b.y) % g.sh, (sx + g.sw - b.x) % g.sw);
        debug_assert!(r < b.body.s() && col < b.body.s());
        let q = r * b.body.s() + col;
        let ha = face_hardness(&agents[i].wcells, p, opp, agents[i].body.s()) as f32 * agents[i].body.density;
        let hb = face_hardness(&b.wcells, q, d, b.body.s()) as f32 * b.body.density;
        let force = agents[i].tips[d][line_of(p, d, agents[i].body.s())].force;
        match pressed.iter_mut().find(|e| e.0 == j) {
            Some(e) => e.1 = e.1.saturating_add(force),
            None => pressed.push((j, force)),
        }
        if hb < ha && force as f32 > hb {
            breaks.push((j, q as u8, i));
        } else if ha < hb && force as f32 > ha {
            breaks.push((i, p as u8, j));
        }
    }
    c.contacts += pressed.len() as u64;
    let mut victims: Vec<usize> = Vec::new();
    for &(v, _, _) in &breaks {
        if !victims.contains(&v) {
            victims.push(v);
        }
    }
    for (victim, pos, eater) in breaks {
        let v = &mut agents[victim];
        if v.wcells[pos as usize] == 0 {
            continue;
        }
        occ.release_one(g, v, pos as usize);
        let (sx, sy) = v.sub_at(g, pos as usize, NORTH, 0);
        let under = g.wcell(sx, sy);
        let bpos = to_body(pos as usize, v.facing as usize, v.body.s());
        let share = v.energy.max(0.0) / v.body.size as f64;
        v.energy -= share;
        let fat = v.fat / v.body.size as f64;
        v.fat -= fat;
        let matter = v.body.block_matter(v.body.cells[bpos]);
        v.body.cells[bpos] = 0;
        v.body.refresh();
        v.reframe();
        c.cells_broken += 1;
        if v.body.size == 0 && v.alive {
            v.alive = false;
            c.kills += 1;
        }
        let taken = share + fat + matter;
        let e = &mut agents[eater];
        if e.body.kinds[DIGESTIVE] > 0 {
            e.energy += taken;
            e.killed += taken as f32;
            c.kill_gain += taken;
        } else {
            lay(carrion, under, taken, s, c);
        }
    }
    for v in victims {
        let lost = cut_loose(&mut agents[v], g, occ, carrion, s, c);
        c.cut_break += lost as u64;
    }
    pressed
}

/// The turns a body of mass `mass` gets per world step (e052, e055).
pub fn pace(mass: f32) -> f32 {
    if mass <= CLOCK_MASS { 1.0 } else { (CLOCK_MASS / mass).powf(CLOCK) }
}

/// The chance that a block of a body of age `age` (in turns) fails this turn (e044).
pub fn wear_chance(age: u32) -> f64 {
    let s = WEAR / WEAR_SPANS;
    let h0 = std::f64::consts::LN_2 * std::f64::consts::LN_2 / (s * (WEAR_SPANS.exp2() - 1.0));
    (h0 * (age as f64 / s).exp2()).min(1.0)
}

/// Each block of body `a` fails with chance `h` and lies on the ground with its share of the
/// body's energy and fat. A body with no block left is dead of wear. Returns the blocks lost.
pub fn wear_blocks(a: &mut Agent, h: f64, rng: &mut Rng, g: Grid, occ: &mut Occ, carrion: &mut [f64], s: f64, c: &mut Counters) -> u16 {
    let failed: Vec<usize> = a.cells_held().filter(|_| rng.f64() < h).collect();
    for &pos in &failed {
        occ.release_one(g, a, pos);
        let (sx, sy) = a.sub_at(g, pos, NORTH, 0);
        let bpos = to_body(pos, a.facing as usize, a.body.s());
        let share = a.energy.max(0.0) / a.body.size as f64;
        a.energy -= share;
        let fat = a.fat / a.body.size as f64;
        a.fat -= fat;
        let matter = a.body.block_matter(a.body.cells[bpos]);
        a.body.cells[bpos] = 0;
        a.body.refresh();
        a.reframe();
        lay(carrion, g.wcell(sx, sy), share + fat + matter, s, c);
    }
    a.worn += failed.len() as u16;
    if !failed.is_empty() {
        let lost = cut_loose(a, g, occ, carrion, s, c);
        c.cut_wear += lost as u64;
    }
    if a.body.size == 0 {
        a.alive = false;
        a.worn_out = true;
    }
    failed.len() as u16
}

/// A body in parts keeps the largest; every block of the others lies on the ground with its share
/// of the body's energy and fat. Returns the blocks lost.
fn cut_loose(a: &mut Agent, g: Grid, occ: &mut Occ, carrion: &mut [f64], s: f64, c: &mut Counters) -> u16 {
    let side = a.body.s();
    let (label, parts) = parts_of(&a.body.cells, side);
    if parts < 2 {
        return 0;
    }
    let keep = kept_part(&a.body.cells, side, &label, parts);
    let size = a.body.size as f64;
    let (share, fat) = (a.energy.max(0.0) / size, a.fat / size);
    let mut lost = 0u16;
    for bpos in 0..side * side {
        if label[bpos] == 0 || label[bpos] == keep {
            continue;
        }
        let pos = to_world(bpos, a.facing as usize, side);
        occ.release_one(g, a, pos);
        let (sx, sy) = a.sub_at(g, pos, NORTH, 0);
        let matter = a.body.block_matter(a.body.cells[bpos]);
        lay(carrion, g.wcell(sx, sy), share + fat + matter, s, c);
        a.body.cells[bpos] = 0;
        lost += 1;
    }
    a.energy -= share * lost as f64;
    a.fat -= fat * lost as f64;
    a.body.refresh();
    a.reframe();
    c.cut_bodies += 1;
    lost
}

/// Whether the motor carries a body one sub-cell, of a step or a turn: with chance speed (e048).
pub fn stroke(speed: f32, rng: &mut Rng) -> bool {
    rng.f32() < speed
}

/// The best of the four outputs.
pub fn act(policy: &[f32; N_POLICY], input: &[f32; N_IN]) -> usize {
    let mut best = 0;
    let mut best_v = f32::NEG_INFINITY;
    for o in 0..N_OUT {
        let mut v = policy[N_IN * N_OUT + o];
        for i in 0..N_IN {
            v += policy[o * N_IN + i] * input[i];
        }
        if v > best_v {
            best_v = v;
            best = o;
        }
    }
    best
}

/// What a body sees k cells away in direction d (e023): the world cells it would newly lie over
/// after moving k cells that way (those under its box moved k * SUB sub-cells, less those under it
/// now and one cell before), the food on them and the crowd there in world cells of bodies.
pub fn look<F: Fn(usize) -> f64>(a: &Agent, g: Grid, d: usize, k: usize, food: &F, crowd: &[u16]) -> (f32, f32) {
    let now = a.under(g, NORTH, 0);
    let before = if k > 1 { a.under(g, d, (k - 1) * SUB) } else { now };
    let (mut f, mut others) = (0.0f32, 0.0f32);
    for c in a.under(g, d, k * SUB).iter() {
        if now.contains(c) || before.contains(c) {
            continue;
        }
        f += food(c) as f32;
        others += crowd[c] as f32 / SUB_CELLS as f32;
    }
    (f, others)
}

#[cfg(test)]
mod tests {
    use super::*;

    fn agent_with(cells: [u8; CELLS], x: usize, y: usize, facing: usize) -> Agent {
        let mut a = Agent::new(0, Vec::new(), Vec::new(), Vec::new(), Body::new(cells, SIDE, [0.0; N_POLICY], 0, 1.0), facing as u8, 1.0, 0);
        a.x = x;
        a.y = y;
        a
    }

    fn land(g: Grid) -> Occ {
        Occ::new(g, &vec![false; g.cells()])
    }

    fn tooth() -> [u8; CELLS] {
        let mut t = [0u8; CELLS];
        t[2] = HARD as u8;
        t[SIDE + 2] = MUSCLE as u8;
        t[2 * SIDE + 2] = MUSCLE as u8;
        t
    }

    #[test]
    fn a_push_meets_face_to_face() {
        let g = Grid::new(8, 8);
        // The tooth faces east at anchor (0, 8): its tip is at sub-cell (7, 10).
        let hunter = agent_with(tooth(), 0, 8, EAST);
        assert_eq!(hunter.wcells[2 * SIDE + 7], HARD as u8);
        let mut soft = [0u8; CELLS];
        soft[0] = MUSCLE as u8;
        soft[1] = MUSCLE as u8;
        let prey = agent_with(soft, 8, 10, NORTH);
        let mut agents = vec![hunter, prey];
        let mut occ = land(g);
        occ.claim(g, &agents[0], 0);
        occ.claim(g, &agents[1], 1);
        let mut c = Counters::default();
        let mut carrion = vec![0.0; g.cells()];
        let pressed = push(&mut agents, 0, EAST, g, &mut occ, &mut carrion, 1.0, &mut c);
        // Force 2 against a soft face of 1: the block breaks and, the hunter having no gut, lies
        // on world cell (2, 2) with half the prey's energy.
        assert_eq!(pressed, vec![(1, 2)]);
        assert_eq!((c.contacts, c.cells_broken), (1, 1));
        assert_eq!(agents[1].body.size, 1);
        assert!((carrion[g.idx(2, 2)] - (CELL_ENERGY + 0.5) as f64).abs() < 1e-6);
        assert!((agents[1].energy - 0.5).abs() < 1e-6);
        assert!(agents[0].fits(g, &occ.sub, 0, EAST, 1));
        // A hunter with a gut eats what it broke.
        let mut gutted = tooth();
        gutted[3 * SIDE + 2] = DIGESTIVE as u8;
        let mut agents = vec![agent_with(gutted, 0, 8, EAST), agent_with(soft, 8, 10, NORTH)];
        let mut occ = land(g);
        occ.claim(g, &agents[0], 0);
        occ.claim(g, &agents[1], 1);
        let mut carrion = vec![0.0; g.cells()];
        push(&mut agents, 0, EAST, g, &mut occ, &mut carrion, 1.0, &mut c);
        assert!((agents[0].killed as f64 - (CELL_ENERGY + 0.5) as f64).abs() < 1e-6);
        assert_eq!(carrion.iter().sum::<f64>(), 0.0);
    }

    #[test]
    fn the_sea_is_a_wall() {
        // The world's column 2 is sea: a body cannot step or turn into it, and presses nothing.
        let g = Grid::new(8, 8);
        let sea: Vec<bool> = (0..g.cells()).map(|c| c % g.w == 2).collect();
        let mut occ = Occ::new(g, &sea);
        assert_eq!(occ.sub[g.sidx(8, 0)], WALL);
        assert_eq!(occ.sub[g.sidx(7, 0)], FREE);
        let mut agents = vec![agent_with(tooth(), 0, 8, EAST)];
        occ.claim(g, &agents[0], 0);
        assert!(!agents[0].fits(g, &occ.sub, 0, EAST, 1));
        let mut c = Counters::default();
        let mut carrion = vec![0.0; g.cells()];
        assert!(push(&mut agents, 0, EAST, g, &mut occ, &mut carrion, 1.0, &mut c).is_empty());
        assert_eq!((c.contacts, c.cells_broken), (0, 0));
        // A new body cannot be placed on the sea.
        let b = agent_with(tooth(), 8, 0, NORTH);
        assert!(!b.fits(g, &occ.sub, FREE, NORTH, 0));
    }

    #[test]
    fn wear_takes_half_the_blocks_by_the_median_life() {
        let alive: f64 = (1..=WEAR as u32).map(|a| 1.0 - wear_chance(a)).product();
        assert!((alive - 0.5).abs() < 0.005, "{alive}");
        assert!((wear_chance(0) - 1.565e-6).abs() < 1e-8);
        let g = Grid::new(8, 8);
        let mut c = Counters::default();
        let mut carrion = vec![0.0; g.cells()];
        let mut cells = [0u8; CELLS];
        cells[0] = DIGESTIVE as u8;
        cells[1] = MUSCLE as u8;
        cells[SIDE] = HARD as u8;
        let mut a = agent_with(cells, 8, 8, NORTH);
        a.fat = 0.3;
        let mut occ = land(g);
        occ.claim(g, &a, 0);
        let before = a.energy + a.fat + a.body.matter();
        let mut rng = Rng(1);
        assert_eq!(wear_blocks(&mut a, 0.0, &mut rng, g, &mut occ, &mut carrion, 1.0, &mut c), 0);
        assert_eq!(wear_blocks(&mut a, 1.0, &mut rng, g, &mut occ, &mut carrion, 1.0, &mut c), 3);
        assert_eq!((a.body.size, a.alive, a.worn_out), (0, false, true));
        assert!((carrion.iter().sum::<f64>() - before).abs() < 1e-9);
        assert_eq!(occ.crowd.iter().map(|&n| n as u32).sum::<u32>(), 0);
    }

    #[test]
    fn a_break_cuts_a_body_in_two() {
        // A column of five guts at sub-cells (8, 8..12) meets the tooth at (8, 10), its third
        // block. The two halves do not touch, even at a corner: the first in grid order stays,
        // the other two blocks fall with their share of what is left, and nothing is lost.
        let mut cells = [0u8; CELLS];
        cells[1] = MUSCLE as u8; // corners join: this block holds to block 0 and to nothing else
        let (_, parts) = parts_of(&{
            let mut x = cells;
            x[SIDE] = DIGESTIVE as u8;
            x
        }, SIDE);
        assert_eq!(parts, 1);
        let mut column = [0u8; CELLS];
        for r in 0..5 {
            column[r * SIDE] = DIGESTIVE as u8;
        }
        let g = Grid::new(8, 8);
        let mut agents = vec![agent_with(tooth(), 0, 8, EAST), agent_with(column, 8, 8, NORTH)];
        let mut occ = land(g);
        occ.claim(g, &agents[0], 0);
        occ.claim(g, &agents[1], 1);
        let before = agents[1].energy + agents[1].body.matter();
        let mut c = Counters::default();
        let mut carrion = vec![0.0; g.cells()];
        push(&mut agents, 0, EAST, g, &mut occ, &mut carrion, 1.0, &mut c);
        assert_eq!((c.cells_broken, c.cut_break, c.cut_bodies), (1, 2, 1));
        assert_eq!(agents[1].body.size, 2);
        assert_eq!(agents[1].body.cells[0], DIGESTIVE as u8);
        assert!((agents[1].energy - 0.4).abs() < 1e-9);
        let after = agents[1].energy + agents[1].body.matter() + carrion.iter().sum::<f64>();
        assert!((after - before).abs() < 1e-9);
        assert_eq!(occ.crowd.iter().map(|&n| n as u32).sum::<u32>(), 3 + 2);
    }

    #[test]
    fn a_step_takes_a_motor_and_a_block_weighs_by_its_kind() {
        let mut rng = Rng(7);
        assert!(!(0..1000).any(|_| stroke(0.0, &mut rng)));
        let n = (0..10_000).filter(|_| stroke(0.25, &mut rng)).count();
        assert!((2_300..2_700).contains(&n), "{n}");
        let mut cells = [0u8; CELLS];
        cells[0] = DIGESTIVE as u8;
        cells[1] = HARD as u8;
        let b = Body::new(cells, SIDE, [0.0; N_POLICY], 0, 1.0);
        assert_eq!((b.size, b.mass, b.speed()), (2, 3.0, 0.0));
        cells[2] = MUSCLE as u8;
        assert!((Body::new(cells, SIDE, [0.0; N_POLICY], 0, 1.0).speed() - 0.25).abs() < 1e-6);
        assert_eq!(Body::new(cells, SIDE, [0.0; N_POLICY], 0, 2.0).mass, 8.0);
        // The pace: one turn a step up to a mass of 16, half a turn at 64.
        assert_eq!(pace(16.0), 1.0);
        assert!((pace(64.0) - 0.5).abs() < 1e-6);
    }

    #[test]
    fn a_body_is_a_function_of_its_gene_list() {
        let mut rng = Rng(3);
        let laws = Laws::new(&mut rng, 3);
        let genome: Vec<u8> = (0..N).map(|_| rng.below(4) as u8).collect();
        let genes = parse_genes(&genome);
        let (a, b) = (develop_genes(&genes, &laws), develop_genes(&genes, &laws));
        assert_eq!((a.cells, a.side, a.density.to_bits()), (b.cells, b.side, b.density.to_bits()));
        assert!((SIDE_MIN..=SIDE_MAX).contains(&a.s()));
        assert!(parts_of(&a.cells, a.s()).1 <= 1);
    }
}
