// What lives on the ground: the plants that stand on a cell, what has fallen on it, and the
// bodies. Everything is instanced, and only what is near the eye is drawn in full.

import * as THREE from 'three';
import { UP, sample } from './render.js';

const M = new THREE.Matrix4();
const COL = new THREE.Color();

/** A pool of one shape, drawn many times. */
class Pool {
  constructor(scene, geo, mat, cap) {
    this.mesh = new THREE.InstancedMesh(geo, mat, cap);
    this.mesh.instanceMatrix.setUsage(THREE.DynamicDrawUsage);
    this.mesh.frustumCulled = false;
    this.mesh.count = 0;
    this.cap = cap;
    scene.add(this.mesh);
  }
  reset() {
    this.n = 0;
  }
  /** An axis-aligned box or sprite: position, size, colour. No rotation, so the matrix is written by hand. */
  put(x, y, z, sx, sy, sz, hex) {
    if (this.n >= this.cap) return;
    const a = this.mesh.instanceMatrix.array, o = this.n * 16;
    a[o] = sx; a[o + 1] = 0; a[o + 2] = 0; a[o + 3] = 0;
    a[o + 4] = 0; a[o + 5] = sy; a[o + 6] = 0; a[o + 7] = 0;
    a[o + 8] = 0; a[o + 9] = 0; a[o + 10] = sz; a[o + 11] = 0;
    a[o + 12] = x; a[o + 13] = y; a[o + 14] = z; a[o + 15] = 1;
    if (hex !== undefined) {
      COL.setHex(hex);
      this.mesh.setColorAt(this.n, COL);
    }
    this.n++;
  }
  putM(m, hex) {
    if (this.n >= this.cap) return;
    m.toArray(this.mesh.instanceMatrix.array, this.n * 16);
    if (hex !== undefined) {
      COL.setHex(hex);
      this.mesh.setColorAt(this.n, COL);
    }
    this.n++;
  }
  done() {
    this.mesh.count = this.n;
    this.mesh.instanceMatrix.needsUpdate = true;
    if (this.mesh.instanceColor) this.mesh.instanceColor.needsUpdate = true;
  }
}

