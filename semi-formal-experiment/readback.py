"""READ-BACK: does the ontology faithfully represent the DOCUMENT?

Everything measured in this repo so far is PREDICTIVE — how well the atoms
recover a panel's judgement. This module measures something different and
logically prior: whether the atoms recorded for a passage are a faithful
compression OF THAT PASSAGE. It never touches the panel, and it is worth
having precisely because it cannot be improved by fitting the panel.

⛔ THE ORIGINAL MOTIVATING ARGUMENT WAS WRONG AND IS WITHDRAWN. It read: "the
atoms support +0.591 under supervision, raw clause text gives +0.398, but the
judges reach +0.514-0.555 — if the atoms were a faithful compression a reader
of them should approach a reader of the text, so that gap says they are not."
ORDER THOSE NUMBERS: atoms +0.591 > judges +0.514-0.555 > text +0.398. The
atoms are the BEST reader in the list. There is no gap in that direction, and
this module was built on a claim that pointed the opposite way from the data.
See `ONTOLOGY_REFINEMENT.md` (withdrawn on the same error).

The module survives its own premise because the QUESTION is still unasked and
does not depend on that argument: everything measured to date is PREDICTIVE
(does the ontology predict what a panel called relevant?). Nothing has tested
whether the ontology is a faithful representation OF THE DOCUMENT. Those are
different questions, and an atom set can score well on the first for spurious
reasons. That is the whole justification — no gap argument is needed, and the
result bears it out: discrimination came back AT ceiling while sufficiency
collapsed to 0.16, which no reading of the +0.591/+0.398 numbers predicted.

THE DESIGN
----------
Step 1, a DETERMINISTIC renderer. `render(atoms, clause_kind)` -> English. No
model, no network, no file, no randomness: a fixed template with the atoms'
names, kinds and glosses slotted in. This is the crux. A model asked to
"describe the passage from its atoms" fills gaps from its own knowledge of what
model specs say, and emits fluent text resembling the clause even when the
atoms are impoverished — which would measure the model's priors, not the
ontology. A mechanical renderer can only say what is there, so the gaps stay
visible.

What the render carries: the clause kind, and for each atom its name, its kind
and its gloss, grouped by the span the annotator drew it from. What it
deliberately does NOT carry: `quote` and `locator` — verbatim source text and
its address. Including either would make the read-back a copy test and
discrimination trivially perfect. That exclusion is asserted in
`test_render_ignores_the_source_text_fields_by_design`.

Step 2, three measures, judged by a cheap model against the SOURCE CLAUSE:
  FAITHFUL       does the render assert what the clause does not say?
  SUFFICIENT     does the clause require what the render omits?
  DISCRIMINABLE  given the render and N candidate clauses, which is its
                 source? Objective, not a judgement call. Distractors are
                 drawn BOTH at random AND from the same section; the
                 same-section case is the hard and interesting one.

THE CEILING
-----------
Atom-name sets partition the corpus into equivalence classes; clauses sharing
a class are indistinguishable by atom IDENTITY alone, whatever the rendering.
That is an information-theoretic ceiling on discriminability, and measured
accuracy must be read against it: far below the ceiling means the loss is in
the RENDERING (glosses and kinds failing to preserve what the names encode),
not in the ontology, and those have completely different fixes.

One correction this module makes to that framing: the whole-corpus ceiling
(classes / n) is the ceiling when EVERY other clause is a candidate. Inside a
4- or 10-candidate trial a twin is usually absent, so the trial-conditional
ceiling is near 1.0 and is the figure a measured accuracy should be compared
with. Both are reported; `identity_collision` is recorded per trial.

PRE-REGISTRATION (written before any live call; run with --live to compare)
--------------------------------------------------------------------------
Sample: 125 clauses, 25 per kind, seed 20260802. At n=125 a 95% Wilson
interval on an accuracy near 0.85 is about +-0.06; per kind (n=25) about
+-0.15 — coarse, but the per-kind effects predicted below are large.

  D1  Discrimination, RANDOM distractors, N=4:  ~0.90
  D2  Discrimination, RANDOM distractors, N=10: ~0.80
  D3  Discrimination, SAME-SECTION, N=4:        ~0.65
  D4  Discrimination, SAME-SECTION, N=10:       ~0.45
      (random distractors are mostly off-topic, so the render only has to
      carry the topic; same-section distractors share the topic and force the
      render to carry what distinguishes neighbours, which is where the atoms
      are expected to be thin.)
  F1  FAITHFUL ~0.90+ overall. A mechanical renderer cannot invent; the
      failures that do occur should be glosses that over-generalise or import
      a party the clause never names.
  F2  SUFFICIENT ~0.35 overall, and this is the headline. The atoms record
      unordered, unrelated concepts; a clause's operative content is mostly
      relational.

  Per kind, predicted worst-to-best on SUFFICIENT and on same-section
  discrimination:
    example      worst. An example's atoms name what happens in the example
                 but not what it is an example OF; and examples inside one
                 section are near-identical in atom terms.
    conditional  loses its TRIGGER. "if X then Y", "Y unless X" and "never Y"
                 all render as the unordered set {X, Y}: no condition, no
                 exception, no polarity.
    meta         poor. Meta clauses are about the document, and atoms about
                 the document are few and generic.
    holistic     middling.
    definitional best. A definition is close to a name plus a gloss, which is
                 exactly what an atom is.

  C   Same-section discrimination will fall well below the whole-corpus
      identity ceiling AND below the trial-conditional ceiling (~0.99), so
      the loss is predicted to be in the projection to English rather than in
      atom identity.

Usage
-----
    .venv/bin/python readback.py --dry-run          # prompts only, no spend
    .venv/bin/python readback.py --live             # the measurement
    .venv/bin/python readback.py --report out.json  # re-analyse an artifact
"""
from __future__ import annotations

