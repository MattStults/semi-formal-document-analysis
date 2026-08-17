#!/usr/bin/env python3
"""THE INSTRUMENT CENSUS. Free, deterministic, no model call.

Every instrument in the pipeline that can EMIT A FINDING OR A VERDICT, with its
generalization class and the file:line that carries the dependency.

CLASSES
  STRUCTURAL   depends only on module/graph shape or on markers the PIPELINE
               ITSELF emits. Survives a document with no conventions at all.
  LANGUAGE     mechanism general, implementation carries English idiom/wordlist.
  DOCUMENT     encodes vocabulary or conventions specific to the Model Spec.
  CORPUS       carries a constant fitted to this corpus.
A row may carry more than one non-STRUCTURAL class; it is then counted as TUNED.

FAILURE MODE on a document without the Model Spec's conventions:
  quiet    produces nothing, and its absence is visible (a count goes to 0)
  graceful degrades and says so
  WRONG    ⛔ produces output that looks like a finding and is not, or goes
           silent in a way indistinguishable from "clean"
"""
import collections, json, os

R = []
def row(layer, name, site, cls, fail, note):
    R.append(dict(layer=layer, name=name, site=site, cls=cls, fail=fail, note=note))

W = "walkthrough/"
P = "walkthrough/paper_pipeline/phase_1/"
G = P + "resolve_runs/graph_v2/"
D = P + "_debug_gen11/"

# ---------------- stage 2: the deterministic check layer -------------------
row("stage2", "schema.validate_all module contract breaches", P+"schema.py:1158", ["STRUCTURAL"], "-",
    "pydantic shape + licence obligations; LICENCES/STATUSES are the pipeline's own")
row("stage2", "arity check", P+"checks.py:243", ["STRUCTURAL"], "-",
    "name/arity identity over declaration sites; no document text")
row("stage2", "prefer-polarity (_DISFAVOURED)", P+"checks.py:305", ["LANGUAGE","CORPUS"], "WRONG",
    "English disfavour alternations; WIDENED 2026-08-16 onto the sentences it scores against")
row("stage2", "link requires-unprovided", W+"link.py:854", ["STRUCTURAL"], "-", "")
row("stage2", "link concept-table-absent", W+"link.py:695", ["STRUCTURAL"], "-", "")
row("stage2", "link concept-not-in-table", W+"link.py:738", ["STRUCTURAL"], "-", "")
row("stage2", "link concept-multi-gloss", W+"link.py:722", ["STRUCTURAL"], "-", "")
row("stage2", "link rule-shape / forbid-body", W+"link.py:507", ["STRUCTURAL"], "-", "")
row("stage2", "link closure check", W+"link.py:551", ["STRUCTURAL"], "-", "")
row("stage2", "link beats-cycle check", W+"link.py:605", ["STRUCTURAL"], "-", "")
row("stage2", "link clingo errors", W+"link.py:782", ["STRUCTURAL"], "-", "")
row("stage2", "link unresolved-reference", W+"link.py:895", ["STRUCTURAL"], "-", "")
row("stage2", "link concept-declared / situation-input notes", W+"link.py:900", ["STRUCTURAL"], "-", "")
row("stage2", "RB1 label-survives", P+"readback.py:813", ["STRUCTURAL"], "-",
    "coined predicate names surviving into English; names are pipeline-coined")
row("stage2", "RB2 missing-gloss", P+"readback.py:829", ["STRUCTURAL"], "-", "")
row("stage2", "RB3 polarity (counts English `not`)", P+"readback.py:846", ["LANGUAGE"], "WRONG",
    "_markers() counts the literal token `not`; a document in another language or "
    "using `no`/`never`-only negation silently balances")
row("stage2", "RB4 echo score + ECHO_LEVEL 0.90", P+"readback.py:869,70", ["LANGUAGE","CORPUS"], "graceful",
    "_TOKEN=[a-z0-9]+ bag-of-lowercase-ASCII; 0.90 is a declared stamp, never a gate")
