#!/usr/bin/env python3
"""Read e079's runs of the producers alone (#91 step 2): where stands stand, the ground's fill by
season, and the rain.

Run from the repo root: `uv run python experiments/e079_crown/sweep.py experiments/e079_crown/results/alone`
For every run (`*_cells.bin`, written with `cell_map` 1) it prints, with 20-50 degrees of latitude
read in both hemispheres and "summer" the hemisphere's own (quarter 1 in the north, 3 in the south):

- **stands** (hypothesis 1): land cells with wood 1 or more at the end, all and at 20-50 degrees; the
  lawn there (wood under 0.1) and its share within REACH cells of a stand;
- **the floor** (2): the mean ground fill of the stands and of the lawn at 20-50 degrees, in summer,
  winter and at the equinoxes;
- **the counterweights** (3): the rain a year on the control's lawn at 20-50 degrees (the same cells
  in every run, so that what S1 takes from the lawn's air is read apart from where the lawn moved),
  the rain on all the land, and the share of the land burnt a year;
- **settling**: the stand cells at 20-50 degrees in the last three years of the settled world's build.

Also the stands' share of the land by 10-degree band. Writes `results/sweep_<dir name>.csv`, and for the
report (the cell maps are not committed): `results/sweep_<dir name>_bands.csv`, each run's land by
10-degree band (the stands' and the lawn's share, the rain a year and the ground's mean fill), and
`results/sweep_<dir name>_maps.csv`, the runs in MAP_RUNS in blocks of 4 x 4 cells (their land's share
and its stands' and lawn's share).
"""
import csv
import glob
import os
import re
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
REACH = 25  # cells: a grown body's travel in a life (22-28, balance.md section 1)
STAND, LAWN = 1.0, 0.1
YEAR, TICK = 11880, 10
CONTROL = "w0r0"
MAP_RUNS = ("w0r0", "w1r0.5", "w1r1", "w2r1")
BLOCK = 4


def read_cells(path):
    b = open(path, "rb").read()
    assert b[:8] == b"E079CELL"
    n = int(np.frombuffer(b[8:12], "<u4")[0])
    a = np.frombuffer(b[12:], "<f4").reshape(-1, n, n)
    m = {"elev": a[0], "lat": a[1], "wood": a[2], "grass": a[3]}
    m["fill"], m["temp"], m["rain"] = a[4:8], a[8:12], a[12:16]
    m["burnt"] = a[16]
    return m


def near(mask, r):
    """Cells within r (Euclidean, on the torus) of a cell of the mask."""
    out = np.zeros_like(mask)
    for dy in range(-r, r + 1):
        w = int((r * r - dy * dy) ** 0.5)
        row = np.roll(mask, dy, axis=0)
        # a row of the disk: a run of 2w+1 shifts in x, as a running OR
        acc = np.zeros_like(mask)
        for dx in range(-w, w + 1):
            acc |= np.roll(row, dx, axis=1)
        out |= acc
    return out


def season_masks(lat):
    """Per quarter, the cells whose hemisphere is in summer, in winter, or at an equinox."""
    north = lat >= 0
    summer = [np.zeros_like(north), north, np.zeros_like(north), ~north]
    winter = [np.zeros_like(north), ~north, np.zeros_like(north), north]
    return summer, winter


def by_season(field, sel, lat):
    """The mean of a quarterly field over the cells `sel`, in their summer, winter and equinoxes."""
    summer, winter = season_masks(lat)
    s = [field[q][sel & summer[q]] for q in (1, 3)]
    w = [field[q][sel & winter[q]] for q in (1, 3)]
    e = [field[q][sel] for q in (0, 2)]
    mean = lambda parts: float(np.concatenate(parts).mean()) if sum(p.size for p in parts) else float("nan")
    return mean(s), mean(w), mean(e)


def settling(log):
    ys = []
    if os.path.exists(log):
        for line in open(log):
            m = re.match(r"settling year (\d+): wood ([\d.]+) a land cell, (\d+) stand cells, (\d+) of them", line)
            if m:
                ys.append((int(m[1]), float(m[2]), int(m[3]), int(m[4])))
    return ys


def burnt_a_year(m, land, built):
    """The share of the land burnt a year over the run: the cells whose last fire came after the
    `built` years of the settled world (the log's column rounds 0.2% a year to nothing)."""
    run_years = int(m["burnt"][land].max()) - built
    return float((m["burnt"][land] > built).sum() / land.sum() / max(run_years, 1))


