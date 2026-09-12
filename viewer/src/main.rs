//! Replay: serve a recorded run to the browser, which seeks and plays it at any speed.
//!
//!     cargo run --release -p viewer -- experiments/e041_stock/results/<run>_view.bin [port]

use std::collections::{HashMap, HashSet};
use std::io::Write;
use std::net::TcpStream;
use std::sync::{Arc, OnceLock};
use viewer::http;
use viewer::wire;

const NONE: u32 = u32::MAX; // no parent, or never in a frame

struct Frame {
    step: u64,
    at: usize, // offset of the record in the file
    end: usize,
    key: bool, // carries the cell layers: a seek starts from one
}

struct Replay {
    data: Vec<u8>,
    frames: Vec<Frame>,
    bodies: Vec<u8>, // every shape record, back to back
    header: String,
    cells: usize,
    deaths: bool, // whether the frames carry what a body died of
    births: bool, // whether they carry who a body came from
    ancestry: OnceLock<Ancestry>,
}

/// Who came from whom, over the whole recording. The frames hold every birth, including the
/// bodies that lived and died between two of them, so a line of descent can be walked back from
/// a body alive at the end to the first of its line. Built once, when a watcher first asks.
struct Ancestry {
    /// Per body: its parent, the first frame it is in, and the last (NONE for none, or never).
    of: HashMap<u32, (u32, u32, u32)>,
    /// The bodies in the last frame, with the lineage each belongs to.
    end: Vec<(u32, u32)>,
}

impl Replay {
    fn load(path: &str) -> Replay {
        let data = std::fs::read(path).unwrap_or_else(|e| panic!("{path}: {e}"));
        let (mut frames, mut bodies, mut header, mut n_bodies) = (Vec::new(), Vec::new(), String::new(), 0);
        let mut i = 0;
        while i + 5 <= data.len() {
            let kind = data[i];
            let len = u32::from_le_bytes(data[i + 1..i + 5].try_into().unwrap()) as usize;
            let (at, end) = (i, i + 5 + len);
            if end > data.len() {
                eprintln!("viewer: the recording ends inside a record, {} bytes in", i);
                break;
            }
            let payload = &data[i + 5..end];
            match kind {
                wire::KIND_HEADER => header = String::from_utf8_lossy(payload).to_string(),
                wire::KIND_BODY => {
                    bodies.extend_from_slice(&data[at..end]);
                    n_bodies += 1;
                }
                wire::KIND_FRAME => frames.push(Frame { step: wire::frame_step(payload), at, end, key: wire::frame_has_layers(payload) }),
                _ => {}
            }
            i = end;
        }
        assert!(!frames.is_empty(), "{path}: no frames");
        let n = frames.len();
        let header = format!(
            "{},\"replay\":{{\"first\":{},\"last\":{},\"frames\":{n},\"bodies\":{n_bodies}}}}}",
            header.trim_end().trim_end_matches('}'),
            frames[0].step,
            frames[n - 1].step,
        );
        eprintln!("viewer: {n} frames, steps {}-{}, {} shapes, {:.1} MB", frames[0].step, frames[n - 1].step, n_bodies, data.len() as f64 / 1e6);
        let cells = num_field(&header, "w") * num_field(&header, "h");
        let deaths = !header.contains("\"deaths\":[]");
        let births = header.contains("\"births\":true");
        Replay { data, frames, bodies, header, cells, deaths, births, ancestry: OnceLock::new() }
    }

