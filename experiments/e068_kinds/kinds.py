#!/usr/bin/env python3
"""Kinds of living inside a lineage (#82): e065-e067's censuses read by birth form.

Run from the repo root: `uv run python experiments/e068_kinds/kinds.py` (about a minute on one core).
It reads the `agents.csv` of four runs on c1225, seed 9 (e065's water layers, e066's dry air at 0.004,
e067's breath at 0.003 and 0.01), prints the counts and writes `results/*.csv` for the report.

A body's birth form is the body its genes develop: the grid's side and, at birth, its blocks of each
kind, its bite and its density (development reads only the genes and the law table). `cells` in
`agents.csv` is the body now, after breaks and wear, so a shape read from it is partly damage. A birth
signature with FORM grown bodies or more over the second half's censuses is a form; every other grown
body joins the nearest form of its lineage and its side of density 1, by its birth traits.

A form's way of living is read over all its grown bodies: e060's diet from their summed intake, its
tooth and its roaming from their medians, and its medium where KEEP of them stand, else "shore". Each
grown body counts under its form's way, and a kind holds e060's 5% of the grown bodies at a census.

The null shuffles what bodies do (intake, bite, travel, medium) among the grown bodies of each lineage
and side of density 1: what the same count reads when a lineage's forms do not differ.
"""
import csv
import math
import os
import statistics as st
import sys
from collections import Counter, defaultdict

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "experiments", "e060_census"))
import census  # noqa: E402  (e060's census of ways of living)

RUNS = [
    ("e065", os.path.join(ROOT, "experiments", "e065_layers", "results", "c1225_life9_water")),
    ("e066", os.path.join(ROOT, "experiments", "e066_dry", "results", "c1225_life9_dry0.004")),
    ("breath 0.003", os.path.join(ROOT, "experiments", "e067_breath", "results", "c1225_life9_breath0.003")),
    ("breath 0.01", os.path.join(ROOT, "experiments", "e067_breath", "results", "c1225_life9_breath0.01")),
]
MEDIA = ["land", "surface", "bottom"]
FORM = 20        # grown bodies over the second half that make a birth signature a form
KEEP = 0.9       # share of a group's grown bodies in one medium for the group to live there (e067's line)
NULLS = 5        # shuffles per null
DOES = ("plant", "meat", "light", "bite_any", "travel", "medium")  # what a body does: shuffled by the null
SWEEP = [(0.8, 20), (0.95, 20), (0.9, 10), (0.9, 50)]  # (KEEP, FORM)


# ---------------------------------------------------------------- one body

def signature(r):
    # e093 (#103): the leaf blocks a body is born with part its form too. A run with no leaf column
    # reads 0 for every body, so the signature is the one e068 read.
    return (int(r["side"]), int(r["born_hard"]), int(r["born_muscle"]), int(r["born_sensor"]),
            int(r["born_digestive"]), int(r.get("born_leaf") or 0), int(r["born_bite"]), r["density"])


def traits(r):
    n = float(r["born_size"])
    return [math.log(n), int(r["born_hard"]) / n, int(r["born_muscle"]) / n, int(r["born_sensor"]) / n,
            int(r["born_digestive"]) / n, int(r.get("born_leaf") or 0) / n, float(r["born_bite"]),
            float(r["density"]), float(r["side"])]


def medium(r):
    return MEDIA[int(r["medium"])]


def open_soft(r):
    """Faces of soft blocks with no block of the body beside them (e066's `open_faces`), from the cells."""
    s, g = int(r["side"]), [int(c) for c in r["cells"]]
    n = 0
    for i, k in enumerate(g):
        if k in (0, 1):
            continue
        y, x = divmod(i, s)
        for yy, xx in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)):
            n += not (0 <= yy < s and 0 <= xx < s) or g[yy * s + xx] == 0
    return n


def intact(r):
    """A body that has lost no block: its cells are its birth body."""
    return r["size"] == r["born_size"]


