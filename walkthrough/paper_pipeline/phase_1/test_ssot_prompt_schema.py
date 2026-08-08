"""One field, one description. The prompt may POINT at a field; it may not restate it.

WHY THIS EXISTS. `schema.json_schema()` is sent to the model inside
`response_format`, so every `description` in it already reaches the model. A
sentence about a field that also sits in `prompt/*.md` is therefore a SECOND
COPY of something the model was already told — and two copies of one rule drift.
The drift is silent: both texts read fine, and nothing anywhere reports that they
have stopped agreeing.

⚠️ THIS IS A SINGLE-SOURCE-OF-TRUTH CHECK, NOT A QUALITY CHECK. It is NOT
claimed to reduce translation errors. Measured evidence on this pipeline points
the other way: a prose prohibition plus schema error text left 59 occurrences of
the defect it named, and one worked example took the same cause to zero. Moving
text between two channels the model already reads is bookkeeping. What it buys
is that there is one place to edit.

WHAT IS AND IS NOT DUPLICATION.

* A POINTER is fine — *"which of the three readings each value stands for is on
  the `closure` field itself"* names the field and copies none of its words.
* A CROSS-FIELD INVARIANT is fine and has nowhere else to live. `asserts` ↔
  `acts` ↔ `closure`; `licence` ↔ `cites` ↔ `inference` ↔ `toggleable`;
  `read_back` ↔ `read_back_slots`; `outcome` ↔ `abstain_reason` ↔ every other
  list being empty. No single field's description can carry a rule about two
  fields, so these stay in the prompt by design.
* A RESTATEMENT is the defect: the prompt saying, in the schema's own words,
  what one field is.

HOW IT DECIDES. Word n-grams, n = _N. Both sides are lowercased and stripped to
alphanumerics first, so markdown emphasis, backticks and the em-dashes this
project writes everywhere cannot hide a copy. A shared run of _N content words
is not something two independently written sentences do.

⚠️ _N IS 6 AND WAS CHOSEN AGAINST THE ARTIFACT, NOT GUESSED. At 5 the check
fires on *"cannot be told apart from"* — a house idiom that appears in this
repo's prose the way "on the other hand" appears in anyone's, and which carries
no field documentation at all. Lowering it re-introduces that false positive.

⛔ PER `DEBUGGING_TIPS.md` ENTRY 9, NOTHING HERE PINS TODAY'S CONTENT. No prompt
sentence, no description, no byte count and no description count is written
down. An ordinary edit to either side must not be reported as a defect; only a
copy between them is.

⛔ PER ENTRY 8, THIS MUST NOT PASS VACUOUSLY. Three separate guards:
`test_the_detector_actually_detects` proves the comparison fires on a planted
copy, `test_there_is_something_to_compare` proves both sides are non-empty, and
`test_every_prompt_file_is_classified` proves no prompt file escapes by not
being listed.
"""

import json
import os
import re
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import schema as S  # noqa: E402

PROMPT_DIR = os.path.join(HERE, "prompt")

#: Word n-gram length. See the module docstring for why it is 6.
_N = 6

#: Prompt files whose field-level documentation has been migrated into
#: `schema.py`. Adding a file here is the whole of "this file is now SSOT".
ENFORCED = {
    "10_output_format.md",
}

#: Prompt files NOT yet migrated, each with the reason. ⚠️ This is recorded
#: DEBT, deliberately visible rather than a silent gap in the check. Every one
#: of these is a watched transcription (`walkthrough/model/guard.py`), so
#: migrating one is a reviewed prompt change and not a documentation edit.
PENDING = {
    "00_task.md":
        "restates the `inference` and `beats.body` field descriptions inside "
        "its licence overview; that overview is also the design's own framing "
        "and rewriting it is a prompt change needing its own review",
    "20_worked_example.md":
        "its examples quote corpus text that the `asserts` and `defines` type "
        "docstrings also quote; the overlap is shared SOURCE material, not a "
        "duplicated description, and untangling it is a separate call",
    "30_failure_modes.md":
        "restates the `forbid_body` docstring's example. The failure-mode list "
        "is transcribed from the design and diverging from it here would break "
        "a different single source of truth",
}


def _norm(text):
    """Lowercase, strip to alphanumeric words. Markdown hides nothing."""
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).split()


def _grams(text, n=_N):
    w = _norm(text)
    return [tuple(w[i:i + n]) for i in range(len(w) - n + 1)]


