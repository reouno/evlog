#!/usr/bin/env python3
"""Senses from sensor blocks (#84): e070's runs (`senses = 1`) against the controls, whose senses are given.

Run from the repo root: `uv run python experiments/e070_senses/senses.py` (a few minutes on one core).
It reads the second half's censuses of every run, counts kinds by birth form with e068's `kinds.py`, reads
where each grown body's sensor blocks look out of it (from `cells`, as `sight_of` in body.rs does), prints
the numbers and writes `results/*.csv`.

The controls are e067's run for seed 9 and e069's constants runs for seeds 10 and 11 (both `senses = 0`).
"""
import csv
import os
import statistics as st
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "experiments", "e068_kinds"))
import kinds  # noqa: E402  (e068's census by birth form; it imports e060's census)

census = kinds.census
CONTROL = {9: os.path.join(ROOT, "experiments", "e067_breath", "results", "c1225_life9_breath0.01"),
           10: os.path.join(ROOT, "experiments", "e069_history", "results", "c1225_life10_constants"),
           11: os.path.join(ROOT, "experiments", "e069_history", "results", "c1225_life11_constants")}
RUNS = [(f"{arm}{s}", s, arm, CONTROL[s] if arm == "given" else os.path.join(HERE, "results", f"c1225_life{s}_senses"))
        for s in (9, 10, 11) for arm in ("given", "senses")]
SIDES = ("front", "back", "left", "right")
CAUSES = ("hunger", "broken", "wear", "thirst", "suffocation")
EYES = 8


# ---------------------------------------------------------------- the sensor blocks

def sight(cells, s):
    """Sensor blocks with nothing of the body beyond them to the front (the grid's first row), the back, the
    left (the first column) and the right."""
    n = [0, 0, 0, 0]
    for pos, c in enumerate(cells):
        if c != "3":
            continue
        r, k = divmod(pos, s)
        n[0] += all(cells[q * s + k] == "0" for q in range(r))
        n[1] += all(cells[q * s + k] == "0" for q in range(r + 1, s))
        n[2] += all(cells[r * s + q] == "0" for q in range(k))
        n[3] += all(cells[r * s + q] == "0" for q in range(k + 1, s))
    return n


def reach(n):
    return 0 if n == 0 else 1 + min(n, EYES)


def senses_of(rows):
    """Bodies with a sensor block, bodies with one looking out, and per side the blocks looking out, the reach
    they give (e070's rule) and the share of bodies dark that way."""
    n = max(len(rows), 1)
    sights = [sight(r["cells"], int(r["side"])) for r in rows]
    out = {"bodies": len(rows), "feeling": sum(int(r["sensor"]) > 0 for r in rows) / n,
           "sighted": sum(any(x) for x in sights) / n, "sensors": sum(int(r["sensor"]) for r in rows) / n,
           "born_sensors": sum(int(r["born_sensor"]) for r in rows) / n}
    for j, side in enumerate(SIDES):
        out[f"sight_{side}"] = sum(x[j] for x in sights) / n
        out[f"reach_{side}"] = sum(reach(x[j]) for x in sights) / n
    return out


# ---------------------------------------------------------------- the log

