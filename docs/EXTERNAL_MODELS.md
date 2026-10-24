# Further assistant and model audit experiments

Release 1.2.2 includes the archived, tool-assisted GPT-6.1 Sol Ultra audit pilot in addition to the deterministic checker results. See [PILOT.md](PILOT.md) for that run's fixed batch protocol, source images, run disclosure, and offline rescoring. The commands below support further model runs using the original generic exporter; they do not initiate model calls or reproduce live inference.

The metadata identifiers `dev` and `test` denote public development and
reporting partitions for compatibility. Both were inspected during implementation;
the `test` label does not establish a blind or independent evaluation. The
separate version-1.1.0 candidate-stability extension remains an authored
conformance diagnostic. The new pilot audits those same cases; their original construction and reference labels remain unchanged.

Grok 4.7 now has supplied claim-level JSONL predictions and protocol files in
addition to its original aggregate report. Those labels were rescored locally
and are marked `supplied_predictions_locally_rescored`; this verifies label
metrics rather than the underlying execution of a named model. Claude Fable
5.1 now has supplied audit and extraction responses with separately documented
tool conditions and execution-provenance limits. See [MODEL_COMPARISON.md](MODEL_COMPARISON.md)
for execution-provenance limits and the GPT display-identity correction.
Never reconstruct claim-level predictions from aggregates to make an otherwise
unverifiable run appear reproducible.

## Export without answer keys

```sh
python -m boundarybench export-prompts --split test --output model-inputs.jsonl
```

Each line contains `case_id`, `task`, and `messages`. Send only `messages` to the selected model; retain `case_id` locally for joining the response. The messages contain the observable sources, citations, execution record, declared alternatives and claims, together with the protocol definitions. They exclude case ID, subject, scenario tags, split tags, reference answers and construction rationales. The exporter reads split metadata to select cases but never reads `reference.jsonl`.

This exporter prepares a claim-audit task: the recorded extraction is deliberately visible because claims about its grounding and execution are the task. It is not an extraction prompt. The separately supplied Claude text/image extraction runs use source-only prompts over the existing synthetic documents and template-derived target fields; see [CLAUDE_EVALUATION.md](CLAUDE_EVALUATION.md). Testing new documents would require an explicit source-only protocol and separately established answers.

## Preserve a reproducible run

Before running, specify the model identifier/version, endpoint, date, exact prompts, sampling parameters, number of attempts, failure/retry policy and any tools available to the model. Hash verification and exact replay can require computational tools; record their availability rather than silently assisting selected cases. Preserve raw responses, tool traces and the response-conversion code. Store API keys outside the repository and do not include them in run metadata.

The model should return `{"claims": [...]}`. Join its response to the original `case_id` and add a descriptive `method` name. The scorer accepts one JSONL object per episode and method:

```json
{
  "case_id": "COPY_THE_EXPORTED_CASE_ID",
  "method": "your-model-and-run-identifier",
  "claims": [
    {
      "claim_id": "COPY_THE_CLAIM_ID",
      "kind": "contract_lineage",
      "label": "unresolved",
      "check": "The retained evidence was insufficient to decide this claim.",
      "evidence": []
    }
  ]
}
```

This illustrates the structure only; a valid episode must include all seven original claim IDs and kinds exactly once. Do not score this placeholder as a model output. `check` and `evidence` are retained for inspection; the scorer evaluates the three-class labels, not rationale quality.

Do not silently drop malformed responses, failures or missing claims. Prespecify how failures map to the output schema, retain an error indicator and report their number separately. If failures are mapped to unresolved labels, state that convention; those labels describe response handling rather than a successfully reasoned abstention. Without complete case and claim coverage the scorer rejects the run.

## Score separate results

```sh
python -m boundarybench score --predictions model-predictions.jsonl --split test --output model-results
```

The scorer allows either reporting-partition-only predictions or a complete all-split file with `--split test`; it ignores known development episodes when that filter is selected. Unknown IDs and duplicate predictions are errors. Every method scored must cover all selected episodes and all their claims. Class confusion matrices, resolution coverage, false support and per-kind/family results are written alongside accuracy.

Keep model runs in a separate directory, with their provenance, instead of replacing the shipped deterministic results. Freeze prompt and conversion choices before an evaluation run. This public constructed corpus has visible templates and labels; family separation does not make it a secret or independently validated benchmark. Additional model runs can test those models on these fixtures, but cannot establish real-world accuracy or confidential implementation claims.
