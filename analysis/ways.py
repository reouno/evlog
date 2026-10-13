"""Groups of bodies by how they live: the open measure for bodies (#119, the new world's `_bodies.csv`).

Nothing is counted in boxes chosen before a run (the old world's label had 64, #115). A row of a body census is
one genotype with the bodies that carry it. It is described in blocks, each a thing `vision.md` asks of a way of
living, each with a distance in its own unit and a cut of its own:

- `diet`: the shares of what its bodies have eaten, one a food. Distance: the share of the diet that differs.
- `place`: the shares of its animals in each medium or layer. Distance: the share that lives elsewhere.
- `size`: its adult mass. Distance: decades apart.
- `range`: the km its bodies walk a year. Distance: decades apart.
- `make`: the shares of its tissue in each function. Distance: the share that differs.

Two genotypes live one way when they are within the cut in every block: their distance is the largest of the
blocks' distances, each over its cut. Groups come from the leader algorithm of `groups.py`: heaviest first, a
genotype joins the nearest leader within 1, or founds a group. The foods and the places are read off the census's
own header (`ate_<food>`, `at_<place>`), so a law that adds one adds a dimension and rewrites no line here; any
other column no reader has classified stops the reading (`CLAUDE.md`, Measuring).

Read beside the number of groups: the number each block gives alone (which freedoms are used), the matter in
groups an earlier census of the run has no match for (change), the matter two replays hold in matching groups
(history), and how far the groups are held by place (a table of matter by genotype and place, e.g. an island).

    from analysis.ways import describe, group, read, matched, changed, held, provenance
"""
import math

import numpy as np

from analysis.groups import hill, masses

# block -> the distance within which two genotypes are alike in it
# (a census is a snapshot of few bodies: a genotype lives elsewhere when most of its animals do)
CUTS = {"diet": 0.25, "place": 0.5, "size": 1.0, "range": 1.0, "make": 0.25}

MAKE = ["frame", "muscle", "gut", "nerve", "fat", "glue"]
RANGE_FLOOR = 1.0  # km a year: under it a body stays
EATEN_FLOOR = 0.0  # a genotype whose bodies have eaten nothing has no diet yet and is not grouped

# census columns read, and those carried but not grouped on
READ = {"matter", "adult_mass", "travel_km_yr", "sea", "born", "id", *MAKE}
CARRIED = {
    "year", "parent", "root", "genes", "bodies", "animals", "mass", "egg", "clutch", "maturity", "t_opt", "breadth",
    "tolerance", "n_keys", "keys", "ckey", "cells", "nv", "a", "b", "cmp", "frame_tough", "density", "legs", "bite",
    "mouth", "eye", "glue_front", "hard_front", "hard_back", "hard_flank", "tip_front", "tip_back", "tip_flank",
    "ext_x", "ext_y", "ext_z", "v_top", "reach", "from_birth_km", "kills",
    "pull_one", "pull_size", "pull_alike", "pull_fat", "pull_near", "pull_coming",
    "press_one", "press_size", "press_alike", "press_fat", "press_near", "press_coming",
}


def foods(columns):
    """The foods of a census, in its order."""
    return [c for c in columns if c.startswith("ate_")]


def places(columns):
    """The places of a census, in its order: `at_<place>` columns, or the sea and the land from `sea`."""
    return [c for c in columns if c.startswith("at_")]


def check(columns):
    """Fail loudly on a census column nobody has classified."""
    unknown = set(columns) - READ - CARRIED - set(foods(columns)) - set(places(columns))
    if unknown:
        raise SystemExit(f"ways.py: body census columns no reader classifies: {sorted(unknown)}")


def describe(rows):
    """Each block's matrix and each row's matter, for the rows that have a diet; and the matter left unread."""
    rows = list(rows)
    if not rows:
        return {k: np.zeros((0, 1)) for k in CUTS}, np.zeros(0), [], 0.0
    cols = list(rows[0].keys())
    check(cols)
    fs, ps = foods(cols), places(cols)
    kept, unread = [], 0.0
    for r in rows:
        if sum(float(r[f]) for f in fs) > EATEN_FLOOR:
            kept.append(r)
        else:
            unread += float(r["matter"])
    n = len(kept)
    d = {
        "diet": np.zeros((n, len(fs))),
        "place": np.zeros((n, len(ps) if ps else 2)),
        "size": np.zeros((n, 1)),
        "range": np.zeros((n, 1)),
        "make": np.zeros((n, len(MAKE))),
    }
    w = np.zeros(n)
    for i, r in enumerate(kept):
        w[i] = float(r["matter"])
        v = np.array([float(r[f]) for f in fs])
        d["diet"][i] = v / v.sum()
        if ps:
            v = np.array([float(r[p]) for p in ps])
            d["place"][i] = v / max(v.sum(), 1e-30)
        else:
            d["place"][i] = [float(r["sea"]), 1.0 - float(r["sea"])]
        d["size"][i, 0] = math.log10(float(r["adult_mass"]))
        d["range"][i, 0] = math.log10(max(float(r["travel_km_yr"]), RANGE_FLOOR))
        v = np.array([float(r[m]) for m in MAKE])
        d["make"][i] = v / max(v.sum(), 1e-30)
    return d, w, kept, unread


