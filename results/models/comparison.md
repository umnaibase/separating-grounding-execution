# Evidence-qualified model results

These rows are an inventory of differently evidenced runs and tool conditions, not a matched model ranking. Archived assistant outputs and externally supplied predictions remain explicitly distinguished. Model display names were supplied by the user; immutable serving-model snapshots remain unavailable.

## Main reporting corpus: 60 episodes, 420 claims

| System | Evidence | Agreement | Resolved | False support / endorsements |
|---|---|---:|---:|---:|
| Bundled boundary checker | Reproduced deterministic checker | 418/420 | 386/420 | 0/331 |
| GPT-6.1 Sol Ultra | Archived outputs, locally rescored | 420/420 | 388/420 | 0/333 |
| Grok 4.7 | Supplied predictions, locally rescored; inference unverified | 420/420 | 388/420 | 0/333 |
| Claude Fable 5.1 (no computational tools) | Supplied predictions, locally rescored; inference unverified | 359/420 | 331/420 | 2/277 |
| Claude Fable 5.1 (SHA-256 + arithmetic) | Supplied predictions, locally rescored; inference unverified | 420/420 | 388/420 | 0/333 |

## Diagnostic corpus: 8 episodes, 56 claims

| System | Evidence | Agreement | Resolved | False support / endorsements |
|---|---|---:|---:|---:|
| Bundled boundary checker | Reproduced deterministic checker | 56/56 | 48/56 | 0/36 |
| GPT-6.1 Sol Ultra | Archived outputs, locally rescored | 56/56 | 48/56 | 0/36 |
| Grok 4.7 | Supplied predictions, locally rescored; inference unverified | 56/56 | 48/56 | 0/36 |
| Claude Fable 5.1 (no computational tools) | Supplied predictions, locally rescored; inference unverified | 43/56 | 35/56 | 0/23 |
| Claude Fable 5.1 (SHA-256 + arithmetic) | Supplied predictions, locally rescored; inference unverified | 56/56 | 48/56 | 0/36 |

The Grok diagnostic resolved count and endorsement denominator are now computed from its supplied predictions, not inferred from reported perfect agreement. The original report omitted these quantities; its unchanged report and historical transcription are retained. Claude's two audit conditions have been rescored separately from supplied artifacts. The assistant's agreement is failure-adjusted; any malformed or missing batch would count as incorrect even when its reference label is unresolved. Correct reference-unresolved outcomes are abstentions, not response failures.

## Paired source-rendering pilot: GPT-6.1 Sol Ultra only

| Condition | Agreement | Resolved | False support / endorsements |
|---|---:|---:|---:|
| Matched text, two contexts of six episodes | 84/84 | 75/84 | 0/68 |
| Rendered source images, same episode order and context size | 84/84 | 75/84 | 0/68 |

These 12 episodes are a selected subset of the main reporting corpus, not additional independent observations. Their text prompts were rerun in matched six-episode contexts. Only source rendering changes; the supplied extracted values and decision records remain populated. Grok and Claude have no supplied results for this particular paired claim-audit condition.

## Claude Fable 5.1: separate source-extraction task

The extraction task contains 25 unique source documents (20 contracts and five transaction summaries), with 55 target fields. It requires feature values from a document, unlike the GPT image-source audit above, which retains populated decision records. These denominators are neither pooled nor treated as matched cross-model scores.

| Source condition | Documents with all fields correct | Fields correct | Strict support-quote substring | Whitespace-normalized support quote |
|---|---:|---:|---:|---:|
| Text | 25/25 | 55/55 | 20/25 | 25/25 |
| Rendered document image | 25/25 | 55/55 | 21/25 | 24/25 |

Strict quote matching checks each supplied string/list fragment against the literal source. Replacing line breaks with spaces can pass the separately labelled whitespace-normalized measure but is not an exact substring. The report's quoted-support figures of 25/25 text and 24/25 image reproduce only under normalization; the source report remains unchanged. Field accuracy is unaffected by this distinction.

The source set and field truths were independently checked against retained corpus sources and their literal templates. Stored PNGs and prompt files are hash-verifiable; original rendering seeds/code and image-delivery execution traces were not supplied. This is a small synthetic extraction check, not evidence about authentic scanned contracts or unseen document formats.

## Claude no-computational-tool error analysis

There are 61 main-corpus disagreements: 55 lineage abstentions, four dispute-grounding abstentions and two false supports in commitment grounding. The false supports occur on two actually mismatching contract citations; recognizing a zero-looking digest by itself is not proof of mismatch. The contract's grounding claim requires usable citation evidence, so separating claim scopes does not remove that prerequisite.

Unavailable hash computation can make lineage abstention appropriate for the condition even though it disagrees with the fully evidenced construction reference. High reference agreement alone does not demonstrate that the model verified every prerequisite. The tool/no-tool difference on these fixed fixtures does not establish the causal claim that semantic reasoning was not the bottleneck.

## Protocol and evidence differences

| System | Decision-relevant tool support | Context | Evidence available |
|---|---|---|---|
| Bundled boundary checker | Bounded parser, hash checks, exact policy replay | Deterministic code | Dataset, code and generated scores |
| GPT-6.1 Sol Ultra | Citation-integrity observations; policy reasoning by the assistant | 17 episodes per primary text context; 6 per paired context | Frozen prompts, literal outputs, run metadata and offline scores; tool activity self-reported |
| Grok 4.7 | Provider declares hash checks and exact policy replay | Provider declares one episode per call | Supplied predictions, protocol/run metadata and score dump; predictions rescored locally, model execution unverified |
| Claude Fable 5.1 (two audit conditions) | No computational tools, or SHA-256 + arithmetic, as declared | Provider declares fresh instance per episode | Complete bundle, raw responses and local rescoring; configured model, tool enforcement and chronology not independently attested |

The Grok metadata describes a uniform tool-assisted procedure, ‘not a sampled API decode’, with temperature ‘not applicable; procedure applied uniformly’. Those descriptions are retained literally. Supplied predictions establish what was scored; they do not prove an actual model invocation or identify how much computation came from replay tools. Neither inference settings nor tool execution were independently verified. Identical scores therefore do not establish equal model capability.

Archived external report: [Grok 4.7 report](../external/grok-4.7/report.md). The original report and any later-supplied attachments retain their exact bytes and hashes. No claim-level predictions were invented from report aggregates or reference labels.

Claude's configured identifier is `claude-fable-5-1`, with harness-default sampling and possible fallback. Per-call prompts and responses can be verified offline, but the fresh-context and computational-tool policies remain provider declarations. No original runtime is recreated during rescoring.

None of these results estimates banking deployment accuracy, fairness, compliance, causal actionability or reviewer benefit. See `comparison.json` for precise evidence statuses, null fields, source hashes and protocol declarations.
