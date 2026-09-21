//! The 3D arm: the same loops with a third axis. A body is a grid of side 4-8 across and `sz` cells
//! up (8 for the full grid, 4 for the cut one), stored plane by plane; a world cell is 4x4x4
//! sub-cells; a block has 6 faces and a body 6 directions to look and to move in. The two water
//! layers and the crown (e065, e091) are gone: height is real here, so a sub-cell is a place.
//!
//! What is deliberately absent, because the spike is about the clock: gravity, a food that stands
//! up, a viewer, and any law of height. Bodies float where they are put.

use crate::genome::*;
use crate::{Cfg, Stats};
use std::collections::HashMap;

pub const SIDE: usize = 8;
pub const SIDE_MAX: usize = 8;
const SIDE_MIN: usize = 4;
pub const CELLS: usize = SIDE_MAX * SIDE_MAX * SIDE_MAX;
const SIDE_RANGE: f32 = 2.0;
pub const N_KINDS: usize = 5;
pub const HARD: usize = 1;
pub const MUSCLE: usize = 2;
pub const SENSOR: usize = 3;
pub const DIGESTIVE: usize = 4;
const N_MORPH: usize = 8; // x, 1-x, y, 1-y, z, 1-z, r, 1-r
pub const SUB: usize = 4;
pub const SUB_CELLS: usize = SUB * SUB * SUB;
pub const N_IN: usize = 14; // food under; food and bodies in the six directions; the energy
pub const N_OUT: usize = 6; // stay, forward, turn left, turn right, up, down
pub const N_POLICY: usize = N_IN * N_OUT + N_OUT;
const K: usize = N_KINDS + N_POLICY;
pub const N_DIRS: usize = 6;
pub const LINES: usize = SIDE_MAX * SIDE_MAX;
pub const UNDER_MAX: usize = (SIDE_MAX / SUB + 1) * (SIDE_MAX / SUB + 1) * (SIDE_MAX / SUB + 1);

pub const CELL_ENERGY: f32 = 0.02;
pub const UPKEEP: f32 = 0.002;
pub const UPKEEP_BODY: f32 = 0.032;
pub const MOVE_COST: f32 = 0.001;
pub const BITE: f32 = 0.02;
pub const STORE: f32 = 5.0;
pub const BREED: f32 = 0.1;
pub const WEAR: f64 = 3_000.0;
pub const WEAR_SPANS: f64 = 10.0;
pub const CLOCK: f32 = 0.5;
pub const CLOCK_MASS: f32 = 16.0;
pub const EYES: usize = 8;
pub const HARDNESS: u8 = 3;
pub const KIND_MASS: [f32; N_KINDS] = [0.0, 2.0, 1.0, 0.5, 1.0];
const DENSITY_RANGE: f32 = 2.0;

const NORTH: usize = 0;
const SOUTH: usize = 1;
const EAST: usize = 2;
const WEST: usize = 3;
const UP: usize = 4;
const DOWN: usize = 5;
const DIRS: [usize; 6] = [NORTH, SOUTH, EAST, WEST, UP, DOWN];
const FREE: u32 = u32::MAX;
const WALL: u32 = u32::MAX - 1;

fn opposite(d: usize) -> usize {
    match d {
        NORTH => SOUTH,
        SOUTH => NORTH,
        EAST => WEST,
        WEST => EAST,
        UP => DOWN,
        _ => UP,
    }
}

fn left_of(d: usize) -> usize {
    match d {
        NORTH => WEST,
        WEST => SOUTH,
        SOUTH => EAST,
        _ => NORTH,
    }
}

/// Where cell i of a grid of side `s` lands in the world frame when the body faces `f`: the facing
/// turns the body about the vertical axis, so a plane turns as a 2D grid does and z is untouched.
fn to_world(i: usize, f: usize, s: usize) -> usize {
    let (z, rem) = (i / (s * s), i % (s * s));
    let (r, c) = (rem / s, rem % s);
    let m = s - 1;
    let (r2, c2) = match f {
        NORTH => (r, c),
        SOUTH => (m - r, m - c),
        EAST => (c, m - r),
        _ => (m - c, r),
    };
    (z * s + r2) * s + c2
}

fn to_body(i: usize, f: usize, s: usize) -> usize {
    let (z, rem) = (i / (s * s), i % (s * s));
    let (r2, c2) = (rem / s, rem % s);
    let m = s - 1;
    let (r, c) = match f {
        NORTH => (r2, c2),
        SOUTH => (m - r2, m - c2),
        EAST => (m - c2, r2),
        _ => (c2, m - r2),
    };
    (z * s + r) * s + c
}

fn rotate(cells: &[u8; CELLS], f: usize, s: usize, sz: usize) -> [u8; CELLS] {
    let mut out = [0u8; CELLS];
    for (i, &c) in cells.iter().enumerate().take(s * s * sz) {
        out[to_world(i, f, s)] = c;
    }
    out
}

/// The cells a grid holds and their box (r0, r1, c0, c1, z0, z1).
fn filled(cells: &[u8; CELLS], s: usize, sz: usize) -> ([u16; CELLS], u16, [u8; 6]) {
    let mut list = [0u16; CELLS];
    let mut n = 0u16;
    let mut bb = [s as u8, 0, s as u8, 0, sz as u8, 0];
    for (i, &c) in cells.iter().enumerate().take(s * s * sz) {
        if c != 0 {
            list[n as usize] = i as u16;
            n += 1;
            let (z, rem) = ((i / (s * s)) as u8, i % (s * s));
            let (r, col) = ((rem / s) as u8, (rem % s) as u8);
            bb = [bb[0].min(r), bb[1].max(r), bb[2].min(col), bb[3].max(col), bb[4].min(z), bb[5].max(z)];
        }
    }
    if n == 0 {
        bb = [0; 6];
    }
    (list, n, bb)
}

