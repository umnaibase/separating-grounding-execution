# Foundation-Model Evaluation on the Claim-Scoped Audit Suite — System Report: Claude

**Companion to:** "Claim-Scoped Auditing for Foundation-Model-Assisted Banking Pipelines: A Synthetic Conformance Study" (MFMB 2026 submission), artifact `explainability-boundaries` v1.1.0.
**Addresses the stated limitation:** "No foundation-model performance, multimodal input, causal actionability, fairness, compliance or reviewer benefit was evaluated." This report covers the first two items (foundation-model performance on the audit task and on extraction; multimodal document-image input). It does not address causal actionability, fairness, compliance or reviewer benefit, which need different experiments.
**Report format:** one system per report, identical protocol, so that reports for other systems (OpenAI, xAI Grok, …) can be placed side by side. Section 7 gives the merge procedure; `results/comparison_template.csv` has the Claude rows filled and empty rows for the other systems.

---

## 0. Provenance block (copy this structure for every system)

| Field | Value |
|---|---|
| System / vendor | Claude / Anthropic |
| Model identifier | `claude-fable-5-1` (requested explicitly on every call) |
| Model identity caveat | The serving model can differ under harness fallback and cannot be verified from inside the session. Treat the identifier as "configured", not "attested". |
| Access route | Claude Code agent harness: one fresh subagent per call. Not the public Messages API. |
| Sampling parameters | Harness default; temperature not controllable or recorded. |
| Attempts per call / retry policy | 1 / none |
| Response failures | 0 of 186 calls (every response parsed; every episode covered all seven claim IDs) |
| Failure mapping (pre-specified) | A missing or invalid label would have been recorded as `unresolved` with a `response_failure` flag and counted separately. None occurred. |
| Tools available to the model | Condition-specific; see §2. Restriction is **instruction-based**; the model self-reports tool use in every response and the harness's tool-use counts are consistent with the instructions (2 per no-tools call, 3–5 per tools call). |
| Operator contamination | The operator session had read the reference labels and checker source before the run. Every model-under-test call was a fresh instance that received only the exported prompt. Scoring was run after all calls completed. |
| Date | 2026-10-04 (Europe/Berlin) |
| Artifact | `explainability-boundaries` v1.1.0; data file SHA-256s recorded in `results/system_report_claude-fable-5-1.json` |
| Prompts | Exported with the artifact's own `boundarybench export-prompts` (task `audit_supplied_claims_v1`); SHA-256 of every per-call prompt in `prompts/agent/*/manifest.json` |
| Approximate cost | ≈12.7 M tokens over 186 calls, dominated by the agent harness's own system prompt; task content ≈2 k tokens per call |

## 1. What was evaluated

Three tasks, six conditions, 186 independent model calls. Each call was a **fresh model instance** that received only its prompt; no instance saw reference labels, construction rationales, metadata, the checker, or any other episode.

