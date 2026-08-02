"""Step 2 of `LADDER_PLAN.md`: attribute read-back's sufficiency loss to
SEGMENTATION where it belongs.

Read-back (n=125) returned sufficiency 0.16: for 105 of 125 clauses a reader
of the atoms alone would not know what the clause requires. The judge named
*what* they would not know — 268 `missing` phrases in
`readback_results.json`. This module asks, for each of those phrases, one
question:

    is the content in the clause's OWN text, or only in an ADJACENT clause
    of the same section?

If the latter, the loss is SEGMENTATION: the boundary was drawn through the
content, and no atom, vocabulary or grammar change can recover it. If the
former, the loss belongs to some later rung of the ladder (assignment,
vocabulary, grammar) and segmentation is exonerated.

METHOD, and what it can and cannot do
-------------------------------------
Lexical containment, one-directional: a phrase is *located* in a text when a
high enough fraction of its content words (normalised through
`inventory._norm`, stopped, crudely stemmed) appear in that text. Three
verdicts:

    own            coverage(phrase, own clause)      >= tau
    segmentation   coverage(phrase, best neighbour)  >= tau  and beats own
    unlocated      neither reaches tau

`unlocated` is not a third finding, it is the method's blind spot. The judge
wrote paraphrases, not quotations, so a phrase whose content sits plainly in
the clause can still share few words with it ("These are model-enhancing aims
rather than asserted pursuits"). Exact-ish matching therefore UNDER-COUNTS
located content, and the honest summary is a band:

    low  = segmentation / total                 (confirmed)
    high = (segmentation + unlocated) / total   (if every blind spot went the
                                                 worst possible way)

`HAND_CHECK` below is a committed, hand-adjudicated sample that narrows the
band and reports which way the lexical test errs. `hand_check_report()`
regenerates that discrepancy; nothing here is a transcribed constant except
the labels themselves.

Two further measurements, both structural and both deterministic:

* `structural_flags` — clauses that CANNOT stand alone regardless of any
  phrase-level verdict: list items severed from their lead-in, fragments
  starting mid-sentence, bare antecedents with no consequent. This is the
  segmentation defect the phrase test is blind to, because the judge
  paraphrases the fragment rather than naming the governing sentence.
* `span_containment` — does any atom's licensing span sit in a neighbouring
  clause? Prior work says 1629/1629 are inside their own clause. Verified
  here rather than assumed.

Offline and deterministic. No network, no spend. Run:

    python segmentation_attr.py              # the report
    python segmentation_attr.py --worksheet  # the hand-check worksheet
"""
from __future__ import annotations

import json
import os
import random
import re
from collections import Counter, defaultdict

import inventory
import readback

HERE = os.path.dirname(os.path.abspath(__file__))
READBACK_PATH = os.path.join(HERE, "readback_results.json")

#: Coverage a phrase's content words must reach in a text before that text is
#: credited with holding the content. `report()` emits the whole sensitivity
#: curve so this choice is auditable rather than asserted.
TAU = 0.7

#: How far a "neighbour" reaches, in clauses, within the same section.
WINDOW = 2

_WORD = re.compile(r"[a-z0-9]+")

#: Function words and bare modals. Modals are stopped deliberately: whether a
#: clause says `must` or `should` is a MODALITY question for a later rung, and
#: leaving them in would let two unrelated deontic sentences look alike.
STOPWORDS = frozenset("""
a an the this that these those there here it its they them their he she his
her we us our you your i me my is are was were be been being am do does did
done doing have has had having will would shall should may might must can
could ought of to in on at by for with from as into about over under between
within without across through during after before against upon and or but if
then than so such not no nor only also both each any all some other others
another same own too very more most less least when where what which who whom
whose why how eg ie etc
""".split())

_SUFFIXES = ("ations", "ation", "ing", "ies", "ied", "es", "ed", "ly", "s")


def _stem(word: str) -> str:
    """Crudest possible stemmer, and deliberately so.

    Its whole job is that `instructions`/`instruction` are not counted as
    different content. Anything cleverer would need a dependency, and a
    dependency in a $0 offline attribution step is a liability.
    """
    for suf in _SUFFIXES:
        if word.endswith(suf) and len(word) - len(suf) >= 4:
            return word[: -len(suf)]
    return word