fn neighbor(pos: usize, d: usize, s: usize, sz: usize) -> Option<usize> {
    let (z, rem) = (pos / (s * s), pos % (s * s));
    let (r, c) = (rem / s, rem % s);
    let (z, r, c) = match d {
        NORTH => (z, r.checked_sub(1)?, c),
        SOUTH => (z, r + 1, c),
        EAST => (z, r, c + 1),
        WEST => (z, r, c.checked_sub(1)?),
        UP => (z + 1, r, c),
        _ => (z.checked_sub(1)?, r, c),
    };
    (r < s && c < s && z < sz).then_some((z * s + r) * s + c)
}

/// The parts of a grid (e045, e047): blocks joined through their faces, their edges and their
/// corners - in 3D that is the 26 cells around one.
fn parts_of(cells: &[u8; CELLS], s: usize, sz: usize) -> ([u8; CELLS], usize) {
    let mut label = [0u8; CELLS];
    let mut n = 0usize;
    let mut stack: Vec<usize> = Vec::new();
    for start in 0..s * s * sz {
        if cells[start] == 0 || label[start] != 0 {
            continue;
        }
        n += 1;
        label[start] = n as u8;
        stack.push(start);
        while let Some(p) = stack.pop() {
            let (z, rem) = ((p / (s * s)) as i32, p % (s * s));
            let (r, c) = ((rem / s) as i32, (rem % s) as i32);
            for dz in -1..=1 {
                for dr in -1..=1 {
                    for dc in -1..=1 {
                        let (zz, rr, cc) = (z + dz, r + dr, c + dc);
                        if (dz == 0 && dr == 0 && dc == 0) || zz < 0 || rr < 0 || cc < 0 || zz >= sz as i32 || rr >= s as i32 || cc >= s as i32 {
                            continue;
                        }
                        let q = (zz as usize * s + rr as usize) * s + cc as usize;
                        if cells[q] != 0 && label[q] == 0 {
                            label[q] = n as u8;
                            stack.push(q);
                        }
                    }
                }
            }
        }
    }
    (label, n)
}

fn keep_largest(cells: &mut [u8; CELLS], s: usize, sz: usize) -> u16 {
    let (label, n) = parts_of(cells, s, sz);
    if n < 2 {
        return 0;
    }
    let mut size = vec![0u16; n + 1];
    let mut mass = vec![0.0f32; n + 1];
    for i in 0..s * s * sz {
        let l = label[i] as usize;
        if l > 0 {
            size[l] += 1;
            mass[l] += KIND_MASS[cells[i] as usize];
        }
    }
    let mut keep = 0usize;
    for l in 1..=n {
        if keep == 0 || size[l] > size[keep] || (size[l] == size[keep] && mass[l] > mass[keep]) {
            keep = l;
        }
    }
    let mut cut = 0u16;
    for (cell, &l) in cells.iter_mut().zip(&label).take(s * s * sz) {
        if l != 0 && l as usize != keep {
            *cell = 0;
            cut += 1;
        }
    }
    cut
}

fn face_hardness(cells: &[u8; CELLS], pos: usize, into: usize, s: usize, sz: usize) -> u8 {
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
        p = neighbor(q, into, s, sz);
    }
    HARDNESS * n
}

/// The line (in the grid's frame) a cell belongs to when the body moves in direction d.
fn line_of(pos: usize, d: usize, s: usize) -> usize {
    let (z, rem) = (pos / (s * s), pos % (s * s));
    let (r, c) = (rem / s, rem % s);
    match d {
        NORTH | SOUTH => z * s + c,
        EAST | WEST => z * s + r,
        _ => r * s + c,
    }
}

#[derive(Clone, Copy, Default)]
pub struct Tip {
    pub hardness: u8,
    pub force: u8,
}

fn tips_of(cells: &[u8; CELLS], s: usize, sz: usize) -> [[Tip; LINES]; 6] {
    let mut tips = [[Tip::default(); LINES]; 6];
    for side in 0..6 {
        let (n_line, depth) = match side {
            NORTH | SOUTH => (sz * s, s),
            EAST | WEST => (sz * s, s),
            _ => (s * s, sz),
        };
        for line in 0..n_line {
            let at = |k: usize| -> usize {
                match side {
                    NORTH => (line / s * s + k) * s + line % s,
                    SOUTH => (line / s * s + (s - 1 - k)) * s + line % s,
                    EAST => (line / s * s + line % s) * s + (s - 1 - k),
                    WEST => (line / s * s + line % s) * s + k,
                    UP => ((depth - 1 - k) * s + line / s) * s + line % s,
                    _ => (k * s + line / s) * s + line % s,
                }
            };
            let mut tip = Tip::default();
            let force = (0..depth).filter(|&k| cells[at(k)] == MUSCLE as u8).count() as u8;
            if let Some(k0) = (0..depth).find(|&k| cells[at(k)] != 0) {
                let hardness = if cells[at(k0)] == HARD as u8 { HARDNESS * (k0..depth).take_while(|&k| cells[at(k)] == HARD as u8).count() as u8 } else { 1 };
                tip = Tip { hardness, force };
            }
            tips[side][line] = tip;
        }
    }
    tips
}

