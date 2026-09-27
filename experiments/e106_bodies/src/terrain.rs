//! The ground, generated once: height and sea (e061), rock provinces, the soil each allows, and the
//! drainage network every land cell's water follows to the sea.

use crate::noise::{noise, Rng};
use crate::par::CHUNKS;
use crate::Params;
use std::cmp::Reverse;
use std::collections::BinaryHeap;

/// Rock kinds, each a row of what it gives and holds. Names are for the reader only; the world knows the
/// numbers. `a`, `b`: nutrient given a year at the mean rate (x `weather`); `hold`: the water its soil holds
/// against the mean; `hard`: how hard the ground is to dig.
pub const ROCKS: [Rock; 5] = [
    Rock { a: 1.0, b: 0.3, hold: 0.7, hard: 3.0 },  // granite-like: rich in A, poor in B, thin soil
    Rock { a: 0.6, b: 1.5, hold: 1.0, hard: 2.5 },  // basalt-like: rich in B
    Rock { a: 0.4, b: 1.0, hold: 0.6, hard: 2.0 },  // limestone-like: B, drains fast
    Rock { a: 0.3, b: 0.2, hold: 0.5, hard: 1.5 },  // sandstone-like: poor, dry
    Rock { a: 1.2, b: 0.8, hold: 1.5, hard: 1.0 },  // shale-like: rich, holds water, soft
];

pub struct Rock {
    pub a: f64,
    pub b: f64,
    pub hold: f64,
    pub hard: f64,
}

pub const NONE: u32 = u32::MAX;

pub struct Terrain {
    pub n: usize,
    pub elev: Vec<f64>, // m above the sea; negative under it
    pub sea: Vec<bool>,
    pub air: Vec<f64>, // m: the surface the air lies on (0 over the sea)
    pub lat: Vec<f64>, // radians, per row
    pub filled: Vec<f64>, // m: the height water must reach to leave a cell (a lake's spill level)
    pub down: Vec<u32>,   // the cell a land cell's water runs to (NONE on the sea)
    pub order: Vec<u32>,  // land cells, every cell before the one it runs to
    pub slope: Vec<f64>,  // m a cell: the drop to the lowest neighbour
    pub rock: Vec<u8>,
    pub cap: Vec<f64>,      // mm: the water the soil holds
    pub lake_cap: Vec<f64>, // mm: the water a basin holds above the soil before it spills
    /// The land's drainage basins dealt into `par::CHUNKS` groups of about equal size, each group's cells
    /// upstream first: a group's water never reaches another's, so the groups are routed on separate threads.
    pub groups: Vec<Vec<u32>>,
}

impl Terrain {
    pub fn new(p: &Params) -> Self {
        let n = p.size as usize;
        let cells = n * n;
        let h = noise(n, p.seed as u64, p.grain, p.rough, 2.0);
        let mut sorted = h.clone();
        sorted.sort_by(|a, b| a.partial_cmp(b).unwrap());
        let level = sorted[(((1.0 - p.land) * cells as f64) as usize).min(cells - 1)];
        let top = sorted[cells - 1];
        let mut elev: Vec<f64> = h.iter().map(|&v| (v - level) / (top - level) * p.relief).collect();
        let sea: Vec<bool> = elev.iter().map(|&e| e < 0.0).collect();
        // The rows run from lat_lo to lat_hi and back: no edge, every latitude twice.
        let lat: Vec<f64> = (0..n)
            .map(|y| (p.lat_lo + (p.lat_hi - p.lat_lo) * (1.0 - (2.0 * (y as f64 + 0.5) / n as f64 - 1.0).abs())).to_radians())
            .collect();
        let (filled, down, order) = drainage(n, &elev, &sea);
        // A pit in noise is not a basin: real ground is filled by what the water brings. Each is filled to
        // `lake_depth` under its spill level, and is a shallow lake that fills and spills.
        for c in 0..cells {
            if !sea[c] {
                elev[c] = elev[c].max(filled[c] - p.lake_depth);
            }
        }
        let air: Vec<f64> = elev.iter().map(|&e| e.max(0.0)).collect();
        let slope: Vec<f64> = (0..cells)
            .map(|c| if sea[c] { 0.0 } else { nbrs(n, c).iter().map(|&m| (elev[c] - elev[m]).max(0.0)).fold(0.0, f64::max) })
            .collect();
        let rock = provinces(n, p);
        let cap: Vec<f64> = (0..cells)
            .map(|c| if sea[c] { 0.0 } else { p.soil * ROCKS[rock[c] as usize].hold * (0.4 + 1.2 / (1.0 + slope[c] / p.depth_slope)) })
            .collect();
        let lake_cap: Vec<f64> = (0..cells).map(|c| if sea[c] { 0.0 } else { ((filled[c] - elev[c]) * 1000.0).max(0.0) }).collect();
        let groups = basin_groups(&sea, &down, &order);
        Terrain { n, elev, sea, air, lat, filled, down, order, slope, rock, cap, lake_cap, groups }
    }
}

