# Tool-assisted assistant audit pilot

Release 1.2.2 preserves the assistant audit run first archived in version 1.2.0 over existing fictional
fixtures. It evaluates seven claim labels per episode. This is a small,
author-associated, same-model conformance pilot, with a separate paired source
presentation exercise. It is not independent external validation.

## Task and denominators

| Condition | Episodes | Claims | Relationship to released data |
|---|---:|---:|---|
| Main text audit | 60 | 420 | Entire original reporting partition (`test`) |
| Diagnostic text audit | 8 | 56 | Entire separately authored diagnostic extension |
| Matched paired text | 12 | 84 | Separate fresh runs on selected main episodes |
| Paired image-source audit | 12 | 84 | The same selected main episodes, with source text rendered as PNG cards |

The text run uses four fresh contexts with 17 episodes each. Main and diagnostic
results are scored separately, despite sharing the batch workflow. The matched text and image runs each use two fresh six-episode contexts with
identical order. The matched text responses are newly produced; primary
17-episode-batch responses are not used as the modality control. These are
repeated evaluations of selected cases, not 12 additional main cases. Neither paired condition is added to the 420-claim main denominator.
Selection and episode mappings are recorded in `data/pilot/selection.json` and
`data/pilot/join_map.json`.

In both modalities the assistant receives the consumed numerical record,
policy configuration, trace, final-action history, declared alternatives,
structured claims, and source evidence. Consequently the task is claim auditing,
not source-only feature extraction. No observed extraction accuracy is measured
by this GPT pilot. The separately supplied Claude extraction task is documented
in [CLAUDE_EVALUATION.md](CLAUDE_EVALUATION.md).
Source-only extraction would require a distinct task that withholds consumed
values and claim answers, with a separately declared evaluation protocol.

## Deterministic tool assistance

The frontend supplies factual observations about each citation: whether its
referenced source is present, its kind, its version, and whether its SHA-256
agrees with the retained original source text. These observations assist
identity and integrity checks; they are not seven-claim labels, source-semantic
answers, or calculated policy recommendations. The assistant assigns all seven
labels under the fixed protocol.

The citation hashes apply to the original retained UTF-8 source text, including
in the image condition. They do not establish what a source means, that a
contract is authentic, or that the pixels themselves are the authoritative
original. PNG hashes separately preserve the visual presentation. A result from
this setup is tool-assisted assistant performance, not unaided model reasoning
or image-only integrity verification.

## Fixed inputs and inference procedure

The export contains text and image task inputs, four primary text batches, two matched text batches, two image batches, source
cards, selection metadata, and a manifest. Task instructions, prompts, and
source presentations are fixed before responses are scored. Emitted structured
responses are retained before conversion to scorer inputs. The scoring code
joins references only after inference; no benchmark label is filled in by the
frontend or scorer as an assistant prediction.

Fresh inference contexts are created without inheriting the authoring thread.
They receive only the specified task instructions and observable inputs,
including opaque episode handles for returning answers. Reference labels,
construction rationales, split/subtype tags, and checker code are not supplied.
The inference instructions prohibit accessing answer keys or running the
checker. Worker-reported activity logs describe compliance; complete tool
traces were not independently audited. This is procedural separation;
it is not a claim of a security-enforced filesystem boundary or a model that
has never encountered the public protocol.

The archive contains supplied task instructions, emitted structured responses,
and worker-reported activity logs. These self-reports list named inputs, image
views and output writes; they are neither independently audited nor complete
platform transport traces. Platform-hidden instructions, hidden
reasoning, and unexposed runtime settings are not represented as archived
material. No confidential organizational information is needed by the task.

## Model disclosure and independence

The pilot is identified as **GPT-6.1 Sol Ultra**, the exact display name supplied
by the user on 2026-10-04. Earlier archived input metadata identifies the
execution environment as Codex/GPT-6. Those frozen files, including the original
model-run example, remain unchanged as historical records. The display-identity
correction is documented separately; no model inference was rerun and no raw
response, fixed input, or score was altered by the correction.

This user-supplied name does not expose an immutable API snapshot, temperature,
seed, provider revision, or sampling configuration. Those fields remain unknown.
Do not reinterpret the corrected display name as a newly verified runtime
identifier.

The same assistant/model environment was used to develop the synthetic protocol
and conduct this pilot. Fresh contexts reduce direct carry-over of the
conversation but do not make the evaluation independent. The data are public,
the semantic rules are authored for the experiment, and the whole task is much
smaller and cleaner than financial documents in deployment. This association
and shared synthetic semantics must accompany any reported performance.

The main dataset still uses legacy `dev` and `test` identifiers for public
development and reporting partitions. Neither the assistant run nor its fresh
contexts retrospectively turn the reporting partition into a blind benchmark.

## Raw response and scoring format

