#!/usr/bin/env python3
"""Read e076's invasion runs (#92): what the hunter's and the grazer's lines did, and what came back.

Run from the repo root once the runs are done (about a minute a run):

    uv run python experiments/e076_pair/invade.py [dir]

Both lines are in every run: mark 1 is the grazer's genomes, mark 2 the hunter's. In the grazer's
world (`oA`) the hunter is the invader and the grazer's line the neutral control; in the hunter's
world (`oB`) it is the other way round. For each run it prints

  - each line's count at the injection and over the last 5,000 steps, and its way at the last census;
  - **what came back** (the question of #92): the kills' share of the world's food by step; whether
    the other kind's way is among the kinds of the census at step 10,000 (e068's census on that census
    alone) - in the grazer's world a land kind with a tooth that takes HUNTER or more of its food from
    kills, in the hunter's world a plant eater with no tooth; the share of the unmarked bodies living
    that way at each census, one body at a time (against the donor world's share); and whether it is a
    kind of the residents at the end;
  - the kinds over the second half, and for each the share of its bodies that carry a mark.

Writes `results/invade.csv` and `results/kinds_invade.csv`.
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

HUNTER = 0.4    # a land kind's share of its food from kills for it to be the hunter's way (pick.py)
WINDOW = 5000   # steps at the end over which a line is counted
INJECT = 10000
MARKS = {1: "grazer", 2: "hunter"}


def food(rs):
    return sum(float(r["plant"]) + float(r["meat"]) for r in rs)


def share(rs, key):
    return sum(float(r[key]) for r in rs) / max(food(rs), 1e-9)


def tooth(rs):
    return sum(census.has_tooth(r) for r in rs) / max(len(rs), 1)


def intake(r):
    return max(float(r["plant_intake"]) + float(r["meat_intake"]), 1e-9)


def kinds_over(pre, steps):
    """e068's kinds over the censuses `steps` alone: {way: [grown rows]} of the last of them, the
    kinds at each census and the kinds held."""
    late = census.late
    census.late = lambda _s: list(steps)
    try:
        run = kinds.Run(os.path.basename(pre), pre)
    finally:
        census.late = late
    unit = run.forms()
    ways = kinds.by_group(run, unit, run.does())
    per, held = kinds.kinds(run.tally(unit, ways))
    rows = {}
    for i in run.at[steps[-1]]:
        rows.setdefault(ways[unit[i]], []).append(run.grown[i])
    return rows, per, held


def is_hunter(w, rs):
    return w[3] == "land" and w[1] == "tooth" and share(rs, "killed") >= HUNTER


def is_grazer(w, rs):
    return w[0] == "plant" and w[1] == "no tooth" and w[3] in ("land", "shore")


def hunter_body(r):
    """A body living the hunter's way by e060's reading of one body: a tooth, roaming, a third or more
    of its food flesh, standing on the land."""
    return census.way(r) in (("mixed", "tooth", "roams"), ("flesh", "tooth", "roams")) and r["medium"] == "0"


def grazer_body(r):
    """A body living the grazer's way: a plant eater with no tooth that stays, out of the surface."""
    return census.way(r) == ("plant", "no tooth", "stays") and r["medium"] != "1"


def donor(seed):
    """The same per-body shares in the donor world at its last census, which the runs are read against."""
    agents = census.read(os.path.join(HERE, "results", "donor", f"c1225_life{seed}_donor_agents.csv"))
    rs = census.grown(agents[max(agents)])
    return sum(hunter_body(r) for r in rs) / len(rs), sum(grazer_body(r) for r in rs) / len(rs)


