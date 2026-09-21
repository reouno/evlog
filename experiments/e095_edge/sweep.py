#!/usr/bin/env python3
"""e095's batch (#107) against the control ladder, a distribution against a distribution.

Run from the repo root: `uv run python experiments/e095_edge/sweep.py` (a few minutes).

Twelve runs of the same world on the same six seeds: the control ladder (e081's seeds 9-11 and
e092's 12-14, neither law) and e095's six at the pair of rates the ladders picked. For each it reads,
with e075's `read_run` (e068's census by birth form), kinds at a census, kinds kept to a place, the
largest kind's and the largest line's share, the kills' share, bodies, travel and the crowd's jam;
and from the censuses the two materials' own measures: a kind led by the spike (most of its flesh
taken through one) and a kind the legs move (it travels where the rest do not), the bodies in each,
how open their blocks are against the world's, and where their spikes and legs sit.

The rule is `foundation.md`'s: the median and the spread of each over six seeds, effect against
spread, with the categorical done-whens (is there a kind of its own, does a form keep to it) deciding.

Writes `results/batch.csv` (a row a run) and `results/kinds.csv` (a row a kind of a run).
"""
import csv
import importlib.util
import os
import statistics as st
import subprocess
import sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "experiments", "e068_kinds"))


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


e075 = load("e075_sweep", os.path.join(ROOT, "experiments", "e075_hunt", "sweep.py"))
e092 = load("e092_sweep", os.path.join(ROOT, "experiments", "e092_yardstick", "sweep.py"))
kinds = e075.kinds

SHARE = 0.05  # of the grown bodies, e060's line for a kind
PROV = []  # e094 (#106): what each reading actually used, written beside the results
SEEDS = [9, 10, 11, 12, 13, 14]
CTL = {s: os.path.join(ROOT, "experiments", "e081_drink" if s < 12 else "e092_yardstick", "results", "ladder",
                       f"c1225_life{s}_" + ("u0" if s < 12 else "ctl")) for s in SEEDS}
PAIR = os.environ.get("EVLOG_PAIR", "pair")  # the batch's name, set when the ladders have picked
RUN = {s: os.path.join(HERE, "results", "batch", f"c1225_life{s}_{PAIR}") for s in SEEDS}
SHARP = 0.5   # of a kind's flesh taken through a spike: it lives by the spike
ROAMS = 2.0   # a kind travels where the rest do not: this many times the run's own median
LEGGED = 0.5  # of a kind's motor coming from its legs: the legs move it
COLS = [("kinds_at", "kinds at a census", "{:.2f}"), ("placed_at", "kinds kept to a place", "{:.2f}"),
        ("by_spike", "kinds led by the spike", "{:.0f}"), ("in_spike", "grown bodies in them", "{:.1%}"),
        ("by_leg", "kinds the legs move", "{:.0f}"), ("in_leg", "grown bodies in them", "{:.1%}"),
        ("open_edge", "open faces a block, in them", "{:.2f}"), ("open_all", "open faces a block, all", "{:.2f}"),
        ("spikes", "spikes a grown body", "{:.2f}"), ("legs_out", "leg faces that pull, a body", "{:.2f}"),
        ("leg_motor", "the legs' share of the motor", "{:.1%}"),
        ("sharp_flesh", "flesh taken through a spike", "{:.1%}"),
        ("per_cell", "bodies a cell held", "{:.2f}"), ("per_cell_edge", "where those kinds stand", "{:.2f}"),
        ("top_kind", "the largest kind's share", "{:.1%}"), ("top_share", "the largest line's share", "{:.1%}"),
        ("kills", "kills' share of intake", "{:.1%}"), ("pop", "bodies", "{:.0f}"),
        ("travel", "travel of a grown body", "{:.1f}"), ("blocked", "moves blocked", "{:.1%}"),
        ("no_room", "births with no room", "{:.1%}"), ("grass_stand", "grass a land cell", "{:.3f}")]


def census(pre):
    """The rows of a census, from the file or from what `tidy.py` compressed."""
    path = pre + "_agents.csv"
    text = open(path).read() if os.path.exists(path) else \
        subprocess.run(["zstd", "-dc", path + ".zst"], capture_output=True, text=True).stdout
    return list(csv.DictReader(text.splitlines()))


