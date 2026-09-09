//! Replay: serve a recorded run to the browser, which seeks and plays it at any speed.
//!
//!     cargo run --release -p viewer -- experiments/e041_stock/results/<run>_view.bin [port]

use std::io::Write;
use std::net::TcpStream;
use std::sync::Arc;
use viewer::http;
use viewer::wire;

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
        Replay { data, frames, bodies, header }
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

fn handle(r: &Arc<Replay>, mut s: TcpStream) {
    let Some(req) = http::read_request(&mut s) else { return };
    let _ = match req.path.as_str() {
        "/world.json" => http::send(&mut s, "200 OK", "application/json", r.header.as_bytes()),
        "/state" => http::send(&mut s, "200 OK", "application/json", b"{\"live\":false}"),
        "/bodies" => http::send(&mut s, "200 OK", "application/octet-stream", &r.bodies),
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
    println!("viewer: watch at http://127.0.0.1:{port}/");
    for s in listener.incoming().flatten() {
        let r = r.clone();
        std::thread::spawn(move || {
            let _ = s.set_nodelay(true);
            handle(&r, s)
        });
    }
}
