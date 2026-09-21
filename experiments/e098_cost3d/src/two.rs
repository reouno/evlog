//! The 2D arm: today's geometry (e097), trimmed to what a step costs. A body is a grid of side
//! 4-16 stored row by row; a world cell is 4x4 sub-cells and holds three layers (e065, e091); a
//! block has 4 faces. Everything the climate and the producers do is left out - it is 2.6 ms of the
//! 28 and 3D does not touch it.

use crate::genome::*;
use crate::{Cfg, Stats};
use std::collections::HashMap;

pub const SIDE: usize = 8;
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
pub const SUB: usize = 4;
pub const SUB_CELLS: usize = SUB * SUB;
pub const LAYERS: usize = 3;
pub const N_IN: usize = 10;
pub const N_OUT: usize = 4;
pub const N_POLICY: usize = N_IN * N_OUT + N_OUT;
const K: usize = N_KINDS + N_POLICY;
pub const N_DIRS: usize = 4;
pub const UNDER_MAX: usize = (SIDE_MAX / SUB + 1) * (SIDE_MAX / SUB + 1);

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
const DIRS: [usize; 4] = [NORTH, SOUTH, EAST, WEST];
const FREE: u32 = u32::MAX;

fn opposite(d: usize) -> usize {
    match d {
        NORTH => SOUTH,
        SOUTH => NORTH,
        EAST => WEST,
        _ => EAST,
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

fn rotate(cells: &[u8; CELLS], f: usize, s: usize) -> [u8; CELLS] {
    let mut out = [0u8; CELLS];
    for (i, &c) in cells.iter().enumerate().take(s * s) {
        out[to_world(i, f, s)] = c;
    }
    out
}

fn filled(cells: &[u8; CELLS], s: usize) -> ([u8; CELLS], u16, [u8; 4]) {
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

fn parts_of(cells: &[u8; CELLS], s: usize) -> ([u8; CELLS], usize) {
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

fn keep_largest(cells: &mut [u8; CELLS], s: usize) -> u16 {
    let (label, n) = parts_of(cells, s);
    if n < 2 {
        return 0;
    }
    let mut size = vec![0u16; n + 1];
    let mut mass = vec![0.0f32; n + 1];
    for i in 0..s * s {
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
    for (cell, &l) in cells.iter_mut().zip(&label).take(s * s) {
        if l != 0 && l as usize != keep {
            *cell = 0;
            cut += 1;
        }
    }
    cut
}

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

fn line_of(pos: usize, d: usize, s: usize) -> usize {
    match d {
        NORTH | SOUTH => pos % s,
        _ => pos / s,
    }
}

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

fn open_faces(cells: &[u8; CELLS], s: usize, hard: bool) -> [u8; CELLS] {
    let mut out = [0u8; CELLS];
    for pos in 0..s * s {
        let c = cells[pos];
        if c == 0 || (c == HARD as u8) != hard {
            continue;
        }
        out[pos] = DIRS.iter().filter(|&&d| neighbor(pos, d, s).is_none_or(|q| cells[q] == 0)).count() as u8;
    }
    out
}

fn sight_of(cells: &[u8; CELLS], s: usize) -> [u8; 4] {
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

/// A small set of world cells: a body lies over at most 5x5 of them.
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
    morph_level: Vec<Vec<Vec<f32>>>,
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
        let morph_level = (0..=SIDE_MAX)
            .map(|s| {
                let n = s * s;
                let mut levels: Vec<Vec<f32>> = (0..N_MORPH).map(|_| vec![0.0f32; n + 1]).collect();
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

#[derive(Clone)]
pub struct Body {
    pub cells: [u8; CELLS],
    pub side: u8,
    pub size: u16,
    pub mass: f32,
    pub density: f32,
    pub kinds: [u16; N_KINDS],
    pub tips: [[Tip; SIDE_MAX]; 4],
    pub policy: [f32; N_POLICY],
    pub open_soft: u16,
    pub sight: [u8; 4],
    pub store: f32,
}

impl Body {
    pub fn new(cells: [u8; CELLS], side: usize, policy: [f32; N_POLICY], density: f32) -> Self {
        let mut b = Body { cells, side: side as u8, size: 0, mass: 0.0, density, kinds: [0; N_KINDS], tips: [[Tip::default(); SIDE_MAX]; 4], policy, open_soft: 0, sight: [0; 4], store: STORE };
        b.refresh();
        b
    }
    pub fn empty() -> Self {
        Body::new([0; CELLS], SIDE, [0.0; N_POLICY], 1.0)
    }
    pub fn s(&self) -> usize {
        self.side as usize
    }
    pub fn block_mass(&self, kind: u8) -> f32 {
        self.density * KIND_MASS[kind as usize]
    }
    pub fn matter(&self) -> f64 {
        (1..N_KINDS).map(|k| self.kinds[k] as f64 * CELL_ENERGY as f64 * self.density as f64 * KIND_MASS[k] as f64).sum()
    }
    pub fn refresh(&mut self) {
        self.kinds = [0; N_KINDS];
        for &c in self.cells.iter().take(self.s() * self.s()) {
            self.kinds[c as usize] += 1;
        }
        self.size = (self.s() * self.s()) as u16 - self.kinds[0];
        self.mass = (1..N_KINDS).map(|k| self.kinds[k] as f32 * self.block_mass(k as u8)).sum();
        self.tips = tips_of(&self.cells, self.s());
        self.open_soft = open_faces(&self.cells, self.s(), false).iter().map(|&f| f as u16).sum();
        self.sight = sight_of(&self.cells, self.s());
    }
    pub fn speed(&self) -> f32 {
        if self.mass <= 0.0 { 0.0 } else { self.kinds[MUSCLE] as f32 / self.mass }
    }
    pub fn range(&self) -> usize {
        1 + (self.kinds[SENSOR] as usize).min(EYES)
    }
    pub fn reach(&self, j: usize) -> usize {
        if self.sight[j] == 0 { 0 } else { 1 + (self.sight[j] as usize).min(EYES) }
    }
    pub fn threshold(&self) -> f32 {
        2.0 + BREED * self.mass
    }
    pub fn bite_any(&self) -> u8 {
        DIRS.iter().flat_map(|&d| &self.tips[d][..self.s()]).filter(|t| t.hardness > 1).map(|t| t.force).max().unwrap_or(0)
    }
}

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
    keep_largest(&mut cells, side);
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
    Body::new(cells, side, policy, density)
}

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

pub struct Occ {
    pub sub: Vec<u32>,
    pub crowd: Vec<u16>,
}

impl Occ {
    pub fn new(g: Grid) -> Self {
        Occ { sub: vec![FREE; LAYERS * g.sw * g.sh], crowd: vec![0; LAYERS * g.cells()] }
    }
    pub fn bytes(&self) -> usize {
        self.sub.len() * 4 + self.crowd.len() * 2
    }
    pub fn at(&self, g: Grid, sx: usize, sy: usize, layer: usize) -> u32 {
        self.sub[LAYERS * g.sidx(sx, sy) + layer]
    }
    fn put(&mut self, g: Grid, a: &Agent, pos: usize, v: u32) {
        let (sx, sy) = a.sub_at(g, pos, NORTH, 0);
        let (i, c) = (LAYERS * g.sidx(sx, sy), g.wcell(sx, sy));
        for l in 0..2 {
            self.sub[i + l] = v;
            if v == FREE {
                self.crowd[LAYERS * c + l] -= 1;
            } else {
                self.crowd[LAYERS * c + l] += 1;
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
}

pub struct Agent {
    pub x: usize,
    pub y: usize,
    pub energy: f64,
    pub fat: f64,
    pub age: u32,
    pub turns: u32,
    pub phase: f32,
    pub alive: bool,
    pub water: f32,
    pub breath: f32,
    pub temp: f32,
    pub layer: usize,
    pub genome: Vec<u8>,
    pub keys: Vec<u16>,
    pub gene_ids: Vec<u16>,
    pub body: Body,
    pub facing: u8,
    pub wcells: [u8; CELLS],
    pub tips: [[Tip; SIDE_MAX]; 4],
    pub filled: [u8; CELLS],
    pub n_filled: u16,
    pub bbox: [u8; 4],
    pub open: [u8; CELLS],
    pub open_hard: [u8; CELLS],
}

impl Agent {
    pub fn new(genome: Vec<u8>, keys: Vec<u16>, gene_ids: Vec<u16>, body: Body, facing: u8, energy: f64) -> Agent {
        let mut a = Agent {
            x: 0, y: 0, energy, fat: 0.0, age: 0, turns: 0, phase: 0.0, alive: body.size > 0, water: 1.0, breath: 1.0, temp: 20.0, layer: 0,
            genome, keys, gene_ids, body, facing, wcells: [0; CELLS], tips: [[Tip::default(); SIDE_MAX]; 4], filled: [0; CELLS], n_filled: 0, bbox: [0; 4], open: [0; CELLS], open_hard: [0; CELLS],
        };
        a.reframe();
        a
    }
    pub fn reframe(&mut self) {
        let s = self.body.s();
        self.wcells = rotate(&self.body.cells, self.facing as usize, s);
        self.tips = tips_of(&self.wcells, s);
        let (list, n, bb) = filled(&self.wcells, s);
        self.filled = list;
        self.n_filled = n;
        self.bbox = bb;
        self.open = open_faces(&self.wcells, s, false);
        self.open_hard = open_faces(&self.wcells, s, true);
    }
    pub fn mass(&self) -> f32 {
        self.body.mass
    }
    pub fn cells_held(&self) -> impl Iterator<Item = usize> + '_ {
        self.filled[..self.n_filled as usize].iter().map(|&p| p as usize)
    }
    pub fn sub_at(&self, g: Grid, pos: usize, d: usize, k: usize) -> (usize, usize) {
        let s = self.body.s();
        g.sstep((self.x + pos % s) % g.sw, (self.y + pos / s) % g.sh, d, k)
    }
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
    pub fn here(&self, g: Grid) -> usize {
        let [r0, r1, c0, c1] = self.bbox;
        let (sx, sy) = self.sub_at(g, (r0 + r1) as usize / 2 * self.body.s() + (c0 + c1) as usize / 2, NORTH, 0);
        g.wcell(sx, sy)
    }
    pub fn fits(&self, g: Grid, occ: &Occ, me: u32, d: usize, k: usize) -> bool {
        self.cells_held().all(|p| {
            let (sx, sy) = self.sub_at(g, p, d, k);
            let o = occ.at(g, sx, sy, self.layer);
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
        others += crowd[LAYERS * c + a.layer] as f32 / SUB_CELLS as f32;
    }
    (f, others)
}

fn sense(a: &Agent, g: Grid, food: &[f32], crowd: &[u16]) -> [f32; N_IN] {
    let f = a.facing as usize;
    let dirs = [f, opposite(f), left_of(f), opposite(left_of(f))];
    let mut input = [0.0f32; N_IN];
    input[0] = a.under(g, NORTH, 0).iter().map(|c| food[c]).sum();
    for (j, &d) in dirs.iter().enumerate() {
        let reach = a.body.range();
        let (f1, o1) = look(a, g, d, 1, food, crowd);
        input[1 + j] = f1;
        input[5 + j] = o1;
        for r in 2..=reach {
            let (fr, ob) = look(a, g, d, r, food, crowd);
            input[1 + j] += fr / r as f32;
            input[5 + j] += ob / r as f32;
        }
    }
    input[9] = (a.energy / a.body.threshold() as f64) as f32;
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
    tiles: Vec<usize>, // the world cells a body may stand on
    cfg: Cfg,
    pub k: Stats,
}

impl World {
    pub fn new(cfg: &Cfg) -> World {
        let g = Grid::new(cfg.side, cfg.side);
        let mut rng = Rng(cfg.seed.wrapping_mul(0x9E3779B97F4A7C15) | 1);
        let laws = Laws::new(cfg.seed);
        // The ground bodies stand on: whole tiles of TILE x TILE cells, as many as the target fill
        // asks for, so that the crowd is the control's (e097: a cell a body stands on carries
        // 8.5-10.5 blocks of the 16 it holds).
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
        // A pool of bodies from random genomes, as e063 seeds a world.
        let mut pool: Vec<(Vec<u8>, Body)> = Vec::new();
        while pool.len() < 64 {
            let genome = random_genome(&mut rng);
            let genes = parse_genes(&genome);
            if genes.is_empty() {
                continue;
            }
            let body = develop_genes(&genes, &w.laws);
            if body.size > 0 && (5..=7).contains(&body.s()) {
                pool.push((genome, body));
            }
        }
        let blocks: f32 = pool.iter().map(|(_, b)| b.size as f32).sum::<f32>() / pool.len() as f32;
        // The tiles: enough sub-cells that `bodies` bodies of `blocks` blocks fill `fill` of them.
        let want = (cfg.bodies as f32 * blocks / (cfg.fill * SUB_CELLS as f32)).ceil() as usize;
        let tile = 16usize;
        let n_tiles = (want / (tile * tile)).max(1);
        let per = g.w / tile;
        let mut chosen: Vec<usize> = (0..per * per).collect();
        for i in 0..chosen.len() {
            let j = i + rng.below(chosen.len() - i);
            chosen.swap(i, j);
        }
        for &t in chosen.iter().take(n_tiles) {
            let (tx, ty) = (t % per * tile, t / per * tile);
            for dy in 0..tile {
                for dx in 0..tile {
                    w.tiles.push(g.idx(tx + dx, ty + dy));
                }
            }
        }
        // The bodies, packed into those tiles at random until the target is met.
        let mut tries = 0u64;
        while w.agents.len() < cfg.bodies && tries < 200 * cfg.bodies as u64 {
            tries += 1;
            let (genome, body) = pool[rng.below(pool.len())].clone();
            let genes = parse_genes(&genome);
            let mut a = Agent::new(genome, sorted_keys(&genes), genes.iter().map(Gene::key).collect(), body, rng.below(4) as u8, 1.0);
            let c = w.tiles[rng.below(w.tiles.len())];
            a.x = c % g.w * SUB + rng.below(SUB);
            a.y = c / g.w * SUB + rng.below(SUB);
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
            // Wear: every block of the body rolls (e044).
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
            // 1. Eat: every gut block takes from the cell under it; then the upkeep.
            if off != "eat" {
                let a = &self.agents[i];
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
            // The faces: the air (e066), the breath (e067) and the heat (e072 set A).
            if off != "faces" {
                let a = &self.agents[i];
                let (mut lost, mut drunk) = (0.0f32, 0.0f32);
                let (mut faces, mut ashore) = (0u16, 0u16);
                let (mut kk, mut sum) = (0.0f64, 0.0f64);
                for p in a.cells_held() {
                    let (sx, sy) = a.sub_at(g, p, NORTH, 0);
                    let c = g.wcell(sx, sy);
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
            // 2. Decide.
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
            // 3. Act.
            if off == "move" {
                continue;
            }
            if action == 1 {
                let d = self.agents[i].facing as usize;
                self.push(i, d);
                if self.agents[i].fits(g, &self.occ, i as u32, d, 1) {
                    if stroke(self.agents[i].body.speed(), &mut self.rng) {
                        self.occ.release(g, &self.agents[i]);
                        let (nx, ny) = g.sstep(self.agents[i].x, self.agents[i].y, d, 1);
                        self.agents[i].x = nx;
                        self.agents[i].y = ny;
                        self.occ.claim(g, &self.agents[i], i as u32);
                        self.k.moved += 1;
                        let a = &mut self.agents[i];
                        let cost = (MOVE_COST * a.mass()) as f64;
                        a.energy -= cost.min(a.energy.max(0.0));
                    }
                } else {
                    self.k.blocked += 1;
                }
            } else if action >= 2 {
                let f = self.agents[i].facing as usize;
                let nf = if action == 2 { left_of(f) } else { opposite(left_of(f)) };
                let a = &self.agents[i];
                let (list, n, _) = filled(&rotate(&a.body.cells, nf, a.body.s()), a.body.s());
                let room = list[..n as usize].iter().all(|&p| {
                    let (sx, sy) = a.sub_at(g, p as usize, NORTH, 0);
                    let o = self.occ.at(g, sx, sy, a.layer);
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

    /// The contact physics (e010, e015, e075): what the body presses on when it steps forward.
    /// A block is broken when the face that meets it is softer and the force behind the tip beats it.
    fn push(&mut self, i: usize, d: usize) {
        let g = self.g;
        let opp = opposite(d);
        let mut pressed: Vec<(usize, u8)> = Vec::new();
        let mut breaks: Vec<(usize, usize)> = Vec::new();
        let layer = self.agents[i].layer;
        for p in self.agents[i].cells_held() {
            let (sx, sy) = self.agents[i].sub_at(g, p, d, 1);
            let j = self.occ.at(g, sx, sy, layer);
            if j == FREE || j as usize == i {
                continue;
            }
            let j = j as usize;
            let b = &self.agents[j];
            let (r, col) = ((sy + g.sh - b.y) % g.sh, (sx + g.sw - b.x) % g.sw);
            if r >= b.body.s() || col >= b.body.s() {
                continue;
            }
            let q = r * b.body.s() + col;
            let ha = face_hardness(&self.agents[i].wcells, p, opp, self.agents[i].body.s()) as f32 * self.agents[i].body.density;
            let hb = face_hardness(&b.wcells, q, d, b.body.s()) as f32 * b.body.density;
            let force = self.agents[i].tips[d][line_of(p, d, self.agents[i].body.s())].force;
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

    /// The births, driven at the control's rates (e097's control log): `children` tries a step,
    /// `develops` of them a development the cache cannot answer, and each child placed by the rule
    /// as it stands (the first spot its whole grid fits in, 1..=reach sub-cells along one of the
    /// four rays). A body is taken out for every child placed, so the crowd stays the control's.
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
            // The mate: the bodies within two sub-cells of the parent's box.
            let mut mate = false;
            {
                let a = &self.agents[parent];
                let [r0, r1, c0, c1] = a.bbox;
                let (x0, y0) = (a.x + g.sw + c0 as usize - 2, a.y + g.sh + r0 as usize - 2);
                'cells: for dy in 0..(r1 - r0 + 5) as usize {
                    for dx in 0..(c1 - c0 + 5) as usize {
                        let j = self.occ.at(g, (x0 + dx) % g.sw, (y0 + dy) % g.sh, a.layer);
                        if j == FREE || j as usize == parent {
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
            self.k.mates += mate as u64;
            let mut genome = self.agents[parent].genome.clone();
            mutate(&mut genome, &mut self.rng);
            let genes = parse_genes(&genome);
            if genes.is_empty() {
                continue;
            }
            let gene_ids: Vec<u16> = genes.iter().map(Gene::key).collect();
            let keys = sorted_keys(&genes);
            // The cache: `develops` of the children a step need a development, the rest are answered
            // by a list already developed (e097's control: 59 developments for 133 children).
            let body = if c < developing && self.cfg.off != "develop" {
                let b = develop_genes(&genes, &self.laws);
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
            let (px, py) = (self.agents[parent].x, self.agents[parent].y);
            let reach = self.agents[parent].body.s().max(child.body.s());
            let start = self.rng.below(4);
            let mut spot = None;
            'search: for t in 0..4 {
                let d = DIRS[(start + t) % 4];
                for kk in 1..=reach {
                    let (cx, cy) = g.sstep(px, py, d, kk);
                    child.x = cx;
                    child.y = cy;
                    if child.fits(g, &self.occ, FREE, NORTH, 0) {
                        spot = Some((cx, cy));
                        break 'search;
                    }
                }
            }
            match spot {
                Some((cx, cy)) => {
                    child.x = cx;
                    child.y = cy;
                    // One out for one in: the oldest slot free, or a body taken at random.
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
