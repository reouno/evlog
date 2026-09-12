// The ground, the water and the sky: everything that is the place rather than what lives in it.
//
// One world cell is one unit. The world's y (south) is the scene's +z, the world's x (east) is
// +x, and up is +y. The terrain is drawn nine times, because the world is a torus and the
// watcher should not see its edge.

import * as THREE from 'three';
import type { World } from './world.js';
import type { Layers } from './wire.js';

export const UP = { terrain: 0.28, plant: 0.5 }; // soil units to world units, cells to world units

/** The shortest way from one place to another on a torus of side n. */
export function shortest(d: number, n: number): number {
  return d > n / 2 ? d - n : d < -n / 2 ? d + n : d;
}

/** Bilinear read of a per-cell field at a point in cell coordinates (wraps).
 * Called once per body every frame, so it wraps its indices by hand and allocates nothing. */
export function sample(field: ArrayLike<number>, w: number, d: number, x: number, z: number): number {
  const fx = x - 0.5, fz = z - 0.5;
  const x0 = Math.floor(fx), z0 = Math.floor(fz);
  const tx = fx - x0, tz = fz - z0;
  const c0 = ((x0 % w) + w) % w, c1 = (c0 + 1) % w;
  const z1 = ((z0 % d) + d) % d, r0 = z1 * w, r1 = ((z1 + 1) % d) * w;
  const a = field[r0 + c0], b = field[r0 + c1], c = field[r1 + c0], e = field[r1 + c1];
  return (a * (1 - tx) + b * tx) * (1 - tz) + (c * (1 - tx) + e * tx) * tz;
}

// The ground's palette, once, as the three numbers the vertex buffer wants: `Ground.update`
// runs over every vertex of the world and cannot afford a colour object per step.
const rgb = (hex: number): [number, number, number] => { const c = new THREE.Color(hex); return [c.r, c.g, c.b]; };
const SAND = rgb(0xa8926a), LOAM = rgb(0x4d3b26), DAMP = rgb(0x3a2f22);
const LAWN = rgb(0x7fa03a), STAND = rgb(0x24521f);
const LUSH = rgb(0x3f8a2c), STRAW = rgb(0xbda874); // high summer, deep winter
const ROT = rgb(0x6d4436), FALL = rgb(0xa8803f);
const FROST = rgb(0xb9bdb8), SNOW = rgb(0xe7edf3);
const SHALLOW = rgb(0x4e9ab0), DEEP = rgb(0x123f5c), ICE = rgb(0xd4e6ee);

export class Ground {
  world: World;
  w: number;
  d: number;
  geo: THREE.BufferGeometry;
  wgeo: THREE.BufferGeometry;
  tiles: THREE.Mesh[];
  water: THREE.Mesh[];
  terrainY: Float32Array; // the ground's height at every vertex, for everything else
  centreY: Float32Array; // and at every cell's centre, for what grows there

