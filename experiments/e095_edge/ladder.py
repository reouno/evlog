#!/usr/bin/env python3
"""The two rate ladders of e095 (#107): what `spike` and `leg` buy, read off the logs alone.

Run from the repo root: `uv run python experiments/e095_edge/ladder.py` (seconds).

One row a run: the four rates of each law on seed 9 and the control's own row at the same step
(e081's ladder, seed 9, which this crate reproduces bit for bit with both laws off). Every number is
the mean over the run's second half, so a rate is read after the world has settled under it and not
in the ungrazed transient a run starts in (e037).
"""
import csv
import os
import statistics as st
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
LADDERS = [("spike", "s", ["0.5", "1", "2", "4", "8"]), ("leg", "k", ["0.25", "0.5", "1", "2", "4"])]
CTL = os.path.join(ROOT, "experiments", "e081_drink", "results", "ladder", "c1225_life9_u0")
COLS = [("pop", "bodies", "{:.0f}"), ("size_mean", "blocks a body", "{:.1f}"),
        ("hard_mean", "hard blocks", "{:.2f}"), ("muscle_mean", "muscle blocks", "{:.2f}"),
        ("digestive_mean", "gut blocks", "{:.1f}"),
        ("spike_mean", "spikes a body", "{:.2f}"), ("spiked", "grown bodies with one", "{:.1%}"),
        ("sharp_share", "flesh taken through a spike", "{:.1%}"),
        ("sharp_broke", "blocks broken by a spike", "{:.1%}"),
        ("leg_mean", "leg blocks", "{:.2f}"), ("leg_open", "their open faces", "{:.2f}"),
        ("leg_led", "grown bodies the legs move", "{:.1%}"),
        ("speed_mean", "motor (chance a sub-cell)", "{:.3f}"), ("travel_p50", "travel in a life", "{:.2f}"),
        ("open_mean", "open faces a body", "{:.1f}"), ("kills_share", "kills' share of intake", "{:.1%}"),
        ("per_cell", "bodies a cell held", "{:.2f}"), ("no_room", "births with no room", "{:.1%}"),
        ("blocked", "moves blocked", "{:.1%}"), ("lineages", "lineages", "{:.0f}")]


def census_at(pre, step):
    """The control has no `open_mean` or `per_cell` column (they are e093's); both are read off its
    census instead, at the step the ladders' runs end on. `tidy.py` keeps the censuses compressed."""
    path = pre + "_agents.csv"
    if os.path.exists(path):
        text = open(path).read()
    else:
        text = subprocess.run(["zstd", "-dc", path + ".zst"], capture_output=True, text=True).stdout
    rows = [r for r in csv.DictReader(text.splitlines()) if int(r["step"]) == step]
    if not rows:
        return {}
    return {"open_mean": st.mean(float(r["open_soft"]) for r in rows),
            "per_cell": len(rows) / max(len({r["cell"] for r in rows}), 1)}


def read(path, upto=None):
    with open(path) as f:
        rows = [r for r in csv.DictReader(f) if upto is None or int(r["step"]) <= upto]
    if not rows:
        return None
    last = int(rows[-1]["step"])
    half = [r for r in rows if int(r["step"]) >= last / 2]
    out = {"step": last}
    for k, _, _ in COLS:
        if k in ("no_room", "blocked", "kills_share"):
            continue
        out[k] = st.mean(float(r[k]) for r in half) if k in half[0] else 0.0
    born = sum(float(r["births"]) + float(r["no_room"]) for r in half)
    out["no_room"] = sum(float(r["no_room"]) for r in half) / max(born, 1)
    moves = sum(float(r["forward"]) + float(r["left"]) + float(r["right"]) for r in half)
    out["blocked"] = sum(float(r["blocked"]) for r in half) / max(moves, 1)
    meat = sum(float(r["meat_intake"]) for r in half)
    out["kills_share"] = meat / max(meat + sum(float(r["plant_intake"]) for r in half), 1e-9)
    return out


def main():
    ctl = read(CTL + "_log.csv", upto=40000)
    ctl.update(census_at(CTL, 40000))
    out = []
    for law, tag, rates in LADDERS:
        runs = [("control", ctl)]
        for r in rates:
            p = os.path.join(HERE, "results", f"c1225_life9_{tag}{r}_log.csv")
            if os.path.exists(p):
                runs.append((r, read(p)))
        runs = [(n, r) for n, r in runs if r]
        print(f"\n{law}")
        print(f"{'measure':<30}" + "".join(f"{n:>11}" for n, _ in runs))
        print(f"{'step':<30}" + "".join(f"{r['step']:>11,}" for _, r in runs))
        for k, label, f in COLS:
            print(f"{label:<30}" + "".join(f"{f.format(r[k]):>11}" for _, r in runs))
        out += [{"law": law, "rate": 0.0 if n == "control" else float(n),
                 **{k: r[k] for k, _, _ in COLS}, "step": r["step"]} for n, r in runs]
    with open(os.path.join(HERE, "results", "ladder.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["law", "rate"] + [k for k, _, _ in COLS] + ["step"])
        w.writeheader()
        w.writerows(out)


if __name__ == "__main__":
    main()
