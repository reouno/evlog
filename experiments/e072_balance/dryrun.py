#!/usr/bin/env python3
"""The scales of e072's seven sets (#88), read off e070's world with no runs of the bodies.

Run from the repo root: `uv run python experiments/e072_balance/dryrun.py` (about a minute).

It reads the censuses of e070's three runs (`c1225_life{9,10,11}_senses`, second half), rebuilds c1225's
terrain exactly as `climate.rs` does, and reads e063's settled world for the standing wood, the ground
and the soil. For each set it prints what the law would take from a body of that world, so that every
rate starts where it bites: a share of the upkeep, of the water, or of the work of a move.
"""
import csv
import math
import os
import struct
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
E070 = os.path.join(os.path.dirname(HERE), "e070_senses", "results")
WORLDS = os.path.join(os.path.dirname(HERE), "e063_bodies", "results", "worlds")
UPKEEP, UPKEEP_BODY, MOVE_COST, DRY, DRINK = 0.002, 0.032, 0.001, 0.004, 0.1
WOOD_HALF, LIGHT_DEPTH, POOL = 4.0, 200.0, 500.0
MEDIA = ("land", "surface", "bottom")
# c1225's parameters (e062's world file), the ones the terrain and the ground read.
SIZE, SEED, GRAIN, ROUGH, LAND, RELIEF, SOIL = 512, 1225, 158.7, 0.5, 0.422, 2002.0, 150.0


def q(v, p):
    v = sorted(v)
    return v[int((len(v) - 1) * p)] if v else float("nan")


class Rng:
    """climate.rs's xorshift64*, drawn in the same order."""

    def __init__(self, seed):
        self.s = (seed * 0x9E3779B97F4A7C15 | 1) & 0xFFFFFFFFFFFFFFFF

    def next(self):
        x = self.s
        x ^= x >> 12
        x = (x ^ (x << 25)) & 0xFFFFFFFFFFFFFFFF
        x ^= x >> 27
        self.s = x
        return (x * 0x2545F4914F6CDD1D) & 0xFFFFFFFFFFFFFFFF

    def f64(self):
        return (self.next() >> 11) / float(1 << 53)


def terrain():
    """c1225's elevation (m) and sea, as `climate.rs` builds them."""
    n, rng = SIZE, Rng(SEED)
    h = np.zeros((n, n))
    k = max(round(n / GRAIN), 1)
    amp = 1.0
    while n // k >= 2:
        lattice = np.array([rng.f64() * 2.0 - 1.0 for _ in range(k * k)]).reshape(k, k)
        spacing = n / k
        u = np.arange(n) / spacing
        f = np.floor(u)
        i0 = (f.astype(int)) % k
        i1 = (i0 + 1) % k
        t = u - f
        fade = t * t * t * (t * (t * 6.0 - 15.0) + 10.0)
        a = lattice[np.ix_(i0, i0)] + (lattice[np.ix_(i0, i1)] - lattice[np.ix_(i0, i0)]) * fade[None, :]
        b = lattice[np.ix_(i1, i0)] + (lattice[np.ix_(i1, i1)] - lattice[np.ix_(i1, i0)]) * fade[None, :]
        h += amp * (a + (b - a) * fade[:, None])
        k *= 2
        amp *= ROUGH
    flat = np.sort(h.ravel())
    level = flat[min(int((1.0 - LAND) * n * n), n * n - 1)]
    top = flat[-1]
    elev = (h - level) / (top - level) * RELIEF
    return elev.ravel(), (elev < 0.0).ravel()


def settled():
    """The fields of e063's settled world for c1225: ground, wood, grass, soil (in cell order)."""
    path = next((os.path.join(WORLDS, f) for f in os.listdir(WORLDS) if f.startswith("c1225_")), None)
    b = open(path, "rb").read()
    o = 8 + 8 + 8
    out = []
    for _ in range(11):
        (n,) = struct.unpack_from("<Q", b, o)
        out.append(np.frombuffer(b, dtype="<f8", count=n, offset=o + 8))
        o += 8 + 8 * n
    names = ["temp", "vapor", "ground", "light", "rain", "grass", "wood", "algae", "litter", "soil", "carrion"]
    return dict(zip(names, out))


