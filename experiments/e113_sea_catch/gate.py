"""Read e113's gate on the trial world (#132, part 1).

    uv run python experiments/e113_sea_catch/gate.py

Reads `results/gate/<run>_{log,bodies,fates}.csv`, against e112's `results/set/layers_log.csv` and
`results/read/nobody_log.csv`. Writes `results/gate.csv` (a row a run and year read), `results/gate_line.csv` (the
designed line by year) and `results/provenance.csv`.
"""
import csv
import os

HERE = os.path.dirname(os.path.abspath(__file__))
GATE = os.path.join(HERE, "results", "gate")
E112 = os.path.join(HERE, "..", "e112_layers", "results")
RUNS = ["off", "all", "no_floor", "hunter", "hunter_press", "hunter_nosight", "hunter_few", "hunter_hungry"]
FOODS = ["leaf", "wood", "seed", "litter", "carrion", "kill", "root", "store", "bank"]
TIMING = {"ms_step", "secs_decide", "secs_meet", "secs_live", "secs_last"}
YEARS = [20, 21, 22, 23, 25, 30, 35, 40]
INJECT = 20
CELL_M2 = 125.0 ** 2


def rows(path):
    with open(path) as f:
        return list(csv.DictReader(f))


def write(path, table):
    keys = list(dict.fromkeys(k for o in table for k in o))
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys, restval="", lineterminator="\n")
        w.writeheader()
        w.writerows(table)


def main():
    res = os.path.join(HERE, "results")
    off, old = rows(os.path.join(GATE, "off_log.csv")), rows(os.path.join(E112, "set", "layers_log.csv"))
    cols = [k for k in old[0] if k not in TIMING and k in off[0]]
    diff = sum(a[k] != b[k] for a, b in zip(off, old) for k in cols)
    print(f"`off` against e112's `layers`: {len(cols)} columns over {min(len(off), len(old))} years, {diff} values differ")
    nobody = {int(r["year"]): float(r["land_biomass"]) for r in rows(os.path.join(E112, "read", "nobody_log.csv"))}

    out, line = [], []
    for run in RUNS:
        log = rows(os.path.join(GATE, run + "_log.csv"))
        err = max(max(float(x[k]) for k in ("water_err", "a_err", "b_err", "c_err")) for x in log)
        for y in YEARS:
            x = next(r for r in log if int(r["year"]) == y)
            ate = {k: float(x["ate_" + k]) for k in FOODS}
            land = float(x["land_biomass"])
            out.append({"run": run, "year": y, "bodies": x["bodies"], "matter_t": f"{float(x['body_matter']) * CELL_M2 / 1000:.0f}",
                        "land": f"{land:.3f}", "of_nobody": f"{land / nobody[y]:.3f}" if y in nobody else "",
                        "sea_share": x["body_sea_share"], "flesh": f"{(ate['carrion'] + ate['kill']) / max(sum(ate.values()), 1e-30):.4f}",
                        "killed": x["killed"], "births": x["births"], "max_err": f"{err:.0e}"})
        if not run.startswith("hunter"):
            continue
        cen = rows(os.path.join(GATE, run + "_bodies.csv"))
        roots = {int(c["root"]) for c in cen if int(c["born"]) == INJECT and int(c["parent"]) < 0}
        fates = rows(os.path.join(GATE, run + "_fates.csv"))
        for y in range(INJECT + 1, 41):
            mine = [c for c in cen if int(c["year"]) == y and int(c["root"]) in roots]
            dead = {}
            for f in fates:
                if int(f["year"]) == y and int(f["root"]) in roots:
                    dead["died_" + f["cause"]] = int(f["bodies"])
            if not mine and not dead:
                continue
            m = sum(float(c["matter"]) for c in mine)
            wt = lambda k: sum(float(c[k]) * float(c["matter"]) for c in mine) / max(m, 1e-30)
            line.append({"run": run, "year": y, "bodies": sum(int(c["bodies"]) for c in mine), "matter_t": f"{m / 1000:.2f}",
                         "ate_kill": f"{wt('ate_kill'):.3f}", "ate_carrion": f"{wt('ate_carrion'):.3f}", "ate_litter": f"{wt('ate_litter'):.3f}", **dead})
    write(os.path.join(res, "gate.csv"), out)
    write(os.path.join(res, "gate_line.csv"), line)
    for o in out:
        print(" ".join(f"{k} {v}" for k, v in o.items() if k not in ("max_err", "births")))
    for o in line:
        print(o)
    write_prov = [["what", "value"],
                  ["gate: the runs", "results/gate: " + " ".join(RUNS)],
                  ["gate: years read", "the log's row of each of " + " ".join(map(str, YEARS))],
                  ["gate: flesh", "(ate_carrion + ate_kill) / all ate_ columns of the log, that year"],
                  ["gate: of_nobody", "land_biomass over e112's results/read/nobody_log.csv, same year (it ends at year 30)"],
                  ["gate: the designed line", f"census rows whose root is a founder born in year {INJECT} with no parent; a run's other bodies are the rest"],
                  ["gate: `off` against e112's `layers`", f"{len(cols)} log columns but the timings, {diff} values differ"]]
    with open(os.path.join(res, "provenance.csv"), "w", newline="") as f:
        csv.writer(f, lineterminator="\n").writerows(write_prov)


if __name__ == "__main__":
    main()
