//! e018: a closed cycle through the soil. e017's world (space at the resolution of the body,
//! facing, two kinds of place, contact physics, a cell costs what it holds, per-body cost,
//! work = force x distance, a cell held by a body does not regrow, a dead body is food where
//! it lies) with one law added about matter:
//!
//! - Matter does not vanish. Every unit of it is in one of four places: the soil of a cell,
//!   the plant on a cell, dead matter lying on a cell, or a body (its cells and its energy).
//!   A plant grows out of the soil of its cell, at most the sun's rate (today's regrowth field)
//!   per step and never above the cap, and not while a body stands on the cell (e016). What a
//!   body spends (its upkeep and the work of moving) falls to the soil of the cell under it.
//!   Dead matter that nobody eats rots into the soil of its cell at DECAY per step. The sun
//!   bounds the speed, the soil bounds the amount, and the total is what the world started with.
//!
//! Two arguments set the world: the matter per cell at the start (`matter`, the cap by
//! default: e017's start, plants at the cap and empty soil; above the cap the rest is soil,
//! below it the plants are that much and the soil empty), and the patch widths, where a width
//! of 0 means the sun is uniform (RES_GROWTH on every cell, one kind of place).
//!
//! Everything else is e017 at a cell of 0.02. The log gets `soil` (matter in the soil),
//! `matter` (the total: soil, plants, dead matter, bodies), `barren` (regrowth the sun would
//! have given but the soil could not, per step), `rot` (dead matter returned to the soil per
//! step) and `spent` (what bodies returned to the soil per step); the snapshots get the soil.
use std::collections::HashMap;
use std::io::Write;

// World (as e001/e003). Width and height are arguments; 64 is e006.
const RES_CAP: f32 = 8.0; // what a cell can hold; e011's runs (no regrowth lost to it at any width)
const RES_GROWTH: f32 = 0.01; // regrowth per cell of the world per step, spread over the patches
const INIT_POP_PER_CELL: f32 = 400.0 / 4096.0; // e006's 400 on 64x64
// Patchy food: one patch per PATCH_AREA cells, a Gaussian of width sigma, whose center takes a
// random step of one cell every PATCH_DRIFT steps. Peak regrowth is set so that the sum over the
// world equals uniform regrowth: RES_GROWTH * PATCH_AREA / (2 pi sigma^2), 0.10 per step at
// width 8 and 6.5 at width 1.
const PATCH_AREA: usize = 4096;
const PATCH_DRIFT: u64 = 50;
const N_PLACES: usize = 2; // kinds of place a world can have (the length of the sigma list, at most)
const NO_PLACE: u8 = N_PLACES as u8; // a cell beyond every patch
const INIT_ENERGY: f32 = 5.0;
const MUTATIONS_PER_CHILD: usize = 2;
const MAX_AGE: u32 = 3000;

// Costs and gains, all per block.
const UPKEEP: f32 = 0.002; // per block per step
// Per body per step, besides its blocks: an individual costs the world something whatever its
// size (the world's compute is per agent). Set to the upkeep of 16 blocks; it bounds the
// population at regrowth / UPKEEP_BODY, about 5,000 on 128x128. Without it the first trial
// filled the world with 4-cell bodies (14,000 of them): plant intake is capped by the food in
// one cell whatever the body, so the smallest body was the best grazer.
const UPKEEP_BODY: f32 = 0.032;
const MOVE_COST: f32 = 0.001; // per block of mass moved per sub-cell moved (work = force x distance); nothing moved, nothing paid
const BITE: f32 = 0.02; // plant intake per digestive block per step
const CELL_ENERGY: f32 = 0.02; // energy in the matter of one cell: paid to build it, gained when it is eaten (the default; an argument)
const DECAY: f32 = 0.01; // share of the dead matter lying on a cell that rots into its soil per step (a corpse nobody eats is soil in a few hundred steps)
const HARDNESS: u8 = 3; // a hard cell resists this much per contiguous hard cell behind the tip; other cells 1
const YOUNG: u32 = 50; // a death by damage before this age counts as a newborn's

// Genome and network (as e002/e004).
const N: usize = 512;
const PROMOTER: [u8; 3] = [0, 1, 0];
const GENE_LEN: usize = 8;
const TAG_LEN: usize = 4;
const T: usize = 40;

// Body (as e004).
const SIDE: usize = 8;
const CELLS: usize = SIDE * SIDE;
const N_KINDS: usize = 5; // empty, hard, muscle, sensor, digestive
const HARD: usize = 1;
const MUSCLE: usize = 2;
const SENSOR: usize = 3;
const DIGESTIVE: usize = 4;
const N_MORPH: usize = 6;
// Development runs the network once per cell plus once without position (for the policy).
// All of these runs are independent, so they are settled together as one batch.
const CTX: usize = CELLS + 1;

// Space: a world cell is SUB x SUB body cells (sub-cells). Occupancy is kept per sub-cell; food
// per world cell. A body anchored at sub-cell (x, y) fills the sub-cells (x + c, y + r) of its
// world-frame grid that hold a cell, so it lies over up to 3x3 world cells.
const SUB: usize = 4;
const SUB_CELLS: usize = SUB * SUB;

// Policy: 10 inputs -> 4 actions (stay, forward, turn left, turn right), read from the same
// table (no position input). The inputs are seen from the body: food under it, food and bodies
// ahead, behind, left and right, and energy.
const N_IN: usize = 10;
const N_OUT: usize = 4;
const N_POLICY: usize = N_IN * N_OUT + N_OUT;
const K: usize = N_KINDS + N_POLICY;

// Sides of a body, and the lines that meet a neighbor on that side. In the body frame NORTH is
// the front; a facing is the world direction the front points to.
const NORTH: usize = 0;
const SOUTH: usize = 1;
const EAST: usize = 2;
const WEST: usize = 3;
const DIRS: [usize; 4] = [NORTH, SOUTH, EAST, WEST];

fn opposite(d: usize) -> usize {
    match d {
        NORTH => SOUTH,
        SOUTH => NORTH,
        EAST => WEST,
        _ => EAST,
    }
}

/// The world direction to the left of facing `d`.
fn left_of(d: usize) -> usize {
    match d {
        NORTH => WEST,
        WEST => SOUTH,
        SOUTH => EAST,
        _ => NORTH,
    }
}

/// Where cell i of the body grid lands in the world frame when the body faces `f`: the front row
/// becomes the side of the grid that points to `f` (a rotation about the center of the grid).
fn to_world(i: usize, f: usize) -> usize {
    let (r, c) = (i / SIDE, i % SIDE);
    let m = SIDE - 1;
    let (r2, c2) = match f {
        NORTH => (r, c),
        SOUTH => (m - r, m - c),
        EAST => (c, m - r),
        _ => (m - c, r),
    };
    r2 * SIDE + c2
}

/// The inverse of `to_world`: the body-grid cell under world-frame cell i.
fn to_body(i: usize, f: usize) -> usize {
    let (r2, c2) = (i / SIDE, i % SIDE);
    let m = SIDE - 1;
    let (r, c) = match f {
        NORTH => (r2, c2),
        SOUTH => (m - r2, m - c2),
        EAST => (m - c2, r2),
        _ => (c2, m - r2),
    };
    r * SIDE + c
}

fn rotate(cells: &[u8; CELLS], f: usize) -> [u8; CELLS] {
    let mut out = [0u8; CELLS];
    for (i, &c) in cells.iter().enumerate() {
        out[to_world(i, f)] = c;
    }
    out
}

/// The cells a grid holds (their indices) and their bounding box (r0, r1, c0, c1), inclusive.
fn filled(cells: &[u8; CELLS]) -> ([u8; CELLS], u8, [u8; 4]) {
    let mut list = [0u8; CELLS];
    let mut n = 0u8;
    let mut bb = [SIDE as u8, 0, SIDE as u8, 0];
    for (i, &c) in cells.iter().enumerate() {
        if c != 0 {
            list[n as usize] = i as u8;
            n += 1;
            let (r, col) = ((i / SIDE) as u8, (i % SIDE) as u8);
            bb = [bb[0].min(r), bb[1].max(r), bb[2].min(col), bb[3].max(col)];
        }
    }
    if n == 0 {
        bb = [0; 4];
    }
    (list, n, bb)
}

/// The grid cell next to `pos` in direction `d`, if it is inside the grid.
fn neighbor(pos: usize, d: usize) -> Option<usize> {
    let (r, c) = (pos / SIDE, pos % SIDE);
    let (r, c) = match d {
        NORTH => (r.checked_sub(1)?, c),
        SOUTH => (r + 1, c),
        EAST => (r, c + 1),
        _ => (r, c.checked_sub(1)?),
    };
    (r < SIDE && c < SIDE).then_some(r * SIDE + c)
}

/// The hardness of the face of the cell at `pos` that looks against direction `into`: 3 per
/// contiguous hard cell from `pos` inward (in direction `into`), else 1 (e010's tip hardness,
/// for any cell whose face can be touched).
fn face_hardness(cells: &[u8; CELLS], pos: usize, into: usize) -> u8 {
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
        p = neighbor(q, into);
    }
    HARDNESS * n
}

/// The line (in the frame of the grid) that cell `pos` belongs to when the body moves in
/// direction d: a column for north and south, a row for east and west.
fn line_of(pos: usize, d: usize) -> usize {
    match d {
        NORTH | SOUTH => pos % SIDE,
        _ => pos / SIDE,
    }
}

/// A small set of world cells (a body lies over at most 3x3).
#[derive(Clone, Copy, Default)]
struct Cells9 {
    c: [usize; 9],
    n: usize,
}

impl Cells9 {
    fn contains(&self, x: usize) -> bool {
        self.c[..self.n].contains(&x)
    }
    fn add(&mut self, x: usize) {
        if !self.contains(x) && self.n < 9 {
            self.c[self.n] = x;
            self.n += 1;
        }
    }
    fn iter(&self) -> impl Iterator<Item = usize> + '_ {
        self.c[..self.n].iter().copied()
    }
}

// Species.
const D: usize = 6; // two agents can mate if their distance is at most D
const MIN_LINEAGE: usize = 5; // a mating-connected group of at least this size is a lineage
const LINEAGE_INTERVAL: u64 = 1_000;
const LINEAGE_CONFIRM: u32 = 5; // detections in a row a group must exist before it is a lineage
const DIST_INTERVAL: u64 = 50_000; // pairwise distance histograms

const LOG_INTERVAL: u64 = 10_000;
const LONG_INTERVAL: u64 = 5_000;
const CLIP_START: u64 = 600_000;
const CLIP_LEN: u64 = 400;
const AGENT_DUMP_INTERVAL: u64 = 100_000;

struct Rng(u64);

impl Rng {
    fn next_u64(&mut self) -> u64 {
        let mut x = self.0;
        x ^= x >> 12;
        x ^= x << 25;
        x ^= x >> 27;
        self.0 = x;
        x.wrapping_mul(0x2545F4914F6CDD1D)
    }
    fn f32(&mut self) -> f32 {
        (self.next_u64() >> 40) as f32 / (1u64 << 24) as f32
    }
    fn below(&mut self, n: usize) -> usize {
        (self.next_u64() % n as u64) as usize
    }
}

#[derive(PartialEq)]
struct Gene {
    tag: [u8; TAG_LEN],
    product: [u8; TAG_LEN],
}

impl Gene {
    /// The 8 symbols packed into 16 bits, for sorted gene lists.
    fn key(&self) -> u16 {
        self.tag.iter().chain(&self.product).fold(0, |acc, &s| acc * 4 + s as u16)
    }
}

fn sorted_keys(genes: &[Gene]) -> Vec<u16> {
    let mut k: Vec<u16> = genes.iter().map(Gene::key).collect();
    k.sort_unstable();
    k
}

