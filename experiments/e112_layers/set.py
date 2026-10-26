"""Read e112's set on the trial world (#125, part 3): the land, the layers' use, the diet and the designed lines.

    uv run python experiments/e112_layers/set.py

Reads `results/set/<run>_{log,bodies,fates}.csv`, against `results/read/{nobody,notear,all}_log.csv` (part 1).
Writes `results/set.csv` (a row a run), `results/set_designed.csv` (a row a designed run and a year) and adds its
rows to `results/provenance.csv`.
"""
import csv
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", ".."))
from analysis import ways  # noqa: E402

RES = os.path.join(HERE, "results")
SET, READ = os.path.join(RES, "set"), os.path.join(RES, "read")
CELL_M2 = 125.0 ** 2
LAST = 5  # years of the log read as a run's level
RUNS = ["off", "layers", "no_ground", "no_crown", "tear", "digger", "climber", "hunter", "digger2", "climber2"]
FOODS = ["leaf", "wood", "seed", "litter", "carrion", "kill", "root", "store", "bank"]
LAYER_FOODS = {"ground": ["root", "store", "bank"], "crown": ["leaf", "seed", "wood"]}
TIMING = {"ms_step", "secs_decide", "secs_meet", "secs_live", "secs_last"}
INJECT = 20


def rows(path):
    with open(path) as f:
        return list(csv.DictReader(f))


def mean(v):
    v = list(v)
    return sum(v) / max(len(v), 1)