import argparse
import json
import math
import os
import random
import re
import time

HERE = os.path.dirname(os.path.abspath(__file__))
CLAUSES_PATH = os.path.join(HERE, "modelspec_clauses.json")
ANNOTATIONS_PATH = os.path.join(HERE, "annotations_b8.json")
PROMPT_PATH = os.path.join(HERE, "readback_prompt.md")

#: Atom fields the renderer READS. Dropping or altering any one of them must
#: change the output — that is what makes the render a total function of the
#: ontology's content rather than a lossy summary of a subset of it.
RENDERED_FIELDS = ("name", "kind", "gloss", "span_id")

#: Atom fields the renderer deliberately IGNORES. `quote` is verbatim document
#: text; `locator` is its address; `clause_id` is its key. None is ontology
#: content, and any of them would leak the document into its own read-back.
IGNORED_FIELDS = ("quote", "locator", "clause_id")

CLAUSE_KINDS = ("conditional", "definitional", "example", "holistic", "meta")

#: Generic type descriptions. Written to be true of the TYPE, not of this
#: document — the renderer must not smuggle in knowledge of what the document
#: says.
CLAUSE_KIND_GLOSS = {
    "conditional": "a passage that makes something depend on a condition",
    "definitional": "a passage that fixes the meaning of a term",
    "example": "a passage that illustrates something with a case",
    "holistic": "a passage stating a general orientation rather than a "
                "specific rule",
    "meta": "a passage about the document itself",
}

#: The closed four-member atom taxonomy the index is built on.
ATOM_KIND_GLOSS = {
    "situation": "a circumstance that may or may not obtain",
    "act": "something someone does",
    "entity": "a party, role, or artifact",
    "value": "a good being promoted or traded off",
}

#: Candidate passages are capped so a 3,036-character outlier cannot dominate
#: a ten-candidate prompt. The cap is above the 90th percentile (963 chars),
#: and every truncation is counted in the artifact.
CANDIDATE_CAP = 1500


# --------------------------------------------------------------------------
# THE RENDERER — mechanical, total, and the crux of the design

def _fmt_field(value, missing):
    """A missing field renders as an explicit marker, never as nothing. A
    silently dropped field would make the render a function of fewer inputs
    than the ontology holds."""
    v = "" if value is None else str(value).strip()
    return v if v else missing


def render(atoms, clause_kind=None):
    """The ontology's content for one clause, as English. Deterministic.

    Total over RENDERED_FIELDS: every field is either printed or printed as an
    explicit `<no ...>` marker, so dropping one always changes the output.

    Grouping. Atoms are grouped by `span_id` in first-appearance order. A group
    is exactly "the concepts the index drew from the same stretch of the
    passage" — genuine structure the ontology holds, and expressible without
    reproducing a single word of the passage. Span ids themselves are not
    printed (they are addresses, not content); their PARTITION is.
    """
    atoms = list(atoms or [])
    kind = _fmt_field(clause_kind, "unclassified")
    gloss = CLAUSE_KIND_GLOSS.get(kind)
    head = (f"PASSAGE TYPE: {kind}" + (f" ({gloss})." if gloss else "."))

    lines = [head, ""]
    if not atoms:
        lines.append("THE INDEX RECORDS NO CONCEPTS FOR THIS PASSAGE.")
    else:
        groups, order = {}, []
        for a in atoms:
            sid = _fmt_field(a.get("span_id"), "<no span>")
            if sid not in groups:
                groups[sid] = []
                order.append(sid)
            groups[sid].append(a)
        lines.append(
            f"THE INDEX RECORDS {len(atoms)} "
            f"CONCEPT{'S' if len(atoms) != 1 else ''} FOR THIS PASSAGE, IN "
            f"{len(order)} GROUP{'S' if len(order) != 1 else ''}. A group "
            "holds the concepts the index drew from the same stretch of the "
            "passage.")
        for i, sid in enumerate(order, start=1):
            lines.append("")
            lines.append(f"Group {i}:")
            for a in groups[sid]:
                name = _fmt_field(a.get("name"), "<no name>")
                akind = _fmt_field(a.get("kind"), "<no type>")
                agloss = _fmt_field(a.get("gloss"), "<no explanation>")
                tgloss = ATOM_KIND_GLOSS.get(akind)
                lines.append(
                    f"  - {name} "
                    f"[{akind}{': ' + tgloss if tgloss else ''}] "
                    f"-- {agloss.rstrip('.')}.")
    lines += [
        "",
        "THAT IS EVERYTHING THE INDEX HOLDS FOR THIS PASSAGE. It records no "
        "wording. The order above is the order the concepts were recorded and "
        "carries no meaning. It records no relation between the concepts: no "
        "condition, no exception, no priority, no polarity, and nothing about "
        "who is addressed or what is required.",
    ]
    return "\n".join(lines)