/// Distance between two genomes: number of genes in one gene list but not the other
/// (the symmetric difference of the two sorted lists, with multiplicity).
fn gene_distance(a: &[u16], b: &[u16]) -> usize {
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

fn hamming(a: &[u8], b: &[u8]) -> usize {
    a.iter().zip(b).filter(|(x, y)| x != y).count()
}

struct Laws {
    morphogen: [[u8; TAG_LEN]; N_MORPH],
    table: Vec<[f32; K]>,
    /// Morphogen level per context; the last context (the policy run) has no position.
    morph_level: [[f32; CTX]; N_MORPH],
}

impl Laws {
    fn new(rng: &mut Rng) -> Self {
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
        let mut morph_level = [[0.0f32; CTX]; N_MORPH];
        let c = (SIDE as f32 - 1.0) / 2.0;
        let rmax = (2.0 * c * c).sqrt();
        for i in 0..CELLS {
            let x = (i % SIDE) as f32 / (SIDE as f32 - 1.0);
            let y = (i / SIDE) as f32 / (SIDE as f32 - 1.0);
            let dx = (i % SIDE) as f32 - c;
            let dy = (i / SIDE) as f32 - c;
            let r = (dx * dx + dy * dy).sqrt() / rmax;
            for (m, v) in [x, 1.0 - x, y, 1.0 - y, r, 1.0 - r].into_iter().enumerate() {
                morph_level[m][i] = 2.0 * v - 1.0;
            }
        }
        Laws { morphogen, table, morph_level }
    }
}

fn parse_genes(genome: &[u8]) -> Vec<Gene> {
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

/// One line of a body seen from one side: how hard the tip is and the force behind it. Hardness 0 means the line is empty on that side: nothing to touch.
#[derive(Clone, Copy, Default)]
struct Tip {
    hardness: u8,
    force: u8,
}

/// The tips of every line on every side of a grid (sides and lines in the frame of the grid:
/// for NORTH and SOUTH the lines are columns from west to east, for EAST and WEST rows from
/// north to south).
fn tips_of(cells: &[u8; CELLS]) -> [[Tip; SIDE]; 4] {
    let mut tips = [[Tip::default(); SIDE]; 4];
    for side in 0..4 {
        for line in 0..SIDE {
            // The cells of this line, from the outside in.
            let at = |k: usize| -> usize {
                match side {
                    NORTH => k * SIDE + line,
                    SOUTH => (SIDE - 1 - k) * SIDE + line,
                    EAST => line * SIDE + (SIDE - 1 - k),
                    _ => line * SIDE + k,
                }
            };
            let mut tip = Tip::default();
            let force = (0..SIDE).filter(|&k| cells[at(k)] == MUSCLE as u8).count() as u8;
            if let Some(k0) = (0..SIDE).find(|&k| cells[at(k)] != 0) {
                let hardness = if cells[at(k0)] == HARD as u8 {
                    HARDNESS * (k0..SIDE).take_while(|&k| cells[at(k)] == HARD as u8).count() as u8
                } else {
                    1
                };
                tip = Tip { hardness, force };
            }
            tips[side][line] = tip;
        }
    }
    tips
}

#[derive(Clone)]
struct Body {
    cells: [u8; CELLS],
    mass: u8,
    kinds: [u8; N_KINDS],
    tips: [[Tip; SIDE]; 4], // per side, per line, in the body frame (NORTH is the front)
    extent: [u8; 2], // cells the body spans along the facing (rows) and across it (columns)
    policy: [f32; N_POLICY],
    n_genes: u16,
}

impl Body {
    fn new(cells: [u8; CELLS], policy: [f32; N_POLICY], n_genes: u16) -> Self {
        let mut b = Body { cells, mass: 0, kinds: [0; N_KINDS], tips: [[Tip::default(); SIDE]; 4], extent: [0; 2], policy, n_genes };
        b.refresh();
        b
    }
    /// Recompute what follows from the cells: mass, counts per kind, the tips of every line
    /// on every side, and the extent. Called at birth and whenever a cell breaks.
    fn refresh(&mut self) {
        self.kinds = [0; N_KINDS];
        for &c in &self.cells {
            self.kinds[c as usize] += 1;
        }
        self.mass = CELLS as u8 - self.kinds[0];
        self.tips = tips_of(&self.cells);
        let (_, n, bb) = filled(&self.cells);
        self.extent = if n == 0 { [0, 0] } else { [bb[1] - bb[0] + 1, bb[3] - bb[2] + 1] };
    }
    fn speed(&self) -> f32 {
        if self.mass == 0 { 0.0 } else { self.kinds[MUSCLE] as f32 / self.mass as f32 }
    }
    fn sense(&self) -> f32 {
        (self.kinds[SENSOR] as f32 / 8.0).min(1.0)
    }
    fn threshold(&self) -> f32 {
        2.0 + 0.1 * self.mass as f32
    }
    /// Measures of shape, for the log only (no rule reads them). Bite: the largest force behind
    /// a hard tip on the front (the only side that pushes). Bite any: the same on any side
    /// (e012's bite). Shell: the mean hardness of the tips that can be touched, on all sides or
    /// on one. Open lines: lines with nothing to touch.
    fn bite(&self) -> u8 {
        self.tips[NORTH].iter().filter(|t| t.hardness > 1).map(|t| t.force).max().unwrap_or(0)
    }
    fn bite_any(&self) -> u8 {
        self.tips.iter().flatten().filter(|t| t.hardness > 1).map(|t| t.force).max().unwrap_or(0)
    }
    fn shell_of(tips: &[Tip]) -> f32 {
        let touchable: Vec<u8> = tips.iter().filter(|t| t.hardness > 0).map(|t| t.hardness).collect();
        if touchable.is_empty() { 0.0 } else { touchable.iter().map(|&h| h as f32).sum::<f32>() / touchable.len() as f32 }
    }
    fn shell(&self) -> f32 {
        Self::shell_of(&self.tips.concat())
    }
    fn shell_side(&self, side: usize) -> f32 {
        Self::shell_of(&self.tips[side])
    }
    fn open_lines(&self) -> u8 {
        self.tips.iter().flatten().filter(|t| t.hardness == 0).count() as u8
    }
}

/// Development (e004): the network settles once per cell (with position) and once without
/// position (for the policy). All 65 runs are batched: `level` is gene-major, so the inner
/// loops run over the contexts and vectorize. The order of floating point operations per
/// context is the one of e004, so the bodies are the same.
fn develop_genes(genes: &[Gene], laws: &Laws) -> Body {
    let n = genes.len();
    let mut w = vec![0.0f32; n * n]; // w[i * n + j]: gene j acting on gene i
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

    let mut level = vec![0.5f32; n * CTX]; // level[i * CTX + c]
    let mut next = vec![0.0f32; n * CTX];
    let mut acc = [0.0f32; CTX];
    for _ in 0..T {
        for i in 0..n {
            acc.fill(0.0);
            for j in 0..n {
                let wij = w[i * n + j];
                for (a, &l) in acc.iter_mut().zip(&level[j * CTX..(j + 1) * CTX]) {
                    *a += wij * l;
                }
            }
            for m in 0..N_MORPH {
                let wim = wm[i * N_MORPH + m];
                for (a, &l) in acc.iter_mut().zip(&laws.morph_level[m]) {
                    *a += wim * l;
                }
            }
            for (o, &a) in next[i * CTX..(i + 1) * CTX].iter_mut().zip(&acc) {
                *o = sigmoid(3.0 * a - 1.0);
            }
        }
        std::mem::swap(&mut level, &mut next);
    }

    let mut cells = [0u8; CELLS];
    for (c, cell) in cells.iter_mut().enumerate() {
        let mut score = [0.0f32; N_KINDS];
        for (i, row) in rows.iter().enumerate() {
            let lv = level[i * CTX + c];
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
    let mut policy = [0.0f32; N_POLICY];
    for (i, row) in rows.iter().enumerate() {
        let lv = level[i * CTX + CELLS];
        for k in 0..N_POLICY {
            policy[k] += row[N_KINDS + k] * lv;
        }
    }
    for p in policy.iter_mut() {
        *p = sigmoid(*p) * 2.0 - 1.0;
    }
    Body::new(cells, policy, n as u16)
}

struct Agent {
    id: u64,
    lineage: u32, // 0 = none; otherwise inherited from the mother, corrected at each detection
    x: usize,
    y: usize,
    energy: f32,
    age: u32,
    plant: f32, // lifetime intake from plants
    meat: f32, // lifetime intake from broken cells of other bodies
    born_mass: u8,
    born_place: u8, // the place of the cell it was born in (a measure only)
    alive: bool,
    genome: Vec<u8>,
    keys: Vec<u16>, // sorted gene keys, for distances
    gene_ids: Vec<u16>, // gene keys in genome order: the body is a function of this list
    body: Body,
    facing: u8, // the world direction the front of the body points to
    // The body in the world frame: its cells rotated by the facing, the tips per world side,
    // the cells it holds (grid indices, `n_filled` of them) and their bounding box. (x, y) is
    // the sub-cell under the north-west corner of the grid.
    wcells: [u8; CELLS],
    tips: [[Tip; SIDE]; 4],
    filled: [u8; CELLS],
    n_filled: u8,
    bbox: [u8; 4],
}

impl Agent {
    fn distance(&self, other: &Agent) -> usize {
        gene_distance(&self.keys, &other.keys)
    }

    /// Recompute the world frame from the body and the facing. Called when the body is made,
    /// turns, or loses a cell.
    fn reframe(&mut self) {
        self.wcells = rotate(&self.body.cells, self.facing as usize);
        self.tips = tips_of(&self.wcells);
        let (list, n, bb) = filled(&self.wcells);
        self.filled = list;
        self.n_filled = n;
        self.bbox = bb;
    }
    fn cells_held(&self) -> impl Iterator<Item = usize> + '_ {
        self.filled[..self.n_filled as usize].iter().map(|&p| p as usize)
    }
    /// The sub-cell under grid cell `pos`, moved k sub-cells in direction d.
    fn sub_at(&self, g: Grid, pos: usize, d: usize, k: usize) -> (usize, usize) {
        g.sstep((self.x + pos % SIDE) % g.sw, (self.y + pos / SIDE) % g.sh, d, k)
    }
    /// The world cells under the body's bounding box, moved k sub-cells in direction d.
    fn under(&self, g: Grid, d: usize, k: usize) -> Cells9 {
        let mut out = Cells9::default();
        if self.n_filled == 0 {
            return out;
        }
        let [r0, r1, c0, c1] = self.bbox;
        let (sx, sy) = self.sub_at(g, r0 as usize * SIDE + c0 as usize, d, k);
        let nx = (sx % SUB + (c1 - c0) as usize) / SUB + 1;
        let ny = (sy % SUB + (r1 - r0) as usize) / SUB + 1;
        for j in 0..ny {
            for i in 0..nx {
                out.add(g.idx((sx / SUB + i) % g.w, (sy / SUB + j) % g.h));
            }
        }
        out
    }
    /// The world cell under the middle of the body (its place).
    fn here(&self, g: Grid) -> usize {
        let [r0, r1, c0, c1] = self.bbox;
        let (sx, sy) = self.sub_at(g, (r0 + r1) as usize / 2 * SIDE + (c0 + c1) as usize / 2, NORTH, 0);
        g.wcell(sx, sy)
    }
    /// World cells under the body's cells (the footprint), a measure.
    fn foot_n(&self, g: Grid) -> u8 {
        let mut out = Cells9::default();
        for p in self.cells_held() {
            let (sx, sy) = self.sub_at(g, p, NORTH, 0);
            out.add(g.wcell(sx, sy));
        }
        out.n as u8
    }
    /// Whether every cell of the body, moved k sub-cells in direction d, lands on a free
    /// sub-cell or on one of its own.
    fn fits(&self, g: Grid, occ: &[u32], me: u32, d: usize, k: usize) -> bool {
        self.cells_held().all(|p| {
            let (sx, sy) = self.sub_at(g, p, d, k);
            let o = occ[g.sidx(sx, sy)];
            o == u32::MAX || o == me
        })
    }

    /// 0 = plants only, 1 = mixed, 2 = meat only, 3 = nothing eaten yet.
    fn diet_class(&self) -> usize {
        let total = self.plant + self.meat;
        if total <= 0.0 {
            3
        } else if self.meat <= 0.0 {
            0
        } else if self.plant <= 0.0 {
            2
        } else {
            1
        }
    }
}

/// The world: w x h cells of food, and sw x sh sub-cells (SUB per cell) of occupancy.
#[derive(Clone, Copy)]
struct Grid {
    w: usize,
    h: usize,
    sw: usize,
    sh: usize,
}

impl Grid {
    fn new(w: usize, h: usize) -> Self {
        Grid { w, h, sw: w * SUB, sh: h * SUB }
    }
    fn idx(&self, x: usize, y: usize) -> usize {
        y * self.w + x
    }
    fn cells(&self) -> usize {
        self.w * self.h
    }
    fn sidx(&self, sx: usize, sy: usize) -> usize {
        sy * self.sw + sx
    }
    /// The world cell a sub-cell lies in.
    fn wcell(&self, sx: usize, sy: usize) -> usize {
        self.idx(sx / SUB, sy / SUB)
    }
    /// Sub-cell (sx, sy) moved k sub-cells in direction d, on the torus.
    fn sstep(&self, sx: usize, sy: usize, d: usize, k: usize) -> (usize, usize) {
        match d {
            NORTH => (sx, (sy + self.sh - k % self.sh) % self.sh),
            SOUTH => (sx, (sy + k) % self.sh),
            EAST => ((sx + k) % self.sw, sy),
            _ => ((sx + self.sw - k % self.sw) % self.sw, sy),
        }
    }
}

/// Occupancy: the body holding each sub-cell (u32::MAX: none), and per world cell the number
/// of sub-cells held (the crowd there, what a body sees ahead).
struct Occ {
    sub: Vec<u32>,
    crowd: Vec<u16>,
}

impl Occ {
    /// Write the body's index into its sub-cells and count them in the crowd.
    fn claim(&mut self, g: Grid, a: &Agent, v: u32) {
        for p in a.cells_held() {
            let (sx, sy) = a.sub_at(g, p, NORTH, 0);
            self.sub[g.sidx(sx, sy)] = v;
            self.crowd[g.wcell(sx, sy)] += 1;
        }
    }
    fn release(&mut self, g: Grid, a: &Agent) {
        for p in a.cells_held() {
            let (sx, sy) = a.sub_at(g, p, NORTH, 0);
            self.sub[g.sidx(sx, sy)] = u32::MAX;
            self.crowd[g.wcell(sx, sy)] -= 1;
        }
    }
    fn release_one(&mut self, g: Grid, a: &Agent, pos: usize) {
        let (sx, sy) = a.sub_at(g, pos, NORTH, 0);
        self.sub[g.sidx(sx, sy)] = u32::MAX;
        self.crowd[g.wcell(sx, sy)] -= 1;
    }
    /// Rewrite the index of a body whose place in the list changed.
    fn relabel(&mut self, g: Grid, a: &Agent, v: u32) {
        for p in a.cells_held() {
            let (sx, sy) = a.sub_at(g, p, NORTH, 0);
            self.sub[g.sidx(sx, sy)] = v;
        }
    }
}

/// Counters of the contact physics, summed over a log interval.
#[derive(Default)]
struct Counters {
    contacts: u64, // pairs whose lines touched
    cells_broken: u64,
    kills: u64, // deaths by damage
    prey_age: u64,
    kills_young: u64,
    meat_intake: f32,
    meat_at: [f32; N_PLACES + 1],
    dead: f64, // matter laid on the ground by the dead (cells and energy), summed over the interval
    dead_at: [f64; N_PLACES + 1],
}

/// Matter on the ground: what a cell holds as food (`res`), how much of that is dead matter
/// (`carrion`, at most `res`), and the soil of the cell (`soil`), which a plant grows out of.
struct Food {
    res: Vec<f32>,
    carrion: Vec<f32>,
    soil: Vec<f32>,
}

/// What one cell did in one step of regrowth.
#[derive(Default, PartialEq, Debug)]
struct Regrown {
    added: f32, // moved from the soil to the plant
    shaded: f32, // sun lost because a body stands on the cell
    wasted: f32, // sun lost because the plant is at the cap
    barren: f32, // sun lost because the soil has nothing left
    rot: f32, // dead matter moved to the soil
}

impl Food {
    /// One step of cell `c` under a sun of `sun`: dead matter rots into the soil, then the
    /// plant grows out of the soil by at most the sun, not above the cap, and not at all while
    /// a body holds the cell.
    fn regrow(&mut self, c: usize, sun: f32, held: bool, cap: f32) -> Regrown {
        let rot = self.carrion[c] * DECAY;
        self.carrion[c] -= rot;
        self.res[c] -= rot;
        self.soil[c] += rot;
        let lit = if held { 0.0 } else { sun };
        let room = lit.min((cap - self.res[c]).max(0.0));
        let added = room.min(self.soil[c]);
        self.soil[c] -= added;
        self.res[c] += added;
        Regrown { added, shaded: sun - lit, wasted: lit - room, barren: room - added, rot }
    }
    /// What a body spends falls to the soil of the cell under it.
    fn spend(&mut self, c: usize, e: f32) {
        self.soil[c] += e;
    }
    /// Dead matter `e` lies on world cell `c`, in full (the cap bounds what a plant grows to).
    fn lay(&mut self, c: usize, e: f32, place: &[u8], cc: &mut Counters) {
        if e <= 0.0 {
            return;
        }
        self.res[c] += e;
        self.carrion[c] += e;
        cc.dead += e as f64;
        cc.dead_at[place[c] as usize] += e as f64;
    }
    /// A gut takes `e` from cell `c`: returns (plant, dead matter) taken.
    fn take(&mut self, c: usize, e: f32) -> (f32, f32) {
        let share = if self.res[c] > 0.0 { (self.carrion[c] / self.res[c]).min(1.0) } else { 0.0 };
        let dead = e * share;
        self.res[c] -= e;
        self.carrion[c] = (self.carrion[c] - dead).max(0.0);
        (e - dead, dead)
    }
}

/// A dead body lies where it is: each cell is `cell_energy` of matter plus its share of the
/// energy the body held, on the world cell under it; a body with no cells leaves its energy on
/// the cell under its anchor. Called after the body's sub-cells are released.
fn lay_body(a: &Agent, g: Grid, food: &mut Food, place: &[u8], cell_energy: f32, cc: &mut Counters) {
    let energy = a.energy.max(0.0);
    if a.n_filled == 0 {
        food.lay(g.wcell(a.x, a.y), energy, place, cc);
        return;
    }
    let share = energy / a.n_filled as f32;
    for p in a.cells_held() {
        let (sx, sy) = a.sub_at(g, p, NORTH, 0);
        food.lay(g.wcell(sx, sy), cell_energy + share, place, cc);
    }
}

/// Body i moves one sub-cell in direction d. Every cell of i whose next sub-cell is held by
/// another body j meets the cell of j there, face to face, as e010's push into a shared cell:
/// the softer face breaks if the muscle of i in that line exceeds its hardness (the hardness of
/// a face is 3 per contiguous hard cell behind it, else 1). A broken cell is gone and its
/// matter and share of energy go to the other if it can digest. Returns, per body pressed, the
/// force against it: the muscle in the lines of i that press on it.
fn push(agents: &mut [Agent], i: usize, d: usize, g: Grid, occ: &mut Occ, place: &[u8], food: &mut Food, cell_energy: f32, c: &mut Counters) -> Vec<(usize, u8)> {
    let opp = opposite(d);
    let mut pressed: Vec<(usize, u8)> = Vec::new(); // (body in the way, force against it)
    let mut breaks: Vec<(usize, u8, usize)> = Vec::new(); // (victim, world-frame cell, eater)
    for p in agents[i].cells_held() {
        let (sx, sy) = agents[i].sub_at(g, p, d, 1);
        let j = occ.sub[g.sidx(sx, sy)];
        if j == u32::MAX || j as usize == i {
            continue;
        }
        let j = j as usize;
        // The cell of j under (sx, sy): its grid index in j's frame.
        let b = &agents[j];
        let (r, col) = ((sy + g.sh - b.y) % g.sh, (sx + g.sw - b.x) % g.sw);
        debug_assert!(r < SIDE && col < SIDE);
        let q = r * SIDE + col;
        let ha = face_hardness(&agents[i].wcells, p, opp);
        let hb = face_hardness(&b.wcells, q, d);
        let force = agents[i].tips[d][line_of(p, d)].force;
        match pressed.iter_mut().find(|e| e.0 == j) {
            Some(e) => e.1 = e.1.saturating_add(force),
            None => pressed.push((j, force)),
        }
        if hb < ha && force > hb {
            breaks.push((j, q as u8, i));
        } else if ha < hb && force > ha {
            breaks.push((i, p as u8, j));
        }
    }
    c.contacts += pressed.len() as u64;
    for (victim, pos, eater) in breaks {
        let v = &mut agents[victim];
        if v.wcells[pos as usize] == 0 {
            continue;
        }
        occ.release_one(g, v, pos as usize);
        let (sx, sy) = v.sub_at(g, pos as usize, NORTH, 0);
        let under = g.wcell(sx, sy);
        let bpos = to_body(pos as usize, v.facing as usize);
        let share = v.energy.max(0.0) / v.body.mass as f32;
        v.energy -= share;
        v.body.cells[bpos] = 0;
        v.body.refresh();
        v.reframe();
        c.cells_broken += 1;
        if v.body.mass == 0 && v.alive {
            v.alive = false;
            c.kills += 1;
            c.prey_age += v.age as u64;
            if v.age < YOUNG {
                c.kills_young += 1;
            }
        }
        let e = &mut agents[eater];
        if e.body.kinds[DIGESTIVE] > 0 {
            let gain = share + cell_energy;
            e.energy += gain;
            e.meat += gain;
            c.meat_intake += gain;
            c.meat_at[place[e.here(g)] as usize] += gain;
        } else {
            food.lay(under, share + cell_energy, place, c);
        }
    }
    pressed
}

/// Food patches: centers on the torus, the width of each (patch k has sigmas[k % sigmas.len()]),
/// the regrowth field they make, and the place of each cell: the kind (index in the sigma list)
/// of the patch that gives the cell the most regrowth, NO_PLACE beyond every patch. Recomputed
/// when the patches move.
struct Patches {
    centers: Vec<(usize, usize)>,
    sigmas: Vec<f32>,
    grow: Vec<f32>,
    place: Vec<u8>,
    rng: Rng, // own stream, as e007-e011
}

impl Patches {
    fn new(g: Grid, seed: u64, sigmas: Vec<f32>) -> Self {
        let mut rng = Rng(seed.wrapping_mul(0xD1B54A32D192ED03) | 1);
        let n = (g.cells() / PATCH_AREA).max(1);
        let centers = (0..n).map(|_| (rng.below(g.w), rng.below(g.h))).collect();
        let mut p = Patches { centers, sigmas, grow: vec![0.0; g.cells()], place: vec![NO_PLACE; g.cells()], rng };
        p.field(g);
        p
    }
    fn sigma_of(&self, k: usize) -> f32 {
        self.sigmas[k % self.sigmas.len()]
    }
    fn field(&mut self, g: Grid) {
        self.grow.iter_mut().for_each(|v| *v = 0.0);
        self.place.iter_mut().for_each(|v| *v = NO_PLACE);
        // A width of 0: the sun is uniform, RES_GROWTH on every cell, and every cell is place 0.
        if self.sigmas[0] == 0.0 {
            self.grow.iter_mut().for_each(|v| *v = RES_GROWTH);
            self.place.iter_mut().for_each(|v| *v = 0);
            return;
        }
        let mut best = vec![0.0f32; g.cells()]; // the largest single contribution to each cell
        for (k, &(cx, cy)) in self.centers.iter().enumerate() {
            let sigma = self.sigma_of(k);
            let kind = (k % self.sigmas.len()) as u8;
            let peak = RES_GROWTH * PATCH_AREA as f32 / (2.0 * std::f32::consts::PI * sigma * sigma);
            let r = (3.0 * sigma).ceil() as isize; // beyond 3 sigma the Gaussian is below 1.2% of the peak
            for dy in -r..=r {
                for dx in -r..=r {
                    let x = (cx as isize + dx).rem_euclid(g.w as isize) as usize;
                    let y = (cy as isize + dy).rem_euclid(g.h as isize) as usize;
                    let d2 = (dx * dx + dy * dy) as f32;
                    let c = g.idx(x, y);
                    let v = peak * (-d2 / (2.0 * sigma * sigma)).exp();
                    self.grow[c] += v;
                    if v > best[c] {
                        best[c] = v;
                        self.place[c] = kind;
                    }
                }
            }
        }
    }
    fn drift(&mut self, g: Grid) {
        for c in self.centers.iter_mut() {
            match self.rng.below(4) {
                0 => c.1 = (c.1 + g.h - 1) % g.h,
                1 => c.1 = (c.1 + 1) % g.h,
                2 => c.0 = (c.0 + 1) % g.w,
                _ => c.0 = (c.0 + g.w - 1) % g.w,
            }
        }
        self.field(g);
    }
}

fn act(policy: &[f32; N_POLICY], input: &[f32; N_IN]) -> usize {
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

fn cells_str(cells: &[u8; CELLS]) -> String {
    cells.iter().map(|&k| (b'0' + k) as char).collect()
}

struct Snapshots {
    long: std::io::BufWriter<std::fs::File>,
    clip: std::io::BufWriter<std::fs::File>,
    bodies: std::io::BufWriter<std::fs::File>,
    ids: HashMap<[u8; CELLS], u32>,
}

impl Snapshots {
    /// Food is written on a square-root scale of the cap (a wide patch holds 0.02-0.1 per cell,
    /// a narrow one up to 8; a linear scale showed only the narrow ones). The patches are written
    /// as center and width so that the viewer can draw each place.
    /// The soil (long frames only) is written on a log scale, 4 ln(1 + soil), 15 at most (a
    /// cell under a crowd can hold many times the cap).
    fn write_frame(&mut self, clip: bool, step: u64, food: &Food, patches: &Patches, agents: &[Agent]) {
        let f = if clip { &mut self.clip } else { &mut self.long };
        write!(f, "{{\"step\":{step},\"food\":[").unwrap();
        for (i, r) in food.res.iter().enumerate() {
            if i > 0 {
                f.write_all(b",").unwrap();
            }
            write!(f, "{}", ((r / RES_CAP).min(1.0).sqrt() * 15.0).round() as u8).unwrap();
        }
        if !clip {
            write!(f, "],\"soil\":[").unwrap();
            for (i, s) in food.soil.iter().enumerate() {
                if i > 0 {
                    f.write_all(b",").unwrap();
                }
                write!(f, "{}", ((1.0 + s).ln() * 4.0).round().min(15.0) as u8).unwrap();
            }
        }
        write!(f, "],\"patches\":[").unwrap();
        for (k, &(x, y)) in patches.centers.iter().enumerate() {
            if k > 0 {
                f.write_all(b",").unwrap();
            }
            write!(f, "[{x},{y},{}]", patches.sigma_of(k)).unwrap();
        }
        write!(f, "],\"agents\":[").unwrap();
        let mut first = true;
        for a in agents.iter().filter(|a| a.alive) {
            if !first {
                f.write_all(b",").unwrap();
            }
            first = false;
            let next_id = self.ids.len() as u32;
            let id = *self.ids.entry(a.body.cells).or_insert_with(|| {
                writeln!(self.bodies, "{{\"id\":{next_id},\"cells\":\"{}\"}}", cells_str(&a.body.cells)).unwrap();
                next_id
            });
            write!(f, "[{},{},{id},{},{},{}]", a.x, a.y, a.diet_class(), a.lineage, a.facing).unwrap();
        }
        writeln!(f, "]}}").unwrap();
    }
}

fn mean_std(vals: impl Iterator<Item = f32> + Clone) -> (f32, f32) {
    let n = vals.clone().count().max(1) as f32;
    let mean = vals.clone().sum::<f32>() / n;
    let var = vals.map(|v| (v - mean) * (v - mean)).sum::<f32>() / n;
    (mean, var.sqrt())
}

fn main() {
    let args: Vec<String> = std::env::args().collect();
    let steps: u64 = args.get(1).and_then(|s| s.parse().ok()).unwrap_or(1_000_000);
    let seed: u64 = args.get(2).and_then(|s| s.parse().ok()).unwrap_or(1);
    let size: usize = args.get(3).and_then(|s| s.parse().ok()).unwrap_or(128);
    // Patch widths, a comma-separated list: patch k has the k-th width, cycling. "8,1" is one
    // world with both kinds of place; "8" is e010's world, "1" is e011's width 1.
    // A width of 0 (alone) makes the sun uniform.
    let sigmas: Vec<f32> = args.get(4).map(String::as_str).unwrap_or("8,1").split(',').map(|s| s.parse().expect("patch width")).collect();
    assert!(!sigmas.is_empty() && sigmas.len() <= N_PLACES, "one or two patch widths");
    assert!(sigmas[0] > 0.0 || sigmas.len() == 1, "a uniform sun is one place");
    // What a cell is made of: paid to build it, food when the body dies (0.02 by default).
    let cell_energy: f32 = args.get(5).and_then(|s| s.parse().ok()).unwrap_or(CELL_ENERGY);
    // Matter per cell at the start: plants up to the cap, the rest soil (the cap by default:
    // e017's start).
    let matter0: f32 = args.get(6).and_then(|s| s.parse().ok()).unwrap_or(RES_CAP);
    let sigma_name = sigmas.iter().map(|s| format!("{s}")).collect::<Vec<_>>().join("-");
    let cap = RES_CAP;
    let sexual = true;
    let d = D;
    let g = Grid::new(size, size);
    let (w, h) = (g.w, g.h);
    let mut rng = Rng(seed.wrapping_mul(0x9E3779B97F4A7C15) | 1);
    let laws = Laws::new(&mut rng);
    let mut patches = Patches::new(g, seed, sigmas.clone());
    let init_pop = (INIT_POP_PER_CELL * (w * h) as f32).round() as usize;
    let cell_tag = if cell_energy == CELL_ENERGY { String::new() } else { format!("-cell{cell_energy}") };
    let matter_tag = if matter0 == RES_CAP { String::new() } else { format!("-m{matter0}") };
    let prefix = format!("experiments/e018_closed_cycle/results/{size}_sigma{sigma_name}{cell_tag}{matter_tag}_seed{seed}");
    let open = |name: &str| std::io::BufWriter::new(std::fs::File::create(format!("{prefix}_{name}")).unwrap());
    let mut log = open("log.csv");
    let mut snaps = Snapshots { long: open("long.jsonl"), clip: open("clip.jsonl"), bodies: open("bodies.jsonl"), ids: HashMap::new() };
    // The soil and the plants of every cell, every AGENT_DUMP_INTERVAL, at two decimals (the
    // long frames carry the soil on a coarse log scale, for the viewer).
    let mut soil_jsonl = open("soil.jsonl");

    // A place is named by its width in the output (0: beyond every patch).
    let place_name = |p: u8| if p == NO_PLACE { 0.0 } else { sigmas[p as usize] };
    let mut agents_csv = open("agents.csv");
    // bite: force behind a hard tip on the front; bite_any: on any side. shell_front, shell_back,
    // shell_side: mean hardness of the touchable tips on that side (side: left and right together).
    // foot: world cells under the body's cells; len_fwd / len_side: cells the body spans along / across the facing.
    writeln!(agents_csv, "step,mass,born_mass,hard,muscle,sensor,digestive,bite,shell,open,speed,age,energy,plant,meat,lineage,place,born_place,bite_any,shell_front,shell_back,shell_side,foot,len_fwd,len_side").unwrap();
    let mut events = open("events.csv");
    writeln!(events, "step,event,lineage,other,size").unwrap(); // other: parent of a split, target of a merge
    let mut lineages_csv = open("lineages.csv");
    // p0, p1: members in the first and second kind of place (by the width list); pnone: beyond every patch.
    writeln!(lineages_csv, "step,lineage,size,mass,hard,muscle,sensor,digestive,bite,shell,open,bodies,age,plant,meat,p0,p1,pnone,bite_any,shell_front,shell_back,shell_side,foot,len_fwd,len_side").unwrap();
    let mut dist_csv = open("dist.csv");
    writeln!(dist_csv, "step,measure,value,count").unwrap();
    // Per place, every LOG_INTERVAL: the population and body means of the agents standing there,
    // the share of its cells covered by bodies, the intake eaten there, the lineages present,
    // and the movers (born in the other kind of place).
    let mut places_csv = open("places.csv");
    writeln!(places_csv, "step,place,pop,mass,hard,muscle,sensor,digestive,bite,shell,biters,cover,plant_intake,meat_intake,lineages,movers,foot,shell_front,shell_back,dead,carrion,soil,barren,regrowth,cells").unwrap();

    let mut food = Food { res: vec![matter0.min(cap); w * h], carrion: vec![0.0; w * h], soil: vec![(matter0 - cap).max(0.0); w * h] };
    let mut next_id = 0u64;
    // Occupancy per sub-cell: the index of the body holding it (u32::MAX: none), kept current
    // by every move, turn, break, birth and death, and relabeled when the list of bodies is
    // compacted at the end of a step.
    let mut occ = Occ { sub: vec![u32::MAX; g.sw * g.sh], crowd: vec![0; w * h] };
    let mut agents: Vec<Agent> = Vec::with_capacity(init_pop);
    for _ in 0..init_pop {
        let genome: Vec<u8> = (0..N).map(|_| rng.below(4) as u8).collect();
        let genes = parse_genes(&genome);
        let body = develop_genes(&genes, &laws);
        next_id += 1;
        let facing = rng.below(4) as u8;
        let mut a = Agent {
            id: next_id - 1, lineage: 0, x: 0, y: 0, energy: INIT_ENERGY, age: 0, plant: 0.0, meat: 0.0, born_mass: body.mass, born_place: NO_PLACE,
            alive: body.mass > 0, keys: sorted_keys(&genes), gene_ids: genes.iter().map(Gene::key).collect(), genome, body, facing,
            wcells: [0; CELLS], tips: [[Tip::default(); SIDE]; 4], filled: [0; CELLS], n_filled: 0, bbox: [0; 4],
        };
        a.reframe();
        if !a.alive {
            continue;
        }
        // A random sub-cell with room for the body; a body that finds none in eight tries is not made.
        for _ in 0..8 {
            a.x = rng.below(g.sw);
            a.y = rng.below(g.sh);
            if a.fits(g, &occ.sub, u32::MAX, NORTH, 0) {
                a.born_place = patches.place[a.here(g)];
                occ.claim(g, &a, agents.len() as u32);
                agents.push(a);
                break;
            }
        }
    }
    // Bodies by ordered gene list. The body is a pure function of the list (same list, same
    // floating point order, same body), so a child whose list any living agent already has is not
    // developed again. Entries are dropped when nobody living carries the list.
    let mut cache: HashMap<Vec<u16>, Body> = agents.iter().map(|a| (a.gene_ids.clone(), a.body.clone())).collect();
    let mut develops = 0u64;
    // Threads for development (EVLOG_THREADS; default: all cores). Runs sharing a machine should
    // split the cores between them: the total work is the same, threads only shorten one run.
    let threads: usize = std::env::var("EVLOG_THREADS").ok().and_then(|s| s.parse().ok()).unwrap_or_else(|| std::thread::available_parallelism().map(|n| n.get()).unwrap_or(1)).max(1);
    let mut next_lineage = 1u32;
    let mut seen: HashMap<u32, u32> = HashMap::new(); // id -> detections in a row as a group
    let mut origin: HashMap<u32, u32> = HashMap::new(); // provisional id -> id it split from (0 = none)
    let mut lineages: HashMap<u32, usize> = HashMap::new(); // confirmed id -> size at the last detection

    writeln!(
        log,
        "step,pop,mean_energy,mean_res,mean_genes,births,deaths_energy,deaths_age,deaths_broken,deaths_body,cells_broken,plant_intake,meat_intake,\
         stay,forward,left,right,steps_per_sec,mass_mean,mass_std,hard_mean,hard_std,muscle_mean,muscle_std,sensor_mean,sensor_std,\
         digestive_mean,digestive_std,bite_mean,bite_std,speed_mean,speed_std,distinct_bodies,top_body_share,\
         diet_plants,diet_mixed,diet_meat,diet_none,births_with_neighbor,sexual_births,lineages,top_lineage_share,no_lineage_share,\
         sensor_agents_share,sense_decisions,sense_used,res_std,res_above_half,regrowth,develops,\
         prey_age_mean,meat_per_cell,kills_young_share,meat_majority,contacts,shell_mean,open_mean,full_share,damaged_share,biters_share,\
         mass_p10,mass_p50,mass_p90,mass_max,occupied_cells,cover,wasted,intake_per_gut,crossers,pop_none,\
         blocked,shoves,turns_blocked,births_no_room,foot_mean,len_fwd,len_side,bite_any_mean,biters_any_share,shell_front,shell_back,shell_side,pushes,move_spent,shaded,dead,carrion,soil,matter,barren,rot,spent"
    )
    .unwrap();

    let mut births = 0u64;
    let mut sexual_births = 0u64;
    let mut births_with_neighbor = 0u64;
    let mut births_no_room = 0u64; // children not born for want of a free cell next to the parent
    let mut deaths = [0u64; 4]; // energy, age, broken (no cells left), body (born without cells)
    let mut cc = Counters::default(); // the contact physics
    let mut plant_intake = 0.0f32;
    let mut plant_at = [0.0f32; N_PLACES + 1]; // intake by the place of the eater
    let mut actions = [0u64; N_OUT];
    let mut moves_tried = 0u64; // forward actions
    let mut blocked = 0u64; // of those, moves that did not happen (the way stayed taken)
    let mut shoves = 0u64; // bodies moved by a push
    let mut pushes = 0u64; // forward actions that pressed on at least one body
    let mut move_spent = 0.0f64; // energy paid for moving, summed over the log interval
    let mut turns_blocked = 0u64; // turns that did not happen (no room for the turned body)
    let mut sense_decisions = 0u64; // moves decided by an agent with at least one sensor block
    let mut sense_used = 0u64; // of those, moves that differ from what the agent would do with sense = 0
    let mut regrowth = 0.0f64; // food actually added (the cap wastes the rest), summed over the log interval
    let mut wasted = 0.0f64; // regrowth lost to the cap (a full cell does not grow)
    let mut shaded = 0.0f64; // regrowth lost to bodies standing on cells (a plant under a body does not grow)
    let mut barren = 0.0f64; // regrowth lost for want of soil
    let mut barren_at = [0.0f64; N_PLACES + 1];
    let mut regrowth_at = [0.0f64; N_PLACES + 1];
    let mut rot = 0.0f64; // dead matter returned to the soil
    let mut spent = 0.0f64; // what living bodies returned to the soil (upkeep and the work of moving)
    let mut last_time = std::time::Instant::now();

    for step in 1..=steps {
        if step % PATCH_DRIFT == 0 {
            patches.drift(g);
        }
        // The dead rot into the soil and the plants grow out of it: by at most the sun, not
        // above the cap (dead matter can lie above it, and then nothing grows), and not on a
        // cell held by a body (e016).
        for c in 0..w * h {
            let r = food.regrow(c, patches.grow[c], occ.crowd[c] > 0, cap);
            let p = patches.place[c] as usize;
            regrowth += r.added as f64;
            regrowth_at[p] += r.added as f64;
            shaded += r.shaded as f64;
            wasted += r.wasted as f64;
            barren += r.barren as f64;
            barren_at[p] += r.barren as f64;
            rot += r.rot as f64;
        }
        // The world cells the body would newly lie over after moving k world cells in
        // direction d (those under its box moved k * SUB sub-cells, less those under it now
        // and, for k = 2, one cell before): the food there and the crowd (sub-cells held by
        // bodies, in world cells) there.
        let look = |a: &Agent, d: usize, k: usize, res: &[f32], occ: &Occ| -> (f32, f32) {
            let now = a.under(g, NORTH, 0);
            let before = if k > 1 { a.under(g, d, SUB) } else { now };
            let mut food = 0.0;
            let mut others = 0.0;
            for c in a.under(g, d, k * SUB).iter() {
                if now.contains(c) || before.contains(c) {
                    continue;
                }
                food += res[c];
                others += occ.crowd[c] as f32 / SUB_CELLS as f32;
            }
            (food, others)
        };

        let mut newborn = Vec::new();
        let mut pending: Vec<(Agent, Option<Vec<Gene>>, usize)> = Vec::new(); // child, genes to develop, parent
        for i in 0..agents.len() {
            if !agents[i].alive {
                continue;
            }

            // 1. Eat: each digestive cell eats from the world cell under it, plant and dead
            //    matter alike (the dead matter's share is a measure).
            let a = &mut agents[i];
            a.age += 1;
            let mass = a.body.mass as f32;
            let mut eaten = 0.0;
            let mut dead_eaten = 0.0;
            let mut guts = Cells9::default();
            let mut gut_n = [0u8; 9];
            for p in a.cells_held() {
                if a.wcells[p] == DIGESTIVE as u8 {
                    let (sx, sy) = a.sub_at(g, p, NORTH, 0);
                    let c = g.wcell(sx, sy);
                    guts.add(c);
                    gut_n[guts.c[..guts.n].iter().position(|&x| x == c).unwrap()] += 1;
                }
            }
            for (k, c) in guts.iter().enumerate() {
                let e = food.res[c].min(BITE * gut_n[k] as f32);
                let (plant, dead) = food.take(c, e);
                eaten += e;
                dead_eaten += dead;
                plant_at[patches.place[c] as usize] += plant;
                cc.meat_at[patches.place[c] as usize] += dead;
            }
            // Upkeep falls to the soil under the body: all of it, or what the body has left.
            let upkeep = (UPKEEP * mass + UPKEEP_BODY).min((a.energy + eaten).max(0.0));
            food.spend(a.here(g), upkeep);
            spent += upkeep as f64;
            a.energy += eaten - UPKEEP * mass - UPKEEP_BODY;
            a.plant += eaten - dead_eaten;
            a.meat += dead_eaten;
            plant_intake += eaten - dead_eaten;
            cc.meat_intake += dead_eaten;

            // 2. Decide: the world seen from the body. Food under it; food and bodies one cell
            //    ahead, behind, left, right (two cells, weighted by sense); energy.
            let a = &agents[i];
            let s = a.body.sense();
            let thr = a.body.threshold();
            let f = a.facing as usize;
            let dirs = [f, opposite(f), left_of(f), opposite(left_of(f))];
            let here: f32 = a.under(g, NORTH, 0).iter().map(|c| food.res[c]).sum();
            let mut input = [0.0f32; N_IN];
            let mut blind = [0.0f32; N_IN];
            input[0] = here;
            blind[0] = here;
            for (k, &d) in dirs.iter().enumerate() {
                let (food1, others1) = look(a, d, 1, &food.res, &occ);
                let (food2, others2) = look(a, d, 2, &food.res, &occ);
                input[1 + k] = food1 + s * food2;
                input[5 + k] = others1 + s * others2;
                blind[1 + k] = food1;
                blind[5 + k] = others1;
            }
            input[9] = a.energy / thr;
            blind[9] = a.energy / thr;
            let action = act(&a.body.policy, &input);
            actions[action] += 1;
            if s > 0.0 {
                sense_decisions += 1;
                if act(&a.body.policy, &blind) != action {
                    sense_used += 1;
                }
            }

            // 3. Act. Forward: one sub-cell along the facing. Every cell of the body whose next
            //    sub-cell is held by another body presses on it (the contact physics); a body
            //    still in the way is shoved one sub-cell if the muscle pressing on it exceeds
            //    its mass and it has room; then the move happens if the way is clear, and a
            //    second sub-cell follows with probability speed if that way is clear too. The
            //    mover pays for the mass it moved (its own and what it shoved) times the
            //    distance; a forward action that moved nothing costs nothing. Turn: the grid
            //    rotates about its center; the turn happens if the sub-cells it would newly
            //    hold are free.
            if action == 1 {
                moves_tried += 1;
                let d = f;
                let pressed = push(&mut agents, i, d, g, &mut occ, &patches.place, &mut food, cell_energy, &mut cc);
                if agents[i].alive {
                    if !pressed.is_empty() {
                        pushes += 1;
                    }
                    let mut work = 0.0f32; // mass moved times sub-cells moved
                    for &(j, force) in &pressed {
                        if !agents[j].alive || agents[i].fits(g, &occ.sub, i as u32, d, 1) || force as u16 <= agents[j].body.mass as u16 {
                            continue;
                        }
                        if agents[j].fits(g, &occ.sub, j as u32, d, 1) {
                            occ.release(g, &agents[j]);
                            let (nx, ny) = g.sstep(agents[j].x, agents[j].y, d, 1);
                            agents[j].x = nx;
                            agents[j].y = ny;
                            occ.claim(g, &agents[j], j as u32);
                            shoves += 1;
                            work += agents[j].body.mass as f32;
                        }
                    }
                    let mut moved = 0;
                    if agents[i].fits(g, &occ.sub, i as u32, d, 1) {
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
                        blocked += 1;
                    }
                    work += agents[i].body.mass as f32 * moved as f32;
                    let cost = MOVE_COST * work;
                    // The work of moving falls to the soil under the body where it stands now.
                    let paid = cost.min(agents[i].energy.max(0.0));
                    food.spend(agents[i].here(g), paid);
                    spent += paid as f64;
                    agents[i].energy -= cost;
                    move_spent += cost as f64;
                }
            } else if action >= 2 {
                let nf = if action == 2 { left_of(f) } else { opposite(left_of(f)) };
                let a = &agents[i];
                let (list, n, _) = filled(&rotate(&a.body.cells, nf));
                if list[..n as usize].iter().all(|&p| {
                    let (sx, sy) = a.sub_at(g, p as usize, NORTH, 0);
                    let o = occ.sub[g.sidx(sx, sy)];
                    o == u32::MAX || o == i as u32
                }) {
                    occ.release(g, &agents[i]);
                    agents[i].facing = nf as u8;
                    agents[i].reframe();
                    occ.claim(g, &agents[i], i as u32);
                } else {
                    turns_blocked += 1;
                }
            }
            if !agents[i].alive {
                continue;
            }

            // 4. Reproduce. The parent pays (half of its energy goes to the child). In sexual
            //    mode it first looks for a mate within distance D among the bodies touching the
            //    ring around its 2x2 block; the child is a one-point crossover of the two
            //    genomes. Without a mate the child is a copy, as in e005. Then 2 point
            //    mutations. The child is placed once its body is known (below).
            if agents[i].energy >= thr {
                let mut mate = None;
                let mut neighbor = false;
                if sexual {
                    // Bodies within two sub-cells of the parent's box.
                    let a = &agents[i];
                    let [r0, r1, c0, c1] = a.bbox;
                    let (x0, y0) = (a.x + g.sw + c0 as usize - 2, a.y + g.sh + r0 as usize - 2);
                    'cells: for dy in 0..(r1 - r0 + 5) as usize {
                        for dx in 0..(c1 - c0 + 5) as usize {
                            let j = occ.sub[g.sidx((x0 + dx) % g.sw, (y0 + dy) % g.sh)];
                            if j == u32::MAX || j as usize == i {
                                continue;
                            }
                            let p = &agents[j as usize];
                            if p.alive {
                                neighbor = true;
                                if agents[i].distance(p) <= d {
                                    mate = Some(j as usize);
                                    break 'cells;
                                }
                            }
                        }
                    }
                }
                if neighbor {
                    births_with_neighbor += 1;
                }
                let mut genome = agents[i].genome.clone();
                if let Some(j) = mate {
                    let cut = rng.below(N);
                    genome[cut..].copy_from_slice(&agents[j].genome[cut..]);
                    sexual_births += 1;
                }
                let a = &mut agents[i];
                a.energy *= 0.5;
                for _ in 0..MUTATIONS_PER_CHILD {
                    let pos = rng.below(N);
                    genome[pos] = (genome[pos] + 1 + rng.below(3) as u8) % 4;
                }
                // The body is a function of the gene list alone. A mutation outside the genes
                // (most of them) gives the parent's body without developing it again.
                let genes = parse_genes(&genome);
                let gene_ids: Vec<u16> = genes.iter().map(Gene::key).collect();
                let body = cache.get(&gene_ids).cloned(); // the birth body of this gene list (the parent's may be damaged)
                next_id += 1;
                let keys = sorted_keys(&genes);
                let todo = body.is_none().then_some(genes);
                pending.push((Agent {
                    id: next_id - 1, lineage: a.lineage, x: a.x, y: a.y, energy: a.energy, age: 0, plant: 0.0, meat: 0.0, born_mass: 0, born_place: NO_PLACE, alive: true,
                    keys, gene_ids, genome, body: body.unwrap_or_else(|| Body::new([0; CELLS], [0.0; N_POLICY], 0)), facing: rng.below(4) as u8,
                    wcells: [0; CELLS], tips: [[Tip::default(); SIDE]; 4], filled: [0; CELLS], n_filled: 0, bbox: [0; 4],
                }, todo, i));
            }
        }
        // Develop the children with a new gene list, one development per distinct list, on all
        // cores. The children keep their birth order, so the result is the same as developing
        // them one by one in the loop.
        let mut jobs: Vec<(&[u16], &[Gene])> = Vec::new();
        for (a, genes, _) in &pending {
            if let Some(g) = genes {
                if !jobs.iter().any(|(k, _)| *k == a.gene_ids.as_slice()) {
                    jobs.push((&a.gene_ids, g));
                }
            }
        }
        develops += jobs.len() as u64;
        let mut developed: Vec<Body> = Vec::with_capacity(jobs.len());
        let n_threads = threads.min(jobs.len() / 2); // at least two developments per thread
        if n_threads < 2 {
            developed.extend(jobs.iter().map(|(_, g)| develop_genes(g, &laws)));
        } else {
            let chunk = jobs.len().div_ceil(n_threads);
            let laws = &laws;
            let parts: Vec<Vec<Body>> = std::thread::scope(|sc| {
                let handles: Vec<_> = jobs.chunks(chunk).map(|c| sc.spawn(move || c.iter().map(|(_, g)| develop_genes(g, laws)).collect::<Vec<Body>>())).collect();
                handles.into_iter().map(|h| h.join().unwrap()).collect()
            });
            developed.extend(parts.into_iter().flatten());
        }
        for ((k, _), b) in jobs.iter().zip(developed) {
            cache.insert(k.to_vec(), b);
        }
        // Place each child: the first anchor where its cells find free sub-cells, one to eight
        // sub-cells (two world cells) from the parent's anchor in the four directions (from a
        // random one). Without room the child is lost with the energy the parent gave it (as
        // a child born without cells, e013).
        for (mut a, genes, parent) in pending.drain(..) {
            if genes.is_some() {
                a.body = cache[&a.gene_ids].clone();
            }
            a.born_mass = a.body.mass;
            a.alive = a.body.mass > 0;
            if !a.alive {
                deaths[3] += 1;
                newborn.push(a);
                continue;
            }
            a.reframe();
            let (px, py) = (agents[parent].x, agents[parent].y);
            let start = rng.below(4);
            let mut spot = None;
            'search: for t in 0..4 {
                let d = DIRS[(start + t) % 4];
                for k in 1..=2 * SUB {
                    let (cx, cy) = g.sstep(px, py, d, k);
                    a.x = cx;
                    a.y = cy;
                    if a.fits(g, &occ.sub, u32::MAX, NORTH, 0) {
                        spot = Some((cx, cy));
                        break 'search;
                    }
                }
            }
            match spot {
                Some((cx, cy)) => {
                    a.x = cx;
                    a.y = cy;
                    a.born_place = patches.place[a.here(g)];
                    occ.claim(g, &a, (agents.len() + newborn.len()) as u32);
                    agents[parent].energy -= cell_energy * a.body.mass as f32; // the matter of the child's body
                    newborn.push(a);
                }
                None => {
                    // The child is never made; what the parent gave it lies where the parent stands.
                    births_no_room += 1;
                    food.lay(g.wcell(px, py), a.energy, &patches.place, &mut cc);
                }
            }
        }
        births += newborn.len() as u64;
        agents.append(&mut newborn);
        // The dead leave their sub-cells; the list is compacted and the survivors relabeled.
        for a in agents.iter_mut() {
            let dead = if !a.alive {
                true
            } else if a.energy <= 0.0 {
                deaths[0] += 1;
                true
            } else if a.age > MAX_AGE {
                deaths[1] += 1;
                true
            } else {
                false
            };
            if dead {
                occ.release(g, a);
                a.alive = false;
                lay_body(a, g, &mut food, &patches.place, cell_energy, &mut cc);
            }
        }
        agents.retain(|a| a.alive);
        for (i, a) in agents.iter().enumerate() {
            occ.relabel(g, a, i as u32);
        }

        if step % LINEAGE_INTERVAL == 0 {
            let live: std::collections::HashSet<&[u16]> = agents.iter().map(|a| a.gene_ids.as_slice()).collect();
            cache.retain(|k, _| live.contains(k.as_slice()));
        }
        // Lineages: groups connected by possible mating (single linkage at distance D).
        if step % LINEAGE_INTERVAL == 0 {
            let n = agents.len();
            let mut parent: Vec<usize> = (0..n).collect();
            fn find(p: &mut Vec<usize>, mut i: usize) -> usize {
                while p[i] != i {
                    p[i] = p[p[i]];
                    i = p[i];
                }
                i
            }
            // Agents with the same gene list are at distance 0, so one representative per list is
            // enough: link the representatives, then attach the copies. Same groups as all pairs.
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
                    if agents[i].distance(&agents[j]) <= d {
                        let (ri, rj) = (find(&mut parent, i), find(&mut parent, j));
                        if ri != rj {
                            parent[ri] = rj;
                        }
                    }
                }
            }
            let mut members: HashMap<usize, Vec<usize>> = HashMap::new();
            for i in 0..n {
                let r = find(&mut parent, i);
                members.entry(r).or_default().push(i);
            }
            let mut groups: Vec<Vec<usize>> = members.into_values().filter(|m| m.len() >= MIN_LINEAGE).collect();
            groups.sort_by_key(|m| (std::cmp::Reverse(m.len()), agents[m[0]].id));
            // Each group keeps the id most of its members inherited (confirmed ids first), unless a bigger group took it;
            // then it gets a provisional id. An id becomes a lineage (event: birth, or split from
            // the id it wanted) once its group has existed LINEAGE_CONFIRM detections in a row.
            // Members of groups smaller than MIN_LINEAGE keep their id. A lineage whose carriers
            // were all relabeled into another group has merged into it; one whose carriers all
            // died is extinct.
            let mut before: HashMap<u32, usize> = HashMap::new();
            for a in &agents {
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
                // A confirmed lineage id wins over a provisional one, so that a provisional group
                // that rejoins its lineage dissolves into it instead of renaming it.
                let best = |confirmed: bool| votes.iter().filter(|(id, _)| lineages.contains_key(id) == confirmed).max_by_key(|(id, c)| (**c, std::cmp::Reverse(**id))).map(|(id, _)| *id);
                let inherited = best(true).or_else(|| best(false)).unwrap_or(0);
                let id = if inherited != 0 && !now.contains_key(&inherited) {
                    inherited
                } else {
                    let id = next_lineage;
                    next_lineage += 1;
                    origin.insert(id, inherited);
                    id
                };
                now.insert(id, m.len());
                assigned.push((id, m));
            }
            seen.retain(|id, _| now.contains_key(id));
            let mut ids: Vec<u32> = now.keys().copied().collect();
            ids.sort_unstable(); // HashMap order differs between processes; the log should not
            for id in ids {
                let size = now[&id];
                let n = seen.entry(id).or_insert(0);
                *n += 1;
                if *n == LINEAGE_CONFIRM && !lineages.contains_key(&id) {
                    let from = origin.remove(&id).unwrap_or(0);
                    let event = if from == 0 { "birth" } else { "split" };
                    writeln!(events, "{step},{event},{id},{from},{size}").unwrap();
                    lineages.insert(id, size);
                }
            }
            let mut into: HashMap<(u32, u32), usize> = HashMap::new(); // (old id, new id) -> relabeled
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
                let sz = m.len() as f32;
                let mut kinds = [0.0f32; N_KINDS];
                let (mut mass, mut bite, mut shell, mut open) = (0.0f32, 0.0f32, 0.0f32, 0.0f32);
                let (mut age, mut plant, mut meat) = (0.0f32, 0.0f32, 0.0f32);
                let (mut bite_any, mut s_front, mut s_back, mut s_side, mut foot, mut long, mut wide) = (0.0f32, 0.0f32, 0.0f32, 0.0f32, 0.0f32, 0.0f32, 0.0f32);
                let mut bodies: HashMap<&[u8; CELLS], usize> = HashMap::new();
                let mut at = [0usize; N_PLACES + 1];
                for &i in m {
                    at[patches.place[agents[i].here(g)] as usize] += 1;
                    for k in 0..N_KINDS {
                        kinds[k] += agents[i].body.kinds[k] as f32;
                    }
                    let b = &agents[i].body;
                    mass += b.mass as f32;
                    bite += b.bite() as f32;
                    shell += b.shell();
                    open += b.open_lines() as f32;
                    bite_any += b.bite_any() as f32;
                    s_front += b.shell_side(NORTH);
                    s_back += b.shell_side(SOUTH);
                    s_side += 0.5 * (b.shell_side(EAST) + b.shell_side(WEST));
                    foot += agents[i].foot_n(g) as f32;
                    long += b.extent[0] as f32;
                    wide += b.extent[1] as f32;
                    age += agents[i].age as f32;
                    plant += agents[i].plant;
                    meat += agents[i].meat;
                    *bodies.entry(&agents[i].body.cells).or_insert(0) += 1;
                }
                writeln!(lineages_csv, "{step},{id},{},{:.1},{:.1},{:.1},{:.1},{:.1},{:.1},{:.2},{:.1},{},{:.0},{:.2},{:.2},{},{},{},{:.1},{:.2},{:.2},{:.2},{:.2},{:.2},{:.2}", m.len(), mass / sz,
                    kinds[HARD] / sz, kinds[MUSCLE] / sz, kinds[SENSOR] / sz, kinds[DIGESTIVE] / sz, bite / sz, shell / sz, open / sz, bodies.len(), age / sz, plant / sz, meat / sz,
                    at[0], at[1], at[N_PLACES], bite_any / sz, s_front / sz, s_back / sz, s_side / sz, foot / sz, long / sz, wide / sz).unwrap();
            }
            let mut carriers: HashMap<u32, usize> = HashMap::new();
            for a in &agents {
                *carriers.entry(a.lineage).or_default() += 1;
            }
            let mut gone: Vec<u32> = lineages.keys().filter(|id| !carriers.contains_key(id)).copied().collect();
            gone.sort();
            for id in gone {
                let size = lineages.remove(&id).unwrap();
                let target = into.iter().filter(|((old, _), _)| *old == id).max_by_key(|((_, new), c)| (**c, std::cmp::Reverse(*new)));
                match target {
                    Some(((_, new), _)) if before.get(&id).copied().unwrap_or(0) > 0 => {
                        writeln!(events, "{step},merge,{id},{new},{size}").unwrap();
                    }
                    _ => writeln!(events, "{step},extinct,{id},0,{size}").unwrap(),
                }
            }
            for (id, size) in &now {
                if let Some(s) = lineages.get_mut(id) {
                    *s = *size;
                }
            }
        }
        // Pairwise distance histograms over all living pairs, three measures.
        if step % DIST_INTERVAL == 0 {
            let mut h = [vec![0u64; N + 1], vec![0u64; 128], vec![0u64; CELLS + 1]];
            for i in 0..agents.len() {
                for j in i + 1..agents.len() {
                    let (a, b) = (&agents[i], &agents[j]);
                    h[0][hamming(&a.genome, &b.genome)] += 1;
                    h[1][gene_distance(&a.keys, &b.keys).min(127)] += 1;
                    h[2][a.body.cells.iter().zip(&b.body.cells).filter(|(x, y)| x != y).count()] += 1;
                }
            }
            for (name, hist) in ["hamming", "genes", "body"].iter().zip(&h) {
                for (v, &c) in hist.iter().enumerate() {
                    if c > 0 {
                        writeln!(dist_csv, "{step},{name},{v},{c}").unwrap();
                    }
                }
            }
        }
        if step % LONG_INTERVAL == 0 {
            snaps.write_frame(false, step, &food, &patches, &agents);
        }
        if step % AGENT_DUMP_INTERVAL == 0 {
            let list = |v: &[f32]| v.iter().map(|x| format!("{x:.2}")).collect::<Vec<_>>().join(",");
            writeln!(soil_jsonl, "{{\"step\":{step},\"soil\":[{}],\"plant\":[{}]}}", list(&food.soil), list(&food.res)).unwrap();
            for a in &agents {
                let k = &a.body.kinds;
                let b = &a.body;
                writeln!(agents_csv, "{step},{},{},{},{},{},{},{},{:.2},{},{:.3},{},{:.2},{:.2},{:.2},{},{},{},{},{:.2},{:.2},{:.2},{},{},{}",
                    b.mass, a.born_mass, k[HARD], k[MUSCLE], k[SENSOR], k[DIGESTIVE], b.bite(), b.shell(), b.open_lines(), b.speed(), a.age, a.energy, a.plant, a.meat, a.lineage,
                    place_name(patches.place[a.here(g)]), place_name(a.born_place), b.bite_any(), b.shell_side(NORTH), b.shell_side(SOUTH), 0.5 * (b.shell_side(EAST) + b.shell_side(WEST)),
                    a.foot_n(g), b.extent[0], b.extent[1]).unwrap();
            }
        }
        if step >= CLIP_START && step < CLIP_START + CLIP_LEN {
            snaps.write_frame(true, step, &food, &patches, &agents);
        }

        if step % LOG_INTERVAL == 0 || agents.is_empty() {
            let now = std::time::Instant::now();
            let sps = LOG_INTERVAL as f64 / (now - last_time).as_secs_f64();
            last_time = now;
            let pop = agents.len().max(1) as f32;
            let mean_energy = agents.iter().map(|a| a.energy).sum::<f32>() / pop;
            let mean_res = food.res.iter().sum::<f32>() / (w * h) as f32;
            let mean_genes = agents.iter().map(|a| a.body.n_genes as f32).sum::<f32>() / pop;
            let total_actions = actions.iter().sum::<u64>().max(1) as f64;
            write!(
                log,
                "{step},{},{mean_energy:.3},{mean_res:.3},{mean_genes:.2},{births},{},{},{},{},{},{plant_intake:.1},{:.1}",
                agents.len(),
                deaths[0],
                deaths[1],
                cc.kills,
                deaths[3],
                cc.cells_broken,
                cc.meat_intake
            )
            .unwrap();
            for a in actions {
                write!(log, ",{:.3}", a as f64 / total_actions).unwrap();
            }
            write!(log, ",{sps:.0}").unwrap();
            let (m, s) = mean_std(agents.iter().map(|a| a.body.mass as f32));
            write!(log, ",{m:.2},{s:.2}").unwrap();
            for k in [HARD, MUSCLE, SENSOR, DIGESTIVE] {
                let (m, s) = mean_std(agents.iter().map(|a| a.body.kinds[k] as f32));
                write!(log, ",{m:.2},{s:.2}").unwrap();
            }
            let (m, s) = mean_std(agents.iter().map(|a| a.body.bite() as f32));
            write!(log, ",{m:.2},{s:.2}").unwrap();
            let (m, s) = mean_std(agents.iter().map(|a| a.body.speed()));
            write!(log, ",{m:.3},{s:.3}").unwrap();
            let mut counts: HashMap<&[u8; CELLS], usize> = HashMap::new();
            for a in &agents {
                *counts.entry(&a.body.cells).or_insert(0) += 1;
            }
            let top = counts.values().max().copied().unwrap_or(0) as f32 / pop;
            write!(log, ",{},{top:.3}", counts.len()).unwrap();
            let mut diet = [0usize; 4];
            for a in &agents {
                diet[a.diet_class()] += 1;
            }
            for d in diet {
                write!(log, ",{:.3}", d as f32 / pop).unwrap();
            }
            let mut carriers: HashMap<u32, usize> = HashMap::new();
            for a in &agents {
                *carriers.entry(a.lineage).or_default() += 1;
            }
            let top_lineage = lineages.keys().map(|id| carriers.get(id).copied().unwrap_or(0)).max().unwrap_or(0) as f32 / pop;
            let no_lineage = agents.iter().filter(|a| !lineages.contains_key(&a.lineage)).count() as f32 / pop;
            let sensor_agents = agents.iter().filter(|a| a.body.kinds[SENSOR] > 0).count() as f32 / pop;
            let (_, res_std) = mean_std(food.res.iter().copied());
            let res_above_half = food.res.iter().filter(|&&r| r > 0.5 * cap).count() as f32 / (w * h) as f32;
            write!(log, ",{births_with_neighbor},{sexual_births},{},{top_lineage:.3},{no_lineage:.3},{sensor_agents:.3},{sense_decisions},{:.3},{res_std:.3},{res_above_half:.3},{:.2},{develops}",
                lineages.len(), if sense_decisions > 0 { sense_used as f64 / sense_decisions as f64 } else { 0.0 }, regrowth / LOG_INTERVAL as f64).unwrap();
            // Deaths by damage in this window: mean age, share before YOUNG. Energy per broken
            // cell. Agents that got most of their food from other bodies. And shape: mean shell
            // hardness, open lines, full squares, damaged bodies, bodies with a bite.
            let kills = cc.kills.max(1) as f64;
            let meat_majority = agents.iter().filter(|a| a.meat > a.plant && a.meat > 0.0).count() as f32 / pop;
            let shell_mean = agents.iter().map(|a| a.body.shell()).sum::<f32>() / pop;
            let open_mean = agents.iter().map(|a| a.body.open_lines() as f32).sum::<f32>() / pop;
            let full = agents.iter().filter(|a| a.body.mass as usize == CELLS).count() as f32 / pop;
            let damaged = agents.iter().filter(|a| a.body.mass < a.born_mass).count() as f32 / pop;
            let biters = agents.iter().filter(|a| a.body.bite() > 0).count() as f32 / pop;
            write!(log, ",{:.0},{:.3},{:.3},{meat_majority:.3},{},{shell_mean:.2},{open_mean:.2},{full:.3},{damaged:.3},{biters:.3}",
                cc.prey_age as f64 / kills, cc.meat_intake as f64 / cc.cells_broken.max(1) as f64, cc.kills_young as f64 / kills, cc.contacts).unwrap();
            // Size distribution (quantiles of mass), space (cells covered, share of the world
            // covered), regrowth lost to the cap, and plant intake per digestive cell per step.
            let mut masses: Vec<u8> = agents.iter().map(|a| a.body.mass).collect();
            masses.sort_unstable();
            let q = |f: f32| masses.get(((masses.len() - 1) as f32 * f) as usize).copied().unwrap_or(0);
            // Space: sub-cells held (occupied_cells) and their share of the world (cover), and
            // per place the sub-cells held there over the sub-cells of the place.
            let covered = occ.crowd.iter().map(|&c| c as usize).sum::<usize>();
            let mut place_cells = [0usize; N_PLACES + 1];
            let mut place_held = [0usize; N_PLACES + 1];
            for (c, &p) in patches.place.iter().enumerate() {
                place_cells[p as usize] += SUB_CELLS;
                place_held[p as usize] += occ.crowd[c] as usize;
            }
            let guts = agents.iter().map(|a| a.body.kinds[DIGESTIVE] as f64).sum::<f64>().max(1.0);
            // Crossers: agents standing in a kind of place other than the one they were born in
            // (both a patch; a body beyond every patch is on its way). Then the same measures per place.
            let place_of = |a: &Agent| patches.place[a.here(g)];
            let crossers = agents.iter().filter(|a| { let p = place_of(a); p != NO_PLACE && a.born_place != NO_PLACE && p != a.born_place }).count() as f32 / pop;
            let pop_none = agents.iter().filter(|a| place_of(a) == NO_PLACE).count();
            write!(log, ",{},{},{},{},{covered},{:.3},{:.2},{:.4},{crossers:.3},{pop_none}", q(0.1), q(0.5), q(0.9), masses.last().copied().unwrap_or(0),
                covered as f32 / (g.sw * g.sh) as f32, wasted / LOG_INTERVAL as f64, plant_intake as f64 / LOG_INTERVAL as f64 / guts).unwrap();
            // Facing and space: blocked moves and shoves per forward action, blocked turns per
            // turn action, births without room per birth; the footprint and extent; the front.
            let tried = moves_tried.max(1) as f64;
            let turns = (actions[2] + actions[3]).max(1) as f64;
            let mean = |f: &dyn Fn(&Agent) -> f32| agents.iter().map(|a| f(a)).sum::<f32>() / pop;
            write!(log, ",{:.3},{:.3},{:.3},{:.3},{:.2},{:.2},{:.2},{:.2},{:.3},{:.2},{:.2},{:.2}",
                blocked as f64 / tried, shoves as f64 / tried, turns_blocked as f64 / turns, births_no_room as f64 / (births + births_no_room).max(1) as f64,
                mean(&|a| a.foot_n(g) as f32), mean(&|a| a.body.extent[0] as f32), mean(&|a| a.body.extent[1] as f32),
                mean(&|a| a.body.bite_any() as f32), mean(&|a| (a.body.bite_any() > 0) as u8 as f32),
                mean(&|a| a.body.shell_side(NORTH)), mean(&|a| a.body.shell_side(SOUTH)), mean(&|a| 0.5 * (a.body.shell_side(EAST) + a.body.shell_side(WEST)))).unwrap();
            // The cost law: pushes per forward action and the energy paid for moving per body per step.
            // Matter: dead matter laid per step and the dead matter lying uneaten now.
            let carrion_stock = food.carrion.iter().map(|&c| c as f64).sum::<f64>();
            let mut carrion_at = [0.0f64; N_PLACES + 1];
            for (c, &p) in patches.place.iter().enumerate() {
                carrion_at[p as usize] += food.carrion[c] as f64;
            }
            // The closed cycle: matter in the soil, the total (soil, plants, dead matter, bodies:
            // energy and cells), regrowth lost for want of soil, dead matter rotted into the
            // soil and what bodies returned to it, per step.
            let soil_stock = food.soil.iter().map(|&s| s as f64).sum::<f64>();
            let mut soil_at = [0.0f64; N_PLACES + 1];
            let mut cells_at = [0usize; N_PLACES + 1];
            for (c, &p) in patches.place.iter().enumerate() {
                soil_at[p as usize] += food.soil[c] as f64;
                cells_at[p as usize] += 1;
            }
            let in_bodies = agents.iter().map(|a| a.energy.max(0.0) as f64 + cell_energy as f64 * a.body.mass as f64).sum::<f64>();
            let matter = soil_stock + food.res.iter().map(|&r| r as f64).sum::<f64>() + in_bodies;
            writeln!(log, ",{:.3},{:.5},{:.2},{:.4},{:.2},{soil_stock:.1},{matter:.1},{:.3},{:.4},{:.3}", pushes as f64 / tried, move_spent / LOG_INTERVAL as f64 / pop as f64, shaded / LOG_INTERVAL as f64,
                cc.dead / LOG_INTERVAL as f64, carrion_stock, barren / LOG_INTERVAL as f64, rot / LOG_INTERVAL as f64, spent / LOG_INTERVAL as f64).unwrap();
            for p in 0..=N_PLACES as u8 {
                if p < NO_PLACE && p as usize >= sigmas.len() {
                    continue;
                }
                let here: Vec<&Agent> = agents.iter().filter(|a| place_of(a) == p).collect();
                let n = here.len().max(1) as f32;
                let mean = |f: &dyn Fn(&Agent) -> f32| here.iter().map(|a| f(a)).sum::<f32>() / n;
                let present: std::collections::HashSet<u32> = here.iter().map(|a| a.lineage).filter(|l| lineages.contains_key(l)).collect();
                let movers = here.iter().filter(|a| a.born_place != NO_PLACE && a.born_place != p).count();
                writeln!(places_csv, "{step},{},{},{:.2},{:.2},{:.2},{:.2},{:.2},{:.2},{:.2},{:.3},{:.3},{:.1},{:.1},{},{movers},{:.2},{:.2},{:.2},{:.4},{:.2},{:.1},{:.4},{:.4},{}", place_name(p), here.len(),
                    mean(&|a| a.body.mass as f32), mean(&|a| a.body.kinds[HARD] as f32), mean(&|a| a.body.kinds[MUSCLE] as f32), mean(&|a| a.body.kinds[SENSOR] as f32),
                    mean(&|a| a.body.kinds[DIGESTIVE] as f32), mean(&|a| a.body.bite() as f32), mean(&|a| a.body.shell()), mean(&|a| (a.body.bite() > 0) as u8 as f32),
                    place_held[p as usize] as f32 / place_cells[p as usize].max(1) as f32, plant_at[p as usize], cc.meat_at[p as usize], present.len(),
                    mean(&|a| a.foot_n(g) as f32), mean(&|a| a.body.shell_side(NORTH)), mean(&|a| a.body.shell_side(SOUTH)),
                    cc.dead_at[p as usize] / LOG_INTERVAL as f64, carrion_at[p as usize], soil_at[p as usize], barren_at[p as usize] / LOG_INTERVAL as f64,
                    regrowth_at[p as usize] / LOG_INTERVAL as f64, cells_at[p as usize]).unwrap();
            }
            plant_at = [0.0; N_PLACES + 1];
            cc = Counters::default();
            births = 0;
            sexual_births = 0;
            births_with_neighbor = 0;
            births_no_room = 0;
            deaths = [0; 4];
            plant_intake = 0.0;
            actions = [0; N_OUT];
            moves_tried = 0;
            blocked = 0;
            shoves = 0;
            pushes = 0;
            move_spent = 0.0;
            turns_blocked = 0;
            sense_decisions = 0;
            sense_used = 0;
            regrowth = 0.0;
            wasted = 0.0;
            shaded = 0.0;
            barren = 0.0;
            barren_at = [0.0; N_PLACES + 1];
            regrowth_at = [0.0; N_PLACES + 1];
            rot = 0.0;
            spent = 0.0;
            develops = 0;
            if agents.is_empty() {
                eprintln!("extinct at step {step}");
                break;
            }
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn rotation_is_a_bijection_and_turns_the_front() {
        for f in DIRS {
            for i in 0..CELLS {
                assert_eq!(to_body(to_world(i, f), f), i);
            }
        }
        // A tooth: a hard tip in the front row with muscle behind it, in column 2.
        let mut cells = [0u8; CELLS];
        cells[2] = HARD as u8;
        cells[SIDE + 2] = MUSCLE as u8;
        cells[2 * SIDE + 2] = MUSCLE as u8;
        let b = Body::new(cells, [0.0; N_POLICY], 0);
        assert_eq!(b.bite(), 2);
        assert_eq!(b.tips[NORTH][2].hardness, HARDNESS);
        // Facing east, the tooth is on the world's east side, in row 2 (the body's left is north).
        let w = rotate(&cells, EAST);
        let t = tips_of(&w);
        assert_eq!(t[EAST][2].hardness, HARDNESS);
        assert_eq!(t[EAST][2].force, 2);
        assert_eq!(t[NORTH][2].hardness, 0);
        // Facing south: on the south side, column 5 (mirrored).
        let t = tips_of(&rotate(&cells, SOUTH));
        assert_eq!(t[SOUTH][5].hardness, HARDNESS);
        // Facing west: the west side, row 5.
        let t = tips_of(&rotate(&cells, WEST));
        assert_eq!(t[WEST][5].hardness, HARDNESS);
        // The tooth spans three rows along the facing and one across.
        assert_eq!(b.extent, [3, 1]);
        // The face of the hard tip, seen from the front: one hard cell behind it; the muscle
        // behind the tip is soft (1) and the tip's face from the side is hard too.
        assert_eq!(face_hardness(&cells, 2, SOUTH), HARDNESS);
        assert_eq!(face_hardness(&cells, SIDE + 2, SOUTH), 1);
        cells[SIDE + 2] = HARD as u8;
        assert_eq!(face_hardness(&cells, 2, SOUTH), 2 * HARDNESS);
        assert_eq!(face_hardness(&cells, SIDE + 2, NORTH), 2 * HARDNESS);
    }

    fn agent_with(cells: [u8; CELLS], x: usize, y: usize, facing: usize) -> Agent {
        let mut a = Agent {
            id: 0, lineage: 0, x, y, energy: 1.0, age: 0, plant: 0.0, meat: 0.0, born_mass: 0, born_place: NO_PLACE, alive: true,
            genome: Vec::new(), keys: Vec::new(), gene_ids: Vec::new(), body: Body::new(cells, [0.0; N_POLICY], 0), facing: facing as u8,
            wcells: [0; CELLS], tips: [[Tip::default(); SIDE]; 4], filled: [0; CELLS], n_filled: 0, bbox: [0; 4],
        };
        a.reframe();
        a
    }

    #[test]
    fn bodies_hold_their_own_sub_cells_and_lie_over_world_cells() {
        let g = Grid::new(8, 8);
        // A three-cell corner body (cells (0,0), (0,1), (1,0)) anchored at sub-cell (6, 6) facing north.
        let mut cells = [0u8; CELLS];
        cells[0] = DIGESTIVE as u8;
        cells[1] = DIGESTIVE as u8;
        cells[SIDE] = HARD as u8;
        let a = agent_with(cells, 6, 6, NORTH);
        assert_eq!(a.n_filled, 3);
        assert_eq!(a.bbox, [0, 1, 0, 1]);
        // It lies over world cells (1,1), (1,2)... no: sub-cells (6,6), (7,6), (6,7) are all in world cell (1,1).
        assert_eq!(a.foot_n(g), 1);
        let under = a.under(g, NORTH, 0);
        assert_eq!((under.n, under.c[0]), (1, g.idx(1, 1)));
        // One sub-cell east: (7,6), (8,6), (7,7): world cells (1,1) and (2,1).
        let b = agent_with(cells, 7, 6, NORTH);
        assert_eq!(b.foot_n(g), 2);
        assert_eq!(b.under(g, NORTH, 0).n, 2);
        // Moved one world cell east, the box lies over (2,1) and (3,1); the new cell is (3,1).
        let ahead = b.under(g, EAST, SUB);
        assert!(ahead.contains(g.idx(2, 1)) && ahead.contains(g.idx(3, 1)) && ahead.n == 2);
        // Occupancy: claim, fits, release.
        let mut occ = Occ { sub: vec![u32::MAX; g.sw * g.sh], crowd: vec![0; g.cells()] };
        occ.claim(g, &a, 0);
        assert_eq!(occ.crowd[g.idx(1, 1)], 3);
        assert_eq!(occ.sub[g.sidx(7, 6)], 0);
        assert!(a.fits(g, &occ.sub, 0, EAST, 1)); // its own cells do not block it
        assert!(!b.fits(g, &occ.sub, 1, NORTH, 0)); // another body cannot stand on it
        assert!(b.fits(g, &occ.sub, 1, EAST, 1)); // one sub-cell further east it can
        occ.release(g, &a);
        assert_eq!(occ.crowd[g.idx(1, 1)], 0);
        // The torus: a body at the far east edge wraps.
        let c = agent_with(cells, g.sw - 1, 0, NORTH);
        assert_eq!(c.sub_at(g, 1, NORTH, 0), (0, 0));
        assert_eq!(c.foot_n(g), 2);
    }

    #[test]
    fn a_dead_body_is_food_where_it_lies() {
        let g = Grid::new(8, 8);
        let place = vec![NO_PLACE; g.cells()];
        let mut food = Food { res: vec![0.0; g.cells()], carrion: vec![0.0; g.cells()], soil: vec![0.0; g.cells()] };
        let mut c = Counters::default();
        // Three cells anchored at sub-cell (7, 4): sub-cells (7,4), (8,4) and (7,5), in world
        // cells (1,1), (2,1) and (1,1).
        let mut cells = [0u8; CELLS];
        cells[0] = DIGESTIVE as u8;
        cells[1] = DIGESTIVE as u8;
        cells[SIDE] = HARD as u8;
        let mut a = agent_with(cells, 7, 4, NORTH);
        a.energy = 0.3;
        lay_body(&a, g, &mut food, &place, 0.02, &mut c);
        // Each cell: 0.02 of matter and 0.1 of energy.
        assert!((food.res[g.idx(1, 1)] - 0.24).abs() < 1e-6);
        assert!((food.res[g.idx(2, 1)] - 0.12).abs() < 1e-6);
        assert!((c.dead - 0.36).abs() < 1e-6);
        assert_eq!(food.carrion[g.idx(1, 1)], food.res[g.idx(1, 1)]);
        // A body with no cells leaves its energy under its anchor; one with no energy leaves nothing.
        let mut b = agent_with([0u8; CELLS], 3, 3, NORTH);
        b.energy = 1.0;
        lay_body(&b, g, &mut food, &place, 0.02, &mut c);
        assert_eq!(food.res[g.idx(0, 0)], 1.0);
        b.energy = -0.5;
        lay_body(&b, g, &mut food, &place, 0.02, &mut c);
        assert_eq!(food.res[g.idx(0, 0)], 1.0);
        // A gut takes plant and dead matter in the cell's proportion.
        food.res[g.idx(0, 0)] = 2.0; // 1.0 of it dead
        let (plant, dead) = food.take(g.idx(0, 0), 0.5);
        assert!((plant - 0.25).abs() < 1e-6 && (dead - 0.25).abs() < 1e-6);
        assert!((food.res[g.idx(0, 0)] - 1.5).abs() < 1e-6 && (food.carrion[g.idx(0, 0)] - 0.75).abs() < 1e-6);
    }

    #[test]
    fn a_plant_grows_out_of_the_soil_and_the_dead_rot_into_it() {
        let mut food = Food { res: vec![0.0; 4], carrion: vec![0.0; 4], soil: vec![0.05, 0.0, 1.0, 1.0] };
        let cap = 8.0;
        // Soil 0.05 under a sun of 0.1: the plant grows 0.05 and the other 0.05 of sun is barren.
        assert_eq!(food.regrow(0, 0.1, false, cap), Regrown { added: 0.05, barren: 0.05, ..Default::default() });
        assert_eq!((food.res[0], food.soil[0]), (0.05, 0.0));
        // No soil: the whole sun is barren.
        assert_eq!(food.regrow(1, 0.1, false, cap), Regrown { barren: 0.1, ..Default::default() });
        // A body on the cell: shaded, nothing moves.
        assert_eq!(food.regrow(2, 0.1, true, cap), Regrown { shaded: 0.1, ..Default::default() });
        assert_eq!((food.res[2], food.soil[2]), (0.0, 1.0));
        // At the cap the sun is wasted and the soil stays.
        food.res[2] = cap;
        assert_eq!(food.regrow(2, 0.1, false, cap), Regrown { wasted: 0.1, ..Default::default() });
        // Dead matter rots by DECAY per step into the soil and leaves the food; the sun then
        // grows the plant out of the soil. The total on the cell is unchanged.
        food.res[3] = 2.0;
        food.carrion[3] = 2.0;
        let r = food.regrow(3, 0.1, false, cap);
        assert!((r.rot - 0.02).abs() < 1e-6 && (r.added - 0.1).abs() < 1e-6);
        assert!((food.carrion[3] - 1.98).abs() < 1e-6 && (food.res[3] - 2.08).abs() < 1e-6 && (food.soil[3] - 0.92).abs() < 1e-6);
        assert!((food.res[3] + food.soil[3] - 3.0).abs() < 1e-6);
        // What a body spends falls to the soil.
        food.spend(1, 0.05);
        assert_eq!(food.soil[1], 0.05);
    }

    #[test]
    fn a_push_meets_face_to_face() {
        let g = Grid::new(8, 8);
        // A tooth (hard tip, two muscle behind, column 2) facing east at anchor (0, 8): its tip
        // is at sub-cell (7, 10) (row 2 of the grid becomes column 7 when facing east).
        let mut tooth = [0u8; CELLS];
        tooth[2] = HARD as u8;
        tooth[SIDE + 2] = MUSCLE as u8;
        tooth[2 * SIDE + 2] = MUSCLE as u8;
        let hunter = agent_with(tooth, 0, 8, EAST);
        assert_eq!(hunter.wcells[2 * SIDE + 7], HARD as u8);
        // A soft body of two digestive cells right in front of it, at sub-cells (8, 10) and (9, 10).
        let mut soft = [0u8; CELLS];
        soft[0] = DIGESTIVE as u8;
        soft[1] = DIGESTIVE as u8;
        let prey = agent_with(soft, 8, 10, NORTH);
        let mut agents = vec![hunter, prey];
        let mut occ = Occ { sub: vec![u32::MAX; g.sw * g.sh], crowd: vec![0; g.cells()] };
        occ.claim(g, &agents[0], 0);
        occ.claim(g, &agents[1], 1);
        let place = vec![NO_PLACE; g.cells()];
        let mut c = Counters::default();
        let mut food = Food { res: vec![0.0; g.cells()], carrion: vec![0.0; g.cells()], soil: vec![0.0; g.cells()] };
        let pressed = push(&mut agents, 0, EAST, g, &mut occ, &place, &mut food, CELL_ENERGY, &mut c);
        // One body pressed with force 2 (two muscle cells in the line); the soft cell broke and
        // was eaten by nobody (the hunter has no digestive cell): it lies on the world cell it
        // was in, (2, 2), with half the prey's energy; the prey lost a cell.
        assert_eq!(pressed, vec![(1, 2)]);
        assert_eq!((c.contacts, c.cells_broken), (1, 1));
        assert_eq!(agents[1].body.mass, 1);
        assert!((food.res[g.idx(2, 2)] - (CELL_ENERGY + 0.5)).abs() < 1e-6);
        assert_eq!(food.carrion[g.idx(2, 2)], food.res[g.idx(2, 2)]);
        assert!((agents[1].energy - 0.5).abs() < 1e-6);
        assert_eq!(occ.sub[g.sidx(8, 10)], u32::MAX);
        assert_eq!(occ.crowd[g.idx(2, 2)], 1);
        // The way is clear now: the hunter fits one sub-cell east.
        assert!(agents[0].fits(g, &occ.sub, 0, EAST, 1));
        // The same push against a hard wall (hardness 3, the hunter's force 2): the wall holds
        // and, the tip being no softer, nothing breaks.
        let mut wall = [0u8; CELLS];
        wall[0] = HARD as u8;
        let w = agent_with(wall, 8, 10, NORTH);
        occ.release(g, &agents[1]);
        agents[1] = w;
        occ.claim(g, &agents[1], 1);
        let pressed = push(&mut agents, 0, EAST, g, &mut occ, &place, &mut food, CELL_ENERGY, &mut c);
        assert_eq!(pressed, vec![(1, 2)]);
        assert_eq!(c.cells_broken, 1);
        assert!(!agents[0].fits(g, &occ.sub, 0, EAST, 1));
    }
}
