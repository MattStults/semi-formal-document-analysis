# PROPOSED — the arity half of D4b, in `schema.py`  (DC-5)

**Status: PROPOSED, NOT APPLIED.** `schema.py` is guard-watched; this diff needs
the owner's review-and-accept. The working half of DC-5 is **already implemented
and pinned in `checks.py` / `test_checks.py`**, and every path that decides an
outcome runs through it. This file records the residual, the exact diff that
would close it, and the registration the diff would owe.

## What is already done (no schema change needed for it)

`checks.py` gained `declared_arities` / `body_uses` / `arity_mismatches` /
`arity_findings`, called from `run_checks` immediately after the abstention
return. A mismatch is emitted as an `error` with `check_id="schema-breach"` and
`origin="schema"` — the same id and origin D4b's own breaches carry, which is
required rather than cosmetic: `translate.py`'s `DISCLOSABLE_ORIGINS` is a fixed
tuple, so a newly invented origin would be **withheld from the repair prompt this
check exists to inform**.

Message shape, on the real instance:

> `conflict` is declared at `conflict/2` but a body uses it at `conflict/3`. A
> predicate's identity is its name AND its argument count, so those are two
> different predicates and only one of them is declared. Either the declaration
> in `ontology`/`requires`/`inputs` or the body atom has the wrong number of
> arguments — this is INSIDE this module, not a missing upstream clause.

Against today's:

> `conflict/3` is used in a body, defined nowhere in this link scope, and
> declared neither in `%% inputs:` nor in `%% requires:` nor in the concept table

## The residual this diff would close

`run_checks` is the gate for the repair loop (`translate.py:2557`) and for the
worked-example check (`test_prompt_examples.py:101`), so nothing that decides an
outcome escapes the check. What escapes it is a **direct `schema.validate`
caller** — `translate.parse_module` (:1044), `translate.py`'s prompt self-test
(:1760), `seats.py:1727`, and a number of test fixtures. Those see an
arity-mismatched module as clean. None of them gates a translation today; the
cost of the gap is that `schema.validate` alone does not mean what it appears to
mean.

## The diff

`schema.py`, in `Module._coherent`, immediately after the D4b level-1 loop that
ends at :877. **The existing name-only loop is left exactly as it is** — it is
located by phrase by `mutate_schema.py` and it owns the undeclared case.

```diff
@@ schema.py — after the `body references ... but nothing declares it` loop
+        # D4b level 1b: a name that IS declared must be declared AT THE ARITY
+        # THE BODY USES. Matching by name alone (the `declared`/`known` sets
+        # above) legalises `inputs: ['conflict/2']` against a body atom
+        # `conflict(P1, P2, C)`; the module then passes with ZERO breaches and
+        # the mismatch surfaces at LINK stage reading like a missing upstream
+        # module, so repair rounds are spent on someone else's export. Four
+        # instances corpus-wide in prompt generation 11, ALL FOUR on
+        # `unrepaired` clauses. A predicate's identity is name AND arity —
+        # which is exactly why the `requires`/`inputs` format guard above
+        # refuses an entry that is not `name/arity`.
+        # ⛔ Fires ONLY on a name that is declared somewhere here. An
+        # undeclared name stays with the loop above: one defect, one message.
+        def _arity(argstr):
+            inner = argstr.strip()[1:-1] if argstr.strip() else ""
+            return 0 if not inner.strip() else len(_split_args(inner))
+
+        sites = {}
+        for f in self.ontology:
+            head = f.atom.strip()
+            nm = head.split("(")[0].strip()
+            sites.setdefault(nm, set()).add(
+                _arity(head[len(nm):]) if "(" in head else 0)
+        for p in self.requires + self.inputs:
+            nm, _, ar = p.partition("/")
+            slot = sites.setdefault(nm.strip(), set())
+            if ar.strip().isdigit():
+                slot.add(int(ar.strip()))
+        for item in (*self.asserts, *self.beats, *self.ontology):
+            body = getattr(item, "body", None) or ""
+            for nm, used in _body_uses(body):
+                if nm in RESERVED or nm not in sites or used in sites[nm]:
+                    continue
+                errs.append(
+                    f"`{nm}` is declared at "
+                    f"{', '.join(f'`{nm}/{a}`' for a in sorted(sites[nm]))} "
+                    f"but a body uses it at `{nm}/{used}`. A predicate's "
+                    f"identity is its name AND its argument count, so those "
+                    f"are two different predicates and only one of them is "
+                    f"declared. Either the declaration in "
+                    f"`ontology`/`requires`/`inputs` or the body atom has the "
+                    f"wrong number of arguments — this is INSIDE this module, "
+                    f"not a missing upstream clause")
```

`_split_args` / `_body_uses` are the two depth-aware helpers; `schema.py` cannot
import them from `checks.py` (`checks` imports `schema`, so that is a cycle).
Either copy them, or lift them into `link.py`, which already has `_split_top` and
`_atom_id` and is imported by both. **`link.py` is on the do-not-touch list for
this task**, so the copy is what is drafted here.

## What the diff would owe on top of itself

* **Registration, not documentation.** A new `schema.py` guard is located by
  PHRASE, so `mutate_schema.py` needs a mutant for it (drop the `used in
  sites[nm]` test, or the `nm not in sites` test) or the guard is unmeasured.
* **The pins move, they do not duplicate.** `test_checks.py` §8 already carries
  eleven of them, including
  `test_the_three_buildable_instances_pass_schema_with_ZERO_breaches`, which is
  written as a MEASUREMENT of the defect and will fail the moment this diff
  lands — deliberately. Its docstring says so. Reversing that test (breaches now
  non-empty, message contains `ARITY_MESSAGE_MARK`) is part of accepting the
  diff, and `checks.arity_findings` should then be deleted rather than left to
  emit a duplicate of a schema breach.
* **A contract change mid-run invalidates `contract_hash`.** Same caution
  `TRANSLATION_FIX_PLAN.md` records for every schema-stage fix: do not land it
  while a batched corpus run is in flight.
