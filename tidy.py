#!/usr/bin/env python3
"""Keep the project's disk use down (a routine, run it now and then).

    uv run python tidy.py                    what is on disk and what could be freed (nothing is changed)
    uv run python tidy.py --apply            compress the large regenerable files (zstd -12, lossless)
    uv run python tidy.py --apply --viewer   also the viewer's recordings (*_view.bin, *_maps.bin, ...)
    uv run python tidy.py --apply --target   also `cargo clean` (about a minute to build back)
    uv run python tidy.py --restore <path>   put an experiment's files back (zstd -d)

What is compressed: the large files a run writes and a reader rebuilds from - the censuses
(`*_agents.csv`), the per-lineage rows, the dryness, the grown dead, the genome dumps. A report or a
sweep that needs one of them again is run after `--restore`.

What is never touched: anything git tracks (the logs, the rows, the bands, and every derived CSV a report
reads), the settled worlds under `e063_bodies/results/worlds` (every stage C run reads them), and any run
with a live process or a file written in the last ten minutes.

What this does not decide: deleting results. `--stale` lists what is only kept for a report that could be
rebuilt - old `*.jsonl.zst` and viewer recordings - so a person can choose.
"""
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(HERE, "experiments")
LEVEL = "12"  # 5x smaller at 150 MB/s; -19 buys 15% more for 15 times the time (measured 2026-09-20)
BIG = ("_agents.csv", "_lineages.csv", "_dryness.csv", "_grown.csv", "_genomes.csv")
VIEWER = ("_view.bin", "_maps.bin", "_months.bin", "_cells.bin")
KEEP = (os.path.join("e063_bodies", "results", "worlds"),)  # the settled worlds every run reads
FRESH = 600  # seconds: a file written this recently belongs to a run that may still be going


def tracked():
    out = subprocess.run(["git", "-C", HERE, "ls-files"], capture_output=True, text=True).stdout
    return {os.path.join(HERE, p) for p in out.splitlines()}


def busy():
    """The prefixes of runs with a live process (`watch.py`'s reading of `ps`)."""
    sys.path.insert(0, HERE)
    import watch  # noqa: E402  (the same reading of ps, in one place)
    return set(watch.running())


def candidates(suffixes, keep, live):
    for folder, _, files in os.walk(RESULTS):
        if any(k in folder for k in KEEP) or f"{os.sep}results" not in folder:
            continue
        for f in sorted(files):
            path = os.path.join(folder, f)
            if not f.endswith(suffixes) or path in keep:
                continue
            prefix = path[: path.rfind("_")]
            if prefix in live or time.time() - os.path.getmtime(path) < FRESH:
                continue
            yield path


def mb(paths):
    return sum(os.path.getsize(p) for p in paths) / 1048576


def by_experiment(paths):
    out = {}
    for p in paths:
        name = os.path.relpath(p, RESULTS).split(os.sep)[0]
        out.setdefault(name, []).append(p)
    return out


def compress(paths):
    done, freed = 0, 0.0
    for p in paths:
        before = os.path.getsize(p)
        r = subprocess.run(["zstd", "-q", f"-{LEVEL}", "-T0", "--rm", p])
        if r.returncode or not os.path.exists(p + ".zst"):
            print(f"  failed: {p}")
            continue
        done += 1
        freed += (before - os.path.getsize(p + ".zst")) / 1048576
    return done, freed


def restore(path):
    path = os.path.abspath(path)
    files = []
    for folder, _, names in os.walk(path) if os.path.isdir(path) else [(os.path.dirname(path), [], [os.path.basename(path)])]:
        files += [os.path.join(folder, n) for n in names if n.endswith(".zst") and not n.endswith(".jsonl.zst")]
    if not files:
        print(f"nothing compressed under {path}")
        return
    print(f"restoring {len(files)} files ({mb(files):.0f} MB compressed)")
    subprocess.run(["zstd", "-q", "-d", "--rm", *files], check=True)


def stale():
    """Kept only so that an old report could be rebuilt: a person decides whether to delete these."""
    out = {}
    for folder, _, files in os.walk(RESULTS):
        for f in files:
            if f.endswith(".jsonl.zst") or f.endswith(VIEWER):
                out.setdefault(os.path.relpath(folder, RESULTS).split(os.sep)[0], []).append(os.path.join(folder, f))
    return out


def report(groups, title):
    if not groups:
        print(f"{title}: nothing")
        return
    total = sum(mb(v) for v in groups.values())
    print(f"\n{title}: {total:,.0f} MB in {sum(len(v) for v in groups.values())} files")
    for name, paths in sorted(groups.items(), key=lambda kv: -mb(kv[1]))[:12]:
        print(f"  {name:<26}{mb(paths):>8,.0f} MB  {len(paths)} files")


def main():
    args = sys.argv[1:]
    if "--restore" in args:
        restore(args[args.index("--restore") + 1])
        return
    apply_ = "--apply" in args
    keep, live = tracked(), busy()
    big = list(candidates(BIG, keep, live))
    view = list(candidates(VIEWER, keep, live)) if "--viewer" in args else []
    print(f"experiments: {mb([os.path.join(d, f) for d, _, fs in os.walk(RESULTS) for f in fs]):,.0f} MB"
          + (f", target: {mb([os.path.join(d, f) for d, _, fs in os.walk(os.path.join(HERE, 'target')) for f in fs]):,.0f} MB"
             if os.path.isdir(os.path.join(HERE, "target")) else ""))
    report(by_experiment(big), "to compress (regenerable, lossless)")
    if view:
        report(by_experiment(view), "viewer recordings to compress")
    if "--stale" in args:
        report(stale(), "kept only for rebuilding an old report (delete by hand if it is not wanted)")
    if not apply_:
        print("\nnothing changed. --apply to compress, --stale to list what only a person should delete.")
        return
    for group, what in ((big, "regenerable files"), (view, "viewer recordings")):
        if group:
            done, freed = compress(group)
            print(f"compressed {done} {what}, freed {freed:,.0f} MB")
    if "--target" in args:
        subprocess.run(["cargo", "clean"], cwd=HERE, check=False)
        print("cargo clean done (the next build takes about a minute)")


if __name__ == "__main__":
    main()
