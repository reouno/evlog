//! e087 (#93): the places a body meets by month, and the measures of a winter lived through (no law).
//!
//! The map is e086's at the same year (`places.py` writes it from `<prefix>_months.bin`): each world
//! cell's class (sea, land always fed, seasonal land, land never fed) and the months it is lean in. A
//! seasonal cell's winter is its longest run of lean months. At the start of each month every grown body
//! on a seasonal cell whose winter starts that month joins a cohort, which is read when that winter
//! ends: how many are alive, how far they went, and whether they stand on land fed that month. Every
//! body-step is counted by the class of its cell, as torpid or not, and in its cell's winter or not;
//! births and deaths by class; every grown body's death is a row of `<prefix>_grown.csv`.

use crate::body::{Agent, Grid, SUB, UPKEEP, UPKEEP_BODY};
use std::collections::HashMap;
use std::io::Write;

pub const SEA: u8 = 0;
pub const SEASONAL: u8 = 2;
pub const CLASSES: [&str; 4] = ["sea", "fed", "seasonal", "never"];
pub const YOUNG: u32 = 75; // half the dead died by this age before e087
const MONTHS: u32 = 12;

struct Entry {
    id: u64,
    end: u64,
    at: (usize, usize),
    fat: f64,
}

#[derive(Default)]
struct Row {
    steps: [u64; 4],
    torpid: [u64; 4],
    winter: [u64; 2], // body-steps on seasonal land in its winter: all, grown
    winter_torpid: [u64; 2],
    winter_temp: f64,
    births: [u64; 4],
    deaths: [u64; 4],
    young: [u64; 4],
    grown: [u64; 4],
    entered: u64,
    fat_in: f64,
    resolved: u64,
    lived: u64,
    moved: f64,
    fed_end: u64,
}

pub struct Places {
    class: Vec<u8>,
    lean: Vec<u16>,
    start: Vec<u8>, // the month a seasonal cell's winter starts
    len: Vec<u8>,   // and its months
    month: u32,
    cohort: Vec<Entry>,
    row: Row,
    months: std::fs::File,
    grown: std::io::BufWriter<std::fs::File>,
}

impl Places {
    /// Reads the map ("E087", n, then per cell its class as a byte and its lean months as a u16).
    pub fn load(path: &str, n: usize, prefix: &str) -> Option<Places> {
        let raw = std::fs::read(path).ok()?;
        assert!(&raw[..4] == b"E087" && u32::from_le_bytes(raw[4..8].try_into().unwrap()) as usize == n, "{path} is not a map of this world");
        let cells = n * n;
        let class: Vec<u8> = raw[8..8 + cells].to_vec();
        let lean: Vec<u16> = (0..cells).map(|c| u16::from_le_bytes([raw[8 + cells + 2 * c], raw[9 + cells + 2 * c]])).collect();
        let (mut start, mut len) = (vec![0u8; cells], vec![0u8; cells]);
        for c in 0..cells {
            if class[c] == SEASONAL {
                (start[c], len[c]) = longest_spell(lean[c]);
            }
        }
        let mut months = std::fs::File::create(format!("{prefix}_months.csv")).unwrap();
        let mut h = String::from("step,month");
        for pre in ["steps", "torpid", "births", "deaths", "young", "grown"] {
            for c in CLASSES {
                h.push_str(&format!(",{pre}_{c}"));
            }
        }
        h.push_str(",winter,winter_torpid,winter_grown,winter_grown_torpid,winter_temp,entered,fat_in,resolved,lived,moved,fed_end\n");
        months.write_all(h.as_bytes()).unwrap();
        let mut grown = std::io::BufWriter::new(std::fs::File::create(format!("{prefix}_grown.csv")).unwrap());
        writeln!(grown, "step,age,cause,class,travel").unwrap();
        eprintln!("places read from {path}: {} seasonal cells", class.iter().filter(|&&c| c == SEASONAL).count());
        Some(Places { class, lean, start, len, month: u32::MAX, cohort: Vec::new(), row: Row::default(), months, grown })
    }

    fn lean_now(&self, c: usize) -> bool {
        self.lean[c] >> self.month & 1 == 1
    }

    /// At the start of the bodies' step: a new month writes the last month's row, reads the cohorts
    /// whose winter has ended and takes in the grown bodies whose winter starts now.
    pub fn month(&mut self, month: u32, step: u64, month_steps: u64, agents: &[Agent], g: Grid, grown_at: u32) {
        if month == self.month {
            return;
        }
        if self.month != u32::MAX {
            self.write(step);
        }
        self.month = month;
        let alive: HashMap<u64, usize> = agents.iter().enumerate().filter(|(_, a)| a.alive).map(|(i, a)| (a.id, i)).collect();
        let r = &mut self.row;
        let mut keep = Vec::with_capacity(self.cohort.len());
        for e in std::mem::take(&mut self.cohort) {
            if e.end > step {
                keep.push(e);
                continue;
            }
            r.resolved += 1;
            if let Some(&i) = alive.get(&e.id) {
                let a = &agents[i];
                r.lived += 1;
                let dx = a.x.abs_diff(e.at.0).min(g.sw - a.x.abs_diff(e.at.0));
                let dy = a.y.abs_diff(e.at.1).min(g.sh - a.y.abs_diff(e.at.1));
                r.moved += ((dx * dx + dy * dy) as f64).sqrt() / SUB as f64;
                let c = a.here(g);
                r.fed_end += (self.class[c] != SEA && self.lean[c] >> month & 1 == 0) as u64;
            }
        }
        self.cohort = keep;
        for a in agents.iter().filter(|a| a.alive && a.age >= grown_at) {
            let c = a.here(g);
            if self.class[c] == SEASONAL && self.start[c] as u32 == month {
                let full = (UPKEEP * a.body.size as f32 + UPKEEP_BODY) as f64;
                self.cohort.push(Entry { id: a.id, end: step + self.len[c] as u64 * month_steps, at: (a.x, a.y), fat: a.fat / full });
                self.row.entered += 1;
                self.row.fat_in += a.fat / full;
            }
        }
    }

