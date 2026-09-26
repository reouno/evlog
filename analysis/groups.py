"""Groups of producers by what they are: the open measure's reading 2 for producers (#116 step 3, e103).

Nothing is counted in boxes chosen before a run. Each genotype of a census is a vector of its traits, each
scaled by a fixed physical range (`SCALES`, the genome's own ranges); genotypes are grouped by a fixed
leader algorithm: taken heaviest first, a genotype joins the first group whose leader lies within `CUT`
(Euclidean distance over the scaled traits, divided by the square root of their number), or founds a group.
The reading is the effective number of groups (Hill number of order 1 over their biomass).

A new trait column extends `SCALES` without a rewrite; a census column no reader knows stops the reading
(CLAUDE.md, Measuring).

    from analysis.groups import vectors, group, hill
"""
import math

import numpy as np

CUT = 0.15  # the distance within which a genotype joins a group's leader

# column -> (lo, hi, log): the physical range each trait is scaled over (the genome's ranges, e103 genome.rs)
SCALES = {
    "alloc_leaf": (0.0, 1.0, False),
    "alloc_wood": (0.0, 1.0, False),
    "alloc_root": (0.0, 1.0, False),
    "alloc_store": (0.0, 1.0, False),
    "alloc_seed": (0.0, 1.0, False),
    "leaf_b": (0.005, 0.05, True),
    "leaf_a": (0.001, 0.05, True),
    "wood_b": (0.0005, 0.01, True),
    "wood_a": (0.0005, 0.03, True),
    "root_b": (0.003, 0.04, True),
    "root_a": (0.001, 0.04, True),
    "h_real": (0.05, 50.0, True),  # the height it stands at, not the height its genes aim at
    "deep": (0.0, 1.0, False),
    "seed_mass": (1e-7, 1e-2, True),
    "wing": (0.0, 0.5, False),
    "float": (0.0, 0.5, False),
    "defence": (0.0, 1.0, False),  # compound share scaled over its range, 0 without a compound gene
    "t_opt": (-10.0, 40.0, False),
    "breadth": (5.0, 25.0, True),
    "shed": (0.01, 20.0, True),
    "water": (0.0, 1.0, False),  # share of its biomass in the sea
}

# census columns read, and those carried but not grouped on
READ = set(SCALES) - {"defence", "water"} | {"compound", "n_keys", "mass_land", "mass_sea"}
CARRIED = {"year", "id", "parent", "born", "genes", "cells", "lead_cells", "height", "keys", "conditional", "age", "lifespan"}


def check(columns):
    """Fail loudly on a census column nobody has classified."""
    unknown = set(columns) - READ - CARRIED
    if unknown:
        raise SystemExit(f"groups.py: census columns no reader classifies: {sorted(unknown)}")


def _scaled(v, lo, hi, log):
    if log:
        v, lo, hi = math.log(max(v, lo)), math.log(lo), math.log(hi)
    return min(max((v - lo) / (hi - lo), 0.0), 1.0)


def vectors(rows):
    """The scaled trait matrix and the biomass of each census row (dicts of strings or numbers)."""
    rows = list(rows)
    if rows:
        check(rows[0].keys())
    x = np.zeros((len(rows), len(SCALES)))
    w = np.zeros(len(rows))
    for i, r in enumerate(rows):
        land, sea = float(r["mass_land"]), float(r["mass_sea"])
        w[i] = land + sea
        v = {k: float(r[k]) for k in SCALES if k in r}
        v["defence"] = _scaled(float(r["compound"]), 1e-4, 0.1, True) if int(r["n_keys"]) > 0 else 0.0
        v["water"] = sea / max(w[i], 1e-30)
        for j, (k, (lo, hi, log)) in enumerate(SCALES.items()):
            x[i, j] = v[k] if k in ("defence", "water") else _scaled(v[k], lo, hi, log)
    return x, w


def group(x, w, cut=CUT):
    """Leader grouping, heaviest first. Returns each row's group (the index of its leader's row)."""
    order = np.argsort(-w, kind="stable")
    leaders = []
    g = np.empty(len(w), dtype=int)
    norm = math.sqrt(x.shape[1])
    for i in order:
        if leaders:
            d = np.sqrt(((x[leaders] - x[i]) ** 2).sum(axis=1)) / norm
            j = int(np.argmin(d))
            if d[j] <= cut:
                g[i] = leaders[j]
                continue
        leaders.append(i)
        g[i] = i
    return g


def hill(weights):
    """Effective number (Hill 1) of positive weights."""
    p = np.asarray([v for v in weights if v > 0], dtype=float)
    if p.size == 0:
        return 0.0
    p /= p.sum()
    return float(np.exp(-(p * np.log(p)).sum()))
