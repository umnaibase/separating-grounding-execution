# Public repository distribution

This repository accompanies the 2026 manuscript by Angelo Dalli. Its scientific
record is frozen artifact release **1.2.2**: the original 100-case corpus retains
identifier 1.0.0, and the separate eight-case diagnostic extension retains
identifier 1.1.0. This public packaging adds no model calls or reference labels.

## Preserved research record

The working copies of `boundarybench/`, `data/`, `results/`, `tests/` and
`scripts/generate_data.py` preserve the original release bytes. In particular,
the original Claude results ZIP remains present because offline verification
checks its exact bytes. Supplied reports, prompt wrappers and responses are
experimental records; their statements describe the corresponding archived
procedure, not independently attested execution.

The complete original release, including historical documentation and citation
metadata, remains unchanged in `archive/explainability-boundaries-v1.2.2.zip`.
Its SHA-256 is:

```text
a782001e3d46970fa046eda6f2cb384f6da02c010d62cc896d3fe23ef02767a6
```

The root README and citation metadata provide the current public presentation.
The old publication checklist and suggested-paper wording are replaced in the
working documentation by these release notes and a factual result inventory.
Their original versions remain available inside the frozen archive.

## Added materials

- The non-anonymous paper PDF and its final LaTeX sources.
- Image-rendering code, source records, pinned dependencies and verification data.
- A provenance inventory and the script that reconstructs it from saved records.
- Public citation metadata, licensing notices and a repository checksum verifier.

The paper's Appendix F describes the arXiv ancillary distribution, which uses
`anc/` and a Base64-encoded ZIP. This GitHub distribution instead includes the
original ZIP directly under `archive/` and an extracted working copy at the root.
It requires no decoding step.

## Reproduction and scope

Validation, 80 existing tests, regeneration of all eight data files and full
offline reproduction passed under Python 3.12.14. Reproduced reports match the
archived reports; all original archived result files remain unchanged. No live
model service is used by these checks.

All merchants, contracts, transaction summaries, rules and intervention histories
in the suite are fictional. The record contains no confidential UMNAI product
implementation or customer banking data. UMNAI appears as the author's public
affiliation. The grant acknowledgement is retained in the paper and NOTICE.

The public answer key makes this a regression and failure-analysis artifact.
It is unsuitable as an unseen evaluation set. Independent documents, independent
annotation, matched model procedures and measured reviewer benefit remain future
work. Fairness, compliance and causal actionability were not evaluated.

The root `SHA256SUMS` covers the packaged files except itself. It records exact
distribution bytes; changing a file locally will cause that file's check to fail.
