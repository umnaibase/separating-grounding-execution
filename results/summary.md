# Controlled-suite claim results

These measurements describe the shipped synthetic cases and bounded checker. They are not foundation-model results or evidence of deployment effectiveness. The ablations receive the same sources and records. Disabled checking capabilities abstain; this is not a competitive model comparison.

| Split | Method | Episodes | Families | Claims | Accuracy | Resolved | Resolved accuracy | False support / endorsements |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| dev | boundary | 40 | 8 | 280 | 99.64% | 91.43% | 100.00% | 0 / 223 |
| test | boundary | 60 | 12 | 420 | 99.52% | 91.90% | 100.00% | 0 / 331 |
| dev | execution_only | 40 | 8 | 280 | 63.21% | 55.00% | 100.00% | 0 / 131 |
| test | execution_only | 60 | 12 | 420 | 62.86% | 55.24% | 100.00% | 0 / 193 |
| dev | provenance | 40 | 8 | 280 | 76.79% | 68.57% | 100.00% | 0 / 167 |
| test | provenance | 60 | 12 | 420 | 76.67% | 69.05% | 100.00% | 0 / 247 |

Accuracy includes all three labels. Resolution coverage counts supported or contradicted predictions. False support counts an endorsement whose reference is contradicted or unresolved; zero observed errors is not a general guarantee.

All variants of a scenario belong to one split. The test set is public, constructed, and was inspected during software validation. It is not a blind model-selection benchmark. No sampling-based confidence intervals or significance claims are made.

## Test claims by kind

| Method | Kind | Claims | Accuracy | Resolved | False support |
|---|---|---:|---:|---:|---:|
| boundary | contract_lineage | 60 | 100.00% | 96.67% | 0 |
| boundary | commitment_grounding | 60 | 96.67% | 63.33% | 0 |
| boundary | dispute_grounding | 60 | 100.00% | 96.67% | 0 |
| boundary | conditional_execution | 60 | 100.00% | 100.00% | 0 |
| boundary | final_action_by_rule | 60 | 100.00% | 90.00% | 0 |
| boundary | candidate_stability | 60 | 100.00% | 96.67% | 0 |
| boundary | sufficient_dispute_reason | 60 | 100.00% | 100.00% | 0 |
| execution_only | contract_lineage | 60 | 3.33% | 0.00% | 0 |
| execution_only | commitment_grounding | 60 | 33.33% | 0.00% | 0 |
| execution_only | dispute_grounding | 60 | 3.33% | 0.00% | 0 |
| execution_only | conditional_execution | 60 | 100.00% | 100.00% | 0 |
| execution_only | final_action_by_rule | 60 | 100.00% | 90.00% | 0 |
| execution_only | candidate_stability | 60 | 100.00% | 96.67% | 0 |
| execution_only | sufficient_dispute_reason | 60 | 100.00% | 100.00% | 0 |
| provenance | contract_lineage | 60 | 100.00% | 96.67% | 0 |
| provenance | commitment_grounding | 60 | 33.33% | 0.00% | 0 |
| provenance | dispute_grounding | 60 | 3.33% | 0.00% | 0 |
| provenance | conditional_execution | 60 | 100.00% | 100.00% | 0 |
| provenance | final_action_by_rule | 60 | 100.00% | 90.00% | 0 |
| provenance | candidate_stability | 60 | 100.00% | 96.67% | 0 |
| provenance | sufficient_dispute_reason | 60 | 100.00% | 100.00% | 0 |

See `summary.json` for all class confusion matrices, per-class precision/recall/F1, per-variant results, and each scenario family's results. Null rates have a zero denominator and are not zero errors.
