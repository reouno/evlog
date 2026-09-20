"""A census of ways of living (#71): what the grown bodies of a world live by.

Run from the repo root: `uv run python experiments/e060_census/census.py` reads the `agents.csv`
and `log.csv` of every run in PAIRS and ALSO, prints the census and the frame test, and writes
`experiments/e060_census/results/{runs,pairs,ways}.csv`. `census.py sweep` repeats the frame test
under other thresholds and writes `results/sweep.csv`. Later experiments import `way`, `census`,
`count`, `count_by_place`, `hill`, `rarefied`, `kinds` and `kills_share` from here (the successor to
e058's diversity.py).

A body's way of living is what it does, read from three columns:

- diet: the flesh share of its lifetime intake, meat / (plant + meat). Plant below 1/3, flesh
  above 2/3, mixed between. `meat` is what it took from broken cells of other bodies and, from
  e017 on, from the dead. No run splits kills from scavenging per body.
- tooth: a hard tip with a force of 2 or more behind it, on any side (`bite_any`; before e024
  only `bite`, the front). A force of 2 breaks a soft face of density 1.
- movement: roams when it stands ROAM world cells or more from where it was born (`travel`,
  e048 on). Runs before e048 have no such column, and their ways have two parts.

Only bodies aged GROWN or more are counted: a newborn has no diet yet. A way of living is counted
when it holds SHARE of the grown bodies; the tail is counted by q1.

The state of a world (e045) is read apart from the bodies, from the log: the flesh of kills' share
of everything the world ate. At HUNTER or more it is a hunter world.
"""
import csv, glob, math, os, random, statistics, sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
EXP = os.path.dirname(HERE)
sys.path.insert(0, os.path.dirname(EXP))
from analysis import schema  # noqa: E402  (the guard: a column no reader has classified stops the reading)

GROWN = 300          # steps of age
FLESH = (1 / 3, 2 / 3)
LIGHT = 0.5          # e093 (#103): a body or a group that took this share of its matter from the light lives by it
TOOTH = 2            # force behind a hard tip
ROAM = 8.0           # world cells from the birthplace
SHARE = 0.05         # of the grown bodies
HUNTER = 0.25        # kills' share of the world's intake (e045: grazer worlds 16-20%, hunter worlds 30-41%)
RAREFY = 100         # grown bodies per draw
DRAWS = 200

KINDS = ["hard", "muscle", "sensor", "digestive"]
LEAF = "leaf"        # e093 (#103): a fifth block kind, in the runs that have the column
SIZE_EDGES = [8, 16, 32, 64]
BIN = 4


# ---------------------------------------------------------------- one body

def flesh_share(r):
    p, m = float(r["plant"]), float(r["meat"])
    return m / (p + m) if p + m > 0 else None


def light_share(r):
    """e093 (#103): the share of a body's life's matter its leaf blocks took from the light, or None
    where the run has no light (every census before e093)."""
    if r.get("light") in (None, ""):
        return None
    p, m, l = float(r["plant"]), float(r["meat"]), float(r["light"])
    return l / (p + m + l) if p + m + l > 0 else None


def has_tooth(r):
    return int(float(r.get("bite_any") or r["bite"])) >= TOOTH


def way(r, roam=True):
    """The way of living of one row of agents.csv, or None for a body that has eaten nothing."""
    f = flesh_share(r)
    lt = light_share(r)
    if f is None and lt is None:
        return None
    # e093 (#103): a body that took most of its matter from the light lives by the light, whatever
    # the rest of it ate. Without the column (every run before e093) this reads as it always did.
    if lt is not None and lt >= LIGHT:
        diet = "light"
    elif f is None:
        return None
    else:
        diet = "plant" if f < FLESH[0] else "flesh" if f > FLESH[1] else "mixed"
    w = (diet, "tooth" if has_tooth(r) else "no tooth")
    if not roam or r.get("travel") in (None, ""):
        return w
    return w + ("roams" if float(r["travel"]) >= ROAM else "stays",)


