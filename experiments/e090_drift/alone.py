#!/usr/bin/env python3
"""Read e090's stage B check (#100 D): where the drifting seed lands, and whether stage B still passes.

Run from the repo root: `uv run python experiments/e090_drift/alone.py`
Reads `results/alone/c1225_life9_d<drift>_{log,bands}.csv` and `_cells.bin` (e090's map: the magic
"E090CELL", the side, then elevation, latitude, wood, grass, seed, four quarters of fill, of temperature
and of rain, and the year each cell last burnt, all as f32). Prints, for every drift:

- **the land**: grass (leaf) and seed standing, a land cell's mean over the two years, against `seed_drift` 0;
  seed set, sprouted and sunk in the water a step;
- **stage B**: each producer's share of the standing matter (grass with its seed), its least total over the
  run, the land burnt a year, the ledger's worst drift;
- **where the seed lands** (the map at the end): the share of the land's seed on cells whose grass is under a
  tenth of the land's mean (ground too dry, too cold or burnt for grass), the seed on them per cell, the land
  cells holding seed over grass (the places a body could live on seed alone) and their share of the land, and
  the seed by band.

Writes `results/alone.csv` (a row a run) and `results/alone_bands.csv` (run x band x quarter).
"""
import csv
import os
import struct

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results", "alone")
YEAR = 11880
RUNS = ["d0", "d0.01", "d0.02", "d0.05", "d0.2"]
LAND = 110625


def rows(path):
    with open(path) as f:
        return list(csv.DictReader(f))


def quarter(step):
    return int(((step - 500) / YEAR + 0.125) % 1.0 * 4) % 4


def cells(path):
    """The map: every field as a list of f32, by name."""
    b = open(path, "rb").read()
    assert b[:8] == b"E090CELL", b[:8]
    n = struct.unpack_from("<I", b, 8)[0]
    names = ["elev", "lat", "wood", "grass", "seed"] + [f"{k}{q}" for k in ("fill", "temp", "rain") for q in range(4)] + ["burnt"]
    out, at = {}, 12
    for name in names:
        out[name] = struct.unpack_from(f"<{n * n}f", b, at)
        at += 4 * n * n
    return out


def main():
    out, bands_out = [], []
    ctrl = None
    for run in RUNS:
        pre = os.path.join(RES, f"c1225_life9_{run}")
        log = rows(pre + "_log.csv")
        n = len(log)
        mean = lambda k: sum(float(r[k]) for r in log) / n  # noqa: E731
        grass, seed = mean("grass") / LAND, mean("seed") / LAND
        wood, algae = mean("wood"), mean("algae")
        standing = mean("grass") + mean("seed") + wood + algae
        years = int(log[-1]["step"]) / YEAR
        row = {
            "run": run,
            "grass": grass,
            "seed": seed,
            "seed_per_grass": seed / grass,
            "seed_set": mean("seed_set"),
            "sprouted": mean("sprouted"),
            "seed_wet": mean("seed_wet"),
            "sank_share": mean("seed_wet") / mean("seed_set") if mean("seed_set") else 0.0,
            "share_grass": (mean("grass") + mean("seed")) / standing,
            "share_wood": wood / standing,
            "share_algae": algae / standing,
            "min_grass": min(float(r["grass"]) for r in log),
            "min_wood": min(float(r["wood"]) for r in log),
            "min_algae": min(float(r["algae"]) for r in log),
            "burnt_a_year": sum(float(r["burnt"]) for r in log) / years,
            "matter_err": max(abs(float(r["matter_err"])) for r in log),
        }
        if ctrl is None:
            ctrl = row
        row["grass_vs_d0"] = grass / ctrl["grass"]

        # The map at the end of the run: where the seed lies against where the grass stands.
        m = cells(pre + "_cells.bin")
        land = [i for i in range(len(m["grass"])) if m["elev"][i] >= 0]
        gs = [m["grass"][i] for i in land]
        sd = [m["seed"][i] for i in land]
        mean_grass = sum(gs) / len(land)
        thin = [i for i, g in enumerate(gs) if g < 0.1 * mean_grass]
        over = [i for i in range(len(land)) if sd[i] > gs[i] and sd[i] > 0.01]
        row["thin_cells"] = len(thin) / len(land)
        row["seed_on_thin"] = sum(sd[i] for i in thin) / sum(sd) if sum(sd) else 0.0
        row["seed_per_thin_cell"] = sum(sd[i] for i in thin) / max(len(thin), 1)
        row["over_cells"] = len(over) / len(land)
        row["seed_on_over"] = sum(sd[i] for i in over) / sum(sd) if sum(sd) else 0.0
        out.append(row)

        acc = {}
        for r in rows(pre + "_bands.csv"):
            k = (int(r["lat"]), quarter(int(r["step"])))
            a = acc.setdefault(k, [0.0] * 6)
            a[0] += float(r["grass"])
            a[1] += float(r["seed"])
            a[2] += float(r["grown"])
            a[3] += float(r["sprouted"])
            a[4] += 1
            a[5] += float(r["cells"])
        for (lat, q), a in sorted(acc.items()):
            bands_out.append({"run": run, "lat": lat, "quarter": q, "grass": a[0] / a[5], "seed": a[1] / a[5],
                              "seed_per_grass": a[1] / a[0] if a[0] > 0 else 0.0,
                              "sprout_share": a[3] / (a[2] + a[3]) if a[2] + a[3] > 0 else 0.0})

    for row in out:
        print(f"{row['run']:6} grass {row['grass']:.3f} ({row['grass_vs_d0']:.2f}) seed {row['seed']:.3f} "
              f"({row['seed_per_grass']:.2f} of grass), set {row['seed_set']:.1f} sprouted {row['sprouted']:.1f} "
              f"sank {row['seed_wet']:.2f} ({row['sank_share']:.1%} of what is set) a step")
        print(f"       shares grass {row['share_grass']:.3f} wood {row['share_wood']:.3f} algae {row['share_algae']:.3f}; "
              f"least {row['min_grass']:.0f}/{row['min_wood']:.0f}/{row['min_algae']:.0f}; "
              f"burnt {row['burnt_a_year']:.3f} of the land a year; matter err {row['matter_err']:.1e}")
        print(f"       thin-grass cells {row['thin_cells']:.1%} of the land hold {row['seed_on_thin']:.1%} of the seed "
              f"({row['seed_per_thin_cell']:.2f} a cell); seed over grass on {row['over_cells']:.1%} of the land, "
              f"{row['seed_on_over']:.1%} of the seed")
    print("\nseed | grass a land cell, by band (rows) and quarter (N spring, summer, autumn, winter)")
    for run in RUNS:
        print(f"  {run}")
        for lat in sorted({b["lat"] for b in bands_out}):
            cs = sorted([b for b in bands_out if b["run"] == run and b["lat"] == lat], key=lambda b: b["quarter"])
            print(f"   {lat:+4d}  " + "  ".join(f"{b['seed']:5.2f}|{b['grass']:4.2f}" for b in cs))

    def write(name, data):
        with open(os.path.join(HERE, "results", name), "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(data[0].keys()))
            w.writeheader()
            for d in data:
                w.writerow({k: (f"{v:.5g}" if isinstance(v, float) else v) for k, v in d.items()})

    write("alone.csv", out)
    write("alone_bands.csv", bands_out)


if __name__ == "__main__":
    main()
