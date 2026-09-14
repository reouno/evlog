#!/usr/bin/env python3
"""The scale of cold (#86), with no runs: what the law would have cost the grown bodies of e070's censuses.

Run from the repo root: `uv run python experiments/e071_cold/dryrun.py` (about 20 seconds).
It reads the second half's censuses of e070's three runs (`c1225_life{9,10,11}_senses`) and prints the
temperature under the grown bodies by medium, the land's mean temperature over a year, and for a few body
temperatures the rate at which the median land body at the land's p10 loses its upkeep again, with what that
rate would take from each medium: `cold x open soft faces x max(0, warm - temp) x (1 - fat fill)` over the
upkeep, `0.002 x blocks + 0.032` a turn. The temperature is the cell under the middle of the body.
"""
import csv
import os

HERE = os.path.dirname(os.path.abspath(__file__))
E070 = os.path.join(os.path.dirname(HERE), "e070_senses", "results")
UPKEEP, UPKEEP_BODY = 0.002, 0.032
MEDIA = ("land", "surface", "bottom")


def q(v, p):
    v = sorted(v)
    return v[int((len(v) - 1) * p)] if v else float("nan")


def main():
    rows = []
    for s in (9, 10, 11):
        with open(os.path.join(E070, f"c1225_life{s}_senses_agents.csv")) as f:
            for r in csv.DictReader(f):
                if int(r["step"]) >= 50000 and int(r["age"]) >= 300:
                    size, mass = int(r["size"]), float(r["mass"])
                    rows.append({"step": int(r["step"]), "m": int(r["medium"]), "t": float(r["temp"]), "open": int(r["open_soft"]),
                                 "size": size, "up": UPKEEP * size + UPKEEP_BODY,
                                 "fill": min(float(r["fat"]) / max(float(r["store"]) * mass, 1e-6), 1.0)})
    print(f"grown bodies over the second half's censuses, seeds 9-11: {len(rows)}")
    for m, name in enumerate(MEDIA):
        rs = [r for r in rows if r["m"] == m]
        t = [r["t"] for r in rs]
        print(f"{name:8s} {len(rs):6d} bodies; temp p10 {q(t, .1):5.1f} p50 {q(t, .5):5.1f} p90 {q(t, .9):5.1f} C; "
              f"open soft faces per block {sum(r['open'] for r in rs) / sum(r['size'] for r in rs):.2f}, "
              f"a body's p50 {q([r['open'] for r in rs], .5)}; upkeep p50 {q([r['up'] for r in rs], .5):.3f}; fat fill p50 {q([r['fill'] for r in rs], .5):.3f}")
    with open(os.path.join(E070, "c1225_life9_senses_log.csv")) as f:
        year = [float(r["land_temp"]) for r in csv.DictReader(f) if 60000 < int(r["step"]) <= 80000]
    print(f"the land's mean temperature over a year (seed 9, steps 60,000-80,000): {min(year):.1f} to {max(year):.1f} C")
    land = [r for r in rows if r["m"] == 0]
    t10, o50, u50 = q([r["t"] for r in land], .1), q([r["open"] for r in land], .5), q([r["up"] for r in land], .5)
    for warm in (10, 20, 30, 37):
        rate = u50 / (o50 * (warm - t10))
        out = []
        for m, name in enumerate(MEDIA):
            rs = [r for r in rows if r["m"] == m]
            loss = [rate * r["open"] * max(0.0, warm - r["t"]) * (1 - r["fill"]) for r in rs]
            out.append(f"{name} pays {sum(v > 0 for v in loss) / len(rs):.0%}, takes {sum(loss) / sum(r['up'] for r in rs):.2f} of its upkeep")
        print(f"warm {warm} C: rate {rate:.3g} | " + " | ".join(out))


if __name__ == "__main__":
    main()
