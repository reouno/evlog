"""Read e112's pilot and its control by decade, against e109's world without bodies, with the bodies read by the
open measure (`analysis/ways.py`). The control is e111's pilot run on to year 140 (`e111_holds/results/pilot/
all140_*`); the pilot is `results/pilot/layers_*`.

    uv run python experiments/e112_layers/control.py [pilot]

Writes `results/<control|pilot>.csv` (a row a decade) and `results/<control|pilot>_ways.csv` (the groups of the last
census), and adds its rows to `results/provenance.csv`. The body censuses (66-71 MB) are not committed: without one
beside its log the files are left as they are.
"""
import csv
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", ".."))
from analysis import ways  # noqa: E402

RES = os.path.join(HERE, "results")
NAME = sys.argv[1] if len(sys.argv) > 1 else "control"
PILOT = {"control": os.path.join(HERE, "..", "e111_holds", "results", "pilot", "all140"),
         "pilot": os.path.join(RES, "pilot", "layers")}[NAME]
BARE = os.path.join(HERE, "..", "e109_metres", "results", "isles1_life1_log.csv")
CELL_M2 = 125.0 ** 2
SOWN = 40  # the year the bodies were sown
BIG = 1.0  # kg: an adult mass over it is a large body
FLESH = 0.1  # share of flesh in its lifetime diet over which a genotype is read as a flesh eater
LINE = 0.01  # share of the bodies' matter over which a founder's line is counted
BACK = 10  # years back a census is matched against, for change
FOODS = ["leaf", "wood", "seed", "litter", "carrion", "kill", "root", "store", "bank"]  # those in the log are read


def rows(path):
    with open(path) as f:
        return list(csv.DictReader(f))


def mean(v):
    v = list(v)
    return sum(v) / max(len(v), 1)