fn open_faces(cells: &[u8; CELLS], s: usize, sz: usize, hard: bool) -> [u8; CELLS] {
    let mut out = [0u8; CELLS];
    for pos in 0..s * s * sz {
        let c = cells[pos];
        if c == 0 || (c == HARD as u8) != hard {
            continue;
        }
        out[pos] = DIRS.iter().filter(|&&d| neighbor(pos, d, s, sz).is_none_or(|q| cells[q] == 0)).count() as u8;
    }
    out
}

fn sight_of(cells: &[u8; CELLS], s: usize, sz: usize) -> [u8; 6] {
    let mut n = [0u8; 6];
    for pos in 0..s * s * sz {
        if cells[pos] != SENSOR as u8 {
            continue;
        }
        for (j, d) in DIRS.into_iter().enumerate() {
            let mut q = neighbor(pos, d, s, sz);
            while let Some(p) = q.filter(|&p| cells[p] == 0) {
                q = neighbor(p, d, s, sz);
            }
            n[j] += q.is_none() as u8;
        }
    }
    n
}

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
    fn add(&mut self, c: usize) {
        if !self.c[..self.n].contains(&c) && self.n < UNDER_MAX {
            self.c[self.n] = c;
            self.n += 1;
        }
    }
    fn iter(&self) -> impl Iterator<Item = usize> + '_ {
        self.c[..self.n].iter().copied()
    }
    fn contains(&self, c: usize) -> bool {
        self.c[..self.n].contains(&c)
    }
}

pub struct Laws {
    morphogen: [[u8; TAG_LEN]; N_MORPH],
    table: Vec<[f32; K]>,
    density: Vec<f32>,
    side: Vec<f32>,
    morph_level: Vec<Vec<Vec<f32>>>, // [side * (SIDE_MAX + 1) + sz]
}

impl Laws {
    pub fn new(seed: u64) -> Self {
        let mut rng = Rng(seed | 1);
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
        let mut morph_level = Vec::new();
        for s in 0..=SIDE_MAX {
            for sz in 0..=SIDE_MAX {
                let n = s * s * sz;
                let mut levels: Vec<Vec<f32>> = (0..N_MORPH).map(|_| vec![0.0f32; n + 1]).collect();
                let (cx, cz) = ((s as f32 - 1.0) / 2.0, (sz as f32 - 1.0) / 2.0);
                let rmax = (2.0 * cx * cx + cz * cz).sqrt().max(1e-6);
                for i in 0..n {
                    let (zi, rem) = (i / (s * s), i % (s * s));
                    let x = (rem % s) as f32 / (s as f32 - 1.0).max(1.0);
                    let y = (rem / s) as f32 / (s as f32 - 1.0).max(1.0);
                    let z = zi as f32 / (sz as f32 - 1.0).max(1.0);
                    let (dx, dy, dz) = ((rem % s) as f32 - cx, (rem / s) as f32 - cx, zi as f32 - cz);
                    let r = (dx * dx + dy * dy + dz * dz).sqrt() / rmax;
                    for (m, v) in [x, 1.0 - x, y, 1.0 - y, z, 1.0 - z, r, 1.0 - r].into_iter().enumerate() {
                        levels[m][i] = 2.0 * v - 1.0;
                    }
                }
                morph_level.push(levels);
            }
        }
        Laws { morphogen, table, density, side, morph_level }
    }
}

#[derive(Clone)]
pub struct Body {
    pub cells: [u8; CELLS],
    pub side: u8,
    pub sz: u8,
    pub size: u16,
    pub mass: f32,
    pub density: f32,
    pub kinds: [u16; N_KINDS],
    pub tips: [[Tip; LINES]; 6],
    pub policy: [f32; N_POLICY],
    pub open_soft: u16,
    pub sight: [u8; 6],
    pub store: f32,
}

impl Body {
    pub fn new(cells: [u8; CELLS], side: usize, sz: usize, policy: [f32; N_POLICY], density: f32) -> Self {
        let mut b = Body { cells, side: side as u8, sz: sz as u8, size: 0, mass: 0.0, density, kinds: [0; N_KINDS], tips: [[Tip::default(); LINES]; 6], policy, open_soft: 0, sight: [0; 6], store: STORE };
        b.refresh();
        b
    }
    pub fn s(&self) -> usize {
        self.side as usize
    }
    pub fn sz(&self) -> usize {
        self.sz as usize
    }
    pub fn block_mass(&self, kind: u8) -> f32 {
        self.density * KIND_MASS[kind as usize]
    }
    pub fn matter(&self) -> f64 {
        (1..N_KINDS).map(|k| self.kinds[k] as f64 * CELL_ENERGY as f64 * self.density as f64 * KIND_MASS[k] as f64).sum()
    }
    pub fn refresh(&mut self) {
        let (s, sz) = (self.s(), self.sz());
        self.kinds = [0; N_KINDS];
        for &c in self.cells.iter().take(s * s * sz) {
            self.kinds[c as usize] += 1;
        }
        self.size = (s * s * sz) as u16 - self.kinds[0];
        self.mass = (1..N_KINDS).map(|k| self.kinds[k] as f32 * self.block_mass(k as u8)).sum();
        self.tips = tips_of(&self.cells, s, sz);
        self.open_soft = open_faces(&self.cells, s, sz, false).iter().map(|&f| f as u16).sum();
        self.sight = sight_of(&self.cells, s, sz);
    }
    pub fn speed(&self) -> f32 {
        if self.mass <= 0.0 { 0.0 } else { self.kinds[MUSCLE] as f32 / self.mass }
    }
    pub fn range(&self) -> usize {
        1 + (self.kinds[SENSOR] as usize).min(EYES)
    }
    pub fn threshold(&self) -> f32 {
        2.0 + BREED * self.mass
    }
}

