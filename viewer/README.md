# viewer

Watching the world in 3D. The experiment is the world; this crate is the window.

    cargo run --release -p viewer -- experiments/e041_stock/results/<run>_view.bin
    open http://127.0.0.1:7777/

## The two ways to watch

**Live.** The world runs and streams its frames, and the browser tells it how fast to run:

    EVLOG_VIEW=serve ./target/release/e041_stock 1000000 1 128 ...      # 127.0.0.1:7777
    EVLOG_VIEW=serve:port=7777,speed=20,from=300000 ...                 # full speed to 300,000, then watch

`from` (and the browser's step box) runs the world at full speed to a step and then holds it to
the speed asked for. Pause, one step, and faster or slower all reach the world itself.

**Replay.** The run writes a recording and the browser plays it at any speed, forwards or back,
from any step:

    EVLOG_VIEW=rec ./target/release/e041_stock ...                      # the whole run
    EVLOG_VIEW=rec:from=299000,len=1200 ...                             # a window of it
    EVLOG_VIEW=rec:from=0,len=1000000,stride=500 ...                    # a time-lapse of the whole run

It is written beside the run's other results as `<run>_view.bin`, and it is large: a frame is
20 bytes per body (about 40 KB at 2,000 bodies), and the cell layers, every `layers` frames
(30 by default), are one byte per cell per layer. A window of 1,200 steps of a 128x128 world is
about 90 MB. Recordings are not committed.

Nothing happens without EVLOG_VIEW, and a run with it writes the same results as one without.

## The interface

`wire.rs` is the whole contract, and the browser reads it rather than knowing the experiment:

- **The header** (once) says what this world is made of: its size, the terrain, the **layers**
  (a name, a cap and a scale per cell layer: `plant`, `fruit`, `carrion`, `soil`, `water`,
  `root`), the **globals** (a number a frame: `sun`, `air`, `pop`), the **blocks** (what kind
  each number in a body means) and the **agent record** (the fields of a body in a frame, in
  order). The run's laws and arguments ride along as `params`.
- **A body shape** is sent once, the first time it is seen, and frames name it by id.
- **A frame** is the step, the globals, the cell layers (every `layers` frames: they change
  slowly) and every living body: where it is, which way it faces, its shape, its lineage, what
  it eats, its water and its energy.

### When an experiment grows

Add the layer or the field to `Init` and to the frame in the experiment, and the header carries
it. The browser draws what it knows by name and ignores the rest, so an old browser still shows
a new world, and a new browser still shows an old recording.

### What an experiment does (three lines)

```rust
let mut view = viewer::View::from_env(&prefix, viewer::Init { .. });   // near the terrain file
...
if let Some(v) = view.as_mut() {                                       // in the step loop
    if v.wants(step) { v.frame(step, &layers, &globals, |push| { for a in &agents { push(..) } }); }
    v.tick(step);                                                      // live: hold to the watched speed
}
```

## What the browser draws

One world cell is one unit; the world's y is the scene's z; the torus is drawn nine times so
there is no edge. The ground is the terrain's height, coloured by its soil, its water and what
grows on it; standing water (above what the sky gives a cell alone) is a pool. A cell's plant is
grass while it is short and a tree when it stands a cell or more, as tall as its column. Fallen
fruit and the dead lie on the ground. A body is its blocks: hard is a shell, muscle is flesh,
sensor is an eye, digestive is a gut. Far bodies are drawn as one slab, coloured by diet.

Drag to turn, right-drag or shift-drag to move, wheel to zoom, WASD to walk, click a body to
follow it, click the minimap to go somewhere.

### The season

The browser works the season out from the law, not from a number in a frame: `params` carries
the period, the amplitude and whether the winter is by height (e032), so every cell's own sun is
`1 + a(cell) sin(2 pi step / period)` and the browser knows the year from the step alone. That
matters because under `winter high` the ridge is in winter while the valley is not, and a single
number for the world cannot say so.

What the watcher sees of it: the ground frosts and then goes white where a cell's sun is nearly
out, and the snow line comes down the hills and goes back up (the minimap shows it too); the
leaves turn amber and then fall, and a conifer stands green through it; the lawn goes to straw;
the sun rides low and pale in winter and high and warm in summer, over the ground the eye is
looking at rather than the one cell it sits on. The HUD has a dial of the year with the season
named on it. A world with no season law says so and none of this happens.

### Cost

Everything that stands is instanced and only what is near the eye is drawn in full. The `草木の
精細` slider is the knob: it sets how many parts a tree has, how many tufts a cell of lawn has,
and how far out either is drawn (a 128 world on a laptop runs at 35-55 fps across its range).
Nothing is rebuilt while the eye and the season hold still.

### How a thing is drawn

A tree is one of three kinds, stands somewhere of its own inside its cell, leans its own way and
has its own greens and bark - all of it from the cell's own number, so it is the same tree every
time it is drawn and no two neighbours are alike. Its height is the matter standing there and it
stands on that one cell, so a tall column is drawn tall and narrow (the leaves stacked up the
trunk) rather than as a wide crown that would cover its neighbours and lie about the world. The
lawn, the fallen fruit and the dead are scattered inside their cells the same way.
