#!/usr/bin/env python3
"""e094 (#106): why no way of living lasts. No runs - this reads twelve finished censuses.

Run from the repo root: `uv run python experiments/e094_hold/hold.py` (about ten minutes on one core).

The six-seed control ladder and e093's six. A run writes a census - every living body, a row each - every
1,000 steps from 36,000; e068's reader takes the second half of them by step, so what is read here is the
51 censuses from 50,000 to 100,000 (50,000 steps, 4.2 years at a year of 11,880, about 93 grown lifetimes). e068's reading is kept exactly: a grown body's form is (lineage, birth
signature), a form's way of living is read over all its grown bodies in the run, and a kind is a way
holding 5% of the grown bodies at a census. So a kind's label never moves; what moves is how many
bodies its forms have at a census.

It writes, per run:
  census.csv  a row a census: kinds, grown bodies, the largest lineage and its share
  spells.csv  a row a stretch of consecutive censuses in which one way held 5%
  events.csv  a row a stretch that ended before the run did, with what became of its forms
  holds.csv   a row a run: the summary, the nulls and the counts at other lines
"""
import csv
import os
import statistics as st
import sys
from collections import Counter, defaultdict

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "experiments", "e068_kinds"))
import kinds  # noqa: E402

SHARE = 0.05      # of the grown bodies: e060's line for a kind
LINES = (0.03, 0.05, 0.10)  # the line, and what a looser and a tighter one would count
ALMOST = 0.9      # "held" loosened: a kind at the line in this share of the censuses
DRAWS = 20        # bootstrap draws a census for the null
GONE = 0.2        # a kind's forms count as gone when this little of their bodies is left
YEAR = 11880.0    # steps (e061's c1225)
LIFE = 535.0      # steps: a grown body's life in this world (e087)

RUNS = [(f"control {s}", os.path.join(ROOT, "experiments", "e081_drink" if s < 12 else "e092_yardstick",
                                      "results", "ladder", f"c1225_life{s}_" + ("u0" if s < 12 else "ctl")))
        for s in (9, 10, 11, 12, 13, 14)]
RUNS += [(f"light {s}", os.path.join(ROOT, "experiments", "e093_leaf", "results", "batch",
                                     f"c1225_life{s}_g0.016")) for s in (9, 10, 11, 12, 13, 14)]


def spells(flags):
    """The maximal stretches of True in `flags`, as (start index, end index inclusive)."""
    out, i = [], 0
    while i < len(flags):
        if flags[i]:
            j = i
            while j + 1 < len(flags) and flags[j + 1]:
                j += 1
            out.append((i, j))
            i = j + 1
        else:
            i += 1
    return out


def by_quarter(steps, share):
    """The share of a series' variance that lies between the four quarters of the year (e061's 11,880
    steps): 1 would mean the swing is the season and nothing else, 0 that the season says nothing."""
    q = defaultdict(list)
    for s, v in zip(steps, share):
        q[int((s % YEAR) / YEAR * 4)].append(v)
    total = st.pvariance(share)
    if total <= 0 or len(q) < 2:
        return 0.0
    mean = st.mean(share)
    between = sum(len(v) * (st.mean(v) - mean) ** 2 for v in q.values()) / len(share)
    return between / total


