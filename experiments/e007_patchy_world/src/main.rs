//! e007: a bigger world with patchy food. The e006 world (sexual mode, D = 6, radius 1) with
//! the world size as an argument and a second food law: instead of +0.01 everywhere, regrowth
//! is concentrated in Gaussian patches that drift, with the same total. The question is whether
//! sensor blocks get a reason to exist. `64 uniform` reproduces e006 sexual seed N byte for byte.

use std::collections::HashMap;
use std::io::Write;

// World (as e001/e003). Width and height are arguments; 64 is e006.
const RES_CAP: f32 = 1.0;
const RES_GROWTH: f32 = 0.01; // uniform regrowth per cell per step; patchy mode spreads the same total over patches
const INIT_POP_PER_CELL: f32 = 400.0 / 4096.0; // e006's 400 on 64x64
// Patchy food: one patch per PATCH_AREA cells, a Gaussian of width PATCH_SIGMA, whose center takes a
// random step of one cell every PATCH_DRIFT steps. Peak regrowth is set so that the sum over the
// world equals uniform regrowth: RES_GROWTH * PATCH_AREA / (2 pi sigma^2), about 0.10 per step.
const PATCH_AREA: usize = 4096;
const PATCH_SIGMA: f32 = 8.0;
const PATCH_DRIFT: u64 = 50;
const INIT_ENERGY: f32 = 5.0;
const MUTATIONS_PER_CHILD: usize = 2;
const MAX_AGE: u32 = 3000;

// Costs and gains, all per block.
const UPKEEP: f32 = 0.002; // per block per step
const MOVE_COST: f32 = 0.001; // per block per cell moved
const BITE: f32 = 0.02; // plant intake per digestive block per step
const GUT: f32 = 4.0; // largest prey mass = GUT * digestive blocks
const MEAT_ENERGY: f32 = 0.5; // share of the prey's energy the eater gets
const MEAT_MASS: f32 = 0.02; // energy per prey block
const FRONT_ROWS: usize = 3; // hard blocks in these rows are the bite; attack = min(bite, muscle)

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

// Policy: 10 inputs -> 5 actions, read from the same table (no position input).
const N_IN: usize = 10;
const N_OUT: usize = 5;
const N_POLICY: usize = N_IN * N_OUT + N_OUT;
const K: usize = N_KINDS + N_POLICY;

// Species.
const D: usize = 6; // two agents can mate if their distance is at most D
const MIN_LINEAGE: usize = 5; // a mating-connected group of at least this size is a lineage
const LINEAGE_INTERVAL: u64 = 1_000;
const LINEAGE_CONFIRM: u32 = 5; // detections in a row a group must exist before it is a lineage
const RADIUS: usize = 1; // mate search: cells within this Manhattan distance
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

#[derive(Clone)]
struct Body {
    cells: [u8; CELLS],
    mass: u8,
    kinds: [u8; N_KINDS],
    attack: u8,
    policy: [f32; N_POLICY],
    n_genes: u16,
}

