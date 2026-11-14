/**
 * The map at real size (#135, e117): a world of 16 km drawn from its ground at 5 m, near the eye cell by cell and
 * coarser with distance, under the sun of its day and hour, with the month's snow, wet and dry ground and streams
 * from its climate.
 *
 * Served by `viewer map <run prefix>`: the page reads `/data/ground5.json|bin` (the fine ground),
 * `/data/maps.json|bin` (the climate's annual maps on cells of 125 m) and `/data/season.json|bin` (its twelve
 * mean months; a run without them gets months drawn from the annual maps). One unit is a metre: x east, y up, and -z
 * north (rows run south to north, so a row's z is the map's height less its own).
 */
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

const SEA = 1, POND = 2, STREAM = 3;
const T = 64; // fine cells a tile side
const TRICKLE = 0.001; // m3/s: a stream under a litre a second in its month is a dry bed
const BUILDS_PER_FRAME = 10;

const $ = (id: string) => document.getElementById(id)!;

async function fetchBin(url: string): Promise<ArrayBuffer> {
  const r = await fetch(url);
  if (!r.ok) throw new Error(`${url}: ${r.status}`);
  return r.arrayBuffer();
}

/** The fine ground and the coarse climate under it. */
class Land {
  n = 0; cell = 5; size = 0;
  height!: Float32Array; water!: Float32Array; flow!: Float32Array; kind!: Uint8Array;
  // the climate, coarse: mean temperature, the season's swing (max - min of quarter means), rain, ground height
  nc = 0; ck = 1; tmean!: Float32Array; swing!: Float32Array; rain!: Float32Array; celev!: Float32Array; lat!: Float32Array;
  // its twelve months (from `start`, a day of the calendar year): temperature, rain (mm), the soil's fill, snow lying
  // (mm of water), and a cell's run-off as a share of its year's mean
  start = 79; months: Float32Array[][] = [];
  // and the day now drawn, between two months
  day = -1; dTemp!: Float32Array; dRain!: Float32Array; dFill!: Float32Array; dSnow!: Float32Array; dFlow!: Float32Array;

