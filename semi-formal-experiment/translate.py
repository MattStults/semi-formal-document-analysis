"""Translation layer: the two profiles over the shared checker.

  clause->rule           (construction side)
  behavior->derived pred (query side)

Both build a prompt from the SAME skeleton: compact DSL reference card +
vocabulary slice + task-specific template, expect strict JSON back, validate
with the checker, and drive a bounded repair loop on failure. Design points
from the NL->ASP literature: keep the reference card COMPACT (verbose docs
degrade translation), and feed structured checker feedback into repairs
rather than free-form retries.
"""
from __future__ import annotations

import json

from dsl import DerivedPredicate, Rule, Vocabulary
from checker import check_definition, check_rule

MAX_REPAIR_ROUNDS = 3

REFERENCE_CARD = """You translate natural language into a small semi-formal DSL.
Output STRICT JSON only, no prose.

Atoms are typed: kind=context (a feature of the situation) or kind=act (a thing
the model does). Use ONLY atoms from the vocabulary slice below. If a needed
distinction has no atom, DO NOT invent one inline — put it in "escalations"
with the exact source text span that needs it.

Expressions: an atom name, {"all": [...]}, {"any": [...]}, or {"not": ...}.
"""

RULE_TEMPLATE = """Task: encode ONE spec clause as a defeasible rule.
Output JSON: {"id": str, "modality": "oblige|forbid|permit", "act": atom,
"conditions": [context atoms], "defeaters": [{"conditions": [...], "source": str}],
"tier": int, "quote": exact source sentence, "escalations": [{"kind": "atom|axiom",
"proposal": str, "span": str}]}

Modality discipline: weighing language ("give weight to", "attend to") is NOT an
obligation — use "permit", or escalate if no faithful encoding exists.
Defeater discipline: a defeater must fire on conditions BEYOND the rule's own
trigger, otherwise the rule is dead code.

Clause locator: {locator}
Clause text: {clause}
Surrounding section text: {section}
"""

BEHAVIOR_TEMPLATE = """Task: define ONE behavior as a derived predicate.
Output JSON: {"name": str, "concept_map": {concept: atom-or-null},
"expr": expression, "escalations": [{"kind": "atom", "proposal": str, "span": str}]}

Decompose the behavior into the SCENARIO CONDITIONS and ACTS it concerns —
the situations in which it applies and what the model does. Ignore rhetorical
or motivational framing ("a real cost", "safe default", "genuinely"): those
are not conditions and should not become concepts.

For each concept, before deciding it is unmappable, check whether it is a
COMPOSITION of existing atoms. Example: "tells the user what they want to hear
though it is false" is not a missing atom — it is user_prefers_p AND bel_false.
Decompose such a concept into sub-concepts that each map to a single atom, and
combine them in "expr" with all/any/not. Only null a concept (and escalate a
proposed atom) when NO combination of existing atoms captures the distinction.
An honest null beats a loose mapping; a needless new atom beats nothing.

Behavior name: {name}
Behavior definition: {definition}
"""


def vocabulary_slice(vocab: Vocabulary, max_atoms=None):
    """Render the vocabulary (or a slice) for the prompt. For large
    vocabularies, callers pass a relevance-filtered subset (the 'ontology
    snippet' pattern)."""
    lines = []
    atoms = list(vocab.atoms.values())[:max_atoms]
    for a in atoms:
        lines.append(f"- {a.name} [{a.kind}/{a.dimension}]: {a.gloss}")
    if vocab.axioms:
        lines.append("Axioms:")
        for ax in vocab.axioms:
            lines.append(f"- {ax.kind}({', '.join(ax.atoms)}) [{ax.license}]")
    return "\n".join(lines)


def _parse_json(text):
    if text is None:
        return None, "no response (dry run)"
    try:
        start = text.index("{")
        end = text.rindex("}") + 1
        return json.loads(text[start:end]), None
    except (ValueError, json.JSONDecodeError) as e:
        return None, f"unparseable JSON: {e}"


class TranslationResult:
    def __init__(self, obj=None, verdict=None, escalations=None,
                 rounds=0, dry_run=False, error=None):
        self.obj = obj
        self.verdict = verdict
        self.escalations = escalations or []
        self.rounds = rounds
        self.dry_run = dry_run
        self.error = error


def translate_behavior(client, vocab: Vocabulary, name, definition) -> TranslationResult:
    system = REFERENCE_CARD + "\nVocabulary:\n" + vocabulary_slice(vocab)
    user = BEHAVIOR_TEMPLATE.replace("{name}", name).replace("{definition}", definition)
    feedback = ""
    for round_ in range(1, MAX_REPAIR_ROUNDS + 1):
        text = client.complete(system, user + feedback)
        if text is None:
            return TranslationResult(dry_run=True, rounds=round_)
        data, err = _parse_json(text)
        if err:
            feedback = f"\n\nYour previous output failed: {err}. Emit strict JSON only."
            continue
        defn = DerivedPredicate(
            name=data.get("name", name),
            expr=data.get("expr"),
            concept_map=data.get("concept_map", {}))
        verdict = check_definition(defn, vocab)
        escal = data.get("escalations", [])
        if verdict.ok or verdict.stage == "existence":
            # existence failures with honest nulls are a RESULT (inexpressibility),
            # not a repair target — return them as-is
            return TranslationResult(defn, verdict, escal, round_)
        feedback = ("\n\nYour previous output failed validation: "
                    + "; ".join(verdict.errors) + ". Fix and re-emit.")
    return TranslationResult(defn, verdict, escal, MAX_REPAIR_ROUNDS,
                             error="repair rounds exhausted")


def translate_clause(client, vocab: Vocabulary, clause_id, locator,
                     clause_text, section_text="") -> TranslationResult:
    system = REFERENCE_CARD + "\nVocabulary:\n" + vocabulary_slice(vocab)
    user = (RULE_TEMPLATE.replace("{locator}", locator)
            .replace("{clause}", clause_text)
            .replace("{section}", section_text))
    feedback = ""
    for round_ in range(1, MAX_REPAIR_ROUNDS + 1):
        text = client.complete(system, user + feedback)
        if text is None:
            return TranslationResult(dry_run=True, rounds=round_)
        data, err = _parse_json(text)
        if err:
            feedback = f"\n\nYour previous output failed: {err}. Emit strict JSON only."
            continue
        rule = Rule(
            id=data.get("id", clause_id), modality=data.get("modality", ""),
            act=data.get("act", ""), conditions=data.get("conditions", []),
            defeaters=data.get("defeaters", []), tier=data.get("tier", 4),
            locator=locator, quote=data.get("quote", ""))
        verdict = check_rule(rule, vocab)
        escal = data.get("escalations", [])
        if verdict.ok:
            return TranslationResult(rule, verdict, escal, round_)
        feedback = ("\n\nYour previous output failed validation: "
                    + "; ".join(verdict.errors) + ". Fix and re-emit.")
    return TranslationResult(rule, verdict, escal, MAX_REPAIR_ROUNDS,
                             error="repair rounds exhausted")
