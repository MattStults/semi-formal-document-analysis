"""The CYCLE DRIVER — a state machine over typed artifacts that walks an
operator (LLM or human) through ONE fix cycle of the iteration process
(ITERATION_LOOP.md, CYCLE_DESIGN.md **including the 2026-08-04 BINDING
AMENDMENTS**), running mechanical phases itself and halting with a named,
templated blank wherever judgment is required.

WHY THIS EXISTS. The loop's tools (snapshot.py, dossier.py,
audit_disagreements.py) each cover one leg; the transitions between them
lived only in session transcripts — exactly the reproducibility violation
class REPRODUCIBILITY.md names, and where every recorded operator error
happened. This module makes the transitions typed artifacts on disk under
`cycles/<cycle_name>/`: `cycle.py status` says where you are and what is
needed; `cycle.py next` either runs the next mechanical phase or halts,
naming the artifact judgment must produce and writing its template.

CYCLE SHAPES (amendment F1). The DEFAULT shape is "code" — a code/matching
fix — whose phases are OPEN → PREDICT → IMPLEMENT → MEASURE → ADJUDICATE →
DECIDE → CLOSE, with `census: deferred_to_checkpoint` recorded. The default
path NEVER touches audit_disagreements: per-cycle census-checking would make
fix selection coordinate descent on panel-derived counts. The CHECKPOINT
shape (declared in the manifest) adds a CENSUS phase between ADJUDICATE and
DECIDE; every census-derived number it produces is stamped DEV and the close
log records `census_consulted: true`.
    EXTENSION POINT (v2): annotation-cycle and selection-cycle shapes are
NOT built; they would add members to PHASES_BY_SHAPE and their own manifest
validation branch in `_open`.

THE FREEZE (amendment F5). BOTH manifest.json and prediction.json are
sha256-frozen when PREDICT validates; every later `status`/`next` re-hashes
both and a mismatch is a hard error naming both shas. Manifest changes are
legal only via a loud `manifest_amendments.json` chain, echoed by every
`status`. PREDICT may be overridden but that DEMOTES the cycle to
exploratory — CLOSE refuses to record `keep`. ADJUDICATE validation and the
DECIDE signature are non-overridable. The one-variable check is TWO-SIDED:
declared files must change AND a sha-pinned closure of undeclared inputs
(captured at OPEN) must not.

WHAT THIS MODULE ORCHESTRATES, NEVER REIMPLEMENTS. snapshot / dossier /
audit_disagreements are driven as subprocesses with real exit codes
propagated (the repo has a recorded incident of `| tail` swallowing a gate).
The two validators keep their differing flag spellings — `--verdict-file`
for dossier.py (the plural is a FORBIDDEN token), `--verdicts` for
audit_disagreements.py (panel-reading by design) — do not "harmonize" them
(amendment F9). This module is panel-adjacent: checkpoint cycles drive the
census tooling, so `cycle` joins FORBIDDEN in test_no_reference_leak.py the
same way `audit_disagreements` did — a query module importing this one
reaches the panel. cycle.py itself may import audit_disagreements /
benchmark freely; the fence is disclosure to the DRIVER, never to query
time.

DETERMINISM CONTRACT. No wall clock anywhere — every date comes from the
manifest (atom_refactor.py's caller-supplied-date pattern). Every artifact
this module writes is sorted-keys canonical JSON with a trailing newline;
same inputs → byte-identical state, templates and assignments. Paths inside
emitted artifacts are RELATIVE (to the cycle dir or the repo) for the same
reason. Snapshot tags are IMMUTABLE (amendment F3): the driver builds the
cycle snapshot into a cycle-local dir and refuses to publish over an
existing `snapshots/<tag>.json` whose content differs.

Usage:
    cycle.py status [--cycle NAME]
    cycle.py next   [--cycle NAME] [--override PHASE --reason "..."]
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

#: The repo the tools and the manifest's relative paths resolve against.
REPO = HERE
#: All cycle state lives here: cycles/<cycle_name>/ + cycles/CYCLE_LOG.jsonl.
CYCLES_ROOT = os.path.join(HERE, "cycles")
#: Where snapshots are read and (immutably) published.
SNAPSHOT_DIR = os.path.join(HERE, "snapshots")

#: The interpreter every subprocess runs under — the one running the driver.
PYTHON = sys.executable

#: THE DEV CELLS (ITERATION_LOOP.md policy §5; amendment F7). The census may
#: touch ONLY these behaviours; the constitution cells (and any future
#: behaviour) are HELD-OUT TEST, and touching one outside a pre-registered
#: checkpoint is a non-overridable refusal.
DEV_CENSUS_CELLS = ("avoiding-over-and-under-caution",
                    "harm-avoidance-to-third-parties",
                    "helpfulness")

#: Phase order per cycle shape (amendment F1). CLOSED is terminal.
PHASES_BY_SHAPE = {
    "code": ("OPEN", "PREDICT", "IMPLEMENT", "MEASURE", "ADJUDICATE",
             "DECIDE", "CLOSE"),
    "checkpoint": ("OPEN", "PREDICT", "IMPLEMENT", "MEASURE", "ADJUDICATE",
                   "CENSUS", "DECIDE", "CLOSE"),
    # EXTENSION POINT (v2): "annotation" and "selection" shapes go here.
}

#: Gates an operator may skip LOUDLY. ADJUDICATE validation and the DECIDE
#: signature are NON-OVERRIDABLE (amendment F5); OPEN produces artifacts
#: every later phase needs; MEASURE is mechanical. Overriding PREDICT is
#: legal but DEMOTES the cycle to exploratory (CLOSE refuses `keep`).
OVERRIDABLE = ("PREDICT", "IMPLEMENT", "CENSUS")

#: Policy §4 flip budget: more flips than this halts MEASURE with the
#: split-or-stratify template. The first customer measured 34.
FLIP_BUDGET = 30

DIRECTIONS = ("newly_predicted", "no_longer_predicted")
DECISION_VALUES = ("keep", "revert")

#: Undeclared inputs whose sha-pinned closure is captured at OPEN (amendment
#: F5, two-sided check): the standard query-side artifacts, when present.
CLOSURE_DEFAULTS = ("modelspec_clauses.json", "constitution_clauses.json",
                    "behaviours_query.json")

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


# ------------------------------------------------------------------ errors

class CycleError(RuntimeError):
    """A refusal: invalid artifact, invalid override, invalid decision."""


class PredictionTampered(CycleError):
    """prediction.json no longer matches the sha frozen at PREDICT."""


class ManifestTampered(CycleError):
    """manifest.json changed after the PREDICT freeze without a
    manifest_amendments.json entry covering the change (amendment F5)."""


class ToolFailed(CycleError):
    """A driven subprocess exited nonzero; `code` is its real exit code,
    propagated (never swallowed — the `| tail` incident)."""

    def __init__(self, msg: str, code: int):
        super().__init__(msg)
        self.code = code


# --------------------------------------------------------------- plumbing

def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def canonical_bytes(obj) -> bytes:
    """THE canonical serialization for everything this module writes —
    sorted keys, indent=1, trailing newline (snapshot.snapshot_bytes'
    convention, restated so the default path never imports the scorer)."""
    return (json.dumps(obj, sort_keys=True, indent=1,
                       ensure_ascii=False) + "\n").encode("utf-8")


def _write_json(path: str, obj) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(canonical_bytes(obj))


def _write_text(path: str, text: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(text)


def _read_json(path: str):
    with open(path) as f:
        return json.load(f)


def _run(argv, cwd=None):
    """Run one tool subprocess, inheriting stdio so the operator sees the
    tool's own output, and RAISE with the real exit code on failure. Every
    external invocation goes through here (tests monkeypatch this)."""
    proc = subprocess.run([str(a) for a in argv], cwd=cwd or REPO)
    if proc.returncode != 0:
        raise ToolFailed(
            f"command failed with exit code {proc.returncode}: "
            f"{' '.join(str(a) for a in argv)}", proc.returncode)
    return proc


def _clear_pycache() -> None:
    shutil.rmtree(os.path.join(REPO, "__pycache__"), ignore_errors=True)


def _taxonomy() -> dict:
    """The closed cause taxonomy, from the tool that owns it. CHECKPOINT
    SHAPE ONLY — the default path never imports audit_disagreements (F1)."""
    import audit_disagreements
    return audit_disagreements.CAUSE_TAXONOMY


def _dir_set_sha(d: str) -> str:
    """Identity of a dossier set: sha256 over the sorted (name, sha) pairs
    of every file in the directory (amendment F3 — verdicts bind to this)."""
    h = hashlib.sha256()
    for name in sorted(os.listdir(d)):
        p = os.path.join(d, name)
        if os.path.isfile(p):
            h.update(name.encode() + b"\0"
                     + sha256_file(p).encode() + b"\n")
    return h.hexdigest()


def _cause_counts(verdicts: list) -> dict:
    return dict(sorted(collections.Counter(
        v.get("cause") for v in verdicts).items()))


# -------------------------------------------------------------- templates

def manifest_template(name: str) -> dict:
    return {
        "cycle_name": name,
        "date": "YYYY-MM-DD",
        "shape": "code",
        "census_scope": "dev",
        "fix_description": "",
        "document_side_rationale": "",
        "files_to_change": [],
        "gate_tests": [],
        "review_required": True,
        "baseline_snapshot_tag": "",
        "compatibility": {"version_key": "", "statement": ""},
        # checkpoint shape additionally requires "baseline_census": the
        # NAMED prior census artifact deltas are computed against (F2).
        "config": {"annotations": "", "atoms": "", "overlay": None,
                   "thresholds": None},
    }


REQUIRED_MANIFEST_KEYS = (
    "cycle_name", "date", "shape", "census_scope", "fix_description",
    "document_side_rationale", "files_to_change", "gate_tests",
    "review_required", "baseline_snapshot_tag", "config")

FLIPS_ASSIGNMENT = """\
# Flip adjudication assignment — cycle {name}