  async load(status: (s: string) => void): Promise<void> {
    status('地面（5 m）を読み込み中…');
    const g = await (await fetch('data/ground5.json')).json();
    this.n = g.n; this.cell = g.cell_m; this.size = this.n * this.cell;
    const buf = await fetchBin('data/ground5.bin');
    const nn = this.n * this.n;
    this.height = new Float32Array(buf, 0, nn);
    this.water = new Float32Array(buf, 4 * nn, nn);
    this.flow = new Float32Array(buf, 8 * nn, nn);
    this.kind = new Uint8Array(buf, 12 * nn, nn);
    status('気候を読み込み中…');
    const m = await (await fetch('data/maps.json')).json();
    const mb = new Float32Array(await fetchBin('data/maps.bin'));
    const nc = m.n, cc = nc * nc, F: string[] = m.fields, S: string[] = m.static, Y = m.years.length;
    this.nc = nc; this.ck = this.n / nc;
    const mean = (f: string) => {
      const out = new Float32Array(cc), k = F.indexOf(f);
      for (let y = 0; y < Y; y++) {
        const off = (y * F.length + k) * cc;
        for (let c = 0; c < cc; c++) out[c] += mb[off + c] / Y;
      }
      return out;
    };
    const stat = (s: string) => mb.slice(Y * F.length * cc + S.indexOf(s) * cc, Y * F.length * cc + (S.indexOf(s) + 1) * cc);
    this.tmean = mean('temp'); this.swing = mean('swing'); this.rain = mean('rain');
    this.celev = stat('elev'); this.lat = stat('lat');
    const seaC = stat('sea');
    // the months
    const months: Float32Array[][] = [];
    const sj = await fetch('data/season.json').then((r) => (r.ok ? r.json() : null)).catch(() => null);
    if (sj) {
      const sb = new Float32Array(await fetchBin('data/season.bin')), SF: string[] = sj.fields;
      this.start = sj.start_day;
      const part = (m: number, f: string) => sb.slice((m * SF.length + SF.indexOf(f)) * cc, (m * SF.length + SF.indexOf(f) + 1) * cc);
      for (let m = 0; m < 12; m++) months.push([part(m, 'temp'), part(m, 'rain'), part(m, 'fill'), part(m, 'snow'), part(m, 'flow')]);
    } else {
      // a run without months: the year's swing as a sine (coldest about 20 January), its rain spread evenly
      this.start = 0;
      for (let m = 0; m < 12; m++) {
        const t = new Float32Array(cc), k = Math.cos((2 * Math.PI * ((m + 0.5) * 30.4 - 20)) / 365);
        for (let c = 0; c < cc; c++) t[c] = this.tmean[c] - (this.swing[c] / 1.8) * k;
        months.push([t, this.rain.map((v) => v / 12), new Float32Array(cc).fill(1), new Float32Array(cc), new Float32Array(cc).fill(1)]);
      }
    }
    // run-off as a share of the cell's own mean month
    for (let c = 0; c < cc; c++) {
      let sum = 0;
      for (let m = 0; m < 12; m++) sum += months[m][4][c];
      for (let m = 0; m < 12; m++) months[m][4][c] = sum > 0 ? (months[m][4][c] * 12) / sum : 1;
    }
    // the sea has no soil, snow or run-off: the shore's land reads its neighbours' there, not zeros
    for (let m = 0; m < 12; m++) {
      for (const f of [2, 3, 4]) {
        const v = months[m][f];
        let known = Uint8Array.from(seaC, (x) => (x < 0.5 ? 1 : 0));
        for (let pass = 0; pass < 3; pass++) {
          const next = known.slice();
          for (let y = 0; y < nc; y++) {
            for (let x = 0; x < nc; x++) {
              const c = y * nc + x;
              if (known[c]) continue;
              let sum = 0, k = 0;
              for (const [dx, dy] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) {
                const xx = x + dx, yy = y + dy;
                if (xx >= 0 && yy >= 0 && xx < nc && yy < nc && known[yy * nc + xx]) { sum += v[yy * nc + xx]; k++; }
              }
              if (k) { v[c] = sum / k; next[c] = 1; }
            }
          }
          known = next;
        }
      }
    }
    this.months = months;
    this.dTemp = new Float32Array(cc); this.dRain = new Float32Array(cc); this.dFill = new Float32Array(cc);
    this.dSnow = new Float32Array(cc); this.dFlow = new Float32Array(cc);
  }

  /** The coarse climate of a day of the calendar year, between the two months about it. */
  setDay(day: number): void {
    if (day === this.day) return;
    this.day = day;
    const u = (((day - this.start + 365) % 365) / 365) * 12 - 0.5, m0 = Math.floor(u), f = u - m0;
    const a = this.months[(m0 + 12) % 12], b = this.months[(m0 + 1) % 12];
    const out = [this.dTemp, this.dRain, this.dFill, this.dSnow, this.dFlow];
    for (let k = 0; k < 5; k++) {
      const o = out[k], x = a[k], y = b[k];
      for (let c = 0; c < o.length; c++) o[c] = x[c] + (y[c] - x[c]) * f;
    }
  }

  /** Whether a stream's cell runs on the day set: its year's flow by its month's share. */
  runs(c: number, i: number, j: number): boolean {
    return this.flow[c] * this.coarse(this.dFlow, i, j) >= TRICKLE;
  }

  /** A coarse field at a fine cell (bilinear between coarse centres). */
  coarse(f: Float32Array, i: number, j: number): number {
    const nc = this.nc;
    const x = Math.min(nc - 1.001, Math.max(0, (i + 0.5) / this.ck - 0.5));
    const y = Math.min(nc - 1.001, Math.max(0, (j + 0.5) / this.ck - 0.5));
    const x0 = Math.floor(x), y0 = Math.floor(y), tx = x - x0, ty = y - y0, c = y0 * nc + x0;
    return (f[c] * (1 - tx) + f[c + 1] * tx) * (1 - ty) + (f[c + nc] * (1 - tx) + f[c + nc + 1] * tx) * ty;
  }

  /** The surface at a fine cell: the ground, or the water standing on a pond or a stream. */
  surface(i: number, j: number): number {
    const n = this.n;
    i = Math.min(n - 1, Math.max(0, i)); j = Math.min(n - 1, Math.max(0, j));
    const c = j * n + i, k = this.kind[c];
    return k === POND || k === STREAM ? this.height[c] + this.water[c] : this.height[c];
  }

