//! e004: shape from the genome. The e002 gene network is run once per cell of an
//! 8x8 grid, with the cell's position fed in as fixed "morphogen" signals. The settled
//! expression of each cell decides whether it holds a block and of which kind.
//! Tested on its own, no world.

use std::collections::HashSet;
use std::io::Write;
use std::time::Instant;

// Genome and network, as e002/e003.
const N: usize = 512;
const PROMOTER: [u8; 3] = [0, 1, 0];
const GENE_LEN: usize = 8;
const TAG_LEN: usize = 4;
const T: usize = 40;

// Body.
const SIDE: usize = 8;
const CELLS: usize = SIDE * SIDE;
const N_KINDS: usize = 5; // 0 = empty, then hard, muscle, sensor, digestive
const KIND_NAMES: [&str; N_KINDS] = ["empty", "hard", "muscle", "sensor", "digestive"];
const N_MORPH: usize = 6; // x, 1-x, y, 1-y, r, 1-r; each stretched to [-1, 1]

const N_RANDOM: usize = 5000;
const N_MUT: usize = 2000;
const N_PAIRS: usize = 2000;
const GALLERY: usize = 40;
const N_FAMILIES: usize = 4;
const FAMILY_CHILDREN: usize = 7;
const WALK_LEN: usize = 32;

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

