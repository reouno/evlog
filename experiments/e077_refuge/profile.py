"""#91 step 0: the year in twelve bins of phase, seeds 9-11 pooled, steps 20,000-100,000 of e075's kept runs."""
import csv
from pathlib import Path
LADDER = Path(__file__).parent.parent / "e075_hunt/results/ladder"
YEAR, BINS = 11880, 12
COLS = ["land_temp", "temp_day_land", "grass_grown", "grass", "pop_land", "pop_surface", "pop_bottom", "intake_land",
        "deaths_hunger", "deaths_thirst", "deaths_cold", "deaths_wound", "births", "warm_land", "cool_land", "drinking_land"]
acc = [[0.0] * len(COLS) for _ in range(BINS)]; n = [0] * BINS
for seed in [9, 10, 11]:
    with open(LADDER / f"c1225_life{seed}_both_log.csv") as f:
        for r in csv.DictReader(f):
            s = int(r["step"])
            if s <= 20000: continue
            b = int((((s - 500) / YEAR) % 1.0) * BINS)
            n[b] += 1
            for i, c in enumerate(COLS):
                acc[b][i] += float(r[c])
print("phase " + "".join(f"{c[:11]:>12}" for c in COLS))
for b in range(BINS):
    print(f"{(b + .5) / BINS:5.2f} " + "".join(f"{v / n[b]:12.4g}" for v in acc[b]) + f"  n={n[b]}")
