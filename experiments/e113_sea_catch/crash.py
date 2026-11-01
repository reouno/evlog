"""Read `hungry70` against `all` by island (#132, hypothesis 5), and who eats flesh in each run.

    uv run python experiments/e113_sea_catch/crash.py

Reads `results/pilot/<run>_{lines,bodies,log}.csv` and the designed line's root from `hungry70.err`. Writes
`results/crash.csv`, `results/crash_reach.csv`, `results/hunters.csv`, `results/flesh_eaters.csv` and adds rows to `results/provenance.csv`.
"""
import csv
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results")
P = os.path.join(RES, "pilot")
INJECT = 70
YEARS = [70, 71, 72, 73, 74, 75, 80, 85, 90, 95, 100]
FLESH = 0.1
HUNTER = 0.5


def rows(path):
    with open(path) as f:
        return list(csv.DictReader(f))


def write(name, table):
    with open(os.path.join(RES, name), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(table[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(table)


def sums(lines, keep):
    out = {}
    for r in lines:
        if keep(r):
            k = (int(r["year"]), "1" if r["island"] == "1" else ("sea" if r["island"] == "0" else "other"))
            a = out.setdefault(k, [0, 0.0, 0.0])
            a[0] += float(r["bodies"])
            a[1] += float(r["matter"])
            a[2] += float(r["animals"])
    return out


def main():
    root = re.search(r"designed body (\d+)", open(os.path.join(P, "hungry70.err")).read()).group(1)
    la, lh = rows(os.path.join(P, "all_lines.csv")), rows(os.path.join(P, "hungry70_lines.csv"))
    A, H, D = sums(la, lambda r: True), sums(lh, lambda r: r["root"] != root), sums(lh, lambda r: r["root"] == root)
    out = []
    for y in YEARS:
        o = {"year": y}
        for w in ("1", "other", "sea"):
            a, h, d = A.get((y, w), [0, 0.0, 0.0]), H.get((y, w), [0, 0.0, 0.0]), D.get((y, w), [0, 0.0, 0.0])
            o |= {f"all_{w}_bodies": a[0], f"rest_{w}_bodies": h[0], f"line_{w}_bodies": d[0], f"rest_of_all_{w}_matter": f"{h[1] / a[1]:.3f}" if a[1] else "",
                  f"all_{w}_animals": f"{a[2]:.3g}", f"rest_{w}_animals": f"{h[2]:.3g}"}
        out.append(o)
        print(o)
    write("crash.csv", out)
    first = {}
    for r in lh:
        if r["root"] == root:
            k = int(r["island"])
            first[k] = min(first.get(k, 999), int(r["year"]))
    write("crash_reach.csv", [{"island": k, "first_year": v} for k, v in sorted(first.items())])
    print("the line first stands on:", sorted(first.items(), key=lambda kv: kv[1]))
    hunters = []
    for run in ("all", "hungry70"):
        by = {}
        for r in rows(os.path.join(P, run + "_bodies.csv")):
            if float(r["ate_kill"]) > HUNTER and r["root"] != root:
                a = by.setdefault(int(r["year"]), [0, 0.0, 0.0])
                a[0] += 1
                a[1] += float(r["bodies"])
                a[2] += float(r["matter"])
        log = {int(x["year"]): x for x in rows(os.path.join(P, run + "_log.csv"))}
        for y, a in sorted(by.items()):
            x = log[y]
            ate = sum(float(x[k]) for k in x if k.startswith("ate_"))
            hunters.append({"run": run, "year": y, "genotypes": a[0], "bodies": f"{a[1]:.0f}", "matter_t": f"{a[2] / 1000:.1f}", "kill_of_diet": f"{float(x['ate_kill']) / ate:.4f}", "all_bodies": x["bodies"]})
    write("hunters.csv", hunters)
    eat = []
    for run in ("all", "sow41", "hungry70"):
        cen = rows(os.path.join(P, run + "_bodies.csv"))
        for y in (70, 80, 90, 100):
            c = [r for r in cen if int(r["year"]) == y]
            tot = sum(float(r["matter"]) for r in c)
            fl = [r for r in c if float(r["ate_carrion"]) + float(r["ate_kill"]) > FLESH]
            m = sum(float(r["matter"]) for r in fl)
            roots = {}
            for r in fl:
                roots[r["root"]] = roots.get(r["root"], 0.0) + float(r["matter"])
            top = sorted(fl, key=lambda r: -float(r["matter"]))[:1]
            o = {"run": run, "year": y, "genotypes": len(fl), "bodies": sum(float(r["bodies"]) for r in fl), "matter_share": f"{m / tot:.4f}", "kills": f"{sum(float(r['kills']) * float(r['animals']) for r in fl):.3g}",
                 "roots": len(roots), "top_root": max(roots, key=roots.get) if roots else "", "top_is_designed": bool(roots) and run == "hungry70" and max(roots, key=roots.get) == root}
            if top:
                t = top[0]
                o |= {"leader_adult_kg": t["adult_mass"], "leader_flesh": f"{float(t['ate_carrion']) + float(t['ate_kill']):.2f}", "leader_kill": t["ate_kill"], "leader_sea": t["sea"], "leader_muscle": t["muscle"], "leader_gut": t["gut"], "leader_km_yr": t["travel_km_yr"], "leader_tip": t["tip_front"], "leader_root": t["root"]}
            eat.append(o)
            print(o)
    write("flesh_eaters.csv", eat)
    prov = os.path.join(RES, "provenance.csv")
    keep = [r for r in csv.reader(open(prov)) if not r[0].startswith("crash")]
    keep += [["crash: the runs", "results/pilot/all, hungry70; the designed line: root " + root + " (hungry70.err)"],
             ["crash: islands", "_lines.csv by year: island 1, the other islands together, the sea (0)"],
             ["crash: rest_of_all", "matter of hungry70's bodies not of the designed line over all's matter, same place and year"],
             ["crash: hunters", f"hunters.csv: genotypes with ate_kill over {HUNTER} of the lifetime diet, not of the designed line, a row a year; kill_of_diet from the log"],
             ["crash: flesh eater", f"a genotype with ate_carrion + ate_kill over {FLESH} of its lifetime diet (_bodies.csv)"]]
    with open(prov, "w", newline="") as f:
        csv.writer(f, lineterminator="\n").writerows(keep)


if __name__ == "__main__":
    main()
