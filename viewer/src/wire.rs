//! The interface between the world (any experiment) and the viewer.
//!
//! One stream of records, the same for a live run and for a replay of a recorded one:
//!
//! ```text
//!     [u8 kind][u32 length][payload]
//! ```
//!
//! kind 0  header, a JSON object (once, first)
//! kind 1  a body shape: [u32 id][u8 side][u8; side*side] block kinds, row by row
//! kind 2  a frame (below)
//!
//! A frame:
//!
//! ```text
//!     [u64 step]
//!     [u8 n_globals][f32 x n_globals]
//!     [u8 n_layers][(u8 layer index, u8 value per cell) x n_layers]   // only on layer steps
//!     [u32 n_agents][agent record x n_agents]
//!     [u32 n_dead][(u32 id, u8 cause) x n_dead]                        // when the header names causes
//! ```
//!
//! The header says what the layers, the globals and the agent record are, so a world that
//! grows a new layer or a new field says so there and the viewer follows without a new format.
//! The dead are the bodies that died since the frame before, with what they died of (the
//! header's `deaths` names the causes by number): a watcher following one sees why it is gone.
//! Cell layers change slowly (a plant grows by 0.01 a step) and are written every
//! `layer_stride` frames; the bodies move every step.

use std::collections::HashMap;

/// How a cell layer's value is packed into a byte. `max` is the value that reaches 255.
#[derive(Clone, Copy, PartialEq)]
pub enum Scale {
    Linear,
    Sqrt, // a wide range where the small values matter (the plant: a lawn is 0.05, a tree is 8)
    Log,  // a value with no cap (the soil under a crowd)
}

impl Scale {
    fn name(self) -> &'static str {
        match self {
            Scale::Linear => "linear",
            Scale::Sqrt => "sqrt",
            Scale::Log => "log",
        }
    }
    pub fn pack(self, v: f64, max: f32) -> u8 {
        let max = max as f64;
        let q = match self {
            Scale::Linear => v / max,
            Scale::Sqrt => (v / max).max(0.0).sqrt(),
            Scale::Log => (1.0 + v.max(0.0)).ln() / (1.0 + max).ln(),
        };
        (q.clamp(0.0, 1.0) * 255.0).round() as u8
    }
}

/// One per-cell layer of the world: a name the viewer knows how to draw ("plant", "water", ...).
pub struct LayerSpec {
    pub name: &'static str,
    pub max: f32,
    pub scale: Scale,
}

impl LayerSpec {
    pub fn new(name: &'static str, max: f32, scale: Scale) -> Self {
        LayerSpec { name, max, scale }
    }
}

/// What the world is, written once at the start.
pub struct Init<'a> {
    pub experiment: &'a str,
    pub w: usize,
    pub h: usize,
    pub sub: usize, // sub-cells per cell along one side: a body cell is 1/sub of a world cell
    pub height: &'a [f32],
    pub band: &'a [u8],
    pub layers: Vec<LayerSpec>,
    pub globals: Vec<&'static str>,
    pub blocks: Vec<&'static str>, // block kinds by index, 0 = empty
    pub deaths: Vec<&'static str>, // what a body dies of, by the number `View::died` is given (empty: none are sent)
    pub params: String,            // the run's laws and arguments, a JSON object
}

/// One body in one frame. `cells` is the body's own frame (row by row, side*side); `facing`
/// is the world direction its front points to, and the viewer turns it.
pub struct AgentIn<'a> {
    pub id: u32,
    pub lineage: u32,
    pub x: u16, // sub-cell of the north-west corner of the body's grid
    pub y: u16,
    pub facing: u8,
    pub diet: u8, // 0 plants, 1 mixed, 2 meat, 3 nothing yet
    pub fill: f32,
    pub energy: f32,
    pub ripe: f32, // the energy at which the body breeds
    pub fat: f32,  // its store, as a share of what its flesh can hold
    pub age: u32,
    pub born: u16, // blocks at birth (what it holds now is its shape's)
    pub side: u8,
    pub cells: &'a [u8],
}