def way_of(ds, keep=KEEP):
    """A group's way of living, read over all its grown bodies: e060's parts, and the medium."""
    plant = sum(float(d["plant"]) for d in ds)
    meat = sum(float(d["meat"]) for d in ds)
    flesh = meat / (plant + meat) if plant + meat else 0.0
    diet = "plant" if flesh < census.FLESH[0] else "flesh" if flesh > census.FLESH[1] else "mixed"
    # e093 (#103): a group that took most of its matter from the light lives by the light, whatever
    # the rest of it ate. A run with no light column reads 0 and the diet is the one e068 read.
    light = sum(float(d.get("light") or 0.0) for d in ds)
    if light > 0.0 and light >= census.LIGHT * (plant + meat + light):
        diet = "light"
    tooth = "tooth" if st.median(int(float(d["bite_any"])) for d in ds) >= census.TOOTH else "no tooth"
    roams = "roams" if st.median(float(d["travel"]) for d in ds) >= census.ROAM else "stays"
    m, v = Counter(d["medium"] for d in ds).most_common(1)[0]
    return (diet, tooth, roams, MEDIA[int(m)] if v >= keep * len(ds) else "shore")


# ---------------------------------------------------------------- a run

class Run:
    def __init__(self, name, pre):
        self.name = name
        agents = census.read(pre + "_agents.csv")
        self.steps = census.late(list(agents))
        self.grown = [r for s in self.steps for r in census.grown(agents[s]) if census.way(r)]
        # A signature's bodies share one exact density, so one layer; `density` is printed to 3 decimals and many
        # lineages sit at 1.000, so the layer is read from where the signature's bodies in the water stand.
        wet = defaultdict(Counter)
        for r in self.grown:
            if r["medium"] != "0":
                wet[signature(r)][r["medium"] == "1"] += 1
        self.mixed_layers = sum(len(c) > 1 for c in wet.values())
        self.light = [wet[signature(r)].most_common(1)[0][0] if wet.get(signature(r)) else float(r["density"]) < 1 for r in self.grown]
        self.groups = defaultdict(list)  # (lineage, lighter than water) -> body indices
        for i, r in enumerate(self.grown):
            self.groups[(r["lineage"], self.light[i])].append(i)
        t = np.array([traits(r) for r in self.grown])
        sd = t.std(0)
        self.traits = (t - t.mean(0)) / np.where(sd > 0, sd, 1)
        self.at = defaultdict(list)
        for i, r in enumerate(self.grown):
            self.at[int(r["step"])].append(i)
        self._forms = {}

    def forms(self, minimum=FORM):
        """Each grown body's form: (lineage, birth signature)."""
        if minimum not in self._forms:
            of = [None] * len(self.grown)
            for (lineage, _), idx in self.groups.items():
                sigs = Counter(signature(self.grown[i]) for i in idx)
                keys = [s for s, v in sigs.items() if v >= minimum] or [sigs.most_common(1)[0][0]]
                centre = np.array([self.traits[[i for i in idx if signature(self.grown[i]) == s]].mean(0) for s in keys])
                near = ((self.traits[idx][:, None, :] - centre[None]) ** 2).sum(-1).argmin(1)
                for i, k in zip(idx, near):
                    of[i] = (lineage, keys[k])
            self._forms[minimum] = of
        return self._forms[minimum]

    def does(self, keys=(), seed=1):
        """What each grown body does, with `keys` shuffled among the grown bodies of its lineage and side of density 1."""
        d = [{k: r[k] for k in DOES if k in r} for r in self.grown]
        if keys:
            rng = np.random.default_rng(seed)
            src = [dict(x) for x in d]
            for idx in self.groups.values():
                for i, j in zip(idx, rng.permutation(idx)):
                    for k in keys:
                        d[i][k] = src[j][k]
        return d

    def tally(self, unit, ways):
        """Grown bodies by kind at each census; unit[i] is body i's group and ways[group] its way."""
        return {s: Counter(ways[unit[i]] for i in self.at[s]) for s in self.steps}


def kinds(tallies):
    """The kinds at each census (holding e060's share of the grown bodies) and those held at every census."""
    per = {s: {w for w, v in c.items() if v >= census.SHARE * sum(c.values())} for s, c in tallies.items()}
    return per, set.intersection(*per.values())


