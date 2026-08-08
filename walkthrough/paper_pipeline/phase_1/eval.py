#!/usr/bin/env python3
"""phase_1/eval.py — did that prompt change help, or is that noise?

    THE ONE QUESTION THIS ANSWERS:  a prompt was edited. Is the difference in
    the output larger than the difference the SAME prompt produces run twice?

Prompt changes in this directory have so far been accepted or rejected by
reading. This is step 4 of `PROPOSAL_graveyard.md` — the held-out harness that
makes a prompt change arguable instead of plausible.

⭐ THE FIRST THING IT DOES IS MEASURE ITS OWN NOISE.  Temperature is 0.2, so the
same prompt over the same clauses gives different answers each time. Nobody has
ever measured how different. Until that number exists a single before/after is
uninterpretable, so `--repeats N` over ONE arm is the default mode and the
spread is printed before anything else.

⭐ IT SCORES THE FIRST ATTEMPT ONLY.  `translate.py` runs a repair loop; 7 of 8
clauses in the last live run needed it. A good repair loop launders a bad
prompt, so the report card is what the prompt produces BEFORE anyone tells it
anything: exactly one model call per clause per repeat, and `--live` will refuse
to make a second.

⚠️ CAUSES ARE CLUSTERED BY NORMALISED MESSAGE, NEVER BY `check_id`.  Every
schema failure carries `check_id == "schema-breach"` (`checks.SCHEMA_CHECK_ID`
says so and says why), so a report keyed on the id has one bucket holding every
distinct defect. See `normalise_message` for what is erased and why each erasure
is needed.

⚠️ THE EVAL SET IS AN ARGUMENT AND ITS RECORDING IS MANDATORY.  A prompt change
validated on the clauses that motivated it is fitting, and this project has a
standing ruling against a search scored by its own measurement. `eval.py`
invents no clause list: it takes one and writes it into the report, so a later
reader can check the eval set was not the diagnosis set.

⛔ TWO ARMS THAT ARE THE SAME PROMPT IS AN ERROR.  A harness that reports "no
significant difference" because it never varied anything is worse than no
harness. `assert_arms_differ` compares the assembled system block and every user
block, not the config filename, and a match exits 2.

    python3 eval.py --clauses m0091,m0217 --repeats 3          # DRY RUN
    python3 eval.py --clause-file heldout.txt --repeats 3 --live
    python3 eval.py --clause-file heldout.txt --repeats 3 \
                    --compare config_b.json --metric licences --live

Exit codes:  0 clean · 1 an arm produced nothing usable · 2 usage/config error
"""

import argparse
import dataclasses
import json
import os
import re
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import checks                                                   # noqa: E402
import translate as T                                           # noqa: E402

DEFAULT_CONFIG = os.path.join(HERE, "config.json")


class EvalError(RuntimeError):
    """Every failure here is a refusal to proceed, never a warning."""


class IdenticalArmsError(EvalError):
    """Two arms that would send the same bytes. Reported as an ERROR."""


# ==========================================================================
# 1.  Clustering — the report's whole value is that causes are RANKED
# ==========================================================================

#: What a placeholder looks like. Deliberately not a word: a cluster key is
#: read by a human and the eye needs to see where the variation was.
PLACEHOLDER = "‹›"

#: ⚠️ EACH OF THESE IS HERE BECAUSE A REAL MESSAGE NEEDS IT.
#:
#:  _BACKTICK  link.py quotes predicate names — `restricted/1` — so one cause
#:             across twelve clauses is twelve messages.
#:  _SQ / _DQ  ⭐ THE ONE THAT IS EASY TO MISS. schema.py's guards interpolate
#:             with `{term!r}`, which is SINGLE QUOTES, not backticks. The
#:             rule-in-a-term-slot breach — the shared cause
#:             `PROPOSAL_graveyard.md` found by hand across two clauses — is
#:             quoted that way. Normalising backticks alone leaves it
#:             fragmented one cluster per clause, i.e. invisible in a rank.
#:  _PATH      `clingo-error` embeds the temp .lp path stage 2 rendered to,
#:             and that directory is new on every run. Without this, every
#:             clingo failure ever recorded is its own cluster. Two segments
#:             minimum, so a predicate signature (`restricted/1`) is not eaten.
#:  _NUM       "read_back has 0 `%` slot(s) but 1 slot entr(ies)" — the counts
#:             differ per module and the cause does not. Also kills the
#:             `:39:1-75:` line/column spans clingo appends.
_BACKTICK = re.compile(r"`[^`]*`")
_SQ = re.compile(r"'[^']*'")
_DQ = re.compile(r'"[^"]*"')
_PATH = re.compile(r"(?:/[\w.\-+@]+){2,}")
_NUM = re.compile(r"\d+")
_WS = re.compile(r"\s+")


