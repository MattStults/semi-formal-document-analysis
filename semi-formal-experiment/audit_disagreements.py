"""The DISAGREEMENT-AUDIT instrument: dossiers + cause taxonomy + validator.

PANEL-READING, DIAGNOSTIC-ONLY — in the anti-cheat FORBIDDEN set, exactly like
its sibling `diagnose_disagreement`. That module dumps ONE hand-picked case
for a human; this one scales the same autopsy to EVERY tool-vs-panel
disagreement in the survey, computing per dossier the mechanical facts a
small model needs to attribute a CAUSE from the closed taxonomy below. Two
disagreements were debugged by hand (DISAGREEMENT_REPORT.md,
DISAGREEMENT_REPORT_ext_v1.md); ~294 exist under the current configuration.
Cause-auditing them one transcript at a time does not scale; a budgeted
small-model seat over deterministic dossiers does (the house pattern:
select_audit.py + briefs/select_audit.md; seat brief:
briefs/disagreement_autopsy.md).

Sandwich (REPRODUCIBILITY.md):
  deterministic core   `dossiers` — byte-reproducible dossier set + index
  judgment interface   briefs/disagreement_autopsy.md — dossier in, verdict out
  mechanical validator `validate` — coverage, closed vocabularies, and
                       dossier-consistency spot rules
  instructions in-repo the brief itself

THE FENCE IS DISCLOSURE, NOT BLINDNESS. This seat sees panel verdicts by
design — cause attribution needs to know what the judges said. Invariant 9
(contract §5) bars FITTING, not measuring: nothing produced here may edit a
vocabulary, a query, a weight or a threshold directly. Findings route through
the iteration loop's label-free instruments. A query module importing this
one would hold per-passage gold verdicts and per-clause tool scores side by
side — the single most launderable pairing — so `audit_disagreements` is a
FORBIDDEN token in test_no_reference_leak.py.

Determinism: dossier JSON is sorted-key, floats rounded to 6 dp, no wall
clock; same inputs give the same bytes.
"""
from __future__ import annotations

import argparse
import json
import os
import re

import grammar

HERE = os.path.dirname(os.path.abspath(__file__))

#: Current configuration (the survey this instrument audits).
ANNOTATIONS = os.path.join(HERE, "annotations_ext_v1_merged.json")
BEHAVIOUR_ATOMS = os.path.join(HERE, "behavior_atoms_audit_v1.json")
OUT_ROOT = os.path.join(HERE, "audit_dossiers")

#: A passage joined to MORE than this many clauses is a degenerate join
#: (quote-containment fan-out): the ext_v1 FP case mapped a header-only quote
#: to 28 clauses and inherited another clause's score. 5 is the working line
#: between "a paragraph holds several provisions" (legitimate) and "the quote
#: matches half a section" (join artifact).
FANOUT_DEGENERATE = 5

#: |distance_to_cut| within which a threshold-family cause is plausible: the
#: clause's match did not fail, the derived cut just fell on the other side.
#: A miss 0.5 below the cut is a matching failure, not a calibration one.
NEAR_CUT_MARGIN = 0.10

SIDES = ("tool", "panel", "both_defensible")

