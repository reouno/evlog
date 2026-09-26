#!/usr/bin/env python3
"""Read e105's millennium runs against their five hypotheses (#116, rung 2); e103's reader, copied and extended.

Run from the repo root: `uv run python experiments/e105_millennium/measure.py [results_dir run ...]` (a minute).

Reads each run's `_log.csv` (a row a year), `_census.csv` (a row a genotype a year), `_eaters.csv`, `_maps.bin`
(the last years' annual maps) and `_lead.bin` (each cell's leading genotype, every 10 years and the last years),
and e102's bare ground for H5. Writes `results/measure.csv` (a row a run), `results/years.csv` (a row a run a
census year: groups, genotypes, the leader) and `results/provenance.csv`.
"""
import csv
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, ROOT)
from analysis.groups import CUT, group, hill, vectors  # noqa: E402

RESULTS = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "results")  # another folder: a pilot's
RUNS = sys.argv[2:] or ["c1225_life1", "c1225_life2"]
E102 = os.path.join(ROOT, "experiments", "e102_ground", "results", "c1225")
LAST = 100           # years read for H2 and H3
TURN = 100           # years read for the leader's changes (beside)
LATE = 510           # a group or genotype born after this year is of the second half (H4)
HALF_SHARE = 0.25    # H4: groups led by second-half genotypes hold this much of the biomass at the end
KEY_TURN, KEY_NEAR = 0.5, 2.0   # H5: the keys' spectrum changes this much in 500 years; eaters within 2 bits
COVER_LAND, COVER_SEA, DRIFT = 0.5, 0.2, 0.01      # H2 (the log's cover: > 0.01 kg on land, > 0.001 at sea)
GROUPS, NMI = 5.0, 0.2                              # H3
CHANGES, NEW_SHARE = 3, 0.01                        # H4
EVAP, AB_CORR = 0.10, 0.8                           # H5
# e102's places, as it read them (its measure.py)
RIVER, LAKE, SHALLOW = 100.0, 0.5, 200.0
COLD, HOT, DRY, WET, RATIO = 5.0, 20.0, 1 / 3, 2 / 3, (0.5, 2.0)


def load_maps(prefix):
    h = json.load(open(prefix + "_maps.json"))
    n, fields, statics, years = h["n"], h["fields"], h["static"], h["years"]
    raw = np.fromfile(prefix + "_maps.bin", dtype="<f4")
    k = len(years) * len(fields) * n * n
    y = raw[:k].reshape(len(years), len(fields), n * n)
    st = raw[k:].reshape(len(statics), n * n)
    return years, {f: y[:, i] for i, f in enumerate(fields)}, {f: st[i] for i, f in enumerate(statics)}


def load_lead(prefix):
    h = json.load(open(prefix + "_lead.json"))
    raw = np.fromfile(prefix + "_lead.bin", dtype="<u4").reshape(len(h["years"]), -1)
    return h["years"], raw, h["none"]


def places(mean, st):
    """e102's label a cell: medium x temperature x moisture x A:B x fertility (its `chemistry` reading)."""
    sea = st["sea"] > 0
    t = mean["temp"]
    tb = np.where(t < COLD, 0, np.where(t < HOT, 1, 2))
    mb = np.where(mean["fill"] < DRY, 0, np.where(mean["fill"] < WET, 1, 2))
    lake = (mean["lake"] >= LAKE) & ~sea
    river = (mean["discharge"] >= RIVER) & ~sea & ~lake
    medium = np.where(sea, np.where(-st["elev"] < SHALLOW, 1, 2), np.where(lake, 3, np.where(river, 4, 0)))
    label = medium * 100 + tb * 10 + np.where(medium == 0, mb, 0)
    ab = mean["a"] / np.maximum(mean["b"], 1e-12)
    rb = np.where(ab < RATIO[0], 0, np.where(ab < RATIO[1], 1, 2))
    tot = mean["a"] + mean["b"]
    fb = (tot >= np.median(tot[~sea])).astype(int)
    return label * 100 + np.where(~sea, rb * 10 + fb, 0)


