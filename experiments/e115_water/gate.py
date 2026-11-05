"""Read e115's gate on the trial world (#134).

    uv run python experiments/e115_water/gate.py

Reads `results/gate/<run>_{log,wet}.csv`, against e114's `results/gate/worn_log.csv` (its law, the same world) and
e112's `results/read/nobody_log.csv`. Writes `results/gate.csv` (a row a run and year read), `results/gate_wet.csv`
(by the ground's wetness, over the years read) and adds rows to `results/provenance.csv`.
"""
import csv
import os

HERE = os.path.dirname(os.path.abspath(__file__))
GATE = os.path.join(HERE, "results", "gate")
E114 = os.path.join(HERE, "..", "e114_chemistry", "results", "gate", "worn_log.csv")
NOBODY = os.path.join(HERE, "..", "e112_layers", "results", "read", "nobody_log.csv")
RUNS = ["off", "water", "water80"]
TIMING = {"ms_step", "secs_decide", "secs_meet", "secs_live", "secs_last"}
YEARS = [15, 20, 25, 30, 35, 40, 50, 60, 70, 80]
WET_FROM = 21  # the wetness table sums the years from here (the bodies sown in 15 have spread)
BINS = 10  # body::WET_BINS; the gate's `wet` column was printed to one decimal, so two bins share a label: the bin is the row's place in its year
AREA = 125.0 ** 2  # m2 a cell (isles1's cell_km 0.125); `animal_days` is k * dt, animals a m2 times years


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
    old = rows(E114)
    off = rows(os.path.join(GATE, "off_log.csv"))
    cols = [k for k in old[0] if k not in TIMING and k in off[0]]
    def same(a, b):  # to the digits e114 printed (its lock columns had four places; the crate prints them in full since)
        if a == b:
            return True
        if "e" in b or "." not in b:
            return False
        return f"{float(a):.{len(b.split('.')[1])}f}" == b
    diff = [(a["year"], k) for a, b in zip(off, old) for k in cols if not same(a[k], b[k])]
    print(f"off against e114's gate worn: {len(cols)} columns, {min(len(off), len(old))} years, {len(diff)} differ" + (f", first {diff[0]}" if diff else ""))
    nobody = {int(r["year"]): float(r["land_biomass"]) for r in rows(NOBODY)}
    out, wet = [], []
    for run in RUNS:
        log = {int(r["year"]): r for r in rows(os.path.join(GATE, run + "_log.csv"))}
        err = max(max(float(r[k]) for k in ("water_err", "a_err", "b_err", "c_err")) for r in log.values())
        for y in YEARS:
            if y not in log:
                continue
            r = log[y]
            ate = {k[4:]: float(r[k]) for k in r if k.startswith("ate_")}
            tot = sum(ate.values()) or 1.0
            died = {k[5:]: float(r[k]) for k in r if k.startswith("died_")}
            dead = sum(died.values()) or 1.0
            drunk = float(r["body_drunk"])
            fw = float(r.get("food_water", 0) or 0)
            out.append({"run": run, "year": y, "bodies": r["bodies"], "land_biomass": r["land_biomass"],
                        "of_nobody": f"{float(r['land_biomass']) / nobody[y]:.3f}" if y in nobody else "",
                        "litter_of_diet": f"{ate['litter'] / tot:.4f}", "leaf_of_diet": f"{ate['leaf'] / tot:.4f}",
                        "living_of_diet": f"{sum(ate[k] for k in ('leaf', 'wood', 'seed', 'root', 'store', 'bank')) / tot:.4f}",
                        "thirst_of_deaths": f"{died['thirst'] / dead:.3f}", "hunger_of_deaths": f"{died['hunger'] / dead:.3f}",
                        "food_water_of_water": f"{fw / (fw + drunk):.4f}" if fw + drunk > 0 else "",
                        "plant_water": r.get("plant_water", ""), "body_crown": r["body_crown"], "body_ground": r["body_ground"],
                        "p_locked": r["p_locked"], "max_err": f"{err:.1e}"})
        path = os.path.join(GATE, run + "_wet.csv")
        if not os.path.exists(path):
            continue
        by = {}
        for n, r in enumerate(rows(path)):
            if int(r["year"]) < WET_FROM:
                continue
            d = by.setdefault(n % BINS, [0.0] * 7)
            for i, k in enumerate(("animal_days", "thirst", "leaf", "litter", "eaten", "food_water", "drunk")):
                d[i] += float(r[k])
        days = sum(d[0] for d in by.values()) or 1.0
        thirst = sum(d[1] for d in by.values())
        for w, d in sorted(by.items()):
            wet.append({"run": run, "wet": f"{(w + 0.5) / BINS:.2f}", "of_animal_days": f"{d[0] / days:.3f}",
                        "thirst_per_1e3_animal_years": f"{1e3 * d[1] / (d[0] * AREA):.2f}" if d[0] > 0 else "",
                        "of_thirst": f"{d[1] / thirst:.3f}" if thirst > 0 else "",
                        "leaf_of_eaten": f"{d[2] / d[4]:.4f}" if d[4] > 0 else "",
                        "food_water_of_water": f"{d[5] / (d[5] + d[6]):.4f}" if d[5] + d[6] > 0 else ""})
    for o in out + wet:
        print(o)
    write("gate.csv", out)
    write("gate_wet.csv", wet)
    prov = os.path.join(HERE, "results", "provenance.csv")
    keep = [r for r in csv.reader(open(prov))] if os.path.exists(prov) else [["what", "value"]]
    keep = [r for r in keep if not r[0].startswith("gate")]
    keep += [["gate: off", f"results/gate/off_log.csv against e114_chemistry/results/gate/worn_log.csv, {len(cols)} columns but timing, to the digits e114 printed"],
             ["gate: of_nobody", "land_biomass over e112_layers/results/read/nobody_log.csv, same year (it ends at year 30)"],
             ["gate: diet", "ate_<food> of the log's year over all; living = leaf, wood, seed, root, store, bank"],
             ["gate: deaths", "died_<cause> of the log's year over all deaths"],
             ["gate: wet", f"_wet.csv summed over years {WET_FROM} on, by the ground's wetness in tenths (the bin's middle; the bin is the row's place in its year); per animal-year = thirst / (animal_days * 15625 m2)"]]
    with open(prov, "w", newline="") as f:
        csv.writer(f, lineterminator="\n").writerows(keep)


if __name__ == "__main__":
    main()
