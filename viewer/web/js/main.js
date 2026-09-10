// Wiring: the records come in, the world holds them, the scene draws them, the bar drives them.

import * as THREE from 'three';
import { LiveSource, ReplaySource, RECORD } from './net.js';
import { World } from './world.js';
import { Ground, Sky, Rig, UP } from './render.js';
import { Life } from './life.js';

const $ = (id) => document.getElementById(id);
const KIND_COLORS = { hard: '#2a2622', muscle: '#a8553c', sensor: '#1b1b20', digestive: '#b09760', empty: '#00000000' };
const DIET = ['植物', 'まぜ', '肉', 'まだ'];

let world, ground, sky, life, rig, renderer, scene, camera, source;
let step = 0, latest = 0, playing = true, speed = 20, picked = null;
let shapeOf = -1, drawnKey = -1, drawnSwing = 99, plantAt = null, last = performance.now(), fps = 60, miniBase = null, seeking = false;
let groundDue = true, plantsDue = true, layersStep = 0, layersDrawnAt = 0;

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

  const [a, b, t, before, after] = world.around(step);
  // Where in the year the world is, straight off the law (World.seasonOf), and what that means
  // for the place being watched: under `winter high` the ridge is in winter while the valley
  // is not, so the light and the sky are the eye's own cell's, not one number for the world.
  const swing = world.swing(step);
  const here = world.season.on ? world.sunAt(rig.target.x, rig.target.z, swing) : a ? a.globals.sun ?? 1 : 1;
  // The layers are blended between the two frames that carry them, so what grows grows rather
  // than jumping; the blend is only allowed to move on so often, so that running the world fast
  // does not mean rebuilding the ground and the plants on every frame.
  if (now - layersDrawnAt > 55) {
    layersDrawnAt = now;
    layersStep = step;
  }
  const v = world.layersAt(layersStep);
  // Colouring the ground and rebuilding the plants are each a pass over the world, so they are
  // never done in the same frame: whichever is due goes now and the other goes next. Neither is
  // due at all while the layers, the season and the eye hold still.
  if (v && (world.decoded.step !== drawnKey || Math.abs(swing - drawnSwing) > 0.12)) {
    drawnKey = world.decoded.step;
    drawnSwing = swing;
    groundDue = plantsDue = true;
  }
  if (!plantAt || Math.hypot(plantAt.x - rig.target.x, plantAt.z - rig.target.z) > 2) plantsDue = true;
  if (v && groundDue) {
    ground.update(v, { swing });
    miniBase = null;
    groundDue = false;
  } else if (v && plantsDue) {
    life.plants(v, rig.target, ground, step);
    plantAt = { x: rig.target.x, z: rig.target.z };
    plantsDue = false;
  }
  life.markScale = Math.max(1, rig.dist / 32); // the pin stays about 20 pixels high however far the eye is
  life.bodies(world, a, b, t, rig.target, ground, picked, before, after);
  if (rig.follow !== null && a) {
    const i = a.index.get(rig.follow);
    if (i !== undefined) {
      // On the same curve as the body itself: from the near frame alone the eye would jump at
      // every frame of the recording, which is the one place a jump is impossible to miss.
      const cell = 1 / world.sub, p = [0, 0];
      Life.track(p, a, i, b, b ? b.index.get(rig.follow) : undefined, t, before, after, cell, world.w, world.d);
      const shape = world.blocks(a.a.body[i], a.a.facing[i]);
      const half = shape ? (shape.side * cell) / 2 : 0.5; // p is the body's corner; the eye goes to its middle
      rig.goTo(p[0] + half, p[1] + half);
    }
  }
  light(here);
  renderer.render(scene, camera);
  hud(a, b, t, here, swing, before, after);
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

/** The light and the sky of the place being watched, from how much of its sun it gets now.
 *
 * The sun rides low and pale where the season has taken it and high and warm where it has not,
 * so the length of the shadows and the colour of the sky say the season before any number does. */
