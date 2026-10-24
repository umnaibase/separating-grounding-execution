# Supplied Claude Fable 5.1 audit and extraction runs

Release 1.2.2 archives supplied outputs for two audit conditions and two
source-only extraction conditions. Local checks reproduce the scores from
saved responses. They do not attest the serving model, tool restrictions,
fresh-context isolation, or original lack of answer-key access.

## Archive and execution provenance

The supplied `report.md` and original
`fm_eval_claude-fable-5-1_results_bundle.zip` are retained under
`results/external/claude-fable-5.1/`. `source_manifest.json` records the
archive, report, and extracted-file hashes. The extracted bundle is under
`bundle/fm_eval/`. Its `raw/` directory contains per-call responses,
`predictions/` contains converted audit labels and failure/self-report files,
`prompts/agent/` contains wrapper prompts and their manifests, and `images/`
contains the rendered sources. The current evidence record is
`supplied_results.json`, marked `supplied_predictions_locally_rescored`.
The original pending `reported_results.json` is
historical metadata, not the current result.

The provider reports 186 calls through an agent harness: 68 audit calls per
tool condition and 25 extraction calls per modality, with one attempt and no
retry. The configured identifier was `claude-fable-5-1`; the provider explicitly
states that harness fallback prevents attestation of the serving model.
Sampling used harness defaults and temperature was not recorded. The report
declares one fresh agent per call, with the operator having already read the
reference labels and checker. Reference isolation and tool restrictions were
instruction-based. The archive includes response-level self-reports; native
model-call and transport traces are not independently audited.

The supplied ZIP retains file timestamps, but those timestamps are mutable
metadata. They do not independently establish that inference preceded scoring,
that the archived response was the only attempt, or that a worker could not
access reference material. The stated chronology and attempt policy remain
provider declarations.

The no-computation condition permits reading the prompt and writing the
response. It is therefore called **no computational tools**, rather than
claiming literally no filesystem interaction. The tool condition additionally
permits Bash for SHA-256 and integer arithmetic. These are declared access
conditions, not independently verified allow-lists.

Independent local checks reproduced all four supplied audit score reports,
reconstructed the converted predictions from all 136 audit response files,
and verified the 186 per-call prompt hashes. The exported audit prompts also
match the released exporter. These checks verify archive consistency; they
cannot establish the original runtime's behaviour.

## Audit results

| Condition | Main agreement | Main resolved | Main false support / endorsements | Diagnostic agreement | Diagnostic resolved | Diagnostic false support / endorsements |
|---|---:|---:|---:|---:|---:|---:|
| No computational tools | 359/420 | 331/420 | 2/277 | 43/56 | 35/56 | 0/23 |
| SHA-256 and integer-arithmetic tools | 420/420 | 388/420 | 0/333 | 56/56 | 48/56 | 0/36 |

Main and diagnostic results are separate. The 60 reporting episodes and eight
diagnostics retain their original source records and construction references.
Every supplied audit response covers its seven claims; the archived failure
lists are empty. The 32 unresolved main reference labels represent correct
evidence-limited answers, not failed responses. Their breakdown appears in
[MODEL_COMPARISON.md](MODEL_COMPARISON.md).

The no-computation main run has 61 disagreements:

| Claim scope | Reference → prediction | Count |
|---|---|---:|
| Contract lineage | Supported → unresolved | 54 |
| Contract lineage | Contradicted → unresolved | 1 |
| Dispute grounding | Supported → unresolved | 4 |
| Commitment grounding | Unresolved → supported | 2 |

Abstaining when a required digest cannot be computed is prudent under that
capability restriction. The agreement measure nevertheless compares against
the construction reference, which assumes the prescribed check can be
performed. Such capability abstentions should be distinguished from false
support. The diagnostic run adds 13 disagreements, all supported-to-unresolved:
eight lineage and five dispute-grounding claims.