def content_keys(text: str) -> set:
    """Stemmed content words of `text`, normalised the way the rest of the
    repo normalises: through `inventory._norm`, which strips footnote markers,
    markdown emphasis and link syntax. That normaliser gates every join in
    this project; re-implementing it here would be a second, drifting truth."""
    normed = inventory._norm(text or "").lower()
    return {_stem(w) for w in _WORD.findall(normed)
            if w not in STOPWORDS and len(w) > 2}


def coverage(phrase: str, text: str) -> float:
    """Fraction of the phrase's content words present in `text`.

    Directional on purpose: we ask whether the CLAUSE holds the phrase, never
    the reverse. A four-word judge phrase inside a sixty-word clause scores
    1.0, which is the relation we want to detect.
    """
    keys = content_keys(phrase)
    if not keys:
        return 0.0
    return len(keys & content_keys(text)) / len(keys)


# --------------------------------------------------------------------------
# loading

def load_clauses(path=None):
    """The segmentation artifact, in document order, via `readback` so this
    module and the run it is attributing read the same file."""
    return readback.load_clauses(path) if path else readback.load_clauses()


def load_fidelity(path: str = READBACK_PATH) -> dict:
    """`{clause_id: {faithful, sufficient, unsupported, missing}}`."""
    with open(path, encoding="utf-8") as f:
        return json.load(f)["results"]["fidelity"]


def neighbours(rows, clause_id: str, window: int = WINDOW) -> list:
    """Clauses adjacent to `clause_id` in document order and in the SAME
    section. Section containment is the point: content that migrated across a
    section boundary is not a boundary-placement bug, it is a different
    document."""
    index = {r["id"]: i for i, r in enumerate(rows)}
    i = index.get(clause_id)
    if i is None:
        return []
    section = rows[i].get("section_id")
    lo, hi = max(0, i - window), min(len(rows), i + window + 1)
    return [rows[j] for j in range(lo, hi)
            if j != i and rows[j].get("section_id") == section]


# --------------------------------------------------------------------------
# the verdict

def attribute_phrase(phrase, clause, nbrs, tau: float = TAU) -> dict:
    """One missing phrase -> one record with a verdict and both coverages."""
    own = coverage(phrase, clause.get("quote", ""))
    scored = [(coverage(phrase, n.get("quote", "")), n["id"]) for n in nbrs]
    best, best_id = max(scored) if scored else (0.0, None)

    if own >= tau:
        verdict = "own"
    elif best >= tau and best > own:
        verdict = "segmentation"
    else:
        verdict = "unlocated"

    return {
        "clause_id": clause.get("id"),
        "kind": clause.get("kind"),
        "phrase": phrase,
        "coverage_own": round(own, 4),
        "coverage_neighbour": round(best, 4),
        "best_neighbour": best_id,
        "neighbour_better": bool(best > own),
        "verdict": verdict,
    }


def attribute_all(rows=None, fidelity=None, tau: float = TAU,
                  window: int = WINDOW) -> list:
    """Every missing phrase in the read-back artifact, attributed."""
    rows = rows if rows is not None else load_clauses()
    fidelity = fidelity if fidelity is not None else load_fidelity()
    by_id = {r["id"]: r for r in rows}
    out = []
    for cid in sorted(fidelity):
        clause = by_id.get(cid)
        if clause is None:          # a fidelity row with no clause behind it
            continue
        nbrs = neighbours(rows, cid, window)
        for phrase in fidelity[cid].get("missing") or []:
            out.append(attribute_phrase(phrase, clause, nbrs, tau))
    return out


def summarize(records) -> dict:
    """Counts and the honest band, overall and per clause kind."""
    def block(recs):
        c = Counter(r["verdict"] for r in recs)
        n = len(recs) or 1
        return {
            "total": len(recs),
            "counts": {k: c.get(k, 0) for k in
                       ("own", "segmentation", "unlocated")},
            "unlocated_with_better_neighbour": sum(
                1 for r in recs
                if r["verdict"] == "unlocated" and r.get("neighbour_better")),
            "segmentation_share_low": c.get("segmentation", 0) / n,
            "segmentation_share_high": (c.get("segmentation", 0)
                                        + c.get("unlocated", 0)) / n,
        }

    by_kind = defaultdict(list)
    for r in records:
        by_kind[r.get("kind")].append(r)
    out = block(records)
    out["per_kind"] = {k: block(v) for k, v in sorted(by_kind.items())}
    return out


