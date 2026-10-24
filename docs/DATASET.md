# Dataset card

## Purpose and provenance

Release 1.2.2 retains an unchanged main corpus (corpus version 1.0.0), the
separate version-1.1.0 diagnostic extension, and archived assistant audit
predictions over selected existing episodes. The entirely fictional main corpus contains
**20 scenario families, five variants per family, 100 episodes and 700
claim-level reference labels**. The extension adds **eight episodes and 56
claims in four paired diagnostic constructions**; its results are reported
separately and are not pooled into the original main totals.
The underlying corpus contains neither sampled banking data nor recorded model
extractions. Saved assistant audit predictions are a separate release artifact;
they are not the source of the injected extraction records or reference labels.
The merchant identifiers, contract passages, transaction counts, policy,
execution records and interventions were authored for this experiment. No real
organisation, client, personal data, private implementation or commercial
policy was used. The policy is an invented illustrative rule.

The corpus asks whether an audit procedure distinguishes source identity,
semantic grounding, conditional execution, final-action attribution and
conditional candidate stability. It cannot establish model extraction accuracy,
real-world banking error rates, general natural-language understanding, legal
compliance, fairness or causal effects. Fault proportions were chosen by the
authors rather than estimated from deployment.

## Files and regeneration

Run from the repository root:

```sh
python scripts/generate_data.py
```

This uses only the Python standard library and rewrites these files with
deterministic UTF-8 content and LF line endings:

| File | Contents |
|---|---|
| `data/cases.jsonl` | Observable episodes with seven claims each |
| `data/reference.jsonl` | Construction labels and claim-specific rationales |
| `data/metadata.json` | Family/split/variant membership, provenance and totals |
| `data/manifest.json` | SHA-256 digests and byte sizes of the preceding main-corpus files |
| `data/diagnostics/cases.jsonl` | Eight diagnostic episodes using the same observable schema |
| `data/diagnostics/reference.jsonl` | Separate diagnostic labels and rationales |
| `data/diagnostics/metadata.json` | Diagnostic set/polarity membership and totals |
| `data/diagnostics/manifest.json` | Diagnostic file integrity manifest |

Use `--output /path/to/another-directory` to regenerate elsewhere. No system
clock, network connection, external model, private resource or random-number
library is used. A fixed public seed string makes stable opaque IDs; it does
not imply stochastic sampling. IDs have no encoded split or variant marker.
This manifest checks byte integrity, not research validity or source authenticity.

## Construction and splits

Eight families form the development partition (`dev`, 40 episodes); the other
twelve form the reporting partition (`test`, 60 episodes). These legacy labels
are retained for format compatibility. All five variants of a family stay
together. Metadata is separate from predictor input and references are joined
only after predictions. Both partitions and their labels were inspected during
implementation and validation. They serve conformance development and reporting,
not blind testing or an assessment of generalisation. Component values and
source grammars recur across partitions. Variants are dependent within a family;
family summaries are descriptive and the main corpus is a designed fixture suite.

The main corpus uses this exact parameter grid:

| Component | Released values |
|---|---|
| Source disputed/eligible counts | 15/800, 20/1000, 25/1200, 25/1500, 45/2000 |
| Source penalty-free commitment (months) | 3, 5, 6, 9, 12, 18 |
| Service-framework duration (months) | 24, 36, 48 |
| Supported contract forms | The three literal templates below |
| Transaction form | One literal template below |
| Observation window | 2026-01-01/2026-01-31 |

For family index `i = family_number - 1`, source count pairs cycle with `i % 5`,
commitments with `i % 6`, and frameworks and contract templates with `i % 3`.
This is a cyclic parameter assignment over 20 families, not a full factorial
design or a diversity claim. Framework duration and commitment are distinct
quantities.
The invented rule recommends `manual_review` when the dispute fraction is at
least 1/50 or commitment is shorter than six months; otherwise it recommends
`standard_processing`. Exact integer cross multiplication avoids floating-point
threshold artifacts. Manual review is a workflow recommendation, not an adverse
financial decision.