pub const AGENT_BYTES: usize = 26;
pub const ENERGY_MAX: f32 = 16.0; // a big body breeds at 14

pub const KIND_HEADER: u8 = 0;
pub const KIND_BODY: u8 = 1;
pub const KIND_FRAME: u8 = 2;

pub fn record(kind: u8, payload: &[u8]) -> Vec<u8> {
    let mut out = Vec::with_capacity(payload.len() + 5);
    out.push(kind);
    out.extend_from_slice(&(payload.len() as u32).to_le_bytes());
    out.extend_from_slice(payload);
    out
}

fn floats(v: &[f32]) -> String {
    v.iter().map(|x| format!("{x:.2}")).collect::<Vec<_>>().join(",")
}

fn strings(v: &[&str]) -> String {
    v.iter().map(|s| format!("\"{s}\"")).collect::<Vec<_>>().join(",")
}

/// The header record's JSON. `extra` is added to the object (replay adds the seek index).
pub fn header_json(init: &Init, stride: u64, layer_stride: u64, live: bool) -> String {
    let layers = init
        .layers
        .iter()
        .map(|l| format!("{{\"name\":\"{}\",\"max\":{},\"scale\":\"{}\"}}", l.name, l.max, l.scale.name()))
        .collect::<Vec<_>>()
        .join(",");
    // The agent record, field by field, so that a world that adds a field only adds a line here.
    let agent = "[{\"name\":\"id\",\"type\":\"u32\"},{\"name\":\"lineage\",\"type\":\"u32\"},{\"name\":\"body\",\"type\":\"u32\"},\
                 {\"name\":\"x\",\"type\":\"u16\"},{\"name\":\"y\",\"type\":\"u16\"},{\"name\":\"facing\",\"type\":\"u8\"},\
                 {\"name\":\"diet\",\"type\":\"u8\"},{\"name\":\"fill\",\"type\":\"u8\",\"max\":1},\
                 {\"name\":\"energy\",\"type\":\"u8\",\"max\":16},{\"name\":\"ripe\",\"type\":\"u8\",\"max\":16},\
                 {\"name\":\"fat\",\"type\":\"u8\",\"max\":1},{\"name\":\"age\",\"type\":\"u16\"},{\"name\":\"born\",\"type\":\"u16\"}]";
    let bands = init.band.iter().map(|b| b.to_string()).collect::<Vec<_>>().join(",");
    format!(
        "{{\"version\":1,\"experiment\":\"{}\",\"live\":{live},\"w\":{},\"h\":{},\"sub\":{},\"stride\":{stride},\"layer_stride\":{layer_stride},\
         \"layers\":[{layers}],\"globals\":[{}],\"blocks\":[{}],\"deaths\":[{}],\"agent_record\":{agent},\"params\":{},\"height\":[{}],\"band\":[{bands}]}}",
        init.experiment,
        init.w,
        init.h,
        init.sub,
        strings(&init.globals),
        strings(&init.blocks),
        strings(&init.deaths),
        init.params,
        floats(init.height),
    )
}

/// Body shapes seen so far: the shape is sent once and the frames name it by id.
#[derive(Default)]
pub struct Bodies {
    ids: HashMap<u64, u32>,
    pub records: Vec<Vec<u8>>,
}

impl Bodies {
    /// The id of this shape, and its record when it is new.
    pub fn id(&mut self, side: u8, cells: &[u8]) -> (u32, Option<&[u8]>) {
        let mut hash: u64 = 0xcbf29ce484222325;
        for &b in std::iter::once(&side).chain(cells) {
            hash = (hash ^ b as u64).wrapping_mul(0x100000001b3);
        }
        if let Some(&id) = self.ids.get(&hash) {
            return (id, None);
        }
        let id = self.records.len() as u32;
        self.ids.insert(hash, id);
        let mut p = Vec::with_capacity(cells.len() + 5);
        p.extend_from_slice(&id.to_le_bytes());
        p.push(side);
        p.extend_from_slice(cells);
        self.records.push(record(KIND_BODY, &p));
        (id, Some(self.records.last().unwrap()))
    }
}

