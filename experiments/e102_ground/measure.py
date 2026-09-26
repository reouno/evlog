#!/usr/bin/env python3
"""Read e102's world against its five hypotheses (#116, rung 1).

Run from the repo root: `uv run python experiments/e102_ground/measure.py [prefix]` (seconds).

Reads `<prefix>_log.csv` (a row a year) and `<prefix>_maps.bin` + `_maps.json` (the last years' annual maps and
the static ones). Writes `results/measure.csv` (one row: every reading), `results/places.csv` (each place type's
area under each classification) and the `measure` rows of `results/provenance.csv`.
"""
import csv
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
PREFIX = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "results", "c1225")

RIVER = 100.0        # mm an update: a river (H2)
RIVER_SHARE = 0.01   # of the land (H2)
DRIFT = 0.01         # a year, of the land's water (H2)
SPAN = 4.0           # p90 / p10 of A:B and of A + B (H3)
CORR = (0.2, 0.95)   # consecutive years' land rain (H4)
TREND = 0.1          # C a year, land temperature over the read years (H4)
LAKE = 0.5           # share of the year a cell is a lake
SHALLOW = 200.0      # m of sea over the shelf (e061)
COLD, HOT = 5.0, 20.0            # C, annual mean (e061 read a quarter's mean)
DRY, WET = 1 / 3, 2 / 3          # the soil's mean fill (e061)
RATIO = (0.5, 2.0)               # A:B bands


def load(prefix):
    h = json.load(open(prefix + "_maps.json"))
    n, fields, statics, years = h["n"], h["fields"], h["static"], h["years"]
    cells = n * n
    raw = np.fromfile(prefix + "_maps.bin", dtype="<f4")
    k = len(years) * len(fields) * cells
    yearly = raw[:k].reshape(len(years), len(fields), cells)
    st = raw[k:].reshape(len(statics), cells)
    return years, {f: yearly[:, i] for i, f in enumerate(fields)}, {f: st[i] for i, f in enumerate(statics)}


def hill(areas):
    p = np.array([a for a in areas if a > 0], dtype=float)
    p /= p.sum()
    return float(np.exp(-(p * np.log(p)).sum()))


def places(mean, st, chem, rivers):
    """A label per cell: medium x temperature (x moisture on land) (x A:B x fertility with `chem`)."""
    sea = st["sea"] > 0
    t = mean["temp"]
    tb = np.where(t < COLD, 0, np.where(t < HOT, 1, 2))
    fill = mean["fill"]
    mb = np.where(fill < DRY, 0, np.where(fill < WET, 1, 2))
    lake = (mean["lake"] >= LAKE) & ~sea
    river = (mean["discharge"] >= RIVER) & ~sea & ~lake if rivers else np.zeros_like(sea)
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
    years, y, st = load(PREFIX)
    sea = st["sea"] > 0
    land = ~sea
    mean = {f: v.mean(axis=0) for f, v in y.items()}
    last = {f: v[-1] for f, v in y.items()}
    read = [r for r in log if int(r["year"]) in years]
    out = {"years_read": f"{years[0]}-{years[-1]}", "land_cells": int(land.sum())}

    # H1: the ledgers
    out["water_err"] = max(float(r["water_err"]) for r in log)
    out["a_err"] = max(float(r["a_err"]) for r in log)
    out["b_err"] = max(float(r["b_err"]) for r in log)

    # H2: rivers, and the land's water steady
    q = mean["discharge"][land]
    out["river_share"] = float((q >= RIVER).mean())
    out["river_share_20"] = float((q >= 20).mean())  # beside H2: smaller streams
    out["river_share_50"] = float((q >= 50).mean())
    lw = np.array([float(r["land_water"]) for r in read])
    slope = np.polyfit(np.arange(len(lw)), lw, 1)[0]
    out["land_water_drift"] = float(slope / lw.mean())
    out["to_sea_mm"] = float(np.mean([float(r["to_sea"]) for r in read]))
    out["land_rain_mm"] = float(np.mean([float(r["land_rain"]) for r in read]))
    out["runoff_ratio"] = out["to_sea_mm"] / out["land_rain_mm"]

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
    anom = rain / rain.mean(axis=0, keepdims=True)
    out["rain_cv_median"] = float(np.median(anom.std(axis=0)))
    # Beside H4 (not its verdict): the map of each year's departure from the mean, year against the next -
    # how much of a wet or dry year persists, which the raw maps' correlation (the fixed pattern) hides.
    dev = rain - rain.mean(axis=0, keepdims=True)
    ds = [float(np.corrcoef(dev[i], dev[i + 1])[0, 1]) for i in range(len(years) - 1)]
    out["rain_anom_corr"] = float(np.mean(ds))
    out["dry_year_share"] = float((anom < 0.8).mean())  # cell-years under 80% of the cell's mean rain

    # H5: places, by three classifications of the mean of the read years
    rows = []
    for name, chem, rivers in [("e061", False, False), ("rivers", False, True), ("chemistry", True, True)]:
        lab = places(mean, st, chem, rivers)
        u, c = np.unique(lab, return_counts=True)
        out[f"places_{name}"] = hill(c)
        out[f"types_{name}"] = int(len(u))
        rows += [{"classification": name, "place": int(k), "cells": int(v), "share": v / lab.size} for k, v in zip(u, c)]
    # the same, on the land alone
    for name, chem, rivers in [("e061", False, False), ("chemistry", True, True)]:
        lab = places(mean, st, chem, rivers)[land]
        out[f"land_places_{name}"] = hill(np.unique(lab, return_counts=True)[1])

    verdicts = {
        "H1": out["water_err"] < 1e-9 and out["a_err"] < 1e-9 and out["b_err"] < 1e-9,
        "H2": out["river_share"] >= RIVER_SHARE and abs(out["land_water_drift"]) < DRIFT,
        "H3": out["ab_span"] >= SPAN and out["fertility_span"] >= SPAN,
        "H4": CORR[0] <= out["rain_corr_mean"] <= CORR[1] and abs(out["temp_trend"]) < TREND,
        "H5": out["places_chemistry"] > out["places_e061"],
    }
    out.update({k: "yes" if v else "no" for k, v in verdicts.items()})
    with open(os.path.join(HERE, "results", "measure.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(out), lineterminator="\n")
        w.writeheader()
        w.writerow(out)
    with open(os.path.join(HERE, "results", "places.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    prov = [{"reading": "measure", "run": os.path.basename(PREFIX), "from": years[0], "to": years[-1], "items": len(years),
             "thresholds": f"river {RIVER} mm/update on {RIVER_SHARE:.0%} of land; drift {DRIFT:.0%}/yr; span x{SPAN}; "
                           f"rain corr {CORR}; trend {TREND} C/yr; lake {LAKE} of the year; shallow {SHALLOW} m; "
                           f"temp {COLD}/{HOT} C annual; fill {DRY:.2f}/{WET:.2f}; A:B {RATIO}; fertility split at the land median"}]
    with open(os.path.join(HERE, "results", "provenance.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(prov[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(prov)
    for k, v in out.items():
        print(f"{k:<22} {v:.4g}" if isinstance(v, float) else f"{k:<22} {v}")


if __name__ == "__main__":
    main()
