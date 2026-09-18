"""#91 step 0: e075's kept runs read by season (no runs). Does the season take the lawn away (A)?

The bodies start on a whole year of the climate, so a step's phase in the year is step / year.
"""
import csv, math, sys
from pathlib import Path

LADDER = Path(__file__).parent.parent / "e075_hunt/results/ladder"
YEAR = 11880
SEEDS = [9, 10, 11]
FROM = 20000  # past the start's transient

def rows(seed):
    with open(LADDER / f"c1225_life{seed}_both_log.csv") as f:
        return [{k: float(v) for k, v in r.items()} for r in csv.DictReader(f)]

def quarter(step):
    # the log's row sums the 1,000 steps before it: its middle is step - 500
    ph = ((step - 500) / YEAR) % 1.0
    return int(((ph + 0.125) % 1.0) * 4)  # 0: around phase 0 (rising), 1: 0.25 (north's summer), ...

NAMES = ["spring (ph 0)", "summer (ph .25)", "autumn (ph .5)", "winter (ph .75)"]
COLS = ["land_temp", "grass", "grass_grown", "wood", "browse", "pop_land", "pop_surface", "pop_bottom",
        "intake_land", "browse_intake", "kills_land", "deaths_hunger", "deaths_thirst", "deaths_cold",
        "deaths_wound", "births", "pop_cold", "pop_mild", "pop_hot"]

for seed in SEEDS:
    rs = [r for r in rows(seed) if r["step"] > FROM]
    print(f"\nseed {seed}: {len(rs)} rows")
    print(f"{'':16}" + "".join(f"{c[:13]:>14}" for c in COLS))
    for q in range(4):
        sel = [r for r in rs if quarter(r["step"]) == q]
        print(f"{NAMES[q]:16}" + "".join(f"{sum(r[c] for r in sel)/len(sel):14.4g}" for c in COLS))
    # the swing, high quarter over low quarter, for a few
    for c in ["grass_grown", "pop_land", "intake_land", "land_temp"]:
        m = [sum(r[c] for r in rs if quarter(r["step"]) == q) / max(1, sum(1 for r in rs if quarter(r["step"]) == q)) for q in range(4)]
        print(f"  {c}: max/min over quarters {max(m)/min(m):.2f}" if min(m) > 0 else f"  {c}: {m}")
