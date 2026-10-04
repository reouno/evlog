"""Read e107's runs beside e106's pilot 3: the same world at three declared sizes.

uv run python experiments/e107_scale/read.py

Each run: its log by year (bodies, the land they hold, what they eat of the producers' fixing, the land's producers,
what they die of), the census of its last year (adult mass, how far a body stands from where it was born), and the
founders' lines in the last frame of its recording (the viewer's `lineage` is a body's founder).
"""

import csv
import json
import os
import io
import struct
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
E106 = os.path.join(HERE, "..", "e106_bodies", "results")
RUNS = [  # name, cell's side in km, the log's prefix, the recording
    ("pilot3", 63.0, f"{E106}/pilot3/c1225_life1", f"{E106}/watch/lapse_view.bin"),
    ("km1", 1.0, f"{HERE}/results/km1", f"{HERE}/results/km1_view.bin"),
    ("km025", 0.25, f"{HERE}/results/km025", f"{HERE}/results/km025_view.bin"),
]
YEARS = [51, 53, 55, 60, 65, 71, 75, 80]
SIZE = {"u8": 1, "u16": 2, "u32": 4, "f32": 4}


def table(path):
    """A CSV, or its compressed copy (`tidy.py` leaves `.zst`)."""
    if os.path.exists(path):
        return csv.DictReader(open(path))
    if os.path.exists(path + ".zst"):
        return csv.DictReader(io.StringIO(subprocess.run(["zstd", "-dc", path + ".zst"], capture_output=True, text=True, check=True).stdout))
    return iter(())


def last_frame_lines(path):
    """Founders' lines in the recording's last frame: {lineage: bodies}."""
    with open(path, "rb") as f:
        kind, n = struct.unpack("<BI", f.read(5))
        head = json.loads(f.read(n))
        rec = sum(SIZE[x["type"]] for x in head["agent_record"])
        cells = head["w"] * head["h"]
        last = None
        while True:
            h = f.read(5)
            if len(h) < 5:
                break
            kind, n = struct.unpack("<BI", h)
            if kind == 2:
                last = f.tell()
            f.seek(n, 1)
        if last is None:  # a run still in its spin-up has written no frame
            return {}
        f.seek(last)
        f.read(8)
        ng = f.read(1)[0]
        f.read(4 * ng)
        nl = f.read(1)[0]
        f.seek(nl * (1 + cells), 1)
        (na,) = struct.unpack("<I", f.read(4))
        buf = f.read(na * rec)
    lines = {}
    for i in range(na):
        (lin,) = struct.unpack_from("<I", buf, i * rec + 4)
        lines[lin] = lines.get(lin, 0) + 1
    return lines


for name, km, prefix, view in RUNS:
    if not os.path.exists(f"{prefix}_log.csv"):
        continue
    log = {int(r["year"]): r for r in csv.DictReader(open(f"{prefix}_log.csv"))}
    deaths = [k for k in next(iter(log.values())) if k.startswith("died_")]
    print(f"\n== {name}: a cell {km} km, the world {512 * km:,.0f} km")
    print(f"{'year':>5} {'bodies':>8} {'land held':>9} {'ate/gpp':>8} {'land kg/m2':>10} {'first death':>11} {'its share':>9} {'moves/body':>10} {'year s':>7}")
    for y in YEARS:
        r = log.get(y)
        if r is None:
            continue
        d = {k[5:]: float(r[k]) for k in deaths}
        tot = sum(d.values())
        top = max(d, key=d.get) if tot else "-"
        ate = sum(float(r[k]) for k in ["ate_leaf", "ate_wood", "ate_seed", "ate_litter"])
        nb = max(int(r["bodies"]), 1)
        print(
            f"{y:>5} {r['bodies']:>8} {float(r['body_land_cells']):>9.3f} {ate / float(r['gpp']):>8.3f} {float(r['land_biomass']):>10.3f} "
            f"{top:>11} {d.get(top, 0) / max(tot, 1):>9.2f} {float(r['body_moves']) / nb:>10.1f} {float(r['ms_step']) * 11.88:>7.1f}"
        )
    rows = list(table(f"{prefix}_bodies.csv"))
    if rows:
        last = max(int(r["year"]) for r in rows)
        rows = [r for r in rows if int(r["year"]) == last]
        m = sum(float(r["matter"]) for r in rows)
        w = lambda c: sum(float(r[c]) * float(r["matter"]) for r in rows) / m
        adults = sorted((float(r["adult_mass"]), float(r["matter"])) for r in rows)
        acc, q = 0.0, {}
        for a, mm in adults:
            acc += mm
            for p in (0.1, 0.5, 0.9):
                if p not in q and acc >= p * m:
                    q[p] = a
        bodies = sum(int(r["bodies"]) for r in rows)
        animals = sum(float(r["animals"]) for r in rows)
        print(
            f"  year {last}: {len(rows)} genotypes, adult mass p10/p50/p90 {q[0.1]:.3g}/{q[0.5]:.3g}/{q[0.9]:.3g} kg, "
            f"a body stands for {animals / bodies:.3g} animals (mean), from its birth {w('from_birth'):.1f} cells = {w('from_birth') * km:.0f} km, "
            f"at sea {w('sea'):.2f}, eats leaf/wood/seed/litter {w('ate_leaf'):.2f}/{w('ate_wood'):.2f}/{w('ate_seed'):.2f}/{w('ate_litter'):.2f}"
        )
    if os.path.exists(view) and last_frame_lines(view):
        lines = sorted(last_frame_lines(view).items(), key=lambda kv: -kv[1])
        n = sum(v for _, v in lines)
        print(f"  founders' lines in the last frame: {len(lines)}; the first three hold " + ", ".join(f"{v / n:.3f}" for _, v in lines[:3]))
