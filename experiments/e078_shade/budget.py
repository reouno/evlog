#!/usr/bin/env python3
"""The land's budget by place and season, on e078's control (seed 9, steps 36,000-60,000), for #91's design.

Run from the repo root: `uv run python experiments/e078_shade/budget.py`. No runs.

- Water, per land body a turn, in units of its fill: what it drinks from the ground (estimated as
  drink 0.1 x fresh 0.05 x the ground's fill under it; a pool gives 20 times that), what it pays to cool
  (`cooled` over `turns`), and what the dry air takes (estimated as dry 0.004 x (1 - fill) x its open
  soft faces over its blocks). Also its fill, its temperature, the energy it pays to warm, its median age.
- Food, per cell and per body, from `bands.csv`: grass grown and the crowns' browse (3e-5 x wood a step)
  per 1,000 steps, and bodies a cell.

Zones by |latitude|: tropics under 20, mid 20-50, high 50 and up. Seasons by hemisphere.
"""
import csv
import os
import statistics as st
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
PRE = os.path.join(HERE, "results", "search", "c1225_life9_h0d0")
YEAR = 11880
N, LAT_LO, LAT_HI = 512, -59.4, 87.0
CLASS = {0: "lawn", 1: "thin", 2: "stand"}


def lat_of(cell):
    return LAT_LO + (LAT_HI - LAT_LO) * (1 - abs(2 * ((cell // N) + 0.5) / N - 1))


def season(step, north):
    q = int(((step / YEAR + 0.125) % 1.0) * 4)  # 1: the north's summer, 3: its winter
    return {1: "summer", 3: "winter"}.get(q, "sp/au") if north else {3: "summer", 1: "winter"}.get(q, "sp/au")


def zone(lat):
    return "trop" if abs(lat) < 20 else "mid" if abs(lat) < 50 else "high"


def water():
    acc = defaultdict(list)
    with open(PRE + "_agents.csv") as f:
        for r in csv.DictReader(f):
            if r["medium"] != "0":
                continue
            lat, w = lat_of(int(r["cell"])), float(r["crown"])
            acc[(zone(lat), CLASS[0 if w < 0.1 else 1 if w < 1 else 2], season(int(r["step"]), lat >= 0))].append(r)
    print(f"{'zone':5}{'class':6}{'season':7}{'bodies':>7}{'fill':>6}{'temp':>6}{'ground':>7}  {'drink':>7}{'cool':>7}{'dry':>7}  {'warm':>7}{'age':>5}")
    for k in sorted(acc):
        v = acc[k]
        mean = lambda c: st.mean(float(r[c]) for r in v)  # noqa: E731
        per_turn = lambda c: st.mean(float(r[c]) / max(1, int(r["turns"])) for r in v)  # noqa: E731
        dry = st.mean(0.004 * (1 - float(r["moist"])) * int(r["open_soft"]) / max(1, int(r["size"])) for r in v)
        print(f"{k[0]:5}{k[1]:6}{k[2]:7}{len(v):7}{mean('water'):6.2f}{mean('btemp'):6.1f}{mean('moist'):7.2f}  "
              f"{0.1 * 0.05 * mean('moist'):7.4f}{per_turn('cooled'):7.4f}{dry:7.4f}  {per_turn('warmed'):7.4f}{st.median(int(r['age']) for r in v):5.0f}")


def food():
    acc = defaultdict(lambda: [0.0] * 4)
    with open(PRE + "_bands.csv") as f:
        for r in csv.DictReader(f):
            s = int(r["step"])
            if s <= 12000:
                continue
            lat = int(r["lat"]) + 5  # the band's middle
            v = acc[(zone(lat), CLASS[int(r["wood_class"])], season(s - 500, lat >= 0))]
            for i, c in enumerate(("grown", "cells", "wood", "bodies")):
                v[i] += float(r[c])
    print(f"\n{'zone':5}{'class':6}{'season':7}{'grass/cell':>11}{'browse/cell':>12}{'bodies/cell':>12}{'food/body':>10}   (per 1,000 steps)")
    for k in sorted(acc):
        g, c, w, b = acc[k]
        print(f"{k[0]:5}{k[1]:6}{k[2]:7}{g / c:11.3f}{0.03 * w / c:12.3f}{b / c:12.3f}{(g + 0.03 * w) / max(b, 1):10.2f}")


water()
food()