def place_of(r):
    """The rich or thin land where the run has it (e059), else `place`: the kind of patch, or the
    height band under a uniform sun."""
    return r["rich"] if "rich" in r else r.get("place", "0")


def kind(r):
    """#66's shape kind: size class and block mix in quarters, from the birth shape where the run
    has it (e058 on), else from the current shape."""
    # e094: the kinds of block are read off the census, so a new one needs no line here.
    pre = "born_" if "born_hard" in r else ""
    kinds = schema.blocks(list(r)) or KINDS
    c = [float(r[pre + k]) for k in kinds]
    n = sum(c)
    if n <= 0:
        return None
    return (sum(n >= e for e in SIZE_EDGES), tuple(round(x / n * BIN) for x in c))


# ---------------------------------------------------------------- a world

def read(path):
    """The rows of agents.csv by census step, once every column of it has been classified."""
    by = defaultdict(list)
    with open(path) as f:
        rows = csv.DictReader(f)
        for r in rows:
            if not by:
                schema.check(rows.fieldnames, os.path.basename(path))
            by[int(r["step"])].append(r)
    return dict(sorted(by.items()))


def grown(rows):
    return [r for r in rows if int(r["age"]) >= GROWN]


def census(rows, roam=True):
    """Counter of ways of living among the grown bodies."""
    return Counter(w for w in (way(r, roam) for r in grown(rows)) if w)


def kinds(rows):
    return Counter(k for k in (kind(r) for r in rows) if k)


def count(c, share=None):
    share = SHARE if share is None else share
    n = sum(c.values())
    return sum(v >= share * n for v in c.values()) if n else 0


def count_by_place(rows, roam=True):
    """Ways of living holding SHARE of the grown bodies of a place that itself holds SHARE of them:
    a way of living confined to a small place still counts."""
    by = defaultdict(Counter)
    for r in grown(rows):
        w = way(r, roam)
        if w:
            by[place_of(r)][w] += 1
    n = sum(sum(c.values()) for c in by.values())
    found = set()
    for c in by.values():
        m = sum(c.values())
        if m >= SHARE * n:
            found |= {w for w, v in c.items() if v >= SHARE * m}
    return len(found)


def hill(c):
    n = sum(c.values())
    if not n:
        return 0, 0.0, 0.0
    p = [v / n for v in c.values()]
    return len(c), math.exp(-sum(x * math.log(x) for x in p)), 1.0 / sum(x * x for x in p)


def rarefied(c, m=RAREFY, draws=DRAWS, seed=1):
    """The mean number of distinct entries in a random draw of m (None if there are fewer)."""
    pool = [k for k, v in c.items() for _ in range(v)]
    if len(pool) < m:
        return None
    rng = random.Random(seed)
    return sum(len(set(rng.sample(pool, m))) for _ in range(draws)) / draws


def describe(rows, w):
    """Where a way of living lives and what it is: the numbers that say what limits it."""
    rs = [r for r in grown(rows) if way(r) == w]
    if not rs:
        return {}
    med = lambda k: statistics.median(float(r[k]) for r in rs)
    size = "born_size" if "born_size" in rs[0] else "born_mass"
    out = {"n": len(rs), "size": med(size), "speed": med("speed"), "age": med("age"),
           "flesh": statistics.median(flesh_share(r) for r in rs),
           "lineages": len({r["lineage"] for r in rs})}
    top = Counter(r["lineage"] for r in rs).most_common(1)[0]
    out["top_lineage"], out["top_lineage_share"] = top[0], top[1] / len(rs)
    if "travel" in rs[0]:
        out["travel"] = med("travel")
    if "rich" in rs[0]:
        out["on_rich"] = statistics.mean(r["rich"] == "1" for r in rs)
    if "place" in rs[0]:
        p = Counter(r["place"] for r in rs)
        out["places"] = " ".join(f"{k}:{v / len(rs):.2f}" for k, v in sorted(p.items()))
        out["crossed"] = statistics.mean(r["place"] != r["born_place"] for r in rs)
    return out