def read_run(pre, kind_rows):
    name = os.path.basename(pre)
    parts = name.split("_")  # c1225_life9_oA_s1: the world of the one kind named
    seed, world, draw = int(parts[1].replace("life", "")), parts[2], int(parts[3][1:])
    invader = "hunter" if world == "oA" else "grazer"
    with open(pre + "_log.csv") as f:
        log = list(csv.DictReader(f))
    at = {int(r["step"]): r for r in log}
    last = int(log[-1]["step"])
    tail = [r for r in log if int(r["step"]) > last - WINDOW]
    half = [r for r in log if int(r["step"]) >= last / 2]
    agents = census.read(pre + "_agents.csv")
    grown = {s: census.grown(rs) for s, rs in agents.items()}

    out = {"run": name, "seed": seed, "world": world, "draw": draw, "invader": invader,
           "pop_end": st.mean(float(r["pop"]) for r in tail),
           "pop_mean": st.mean(float(r["pop"]) for r in half),
           "pop_min": min(float(r["pop"]) for r in log),
           "pop_land": st.mean(float(r["pop_land"]) for r in half),
           "pop_surface": st.mean(float(r["pop_surface"]) for r in half),
           "pop_bottom": st.mean(float(r["pop_bottom"]) for r in half),
           "err": max(float(r["matter_err"]) for r in log),
           "kills_half": st.mean(float(r["kill_intake"]) for r in half) / st.mean(intake(r) for r in half),
           "browse_half": st.mean(float(r["browse_intake"]) for r in half) / st.mean(intake(r) for r in half)}
    out["donor_hunters"], out["donor_grazers"] = donor(seed)
    for m, who in MARKS.items():
        n0 = float(at[INJECT][f"inv{m}"])
        n_end = st.mean(float(r[f"inv{m}"]) for r in tail)
        mine = [r for r in grown[last] if r.get("invader") == str(m)]
        out[f"{who}_n0"] = n0
        out[f"{who}_end"] = n_end
        out[f"{who}_max"] = max(float(r[f"inv{m}"]) for r in log)
        out[f"{who}_alive"] = float(log[-1][f"inv{m}"]) > 0
        out[f"{who}_r_1k"] = math.log(max(n_end, 0.5) / max(n0, 1)) / ((last - INJECT) / 1000)
        out[f"{who}_share"] = n_end / max(out["pop_end"], 1)
        out[f"{who}_grown"] = len(mine)
        out[f"{who}_kills"] = share(mine, "killed") if mine else float("nan")
        out[f"{who}_wood"] = share(mine, "wood") if mine else float("nan")
        out[f"{who}_tooth"] = tooth(mine) if mine else float("nan")
        out[f"{who}_way"] = "/".join(kinds.way_of(mine)) if mine else "-"
        out[f"{who}_land"] = (st.mean(float(r[f"inv{m}_land"]) for r in tail) / n_end) if n_end else float("nan")

    # What came back before the injection: the kills' share of the world's food by step, and the
    # unmarked grown bodies of each census (a body with a tooth; one of the land that takes HUNTER of
    # its own food from kills with a tooth; a plant eater with no tooth).
    pre_inj = [r for r in log if int(r["step"]) <= INJECT]
    out["kills_1k"] = float(pre_inj[0]["kill_intake"]) / intake(pre_inj[0])
    out["kills_10k"] = st.mean(float(r["kill_intake"]) / intake(r) for r in pre_inj if int(r["step"]) > INJECT - 2000)
    out["tooth_1k"] = float(pre_inj[0]["tooth"])
    out["tooth_10k"] = float(at[INJECT]["tooth"])
    for s in sorted(grown):
        res = [r for r in grown[s] if r.get("invader") == "0"]
        tag = "at_inject" if s == INJECT else "end" if s == last else f"{s // 1000}k"
        out[f"residents_{tag}"] = len(res)
        out[f"res_kills_{tag}"] = share(res, "killed")
        out[f"res_tooth_{tag}"] = tooth(res)
        out[f"res_hunters_{tag}"] = sum(hunter_body(r) for r in res) / max(len(res), 1)
        out[f"res_grazers_{tag}"] = sum(grazer_body(r) for r in res) / max(len(res), 1)

    # The other kind's way among the kinds of the census at the injection (e068's census on that census
    # alone; no marked body is grown yet). This is the reading hypotheses 1 and 2 were written for.
    test = is_hunter if world == "oA" else is_grazer
    rows, per, _ = kinds_over(pre, [INJECT])
    back = [w for w in per[INJECT] if test(w, rows[w])]
    out["kinds_at_inject"] = len(per[INJECT])
    out["back_at_inject"] = "; ".join("/".join(w) + f" ({len(rows[w])}, kills {share(rows[w], 'killed'):.0%})" for w in back) or "-"
    out["back_n_at_inject"] = sum(len(rows[w]) for w in back)

    # The kinds over the second half, and the share of each that carries a mark.
    steps = census.late(list(agents))
    rows, per, held = kinds_over(pre, steps)
    out["kinds_at"] = kinds.mean_count(per)
    out["kinds_held"] = len(held)
    out["placed_at"] = st.mean(sum(w[3] != "shore" for w in ws) for ws in per.values())
    # The other kind's way at the end, over the second half's censuses as stage C reads kinds: the kinds
    # of the last census that are the other's way and whose bodies mostly carry no mark, so that the
    # injected line is not read as the residents' own.
    resident = lambda rs: sum(r["invader"] == "0" for r in rs)  # noqa: E731
    back = [w for w in per[last] if test(w, rows[w]) and resident(rows[w]) >= len(rows[w]) / 2]
    out["back_end"] = "; ".join("/".join(w) + f" ({len(rows[w])}, kills {share(rows[w], 'killed'):.0%})" for w in back) or "-"
    out["back_n_end"] = sum(resident(rows[w]) for w in back)
    out["hunter_kinds_end"] = sum(is_hunter(w, rows[w]) for w in per[last])
    out["grazer_kinds_end"] = sum(is_grazer(w, rows[w]) for w in per[last])
    for w in sorted(per[last], key=lambda w: -len(rows[w])):
        rs = rows[w]
        kind_rows.append({"run": name, "seed": seed, "world": world, "draw": draw, "way": "/".join(w),
                          "n": len(rs), "held": w in held, "kills": share(rs, "killed"), "wood": share(rs, "wood"),
                          "tooth": tooth(rs), "grazer_mark": sum(r["invader"] == "1" for r in rs) / len(rs),
                          "hunter_mark": sum(r["invader"] == "2" for r in rs) / len(rs)})
    return out


