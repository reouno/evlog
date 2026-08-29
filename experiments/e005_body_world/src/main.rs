//! e005: bodies (e004) in the world (e003), with function derived from shape and one
//! predation rule: you can eat what your attack beats and your gut accepts, unless it
//! is faster than you and gets away.

use std::collections::HashMap;
use std::io::Write;

// World (as e001/e003).
const W: usize = 64;
const H: usize = 64;
const RES_CAP: f32 = 1.0;
const RES_GROWTH: f32 = 0.01;
const INIT_POP: usize = 400;
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

// Policy: 10 inputs -> 5 actions, read from the same table (no position input).
const N_IN: usize = 10;
const N_OUT: usize = 5;
const N_POLICY: usize = N_IN * N_OUT + N_OUT;
const K: usize = N_KINDS + N_POLICY;

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

struct Gene {
    tag: [u8; TAG_LEN],
    product: [u8; TAG_LEN],
}

struct Laws {
    morphogen: [[u8; TAG_LEN]; N_MORPH],
    table: Vec<[f32; K]>,
    morph_level: [[f32; N_MORPH]; CELLS],
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
        let mut morph_level = [[0.0f32; N_MORPH]; CELLS];
        let c = (SIDE as f32 - 1.0) / 2.0;
        let rmax = (2.0 * c * c).sqrt();
        for (i, lv) in morph_level.iter_mut().enumerate() {
            let x = (i % SIDE) as f32 / (SIDE as f32 - 1.0);
            let y = (i / SIDE) as f32 / (SIDE as f32 - 1.0);
            let dx = (i % SIDE) as f32 - c;
            let dy = (i / SIDE) as f32 - c;
            let r = (dx * dx + dy * dy).sqrt() / rmax;
            *lv = [x, 1.0 - x, y, 1.0 - y, r, 1.0 - r];
            for v in lv.iter_mut() {
                *v = 2.0 * *v - 1.0;
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

/// Development (e004) for the cells, plus one run without position for the policy.
fn develop(genome: &[u8], laws: &Laws) -> Body {
    let genes = parse_genes(genome);
    let n = genes.len();
    let mut w = vec![0.0f32; n * n];
    let mut wm = vec![0.0f32; N_MORPH * n];
    for i in 0..n {
        for j in 0..n {
            w[j * n + i] = bind(&genes[j].product, &genes[i].tag);
        }
        for m in 0..N_MORPH {
            wm[m * n + i] = bind_morphogen(&laws.morphogen[m], &genes[i].tag);
        }
    }
    let rows: Vec<&[f32; K]> = genes.iter().map(|g| &laws.table[pattern_index(&g.product)]).collect();

    let mut level = vec![0.0f32; n];
    let mut next = vec![0.0f32; n];
    let mut settle = |morph: &[f32; N_MORPH], level: &mut Vec<f32>| {
        level.iter_mut().for_each(|l| *l = 0.5);
        for _ in 0..T {
            for i in 0..n {
                let mut input = 0.0;
                for j in 0..n {
                    input += w[j * n + i] * level[j];
                }
                for m in 0..N_MORPH {
                    input += wm[m * n + i] * morph[m];
                }
                next[i] = sigmoid(3.0 * input - 1.0);
            }
            std::mem::swap(level, &mut next);
        }
    };

    let mut cells = [0u8; CELLS];
    let mut kinds = [0u8; N_KINDS];
    let mut front_hard = 0u8;
    for (c, cell) in cells.iter_mut().enumerate() {
        settle(&laws.morph_level[c], &mut level);
        let mut score = [0.0f32; N_KINDS];
        for (row, &lv) in rows.iter().zip(level.iter()) {
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
    settle(&[0.0; N_MORPH], &mut level);
    let mut policy = [0.0f32; N_POLICY];
    for (row, &lv) in rows.iter().zip(level.iter()) {
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
    x: usize,
    y: usize,
    energy: f32,
    age: u32,
    plant: f32, // lifetime intake from plants
    meat: f32, // lifetime intake from prey
    alive: bool,
    genome: Vec<u8>,
    body: Body,
}

impl Agent {
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

fn idx(x: usize, y: usize) -> usize {
    y * W + x
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
            write!(f, "[{},{},{id},{}]", a.x, a.y, a.diet_class()).unwrap();
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
    let mut rng = Rng(seed.wrapping_mul(0x9E3779B97F4A7C15) | 1);
    let laws = Laws::new(&mut rng);
    let dir = "experiments/e005_body_world/results";
    let mut log = std::io::BufWriter::new(std::fs::File::create(format!("{dir}/seed{seed}_log.csv")).unwrap());
    let mut snaps = Snapshots {
        long: std::io::BufWriter::new(std::fs::File::create(format!("{dir}/seed{seed}_long.jsonl")).unwrap()),
        clip: std::io::BufWriter::new(std::fs::File::create(format!("{dir}/seed{seed}_clip.jsonl")).unwrap()),
        bodies: std::io::BufWriter::new(std::fs::File::create(format!("{dir}/seed{seed}_bodies.jsonl")).unwrap()),
        ids: HashMap::new(),
    };

    let mut agents_csv = std::io::BufWriter::new(std::fs::File::create(format!("{dir}/seed{seed}_agents.csv")).unwrap());
    writeln!(agents_csv, "step,mass,hard,muscle,sensor,digestive,attack,speed,age,energy,plant,meat").unwrap();

    let mut res = vec![RES_CAP; W * H];
    let mut agents: Vec<Agent> = (0..INIT_POP)
        .map(|_| {
            let genome: Vec<u8> = (0..N).map(|_| rng.below(4) as u8).collect();
            let body = develop(&genome, &laws);
            Agent { x: rng.below(W), y: rng.below(H), energy: INIT_ENERGY, age: 0, plant: 0.0, meat: 0.0, alive: body.mass > 0, genome, body }
        })
        .collect();

    writeln!(
        log,
        "step,pop,mean_energy,mean_res,mean_genes,births,deaths_energy,deaths_age,deaths_eaten,deaths_body,escapes,plant_intake,meat_intake,\
         stay,n,s,e,w,steps_per_sec,mass_mean,mass_std,hard_mean,hard_std,muscle_mean,muscle_std,sensor_mean,sensor_std,\
         digestive_mean,digestive_std,attack_mean,attack_std,speed_mean,speed_std,distinct_bodies,top_body_share,\
         diet_plants,diet_mixed,diet_meat,diet_none"
    )
    .unwrap();

    let mut births = 0u64;
    let mut deaths = [0u64; 4]; // energy, age, eaten, body
    let mut escapes = 0u64;
    let mut plant_intake = 0.0f32;
    let mut meat_intake = 0.0f32;
    let mut actions = [0u64; N_OUT];
    let mut last_time = std::time::Instant::now();
    // Occupancy: first agent in each cell, and the next agent in the same cell.
    let mut head = vec![u32::MAX; W * H];
    let mut next = Vec::new();

    for step in 1..=steps {
        for r in res.iter_mut() {
            *r = (*r + RES_GROWTH).min(RES_CAP);
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
        for i in 0..agents.len() {
            if !agents[i].alive {
                continue;
            }
            let (x, y) = (agents[i].x, agents[i].y);
            let here = idx(x, y);
            let xn = (x + W - 1) % W;
            let xp = (x + 1) % W;
            let yn = (y + H - 1) % H;
            let yp = (y + 1) % H;
            let xn2 = (x + W - 2) % W;
            let xp2 = (x + 2) % W;
            let yn2 = (y + H - 2) % H;
            let yp2 = (y + 2) % H;

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

            // 4. Split.
            if a.energy >= thr {
                a.energy *= 0.5;
                let mut genome = a.genome.clone();
                for _ in 0..MUTATIONS_PER_CHILD {
                    let pos = rng.below(N);
                    genome[pos] = (genome[pos] + 1 + rng.below(3) as u8) % 4;
                }
                let body = develop(&genome, &laws);
                let (cx, cy) = match rng.below(4) {
                    0 => (a.x, yn),
                    1 => (a.x, yp),
                    2 => (xp, a.y),
                    _ => (xn, a.y),
                };
                let alive = body.mass > 0;
                if !alive {
                    deaths[3] += 1;
                }
                newborn.push(Agent { x: cx, y: cy, energy: a.energy, age: 0, plant: 0.0, meat: 0.0, alive, genome, body });
            }
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

        if step % LONG_INTERVAL == 0 {
            snaps.write_frame(false, step, &res, &agents);
        }
        if step % AGENT_DUMP_INTERVAL == 0 {
            for a in &agents {
                let k = &a.body.kinds;
                writeln!(agents_csv, "{step},{},{},{},{},{},{},{:.3},{},{:.2},{:.2},{:.2}",
                    a.body.mass, k[HARD], k[MUSCLE], k[SENSOR], k[DIGESTIVE], a.body.attack, a.body.speed(), a.age, a.energy, a.plant, a.meat).unwrap();
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
            let mean_res = res.iter().sum::<f32>() / (W * H) as f32;
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
            writeln!(log).unwrap();
            births = 0;
            deaths = [0; 4];
            escapes = 0;
            plant_intake = 0.0;
            meat_intake = 0.0;
            actions = [0; N_OUT];
            if agents.is_empty() {
                eprintln!("extinct at step {step}");
                break;
            }
        }
    }
}
