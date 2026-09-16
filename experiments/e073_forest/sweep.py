#!/usr/bin/env python3
"""Read e073's runs (#89): what the crown's yield and the cold by place held.

Run from the repo root: `uv run python experiments/e073_forest/sweep.py [dir ...]` (a few minutes).
For every run in the directories given (the search by default) it prints the two rates, the kinds by
birth form (e068's `kinds.py`), how many keep to a medium and how many to a temperature band, what
the browse fed, the forest left standing and the deaths by cause. Writes `results/sweep.csv`.
"""
import csv
import os
import statistics as st
import sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "experiments", "e068_kinds"))
import kinds  # noqa: E402  (e068's census by birth form; it imports e060's census)

RATES = ("day_temp", "wood_yield", "wood_food", "wood_hard")
CAUSES = ("hunger", "broken", "wear", "thirst", "suffocation", "cold")
BANDS = ("cold", "mild", "hot")
LAND = 110625


def band_of(place):
    """The temperature band of e061's 15 habitats: land 0-8 by threes, water 9-11 and 12-14."""
    h = int(place)
    return BANDS[h // 3 if h < 9 else (h - 9) % 3]


def log_stats(pre):
    with open(pre + "_log.csv") as f:
        rows = list(csv.DictReader(f))
    half = [r for r in rows if int(r["step"]) >= int(rows[-1]["step"]) / 2]
    col = lambda k: [float(r[k]) for r in half]  # noqa: E731
    deaths = {c: sum(float(r[f"deaths_{c}"]) for r in half) for c in CAUSES}
    total = max(sum(deaths.values()), 1)
    intake = max(st.mean(col("plant_intake")) + st.mean(col("meat_intake")), 1e-9)
    out = {"pop": st.mean(col("pop")), "pop_min": min(float(r["pop"]) for r in rows), "ms_step": st.mean(col("ms_step")),
           "err": max(col("matter_err")), "blocked": st.mean(col("blocked")), "tooth": st.mean(col("tooth")),
           "wood_stand": st.mean(col("wood")) / LAND, "browse_stand": st.mean(col("browse")) / LAND,
           "grass_stand": st.mean(col("grass")) / LAND,
           "wood_share": st.mean(col("wood_intake")) / intake, "browse_share": st.mean(col("browse_intake")) / intake,
           "kills": st.mean(col("kill_gain")) / intake, "warm_land": st.mean(col("warm_land")),
           "btemp_land": st.mean(col("btemp_land")), "open_land": st.mean(col("open_land")),
           "land_temp": st.mean(col("land_temp")), "temp_day_land": st.mean(col("temp_day_land")),
           "land_drift": (float(half[-1]["matter_land"]) - float(rows[0]["matter_land"])) / float(rows[0]["matter_land"])}
    out.update({f"death_{c}": deaths[c] / total for c in CAUSES})
    for m in kinds.MEDIA:
        out[f"pop_{m}"] = st.mean(col(f"pop_{m}"))
    for b in BANDS:
        out[f"pop_{b}"] = st.mean(col(f"pop_{b}"))
    return out


def rates_of(pre):
    with open(pre + "_row.csv") as f:
        row = next(csv.DictReader(f))
    return {k: float(row[k]) for k in RATES}


def read_run(name, pre):
    run = kinds.Run(name, pre)
    unit = run.forms()
    ways = kinds.by_group(run, unit, run.does())
    per, held = kinds.kinds(run.tally(unit, ways))
    # What each kind is besides its way: where it stands by band, and what browse fed it.
    rows = defaultdict(list)
    for i, r in enumerate(run.grown):
        rows[ways[unit[i]]].append(r)
    placed, banded, by_wood, lines = 0, 0, 0, []
    for w in sorted(held):
        rs = rows[w]
        bands = Counter(band_of(r["place"]) for r in rs)
        band, n = bands.most_common(1)[0]
        food = sum(float(r["plant"]) + float(r["meat"]) for r in rs)
        woody = sum(float(r["wood"]) for r in rs) / max(food, 1e-9)
        placed += w[3] != "shore"
        banded += n >= kinds.KEEP * len(rs)
        by_wood += woody >= 0.2
        lines.append(f"{'/'.join(w)} [{band} {n / len(rs):.0%}, wood {woody:.0%}, {len(rs)} bodies]")
    out = {"name": name, "kinds_held": len(held), "kinds_at": kinds.mean_count(per),
           "lean": min(len(k) for k in per.values()), "placed": placed, "banded": banded, "by_wood": by_wood,
           "forms": len(set(unit)), "ways": "; ".join(lines)}
    out.update(log_stats(pre))
    out.update(rates_of(pre))
    return out


def main():
    dirs = sys.argv[1:] or [os.path.join(HERE, "results", "search")]
    pres = sorted({os.path.join(d, f[: -len("_agents.csv")]) for d in dirs for f in os.listdir(d) if f.endswith("_agents.csv")})
    rows = []
    for pre in pres:
        name = os.path.basename(pre).split("_")[-1]
        try:
            rows.append(read_run(name, pre))
        except Exception as e:  # a run that died out has no grown bodies
            print(f"{name}: {type(e).__name__}: {e}")
    print(f"{'run':>7} {'day':>4} {'yield':>7} {'food':>5} {'hd':>3} {'held':>4} {'at':>5} {'lean':>4} {'plcd':>4} {'band':>4} {'wood':>4} "
          f"{'pop':>7} {'min':>7} {'browse%':>7} {'wood%':>6} {'stand':>6} {'brwse':>6} {'grass':>6} {'tooth':>6} {'warm':>5} {'cold':>5} {'ms':>5}")
    for r in sorted(rows, key=lambda r: r["name"]):
        print(f"{r['name']:>7} {r['day_temp']:>4.1f} {r['wood_yield']:>7.0e} {r['wood_food']:>5.2f} {r['wood_hard']:>3.0f} "
              f"{r['kinds_held']:>4} {r['kinds_at']:>5.1f} {r['lean']:>4} {r['placed']:>4} {r['banded']:>4} {r['by_wood']:>4} "
              f"{r['pop']:>7.0f} {r['pop_min']:>7.0f} {r['browse_share']:>7.1%} {r['wood_share']:>6.1%} {r['wood_stand']:>6.3f} "
              f"{r['browse_stand']:>6.3f} {r['grass_stand']:>6.3f} {r['tooth']:>6.1%} {r['warm_land']:>5.2f} {r['death_cold']:>5.1%} {r['ms_step']:>5.1f}")
    if rows:
        out = os.path.join(HERE, "results", "sweep.csv")
        with open(out, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0]))
            w.writeheader()
            w.writerows(rows)
        print(f"\n{len(rows)} runs -> {out}")
        for r in sorted(rows, key=lambda r: r["name"]):
            print(f"  {r['name']}: {r['ways']}")


if __name__ == "__main__":
    main()