def mean_count(per):
    return st.mean(len(k) for k in per.values())


def by_group(run, unit, does, keep=KEEP):
    members = defaultdict(list)
    for i, u in enumerate(unit):
        members[u].append(does[i])
    return {u: way_of(ds, keep) for u, ds in members.items()}


def form_census(run, keep=KEEP, minimum=FORM, keys=(), seed=1):
    unit = run.forms(minimum)
    return kinds(run.tally(unit, by_group(run, unit, run.does(keys, seed), keep)))


def null(run, keys, keep=KEEP, minimum=FORM):
    """The form census over NULLS shuffles: mean count, mean count held at every census, and each census's mean."""
    res = [form_census(run, keep, minimum, keys, s) for s in range(1, NULLS + 1)]
    return (st.mean(mean_count(p) for p, _ in res), st.mean(len(h) for _, h in res),
            {s: st.mean(len(p[s]) for p, _ in res) for s in run.steps})


# ---------------------------------------------------------------- the candidates of #82 and what was tried

def per_body_medium(run, keys=(), seed=1):
    """#82's first candidate: e060's way with the medium, counted over bodies."""
    d = run.does(keys, seed)
    ways = [census.way({**r, **d[i]}) + (MEDIA[int(d[i]["medium"])],) for i, r in enumerate(run.grown)]
    return kinds(run.tally(list(range(len(run.grown))), ways))


def lineage_e060(run):
    """e060's count by lineage: every grown body under its lineage's commonest way, at each census."""
    return st.mean(census.count(census.census_by_lineage([run.grown[i] for i in run.at[s]])) for s in run.steps)


def lineage_read(run):
    """The lineage as the group, read as a form is (the medium kept at KEEP, else shore)."""
    unit = [r["lineage"] for r in run.grown]
    return kinds(run.tally(unit, by_group(run, unit, run.does())))


def modal_forms(run, keys=(), seed=1):
    """#82's second candidate as far as the logs allow: each body under its form's commonest way with the medium."""
    unit, d = run.forms(), run.does(keys, seed)
    members = defaultdict(Counter)
    for i, u in enumerate(unit):
        members[u][census.way({**run.grown[i], **d[i]}) + (MEDIA[int(d[i]["medium"])],)] += 1
    return kinds(run.tally(unit, {u: c.most_common(1)[0][0] for u, c in members.items()}))


def confined(run, key, keys=(), seed=1):
    """e067's measure: the share of grown bodies, in groups by `key` of 20 or more, whose group keeps 90% to one medium."""
    d = run.does(keys, seed)
    c = defaultdict(Counter)
    for i, r in enumerate(run.grown):
        c[key(r)][d[i]["medium"]] += 1
    common = [v for v in c.values() if sum(v.values()) >= 20]
    n = sum(sum(v.values()) for v in common)
    return sum(sum(v.values()) for v in common if max(v.values()) >= KEEP * sum(v.values())) / max(n, 1)


def apart(run, k=5, cap=400, seed=1):
    """Born apart: inside a lineage, can a body's birth traits tell a group living one way (with the medium) from
    the lineage's largest group? Balanced leave-one-out k-NN accuracy (0.5 = no), per part of the way that differs."""
    rng = np.random.default_rng(seed)
    out = []
    for s in run.steps:
        groups = defaultdict(list)
        for i in run.at[s]:
            r = run.grown[i]
            groups[(r["lineage"], census.way(r) + (medium(r),))].append(i)
        lineages = defaultdict(list)
        for (lineage, w), idx in groups.items():
            lineages[lineage].append((len(idx), w, idx))
        for rows in lineages.values():
            rows.sort(key=lambda x: -x[0])
            _, wb, ib = rows[0]
            for n, wa, ia in rows[1:]:
                if n < 20:
                    continue
                a = run.traits[rng.choice(ia, min(cap, len(ia)), replace=False)]
                b = run.traits[rng.choice(ib, min(cap, len(ib)), replace=False)]
                x = np.vstack([a, b])
                y = np.r_[np.ones(len(a), bool), np.zeros(len(b), bool)]
                dist = ((x[:, None, :] - x[None]) ** 2).sum(-1)
                np.fill_diagonal(dist, np.inf)
                nn = np.argpartition(dist, k, axis=1)[:, :k]

                def balanced(lab):
                    pred = lab[nn].sum(1) * 2 > k
                    return 0.5 * (pred[lab].mean() + (~pred[~lab]).mean())
                parts = [p for p, u, v in zip(("diet", "tooth", "roams", "medium"), wa, wb) if u != v]
                out.append({"run": run.name, "step": s, "parts": " ".join(parts), "n": n,
                            "balanced": balanced(y), "null": balanced(rng.permutation(y))})
    return out