def nmi(a, b):
    """Normalised mutual information of two labelings (by the geometric mean of their entropies)."""
    _, ia = np.unique(a, return_inverse=True)
    _, ib = np.unique(b, return_inverse=True)
    joint = np.zeros((ia.max() + 1, ib.max() + 1))
    np.add.at(joint, (ia, ib), 1)
    p = joint / joint.sum()
    pa, pb = p.sum(1), p.sum(0)
    nz = p > 0
    mi = (p[nz] * np.log(p[nz] / np.outer(pa, pb)[nz])).sum()
    ha = -(pa[pa > 0] * np.log(pa[pa > 0])).sum()
    hb = -(pb[pb > 0] * np.log(pb[pb > 0])).sum()
    return float(mi / np.sqrt(ha * hb)) if ha > 0 and hb > 0 else 0.0


def slope(v):
    return float(np.polyfit(np.arange(len(v)), v, 1)[0])


def key_spectrum(rows, weight, keys, n_keys=None):
    """Biomass over the 256 keys (a compound's mass shared among its keys)."""
    s = np.zeros(256)
    for r in rows:
        ks = [k for k in r[keys].split("-") if k]
        for k in ks:
            s[int(k, 16)] += float(r[weight]) / len(ks)
    return s


def read(run):
    prefix = os.path.join(RESULTS, run)
    log = list(csv.DictReader(open(prefix + "_log.csv")))
    census = list(csv.DictReader(open(prefix + "_census.csv")))
    eaters = list(csv.DictReader(open(prefix + "_eaters.csv")))
    by_year = {}
    for r in census:
        by_year.setdefault(int(r["year"]), []).append(r)
    e_by_year = {}
    for r in eaters:
        e_by_year.setdefault(int(r["year"]), []).append(r)
    years = sorted(by_year)
    end = years[-1]
    out = {"run": run, "years": f"{years[0]}-{end}"}

    # H1
    for k in ["water_err", "a_err", "b_err", "c_err"]:
        out[k] = max(float(r[k]) for r in log)

    # H2
    last = [r for r in log if int(r["year"]) > end - LAST]
    out["land_cover_min"] = min(float(r["land_cover"]) for r in last)
    out["sea_cover_min"] = min(float(r["sea_cover"]) for r in last)
    lb = [float(r["land_biomass"]) for r in last]
    out["land_biomass"] = float(np.mean(lb))
    out["biomass_drift"] = slope(lb) / np.mean(lb)

    # H3 and the years: groups at every census
    rows_years, gyear = [], {}
    for y in years:
        rows = by_year[y]
        x, w = vectors(rows)
        g = group(x, w)
        gm = {}
        for i, gi in enumerate(g):
            gm[gi] = gm.get(gi, 0.0) + w[i]
        lead = int(np.argmax(w))
        gyear[y] = (rows, g, gm, w)
        es = e_by_year.get(y, [])
        ps, ek = key_spectrum(rows, "mass_land", "keys"), key_spectrum(es, "mass", "keys")
        track = float(ps @ ek / np.sqrt((ps @ ps) * (ek @ ek))) if ps.any() and ek.any() else 0.0
        defended = sum(float(r["mass_land"]) + float(r["mass_sea"]) for r in rows if int(r["n_keys"]) > 0) / w.sum()
        rows_years.append({
            "run": run, "year": y, "genotypes": len(rows), "groups_hill": hill(gm.values()), "groups": len(gm),
            "genotypes_hill": hill(w), "leader": rows[lead]["id"], "leader_share": w[lead] / w.sum(),
            "top_group_share": max(gm.values()) / w.sum(), "defended": defended, "key_track": track,
            "eater_genotypes": len(es), "eater_hill": hill([float(r["mass"]) for r in es]),
            "mutant_share": sum(w[i] for i in range(len(rows)) if int(rows[i]["born"]) > years[0] - 1) / w.sum(),
            "lifespan": sum(w[i] * float(rows[i]["lifespan"]) for i in range(len(rows))) / w.sum(),
        })
    ly = [r for r in rows_years if r["year"] > end - LAST]
    out["groups_hill"] = float(np.mean([r["groups_hill"] for r in ly]))
    out["groups_hill_end"] = rows_years[-1]["groups_hill"]
    out["top_group_share"] = rows_years[-1]["top_group_share"]
    out["genotypes_hill"] = float(np.mean([r["genotypes_hill"] for r in ly]))

    # H3: the leading group of each land cell against its place (the last year's leaders, the last years' maps)
    myears, ym, st = load_maps(prefix)
    mean = {f: v.mean(axis=0) for f, v in ym.items()}
    place = places(mean, st)
    lyears, lead_map, none = load_lead(prefix)
    rows, g, gm, w = gyear[end]
    id_group = {int(rows[i]["id"]): int(g[i]) for i in range(len(rows))}
    lm = lead_map[lyears.index(end)]
    land = st["sea"] == 0
    has = land & (lm != none) & np.isin(lm, list(id_group))
    grp = np.array([id_group[int(v)] for v in lm[has]])
    out["lead_cells_read"] = int(has.sum())
    out["nmi_group_place"] = nmi(grp, place[has])
    out["nmi_genotype_place"] = nmi(lm[has], place[has])
    out["place_types"] = int(len(np.unique(place[land])))

    # H4: the leader's changes over the last 100 years; groups whose leader was born late
    lead_ids = [r["leader"] for r in rows_years if r["year"] > end - TURN]
    out["leader_changes"] = sum(1 for a, b in zip(lead_ids, lead_ids[1:]) if a != b)
    out["leaders_distinct"] = len(set(lead_ids))
    new = sum(m for gi, m in gm.items() if int(rows[gi]["born"]) > LATE)
    out["new_group_share"] = new / w.sum()
    out["new_groups"] = sum(1 for gi, m in gm.items() if int(rows[gi]["born"]) > LATE and m / w.sum() >= NEW_SHARE)
    out["born_median"] = float(np.median([int(r["born"]) for r in rows]))

    # H5: against e102's bare ground
    e102 = list(csv.DictReader(open(E102 + "_log.csv")))[-10:]
    bare = float(np.mean([float(r["land_evap"]) for r in e102]))
    lastlog = log[-10:]
    et = float(np.mean([float(r["land_evap"]) + float(r["transp"]) for r in lastlog]))
    out["et_bare"], out["et_living"], out["et_change"] = bare, et, et / bare - 1
    out["transp_share"] = float(np.mean([float(r["transp"]) / (float(r["land_evap"]) + float(r["transp"])) for r in lastlog]))
    _, y2, st2 = load_maps(E102)
    ab = np.log(np.maximum(ym["a"][-1], 1e-9) / np.maximum(ym["b"][-1], 1e-9))[land]
    ab2 = np.log(np.maximum(y2["a"][-1], 1e-9) / np.maximum(y2["b"][-1], 1e-9))[st2["sea"] == 0]
    out["ab_corr_e102"] = float(np.corrcoef(ab, ab2)[0, 1])
    out["runoff_ratio"] = float(np.mean([float(r["to_sea"]) / float(r["land_rain"]) for r in lastlog]))
    out["runoff_ratio_e102"] = float(np.mean([float(r["to_sea"]) / float(r["land_rain"]) for r in e102]))

    # beside: keys, fire, eaters. The key reading: how far (bits) a producer's compound lies from the nearest
    # detox key any eater carries, by the producer's biomass (8 = no eater carries a key near it; 0 = matched).
    es = e_by_year.get(end, [])
    ekeys = [int(k, 16) for r in es for k in r["keys"].split("-") if k]
    pk = [(int(k, 16), float(r["mass_land"]) + float(r["mass_sea"])) for r in rows for k in r["keys"].split("-") if k]
    out["key_distance"] = (sum(m * min((bin(k ^ e).count("1") for e in ekeys), default=8) for k, m in pk) / sum(m for _, m in pk)) if pk else 8.0
    em = sum(float(r["mass"]) for r in es)
    out["eaters_keyless"] = sum(float(r["mass"]) for r in es if int(r["n_keys"]) == 0) / em if em else 0.0
    out["eaters_mutant"] = sum(float(r["mass"]) for r in es if int(r["born"]) > years[0] - 1) / em if em else 0.0
    out["producers_mutant"] = sum(w[i] for i in range(len(rows)) if int(rows[i]["born"]) > years[0] - 1) / w.sum()
    out["defended"] = rows_years[-1]["defended"]
    out["key_track"] = float(np.mean([r["key_track"] for r in ly]))
    out["burnt_cells"] = float(np.mean([float(r["burnt_cells"]) for r in last]))
    out["eaters"] = float(np.mean([float(r["eaters"]) for r in last]))
    out["eater_hill"] = float(np.mean([r["eater_hill"] for r in ly]))
    out["max_height"] = float(np.percentile(mean["height"][land], 99))

    # H4 (e105): how young the living's genes are, and the groups the second half founded
    ws = sorted((int(rows[i]["born"]), w[i]) for i in range(len(rows)))
    half, acc = w.sum() / 2, 0.0
    for born, m in ws:
        acc += m
        if acc >= half:
            out["born_median_biomass"] = born
            break
    out["late_group_share"] = sum(m for gi, m in gm.items() if int(rows[gi]["born"]) > LATE) / w.sum()
    # H5 (e105): the producers' keys at the end against 500 years before (Bray-Curtis over the 256 keys, by biomass)
    back = max([y for y in years if y <= end - 500] or [years[0]])
    k0, k1 = key_spectrum(by_year[back], "mass_land", "keys"), key_spectrum(rows, "mass_land", "keys")
    out["key_years"] = f"{back}-{end}"
    out["key_turnover"] = float(np.abs(k1 - k0).sum() / max((k1 + k0).sum(), 1e-30))

    out["H1"] = all(out[k] < 1e-9 for k in ["water_err", "a_err", "b_err", "c_err"])
    out["H2"] = out["land_cover_min"] >= COVER_LAND and out["sea_cover_min"] >= COVER_SEA and abs(out["biomass_drift"]) < DRIFT
    out["H3"] = out["groups_hill"] >= GROUPS and out["nmi_group_place"] >= NMI
    out["H4"] = out["born_median_biomass"] > LATE and out["late_group_share"] >= HALF_SHARE
    out["H5"] = out["key_turnover"] >= KEY_TURN and out["key_distance"] <= KEY_NEAR
    for k in ["H1", "H2", "H3", "H4", "H5"]:
        out[k] = "yes" if out[k] else "no"
    return out, rows_years, gyear[end]


