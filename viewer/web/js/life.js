// What lives on the ground: the plants that stand on a cell, what has fallen on it, and the
// bodies. Everything is instanced, and only what is near the eye is drawn in full.

import * as THREE from 'three';
import { UP } from './render.js';

const M = new THREE.Matrix4(), TURN = new THREE.Matrix4();
const V = new THREE.Vector3();
const HI = new THREE.Color(), WARM = new THREE.Color(0xffd24a);
// The palette of what grows. A season moves a colour between these, and a cell's own number
// picks where in a range it sits, so two neighbours are never the same green.
const LEAF0 = new THREE.Color(0x2f6d33), LEAF1 = new THREE.Color(0x1c4a24);
const LUSH = new THREE.Color(0x3f9a2e), AMBER = new THREE.Color(0xb5761f), SNOW = new THREE.Color(0xeff4f7);
const EVER = new THREE.Color(0x1e4230); // what a conifer goes to in the cold: darker, not amber
const BARK0 = new THREE.Color(0x6a4a30), BARK1 = new THREE.Color(0x46321f);
const DRY = new THREE.Color(0xe8e0b4), FRESH = new THREE.Color(0xa8d089), HAY = new THREE.Color(0xd2bd7e);
const FR0 = new THREE.Color(0xc06a2a), FR1 = new THREE.Color(0xa82f22);
const CAR0 = new THREE.Color(0x6d3a2c), CAR1 = new THREE.Color(0x4e2b23);
const LEAF = new THREE.Color(), DARK = new THREE.Color(), BARK = new THREE.Color();
// The bodies: a colour per kind of block, the socket an eye sits in, and the flat slab a body
// too far off to make out is drawn as, by what it eats.
const KIND = [null, new THREE.Color(0x2a2622), new THREE.Color(0xa8553c), new THREE.Color(0x1b1b20), new THREE.Color(0xb09760)];
const SOCKET = new THREE.Color(0x8f7f5e), SOCKETLIT = new THREE.Color(0xffe9a8);
const FAR = [0x9ecf6a, 0xd9a441, 0xc4553f, 0x9aa0a6].map((h) => new THREE.Color(h).multiplyScalar(0.5));
const FARLIT = new THREE.Color(0xffffff).multiplyScalar(0.5);
const TINT = new THREE.Color(), SPOT = new THREE.Color();

/** A pool of one shape, drawn many times. */
class Pool {
  constructor(scene, geo, mat, cap) {
    this.mesh = new THREE.InstancedMesh(geo, mat, cap);
    this.mesh.instanceMatrix.setUsage(THREE.DynamicDrawUsage);
    this.mesh.instanceColor = new THREE.InstancedBufferAttribute(new Float32Array(cap * 3).fill(1), 3);
    this.mesh.instanceColor.setUsage(THREE.DynamicDrawUsage);
    this.mesh.frustumCulled = false;
    this.mesh.count = 0;
    this.cap = cap;
    this.n = 0;
    this.sent = 0; // how many instances the card has, so an empty pool is not sent again
    scene.add(this.mesh);
  }
  reset() {
    this.n = 0;
  }
  /** The colour of the instance being written. It is taken apart here and not kept, so every
   * caller can hand over the same scratch colour. */
  tint(col) {
    const a = this.mesh.instanceColor.array, o = this.n * 3;
    a[o] = col.r; a[o + 1] = col.g; a[o + 2] = col.b;
  }
  /** An axis-aligned box or sprite: position, size, colour. No rotation, so the matrix is written by hand. */
  put(x, y, z, sx, sy, sz, col) {
    if (this.n >= this.cap) return;
    const a = this.mesh.instanceMatrix.array, o = this.n * 16;
    a[o] = sx; a[o + 1] = 0; a[o + 2] = 0; a[o + 3] = 0;
    a[o + 4] = 0; a[o + 5] = sy; a[o + 6] = 0; a[o + 7] = 0;
    a[o + 8] = 0; a[o + 9] = 0; a[o + 10] = sz; a[o + 11] = 0;
    a[o + 12] = x; a[o + 13] = y; a[o + 14] = z; a[o + 15] = 1;
    if (col !== undefined) this.tint(col);
    this.n++;
  }
  putM(m, col) {
    if (this.n >= this.cap) return;
    m.toArray(this.mesh.instanceMatrix.array, this.n * 16);
    if (col !== undefined) this.tint(col);
    this.n++;
  }
  /** Hand the pool to the card. A pool is made big enough for the worst case and is usually far
   * from full, so only what was written this time is sent: sending the whole buffer was most of
   * the cost of a frame that rebuilt the plants, and it is the size of the pool, not of the work. */
  done() {
    this.mesh.count = this.n;
    const m = this.mesh.instanceMatrix, c = this.mesh.instanceColor;
    if (this.n === 0 && this.sent === 0) return; // nothing there, and nothing was there before
    this.sent = this.n;
    m.clearUpdateRanges();
    m.addUpdateRange(0, this.n * 16);
    m.needsUpdate = true;
    c.clearUpdateRanges();
    c.addUpdateRange(0, this.n * 3);
    c.needsUpdate = true;
  }
}