    /// One pass over every frame: who each body came from, and the frames it is in.
    fn ancestry(&self) -> &Ancestry {
        self.ancestry.get_or_init(|| {
            let t = std::time::Instant::now();
            let mut of: HashMap<u32, (u32, u32, u32)> = HashMap::new();
            let mut end = Vec::new();
            for (k, f) in self.frames.iter().enumerate() {
                let parts = wire::frame_parts(&self.data[f.at + 5..f.end], self.cells, self.deaths, self.births);
                let step = parts.step as u32;
                let last = k + 1 == self.frames.len();
                for i in 0..parts.n_agents {
                    let r = &parts.agents[i * wire::AGENT_BYTES..];
                    let id = u32::from_le_bytes(r[0..4].try_into().unwrap());
                    let e = of.entry(id).or_insert((NONE, NONE, NONE));
                    if e.1 == NONE {
                        e.1 = step;
                    }
                    e.2 = step;
                    if last {
                        end.push((id, u32::from_le_bytes(r[4..8].try_into().unwrap())));
                    }
                }
                for i in 0..parts.n_born {
                    let r = &parts.born[i * 8..];
                    let child = u32::from_le_bytes(r[0..4].try_into().unwrap());
                    let parent = u32::from_le_bytes(r[4..8].try_into().unwrap());
                    of.entry(child).or_insert((NONE, NONE, NONE)).0 = parent;
                }
            }
            eprintln!("viewer: {} bodies indexed, {} alive at the end, {:.1}s", of.len(), end.len(), t.elapsed().as_secs_f32());
            Ancestry { of, end }
        })
    }

    /// A few lines of descent that reach the end of the recording, as JSON: a body alive in the
    /// last frame walked back to the first of its line, so that following it forward from the
    /// start always goes to the child that leads to the end.
    ///
    /// The lines are taken one at a time: the longest first, then the one that shares the least
    /// with the lines already taken. Every body at the end descends from one of a handful of
    /// bodies the world started with, so lines chosen any other way are the same line for most
    /// of their length (the lineage a body belongs to is a group detected again at every log,
    /// not a family, so it does not separate them either).
    ///
    /// The bodies that never made it into a frame are left out of the path - the camera has
    /// nowhere to go for them - but they are counted in `births`.
    fn lines(&self, want: usize) -> String {
        if !self.births {
            return "[]".to_string();
        }
        let a = self.ancestry();
        let mut depth: HashMap<u32, u32> = HashMap::new();
        let mut rest: Vec<(u32, u32, u32)> = a.end.iter().map(|&(id, lineage)| (walk_back(id, &a.of, &mut depth), id, lineage)).collect();
        rest.sort_by(|x, y| y.0.cmp(&x.0));
        let mut taken: Vec<(u32, u32, u32, usize)> = Vec::new(); // depth, body, lineage, bodies of its own
        let mut on_a_line: HashSet<u32> = HashSet::new();
        while taken.len() < want && !rest.is_empty() {
            // How much of a line is not on one already taken. `rest` is deepest first, so the
            // longest wins where two add as much.
            let adds = |id: u32| chain(id, &a.of).iter().filter(|c| !on_a_line.contains(c)).count();
            let (i, fresh) = rest.iter().enumerate().map(|(i, &(_, id, _))| (i, adds(id))).max_by_key(|&(i, fresh)| (fresh, std::cmp::Reverse(i))).unwrap();
            if fresh == 0 {
                break;
            }
            let (d, id, lineage) = rest.remove(i);
            on_a_line.extend(chain(id, &a.of));
            taken.push((d, id, lineage, fresh));
        }
        let mut out = String::from("[");
        for (i, &(d, id, lineage, fresh)) in taken.iter().enumerate() {
            // Only the bodies a frame caught can be followed; the rest lived and died between two.
            let seen: Vec<u32> = chain(id, &a.of).into_iter().filter(|c| a.of[c].1 != NONE).collect();
            let path: Vec<String> = seen.iter().map(|c| format!("[{c},{},{}]", a.of[c].1, a.of[c].2)).collect();
            let from = seen.first().map_or(0, |c| a.of[c].1);
            let to = seen.last().map_or(0, |c| a.of[c].2);
            if i > 0 {
                out.push(',');
            }
            out.push_str(&format!(
                "{{\"body\":{id},\"lineage\":{lineage},\"births\":{d},\"seen\":{},\"own\":{fresh},\"from\":{from},\"to\":{to},\"path\":[{}]}}",
                seen.len(),
                path.join(",")
            ));
        }
        out.push(']');
        out
    }

