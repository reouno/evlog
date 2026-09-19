#!/usr/bin/env python3
"""The regions a generated world holds apart (e084, #97), from e062's producers-only maps (no bodies).

Run from the repo root: `uv run python experiments/e084_regions/regions.py [--dense 0.03]`

On c1225 the density of land bodies (e081's control, seeds 9-11) follows the producers-only map: the ground's
yearly dryness (1 - its fill, what a body's drink reads; correlation -0.93 over blocks of 8 x 8 cells), and
within a dryness the temperature of the coolest quarter: a place cold in winter holds fewer, and a place hot
in every quarter (over the heat band's 30 C all year, so its bodies sweat water every season) holds fewer
too. The **calibration** is c1225's mean density for each class of dryness and coolest-quarter temperature.

- a block (8 x 8 cells, half or more of it land) is **dense** when its predicted density is `--dense` (0.03
  bodies a land cell) or more;
- a **region** is a 4-connected piece of dense blocks (on the torus). On c1225's measured densities this rule
  finds the region e083 saw held (the upper north, the leader 6%) apart from the leader's (87%): what holds a
  boundary is the depth of the thin strip, and the strip there is one or two blocks wide;
- a region's **room** is its predicted bodies; the world's **effective number of regions** is exp(entropy) of
  the rooms' shares over the regions of 10 blocks or more (Hill 1, as for kinds).

Writes `results/regions.csv` (a row a world), `results/blocks_<world>.csv` (each block's dryness, temperature,
predicted density and region) and `results/calibration.csv`.
"""
import csv
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from mapsio import read_maps  # noqa: E402

EXP = os.path.dirname(HERE)
B = 8
MAPS = {"c1225": os.path.join(EXP, "e062_producers/results/pass/c1225_d11_maps.bin")}
for w in ("c1173", "c1182", "c1208", "c1221", "c1236"):
    MAPS[w] = os.path.join(HERE, "results/maps", f"{w}_d11_maps.bin")
DRY = [0, 0.4, 0.5, 0.55, 0.6, 0.65, 0.7, 0.75, 0.8, 0.9, 1.01]
TEMP = [-99, 0, 10, 20, 25, 30, 33, 99]  # the coolest quarter's mean temperature
BIG = 10  # blocks: a region counts from here


def cls(v, edges):
    return np.clip(np.searchsorted(edges, v, side="right") - 1, 0, len(edges) - 2)


def arg(name, default):
    return float(sys.argv[sys.argv.index(name) + 1]) if name in sys.argv else default


def blocks_of(path):
    m = read_maps(path)
    n = m["n"]
    g = n // B
    moist = m["moist"]
    land = moist.max(0) > 0
    lc = land.reshape(g, B, g, B).sum((1, 3))
    mean = lambda a: (a * land).reshape(g, B, g, B).sum((1, 3)) / np.maximum(lc, 1)  # noqa: E731
    return n, g, lc, mean(1 - moist.mean(0)), mean(m["temp"].min(0))