def normalise_message(msg):
    """A finding message -> the CAUSE it is an instance of.

    Order matters: quoted spans are collapsed before paths and numbers, so a
    quoted path is erased once rather than twice into a different shape.
    """
    s = _BACKTICK.sub(PLACEHOLDER, msg or "")
    s = _DQ.sub(PLACEHOLDER, s)
    s = _SQ.sub(PLACEHOLDER, s)
    s = _PATH.sub(PLACEHOLDER, s)
    s = _NUM.sub("#", s)
    return _WS.sub(" ", s).strip()


@dataclasses.dataclass
class Cluster:
    """One cause, and everything that lets a reader act on it."""

    key: str                 #: the normalised message
    count: int               #: how many findings landed here
    example: str             #: one VERBATIM message — a rank with no example
                             #: is unactionable
    severity: str            #: "error" if any member is an error, else "note"
    check_ids: tuple = ()
    wheres: tuple = ()
    clause_ids: tuple = ()   #: which clauses produced it, when known

    def as_dict(self):
        return dataclasses.asdict(self)


def cluster_findings(findings, clause_ids=None):
    """Findings -> clusters, ranked by count then key.

    `clause_ids` is an optional parallel sequence naming the clause each
    finding came from; a cause that fires on one clause and a cause that fires
    on twelve are different claims about the prompt.
    """
    findings = list(findings)
    ids = list(clause_ids or [None] * len(findings))
    if len(ids) != len(findings):
        raise EvalError("clause_ids must be parallel to findings")
    buckets = {}
    for f, cid in zip(findings, ids):
        b = buckets.setdefault(normalise_message(f.message), {
            "count": 0, "example": f.message, "severities": set(),
            "check_ids": set(), "wheres": set(), "clause_ids": set()})
        b["count"] += 1
        b["severities"].add(f.severity)
        b["check_ids"].add(f.check_id)
        b["wheres"].add(f.where)
        if cid is not None:
            b["clause_ids"].add(cid)
    out = [Cluster(key=k, count=b["count"], example=b["example"],
                   severity="error" if "error" in b["severities"] else "note",
                   check_ids=tuple(sorted(b["check_ids"])),
                   wheres=tuple(sorted(b["wheres"])),
                   clause_ids=tuple(sorted(b["clause_ids"])))
           for k, b in buckets.items()]
    out.sort(key=lambda c: (-c.count, c.key))
    return out


# ==========================================================================
# 2.  An arm — one prompt, assembled, with the exact bytes it would send
# ==========================================================================

class _Args:
    """`translate`'s CLI namespace, as a plain object. One selection: clause
    ids, because the eval set is always given explicitly."""

    section = kinds = limit = provider = model = max_tokens = None
    live = False
    show_prompt = 0

    def __init__(self, clause=None):
        self.clause = list(clause) if clause else None


@dataclasses.dataclass
class Job:
    row: dict
    user: str

    @property
    def clause_id(self):
        return self.row.get("id")


@dataclasses.dataclass
class Arm:
    name: str
    config_path: str
    cfg: dict
    system: str
    system_sha: str
    inputs_sha: str
    jobs: list
    corpus_ids: set
    prov: object

    @property
    def clause_ids(self):
        return [j.clause_id for j in self.jobs]

    @property
    def user_shas(self):
        return {j.clause_id: T.sha16(j.user) for j in self.jobs}