function light(here) {
  const s = Math.max(0, Math.min(2, here));
  const cold = Math.max(0, 1 - s), warm = Math.min(1, Math.max(0, s - 1));
  const high = Math.min(1, s / 1.5);
  const el = 0.16 + 0.62 * high;
  const az = 2.1;
  const dir = new THREE.Vector3(Math.cos(az) * Math.cos(el), Math.sin(el), Math.sin(az) * Math.cos(el));
  window.sun.position.copy(camera.position).addScaledVector(dir, 120);
  window.sun.target.position.copy(rig.target);
  window.sun.intensity = 0.5 + 2.1 * high;
  window.sun.color.setHSL(0.09 + 0.02 * high, 0.62 - 0.3 * high, 0.52 + 0.12 * high);
  // What the sky and the ground bounce back: a pale cold light over snow, a warm one over grass.
  window.hemi.intensity = 0.4 + 0.55 * high;
  window.hemi.color.setHSL(0.57, 0.16 + 0.3 * high, 0.72 - 0.1 * high);
  window.hemi.groundColor.setHSL(0.18 + 0.4 * cold, 0.3 - 0.16 * cold, 0.28 + 0.22 * cold); // earth, then snow
  sky.uniforms.uSun.value.copy(dir);
  sky.uniforms.uTop.value.setHSL(0.6, 0.34 + 0.3 * high + 0.12 * warm, 0.34 - 0.08 * cold);
  sky.uniforms.uHorizon.value.setHSL(0.57, 0.10 + 0.24 * high, 0.66 - 0.16 * cold);
  sky.uniforms.uSunColor.value.copy(window.sun.color).multiplyScalar(1.6);
  scene.fog.color.copy(sky.uniforms.uHorizon.value);
  // The world is a torus drawn nine times; the haze has to close before its edge, and what
  // lies beyond the ground is the same haze, so there is no seam to see.
  scene.fog.density = 0.0028 + 0.005 * Math.min(1, rig.dist / 120) + cold * 0.001;
  sky.uniforms.uGround.value.copy(sky.uniforms.uHorizon.value).multiplyScalar(0.92);
}

// ---- what the watcher reads ------------------------------------------------

let hudAt = 0;
function hud(a, b, t, here, swing, before, after) {
  const now = performance.now();
  if (now - hudAt < 120) return;
  hudAt = now;
  $('step').textContent = Math.round(step).toLocaleString();
  $('pop').textContent = a ? (a.globals.pop ?? a.n).toLocaleString() : '—';
  dial(swing);
  $('where').textContent = `${rig.target.x.toFixed(0)}, ${rig.target.z.toFixed(0)}`;
  $('localsun').textContent = here.toFixed(2) + (here < 0.08 ? ' (日が出ない)' : '');
  $('fps').textContent = fps.toFixed(0);
  if (!source.live && !seeking) $('seek').value = step;
  $('speedv').textContent = (source.live ? '' : (speed < 0 ? '逆 ' : '')) + Math.abs(speed).toFixed(speed >= 10 ? 0 : 1) + ' 歩/秒';
  selection(a, b, t);
  minimap(a, b, t, before, after);
}

// The year as a dial: a ring of the four seasons with a hand on it, and the name under it.
// The world with no season law (`weather` 0 or cloud) says so and shows no ring.
const SEASONS = [['春', '#7fb84a'], ['夏', '#e0b520'], ['秋', '#c4701f'], ['冬', '#7fa8c8']];
function dial(swing) {
  const c = $('dial'), g = c.getContext('2d');
  const R = c.width / 2;
  g.clearRect(0, 0, c.width, c.width);
  if (!world.season.on) {
    $('seasonname').textContent = '季節なし';
    $('year').textContent = '—';
    return;
  }
  const year = world.year(step);
  // Straight up on the dial is the spring equinox, and it turns clockwise. A season is the
  // quarter of the year around its own extreme, so midsummer is the middle of summer, not
  // the start of it: the quarters are set back an eighth of a year.
  const seg = Math.floor(((year + 0.125) % 1) * 4) % 4;
  g.lineWidth = R * 0.3;
  for (let i = 0; i < 4; i++) {
    g.beginPath();
    g.arc(R, R, R * 0.74, (i / 4 - 0.125) * 6.283 - 1.5708, ((i + 1) / 4 - 0.125) * 6.283 - 1.5708);
    g.strokeStyle = SEASONS[i][1] + (seg === i ? 'ff' : '44');
    g.stroke();
  }
  const a = year * 6.283 - 1.5708;
  g.beginPath();
  g.moveTo(R, R);
  g.lineTo(R + Math.cos(a) * R * 0.92, R + Math.sin(a) * R * 0.92);
  g.strokeStyle = '#eef2ee';
  g.lineWidth = R * 0.1;
  g.lineCap = 'round';
  g.stroke();
  $('seasonname').textContent = SEASONS[seg][0] + (swing > 0.92 ? ' (盛夏)' : swing < -0.92 ? ' (真冬)' : '');
  $('seasonname').style.color = SEASONS[seg][1];
  $('year').textContent = (step / world.season.period).toFixed(2) + ' 年';
}

