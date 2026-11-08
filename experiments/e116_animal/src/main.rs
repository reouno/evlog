//! e116: the speed of a world at the size of an animal - a prototype (#135). Not a world: no climate, no water,
//! no chemistry, and a placeholder for the mind. It measures what animals at their own size cost when time is
//! continuous and each animal decides at its own pace, and it shows them on the screen.
//!
//!     e116_animal <prefix> key=value ...
//!
//! Keys: side (m), cell (m), n (founders), days, bench (0/1: fixed animals, no births, deaths or kills),
//! hunters (share of founders that chase), seed, frame (s a viewer frame).
//! Writes <prefix>_log.csv (a row a day) and <prefix>_sum.csv; with EVLOG_VIEW set, the viewer's frames, one
//! a `frame` seconds (the viewer's step is the frame's number).

use std::cmp::Reverse;
use std::collections::BinaryHeap;
use std::io::Write;
use std::time::Instant;

// ---------------------------------------------------------------- numbers of the prototype

const DAY: f64 = 86_400.0;
const YEAR: f64 = 365.0 * DAY;
const BMR: f64 = 3.4; // W kg^-0.75 (Kleiber)
const COT: f64 = 10.7; // J kg^-1 m^-1 at 1 kg, falling as m^-0.32
const GRAZE: f64 = 0.1 / DAY; // kg of dry grass a s, kg^-0.75
const GRASS_J: f64 = 9e6; // J a kg of dry grass, what a gut takes from it
const FLESH_J: f64 = 4e6; // J a kg of a body eaten
const STORE: f64 = 3e7; // J kg^-0.75: what a body holds (some 100 days of its rest)
const LIFE: f64 = 5.0 * YEAR;
const K_GRASS: f64 = 0.15; // kg a m2 of grass on open, fertile ground
const R_GRASS: f64 = 2.0 / YEAR; // its growth rate, logistic
const SIGHT: f64 = 40.0; // m kg^-1/3
const LEN: f64 = 0.25; // m kg^-1/3: a body's length
const STRIDE: f64 = 20.0; // m an animal goes between decisions at most
const IDLE: f64 = 600.0; // s: the longest it goes without one
const CLOSE: f64 = 1.0; // s between decisions while another is near
const BUCKET: f64 = 50.0; // m

const NI: usize = 11; // bias, grass, its slope x y, the nearest larger (dx dy near), smaller (dx dy near), energy
const NO: usize = 3; // move x, move y, bite
const NW: usize = NI * NO;

// ---------------------------------------------------------------- random numbers and noise

struct Rng(u64);
impl Rng {
    fn new(seed: u64) -> Self {
        Rng(seed.wrapping_mul(0x9E37_79B9_7F4A_7C15) | 1)
    }
    fn u64(&mut self) -> u64 {
        let mut x = self.0;
        x ^= x >> 12;
        x ^= x << 25;
        x ^= x >> 27;
        self.0 = x;
        x.wrapping_mul(0x2545_F491_4F6C_DD1D)
    }
    fn f(&mut self) -> f64 {
        (self.u64() >> 11) as f64 / (1u64 << 53) as f64
    }
    fn normal(&mut self) -> f64 {
        let (u, v) = (self.f().max(1e-300), self.f());
        (-2.0 * u.ln()).sqrt() * (std::f64::consts::TAU * v).cos()
    }
}

fn hash(seed: u64, i: i64, j: i64) -> f64 {
    let mut h = seed ^ (i as u64).wrapping_mul(0x9E37_79B9_7F4A_7C15) ^ (j as u64).wrapping_mul(0xC2B2_AE3D_27D4_EB4F);
    h ^= h >> 33;
    h = h.wrapping_mul(0xFF51_AFD7_ED55_8CCD);
    h ^= h >> 33;
    (h >> 11) as f64 / (1u64 << 53) as f64
}

