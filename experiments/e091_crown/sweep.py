#!/usr/bin/env python3
"""Read e091's runs (#101, the crown as a place) against e081's control ladder: kinds, the foods that part
them, size by food.

Run from the repo root: `uv run python experiments/e091_crown/sweep.py` (a few minutes).
For every run (e091's three and the three controls) it prints:

- **kinds** (done-when 1): kinds at a census and kinds kept to a place (e075's `read_run`, e068's census by
  birth form, with the crown as a fourth medium), and the largest line's share of the bodies that stand on
  land, the crowns' among them;
- **the foods** (2): each kind held at a census is led by the plant food that gives its grown bodies the most
  matter (there is no fiber law here, so matter is energy). The foods are grass, the crowns' fruit, browse,
  algae and the bottom's litter; grass is a land body's plant intake less its fruit, its browse and the water's
  foods. Then the mean share of the grown bodies a census in fruit-led and in grass-led kinds, and the censuses
  where both hold 5% or more;
- **size** (3): the median mass and pace of the grown bodies of grass-led and of fruit-led kinds;
- **the world** (4): the bodies by medium, the world's intake by food (second half), the fruit standing in the
  crowns, the times a body changed layer, and the ledger's worst drift.

Writes `results/sweep.csv` (one row a run), `results/kinds.csv` (one row a kind of a run) and `results/bodies.csv`
(e075's rows: each kind's commonest birth body, with its foods).
"""
import csv
import importlib.util
import os
import statistics as st
import sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# e075's sweep (its read_run: kinds at a census and kept to a place), which imports e068's kinds; every one of
# them is named sweep.py, so each is loaded by its path.
sys.path.insert(0, os.path.join(ROOT, "experiments", "e068_kinds"))
e075 = load("e075_sweep", os.path.join(ROOT, "experiments", "e075_hunt", "sweep.py"))
kinds = e075.kinds
census = kinds.census
kinds.MEDIA = ["land", "surface", "bottom", "crown"]  # e091 (C1): the crown is a fourth medium
SCALE = 0.0625
LOG = 1000  # steps a log row
LADDER = os.path.join(ROOT, "experiments", "e081_drink", "results", "ladder")
RUNS = [
    ("control 9", os.path.join(LADDER, "c1225_life9_u0")),
    ("control 10", os.path.join(LADDER, "c1225_life10_u0")),
    ("control 11", os.path.join(LADDER, "c1225_life11_u0")),
    ("crown 9", os.path.join(HERE, "results", "c1225_life9_crown")),
    ("crown 10", os.path.join(HERE, "results", "c1225_life10_crown")),
    ("crown 11", os.path.join(HERE, "results", "c1225_life11_crown")),
]
FOODS = ("grass", "fruit", "browse", "algae", "litter")


def foods(r):
    """A grown body's lifetime plant intake by food. With no fiber law, matter is energy."""
    plant, algae, litter = float(r["plant"]), float(r["algae"]), float(r["detritus"])
    fruit, wood = float(r.get("fruit", 0.0)), float(r["wood"])
    return {"grass": max(plant - algae - litter - fruit - wood, 0.0), "fruit": fruit, "browse": wood,
            "algae": algae, "litter": litter}


def top_share(pre):
    """The largest line's share of the bodies standing on land (e081's census, with the crowns' counted)."""
    per = defaultdict(Counter)
    with open(pre + "_agents.csv") as f:
        for r in csv.DictReader(f):
            if r["medium"] in ("0", "3"):
                per[int(r["step"])][r["lineage"]] += 1
    return st.mean(max(c.values()) / sum(c.values()) for c in per.values() if c)


def by_food(name, pre):
    """Kinds by the food that leads them."""
    run = kinds.Run(name, pre)
    unit = run.forms()
    ways = kinds.by_group(run, unit, run.does())
    per, _ = kinds.kinds(run.tally(unit, ways))
    members = defaultdict(list)
    for i, r in enumerate(run.grown):
        members[ways[unit[i]]].append(r)
    lead = {}
    rows = []
    for w, rs in members.items():
        tot = Counter()
        for r in rs:
            tot.update(foods(r))
        plant = sum(tot.values())
        lead[w] = max(FOODS, key=lambda f: tot[f]) if plant > 0 else "none"
        rows.append({"run": name, "kind": " / ".join(w), "lead": lead[w], "bodies": len(rs), "share": len(rs) / len(run.grown),
                     "mass": st.median(float(r["mass"]) for r in rs), "pace": st.median(float(r["pace"]) for r in rs),
                     "crown": sum(r["medium"] == "3" for r in rs) / len(rs),
                     **{f: tot[f] / plant if plant else 0.0 for f in FOODS},
                     "kills": sum(float(r["killed"]) for r in rs) / max(plant + sum(float(r["meat"]) for r in rs), 1e-9)})
    shares = {"fruit": [], "grass": []}
    both = 0
    for s, ws in per.items():
        at = run.at[s]
        n = len(at)
        c = Counter(ways[unit[i]] for i in at)
        for f in shares:
            shares[f].append(sum(v for w, v in c.items() if w in ws and lead[w] == f) / n)
        both += any(lead[w] == "fruit" for w in ws) and any(lead[w] == "grass" for w in ws)
    mass = {f: [float(r["mass"]) for w, rs in members.items() if lead[w] == f and any(w in ws for ws in per.values()) for r in rs] for f in shares}
    pace = {f: [float(r["pace"]) for w, rs in members.items() if lead[w] == f and any(w in ws for ws in per.values()) for r in rs] for f in shares}
    # The grown bodies in a crown, and those with a tooth that opens what falls to the floor (wood_hard 3).
    up = sum(r["medium"] == "3" for r in run.grown) / max(len(run.grown), 1)
    toothed = sum(float(r["bite_any"]) >= 3 for r in run.grown) / max(len(run.grown), 1)
    out = {"fruit_led": st.mean(shares["fruit"]), "grass_led": st.mean(shares["grass"]), "both_at": both / len(per),
           "in_crowns": up, "toothed": toothed}
    for f in shares:
        out[f"mass_{f}"] = st.median(mass[f]) if mass[f] else float("nan")
        out[f"pace_{f}"] = st.median(pace[f]) if pace[f] else float("nan")
    return out, sorted(rows, key=lambda r: -r["share"])


