#!/usr/bin/env python3
"""Read e108's world against its five hypotheses (#127): e102's readings, on the small world.

Run from the repo root: `uv run python experiments/e108_islands/measure.py [prefix]` (seconds).

Reads `<prefix>_log.csv` (a row a year) and `<prefix>_maps.bin` + `_maps.json` (the last years' annual maps and
the static ones). Writes `results/measure.csv` (one row: every reading), `results/places.csv` (each place type's
area under each classification), `results/islands.csv` (a row an island of 1 km2 or more) and the `measure` rows
of `results/provenance.csv`. The bands of a place are e102's, unchanged.
"""
import csv
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from terrain import CELL_KM, MIN_CELLS, islands, steps_from  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
PREFIX = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "results", "isles1")

UPDATE_S = 10 / 74.7 * 86400                                 # an update, in seconds
STREAM = 0.1 * UPDATE_S / (CELL_KM * 1000) ** 2 * 1000       # mm an update out of a cell: 0.1 m3/s (H2)
RIVER = 10 * STREAM                                          # 1 m3/s, read beside it
RIVER_SHARE = 0.01   # of the land (H2)
DRIFT = 0.01         # a year, of the land's water (H2)
SPAN = 4.0           # p90 / p10 of A:B and of A + B (H3)
CORR = (0.2, 0.95)   # consecutive years' land rain (H4)
TREND = 0.1          # C a year, land temperature over the read years (H4)
PLANET = 15.4        # e102's effective places on the land (H5)
LAKE = 0.5           # share of the year a cell is a lake
SHALLOW = 200.0      # m of sea over the shelf (e061)
COLD, HOT = 5.0, 20.0            # C, annual mean (e102)
DRY, WET = 1 / 3, 2 / 3          # the soil's mean fill (e102)
RATIO = (0.5, 2.0)               # A:B bands (e102)
BIG = 20.0           # km2: an island large enough to hold a line of bodies
LOW = 200.0          # m: the lowland whose windward and lee halves are compared
WIND_TO = 200.0      # degrees: the wind's mean direction (worlds/small.params)
HEIGHTS = [0, 100, 300, 600, 1000, 3000]  # m: bands within which rain is compared


def load(prefix):
    h = json.load(open(prefix + "_maps.json"))
    n, fields, statics, years = h["n"], h["fields"], h["static"], h["years"]
    cells = n * n
    raw = np.fromfile(prefix + "_maps.bin", dtype="<f4")
    k = len(years) * len(fields) * cells
    yearly = raw[:k].reshape(len(years), len(fields), cells)
    st = raw[k:].reshape(len(statics), cells)
    return n, years, {f: yearly[:, i] for i, f in enumerate(fields)}, {f: st[i] for i, f in enumerate(statics)}


def hill(areas):
    p = np.array([a for a in areas if a > 0], dtype=float)
    p /= p.sum()
    return float(np.exp(-(p * np.log(p)).sum()))


def places(mean, st, chem, rivers):
    """A label per cell: medium x temperature (x moisture on land) (x A:B x fertility with `chem`). e102's."""
    sea = st["sea"] > 0
    t = mean["temp"]
    tb = np.where(t < COLD, 0, np.where(t < HOT, 1, 2))
    fill = mean["fill"]
    mb = np.where(fill < DRY, 0, np.where(fill < WET, 1, 2))
    lake = (mean["lake"] >= LAKE) & ~sea
    river = (mean["discharge"] >= STREAM) & ~sea & ~lake if rivers else np.zeros_like(sea)
    medium = np.where(sea, np.where(-st["elev"] < SHALLOW, 1, 2), np.where(lake, 3, np.where(river, 4, 0)))
    label = medium * 100 + tb * 10 + np.where(medium == 0, mb, 0)
    if chem:
        ab = mean["a"] / np.maximum(mean["b"], 1e-12)
        rb = np.where(ab < RATIO[0], 0, np.where(ab < RATIO[1], 1, 2))
        land = ~sea
        tot = mean["a"] + mean["b"]
        fb = (tot >= np.median(tot[land])).astype(int)
        label = label * 100 + np.where(land, rb * 10 + fb, 0)
    return label


