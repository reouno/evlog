#!/usr/bin/env python3
"""The rate ladder of e093 (#103): what `light_gain` buys, read off the logs alone.

Run from the repo root: `uv run python experiments/e093_leaf/ladder.py` (seconds).

One row a run: the five rates on seed 9 and the control's own row at the same step (e081's ladder,
seed 9, which this crate reproduces bit for bit with the light off). Every number is the mean over
the run's second half, so a rate is read after the world has settled under it, not at the turn.
"""
import csv
import os
import statistics as st
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
RATES = ["0.0005", "0.001", "0.002", "0.004", "0.008", "0.016", "0.032", "0.064"]
SCALE = 0.0625  # a body's matter in the world's (e064)
CTL = os.path.join(ROOT, "experiments", "e081_drink", "results", "ladder", "c1225_life9_u0")
COLS = [("pop", "bodies", "{:.0f}"), ("size_mean", "blocks a body", "{:.1f}"),
        ("leaf_mean", "leaf blocks", "{:.2f}"), ("leaf_open", "their open faces", "{:.2f}"),
        ("open_mean", "open faces a body", "{:.1f}"), ("light_intake", "light the world a step", "{:.1f}"),
        ("plant_step", "plants the world a step", "{:.0f}"), ("light_share", "light's share of intake", "{:.1%}"),
        ("leaf_led", "grown bodies led by light", "{:.1%}"),
        ("per_cell", "bodies a cell held", "{:.2f}"), ("no_room", "births with no room", "{:.1%}"),
        ("blocked", "moves blocked", "{:.1%}"), ("grass", "grass standing", "{:.0f}"),
        ("soil_land", "soil on land", "{:.0f}"), ("digestive_mean", "gut blocks", "{:.1f}"),
        ("lineages", "lineages", "{:.0f}")]


def census_at(pre, step):
    """The control has no `open_mean` or `per_cell` column (they are e093's); both are read off its
    census instead, at the step the ladder's runs end on. `tidy.py` keeps the censuses compressed."""
    path = pre + "_agents.csv"
    if os.path.exists(path):
        text = open(path).read()
    else:
        text = subprocess.run(["zstd", "-dc", path + ".zst"], capture_output=True, text=True).stdout
    rows = [r for r in csv.DictReader(text.splitlines()) if int(r["step"]) == step]
    if not rows:
        return {}
    cells = len({r["cell"] for r in rows})
    return {"open_mean": st.mean(float(r["open_soft"]) for r in rows),
            "per_cell": len(rows) / max(cells, 1)}


def read(path, upto=None):
    with open(path) as f:
        rows = [r for r in csv.DictReader(f) if upto is None or int(r["step"]) <= upto]
    if not rows:
        return None
    last = int(rows[-1]["step"])
    half = [r for r in rows if int(r["step"]) >= last / 2]
    out = {"step": last}
    for k, _, _ in COLS:
        if k in ("plant_step", "light_share"):
            continue
        if k not in half[0]:
            out[k] = 0.0
        elif k in ("no_room", "blocked"):
            out[k] = 0.0  # filled below: both are shares of a total the log gives as counts
        else:
            out[k] = st.mean(float(r[k]) for r in half)
    born = sum(float(r["births"]) + float(r["no_room"]) for r in half)
    out["no_room"] = sum(float(r["no_room"]) for r in half) / max(born, 1)
    moves = sum(float(r["forward"]) + float(r["left"]) + float(r["right"]) for r in half)
    out["blocked"] = sum(float(r["blocked"]) for r in half) / max(moves, 1)
    # `plant_intake` is the world's matter over a log interval; `light_intake` is a body's units a
    # step. Put the first in the second's units so that the two foods can be read against each other.
    interval = int(rows[1]["step"]) - int(rows[0]["step"]) if len(rows) > 1 else 1
    plant = st.mean(float(r["plant_intake"]) for r in half)
    out["plant_step"] = plant / SCALE / interval
    out["light_share"] = out["light_intake"] / max(out["light_intake"] + out["plant_step"], 1e-9)
    return out


def main():
    ctl = read(CTL + "_log.csv", upto=40000)
    ctl.update(census_at(CTL, 40000))
    runs = [("control", ctl)]
    for r in RATES:
        p = os.path.join(HERE, "results", f"c1225_life9_g{r}_log.csv")
        if os.path.exists(p):
            runs.append((r, read(p)))
    runs = [(n, r) for n, r in runs if r]
    print(f"{'measure':<26}" + "".join(f"{n:>11}" for n, _ in runs))
    print(f"{'step':<26}" + "".join(f"{r['step']:>11,}" for _, r in runs))
    for k, label, f in COLS:
        print(f"{label:<26}" + "".join(f"{f.format(r[k]):>11}" for _, r in runs))
    with open(os.path.join(HERE, "results", "ladder.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["rate"] + [k for k, _, _ in COLS] + ["step"])
        w.writeheader()
        for name, r in runs:
            w.writerow({"rate": 0.0 if name == "control" else float(name), **{k: r[k] for k, _, _ in COLS}, "step": r["step"]})


if __name__ == "__main__":
    main()