def world(pre):
    with open(pre + "_log.csv") as f:
        rows = list(csv.DictReader(f))
    half = [r for r in rows if int(r["step"]) > int(rows[-1]["step"]) / 2]
    m = lambda k: st.mean(float(r[k]) for r in half) if k in half[0] else 0.0  # noqa: E731
    fruit = m("fruit_intake") * LOG * SCALE  # a step in a body's units, as e089's columns
    wood, algae, litter = m("wood_intake"), m("algae_intake"), m("detritus_intake")
    plant = m("plant_intake")
    eat = {"grass": plant - fruit - wood - algae - litter, "fruit": fruit, "browse": wood, "algae": algae,
           "litter": litter, "kills": m("kill_intake"), "carrion": m("scavenged")}
    tot = sum(eat.values())
    out = {f"eat_{k}": v / tot for k, v in eat.items()}
    out.update({"steps": int(rows[-1]["step"]), "pop": m("pop"), "pop_land": m("pop_land"), "pop_surface": m("pop_surface"),
                "pop_bottom": m("pop_bottom"), "pop_crown": m("pop_crown"), "fruit_bank": m("fruit"),
                "browse_bank": m("browse"), "climbs": m("climbs") / LOG,
                "err": max(abs(float(r["matter_err"])) for r in rows)})
    return out


def main():
    out, kind_rows, bodies = [], [], []
    for name, pre in RUNS:
        if not os.path.exists(pre + "_agents.csv"):
            print(f"{name}: no run")
            continue
        row = {"run": name}
        k, kr = e075.read_run(name, pre)
        row.update({x: k[x] for x in ("kinds_at", "placed_at", "travel", "kills")})
        row["top_share"] = top_share(pre)
        f, ks = by_food(name, pre)
        row.update(f)
        row.update(world(pre))
        out.append(row)
        kind_rows += ks
        # e075's rows (each kind's commonest birth body) with the foods of this sweep, for the report's gallery
        of = {r["kind"]: r for r in ks}
        for r in kr:
            f = of.get(r["kind"], {})
            bodies.append({**r, **{x: f.get(x, 0.0) for x in ("lead", "mass", "pace", "grass", "fruit", "crown")}})
        print(f"{name:10} kinds {row['kinds_at']:.2f} placed {row['placed_at']:.2f} top {row['top_share']:.0%} "
              f"| fruit-led {row['fruit_led']:.0%} grass-led {row['grass_led']:.0%} both {row['both_at']:.0%} "
              f"| mass grass {row['mass_grass']:.0f} fruit {row['mass_fruit']:.0f} pace {row['pace_grass']:.2f}/{row['pace_fruit']:.2f} "
              f"| in crowns {row['in_crowns']:.0%} tooth {row['toothed']:.0%} "
              f"| pop {row['pop']:.0f} (land {row['pop_land']:.0f}, crown {row['pop_crown']:.0f}) "
              f"fruit {row['fruit_bank']:.0f} browse {row['browse_bank']:.0f} climbs/step {row['climbs']:.1f} err {row['err']:.0e}")
        print("           eats " + " ".join(f"{x} {row['eat_' + x]:.0%}" for x in ("grass", "fruit", "browse", "algae", "litter", "kills", "carrion")))
        for r in ks:
            if r["share"] >= 0.03:
                print(f"             {r['share']:4.0%} {r['kind']:38} led by {r['lead']:6} mass {r['mass']:3.0f} pace {r['pace']:.2f} "
                      f"fruit {r['fruit']:.0%} grass {r['grass']:.0%} browse {r['browse']:.0%} kills {r['kills']:.0%}")

    def write(name, data):
        with open(os.path.join(HERE, "results", name), "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(data[0].keys()))
            w.writeheader()
            for d in data:
                w.writerow({k: (f"{v:.5g}" if isinstance(v, float) else v) for k, v in d.items()})

    write("sweep.csv", out)
    write("kinds.csv", kind_rows)
    write("bodies.csv", bodies)


if __name__ == "__main__":
    main()