pub fn develop_genes(genes: &[Gene], laws: &Laws, zcap: usize) -> Body {
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
    let no_pos: Vec<Vec<f32>> = (0..N_MORPH).map(|_| vec![0.0f32]).collect();
    let free = settle(n, &w, &wm, &no_pos, 1);
    let read = |column: &[f32]| -> f32 {
        let mut d = 0.0f32;
        for (i, g) in genes.iter().enumerate() {
            d += column[pattern_index(&g.product)] * free[i];
        }
        d
    };
    let side = ((SIDE as f32 * SIDE_RANGE.powf(sigmoid(read(&laws.side)) * 2.0 - 1.0)).round() as usize).clamp(SIDE_MIN, SIDE_MAX);
    let sz = side.min(zcap);
    let ncell = side * side * sz;
    let level = settle(n, &w, &wm, &laws.morph_level[side * (SIDE_MAX + 1) + sz], ncell);
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
    keep_largest(&mut cells, side, sz);
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
    Body::new(cells, side, sz, policy, density)
}

#[derive(Clone, Copy)]
pub struct Grid {
    pub w: usize,
    pub h: usize,
    pub up: usize, // world cells up
    pub sw: usize,
    pub sh: usize,
    pub sd: usize,
}

impl Grid {
    pub fn new(w: usize, h: usize, up: usize) -> Self {
        Grid { w, h, up, sw: w * SUB, sh: h * SUB, sd: up * SUB }
    }
    pub fn idx(&self, x: usize, y: usize, z: usize) -> usize {
        (z * self.h + y) * self.w + x
    }
    pub fn cells(&self) -> usize {
        self.w * self.h * self.up
    }
    pub fn sidx(&self, sx: usize, sy: usize, sz: usize) -> usize {
        (sz * self.sh + sy) * self.sw + sx
    }
    pub fn wcell(&self, sx: usize, sy: usize, sz: usize) -> usize {
        self.idx(sx / SUB, sy / SUB, sz / SUB)
    }
    /// Moved k sub-cells in direction d. The world wraps in x and y and is closed above and below:
    /// off the top or the bottom is out of the world, which `Occ::at` reads as a wall.
    pub fn sstep(&self, sx: usize, sy: usize, sz: usize, d: usize, k: usize) -> (usize, usize, usize) {
        match d {
            NORTH => (sx, (sy + self.sh - k % self.sh) % self.sh, sz),
            SOUTH => (sx, (sy + k) % self.sh, sz),
            EAST => ((sx + k) % self.sw, sy, sz),
            WEST => ((sx + self.sw - k % self.sw) % self.sw, sy, sz),
            UP => (sx, sy, sz + k),
            _ => (sx, sy, sz.wrapping_sub(k)),
        }
    }
}

pub struct Occ {
    pub sub: Vec<u32>,
    pub crowd: Vec<u16>,
}