def replay(a, b):
    """The share of each run's biomass in groups whose leader has a match in the other run within the cut."""
    (ra, ga, gma, wa), (rb, gb, gmb, wb) = a, b
    xa, _ = vectors(ra)
    xb, _ = vectors(rb)
    la, lb = list(gma), list(gmb)
    norm = np.sqrt(xa.shape[1])
    d = np.sqrt(((xa[la][:, None, :] - xb[lb][None, :, :]) ** 2).sum(-1)) / norm
    ma = sum(gma[g] for i, g in enumerate(la) if d[i].min() <= CUT) / wa.sum()
    mb = sum(gmb[g] for j, g in enumerate(lb) if d[:, j].min() <= CUT) / wb.sum()
    return ma, mb


def main():
    outs, years, ends = [], [], []
    for run in RUNS:
        o, y, e = read(run)
        outs.append(o)
        years += y
        ends.append(e)
    if len(ends) == 2:
        ma, mb = replay(*ends)
        for o in outs:
            o["replay_matched"] = (ma + mb) / 2
    for name, rows in [("measure.csv", outs), ("years.csv", years)]:
        with open(os.path.join(RESULTS, name), "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
            w.writeheader()
            w.writerows(rows)
    prov = [{"reading": "measure", "run": o["run"], "census_years": o["years"], "thresholds":
             f"groups by analysis/groups.py cut {CUT}; last {LAST} years for H2/H3, {TURN} for the leader; new after "
             f"year {LATE}; cover land {COVER_LAND} sea {COVER_SEA}; drift {DRIFT}; groups {GROUPS}; NMI {NMI}; changes "
             f"{CHANGES}; new share {NEW_SHARE}; H4 second half after {LATE}, late groups {HALF_SHARE}; H5 keys Bray-Curtis {KEY_TURN} over 500 years, eaters within {KEY_NEAR} bits; places as e102 (river {RIVER} mm, "
             f"lake {LAKE}, shallow {SHALLOW} m, temp {COLD}/{HOT} C, fill {DRY:.2f}/{WET:.2f}, A:B {RATIO})"} for o in outs]
    with open(os.path.join(RESULTS, "provenance.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(prov[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(prov)
    for k in outs[0]:
        print(f"{k:<22}", "  ".join(f"{o[k]:.4g}" if isinstance(o[k], float) else str(o[k]) for o in outs))


if __name__ == "__main__":
    main()
