"""#91 step 0: e075's censuses (every 10,000 steps) fall at ten phases of the year; land bodies by phase."""
import csv, statistics as st
from pathlib import Path
LADDER = Path(__file__).parent.parent / "e075_hunt/results/ladder"
YEAR = 11880
for seed in [9, 10, 11]:
    by = {}
    with open(LADDER / f"c1225_life{seed}_both_agents.csv") as f:
        for r in csv.DictReader(f):
            by.setdefault(int(r["step"]), []).append(r)
    print(f"\nseed {seed}   step   phase  land  sea   temp p10/50/90   <15C  >30C  hab cold/mild/hot  moist p50  age p50  warmed/cooled a life")
    for s in sorted(by):
        if s < 20000: continue
        land = [r for r in by[s] if r["medium"] == "0"]
        t = sorted(float(r["temp"]) for r in land)
        q = lambda p: t[int(p * (len(t) - 1))]
        hab = [int(r["place"]) for r in land]
        cold = sum(h < 3 for h in hab); mild = sum(3 <= h < 6 for h in hab); hot = sum(6 <= h < 9 for h in hab)
        w = st.mean(float(r["warmed"]) for r in land); c = st.mean(float(r["cooled"]) for r in land)
        print(f"{'':9}{s:6} {((s)/YEAR)%1:6.2f} {len(land):5} {len(by[s])-len(land):5}  {q(.1):5.1f}{q(.5):5.1f}{q(.9):5.1f}"
              f"  {sum(x<15 for x in t)/len(t):5.2f} {sum(x>30 for x in t)/len(t):5.2f}   {cold:5}{mild:5}{hot:5}"
              f"   {st.median(float(r['moist']) for r in land):6.2f} {st.median(int(r['age']) for r in land):6}  {w:7.2f} {c:7.2f}")
