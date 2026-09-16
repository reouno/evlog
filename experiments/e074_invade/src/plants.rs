//! Stage B's producers (#75): grass, wood and algae as fields of matter on the climate's clock,
//! the litter they drop, and fire.
//!
//! Every cell holds matter in its soil, in its three producers and in its litter; the world holds
//! some in the air. Nothing makes or destroys matter: a producer grows out of the soil of its
//! cell, what dies of it lies as litter (algae sink into the water's soil), litter rots into the
//! soil, fire sends what it burns to the air and the soil, and the air falls with the rain.
//!
//! **Growth.** A producer grows `rate` x sun x warmth x water x cover a step, taken from the soil:
//! the sun is the climate's light (1 with the sun overhead), the warmth goes from 0 at 5 C to 1 at
//! 20 C (e061's bands), the water is the ground's fill on land, and the cover is s / (s + half),
//! the share of the light a stand of s matter takes. Grass's half is small (a stand of grass is
//! all leaf), wood's large (most of a tree is trunk that takes no light), so wood needs better
//! ground to stand but, standing, it shades the grass under it by its own cover. Algae grow only
//! in water (the sea, and pools of 500 mm), slowed by the depth: the light reaches the bottom of
//! shallow water only, and the matter the algae need sinks out of reach in deep water.
//!
//! **Seed.** A cell with none of a producer can get it only from its four neighbors: s counts
//! `SEED` of their mean. A producer that dies out of a place comes back from its edges.
//!
//! **Death and rot.** A producer loses its standing matter over its life. Litter rots by warmth x
//! water, so it piles up where the ground is cold or dry.
//!
//! **Fire.** A land cell burns when its ground is dry (a third full, e061's dry band), warm, and
//! holds grass or litter (the fuel). A strike hits each cell with chance `ignite` an update, and a
//! fire spreads from every cell that caught in the last update to its four neighbors; a cell
//! catches with chance fuel / (fuel + FUEL). A burning cell loses its fuel and the share fuel /
//! (fuel + wood) of its wood: a closed forest shrugs off a fire that kills trees standing in grass.
//! Half of what burns goes to the air, the rest is ash in the soil.
//!
//! **The dead of the bodies** (e063). A cell also holds `carrion`: what dies of a body and a block
//! broken off one that nobody ate. A gut takes from the grass and the carrion of its cell in their
//! proportions (`take`), and the carrion rots into the cell's soil at CARRION_ROT a step (e017),
//! on the producers' clock. Nothing else here changed from e062.
//!
//! **The water's bottom** (e065, `water = 1`). The algae's dead sink and lie on the bottom as
//! litter, which rots as the land's does (warmth x water), instead of going straight to the water's
//! soil. A gut at the surface takes the algae (`take_algae`); a gut on the bottom takes that litter
//! and the carrion (`take_bottom`). A gut on land takes the grass and the carrion, as before.
//!
//! **The crown's yield** (e073, `wood_yield`, #89). A stand of wood drops `wood_yield` of `browse`
//! per unit of what it stands a step, out of its cell's soil and beside its own growth, so a forest
//! feeds a body every year instead of once. The trunk is not touched: the stand keeps its shade and
//! its fire. Browse uneaten rots into the soil at the litter's rate (warmth x water), so it keeps
//! where the ground is cold or dry. Only a body with a tooth of `wood_hard` takes it (`take_with_wood`).

use crate::climate::{Rng, World};
use crate::habitat::POOL;
use crate::Params;

pub const GRASS_LIFE: f64 = 2_000.0; // steps: grass is leaf, it dies back within a season
pub const WOOD_LIFE: f64 = 20_000.0; // steps: a trunk outlasts a year of 20,000 steps
pub const ALGAE_LIFE: f64 = 500.0; // steps: algae turn over within a few lives of a body
pub const GRASS_HALF: f64 = 0.2; // matter at which a stand of grass takes half its light
pub const WOOD_HALF: f64 = 4.0; // for wood
pub const ALGAE_HALF: f64 = 0.1; // for algae
pub const SEED: f64 = 0.1; // share of the neighbors' mean stand that seeds a cell
pub const WARM_FROM: f64 = 5.0; // C: nothing grows or rots below (e061's cold band)
pub const WARM_FULL: f64 = 20.0; // C: full growth from here (e061's hot band)
pub const LIGHT_DEPTH: f64 = 200.0; // m of water under which algae grow at half the rate (the shelf)
pub const ROT: f64 = 1.0 / 2_000.0; // share of the litter that rots a step in warm, wet ground
pub const BURN_DRY: f64 = 1.0 / 3.0; // a land cell burns under this fill (e061's dry band)
pub const FUEL: f64 = 1.0; // fuel at which a cell catches half the time
pub const SMOKE: f64 = 0.5; // share of what burns that goes to the air
pub const START_GRASS: f64 = 0.5; // matter on every land cell at the start
pub const START_WOOD: f64 = 1.0;
pub const START_ALGAE: f64 = 0.1; // on every water cell
pub const CARRION_ROT: f64 = 0.01; // e017: share of the dead lying on a cell that rots into its soil a step

