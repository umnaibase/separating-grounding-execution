# Controlled-suite claim results

These measurements describe supplied predictions on synthetic constructed cases. Model identity, prompt, parameters, tool access and raw-response provenance must be reported separately if external models produced these predictions. These figures do not establish deployment effectiveness.

| Split | Method | Episodes | Families | Claims | Accuracy | Resolved | Resolved accuracy | False support / endorsements |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| diagnostic | claude-fable-5-1_audit_notools | 8 | 4 | 56 | 76.79% | 62.50% | 100.00% | 0 / 23 |

Accuracy includes all three labels. Resolution coverage counts supported or contradicted predictions. False support counts an endorsement whose reference is contradicted or unresolved; zero observed errors is not a general guarantee.

All variants of a scenario belong to one split. The test set is public, constructed, and was inspected during software validation. It is not a blind model-selection benchmark. No sampling-based confidence intervals or significance claims are made.

## Test claims by kind

| Method | Kind | Claims | Accuracy | Resolved | False support |
|---|---|---:|---:|---:|---:|
| claude-fable-5-1_audit_notools | contract_lineage | 0 | n/a | n/a | 0 |
| claude-fable-5-1_audit_notools | commitment_grounding | 0 | n/a | n/a | 0 |
| claude-fable-5-1_audit_notools | dispute_grounding | 0 | n/a | n/a | 0 |
| claude-fable-5-1_audit_notools | conditional_execution | 0 | n/a | n/a | 0 |
| claude-fable-5-1_audit_notools | final_action_by_rule | 0 | n/a | n/a | 0 |
| claude-fable-5-1_audit_notools | candidate_stability | 0 | n/a | n/a | 0 |
| claude-fable-5-1_audit_notools | sufficient_dispute_reason | 0 | n/a | n/a | 0 |

See `summary.json` for all class confusion matrices, per-class precision/recall/F1, per-variant results, and each scenario family's results. Null rates have a zero denominator and are not zero errors.
