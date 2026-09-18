#!/usr/bin/env python3
"""The pools of #92's invasion test: the hunter and the grazer of a donor run.

Run from the repo root, once the donor runs are done (a minute a run):

    uv run python experiments/e076_pair/pick.py results/donor/c1225_life9_donor ...

For each donor run it reads the kinds by birth form (e068's `kinds.py`) over the second half and names
the two ways of living the test uses at the last census:

  - **the hunter** (B): the land kind holding e060's 5% of the census with the largest share of its
    food from kills (the census's `killed`, the flesh of the living alone), which must be HUNTER or
    more (e075: `mixed/tooth/roams/land`, 45-53%);
  - **the grazer** (A): the largest way of the land or the shore with e060's plant diet and no tooth
    (e075: `plant/no tooth/stays/shore`, 6-12% kills). It need not hold 5%: on seed 9 it is 4.6%.

It writes their genomes (`<life>_A.csv`, `<life>_B.csv`, one `medium,genome` a line, the medium the
body stood in), which seed the one-kind worlds and are what is injected.

e074 also built worlds with a whole way of living taken out, form by form. In e075's world that is not
a community any more, and this prints why: the share of the census in forms that take a quarter or
more of their food from kills.
"""
import csv
import os
import sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "experiments", "e068_kinds"))
sys.path.insert(0, os.path.join(ROOT, "experiments", "e060_census"))
import census  # noqa: E402  (e060's census of ways of living)
import kinds  # noqa: E402  (e068's census by birth form)

HUNTER = 0.4  # a land kind's share of its food from kills for it to be the hunter (#92)
KILLER = 0.25  # a form's share from kills for it to live partly by killing (e060's hunter world)
LEAST = 100   # grown bodies a way needs at the census to seed a world


def food(rs):
    return sum(float(r["plant"]) + float(r["meat"]) for r in rs)


def share(rs, key):
    return sum(float(r[key]) for r in rs) / max(food(rs), 1e-9)


def tooth(rs):
    return sum(int(float(r["bite_any"])) >= census.TOOTH for r in rs) / max(len(rs), 1)


def travel(rs):
    return sorted(float(r["travel"]) for r in rs)[len(rs) // 2]


def pick(pre, out_dir):
    name = os.path.basename(pre)
    run = kinds.Run(name, pre)
    unit = run.forms()
    ways = kinds.by_group(run, unit, run.does())
    per, held = kinds.kinds(run.tally(unit, ways))
    last = max(run.steps)
    rows, form_rows = defaultdict(list), defaultdict(list)
    for i in run.at[last]:
        rows[ways[unit[i]]].append(run.grown[i])
        form_rows[unit[i]].append(run.grown[i])
    n = len(run.at[last])

    print(f"\n=== {name}: censuses {run.steps}, {n} grown at {last}, {len(held)} kinds held")
    for w in sorted(rows, key=lambda w: -len(rows[w])):
        rs = rows[w]
        if len(rs) < 40:
            continue
        print(f"  {'/'.join(w):34s} n={len(rs):5d} kills={share(rs, 'killed'):4.0%} wood={share(rs, 'wood'):4.0%} "
              f"tooth={tooth(rs):4.0%} travel={travel(rs):5.1f} kind={w in per[last]:d} held={w in held:d} "
              f"media={dict(sorted(Counter(r['medium'] for r in rs).items()))}")

    land = [w for w in per[last] if w[3] == "land"]
    b = max((w for w in land if share(rows[w], "killed") >= HUNTER), key=lambda w: share(rows[w], "killed"), default=None)
    a = max((w for w in rows if w[0] == "plant" and w[1] == "no tooth" and w[3] in ("land", "shore")
             and len(rows[w]) >= LEAST), key=lambda w: len(rows[w]), default=None)
    assert b is not None, f"{name}: no land kind lives by killing"
    assert a is not None, f"{name}: no grazer of the land or the shore"
    print(f"  B the hunter: {'/'.join(b)} ({len(rows[b])} bodies, kills {share(rows[b], 'killed'):.0%})")
    print(f"  A the grazer: {'/'.join(a)} ({len(rows[a])} bodies, kills {share(rows[a], 'killed'):.0%})")
    killers = sum(len(rs) for rs in form_rows.values() if share(rs, "killed") >= KILLER)
    print(f"  forms taking {KILLER:.0%} or more from kills: {killers} of {n} grown bodies ({killers / n:.0%})")

    genome = {}
    with open(pre + "_genomes.csv") as f:
        for r in csv.DictReader(f):
            if int(r["step"]) == last:
                genome[r["id"]] = r["genome"]
    pools = {"A": [], "B": []}
    for i in run.at[last]:
        r = run.grown[i]
        g = genome.get(r["id"])
        if g is None:
            continue
        w = ways[unit[i]]
        if w == a:
            pools["A"].append((r["medium"], g))
        if w == b:
            pools["B"].append((r["medium"], g))

    os.makedirs(out_dir, exist_ok=True)
    life = name.split("_")[1]
    for tag, lines in pools.items():
        path = os.path.join(out_dir, f"{life}_{tag}.csv")
        with open(path, "w") as f:
            f.write("medium,genome\n")
            for m, g in lines:
                f.write(f"{m},{g}\n")
        print(f"  pool {tag} {len(lines):5d} genomes, media {dict(sorted(Counter(m for m, _ in lines).items()))} -> {path}")
    # For the report: each kind's most common birth body, drawn from a body of it that has lost no block.
    for tag, w in (("A", a), ("B", b)):
        sig = Counter(kinds.signature(r) for r in rows[w]).most_common(1)[0][0]
        body = next((r for r in rows[w] if kinds.signature(r) == sig and kinds.intact(r)), None)
        if body is not None:
            BODIES.append({"run": name, "tag": tag, "way": "/".join(w), "same_form": sum(kinds.signature(r) == sig for r in rows[w]) / len(rows[w]),
                           **{k: body[k] for k in ("side", "cells", "born_size", "born_hard", "born_muscle", "born_sensor",
                                                   "born_digestive", "born_bite", "travel", "medium")}})

    out = {"run": name, "grown_at_last": n, "kinds_at_last": len(per[last]), "kinds_held": len(held),
           "killer_share": killers / n}
    for tag, w in (("A", a), ("B", b)):
        rs = rows[w]
        out.update({f"{tag}": "/".join(w), f"{tag}_bodies": len(rs), f"{tag}_kills": share(rs, "killed"),
                    f"{tag}_wood": share(rs, "wood"), f"{tag}_tooth": tooth(rs), f"{tag}_travel": travel(rs),
                    f"{tag}_lineages": len(set(r["lineage"] for r in rs)),
                    f"{tag}_land": sum(r["medium"] == "0" for r in rs) / len(rs)})
    return out


BODIES = []  # one birth body of each kind, for the report's gallery


def main():
    out_dir = os.path.join(HERE, "results", "pools")
    rows = [pick(a if os.path.isabs(a) else os.path.join(HERE, a), out_dir) for a in sys.argv[1:]]
    for path, rs in (("kinds.csv", rows), ("bodies.csv", BODIES)):
        with open(os.path.join(HERE, "results", path), "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rs[0]), lineterminator="\n")
            w.writeheader()
            w.writerows(rs)


if __name__ == "__main__":
    main()
