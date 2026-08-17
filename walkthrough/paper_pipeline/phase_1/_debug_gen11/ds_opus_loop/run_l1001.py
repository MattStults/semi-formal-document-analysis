#!/usr/bin/env python3
"""Thin driver for clause l1001_1107_n005 (clause 6 of 15).

Copies `run_l699.py` exactly; `loop.py` is unmodified.  Two module-level
constants are rebound, both narrowing, never widening:

  * CLAUSES -> this clause alone, so `ledger_spent()` measures THIS clause's
    spend and does not inherit prior runs' spend.
  * CAP_USD -> $0.03, the owner-set cap for this clause.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import loop                                                   # noqa: E402

loop.CLAUSES = ["l1001_1107_n005"]
loop.CAP_USD = 0.03

if __name__ == "__main__":
    raise SystemExit(loop.main())
