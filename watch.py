#!/usr/bin/env python3
"""Watch running experiments from outside (#105).

    uv run python watch.py                       every run of this repo now on the machine
    uv run python watch.py <dir or prefix> ...   those runs, running or finished

One line a run: where it is, what the world is doing, when its log last grew, and when it should end.
A run writes its log row every 1,000 steps and flushes it, so what is printed is at most a minute old.
A run whose log has not grown for a few minutes is stuck or dead, whatever `ps` says.

**Stop rules.** If the run's experiment has a `Stop early if:` list in its README, every rule is read
against the latest log row and printed as PASS, FAIL or UNKNOWN (the run has not reached the rule's step
yet). A rule is one bullet:

    - pop < 500 at 20000
    - fruit_intake <= 0 at 30000

column, one of < <= > >= ==, a number, and the step from which the rule is read. Only a rule written
before the runs started may stop a run, and only about a failed precondition - the world does not stand,
or the law's mechanism never engages. Never about the measure the experiment is judged by: stopping on
the outcome is choosing the result (e092, #102).
"""
import csv
import io
import os
import re
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
OPS = {"<": lambda a, b: a < b, "<=": lambda a, b: a <= b, ">": lambda a, b: a > b,
       ">=": lambda a, b: a >= b, "==": lambda a, b: a == b}
RULE = re.compile(r"^\s*[-*]\s*`?(\w+)`?\s*(<=|>=|==|<|>)\s*(-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)\s*%?\s+at\s+([\d_,]+)", re.M)
COLS = ("pop", "matter_err", "ms_step", "blocked")


def running():
    """Every run of this repo now on the machine: {prefix: (pid, the step it is going to)}. A run's first
    argument is the prefix it writes to, relative to the repo root, and `steps=` is where it stops."""
    out = subprocess.run(["ps", "-eo", "pid=,command="], capture_output=True, text=True).stdout
    found = {}
    for line in out.splitlines():
        pid, _, command = line.strip().partition(" ")  # `ps` right-aligns the pid, so strip first
        args = command.split()
        if "/target/release/e" not in command or len(args) < 2 or args[1].startswith("-"):
            continue
        steps = next((int(float(a.split("=")[1])) for a in args if a.startswith("steps=")), None)
        found[os.path.normpath(os.path.join(HERE, args[1]))] = (int(pid), steps)
    return found


def last_row(path, back=1 << 16):
    """The last complete row of a CSV, with its header, without reading the whole file."""
    with open(path, "rb") as f:
        head = f.readline().decode()
        size = f.seek(0, io.SEEK_END)
        f.seek(max(len(head), size - back))
        tail = f.read().decode(errors="ignore").splitlines()
    for line in reversed(tail):
        if line.count(",") == head.count(","):
            return next(csv.DictReader([head, line]))
    return None


def clock(seconds):
    if seconds is None:
        return "-"
    seconds = int(seconds)
    return f"{seconds // 3600}:{seconds // 60 % 60:02d}:{seconds % 60:02d}" if seconds >= 3600 else f"{seconds // 60}:{seconds % 60:02d}"


def experiment_of(prefix):
    """The experiment folder a run writes into (the one with the README and the crate)."""
    d = os.path.dirname(prefix)
    while d not in ("/", HERE, ""):
        if os.path.exists(os.path.join(d, "README.md")) and os.path.exists(os.path.join(d, "Cargo.toml")):
            return d
        d = os.path.dirname(d)
    return None


def rules_of(folder):
    """The `Stop early if:` bullets of an experiment's README: (column, op, value, step)."""
    if not folder or not os.path.exists(os.path.join(folder, "README.md")):
        return []
    text = open(os.path.join(folder, "README.md")).read()
    lines = text.splitlines()
    start = next((i for i, l in enumerate(lines) if "stop early if" in l.lower()), None)
    if start is None:
        return []
    block, seen = [], False
    for line in lines[start + 1:]:  # the bullets under the marker, blank lines before them allowed
        if line.strip().startswith(("-", "*")):
            block.append(line)
            seen = True
        elif not line.strip() and not seen:
            continue
        else:
            break
    return [(c, op, float(v), int(step.replace("_", "").replace(",", "")))
            for c, op, v, step in RULE.findall("\n".join(block))]


def prefixes(args):
    """Run prefixes from the paths given: a prefix, or every run in a directory."""
    out = []
    for a in args:
        a = os.path.abspath(a)
        if os.path.isdir(a):
            out += [os.path.join(a, f[: -len("_log.csv")]) for f in sorted(os.listdir(a)) if f.endswith("_log.csv")]
        else:
            out.append(a[: -len("_log.csv")] if a.endswith("_log.csv") else a)
    return out


def main():
    live = running()
    watched = prefixes(sys.argv[1:]) if len(sys.argv) > 1 else sorted(live)
    if not watched:
        print("no runs")
        return
    print(f"{'run':<26}{'step':>16}{'pop':>8}{'err':>9}{'ms':>7}{'blocked':>9}{'age':>7}{'left':>8}  state")
    for pre in watched:
        pid, target = live.get(os.path.abspath(pre), (None, None))
        log = pre + "_log.csv"
        if not os.path.exists(log):
            print(f"{os.path.basename(pre):<26}{'-':>16}  no log yet")
            continue
        row = last_row(log)
        age = time.time() - os.path.getmtime(log)
        step = int(float(row["step"])) if row else 0
        done = os.path.exists(pre + "_row.csv")
        state = "done" if done else f"running (pid {pid})" if pid else "no process"
        if row is None:
            state = f"spinning up (pid {pid})" if pid else "no rows"
        if not done and pid and age > 300:
            state += " - STALLED"
        # What is left, at the pace of the last 1,000 steps (`ms_step`), which the spin-up does not enter.
        ms = float(row["ms_step"]) if row and "ms_step" in row else 0.0
        left = (target - step) * ms / 1000 if (pid and target and step and ms and target > step) else None
        vals = {c: float(row[c]) for c in COLS if row and c in row}
        print(f"{os.path.basename(pre):<26}{step:>9,}{'/' + format(target, ',') if target else '':>7}"
              f"{vals.get('pop', 0):>8,.0f}{vals.get('matter_err', 0):>9.0e}{vals.get('ms_step', 0):>7.1f}"
              f"{vals.get('blocked', 0):>9.0%}{clock(age):>7}{clock(left):>8}  {state}")
        for column, op, value, at in rules_of(experiment_of(pre)):
            rule = f"    stop if {column} {op} {value:g} at {at:,}:"
            if column not in (row or {}):
                print(f"{rule} UNKNOWN (the log has no {column})")
            elif step < at:
                print(f"{rule} UNKNOWN (step {step:,})")
            else:
                hit = OPS[op](float(row[column]), value)
                print(f"{rule} {'FAIL - stop it' if hit else 'PASS'} ({column} {float(row[column]):g})")


if __name__ == "__main__":
    main()