Raw batch files contain an `episodes` array. Each element has the supplied
`episode_id` and seven claim objects with `claim_id`, `kind`, `label`, `check`,
and `evidence`. Labels are `supported`, `contradicted`, or `unresolved`. Each
text batch must include its 17 episodes exactly once. Each matched text and image batch must contain its six scheduled episodes. The parser checks coverage and identifiers;
it does not silently discard incorrect or unresolved labels.

A missing, malformed, incomplete or duplicate-containing response makes its
entire scheduled batch a conversion failure. The scorer preserves the raw file
and assigns unresolved labels for compatibility, without repair or retry. All
scheduled claims remain in their denominators. Failure-adjusted agreement
counts every converted claim as incorrect, including against reference
unresolved; ordinary label agreement is secondary. Conversion failures are
reported separately.

Checks and evidence notes are retained for inspection. Numerical scoring
assesses the labels; it does not itself certify rationale faithfulness. A
successful score does not mean the checker has independently validated every
free-text explanation in the assistant's response.

## Offline reproduction

The supplied PNGs require no rendering dependency for scoring. Optional source
card regeneration requires Pillow; the archived renderer used Pillow 12.3.0.
Export to a fresh directory because an existing frozen export is not overwritten:


```sh
python -m boundarybench.pilot export --data-dir data --output regenerated-pilot --render-images
```

Rescore the archived assistant outputs with:

```sh
python -m boundarybench.pilot score --pilot-dir data/pilot --data-dir data --raw-text results/pilot/raw/text --raw-image results/pilot/raw/image --raw-paired-text results/pilot/raw/paired_text --run-metadata results/pilot/model_run.json --output results/pilot
```

The score command produces distinct main-reporting, diagnostic, paired-text,
and paired-image reports, plus `paired_differences.json`. The original
main-corpus and deterministic capability-ablation results remain separately
identifiable. The preserved prompts and responses, their manifests, and the
same scoring code reproduce the saved run's scores offline.

The ordinary `python -m boundarybench reproduce --output results` command also
rescores the archived pilot when its saved inputs and responses are present.
Scoring uses the Python standard library; Pillow is required only for optional
PNG regeneration, not for reading the supplied archive or recomputing scores.

Neither command initiates model inference. Repeating live assistant inference
requires a new run and new metadata. Its outputs are not guaranteed to match
bit for bit, especially because the exact model snapshot and sampling settings
are unavailable. Never replace a preserved run's raw outputs with corrected
labels after inspecting references; a changed output set is a new run.

## Observed results

Run `codex-assistant-pilot-2026-10-04-1` produced the following saved results.
Failure-adjusted agreement is the primary measure: a converted batch would
count every scheduled claim as wrong, including a reference-unresolved claim.
There were no malformed or missing batches and no converted claims, so ordinary
label agreement equals failure-adjusted agreement in this run.

| Condition | Failure-adjusted agreement | Resolved claims | Supported / contradicted / unresolved | False support / endorsements |
|---|---:|---:|---:|---:|
| Main reporting text | 420/420 | 388/420 | 333 / 55 / 32 | 0/333 |
| Diagnostic text | 56/56 | 48/56 | 36 / 12 / 8 | 0/36 |
| Matched paired text | 84/84 | 75/84 | 68 / 7 / 9 | 0/68 |
| Paired image sources | 84/84 | 75/84 | 68 / 7 / 9 | 0/68 |

Because citation-integrity tooling directly assists lineage, report c1
separately from the six remaining scopes. Main text agrees on c1 60/60, the
other scopes 360/360, and source grounding c2–c3 120/120. Diagnostic text agrees
on c1 8/8, other scopes 48/48, and grounding 16/16. Each paired condition agrees
on c1 12/12, other scopes 72/72, and grounding 24/24. Grounding is a subset of
the six remaining scopes, not an additional disjoint denominator.

There are zero label disagreements between matched text and images. Both
main-reporting spelled-out eighteen-month grounding claims are supported
correctly (2/2); the bounded deterministic parser returned unresolved on those
two claims. This describes the two designed wording cases and does not
establish general language or multimodal superiority. No free-text rationale
quality was independently adjudicated.

## Reporting and limitations

Report counts and denominators for each group, including reference agreement,
resolution coverage, false support, confusion matrices, and claim-kind results.
Report the two main reporting episodes with spelled-out eighteen-month sources
as a small, prespecified source-wording subgroup; it is not a broad language
capability benchmark. Preserve every emitted abstention and error.

For the 12 paired cases, report label disagreements and errors against the same
references. Source cards contain the same deliberately simple source text;
there are no natural scans, handwriting, layout diversity, or image corruption.
Batch/context differences and the small dependent selection prevent a causal
claim that any difference was caused by modality alone.

The pilot does not evaluate financial decision quality, source authenticity,
source-only extraction, causal actionability, fairness, legal compliance,
independent human review, review-time savings, or deployment effectiveness.
Tool assistance, author association, public synthetic data, unknown runtime
settings, and the narrow fault model remain material limitations even if all
labels in a particular group agree with their construction references.