/// Write one frame's payload into `buf`.
pub struct FrameWriter<'a> {
    pub buf: &'a mut Vec<u8>,
    pub n_agents: u32,
    agents_at: usize,
}

impl<'a> FrameWriter<'a> {
    pub fn start(buf: &'a mut Vec<u8>, step: u64, globals: &[f32]) -> Self {
        buf.clear();
        buf.extend_from_slice(&step.to_le_bytes());
        FrameWriter { buf, n_agents: 0, agents_at: 0 }.globals(globals)
    }
    fn globals(self, globals: &[f32]) -> Self {
        self.buf.push(globals.len() as u8);
        for g in globals {
            self.buf.extend_from_slice(&g.to_le_bytes());
        }
        self
    }
    /// The layers, packed by their spec. Called before `agents`, or not at all.
    pub fn layers(self, specs: &[LayerSpec], values: &[&[f64]]) -> Self {
        let n = specs.len().min(values.len());
        self.buf.push(n as u8);
        for (i, (spec, vals)) in specs.iter().zip(values).enumerate().take(n) {
            self.buf.push(i as u8);
            self.buf.extend(vals.iter().map(|&v| spec.scale.pack(v, spec.max)));
        }
        self
    }
    pub fn no_layers(self) -> Self {
        self.buf.push(0);
        self
    }
    pub fn agents_start(mut self) -> Self {
        self.agents_at = self.buf.len();
        self.buf.extend_from_slice(&0u32.to_le_bytes());
        self
    }
    pub fn agent(&mut self, a: &AgentIn, body: u32) {
        let b = &mut *self.buf;
        b.extend_from_slice(&a.id.to_le_bytes());
        b.extend_from_slice(&a.lineage.to_le_bytes());
        b.extend_from_slice(&body.to_le_bytes());
        b.extend_from_slice(&a.x.to_le_bytes());
        b.extend_from_slice(&a.y.to_le_bytes());
        b.push(a.facing);
        b.push(a.diet);
        b.push((a.fill.clamp(0.0, 1.0) * 255.0) as u8);
        b.push(((a.energy / ENERGY_MAX).clamp(0.0, 1.0) * 255.0) as u8);
        b.push(((a.ripe / ENERGY_MAX).clamp(0.0, 1.0) * 255.0) as u8);
        b.push((a.fat.clamp(0.0, 1.0) * 255.0) as u8);
        b.extend_from_slice(&(a.age.min(u16::MAX as u32) as u16).to_le_bytes());
        b.extend_from_slice(&a.born.to_le_bytes());
        self.n_agents += 1;
    }
    /// The bodies that died since the frame before, after the living ones.
    pub fn deaths(self, dead: &[(u32, u8)]) -> Self {
        self.buf.extend_from_slice(&(dead.len() as u32).to_le_bytes());
        for &(id, cause) in dead {
            self.buf.extend_from_slice(&id.to_le_bytes());
            self.buf.push(cause);
        }
        self
    }
    pub fn finish(self) -> Vec<u8> {
        let at = self.agents_at;
        self.buf[at..at + 4].copy_from_slice(&self.n_agents.to_le_bytes());
        record(KIND_FRAME, self.buf)
    }
}

/// The step of a frame record, for the replay index.
pub fn frame_step(payload: &[u8]) -> u64 {
    u64::from_le_bytes(payload[..8].try_into().unwrap())
}

/// Whether a frame record carries the cell layers (a keyframe: a seek starts from one).
pub fn frame_has_layers(payload: &[u8]) -> bool {
    let n_globals = payload[8] as usize;
    payload[9 + n_globals * 4] > 0
}

/// The header is written here by hand and read in the browser by hand, so these two tests hold
/// the two together: what `header_json` says a world is must be what `web/src/wire.ts` declares
/// it is. A field renamed on one side and not the other is then a failing build rather than a
/// layer that silently stops being drawn.
#[cfg(test)]
mod tests {
    use super::*;

