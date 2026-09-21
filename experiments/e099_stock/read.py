#!/usr/bin/env python3
"""e099 (#112): the rejected laws re-read by today's measure. No runs - this reads censuses on disk.

Run from the repo root: `uv run python experiments/e099_stock/read.py [group ...]`.

Every law of stage C that was not kept is read again with the classifier every reading since e068 goes
through (`analysis/`, `e060_census`, `e068_kinds`), against its own experiment's control, over the
second half of each run's censuses. What each verdict then used is in the table of the README; what
this reads is written to `results/stock.csv` and `results/provenance.csv`.

The line: the control ladder of six seeds of one world spreads 1.02 kinds at a census and 1.24 kinds
kept to a place (e092). A difference inside that spread was never readable, whatever the verdict said.
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


e075 = load("e075_sweep", os.path.join(ROOT, "experiments", "e075_hunt", "sweep.py"))
kinds = e075.kinds

PROV = []
SPREAD = {"kinds_at": 1.02, "placed_at": 1.24}  # e092's six seeds of one world
E081 = os.path.join(ROOT, "experiments", "e081_drink", "results", "ladder")
E092 = os.path.join(ROOT, "experiments", "e092_yardstick", "results", "ladder")


def p(*parts):
    return os.path.join(ROOT, "experiments", *parts)


# (group, law, parameter in today's crate, [(seed, control prefix, run prefix)])
GROUPS = [
    ("e069", "life history from the genome", "history=1",
     [(s, p("e069_history", "results", f"c1225_life{s}_" + ("check" if s == 9 else "constants")),
       p("e069_history", "results", f"c1225_life{s}_history")) for s in (9, 10, 11)]),
    ("e078", "the crown's shade (heat 2.5, dry 2.5)", "shade_heat=2.5 shade_dry=2.5",
     [(9, p("e078_shade", "results", "search", "c1225_life9_h0d0"),
       p("e078_shade", "results", "search", "c1225_life9_h2.5d2.5"))]),
    ("e078b", "the crown's shade (heat 5, dry 5)", "shade_heat=5 shade_dry=5",
     [(9, p("e078_shade", "results", "search", "c1225_life9_h0d0"),
       p("e078_shade", "results", "search", "c1225_life9_h5d5"))]),
    ("e079", "the crown's ground and wood's rest (S1+S2), with no crown_cool", "crown_wet=1 wood_rest=1",
     [(9, p("e078_shade", "results", "search", "c1225_life9_h0d0"),
       p("e080_cool", "results", "search", "c1225_life9_c0"))]),
    ("e080", "the crown's cooling (S3) over S1+S2", "crown_cool=0.1",
     [(9, p("e080_cool", "results", "search", "c1225_life9_c0"),
       p("e080_cool", "results", "search", "c1225_life9_c0.1"))]),
    ("e081", "the body's water part of the land's (W1+W2)", "unit=9.4",
     [(s, os.path.join(E081, f"c1225_life{s}_u0"), os.path.join(E081, f"c1225_life{s}_u9.4"))
      for s in (9, 10, 11)]),
    ("e082", "fresh water (0.2) under W1", "fresh=0.2",
     [(s, os.path.join(E081, f"c1225_life{s}_u9.4"),
       p("e082_fresh", "results", "ladder", f"c1225_life{s}_u9.4_f0.2")) for s in (9, 10, 11)]),
    ("e087", "the year and torpor (Y+Q)", "not carried",
     [(s, os.path.join(E081, f"c1225_life{s}_u0"),
       p("e087_torpor", "results", "batch", f"c1225_life{s}_yq")) for s in (9, 10, 11)]),
]


def plain(pre):
    """A run's files where the reader can open them: `tidy.py` compresses the censuses, so the
    compressed ones are unpacked into a scratch directory and the rest are linked beside them."""
    if os.path.exists(pre + "_agents.csv"):
        return pre
    d = os.path.join(tempfile.gettempdir(), "e099_plain")
    os.makedirs(d, exist_ok=True)
    out = os.path.join(d, os.path.basename(pre))
    for f in glob.glob(pre + "_*"):
        tail = os.path.basename(f)[len(os.path.basename(pre)):]
        if tail.endswith(".zst"):
            dst = out + tail[:-4]
            if not os.path.exists(dst):
                with open(dst, "wb") as fh:
                    subprocess.run(["zstd", "-dc", f], stdout=fh, check=True)
        elif not os.path.exists(out + tail):
            os.symlink(os.path.abspath(f), out + tail)
    return out


def read(name, pre):
    """Kinds at a census, kinds kept to a place and the largest kind's share, read exactly as e068
    reads them. e075's `read_run` is not used: it also reads columns (`wood`) that the censuses of
    e069, from before e072's set B, do not hold."""
    run = kinds.Run(name, plain(pre))
    unit = run.forms()
    ways = kinds.by_group(run, unit, run.does())
    tallies = run.tally(unit, ways)
    per, _ = kinds.kinds(tallies)
    share = []
    for s, c in tallies.items():
        total = max(sum(c.values()), 1)
        share.append(max((v for w, v in c.items() if w in per[s]), default=0) / total)
    PROV.append(kinds.provenance(run))
    return {"kinds_at": kinds.mean_count(per),
            "placed_at": st.mean(sum(w[3] != "shore" for w in ws) for ws in per.values()),
            "top_kind": st.mean(share)}


def main():
    want = sys.argv[1:]
    out = []
    for group, law, param, pairs in GROUPS:
        if want and group not in want:
            continue
        for seed, ctl, run in pairs:
            c = read(f"{group}-ctl-{seed}", ctl)
            r = read(f"{group}-run-{seed}", run)
            out.append({"group": group, "law": law, "param": param, "seed": seed,
                        "kinds_ctl": c["kinds_at"], "kinds_run": r["kinds_at"],
                        "placed_ctl": c["placed_at"], "placed_at": r["placed_at"],
                        "top_ctl": c["top_kind"], "top_run": r["top_kind"]})
            d = out[-1]
            print(f"{group:6s} seed {seed}: kinds {d['kinds_ctl']:.2f} -> {d['kinds_run']:.2f} "
                  f"({d['kinds_run'] - d['kinds_ctl']:+.2f}), placed {d['placed_ctl']:.2f} -> "
                  f"{d['placed_at']:.2f} ({d['placed_at'] - d['placed_ctl']:+.2f})", flush=True)
    os.makedirs(os.path.join(HERE, "results"), exist_ok=True)
    path = os.path.join(HERE, "results", "stock.csv")
    old = list(csv.DictReader(open(path))) if os.path.exists(path) and want else []
    keep = [r for r in old if r["group"] not in want]
    with open(path, "w", newline="\n") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0].keys()), lineterminator="\n")
        w.writeheader()
        w.writerows(keep + out)
    with open(os.path.join(HERE, "results", "provenance.csv"), "w", newline="\n") as f:
        w = csv.DictWriter(f, fieldnames=list(PROV[0].keys()), lineterminator="\n")
        w.writeheader()
        w.writerows(PROV)
    print(f"wrote {path}; the spread that reads any of it: {SPREAD}")


if __name__ == "__main__":
    main()