impl Occ {
    pub fn new(g: Grid) -> Self {
        Occ { sub: vec![FREE; g.sw * g.sh * g.sd], crowd: vec![0; g.cells()] }
    }
    pub fn bytes(&self) -> usize {
        self.sub.len() * 4 + self.crowd.len() * 2
    }
    pub fn at(&self, g: Grid, sx: usize, sy: usize, sz: usize) -> u32 {
        if sz >= g.sd {
            return WALL;
        }
        self.sub[g.sidx(sx, sy, sz)]
    }
    fn put(&mut self, g: Grid, a: &Agent, pos: usize, v: u32) {
        let (sx, sy, sz) = a.sub_at(g, pos, NORTH, 0);
        if sz >= g.sd {
            return;
        }
        self.sub[g.sidx(sx, sy, sz)] = v;
        let c = g.wcell(sx, sy, sz);
        if v == FREE {
            self.crowd[c] -= 1;
        } else {
            self.crowd[c] += 1;
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
}

pub struct Agent {
    pub x: usize,
    pub y: usize,
    pub z: usize,
    pub energy: f64,
    pub fat: f64,
    pub age: u32,
    pub turns: u32,
    pub phase: f32,
    pub alive: bool,
    pub water: f32,
    pub breath: f32,
    pub temp: f32,
    pub genome: Vec<u8>,
    pub keys: Vec<u16>,
    pub gene_ids: Vec<u16>,
    pub body: Body,
    pub facing: u8,
    pub wcells: [u8; CELLS],
    pub tips: [[Tip; LINES]; 6],
    pub filled: [u16; CELLS],
    pub n_filled: u16,
    pub bbox: [u8; 6],
    pub open: [u8; CELLS],
    pub open_hard: [u8; CELLS],
}

impl Agent {
    pub fn new(genome: Vec<u8>, keys: Vec<u16>, gene_ids: Vec<u16>, body: Body, facing: u8, energy: f64) -> Agent {
        let mut a = Agent {
            x: 0, y: 0, z: 0, energy, fat: 0.0, age: 0, turns: 0, phase: 0.0, alive: body.size > 0, water: 1.0, breath: 1.0, temp: 20.0,
            genome, keys, gene_ids, body, facing, wcells: [0; CELLS], tips: [[Tip::default(); LINES]; 6], filled: [0; CELLS], n_filled: 0, bbox: [0; 6], open: [0; CELLS], open_hard: [0; CELLS],
        };
        a.reframe();
        a
    }
    pub fn reframe(&mut self) {
        let (s, sz) = (self.body.s(), self.body.sz());
        self.wcells = rotate(&self.body.cells, self.facing as usize, s, sz);
        self.tips = tips_of(&self.wcells, s, sz);
        let (list, n, bb) = filled(&self.wcells, s, sz);
        self.filled = list;
        self.n_filled = n;
        self.bbox = bb;
        self.open = open_faces(&self.wcells, s, sz, false);
        self.open_hard = open_faces(&self.wcells, s, sz, true);
    }
    pub fn mass(&self) -> f32 {
        self.body.mass
    }
    pub fn cells_held(&self) -> impl Iterator<Item = usize> + '_ {
        self.filled[..self.n_filled as usize].iter().map(|&p| p as usize)
    }
    pub fn sub_at(&self, g: Grid, pos: usize, d: usize, k: usize) -> (usize, usize, usize) {
        let s = self.body.s();
        let (z, rem) = (pos / (s * s), pos % (s * s));
        g.sstep((self.x + rem % s) % g.sw, (self.y + rem / s) % g.sh, self.z + z, d, k)
    }
    pub fn under(&self, g: Grid, d: usize, k: usize) -> CellsUnder {
        let mut out = CellsUnder::default();
        if self.n_filled == 0 {
            return out;
        }
        let [r0, r1, c0, c1, z0, z1] = self.bbox;
        let s = self.body.s();
        let (sx, sy, sz) = self.sub_at(g, (z0 as usize * s + r0 as usize) * s + c0 as usize, d, k);
        if sz >= g.sd {
            return out;
        }
        let nx = (sx % SUB + (c1 - c0) as usize) / SUB + 1;
        let ny = (sy % SUB + (r1 - r0) as usize) / SUB + 1;
        let nz = (sz % SUB + (z1 - z0) as usize) / SUB + 1;
        for l in 0..nz {
            if sz / SUB + l >= g.up {
                break;
            }
            for j in 0..ny {
                for i in 0..nx {
                    out.add(g.idx((sx / SUB + i) % g.w, (sy / SUB + j) % g.h, sz / SUB + l));
                }
            }
        }
        out
    }
    pub fn here(&self, g: Grid) -> usize {
        let [r0, r1, c0, c1, z0, z1] = self.bbox;
        let s = self.body.s();
        let mid = (((z0 + z1) as usize / 2) * s + (r0 + r1) as usize / 2) * s + (c0 + c1) as usize / 2;
        let (sx, sy, sz) = self.sub_at(g, mid, NORTH, 0);
        g.wcell(sx, sy, sz.min(g.sd - 1))
    }
    pub fn fits(&self, g: Grid, occ: &Occ, me: u32, d: usize, k: usize) -> bool {
        self.cells_held().all(|p| {
            let (sx, sy, sz) = self.sub_at(g, p, d, k);
            let o = occ.at(g, sx, sy, sz);
            o == FREE || o == me
        })
    }
}

pub fn pace(mass: f32) -> f32 {
    if mass <= CLOCK_MASS { 1.0 } else { (CLOCK_MASS / mass).powf(CLOCK) }
}

pub fn wear_chance(age: u32) -> f64 {
    let s = WEAR / WEAR_SPANS;
    let h0 = std::f64::consts::LN_2 * std::f64::consts::LN_2 / (s * (WEAR_SPANS.exp2() - 1.0));
    (h0 * (age as f64 / s).exp2()).min(1.0)
}

fn stroke(speed: f32, rng: &mut Rng) -> bool {
    speed >= 1.0 || rng.f32() < speed
}

fn act(policy: &[f32; N_POLICY], input: &[f32; N_IN]) -> usize {
    let mut best = 0;
    let mut top = f32::MIN;
    for o in 0..N_OUT {
        let mut v = policy[N_IN * N_OUT + o];
        for (i, &x) in input.iter().enumerate() {
            v += policy[i * N_OUT + o] * x;
        }
        if v > top {
            top = v;
            best = o;
        }
    }
    best
}

fn look(a: &Agent, g: Grid, d: usize, k: usize, food: &[f32], crowd: &[u16]) -> (f32, f32) {
    let now = a.under(g, NORTH, 0);
    let before = if k > 1 { a.under(g, d, (k - 1) * SUB) } else { now };
    let (mut f, mut others) = (0.0f32, 0.0f32);
    for c in a.under(g, d, k * SUB).iter() {
        if now.contains(c) || before.contains(c) {
            continue;
        }
        f += food[c];
        others += crowd[c] as f32 / SUB_CELLS as f32;
    }
    (f, others)
}

fn sense(a: &Agent, g: Grid, food: &[f32], crowd: &[u16]) -> [f32; N_IN] {
    let f = a.facing as usize;
    let dirs = [f, opposite(f), left_of(f), opposite(left_of(f)), UP, DOWN];
    let mut input = [0.0f32; N_IN];
    input[0] = a.under(g, NORTH, 0).iter().map(|c| food[c]).sum();
    for (j, &d) in dirs.iter().enumerate() {
        let reach = a.body.range();
        let (f1, o1) = look(a, g, d, 1, food, crowd);
        input[1 + j] = f1;
        input[7 + j] = o1;
        for r in 2..=reach {
            let (fr, ob) = look(a, g, d, r, food, crowd);
            input[1 + j] += fr / r as f32;
            input[7 + j] += ob / r as f32;
        }
    }
    input[13] = (a.energy / a.body.threshold() as f64) as f32;
    input
}

pub struct World {
    g: Grid,
    occ: Occ,
    agents: Vec<Agent>,
    food: Vec<f32>,
    dryness: Vec<f32>,
    temp: Vec<f64>,
    laws: Laws,
    cache: HashMap<Vec<u16>, Body>,
    rng: Rng,
    tiles: Vec<usize>, // the world cells (columns x levels) a body may stand on
    cfg: Cfg,
    pub k: Stats,
}

impl World {
    pub fn new(cfg: &Cfg) -> World {
        let g = Grid::new(cfg.side, cfg.side, cfg.height);
        let mut rng = Rng(cfg.seed.wrapping_mul(0x9E3779B97F4A7C15) | 1);
        let laws = Laws::new(cfg.seed);
        let mut w = World {
            g,
            occ: Occ::new(g),
            agents: Vec::new(),
            food: vec![1.0; g.cells()],
            dryness: vec![0.3; g.cells()],
            temp: vec![20.0; g.cells()],
            laws,
            cache: HashMap::new(),
            rng: Rng(cfg.seed.wrapping_mul(0xA0761D6478BD642F) | 1),
            tiles: Vec::new(),
            cfg: cfg.clone(),
            k: Stats::default(),
        };
        let mut pool: Vec<(Vec<u8>, Body)> = Vec::new();
        while pool.len() < 64 {
            let genome = random_genome(&mut rng);
            let genes = parse_genes(&genome);
            if genes.is_empty() {
                continue;
            }
            let body = develop_genes(&genes, &w.laws, cfg.sz);
            if body.size > 0 && (5..=7).contains(&body.s()) {
                pool.push((genome, body));
            }
        }
        let blocks: f32 = pool.iter().map(|(_, b)| b.size as f32).sum::<f32>() / pool.len() as f32;
        // The ground: whole columns of tile x tile cells, all the way up, as many as the target fill
        // asks for - so the crowd around a body is the control's whatever the bodies came out.
        let want = (cfg.bodies as f32 * blocks / (cfg.fill * SUB_CELLS as f32)).ceil() as usize;
        let tile = 16usize;
        let n_tiles = (want / (tile * tile * g.up)).max(1);
        let per = g.w / tile;
        let mut chosen: Vec<usize> = (0..per * per).collect();
        for i in 0..chosen.len() {
            let j = i + rng.below(chosen.len() - i);
            chosen.swap(i, j);
        }
        for &t in chosen.iter().take(n_tiles) {
            let (tx, ty) = (t % per * tile, t / per * tile);
            for dz in 0..g.up {
                for dy in 0..tile {
                    for dx in 0..tile {
                        w.tiles.push(g.idx(tx + dx, ty + dy, dz));
                    }
                }
            }
        }
        let mut tries = 0u64;
        while w.agents.len() < cfg.bodies && tries < 200 * cfg.bodies as u64 {
            tries += 1;
            let (genome, body) = pool[rng.below(pool.len())].clone();
            let genes = parse_genes(&genome);
            let mut a = Agent::new(genome, sorted_keys(&genes), genes.iter().map(Gene::key).collect(), body, rng.below(4) as u8, 1.0);
            let c = w.tiles[rng.below(w.tiles.len())];
            let (cx, cy, cz) = (c % g.w, c / g.w % g.h, c / (g.w * g.h));
            a.x = cx * SUB + rng.below(SUB);
            a.y = cy * SUB + rng.below(SUB);
            a.z = (cz * SUB + rng.below(SUB)).min(g.sd.saturating_sub(a.body.sz()));
            a.energy = 1.0 + rng.f64() * a.body.threshold() as f64;
            if !a.fits(g, &w.occ, FREE, NORTH, 0) {
                continue;
            }
            let i = w.agents.len() as u32;
            w.occ.claim(g, &a, i);
            w.agents.push(a);
        }
        w
    }