Seat brief: briefs/flip_adjudicator.md — read it first; it is the seat's
entire instruction. Judge each flip AGAINST THE DOCUMENT, from the dossier
alone.

Dossiers: flip_dossiers/ under this cycle's directory. Enumerate the work via
flip_dossiers/index.jsonl — one JSON dossier file per flip.

Dossier set sha256: {set_sha}

Required output: flip_verdicts.json in this cycle's directory:

    {{"dossier_set_sha": "{set_sha}",
      "records": [
        {{"flip_id": "<copied verbatim from the dossier>",
          "verdict": "correct" | "regression" | "unclear",
          "document_reason": "<document-side reason, citing the clause>",
          "confidence": "high" | "medium" | "low"}},
        ...]}}

The dossier_set_sha above MUST be echoed verbatim — it binds your verdicts
to exactly this dossier set. flip_id, verdict, document_reason are REQUIRED
per record; confidence optional. Every flip in index.jsonl exactly once.
Reusing a previous adjudication is legal ONLY when the dossier bytes are
identical (same set sha) and declared via a "reused_from" key naming the
source file — never presented as fresh adjudication. The file is checked by
`dossier.py validate` before the cycle advances.
"""

REVIEW_ASSIGNMENT = """\
# Change review assignment — cycle {name}

Seat brief: briefs/change_reviewer.md — read it first; it is the seat's
entire instruction. This is a frontier/careful seat: it exists to catch the
implementer's mistakes, so the small-model standard does not apply.

Change under review (from the manifest):

- fix_description: {fix}
- document_side_rationale: {rationale}
- files_to_change: {files}
- gate_tests: {gates}

Required output: review_verdict.json in this cycle's directory:

    {{"verdict": "proceed" | "blocked",
      "by": "<who reviewed — never the implementer>",
      "notes": "<what was verified, or why blocked>"}}

All three keys are REQUIRED; verdict is a CLOSED set. The driver re-checks
the frozen manifest/prediction shas, the two-sided one-variable check and
the gate tests mechanically; your seat verifies what the machine cannot
(see the brief: freeze shas, declared-diff-only, tests bind — at least one
mutant — and the fence scan). A "blocked" verdict halts the cycle until
resolved and re-reviewed.
"""

CENSUS_ASSIGNMENT = """\
# Census seat assignment — cycle {name}, behaviour {slug}  [CHECKPOINT]

Seat brief: briefs/disagreement_autopsy.md — read it first. This seat SEES
panel verdicts by design; the fence is disclosure, not blindness — nothing
from it may edit a vocabulary, query, weight or threshold directly. Every
number derived from this census is a DEV number.

Dossiers: census/audit_dossiers/{tag}/ under this cycle's directory.
Enumerate via its index.jsonl, restricted to records with
"behaviour": "{slug}".

Dossier set sha256: {set_sha}

Required output: census/verdicts_{slug}.json in this cycle's directory:

    {{"dossier_set_sha": "{set_sha}",
      "records": [
        {{"dossier_id": "<copied verbatim>",
          "cause": "<one CAUSE_TAXONOMY member>",
          "side": "tool" | "panel" | "both_defensible",
          "note": "<one or two sentences citing the dossier facts used>",
          "sweep_core_evidence": ["<atom>", ...]}},
        ...]}}

