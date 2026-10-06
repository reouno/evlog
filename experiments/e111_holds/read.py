"""Read e111 (#130): each run's log on one line, against the same world without bodies.

    uv run python experiments/e111_holds/read.py

Three sets of runs, each read if its directory is there: `results/read` (the readings: switches and a designed
body on the trial world), `results/set` (the design's four cycles on the trial world, all on and each left out)
and `results/pilot` (the design on `isles1`). Prints a row a run and, for a run with a designed body put in, that
body's line by year. Writes `results/<set>.csv` (a row a run), `results/designed.csv` (a row a run and a year) and
`results/provenance.csv` (the windows read and every threshold).
"""
import csv
import os

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results")
CELL_M2 = 125.0 ** 2
FLESH = 0.1  # share of flesh in its diet over which a genotype is read as a flesh eater
BIG = 1.0  # kg: an adult mass over it is a large body
LINE = 0.01  # share of the bodies' matter over which a founder's line is counted
FOODS = ["leaf", "wood", "seed", "litter", "carrion", "kill"]
POOLS = ["soil", "plants", "litter", "bodies"]
TRIAL_CONTROL = os.path.join(RES, "read", "nobody_log.csv")
SETS = [
    # directory, the runs in the order they are printed, the log of the world without bodies, years read
    ("read", ["nobody", "base", "nolitter", "decay10", "noreach", "nolitter_noreach", "decay10_noreach", "hunter", "twin"], TRIAL_CONTROL, 5),
    ("set", ["e110", "all", "no_road", "no_worth", "no_reach", "no_bite", "all_hunter", "no_bite_hunter", "all_twin"], TRIAL_CONTROL, 5),
    ("pilot", ["tick1", "all"], os.path.join(HERE, "..", "e109_metres", "results", "isles1_life1_log.csv"), 10),
]
# e110's `tick1` is the pilot's world with none of the four cycles: read from its own experiment
ELSEWHERE = {("pilot", "tick1"): os.path.join(HERE, "..", "e110_meet", "results", "pilot")}


def rows(path):
    with open(path) as f:
        return list(csv.DictReader(f))


def mean(v):
    return sum(v) / max(len(v), 1)