  constructor(scene: THREE.Scene, world: World) {
    this.world = world;
    const { w, d } = world;
    this.w = w;
    this.d = d;
    const nv = (w + 1) * (d + 1);
    const pos = new Float32Array(nv * 3), nor = new Float32Array(nv * 3), col = new Float32Array(nv * 3);
    const idx = new Uint32Array(w * d * 6);
    for (let j = 0; j <= d; j++) {
      for (let i = 0; i <= w; i++) {
        const v = j * (w + 1) + i;
        pos[v * 3] = i;
        pos[v * 3 + 2] = j;
      }
    }
    let k = 0;
    for (let j = 0; j < d; j++) {
      for (let i = 0; i < w; i++) {
        const a = j * (w + 1) + i, b = a + 1, c = a + w + 1, e = c + 1;
        idx[k++] = a; idx[k++] = c; idx[k++] = b;
        idx[k++] = b; idx[k++] = c; idx[k++] = e;
      }
    }
    const g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.BufferAttribute(pos, 3));
    g.setAttribute('normal', new THREE.BufferAttribute(nor, 3));
    g.setAttribute('color', new THREE.BufferAttribute(col, 3));
    g.setIndex(new THREE.BufferAttribute(idx, 1));
    this.geo = g;
    const mat = new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 0.96, metalness: 0 });
    this.tiles = [];
    for (let j = -1; j <= 1; j++) {
      for (let i = -1; i <= 1; i++) {
        const m = new THREE.Mesh(g, mat);
        m.position.set(i * w, 0, j * d);
        m.receiveShadow = true;
        m.frustumCulled = false; // nine tiles are the whole world; there is nothing to cull
        m.userData.tile = [i, j];
        scene.add(m);
        this.tiles.push(m);
      }
    }
    // The water lies on the same grid, and fades out where no water stands.
    const wpos = new Float32Array(nv * 3), wcol = new Float32Array(nv * 4);
    const wg = new THREE.BufferGeometry();
    wg.setAttribute('position', new THREE.BufferAttribute(wpos, 3));
    wg.setAttribute('color', new THREE.BufferAttribute(wcol, 4));
    wg.setIndex(new THREE.BufferAttribute(idx, 1));
    wg.setAttribute('normal', new THREE.BufferAttribute(new Float32Array(nv * 3), 3));
    for (let v = 0; v < nv; v++) {
      wpos[v * 3] = pos[v * 3];
      wpos[v * 3 + 2] = pos[v * 3 + 2];
      (wg.attributes.normal.array as Float32Array)[v * 3 + 1] = 1;
    }
    this.wgeo = wg;
    const wmat = new THREE.MeshStandardMaterial({ vertexColors: true, transparent: true, roughness: 0.15, metalness: 0.3, depthWrite: false });
    this.water = [];
    for (let j = -1; j <= 1; j++) {
      for (let i = -1; i <= 1; i++) {
        const m = new THREE.Mesh(wg, wmat);
        m.position.set(i * w, 0, j * d);
        m.renderOrder = 1;
        m.frustumCulled = false;
        scene.add(m);
        this.water.push(m);
      }
    }
    this.terrainY = new Float32Array(nv);
    this.centreY = new Float32Array(world.cells);
    this.buildHeight();
  }

  vertexHeight(i: number, j: number): number {
    const { w, d, height } = this.world;
    const at = (a: number, b: number) => height[(((b % d) + d) % d) * w + (((a % w) + w) % w)];
    return 0.25 * (at(i - 1, j - 1) + at(i, j - 1) + at(i - 1, j) + at(i, j));
  }

  buildHeight(): void {
    const { w, d } = this;
    const pos = this.geo.attributes.position.array as Float32Array;
    const nor = this.geo.attributes.normal.array as Float32Array;
    const s = UP.terrain;
    for (let j = 0; j <= d; j++) {
      for (let i = 0; i <= w; i++) {
        const v = j * (w + 1) + i;
        const y = this.vertexHeight(i, j) * s;
        pos[v * 3 + 1] = y;
        this.terrainY[v] = y;
      }
    }
    // Normals from the height field itself, so the nine tiles meet without a seam.
    for (let j = 0; j <= d; j++) {
      for (let i = 0; i <= w; i++) {
        const v = j * (w + 1) + i;
        const dx = (this.vertexHeight(i + 1, j) - this.vertexHeight(i - 1, j)) * s * 0.5;
        const dz = (this.vertexHeight(i, j + 1) - this.vertexHeight(i, j - 1)) * s * 0.5;
        const l = Math.hypot(dx, 1, dz);
        nor[v * 3] = -dx / l;
        nor[v * 3 + 1] = 1 / l;
        nor[v * 3 + 2] = -dz / l;
      }
    }
    // The height at each cell's own centre, which is where everything that grows on it stands.
    for (let c = 0; c < this.world.cells; c++) this.centreY[c] = this.world.height[c] * s;
    this.geo.attributes.position.needsUpdate = true;
    this.geo.attributes.normal.needsUpdate = true;
    this.geo.computeBoundingSphere();
  }

  /** The ground's height in world units at a point in cell coordinates. */
  heightAt(x: number, z: number): number {
    return sample(this.world.height, this.w, this.d, x, z) * UP.terrain;
  }

  /** Colour the ground and lay the water, from one set of layer values.
   *
   * This runs over every vertex of the world (16,641 of them at 128x128) whenever the layers or
   * the season move, so it is written in plain numbers: a `THREE.Color` here would be a hundred
   * thousand colour-space conversions and the frame it lands on would be dropped. */
  update(v: Layers, opts: { swing?: number }): void {
    const { w, d } = this;
    const col = this.geo.attributes.color.array as Float32Array;
    const wpos = this.wgeo.attributes.position.array as Float32Array;
    const wcol = this.wgeo.attributes.color.array as Float32Array;
    const plant = v.plant, soil = v.soil, water = v.water, carrion = v.carrion, fruit = v.fruit;
    const wet = this.world.wet, depth = this.world.depth * UP.terrain;
    // The season, cell by cell: under `winter high` the ridge is in winter while the valley is
    // not, so the ground says so place by place rather than by one number for the whole world.
    const swing = opts.swing || 0, amp = this.world.season.at;
    for (let j = 0; j <= d; j++) {
      const j0 = (((j - 1) % d) + d) % d * w, j1 = (j % d) * w;
      for (let i = 0; i <= w; i++) {
        const i0 = (((i - 1) % w) + w) % w, i1 = i % w;
        const v0 = j0 + i0, v1 = j0 + i1, v2 = j1 + i0, v3 = j1 + i1;
        const so = soil ? 0.25 * (soil[v0] + soil[v1] + soil[v2] + soil[v3]) : 0;
        const pl = plant ? 0.25 * (plant[v0] + plant[v1] + plant[v2] + plant[v3]) : 0;
        const wa = water ? 0.25 * (water[v0] + water[v1] + water[v2] + water[v3]) : 0;
        // How much of its sun this place loses now (cold) or gains (warm).
        const am = 0.25 * (amp[v0] + amp[v1] + amp[v2] + amp[v3]);
        const cold = am * swing < 0 ? -am * swing : 0, warm = am * swing > 0 ? am * swing : 0;
        // Bare ground: sand where the soil is thin, dark loam where it is deep.
        let r = SAND[0], g = SAND[1], b = SAND[2];
        let t = so > 8 ? 1 : so / 8;
        r += (LOAM[0] - r) * t; g += (LOAM[1] - g) * t; b += (LOAM[2] - b) * t;
        // Wet ground darkens before it holds a pool.
        if (wa > 0) {
          t = Math.min(0.5, wa / (wet * 2));
          r += (DAMP[0] - r) * t; g += (DAMP[1] - g) * t; b += (DAMP[2] - b) * t;
        }
        // What grows on it: a lawn is thin and yellowish, a stand of plants is deep green, and
        // the green leaves it for straw as its own winter comes on.
        if (pl > 0) {
          const k = pl > 4 ? 1 : pl / 4;
          let vr = LAWN[0] + (STAND[0] - LAWN[0]) * k, vg = LAWN[1] + (STAND[1] - LAWN[1]) * k, vb = LAWN[2] + (STAND[2] - LAWN[2]) * k;
          if (warm > 0) {
            const u = warm * 0.35;
            vr += (LUSH[0] - vr) * u; vg += (LUSH[1] - vg) * u; vb += (LUSH[2] - vb) * u;
          }
          if (cold > 0) {
            const u = Math.min(0.92, cold * 1.15);
            vr += (STRAW[0] - vr) * u; vg += (STRAW[1] - vg) * u; vb += (STRAW[2] - vb) * u;
          }
          const q = Math.min(1, Math.sqrt(pl / 1.2)) * 0.85;
          r += (vr - r) * q; g += (vg - g) * q; b += (vb - b) * q;
        }
        if (carrion) {
          t = Math.min(0.34, 0.25 * (carrion[v0] + carrion[v1] + carrion[v2] + carrion[v3]) * 0.32);
          if (t > 0) { r += (ROT[0] - r) * t; g += (ROT[1] - g) * t; b += (ROT[2] - b) * t; }
        }
        if (fruit) {
          t = Math.min(0.22, 0.25 * (fruit[v0] + fruit[v1] + fruit[v2] + fruit[v3]) * 0.28);
          if (t > 0) { r += (FALL[0] - r) * t; g += (FALL[1] - g) * t; b += (FALL[2] - b) * t; }
        }
        // The frost, then the snow: the ground pales as its sun goes, and goes white where the
        // sun has nearly gone out. Half a world can be under snow while the other half is green.
        if (cold > 0.12) {
          t = Math.min(0.4, (cold - 0.12) * 0.9);
          r += (FROST[0] - r) * t; g += (FROST[1] - g) * t; b += (FROST[2] - b) * t;
        }
        const snow = cold > 0.42 ? Math.min(1, (cold - 0.42) / 0.34) : 0;
        if (snow > 0) {
          t = snow * 0.84;
          r += (SNOW[0] - r) * t; g += (SNOW[1] - g) * t; b += (SNOW[2] - b) * t;
        }
        const vi = j * (w + 1) + i, c3 = vi * 3;
        col[c3] = r; col[c3 + 1] = g; col[c3 + 2] = b;
        // Standing water: what came down from above, above what the sky gives a cell alone.
        const pool = wa - wet;
        const dep = pool > 0 ? pool * depth : 0;
        wpos[c3 + 1] = this.terrainY[vi] + (dep > 0.02 ? dep : 0.02);
        const c4 = vi * 4;
        if (pool > 0) {
          t = Math.min(1, dep / 2.5);
          let r2 = SHALLOW[0] + (DEEP[0] - SHALLOW[0]) * t;
          let g2 = SHALLOW[1] + (DEEP[1] - SHALLOW[1]) * t;
          let b2 = SHALLOW[2] + (DEEP[2] - SHALLOW[2]) * t;
          if (snow > 0) { // a pool under the snow line reads as ice
            const u = snow * 0.8;
            r2 += (ICE[0] - r2) * u; g2 += (ICE[1] - g2) * u; b2 += (ICE[2] - b2) * u;
          }
          wcol[c4] = r2; wcol[c4 + 1] = g2; wcol[c4 + 2] = b2;
          wcol[c4 + 3] = Math.max(Math.min(0.9, dep / (0.35 + dep) + 0.25), snow * 0.75);
        } else {
          wcol[c4 + 3] = 0;
        }
      }
    }
    this.geo.attributes.color.needsUpdate = true;
    this.wgeo.attributes.position.needsUpdate = true;
    this.wgeo.attributes.color.needsUpdate = true;
  }
}

