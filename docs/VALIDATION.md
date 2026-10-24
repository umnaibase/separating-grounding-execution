# Release validation

Release/code version 1.2.2 preserves the original main-corpus files at corpus
version 1.0.0 and retains separate candidate-stability diagnostics. It also includes
an archived GPT audit pilot and supplied Grok/Claude audit and extraction outputs
with offline rescoring. Validation of
the code and deterministic files is software conformance evidence; it does not
constitute blind empirical testing, independent annotation, or external model
validation.

## Reproduce the checks

Run from a fresh copy of the repository:

```sh
python -m boundarybench validate --data-dir data
python -m unittest discover -s tests -v
python -m boundarybench reproduce --output results
python scripts/generate_data.py --output regenerated-data
python -m boundarybench validate --data-dir regenerated-data
python -m boundarybench reproduce --data-dir regenerated-data --output regenerated-results
python -m boundarybench diagnostics --data-dir regenerated-data/diagnostics --output diagnostic-results
```

The default reproduction command uses the released archives to regenerate
current model reporting offline, including both Claude audit conditions and
its separately scored extraction task. It makes no model calls and needs no
image-rendering dependency for the stored PNGs. Regenerating the original
synthetic data is a separate check; it does not recreate live model responses.

Compare released main-corpus and diagnostic files to their regenerated
counterparts byte for byte. Compare both sets of predictions and summary
reports separately. Confirm that original main-corpus files and headline
results remain unchanged, and that the eight diagnostic episodes and 56 claims
are excluded from main totals. Check both true and false c6 assertions and the
non-equivalence of c6 and c7 at fixed below-threshold dispute counts.

Inspect the release manifest and content for private organizational material,
credentials, personal contact information, internal URLs, and absolute
workstation paths. All case content is newly authored fiction. A content review
is not independent confidentiality certification.

The CI matrix is configured for Python 3.10, 3.12, and 3.13. Hosted CI results
must be reported only after that workflow has actually run. The local validation
record below distinguishes completed checks from this procedure.

## Version 1.2.2 local validation

A fresh-copy check on Python 3.12.14 on Linux completed all **80 tests**
successfully. The added checks cover Claude raw-response conversion, complete
audit denominators, archive integrity, typed extraction fields, quote-match
definitions, current evidence status, and the two preserved false supports.
They also reject absolute paths, parent-directory paths, and symlink escapes
in archive references, nested manifests, and response identifiers, and reject
blank normalized quote strings or fragments.

Regeneration reproduced all eight original main/diagnostic data files byte
for byte. In the final fresh copy, 35 generated reports were removed and the
default `python -m boundarybench reproduce` recreated every one byte for byte.
The complete 549-file data/results tree matched the current repository.
Seventy-five protected files remain unchanged from release 1.2.1. These
checks preserve the original corpus, deterministic results, and archived
responses while adding separately reported external results.

All 454 files in the supplied Claude ZIP, plus the original ZIP and standalone
report, match their archived bytes and 456 manifest records. The four Claude
audit summary JSON files are byte-identical to the supplied score reports;
conversion from all 136 raw audit responses reproduces the supplied labels.
All 186 per-call prompt hashes and the exported audit prompts were checked.
Source-only extraction uses exactly the 25 distinct retained documents, and
target fields were checked against their complete literal source templates.

The no-computation Claude audit gives 359/420 main agreement, 331 resolved,
and two false supports among 277 endorsements; diagnostics give 43/56,
35 resolved, and zero false support among 23 endorsements. The hash-and-
arithmetic audit gives 420/420 main agreement, 388 resolved, and zero false
support among 333 endorsements; diagnostics give 56/56, 48 resolved, and
zero false support among 36 endorsements. Both extraction conditions give
25/25 fully correct documents and 55/55 typed fields. Strict supporting-quote
matches are 20/25 for text and 21/25 for images; whitespace-normalized matches
are 25/25 and 24/25. Current reporting corrects the supplied report's use of
“exact” for the latter measure without altering the original report.

Default reproduction also retains the archived GPT and supplied Grok scores
and generates the five-row comparison, including the bounded checker and
both Claude audit conditions. The original Claude pending record remains
historical only. All current reference-unresolved counts describe scored
answers: the 32 unresolved main references are correct evidence-limited
abstentions, not missing responses. Capability-related abstentions and false
supports in the no-computation condition are reported separately.

All these scoring checks run offline with the standard library; stored images
require no Pillow installation. They do not rerun live inference or verify
the serving-model identity, fresh-context execution, tool restrictions,
attempt counts, or scoring chronology. Mutable ZIP timestamps cannot
establish those properties. Original Claude image-rendering code and seeds
were not supplied. Hosted CI has not been run as part of this local validation.

## Version 1.2.1 local validation

Python 3.12.14 on Linux completed all **72 tests** successfully. The four new
comparison tests check that pending metrics remain null, historical report-only
evidence cannot claim local rescoring, inconsistent aggregate arithmetic is
rejected, and supplied predictions can be rescored without implying verified
model inference.