  /** The surface at a point in metres (bilinear), never under the sea's. */
  heightAt(x: number, z: number): number {
    const fi = x / this.cell - 0.5, fj = (this.size - z) / this.cell - 0.5;
    const i = Math.floor(fi), j = Math.floor(fj), tx = fi - i, ty = fj - j;
    const h = (this.surface(i, j) * (1 - tx) + this.surface(i + 1, j) * tx) * (1 - ty) + (this.surface(i, j + 1) * (1 - tx) + this.surface(i + 1, j + 1) * tx) * ty;
    return Math.max(0, h);
  }

  /** How far a fine cell stands over its coarse cell's ground, m. */
  over(i: number, j: number): number {
    return Math.max(0, this.height[j * this.n + i]) - Math.max(0, this.coarse(this.celev, i, j));
  }

  /** The air's mean temperature at a fine cell on the day set: the month's, and the lapse from the coarse cell's
   * height to this one's. */
  tempAt(i: number, j: number): number {
    return this.coarse(this.dTemp, i, j) - 0.0065 * this.over(i, j);
  }
}

const C = {
  sand: [0.78, 0.72, 0.55], soil: [0.45, 0.38, 0.28], straw: [0.66, 0.6, 0.38], green: [0.3, 0.48, 0.18],
  lush: [0.18, 0.38, 0.12], rock: [0.48, 0.47, 0.45], snow: [0.93, 0.95, 0.98], water: [0.16, 0.36, 0.52], seabed: [0.3, 0.38, 0.36],
  bed: [0.6, 0.57, 0.5],
};
const mix = (a: number[], b: number[], t: number, out: number[]) => {
  for (let k = 0; k < 3; k++) out[k] = a[k] + (b[k] - a[k]) * t;
  return out;
};
const smooth = (e0: number, e1: number, x: number) => {
  const t = Math.min(1, Math.max(0, (x - e0) / (e1 - e0)));
  return t * t * (3 - 2 * t);
};

/** One tile's mesh at one stride: (m+3)^2 vertices, the outer ring a skirt hung under the edge. */
function buildTile(L: Land, tx: number, ty: number, s: number, day: number, mat: THREE.Material): THREE.Mesh {
  const m = T / s, side = m + 3, nv = side * side;
  const pos = new Float32Array(nv * 3), nor = new Float32Array(nv * 3), col = new Float32Array(nv * 3);
  const i0 = tx * T, j0 = ty * T, cell = L.cell;
  const drop = 2 + 2 * s;
  for (let b = 0; b < side; b++) {
    const bb = Math.min(m, Math.max(0, b - 1)), j = j0 + bb * s;
    for (let a = 0; a < side; a++) {
      const aa = Math.min(m, Math.max(0, a - 1)), i = i0 + aa * s;
      const v = b * side + a;
      const skirt = a === 0 || b === 0 || a === side - 1 || b === side - 1;
      // the sea floor flattened past 40 m: deeper ground would show through the water as hills
      const h = Math.max(-40, L.surface(i, j));
      pos[v * 3] = (i + 0.5) * cell;
      pos[v * 3 + 1] = h - (skirt ? drop : 0);
      pos[v * 3 + 2] = L.size - (j + 0.5) * cell;
      const dx = (Math.max(-40, L.surface(i + s, j)) - Math.max(-40, L.surface(i - s, j))) / (2 * s * cell);
      const dz = (Math.max(-40, L.surface(i, j + s)) - Math.max(-40, L.surface(i, j - s))) / (2 * s * cell);
      // z runs against j: the normal's z is +dz
      const l = Math.hypot(dx, 1, dz);
      nor[v * 3] = -dx / l; nor[v * 3 + 1] = 1 / l; nor[v * 3 + 2] = dz / l;
    }
  }
  const idx = new Uint32Array((side - 1) * (side - 1) * 6);
  let k = 0;
  for (let b = 0; b < side - 1; b++) {
    for (let a = 0; a < side - 1; a++) {
      const p = b * side + a, q = p + 1, r = p + side, t = r + 1;
      idx[k++] = p; idx[k++] = q; idx[k++] = r; idx[k++] = q; idx[k++] = t; idx[k++] = r;
    }
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.BufferAttribute(pos, 3));
  g.setAttribute('normal', new THREE.BufferAttribute(nor, 3));
  g.setAttribute('color', new THREE.BufferAttribute(col, 3));
  g.setIndex(new THREE.BufferAttribute(idx, 1));
  g.computeBoundingSphere();
  const mesh = new THREE.Mesh(g, mat);
  mesh.receiveShadow = false;
  mesh.userData = { tx, ty, s, day: -1 };
  colourTile(L, mesh, day);
  return mesh;
}