class ReadbackIndex:
    """Clause id -> its read-back. Holds no model and no state beyond the two
    declared artifacts.

    `sweep` exists so the repo's anti-cheat spy can drive this module: it
    accepts and ignores any query object and renders the whole corpus.
    """

    def __init__(self, rows, annotations=None):
        self.rows = list(rows or [])
        self.by_id = {r["id"]: r for r in self.rows}
        self.annotations = _normalize_annotations(annotations)

    def render_clause(self, clause_id):
        row = self.by_id.get(clause_id, {})
        return render(self.annotations.get(clause_id, []), row.get("kind"))

    def sweep(self, _query=None):
        return [(r["id"], self.render_clause(r["id"])) for r in self.rows]


#: The spy in test_no_reference_leak looks for a class by one of a few fixed
#: names before it will consider a module guarded. A module it cannot drive is
#: a module it cannot check, and a skip is not a guard.
Index = ReadbackIndex


# --------------------------------------------------------------------------
# loading

def load_clauses(path=CLAUSES_PATH):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    rows = data["clauses"] if isinstance(data, dict) else data
    return list(rows)


def _normalize_annotations(source):
    if source is None:
        return {}
    if isinstance(source, dict) and "by_clause" in source:
        source = source["by_clause"]
    if isinstance(source, dict) and all(isinstance(v, list)
                                        for v in source.values()):
        return {str(k): list(v) for k, v in source.items()}
    return {}


def load_annotations(path=ANNOTATIONS_PATH):
    """`{clause_id: [atom, ...]}` straight from the annotation artifact."""
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    got = _normalize_annotations(data)
    if got:
        return got
    out = {}
    for a in data.get("atoms", []):
        out.setdefault(str(a.get("clause_id")), []).append(a)
    return out


def load_template(path=PROMPT_PATH):
    """Four sections, split on marker lines."""
    with open(path, encoding="utf-8") as f:
        text = f.read()
    marks = ["=== FIDELITY SYSTEM ===", "=== FIDELITY USER ===",
             "=== DISCRIM SYSTEM ===", "=== DISCRIM USER ==="]
    out, rest = {}, text
    for i, m in enumerate(marks):
        rest = rest.split(m, 1)[1]
        nxt = marks[i + 1] if i + 1 < len(marks) else None
        out[m] = (rest.split(nxt, 1)[0] if nxt else rest).strip()
    return (out[marks[0]], out[marks[1]], out[marks[2]], out[marks[3]])


# --------------------------------------------------------------------------
# sampling and trials

def stratified_sample(rows, per_kind=25, seed=20260802):
    """`per_kind` clauses of EVERY clause kind, deterministically.

    Stratified rather than proportional because the per-kind comparison is the
    point: examples and conditionals are predicted to fail differently, and a
    proportional sample would leave meta and holistic with ~15 clauses each.
    """
    by_kind = {}
    for r in rows:
        by_kind.setdefault(r.get("kind"), []).append(r["id"])
    out = []
    for kind in CLAUSE_KINDS:
        pool = sorted(by_kind.get(kind, []))
        rng = random.Random(f"{seed}|{kind}")
        out.extend(sorted(rng.sample(pool, min(per_kind, len(pool)))))
    return out


def atom_signature(atoms):
    return frozenset(a.get("name") for a in atoms or [])


def equivalence_profile(rows, annotations):
    """The information-theoretic ceiling on discriminability.

    Clauses whose atom-NAME sets are identical cannot be told apart by any
    rendering of those atoms. `identity_ceiling` = classes / n is the best
    accuracy achievable if every other clause were a candidate.
    """
    classes = {}
    for r in rows:
        classes.setdefault(atom_signature(annotations.get(r["id"], [])),
                           []).append(r["id"])
    prof = {}
    for members in classes.values():
        prof[str(len(members))] = prof.get(str(len(members)), 0) + 1
    return {
        "n": len(rows),
        "classes": len(classes),
        "identity_ceiling": len(classes) / len(rows) if rows else 1.0,
        "collision_profile": prof,
        "clauses_in_collision": sum(len(m) for m in classes.values()
                                    if len(m) > 1),
    }


