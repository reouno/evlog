#!/usr/bin/env python3
"""The balance sets (#88): e072's chosen combination against e070's runs on the same seeds.

Run from the repo root: `uv run python experiments/e072_balance/balance.py [name]` (a few minutes).
It reads the second half's censuses of every run, counts kinds by birth form with e068's `kinds.py`,
reads the grown bodies by medium and by temperature band (e061's cold, mild and hot, of the habitat
under them), prints the numbers and writes `results/*.csv` for the report.
"""
import csv
import os
import statistics as st
import sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "experiments", "e068_kinds"))
import kinds  # noqa: E402  (e068's census by birth form; it imports e060's census)

census = kinds.census
SEEDS = (9, 10, 11)
NAME = sys.argv[1] if len(sys.argv) > 1 else "sets"
PRE = {"control": lambda s: os.path.join(ROOT, "experiments", "e070_senses", "results", f"c1225_life{s}_senses"),
       "sets": lambda s: os.path.join(HERE, "results", f"c1225_life{s}_{NAME}")}
RUNS = [(f"{arm}{s}", s, arm, PRE[arm](s)) for s in SEEDS for arm in ("control", "sets")]
CAUSES = ("hunger", "broken", "wear", "thirst", "suffocation", "cold")
BANDS = ("cold", "mild", "hot")
UPKEEP, UPKEEP_BODY = 0.002, 0.032


