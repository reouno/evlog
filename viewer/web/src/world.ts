// The world as the browser holds it: the header (what this world is made of), the shapes of
// the bodies, and a window of frames around wherever the watcher is looking.
//
// Nothing here knows about the experiment: the header says what the layers, the globals and the
// agent record are, and everything below reads them by name.

import type { AgentColumns, AgentField, AgentFieldSpec, Header, Layers, LayerSpec, NumType, Params } from './wire.js';

const TYPES: Record<NumType, number> = { u8: 1, u16: 2, u32: 4, f32: 4 };

/** A body's shape, as it was sent: one per shape, named by the frames. */
export interface BodyShape {
  id: number;
  side: number;
  cells: Uint8Array;
  n: number; // how many of its cells hold a block
}

/** One block of a body, turned the way the body faces: `r` south, `c` east. */
export interface Block {
  r: number;
  c: number;
  kind: number;
}

export interface TurnedShape {
  side: number;
  blocks: Block[];
}

/** One frame as the browser holds it: the bodies as a flat array per field, an index from a
 * body's id to its place in them, and what died since the frame before. */
export interface Frame {
  step: number;
  globals: Record<string, number | undefined>;
  n: number;
  a: AgentColumns;
  index: Map<number, number>;
  deaths: Map<number, number> | null;
}

/** A field of the agent record, with where in the record it sits. */
export interface FieldPlan extends AgentFieldSpec {
  off: number;
}

/** The season as the law states it: see `World.seasonOf`. */
export interface Season {
  on: boolean;
  period: number;
  amp: number;
  byHeight: boolean;
  at: Float32Array; // how much of its sun a cell loses in winter
  top: number;
}

/** What a frame after the last one a body was in says it died of. */
export interface Death {
  at: number;
  cause: string;
}

/** Where a body was last seen: the frame and its place in it, or nothing left of it. */
export type Fate =
  | { f: Frame; i: number; died: Death | null }
  | { f: null; i?: undefined; died: Death | null };

// The wood of a cell (`World.woodAt`): a tree with a leaf on it keeps its height, and a bare one
// rots away with this half-life (steps). WOOD_BARE (and WOOD_RAMP over it) is how little of the
// wood can still be living matter and count as a tree with a leaf on it; WOOD_BACK and WOOD_KEYS
// are how far back the memory is run when the watcher arrives somewhere new.
const WOOD_ROT = 100;
const WOOD_BARE = 0.12;
const WOOD_RAMP = 0.06;
const WOOD_BACK = 4000;
const WOOD_KEYS = 40;

export class World {
  h: Header;
  w: number;
  d: number;
  cells: number;
  sub: number;
  params: Params;
  height: Float32Array;
  band: Uint8Array;
  layerOf: Record<string, number>;
  bodies: Map<number, BodyShape>;
  turned: Map<number, TurnedShape>;
  frames: Map<number, Frame>;
  steps: number[];
  keys: Map<number, (Uint8Array | undefined)[]>;
  keySteps: number[];
  decoded: { step: number; v: Layers };
  peak: { at: number; cur: Float32Array | null; plant: Float32Array | null; was: Float32Array | null };
  luts: Float32Array[];
  unpacked: Float32Array[];
  plan: FieldPlan[];
  stride: number;
  fields: Record<AgentField, FieldPlan | undefined>;
  relief: number;
  wet: number;
  depth: number;
  season: Season;
  woodv?: Float32Array;