def read(name, pre):
    run = kinds.Run(name, pre)
    unit = run.forms()
    ways = kinds.by_group(run, unit, run.does())
    steps = list(run.steps)
    # Per census: the bodies of each way and of each form, and the largest lineage.
    by_way = [Counter(ways[unit[i]] for i in run.at[s]) for s in steps]
    by_form = [Counter(unit[i] for i in run.at[s]) for s in steps]
    grown = [sum(c.values()) for c in by_way]
    top = [Counter(run.grown[i]["lineage"] for i in run.at[s]).most_common(1)[0] for s in steps]
    forms_of = defaultdict(set)
    for u, w in ways.items():
        forms_of[w].add(u)

    census = [{"run": name, "step": s, "grown": g,
               "kinds": sum(v >= SHARE * g for v in c.values()),
               "top_lineage": t[0], "top_share": t[1] / max(g, 1)}
              for s, c, g, t in zip(steps, by_way, grown, top)]

    # 1. How long a way holds the line, and what happened when it stopped.
    sp, ev = [], []
    for w in forms_of:
        flags = [c[w] >= SHARE * g for c, g in zip(by_way, grown)]
        for a, b in spells(flags):
            sp.append({"run": name, "way": " / ".join(w), "from": steps[a], "to": steps[b],
                       "censuses": b - a + 1, "steps": steps[b] - steps[a] + 1000,
                       "whole": int(a == 0 and b == len(steps) - 1),
                       "share_max": max(by_way[i][w] / max(grown[i], 1) for i in range(a, b + 1)),
                       "share_min": min(by_way[i][w] / max(grown[i], 1) for i in range(a, b + 1))})
            if b == len(steps) - 1:
                continue
            # The census after the stretch: where did the way's bodies go?
            before, after = by_form[b], by_form[b + 1]
            mine = [u for u in forms_of[w] if before[u] > 0]
            was = sum(before[u] for u in mine)
            now = sum(after[u] for u in mine)
            back = any(by_way[i][w] >= SHARE * grown[i] for i in range(b + 1, len(steps)))
            ev.append({"run": name, "way": " / ".join(w), "at": steps[b + 1], "forms": len(mine),
                       "forms_left": sum(after[u] > 0 for u in mine),
                       "share_before": was / max(grown[b], 1), "share_after": now / max(grown[b + 1], 1),
                       "kept": now / max(was, 1), "comes_back": int(back),
                       "why": "forms gone" if now < GONE * was else "under the line",
                       "top_changed": int(top[b][0] != top[b + 1][0])})

    # 2. The same for a form: how long one birth form holds 5% of the grown bodies.
    form_sp = []
    for u in {u for c in by_form for u in c}:
        flags = [c[u] >= SHARE * g for c, g in zip(by_form, grown)]
        for a, b in spells(flags):
            form_sp.append(b - a + 1)

    # 3. The null: resample each census's grown bodies with replacement and count again. This is what
    #    the measure makes on its own when nothing about the world changes.
    rng = np.random.default_rng(7)
    null_at, null_held = [], []
    for _ in range(DRAWS):
        per = []
        for c, g in zip(by_way, grown):
            keys = list(c)
            n = rng.multinomial(g, [c[k] / max(g, 1) for k in keys])
            per.append({k for k, v in zip(keys, n) if v >= SHARE * g})
        null_at.append(st.mean(len(p) for p in per))
        null_held.append(len(set.intersection(*per)))

    # 4. What other lines would count.
    lines = {}
    for line in LINES:
        per = [{w for w, v in c.items() if v >= line * g} for c, g in zip(by_way, grown)]
        lines[f"at_{line:g}"] = st.mean(len(p) for p in per)
        lines[f"held_{line:g}"] = len(set.intersection(*per))
        seen = Counter(w for p in per for w in p)
        lines[f"almost_{line:g}"] = sum(v >= ALMOST * len(per) for v in seen.values())

    ended = [e for e in ev]
    row = {"run": name, "censuses": len(steps), "grown_med": st.median(grown),
           "kinds_at": st.mean(c["kinds"] for c in census), "kinds_held": lines["held_0.05"],
           # What the world holds in the mean, instead of at every census: a way's share over the run.
           "ways_mean5": sum(st.mean(c[w] / max(g, 1) for c, g in zip(by_way, grown)) >= SHARE for w in forms_of),
           "share_cv": st.median([st.pstdev(v) / st.mean(v) for w in forms_of
                                  for v in [[c[w] / max(g, 1) for c, g in zip(by_way, grown)]] if st.mean(v) > 0.01]),
           # Is the swing the year? The share of a way's variance that lies between the year's quarters.
           "season": st.median([by_quarter(steps, v) for w in forms_of
                                for v in [[c[w] / max(g, 1) for c, g in zip(by_way, grown)]] if st.mean(v) > 0.03]),
           "ways_seen": len({w for c, g in zip(by_way, grown) for w, v in c.items() if v >= SHARE * g}),
           "spell_med": st.median(s["censuses"] for s in sp) if sp else 0,
           "spell_p90": (sorted(s["censuses"] for s in sp)[int(0.9 * (len(sp) - 1))] if sp else 0),
           "spell_whole": sum(s["whole"] for s in sp),
           "form_spell_med": st.median(form_sp) if form_sp else 0,
           "ends": len(ended),
           "ends_forms_gone": sum(e["why"] == "forms gone" for e in ended),
           "ends_come_back": sum(e["comes_back"] for e in ended),
           "ends_top_changed": sum(e["top_changed"] for e in ended),
           "top_changes": sum(top[i][0] != top[i + 1][0] for i in range(len(top) - 1)),
           "null_at": st.mean(null_at), "null_held": st.mean(null_held), **lines}
    shares = [{"run": name, "step": st_, "way": " / ".join(w), "share": c[w] / max(g, 1)}
              for w in forms_of for st_, c, g in zip(steps, by_way, grown)
              if st.mean(cc[w] / max(gg, 1) for cc, gg in zip(by_way, grown)) >= 0.03]
    return row, census, sp, ev, shares