function grassTexture() {
  const n = 128;
  const c = document.createElement('canvas');
  c.width = c.height = n;
  const g = c.getContext('2d');
  g.clearRect(0, 0, n, n);
  // A tuft: thin blades of their own length, bend and shade, the tips paler than the roots.
  for (let i = 0; i < 26; i++) {
    const x = 10 + Math.random() * (n - 20), h = (0.4 + Math.random() * 0.58) * n;
    const wdt = 1.4 + Math.random() * 2.6, bend = (Math.random() - 0.5) * 0.36 * n;
    const tip = n - h;
    const shade = 96 + Math.random() * 86;
    const grad = g.createLinearGradient(0, n, 0, tip);
    grad.addColorStop(0, `rgb(${(shade * 0.4) | 0},${(shade * 0.78) | 0},${(shade * 0.3) | 0})`);
    grad.addColorStop(1, `rgb(${(shade * 0.72) | 0},${shade | 0},${(shade * 0.45) | 0})`);
    g.beginPath();
    g.moveTo(x - wdt, n);
    g.quadraticCurveTo(x - wdt * 0.3 + bend * 0.5, n - h * 0.55, x + bend, tip);
    g.quadraticCurveTo(x + wdt * 0.3 + bend * 0.5, n - h * 0.55, x + wdt, n);
    g.closePath();
    g.fillStyle = grad;
    g.fill();
  }
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = THREE.SRGBColorSpace;
  return t;
}

/** A deterministic small number per cell, so the same cell always looks the same. */
function hash(c) {
  let x = (c * 2654435761) >>> 0;
  x ^= x >>> 15;
  x = Math.imul(x, 2246822519) >>> 0;
  return ((x >>> 8) & 0xffff) / 0xffff;
}

/** Another number for the same cell: which kind of tree, where in its cell, how it leans. */
function rnd(c, k) {
  return hash(c + k * 104729);
}


/** The pool a kind of block is drawn from (a kind the browser does not know goes in with the gut). */
function pools_of(life, k) {
  return life.blockPools[k] || life.blockPools[4];
}