/** A tile's colours for a day: the ground by its slope and height, green where the month is warm and its soil wet
 * (no plants exist: it is what the climate would let grow), straw where it is not, the month's snow, water where it
 * stands or runs and a dry bed where a stream does not. */
function colourTile(L: Land, mesh: THREE.Mesh, day: number): void {
  const { tx, ty, s } = mesh.userData;
  if (mesh.userData.day === day) return;
  mesh.userData.day = day;
  L.setDay(day);
  const m = T / s, side = m + 3;
  const col = mesh.geometry.attributes.color.array as Float32Array;
  const nor = mesh.geometry.attributes.normal.array as Float32Array;
  const n = L.n, out = [0, 0, 0];
  for (let b = 0; b < side; b++) {
    const j = ty * T + Math.min(m, Math.max(0, b - 1)) * s;
    for (let a = 0; a < side; a++) {
      const i = tx * T + Math.min(m, Math.max(0, a - 1)) * s;
      const v = b * side + a, c = j * n + i, kind = L.kind[c], h = L.height[c];
      let rgb: number[];
      if (kind === SEA) {
        rgb = mix(C.seabed, C.water, smooth(0, 15, -h), out);
      } else if (kind === POND || (kind === STREAM && L.runs(c, i, j))) {
        rgb = C.water;
      } else if (kind === STREAM) {
        rgb = C.bed;
      } else {
        const steep = 1 - nor[v * 3 + 1]; // 0 flat, ~0.3 at 45 degrees
        const dh = L.over(i, j), temp = L.coarse(L.dTemp, i, j) - 0.0065 * dh, tmean = L.coarse(L.tmean, i, j) - 0.0065 * dh;
        const rain = L.coarse(L.rain, i, j);
        // what the climate would let grow: green while the month is warm and the soil wet, straw when it is cold or
        // dry, bare soil where little rain ever falls
        const growing = smooth(3, 10, temp) * smooth(0.2, 0.6, L.coarse(L.dFill, i, j)) * smooth(-2, 6, tmean);
        mix(mix(C.soil, C.straw, smooth(100, 400, rain), out), rain > 1400 ? C.lush : C.green, growing, out);
        if (h < 2) mix(out, C.sand, 1 - smooth(0.5, 2, h), out);
        mix(out, C.rock, smooth(0.2, 0.4, steep), out); // bare from about 37 degrees, rock by 53
        // the month's snow, deeper on the ground that stands over its coarse cell's
        const lying = L.coarse(L.dSnow, i, j) * Math.min(2.5, Math.max(0, 1 + dh / 80));
        rgb = mix(out, C.snow, smooth(3, 25, lying) * (1 - smooth(0.25, 0.45, steep)), out);
      }
      col[v * 3] = rgb[0]; col[v * 3 + 1] = rgb[1]; col[v * 3 + 2] = rgb[2];
    }
  }
  mesh.geometry.attributes.color.needsUpdate = true;
}

/** The stride a tile is drawn at, by how far it is: a vertex every metre or so per 60 m of distance. */
function strideFor(d: number, cell: number): number {
  let s = 1;
  while (s < T && s * cell * 60 < d) s *= 2;
  return s;
}