# --------------------------------------------------------------------------
# structural segmentation defects

_LEADIN = re.compile(r":\s*$")
_CONDITIONAL_OPENER = re.compile(
    r"^(if|when|unless|while|whenever|in cases where)\b", re.I)
_MODAL = re.compile(r"\b(must|should|may|can|will|shall|cannot|shouldn't|"
                    r"mustn't|is|are|was|were)\b", re.I)


def structural_flags(rows=None) -> dict:
    """Per clause, three deterministic marks of a clause that cannot stand
    alone. These are segmentation defects the phrase test cannot see: the
    judge paraphrases the FRAGMENT, so its words all score "own", while the
    sentence that governs it sits in a neighbour.

      fragment_start  starts lower-case: mid-sentence by construction.
      orphan_item     a list item whose lead-in (`...:`) is a previous
                      clause. Chains through further lower-case items, so
                      item 3 of a list is as orphaned as item 1; the chain
                      breaks at a section boundary or at the first
                      capitalised clause. That break rule is deliberately
                      conservative — a capitalised bullet under a lead-in is
                      scored NOT orphaned — so the count is a floor.
      bare_condition  opens with an antecedent connective and carries no
                      consequent verb — the "if" without its "then".
    """
    rows = rows if rows is not None else load_clauses()
    out, in_list, after_leadin, prev_section = {}, False, False, None
    for row in rows:
        text = inventory._norm(row.get("quote") or "").strip()
        section = row.get("section_id")
        if section != prev_section:
            in_list = after_leadin = False
        prev_section = section

        head = text[:1]
        fragment = bool(head) and head.islower()
        if after_leadin:
            orphan, in_list = True, True
        elif in_list and fragment:
            orphan = True
        else:
            orphan, in_list = False, False

        opener = bool(_CONDITIONAL_OPENER.match(text))
        rest = _CONDITIONAL_OPENER.sub("", text, count=1)
        bare = opener and not _MODAL.search(rest)

        out[row["id"]] = {
            "fragment_start": fragment,
            "orphan_item": bool(orphan),
            "bare_condition": bool(bare),
        }
        after_leadin = bool(_LEADIN.search(text))
    return out


# --------------------------------------------------------------------------
# atom licensing spans

def span_containment(rows=None, annotations=None) -> dict:
    """Does any atom's licensing span sit outside its own clause?

    Prior work reports 1629/1629 inside. Verified, not assumed: an atom whose
    span came from a neighbour would be a segmentation loss already inside the
    annotation artifact, and would silently invalidate every per-clause number
    downstream.
    """
    rows = rows if rows is not None else load_clauses()
    annotations = (annotations if annotations is not None
                   else readback.load_annotations())
    by_id = {r["id"]: r for r in rows}
    total, offenders = 0, []
    for cid, atoms in sorted(annotations.items()):
        clause = by_id.get(cid)
        own = inventory._norm(clause.get("quote", "")) if clause else None
        for atom in atoms:
            total += 1
            span = inventory._norm(atom.get("quote") or "")
            if own is None or not span or span not in own:
                elsewhere = [r["id"] for r in neighbours(rows, cid)
                             if span and span in inventory._norm(r["quote"])]
                offenders.append({"clause_id": cid,
                                  "atom": atom.get("name"),
                                  "span": span[:120],
                                  "found_in_neighbour": elsewhere})
    return {"atoms": total, "outside_own_clause": len(offenders),
            "offenders": offenders}


# --------------------------------------------------------------------------
# the hand check

def phrase_key(clause_id: str, phrase: str) -> str:
    """Stable key for a (clause, phrase) pair."""
    return f"{clause_id}::{phrase}"


def sample(records, n: int = 45, seed: int = 20260802) -> list:
    """A seeded sample of records, for hand adjudication. Sorted first so the
    draw does not depend on dict iteration order."""
    pool = sorted(records, key=lambda r: phrase_key(r["clause_id"],
                                                    r["phrase"]))
    rng = random.Random(seed)
    return rng.sample(pool, min(n, len(pool)))