export class Life {
  constructor(scene, world) {
    this.world = world;
    this.w = world.w;
    this.d = world.d;
    const box = new THREE.BoxGeometry(1, 1, 1);
    box.translate(0, 0.5, 0);
    // The parts a tree is put together from: a tapered trunk, a limb, a blob of leaves and a
    // spire. Three kinds of tree are these four parts in different numbers and places.
    const cyl = new THREE.CylinderGeometry(0.66, 1.0, 1, 7);
    cyl.translate(0, 0.5, 0);
    const limb = new THREE.CylinderGeometry(0.42, 1.0, 1, 5);
    limb.translate(0, 0.5, 0);
    const crown = new THREE.IcosahedronGeometry(1, 1);
    const spire = new THREE.ConeGeometry(1, 1, 7);
    spire.translate(0, 0.5, 0);
    const ball = new THREE.SphereGeometry(1, 8, 6);
    const quad = new THREE.PlaneGeometry(1, 1);
    quad.translate(0, 0.5, 0);
    const grassMat = new THREE.MeshStandardMaterial({ map: grassTexture(), transparent: true, alphaTest: 0.35, side: THREE.DoubleSide, roughness: 1 });
    const leaf = new THREE.MeshStandardMaterial({ roughness: 0.9, flatShading: true });
    const bark = new THREE.MeshStandardMaterial({ roughness: 1 });
    const flesh = new THREE.MeshStandardMaterial({ roughness: 0.75 });
    const shell = new THREE.MeshStandardMaterial({ roughness: 0.35, metalness: 0.15 });
    const eye = new THREE.MeshStandardMaterial({ roughness: 0.1, metalness: 0.4 });
    this.grass = new Pool(scene, quad, grassMat, 30000);
    this.grass2 = new Pool(scene, quad, grassMat, 30000);
    this.trunk = new Pool(scene, cyl, bark, 20000);
    this.limb = new Pool(scene, limb, bark, 24000);
    this.crown = new Pool(scene, crown, leaf, 48000);
    this.spire = new Pool(scene, spire, leaf, 20000);
    this.fruit = new Pool(scene, ball, leaf, 16000);
    this.carrion = new Pool(scene, box, flesh, 9000);
    this.standing = [this.grass, this.grass2, this.trunk, this.limb, this.crown, this.spire, this.fruit, this.carrion];
    // The bodies: one pool per kind of block, and one flat box for the ones far away.
    this.blockPools = [null, new Pool(scene, box, shell, 40000), new Pool(scene, box, flesh, 60000), new Pool(scene, ball, eye, 20000), new Pool(scene, box, flesh, 60000)];
    this.far = new Pool(scene, box, flesh, 8000);
    this.pools = [...this.standing, this.far, ...this.blockPools.filter(Boolean)];
    // The body being followed wears a ring, so it can be found again in a crowd. It is a mark,
    // not a thing in the world: it shows through the water and over a hill.
    // A pin that hangs over it, not a ring on the ground: at the angle the world is watched
    // from, a ring lies under the body itself. It shows through everything.
    const pin = new THREE.ConeGeometry(0.3, 0.62, 4);
    pin.rotateX(Math.PI);
    pin.translate(0, 0.31, 0);
    const markMat = new THREE.MeshBasicMaterial({ color: 0xffd24a, depthTest: false, depthWrite: false, fog: false, toneMapped: false });
    this.mark = new Pool(scene, pin, markMat, 2);
    this.mark.mesh.renderOrder = 999;
    this.treeMin = 1.0;
    this.bodyNear = 55;
    // The bodies drawn in full this frame, so a click can find the nearest one: three flat arrays
    // rather than an object each, because there are thousands of them every frame.
    this.drawnN = 0;
    this.drawnId = new Uint32Array(20000);
    this.drawnX = new Float32Array(20000);
    this.drawnZ = new Float32Array(20000);
    this.setDetail(1);
  }

  /** How much of a thing is drawn. The cost of the world is in what stands on it, so this is
   * the knob that buys frames back: how many parts a tree has, how many tufts a cell of lawn
   * has, and how far out either is drawn at all. */
  setDetail(n) {
    this.detail = Math.max(0, Math.min(2, n | 0));
    this.near = [24, 34, 46][this.detail]; // cells: the lawn, the fallen, a tree in full
    this.mid = [70, 90, 112][this.detail]; // cells: a tree at all
  }

  setVisible(what, on) {
    const map = { grass: [this.grass, this.grass2], trees: [this.trunk, this.limb, this.crown, this.spire], fruit: [this.fruit], carrion: [this.carrion], bodies: [...this.blockPools.filter(Boolean), this.far] };
    (map[what] || []).forEach((p) => (p.mesh.visible = on));
  }

  /** The shortest way from a to b on a torus of side n. */
  static wrap(d, n) {
    return d > n / 2 ? d - n : d < -n / 2 ? d + n : d;
  }

  /** Ease a fade, so a body holds its size at the ends of the interval and goes in the middle. */
  static ease(f) {
    return f * f * (3 - 2 * f);
  }