def density_of(n, g, lc):
    """c1225's control: land bodies a land cell a census, per block, mean of seeds 9-11."""
    dens = np.zeros((g, g))
    for s in (9, 10, 11):
        cnt = np.zeros((g, g))
        steps = set()
        with open(os.path.join(EXP, f"e081_drink/results/ladder/c1225_life{s}_u0_agents.csv")) as f:
            for r in csv.DictReader(f):
                if r["medium"] != "0":
                    continue
                c = int(r["cell"])
                cnt[(c // n) // B, (c % n) // B] += 1
                steps.add(r["step"])
        dens += cnt / len(steps) / np.maximum(lc, 1) / 3
    return dens


def label(mask):
    """4-connected pieces of a mask on the torus: labels (0 = none, 1..k)."""
    g = mask.shape[0]
    lab = np.zeros(mask.shape, int)
    k = 0
    for y in range(g):
        for x in range(g):
            if mask[y, x] and not lab[y, x]:
                k += 1
                stack = [(y, x)]
                lab[y, x] = k
                while stack:
                    a, b = stack.pop()
                    for da, db in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        c, d = (a + da) % g, (b + db) % g
                        if mask[c, d] and not lab[c, d]:
                            lab[c, d] = k
                            stack.append((c, d))
    return lab, k


def regions_of(dense):
    lab, _ = label(dense)
    ks, cnt = np.unique(lab[lab > 0], return_counts=True)
    keep = {int(k) for k, c in zip(ks, cnt) if c >= BIG}
    return np.where(np.isin(lab, list(keep)), lab, 0)


def main():
    cut = arg("--dense", 0.03)
    n, g, lc, bdry, btemp = blocks_of(MAPS["c1225"])
    dens = density_of(n, g, lc)
    ok = lc >= B * B // 2
    # the calibration: c1225's mean density by dryness and temperature class (a class with few blocks
    # takes its dryness class's mean)
    dc, tc = cls(bdry, DRY), cls(btemp, TEMP)
    table = np.zeros((len(DRY) - 1, len(TEMP) - 1))
    count = np.zeros_like(table)
    for i in range(len(DRY) - 1):
        row = ok & (dc == i)
        for j in range(len(TEMP) - 1):
            sel = row & (tc == j)
            count[i, j] = sel.sum()
            table[i, j] = dens[sel].mean() if sel.sum() >= 5 else (dens[row].mean() if row.sum() else 0.0)
    with open(os.path.join(HERE, "results", "calibration.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["dry_lo", "dry_hi", "temp_lo", "temp_hi", "blocks", "density"])
        for i in range(len(DRY) - 1):
            for j in range(len(TEMP) - 1):
                w.writerow([DRY[i], DRY[i + 1], TEMP[j], TEMP[j + 1], int(count[i, j]), round(float(table[i, j]), 5)])
    predict = lambda d, t: table[cls(d, DRY), cls(t, TEMP)]  # noqa: E731
    pred = predict(bdry, btemp)
    print(f"c1225 calibration: correlation of predicted and measured density {np.corrcoef(pred[ok], dens[ok])[0, 1]:.3f}")
    # the check: the rule on c1225's measured densities against the same rule on its predicted ones
    meas = regions_of(ok & (dens >= cut))
    pr = regions_of(ok & (pred >= cut))
    for name, lab in (("measured", meas), ("predicted", pr)):
        ks, cnt = np.unique(lab[lab > 0], return_counts=True)
        print(f"c1225 {name}: {len(ks)} regions of {BIG}+ blocks, sizes {sorted(cnt.tolist(), reverse=True)}")
    both = (meas > 0) & (pr > 0)
    agree = np.mean([len(np.unique(pr[(meas == k) & both])) == 1 for k in np.unique(meas[meas > 0])])
    print(f"c1225: share of measured regions that fall in one predicted region {agree:.2f}")
    rows = []
    for world, path in MAPS.items():
        if not os.path.exists(path):
            print(f"{world}: no map yet")
            continue
        n, g, lc, bdry, btemp = blocks_of(path)
        ok = lc >= B * B // 2
        pred = predict(bdry, btemp) * ok
        lab = regions_of(pred >= cut)
        rooms = {int(k): float((pred * lc)[lab == k].sum()) for k in np.unique(lab[lab > 0])}
        room = float((pred * lc).sum())
        p = np.array(sorted(rooms.values(), reverse=True)) / max(sum(rooms.values()), 1e-9)
        eff = float(np.exp(-(p * np.log(p)).sum())) if len(p) else 0.0
        land = int(lc.sum())
        row = {"world": world, "dense": cut, "land_cells": land, "room": round(room), "dense_share": float((lc * (lab > 0)).sum() / max(land, 1)),
               "regions": len(rooms), "regions_5pct": int((p >= 0.05).sum()), "effective": eff,
               "largest": float(p[0]) if len(p) else 0.0, "shares": " ".join(f"{x:.3f}" for x in p[:8])}
        rows.append(row)
        print(f"{world}: land {land} room {room:,.0f} in regions {row['dense_share']:.0%} regions {len(rooms)} "
              f"(>=5%: {row['regions_5pct']}) effective {eff:.2f} shares {row['shares']}")
        with open(os.path.join(HERE, "results", f"blocks_{world}.csv"), "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["gx", "gy", "land", "dry", "temp", "predicted", "region"])
            for y in range(g):
                for x in range(g):
                    if lc[y, x]:
                        w.writerow([x, y, int(lc[y, x]), round(float(bdry[y, x]), 4), round(float(btemp[y, x]), 2),
                                    round(float(pred[y, x]), 5), int(lab[y, x])])
    suffix = "" if cut == 0.03 else f"_dense{cut:g}"
    with open(os.path.join(HERE, "results", f"regions{suffix}.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


if __name__ == "__main__":
    main()