/// Smooth value noise in [0, 1] at a scale of `l` m, three octaves.
fn noise(seed: u64, x: f64, y: f64, l: f64) -> f64 {
    let mut s = 0.0;
    let mut w = 0.0;
    for o in 0..3 {
        let k = (1 << o) as f64;
        let (fx, fy) = (x * k / l, y * k / l);
        let (i, j) = (fx.floor(), fy.floor());
        let (u, v) = (fx - i, fy - j);
        let (u, v) = (u * u * (3.0 - 2.0 * u), v * v * (3.0 - 2.0 * v));
        let (i, j) = (i as i64, j as i64);
        let sd = seed.wrapping_add(o as u64 * 7919);
        let a = hash(sd, i, j) * (1.0 - u) + hash(sd, i + 1, j) * u;
        let b = hash(sd, i, j + 1) * (1.0 - u) + hash(sd, i + 1, j + 1) * u;
        s += (a * (1.0 - v) + b * v) / k;
        w += 1.0 / k;
    }
    s / w
}

// ---------------------------------------------------------------- the ground

struct Ground {
    n: usize,
    cell: f64,
    elev: Vec<f32>, // m, below 0 the sea
    tree: Vec<f32>, // m: the height of the tree on the cell, 0 none
    cap: Vec<f32>,  // kg a m2: what the grass grows back to
    grass: Vec<f32>, // kg a m2 at `seen`
    seen: Vec<f32>, // s: when the grass was last worked out
}

impl Ground {
    fn new(side: f64, cell: f64, seed: u64) -> Ground {
        let n = (side / cell).round() as usize;
        let mut g = Ground { n, cell, elev: vec![0.0; n * n], tree: vec![0.0; n * n], cap: vec![0.0; n * n], grass: vec![0.0; n * n], seen: vec![0.0; n * n] };
        let half = side / 2.0;
        for j in 0..n {
            for i in 0..n {
                let (x, y) = ((i as f64 + 0.5) * cell, (j as f64 + 0.5) * cell);
                let r = ((x - half).powi(2) + (y - half).powi(2)).sqrt() / (0.45 * side);
                let hill = noise(seed, x, y, side / 3.0);
                let e = (1.0 - r * r) * 120.0 + (hill - 0.5) * 160.0 + (noise(seed + 5, x, y, 300.0) - 0.5) * 20.0;
                let c = j * n + i;
                g.elev[c] = e as f32;
                if e <= 0.0 {
                    continue;
                }
                let wood = noise(seed + 1, x, y, 600.0);
                let shade = if wood > 0.55 && hash(seed + 2, i as i64, j as i64) < (wood - 0.55) * 4.0 { 1.0 } else { 0.0 };
                if shade > 0.0 {
                    g.tree[c] = (8.0 + 17.0 * hash(seed + 3, i as i64, j as i64)) as f32;
                }
                let fert = 0.4 + 0.6 * noise(seed + 4, x, y, 400.0);
                g.cap[c] = (K_GRASS * fert * (1.0 - 0.7 * shade)) as f32;
                g.grass[c] = g.cap[c] * 0.8;
            }
        }
        g
    }
    fn at(&self, x: f64, y: f64) -> Option<usize> {
        let (i, j) = ((x / self.cell).floor(), (y / self.cell).floor());
        if i < 0.0 || j < 0.0 || i >= self.n as f64 || j >= self.n as f64 {
            return None;
        }
        Some(j as usize * self.n + i as usize)
    }
    fn land(&self, x: f64, y: f64) -> bool {
        self.at(x, y).is_some_and(|c| self.elev[c] > 0.0)
    }
    /// The grass on a cell now: logistic regrowth since it was last seen, worked out when it is read.
    fn grass(&mut self, c: usize, t: f64) -> f64 {
        let k = self.cap[c] as f64;
        if k <= 0.0 {
            return 0.0;
        }
        let f0 = (self.grass[c] as f64).max(0.01 * k);
        let dt = t - self.seen[c] as f64;
        let f = k / (1.0 + (k / f0 - 1.0) * (-R_GRASS * dt).exp());
        self.grass[c] = f as f32;
        self.seen[c] = t as f32;
        f
    }
    fn peek(&self, x: f64, y: f64, t: f64) -> f64 {
        let Some(c) = self.at(x, y) else { return 0.0 };
        let k = self.cap[c] as f64;
        if k <= 0.0 {
            return 0.0;
        }
        let f0 = (self.grass[c] as f64).max(0.01 * k);
        k / (1.0 + (k / f0 - 1.0) * (-R_GRASS * (t - self.seen[c] as f64)).exp())
    }
}

// ---------------------------------------------------------------- animals

