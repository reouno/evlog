"""e101 (from e097): one `results/provenance.csv` for both readings (CLAUDE.md: what a reading actually used).

A row is one run under one reading: the window it read, how many items it read there, and the
thresholds it classified by. A script rewrites its own reading's rows and leaves the others.
"""
import csv, os

FIELDS = ["reading", "run", "from", "to", "items", "thresholds"]


def write(here, reading, rows):
    path = os.path.join(here, "results", "provenance.csv")
    old = []
    if os.path.exists(path):
        with open(path) as f:
            old = [r for r in csv.DictReader(f) if r.get("reading") != reading]
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, lineterminator="\n")
        w.writeheader()
        w.writerows([{**{k: r.get(k, "") for k in FIELDS}, "reading": r.get("reading", reading)} for r in old + list(rows)])
    return path
