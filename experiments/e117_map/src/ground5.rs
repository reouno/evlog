//! e117 (#135): the ground at an animal's grain. The climate, soil and water stay on the cells of 125 m; the ground
//! an animal walks on is drawn at 5 m from them, once: the coarse height made smooth, a detail that grows with the
//! slope, the hollows filled to shallow ponds, and streams where the water a year's rain sends down the fine ground
//! gathers past a brook's flow, cut a little into it. Generated, not a law: nothing here changes as the world runs.

use crate::par;
use crate::terrain::Terrain;
use std::cmp::Reverse;
use std::collections::BinaryHeap;

pub const LAND: u8 = 0;
pub const SEA: u8 = 1;
pub const POND: u8 = 2;
pub const STREAM: u8 = 3;

const DETAIL_M: f64 = 3.0; // m of detail on flat ground
const DETAIL_SLOPE: f64 = 0.12; // and this share of the coarse drop across a coarse cell
const POND_MAX: f64 = 1.0; // m: a hollow deeper than this is raised to it (the noise is not a basin)
const POND_MIN: f64 = 0.5; // m of standing water that makes a pond
const ROUGH: f64 = 0.6; // each finer octave of the detail this strong (real ground is rough at every scale)
const RUNOFF: f64 = 0.7; // share of the rain that runs off the bare ground to the streams
const BROOK: f64 = 0.005; // m3/s: the least flow drawn as a stream (5 litres a second)

pub struct Ground5 {
    pub n: usize,
    pub cell_m: f64,
    pub height: Vec<f32>, // m, below 0 the sea floor
    pub kind: Vec<u8>,
    pub water: Vec<f32>, // m of water over the ground (sea, pond, stream)
    pub flow: Vec<f32>,  // m3/s down a stream cell, 0 elsewhere
}

fn hash(seed: u64, i: i64, j: i64) -> f64 {
    let mut h = seed ^ (i as u64).wrapping_mul(0x9E37_79B9_7F4A_7C15) ^ (j as u64).wrapping_mul(0xC2B2_AE3D_27D4_EB4F);
    h ^= h >> 33;
    h = h.wrapping_mul(0xFF51_AFD7_ED55_8CCD);
    h ^= h >> 33;
    (h >> 11) as f64 / (1u64 << 53) as f64
}

/// Value noise in [-1, 1] at a scale of `l` m, octaves halving down to `fine` m, each half as strong.
fn detail(seed: u64, x: f64, y: f64, l: f64, fine: f64) -> f64 {
    let (mut s, mut w, mut amp, mut l) = (0.0, 0.0, 1.0, l);
    let mut o = 0u64;
    while l >= fine {
        let (fx, fy) = (x / l, y / l);
        let (i, j) = (fx.floor(), fy.floor());
        let (u, v) = (fx - i, fy - j);
        let (u, v) = (u * u * (3.0 - 2.0 * u), v * v * (3.0 - 2.0 * v));
        let (i, j) = (i as i64, j as i64);
        let sd = seed.wrapping_add(o * 7919);
        let a = hash(sd, i, j) * (1.0 - u) + hash(sd, i + 1, j) * u;
        let b = hash(sd, i, j + 1) * (1.0 - u) + hash(sd, i + 1, j + 1) * u;
        s += amp * (2.0 * (a * (1.0 - v) + b * v) - 1.0);
        w += amp;
        amp *= ROUGH;
        l *= 0.5;
        o += 1;
    }
    s / w
}

/// Catmull-Rom through four values.
fn cr(p0: f64, p1: f64, p2: f64, p3: f64, t: f64) -> f64 {
    p1 + 0.5 * t * (p2 - p0 + t * (2.0 * p0 - 5.0 * p1 + 4.0 * p2 - p3 + t * (3.0 * (p1 - p2) + p3 - p0)))
}

/// A coarse field at a point in coarse cells (centres at i + 0.5), smooth, clamped at the border.
fn bicubic(v: &[f64], n: usize, x: f64, y: f64) -> f64 {
    let (fx, fy) = (x - 0.5, y - 0.5);
    let (i, j) = (fx.floor() as i64, fy.floor() as i64);
    let (tx, ty) = (fx - i as f64, fy - j as f64);
    let at = |a: i64, b: i64| v[(b.clamp(0, n as i64 - 1) as usize) * n + a.clamp(0, n as i64 - 1) as usize];
    let row = |b: i64| cr(at(i - 1, b), at(i, b), at(i + 1, b), at(i + 2, b), tx);
    cr(row(j - 1), row(j), row(j + 1), row(j + 2), ty)
}