#[derive(Clone)]
struct Body {
    id: u32,
    line: u32,
    alive: bool,
    x: f64,
    y: f64,
    vx: f64,
    vy: f64,
    t0: f64, // when it last decided: it is at x + vx (t - t0)
    next: f64,
    ver: u32,
    m: f64,
    e: f64,
    born: f64,
    w: [f32; NW],
    bucket: usize,
    ate_grass: f64,
    ate_flesh: f64,
}

impl Body {
    fn pos(&self, t: f64) -> (f64, f64) {
        (self.x + self.vx * (t - self.t0), self.y + self.vy * (t - self.t0))
    }
    fn cap(&self) -> f64 {
        STORE * self.m.powf(0.75)
    }
    fn sight(&self) -> f64 {
        SIGHT * self.m.cbrt()
    }
    fn len(&self) -> f64 {
        LEN * self.m.cbrt()
    }
}

/// When two straight paths first come within `r` of each other after now (`dx`, `dy` from a to b now, `ux`,
/// `uy` b's velocity less a's), or None.
fn meet(dx: f64, dy: f64, ux: f64, uy: f64, r: f64) -> Option<f64> {
    let c = dx * dx + dy * dy - r * r;
    if c <= 0.0 {
        return Some(0.0);
    }
    let a = ux * ux + uy * uy;
    let b = 2.0 * (dx * ux + dy * uy);
    if a <= 0.0 || b >= 0.0 {
        return None;
    }
    let disc = b * b - 4.0 * a * c;
    if disc < 0.0 {
        return None;
    }
    Some((-b - disc.sqrt()) / (2.0 * a))
}

struct P {
    side: f64,
    cell: f64,
    n: usize,
    days: f64,
    bench: bool,
    hunters: f64,
    seed: u64,
    frame: f64,
    density: f64, // founders a km2 of land, when above 0 (sets `n`)
}

impl P {
    fn parse(args: &[String]) -> P {
        let mut p = P { side: 4000.0, cell: 5.0, n: 300, days: 730.0, bench: false, hunters: 0.05, seed: 1, frame: 1.0, density: 0.0 };
        for a in args {
            let (k, v) = a.split_once('=').unwrap_or_else(|| panic!("key=value, not {a}"));
            let f: f64 = v.parse().unwrap_or_else(|_| panic!("{a}: not a number"));
            match k {
                "side" => p.side = f,
                "cell" => p.cell = f,
                "n" => p.n = f as usize,
                "days" => p.days = f,
                "bench" => p.bench = f > 0.0,
                "hunters" => p.hunters = f,
                "seed" => p.seed = f as u64,
                "frame" => p.frame = f,
                "density" => p.density = f,
                _ => panic!("unknown key {k}"),
            }
        }
        p
    }
}

#[derive(Default, Clone)]
struct Count {
    decisions: u64,
    close: u64,
    notices: u64,
    births: u64,
    hunger: u64,
    age: u64,
    killed: u64,
    animal_s: f64,
}

struct World {
    p: P,
    g: Ground,
    b: Vec<Body>,
    free: Vec<usize>,
    nb: usize, // buckets a side
    buckets: Vec<Vec<u32>>,
    q: BinaryHeap<Reverse<(u64, u32, u32)>>, // ms, index, version
    rng: Rng,
    next_id: u32,
    c: Count,
    died: Vec<(u32, u8)>,
    born: Vec<(u32, u32)>,
}

fn ms(t: f64) -> u64 {
    (t * 1000.0).round() as u64
}

