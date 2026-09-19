#!/usr/bin/env python3
"""What holds the other lines against the leading line? (e083, #96; analysis of e081's and e082's censuses)

Run from the repo root: `uv run python experiments/e083_hold/hold.py`

For each ladder run (seeds 9-11: e081's control and `fresh` 0.05, e082's `fresh` 0.2) the land bodies of
every census (36,000-100,000) are read. The leader is the lineage with the most land bodies; every other
line is a local. The map is a torus whose latitude runs from -59 to 87 degrees twice, so a place is its
half (upper: rows 0-255, lower: 256-511), its latitude and, in the upper half, its side:

- **upper west**: the upper half's continent, x 128-327 (its south, tropics and north);
- **upper east**: the upper half's land east of it, x 328 and on (joined to the west in the far south);
- **lower**: the lower half's land (one continent, joined to the upper half across the map's southern edge
  and across the pole).

Writes, into `results/`:

- `regions.csv`: each run and place (half/side x zone: south under -20 degrees, tropics -20 to 10, north
  10 and over): bodies a land cell a census, the leader's share, the ground's and air's mean dryness
  (`_dryness.csv`), and for the leader's and the locals' bodies there: children per 1,000 steps of age
  (bodies aged 50 or more), water, energy, fat, body heat, energy paid to warm and water paid to cool per
  turn, water drunk per turn, the temperature, ground fill, height and crown at their cells, and their
  traits at birth (size, hard, muscle, digestive, sensor), open soft faces, store and meat's share;
- `transect.csv`: the same by strips of 8 rows along the upper west (the boundary) and the lower half;
- `time.csv`: the leader's share in each place per 16,000 steps;
- `maps.csv`: land bodies and the leader's among them on a 64 x 64 map (8 x 8 cells), seed 9.
"""
import csv
import os
import statistics as st
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
EXP = os.path.dirname(HERE)
N, LAT_LO, LAT_HI = 512, -59.4, 87.0
RUNS = [("control", "e081_drink/results/ladder/c1225_life{s}_u0"),
        ("fresh 0.05", "e081_drink/results/ladder/c1225_life{s}_u9.4"),
        ("fresh 0.2", "e082_fresh/results/ladder/c1225_life{s}_u9.4_f0.2")]
SEEDS = (9, 10, 11)
KEEP = ("step", "lineage", "age", "turns", "kids", "water", "energy", "fat", "btemp", "warmed", "cooled", "drank",
        "born_size", "born_hard", "born_muscle", "born_digestive", "born_sensor", "open_soft", "store", "meat",
        "plant", "temp", "moist", "height", "crown", "travel")
MEAN = ("water", "energy", "fat", "btemp", "temp", "moist", "height", "crown",
        "born_size", "born_hard", "born_muscle", "born_digestive", "born_sensor", "open_soft", "store")


def lat_of_row(y):
    return LAT_LO + (LAT_HI - LAT_LO) * (1 - abs(2 * (y + 0.5) / N - 1))


def side(x, y):
    if y >= N // 2:
        return "lower"
    return "upper west" if 128 <= x < 328 else "upper east"


def zone(lat):
    return "south" if lat < -20 else "tropics" if lat < 10 else "north"


def read_dry(pre):
    """(land share, air dryness, ground dryness) per coarse cell (4 x 4 cells)."""
    d = {}
    with open(pre + "_dryness.csv") as f:
        for r in csv.DictReader(f):
            d[(int(r["x"]), int(r["y"]))] = (float(r["land"]), float(r["air"]), float(r["ground"]))
    return d


def place_of_coarse(x, y):
    """The place of a coarse cell's centre."""
    fx, fy = 4 * x + 2, 4 * y + 2
    return side(fx, fy), lat_of_row(fy)


def read_bodies(pre):
    rows = []
    with open(pre + "_agents.csv") as f:
        for r in csv.DictReader(f):
            if r["medium"] != "0":
                continue
            c = int(r["cell"])
            x, y = c % N, c // N
            b = {k: float(r[k]) for k in KEEP if k != "lineage"}
            b["lineage"] = r["lineage"]
            b["side"], b["lat"], b["x"], b["y"] = side(x, y), lat_of_row(y), x, y
            rows.append(b)
    return rows


