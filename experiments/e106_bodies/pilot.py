"""Read a pilot of e106: does the world stand with bodies, what do they eat, what kills them, what they cost.

uv run python experiments/e106_bodies/pilot.py <prefix>
"""

import csv
import sys

prefix = sys.argv[1]
log = list(csv.DictReader(open(f"{prefix}_log.csv")))
deaths = [k for k in log[0] if k.startswith("died_")]
cols = ["year", "bodies", "body_land_cells", "body_sea_share", "body_genotypes", "births", "splits"]
print(" ".join(f"{c[:10]:>10}" for c in cols + ["deaths", "top_cause", "ate/gpp", "leaf/ate", "litter/ate", "body_s", "year_s", "errs"]))
for r in log:
    if int(r["bodies"]) == 0 and float(r["births"]) == 0:
        continue
    d = {k[5:]: float(r[k]) for k in deaths}
    tot = sum(d.values())
    top = max(d, key=d.get) if tot else "-"
    ate = sum(float(r[k]) for k in ["ate_leaf", "ate_wood", "ate_seed", "ate_litter"])
    gpp = float(r["gpp"])
    err = max(float(r[k]) for k in ["water_err", "a_err", "b_err", "c_err"])
    year_s = float(r["ms_step"]) * 11880 / 1000
    vals = [r[c] for c in cols] + [
        f"{tot:.0f}",
        top,
        f"{ate / gpp:.2e}" if gpp else "-",
        f"{float(r['ate_leaf']) / ate:.3f}" if ate else "-",
        f"{float(r['ate_litter']) / ate:.3f}" if ate else "-",
        r["body_secs"],
        f"{year_s:.1f}",
        f"{err:.0e}",
    ]
    print(" ".join(f"{v[:10]:>10}" for v in vals))

rows = list(csv.DictReader(open(f"{prefix}_bodies.csv")))
last = max(int(r["year"]) for r in rows)
top = sorted([r for r in rows if int(r["year"]) == last], key=lambda r: -float(r["matter"]))[:12]
cols = ["id", "born", "bodies", "matter", "mass", "adult_mass", "egg", "nv", "muscle", "gut", "fat", "frame", "bite", "sea", "travel_yr", "ate_leaf", "ate_wood", "ate_seed", "ate_litter"]
print(f"\nyear {last}: the heaviest genotypes")
print(" ".join(f"{c[:9]:>9}" for c in cols))
for r in top:
    print(" ".join(f"{float(r[c]):>9.3g}" for c in cols))