    pub fn step(&mut self) {
        let g = self.g;
        let off = self.cfg.off.clone();
        for i in 0..self.agents.len() {
            if !self.agents[i].alive {
                continue;
            }
            let a = &mut self.agents[i];
            a.age += 1;
            a.phase += pace(a.mass());
            if a.phase < 1.0 {
                continue;
            }
            a.phase -= 1.0;
            a.turns += 1;
            self.k.turns += 1;
            if off != "wear" {
                let h = wear_chance(self.agents[i].turns);
                let failed: Vec<usize> = self.agents[i].cells_held().filter(|_| self.rng.f64() < h).collect();
                for pos in failed {
                    let a = &mut self.agents[i];
                    if a.wcells[pos] == 0 {
                        continue;
                    }
                    self.occ.release_one(g, a, pos);
                    let bpos = to_body(pos, a.facing as usize, a.body.s());
                    a.body.cells[bpos] = 0;
                    a.body.refresh();
                    a.reframe();
                    self.k.worn += 1;
                }
                if self.agents[i].body.size == 0 {
                    self.agents[i].alive = false;
                    continue;
                }
            }
            if off != "eat" {
                let a = &self.agents[i];
                let mut guts = CellsUnder::default();
                let mut gut_n = [0u8; UNDER_MAX];
                for p in a.cells_held() {
                    if a.wcells[p] == DIGESTIVE as u8 {
                        let (sx, sy, sz) = a.sub_at(g, p, NORTH, 0);
                        if sz >= g.sd {
                            continue;
                        }
                        let c = g.wcell(sx, sy, sz);
                        guts.add(c);
                        gut_n[guts.c[..guts.n].iter().position(|&x| x == c).unwrap()] += 1;
                    }
                }
                let mut eaten = 0.0f64;
                for (j, c) in guts.iter().enumerate() {
                    let bite = (BITE * gut_n[j] as f32).min(self.food[c]);
                    self.food[c] = self.food[c] - bite + 0.01;
                    eaten += bite as f64;
                }
                let a = &mut self.agents[i];
                let full = (UPKEEP * a.body.size as f32 + UPKEEP_BODY) as f64;
                let from_energy = full.min((a.energy + eaten).max(0.0));
                let from_fat = (full - from_energy).min(a.fat);
                a.fat += from_energy - from_fat;
                let over = (a.fat - (a.body.store * a.body.mass) as f64).max(0.0);
                a.fat -= over;
                a.energy += eaten - from_energy;
            }
            if off != "faces" {
                let a = &self.agents[i];
                let (mut lost, mut drunk) = (0.0f32, 0.0f32);
                let (mut faces, mut ashore) = (0u16, 0u16);
                let (mut kk, mut sum) = (0.0f64, 0.0f64);
                for p in a.cells_held() {
                    let (sx, sy, sz) = a.sub_at(g, p, NORTH, 0);
                    if sz >= g.sd {
                        continue;
                    }
                    let c = g.wcell(sx, sy, sz);
                    lost += self.dryness[c] * a.open[p] as f32;
                    drunk += self.dryness[c];
                    ashore += 1;
                    faces += a.open[p] as u16;
                    let f = a.open[p] as f64 + 0.25 * a.open_hard[p] as f64;
                    if f > 0.0 {
                        kk += f;
                        sum += f * self.temp[c];
                    }
                }
                let a = &mut self.agents[i];
                let size = a.body.size.max(1) as f32;
                a.water = (a.water + (0.01 * drunk - 0.004 * lost) / size).min(1.0);
                a.breath = (a.breath + (0.01 * (faces as f32 - ashore as f32)) / size).min(1.0);
                if kk > 0.0 {
                    let target = sum / kk;
                    let r = (0.09 * kk / a.mass().max(1e-6) as f64).min(1.0);
                    a.temp += (r * (target - a.temp as f64)) as f32;
                }
            }
            let action = if off == "sense" {
                1
            } else {
                let input = sense(&self.agents[i], g, &self.food, &self.occ.crowd);
                self.k.acted += act(&self.agents[i].body.policy, &input) as u64;
                // The action a body takes is drawn from the control's mix (e097: stay 5.4%, forward
                // 86.1%, turn left 4.1%, turn right 4.4%), so that both arms do the same work after
                // the decision. What the policy chose is counted and thrown away: random genomes
                // hardly ever walk, and the walk is where the geometry is paid.
                let r = self.rng.f32();
                if r < 0.054 { 0 } else if r < 0.915 { 1 } else if r < 0.956 { 2 } else { 3 }
            };
            if off == "move" {
                continue;
            }
            if action == 1 || action >= 4 {
                let d = match action {
                    1 => self.agents[i].facing as usize,
                    4 => UP,
                    _ => DOWN,
                };
                self.push(i, d);
                if self.agents[i].fits(g, &self.occ, i as u32, d, 1) {
                    if stroke(self.agents[i].body.speed(), &mut self.rng) {
                        self.occ.release(g, &self.agents[i]);
                        let (nx, ny, nz) = g.sstep(self.agents[i].x, self.agents[i].y, self.agents[i].z, d, 1);
                        self.agents[i].x = nx;
                        self.agents[i].y = ny;
                        self.agents[i].z = nz;
                        self.occ.claim(g, &self.agents[i], i as u32);
                        self.k.moved += 1;
                        let a = &mut self.agents[i];
                        let cost = (MOVE_COST * a.mass()) as f64;
                        a.energy -= cost.min(a.energy.max(0.0));
                    }
                } else {
                    self.k.blocked += 1;
                }
            } else if action == 2 || action == 3 {
                let f = self.agents[i].facing as usize;
                let nf = if action == 2 { left_of(f) } else { opposite(left_of(f)) };
                let a = &self.agents[i];
                let (s, sz) = (a.body.s(), a.body.sz());
                let (list, n, _) = filled(&rotate(&a.body.cells, nf, s, sz), s, sz);
                let room = list[..n as usize].iter().all(|&p| {
                    let (sx, sy, szz) = a.sub_at(g, p as usize, NORTH, 0);
                    let o = self.occ.at(g, sx, sy, szz);
                    o == FREE || o == i as u32
                });
                if room && stroke(self.agents[i].body.speed(), &mut self.rng) {
                    self.occ.release(g, &self.agents[i]);
                    self.agents[i].facing = nf as u8;
                    self.agents[i].reframe();
                    self.occ.claim(g, &self.agents[i], i as u32);
                }
            }
        }
        if off != "births" {
            self.births();
        }
        self.k.steps += 1;
    }

