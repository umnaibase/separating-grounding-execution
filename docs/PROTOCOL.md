# Evaluation protocol

Release/protocol version 1.2.2; original main-corpus version 1.0.0 is preserved. The normative record and claim definitions are in [CONTRACT.md](CONTRACT.md).

## Research question

Can a structured audit distinguish evidence that a source was retained, evidence that an extraction is supported, evidence that a rule was faithfully executed, and evidence explaining the final action? A second question is whether a recommendation remains unchanged across explicitly supplied candidate inputs despite unresolved source interpretation.

The original deterministic evaluation operationalizes these distinctions using controlled examples. It tests a reference checker against construction labels and shows the resolution contributed by enabling successive checking capabilities. Later assistant runs measure agreement on the same authored fixtures; they do not estimate deployment accuracy or establish superiority of a proprietary architecture.

## Unit of analysis and construction

The unchanged main corpus has 20 fictional scenario families. Each family contributes five variants and each variant contributes seven claims, yielding 100 episodes and 700 claim instances. Release 1.1.0 adds a separate eight-episode, 56-claim diagnostic extension; its results are never pooled into the main-corpus denominators. The five variant types are:

| Type | Manipulation | Purpose |
|---|---|---|
| Clean | Retained sources agree with the recorded numerical values | Check supported evidence and conditional execution |
| Extraction error | A consumed value is deliberately changed before rule execution | Separate erroneous grounding from faithful execution |
| Source gap | An artifact is absent, a digest disagrees, or authoritative evidence conflicts | Distinguish identity checks from semantic support and unresolved evidence |
| Ambiguity | Declared candidate commitments lie on either side of six months | Check whether uncertainty affects the recommendation under fixed other inputs |
| Intervention | An override, incomplete history, or inconsistent commitment trace is recorded | Separate matching outcomes from final-action attribution and trace conformance |

Exact family assignments and the 14 non-clean subtypes are recorded in `data/metadata.json` and enumerated in [DATASET.md](DATASET.md). Source parameters cycle through five count pairs (15/800, 20/1000, 25/1200, 25/1500, 45/2000), six commitment values (3, 5, 6, 9, 12, 18 months), three frameworks (24, 36, 48 months), three contract templates, and one observation window. This is a cyclic fixture grid, not a full factorial design or a sample of financial documents. Only four of 20 injected extraction errors change the recommendation relative to the corresponding clean case; two of twelve do so in the reporting partition. All five trace faults flip only the recorded commitment predicate, retaining the recommendation and final output. The small corpus is designed to cover logical distinctions, not to match population demographics, transaction distributions, or error prevalence. The generator's latent fictional facts are not automatically evidence available to an auditor. In particular, absent or conflicting source evidence is labelled unresolved even when the constructor could supply an answer.

## Decision procedure

For nonnegative disputed count `d`, positive eligible count `n`, and nonnegative commitment `c`, toy-v1 recommends manual review when `50*d >= n` or `c < 6`; otherwise it recommends standard processing. Integer arithmetic avoids floating-point boundary drift. Both predicates appear in the trace regardless of whether one alone determines the outcome.

The final action is recorded separately and may include an intervention. A same-valued intervention still breaks an assertion that the policy alone produced the final action. If no intervention is recorded but action-history completeness is unknown, this attribution is unresolved. Completeness is explicitly stipulated by the fixture, not inferred from the absence of a log entry.

## Claim semantics and reference answers

The claims concern contract lineage, commitment grounding, dispute grounding, conditional execution, final-action attribution, candidate stability, and a sufficient dispute reason. Each claim is deliberately narrow. The exact definitions in CONTRACT.md take precedence over informal wording.

For reference labels, `supported` means the retained evidence establishes the specified claim under this protocol, `contradicted` means that evidence establishes a conflicting result, and `unresolved` means that the available evidence is insufficient to decide. A checker can also predict unresolved because its capabilities or source language are limited, even when the reference is supported. The three worded-number fixtures deliberately demonstrate that distinction. Unresolved is not a synonym for false.

Construction labels and their rationales are stored separately from observable inputs. These are deterministic reference answers, not blind human annotations or independently sampled truth. Agreement measures internal conformance. Code review and targeted adversarial tests improve implementation assurance but do not substitute for independent external validation.

## Source identity and bounded source interpretation

Sources retain their complete UTF-8 text, type, identifier, and version. Citations include identifiers, versions, and SHA-256 digests of the exact source text. The lineage check verifies agreement with this retained representation. It cannot establish authenticity, real-world correctness, or absence of omitted documents.