def gloss_echo(rows, annotations, k=8):
    """How often a GLOSS copies the passage verbatim.

    A caveat on discriminability that has to be a number rather than a
    footnote: where an annotator wrote a gloss by lifting the clause's own
    words, the render carries source text after all, and those trials are easy
    for reasons that have nothing to do with the ontology being expressive.
    Counts clauses with at least one shared `k`-word shingle between the
    passage and the concatenated names+glosses.
    """
    annotations = _normalize_annotations(annotations) or annotations or {}
    hits, examples = 0, []
    for r in rows:
        atoms = annotations.get(r["id"], [])
        atom_text = " ".join(f"{a.get('name', '')} {a.get('gloss', '')}"
                             for a in atoms).lower().replace("_", " ")
        words = re.findall(r"[A-Za-z']+", (r.get("quote") or "").lower())
        shared = None
        for i in range(len(words) - k + 1):
            sh = " ".join(words[i:i + k])
            if sh in atom_text:
                shared = sh
                break
        if shared:
            hits += 1
            if len(examples) < 15:
                examples.append({"clause_id": r["id"], "shingle": shared})
    return {"n": len(rows), "clauses_with_echo": hits,
            "rate": hits / len(rows) if rows else 0.0,
            "shingle_words": k, "examples": examples}


def _candidate_text(row):
    q = (row.get("quote") or "").strip()
    if len(q) > CANDIDATE_CAP:
        return q[:CANDIDATE_CAP].rstrip() + " [...]", True
    return q, False


def build_trials(clause_ids, rows, annotations, n_candidates=4,
                 mode="random", seed=20260802):
    """One discrimination trial per clause.

    `mode="random"`  distractors from anywhere in the document.
    `mode="section"` distractors from the SAME section — the near-miss case,
                     where the render has to carry what distinguishes a clause
                     from its neighbours rather than merely its topic.

    Sections smaller than `n_candidates` fall back to topping up from the rest
    of the document; `pool` records which happened, and only trials with
    `pool == "section"` are pure near-miss trials.
    """
    annotations = _normalize_annotations(annotations) or annotations or {}
    by_id = {r["id"]: r for r in rows}
    all_ids = [r["id"] for r in rows]
    by_section = {}
    for r in rows:
        by_section.setdefault(r.get("section_id"), []).append(r["id"])
    sigs = {r["id"]: atom_signature(annotations.get(r["id"], [])) for r in rows}

    trials = []
    for cid in clause_ids:
        row = by_id[cid]
        rng = random.Random(f"{seed}|{cid}|{n_candidates}|{mode}")
        if mode == "section":
            pool = [i for i in sorted(by_section.get(row.get("section_id"), []))
                    if i != cid]
            pool_name = "section"
        else:
            pool = [i for i in all_ids if i != cid]
            pool_name = "random"
        need = n_candidates - 1
        if len(pool) < need:
            pool_name = "section+fallback" if mode == "section" else "random"
            extra = [i for i in all_ids if i != cid and i not in set(pool)]
            pool = pool + sorted(rng.sample(extra, min(need - len(pool),
                                                       len(extra))))
        chosen = rng.sample(pool, min(need, len(pool)))
        cands = chosen + [cid]
        rng.shuffle(cands)
        texts, trunc = [], 0
        for c in cands:
            t, was = _candidate_text(by_id[c])
            texts.append(t)
            trunc += int(was)
        src_full = (row.get("quote") or "").strip()
        trials.append({
            "clause_id": cid,
            "clause_kind": row.get("kind"),
            "section_id": row.get("section_id"),
            "mode": mode,
            "pool": pool_name,
            "seed": seed,
            "n_candidates": len(cands),
            "n_atoms": len(annotations.get(cid, [])),
            "candidate_ids": cands,
            "candidate_texts": texts,
            "answer_index": cands.index(cid),
            "truncated_candidates": trunc,
            "source_text": src_full,
            "render": render(annotations.get(cid, []), row.get("kind")),
            "identity_collision": any(sigs[c] == sigs[cid]
                                      for c in cands if c != cid),
            # An offline upper bound on how much the clause-kind label alone
            # could be doing: if only one candidate has the stated kind, the
            # label solves the trial without any atom carrying weight.
            "kind_alone_solves": sum(
                1 for c in cands if by_id[c].get("kind") == row.get("kind")) == 1,
        })
    return trials


# --------------------------------------------------------------------------
# prompts. NOTHING here may be a function of the answer.

def _sub(template, n, items):
    return template.replace("{{N}}", str(n)).replace("{{ITEMS}}", items)


