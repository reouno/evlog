#!/usr/bin/env python3
"""Is the sorting by place slow, or absent? Two readings added after e109's batch was read (#128).

Run from the repo root, after `measure.py`: `uv run python experiments/e109_metres/sorting.py` (two minutes).

H3 failed at year 310 (the leading group against place, NMI 0.12-0.13 against a line of 0.2). This reads what the
line cannot say:

- `results/trend.csv`, a row a run every 30 years: the same NMIs at each map of the leaders, the distinct leading
  genotypes, and the share of neighbouring land cells with the same leader (how coarse the mosaic is).
- `results/leaders.csv`, a row a run: over the `TOP` genotypes leading the most land cells and the nine places of
  rain x temperature (terciles), how much of the difference in standing biomass between (leader, place) pairs is
  the leader's, the place's, and neither's alone (the better form changing with the place); and how much of a
  leader's ground lies in its one most held place.

Both are appended to `results/provenance.csv`.
"""
import collections
import csv
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.argv = sys.argv[:1]
import measure as M  # noqa: E402
from analysis.groups import group, vectors  # noqa: E402

EVERY = 30    # years between the trend's rows
TOP = 20      # leaders read
MIN = 20      # cells a (leader, place) pair needs to be read
FLIP = 0.2    # log biomass by which the better of two leaders must change both ways


def write(name, table):
    with open(os.path.join(M.RESULTS, name), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(table[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(table)


def main():
    trend, leaders = [], []
    for run in M.RUNS:
        prefix = os.path.join(M.RESULTS, run)
        _, ym, st = M.load_maps(prefix)
        mean = {f: v.mean(axis=0) for f, v in ym.items()}
        land = st["sea"] == 0
        n = int(round(np.sqrt(land.size)))

        def terc(v):
            lo, hi = np.percentile(v[land], [100 / 3, 200 / 3])
            return np.where(v < lo, 0, np.where(v < hi, 1, 2))

        place = M.places(mean, st)
        isles = terc(mean["rain"]) * 9 + terc(mean["temp"]) * 3 + terc(mean["light"])
        isl, _ = M.islands(land.reshape(n, n))
        lyears, lead, none = M.load_lead(prefix)
        by = collections.defaultdict(list)
        for r in csv.DictReader(open(prefix + "_census.csv")):
            if int(r["year"]) in lyears:
                by[int(r["year"])].append(r)
        for k, y in enumerate(lyears):
            if (y - lyears[0]) % EVERY and y != lyears[-1]:
                continue
            rows = by[y]
            x, w = vectors(rows)
            g = group(x, w)
            idg = {int(rows[i]["id"]): int(g[i]) for i in range(len(rows))}
            lm = lead[k]
            has = land & (lm != none) & np.isin(lm, list(idg))
            grp = np.array([idg[int(v)] for v in lm[has]])
            grid = np.where(has, lm.astype(np.int64), -1).reshape(n, n)
            pairs = [(grid[:, 1:], grid[:, :-1]), (grid[1:, :], grid[:-1, :])]
            same = sum(((a == b) & (a >= 0)).sum() for a, b in pairs) / sum(((a >= 0) & (b >= 0)).sum() for a, b in pairs)
            trend.append({"run": run, "year": y, "leaders": int(len(np.unique(lm[has]))), "leading_groups": int(len(np.unique(grp))),
                          "nmi_group_place": M.nmi(grp, place[has]), "nmi_group_isles": M.nmi(grp, isles[has]),
                          "nmi_group_island": M.nmi(grp, isl[has]), "same_leader_neighbours": float(same)})

        # the last year: do leaders stand differently in different places?
        lm = lead[-1]
        bins = terc(mean["rain"]) * 3 + terc(mean["temp"])
        bio = np.log(np.maximum(ym["biomass"][-1], 1e-4))
        ids, cnt = np.unique(lm[land & (lm != none)], return_counts=True)
        order = np.argsort(-cnt)[:TOP]
        top = ids[order]
        cellmean = {}
        for gi, gid in enumerate(top):
            for b in range(9):
                m = land & (lm == gid) & (bins == b)
                if m.sum() >= MIN:
                    cellmean[(gi, b)] = (float(bio[m].mean()), int(m.sum()))
        gi = np.array([k[0] for k in cellmean])
        bi = np.array([k[1] for k in cellmean])
        yv = np.array([v[0] for v in cellmean.values()])
        wv = np.array([v[1] for v in cellmean.values()], dtype=float)
        x = np.zeros((len(yv), TOP + 9))
        x[np.arange(len(yv)), gi] = 1
        x[np.arange(len(yv)), TOP + bi] = 1
        sw = np.sqrt(wv)
        total = (wv * (yv - np.average(yv, weights=wv)) ** 2).sum()

        def left(cols):
            c, *_ = np.linalg.lstsq(x[:, cols] * sw[:, None], yv * sw, rcond=None)
            return (wv * (yv - x[:, cols] @ c) ** 2).sum() / total

        flips = shared = 0
        for a in range(TOP):
            for b in range(a + 1, TOP):
                d = [cellmean[(a, k)][0] - cellmean[(b, k)][0] for k in range(9) if (a, k) in cellmean and (b, k) in cellmean]
                if len(d) >= 2:
                    shared += 1
                    flips += min(d) < -FLIP and max(d) > FLIP
        modal = [max(((lm == gid) & land & (bins == b)).sum() for b in range(9)) / ((lm == gid) & land).sum() for gid in top]
        leaders.append({"run": run, "year": lyears[-1], "top_share_of_land": float(cnt[order].sum() / land.sum()), "pairs_read": len(yv),
                        "by_leader": 1 - left(list(range(TOP))), "by_place": 1 - left(list(range(TOP, TOP + 9))),
                        "by_neither_alone": left(list(range(TOP + 9))), "leader_pairs": shared, "pairs_that_flip": int(flips),
                        "modal_place_share": float(np.median(modal))})
    write("trend.csv", trend)
    write("leaders.csv", leaders)
    prov = list(csv.DictReader(open(os.path.join(M.RESULTS, "provenance.csv"))))
    prov = [r for r in prov if r["reading"] == "measure"]
    for run in M.RUNS:
        prov.append({"reading": "sorting (added after the batch)", "run": run, "census_years": f"leaders' maps every {EVERY} years",
                     "thresholds": f"places and groups as measure; the {TOP} genotypes leading the most land cells in the last year; nine places = "
                                   f"terciles of rain x temperature; a (leader, place) pair read from {MIN} cells; log of the last year's biomass, "
                                   f"floor 1e-4; a flip: the better of two leaders changes by {FLIP} both ways"})
    write("provenance.csv", prov)
    for t in (trend, leaders):
        for r in t:
            print("  ".join(f"{k} {v:.3g}" if isinstance(v, float) else f"{k} {v}" for k, v in r.items()))


if __name__ == "__main__":
    main()