/// What moved in an update.
#[derive(Default, Clone, Copy)]
pub struct Flow {
    pub grass: f64, // grown
    pub wood: f64,
    pub browse: f64, // e073: dropped by the crowns
    pub algae: f64,
    pub burnt: f64,  // matter burnt
    pub caught: u32, // cells that caught fire
    pub ignitions: u32,
    pub fell: f64, // matter from the air to the soil
}

pub struct Plants {
    pub grass: Vec<f64>,
    pub wood: Vec<f64>,
    pub browse: Vec<f64>, // e073: what the crowns dropped and nothing has eaten
    pub algae: Vec<f64>,
    pub litter: Vec<f64>,
    pub carrion: Vec<f64>, // e063: the dead of the bodies
    pub soil: Vec<f64>,
    pub air: f64,
    pub front: Vec<(u32, u32)>, // the cells that caught fire in the last update, and their fire
    next: Vec<(u32, u32)>,
    pub burnt_in: Vec<u32>,   // the year a cell last burnt (0: never)
    pub fire_sizes: Vec<u32>, // cells burnt by every fire of the run, by the order they started
    nb_grass: Vec<f64>,
    nb_wood: Vec<f64>,
    nb_algae: Vec<f64>,
    pub rng: Rng,
}

/// The mean of the four neighbors of every cell, on the torus.
fn neighbors(n: usize, f: &[f64], out: &mut [f64]) {
    for y in 0..n {
        let (yu, yd) = (if y == 0 { n - 1 } else { y - 1 }, if y + 1 == n { 0 } else { y + 1 });
        for x in 0..n {
            let (xl, xr) = (if x == 0 { n - 1 } else { x - 1 }, if x + 1 == n { 0 } else { x + 1 });
            out[y * n + x] = 0.25 * (f[yu * n + x] + f[yd * n + x] + f[y * n + xl] + f[y * n + xr]);
        }
    }
}

/// A Poisson draw (Knuth's product of uniforms; a normal draw past 30).
fn poisson(rng: &mut Rng, lambda: f64) -> u32 {
    if lambda <= 0.0 {
        return 0;
    }
    if lambda > 30.0 {
        let (u1, u2) = (rng.f64().max(1e-300), rng.f64());
        let z = (-2.0 * u1.ln()).sqrt() * (std::f64::consts::TAU * u2).cos();
        return (lambda + lambda.sqrt() * z).round().max(0.0) as u32;
    }
    let l = (-lambda).exp();
    let mut k = 0;
    let mut prod = rng.f64();
    while prod > l {
        k += 1;
        prod *= rng.f64();
    }
    k
}

/// The depth of the water a cell is under (m), or None on dry land.
pub fn depth(w: &World, p: &Params, c: usize) -> Option<f64> {
    if w.sea[c] {
        Some(-w.elev[c])
    } else {
        let standing = w.ground[c] - p.soil;
        (standing >= POOL).then(|| standing / 1000.0)
    }
}

/// Take at most `bite` from two stores in their proportions. Returns what each gave.
fn take_both(x: &mut f64, y: &mut f64, bite: f64) -> (f64, f64) {
    let (a, b) = (*x, *y);
    let all = a + b;
    if all <= 0.0 {
        return (0.0, 0.0);
    }
    if bite >= all {
        *x = 0.0;
        *y = 0.0;
        return (a, b);
    }
    let first = bite * a / all;
    let second = bite - first;
    *x = a - first;
    *y = b - second;
    (first, second)
}

impl Plants {
    pub fn new(w: &World, p: &Params) -> Self {
        let cells = w.n * w.n;
        let mut pl = Plants {
            grass: vec![0.0; cells],
            wood: vec![0.0; cells],
            browse: vec![0.0; cells],
            algae: vec![0.0; cells],
            litter: vec![0.0; cells],
            carrion: vec![0.0; cells],
            soil: vec![p.matter; cells],
            air: 0.0,
            front: Vec::new(),
            next: Vec::new(),
            burnt_in: vec![0; cells],
            fire_sizes: Vec::new(),
            nb_grass: vec![0.0; cells],
            nb_wood: vec![0.0; cells],
            nb_algae: vec![0.0; cells],
            rng: Rng::new(p.seed as u64 ^ 0x62),
        };
        for c in 0..cells {
            if depth(w, p, c).is_some() {
                pl.algae[c] = START_ALGAE;
            } else {
                pl.grass[c] = START_GRASS;
                pl.wood[c] = START_WOOD;
            }
            pl.soil[c] -= pl.algae[c] + pl.grass[c] + pl.wood[c];
        }
        pl
    }

