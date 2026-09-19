"""e087: the map of the places by month that the bodies' run reads, from e086's months at a year.

Each cell's class (0 sea, 1 land always fed, 2 seasonal land, 3 land never fed) and its lean months, as
e086's `months.py` reads them at the bar 0.25: a land month is lean when its growing index is under a
quarter of the land's median yearly index. Writes results/places_y<year>.bin: "E087", n (u32), the
classes (a byte a cell), the lean months (a u16 a cell, bit m for month m).

Run: uv run python experiments/e087_torpor/places.py [year ...]   (default 1200)
"""
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
E086 = os.path.join(HERE, "..", "e086_year", "results")
BAR = 0.25


def main(year):
    raw = open(os.path.join(E086, f"c1225_d11_y{year}_months.bin"), "rb").read()
    assert raw[:4] == b"E086"
    n, months = (int(v) for v in np.frombuffer(raw[4:12], dtype="<u4"))
    elev = np.frombuffer(raw[12:12 + 4 * n * n], dtype="<f4").reshape(n, n)
    grow = np.frombuffer(raw[12 + 4 * n * n:], dtype="<f4").reshape(months, n, n, 3)[..., 2]
    land = elev >= 0
    lean = (grow < BAR * np.median(grow.mean(axis=0)[land])) & land[None]
    n_lean = lean.sum(axis=0)
    cls = np.where(~land, 0, np.where(n_lean == 0, 1, np.where(n_lean == months, 3, 2))).astype(np.uint8)
    bits = (lean.astype(np.uint16) << np.arange(months, dtype=np.uint16)[:, None, None]).sum(axis=0).astype("<u2")
    out = os.path.join(HERE, "results", f"places_y{year}.bin")
    with open(out, "wb") as f:
        f.write(b"E087" + np.uint32(n).astype("<u4").tobytes() + cls.tobytes() + bits.tobytes())
    shares = [(cls == c).sum() / land.sum() for c in (1, 2, 3)]
    print(f"{out}: land fed / seasonal / never {shares[0]:.2f} / {shares[1]:.2f} / {shares[2]:.2f}")


for y in sys.argv[1:] or ["1200"]:
    main(int(y))