impl World {
    fn new(mut p: P) -> World {
        let g = Ground::new(p.side, p.cell, p.seed);
        if p.density > 0.0 {
            let land = g.elev.iter().filter(|&&e| e > 0.0).count() as f64 * g.cell * g.cell / 1e6;
            p.n = (p.density * land).round() as usize;
        }
        let nb = (p.side / BUCKET).ceil() as usize;
        let mut w = World { rng: Rng::new(p.seed), p, g, b: Vec::new(), free: Vec::new(), nb, buckets: vec![Vec::new(); nb * nb], q: BinaryHeap::new(), next_id: 1, c: Count::default(), died: Vec::new(), born: Vec::new() };
        let mut placed = 0;
        while placed < w.p.n {
            let (x, y) = (w.rng.f() * w.p.side, w.rng.f() * w.p.side);
            if !w.g.land(x, y) {
                continue;
            }
            let hunter = w.rng.f() < w.p.hunters;
            let m = if hunter { 5.0 * 8f64.powf(w.rng.f()) } else { 2.0 * 30f64.powf(w.rng.f()) };
            let mut genes = [0f32; NW];
            for g in genes.iter_mut() {
                *g = (0.3 * w.rng.normal()) as f32;
            }
            // The founders' placeholder minds (#131 replaces them): up the grass's slope and stop where it is
            // thick; away from a larger body; a hunter towards a smaller one, biting.
            let o = |out: usize, inp: usize| out * NI + inp;
            genes[o(0, 2)] += 3.0;
            genes[o(1, 3)] += 3.0;
            genes[o(0, 4)] -= 3.0;
            genes[o(1, 5)] -= 3.0;
            genes[o(2, 0)] -= 1.0;
            if hunter {
                genes[o(0, 7)] += 4.0;
                genes[o(1, 8)] += 4.0;
                genes[o(2, 0)] += 2.0;
            }
            let id = w.next_id;
            let (next, born) = (w.rng.f() * 60.0, -w.rng.f() * LIFE * 0.5);
            w.add(Body { id, line: id, alive: true, x, y, vx: 0.0, vy: 0.0, t0: 0.0, next, ver: 0, m, e: 0.0, born, w: genes, bucket: 0, ate_grass: 0.0, ate_flesh: 0.0 });
            let i = w.b.len() - 1;
            w.b[i].e = 0.6 * w.b[i].cap();
            placed += 1;
        }
        w
    }

    fn bucket_of(&self, x: f64, y: f64) -> usize {
        let i = ((x / BUCKET).floor().max(0.0) as usize).min(self.nb - 1);
        let j = ((y / BUCKET).floor().max(0.0) as usize).min(self.nb - 1);
        j * self.nb + i
    }

    fn add(&mut self, mut body: Body) -> usize {
        self.next_id = self.next_id.max(body.id + 1);
        body.bucket = self.bucket_of(body.x, body.y);
        let i = if let Some(i) = self.free.pop() {
            self.b[i] = body;
            i
        } else {
            self.b.push(body);
            self.b.len() - 1
        };
        self.buckets[self.b[i].bucket].push(i as u32);
        let (t, v) = (self.b[i].next, self.b[i].ver);
        self.q.push(Reverse((ms(t), i as u32, v)));
        i
    }

    fn remove(&mut self, i: usize, cause: u8) {
        let bk = self.b[i].bucket;
        if let Some(k) = self.buckets[bk].iter().position(|&j| j as usize == i) {
            self.buckets[bk].swap_remove(k);
        }
        self.b[i].alive = false;
        self.b[i].ver += 1;
        self.died.push((self.b[i].id, cause));
        self.free.push(i);
    }

    /// The bodies within `r` of (x, y) at time t (as they are on their paths), with their distances.
    fn near(&self, x: f64, y: f64, r: f64, t: f64, me: usize, out: &mut Vec<(usize, f64, f64, f64)>) {
        out.clear();
        let reach = r + STRIDE;
        let (i0, i1) = (((x - reach) / BUCKET).floor().max(0.0) as usize, (((x + reach) / BUCKET).floor().max(0.0) as usize).min(self.nb - 1));
        let (j0, j1) = (((y - reach) / BUCKET).floor().max(0.0) as usize, (((y + reach) / BUCKET).floor().max(0.0) as usize).min(self.nb - 1));
        for j in j0..=j1 {
            for i in i0..=i1 {
                for &k in &self.buckets[j * self.nb + i] {
                    let k = k as usize;
                    if k == me {
                        continue;
                    }
                    let (bx, by) = self.b[k].pos(t);
                    let (dx, dy) = (bx - x, by - y);
                    let d = (dx * dx + dy * dy).sqrt();
                    if d <= r {
                        out.push((k, dx, dy, d));
                    }
                }
            }
        }
    }

