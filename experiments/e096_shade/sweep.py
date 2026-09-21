#!/usr/bin/env python3
"""e093's batch (#103) against the control ladder, a distribution against a distribution.

Run from the repo root: `uv run python experiments/e093_leaf/sweep.py` (a few minutes).

Twelve runs of the same world on the same six seeds: the control ladder (e081's seeds 9-11 and
e092's 12-14, no light) and e093's six at `light_gain` 0.016. For each it reads, with e075's
`read_run` (e068's census by birth form), kinds at a census, kinds kept to a place, the largest
kind's and the largest line's share, the kills' share, bodies, travel and the crowd's jam; and from
the censuses the light's own measures: the kinds led by the light, the bodies in them, how open
their blocks are against the world's, and the bodies per cell where they stand.

The rule is `foundation.md`'s: the median and the spread of each over six seeds, effect against
spread, with the categorical done-whens (is there a light-led kind, does a form keep to it) deciding.

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
RUN = {s: os.path.join(HERE, "results", "batch", f"c1225_life{s}_g0.016") for s in SEEDS}
COLS = [("kinds_at", "kinds at a census", "{:.2f}"), ("placed_at", "kinds kept to a place", "{:.2f}"),
        ("by_light", "kinds led by the light", "{:.0f}"), ("in_light", "grown bodies in them", "{:.1%}"),
        ("open_light", "open faces a block, in them", "{:.2f}"), ("open_all", "open faces a block, all", "{:.2f}"),
        ("per_cell", "bodies a cell held", "{:.2f}"), ("per_cell_light", "where the light-led stand", "{:.2f}"),
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


def light_of(pre, run, unit, ways):
    """The light's own measures of a run, over the grown bodies of its censuses. Without the column
    (the control) every one of them is 0 but the shape and the crowd, which every run has."""
    rows = defaultdict(list)
    for i, r in enumerate(run.grown):
        rows[ways[unit[i]]].append(r)
    grown = len(run.grown)
    led, in_led, open_led, cells_led, wet_led = [], 0, [], Counter(), 0
    for w, rs in rows.items():
        if len(rs) < SHARE * grown:
            continue
        got = [kinds.census.light_share(r) for r in rs]
        got = [g for g in got if g is not None]
        if got and st.mean(got) >= kinds.census.LIGHT:
            led.append(w)
            in_led += len(rs)
            open_led += [kinds.open_soft(r) / max(float(r["size"]), 1) for r in rs]
            cells_led.update(r["cell"] for r in rs)
            wet_led += sum(r["medium"] != "0" for r in rs)
    every = census(pre)
    at = defaultdict(list)
    for r in every:
        at[r["step"]].append(r)
    return {"by_light": len(led), "in_light": in_led / max(grown, 1),
            "land_share": sum(r["medium"] == "0" for r in run.grown) / max(grown, 1),
            "water_led": wet_led / max(in_led, 1),
            "born_med": st.median(float(r["born_size"]) for r in run.grown),
            "open_light": st.mean(open_led) if open_led else 0.0,
            "open_all": st.mean(kinds.open_soft(r) / max(float(r["size"]), 1) for r in run.grown),
            "per_cell": st.mean(len(rs) / len({r["cell"] for r in rs}) for rs in at.values()),
            "per_cell_light": in_led / max(len(cells_led), 1) if cells_led else 0.0}


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
        food = sum(float(r["plant"]) + float(r["meat"]) + float(r.get("light") or 0.0) for r in rs)
        take = lambda k: sum(float(r.get(k) or 0.0) for r in rs) / max(food, 1e-9)  # noqa: E731
        out.append({"seed": seed, "kind": " / ".join(w), "share": len(rs) / len(run.grown),
                    "side": side, "cells": cells,
                    "born_size": st.median(float(r["born_size"]) for r in rs),
                    "open_block": st.mean(kinds.open_soft(r) / max(float(r["size"]), 1) for r in rs),
                    "travel": st.median(float(r["travel"]) for r in rs),
                    "light": take("light"), "plant": take("plant"), "kills": take("killed"),
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
    row.update(light_of(pre, run, unit, ways))
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
    for label, pres in (("control", CTL), ("light", RUN)):
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
    if len(out.get("control", [])) and len(out.get("light", [])):
        print(f"\n{'measure':<32}{'control':>12}{'light':>12}{'effect':>12}{'ctl spread':>12}{'light spread':>14}")
        for k, label, f in COLS:
            c = [r[k] for r in out["control"]]
            l = [r[k] for r in out["light"]]
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
    rows = out.get("control", []) + out.get("light", [])
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