/** What the sky is told: where the sun is, and the colours it is painted from. */
export interface SkyUniforms {
  uSun: { value: THREE.Vector3 };
  uTop: { value: THREE.Color };
  uHorizon: { value: THREE.Color };
  uGround: { value: THREE.Color };
  uSunColor: { value: THREE.Color };
  [name: string]: { value: unknown };
}

/** The sky: a dome that goes from the horizon's haze to the zenith, with the sun in it. */
export class Sky {
  uniforms: SkyUniforms;
  mesh: THREE.Mesh;

  constructor(scene: THREE.Scene) {
    const g = new THREE.SphereGeometry(1, 32, 16);
    this.uniforms = {
      uSun: { value: new THREE.Vector3(0.3, 0.6, 0.4) },
      uTop: { value: new THREE.Color(0x2f6ab0) },
      uHorizon: { value: new THREE.Color(0xc8d7e2) },
      uGround: { value: new THREE.Color(0x6a6f63) },
      uSunColor: { value: new THREE.Color(0xfff0c8) },
    };
    const m = new THREE.ShaderMaterial({
      uniforms: this.uniforms,
      side: THREE.BackSide,
      depthWrite: false,
      depthTest: false,
      fog: false,
      vertexShader: `varying vec3 vWorld; void main(){ vec4 wp = modelMatrix * vec4(position, 1.0); vWorld = wp.xyz; gl_Position = projectionMatrix * viewMatrix * wp; }`,
      fragmentShader: `
        varying vec3 vWorld; uniform vec3 uSun, uTop, uHorizon, uGround, uSunColor;
        void main(){
          vec3 dir = normalize(vWorld - cameraPosition);
          float h = dir.y;
          vec3 c = mix(uHorizon, uTop, pow(clamp(h,0.0,1.0), 0.55));
          c = mix(c, uGround, clamp(-h*4.0, 0.0, 1.0));
          float s = max(dot(dir, normalize(uSun)), 0.0);
          c += uSunColor * (pow(s, 900.0) * 1.6 + pow(s, 24.0) * 0.28 + pow(s, 4.0) * 0.06);
          gl_FragColor = vec4(c, 1.0);
          #include <tonemapping_fragment>
          #include <colorspace_fragment>
        }`,
    });
    this.mesh = new THREE.Mesh(g, m);
    this.mesh.scale.setScalar(1500);
    this.mesh.renderOrder = -1;
    this.mesh.frustumCulled = false;
    scene.add(this.mesh);
  }
  follow(camera: THREE.Camera): void {
    this.mesh.position.copy(camera.position);
  }
}