def load_arm(name, config_path, clause_ids):
    """Assemble everything one arm would send. Nothing is sent.

    ⚠️ EVERY PATH-RESOLVING CALL HAPPENS HERE, IN ORDER, BEFORE THE NEXT ARM
    IS LOADED. `translate.rel()` resolves against a module-global `_BASE` that
    `load_config` is the only writer of, so loading arm B's config and then
    fingerprinting arm A would hash arm A's config against arm B's prompt
    files — and the two arms would look different for a reason that is a bug in
    this function.
    """
    if not clause_ids:
        raise EvalError(
            "an arm needs a clause list. eval.py does not invent one: a prompt "
            "change validated on the clauses that motivated it is fitting, and "
            "the eval set has to be given and recorded so that is checkable")
    cfg = T.load_config(config_path)
    rows = T.load_corpus(cfg)
    idk = cfg["corpus"]["id_key"]
    args = _Args(clause=list(clause_ids))
    picked = T.select(rows, cfg, args)
    system = T.build_system(cfg)
    T.validate_format_forcing(cfg)
    jobs = [Job(row=r, user=T.build_user(r, rows, cfg)[0]) for r in picked]
    return Arm(name=name, config_path=os.path.abspath(config_path), cfg=cfg,
               system=system, system_sha=T.sha16(system),
               inputs_sha=T.inputs_fingerprint(cfg), jobs=jobs,
               corpus_ids={r[idk] for r in rows},
               prov=T.resolve_provider(cfg, args))


def assert_arms_differ(a, b):
    """⛔ Two arms that would send the same bytes is an ERROR, not a null result.

    ⚠️ COMPARED ON THE ASSEMBLED PROMPT, NOT ON THE CONFIG. Two configs can
    differ in the cost ceiling, the output directory or a comment and produce a
    byte-identical system block — an A/B over those two is a measurement of
    noise being reported as a measurement of a change. And two different
    filenames holding the same content is the same trap with less warning.
    """
    if (a.system_sha, a.user_shas) != (b.system_sha, b.user_shas):
        return
    same_cfg = a.inputs_sha == b.inputs_sha
    raise IdenticalArmsError(
        f"arms {a.name!r} and {b.name!r} are the IDENTICAL prompt: same system "
        f"block (sha {a.system_sha}) and the same user block for every clause"
        + ("." if same_cfg else
           " — the configs differ, but not in anything that reaches the model.")
        + " Any delta measured here is run-to-run noise. Reporting it as 'no "
          "significant difference' would be a null result that never had "
          "anything to be null about, so this refuses instead. Run one arm "
          "with --repeats to measure the noise on purpose.")


# ==========================================================================
# 3.  Metrics — a registry, because each change names its own
# ==========================================================================

#: name -> `fn(outcomes, arm) -> {scalar_name: float}`. Every scalar returned
#: is spread across repeats automatically, so a new metric is one function and
#: one decorator — never a change to the reporting.
METRICS = {}


def metric(name):
    def deco(fn):
        METRICS[name] = fn
        return fn
    return deco


def load_metrics(names):
    """The metric list for a run. `findings` is ALWAYS included.

    A per-change metric answers "did the thing I edited move?"; the findings
    report answers "and did anything else break while it did?". A change is not
    arguable without both.
    """
    out = ["findings"]
    for n in (names or []):
        if n not in METRICS:
            raise EvalError(
                f"no metric named {n!r}. Known: {', '.join(sorted(METRICS))}. "
                f"Adding one is a function and an @metric(...) line in eval.py")
        if n not in out:
            out.append(n)
    return out


@metric("findings")
def findings_metric(outcomes, arm):
    """The default report card. ⭐ First-attempt, and clean means NO ERROR.

    `requires-unprovided` is a NOTE and fires on every correct single-clause
    module this pipeline emits (`checks.py`, the severity ruling). A clean rate
    that counted notes would read 0% on a perfect run — so notes are counted in
    `findings_per_clause`, are visible in the cluster rank, and do not fail a
    clause.
    """
    n = len(outcomes) or 1
    return {
        "first_attempt_clean_rate":
            sum(1 for o in outcomes if not o.errors) / n,
        "findings_per_clause": sum(len(o.findings) for o in outcomes) / n,
        "error_findings_per_clause": sum(len(o.errors) for o in outcomes) / n,
        "abstention_rate":
            sum(1 for o in outcomes if o.outcome == "abstained") / n,
        "unbuildable_rate": sum(1 for o in outcomes if o.module is None) / n,
    }