def read_set(name, order, control_path, last, prov, des):
    d = os.path.join(RES, name)
    where = {r: ELSEWHERE.get((name, r), d) for r in order}
    runs = [r for r in order if os.path.exists(os.path.join(where[r], r + "_log.csv"))]
    if not runs:
        return
    logs = {r: rows(os.path.join(where[r], r + "_log.csv")) for r in runs}
    control = rows(control_path) if os.path.exists(control_path) else None
    last_year = min([int(l[-1]["year"]) for l in logs.values()] + ([int(control[-1]["year"])] if control else []))
    window = range(last_year - last + 1, last_year + 1)
    ctl = mean([float(x["land_biomass"]) for x in control if int(x["year"]) in window]) if control else float("nan")
    out = []
    for r in runs:
        w = [x for x in logs[r] if int(x["year"]) in window]
        ate = {k: mean([float(x.get("ate_" + k, 0)) for x in w]) * CELL_M2 / 1000 for k in FOODS}  # t a year
        eaten = sum(ate.values())
        gpp = mean([float(x["gpp"]) for x in w]) * CELL_M2 / 1000
        peak = max(logs[r], key=lambda x: float(x.get("body_matter", 0)))
        o = {
            "run": r,
            "years": f"{window[0]}-{window[-1]}",
            "land_biomass": mean([float(x["land_biomass"]) for x in w]),
            "land_of_control": mean([float(x["land_biomass"]) for x in w]) / ctl,
            "land_last_year": float(logs[r][last_year - 1]["land_biomass"]),
            "land_cover": mean([float(x["land_cover"]) for x in w]),
            "gpp_t": gpp,
            "bodies": mean([float(x.get("bodies", 0)) for x in w]),
            "matter_t": mean([float(x.get("body_matter", 0)) for x in w]) * CELL_M2 / 1000,
            "peak_t": float(peak.get("body_matter", 0)) * CELL_M2 / 1000,
            "peak_year": int(peak["year"]),
            "sea_share": mean([float(x.get("body_sea_share", 0)) for x in w]),
            "eaten_of_gpp": (eaten - ate["carrion"] - ate["kill"]) / max(gpp, 1e-30),
            **{"ate_" + k + "_t": ate[k] for k in FOODS},
            "flesh_share": (ate["carrion"] + ate["kill"]) / max(eaten, 1e-30),
            "breaks": mean([float(x.get("breaks", 0)) for x in w]),
            "killed_t": mean([float(x.get("torn", 0)) for x in w]) * CELL_M2 / 1000,
            "err": max(max(float(x[k]) for k in ("water_err", "a_err", "b_err", "c_err")) for x in logs[r]),
        }
        # who the bodies are, at the window's last census: large bodies, flesh eaters, founders' lines
        cpath = os.path.join(where[r], r + "_bodies.csv")
        cen = [x for x in rows(cpath) if int(x["year"]) == last_year] if os.path.exists(cpath) else []
        tot = sum(float(x["matter"]) for x in cen)
        if tot > 0:
            share = lambda keep: sum(float(x["matter"]) for x in cen if keep(x)) / tot
            lines = {}
            for x in cen:
                lines[x["root"]] = lines.get(x["root"], 0.0) + float(x["matter"]) / tot
            o["over_1kg"] = share(lambda x: float(x["adult_mass"]) > BIG)
            o["flesh_eaters"] = share(lambda x: float(x["ate_carrion"]) + float(x["ate_kill"]) > FLESH)
            o["lines"] = sum(1 for v in lines.values() if v > LINE)
            o["largest_line"] = max(lines.values())
        if "land_b_soil" in w[0]:
            for k in POOLS:
                o["land_b_" + k] = mean([float(x["land_b_" + k]) for x in w])
            o["sea_b_bodies"] = mean([float(x["sea_b_bodies"]) for x in w])
        out.append(o)
    print(f"\n==== {name}: years {window[0]}-{window[-1]} (means); t = tonnes of dry matter on the whole world; the world without bodies holds {ctl:.3f} kg a m2")
    print(f"{'run':17s} land_bio of_ctrl (last) cover   gpp_t bodies matter_t (peak, yr)  sea% eaten/gpp  leaf  wood  seed litter flesh% killed_t >1kg flesh_eaters lines (largest)")
    for o in out:
        who = f"{100 * o['over_1kg']:5.1f}% {100 * o['flesh_eaters']:5.1f}% {o['lines']:3d} ({100 * o['largest_line']:.0f}%)" if "over_1kg" in o else "    -"
        print(
            f"{o['run']:17s} {o['land_biomass']:7.3f} {100 * o['land_of_control']:6.0f}% ({o['land_last_year']:.3f}) {100 * o['land_cover']:3.0f}% {o['gpp_t']:7.0f} {o['bodies']:6.0f} {o['matter_t']:8.1f} ({o['peak_t']:6.0f}, {o['peak_year']}) "
            f"{100 * o['sea_share']:4.0f} {100 * o['eaten_of_gpp']:8.1f}% {o['ate_leaf_t']:5.0f} {o['ate_wood_t']:5.0f} {o['ate_seed_t']:5.0f} {o['ate_litter_t']:6.0f} {100 * o['flesh_share']:6.2f} {o['killed_t']:8.1f} {who}"
        )
    if any("land_b_soil" in o for o in out):
        print("the land's B, g a m2 of land (the same years)")
        print(f"{'run':17s}   soil plants litter bodies   land  at_sea")
        for o in out:
            if "land_b_soil" in o:
                print(f"{o['run']:17s} " + " ".join(f"{o['land_b_' + k]:6.3f}" for k in POOLS) + f" {sum(o['land_b_' + k] for k in POOLS):6.3f} {o['sea_b_bodies']:7.3f}")
    keys = list(dict.fromkeys(k for o in out for k in o))
    with open(os.path.join(RES, name + ".csv"), "w", newline="") as f:
        wr = csv.DictWriter(f, fieldnames=keys, restval="", lineterminator="\n")
        wr.writeheader()
        for o in out:
            wr.writerow({k: (f"{v:.6g}" if isinstance(v, float) else v) for k, v in o.items()})

    # A designed body's line: the genotypes whose founder is the injected type (the root born in that year).
    for r in runs:
        rp = os.path.join(where[r], r + "_row.csv")
        iy = int(float(rows(rp)[0].get("inject_year", 0))) if os.path.exists(rp) else 0
        if iy == 0:
            continue
        cen = rows(os.path.join(where[r], r + "_bodies.csv"))
        roots = {int(x["root"]) for x in cen if int(x["born"]) == iy and int(x["parent"]) < 0}
        if not roots:
            print(f"{name}/{r}: no designed line in the census")
            continue
        root = min(roots)
        print(f"== {name}/{r}: the designed line (root {root}, put in in year {iy})")
        print("year bodies  animals matter_t  of_all  mass_kg  leaf  wood  seed litter carrion  kill  kills  km/yr")
        for y in sorted({int(x["year"]) for x in cen}):
            if y <= iy:
                continue
            mine = [x for x in cen if int(x["year"]) == y and int(x["root"]) == root]
            all_m = sum(float(x["matter"]) for x in cen if int(x["year"]) == y)
            m = sum(float(x["matter"]) for x in mine)
            wt = lambda k: sum(float(x[k]) * float(x["matter"]) for x in mine) / max(m, 1e-30)
            row = {
                "set": name, "run": r, "year": y, "bodies": sum(int(x["bodies"]) for x in mine), "animals": sum(float(x["animals"]) for x in mine),
                "matter_t": m / 1000, "of_all": m / max(all_m, 1e-30), "mass_kg": wt("mass"),
                **{"ate_" + k: wt("ate_" + k) for k in FOODS}, "kills": sum(float(x["kills"]) for x in mine), "travel_km_yr": wt("travel_km_yr"),
            }
            des.append(row)
            print(
                f"{y:4d} {row['bodies']:6d} {row['animals']:8.0f} {row['matter_t']:8.2f} {100 * row['of_all']:6.1f}% {row['mass_kg']:8.3f} "
                + " ".join(f"{100 * row['ate_' + k]:5.1f}" for k in FOODS) + f" {row['kills']:8.0f} {row['travel_km_yr']:6.0f}"
            )
    prov.append([f"{name}: runs read", " ".join(runs)])
    prov.append([f"{name}: window, the last years of the shortest run (means)", f"{window[0]}-{window[-1]}"])
    prov.append([f"{name}: the world without bodies (land_biomass over the same years)", os.path.relpath(control_path, HERE)])


