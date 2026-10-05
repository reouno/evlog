#!/usr/bin/env python3
"""The islands of terrain candidates (e108): what each seed's ground holds before any climate is run.

Run from the repo root: `uv run python experiments/e108_islands/terrain.py <prefix> ...` on runs made with
`years=0` (each writes the static maps). Prints a row a prefix: the land's share, the islands of 1 km2 and
more (area in km2 and peak in m, largest first), and the narrowest sea between two of the four largest.
"""
import json
import sys

import numpy as np

CELL_KM = 0.125
MIN_CELLS = 64  # 1 km2


def statics(prefix):
    h = json.load(open(prefix + "_maps.json"))
    n, fields, st, years = h["n"], h["fields"], h["static"], h["years"]
    raw = np.fromfile(prefix + "_maps.bin", dtype="<f4")
    k = len(years) * len(fields) * n * n
    return n, {f: raw[k:].reshape(len(st), n * n)[i].reshape(n, n) for i, f in enumerate(st)}


def islands(land):
    """Each land cell's island (4-neighbours, no wrap: the border is sea), islands numbered largest first."""
    n = land.shape[0]
    lab = np.full(land.shape, -1, dtype=int)
    sizes = []
    for y0, x0 in zip(*np.nonzero(land)):
        if lab[y0, x0] >= 0:
            continue
        k, stack, size = len(sizes), [(y0, x0)], 0
        lab[y0, x0] = k
        while stack:
            y, x = stack.pop()
            size += 1
            for yy, xx in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)):
                if 0 <= yy < n and 0 <= xx < n and land[yy, xx] and lab[yy, xx] < 0:
                    lab[yy, xx] = k
                    stack.append((yy, xx))
        sizes.append(size)
    order = np.argsort(sizes)[::-1]
    rank = np.empty(len(sizes), dtype=int)
    rank[order] = np.arange(len(sizes))
    return np.where(lab >= 0, rank[lab], -1), [sizes[i] for i in order]


def steps_from(mask):
    """Cells of 4-neighbour steps from `mask` to every cell."""
    d = np.where(mask, 0, -1)
    front, k = mask.copy(), 0
    while front.any():
        k += 1
        grown = np.zeros_like(front)
        grown[1:, :] |= front[:-1, :]
        grown[:-1, :] |= front[1:, :]
        grown[:, 1:] |= front[:, :-1]
        grown[:, :-1] |= front[:, 1:]
        front = grown & (d < 0)
        d[front] = k
    return d


def gaps(lab, top):
    """The narrowest sea, in km, between each two of the `top` largest islands."""
    out = {}
    for i in range(top):
        d = steps_from(lab == i)
        for j in range(i + 1, top):
            out[(i, j)] = (int(d[lab == j].min()) - 1) * CELL_KM
    return out


def main():
    for prefix in sys.argv[1:]:
        n, st = statics(prefix)
        land = st["sea"] < 0.5
        lab, sizes = islands(land)
        big = [i for i, s in enumerate(sizes) if s >= MIN_CELLS]
        desc = ", ".join(f"{sizes[i] * CELL_KM**2:.0f} km2 / {st['elev'][lab == i].max():.0f} m" for i in big)
        g = gaps(lab, min(4, len(big)))
        slope = st["slope"][land] / (CELL_KM * 1000)
        print(f"{prefix.split('/')[-1]}: land {land.mean():.3f}, {len(big)} islands ({desc}); "
              f"narrowest sea {', '.join(f'{a}-{b} {v:.1f} km' for (a, b), v in g.items())}; "
              f"slope median {np.median(slope):.2f}, p90 {np.percentile(slope, 90):.2f}")


if __name__ == "__main__":
    main()
