#!/usr/bin/env python3
"""e074 with no pool is e073: compare a check run to the kept run of e073 it copies.

Run from the repo root:

    uv run python experiments/e074_invade/check.py \
      experiments/e074_invade/results/c1225_life9_check \
      experiments/e073_forest/results/ladder/c1225_life9_y3e-5h3

Every shared column of `log.csv` but the wall times, every body of the census at the check run's last
step, every lineage row and every event must agree. The columns e074 adds (the invaders) are ignored.
"""
import csv
import sys

SKIP = ("ms_step", "ms_world", "ms_bodies", "ms_lineage", "ms_wall")


def rows(path):
    with open(path) as f:
        return list(csv.DictReader(f))


def compare(name, mine, theirs, keys=None):
    shared = [k for k in mine[0] if k in theirs[0] and k not in SKIP]
    assert shared, f"{name}: no shared columns"
    theirs = {tuple(r[k] for k in keys): r for r in theirs} if keys else theirs
    n, bad = 0, 0
    for r in mine:
        t = theirs.get(tuple(r[k] for k in keys)) if keys else None
        if keys and t is None:
            print(f"  {name}: {tuple(r[k] for k in keys)} is not in the other run")
            bad += 1
            continue
        n += 1
    if keys:
        pairs = [(r, theirs[tuple(r[k] for k in keys)]) for r in mine if tuple(r[k] for k in keys) in theirs]
    else:
        pairs = list(zip(mine, theirs))
    for a, b in pairs:
        for k in shared:
            if a[k] != b[k]:
                print(f"  {name}: {k} {a[k]} != {b[k]} at {[a[j] for j in (keys or ['step'])]}")
                bad += 1
                if bad > 10:
                    return False
    print(f"  {name}: {len(pairs)} rows, {len(shared)} shared columns, {'same' if not bad else str(bad) + ' DIFFER'}")
    return not bad


def main():
    mine, theirs = sys.argv[1], sys.argv[2]
    ok = True
    log = rows(mine + "_log.csv")
    last = int(log[-1]["step"])
    ok &= compare("log", log, [r for r in rows(theirs + "_log.csv") if int(r["step"]) <= last])
    agents = [r for r in rows(mine + "_agents.csv") if int(r["step"]) == last]
    ok &= compare("agents", agents, [r for r in rows(theirs + "_agents.csv") if int(r["step"]) == last], keys=["id"])
    ok &= compare("lineages", rows(mine + "_lineages.csv"), [r for r in rows(theirs + "_lineages.csv") if int(r["step"]) <= last])
    ok &= compare("events", rows(mine + "_events.csv"), [r for r in rows(theirs + "_events.csv") if int(r["step"]) <= last])
    print("SAME" if ok else "DIFFERENT")


if __name__ == "__main__":
    main()