def main():
    rows, censuses, sps, evs, shares = [], [], [], [], []
    for name, pre in RUNS:
        if not os.path.exists(pre + "_agents.csv"):
            print(f"{name}: no census at {pre}_agents.csv (restore it with zstd -d)")
            continue
        row, census, sp, ev, sh = read(name, pre)
        rows.append(row)
        censuses += census
        sps += sp
        evs += ev
        shares += sh
        print(f"{name}: {row['kinds_at']:.2f} kinds at a census, {row['kinds_held']} held, "
              f"spells {row['spell_med']:.0f} censuses (p90 {row['spell_p90']:.0f}), "
              f"{row['ends']} ends of which {row['ends_forms_gone']} lost their forms, "
              f"null held {row['null_held']:.1f}")
    if not rows:
        return
    for name, data in (("holds", rows), ("census", censuses), ("spells", sps), ("events", evs), ("shares", shares)):
        with open(os.path.join(HERE, "results", f"{name}.csv"), "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(data[0]))
            w.writeheader()
            w.writerows(data)

    def med(k):
        return st.median(r[k] for r in rows)
    print(f"\n{'measure':<44}{'control':>10}{'light':>10}{'all':>10}")
    for k, label, fmt in [("kinds_at", "kinds at a census", "{:.2f}"), ("kinds_held", "held at every census", "{:.1f}"),
                          ("ways_seen", "ways that ever hold the line", "{:.0f}"),
                          ("spell_med", "censuses a way holds it (median)", "{:.0f}"),
                          ("spell_p90", "the same, p90", "{:.0f}"),
                          ("form_spell_med", "censuses a form holds it (median)", "{:.0f}"),
                          ("null_at", "kinds at a census, resampled", "{:.2f}"),
                          ("null_held", "held at every census, resampled", "{:.1f}"),
                          ("at_0.03", "kinds at a census, line 3%", "{:.2f}"), ("held_0.03", "held, line 3%", "{:.1f}"),
                          ("almost_0.05", "held in 90% of censuses, line 5%", "{:.1f}"),
                          ("almost_0.03", "held in 90% of censuses, line 3%", "{:.1f}"),
                          ("at_0.1", "kinds at a census, line 10%", "{:.2f}"), ("held_0.1", "held, line 10%", "{:.1f}"),
                          ("ways_mean5", "ways at 5% of the grown bodies in the mean", "{:.1f}"),
                          ("share_cv", "how far a way's share swings (sd over mean)", "{:.2f}"),
                          ("season", "of that swing, what the year explains", "{:.2f}"),
                          ("top_changes", "changes of the largest lineage", "{:.0f}")]:
        c = st.median(r[k] for r in rows if r["run"].startswith("control"))
        l = st.median(r[k] for r in rows if r["run"].startswith("light"))
        print(f"{label:<44}{fmt.format(c):>10}{fmt.format(l):>10}{fmt.format(med(k)):>10}")
    why = Counter(e["why"] for e in evs)
    print(f"\n{len(evs)} ends of a stretch: {dict(why)}; "
          f"{sum(e['comes_back'] for e in evs)} come back later; "
          f"{sum(e['top_changed'] for e in evs)} fall on a change of the largest lineage")
    steps = [s["steps"] for s in sps]
    print(f"a stretch lasts {st.median(steps):,.0f} steps at the median "
          f"({st.median(steps) / YEAR:.2f} years, {st.median(steps) / LIFE:.0f} grown lifetimes)")


if __name__ == "__main__":
    main()