def main():
    log = list(csv.DictReader(open(PREFIX + "_log.csv")))
    n, years, y, st = load(PREFIX)
    sea = st["sea"] > 0
    land = ~sea
    mean = {f: v.mean(axis=0) for f, v in y.items()}
    last = {f: v[-1] for f, v in y.items()}
    read = [r for r in log if int(r["year"]) in years]
    out = {"years_read": f"{years[0]}-{years[-1]}", "land_cells": int(land.sum()), "land_km2": float(land.sum() * CELL_KM**2)}

    # H1: the ledgers
    for k in ("water_err", "a_err", "b_err", "air_err"):
        out[k] = max(float(r[k]) for r in log)

    # H2: rivers, and the land's water steady; #118: what of the rain runs off
    q = mean["discharge"][land]
    out["stream_share"] = float((q >= STREAM).mean())
    out["river_share"] = float((q >= RIVER).mean())
    out["largest_river_m3s"] = float(q.max() / STREAM * 0.1)
    lw = np.array([float(r["land_water"]) for r in read])
    out["land_water_drift"] = float(np.polyfit(np.arange(len(lw)), lw, 1)[0] / lw.mean())
    out["to_sea_mm"] = float(np.mean([float(r["to_sea"]) for r in read]))
    out["land_rain_mm"] = float(np.mean([float(r["land_rain"]) for r in read]))
    out["land_evap_mm"] = float(np.mean([float(r["land_evap"]) for r in read]))
    out["runoff_ratio"] = out["to_sea_mm"] / out["land_rain_mm"]
    out["lake_cells"] = int(((mean["lake"] >= LAKE) & land).sum())

    # H3: chemistry across the land (the last year's soil)
    a, b = last["a"][land], last["b"][land]
    ratio = a / np.maximum(b, 1e-12)
    tot = a + b
    p10, p90 = np.percentile(ratio, [10, 90])
    out["ab_p10"], out["ab_p90"], out["ab_span"] = float(p10), float(p90), float(p90 / max(p10, 1e-12))
    f10, f90 = np.percentile(tot, [10, 90])
    out["ab_sum_p10"], out["ab_sum_p90"], out["fertility_span"] = float(f10), float(f90), float(f90 / max(f10, 1e-12))
    a_drift = [float(r["a"]) for r in read]
    out["a_drift"] = float(np.polyfit(np.arange(len(a_drift)), a_drift, 1)[0] / np.mean(a_drift))

    # H4: years differ, without drifting
    rain = y["rain"][:, land]
    cs = [float(np.corrcoef(rain[i], rain[i + 1])[0, 1]) for i in range(len(years) - 1)]
    out["rain_corr_mean"], out["rain_corr_min"], out["rain_corr_max"] = float(np.mean(cs)), float(min(cs)), float(max(cs))
    tl = [float(r["land_temp"]) for r in read]
    out["temp_trend"] = float(np.polyfit(np.arange(len(tl)), tl, 1)[0])
    anom = rain / np.maximum(rain.mean(axis=0, keepdims=True), 1e-9)
    out["rain_cv_median"] = float(np.median(anom.std(axis=0)))
    dev = rain - rain.mean(axis=0, keepdims=True)
    out["rain_anom_corr"] = float(np.mean([np.corrcoef(dev[i], dev[i + 1])[0, 1] for i in range(len(years) - 1)]))
    out["dry_year_share"] = float((anom < 0.8).mean())  # cell-years under 80% of the cell's mean rain
    lr = np.array([float(r["land_rain"]) for r in read])
    out["land_rain_cv"] = float(lr.std() / lr.mean())  # the whole land's rain, year against year

    # H5: places by e102's classifications of the mean of the read years
    rows = []
    for name, chem, rivers in [("e061", False, False), ("rivers", False, True), ("chemistry", True, True)]:
        lab = places(mean, st, chem, rivers)
        u, c = np.unique(lab, return_counts=True)
        out[f"places_{name}"] = hill(c)
        out[f"types_{name}"] = int(len(u))
        rows += [{"classification": name, "place": int(k), "cells": int(v), "share": v / lab.size} for k, v in zip(u, c)]
    for name, chem, rivers in [("e061", False, False), ("chemistry", True, True)]:
        lab = places(mean, st, chem, rivers)[land]
        out[f"land_places_{name}"] = hill(np.unique(lab, return_counts=True)[1])
    # which of e102's bands this land holds: the share of the land in each band of temperature and of moisture
    t, fill = mean["temp"][land], mean["fill"][land]
    out["temp_cold"], out["temp_mid"], out["temp_hot"] = float((t < COLD).mean()), float(((t >= COLD) & (t < HOT)).mean()), float((t >= HOT).mean())
    out["fill_dry"], out["fill_mid"], out["fill_wet"] = float((fill < DRY).mean()), float(((fill >= DRY) & (fill < WET)).mean()), float((fill >= WET).mean())

    # Beside H5: what differs over the land
    e = st["elev"]
    mrain, mlight = mean["rain"], mean["light"]
    for name, v, (lo, hi) in [("temp", mean["temp"], (5, 95)), ("rain", mrain, (10, 90)), ("light", mlight, (5, 95)), ("fill", mean["fill"], (5, 95))]:
        a_, b_ = np.percentile(v[land], [lo, hi])
        out[f"{name}_p{lo}"], out[f"{name}_p{hi}"] = float(a_), float(b_)
    out["swing_median"] = float(np.median(mean["swing"][land]))
    out["sea_temp"] = float(mean["temp"][sea].mean())
    out["sea_rain_mm"] = float(mrain[sea].mean())
    out["rain_height_corr"] = float(np.corrcoef(mrain[land], e[land])[0, 1])
    for lo, hi in zip(HEIGHTS, HEIGHTS[1:]):
        m = land & (e >= lo) & (e < hi)
        p10, p50, p90 = np.percentile(mrain[m], [10, 50, 90])
        out[f"h{lo}_share"], out[f"h{lo}_rain_p10"], out[f"h{lo}_rain_p50"], out[f"h{lo}_rain_p90"] = float(m.sum() / land.sum()), float(p10), float(p50), float(p90)
    slope = st["slope"][land] / (CELL_KM * 1000)
    out["slope_median"], out["slope_p90"] = float(np.median(slope)), float(np.percentile(slope, 90))

    # The islands: what each holds, and the sea between the large ones
    grid = lambda v: v.reshape(n, n)
    lab, sizes = islands(grid(land))
    yy, xx = np.mgrid[0:n, 0:n]
    up = xx * -np.cos(np.radians(WIND_TO)) + yy * -np.sin(np.radians(WIND_TO))  # larger: further upwind
    chem = grid(places(mean, st, True, True))
    isl = []
    for i, s in enumerate(sizes):
        if s < MIN_CELLS:
            break
        m = lab == i
        mf = m.reshape(-1)
        low = m & (grid(e) < LOW)
        mid = np.median(up[m])
        ww, ll = low & (up > mid), low & (up <= mid)
        ab = mean["a"][mf] / np.maximum(mean["b"][mf], 1e-12)
        isl.append({
            "island": i, "km2": s * CELL_KM**2, "peak_m": float(e[mf].max()),
            "temp_min": float(mean["temp"][mf].min()), "temp_max": float(mean["temp"][mf].max()),
            "rain_mean": float(mrain[mf].mean()), "rain_p10": float(np.percentile(mrain[mf], 10)), "rain_p90": float(np.percentile(mrain[mf], 90)),
            "low_windward_rain": float(grid(mrain)[ww].mean()) if ww.any() else float("nan"),
            "low_lee_rain": float(grid(mrain)[ll].mean()) if ll.any() else float("nan"),
            "fill_min": float(mean["fill"][mf].min()), "ab_median": float(np.median(ab)),
            "streams": int((mean["discharge"][mf] >= STREAM).sum()), "places": hill(np.unique(chem[m], return_counts=True)[1]),
        })
    big = [r["island"] for r in isl if r["km2"] >= BIG]
    out["islands"], out["islands_big"] = len(isl), len(big)
    gaps = []
    for i in big:
        d = steps_from(lab == i)
        gaps += [(int(d[lab == j].min()) - 1) * CELL_KM for j in big if j > i]
    if gaps:
        out["sea_narrowest_km"], out["sea_widest_km"] = float(min(gaps)), float(max(gaps))
    out["low_windward_over_lee"] = float(np.nanmedian([r["low_windward_rain"] / r["low_lee_rain"] for r in isl if r["km2"] >= BIG]))

    verdicts = {
        "H1": all(out[k] < 1e-9 for k in ("water_err", "a_err", "b_err", "air_err")),
        "H2": out["stream_share"] >= RIVER_SHARE and abs(out["land_water_drift"]) < DRIFT,
        "H3": out["ab_span"] >= SPAN and out["fertility_span"] >= SPAN,
        "H4": CORR[0] <= out["rain_corr_mean"] <= CORR[1] and abs(out["temp_trend"]) < TREND,
        "H5": out["land_places_chemistry"] >= PLANET,
    }
    out.update({k: "yes" if v else "no" for k, v in verdicts.items()})
    res = os.path.join(HERE, "results")
    for name, table in [("measure.csv", [out]), ("places.csv", rows), ("islands.csv", isl)]:
        with open(os.path.join(res, name), "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(table[0]), lineterminator="\n")
            w.writeheader()
            w.writerows(table)
    prov = [{"reading": "measure", "run": os.path.basename(PREFIX), "from": years[0], "to": years[-1], "items": len(years),
             "thresholds": f"stream {STREAM:.1f} mm/update (0.1 m3/s) on {RIVER_SHARE:.0%} of land, river {RIVER:.0f} (1 m3/s); "
                           f"drift {DRIFT:.0%}/yr; span x{SPAN}; rain corr {CORR}; trend {TREND} C/yr; places >= {PLANET} (e102); "
                           f"lake {LAKE} of the year; shallow {SHALLOW} m; temp {COLD}/{HOT} C annual; fill {DRY:.2f}/{WET:.2f}; "
                           f"A:B {RATIO}; fertility split at the land median; island >= {MIN_CELLS} cells, large >= {BIG} km2; "
                           f"lowland < {LOW} m, halves by the median along the wind to {WIND_TO} degrees; height bands {HEIGHTS} m"}]
    with open(os.path.join(res, "provenance.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(prov[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(prov)
    for k, v in out.items():
        print(f"{k:<24} {v:.4g}" if isinstance(v, float) else f"{k:<24} {v}")
    for r in isl:
        print("  ".join(f"{k} {v:.3g}" if isinstance(v, float) else f"{k} {v}" for k, v in r.items()))


if __name__ == "__main__":
    main()
