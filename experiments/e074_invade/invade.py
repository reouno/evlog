#!/usr/bin/env python3
"""Read e074's invasion runs (#72): what the injected line did, and what the world it entered held.

Run from the repo root once the runs are done (a minute a run):

    uv run python experiments/e074_invade/invade.py [dir]

For every run in the directory (`results/invade` by default) it prints the injected line's count at
the injection and over the last 5,000 steps, its way of living at the last census, the world it
entered (its kinds by birth form, e068's `kinds.py`) and whether the kind taken out came back on its
own out of the resident genomes. Writes `results/invade.csv` and `results/lines.csv`.
"""
import csv
import math
import os
import statistics as st
import sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "experiments", "e068_kinds"))
sys.path.insert(0, os.path.join(ROOT, "experiments", "e060_census"))
import census  # noqa: E402
import kinds  # noqa: E402

WOOD = 0.2   # the browse's share of a body's food for it to live by wood (e073's line)
WINDOW = 5000  # steps at the end over which the line is counted


def wood_share(rs):
    food = sum(float(r["plant"]) + float(r["meat"]) for r in rs)
    return sum(float(r["wood"]) for r in rs) / max(food, 1e-9)


def way_of(rs):
    """The way of living of a group of bodies, as e068 reads a form's."""
    return "/".join(kinds.way_of(rs))


def read_run(pre):
    name = os.path.basename(pre)
    parts = name.split("_")  # c1225_life9_mA_injA
    seed = int(parts[1].replace("life", ""))
    removed, injected = parts[2][1], parts[3][-1]
    with open(pre + "_log.csv") as f:
        log = list(csv.DictReader(f))
    at = {int(r["step"]): r for r in log}
    last = int(log[-1]["step"])
    inject_at = 10000
    inv = lambda r: float(r["invaders"])  # noqa: E731
    n0 = inv(at[inject_at])
    tail = [r for r in log if int(r["step"]) > last - WINDOW]
    n_end = st.mean(inv(r) for r in tail)
    pop_end = st.mean(float(r["pop"]) for r in tail)
    half = [r for r in log if int(r["step"]) >= last / 2]

    # The bodies of the census, marked and not.
    agents = census.read(pre + "_agents.csv")
    steps = sorted(agents)
    marked = {s: [r for r in agents[s] if r.get("invader") == "1"] for s in steps}
    grown_res = {s: [r for r in census.grown(agents[s]) if r.get("invader") != "1"] for s in steps}
    mine = census.grown(marked[last])
    # Did the kind taken out come back on its own? The share of the resident grown bodies that live
    # by wood, and that carry a tooth, at each census.
    woody = {s: sum(wood_share([r]) >= WOOD for r in rs) / max(len(rs), 1) for s, rs in grown_res.items()}
    toothed = {s: sum(int(float(r["bite_any"])) >= census.TOOTH for r in rs) / max(len(rs), 1) for s, rs in grown_res.items()}

    out = {"run": name, "seed": seed, "world": f"minus{removed}", "injected": injected,
           "test": removed == injected, "n0": n0, "n_end": n_end, "n_max": max(inv(r) for r in log),
           "alive": inv(log[-1]) > 0, "growth": n_end / max(n0, 1),
           "r_1k": math.log(max(n_end, 0.5) / max(n0, 1)) / ((last - inject_at) / 1000),
           "share_end": n_end / max(pop_end, 1), "pop_end": pop_end,
           "pop_mean": st.mean(float(r["pop"]) for r in half),
           "pop_land": st.mean(float(r["pop_land"]) for r in half),
           "pop_surface": st.mean(float(r["pop_surface"]) for r in half),
           "pop_bottom": st.mean(float(r["pop_bottom"]) for r in half),
           "err": max(float(r["matter_err"]) for r in log),
           "wood_marked": wood_share(mine) if mine else float("nan"),
           "way_marked": way_of(mine) if mine else "-",
           "marked_grown": len(mine),
           "wood_res": wood_share(grown_res[last]),
           "woody_at_inject": woody.get(inject_at, float("nan")), "woody_end": woody[last],
           "tooth_at_inject": toothed.get(inject_at, float("nan")), "tooth_end": toothed[last],
           "browse_share": st.mean(float(r["browse_intake"]) for r in half) /
                           max(st.mean(float(r["plant_intake"]) + float(r["meat_intake"]) for r in half), 1e-9)}

    # The world's kinds over the second half, as stage C reads them (the injected line among them:
    # it is part of the world once it is in, and `way_marked` says what it is).
    run = kinds.Run(name, pre)
    unit = run.forms()
    ways = kinds.by_group(run, unit, run.does())
    per, held = kinds.kinds(run.tally(unit, ways))
    out["kinds_at"] = kinds.mean_count(per)
    out["kinds_held"] = len(held)
    out["placed_at"] = st.mean(sum(w[3] != "shore" for w in ws) for ws in per.values())
    out["ways"] = "; ".join(sorted("/".join(w) for w in held))
    return out


def main():
    d = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "results", "invade")
    pres = sorted(os.path.join(d, f[: -len("_agents.csv")]) for f in os.listdir(d) if f.endswith("_agents.csv"))
    rows = [read_run(p) for p in pres]
    with open(os.path.join(HERE, "results", "invade.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(f"{'run':28s} {'test':5s} {'n0':>5s} {'end':>7s} {'max':>6s} {'growth':>7s} {'share':>6s} {'wood':>5s}  way of the line")
    for r in sorted(rows, key=lambda r: (r["seed"], r["world"], r["injected"])):
        print(f"{r['run']:28s} {str(r['test']):5s} {r['n0']:5.0f} {r['n_end']:7.1f} {r['n_max']:6.0f} "
              f"{r['growth']:7.2f} {r['share_end']:6.2%} {r['wood_marked']:5.0%}  {r['way_marked']}")
    print(f"\n{'run':28s} {'pop':>7s} {'kinds':>5s} {'held':>4s} {'woody@10k':>9s} {'woody@end':>9s} {'tooth@10k':>9s}")
    for r in sorted(rows, key=lambda r: (r["seed"], r["world"], r["injected"])):
        print(f"{r['run']:28s} {r['pop_mean']:7.0f} {r['kinds_at']:5.2f} {r['kinds_held']:4d} "
              f"{r['woody_at_inject']:9.1%} {r['woody_end']:9.1%} {r['tooth_at_inject']:9.1%}")


if __name__ == "__main__":
    main()
