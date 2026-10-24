# Archived result inventory

These counts reproduce the frozen authored answer key. They are not an
independent validation study or a matched ranking of foundation models. Reporting
and diagnostic claims are scored separately; neither includes response-rationale
quality.

## Grounding-prerequisite failure

Two saved Claude Fable 5.1 responses without computational tools endorse
commitment grounding despite invalid all-zero citation digests. Local SHA-256
recomputation confirms the mismatches. The required grounding label is unresolved
in both cases.

| Response | Case | Predicted lineage | Predicted grounding | Required grounding |
|---|---|---|---|---|
| A | `case_96101184a60febe1` | Contradicted | Supported | Unresolved |
| B | `case_91bf94e28c04fb8c` | Unresolved | Supported | Unresolved |

This is one observed failure mode in two fixtures. The tool-assisted condition
changes hashing and integer arithmetic together, on separate calls with
unrecorded sampling. Its lack of false support does not establish that tools
prevented the error. Equivalent tool-free conditions are absent for the other
two models. These records cannot establish comparative susceptibility or a
deployment error rate.

## Same authored key, different archived procedures

The reporting key contains 333 supported, 55 contradicted and 32 unresolved
labels. Those 32 unresolved labels are required abstentions. The diagnostic key
contains 36 supported, 12 contradicted and eight unresolved labels.

| Record | Reporting agreement | Reporting resolved | Reporting false support / endorsements | Diagnostic agreement | Diagnostic resolved | Diagnostic false support / endorsements |
|---|---:|---:|---:|---:|---:|---:|
| Claude Fable 5.1, no computational tools | 359/420 | 331 | 2/277 | 43/56 | 35 | 0/23 |
| Bounded checker, all checks enabled | 418/420 | 386 | 0/331 | 56/56 | 48 | 0/36 |
| Claude Fable 5.1, hash/arithmetic | 420/420 | 388 | 0/333 | 56/56 | 48 | 0/36 |
| GPT-6.1 Sol Ultra, integrity-assisted | 420/420 | 388 | 0/333 | 56/56 | 48 | 0/36 |
| Grok 4.7, supplied predictions | 420/420 | 388 | 0/333 | 56/56 | 48 | 0/36 |

Agreement counts labels equal to the authored key. Resolution counts supported
or contradicted labels. False support is a supported prediction whose reference
is contradicted or unresolved; its denominator is all supported predictions.

The checker abstains on two reporting contracts using the word "eighteen",
outside its digit-based grammar. Its other 32 unresolved predictions match the
reference abstentions. The assisted model records reach the authored resolution
ceiling, so this subset cannot distinguish them by agreement.

Tools, batching, construction provenance and available execution records differ.
Grok predictions can be rescored, but native prompts and execution traces were
not supplied. Serving snapshots and sampling parameters are unavailable where
the source records did not retain them. Display names are not serving attestations.

## Separate source-only extraction and paired presentations

Claude Fable 5.1 extracted 55 target fields from 25 unique templated documents
in each of two presentations. All fields matched in both text and image
conditions. Literal quote matches were 20/25 for text and 21/25 for images;
whitespace-normalised quote matches were 25/25 and 24/25. These are paired
presentations of the same documents, not 50 independent documents.

The separate GPT-6.1 Sol Ultra rendered-evidence audit and its matched text
control each agree with 84/84 authored labels over the same twelve audit cases.
This task retains populated audit inputs and frontend integrity observations;
it is distinct from source-only extraction.

The image renderer regenerates the archived mild synthetic scans. Byte-identical
rendering does not establish realistic scan difficulty or integrated pipeline
performance. See the paper and the rendering and provenance supplements for
the task-specific limitations.
