#!/usr/bin/env python3
"""Read e087's runs (#93) against the done-when of P1, over the steps from FROM on.

For every run prefix (or every run in a directory):

1. **a winter lived through**: of the grown bodies (300 steps or older) standing on a seasonal cell whose
   winter starts, the share alive when it ends (`_months.csv`: lived / resolved), with their fat at the
   start in steps of fasting, how far the living went and the share of them on land fed that month;
2. **a year lived**: p50 and p90 of a grown body's age at death (`_grown.csv`), all and on seasonal land;
3. **the season changes what a body does**: torpid body-steps on seasonal land in its winter, all and grown,
   and the mean temperature there; the torpid share on the land always fed, for contrast;
4. **no harm**: kinds at a census and kinds kept to a place (e075's `read_run`, as e081 and e082), the
   largest lineage's share of the land's bodies at a census, bodies, deaths by cause and the ledger.

Besides: the dead by 75 steps as a share of the dead, and births on seasonal land by month of its winter
against the rest of the year.

Run from the repo root: `uv run python experiments/e087_torpor/read.py <dir or prefix> ...`
Writes `results/read_<first dir name>.csv`.
"""
import csv
import os
import statistics as st
import sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "experiments", "e075_hunt"))
import sweep as e075  # noqa: E402

FROM = 36000
CLASSES = ["sea", "fed", "seasonal", "never"]
CAUSES = ["hunger", "broken", "wear", "thirst", "suffocation", "cold", "wound"]


def quantile(v, q):
    v = sorted(v)
    return v[min(len(v) - 1, int(q * len(v)))] if v else float("nan")


def months(pre, start):
    with open(pre + "_months.csv") as f:
        rows = [r for r in csv.DictReader(f) if int(r["step"]) > start]
    s = lambda k: sum(float(r[k]) for r in rows)  # noqa: E731
    out = {
        "lived": s("lived") / max(s("resolved"), 1), "cohort": s("entered"),
        "fat_in": s("fat_in") / max(len([r for r in rows if float(r["entered"]) > 0]), 1),
        "moved": sum(float(r["moved"]) * float(r["lived"]) for r in rows) / max(s("lived"), 1),
        "fed_end": s("fed_end") / max(s("lived"), 1),
        "torpid_winter": s("winter_torpid") / max(s("winter"), 1),
        "torpid_winter_grown": s("winter_grown_torpid") / max(s("winter_grown"), 1),
        "temp_winter": sum(float(r["winter_temp"]) * float(r["winter"]) for r in rows) / max(s("winter"), 1),
        "torpid_fed": s("torpid_fed") / max(s("steps_fed"), 1),
        "torpid_seasonal": s("torpid_seasonal") / max(s("steps_seasonal"), 1),
        "young": sum(s(f"young_{c}") for c in CLASSES) / max(sum(s(f"deaths_{c}") for c in CLASSES), 1),
        "young_seasonal": s("young_seasonal") / max(s("deaths_seasonal"), 1),
        "bodies_seasonal": s("steps_seasonal") / max(sum(s(f"steps_{c}") for c in CLASSES), 1),
    }
    # Births on seasonal land by month of the year (the report's season profile).
    by = defaultdict(float)
    for r in rows:
        by[int(r["month"])] += float(r["births_seasonal"])
    out["births_by_month"] = "/".join(f"{by[m]:.0f}" for m in range(12))
    return out


def grown(pre, start):
    ages, seasonal, causes = [], [], Counter()
    with open(pre + "_grown.csv") as f:
        for r in csv.DictReader(f):
            if not r["travel"] or int(r["step"]) <= start:  # a run still writing ends mid-line
                continue
            a = int(r["age"])
            ages.append(a)
            if r["class"] == "2":
                seasonal.append(a)
            causes[CAUSES[int(r["cause"])]] += 1
    n = max(sum(causes.values()), 1)
    return {"grown_n": len(ages), "grown_p50": quantile(ages, 0.5), "grown_p90": quantile(ages, 0.9),
            "grown_p99": quantile(ages, 0.99), "grown_seasonal_p50": quantile(seasonal, 0.5),
            "grown_seasonal_p90": quantile(seasonal, 0.9),
            "grown_causes": " ".join(f"{c} {v / n:.0%}" for c, v in causes.most_common(4))}