// What a body has, as gauges: each one that runs out is a way to die (the header's `deaths`), so
// the watcher sees which one this body is running out of. The chart under them uses the same colours.
const CAUSES = { hunger: '餓死', age: '寿命', broken: '体を壊された', thirst: '渇き' };
const GAUGE = { energy: '#dcc64a', fat: '#e0873a', body: '#d8584c', age: '#9fb3c4', fill: '#5aa6e0' };

function selection(a, b, t) {
  const empty = $('selempty'), box = $('selbody');
  if (picked === null) {
    empty.hidden = false;
    box.hidden = true;
    shapeOf = -1;
    return;
  }
  empty.hidden = true;
  box.hidden = false;
  // The body in the frame being shown, or the frame it was last seen in and, if a frame since
  // says so, what it died of.
  const seen = a ? world.fate(picked, a.step) : { f: null, died: null };
  const f = seen.f, i = seen.i;
  if (f === null) {
    $('fate').textContent = 'いなくなった';
    $('gauges').innerHTML = $('selrows').innerHTML = $('shape').innerHTML = '';
    shapeOf = -1;
    lifeChart(null);
    return;
  }
  const alive = f === a;
  const j = alive && b ? b.index.get(picked) : undefined;
  // Between two frames the gauges are carried like everything else.
  const val = (name) => {
    const x = world.value(f, name, i);
    return x === undefined || j === undefined ? x : x + (world.value(b, name, j) - x) * t;
  };
  const names = world.h.blocks;
  const body = world.bodies.get(f.a.body[i]);
  // The shape only changes when the body does, and the panel is rebuilt 8 times a second.
  if (body && shapeOf !== f.a.body[i]) {
    shapeOf = f.a.body[i];
    $('shape').style.gridTemplateColumns = `repeat(${body.side},1fr)`;
    $('shape').style.width = body.side * 9 + 'px';
    $('shape').innerHTML = [...body.cells].map((k) => `<i style="background:${k ? KIND_COLORS[names[k]] : '#ffffff10'}"></i>`).join('');
  }
  const energy = val('energy'), ripe = val('ripe'), fat = val('fat'), age = val('age'), born = val('born');
  const n = body ? body.n : 0, maxAge = world.params.max_age;
  const rows = [];
  const gauge = (label, share, colour, text, tip) => rows.push(
    `<div class="gauge" title="${tip}"><span>${label}</span><b><i style="width:${(Math.max(0, Math.min(1, share)) * 100).toFixed(0)}%;background:${colour}"></i></b><span>${text}</span></div>`);
  if (ripe) gauge('力', energy / ripe, GAUGE.energy, `${energy.toFixed(1)} / ${ripe.toFixed(1)}`, '食べると増え、毎歩の維持費で減る。右端 (子を産む量) に届くと子を産み、半分を渡す');
  else gauge('力', energy / world.fields.energy.max, GAUGE.energy, energy.toFixed(2), '食べると増え、毎歩の維持費で減る');
  if (fat !== undefined) gauge('蓄え', fat, GAUGE.fat, `${Math.round(fat * 100)}%`, '維持費を払うたびに体に貯まる。力が尽きるとここから払い、これも尽きると餓死');
  if (born) gauge('体', n / born, GAUGE.body, `${n} / ${born}`, 'ブロックの数。ほかの体に押されると一つずつ壊され (相手に胃があれば食べられ、なければ地面に落ちる)、0 で死ぬ。育つことはない');
  if (age !== undefined) gauge('齢', maxAge ? age / maxAge : 0, GAUGE.age, maxAge ? `${Math.round(age)} / ${maxAge}` : `${Math.round(age)}`, maxAge ? `${maxAge} 歩で寿命。それまで衰えはない` : '');
  if (world.params.thirst > 0) gauge('水', val('fill'), GAUGE.fill, `${Math.round(val('fill') * 100)}%`, '毎歩乾き、水たまりで飲む。0 で死ぬ');
  $('gauges').innerHTML = rows.join('');
  $('gauges').classList.toggle('gone', !alive);
  // What is happening to it, in words.
  const now = [];
  if (!alive) now.push(seen.died ? `死んだ: ${CAUSES[seen.died.cause] || seen.died.cause}` : 'いなくなった');
  else {
    // Nothing left is not a death sentence: a body dies only in a step it eats nothing, and about
    // half of them live at zero, some for thousands of steps.
    if (energy < 0.05) now.push(fat === undefined ? '力が尽きている' : fat > 0.01 ? '力が尽き、蓄えで生きている' : '蓄えもなく、食べた分で食いつないでいる');
    else if (ripe && energy / ripe > 0.85) now.push('もうすぐ子を産む');
    if (born && n < born) now.push(`${born - n} 個壊された`);
  }
  $('fate').textContent = now.join('・');
  const counts = {};
  if (body) for (const k of body.cells) if (k) counts[names[k]] = (counts[names[k]] || 0) + 1;
  $('selrows').innerHTML =
    `<div>系統 ${f.a.lineage[i] || '—'}・食 ${DIET[f.a.diet[i]]}</div>` +
    Object.entries(counts).map(([k, c]) => `<div><i class="k" style="background:${KIND_COLORS[k]}"></i>${k} ${c}</div>`).join('');
  lifeChart(picked, f.step);
}