#: THE CLOSED CAUSE TAXONOMY. Sources: the two hand-debugged generations
#: (DISAGREEMENT_REPORT.md — naming/patient defects; _ext_v1 — selection gap,
#: join artifact) plus the mechanically distinguishable neighbours of each.
#: `signature` states the mechanical facts a dossier must show for the cause
#: to be attributable; the validator enforces the checkable ones.
CAUSE_TAXONOMY = {
    "fn_family_absent_from_vocabulary": {
        "kind": "FN",
        "definition": "The concept the panel matched on has NO atom family in "
                      "the clause-side vocabulary at all — no annotation "
                      "could have carried the match; the defect is upstream "
                      "of both selection and matching.",
        "signature": "atom_channel_zero; exact_name_intersection empty; "
                     "stem_family_adjacency empty (a nonempty adjacency "
                     "proves a family member exists in the vocabulary, "
                     "refuting this cause).",
    },
    "fn_family_unselected": {
        "kind": "FN",
        "definition": "The vocabulary HAS the relevant atom family but the "
                      "behaviour's query selection never reached for it — "
                      "the ext_v1 FN: a manipulation family on the clause "
                      "side, zero manipulation atoms among the query's "
                      "selection (selection-recall failure).",
        "signature": "nonempty stem_family_adjacency, OR sweep-core evidence "
                     "(a select_audit score-3 in_scope_unselected finding "
                     "naming the family) carried in the verdict's "
                     "sweep_core_evidence field.",
    },
    "fn_names_cannot_meet": {
        "kind": "FN",
        "definition": "Query and clause both hold atoms for the concept but "
                      "under different names (a coined compound vs a generic "
                      "sibling, or synonyms) — exact-name intersection has "
                      "no way to connect them; the b8 FN "
                      "(targeted_political_manipulation vs "
                      "psychological_manipulation).",
        "signature": "atom_channel_zero; exact_name_intersection empty; "
                     "typically nonempty stem_family_adjacency.",
    },
    "fn_kind_or_patient_discount": {
        "kind": "FN",
        "definition": "Names DO meet but the match under-scores: kind "
                      "disagreement discounts it, the matched atoms are "
                      "stopworded/low-IDF, or the patient/principal facts "
                      "the panel keyed on are unrepresented so the match "
                      "stays weak.",
        "signature": "nonempty exact_name_intersection with the total still "
                     "below the cut.",
    },
    "fn_threshold": {
        "kind": "FN",
        "definition": "The match is real and scored; the label-free cut "
                      "landed just above it. A calibration miss, not a "
                      "matching one.",
        "signature": "|distance_to_cut| <= NEAR_CUT_MARGIN.",
    },
    "fp_promiscuous_atom": {
        "kind": "FP",
        "definition": "Patient-free / stock atoms (human_safety, "
                      "safe_completion...) fired on a clause about a "
                      "different party or subject — the b8 FP: three "
                      "generic atoms matched while the one discriminating "
                      "atom could not exert negative influence.",
        "signature": "nonempty exact_name_intersection carrying most of the "
                     "score on a clause the panel scored low.",
    },
    "fp_section_prior": {
        "kind": "FP",
        "definition": "The clause scores mainly by inheriting its section's "
                      "best local score — neighbourhood, not content.",
        "signature": "section is the dominant channel share of the "
                     "max-scoring clause.",
    },
    "fp_lexical_only": {
        "kind": "FP",
        "definition": "No atom matched at all; the score is lexical overlap "
                      "(plus crumbs) — shared vocabulary without shared "
                      "concept.",
        "signature": "atom_channel_zero; lex share >= section share.",
    },
    "fp_join_artifact": {
        "kind": "FP",
        "definition": "The quote-containment join mapped a degenerate quote "
                      "to many clauses and passage-level max attributed "
                      "another clause's score to this passage — the ext_v1 "
                      "FP ('!!! meta \"Commentary\"' -> 28 clauses). The "
                      "tool never claimed this passage was relevant.",
        "signature": "join_fanout > FANOUT_DEGENERATE (dossier flags it "
                     "degenerate, with the quote length).",
    },
    "fp_threshold_drift": {
        "kind": "FP",
        "definition": "A weak, honest score that the derived cut happened to "
                      "admit; just above the line, not a confident match.",
        "signature": "|distance_to_cut| <= NEAR_CUT_MARGIN.",
    },
    "boundary_dispute_tool_defensible": {
        "kind": "either",
        "definition": "Genuine relevance-boundary judgment call; on the "
                      "auditor-need standard (briefs/flip_adjudicator.md) "
                      "the TOOL's side is the defensible reading.",
        "signature": "no mechanical defect; side must be 'tool'.",
    },
    "boundary_dispute_panel_defensible": {
        "kind": "either",
        "definition": "Genuine relevance-boundary judgment call; the PANEL's "
                      "side is the defensible reading.",
        "signature": "no mechanical defect; side must be 'panel'.",
    },
    "unexplained_escalate": {
        "kind": "either",
        "definition": "The dossier's facts fit no cause above. NEVER "
                      "force-fit: escalate with a note saying what was "
                      "observed. Unmapped passages (join_fanout 0 — a "
                      "segmentation-coverage gap, outside this taxonomy) "
                      "always land here.",
        "signature": "required nonempty note; the only admissible cause for "
                     "an unmapped dossier.",
    },
}


# ------------------------------------------------------------ discriminators

def _singular(tok: str) -> str:
    """head_induction_probe.py's convention, verbatim: trailing 's' dropped
    on tokens longer than 3 chars, double-s kept."""
    if len(tok) > 3 and tok.endswith("s") and not tok.endswith("ss"):
        return tok[:-1]
    return tok


