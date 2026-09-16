#!/usr/bin/env python3
"""The scales of e073's two laws (#89), read with no runs of the bodies.

Run from the repo root: `uv run python experiments/e073_forest/dryrun.py` (about two minutes).

It rebuilds c1225's terrain as `climate.rs` does, reads e063's settled world for the standing wood,
runs the climate's temperature alone in numpy for two years (it depends on the light, the height and
its neighbours only), and reads e072's runs for what the bodies did. Then, for each law:

- **B, wood.** How patchy the standing wood is at a body's scale (#68 rule 1), what a share of the
  stock leaves standing, what a share of the growth can be taken without felling the stand, and what
  a crown's yield per unit of stand would offer against the grass the same land grows.
- **A, the cold by place.** The day's mean against the moment a body reads today: how wide the day
  swings a cell, how much of the land the two call cold, and how broad a patch each draws.
"""
import csv
import os
import struct
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
E072 = os.path.join(os.path.dirname(HERE), "e072_balance", "results")
WORLDS = os.path.join(os.path.dirname(HERE), "e063_bodies", "results", "worlds")
# c1225 is a world of stage A (e061): its parameters are read from the file the runs are given.
PARAMS = os.path.join(os.path.dirname(HERE), "e062_producers", "results", "worlds", "c1225.params")
P = {k: float(v) for k, v in (l.split("#")[0].strip().split("=") for l in open(PARAMS) if "=" in l.split("#")[0])}
SIZE, SEED, GRAIN, ROUGH, LAND, RELIEF, SOIL = int(P["size"]), int(P["seed"]), P["grain"], P["rough"], P["land"], P["relief"], P["soil"]
YEAR, DAY, TICK, TILT = P["year"], P["day"], P["tick"], P["tilt"]
LAT_LO, LAT_HI, NIGHT, GAIN, LAPSE = P["lat_lo"], P["lat_hi"], P["night"], P["gain"], P["lapse"]
LAND_RATE, SEA_RATE, SPREAD = P["land_rate"], P["sea_rate"], P["spread"]
# e062's draw d11, the producers' rates the runs are given.
WOOD_RATE, GRASS_RATE, WOOD_HALF, GRASS_HALF = 0.0017, 0.009983, 4.0, 0.2
WOOD_LIFE, GRASS_LIFE, ROT = 20_000.0, 2_000.0, 1.0 / 2_000.0
WARM_FROM, WARM_FULL, WARM_LO = 5.0, 20.0, 15.0
TRAVEL = 6  # cells a body covers in a life (e072's travel_p50 is 1.8-5.7 on seeds 9-11)


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
    elev = (h - level) / (flat[-1] - level) * RELIEF
    return elev, elev < 0.0


def settled():
    """The fields of e063's settled world for c1225 (in cell order)."""
    path = next(os.path.join(WORLDS, f) for f in os.listdir(WORLDS) if f.startswith("c1225_"))
    b = open(path, "rb").read()
    o = 24
    out = []
    for _ in range(11):
        (n,) = struct.unpack_from("<Q", b, o)
        out.append(np.frombuffer(b, dtype="<f8", count=n, offset=o + 8))
        o += 8 + 8 * n
    names = ["temp", "vapor", "ground", "light", "rain", "grass", "wood", "algae", "litter", "soil", "carrion"]
    return dict(zip(names, out))


# ---------------------------------------------------------------- the climate's temperature

def temperatures(elev, sea, updates):
    """`climate.rs`'s temperature field, update by update, for `updates` updates from the settled
    world's temperature. It reads the light, the height and its four neighbours only, so it runs
    without the water. Yields (step, temp) every update."""
    n = SIZE
    air = np.maximum(elev, 0.0)
    lat = np.radians(LAT_LO + (LAT_HI - LAT_LO) * (1.0 - np.abs(2.0 * (np.arange(n) + 0.5) / n - 1.0)))
    lat_sin, lat_cos = np.sin(lat)[:, None], np.cos(lat)[:, None]
    rate = np.where(sea, SEA_RATE, LAND_RATE)
    inv_cap = np.where(sea, SEA_RATE / LAND_RATE, 1.0)
    lapse = LAPSE / 1000.0
    temp = settled()["temp"].reshape(n, n).copy()
    span = 2 * np.pi * TICK / DAY
    x = np.arange(n)[None, :]
    step = 0.0
    for _ in range(updates):
        season = np.sin(2 * np.pi * (step + 0.5 * TICK) / YEAR)
        decl = np.radians(TILT) * season
        a, b = lat_sin * np.sin(decl), lat_cos * np.cos(decl)
        h0 = np.remainder(2 * np.pi * (step / DAY + x / n) + np.pi, 2 * np.pi) - np.pi
        with np.errstate(invalid="ignore"):
            rise = np.where(a >= b, np.inf, np.where(a <= -b, -1.0, np.arccos(np.clip(-a / np.maximum(b, 1e-12), -1, 1))))
        sin_rise = np.where(np.isfinite(rise) & (rise > 0.0), np.sin(np.where(np.isfinite(rise), rise, 0.0)), 0.0)
        lo0, hi0 = h0 + 0.0 * a, h0 + span + 0.0 * a
        s_lo0, s_hi0 = np.sin(lo0), np.sin(hi0)
        q = np.zeros((n, n))
        for noon in (0.0, 2 * np.pi):
            lo = np.where(lo0 > noon - rise, lo0, noon - rise)
            s_lo = np.where(lo0 > noon - rise, s_lo0, -sin_rise)
            hi = np.where(hi0 < noon + rise, hi0, noon + rise)
            s_hi = np.where(hi0 < noon + rise, s_hi0, sin_rise)
            q += np.where(hi > lo, a * (hi - lo) + b * (s_hi - s_lo), 0.0)
        q = np.maximum(q / span, 0.0)
        polar = np.isinf(rise) & np.ones((n, n), dtype=bool)
        q = np.where(polar, np.maximum(a + b * (s_hi0 - s_lo0) / span, 0.0), q)
        eq = NIGHT + GAIN * q - lapse * air
        temp += rate * (eq - temp)
        theta = temp + lapse * air
        k = 0.25 * SPREAD
        d = k * ((np.roll(theta, -1, 1) - theta) + (np.roll(theta, 1, 1) - theta)
                 + (np.roll(theta, -1, 0) - theta) + (np.roll(theta, 1, 0) - theta))
        temp += d * inv_cap
        step += TICK
        yield step, temp