    /// The frames from `from` on: the last keyframe at or before it, then everything through
    /// `count` frames past it. The browser plays from `from` and keeps the layers of the
    /// keyframe.
    fn slice(&self, from: u64, count: usize) -> &[u8] {
        let i = self.frames.partition_point(|f| f.step < from).min(self.frames.len() - 1);
        let k = self.frames[..=i].iter().rposition(|f| f.key).unwrap_or(0);
        let j = (i + count).min(self.frames.len() - 1);
        &self.data[self.frames[k].at..self.frames[j].end]
    }
}

/// A body's line, from the first of it to the body itself.
fn chain(id: u32, of: &HashMap<u32, (u32, u32, u32)>) -> Vec<u32> {
    let mut chain = vec![id];
    let mut cur = id;
    while let Some(&(p, _, _)) = of.get(&cur) {
        if p == NONE || p == cur {
            break;
        }
        chain.push(p);
        cur = p;
    }
    chain.reverse();
    chain
}

/// How many births back the first of this body's line is (0: it is the first).
fn walk_back(id: u32, of: &HashMap<u32, (u32, u32, u32)>, depth: &mut HashMap<u32, u32>) -> u32 {
    let mut chain = Vec::new();
    let mut cur = id;
    let mut d = loop {
        if let Some(&d) = depth.get(&cur) {
            break d;
        }
        match of.get(&cur) {
            Some(&(p, _, _)) if p != NONE && p != cur => {
                chain.push(cur);
                cur = p;
            }
            _ => {
                depth.insert(cur, 0);
                break 0;
            }
        }
    };
    for &c in chain.iter().rev() {
        d += 1;
        depth.insert(c, d);
    }
    d
}

/// A number written in the header's JSON (the few the replay itself reads).
fn num_field(header: &str, key: &str) -> usize {
    let pat = format!("\"{key}\":");
    let at = header.find(&pat).map(|i| i + pat.len()).unwrap_or(0);
    header[at..].chars().take_while(|c| c.is_ascii_digit()).collect::<String>().parse().unwrap_or(0)
}

fn handle(r: &Arc<Replay>, mut s: TcpStream) {
    let Some(req) = http::read_request(&mut s) else { return };
    let _ = match req.path.as_str() {
        "/world.json" => http::send(&mut s, "200 OK", "application/json", r.header.as_bytes()),
        "/state" => http::send(&mut s, "200 OK", "application/json", b"{\"live\":false}"),
        "/bodies" => http::send(&mut s, "200 OK", "application/octet-stream", &r.bodies),
        // The longest lines of descent in the recording: the index is built the first time.
        "/lines" => {
            let want = req.num::<usize>("n").unwrap_or(6).clamp(1, 40);
            http::send(&mut s, "200 OK", "application/json", r.lines(want).as_bytes())
        }
        "/frames" => {
            let from = req.num::<u64>("from").unwrap_or(0);
            let count = req.num::<usize>("count").unwrap_or(120).clamp(1, 4000);
            http::send(&mut s, "200 OK", "application/octet-stream", r.slice(from, count))
        }
        p => {
            let web = http::web_dir();
            match http::serve_file(&mut s, &web, p) {
                Ok(true) => Ok(()),
                _ => http::not_found(&mut s),
            }
        }
    };
    let _ = s.flush();
}

fn main() {
    let args: Vec<String> = std::env::args().collect();
    let path = args.get(1).unwrap_or_else(|| {
        eprintln!("usage: viewer <run>_view.bin [port]");
        std::process::exit(2);
    });
    let port: u16 = args.get(2).and_then(|p| p.parse().ok()).unwrap_or(7777);
    let r = Arc::new(Replay::load(path));
    let listener = std::net::TcpListener::bind(("127.0.0.1", port)).unwrap_or_else(|e| panic!("port {port}: {e}"));
    http::warn_if_stale(&http::web_dir());
    println!("viewer: watch at http://127.0.0.1:{port}/");
    for s in listener.incoming().flatten() {
        let r = r.clone();
        std::thread::spawn(move || {
            let _ = s.set_nodelay(true);
            handle(&r, s)
        });
    }
}