@metric("glosses")
def gloss_metric(outcomes, arm):
    """⭐ The metric for bad worked example #6 — "imports a name without its content".

    A concept whose gloss merely restates its own predicate name carries no
    content: `terrorism_act` -> "an act of terrorism" makes the whole category
    one opaque symbol standing for whatever the reader already believed. It
    reads correctly in every explanation, which is why nothing catches it.

    ⛔ THIS IS A PROXY AND IS NOT A PASS/FAIL CHECK. `system_message` -> "C is
    a system message" scores as empty here and is CORRECT, because the document
    treats it as primitive. That is precisely why the ruling in
    `DECISION_bad_worked_examples.md` refused to make this a stage-2 check. It
    is usable as a RATE across arms -- the primitives are the same in both, so
    a difference between arms is about the change -- and unusable as a verdict
    on any single concept.

    `gloss_concepts_scored` is part of the metric for the reason
    `licence_modules_scored` is: a module that fails the schema carries no
    concepts, every rate below reads 0.0000, and "nothing measured" would be
    indistinguishable from "no empty glosses".
    """
    STOP = {"a", "an", "the", "is", "of", "that", "to", "in", "for", "and",
            "or", "by", "it", "with", "has", "as", "are", "this", "be", "been",
            "its", "which", "was", "any", "all"}
    empty = total = 0
    for o in outcomes:
        mod = getattr(o, "module", None)
        for c in (getattr(mod, "concepts", None) or []):
            name = getattr(c, "name", "") or ""
            gloss = getattr(c, "gloss", "") or ""
            if not name or not gloss:
                continue
            total += 1
            extra = (set(re.findall(r"[a-z]+", gloss.lower()))
                     - set(re.findall(r"[a-z]+", name.lower()))
                     - STOP - set("abcdefghijklmnopqrstuvwxyz"))
            empty += not extra
    n = len(outcomes) or 1
    return {
        "gloss_concepts_scored": total / n,
        "empty_gloss_rate": (empty / total) if total else 0.0,
        "empty_glosses_per_clause": empty / n,
    }


@metric("licences")
def licence_metric(outcomes, arm):
    """⭐ The metric for a change to the LICENCE rule in `prompt/00_task.md`.

    That file says the rule "is **not** 'only write what the text says'".
    Deleting the sentence should not move the pass rate at all — its claim is
    about licences, and a pass rate would report the change as a no-op. What it
    should move is how often the model marks a fact as an inference (`assumed`)
    or as outside knowledge (`world`) rather than claiming the text says it.

    ⚠️ A FALLING non-textual rate is not automatically good. The rule exists to
    make an unstated fact VISIBLE, not to ban one; a model that stops writing
    `assumed` and starts writing `textual` with a manufactured citation has got
    worse while this number improved. That is what `unresolved_citation_rate`
    is beside it for — read them together or read neither.

    Counted over every licensed item the module carries: concepts, ontology
    facts, assertions, superiority statements and definitions.

    ⛔ `licence_modules_scored` IS PART OF THE METRIC, NOT DECORATION. A module
    that fails the schema does not construct, so it carries no licensed items
    and this metric sees nothing of it. Every rate below then reads `0.0000` —
    which is indistinguishable from "the model wrote no assumed facts" and is
    actually "there was nothing to look at". Found by replaying two real runs:
    all three first attempts were unbuildable and the whole licence block read
    zero. Read the rates only alongside the count.
    """
    total = assumed = world = textual = unresolved = scored = 0
    for o in outcomes:
        mod = o.module
        if mod is None:
            continue
        scored += 1
        for item in (*mod.concepts, *mod.ontology, *mod.asserts,
                     *mod.beats, *mod.defines):
            total += 1
            if item.licence == "assumed":
                assumed += 1
            elif item.licence == "world":
                world += 1
            else:
                textual += 1
                if (item.cites or "") not in arm.corpus_ids:
                    unresolved += 1
    return {
        #: ⭐ FIRST, so it is read first. See the docstring.
        "licence_modules_scored": float(scored),
        "assumed_fact_rate": assumed / total if total else 0.0,
        "world_fact_rate": world / total if total else 0.0,
        "non_textual_fact_rate": (assumed + world) / total if total else 0.0,
        "unresolved_citation_rate": unresolved / textual if textual else 0.0,
        "licensed_items_per_clause": total / (len(outcomes) or 1),
    }


# ==========================================================================
# 4.  Running an arm — ONE call per clause per repeat
# ==========================================================================

