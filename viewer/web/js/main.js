// Wiring: the records come in, the world holds them, the scene draws them, the bar drives them.

import * as THREE from 'three';
import { LiveSource, ReplaySource, RECORD } from './net.js';
import { World } from './world.js';
import { Ground, Sky, Rig, UP } from './render.js';
import { Life } from './life.js';

const $ = (id) => document.getElementById(id);
const KIND_COLORS = { hard: '#2a2622', muscle: '#a8553c', sensor: '#1b1b20', digestive: '#cbb98a', empty: '#00000000' };
const DIET = ['植物', 'まぜ', '肉', 'まだ'];

let world, ground, sky, life, rig, renderer, scene, camera, source;
let step = 0, latest = 0, playing = true, speed = 20, picked = null;
let shapeOf = -1, drawnKey = -1, plantAt = null, last = performance.now(), fps = 60, miniBase = null, seeking = false;

async function boot() {
  let state = { live: false };
  try { state = await (await fetch('/state')).json(); } catch (e) {}
  const ready = new Promise((res) => (window.__ready = res));
  source = state.live ? new LiveSource({ record: onRecord }) : new ReplaySource({ record: onRecord });
  source.start().catch((e) => console.error('source', e));
  await ready;
  $('mode').textContent = source.live ? 'live' : 'replay';
  if (source.live) source.setSpeed(speed);
  requestAnimationFrame(loop);
}

function onRecord(kind, payload) {
  if (kind === RECORD.HEADER) {
    const header = JSON.parse(new TextDecoder().decode(payload));
    setup(header);
    window.__ready();
  } else if (kind === RECORD.BODY) {
    world.addBody(payload);
  } else if (kind === RECORD.FRAME) {
    const s = world.addFrame(payload);
    if (s > latest) latest = s;
    if (step === 0) step = s;
  }
}

function setup(header) {
  world = new World(header);
  window.world = world;
  const canvas = $('view');
  renderer = new THREE.WebGLRenderer({ canvas, antialias: true, powerPreference: 'high-performance' });
  renderer.setPixelRatio(Math.min(2, devicePixelRatio));
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.05;
  scene = new THREE.Scene();
  scene.fog = new THREE.FogExp2(0xbcd0dd, 0.0035);
  camera = new THREE.PerspectiveCamera(55, 1, 0.1, 3000);
  sky = new Sky(scene);
  ground = new Ground(scene, world);
  life = new Life(scene, world);
  rig = new Rig(camera, canvas, world);
  rig.dist = 70;
  rig.pitch = 0.42;
  window.sun = new THREE.DirectionalLight(0xfff2d8, 2.2);
  window.hemi = new THREE.HemisphereLight(0xa8c8e8, 0x50503a, 0.85);
  scene.add(window.sun, window.hemi, window.sun.target);
  window.V = { world, scene, camera, ground, life, rig, renderer };
  resize();
  addEventListener('resize', resize);
  bindUI(header);
}

function resize() {
  const w = innerWidth, h = innerHeight;
  renderer.setSize(w, h, false);
  camera.aspect = w / h;
  camera.updateProjectionMatrix();
}

// ---- the clock -------------------------------------------------------------

function advance(dt) {
  const stride = world.h.stride || 1;
  if (source.live) {
    // Follow what arrives, a frame behind, and never run away from it.
    const target = latest - stride;
    if (Math.abs(target - step) > 60 * stride) step = target;
    else step += (target - step) * Math.min(1, dt * 5);
  } else {
    if (playing) step += speed * dt;
    step = Math.max(source.first, Math.min(source.last, step));
    source.fetchFrom(step);
    source.fetchFrom(step + 160 * stride);
    if (step <= source.first + 1 && speed < 0) playing = false;
  }
  world.trim(step);
}