def main():
    runs = [r for r in RUNS if os.path.exists(os.path.join(SET, r + "_log.csv"))]
    logs = {r: rows(os.path.join(SET, r + "_log.csv")) for r in runs}
    ref = {r: rows(os.path.join(READ, r + "_log.csv")) for r in ("nobody", "notear", "all")}
    end = min(int(v[-1]["year"]) for v in logs.values())
    years = range(end - LAST + 1, end + 1)
    lv = lambda log, k: mean(float(x[k]) for x in log if int(x["year"]) in years)

    out, des = [], []
    for r in runs + ["notear"]:
        log = logs.get(r, ref["notear"])
        o = {"run": r, "land_biomass": lv(log, "land_biomass")}
        o["of_nobody"] = o["land_biomass"] / lv(ref["nobody"], "land_biomass")
        o["minus_notear"] = o["land_biomass"] - lv(ref["notear"], "land_biomass")
        for k in ("root", "store", "bank", "leaf", "wood"):
            o[f"land_{k}"] = lv(log, f"land_{k}")
        o["bodies"] = lv(log, "bodies")
        o["matter_t"] = lv(log, "body_matter") * CELL_M2 / 1000
        o["ground_share"] = lv(log, "body_ground") if "body_ground" in log[0] else 0.0
        o["crown_share"] = lv(log, "body_crown") if "body_crown" in log[0] else 0.0
        ate = {k: lv(log, "ate_" + k) if "ate_" + k in log[0] else 0.0 for k in FOODS}
        tot = max(sum(ate.values()), 1e-30)
        for k in FOODS:
            o["diet_" + k] = ate[k] / tot
        o["flesh"] = o["diet_carrion"] + o["diet_kill"]
        o["err"] = max(max(float(x[k]) for k in ("water_err", "a_err", "b_err", "c_err")) for x in log)
        bp = os.path.join(SET, r + "_bodies.csv")
        if r in logs and os.path.exists(bp):
            cen = rows(bp)
            last = [x for x in cen if int(x["year"]) == end]
            rd, _ = ways.read(last)
            o["ways"], o["ways_place"], o["ways_diet"], o["ways_size"] = rd["groups_hill"], rd["hill_place"], rd["hill_diet"], rd["hill_size"]
            # the designed line: the founder born in the injection's year with no parent
            roots = {int(x["root"]) for x in cen if int(x["born"]) == INJECT and int(x["parent"]) < 0}
            if roots:
                root = min(roots)
                fates = rows(os.path.join(SET, r + "_fates.csv"))
                for y in range(INJECT + 1, end + 1):
                    mine = [x for x in cen if int(x["year"]) == y and int(x["root"]) == root]
                    m = sum(float(x["matter"]) for x in mine)
                    a = sum(float(x["animals"]) for x in mine)
                    wt = lambda k: sum(float(x[k]) * float(x["matter"]) for x in mine) / max(m, 1e-30)
                    d = {"run": r, "year": y, "bodies": sum(int(x["bodies"]) for x in mine), "matter_t": m / 1000,
                         "adult_mass": wt("adult_mass"), **{"ate_" + k: wt("ate_" + k) for k in FOODS},
                         **{p: sum(float(x[p]) * float(x["animals"]) for x in mine) / max(a, 1e-30) for p in ("at_sea", "at_surface", "at_ground", "at_crown")}}
                    for f in fates:
                        if int(f["year"]) == y and int(f["root"]) == root:
                            d["died_" + f["cause"]] = int(f["bodies"])
                    des.append(d)
        out.append(o)

    print(f"==== the set, years {years[0]}-{years[-1]} (land kg a m2; the bodies' matter t; diet shares of what was eaten)")
    print(f"{'run':10s}  land of_nobody -notear  root store  bank | bodies matter_t ground% crown% | litter  leaf  wood  seed  root store  bank flesh | ways place diet size | err")
    for o in out:
        w = f"{o['ways']:4.2f} {o['ways_place']:5.2f} {o['ways_diet']:4.2f} {o['ways_size']:4.2f}" if "ways" in o else "   -"
        print(f"{o['run']:10s} {o['land_biomass']:.3f} {100 * o['of_nobody']:8.0f}% {o['minus_notear']:+.3f} {o['land_root']:.3f} {o['land_store']:.3f} {o['land_bank']:.3f} | {o['bodies']:6.0f} {o['matter_t']:8.0f} {100 * o['ground_share']:7.2f} {100 * o['crown_share']:6.2f} | "
              + " ".join(f"{100 * o['diet_' + k]:5.1f}" for k in ("litter", "leaf", "wood", "seed", "root", "store", "bank")) + f" {100 * o['flesh']:5.2f} | {w} | {o['err']:.0e}")
    for r in sorted({d["run"] for d in des}):
        print(f"\n== {r}: the designed line (put in in year {INJECT})")
        print("year bodies matter_t adult_kg | at ground surface crown sea | litter leaf wood seed root store bank carrion kill | died")
        for d in (d for d in des if d["run"] == r):
            died = " ".join(f"{k[5:]} {v}" for k, v in d.items() if k.startswith("died_"))
            print(f"{d['year']:4d} {d['bodies']:6d} {d['matter_t']:8.3f} {d['adult_mass']:.2e} | {100 * d['at_ground']:9.0f} {100 * d['at_surface']:7.0f} {100 * d['at_crown']:5.0f} {100 * d['at_sea']:3.0f} | "
                  + " ".join(f"{100 * d['ate_' + k]:4.0f}" for k in ("litter", "leaf", "wood", "seed", "root", "store", "bank", "carrion", "kill")) + f" | {died}")

    same = None
    if "off" in logs:
        old = ref["all"]
        cols = [k for k in old[0] if k not in TIMING and k in logs["off"][0]]
        diff = [(a["year"], k) for a, b in zip(logs["off"], old) for k in cols if a[k] != b[k]]
        same = not diff and len(old) == len(logs["off"])
        print(f"\n`off` against part 1's `all` (e111's world): {len(cols)} columns over {len(old)} years, " + ("the same to the digit" if same else f"{len(diff)} values differ, the first {diff[:3]}"))

    for name, table in [("set.csv", out), ("set_designed.csv", des)]:
        if not table:
            continue
        keys = list(dict.fromkeys(k for o in table for k in o))
        with open(os.path.join(RES, name), "w", newline="") as f:
            wr = csv.DictWriter(f, fieldnames=keys, restval="", lineterminator="\n")
            wr.writeheader()
            for o in table:
                wr.writerow({k: (f"{v:.6g}" if isinstance(v, float) else v) for k, v in o.items()})
    prov = os.path.join(RES, "provenance.csv")
    keep = [r for r in csv.reader(open(prov)) if not r[0].startswith("set")]
    keep += [
        ["set: the runs", "results/set: " + " ".join(runs) + "; notear from results/read"],
        ["set: window", f"years {years[0]}-{years[-1]}, means of the log; the body census of year {end}"],
        ["set: the world without bodies", "results/read/nobody, land_biomass over the same years"],
        ["set: ground and crown shares", "body_ground, body_crown: the share of the bodies' matter in each layer (log)"],
        ["set: a designed line", f"census rows whose root is the founder born in year {INJECT} with no parent; diet by matter, places by animals; deaths from _fates.csv"],
        ["set: the ways", ways.provenance()],
        ["set: `off` against `all`", "every log column of part 1's `all` but the timings: " + ("the same to the digit" if same else "not compared" if same is None else "differs")],
    ]
    with open(prov, "w", newline="") as f:
        csv.writer(f, lineterminator="\n").writerows(keep)


if __name__ == "__main__":
    main()
