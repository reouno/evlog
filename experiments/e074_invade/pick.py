#!/usr/bin/env python3
"""The pools of #72's invasion test: two kinds of a donor run, and the world without each of them.

Run from the repo root, once the donor runs are done (a minute a run):

    uv run python experiments/e074_invade/pick.py results/donor/c1225_life9_donor ...

For each donor run it reads the kinds by birth form (e068's `kinds.py`) over the second half, names
the two kinds the invasion test uses at the last census

  - **the browser** (B): the land kind with the largest share of its food from the crowns' yield
    (e073's new way of living), which must be a fifth or more, and
  - **the grazer** (A): the largest kind of the land and the shore with no tooth and under a tenth
    of its food from wood,

and writes four pools of genomes out of the grown bodies of that census (`<life>_<tag>.csv`, one
`medium,genome` a line, the medium the body stood in):

  - `A` and `B`: the genomes of each kind, which are what is injected;
  - `minusA` and `minusB`: the community with that kind's forms taken out, which is what a world
    held by the other is seeded with.

It prints the kinds it found and what each pool holds.
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

WOOD = 0.2   # the browse's share of a kind's food for it to live by wood (e073's line)
LAWN = 0.1   # under this the kind does not live by wood


def food(rs):
    return sum(float(r["plant"]) + float(r["meat"]) for r in rs)


def wood_share(rs):
    return sum(float(r["wood"]) for r in rs) / max(food(rs), 1e-9)


def pick(pre, out_dir):
    name = os.path.basename(pre)
    run = kinds.Run(name, pre)
    unit = run.forms()
    ways = kinds.by_group(run, unit, run.does())
    per, held = kinds.kinds(run.tally(unit, ways))
    last = max(run.steps)
    rows = defaultdict(list)
    for i in run.at[last]:
        rows[ways[unit[i]]].append(run.grown[i])

    print(f"\n=== {name}: censuses {run.steps}, {len(run.at[last])} grown at {last}, {len(held)} kinds held")
    for w in sorted(per[last], key=lambda w: -len(rows[w])):
        rs = rows[w]
        med = Counter(r["medium"] for r in rs)
        print(f"  {'/'.join(w):40s} n={len(rs):5d} wood={wood_share(rs):4.0%} held={w in held:d} "
              f"media={dict(med)} lineages={len(set(r['lineage'] for r in rs))}")

    land = [w for w in per[last] if w[3] == "land"]
    b = max((w for w in land if wood_share(rows[w]) >= WOOD), key=lambda w: wood_share(rows[w]), default=None)
    a = max((w for w in per[last] if w[1] == "no tooth" and w[3] in ("land", "shore") and wood_share(rows[w]) < LAWN),
            key=lambda w: len(rows[w]), default=None)
    assert b is not None, f"{name}: no land kind lives by wood"
    assert a is not None, f"{name}: no grazer of the land or the shore"
    print(f"  B the browser: {'/'.join(b)} ({len(rows[b])} bodies, wood {wood_share(rows[b]):.0%})")
    print(f"  A the grazer:  {'/'.join(a)} ({len(rows[a])} bodies, wood {wood_share(rows[a]):.0%})")

    # The genomes of that census, by body id.
    genome = {}
    with open(pre + "_genomes.csv") as f:
        for r in csv.DictReader(f):
            if int(r["step"]) == last:
                genome[r["id"]] = r["genome"]

    pools = {"A": [], "B": [], "minusA": [], "minusB": []}
    for i in run.at[last]:
        r = run.grown[i]
        g = genome.get(r["id"])
        if g is None:
            continue
        w = ways[unit[i]]
        line = (r["medium"], g)
        if w == a:
            pools["A"].append(line)
            pools["minusB"].append(line)
        elif w == b:
            pools["B"].append(line)
            pools["minusA"].append(line)
        else:
            pools["minusA"].append(line)
            pools["minusB"].append(line)

    os.makedirs(out_dir, exist_ok=True)
    life = name.split("_")[1]
    for tag, lines in pools.items():
        path = os.path.join(out_dir, f"{life}_{tag}.csv")
        with open(path, "w") as f:
            f.write("medium,genome\n")
            for m, g in lines:
                f.write(f"{m},{g}\n")
        med = Counter(m for m, _ in lines)
        print(f"  pool {tag:7s} {len(lines):5d} genomes, media {dict(sorted(med.items()))} -> {path}")
    return {"run": name, "A": "/".join(a), "B": "/".join(b), "A_bodies": len(rows[a]), "B_bodies": len(rows[b]),
            "A_wood": wood_share(rows[a]), "B_wood": wood_share(rows[b]),
            "grown_at_last": len(run.at[last]), "kinds_at_last": len(per[last]), "kinds_held": len(held),
            "minusA": len(pools["minusA"]), "minusB": len(pools["minusB"])}


def main():
    args = sys.argv[1:]
    out_dir = os.path.join(HERE, "results", "pools")
    rows = [pick(a if os.path.isabs(a) else os.path.join(HERE, a), out_dir) for a in args]
    with open(os.path.join(HERE, "results", "kinds.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


if __name__ == "__main__":
    main()
