//! e001: minimal world. Resources on a torus grid, agents with a linear policy,
//! energy-driven birth and death, gaussian mutation. No learning.

use std::io::Write;

const W: usize = 64;
const H: usize = 64;

const RES_CAP: f32 = 1.0;
const RES_GROWTH: f32 = 0.01;
const BITE: f32 = 0.2;

const BASE_COST: f32 = 0.05;
const MOVE_COST: f32 = 0.03;
const REPRO_THRESHOLD: f32 = 10.0;
const INIT_ENERGY: f32 = 5.0;
const INIT_POP: usize = 200;

const N_IN: usize = 6;
const N_OUT: usize = 5;
const GENOME_LEN: usize = N_IN * N_OUT + N_OUT;
const MUT_SIGMA: f32 = 0.1;

const LOG_INTERVAL: u64 = 10_000;

struct Rng(u64);

impl Rng {
    fn next_u64(&mut self) -> u64 {
        // xorshift64*
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
    fn gauss(&mut self) -> f32 {
        let u1 = self.f32().max(1e-7);
        let u2 = self.f32();
        (-2.0 * u1.ln()).sqrt() * (2.0 * std::f32::consts::PI * u2).cos()
    }
}

#[derive(Clone)]
struct Agent {
    x: usize,
    y: usize,
    energy: f32,
    genome: [f32; GENOME_LEN],
}

fn idx(x: usize, y: usize) -> usize {
    y * W + x
}

fn act(genome: &[f32; GENOME_LEN], input: &[f32; N_IN]) -> usize {
    let mut best = 0;
    let mut best_v = f32::NEG_INFINITY;
    for o in 0..N_OUT {
        let mut v = genome[N_IN * N_OUT + o];
        for i in 0..N_IN {
            v += genome[o * N_IN + i] * input[i];
        }
        if v > best_v {
            best_v = v;
            best = o;
        }
    }
    best
}

struct Stats {
    births: u64,
    deaths: u64,
    actions: [u64; N_OUT],
}

fn main() {
    let args: Vec<String> = std::env::args().collect();
    let steps: u64 = args.get(1).and_then(|s| s.parse().ok()).unwrap_or(1_000_000);
    let seed: u64 = args.get(2).and_then(|s| s.parse().ok()).unwrap_or(1);
    let mut rng = Rng(seed.wrapping_mul(0x9E3779B97F4A7C15) | 1);

    let mut res = vec![RES_CAP; W * H];
    let mut agents: Vec<Agent> = (0..INIT_POP)
        .map(|_| {
            let mut g = [0.0; GENOME_LEN];
            for v in g.iter_mut() {
                *v = rng.gauss();
            }
            Agent { x: rng.below(W), y: rng.below(H), energy: INIT_ENERGY, genome: g }
        })
        .collect();

    let mut stats = Stats { births: 0, deaths: 0, actions: [0; N_OUT] };
    let mut prev_mean = mean_genome(&agents);
    let mut last_time = std::time::Instant::now();

    let out = std::io::stdout();
    let mut out = out.lock();
    writeln!(
        out,
        "step,pop,mean_energy,mean_res,stay,n,s,e,w,diversity,drift,births,deaths,steps_per_sec"
    )
    .unwrap();

    for step in 1..=steps {
        for r in res.iter_mut() {
            *r = (*r + RES_GROWTH).min(RES_CAP);
        }

        let mut newborn = Vec::new();
        for a in agents.iter_mut() {
            let here = idx(a.x, a.y);
            let eaten = res[here].min(BITE);
            res[here] -= eaten;
            a.energy += eaten - BASE_COST;

            let xn = (a.x + W - 1) % W;
            let xp = (a.x + 1) % W;
            let yn = (a.y + H - 1) % H;
            let yp = (a.y + 1) % H;
            let input = [
                res[here],
                res[idx(a.x, yn)],
                res[idx(a.x, yp)],
                res[idx(xp, a.y)],
                res[idx(xn, a.y)],
                a.energy / REPRO_THRESHOLD,
            ];
            let action = act(&a.genome, &input);
            stats.actions[action] += 1;
            match action {
                1 => a.y = yn,
                2 => a.y = yp,
                3 => a.x = xp,
                4 => a.x = xn,
                _ => {}
            }
            if action != 0 {
                a.energy -= MOVE_COST;
            }

            if a.energy >= REPRO_THRESHOLD {
                a.energy *= 0.5;
                let mut child = a.clone();
                for v in child.genome.iter_mut() {
                    *v += rng.gauss() * MUT_SIGMA;
                }
                newborn.push(child);
            }
        }
        stats.births += newborn.len() as u64;
        agents.append(&mut newborn);

        let before = agents.len();
        agents.retain(|a| a.energy > 0.0);
        stats.deaths += (before - agents.len()) as u64;

        if step % LOG_INTERVAL == 0 || agents.is_empty() {
            let now = std::time::Instant::now();
            let sps = LOG_INTERVAL as f64 / (now - last_time).as_secs_f64();
            last_time = now;

            let pop = agents.len();
            let mean_energy = agents.iter().map(|a| a.energy).sum::<f32>() / pop.max(1) as f32;
            let mean_res = res.iter().sum::<f32>() / (W * H) as f32;
            let total_actions = stats.actions.iter().sum::<u64>().max(1) as f64;
            let mean = mean_genome(&agents);
            let diversity = diversity(&agents, &mean);
            let drift = mean
                .iter()
                .zip(prev_mean.iter())
                .map(|(a, b)| (a - b) * (a - b))
                .sum::<f32>()
                .sqrt();
            prev_mean = mean;

            write!(out, "{step},{pop},{mean_energy:.3},{mean_res:.3}").unwrap();
            for a in stats.actions {
                write!(out, ",{:.3}", a as f64 / total_actions).unwrap();
            }
            writeln!(
                out,
                ",{diversity:.4},{drift:.4},{},{},{sps:.0}",
                stats.births, stats.deaths
            )
            .unwrap();
            stats = Stats { births: 0, deaths: 0, actions: [0; N_OUT] };

            if agents.is_empty() {
                eprintln!("extinct at step {step}");
                break;
            }
        }
    }
}

fn mean_genome(agents: &[Agent]) -> [f32; GENOME_LEN] {
    let mut m = [0.0f32; GENOME_LEN];
    for a in agents {
        for (mi, g) in m.iter_mut().zip(a.genome.iter()) {
            *mi += g;
        }
    }
    let n = agents.len().max(1) as f32;
    for v in m.iter_mut() {
        *v /= n;
    }
    m
}

fn diversity(agents: &[Agent], mean: &[f32; GENOME_LEN]) -> f32 {
    if agents.is_empty() {
        return 0.0;
    }
    let mut var = [0.0f32; GENOME_LEN];
    for a in agents {
        for i in 0..GENOME_LEN {
            let d = a.genome[i] - mean[i];
            var[i] += d * d;
        }
    }
    let n = agents.len() as f32;
    var.iter().map(|v| (v / n).sqrt()).sum::<f32>() / GENOME_LEN as f32
}
