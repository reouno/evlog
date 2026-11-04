"""Read e114's gate on the trial world (#133).

    uv run python experiments/e114_chemistry/gate.py

Reads `results/gate/<run>_{log,census}.csv`, against e113's `results/gate/all_log.csv` and e112's
`results/read/nobody_log.csv`. Writes `results/gate.csv` (a row a run and year read), `results/gate_locks.csv` (the
producers' locks over 10% of their mass, by year) and adds rows to `results/provenance.csv`.
"""
import csv
import os

HERE = os.path.dirname(os.path.abspath(__file__))
GATE = os.path.join(HERE, "results", "gate")
E113 = os.path.join(HERE, "..", "e113_sea_catch", "results", "gate", "all_log.csv")
NOBODY = os.path.join(HERE, "..", "e112_layers", "results", "read", "nobody_log.csv")
RUNS = ["off", "lock", "lock80"]
TIMING = {"ms_step", "secs_decide", "secs_meet", "secs_live", "secs_last"}
YEARS = [15, 20, 25, 30, 35, 40, 50, 60, 70, 80]
LOCK_SHARE = 0.1  # a producer lock holding this share of the producers' mass counts


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
    off, old = rows(os.path.join(GATE, "off_log.csv")), rows(E113)
    cols = [k for k in old[0] if k not in TIMING and k in off[0]]
    diff = [(a["year"], k) for a, b in zip(off, old) for k in cols if a[k] != b[k]]
    print(f"off against e113's gate all: {len(cols)} columns, {min(len(off), len(old))} years, {len(diff)} differ" + (f", first {diff[0]}" if diff else ""))
    nobody = {int(r["year"]): float(r["land_biomass"]) for r in rows(NOBODY)}
    out, locks = [], []
    for run in RUNS:
        log = {int(r["year"]): r for r in rows(os.path.join(GATE, run + "_log.csv"))}
        err = max(max(float(r[k]) for k in ("water_err", "a_err", "b_err", "c_err")) for r in log.values())
        for y in YEARS:
            if y not in log:
                continue
            r = log[y]
            ate = {k[4:]: float(r[k]) for k in r if k.startswith("ate_")}
            tot = sum(ate.values()) or 1.0
            out.append({"run": run, "year": y, "bodies": r["bodies"], "land_biomass": r["land_biomass"],
                        "of_nobody": f"{float(r['land_biomass']) / nobody[y]:.3f}" if y in nobody else "",
                        "land_b_soil": r["land_b_soil"], "litter": r["litter"], "eaters": r["eaters"],
                        "litter_of_diet": f"{ate['litter'] / tot:.4f}", "flesh_of_diet": f"{(ate['carrion'] + ate['kill']) / tot:.4f}",
                        "lit_eaten": r.get("lit_eaten", ""), "lit_locked": r.get("lit_locked", ""), "p_locked": r.get("p_locked", ""),
                        "p_locks": r.get("p_locks", ""), "b_locked": r.get("b_locked", ""), "b_keys": r.get("b_keys", ""), "max_err": f"{err:.1e}"})
        by = {}
        for r in rows(os.path.join(GATE, run + "_census.csv")):
            m = float(r["mass_land"]) + float(r["mass_sea"])
            y = int(r["year"])
            d = by.setdefault(y, {})
            d[r["lock"]] = d.get(r["lock"], 0.0) + m
        for y, d in sorted(by.items()):
            t = sum(d.values())
            big = sorted(((v / t, k) for k, v in d.items() if v / t >= LOCK_SHARE), reverse=True)
            locks.append({"run": run, "year": y, "locks_over": len(big), "locks": " ".join(f"{k}:{s:.2f}" for s, k in big), "nonplain": f"{1 - d.get('00', 0.0) / t:.4f}"})
    for o in out:
        print(o)
    for o in locks:
        if o["run"] != "off" and (o["year"] % 10 == 0 or o["locks_over"] > 1):
            print(o)
    write("gate.csv", out)
    write("gate_locks.csv", locks)
    prov = os.path.join(HERE, "results", "provenance.csv")
    keep = [r for r in csv.reader(open(prov))] if os.path.exists(prov) else [["what", "value"]]
    keep = [r for r in keep if not r[0].startswith("gate")]
    keep += [["gate: off", f"results/gate/off_log.csv against e113_sea_catch/results/gate/all_log.csv, {len(cols)} columns but timing: {len(diff)} differ"],
             ["gate: of_nobody", "land_biomass over e112_layers/results/read/nobody_log.csv, same year (it ends at year 30)"],
             ["gate: diet", "ate_<food> of the log's year, litter and carrion + kill over all"],
             ["gate: locks", f"_census.csv by lock: producer mass (land + sea) a lock holds, counted at {LOCK_SHARE} of it"]]
    with open(prov, "w", newline="") as f:
        csv.writer(f, lineterminator="\n").writerows(keep)


if __name__ == "__main__":
    main()