The grounding checker parses only the documented fixture language. An unrecognized or ambiguous construction should produce an unresolved grounding result. Paraphrasing sources outside that language changes the task; it is not evidence that a general-purpose language model failed or succeeded. Conflicting authoritative values remain unresolved. Numerical commitments use the fixture's penalty-free exit semantics, which are experimental definitions rather than legal contract interpretation.

## Split and inference boundary

Families 1–8 form a development partition and families 9–20 a reporting partition. The legacy metadata labels `dev` and `test` are retained solely for format compatibility. All variants within a family share a partition, while templates and component parameter values recur across partitions. Both partitions were inspected during implementation and validation. This organization serves conformance development and reporting; it is not a blind test, an unseen-language evaluation, or evidence of generalisation. No preregistration or absence of post-inspection development is claimed.

Prediction receives only sources, citations, record, alternatives, and claims. Case identifiers are retained for joining outputs, never as predictive features; subjects, variant tags, split metadata, and reference labels are excluded from inference. Scoring occurs afterwards. The public repository contains labels for reproducibility, so an external participant must separately enforce its own evaluation discipline.

## Capability ablations

All methods receive the same observable evidence. `execution_only` handles the four checks over the recorded decision state. `provenance` adds the contract identity/version/digest check. `boundary` adds grounding checks over supported source templates. An unavailable capability emits unresolved.

This design isolates what each implemented capability resolves. It is not a comparison between equal-capability competitors, and the deliberately conservative ablations are not representative of all logging, provenance, or foundation-model systems. An ordinary log containing sufficient fields could support a suitably implemented checker too. The artifact's contribution is explicit claim scope and checkability, not an exclusive claim to particular record contents.

## Metrics

For each claim let `y` be its reference label and `p` its prediction. Report counts as well as ratios, with an undefined ratio represented as null rather than a fabricated zero when its denominator is zero.

| Metric | Definition |
|---|---|
| Three-class accuracy | Number of predictions equal to their reference / all claims |
| Resolution coverage | Number predicted supported or contradicted / all claims |
| False-support frequency | Number predicted supported with reference contradicted or unresolved / all claims |
| False support among endorsements | Number predicted supported with reference contradicted or unresolved / number predicted supported |
| Resolved-prediction accuracy | Number of correct supported/contradicted predictions / number predicted supported or contradicted |
| Confusion matrix | Counts for each reference-label and predicted-label pair, including unresolved |

Report aggregates by method and split, and break down by claim kind and scenario family. Aggregate accuracy can obscure which boundary failed. Coverage is not correctness, and low false support can arise from abstention. An abstain-all method earns credit only for reference-unresolved cases in three-class accuracy and has zero resolution coverage; it cannot be treated as a perfect audit.

Variants share their family's source and numerical structure. Do not calculate uncertainty as though the 100 episodes or 700 claims were independent population samples. If exploratory intervals are added later, resample whole families within the relevant split, report the procedure and number of families, and describe the intervals as variation within this constructed design. They do not justify population inference. The release's family summaries are descriptive.

## Reproduction procedure

1. Record the release version and the local Python version.
2. Validate the released dataset's file integrity, identifier links, annotation coverage and family/variant structure. This command is not a complete validator for arbitrary records against every field in the contract.
3. Run the tests.
4. Regenerate data in a separate directory and compare the released files with the regenerated files.
5. Run all three methods over the same observable main-corpus cases and report the diagnostic extension separately.
6. Join predictions to reference labels only in the scorer.
7. Inspect aggregate, split, claim-kind, and family results together with individual check evidence.

The README provides the exact executable commands. Deterministic regeneration reproduces the designed corpus; it does not introduce new independently sampled evidence.

## Separate candidate-stability diagnostics

The original ambiguity variant always declares `{3,9}` months. In that restricted subcorpus, candidate stability holds exactly when the fixed dispute predicate forces manual review. Those examples alone therefore cannot distinguish a general candidate-stability calculation from simply checking the dispute predicate.

Release 1.1.0 adds four explicitly authored candidate sets, with fixed consumed dispute counts 25/1500 (below threshold):

| Declared candidates (months) | Policy outcomes across candidates | Stable? |
|---|---|---|
| `{6,9}` | Standard processing for both | true |
| `{3,5}` | Manual review for both | true |
| `{3,6,9}` | Manual review and standard processing | false |
| `{6,9,12}` | Standard processing for all | true |

For each set there are two episodes, differing in whether claim c6 asserts stability (`true`) or its negation (`false`). This yields eight episodes, 56 claims, and four paired diagnostic families. A Boolean assertion is supported when it matches computed stability and contradicted when it does not. Claim c7 always positively asserts that the dispute predicate is sufficient; it is contradicted throughout because 25/1500 is below threshold. This makes c6 and c7 non-equivalent while exercising both Boolean polarities.

