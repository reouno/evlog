"""Read e062's `<prefix>_maps.bin` (the producers' last year, `maps=1`).

Layout: b"E062", n (u32), the height (n*n f32), then for each quarter the habitats (n*n u8) and the means of
temperature, ground fill (ground over soil, at most 1; 0 in the sea), grass, wood and algae (n*n f32 each),
then the cells burnt in the year (n*n u8), the litter and the soil (n*n f32 each).
"""
import numpy as np


def read_maps(path):
    raw = open(path, "rb").read()
    assert raw[:4] == b"E062", path
    n = int(np.frombuffer(raw, "<u4", 1, 4)[0])
    cells = n * n
    at = 8
    elev = np.frombuffer(raw, "<f4", cells, at).reshape(n, n)
    at += 4 * cells
    q = {k: [] for k in ("hab", "temp", "moist", "grass", "wood", "algae")}
    for _ in range(4):
        q["hab"].append(np.frombuffer(raw, "u1", cells, at).reshape(n, n))
        at += cells
        for k in ("temp", "moist", "grass", "wood", "algae"):
            q[k].append(np.frombuffer(raw, "<f4", cells, at).reshape(n, n))
            at += 4 * cells
    out = {"n": n, "elev": elev}
    for k, v in q.items():
        out[k] = np.stack(v)
    return out