    /// A body's step: its cell's class, whether it is torpid, and whether its cell is in its winter.
    pub fn body_step(&mut self, a: &Agent, g: Grid, torpid: bool, grown_at: u32) {
        let c = a.here(g);
        let cl = self.class[c] as usize;
        let r = &mut self.row;
        r.steps[cl] += 1;
        r.torpid[cl] += torpid as u64;
        if cl == SEASONAL as usize && self.lean[c] >> self.month & 1 == 1 {
            let grown = a.age >= grown_at;
            r.winter[0] += 1;
            r.winter_torpid[0] += torpid as u64;
            r.winter[1] += grown as u64;
            r.winter_torpid[1] += (grown && torpid) as u64;
            r.winter_temp += a.temp as f64;
        }
    }

    pub fn born(&mut self, a: &Agent, g: Grid) {
        self.row.births[self.class[a.here(g)] as usize] += 1;
    }

    pub fn died(&mut self, a: &Agent, g: Grid, cause: u8, step: u64, grown_at: u32) {
        let cl = self.class[a.here(g)] as usize;
        self.row.deaths[cl] += 1;
        self.row.young[cl] += (a.age <= YOUNG) as u64;
        if a.age >= grown_at {
            self.row.grown[cl] += 1;
            writeln!(self.grown, "{step},{},{cause},{cl},{:.1}", a.age, a.travel(g)).unwrap();
        }
    }

    fn write(&mut self, step: u64) {
        let r = std::mem::take(&mut self.row);
        let mut s = format!("{step},{}", self.month);
        for v in [r.steps, r.torpid, r.births, r.deaths, r.young, r.grown] {
            for x in v {
                s.push_str(&format!(",{x}"));
            }
        }
        s.push_str(&format!(
            ",{},{},{},{},{:.2},{},{:.1},{},{},{:.2},{}\n",
            r.winter[0],
            r.winter_torpid[0],
            r.winter[1],
            r.winter_torpid[1],
            r.winter_temp / r.winter[0].max(1) as f64,
            r.entered,
            r.fat_in / r.entered.max(1) as f64,
            r.resolved,
            r.lived,
            r.moved / r.lived.max(1) as f64,
            r.fed_end
        ));
        self.months.write_all(s.as_bytes()).unwrap();
        self.grown.flush().unwrap();
    }

    /// Whether a cell is seasonal and lean this month (for tests and the viewer's reading).
    #[allow(dead_code)]
    pub fn in_winter(&self, c: usize) -> bool {
        self.class[c] == SEASONAL && self.lean_now(c)
    }
}

/// A cell's longest circular run of lean months: the month it starts and its length (1-11).
pub fn longest_spell(lean: u16) -> (u8, u8) {
    let (mut best, mut best_start) = (0u32, 0u32);
    for s in 0..MONTHS {
        // Only a run's first month starts one.
        if lean >> s & 1 == 0 || lean >> ((s + MONTHS - 1) % MONTHS) & 1 == 1 {
            continue;
        }
        let mut l = 0;
        while l < MONTHS && lean >> ((s + l) % MONTHS) & 1 == 1 {
            l += 1;
        }
        if l > best {
            (best, best_start) = (l, s);
        }
    }
    (best_start as u8, best as u8)
}

/// The share of its clock a body of temperature `t` keeps (e087, Q): q10 to the tenth of the degrees
/// it is over `lo`, at most 1 and at least `floor`.
pub fn warmth(t: f64, lo: f64, q10: f64, floor: f64) -> f64 {
    if q10 <= 0.0 {
        return 1.0;
    }
    q10.powf((t - lo) / 10.0).clamp(floor, 1.0)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn the_longest_spell_wraps_the_year() {
        // Lean in months 10, 11, 0 and 1, and in 5 alone.
        let lean = 1 << 10 | 1 << 11 | 1 | 1 << 1 | 1 << 5;
        assert_eq!(longest_spell(lean), (10, 4));
        assert_eq!(longest_spell(1 << 3), (3, 1));
    }

    #[test]
    fn a_cold_body_keeps_a_share_of_its_clock() {
        assert_eq!(warmth(20.0, 15.0, 2.5, 0.1), 1.0);
        assert_eq!(warmth(15.0, 15.0, 2.5, 0.1), 1.0);
        assert!((warmth(5.0, 15.0, 2.5, 0.1) - 0.4).abs() < 1e-12);
        assert_eq!(warmth(-30.0, 15.0, 2.5, 0.1), 0.1);
        assert_eq!(warmth(-30.0, 15.0, 0.0, 0.1), 1.0);
    }
}
