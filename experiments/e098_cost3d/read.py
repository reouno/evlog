#!/usr/bin/env python3
"""e098 (#110): the spike's numbers, read off `results/spike.txt` and `results/spike2.txt`.

Run from the repo root: `uv run python experiments/e098_cost3d/read.py`. It prints the tables the
README quotes and writes `results/spike.csv` (every run, one row) and `results/provenance.csv`
(what the projection was built from).
"""
import csv
import os
import statistics as st

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
RES = os.path.join(HERE, "results")

# The control the projection is measured against: e092's control ladder, 100,000 steps, six at once.
CONTROL = {"ms_step": 30.52, "ms_world": 2.55, "ms_bodies": 27.30, "ms_lineage": 0.66, "pop": 8590.0,
           "source": "experiments/e092_yardstick/results/ladder/*_ctl_row.csv (4 seeds kept on disk)"}
LINE = 180.0  # ms a step at which a six-seed batch of 100,000 steps takes 5 hours (#110's line)


def rows(path):
    out = []
    for line in open(path):
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("DONE"):
            continue
        r = dict(p.split("=", 1) for p in line.split())
        r["file"] = os.path.basename(path)
        out.append(r)
    return out


def f(r, k):
    return float(r[k])


def main():
    seq = rows(os.path.join(RES, "spike.txt"))
    more = rows(os.path.join(RES, "spike2.txt"))
    allr = seq + more
    with open(os.path.join(RES, "spike.csv"), "w", newline="\n") as fh:
        keys = sorted({k for r in allr for k in r})
        w = csv.DictWriter(fh, fieldnames=keys)
        w.writeheader()
        w.writerows(allr)

    def pick(src, **want):
        return [r for r in src if all(r.get(k) == v for k, v in want.items())]

    print("== the arms at the control's population, three seeds, one run at a time ==")
    arms = [("2d", {"arm": "2d", "off": "-", "bodies_at": "10000"}),
            ("3d 8x8x8", {"arm": "3d", "off": "-", "sz": "8", "height": "4", "bodies_at": "10000"}),
            ("3d 8x8x4", {"arm": "3d", "off": "-", "sz": "4", "height": "4", "bodies_at": "10000"})]
    base = {}
    for name, want in arms:
        w2 = {k: v for k, v in want.items() if k != "bodies_at"}
        rs = [r for r in pick(seq, **w2) if abs(f(r, "bodies") - 10000) < 800]
        ms = [f(r, "ms_step") for r in rs]
        us = [f(r, "us_body") for r in rs]
        bl = [f(r, "blocks") for r in rs]
        base[name] = st.mean(us)
        print(f"{name:10s} n={len(rs)} ms_step={st.mean(ms):6.2f} ({min(ms):.1f}-{max(ms):.1f}) "
              f"us_body={st.mean(us):5.3f} blocks={st.mean(bl):6.1f} "
              f"occ_mb={rs[0]['occ_mb']} agent_b={rs[0]['agent_b']}")
    for name, _ in arms[1:]:
        print(f"  {name}: {base[name] / base['2d']:.2f}x the 2D clock a body")

    print("\n== the same matter instead of the same population ==")
    for name, want, n in [("3d 8x8x8", {"arm": "3d", "sz": "8", "off": "-"}, 1940),
                          ("3d 8x8x4", {"arm": "3d", "sz": "4", "off": "-"}, 3850)]:
        rs = [r for r in pick(seq, **want) if abs(f(r, "bodies") - n) < 300]
        ms = [f(r, "ms_step") for r in rs]
        bl = [f(r, "blocks") for r in rs]
        print(f"{name:10s} n={len(rs)} bodies~{n} ms_step={st.mean(ms):6.2f} blocks={st.mean(bl):6.1f}")

    print("\n== what each part costs, by what leaving it out saves (seed 1, 10,000 bodies) ==")
    full2 = f([r for r in seq if r["arm"] == "2d" and r["off"] == "-"][0], "ms_step")
    full3 = f([r for r in seq if r["arm"] == "3d" and r["off"] == "-" and r["sz"] == "8"][0], "ms_step")
    print(f"{'part':10s} {'2D ms':>8s} {'share':>7s} {'3D ms':>8s} {'share':>7s}")
    for part in ["wear", "eat", "faces", "sense", "move", "births", "develop"]:
        src = seq + more
        r2 = [r for r in src if r["arm"] == "2d" and r["off"] == part]
        r3 = [r for r in src if r["arm"] == "3d" and r["off"] == part and r["sz"] == "8"]
        if not r2 or not r3:
            continue
        d2, d3 = full2 - f(r2[0], "ms_step"), full3 - f(r3[0], "ms_step")
        # A run with a part off draws a different stream, so the world drifts: anything under the
        # spread between runs of the same seed (2.5 ms in 3D, 0.8 in 2D) is not a cost, it is noise.
        s2, p2 = (f"{d2:8.2f}", f"{100 * d2 / full2:6.1f}%") if abs(d2) > 0.8 else ("  <noise", "      -")
        s3, p3 = (f"{d3:8.2f}", f"{100 * d3 / full3:6.1f}%") if abs(d3) > 2.5 else ("  <noise", "      -")
        print(f"{part:10s} {s2} {p2} {s3} {p3}")
    print(f"{'the step':10s} {full2:8.2f} {100:6.1f}% {full3:8.2f} {100:6.1f}%")

    print("\n== one development ==")
    for r in [r for r in more if r["off"] == "develop_only"]:
        print(f"{r['arm']:4s} cells={float(r['cells']):6.1f} us={float(r['us_develop']):7.1f} "
              f"us_per_cell={float(r['us_develop']) / float(r['cells']):.3f}")

    print("\n== six at once, the batch's own shape ==")
    six = {}
    for a, sz in [("2d", None), ("3d", "8")]:
        rs = [r for r in more if r["arm"] == a and r["off"] == "-" and (sz is None or r["sz"] == sz)]
        ms = [f(r, "ms_step") for r in rs]
        six[a] = st.mean(ms)
        print(f"{a:4s} n={len(rs)} ms_step={st.mean(ms):6.2f} ({min(ms):.1f}-{max(ms):.1f})")
    ratio = six["3d"] / six["2d"]
    print(f"3D costs {ratio:.2f}x 2D with six running at once")

    print("\n== the projection onto the control ==")
    hi = CONTROL["ms_world"] + CONTROL["ms_lineage"] + CONTROL["ms_bodies"] * ratio
    covered = six["2d"] / 1000.0 * 1e3  # ms a step of the harness's own 2D arm at 10,000 bodies
    share = (covered / 10000.0) / (CONTROL["ms_bodies"] / CONTROL["pop"])  # of the control's per-body cost
    lo = CONTROL["ms_world"] + CONTROL["ms_lineage"] + CONTROL["ms_bodies"] * (share * ratio + (1 - share))
    print(f"the harness's 2D arm covers {100 * share:.0f}% of the control's cost a body")
    print(f"3D at the control's population: {lo:.0f}-{hi:.0f} ms a step "
          f"(control {CONTROL['ms_step']:.1f}), a 100,000-step batch {lo * 100:.0f}-{hi * 100:.0f} s "
          f"= {lo * 100 / 3600:.1f}-{hi * 100 / 3600:.1f} h; the line is {LINE:.0f} ms a step")
    with open(os.path.join(RES, "provenance.csv"), "w", newline="\n") as fh:
        w = csv.writer(fh)
        w.writerow(["what", "value", "source"])
        for k, v in CONTROL.items():
            w.writerow([f"control {k}", v, CONTROL["source"] if k != "source" else ""])
        w.writerow(["harness 2d ms_step, six at once, 10,000 bodies", f"{six['2d']:.2f}", "results/spike2.txt"])
        w.writerow(["harness 3d ms_step, six at once, 10,000 bodies", f"{six['3d']:.2f}", "results/spike2.txt"])
        w.writerow(["ratio 3d/2d, six at once", f"{ratio:.2f}", "results/spike2.txt"])
        w.writerow(["share of the control's cost a body the harness covers", f"{share:.2f}", "results/spike2.txt"])
        w.writerow(["projected 3d ms a step", f"{lo:.0f}-{hi:.0f}", "the two lines above"])
        w.writerow(["the line (5 h for six seeds at 100,000 steps)", LINE, "#110"])


if __name__ == "__main__":
    main()
