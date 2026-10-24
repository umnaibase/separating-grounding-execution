# Archived run provenance

This supplement documents existing records from the frozen `explainability-boundaries` release 1.2.2. It adds no model inference, reference labels or new evaluation results. Release 1.2.2 remains unchanged.

`run_provenance.json` distinguishes user-facing model names, configured harness strings and unavailable provider API or serving-snapshot identifiers. A `null` value means that information was unavailable in the source record. Fresh contexts, tool restrictions and attempt counts are attributed to their archived records or supplier reports; they are not independently attested platform behaviour. No provider API model string, immutable serving snapshot or numeric temperature is available for any of these three runs.

For GPT-6.1 Sol Ultra, 37 of the 60 reporting episodes share a primary context with at least one sibling from the same family. The 16 sibling groups include 11 pairs and five triples, spanning all 12 reporting families. Primary-context compositions, in reporting/diagnostic episodes, are 17/0, 14/3, 15/2 and 14/3. Thus three of the four contexts mix reporting and diagnostic episodes. No diagnostic siblings co-occurred. These counts establish opportunities for within-context comparison; they do not show that a model used them or estimate their effect on the score.

The GPT-6.1 Sol Ultra frontend provides retained-artifact presence, kind, version and digest comparisons. It therefore removes unaided integrity computation from that condition. It does not supply source interpretations, policy decisions or claim labels, and does not prevent the model from disregarding an integrity mismatch when judging grounding. Applying the grounding prerequisite remains a model task.

Every entry in the archived worker instructions declares `fork_turns=none` and prohibits prior-conversation, memory and project lookup. The run record reports inherited parent assistant configuration. These declarations do not independently establish isolation from persistent memory, project context or instruction state; worker activity records are self-reports rather than complete audited transport traces. Shared artifact-construction and auditing provenance adds dependence beyond generator/checker conformance.

Only Claude Fable 5.1 has an archived no-computational-tools condition. The other systems have no equivalent run, so these observations do not compare model susceptibility to the grounding-prerequisite failure.

Claude Fable 5.1 has per-call prompt wrappers and literal responses in the frozen archive. Its configured identifier is `claude-fable-5-1` and its declared agent parameter is `fable`; neither is an attested serving snapshot. Grok 4.7 has supplied structured predictions and procedure metadata, but no native prompts or execution traces. Its predictions can be rescored; its inference procedure cannot be examined from these records.

## Archive inventory

These records differ in tool access, batching and execution provenance. The inventory is not a controlled model comparison. Procedures describe available records or supplied accounts, rather than independently attested serving conditions.

| Run | Integrity procedure and context | Archived prompts | Archived literal responses |
| --- | --- | --- | --- |
| Bounded checker | Code-based checks | Not applicable | Code, outputs and reports |
| Claude Fable 5.1, no compute | No computational tools; per episode | Yes | Yes |
| Claude Fable 5.1, hash/arithmetic | Model-requested Bash; per episode | Yes | Yes |
| GPT-6.1 Sol Ultra | Frontend integrity observations; 17-episode contexts | Yes | Yes |
| Grok 4.7, supplied predictions | Reported hash/exact-replay tools; per episode | No | No; structured predictions only |

## Reproduce the provenance inventory

To reproduce the inventory, extract the unchanged release 1.2.2, then run with Python 3.10 or later:

```sh
python build_run_inventory.py --artifact-root /path/to/explainability-boundaries --output run_provenance.json
```

The script joins archived episode identifiers and scenario metadata, inspects the scheduled batch composition, and transcribes selected provenance fields. It performs no claim judging. The JSON records the SHA-256 and size of every archive file it reads. Repeating the command on the same release produces identical JSON bytes.