def spikes_of(row):
    """The blocks of a birth grid that are a spike toward at least one side: a hard block with
    nothing of the body ahead of it or to either side across that line (`body.rs::is_spike`)."""
    s, g = int(row["side"]), [int(c) for c in row["cells"]]
    at = lambda y, x: g[y * s + x] if 0 <= y < s and 0 <= x < s else 0  # noqa: E731
    n = 0
    for i, k in enumerate(g):
        if k != 1:
            continue
        y, x = divmod(i, s)
        ahead = [(y - 1, x, [(y, x - 1), (y, x + 1)]), (y + 1, x, [(y, x - 1), (y, x + 1)]),
                 (y, x - 1, [(y - 1, x), (y + 1, x)]), (y, x + 1, [(y - 1, x), (y + 1, x)])]
        if any(at(ay, ax) == 0 and all(at(by, bx) == 0 for by, bx in side) for ay, ax, side in ahead):
            n += 1
    return n


def sharp_share(r):
    """The share of a body's flesh that came in through a spike, or None where it ate none."""
    if r.get("sharp") in (None, ""):
        return None
    killed = float(r["killed"])
    return float(r["sharp"]) / killed if killed > 0 else None


def rate_of(pre, key):
    """The rate a run was made at, read from its own row (`results/<run>_row.csv`)."""
    with open(pre + "_row.csv") as f:
        row = next(csv.DictReader(f))
    return float(row.get(key) or 0.0)


def motor_share(r, leg):
    """The share of a body's motor that comes from its legs, 0 where the law is off (e048's muscle)."""
    pull = leg * float(r.get("leg_open") or 0.0)
    return pull / (pull + float(r["muscle"])) if pull + float(r["muscle"]) > 0 else 0.0


def edge_of(pre, run, unit, ways):
    """The two materials' own measures of a run, over the grown bodies of its censuses. Without the
    columns (the control) every one of them is 0 but the shape and the crowd, which every run has."""
    rows = defaultdict(list)
    for i, r in enumerate(run.grown):
        rows[ways[unit[i]]].append(r)
    grown = len(run.grown)
    roams = st.median([float(r["travel"]) for r in run.grown] or [0.0])
    leg = rate_of(pre, "leg")
    spike_kinds, leg_kinds, in_spike, in_leg, open_edge, cells_edge = [], [], 0, 0, [], Counter()
    for w, rs in rows.items():
        if len(rs) < SHARE * grown:
            continue
        got = [x for x in (sharp_share(r) for r in rs) if x is not None]
        by_spike = bool(got) and st.mean(got) >= SHARP
        # A kind the legs move: most of its motor comes from its legs, and it travels further than
        # the run's own median. Travel alone is no test - a run with no legs at all has kinds that
        # roam (the hunters do), which is why the motor is read first.
        by_leg = st.mean(motor_share(r, leg) for r in rs) >= LEGGED \
            and st.median(float(r["travel"]) for r in rs) >= ROAMS * roams
        if by_spike:
            spike_kinds.append(w)
            in_spike += len(rs)
        if by_leg:
            leg_kinds.append(w)
            in_leg += len(rs)
        if by_spike or by_leg:
            open_edge += [kinds.open_soft(r) / max(float(r["size"]), 1) for r in rs]
            cells_edge.update(r["cell"] for r in rs)
    every = census(pre)
    at = defaultdict(list)
    for r in every:
        at[r["step"]].append(r)
    flesh = sum(float(r["killed"]) for r in run.grown)
    return {"by_spike": len(spike_kinds), "in_spike": in_spike / max(grown, 1),
            "by_leg": len(leg_kinds), "in_leg": in_leg / max(grown, 1),
            "spikes": st.mean(spikes_of(r) for r in run.grown),
            "legs_out": st.mean(float(r.get("leg_open") or 0.0) for r in run.grown),
            "leg_motor": st.mean(motor_share(r, leg) for r in run.grown),
            "sharp_flesh": sum(float(r.get("sharp") or 0.0) for r in run.grown) / max(flesh, 1e-9),
            "land_share": sum(r["medium"] == "0" for r in run.grown) / max(grown, 1),
            "born_med": st.median(float(r["born_size"]) for r in run.grown),
            "open_edge": st.mean(open_edge) if open_edge else 0.0,
            "open_all": st.mean(kinds.open_soft(r) / max(float(r["size"]), 1) for r in run.grown),
            "per_cell": st.mean(len(rs) / len({r["cell"] for r in rs}) for rs in at.values()),
            "per_cell_edge": (in_spike + in_leg) / max(len(cells_edge), 1) if cells_edge else 0.0}