# ---------------------------------------------------------------- the runs

# A run is (experiment folder, file pattern with {s} for the seed). Patterns are checked to match
# one file each.
R = {
    "e010 width 8": ("e010_contact", "128_patchy_seed{s}_agents.csv"),
    "e011 width 1": ("e011_rich_cells", "128_patchy_cap8_sigma1_seed{s}_agents.csv"),
    "e012 widths 8+1": ("e012_two_places", "128_sigma8-1_seed{s}_agents.csv"),
    "e025 weight 0": ("e025_weight", "*_flesh1_w0_seed{s}_agents.csv"),
    "e025 weight 1": ("e025_weight", "*_flesh1_w1_seed{s}_agents.csv"),
    "e026 season 0.5": ("e026_weather", "*_w1_season0.5_seed{s}_agents.csv"),
    "e026 cloud 1": ("e026_weather", "*_w1_cloud1_seed{s}_agents.csv"),
    "e028 gut curve": ("e028_gut", "*_season0.5_digest2_seed{s}_agents.csv"),
    "e032 flat 0.75": ("e032_winter", "*_season0.75_*_breed0_seed{s}_agents.csv"),
    "e032 winter high 2": ("e032_winter", "*_season2_*_winterhigh_seed{s}_agents.csv"),
    "e037 control": ("e037_upkeep", "*_mix0.2_seed{s}_agents.csv"),
    "e037 k 0.6": ("e037_upkeep", "*_mix0.2_k0.6_seed{s}_agents.csv"),
    "e038 sun 2": ("e038_income", "*_mix0.2_sun2_seed{s}_agents.csv"),
    "e038 sun 4": ("e038_income", "*_mix0.2_sun4_seed{s}_agents.csv"),
    "e038 k 0.6 sun 2": ("e038_income", "*_mix0.2_k0.6_sun2_seed{s}_agents.csv"),
    "e038 k 0.6 sun 4": ("e038_income", "*_mix0.2_k0.6_sun4_seed{s}_agents.csv"),
    "e039 reach 1": ("e039_reach", "*_mix0.2_reach1_seed{s}_agents.csv"),
    "e039 same reach": ("e039_reach", "*_mix0.2_reachfix1_seed{s}_agents.csv"),
    "e040 thirst 0.001": ("e040_thirst", "*_thirst0.001_seed{s}_agents.csv"),
    "e040 thirst 0.002": ("e040_thirst", "*_thirst0.002_seed{s}_agents.csv"),
    "e040 thirst 0.005": ("e040_thirst", "*_thirst0.005_seed{s}_agents.csv"),
    "e041 control": ("e041_stock", "*_mix0.2_seed{s}_agents.csv"),
    "e041 stock 1": ("e041_stock", "*_mix0.2_stock1_seed{s}_agents.csv"),
    "e041 stock 4": ("e041_stock", "*_mix0.2_stock4_seed{s}_agents.csv"),
    "e045 control": ("e045_connect", "*_wear3000_seed{s}_agents.csv"),
    "e045 connect": ("e045_connect", "*_wear3000_connect_seed{s}_agents.csv"),
    "e046 plant 0.5": ("e046_yield", "*_connect_plant0.5_seed{s}_agents.csv"),
    "e048 motor": ("e048_motor", "*_mix0.2_strict_sat_hold_wear3000_corner_motor_seed{s}_agents.csv"),
    "e050 brain": ("e050_brain", "*_mix0.2_strict_sat_hold_wear3000_corner_motor_brain_seed{s}_agents.csv"),
    "e051 stock 1": ("e051_leave", "*_stock1_strict_sat_hold_wear3000_corner_motor_seed{s}_agents.csv"),
    "e051 stock 4": ("e051_leave", "*_stock4_strict_sat_hold_wear3000_corner_motor_seed{s}_agents.csv"),
    "e051 stock 1 brain": ("e051_leave", "*_stock1_strict_sat_hold_wear3000_corner_motor_brain_seed{s}_agents.csv"),
    "e051 stock 4 brain": ("e051_leave", "*_stock4_strict_sat_hold_wear3000_corner_motor_brain_seed{s}_agents.csv"),
    "e054 control": ("e054_grain", "*_mix0.2_strict_sat_hold_wear3000_corner_motor_seed{s}_agents.csv"),
    "e054 grain 64": ("e054_grain", "*_corner_motor_patch64_seed{s}_agents.csv"),
    "e055 flat pace": ("e055_span", "*_corner_motor_pace0.68_seed{s}_agents.csv"),
    "e055 clock 0.5": ("e055_span", "*_mix0.2_strict_sat_hold_wear3000_corner_motor_clock0.5_seed{s}_agents.csv"),
    "e056 sun 2": ("e056_sun", "*_mix0.2_sun2_strict_*_clock0.5_seed{s}_agents.csv"),
    "e056 sun 4": ("e056_sun", "*_mix0.2_sun4_strict_*_clock0.5_seed{s}_agents.csv"),
    "e057 control": ("e057_foul", "*_corner_motor_clock0.5_seed{s}_agents.csv"),
    "e057 foul 0.03": ("e057_foul", "*_clock0.5_foul0.03_seed{s}_agents.csv"),
    "e058 sun 1": ("e058_thin", "*_mix0.2_strict_sat_hold_wear3000_corner_motor_clock0.5_seed{s}_agents.csv"),
    "e058 sun 0.2": ("e058_thin", "*_mix0.2_sun0.2_*_seed{s}_agents.csv"),
    "e058 sun 0.1": ("e058_thin", "*_mix0.2_sun0.1_*_seed{s}_agents.csv"),
    "e059 thin uniform": ("e059_places", "128_sigma0_*_sun0.2_*_clock0.5_seed{s}_agents.csv"),
    "e059 islands": ("e059_places", "128_sigma8_*_patch1820_seed{s}_agents.csv"),
}

