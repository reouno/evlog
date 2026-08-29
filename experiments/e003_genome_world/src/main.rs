//! e003: e001's world with e002's genome. Traits have costs; selection acts on the map.

use std::io::Write;

const W: usize = 64;
const H: usize = 64;
const RES_CAP: f32 = 1.0;
const RES_GROWTH: f32 = 0.01;
const INIT_POP: usize = 300;
const INIT_ENERGY: f32 = 5.0;
const MUTATIONS_PER_CHILD: usize = 2;

// Genome (as e002).
const N: usize = 512;
const PROMOTER: [u8; 3] = [0, 1, 0];
const GENE_LEN: usize = 8;
const TAG_LEN: usize = 4;
const T: usize = 40;
const N_TRAITS: usize = 8;
const TRAIT_NAMES: [&str; N_TRAITS] = [
    "speed", "metabolism", "sense", "size", "lifespan", "greed", "boldness", "fertility",
];
const SPEED: usize = 0;
const SENSE: usize = 2;
const SIZE: usize = 3;
const LIFESPAN: usize = 4;
const FERTILITY: usize = 7;

// Policy (as e001): 6 inputs -> 5 actions.
const N_IN: usize = 6;
const N_OUT: usize = 5;
const N_POLICY: usize = N_IN * N_OUT + N_OUT;
const K: usize = N_TRAITS + N_POLICY;

const LOG_INTERVAL: u64 = 10_000;
const LONG_INTERVAL: u64 = 5_000;
const CLIP_START: u64 = 600_000;
const CLIP_LEN: u64 = 400;

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

struct Laws {
    table: Vec<[f32; K]>,
}

impl Laws {
    fn new(rng: &mut Rng) -> Self {
        let table = (0..256)
            .map(|_| {
                let mut row = [0.0; K];
                for v in row.iter_mut() {
                    *v = rng.f32() * 2.0 - 1.0;
                }
                row
            })
            .collect();
        Laws { table }
    }
}

