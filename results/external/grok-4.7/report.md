# Foundation-model evaluation of the MFMB 2026 claim contract

**Paper:** Claim-Scoped Auditing for Foundation-Model-Assisted Banking Pipelines: A Synthetic Conformance Study  
**Release judged:** explainability-boundaries 1.1.0  
**System in this file:** Grok 4.7  
**Date:** 4 October 2026  
**Purpose:** Fill the paper’s stated gap that no foundation model was run, in a form that can sit beside OpenAI and Claude runs on the same frozen task.

This file does not replace the paper’s conformance results. The bundled checker remains the implementation under test. These numbers are an external-model run against the authored references.

## What was evaluated, and what was not

The limitation in Section 5 lists six unevaluated items. Only one is testable on the released artifact.

| Limitation | Testable on release 1.1.0? | This run |
|---|---|---|
| Foundation-model performance | Yes, as claim audit on the supplied records | Evaluated. See primary table. |
| Multimodal input | No. Sources are short UTF-8 strings, not page images or PDFs. | Not evaluated. Leave blank for other systems unless new inputs are added. |
| Causal actionability | No. Candidate sets are declared sensitivity checks. The paper already excludes a causal reading. | Not evaluated. |
| Fairness | No. Merchants are fictional and carry no protected attributes. | Not evaluated. |
| Compliance | No. No control, regulation, or policy mapping is in the release. | Not evaluated. |
| Reviewer benefit | No human subjects. | Not evaluated. A proxy note is included below and is not a benefit estimate. |

Do not impute a score for a blank cell. A later OpenAI or Claude run should fill the same cells or leave them null.

## Protocol other systems must share

Protocol id: `mfmb2026-audit-supplied-claims-v1`.

The official exporter is `python -m boundarybench export-prompts --split test`. Each episode is one call. The model sees sources, citations, the execution record, declared alternatives, and the seven claims. It does not see case id, subject, split, variant, subtype, reference labels, or construction rationales.

Labels are `supported`, `contradicted`, or `unresolved`. The policy is toy-v1: manual review if `50 * disputed >= eligible` or `commitment_months < 6`, else standard processing. Hash checks and exact replay may use tools. Tool use has to be declared. A run with no hash tool should mark lineage unresolved rather than guess digests.

Primary split: the public reporting partition, 60 episodes, 420 claims. Secondary split: the eight diagnostic episodes, 56 claims, reported separately and not pooled. Metrics, matching the paper: agreement with the authored reference, resolution (supported or contradicted), false support among endorsements (predicted supported when the reference is contradicted or unresolved).

This split was inspected by the authors during development. It is not a blind benchmark. Templated contracts dominate. High agreement is expected from any system that follows the instructions and uses the same tools.

## Grok 4.7 run card

- Run id: `grok-4.7-audit-supplied-claims-v1`
- Interface: this session, under the frozen instructions in `boundarybench/external.py`
- Sampling: not a sampled decode. The instructions were applied uniformly, with SHA-256 of the retained UTF-8 text and exact integer replay available on every case
- Reference file: not read until scoring
- Checker code: not imported. Predictions were written first, then scored with `python -m boundarybench score`
- Raw predictions: `fm_eval/grok_predictions_main.jsonl`, `fm_eval/grok_predictions_diagnostics.jsonl`
- Official score dump: `fm_eval/score_test/summary.md`

## Primary result, reporting split

| System | Tools | Agreement | Resolved | False support / endorsements |
|---|---|---:|---:|---:|
| Bundled boundary checker (paper Table 3) | parser, hash, replay | 418/420 | 386/420 | 0/331 |
| Grok 4.7 | hash, exact replay, open numeric reading | 420/420 | 388/420 | 0/333 |
| OpenAI |  |  |  |  |
| Claude |  |  |  |  |

Grok endorsements are 333 supported predictions. Resolved claims are 388 (333 supported, 55 contradicted). The remaining 32 are unresolved. Agreement on resolved claims is 388/388. False support is 0/333.

By kind, all 60 reporting episodes:

| Kind | Agreement | Resolved | Supported | Contradicted | Unresolved |
|---|---:|---:|---:|---:|---:|
| Contract lineage | 60/60 | 58 | 54 | 4 | 2 |
| Commitment grounding | 60/60 | 40 | 34 | 6 | 20 |
| Dispute grounding | 60/60 | 58 | 52 | 6 | 2 |
| Conditional execution | 60/60 | 60 | 57 | 3 | 0 |
| Final rule attribution | 60/60 | 54 | 48 | 6 | 6 |
| Candidate stability | 60/60 | 58 | 52 | 6 | 2 |
| Sufficient dispute reason | 60/60 | 60 | 36 | 24 | 0 |

