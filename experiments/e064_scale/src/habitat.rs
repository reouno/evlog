//! e061's habitats and their measures, ported as they are, with the producers added to what a
//! quarter adds up.

use crate::climate::World;
use crate::plants::Plants;
use std::collections::VecDeque;

pub const TRAVEL: usize = 14; // cells a body travels in a life (e058: 3 in the crowd, 14 in a thin world)
pub const WIDE: usize = 3 * TRAVEL; // a patch a body cannot average away (#68 rule 1)
pub const SHARE: f64 = 0.02; // a habitat counts when it holds this share of the cells
pub const COLD: f64 = 5.0; // C: the quarter's mean under which nothing grows (the base of growing degree days)
pub const HOT: f64 = 20.0; // C
pub const DRY: f64 = 1.0 / 3.0; // the ground's mean fill
pub const WET: f64 = 2.0 / 3.0;
pub const SHALLOW: f64 = 200.0; // m: the sea over the shelf, where light can reach the bottom's layer
pub const POOL: f64 = 500.0; // mm of standing water that makes a land cell a lake
pub const N_HAB: usize = 15;
pub const HAB_NAMES: [&str; N_HAB] = [
    "land_cold_dry", "land_cold_moist", "land_cold_wet",
    "land_mild_dry", "land_mild_moist", "land_mild_wet",
    "land_hot_dry", "land_hot_moist", "land_hot_wet",
    "shallow_cold", "shallow_mild", "shallow_hot",
    "deep_cold", "deep_mild", "deep_hot",
];

/// What a quarter of a year adds up per cell.
pub struct Quarter {
    pub temp: Vec<f64>,
    pub moist: Vec<f64>,
    pub rain: Vec<f64>,
    pub pool: Vec<u32>,
    pub grass: Vec<f64>,
    pub wood: Vec<f64>,
    pub algae: Vec<f64>,
    pub updates: u32,
}

impl Quarter {
    pub fn new(cells: usize) -> Self {
        let z = vec![0.0; cells];
        Quarter { temp: z.clone(), moist: z.clone(), rain: z.clone(), pool: vec![0; cells], grass: z.clone(), wood: z.clone(), algae: z, updates: 0 }
    }
    pub fn clear(&mut self) {
        for v in [&mut self.temp, &mut self.moist, &mut self.rain, &mut self.grass, &mut self.wood, &mut self.algae] {
            v.iter_mut().for_each(|x| *x = 0.0);
        }
        self.pool.iter_mut().for_each(|v| *v = 0);
        self.updates = 0;
    }
    pub fn add(&mut self, w: &World, pl: &Plants, soil: f64) {
        for c in 0..w.temp.len() {
            self.temp[c] += w.temp[c];
            self.rain[c] += w.rain_now[c];
            self.grass[c] += pl.grass[c];
            self.wood[c] += pl.wood[c];
            self.algae[c] += pl.algae[c];
            if !w.sea[c] {
                let g = w.ground[c];
                self.moist[c] += (g / soil).min(1.0);
                if g - soil >= POOL {
                    self.pool[c] += 1;
                }
            }
        }
        self.updates += 1;
    }
    /// The quarter's habitat map (see `HAB_NAMES`).
    pub fn habitats(&self, w: &World) -> Vec<u8> {
        let u = self.updates.max(1) as f64;
        (0..w.temp.len())
            .map(|c| {
                let t = self.temp[c] / u;
                let tb = if t < COLD { 0 } else if t < HOT { 1 } else { 2 };
                if w.sea[c] {
                    if -w.elev[c] < SHALLOW { 9 + tb } else { 12 + tb }
                } else if 2 * self.pool[c] > self.updates {
                    9 + tb
                } else {
                    let m = self.moist[c] / u;
                    let mb = if m < DRY { 0 } else if m < WET { 1 } else { 2 };
                    (tb * 3 + mb) as u8
                }
            })
            .collect()
    }
}

