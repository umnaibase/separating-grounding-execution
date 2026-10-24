# Archived assistant pilot

All figures below are scored from archived literal assistant outputs. Conditions and corpora remain separate; no combined 68-episode accuracy is reported.

| Corpus / condition | Episodes | Claims | Failure-adjusted agreement | Ordinary agreement | Failed claims | False support / endorsements |
|---|---:|---:|---:|---:|---:|---:|
| main_reporting | 60 | 420 | 100.00% | 100.00% | 0 | 0 / 333 |
| diagnostics | 8 | 56 | 100.00% | 100.00% | 0 | 0 / 36 |
| paired_text | 12 | 84 | 100.00% | 100.00% | 0 | 0 / 68 |
| paired_image | 12 | 84 | 100.00% | 100.00% | 0 | 0 / 68 |

## Helper-sensitive and reasoning scopes

| Corpus / condition | Scope | Claims | Failure-adjusted agreement | Failed claims | False support |
|---|---|---:|---:|---:|---:|
| main_reporting | lineage_c1 | 60 | 100.00% | 0 | 0 |
| main_reporting | six_reasoning_scopes | 360 | 100.00% | 0 | 0 |
| main_reporting | source_grounding_c2_c3 | 120 | 100.00% | 0 | 0 |
| diagnostics | lineage_c1 | 8 | 100.00% | 0 | 0 |
| diagnostics | six_reasoning_scopes | 48 | 100.00% | 0 | 0 |
| diagnostics | source_grounding_c2_c3 | 16 | 100.00% | 0 | 0 |
| paired_text | lineage_c1 | 12 | 100.00% | 0 | 0 |
| paired_text | six_reasoning_scopes | 72 | 100.00% | 0 | 0 |
| paired_text | source_grounding_c2_c3 | 24 | 100.00% | 0 | 0 |
| paired_image | lineage_c1 | 12 | 100.00% | 0 | 0 |
| paired_image | six_reasoning_scopes | 72 | 100.00% | 0 | 0 |
| paired_image | source_grounding_c2_c3 | 24 | 100.00% | 0 | 0 |

## Claims by kind

| Corpus / condition | Kind | Claims | Failure-adjusted agreement | Failed claims | False support |
|---|---|---:|---:|---:|---:|
| main_reporting | candidate_stability | 60 | 100.00% | 0 | 0 |
| main_reporting | commitment_grounding | 60 | 100.00% | 0 | 0 |
| main_reporting | conditional_execution | 60 | 100.00% | 0 | 0 |
| main_reporting | contract_lineage | 60 | 100.00% | 0 | 0 |
| main_reporting | dispute_grounding | 60 | 100.00% | 0 | 0 |
| main_reporting | final_action_by_rule | 60 | 100.00% | 0 | 0 |
| main_reporting | sufficient_dispute_reason | 60 | 100.00% | 0 | 0 |
| diagnostics | candidate_stability | 8 | 100.00% | 0 | 0 |
| diagnostics | commitment_grounding | 8 | 100.00% | 0 | 0 |
| diagnostics | conditional_execution | 8 | 100.00% | 0 | 0 |
| diagnostics | contract_lineage | 8 | 100.00% | 0 | 0 |
| diagnostics | dispute_grounding | 8 | 100.00% | 0 | 0 |
| diagnostics | final_action_by_rule | 8 | 100.00% | 0 | 0 |
| diagnostics | sufficient_dispute_reason | 8 | 100.00% | 0 | 0 |
| paired_text | candidate_stability | 12 | 100.00% | 0 | 0 |
| paired_text | commitment_grounding | 12 | 100.00% | 0 | 0 |
| paired_text | conditional_execution | 12 | 100.00% | 0 | 0 |
| paired_text | contract_lineage | 12 | 100.00% | 0 | 0 |
| paired_text | dispute_grounding | 12 | 100.00% | 0 | 0 |
| paired_text | final_action_by_rule | 12 | 100.00% | 0 | 0 |
| paired_text | sufficient_dispute_reason | 12 | 100.00% | 0 | 0 |
| paired_image | candidate_stability | 12 | 100.00% | 0 | 0 |
| paired_image | commitment_grounding | 12 | 100.00% | 0 | 0 |
| paired_image | conditional_execution | 12 | 100.00% | 0 | 0 |
| paired_image | contract_lineage | 12 | 100.00% | 0 | 0 |
| paired_image | dispute_grounding | 12 | 100.00% | 0 | 0 |
| paired_image | final_action_by_rule | 12 | 100.00% | 0 | 0 |
| paired_image | sufficient_dispute_reason | 12 | 100.00% | 0 | 0 |

The pre-existing reporting-source subgroup containing the phrase ‘eighteen months’ has 2 commitment-grounding claims; its failure-adjusted agreement is 100.00% and false-support count is 0. This is reported separately because it lies beyond the released checker's numeric source grammar.

Malformed or missing batches are converted wholly to unresolved, marked as conversion failures, and retained in the denominator. Every converted claim counts as incorrect in the primary failure-adjusted measure, including when its reference is unresolved. Ordinary three-label agreement is secondary; raw files are neither repaired nor retried.

Limitations: Same assistant system as author; not independent annotation or blind model selection. Exact model identity and sampling settings may be unavailable; use archived run metadata. Tool-assisted citation integrity; no tool computed model claim labels. Seventeen episodes share each primary-text context; six share each matched-text or image context. No per-case isolation is claimed. Images render the same source passages with the populated record unchanged; this is not an extraction accuracy experiment. Tool restrictions are instructions with worker-reported protocol compliance; complete tool traces were not independently audited, not a technical sandbox. These are designed fixtures, not a sampled financial deployment population.