# ---------------------------------------------------------------- what a kind is

def describe(run, per, held):
    """Each kind of the form census: how many bodies, which forms and lineages, what they are born as and eat."""
    unit = run.forms()
    ways = by_group(run, unit, run.does())
    members = defaultdict(list)
    for i, u in enumerate(unit):
        members[ways[u]].append(i)
    seen = Counter(w for p in per.values() for w in p)
    out = []
    for w, idx in sorted(members.items(), key=lambda x: -len(x[1])):
        if not seen[w]:
            continue
        rs = [run.grown[i] for i in idx]
        forms = Counter(unit[i] for i in idx)
        lineages = Counter(r["lineage"] for r in rs)
        eat = lambda k: sum(float(r[k]) for r in rs)
        intake = eat("plant") + eat("meat")
        top_form = forms.most_common(1)[0][0]
        bodies = Counter((r["side"], r["cells"]) for i, r in zip(idx, rs) if unit[i] == top_form and intact(r))
        side, cells = bodies.most_common(1)[0][0] if bodies else ("0", "")
        where = Counter(medium(r) for r in rs)
        whole = [open_soft(r) / int(r["size"]) for r in rs if intact(r)]
        out.append({
            "run": run.name, "kind": " / ".join(w), "share": len(idx) / len(run.grown), "censuses": seen[w],
            "held": w in held, "forms": len(forms), "lineages": len(lineages),
            "top_lineages": " ".join(f"{l}:{v / len(rs):.2f}" for l, v in lineages.most_common(3)),
            "born_size": st.median(int(r["born_size"]) for r in rs), "density": st.median(float(r["density"]) for r in rs),
            "open_born": st.median(whole) if whole else "",
            "grass": (eat("plant") - eat("algae") - eat("detritus")) / intake, "algae": eat("algae") / intake,
            "detritus": eat("detritus") / intake, "meat": eat("meat") / intake, "kills": eat("killed") / intake,
            "travel": st.median(float(r["travel"]) for r in rs),
            **{m: where[m] / len(rs) for m in MEDIA},
            "side": side, "cells": cells,
        })
    return out