function loop(now) {
  const dt = Math.min(0.1, (now - last) / 1000);
  last = now;
  fps += (1 / Math.max(dt, 1e-3) - fps) * 0.1;
  advance(dt);
  rig.update(dt, ground);
  camera.updateMatrixWorld();
  sky.follow(camera);

  const [a, b, t] = world.around(step);
  const season = a ? a.globals.sun ?? 1 : 1;
  const v = world.layersAt(step);
  let redrawPlants = false;
  if (v && world.decoded.step !== drawnKey) {
    drawnKey = world.decoded.step;
    ground.update(v, { sun: season });
    miniBase = null;
    redrawPlants = true;
  }
  if (!plantAt || Math.hypot(plantAt.x - rig.target.x, plantAt.z - rig.target.z) > 2) redrawPlants = true;
  if (v && redrawPlants) {
    life.plants(v, rig.target, ground, season);
    plantAt = { x: rig.target.x, z: rig.target.z };
  }
  life.bodies(world, a, b, t, rig.target, ground, picked);
  if (rig.follow !== null && a) {
    const i = a.index.get(rig.follow);
    if (i !== undefined) {
      const cell = 1 / world.sub;
      rig.goTo(a.a.x[i] * cell + 0.5, a.a.y[i] * cell + 0.5);
    }
  }
  light(season);
  renderer.render(scene, camera);
  hud(a, season);
  requestAnimationFrame(loop);
}

/** Shadows read well but cost a second pass over everything that stands. */
function setShadows(on) {
  renderer.shadowMap.enabled = on;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  window.sun.castShadow = on;
  const c = window.sun.shadow.camera;
  c.left = -55; c.right = 55; c.top = 55; c.bottom = -55; c.near = 20; c.far = 320;
  window.sun.shadow.mapSize.set(2048, 2048);
  window.sun.shadow.bias = -0.0012;
  c.updateProjectionMatrix();
  for (const p of life.pools) p.mesh.castShadow = on;
  for (const m of ground.tiles) m.receiveShadow = on;
  scene.traverse((o) => { if (o.material) o.material.needsUpdate = true; });
}

function light(season) {
  const s = Math.max(0.1, Math.min(2, season));
  const el = 0.22 + 0.42 * Math.min(1, s / 1.6);
  const az = 2.1;
  const dir = new THREE.Vector3(Math.cos(az) * Math.cos(el), Math.sin(el), Math.sin(az) * Math.cos(el));
  window.sun.position.copy(camera.position).addScaledVector(dir, 120);
  window.sun.target.position.copy(rig.target);
  window.sun.intensity = 1.0 + 1.5 * Math.min(1, s / 1.4);
  window.sun.color.setHSL(0.11 - 0.03 * Math.min(1, s), 0.55 - 0.25 * Math.min(1, s), 0.62);
  window.hemi.intensity = 0.5 + 0.5 * Math.min(1, s);
  sky.uniforms.uSun.value.copy(dir);
  const cold = Math.max(0, 1 - s);
  sky.uniforms.uTop.value.setHSL(0.6, 0.62 - cold * 0.25, 0.30 - cold * 0.05);
  sky.uniforms.uHorizon.value.setHSL(0.57, 0.30, 0.68 - cold * 0.10);
  scene.fog.color.copy(sky.uniforms.uHorizon.value);
  // The world is a torus drawn nine times; the haze has to close before its edge, and what
  // lies beyond the ground is the same haze, so there is no seam to see.
  scene.fog.density = 0.0028 + 0.005 * Math.min(1, rig.dist / 120) + cold * 0.001;
  sky.uniforms.uGround.value.copy(sky.uniforms.uHorizon.value).multiplyScalar(0.92);
}

// ---- what the watcher reads ------------------------------------------------