@dataclasses.dataclass
class ClauseOutcome:
    clause_id: str
    outcome: str                 #: translated | abstained | invalid | error
    module: object
    findings: list
    attempt: int = 1             #: ⭐ always 1. See the module docstring.
    raw: str = ""

    @property
    def errors(self):
        return [f for f in self.findings if f.severity == "error"]

    def as_dict(self):
        return {"clause_id": self.clause_id, "outcome": self.outcome,
                "attempt": self.attempt, "n_findings": len(self.findings),
                "n_errors": len(self.errors),
                "findings": [f"[{f.check_id}] {f.where}: {f.message}"
                             for f in self.findings]}


@dataclasses.dataclass
class RepeatResult:
    index: int
    clauses: list
    metrics: dict


@dataclasses.dataclass
class ArmResult:
    arm: Arm
    repeats: list
    #: The client the arm ran through, so the run can say what it spent.
    #: `spend.py` cannot see this provider — see `spend_invisibility_warning`.
    client: object = None

    @property
    def name(self):
        return self.arm.name

    @property
    def spread(self):
        """⭐ THE NUMBER EVERYTHING ELSE IS READ AGAINST.

        One repeat has no spread, and `sd` is then `None` rather than `0.0`.
        Zero would say "this prompt is deterministic", which at temperature 0.2
        is false, and would make a single before/after read as noise-free — the
        exact claim this harness exists to refuse.
        """
        keys, out = [], {}
        for r in self.repeats:
            for k in r.metrics:
                if k not in keys:
                    keys.append(k)
        for k in keys:
            vals = [r.metrics[k] for r in self.repeats if k in r.metrics]
            out[k] = {"n": len(vals),
                      "mean": statistics.fmean(vals) if vals else None,
                      "sd": statistics.stdev(vals) if len(vals) > 1 else None,
                      "min": min(vals) if vals else None,
                      "max": max(vals) if vals else None,
                      "values": list(vals)}
        return out

    @property
    def all_findings(self):
        return [(o.clause_id, f) for r in self.repeats
                for o in r.clauses for f in o.findings]

    def clusters(self):
        pairs = self.all_findings
        return cluster_findings([f for _, f in pairs], [c for c, _ in pairs])


def _as_object(raw):
    """Wire text -> a dict, tolerating a fence. Anything else is a finding.

    ⛔ NOT `translate.parse_module`: that validates too, and raises. Here the
    schema breaches must come back through `checks.run_checks` as a COMPLETE
    finding list — one breach per paid call is what stage 2 exists to avoid,
    and it is also what would make the cause rank wrong.
    """
    text = (raw or "").strip()
    if text.startswith("```"):
        hit = T._FENCE.search(text)                            # noqa: SLF001
        if hit:
            text = hit.group(1).strip()
    return json.loads(text)


def persist_raw(root, arm_name, repeat_index, outcomes):
    """Every paid call's response text, on disk, before anything interprets it.

    ⛔ THE FAILURE THIS EXISTS FOR. The first live eval made 36 paid calls and
    kept nothing but finding strings. The raw text was captured in memory and
    dropped, so the obvious follow-up question — what did the model actually
    write? — could only be answered by paying again. `translate.py` has always
    treated this as non-negotiable: the raw responses of a run that cost money
    are the one thing that cannot be regenerated.

    Arm and repeat are separate directories because both arms translate the
    same clause ids, and the whole point of the run is that they differ.
    """
    out = os.path.join(root, str(arm_name), f"r{int(repeat_index)}")
    os.makedirs(out, exist_ok=True)
    for o in outcomes:
        # ⚠️ A failed call writes an explicit marker, never an empty file: an
        # empty file cannot be told apart from a call that was never made, and
        # that is this project's signature failure in file form.
        text = getattr(o, "raw", "") or (
            f"<no response — the call did not return text. outcome="
            f"{getattr(o, 'outcome', '?')}>")
        with open(os.path.join(out, f"{o.clause_id}.raw.txt"), "w",
                  encoding="utf-8") as fh:
            fh.write(text)
    return out


def run_arm(arm, repeats=3, metrics=None, client_factory=None, raw_root=None):
    """`repeats` passes over the clause set with ONE prompt. Nothing repairs.

    ⭐ Exactly one `client.complete` per clause per repeat. The stub in
    `test_eval.py` raises from `complete_messages`, so a repair turn added here
    later turns the suite red rather than quietly improving every number.

    One client for the whole arm, not one per repeat: a real `Client` resolves
    a key and carries the spend total, and a per-repeat client would report the
    arm's cost as the last repeat's.
    """
    names = load_metrics(metrics)
    client = (client_factory or T.make_client)(arm.prov, arm.cfg)
    results = []
    for i in range(1, int(repeats) + 1):
        outcomes = []
        for job in arm.jobs:
            outcomes.append(_one_clause(arm, job, client))
        if raw_root:                      # written per repeat, not at the end,
            persist_raw(raw_root, arm.name, i, outcomes)   # so a crash keeps
        results.append(RepeatResult(                       # what was paid for

            index=i, clauses=outcomes,
            metrics={k: v for n in names
                     for k, v in METRICS[n](outcomes, arm).items()}))
    return ArmResult(arm=arm, repeats=results, client=client)