  /** Rebuild the plants and what has fallen. `v` is the layer values, `at` the eye's target,
   * `step` where in the year the world is (every cell has its own season: see `World.cellSun`). */
  plants(v, at, ground, step) {
    const { w, d } = this;
    const plant = v.plant, fruit = v.fruit, carrion = v.carrion;
    const swing = this.world.swing(step), amp = this.world.season.at;
    this.standing.forEach((p) => p.reset());
    const cx = Math.round(at.x), cz = Math.round(at.z);
    const mid2 = this.mid * this.mid, near2 = this.near * this.near, centreY = ground.centreY;
    for (let dz = -this.mid; dz <= this.mid; dz++) {
      const row = ((((cz + dz) % d) + d) % d) * w;
      const dz2 = dz * dz;
      for (let dx = -this.mid; dx <= this.mid; dx++) {
        const r2 = dx * dx + dz2;
        if (r2 > mid2) continue;
        const c = row + ((((cx + dx) % w) + w) % w);
        const p = plant ? plant[c] : 0;
        if (p <= 0.002 && (!fruit || fruit[c] <= 0) && (!carrion || carrion[c] <= 0)) continue;
        const px = cx + dx + 0.5, pz = cz + dz + 0.5; // drawn around the eye, not around the origin
        const y = centreY[c];
        const near = r2 <= near2;
        // This cell's own season: how much of its sun it is losing now, or gaining.
        const cold = Math.max(0, -amp[c] * swing), warm = Math.max(0, amp[c] * swing);
        if (p >= this.treeMin) this.tree(c, px, pz, y, p, cold, warm, near);
        else if (p > 0.002 && near) this.tuft(c, px, pz, y, p, cold, warm);
        if (near && fruit && fruit[c] > 0.001) this.fallen(c, px, pz, y, fruit[c]);
        if (near && carrion && carrion[c] > 0.002) this.dead(c, px, pz, y, carrion[c]);
      }
    }
    this.standing.forEach((p) => p.done());
  }

