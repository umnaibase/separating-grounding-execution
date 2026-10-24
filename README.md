# Separating Grounding, Execution and Attribution

Reproducibility artifact for **[Separating Grounding, Execution and Attribution in Foundation-Model-Assisted Banking Audits](paper/Separating_Grounding_Execution_Attribution.pdf)** by **Angelo Dalli, UMNAI** (2026).

A correctly replayed rule can still use a misread contract. A stable recommendation can still depend on an unresolved interpretation. A matching final action can still involve a human intervention. This project makes those distinctions explicit through seven separately checked assertions.

The repository contains fictional merchant-onboarding cases, an executable audit contract, a bounded checker, authored reference labels, archived model outputs and offline scoring. Its central failure analysis examines two model responses that endorsed a contract-derived value despite an invalid citation digest.

## Seven audit assertions

Each assertion receives **supported (S)**, **contradicted (C)** or **unresolved (U)**, with a reason and evidence references. Contradiction requires counter-evidence; unresolved means an evidence prerequisite or checking capability is unavailable.

| Assertion | What the check establishes |
|---|---|
| **Contract lineage** | The cited identifier, version and SHA-256 digest match the retained contract. |
| **Commitment grounding** | The validated contract supports the asserted time until penalty-free exit. |
| **Dispute grounding** | Valid transaction evidence supports the asserted disputed-to-eligible fraction in the specified window. |
| **Conditional execution** | Both recorded rule predicates and the recommendation match exact replay on the consumed inputs. |
| **Final-action attribution** | Valid execution, a matching action, no intervention and stipulated complete history support attribution to the policy alone. |
| **Candidate stability** | Every declared candidate commitment gives the same recommendation, holding other inputs fixed. |
| **Sufficient dispute reason** | The recorded dispute counts alone meet the policy's review threshold. |

These scopes are deliberately limited. Lineage does not establish document authenticity. Grounding does not establish real-world truth. Replay does not repair incorrect inputs. Stability does not establish that the candidate set is exhaustive. Dispute sufficiency is conditional on the recorded inputs and policy, not a claim about actual merchant risk or causation. The diagnostics also test false-valued assertions; a supported label always refers to the proposition actually supplied.

The exact definitions are in [the audit contract](docs/CONTRACT.md) and the paper. The illustrative rule recommends review when the recorded dispute fraction is at least 2% **or** penalty-free commitment is below six months. These are invented screening thresholds.

## Findings and their scope

In the archived **Claude Fable 5.1** run without computational tools, two responses supported commitment grounding despite all-zero citation digests that fail local hash recomputation. One response explicitly contradicted lineage while supporting grounding; the other left lineage unresolved while supporting grounding. Both exhibit the same prerequisite failure: readable retained text does not satisfy this contract's requirement for a validated citation. See [the response analysis](results/external/claude-fable-5.1/rescored/error_analysis.json) and [evaluation notes](docs/CLAUDE_EVALUATION.md).

The bounded checker agrees with **418 of 420 authored labels** in the reporting subset. Its two disagreements are cautious abstentions on the word **“eighteen,”** outside its digit-based parser grammar. All 386 resolved predictions match the references; the remaining 34 are unresolved, including 32 required evidence-limited abstentions.

| Enabled checker capabilities | Reference agreement | Resolved assertions | False support / endorsements |
|---|---:|---:|---:|
| Execution checks | 264/420 | 232/420 | 0/193 |
| Plus contract identity checks | 322/420 | 290/420 | 0/247 |
| Plus bounded source grounding | 418/420 | 386/420 | 0/331 |

These are capability ablations of one implementation: disabled checks abstain. Generator and checker encode the same authored semantics, and the reporting cases were inspected during development. The counts establish conformance on these fixtures, not generalisation to banking documents.

The integrity-assisted **GPT-6.1 Sol Ultra** audit, supplied **Grok 4.7** predictions and hash/arithmetic-assisted **Claude Fable 5.1** audit each agree with all 420 reporting labels. Their tools, batching and execution provenance differ, so these results do not support a model ranking. The names identify archived display identities; immutable serving snapshots are unavailable. Offline rescoring reproduces scores, not live inference or the claimed execution restrictions. [Run reporting](docs/MODEL_COMPARISON.md) and the [provenance supplement](supplements/run-provenance/README.md) document these distinctions.

## Dataset