row("stage2", "RB5", P+"readback.py:939", ["STRUCTURAL"], "-", "")
row("stage2", "readback.clause_text node-row unpacking", P+"readback.py:462-470", ["STRUCTURAL"], "-",
    "NODE_SECTION_ID / L####-L#### / packed-prompt marker are all PIPELINE-emitted")

# ---------------- stage 3 ---------------------------------------------------
row("stage3", "probe structural checks", P+"probe.py:117", ["STRUCTURAL"], "-", "")
row("stage3", "probe verdict comparison / discrimination count", P+"probe.py:115", ["STRUCTURAL"], "-", "")
row("stage3", "hand-authored act_phrase per clause", P+"probe_live_clauses.json:4", ["DOCUMENT"], "quiet",
    "human input, not code: general in mechanism, must be re-authored per document")

# ---------------- stage 4: the seats ---------------------------------------
row("stage4", "seat 4a as-meant", P+"seats.py:389-406", ["STRUCTURAL"], "-",
    "brief carries NO Model-Spec vocabulary; denominator is module shape")
row("stage4", "seat 4b faithful", P+"seats.py:408-450", ["STRUCTURAL"], "-",
    "one example node id l1_170_n001 appears as frame illustration only, seats.py:426")
row("stage4", "seat 4c licensed (+ PROVIDES join)", P+"seats.py:452-483", ["STRUCTURAL"], "-",
    "join at _debug_gen11/seat_fix/needs_join.py:46-57 is pure needs/provides set logic")
row("stage4", "seat 4d covered", P+"seats.py:485-501", ["STRUCTURAL"], "-", "")
row("stage4", "cross_check_4d vs stage-3 discrimination", P+"seats.py:1073", ["STRUCTURAL"], "-", "")
row("stage4", "seat disclosure fences", P+"seats.py:308-337", ["STRUCTURAL"], "-",
    "_UNIVERSAL_/_MODULE_/_RENDERING_PATTERNS all match pipeline-emitted text")

# ---------------- stage 0/1: decomposition + graph -------------------------
row("graph", "graph_check span/range/quote integrity", G+"graph_check.py:46-102", ["STRUCTURAL"], "-", "")
row("graph", "graph_check normalise() markdown stripping", G+"graph_check.py:14-15", ["LANGUAGE"], "graceful",
    "footnotes, [t](url), ** emphasis, smart quotes")
row("graph", "graph_check K1 (doc lines 183/186/191 + order|rank|... wordlist)", G+"graph_check.py:104-120",
    ["DOCUMENT","LANGUAGE"], "WRONG", "HARD-PINNED DOCUMENT LINE NUMBERS; on any other document "
    "it silently checks a random 8-line window")
row("graph", "graph_check heading-authority capture", G+"graph_check.py:128", ["DOCUMENT"], "quiet",
    "^#+ .*authority=")
row("graph", "recurse_driver formatting_reason (heading/boldline/rule)", G+"recurse_driver.py:347-349",
    ["LANGUAGE"], "graceful", "markdown-generic, not Model-Spec-specific")
row("graph", "recurse_driver bare example-markup tag", G+"recurse_driver.py:358", ["DOCUMENT"], "quiet",
    "<comparison>, </assistant>")
row("graph", "recurse_driver admonition marker", G+"recurse_driver.py:367", ["DOCUMENT"], "quiet", "!!! meta")
row("graph", "recurse_driver authority label + canon + coinage autofix", G+"recurse_driver.py:383-452",
    ["DOCUMENT"], "WRONG", "AUTHORITY_CANONICAL = {root,system,developer,user,guideline}; the autofix "
    "REWRITES a node's section label from the nearest authority= line -- with none present it "
    "cannot fire, so authority coinages pass unrepaired and unflagged")
