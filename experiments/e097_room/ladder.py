#!/usr/bin/env python3
"""e097 step 1 (#109): the ladder over the birth rule - what the shape of the search and its reach
buy, read off the logs and the censuses.

Run from the repo root: `uv run python experiments/e097_room/ladder.py` (a minute).

One column a run: the control (e096's own control run of this world and seed, which reproduces
e081's seed-9 run to the body), this experiment's step-0 run (the same world again, with the probe),
and the rungs. The log numbers are the mean over the run's second half; the ways of living come from
each run's own censuses through `analysis`'s classifier (e068's birth form), as the batch would read
them. What each reading used is written to `results/provenance.csv`.
"""
import csv
import importlib.util
import os
import statistics as st
import subprocess
import sys
import tempfile
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "experiments", "e068_kinds"))


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


prov_mod = load("e097_prov", os.path.join(HERE, "prov.py"))
e092 = load("e092_sweep", os.path.join(ROOT, "experiments", "e092_yardstick", "sweep.py"))
e075 = load("e075_sweep", os.path.join(ROOT, "experiments", "e075_hunt", "sweep.py"))
kinds = e075.kinds

SCALE = 0.0625  # a body's matter in the world's (e064)
CTL = os.path.join(ROOT, "experiments", "e096_shade", "results", "c1225_life9_s0g0")
RUNGS = [("probe", "step 0"), ("ring1", "ring r1"), ("r2", "rays r2"), ("ring2", "ring r2"), ("r4", "rays r4")]
COLS = [("pop", "bodies", "{:.0f}"), ("size_mean", "blocks a body", "{:.1f}"),
        ("no_room", "births with no room", "{:.1%}"), ("blocked", "moves blocked", "{:.1%}"),
        ("place_k", "sub-cells a child was placed at", "{:.2f}"),
        ("cells_held", "cells a body stands on", "{:.1%}"), ("land_bare", "land cells none stands on", "{:.1%}"),
        ("travel_p50", "travel of a grown body", "{:.1f}"),
        ("gut_income", "intake a gut block", "{:.4f}"), ("grass", "grass standing", "{:.0f}"),
        ("digestive_mean", "gut blocks a body", "{:.1f}"),
        ("lineages", "lineages", "{:.0f}"),
        ("ms_step", "ms a step", "{:.1f}")]


def read_log(path, upto=None):
    with open(path) as f:
        rows = [r for r in csv.DictReader(f) if upto is None or int(r["step"]) <= upto]
    if not rows:
        return None
    last = int(rows[-1]["step"])
    half = [r for r in rows if int(r["step"]) >= last / 2]
    mean = lambda k: st.mean(float(r[k]) for r in half) if k in half[0] else float("nan")
    out = {k: mean(k) for k, _, _ in COLS}
    out["step"], out["from"], out["rows"] = last, int(half[0]["step"]), len(half)
    born = sum(float(r["births"]) + float(r["no_room"]) for r in half)
    out["no_room"] = sum(float(r["no_room"]) for r in half) / max(born, 1)
    moves = sum(float(r["forward"]) + float(r["left"]) + float(r["right"]) for r in half)
    out["blocked"] = sum(float(r["blocked"]) for r in half) / max(moves, 1)
    interval = int(rows[1]["step"]) - int(rows[0]["step"]) if len(rows) > 1 else 1
    plant = st.mean(float(r["plant_intake"]) for r in half) / SCALE / interval
    # e057's fingerprint: what one gut block takes a step, which no law we kept has moved.
    out["gut_income"] = plant / max(out["pop"], 1) / max(out["digestive_mean"], 1e-9)
    return out


def plain(pre):
    """The censuses of a run `tidy.py` has compressed are read from a copy beside them."""
    if os.path.exists(pre + "_agents.csv") or not os.path.exists(pre + "_agents.csv.zst"):
        return pre
    out = os.path.join(tempfile.gettempdir(), os.path.basename(pre))
    if not os.path.exists(out + "_agents.csv"):
        with open(out + "_agents.csv", "wb") as f:
            subprocess.run(["zstd", "-dc", pre + "_agents.csv.zst"], stdout=f, check=True)
    return out


def read_kinds(name, pre):
    """Ways of living from the run's own censuses: kinds at a census, kinds kept to a place, the
    largest kind's share (`analysis`'s classifier, e068's birth form)."""
    if not (os.path.exists(pre + "_agents.csv") or os.path.exists(pre + "_agents.csv.zst")):
        return None, None
    run = kinds.Run(name, plain(pre))
    p = kinds.provenance(run)
    unit = run.forms()
    ways = kinds.by_group(run, unit, run.does())
    per, _held = kinds.kinds(run.tally(unit, ways))
    top = Counter(ways[unit[i]] for i in range(len(run.grown))).most_common(1)[0][1] / len(run.grown)
    lines = e092.lines_of(plain(pre))
    return {"kinds_at": kinds.mean_count(per),
            "placed_at": st.mean(sum(w[3] != "shore" for w in ws) for ws in per.values()),
            "top_kind": top, "top_share": lines["top_share"], "lines": lines["lines"]}, p


def main():
    runs, prov = [("control", read_log(CTL + "_log.csv", upto=40000), CTL)], []
    for name, label in RUNGS:
        pre = os.path.join(HERE, "results", f"c1225_life9_{name}")
        if os.path.exists(pre + "_log.csv"):
            runs.append((label, read_log(pre + "_log.csv"), pre))
    runs = [(n, r, p) for n, r, p in runs if r]
    names = [n for n, _, _ in runs]
    print(f"{'measure':<34}" + "".join(f"{n:>11}" for n in names))
    print(f"{'step':<34}" + "".join(f"{r['step']:>11,}" for _, r, _ in runs))
    for k, label, f in COLS:
        print(f"{label:<34}" + "".join(f"{f.format(r[k]):>11}" for _, r, _ in runs))
    ways = []
    for name, _, pre in runs:
        w, p = read_kinds(os.path.basename(pre), pre)
        ways.append(w)
        if p:
            prov.append({"reading": "ladder-kinds", "run": os.path.basename(pre), "from": p["from"], "to": p["to"],
                         "items": p["censuses"], "thresholds": "kinds by birth form (e068); a place is not `shore`"})
    if any(ways):
        print()
        for k, label, f in [("kinds_at", "kinds at a census", "{:.2f}"), ("placed_at", "kinds kept to a place", "{:.2f}"),
                            ("top_kind", "the largest kind's share", "{:.1%}"),
                            ("top_share", "the largest line's share", "{:.1%}"), ("lines", "lines holding 5%", "{:.0f}")]:
            print(f"{label:<34}" + "".join((f.format(w[k]) if w else "-").rjust(11) for w in ways))
    for (name, r, pre), w in zip(runs, ways):
        prov.append({"reading": "ladder-log", "run": os.path.basename(pre), "from": r["from"], "to": r["step"],
                     "items": r["rows"], "thresholds": "the run's second half, a row every 1,000 steps"})
    with open(os.path.join(HERE, "results", "ladder.csv"), "w", newline="") as f:
        out = csv.DictWriter(f, fieldnames=["run"] + [k for k, _, _ in COLS] + ["kinds_at", "placed_at", "top_kind", "top_share", "lines", "step"])
        out.writeheader()
        for (name, r, _), w in zip(runs, ways):
            out.writerow({"run": name, **{k: r[k] for k, _, _ in COLS}, **(w or {}), "step": r["step"]})
    print(f"\nprovenance: {prov_mod.write(HERE, 'ladder-kinds', prov)}")


if __name__ == "__main__":
    main()