    pub fn matter(&self) -> f64 {
        let cells: f64 = (0..self.soil.len()).map(|c| self.soil[c] + self.grass[c] + self.wood[c] + self.browse[c] + self.algae[c] + self.litter[c] + self.carrion[c]).sum();
        cells + self.air
    }

    /// A gut on land takes at most `bite` from cell `c`: the grass and the carrion in their
    /// proportions. Returns (plant, dead) taken.
    pub fn take(&mut self, c: usize, bite: f64) -> (f64, f64) {
        take_both(&mut self.grass[c], &mut self.carrion[c], bite)
    }

    /// e072 (set B) and e073: a gut on land in a body with a tooth hard enough for wood takes at most
    /// `bite` from the grass, the carrion, `share` of the standing wood and all of the browse the
    /// crowns dropped on cell `c`, in their proportions. Returns (grass, dead, wood, browse) taken.
    pub fn take_with_wood(&mut self, c: usize, bite: f64, share: f64) -> (f64, f64, f64, f64) {
        let (g, d) = (self.grass[c].max(0.0), self.carrion[c].max(0.0));
        let (w, b) = ((self.wood[c] * share).max(0.0), self.browse[c].max(0.0));
        let all = g + d + w + b;
        if all <= 0.0 {
            return (0.0, 0.0, 0.0, 0.0);
        }
        let k = (bite / all).min(1.0);
        let (tg, td, tw, tb) = (g * k, d * k, w * k, b * k);
        self.grass[c] -= tg;
        self.carrion[c] -= td;
        self.wood[c] -= tw;
        self.browse[c] -= tb;
        (tg, td, tw, tb)
    }

    /// A gut in the water's surface layer (e065) takes at most `bite` of the algae of cell `c`.
    pub fn take_algae(&mut self, c: usize, bite: f64) -> f64 {
        let a = self.algae[c];
        if bite >= a {
            self.algae[c] = 0.0;
            return a.max(0.0);
        }
        self.algae[c] = a - bite;
        bite
    }

    /// A gut on the water's bottom (e065) takes at most `bite` of what sank to cell `c`: the algae's
    /// dead (its litter) and the carrion, in their proportions. Returns (litter, dead) taken.
    pub fn take_bottom(&mut self, c: usize, bite: f64) -> (f64, f64) {
        take_both(&mut self.litter[c], &mut self.carrion[c], bite)
    }

    fn burnable(&self, w: &World, p: &Params, c: usize) -> bool {
        !w.sea[c] && w.ground[c] < BURN_DRY * p.soil && w.temp[c] > WARM_FROM && self.grass[c] + self.litter[c] > 0.0
    }

    /// Cell `c` burns: its fuel, and the share of its wood the fuel stands for.
    fn burn(&mut self, c: usize, year: u32, f: &mut Flow) {
        let fuel = self.grass[c] + self.litter[c];
        let wood = self.wood[c] * fuel / (fuel + self.wood[c]);
        let total = fuel + wood;
        self.grass[c] = 0.0;
        self.litter[c] = 0.0;
        self.wood[c] -= wood;
        let smoke = SMOKE * total;
        self.air += smoke;
        self.soil[c] += total - smoke;
        self.burnt_in[c] = year;
        f.burnt += total;
        f.caught += 1;
    }