    /// One animal's decision at time t.
    fn decide(&mut self, i: usize, t: f64, scratch: &mut Vec<(usize, f64, f64, f64)>) {
        self.c.decisions += 1;
        let dt = t - self.b[i].t0;
        let (mut x, mut y) = self.b[i].pos(t);
        let (vx, vy) = (self.b[i].vx, self.b[i].vy);
        let moved = (vx * vx + vy * vy).sqrt() * dt;
        if !self.g.land(x, y) {
            // it walked to the shore: it stopped there
            x = self.b[i].x;
            y = self.b[i].y;
        }
        let m = self.b[i].m;
        let cap = self.b[i].cap();
        self.c.animal_s += dt;
        // what it spent, and what it grazed if it stood
        let mut e = self.b[i].e - BMR * m.powf(0.75) * dt - COT * m.powf(0.68) * moved;
        if moved == 0.0 {
            if let Some(c) = self.g.at(x, y) {
                let area = self.g.cell * self.g.cell;
                let have = self.g.grass(c, t) * area;
                let room = ((cap - e) / GRASS_J).max(0.0);
                let eat = (GRAZE * m.powf(0.75) * dt).min(0.9 * have).min(room);
                self.g.grass[c] -= (eat / area) as f32;
                e += eat * GRASS_J;
                self.b[i].ate_grass += eat;
            }
        }
        if self.p.bench {
            e = e.max(0.5 * cap);
        } else if e <= 0.0 {
            self.c.hunger += 1;
            self.remove(i, 0);
            return;
        } else if t - self.b[i].born > LIFE {
            self.c.age += 1;
            self.remove(i, 1);
            return;
        }
        self.b[i].e = e;
        // what it senses
        let sight = self.b[i].sight();
        let len = self.b[i].len();
        self.near(x, y, sight, t, i, scratch);
        let g_here = self.g.peek(x, y, t) / K_GRASS;
        let gx = (self.g.peek(x + 10.0, y, t) - self.g.peek(x - 10.0, y, t)) / K_GRASS * 5.0;
        let gy = (self.g.peek(x, y + 10.0, t) - self.g.peek(x, y - 10.0, t)) / K_GRASS * 5.0;
        let (mut big, mut small) = (None::<(usize, f64, f64, f64)>, None::<(usize, f64, f64, f64)>);
        let mut close = false;
        for &(k, dx, dy, d) in scratch.iter() {
            let o = &self.b[k];
            if d < 10.0 * len + 5.0 {
                close = true;
            }
            if o.m > m {
                if big.map_or(true, |b| d < b.3) {
                    big = Some((k, dx, dy, d));
                }
            } else if small.map_or(true, |s| d < s.3) {
                small = Some((k, dx, dy, d));
            }
        }
        let dir = |n: Option<(usize, f64, f64, f64)>| match n {
            Some((_, dx, dy, d)) => (dx / d.max(1e-9), dy / d.max(1e-9), 1.0 / (1.0 + d / len)),
            None => (0.0, 0.0, 0.0),
        };
        let (bx, by, bn) = dir(big);
        let (sx, sy, sn) = dir(small);
        let inp = [1.0, g_here, gx, gy, bx * bn.sqrt(), by * bn.sqrt(), bn, sx, sy, sn, e / cap];
        let mut out = [0.0f64; NO];
        for (o, v) in out.iter_mut().enumerate() {
            *v = (0..NI).map(|k| self.b[i].w[o * NI + k] as f64 * inp[k]).sum();
        }
        // a bite at contact on a body under 2/3 of its mass kills and eats it
        if !self.p.bench && out[2] > 0.0 {
            if let Some((k, _, _, d)) = small {
                if d < 0.5 * (len + self.b[k].len()) + 0.3 && self.b[k].m < 2.0 / 3.0 * m {
                    let gain = (self.b[k].m * FLESH_J).min((cap - self.b[i].e).max(0.0));
                    self.b[i].e += gain;
                    self.b[i].ate_flesh += self.b[k].m;
                    self.c.killed += 1;
                    self.remove(k, 2);
                }
            }
        }
        // its move
        let vmax = 5.0 * m.powf(0.17);
        let (ux, uy) = (out[0], out[1]);
        let u = (ux * ux + uy * uy).sqrt();
        let s = vmax * u.tanh();
        let (nvx, nvy) = if s < 0.1 * vmax { (0.0, 0.0) } else { (s * ux / u, s * uy / u) };
        // a birth when its store is full
        if !self.p.bench && self.b[i].e >= cap {
            self.b[i].e -= 0.6 * cap;
            let mut child = self.b[i].clone();
            for g in child.w.iter_mut() {
                if self.rng.f() < 0.1 {
                    *g += (0.2 * self.rng.normal()) as f32;
                }
            }
            child.m = (m * (0.1 * self.rng.normal()).exp()).clamp(1.0, 200.0);
            child.id = self.next_id;
            child.x = x + self.rng.normal() * len;
            child.y = y + self.rng.normal() * len;
            if !self.g.land(child.x, child.y) {
                child.x = x;
                child.y = y;
            }
            child.vx = 0.0;
            child.vy = 0.0;
            child.t0 = t;
            child.next = t + 1.0;
            child.ver = 0;
            child.e = 0.3 * child.cap();
            child.born = t;
            child.ate_grass = 0.0;
            child.ate_flesh = 0.0;
            let (cid, pid) = (child.id, self.b[i].id);
            self.add(child);
            self.born.push((cid, pid));
            self.c.births += 1;
        }
        // when it decides next
        let speed = (nvx * nvx + nvy * nvy).sqrt();
        let mut next = if close {
            self.c.close += 1;
            CLOSE
        } else if speed > 0.0 {
            (STRIDE / speed).min(IDLE)
        } else if self.g.at(x, y).is_some() {
            let have = self.g.peek(x, y, t) * self.g.cell * self.g.cell;
            (0.7 * have / (GRAZE * m.powf(0.75))).clamp(10.0, IDLE)
        } else {
            IDLE
        };
        // another coming into sight, its own or the other's, sets an earlier decision for whoever sees
        for &(k, dx, dy, _) in scratch.iter() {
            let o = &self.b[k];
            if !o.alive {
                continue;
            }
            let (ux, uy) = (o.vx - nvx, o.vy - nvy);
            if let Some(tm) = meet(dx, dy, ux, uy, sight) {
                if tm > 0.0 {
                    next = next.min(tm.max(CLOSE));
                }
            }
            let osight = o.sight();
            if let Some(tm) = meet(-dx, -dy, -ux, -uy, osight) {
                if tm > 0.0 && t + tm < o.next {
                    let nt = t + tm.max(CLOSE);
                    let o = &mut self.b[k];
                    // its path is fixed until then: rebase it so the next decision reads from where it is
                    o.next = nt;
                    o.ver += 1;
                    self.q.push(Reverse((ms(nt), k as u32, o.ver)));
                    self.c.notices += 1;
                }
            }
        }
        let bnew = self.bucket_of(x, y);
        let b = &mut self.b[i];
        b.x = x;
        b.y = y;
        b.vx = nvx;
        b.vy = nvy;
        b.t0 = t;
        b.next = t + next;
        b.ver += 1;
        let (old, ver, nt) = (b.bucket, b.ver, b.next);
        if old != bnew {
            if let Some(k) = self.buckets[old].iter().position(|&j| j as usize == i) {
                self.buckets[old].swap_remove(k);
            }
            self.buckets[bnew].push(i as u32);
            self.b[i].bucket = bnew;
        }
        self.q.push(Reverse((ms(nt), i as u32, ver)));
    }
}

