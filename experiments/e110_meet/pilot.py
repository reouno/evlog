"""Read e110's pilot (#123): the log, the body census and the lines of each run.

    uv run python experiments/e110_meet/pilot.py [results dir]

Prints, a run: the years after the sowing, the last ten years' means the hypotheses are read on, what the leading
body genotypes are, and founders' lines by island. Writes `results/pilot.csv` and `results/sizes.csv` (a row a run and a year) and
`results/provenance.csv` (the window read and every threshold).
"""
import csv
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DIR = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "results", "pilot")
CONTROL = os.path.join(HERE, "..", "e109_metres", "results", "isles1_life1_log.csv")
CELL_M2 = 125.0 ** 2
LAST = 10  # years the levels are read over
FLESH = 0.1  # share of flesh in its diet over which a genotype is read as a flesh eater
BIG = 1.0  # kg grown: over it a genotype is read as a large body
FOODS = ["leaf", "wood", "seed", "litter", "carrion", "kill"]
DEATHS = ["hunger", "thirst", "heat", "cold", "breath", "poison", "age", "form", "broken"]


def rows(path):
    with open(path) as f:
        return list(csv.DictReader(f))


def year_row(x, land_cells):
    """One year of a log: what the pilot is read on."""
    nb = int(x["bodies"])
    ate = {k: float(x["ate_" + k]) for k in FOODS}
    eaten = sum(ate.values())
    died = {k: float(x["died_" + k]) for k in DEATHS}
    matter = float(x["body_matter"]) * CELL_M2
    return {
        "year": int(x["year"]),
        "bodies": nb,
        "matter_t": matter / 1000,
        "kg_a_body": matter / max(nb, 1),
        "land_cells": float(x["body_land_cells"]),
        "sea_share": float(x["body_sea_share"]),
        "land_biomass": float(x["land_biomass"]),
        "land_cover": float(x["land_cover"]),
        "eaten_of_gpp": (eaten - ate["carrion"] - ate["kill"]) / max(float(x["gpp"]), 1e-30),
        "flesh_share": (ate["carrion"] + ate["kill"]) / max(eaten, 1e-30),
        "kill_share": ate["kill"] / max(eaten, 1e-30),
        "catches": float(x["catches"]),
        "breaks": float(x["breaks"]),
        "torn_t": float(x["torn"]) * CELL_M2 / 1000,
        "riders": float(x["riders"]),
        "first_death": max(died, key=died.get),
        "broken_share": died["broken"] / max(sum(died.values()), 1),
        "births": float(x["births"]),
        "genotypes": int(x["body_genotypes"]),
        "s_year": float(x["ms_step"]) * 11.88,
        "body_s_year": sum(float(x[k]) for k in ("secs_decide", "secs_meet", "secs_live", "secs_last")),
        "err": max(float(x["water_err"]), float(x["a_err"]), float(x["b_err"]), float(x["c_err"])),
    }


