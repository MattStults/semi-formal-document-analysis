#!/usr/bin/env python3
"""H1 arm runner — the baseline driver, with ONE thing different.

⛔ IT DOES NOT COPY `stage4_baseline/stage4_driver.py`. It imports it and
wraps `seats.plan_clause`, so every other decision in the run — the corpus,
the readback, the denominators, the seam, the budget gate, the raw-reply
dump — is byte-identical to the arm it is compared against. A forked copy of
a 600-line driver is how two "identical" arms stop being identical.

The one difference: 4c is handed the judged node's NEEDS block (name + the
decomposer's prose) via `seats.build_4c_prompt(borrowed_concepts=…)`.

Usage is the baseline driver's, unchanged:

    PY _debug_gen11/seat_fix/run_h1.py --dry --run … --out … --ids …
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
GEN11 = os.path.dirname(HERE)
PHASE1 = os.path.dirname(GEN11)
for _p in (HERE, os.path.join(GEN11, "stage4_baseline"), PHASE1):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import needs_join                              # noqa: E402
import stage4_driver                           # noqa: E402
import seats                                   # noqa: E402

NEEDS_OF, PROVIDERS_OF = needs_join.load()
_plan_clause = seats.plan_clause


def plan_clause(mod, rb, **kw):
    kw["borrowed_concepts"] = needs_join.borrowed_concepts(
        mod.clause_id, NEEDS_OF, PROVIDERS_OF)
    return _plan_clause(mod, rb, **kw)


seats.plan_clause = plan_clause

if __name__ == "__main__":
    sys.exit(stage4_driver.main() or 0)
