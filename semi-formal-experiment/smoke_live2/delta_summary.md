# Conflict delta --- mechanical metrics

| metric | value |
|---|---|
| `|C_tool|` | 0 |
| `|C_baseline|` | 6 |
| tool_only | 0 |
| baseline_only | 6 |
| both | 0 |
| tool_self_agreement (k=1) | n/a (1/1 runs empty) |
| baseline_self_agreement (k=3) | 0.244 |
| coverage | 0.524 (22/42) |
| rules emitted vs rejected | 22 emitted, 2 rejected (of 24 extracted) |
| coverage_claimed (pre-rejection) | 0.571 (24/42) |
| unencoded | 18 |
| tool conflict channels open | NO (0 incompat, 0 acts both obliged and forbidden) |
| **degenerate** | yes — tool found no conflicts — every bucket is one-sided, `both` is vacuously empty, and no delta is a disagreement between two populated sets |

> **Degenerate comparison.** tool found no conflicts — every bucket is one-sided, `both` is vacuously empty, and no delta is a disagreement between two populated sets.

> **The tool's empty conflict set is not a solver finding.** The emitted program can derive a conflict only from an act that is both obliged and forbidden, or from two obligations over an `incompat` pair. This extraction has 0 `incompat` facts and no act in both modalities, so zero conflicts follows from the extraction before the solver runs. Read it as an extraction result, not as evidence about the section or the method.

## Deltas

**tool_only (0)** --- a real conflict the model missed, or an encoding artifact.

- (none)

**baseline_only (6)** --- a tool miss (name the atom), or a confabulation.

- `fa_0prn` + `fa_1ka0`
- `fa_0prn` + `fa_a9sh`
- `fa_0q9d` + `fa_bn8b`
- `fa_1ka0` + `fa_agh7`
- `fa_1ka0` + `fa_m12p`
- `fa_a9sh` + `fa_agh7`

## Unencoded reasons

- 15 x not reported by the model; no rule was emitted for this provision (reason unstated)
- 3 x no determinate act

Both-found items are low information and are not listed; `adjudicate.py` skips them.