Each diagnostic retains conflicting valid contracts for the declared candidates, so commitment grounding (c2) remains unresolved; candidate stability is still checkable. The extension has its own `diagnostic` metadata label, integrity manifest, predictions, and results. Its original deterministic evaluation addresses a known construction limitation; it is not a hidden holdout, independent replication, or evidence of generalisation. Later assistant audits of these diagnostics are reported separately. The paired episodes are deliberately dependent. Main-corpus files and headline deterministic results remain unchanged.

## Archived assistant audit pilot

Version 1.2.0 added the tool-assisted same-model assistant pilot, now identified
by the user-supplied display name GPT-6.1 Sol Ultra and documented in
[PILOT.md](PILOT.md). It scores 60 existing main reporting episodes and eight
diagnostics separately, and compares text and image-source presentations for
12 paired main episodes. Primary text uses four 17-episode contexts; matched
text and image conditions each use two fresh six-episode contexts in identical
case order. The assistant is given citation-integrity observations
but no semantic frontend labels or computed policy answers. It assigns all
seven labels; reference labels and checker code are not supplied, and inference instructions prohibit accessing them.

Fresh contexts and frozen prompts reduce direct answer-key exposure during the
run, but do not create independent validation: the authoring and evaluating
assistant use the same model environment, the protocol is synthetic and public,
and its semantics were developed in the same project. The exact model snapshot
and sampling parameters are unavailable. Offline rescoring of preserved outputs
is reproducible; live model inference is not guaranteed to be bit-identical.
Worker activity logs are self-reports; complete tool traces were not
independently audited. A malformed or missing response fails its entire
scheduled batch without retry or repair. All claims retain their denominators;
primary failure-adjusted agreement counts converted claims as wrong even when
the fallback unresolved label matches the reference. Report lineage c1
separately from the other six scopes and report source grounding c2–c3 as a
subset of those scopes.

Report observed errors, abstentions, subgroup counts, and paired disagreements
without converting a small author-associated pilot into a deployment claim.

## Externally supplied predictions

Release 1.2.2 preserves the original Grok 4.7 aggregate report and a later
claim-level prediction/protocol submission. Local rescoring verifies the
supplied labels and is marked `supplied_predictions_locally_rescored`; model
execution is not independently verified. The declared uniform procedure,
single-case calls, and hash-plus-exact-replay assistance differ from the GPT
pilot. Claude Fable 5.1 supplies raw responses and predictions for separate
audit conditions without computational tools and with SHA-256/integer-arithmetic
tools. The provider reports fresh per-episode agents, instruction-based tool
restrictions, default sampling, and a configured identity that is not attested.
The operator had already seen the answer key and checker. Local rescoring
verifies saved labels and conversion, not those execution properties.
These are provenance-labelled separate runs, not a matched model ranking or
a causal estimate of tool access.
See [MODEL_COMPARISON.md](MODEL_COMPARISON.md).

The separately supplied Claude extraction task presents one existing synthetic
source document at a time, as text or a mildly degraded rendered image,
without consumed inputs or audit records. Typed field matching and supporting
quote matching are different measures: report exact-character and
whitespace-normalized quote checks separately. This source-only extraction
task does not integrate the extracted fields into a subsequent policy decision.
See [CLAUDE_EVALUATION.md](CLAUDE_EVALUATION.md).

## Further foundation-model study

The prompt exporter prepares an audit task over these fictional observations and claims without reference labels. It performs no external inference. To evaluate a model, preserve the model identifier/version, prompt bytes, sampling parameters, raw outputs, conversion procedure, failure handling, number of attempts, and run dates. Set the retry/error policy before the run and retain unsuccessful cases.

Keep such results separate from the bundled controlled injections. An extraction study requires a different prompt that exposes source documents but withholds the consumed extraction, reference labels, and fault metadata. It also needs an explicit output schema and a policy for unavailable or ambiguous evidence. Repeated calls and sensitivity to paraphrase would then be additional experiments, not properties demonstrated by the present corpus.

## Claims supported by this artifact

Results can support statements about the implemented checker's agreement with the defined labels on these controlled cases, the consequences of disabling particular checks, and conditional stability across declared alternatives. Archived assistant and supplied-prediction scores support fixture-specific label-agreement claims with their stated provenance limits. They cannot support claims about general natural-language verification, deployment error rates, financial decision quality, causal recourse, fairness, regulatory compliance, source authenticity, user trust, or operational savings.