row("graph", "recurse_driver L<band> sibling id guard", G+"recurse_driver.py:528-534", ["STRUCTURAL"], "-",
    "ids are pipeline-generated")
row("graph", "recurse_driver L<n>/line n citation pattern", G+"recurse_driver.py:575", ["STRUCTURAL"], "-", "")
row("graph", "recurse_driver MERGE_EL element extraction", G+"recurse_driver.py:641", ["LANGUAGE"], "WRONG",
    "(1)-enumerations, Title Case Phrases, \"quoted\"; a document without them falls through to the "
    "lowercase floor with a different threshold")
row("graph", "recurse_driver merge_loss content-word floor <0.6", G+"recurse_driver.py:664", ["LANGUAGE","CORPUS"],
    "WRONG", "[a-z]{5,} bag of words; 0.6 undocumented in derivation")
row("graph", "LEAF_MAX_LINES 300", G+"recurse_driver.py:54", ["CORPUS"], "WRONG",
    "a line is a UNIT OF LENGTH here; model_spec 10.8 words/nonblank line, constitution 58.7 -- "
    "the same 300 buys 5.4x the content")
row("graph", "DEPTH_MAX 8", G+"recurse_driver.py:55", ["CORPUS"], "graceful", "")
row("graph", "LEAF_DENSITY_MAX 0.7", G+"recurse_driver.py:374-380", ["CORPUS"], "WRONG",
    "fitted: 'golden-graph leaves sit at 0.13-0.35'; nodes-per-LINE, so it moves with line length")
row("graph", "density warn 0.5", G+"recurse_driver.py:1532", ["CORPUS"], "graceful", "")
row("graph", "rename similarity >= 0.25", G+"recurse_driver.py:1989", ["CORPUS","LANGUAGE"], "graceful", "")
row("graph", "node_corpus hardcoded DOC path", G+"node_corpus.py:38", ["DOCUMENT"], "quiet", "")
row("graph", "node_corpus kind_of() content sniff", G+"node_corpus.py:76-82", ["LANGUAGE","DOCUMENT"], "WRONG",
    "'rank'/'order'/'hierarch' -> ordering; 'worked example' -> meta. Mis-kinds silently")
row("graph", "node_corpus MUST_HAVE ids / n=15 / seed 42", G+"node_corpus.py:44,124,131", ["CORPUS"], "quiet", "")
row("graph", "promise_repair XREF_RE [t](#anchor)", G+"promise_repair.py:148", ["LANGUAGE"], "quiet",
    "markdown-generic")
row("graph", "promise_repair HEADING_RE ## T {#slug}", G+"promise_repair.py:149-150", ["DOCUMENT"], "WRONG",
    "0 matches on a document without {#anchors}: EVERY promise reads as unestablished")
row("graph", "promise_repair concept_slug *_section convention", G+"promise_repair.py:155-159", ["DOCUMENT"],
    "quiet", "")
row("graph", "promise_repair delivery-narration regex family", G+"promise_repair.py:640-677", ["LANGUAGE"],
    "WRONG", "I/we + add|include|provide...; contraction and negation lists are English-only")
row("graph", "promise_repair same_referent_provider threshold 0.5 (+-2 lines)", G+"promise_repair.py:289",
    ["CORPUS","LANGUAGE"], "WRONG", "token overlap; derivation cites risk_queue.sim 0.545 on THIS corpus")
row("graph", "promise_repair underexport >= 0.25", G+"promise_repair.py:546,569", ["CORPUS"], "graceful", "")
row("graph", "promise_repair SECTION_MAX_LINES 120", G+"promise_repair.py:200", ["CORPUS"], "WRONG",
    "same line-as-unit-of-length problem as LEAF_MAX_LINES")
row("graph", "modal_repair EXAMPLE_MARKERS", G+"modal_repair.py:55-56", ["DOCUMENT"], "WRONG",
    "~~~|<assistant>|<user>|<developer>|<comparison>|!!! meta routes example-quoting spans AWAY from "
    "templating; 0 matches -> every span is templated, including quoted example text")