  /** One standing column, drawn as a tree.
   *
   * The world's arithmetic first: h matter standing on a cell stands h cells tall (the canopy's
   * own reading), and it stands on that one cell. So a tall column is a tall, narrow thing, and
   * the leaves are stacked up the trunk rather than balled on top of it - a crown wide enough to
   * look like a picture of a tree would cover its neighbours' cells and lie about the world.
   *
   * Everything else is the cell's own number, so a tree is the same tree every time it is drawn
   * and no two neighbours are alike: which of three kinds it is, where in its cell it stands, how
   * it leans, how dark its bark and its leaves are. The leaves come and go with that cell's
   * season, and a broadleaf stands bare in a winter a conifer sits through. */
  tree(c, px, pz, y, p, cold, warm, near) {
    const r0 = hash(c), r1 = rnd(c, 1), r2 = rnd(c, 2), r3 = rnd(c, 3), r4 = rnd(c, 4);
    const kind = r0 < 0.52 ? 0 : r0 < 0.76 ? 1 : 2; // broadleaf, conifer, spreading
    const hgt = Math.min(p, 40) * UP.plant;
    const x = px + (r1 - 0.5) * 0.68, z = pz + (r2 - 0.5) * 0.68; // anywhere in its cell
    const bark = BARK.copy(BARK0).lerp(BARK1, r3);
    const snow = Math.min(1, Math.max(0, (cold - 0.45) / 0.35));
    const shed = kind === 1 ? (cold - 0.7) / 0.9 : (cold - 0.3) / 0.42;
    const leaf = 1 - Math.min(1, Math.max(0, shed));
    LEAF.copy(LEAF0).lerp(LEAF1, r4);
    if (warm > 0) LEAF.lerp(LUSH, warm * 0.4);
    // The turn of the leaves, and then the loss of them. A conifer does neither: it only darkens
    // and takes the snow, which is what makes it the tree still standing green in a white world.
    if (cold > 0) LEAF.lerp(kind === 1 ? EVER : AMBER, Math.min(1, cold / 0.3) * (kind === 1 ? 0.55 : 0.8));
    if (snow > 0) LEAF.lerp(SNOW, snow * 0.3);
    const green = LEAF, dark = DARK.copy(LEAF).multiplyScalar(0.84);
    const tw = (0.05 + 0.045 * Math.sqrt(hgt)) * (kind === 2 ? 1.4 : 1);
    // The leafy part reaches the column's own height; the trunk is what carries it up to there.
    const wide = kind === 2;
    const crownH = hgt * (kind === 1 ? 0.78 : wide ? 0.62 : 0.5) * (0.55 + 0.45 * leaf);
    const trunkH = hgt - crownH;
    const cr = Math.min(0.4 + 0.045 * hgt, 0.6) * (wide ? 1.5 : 1) * (0.8 + r4 * 0.4) * (0.4 + 0.6 * leaf);
    const most = near ? (this.detail === 0 ? 2 : this.detail === 1 ? 6 : 9) : this.detail === 0 ? 2 : 3;
    if (kind === 1) {
      // A conifer: one stem the whole way up, with spires stacked on it, widest at the bottom.
      this.trunk.put(x, y, z, tw * 0.8, hgt, tw * 0.8, bark);
      const n = Math.max(2, Math.min(most, Math.round(crownH / (cr * 1.6))));
      for (let i = 0; i < n; i++) {
        const f = i / n;
        const rr = cr * (1 - f * 0.62);
        M.makeScale(rr, (crownH / n) * 1.9, rr);
        M.setPosition(x, y + trunkH + crownH * f, z);
        this.spire.putM(M, i % 2 ? dark : green);
      }
      return;
    }
    // A broadleaf carries its leaves high on one trunk; a spreading one is short, thick and wide.
    const lean = (r3 - 0.5) * (wide ? 0.1 : 0.18);
    this.trunk.put(x, y, z, tw, trunkH + crownH * 0.85, tw, bark);
    // The limbs hold the crown up, and are what is left to see when the leaves have gone.
    const limbs = this.detail > 0 && (near || leaf < 0.5) ? (wide ? 3 : 2) : 0;
    for (let i = 0; i < limbs; i++) {
      const a = (r4 + i / limbs) * 6.283, tilt = wide ? 0.8 : 0.45;
      const len = crownH * (wide ? 0.7 : 0.55) * (0.8 + rnd(c, 5 + i) * 0.4);
      M.makeRotationY(a);
      M.multiply(TURN.makeRotationX(tilt));
      M.scale(V.set(tw * 0.62, len, tw * 0.62));
      M.setPosition(x, y + trunkH + crownH * 0.2, z);
      this.limb.putM(M, bark);
    }
    if (leaf < 0.14) return; // bare: the trunk and its limbs are the whole tree now
    // The blobs go up the crown, enough of them that a tall column is leafy the whole way and
    // not a ball on a pole. Only so many are drawn, so when a column is taller than that many
    // blobs reach, each one is drawn taller rather than wider: the tree stays inside its cell,
    // which is where the world says its matter is.
    const n = Math.max(2, Math.min(most, Math.round(crownH / (cr * 1.05))));
    const rise = crownH / n;
    for (let i = 0; i < n; i++) {
      const f = n === 1 ? 0.5 : i / (n - 1);
      const a = rnd(c, 10 + i) * 6.283;
      const taper = wide ? 1 - f * 0.35 : 0.62 + 1.5 * f * (1 - f); // fattest in the middle
      const s = cr * taper * (0.72 + 0.4 * rnd(c, 40 + i));
      const rad = cr * 0.34 * rnd(c, 20 + i);
      const sy = Math.max(s * (wide ? 0.66 : 0.9 + rnd(c, 50 + i) * 0.3), rise * 0.8);
      M.makeScale(s, sy, s);
      M.setPosition(x + lean * f + Math.cos(a) * rad, y + trunkH + crownH * f, z + lean * f + Math.sin(a) * rad);
      this.crown.putM(M, i % 2 ? dark : green);
    }
  }

