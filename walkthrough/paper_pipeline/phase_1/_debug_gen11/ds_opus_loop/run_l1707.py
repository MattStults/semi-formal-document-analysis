#!/usr/bin/env python3
"""Thin driver for clause l1707_1973_n006.

Reuses `loop.py` unmodified (it is proven and other clauses' records live in
the same `out/`).  Only two module-level constants are rebound, and both are
narrowing, never widening:

  * CLAUSES  -> this clause alone, so `ledger_spent()` measures THIS clause's
    spend and does not inherit the proof run's $0.019.
  * CAP_USD  -> $0.03, the owner-set cap for this clause.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import loop                                                   # noqa: E402

loop.CLAUSES = ["l1707_1973_n006"]
loop.CAP_USD = 0.03

if __name__ == "__main__":
    raise SystemExit(loop.main())