# The frame test (#71): the law, its control at the same code, the seeds, and what the frame
# says the law did. "axis" laws added an independent limiting factor with a trade-off, so they
# should hold more ways of living than their control; the others moved the amount, timing or
# place of the one resource, overlapped an old axis in place, or had no trade-off, and should not.
PAIRS = [
    ("axis", "two places", "e012 widths 8+1", "e011 width 1", range(1, 5)),
    ("axis", "two places", "e012 widths 8+1", "e010 width 8", range(1, 5)),
    ("axis", "flesh + weight", "e025 weight 1", "e025 weight 0", range(1, 5)),
    ("axis", "time (season)", "e026 season 0.5", "e025 weight 1", range(1, 5)),
    ("axis", "time (cloud)", "e026 cloud 1", "e025 weight 1", range(1, 5)),
    ("axis", "time by place", "e032 winter high 2", "e032 flat 0.75", range(1, 4)),
    ("overlap", "flesh with the plants", "e028 gut curve", "e026 season 0.5", range(1, 5)),
    ("overlap", "water with the food", "e040 thirst 0.001", "e041 control", [9]),
    ("overlap", "water with the food", "e040 thirst 0.002", "e041 control", [9]),
    ("overlap", "water with the food", "e040 thirst 0.005", "e041 control", [9]),
    ("no trade-off", "reach", "e039 reach 1", "e039 same reach", [1, 2, 3, 9]),
    ("amount", "more sun", "e038 sun 2", "e037 control", [9]),
    ("amount", "more sun", "e038 sun 4", "e037 control", [9]),
    ("amount", "more sun", "e038 k 0.6 sun 2", "e037 k 0.6", [9]),
    ("amount", "more sun", "e038 k 0.6 sun 4", "e037 k 0.6", [9]),
    ("amount", "growth follows stock", "e041 stock 1", "e041 control", [9]),
    ("amount", "growth follows stock", "e041 stock 4", "e041 control", [9]),
    ("amount", "plant yield", "e046 plant 0.5", "e045 connect", range(9, 15)),
    ("amount", "slow return", "e051 stock 1", "e048 motor", range(9, 13)),
    ("amount", "slow return", "e051 stock 4", "e048 motor", range(9, 13)),
    ("amount", "slow return", "e051 stock 1 brain", "e050 brain", range(9, 13)),
    ("amount", "slow return", "e051 stock 4 brain", "e050 brain", range(9, 13)),
    ("amount", "grain of the food", "e054 grain 64", "e054 control", range(9, 13)),
    ("amount", "more sun", "e056 sun 2", "e055 clock 0.5", range(9, 15)),
    ("amount", "more sun", "e056 sun 4", "e055 clock 0.5", range(9, 12)),
    ("amount", "fouling", "e057 foul 0.03", "e057 control", range(9, 15)),
    ("amount", "islands of food", "e059 islands", "e059 thin uniform", range(9, 15)),
]

