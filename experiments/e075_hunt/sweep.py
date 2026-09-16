#!/usr/bin/env python3
"""Read e075's runs (#90): what the tear and the frail line held.

Run from the repo root: `uv run python experiments/e075_hunt/sweep.py [dir ...]` (a few minutes).
For every run in the directories given (the search by default) it prints the two rates, the kinds by
birth form (e068's `kinds.py`), how many keep to a medium, what the flesh of the living fed and what
the tear gave of it, the deaths by cause, and **the hunter kinds**: the kinds holding e060's 5% of a
census that take more than half their food from kills. Writes `results/sweep.csv` and `kinds.csv`.

e073's `sweep.py` read the log's `kill_gain` column as a total; it is the gain per cell broken. This
one reads `kill_intake` (e075's column) where the run has it, and the log's `meat_intake` less the
dead where it does not.
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

RATES = ("flesh_bite", "frail", "wood_yield", "day_temp")
CAUSES = ("hunger", "broken", "wear", "thirst", "suffocation", "cold", "wound")
HUNTER = 0.5  # a kind's share of its food from kills for it to live by killing
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
    col = lambda k: [float(r[k]) for r in half] if k in half[0] else [0.0]  # noqa: E731  (e072's runs have no browse)
    deaths = {c: sum(float(r.get(f"deaths_{c}", 0.0)) for r in half) for c in CAUSES}
    total = max(sum(deaths.values()), 1)
    intake = max(st.mean(col("plant_intake")) + st.mean(col("meat_intake")), 1e-9)
    out = {"pop": st.mean(col("pop")), "pop_min": min(float(r["pop"]) for r in rows), "ms_step": st.mean(col("ms_step")),
           "err": max(col("matter_err")), "blocked": st.mean(col("blocked")), "tooth": st.mean(col("tooth")),
           "wood_stand": st.mean(col("wood")) / LAND, "browse_stand": st.mean(col("browse")) / LAND,
           "grass_stand": st.mean(col("grass")) / LAND,
           "wood_share": st.mean(col("wood_intake")) / intake, "browse_share": st.mean(col("browse_intake")) / intake,
           # e075: the flesh of the living as a total (`kill_intake`), the tear's share of it, and
           # the gain per cell broken, which is what the `kill_gain` column has always been.
           "kills": (st.mean(col("kill_intake")) if "kill_intake" in half[0] else
                     st.mean(col("meat_intake")) - st.mean(col("scavenged"))) / intake,
           "tear": st.mean(col("flesh_intake")) / max(st.mean(col("kill_intake")), 1e-12) if "flesh_intake" in half[0] else 0.0,
           "blocks_kept": st.mean(col("blocks_kept")), "gain_per_break": st.mean(col("kill_gain")),
           "warm_land": st.mean(col("warm_land")),
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
    return {k: float(row.get(k, 0.0)) for k in RATES}  # e072's runs have neither of e073's rates


def kind_rows(name, run, ways, unit, held):
    """One row per kind of a run, for the report's gallery: its commonest birth body and what it does."""
    members = defaultdict(list)
    for i, r in enumerate(run.grown):
        members[ways[unit[i]]].append(r)
    out = []
    for w, rs in members.items():
        body = Counter((r["side"], r["cells"]) for r in rs).most_common(1)[0][0]
        food = sum(float(r["plant"]) + float(r["meat"]) for r in rs)
        by_m = Counter(r["medium"] for r in rs)
        out.append({"run": name, "kind": " / ".join(w), "share": len(rs) / len(run.grown), "held": w in held,
                    "side": body[0], "cells": body[1], "bodies": len(rs),
                    "born_size": st.median(int(r["born_size"]) for r in rs),
                    "hard": st.mean(int(r["born_hard"]) for r in rs) / max(st.mean(int(r["born_size"]) for r in rs), 1),
                    "open_born": st.median(int(r["open_soft"]) for r in rs) / max(st.median(int(r["size"]) for r in rs), 1),
                    "travel": st.median(float(r["travel"]) for r in rs),
                    "wood": sum(float(r["wood"]) for r in rs) / max(food, 1e-9),
                    "kills": sum(float(r["killed"]) for r in rs) / max(food, 1e-9),
                    "land": by_m["0"] / len(rs), "surface": by_m["1"] / len(rs), "bottom": by_m["2"] / len(rs),
                    "cold": sum(band_of(r["place"]) == "cold" for r in rs) / len(rs)})
    return sorted(out, key=lambda r: -r["share"])


