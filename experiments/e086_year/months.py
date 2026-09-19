"""e086: what the season is to a body, from `<prefix>_months.bin` (12 months of the last year).

For each year length: the land's lean months (growing index under a bar), the longest lean spell of a
place in steps, the distance over land from a place in a lean month to the nearest place fed that month,
and the temperatures of the lean months. Writes results/months.csv (printed), and for the report
results/spells.csv and results/dist.csv (at the first bar) and results/lean_map.csv (lean months by
4 x 4 block at a year of 1,200, -1 for a block mostly sea).

Run: uv run python experiments/e086_year/months.py
"""
import csv
import os
from collections import deque

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results")
YEARS = [11880, 2400, 1200, 600]
BARS = [0.25, 0.1, 0.5]  # a month is lean under this share of the land's median yearly growing index


def load(year):
    raw = open(os.path.join(RES, f"c1225_d11_y{year}_months.bin"), "rb").read()
    assert raw[:4] == b"E086"
    n, months = np.frombuffer(raw[4:12], dtype="<u4")
    n, months = int(n), int(months)
    elev = np.frombuffer(raw[12:12 + 4 * n * n], dtype="<f4").reshape(n, n)
    rest = np.frombuffer(raw[12 + 4 * n * n:], dtype="<f4").reshape(months, n, n, 3)
    return elev, rest[..., 0], rest[..., 1], rest[..., 2]


def land_distance(land, sources):
    """Steps over land (4 neighbours, torus) from every land cell to the nearest source."""
    n = land.shape[0]
    dist = np.full(land.shape, -1, dtype=np.int32)
    q = deque()
    ys, xs = np.nonzero(sources & land)
    for y, x in zip(ys.tolist(), xs.tolist()):
        dist[y, x] = 0
        q.append((y, x))
    L = land.tolist()
    D = dist.tolist()
    while q:
        y, x = q.popleft()
        d = D[y][x] + 1
        for yy, xx in ((y - 1) % n, x), ((y + 1) % n, x), (y, (x + 1) % n), (y, (x - 1) % n):
            if L[yy][xx] and D[yy][xx] < 0:
                D[yy][xx] = d
                q.append((yy, xx))
    return np.array(D, dtype=np.int32)


def longest_run(lean):
    """The longest circular run of lean months per cell (12 = always lean)."""
    m = lean.shape[0]
    best = np.zeros(lean.shape[1:], dtype=np.int32)
    run = np.zeros(lean.shape[1:], dtype=np.int32)
    for i in range(2 * m):
        run = np.where(lean[i % m], run + 1, 0)
        best = np.maximum(best, np.minimum(run, m))
    return best


rows = []
spells_out, dist_out = [], []
for year in YEARS:
    path = os.path.join(RES, f"c1225_d11_y{year}_months.bin")
    if not os.path.exists(path):
        continue
    elev, temp, low, grow = load(year)
    land = elev >= 0
    yearly = grow.mean(axis=0)
    median = float(np.median(yearly[land]))
    month_steps = year / 12
    dists = {}
    for bar in BARS:
        fed_bar = bar * median
        lean = (grow < fed_bar) & land[None]
        n_lean = lean.sum(axis=0)
        seasonal = land & (n_lean > 0) & (n_lean < 12)
        spell = longest_run(lean)
        row = {
            "year": year, "bar": bar, "median_index": round(median, 4),
            "always_fed": round(float((land & (n_lean == 0)).sum() / land.sum()), 3),
            "seasonal": round(float(seasonal.sum() / land.sum()), 3),
            "never_fed": round(float((land & (n_lean == 12)).sum() / land.sum()), 3),
            "spell_p50_steps": round(float(np.median(spell[seasonal])) * month_steps) if seasonal.any() else 0,
            "spell_p90_steps": round(float(np.percentile(spell[seasonal], 90)) * month_steps) if seasonal.any() else 0,
        }
        if bar == BARS[0]:
            for k in range(1, 12):
                spells_out.append({"year": year, "months": k, "steps": round(k * month_steps), "cells": int((spell[seasonal] == k).sum())})
            if year == 1200:
                b = 4
                nb = land.shape[0] // b
                lm = np.where(land, n_lean, 0).reshape(nb, b, nb, b).sum(axis=(1, 3)) / np.maximum(land.reshape(nb, b, nb, b).sum(axis=(1, 3)), 1)
                lm = np.where(land.reshape(nb, b, nb, b).mean(axis=(1, 3)) >= 0.5, lm, -1)
                np.savetxt(os.path.join(RES, "lean_map.csv"), lm, fmt="%.2f", delimiter=",")
            # the distance from a seasonal place in a lean month to the nearest place fed that month
            ds, t_lean, low_lean = [], [], []
            for m in range(12):
                fed = land & ~lean[m]
                d = land_distance(land, fed)
                sel = seasonal & lean[m]
                ds.append(d[sel])
                t_lean.append(temp[m][sel])
                low_lean.append(low[m][sel])
            ds = np.concatenate(ds)
            ds = ds[ds >= 0]
            for d, c in zip(*np.unique(ds, return_counts=True)):
                dist_out.append({"year": year, "dist": int(d), "count": int(c)})
            t_lean, low_lean = np.concatenate(t_lean), np.concatenate(low_lean)
            row.update({
                "dist_p25": int(np.percentile(ds, 25)), "dist_p50": int(np.median(ds)), "dist_p75": int(np.percentile(ds, 75)),
                "within_10": round(float((ds <= 10).mean()), 3), "within_25": round(float((ds <= 25).mean()), 3),
                "within_50": round(float((ds <= 50).mean()), 3),
                "lean_temp_p50": round(float(np.median(t_lean)), 1), "lean_low_p50": round(float(np.median(low_lean)), 1),
            })
        land_months = land[None] & np.ones((12, 1, 1), dtype=bool)
        row["frost_share"] = round(float((low[land_months.nonzero()] < 0).mean()), 3)
        row["cold_share"] = round(float((temp[land_months.nonzero()] < 5).mean()), 3)
        # the swing of a cell's growing index over its year: the worst month over the mean, on seasonal land
        worst = grow.min(axis=0)
        row["worst_over_mean_p50"] = round(float(np.median(worst[seasonal] / np.maximum(yearly[seasonal], 1e-9))), 3) if seasonal.any() else 0
        # the day's swing on land: mean less the lowest, by month
        row["night_drop_p50"] = round(float(np.median((temp - low)[land_months.nonzero()])), 1)
        rows.append(row)

keys = []
for r in rows:
    for k in r:
        if k not in keys:
            keys.append(k)
with open(os.path.join(RES, "months.csv"), "w", newline="") as f:
    wr = csv.DictWriter(f, fieldnames=keys)
    wr.writeheader()
    wr.writerows(rows)
for name, out in (("spells.csv", spells_out), ("dist.csv", dist_out)):
    with open(os.path.join(RES, name), "w", newline="") as f:
        wr = csv.DictWriter(f, fieldnames=list(out[0]))
        wr.writeheader()
        wr.writerows(out)
for r in rows:
    print(r)
