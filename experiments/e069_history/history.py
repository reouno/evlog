#!/usr/bin/env python3
"""Life history from the genome (#83): e069's pilot against e067's run at breath 0.01.

Run from the repo root: `uv run python experiments/e069_history/history.py` (under a minute on one core).
It reads the second half's censuses of both runs, counts kinds by birth form with e068's `kinds.py`, reads
the three values of a life by medium and inside lineage groups (the water's median over the land's, against
the same with the medium shuffled inside each group), prints the numbers and writes `results/*.csv`.

e067 has no columns for the values: its bodies hold today's constants.
"""
import csv
import math
import os
import statistics as st
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "experiments", "e068_kinds"))
import kinds  # noqa: E402  (e068's census by birth form; it imports e060's census)

RUNS = [
    ("e067", os.path.join(ROOT, "experiments", "e067_breath", "results", "c1225_life9_breath0.01")),
    ("e069", os.path.join(HERE, "results", "c1225_life9_history")),
]
VALUES = ("breed", "share", "store")
CENTRE = {"breed": 0.1, "share": 0.5, "store": 5.0}
GROUP = 20  # grown bodies on land and in the water for a lineage group to be compared
CAUSES = ("hunger", "broken", "wear", "thirst", "suffocation")


def value(r, v):
    return float(r[v]) if v in r else CENTRE[v]


def quantile(x, q):
    x = sorted(x)
    return x[int((len(x) - 1) * q)] if x else float("nan")


# ---------------------------------------------------------------- the values

def by_medium(run):
    """The grown bodies' values by the medium they stand in."""
    out = []
    for m, name in enumerate(kinds.MEDIA):
        rs = [r for r in run.grown if r["medium"] == str(m)]
        row = {"run": run.name, "medium": name, "grown": len(rs) / len(run.steps)}
        for v in VALUES:
            x = [value(r, v) for r in rs]
            row |= {v: st.median(x), f"{v}_p10": quantile(x, 0.1), f"{v}_p90": quantile(x, 0.9)}
        row["fat_fill"] = st.median(float(r["fat"]) / (value(r, "store") * float(r["mass"])) for r in rs)
        row["kids"] = st.mean(int(r["kids"]) for r in rs) if rs and "kids" in rs[0] else ""
        out.append(row)
    return out


def parting(run, does):
    """Each lineage group with GROUP grown bodies on land and in the water: log of the water's median of each
    value over the land's."""
    rows = []
    for (lineage, light), idx in run.groups.items():
        land = [i for i in idx if does[i]["medium"] == "0"]
        water = [i for i in idx if does[i]["medium"] != "0"]
        if len(land) < GROUP or len(water) < GROUP:
            continue
        row = {"run": run.name, "lineage": lineage, "light": int(light), "land": len(land), "water": len(water)}
        for v in VALUES:
            row[v] = math.log(st.median(value(run.grown[i], v) for i in water) / st.median(value(run.grown[i], v) for i in land))
        rows.append(row)
    return rows


def gap(rows):
    """The groups' mean of |log ratio|, weighted by their grown bodies, as a percentage."""
    n = sum(r["land"] + r["water"] for r in rows)
    return {v: math.expm1(sum(abs(r[v]) * (r["land"] + r["water"]) for r in rows) / n) if n else float("nan") for v in VALUES}


def kind_values(run):
    """The median values of each kind of the form census."""
    unit = run.forms()
    ways = kinds.by_group(run, unit, run.does())
    members = defaultdict(list)
    for i, u in enumerate(unit):
        members[" / ".join(ways[u])].append(run.grown[i])
    return {k: {v: st.median(value(r, v) for r in rs) for v in VALUES} for k, rs in members.items()}


def lineage_values(run, n=8):
    """The largest lineages over the second half: their share of the grown bodies, where they stand, their values."""
    by = defaultdict(list)
    for r in run.grown:
        by[r["lineage"]].append(r)
    out = []
    for lineage, rs in sorted(by.items(), key=lambda x: -len(x[1]))[:n]:
        row = {"run": run.name, "lineage": lineage, "grown": len(rs) / len(run.grown)}
        row |= {m: sum(r["medium"] == str(i) for r in rs) / len(rs) for i, m in enumerate(kinds.MEDIA)}
        row |= {v: st.median(value(r, v) for r in rs) for v in VALUES}
        row |= {"born_size": st.median(int(r["born_size"]) for r in rs), "density": st.median(float(r["density"]) for r in rs)}
        out.append(row)
    return out


# ---------------------------------------------------------------- the log