/// The fixed "laws": morphogen products and the product -> kind table. Same for every genome.
struct Laws {
    morphogen: [[u8; TAG_LEN]; N_MORPH],
    table: Vec<[f32; N_KINDS]>, // indexed by product pattern (256 entries)
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
                let mut row = [0.0; N_KINDS];
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

fn random_genome(rng: &mut Rng) -> Vec<u8> {
    (0..N).map(|_| rng.below(4) as u8).collect()
}

fn mutate(genome: &mut [u8], rng: &mut Rng) {
    let pos = rng.below(genome.len());
    genome[pos] = (genome[pos] + 1 + rng.below(3) as u8) % 4;
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

/// Binding weight of a product on a tag (as e002): match >= 3 of 4 binds, 0.5 or 1.0, signed by the product.
fn bind(product: &[u8; TAG_LEN], tag: &[u8; TAG_LEN]) -> f32 {
    let m = product.iter().zip(tag).filter(|(a, b)| a == b).count();
    if m < 3 {
        return 0.0;
    }
    let sign = if product[0] < 2 { 1.0 } else { -1.0 };
    sign * (m as f32 - 2.0) / 2.0
}

/// A morphogen is a broad signal: it binds on 2 or more matching symbols, weight m/4.
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

struct Body {
    cells: [u8; CELLS],
    n_genes: usize,
    gene_edges: usize,
    morph_edges: usize,
}

/// Development: for each cell, run the network with the cell's morphogen levels as extra input,
/// then read the kind with the highest score (empty wins ties).
fn develop(genome: &[u8], laws: &Laws) -> Body {
    let genes = parse_genes(genome);
    let n = genes.len();

    let mut w = vec![0.0f32; n * n]; // gene j acting on gene i
    let mut wm = vec![0.0f32; N_MORPH * n]; // morphogen m acting on gene i
    let mut gene_edges = 0;
    let mut morph_edges = 0;
    for i in 0..n {
        for j in 0..n {
            let b = bind(&genes[j].product, &genes[i].tag);
            if b != 0.0 {
                gene_edges += 1;
            }
            w[j * n + i] = b;
        }
        for m in 0..N_MORPH {
            let b = bind_morphogen(&laws.morphogen[m], &genes[i].tag);
            if b != 0.0 {
                morph_edges += 1;
            }
            wm[m * n + i] = b;
        }
    }
    let rows: Vec<&[f32; N_KINDS]> = genes.iter().map(|g| &laws.table[pattern_index(&g.product)]).collect();

    let mut cells = [0u8; CELLS];
    let mut level = vec![0.0f32; n];
    let mut next = vec![0.0f32; n];
    for (c, cell) in cells.iter_mut().enumerate() {
        let morph = &laws.morph_level[c];
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
            std::mem::swap(&mut level, &mut next);
        }
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
    }
    Body { cells, n_genes: n, gene_edges, morph_edges }
}

fn kind_counts(cells: &[u8; CELLS]) -> [usize; N_KINDS] {
    let mut c = [0; N_KINDS];
    for &k in cells {
        c[k as usize] += 1;
    }
    c
}

/// Size of the largest 4-connected group of non-empty cells.
fn largest_component(cells: &[u8; CELLS]) -> usize {
    let mut seen = [false; CELLS];
    let mut best = 0;
    let mut stack = Vec::new();
    for start in 0..CELLS {
        if cells[start] == 0 || seen[start] {
            continue;
        }
        let mut size = 0;
        seen[start] = true;
        stack.push(start);
        while let Some(c) = stack.pop() {
            size += 1;
            let (x, y) = (c % SIDE, c / SIDE);
            let mut nb = Vec::with_capacity(4);
            if x > 0 { nb.push(c - 1); }
            if x + 1 < SIDE { nb.push(c + 1); }
            if y > 0 { nb.push(c - SIDE); }
            if y + 1 < SIDE { nb.push(c + SIDE); }
            for d in nb {
                if cells[d] != 0 && !seen[d] {
                    seen[d] = true;
                    stack.push(d);
                }
            }
        }
        best = best.max(size);
    }
    best
}

/// Number of cells that differ (kind-aware), 0..64.
fn dist(a: &[u8; CELLS], b: &[u8; CELLS]) -> usize {
    a.iter().zip(b).filter(|(x, y)| x != y).count()
}

fn cells_str(cells: &[u8; CELLS]) -> String {
    cells.iter().map(|&k| (b'0' + k) as char).collect()
}

fn percentile(sorted: &[usize], p: f32) -> usize {
    sorted[((sorted.len() - 1) as f32 * p).round() as usize]
}

fn main() {
    let seed: u64 = std::env::args().nth(1).and_then(|s| s.parse().ok()).unwrap_or(1);
    let mut rng = Rng(seed.wrapping_mul(0x9E3779B97F4A7C15) | 1);
    let laws = Laws::new(&mut rng);
    let dir = "experiments/e004_genome_shape/results";
    let prefix = format!("{dir}/seed{seed}_");

    // 1. Random genomes.
    let mut f = std::fs::File::create(format!("{prefix}random.csv")).unwrap();
    writeln!(f, "id,n_genes,gene_edges,morph_edges,n_blocks,hard,muscle,sensor,digestive,largest,connected,dev_ns").unwrap();
    let mut genomes = Vec::with_capacity(N_RANDOM);
    let mut bodies = Vec::with_capacity(N_RANDOM);
    let mut total_ns = 0u128;
    let mut distinct = HashSet::new();
    let (mut empty, mut full, mut connected, mut uniform, mut with_morph) = (0, 0, 0, 0, 0);
    let mut kind_total = [0usize; N_KINDS];
    let mut blocks_hist = [0usize; CELLS + 1];
    let mut n_kinds_hist = [0usize; N_KINDS];
    for id in 0..N_RANDOM {
        let g = random_genome(&mut rng);
        let t0 = Instant::now();
        let b = develop(&g, &laws);
        let ns = t0.elapsed().as_nanos();
        total_ns += ns;
        let kc = kind_counts(&b.cells);
        let n_blocks = CELLS - kc[0];
        let largest = largest_component(&b.cells);
        let is_conn = n_blocks > 0 && largest == n_blocks;
        let kinds_present = kc[1..].iter().filter(|&&c| c > 0).count();
        if n_blocks == 0 { empty += 1; }
        if n_blocks == CELLS { full += 1; }
        if is_conn { connected += 1; }
        if b.cells.iter().all(|&k| k == b.cells[0]) { uniform += 1; }
        if b.morph_edges > 0 { with_morph += 1; }
        for k in 0..N_KINDS { kind_total[k] += kc[k]; }
        blocks_hist[n_blocks] += 1;
        n_kinds_hist[kinds_present] += 1;
        distinct.insert(b.cells);
        writeln!(f, "{id},{},{},{},{n_blocks},{},{},{},{},{largest},{},{ns}",
            b.n_genes, b.gene_edges, b.morph_edges, kc[1], kc[2], kc[3], kc[4], is_conn as u8).unwrap();
        genomes.push(g);
        bodies.push(b);
    }

    // 2. One point mutation (and, for reference, two).
    let mut f = std::fs::File::create(format!("{prefix}mutation.csv")).unwrap();
    writeln!(f, "id,n_blocks_before,n_blocks_after,dist1,dist2").unwrap();
    let mut d1 = Vec::with_capacity(N_MUT);
    let mut d2 = Vec::with_capacity(N_MUT);
    for id in 0..N_MUT {
        let mut g = genomes[id].clone();
        mutate(&mut g, &mut rng);
        let b = develop(&g, &laws);
        let a = dist(&bodies[id].cells, &b.cells);
        let mut g2 = genomes[id].clone();
        mutate(&mut g2, &mut rng);
        mutate(&mut g2, &mut rng);
        let b2 = develop(&g2, &laws);
        let c = dist(&bodies[id].cells, &b2.cells);
        writeln!(f, "{id},{},{},{a},{c}", CELLS - kind_counts(&bodies[id].cells)[0], CELLS - kind_counts(&b.cells)[0]).unwrap();
        d1.push(a);
        d2.push(c);
    }

    // 3. Random pairs (baseline).
    let mut f = std::fs::File::create(format!("{prefix}pairs.csv")).unwrap();
    writeln!(f, "a,b,dist").unwrap();
    let mut dp = Vec::with_capacity(N_PAIRS);
    for _ in 0..N_PAIRS {
        let a = rng.below(N_RANDOM);
        let b = rng.below(N_RANDOM);
        let d = dist(&bodies[a].cells, &bodies[b].cells);
        writeln!(f, "{a},{b},{d}").unwrap();
        dp.push(d);
    }

    // 4. Gallery for the report: random bodies, families (parent + children with one mutation),
    //    and one walk of successive single mutations.
    let mut f = std::fs::File::create(format!("{prefix}bodies.json")).unwrap();
    let list = |v: &[String]| v.iter().map(|s| format!("\"{s}\"")).collect::<Vec<_>>().join(",");
    let random: Vec<String> = bodies[..GALLERY].iter().map(|b| cells_str(&b.cells)).collect();
    let mut families = Vec::new();
    let mut fam_ids = Vec::new();
    for id in 0..N_RANDOM {
        let n = CELLS - kind_counts(&bodies[id].cells)[0];
        if n < 8 || n > CELLS - 8 || bodies[id].morph_edges == 0 {
            continue;
        }
        let mut children = Vec::new();
        for _ in 0..FAMILY_CHILDREN {
            let mut g = genomes[id].clone();
            mutate(&mut g, &mut rng);
            children.push(cells_str(&develop(&g, &laws).cells));
        }
        families.push(format!("{{\"id\":{id},\"parent\":\"{}\",\"children\":[{}]}}", cells_str(&bodies[id].cells), list(&children)));
        fam_ids.push(id);
        if families.len() == N_FAMILIES {
            break;
        }
    }
    let mut walk = vec![cells_str(&bodies[fam_ids[0]].cells)];
    let mut g = genomes[fam_ids[0]].clone();
    for _ in 0..WALK_LEN {
        mutate(&mut g, &mut rng);
        walk.push(cells_str(&develop(&g, &laws).cells));
    }
    writeln!(f, "{{\"side\":{SIDE},\"kinds\":[{}],\"random\":[{}],\"families\":[{}],\"walk\":[{}]}}",
        KIND_NAMES.iter().map(|k| format!("\"{k}\"")).collect::<Vec<_>>().join(","),
        list(&random), families.join(","), list(&walk)).unwrap();

    // Summary.
    println!("seed {seed}: N={N} grid={SIDE}x{SIDE} morphogens={N_MORPH} T={T}");
    println!("random genomes: {N_RANDOM}, mean develop {:.1} us", total_ns as f64 / N_RANDOM as f64 / 1000.0);
    let pct = |c: usize| c as f64 / N_RANDOM as f64 * 100.0;
    println!("bodies: empty {:.1}%  full {:.1}%  uniform {:.1}%  connected {:.1}%  genomes with a morphogen edge {:.1}%  distinct bodies {}",
        pct(empty), pct(full), pct(uniform), pct(connected), pct(with_morph), distinct.len());
    let mut nb: Vec<usize> = (0..=CELLS).flat_map(|n| std::iter::repeat(n).take(blocks_hist[n])).collect();
    nb.sort_unstable();
    println!("blocks per body: mean {:.1}  p10 {}  median {}  p90 {}", nb.iter().sum::<usize>() as f64 / N_RANDOM as f64,
        percentile(&nb, 0.1), percentile(&nb, 0.5), percentile(&nb, 0.9));
    print!("share of cells by kind:");
    for k in 0..N_KINDS {
        print!("  {} {:.1}%", KIND_NAMES[k], kind_total[k] as f64 / (N_RANDOM * CELLS) as f64 * 100.0);
    }
    println!();
    print!("kinds present per body:");
    for k in 0..N_KINDS {
        print!("  {k}: {:.1}%", pct(n_kinds_hist[k]));
    }
    println!();
    d1.sort_unstable();
    d2.sort_unstable();
    dp.sort_unstable();
    let neutral1 = d1.iter().filter(|&&d| d == 0).count() as f64 / N_MUT as f64 * 100.0;
    let neutral2 = d2.iter().filter(|&&d| d == 0).count() as f64 / N_MUT as f64 * 100.0;
    let nonzero1: Vec<usize> = d1.iter().cloned().filter(|&d| d > 0).collect();
    println!("one mutation: neutral {neutral1:.1}%  median {}  p90 {}  max {}  (non-neutral only: median {}  p90 {})",
        percentile(&d1, 0.5), percentile(&d1, 0.9), d1.last().unwrap(),
        percentile(&nonzero1, 0.5), percentile(&nonzero1, 0.9));
    println!("two mutations: neutral {neutral2:.1}%  median {}  p90 {}  max {}",
        percentile(&d2, 0.5), percentile(&d2, 0.9), d2.last().unwrap());
    println!("random pairs: median {}  p10 {}  p90 {}", percentile(&dp, 0.5), percentile(&dp, 0.1), percentile(&dp, 0.9));
    println!("gallery families from genomes {fam_ids:?}");
}
