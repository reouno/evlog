"""Read e112's readings (#125, part 1): what the land holds by layer, what a body reaches of it, and the hunters
whose fronts tear nothing they do not swallow.

    uv run python experiments/e112_layers/read.py

Reads `results/read/<run>_{log,stands,cells,bodies,row}.csv`. Prints a table a question and writes
`results/read.csv` (a row a run), `results/layers.csv` (a row a run and a pool), `results/designed.csv` (a row a
run and a year of a designed line) and `results/provenance.csv` (the windows read and every threshold).
"""
import csv
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results")
READ = os.path.join(RES, "read")
E111_ALL = os.path.join(HERE, "..", "e111_holds", "results", "set", "all_log.csv")
CELL_M2 = 125.0 ** 2
LAST = 5  # years of the log read as a run's level
RUNS = ["nobody", "all", "notear", "notear_hunter", "notear_hunter3"]
ORGANS = ["leaf", "wood", "root", "store", "seed"]
GROUND = ["root", "store", "bank"]  # what lies in the ground
FOODS = ["leaf", "wood", "seed", "litter", "carrion", "kill"]
HEIGHTS = [0.03, 0.1, 0.3, 1.0, 3.0]  # m: a body this tall reaches the share of a stand's leaves below it
WET, FAT_WET = 3.3, 1.1  # wet over dry mass of tissue and of fat (`body.rs`)
TIMING = {"ms_step", "secs_decide", "secs_meet", "secs_live", "secs_last"}


def rows(path):
    with open(path) as f:
        return list(csv.DictReader(f))


def mean(v):
    v = list(v)
    return sum(v) / max(len(v), 1)


def wquant(pairs, q):
    """The value under which a share `q` of the weight lies."""
    pairs = sorted(pairs)
    tot = sum(w for _, w in pairs)
    acc = 0.0
    for v, w in pairs:
        acc += w
        if acc >= q * tot:
            return v
    return pairs[-1][0] if pairs else float("nan")


def height(r, mass):
    """The height of one animal of a census row at a dry mass (its fat as the row's bodies carry it)."""
    fat = max(float(r["matter"]) / float(r["animals"]) - float(r["mass"]), 0.0) * mass / float(r["mass"])
    wet = mass * WET + fat * FAT_WET
    d = (wet / (float(r["density"]) * 1000.0) / float(r["nv"])) ** (1.0 / 3.0)
    return float(r["ext_z"]) * d