def lines(pre):
    """The largest lineage's share of the land's bodies, per census, over the mean."""
    per = defaultdict(Counter)
    with open(pre + "_agents.csv") as f:
        for r in csv.DictReader(f):
            if int(r["step"]) >= FROM and r["medium"] == "0":
                per[r["step"]][r["lineage"]] += 1
    return {"top_share": st.mean(max(c.values()) / sum(c.values()) for c in per.values()) if per else float("nan")}


def log(pre, start):
    with open(pre + "_log.csv") as f:
        rows = [r for r in csv.DictReader(f) if int(r["step"]) > start]
    deaths = {c: sum(float(r[f"deaths_{c}"]) for r in rows) for c in CAUSES}
    n = max(sum(deaths.values()), 1)
    return {"pop": st.mean(float(r["pop"]) for r in rows), "pop_land": st.mean(float(r["pop_land"]) for r in rows),
            "pop_min": min(float(r["pop"]) for r in rows), "err": max(abs(float(r["matter_err"])) for r in rows),
            "births": st.mean(float(r["births"]) for r in rows), "last": int(rows[-1]["step"]) if rows else 0,
            **{f"d_{c}": deaths[c] / n for c in CAUSES}}


def prefixes(arg):
    if os.path.isdir(arg):
        return sorted(os.path.join(arg, f[: -len("_log.csv")]) for f in os.listdir(arg) if f.endswith("_log.csv"))
    return [arg]


def main():
    args = sys.argv[1:]
    start = FROM
    if args and args[0] == "--from":
        start, args = int(args[1]), args[2:]
    rows = []
    for arg in args:
        for pre in prefixes(arg):
            out = {"run": os.path.basename(pre)}
            out.update(log(pre, start))
            if os.path.exists(pre + "_months.csv"):
                out.update(months(pre, start))
                out.update(grown(pre, start))
            try:
                k, _ = e075.read_run(out["run"], pre)
                out.update({x: k[x] for x in ("kinds_at", "placed_at", "travel")})
                out.update(lines(pre))
            except Exception as e:  # no census from FROM yet
                print(f"{pre}: no kinds ({e})", file=sys.stderr)
            rows.append(out)
    g = lambda r, k, f: format(r[k], f) if k in r else "-"  # noqa: E731
    print(f"{'run':>24} {'step':>6} {'bodies':>6} {'land':>5} {'lived':>5} {'cohort':>6} {'fat':>5} {'moved':>5} {'fed':>4}"
          f" {'grown p50/p90':>13} {'torpid w':>8} {'grown':>5} {'T w':>5} {'fed':>5} {'young':>5}"
          f" {'hunger':>6} {'thirst':>6} {'cold':>5} {'kinds':>5} {'place':>5} {'top':>4} {'trav':>5} {'err':>7}")
    for r in rows:
        print(f"{r['run']:>24} {r['last']:>6} {r['pop']:>6.0f} {r['pop_land']:>5.0f} {g(r, 'lived', '.1%'):>5} {g(r, 'cohort', '.0f'):>6}"
              f" {g(r, 'fat_in', '.0f'):>5} {g(r, 'moved', '.1f'):>5} {g(r, 'fed_end', '.0%'):>4}"
              f" {g(r, 'grown_p50', '.0f'):>6}/{g(r, 'grown_p90', '.0f'):<6} {g(r, 'torpid_winter', '.1%'):>8} {g(r, 'torpid_winter_grown', '.0%'):>5}"
              f" {g(r, 'temp_winter', '.1f'):>5} {g(r, 'torpid_fed', '.1%'):>5} {g(r, 'young', '.0%'):>5}"
              f" {r['d_hunger']:>6.0%} {r['d_thirst']:>6.0%} {r['d_cold']:>5.1%} {g(r, 'kinds_at', '.2f'):>5} {g(r, 'placed_at', '.2f'):>5}"
              f" {g(r, 'top_share', '.0%'):>4} {g(r, 'travel', '.1f'):>5} {r['err']:>7.1e}")
    if rows and args and os.path.isdir(args[0]):
        out = os.path.join(HERE, "results", f"read_{os.path.basename(os.path.normpath(args[0]))}.csv")
        keys = sorted(set().union(*rows))
        with open(out, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["run"] + [k for k in keys if k != "run"])
            w.writeheader()
            w.writerows(rows)


if __name__ == "__main__":
    main()