The two main false supports occur on invalid contract citations. Grounding
requires usable cited evidence under the trusted fixture rules; content that
looks consistent does not repair a failed citation. Other grounding claims
were sometimes accepted despite the same lack of hashing capability, so their
correct final labels do not establish that the prerequisite was verified.
This is a scope-specific consistency issue, not proof that all no-computation
reasoning is unreliable.

The retained source bytes have been hashed locally to confirm the two citation
mismatches. An all-zero-looking digest alone is not proof of a mismatch;
appearance must not substitute for computing and comparing the retained bytes.

The hash-and-arithmetic run has no such disagreements. This is an observed
difference between two supplied runs with multiple capability differences,
not a randomized causal estimate of hashing, and not evidence that semantic
reasoning can never be a bottleneck. GPT and Grok use still different
frontends, context sizes, and execution protocols. No matched cross-model
ranking follows from these results.

## Separate source-only extraction task

The extraction task uses 25 distinct existing synthetic documents: 20 contracts
and five transaction summaries. Each prompt presents one document and requests
typed fields plus supporting text. It withholds the audit episode's consumed
inputs, policy execution, and claim labels. Contracts require commitment and
framework durations; transaction summaries require the observation window,
eligible count, and disputed count. This produces 55 scored fields per
condition, with targets derived from the generator's templates.

Text and image runs use the same documents. The provider describes the images
as formatted renders with mild rotation, blur, and speckle. They are not
natural scanned financial documents. Stored images allow offline scoring and
inspection without regenerating them. The original Claude image-rendering
code, seeds, prompt-building code, and image-delivery traces were not supplied,
so original generation and delivery cannot be reconstructed from the archive.
The separate GPT source-card renderer is supplied in `boundarybench/pilot.py`;
it does not regenerate these Claude images.

| Measure | Text | Rendered image |
|---|---:|---:|
| Documents with all target fields correct | 25/25 | 25/25 |
| Correct typed fields | 55/55 | 55/55 |
| Supporting quote is an exact character substring of source text | 20/25 | 21/25 |
| Supporting quote matches after whitespace normalization | 25/25 | 24/25 |

The source report's 25/25 and 24/25 quote figures correspond to
**whitespace-normalized** matching, despite its description as exact verbatim
matching. The original report remains unchanged; current scoring distinguishes
these measures. One image response inserts a vertical-bar separator, which
still fails the whitespace-normalized check. Typed-field accuracy does not
imply exact quotation fidelity.

No framework duration was returned as the commitment value in these 20
contracts in either condition; the spelled-out eighteen-month value was read
as 18. This tests a narrow source-only extraction task. It does not evaluate
an integrated extraction-to-policy pipeline, natural document diversity,
multiple-page interpretation, or rates of extraction faults in deployment.

## Reproduction and interpretation

From the repository root, `python -m boundarybench.comparison` rescores the
supplied external results and regenerates provenance-labelled reporting.
The default `python -m boundarybench reproduce --output results` also processes
the deterministic fixtures and archived GPT responses. Offline scoring uses
the standard library and makes no model call. The supplied PNGs do not require
Pillow for scoring.

Claude's derived files are written under
`results/external/claude-fable-5.1/rescored/`. The four condition directories
`audit_notools/`, `audit_tools/`, `diag_notools/`, and `diag_tools/` each contain
`summary.json`, `summary.md`, and reconverted `predictions.jsonl`.
`rescored/extraction.json` records typed-field and both quote measures;
`rescored/error_analysis.json` records the scope-specific audit disagreements
and actual contract-digest comparisons. `boundarybench/claude.py` implements
this local validation, conversion, and scoring. The original supplied files
remain unchanged.

These results supersede the earlier release-wide statement that no
source-only extraction had been evaluated. The narrower GPT image-source
audit remains a different task. The new results still do not test causal
actionability, fairness, compliance, source authenticity, human review benefit,
or real-world financial decision quality. Broader interpretations in supplied
reports remain attributed to those reports rather than adopted as findings.