def head_of(name: str) -> str:
    """The candidate hypernym head of an atom name.

    English compounds are mostly right-headed ("targeted_political_
    manipulation" is a kind of manipulation) — head_induction_probe.py's
    convention: last underscore token, singularized. Applied AFTER
    `grammar.stem_of`, so polarity prefixes and principal chains never
    masquerade as heads (`mustnot_x__model_user` heads on x's last token,
    not on "user").
    """
    stem = grammar.stem_of(name)
    return _singular(stem.rsplit("_", 1)[-1])


def stem_family_adjacency(query_atoms, clause_atoms) -> list:
    """Query atoms sharing a stem head with a DIFFERENTLY-NAMED clause atom.

    Exact name matches are excluded — they belong to exact_name_intersection;
    adjacency exists to show family-but-not-exact pairs (the naming-
    granularity defect the b8 FN report identified). Sorted, deterministic.
    """
    out = []
    cheads = {}
    for c in clause_atoms:
        cheads.setdefault(head_of(c["name"]), set()).add(c["name"])
    for q in sorted({a["name"] for a in query_atoms}):
        for cname in sorted(cheads.get(head_of(q), set()) - {q}):
            out.append({"query_atom": q, "clause_atom": cname,
                        "shared_head": head_of(q)})
    return out


def join_fanout(n_mapped: int, passage_quote: str) -> dict:
    """Fan-out of the quote-containment join for one passage, with the
    degenerate flag (> FANOUT_DEGENERATE) and the quote length that usually
    explains it (short/header-only quotes match everywhere)."""
    return {"n_mapped_clauses": int(n_mapped),
            "degenerate": n_mapped > FANOUT_DEGENERATE,
            "quote_len": len(passage_quote or "")}


def discriminators(query_atoms, clause_atoms, explain, n_mapped,
                   quote, cut, max_norm) -> dict:
    """Every computed fact the cause attribution needs, for the max-scoring
    clause of one disagreement. `explain` is relevance.explain()'s dict (or
    the same keys); `max_norm` the max normalized score over mapped clauses;
    `cut` the behaviour's derived operating point."""
    qnames = {a["name"] for a in query_atoms}
    cnames = {a["name"] for a in clause_atoms}
    channels = explain.get("channels") or {}
    return {
        "atom_channel_zero": not channels.get("atom", 0.0),
        "exact_name_intersection": sorted(qnames & cnames),
        "stem_family_adjacency": stem_family_adjacency(query_atoms,
                                                       clause_atoms),
        "join_fanout": join_fanout(n_mapped, quote),
        "distance_to_cut": round(max_norm - cut, 6),
        "channel_shares": {k: round(v, 6) for k, v in
                           sorted((explain.get("channel_share") or {}).items())},
    }


# --------------------------------------------------------------- generation

def _sanitize(pid: str) -> str:
    return re.sub(r"[^A-Za-z0-9_-]+", "_", pid).strip("_")


def config_tag(annotations_path: str, atoms_path: str) -> str:
    a = os.path.basename(annotations_path).removesuffix(".json")
    b = os.path.basename(atoms_path).removesuffix(".json")
    return (a.removeprefix("annotations_") + "__"
            + b.removeprefix("behavior_atoms_"))


def _round(x: float) -> float:
    return round(float(x), 6)


def config_identity(annotations_path: str, atoms_path: str,
                    overlay_path: str | None = None,
                    thresholds_path: str | None = None,
                    join_version: int | None = None) -> dict:
    """The census's FULL config identity (amendment F2 / TOOLING item 1),
    in snapshot.py's exact key shape: every input as {path, sha256},
    explicit nulls for absent overlay/thresholds, the threshold rule, and
    pricing_version only when an overlay is active (containment's rules
    scored the census). `join_version` records which join scored THIS census
    run (F12: join identity belongs to the CENSUS, not the snapshot). The
    v2 join now exists (inventory.match_passage_v2, JOIN_INTEGRITY_DESIGN);
    the default stays None because the shipped census predates the versioned
    join — the S8 checkpoint census passes its version explicitly.
    """
    import snapshot
    import threshold as T

    def rec(p):
        return ({"path": os.path.basename(p),
                 "sha256": snapshot._sha256_file(p)} if p else None)

    ident = {
        "record": "config_identity",
        "config_tag": config_tag(annotations_path, atoms_path),
        "inputs": {
            "annotations": rec(annotations_path),
            "behaviour_atoms": rec(atoms_path),
            "overlay": rec(overlay_path),
            "thresholds": rec(thresholds_path),
        },
        "threshold_rule": T.PREFERRED,
        "join_version": join_version,
    }
    if overlay_path:
        import containment
        ident["pricing_version"] = containment.PRICING_VERSION
    return ident


