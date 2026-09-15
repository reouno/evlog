#!/usr/bin/env python3
"""Read e072's search (#88): what each combination of the seven rates held.

Run from the repo root: `uv run python experiments/e072_balance/sweep.py [dir]` (a few minutes).
For every candidate of `results/search` it prints the rates, whether the world stood, the kinds by birth
form (e068's `kinds.py`), how many of them keep to a medium, what each set cost, and the land's and the
sea's matter; then the candidates ranked by the kinds held at every census. Writes `results/sweep.csv`.
"""
import csv
import os
import statistics as st
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "experiments", "e068_kinds"))
import kinds  # noqa: E402  (e068's census by birth form; it imports e060's census)

census = kinds.census
RATES = ("heat", "wood_food", "fat_weight", "fresh", "light", "climb", "carry")
CAUSES = ("hunger", "broken", "wear", "thirst", "suffocation", "cold")


def log_stats(pre):
    with open(pre + "_log.csv") as f:
        rows = list(csv.DictReader(f))
    half = [r for r in rows if int(r["step"]) >= int(rows[-1]["step"]) / 2]
    col = lambda k: [float(r[k]) for r in half]  # noqa: E731
    deaths = {c: sum(float(r[f"deaths_{c}"]) for r in half) for c in CAUSES}
    total = max(sum(deaths.values()), 1)
    out = {"pop": st.mean(col("pop")), "pop_min": min(float(r["pop"]) for r in rows), "pop_end": float(rows[-1]["pop"]),
           "ms_step": st.mean(col("ms_step")), "err": max(col("matter_err")),
           "blocked": st.mean(col("blocked")), "no_room": st.mean(col("no_room_land")),
           "kills": st.mean(col("kill_gain")), "wood": st.mean(col("wood_intake")) / max(st.mean(col("plant_intake")), 1e-9),
           "warm_land": st.mean(col("warm_land")), "cool_land": st.mean(col("cool_land")),
           "btemp_land": st.mean(col("btemp_land")), "open_land": st.mean(col("open_land")),
           "climbed": st.mean(col("climbed")), "carried": st.mean(col("carried")),
           "fat": st.mean(col("fat_mean")), "sighted": st.mean(col("sighted")),
           "land_drift": (float(half[-1]["matter_land"]) - float(rows[0]["matter_land"])) / float(rows[0]["matter_land"]),
           "sea_drift": (float(half[-1]["matter_sea"]) - float(rows[0]["matter_sea"])) / float(rows[0]["matter_sea"])}
    out.update({f"death_{c}": deaths[c] / total for c in CAUSES})
    for m in kinds.MEDIA:
        out[f"pop_{m}"] = st.mean(col(f"pop_{m}"))
    return out


def rates_of(pre):
    with open(pre + "_row.csv") as f:
        row = next(csv.DictReader(f))
    return {k: float(row[k]) for k in RATES}


def read_run(name, pre):
    run = kinds.Run(name, pre)
    per, held = kinds.form_census(run)
    unit = run.forms()
    ways = kinds.by_group(run, unit, run.does())
    # A kind held at every census that keeps its bodies to one medium is not a kind of the shore.
    placed = sum(w[3] != "shore" for w in held)
    out = {"name": name, "kinds_held": len(held), "kinds_at": kinds.mean_count(per), "placed": placed,
           "forms": len(set(unit)), "ways": ", ".join(sorted("/".join(w) for w in held))}
    out.update(log_stats(pre))
    out.update(rates_of(pre))
    return out


def main():
    d = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "results", "search")
    pres = sorted({os.path.join(d, f[: -len("_agents.csv")]) for f in os.listdir(d) if f.endswith("_agents.csv")})
    rows = []
    for pre in pres:
        name = os.path.basename(pre).split("_")[-1]
        try:
            rows.append(read_run(name, pre))
        except Exception as e:  # a run that died out has no grown bodies
            print(f"{name}: {type(e).__name__}: {e}")
    rows.sort(key=lambda r: (-r["kinds_held"], -r["placed"], -r["kinds_at"]))
    print(f"{'run':>5} {'held':>4} {'plcd':>4} {'at':>5} {'pop':>7} {'min':>7} {'heat':>7} {'wood':>7} {'fat_w':>7} {'fresh':>7} "
          f"{'light':>6} {'climb':>8} {'carry':>7} {'warm':>5} {'cool':>6} {'open':>5} {'wood%':>6} {'thirst':>6} {'cold':>5} {'land%':>6} {'ms':>5}")
    for r in rows:
        print(f"{r['name']:>5} {r['kinds_held']:>4} {r['placed']:>4} {r['kinds_at']:>5.1f} {r['pop']:>7.0f} {r['pop_min']:>7.0f} "
              f"{r['heat']:>7.3f} {r['wood_food']:>7.3f} {r['fat_weight']:>7.3f} {r['fresh']:>7.3f} {r['light']:>6.2f} "
              f"{r['climb']:>8.1e} {r['carry']:>7.3f} {r['warm_land']:>5.2f} {r['cool_land']:>6.4f} {r['open_land']:>5.2f} "
              f"{r['wood']:>6.1%} {r['death_thirst']:>6.1%} {r['death_cold']:>5.1%} {r['land_drift']:>6.1%} {r['ms_step']:>5.1f}")
    if rows:
        out = os.path.join(HERE, "results", "sweep.csv")
        with open(out, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0]))
            w.writeheader()
            w.writerows(rows)
        print(f"\n{len(rows)} candidates -> {out}")
        for r in rows[:5]:
            print(f"  {r['name']}: {r['ways']}")


if __name__ == "__main__":
    main()
