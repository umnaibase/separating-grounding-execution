# Candidate-stability diagnostics — release 1.1.0

This author-written conformance extension is reported separately from the preserved 100-episode main corpus. It contains eight episodes (56 claims), arranged in four positive/negative assertion pairs. The construction-reference labels are not external or independently collected annotations.

Every episode uses 25 disputed transactions out of 1,500, below the toy 2% threshold. Valid conflicting contract records retain each declared candidate, with no precedence. Consumed commitment is the first listed candidate; execution is faithful and history is stipulated complete with no intervention.

| Method | Episodes | Claims | Accuracy | Resolved | False support / endorsements |
|---|---:|---:|---:|---:|---:|
| boundary | 8 | 56 | 100.00% | 85.71% | 0 / 36 |
| execution_only | 8 | 56 | 71.43% | 57.14% | 0 / 20 |
| provenance | 8 | 56 | 85.71% | 71.43% | 0 / 28 |

## Stability assertion matrix

| Candidates | Asserted stable | Reference c6 | execution_only c6 | provenance c6 | boundary c6 |
|---|---|---|---|---|---|
| [6, 9] | true | supported | supported | supported | supported |
| [6, 9] | false | contradicted | contradicted | contradicted | contradicted |
| [3, 5] | true | supported | supported | supported | supported |
| [3, 5] | false | contradicted | contradicted | contradicted | contradicted |
| [3, 6, 9] | true | contradicted | contradicted | contradicted | contradicted |
| [3, 6, 9] | false | supported | supported | supported | supported |
| [6, 9, 12] | true | supported | supported | supported | supported |
| [6, 9, 12] | false | contradicted | contradicted | contradicted | contradicted |

Every c7 construction reference (the dispute predicate alone suffices for manual review) is contradicted. Correct c7 predictions: execution_only 8/8, provenance 8/8, boundary 8/8. The homogeneous candidate sets demonstrate stable decisions without that sufficient dispute reason. The straddling set changes its recommendation at six months. Negative assertions reverse the c6 support/contradiction label.

Other construction labels in every episode are c1 supported, c2 unresolved, c3 supported, c4 supported and c5 supported. The boundary checker matches 56 of 56 construction labels. The ablations abstain on disabled capabilities; these are not competitive model baselines.

These are targeted branch checks, not random observations or evidence of generalisation. Their counts and percentages are not pooled with the main-corpus results. See `summary.json` and `predictions.jsonl` for complete confusion matrices and retained checks.
