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
//!
//! e065 (#79) opens the water. A water cell has a surface layer and a bottom layer: a body lighter
//! than water (density under 1) lives in the surface layer, a denser one on the bottom, and each
//! layer has its own occupancy (`Occ`), so bodies of different layers never meet in the water. Land
//! has one layer, which both share. A body over land and water at once holds, where a sub-cell is
//! water, the layer its density picks. With the water closed the sea is a wall, as in e064.
//!
//! e066 (#80) prices the dry air. A body holds water, its fill (1 full), in its blocks. Each turn
//! a soft block (muscle, sensor, gut) over ground that is not water loses `dry` x the dryness there
//! (1 - the ground's fill, `main.rs`) for each of its faces open to the air (no block of the body beside it); a hard block
//! loses nothing, and neither does a block over water, which gives `drink` instead. What the
//! blocks lose and drink is counted in blocks of water, so the fill moves by it over the block
//! count (`dry_turn`). A body sees the water in its four directions as it sees the food, and reads
//! its own thirst, through weights of their own (`Laws::water`, e040's way). With `dry` 0 none of
//! this is read and the bodies are e065's.
//!
//! e067 (#81) prices the closed body in the water. A body holds breath, a second fill (1 full).
//! Each turn each block over water uses `breath` and each face of a soft block over water with no
//! block of the body beside it gives `breath` back; each block over land gives `inhale`; the net over
//! the block count moves the fill (`breath_turn`). The open faces that dry a body on land feed it in
//! the water, and a hard block breathes through nothing. A body reads its breath through a column of
//! its own (`Laws::breath`). With `breath` 0 none of this is read and the bodies are e066's.
//!
//! e069 (#83) reads three values of a life from the genome instead of writing them as constants: the
//! energy a body breeds at per unit of its mass (`BREED`), the share of its energy a child gets
//! (`SHARE`) and the fat its flesh holds per unit of mass (`STORE`). Each is a column of the law table
//! from its own stream, read from the run without position as the density is, today's constant times
//! `LIFE_RANGE` to a power from -1 to 1 (x0.5 to x2), so a child inherits it and it mutates with the
//! genes. With `Laws::history` off each is today's constant and the bodies are e067's.
//!
//! e070 (#84) moves the senses into the sensor blocks (`sense`). With `senses` on, a body registers
//! only what its sensor blocks register: the food on the world cells under them; the food, the bodies
//! and the water in a direction only through a sensor block with nothing of its body beyond it that
//! way, one cell and one more per such block up to EYES (`Body::sight`, `Body::reach`), and nothing in
//! a direction without one; and its own energy, thirst and breath only if it has a sensor block. The
//! inputs and their weights are e069's. Off, every direction sees as far as `Body::range`, the food is
//! read under the whole body and every body reads its fills: the same readings configured as e069's.

pub const CELL_ENERGY: f32 = 0.02; // the matter of a block of mass 1: paid to build it, gained when it is eaten
pub const INIT_ENERGY: f32 = 5.0;
pub const UPKEEP: f32 = 0.002; // per block per step
pub const UPKEEP_BODY: f32 = 0.032; // per body per step, besides its blocks (e016: the world's compute is per body)
pub const MOVE_COST: f32 = 0.001; // per unit of mass moved per sub-cell (work = force x distance)
pub const BITE: f32 = 0.02; // what a gut block takes a step
pub const STORE: f32 = 5.0; // fat the flesh holds per unit of mass (e030); e069: the centre of the genome's range
pub const BREED: f32 = 0.1; // energy to breed per unit of mass, over 2; e069: the centre of the genome's range
pub const SHARE: f32 = 0.5; // the share of its energy a parent gives a child; e069: the centre of the genome's range
pub const LIFE_RANGE: f32 = 2.0; // e069: each value of a life is its centre times LIFE_RANGE^(2 sigmoid(s) - 1)
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
// e066: the water seen ahead, behind, left and right, and the thirst (1 - fill), read by weights of
// their own so that without dry air the outputs are e065's (e040's way).
pub const N_IN_WATER: usize = 5;
pub const N_WATER_POLICY: usize = N_IN_WATER * N_OUT;

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
    water: Vec<[f32; N_WATER_POLICY]>,
    breath: Vec<[f32; N_OUT]>,
    breed: Vec<f32>, // e069: the energy to breed per unit of mass
    share: Vec<f32>, // e069: the share of its energy a child gets
    store: Vec<f32>, // e069: the fat the flesh holds per unit of mass
    pub history: bool, // e069: read the three from the genome; off, each is today's constant
    morph_level: Vec<[Vec<f32>; N_MORPH]>,
}