    /// One update, after the climate's.
    pub fn update(&mut self, w: &World, p: &Params, year: u32) -> Flow {
        let n = w.n;
        let cells = n * n;
        let tick = p.tick;
        let mut f = Flow::default();
        neighbors(n, &self.grass, &mut self.nb_grass);
        neighbors(n, &self.wood, &mut self.nb_wood);
        neighbors(n, &self.algae, &mut self.nb_algae);
        let carrion_rot = 1.0 - (1.0 - CARRION_ROT).powf(tick);

        for c in 0..cells {
            if self.carrion[c] > 0.0 {
                let r = self.carrion[c] * carrion_rot;
                self.carrion[c] -= r;
                self.soil[c] += r;
            }
            let warm = ((w.temp[c] - WARM_FROM) / (WARM_FULL - WARM_FROM)).clamp(0.0, 1.0);
            let sun = w.light[c] * warm;
            let (g, wd, a, lit) = (self.grass[c], self.wood[c], self.algae[c], self.litter[c]);
            let (mut grow_g, mut grow_w, mut grow_a) = (0.0, 0.0, 0.0);
            let mut drop_b = 0.0;
            let wet = match depth(w, p, c) {
                Some(d) => {
                    let s = a + SEED * self.nb_algae[c];
                    grow_a = p.algae_rate * tick * sun / (1.0 + d / LIGHT_DEPTH) * s / (s + ALGAE_HALF);
                    1.0
                }
                None => {
                    let wet = (w.ground[c] / p.soil).min(1.0);
                    let q = sun * wet;
                    let sw = wd + SEED * self.nb_wood[c];
                    grow_w = p.wood_rate * tick * q * sw / (sw + WOOD_HALF);
                    drop_b = p.wood_yield * tick * wd; // e073: the crown's yield follows the stand
                    let sg = g + SEED * self.nb_grass[c];
                    grow_g = p.grass_rate * tick * q * (1.0 - wd / (wd + WOOD_HALF)) * sg / (sg + GRASS_HALF);
                    wet
                }
            };
            let want = grow_g + grow_w + grow_a + drop_b;
            let soil = self.soil[c].max(0.0);
            if want > soil {
                let k = soil / want;
                grow_g *= k;
                grow_w *= k;
                grow_a *= k;
                drop_b *= k;
            }
            let die_g = g * tick / GRASS_LIFE;
            let die_w = wd * tick / WOOD_LIFE;
            let die_a = a * tick / ALGAE_LIFE;
            let rot = lit * (ROT * tick * warm * wet).min(1.0);
            let rot_b = self.browse[c] * (ROT * tick * warm * wet).min(1.0); // e073: browse rots as litter does
            self.browse[c] += drop_b - rot_b;
            self.grass[c] = g + grow_g - die_g;
            self.wood[c] = wd + grow_w - die_w;
            self.algae[c] = a + grow_a - die_a;
            if p.water > 0.0 {
                // e065: the algae's dead sink and lie on the bottom as litter before they rot.
                self.litter[c] = lit + die_g + die_w + die_a - rot;
                self.soil[c] += rot + rot_b - (grow_g + grow_w + grow_a + drop_b);
            } else {
                self.litter[c] = lit + die_g + die_w - rot;
                self.soil[c] += die_a + rot + rot_b - (grow_g + grow_w + grow_a + drop_b);
            }
            f.grass += grow_g;
            f.wood += grow_w;
            f.browse += drop_b;
            f.algae += grow_a;
        }

        // Fire: what caught in the last update spreads to its neighbors, then the strikes.
        let front = std::mem::take(&mut self.front);
        let mut next = std::mem::take(&mut self.next);
        next.clear();
        for &(c, id) in &front {
            let (x, y) = (c as usize % n, c as usize / n);
            let nb = [(y + n - 1) % n * n + x, (y + 1) % n * n + x, y * n + (x + 1) % n, y * n + (x + n - 1) % n];
            for m in nb {
                if self.burnable(w, p, m) {
                    let fuel = self.grass[m] + self.litter[m];
                    if self.rng.f64() < fuel / (fuel + FUEL) {
                        self.burn(m, year, &mut f);
                        self.fire_sizes[id as usize] += 1;
                        next.push((m as u32, id));
                    }
                }
            }
        }
        let strikes = poisson(&mut self.rng, p.ignite * cells as f64);
        for _ in 0..strikes {
            let c = (self.rng.next_u64() % cells as u64) as usize;
            if self.burnable(w, p, c) {
                let fuel = self.grass[c] + self.litter[c];
                if self.rng.f64() < fuel / (fuel + FUEL) {
                    let id = self.fire_sizes.len() as u32;
                    self.fire_sizes.push(1);
                    self.burn(c, year, &mut f);
                    next.push((c as u32, id));
                    f.ignitions += 1;
                }
            }
        }
        self.front = next;
        self.next = front;

        // The air falls with the rain, on each cell by its share of the rain.
        let rain: f64 = w.rain_now.iter().sum();
        if self.air > 0.0 && rain > 0.0 {
            let per = self.air / rain;
            let mut fell = 0.0;
            for c in 0..cells {
                let r = w.rain_now[c];
                if r > 0.0 {
                    let d = r * per;
                    self.soil[c] += d;
                    fell += d;
                }
            }
            self.air -= fell;
            f.fell = fell;
        }
        f
    }
}