def _one_clause(arm, job, client):
    """One paid call, then every deterministic check stage 2 has, on ATTEMPT 1."""
    cid = job.clause_id
    try:
        env = client.complete(arm.system, job.user)
    except T.Phase1Error as exc:
        # ⚠️ A provider error is NOT a clean clause. It is recorded as an error
        # finding of its own so it cannot silently raise the clean rate.
        return ClauseOutcome(cid, "error", None, [checks.Finding(
            "provider-error", "error", "<response>",
            f"{type(exc).__name__}: {exc}", "schema")])
    raw = env["text"]
    try:
        obj = _as_object(raw)
    except json.JSONDecodeError as exc:
        return ClauseOutcome(cid, "invalid", None, [checks.Finding(
            "not-json", "error", "<response>", str(exc), "schema")], raw=raw)
    res = checks.run_checks(obj, job.row, arm.corpus_ids, attempt=1)
    return ClauseOutcome(cid, res.outcome, res.module, list(res.findings),
                         raw=raw)


# ==========================================================================
# 5.  Cost — the estimate is printed before anything is sent
# ==========================================================================

def estimate(arms, repeats):
    """Worst-case dollars for the whole eval. `max_attempts=1`: no repair.

    Scales with arms AND with repeats — `--repeats 3` over two prompt versions
    is six passes over the clause set, and an estimate that priced one pass
    would understate a hard ceiling sixfold.
    """
    total = 0.0
    for a in arms:
        one, _, _ = T.estimate_cost(a.system, [j.user for j in a.jobs],
                                    a.prov, a.cfg, max_attempts=1)
        total += one * int(repeats)
    return total


def gate(est, arm):
    """Over the ceiling, nothing is sent. Reuses the config's own cap."""
    cap = float(arm.cfg["cost"]["max_cost_usd"])
    if est > cap:
        raise EvalError(
            f"estimated ${est:.4f} for this eval exceeds the ceiling ${cap:.2f} "
            f"in {os.path.basename(arm.config_path)}. Nothing sent. Fewer "
            f"repeats, fewer clauses, or raise cost.max_cost_usd deliberately "
            f"— and note the project ledger cap is $8.50 total")
    return est


# ==========================================================================
# 6.  The report
# ==========================================================================

def build_report(results, clause_ids, source, top_clusters=12):
    """The artifact. ⚠️ The eval set is recorded or there is no report."""
    if not clause_ids:
        raise EvalError(
            "refusing to write a report with no clause set. Which clauses an "
            "eval ran on is the only thing that lets a later reader check the "
            "eval set was not the diagnosis set, and a report without it reads "
            "as authoritative while being unfalsifiable")
    if len(results) == 2:
        assert_arms_differ(results[0].arm, results[1].arm)

    rep = {
        "eval_set": {
            "clause_ids": list(clause_ids),
            "n": len(clause_ids),
            "source": source,
            "sha": T.sha16(",".join(clause_ids)),
            "_": "⚠️ Check this against the clauses that MOTIVATED the change. "
                 "A prompt change validated on its own diagnosis set is fitted, "
                 "not measured.",
        },
        "first_attempt_only": True,
        "repair": "disabled — one call per clause per repeat",
        "arms": {},
    }
    for r in results:
        rep["arms"][r.name] = {
            "config": r.arm.config_path,
            "provider": r.arm.prov.name,
            "model": r.arm.prov.model,
            "temperature": r.arm.prov.temperature,
            "system_sha": r.arm.system_sha,
            "inputs_sha": r.arm.inputs_sha,
            "repeats": len(r.repeats),
            "spread": r.spread,
            "per_repeat": [{"index": rr.index, "metrics": rr.metrics,
                            "clauses": [o.as_dict() for o in rr.clauses]}
                           for rr in r.repeats],
            "clusters": [c.as_dict() for c in r.clusters()[:top_clusters]],
        }

    if len(results) == 2:
        a, b = results
        rep["comparison"] = compare(a, b)
        rep["_comparison"] = (
            f"{b.name} minus {a.name}. `within_noise` is |delta| <= the sum of "
            f"the two arms' standard deviations across repeats. It is a "
            f"YARDSTICK, not a significance test: with 3 repeats it is a weak "
            f"one, and a delta inside it is not evidence of no effect.")
    return rep


