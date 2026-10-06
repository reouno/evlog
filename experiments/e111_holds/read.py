"""Read e111's readings (#130): each run's log on one line, against the same world without bodies.

    uv run python experiments/e111_holds/read.py

Prints a row a run and, for a run with a designed body put in, that body's line by year. Writes
`results/read.csv` (a row a run), `results/designed.csv` (a row a run and a year) and `results/provenance.csv`
(the window read and every threshold).
"""
import csv
import os

HERE = os.path.dirname(os.path.abspath(__file__))
DIR = os.path.join(HERE, "results", "read")
CELL_M2 = 125.0 ** 2
LAST = 5  # years the levels are read over
CONTROL = "nobody"
FOODS = ["leaf", "wood", "seed", "litter", "carrion", "kill"]
ORDER = ["nobody", "base", "nolitter", "decay10", "noreach", "nolitter_noreach", "decay10_noreach", "hunter", "twin"]


def rows(path):
    with open(path) as f:
        return list(csv.DictReader(f))


def mean(v):
    return sum(v) / max(len(v), 1)


def main():
    runs = [r for r in ORDER if os.path.exists(os.path.join(DIR, r + "_log.csv"))]
    logs = {r: rows(os.path.join(DIR, r + "_log.csv")) for r in runs}
    last_year = min(int(l[-1]["year"]) for l in logs.values())
    window = range(last_year - LAST + 1, last_year + 1)
    land_cells = None
    out = []
    for r in runs:
        w = [x for x in logs[r] if int(x["year"]) in window]
        ate = {k: mean([float(x["ate_" + k]) for x in w]) * CELL_M2 / 1000 for k in FOODS}  # t a year
        eaten = sum(ate.values())
        plants = eaten - ate["carrion"] - ate["kill"]
        peak = max(logs[r], key=lambda x: float(x["body_matter"]))
        out.append({
            "run": r,
            "years": f"{window[0]}-{window[-1]}",
            "land_biomass": mean([float(x["land_biomass"]) for x in w]),
            "land_cover": mean([float(x["land_cover"]) for x in w]),
            "litter": mean([float(x["litter"]) for x in w]),
            "gpp_t": mean([float(x["gpp"]) for x in w]) * CELL_M2 / 1000,
            "bodies": mean([float(x["bodies"]) for x in w]),
            "matter_t": mean([float(x["body_matter"]) for x in w]) * CELL_M2 / 1000,
            "peak_t": float(peak["body_matter"]) * CELL_M2 / 1000,
            "peak_year": int(peak["year"]),
            "sea_share": mean([float(x["body_sea_share"]) for x in w]),
            "eaten_of_gpp": plants / max(mean([float(x["gpp"]) for x in w]) * CELL_M2 / 1000, 1e-30),
            **{"ate_" + k + "_t": ate[k] for k in FOODS},
            "flesh_share": (ate["carrion"] + ate["kill"]) / max(eaten, 1e-30),
            "breaks": mean([float(x["breaks"]) for x in w]),
            "err": max(max(float(x[k]) for k in ("water_err", "a_err", "b_err", "c_err")) for x in logs[r]),
        })
    control = next((o for o in out if o["run"] == CONTROL), None)
    for o in out:
        o["land_of_control"] = o["land_biomass"] / control["land_biomass"] if control else float("nan")
    print(f"years {window[0]}-{window[-1]} (means); t = tonnes of dry matter on the whole trial world")
    print(f"{'run':18s} land_bio  of_ctrl cover litter   gpp_t  bodies matter_t (peak, yr)  sea% eaten/gpp  leaf  wood  seed litter flesh%  breaks  err")
    for o in out:
        print(
            f"{o['run']:18s} {o['land_biomass']:8.3f} {100 * o['land_of_control']:7.0f}% {100 * o['land_cover']:4.0f}% {o['litter']:6.3f} {o['gpp_t']:7.0f} {o['bodies']:7.0f} {o['matter_t']:8.1f} ({o['peak_t']:6.0f}, {o['peak_year']}) "
            f"{100 * o['sea_share']:4.0f} {100 * o['eaten_of_gpp']:8.1f}% {o['ate_leaf_t']:5.0f} {o['ate_wood_t']:5.0f} {o['ate_seed_t']:5.0f} {o['ate_litter_t']:6.0f} {100 * o['flesh_share']:6.2f} {o['breaks']:7.1f} {o['err']:.0e}"
        )
    with open(os.path.join(HERE, "results", "read.csv"), "w", newline="") as f:
        wr = csv.DictWriter(f, fieldnames=list(out[0].keys()))
        wr.writeheader()
        for o in out:
            wr.writerow({k: (f"{v:.6g}" if isinstance(v, float) else v) for k, v in o.items()})

    # A designed body's line: the genotypes whose founder is the injected type (the first root born in that year).
    des = []
    for r in runs:
        par = rows(os.path.join(DIR, r + "_row.csv"))[0] if os.path.exists(os.path.join(DIR, r + "_row.csv")) else {}
        iy = int(float(par.get("inject_year", 0)))
        if iy == 0:
            continue
        cen = rows(os.path.join(DIR, r + "_bodies.csv"))
        roots = {int(x["root"]) for x in cen if int(x["born"]) == iy and int(x["parent"]) < 0}
        if not roots:
            print(f"\n{r}: no designed line in the census")
            continue
        root = min(roots)
        print(f"\n== {r}: the designed line (root {root}, put in in year {iy})")
        print("year bodies  animals matter_t  of_all  mass_kg  leaf  wood  seed litter carrion  kill  kills  km/yr")
        for y in sorted({int(x["year"]) for x in cen}):
            if y <= iy:
                continue
            mine = [x for x in cen if int(x["year"]) == y and int(x["root"]) == root]
            all_m = sum(float(x["matter"]) for x in cen if int(x["year"]) == y)
            m = sum(float(x["matter"]) for x in mine)
            wt = lambda k: sum(float(x[k]) * float(x["matter"]) for x in mine) / max(m, 1e-30)
            row = {
                "run": r, "year": y, "bodies": sum(int(x["bodies"]) for x in mine), "animals": sum(float(x["animals"]) for x in mine),
                "matter_t": m / 1000, "of_all": m / max(all_m, 1e-30), "mass_kg": wt("mass"),
                **{"ate_" + k: wt("ate_" + k) for k in FOODS}, "kills": sum(float(x["kills"]) for x in mine), "travel_km_yr": wt("travel_km_yr"),
            }
            des.append(row)
            print(
                f"{y:4d} {row['bodies']:6d} {row['animals']:8.0f} {row['matter_t']:8.2f} {100 * row['of_all']:6.1f}% {row['mass_kg']:8.3f} "
                + " ".join(f"{100 * row['ate_' + k]:5.1f}" for k in FOODS) + f" {row['kills']:8.0f} {row['travel_km_yr']:6.0f}"
            )
    if des:
        with open(os.path.join(HERE, "results", "designed.csv"), "w", newline="") as f:
            wr = csv.DictWriter(f, fieldnames=list(des[0].keys()))
            wr.writeheader()
            for o in des:
                wr.writerow({k: (f"{v:.6g}" if isinstance(v, float) else v) for k, v in o.items()})
    with open(os.path.join(HERE, "results", "provenance.csv"), "w", newline="") as f:
        wr = csv.writer(f)
        wr.writerow(["what", "value"])
        wr.writerow(["runs read", " ".join(runs)])
        wr.writerow(["window: the last years of the shortest run (means)", f"{window[0]}-{window[-1]}"])
        wr.writerow(["the line a run is set against", f"{CONTROL}: land_biomass over the same years"])
        wr.writerow(["cell, m2 (log sums are kg a m2 summed over cells)", CELL_M2])
        wr.writerow(["flesh in the diet", "(ate_carrion + ate_kill) / all eaten, from the log"])
        wr.writerow(["a designed line", "census rows whose root is the founder born in inject_year with no parent"])
        wr.writerow(["a designed line's diet", "its genotypes' lifetime diet shares of the bodies alive, weighted by matter"])


if __name__ == "__main__":
    main()