The paper’s checker agrees with the reference on 418/420 and with these labels on 418/420. The two disagreements are the only model-versus-parser difference on this split.

| Case | Source sentence | Asserted commitment | Bundled checker | Grok 4.7 | Authored reference |
|---|---|---:|---|---|---|
| `case_75c52dd0d7f2eb82` | “The minimum penalty-free cancellation time is eighteen months.” | 18 | unresolved | supported | supported |
| `case_b5d5d07bc025f241` | same sentence | 18 | unresolved | supported | supported |

Both citations match the retained bytes. The bundled parser abstains because “eighteen” is outside its numeric grammar. A model that can read the sentence supports the assertion. That is the extraction-integration gap the paper describes, on the only linguistic variant in the release. It is not evidence about unseen legal language.

## Diagnostic split, not pooled

Eight episodes, candidate sets `{6, 9}`, `{3, 5}`, `{3, 6, 9}`, `{6, 9, 12}`, each with a true and a false stability assertion, at `u = 25`, `n = 1500`. Grok agrees with all 56 authored labels. False support is 0. The paper’s checker also matches 56/56. No model-versus-parser difference appears here, because these episodes do not use the worded-number template.

| System | Agreement | False support |
|---|---:|---:|
| Bundled boundary checker | 56/56 | 0 |
| Grok 4.7 | 56/56 | 0 |
| OpenAI |  |  |
| Claude |  |  |

## How to read the perfect score

420/420 does not mean the contract has been independently validated, and it does not mean a foundation model audits banking pipelines. The references and the task definition encode the same rules. The inputs are three numeric templates plus one worded sentence, one transaction template, and injected faults. A system that implements those rules will match. The informative result is the two-claim delta: open reading resolves the abstentions the bounded parser is specified to leave unresolved, without a false endorsement on this split.

Conditions that would make a later run non-comparable:

- different split, or pooling diagnostics into the 420
- hash or replay tools used on some episodes only
- reference labels, variant names, or subtypes present in the prompt
- a sampled decode reported as if it were this deterministic procedure
- accuracy computed only on resolved claims, without the endorsement denominator

## Reviewer-proxy notes

These are not a reviewer study. They record whether the retained bundle, read under the contract, identifies the fault a reviewer would have to ask about. Other systems can add a column. Do not average these into a benefit number.

| Episode | Observable fault | Scope a reviewer can settle from the bundle | Still unresolved |
|---|---|---|---|
| `case_75c52dd0d7f2eb82` | Worded commitment, valid citation | Commitment grounding, once the sentence is read | Nothing in this episode |
| `case_96101184a60febe1` | Cited contract digest is zeros | Lineage contradicted; grounding unresolved | Whether a true document exists outside the bundle |
| `case_7ca91a566f45a47a` | Two valid contracts, 3 and 9 months | Lineage supported; grounding unresolved | Which contract controls |
| `case_45cefda2b29cd619` | Contract cited but not retained; empty candidates | Grounding and stability unresolved; replay still supported | The missing agreement |
| `case_ac1cc51279b6ef89` | Same-valued reviewer confirmation | Attribution contradicted; replay supported | Why the reviewer confirmed |
| `case_89d21a7a98be486c` | History completeness false; trace matches | Attribution unresolved; replay supported | Whether an intervention occurred |

## Blank cells for the other limitations

Fill only if the run actually changes the inputs or the population. Otherwise leave null.

| Dimension | Shared rule | Grok 4.7 | OpenAI | Claude |
|---|---|---|---|---|
| Multimodal claim audit | Score only if the input is a page image or PDF the release does not contain | not evaluated |  |  |
| Causal actionability | Do not score declared candidate sensitivity as an intervention effect | not evaluated |  |  |
| Fairness | Do not score without a declared protected attribute and a base rate | not evaluated |  |  |
| Compliance | Do not score without a named control and an evidence mapping | not evaluated |  |  |
| Reviewer benefit | Human subjects only; proxy notes stay qualitative | not evaluated |  |  |

## Adding an OpenAI or Claude run

1. Export prompts with `python -m boundarybench export-prompts --split test --output model-inputs.jsonl`. Repeat for a diagnostic export from `data/diagnostics/cases.jsonl` if the exporter is pointed at that file, or send those eight observables under the same instructions.
2. Send only `messages`. Keep `case_id` locally for the join.
3. Record model snapshot, date, temperature, tool list, and raw responses.
4. Convert to JSONL objects `{case_id, method, claims: [{claim_id, kind, label}]}`.
5. Score with `python -m boundarybench score --predictions <file> --split test --output <dir>`.
6. Append a system object to `fm_eval/systems.json`. Do not edit the Grok row. Do not pool diagnostic claims into the 420.

Machine-readable merge file: `fm_eval/systems.json`. Protocol card: `fm_eval/protocol.json`.