def main():
    prov, des = [], []
    for name, order, control, last in SETS:
        read_set(name, order, control, last, prov, des)
    if des:
        with open(os.path.join(RES, "designed.csv"), "w", newline="") as f:
            wr = csv.DictWriter(f, fieldnames=list(des[0].keys()), lineterminator="\n")
            wr.writeheader()
            for o in des:
                wr.writerow({k: (f"{v:.6g}" if isinstance(v, float) else v) for k, v in o.items()})
    with open(os.path.join(RES, "provenance.csv"), "w", newline="") as f:
        wr = csv.writer(f, lineterminator="\n")
        wr.writerow(["what", "value"])
        wr.writerows(prov)
        wr.writerow(["cell, m2 (log sums are kg a m2 summed over cells)", CELL_M2])
        wr.writerow(["flesh in the diet", "(ate_carrion + ate_kill) / all eaten, from the log"])
        wr.writerow(["killed_t", "the log's `torn`: tissue that failed in meetings, t a year"])
        wr.writerow(["who the bodies are", "the body census of the window's last year, by matter"])
        wr.writerow(["a large body: adult mass over, kg", BIG])
        wr.writerow(["a flesh eater: flesh over this share of its lifetime diet", FLESH])
        wr.writerow(["a founder's line is counted over this share of the matter", LINE])
        wr.writerow(["the land's B by pool", "land_b_soil, _plants (stands, seed bank, small eaters), _litter, _bodies (with carrion): g a m2 of land; sea_b_bodies: the bodies at sea, over the land's area"])
        wr.writerow(["a designed line", "census rows whose root is the founder born in inject_year with no parent"])
        wr.writerow(["a designed line's diet", "its genotypes' lifetime diet shares of the bodies alive, weighted by matter"])


if __name__ == "__main__":
    main()
