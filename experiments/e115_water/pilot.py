"""Read e115's pilot on isles1 (#134), against e114's seeds `lock_l2` and `lock_l3` (the same machine).

    uv run python experiments/e115_water/pilot.py

Writes `results/pilot.csv` (a row a run and year read), `results/pilot_wet.csv` (by the ground's wetness, years
WET_FROM-60) and adds rows to `results/provenance.csv`.
"""
import csv
import os

HERE = os.path.dirname(os.path.abspath(__file__))
PILOT = os.path.join(HERE, "results", "pilot")
E114 = os.path.join(HERE, "..", "e114_chemistry", "results", "pilot")
RUNS = [("lock_l2", E114), ("water_l2", PILOT), ("lock_l3", E114), ("water_l3", PILOT)]
YEARS = [41, 45, 50, 55, 60]
WET_FROM = 45  # stated before the run
BINS = 10  # body::WET_BINS
AREA = 125.0 ** 2  # m2 a cell (isles1's cell_km 0.125)


def rows(path):
    with open(path) as f:
        return list(csv.DictReader(f))


def write(name, table):
    keys = list(dict.fromkeys(k for o in table for k in o))
    with open(os.path.join(HERE, "results", name), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys, restval="", lineterminator="\n")
        w.writeheader()
        w.writerows(table)


def main():
    out, wet = [], []
    for run, where in RUNS:
        log = {int(r["year"]): r for r in rows(os.path.join(where, run + "_log.csv"))}
        err = max(max(float(r[k]) for k in ("water_err", "a_err", "b_err", "c_err")) for r in log.values())
        crown = max(float(r["body_crown"]) for r in log.values())
        for y in YEARS:
            r = log[y]
            ate = {k[4:]: float(r[k]) for k in r if k.startswith("ate_")}
            tot = sum(ate.values()) or 1.0
            died = {k[5:]: float(r[k]) for k in r if k.startswith("died_")}
            dead = sum(died.values()) or 1.0
            fw, drunk = float(r.get("food_water", 0) or 0), float(r["body_drunk"])
            out.append({"run": run, "year": y, "bodies": r["bodies"], "land_biomass": r["land_biomass"],
                        "leaf_of_diet": f"{ate['leaf'] / tot:.4f}", "litter_of_diet": f"{ate['litter'] / tot:.4f}",
                        "thirst_of_deaths": f"{died['thirst'] / dead:.3f}", "hunger_of_deaths": f"{died['hunger'] / dead:.3f}",
                        "food_water_of_water": f"{fw / (fw + drunk):.3f}" if fw + drunk > 0 else "",
                        "p_locked": r["p_locked"], "body_crown_most": f"{crown:.2e}", "max_err": f"{err:.1e}"})
        path = os.path.join(where, run + "_wet.csv")
        if not os.path.exists(path):
            continue
        by = {}
        for n, r in enumerate(rows(path)):
            if int(r["year"]) <= WET_FROM:
                continue
            d = by.setdefault(n % BINS, [0.0] * 7)
            for i, k in enumerate(("animal_days", "thirst", "leaf", "litter", "eaten", "food_water", "drunk")):
                d[i] += float(r[k])
        days = sum(d[0] for d in by.values()) or 1.0
        thirst = sum(d[1] for d in by.values())
        for w, d in sorted(by.items()):
            wet.append({"run": run, "wet": f"{(w + 0.5) / BINS:.2f}", "of_animal_days": f"{d[0] / days:.3f}",
                        "of_thirst": f"{d[1] / thirst:.3f}" if thirst > 0 else "",
                        "thirst_per_1e3_animal_years": f"{1e3 * d[1] / (d[0] * AREA):.2f}" if d[0] > 0 else "",
                        "leaf_of_eaten": f"{d[2] / d[4]:.4f}" if d[4] > 0 else "",
                        "food_water_of_water": f"{d[5] / (d[5] + d[6]):.4f}" if d[5] + d[6] > 0 else ""})
    for o in out + wet:
        print(o)
    write("pilot.csv", out)
    write("pilot_wet.csv", wet)
    prov = os.path.join(HERE, "results", "provenance.csv")
    keep = [r for r in csv.reader(open(prov))] if os.path.exists(prov) else [["what", "value"]]
    keep = [r for r in keep if not r[0].startswith("pilot")]
    keep += [["pilot: control", "e114_chemistry/results/pilot/lock_l2 and lock_l3 (Ubuntu), the same life seeds"],
             ["pilot: diet, deaths", "ate_<food> and died_<cause> of the log's year over all"],
             ["pilot: wet", f"_wet.csv summed over the ends of years {WET_FROM + 1}-60 (rows of year > {WET_FROM}), by the ground's wetness in tenths; per animal-year = thirst / (animal_days * 15625 m2)"]]
    with open(prov, "w", newline="") as f:
        csv.writer(f, lineterminator="\n").writerows(keep)


if __name__ == "__main__":
    main()