def _cut_for(index, behaviour) -> float:
    """EXACTLY relevance.predict's label-free derivation (Otsu over this
    query's own positive normalized scores)."""
    import threshold as T
    vals = [s for _, s in index.rank(behaviour) if s > 0]
    return T.apply_rule(T.PREFERRED, vals) if vals else 0.0


def generate_dossiers(index, behaviours, panel, clauses, clause_atoms,
                      out_dir, config_tag: str, header: dict | None = None,
                      frozen_cuts: dict | None = None) -> list:
    """One AUDIT DOSSIER per survey disagreement, plus index.jsonl.

    `clause_atoms` is the raw per-clause atom map (name/kind/gloss/role —
    relevance's loader drops `role`, so the caller passes the artifact's own
    by_clause map). Returns the index records, sorted by dossier_id.
    Byte-deterministic: sorted keys, rounded floats, no wall clock.

    `header` (item 0c) is the config-identity record written as the FIRST
    line of index.jsonl — the CLI always passes one (`config_identity`);
    `validate` refuses a headerless directory. `frozen_cuts` mirrors
    snapshot.py's --thresholds: a behaviour named in it takes its cut FROM
    the artifact (dossier records cut_source "frozen_artifact"), one absent
    falls back to `_cut_for` ("rule_fallback"); when None the old shape is
    preserved exactly (no cut_source key).
    """
    import diagnose_disagreement as DD

    os.makedirs(out_dir, exist_ok=True)
    clause_text = {str(c.get("id")): c.get("quote") or c.get("text", "")
                   for c in clauses}
    rows = DD.survey(index, behaviours, panel, clauses)

    # Per-behaviour caches: the passage map, the score vectors and the cut
    # are functions of the behaviour alone, and recomputing the join per
    # dossier is O(passages x clauses) — measured minutes over the real set.
    _pmaps, _raws, _norms, _cuts = {}, {}, {}, {}

    _cut_sources = {}

    def _for(slug):
        if slug not in _pmaps:
            beh = behaviours[slug]
            _pmaps[slug] = DD.passage_map(panel[slug], clauses)
            _raws[slug] = index.raw_scores(beh)
            _norms[slug] = dict(index.rank(beh))
            if frozen_cuts is not None and slug in frozen_cuts:
                _cuts[slug] = float(frozen_cuts[slug])
                _cut_sources[slug] = "frozen_artifact"
            else:
                _cuts[slug] = _cut_for(index, beh)
                if frozen_cuts is not None:
                    _cut_sources[slug] = "rule_fallback"
        return _pmaps[slug], _raws[slug], _norms[slug], _cuts[slug]

    records = []
    seen = set()
    for r in sorted(rows, key=lambda r: (r["behaviour"], r["pid"])):
        slug, pid = r["behaviour"], r["pid"]
        beh = behaviours[slug]
        pmaps, raw, norm, cut = _for(slug)
        pmap = pmaps[pid]

        cids = pmap["clause_ids"]
        mapped = [{"clause_id": c, "raw": _round(raw.get(c, 0.0)),
                   "norm": _round(norm.get(c, 0.0))} for c in sorted(cids)]

        qatoms = [{"name": a["name"], "kind": a["kind"], "gloss": a["gloss"]}
                  for a in beh.norm_atoms]
        qatoms.sort(key=lambda a: a["name"])

        if cids:
            best = sorted(cids, key=lambda c: (-norm.get(c, 0.0), c))[0]
            ex = index.explain(beh, best)
            catoms = [{"name": a.get("name", ""), "kind": a.get("kind", ""),
                       "gloss": a.get("gloss", ""), "role": a.get("role", "")}
                      for a in clause_atoms.get(best, [])]
            catoms.sort(key=lambda a: (a["name"], a["kind"]))
            max_clause = {
                "clause_id": best,
                "raw": _round(raw.get(best, 0.0)),
                "norm": _round(norm.get(best, 0.0)),
                "text": clause_text.get(best, ""),
                "atoms": catoms,
                "explain": {
                    "locator": ex.get("locator", ""),
                    "section_path": list(ex.get("section_path") or []),
                    "channels": {k: _round(v) for k, v in
                                 sorted(ex["channels"].items())},
                    "channel_share": {k: _round(v) for k, v in
                                      sorted(ex["channel_share"].items())},
                    "matched_atoms": ex["matched_atoms"],
                    "top_lexical_terms": [[t, _round(v)] for t, v in
                                          ex.get("top_lexical_terms", [])],
                    "atom_channel_live": ex.get("atom_channel_live"),
                },
            }
            disc = discriminators(qatoms, catoms, ex, len(cids),
                                  pmap["quote"], cut,
                                  norm.get(best, 0.0))
        else:
            max_clause = None
            disc = {
                "atom_channel_zero": True,
                "exact_name_intersection": [],
                "stem_family_adjacency": [],
                "join_fanout": join_fanout(0, pmap["quote"]),
                "distance_to_cut": _round(0.0 - cut),
                "channel_shares": {},
            }

        did = f"{slug}__{_sanitize(pid)}"
        assert did not in seen, f"dossier id collision: {did}"
        seen.add(did)

        dossier = {
            "dossier_id": did,
            "config_tag": config_tag,
            "behaviour": slug,
            "kind": r["kind"],
            "passage": {"id": pid, "quote": pmap["quote"],
                        "panel_score": pmap["score"],
                        "verdicts": pmap["verdicts"]},
            "cut": _round(cut),
            "mapped_clauses": mapped,
            "max_clause": max_clause,
            "query_atoms": qatoms,
            "discriminators": disc,
        }
        if slug in _cut_sources:
            dossier["cut_source"] = _cut_sources[slug]
        fname = did + ".json"
        with open(os.path.join(out_dir, fname), "w") as f:
            json.dump(dossier, f, indent=1, sort_keys=True)
            f.write("\n")
        records.append({"dossier_id": did, "behaviour": slug, "pid": pid,
                        "kind": r["kind"], "file": fname})

    records.sort(key=lambda r: r["dossier_id"])
    with open(os.path.join(out_dir, "index.jsonl"), "w") as f:
        if header is not None:
            f.write(json.dumps(header, sort_keys=True) + "\n")
        for rec in records:
            f.write(json.dumps(rec, sort_keys=True) + "\n")
    return records