def discrim_prompt(trials):
    """(system, user). A pure function of each trial's render and its ORDERED
    candidate texts. Nothing else about the trial is read — above all not
    `answer_index`, `clause_id` or `candidate_ids`."""
    _, _, sys_t, usr_t = load_template()
    blocks = []
    for i, t in enumerate(trials, start=1):
        cands = "\n".join(
            f"  ({j}) {txt}" for j, txt in enumerate(t["candidate_texts"],
                                                     start=1))
        blocks.append(
            f"### ITEM {i}\nDESCRIPTION:\n{t['render']}\n\n"
            f"CANDIDATE PASSAGES:\n{cands}")
    return sys_t, _sub(usr_t, len(trials), "\n\n".join(blocks))


def fidelity_prompt(items):
    """(system, user) for the FAITHFUL / SUFFICIENT judgement. The passage is
    given in FULL here — it is the ground truth being compared against, not a
    candidate competing for prompt space."""
    sys_t, usr_t, _, _ = load_template()
    blocks = []
    for i, t in enumerate(items, start=1):
        blocks.append(
            f"### ITEM {i}\nDESCRIPTION:\n{t['render']}\n\n"
            f"PASSAGE:\n{t['source_text']}")
    return sys_t, _sub(usr_t, len(items), "\n\n".join(blocks))


# --------------------------------------------------------------------------
# parsing

def _json_array(text):
    if not isinstance(text, str):
        return None, "no response"
    s = text.strip()
    s = re.sub(r"^```(?:json)?\s*", "", s)
    s = re.sub(r"\s*```$", "", s).strip()
    i, j = s.find("["), s.rfind("]")
    if i < 0 or j < i:
        return None, "no JSON array in response"
    try:
        obj = json.loads(s[i:j + 1])
    except ValueError as e:
        return None, f"bad JSON: {e}"
    return (obj, None) if isinstance(obj, list) else (None, "not an array")


def parse_discrim(text, batch):
    """(choices, errors). `choices[k]` is a 0-BASED candidate index or None.

    An out-of-range or absent answer is None, never a guess: a silent
    coercion to 0 would inflate accuracy by exactly the chance rate.
    """
    choices = [None] * len(batch)
    obj, err = _json_array(text)
    if err:
        return choices, [err]
    errors = []
    for rec in obj:
        if not isinstance(rec, dict):
            continue
        try:
            k = int(rec.get("item")) - 1
            c = int(rec.get("choice")) - 1
        except (TypeError, ValueError):
            errors.append(f"unparseable record {rec!r}")
            continue
        if not 0 <= k < len(batch):
            errors.append(f"item {rec.get('item')} out of range")
            continue
        if not 0 <= c < batch[k]["n_candidates"]:
            errors.append(f"item {rec.get('item')}: choice "
                          f"{rec.get('choice')} out of range")
            continue
        choices[k] = c
    for k, c in enumerate(choices):
        if c is None and not errors:
            errors.append(f"item {k + 1}: no answer")
    return choices, errors


def parse_fidelity(text, batch):
    out = [None] * len(batch)
    obj, err = _json_array(text)
    if err:
        return out, [err]
    errors = []
    for rec in obj:
        if not isinstance(rec, dict):
            continue
        try:
            k = int(rec.get("item")) - 1
        except (TypeError, ValueError):
            continue
        if not 0 <= k < len(batch):
            continue
        f, s = rec.get("faithful"), rec.get("sufficient")
        if not isinstance(f, bool) or not isinstance(s, bool):
            errors.append(f"item {rec.get('item')}: non-boolean verdict")
            continue
        out[k] = {
            "faithful": f, "sufficient": s,
            "unsupported": [str(x)[:200] for x in (rec.get("unsupported") or [])
                            if isinstance(x, (str, int, float))],
            "missing": [str(x)[:200] for x in (rec.get("missing") or [])
                        if isinstance(x, (str, int, float))],
        }
    return out, errors


# --------------------------------------------------------------------------
# statistics