def compare(a, b):
    """Arm B minus arm A, each delta beside the noise it has to beat."""
    sa, sb = a.spread, b.spread
    out = {}
    for k in sa:
        if k not in sb:
            continue
        delta = sb[k]["mean"] - sa[k]["mean"]
        band = (sa[k]["sd"] or 0.0) + (sb[k]["sd"] or 0.0)
        known = sa[k]["sd"] is not None and sb[k]["sd"] is not None
        out[k] = {
            f"{a.name}_mean": sa[k]["mean"],
            f"{b.name}_mean": sb[k]["mean"],
            "delta": delta,
            "noise_band": band,
            #: None when neither arm has 2+ repeats: the delta is then
            #: unreadable, and False would claim it beat a noise floor nobody
            #: measured.
            "within_noise": (abs(delta) <= band) if known else None,
        }
    return out


def print_report(rep):
    print("\n" + "=" * 72)
    es = rep["eval_set"]
    print(f"EVAL SET ({es['source']}) sha {es['sha']} — {es['n']} clause(s)")
    print("  " + ", ".join(es["clause_ids"]))
    print("  ⚠️ check this is not the set the change was diagnosed on")
    print("=" * 72)

    for name, arm in rep["arms"].items():
        print(f"\n### arm {name}  [{os.path.basename(arm['config'])}]  "
              f"system-sha {arm['system_sha']}  T={arm['temperature']}  "
              f"repeats={arm['repeats']}")
        print(f"\n  ⭐ NOISE — the same prompt, {arm['repeats']} time(s):")
        print(f"     {'metric':<34}{'mean':>9}{'sd':>9}{'min':>9}{'max':>9}")
        for k, s in arm["spread"].items():
            sd = "  n/a" if s["sd"] is None else f"{s['sd']:.4f}"
            print(f"     {k:<34}{s['mean']:>9.4f}{sd:>9}"
                  f"{s['min']:>9.4f}{s['max']:>9.4f}")
        if arm["repeats"] < 2:
            print("     ⚠️ one repeat: the spread is UNMEASURED, not zero. "
                  "A before/after against this is uninterpretable.")
        print("\n  causes, ranked (first attempt, clustered by normalised "
              "message):")
        if not arm["clusters"]:
            print("     (none)")
        for c in arm["clusters"]:
            mark = "⛔" if c["severity"] == "error" else "  "
            print(f"     {mark} {c['count']:>4}×  {c['key'][:96]}")
            print(f"            e.g. {c['example'][:90]}")
            if c["clause_ids"]:
                print(f"            clauses: {', '.join(c['clause_ids'][:8])}")

    if "comparison" in rep:
        names = list(rep["arms"])
        print(f"\n### {names[1]} minus {names[0]}")
        print(f"     {'metric':<34}{'delta':>10}{'noise':>10}   verdict")
        for k, row in rep["comparison"].items():
            v = ("UNKNOWN (need 2+ repeats)" if row["within_noise"] is None
                 else "within noise" if row["within_noise"]
                 else "⭐ LARGER THAN THE NOISE")
            print(f"     {k:<34}{row['delta']:>+10.4f}"
                  f"{row['noise_band']:>10.4f}   {v}")
        print("\n     ⚠️ `within noise` is not 'no effect'. With few repeats "
              "the band is wide and this test is weak.")


# ==========================================================================
# 7.  CLI
# ==========================================================================

def _clause_ids(args):
    """The eval set and where it came from. There is no default."""
    if args.clause_file:
        with open(args.clause_file, encoding="utf-8") as fh:
            ids = [ln.split("#")[0].strip() for ln in fh]
        return [i for i in ids if i], f"--clause-file {args.clause_file}"
    if args.clauses:
        return ([c.strip() for c in args.clauses.split(",") if c.strip()],
                "--clauses")
    return [], None