def patchiness(field, land, name, widths=(1, 2, 4, 6, 12, 24, 48)):
    """How much of a field's spread over the land survives averaging over a W x W window: a law a
    body can cross in a life is a law it averages away (#68 rule 1)."""
    out = []
    v = np.where(land, field, np.nan)
    for w in widths:
        if w == 1:
            m = field[land]
        else:
            pad = SIZE // w * w
            blocks = v[:pad, :pad].reshape(pad // w, w, pad // w, w)
            with np.errstate(invalid="ignore"):
                m = np.nanmean(blocks, axis=(1, 3)).ravel()
            m = m[~np.isnan(m)]
        out.append((w, np.quantile(m, 0.1), np.quantile(m, 0.5), np.quantile(m, 0.9), m.std() / max(abs(m.mean()), 1e-9)))
    print(f"  {name}: the mean over a window of W cells (p10 / p50 / p90, and its spread over its mean)")
    for w, p10, p50, p90, cv in out:
        mark = "  <- a life's travel" if w == TRAVEL else ""
        print(f"    W {w:2d}: {p10:7.2f} {p50:7.2f} {p90:7.2f}   cv {cv:5.2f}{mark}")


def e072_runs():
    """What e072's three runs did over their second half."""
    out = {}
    for s in (9, 10, 11):
        with open(os.path.join(E072, f"c1225_life{s}_sets_log.csv")) as f:
            rows = [r for r in csv.DictReader(f) if int(r["step"]) >= 50000]
        m = lambda k: sum(float(r[k]) for r in rows) / len(rows)  # noqa: E731
        out[s] = {k: m(k) for k in ("pop", "plant_intake", "wood_intake", "wood", "grass", "travel_p50", "land_temp", "pop_cold", "pop_mild", "pop_hot", "tooth")}
    return out


def main():
    elev, sea = terrain()
    land = ~sea
    w = settled()
    wood = w["wood"].reshape(SIZE, SIZE)
    grass = w["grass"].reshape(SIZE, SIZE)
    n_land = land.sum()
    runs = e072_runs()
    print(f"c1225: {n_land} land cells of {SIZE * SIZE}; e072's bodies travel "
          f"{min(r['travel_p50'] for r in runs.values()):.1f}-{max(r['travel_p50'] for r in runs.values()):.1f} cells in a life")

    # ------------------------------------------------------------ B. wood
    print("\nB. wood a body can live on")
    print(f"  the settled world's land: wood {wood[land].mean():.3f} a cell (p50 {np.quantile(wood[land], .5):.3f}, "
          f"p90 {np.quantile(wood[land], .9):.2f}, max {wood[land].max():.2f}); {(wood[land] > 0.1).mean():.0%} of it stands over 0.1")
    print(f"  grass {grass[land].mean():.3f} a cell before the bodies graze it")
    print("\n  1. is the wood patchy at a body's scale? (#68 rule 1)")
    patchiness(wood, land, "wood")
    patchiness(grass, land, "grass")

    print("\n  2. what a share of the stock leaves standing (e072's law, `wood_food`)")
    for s in (9, 10, 11):
        r = runs[s]
        print(f"    e072 seed {s}: wood {r['wood'] / n_land:.3f} a cell over the second half "
              f"({r['wood'] / (wood[land].sum()):.1%} of the settled stand), the wood {r['wood_intake'] / r['plant_intake']:.2%} of what is eaten")
    print(f"    the settled stand holds {wood[land].sum():.0f}; e072's bodies eat {runs[9]['plant_intake']:.0f} a 1,000 steps, "
          f"so the whole forest is {wood[land].sum() / runs[9]['plant_intake']:.1f} thousand steps of food, once")

    print("\n  3. what a share of the growth can be taken (option (b), a flow off the stand)")
    # A stand holds where its growth pays its death: R L s/(s+H) = s, so R L = s + H and the share of
    # its growth it can give up before it falls is 1 - H/(s+H) = its own cover.
    cover = wood / (wood + WOOD_HALF)
    grow = wood / WOOD_LIFE  # per step, at the settled stand growth answers death
    for name, m in (("the mean land cell", land), ("the 10% with the most wood", land & (wood >= np.quantile(wood[land], 0.9)))):
        c = cover[m].mean()
        print(f"    {name}: cover {c:.2f}, so it can give up {c:.0%} of its growth; "
              f"that is {(c * grow[m]).sum():.2f} a step over {m.sum()} cells")
    print(f"    the whole land's wood grows {grow[land].sum():.1f} a step ({grow[land].sum() * 1000:.0f} a 1,000 steps) and "
          f"the most that can be taken is {(cover * grow)[land].sum() * 1000:.0f}, against the {runs[9]['plant_intake']:.0f} the bodies eat")

    print("\n  4. what a crown's yield would offer (`wood_yield` per unit of stand a step)")
    grass_grow = grass / GRASS_LIFE  # at the settled stand, growth answers death
    print(f"    the land's grass grows {grass_grow[land].sum() * 1000:.0f} a 1,000 steps before the bodies; "
          f"e072's bodies eat {runs[9]['plant_intake']:.0f}")
    for y in (1e-5, 3e-5, 1e-4, 3e-4, 1e-3):
        world = (y * wood)[land].sum() * 1000
        rich = land & (wood >= np.quantile(wood[land], 0.9))
        print(f"    wood_yield {y:.0e}: {world:8.0f} a 1,000 steps ({world / runs[9]['plant_intake']:5.1%} of what is eaten); "
              f"a cell of the richest tenth yields {(y * wood[rich]).mean() * 1000:.3f} against the {grass_grow[rich].mean() * 1000:.3f} of grass it grows; "
              f"uneaten it stands at {y * np.quantile(wood[land & (wood > 0.1)], .9) / ROT:.2f} where the ground is warm and wet")

    # ------------------------------------------------------------ A. the cold by place
    print("\nA. a cold that differs by place (`day_temp`)")
    # The law: the climate keeps a running mean of a cell's temperature over the last day (a weight
    # of tick/day an update), and a body reads `day_temp` of the way from the moment to that mean.
    ups = int(round(YEAR / TICK))
    alpha = TICK / DAY
    it = temperatures(elev, sea, 2 * ups)
    tday = None
    for i in range(ups):  # a year of spin-up, so the running mean is settled too
        _, t = next(it)
        tday = t.copy() if tday is None else tday + alpha * (t - tday)
    n2 = (SIZE, SIZE)
    acc = {k: np.zeros(n2) for k in ("inst", "day", "cold_inst", "cold_day", "gap")}
    lo_day, hi_day = np.full(n2, np.inf), np.full(n2, -np.inf)
    for i in range(ups):
        _, t = next(it)
        tday += alpha * (t - tday)
        acc["inst"] += t
        acc["day"] += tday
        acc["cold_inst"] += t < WARM_LO
        acc["cold_day"] += tday < WARM_LO
        acc["gap"] += np.abs(t - tday)
        np.minimum(lo_day, tday, out=lo_day)
        np.maximum(hi_day, tday, out=hi_day)
    for k in acc:
        acc[k] /= ups
    print(f"    the land over a year: {acc['inst'][land].mean():.1f} C by the moment, {acc['day'][land].mean():.1f} C by the day's mean "
          f"(e072's runs log {sum(r['land_temp'] for r in runs.values()) / 3:.1f} C)")
    print(f"    the moment stands {np.quantile(acc['gap'][land], .5):.1f} C from the day's mean on a median land cell "
          f"(p90 {np.quantile(acc['gap'][land], .9):.1f} C); the year swings the mean by {np.quantile((hi_day - lo_day)[land], .5):.1f} C")
    print(f"    cold ({WARM_LO:.0f} C, the band a body pays to leave): the moment calls {acc['cold_inst'][land].mean():.0%} of the land-hours cold, "
          f"the day's mean {acc['cold_day'][land].mean():.0%} of the land-days")
    for name, share in (("by the moment", acc["cold_inst"]), ("by the day's mean", acc["cold_day"])):
        print(f"    {name}: {(share[land] > 0.9).mean():5.1%} of the land is cold nine days in ten, {(share[land] < 0.1).mean():5.1%} is cold one in ten, "
              f"{((share[land] >= 0.1) & (share[land] <= 0.9)).mean():5.1%} is between")
    print("\n    how broad a patch each draws (the share of a year a cell is cold):")
    patchiness(acc["cold_inst"], land, "cold by the moment")
    patchiness(acc["cold_day"], land, "cold by the day's mean")
    for s in (9, 10, 11):
        r = runs[s]
        tot = r["pop_cold"] + r["pop_mild"] + r["pop_hot"]
        print(f"    e072 seed {s}: {r['pop_cold'] / tot:.1%} of its bodies in the cold band, {r['pop_hot'] / tot:.1%} in the hot")


if __name__ == "__main__":
    sys.exit(main())