def bodies_of(seed, pre, least=0.03):
    """For the gallery: each kind of a run holding `least` of its grown bodies, with the commonest
    birth body of its largest form, how open its blocks are, where it stands and what it ate."""
    run = kinds.Run(f"seed{seed}", pre)
    unit = run.forms()
    ways = kinds.by_group(run, unit, run.does())
    rows = defaultdict(list)
    for i, r in enumerate(run.grown):
        rows[ways[unit[i]]].append(r)
    out = []
    for w, rs in rows.items():
        if len(rs) < least * len(run.grown):
            continue
        shape = Counter((r["side"], r["cells"]) for r in rs if r["size"] == r["born_size"]).most_common(1)
        if not shape:
            continue
        (side, cells), _ = shape[0]
        food = sum(float(r["plant"]) + float(r["meat"]) for r in rs)
        take = lambda k: sum(float(r.get(k) or 0.0) for r in rs) / max(food, 1e-9)  # noqa: E731
        out.append({"seed": seed, "kind": " / ".join(w), "share": len(rs) / len(run.grown),
                    "side": side, "cells": cells,
                    "born_size": st.median(float(r["born_size"]) for r in rs),
                    "open_block": st.mean(kinds.open_soft(r) / max(float(r["size"]), 1) for r in rs),
                    "travel": st.median(float(r["travel"]) for r in rs),
                    "spikes": st.mean(spikes_of(r) for r in rs),
                    "legs_out": st.mean(float(r.get("leg_open") or 0.0) for r in rs),
                    "leg_motor": st.mean(motor_share(r, rate_of(pre, "leg")) for r in rs),
                    "sharp": sum(float(r.get("sharp") or 0.0) for r in rs) / max(sum(float(r["killed"]) for r in rs), 1e-9),
                    "plant": take("plant"), "kills": take("killed"),
                    "water": sum(r["medium"] != "0" for r in rs) / len(rs)})
    return sorted(out, key=lambda r: -r["share"])


def read(seed, pre):
    run = kinds.Run(f"seed{seed}", pre)
    PROV.append(kinds.provenance(run))
    unit = run.forms()
    ways = kinds.by_group(run, unit, run.does())
    row, ks = e075.read_run(f"seed{seed}", pre)
    row.update(e092.lines_of(pre))
    row.update(e092.jam(pre))
    row.update(edge_of(pre, run, unit, ways))
    row["seed"] = seed
    return row, ks


def table(name, rows):
    print(f"\n{name}: {'measure':<32}" + "".join(f"{'seed %d' % r['seed']:>10}" for r in rows) + f"{'median':>10}{'spread':>10}")
    for k, label, f in COLS:
        v = [r[k] for r in rows]
        print(f"{' ' * (len(name) + 2)}{label:<32}" + "".join(f"{f.format(x):>10}" for x in v)
              + f"{f.format(st.median(v)):>10}{f.format(max(v) - min(v)):>10}")


def main():
    out, per_kind = {}, []
    for label, pres in (("control", CTL), ("edge", RUN)):
        rows = []
        for seed in SEEDS:
            pre = pres[seed]
            if not os.path.exists(pre + "_row.csv"):
                print(f"{label} seed {seed}: no finished run at {pre}")
                continue
            row, ks = read(seed, pre)
            row["run"] = label
            rows.append(row)
            per_kind += [dict(k, run=label, seed=seed) for k in ks]
        out[label] = rows
        if rows:
            table(label, rows)
    if len(out.get("control", [])) and len(out.get("edge", [])):
        print(f"\n{'measure':<32}{'control':>12}{'edge':>12}{'effect':>12}{'ctl spread':>12}{'edge spread':>14}")
        for k, label, f in COLS:
            c = [r[k] for r in out["control"]]
            l = [r[k] for r in out["edge"]]
            print(f"{label:<32}{f.format(st.median(c)):>12}{f.format(st.median(l)):>12}"
                  f"{f.format(st.median(l) - st.median(c)):>12}{f.format(max(c) - min(c)):>12}{f.format(max(l) - min(l)):>14}")
    bodies = [b for s in SEEDS if os.path.exists(RUN[s] + "_row.csv") for b in bodies_of(s, RUN[s])]
    if bodies:
        with open(os.path.join(HERE, "results", "bodies.csv"), "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(bodies[0]))
            w.writeheader()
            w.writerows(bodies)
    if PROV:
        p = PROV[0]
        print(f"\nwhat was read: {p['censuses']} censuses every {p['every']:,} steps, {p['from']:,} to "
              f"{p['to']:,}; a kind is {p['kind_share']:.0%} of the bodies aged {p['grown_age']}+")
        with open(os.path.join(HERE, "results", "provenance.csv"), "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(p))
            w.writeheader()
            w.writerows(PROV)
    rows = out.get("control", []) + out.get("edge", [])
    if not rows:
        return
    with open(os.path.join(HERE, "results", "batch.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    if per_kind:
        with open(os.path.join(HERE, "results", "kinds.csv"), "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(per_kind[0]))
            w.writeheader()
            w.writerows(per_kind)


if __name__ == "__main__":
    main()
