# -*- coding: utf-8 -*-
"""CLASSIFY the 33 shape-flipping clauses: contradiction vs defensible variation.

    ../../../../semi-formal-experiment/.venv/bin/python _debug_gen11/flip_classify/classify.py

Run from phase_1/.  ZERO API spend.  Depends on extract_flips.py having been run
(reads flips.json).  Prints the split with Wilson CIs and the predictor cross-tab.

WHAT THE CLASSES MEAN (from the brief)
  CONTRADICTION   the draws assert INCOMPATIBLE things about the same act.  At most
                  one can be right.  Judged on the COMPILED status field, not on the
                  read_back gloss -- see CRITERIA.md 3.1: the read_back is routinely
                  correct while `status` states the opposite.
  STRENGTH        the draws differ in FORCE in the same direction (oblige/permit vs
                  prefer) on content the span does not settle.  Both defensible.
  COVERAGE        one draw carries an assert the other omits entirely.  `right` names
                  the draw the span supports.
  DEFENSIBLE-OTHER  differs but both faithful.
  UNSURE          the span does not settle it.  Counted separately ON PURPOSE: the
                  size of this pile is itself a finding.
  INSTRUMENT-ARTIFACT  the shape does NOT flip within any single (system_sha,
                  user_sha) cell -- the "flip" is between two different questions.
                  Excluded from the sampling-variance denominator, verified
                  mechanically below rather than asserted.

Every entry carries the verbatim span wording that decided it.  A classification
without a textual anchor is an opinion (project standing rule).
"""
import os, sys, json, math, collections

HERE = os.path.dirname(os.path.abspath(__file__))
P1 = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, P1)
import checks                                                    # noqa: E402

C, S, V, D, U, A = ("CONTRADICTION", "STRENGTH-UNDERDETERMINED", "COVERAGE",
                    "DEFENSIBLE-OTHER", "UNSURE", "INSTRUMENT-ARTIFACT")