| Variant | Episodes | Construction |
|---|---:|---|
| `clean` | 20 | Correct consumed values, retained sources, faithful rule execution |
| `extraction_error` | 20 | Framework duration substituted for commitment, or disputed count incremented; execution uses the faulty consumed feature faithfully |
| `source_gap` | 20 | Cycles through missing contract, missing transactions, conflicting contracts, bad contract hash, wrong contract version and human-clear unsupported wording |
| `ambiguity` | 20 | Equally authoritative contracts specify three and nine months; policy recommendations may change or stay equal depending on the dispute predicate |
| `intervention` | 20 | Five each: changed-output override, same-valued logged intervention, incomplete history, and an inconsistent recorded trace predicate |

The 14 non-clean subtype counts are exact and describe the entire injected
fault/ambiguity model (the clean `faithful_record` subtype adds 20 episodes):

| Non-clean subtype | Development (`dev`) | Reporting (`test`) | Total |
|---|---:|---:|---:|
| `framework_duration_as_commitment` | 4 | 6 | 10 |
| `disputed_count_increment` | 4 | 6 | 10 |
| `missing_contract` | 2 | 2 | 4 |
| `missing_transactions` | 2 | 2 | 4 |
| `conflicting_contracts` | 1 | 2 | 3 |
| `invalid_contract_hash` | 1 | 2 | 3 |
| `wrong_contract_version` | 1 | 2 | 3 |
| `unsupported_worded_contract` | 1 | 2 | 3 |
| `conflicting_commitments_sensitive` | 3 | 5 | 8 |
| `conflicting_commitments_stable` | 5 | 7 | 12 |
| `changed_output` | 2 | 3 | 5 |
| `same_valued_intervention` | 2 | 3 | 5 |
| `incomplete_history` | 2 | 3 | 5 |
| `trace_fault` | 2 | 3 | 5 |

Of the 20 extraction-error episodes, four change the policy recommendation
relative to the clean counterpart; two of the twelve in the reporting partition
do so. The other injected extraction errors change a grounded value while the
policy recommendation remains equal. This narrow fault model excludes most
possible real extraction, trace, document, and human-action failures.

`source_gap` is an authoring category, not an input to the checker. Its
`unsupported_worded_contract` subtype deliberately contains **sufficient semantic
evidence** but exceeds the released numeric parser's capability. Thus a source
grounding reference label can be `supported` while the bounded implementation
returns `unresolved`. This is an intentional abstention example, not a mislabeled
missing-source case. Three such cases exist, one in dev and two in test.

Trace-fault episodes flip the recorded commitment predicate while retaining the
correct recommendation and final output. Conditional execution is contradicted;
final-action attribution remains unresolved because the inconsistent execution record
cannot establish provenance of the action. A logged same-valued intervention
contradicts a claim of intervention-free attribution even when outcomes match.
With absent overrides and incomplete history, attribution is unresolved.

## Exact retained source language

`N` denotes a numeric commitment and `F` a numeric framework duration. Each
contract uses one of these supported literal templates:

```text
Minimum penalty-free cancellation time: N months.
Service framework duration: F months.
```

```text
The service framework lasts F months. The merchant may terminate after N months without penalty.
```

```text
Penalty-free termination is available once N months have elapsed. Framework duration: F months.
```

The deliberately unsupported form is:

```text
The minimum penalty-free cancellation time is eighteen months. The service framework lasts 48 months.
```

The number-word is generated from a finite vocabulary; the current three such
fixtures use eighteen. A human reader can recover the stipulated penalty-free
commitment, but the documented bounded numeric parser declines this grammar.
The observation window and transaction template are exactly:

```text
Observation window: 2026-01-01/2026-01-31
Eligible transactions: E
Disputed transactions: D
```

Sources are minimal snippets, without distractor passages or real document
layout. All supported grammars appear in both splits. This is not a held-out
language or OCR benchmark. Source IDs, versions and exact-text SHA-256 hashes
allow lineage checks, but a matching hash does not prove that a real contract is
genuine, true, complete or legally authoritative.

## Separate candidate-stability diagnostic extension

The original ambiguity variants all declare candidate commitments `{3,9}`.
Within those variants, a stable recommendation is obtained exactly when the
dispute predicate forces review, so those cases alone cannot distinguish
candidate stability (c6) from the sufficient-dispute-reason predicate (c7).
The extension fixes the dispute count pair to 25/1500 (below the threshold) and
adds candidate sets that exercise different stability outcomes:

| Candidate set (months) | True stability value | c6 asserting true | c6 asserting false | c7 asserting sufficient dispute reason |
|---|---|---|---|---|
| `{6,9}` | true | supported | contradicted | contradicted |
| `{3,5}` | true | supported | contradicted | contradicted |
| `{3,6,9}` | false | contradicted | supported | contradicted |
| `{6,9,12}` | true | supported | contradicted | contradicted |

