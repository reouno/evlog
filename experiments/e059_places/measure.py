"""One row of numbers per run of e059. Run from the repo root: `uv run python
experiments/e059_places/measure.py <glob of _log.csv>`.

Means are over the second half of the run. Diversity is #66's (experiments/e059_places/diversity.py
as imported here): kinds, kinds rarefied to a fixed draw, q1 and q2 over birth shapes, for all the
bodies and for the bodies born on the rich and on the thin land apart.
"""
import csv, glob, math, statistics, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from diversity import census, hill, rarefied, kind_of, KINDS

LOG = 10_000          # steps per log row
LIGHT = 0.01 * 16384  # the world's light per step at sun 1 (RES_GROWTH * cells)


def rows(path):
    return list(csv.DictReader(open(path)))


def half(d, col):
    n = len(d)
    v = [float(r[col]) for r in d[n // 2:]]
    return statistics.mean(v)


def agents(path, step):
    return [r for r in csv.DictReader(open(path)) if int(r["step"]) == step]


def mix(rs):
    """Mean share of each kind of block in the birth shape, and the mean birth size."""
    out = []
    for k in KINDS:
        tot = [sum(float(r["born_" + j]) for j in KINDS) for r in rs]
        out.append(statistics.mean(float(r["born_" + k]) / t for r, t in zip(rs, tot) if t > 0))
    return out, statistics.mean(float(r["born_size"]) for r in rs)


def div(rs, rarefy):
    from collections import Counter
    c = Counter()
    for r in rs:
        k = kind_of([int(float(r["born_" + j])) for j in KINDS])
        if k:
            c[k] += 1
    q = hill(c)
    return len(c), rarefied(c, m=rarefy), q[1], q[2]


def report(log_path, rarefy=120):
    d = rows(log_path)
    pre = log_path[:-len("_log.csv")]
    a_path = pre + "_agents.csv"
    step = int(d[-1]["step"])
    pop = half(d, "pop")
    broken = half(d, "cells_broken") / LOG
    floors = [float(r["pop"]) for r in d[len(d) // 2:]]
    name = os.path.basename(pre).split("_r64")[0] + "_" + os.path.basename(pre).split("_mix0.2")[1]
    print(f"\n== {name} ({step} steps)")
    print(f"bodies {pop:.0f}  kills/body {broken / pop:.4f}  blocked {half(d, 'blocked'):.3f}  "
          f"no_room {half(d, 'births_no_room'):.3f}  moved {half(d, 'moved'):.3f}  "
          f"floor {min(floors):.0f}  regrowth {half(d, 'regrowth'):.1f}  "
          f"barren {half(d, 'barren'):.2f} ({half(d, 'barren') / (LIGHT * SUN):.1%} of the light)")
    if "rich" in d[0]:
        print(f"rich land {half(d, 'rich'):.1%}  plant rich/thin {half(d, 'plant_rich'):.2f}/"
              f"{half(d, 'plant_thin'):.2f}  bodies on rich {half(d, 'pop_rich'):.1%}  "
              f"hunger rich/thin {half(d, 'hunger_rich'):.4f}/{half(d, 'hunger_thin'):.4f}")
    if not os.path.exists(a_path):
        return
    rs = agents(a_path, step)
    if not rs:
        return
    tr = sorted(float(r["travel"]) for r in rs)
    bins = [(0, 200), (200, 500), (500, 1000), (1000, 10 ** 9)]
    by_age = []
    for lo, hi in bins:
        v = sorted(float(r["travel"]) for r in rs if lo <= int(r["age"]) < hi)
        by_age.append(f"{statistics.median(v):.1f}" if v else "-")
    print(f"travel median {statistics.median(tr):.2f}  by age {' / '.join(by_age)}  "
          f"p90 {tr[int(0.9 * len(tr))]:.1f}")
    if "_sigma0_" not in pre:
        sg = float(pre.split("_sigma")[1].split("_")[0])
        ar = int(pre.split("_patch")[1].split("_")[0])
        land(pre, sg, ar)
    groups = [("all", rs)]
    if "born_rich" in rs[0]:
        groups += [("born rich", [r for r in rs if r["born_rich"] == "1"]),
                   ("born thin", [r for r in rs if r["born_rich"] == "0"])]
    for label, g in groups:
        if len(g) < 20:
            print(f"{label:10s} n={len(g)} (too few)")
            continue
        k, rar, q1, q2 = div(g, rarefy)
        m, size = mix(g)
        rar_txt = f"{rar:5.1f}" if rar is not None else "    -"
        print(f"{label:10s} n={len(g):4d}  kinds {k:3d}  rarefied {rar_txt}  q1 {q1:5.2f}  q2 {q2:5.2f}  "
              f"size {size:5.1f}  mix " + " ".join(f"{x:.2f}" for x in m))


def regions(sigma, area, centers, sun=0.2, w=128, h=128):
    """Rebuild the regrowth field from the patch centres and measure the rich land: its share of
    the world, the connected regions it falls into (4-neighbour, on the torus) and their sizes.
    e054's lesson was that patches merge into land a body is born inside."""
    import math
    grow = [0.0] * (w * h)
    peak = 0.01 * sun * area / (2 * math.pi * sigma * sigma)
    r = math.ceil(3 * sigma)
    for (cx, cy, _sg) in centers:
        for dy in range(-r, r + 1):
            for dx in range(-r, r + 1):
                x, y = (cx + dx) % w, (cy + dy) % h
                grow[y * w + x] += peak * math.exp(-(dx * dx + dy * dy) / (2 * sigma * sigma))
    rich = [g >= 0.01 * sun for g in grow]
    seen = [False] * (w * h)
    sizes = []
    for c in range(w * h):
        if rich[c] and not seen[c]:
            stack, n = [c], 0
            seen[c] = True
            while stack:
                i = stack.pop()
                n += 1
                x, y = i % w, i // w
                for nx, ny in (((x + 1) % w, y), ((x - 1) % w, y), (x, (y + 1) % h), (x, (y - 1) % h)):
                    j = ny * w + nx
                    if rich[j] and not seen[j]:
                        seen[j] = True
                        stack.append(j)
            sizes.append(n)
    sizes.sort()
    return sum(rich) / (w * h), len(sizes), sizes[-1] if sizes else 0, statistics.median(sizes) if sizes else 0


def land(pre, sigma, area):
    """The rich land of the last frame of a run's long.jsonl."""
    import json
    path = pre + "_long.jsonl"
    if not os.path.exists(path):
        return
    last = None
    for line in open(path):
        if '"patches"' in line:
            last = line
    if last is None:
        return
    f = json.loads(last)
    share, n, big, med = regions(sigma, area, f["patches"])
    print(f"rich land (rebuilt from {len(f['patches'])} centres at step {f.get('step')}): {share:.1%} of the world, "
          f"{n} connected regions, largest {big} cells ({math.sqrt(big):.0f} across), median {med:.0f}")


if __name__ == "__main__":
    SUN = float(os.environ.get("SUN", "0.2"))
    for p in sorted(x for pat in sys.argv[1:] for x in glob.glob(pat)):
        report(p)