/** The followed body's gauges over the frames the browser holds, up to `upto`: whether one is
 * running down is what a number on its own cannot say. */
function lifeChart(id, upto) {
  const c = $('life'), g = c.getContext('2d');
  g.clearRect(0, 0, c.width, c.height);
  $('lifespan').textContent = '';
  if (id === null) return;
  const lines = { body: [], fat: [], energy: [] };
  let s0 = -1, s1 = -1;
  for (const s of world.steps) {
    if (s > upto) break;
    const f = world.frames.get(s), i = f.index.get(id);
    if (i === undefined) continue;
    if (s0 < 0) s0 = s;
    s1 = s;
    const e = world.value(f, 'energy', i), ripe = world.value(f, 'ripe', i);
    lines.energy.push([s, ripe ? e / ripe : e / world.fields.energy.max]);
    const fat = world.value(f, 'fat', i);
    if (fat !== undefined) lines.fat.push([s, fat]);
    const born = world.value(f, 'born', i), shape = world.bodies.get(f.a.body[i]);
    if (born && shape) lines.body.push([s, shape.n / born]);
  }
  if (s1 <= s0) return;
  const W = c.width, H = c.height, pad = 3;
  g.lineWidth = 2;
  for (const [k, pts] of Object.entries(lines)) {
    g.strokeStyle = GAUGE[k];
    g.beginPath();
    pts.forEach(([s, v], m) => {
      const x = ((s - s0) / (s1 - s0)) * W, y = H - pad - Math.max(0, Math.min(1, v)) * (H - 2 * pad);
      m ? g.lineTo(x, y) : g.moveTo(x, y);
    });
    g.stroke();
  }
  $('lifespan').textContent = `この ${(s1 - s0).toLocaleString()} 歩`;
}

function unfollow() {
  picked = null;
  rig.follow = null;
  selection(null);
}

/** The map in the corner: the world from above, with a dot for every body.
 *
 * The dots are where the bodies are drawn, interpolated between the two frames the same way. A
 * recording knows the world every `stride` steps, so taking the dots from the near frame alone
 * makes every one of a few thousand of them jump at once every `stride` steps - a bright panel
 * rearranging itself in the corner of the eye, and by a long way the largest thing on the screen
 * that moves at a frame boundary. */