def _apart(d, i, js, blocks):
    """The distance of row `i` from the rows `js`: the largest of the blocks' distances, each over its cut."""
    out = np.zeros(len(js))
    for k in blocks:
        diff = np.abs(d[k][js] - d[k][i]).sum(axis=1)
        if k in ("diet", "place", "make"):
            diff = diff / 2.0  # shares: half the L1 distance is the share that differs
        out = np.maximum(out, diff / CUTS[k])
    return out


def group(d, w, blocks=None):
    """Leader grouping, heaviest first. Returns each row's group (the index of its leader's row)."""
    blocks = list(CUTS) if blocks is None else blocks
    order = np.argsort(-w, kind="stable")
    leaders = []
    g = np.empty(len(w), dtype=int)
    for i in order:
        if leaders:
            a = _apart(d, i, leaders, blocks)
            j = int(np.argmin(a))
            if a[j] <= 1.0:
                g[i] = leaders[j]
                continue
        leaders.append(i)
        g[i] = i
    return g


def read(rows):
    """A census's reading: the groups, their effective number, and the number each block gives alone."""
    d, w, kept, unread = describe(rows)
    out = {"genotypes": len(kept), "unread_share": float(unread / max(unread + w.sum(), 1e-30))}
    if not len(w):
        return {**out, "groups": 0, "groups_hill": 0.0, "top_group_share": 0.0, **{f"hill_{k}": 0.0 for k in CUTS}}, (d, w, kept, np.zeros(0, dtype=int))
    g = group(d, w)
    gm = masses(g, w)
    out.update(groups=len(gm), groups_hill=hill(gm.values()), top_group_share=float(max(gm.values()) / w.sum()))
    for k in CUTS:
        out[f"hill_{k}"] = hill(masses(group(d, w, [k]), w).values())
    return out, (d, w, kept, g)


def matched(a, b):
    """History: the share of each replay's matter in groups whose leader has a match in the other within the cut.
    `a` and `b` are what `read` returns second. The two censuses must hold the same foods and places."""
    (da, wa, _, ga), (db, wb, _, gb) = a, b
    la, lb = sorted(set(int(v) for v in ga)), sorted(set(int(v) for v in gb))
    gma, gmb = masses(ga, wa), masses(gb, wb)
    both = {k: np.vstack([da[k][la], db[k][lb]]) for k in CUTS}
    na = len(la)
    ma = sum(gma[gi] for i, gi in enumerate(la) if _apart(both, i, list(range(na, na + len(lb))), list(CUTS)).min() <= 1.0)
    mb = sum(gmb[gi] for j, gi in enumerate(lb) if _apart(both, na + j, list(range(na)), list(CUTS)).min() <= 1.0)
    return float(ma / wa.sum()), float(mb / wb.sum())


def changed(now, then):
    """Change: the share of a census's matter in groups with no match in an earlier census of the same run. A
    body's genotypes turn over in a few years whatever its way of living, so a group's age is not read from the
    year its leader was born (as a producer's is, `groups.founded`) but from whether its way was there before."""
    return 1.0 - matched(now, then)[0]


def held(table, group_of):
    """How far the groups are held by place: the normalised mutual information of group and place over matter.
    `table`: (genotype id, place, matter) triples; `group_of`: a genotype id's group. 0: every place holds the
    same mix; 1: each group has its own places."""
    joint = {}
    for gid, place, m in table:
        if gid in group_of and m > 0:
            key = (group_of[gid], place)
            joint[key] = joint.get(key, 0.0) + m
    if not joint:
        return 0.0
    gs = sorted({k[0] for k in joint})
    ps = sorted({k[1] for k in joint})
    p = np.zeros((len(gs), len(ps)))
    for (gi, pl), m in joint.items():
        p[gs.index(gi), ps.index(pl)] = m
    p /= p.sum()
    pa, pb = p.sum(1), p.sum(0)
    nz = p > 0
    mi = (p[nz] * np.log(p[nz] / np.outer(pa, pb)[nz])).sum()
    ha = -(pa[pa > 0] * np.log(pa[pa > 0])).sum()
    hb = -(pb[pb > 0] * np.log(pb[pb > 0])).sum()
    return float(mi / math.sqrt(ha * hb)) if ha > 0 and hb > 0 else 0.0


def provenance():
    """Every threshold the reading classifies by, for a sweep's `provenance.csv`."""
    cuts = ", ".join(f"{k} {v}" for k, v in CUTS.items())
    return (f"ways by analysis/ways.py: blocks and cuts {cuts} (shares: the share that differs; size and range: "
            f"decades); range floor {RANGE_FLOOR} km a year; genotypes that have eaten nothing unread; leader "
            f"grouping by matter, the largest block distance over its cut <= 1")
