# Controlled-suite claim results

These measurements describe supplied predictions on synthetic constructed cases. Model identity, prompt, parameters, tool access and raw-response provenance must be reported separately if external models produced these predictions. These figures do not establish deployment effectiveness.

| Split | Method | Episodes | Families | Claims | Accuracy | Resolved | Resolved accuracy | False support / endorsements |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| test | grok-4.7-audit-supplied-claims-v1 | 60 | 12 | 420 | 100.00% | 92.38% | 100.00% | 0 / 333 |

Accuracy includes all three labels. Resolution coverage counts supported or contradicted predictions. False support counts an endorsement whose reference is contradicted or unresolved; zero observed errors is not a general guarantee.

All variants of a scenario belong to one split. The test set is public, constructed, and was inspected during software validation. It is not a blind model-selection benchmark. No sampling-based confidence intervals or significance claims are made.

## Test claims by kind

| Method | Kind | Claims | Accuracy | Resolved | False support |
|---|---|---:|---:|---:|---:|
| grok-4.7-audit-supplied-claims-v1 | contract_lineage | 60 | 100.00% | 96.67% | 0 |
| grok-4.7-audit-supplied-claims-v1 | commitment_grounding | 60 | 100.00% | 66.67% | 0 |
| grok-4.7-audit-supplied-claims-v1 | dispute_grounding | 60 | 100.00% | 96.67% | 0 |
| grok-4.7-audit-supplied-claims-v1 | conditional_execution | 60 | 100.00% | 100.00% | 0 |
| grok-4.7-audit-supplied-claims-v1 | final_action_by_rule | 60 | 100.00% | 90.00% | 0 |
| grok-4.7-audit-supplied-claims-v1 | candidate_stability | 60 | 100.00% | 96.67% | 0 |
| grok-4.7-audit-supplied-claims-v1 | sufficient_dispute_reason | 60 | 100.00% | 100.00% | 0 |

See `summary.json` for all class confusion matrices, per-class precision/recall/F1, per-variant results, and each scenario family's results. Null rates have a zero denominator and are not zero errors.