# ---------------------------------------------------------------- validator

def _load_index(dossier_dir: str) -> tuple[dict | None, dict]:
    """(config-identity header or None, {dossier_id: record}).

    The header is the FIRST non-blank line iff it is a config_identity
    record (item 0c); dossier records follow. A headerless index parses —
    so old directories can still be read for diagnosis — but `validate`
    refuses it."""
    path = os.path.join(dossier_dir, "index.jsonl")
    header, out, first = None, {}, True
    with open(path) as f:
        for line in f:
            if not line.strip():
                continue
            r = json.loads(line)
            if first and r.get("record") == "config_identity":
                header = r
                first = False
                continue
            first = False
            out[r["dossier_id"]] = r
    return header, out


def _consistency(v, d) -> list:
    """Mechanical spot rules: does this verdict's cause fit this dossier's
    computed facts? Only checkable facts are enforced; judgment stays with
    the seat."""
    cause, side = v.get("cause"), v.get("side")
    disc = d.get("discriminators") or {}
    fan = (disc.get("join_fanout") or {}).get("n_mapped_clauses", 0)
    inter = disc.get("exact_name_intersection") or []
    adj = disc.get("stem_family_adjacency") or []
    azero = disc.get("atom_channel_zero")
    dist = disc.get("distance_to_cut", 0.0)
    shares = disc.get("channel_shares") or {}
    did = v.get("dossier_id")
    errs = []

    spec = CAUSE_TAXONOMY.get(cause) or {}
    if spec.get("kind") in ("FN", "FP") and spec["kind"] != d.get("kind"):
        errs.append(f"{did}: cause {cause} is a {spec['kind']} cause but the "
                    f"dossier kind is {d.get('kind')}")
    if fan == 0 and cause != "unexplained_escalate":
        errs.append(f"{did}: unmapped dossier (join_fanout 0) admits only "
                    f"unexplained_escalate, got {cause}")
        return errs

    if cause == "fp_join_artifact" and fan <= FANOUT_DEGENERATE:
        errs.append(f"{did}: fp_join_artifact requires join_fanout > "
                    f"{FANOUT_DEGENERATE}, dossier has {fan}")
    if cause == "fn_family_unselected" and not adj:
        sweep = v.get("sweep_core_evidence")
        if not (isinstance(sweep, list) and sweep):
            errs.append(f"{did}: fn_family_unselected requires nonempty "
                        "stem_family_adjacency or sweep_core_evidence")
    if cause == "fn_names_cannot_meet" and (not azero or inter):
        errs.append(f"{did}: fn_names_cannot_meet requires atom_channel_zero "
                    "and empty exact_name_intersection")
    if cause == "fn_family_absent_from_vocabulary" and (adj or inter):
        errs.append(f"{did}: fn_family_absent_from_vocabulary refuted — the "
                    "dossier shows a family member in the vocabulary "
                    "(adjacency/intersection nonempty)")
    if cause == "fn_kind_or_patient_discount" and not inter:
        errs.append(f"{did}: fn_kind_or_patient_discount requires a nonempty "
                    "exact_name_intersection (some name met)")
    if cause == "fp_promiscuous_atom" and not inter:
        errs.append(f"{did}: fp_promiscuous_atom requires a matched atom "
                    "(nonempty exact_name_intersection)")
    if cause in ("fn_threshold", "fp_threshold_drift") \
            and abs(dist) > NEAR_CUT_MARGIN:
        errs.append(f"{did}: {cause} requires |distance_to_cut| <= "
                    f"{NEAR_CUT_MARGIN}, dossier has {dist}")
    if cause == "fp_section_prior":
        if not shares or shares.get("section", 0.0) < max(
                shares.get("lex", 0.0), shares.get("atom", 0.0)):
            errs.append(f"{did}: fp_section_prior requires section to be the "
                        "dominant channel share")
    if cause == "fp_lexical_only":
        if not azero or shares.get("lex", 0.0) < shares.get("section", 0.0):
            errs.append(f"{did}: fp_lexical_only requires atom_channel_zero "
                        "and lex share >= section share")
    if cause == "boundary_dispute_tool_defensible" and side != "tool":
        errs.append(f"{did}: boundary_dispute_tool_defensible requires "
                    f"side 'tool', got {side!r}")
    if cause == "boundary_dispute_panel_defensible" and side != "panel":
        errs.append(f"{did}: boundary_dispute_panel_defensible requires "
                    f"side 'panel', got {side!r}")
    if cause == "unexplained_escalate" and not (v.get("note") or "").strip():
        errs.append(f"{did}: unexplained_escalate requires a nonempty note")
    return errs