/** The god's eye: it turns around a point on the ground, and the point moves where you want. */
export class Rig {
  cam: THREE.PerspectiveCamera;
  world: World;
  target: THREE.Vector3; // the point the eye is on now
  aim: THREE.Vector3; // and the one it is being sent to: the two part only while it slides
  slid: number;
  offX: number;
  offZ: number;
  sending: boolean;
  dist: number;
  yaw: number;
  pitch: number;
  follow: number | null;
  want: number | null;
  keys: Set<string>;

  static SLIDE = 0.25; // seconds to cover the gap left by a change of what is watched
  static LEAP = 8; // cells: farther than this the eye cuts, because sliding would be a whip

  constructor(camera: THREE.PerspectiveCamera, dom: HTMLElement, world: World) {
    this.cam = camera;
    this.world = world;
    this.target = new THREE.Vector3(world.w / 2, 0, world.d / 2);
    this.aim = this.target.clone();
    this.slid = 1; // 0 while a slide is on its way, 1 when the eye is on its aim again
    this.offX = 0;
    this.offZ = 0;
    this.sending = false;
    this.dist = 60;
    this.yaw = Math.PI * 0.25;
    this.pitch = 0.55;
    this.follow = null;
    this.want = null; // a distance the eye is on its way to: a picked body is brought close, not jumped to
    this.keys = new Set();
    let drag: { x: number; y: number; pan: boolean } | null = null;
    dom.addEventListener('pointerdown', (e) => {
      if (e.button === 1 || (e.target as HTMLElement).closest('.ui')) return;
      drag = { x: e.clientX, y: e.clientY, pan: e.button === 2 || e.shiftKey };
      dom.setPointerCapture(e.pointerId);
    });
    dom.addEventListener('pointermove', (e) => {
      if (!drag) return;
      const dx = e.clientX - drag.x, dy = e.clientY - drag.y;
      drag.x = e.clientX; drag.y = e.clientY;
      if (drag.pan) this.pan(-dx * this.dist * 0.0016, dy * this.dist * 0.0016); // the ground follows the hand
      else {
        // Turning goes around the point being watched, so it keeps a followed body; moving the
        // point (`pan`) lets it go.
        this.yaw -= dx * 0.005;
        this.pitch = Math.max(0.06, Math.min(1.52, this.pitch + dy * 0.005));
      }
    });
    const stop = (e: PointerEvent) => { if (drag) { dom.releasePointerCapture(e.pointerId); drag = null; } };
    dom.addEventListener('pointerup', stop);
    dom.addEventListener('pointercancel', stop);
    dom.addEventListener('contextmenu', (e) => e.preventDefault());
    dom.addEventListener('wheel', (e) => {
      e.preventDefault();
      this.want = null;
      this.dist = Math.max(1.2, Math.min(420, this.dist * Math.exp(e.deltaY * 0.0012)));
    }, { passive: false });
    addEventListener('keydown', (e) => {
      if ((e.target as HTMLElement).tagName === 'INPUT') return;
      this.keys.add(e.key.toLowerCase());
    });
    addEventListener('keyup', (e) => this.keys.delete(e.key.toLowerCase()));
  }
  /** Move the point being watched: `right` is the screen's right, `forward` is into the view. */
  pan(right: number, forward: number): void {
    const s = Math.sin(this.yaw), c = Math.cos(this.yaw);
    this.aim.x += forward * s - right * c;
    this.aim.z += forward * c + right * s;
    this.follow = null;
  }
  /** Send the eye to a point. While a body is being followed this is every frame, and the point
   * is that body's, so the eye goes where it goes. */
  goTo(x: number, z: number): void {
    if (this.sending) {
      this.sending = false;
      // What the eye would have had to cut across. It keeps that gap and gives it up over the
      // next quarter second, so the change is a move rather than a cut. Too far to be a move at
      // all (a body picked across the world) and it cuts, as before.
      const dx = shortest(this.target.x - x, this.world.w), dz = shortest(this.target.z - z, this.world.d);
      const near = Math.hypot(dx, dz) <= Rig.LEAP;
      this.offX = near ? dx : 0;
      this.offZ = near ? dz : 0;
      this.slid = near ? 0 : 1;
    }
    this.aim.x = x;
    this.aim.z = z;
  }
  /** The next point the eye is sent to is a different thing to watch, not the same thing moved.
   *
   * Following a line of descent, the eye changes body every few hundred steps, and a body's
   * child is a cell or two away: the watcher sees the whole world jump sideways. Nothing else in
   * the picture is as hard to look away from as that, so the eye slides instead. */
  send(): void {
    this.sending = true;
  }
  update(dt: number, ground: Ground): void {
    const k = this.keys;
    const v = (k.has('shift') ? 3 : 1) * dt * Math.max(6, this.dist * 0.9);
    if (k.has('w') || k.has('arrowup')) this.pan(0, v);
    if (k.has('s') || k.has('arrowdown')) this.pan(0, -v);
    if (k.has('a') || k.has('arrowleft')) this.pan(-v, 0);
    if (k.has('d') || k.has('arrowright')) this.pan(v, 0);
    if (k.has('q') || k.has('e')) this.want = null;
    if (k.has('q')) this.dist = Math.max(1.2, this.dist * (1 - dt));
    if (k.has('e')) this.dist = Math.min(420, this.dist * (1 + dt));
    if (this.want !== null) {
      this.dist += (this.want - this.dist) * Math.min(1, dt * 3);
      if (Math.abs(this.want - this.dist) < 0.05) this.want = null;
    }
    if (this.slid < 1) {
      this.slid = Math.min(1, this.slid + dt / Rig.SLIDE);
      if (this.slid === 1) this.offX = this.offZ = 0;
    }
    const { w, d } = this.world;
    this.aim.x = ((this.aim.x % w) + w) % w;
    this.aim.z = ((this.aim.z % d) + d) % d;
    // Still at both ends of the slide: the eye takes up the gap and gives it back without a jerk
    // on to it or off it, and what it is watching keeps moving underneath the whole way.
    const hold = 1 - this.slid * this.slid * (3 - 2 * this.slid);
    this.target.x = (((this.aim.x + this.offX * hold) % w) + w) % w;
    this.target.z = (((this.aim.z + this.offZ * hold) % d) + d) % d;
    this.target.y = ground.heightAt(this.target.x, this.target.z);
    const cp = Math.cos(this.pitch);
    this.cam.position.set(
      this.target.x - Math.sin(this.yaw) * cp * this.dist,
      this.target.y + Math.sin(this.pitch) * this.dist,
      this.target.z - Math.cos(this.yaw) * cp * this.dist,
    );
    this.cam.lookAt(this.target);
  }
}