def _schema_descriptions():
    """Every `description` the wire schema sends, with where it sits.

    Taken from `json_schema()` rather than from the source, because that is
    exactly the text the model receives: field descriptions AND the type
    docstrings pydantic promotes to object descriptions.
    """
    out = []

    def walk(node, path):
        if isinstance(node, dict):
            d = node.get("description")
            if isinstance(d, str) and d.strip():
                out.append((path or "<root>", d))
            for k, v in node.items():
                walk(v, f"{path}.{k}" if path else k)
        elif isinstance(node, list):
            for i, v in enumerate(node):
                walk(v, f"{path}[{i}]")

    walk(S.json_schema(), "")
    return out


def _prompt_files():
    return sorted(f for f in os.listdir(PROMPT_DIR) if f.endswith(".md"))


def _restatements(prompt_text, descriptions):
    """[(where, description, the shared run of words)] — empty when SSOT holds."""
    have = set(_grams(prompt_text))
    hits = []
    for where, desc in descriptions:
        shared = [g for g in _grams(desc) if g in have]
        if shared:
            hits.append((where, desc, " ".join(shared[0])))
    return hits


# ==========================================================================
#  The guards that keep the check from passing when it did not run
# ==========================================================================

def test_there_is_something_to_compare():
    """An empty description set or an empty prompt passes every loop below."""
    descs = _schema_descriptions()
    assert descs, "the wire schema carries no descriptions — nothing to compare"
    assert any(_grams(d) for _, d in descs), (
        f"no schema description is as long as {_N} words, so no comparison can "
        f"ever fire and this whole file is decorative")
    for name in sorted(ENFORCED):
        text = open(os.path.join(PROMPT_DIR, name), encoding="utf-8").read()
        assert _grams(text), f"{name} is empty or too short to compare"


def test_the_detector_actually_detects():
    """RED on demand: plant a copy of a real description and it must be found.

    Content-independent — it copies whatever the schema says today, so an edit
    to the schema cannot turn this into a test of a sentence that is gone.
    """
    descs = [(w, d) for w, d in _schema_descriptions() if _grams(d)]
    where, desc = descs[0]
    planted = f"# not a real prompt\n\nSome preamble. {desc} Some more prose.\n"
    hits = _restatements(planted, descs)
    assert hits, (
        f"a verbatim copy of the description at {where} was NOT detected. The "
        f"comparison is broken and every SSOT assertion below is vacuous")


def test_every_prompt_file_is_classified():
    """A new prompt file must be enforced or excused BY NAME.

    Without this, adding `40_whatever.md` silently opts out of the check —
    which is how a check quietly stops covering the thing it was written for.
    """
    on_disk = set(_prompt_files())
    listed = ENFORCED | set(PENDING)
    assert on_disk, f"no prompt files found in {PROMPT_DIR}"
    unclassified = sorted(on_disk - listed)
    assert not unclassified, (
        f"prompt file(s) {unclassified} are in neither ENFORCED nor PENDING. "
        f"Add to ENFORCED, or to PENDING with the reason it is not ready")
    vanished = sorted(listed - on_disk)
    assert not vanished, (
        f"{vanished} are listed here but no longer exist; the list is stale "
        f"and a stale list is how a file gets excused that nobody excused")


def test_enforced_and_pending_do_not_overlap():
    both = ENFORCED & set(PENDING)
    assert not both, f"{sorted(both)} is both enforced and excused"


# ==========================================================================
#  The invariant itself
# ==========================================================================

@pytest.mark.parametrize("name", sorted(ENFORCED))
def test_prompt_does_not_restate_the_schema(name):
    text = open(os.path.join(PROMPT_DIR, name), encoding="utf-8").read()
    hits = _restatements(text, _schema_descriptions())
    assert not hits, "\n".join(
        [f"{name} restates {len(hits)} schema description(s). Each field is "
         f"documented in ONE place: delete the prompt copy and leave a pointer, "
         f"or move the sentence out of the schema. Do not edit one to match the "
         f"other — that is two copies again."]
        + [f"  · {where}\n      schema : {desc[:150]}\n      shared : {run}"
           for where, desc, run in hits])


def test_the_pending_list_carries_a_reason():
    for name, why in PENDING.items():
        assert why and why.strip(), (
            f"{name} is excused with no reason. An unexplained exemption is "
            f"indistinguishable from an oversight")


# ==========================================================================
#  The other half of SSOT: the schema really is reaching the model
# ==========================================================================

def test_the_descriptions_are_actually_sent():
    """Moving documentation into the schema only helps if the schema is sent.

    If `response_format` ever stops carrying the descriptions, this file's
    whole premise is false and the prompt was emptied for nothing.
    """
    blob = json.dumps(S.response_format())
    descs = _schema_descriptions()
    assert descs, "no descriptions to look for"
    missing = [w for w, d in descs if json.dumps(d)[1:-1] not in blob]
    assert not missing, (
        f"{len(missing)} description(s) are in the schema but not in what is "
        f"sent to the model, e.g. {missing[:3]}")
