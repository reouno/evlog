#!/usr/bin/env python3
"""The ladder of e096 (#108): what the pair (`shade`, `light_gain`) buys, read off the logs alone.

Run from the repo root: `uv run python experiments/e096_shade/ladder.py` (seconds).

One row a run: the pairs on seed 9, the shade alone (the e057 read: a subtraction with nobody to
take what it took), and the control - e081's ladder run at seed 9, which this crate reproduces bit
for bit with both laws off, re-run here so that the shade's own columns have a control row. Every
number is the mean over the run's second half, so a rate is read after the world has settled under
it, not at the turn.
"""
import csv
import os
import statistics as st
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
# (shade, light_gain), as the run names carry them: s<shade>g<light_gain>
# `shade` sets where a block's income starts to fall with the crowd (past 16 / shade blocks on a
# cell) and, because a block's shadow covers `shade` of its own footprint, what it earns where the
# cell is empty (`shade` x `light_gain`). The second row holds that sparse income at e093's kept
# rate, so that the sharing is read on its own; the pairs at 0.016 and 0.032 hold `light_gain`.
RUNS = [("0", "0"), ("1", "0"), ("2", "0"),
        ("1", "0.016"), ("2", "0.008"), ("4", "0.004"),
        ("2", "0.016"), ("4", "0.016"), ("1", "0.032")]
SCALE = 0.0625  # a body's matter in the world's (e064)
CTL = os.path.join(ROOT, "experiments", "e081_drink", "results", "ladder", "c1225_life9_u0")
COLS = [("pop", "bodies", "{:.0f}"), ("size_mean", "blocks a body", "{:.1f}"),
        ("leaf_mean", "leaf blocks", "{:.2f}"), ("leaf_open", "their open faces", "{:.2f}"),
        ("open_mean", "open faces a body", "{:.1f}"), ("light_intake", "light the world a step", "{:.1f}"),
        ("plant_step", "plants the world a step", "{:.0f}"), ("light_share", "light's share of intake", "{:.1%}"),
        ("leaf_led", "grown bodies led by light", "{:.1%}"),
        ("per_cell", "bodies a cell held", "{:.2f}"), ("blocks_cell", "blocks over such a cell", "{:.1f}"),
        ("shaded", "of its light they take", "{:.1%}"),
        ("grass_under", "grass where they stand", "{:.3f}"), ("grass_free", "grass where they do not", "{:.3f}"),
        ("gut_income", "intake a gut block", "{:.4f}"),
        ("no_room", "births with no room", "{:.1%}"),
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
        if k in ("plant_step", "light_share", "gut_income"):
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
    # e057's fingerprint: what one gut block takes a step. A law that only subtracts leaves it where
    # it was while the world and its plant fall together.
    out["gut_income"] = out["plant_step"] / max(out["pop"], 1) / max(out["digestive_mean"], 1e-9)
    return out


def main():
    ctl = read(CTL + "_log.csv", upto=40000)
    ctl.update(census_at(CTL, 40000))
    runs = [("e081 ctl", ctl)]
    for sh, gain in RUNS:
        p = os.path.join(HERE, "results", f"c1225_life9_s{sh}g{gain}_log.csv")
        if os.path.exists(p):
            runs.append((f"s{sh} g{gain}", read(p)))
    runs = [(n, r) for n, r in runs if r]
    print(f"{'measure':<26}" + "".join(f"{n:>11}" for n, _ in runs))
    print(f"{'step':<26}" + "".join(f"{r['step']:>11,}" for _, r in runs))
    for k, label, f in COLS:
        print(f"{label:<26}" + "".join(f"{f.format(r[k]):>11}" for _, r in runs))
    with open(os.path.join(HERE, "results", "ladder.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["run"] + [k for k, _, _ in COLS] + ["step"])
        w.writeheader()
        for name, r in runs:
            w.writerow({"run": name, **{k: r[k] for k, _, _ in COLS}, "step": r["step"]})


if __name__ == "__main__":
    main()