# Runs censused for their own sake (the states of e045 and e055, the thinning of e058).
ALSO = [("e045 control", range(9, 15)), ("e045 connect", range(9, 15)),
        ("e055 flat pace", range(9, 15)), ("e055 clock 0.5", range(9, 15)),
        ("e058 sun 1", [9]), ("e058 sun 0.2", [9]), ("e058 sun 0.1", [9])]


def path(run, seed):
    d, pat = R[run]
    hits = glob.glob(os.path.join(EXP, d, "results", pat.format(s=seed)))
    if len(hits) != 1:
        raise SystemExit(f"{run} seed {seed}: {len(hits)} files match {pat}")
    return hits[0]


_agents, _logs = {}, {}


def load(run, seed):
    if (run, seed) not in _agents:
        _agents[(run, seed)] = read(path(run, seed))
    return _agents[(run, seed)]


def log_rows(run, seed):
    if (run, seed) not in _logs:
        with open(path(run, seed)[:-len("_agents.csv")] + "_log.csv") as f:
            _logs[(run, seed)] = list(csv.DictReader(f))
    return _logs[(run, seed)]


def kills_share(run, seed, upto):
    """The flesh of kills' share of what the world ate over steps (upto / 2, upto], as e045 measured it,
    and whether the log can say (`kill_gain`, e024 on; before, `meat` is kills alone and no state is read)."""
    rows = [r for r in log_rows(run, seed) if upto / 2 < int(r["step"]) <= upto]
    plant = sum(float(r["plant_intake"]) for r in rows)
    meat = sum(float(r["meat_intake"]) for r in rows)
    known = "kill_gain" in rows[0]
    kills = sum(float(r["kill_gain"]) * float(r["cells_broken"]) for r in rows) if known else meat
    return (kills / (plant + meat) if plant + meat else 0.0), known


def late(steps):
    """The census steps of the second half (the last alone for a run with one census)."""
    steps = sorted(s for s in steps if s > 0)
    return [s for s in steps if s >= steps[-1] / 2]


def census_by_lineage(rows):
    """Every grown body counted under its lineage's most common way of living: the count of ways that
    are kinds, not the spread inside one kind. A lower bound, since a lineage (single linkage on gene
    lists) can join bodies of different builds."""
    by = defaultdict(Counter)
    for r in grown(rows):
        w = way(r)
        if w:
            by[r["lineage"]][w] += 1
    out = Counter()
    for c in by.values():
        out[c.most_common(1)[0][0]] += sum(c.values())
    return out