function minimap(a, b, t, before, after) {
  const c = $('mini'), g = c.getContext('2d');
  const w = world.w, d = world.d;
  if (!miniBase) {
    const off = document.createElement('canvas');
    off.width = w; off.height = d;
    const og = off.getContext('2d');
    const img = og.createImageData(w, d);
    const v = world.layersAt(layersStep) || {};
    const hgt = world.height, relief = world.relief || 1;
    const swing = world.swing(step), amp = world.season.at;
    for (let i = 0; i < w * d; i++) {
      const pl = v.plant ? Math.min(1, v.plant[i] / 3) : 0;
      const wa = v.water ? Math.max(0, v.water[i] - world.wet) : 0;
      const sh = 0.45 + 0.55 * (hgt[i] / relief);
      let cr = 150 * sh, cg = 135 * sh, cb = 105 * sh;
      cr = cr * (1 - pl) + 45 * pl * sh * 1.6; cg = cg * (1 - pl) + 110 * pl * sh * 1.6; cb = cb * (1 - pl) + 40 * pl * sh * 1.6;
      if (wa > 0) { const k = Math.min(0.85, wa / 200 + 0.25); cr = cr * (1 - k) + 40 * k; cg = cg * (1 - k) + 100 * k; cb = cb * (1 - k) + 160 * k; }
      // The snow line, so the whole map says how far the winter has come down the hills.
      const snow = Math.min(1, Math.max(0, (-amp[i] * swing - 0.42) / 0.34)) * 0.9;
      if (snow > 0) { cr = cr * (1 - snow) + 244 * snow; cg = cg * (1 - snow) + 247 * snow; cb = cb * (1 - snow) + 250 * snow; }
      img.data[i * 4] = cr; img.data[i * 4 + 1] = cg; img.data[i * 4 + 2] = cb; img.data[i * 4 + 3] = 255;
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
    const dot = (x, z, f) => g.fillRect(x * s - 0.8 * f, z * s - 0.8 * f, 1.6 * f, 1.6 * f);
    const p = [0, 0];
    for (let i = 0; i < a.n; i += 1) {
      const j = b ? b.index.get(a.a.id[i]) : undefined;
      Life.track(p, a, i, b, j, t, before, after, cell, w, d); // the same curve the world uses
      dot(p[0], p[1], b && j === undefined ? Life.ease(1 - t) : 1);
    }
    if (b && t > 0) {
      for (let j = 0; j < b.n; j += 1) {
        if (a.index.has(b.a.id[j])) continue; // it is born inside this interval
        Life.trackIn(p, b, j, after, t, cell, w, d);
        dot(p[0], p[1], Life.ease(t));
      }
    }
  }
  g.strokeStyle = '#fff'; g.lineWidth = 1.5;
  g.strokeRect(rig.target.x * s - 5, rig.target.z * s - 5, 10, 10);
}

// ---- the bar ---------------------------------------------------------------

function bindUI(header) {
  for (const k of ['grass', 'trees', 'fruit', 'carrion', 'bodies']) {
    $('v-' + k).onchange = (e) => life.setVisible(k, e.target.checked);
  }
  $('s-terrain').oninput = (e) => { UP.terrain = +e.target.value; ground.buildHeight(); groundDue = plantsDue = true; };
  $('s-plant').oninput = (e) => { UP.plant = +e.target.value; plantsDue = true; };
  $('s-detail').oninput = (e) => { life.setDetail(+e.target.value); plantsDue = true; };
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
  // Clicking the world picks the body under the pointer: the one whose blocks a ray through the
  // pointer meets first, which is the one in front where bodies overlap on the screen. A click
  // just off a small body finds the body drawn nearest it on the screen, within its own size (at
  // least 16 pixels). The ground is no guide: the ground a click hits is behind the body, and on
  // a hillside far behind it. A press that turned the view is a drag, not a click.
  let pressedAt = null;
  const onScreen = new THREE.Vector3(), ray = new THREE.Raycaster(), pointer = new THREE.Vector2();
  $('view').addEventListener('pointerdown', (e) => (pressedAt = [e.clientX, e.clientY]));
  $('view').addEventListener('click', (e) => {
    if (e.target.closest('.ui')) return;
    if (pressedAt && Math.hypot(e.clientX - pressedAt[0], e.clientY - pressedAt[1]) > 5) return;
    const r = e.target.getBoundingClientRect();
    pointer.set(((e.clientX - r.left) / r.width) * 2 - 1, -((e.clientY - r.top) / r.height) * 2 + 1);
    ray.setFromCamera(pointer, camera);
    picked = life.under(ray);
    rig.follow = picked;
    if (picked !== null) {
      rig.want = Math.min(rig.dist, 24); // brought close enough to see what it is
      return;
    }
    const focal = r.height / 2 / Math.tan((camera.fov * Math.PI) / 360); // pixels per unit at distance 1
    let best = null, bestFit = 1;
    for (let i = 0; i < life.drawnN; i++) {
      onScreen.set(life.drawnX[i], life.drawnY[i], life.drawnZ[i]);
      const far = onScreen.distanceTo(camera.position);
      onScreen.project(camera);
      if (onScreen.z > 1) continue; // behind the eye
      const sx = r.left + ((onScreen.x + 1) / 2) * r.width, sy = r.top + ((1 - onScreen.y) / 2) * r.height;
      const reach = Math.max(16, (0.75 * life.drawnS[i] * focal) / far);
      const fit = ((sx - e.clientX) ** 2 + (sy - e.clientY) ** 2) / (reach * reach);
      if (fit < bestFit) { bestFit = fit; best = life.drawnId[i]; }
    }
    picked = best;
    rig.follow = picked;
    if (picked !== null) rig.want = Math.min(rig.dist, 24);
  });
}

boot();