fn bilinear(v: &[f64], n: usize, x: f64, y: f64) -> f64 {
    let (fx, fy) = ((x - 0.5).clamp(0.0, n as f64 - 1.0), (y - 0.5).clamp(0.0, n as f64 - 1.0));
    let (i, j) = ((fx as usize).min(n - 2), (fy as usize).min(n - 2));
    let (tx, ty) = (fx - i as f64, fy - j as f64);
    let a = v[j * n + i] * (1.0 - tx) + v[j * n + i + 1] * tx;
    let b = v[(j + 1) * n + i] * (1.0 - tx) + v[(j + 1) * n + i + 1] * tx;
    a * (1.0 - ty) + b * ty
}

/// An f32's bits in an order that sorts as the numbers do.
fn key(h: f32) -> u32 {
    let b = h.to_bits();
    if b >> 31 == 1 { !b } else { b | 0x8000_0000 }
}

impl Ground5 {
    /// `k` fine cells a coarse cell; `rain` the coarse cells' mean mm a year.
    pub fn new(t: &Terrain, cell_km: f64, k: usize, rain: &[f64], seed: u64, threads: usize) -> Ground5 {
        let nc = t.n;
        let n = nc * k;
        let cell_m = cell_km * 1000.0 / k as f64;
        // The coarse drop across each coarse cell, for the detail's strength.
        let drop: Vec<f64> = (0..nc * nc)
            .map(|c| crate::terrain::nbrs(nc, c).iter().map(|&m| (t.elev[c] - t.elev[m]).abs()).fold(0.0, f64::max))
            .collect();
        let mut height = vec![0f32; n * n];
        {
            let hs = par::Shared::new(&mut height);
            par::pieces(threads, n, |lo, hi| {
                for y in lo..hi {
                    for x in 0..n {
                        let (cx, cy) = ((x as f64 + 0.5) / k as f64, (y as f64 + 0.5) / k as f64);
                        let base = bicubic(&t.elev, nc, cx, cy);
                        let amp = DETAIL_M + DETAIL_SLOPE * bilinear(&drop, nc, cx, cy);
                        let (mx, my) = ((x as f64 + 0.5) * cell_m, (y as f64 + 0.5) * cell_m);
                        *hs.at(y * n + x) = (base + amp * detail(seed, mx, my, 400.0, 2.0 * cell_m)) as f32;
                    }
                }
            });
        }
        // Priority flood from the sea: each land cell's water leaves by the way it was reached; a hollow fills to
        // its spill level.
        let cells = n * n;
        // The sea is what lies below 0 and is joined to the border; a hollow below 0 inland is ground (a pond).
        let mut kind = vec![LAND; cells];
        {
            let mut stack: Vec<usize> = (0..cells).filter(|&c| {
                let (x, y) = (c % n, c / n);
                (x == 0 || y == 0 || x == n - 1 || y == n - 1) && height[c] < 0.0
            }).collect();
            for &c in &stack {
                kind[c] = SEA;
            }
            while let Some(c) = stack.pop() {
                let (x, y) = (c % n, c / n);
                for (ok, m) in [(x > 0, c.wrapping_sub(1)), (x + 1 < n, c + 1), (y > 0, c.wrapping_sub(n)), (y + 1 < n, c + n)] {
                    if ok && kind[m] != SEA && height[m] < 0.0 {
                        kind[m] = SEA;
                        stack.push(m);
                    }
                }
            }
        }
        let mut filled = height.clone();
        let mut down = vec![u32::MAX; cells];
        let mut order: Vec<u32> = Vec::with_capacity(cells);
        let mut done = vec![false; cells];
        let mut heap = BinaryHeap::new();
        for c in 0..cells {
            let (x, y) = (c % n, c / n);
            let edge = x == 0 || y == 0 || x == n - 1 || y == n - 1;
            if kind[c] == SEA {
                // the sea is reached first: a land cell next to it drains into it
                done[c] = true;
                continue;
            }
            let by_sea = edge || [c.wrapping_sub(1), c + 1, c.wrapping_sub(n), c + n].iter().any(|&m| m < cells && kind[m] == SEA);
            if by_sea {
                done[c] = true;
                heap.push(Reverse((key(height[c]), c as u32)));
            }
        }
        while let Some(Reverse((_, c))) = heap.pop() {
            let c = c as usize;
            order.push(c as u32);
            let (x, y) = (c % n, c / n);
            // eight neighbours, so that water does not run only along the grid; a filled hollow keeps a slope of a
            // millimetre or so a cell towards its outlet, wobbling over some 80 m, so that its water winds its way out
            let (l, r, u, d) = (x > 0, x + 1 < n, y > 0, y + 1 < n);
            let nb = [
                (l, c.wrapping_sub(1)),
                (r, c + 1),
                (u, c.wrapping_sub(n)),
                (d, c + n),
                (l && u, c.wrapping_sub(n + 1)),
                (r && u, c.wrapping_sub(n).wrapping_add(1)),
                (l && d, (c + n).wrapping_sub(1)),
                (r && d, c + n + 1),
            ];
            for (ok, m) in nb {
                if ok && !done[m] {
                    done[m] = true;
                    let wobble = 0.5 + 0.5 * (detail(seed ^ 0xF1A7, (m % n) as f64 * cell_m, (m / n) as f64 * cell_m, 80.0, 20.0) + 1.0);
                    filled[m] = filled[m].max(filled[c] + (0.001 * wobble) as f32);
                    down[m] = c as u32;
                    heap.push(Reverse((key(filled[m]), m as u32)));
                }
            }
        }
        // A hollow keeps at most POND_MAX of water; deeper than POND_MIN it is a pond.
        let mut water = vec![0f32; cells];
        for c in 0..cells {
            if kind[c] == SEA {
                water[c] = -height[c];
                continue;
            }
            let d = (filled[c] - height[c]) as f64;
            if d > POND_MAX {
                height[c] = filled[c] - POND_MAX as f32;
            }
            let d = (filled[c] - height[c]) as f64;
            if d > POND_MIN {
                kind[c] = POND;
                water[c] = d as f32;
            }
        }
        // The year's runoff gathered down the fine ground: m3 a year, then m3/s.
        let area = cell_m * cell_m;
        let mut acc: Vec<f64> = (0..cells)
            .map(|c| {
                if kind[c] == SEA {
                    return 0.0;
                }
                let (cx, cy) = (((c % n) as f64 + 0.5) / k as f64, ((c / n) as f64 + 0.5) / k as f64);
                bilinear(rain, nc, cx, cy).max(0.0) / 1000.0 * RUNOFF * area
            })
            .collect();
        // Water goes down the steepest way of the filled ground (its own slope where nothing is filled, the
        // millimetres towards the outlet where it is): every step is lower, so no water goes round. The flood's
        // own way (`down`) would draw straight lines across every filled hollow.
        let steep: Vec<u32> = (0..cells)
            .map(|c| {
                if kind[c] == SEA {
                    return u32::MAX;
                }
                let (x, y) = (c % n, c / n);
                let (mut best, mut to) = (0.0f64, down[c]);
                for (dx, dy) in [(-1i64, 0i64), (1, 0), (0, -1), (0, 1), (-1, -1), (1, -1), (-1, 1), (1, 1)] {
                    let (mx, my) = (x as i64 + dx, y as i64 + dy);
                    if mx < 0 || my < 0 || mx >= n as i64 || my >= n as i64 {
                        continue;
                    }
                    let m = my as usize * n + mx as usize;
                    let drop = (filled[c] - filled[m]) as f64 / if dx != 0 && dy != 0 { std::f64::consts::SQRT_2 } else { 1.0 };
                    let drop = if kind[m] == SEA { drop.max(1e-9) } else { drop };
                    if drop > best {
                        best = drop;
                        to = m as u32;
                    }
                }
                to
            })
            .collect();
        // highest first, so that a cell has all it gathers before it passes it on
        let mut by_height: Vec<u32> = order.clone();
        by_height.sort_by(|&a, &b| filled[b as usize].partial_cmp(&filled[a as usize]).unwrap());
        for &c in &by_height {
            let d = steep[c as usize];
            if d != u32::MAX && kind[d as usize] != SEA {
                acc[d as usize] += acc[c as usize];
            }
        }
        let year_s = 365.0 * 86_400.0;
        let mut flow = vec![0f32; cells];
        for c in 0..cells {
            let q = acc[c] / year_s;
            if kind[c] == LAND && q >= BROOK {
                kind[c] = STREAM;
                // a channel cut by its flow: some 5 cm deep at a brook, 40 cm at a cubic metre a second
                let depth = 0.4 * q.powf(0.4);
                height[c] -= depth as f32;
                water[c] = depth as f32;
                flow[c] = q as f32;
            } else if kind[c] == POND {
                flow[c] = q as f32;
            }
        }
        Ground5 { n, cell_m, height, kind, water, flow }
    }

    /// Writes `<prefix>_ground5.bin` (height f32, water f32, flow f32, kind u8, each n x n, rows south to north) and
    /// its `.json`.
    pub fn write(&self, prefix: &str) {
        use std::io::Write;
        let mut f = std::io::BufWriter::new(std::fs::File::create(format!("{prefix}_ground5.bin")).unwrap());
        for v in [&self.height, &self.water, &self.flow] {
            for x in v.iter() {
                f.write_all(&x.to_le_bytes()).unwrap();
            }
        }
        f.write_all(&self.kind).unwrap();
        f.flush().unwrap();
        let count = |k: u8| self.kind.iter().filter(|&&v| v == k).count();
        std::fs::write(
            format!("{prefix}_ground5.json"),
            format!(
                "{{\"n\":{},\"cell_m\":{},\"parts\":[\"height:f32\",\"water:f32\",\"flow:f32\",\"kind:u8\"],\"kinds\":[\"land\",\"sea\",\"pond\",\"stream\"],\"counts\":[{},{},{},{}]}}\n",
                self.n,
                self.cell_m,
                count(LAND),
                count(SEA),
                count(POND),
                count(STREAM)
            ),
        )
        .unwrap();
    }
}
