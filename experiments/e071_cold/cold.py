#!/usr/bin/env python3
"""Cold (#86): e071's runs (`cold = 0.000125`) against e070's runs on the same seeds (no cold).

Run from the repo root: `uv run python experiments/e071_cold/cold.py` (about a minute on one core).
It reads the second half's censuses of every run, counts kinds by birth form with e068's `kinds.py`, reads the
grown bodies' blocks and fat by medium and by temperature band (e061's cold, mild and hot, of the habitat under
them), prints the numbers and writes `results/*.csv`.
"""
import csv
import os
import statistics as st
import sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "experiments", "e068_kinds"))
sys.path.insert(0, os.path.join(ROOT, "experiments", "e070_senses"))
import kinds  # noqa: E402  (e068's census by birth form; it imports e060's census)
import senses  # noqa: E402  (e070's reading of the sensor blocks)

census = kinds.census
SEEDS = (9, 10, 11)
PRE = {"control": lambda s: os.path.join(ROOT, "experiments", "e070_senses", "results", f"c1225_life{s}_senses"),
       "cold": lambda s: os.path.join(HERE, "results", f"c1225_life{s}_cold")}
RUNS = [(f"{arm}{s}", s, arm, PRE[arm](s)) for s in SEEDS for arm in ("control", "cold")]
CAUSES = ("hunger", "broken", "wear", "thirst", "suffocation", "cold")
BANDS = ("cold", "mild", "hot")
UPKEEP, UPKEEP_BODY = 0.002, 0.032
# Written in the README before the runs.
OPEN_LINE, FILL_LINE = 0.87 - 0.1, 1.5 * 0.069


