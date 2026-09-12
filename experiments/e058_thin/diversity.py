"""Diversity of the living bodies: the long tail counted, not the podium (#66).

Run from the repo root. Import `census`, `hill` and `rarefied` from an experiment's report.py;
this file moves to a shared place once a few experiments have used it.

A body's kind is where it falls on a grid over morphospace: its size class (blocks, by doubling)
and the mix of its blocks (the share of each of the four kinds, rounded to `BIN` parts). Every
living body is counted, however rare its kind - no share threshold.

Reported as Hill numbers: q0 is how many kinds there are, q1 = exp(Shannon) the effective number
of common kinds, q2 = 1/Simpson the effective number of abundant kinds. A real ecosystem reads
high q0 and much lower q2: one or two abundant kinds and a long tail.

q0 grows with how many bodies you looked at, so worlds of different population are compared by
rarefaction: the mean number of kinds in a random draw of RAREFY bodies.
"""
import csv, math, random
from collections import Counter

KINDS = ["hard", "muscle", "sensor", "digestive"]
BIN = 4          # the mix is rounded to quarters
SIZE_EDGES = [8, 16, 32, 64]
RAREFY = 200     # bodies per draw when richness is compared across worlds
DRAWS = 200


def kind_of(counts):
    n = sum(counts)
    if n <= 0:
        return None
    return (sum(n >= e for e in SIZE_EDGES), tuple(round(c / n * BIN) for c in counts))


def census(path, step=100_000, born=True):
    """Counter of kinds among the bodies alive at `step`. `born` reads the shape the body was
    built with (e058's columns) rather than the one wear and teeth have left it."""
    rows = [r for r in csv.DictReader(open(path)) if int(r["step"]) == step]
    pre = "born_" if born and rows and "born_hard" in rows[0] else ""
    c = Counter()
    for r in rows:
        k = kind_of([float(r[pre + x]) for x in KINDS])
        if k:
            c[k] += 1
    return c, (pre == "born_")


def hill(c):
    n = sum(c.values())
    p = [v / n for v in c.values()]
    return len(c), math.exp(-sum(x * math.log(x) for x in p)), 1.0 / sum(x * x for x in p)


def rarefied(c, m=RAREFY, draws=DRAWS, seed=1):
    """The mean number of kinds in a random draw of m bodies (None if there are fewer than m)."""
    pool = [k for k, v in c.items() for _ in range(v)]
    if len(pool) < m:
        return None
    rng = random.Random(seed)
    return sum(len(set(rng.sample(pool, m))) for _ in range(draws)) / draws


def line(label, path, step=100_000):
    c, was_born = census(path, step)
    if not c:
        return None
    q0, q1, q2 = hill(c)
    n = sum(c.values())
    r = rarefied(c)
    top = c.most_common(1)[0][1] / n
    print(f"{label:26s} n {n:5d} | kinds {q0:4d} (rarefied {('%.1f' % r) if r else '   -':>6s})  "
          f"q1 {q1:6.2f}  q2 {q2:6.2f} | biggest kind {top:5.1%}{'' if was_born else '  [current shape]'}")
    return q0, r, q1, q2