def bodies():
    rows = []
    for s in (9, 10, 11):
        with open(os.path.join(E070, f"c1225_life{s}_senses_agents.csv")) as f:
            for r in csv.DictReader(f):
                if int(r["step"]) >= 50000 and int(r["age"]) >= 300:
                    size, mass = int(r["size"]), float(r["mass"])
                    rows.append({"m": int(r["medium"]), "t": float(r["temp"]), "open": int(r["open_soft"]), "size": size, "mass": mass,
                                 "up": UPKEEP * size + UPKEEP_BODY, "fat": float(r["fat"]), "store": float(r["store"]),
                                 "fill": min(float(r["fat"]) / max(float(r["store"]) * mass, 1e-6), 1.0), "bite": int(r["bite_any"]), "hard": int(r["hard"]),
                                 "height": float(r["height"]), "water": float(r["water"]), "moist": float(r["moist"]), "path": float(r["path"])})
    return rows


def main():
    rows = bodies()
    land = [r for r in rows if r["m"] == 0]
    print(f"grown bodies over the second half's censuses, seeds 9-11: {len(rows)} ({len(land)} on land)")
    o50 = q([r["open"] for r in land], 0.5)
    u50 = q([r["up"] for r in land], 0.5)
    m50 = q([r["mass"] for r in land], 0.5)
    print(f"land bodies with no open soft face: {sum(r['open'] == 0 for r in land) / len(land):.2%}")
    print(f"the median land body: {q([r['size'] for r in land], .5):.0f} blocks, mass {m50:.1f}, {o50:.0f} open soft faces, "
          f"upkeep {u50:.3f} a turn, fat fill {q([r['fill'] for r in land], .5):.3f}, water {q([r['water'] for r in land], .5):.2f}")
    t = [r["t"] for r in land]
    print(f"the cell under it: temp p10 {q(t, .1):5.1f} p50 {q(t, .5):5.1f} p90 {q(t, .9):5.1f} C, "
          f"ground fill p10 {q([r['moist'] for r in land], .1):.2f} p50 {q([r['moist'] for r in land], .5):.2f}")

    # A. Heat. A body sits `offset` = heat_make x upkeep / its open faces over the cell under it, so a
    # closed body runs hot. Out of the band it pays to come back: warming costs energy by the heat its
    # faces lose, cooling costs water by the heat it must shed, over those same faces.
    print("\nA. heat")
    for make in (250, 500, 1000, 2000):
        print(f"  heat_make {make:5d}: over its cell, the median land body sits {make * u50 / o50:5.1f} C, "
              f"a body of 6 open faces {make * u50 / 6:5.1f} C")
    make, spend, sweat, lo, hi = 1000.0, 0.0035, 0.003, 15.0, 30.0
    for heat in (0.03, 0.1, 0.3):
        out = []
        for m, name in enumerate(MEDIA):
            rs = [r for r in rows if r["m"] == m]
            warm, cool, up, n = 0.0, 0.0, 0.0, 0
            for r in rs:
                # The heat crosses the open soft faces and, at a quarter, the hard blocks' own faces
                # (about 1.5 a block); the sweat leaves by the soft faces alone.
                faces = max((r["open"] + 0.375 * r["hard"]) * (1.0 - 0.75 * r["fill"]), 0.25)
                soft = max(r["open"], 1)
                body = r["t"] + make * r["up"] / faces
                warm += spend * heat * faces * max(0.0, lo - body)
                cool += sweat * heat * faces / soft * max(0.0, body - hi)
                up += r["up"]
                n += 1
            out.append(f"{name}: warming {warm / up:.2f} of the upkeep, cooling {cool / n / DRY:.2f} of the dry air")
        print(f"  heat {heat:4.2f} (make {make:.0f}, spend {spend}, sweat {sweat}, band {lo:.0f}-{hi:.0f} C) | " + " | ".join(out))
    # What the law does to two bodies of the same size, one open and one closed, on the same cell.
    for t in (-5.0, 20.0, 45.0):
        line = []
        for faces in (22, 6):
            body = t + make * u50 / faces
            warm = spend * 0.1 * faces * max(0.0, lo - body)
            cool = sweat * 0.1 * max(0.0, body - hi)  # over the same faces it loses heat by
            line.append(f"{faces:2d} faces: {body:5.1f} C, warming {warm / u50:.2f} upkeep, cooling {cool / DRY:.2f} dry air")
        print(f"  a cell at {t:5.1f} C, heat 0.1 | " + " | ".join(line))

    # B. Wood as food: who has a tooth, and what a share of the wood offers a bite.
    w = settled()
    elev, sea = terrain()
    land_cells = ~sea
    print("\nB. wood as food")
    for force in (1, 2, 3, 4):
        print(f"  grown bodies with a tooth of {force}+: {sum(r['bite'] >= force for r in rows) / len(rows):.1%}")
    grass_c, wood_c = w["grass"][land_cells].mean(), w["wood"][land_cells].mean()
    print(f"  a land cell of the settled world: grass {grass_c:.3f}, wood {wood_c:.3f} ({wood_c / grass_c:.0f}x the grass)")
    for share in (0.01, 0.05, 0.2, 0.5):
        print(f"  wood_food {share:4.2f}: the wood offers {share * wood_c:.3f} a cell, {share * wood_c / grass_c:.1f}x the grass")

    # C. The fat weighs.
    print("\nC. the fat weighs")
    fat50 = q([r["fat"] for r in land], 0.5)
    print(f"  the median land body holds {fat50:.2f} of fat against a mass of {m50:.1f}, a full store being {5.0 * m50:.0f}")
    for fw in (0.02, 0.05, 0.2):
        print(f"  fat_weight {fw:4.2f}: it carries {fw * fat50 / m50:.1%} of its mass now, {fw * 5.0:.0%} with a full store")

    # D. The sea does not quench: where the fresh water is.
    print("\nD. the sea does not quench")
    ground = w["ground"]
    pools = (ground[land_cells] - SOIL >= POOL).mean()
    fill = np.clip(ground[land_cells] / SOIL, 0, 1)
    print(f"  land cells that are pools: {pools:.2%}; the ground's fill p10 {np.quantile(fill, .1):.2f} p50 {np.quantile(fill, .5):.2f} p90 {np.quantile(fill, .9):.2f}")
    loss = DRY * o50 * (1 - np.quantile(fill, .5)) / q([r["size"] for r in land], 0.5)
    print(f"  the median land body loses {loss:.4f} of its fill a turn to the air; a block drinks {DRINK:.2f} over water")
    for fr in (0.02, 0.1, 0.5):
        gain = DRINK * fr * np.quantile(fill, .5) * 1.0
        print(f"  fresh {fr:4.2f}: a block over median ground drinks {gain:.4f} a turn, {gain / loss:.1f}x what the body loses")

    # E. Light: the shade of the wood and the depth of the water.
    print("\nE. light")
    shade = 1.0 - w["wood"][land_cells] / (w["wood"][land_cells] + WOOD_HALF)
    print(f"  the wood's shade on land: a cell passes p10 {np.quantile(shade, .1):.2f} p50 {np.quantile(shade, .5):.2f} p90 {np.quantile(shade, .9):.2f} of the light")
    depth = np.clip(-elev[sea], 0, None)
    print(f"  the sea's depth cuts the light to p50 {1 / (1 + np.quantile(depth, .5) / LIGHT_DEPTH):.2f} of it")
    print("  the sun's height over a day averages 1/pi of noon; at a reach of 9 cells, light 1 leaves 0 cells at night")

    # F. Height: what a body climbs when it crosses a cell.
    print("\nF. height")
    e = elev.reshape(SIZE, SIZE)
    rises = []
    for shift in (1, -1):
        for axis in (0, 1):
            d = np.roll(e, shift, axis=axis) - e
            rises.append(d[(~sea.reshape(SIZE, SIZE)) & (~np.roll(sea.reshape(SIZE, SIZE), shift, axis=axis))])
    rise = np.concatenate(rises)
    up = rise[rise > 0]
    print(f"  the rise between two land cells: p50 {np.quantile(up, .5):.1f} m, p90 {np.quantile(up, .9):.1f} m (uphill only)")
    step = MOVE_COST * m50
    print(f"  a sub-cell of a move costs the median land body {step:.4f}; the path of a life is {q([r['path'] for r in land], .5):.0f} sub-cells")
    for climb in (1e-5, 3e-5, 1e-4):
        cost = climb * m50 * np.quantile(up, .5)
        print(f"  climb {climb:.0e}: the median rise costs {cost:.4f}, {cost / step:.1f}x a sub-cell of moving")

    # G. The runoff's soil: the soil a land cell holds against what the bodies pump into it.
    print("\nG. the runoff carries soil")
    soil_land = w["soil"][land_cells].sum()
    print(f"  the settled world's land holds {soil_land:.0f} of soil over {land_cells.sum()} cells ({w['soil'][land_cells].mean():.1f} a cell)")
    print("  e070's bodies moved about 1,700 a 1,000 steps from the sea's soil to the land (#88)")
    print("  `carry` is set by the probe: a short run at a known rate says what a rate moves a 1,000 steps")


if __name__ == "__main__":
    sys.exit(main())