    fn browser_wire() -> String {
        let path = concat!(env!("CARGO_MANIFEST_DIR"), "/web/src/wire.ts");
        std::fs::read_to_string(path).unwrap_or_else(|e| panic!("{path}: {e}"))
    }

    fn sample_header() -> String {
        let init = Init {
            experiment: "test",
            w: 2,
            h: 2,
            sub: 2,
            height: &[0.0; 4],
            band: &[0; 4],
            layers: vec![LayerSpec::new("plant", 8.0, Scale::Sqrt)],
            globals: vec!["sun"],
            blocks: vec!["empty", "hard"],
            deaths: vec!["hunger"],
            params: "{\"weather\":\"season\"}".to_string(),
        };
        header_json(&init, 1, 30, false)
    }

    /// The keys of a JSON object, the top level of it only.
    fn json_keys(s: &str) -> Vec<String> {
        let b = s.as_bytes();
        let (mut keys, mut depth, mut i, mut in_str, mut start) = (Vec::new(), 0i32, 0, false, 0);
        while i < b.len() {
            match b[i] {
                b'\\' if in_str => i += 1,
                b'"' if !in_str => {
                    in_str = true;
                    start = i + 1;
                }
                b'"' => {
                    in_str = false;
                    let rest = s[i + 1..].trim_start();
                    if depth == 1 && rest.starts_with(':') {
                        keys.push(s[start..i].to_string());
                    }
                }
                b'{' | b'[' if !in_str => depth += 1,
                b'}' | b']' if !in_str => depth -= 1,
                _ => {}
            }
            i += 1;
        }
        keys
    }

    /// The fields an `export interface` declares: all of them, and the ones it says must be there.
    fn interface_fields(src: &str, name: &str) -> (Vec<String>, Vec<String>) {
        let head = format!("export interface {name} {{");
        let at = src.find(&head).unwrap_or_else(|| panic!("wire.ts has no `{head}`"));
        let body = &src[at + head.len()..];
        let body = &body[..body.find("\n}").expect("the interface is not closed")];
        let (mut all, mut required) = (Vec::new(), Vec::new());
        for line in body.lines() {
            let line = line.trim();
            if line.starts_with('/') || line.starts_with('*') {
                continue;
            }
            let Some((key, _)) = line.split_once(':') else { continue };
            let key = key.trim();
            let name = key.trim_end_matches('?');
            if name.is_empty() || !name.chars().all(|c| c.is_ascii_alphanumeric() || c == '_') {
                continue;
            }
            all.push(name.to_string());
            if !key.ends_with('?') {
                required.push(name.to_string());
            }
        }
        (all, required)
    }

    /// The names in a union of string literals (`export type X = 'a' | 'b';`), in order.
    fn union_members(src: &str, name: &str) -> Vec<String> {
        let head = format!("export type {name} =");
        let at = src.find(&head).unwrap_or_else(|| panic!("wire.ts has no `{head}`"));
        let body = &src[at..];
        let body = &body[..body.find(';').expect("the type is not closed")];
        body.split('\'').skip(1).step_by(2).map(|s| s.to_string()).collect()
    }

    #[test]
    fn header_is_what_the_browser_declares() {
        let json = sample_header();
        let keys = json_keys(&json);
        let src = browser_wire();
        let (all, required) = interface_fields(&src, "Header");
        for k in &keys {
            assert!(all.contains(k), "the header carries `{k}`; web/src/wire.ts's Header does not declare it");
        }
        for k in &required {
            assert!(keys.contains(k), "web/src/wire.ts's Header declares `{k}`; the header does not carry it");
        }
    }

    #[test]
    fn agent_record_is_what_the_browser_declares() {
        let json = sample_header();
        let at = json.find("\"agent_record\":").expect("no agent record");
        let record = &json[at..at + json[at..].find(']').unwrap()];
        let sent: Vec<String> = record
            .split("\"name\":\"")
            .skip(1)
            .map(|p| p[..p.find('"').unwrap()].to_string())
            .collect();
        assert_eq!(sent, union_members(&browser_wire(), "AgentField"), "the agent record and web/src/wire.ts's AgentField differ");
    }
}