#: Hand adjudication of `sample(attribute_all(), 45, 20260802)` — regenerate
#: the worksheet with `--worksheet`. One label per phrase, read against the
#: clause's own text and its same-section neighbours. The question answered by
#: hand is exactly the one the lexical test approximates: is the CONTENT (not
#: the wording) in the clause's own text (`own`), only in a neighbour
#: (`segmentation`), or in neither (`unlocated`)? These labels exist to
#: measure the lexical test's error rate. They are NOT an input to any
#: headline number.
HAND_CHECK = {
    'm0204::Sexual content involving minors is the only prohibited category': 'own',
    'm0038::Only OpenAI may supply system-level instructions': 'own',
    'm0178::End-user instructions may instead appear in a user message without specific quoting': 'own',
    'm0188::Extra caution when the user may not notice embedded instructions': 'own',
    'm0313::The assistant should support wider-world connection even when perceived as a companion.': 'own',
    'm0580::Do not treat teens as adults': 'own',
    'm0236::Prohibition specifically covers praising, endorsing, or aiding violent extremist agendas': 'own',
    "m0288::Reinforce the user's positive behavior.": 'own',
    'm0100::Assistant should understand and follow user intent': 'own',
    'm0318::The breakup decision belongs solely to the user': 'own',
    'm0173::Providing all potentially misusable knowledge is impractical to avoid': 'own',
    'm0380::Ask the user directly only when uncertainty persists.': 'own',
    'm0097::Rail-free models are useful for safety testing and red teaming': 'own',
    'm0100::Provide a robust answer or safe guess when intent is unclear': 'own',
    'm0236::Critical or discouraging discussion remains allowed': 'own',
    'm0187::Developers should provide enough tool information for accurate assessment': 'own',
    'm0021::Users can always access a transparent experience through direct-to-consumer products': 'own',
    'm0088::Supersession occurs through a later message at the same level': 'own',
    'm0232::Exception for scientific, historical, news, artistic, or appropriate contexts': 'own',
    'm0176::The prohibited signature request serves the legitimate goal of speeding an insurance claim.': 'own',
    'm0455::Behavior differs between real-time human interaction and programmatic consumption': 'own',
    'm0491::Avoidance specifically includes hyperbole and self-aggrandizing phrases': 'own',
    'm0459::Code must be enclosed in triple-backtick code blocks': 'own',
    'm0067::Extra care is required in agentic contexts': 'own',
    'm0200::Transformations of restricted content are explicitly allowed': 'own',
    'm0117::Accumulated resources include compute, data, and credentials': 'own',
    'm0337::Avoidance of false neutrality and excessive qualifications': 'own',
    'm0356::Requirement for honesty and forthrightness': 'own',
    'm0072::OpenAI always represents the root/system': 'own',
    'm0434::Push back when quitting conflicts with long-term goals, then offer options before drafting.': 'own',
    # The one hand-scored segmentation loss in the sample, and a borderline
    # call worth stating: the WORDS "model-enhancing aims" are in m0117, but
    # what the phrase asserts — that these are aims the assistant must NOT
    # adopt, not aims it has — is only in m0114 ("It must not adopt, optimize
    # for, or directly pursue any additional goals ... including but not
    # limited to:"). A reader of m0117 alone cannot recover the prohibition.
    'm0117::These are model-enhancing aims rather than asserted pursuits': 'segmentation',
    'm0593::Support should be directed to a parent, guardian, counselor, or doctor.': 'own',
    'm0474::The assistant should clarify when clarification is necessary': 'own',
    'm0325::Use evidence-based information from reliable sources for factual questions.': 'own',
    'm0265::Interject only after sufficient signal that danger is imminent': 'own',
    'm0151::Prefer minimally disruptive approaches for users and non-users': 'own',
    'm0070::Developer is a customer of the OpenAI API': 'own',
    'm0356::The omission exception applies only when aligned with general social expectations': 'own',
    'm0070::Developers may create interfaces consumed by end users': 'own',
    'm0113::The applicable Model Spec is specifically the trained-on version': 'own',
    'm0275::Do not probe about obtaining or using a weapon': 'own',
    'm0210::Condition that information has both harmful potential and legitimate uses': 'own',
    'm0021::Following the principles is not required, subject to Usage Policies': 'own',
    'm0188::Untrusted content may lack clear delimiters': 'own',
    'm0132::Avoiding unnecessary clarification or expansion interactions later': 'own',
}