def main():
    d = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "results", "invade")
    pres = sorted(os.path.join(d, f[: -len("_agents.csv")]) for f in os.listdir(d) if f.endswith("_agents.csv"))
    pres = [p for p in pres if os.path.exists(p + "_row.csv")]  # a run still going has no summary row
    kind_rows = []
    rows = [read_run(p, kind_rows) for p in pres]
    rows.sort(key=lambda r: (r["seed"], r["world"], r["draw"]))
    for path, rs in (("invade.csv", rows), ("kinds_invade.csv", kind_rows)):
        with open(os.path.join(HERE, "results", path), "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rs[0]), lineterminator="\n")
            w.writeheader()
            w.writerows(rs)
    print(f"{'run':22s} {'invader':7s} | {'grazer n0':>9s} {'end':>7s} {'kills':>5s} | "
          f"{'hunter n0':>9s} {'end':>7s} {'kills':>5s} {'tooth':>5s} | {'pop':>6s} {'min':>6s}")
    for r in rows:
        print(f"{r['run']:22s} {r['invader']:7s} | {r['grazer_n0']:9.0f} {r['grazer_end']:7.1f} {r['grazer_kills']:5.0%} | "
              f"{r['hunter_n0']:9.0f} {r['hunter_end']:7.1f} {r['hunter_kills']:5.0%} {r['hunter_tooth']:5.0%} | "
              f"{r['pop_mean']:6.0f} {r['pop_min']:6.0f}")
    print(f"\n{'run':22s} {'kills 1k':>8s} {'10k':>5s} {'half':>5s} {'tooth 10k':>9s} {'hunters':>7s} {'grazers':>7s} | back at 10k")
    for r in rows:
        print(f"{r['run']:22s} {r['kills_1k']:8.1%} {r['kills_10k']:5.1%} {r['kills_half']:5.1%} {r['res_tooth_at_inject']:9.1%} "
              f"{r['res_hunters_at_inject']:7.1%} {r['res_grazers_at_inject']:7.1%} | {r['back_at_inject']}")
    print(f"\n{'run':22s} {'kinds':>5s} {'held':>4s} {'placed':>6s} | the other way's bodies among the residents "
          f"at 10k / 20k / 30k / end (donor) | its kinds at the end")
    for r in rows:
        key = "res_hunters" if r["world"] == "oA" else "res_grazers"
        d = r["donor_hunters"] if r["world"] == "oA" else r["donor_grazers"]
        print(f"{r['run']:22s} {r['kinds_at']:5.2f} {r['kinds_held']:4d} {r['placed_at']:6.2f} | "
              + " / ".join(f"{r.get(f'{key}_{t}', float('nan')):5.1%}" for t in ("at_inject", "20k", "30k", "end"))
              + f" ({d:.1%}) | {r['back_end']}")


if __name__ == "__main__":
    main()
