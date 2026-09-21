"""The columns a census may hold, and what a birth form is made of.

A run writes `<prefix>_agents.csv`: one row per living body at a census. Every column it can hold is
named below, as one the readers use or one they ignore. **A column that is in neither stops the
reading** - so when `main.rs` starts writing something new, the analysis fails loudly on the next run
instead of counting the world wrong in silence. Classifying it is one line of work, once.

The blocks a birth form is made of are not named here: they are read off the header (`born_<kind>`
beside `<kind>`), so a new kind of block parts the forms without a line of analysis being rewritten.
"""

# Columns the shared readers actually read (`census.py`, `kinds.py`, and the sweeps that build on them).
USED = {
    "step", "id", "lineage", "age", "size", "side", "density", "mass",
    "born_size", "born_mass", "born_bite", "born_place", "born_rich",
    "bite", "bite_any", "cells", "medium", "place",
    "plant", "meat", "killed", "scavenged", "light",  # what decides a diet
    "travel", "wood", "crown", "seed", "fruit", "invader", "cell",
}

# Columns a census holds that no shared reader classifies a body by. An experiment's own sweep may
# read any of them; they are listed so that a genuinely new column cannot hide among them.
IGNORED = {
    "turns", "shell", "speed", "energy", "fat", "path", "worn", "pace",
    "temp", "moist", "height", "algae", "detritus", "water", "drank",
    "open_soft", "breath", "inhaled", "breed", "share", "store", "kids",
    "btemp", "warmed", "cooled", "load", "fermented", "dunged", "fiber",
    "leaf_open", "born_hab", "rich",
    # e095 (#107): the faces of a body's leg blocks that pull, and what it took through a spike. The
    # second is not a food of its own - it is part of `killed`, read apart by that experiment's sweep.
    "leg_open", "sharp",
}

# Columns that older crates wrote and no crate writes now (e005-e059, e071). They are named so that
# the censuses on disk still read, and so that a name that is genuinely new cannot hide among them.
LEGACY = {
    "hard", "muscle", "sensor", "digestive",   # block counts before e058 wrote `born_*` beside them
    "attack", "digest", "foot", "open", "long", "wide",
    "len_fwd", "len_side", "shell_back", "shell_front", "shell_side",
    "beta", "eta", "hidden", "drift", "wchange",  # e050-e057's learning columns
    "chilled",                                    # e071's cold
}

# `born_<x>` columns that are not a kind of block.
NOT_A_BLOCK = {"size", "mass", "bite", "place", "hab", "rich"}  # `rich` is e059's place, not a block


class UnknownColumn(Exception):
    pass


def check(header, where=""):
    """Raise unless every column of a census is one this package has classified."""
    unknown = sorted(c for c in header
                     if c not in USED and c not in IGNORED and c not in LEGACY and not is_block(c, header))
    if unknown:
        raise UnknownColumn(
            f"{where}: the census has columns this analysis has never seen: {unknown}. "
            f"Add each to USED or IGNORED in analysis/schema.py - and if it is something a body eats, "
            f"teach `census.way` what it means before counting anything.")
    return header


def is_block(column, header):
    """Is this column a kind of block? `born_<kind>` with a `<kind>` beside it, or that `<kind>`."""
    name = column[len("born_"):] if column.startswith("born_") else column
    if name in NOT_A_BLOCK:
        return False
    return f"born_{name}" in header and name in header


_memo = {}


def blocks(header):
    """The kinds of block a body of this run is made of, in the order the census writes them."""
    key = tuple(header)
    if key not in _memo:
        _memo[key] = [c[len("born_"):] for c in header if c.startswith("born_") and is_block(c, header)]
    return _memo[key]


def born(header):
    """The same columns as they are named at birth."""
    return [f"born_{b}" for b in blocks(header)]
