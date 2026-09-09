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

### Between two frames

A recording knows the world every `stride` steps and the browser draws the steps in between, so
what happens inside an interval has to be shown rather than skipped.

**A body moves along a curve through four frames, not a chord between two.** A chord gives every
body one velocity for the whole interval and then turns all of them at the same instant. The
position is continuous, so two pictures either side of a frame look almost the same and no diff
of pictures will find it - but the velocity is not continuous, and a jump in velocity is what the
eye reads as a stutter. Measured as the change in the drawn bodies' velocity, a chord gives
exactly 0 inside an interval and 37 at the boundary; a Catmull-Rom through the frame before and
the frame after as well gives about 2 either side, and the boundary is no longer a place.

Births and deaths are the ends of that: a body that dies inside the interval carries on the way
it was going and shrinks to nothing over the interval, and one that is born inside it comes up
from nothing along the way it will be going. Standing them still at the near frame is a jerk of
their whole speed, and popping them in and out whole is a quarter of the world blinking (in 50
steps of e041, 12% of the bodies die and 15% are born).

The map in the corner is drawn by the same rule, and it is the one that mattered most: it is a
few thousand bright dots on a small dark panel, and taking them from the near frame alone made
every one of them jump at once. Measured on screenshots either side of a boundary, it was 385
times an ordinary step's change, against 1.5 for the world.

What is still cut rather than carried: a body's facing and its shape. In those same 50 steps 10%
of the bodies turn and 6% change shape, and they do it in one frame. It measures 1.5x an ordinary
step, so it is what to look at next if a boundary is still visible.

### Cost

Everything that stands is instanced and only what is near the eye is drawn in full. The `草木の
精細` slider is the knob: it sets how many parts a tree has, how many tufts a cell of lawn has,
and how far out either is drawn.

Three passes make a frame: the ground's colour, the plants, and the bodies. The first two run
only when the layers, the season or the eye move, and never in the same frame; the third runs
every frame. On a 128 world with 4,800 bodies a frame is about 1 ms and the worst one in a
thousand is 12 ms, so nothing stalls when the season turns.

Two things cost far more than the work in them, and both are worth knowing:

- **A pool is sent to the card by how big it is, not by how full it is.** The pools are sized for
  the worst case and are usually a tenth full, so `Pool.done` sends only the instances it wrote
  (`addUpdateRange`). Sending the whole buffer was most of the cost of a frame that rebuilt the
  plants: 12 ms of a 19 ms frame.
- **An allocation inside a per-item loop.** An object per body drawn, 2,900 a frame, cost 24 ms
  a frame in garbage alone. Nothing that runs per cell, per vertex or per instance allocates, and
  nothing there makes a `THREE.Color`: the palette is plain numbers made once, a cell layer is
  unpacked through a table of 256 values, and the bodies are picked out of flat arrays.

### How a thing is drawn

A tree is one of three kinds, stands somewhere of its own inside its cell, leans its own way and
has its own greens and bark - all of it from the cell's own number, so it is the same tree every
time it is drawn and no two neighbours are alike. Its height is the matter standing there and it
stands on that one cell, so a tall column is drawn tall and narrow (the leaves stacked up the
trunk) rather than as a wide crown that would cover its neighbours and lie about the world. The
lawn, the fallen fruit and the dead are scattered inside their cells the same way.