def log_half(pre):
    with open(pre + "_log.csv") as f:
        rows = list(csv.DictReader(f))
    last = int(rows[-1]["step"])
    late = [r for r in rows if 2 * int(r["step"]) > last]
    col = lambda k: [float(r[k]) for r in late]
    deaths = {c: sum(col(f"deaths_{c}")) for c in CAUSES}
    total = sum(deaths.values())
    out = {"steps": last, "pop": st.mean(col("pop")), "pop_min": min(col("pop")), "pop_max": max(col("pop")),
           "lineages": st.mean(col("lineages")), "top_lineage": st.mean(col("top_lineage")),
           "births_per_body": sum(col("births")) / sum(col("pop")),  # a row's births are its 1,000 steps'
           "blocked": st.mean(col("blocked")), "no_room": sum(col("no_room")) / max(sum(col("no_room")) + sum(col("births")), 1),
           "age_death_p50": st.mean(col("age_death_p50")), "fat_mean": st.mean(col("fat_mean")),
           "kills": (sum(col("meat_intake")) - sum(col("scavenged"))) / (sum(col("plant_intake")) + sum(col("meat_intake")))}
    out |= {f"deaths_{c}": deaths[c] / total for c in CAUSES}
    return out


# ---------------------------------------------------------------- main

def write(name, rows):
    keys = list(dict.fromkeys(k for r in rows for k in r))
    with open(os.path.join(HERE, "results", f"{name}.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        w.writerows(rows)


def main():
    out = defaultdict(list)
    for name, pre in RUNS:
        run = kinds.Run(name, pre)
        per, held = kinds.form_census(run)
        nm, nm_held, _ = kinds.null(run, ("medium",))
        nw, nw_held, _ = kinds.null(run, kinds.DOES)
        groups = parting(run, run.does())
        seen = gap(groups)
        shuffled = [gap(parting(run, run.does(("medium",), s))) for s in range(1, kinds.NULLS + 1)]
        row = {"run": name, "censuses": len(run.steps), "grown": len(run.grown) / len(run.steps),
               "lineage_e060": kinds.lineage_e060(run), "forms": len(set(run.forms())),
               "form": kinds.mean_count(per), "form_low": min(len(p) for p in per.values()), "form_high": max(len(p) for p in per.values()),
               "form_held": len(held), "null_medium": nm, "null_medium_held": nm_held, "null_whole": nw, "null_whole_held": nw_held,
               "groups": len(groups), "grouped": sum(g["land"] + g["water"] for g in groups) / len(run.grown)}
        for v in VALUES:
            x = [value(r, v) for r in run.grown]
            row |= {v: st.median(x), f"{v}_p10": quantile(x, 0.1), f"{v}_p90": quantile(x, 0.9),
                    f"gap_{v}": seen[v], f"gap_{v}_null_max": max(s[v] for s in shuffled)}
        row |= log_half(pre)
        out["runs"].append(row)
        out["media"] += by_medium(run)
        out["groups"] += groups
        values = kind_values(run)
        for k in kinds.describe(run, per, held):
            out["kinds"].append(k | {f"median_{v}": x for v, x in values[k["kind"]].items()})  # `share` is the kind's share
        out["lineages"] += lineage_values(run)
        print(f"{name}: grown {row['grown']:.0f}, kinds by form {row['form']:.1f} [{row['form_low']}-{row['form_high']}] held {row['form_held']} "
              f"(null medium {nm:.1f}/{nm_held:.1f}, whole {nw:.1f}/{nw_held:.1f}), lineage {row['lineage_e060']:.1f}, forms {row['forms']}")
        print("  values " + ", ".join(f"{v} {row[v]:.3g} [{row[f'{v}_p10']:.3g}-{row[f'{v}_p90']:.3g}]" for v in VALUES))
        print(f"  water/land inside {len(groups)} lineage groups ({row['grouped']:.0%} of grown): "
              + ", ".join(f"{v} {seen[v]:+.1%} (shuffled max {row[f'gap_{v}_null_max']:.1%})" for v in VALUES))
        for m in by_medium(run):
            print(f"  {m['medium']:7s} grown {m['grown']:.0f}: " + ", ".join(f"{v} {m[v]:.3g}" for v in VALUES) + f", fat fill {m['fat_fill']:.2f}, kids {m['kids']}")
        print("  " + ", ".join(f"{k} {row[k]:.3g}" for k in ("pop", "lineages", "top_lineage", "blocked", "no_room", "births_per_body", "age_death_p50", "kills") + tuple(f"deaths_{c}" for c in CAUSES)))
    for name, rows in out.items():
        write(name, rows)
    print("wrote " + ", ".join(f"results/{n}.csv" for n in out))


if __name__ == "__main__":
    main()