def log_half(pre):
    with open(pre + "_log.csv") as f:
        rows = list(csv.DictReader(f))
    last = int(rows[-1]["step"])
    late = [r for r in rows if 2 * int(r["step"]) > last]
    col = lambda k: [float(r[k]) for r in late]
    deaths = {c: sum(col(f"deaths_{c}")) for c in CAUSES}
    total = max(sum(deaths.values()), 1)
    out = {"steps": last, "pop": st.mean(col("pop")), "pop_min": min(col("pop")), "pop_max": max(col("pop")),
           "pop_end": float(rows[-1]["pop"]), "lineages": st.mean(col("lineages")), "top_lineage": st.mean(col("top_lineage")),
           "births_per_body": sum(col("births")) / sum(col("pop")),
           "blocked": st.mean(col("blocked")), "no_room": sum(col("no_room")) / max(sum(col("no_room")) + sum(col("births")), 1),
           "age_death_p50": st.mean(col("age_death_p50")), "size_mean": st.mean(col("size_mean")),
           "kills": (sum(col("meat_intake")) - sum(col("scavenged"))) / (sum(col("plant_intake")) + sum(col("meat_intake"))),
           "moved": st.mean(col("moved")), "sense_used": st.mean(col("sense_used")), "ms_step": st.mean(col("ms_step")),
           "pop_land": st.mean(col("pop_land")), "pop_surface": st.mean(col("pop_surface")), "pop_bottom": st.mean(col("pop_bottom"))}
    out |= {a: st.mean(col(a)) for a in ("stay", "forward", "left", "right")}
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
    for name, seed, arm, pre in RUNS:
        if not os.path.exists(pre + "_row.csv"):
            print(f"{name}: not run yet ({pre})")
            continue
        run = kinds.Run(name, pre)
        per, held = kinds.form_census(run)
        nm, nm_held, _ = kinds.null(run, ("medium",))
        row = {"run": name, "seed": seed, "arm": arm, "censuses": len(run.steps), "grown": len(run.grown) / len(run.steps),
               "lineage_e060": kinds.lineage_e060(run), "forms": len(set(run.forms())),
               "form": kinds.mean_count(per), "form_low": min(len(p) for p in per.values()), "form_high": max(len(p) for p in per.values()),
               "form_held": len(held), "null_medium": nm, "null_medium_held": nm_held}
        row |= senses_of(run.grown) | log_half(pre)
        out["runs"].append(row)
        for m, medium in enumerate(kinds.MEDIA):
            out["media"].append({"run": name, "medium": medium} | senses_of([r for r in run.grown if r["medium"] == str(m)]))
        for step, rs in census.read(pre + "_agents.csv").items():
            out["time"].append({"run": name, "step": step} | senses_of(census.grown(rs)))
        unit = run.forms()
        ways = kinds.by_group(run, unit, run.does())
        members = defaultdict(list)
        for i, u in enumerate(unit):
            members[" / ".join(ways[u])].append(run.grown[i])
        for k in kinds.describe(run, per, held):
            eye = senses_of(members[k["kind"]])
            out["kinds"].append(k | {"run": name} | {f"eye_{x}": eye[x] for x in ("feeling", "sighted", "sensors", "sight_front", "sight_back", "sight_left", "sight_right")})
        print(f"{name}: grown {row['grown']:.0f}, kinds by form {row['form']:.1f} [{row['form_low']}-{row['form_high']}] held {row['form_held']} "
              f"(medium shuffled {nm:.1f}/{nm_held:.1f}), lineage {row['lineage_e060']:.1f}, forms {row['forms']}; stood {row['steps']} steps, low {row['pop_min']:.0f}")
        print(f"  sensor block {row['feeling']:.1%}, looking out {row['sighted']:.1%}, sensors {row['sensors']:.2f} (born {row['born_sensors']:.2f}); "
              + ", ".join(f"{s} {row[f'sight_{s}']:.2f}" for s in SIDES))
        print("  " + ", ".join(f"{k} {row[k]:.3g}" for k in ("pop", "lineages", "top_lineage", "blocked", "no_room", "kills", "stay", "forward", "sense_used", "size_mean", "ms_step")
                                + tuple(f"deaths_{c}" for c in CAUSES)))
    for arm in ("given", "senses"):
        rs = [r for r in out["runs"] if r["arm"] == arm]
        if not rs:
            continue
        mean = lambda k: st.mean(r[k] for r in rs)
        a = {"arm": arm, "seeds": " ".join(str(r["seed"]) for r in rs)}
        a |= {k: mean(k) for k in ("form_held", "form", "null_medium", "lineage_e060", "top_lineage", "pop", "feeling", "sighted", "sight_front", "sight_back")}
        out["arms"].append(a)
        print(f"{arm:6s} seeds {a['seeds']}: kinds held {a['form_held']:.2f} ({', '.join(str(r['form_held']) for r in rs)}), at a census {a['form']:.2f}, "
              f"medium shuffled {a['null_medium']:.2f}, per lineage {a['lineage_e060']:.2f}; looking out {a['sighted']:.1%}, front {a['sight_front']:.2f} back {a['sight_back']:.2f}")
    s = [r for r in out["runs"] if r["arm"] == "senses"]
    if s:
        print("verdicts: stands " + ", ".join(f"{r['seed']}:{r['steps'] == 100000 and r['pop_min'] > 0}" for r in s)
              + "; 1 looking out >= 50%: " + ", ".join(f"{r['sighted']:.0%}" for r in s)
              + "; 2 front >= 1.5 back: " + ", ".join(f"{r['sight_front']:.2f}/{r['sight_back']:.2f}" for r in s)
              + f"; 3 mean held {st.mean(r['form_held'] for r in s):.2f} (>= 3.0)")
    for name, rows in out.items():
        write(name, rows)
    print("wrote " + ", ".join(f"results/{n}.csv" for n in out))


if __name__ == "__main__":
    main()