let hudAt = 0;
function hud(a, season) {
  const now = performance.now();
  if (now - hudAt < 120) return;
  hudAt = now;
  $('step').textContent = Math.round(step).toLocaleString();
  $('pop').textContent = a ? (a.globals.pop ?? a.n).toLocaleString() : '—';
  $('season').textContent = season.toFixed(2) + (season < 0.9 ? ' 冬' : season > 1.1 ? ' 夏' : '');
  $('where').textContent = `${rig.target.x.toFixed(0)}, ${rig.target.z.toFixed(0)}`;
  $('fps').textContent = fps.toFixed(0);
  if (!source.live && !seeking) $('seek').value = step;
  $('speedv').textContent = (source.live ? '' : (speed < 0 ? '逆 ' : '')) + Math.abs(speed).toFixed(speed >= 10 ? 0 : 1) + ' 歩/秒';
  selection(a);
  minimap(a);
}

function selection(a) {
  const empty = $('selempty'), box = $('selbody');
  if (picked === null) {
    empty.hidden = false;
    box.hidden = true;
    shapeOf = -1;
    return;
  }
  empty.hidden = true;
  box.hidden = false;
  const i = a ? a.index.get(picked) : undefined;
  if (i === undefined) {
    $('selrows').innerHTML = '<span class="muted">いなくなった</span>';
    $('shape').innerHTML = '';
    shapeOf = -1;
    return;
  }
  const names = world.h.blocks;
  const body = world.bodies.get(a.a.body[i]);
  // The shape only changes when the body does, and the panel is rebuilt 8 times a second.
  if (body && shapeOf !== a.a.body[i]) {
    shapeOf = a.a.body[i];
    $('shape').style.gridTemplateColumns = `repeat(${body.side},1fr)`;
    $('shape').style.width = body.side * 9 + 'px';
    $('shape').innerHTML = [...body.cells].map((k) => `<i style="background:${k ? KIND_COLORS[names[k]] : '#ffffff10'}"></i>`).join('');
  }
  const counts = {};
  if (body) for (const k of body.cells) if (k) counts[names[k]] = (counts[names[k]] || 0) + 1;
  $('selrows').innerHTML =
    `<div>系統 ${a.a.lineage[i] || '—'}</div>` +
    `<div>食 ${DIET[a.a.diet[i]]}</div>` +
    `<div>力 ${(a.a.energy[i] / 255 * 8).toFixed(2)}</div>` +
    (world.h.agent_record.some((f) => f.name === 'fill') ? `<div>水 ${(a.a.fill[i] / 255).toFixed(2)}</div>` : '') +
    Object.entries(counts).map(([k, n]) => `<div><i class="k" style="background:${KIND_COLORS[k]}"></i>${k} ${n}</div>`).join('');
}

function unfollow() {
  picked = null;
  rig.follow = null;
  selection(null);
}

function minimap(a) {
  const c = $('mini'), g = c.getContext('2d');
  const w = world.w, d = world.d;
  if (!miniBase) {
    const off = document.createElement('canvas');
    off.width = w; off.height = d;
    const og = off.getContext('2d');
    const img = og.createImageData(w, d);
    const v = world.layersAt(step) || {};
    const hgt = world.height, relief = world.relief || 1;
    for (let i = 0; i < w * d; i++) {
      const pl = v.plant ? Math.min(1, v.plant[i] / 3) : 0;
      const wa = v.water ? Math.max(0, v.water[i] - world.wet) : 0;
      const sh = 0.45 + 0.55 * (hgt[i] / relief);
      let r = 150 * sh, gg = 135 * sh, b = 105 * sh;
      r = r * (1 - pl) + 45 * pl * sh * 1.6; gg = gg * (1 - pl) + 110 * pl * sh * 1.6; b = b * (1 - pl) + 40 * pl * sh * 1.6;
      if (wa > 0) { const t = Math.min(0.85, wa / 200 + 0.25); r = r * (1 - t) + 40 * t; gg = gg * (1 - t) + 100 * t; b = b * (1 - t) + 160 * t; }
      img.data[i * 4] = r; img.data[i * 4 + 1] = gg; img.data[i * 4 + 2] = b; img.data[i * 4 + 3] = 255;
    }
    og.putImageData(img, 0, 0);
    miniBase = off;
  }
  g.imageSmoothingEnabled = false;
  g.drawImage(miniBase, 0, 0, c.width, c.height);
  const s = c.width / w;
  if (a) {
    g.fillStyle = '#ffd9a0';
    const cell = 1 / world.sub;
    for (let i = 0; i < a.n; i += 1) g.fillRect(a.a.x[i] * cell * s - 0.5, a.a.y[i] * cell * s - 0.5, 1.6, 1.6);
  }
  g.strokeStyle = '#fff'; g.lineWidth = 1.5;
  g.strokeRect(rig.target.x * s - 5, rig.target.z * s - 5, 10, 10);
}

