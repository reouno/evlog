//! Random numbers and smooth noise on the torus (e061's, with a finest scale and a normalisation).

pub struct Rng(pub u64);

impl Rng {
    pub fn new(seed: u64) -> Self {
        Rng(seed.wrapping_mul(0x9E37_79B9_7F4A_7C15) | 1)
    }
    pub fn next_u64(&mut self) -> u64 {
        let mut x = self.0;
        x ^= x >> 12;
        x ^= x << 25;
        x ^= x >> 27;
        self.0 = x;
        x.wrapping_mul(0x2545_F491_4F6C_DD1D)
    }
    pub fn f64(&mut self) -> f64 {
        (self.next_u64() >> 11) as f64 / (1u64 << 53) as f64
    }
    pub fn below(&mut self, n: usize) -> usize {
        (self.next_u64() % n as u64) as usize
    }
    /// A Poisson count with mean `m` (by multiplication; `m` is small here).
    pub fn poisson(&mut self, m: f64) -> usize {
        let l = (-m).exp();
        let (mut k, mut p) = (0, self.f64());
        while p > l {
            k += 1;
            p *= self.f64();
        }
        k
    }
}

fn fade(t: f64) -> f64 {
    t * t * t * (t * (t * 6.0 - 15.0) + 10.0)
}

/// Octaves of smooth lattice noise on the torus: the first with a lattice point every `grain` cells,
/// each next with twice as many points at `rough` of the amplitude, down to `finest` cells.
pub fn noise(n: usize, seed: u64, grain: f64, rough: f64, finest: f64) -> Vec<f64> {
    let mut rng = Rng::new(seed);
    let mut h = vec![0.0f64; n * n];
    let mut k = ((n as f64 / grain).round() as usize).max(1);
    let mut amp = 1.0;
    while n as f64 / k as f64 >= finest.max(2.0) {
        let lattice: Vec<f64> = (0..k * k).map(|_| rng.f64() * 2.0 - 1.0).collect();
        let spacing = n as f64 / k as f64;
        let axis: Vec<(usize, usize, f64)> = (0..n)
            .map(|i| {
                let u = i as f64 / spacing;
                let f = u.floor();
                let i0 = (f as usize) % k;
                (i0, (i0 + 1) % k, fade(u - f))
            })
            .collect();
        for (y, &(y0, y1, fy)) in axis.iter().enumerate() {
            for (x, &(x0, x1, fx)) in axis.iter().enumerate() {
                let a = lattice[y0 * k + x0] + (lattice[y0 * k + x1] - lattice[y0 * k + x0]) * fx;
                let b = lattice[y1 * k + x0] + (lattice[y1 * k + x1] - lattice[y1 * k + x0]) * fx;
                h[y * n + x] += amp * (a + (b - a) * fy);
            }
        }
        k *= 2;
        amp *= rough;
    }
    h
}

/// The same field shifted to mean 0 and scaled to a spread of 1.
pub fn normalised(mut v: Vec<f64>) -> Vec<f64> {
    let m = v.iter().sum::<f64>() / v.len() as f64;
    let s = (v.iter().map(|x| (x - m) * (x - m)).sum::<f64>() / v.len() as f64).sqrt().max(1e-12);
    v.iter_mut().for_each(|x| *x = (*x - m) / s);
    v
}