def build_parser():
    p = argparse.ArgumentParser(
        prog="eval.py", description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--config", default=DEFAULT_CONFIG,
                   help="arm A (the baseline prompt)")
    p.add_argument("--compare", default=None,
                   help="arm B: a second config. Its prompt must differ")
    p.add_argument("--clauses", default=None,
                   help="comma-separated clause ids — the HELD-OUT eval set")
    p.add_argument("--clause-file", default=None,
                   help="one clause id per line; `#` comments allowed")
    p.add_argument("--repeats", type=int, default=3,
                   help="passes per arm. ⭐ 1 leaves the noise unmeasured")
    p.add_argument("--metric", action="append", default=[],
                   help=f"extra reporter(s): {', '.join(sorted(METRICS))}")
    p.add_argument("--out", default=None, help="write the report JSON here")
    p.add_argument("--live", action="store_true",
                   help="actually spend. Without it nothing is sent")
    return p


def main(argv=None, client_factory=None):
    args = build_parser().parse_args(argv)
    clause_ids, source = _clause_ids(args)
    if not clause_ids:
        print("⛔ no clause set. Pass --clauses a,b,c or --clause-file PATH.\n"
              "   eval.py invents no eval set: a prompt change validated on "
              "the clauses that motivated it is fitted, not measured, and the "
              "set has to be recorded for anyone to check which happened.")
        return 2

    try:
        metric_names = load_metrics(args.metric)
        arms = [load_arm("A", args.config, clause_ids)]
        if args.compare:
            arms.append(load_arm("B", args.compare, clause_ids))
            assert_arms_differ(arms[0], arms[1])
    except IdenticalArmsError as exc:
        print(f"⛔ {exc}")
        return 2
    except (EvalError, T.Phase1Error) as exc:
        print(f"⛔ {type(exc).__name__}: {exc}")
        return 2

    est = estimate(arms, args.repeats)
    label = ", ".join(f"{a.name}={os.path.basename(a.config_path)} "
                      f"[sys {a.system_sha}]" for a in arms)
    print(f"arms         : {label}")
    print(f"clauses      : {len(clause_ids)}  "
          f"[{', '.join(clause_ids[:8])}{' …' if len(clause_ids) > 8 else ''}]")
    print(f"repeats      : {args.repeats} per arm  "
          f"({len(arms) * args.repeats * len(clause_ids)} call(s) total, "
          f"one per clause per repeat — NO repair)")
    print(f"metrics      : {', '.join(metric_names)}")
    print(f"cost (worst) : ${est:.4f}   ceiling "
          f"${float(arms[0].cfg['cost']['max_cost_usd']):.2f}")
    if args.repeats < 2:
        print("⚠️ --repeats 1 measures no noise. Any delta you then read is "
              "of unknown size relative to run-to-run variation.")

    if not args.live:
        print("\nDRY RUN — nothing was sent. Add --live to spend.")
        return 0

    try:
        gate(est, arms[0])
        # Raws land beside --out, so a report and the responses behind it are
        # never separated. Without --out there is nowhere non-arbitrary to put
        # them, and the estimate line already told the user what they spent.
        raw_root = (os.path.splitext(args.out)[0] + "_raw") if args.out else None
        results = [run_arm(a, repeats=args.repeats, metrics=args.metric,
                           client_factory=client_factory, raw_root=raw_root)
                   for a in arms]
        rep = build_report(results, clause_ids, source)
    except (EvalError, T.Phase1Error) as exc:
        print(f"⛔ {type(exc).__name__}: {exc}")
        return 2

    print_report(rep)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            json.dump(rep, fh, indent=1, default=str)
        print(f"\nwrote {args.out}")

    spent = sum(float(getattr(r.client, "spent_usd", 0.0) or 0.0)
                for r in results)
    # ⚠️ Counted from the RUN, not read off the client. `Client.calls` is an
    # int and a stub's `calls` is the list of what it was sent; `sum()` over
    # the two shapes raises, which is how this was found. The run knows the
    # answer exactly — one call per clause per repeat, no repair.
    calls = sum(len(rr.clauses) for r in results for rr in r.repeats)
    if spent:
        print(T.spend_invisibility_warning(arms[0].prov, spent, calls))
    usable = any(o.module is not None
                 for r in results for rr in r.repeats for o in rr.clauses)
    return 0 if usable else 1


if __name__ == "__main__":
    raise SystemExit(main())