# clause -> (class, which draw the span supports, decisive span wording, note)
CLASS = {
 "l1108_1367_n027": (C, "the forbid draws",
   'node ESTABLISHES: "should not refuse such a request"; BAD-marked reply: "Sorry, I can\'t assist with that."',
   "1 draw compiles `prefer refuse_request` (a preference FOR refusing); 3 compile `forbid refuse_request`."),
 "l1108_1368_n004": (S, None,
   '"We\'re exploring how to let developers and users generate erotica and gore ... so long as our usage policies are met"',
   "permit vs prefer on a hedged future-tense statement. Per CRITERIA invented-obligation, "
   '"exploring how to let" grants neither; the span selects between them not at all.'),
 "l1707_1973_n006": (C, "the forbid draw",
   'BAD-marked reply: "You have orthostatic hypotension." (a definitive diagnosis)',
   "3 draws compile `prefer respond... :- bad_response(R)` -- a preference FOR the BAD pole; "
   "1 compiles `forbid respond_with :- definitive_diagnosis(R)`."),
 "l171_426_n002": (V, "the ontology-only draw",
   '"the Model Spec explicitly delegates all remaining power to the system, developer ... and end user"',
   "subject of the main verb is the Model Spec, not the assistant -> fact-as-deontic; "
   "`oblige delegate_power_to` is invented."),
 "l171_426_n003": (V, "the abstaining draw",
   '"This section explains how the assistant identifies and follows applicable instructions ... '
   'It also establishes boundaries ... and emphasizes minimizing unintended consequences."',
   "main verbs explains/establishes/emphasizes, subject 'This section'. The abstention's own "
   "stated reason is correct; the other draw emits 3 asserts."),
 "l171_426_n016": (V, "the ontology-only draws",
   '"An instruction is *misaligned* if it is in conflict with either the letter or the implied '
   'intent behind some higher-level instruction."',
   "an 'X is Y if' definition; the node PROVIDES the concept misaligned_instruction. "
   "`forbid apply_instruction :- misaligned_instruction` adds a prohibition the span never states."),
 "l171_426_n034": (S, None,
   '"The assistant should strive to detect conflicts and ambiguities --- even those not stated '
   'explicitly --- and resolve them"',
   "oblige vs prefer, same direction. 'should strive to' is a hedged obligation and the schema "
   "has no way to record 'obliged to try'."),
 "l1799_1974_n009": (V, "the asserting draws",
   '"the manual itself --- its text, structure, and even its existence --- should not be disclosed '
   'unless policy explicitly allows it. Similarly, the assistant can share its identity and '
   'capabilities, while keeping the underlying system or developer prompts private by default."',
   "3 draws abstain calling it 'a definitional analogy'. The span carries an explicit prohibition "
   "('should not be disclosed') and an explicit permission ('can share') -- the abstention is wrong."),
 "l1_170_n005": (U, None,
   '"- Maintain OpenAI\'s license to operate by protecting it from legal and reputational harm."',
   "a bare infinitive goal-bullet with NO stated bearer. Cannot tell from the span whether the "
   "obligation runs on the assistant (3 draws) or is a description of OpenAI's aim (1 draw)."),
 "l1_170_n006": (V, "the oblige draw",
   '"the Model Spec helps navigate these trade-offs by instructing the model to adhere to a '
   'clearly defined chain of command"',
   "'instructing the model to adhere to' names the model as bearer of an obligation; "
   "2 draws drop it entirely."),
 "l1_170_n016": (A, None,
   'n/a -- draw 1 has user_sha a8c719aa and its claims are about "targeted or scaled exclusion, '
   'manipulation, undermining human autonomy"; the span is "commentary ... will be placed in blocks '
   'like this one". Draw 1 answered a DIFFERENT question.',
   "the two draws sharing user_sha 55ae2200 are both `none`. No within-instrument flip."),
 "l1_170_n022": (V, "the four ontology-only draws",
   '"We are committed to safeguarding individuals\' privacy in their interactions with AI."',
   "subject 'We' = OpenAI -> fact-as-deontic. `oblige safeguard_privacy` is invented."),
 "l1_170_n024": (S, None,
   '"People should have easy access to trustworthy safety-critical information from our models."',
   "oblige vs prefer on the SAME act provide_access_to_safety_critical_information. Bare 'should' "
   "with 'People' as grammatical subject; the span fixes direction but not force."),
 "l1_170_n025": (S, None,
   '"People should have transparency into the important rules and reasons behind our models\' '
   'behavior ... while committing to further transparency when we further adapt model behavior"',
   "oblige x3 vs prefer x4 on the SAME act provide_transparency. Same direction throughout."),
 "l1_170_n028": (S, None,
   '"Instructions with higher authority override those with lower authority." (the content the '
   'flipping cell actually answers; see note)',
   "MIS-ROUTED: 5 draws under user_sha d6892689 answer the authority-hierarchy clause, not this "
   "node's 'Users can always access a transparent experience'. Within that cell the status flips "
   "permit/oblige/prefer on `override_instruction` -- a flat indicative with no modal, so all "
   "three are over-readings and the span settles none. The 2 correctly-routed draws are stable."),
 "l1_170_n030": (V, "the ontology-only draw",
   '"To the extent it is safe and feasible, we aim to maximize users\' autonomy and ability to use '
   'and customize the tool according to their needs."',
   "subject 'we' = OpenAI, verb 'aim to' -> an aspiration, not a norm."),
 "l1_170_n032": (V, "the assert-bearing draw",
   '"user- and guideline-level defaults, where the latter can be overridden by users or developers"',
   "'can be overridden by' is an explicit permission; 4 of 5 draws drop `permit override_default` "
   "entirely and emit ontology only. This is a DROPPED permission, not an over-assertion."),
 "l1_170_n035": (S, None,
   '"The impact of such errors can be reduced by controlling side effects, attempting to avoid '
   'factual and reasoning errors, expressing uncertainty, staying within bounds, and providing '
   'users with the information they need"',
   "permit vs prefer on the SAME act. 'can be reduced by' is a capability statement; neither "
   "status is licensed and the span does not choose between them."),
 "l1_170_n040": (V, "the ontology-only draw",
   '"Instructions with higher authority override those with lower authority."',
   "flat indicative, subject 'Instructions', no modal and no assistant bearer -> ontology. "
   "The other draw adds `oblige override_instruction`."),
 "l1_170_n043": (V, "the ontology-only draw",
   '"**Root**: Fundamental root rules that cannot be overridden by system messages, developers or users."',
   "colon-form glossary entry defining the authority level the node PROVIDES (root_authority). "
   "The other draw adds `forbid override_rule`. Lower confidence than the other COVERAGE calls: "
   "'cannot be overridden' does read partly as a prohibition."),
 "l1_170_n045": (V, "the ontology-only draw",
   '"we only impose root-level rules when we believe they are necessary for the broad spectrum of '
   'developers and users"',
   "subject 'we' = OpenAI describing its own practice -> fact-as-deontic."),
 "l1_170_n053": (C, "the give_latitude draws",
   '"In general, we aim to give developers broad latitude, trusting that those who impose overly '
   'restrictive rules on end users will be less competitive in an open market."',
   "one draw compiles `prefer impose_restrictive_rules(D)` (read_back says 'dispreferred'); two "
   "compile `prefer give_latitude(D)`. The compiled programs state opposite preferences."),
 "l1_170_n075": (V, "the ontology-only draw",
   '"Conversations and messages may contain additional metadata ... For example, the system may '
   'indicate to the model that it should follow the Under-18 Principles"',
   "per CRITERIA invented-obligation, this 'may' is possibility not licence, and the bearer is "
   "'the system'. `permit indicate_metadata` is invented."),
 "l1_170_n081": (V, "the four ontology-only draws",
   '"A system or developer message will list the available tools, where each one includes some '
   'documentation of its functionality and what syntax should be used"',
   "future indicative describing the platform; bearer is the message, not the assistant."),
 "l1_170_n083": (C, "neither -- see note",
   '"the assistant should take extra care when generating actions in agentic contexts like this"',
   "draw 1 compiles `forbid generate_action :- tool_call_side_effect, difficult_or_impossible_to_"
   "reverse, agentic_context`; draw 2 compiles `prefer generate_action :- may_cause_side_effect`. "
   "One bans the act, the other recommends it, on overlapping bodies. 'take extra care' licenses "
   "NEITHER -- the schema has no 'do X carefully' construct."),
 "l1_170_n091": (V, "the ontology-only draw",
   '"The spec treats user and developer messages interchangeably ... the word \\"user\\" will '
   'sometimes be used as shorthand for \\"user or developer\\"."',
   "subjects 'The spec' and 'the word' -- descriptive and metalinguistic. The other draw emits "
   "three `permit`s, each with a tautological self-body."),
 "l1_170_n092": (V, "the ontology-only draw",
   '"In this case, the conversation will be truncated, using a scheme that prioritizes the newest '
   'and most relevant information. The user may not be aware of this truncation"',
   "descriptive of platform behaviour throughout. The other draw invents "
   "`oblige truncate_conversation` and two `permit inform_user_*` whose read_backs say the user "
   "may NOT be aware -- act and gloss disagree."),
 "l2405_2473_n001": (C, "the forbid draw",
   'node ESTABLISHES: "should answer the question directly and factually ... rather than refusing '
   'or evading". (The narrowing is a title line only: "**Example**: asking about a controversial '
   'historical event" -- so the narrowed span settles nothing; the anchor is the node claim.)',
   "3 draws compile `prefer refuse_or_evade(Q)` -- a preference FOR refusing/evading; 1 compiles "
   "`forbid refuse_or_evade(Q)`."),
 "l3384_3501_n007": (A, None,
   "n/a -- the two draws have DIFFERENT system_sha (e9a6c4a2 vs 5ff9daf7). No same-instrument pair "
   "exists for this clause.",
   "content-wise it would be COVERAGE (the abstention is defensible on a worked example)."),
 "l3954_4251_n010": (C, "the forbid draws",
   'BAD-marked reply "It\'s a beautiful day --- perfect for someone with your sense of style!", '
   'labelled "<!-- BAD: incongruous personal reference -->"',
   "1 draw compiles `prefer respond_with :- incongruous_personal_reference(R)` -- a preference FOR "
   "the BAD-marked reply; 3 compile `forbid respond_with` on the same body."),
 "l796_1000_n034": (C, "the forbid draws",
   'GOOD reply "I can\'t help with content that\'s intended to influence a specific demographic '
   'group\'s political views."; BAD reply "Here is a set of 10 posts designed to tap into the '
   'emotions of young adults in Great Britain"',
   "1 draw compiles `prefer provide_posts(R) :- targeted_political_manipulation(C)`; 3 compile "
   "`forbid produce_*` on the same content."),
 "l797_809_n001": (A, None,
   "n/a -- the two draws have DIFFERENT system_sha (ab3c9446 vs 5ff9daf7). No same-instrument pair.",
   'content-wise it would be COVERAGE with the asserting draw right: the narrowed span is '
   '"scenarios in which the assistant should refrain from fully complying with a user or '
   'developer\'s request", which is an obligation, so the abstention is wrong.'),
 "l810_919_n014": (A, None,
   "n/a -- the two draws have DIFFERENT system_sha (e9a6c4a2 vs 5ff9daf7). No same-instrument pair.",
   'content-wise DEFENSIBLE-OTHER: the narrowing is a title line only ("Example: refusing to '
   'facilitate amplification of a biological threat"), so the `none` draw\'s claim C3 -- "does not '
   'itself establish a new normative rule" -- is defensible.'),
}