impl Body {
    fn speed(&self) -> f32 {
        if self.mass == 0 { 0.0 } else { self.kinds[MUSCLE] as f32 / self.mass as f32 }
    }
    fn sense(&self) -> f32 {
        (self.kinds[SENSOR] as f32 / 8.0).min(1.0)
    }
    fn defense(&self) -> f32 {
        self.kinds[HARD] as f32 / 2.0
    }
    fn gut(&self) -> f32 {
        GUT * self.kinds[DIGESTIVE] as f32
    }
    fn threshold(&self) -> f32 {
        2.0 + 0.1 * self.mass as f32
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
    let mut kinds = [0u8; N_KINDS];
    let mut front_hard = 0u8;
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
        kinds[best] += 1;
        if best == HARD && c / SIDE < FRONT_ROWS {
            front_hard += 1;
        }
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
    let attack = front_hard.min(kinds[MUSCLE]);
    Body { cells, mass: CELLS as u8 - kinds[0], kinds, attack, policy, n_genes: n as u16 }
}

struct Agent {
    id: u64,
    lineage: u32, // 0 = none; otherwise inherited from the mother, corrected at each detection
    x: usize,
    y: usize,
    energy: f32,
    age: u32,
    plant: f32, // lifetime intake from plants
    meat: f32, // lifetime intake from prey
    alive: bool,
    genome: Vec<u8>,
    keys: Vec<u16>, // sorted gene keys, for distances
    gene_ids: Vec<u16>, // gene keys in genome order: the body is a function of this list
    body: Body,
}

impl Agent {
    fn distance(&self, other: &Agent) -> usize {
        gene_distance(&self.keys, &other.keys)
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

#[derive(Clone, Copy)]
struct Grid {
    w: usize,
    h: usize,
}

impl Grid {
    fn idx(&self, x: usize, y: usize) -> usize {
        y * self.w + x
    }
    fn cells(&self) -> usize {
        self.w * self.h
    }
}

/// Food patches: centers on the torus, and the regrowth field they make (recomputed when they move).
struct Patches {
    centers: Vec<(usize, usize)>,
    grow: Vec<f32>,
    rng: Rng, // own stream, so that uniform runs use the world's rng exactly as e006
}

impl Patches {
    fn new(g: Grid, seed: u64) -> Self {
        let mut rng = Rng(seed.wrapping_mul(0xD1B54A32D192ED03) | 1);
        let n = (g.cells() / PATCH_AREA).max(1);
        let centers = (0..n).map(|_| (rng.below(g.w), rng.below(g.h))).collect();
        let mut p = Patches { centers, grow: vec![0.0; g.cells()], rng };
        p.field(g);
        p
    }
    fn field(&mut self, g: Grid) {
        let peak = RES_GROWTH * PATCH_AREA as f32 / (2.0 * std::f32::consts::PI * PATCH_SIGMA * PATCH_SIGMA);
        let r = (3.0 * PATCH_SIGMA) as isize; // beyond 3 sigma the Gaussian is below 1.2% of the peak
        self.grow.iter_mut().for_each(|v| *v = 0.0);
        for &(cx, cy) in &self.centers {
            for dy in -r..=r {
                for dx in -r..=r {
                    let x = (cx as isize + dx).rem_euclid(g.w as isize) as usize;
                    let y = (cy as isize + dy).rem_euclid(g.h as isize) as usize;
                    let d2 = (dx * dx + dy * dy) as f32;
                    self.grow[g.idx(x, y)] += peak * (-d2 / (2.0 * PATCH_SIGMA * PATCH_SIGMA)).exp();
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
    fn write_frame(&mut self, clip: bool, step: u64, res: &[f32], agents: &[Agent]) {
        let f = if clip { &mut self.clip } else { &mut self.long };
        write!(f, "{{\"step\":{step},\"food\":[").unwrap();
        for (i, r) in res.iter().enumerate() {
            if i > 0 {
                f.write_all(b",").unwrap();
            }
            write!(f, "{}", (r * 15.0).round() as u8).unwrap();
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
            write!(f, "[{},{},{id},{},{}]", a.x, a.y, a.diet_class(), a.lineage).unwrap();
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
    let size: usize = args.get(3).and_then(|s| s.parse().ok()).unwrap_or(64);
    let patchy = match args.get(4).map(String::as_str) {
        None | Some("uniform") => false,
        Some("patchy") => true,
        Some(m) => panic!("unknown food law {m}: use uniform or patchy"),
    };
    let sexual = true;
    let d = D;
    let g = Grid { w: size, h: size };
    let (w, h) = (g.w, g.h);
    let idx = |x: usize, y: usize| g.idx(x, y);
    let reach: Vec<(usize, usize)> = (0..w * h)
        .map(|c| ((c % w) as isize, (c / w) as isize))
        .filter(|&(dx, dy)| {
            let dx = dx.min(w as isize - dx);
            let dy = dy.min(h as isize - dy);
            (dx + dy) as usize <= RADIUS
        })
        .map(|(dx, dy)| (dx as usize, dy as usize))
        .collect();
    let mut rng = Rng(seed.wrapping_mul(0x9E3779B97F4A7C15) | 1);
    let laws = Laws::new(&mut rng);
    let mut patches = if patchy { Some(Patches::new(g, seed)) } else { None };
    let init_pop = (INIT_POP_PER_CELL * (w * h) as f32).round() as usize;
    let prefix = format!("experiments/e007_patchy_world/results/{size}_{}_seed{seed}", if patchy { "patchy" } else { "uniform" });
    let open = |name: &str| std::io::BufWriter::new(std::fs::File::create(format!("{prefix}_{name}")).unwrap());
    let mut log = open("log.csv");
    let mut snaps = Snapshots { long: open("long.jsonl"), clip: open("clip.jsonl"), bodies: open("bodies.jsonl"), ids: HashMap::new() };

    let mut agents_csv = open("agents.csv");
    writeln!(agents_csv, "step,mass,hard,muscle,sensor,digestive,attack,speed,age,energy,plant,meat,lineage").unwrap();
    let mut events = open("events.csv");
    writeln!(events, "step,event,lineage,other,size").unwrap(); // other: parent of a split, target of a merge
    let mut lineages_csv = open("lineages.csv");
    writeln!(lineages_csv, "step,lineage,size,hard,muscle,sensor,digestive,attack,bodies").unwrap();
    let mut dist_csv = open("dist.csv");
    writeln!(dist_csv, "step,measure,value,count").unwrap();

    let mut res = vec![RES_CAP; w * h];
    let mut next_id = 0u64;
    let mut agents: Vec<Agent> = (0..init_pop)
        .map(|_| {
            let genome: Vec<u8> = (0..N).map(|_| rng.below(4) as u8).collect();
            let genes = parse_genes(&genome);
            let body = develop_genes(&genes, &laws);
            next_id += 1;
            Agent {
                id: next_id - 1, lineage: 0, x: rng.below(w), y: rng.below(h), energy: INIT_ENERGY, age: 0, plant: 0.0, meat: 0.0,
                alive: body.mass > 0, keys: sorted_keys(&genes), gene_ids: genes.iter().map(Gene::key).collect(), genome, body,
            }
        })
        .collect();
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
        "step,pop,mean_energy,mean_res,mean_genes,births,deaths_energy,deaths_age,deaths_eaten,deaths_body,escapes,plant_intake,meat_intake,\
         stay,n,s,e,w,steps_per_sec,mass_mean,mass_std,hard_mean,hard_std,muscle_mean,muscle_std,sensor_mean,sensor_std,\
         digestive_mean,digestive_std,attack_mean,attack_std,speed_mean,speed_std,distinct_bodies,top_body_share,\
         diet_plants,diet_mixed,diet_meat,diet_none,births_with_neighbor,sexual_births,lineages,top_lineage_share,no_lineage_share,\
         sensor_agents_share,sense_decisions,sense_used,res_std,res_above_half,regrowth,develops"
    )
    .unwrap();

    let mut births = 0u64;
    let mut sexual_births = 0u64;
    let mut births_with_neighbor = 0u64;
    let mut deaths = [0u64; 4]; // energy, age, eaten, body
    let mut escapes = 0u64;
    let mut plant_intake = 0.0f32;
    let mut meat_intake = 0.0f32;
    let mut actions = [0u64; N_OUT];
    let mut sense_decisions = 0u64; // moves decided by an agent with at least one sensor block
    let mut sense_used = 0u64; // of those, moves that differ from what the agent would do with sense = 0
    let mut regrowth = 0.0f64; // food actually added (the cap wastes the rest), summed over the log interval
    let mut last_time = std::time::Instant::now();
    // Occupancy: first agent in each cell, and the next agent in the same cell.
    let mut head = vec![u32::MAX; w * h];
    let mut next = Vec::new();

    for step in 1..=steps {
        match patches.as_mut() {
            None => {
                for r in res.iter_mut() {
                    let added = RES_GROWTH.min(RES_CAP - *r);
                    *r += added;
                    regrowth += added as f64;
                }
            }
            Some(p) => {
                if step % PATCH_DRIFT == 0 {
                    p.drift(g);
                }
                for (r, &gr) in res.iter_mut().zip(&p.grow) {
                    let added = gr.min(RES_CAP - *r);
                    *r += added;
                    regrowth += added as f64;
                }
            }
        }
        head.iter_mut().for_each(|h| *h = u32::MAX);
        next.clear();
        next.resize(agents.len(), u32::MAX);
        for (i, a) in agents.iter().enumerate() {
            let c = idx(a.x, a.y);
            next[i] = head[c];
            head[c] = i as u32;
        }
        let count_at = |c: usize, head: &[u32], next: &[u32]| {
            let mut n = 0.0;
            let mut i = head[c];
            while i != u32::MAX {
                n += 1.0;
                i = next[i as usize];
            }
            n
        };

        let mut newborn = Vec::new();
        let mut pending: Vec<(Agent, Option<Vec<Gene>>)> = Vec::new();
        for i in 0..agents.len() {
            if !agents[i].alive {
                continue;
            }
            let (x, y) = (agents[i].x, agents[i].y);
            let here = idx(x, y);
            let xn = (x + w - 1) % w;
            let xp = (x + 1) % w;
            let yn = (y + h - 1) % h;
            let yp = (y + 1) % h;
            let xn2 = (x + w - 2) % w;
            let xp2 = (x + 2) % w;
            let yn2 = (y + h - 2) % h;
            let yp2 = (y + 2) % h;

            // 1. Eat plants.
            let a = &mut agents[i];
            a.age += 1;
            let mass = a.body.mass as f32;
            let bite = BITE * a.body.kinds[DIGESTIVE] as f32;
            let eaten = res[here].min(bite);
            res[here] -= eaten;
            a.energy += eaten - UPKEEP * mass;
            a.plant += eaten;
            plant_intake += eaten;

            // 2. Try to eat one neighbor: attack must beat its defense, the gut must accept
            //    its mass, and it escapes with probability (its speed - our speed).
            let attack = a.body.attack as f32;
            let gut = a.body.gut();
            let my_speed = a.body.speed();
            if attack > 0.0 {
                let mut prey = None;
                'cells: for c in [here, idx(x, yn), idx(x, yp), idx(xp, y), idx(xn, y)] {
                    let mut j = head[c];
                    while j != u32::MAX {
                        let p = &agents[j as usize];
                        if j as usize != i && p.alive && p.body.cells != agents[i].body.cells
                            && attack > p.body.defense() && p.body.mass as f32 <= gut
                        {
                            if rng.f32() >= p.body.speed() - my_speed {
                                prey = Some(j as usize);
                            } else {
                                escapes += 1;
                            }
                            break 'cells;
                        }
                        j = next[j as usize];
                    }
                }
                if let Some(j) = prey {
                    let gain = MEAT_ENERGY * agents[j].energy.max(0.0) + MEAT_MASS * agents[j].body.mass as f32;
                    agents[j].alive = false;
                    deaths[2] += 1;
                    let a = &mut agents[i];
                    a.energy += gain;
                    a.meat += gain;
                    meat_intake += gain;
                }
            }

            // 3. Move.
            let a = &agents[i];
            let s = a.body.sense();
            let thr = a.body.threshold();
            let others = |c1: usize, c2: usize| count_at(c1, &head, &next) + s * count_at(c2, &head, &next);
            let input = [
                res[here],
                res[idx(x, yn)] + s * res[idx(x, yn2)],
                res[idx(x, yp)] + s * res[idx(x, yp2)],
                res[idx(xp, y)] + s * res[idx(xp2, y)],
                res[idx(xn, y)] + s * res[idx(xn2, y)],
                others(idx(x, yn), idx(x, yn2)),
                others(idx(x, yp), idx(x, yp2)),
                others(idx(xp, y), idx(xp2, y)),
                others(idx(xn, y), idx(xn2, y)),
                a.energy / thr,
            ];
            let action = act(&a.body.policy, &input);
            actions[action] += 1;
            if s > 0.0 {
                sense_decisions += 1;
                let blind = [
                    res[here], res[idx(x, yn)], res[idx(x, yp)], res[idx(xp, y)], res[idx(xn, y)],
                    count_at(idx(x, yn), &head, &next), count_at(idx(x, yp), &head, &next),
                    count_at(idx(xp, y), &head, &next), count_at(idx(xn, y), &head, &next), a.energy / thr,
                ];
                if act(&a.body.policy, &blind) != action {
                    sense_used += 1;
                }
            }
            let a = &mut agents[i];
            if action != 0 {
                let two = rng.f32() < a.body.speed();
                match action {
                    1 => a.y = if two { yn2 } else { yn },
                    2 => a.y = if two { yp2 } else { yp },
                    3 => a.x = if two { xp2 } else { xp },
                    _ => a.x = if two { xn2 } else { xn },
                }
                a.energy -= MOVE_COST * mass * if two { 2.0 } else { 1.0 };
            }

            // 4. Reproduce. The parent pays (half of its energy goes to the child). In sexual
            //    mode it first looks for a mate within distance D in the cells within `radius`
            //    (its own cell and the 4 neighbors by default); the child is a one-point crossover
            //    of the two genomes. Without a mate (or in asexual mode) the child is a copy, as
            //    in e005. Then 2 point mutations.
            if agents[i].energy >= thr {
                let (x, y) = (agents[i].x, agents[i].y);
                let mut mate = None;
                let mut neighbor = false;
                if sexual {
                    'cells: for &(dx, dy) in &reach {
                        let mut j = head[idx((x + dx) % w, (y + dy) % h)];
                        while j != u32::MAX {
                            let p = &agents[j as usize];
                            if j as usize != i && p.alive {
                                neighbor = true;
                                if agents[i].distance(p) <= d {
                                    mate = Some(j as usize);
                                    break 'cells;
                                }
                            }
                            j = next[j as usize];
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
                let body = if gene_ids == a.gene_ids { Some(a.body.clone()) } else { cache.get(&gene_ids).cloned() };
                let (cx, cy) = match rng.below(4) {
                    0 => (a.x, yn),
                    1 => (a.x, yp),
                    2 => (xp, a.y),
                    _ => (xn, a.y),
                };
                next_id += 1;
                let keys = sorted_keys(&genes);
                let todo = body.is_none().then_some(genes);
                pending.push((Agent {
                    id: next_id - 1, lineage: a.lineage, x: cx, y: cy, energy: a.energy, age: 0, plant: 0.0, meat: 0.0, alive: true,
                    keys, gene_ids, genome, body: body.unwrap_or_else(|| Body { cells: [0; CELLS], mass: 0, kinds: [0; N_KINDS], attack: 0, policy: [0.0; N_POLICY], n_genes: 0 }),
                }, todo));
            }
        }
        // Develop the children with a new gene list, one development per distinct list, on all
        // cores. The children keep their birth order, so the result is the same as developing
        // them one by one in the loop.
        let mut jobs: Vec<(&[u16], &[Gene])> = Vec::new();
        for (a, genes) in &pending {
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
        for (mut a, genes) in pending.drain(..) {
            if genes.is_some() {
                a.body = cache[&a.gene_ids].clone();
            }
            a.alive = a.body.mass > 0;
            if !a.alive {
                deaths[3] += 1;
            }
            newborn.push(a);
        }
        births += newborn.len() as u64;
        agents.append(&mut newborn);
        agents.retain(|a| {
            if !a.alive {
                false
            } else if a.energy <= 0.0 {
                deaths[0] += 1;
                false
            } else if a.age > MAX_AGE {
                deaths[1] += 1;
                false
            } else {
                true
            }
        });

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
                let mut attack = 0.0f32;
                let mut bodies: HashMap<&[u8; CELLS], usize> = HashMap::new();
                for &i in m {
                    for k in 0..N_KINDS {
                        kinds[k] += agents[i].body.kinds[k] as f32;
                    }
                    attack += agents[i].body.attack as f32;
                    *bodies.entry(&agents[i].body.cells).or_insert(0) += 1;
                }
                writeln!(lineages_csv, "{step},{id},{},{:.1},{:.1},{:.1},{:.1},{:.1},{}", m.len(),
                    kinds[HARD] / sz, kinds[MUSCLE] / sz, kinds[SENSOR] / sz, kinds[DIGESTIVE] / sz, attack / sz, bodies.len()).unwrap();
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
            snaps.write_frame(false, step, &res, &agents);
        }
        if step % AGENT_DUMP_INTERVAL == 0 {
            for a in &agents {
                let k = &a.body.kinds;
                writeln!(agents_csv, "{step},{},{},{},{},{},{},{:.3},{},{:.2},{:.2},{:.2},{}",
                    a.body.mass, k[HARD], k[MUSCLE], k[SENSOR], k[DIGESTIVE], a.body.attack, a.body.speed(), a.age, a.energy, a.plant, a.meat, a.lineage).unwrap();
            }
        }
        if step >= CLIP_START && step < CLIP_START + CLIP_LEN {
            snaps.write_frame(true, step, &res, &agents);
        }

        if step % LOG_INTERVAL == 0 || agents.is_empty() {
            let now = std::time::Instant::now();
            let sps = LOG_INTERVAL as f64 / (now - last_time).as_secs_f64();
            last_time = now;
            let pop = agents.len().max(1) as f32;
            let mean_energy = agents.iter().map(|a| a.energy).sum::<f32>() / pop;
            let mean_res = res.iter().sum::<f32>() / (w * h) as f32;
            let mean_genes = agents.iter().map(|a| a.body.n_genes as f32).sum::<f32>() / pop;
            let total_actions = actions.iter().sum::<u64>().max(1) as f64;
            write!(
                log,
                "{step},{},{mean_energy:.3},{mean_res:.3},{mean_genes:.2},{births},{},{},{},{},{escapes},{plant_intake:.1},{meat_intake:.1}",
                agents.len(),
                deaths[0],
                deaths[1],
                deaths[2],
                deaths[3]
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
            let (m, s) = mean_std(agents.iter().map(|a| a.body.attack as f32));
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
            let (_, res_std) = mean_std(res.iter().copied());
            let res_above_half = res.iter().filter(|&&r| r > 0.5).count() as f32 / (w * h) as f32;
            writeln!(log, ",{births_with_neighbor},{sexual_births},{},{top_lineage:.3},{no_lineage:.3},{sensor_agents:.3},{sense_decisions},{:.3},{res_std:.3},{res_above_half:.3},{:.2},{develops}",
                lineages.len(), if sense_decisions > 0 { sense_used as f64 / sense_decisions as f64 } else { 0.0 }, regrowth / LOG_INTERVAL as f64).unwrap();
            births = 0;
            sexual_births = 0;
            births_with_neighbor = 0;
            deaths = [0; 4];
            escapes = 0;
            plant_intake = 0.0;
            meat_intake = 0.0;
            actions = [0; N_OUT];
            sense_decisions = 0;
            sense_used = 0;
            regrowth = 0.0;
            develops = 0;
            if agents.is_empty() {
                eprintln!("extinct at step {step}");
                break;
            }
        }
    }
}