pub fn nbrs(n: usize, c: usize) -> [usize; 4] {
    let (x, y) = (c % n, c / n);
    let (xl, xr) = (if x == 0 { n - 1 } else { x - 1 }, if x + 1 == n { 0 } else { x + 1 });
    let (yu, yd) = (if y == 0 { n - 1 } else { y - 1 }, if y + 1 == n { 0 } else { y + 1 });
    [yu * n + x, yd * n + x, y * n + xr, y * n + xl]
}

/// Priority flood from the coast: every land cell is reached from the lowest way in, so the way it was
/// reached is the way its water leaves, and a basin fills to its spill level before it drains.
fn drainage(n: usize, elev: &[f64], sea: &[bool]) -> (Vec<f64>, Vec<u32>, Vec<u32>) {
    const EPS: f64 = 1e-4; // m: a flat still slopes to its outlet
    let cells = n * n;
    let mut filled = elev.to_vec();
    let mut down = vec![NONE; cells];
    let mut seen: Vec<bool> = sea.to_vec();
    let mut heap = BinaryHeap::new();
    let key = |v: f64| Reverse((v * 1e6) as i64);
    for c in 0..cells {
        if sea[c] {
            continue;
        }
        if let Some(&m) = nbrs(n, c).iter().filter(|&&m| sea[m]).min_by(|&&a, &&b| elev[a].partial_cmp(&elev[b]).unwrap()) {
            down[c] = m as u32;
            seen[c] = true;
            heap.push((key(elev[c]), c as u32));
        }
    }
    let mut popped = Vec::with_capacity(cells);
    while let Some((_, c)) = heap.pop() {
        let c = c as usize;
        popped.push(c as u32);
        for m in nbrs(n, c) {
            if !seen[m] {
                seen[m] = true;
                filled[m] = elev[m].max(filled[c] + EPS);
                down[m] = c as u32;
                heap.push((key(filled[m]), m as u32));
            }
        }
    }
    popped.reverse(); // the last reached is the furthest upstream
    (filled, down, popped)
}

/// Each land cell's basin (the cell whose water enters the sea), the basins dealt largest first to the group
/// with the fewest cells so far; within a group, cells keep the network's upstream-first order.
fn basin_groups(sea: &[bool], down: &[u32], order: &[u32]) -> Vec<Vec<u32>> {
    let mut basin = vec![NONE; sea.len()];
    for &c in order.iter().rev() {
        let c = c as usize;
        let d = down[c] as usize;
        basin[c] = if sea[d] { c as u32 } else { basin[d] };
    }
    let mut size: std::collections::HashMap<u32, usize> = std::collections::HashMap::new();
    for &c in order {
        *size.entry(basin[c as usize]).or_insert(0) += 1;
    }
    let mut basins: Vec<(u32, usize)> = size.into_iter().collect();
    basins.sort_by(|a, b| b.1.cmp(&a.1).then(a.0.cmp(&b.0)));
    let mut load = vec![0usize; CHUNKS];
    let mut group_of: std::collections::HashMap<u32, usize> = std::collections::HashMap::new();
    for (b, s) in basins {
        let g = (0..CHUNKS).min_by_key(|&g| (load[g], g)).unwrap();
        load[g] += s;
        group_of.insert(b, g);
    }
    let mut groups = vec![Vec::new(); CHUNKS];
    for &c in order {
        groups[group_of[&basin[c as usize]]].push(c);
    }
    groups
}

/// Rock provinces: the nearest of `provinces` seeds, with borders that wander by `warp` cells.
fn provinces(n: usize, p: &Params) -> Vec<u8> {
    let mut rng = Rng::new(p.seed as u64 ^ 0x5EED_0F_0C4);
    let k = p.provinces as usize;
    let seeds: Vec<(f64, f64, u8)> = (0..k).map(|_| (rng.f64() * n as f64, rng.f64() * n as f64, rng.below(ROCKS.len()) as u8)).collect();
    let wx = noise(n, p.seed as u64 ^ 0xA11, 64.0, 0.5, 8.0);
    let wy = noise(n, p.seed as u64 ^ 0xB22, 64.0, 0.5, 8.0);
    let nf = n as f64;
    (0..n * n)
        .map(|c| {
            let x = (c % n) as f64 + p.warp * wx[c];
            let y = (c / n) as f64 + p.warp * wy[c];
            let mut best = (f64::MAX, 0u8);
            for &(sx, sy, r) in &seeds {
                let dx = ((x - sx).rem_euclid(nf)).min((sx - x).rem_euclid(nf));
                let dy = ((y - sy).rem_euclid(nf)).min((sy - y).rem_euclid(nf));
                let d = dx * dx + dy * dy;
                if d < best.0 {
                    best = (d, r);
                }
            }
            best.1
        })
        .collect()
}
