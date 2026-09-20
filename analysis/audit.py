"""Is a run's census a true count of its world? Five checks, meant to be run after every batch.

`uv run python analysis/audit.py <prefix> [<prefix> ...]` - a prefix is a run's path without
`_agents.csv`. A directory is read as every run in it. It prints one line a run and exits non-zero if
any check fails, so a batch script can refuse to report on a broken run.

The checks are about the census being what it claims - every living body, once, written whole - not
about the world being interesting:

1. **every body, and only living ones**: the rows at a census equal `pop` in the log at that step;
2. **once each**: no id appears twice in one census;
3. **whole**: `size` equals the blocks the `cells` grid holds and the sum of the per-kind counts, and
   `born_size` equals the sum of the birth counts;
4. **the grid fits its side**: `len(cells) == side * side`;
5. **named**: no body is left in lineage 0 (undetected) at a census the lineages were detected on.
"""
import csv
import os
import subprocess
import sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from analysis import schema  # noqa: E402


def rows_of(path):
    """A census, from the file or from what `tidy.py` compressed."""
    if os.path.exists(path):
        with open(path) as f:
            return list(csv.DictReader(f))
    text = subprocess.run(["zstd", "-dc", path + ".zst"], capture_output=True, text=True).stdout
    return list(csv.DictReader(text.splitlines()))


def audit(pre):
    """The problems found with one run, as a list of strings; empty is a clean run."""
    rows = rows_of(pre + "_agents.csv")
    if not rows:
        return [f"no census at {pre}_agents.csv"]
    header = list(rows[0])
    schema.check(header, os.path.basename(pre))
    born = schema.born(header)
    now = schema.blocks(header)
    by_step = defaultdict(list)
    for r in rows:
        by_step[int(r["step"])].append(r)
    bad = []

    log = {}
    if os.path.exists(pre + "_log.csv"):
        with open(pre + "_log.csv") as f:
            log = {int(r["step"]): int(float(r["pop"])) for r in csv.DictReader(f)}
    off = [(s, len(rs), log[s]) for s, rs in by_step.items() if s in log and len(rs) != log[s]]
    if off:
        bad.append(f"{len(off)} censuses do not hold the log's bodies, first {off[0]}")
    if log and not any(s in log for s in by_step):
        bad.append("no census step is in the log")

    twice = [s for s, rs in by_step.items() if len({r["id"] for r in rs}) != len(rs)]
    if twice:
        bad.append(f"{len(twice)} censuses hold a body twice, first at {min(twice)}")

    def count(r, keys):
        return sum(int(r[k]) for k in keys if k in r)

    cells = [r for r in rows if "cells" in r and int(r["size"]) != sum(c != "0" for c in r["cells"])]
    kinds = [r for r in rows if now and int(r["size"]) != count(r, now)]
    at_birth = [r for r in rows if born and int(r["born_size"]) != count(r, born)]
    side = [r for r in rows if "cells" in r and len(r["cells"]) != int(r["side"]) ** 2]
    for what, got in (("size against its cells", cells), ("size against its blocks", kinds),
                      ("born_size against its birth blocks", at_birth), ("the grid against its side", side)):
        if got:
            bad.append(f"{len(got)} bodies do not add up: {what} (first id {got[0]['id']})")

    if "lineage" in header:
        none = Counter(r["step"] for r in rows if r["lineage"] == "0")
        if none:
            bad.append(f"{sum(none.values())} bodies in no lineage, over {len(none)} censuses")
    return bad


def prefixes(args):
    out = []
    for a in args:
        if os.path.isdir(a):
            out += sorted({os.path.join(a, f[: -len("_agents.csv")]) for f in os.listdir(a)
                           if f.endswith("_agents.csv")} |
                          {os.path.join(a, f[: -len("_agents.csv.zst")]) for f in os.listdir(a)
                           if f.endswith("_agents.csv.zst")})
        else:
            out.append(a[: -len("_agents.csv")] if a.endswith("_agents.csv") else a)
    return out


def main():
    pres = prefixes(sys.argv[1:])
    if not pres:
        print(__doc__.strip().splitlines()[2])
        return 2
    worst = 0
    for pre in pres:
        bad = audit(pre)
        print(f"{'FAIL' if bad else 'ok  '} {os.path.basename(pre)}" + ("" if not bad else ": " + "; ".join(bad)))
        worst |= bool(bad)
    return worst


if __name__ == "__main__":
    sys.exit(main())
