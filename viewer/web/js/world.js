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
    this.turned = new Map(); // (shape, facing) -> its blocks in the world frame
    this.frames = new Map(); // step -> frame
    this.steps = [];         // the steps in `frames`, sorted
    this.keys = new Map();   // step -> [Uint8Array per layer]  (frames that carry the layers)
    this.keySteps = [];
    this.decoded = { step: -1, v: {} };
    this.luts = [];     // byte -> value, one table per layer
    this.unpacked = []; // the values of the layers being shown, reused rather than reallocated
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
    this.season = this.seasonOf();
  }

  /** The season, read off the law itself rather than off the number in a frame.
   *
   * The world's sun is RES_GROWTH times (1 + a(cell) sin(2 pi step / period)): `period` and the
   * amplitude `a` are in the header's params, and under `winter high` (e032) the amplitude is the
   * cell's own, by its height. So the browser knows the year from the step alone, and knows which
   * places are in winter while others are not - which is the whole point of that law. */
  seasonOf() {
    const p = this.params;
    const amp = p.amplitude ?? 1;
    const on = p.weather === 'season' && amp > 0;
    const at = new Float32Array(this.cells);
    const byHeight = p.winter === 'high';
    for (let c = 0; c < this.cells; c++) {
      at[c] = on ? (byHeight ? Math.min(1, (amp * this.height[c]) / this.relief) : amp) : 0;
    }
    let top = 0;
    for (let c = 0; c < this.cells; c++) top = Math.max(top, at[c]);
    return { on, period: p.season || 20000, amp, byHeight, at, top };
  }

  /** Where in the year a step falls, as the sine of it: +1 midsummer, -1 midwinter, 0 between. */
  swing(step) {
    return this.season.on ? Math.sin((2 * Math.PI * step) / this.season.period) : 0;
  }

  /** The year as a turn of the dial: 0 spring, 0.25 summer, 0.5 autumn, 0.75 winter. */
  year(step) {
    return ((step / this.season.period) % 1 + 1) % 1;
  }

  /** The factor on a cell's own sun: 0 (the sun is out there) to 1 + a. */
  cellSun(c, swing) {
    return Math.max(0, 1 + this.season.at[c] * swing);
  }

  /** The factor over the ground around a point, not just under it: the light and the sky belong
   * to a view, and a view takes in a stretch of hillside, not the one cell the eye sits on. */
  sunAt(x, z, swing, r = 24) {
    let sum = 0, n = 0;
    for (let dz = -r; dz <= r; dz += 6) {
      const j = ((Math.round(z + dz) % this.d) + this.d) % this.d;
      for (let dx = -r; dx <= r; dx += 6) {
        sum += this.season.at[j * this.w + (((Math.round(x + dx) % this.w) + this.w) % this.w)];
        n++;
      }
    }
    return Math.max(0, 1 + (sum / n) * swing);
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

  /** The frame at or before `step` and the one after it, how far between them `step` is, and the
   * frames on either side of those two.
   *
   * The outer pair is what makes the move between the inner pair smooth: with only two frames a
   * body runs in a straight line and every one of them changes direction at the same instant, at
   * every frame of the recording. They are given only when they are a whole interval away, so a
   * gap in what has been loaded cannot bend the curve. */
  around(step) {
    const i = upperBound(this.steps, step) - 1;
    if (i < 0) return [null, null, 0, null, null];
    const a = this.frames.get(this.steps[i]);
    const b = i + 1 < this.steps.length ? this.frames.get(this.steps[i + 1]) : null;
    const t = b && b.step > a.step ? Math.min(1, (step - a.step) / (b.step - a.step)) : 0;
    if (!b) return [a, null, 0, null, null];
    const span = b.step - a.step;
    const before = i > 0 ? this.frames.get(this.steps[i - 1]) : null;
    const after = i + 2 < this.steps.length ? this.frames.get(this.steps[i + 2]) : null;
    return [a, b, t, before && a.step - before.step === span ? before : null, after && after.step - b.step === span ? after : null];
  }

  hasFrame(step) {
    return upperBound(this.steps, step) > 0;
  }

  /** The cell layers at `step`, as physical values: {plant, water, soil, ...}.
   *
   * The layers are only recorded every `layer_stride` frames, because they change slowly - but
   * slowly is not never. A tree grows a cell in a few hundred steps, so taking the nearest frame
   * makes everything that grows, and the colour of the whole ground with it, jump at once every
   * time one arrives: on this recording the standing plant matter sat at 7,857 for 200 steps and
   * then moved 341 in a single frame. So the two frames around `step` are blended.
   *
   * `grain` is how finely the blend is cut. Colouring the ground and rebuilding the plants is the
   * cost, and they are only done when these values change, so this is how many times that happens
   * between two recorded frames. */
  layersAt(step, grain = 20) {
    const i = upperBound(this.keySteps, step) - 1;
    if (i < 0) return null;
    const at = this.keySteps[i];
    const next = i + 1 < this.keySteps.length ? this.keySteps[i + 1] : at;
    const packed = this.keys.get(at);
    const ahead = next > at ? this.keys.get(next) : null;
    const u = ahead ? Math.round(((step - at) / (next - at)) * grain) / grain : 0;
    if (this.decoded.step === at + u) return this.decoded.v;
    const v = {};
    // A layer arrives as one byte a cell, so the whole unpacking is a table of 256 values: the
    // scale is worked out once per layer instead of once per cell (this runs on every keyframe).
    this.h.layers.forEach((spec, k) => {
      const src = packed[k];
      if (!src) return;
      const out = this.unpacked[k] || (this.unpacked[k] = new Float32Array(this.cells));
      const lut = this.luts[k] || (this.luts[k] = table(spec));
      const to = u > 0 && ahead ? ahead[k] : null;
      if (to) for (let c = 0; c < this.cells; c++) out[c] = lut[src[c]] + (lut[to[c]] - lut[src[c]]) * u;
      else for (let c = 0; c < this.cells; c++) out[c] = lut[src[c]];
      v[spec.name] = out;
    });
    this.decoded = { step: at + u, v };
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

  /** The blocks of one body in the world frame: [{c, r, kind}] with r south, c east.
   * A shape turned a way is the same every time it is drawn, so it is worked out once. */
  blocks(bodyId, facing) {
    const key = bodyId * 4 + facing;
    const hit = this.turned.get(key);
    if (hit !== undefined) return hit;
    const out = this.turn(bodyId, facing);
    if (out) this.turned.set(key, out); // a shape not seen yet may still arrive
    return out;
  }

  turn(bodyId, facing) {
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

/** The 256 values a layer's byte can stand for, under its own scale. */
function table(spec) {
  const t = new Float32Array(256), max = spec.max, l = Math.log(1 + max);
  for (let b = 0; b < 256; b++) {
    const q = b / 255;
    t[b] = spec.scale === 'linear' ? q * max : spec.scale === 'sqrt' ? q * q * max : Math.exp(q * l) - 1;
  }
  return t;
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
