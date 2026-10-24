# Dataset and evaluation contract

Release/protocol version 1.2.2; the original main-corpus files retain version 1.0.0 byte for byte. All cases are deliberately fictional. This is a controlled fault-injection and conformance suite, not sampled banking data or recorded foundation-model output.

## Observable episode

`data/cases.jsonl` contains the original 100 objects, twenty scenario families with five variants each. The separate `data/diagnostics/cases.jsonl` contains eight additional objects using the same schema; diagnostic results are reported separately. IDs are opaque stable identifiers. Each has:

- `case_id`: unique string.
- `subject`: an explicitly fictional merchant identifier.
- `sources`: list of `{source_id, kind, version, text}`. Kinds are `contract` and `transactions`; `text` is the actual retained UTF-8 source content.
- `citations`: object with `contract` and `transactions` lists of `{source_id, version, sha256}`. Hashes cover exact UTF-8 text bytes.
- `record`: `{input, policy, trace, rule_output, final_output, override, action_history_complete}`.
- `record.input`: `{disputed, eligible, commitment_months}`; integers, 0 <= disputed <= eligible, eligible > 0, commitment_months >= 0.
- `record.policy`: `{id: "toy-v1", dispute_threshold: {numerator: 1, denominator: 50}, commitment_threshold_months: 6}`. Any other policy version/configuration is unsupported by the reference checker and unresolved.
- `record.trace`: `{dispute_trigger: bool, commitment_trigger: bool}`. Evaluate both predicates; no short-circuit trace convention.
- `record.rule_output`: `manual_review` if disputed / eligible >= 1/50 OR commitment_months < 6, else `standard_processing`.
- `record.final_output`: same enum; may differ from the rule output.
- `record.override`: null or `{from, to, reason}`. A same-valued intervention still counts as an intervention.
- `record.action_history_complete`: boolean. This is a stipulated trusted property of the constructed episode, not evidence that real logs are complete.
- `alternatives`: a nonempty list of nonnegative integer commitment values, or an empty list when candidate analysis is unavailable. All remaining input/state stays fixed.
- `claims`: seven objects `{claim_id, kind, text, asserted_value}`. `kind` is one of the following.

| Kind | Exact scope | Asserted value |
|---|---|---|
| `contract_lineage` | Every cited contract's bytes and version match the retained reference; neither source truth nor semantic accuracy is asserted | true |
| `commitment_grounding` | Unambiguous valid cited contract evidence supports the recorded commitment under the defined penalty-free exit semantics | recorded commitment integer |
| `dispute_grounding` | Unambiguous valid cited transaction evidence supports the recorded disputed/eligible fraction in the fixture window | `{numerator, denominator}` |
| `conditional_execution` | The recorded output and both trace predicates match executing toy-v1 on the recorded inputs | recorded rule output string |
| `final_action_by_rule` | The retained complete action history establishes that the final action was produced by this policy without an intervention | recorded final output string |
| `candidate_stability` | Whether all declared candidate commitments produce the same policy recommendation conditional on the remaining recorded inputs | Boolean; true in the main corpus, true or false in the diagnostic extension |
| `sufficient_dispute_reason` | The dispute predicate alone is sufficient for manual review conditional on recorded inputs and toy-v1; it makes no claim about final human action or source truth | true |

For `candidate_stability`, the reference and checker compare computed stability with the asserted Boolean. A true assertion affirms equal recommendations; a false assertion affirms unequal recommendations. Unavailable candidate analysis remains unresolved for either polarity.

Labels are `supported`, `contradicted`, `unresolved`. A source-grounding label is supported when valid authoritative fixture evidence yields one value equal to the assertion, contradicted when it yields one different value, and unresolved when absent, unusable, or conflicting. In this protocol unresolved evidence means withholding endorsement, not asserting that the claim is false. Known missing source evidence remains unresolved even though the data constructor knows fictional hidden facts.

For final-action attribution, an explicit intervention or a mismatch contradicts the claim. Otherwise missing history completeness makes it unresolved. Supported requires complete stipulated history, no override, valid matching execution, and matching final output. Equal outcomes alone do not support attribution.

## Reference and metadata separation

`data/reference.jsonl` contains `{case_id, labels: {claim_id: label}, rationale: {claim_id: text}}`. It is a construction reference, not an independent human-annotation study. `data/metadata.json` contains `cases` records with `{case_id, scenario_id, split, variant, subtype}` and descriptive corpus metadata. Families 1-8 form the development partition (`dev`); families 9-20 form the reporting partition (`test`); all variants from a family stay together. These legacy identifiers are retained for format compatibility, not to imply a blind test. Both public partitions were inspected during implementation and software validation; no absence of post-inspection development is claimed. The separate extension uses split `diagnostic` and four two-episode families. The public templates and labels preclude treating this as a secret benchmark.

The prediction function receives only sources, citations, record, alternatives and claims. It must not inspect case IDs, subjects, metadata, split/variant information or reference labels. Scoring joins predictions to reference labels only after inference.

## Capability ablations

`execution_only` checks conditional execution, final-action attribution, candidate stability and conditional sufficient reasons. All source claims are unresolved. `provenance` adds contract identity/version/hash checks; grounding stays unresolved. `boundary` additionally parses the supported source language and checks source grounding. All receive the same observable input; differences are disabled capabilities. These are conservative ablations, not competitive trained baselines or evidence of superiority to commercial systems.

Confusion matrices and metrics are reported separately for the seven kinds and three classes, by split and scenario family. A resolved prediction is supported or contradicted. False support means predicting supported when the reference is contradicted or unresolved. Distinguish false-support frequency (denominator all claims) from false-support among endorsements (denominator predicted supported). Coverage alone is not correctness; abstain-all must not be rewarded as perfect accuracy. Synthetic fault frequencies are experimental choices, not deployment estimates.

## Released variants

Each family has `clean`, `extraction_error`, `source_gap`, `ambiguity`, and `intervention`. Errors are injected into consumed features before the deterministic rule is executed; conditional execution remains faithful unless an explicit trace fault is introduced. Source gaps cover missing artifacts, digest mismatches and conflicting evidence. Ambiguity uses commitments on either side of six months; dispute fractions vary by family so some outcomes change and others remain stable. Interventions include outcome-changing overrides, same-valued interventions and incomplete history. Full cases and the 14 non-clean subtypes are described by metadata and DATASET.md. Trace faults flip only the commitment predicate. Four of twenty extraction-error variants change the recommendation relative to their clean counterpart, including two of twelve in the reporting partition.

## Scope of evidence

The deterministic checker evaluates the structured proposition defined by `kind` and `asserted_value`. The `text` field is a human-readable rendering and must agree with that proposition; the checker does not verify arbitrary prose against the structured fields. The supplied generator produces consistent renderings. Free-text explanation entailment is outside the implemented task.

The reference implementation supports bounded, documented source templates. It is not a general natural-language semantic verifier. Every inference must retain its check and evidence references. Causal effects, fairness, authentic source truth, real-world error rates and user review-time benefits are untested. No model was trained or externally invoked to create the original included extraction records. Separately archived assistant audit runs assess these fictional inputs; they do not generate the original records. The later Claude source-only extraction outputs are a separate experiment over existing synthetic documents and do not replace the injected records. Task inputs, emitted structured responses, available tool observations, and disclosed model information are preserved for each run. Further model runs must retain equivalent provenance.