// ---- the bar ---------------------------------------------------------------

function bindUI(header) {
  for (const k of ['grass', 'trees', 'fruit', 'carrion', 'bodies']) {
    $('v-' + k).onchange = (e) => life.setVisible(k, e.target.checked);
  }
  $('s-terrain').oninput = (e) => { UP.terrain = +e.target.value; ground.buildHeight(); drawnKey = -1; plantAt = null; };
  $('s-plant').oninput = (e) => { UP.plant = +e.target.value; plantAt = null; };
  $('legend').innerHTML = header.blocks.slice(1).map((b) => `<span><i style="background:${KIND_COLORS[b]}"></i>${b}</span>`).join('');
  $('play').onclick = () => {
    playing = !playing;
    $('play').textContent = playing ? '⏸' : '▶';
    if (source.live) source.setPaused(!playing);
  };
  $('stepone').onclick = () => {
    if (source.live) source.stepOnce();
    else { step += world.h.stride || 1; playing = false; $('play').textContent = '▶'; }
  };
  const sp = $('speed');
  sp.oninput = () => {
    const v = +sp.value;
    speed = Math.round(Math.pow(10, Math.abs(v)) * 10) / 10 * (v < 0 ? -1 : 1);
    if (source.live) source.setSpeed(Math.abs(speed));
  };
  sp.min = source.live ? 0 : -1;
  sp.oninput();
  $('gotob').onclick = () => {
    const to = +$('goto').value;
    if (!isFinite(to)) return;
    if (source.live) source.seek(to);
    else { step = to; source.asked.clear(); source.fetchFrom(step); }
  };
  $('goto').onkeydown = (e) => { if (e.key === 'Enter') $('gotob').onclick(); };
  const seek = $('seek');
  if (source.live) seek.style.display = 'none';
  else {
    seek.min = source.first; seek.max = source.last; seek.step = world.h.stride || 1;
    seek.oninput = () => { step = +seek.value; source.asked.clear(); source.fetchFrom(step); };
    seek.onpointerdown = () => (seeking = true);
    addEventListener('pointerup', () => (seeking = false));
  }
  $('v-shadow').onchange = (e) => setShadows(e.target.checked);
  $('unfollow').onclick = unfollow;
  addEventListener('keydown', (e) => {
    if (e.key === 'Escape') unfollow();
  });
  setShadows($('v-shadow').checked);
  $('mini').onclick = (e) => {
    const r = e.target.getBoundingClientRect();
    rig.goTo(((e.clientX - r.left) / r.width) * world.w, ((e.clientY - r.top) / r.height) * world.d);
    rig.follow = null;
  };
  // Clicking the world picks the body nearest to where the ground was hit.
  $('view').addEventListener('click', (e) => {
    if (e.target.closest('.ui')) return;
    const ray = new THREE.Raycaster();
    ray.setFromCamera(new THREE.Vector2((e.clientX / innerWidth) * 2 - 1, -(e.clientY / innerHeight) * 2 + 1), camera);
    const hits = ray.intersectObjects(ground.tiles, false);
    if (!hits.length) return;
    const p = hits[0].point;
    let best = null, bd = 4;
    for (const b of life.drawn || []) {
      const dd = Math.hypot(b.x - p.x, b.z - p.z);
      if (dd < bd) { bd = dd; best = b; }
    }
    picked = best ? best.id : null;
    rig.follow = picked;
  });
}

boot();