| Portion | Episodes | Assertions | Purpose |
|---|---:|---:|---|
| Development subset | 40 | 280 | Eight original scenario families |
| Reporting subset | 60 | 420 | Twelve original scenario families |
| **Original suite total** | **100** | **700** | Five variants per family |
| Separate diagnostics | 8 | 56 | Additional candidate sets and assertion polarities |

The five original variants cover clean evidence, injected extraction errors, source gaps, ambiguity and intervention/history issues. All merchants, contracts, transaction summaries and screening rules are fictional. Claims and variants share family structure; they are not independent population observations. Diagnostics are reported separately from the original totals.

The [dataset card](docs/DATASET.md) describes construction and limitations. [Cases](data/cases.jsonl), [references](data/reference.jsonl) and [family metadata](data/metadata.json) are separate files. The checker receives observable evidence without reference labels or scenario tags. The public references are authored answers, not independently collected human annotations.

## Reproduce locally

The core checker, generator, tests and archived-output scorers use **Python 3.10 or later and the standard library**. They require no API key, model service or network connection. Run from the repository root:

```sh
python -m boundarybench validate --data-dir data
python -m unittest discover -s tests -v
python -m boundarybench reproduce --output reproduced-results
```

Use `python3` if that is your Python 3 command. Reproduction runs the checker configurations, evaluates the separate diagnostics and rescores the archived model outputs. It writes reports under `reproduced-results/` and refreshes generated external score reports under `results/external/`. It does not invoke models or rewrite archived responses.

To check the distributed repository files against their SHA-256 manifest before making changes:

```sh
python scripts/verify_release.py
```

To regenerate the fictional data and deterministic checker results separately:

```sh
python scripts/generate_data.py --output generated-data
python -m boundarybench validate --data-dir generated-data
python -m boundarybench reproduce --data-dir generated-data --output generated-results
```

Regeneration does not create new model responses. The [validation record](docs/VALIDATION.md) describes the frozen release's checks, including 80 passing tests and byte-for-byte reproduction. Existing images require no rendering dependency for scoring. Regenerating the 25 document images additionally requires the pinned environment described in the [rendering supplement](supplements/rendering-supplement/README.md).

## Repository contents

| Location | Contents |
|---|---|
| [Paper PDF](paper/Separating_Grounding_Execution_Attribution.pdf) and [LaTeX source](paper/source/) | Manuscript and supplementary methods |
| [boundarybench/](boundarybench/) | Audit checks, command-line interface and offline scoring |
| [data/](data/) | Original cases, references, diagnostics and archived pilot inputs |
| [results/](results/) | Checker reports, saved model outputs and local rescoring |
| [scripts/](scripts/) and [tests/](tests/) | Deterministic generation and regression tests |
| [docs/](docs/) | Contract, dataset card, protocols and release validation |
| [Rendering supplement](supplements/rendering-supplement/) | Image renderer, inputs and reproduction evidence |
| [Run-provenance supplement](supplements/run-provenance/) | Archived procedure inventory and its reproduction script |
| [Frozen release 1.2.2](archive/explainability-boundaries-v1.2.2.zip) | Original release ZIP preserved unchanged |

The root working copy preserves the frozen release's code, data, tests and result artifacts. This README and citation metadata describe the public repository presentation. Earlier names, pending-result records and release-specific documentation remain preserved as historical metadata; current evidence is identified in [the model-run documentation](docs/MODEL_COMPARISON.md).

[Public release notes](docs/PUBLIC_RELEASE.md) identify the unchanged scientific files and the added repository materials. The [result inventory](docs/RESULTS_FOR_PAPER.md) separates reporting counts, diagnostics and document extraction. Fork the repository to conduct new experiments, retaining the original records and saving new outputs separately.

Appendix F of the paper describes an arXiv-style ancillary layout using `anc/` and a Base64-encoded release archive. Here the same ZIP is supplied directly under `archive/`, with the working copy already extracted at the repository root. The commands above therefore require no Base64 restoration step.

## Citation and licensing

Please cite the accompanying manuscript:

> Angelo Dalli. 2026. *Separating Grounding, Execution and Attribution in Foundation-Model-Assisted Banking Audits.* UMNAI.

[CITATION.cff](CITATION.cff) supplies machine-readable citation metadata. The code, documentation and fictional dataset are covered by the [MIT License](LICENSE). The paper and manuscript retain the author's rights; the bundled ACM class and bibliography files retain their own notices. See [NOTICE](NOTICE) for the scope of these materials.
