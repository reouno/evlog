"""Shared readers' guards: the schema of a census and the audit of a run.

What lives here is only what decides **how a body is classified** and never changes when a law is
added: which columns a census may hold, which blocks a birth form is made of, the window and the
thresholds a reading used. What a particular law means stays in that experiment's own `sweep.py`.
"""