    fn push(&mut self, i: usize, d: usize) {
        let g = self.g;
        let opp = opposite(d);
        let mut pressed: Vec<(usize, u8)> = Vec::new();
        let mut breaks: Vec<(usize, usize)> = Vec::new();
        for p in self.agents[i].cells_held() {
            let (sx, sy, sz) = self.agents[i].sub_at(g, p, d, 1);
            let j = self.occ.at(g, sx, sy, sz);
            if j == FREE || j == WALL || j as usize == i {
                continue;
            }
            let j = j as usize;
            let b = &self.agents[j];
            let (bs, bz) = (b.body.s(), b.body.sz());
            let (r, col) = ((sy + g.sh - b.y) % g.sh, (sx + g.sw - b.x) % g.sw);
            if r >= bs || col >= bs || sz < b.z || sz - b.z >= bz {
                continue;
            }
            let q = ((sz - b.z) * bs + r) * bs + col;
            let (asz, aszz) = (self.agents[i].body.s(), self.agents[i].body.sz());
            let ha = face_hardness(&self.agents[i].wcells, p, opp, asz, aszz) as f32 * self.agents[i].body.density;
            let hb = face_hardness(&b.wcells, q, d, bs, bz) as f32 * b.body.density;
            let force = self.agents[i].tips[d][line_of(p, d, asz)].force;
            match pressed.iter_mut().find(|e| e.0 == j) {
                Some(e) => e.1 = e.1.saturating_add(force),
                None => pressed.push((j, force)),
            }
            if hb < ha && force as f32 > hb {
                breaks.push((j, q));
            }
        }
        self.k.contacts += pressed.len() as u64;
        for (victim, pos) in breaks {
            let v = &mut self.agents[victim];
            if v.wcells[pos] == 0 {
                continue;
            }
            self.occ.release_one(g, v, pos);
            let v = &mut self.agents[victim];
            let bpos = to_body(pos, v.facing as usize, v.body.s());
            v.body.cells[bpos] = 0;
            v.body.refresh();
            v.reframe();
            self.k.broken += 1;
            if v.body.size == 0 {
                v.alive = false;
            }
        }
    }