def measure(rows, full=True):
    c = census(rows)
    g = grown(rows)
    out = {"bodies": len(rows), "grown": len(g), "ways": count(c), "ways_diet_tooth": count(census(rows, roam=False)),
           "ways_by_place": count_by_place(rows), "ways_lineage": count(census_by_lineage(rows)), "q1": hill(c)[1]}
    if full:
        out["ways_rarefied"] = rarefied(c)
        out["kinds_rarefied"] = rarefied(kinds(rows), m=120)
        out["tooth"] = statistics.mean(has_tooth(r) for r in g) if g else None
        out["roams"] = statistics.mean(float(r["travel"]) >= ROAM for r in g) if g and "travel" in g[0] else None
    return out


def mean_over(run, seed, steps, full=True):
    data = load(run, seed)
    ms = [measure(data[s], full) for s in steps]
    out = {}
    for k in ms[0]:
        v = [m[k] for m in ms if m[k] is not None]
        out[k] = statistics.mean(v) if v else None
    share, known = kills_share(run, seed, max(steps))
    out["kills_share"] = share
    out["state"] = ("hunter" if share >= HUNTER else "grazer") if known else None
    return out


def pair(law, control, seeds, full=True):
    out = []
    for s in seeds:
        steps = late(set(load(law, s)) & set(load(control, s)))
        out.append((s, steps, mean_over(law, s, steps, full), mean_over(control, s, steps, full)))
    return out


def verdict(diffs):
    if not diffs:
        return "-"
    more = sum(d >= 1 for d in diffs)
    fewer = sum(d <= -1 for d in diffs)
    top = max((more, "more"), (len(diffs) - more - fewer, "same"), (fewer, "fewer"))
    return top[1] if top[0] > len(diffs) / 2 else "split"


def holds(cls, v):
    return v == "more" if cls == "axis" else v not in ("more", "-")


def summarize(res, key="ways"):
    """The verdict over all seeds, over the seeds where law and control are in the same state, and
    the state changes the law made (control > law, h hunter, g grazer)."""
    d = [a[key] - b[key] for _, _, a, b in res]
    same = [a[key] - b[key] for _, _, a, b in res if a["state"] and a["state"] == b["state"]]
    moved = Counter(f"{b['state'][0]}>{a['state'][0]}" for _, _, a, b in res
                    if a["state"] and b["state"] and a["state"] != b["state"])
    return verdict(d), verdict(same), len(same), " ".join(f"{k} x{v}" for k, v in sorted(moved.items()))