row("graph", "modal_repair IMPERATIVE", G+"modal_repair.py:39-41", ["LANGUAGE"], "quiet", "")
row("graph", "modal_repair SWAPS must<->should", G+"modal_repair.py:47-50", ["LANGUAGE"], "graceful", "")
row("graph", "sweep_modals flattened/weakened/strengthened", G+"sweep_modals.py:32-36", ["LANGUAGE"],
    "graceful",
    "MEASURED CORRECTION: I predicted this would go quiet. It does not. The ladder already carries "
    "required|prohibited|expected to|allowed to, and its any-modal sentence coverage is HIGHER on the "
    "second document (40.5%) than on the Model Spec (18.1%). English-only, but general within English.")
row("graph", "sweep_headings modal_in_heading", G+"sweep_headings.py", ["LANGUAGE"], "quiet", "")
row("graph", "division_check 2-3 children", G+"division_check.py:11", ["CORPUS"], "graceful", "")
row("graph", "division_check contiguity/coverage/seed-vocab", G+"division_check.py:14-26", ["STRUCTURAL"], "-", "")
row("graph", "link_nodes gather / requires_resolution", G+"link_nodes.py:53-142", ["STRUCTURAL"], "-", "")
row("graph", "corpus_exclusions digest verification", G+"corpus_exclusions.py:99-147", ["STRUCTURAL"], "-", "")
row("graph", "graph_corrections apply()", G+"graph_corrections.py:59-135", ["DOCUMENT"], "quiet",
    "mechanism structural, PAYLOAD is a hand-adjudicated per-node list for this document")
row("graph", "fixup.apply_fixups verdict routing", G+"fixup.py:70-153", ["STRUCTURAL"], "-", "")

# ---------------- the campaign detectors -----------------------------------
row("campaign", "F1-regex (= checks._DISFAVOURED)", D+"fix_matrix/detectors.py:66", ["LANGUAGE","CORPUS"],
    "WRONG", "see stage2 row; its recall is in-sample by the author's own disclosure")
row("campaign", "F1-general polarity oracle", D+"fix_matrix/detectors.py:82", ["STRUCTURAL"], "-",
    "the question contains no corpus wording; MEASURED identical extension to the regex")
row("campaign", "F2 _BEARER actor list", D+"fix_matrix/detectors.py:227", ["DOCUMENT"], "WRONG",
    "(the )?(assistant|model|models|chatgpt|it) -- MEASURED 74.5%->16.5% recognition of deontic "
    "sentences on the second document; F2 fires when NOTHING is norm-bearing, so it becomes a "
    "false-positive generator, not a quiet one")
row("campaign", "F2 _DEONTIC / _PERMISSION / _HEDGE", D+"fix_matrix/detectors.py:232-243", ["LANGUAGE"],
    "WRONG", "may-is-not-a-grant ruling is a MEASURED CORPUS FACT (CRITERIA.md 2), not a language fact")
row("campaign", "F2-wx worked-example guard", D+"fix_matrix/detectors.py:280", ["DOCUMENT"], "WRONG",
    "<!-- GOOD/BAD -->; author already discloses it is FITTED on P-REF")
row("campaign", "F2-live bearer oracle prompt", D+"fix_matrix/oracle.py:66", ["DOCUMENT"], "WRONG",
    "asks a model whether the subject is 'the model/assistant'")
row("campaign", "F4-reach", D+"fix_matrix/detectors.py:328", ["LANGUAGE","CORPUS"], "WRONG",
    "identical extension to F1 by construction")
row("campaign", "_span_sentences ESTABLISHES/SOURCE TEXT parse", D+"fix_matrix/detectors.py:189",
    ["STRUCTURAL"], "-", "parses the pipeline's own prompt format")