def sizes(run, n=3, bin_=4):
    """Birth size by medium (land, water) for the largest lineages, on each side of density 1."""
    top = [l for l, _ in Counter(r["lineage"] for r in run.grown).most_common(n)]
    out = []
    for lineage in top:
        for light in (False, True):
            rs = [r for i, r in enumerate(run.grown) if r["lineage"] == lineage and run.light[i] == light]
            for where in ("land", "water"):
                part = [r for r in rs if (medium(r) != "land") == (where == "water")]
                c = Counter(int(r["born_size"]) // bin_ * bin_ for r in part)
                for size, v in sorted(c.items()):
                    out.append({"run": run.name, "lineage": lineage, "light": int(light), "where": where, "bodies": len(part),
                                "born_size": size, "share": v / len(part)})
    return out


# ---------------------------------------------------------------- main

def write(name, rows):
    keys = list(dict.fromkeys(k for r in rows for k in r))
    with open(os.path.join(HERE, "results", f"{name}.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        w.writerows(rows)


def main():
    os.makedirs(os.path.join(HERE, "results"), exist_ok=True)
    out = defaultdict(list)
    for name, pre in RUNS:
        run = Run(name, pre)
        per, held = form_census(run)
        nm, nm_held, nm_at = null(run, ("medium",))
        nw, nw_held, nw_at = null(run, DOES)
        body, _ = per_body_medium(run)
        body_null = st.mean(mean_count(per_body_medium(run, ("medium",), s)[0]) for s in range(1, NULLS + 1))
        lin, lin_held = lineage_read(run)
        modal, _ = modal_forms(run)
        modal_null = st.mean(mean_count(modal_forms(run, DOES, s)[0]) for s in range(1, NULLS + 1))
        unit = run.forms()
        ways = by_group(run, unit, run.does())
        sig_count = Counter(signature(r) for r in run.grown)
        row = {
            "run": name, "censuses": len(run.steps), "grown": len(run.grown) / len(run.steps),
            "lineages": len({r["lineage"] for r in run.grown}), "forms": len(set(unit)), "mixed_layers": run.mixed_layers,
            "in_forms": sum(sig_count[signature(r)] >= FORM for r in run.grown) / len(run.grown),
            "body_medium": mean_count(body), "body_medium_null": body_null,
            "lineage_e060": lineage_e060(run), "lineage": mean_count(lin), "lineage_held": len(lin_held),
            "modal_form": mean_count(modal), "modal_form_null": modal_null,
            "form": mean_count(per), "form_low": min(len(p) for p in per.values()), "form_high": max(len(p) for p in per.values()),
            "form_held": len(held), "null_medium": nm, "null_medium_held": nm_held, "null_whole": nw, "null_whole_held": nw_held,
            "sorted": sum(ways[unit[i]][3] != "shore" for i in range(len(run.grown))) / len(run.grown),
            "confined_shape": confined(run, lambda r: (r["side"], r["cells"])),
            "confined_signature": confined(run, signature),
            "confined_signature_null": st.mean(confined(run, signature, ("medium",), s) for s in range(1, NULLS + 1)),
        }
        out["runs"].append(row)
        for s in run.steps:
            out["counts"].append({"run": name, "step": s, "body_medium": len(body[s]), "lineage": len(lin[s]),
                                  "form": len(per[s]), "null_medium": nm_at[s], "null_whole": nw_at[s]})
        out["kinds"] += describe(run, per, held)
        out["sizes"] += sizes(run)
        for keep, minimum in SWEEP:
            p, h = form_census(run, keep, minimum)
            a, ah, _ = null(run, DOES, keep, minimum)
            b, bh, _ = null(run, ("medium",), keep, minimum)
            out["sweep"].append({"run": name, "keep": keep, "form_min": minimum, "form": mean_count(p), "form_held": len(h),
                                 "null_whole": a, "null_whole_held": ah, "null_medium": b, "null_medium_held": bh})
        tried = apart(run)
        for part in ("diet", "tooth", "roams", "medium"):
            v = [t for t in tried if part in t["parts"].split()]
            if v:
                out["apart"].append({"run": name, "part": part, "groups": len(v), "balanced": st.median(t["balanced"] for t in v),
                                     "at_0.8": sum(t["balanced"] >= 0.8 for t in v) / len(v), "null": st.mean(t["null"] for t in v)})
        print(f"{name:13s} body+medium {row['body_medium']:.1f} (null {body_null:.1f}) | lineage e060 {row['lineage_e060']:.1f}, read as a form {row['lineage']:.1f} "
              f"| modal form {row['modal_form']:.1f} (null {modal_null:.1f}) | form {row['form']:.1f} [{row['form_low']}-{row['form_high']}] held {len(held)} "
              f"| null medium {nm:.1f} ({nm_held:.1f}), whole {nw:.1f} ({nw_held:.1f}) | forms {row['forms']} ({row['in_forms']:.0%} in their own signature), "
              f"sorted {row['sorted']:.0%} | confined: shape {row['confined_shape']:.0%}, signature {row['confined_signature']:.0%} (null {row['confined_signature_null']:.0%})")
    for name, rows in out.items():
        write(name, rows)
    print("wrote " + ", ".join(f"results/{n}.csv" for n in out))


if __name__ == "__main__":
    main()
