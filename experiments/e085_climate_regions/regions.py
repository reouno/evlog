#!/usr/bin/env python3
"""The regions over stage A's climates (e085, #98), from e061's climate maps (no producers, no bodies).

Run from the repo root: `uv run python experiments/e085_climate_regions/regions.py`

e084's rule and calibration, unchanged (its `regions.py` and `results/calibration.csv`): a block of 8 x 8 cells
(half or more of it land) is predicted the mean density of c1225's control for its class of yearly ground
dryness and coolest-quarter temperature; it is dense at 0.03 bodies a land cell (0.025 and 0.035 as a check);
a region is a 4-connected piece of 10 or more dense blocks on the torus; the effective number of regions is
exp(entropy) of the regions' predicted bodies.

First the check: c1225's climate map (e061, 20 years) against its producers map (e062 d11, e084's input).

Also: the land masses that hold each climate's regions (regions held apart by the sea or on one land), the rank
correlation of the effective number with the climate's axes, and the regions recounted on any producers map in
`results/producers/` (e062 with draw d11).

Writes `results/regions.csv` (a row a climate), `results/check.csv` and `results/blocks_<id>.csv` for c1225
and every climate with 3.5 effective regions or more.
"""
import csv
import glob
import importlib.util
import os

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
EXP = os.path.dirname(HERE)
_spec = importlib.util.spec_from_file_location("e084_regions", os.path.join(EXP, "e084_regions", "regions.py"))
e084 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(e084)
B, BIG, DRY, TEMP = e084.B, e084.BIG, e084.DRY, e084.TEMP
MAPS = os.path.join(HERE, "results", "maps")
CUTS = (0.025, 0.03, 0.035)


def read_e061(path):
    """e061's `<prefix>_maps.bin`: b"E061", n (u32), the height (n*n f32), then for each quarter of the last
    year the habitats (n*n u8) and the means of temperature, ground fill (at most 1; 0 in the sea) and the
    rain (n*n f32 each), then the middle year's four habitat maps."""
    raw = open(path, "rb").read()
    assert raw[:4] == b"E061", path
    n = int(np.frombuffer(raw, "<u4", 1, 4)[0])
    cells = n * n
    at = 8
    elev = np.frombuffer(raw, "<f4", cells, at).reshape(n, n)
    at += 4 * cells
    q = {k: [] for k in ("hab", "temp", "moist", "rain")}
    for _ in range(4):
        q["hab"].append(np.frombuffer(raw, "u1", cells, at).reshape(n, n))
        at += cells
        for k in ("temp", "moist", "rain"):
            q[k].append(np.frombuffer(raw, "<f4", cells, at).reshape(n, n))
            at += 4 * cells
    out = {"n": n, "elev": elev}
    for k, v in q.items():
        out[k] = np.stack(v)
    return out


def blocks(m, land):
    """Each block's land cells, mean yearly dryness and mean coolest-quarter temperature over its land."""
    n = m["n"]
    g = n // B
    lc = land.reshape(g, B, g, B).sum((1, 3))
    mean = lambda a: (a * land).reshape(g, B, g, B).sum((1, 3)) / np.maximum(lc, 1)  # noqa: E731
    return g, lc, mean(1 - m["moist"].mean(0)), mean(m["temp"].min(0))


def calibration():
    table = np.zeros((len(DRY) - 1, len(TEMP) - 1))
    with open(os.path.join(EXP, "e084_regions", "results", "calibration.csv")) as f:
        for r in csv.DictReader(f):
            i = DRY.index(float(r["dry_lo"]))
            j = TEMP.index(float(r["temp_lo"]))
            table[i, j] = float(r["density"])
    return lambda d, t: table[e084.cls(d, DRY), e084.cls(t, TEMP)]


def count(pred, lc, cut):
    """Regions of `pred` at a dense line: (labels, the rooms' shares largest first, the effective number)."""
    lab = e084.regions_of(pred >= cut)
    rooms = np.array(sorted((float((pred * lc)[lab == k].sum()) for k in np.unique(lab[lab > 0])), reverse=True))
    p = rooms / max(rooms.sum(), 1e-9)
    eff = float(np.exp(-(p * np.log(p)).sum())) if len(p) else 0.0
    return lab, p, eff