function grassTexture() {
  const c = document.createElement('canvas');
  c.width = c.height = 64;
  const g = c.getContext('2d');
  g.clearRect(0, 0, 64, 64);
  for (let i = 0; i < 14; i++) {
    const x = 6 + Math.random() * 52, h = 26 + Math.random() * 34, wdt = 1.6 + Math.random() * 2.2;
    const bend = (Math.random() - 0.5) * 22;
    const shade = 120 + Math.random() * 70;
    g.beginPath();
    g.moveTo(x - wdt, 64);
    g.quadraticCurveTo(x - wdt * 0.4 + bend * 0.5, 64 - h * 0.6, x + bend, 64 - h);
    g.quadraticCurveTo(x + wdt * 0.4 + bend * 0.5, 64 - h * 0.6, x + wdt, 64);
    g.closePath();
    g.fillStyle = `rgb(${(shade * 0.55) | 0},${shade | 0},${(shade * 0.4) | 0})`;
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

export class Life {
  constructor(scene, world) {
    this.world = world;
    this.w = world.w;
    this.d = world.d;
    const box = new THREE.BoxGeometry(1, 1, 1);
    box.translate(0, 0.5, 0);
    const cyl = new THREE.CylinderGeometry(1, 1.25, 1, 6);
    cyl.translate(0, 0.5, 0);
    const crown = new THREE.IcosahedronGeometry(1, 1);
    const ball = new THREE.SphereGeometry(1, 8, 6);
    const quad = new THREE.PlaneGeometry(1, 1);
    quad.translate(0, 0.5, 0);
    const grassMat = new THREE.MeshStandardMaterial({ map: grassTexture(), transparent: true, alphaTest: 0.35, side: THREE.DoubleSide, roughness: 1 });
    const leaf = new THREE.MeshStandardMaterial({ roughness: 0.9, flatShading: true });
    const bark = new THREE.MeshStandardMaterial({ roughness: 1 });
    const flesh = new THREE.MeshStandardMaterial({ roughness: 0.75 });
    const shell = new THREE.MeshStandardMaterial({ roughness: 0.35, metalness: 0.15 });
    const eye = new THREE.MeshStandardMaterial({ roughness: 0.1, metalness: 0.4 });
    this.grass = new Pool(scene, quad, grassMat, 24000);
    this.grass2 = new Pool(scene, quad, grassMat, 24000);
    this.trunk = new Pool(scene, cyl, bark, 12000);
    this.crown = new Pool(scene, crown, leaf, 24000);
    this.fruit = new Pool(scene, ball, leaf, 12000);
    this.carrion = new Pool(scene, box, flesh, 6000);
    // The bodies: one pool per kind of block, and one flat box for the ones far away.
    this.blockPools = [null, new Pool(scene, box, shell, 40000), new Pool(scene, box, flesh, 60000), new Pool(scene, ball, eye, 20000), new Pool(scene, box, flesh, 60000)];
    this.far = new Pool(scene, box, flesh, 8000);
    this.pools = [this.grass, this.grass2, this.trunk, this.crown, this.fruit, this.carrion, this.far, ...this.blockPools.filter(Boolean)];
    this.treeMin = 1.0;
    this.near = 34;   // cells: grass and fruit
    this.mid = 90;    // cells: trees
    this.bodyNear = 55;
  }

  setVisible(what, on) {
    const map = { grass: [this.grass, this.grass2], trees: [this.trunk, this.crown], fruit: [this.fruit], carrion: [this.carrion], bodies: [...this.blockPools.filter(Boolean), this.far] };
    (map[what] || []).forEach((p) => (p.mesh.visible = on));
  }

  /** The shortest way from a to b on a torus of side n. */
  static wrap(d, n) {
    return d > n / 2 ? d - n : d < -n / 2 ? d + n : d;
  }

  /** Rebuild the plants and what has fallen. `v` is the layer values, `at` the eye's target. */
  plants(v, at, ground, season) {
    const { w, d } = this;
    const plant = v.plant, fruit = v.fruit, carrion = v.carrion;
    [this.grass, this.grass2, this.trunk, this.crown, this.fruit, this.carrion].forEach((p) => p.reset());
    const cx = Math.round(at.x), cz = Math.round(at.z);
    const winter = Math.max(0, 1 - season);
    for (let dz = -this.mid; dz <= this.mid; dz++) {
      for (let dx = -this.mid; dx <= this.mid; dx++) {
        const r2 = dx * dx + dz * dz;
        if (r2 > this.mid * this.mid) continue;
        const gx = ((cx + dx) % w + w) % w, gz = ((cz + dz) % d + d) % d;
        const c = gz * w + gx;
        const px = cx + dx + 0.5, pz = cz + dz + 0.5; // drawn around the eye, not around the origin
        const p = plant ? plant[c] : 0;
        if (p <= 0.002 && (!fruit || fruit[c] <= 0) && (!carrion || carrion[c] <= 0)) continue;
        const y = ground.heightAt(gx + 0.5, gz + 0.5);
        const near = r2 <= this.near * this.near;
        if (p >= this.treeMin) {
          // A column of h matter stands h cells tall (the canopy's own reading).
          const hgt = Math.min(p, 40) * UP.plant;
          const r = hash(c);
          const tw = 0.05 + 0.035 * Math.sqrt(hgt);
          const lean = (r - 0.5) * 0.12;
          this.trunk.put(px + lean, y, pz + lean, tw, hgt * 0.72, tw, 0x6a4a30);
          const cr = 0.24 + 0.07 * hgt + r * 0.08;
          const green = new THREE.Color(0x2f6d33).lerp(new THREE.Color(0x1c4a24), r).lerp(new THREE.Color(0x7a6b33), winter * 0.7);
          // Two blobs make a crown that is not a mushroom cap.
          M.makeScale(cr, cr * (0.85 + r * 0.4), cr);
          M.setPosition(px + lean * 2, y + hgt * 0.78, pz + lean * 2);
          this.crown.putM(M, green.getHex());
          M.makeScale(cr * 0.78, cr * 0.7, cr * 0.78);
          M.setPosition(px + lean * 2 + cr * 0.5 * (r - 0.5), y + hgt * 0.56, pz + lean * 2 - cr * 0.4 * (r - 0.5));
          this.crown.putM(M, green.clone().multiplyScalar(0.86).getHex());
        } else if (p > 0.002 && near) {
          const r = hash(c);
          // A column of p matter stands p cells tall, which is nothing for a lawn; it is drawn
          // a little taller than that so it can be seen, and never above a body's back.
          const hgt = (0.07 + Math.min(1, p) * 0.9) * UP.plant * 1.3;
          const wdt = 0.42 + 0.3 * Math.min(1, p);
          const jx = (r - 0.5) * 0.3, jz = (hash(c + 7777) - 0.5) * 0.3;
          // Short and yellow when it is grazed down, tall and green when it stands.
          const tint = new THREE.Color(0xe8e0b4).lerp(new THREE.Color(0xa8d089), Math.min(1, p * 2.2)).lerp(new THREE.Color(0xd9c98d), winter * 0.6).getHex();
          this.grass.put(px + jx, y, pz + jz, wdt, hgt, 1, tint);
          M.makeRotationY(Math.PI / 2);
          M.scale(new THREE.Vector3(wdt, hgt, 1));
          M.setPosition(px + jx, y, pz + jz);
        this.grass2.putM(M, tint);
        }
        if (near && fruit && fruit[c] > 0.001) {
          const n = Math.min(6, 1 + Math.floor(fruit[c] * 3));
          for (let i = 0; i < n; i++) {
            const a = hash(c + i * 131) * 6.283, rr = 0.12 + hash(c + i * 977) * 0.34;
            const s = 0.05 + Math.min(0.06, fruit[c] * 0.03);
            this.fruit.put(px + Math.cos(a) * rr, y + s, pz + Math.sin(a) * rr, s, s, s, 0xc06a2a);
          }
        }
        if (near && carrion && carrion[c] > 0.002) {
          const s = Math.min(0.5, 0.12 + carrion[c] * 0.2);
          this.carrion.put(px, y, pz, s, s * 0.45, s * 0.8, 0x6d3a2c);
        }
      }
    }
    [this.grass, this.grass2, this.trunk, this.crown, this.fruit, this.carrion].forEach((p) => p.done());
  }

  /** Rebuild the bodies from two frames and where between them we are. */
  bodies(world, a, b, t, at, ground, picked) {
    const pools = this.blockPools;
    pools.forEach((p) => p && p.reset());
    this.far.reset();
    this.drawn = [];
    if (!a) {
      pools.forEach((p) => p && p.done());
      this.far.done();
      return;
    }
    const sub = world.sub, w = this.w, d = this.d;
    const cell = 1 / sub;
    const kinds = [0, 0x2a2622, 0xa8553c, 0x1b1b20, 0xcbb98a]; // hard, muscle, sensor, digestive
    const diet = [0x9ecf6a, 0xd9a441, 0xc4553f, 0x9aa0a6];
    for (let i = 0; i < a.n; i++) {
      let x = a.a.x[i] * cell, z = a.a.y[i] * cell;
      if (b) {
        const j = b.index.get(a.a.id[i]);
        if (j !== undefined) {
          x += Life.wrap(b.a.x[j] * cell - x, w) * t;
          z += Life.wrap(b.a.y[j] * cell - z, d) * t;
        }
      }
      // Draw it near the eye's own copy of the world.
      const px = at.x + Life.wrap(x - at.x, w), pz = at.z + Life.wrap(z - at.z, d);
      const dx = px - at.x, dz = pz - at.z;
      const r2 = dx * dx + dz * dz;
      if (r2 > this.mid * this.mid) continue;
      const shape = world.blocks(a.a.body[i], a.a.facing[i]);
      if (!shape) continue;
      const y = ground.heightAt(x + 0.5, z + 0.5);
      const id = a.a.id[i];
      const lit = picked === id;
      if (r2 > this.bodyNear * this.bodyNear) {
        // Too far to make out its blocks: one low body, the colour of what it eats.
        const s = shape.side * cell;
        const c = new THREE.Color(lit ? 0xffffff : diet[a.a.diet[i]]).multiplyScalar(0.5);
        this.far.put(px + s / 2, y, pz + s / 2, s * 0.45, 0.1, s * 0.45, c.getHex());
        continue;
      }
      this.drawn.push({ id, x: px, z: pz, y, i });
      // The world is flat, so a body would be a pallet if every block were the same height.
      // It is given a back: the blocks stand tallest in the middle and fall away to the rim,
      // and a bigger body stands higher.
      const half = (shape.side - 1) / 2, span = half + 0.6;
      const grow = 0.62 + 0.05 * shape.side;
      for (const bl of shape.blocks) {
        const bx = px + (bl.c + 0.5) * cell, bz = pz + (bl.r + 0.5) * cell;
        const k = bl.kind;
        const pool = pools[k] || pools[4];
        const dr = (bl.r - half) / span, dc = (bl.c - half) / span;
        const dome = 0.42 + 0.78 * Math.sqrt(Math.max(0, 1 - dr * dr - dc * dc));
        const base = k === 1 ? 0.42 : k === 2 ? 0.36 : k === 3 ? 0.3 : 0.3;
        const hgt = base * dome * grow;
        let hex = kinds[k] ?? 0xcbb98a;
        if (lit) hex = 0xffe9a8;
        if (k === 3) {
          // An eye sits on the body, round and dark.
          this.blockPools[4].put(bx, y, bz, cell, hgt * 0.8, cell, lit ? 0xffe9a8 : 0x8f7f5e);
          pool.put(bx, y + hgt * 0.8 + cell * 0.2, bz, cell * 0.44, cell * 0.44, cell * 0.44, hex);
        } else {
          pool.put(bx, y, bz, cell * 0.98, hgt, cell * 0.98, hex);
        }
      }
    }
    pools.forEach((p) => p && p.done());
    this.far.done();
  }
}