  /** The lawn on a cell: a few tufts, each somewhere of its own in the cell and turned its own
   * way, so that a field does not read as a grid. A tuft is two crossed sprites.
   *
   * A column of p matter stands p cells tall, which is nothing for a lawn; it is drawn a little
   * taller than that so it can be seen, and never above a body's back. */
  tuft(c, px, pz, y, p, cold, warm) {
    const n = this.detail + 1;
    const snow = Math.min(1, Math.max(0, (cold - 0.45) / 0.35));
    TINT.copy(DRY).lerp(FRESH, Math.min(1, p * 2.2)); // short and yellow grazed down, green standing
    if (warm > 0) TINT.lerp(LUSH, warm * 0.3);
    if (cold > 0) TINT.lerp(HAY, Math.min(0.9, cold * 1.2));
    if (snow > 0) TINT.lerp(SNOW, snow * 0.42);
    const hgt = (0.07 + Math.min(1, p) * 0.9) * UP.plant * 1.3 * (1 - snow * 0.5);
    const wide = 0.42 + 0.3 * Math.min(1, p);
    for (let i = 0; i < n; i++) {
      const jx = (rnd(c, 60 + i) - 0.5) * 0.78, jz = (rnd(c, 70 + i) - 0.5) * 0.78;
      const a = rnd(c, 80 + i) * 3.1416, sc = 0.72 + rnd(c, 90 + i) * 0.56;
      const hex = SPOT.copy(TINT).multiplyScalar(0.86 + rnd(c, 100 + i) * 0.28);
      for (const turn of [a, a + 1.5708]) {
        M.makeRotationY(turn);
        M.scale(V.set(wide * sc, hgt * sc, 1));
        M.setPosition(px + jx, y, pz + jz);
        (turn === a ? this.grass : this.grass2).putM(M, hex);
      }
    }
  }

  /** Fruit lying on a cell: a scatter of it, each one its own size and its own ripeness. */
  fallen(c, px, pz, y, q) {
    const n = Math.min(7, 1 + Math.floor(q * 3));
    for (let i = 0; i < n; i++) {
      const a = rnd(c, 110 + i) * 6.283, rr = 0.08 + rnd(c, 120 + i) * 0.4;
      const s = (0.05 + Math.min(0.06, q * 0.03)) * (0.7 + rnd(c, 130 + i) * 0.6);
      const hex = SPOT.copy(FR0).lerp(FR1, rnd(c, 140 + i));
      this.fruit.put(px + Math.cos(a) * rr, y + s * 0.85, pz + Math.sin(a) * rr, s, s * 0.88, s, hex);
    }
  }

  /** The dead lying on a cell: one to three lumps, each turned its own way. */
  dead(c, px, pz, y, q) {
    const n = Math.min(3, 1 + Math.floor(q * 1.5));
    for (let i = 0; i < n; i++) {
      const s = Math.min(0.5, 0.12 + q * 0.2) * (0.6 + rnd(c, 150 + i) * 0.6);
      const a = rnd(c, 160 + i) * 6.283, rr = i === 0 ? 0 : 0.16 + rnd(c, 170 + i) * 0.2;
      M.makeRotationY(rnd(c, 180 + i) * 6.283);
      M.scale(V.set(s, s * 0.45, s * 0.8));
      M.setPosition(px + Math.cos(a) * rr, y, pz + Math.sin(a) * rr);
      this.carrion.putM(M, SPOT.copy(CAR0).lerp(CAR1, rnd(c, 190 + i)));
    }
  }

  /** Rebuild the bodies from two frames and where between them we are.
   *
   * The world is only known every `stride` steps, and between two frames of a recording about a
   * quarter of the bodies are born or die (12% die and 15% are born in 50 steps of e041). Drawn
   * as they come, that is a quarter of the world blinking in and out at every frame - the one
   * thing the eye cannot ignore, and by far the largest change on the screen at a frame boundary.
   * So a body that dies inside the interval goes down to nothing over it, and one that is born
   * inside it comes up from nothing, and neither appears or vanishes whole. */
  bodies(world, a, b, t, at, ground, picked) {
    const pools = this.blockPools;
    pools.forEach((p) => p && p.reset());
    this.far.reset();
    this.drawnN = 0;
    this.mark.reset();
    if (!a) {
      pools.forEach((p) => p && p.done());
      this.far.done();
      this.mark.done();
      return;
    }
    const cell = 1 / world.sub, w = this.w, d = this.d;
    for (let i = 0; i < a.n; i++) {
      let x = a.a.x[i] * cell, z = a.a.y[i] * cell;
      let fade = 1;
      if (b) {
        const j = b.index.get(a.a.id[i]);
        if (j !== undefined) {
          x += Life.wrap(b.a.x[j] * cell - x, w) * t;
          z += Life.wrap(b.a.y[j] * cell - z, d) * t;
        } else {
          fade = Life.ease(1 - t); // it dies inside this interval
        }
      }
      this.body(world, a, i, x, z, fade, cell, at, ground, picked);
    }
    if (b && t > 0) {
      for (let j = 0; j < b.n; j++) {
        if (a.index.has(b.a.id[j])) continue; // it is born inside this interval
        this.body(world, b, j, b.a.x[j] * cell, b.a.y[j] * cell, Life.ease(t), cell, at, ground, picked);
      }
    }
    pools.forEach((p) => p && p.done());
    this.far.done();
    this.mark.done();
  }

