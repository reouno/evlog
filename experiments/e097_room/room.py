"""e097 (#109 step 0): what a birth that found no room hits, read off `<prefix>_room.csv`.

    uv run python experiments/e097_room/room.py [prefix ...]

With no argument it reads every `*_room.csv` in `results/`. It windows the rows to the settled part
of the run (`--from`, 20,000 by default), prints the distribution a failed birth is judged by, and
writes `results/provenance.csv` - the window it read and every threshold it classified by.
"""
import csv, glob, importlib.util, os, statistics as st, sys

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("e097_prov", os.path.join(HERE, "prov.py"))
prov_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(prov_mod)
MEDIA = ["land", "surface", "bottom", "crown"]
LENGTHS = [1, 2, 4, 8]  # body lengths the nearest spot with room is bucketed by


def rows_of(path, start):
    with open(path) as f:
        return [{k: int(v) for k, v in r.items()} for r in csv.DictReader(f) if int(r["step"]) >= start]


def log_of(pre, start):
    """The last log row of the run, and the jam over the window it covers."""
    with open(f"{pre}_log.csv") as f:
        rows = [r for r in csv.DictReader(f) if int(r["step"]) >= start]
    n = len(rows) or 1
    mean = lambda k: sum(float(r[k]) for r in rows) / n
    return {
        "steps": int(rows[-1]["step"]) if rows else 0,
        "pop": float(rows[-1]["pop"]) if rows else 0,
        "no_room": mean("no_room") / max(mean("children"), 1e-9),
        "blocked": mean("blocked"),
        "place_k": mean("place_k"),
        "cells_held": float(rows[-1]["cells_held"]) if rows else 0,
        "land_bare": float(rows[-1]["land_bare"]) if rows else 0,
    }


def share(rows, f):
    return sum(1 for r in rows if f(r)) / max(len(rows), 1)


def read(rows):
    """The measures of one run's failed births. `near` is in sub-cells; a body length is `reach`."""
    near = [r["near"] / r["reach"] for r in rows if r["near"] > 0]
    ring = [r for r in rows if r["ring"] > 0]
    out = {
        "failures": len(rows),
        "reach": st.mean(r["reach"] for r in rows),
        "blocks": st.mean(r["blocks"] for r in rows),
        "by_body": st.mean(r["hit_body"] / (4 * r["reach"]) for r in rows),
        "by_wall": st.mean(r["hit_wall"] / (4 * r["reach"]) for r in rows),
        "none": share(rows, lambda r: r["near"] < 0),
        "near_p50": st.median(near) if near else float("nan"),
        "near_p90": sorted(near)[int(0.9 * (len(near) - 1))] if near else float("nan"),
        "on_ray": st.mean(r["axis"] / r["ring"] for r in ring) if ring else float("nan"),
        "free_here": st.mean(r["free_here"] for r in rows) / 16,
        "free_around": st.mean(r["free_around"] for r in rows) / 128,
    }
    for b in LENGTHS:
        out[f"under_{b}"] = share(rows, lambda r, b=b: 0 < r["near"] <= b * r["reach"])
    return out


def table(name, cols, rows):
    w = [max(12, len(c) + 2) for c in cols]
    print(f"\n{name}")
    print(f"{'measure':<50}" + "".join(c.rjust(n) for c, n in zip(cols, w)))
    for key, label, fmt in LINES:
        print(f"{label:<50}" + "".join(format(r.get(key, float('nan')), fmt).rjust(n) for r, n in zip(rows, w)))


LINES = [
    ("failures", "failed births measured", ",d"),
    ("reach", "the rule's reach (sub-cells)", ".2f"),
    ("blocks", "blocks of the child", ".1f"),
    ("by_body", "its spots held by a body", ".1%"),
    ("by_wall", "its spots held by a wall", ".1%"),
    ("free_here", "free sub-cells, parent's cell", ".1%"),
    ("free_around", "free sub-cells, its neighbours", ".1%"),
    ("under_1", "room within 1 body length (the rule's own reach)", ".1%"),
    ("under_2", "room within 2", ".1%"),
    ("under_4", "room within 4", ".1%"),
    ("under_8", "room within 8", ".1%"),
    ("none", "no room within 8", ".1%"),
    ("near_p50", "nearest room, body lengths (p50)", ".2f"),
    ("near_p90", "the same (p90)", ".2f"),
    ("on_ray", "of that ring's spots, on the 4 rays", ".1%"),
]


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    start = next((int(a.split("=")[1]) for a in sys.argv[1:] if a.startswith("--from=")), 20000)
    files = sorted(glob.glob(os.path.join(HERE, "results", "*_room.csv")))
    if args:
        files = [f"{a}_room.csv" for a in args]
    prov = []
    cols, runs, by_medium = [], [], []
    for path in files:
        pre = path[: -len("_room.csv")]
        name = os.path.basename(pre)
        rows = rows_of(path, start)
        if not rows:
            print(f"{name}: no rows from step {start}")
            continue
        log = log_of(pre, start)
        cols.append(name.split("_")[-1])
        runs.append({**read(rows), **log})
        for m, label in enumerate(MEDIA):
            rs = [r for r in rows if r["medium"] == m]
            if len(rs) >= 100:
                by_medium.append((f"{cols[-1]} {label}", read(rs)))
        prov.append({
            "run": name, "from": start, "to": rows[-1]["step"], "items": len(rows),
            "thresholds": "failed births measured; body lengths " + " ".join(str(b) for b in LENGTHS)
                          + "; searched out to 8 body lengths",
        })
    if not runs:
        return
    table("A birth that found no room (the window in provenance.csv)", cols, runs)
    print(f"\n{'the run':<50}" + "".join(f"{c:>12}" for c in cols))
    for key, label, fmt in [("pop", "bodies at the end", ",.0f"), ("no_room", "births with no room", ".1%"),
                            ("place_k", "sub-cells a placed child went", ".2f"),
                            ("cells_held", "cells a body stands on", ".1%"),
                            ("land_bare", "land cells none stands on", ".1%")]:
        print(f"{label:<50}" + "".join(format(r[key], fmt).rjust(12) for r in runs))
    if by_medium:
        table("By the parent's medium", [n for n, _ in by_medium], [r for _, r in by_medium])
    print(f"\nprovenance: {prov_mod.write(HERE, 'room', prov)}")


if __name__ == "__main__":
    main()
