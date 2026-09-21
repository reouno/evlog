#!/usr/bin/env python3
"""Read the control ladder of the new default world at six seeds (#112, e100).

Run from the repo root: `uv run python experiments/e092_yardstick/sweep.py` (a few minutes).

The six runs are the new default world (e099's three laws back in) with no law added on top. For each it reads, with e075's `read_run` (e068's census by birth form),
kinds at a census, kinds kept to a place, the largest kind's share, the kills' share of what bodies
eat (the world state, e025/e045/e076), bodies, travel and the crowd's jam; and from the censuses the
largest lineage's share of the land's bodies and the lines holding 5% of them. Then the median and
the spread (max - min) of each over the six seeds: that spread is what any later effect is read
against.

It also checks e092's seed 9 (`ctl`) against e081's seed 9 (`u0`) column for column, which is what
lets the two halves of the ladder be one ladder.

Writes `results/ladder.csv` (one row a run) and `results/kinds.csv` (one row a kind of a run).
"""
import csv
import importlib.util
import os
import statistics as st
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "experiments", "e068_kinds"))


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


e075 = load("e075_sweep", os.path.join(ROOT, "experiments", "e075_hunt", "sweep.py"))
kinds = e075.kinds  # e068's census by birth form, which e075's sweep imports

LINE = 0.05  # a lineage holding this share of the land's bodies over the censuses is a line
LADDER = os.path.join(HERE, "results", "ladder")
RUNS = [(s, os.path.join(LADDER, f"c1225_life{s}_ctl")) for s in (9, 10, 11, 12, 13, 14)]
CHECK = None
COLS = [("kinds_at", "kinds at a census", "{:.2f}"), ("kinds_held", "kinds held at every census", "{:.0f}"),
        ("placed_at", "kinds kept to a place", "{:.2f}"), ("top_kind", "the largest kind's share", "{:.1%}"),
        ("top_share", "the largest line's share", "{:.1%}"), ("lines", "lines over 5%", "{:.0f}"),
        ("kills", "kills' share of intake", "{:.1%}"), ("by_kills", "kinds living by killing", "{:.0f}"),
        ("pop", "bodies", "{:.0f}"), ("travel", "travel of a grown body", "{:.1f}"),
        ("blocked", "moves blocked", "{:.1%}"), ("no_room", "births with no room", "{:.1%}")]


def lines_of(pre):
    """From the censuses: the largest lineage's share of the land's bodies, and the lines holding 5%."""
    per = defaultdict(lambda: defaultdict(int))  # step -> lineage -> bodies on land
    with open(pre + "_agents.csv") as f:
        for r in csv.DictReader(f):
            if r["medium"] == "0":
                per[int(r["step"])][r["lineage"]] += 1
    held = defaultdict(int)
    for by in per.values():
        for k, n in by.items():
            held[k] += n
    land = max(sum(held.values()), 1)
    return {"lines": sum(n >= LINE * land for n in held.values()),
            "top_share": st.mean(max(by.values()) / sum(by.values()) for by in per.values())}


def jam(pre):
    """The crowd's jam over the second half: the share of moves blocked and of births with no room."""
    with open(pre + "_log.csv") as f:
        rows = list(csv.DictReader(f))
    half = [r for r in rows if int(r["step"]) >= int(rows[-1]["step"]) / 2]
    born = sum(float(r["births"]) for r in half) + sum(float(r["no_room"]) for r in half)
    return {"no_room": sum(float(r["no_room"]) for r in half) / max(born, 1)}


def series(seed, pre):
    """The kinds at each census of a run: what one run's own count does from census to census."""
    run = kinds.Run(f"seed{seed}", pre)
    unit = run.forms()
    ways = kinds.by_group(run, unit, run.does())
    per, _ = kinds.kinds(run.tally(unit, ways))
    return [{"seed": seed, "step": s, "kinds": len(ws), "placed": sum(w[3] != "shore" for w in ws)}
            for s, ws in sorted(per.items())]


def read(seed, pre):
    row, ks = e075.read_run(f"seed{seed}", pre)
    row.update(lines_of(pre))
    row.update(jam(pre))
    row["seed"] = seed
    return row, ks


def check(new, old):
    """e092's seed 9 against e081's: every column both logs carry, every row both wrote."""
    if not os.path.exists(new + "_row.csv"):
        return "no seed 9 run of e092 to check"
    a = list(csv.DictReader(open(new + "_log.csv")))
    b = list(csv.DictReader(open(old + "_log.csv")))
    shared = [k for k in a[0] if k in b[0] and not k.startswith("ms_")]  # times differ by the machine's hour
    n = min(len(a), len(b))
    bad = [(a[i]["step"], k) for i in range(n) for k in shared if a[i][k] != b[i][k]]
    return (f"seed 9: {len(shared)} columns x {n} rows equal (e092 logs "
            f"{len(a[0]) - len(shared) - sum(k.startswith('ms_') for k in a[0])} columns e081 has not)"
            if not bad else f"seed 9 DIFFERS in {len(bad)} cells, first {bad[:5]}")


def main():
    rows, per_kind, censuses = [], [], []
    for seed, pre in RUNS:
        if not os.path.exists(pre + "_row.csv"):  # written when a run ends: an unfinished run is skipped
            print(f"seed {seed}: no finished run at {pre}")
            continue
        row, ks = read(seed, pre)
        rows.append(row)
        per_kind += ks
        censuses += series(seed, pre)
    if not rows:
        return
    print(f"{'seed':>5} " + " ".join(f"{k:>9}" for k, _, _ in COLS))
    for r in rows:
        print(f"{r['seed']:>5} " + " ".join(f"{f.format(r[k]):>9}" for k, _, f in COLS))
    print(f"\n{'measure':<28} {'median':>9} {'spread':>9} {'lo':>9} {'hi':>9}   (n = {len(rows)} seeds)")
    for k, label, f in COLS:
        v = [r[k] for r in rows]
        print(f"{label:<28} {f.format(st.median(v)):>9} {f.format(max(v) - min(v)):>9} "
              f"{f.format(min(v)):>9} {f.format(max(v)):>9}")
    if CHECK:
        print("\n" + check(*CHECK))
    out = os.path.join(HERE, "results", "ladder.csv")
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    kout = os.path.join(HERE, "results", "kinds.csv")
    with open(kout, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(per_kind[0]))
        w.writeheader()
        w.writerows(per_kind)
    cout = os.path.join(HERE, "results", "census.csv")
    with open(cout, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(censuses[0]))
        w.writeheader()
        w.writerows(censuses)
    print(f"\n{len(rows)} runs -> {out}, {len(per_kind)} kinds -> {kout}, {len(censuses)} censuses -> {cout}")
    for r in rows:
        print(f"  seed {r['seed']}: {r['ways']}")


if __name__ == "__main__":
    main()