// ---------------------------------------------------------------- the viewer

const SUB: usize = 64;

fn body_shape(hunter: bool) -> Vec<u8> {
    // A placeholder animal: a trunk on four legs with a head, gut-coloured for a grazer, muscle for a hunter.
    let side = 8;
    let mut v = vec![0u8; side * side * side];
    let k = if hunter { 2 } else { 4 };
    let mut put = |x: usize, y: usize, z: usize, c: u8| v[(z * side + y) * side + x] = c;
    for x in 1..7 {
        for y in 2..6 {
            for z in 3..6 {
                put(x, y, z, k);
            }
        }
    }
    for (x, y) in [(1, 2), (1, 5), (6, 2), (6, 5)] {
        for z in 0..3 {
            put(x, y, z, 1);
        }
    }
    for y in 3..5 {
        for z in 5..8 {
            put(7, y, z, 3);
        }
    }
    v
}

fn main() {
    let args: Vec<String> = std::env::args().collect();
    let prefix = args.get(1).expect("e116_animal <prefix> key=value ...").clone();
    let p = P::parse(&args[2..]);
    let wall = Instant::now();
    let mut w = World::new(p);
    let n = w.g.n;
    let land = w.g.elev.iter().filter(|&&e| e > 0.0).count() as f64 * w.g.cell * w.g.cell / 1e6;
    eprintln!("e116: {:.1} km side, {n}x{n} cells of {} m, {land:.1} km2 of land, {} founders ({:.0} a km2), {:.1} s", w.p.side / 1e3, w.g.cell, w.p.n, w.p.n as f64 / land, wall.elapsed().as_secs_f64());

    // the viewer: nothing unless EVLOG_VIEW is set
    let height: Vec<f32> = w.g.elev.iter().map(|&e| if e > 0.0 { e / w.g.cell as f32 / 0.28 } else { -3.0 * (-e / 20.0).min(1.0) }).collect();
    let band = vec![0u8; n * n];
    let params = format!("{{\"side\":{},\"cell\":{},\"n\":{},\"bench\":{},\"hunters\":{},\"seed\":{},\"frame\":{},\"view_size\":{}}}", w.p.side, w.g.cell, w.p.n, w.p.bench as u8, w.p.hunters, w.p.seed, w.p.frame, 2.0 * LEN / w.g.cell * 0.5);
    let mut view = viewer::View::from_env_ext(
        &prefix,
        viewer::Init {
            experiment: "e116_animal",
            w: n,
            h: n,
            sub: SUB,
            height: &height,
            band: &band,
            layers: vec![viewer::LayerSpec::new("water", 4.0, viewer::Scale::Sqrt), viewer::LayerSpec::new("plant", 40.0, viewer::Scale::Sqrt)],
            globals: vec!["day", "pop"],
            blocks: vec!["empty", "hard", "muscle", "sensor", "digestive", "fat", "glue"],
            deaths: vec!["hunger", "age", "eaten"],
            births: true,
            params,
        },
        viewer::Ext { voxels: true, fields: vec![("mass", "f32", None), ("animals", "f32", None), ("lifespan", "u16", None)], diets: vec!["grass", "meat", "nothing yet"] },
    );
    let shapes = [body_shape(false), body_shape(true)];
    let water: Vec<f64> = w.g.elev.iter().map(|&e| if e > 0.0 { 0.0 } else { 1.0 + 3.0 * (-e as f64 / 20.0).min(1.0) }).collect();
    let mut plant = vec![0.0f64; n * n];
    let mut plant_t = -1.0f64;

    let mut log = std::fs::File::create(format!("{prefix}_log.csv")).unwrap();
    writeln!(log, "day,animals,hunters,mass_mean,births,hunger,age,killed,decisions,close,notices,dec_per_animal_day,us_per_decision,secs").unwrap();
    let end = w.p.days * DAY;
    let mut scratch = Vec::new();
    let mut day = 1.0;
    let mut frame_t = 0.0;
    let mut last = Count::default();
    let mut last_wall = Instant::now();
    let mut decide_secs = 0.0;
    while let Some(Reverse((tm, i, ver))) = w.q.pop() {
        let t = tm as f64 / 1000.0;
        if t > end {
            break;
        }
        if let Some(v) = view.as_mut() {
            for (id, c) in w.died.drain(..) {
                v.died((t / w.p.frame) as u64, id, c);
            }
            for (c, p) in w.born.drain(..) {
                v.born((t / w.p.frame) as u64, c, p);
            }
            while frame_t <= t {
                let step = (frame_t / w.p.frame).round() as u64;
                if v.wants(step) {
                    if frame_t - plant_t >= 600.0 || plant_t < 0.0 {
                    plant_t = frame_t;
                    for c in 0..n * n {
                        plant[c] = if w.g.tree[c] > 0.0 { w.g.tree[c] as f64 / w.g.cell / 0.5 } else if w.g.cap[c] > 0.0 { 0.9 * w.g.peek((c % n) as f64 * w.g.cell + 1.0, (c / n) as f64 * w.g.cell + 1.0, frame_t) / K_GRASS } else { 0.0 };
                    }
                    }
                    let alive = w.b.iter().filter(|b| b.alive).count();
                    let refs: Vec<&[f64]> = vec![&water, &plant];
                    let ft = frame_t;
                    let cell = w.g.cell;
                    v.frame_ext(step, &refs, &[(ft / DAY) as f32, alive as f32], |push| {
                        for b in w.b.iter().filter(|b| b.alive) {
                            let (x, y) = b.pos(ft);
                            let hunter = b.w[2 * NI] > 0.0;
                            let facing = if b.vx.abs() > b.vy.abs() { if b.vx > 0.0 { 2 } else { 3 } } else if b.vy > 0.0 { 1 } else { 0 };
                            let diet = if b.ate_flesh > 0.0 && b.ate_flesh >= b.ate_grass { 1 } else if b.ate_grass > 0.0 { 0 } else { 2 };
                            let a = viewer::AgentIn {
                                id: b.id,
                                lineage: b.line,
                                x: ((x / cell * SUB as f64).max(0.0) as u64).min(65535) as u16,
                                y: ((y / cell * SUB as f64).max(0.0) as u64).min(65535) as u16,
                                facing,
                                diet,
                                fill: 1.0,
                                energy: (16.0 * b.e / b.cap()) as f32,
                                ripe: 16.0,
                                fat: (b.e / b.cap()) as f32,
                                age: ((ft - b.born) / DAY).max(0.0) as u32,
                                born: 0,
                                side: 8,
                                cells: &shapes[hunter as usize],
                            };
                            let mut extra = Vec::with_capacity(10);
                            extra.extend_from_slice(&(b.m as f32).to_le_bytes());
                            extra.extend_from_slice(&1f32.to_le_bytes());
                            extra.extend_from_slice(&((LIFE / DAY) as u16).to_le_bytes());
                            push(a, &extra);
                        }
                    });
                }
                v.tick(step);
                frame_t += w.p.frame;
            }
        }
        while t >= day * DAY {
            let alive: Vec<&Body> = w.b.iter().filter(|b| b.alive).collect();
            let hunters = alive.iter().filter(|b| b.w[2 * NI] > 0.0).count();
            let mm = alive.iter().map(|b| b.m).sum::<f64>() / alive.len().max(1) as f64;
            let d = &w.c;
            let dd = d.decisions - last.decisions;
            let ad = (d.animal_s - last.animal_s) / DAY;
            let secs = last_wall.elapsed().as_secs_f64();
            writeln!(log, "{day},{},{hunters},{mm:.2},{},{},{},{},{dd},{},{},{:.1},{:.3},{secs:.3}", alive.len(), d.births - last.births, d.hunger - last.hunger, d.age - last.age, d.killed - last.killed, d.close - last.close, d.notices - last.notices, dd as f64 / ad.max(1e-9), decide_secs * 1e6 / dd.max(1) as f64).unwrap();
            log.flush().unwrap();
            last = w.c.clone();
            last_wall = Instant::now();
            decide_secs = 0.0;
            day += 1.0;
            if alive.is_empty() {
                break;
            }
        }
        let i = i as usize;
        if !w.b[i].alive || w.b[i].ver != ver {
            continue;
        }
        let t0 = Instant::now();
        w.decide(i, t, &mut scratch);
        decide_secs += t0.elapsed().as_secs_f64();
        if view.is_none() {
            w.died.clear();
            w.born.clear();
        }
    }
    let secs = wall.elapsed().as_secs_f64();
    let ay = w.c.animal_s / YEAR;
    let mut sum = std::fs::File::create(format!("{prefix}_sum.csv")).unwrap();
    writeln!(sum, "what,value").unwrap();
    for (k, v) in [
        ("land_km2", land),
        ("founders", w.p.n as f64),
        ("days", w.p.days),
        ("animal_years", ay),
        ("decisions", w.c.decisions as f64),
        ("decisions_per_animal_day", w.c.decisions as f64 / (w.c.animal_s / DAY).max(1e-9)),
        ("close_share", w.c.close as f64 / w.c.decisions.max(1) as f64),
        ("notices", w.c.notices as f64),
        ("wall_secs", secs),
        ("us_per_decision", secs * 1e6 / w.c.decisions.max(1) as f64),
        ("animal_years_per_core_hour", ay / (secs / 3600.0)),
    ] {
        writeln!(sum, "{k},{v}").unwrap();
    }
    eprintln!("e116: {ay:.0} animal-years in {secs:.0} s, {:.0} decisions an animal-day, {:.2} us a decision, {:.0} animal-years a core-hour", w.c.decisions as f64 / (w.c.animal_s / DAY).max(1e-9), secs * 1e6 / w.c.decisions.max(1) as f64, ay / (secs / 3600.0));
}