def write(name, rows):
    keys = list(dict.fromkeys(k for r in rows for k in r))
    with open(os.path.join(HERE, "results", f"{name}.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        w.writerows(rows)


def all_runs():
    seeds = defaultdict(set)
    for _, _, a, b, ss in PAIRS:
        seeds[a].update(ss)
        seeds[b].update(ss)
    for r, ss in ALSO:
        seeds[r].update(ss)
    return [(r, s) for r in sorted(seeds) for s in sorted(seeds[r])]


def main():
    os.makedirs(os.path.join(HERE, "results"), exist_ok=True)
    print(f"grown {GROWN}, diet cut {FLESH[0]:.2f}/{FLESH[1]:.2f}, tooth force {TOOTH}, roam {ROAM} cells, "
          f"share {SHARE}, hunter world at kills {HUNTER:.0%} of the intake")
    out_pairs = []
    for cls, what, law, control, seeds in PAIRS:
        res = pair(law, control, seeds)
        v, v_same, n_same, moved = summarize(res)
        vp = summarize(res, "ways_by_place")[0]
        vl = summarize(res, "ways_lineage")[0]
        print(f"\n[{cls}] {what}: {law} vs {control} -> {v}; same-state seeds ({n_same}): {v_same}; "
              f"by place: {vp}; by lineage: {vl}; state changes: {moved or 'none'}; "
              f"frame {'holds' if holds(cls, v) else 'FAILS'} (by lineage {'holds' if holds(cls, vl) else 'FAILS'})")
        for s, steps, a, b in res:
            st = lambda m: (m["state"] or "-")[0]
            print(f"  seed {s:2d} [{len(steps)} census]  ways {a['ways']:4.1f} vs {b['ways']:4.1f}  "
                  f"by place {a['ways_by_place']:4.1f} vs {b['ways_by_place']:4.1f}  "
                  f"by lineage {a['ways_lineage']:4.1f} vs {b['ways_lineage']:4.1f}  q1 {a['q1']:5.2f} vs {b['q1']:5.2f}  "
                  f"kills {a['kills_share']:4.0%} {st(a)} vs {b['kills_share']:4.0%} {st(b)}  "
                  f"tooth {a['tooth'] or 0:4.0%} vs {b['tooth'] or 0:4.0%}  grown {a['grown']:5.0f} vs {b['grown']:5.0f}")
            out_pairs.append({"class": cls, "what": what, "law": law, "control": control, "seed": s, "census": len(steps),
                              "verdict": v, "verdict_same_state": v_same, "verdict_by_place": vp, "verdict_lineage": vl,
                              "state_changes": moved,
                              **{f"law_{k}": x for k, x in a.items()}, **{f"control_{k}": x for k, x in b.items()}})
    out_runs, out_ways = [], []
    for run, s in all_runs():
        data = load(run, s)
        steps = late(data)
        m = mean_over(run, s, steps)
        out_runs.append({"run": run, "seed": s, "steps": " ".join(map(str, steps)), **m})
        rows = [r for st in steps for r in data[st]]
        c = census(rows)
        n = sum(c.values())
        for w, v in c.most_common():
            out_ways.append({"run": run, "seed": s, "way": " / ".join(w), "share": v / n, **describe(rows, w)})
    print("\nways of living by the state of the world (every run and seed whose log has kill_gain):")
    for state in ("grazer", "hunter"):
        rs = [r for r in out_runs if r["state"] == state]
        for key in ("ways", "ways_diet_tooth", "ways_lineage", "q1"):
            v = [r[key] for r in rs]
            print(f"  {state:6s} n {len(rs):3d}  {key:16s} mean {statistics.mean(v):5.2f}  range {min(v):4.1f}-{max(v):4.1f}")
    for name, rows in (("pairs", out_pairs), ("runs", out_runs), ("ways", out_ways)):
        write(name, rows)


SETTINGS = [
    ("base", {}),
    ("roam 4", {"ROAM": 4.0}), ("roam 16", {"ROAM": 16.0}),
    ("diet 0.2/0.8", {"FLESH": (0.2, 0.8)}),
    ("tooth 1", {"TOOTH": 1}), ("tooth 3", {"TOOTH": 3}),
    ("grown 100", {"GROWN": 100}), ("grown 1000", {"GROWN": 1000}),
    ("share 2%", {"SHARE": 0.02}), ("share 10%", {"SHARE": 0.10}),
]


def sweep():
    """The frame test under other thresholds: does a verdict depend on where a line was drawn?"""
    g = globals()
    base = {k: g[k] for _, s in SETTINGS for k in s}
    table = []
    for label, s in SETTINGS:
        g.update(base)
        g.update(s)
        row = {"setting": label}
        for cls, what, law, control, seeds in PAIRS:
            row[f"{law} vs {control}"] = summarize(pair(law, control, seeds, full=False))[0]
        row["frame holds"] = sum(holds(p[0], row[f"{p[2]} vs {p[3]}"]) for p in PAIRS)
        table.append(row)
    g.update(base)
    keys = [f"{p[2]} vs {p[3]}" for p in PAIRS]
    print(f"{'pair':40s} " + " ".join(f"{t['setting']:>12s}" for t in table))
    for p, k in zip(PAIRS, keys):
        print(f"{p[0][:7]:7s} {k[:32]:32s} " + " ".join(f"{t[k]:>12s}" for t in table))
    print(f"{'frame holds (of ' + str(len(PAIRS)) + ')':40s} " + " ".join(f"{t['frame holds']:>12d}" for t in table))
    write("sweep", table)


if __name__ == "__main__":
    sweep() if sys.argv[1:] == ["sweep"] else main()
