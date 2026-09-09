// Where the records come from: a world running now (/stream), or a recorded one (/frames).
// Both give the same records; only the seeking differs.

const HEADER = 0, BODY = 1, FRAME = 2;

/** Cuts a byte stream into records. Keeps what is left of a half record for the next chunk. */
export class RecordParser {
  constructor(onRecord) {
    this.onRecord = onRecord;
    this.left = new Uint8Array(0);
  }
  push(chunk) {
    let buf;
    if (this.left.length === 0) buf = chunk;
    else {
      buf = new Uint8Array(this.left.length + chunk.length);
      buf.set(this.left, 0);
      buf.set(chunk, this.left.length);
    }
    let i = 0;
    while (i + 5 <= buf.length) {
      const kind = buf[i];
      const len = buf[i + 1] | (buf[i + 2] << 8) | (buf[i + 3] << 16) | (buf[i + 4] << 24);
      if (i + 5 + len > buf.length) break;
      this.onRecord(kind, buf.subarray(i + 5, i + 5 + len));
      i += 5 + len;
    }
    this.left = buf.subarray(i).slice();
  }
}

export const RECORD = { HEADER, BODY, FRAME };

/** A world running now: it streams its frames and takes orders about its speed. */
export class LiveSource {
  constructor(handlers) {
    this.h = handlers;
    this.live = true;
    this.stopped = false;
  }
  async start() {
    const res = await fetch('/stream');
    const reader = res.body.getReader();
    const parser = new RecordParser((kind, payload) => this.h.record(kind, payload));
    for (;;) {
      const { done, value } = await reader.read();
      if (done || this.stopped) break;
      parser.push(value);
    }
  }
  // The world's own pace, in steps a second.
  async control(q) {
    await fetch('/control?' + new URLSearchParams(q));
  }
  setSpeed(s) { this.control({ speed: s }); }
  setPaused(p) { this.control({ paused: p ? 1 : 0 }); }
  stepOnce() { this.control({ once: 1 }); }
  seek(step) { this.control({ skip: Math.round(step) }); }
}

/** A recorded world: frames are asked for around wherever the watcher is looking. */
export class ReplaySource {
  constructor(handlers) {
    this.h = handlers;
    this.live = false;
    this.asked = new Set(); // fetches in flight or done, by their `from` step
  }
  async start() {
    const header = await (await fetch('/world.json')).json();
    // What the recording holds, before anything is told about it: the bar reads these.
    this.first = header.replay.first;
    this.last = header.replay.last;
    this.stride = header.stride;
    this.h.record(HEADER, new TextEncoder().encode(JSON.stringify(header)));
    const bodies = new Uint8Array(await (await fetch('/bodies')).arrayBuffer());
    new RecordParser((kind, payload) => this.h.record(kind, payload)).push(bodies);
    await this.fetchFrom(this.first);
  }
  /** Ask for a run of frames from `step` on, once. */
  async fetchFrom(step, count = 240) {
    step = Math.max(this.first, Math.min(this.last, Math.round(step)));
    const key = Math.floor((step - this.first) / (this.stride * count));
    if (this.asked.has(key)) return;
    this.asked.add(key);
    const from = this.first + key * this.stride * count;
    const buf = new Uint8Array(await (await fetch(`/frames?from=${from}&count=${count}`)).arrayBuffer());
    new RecordParser((kind, payload) => this.h.record(kind, payload)).push(buf);
  }
}
