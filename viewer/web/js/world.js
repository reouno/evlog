// The world as the browser holds it: the header (what this world is made of), the shapes of
// the bodies, and a window of frames around wherever the watcher is looking.
//
// Nothing here knows about the experiment: the header says what the layers, the globals and the
// agent record are, and everything below reads them by name.

const TYPES = { u8: 1, u16: 2, u32: 4, f32: 4 };

export class World {
  constructor(header) {
    this.h = header;
    this.w = header.w;
    this.d = header.h; // depth: the grid's other side (the world's y)
    this.cells = this.w * this.d;
    this.sub = header.sub;
    this.params = header.params || {};
    this.height = Float32Array.from(header.height);
    this.band = Uint8Array.from(header.band || []);
    this.layerOf = {};
    header.layers.forEach((l, i) => (this.layerOf[l.name] = i));
    this.bodies = new Map();
    this.frames = new Map(); // step -> frame
    this.steps = [];         // the steps in `frames`, sorted
    this.keys = new Map();   // step -> [Uint8Array per layer]  (frames that carry the layers)
    this.keySteps = [];
    this.decoded = { step: -1, v: {} };
    // The agent record, read off the header.
    let off = 0;
    this.plan = header.agent_record.map((f) => {
      const p = { ...f, off };
      off += TYPES[f.type];
      return p;
    });
    this.stride = off;
    this.relief = this.params.relief || 1;
    this.wet = (this.params.water_rain || 1) / (this.params.water_evap || 1); // a cell's own water
    this.depth = this.params.depth || 0; // height per unit of water
  }

  addBody(p) {
    const dv = new DataView(p.buffer, p.byteOffset, p.byteLength);
    const id = dv.getUint32(0, true);
    const side = p[4];
    this.bodies.set(id, { id, side, cells: p.slice(5, 5 + side * side) });
  }

  addFrame(p) {
    const dv = new DataView(p.buffer, p.byteOffset, p.byteLength);
    let o = 0;
    const step = Number(dv.getBigUint64(o, true)); o += 8;
    const ng = p[o]; o += 1;
    const globals = {};
    (this.h.globals || []).forEach((name, i) => (globals[name] = i < ng ? dv.getFloat32(o + i * 4, true) : 0));
    o += ng * 4;
    const nl = p[o]; o += 1;
    if (nl > 0) {
      const layers = [];
      for (let i = 0; i < nl; i++) {
        const idx = p[o]; o += 1;
        layers[idx] = p.slice(o, o + this.cells);
        o += this.cells;
      }
      this.keys.set(step, layers);
      insort(this.keySteps, step);
    }
    const n = dv.getUint32(o, true); o += 4;
    const a = {};
    for (const f of this.plan) {
      a[f.name] = f.type === 'u8' ? new Uint8Array(n) : f.type === 'u16' ? new Uint16Array(n) : new Uint32Array(n);
    }
    for (let i = 0; i < n; i++) {
      const base = o + i * this.stride;
      for (const f of this.plan) {
        const at = base + f.off;
        a[f.name][i] = f.type === 'u8' ? p[at] : f.type === 'u16' ? dv.getUint16(at, true) : dv.getUint32(at, true);
      }
    }
    const index = new Map();
    for (let i = 0; i < n; i++) index.set(a.id[i], i);
    this.frames.set(step, { step, globals, n, a, index });
    insort(this.steps, step);
    return step;
  }

  /** The frame at or before `step`, and the one after it, for a smooth move between them. */
  around(step) {
    const i = upperBound(this.steps, step) - 1;
    if (i < 0) return [null, null, 0];
    const a = this.frames.get(this.steps[i]);
    const b = i + 1 < this.steps.length ? this.frames.get(this.steps[i + 1]) : null;
    const t = b && b.step > a.step ? Math.min(1, (step - a.step) / (b.step - a.step)) : 0;
    return [a, b, t];
  }

  hasFrame(step) {
    return upperBound(this.steps, step) > 0;
  }

  /** The cell layers at `step`, as physical values: {plant, water, soil, ...}. */
  layersAt(step) {
    const i = upperBound(this.keySteps, step) - 1;
    if (i < 0) return null;
    const at = this.keySteps[i];
    if (this.decoded.step === at) return this.decoded.v;
    const packed = this.keys.get(at);
    const v = {};
    this.h.layers.forEach((spec, k) => {
      const src = packed[k];
      if (!src) return;
      const out = new Float32Array(this.cells);
      const max = spec.max;
      if (spec.scale === 'linear') for (let c = 0; c < this.cells; c++) out[c] = (src[c] / 255) * max;
      else if (spec.scale === 'sqrt') { for (let c = 0; c < this.cells; c++) { const q = src[c] / 255; out[c] = q * q * max; } }
      else { const l = Math.log(1 + max); for (let c = 0; c < this.cells; c++) out[c] = Math.exp((src[c] / 255) * l) - 1; }
      v[spec.name] = out;
    });
    this.decoded = { step: at, v };
    return v;
  }

  /** Forget what is far from `step`, so a long watch does not fill the browser. */
  trim(step, keep = 400) {
    for (const s of this.steps.slice()) {
      if (Math.abs(s - step) > keep * (this.h.stride || 1)) {
        this.frames.delete(s);
        this.steps.splice(this.steps.indexOf(s), 1);
        if (this.keys.has(s) && this.keySteps.length > 2) {
          this.keys.delete(s);
          this.keySteps.splice(this.keySteps.indexOf(s), 1);
        }
      }
    }
  }

  /** The blocks of one body in the world frame: [{c, r, kind}] with r south, c east. */
  blocks(bodyId, facing) {
    const b = this.bodies.get(bodyId);
    if (!b) return null;
    const s = b.side, m = s - 1, out = [];
    for (let i = 0; i < s * s; i++) {
      const k = b.cells[i];
      if (k === 0) continue;
      const r = (i / s) | 0, c = i % s;
      let r2, c2;
      if (facing === 0) { r2 = r; c2 = c; }            // north: the front row points north
      else if (facing === 1) { r2 = m - r; c2 = m - c; } // south
      else if (facing === 2) { r2 = c; c2 = m - r; }     // east
      else { r2 = m - c; c2 = r; }                       // west
      out.push({ r: r2, c: c2, kind: k });
    }
    return { side: s, blocks: out };
  }
}

function insort(arr, v) {
  const i = upperBound(arr, v);
  if (i > 0 && arr[i - 1] === v) return;
  arr.splice(i, 0, v);
}

function upperBound(arr, v) {
  let lo = 0, hi = arr.length;
  while (lo < hi) {
    const mid = (lo + hi) >> 1;
    if (arr[mid] <= v) lo = mid + 1;
    else hi = mid;
  }
  return lo;
}