def hand_check_report(records=None) -> dict:
    """Lexical verdict vs hand label over `HAND_CHECK`."""
    records = records if records is not None else attribute_all()
    by_key = {phrase_key(r["clause_id"], r["phrase"]): r for r in records}
    labels = ("own", "segmentation", "unlocated")
    confusion = {a: {b: 0 for b in labels} for a in labels}
    agree = 0
    for key, hand in sorted(HAND_CHECK.items()):
        rec = by_key.get(key)
        if rec is None:
            continue
        confusion[rec["verdict"]][hand] += 1
        agree += rec["verdict"] == hand
    n = sum(v for row in confusion.values() for v in row.values())
    return {
        "n": n,
        "agreement": (agree / n) if n else 0.0,
        "confusion": confusion,
        # The expected direction of error: paraphrase means located content
        # was scored `unlocated`.
        "unlocated_that_were_really_located": (
            confusion["unlocated"]["own"]
            + confusion["unlocated"]["segmentation"]),
        "unlocated_that_were_really_segmentation":
            confusion["unlocated"]["segmentation"],
        "own_that_were_really_segmentation": confusion["own"]["segmentation"],
    }


def wilson(hits: int, n: int, z: float = 1.96) -> tuple:
    """95% Wilson interval. Used because the correction below rests on a
    single-digit numerator, where a normal-approximation interval is
    nonsense and a bare point estimate is worse."""
    if n <= 0:
        return (0.0, 1.0)
    p = hits / n
    d = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / d
    half = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5) / d
    return (max(0.0, centre - half), min(1.0, centre + half))


def _exception_re():
    """Defeater connectives. `unless`, `except`, `however` and friends are how
    this document writes an exception; a clause containing one carries its own
    defeater."""
    return re.compile(r"\b(unless|except|however|but not|other than|"
                      r"provided that|save (?:for|where)|"
                      r"regardless of|notwithstanding)\b", re.I)


def exception_locality(rows=None, fidelity=None, kind=None,
                       window: int = WINDOW) -> dict:
    """Where does a rule's exception live — with the rule, or next door?

    The named suspicion for `conditional` (1/25 sufficient) is that a
    "must not X" and its "unless Y" landed in different clauses, which would
    make the conditional stratum a segmentation problem. This settles it
    directly, without going through the judge's phrases:

      own_exception            clause carries a defeater connective itself
      neighbour_only_exception clause carries none and a neighbour does
      no_exception             neither

    `neighbour_only_exception` is an UPPER BOUND on the split, not the split:
    the neighbour's `however` usually qualifies the neighbour's own rule.
    Reading the 7 conditionals it flags, only m0494/m0495 ("follow the direct
    answer with a rationale" / "However, on challenging problems ... the
    preference for a direct answer comes second") is a rule and its exception
    genuinely severed by a boundary. `neighbour_only_ids` is returned so that
    reading is repeatable rather than asserted.
    """
    rows = rows if rows is not None else load_clauses()
    fidelity = fidelity if fidelity is not None else load_fidelity()
    pat = _exception_re()
    by_id = {r["id"]: r for r in rows}
    own_ids, nbr_ids, none_ids = [], [], []
    for cid in sorted(fidelity):
        clause = by_id.get(cid)
        if clause is None or (kind is not None and clause.get("kind") != kind):
            continue
        text = inventory._norm(clause.get("quote") or "")
        if pat.search(text):
            own_ids.append(cid)
            continue
        nbrs = [n for n in neighbours(rows, cid, window)
                if pat.search(inventory._norm(n.get("quote") or ""))]
        (nbr_ids if nbrs else none_ids).append(cid)
    return {
        "clauses": len(own_ids) + len(nbr_ids) + len(none_ids),
        "own_exception": len(own_ids),
        "neighbour_only_exception": len(nbr_ids),
        "no_exception": len(none_ids),
        "own_exception_ids": own_ids,
        "neighbour_only_ids": nbr_ids,
    }


