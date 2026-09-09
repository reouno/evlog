//! Watching the world: the world writes frames, the browser draws them.
//!
//! An experiment adds three lines (`View::from_env`, `view.frame(..)`, `view.tick(step)`) and
//! nothing else changes: with EVLOG_VIEW unset the viewer does not exist and the run is what it
//! was. What the frames are is in `wire.rs`, and it is the whole interface.
//!
//! EVLOG_VIEW:
//!   rec                          record the whole run to <prefix>_view.bin
//!   rec:from=300000,len=2000     record a window of it
//!   rec:...,stride=2,layers=30   every 2nd step, the cell layers every 30th frame
//!   serve                        run as a server on 127.0.0.1:7777 and pace the world to the
//!                                speed the browser asks for
//!   serve:port=7777,speed=20,from=100000
//!                                (from: run at full speed until that step, then watch)

pub mod http;
pub mod live;
pub mod wire;

pub use wire::{AgentIn, Init, LayerSpec, Scale};

use std::collections::HashMap;
use std::io::Write;
use std::sync::Arc;
use std::time::{Duration, Instant};

pub struct View {
    layers: Vec<LayerSpec>,
    from: u64,
    until: u64,
    stride: u64,
    layer_stride: u64,
    bodies: wire::Bodies,
    buf: Vec<u8>,
    keyed: bool, // whether a frame with the cell layers has gone out yet
    out: Out,
}

enum Out {
    File(std::io::BufWriter<std::fs::File>),
    Live(Arc<live::Live>, Instant),
}

fn opts(s: &str) -> HashMap<&str, &str> {
    s.split(',').filter_map(|p| p.split_once('=')).collect()
}

impl View {
    /// The viewer asked for by EVLOG_VIEW, or None. `prefix` is the run's results prefix.
    pub fn from_env(prefix: &str, init: Init) -> Option<View> {
        let spec = std::env::var("EVLOG_VIEW").ok()?;
        let spec = spec.trim();
        if spec.is_empty() {
            return None;
        }
        let (kind, rest) = spec.split_once(':').unwrap_or((spec, ""));
        let o = opts(rest);
        let num = |k: &str, d: u64| o.get(k).and_then(|v| v.parse().ok()).unwrap_or(d);
        let from = num("from", 0);
        let stride = num("stride", 1).max(1);
        let layer_stride = num("layers", 30).max(1);
        let live_mode = kind == "serve";
        let until = match o.get("len") {
            Some(v) => from + v.parse::<u64>().unwrap_or(0),
            None => u64::MAX,
        };
        let json = wire::header_json(&init, stride, layer_stride, live_mode);
        let header = wire::record(wire::KIND_HEADER, json.as_bytes());
        let out = match kind {
            "rec" => {
                let path = format!("{prefix}_view.bin");
                let mut f = std::io::BufWriter::new(std::fs::File::create(&path).unwrap());
                f.write_all(&header).unwrap();
                eprintln!("viewer: recording to {path}");
                Out::File(f)
            }
            "serve" => {
                let port = num("port", 7777) as u16;
                let speed = o.get("speed").and_then(|v| v.parse().ok()).unwrap_or(20.0);
                let l = live::Live::start(port, json, header, speed, from);
                eprintln!("viewer: watch at http://127.0.0.1:{port}/");
                Out::Live(l, Instant::now())
            }
            other => panic!("EVLOG_VIEW: unknown mode {other:?} (rec or serve)"),
        };
        Some(View { layers: init.layers, from, until, stride, layer_stride, bodies: wire::Bodies::default(), buf: Vec::new(), keyed: false, out })
    }

    /// Whether this step is a frame. The caller skips the work of a frame when it is not.
    pub fn wants(&self, step: u64) -> bool {
        step >= self.from && step <= self.until && (step - self.from) % self.stride == 0
    }

    /// A frame carries the cell layers every `layer_stride` frames, and the first one always
    /// does: a watcher that joins at any point is given a whole world before it is moved.
    fn is_key(&self, step: u64) -> bool {
        !self.keyed || (step - self.from) % (self.stride * self.layer_stride) == 0
    }

    /// One frame: the cell layers in the order of the header, the globals in its order, and
    /// every living body through `fill`.
    pub fn frame<F>(&mut self, step: u64, layers: &[&[f64]], globals: &[f32], mut fill: F)
    where
        F: FnMut(&mut dyn FnMut(AgentIn)),
    {
        let key = self.is_key(step);
        self.keyed |= key;
        let View { layers: specs, bodies, buf, out, .. } = self;
        let mut new_bodies: Vec<Vec<u8>> = Vec::new();
        let rec = {
            let fw = wire::FrameWriter::start(buf, step, globals);
            let fw = if key { fw.layers(specs, layers) } else { fw.no_layers() };
            let mut fw = fw.agents_start();
            fill(&mut |a: AgentIn| {
                let (id, rec) = bodies.id(a.side, a.cells);
                if let Some(r) = rec {
                    new_bodies.push(r.to_vec());
                }
                fw.agent(&a, id);
            });
            fw.finish()
        };
        match out {
            Out::File(f) => {
                for b in &new_bodies {
                    f.write_all(b).unwrap();
                }
                f.write_all(&rec).unwrap();
            }
            Out::Live(l, _) => {
                for b in new_bodies {
                    l.push_body(Arc::new(b));
                }
                l.push_frame(Arc::new(rec), key);
            }
        }
    }

    /// Live: hold the world back to the speed the browser asks for (nothing when recording).
    /// Called every step, whether or not the step is a frame.
    pub fn tick(&mut self, step: u64) {
        let Out::Live(l, next) = &mut self.out else { return };
        let dt = loop {
            let mut c = l.control.lock().unwrap();
            if step < c.fast_until {
                return;
            }
            if c.paused {
                if c.once {
                    c.once = false;
                    return;
                }
                drop(c);
                std::thread::sleep(Duration::from_millis(20));
                continue;
            }
            break Duration::from_secs_f32(1.0 / c.speed.max(0.05));
        };
        let now = Instant::now();
        if now < *next {
            std::thread::sleep(*next - now);
        }
        *next = Instant::now() + dt;
    }

    /// Live: whether anybody is watching (the world can stop when the last one leaves).
    pub fn watchers(&self) -> usize {
        match &self.out {
            Out::Live(l, _) => l.watchers(),
            Out::File(_) => 0,
        }
    }
}

impl Drop for View {
    fn drop(&mut self) {
        if let Out::File(f) = &mut self.out {
            let _ = f.flush();
        }
    }
}