sweep_core_evidence is optional (see fn_family_unselected). Every dossier of
this behaviour exactly once. The merged file is checked by
`audit_disagreements.py validate` before the cycle advances.
"""

BUDGET_HALT = """\
HALT (MEASURE): FLIP BUDGET EXCEEDED — {n} flips > {budget}
(ITERATION_LOOP.md policy §4: a big delta is a finding; the change is too
coarse). Choose, in flip_budget_plan.json:

    {{"resolution": "split",
      "rationale": "<how the change will be split into smaller cycles>"}}

  — then revert this cycle (DECIDE: revert) and open one cycle per piece; OR

    {{"resolution": "stratified_sample",
      "rationale": "<the PRE-REGISTERED strata: behaviour x direction x
                    cause — never label-selected sampling>"}}

  — then `next` proceeds, dossiers all flips, and the seat adjudicates the
declared strata. The plan is pre-registered: it is written BEFORE any
dossier is read.
"""


# ------------------------------------------------------------------ Cycle

class Cycle:
    """One cycle directory under CYCLES_ROOT, with state.json derived and
    updated by the driver. All judgment artifacts (manifest, prediction,
    review verdict, seat verdicts, signed decision) are written by the
    OPERATOR; everything else is written here, deterministically."""

    def __init__(self, name: str, root: str | None = None):
        self.name = name
        self.dir = os.path.join(root or CYCLES_ROOT, name)

    # ---------------------------------------------------------- state

    @property
    def state_path(self) -> str:
        return os.path.join(self.dir, "state.json")

    def _state(self) -> dict:
        if os.path.exists(self.state_path):
            return _read_json(self.state_path)
        return {"cycle": self.name, "completed": [], "overrides": [],
                "skipped": {}, "closed": False}

    def _save(self, state: dict) -> None:
        _write_json(self.state_path, state)

    def _p(self, *parts) -> str:
        return os.path.join(self.dir, *parts)

    def _manifest(self) -> dict:
        return _read_json(self._p("manifest.json"))

    def _shape(self) -> str:
        mpath = self._p("manifest.json")
        if os.path.exists(mpath):
            shape = self._manifest().get("shape", "code")
            if shape in PHASES_BY_SHAPE:
                return shape
        return "code"

    def _phases(self):
        return PHASES_BY_SHAPE[self._shape()]

    def phase(self) -> str:
        self._check_freeze()
        return self._phase_of(self._state())

    def _phase_of(self, state: dict) -> str:
        for p in self._phases():
            if p not in state["completed"]:
                return p
        return "CLOSED"

    # ---------------------------------------------------------- freeze

    def _amendment_chain(self) -> list:
        apath = self._p("manifest_amendments.json")
        return _read_json(apath) if os.path.exists(apath) else []

    def _check_freeze(self) -> None:
        """THE FREEZE (amendment F5): after PREDICT, prediction.json AND
        manifest.json are pinned; any silent change is a hard error naming
        both shas. Manifest edits are legal only through the loud
        manifest_amendments.json chain."""
        state = self._state()
        frozen = state.get("frozen_prediction_sha")
        if frozen:
            ppath = self._p("prediction.json")
            if not os.path.exists(ppath):
                raise PredictionTampered(
                    f"prediction.json was DELETED after the freeze (frozen "
                    f"sha256 {frozen}) — the frozen prediction is the "
                    f"contract; restore the file.")
            now = sha256_file(ppath)
            if now != frozen:
                raise PredictionTampered(
                    f"prediction.json changed AFTER the freeze: frozen "
                    f"sha256 {frozen}, on disk now {now}. Predictions are "
                    f"checked against the outcome, never edited to fit it; "
                    f"restore the frozen bytes (a genuinely new prediction "
                    f"means a new cycle).")
        mfrozen = state.get("frozen_manifest_sha")
        if mfrozen and os.path.exists(self._p("manifest.json")):
            now = sha256_file(self._p("manifest.json"))
            expected = mfrozen
            for amend in self._amendment_chain():
                if amend.get("old_sha") == expected and \
                        str(amend.get("reason", "")).strip():
                    expected = amend.get("new_sha")
            if now != expected:
                raise ManifestTampered(
                    f"manifest.json changed AFTER the freeze without an "
                    f"amendment: expected sha256 {expected} (frozen "
                    f"{mfrozen} plus {len(self._amendment_chain())} "
                    f"amendment(s)), on disk now {now}. Manifest changes "
                    f"go through manifest_amendments.json — a list of "
                    f"{{reason, old_sha, new_sha}} records chaining from "
                    f"the frozen sha to the current file — never silent "
                    f"edits.")

    # ---------------------------------------------------------- status

    def status(self) -> str:
        self._check_freeze()
        state = self._state()
        phase = self._phase_of(state)
        lines = [f"cycle: {self.name}  (shape: {self._shape()})",
                 f"phase: {phase}"]
        for ov in state["overrides"]:
            lines.append(f"⚠ OVERRIDDEN gate: {ov['phase']} — {ov['reason']}")
        if state.get("exploratory"):
            lines.append("⚠ EXPLORATORY cycle (PREDICT overridden): CLOSE "
                         "will refuse decision=keep.")
        for amend in self._amendment_chain():
            lines.append(f"⚠ MANIFEST AMENDED: {amend.get('reason', '')} "
                         f"({str(amend.get('old_sha', ''))[:12]}… → "
                         f"{str(amend.get('new_sha', ''))[:12]}…)")
        for p, why in sorted(state.get("skipped", {}).items()):
            lines.append(f"skipped: {p} — {why}")
        if state.get("noop"):
            lines.append("measured effect: NO-OP (diff found no change)")
        lines.append(self._needed(phase))
        return "\n".join(lines) + "\n"

    def _needed(self, phase: str) -> str:
        need = {
            "OPEN": "needed next: manifest.json in the cycle directory "
                    "(template: manifest.template.json; run `next` to emit "
                    "it). `next` validates it, records the files_to_change "
                    "baseline shas and the undeclared-input closure.",
            "PREDICT": "needed next: prediction.json (template: "
                       "prediction.template.json; run `next` to emit it) — "
                       "mechanism-level targets: expected flip count, "
                       "directions, clauses, max regressions. On validation "
                       "BOTH its sha and the manifest's are FROZEN.",
            "IMPLEMENT": "needed next: the fix itself — gate_tests must "
                         "pass, every files_to_change must differ from its "
                         "OPEN sha, the undeclared-input closure must NOT "
                         "have changed, and (if review_required) "
                         "review_verdict.json must say proceed. Run `next` "
                         "to check the gate.",
            "MEASURE": "needed next: nothing from you — `next` runs "
                       "snapshot + diff + flip dossiers mechanically "
                       "(halting only on the >%d flip budget)."
                       % FLIP_BUDGET,
            "ADJUDICATE": "needed next: flip_verdicts.json per "
                          "assignments/flips.md (must echo the "
                          "dossier_set_sha); `next` validates it via "
                          "dossier.py.",
            "CENSUS": "needed next (CHECKPOINT): per-behaviour census "
                      "verdict files per assignments/census_<behaviour>.md;"
                      " `next` runs the mechanical parts, the DEV-stamped "
                      "deltas and the frozen census-class check.",
            "DECIDE": "needed next: decision.json (draft with computed "
                      "fields: decision.draft.json; run `next` to emit it) "
                      "with decision keep|revert and signed_by filled.",
            "CLOSE": "needed next: nothing from you — `next` appends the "
                     "CYCLE_LOG.jsonl line and closes the cycle.",
            "CLOSED": "this cycle is closed.",
        }
        return need[phase]

    # ------------------------------------------------------------ next

    def next(self, override: str | None = None,
             reason: str | None = None) -> str:
        self._check_freeze()
        state = self._state()
        phase = self._phase_of(state)
        if override is not None:
            return self._override(state, phase, override, reason)
        if phase == "CLOSED":
            return "cycle is closed — nothing to run."
        runner = getattr(self, "_" + phase.lower())
        done, msg = runner(state)
        if done:
            state = self._state()  # runners may have saved intermediate state
            state["completed"].append(phase)
            self._save(state)
        return msg

    def _override(self, state, phase, override, reason) -> str:
        if not (isinstance(reason, str) and reason.strip()):
            raise CycleError("--override requires a non-empty --reason: an "
                             "unexplained skipped gate is indistinguishable "
                             "from a forgotten one.")
        if override != phase:
            raise CycleError(
                f"--override names {override!r} but the current phase is "
                f"{phase!r}: only the gate actually in front of you can be "
                f"skipped.")
        if override not in OVERRIDABLE:
            raise CycleError(
                f"phase {override!r} is non-overridable (only "
                f"{', '.join(OVERRIDABLE)} can be skipped): OPEN produces "
                f"the artifacts every later phase needs, MEASURE is "
                f"mechanical, ADJUDICATE validation and the DECIDE "
                f"signature cannot be waived (amendment F5).")
        state["overrides"].append({"phase": override,
                                   "reason": reason.strip()})
        state["completed"].append(override)
        extra = ""
        if override == "PREDICT":
            # amendment F5: skipping the freeze demotes the cycle — no
            # prediction means no falsifiable target, so no KEEP.
            state["exploratory"] = True
            if os.path.exists(self._p("manifest.json")):
                state["frozen_manifest_sha"] = sha256_file(
                    self._p("manifest.json"))
            extra = ("\nCycle DEMOTED to exploratory: CLOSE will refuse "
                     "decision=keep.")
        self._save(state)
        return (f"⚠ GATE OVERRIDDEN: {override} skipped — {reason.strip()}\n"
                f"Recorded in state.json; every later `status` echoes it, "
                f"and the DECIDE signature will require a justification."
                + extra)

    # ---------------------------------------------------- phase 1: OPEN

    def _open(self, state) -> tuple[bool, str]:
        mpath = self._p("manifest.json")
        if not os.path.exists(mpath):
            tpath = self._p("manifest.template.json")
            if not os.path.exists(tpath):
                _write_json(tpath, manifest_template(self.name))
            return False, (
                "HALT (OPEN): judgment required — fill in manifest.json.\n"
                f"Template written: manifest.template.json (in {self.dir}).\n"
                "Copy it to manifest.json and fill every field; `next` then "
                "validates it.")
        m = _read_json(mpath)
        problems = [f"missing key: {k}" for k in REQUIRED_MANIFEST_KEYS
                    if k not in m]
        if problems:
            raise CycleError("manifest.json invalid: " + "; ".join(problems))
        if m["cycle_name"] != self.name:
            problems.append(f"cycle_name {m['cycle_name']!r} != directory "
                            f"name {self.name!r}")
        if not _DATE_RE.match(str(m["date"])):
            problems.append(f"date {m['date']!r} is not YYYY-MM-DD (dates "
                            "are caller-supplied — no wall clock)")
        shape = m.get("shape")
        if shape not in PHASES_BY_SHAPE:
            problems.append(f"shape {shape!r} not in "
                            f"{sorted(PHASES_BY_SHAPE)} (EXTENSION POINT "
                            f"(v2): annotation/selection shapes)")
        if m.get("census_scope") != "dev":
            problems.append(
                f"census_scope must be 'dev' (got {m.get('census_scope')!r})"
                f" — the held-out cells are never consulted during "
                f"iteration (policy §5, amendment F7)")
        for field in ("fix_description", "document_side_rationale"):
            if not str(m.get(field, "")).strip():
                problems.append(f"{field} is empty")
        if not isinstance(m["review_required"], bool):
            problems.append("review_required must be a bool")
        if shape == "code":
            if not m["files_to_change"]:
                problems.append("files_to_change is empty — a code fix "
                                "cycle changes something")
            compat = m.get("compatibility") or {}
            if not (str(compat.get("version_key", "")).strip()
                    and str(compat.get("statement", "")).strip()):
                problems.append(
                    "compatibility.version_key / compatibility.statement "
                    "required for a code fix (amendment F9): the old "
                    "behavior must remain reachable via a version recorded "
                    "in snapshot config (the PRICING_VERSION pattern), or "
                    "the baseline side cannot reconstruct.")
        if shape == "checkpoint" and not str(
                m.get("baseline_census", "")).strip():
            problems.append("baseline_census required for a checkpoint "
                            "cycle: deltas are computed against a NAMED "
                            "prior census artifact, never a directory "
                            "(amendment F2)")
        for rel in list(m["files_to_change"]) + list(m["gate_tests"]):
            if not os.path.exists(os.path.join(REPO, rel)):
                problems.append(f"path does not exist: {rel}")
        cfg = m.get("config") or {}
        for key in ("annotations", "atoms"):
            if not cfg.get(key):
                problems.append(f"config.{key} is empty")
            elif not os.path.exists(os.path.join(REPO, cfg[key])):
                problems.append(f"config.{key} path does not exist: "
                                f"{cfg[key]}")
        for opt in ("overlay", "thresholds"):
            if cfg.get(opt) and not os.path.exists(
                    os.path.join(REPO, cfg[opt])):
                problems.append(f"config.{opt} path does not exist: "
                                f"{cfg[opt]}")
        if not str(m["baseline_snapshot_tag"]).strip():
            problems.append("baseline_snapshot_tag is empty")
        if problems:
            raise CycleError("manifest.json invalid: " + "; ".join(problems))
        # the IMPLEMENT gate's "declared files changed" baseline...
        state["open_shas"] = {
            rel: sha256_file(os.path.join(REPO, rel))
            for rel in sorted(m["files_to_change"])}
        # ...and the two-sided closure: undeclared inputs pinned (F5)
        closure = set(m["gate_tests"]) | {cfg["annotations"], cfg["atoms"]}
        for opt in ("overlay", "thresholds"):
            if cfg.get(opt):
                closure.add(cfg[opt])
        for rel in CLOSURE_DEFAULTS:
            if os.path.exists(os.path.join(REPO, rel)):
                closure.add(rel)
        closure -= set(m["files_to_change"])
        state["closure_shas"] = {
            rel: sha256_file(os.path.join(REPO, rel))
            for rel in sorted(closure)}
        if shape == "code":
            state["census"] = "deferred_to_checkpoint"
        self._save(state)
        return True, ("OPEN complete: manifest validated; files_to_change "
                      "baseline shas and the undeclared-input closure "
                      "recorded in state.json."
                      + self._prior_uncommitted_warning())

    def _prior_uncommitted_warning(self) -> str:
        """F12 ruling: OPEN WARNS (never refuses) when a prior cycle closed
        with a drafted commit_message.txt whose declared files are still
        uncommitted — the exact drift the sha-closure guard exists to catch,
        surfaced at the moment new work opens. Read-only: a single
        `git status --porcelain` per prior draft; git absence, a non-repo
        tree, or any git error silently yields no warning (git is never an
        OPEN dependency)."""
        warnings = []
        root = os.path.dirname(self.dir)
        if not os.path.isdir(root):
            return ""
        for name in sorted(os.listdir(root)):
            if name == self.name:
                continue
            cdir = os.path.join(root, name)
            slist = os.path.join(cdir, "staging_list.txt")
            if not (os.path.isfile(os.path.join(cdir, "commit_message.txt"))
                    and os.path.isfile(slist)):
                continue
            with open(slist) as f:
                declared = [l.strip() for l in f if l.strip()]
            declared = [rel for rel in declared
                        if os.path.exists(os.path.join(REPO, rel))]
            if not declared:
                continue
            try:
                proc = subprocess.run(
                    ["git", "-C", REPO, "status", "--porcelain", "--"]
                    + declared,
                    capture_output=True, text=True)
            except OSError:
                return ""      # no git binary: never an OPEN failure
            if proc.returncode != 0:
                continue       # not a git repo (or git unhappy): stay quiet
            dirty = sorted({l[3:].strip() for l in proc.stdout.splitlines()
                            if l.strip()})
            if dirty:
                warnings.append(
                    f"\n⚠ WARNING (not a refusal): prior cycle {name!r} "
                    f"closed with a drafted commit_message.txt and its "
                    f"declared files are still uncommitted: "
                    f"{', '.join(dirty)}. Commit that cycle before this "
                    f"one's changes interleave with it.")
        return "".join(warnings)

    # ------------------------------------------------- phase 2: PREDICT

    def _baseline_census_path(self):
        rel = str(self._manifest().get("baseline_census", "")).strip()
        return os.path.join(REPO, rel) if rel else None

    def _predict(self, state) -> tuple[bool, str]:
        ppath = self._p("prediction.json")
        checkpoint = self._shape() == "checkpoint"
        if not os.path.exists(ppath):
            tpath = self._p("prediction.template.json")
            if not os.path.exists(tpath):
                tpl = {
                    "expected_flip_count": {"min": 0, "max": 0},
                    "expected_directions": [],
                    "expected_clauses": [],
                    "max_regressions": 0,
                    "notes": "",
                }
                if checkpoint:
                    # census-class predictions are OPTIONAL and checked only
                    # in checkpoint cycles (amendment F1) — only here does
                    # the driver touch the census taxonomy.
                    tpl["census_classes"] = {"expected_shrink": [],
                                             "must_not_grow": []}
                    tpl["_cause_taxonomy"] = sorted(_taxonomy())
                    bpath = self._baseline_census_path()
                    tpl["_baseline_census_counts"] = (
                        _cause_counts(_read_json(bpath))
                        if bpath and os.path.exists(bpath) else None)
                _write_json(tpath, tpl)
            return False, (
                "HALT (PREDICT): judgment required — fill in "
                "prediction.json.\nTemplate written: "
                "prediction.template.json. Targets are MECHANISM-LEVEL "
                "(document-side, checkable with zero panel contact): "
                "expected flip count range, allowed directions, specific "
                "clause ids expected to flip, and the maximum regressions "
                "the adjudication may find. On validation BOTH the "
                "prediction's sha256 AND the manifest's are FROZEN; any "
                "later edit is a hard error.")
        pred = _read_json(ppath)
        problems = []
        fc = pred.get("expected_flip_count")
        if not (isinstance(fc, dict) and isinstance(fc.get("min"), int)
                and isinstance(fc.get("max"), int)
                and 0 <= fc["min"] <= fc["max"]):
            problems.append("expected_flip_count must be {min: int, max: "
                            "int} with 0 <= min <= max")
        dirs = pred.get("expected_directions")
        # An empty direction list is legal iff the prediction is the honest
        # zero-flip one (expected_flip_count.max == 0): zero flips means no
        # direction CAN occur, so [] is the true target — forcing a non-empty
        # fill there weakens nothing and lies (first-customer finding,
        # versioned-cut-2026-08-04 prediction.json FIELD NOTE).
        zero_flips = isinstance(fc, dict) and fc.get("max") == 0
        if not isinstance(dirs, list) or (not dirs and not zero_flips):
            problems.append(
                "expected_directions must be a non-empty list (empty is "
                "legal ONLY when expected_flip_count.max == 0 — the honest "
                "zero-flip prediction, where no direction can occur)")
        else:
            for d in dirs:
                if d not in DIRECTIONS:
                    problems.append(f"expected_directions: {d!r} not in "
                                    f"{DIRECTIONS}")
        if not isinstance(pred.get("expected_clauses", []), list):
            problems.append("expected_clauses must be a list")
        if not (isinstance(pred.get("max_regressions"), int)
                and pred["max_regressions"] >= 0):
            problems.append("max_regressions must be a non-negative int")
        if not isinstance(pred.get("notes", ""), str):
            problems.append("notes must be a string")
        cc = pred.get("census_classes")
        if cc is not None and checkpoint:
            tax = _taxonomy()
            for key in ("expected_shrink", "must_not_grow"):
                for cause in (cc.get(key) or []):
                    if cause not in tax:
                        problems.append(f"census_classes.{key}: {cause!r} "
                                        "not in the closed cause taxonomy")
        if problems:
            raise CycleError("prediction.json invalid: "
                             + "; ".join(problems))
        state["frozen_prediction_sha"] = sha256_file(ppath)
        state["frozen_manifest_sha"] = sha256_file(self._p("manifest.json"))
        self._save(state)
        return True, (f"PREDICT complete: prediction AND manifest FROZEN "
                      f"(prediction sha256 "
                      f"{state['frozen_prediction_sha']}, manifest sha256 "
                      f"{state['frozen_manifest_sha']}).")

    # ----------------------------------------------- phase 3: IMPLEMENT

    def _implement(self, state) -> tuple[bool, str]:
        m = self._manifest()
        # (a) gate tests — pycache cleared, exit code propagated by _run
        if m["gate_tests"]:
            _clear_pycache()
            _run([PYTHON, "-m", "pytest", *m["gate_tests"], "-q"], cwd=REPO)
        # (b) TWO-SIDED one-variable check (amendment F5):
        #     declared files changed...
        unchanged = [rel for rel, sha in sorted(state["open_shas"].items())
                     if sha256_file(os.path.join(REPO, rel)) == sha]
        if unchanged:
            return False, (
                "HALT (IMPLEMENT): gate tests pass but these "
                "files_to_change are byte-identical to their OPEN shas — "
                "the fix has not been implemented: "
                + ", ".join(unchanged))
        #     ...and the sha-pinned closure of undeclared inputs unchanged
        drifted = []
        for rel, sha in sorted(state.get("closure_shas", {}).items()):
            full = os.path.join(REPO, rel)
            if not os.path.exists(full) or sha256_file(full) != sha:
                drifted.append(rel)
        if drifted:
            raise CycleError(
                "UNDECLARED INPUTS CHANGED since OPEN (two-sided "
                "one-variable check, amendment F5 — this workspace has "
                "concurrent agents and no git): "
                + ", ".join(drifted)
                + ". Either restore them, or open a new cycle declaring "
                "them in files_to_change.")
        # (c) review, when the manifest requires one
        review = None
        if m["review_required"]:
            # the review wait-state writes its seat assignment, exactly as
            # ADJUDICATE does — a reviewer without a typed assignment is a
            # transcript-only seat (first-customer finding)
            apath = self._p("assignments", "review.md")
            if not os.path.exists(apath):
                _write_text(apath, REVIEW_ASSIGNMENT.format(
                    name=self.name,
                    fix=m["fix_description"],
                    rationale=m["document_side_rationale"],
                    files=", ".join(m["files_to_change"]),
                    gates=", ".join(m["gate_tests"])))
            rpath = self._p("review_verdict.json")
            if not os.path.exists(rpath):
                return False, (
                    "HALT (IMPLEMENT): review_required — write "
                    "review_verdict.json ({\"verdict\": \"proceed\"|"
                    "\"blocked\", \"by\": ..., \"notes\": ...}) after an "
                    "independent review of the change.\nAssignment "
                    "written: assignments/review.md (brief: "
                    "briefs/change_reviewer.md).")
            review = _read_json(rpath)
            if review.get("verdict") not in ("proceed", "blocked"):
                raise CycleError(
                    f"review_verdict.json: verdict must be proceed|blocked, "
                    f"got {review.get('verdict')!r}")
            if not str(review.get("by", "")).strip():
                raise CycleError("review_verdict.json: 'by' is empty")
            if review["verdict"] == "blocked":
                return False, (
                    "HALT (IMPLEMENT): review verdict is BLOCKED — "
                    f"{review.get('notes', '(no notes)')}\nResolve and "
                    "re-review before advancing.")
        state["gate"] = {
            "tests_passed": sorted(m["gate_tests"]),
            "files_changed": sorted(state["open_shas"]),
            "closure_checked": sorted(state.get("closure_shas", {})),
            "review": review,
        }
        self._save(state)
        return True, ("IMPLEMENT gate passed: gate tests green, all "
                      "files_to_change changed, undeclared-input closure "
                      "intact" + (", review proceed" if review else "")
                      + ".")

    # ------------------------------------------------- phase 4: MEASURE

    def _flip_list(self, diff) -> list:
        out = []
        for slug in sorted(diff.get("behaviours") or {}):
            beh = diff["behaviours"][slug]
            for direction in DIRECTIONS:
                for f in beh.get(direction) or []:
                    out.append({"behaviour": slug,
                                "clause_id": f.get("clause_id"),
                                "direction": direction})
        return out

    def _measure(self, state) -> tuple[bool, str]:
        m = self._manifest()
        base = m["baseline_snapshot_tag"]
        base_path = os.path.join(SNAPSHOT_DIR, base + ".json")
        if not os.path.exists(base_path):
            return False, (
                f"HALT (MEASURE): baseline snapshot {base!r} not found at "
                f"{base_path}. Generate it first (on the PRE-fix code — the "
                f"sandwich rule):\n  {PYTHON} snapshot.py snapshot --tag "
                f"{base} --annotations {m['config']['annotations']} --atoms "
                f"{m['config']['atoms']}")
        cfg = m["config"]
        # build into a cycle-local dir, then publish IMMUTABLY (F3): never
        # overwrite an existing snapshots/<tag>.json with different bytes.
        build_dir = self._p("snapshot_build")
        built = os.path.join(build_dir, self.name + ".json")
        if not os.path.exists(built):
            snap_cmd = [PYTHON, os.path.join(REPO, "snapshot.py"),
                        "snapshot", "--tag", self.name,
                        "--annotations",
                        os.path.join(REPO, cfg["annotations"]),
                        "--atoms", os.path.join(REPO, cfg["atoms"]),
                        "--dir", build_dir]
            if cfg.get("overlay"):
                snap_cmd += ["--overlay",
                             os.path.join(REPO, cfg["overlay"])]
            if cfg.get("thresholds"):
                # the frozen-thresholds artifact threads exactly like the
                # overlay: the flag carries the path; the snapshot itself
                # records the sha in its config identity under "thresholds"
                snap_cmd += ["--thresholds",
                             os.path.join(REPO, cfg["thresholds"])]
            _run(snap_cmd)
        published = os.path.join(SNAPSHOT_DIR, self.name + ".json")
        if os.path.exists(published):
            if sha256_file(published) != sha256_file(built):
                raise CycleError(
                    f"snapshot tag {self.name!r} already exists at "
                    f"{published} with DIFFERENT content than this cycle's "
                    f"build — tags are immutable (amendment F3). Choose a "
                    f"fresh cycle name; never overwrite a published "
                    f"snapshot.")
        else:
            os.makedirs(SNAPSHOT_DIR, exist_ok=True)
            shutil.copyfile(built, published)
        _run([PYTHON, os.path.join(REPO, "snapshot.py"), "diff",
              "--a", base, "--b", self.name, "--dir", SNAPSHOT_DIR,
              "--json", self._p("diff.json")])
        diff = _read_json(self._p("diff.json"))
        if diff.get("noop"):
            # record it and jump to DECIDE with a drafted no-effect
            # decision — nothing to adjudicate.
            state["noop"] = True
            state["flips"] = []
            state["skipped"]["ADJUDICATE"] = "no-op diff: nothing flipped"
            if "CENSUS" in self._phases():
                state["skipped"]["CENSUS"] = "no-op diff: nothing flipped"
                state["completed"].append("CENSUS")
            state["completed"].append("ADJUDICATE")
            self._save(state)
            self._check_predictions_measure(state)
            self._append_vacuous_checks(state)
            self._write_draft(state)
            return True, (
                "MEASURE complete: the diff is a NO-OP (identical config "
                "and scores) — the change had no effect on the tool. "
                "Jumping to DECIDE with a drafted no-effect decision "
                "(decision.draft.json).")
        flips = self._flip_list(diff)
        # THE FLIP BUDGET (policy §4, amendment F4b)
        plan_path = self._p("flip_budget_plan.json")
        if len(flips) > FLIP_BUDGET and not os.path.exists(plan_path):
            return False, BUDGET_HALT.format(n=len(flips),
                                             budget=FLIP_BUDGET)
        if os.path.exists(plan_path):
            plan = _read_json(plan_path)
            if plan.get("resolution") not in ("split", "stratified_sample"):
                raise CycleError(
                    "flip_budget_plan.json: resolution must be 'split' or "
                    f"'stratified_sample', got {plan.get('resolution')!r}")
            if not str(plan.get("rationale", "")).strip():
                raise CycleError("flip_budget_plan.json: rationale is empty")
            if plan["resolution"] == "split":
                return False, (
                    "HALT (MEASURE): flip_budget_plan.json says SPLIT — "
                    "this change is too coarse to adjudicate as one cycle. "
                    "Revert the change, close this cycle as revert, and "
                    "open one cycle per declared piece.")
            state["flip_budget_plan"] = plan
        _run([PYTHON, os.path.join(REPO, "dossier.py"), "dossiers",
              "--a", base, "--b", self.name, "--snap-dir", SNAPSHOT_DIR,
              "--inputs-dir", REPO, "--out-dir", self._p("flip_dossiers")])
        state["flips"] = flips
        state["dossier_set_sha"] = _dir_set_sha(self._p("flip_dossiers"))
        self._save(state)
        self._check_predictions_measure(state)
        return True, (f"MEASURE complete: snapshot {self.name!r} built and "
                      f"published, diffed vs {base!r} ({len(flips)} flips), "
                      f"flip dossiers written to flip_dossiers/ "
                      f"(set sha {state['dossier_set_sha']}).")

    # --------------------------------------- the frozen-prediction checks

    def _prediction(self):
        ppath = self._p("prediction.json")
        return _read_json(ppath) if os.path.exists(ppath) else None

    def _check_predictions_measure(self, state) -> None:
        """Mechanism-level checks decidable at MEASURE: flip count within
        the predicted range, directions within the predicted set, every
        predicted clause actually flipped. Zero panel contact."""
        pred = self._prediction()
        if pred is None:      # exploratory cycle: nothing frozen to check
            return
        flips = state.get("flips") or []
        checks = []
        fc = pred["expected_flip_count"]
        n = len(flips)
        checks.append({"kind": "flip_count", "expected": fc, "observed": n,
                       "result": "PASS" if fc["min"] <= n <= fc["max"]
                       else "FAIL"})
        observed_dirs = sorted({f["direction"] for f in flips})
        checks.append({"kind": "directions",
                       "expected": sorted(pred["expected_directions"]),
                       "observed": observed_dirs,
                       "result": "PASS" if set(observed_dirs)
                       <= set(pred["expected_directions"]) else "FAIL"})
        flipped_ids = {f["clause_id"] for f in flips}
        for cid in pred.get("expected_clauses") or []:
            checks.append({"kind": "expected_clause", "clause": cid,
                           "result": "PASS" if cid in flipped_ids
                           else "FAIL"})
        state.setdefault("prediction_checks", {})["measure"] = checks
        self._save(state)
        self._write_prediction_check(state)

    def _check_predictions_adjudicate(self, state) -> None:
        pred = self._prediction()
        if pred is None:
            return
        regressions = (state.get("flip_tallies") or {}).get("regression", 0)
        checks = [{"kind": "max_regressions",
                   "expected": pred["max_regressions"],
                   "observed": regressions,
                   "result": "PASS" if regressions <= pred["max_regressions"]
                   else "FAIL"}]
        state.setdefault("prediction_checks", {})["adjudicate"] = checks
        self._save(state)
        self._write_prediction_check(state)

    def _append_vacuous_checks(self, state) -> None:
        """The no-op short-circuit skips ADJUDICATE (and CENSUS): every
        frozen prediction target whose checking phase never ran must still
        appear in prediction_check.json — as PASS_VACUOUS with a reason,
        never silently dropped (first-customer finding: the frozen
        max_regressions target vanished from versioned-cut-2026-08-04's
        check). A vacuous pass counts as a pass: with zero flips the target
        cannot be violated."""
        pred = self._prediction()
        if pred is None:      # exploratory cycle: nothing frozen to check
            return
        groups = state.setdefault("prediction_checks", {})
        recorded_kinds = {c.get("kind")
                          for g in groups.values() for c in g}
        recorded_classes = {c.get("class")
                            for g in groups.values() for c in g if "class" in c}
        vacuous = []
        if "max_regressions" not in recorded_kinds:
            vacuous.append({
                "kind": "max_regressions",
                "expected": pred.get("max_regressions"),
                "result": "PASS_VACUOUS",
                "reason": "no-op short-circuit: ADJUDICATE skipped — zero "
                          "flips, so zero regressions are observable and "
                          "the target holds vacuously"})
        cc = pred.get("census_classes") or {}
        for key, kind in (("expected_shrink", "census_shrink"),
                          ("must_not_grow", "census_must_not_grow")):
            for cause in cc.get(key) or []:
                if cause not in recorded_classes:
                    vacuous.append({
                        "kind": kind, "class": cause,
                        "result": "PASS_VACUOUS",
                        "reason": "no-op short-circuit: CENSUS skipped on "
                                  "the no-op path — this frozen census-"
                                  "class target was never checked"})
        if vacuous:
            groups["vacuous"] = vacuous
            self._save(state)
        self._write_prediction_check(state)

    def _write_prediction_check(self, state) -> None:
        groups = state.get("prediction_checks") or {}
        checks = (list(groups.get("measure") or [])
                  + list(groups.get("adjudicate") or [])
                  + list(groups.get("census") or [])
                  + list(groups.get("vacuous") or []))
        if not checks:
            return
        passes = sum(1 for c in checks
                     if c["result"] in ("PASS", "PASS_VACUOUS"))
        out = {"checks": checks, "pass_rate": [passes, len(checks)]}
        if groups.get("census"):
            # census-class checks are panel-derived: DEV numbers, stamped.
            out["stamp"] = "DEV"
        _write_json(self._p("prediction_check.json"), out)

    # ---------------------------------------------- phase 5: ADJUDICATE

    def _adjudicate(self, state) -> tuple[bool, str]:
        set_sha = state.get("dossier_set_sha", "")
        apath = self._p("assignments", "flips.md")
        if not os.path.exists(apath):
            _write_text(apath, FLIPS_ASSIGNMENT.format(name=self.name,
                                                       set_sha=set_sha))
        vpath = self._p("flip_verdicts.json")
        if not os.path.exists(vpath):
            return False, (
                "HALT (ADJUDICATE): judgment required — the "
                "flip-adjudicator seat must produce flip_verdicts.json "
                "(echoing the dossier_set_sha).\nAssignment written: "
                "assignments/flips.md (brief: briefs/flip_adjudicator.md; "
                "dossiers: flip_dossiers/).")
        raw = _read_json(vpath)
        # VERDICT BINDING (amendment F3): the artifact must echo the sha of
        # exactly the dossier set it adjudicated.
        if not isinstance(raw, dict) or "dossier_set_sha" not in raw:
            raise CycleError(
                "flip_verdicts.json must be an object with a "
                "dossier_set_sha key echoing the assignment's sha (plus a "
                "'records' list) — an unbound verdict file cannot prove "
                "which dossiers it adjudicated.")
        if raw["dossier_set_sha"] != set_sha:
            raise CycleError(
                f"flip_verdicts.json is bound to dossier set "
                f"{raw['dossier_set_sha']} but this cycle's dossier set is "
                f"{set_sha} — the verdicts were made over DIFFERENT "
                f"dossiers. Re-adjudicate this set (or carry verdicts "
                f"forward with reused_from only when the set shas match).")
        records = raw.get("records") or []
        _run([PYTHON, os.path.join(REPO, "dossier.py"), "validate",
              "--dir", self._p("flip_dossiers"), "--verdict-file", vpath])
        if raw.get("reused_from"):
            state["flip_verdicts_reused_from"] = raw["reused_from"]
        state["flip_tallies"] = dict(sorted(collections.Counter(
            v.get("verdict") for v in records).items()))
        self._save(state)
        self._check_predictions_adjudicate(self._state())
        state = self._state()
        return True, ("ADJUDICATE complete: flip_verdicts.json bound to the "
                      "dossier set and validated clean (tallies: "
                      f"{state['flip_tallies']}).")

    # ------------------------------------ phase 6: CENSUS (checkpoint only)

    def _census(self, state) -> tuple[bool, str]:
        m = self._manifest()
        cfg = m["config"]
        import audit_disagreements
        tag = audit_disagreements.config_tag(cfg["annotations"],
                                             cfg["atoms"])
        baseline_path = self._baseline_census_path()
        if not baseline_path or not os.path.exists(baseline_path):
            return False, (
                f"HALT (CENSUS): the NAMED baseline census artifact "
                f"({m.get('baseline_census')!r}, resolved to "
                f"{baseline_path}) does not exist — the census-to-census "
                f"diff and the frozen census-class check need it. Generate "
                f"it rather than skipping:\n"
                f"  1. {PYTHON} audit_disagreements.py dossiers "
                f"--annotations {cfg['annotations']} --atoms {cfg['atoms']}"
                f"\n  2. adjudicate every dossier per "
                f"briefs/disagreement_autopsy.md\n"
                f"  3. validate, then save the merged verdict list as "
                f"verdicts_merged.json at the path the manifest names.")
        # cycle-scoped census output (F2): never a baseline's directory
        census_root = self._p("census", "audit_dossiers")
        dossier_dir = os.path.join(census_root, tag)
        if not os.path.exists(os.path.join(dossier_dir, "index.jsonl")):
            census_cmd = [PYTHON, os.path.join(REPO,
                                               "audit_disagreements.py"),
                          "dossiers",
                          "--annotations",
                          os.path.join(REPO, cfg["annotations"]),
                          "--atoms", os.path.join(REPO, cfg["atoms"]),
                          "--out-root", census_root]
            # overlay/thresholds thread to the census EXACTLY as they
            # thread to the snapshot build (item 0c): the census must audit
            # the shipped configuration, not a plain-index rebuild of it.
            if cfg.get("overlay"):
                census_cmd += ["--overlay",
                               os.path.join(REPO, cfg["overlay"])]
            if cfg.get("thresholds"):
                census_cmd += ["--thresholds",
                               os.path.join(REPO, cfg["thresholds"])]
            _run(census_cmd)
            # F2: full config identity alongside the dossier set
            ident = {"annotations": {"path": cfg["annotations"],
                                     "sha256": sha256_file(os.path.join(
                                         REPO, cfg["annotations"]))},
                     "atoms": {"path": cfg["atoms"],
                               "sha256": sha256_file(os.path.join(
                                   REPO, cfg["atoms"]))},
                     "overlay": ({"path": cfg["overlay"],
                                  "sha256": sha256_file(os.path.join(
                                      REPO, cfg["overlay"]))}
                                 if cfg.get("overlay") else None),
                     "config_tag": tag}
            _write_json(os.path.join(dossier_dir, "config_identity.json"),
                        ident)
        index_records = [json.loads(line)
                         for line in open(os.path.join(
                             dossier_dir, "index.jsonl"))
                         if line.strip()]
        # item 0c: the FIRST record must be the config-identity header —
        # an unidentified census cannot prove which configuration it
        # audited (amendment F2). Refuse a headerless index outright.
        if not (index_records
                and index_records[0].get("record") == "config_identity"):
            raise CycleError(
                f"census index at {dossier_dir} has no config-identity "
                f"header record (first index.jsonl line must carry the "
                f"input shas — amendment F2, TOOLING item 1). Delete the "
                f"directory and regenerate with the current "
                f"audit_disagreements.py.")
        behaviours = sorted({r["behaviour"] for r in index_records[1:]})
        # THE SCOPE PIN (amendment F7): non-overridable held-out refusal
        held_out = [b for b in behaviours if b not in DEV_CENSUS_CELLS]
        if held_out:
            raise CycleError(
                "CENSUS touched HELD-OUT cells: " + ", ".join(held_out)
                + f". census_scope is pinned to the DEV cells "
                f"{DEV_CENSUS_CELLS} (policy §5, amendment F7); the "
                f"held-out cells are evaluated only at pre-registered "
                f"checkpoints, never during iteration. This refusal is "
                f"non-overridable.")
        set_sha = _dir_set_sha(dossier_dir)
        if state.get("census_set_sha") != set_sha:
            state["census_set_sha"] = set_sha
            self._save(state)
        missing = []
        for slug in behaviours:
            apath = self._p("assignments", f"census_{slug}.md")
            if not os.path.exists(apath):
                _write_text(apath, CENSUS_ASSIGNMENT.format(
                    name=self.name, slug=slug, tag=tag, set_sha=set_sha))
            if not os.path.exists(self._p("census",
                                          f"verdicts_{slug}.json")):
                missing.append(f"census/verdicts_{slug}.json")
        if missing:
            return False, (
                "HALT (CENSUS): judgment required — the autopsy seat must "
                "produce per-behaviour verdict files (assignments under "
                "assignments/census_<behaviour>.md, echoing the dossier "
                "set sha): missing " + ", ".join(missing))
        merged = []
        for slug in behaviours:
            raw = _read_json(self._p("census", f"verdicts_{slug}.json"))
            if not isinstance(raw, dict) \
                    or raw.get("dossier_set_sha") != set_sha:
                raise CycleError(
                    f"census/verdicts_{slug}.json must echo dossier_set_sha "
                    f"{set_sha} (got "
                    f"{raw.get('dossier_set_sha') if isinstance(raw, dict) else type(raw).__name__!r})"
                    f" — unbound census verdicts cannot prove which "
                    f"dossier set they judged (amendment F3).")
            merged.extend(raw.get("records") or [])
        merged.sort(key=lambda v: v.get("dossier_id") or "")
        mpath = self._p("census", "verdicts_merged.json")
        _write_json(mpath, merged)
        # audit_disagreements' flag IS --verdicts (F9: never harmonize)
        _run([PYTHON, os.path.join(REPO, "audit_disagreements.py"),
              "validate", "--verdicts", mpath, "--dossier-dir", dossier_dir])
        baseline = _cause_counts(_read_json(baseline_path))
        new = _cause_counts(merged)
        delta = {cause: {"baseline": baseline.get(cause, 0),
                         "new": new.get(cause, 0),
                         "delta": new.get(cause, 0) - baseline.get(cause, 0)}
                 for cause in sorted(set(baseline) | set(new))}
        _write_json(self._p("census_delta.json"), {
            "baseline_census": os.path.relpath(baseline_path, REPO),
            "by_cause": delta,
            "stamp": "DEV",   # every census-derived number is a dev number
        })
        pred = self._prediction() or {}
        cc = pred.get("census_classes") or {}
        checks = []
        for cause in cc.get("expected_shrink") or []:
            b, n = baseline.get(cause, 0), new.get(cause, 0)
            checks.append({"kind": "census_shrink", "class": cause,
                           "baseline": b, "new": n,
                           "result": "PASS" if n < b else "FAIL"})
        for cause in cc.get("must_not_grow") or []:
            b, n = baseline.get(cause, 0), new.get(cause, 0)
            checks.append({"kind": "census_must_not_grow", "class": cause,
                           "baseline": b, "new": n,
                           "result": "PASS" if n <= b else "FAIL"})
        state = self._state()
        state["census_consulted"] = True
        if checks:
            state.setdefault("prediction_checks", {})["census"] = checks
        self._save(state)
        self._write_prediction_check(state)
        failed = [c["class"] for c in checks if c["result"] == "FAIL"]
        return True, (
            "CENSUS complete (CHECKPOINT — all numbers DEV-stamped): "
            "merged verdicts validated clean; census_delta.json written"
            + (f"; census-class check FAILED: {', '.join(failed)}"
               if failed else
               ("; census-class predictions all PASS" if checks else ""))
            + ".")

    # -------------------------------------------------- phase 7: DECIDE

    def _write_draft(self, state) -> None:
        m = self._manifest()

        def maybe(rel):
            p = self._p(rel)
            return _read_json(p) if os.path.exists(p) else None

        delta = maybe("census_delta.json")
        draft = {
            "cycle": self.name,
            "date": m["date"],
            "shape": self._shape(),
            "fix_description": m["fix_description"],
            "noop": bool(state.get("noop")),
            "exploratory": bool(state.get("exploratory")),
            "census": state.get("census",
                                "consulted" if state.get("census_consulted")
                                else "deferred_to_checkpoint"),
            "gate": state.get("gate"),
            "flip_tallies": state.get("flip_tallies") or {},
            "flip_verdicts_reused_from":
                state.get("flip_verdicts_reused_from"),
            "census_delta": (delta or {}).get("by_cause"),
            "prediction_check": maybe("prediction_check.json"),
            "overrides": state["overrides"],
            "decision": "",
            "signed_by": "",
            "justification": "",
        }
        _write_json(self._p("decision.draft.json"), draft)

    def _decide(self, state) -> tuple[bool, str]:
        self._write_draft(state)
        dpath = self._p("decision.json")
        if not os.path.exists(dpath):
            return False, (
                "HALT (DECIDE): judgment required — sign decision.json.\n"
                "Draft with all computed fields written: "
                "decision.draft.json. Copy it to decision.json and fill "
                "decision (keep|revert), signed_by, and justification "
                "(REQUIRED if any prediction FAILed or any gate was "
                "overridden). The decision cites the DOCUMENT-SIDE "
                "adjudications; census numbers inform, never decide.")
        d = _read_json(dpath)
        if d.get("decision") not in DECISION_VALUES:
            raise CycleError(f"decision.json: decision must be one of "
                             f"{DECISION_VALUES}, got {d.get('decision')!r}")
        if state.get("exploratory") and d["decision"] == "keep":
            raise CycleError(
                "decision.json: this cycle is EXPLORATORY (PREDICT was "
                "overridden) and cannot record keep — a change kept without "
                "a frozen prediction is unfalsifiable. Re-run it as a "
                "proper cycle to keep it.")
        if not str(d.get("signed_by", "")).strip():
            raise CycleError("decision.json: signed_by is empty — an "
                             "unsigned decision is not a decision")
        check = None
        if os.path.exists(self._p("prediction_check.json")):
            check = _read_json(self._p("prediction_check.json"))
        any_fail = bool(check and any(c["result"] == "FAIL"
                                      for c in check["checks"]))
        if (any_fail or state["overrides"]) \
                and not str(d.get("justification", "")).strip():
            raise CycleError(
                "decision.json: a non-empty justification is required — "
                + ("a prediction FAILed" if any_fail else "")
                + (" and " if any_fail and state["overrides"] else "")
                + ("a gate was overridden" if state["overrides"] else "")
                + ".")
        state["decision"] = {"decision": d["decision"],
                             "signed_by": d["signed_by"]}
        self._save(state)
        return True, (f"DECIDE complete: {d['decision']} signed by "
                      f"{d['signed_by']}.")

    # --------------------------------------------------- phase 8: CLOSE

    def _close(self, state) -> tuple[bool, str]:
        if state.get("closed"):
            return True, "cycle already closed."
        m = self._manifest()
        d = _read_json(self._p("decision.json"))
        check = None
        if os.path.exists(self._p("prediction_check.json")):
            check = _read_json(self._p("prediction_check.json"))
        deltas = None
        if os.path.exists(self._p("census_delta.json")):
            by = _read_json(self._p("census_delta.json"))["by_cause"]
            deltas = {cause: rec["delta"]
                      for cause, rec in sorted(by.items()) if rec["delta"]}
        rec = {
            "cycle": self.name,
            "date": m["date"],
            "shape": self._shape(),
            "decision": d["decision"],
            "prediction_pass_rate": check["pass_rate"] if check else None,
            "census_consulted": bool(state.get("census_consulted")),
            "census_deltas": deltas,
            "overrides": [ov["phase"] for ov in state["overrides"]],
            "exploratory": bool(state.get("exploratory")),
            "noop": bool(state.get("noop")),
        }
        log = os.path.join(os.path.dirname(self.dir), "CYCLE_LOG.jsonl")
        with open(log, "a") as f:
            f.write(json.dumps(rec, sort_keys=True) + "\n")
        # COMMIT-AT-CLOSE (TOOLING item 6): draft the commit so a closed
        # cycle never sits uncommitted for lack of a ready message — but the
        # DRIVER NEVER RUNS GIT. The coordinator confirms and executes
        # (committing each unit once its review resolves); the draft removes
        # the friction, the human keeps the authority.
        if check:
            passed = sum(1 for c in check["checks"]
                         if c["result"] in ("PASS", "PASS_VACUOUS"))
            pred_note = f"predictions {passed}/{len(check['checks'])}"
        else:
            pred_note = "no predictions"
        lines = [f"{self.name}: {d['decision']} ({self._shape()}, "
                 f"{pred_note})", ""]
        if str(m.get("fix_description", "")).strip():
            lines += [str(m["fix_description"]).strip(), ""]
        if str(d.get("justification", "")).strip():
            lines += [str(d["justification"]).strip(), ""]
        lines += ["Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>",
                  ""]
        _write_text(self._p("commit_message.txt"), "\n".join(lines))
        staging = sorted(m["files_to_change"]) \
            + [os.path.relpath(self.dir, REPO)]
        _write_text(self._p("staging_list.txt"), "\n".join(staging) + "\n")
        state["closed"] = True
        self._save(state)
        return True, (
            f"CLOSE complete: one line appended to CYCLE_LOG.jsonl "
            f"({d['decision']}). Cycle closed.\n"
            f"Commit draft ready (the driver never runs git — the "
            f"coordinator commits):\n"
            f"  message: {self._p('commit_message.txt')}\n"
            f"  staging set: {', '.join(staging)}")


# --------------------------------------------------------------------- CLI

def _default_cycle() -> str:
    """The single open (non-closed) cycle, when --cycle is omitted."""
    if not os.path.isdir(CYCLES_ROOT):
        raise CycleError("no cycles/ directory yet — pass --cycle NAME to "
                         "open the first cycle.")
    open_cycles = []
    for name in sorted(os.listdir(CYCLES_ROOT)):
        cdir = os.path.join(CYCLES_ROOT, name)
        if not os.path.isdir(cdir):
            continue
        spath = os.path.join(cdir, "state.json")
        closed = os.path.exists(spath) and _read_json(spath).get("closed")
        if not closed:
            open_cycles.append(name)
    if len(open_cycles) == 1:
        return open_cycles[0]
    raise CycleError(
        f"{len(open_cycles)} open cycles ({', '.join(open_cycles) or 'none'})"
        " — pass --cycle NAME.")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="cycle.py",
        description="drive one fix cycle of the iteration loop: mechanical "
                    "phases run, judgment phases halt with a template")
    sub = parser.add_subparsers(dest="cmd", required=True)
    for name in ("status", "next"):
        p = sub.add_parser(name)
        p.add_argument("--cycle", default=None)
        if name == "next":
            p.add_argument("--override", default=None, metavar="PHASE",
                           help="skip this gate LOUDLY (recorded in "
                                "state.json, echoed by every later status; "
                                "PREDICT demotes the cycle to exploratory)")
            p.add_argument("--reason", default=None,
                           help="required with --override")
    args = parser.parse_args(argv)

    try:
        name = args.cycle or _default_cycle()
        c = Cycle(name)
        if args.cmd == "status":
            sys.stdout.write(c.status())
            return 0
        msg = c.next(override=getattr(args, "override", None),
                     reason=getattr(args, "reason", None))
        print(msg)
        return 0
    except (PredictionTampered, ManifestTampered) as e:
        print(f"FREEZE VIOLATION: {e}", file=sys.stderr)
        return 2
    except ToolFailed as e:
        print(f"TOOL FAILED: {e}", file=sys.stderr)
        return e.code
    except CycleError as e:
        print(f"REFUSED: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
