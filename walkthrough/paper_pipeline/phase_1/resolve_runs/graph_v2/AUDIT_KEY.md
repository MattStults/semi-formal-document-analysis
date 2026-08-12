# Fable audit of the document graph — key, written BEFORE any auditor ran

**Purpose.** The graph's mechanics are verified (spans resolve, quotes verbatim, names
link, nothing lost). This audit measures what mechanics cannot: whether the JUDGMENTS are
right. Output: an error-rate estimate per stratum plus a findings list — the graph's
quality bar, and the first live run of the golden protocol's adjudication seat.

**Clean-context rules.** Auditors receive ONLY: the raw document, the line-numbered copy,
`graph_stripped.json` (nodes with establishes/needs/provides/spans/uncovered ONLY —
judgment_calls and cross_link_report removed so recorded decisions cannot leak), and
their own sample file. They never see the build prompts, the experiment log, the
orchestrator's transcripts, or another stratum's questions. The orchestrator (who built
the graph) writes no verdicts — only this key, the samples, and the scoring arithmetic.

**Sampling.** Deterministic, seed=42, drawn by script (`audit_sample.py`) from the final
post-mapping graph. Sample files list item ids only.

## Stratum A — node fidelity (n=30 nodes, random)
For each node: read the raw text of its spans (quotes narrow within lines), then score
`establishes` as one of:
- FAITHFUL — states what the text asserts, no more, no less;
- OVERREACH — asserts something the cited text does not;
- INCOMPLETE — the cited text (as narrowed by quotes) asserts something material the
  establishes omits AND no other node citing the same lines covers it (the sample file
  lists co-citing nodes);
- WRONG — misstates the text.
Also flag SPLIT-DEFECT if the establishes conjoins claims that are independently
checkable against a situation (should have been >1 node).

## Stratum B — edge validity (n=30 needs-entries with resolved providers, random)
For each edge (needer id + its needs entry, provider id): read both nodes and their
cited text. Score:
- VALID — the provider ESTABLISHES the concept the needer's prose describes;
- MENTION-ONLY — the provider references/uses the concept but does not establish it;
- MISMATCH — provider establishes a different concept than the needer means;
- PARTIAL — provider establishes part of it (say which part is missing).

## Stratum C — blind re-adjudication of the judgment surface (all items)
Each item is a QUESTION, never the recorded answer:
- For each final_dangling name (with its prose): "Does any node in the graph establish
  this concept? Does the document establish it anywhere (give lines)? Verdict:
  truly-external / establishable-but-missed (say where) / underspecified-by-document."
- For each applied rename (old name, new provider name, needer id): "Read the needer and
  the provider against the document: same concept? YES/NO with grounds."
- The multi-span merge (L1-170_n028): "Do L69-101 and L183-191 establish the SAME claim?
  Should they be one node?"
- The structure node (L1-4691_n001_structure): "Is 'chain_of_command' as defined actually
  established by L66-67 + L171, or invented?"
Agreement with the recorded decision is computed by the orchestrator afterward — the
auditor never knows what was decided.

## Stratum D — coverage honesty (n=15 uncovered ranges, random, weighted by length)
For each range: read it in the raw document. Verdict:
- CORRECTLY-UNCOVERED — establishes nothing (blank/heading/example dialog);
- SILENTLY-DROPPED — contains an assertion/definition/scope no node covers (quote it).

## Outputs
Per stratum: counts per verdict, rate with denominator printed beside it, and a findings
list (item id, verdict, one-sentence grounds). No aggregate "quality score" — the four
rates stay separate because they have different consumers.

## Pre-registered thresholds (what the numbers decide)
- A: FAITHFUL ≥ 90% → establishes-prose is translation-grade; 80–90% → usable with a
  repair pass; <80% → leaf prompt needs another iteration before translation.
- B: VALID ≥ 90% → links are join-grade; MENTION-ONLY is the failure mode to watch
  (it is the self-satisfaction defect surviving in disguise).
- C: disagreements are individually adjudicated (they are few); each one is a finding,
  not a rate.
- D: any SILENTLY-DROPPED is a finding to fix; >2 of 15 → coverage rule needs work.