def masses(lab, pred, lc):
    """The land masses (4-connected blocks holding any land) that hold the regions: how many, the effective
    number by their regions' rooms, and how many regions share a mass with another (held apart on land, not
    by the sea)."""
    mass, _ = e084.label(lc > 0)
    per = {}
    for k in np.unique(lab[lab > 0]):
        ms, c = np.unique(mass[lab == k], return_counts=True)
        per.setdefault(int(ms[np.argmax(c)]), []).append(float((pred * lc)[lab == k].sum()))
    if not per:
        return 0, 0.0, 0
    q = np.array([sum(v) for v in per.values()])
    q = q / q.sum()
    return len(per), float(np.exp(-(q * np.log(q)).sum())), sum(len(v) for v in per.values() if len(v) > 1)


def check(predict):
    """c1225: e061's climate map against e062's producers map (e084's input), block by block."""
    a = read_e061(os.path.join(MAPS, "c1225_maps.bin"))
    b = e084.read_maps(os.path.join(EXP, "e062_producers", "results", "pass", "c1225_d11_maps.bin"))
    assert np.array_equal(a["elev"], b["elev"]), "not the same terrain"
    rows = []
    out = {}
    for name, m, land in (("climate (e061)", a, a["elev"] >= 0), ("producers (e062)", b, b["moist"].max(0) > 0)):
        g, lc, d, t = blocks(m, land)
        ok = lc >= B * B // 2
        pred = predict(d, t) * ok
        out[name] = (ok, d, t, pred)
        for cut in CUTS:
            lab, p, eff = count(pred, lc, cut)
            rows.append({"map": name, "dense": cut, "regions": len(p), "effective": round(eff, 3),
                         "sizes": " ".join(str(int(x)) for x in sorted(np.unique(lab[lab > 0], return_counts=True)[1], reverse=True))})
    (ok1, d1, t1, p1), (ok2, d2, t2, p2) = out.values()
    ok = ok1 & ok2
    print(f"c1225 check: blocks {ok.sum()} (land differs in {(ok1 != ok2).sum()}); dryness r {np.corrcoef(d1[ok], d2[ok])[0, 1]:.4f}, "
          f"mean {d1[ok].mean():.3f} vs {d2[ok].mean():.3f}, largest gap {np.abs(d1 - d2)[ok].max():.3f}; coolest quarter r "
          f"{np.corrcoef(t1[ok], t2[ok])[0, 1]:.4f}, mean {t1[ok].mean():.2f} vs {t2[ok].mean():.2f} C; predicted density r "
          f"{np.corrcoef(p1[ok], p2[ok])[0, 1]:.4f}; dense blocks agree {np.mean((p1 >= 0.03) == (p2 >= 0.03)):.4f}")
    for r in rows:
        print(f"  {r['map']} at {r['dense']}: {r['regions']} regions, effective {r['effective']}, sizes {r['sizes']}")
    with open(os.path.join(HERE, "results", "check.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def main():
    predict = calibration()
    check(predict)
    search = {}
    for f in glob.glob(os.path.join(EXP, "e061_climate", "results", "search", "c*_row.csv")):
        r = next(csv.DictReader(open(f)))
        search["c" + r["seed"]] = r
    rows = []
    for path in sorted(glob.glob(os.path.join(MAPS, "c*_maps.bin"))):
        cid = os.path.basename(path)[:5]
        row = next(csv.DictReader(open(os.path.join(MAPS, f"{cid}_row.csv"))))
        same = all(row[k] == search[cid][k] for k in ("habitats", "wide", "change", "stand", "pass", "land_temp", "rain_land"))
        m = read_e061(path)
        land = m["elev"] >= 0
        g, lc, d, t = blocks(m, land)
        ok = lc >= B * B // 2
        pred = predict(d, t) * ok
        out = {"climate": cid, "size": m["n"], "row_matches_search": int(same), "land_share": round(float(land.mean()), 3),
               "land_temp": float(row["land_temp"]), "rain_land": float(row["rain_land"]),
               "dryness": round(float(d[ok].mean()), 3), "coolest": round(float(t[ok].mean()), 2),
               "room": round(float((pred * lc).sum()))}
        for cut in CUTS:
            lab, p, eff = count(pred, lc, cut)
            tag = f"{cut:g}"
            out[f"effective_{tag}"] = round(eff, 3)
            if cut == 0.03:
                out["regions"] = len(p)
                out["regions_5pct"] = int((p >= 0.05).sum())
                out["largest"] = round(float(p[0]), 3) if len(p) else 0.0
                out["dense_share"] = round(float((lc * (lab > 0)).sum() / max(lc.sum(), 1)), 3)
                out["shares"] = " ".join(f"{x:.3f}" for x in p[:10])
                out["masses"], em, out["regions_sharing_a_mass"] = masses(lab, pred, lc)
                out["effective_masses"] = round(em, 3)
                keep = lab
        rows.append(out)
        if cid == "c1225" or out["effective_0.03"] >= 3.5:
            with open(os.path.join(HERE, "results", f"blocks_{cid}.csv"), "w", newline="") as f:
                w = csv.writer(f)
                w.writerow(["gx", "gy", "land", "dry", "temp", "predicted", "region"])
                for y in range(g):
                    for x in range(g):
                        if lc[y, x]:
                            w.writerow([x, y, int(lc[y, x]), round(float(d[y, x]), 4), round(float(t[y, x]), 2),
                                        round(float(pred[y, x]), 5), int(keep[y, x])])
    rows.sort(key=lambda r: -r["effective_0.03"])
    print(f"{'climate':8} size match land  temp   rain  dry  coolest  room  regions(5%) eff 0.025/0.03/0.035 largest masses(eff) shared")
    for r in rows:
        print(f"{r['climate']:8} {r['size']:4} {r['row_matches_search']:5} {r['land_share']:.2f} {r['land_temp']:5.1f} {r['rain_land']:6.0f} "
              f"{r['dryness']:.2f} {r['coolest']:6.1f} {r['room']:6} {r['regions']:3} ({r['regions_5pct']}) "
              f"{r['effective_0.025']:5.2f} {r['effective_0.03']:5.2f} {r['effective_0.035']:5.2f} {r['largest']:.2f} "
              f"{r['masses']:3} ({r['effective_masses']:.2f}) {r['regions_sharing_a_mass']:3}")
    # the rank correlation of the effective number with each axis, over the 512 climates
    big = [r for r in rows if r["size"] == 512]
    rank = lambda a: np.argsort(np.argsort(a))  # noqa: E731
    eff = rank(np.array([r["effective_0.03"] for r in big]))
    axes = {k: [r[k] for r in big] for k in ("land_share", "dryness", "coolest", "rain_land")}
    for k in ("relief", "grain", "tilt", "year"):
        axes[k] = [float(search[r["climate"]][k]) for r in big]
    axes["latitude_span"] = [float(search[r["climate"]]["lat_hi"]) - float(search[r["climate"]]["lat_lo"]) for r in big]
    print(f"rank correlation with the effective number over the {len(big)} climates at 512: " +
          ", ".join(f"{k} {np.corrcoef(rank(np.array(v)), eff)[0, 1]:+.2f}" for k, v in axes.items()))
    # the producers' maps made here (e062 with draw d11), recounted
    for path in sorted(glob.glob(os.path.join(HERE, "results", "producers", "c*_maps.bin"))):
        m = e084.read_maps(path)
        g, lc, d, t = blocks(m, m["elev"] >= 0)
        pred = predict(d, t) * (lc >= B * B // 2)
        for cut in CUTS:
            lab, p, eff1 = count(pred, lc, cut)
            print(f"{os.path.basename(path)[:-9]} (producers) at {cut}: {len(p)} regions, effective {eff1:.2f}")
    with open(os.path.join(HERE, "results", "regions.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


if __name__ == "__main__":
    main()