  /** One body of frame `fr`, at `fade` of its size about its own middle: 1 while it is alive
   * across the whole interval, going to 0 as it dies and coming up from 0 as it is born. */
  body(world, fr, i, x, z, fade, cell, at, ground, picked) {
    const px = at.x + Life.wrap(x - at.x, this.w), pz = at.z + Life.wrap(z - at.z, this.d);
    const dx = px - at.x, dz = pz - at.z;
    const r2 = dx * dx + dz * dz;
    if (r2 > this.mid * this.mid) return;
    const shape = world.blocks(fr.a.body[i], fr.a.facing[i]);
    if (!shape) return;
    const y = ground.heightAt(x + 0.5, z + 0.5);
    const lit = picked === fr.a.id[i];
    const side = shape.side * cell;
    const mx = px + side / 2, mz = pz + side / 2; // the body's own middle: it shrinks towards this
    if (lit) {
      const bob = 0.09 * Math.sin(performance.now() / 320);
      this.mark.put(mx, y + 0.55 + side * 0.22 + bob, mz, 1, 1, 1, WARM);
    }
    if (r2 > this.bodyNear * this.bodyNear) {
      // Too far to make out its blocks: one low body, the colour of what it eats. It is seen
      // from above, so it goes out by its footprint and not by its height.
      const s = side * 0.45 * fade;
      this.far.put(mx, y, mz, s, 0.1, s, lit ? FARLIT : FAR[fr.a.diet[i]]);
      return;
    }
    if (fade > 0.5 && this.drawnN < this.drawnId.length) {
      this.drawnId[this.drawnN] = fr.a.id[i];
      this.drawnX[this.drawnN] = px;
      this.drawnZ[this.drawnN] = pz;
      this.drawnN++;
    }
    // The world is flat, so a body would be a pallet if every block were the same height.
    // It is given a back: the blocks stand tallest in the middle and fall away to the rim,
    // and a bigger body stands higher.
    const half = (shape.side - 1) / 2, span = half + 0.6;
    const grow = 0.62 + 0.05 * shape.side;
    const wide = cell * 0.98 * fade;
    for (const bl of shape.blocks) {
      const bx = mx + (px + (bl.c + 0.5) * cell - mx) * fade;
      const bz = mz + (pz + (bl.r + 0.5) * cell - mz) * fade;
      const k = bl.kind;
      const pool = pools_of(this, k);
      const dr = (bl.r - half) / span, dc = (bl.c - half) / span;
      const dome = 0.42 + 0.78 * Math.sqrt(Math.max(0, 1 - dr * dr - dc * dc));
      const base = k === 1 ? 0.42 : k === 2 ? 0.36 : k === 3 ? 0.3 : 0.3;
      const hgt = base * dome * grow * fade;
      let col = KIND[k] || KIND[4];
      if (lit) col = HI.copy(col).lerp(WARM, 0.55); // marked, but still readable
      if (k === 3) {
        // An eye sits on the body, round and dark.
        const eye = cell * 0.44 * fade;
        this.blockPools[4].put(bx, y, bz, wide, hgt * 0.8, wide, lit ? SOCKETLIT : SOCKET);
        pool.put(bx, y + hgt * 0.8 + cell * 0.2 * fade, bz, eye, eye, eye, col);
      } else {
        pool.put(bx, y, bz, wide, hgt, wide, col);
      }
    }
  }
}
