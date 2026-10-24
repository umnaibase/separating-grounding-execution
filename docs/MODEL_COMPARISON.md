# Provenance-labelled model-run reporting

Release 1.2.2 distinguishes the archived GPT assistant run, supplied Grok
predictions, and supplied Claude audit and extraction conditions. Available
prediction files can be scored locally. This is not a controlled model ranking: label agreement
does not independently verify how the supplied predictions were produced.

## Evidence status

| Display name | Available evidence | Reporting status |
|---|---|---|
| GPT-6.1 Sol Ultra | Fixed inputs, emitted structured responses, run metadata, and executable scoring | Archived predictions; locally rescored |
| Grok 4.7 | Supplied JSONL predictions, report, protocol and system cards, and original summaries | `supplied_predictions_locally_rescored`; model execution not independently verified |
| Claude Fable 5.1 | Supplied raw responses, converted audit predictions, prompts and manifests, rendered documents, and report | Locally rescored supplied outputs; configured identity and execution restrictions not independently attested |

The initial Grok Markdown-only report was insufficient for rescoring. A later
submission supplied `grok_predictions_main.jsonl`,
`grok_predictions_diagnostics.jsonl`, `protocol.json`, `systems.json`,
`summary.json`, and `summary.md`. These files are archived unchanged under
`results/external/grok-4.7/`, alongside the original report and provenance
records. The existing scorer validates the supplied claim labels against the
released cases and reference annotations, selecting the main reporting
partition separately from diagnostics.

`results/external/grok-4.7/supplied_artifacts_manifest.json` records the exact
bytes of the seven attachments, including the initial report. The current
evidence record is `supplied_results.json`. The earlier `reported_results.json`
is retained as a historical transcription of the initial report-only stage;
it is not the current comparison record.

This verification establishes coverage, label agreement, resolution, and
endorsement counts for the supplied prediction files. It does not establish
that a particular immutable model ran, that the described tools were executed,
or that reference labels were inaccessible during the original procedure.
Those execution properties remain claims in the supplied materials.

Claude's original pending `reported_results.json` is retained as historical
metadata. The current `supplied_results.json` and generated comparison replace
that pending status with the supplied evidence; null historical metrics are
not zero scores. See [CLAUDE_EVALUATION.md](CLAUDE_EVALUATION.md) for conditions,
raw-output provenance, extraction scoring, and the audit disagreement analysis.
`results/models/` retains evidence status alongside numbers.

## GPT display-identity correction

The user identified the assistant as **GPT-6.1 Sol Ultra** on 2026-10-04. This is
a display identity supplied after the archived run. Earlier frozen files,
including the input model-run example, use Codex/GPT-6 labels. These historical
files remain unchanged. The correction is documented separately from frozen
inputs and emitted responses; it does not represent new inference or an
altered output set.

The correction and its source are recorded in
`results/pilot/model_run.json` under `model_identity_provenance`. The original
`data/pilot/model_run.example.json` remains part of the frozen input archive.

The exact immutable model snapshot and sampling configuration remain
unavailable. A more specific display name does not establish those missing
runtime details. The GPT run remains author-associated and its worker activity
logs remain self-reports, not independently audited complete tool traces.

## Locally checked numerical results

| Entry | Main agreement | Main resolved | Main false support / endorsements | Diagnostic agreement | Diagnostic resolved | Diagnostic false support / endorsements |
|---|---:|---:|---:|---:|---:|---:|
| Bundled boundary checker | 418/420 | 386/420 | 0/331 | 56/56 | 48/56 | 0/36 |
| GPT-6.1 Sol Ultra — archived responses | 420/420 | 388/420 | 0/333 | 56/56 | 48/56 | 0/36 |
| Grok 4.7 — supplied predictions | 420/420 | 388/420 | 0/333 | 56/56 | 48/56 | 0/36 |
| Claude Fable 5.1 — no computational tools | 359/420 | 331/420 | 2/277 | 43/56 | 35/56 | 0/23 |
| Claude Fable 5.1 — hash and integer-arithmetic tools | 420/420 | 388/420 | 0/333 | 56/56 | 48/56 | 0/36 |

For GPT, the primary measure is failure-adjusted agreement; it equals ordinary
label agreement because no response conversion failed. For Grok, ordinary
label agreement is recomputed from the supplied JSONL. The files do not provide
a native batch-failure archive sufficient to reproduce an equivalent
failure-adjusted inference procedure.

Claude's supplied audit response files cover every selected claim and the
archived failure lists are empty; ordinary label agreement is locally
recomputed. The provider reports one attempt per call and no retries. The
absence of an observed failure does not make its failure protocol identical
to GPT's frozen whole-batch conversion procedure.

Main reference labels and the three fully agreeing run conditions comprise
333 supported, 55 contradicted, and
32 unresolved; diagnostic labels comprise 36 supported, 12 contradicted, and
eight unresolved. Grok's original aggregate report did not state diagnostic
resolution or endorsement denominators. The values 48 and 36 above are now
computed from the subsequently supplied labels, not inferred from perfect
agreement or retroactively added to the untouched original report.

The main reference's **32 unresolved labels are expected, correct abstentions**:

| Claim scope | Unresolved references | Constructed reason |
|---|---:|---|
| Commitment grounding | 20 | 14 conflicting contracts, four invalid citations, two missing contracts |
| Final-action attribution | 6 | Three incomplete histories and three inconsistent traces |
| Contract lineage | 2 | Missing contracts |
| Dispute grounding | 2 | Missing transaction sources |
| Candidate stability | 2 | Empty candidate sets |
| Conditional execution; sufficient dispute reason | 0 | No unresolved reference in either scope |