def main():
    log = {int(r["year"]): r for r in rows(PILOT + "_log.csv")}
    bare = {int(r["year"]): r for r in rows(BARE)}
    end = max(log)
    foods = [k for k in FOODS if "ate_" + k in log[end]]
    where = {}
    if os.path.exists(PILOT + "_where.csv"):
        for r in rows(PILOT + "_where.csv"):
            where.setdefault(int(r["year"]), []).append((r["id"], r["island"], float(r["matter"])))
    if not os.path.exists(PILOT + "_bodies.csv"):
        print("no body census beside the log: control.csv is left as it is")
        return
    cen = {}
    for r in rows(PILOT + "_bodies.csv"):
        cen.setdefault(int(r["year"]), []).append(r)
    out, reads = [], {}
    for y1 in range(SOWN + 10, end + 1, 10):
        ys = range(y1 - 9, y1 + 1)
        f = lambda k, src=log: mean(float(src[y][k]) for y in ys)
        ate = {k: f("ate_" + k) for k in foods}
        o, rd = ways.read(cen[y1])
        reads[y1] = rd
        _, w, kept, _ = rd
        share = lambda keep: sum(float(r["matter"]) for r in kept if keep(r)) / w.sum()
        wm = lambda k: sum(float(r[k]) * float(r["matter"]) for r in kept) / w.sum()
        lines = {}
        for r in kept:
            lines[r["root"]] = lines.get(r["root"], 0.0) + float(r["matter"]) / w.sum()
        out.append({
            "years": f"{ys[0]}-{ys[-1]}",
            "land_biomass": f("land_biomass"), "bare": f("land_biomass", bare), "of_bare": f("land_biomass") / f("land_biomass", bare),
            "land_cover": f("land_cover"), "gpp_of_bare": f("gpp") / f("gpp", bare), "sea_biomass_of_bare": f("sea_biomass") / f("sea_biomass", bare),
            "land_b_soil": f("land_b_soil"), "land_b_plants": f("land_b_plants"),
            "bodies": f("bodies"), "matter_t": f("body_matter") * CELL_M2 / 1000, "sea_share": f("body_sea_share"),
            "litter_share": ate["litter"] / sum(ate.values()), "flesh_share": (ate["carrion"] + ate["kill"]) / sum(ate.values()),
            "ground_share": f("body_ground") if "body_ground" in log[end] else 0.0, "crown_share": f("body_crown") if "body_crown" in log[end] else 0.0,
            "layer_food_share": sum(ate[k] for k in ("root", "store", "bank", "leaf") if k in ate) / sum(ate.values()),
            "presses": f("presses"), "died_broken": f("died_broken"), "died_poison": f("died_poison"), "died_thirst": f("died_thirst"),
            "secs_year": f("ms_step") * 11880 / 1000,
            "census": y1, "over_1kg": share(lambda r: float(r["adult_mass"]) > BIG),
            "flesh_eaters": share(lambda r: float(r["ate_carrion"]) + float(r["ate_kill"]) > FLESH),
            "lines": sum(1 for v in lines.values() if v > LINE),
            "frame": wm("frame"), "muscle": wm("muscle"), "gut": wm("gut"),
            "ways_hill": o["groups_hill"], "top_way": o["top_group_share"], **{k: o[k] for k in o if k.startswith("hill_")},
            "held": ways.held(where[y1], {r["id"]: int(gi) for r, gi in zip(kept, rd[3])}) if y1 in where else "",
            "changed": ways.changed(rd, reads[y1 - BACK]) if y1 - BACK in reads else "",
            "new_since_first": ways.changed(rd, reads[SOWN + 10]) if y1 > SOWN + 10 else "",
            "err": max(max(float(log[y][k]) for k in ("water_err", "a_err", "b_err", "c_err")) for y in ys),
        })
    last = max(reads)
    d, w, kept, g = reads[last]
    groups = []
    for gi, m in sorted(ways.masses(g, w).items(), key=lambda kv: -kv[1]):
        if m / w.sum() < LINE:
            break
        r = kept[gi]
        groups.append({"census": last, "share": m / w.sum(), "genotypes": int((g == gi).sum()), "leader": r["id"], "adult_mass": r["adult_mass"], "sea": r["sea"],
                       "travel_km_yr": r["travel_km_yr"], **{k: r[k] for k in ways.MAKE}, **{"ate_" + k: r["ate_" + k] for k in foods}, "tip_front": r["tip_front"], "press_one": r["press_one"]})

    print(f"{NAME} ({PILOT}) to year {end}, by decade; the land against e109's world without bodies")
    print("years    land   bare of_bare cover gpp/bare  soilB plantB  bodies matter_t sea% litter% flesh% ground% crown% layerfood% presses broken poison thirst s/year | >1kg flesh_eaters lines frame muscle gut | ways top diet place size range make held changed new_since_first")
    for o in out:
        ch = f"{o['changed']:.3f} {o['new_since_first']:.3f}" if o["changed"] != "" else "    -"
        print(f"{o['years']:8s} {o['land_biomass']:.3f} {o['bare']:.3f} {100 * o['of_bare']:5.0f}% {100 * o['land_cover']:4.0f}% {o['gpp_of_bare']:7.2f} {o['land_b_soil']:6.2f} {o['land_b_plants']:6.1f} {o['bodies']:7.0f} {o['matter_t']:8.0f} {100 * o['sea_share']:3.0f} {100 * o['litter_share']:7.2f} {100 * o['flesh_share']:6.2f} {100 * o['ground_share']:7.2f} {100 * o['crown_share']:6.2f} {100 * o['layer_food_share']:10.2f} {o['presses']:7.0f} {o['died_broken']:6.0f} {o['died_poison']:6.0f} {o['died_thirst']:6.0f} {o['secs_year']:6.0f} | "
              f"{100 * o['over_1kg']:4.2f} {100 * o['flesh_eaters']:11.2f} {o['lines']:5d} {o['frame']:5.2f} {o['muscle']:6.2f} {o['gut']:4.2f} | {o['ways_hill']:4.2f} {o['top_way']:.2f} {o['hill_diet']:4.2f} {o['hill_place']:5.2f} {o['hill_size']:4.2f} {o['hill_range']:5.2f} {o['hill_make']:4.2f} {o['held'] if o['held'] == '' else f"{o['held']:.3f}"} {ch}")
    print(f"the ways of year {last} holding {LINE:.0%} of the matter")
    for x in groups:
        print(f"  {100 * x['share']:5.1f}% {x['genotypes']:5d} genotypes; leader: adult {float(x['adult_mass']):.3g} kg, {100 * float(x['sea']):.0f}% at sea, {float(x['travel_km_yr']):.0f} km a year, "
              + " ".join(f"{k} {float(x[k]):.2f}" for k in ways.MAKE) + "; eats " + " ".join(f"{k} {float(x['ate_' + k]):.2f}" for k in foods if float(x["ate_" + k]) >= 0.005))

    for name, table in [(NAME + ".csv", out), (NAME + "_ways.csv", groups)]:
        with open(os.path.join(RES, name), "w", newline="") as f:
            wr = csv.DictWriter(f, fieldnames=list(table[0]), lineterminator="\n")
            wr.writeheader()
            for o in table:
                wr.writerow({k: (f"{v:.6g}" if isinstance(v, float) else v) for k, v in o.items()})
    prov = os.path.join(RES, "provenance.csv")
    keep = [r for r in csv.reader(open(prov))] if os.path.exists(prov) else [["what", "value"]]
    keep = [r for r in keep if not r[0].startswith(NAME)]
    keep += [[f"{NAME}{k[7:]}", v] for k, v in [
        ["control: the run", f"{os.path.relpath(PILOT, os.path.join(HERE, '..'))}, years {SOWN + 1}-{end}; decades as means of the log, the body census of each decade's last year"],
        ["control: the world without bodies", "e109_metres/results/isles1_life1_log.csv, the same years"],
        ["control: a large body, a flesh eater, a line", f"adult mass over {BIG} kg; flesh over {FLESH} of its lifetime diet; a founder's line over {LINE} of the matter"],
        ["control: the ways", ways.provenance()],
        ["control: changed, new_since_first", f"the matter of a census in ways with no match in the census {BACK} years before, and in the census of year {SOWN + 10} (analysis/ways.py)"],
        ["control: held", "ways.held over the matter of each genotype by island (_where.csv, every tenth year); \"\" where no table"],
        ["control: layers", "ground_share, crown_share: body_ground, body_crown of the log; layer_food_share: root, store, bank and leaf in the diet"],
        ["control: seconds a year", "ms_step x 11,880 steps (six threads on Ubuntu; " + ("from year 127 five other runs shared the machine)" if NAME == "control" else "beside the trace runs early on)")],
    ]]
    with open(prov, "w", newline="") as f:
        csv.writer(f, lineterminator="\n").writerows(keep)


if __name__ == "__main__":
    main()
