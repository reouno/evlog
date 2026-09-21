"""How much two runs of one world agree: the measure of a replay (#112, e100).

A run of a world is a replay of it with a different seed of the bodies. Two things can agree or
differ between replays, and the project wants opposite answers for them:

- **the ways of living** - what is eaten, whether a body can break another, whether it stays or
  roams, where it lives. Agreement here is convergence: the same roles are filled every time.
- **the birth forms** - the bodies that fill those roles. Agreement here would be a world with one
  body in it; disagreement is what selection finding many answers looks like.

The real world answers the first "mostly yes" (eyes about forty times over, powered flight four,
C4 photosynthesis sixty) and the second "no". A world whose replays fill the same roles with
different bodies is convergent in function and contingent in content; a world whose replays differ
in the roles themselves has a space of ways larger than one run can exhaust, which is what
`vision.md` asks of history.

This reads the `kinds.csv` a sweep writes (one row a kind of a run: `run`, `kind`, `side`, `cells`)
and depends on no experiment.

    uv run python -m analysis.replay <kinds.csv> [...]
"""
import csv
import itertools
import statistics as st
import sys
from collections import defaultdict


def agreement(path):
    """The agreement between the runs in one `kinds.csv`."""
    ways, forms = defaultdict(set), defaultdict(set)
    for r in csv.DictReader(open(path)):
        ways[r["run"]].add(r["kind"])
        forms[r["run"]].add((r["side"], r["cells"]))
    runs = sorted(ways)
    if len(runs) < 2:
        raise ValueError(f"{path}: a replay needs two runs of one world, found {len(runs)}")
    every = set.intersection(*(ways[r] for r in runs))
    union = set.union(*(ways[r] for r in runs))
    seen = {w: sum(w in ways[r] for r in runs) for w in union}
    pairs = list(itertools.combinations(runs, 2))
    jac = lambda d: st.mean(len(d[a] & d[b]) / max(len(d[a] | d[b]), 1) for a, b in pairs)
    return {"runs": len(runs), "ways_seen": len(union), "ways_in_every_run": len(every),
            "ways_in_one_run": sum(v == 1 for v in seen.values()),
            "ways_agree": jac(ways), "forms_agree": jac(forms),
            "ways_a_run": st.mean(len(ways[r]) for r in runs)}


def main(paths):
    for p in paths:
        a = agreement(p)
        print(f"{p}: {a['runs']} runs, {a['ways_seen']} ways over all of them "
              f"({a['ways_a_run']:.1f} a run), {a['ways_in_every_run']} in every run, "
              f"{a['ways_in_one_run']} in one only")
        print(f"    ways agree {a['ways_agree']:.2f}   birth forms agree {a['forms_agree']:.3f}")


if __name__ == "__main__":
    main(sys.argv[1:])
