#!/usr/bin/env python3
"""e097's batch (#109 step 1) against the control ladder, a distribution against a distribution.

Run from the repo root: `uv run python experiments/e097_room/sweep.py` (a few minutes).

Twelve runs of the same world on the same six seeds: the control ladder (e081's seeds 9-11 and
e092's 12-14, today's birth rule) and this experiment's six at the rung the ladder picked (`ring` 1,
`reach` 2 - a child looks at every spot at a distance, out to two body lengths). For each it reads,
with e075's `read_run` (e068's census by birth form), kinds at a census, kinds kept to a place, the
largest kind's and the largest line's share, the kills' share, bodies, travel and the crowd's jam.

The rule is `foundation.md`'s: the median and the spread of each over six seeds, effect against
spread. **The population is not a done-when** (#67): a rung that doubles the bodies and changes
nothing about who wins is a failure of this piece.

Writes `results/batch.csv` (a row a run), `results/kinds.csv` (a row a kind of a run) and the
`batch` rows of `results/provenance.csv`.
"""
import csv
import glob
import importlib.util
import os
import statistics as st
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "experiments", "e068_kinds"))


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


prov_mod = load("e097_prov", os.path.join(HERE, "prov.py"))
e075 = load("e075_sweep", os.path.join(ROOT, "experiments", "e075_hunt", "sweep.py"))
e092 = load("e092_sweep", os.path.join(ROOT, "experiments", "e092_yardstick", "sweep.py"))
kinds = e075.kinds

SEEDS = [9, 10, 11, 12, 13, 14]
CTL = {s: os.path.join(ROOT, "experiments", "e081_drink" if s < 12 else "e092_yardstick", "results", "ladder",
                       f"c1225_life{s}_" + ("u0" if s < 12 else "ctl")) for s in SEEDS}
RUN = {s: os.path.join(HERE, "results", "batch", f"c1225_life{s}_ring2") for s in SEEDS}
COLS = [("kinds_at", "kinds at a census", "{:.2f}"), ("placed_at", "kinds kept to a place", "{:.2f}"),
        ("top_kind", "the largest kind's share", "{:.1%}"), ("top_share", "the largest line's share", "{:.1%}"),
        ("lines", "lines over 5%", "{:.0f}"), ("kills", "kills' share of intake", "{:.1%}"),
        ("no_room", "births with no room", "{:.1%}"), ("blocked", "moves blocked", "{:.1%}"),
        ("place_k", "sub-cells a child was placed at", "{:.2f}"),
        ("pop", "bodies", "{:.0f}"), ("travel", "travel of a grown body", "{:.1f}")]


def plain(pre):
    """A run whose censuses `tidy.py` compressed is read through a temporary copy: the census
    decompressed, every other file of the run linked beside it."""
    if os.path.exists(pre + "_agents.csv") or not os.path.exists(pre + "_agents.csv.zst"):
        return pre
    base = os.path.basename(pre)
    d = os.path.join(tempfile.gettempdir(), "e097_plain", base)
    os.makedirs(d, exist_ok=True)
    out = os.path.join(d, base)
    if not os.path.exists(out + "_agents.csv"):
        with open(out + "_agents.csv", "wb") as f:
            subprocess.run(["zstd", "-dc", pre + "_agents.csv.zst"], stdout=f, check=True)
    for path in glob.glob(pre + "_*"):
        name = os.path.join(d, os.path.basename(path))
        if not path.endswith(".zst") and not os.path.exists(name):
            os.symlink(os.path.abspath(path), name)
    return out


def log_of(pre):
    """The second half of the log: the jam, and how far out a child was placed (0 where the control's
    crate did not write the column)."""
    with open(pre + "_log.csv") as f:
        rows = list(csv.DictReader(f))
    half = [r for r in rows if int(r["step"]) >= int(rows[-1]["step"]) / 2]
    moves = sum(float(r["forward"]) + float(r["left"]) + float(r["right"]) for r in half)
    return {"blocked": sum(float(r["blocked"]) for r in half) / max(moves, 1),
            "place_k": st.mean(float(r["place_k"]) for r in half) if "place_k" in half[0] else float("nan"),
            "rows": len(half), "from": int(half[0]["step"]), "to": int(rows[-1]["step"])}


def read(label, seed, pre, prov):
    src = plain(pre)
    row, ks = e075.read_run(f"{label} seed{seed}", src)
    row.update(e092.lines_of(src))
    row.update(e092.jam(pre))
    log = log_of(pre)
    row.update({k: v for k, v in log.items() if k in ("blocked", "place_k")})
    row["seed"] = seed
    run = kinds.Run(f"{label} seed{seed}", src)
    p = kinds.provenance(run)
    prov.append({"reading": "batch", "run": f"{label} seed{seed}", "from": p["from"], "to": p["to"],
                 "items": p["censuses"], "thresholds": "kinds by birth form (e068); a place is not `shore`; "
                                                       f"the log's second half from {log['from']:,} ({log['rows']} rows)"})
    return row, ks


def main():
    out, per_kind, prov = {}, [], []
    for label, pres in (("control", CTL), ("ring2", RUN)):
        rows = []
        for seed in SEEDS:
            pre = pres[seed]
            if not os.path.exists(pre + "_row.csv"):
                print(f"{label} seed {seed}: no finished run at {pre}")
                continue
            row, ks = read(label, seed, pre, prov)
            rows.append(row)
            per_kind += [dict(k, run=label) for k in ks]
        out[label] = rows
    for label, rows in out.items():
        if not rows:
            continue
        print(f"\n{label}: {'measure':<32}" + "".join(f"{'seed %d' % r['seed']:>10}" for r in rows) + f"{'median':>10}{'spread':>10}")
        for k, lab, f in COLS:
            v = [r[k] for r in rows]
            print(f"{'':<9}{lab:<32}" + "".join(f"{f.format(r[k]):>10}" for r in rows)
                  + f"{f.format(st.median(v)):>10}{f.format(max(v) - min(v)):>10}")
    if len(out.get("control", [])) and len(out.get("ring2", [])):
        print(f"\n{'measure':<32}{'control':>12}{'ring2':>12}{'effect':>12}{'ctl spread':>12}")
        for k, lab, f in COLS:
            a = [r[k] for r in out["control"]]
            b = [r[k] for r in out["ring2"]]
            print(f"{lab:<32}{f.format(st.median(a)):>12}{f.format(st.median(b)):>12}"
                  f"{f.format(st.median(b) - st.median(a)):>12}{f.format(max(a) - min(a)):>12}")
    rows = out.get("control", []) + out.get("ring2", [])
    if rows:
        with open(os.path.join(HERE, "results", "batch.csv"), "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["run", "seed"] + [k for k, _, _ in COLS])
            w.writeheader()
            for label, rs in out.items():
                for r in rs:
                    w.writerow({"run": label, "seed": r["seed"], **{k: r[k] for k, _, _ in COLS}})
    if per_kind:
        with open(os.path.join(HERE, "results", "kinds.csv"), "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(per_kind[0]))
            w.writeheader()
            w.writerows(per_kind)
    print(f"\nprovenance: {prov_mod.write(HERE, 'batch', prov)}")


if __name__ == "__main__":
    main()