  constructor(header: Header) {
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
    this.peak = { at: -1, cur: null, plant: null, was: null }; // the wood at the keyframe the watcher is in
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
    this.fields = Object.fromEntries(this.plan.map((p) => [p.name, p])) as Record<AgentField, FieldPlan | undefined>;
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
  seasonOf(): Season {
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
  swing(step: number): number {
    return this.season.on ? Math.sin((2 * Math.PI * step) / this.season.period) : 0;
  }

  /** The year as a turn of the dial: 0 spring, 0.25 summer, 0.5 autumn, 0.75 winter. */
  year(step: number): number {
    return ((step / this.season.period) % 1 + 1) % 1;
  }

  /** The factor on a cell's own sun: 0 (the sun is out there) to 1 + a. */
  cellSun(c: number, swing: number): number {
    return Math.max(0, 1 + this.season.at[c] * swing);
  }

  /** The factor over the ground around a point, not just under it: the light and the sky belong
   * to a view, and a view takes in a stretch of hillside, not the one cell the eye sits on. */
  sunAt(x: number, z: number, swing: number, r = 24): number {
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

  addBody(p: Uint8Array): void {
    const dv = new DataView(p.buffer, p.byteOffset, p.byteLength);
    const id = dv.getUint32(0, true);
    const side = p[4];
    const cells = p.slice(5, 5 + side * side);
    let n = 0;
    for (const k of cells) if (k) n++;
    this.bodies.set(id, { id, side, cells, n });
  }

  addFrame(p: Uint8Array): number {
    const dv = new DataView(p.buffer, p.byteOffset, p.byteLength);
    let o = 0;
    const step = Number(dv.getBigUint64(o, true)); o += 8;
    const ng = p[o]; o += 1;
    const globals: Record<string, number | undefined> = {};
    (this.h.globals || []).forEach((name, i) => (globals[name] = i < ng ? dv.getFloat32(o + i * 4, true) : 0));
    o += ng * 4;
    const nl = p[o]; o += 1;
    if (nl > 0) {
      const layers: (Uint8Array | undefined)[] = [];
      for (let i = 0; i < nl; i++) {
        const idx = p[o]; o += 1;
        layers[idx] = p.slice(o, o + this.cells);
        o += this.cells;
      }
      this.keys.set(step, layers);
      insort(this.keySteps, step);
    }
    const n = dv.getUint32(o, true); o += 4;
    const a = {} as AgentColumns;
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
    o += n * this.stride;
    // The bodies that died since the frame before, and of what (a number into the header's `deaths`).
    let deaths: Map<number, number> | null = null;
    if (this.h.deaths && this.h.deaths.length) {
      const m = dv.getUint32(o, true); o += 4;
      deaths = new Map();
      for (let k = 0; k < m; k++, o += 5) deaths.set(dv.getUint32(o, true), p[o + 4]);
    }
    const index = new Map<number, number>();
    for (let i = 0; i < n; i++) index.set(a.id[i], i);
    this.frames.set(step, { step, globals, n, a, index, deaths });
    insort(this.steps, step);
    return step;
  }

  /** What a field's byte stands for at its fullest, or 1 where the field is a plain number. */
  maxOf(name: AgentField): number {
    return this.fields[name]?.max ?? 1;
  }

  /** A body's field in a frame as the world meant it: a byte with a `max` is that share of it. */
  value(f: Frame, name: AgentField, i: number | undefined): number | undefined {
    const p = this.fields[name];
    if (!p || i === undefined) return undefined;
    const v = f.a[name][i];
    return p.max !== undefined ? (v / 255) * p.max : v;
  }

  /** The last frame at or before `step` that holds body `id`, and what it died of if a frame
   * after that one says so. A living body is in the frame at `step`, so it is found first. */
  fate(id: number, step: number): Fate {
    let died: Death | null = null;
    for (let k = this.steps.length - 1; k >= 0; k--) {
      if (this.steps[k] > step) continue;
      const f = this.frames.get(this.steps[k])!;
      const i = f.index.get(id);
      if (i !== undefined) return { f, i, died };
      const c = f.deaths ? f.deaths.get(id) : undefined;
      if (c !== undefined) died = { at: f.step, cause: this.h.deaths[c] };
    }
    return { f: null, i: undefined, died };
  }

  /** The frame at or before `step` and the one after it, how far between them `step` is, and the
   * frames on either side of those two.
   *
   * The outer pair is what makes the move between the inner pair smooth: with only two frames a
   * body runs in a straight line and every one of them changes direction at the same instant, at
   * every frame of the recording. They are given only when they are a whole interval away, so a
   * gap in what has been loaded cannot bend the curve. */
  around(step: number): [Frame | null, Frame | null, number, Frame | null, Frame | null] {
    const i = upperBound(this.steps, step) - 1;
    if (i < 0) return [null, null, 0, null, null];
    const a = this.frames.get(this.steps[i])!;
    const b = i + 1 < this.steps.length ? this.frames.get(this.steps[i + 1])! : null;
    const t = b && b.step > a.step ? Math.min(1, (step - a.step) / (b.step - a.step)) : 0;
    if (!b) return [a, null, 0, null, null];
    const span = b.step - a.step;
    const before = i > 0 ? this.frames.get(this.steps[i - 1])! : null;
    const after = i + 2 < this.steps.length ? this.frames.get(this.steps[i + 2])! : null;
    return [a, b, t, before && a.step - before.step === span ? before : null, after && after.step - b.step === span ? after : null];
  }

  hasFrame(step: number): boolean {
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
  layersAt(step: number, grain = 20): Layers | null {
    const i = upperBound(this.keySteps, step) - 1;
    if (i < 0) return null;
    const at = this.keySteps[i];
    const next = i + 1 < this.keySteps.length ? this.keySteps[i + 1] : at;
    const packed = this.keys.get(at)!;
    const ahead = next > at ? this.keys.get(next) : null;
    const u = ahead ? Math.round(((step - at) / (next - at)) * grain) / grain : 0;
    if (this.decoded.step === at + u) return this.decoded.v;
    const v: Layers = {};
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
    if (v.plant) v.wood = this.woodAt(i, u * (next - at), v.plant);
    this.decoded = { step: at + u, v };
    return v;
  }

  /** The wood on a cell: not what stands there now, but what stood there while anything did.
   *
   * The world holds one number for a cell - the matter standing on it - and a body eats it: on
   * e041 half of the cells drawn as a tree hold less at the next keyframe than at this one.
   * Drawn as height, that is a tree sinking back into the ground, which no tree does. So the
   * wood is held while any of it is still alive, and only rots (a half-life of WOOD_ROT steps)
   * once none of it is: a grazed column loses its leaves, and then a dead pole stands and goes.
   *
   * The rule runs on the blended plant and not only on the keyframes, because a whole tree can
   * be eaten inside one interval: blending between the wood at two keyframes made a green tree
   * slide into the ground over the 200 steps between them.
   *
   * The memory is run from the recording itself rather than carried along, so seeking to a step
   * gives what playing to it does (measured: the same to 0.01 units of matter). */
  woodAt(i: number, du: number, plant: Float32Array): Float32Array {
    // Keyed by the step and not by the index: `trim` drops old keyframes, and every index moves.
    if (this.peak.at !== this.keySteps[i]) this.remember(i);
    const out = this.woodv || (this.woodv = new Float32Array(this.cells));
    out.set(this.peak.cur!);
    age(out, this.peak.plant!, plant, du, this.cells);
    return out;
  }

  /** The wood at the keyframe `i`: one step on from where the memory stands, or, if the watcher
   * is somewhere else, run over the keyframes before it. Once a keyframe, not once a frame. */
  remember(i: number): void {
    const k = this.layerOf.plant;
    const lut = this.luts[k] || (this.luts[k] = table(this.h.layers[k]));
    const cur = this.peak.cur || (this.peak.cur = new Float32Array(this.cells));
    // The plant at that keyframe, which is where the rot inside the interval after it counts
    // from, and a spare to read the next one into.
    let now = this.peak.plant || (this.peak.plant = new Float32Array(this.cells));
    let spare = this.peak.was || (this.peak.was = new Float32Array(this.cells));
    const at = this.keySteps[i];
    const on = i > 0 && this.peak.at === this.keySteps[i - 1]; // playing on, which is most of it
    let first = i;
    if (!on) while (first > 0 && i - first < WOOD_KEYS && at - this.keySteps[first - 1] < WOOD_BACK) first--;
    for (let j = on ? i : first; j <= i; j++) {
      const src = (this.keys.get(this.keySteps[j]) || [])[k];
      if (!src) continue;
      for (let c = 0; c < this.cells; c++) spare[c] = lut[src[c]];
      if (!on && j === first) cur.set(spare);
      else age(cur, now, spare, this.keySteps[j] - this.keySteps[j - 1], this.cells);
      const swap = now;
      now = spare;
      spare = swap; // what was just read is the keyframe the next step counts from
    }
    this.peak.plant = now;
    this.peak.was = spare;
    this.peak.at = at;
  }

  /** Forget what is far from `step`, so a long watch does not fill the browser. */
  trim(step: number, keep = 400): void {
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
  blocks(bodyId: number, facing: number): TurnedShape | null {
    const key = bodyId * 4 + facing;
    const hit = this.turned.get(key);
    if (hit !== undefined) return hit;
    const out = this.turn(bodyId, facing);
    if (out) this.turned.set(key, out); // a shape not seen yet may still arrive
    return out;
  }

  turn(bodyId: number, facing: number): TurnedShape | null {
    const b = this.bodies.get(bodyId);
    if (!b) return null;
    const s = b.side, m = s - 1, out: Block[] = [];
    for (let i = 0; i < s * s; i++) {
      const k = b.cells[i];
      if (k === 0) continue;
      const r = (i / s) | 0, c = i % s;
      let r2: number, c2: number;
      if (facing === 0) { r2 = r; c2 = c; }            // north: the front row points north
      else if (facing === 1) { r2 = m - r; c2 = m - c; } // south
      else if (facing === 2) { r2 = c; c2 = m - r; }     // east
      else { r2 = m - c; c2 = r; }                       // west
      out.push({ r: r2, c: c2, kind: k });
    }
    return { side: s, blocks: out };
  }
}

/** The wood after `du` steps in which the matter standing on the cell went from `was` to `now`:
 * what stands there now, or the wood that was there, rotted by however much of those steps it
 * spent bare (WOOD_BARE of it, or less, being living matter).
 *
 * It is the time spent bare and not the state at the end of it, because the tree can be eaten
 * inside one interval: charging the whole interval's rot at the moment the last leaf goes drops
 * a tree by three quarters in one frame. */
function age(wood: Float32Array, was: Float32Array, now: Float32Array, du: number, cells: number): void {
  for (let c = 0; c < cells; c++) {
    const w = wood[c], p = now[c];
    if (p >= w) {
      // Growing, or nothing there: the wood is what stands. Most of a world is this.
      wood[c] = p;
      continue;
    }
    const a = Math.min(1, Math.max(0, (was[c] / w - WOOD_BARE) / WOOD_RAMP));
    const b = Math.min(1, Math.max(0, (p / w - WOOD_BARE) / WOOD_RAMP));
    const bare = du * (1 - 0.5 * (a + b));
    const left = bare > 0 ? w * Math.pow(0.5, bare / WOOD_ROT) : w;
    wood[c] = p > left ? p : left;
  }
}

/** The 256 values a layer's byte can stand for, under its own scale. */
function table(spec: LayerSpec): Float32Array {
  const t = new Float32Array(256), max = spec.max, l = Math.log(1 + max);
  for (let b = 0; b < 256; b++) {
    const q = b / 255;
    t[b] = spec.scale === 'linear' ? q * max : spec.scale === 'sqrt' ? q * q * max : Math.exp(q * l) - 1;
  }
  return t;
}

function insort(arr: number[], v: number): void {
  const i = upperBound(arr, v);
  if (i > 0 && arr[i - 1] === v) return;
  arr.splice(i, 0, v);
}

function upperBound(arr: number[], v: number): number {
  let lo = 0, hi = arr.length;
  while (lo < hi) {
    const mid = (lo + hi) >> 1;
    if (arr[mid] <= v) lo = mid + 1;
    else hi = mid;
  }
  return lo;
}