struct Gene {
    tag: [u8; TAG_LEN],
    product: [u8; TAG_LEN],
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

fn sigmoid(x: f32) -> f32 {
    1.0 / (1.0 + (-x).exp())
}

struct Body {
    traits: [f32; N_TRAITS],
    policy: [f32; N_POLICY],
    n_genes: u16,
}

fn decode(genome: &[u8], laws: &Laws) -> Body {
    let genes = parse_genes(genome);
    let n = genes.len();
    let mut w = vec![0.0f32; n * n];
    for j in 0..n {
        let sign = if genes[j].product[0] < 2 { 1.0 } else { -1.0 };
        for i in 0..n {
            let m = genes[j].product.iter().zip(genes[i].tag.iter()).filter(|(a, b)| a == b).count();
            if m >= 3 {
                w[j * n + i] = sign * (m as f32 - 2.0) / 2.0;
            }
        }
    }
    let mut level = vec![0.5f32; n];
    let mut next = vec![0.0f32; n];
    for _ in 0..T {
        for i in 0..n {
            let mut input = 0.0;
            for j in 0..n {
                input += w[j * n + i] * level[j];
            }
            next[i] = sigmoid(3.0 * input - 1.0);
        }
        std::mem::swap(&mut level, &mut next);
    }
    let mut out = [0.0f32; K];
    for (g, &lv) in genes.iter().zip(level.iter()) {
        let row = &laws.table[pattern_index(&g.product)];
        for k in 0..K {
            out[k] += row[k] * lv;
        }
    }
    let mut traits = [0.0; N_TRAITS];
    for k in 0..N_TRAITS {
        traits[k] = sigmoid(out[k]);
    }
    let mut policy = [0.0; N_POLICY];
    for k in 0..N_POLICY {
        policy[k] = sigmoid(out[N_TRAITS + k]) * 2.0 - 1.0;
    }
    Body { traits, policy, n_genes: n as u16 }
}

struct Agent {
    x: usize,
    y: usize,
    energy: f32,
    age: u32,
    genome: Vec<u8>,
    body: Body,
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

fn threshold(fertility: f32) -> f32 {
    14.0 - 8.0 * fertility
}

fn write_frame(f: &mut impl Write, step: u64, res: &[f32], agents: &[Agent]) {
    write!(f, "{{\"step\":{step},\"food\":[").unwrap();
    for (i, r) in res.iter().enumerate() {
        if i > 0 {
            f.write_all(b",").unwrap();
        }
        write!(f, "{}", (r * 15.0).round() as u8).unwrap();
    }
    write!(f, "],\"agents\":[").unwrap();
    for (i, a) in agents.iter().enumerate() {
        if i > 0 {
            f.write_all(b",").unwrap();
        }
        write!(
            f,
            "[{},{},{},{}]",
            a.x,
            a.y,
            (a.body.traits[SIZE] * 255.0) as u8,
            (a.body.traits[LIFESPAN] * 255.0) as u8
        )
        .unwrap();
    }
    writeln!(f, "]}}").unwrap();
}

fn main() {
    let args: Vec<String> = std::env::args().collect();
    let steps: u64 = args.get(1).and_then(|s| s.parse().ok()).unwrap_or(1_000_000);
    let seed: u64 = args.get(2).and_then(|s| s.parse().ok()).unwrap_or(1);
    let mut rng = Rng(seed.wrapping_mul(0x9E3779B97F4A7C15) | 1);
    let laws = Laws::new(&mut rng);
    let dir = "experiments/e003_genome_world/results";
    let mut log = std::io::BufWriter::new(std::fs::File::create(format!("{dir}/seed{seed}_log.csv")).unwrap());
    let mut long = std::io::BufWriter::new(std::fs::File::create(format!("{dir}/seed{seed}_long.jsonl")).unwrap());
    let mut clip = std::io::BufWriter::new(std::fs::File::create(format!("{dir}/seed{seed}_clip.jsonl")).unwrap());

    let mut res = vec![RES_CAP; W * H];
    let mut agents: Vec<Agent> = (0..INIT_POP)
        .map(|_| {
            let genome: Vec<u8> = (0..N).map(|_| rng.below(4) as u8).collect();
            let body = decode(&genome, &laws);
            Agent { x: rng.below(W), y: rng.below(H), energy: INIT_ENERGY, age: 0, genome, body }
        })
        .collect();

    write!(log, "step,pop,mean_energy,mean_res,mean_genes,births,deaths_energy,deaths_age,stay,n,s,e,w,steps_per_sec").unwrap();
    for name in TRAIT_NAMES {
        write!(log, ",{name}_mean,{name}_std").unwrap();
    }
    writeln!(log).unwrap();

    let mut births = 0u64;
    let mut deaths_energy = 0u64;
    let mut deaths_age = 0u64;
    let mut actions = [0u64; N_OUT];
    let mut last_time = std::time::Instant::now();

    for step in 1..=steps {
        for r in res.iter_mut() {
            *r = (*r + RES_GROWTH).min(RES_CAP);
        }
        let mut newborn = Vec::new();
        for a in agents.iter_mut() {
            let t = &a.body.traits;
            a.age += 1;
            let here = idx(a.x, a.y);
            let bite = 0.1 + 0.3 * t[SIZE];
            let eaten = res[here].min(bite);
            res[here] -= eaten;
            a.energy += eaten - (0.03 + 0.06 * t[SIZE] + 0.02 * t[SENSE] + 0.02 * t[LIFESPAN]);

            let xn = (a.x + W - 1) % W;
            let xp = (a.x + 1) % W;
            let yn = (a.y + H - 1) % H;
            let yp = (a.y + 1) % H;
            let xn2 = (a.x + W - 2) % W;
            let xp2 = (a.x + 2) % W;
            let yn2 = (a.y + H - 2) % H;
            let yp2 = (a.y + 2) % H;
            let s = t[SENSE];
            let thr = threshold(t[FERTILITY]);
            let input = [
                res[here],
                res[idx(a.x, yn)] + s * res[idx(a.x, yn2)],
                res[idx(a.x, yp)] + s * res[idx(a.x, yp2)],
                res[idx(xp, a.y)] + s * res[idx(xp2, a.y)],
                res[idx(xn, a.y)] + s * res[idx(xn2, a.y)],
                a.energy / thr,
            ];
            let action = act(&a.body.policy, &input);
            actions[action] += 1;
            if action != 0 {
                let two = rng.f32() < t[SPEED];
                match action {
                    1 => a.y = if two { yn2 } else { yn },
                    2 => a.y = if two { yp2 } else { yp },
                    3 => a.x = if two { xp2 } else { xp },
                    _ => a.x = if two { xn2 } else { xn },
                }
                a.energy -= 0.01 + 0.05 * t[SPEED];
            }
            if a.energy >= thr {
                a.energy *= 0.5;
                let mut genome = a.genome.clone();
                for _ in 0..MUTATIONS_PER_CHILD {
                    let pos = rng.below(N);
                    genome[pos] = (genome[pos] + 1 + rng.below(3) as u8) % 4;
                }
                let body = decode(&genome, &laws);
                newborn.push(Agent { x: a.x, y: a.y, energy: a.energy, age: 0, genome, body });
            }
        }
        births += newborn.len() as u64;
        agents.append(&mut newborn);
        agents.retain(|a| {
            if a.energy <= 0.0 {
                deaths_energy += 1;
                false
            } else if a.age as f32 > 200.0 + 1800.0 * a.body.traits[LIFESPAN] {
                deaths_age += 1;
                false
            } else {
                true
            }
        });

        if step % LONG_INTERVAL == 0 {
            write_frame(&mut long, step, &res, &agents);
        }
        if step >= CLIP_START && step < CLIP_START + CLIP_LEN {
            write_frame(&mut clip, step, &res, &agents);
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
                "{step},{},{mean_energy:.3},{mean_res:.3},{mean_genes:.2},{births},{deaths_energy},{deaths_age}",
                agents.len()
            )
            .unwrap();
            for a in actions {
                write!(log, ",{:.3}", a as f64 / total_actions).unwrap();
            }
            write!(log, ",{sps:.0}").unwrap();
            for k in 0..N_TRAITS {
                let mean = agents.iter().map(|a| a.body.traits[k]).sum::<f32>() / pop;
                let var = agents.iter().map(|a| (a.body.traits[k] - mean).powi(2)).sum::<f32>() / pop;
                write!(log, ",{mean:.4},{:.4}", var.sqrt()).unwrap();
            }
            writeln!(log).unwrap();
            births = 0;
            deaths_energy = 0;
            deaths_age = 0;
            actions = [0; N_OUT];
            if agents.is_empty() {
                eprintln!("extinct at step {step}");
                break;
            }
        }
    }
}