def validate(verdicts, dossier_dir: str, sweep_findings: str | None = None):
    """Audit a verdict file against the dossier set. REFUSES loudly.

    `verdicts`: a path or a list of {dossier_id, cause, side, note[,
    sweep_core_evidence]}. Checks: every dossier in index.jsonl covered
    exactly once, no unknown ids, closed cause/side vocabularies, and the
    mechanical dossier-consistency rules. With `sweep_findings` (a
    select_audit findings JSON), sweep_core_evidence atoms must appear in its
    in_scope_unselected list. Returns {"ok", "violations", "n_verdicts",
    "by_cause"}.
    """
    if isinstance(verdicts, str):
        verdicts = json.load(open(verdicts))
    header, index = _load_index(dossier_dir)
    errs = []
    if header is None:
        # item 0c / amendment F2: a census without its config-identity
        # header cannot prove WHICH configuration produced it — the exact
        # gap that let a plain-index rebuild contradict frozen overlay
        # scores (2026-08-03). Refuse; regenerate the dossier set.
        errs.append(f"{dossier_dir}: index.jsonl has no config-identity "
                    "header record (first line must be a config_identity "
                    "record carrying input shas) — regenerate the census "
                    "with the current tooling")

    ids = [v.get("dossier_id") for v in verdicts]
    from collections import Counter
    for did, n in sorted(Counter(ids).items()):
        if n > 1:
            errs.append(f"duplicate verdict for {did} ({n} records)")
    unknown = sorted(set(ids) - set(index))
    for did in unknown:
        errs.append(f"unknown dossier_id {did}")
    missing = sorted(set(index) - set(ids))
    for did in missing:
        errs.append(f"missing verdict: dossier {did} has no record")

    sweep_core = None
    if sweep_findings:
        sf = json.load(open(sweep_findings))
        sweep_core = set(sf.get("in_scope_unselected") or [])

    by_cause = Counter()
    for v in verdicts:
        did = v.get("dossier_id")
        cause, side = v.get("cause"), v.get("side")
        if cause not in CAUSE_TAXONOMY:
            errs.append(f"{did}: cause {cause!r} not in the closed taxonomy")
            continue
        by_cause[cause] += 1
        if side not in SIDES:
            errs.append(f"{did}: side {side!r} not in {SIDES}")
        if not isinstance(v.get("note", ""), str):
            errs.append(f"{did}: note must be a string")
        if sweep_core is not None:
            for name in v.get("sweep_core_evidence") or []:
                if name not in sweep_core:
                    errs.append(f"{did}: sweep_core_evidence {name!r} is not "
                                "an in_scope_unselected sweep finding")
        if did in index:
            fname = index[did].get("file", did + ".json")
            d = json.load(open(os.path.join(dossier_dir, fname)))
            errs.extend(_consistency(v, d))

    return {"ok": not errs, "violations": errs, "n_verdicts": len(verdicts),
            "by_cause": dict(sorted(by_cause.items()))}