def wilson(k, n, z=1.959963984540054):
    """95% Wilson score interval. Chosen over the normal approximation because
    several cells here sit near 0 or 1 at n=25, where the normal interval runs
    outside [0, 1] and understates the uncertainty."""
    if n <= 0:
        return (0.0, 1.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def _rate(k, n):
    lo, hi = wilson(k, n)
    return {"k": k, "n": n, "rate": (k / n) if n else None,
            "ci95": [round(lo, 4), round(hi, 4)]}


# --------------------------------------------------------------------------
# the live run

def _batches(seq, size):
    return [seq[i:i + size] for i in range(0, len(seq), size)]


def _call(client, system, user):
    if hasattr(client, "complete_envelope"):
        env = client.complete_envelope(system, user)
        return (env or {}).get("text")
    return client.complete(system, user)


def run(clause_ids=None, rows=None, annotations=None, client=None,
        conditions=((4, "random"), (10, "random"),
                    (4, "section"), (10, "section")),
        per_kind=25, seed=20260802, discrim_batch=5, fidelity_batch=5,
        workers=4, progress=None, fidelity_client=None, prior=None):
    """The whole measurement. Returns the artifact dict.

    `prior` is a previously written artifact: any clause already answered in
    it is not asked again. The provider rate-limits at 200k tokens/minute and
    a parallel first pass lost 65 of 100 discrimination batches to 429s;
    re-billing the 35 that succeeded to recover them would be waste, and
    silently dropping them would shrink the sample without saying so.
    """
    rows = rows if rows is not None else load_clauses()
    annotations = (annotations if annotations is not None
                   else load_annotations())
    clause_ids = clause_ids or stratified_sample(rows, per_kind, seed)

    base = build_trials(clause_ids, rows, annotations, 4, "random", seed)
    jobs = []
    prior = prior or {}
    pr = (prior.get("results") or {})
    results = {"fidelity": dict(pr.get("fidelity") or {}),
               "discrim": {k: dict(v) for k, v in
                           (pr.get("discrim") or {}).items()}}
    # Errors are NOT carried over: a 429 in an earlier pass whose trial this
    # pass answers is not an error of this measurement. The count is kept so
    # the artifact still records that a retried pass happened.
    n_prior_errors = len(prior.get("errors") or [])
    errors = []

    # FIDELITY
    todo = [t for t in base if results["fidelity"].get(t["clause_id"]) is None]
    for bi, b in enumerate(_batches(todo, fidelity_batch)):
        jobs.append(("fidelity", None, bi, b))
    # DISCRIMINATION
    trial_sets = {}
    for n, mode in conditions:
        cond = f"{mode}_N{n}"
        ts = build_trials(clause_ids, rows, annotations, n, mode, seed)
        trial_sets[cond] = ts
        have = results["discrim"].get(cond) or {}
        todo = [t for t in ts if have.get(t["clause_id"]) is None]
        for bi, b in enumerate(_batches(todo, discrim_batch)):
            jobs.append(("discrim", cond, bi, b))

    def do(job):
        kind, cond, bi, batch = job
        # Two clients, because the two tasks have very different completion
        # budgets. Measured: a discrimination batch of 5 spends ~240 completion
        # tokens, a fidelity batch of 5 blew a 1,400-token cap entirely on
        # reasoning and returned ZERO content. One shared cap would either
        # truncate every fidelity call or overpay for every discrimination one.
        cl = (fidelity_client or client) if kind == "fidelity" else client
        if kind == "fidelity":
            system, user = fidelity_prompt(batch)
        else:
            system, user = discrim_prompt(batch)
        try:
            text = _call(cl, system, user)
        except Exception as e:                       # a dead call is data
            return job, None, [f"{kind}/{cond}/{bi}: "
                               f"{type(e).__name__}: {e}"]
        if kind == "fidelity":
            parsed, errs = parse_fidelity(text, batch)
        else:
            parsed, errs = parse_discrim(text, batch)
        return job, parsed, [f"{kind}/{cond}/{bi}: {e}" for e in errs]

    done = 0
    if workers and workers > 1:
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=workers) as ex:
            outs = list(ex.map(do, jobs))
    else:
        outs = [do(j) for j in jobs]

    for (kind, cond, bi, batch), parsed, errs in outs:
        errors.extend(errs)
        done += 1
        if progress:
            progress(done, len(jobs))
        if parsed is None:
            continue
        for t, p in zip(batch, parsed):
            if kind == "fidelity":
                results["fidelity"][t["clause_id"]] = p
            else:
                results["discrim"].setdefault(cond, {})[t["clause_id"]] = p

    return {
        "provenance": {
            "created": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "seed": seed, "per_kind": per_kind,
            "conditions": [f"{m}_N{n}" for n, m in conditions],
            "n_clauses": len(clause_ids),
            "discrim_batch": discrim_batch, "fidelity_batch": fidelity_batch,
            "candidate_cap": CANDIDATE_CAP,
            "renderer": "readback.render (mechanical, no model)",
            "errors_in_earlier_passes": n_prior_errors,
            "jobs_this_pass": len(jobs),
        },
        "clause_ids": list(clause_ids),
        "trials": {k: [{kk: v for kk, v in t.items()
                        if kk not in ("candidate_texts", "source_text")}
                       for t in ts] for k, ts in trial_sets.items()},
        "fidelity_trials": [{kk: v for kk, v in t.items()
                             if kk not in ("candidate_texts",)} for t in base],
        "results": results,
        "errors": errors,
        "ceiling": equivalence_profile(rows, annotations),
        "gloss_echo": gloss_echo(rows, annotations),
    }


# --------------------------------------------------------------------------
# analysis