/// The patches of one habitat map: (habitat, width, cells) for every 8-connected patch, where the
/// width is the side of the largest square that fits inside it (2 d - 1 for the deepest cell's
/// chessboard distance d to another habitat).
pub fn patches(map: &[u8], n: usize) -> Vec<(u8, usize, usize)> {
    let cells = n * n;
    let nb8 = |c: usize| {
        let (x, y) = (c % n, c / n);
        let xs = [(x + n - 1) % n, x, (x + 1) % n];
        let ys = [(y + n - 1) % n, y, (y + 1) % n];
        let mut out = [0usize; 8];
        let mut i = 0;
        for &yy in &ys {
            for &xx in &xs {
                if xx != x || yy != y {
                    out[i] = yy * n + xx;
                    i += 1;
                }
            }
        }
        out
    };
    let mut dist = vec![u32::MAX; cells];
    let mut queue = VecDeque::new();
    for c in 0..cells {
        if nb8(c).iter().any(|&m| map[m] != map[c]) {
            dist[c] = 1;
            queue.push_back(c);
        }
    }
    if queue.is_empty() {
        return vec![(map[0], n, cells)];
    }
    while let Some(c) = queue.pop_front() {
        for m in nb8(c) {
            if map[m] == map[c] && dist[m] == u32::MAX {
                dist[m] = dist[c] + 1;
                queue.push_back(m);
            }
        }
    }
    let mut seen = vec![false; cells];
    let mut out = Vec::new();
    let mut stack = Vec::new();
    for s in 0..cells {
        if seen[s] {
            continue;
        }
        seen[s] = true;
        stack.push(s);
        let (mut area, mut deepest) = (0usize, 0u32);
        while let Some(c) = stack.pop() {
            area += 1;
            deepest = deepest.max(dist[c]);
            for m in nb8(c) {
                if !seen[m] && map[m] == map[s] {
                    seen[m] = true;
                    stack.push(m);
                }
            }
        }
        out.push((map[s], (2 * deepest as usize - 1).min(n), area));
    }
    out
}

/// The width of the patch a cell of each habitat lies in, at the median over the cells.
pub fn median_widths(maps: &[Vec<u8>], n: usize) -> [usize; N_HAB] {
    let mut by: Vec<Vec<(usize, usize)>> = vec![Vec::new(); N_HAB];
    for m in maps {
        for (h, width, area) in patches(m, n) {
            by[h as usize].push((width, area));
        }
    }
    let mut out = [0usize; N_HAB];
    for (h, ps) in by.iter_mut().enumerate() {
        ps.sort();
        let total: usize = ps.iter().map(|p| p.1).sum();
        let mut acc = 0;
        for &(width, area) in ps.iter() {
            acc += area;
            if 2 * acc >= total {
                out[h] = width;
                break;
            }
        }
    }
    out
}

pub fn shares(maps: &[Vec<u8>]) -> [f64; N_HAB] {
    let mut s = [0.0; N_HAB];
    let total = maps.iter().map(|m| m.len()).sum::<usize>() as f64;
    for m in maps {
        for &h in m {
            s[h as usize] += 1.0;
        }
    }
    s.iter_mut().for_each(|v| *v /= total);
    s
}

/// Share of cells whose habitat is not the same in every quarter.
pub fn change(maps: &[Vec<u8>]) -> f64 {
    let cells = maps[0].len();
    (0..cells).filter(|&c| maps.iter().any(|m| m[c] != maps[0][c])).count() as f64 / cells as f64
}

/// Share of (cell, quarter) that agree between two years.
pub fn agree(a: &[Vec<u8>], b: &[Vec<u8>]) -> f64 {
    let mut same = 0usize;
    let mut total = 0usize;
    for (ma, mb) in a.iter().zip(b) {
        same += ma.iter().zip(mb).filter(|(x, y)| x == y).count();
        total += ma.len();
    }
    same as f64 / total as f64
}