# ---------------------------------------------------------------------- CLI

def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    g = sub.add_parser("dossiers")
    g.add_argument("--annotations", default=ANNOTATIONS)
    g.add_argument("--atoms", default=BEHAVIOUR_ATOMS)
    g.add_argument("--out-root", default=OUT_ROOT)
    g.add_argument("--overlay", default=None,
                   help="opt-in containment overlay (licensed edges), "
                        "mirroring snapshot.py: the census index scores "
                        "through ContainmentIndex and the overlay sha joins "
                        "the config-identity header. Absent means none, "
                        "recorded as an explicit null.")
    g.add_argument("--thresholds", default=None,
                   help="opt-in frozen-thresholds artifact, mirroring "
                        "snapshot.py: named behaviours take their cut FROM "
                        "the artifact (cut_source frozen_artifact), others "
                        "fall back to the label-free rule (rule_fallback); "
                        "the artifact sha joins the header.")
    v = sub.add_parser("validate")
    v.add_argument("--verdicts", required=True)
    v.add_argument("--dossier-dir", required=True)
    v.add_argument("--sweep-findings", default=None)
    args = ap.parse_args()

    if args.cmd == "dossiers":
        import benchmark as B
        import relevance as R
        clauses, _ = B.load_clauses()
        if args.overlay:
            # the shipped configuration is overlay-ON with frozen cuts: a
            # plain-index rebuild of it silently contradicts frozen scores
            # (the 2026-08-03 dossier lesson) — thread the overlay HERE.
            import containment
            index = containment.ContainmentIndex.from_files(
                annotations_path=args.annotations,
                edges=containment.load_edges(args.overlay))
        else:
            index = R.RelevanceIndex.from_files(
                annotations_path=args.annotations)
        frozen_cuts = None
        if args.thresholds:
            import snapshot
            frozen_cuts = snapshot.load_frozen_thresholds(args.thresholds)
        panel = B.load_true_panel()
        behaviours = R.behaviours_from_panel(panel, atoms_source=args.atoms)
        raw_ann = json.load(open(args.annotations))
        clause_atoms = raw_ann.get("by_clause") or R.load_annotations(
            args.annotations)
        tag = config_tag(args.annotations, args.atoms)
        out_dir = os.path.join(args.out_root, tag)
        header = config_identity(args.annotations, args.atoms,
                                 overlay_path=args.overlay,
                                 thresholds_path=args.thresholds)
        recs = generate_dossiers(index, behaviours, panel, clauses,
                                 clause_atoms, out_dir, tag, header=header,
                                 frozen_cuts=frozen_cuts)
        from collections import Counter
        kinds = Counter(r["kind"] for r in recs)
        print(f"wrote {len(recs)} dossiers -> {out_dir} "
              f"(FN {kinds.get('FN', 0)}, FP {kinds.get('FP', 0)})")
    else:
        rep = validate(args.verdicts, args.dossier_dir, args.sweep_findings)
        print(f"--- verdicts {rep['n_verdicts']}; by_cause {rep['by_cause']}")
        if rep["ok"]:
            print("CLEAN")
        else:
            for e in rep["violations"]:
                print("VIOLATION:", e)
            raise SystemExit(
                f"INVALID: {len(rep['violations'])} violation(s) — the "
                "verdict file is refused; fix and re-validate.")


if __name__ == "__main__":
    main()
