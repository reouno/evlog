//! e002: artificial genome -> traits, tested on its own (no world).
//!
//! Genome: string over {0,1,2,3}. A promoter pattern marks a gene; each gene is a
//! regulatory tag plus a product. Products bind tags of other genes (match >= 3 of 4)
//! and raise or lower their expression. After T steps the expression levels are read
//! into K traits through a fixed random table indexed by product.

use std::io::Write;
use std::time::Instant;

const N: usize = 512;
const PROMOTER: [u8; 3] = [0, 1, 0];
const GENE_LEN: usize = 8;
const TAG_LEN: usize = 4;
const T: usize = 40;
const K: usize = 8;
const TRAIT_NAMES: [&str; K] = [
    "speed", "metabolism", "sense", "size", "lifespan", "greed", "boldness", "fertility",
];

const N_RANDOM: usize = 5000;
const N_MUT: usize = 2000;
const N_PAIRS: usize = 2000;

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

/// The fixed "laws": how a product pattern maps onto traits. Same for every genome.
struct Laws {
    table: Vec<[f32; K]>, // indexed by product pattern (4 symbols -> 256 entries)
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

fn random_genome(rng: &mut Rng) -> Vec<u8> {
    (0..N).map(|_| rng.below(4) as u8).collect()
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

/// Development: run the regulatory network, then read traits.
/// Returns (traits, gene count, number of binding edges).
fn decode(genome: &[u8], laws: &Laws) -> (Vec<f32>, usize, usize) {
    let genes = parse_genes(genome);
    let n = genes.len();

    // Binding weights: product of j acting on tag of i. Match >= 3 of 4 binds.
    let mut w = vec![0.0f32; n * n];
    let mut edges = 0;
    for j in 0..n {
        let sign = if genes[j].product[0] < 2 { 1.0 } else { -1.0 };
        for i in 0..n {
            let m = genes[j]
                .product
                .iter()
                .zip(genes[i].tag.iter())
                .filter(|(a, b)| a == b)
                .count();
            if m >= 3 {
                w[j * n + i] = sign * (m as f32 - 2.0) / 2.0; // 0.5 or 1.0
                edges += 1;
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

    let mut traits = vec![0.0f32; K];
    for (g, &lv) in genes.iter().zip(level.iter()) {
        let row = &laws.table[pattern_index(&g.product)];
        for k in 0..K {
            traits[k] += row[k] * lv;
        }
    }
    for t in traits.iter_mut() {
        *t = sigmoid(*t);
    }
    (traits, n, edges)
}

fn dist(a: &[f32], b: &[f32]) -> f32 {
    a.iter().zip(b).map(|(x, y)| (x - y) * (x - y)).sum::<f32>().sqrt()
}

fn percentile(sorted: &[f32], p: f32) -> f32 {
    let idx = ((sorted.len() - 1) as f32 * p).round() as usize;
    sorted[idx]
}

fn main() {
    let seed: u64 = std::env::args().nth(1).and_then(|s| s.parse().ok()).unwrap_or(1);
    let mut rng = Rng(seed.wrapping_mul(0x9E3779B97F4A7C15) | 1);
    let laws = Laws::new(&mut rng);
    let dir = "experiments/e002_genome_map/results";
    let prefix = format!("{dir}/seed{seed}_");

    // 1. Random genomes.
    let mut f = std::fs::File::create(format!("{prefix}random.csv")).unwrap();
    write!(f, "id,n_genes,n_edges,decode_ns").unwrap();
    for name in TRAIT_NAMES {
        write!(f, ",{name}").unwrap();
    }
    writeln!(f).unwrap();
    let mut genomes = Vec::with_capacity(N_RANDOM);
    let mut traits_all = Vec::with_capacity(N_RANDOM);
    let mut gene_counts = Vec::with_capacity(N_RANDOM);
    let mut total_ns = 0u128;
    let mut total_edges = 0usize;
    let mut regulated = 0usize;
    for id in 0..N_RANDOM {
        let g = random_genome(&mut rng);
        let t0 = Instant::now();
        let (tr, n, edges) = decode(&g, &laws);
        let ns = t0.elapsed().as_nanos();
        total_ns += ns;
        total_edges += edges;
        if edges > 0 {
            regulated += 1;
        }
        write!(f, "{id},{n},{edges},{ns}").unwrap();
        for v in &tr {
            write!(f, ",{v:.4}").unwrap();
        }
        writeln!(f).unwrap();
        genomes.push(g);
        traits_all.push(tr);
        gene_counts.push(n);
    }

    // 2. One point mutation.
    let mut f = std::fs::File::create(format!("{prefix}mutation.csv")).unwrap();
    write!(f, "id,n_genes_before,n_genes_after,dist").unwrap();
    for name in TRAIT_NAMES {
        write!(f, ",d_{name}").unwrap();
    }
    writeln!(f).unwrap();
    let mut mut_d = Vec::with_capacity(N_MUT);
    for id in 0..N_MUT {
        let mut g = genomes[id].clone();
        let pos = rng.below(N);
        g[pos] = (g[pos] + 1 + rng.below(3) as u8) % 4;
        let (tr, n, _) = decode(&g, &laws);
        let d = dist(&traits_all[id], &tr);
        write!(f, "{id},{},{n},{d:.5}", gene_counts[id]).unwrap();
        for k in 0..K {
            write!(f, ",{:.5}", (tr[k] - traits_all[id][k]).abs()).unwrap();
        }
        writeln!(f).unwrap();
        mut_d.push(d);
    }

    // 3. Random pairs (baseline distance).
    let mut f = std::fs::File::create(format!("{prefix}pairs.csv")).unwrap();
    writeln!(f, "a,b,dist").unwrap();
    let mut pair_d = Vec::with_capacity(N_PAIRS);
    for _ in 0..N_PAIRS {
        let a = rng.below(N_RANDOM);
        let b = rng.below(N_RANDOM);
        let d = dist(&traits_all[a], &traits_all[b]);
        writeln!(f, "{a},{b},{d:.5}").unwrap();
        pair_d.push(d);
    }

    // Summary.
    println!("seed {seed}: N={N} promoter={PROMOTER:?} gene_len={GENE_LEN} T={T} K={K}");
    println!("random genomes: {N_RANDOM}, mean decode {:.1} us", total_ns as f64 / N_RANDOM as f64 / 1000.0);
    let zero = gene_counts.iter().filter(|&&n| n == 0).count();
    let mean_genes = gene_counts.iter().sum::<usize>() as f64 / N_RANDOM as f64;
    println!(
        "genes per genome: mean {mean_genes:.2} min {} max {} zero-gene genomes {zero}",
        gene_counts.iter().min().unwrap(),
        gene_counts.iter().max().unwrap()
    );
    println!(
        "binding edges per genome: mean {:.2}; genomes with at least one edge {:.1}%",
        total_edges as f64 / N_RANDOM as f64,
        regulated as f64 / N_RANDOM as f64 * 100.0
    );
    println!("trait        mean   std    min    max");
    for k in 0..K {
        let vals: Vec<f32> = traits_all.iter().map(|t| t[k]).collect();
        let mean = vals.iter().sum::<f32>() / vals.len() as f32;
        let var = vals.iter().map(|v| (v - mean) * (v - mean)).sum::<f32>() / vals.len() as f32;
        let min = vals.iter().cloned().fold(f32::INFINITY, f32::min);
        let max = vals.iter().cloned().fold(f32::NEG_INFINITY, f32::max);
        println!("{:<12} {mean:.3}  {:.3}  {min:.3}  {max:.3}", TRAIT_NAMES[k], var.sqrt());
    }
    mut_d.sort_by(|a, b| a.partial_cmp(b).unwrap());
    pair_d.sort_by(|a, b| a.partial_cmp(b).unwrap());
    let neutral = mut_d.iter().filter(|&&d| d < 1e-6).count() as f32 / N_MUT as f32;
    println!(
        "one mutation: neutral {:.1}%  median {:.4}  p90 {:.4}  max {:.4}",
        neutral * 100.0,
        percentile(&mut_d, 0.5),
        percentile(&mut_d, 0.9),
        mut_d.last().unwrap()
    );
    println!(
        "random pairs: median {:.4}  p10 {:.4}  p90 {:.4}",
        percentile(&pair_d, 0.5),
        percentile(&pair_d, 0.1),
        percentile(&pair_d, 0.9)
    );
}
