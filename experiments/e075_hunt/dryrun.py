#!/usr/bin/env python3
"""The scales of e075's two laws (#90), read with no runs of the bodies.

Run from the repo root: `uv run python experiments/e075_hunt/dryrun.py` (a few seconds).

It reads e072's and e073's runs (the census `agents.csv` and the log) and asks what the flesh of a
body is worth against what taking it costs, so that the rates of the tear (`flesh_bite`) and of the
frail line (`frail`) start where they bite. It also re-measures the kills' share: e073's `sweep.py`
read the log's `kill_gain` column, which is the gain **per cell broken**, not a total, and reported
0.0%. The run's own `row.csv` and the census say 8-13%.
"""
import csv
import os
import statistics as st

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
E072 = os.path.join(ROOT, "experiments", "e072_balance", "results")
E073 = os.path.join(ROOT, "experiments", "e073_forest", "results", "ladder")
SEEDS = (9, 10, 11)
UPKEEP, UPKEEP_BODY, MOVE_COST, BITE, CELL_ENERGY = 0.002, 0.032, 0.001, 0.02, 0.02
GROWN = 300


def rows(path):
    with open(path) as f:
        return list(csv.DictReader(f))


def census(pre):
    r = rows(pre + "_agents.csv")
    last = max(set(int(x["step"]) for x in r))
    return [x for x in r if int(x["step"]) == last]


def half(pre):
    r = rows(pre + "_log.csv")
    end = int(r[-1]["step"])
    return [x for x in r if int(x["step"]) >= end / 2]


def q(v, p):
    v = sorted(v)
    return v[int((len(v) - 1) * p)]


def per_turn(bodies, col):
    return st.mean(float(x[col]) / max(int(x["turns"]), 1) for x in bodies)


