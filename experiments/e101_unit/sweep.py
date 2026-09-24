#!/usr/bin/env python3
"""e101's batch (#113): the body's water alone, against the control ladder and e100's full set.

Run from the repo root: `uv run python experiments/e101_unit/sweep.py` (a few minutes).

Eighteen runs of one world on the same six seeds: the control ladder (e081's seeds 9-11 and e092's
12-14, e092's own reading), e100's set (`unit` with the crown's four laws) and this experiment's six
(`unit` 9.4 alone). For each it reads, with e075's `read_run` (e068's census by birth form), kinds at a
census, kinds kept to a place, the largest kind's and the largest line's share, the kills' share,
bodies, travel and the crowd's jam; then the median and spread of each over six seeds, and how much
the six replays of each world agree (`analysis/replay.py`).

Writes `results/batch.csv` (a row a run), `results/kinds_<world>.csv` (a row a kind of a run, one file
a world, so a replay is read within one world) and the `batch` rows of `results/provenance.csv`.
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
sys.path.insert(0, ROOT)


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


from analysis import replay  # noqa: E402

prov_mod = load("e101_prov", os.path.join(HERE, "prov.py"))
e075 = load("e075_sweep", os.path.join(ROOT, "experiments", "e075_hunt", "sweep.py"))
e092 = load("e092_sweep", os.path.join(ROOT, "experiments", "e092_yardstick", "sweep.py"))
e097 = load("e097_sweep", os.path.join(ROOT, "experiments", "e097_room", "sweep.py"))
kinds = e075.kinds

SEEDS = [9, 10, 11, 12, 13, 14]
WORLDS = {
    "control": dict(e092.RUNS),
    "e100": {s: os.path.join(ROOT, "experiments", "e100_base", "results", "ladder", f"c1225_life{s}_ctl")
             for s in SEEDS},
    "unit": {s: os.path.join(HERE, "results", "ladder", f"c1225_life{s}_unit") for s in SEEDS},
}
COLS = [("kinds_at", "kinds at a census", "{:.2f}"), ("placed_at", "kinds kept to a place", "{:.2f}"),
        ("top_kind", "the largest kind's share", "{:.1%}"), ("top_share", "the largest line's share", "{:.1%}"),
        ("lines", "lines over 5%", "{:.0f}"), ("kills", "kills' share of intake", "{:.1%}"),
        ("no_room", "births with no room", "{:.1%}"), ("blocked", "moves blocked", "{:.1%}"),
        ("pop", "bodies", "{:.0f}"), ("travel", "travel of a grown body", "{:.1f}")]
REPLAY = [("held_a_run", "ways holding 5%, a run", "{:.1f}"), ("held_agree", "  they agree", "{:.2f}"),
          ("shares_agree", "  their shares agree", "{:.2f}"), ("same_largest_way", "the same largest way", "{}/6"),
          ("forms_agree", "the birth forms agree", "{:.3f}")]


def plain(world, pre):
    """A run whose census `tidy.py` compressed is read through a temporary copy, one directory a world:
    e092's and e100's runs share their names, so e097's copy (named by the run alone) would read one
    world's census for the other's."""
    if os.path.exists(pre + "_agents.csv") or not os.path.exists(pre + "_agents.csv.zst"):
        return pre
    base = os.path.basename(pre)
    d = os.path.join(tempfile.gettempdir(), "e101_plain", world)
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


def read(world, seed, pre, prov):
    src = plain(world, pre)
    row, ks = e075.read_run(f"seed{seed}", src)
    row.update(e092.lines_of(src))
    row.update(e092.jam(pre))
    log = e097.log_of(pre)
    row["blocked"] = log["blocked"]
    row["seed"] = seed
    p = kinds.provenance(kinds.Run(f"{world} seed{seed}", src))
    prov.append({"reading": "batch", "run": f"{world} seed{seed}", "from": p["from"], "to": p["to"],
                 "items": p["censuses"], "thresholds": "kinds by birth form (e068); a place is not `shore`; "
                 f"a line holds {e092.LINE:.0%} of the land's bodies; the log's second half from "
                 f"{log['from']:,} ({log['rows']} rows); a replay's way holds {replay.LINE:.0%}"})
    return row, ks


def main():
    out, agree, prov = {}, {}, []
    for world, pres in WORLDS.items():
        rows, per_kind = [], []
        for seed in SEEDS:
            pre = pres[seed]
            if not os.path.exists(pre + "_row.csv"):
                print(f"{world} seed {seed}: no finished run at {pre}")
                continue
            row, ks = read(world, seed, pre, prov)
            rows.append(row)
            per_kind += ks
        out[world] = rows
        if per_kind:
            path = os.path.join(HERE, "results", f"kinds_{world}.csv")
            with open(path, "w", newline="") as f:
                w = csv.DictWriter(f, fieldnames=list(per_kind[0]), lineterminator="\n")
                w.writeheader()
                w.writerows(per_kind)
            if len(rows) > 1:
                agree[world] = replay.agreement(path)
    for world, rows in out.items():
        if not rows:
            continue
        print(f"\n{world}: {'measure':<30}" + "".join(f"{'seed %d' % r['seed']:>9}" for r in rows)
              + f"{'median':>9}{'spread':>9}")
        for k, lab, f in COLS:
            v = [r[k] for r in rows]
            print(f"{'':<9}{lab:<30}" + "".join(f"{f.format(r[k]):>9}" for r in rows)
                  + f"{f.format(st.median(v)):>9}{f.format(max(v) - min(v)):>9}")
    have = [w for w in WORLDS if out.get(w)]
    print(f"\n{'median (spread)':<30}" + "".join(f"{w:>18}" for w in have))
    for k, lab, f in COLS:
        cell = lambda v: f"{f.format(st.median(v))} ({f.format(max(v) - min(v))})"
        print(f"{lab:<30}" + "".join(f"{cell([r[k] for r in out[w]]):>18}" for w in have))
    print(f"\n{'replays agree':<30}" + "".join(f"{w:>18}" for w in agree))
    for k, lab, f in REPLAY:
        print(f"{lab:<30}" + "".join(f"{f.format(agree[w][k]):>18}" for w in agree))
    with open(os.path.join(HERE, "results", "batch.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["world", "seed"] + [k for k, _, _ in COLS], lineterminator="\n")
        w.writeheader()
        for world, rs in out.items():
            for r in rs:
                w.writerow({"world": world, "seed": r["seed"], **{k: r[k] for k, _, _ in COLS}})
    with open(os.path.join(HERE, "results", "replay.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["world"] + list(next(iter(agree.values()))), lineterminator="\n")
        w.writeheader()
        w.writerows({"world": k, **v} for k, v in agree.items())
    print(f"\nprovenance: {prov_mod.write(HERE, 'batch', prov)}")


if __name__ == "__main__":
    main()