def summarize(art):
    """Accuracy / faithfulness / sufficiency overall and per clause kind,
    every rate with a 95% Wilson interval."""
    fid_trials = art["fidelity_trials"]
    kind_of = {t["clause_id"]: t["clause_kind"] for t in fid_trials}
    out = {"ceiling": art["ceiling"], "fidelity": {}, "discrim": {}}
    # ⚠️ THE DENOMINATOR IS THE DECLARED SAMPLE, NEVER WHAT CAME BACK.
    # A rate-limited batch writes NO key into `results`, so counting `None`s
    # among present keys cannot see it. The 2026-08-02 run lost 52 of 125
    # calls that way: one condition sat at 90/125 with the losses concentrated
    # in whole clause-kind strata (batches are contiguous slices of a
    # kind-sorted sample) while this function reported `"unanswered": 0`.
    declared = list(art.get("clause_ids") or [])
    n_declared = len(declared)

    def _coverage(per):
        answered = sum(1 for c in declared
                       if per.get(c) is not None) if declared else len(per)
        return (answered, n_declared or len(per))

    fr = art["results"]["fidelity"]
    for label, key in (("faithful", "faithful"), ("sufficient", "sufficient")):
        cells = {"overall": [0, 0]}
        for cid, rec in fr.items():
            if rec is None:
                continue
            for cell in ("overall", kind_of.get(cid, "?")):
                c = cells.setdefault(cell, [0, 0])
                c[0] += int(bool(rec[key]))
                c[1] += 1
        out["fidelity"][label] = {c: _rate(*v) for c, v in sorted(cells.items())}
    out["fidelity"]["coverage"] = _coverage(fr)
    out["fidelity"]["unanswered"] = (out["fidelity"]["coverage"][1]
                                     - out["fidelity"]["coverage"][0])

    for cond, per in sorted(art["results"]["discrim"].items()):
        answer = {t["clause_id"]: t["answer_index"]
                  for t in art["trials"][cond]}
        collide = {t["clause_id"]: t["identity_collision"]
                   for t in art["trials"][cond]}
        kindsolve = {t["clause_id"]: t["kind_alone_solves"]
                     for t in art["trials"][cond]}
        cells, ceil = {"overall": [0, 0]}, [0, 0]
        ks = {"kind_alone_solvable": [0, 0], "kind_alone_unsolvable": [0, 0]}
        for cid, choice in per.items():
            if choice is None:
                continue
            hit = int(choice == answer[cid])
            for cell in ("overall", kind_of.get(cid, "?")):
                c = cells.setdefault(cell, [0, 0])
                c[0] += hit
                c[1] += 1
            ceil[0] += int(not collide[cid])
            ceil[1] += 1
            b = ks["kind_alone_solvable" if kindsolve[cid]
                   else "kind_alone_unsolvable"]
            b[0] += hit
            b[1] += 1
        n = int(cond.split("_N")[1])
        out["discrim"][cond] = {
            "cells": {c: _rate(*v) for c, v in sorted(cells.items())},
            "chance": 1.0 / n,
            "trial_conditional_ceiling": (ceil[0] / ceil[1]) if ceil[1] else None,
            "corpus_identity_ceiling": art["ceiling"]["identity_ceiling"],
            "by_kind_label_reachability": {k: _rate(*v)
                                           for k, v in sorted(ks.items())},
            "coverage": _coverage(per),
            "unanswered": _coverage(per)[1] - _coverage(per)[0],
        }
    return out


def losses(art, top=25):
    """WHAT IS SYSTEMATICALLY LOST — the phrases the judge listed as missing,
    pooled and counted per clause kind."""
    kind_of = {t["clause_id"]: t["clause_kind"]
               for t in art["fidelity_trials"]}
    out = {}
    for cid, rec in art["results"]["fidelity"].items():
        if not rec:
            continue
        k = kind_of.get(cid, "?")
        d = out.setdefault(k, {"missing": [], "unsupported": []})
        for m in rec["missing"]:
            d["missing"].append((cid, m))
        for m in rec["unsupported"]:
            d["unsupported"].append((cid, m))
    for k in out:
        out[k]["missing"] = out[k]["missing"][:top]
        out[k]["unsupported"] = out[k]["unsupported"][:top]
    return out


# --------------------------------------------------------------------------
# CLI