impl Laws {
    pub fn new(rng: &mut Rng, seed: u64) -> Self {
        let column = |a: u64, b: u64| {
            let mut r = Rng(seed.wrapping_mul(a).wrapping_add(b) | 1);
            (0..256).map(|_| r.f32() * 2.0 - 1.0).collect::<Vec<f32>>()
        };
        let breed = column(0xBF58476D1CE4E5B9, 0x94D049BB133111EB);
        let share = column(0x2127599BF4325C37, 0x880355F21E6D1965);
        let store = column(0xFF51AFD7ED558CCD, 0xC4CEB9FE1A85EC53);
        let mut rng2 = Rng(seed.wrapping_mul(0x9E3779B97F4A7C15).wrapping_add(0x5851F42D4C957F2D) | 1);
        let density = (0..256).map(|_| rng2.f32() * 2.0 - 1.0).collect();
        let mut rng4 = Rng(seed.wrapping_mul(0xA0761D6478BD642F).wrapping_add(0xE7037ED1A0B428DB) | 1);
        let side = (0..256).map(|_| rng4.f32() * 2.0 - 1.0).collect();
        let mut rng5 = Rng(seed.wrapping_mul(0xD1B54A32D192ED03).wrapping_add(0x8CB92BA72F3D8DD7) | 1);
        let water = (0..256).map(|_| std::array::from_fn(|_| rng5.f32() * 2.0 - 1.0)).collect();
        let mut rng6 = Rng(seed.wrapping_mul(0x9FB21C651E98DF25).wrapping_add(0xC2B2AE3D27D4EB4F) | 1);
        let breath = (0..256).map(|_| std::array::from_fn(|_| rng6.f32() * 2.0 - 1.0)).collect();
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
        Laws { morphogen, table, density, side, water, breath, breed, share, store, history: false, morph_level }
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
    pub water_policy: [f32; N_WATER_POLICY], // e066: what the four outputs make of the water seen and the thirst
    pub open_soft: u16, // e066: faces of soft blocks open to the air
    pub breath_policy: [f32; N_OUT], // e067: what the four outputs make of the breath short of full
    pub breed: f32, // e069: the energy to breed per unit of mass, over 2
    pub share: f32, // e069: the share of its energy it gives a child
    pub store: f32, // e069: the fat its flesh holds per unit of mass
    pub sight: [u8; 4], // e070: sensor blocks looking out of the body to the front, back, left and right
}

impl Body {
    pub fn new(cells: [u8; CELLS], side: usize, policy: [f32; N_POLICY], n_genes: u16, density: f32) -> Self {
        let mut b = Body { cells, side: side as u8, size: 0, mass: 0.0, density, kinds: [0; N_KINDS], tips: [[Tip::default(); SIDE_MAX]; 4], extent: [0; 2], policy, n_genes, cut: 0, water_policy: [0.0; N_WATER_POLICY], open_soft: 0, breath_policy: [0.0; N_OUT], breed: BREED, share: SHARE, store: STORE, sight: [0; 4] };
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
        self.open_soft = open_faces(&self.cells, self.s()).iter().map(|&f| f as u16).sum();
        self.sight = sight_of(&self.cells, self.s());
    }
    /// Muscle over mass.
    pub fn speed(&self) -> f32 {
        if self.mass <= 0.0 { 0.0 } else { self.kinds[MUSCLE] as f32 / self.mass }
    }
    /// The eye's range: one cell, and one more per sensor block up to EYES.
    pub fn range(&self) -> usize {
        1 + (self.kinds[SENSOR] as usize).min(EYES)
    }
    /// The eye's range to one side of the body (e070; 0 front, 1 back, 2 left, 3 right): one cell and
    /// one more per sensor block looking out that way, up to EYES more; none without one.
    pub fn reach(&self, j: usize) -> usize {
        if self.sight[j] == 0 { 0 } else { 1 + (self.sight[j] as usize).min(EYES) }
    }
    pub fn threshold(&self) -> f32 {
        2.0 + self.breed * self.mass
    }
    /// The layer of the water it lives in (e065): the surface if it is lighter than water.
    pub fn layer(&self) -> usize {
        if self.density < 1.0 { SURFACE } else { BOTTOM }
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
    // The reading of water (e066): read like the policy, from the run without position.
    for (i, g) in genes.iter().enumerate() {
        let row = &laws.water[pattern_index(&g.product)];
        for k in 0..N_WATER_POLICY {
            body.water_policy[k] += row[k] * free[i];
        }
    }
    for v in body.water_policy.iter_mut() {
        *v = sigmoid(*v) * 2.0 - 1.0;
    }
    // The reading of breath (e067), the same way from its own column.
    for (i, g) in genes.iter().enumerate() {
        let row = &laws.breath[pattern_index(&g.product)];
        for k in 0..N_OUT {
            body.breath_policy[k] += row[k] * free[i];
        }
    }
    for v in body.breath_policy.iter_mut() {
        *v = sigmoid(*v) * 2.0 - 1.0;
    }
    // The values of a life (e069), each from its own column as the density is.
    if laws.history {
        let life = |column: &[f32], centre: f32| centre * LIFE_RANGE.powf(sigmoid(read(column)) * 2.0 - 1.0);
        body.breed = life(&laws.breed, BREED);
        body.share = life(&laws.share, SHARE);
        body.store = life(&laws.store, STORE);
    }
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
    pub algae: f32, // e065: of `plant`, the algae it took at the surface
    pub detritus: f32, // e065: of `plant`, the algae's dead it took on the bottom
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
    pub open: [u8; CELLS], // e066: the faces of each soft block open to the air (e067: or the water), in the world frame
    pub water: f32, // e066: the fill, 1 full, 0 dry (a state, not matter)
    pub drank: u32, // e066: turns with a block in water
    pub breath: f32, // e067: the breath, 1 full, 0 suffocated (a state, not matter)
    pub inhaled: u32, // e067: turns with a block over land
    pub kids: u32, // e069: children it placed
}

impl Agent {
    #[allow(clippy::too_many_arguments)]
    pub fn new(id: u64, genome: Vec<u8>, keys: Vec<u16>, gene_ids: Vec<u16>, body: Body, facing: u8, energy: f64, lineage: u32) -> Agent {
        let mut a = Agent {
            id, lineage, x: 0, y: 0, energy, age: 0, plant: 0.0, scavenged: 0.0, killed: 0.0, algae: 0.0, detritus: 0.0, fat: 0.0, born_size: 0, born_mass: 0.0, born_kinds: [0; N_KINDS], born_bite: 0, born_at: (0, 0), born_hab: 0,
            turns: 0, phase: 0.0, path: 0, alive: false, short: false, worn: 0, worn_out: false, genome, keys, gene_ids, body: Body::empty(), facing,
            wcells: [0; CELLS], tips: [[Tip::default(); SIDE_MAX]; 4], filled: [0; CELLS], n_filled: 0, bbox: [0; 4], open: [0; CELLS], water: 1.0, drank: 0, breath: 1.0, inhaled: 0, kids: 0,
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
        self.open = open_faces(&self.wcells, s);
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
    /// The world cells under its sensor blocks (e070): what they touch.
    pub fn touched(&self, g: Grid) -> CellsUnder {
        let mut out = CellsUnder::default();
        for p in self.cells_held() {
            if self.wcells[p] == SENSOR as u8 {
                let (sx, sy) = self.sub_at(g, p, NORTH, 0);
                out.add(g.wcell(sx, sy));
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
    /// or on one of its own, in its layer.
    pub fn fits(&self, g: Grid, occ: &Occ, me: u32, d: usize, k: usize) -> bool {
        let layer = self.body.layer();
        self.cells_held().all(|p| {
            let (sx, sy) = self.sub_at(g, p, d, k);
            let o = occ.at(g, sx, sy, layer);
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
/// A sub-cell of the sea while the water is closed (e063, e064): no body stands there.
pub const WALL: u32 = u32::MAX - 1;

/// The two layers of a water cell (e065): a body lighter than water lives at the surface, a denser
/// one on the bottom. Land has one layer, held in both.
pub const SURFACE: usize = 0;
pub const BOTTOM: usize = 1;

/// Occupancy, per layer: the body holding each sub-cell (FREE, WALL, or its index) at
/// `2 * sidx + layer`, and per world cell the sub-cells bodies hold (the crowd there, what a body
/// sees) at `2 * cell + layer`. A land sub-cell holds its body in both layers.
pub struct Occ {
    pub sub: Vec<u32>,
    pub crowd: Vec<u16>,
    wet: Vec<bool>, // per world cell: water, where the layers are apart
}

impl Occ {
    /// `open`: bodies may live in the water (e065); else the sea is a wall.
    pub fn new(g: Grid, sea: &[bool], open: bool) -> Self {
        let mut sub = vec![FREE; 2 * g.sw * g.sh];
        if !open {
            for sy in 0..g.sh {
                for sx in 0..g.sw {
                    if sea[g.wcell(sx, sy)] {
                        sub[2 * g.sidx(sx, sy)] = WALL;
                        sub[2 * g.sidx(sx, sy) + 1] = WALL;
                    }
                }
            }
        }
        let wet = if open { sea.to_vec() } else { vec![false; g.cells()] };
        Occ { sub, crowd: vec![0; 2 * g.cells()], wet }
    }
    /// The body in sub-cell (sx, sy) as a body of `layer` meets it.
    pub fn at(&self, g: Grid, sx: usize, sy: usize, layer: usize) -> u32 {
        self.sub[2 * g.sidx(sx, sy) + layer]
    }
    /// The layers a body of `layer` holds on world cell c.
    fn layers(&self, c: usize, layer: usize) -> std::ops::Range<usize> {
        if self.wet[c] { layer..layer + 1 } else { 0..2 }
    }
    /// 0 on land, 1 at the surface, 2 on the bottom: the medium under the middle of the body.
    pub fn medium(&self, g: Grid, a: &Agent) -> usize {
        if self.wet[a.here(g)] { 1 + a.body.layer() } else { 0 }
    }
    fn put(&mut self, g: Grid, a: &Agent, pos: usize, v: u32) {
        let (sx, sy) = a.sub_at(g, pos, NORTH, 0);
        let (i, c) = (2 * g.sidx(sx, sy), g.wcell(sx, sy));
        for l in self.layers(c, a.body.layer()) {
            self.sub[i + l] = v;
            if v == FREE {
                self.crowd[2 * c + l] -= 1;
            } else {
                self.crowd[2 * c + l] += 1;
            }
        }
    }
    pub fn claim(&mut self, g: Grid, a: &Agent, v: u32) {
        for p in a.cells_held() {
            self.put(g, a, p, v);
        }
    }
    pub fn release(&mut self, g: Grid, a: &Agent) {
        for p in a.cells_held() {
            self.put(g, a, p, FREE);
        }
    }
    fn release_one(&mut self, g: Grid, a: &Agent, pos: usize) {
        self.put(g, a, pos, FREE);
    }
    pub fn relabel(&mut self, g: Grid, a: &Agent, v: u32) {
        for p in a.cells_held() {
            let (sx, sy) = a.sub_at(g, p, NORTH, 0);
            let (i, c) = (2 * g.sidx(sx, sy), g.wcell(sx, sy));
            for l in self.layers(c, a.body.layer()) {
                self.sub[i + l] = v;
            }
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
    pub kill_by: [f64; 3], // e065: the same, by the eater's medium (`Occ::medium`)
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
    let layer = agents[i].body.layer();
    for p in agents[i].cells_held() {
        let (sx, sy) = agents[i].sub_at(g, p, d, 1);
        let j = occ.at(g, sx, sy, layer);
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
        let m = occ.medium(g, &agents[eater]);
        let e = &mut agents[eater];
        if e.body.kinds[DIGESTIVE] > 0 {
            e.energy += taken;
            e.killed += taken as f32;
            c.kill_gain += taken;
            c.kill_by[m] += taken;
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

/// The best of the four outputs. `winput` (e066) is the water seen and the thirst, read through
/// `wpolicy`; None without dry air, and the outputs are e065's. `binput` (e067) is the breath short
/// of full, read through `bpolicy`; None without breath, and the outputs are e066's.
pub fn act(policy: &[f32; N_POLICY], wpolicy: &[f32; N_WATER_POLICY], bpolicy: &[f32; N_OUT], input: &[f32; N_IN], winput: Option<&[f32; N_IN_WATER]>, binput: Option<f32>) -> usize {
    let mut best = 0;
    let mut best_v = f32::NEG_INFINITY;
    for o in 0..N_OUT {
        let mut v = policy[N_IN * N_OUT + o];
        for i in 0..N_IN {
            v += policy[o * N_IN + i] * input[i];
        }
        if let Some(wi) = winput {
            for i in 0..N_IN_WATER {
                v += wpolicy[o * N_IN_WATER + i] * wi[i];
            }
        }
        if let Some(b) = binput {
            v += bpolicy[o] * b;
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
/// now and one cell before), the food on them, the crowd there in world cells of bodies, and the
/// water (e066) as `water` counts it.
pub fn look<F: Fn(usize) -> f64, W: Fn(usize) -> f64>(a: &Agent, g: Grid, d: usize, k: usize, food: &F, water: &W, crowd: &[u16]) -> (f32, f32, f32) {
    let now = a.under(g, NORTH, 0);
    let before = if k > 1 { a.under(g, d, (k - 1) * SUB) } else { now };
    let layer = a.body.layer();
    let (mut f, mut others, mut wt) = (0.0f32, 0.0f32, 0.0f32);
    for c in a.under(g, d, k * SUB).iter() {
        if now.contains(c) || before.contains(c) {
            continue;
        }
        f += food(c) as f32;
        others += crowd[2 * c + layer] as f32 / SUB_CELLS as f32;
        wt += water(c) as f32;
    }
    (f, others, wt)
}

/// What a body registers when it decides: the inputs, the same with the eye cut to one cell (the
/// knockout of `sense_used`), the water seen and the thirst (e066) with their knockout, and the breath
/// short of full (e067).
pub struct Readings {
    pub input: [f32; N_IN],
    pub blind: [f32; N_IN],
    pub water: [f32; N_IN_WATER],
    pub water_blind: [f32; N_IN_WATER],
    pub breath: f32,
}

/// The readings (e023, e066, e067): the food under the body; the food, the bodies and the water
/// ahead, behind, left and right as far as the eye's range, what lies j cells away at 1/j; its energy
/// over its threshold, its thirst and its breath. With `senses` on (e070) the sensor blocks register
/// them: the food under the sensor blocks, each direction as far as `Body::reach` and nothing where no
/// sensor block looks out, and the fills only in a body with a sensor block. Off, every direction sees
/// as far as `Body::range`, the food is read under the whole body and every body reads its fills.
pub fn sense<F: Fn(usize) -> f64, W: Fn(usize) -> f64>(a: &Agent, g: Grid, food: &F, water: &W, crowd: &[u16], senses: bool) -> Readings {
    let f = a.facing as usize;
    let dirs = [f, opposite(f), left_of(f), opposite(left_of(f))];
    let mut input = [0.0f32; N_IN];
    let under = if senses { a.touched(g) } else { a.under(g, NORTH, 0) };
    input[0] = under.iter().map(|c| food(c) as f32).sum();
    let mut blind = input;
    let (mut winput, mut wblind) = ([0.0f32; N_IN_WATER], [0.0f32; N_IN_WATER]);
    for (j, &d) in dirs.iter().enumerate() {
        let reach = if senses { a.body.reach(j) } else { a.body.range() };
        if reach == 0 {
            continue;
        }
        let (f1, o1, w1) = look(a, g, d, 1, food, water, crowd);
        blind[1 + j] = f1;
        blind[5 + j] = o1;
        input[1 + j] = f1;
        input[5 + j] = o1;
        wblind[j] = w1;
        winput[j] = w1;
        for r in 2..=reach {
            let (fr, ob, wr) = look(a, g, d, r, food, water, crowd);
            input[1 + j] += fr / r as f32;
            input[5 + j] += ob / r as f32;
            winput[j] += wr / r as f32;
        }
    }
    let feels = !senses || a.body.kinds[SENSOR] > 0;
    if feels {
        input[9] = (a.energy / a.body.threshold() as f64) as f32;
        winput[N_IN_WATER - 1] = 1.0 - a.water;
    }
    blind[9] = input[9];
    wblind[N_IN_WATER - 1] = winput[N_IN_WATER - 1];
    Readings { input, blind, water: winput, water_blind: wblind, breath: if feels { 1.0 - a.breath } else { 0.0 } }
}

/// The sensor blocks of a grid with nothing of the body beyond them to the front (north of the grid),
/// the back (south), the left (west) and the right (east) (e070): the blocks that look out that way.
pub fn sight_of(cells: &[u8; CELLS], s: usize) -> [u8; 4] {
    let mut n = [0u8; 4];
    for pos in 0..s * s {
        if cells[pos] != SENSOR as u8 {
            continue;
        }
        for (j, d) in [NORTH, SOUTH, WEST, EAST].into_iter().enumerate() {
            let mut q = neighbor(pos, d, s);
            while let Some(p) = q.filter(|&p| cells[p] == 0) {
                q = neighbor(p, d, s);
            }
            n[j] += q.is_none() as u8;
        }
    }
    n
}

/// The faces of each soft block (muscle, sensor, gut) of a grid with no block of the body beside
/// them (e066): open to the air. A hard block's are 0.
pub fn open_faces(cells: &[u8; CELLS], s: usize) -> [u8; CELLS] {
    let mut out = [0u8; CELLS];
    for pos in 0..s * s {
        if cells[pos] == 0 || cells[pos] == HARD as u8 {
            continue;
        }
        out[pos] = DIRS.iter().filter(|&&d| neighbor(pos, d, s).is_none_or(|q| cells[q] == 0)).count() as u8;
    }
    out
}

/// A body's turn in the air (e066): each soft block over ground that is not water loses `dry` x
/// the dryness there per open face, each block over water gives `drink`, both in blocks of
/// water, and the fill moves by their sum over the body's block count, up to full. Returns whether
/// a block was in water.
pub fn dry_turn(a: &mut Agent, g: Grid, wet: &[bool], dryness: &[f32], dry: f32, drink: f32) -> bool {
    let (mut lost, mut drunk) = (0.0f32, 0u16);
    for p in a.cells_held() {
        let (sx, sy) = a.sub_at(g, p, NORTH, 0);
        let c = g.wcell(sx, sy);
        if wet[c] {
            drunk += 1;
        } else {
            lost += dryness[c] * a.open[p] as f32;
        }
    }
    a.water = (a.water + (drink * drunk as f32 - dry * lost) / a.body.size.max(1) as f32).min(1.0);
    drunk > 0
}

/// A body's breath (e067): each block over water uses `breath` and each open face of a soft block
/// over water gives `breath` back, each block over land gives `inhale`, and the fill moves by the net
/// over the body's block count, up to full. Returns whether a block was over land.
pub fn breath_turn(a: &mut Agent, g: Grid, wet: &[bool], breath: f32, inhale: f32) -> bool {
    let (mut faces, mut under, mut ashore) = (0u16, 0u16, 0u16);
    for p in a.cells_held() {
        let (sx, sy) = a.sub_at(g, p, NORTH, 0);
        if wet[g.wcell(sx, sy)] {
            under += 1;
            faces += a.open[p] as u16;
        } else {
            ashore += 1;
        }
    }
    a.breath = (a.breath + (breath * (faces as f32 - under as f32) + inhale * ashore as f32) / a.body.size.max(1) as f32).min(1.0);
    ashore > 0
}

#[cfg(test)]
mod tests {
    use super::*;

    fn agent_of(cells: [u8; CELLS], x: usize, y: usize, facing: usize, density: f32) -> Agent {
        let mut a = Agent::new(0, Vec::new(), Vec::new(), Vec::new(), Body::new(cells, SIDE, [0.0; N_POLICY], 0, density), facing as u8, 1.0, 0);
        a.x = x;
        a.y = y;
        a
    }

    fn agent_with(cells: [u8; CELLS], x: usize, y: usize, facing: usize) -> Agent {
        agent_of(cells, x, y, facing, 1.0)
    }

    fn land(g: Grid) -> Occ {
        Occ::new(g, &vec![false; g.cells()], true)
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
        assert!(agents[0].fits(g, &occ, 0, EAST, 1));
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
        let mut occ = Occ::new(g, &sea, false);
        assert_eq!(occ.at(g, 8, 0, SURFACE), WALL);
        assert_eq!(occ.at(g, 8, 0, BOTTOM), WALL);
        assert_eq!(occ.at(g, 7, 0, BOTTOM), FREE);
        let mut agents = vec![agent_with(tooth(), 0, 8, EAST)];
        occ.claim(g, &agents[0], 0);
        assert!(!agents[0].fits(g, &occ, 0, EAST, 1));
        let mut c = Counters::default();
        let mut carrion = vec![0.0; g.cells()];
        assert!(push(&mut agents, 0, EAST, g, &mut occ, &mut carrion, 1.0, &mut c).is_empty());
        assert_eq!((c.contacts, c.cells_broken), (0, 0));
        // A new body cannot be placed on the sea.
        let b = agent_with(tooth(), 8, 0, NORTH);
        assert!(!b.fits(g, &occ, FREE, NORTH, 0));
    }

    #[test]
    fn the_water_has_two_layers() {
        // World columns 0-3 are land (sub-cells x < 16), the rest water. The tooth faces east with
        // its tip at sub-cell (x + 7, 10), and a soft body lies just ahead of it.
        let g = Grid::new(8, 8);
        let sea: Vec<bool> = (0..g.cells()).map(|c| c % g.w >= 4).collect();
        let meet = |x: usize, hunter: f32, prey: f32| {
            let mut occ = Occ::new(g, &sea, true);
            let mut soft = [0u8; CELLS];
            soft[0] = MUSCLE as u8;
            soft[1] = MUSCLE as u8;
            let mut agents = vec![agent_of(tooth(), x, 8, EAST, hunter), agent_of(soft, x + 8, 10, NORTH, prey)];
            occ.claim(g, &agents[0], 0);
            occ.claim(g, &agents[1], 1);
            let fits = agents[0].fits(g, &occ, 0, EAST, 1);
            let mut c = Counters::default();
            let mut carrion = vec![0.0; g.cells()];
            push(&mut agents, 0, EAST, g, &mut occ, &mut carrion, 1.0, &mut c);
            (fits, c.contacts, c.cells_broken)
        };
        // In the water a light body and a dense one pass through each other; two of a layer meet,
        // and force 2 breaks the softer face.
        assert_eq!(meet(16, 0.5, 1.2), (true, 0, 0));
        assert_eq!(meet(16, 0.5, 0.5), (false, 1, 1));
        assert_eq!(meet(16, 1.5, 1.5), (false, 1, 1));
        // On land they meet: the tip's 3 x 0.5 is harder than the soft face's 1 x 1.2.
        assert_eq!(meet(0, 0.5, 1.2), (false, 1, 1));
        // The crowd: in the water in its layer only, on land in both; over the edge, each sub-cell
        // by its medium.
        let layer_sum = |occ: &Occ, l: usize| occ.crowd.iter().skip(l).step_by(2).map(|&n| n as u32).sum::<u32>();
        let mut occ = Occ::new(g, &sea, true);
        let light = agent_of(tooth(), 16, 8, EAST, 0.5);
        occ.claim(g, &light, 0);
        assert_eq!((layer_sum(&occ, SURFACE), layer_sum(&occ, BOTTOM), occ.medium(g, &light)), (3, 0, 1));
        occ.release(g, &light);
        let dense = agent_of(tooth(), 0, 8, EAST, 1.5);
        occ.claim(g, &dense, 0);
        assert_eq!((layer_sum(&occ, SURFACE), layer_sum(&occ, BOTTOM), occ.medium(g, &dense)), (3, 3, 0));
        occ.release(g, &dense);
        let edge = agent_of(tooth(), 10, 8, EAST, 0.5);
        occ.claim(g, &edge, 7);
        assert_eq!((occ.at(g, 15, 10, BOTTOM), occ.at(g, 16, 10, BOTTOM), occ.at(g, 16, 10, SURFACE)), (7, FREE, 7));
    }

    #[test]
    fn soft_faces_dry_in_the_air_and_blocks_in_water_drink() {
        // World columns 0-3 are dry land (sub-cells x < 16), the rest water; the air's dryness is
        // 1/2 over every cell.
        let g = Grid::new(8, 8);
        let wet: Vec<bool> = (0..g.cells()).map(|c| c % g.w >= 4).collect();
        let dryness = vec![0.5f32; g.cells()];
        // Two muscles side by side: three open faces each, whichever way the body faces.
        let mut pair = [0u8; CELLS];
        pair[0] = MUSCLE as u8;
        pair[1] = MUSCLE as u8;
        let mut a = agent_with(pair, 0, 0, EAST);
        assert_eq!((a.body.open_soft, a.open.iter().map(|&f| f as u16).sum::<u16>()), (6, 6));
        assert!(!dry_turn(&mut a, g, &wet, &dryness, 0.1, 0.1));
        assert!((a.water - (1.0 - 0.1 * 0.5 * 6.0 / 2.0)).abs() < 1e-6, "{}", a.water);
        // In the water it loses nothing and each block drinks, up to full.
        a.x = 16;
        assert!(dry_turn(&mut a, g, &wet, &dryness, 0.1, 0.1));
        assert!((a.water - 0.95).abs() < 1e-6, "{}", a.water);
        dry_turn(&mut a, g, &wet, &dryness, 0.1, 0.1);
        assert_eq!(a.water, 1.0);
        // A gut walled in by hard blocks on its four sides has no open face, and a hard block
        // loses nothing.
        let mut shell = [0u8; CELLS];
        shell[SIDE + 1] = DIGESTIVE as u8;
        for q in [1, SIDE, SIDE + 2, 2 * SIDE + 1] {
            shell[q] = HARD as u8;
        }
        let mut b = agent_with(shell, 0, 0, SOUTH);
        assert_eq!(b.body.open_soft, 0);
        dry_turn(&mut b, g, &wet, &dryness, 0.1, 0.1);
        assert_eq!(b.water, 1.0);
    }

    #[test]
    fn a_closed_body_suffocates_in_water_and_every_block_breathes_on_land() {
        // World columns 0-3 are land (sub-cells x < 16), the rest water.
        let g = Grid::new(8, 8);
        let wet: Vec<bool> = (0..g.cells()).map(|c| c % g.w >= 4).collect();
        // A solid 6x6 of guts opens 24 faces for 36 blocks: in the water it is 12 blocks short.
        let mut solid = [0u8; CELLS];
        for r in 0..6 {
            for c in 0..6 {
                solid[r * SIDE + c] = DIGESTIVE as u8;
            }
        }
        let mut a = agent_with(solid, 16, 0, NORTH);
        assert_eq!((a.body.size, a.body.open_soft), (36, 24));
        assert!(!breath_turn(&mut a, g, &wet, 0.1, 0.1));
        assert!((a.breath - (1.0 - 0.1 * 12.0 / 36.0)).abs() < 1e-6, "{}", a.breath);
        // On land every block gives `inhale`.
        a.x = 0;
        a.breath = 0.5;
        assert!(breath_turn(&mut a, g, &wet, 0.1, 0.1));
        assert!((a.breath - 0.6).abs() < 1e-6, "{}", a.breath);
        // Two muscles side by side open 6 faces for 2 blocks: in the water they refill.
        let mut pair = [0u8; CELLS];
        pair[0] = MUSCLE as u8;
        pair[1] = MUSCLE as u8;
        let mut b = agent_with(pair, 16, 0, EAST);
        b.breath = 0.5;
        breath_turn(&mut b, g, &wet, 0.1, 0.1);
        assert!((b.breath - 0.7).abs() < 1e-6, "{}", b.breath);
        breath_turn(&mut b, g, &wet, 0.1, 0.1);
        breath_turn(&mut b, g, &wet, 0.1, 0.1);
        assert_eq!(b.breath, 1.0);
        // A gut walled in by hard blocks breathes through nothing: 5 blocks short.
        let mut shell = [0u8; CELLS];
        shell[SIDE + 1] = DIGESTIVE as u8;
        for q in [1, SIDE, SIDE + 2, 2 * SIDE + 1] {
            shell[q] = HARD as u8;
        }
        let mut c = agent_with(shell, 16, 0, SOUTH);
        breath_turn(&mut c, g, &wet, 0.1, 0.1);
        assert!((c.breath - 0.9).abs() < 1e-6, "{}", c.breath);
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
        assert_eq!(occ.crowd.iter().map(|&n| n as u32).sum::<u32>(), 2 * (3 + 2)); // land: both layers
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

    #[test]
    fn the_values_of_a_life_come_from_the_genome() {
        let mut rng = Rng(5);
        let mut laws = Laws::new(&mut rng, 5);
        let genomes: Vec<Vec<Gene>> = (0..200).map(|_| parse_genes(&(0..N).map(|_| rng.below(4) as u8).collect::<Vec<u8>>())).collect();
        // Off, every body holds today's constants and its threshold is 2 + 0.1 x its mass.
        for genes in &genomes {
            let b = develop_genes(genes, &laws);
            assert_eq!((b.breed, b.share, b.store), (BREED, SHARE, STORE));
            assert_eq!(b.threshold().to_bits(), (2.0 + 0.1 * b.mass).to_bits());
        }
        // On, each lies within x0.5 to x2 of its constant, differs between genomes, and follows the
        // gene list; the body itself is the same as off.
        laws.history = true;
        let within = |v: f32, c: f32| (0.5 * c..=2.0 * c).contains(&v);
        let mut seen = Vec::new();
        for genes in &genomes {
            let b = develop_genes(genes, &laws);
            assert!(within(b.breed, BREED) && within(b.share, SHARE) && within(b.store, STORE), "{} {} {}", b.breed, b.share, b.store);
            assert_eq!(develop_genes(genes, &laws).store.to_bits(), b.store.to_bits());
            laws.history = false;
            assert_eq!(develop_genes(genes, &laws).cells, b.cells);
            laws.history = true;
            seen.push((b.breed, b.share, b.store));
        }
        let spread = |f: &dyn Fn(&(f32, f32, f32)) -> f32| seen.iter().map(f).fold(f32::MIN, f32::max) / seen.iter().map(f).fold(f32::MAX, f32::min);
        assert!(spread(&|v| v.0) > 1.5 && spread(&|v| v.1) > 1.5 && spread(&|v| v.2) > 1.5);
    }

    #[test]
    fn a_sensor_looks_out_where_nothing_of_its_body_lies_beyond() {
        // A sensor in the grid's corner, a row of muscle under it, a second sensor under the row with
        // a gut to its right, and a third walled in by guts.
        let mut cells = [0u8; CELLS];
        cells[0] = SENSOR as u8; // looks out to the front, the left and the right
        for c in 0..3 {
            cells[SIDE + c] = MUSCLE as u8;
        }
        cells[2 * SIDE + 1] = SENSOR as u8; // to the back and the left
        cells[2 * SIDE + 2] = DIGESTIVE as u8;
        for q in [3 * SIDE + 5, 4 * SIDE + 4, 4 * SIDE + 6, 5 * SIDE + 5] {
            cells[q] = DIGESTIVE as u8;
        }
        cells[4 * SIDE + 5] = SENSOR as u8; // walled in on its four sides: looks out nowhere
        let b = Body::new(cells, SIDE, [0.0; N_POLICY], 0, 1.0);
        assert_eq!(b.sight, [1, 1, 2, 1]);
        assert_eq!((0..4).map(|j| b.reach(j)).collect::<Vec<_>>(), vec![2, 2, 3, 2]);
        assert_eq!(b.range(), 4);
    }

    #[test]
    fn a_body_senses_only_through_its_sensor_blocks() {
        let g = Grid::new(8, 8);
        let occ = land(g);
        let food = |c: usize| c as f64;
        let water = |_: usize| 1.0;
        // Two guts and a muscle, no sensor block: off, it sees around it and reads its fills; on, nothing.
        let mut cells = [0u8; CELLS];
        cells[0] = DIGESTIVE as u8;
        cells[1] = MUSCLE as u8;
        cells[2] = DIGESTIVE as u8;
        let mut a = agent_with(cells, 16, 16, NORTH);
        (a.water, a.breath) = (0.5, 0.75);
        let off = sense(&a, g, &food, &water, &occ.crowd, false);
        assert!(off.input[..5].iter().all(|&v| v > 0.0) && off.input[9] > 0.0, "{:?}", off.input);
        assert_eq!((off.water[4], off.breath), (0.5, 0.25));
        let on = sense(&a, g, &food, &water, &occ.crowd, true);
        assert!(on.input.iter().chain(&on.water).all(|&v| v == 0.0) && on.breath == 0.0);
        // A sensor in the front row and a row of six guts under it, over world cells (4, 4) and (5, 4):
        // on, it touches the first cell only, sees the front, the left and the right as far as the body
        // sees off, reads the fills, and sees nothing behind. The same facing east.
        let mut cells = [0u8; CELLS];
        cells[0] = SENSOR as u8;
        for c in 0..6 {
            cells[SIDE + c] = DIGESTIVE as u8;
        }
        for facing in [NORTH, EAST] {
            let mut a = agent_with(cells, 16, 16, facing);
            (a.water, a.breath) = (0.5, 0.75);
            let (off, on) = (sense(&a, g, &food, &water, &occ.crowd, false), sense(&a, g, &food, &water, &occ.crowd, true));
            if facing == NORTH {
                assert_eq!((off.input[0], on.input[0]), ((4 * 8 + 4 + 4 * 8 + 5) as f32, (4 * 8 + 4) as f32));
            }
            for j in [0, 2, 3] {
                assert_eq!((on.input[1 + j], on.water[j]), (off.input[1 + j], off.water[j]));
            }
            assert!(off.input[2] > 0.0 && off.water[1] > 0.0);
            assert_eq!((on.input[2], on.water[1]), (0.0, 0.0));
            assert_eq!((on.input[9], on.water[4], on.breath), (off.input[9], off.water[4], off.breath));
        }
    }

    /// Not a check: the values of random genomes under seed 9's law table, the start of e069's pilot
    /// before any selection (`cargo test --release -p e070_senses start_spread -- --ignored --nocapture`).
    #[test]
    #[ignore]
    fn start_spread() {
        let mut rng = Rng(9u64.wrapping_mul(0x9E3779B97F4A7C15) | 1);
        let mut laws = Laws::new(&mut rng, 9);
        laws.history = true;
        let mut v: [Vec<f32>; 4] = Default::default();
        for _ in 0..5_000 {
            let b = develop_genes(&parse_genes(&(0..N).map(|_| rng.below(4) as u8).collect::<Vec<u8>>()), &laws);
            for (k, x) in [b.breed / BREED, b.share / SHARE, b.store / STORE, b.density].into_iter().enumerate() {
                v[k].push(x);
            }
        }
        for (name, mut x) in ["breed", "share", "store", "density"].into_iter().zip(v) {
            x.sort_by(f32::total_cmp);
            let q = |p: f64| x[((x.len() - 1) as f64 * p) as usize];
            let ends = x.iter().filter(|&&y| !(0.55..=1.8).contains(&y)).count() as f32 / x.len() as f32;
            println!("{name}: over its centre p10 {:.2} p25 {:.2} p50 {:.2} p75 {:.2} p90 {:.2}; within 10% of an end {:.0}%", q(0.1), q(0.25), q(0.5), q(0.75), q(0.9), 100.0 * ends);
        }
    }
}
