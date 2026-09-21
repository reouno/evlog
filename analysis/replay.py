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

**The coarse reading saturates and must not be used alone.** A way's label is a diet (4), a tooth (2),
roaming (2) and a medium (4): 64 boxes in all, of which about 43 are filled in every run, so any two
runs of any world overlap by 0.9 whatever they do. What says something is the agreement over the ways
that actually hold e060's 5% of the grown bodies, the similarity of their shares, and whether the
largest way is the same one.

This reads the `kinds.csv` a sweep writes (one row a kind of a run: `run`, `kind`, `share`, `side`,
`cells`) and depends on no experiment.

    uv run python -m analysis.replay <kinds.csv> [...]
"""
import csv
import itertools
import statistics as st
import sys
from collections import defaultdict


LINE = 0.05  # e060's share of the grown bodies at which a way is a kind


def agreement(path, line=LINE):
    """The agreement between the runs in one `kinds.csv`."""
    share, forms = defaultdict(dict), defaultdict(set)
    for r in csv.DictReader(open(path)):
        share[r["run"]][r["kind"]] = float(r["share"])
        forms[r["run"]].add((r["side"], r["cells"]))
    runs = sorted(share)
    if len(runs) < 2:
        raise ValueError(f"{path}: a replay needs two runs of one world, found {len(runs)}")
    seen = {r: set(d) for r, d in share.items()}
    held = {r: {w for w, v in d.items() if v >= line} for r, d in share.items()}
    union = sorted(set().union(*seen.values()))
    pairs = list(itertools.combinations(runs, 2))
    jac = lambda d: st.mean(len(d[a] & d[b]) / max(len(d[a] | d[b]), 1) for a, b in pairs)

    def bray(a, b):
        """How alike two runs' shares of the ways are (1: the same world twice)."""
        va = [share[a].get(w, 0.0) for w in union]
        vb = [share[b].get(w, 0.0) for w in union]
        den = (sum(va) + sum(vb)) / 2
        return sum(min(x, y) for x, y in zip(va, vb)) / den if den else 0.0

    top = {r: max(d, key=d.get) for r, d in share.items()}
    same_top = max(sum(1 for r in runs if top[r] == t) for t in set(top.values()))
    return {"runs": len(runs), "ways_seen": len(union),
            "ways_a_run": st.mean(len(seen[r]) for r in runs),
            "ways_agree": jac(seen), "held_a_run": st.mean(len(held[r]) for r in runs),
            "held_agree": jac(held), "shares_agree": st.mean(bray(a, b) for a, b in pairs),
            "same_largest_way": same_top, "forms_agree": jac(forms)}


def main(paths):
    for p in paths:
        a = agreement(p)
        print(f"{p}: {a['runs']} runs; {a['ways_seen']} of the label's 64 boxes seen, "
              f"{a['ways_a_run']:.1f} a run, {a['held_a_run']:.1f} of them holding 5%")
        print(f"    every way seen agrees {a['ways_agree']:.2f} (saturated - read the next three)")
        print(f"    the ways holding 5% agree {a['held_agree']:.2f}; their shares {a['shares_agree']:.2f}; "
              f"the largest way is the same in {a['same_largest_way']}/{a['runs']} runs")
        print(f"    the birth forms agree {a['forms_agree']:.3f}")


if __name__ == "__main__":
    main(sys.argv[1:])