| Task | Condition | Calls | What the model sees | What it must produce |
|---|---|---:|---|---|
| A. Claim audit (the paper's task) | A1 `audit_notools` | 60 + 8 | The artifact's exported `messages` (system instructions with the seven claim definitions + observable episode JSON) | Seven S/C/U labels with reasons; no computation permitted, so SHA-256 digests cannot be checked |
| | A2 `audit_tools` | 60 + 8 | Same | Same; Bash permitted **only** for SHA-256 of source text and integer arithmetic; commands self-reported |
| B. Extraction from text | `extract_text` | 25 | One source document as text | `commitment_months` + `framework_months` (contracts) or window + `eligible` + `disputed` (transaction summaries), with verbatim supporting quote |
| C. Extraction from document image | `extract_image` | 25 | A rendered, mildly degraded scan-style PNG of the same document (serif contract layout / monospace export layout, ±0.6° rotation, blur, speckle); nothing else | Same fields as B |

Task A uses the 60-episode reporting subset (420 claims, 12 families) and the 8-episode candidate-stability diagnostics (56 claims), exactly as the paper reports them. Tasks B and C use the 25 unique source documents that occur in those episodes (20 contracts across the three numeric templates plus the one spelled-out-number template; 5 transaction summaries). Ground truth for B/C is parsed from the generator templates and is unambiguous per document (conflicts between documents are an episode-level property and belong to Task A).

Why two audit conditions: the lineage claim requires a SHA-256 over retained bytes. A plain language model cannot do that, and the protocol explicitly says to record tool availability rather than "silently assisting selected cases". A1 is the condition most comparable to a bare API call; A2 is the condition a deployed agentic auditor would run in.

## 2. Results

### 2.1 Task A — claim audit, reporting subset (60 episodes, 420 claims)

| Method | Agreement /420 | Resolved /420 | False support / endorsements | Resolved-prediction accuracy |
|---|---:|---:|---:|---:|
| Paper's bounded checker (+Grounding), for reference | 418 (99.52%) | 386 (91.90%) | 0 / 331 | 100% |
| **Claude, no tools (A1)** | 359 (85.48%) | 331 (78.81%) | **2 / 277** | 99.40% |
| **Claude, sha256 + arithmetic (A2)** | **420 (100%)** | **388 (92.38%)** | **0 / 333** | 100% |

Confusion matrices (reference → prediction):

| | A1 no tools | A2 tools |
|---|---|---|
| supported → supported / unresolved | 275 / 58 | 333 / 0 |
| contradicted → contradicted / unresolved | 54 / 1 | 55 / 0 |
| unresolved → unresolved / **supported** | 30 / **2** | 32 / 0 |

Per claim kind (agreement with reference, resolution):

| Claim kind | A1 agreement | A1 resolved | A2 agreement | A2 resolved | Bounded checker resolved |
|---|---:|---:|---:|---:|---:|
| contract_lineage | 5/60 (8%) | 3/60 | 60/60 | 58/60 | 58/60 |
| commitment_grounding | 58/60 | 42/60 | 60/60 | **40/60** | 38/60 |
| dispute_grounding | 56/60 | 54/60 | 60/60 | 58/60 | 58/60 |
| conditional_execution | 60/60 | 60/60 | 60/60 | 60/60 | 60/60 |
| final_action_by_rule | 60/60 | 54/60 | 60/60 | 54/60 | 54/60 |
| candidate_stability | 60/60 | 58/60 | 60/60 | 58/60 | 58/60 |
| sufficient_dispute_reason | 60/60 | 60/60 | 60/60 | 60/60 | 60/60 |

Per fault variant (A1 correct/84 → A2 correct/84): clean 72 → 84; extraction error 72 → 84; source gap 74 → 84; ambiguity 69 → 84; intervention 72 → 84.

**Head-to-head with the paper's bounded checker on the same 420 claims (A2):** identical on 418; on the remaining 2 the bounded checker abstains and the model supports — these are the two "eighteen" commitment-grounding claims whose reference label is *supported*. The model therefore weakly dominates the released checker on this corpus: same zero false support, two more correct resolutions.

### 2.2 Task A — candidate-stability diagnostics (8 episodes, 56 claims)

| Method | Agreement /56 | Resolved /56 | False support / endorsements |
|---|---:|---:|---:|
| Paper's bounded checker | 56 | 48 | 0 / 36 |
| Claude, no tools | 43 (76.79%) | 35 | 0 / 23 |
| Claude, tools | **56 (100%)** | 48 | 0 / 36 |

Both Claude conditions reproduced the entire Table 4 stability matrix of the paper (homogeneous sets {6,9}, {3,5}, {6,9,12} stable; straddling {3,6,9} sensitive; false assertions inverting the label) — all 8 candidate-stability labels correct in each condition. The 13 no-tools disagreements are 8 lineage abstentions and 5 dispute-grounding abstentions, all of the hash-prerequisite type described in §3.

### 2.3 Tasks B and C — extraction

| Condition | Documents fully correct | Fields correct | Framework-duration-as-commitment confusions (the paper's injected fault) | "eighteen" (spelled-out) read as 18 | Verbatim quote is an exact substring of source |
|---|---:|---:|---:|---|---:|
| Text | 25/25 | 55/55 | 0/20 contracts | yes | 25/25 |
| Document image | 25/25 | 55/55 | 0/20 contracts | yes | 24/25 (the one exception replaced line breaks with " \| "; content identical) |

## 3. Failure analysis (no-tools condition)

All 61 disagreements in A1 fall into four classes, and three of the four are about one thing — whether a citation counts as *valid evidence* when its digest cannot be checked.

1. **54 × lineage: supported → unresolved.** Structural. The model cannot compute SHA-256 and the instructions forbid guessing, so it abstains. This is the correct behaviour for a tool-less auditor and is what the paper's protocol anticipates. It is not an error in any useful sense, but it costs 54 points of "agreement" and should be read as such by anyone comparing systems.

2. **1 × lineage: contradicted → unresolved** (`invalid_contract_hash`). The citation carries an all-zero digest. The model called it "a placeholder rather than a verifiable digest" and abstained; the reference treats any observed mismatch as contradicted. Borderline — a defensible reading of "cannot verify" versus "observed mismatch".

3. **4 × dispute grounding: supported → unresolved.** In 4 of 60 episodes the model refused to support dispute grounding because the transaction citation's digest could not be verified; in the other 56 it accepted content match as sufficient. The same question — does grounding require a *validated* citation? — was answered differently across otherwise identical situations. This is an inconsistency in applying the contract's prerequisite, not a factual error; a strictly consistent tool-less auditor would answer *unresolved* for every grounding claim, as the model did for lineage.

4. **2 × commitment grounding: unresolved → supported (false support).** Both are `invalid_contract_hash` episodes. In one of them the model *itself* labelled lineage as contradicted (it recognised the all-zero digest as a mismatch) and then supported commitment grounding from the same document, reasoning that "the digest problem in c1 is a lineage defect assessed separately". The paper's contract says the opposite: a hash mismatch yields C for lineage and U for grounding, because evidence whose citation fails validation cannot ground anything. This is the exact failure mode the paper's claim separation is designed to expose — treating a cited document as evidence without first establishing that it is the cited document — and it is the only place where a tool-less foundation model produced a false support.

With the hash tool (A2) all four classes vanish: the model computed digests in every episode (115 self-reported `sha256` invocations across 68 calls) and applied the lineage→grounding dependency correctly in all four `invalid_contract_hash` / `wrong_contract_version` episodes.

## 4. What this does and does not establish

**Establishes, on this corpus:**
- A current foundation model, given the paper's claim definitions and a hash tool, reproduces the authored reference labels exactly (476/476 claims across both sets) with zero false support, and resolves the two spelled-out-number cases the bounded regex parser cannot. The paper's "unsupported wording" abstention is a limitation of the released parser, not of the contract.
- The same model with no computational tool is honest about what it cannot verify (lineage), but applies the contract's "valid citation" prerequisite inconsistently and produced two false supports on invalid-hash episodes. Access to a trivial computation changed the false-support count from 2 to 0; the semantic reasoning was not the bottleneck.
- The injected extraction fault the paper uses (framework duration consumed as commitment) did not occur in 0/20 contracts for this model in either modality, and the spelled-out number was read correctly in both. Document-image input produced identical extractions to text input on these renders.

**Does not establish:**
- Anything about real contracts, real transaction exports, scanned originals, or multi-page documents. The corpus has three numeric templates, one worded template, and one transaction template; the images are clean synthetic renders with mild degradation. Extraction at 25/25 on this material is a floor check, not evidence of deployment accuracy.
- Robustness of the audit result to prompt variation, sampling temperature, or repeated runs: one attempt per call, harness-default sampling, prompts fixed to the artifact's export.
- Independence of the evaluation: the system under test and the operator are the same model family, and the contract text in the prompt is highly explicit, so the audit task measures instruction-following against a well-specified contract more than open-ended judgement. Results for other vendors' systems on the identical prompts are the right comparison, which is why this report is formatted for merging.
- Tool restriction was enforced by instruction and verified only through self-report plus the harness's tool-use counts. A run through a raw API with a function-calling allow-list would be a stronger enforcement.
- Causal actionability, fairness, compliance and reviewer benefit — untouched.

**Suggested wording for the paper, if the authors want to cite this:** "A separately run external evaluation of one foundation model on the exported audit prompts (fresh instance per episode, no access to references) agreed with all 476 reference labels when permitted to compute digests, and disagreed on 74 of 476 without that capability, including two false supports on invalid-hash episodes; details in the accompanying system report." Any such sentence should cite the merged multi-system table rather than a single system.

## 5. Observations relevant to the paper's design

- The no-tools results expose a question the paper's contract settles but a human reader of Table 1 might not notice: *does semantic grounding presuppose a validated citation?* The contract says yes (hash mismatch ⇒ grounding U). A model with no hash capability must then either abstain on **every** grounding claim or decide to trust content match; this model did the latter 56 times and the former 4 times. The paper could state this dependency more prominently, since it is exactly where an LLM-based auditor drifts.
- The all-zero placeholder digest in `invalid_contract_hash` is recognisable without computation; the model noticed it in both episodes. A fault with a plausible-looking wrong digest would be a stricter test for tool-less auditors.
- The two "eighteen" cases: an LLM reads them correctly and the reference says *supported*. If the authors keep the bounded parser as the released reference checker, they might note that the abstention is by design and that a semantic reader resolves these cases — this report provides that data point.

## 6. Files in the results bundle

```
fm_eval/
  REPORT_claude-fable-5-1.md              this report
  results/system_report_claude-fable-5-1.json   machine-readable record (schema mfmb2026-fm-eval/1.0)
  results/comparison_template.csv         cross-system table; Claude rows filled, OpenAI / Grok rows empty
  results/audit_notools/, audit_tools/, diag_notools/, diag_tools/   artifact scorer output (summary.json, summary.md)
  results/extraction_results.json         per-document extraction scoring
  results/audit_crosscheck.json           confusion matrices and head-to-head vs bounded checker
  predictions/*.jsonl                     scorer-format predictions (+ .failures.json, .selfreport.json)
  prompts/audit_reporting.jsonl, audit_diagnostics.jsonl   artifact's exported prompts (unmodified)
  prompts/extraction_docs.jsonl           25 documents with parsed ground truth
  prompts/agent/<condition>/*.txt + manifest.json   exact per-call wrapper prompt and its SHA-256
  raw/<condition>/*.json                  every raw model response, as written by the model
  images/*.png                            the 25 rendered documents for the image condition
  convert.py, disagree.py                 response-conversion and analysis code
```

## 7. Merging results from other systems

To produce a comparable report for another system (OpenAI, xAI Grok, …):

1. Use the **same exported prompts** (`prompts/audit_reporting.jsonl`, `prompts/audit_diagnostics.jsonl`; SHA-256 in the JSON record). Send `messages` as-is: the first element is the system message, the second the user message. Do not add the agent wrapper text unless the system is run through a comparable agent harness; if you do, record the wrapper verbatim.
2. Run the two audit conditions separately: **no tools**, and **tools limited to SHA-256 + integer arithmetic** (a function-calling allow-list is preferable to instruction). Record tool availability and actual tool use per call.
3. For extraction, use `prompts/extraction_docs.jsonl` (text) and `images/*.png` (image) with the instruction block in `prompts/agent/extract_text/*.txt` / `extract_image/*.txt` (identical across documents apart from the document itself).
4. Convert responses with `convert.py` (or equivalent) so that every episode has all seven claim IDs; map any failure to `unresolved` **with a failure flag** and report the failure count separately. Never drop episodes.
5. Score with the artifact's own scorer so the metrics are computed by the same code:
   ```sh
   python -m boundarybench score --predictions <preds>.jsonl --split test --output <out>
   python -m boundarybench score --predictions <diag_preds>.jsonl --reference data/diagnostics/reference.jsonl \
       --metadata data/diagnostics/metadata.json --cases data/diagnostics/cases.jsonl --split all --output <out_diag>
   ```
6. Fill the system's rows in `comparison_template.csv` from `summary.json` (`agreement` = sum of the confusion-matrix diagonal; `resolved` = `resolved_count`; `endorsements`; `false_support_count`) and produce a `system_report_<model>.json` with the same top-level keys as the Claude record. Keep raw responses.
7. Report per-kind and per-variant tables as in §2.1; the interesting differences between systems will be in lineage/grounding handling without tools and in false-support counts, not in the aggregate.

A merged paper table should carry, per system and condition: model id as attested by the provider, access route, sampling parameters, tool policy, agreement, resolved, false support / endorsements, and response failures. Aggregates across systems are not meaningful without the tool condition being held fixed.

## 8. Reproduction of this run

```sh
# from the artifact root (explainability-boundaries v1.1.0)
python -m boundarybench export-prompts --split test --output audit_reporting.jsonl
python -m boundarybench export-prompts --data-dir data/diagnostics --split all --output audit_diagnostics.jsonl
# build per-call prompts, run the model, write raw/<condition>/<id>.json  (see prompts/agent/*/manifest.json for exact text)
python convert.py raw/audit_tools audit_reporting.jsonl <method-name> predictions/<method-name>.jsonl
python -m boundarybench score --predictions predictions/<method-name>.jsonl --split test --output results/<method-name>
```
The scorer rejects runs that do not cover every selected episode and claim, so a scored run is a complete run.