def band(r):
    h = int(r["place"])
    return BANDS[h // 3 if h < 9 else (h - 9) % 3]


def fill(r):
    return min(float(r["fat"]) / max(float(r["store"]) * float(r["mass"]), 1e-6), 1.0)


def bodies(rows):
    """Grown bodies' blocks, fat and cold: open soft faces and hard blocks per block, the fat's median fill, blocks,
    the median temperature under them, and the energy lost to cold over the upkeep of their turns."""
    n, size = max(len(rows), 1), max(sum(int(r["size"]) for r in rows), 1)
    upkeep = sum(int(r["turns"]) * (UPKEEP * int(r["size"]) + UPKEEP_BODY) for r in rows)
    return {"bodies": len(rows), "open": sum(int(r["open_soft"]) for r in rows) / size, "hard": sum(int(r["hard"]) for r in rows) / size,
            "fat_fill": st.median(fill(r) for r in rows) if rows else float("nan"), "blocks": size / n,
            "born_blocks": sum(int(r["born_size"]) for r in rows) / n, "temp": st.median(float(r["temp"]) for r in rows) if rows else float("nan"),
            "cold_share": sum(float(r.get("chilled", 0)) for r in rows) / max(upkeep, 1e-12)}


def log_half(pre):
    with open(pre + "_log.csv") as f:
        rows = list(csv.DictReader(f))
    last = int(rows[-1]["step"])
    late = [r for r in rows if 2 * int(r["step"]) > last]
    col = lambda k: [float(r.get(k, 0) or 0) for r in late]
    deaths = {c: sum(col(f"deaths_{c}")) for c in CAUSES}
    total = max(sum(deaths.values()), 1)
    out = {"steps": last, "pop": st.mean(col("pop")), "pop_min": min(col("pop")), "pop_end": float(rows[-1]["pop"]),
           "lineages": st.mean(col("lineages")), "top_lineage": st.mean(col("top_lineage")),
           "births_per_body": 1000 * sum(col("births")) / sum(col("pop")) / 1000,
           "blocked": st.mean(col("blocked")), "no_room": sum(col("no_room")) / max(sum(col("no_room")) + sum(col("births")), 1),
           "kills": (sum(col("meat_intake")) - sum(col("scavenged"))) / (sum(col("plant_intake")) + sum(col("meat_intake"))),
           "size_mean": st.mean(col("size_mean")), "ms_step": st.mean(col("ms_step")),
           **{f"pop_{m}": st.mean(col(f"pop_{m}")) for m in kinds.MEDIA},
           **{f"logcold_{m}": st.mean(col(f"cold_{m}")) for m in kinds.MEDIA},
           **{f"logfat_{m}": st.mean(col(f"fat_{m}")) for m in kinds.MEDIA},
           **{f"logopen_{m}": st.mean(col(f"open_{m}")) for m in kinds.MEDIA}}
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
               **{f"land_{b}": sum(band(r) == b for r in land) / max(len(land), 1) for b in BANDS}}
        row |= senses.senses_of(run.grown) | log_half(pre)
        out["runs"].append(row)
        for m, medium in enumerate(kinds.MEDIA):
            out["media"].append({"run": name, "seed": seed, "arm": arm, "medium": medium} | bodies([r for r in run.grown if r["medium"] == str(m)]))
        for b in BANDS:
            out["bands"].append({"run": name, "seed": seed, "arm": arm, "band": b} | bodies([r for r in land if band(r) == b]))
        for step, rs in census.read(pre + "_agents.csv").items():
            g = census.grown(rs)
            gl = [r for r in g if r["medium"] == "0"]
            out["time"].append({"run": name, "seed": seed, "arm": arm, "step": step, "kinds": len(per[step]) if step in per else "",
                                "land_open": bodies(gl)["open"], "land_fill": bodies(gl)["fat_fill"] if gl else "",
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
            b = bodies(ms)
            out["kinds"].append(k | {"seed": seed, "arm": arm, "open_now": b["open"], "hard_now": b["hard"], "fat_fill": b["fat_fill"],
                                     "cold_share": b["cold_share"], **{f"band_{x}": where[x] / max(len(ms), 1) for x in BANDS}})
        print(f"{name}: grown {row['grown']:.0f}, kinds by form {row['form']:.2f} [{row['form_low']}-{row['form_high']}] held {row['form_held']} "
              f"(medium shuffled {nm:.2f}/{nm_held:.1f}), lineage {row['lineage_e060']:.2f}; stood {row['steps']} steps, low {row['pop_min']:.0f}")
        print(f"  held in one medium: {row['held_one_medium']} ({row['one_medium']}); land open/block {lb['open']:.3f}, fat fill {lb['fat_fill']:.3f}, "
              f"hard {lb['hard']:.3f}, blocks {lb['blocks']:.1f}, cold share {lb['cold_share']:.3f}; land by band "
              + ", ".join(f"{b} {row[f'land_{b}']:.0%}" for b in BANDS))
        print("  " + ", ".join(f"{k} {row[k]:.3g}" for k in ("pop", "pop_land", "pop_surface", "pop_bottom", "top_lineage", "blocked", "no_room", "kills",
                                                              "births_per_body", "size_mean", "sighted", "ms_step", "logcold_land", "logcold_surface", "logcold_bottom")
                                + tuple(f"deaths_{c}" for c in CAUSES)))
    for arm in ("control", "cold"):
        rs = [r for r in out["runs"] if r["arm"] == arm]
        if not rs:
            continue
        a = {"arm": arm, "seeds": " ".join(str(r["seed"]) for r in rs)}
        a |= {k: st.mean(r[k] for r in rs) for k in ("form_held", "form", "null_medium", "lineage_e060", "top_lineage", "pop", "pop_land",
                                                    "land_open", "land_fill", "land_hard", "land_blocks", "held_one_medium", "sighted")}
        out["arms"].append(a)
        print(f"{arm:7s} seeds {a['seeds']}: kinds held {a['form_held']:.2f} ({', '.join(str(r['form_held']) for r in rs)}), at a census {a['form']:.2f}, "
              f"medium shuffled {a['null_medium']:.2f}, per lineage {a['lineage_e060']:.2f}; land open {a['land_open']:.3f} fill {a['land_fill']:.3f}")
    c = [r for r in out["runs"] if r["arm"] == "cold"]
    if c:
        print("verdicts: stands " + ", ".join(f"{r['seed']}:{r['steps'] == 100000 and r['pop_min'] > 0}" for r in c)
              + f"; 1 land open <= {OPEN_LINE:.2f} or fill >= {FILL_LINE:.3f}: " + ", ".join(f"{r['land_open']:.3f}/{r['land_fill']:.3f}" for r in c)
              + "; 2 a held kind in one medium: " + ", ".join(str(r["held_one_medium"]) for r in c)
              + f"; 3 mean held {st.mean(r['form_held'] for r in c):.2f} (>= 3.0)")
    for name, rows in out.items():
        write(name, rows)
    print("wrote " + ", ".join(f"results/{n}.csv" for n in out))


if __name__ == "__main__":
    main()
