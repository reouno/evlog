//! The live server: the world runs in the main thread and streams its frames to the browser,
//! which tells it how fast to run.

use crate::http;
use std::collections::VecDeque;
use std::net::{TcpListener, TcpStream};
use std::sync::{Arc, Condvar, Mutex};
use std::time::Duration;

pub struct Control {
    pub speed: f32,     // steps per second
    pub paused: bool,
    pub fast_until: u64, // run at full speed until this step (a skip forward)
    pub once: bool,      // let one step through while paused
}

#[derive(Default)]
struct Backlog {
    bodies: Vec<Arc<Vec<u8>>>,   // every shape seen, for a browser that joins late
    key: Option<Arc<Vec<u8>>>,   // the last frame carrying the cell layers
}

struct Client {
    q: Mutex<VecDeque<Arc<Vec<u8>>>>,
    cv: Condvar,
}

pub struct Live {
    pub control: Mutex<Control>,
    clients: Mutex<Vec<Arc<Client>>>,
    backlog: Mutex<Backlog>,
    header_rec: Arc<Vec<u8>>,
    header_json: String,
}

const QUEUE_MAX: usize = 240; // a browser that falls behind loses the oldest frames, not the world

impl Live {
    pub fn start(port: u16, header_json: String, header_rec: Vec<u8>, speed: f32, from: u64) -> Arc<Live> {
        let live = Arc::new(Live {
            control: Mutex::new(Control { speed, paused: false, fast_until: from, once: false }),
            clients: Mutex::new(Vec::new()),
            backlog: Mutex::new(Backlog::default()),
            header_rec: Arc::new(header_rec),
            header_json,
        });
        let listener = TcpListener::bind(("127.0.0.1", port)).unwrap_or_else(|e| panic!("viewer: port {port}: {e}"));
        http::warn_if_stale(&http::web_dir());
        let l = live.clone();
        std::thread::spawn(move || {
            for s in listener.incoming().flatten() {
                let l = l.clone();
                std::thread::spawn(move || {
                    let _ = s.set_nodelay(true);
                    l.handle(s);
                });
            }
        });
        live
    }

    pub fn watchers(&self) -> usize {
        self.clients.lock().unwrap().len()
    }

    pub fn push_body(&self, rec: Arc<Vec<u8>>) {
        self.backlog.lock().unwrap().bodies.push(rec.clone());
        self.push(rec);
    }

    pub fn push_frame(&self, rec: Arc<Vec<u8>>, key: bool) {
        if key {
            self.backlog.lock().unwrap().key = Some(rec.clone());
        }
        self.push(rec);
    }

    fn push(&self, rec: Arc<Vec<u8>>) {
        for c in self.clients.lock().unwrap().iter() {
            let mut q = c.q.lock().unwrap();
            if q.len() >= QUEUE_MAX {
                q.pop_front();
            }
            q.push_back(rec.clone());
            c.cv.notify_one();
        }
    }

    fn handle(self: &Arc<Self>, mut s: TcpStream) {
        let Some(req) = http::read_request(&mut s) else { return };
        let _ = match req.path.as_str() {
            "/world.json" => http::send(&mut s, "200 OK", "application/json", self.header_json.as_bytes()),
            "/state" => {
                let c = self.control.lock().unwrap();
                let body = format!("{{\"live\":true,\"speed\":{},\"paused\":{},\"watchers\":{}}}", c.speed, c.paused, self.clients.lock().unwrap().len());
                drop(c);
                http::send(&mut s, "200 OK", "application/json", body.as_bytes())
            }
            "/control" => {
                {
                    let mut c = self.control.lock().unwrap();
                    if let Some(v) = req.num::<f32>("speed") {
                        c.speed = v.clamp(0.05, 100_000.0);
                    }
                    if let Some(v) = req.num::<u8>("paused") {
                        c.paused = v != 0;
                    }
                    if req.num::<u8>("once").is_some() {
                        c.once = true;
                    }
                    if let Some(v) = req.num::<u64>("skip") {
                        c.fast_until = c.fast_until.max(v);
                    }
                }
                http::send(&mut s, "200 OK", "application/json", b"{\"ok\":true}")
            }
            "/stream" => {
                self.stream(s);
                return;
            }
            p => {
                let web = http::web_dir();
                match http::serve_file(&mut s, &web, p) {
                    Ok(true) => Ok(()),
                    _ => http::not_found(&mut s),
                }
            }
        };
    }

    fn stream(self: &Arc<Self>, mut s: TcpStream) {
        let client = Arc::new(Client { q: Mutex::new(VecDeque::new()), cv: Condvar::new() });
        // The world so far: the header, every shape, the last frame with the cell layers. It is
        // taken while the queue is already registered, so nothing is missed and nothing is
        // doubled that would matter (a repeated frame is idempotent).
        let start: Vec<Arc<Vec<u8>>> = {
            let mut clients = self.clients.lock().unwrap();
            let b = self.backlog.lock().unwrap();
            clients.push(client.clone());
            let mut v = vec![self.header_rec.clone()];
            v.extend(b.bodies.iter().cloned());
            v.extend(b.key.iter().cloned());
            v
        };
        let ok = http::chunked(&mut s, "application/octet-stream").is_ok() && start.iter().all(|r| http::chunk(&mut s, r).is_ok());
        if ok {
            loop {
                let rec = {
                    let mut q = client.q.lock().unwrap();
                    while q.is_empty() {
                        let (g, t) = client.cv.wait_timeout(q, Duration::from_millis(500)).unwrap();
                        q = g;
                        if t.timed_out() && q.is_empty() {
                            break;
                        }
                    }
                    q.pop_front()
                };
                match rec {
                    Some(r) => {
                        if http::chunk(&mut s, &r).is_err() {
                            break;
                        }
                    }
                    None => continue, // idle: the world may be paused
                }
            }
        }
        self.clients.lock().unwrap().retain(|c| !Arc::ptr_eq(c, &client));
    }
}