def main(dirs):
    runs = {}
    for d in dirs:
        for path in sorted(glob.glob(os.path.join(d, "*_cells.bin"))):
            name = os.path.basename(path)[: -len("_cells.bin")].split("_")[-1]
            runs[name] = (path[: -len("_cells.bin")], read_cells(path))
    assert CONTROL in runs, f"no control {CONTROL}"
    ctl = runs[CONTROL][1]
    land = ctl["elev"] >= 0
    lat = ctl["lat"]
    mid = land & (np.abs(lat) >= 20) & (np.abs(lat) < 50)
    ctl_lawn = mid & (ctl["wood"] < LAWN)
    per_year = YEAR / TICK
    out = []
    print(f"{'run':>5} {'stands':>6} {'s20-50':>6} {'lawn20-50':>9} {'near':>5} "
          f"{'fill stand S/W/E':>17} {'fill lawn S/W/E':>17} {'rain ctl-lawn':>13} {'rain land':>9} {'burnt/yr':>8}  settling s20-50")
    for name, (pre, m) in runs.items():
        wood = m["wood"]
        stand = land & (wood >= STAND)
        lawn = mid & (wood < LAWN)
        s_mid = stand & mid
        close = near(stand, REACH)
        near_share = float((lawn & close).sum() / max(lawn.sum(), 1))
        fs = by_season(m["fill"], s_mid, lat)
        fl = by_season(m["fill"], lawn, lat)
        rain_ctl_lawn = float(np.mean([m["rain"][q][ctl_lawn].mean() for q in range(4)]) * per_year)
        rain_land = float(np.mean([m["rain"][q][land].mean() for q in range(4)]) * per_year)
        st = settling(pre + ".log")
        burnt = burnt_a_year(m, land, len(st) or 17)
        tail = " ".join(f"{y[3]}" for y in st[-3:])
        print(f"{name:>5} {stand.sum():6d} {s_mid.sum():6d} {lawn.sum():9d} {near_share:5.2f} "
              f"{fs[0]:5.2f}/{fs[1]:4.2f}/{fs[2]:4.2f}  {fl[0]:5.2f}/{fl[1]:4.2f}/{fl[2]:4.2f}  {rain_ctl_lawn:13.0f} {rain_land:9.0f} {burnt:8.4f}  {tail}")
        prof = []
        for lo in range(-60, 90, 10):
            band = land & (lat >= lo) & (lat < lo + 10)
            prof.append(float((band & stand).sum() / max(band.sum(), 1)))
        out.append({
            "run": name, "stands": int(stand.sum()), "stands_mid": int(s_mid.sum()), "lawn_mid": int(lawn.sum()),
            "near": round(near_share, 4),
            "fill_stand_summer": round(fs[0], 4), "fill_stand_winter": round(fs[1], 4), "fill_stand_equinox": round(fs[2], 4),
            "fill_lawn_summer": round(fl[0], 4), "fill_lawn_winter": round(fl[1], 4), "fill_lawn_equinox": round(fl[2], 4),
            "rain_ctl_lawn": round(rain_ctl_lawn, 1), "rain_land": round(rain_land, 1), "burnt": round(burnt, 5),
            "settling_mid": " ".join(str(y[3]) for y in st),
            **{f"stand_share_{lo}": round(v, 4) for lo, v in zip(range(-60, 90, 10), prof)},
        })
    print("\nstands' share of the land by band (lower edge):")
    print("       " + " ".join(f"{lo:>5}" for lo in range(-60, 90, 10)))
    for r in out:
        print(f"{r['run']:>6} " + " ".join(f"{r[f'stand_share_{lo}']:5.2f}" for lo in range(-60, 90, 10)))
    base = os.path.join(HERE, "results", f"sweep_{os.path.basename(os.path.normpath(dirs[0]))}")
    with open(base + ".csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0]))
        w.writeheader()
        w.writerows(out)
    with open(base + "_bands.csv", "w") as f:
        f.write("run,lat,land,stand,lawn,rain,fill\n")
        for name, (_, m) in runs.items():
            rain, fill = m["rain"].mean(axis=0) * per_year, m["fill"].mean(axis=0)
            for lo in range(-60, 90, 10):
                band = land & (lat >= lo) & (lat < lo + 10)
                k = max(int(band.sum()), 1)
                f.write(f"{name},{lo},{int(band.sum())},{(band & (m['wood'] >= STAND)).sum() / k:.4f},"
                        f"{(band & (m['wood'] < LAWN)).sum() / k:.4f},{rain[band].mean():.1f},{fill[band].mean():.4f}\n")
    with open(base + "_maps.csv", "w") as f:
        f.write("run,bx,by,land,stand,lawn\n")
        n = land.shape[0]
        blocks = lambda a: a.reshape(n // BLOCK, BLOCK, n // BLOCK, BLOCK).sum(axis=(1, 3))
        cells = blocks(land.astype(float))
        for name in MAP_RUNS:
            if name not in runs:
                continue
            wood = runs[name][1]["wood"]
            st, lw = blocks((land & (wood >= STAND)).astype(float)), blocks((land & (wood < LAWN)).astype(float))
            for by in range(n // BLOCK):
                for bx in range(n // BLOCK):
                    c = cells[by, bx]
                    if c:
                        f.write(f"{name},{bx},{by},{c / BLOCK**2:.3f},{st[by, bx] / c:.3f},{lw[by, bx] / c:.3f}\n")
    print(f"\nwrote {base}.csv, _bands.csv and _maps.csv")


if __name__ == "__main__":
    main(sys.argv[1:])
