%% A FORMAL MODEL OF THE PIPELINE DESCRIBED IN resources/03_pipeline.md
%%
%% Hand-authored. Every fact should be checkable against that document; guard.py
%% detects when the document changes and this has not been reviewed.
%%
%% This models the DESIGN, not the specification corpus. It answers:
%%   - does every problem have a check that claims to catch it?
%%   - can a seat reach material it is forbidden from seeing, transitively?
%%   - does every check run where its inputs exist?
%%   - does every measured claim carry a source and an n?

%% ---------- problems -------------------------------------------------------
%% problem(Id, Category, Detection)
problem(p1,  translation, silent).       problem(p2,  translation, silent).
problem(p3,  translation, loud).         problem(p4,  translation, misleading).
problem(p5,  translation, silent).       problem(p6,  translation, silent).
problem(p7,  translation, loud).
problem(p8,  cross_clause, silent).      problem(p9,  cross_clause, silent).
problem(p10, cross_clause, silent).
problem(p11, testing, silent).           problem(p12, testing, silent).
problem(p13, testing, silent).           problem(p14, testing, silent).
problem(p15, testing, misleading).
problem(p16, checking, silent).
problem(p17, cross_clause, silent).      % cyclic beats/2 silently wrong (deolingo assessment)

%% ---------- stages ---------------------------------------------------------
stage(s0, competency_questions).   stage(s1, translate).
stage(s2, deterministic).          stage(s3, repair).
stage(s4, test_cases).             stage(s5, read_back).
stage(s6, divergence).             stage(s7, normalise).
stage(s8, expand).                 stage(s9, link).
stage(s10, mutation).              stage(s11, disagreement).

%% ---------- checks, and what each does about which problem -----------------
%% check(Id, Stage, Kind)
%%   catches(Check, Problem)         — the check CLOSES it
%%   narrows(Check, Problem, Escape) — the check REDUCES it; Escape names what
%%                                     still gets through. A narrowed problem is
%%                                     NOT deterministically floored.
%%
%% ⚠️ Distinguishing these matters: an earlier version recorded everything as
%% `catches`, so the silent-needs-determinism rule stayed quiet on problems that
%% only had partial mechanical coverage. That is false comfort, which is worse
%% than an open finding.
check(compile,    s2, deterministic).  catches(compile, p7).
check(link,       s2, deterministic).  narrows(link, p2, never_referenced).
%%   escapes: a dependency the translation should have used and simply did not.
check(witness,    s2, deterministic).  catches(witness, p3).   catches(witness, p15).
check(coverage,   s2, deterministic).  catches(coverage, p12).
check(stub,       s2, deterministic).  narrows(stub, p5, partially_filled).
%%   escapes: a stub carrying some trivial content is not a bare leaf.
check(licence,    s2, deterministic).  narrows(licence, p1, mints_a_dictionary_entry).
%%   escapes: an invention that also mints a concept entry resolves cleanly.
check(anthem,     s2, deterministic).  narrows(anthem, p14, undeclared_spec).
%%   escapes: a rule-set claim nobody thought to declare.
check(cycle_beats,s2, deterministic).  catches(cycle_beats, p17).
check(probe_run,  s4, deterministic).  catches(probe_run, p11). narrows(probe_run, p13, outside_the_probe_set).
%%   escapes: over-permissiveness on situations no probe covers. A test, not a proof.
check(citation,   s5, seat).           catches(citation, p1).   catches(citation, p6).
check(fresh,      s5, seat).           catches(fresh, p4).
check(complete,   s5, seat).           catches(complete, p12).
check(diverge,    s6, deterministic).  narrows(diverge, p9, single_reading_only).
%%   escapes: needs two readings to compare; a uniformly-wrong reading has no twin.
check(normalise,  s7, seat).           catches(normalise, p8).  catches(normalise, p9).
check(param,      s7, seat).           catches(param, p10).
check(mutate,     s10, deterministic). catches(mutate, p16).
check(disagree,   s11, deterministic). catches(disagree, p16).

%% ---------- seats and their materials --------------------------------------
%% seat(Id, Stage) · sees(Seat, Material) · forbidden(Seat, Material)
seat(self_check, s5).      sees(self_check, own_translation).
                           sees(self_check, clause).
seat(fresh_reader, s5).    sees(fresh_reader, clause).
                           sees(fresh_reader, paraphrase).
                           forbidden(fresh_reader, logic_source).
seat(citation_checker,s5). sees(citation_checker, one_fact).
                           sees(citation_checker, cited_clause).
seat(completeness, s5).    sees(completeness, clause).
                           sees(completeness, all_paraphrases).
seat(probe_labeller, s4).  sees(probe_labeller, clause).
                           sees(probe_labeller, enumerated_situations).
                           forbidden(probe_labeller, expected_verdicts).
seat(translator, s1).      sees(translator, clause).
                           sees(translator, closure_texts).
                           forbidden(translator, expected_verdicts).
                           forbidden(translator, behaviour).
                           forbidden(translator, panel_label).

%% ---------- conversation continuity ----------------------------------------
%% A seat that continues an earlier conversation inherits everything that
%% conversation saw. This is what makes the repair loop checkable.
%% continues(Seat, EarlierSeat)
continues(repair_seat, translator).
seat(repair_seat, s3).     sees(repair_seat, failing_check).
                           forbidden(repair_seat, expected_verdicts).

%% ---------- what each stage exposes ----------------------------------------
exposes(s4, expected_verdicts).
exposes(s5, paraphrase).
exposes(s1, logic_source).