def main():
    runs = sorted(f[: -len("_log.csv")] for f in os.listdir(DIR) if f.endswith("_log.csv"))
    control = {int(x["year"]): float(x["land_biomass"]) for x in rows(CONTROL)} if os.path.exists(CONTROL) else {}
    out = []
    for run in runs:
        log = rows(os.path.join(DIR, run + "_log.csv"))
        par = rows(os.path.join(DIR, run + "_row.csv"))[0] if os.path.exists(os.path.join(DIR, run + "_row.csv")) else {}
        sow = int(float(par.get("body_sow", 40)))
        ys = [year_row(x, None) for x in log if int(x["year"]) > sow]
        if not ys:
            print(f"{run}: no year with bodies yet ({len(log)} years)")
            continue
        print(f"\n== {run}: years {ys[0]['year']}-{ys[-1]['year']} (bodies sown in year {sow})")
        print("year  bodies  matter_t kg/body land%  sea%  land_bio (control) eaten/gpp flesh%  kill% catches  breaks torn_t first_death broken%  s/yr (bodies)")
        for y in ys:
            if y is ys[0] or y is ys[-1] or y["year"] % 5 == 0:
                print(
                    f"{y['year']:4d} {y['bodies']:7d} {y['matter_t']:8.0f} {y['kg_a_body']:7.0f} {100 * y['land_cells']:5.1f} {100 * y['sea_share']:5.0f} "
                    f"{y['land_biomass']:8.3f} ({control.get(y['year'], float('nan')):.3f}) {100 * y['eaten_of_gpp']:8.1f} {100 * y['flesh_share']:6.1f} {100 * y['kill_share']:6.1f} "
                    f"{y['catches']:8.0f} {y['breaks']:7.0f} {y['torn_t']:6.0f} {y['first_death']:>11s} {100 * y['broken_share']:6.0f} {y['s_year']:6.0f} ({y['body_s_year']:.0f})"
                )
        last = ys[-LAST:]
        mean = lambda k: sum(y[k] for y in last) / len(last)
        deaths = {}
        for y in last:
            deaths[y["first_death"]] = deaths.get(y["first_death"], 0) + 1
        print(
            f"last {len(last)} years: bodies {mean('bodies'):.0f}, matter {mean('matter_t'):.0f} t ({mean('kg_a_body'):.0f} kg a body), eaten/gpp {100 * mean('eaten_of_gpp'):.1f}%, "
            f"flesh {100 * mean('flesh_share'):.1f}% (kills {100 * mean('kill_share'):.1f}%), land biomass {mean('land_biomass'):.3f}, first death {max(deaths, key=deaths.get)}, "
            f"a year {mean('s_year'):.0f} s (bodies {mean('body_s_year'):.0f} s), worst ledger {max(y['err'] for y in ys):.1e}"
        )
        for y in ys:
            out.append({"run": run, **y})
        # the census of the last year: who holds the matter
        cen = os.path.join(DIR, run + "_bodies.csv")
        if os.path.exists(cen):
            c = [x for x in rows(cen) if int(x["year"]) == ys[-1]["year"]]
            tot = sum(float(x["matter"]) for x in c) or 1.0
            c.sort(key=lambda x: -float(x["matter"]))
            share = lambda f: sum(float(x["matter"]) for x in c if f(x)) / tot
            roots = {}
            for x in c:
                roots[x["root"]] = roots.get(x["root"], 0.0) + float(x["matter"]) / tot
            top = sorted(roots.items(), key=lambda kv: -kv[1])
            masses = sorted((float(x["adult_mass"]), float(x["matter"])) for x in c)
            acc, p10, p90 = 0.0, None, None
            for m, w in masses:
                acc += w / tot
                if p10 is None and acc >= 0.1:
                    p10 = m
                if p90 is None and acc >= 0.9:
                    p90 = m
            print(
                f"census year {ys[-1]['year']}: {len(c)} genotypes; founders' lines {len(top)} (largest {100 * top[0][1]:.0f}%, next {100 * top[1][1] if len(top) > 1 else 0:.0f}%); "
                f"adult mass p10-p90 by matter {p10:.3g}-{p90:.3g} kg; at sea {100 * share(lambda x: float(x['sea']) > 0.5):.0f}%; "
                f"flesh eaters (> {FLESH:.0%} of the diet) {100 * share(lambda x: float(x['ate_carrion']) + float(x['ate_kill']) > FLESH):.1f}% of the matter, "
                f"killers (kills > {FLESH:.0%}) {100 * share(lambda x: float(x['ate_kill']) > FLESH):.1f}%; with a pull {100 * share(lambda x: any(abs(float(x['pull_' + k])) > 0 for k in ('one', 'size', 'alike', 'fat', 'near', 'coming'))):.0f}%"
            )
            print("  root bodies animals matter_kg adult_kg sea v_top reach km/yr leaf wood seed litter carrion kill kills bite hard_f glue cmp")
            for x in c[:8]:
                g = lambda k: float(x[k])
                print(
                    f"  {x['root']:>4s} {int(g('bodies')):6d} {g('animals'):8.3g} {g('matter'):8.3g} {g('adult_mass'):8.3g} {g('sea'):4.2f} {g('v_top'):5.2f} {g('reach'):5.0f} {g('travel_km_yr'):6.0f} "
                    f"{g('ate_leaf'):4.2f} {g('ate_wood'):4.2f} {g('ate_seed'):4.2f} {g('ate_litter'):6.2f} {g('ate_carrion'):7.2f} {g('ate_kill'):4.2f} {g('kills'):7.3g} {g('bite'):5.3f} {g('hard_front'):5.3f} {g('glue_front'):4.2f} {g('cmp'):5.3f}"
                )
        # founders' lines by island in the last year
        lin = os.path.join(DIR, run + "_lines.csv")
        if os.path.exists(lin):
            l = [x for x in rows(lin) if int(x["year"]) == ys[-1]["year"]]
            isles = {}
            for x in l:
                isles.setdefault(int(x["island"]), {})[x["root"]] = float(x["matter"])
            parts = []
            for i in sorted(isles):
                if i > 8:
                    continue
                m = isles[i]
                t = sum(m.values()) or 1.0
                lead = max(m, key=m.get)
                parts.append(f"{'sea' if i == 0 else 'island ' + str(i)}: {t / 1000:.0f} t, {len(m)} lines, line {lead} {100 * m[lead] / t:.0f}%")
            print("  " + "; ".join(parts))
    # a row a run and a year off the censuses and the lines, so that a report needs neither
    sizes = []
    for run in runs:
        cen, lin = os.path.join(DIR, run + "_bodies.csv"), os.path.join(DIR, run + "_lines.csv")
        if not (os.path.exists(cen) and os.path.exists(lin)):
            continue
        by, lines = {}, {}
        for x in rows(cen):
            by.setdefault(int(x["year"]), []).append(x)
        for x in rows(lin):
            lines.setdefault(int(x["year"]), set()).add(x["root"])
        for y in sorted(by):
            c = by[y]
            tot = sum(float(x["matter"]) for x in c) or 1.0
            share = lambda f: sum(float(x["matter"]) for x in c if f(x)) / tot
            sizes.append({
                "run": run,
                "year": y,
                "genotypes": len(c),
                "lines": len(lines.get(y, ())),
                "over_1kg": share(lambda x: float(x["adult_mass"]) > BIG),
                "flesh_eaters": share(lambda x: float(x["ate_carrion"]) + float(x["ate_kill"]) > FLESH),
                "travel_km_yr": sum(float(x["matter"]) * float(x["travel_km_yr"]) for x in c) / tot,
                "from_birth_km": sum(float(x["matter"]) * float(x["from_birth_km"]) for x in c) / tot,
            })
    if sizes:
        with open(os.path.join(HERE, "results", "sizes.csv"), "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(sizes[0].keys()))
            w.writeheader()
            w.writerows(sizes)
    if out:
        with open(os.path.join(HERE, "results", "pilot.csv"), "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(out[0].keys()))
            w.writeheader()
            w.writerows(out)
        with open(os.path.join(HERE, "results", "provenance.csv"), "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["what", "value"])
            w.writerow(["runs", " ".join(runs)])
            w.writerow(["years read a run", f"{out[0]['year']}-{max(y['year'] for y in out)}"])
            w.writerow(["levels: the last years", LAST])
            w.writerow(["a flesh eater: flesh over this share of its diet", FLESH])
            w.writerow(["a large body: adult mass over, kg", BIG])
            w.writerow(["a cell, m2", CELL_M2])
            w.writerow(["control without bodies", "e109 isles1_life1 (land_biomass)"])


if __name__ == "__main__":
    main()