row("campaign", "span-first enumerator (force/bearer/act/condition/...)", D+"dropped_content/spanfirst.py:77",
    ["DOCUMENT"], "graceful", "bearer enum is assistant|developer|user|model|none -- a wordlist in a "
    "PROMPT, one line to change, and the verbatim-quote guard is document-independent")
row("campaign", "span-first comparator + verbatim-quote guard", D+"dropped_content/spanfirst.py:154-169",
    ["STRUCTURAL"], "-", "")
row("campaign", "dropped-content Rule B modality presence", D+"dropped_content/RESULT.md", ["LANGUAGE"],
    "quiet", "already a near-null: 1/7 recall")
row("campaign", "flip_classify predictors (GOOD/BAD, kind==meta, **Example** title)",
    D+"flip_classify/classify.py:333-337", ["DOCUMENT"], "WRONG",
    "all three strata predictors go to 0 and the stratification silently collapses to one cell")
row("campaign", "node-conflict heuristic (ESTABLISHES vs span, >50%, L<band> siblings)",
    D+"triage_verify/rederive.py:7-11,23", ["LANGUAGE","CORPUS","STRUCTURAL"], "WRONG",
    "[a-z]{4,} + a ~30-word English stoplist + a 0.5 threshold; the sibling half is structural")
row("campaign", "golden_set known-good / known-bad construction", P+"golden_set.py:63,82,122-140",
    ["LANGUAGE","DOCUMENT"], "graceful",
    "ALIEN wordlist is VERIFIED-ABSENT at build time and RAISES if not; `**Term**:` and the META "
    "section names are the tuned parts. Mechanism regenerates per document.")
row("campaign", "d1_recruit census (wilson, n_for_power, >=2-draw rule)", D+"d1_recruit/census.py:160-274",
    ["STRUCTURAL"], "-", "statistics")

def main():
    by = collections.Counter()
    tuned = [r for r in R if r["cls"] != ["STRUCTURAL"]]
    struct = [r for r in R if r["cls"] == ["STRUCTURAL"]]
    print("=" * 78)
    print(f"INSTRUMENT CENSUS: {len(R)} instruments")
    print("=" * 78)
    lay = collections.defaultdict(lambda: [0, 0])
    for r in R:
        s = r["cls"] == ["STRUCTURAL"]
        lay[r["layer"]][0 if s else 1] += 1
        for c in r["cls"]:
            by[c] += 1
    print(f"\n  STRUCTURAL {len(struct):3d} / {len(R)} = {len(struct)/len(R)*100:.0f}%")
    print(f"  TUNED      {len(tuned):3d} / {len(R)} = {len(tuned)/len(R)*100:.0f}%")
    print("\n  class tags (a row may carry more than one):")
    for c, n in by.most_common():
        print(f"    {c:12s} {n:3d}")
    print("\n  BY LAYER            structural   tuned   %structural")
    for L in ("stage2", "stage3", "stage4", "graph", "campaign"):
        s, t = lay[L]
        print(f"    {L:16s} {s:6d} {t:8d}      {s/(s+t)*100:5.0f}%")
    print("\n" + "=" * 78)
    print("FAILURE MODE ON A CONVENTION-FREE DOCUMENT")
    print("=" * 78)
    fm = collections.Counter(r["fail"] for r in R)
    for k in ("-", "graceful", "quiet", "WRONG"):
        print(f"  {k:10s} {fm[k]:3d}")
    print(f"\n  ⛔ THE SILENTLY-WRONG CLASS ({fm['WRONG']} instruments):")
    for r in R:
        if r["fail"] == "WRONG":
            print(f"    [{r['layer']:8s}] {r['name']}")
            print(f"               {r['site']}")
            print(f"               {r['note']}")
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "census.json")
    json.dump(R, open(out, "w"), indent=1)
    print(f"\n  wrote {out}")

if __name__ == "__main__":
    main()