def band(r):
    h = int(r["place"])
    return BANDS[h // 3 if h < 9 else (h - 9) % 3]


def fill(r):
    return min(float(r["fat"]) / max(float(r["store"]) * float(r["mass"]), 1e-6), 1.0)


def bodies(rows):
    """Grown bodies read together: open soft faces and hard blocks per block, the fat's fill, blocks, the
    cell's temperature and the body's own, what they paid to the heat, and the wood in their diet."""
    n, size = max(len(rows), 1), max(sum(int(r["size"]) for r in rows), 1)
    upkeep = max(sum(int(r["turns"]) * (UPKEEP * int(r["size"]) + UPKEEP_BODY) for r in rows), 1e-12)
    food = max(sum(float(r["plant"]) + float(r["meat"]) for r in rows), 1e-12)
    med = Counter(r["medium"] for r in rows)
    return {"bodies": len(rows), "open": sum(int(r["open_soft"]) for r in rows) / size,
            "hard": sum(int(r["hard"]) for r in rows) / size, "blocks": size / n,
            "fat_fill": st.median(fill(r) for r in rows) if rows else float("nan"),
            "mass": st.median(float(r["mass"]) for r in rows) if rows else float("nan"),
            "temp": st.median(float(r["temp"]) for r in rows) if rows else float("nan"),
            "btemp": st.median(float(r.get("btemp", 0)) for r in rows) if rows else float("nan"),
            "warmed": sum(float(r.get("warmed", 0)) for r in rows) / upkeep,
            "cooled": sum(float(r.get("cooled", 0)) for r in rows) / max(sum(int(r["turns"]) for r in rows), 1),
            "wood": sum(float(r.get("wood", 0)) for r in rows) / food,
            "store": st.median(float(r["store"]) for r in rows) if rows else float("nan"),
            "travel": st.median(float(r["travel"]) for r in rows) if rows else float("nan"),
            "height": st.median(float(r["height"]) for r in rows) if rows else float("nan"),
            "tooth": sum(int(float(r["bite_any"])) >= 3 for r in rows) / n,
            **{f"in_{m}": med[str(i)] / n for i, m in enumerate(kinds.MEDIA)}}


def log_half(pre):
    with open(pre + "_log.csv") as f:
        rows = list(csv.DictReader(f))
    last = int(rows[-1]["step"])
    late = [r for r in rows if 2 * int(r["step"]) > last]
    col = lambda k: [float(r.get(k, 0) or 0) for r in late]  # noqa: E731
    deaths = {c: sum(col(f"deaths_{c}")) for c in CAUSES}
    total = max(sum(deaths.values()), 1)
    first = rows[0]
    out = {"steps": last, "pop": st.mean(col("pop")), "pop_min": min(col("pop")), "pop_end": float(rows[-1]["pop"]),
           "lineages": st.mean(col("lineages")), "top_lineage": st.mean(col("top_lineage")),
           "births_per_body": sum(col("births")) / max(sum(col("pop")), 1),
           "blocked": st.mean(col("blocked")), "no_room": st.mean(col("no_room_land")),
           "kills": (sum(col("meat_intake")) - sum(col("scavenged"))) / max(sum(col("plant_intake")) + sum(col("meat_intake")), 1e-9),
           "size_mean": st.mean(col("size_mean")), "ms_step": st.mean(col("ms_step")),
           "err": max(col("matter_err")), "sighted": st.mean(col("sighted")),
           "land_drift": (float(rows[-1].get("matter_land", 0) or 0) - float(first.get("matter_land", 0) or 0)) / max(float(first.get("matter_land", 1) or 1), 1),
           "sea_drift": (float(rows[-1].get("matter_sea", 0) or 0) - float(first.get("matter_sea", 0) or 0)) / max(float(first.get("matter_sea", 1) or 1), 1),
           "carried": st.mean(col("carried")), "wood_intake": st.mean(col("wood_intake")),
           **{f"pop_{m}": st.mean(col(f"pop_{m}")) for m in kinds.MEDIA},
           **{f"open_{m}": st.mean(col(f"open_{m}")) for m in kinds.MEDIA},
           **{f"warm_{m}": st.mean(col(f"warm_{m}")) for m in kinds.MEDIA}}
    return out | {f"deaths_{c}": deaths[c] / total for c in CAUSES}


def write(name, rows):
    keys = list(dict.fromkeys(k for r in rows for k in r))
    with open(os.path.join(HERE, "results", f"{name}.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        w.writerows(rows)


def main():
    out = defaultdict(list)
    for name, seed, arm, pre in RUNS:
        if not os.path.exists(pre + "_row.csv"):
            print(f"{name}: not run yet ({pre})")
            continue
        run = kinds.Run(name, pre)
        per, held = kinds.form_census(run)
        nm, nm_held, _ = kinds.null(run, ("medium",))
        described = kinds.describe(run, per, held)
        kept = [k for k in described if k["held"] and not k["kind"].endswith("shore")]
        land = [r for r in run.grown if r["medium"] == "0"]
        lb = bodies(land)
        row = {"run": name, "seed": seed, "arm": arm, "censuses": len(run.steps), "grown": len(run.grown) / len(run.steps),
               "lineage_e060": kinds.lineage_e060(run), "forms": len(set(run.forms())),
               "form": kinds.mean_count(per), "form_low": min(len(p) for p in per.values()), "form_high": max(len(p) for p in per.values()),
               "form_held": len(held), "null_medium": nm, "null_medium_held": nm_held,
               "held_one_medium": len(kept), "one_medium": " | ".join(k["kind"] for k in kept),
               "land_open": lb["open"], "land_fill": lb["fat_fill"], "land_hard": lb["hard"], "land_blocks": lb["blocks"],
               "land_wood": lb["wood"], "land_tooth": lb["tooth"], "land_btemp": lb["btemp"], "land_store": lb["store"],
               **{f"land_{b}": sum(band(r) == b for r in land) / max(len(land), 1) for b in BANDS}}
        row |= log_half(pre)
        out["runs"].append(row)
        for m, medium in enumerate(kinds.MEDIA):
            out["media"].append({"run": name, "seed": seed, "arm": arm, "medium": medium} | bodies([r for r in run.grown if r["medium"] == str(m)]))
        for b in BANDS:
            out["bands"].append({"run": name, "seed": seed, "arm": arm, "band": b} | bodies([r for r in land if band(r) == b]))
        for step, rs in census.read(pre + "_agents.csv").items():
            g = census.grown(rs)
            gl = [r for r in g if r["medium"] == "0"]
            out["time"].append({"run": name, "seed": seed, "arm": arm, "step": step, "kinds": len(per[step]) if step in per else "",
                                "land_open": bodies(gl)["open"] if gl else "", "land_wood": bodies(gl)["wood"] if gl else "",
                                **{f"share_{m}": sum(r["medium"] == str(i) for r in g) / max(len(g), 1) for i, m in enumerate(kinds.MEDIA)},
                                **{f"land_{b}": sum(band(r) == b for r in gl) / max(len(gl), 1) for b in BANDS}})
        unit = run.forms()
        ways = kinds.by_group(run, unit, run.does())
        members = defaultdict(list)
        for i, u in enumerate(unit):
            members[" / ".join(ways[u])].append(run.grown[i])
        for k in described:
            ms = members[k["kind"]]
            where = Counter(band(r) for r in ms)
            out["kinds"].append(k | {"seed": seed, "arm": arm} | bodies(ms) | {f"band_{x}": where[x] / max(len(ms), 1) for x in BANDS})
        print(f"{name}: grown {row['grown']:.0f}, kinds by form {row['form']:.2f} [{row['form_low']}-{row['form_high']}] held {row['form_held']} "
              f"(medium shuffled {nm:.2f}/{nm_held:.1f}), lineage {row['lineage_e060']:.2f}; stood {row['steps']} steps, low {row['pop_min']:.0f}")
        print(f"  held in one medium: {row['held_one_medium']} ({row['one_medium']})")
        print(f"  land bodies: open/block {lb['open']:.3f}, hard {lb['hard']:.3f}, blocks {lb['blocks']:.1f}, fat fill {lb['fat_fill']:.3f}, "
              f"store {lb['store']:.2f}, body {lb['btemp']:.1f} C on a cell of {lb['temp']:.1f} C, warming {lb['warmed']:.2f} of the upkeep, "
              f"wood {lb['wood']:.1%} of the diet, tooth {lb['tooth']:.1%}; by band " + ", ".join(f"{b} {row[f'land_{b}']:.0%}" for b in BANDS))
        print("  " + ", ".join(f"{k} {row[k]:.3g}" for k in ("pop", "pop_land", "pop_surface", "pop_bottom", "top_lineage", "blocked", "no_room",
                                                             "kills", "births_per_body", "size_mean", "sighted", "land_drift", "sea_drift", "ms_step")
                               + tuple(f"deaths_{c}" for c in CAUSES)))
    for arm in ("control", "sets"):
        rs = [r for r in out["runs"] if r["arm"] == arm]
        if not rs:
            continue
        keys = ("form_held", "form", "null_medium", "held_one_medium", "lineage_e060", "top_lineage", "pop", "pop_land", "pop_surface",
                "pop_bottom", "land_open", "land_fill", "land_hard", "land_blocks", "blocked", "kills", "ms_step")
        print(f"{arm} over seeds {' '.join(str(r['seed']) for r in rs)}: "
              + ", ".join(f"{k} {st.mean(r[k] for r in rs):.3g}" for k in keys))
    for name, rows in out.items():
        write(name, rows)
    print(f"wrote {', '.join(name + '.csv' for name in out)}")


if __name__ == "__main__":
    main()
