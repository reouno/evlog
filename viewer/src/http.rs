//! The smallest HTTP server that serves the web app and streams the records (std only).

use std::collections::HashMap;
use std::io::{self, Read, Write};
use std::net::TcpStream;
use std::path::{Path, PathBuf};

pub struct Req {
    pub path: String,
    pub query: HashMap<String, String>,
}

impl Req {
    pub fn num<T: std::str::FromStr>(&self, key: &str) -> Option<T> {
        self.query.get(key).and_then(|v| v.parse().ok())
    }
}

pub fn read_request(s: &mut TcpStream) -> Option<Req> {
    let mut buf = Vec::with_capacity(1024);
    let mut b = [0u8; 512];
    while !buf.windows(4).any(|w| w == b"\r\n\r\n") {
        let n = s.read(&mut b).ok()?;
        if n == 0 || buf.len() > 16384 {
            return None;
        }
        buf.extend_from_slice(&b[..n]);
    }
    let line = String::from_utf8_lossy(&buf).lines().next()?.to_string();
    let target = line.split(' ').nth(1)?.to_string();
    let (path, q) = target.split_once('?').unwrap_or((target.as_str(), ""));
    let query = q
        .split('&')
        .filter(|p| !p.is_empty())
        .filter_map(|p| p.split_once('=').map(|(k, v)| (k.to_string(), v.to_string())))
        .collect();
    Some(Req { path: path.to_string(), query })
}

pub fn send(s: &mut TcpStream, status: &str, ctype: &str, body: &[u8]) -> io::Result<()> {
    write!(s, "HTTP/1.1 {status}\r\nContent-Type: {ctype}\r\nContent-Length: {}\r\nCache-Control: no-store\r\nConnection: close\r\n\r\n", body.len())?;
    s.write_all(body)
}

pub fn not_found(s: &mut TcpStream) -> io::Result<()> {
    send(s, "404 Not Found", "text/plain", b"not here")
}

pub fn chunked(s: &mut TcpStream, ctype: &str) -> io::Result<()> {
    write!(s, "HTTP/1.1 200 OK\r\nContent-Type: {ctype}\r\nTransfer-Encoding: chunked\r\nCache-Control: no-store\r\nConnection: close\r\n\r\n")
}

pub fn chunk(s: &mut TcpStream, data: &[u8]) -> io::Result<()> {
    write!(s, "{:x}\r\n", data.len())?;
    s.write_all(data)?;
    s.write_all(b"\r\n")
}

fn mime(path: &str) -> &'static str {
    match path.rsplit('.').next().unwrap_or("") {
        "html" => "text/html; charset=utf-8",
        "js" => "text/javascript; charset=utf-8",
        "css" => "text/css; charset=utf-8",
        "json" => "application/json",
        "svg" => "image/svg+xml",
        "png" => "image/png",
        _ => "application/octet-stream",
    }
}

/// The web app's directory: the crate's own `web/`, or EVLOG_VIEW_WEB.
pub fn web_dir() -> PathBuf {
    match std::env::var("EVLOG_VIEW_WEB") {
        Ok(p) => PathBuf::from(p),
        Err(_) => PathBuf::from(concat!(env!("CARGO_MANIFEST_DIR"), "/web")),
    }
}

/// Serve a file from the web directory. False when there is no such file.
pub fn serve_file(s: &mut TcpStream, web: &Path, path: &str) -> io::Result<bool> {
    let rel = if path == "/" { "index.html" } else { path.trim_start_matches('/') };
    if rel.contains("..") {
        return Ok(false);
    }
    match std::fs::read(web.join(rel)) {
        Ok(body) => send(s, "200 OK", mime(rel), &body).map(|_| true),
        Err(_) => Ok(false),
    }
}