%% ---------- accounting: built, or explicitly owed ---------------------------
%% ⚠️ At this stage almost nothing is built, so "is it implemented?" is the wrong
%% question — the answer is always no. The defect is a check asserted with
%% NEITHER an implementation NOR a TODO: that is a fabrication, and this model
%% committed two of them before this section existed.
%%
%%   implementation(Check, Path) — code exists and runs
%%   todo(Check, Why)            — deliberately owed, with a reason
%%   neither                     — invented; the `unaccounted` finding fires
%%
%% ⭐ TODO support is scaffolding. When the pipeline is built, `todo/2` should be
%% removed and every check should carry an implementation or not exist.

implementation(compile,  "walkthrough/link.py — parse and unresolved-name check").
implementation(link,     "walkthrough/link.py — anchor closure + unresolved predicates").
implementation(witness,  "walkthrough/witness.lp — demonstrated, not packaged").

todo(coverage,    "ASP has published rule/definition/loop coverage criteria; none written here").
todo(cycle_beats, "the design says #17 needs a mechanical cycle check on beats/2; not written").
todo(stub,        "opaque-stub detection: a predicate standing for a referenced section with no defining rules").
todo(licence,     "blocked: facts do not carry licences yet — Invariant 2 unimplemented").
todo(anthem,      "external tool identified (anthem 2.0); not wired").
todo(probe_run,   "needs stage 4 to exist").
todo(diverge,     "needs two readings to compare; stage 6 unbuilt").
todo(mutate,      "stage 10 unbuilt").
todo(disagree,    "stage 11 unbuilt").
todo(citation,    "seat unbuilt").
todo(fresh,       "seat unbuilt").
todo(complete,    "seat unbuilt").
todo(normalise,   "stage 7 unbuilt; and open question 3 says its shape is unresolved").
todo(param,       "stage 7 unbuilt").

%% Deterministic checks the design says are possible and nobody has written.
%% Adding these here is a claim that they CAN exist, not that they do.
check(name_divergence, s7, deterministic).  catches(name_divergence, p8).
todo(name_divergence, "compare predicate names across modules; the design says this is mechanical").

check(sibling_detect,  s7, deterministic).  catches(sibling_detect, p10).
todo(sibling_detect,  "shared stem + same rule position proposes a parameterisation candidate").

check(stub_leaf,       s2, deterministic).  catches(stub_leaf, p5).
todo(stub_leaf,       "a predicate standing for a referenced section with NO defining rules is a bare leaf").

label(name_divergence, "cross-module predicate name comparison").
label(sibling_detect, "shared-stem parameterisation proposer").
label(stub_leaf, "bare-leaf detection for referenced sections").

specified(coverage_rule, citation_checker).
%%   ruled 2026-08-07 under open question 5; mechanism written up under stage 5.
%% NOT implemented: its denominator is licence-dependent and facts do not carry
%% licences yet. Invariant 2 is designed and unimplemented.
blocked_by(coverage_rule, invariant_2_unimplemented).

specified(licence_annotation, translation_format).
%%   Invariant 2. No fact in the one worked translation declares a licence.

%% ---------- invariants -----------------------------------------------------
invariant(i1, concept_identity).  invariant(i2, licence_and_citation).
invariant(i3, one_clause_one_module).

%% ---------- measured claims: every one needs a source and an n -------------
%% claim(Id, Source, N)
claim(divergence,     "smoke_live2/extraction_filtered.json", 1).
claim(gloss_drift,    "annotations.json", 228).
claim(flat_siblings,  "smoke_live2/extraction_filtered.json", 1).
claim(witness_scope,  "walkthrough/m0255.lp", 1).
claim(reviewer_blind, "session 2026-08-07 blind judge", 1).
claim(completeness_ok,"session 2026-08-07 blind judge", 1).

%% ---------- declared departures from wider-repo practice -------------------
%% Anything here is a deliberate divergence; anything NOT here is undeclared.
declared_departure(no_cycle_driver).
declared_departure(no_panel_fencing).
declared_departure(no_dev_test_split).

%% ---------- human-readable labels ------------------------------------------
%% So a finding reads as a sentence rather than an id you have to look up.
label(p1, "made-up things").
label(p2, "missing cross-references").
label(p3, "rules that can never fire").
label(p4, "right answer, wrong stated reason").
label(p5, "hollow stubs").
label(p6, "guessing forward from a backward statement").
label(p7, "anonymous placeholders break the explainer").
label(p8, "different names for the same thing").
label(p9, "same name, different meanings").
label(p10, "flat lists where structure was needed").
label(p11, "test cases describing impossible situations").
label(p12, "testing one branch only").
label(p13, "only testing that it forbids").
label(p14, "claims no test case can demonstrate").
label(p15, "'never fired' has three causes").
label(p16, "a reviewer cannot see invented entities").
label(p17, "a cyclic priority relation is silently wrong").
label(citation_checker, "the citation checker seat").
label(coverage_rule, "every judgeable fact judged exactly once, ids known, reasons non-empty").
label(invariant_2_unimplemented, "facts do not carry licences yet, so the denominator cannot be computed").
label(divergence, "predicate divergence, 12 of 13 names singleton").
label(gloss_drift, "definition drift, 46 of 228 reused names").
label(flat_siblings, "eight quoted_text_* symbols where one was wanted").
label(witness_scope, "5 witnesses linked vs 0 unlinked").
label(reviewer_blind, "a clean reviewer passed a fabricated policy").
label(completeness_ok, "the same reviewer named both uncovered claims").
