//! e098 (#110): what 3D costs, a spike. Not an experiment - no law, no batch, nothing kept.
//!
//! The question is the clock: stage C runs at about 28 ms a step with 10,000 bodies, and a 3D body
//! grid touches every hot loop. This crate runs the loops that 3D touches, and nothing else, in two
//! geometries at the control's crowd:
//!
//! - `2d`: today's, a grid of side 4-16 in a world cell of 4x4 sub-cells with three layers;
//! - `3d`: a grid of side 4-8 in all three axes, in a world cell of 4x4x4 sub-cells, 6 faces a block.
//!
//! What the arms do a step is driven at the rates e097's control log measured, so both do the same
//! work and only the geometry differs: 0.65 turns a body, 0.0122 children a body (0.0054 of them a
//! development the gene-list cache cannot answer), one body out for one child placed.
//!
//! Left out on purpose: the climate and the producers (2.6 ms of the 28, and 3D does not touch
//! them), the lineages (0.8-2.2 ms, a fact about gene lists), the matter ledger, the censuses.

mod genome;
mod three;
mod two;

use std::time::Instant;

#[derive(Clone)]
pub struct Cfg {
    pub side: usize,    // the world's cells per axis
    pub height: usize,  // the world's cells up (3D only)
    pub sz: usize,      // the cells a body's grid may hold up (3D only)
    pub bodies: usize,
    pub steps: usize,
    pub warm: usize,
    pub seed: u64,
    pub fill: f32,      // the share of an occupied cell's sub-cells bodies hold (e097: 8.5-10.5 of 16)
    pub children: f64,  // children tried a body a step
    pub develops: f64,  // of them, developments the cache cannot answer
    pub off: String,    // a part left out, to price it by what its absence saves
}

#[derive(Default, Clone)]
pub struct Stats {
    pub pop: usize,
    pub blocks: f64,
    pub side: f64,
    pub fill: f64,
    pub ground: usize,
    pub occ_bytes: usize,
    pub agent_bytes: usize,
    pub steps: u64,
    pub turns: u64,
    pub moved: u64,
    pub blocked: u64,
    pub contacts: u64,
    pub broken: u64,
    pub worn: u64,
    pub births: u64,
    pub no_room: u64,
    pub develops: u64,
    pub mates: u64,
    pub acted: u64,
}

fn main() {
    let mut cfg = Cfg {
        side: 512,
        height: 4,
        sz: 8,
        bodies: 10_000,
        steps: 200,
        warm: 20,
        seed: 1,
        fill: 0.56,
        children: 0.01217, // 132.9 children a step at 10,917 bodies (e097's control)
        develops: 0.00545, // 59.5 developments a step at 10,917 bodies
        off: String::new(),
    };
    let mut arm = String::from("2d");
    for a in std::env::args().skip(1) {
        let (k, v) = a.split_once('=').unwrap_or(("arm", a.as_str()));
        match k {
            "arm" => arm = v.to_string(),
            "side" => cfg.side = v.parse().unwrap(),
            "height" => cfg.height = v.parse().unwrap(),
            "sz" => cfg.sz = v.parse().unwrap(),
            "bodies" => cfg.bodies = v.parse().unwrap(),
            "steps" => cfg.steps = v.parse().unwrap(),
            "warm" => cfg.warm = v.parse().unwrap(),
            "seed" => cfg.seed = v.parse().unwrap(),
            "fill" => cfg.fill = v.parse().unwrap(),
            "children" => cfg.children = v.parse().unwrap(),
            "develops" => cfg.develops = v.parse().unwrap(),
            "off" => cfg.off = v.to_string(),
            _ => panic!("unknown argument {k}"),
        }
    }
    // `bench=develop`: what one development costs, on its own, from `steps` random genomes.
    if cfg.off == "develop_only" {
        let mut rng = genome::Rng(cfg.seed.wrapping_mul(0x9E3779B97F4A7C15) | 1);
        let mut n = 0usize;
        let mut cells = 0usize;
        let genomes: Vec<Vec<u8>> = (0..cfg.steps).map(|_| genome::random_genome(&mut rng)).collect();
        let (two_laws, three_laws) = (two::Laws::new(cfg.seed), three::Laws::new(cfg.seed));
        let t = Instant::now();
        for g in &genomes {
            let genes = genome::parse_genes(g);
            if genes.is_empty() {
                continue;
            }
            n += 1;
            if arm == "2d" {
                let b = two::develop_genes(&genes, &two_laws);
                cells += b.s() * b.s();
            } else {
                let b = three::develop_genes(&genes, &three_laws, cfg.sz);
                cells += b.s() * b.s() * b.sz();
            }
        }
        let us = t.elapsed().as_secs_f64() * 1e6 / n as f64;
        println!("arm={arm} off=develop_only n={n} us_develop={us:.1} cells={:.1}", cells as f64 / n as f64);
        return;
    }
    let built = Instant::now();
    let (k, ms, ms_build) = match arm.as_str() {
        "2d" => {
            let mut w = two::World::new(&cfg);
            let build = built.elapsed().as_secs_f64();
            for _ in 0..cfg.warm {
                w.step();
            }
            w.k = Stats::default();
            let t = Instant::now();
            for _ in 0..cfg.steps {
                w.step();
            }
            let ms = t.elapsed().as_secs_f64() * 1000.0 / cfg.steps as f64;
            (w.stats(), ms, build)
        }
        "3d" => {
            let mut w = three::World::new(&cfg);
            let build = built.elapsed().as_secs_f64();
            for _ in 0..cfg.warm {
                w.step();
            }
            w.k = Stats::default();
            let t = Instant::now();
            for _ in 0..cfg.steps {
                w.step();
            }
            let ms = t.elapsed().as_secs_f64() * 1000.0 / cfg.steps as f64;
            (w.stats(), ms, build)
        }
        _ => panic!("arm is 2d or 3d"),
    };
    let per = |n: u64| n as f64 / cfg.steps as f64;
    println!(
        "arm={arm} off={off} bodies={pop} sz={sz} height={height} ms_step={ms:.3} us_body={us:.3} \
         blocks={blocks:.1} side={side:.2} fill={fill:.3} ground={ground} occ_mb={occ:.1} agent_b={ab} \
         turns={turns:.0} moved={moved:.0} blocked={blocked:.0} contacts={contacts:.0} broken={broken:.1} worn={worn:.2} \
         births={births:.1} no_room={no_room:.1} develops={develops:.1} mates={mates:.1} build_s={build:.1}",
        off = if cfg.off.is_empty() { "-" } else { &cfg.off },
        pop = k.pop,
        sz = cfg.sz,
        height = cfg.height,
        us = ms * 1000.0 / k.pop.max(1) as f64,
        blocks = k.blocks,
        side = k.side,
        fill = k.fill,
        ground = k.ground,
        occ = k.occ_bytes as f64 / 1e6,
        ab = k.agent_bytes / k.pop.max(1),
        turns = per(k.turns),
        moved = per(k.moved),
        blocked = per(k.blocked),
        contacts = per(k.contacts),
        broken = per(k.broken),
        worn = per(k.worn),
        births = per(k.births),
        no_room = per(k.no_room),
        develops = per(k.develops),
        mates = per(k.mates),
        build = ms_build,
    );
}