    fn births(&mut self) {
        let g = self.g;
        let n = self.agents.len();
        let children = (self.cfg.children * n as f64).round() as usize;
        let developing = (self.cfg.develops * n as f64).round() as usize;
        for c in 0..children {
            let parent = self.rng.below(n);
            if !self.agents[parent].alive {
                continue;
            }
            let mut mate = false;
            {
                let a = &self.agents[parent];
                let [r0, r1, c0, c1, z0, z1] = a.bbox;
                let (x0, y0) = (a.x + g.sw + c0 as usize - 2, a.y + g.sh + r0 as usize - 2);
                let z0 = (a.z + z0 as usize).saturating_sub(2);
                'cells: for dz in 0..(z1 - z0.min(z1 as usize) as u8 + 5) as usize {
                    if z0 + dz >= g.sd {
                        break;
                    }
                    for dy in 0..(r1 - r0 + 5) as usize {
                        for dx in 0..(c1 - c0 + 5) as usize {
                            let j = self.occ.at(g, (x0 + dx) % g.sw, (y0 + dy) % g.sh, z0 + dz);
                            if j == FREE || j == WALL || j as usize == parent {
                                continue;
                            }
                            let m = &self.agents[j as usize];
                            if m.alive && gene_distance(&a.keys, &m.keys) <= 6 {
                                mate = true;
                                break 'cells;
                            }
                        }
                    }
                }
            }
            self.k.mates += mate as u64;
            let mut genome = self.agents[parent].genome.clone();
            mutate(&mut genome, &mut self.rng);
            let genes = parse_genes(&genome);
            if genes.is_empty() {
                continue;
            }
            let gene_ids: Vec<u16> = genes.iter().map(Gene::key).collect();
            let keys = sorted_keys(&genes);
            let body = if c < developing && self.cfg.off != "develop" {
                let b = develop_genes(&genes, &self.laws, self.cfg.sz);
                self.k.develops += 1;
                self.cache.insert(gene_ids.clone(), b.clone());
                b
            } else {
                match self.cache.get(&gene_ids) {
                    Some(b) => b.clone(),
                    None => self.agents[parent].body.clone(),
                }
            };
            if body.size == 0 {
                continue;
            }
            let mut child = Agent::new(genome, keys, gene_ids, body, self.rng.below(4) as u8, 1.0);
            let (px, py, pz) = (self.agents[parent].x, self.agents[parent].y, self.agents[parent].z);
            let reach = self.agents[parent].body.s().max(child.body.s());
            let start = self.rng.below(6);
            let mut spot = None;
            'search: for t in 0..6 {
                let d = DIRS[(start + t) % 6];
                for kk in 1..=reach {
                    let (cx, cy, cz) = g.sstep(px, py, pz, d, kk);
                    if cz >= g.sd {
                        break;
                    }
                    child.x = cx;
                    child.y = cy;
                    child.z = cz;
                    if child.fits(g, &self.occ, FREE, NORTH, 0) {
                        spot = Some((cx, cy, cz));
                        break 'search;
                    }
                }
            }
            match spot {
                Some((cx, cy, cz)) => {
                    child.x = cx;
                    child.y = cy;
                    child.z = cz;
                    let slot = self.rng.below(n);
                    if self.agents[slot].alive {
                        self.occ.release(g, &self.agents[slot]);
                    }
                    self.occ.claim(g, &child, slot as u32);
                    self.agents[slot] = child;
                    self.k.births += 1;
                }
                None => self.k.no_room += 1,
            }
        }
    }

    pub fn stats(&mut self) -> Stats {
        let alive: Vec<&Agent> = self.agents.iter().filter(|a| a.alive).collect();
        let mut k = std::mem::take(&mut self.k);
        k.pop = alive.len();
        k.blocks = alive.iter().map(|a| a.body.size as f64).sum::<f64>() / alive.len().max(1) as f64;
        k.side = alive.iter().map(|a| a.body.s() as f64).sum::<f64>() / alive.len().max(1) as f64;
        let held: usize = alive.iter().map(|a| a.n_filled as usize).sum();
        k.fill = held as f64 / (self.tiles.len() * SUB_CELLS).max(1) as f64;
        k.ground = self.tiles.len();
        k.occ_bytes = self.occ.bytes();
        k.agent_bytes = alive.len() * std::mem::size_of::<Agent>();
        k
    }
}

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
