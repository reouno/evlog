// The ground, the water and the sky: everything that is the place rather than what lives in it.
//
// One world cell is one unit. The world's y (south) is the scene's +z, the world's x (east) is
// +x, and up is +y. The terrain is drawn nine times, because the world is a torus and the
// watcher should not see its edge.

import * as THREE from 'three';

export const UP = { terrain: 0.28, plant: 0.5 }; // soil units to world units, cells to world units

/** Bilinear read of a per-cell field at a point in cell coordinates (wraps). */
export function sample(field, w, d, x, z) {
  const fx = x - 0.5, fz = z - 0.5;
  const x0 = Math.floor(fx), z0 = Math.floor(fz);
  const tx = fx - x0, tz = fz - z0;
  const i = (a, b) => ((b % d) + d) % d * w + (((a % w) + w) % w);
  const a = field[i(x0, z0)], b = field[i(x0 + 1, z0)], c = field[i(x0, z0 + 1)], e = field[i(x0 + 1, z0 + 1)];
  return (a * (1 - tx) + b * tx) * (1 - tz) + (c * (1 - tx) + e * tx) * tz;
}

const C = new THREE.Color();
function mix(out, hex, t) {
  C.setHex(hex);
  out.lerp(C, t);
  return out;
}

export class Ground {
  constructor(scene, world) {
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
      wg.attributes.normal.array[v * 3 + 1] = 1;
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
    this.terrainY = new Float32Array(nv); // the ground's height at every vertex, for everything else
    this.buildHeight();
  }

  vertexHeight(i, j) {
    const { w, d, height } = this.world;
    const at = (a, b) => height[(((b % d) + d) % d) * w + (((a % w) + w) % w)];
    return 0.25 * (at(i - 1, j - 1) + at(i, j - 1) + at(i - 1, j) + at(i, j));
  }

  buildHeight() {
    const { w, d } = this;
    const pos = this.geo.attributes.position.array;
    const nor = this.geo.attributes.normal.array;
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
    this.geo.attributes.position.needsUpdate = true;
    this.geo.attributes.normal.needsUpdate = true;
    this.geo.computeBoundingSphere();
  }

  /** The ground's height in world units at a point in cell coordinates. */
  heightAt(x, z) {
    return sample(this.world.height, this.w, this.d, x, z) * UP.terrain;
  }

  /** Colour the ground and lay the water, from one set of layer values. */
  update(v, opts) {
    const { w, d } = this;
    const col = this.geo.attributes.color.array;
    const wpos = this.wgeo.attributes.position.array;
    const wcol = this.wgeo.attributes.color.array;
    const plant = v.plant, soil = v.soil, water = v.water, carrion = v.carrion, fruit = v.fruit;
    const wet = this.world.wet, depth = this.world.depth * UP.terrain;
    const winter = Math.max(0, 1 - (opts.sun ?? 1));
    const relief = this.world.relief || 1;
    const at = (i, j) => (((j % d) + d) % d) * w + (((i % w) + w) % w);
    const c = new THREE.Color();
    for (let j = 0; j <= d; j++) {
      for (let i = 0; i <= w; i++) {
        const v0 = at(i - 1, j - 1), v1 = at(i, j - 1), v2 = at(i - 1, j), v3 = at(i, j);
        const q = (f) => 0.25 * (f[v0] + f[v1] + f[v2] + f[v3]);
        const so = soil ? q(soil) : 0;
        const pl = plant ? q(plant) : 0;
        const wa = water ? q(water) : 0;
        // Bare ground: sand where the soil is thin, dark loam where it is deep.
        c.setHex(0xa8926a);
        mix(c, 0x4d3b26, Math.min(1, so / 8));
        // Wet ground darkens before it holds a pool.
        if (wa > 0) mix(c, 0x3a2f22, Math.min(0.5, wa / (wet * 2)));
        // What grows on it: a lawn is thin and yellowish, a stand of plants is deep green.
        if (pl > 0) {
          const g = Math.min(1, Math.sqrt(pl / 1.2));
          c.lerp(new THREE.Color(0x7fa03a).lerp(new THREE.Color(0x24521f), Math.min(1, pl / 4)), g * 0.85);
        }
        if (carrion) mix(c, 0x6b3a2e, Math.min(0.6, q(carrion) * 0.5));
        if (fruit) mix(c, 0xb8703a, Math.min(0.35, q(fruit) * 0.4));
        // Winter whitens the high ground first (the season is by height in this world).
        const hi = this.terrainY[j * (w + 1) + i] / (relief * UP.terrain);
        const snow = Math.max(0, Math.min(1, (winter * 2.2 - 0.35) * 3 * Math.max(0, hi - 0.35)));
        if (snow > 0) mix(c, 0xf2f4f6, snow * 0.9);
        const vi = j * (w + 1) + i;
        col[vi * 3] = c.r; col[vi * 3 + 1] = c.g; col[vi * 3 + 2] = c.b;
        // Standing water: what came down from above, above what the sky gives a cell alone.
        const pool = Math.max(0, wa - wet);
        const dep = pool * depth;
        wpos[vi * 3 + 1] = this.terrainY[vi] + Math.max(dep, 0.02);
        const alpha = Math.min(0.86, dep / (0.6 + dep) + (pool > 0 ? 0.15 : 0));
        c.setHex(0x2a6f8f).lerp(new THREE.Color(0x0d3550), Math.min(1, dep / 3));
        wcol[vi * 4] = c.r; wcol[vi * 4 + 1] = c.g; wcol[vi * 4 + 2] = c.b;
        wcol[vi * 4 + 3] = pool > 0 ? alpha : 0;
      }
    }
    this.geo.attributes.color.needsUpdate = true;
    this.wgeo.attributes.position.needsUpdate = true;
    this.wgeo.attributes.color.needsUpdate = true;
  }
}

