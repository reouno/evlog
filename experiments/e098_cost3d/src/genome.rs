//! The genome and the network, shared by both arms of the spike. Copied from e097's `body.rs`
//! unchanged: nothing here knows how many axes a body has. What the geometry decides - how wide the
//! morphogen table is and how wide the policy is - each arm builds for itself.

pub const N: usize = 512;
const PROMOTER: [u8; 3] = [0, 1, 0];
const GENE_LEN: usize = 8;
pub const TAG_LEN: usize = 4;
pub const T: usize = 40;

pub struct Rng(pub u64);

impl Rng {
    pub fn next_u64(&mut self) -> u64 {
        let mut x = self.0;
        x ^= x >> 12;
        x ^= x << 25;
        x ^= x >> 27;
        self.0 = x;
        x.wrapping_mul(0x2545F4914F6CDD1D)
    }
    pub fn f32(&mut self) -> f32 {
        (self.next_u64() >> 40) as f32 / (1u64 << 24) as f32
    }
    pub fn f64(&mut self) -> f64 {
        (self.next_u64() >> 11) as f64 / (1u64 << 53) as f64
    }
    pub fn below(&mut self, n: usize) -> usize {
        (self.next_u64() % n as u64) as usize
    }
}

#[derive(Clone)]
pub struct Gene {
    pub tag: [u8; TAG_LEN],
    pub product: [u8; TAG_LEN],
}

impl Gene {
    pub fn key(&self) -> u16 {
        self.tag.iter().chain(&self.product).fold(0, |acc, &s| acc * 4 + s as u16)
    }
}

pub fn sorted_keys(genes: &[Gene]) -> Vec<u16> {
    let mut k: Vec<u16> = genes.iter().map(Gene::key).collect();
    k.sort_unstable();
    k
}

pub fn parse_genes(genome: &[u8]) -> Vec<Gene> {
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

pub fn pattern_index(p: &[u8; TAG_LEN]) -> usize {
    p.iter().fold(0, |acc, &s| acc * 4 + s as usize)
}

pub fn bind(product: &[u8; TAG_LEN], tag: &[u8; TAG_LEN]) -> f32 {
    let m = product.iter().zip(tag).filter(|(a, b)| a == b).count();
    if m < 3 {
        return 0.0;
    }
    let sign = if product[0] < 2 { 1.0 } else { -1.0 };
    sign * (m as f32 - 2.0) / 2.0
}

pub fn bind_morphogen(morphogen: &[u8; TAG_LEN], tag: &[u8; TAG_LEN]) -> f32 {
    let m = morphogen.iter().zip(tag).filter(|(a, b)| a == b).count();
    if m < 2 {
        return 0.0;
    }
    let sign = if morphogen[0] < 2 { 1.0 } else { -1.0 };
    sign * m as f32 / 4.0
}

pub fn sigmoid(x: f32) -> f32 {
    1.0 / (1.0 + (-x).exp())
}

/// The network settled in `nctx` contexts at once (e004); every context its own run. The number of
/// contexts is the cells of the body's grid, which is what 3D changes: 256 -> 512 at the cap, and
/// what a body actually grows (side 6 in the control) 36 -> 216.
pub fn settle(n: usize, w: &[f32], wm: &[f32], morph: &[Vec<f32>], nctx: usize) -> Vec<f32> {
    let n_morph = morph.len();
    let mut level = vec![0.5f32; n * nctx];
    let mut next = vec![0.0f32; n * nctx];
    let mut acc = vec![0.0f32; nctx];
    for _ in 0..T {
        for i in 0..n {
            acc.fill(0.0);
            for j in 0..n {
                let wij = w[i * n + j];
                for (a, &l) in acc.iter_mut().zip(&level[j * nctx..(j + 1) * nctx]) {
                    *a += wij * l;
                }
            }
            for (m, mo) in morph.iter().enumerate() {
                let wim = wm[i * n_morph + m];
                for (a, &l) in acc.iter_mut().zip(&mo[..nctx]) {
                    *a += wim * l;
                }
            }
            for (o, &a) in next[i * nctx..(i + 1) * nctx].iter_mut().zip(&acc) {
                *o = sigmoid(3.0 * a - 1.0);
            }
        }
        std::mem::swap(&mut level, &mut next);
    }
    level
}

/// A random genome, as e063 seeds the world with.
pub fn random_genome(rng: &mut Rng) -> Vec<u8> {
    (0..N).map(|_| rng.below(4) as u8).collect()
}

pub const MUTATION: f32 = 2.0 / N as f32;

pub fn mutate(genome: &mut [u8], rng: &mut Rng) {
    for base in genome.iter_mut() {
        if rng.f32() < MUTATION {
            *base = (*base + 1 + rng.below(3) as u8) % 4;
        }
    }
}
