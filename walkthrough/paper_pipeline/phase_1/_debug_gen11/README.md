# gen-11 failure debugging

Temporary working directory for the gen-11 translation post-mortem
(2026-08-15). One notes file per FAILURE CLASS, named `class_<slug>.md`.

Rules for these files:
* A class is a MECHANISM, not a `check_id`. Two clauses share a class when
  the same thing went wrong for the same reason, whatever the checker said.
  (`undeclared-body-name` was 32 findings and at least three mechanisms.)
* Every claim carries evidence: clause ids, VERBATIM document text, the
  finding text, and the attempt number it appeared on.
* Recoveries count. A module that translated on attempt 4 cost three paid
  rounds and is evidence about the same mechanisms.
* Write the FALSIFIER: what result would show the hypothesis is wrong.
* Do not propose a fix in the analysis pass. Fixes are phase B, and they
  are tested with Haiku subagents before anything is written into a prompt.

Not for permanent record — findings that survive get promoted into
EXPERIMENTS.md with their grounds.