def main():
    print("1. The kills' share, three ways (e073's kept world, `wood_yield` 3e-5)\n")
    print(f"   {'run':16s} {'log (meat - dead)':>18s} {'row.csv':>9s} {'census':>8s} {'sweep.py (wrong)':>18s}")
    for seed in SEEDS:
        pre = os.path.join(E073, f"c1225_life{seed}_y3e-5h3")
        h = half(pre)
        m = lambda k: st.mean(float(x[k]) for x in h)  # noqa: E731
        intake = m("plant_intake") + m("meat_intake")
        log_share = (m("meat_intake") - m("scavenged")) / intake
        row = float(rows(pre + "_row.csv")[0]["kills_share"])
        c = census(pre)
        food = sum(float(x["plant"]) + float(x["meat"]) for x in c)
        print(f"   seed {seed:<11d} {log_share:>17.1%} {row:>9.1%} {sum(float(x['killed']) for x in c) / food:>8.1%} "
              f"{m('kill_gain') / intake:>18.4%}")

    print("\n2. What one break gives, and what a whole body is worth (seed 9, body units)\n")
    c = census(os.path.join(E073, "c1225_life9_y3e-5h3"))
    size, dens = [float(x["size"]) for x in c], [float(x["density"]) for x in c]
    en, fat = [float(x["energy"]) for x in c], [float(x["fat"]) for x in c]
    block = [(e + f + CELL_ENERGY * d * s) / s for e, f, d, s in zip(en, fat, dens, size)]
    whole = [e + f + CELL_ENERGY * d * s for e, f, d, s in zip(en, fat, dens, size)]
    print(f"   a block of a body      p10 {q(block, 0.1):.3f}  p50 {q(block, 0.5):.3f}  p90 {q(block, 0.9):.3f}")
    print(f"     of which the fat     {q(fat, 0.5) / q(size, 0.5):.3f} of {q(block, 0.5):.3f} at the median "
          f"(energy {q(en, 0.5) / q(size, 0.5):.3f}, matter {CELL_ENERGY * q(dens, 0.5):.3f})")
    print(f"   a whole body           p10 {q(whole, 0.1):.2f}  p50 {q(whole, 0.5):.2f}  p90 {q(whole, 0.9):.2f}"
          f"   ({q(size, 0.5):.0f} blocks: one break is {1 / q(size, 0.5):.1%} of it)")
    h = half(os.path.join(E073, "c1225_life9_y3e-5h3"))
    m = lambda k: st.mean(float(x[k]) for x in h)  # noqa: E731
    pace = st.mean(float(x["pace"]) for x in c)
    presses = st.mean(float(x["pop"]) for x in h) * pace * 1000 * m("forward") / m("cells_broken")
    print(f"   measured gain a break  {m('kill_gain'):.3f}   contacts a press {m('contacts') / (st.mean(float(x['pop']) for x in h) * pace * 1000 * m('forward')):.2f}, "
          f"breaks a contact {m('cells_broken') / m('contacts'):.2f}, presses a break {presses:.0f}")

    print("\n3. What it costs to take it, against what the same turns give from plants (seed 9)\n")
    g = [x for x in c if int(x["age"]) >= GROWN]
    groups = [("all grown", lambda x: True),
              ("tooth and roams", lambda x: float(x["bite_any"]) >= 2 and float(x["travel"]) >= 8),
              ("tooth, stays", lambda x: float(x["bite_any"]) >= 2 and float(x["travel"]) < 8),
              ("no tooth, sits", lambda x: float(x["bite_any"]) < 2 and float(x["travel"]) < 2)]
    print(f"   {'':18s} {'n':>5s} {'killed':>8s} {'plant':>8s} {'dead':>8s} {'move work':>10s} {'upkeep':>8s} {'kids':>5s}   (a turn)")
    for name, sel in groups:
        s = [x for x in g if sel(x)]
        work = st.mean(MOVE_COST * float(x["mass"]) * float(x["path"]) / max(int(x["turns"]), 1) for x in s)
        up = st.mean(UPKEEP * float(x["size"]) + UPKEEP_BODY for x in s)
        print(f"   {name:18s} {len(s):>5d} {per_turn(s, 'killed'):>8.4f} {per_turn(s, 'plant'):>8.4f} "
              f"{per_turn(s, 'scavenged'):>8.4f} {work:>10.4f} {up:>8.4f} {st.mean(float(x['kids']) for x in s):>5.2f}")
    gut = st.median(float(x["digestive"]) for x in g)
    print(f"   a gut of {gut:.0f} blocks takes at most {BITE * gut:.3f} a turn: a break is {m('kill_gain') / (BITE * gut):.1f} turns of full feeding")

    print("\n4. The rates the search starts from\n")
    hold = [e + f for e, f in zip(en, fat)]
    print(f"   `flesh_bite`: a prey holds {q(hold, 0.5):.2f} (p10 {q(hold, 0.1):.2f}, p90 {q(hold, 0.9):.2f}); a tear of")
    for r in (0.05, 0.15, 0.4):
        print(f"      {r:<5g} gives {r * q(hold, 0.5):.3f} on top of a break's {m('kill_gain'):.3f}"
              f" -> {(r * q(hold, 0.5) + m('kill_gain')) / (BITE * gut):.2f} turns of full feeding a break")
    keep = [float(x["size"]) / max(float(x["born_size"]), 1) for x in c]
    print(f"\n   `frail`: a standing body has {q(keep, 0.1):.2f} / {q(keep, 0.5):.2f} / {q(keep, 0.9):.2f} of its birth blocks (p10/p50/p90)")
    for r in (0.5, 0.75, 0.9):
        dead = sum(v < r for v in keep) / len(keep)
        print(f"      {r:<5g} kills {dead:.1%} of the standing crowd at once, and a prey of {q(size, 0.5):.0f} blocks "
              f"dies after {(1 - r) * q(size, 0.5):.0f} breaks ({(1 - r) * q(size, 0.5) * presses:.0f} presses)")

    print("\n5. The crowd, e072's world against e073's kept world (the browse thinned it)\n")
    print(f"   {'run':16s} {'pop':>7s} {'contacts a body a step':>23s} {'breaks a body a step':>21s} {'blocked':>8s}")
    for label, d, name in [("e072 sets", E072, "c1225_life{}_sets"), ("e073 kept", E073, "c1225_life{}_y3e-5h3")]:
        for seed in SEEDS:
            h = half(os.path.join(d, name.format(seed)))
            m = lambda k: st.mean(float(x[k]) for x in h)  # noqa: E731
            pop = m("pop")
            print(f"   {label} seed {seed:<2d} {pop:>7.0f} {m('contacts') / pop / 1000:>23.2f} "
                  f"{m('cells_broken') / pop / 1000:>21.3f} {m('blocked'):>8.2f}")


if __name__ == "__main__":
    main()