/** The sky: a dome that goes from the horizon's haze to the zenith, with the sun in it. */
export class Sky {
  constructor(scene) {
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
  follow(camera) {
    this.mesh.position.copy(camera.position);
  }
}

/** The god's eye: it turns around a point on the ground, and the point moves where you want. */
export class Rig {
  constructor(camera, dom, world) {
    this.cam = camera;
    this.world = world;
    this.target = new THREE.Vector3(world.w / 2, 0, world.d / 2);
    this.dist = 60;
    this.yaw = Math.PI * 0.25;
    this.pitch = 0.55;
    this.follow = null;
    this.keys = new Set();
    let drag = null;
    dom.addEventListener('pointerdown', (e) => {
      if (e.button === 1 || e.target.closest('.ui')) return;
      drag = { x: e.clientX, y: e.clientY, pan: e.button === 2 || e.shiftKey };
      dom.setPointerCapture(e.pointerId);
    });
    dom.addEventListener('pointermove', (e) => {
      if (!drag) return;
      const dx = e.clientX - drag.x, dy = e.clientY - drag.y;
      drag.x = e.clientX; drag.y = e.clientY;
      if (drag.pan) this.pan(-dx * this.dist * 0.0016, -dy * this.dist * 0.0016);
      else {
        this.yaw -= dx * 0.005;
        this.pitch = Math.max(0.06, Math.min(1.52, this.pitch + dy * 0.005));
        this.follow = null;
      }
    });
    const stop = (e) => { if (drag) { dom.releasePointerCapture(e.pointerId); drag = null; } };
    dom.addEventListener('pointerup', stop);
    dom.addEventListener('pointercancel', stop);
    dom.addEventListener('contextmenu', (e) => e.preventDefault());
    dom.addEventListener('wheel', (e) => {
      e.preventDefault();
      this.dist = Math.max(1.2, Math.min(420, this.dist * Math.exp(e.deltaY * 0.0012)));
    }, { passive: false });
    addEventListener('keydown', (e) => {
      if (e.target.tagName === 'INPUT') return;
      this.keys.add(e.key.toLowerCase());
    });
    addEventListener('keyup', (e) => this.keys.delete(e.key.toLowerCase()));
  }
  pan(dx, dz) {
    const s = Math.sin(this.yaw), c = Math.cos(this.yaw);
    this.target.x += dx * c - dz * s;
    this.target.z += dx * s + dz * c;
    this.follow = null;
  }
  goTo(x, z) {
    this.target.x = x;
    this.target.z = z;
  }
  update(dt, ground) {
    const k = this.keys;
    const v = (k.has('shift') ? 3 : 1) * dt * Math.max(6, this.dist * 0.9);
    if (k.has('w') || k.has('arrowup')) this.pan(0, -v);
    if (k.has('s') || k.has('arrowdown')) this.pan(0, v);
    if (k.has('a') || k.has('arrowleft')) this.pan(-v, 0);
    if (k.has('d') || k.has('arrowright')) this.pan(v, 0);
    if (k.has('q')) this.dist = Math.max(1.2, this.dist * (1 - dt));
    if (k.has('e')) this.dist = Math.min(420, this.dist * (1 + dt));
    const { w, d } = this.world;
    this.target.x = ((this.target.x % w) + w) % w;
    this.target.z = ((this.target.z % d) + d) % d;
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