def read_run(name, pre):
    run = kinds.Run(name, pre)
    unit = run.forms()
    ways = kinds.by_group(run, unit, run.does())
    per, held = kinds.kinds(run.tally(unit, ways))
    # What each kind is besides its way: where it stands by band, and what browse fed it.
    rows = defaultdict(list)
    for i, r in enumerate(run.grown):
        rows[ways[unit[i]]].append(r)
    # The world's own band, so that keeping to it counts for nothing: in e072's runs 82% of the
    # bodies stand in the hot band, and a kind 96% hot is the world, not a place.
    world = Counter(band_of(r["place"]) for r in run.grown).most_common(1)[0][0]
    placed, banded, off_band, by_wood, lines = 0, 0, 0, 0, []
    for w in sorted(held):
        rs = rows[w]
        bands = Counter(band_of(r["place"]) for r in rs)
        band, n = bands.most_common(1)[0]
        keeps = n >= kinds.KEEP * len(rs)
        food = sum(float(r["plant"]) + float(r["meat"]) for r in rs)
        woody = sum(float(r["wood"]) for r in rs) / max(food, 1e-9)
        placed += w[3] != "shore"
        banded += keeps
        off_band += keeps and band != world
        by_wood += woody >= 0.2
        killed = sum(float(r["killed"]) for r in rs) / max(food, 1e-9)
        lines.append(f"{'/'.join(w)} [{band} {n / len(rs):.0%}, wood {woody:.0%}, kills {killed:.0%}, {len(rs)} bodies]")
    # e075 (#90): a kind that lives by killing, over the kinds holding 5% at any census. `killed` is
    # the flesh of the living alone (the tear with it); the dead lie in `scavenged`.
    at_a_census = sorted(set().union(*per.values())) if per else []
    shares = {}
    for w in at_a_census:
        rs = rows[w]
        shares[w] = sum(float(r["killed"]) for r in rs) / max(sum(float(r["plant"]) + float(r["meat"]) for r in rs), 1e-9)
    by_kills = sum(v >= HUNTER for v in shares.values())
    top_kills = max(shares.values(), default=0.0)
    # `placed` counts only kinds held at every census, so an even world loses it for being even
    # (#88). `placed_at` is the like-for-like: of the kinds at a census, how many keep to a medium.
    placed_at = st.mean(sum(w[3] != "shore" for w in ws) for ws in per.values())
    top = Counter(ways[unit[i]] for i in range(len(run.grown))).most_common(1)[0][1] / len(run.grown)
    out = {"name": name, "kinds_held": len(held), "kinds_at": kinds.mean_count(per),
           "lean": min(len(k) for k in per.values()), "placed": placed, "placed_at": placed_at, "top_kind": top,
           "travel": st.median(float(r["travel"]) for r in run.grown), "banded": banded, "off_band": off_band,
           "by_wood": by_wood, "by_kills": by_kills, "top_kills": top_kills, "world_band": world,
           "forms": len(set(unit)), "ways": "; ".join(lines)}
    out.update(log_stats(pre))
    out.update(rates_of(pre))
    return out, kind_rows(name, run, ways, unit, held)


def main():
    args = sys.argv[1:] or [os.path.join(HERE, "results", "search")]
    pres = sorted({a[: -len("_agents.csv")] if a.endswith("_agents.csv") else os.path.join(a, f[: -len("_agents.csv")])
                   for a in args for f in ([""] if a.endswith("_agents.csv") else os.listdir(a)) if a.endswith("_agents.csv") or f.endswith("_agents.csv")})
    rows, per_kind = [], []
    for pre in pres:
        name = "_".join(os.path.basename(pre).split("_")[1:])
        try:
            row, ks = read_run(name, pre)
            rows.append(row)
            per_kind += ks
        except Exception as e:  # a run that died out has no grown bodies
            print(f"{name}: {type(e).__name__}: {e}")
    print(f"{'run':>7} {'tear':>5} {'frail':>5} {'yield':>7} {'held':>4} {'at':>5} {'lean':>4} {'plcd':>5} {'top':>5} {'trav':>5} {'hunt':>4} {'topk':>5} "
          f"{'pop':>7} {'min':>7} {'kills%':>7} {'tear%':>6} {'brwse%':>6} {'tooth':>6} {'kept':>5} {'brkn':>5} {'wound':>5} {'hungr':>5} {'ms':>5}")
    for r in sorted(rows, key=lambda r: r["name"]):
        print(f"{r['name']:>7} {r['flesh_bite']:>5.2f} {r['frail']:>5.2f} {r['wood_yield']:>7.0e} "
              f"{r['kinds_held']:>4} {r['kinds_at']:>5.1f} {r['lean']:>4} {float(r['placed_at']):>5.1f} {float(r['top_kind']):>5.0%} {float(r['travel']):>5.1f} "
              f"{r['by_kills']:>4} {r['top_kills']:>5.0%} "
              f"{r['pop']:>7.0f} {r['pop_min']:>7.0f} {r['kills']:>7.1%} {r['tear']:>6.0%} {r['browse_share']:>6.1%} {r['tooth']:>6.1%} "
              f"{r['blocks_kept']:>5.2f} {r['death_broken']:>5.1%} {r['death_wound']:>5.1%} {r['death_hunger']:>5.1%} {r['ms_step']:>5.1f}")
    if rows:
        out = os.path.join(HERE, "results", "sweep.csv")
        with open(out, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0]))
            w.writeheader()
            w.writerows(rows)
        kout = os.path.join(HERE, "results", "kinds.csv")
        with open(kout, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(per_kind[0]))
            w.writeheader()
            w.writerows(per_kind)
        print(f"\n{len(rows)} runs -> {out}, {len(per_kind)} kinds -> {kout}")
        for r in sorted(rows, key=lambda r: r["name"]):
            print(f"  {r['name']}: {r['ways']}")


if __name__ == "__main__":
    main()