def group(bs):
    """How a group of bodies does, and what it is."""
    if not bs:
        return {}
    g = {"n": len(bs)}
    old = [b for b in bs if b["age"] >= 50]
    g["kids_1000"] = 1000 * sum(b["kids"] for b in old) / max(sum(b["age"] for b in old), 1)
    for k in MEAN:
        g[k] = st.mean(b[k] for b in bs)
    turns = sum(max(b["turns"], 1) for b in bs)
    for k in ("warmed", "cooled", "drank"):
        g[k + "_turn"] = sum(b[k] for b in bs) / turns
    g["meat_share"] = sum(b["meat"] for b in bs) / max(sum(b["meat"] + b["plant"] for b in bs), 1e-9)
    g["age"] = st.mean(b["age"] for b in bs)
    g["travel"] = st.median(b["travel"] for b in bs)
    return g


def main():
    regions, transect, times, maps = [], [], [], []
    for run, pat in RUNS:
        for s in SEEDS:
            pre = os.path.join(EXP, pat.format(s=s))
            bodies = read_bodies(pre)
            dry = read_dry(pre)
            censuses = len({b["step"] for b in bodies})
            leader = Counter(b["lineage"] for b in bodies).most_common(1)[0][0]
            # land cells and dryness per place and per strip, from the coarse map
            land = defaultdict(float)
            air, ground = defaultdict(float), defaultdict(float)
            for (x, y), (ls, a, gr) in dry.items():
                if ls <= 0:
                    continue
                sd, lat = place_of_coarse(x, y)
                cells = 16 * ls
                for key in ((sd, zone(lat)), (sd, "strip", (4 * y + 2) // 8)):
                    land[key] += cells
                    air[key] += a * cells
                    ground[key] += gr * cells
            by = defaultdict(list)
            for b in bodies:
                by[(b["side"], zone(b["lat"]))].append(b)
                by[(b["side"], "strip", int(b["y"]) // 8)].append(b)
            for key, bs in by.items():
                lead = [b for b in bs if b["lineage"] == leader]
                loc = [b for b in bs if b["lineage"] != leader]
                row = {"run": run, "seed": s, "side": key[0]}
                if key[1] == "strip":
                    row["lat"] = round(lat_of_row(key[2] * 8 + 4), 1)
                else:
                    row["zone"] = key[1]
                cells = land.get(key, 0.0)
                row.update({"land_cells": round(cells), "bodies_cell": len(bs) / censuses / cells if cells else float("nan"),
                            "leader_share": len(lead) / len(bs),
                            "air_dry": air[key] / cells if cells else float("nan"),
                            "ground_dry": ground[key] / cells if cells else float("nan")})
                for name, grp in (("lead", lead), ("loc", loc)):
                    for k, v in group(grp).items():
                        row[f"{name}_{k}"] = v
                (transect if key[1] == "strip" else regions).append(row)
            if s == 9:
                cell = defaultdict(lambda: [0, 0])
                for b in bodies:
                    m = cell[(int(b["x"]) // 8, int(b["y"]) // 8)]
                    m[0] += 1
                    m[1] += b["lineage"] == leader
                maps += [{"run": run, "seed": s, "gx": gx, "gy": gy, "bodies": n, "leader": a} for (gx, gy), (n, a) in sorted(cell.items())]
            win = defaultdict(lambda: [0, 0])
            for b in bodies:
                w = win[(b["side"], zone(b["lat"]), int(b["step"]) // 16000 * 16)]
                w[0] += b["lineage"] == leader
                w[1] += 1
            for (sd, zn, t), (a, n) in sorted(win.items()):
                times.append({"run": run, "seed": s, "side": sd, "zone": zn, "from_k": t, "leader_share": a / n, "bodies": n})
            print(f"{run:10} seed {s} leader {leader}: " + "  ".join(
                f"{r['side']}/{r['zone']} {r['leader_share']:.0%}" for r in regions if r["run"] == run and r["seed"] == s
                and r["zone"] in ("tropics", "north")))
    for name, rows in (("regions", regions), ("transect", transect), ("time", times), ("maps", maps)):
        keys = []
        for r in rows:
            keys += [k for k in r if k not in keys]
        with open(os.path.join(HERE, "results", f"{name}.csv"), "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=keys)
            w.writeheader()
            w.writerows(rows)
    print("-> results/regions.csv, transect.csv, time.csv, maps.csv")


if __name__ == "__main__":
    main()
