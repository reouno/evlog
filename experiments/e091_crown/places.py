#!/usr/bin/env python3
"""e091's second reading: the crown against the floor, form by form, and the measure's own share of the fall.

Run from the repo root: `uv run python experiments/e091_crown/places.py` (a few minutes, one core).
It writes three small tables the report draws from:

- `results/places.csv` - the grown bodies of each run by where they stand (the crown or the floor): what they
  eat, what they weigh now and at birth, the blocks they have lost, how far they are from where they were born,
  their age and the share carrying a tooth that opens wood.
- `results/forms.csv` - every birth form with 50 grown bodies or more: its bodies and the share of them standing
  in a crown. A form bound to the crown would sit at 1.
- `results/measure.csv` - kinds at a census and kinds kept to a place, read as they are and again with the crown
  counted as land (the same censuses, `medium` 3 read as 0), which separates the fall in the world from the fall
  in the measure (a kind keeps to a place when 90% of its bodies stand in one medium, so a body that climbs and
  comes down breaks it for its whole form).
"""
import csv
import importlib.util
import os
import shutil
import statistics as st
import tempfile
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
LADDER = os.path.join(ROOT, "experiments", "e081_drink", "results", "ladder")
SEEDS = (9, 10, 11)
spec = importlib.util.spec_from_file_location("e091_sweep", os.path.join(HERE, "sweep.py"))
sweep = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sweep)


def diet(rs):
    plant = sum(float(r["plant"]) for r in rs)
    fruit = sum(float(r["fruit"]) for r in rs)
    wood = sum(float(r["wood"]) for r in rs)
    algae = sum(float(r["algae"]) for r in rs)
    litter = sum(float(r["detritus"]) for r in rs)
    kills = sum(float(r["killed"]) for r in rs)
    carrion = sum(float(r["scavenged"]) for r in rs)
    total = max(plant + kills + carrion, 1e-9)
    return {"grass": (plant - fruit - wood - algae - litter) / total, "fruit": fruit / total,
            "browse": wood / total, "water": (algae + litter) / total, "kills": kills / total,
            "carrion": carrion / total}


def main():
    places, forms, measure = [], [], []
    for s in SEEDS:
        pre = os.path.join(HERE, "results", f"c1225_life{s}_crown")
        rows = [r for r in csv.DictReader(open(pre + "_agents.csv")) if int(r["age"]) >= 300]
        for name, want in (("crown", "3"), ("floor", "0")):
            rs = [r for r in rows if r["medium"] == want]
            places.append({"run": f"crown {s}", "place": name, "bodies": len(rs), "share": len(rs) / len(rows),
                           "mass": st.median(float(r["mass"]) for r in rs),
                           "born_mass": st.median(float(r["born_mass"]) for r in rs),
                           "lost": st.median(float(r["born_mass"]) - float(r["mass"]) for r in rs),
                           "travel": st.median(float(r["travel"]) for r in rs),
                           "age": st.median(int(r["age"]) for r in rs),
                           "wood": st.median(float(r["crown"]) for r in rs),
                           "tooth": sum(float(r["bite_any"]) >= 3 for r in rs) / len(rs),
                           **diet(rs)})
        # every birth form of 50 grown bodies or more, and how much of it stands in a crown
        run = sweep.kinds.Run(f"crown {s}", pre)
        unit = run.forms()
        per, up = Counter(), Counter()
        for i, r in enumerate(run.grown):
            per[unit[i]] += 1
            up[unit[i]] += r["medium"] == "3"
        for u, n in per.items():
            if n >= 50:
                forms.append({"run": f"crown {s}", "bodies": n, "share": n / len(run.grown), "in_crowns": up[u] / n})
        # the same censuses with the crown read as the land
        k, _ = sweep.e075.read_run(f"crown {s}", pre)
        tmp = tempfile.mkdtemp()
        merged = os.path.join(tmp, "merged")
        for suffix in ("_log.csv", "_row.csv"):
            shutil.copy(pre + suffix, merged + suffix)
        with open(pre + "_agents.csv") as fh:
            rr = list(csv.DictReader(fh))
        with open(merged + "_agents.csv", "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rr[0].keys()))
            w.writeheader()
            for r in rr:
                r["medium"] = "0" if r["medium"] == "3" else r["medium"]
                w.writerow(r)
        k2, _ = sweep.e075.read_run(f"merged {s}", merged)
        shutil.rmtree(tmp)
        c, _ = sweep.e075.read_run(f"control {s}", os.path.join(LADDER, f"c1225_life{s}_u0"))
        measure.append({"run": f"seed {s}", "kinds_control": c["kinds_at"], "kinds": k["kinds_at"], "kinds_merged": k2["kinds_at"],
                        "placed_control": c["placed_at"], "placed": k["placed_at"], "placed_merged": k2["placed_at"]})
        print(f"seed {s}: kinds {c['kinds_at']:.2f} -> {k['kinds_at']:.2f} (as land {k2['kinds_at']:.2f}), "
              f"kept to a place {c['placed_at']:.2f} -> {k['placed_at']:.2f} (as land {k2['placed_at']:.2f})")

    def write(name, data):
        with open(os.path.join(HERE, "results", name), "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(data[0].keys()))
            w.writeheader()
            for d in data:
                w.writerow({k: (f"{v:.5g}" if isinstance(v, float) else v) for k, v in d.items()})

    write("places.csv", places)
    write("forms.csv", forms)
    write("measure.csv", measure)


if __name__ == "__main__":
    main()