These are neither missing responses nor claims that failed to be scored.
Claude's no-computation condition adds capability-related abstentions beyond
these evidence-limited reference labels; it also supports two reference-
unresolved claims incorrectly. Its 89 unresolved predictions therefore cannot
be interpreted as 89 response failures.

The GPT archive also includes fresh matched text and image-source conditions,
each 84/84 agreement, 75/84 resolved, and 0/68 false support among endorsements,
with no paired label differences. Neither Grok nor Claude has a corresponding
paired run supplied here. Their paired fields remain null.

The available audit prediction sets label the two spelled-out eighteen-month
commitment-grounding claims supported. This checks a recorded feature against
source text; it is not an extraction-integration result or a general language
benchmark.

## Protocol and execution provenance

| Dimension | GPT-6.1 Sol Ultra archive | Grok 4.7 supplied materials |
|---|---|---|
| Tool assistance | Citation presence, kind, version and SHA-256 observations; frontend does not calculate semantic labels or policy outcomes | Protocol requires hash checking and exact integer policy replay |
| Primary text contexts | Four fresh contexts of 17 episodes | Report declares single-case calls |
| Paired modality control | Separate fresh matched-text and image runs, each two six-episode batches in identical order | No paired multimodal run supplied |
| Output provenance | Structured responses retained from session workers; worker activity is self-reported | Supplied prediction files are rescored; native model-call/transport traces are unavailable |
| Failure handling | Frozen whole-batch conversion with fixed denominators and failure-adjusted agreement | No equivalent native response/failure archive supplied |
| Runtime identity | Display name supplied by user; immutable snapshot and sampling settings unavailable | Display name in supplied files; immutable snapshot and runtime execution unverified |

The Grok system card explicitly describes session judgement under a uniform
tool-assisted procedure rather than a sampled API decode, and describes
temperature as not applicable because the procedure was applied uniformly.
These are source declarations, not independently verified runtime settings.
They leave uncertain which parts of the supplied predictions were generated
through model inference versus the uniform procedure. Repeated or templated
rationales alone do not prove their origin; this release makes no such inference.

Claude's provider reports one fresh agent per call, Read/Write-only access for
the no-computation audit condition, and additional Bash restricted to SHA-256
and integer arithmetic for the tool condition. Restrictions and fresh-context
isolation are provider declarations, supported by archived self-reports rather
than independently audited native API traces. The configured identifier
`claude-fable-5-1` is not attested because the harness may fall back to another
serving model. Temperature was not recorded. The operator had already seen
the reference labels and checker, so fresh worker contexts do not establish
independence from the operator or the authored protocol.

The different tool scopes matter: exact replay can supply information that
the GPT integrity-only frontend does not. Batching changes the context shared
between cases. The release therefore presents separate-run results with
attributed provenance, not a leaderboard or proof of relative model capability.
Claude's two audit runs also differ in both hash and arithmetic permissions;
their observed difference does not isolate a causal effect of hashing or show
that semantic reasoning can never be a bottleneck.

## Reproduce the reporting

Run from the repository root with Python 3.10 or later:

```sh
python -m boundarybench reproduce --output results
```

This rescoring path evaluates the deterministic fixtures, processes the saved
GPT responses, rescores the supplied external predictions, and regenerates the
comparison. It uses the standard library and makes no live model calls.

To regenerate external rescoring and cross-run reporting after the saved
GPT score reports exist:

```sh
python -m boundarybench.comparison
```

The comparison is written to `results/models/comparison.json` and
`results/models/comparison.md`. Grok reports are written separately to
`results/external/grok-4.7/rescored/main_reporting/` and
`results/external/grok-4.7/rescored/diagnostics/`. Claude reports are written to
`results/external/claude-fable-5.1/rescored/` under `audit_notools/`,
`audit_tools/`, `diag_notools/`, and `diag_tools/`, with separate
`extraction.json` and `error_analysis.json` files. The command accepts `--root`
for the repository location and `--output` for the comparison destination;
external rescoring remains under the repository's external-results directories.
No response file, frozen input, or supplied attachment is rewritten.

## Task scope and terminology

All audit episodes already contain consumed inputs, an execution record, source
evidence, and seven structured claims. Reading a spelled-out number and
checking whether it supports the recorded input is a **source-grounding audit**.
This audit task does not evaluate an integrated source-only extraction
pipeline or unaided foundation-model performance. Claude's distinct extraction
task does withhold consumed inputs and supplies one source document at a time.
Both text and mildly degraded rendered-image conditions reproduce all 55 target
fields across 25 synthetic documents. This narrow source-only task is now
tested; end-to-end extraction-to-decision integration and performance on natural
banking documents remain untested.

Human-facing terminology uses **final-action attribution** for claim c5. Its
immutable machine kind remains `final_action_by_rule`: the claim asks whether
retained evidence establishes that the policy produced the final action without
an intervention. No schema or original annotation changes with this terminology.

The available assistant outputs supersede an earlier release-wide statement
that no model results existed. They do not remove the narrow fixture, public
reference, fault-coverage, or independence limitations. Causal actionability,
fairness, compliance, and human review benefits remain
untested. Broad interpretations in external materials remain attributed to
those sources rather than adopted as findings of this package.