def main():
    runs = [r for r in RUNS if os.path.exists(os.path.join(READ, r + "_log.csv"))]
    logs = {r: rows(os.path.join(READ, r + "_log.csv")) for r in runs}
    end = min(int(l[-1]["year"]) for l in logs.values())
    window = range(end - LAST + 1, end + 1)
    ctl = mean(float(x["land_biomass"]) for x in logs["nobody"] if int(x["year"]) in window)
    out, layers, des = [], [], []

    # 1. What the land holds by organ (the log, the window's means), and its B at the run's end (the stands).
    print(f"==== what the land holds, kg a m2 of land (years {window[0]}-{window[-1]}); B in g a m2 at year {end}")
    print(f"{'run':15s} " + " ".join(f"{k:>7s}" for k in ORGANS + ["bank", "ground%", "litter"]) + "   B: " + " ".join(f"{k:>6s}" for k in ORGANS + ["bank", "ground%"]))
    for r in runs:
        w = [x for x in logs[r] if int(x["year"]) in window]
        m = {k: mean(float(x["land_" + k]) for x in w) for k in ORGANS + ["bank"]}
        st = rows(os.path.join(READ, r + "_stands.csv"))
        ce = rows(os.path.join(READ, r + "_cells.csv"))
        land = len(ce)
        b = {k: sum(float(x[k + "_b"]) for x in st) / land for k in ["leaf", "wood", "root", "seed"]}
        b["store"] = sum(float(x["store"]) for x in st) / land * 1.0  # a store holds 0.001 of its matter as B: g a kg
        b["bank"] = sum(float(x["bank_b"]) for x in ce) / land
        litter = sum(float(x["litter"]) for x in ce) / land
        gm, gb = sum(m[k] for k in GROUND) / sum(m.values()), sum(b[k] for k in GROUND) / sum(b.values())
        print(f"{r:15s} " + " ".join(f"{m[k]:7.4f}" for k in ORGANS + ["bank"]) + f" {100 * gm:6.1f}% {litter:7.4f}      " + " ".join(f"{b[k]:6.2f}" for k in ORGANS + ["bank"]) + f" {100 * gb:6.1f}%")
        for k in ORGANS + ["bank"]:
            layers.append({"run": r, "pool": k, "kg_m2": m[k], "b_g_m2": b[k], "b_share": b[k] / max(m[k] * 1000.0, 1e-30)})
        layers.append({"run": r, "pool": "litter", "kg_m2": litter, "b_g_m2": sum(float(x["litter_b"]) for x in ce) / land, "b_share": sum(float(x["litter_b"]) for x in ce) / max(sum(float(x["litter"]) for x in ce) * 1000.0, 1e-30)})
        o = {"run": r, "years": f"{window[0]}-{window[-1]}", "land_biomass": mean(float(x["land_biomass"]) for x in w)}
        o["land_of_nobody"] = o["land_biomass"] / ctl
        o["ground_share"], o["ground_b_share"] = gm, gb
        o["ground_over_leaf"] = sum(m[k] for k in GROUND) / m["leaf"]

        # 2. What a body reaches: the stands' leaves and hanging seed below a height, and how tall the bodies are.
        hang = [(float(x["h"]), float(x["leaf"]) + float(x["seed"]), float(x["wood"])) for x in st]
        tot = sum(m for _, m, _ in hang)
        for hb in HEIGHTS:
            o[f"reach_{hb}"] = sum(m * min(1.0, hb / max(h, 1e-3)) for h, m, _ in hang) / tot
        o["stand_h_p10"], o["stand_h_p50"], o["stand_h_p90"] = (wquant([(h, m) for h, m, _ in hang], q) for q in (0.1, 0.5, 0.9))
        o["wood_p10"], o["wood_p50"], o["wood_p90"] = (wquant([(wd, m) for _, m, wd in hang], q) for q in (0.1, 0.5, 0.9))
        fill = [float(x["ground"]) / max(float(x["cap"]), 1e-9) for x in ce]
        o["fill_under_third"], o["fill_over_two_thirds"] = mean(f < 1 / 3 for f in fill), mean(f > 2 / 3 for f in fill)
        bp = os.path.join(READ, r + "_bodies.csv")
        cen = [x for x in rows(bp) if int(x["year"]) == end] if os.path.exists(bp) else []
        if cen:
            now = [(height(x, float(x["mass"])), float(x["matter"])) for x in cen]
            grown = [(height(x, float(x["adult_mass"])), float(x["matter"])) for x in cen]
            o["body_h_now_p50"], o["body_h_grown_p50"], o["body_h_grown_p90"] = wquant(now, 0.5), wquant(grown, 0.5), wquant(grown, 0.9)
            o["leaf_in_reach"] = sum(m * min(1.0, o["body_h_grown_p50"] / max(h, 1e-3)) for h, m, _ in hang) / tot

        # 3. The bodies and what fails in their meetings (the window; t a year on the whole world).
        ate = {k: mean(float(x.get("ate_" + k, 0)) for x in w) * CELL_M2 / 1000 for k in FOODS}
        o["bodies"] = mean(float(x["bodies"]) for x in w)
        o["matter_t"] = mean(float(x["body_matter"]) for x in w) * CELL_M2 / 1000
        o["flesh_share"] = (ate["carrion"] + ate["kill"]) / max(sum(ate.values()), 1e-30)
        o["torn_t"] = mean(float(x["torn"]) for x in w) * CELL_M2 / 1000
        o["kill_eaten_t"] = ate["kill"]
        o["err"] = max(max(float(x[k]) for k in ("water_err", "a_err", "b_err", "c_err")) for x in logs[r])
        out.append(o)

    print("\n==== what a body reaches of the leaves and hanging seed (by their matter), and how tall the bodies are")
    print(f"{'run':15s} stand h p10/p50/p90 m   " + " ".join(f"<{hb:g}m" for hb in HEIGHTS) + "   wood kg/m2 p10/p50/p90   body h now / grown p50 / p90   in reach   soil fill <1/3, >2/3")
    for o in out:
        who = f"{o['body_h_now_p50']:.3f} / {o['body_h_grown_p50']:.3f} / {o['body_h_grown_p90']:.3f}   {100 * o['leaf_in_reach']:5.1f}%" if "leaf_in_reach" in o else "        -"
        print(f"{o['run']:15s} {o['stand_h_p10']:5.2f} {o['stand_h_p50']:5.2f} {o['stand_h_p90']:5.2f}   " + " ".join(f"{100 * o[f'reach_{hb}']:4.1f}%" for hb in HEIGHTS)
              + f"   {o['wood_p10']:.3f} {o['wood_p50']:.3f} {o['wood_p90']:.3f}   {who}   {100 * o['fill_under_third']:.0f}% {100 * o['fill_over_two_thirds']:.0f}%")

    print(f"\n==== the land and the bodies (years {window[0]}-{window[-1]}; t a year on the whole world; `nobody` holds {ctl:.3f} kg a m2)")
    print(f"{'run':15s} land_bio of_nobody bodies matter_t flesh%  torn_t kill_eaten_t")
    for o in out:
        print(f"{o['run']:15s} {o['land_biomass']:8.3f} {100 * o['land_of_nobody']:8.0f}% {o['bodies']:6.0f} {o['matter_t']:8.1f} {100 * o['flesh_share']:6.2f} {o['torn_t']:7.1f} {o['kill_eaten_t']:8.1f}")

    # The years after an injection: what failed, what of it went down a gut, and the designed line.
    for r in runs:
        iy = int(float(rows(os.path.join(READ, r + "_row.csv"))[0].get("inject_year", 0)))
        bp = os.path.join(READ, r + "_bodies.csv")
        if iy == 0 or not os.path.exists(bp):
            continue
        cen = rows(bp)
        roots = {int(x["root"]) for x in cen if int(x["born"]) == iy and int(x["parent"]) < 0}
        root = min(roots) if roots else -1
        print(f"\n== {r}: designed bodies put in in year {iy} (root {root})")
        print("year  bodies matter_t  torn_t kill_eaten_t  swallowed | designed: bodies matter_t of_all  leaf  wood  seed litter carrion  kill | died: hunger thirst poison broken")
        for x in logs[r]:
            y = int(x["year"])
            if y <= iy:
                continue
            torn, kill = float(x["torn"]) * CELL_M2 / 1000, float(x["ate_kill"]) * CELL_M2 / 1000
            mine = [c for c in cen if int(c["year"]) == y and int(c["root"]) == root]
            all_m = sum(float(c["matter"]) for c in cen if int(c["year"]) == y)
            m = sum(float(c["matter"]) for c in mine)
            wt = lambda k: sum(float(c[k]) * float(c["matter"]) for c in mine) / max(m, 1e-30)
            row = {"run": r, "year": y, "bodies": int(x["bodies"]), "matter_t": float(x["body_matter"]) * CELL_M2 / 1000, "torn_t": torn, "kill_eaten_t": kill,
                   "swallowed": kill / torn if torn > 0 else float("nan"), "designed_bodies": sum(int(c["bodies"]) for c in mine), "designed_matter_t": m / 1000,
                   "designed_of_all": m / max(all_m, 1e-30), **{"designed_ate_" + k: wt("ate_" + k) for k in FOODS}}
            des.append(row)
            print(f"{y:4d} {row['bodies']:7d} {row['matter_t']:8.1f} {torn:7.1f} {kill:12.1f} {100 * row['swallowed']:9.0f}% | {row['designed_bodies']:16d} {row['designed_matter_t']:8.2f} {100 * row['designed_of_all']:5.1f}% "
                  + " ".join(f"{100 * row['designed_ate_' + k]:5.1f}" for k in FOODS) + f" | {float(x['died_hunger']):12.0f} {float(x['died_thirst']):6.0f} {float(x['died_poison']):6.0f} {float(x['died_broken']):6.0f}")

    # 4. `all` against e111's `all`: every column of the log but the timings and those e111 does not have.
    same = None
    if "all" in logs and os.path.exists(E111_ALL):
        old = rows(E111_ALL)
        cols = [k for k in old[0] if k not in TIMING]
        diff = [(a["year"], k) for a, b in zip(logs["all"], old) for k in cols if a[k] != b[k]]
        same = len(diff) == 0 and len(old) == len(logs["all"])
        print(f"\n`all` against e111's `all`: {len(cols)} columns over {len(old)} years, " + ("the same to the digit" if same else f"{len(diff)} values differ, the first {diff[:3]}"))

    for name, table in [("read.csv", out), ("layers.csv", layers), ("designed.csv", des)]:
        if not table:
            continue
        keys = list(dict.fromkeys(k for o in table for k in o))
        with open(os.path.join(RES, name), "w", newline="") as f:
            wr = csv.DictWriter(f, fieldnames=keys, restval="", lineterminator="\n")
            wr.writeheader()
            for o in table:
                wr.writerow({k: (f"{v:.6g}" if isinstance(v, float) else v) for k, v in o.items()})
    with open(os.path.join(RES, "provenance.csv"), "w", newline="") as f:
        wr = csv.writer(f, lineterminator="\n")
        wr.writerow(["what", "value"])
        wr.writerow(["runs read (results/read)", " ".join(runs)])
        wr.writerow(["window: the last years of the shortest run, means of the log", f"{window[0]}-{window[-1]}"])
        wr.writerow(["the world without bodies", "nobody, land_biomass over the same years"])
        wr.writerow(["the stands, the cells and the body census", f"as the run ends, year {end}"])
        wr.writerow(["cell, m2 (log sums are kg a m2 summed over cells)", CELL_M2])
        wr.writerow(["the ground", "root + store + seed bank, over leaf + wood + root + store + hanging seed + bank"])
        wr.writerow(["a store's B", "0.001 of its matter (`life.rs`, STORE_SHARE)"])
        wr.writerow(["what a body of height H reaches of a stand", "min(1, H / the stand's height) of its leaves and hanging seed (`body.rs`)"])
        wr.writerow(["heights read, m", " ".join(str(h) for h in HEIGHTS)])
        wr.writerow(["a body's height", f"ext_z x (wet / density / nv)^(1/3); wet = {WET} x tissue + {FAT_WET} x fat; `now` at the row's mean mass, `grown` at its adult mass; quantiles by matter"])
        wr.writerow(["leaf_in_reach", "what a body of the grown p50 height reaches"])
        wr.writerow(["stand heights and wood", "quantiles over stands by their leaves and hanging seed"])
        wr.writerow(["soil fill", "ground / cap of a land cell as the run ends"])
        wr.writerow(["swallowed", "ate_kill / torn of a year, from the log"])
        wr.writerow(["a designed line", "census rows whose root is the founder born in inject_year with no parent; its diet by matter"])
        wr.writerow(["`all` against e111's", "every log column but the timings: " + ("the same to the digit" if same else "not compared" if same is None else "differs")])


if __name__ == "__main__":
    main()