async function main(): Promise<void> {
  const L = new Land();
  await L.load((s) => ($('load').textContent = s));
  const canvas = $('view') as HTMLCanvasElement;
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, logarithmicDepthBuffer: true });
  renderer.setPixelRatio(Math.min(2, window.devicePixelRatio));
  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(55, 1, 0.3, 400000);
  const controls = new OrbitControls(camera, canvas);
  controls.enableDamping = true;
  controls.maxPolarAngle = Math.PI * 0.495;
  controls.minDistance = 3;
  controls.maxDistance = 30000;
  const sun = new THREE.DirectionalLight(0xffffff, 2.2);
  scene.add(sun, sun.target);
  const hemi = new THREE.HemisphereLight(0xbfd8ff, 0x3a3226, 0.6);
  scene.add(hemi);
  scene.fog = new THREE.Fog(0xaec6d8, 4000, 26000);
  // the sea: one sheet at 0, the ground under it shows through its shallows
  const seaMat = new THREE.MeshStandardMaterial({ color: 0x1d4d6e, transparent: true, opacity: 0.82, roughness: 0.25, metalness: 0.1 });
  const sea = new THREE.Mesh(new THREE.PlaneGeometry(L.size * 40, L.size * 40), seaMat);
  sea.rotation.x = -Math.PI / 2;
  sea.position.set(L.size / 2, 0, L.size / 2);
  sea.renderOrder = 1;
  scene.add(sea);
  // and a floor under it past the map's edge, where there is no ground to see through the water (over the tiles'
  // own deep floor at -40, so that no seam shows at the border)
  const floor = new THREE.Mesh(new THREE.PlaneGeometry(L.size * 40, L.size * 40), new THREE.MeshStandardMaterial({ color: new THREE.Color(0.16, 0.36, 0.52), roughness: 0.95 }));
  floor.rotation.x = -Math.PI / 2;
  floor.position.set(L.size / 2, -38, L.size / 2);
  scene.add(floor);
  const groundMat = new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 0.95, metalness: 0 });

  // where to start: above the highest ground, looking at it from the south-west
  let top = 0, topC = 0;
  for (let c = 0; c < L.height.length; c++) if (L.height[c] > top) { top = L.height[c]; topC = c; }
  const ti = topC % L.n, tj = Math.floor(topC / L.n);
  const at0 = new THREE.Vector3((ti + 0.5) * L.cell, 0, L.size - (tj + 0.5) * L.cell);
  at0.y = L.heightAt(at0.x, at0.z);
  controls.target.copy(at0);
  camera.position.set(at0.x - 2500, at0.y + 1600, at0.z + 2500);

  const nt = L.n / T;
  const tiles = new Map<number, THREE.Mesh>(); // tile index -> mesh in the scene
  let day = Number(($('day') as HTMLInputElement).value), hour = Number(($('hour') as HTMLInputElement).value);

  function updateTiles(): void {
    const cam = camera.position;
    let built = 0;
    const want: { t: number; s: number; d: number }[] = [];
    for (let ty = 0; ty < nt; ty++) {
      for (let tx = 0; tx < nt; tx++) {
        const x0 = tx * T * L.cell, x1 = x0 + T * L.cell, z1 = L.size - ty * T * L.cell, z0 = z1 - T * L.cell;
        const dx = Math.max(x0 - cam.x, 0, cam.x - x1), dz = Math.max(z0 - cam.z, 0, cam.z - z1);
        const hy = L.heightAt((x0 + x1) / 2, (z0 + z1) / 2);
        const d = Math.hypot(dx, dz, Math.max(0, cam.y - hy - 200));
        want.push({ t: ty * nt + tx, s: strideFor(d, L.cell), d });
      }
    }
    want.sort((a, b) => a.d - b.d);
    for (const w of want) {
      const have = tiles.get(w.t);
      if (have && have.userData.s === w.s) {
        if (have.userData.day !== day && built < BUILDS_PER_FRAME * 4) { colourTile(L, have, day); built += 0.25; }
        continue;
      }
      if (built >= BUILDS_PER_FRAME) continue;
      const mesh = buildTile(L, w.t % nt, Math.floor(w.t / nt), w.s, day, groundMat);
      if (have) { scene.remove(have); have.geometry.dispose(); }
      scene.add(mesh);
      tiles.set(w.t, mesh);
      built++;
    }
  }

  // the sun of the day and the hour at the map's middle latitude
  function placeSun(): void {
    const lat = (L.coarse(L.lat, L.n / 2, L.n / 2) * Math.PI) / 180;
    const decl = (-23.44 * Math.PI / 180) * Math.cos((2 * Math.PI * (day + 10)) / 365);
    const ha = ((hour - 12) / 24) * 2 * Math.PI;
    const alt = Math.asin(Math.sin(lat) * Math.sin(decl) + Math.cos(lat) * Math.cos(decl) * Math.cos(ha));
    const az = Math.atan2(Math.sin(ha), Math.cos(ha) * Math.sin(lat) - Math.tan(decl) * Math.cos(lat)); // from south, west positive
    const dir = new THREE.Vector3(-Math.sin(az) * Math.cos(alt), Math.sin(alt), Math.cos(az) * Math.cos(alt));
    const t = controls.target;
    sun.position.copy(t).addScaledVector(dir, 10000);
    sun.target.position.copy(t);
    const up = smooth(-0.1, 0.25, Math.sin(alt));
    sun.intensity = 2.6 * up;
    sun.color.setRGB(1, 0.75 + 0.25 * up, 0.55 + 0.45 * up);
    hemi.intensity = 0.08 + 0.7 * up;
    const sky = new THREE.Color().setRGB(0.04 + 0.64 * up, 0.06 + 0.72 * up, 0.12 + 0.76 * up);
    scene.background = sky;
    (scene.fog as THREE.Fog).color.copy(sky);
  }

  function hud(): void {
    L.setDay(day);
    const t = controls.target;
    const i = Math.min(L.n - 1, Math.max(0, Math.floor(t.x / L.cell))), j = Math.min(L.n - 1, Math.max(0, Math.floor((L.size - t.z) / L.cell)));
    const c = j * L.n + i, k = L.kind[c];
    const date = new Date(Date.UTC(2001, 0, 1 + day));
    $('date').textContent = `${date.getUTCMonth() + 1}月${date.getUTCDate()}日`;
    $('clock').textContent = `${Math.floor(hour)}:${String(Math.round((hour % 1) * 60)).padStart(2, '0')}`;
    $('where').textContent = k === STREAM && !L.runs(c, i, j) ? '涸れた小川' : ['陸', '海', '池', '小川'][k];
    $('elev').textContent = `${Math.round(L.height[c])} m`;
    $('lat').textContent = `${L.coarse(L.lat, i, j).toFixed(1)}°N`;
    $('temp').textContent = `${L.tempAt(i, j).toFixed(1)} ℃`;
    $('mrain').textContent = `${Math.round(L.coarse(L.dRain, i, j))} mm`;
    $('wet').textContent = k === SEA ? '—' : `${Math.round(100 * Math.min(1, L.coarse(L.dFill, i, j)))} %`;
    $('snow').textContent = k === SEA ? '—' : `${Math.round(L.coarse(L.dSnow, i, j))} mm`;
    $('tmean').textContent = `${(L.coarse(L.tmean, i, j) - 0.0065 * (Math.max(0, L.height[c]) - L.coarse(L.celev, i, j))).toFixed(1)} ℃`;
    $('rain').textContent = `${Math.round(L.coarse(L.rain, i, j))} mm`;
    $('eye').textContent = `${Math.round(camera.position.distanceTo(t))} m`;
    ($('dayv')).textContent = `${day + 1} 日目`;
    ($('hourv')).textContent = `${hour.toFixed(2)} 時`;
  }

  // the minimap: the ground from above, a pixel per 50 m
  const mini = $('minimap') as HTMLCanvasElement, mctx = mini.getContext('2d')!;
  const mimg = mctx.createImageData(mini.width, mini.height), st = L.n / mini.width;
  for (let y = 0; y < mini.height; y++) {
    for (let x = 0; x < mini.width; x++) {
      const c = Math.floor((L.n - 1 - y * st)) * L.n + Math.floor(x * st), k = L.kind[c], h = L.height[c], p = (y * mini.width + x) * 4;
      const rgb = k === SEA ? [20, 50, 80] : k === POND || k === STREAM ? [50, 110, 180] : [90 + h * 0.08, 110 + h * 0.06, 70 + h * 0.08];
      mimg.data[p] = rgb[0]; mimg.data[p + 1] = rgb[1]; mimg.data[p + 2] = rgb[2]; mimg.data[p + 3] = 255;
    }
  }
  function drawMini(): void {
    mctx.putImageData(mimg, 0, 0);
    const t = controls.target, sx = (t.x / L.size) * mini.width, sy = (t.z / L.size) * mini.height;
    mctx.strokeStyle = '#ffd24a'; mctx.lineWidth = 2;
    mctx.beginPath(); mctx.arc(sx, sy, 5, 0, 2 * Math.PI); mctx.stroke();
  }
  mini.addEventListener('click', (e) => {
    const r = mini.getBoundingClientRect();
    const x = ((e.clientX - r.left) / r.width) * L.size, z = ((e.clientY - r.top) / r.height) * L.size;
    const off = camera.position.clone().sub(controls.target);
    controls.target.set(x, L.heightAt(x, z), z);
    camera.position.copy(controls.target).add(off);
  });

  // walking: WASD moves the point looked at along the ground, the eye with it
  const keys = new Set<string>();
  addEventListener('keydown', (e) => keys.add(e.key.toLowerCase()));
  addEventListener('keyup', (e) => keys.delete(e.key.toLowerCase()));

  const dayIn = $('day') as HTMLInputElement, hourIn = $('hour') as HTMLInputElement;
  dayIn.addEventListener('input', () => { day = Number(dayIn.value); placeSun(); });
  hourIn.addEventListener('input', () => { hour = Number(hourIn.value); placeSun(); });
  let playYear = false, playDay = false;
  $('playYear').addEventListener('click', () => { playYear = !playYear; $('playYear').textContent = playYear ? '止める' : '季節を進める'; });
  $('playDay').addEventListener('click', () => { playDay = !playDay; $('playDay').textContent = playDay ? '止める' : '一日を進める'; });

  function resize(): void {
    const w = innerWidth, h = innerHeight;
    renderer.setSize(w, h, false);
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
  }
  addEventListener('resize', resize);
  resize();
  placeSun();
  $('load').remove();

  let last = performance.now(), dayF = day, frames = 0, hudAt = 0;
  (window as any).M = { L, scene, camera, controls, tiles, renderer };
  function frame(now: number): void {
    const dt = Math.min(0.1, (now - last) / 1000);
    last = now;
    if (playYear) { dayF = (dayF + dt * 12) % 365; day = Math.floor(dayF); dayIn.value = String(day); placeSun(); }
    else dayF = day;
    if (playDay) { hour = (hour + dt * 1.5) % 24; hourIn.value = String(hour); placeSun(); }
    if (keys.size) {
      const fwd = new THREE.Vector3().subVectors(controls.target, camera.position).setY(0).normalize();
      const right = new THREE.Vector3(-fwd.z, 0, fwd.x);
      const dist = camera.position.distanceTo(controls.target);
      const v = (keys.has('shift') ? 3 : 1) * Math.max(5, dist * 0.8) * dt;
      const mv = new THREE.Vector3();
      if (keys.has('w')) mv.add(fwd);
      if (keys.has('s')) mv.sub(fwd);
      if (keys.has('d')) mv.add(right);
      if (keys.has('a')) mv.sub(right);
      if (mv.lengthSq() > 0) {
        mv.normalize().multiplyScalar(v);
        controls.target.add(mv);
        camera.position.add(mv);
      }
    }
    // the point looked at stays on the ground, and the eye never under it
    const gy = L.heightAt(controls.target.x, controls.target.z);
    camera.position.y += gy - controls.target.y;
    controls.target.y = gy;
    controls.update();
    // the haze begins beyond what is looked at, however far the eye stands back
    const reach = camera.position.distanceTo(controls.target), fog = scene.fog as THREE.Fog;
    fog.near = Math.max(4000, reach * 1.5); fog.far = Math.max(26000, reach * 6);
    const under = L.heightAt(camera.position.x, camera.position.z) + 1.6;
    if (camera.position.y < under) camera.position.y = under;
    updateTiles();
    if (now - hudAt > 200) { hud(); drawMini(); hudAt = now; }
    if (frames++ % 30 === 0) placeSun();
    renderer.render(scene, camera);
    requestAnimationFrame(frame);
  }
  requestAnimationFrame(frame);
}

main().catch((e) => {
  $('load').textContent = `読み込めなかった: ${e}`;
  console.error(e);
});