def corrected_share(records=None) -> dict:
    """The segmentation share after pushing the hand-check's observed
    resolution of `unlocated` through the whole population.

    A point estimate on a small sample; the band from `summarize` remains the
    thing to quote when only one number is wanted.
    """
    records = records if records is not None else attribute_all()
    rep = hand_check_report(records)
    conf = rep["confusion"]
    unloc_n = sum(conf["unlocated"].values())
    seg_rate = (conf["unlocated"]["segmentation"] / unloc_n) if unloc_n else 0.0
    s = summarize(records)
    n = s["total"] or 1
    confirmed, unloc = s["counts"]["segmentation"], s["counts"]["unlocated"]
    est = (confirmed + seg_rate * unloc) / n
    lo, hi = wilson(conf["unlocated"]["segmentation"], unloc_n)
    return {
        "unlocated_sampled": unloc_n,
        "unlocated_segmentation_rate": seg_rate,
        "point_estimate": est,
        "ci_low": (confirmed + lo * unloc) / n,
        "ci_high": (confirmed + hi * unloc) / n,
        "band_low": s["segmentation_share_low"],
        "band_high": s["segmentation_share_high"],
    }


# --------------------------------------------------------------------------
# report

def report(rows=None, fidelity=None) -> dict:
    """Everything Step 2 measured, in one JSON-serialisable dict."""
    rows = rows if rows is not None else load_clauses()
    fidelity = fidelity if fidelity is not None else load_fidelity()
    records = attribute_all(rows, fidelity)
    summary = summarize(records)

    flags = structural_flags(rows)
    kind_of = {r["id"]: r["kind"] for r in rows}
    struct = defaultdict(Counter)
    for cid in sorted(fidelity):
        f = flags.get(cid, {})
        k = kind_of.get(cid)
        struct[k]["clauses"] += 1
        for name, hit in f.items():
            struct[k][name] += bool(hit)
        struct[k]["any"] += any(f.values())

    sensitivity = {}
    for tau in (0.5, 0.6, 0.7, 0.8, 0.9, 1.0):
        s = summarize(attribute_all(rows, fidelity, tau=tau))
        sensitivity[str(tau)] = s["counts"]

    window_sensitivity = {}
    for w in (1, 2, 4):
        s = summarize(attribute_all(rows, fidelity, window=w))
        window_sensitivity[str(w)] = s["counts"]["segmentation"]

    return {
        "clauses_scored": len(fidelity),
        "missing_phrases": len(records),
        "tau": TAU,
        "window": WINDOW,
        "counts": summary["counts"],
        "segmentation_share_low": summary["segmentation_share_low"],
        "segmentation_share_high": summary["segmentation_share_high"],
        "per_kind": summary["per_kind"],
        "tau_sensitivity": sensitivity,
        "window_sensitivity": window_sensitivity,
        "structural": {k: dict(v) for k, v in sorted(struct.items())},
        "atom_spans": {k: v for k, v in span_containment(rows).items()
                       if k != "offenders"},
        "hand_check": hand_check_report(records),
        "corrected": corrected_share(records),
        "exception_locality": {
            k: exception_locality(rows, fidelity, kind=k)
            for k in sorted({r["kind"] for r in records})
        },
    }


def worksheet(n: int = 45, seed: int = 20260802) -> str:
    """The hand-adjudication worksheet: sampled phrase, its clause, its
    neighbours. Printed by `--worksheet` so the `HAND_CHECK` labels are
    reproducible by anyone who wants to re-adjudicate them."""
    rows = load_clauses()
    by_id = {r["id"]: r for r in rows}
    lines = []
    for rec in sample(attribute_all(rows), n, seed):
        cid = rec["clause_id"]
        lines.append("=" * 72)
        lines.append(f'{phrase_key(cid, rec["phrase"])}  '
                     f'[lexical={rec["verdict"]} own={rec["coverage_own"]} '
                     f'nbr={rec["coverage_neighbour"]}]')
        lines.append(f'  OWN  {cid}: {by_id[cid]["quote"][:500]}')
        for nb in neighbours(rows, cid):
            lines.append(f'  NBR  {nb["id"]}: {nb["quote"][:250]}')
    return "\n".join(lines)


def main(argv=None):
    import sys

    argv = list(sys.argv[1:] if argv is None else argv)
    if "--worksheet" in argv:
        print(worksheet())
        return 0
    print(json.dumps(report(), indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