Each row contributes two episodes, with positive and negative c6 assertions.
Each diagnostic retains conflicting valid contracts for the declared candidates, so commitment grounding (c2) remains unresolved; candidate stability is still checkable. The eight episodes and 56 labels have separate files and results, and use the
metadata partition label `diagnostic`. Their four pairs are authored logical
checks, not independent samples. They test non-equivalence of c6 and c7 and
whether the checker honours the asserted Boolean; they add no external
validation, natural-language diversity, or foundation-model evidence.

Run the extension on its own with:

```sh
python -m boundarybench diagnostics --data-dir data/diagnostics --output results/diagnostics
```

The main reproduction command also writes this separate report. Original
main-corpus data and manifests remain byte-identical to version 1.0.0. The
release/code version is now 1.2.2; the main-corpus identifier should be retained when
reporting the original results.

## Pilot selections and image presentation

The version-1.2.0 pilot audits the same 60 main reporting episodes (420 claims)
and eight diagnostic episodes (56 claims), with each group scored separately.
A paired 12-episode main-corpus subset (84 claims) is also presented with source
text rendered as PNG cards. This changes source presentation only; it does not
create new merchants, documents, reference annotations, or independent cases.
Images of synthetic text are not evidence of performance on natural scanned
banking documents, OCR variation, or new visual data.

Fixed prompts, selected episode IDs, source cards, integrity observations, and
join metadata are archived under `data/pilot/`. Saved assistant responses,
model-run disclosure, and scores are under `results/pilot/`. The assistant sees
opaque episode handles for returning answers, but no reference labels or
construction subtype/split tags. See [PILOT.md](PILOT.md) for inference isolation,
tool assistance, and reproduction limits.

## Labels and assumptions

Release 1.2.2 also archives a separately supplied Claude extraction study over
25 distinct existing source documents: 20 contracts and five transaction
summaries. Each source is presented once as text and once as a mildly degraded
rendered image. Target fields come from the authored templates; they are not
new human annotations. These documents do not add independent main episodes,
and their extracted outputs do not replace the original injected inputs.
See [CLAUDE_EVALUATION.md](CLAUDE_EVALUATION.md) for task and scoring details.

The seven claim scopes and schemas are specified in [CONTRACT.md](CONTRACT.md).
Each reference label is `supported`, `contradicted` or `unresolved` with a written
rationale. The generator does not import the checker or use its predictions.
Source-grounding labels derive from the semantics stipulated when the passages
are authored, and execution labels use a separate complementary-condition
calculation. This is a **construction reference**, not independently collected
human annotations or empirical proof that an audit system generalises.

The authoring process does not resolve missing or conflicting evidence using
hidden fictional facts. A missing artifact yields unresolved grounding. A
matching unique usable value yields supported grounding; a unique different
value yields contradicted grounding. Valid conflicting contract values yield
unresolved grounding. A digest/version mismatch contradicts lineage but makes
source grounding unresolved. A wrong extracted value can coexist with supported
conditional execution.

Dispute grounding asserts fraction equality, tested by cross multiplication,
rather than separate exact counts. Candidate stability refers only to declared
commitments with all other consumed inputs fixed. It neither asserts exhaustive
coverage of all plausible interpretations nor recommends a real-world action.
Missing candidate analysis is unresolved. Source authority and complete action
history are explicit trusted fixture assumptions; no mechanism here proves
those properties for real deployments.

The public inference function must not read case identifiers, subjects,
scenario/split/variant metadata or reference labels. Public availability does
not prevent another implementation from abusing these files, so a published
evaluation must disclose its procedure and data access. Model adapters should
also retain actual raw outputs, prompt, version and runtime settings and report
observed model failures separately from these injected failures.

## Interpretation of results

Report class/kind confusion matrices, endorsement errors and resolved coverage
together. Returning unresolved on everything is a useful control, not perfect
accuracy. Do not interpret conservative capability ablations as competitive
commercial baselines. Aggregate by scenario family and disclose the small,
constructed sample. A zero error count on these fixtures is not a guarantee for
unseen cases. Even on the numeric fixtures, parser success is bounded by the
documented grammar. Reported numbers must identify the corpus version and
release-manifest digests.