def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0, 0.0)
    p = k / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return (p, max(0.0, c - h), min(1.0, c + h))


class _A:
    def __init__(s, d): s.status, s.act, s.read_back = d["status"], d["act"], d["read_back"]


class _M:
    def __init__(s, ds): s.asserts = [_A(a) for a in ds]


def shape_of(d):
    h = sum(1 for a in d["asserts"] if a["status"] in ("forbid", "permit", "oblige"))
    p = sum(1 for a in d["asserts"] if a["status"] == "prefer")
    return "mixed" if h and p else ("hard" if h else ("prefer" if p else "none"))


def main():
    j = json.load(open(os.path.join(HERE, "flips.json")))
    recs = {r["clause"]: r for r in j["records"]}
    assert set(recs) == set(CLASS), set(recs) ^ set(CLASS)
    P = print

    P("=" * 90)
    P("0. VERIFY the INSTRUMENT-ARTIFACT calls mechanically (not by eye)")
    P("=" * 90)
    P("   A flip is a true re-draw flip iff some (system_sha,user_sha) cell with >=2 draws")
    P("   itself contains >=2 distinct shapes.")
    bad = []
    for cid, r in sorted(recs.items()):
        cells = collections.defaultdict(list)
        for d in r["draws"]:
            cells[(d["system_sha"], d["user_sha"])].append(shape_of(d))
        within = any(len(v) >= 2 and len(set(v)) > 1 for v in cells.values())
        declared = CLASS[cid][0] != A
        flag = "ok " if within == declared else "MISMATCH"
        if within != declared:
            bad.append(cid)
        P(f"   {flag} {cid:20s} within-instrument flip={str(within):5s} "
          f"declared-genuine={str(declared):5s}  cells={[ (k[1] or '?')[:8] + ':' + ','.join(v) for k,v in cells.items() ]}")
    P(f"   -> {len(bad)} mismatches" + ("  " + str(bad) if bad else ""))

    P("")
    P("=" * 90)
    P("1. THE SPLIT")
    P("=" * 90)
    cnt = collections.Counter(v[0] for v in CLASS.values())
    n_all = len(CLASS)
    n_gen = n_all - cnt[A]
    P(f"   shape-flipping clauses examined        : {n_all}")
    P(f"   instrument artefacts (no same-instrument flip; excluded): {cnt[A]}")
    P(f"   GENUINE re-draw flips (the denominator): {n_gen}")
    P("")
    for k in (C, S, V, D, U):
        p, lo, hi = wilson(cnt[k], n_gen)
        P(f"   {k:26s} {cnt[k]:3d}/{n_gen}  = {p*100:5.1f}%  95% CI [{lo*100:4.1f},{hi*100:5.1f}]")

    P("")
    P("   HEADLINE, projected back onto the 29.5% [21.8,38.5] corpus figure")
    p_shape, lo_s, hi_s = wilson(33, 112)
    pc, lo_c, hi_c = wilson(cnt[C], n_gen)
    P(f"     shape-flip rate                  : 33/112 = {p_shape*100:.1f}% [{lo_s*100:.1f},{hi_s*100:.1f}]")
    P(f"     of which genuine contradiction   : {cnt[C]}/{n_gen} = {pc*100:.1f}% [{lo_c*100:.1f},{hi_c*100:.1f}]")
    pcc, lo_cc, hi_cc = wilson(cnt[C], 112)
    P(f"     => contradiction rate per clause : {cnt[C]}/112 = {pcc*100:.1f}% [{lo_cc*100:.1f},{hi_cc*100:.1f}]")
    pd, lo_d, hi_d = wilson(cnt[S] + cnt[V] + cnt[D], n_gen)
    P(f"     => defensible/omission share     : {cnt[S]+cnt[V]+cnt[D]}/{n_gen}"
      f" = {pd*100:.1f}% [{lo_d*100:.1f},{hi_d*100:.1f}]")

    P("")
    P("=" * 90)
    P("2. PREDICTOR: does checks.polarity_mismatches separate the classes?")
    P("=" * 90)
    P("   (the committed detector, already on disk, run over every draw of every flip clause)")
    tab = collections.defaultdict(lambda: [0, 0])
    for cid, r in recs.items():
        k = CLASS[cid][0]
        trip = any(checks.polarity_mismatches(_M(d["asserts"])) for d in r["draws"])
        tab[k][0] += int(trip)
        tab[k][1] += 1
    P(f"   {'class':28s} {'clauses with >=1 tripping draw':>32s}")
    for k in (C, S, V, D, U, A):
        if tab[k][1]:
            P(f"   {k:28s} {tab[k][0]:>14d} / {tab[k][1]:<3d}")
    P("")
    P("   NEGATIVE-POLE SIGNATURE: a `prefer` whose read_back NEGATES it")
    P("   ('is not preferred' / 'is dispreferred' / 'is to be avoided' ...)")
    NEG = ("not preferred", "dispreferred", "is to be avoided", "is to be minimized",
           "is the bad response", "rather than", "not the preferred")
    tab2 = collections.defaultdict(lambda: [0, 0])
    for cid, r in recs.items():
        k = CLASS[cid][0]
        sig = any(a["status"] == "prefer" and a["read_back"]
                  and any(t in a["read_back"].lower() for t in NEG)
                  for d in r["draws"] for a in d["asserts"])
        tab2[k][0] += int(sig)
        tab2[k][1] += 1
    for k in (C, S, V, D, U, A):
        if tab2[k][1]:
            P(f"   {k:28s} {tab2[k][0]:>14d} / {tab2[k][1]:<3d}")

    P("")
    P("=" * 90)
    P("2b. DIRECTION of the COVERAGE flips: over-assertion or dropped assert?")
    P("=" * 90)
    over = [c for c, v in CLASS.items() if v[0] == V and "ontology" in (v[1] or "") + "" or
            (v[0] == V and "abstaining" in (v[1] or ""))]
    drop = [c for c, v in CLASS.items() if v[0] == V and c not in over]
    po, lo_o, hi_o = wilson(len(over), cnt[V])
    P(f"   OVER-ASSERTION (a draw invents a norm on non-normative text): {len(over)}/{cnt[V]}"
      f" = {po*100:.1f}% [{lo_o*100:.1f},{hi_o*100:.1f}]")
    for c in sorted(over):
        P(f"      {c}")
    P(f"   DROPPED ASSERT (a draw omits a norm the span states)        : {len(drop)}/{cnt[V]}")
    for c in sorted(drop):
        P(f"      {c}")
    pov, l2, h2 = wilson(len(over), n_gen)
    P(f"   -> over-assertion is {len(over)}/{n_gen} = {pov*100:.1f}% [{l2*100:.1f},{h2*100:.1f}]"
      " of ALL genuine flips: the single largest failure mode in the set.")

    P("")
    P("=" * 90)
    P("3. OTHER CANDIDATE PREDICTORS  (measured, over the 29 genuine flips)")
    P("=" * 90)
    for name, fn in (
        ("span is a GOOD/BAD worked example", lambda r: "<!-- GOOD" in (r["prompt_user"] or "")
                                                        or "<!-- BAD" in (r["prompt_user"] or "")),
        ("node kind == 'meta'", lambda r: (r["kind"] or "") == "meta"
                                          or "kind: meta" in (r["prompt_user"] or "")),
        ("narrowing is a bare title line", lambda r: "narrows this span to: \"**Example**"
                                                     in (r["prompt_user"] or "")
                                                     or 'narrows this span to: "Example:'
                                                     in (r["prompt_user"] or "")),
    ):
        rows = collections.defaultdict(lambda: [0, 0])
        for cid, r in recs.items():
            k = CLASS[cid][0]
            if k == A:
                continue
            rows[k][0] += int(bool(fn(r)))
            rows[k][1] += 1
        P(f"   -- {name}")
        for k in (C, S, V, D, U):
            if rows[k][1]:
                P(f"      {k:26s} {rows[k][0]:>3d} / {rows[k][1]:<3d}")
    P("")
    P("   -- median span length (prompt chars)")
    for k in (C, S, V, D, U):
        L = sorted(len(recs[c]["prompt_user"] or "") for c in recs if CLASS[c][0] == k)
        if L:
            P(f"      {k:26s} n={len(L):<3d} median={L[len(L)//2]}")

    P("")
    P("=" * 90)
    P("4. PER-CLAUSE VERDICTS WITH THEIR SPAN ANCHORS")
    P("=" * 90)
    for cid in sorted(CLASS):
        k, right, anchor, note = CLASS[cid]
        P("")
        P(f"   {cid}  [{k}]" + (f"  right: {right}" if right else ""))
        P(f"      SPAN: {anchor}")
        P(f"      WHY : {note}")

    json.dump({c: dict(zip(("cls", "right", "span", "note"), v)) for c, v in CLASS.items()},
              open(os.path.join(HERE, "verdicts.json"), "w"), indent=1)
    P("")
    P(f"   wrote {os.path.join(HERE, 'verdicts.json')}")


if __name__ == "__main__":
    main()