A disposable fresh-copy check also regenerated all eight main/diagnostic
data files and twenty result reports byte for byte, including archived-output
scoring and the default comparison hook. Forty-nine protected files match the
actual 1.2.0 ZIP: eight data files, the original checker, twenty-six frozen pilot
inputs, eight literal responses and six original reports. All seven Grok
attachments match the supplied bytes and their manifest hashes. Its locally
rescored main summary is byte-identical to the supplied main score dump.

Local rescoring of the supplied Grok files confirms 420/420 main reporting
labels, 388 resolved claims and zero false support among 333 endorsements.
Diagnostics separately confirm 56/56 labels, 48 resolved claims and zero false
support among 36 endorsements. The supplied main file contains 100 episodes;
the main reporting score selects the original 60 reporting episodes. The new
reports preserve that selection and the separate diagnostic denominator.

The generated comparison retains the archived GPT results, gives Grok the
status `supplied_predictions_locally_rescored`, and leaves every pending Claude
metric null. It preserves the original Grok report-only record as historical
evidence and hashes the subsequently supplied attachments. These checks do
not verify actual Grok model invocation, tool execution, or original access
restrictions. The supplied run card describes a uniform procedure rather than
a sampled API decode; different protocols prevent a matched model ranking.

The GPT display-name correction to **GPT-6.1 Sol Ultra** records user-supplied
identity information, not a new inference run. Frozen inputs and response files
remain unchanged; immutable model snapshot and sampling settings remain
unavailable. Hosted CI has not been run as part of this local validation.

## Version 1.2.0 local validation

Python 3.12.14 on Linux completed all **68 tests** successfully. This includes
the prior conformance and diagnostic tests plus ten pilot tests. The pilot
coverage exercises frozen input integrity, selection without answer-key input,
strict batch conversion, fixed denominators, failure-adjusted scoring, separate
scope/condition reports, pairing, and archived-output processing.

The archived score reports contain 420 main reporting claims, 56 diagnostic
claims, and 84 claims in each of the separate matched-text and image conditions.
All agree with their construction references; no conversion failures or paired
label differences are recorded. Matched conditions each contain 68 supported,
seven contradicted, and nine unresolved predictions. Main and diagnostic
corpora and deterministic reports remain distinct from these assistant outputs.

The scorer's primary failure-adjusted agreement counts a converted claim as
incorrect even when its fallback unresolved label matches the reference. Thus
missing or malformed batches cannot receive apparent agreement from abstention.
There were no such batches in the archived run.

These local checks validate software behaviour and preserved-output scoring.
They do not independently validate the assistant's self-reported tool activity
or reproduce live model inference. Exact model snapshot and sampling settings
remain unavailable. All source-only extraction, causal actionability, fairness,
compliance, and human-benefit claims remain outside the experiment.

## Version 1.1.0 local validation

Python 3.12.14 on Linux completed all **58 tests** successfully. The seven
added diagnostic tests cover the four candidate sets and both assertion
polarities, exact threshold outcomes, c6/c7 non-equivalence, source/citation
validity with unresolved c2 grounding, pair-only assertion changes, manifest
tamper detection, original-file hash preservation, deterministic regeneration
of both report sets, and standalone diagnostic execution without the main corpus.
The test count refers to test methods; several methods exercise multiple cases.

Main cases, references, metadata and the original three result files retain
their version-1.0.0 hashes. Regenerated main-corpus and diagnostic reports agree
byte for byte with the released outputs. The diagnostic report contains eight
episodes and 56 claims; each method evaluates all eight c6 and c7 claims
correctly. The fully enabled checker agrees with all 56 diagnostic references,
including eight unresolved commitment-grounding labels. These are checks of
the authored conformance design, not external evidence of generalisation.

The main `validate` command validates the main corpus. The separate `diagnostics`
command validates its own diagnostic files before evaluation. The local tests
exercise both paths. Hosted CI has not been run as part of this local validation.

## Historical version 1.0.0 validation

The previous release was checked with Python 3.12.14 on Linux: all 51 tests
passed from a fresh copy, main-corpus data and manifests regenerated byte for
byte, and predictions and reports reproduced byte for byte. The exporter
produced 60 reporting-partition prompts without a model call. Release contents
were reviewed without finding private organizational material, credentials,
personal contacts, internal URLs, or workstation paths. These historical
checks do not automatically attest to additions in later releases.

Within the unchanged release ZIP at `archive/explainability-boundaries-v1.2.2.zip`,
`RELEASE_MANIFEST.sha256` records SHA-256 digests of the original released files
except itself. The public repository distribution has a separate root
`SHA256SUMS`, checked by `python scripts/verify_release.py`. Main-corpus and
diagnostic manifests each distinguish file corruption from deliberately
inconsistent citations inside controlled cases.
