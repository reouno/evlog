#!/usr/bin/env python3
"""Read e074's invasion runs (#72): what the two injected lines did in the world they entered.

Run from the repo root once the runs are done (about a minute a run):

    uv run python experiments/e074_invade/invade.py [dir]

Both lines are in every run: mark 1 is the grazer's genomes, mark 2 the browser's. In the world
seeded without the browser (`mB`) mark 2 is the invader and mark 1 the neutral control; in the world
without the grazer (`mA`) it is the other way round. For each run it prints each line's count at the
injection and over the last 5,000 steps, its way of living at the last census, and what the world it
entered held. Writes `results/invade.csv`.
"""
import csv
import math
import os
import statistics as st
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "experiments", "e068_kinds"))
sys.path.insert(0, os.path.join(ROOT, "experiments", "e060_census"))
import census  # noqa: E402
import kinds  # noqa: E402

WOOD = 0.2     # the browse's share of a body's food for it to live by wood (e073's line)
WINDOW = 5000  # steps at the end over which a line is counted
INJECT = 10000
MARKS = {1: "grazer", 2: "browser"}


def wood_share(rs):
    food = sum(float(r["plant"]) + float(r["meat"]) for r in rs)
    return sum(float(r["wood"]) for r in rs) / max(food, 1e-9)


def read_run(pre):
    name = os.path.basename(pre)
    parts = name.split("_")  # c1225_life9_mA_s1
    seed, removed, draw = int(parts[1].replace("life", "")), parts[2][1], int(parts[3][1:])
    with open(pre + "_log.csv") as f:
        log = list(csv.DictReader(f))
    at = {int(r["step"]): r for r in log}
    last = int(log[-1]["step"])
    tail = [r for r in log if int(r["step"]) > last - WINDOW]
    half = [r for r in log if int(r["step"]) >= last / 2]
    agents = census.read(pre + "_agents.csv")
    grown = {s: census.grown(rs) for s, rs in agents.items()}

    out = {"run": name, "seed": seed, "world": f"minus{removed}", "draw": draw,
           "invader": "browser" if removed == "B" else "grazer",
           "pop_end": st.mean(float(r["pop"]) for r in tail),
           "pop_mean": st.mean(float(r["pop"]) for r in half),
           "pop_land": st.mean(float(r["pop_land"]) for r in half),
           "pop_surface": st.mean(float(r["pop_surface"]) for r in half),
           "pop_bottom": st.mean(float(r["pop_bottom"]) for r in half),
           "err": max(float(r["matter_err"]) for r in log),
           "browse_share": st.mean(float(r["browse_intake"]) for r in half) /
                           max(st.mean(float(r["plant_intake"]) + float(r["meat_intake"]) for r in half), 1e-9)}
    for m, who in MARKS.items():
        n0 = float(at[INJECT][f"inv{m}"])
        n_end = st.mean(float(r[f"inv{m}"]) for r in tail)
        mine = [r for r in grown[last] if r.get("invader") == str(m)]
        out[f"{who}_n0"] = n0
        out[f"{who}_end"] = n_end
        out[f"{who}_max"] = max(float(r[f"inv{m}"]) for r in log)
        out[f"{who}_alive"] = float(log[-1][f"inv{m}"]) > 0
        out[f"{who}_growth"] = n_end / max(n0, 1)
        out[f"{who}_r_1k"] = math.log(max(n_end, 0.5) / max(n0, 1)) / ((last - INJECT) / 1000)
        out[f"{who}_share"] = n_end / max(out["pop_end"], 1)
        out[f"{who}_grown"] = len(mine)
        out[f"{who}_wood"] = wood_share(mine) if mine else float("nan")
        out[f"{who}_way"] = "/".join(kinds.way_of(mine)) if mine else "-"
        out[f"{who}_land"] = (st.mean(float(r[f"inv{m}_land"]) for r in tail) / max(n_end, 1e-9)) if n_end else float("nan")

    # Did the kind taken out come back on its own, out of the resident genomes? The share of the
    # unmarked grown bodies that live by wood, and that carry a tooth, at the injection and at the end.
    for s in sorted(grown):
        res = [r for r in grown[s] if r.get("invader") == "0"]
        tag = {INJECT: "at_inject", last: "end"}.get(s, f"{s // 1000}k")
        out[f"woody_{tag}"] = sum(wood_share([r]) >= WOOD for r in res) / max(len(res), 1)
        out[f"tooth_{tag}"] = sum(int(float(r["bite_any"])) >= census.TOOTH for r in res) / max(len(res), 1)
        out[f"residents_{tag}"] = len(res)

    # The world's kinds over the second half, as stage C reads them.
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
    rows.sort(key=lambda r: (r["seed"], r["world"], r["draw"]))
    with open(os.path.join(HERE, "results", "invade.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    print(f"{'run':24s} {'invader':8s} | {'grazer n0':>9s} {'end':>7s} {'growth':>6s} {'wood':>5s} | "
          f"{'browser n0':>10s} {'end':>7s} {'growth':>6s} {'wood':>5s} | {'pop':>6s}")
    for r in rows:
        print(f"{r['run']:24s} {r['invader']:8s} | {r['grazer_n0']:9.0f} {r['grazer_end']:7.1f} {r['grazer_growth']:6.2f} "
              f"{r['grazer_wood']:5.0%} | {r['browser_n0']:10.0f} {r['browser_end']:7.1f} {r['browser_growth']:6.2f} "
              f"{r['browser_wood']:5.0%} | {r['pop_mean']:6.0f}")
    print(f"\n{'run':24s} {'kinds':>5s} {'held':>4s} {'woody@10k':>9s} {'woody@end':>9s} {'tooth@10k':>9s} {'browse':>7s}")
    for r in rows:
        print(f"{r['run']:24s} {r['kinds_at']:5.2f} {r['kinds_held']:4d} {r['woody_at_inject']:9.1%} "
              f"{r['woody_end']:9.1%} {r['tooth_at_inject']:9.1%} {r['browse_share']:7.1%}")


if __name__ == "__main__":
    main()