def _print_report(art):
    s = summarize(art)
    c = s["ceiling"]
    print(f"\nCEILING  {c['classes']}/{c['n']} distinct atom-identity classes "
          f"= {c['identity_ceiling']:.3f}   "
          f"({c['clauses_in_collision']} clauses share a class)")
    print(f"         collision profile {c['collision_profile']}")

    print("\nFIDELITY (rate [95% Wilson CI])")
    kinds = ["overall"] + list(CLAUSE_KINDS)
    print(f"  {'':14s}" + "".join(f"{k:>22s}" for k in kinds))
    for label in ("faithful", "sufficient"):
        row = s["fidelity"][label]
        cells = []
        for k in kinds:
            r = row.get(k)
            cells.append("-" if not r or not r["n"] else
                         f"{r['rate']:.2f} [{r['ci95'][0]:.2f},{r['ci95'][1]:.2f}] n={r['n']}")
        print(f"  {label:14s}" + "".join(f"{c:>22s}" for c in cells))

    print("\nDISCRIMINABILITY (accuracy [95% Wilson CI])")
    print(f"  {'':18s}" + "".join(f"{k:>22s}" for k in kinds))
    for cond in sorted(s["discrim"], key=lambda c: (c.split("_")[0],
                                                    int(c.split("_N")[1]))):
        d = s["discrim"][cond]
        cells = []
        for k in kinds:
            r = d["cells"].get(k)
            cells.append("-" if not r or not r["n"] else
                         f"{r['rate']:.2f} [{r['ci95'][0]:.2f},{r['ci95'][1]:.2f}] n={r['n']}")
        print(f"  {cond:18s}" + "".join(f"{c:>22s}" for c in cells))
        print(f"  {'':18s}chance {d['chance']:.2f}   trial-conditional "
              f"ceiling {d['trial_conditional_ceiling']}   corpus ceiling "
              f"{d['corpus_identity_ceiling']:.3f}   unanswered "
              f"{d['unanswered']}")
        kr = d["by_kind_label_reachability"]
        print(f"  {'':18s}kind-label alone could solve: "
              f"{kr['kind_alone_solvable']['n']} trials "
              f"(acc {kr['kind_alone_solvable']['rate']}); "
              f"could not: {kr['kind_alone_unsolvable']['n']} "
              f"(acc {kr['kind_alone_unsolvable']['rate']})")
    if art.get("errors"):
        print(f"\n{len(art['errors'])} error(s); first few:")
        for e in art["errors"][:6]:
            print("   !! " + e)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--live", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--report", help="re-analyse an existing artifact")
    ap.add_argument("--resume", help="artifact whose answers to keep")
    ap.add_argument("--provider", default="luna")
    ap.add_argument("--per-kind", type=int, default=25)
    ap.add_argument("--seed", type=int, default=20260802)
    ap.add_argument("--max-tokens", type=int, default=1400)
    ap.add_argument("--fidelity-max-tokens", type=int, default=4000)
    ap.add_argument("--discrim-batch", type=int, default=5)
    ap.add_argument("--fidelity-batch", type=int, default=5)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--temperature", type=float, default=1.0)
    ap.add_argument("--limit", type=int, default=0,
                    help="pilot: keep only this many clauses")
    ap.add_argument("--conditions", default="4:random,10:random,"
                                            "4:section,10:section")
    ap.add_argument("--out", default="readback_results.json")
    a = ap.parse_args(argv)

    if a.report:
        with open(a.report, encoding="utf-8") as f:
            _print_report(json.load(f))
        return 0

    rows, ann = load_clauses(), load_annotations()
    ids = stratified_sample(rows, a.per_kind, a.seed)
    if a.limit:
        ids = ids[:a.limit]
    conds = tuple((int(c.split(":")[0]), c.split(":")[1])
                  for c in a.conditions.split(",") if c.strip())

    from providers import ProviderConfig, make_client
    def _cfg(max_tokens):
        c = {p.name: p for p in ProviderConfig.load_all(
            os.path.join(HERE, "providers.json"))}[a.provider]
        c.max_tokens = max_tokens
        # This model rejects any temperature but the default with a 400.
        # providers._adapt_body recovers by dropping the parameter and
        # retrying, but the retry counter is shared with the 429 backoff, so
        # under rate-limiting the adaptation ran out of attempts and killed
        # whole batches. Ask for the only supported value up front.
        c.temperature = a.temperature
        return c
    cfg = _cfg(a.max_tokens)
    client = make_client(cfg, live=a.live, log_dir="prompt_log_readback")
    fid_client = make_client(_cfg(a.fidelity_max_tokens), live=a.live,
                             log_dir="prompt_log_readback")

    t0 = time.time()

    def progress(done, total):
        print(f"  [{done}/{total}] {time.time() - t0:.0f}s", flush=True)

    art = run(ids, rows, ann, client, conditions=conds, per_kind=a.per_kind,
              seed=a.seed, discrim_batch=a.discrim_batch,
              fidelity_batch=a.fidelity_batch, workers=a.workers,
              progress=progress, fidelity_client=fid_client,
              prior=(json.load(open(a.resume, encoding="utf-8"))
                     if a.resume and os.path.exists(a.resume) else None))
    art["provenance"]["model"] = cfg.model
    art["provenance"]["live"] = bool(a.live)
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(art, f, indent=1, ensure_ascii=False)
    print(f"-> {a.out}")
    _print_report(art)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
