"""Read part 3, the hunter's fate: `all200` against the lines its README wrote before the run (#116).

    uv run python experiments/e113_sea_catch/fate.py

Reads `results/pilot/all200_{bodies,log,where}.csv` and `all_log.csv`. A hunter is crash.py's: a genotype with ate_kill
over half of its lifetime diet. Writes `results/fate.csv` (a row a year with a census), `results/fate_decades.csv`,
`results/fate_islands.csv` (hunters' matter by island, every tenth year) and adds rows to `results/provenance.csv`.
"""
import csv
import os

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results")
P = os.path.join(RES, "pilot")
RUN = "all200"
HUNTER = 0.5  # crash.py's
SETTLE = 2.0  # hunters' matter within this factor over the last LAST years
LAST = 30
GROW = (0.01, 0.10)  # kills of the diet over a decade: the pilot's line, rung 3's
CRASH = 0.1  # bodies under this share of their year-100 number
SKIP = {"ms_step", "secs_decide", "secs_meet", "secs_live", "secs_last"}  # timing columns


def rows(path):
    with open(path) as f:
        return list(csv.DictReader(f))


def write(name, table):
    with open(os.path.join(RES, name), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(table[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(table)


def main():
    log = {int(r["year"]): r for r in rows(os.path.join(P, RUN + "_log.csv"))}
    old = rows(os.path.join(P, "all_log.csv"))
    same = all(r[k] == log[int(r["year"])][k] for r in old for k in r if k not in SKIP)
    ate = lambda x: sum(float(x[k]) for k in x if k.startswith("ate_"))
    by, ids = {}, {}
    with open(os.path.join(P, RUN + "_bodies.csv")) as f:
        for r in csv.DictReader(f):
            y = int(r["year"])
            a = by.setdefault(y, [0, 0.0, 0.0, 0.0, set()])
            a[3] += float(r["matter"])
            if float(r["ate_kill"]) > HUNTER:
                a[0] += 1
                a[1] += float(r["bodies"])
                a[2] += float(r["matter"])
                a[4].add(r["root"])
                ids.setdefault(y, set()).add(r["id"])
    out = []
    for y, a in sorted(by.items()):
        x = log[y]
        out.append({"year": y, "genotypes": a[0], "roots": len(a[4]), "bodies": f"{a[1]:.0f}", "matter_t": f"{a[2] / 1000:.1f}", "of_matter": f"{a[2] / a[3]:.4f}",
                    "kill_of_diet": f"{float(x['ate_kill']) / ate(x):.4f}", "all_bodies": x["bodies"]})
    write("fate.csv", out)
    dec = []
    for y1 in range(50, max(log) + 1, 10):
        ys = [y for y in range(y1 - 9, y1 + 1) if y in log]
        dec.append({"years": f"{ys[0]}-{ys[-1]}", "kill_of_diet": f"{sum(float(log[y]['ate_kill']) for y in ys) / sum(ate(log[y]) for y in ys):.4f}",
                    "bodies": f"{sum(float(log[y]['bodies']) for y in ys) / len(ys):.0f}", "ms_step": f"{sum(float(log[y]['ms_step']) for y in ys) / len(ys):.1f}"})
    write("fate_decades.csv", dec)
    isl = {}
    for r in rows(os.path.join(P, RUN + "_where.csv")):
        y = int(r["year"])
        a = isl.setdefault((y, r["island"]), [0.0, 0.0])
        a[0] += float(r["matter"])
        if r["id"] in ids.get(y, ()):
            a[1] += float(r["matter"])
    write("fate_islands.csv", [{"year": y, "island": i, "matter_t": f"{a[0] / 1000:.1f}", "hunter_t": f"{a[1] / 1000:.1f}", "hunter_share": f"{a[1] / a[0]:.4f}" if a[0] else ""}
                               for (y, i), a in sorted(isl.items(), key=lambda kv: (kv[0][0], int(kv[0][1])))])
    end = max(by)
    last = [float(o["matter_t"]) for o in out if o["year"] > end - LAST]
    settles = by[end][0] > 0 and min(last) > 0 and max(last) / min(last) <= SETTLE
    top = max(float(d["kill_of_diet"]) for d in dec)
    crashes = by[end][0] == 0 or float(log[end]["bodies"]) < CRASH * float(log[100]["bodies"])
    print(f"first 100 years equal to all's (but timing): {same}")
    for o in out:
        print(o)
    for d in dec:
        print(d)
    print(f"settles {settles} (last {LAST} y matter {min(last):.1f}-{max(last):.1f} t); grows {top >= GROW[0]} / {top >= GROW[1]} (top decade {top:.4f}); crashes {crashes}")
    prov = os.path.join(RES, "provenance.csv")
    keep = [r for r in csv.reader(open(prov)) if not r[0].startswith("fate")]
    keep += [["fate: the run", f"results/pilot/{RUN}, years 1-{end}; first 100 years equal to all's but timing columns: {same}"],
             ["fate: hunter", f"a genotype with ate_kill over {HUNTER} of its lifetime diet (_bodies.csv, every year), as crash.py"],
             ["fate: settles", f"hunters alive at year {end}, their matter within a factor {SETTLE} over the last {LAST} years: {settles} ({min(last):.1f}-{max(last):.1f} t)"],
             ["fate: grows", f"kill of the diet over a decade at least {GROW[0]}, then {GROW[1]} (log): top decade {top:.4f}"],
             ["fate: crashes", f"no hunters at year {end}, or bodies under {CRASH} of year 100's (log): {crashes}"],
             ["fate: islands", "fate_islands.csv: matter of hunter genotypes by island from _where.csv (every tenth year), island 0 the sea"]]
    with open(prov, "w", newline="") as f:
        csv.writer(f, lineterminator="\n").writerows(keep)


if __name__ == "__main__":
    main()
