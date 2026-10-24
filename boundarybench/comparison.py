"""Present reproducible local scores beside explicitly unverified report aggregates.

This module does not invoke models, create claim predictions, infer omitted
external metrics, or pool results across protocols or corpora. It can rescore
supplied predictions without thereby verifying their model-inference provenance.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

from .artifact_paths import contained_path


LABELS = ("supported", "contradicted", "unresolved")
CORPORA = ("main_reporting", "diagnostics", "paired_text", "paired_image")
OUR_MODEL = "GPT-6.1 Sol Ultra"
EXTERNAL_MODELS = (
    ("Grok 4.7", "results/external/grok-4.7/reported_results.json"),
    ("Claude Fable 5.1", "results/external/claude-fable-5.1/reported_results.json"),
)


def _read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _count(value, name: str, upper: int | None = None, nullable: bool = False) -> None:
    if value is None and nullable:
        return
    if type(value) is not int or value < 0 or (upper is not None and value > upper):
        raise ValueError("Invalid count or denominator: " + name)


def validate_reported_metrics(metrics: dict) -> None:
    """Check aggregate arithmetic without producing claim-level annotations."""
    if not isinstance(metrics, dict):
        raise ValueError("Reported metrics must be an object or an explicitly pending null")
    total = metrics.get("claims")
    _count(total, "claims")
    if total == 0:
        raise ValueError("A reported corpus must have a positive claim denominator")
    _count(metrics.get("agreement_correct"), "agreement_correct", total)
    for name in ("resolved_count", "endorsements", "false_support_count"):
        _count(metrics.get(name), name, total, nullable=True)
    if "episodes" in metrics:
        _count(metrics["episodes"], "episodes")
        if metrics["episodes"] * 7 != total:
            raise ValueError("Episode/claim denominators are inconsistent")
    resolved, endorsements, false_support = (metrics.get(name) for name in ("resolved_count", "endorsements", "false_support_count"))
    if endorsements is not None and resolved is not None and endorsements > resolved:
        raise ValueError("Endorsements exceed resolved claims")
    if false_support is not None and endorsements is not None and false_support > endorsements:
        raise ValueError("False support exceeds endorsements")
    labels = metrics.get("predicted_label_counts")
    if labels is not None:
        if not isinstance(labels, dict) or set(labels) != set(LABELS):
            raise ValueError("Invalid predicted-label aggregate keys")
        for label in LABELS:
            _count(labels[label], "predicted " + label, total)
        if sum(labels.values()) != total:
            raise ValueError("Predicted-label aggregates do not sum to claim denominator")
        if resolved is not None and labels["supported"] + labels["contradicted"] != resolved:
            raise ValueError("Predicted-label aggregates disagree with resolved count")
        if endorsements is not None and labels["supported"] != endorsements:
            raise ValueError("Supported aggregate differs from endorsements")
    by_kind = metrics.get("by_kind")
    if by_kind is not None:
        if not isinstance(by_kind, dict) or len(by_kind) != 7:
            raise ValueError("Expected seven per-kind reported aggregates")
        for values in by_kind.values():
            validate_reported_metrics(values)
        for name in ("claims", "agreement_correct", "resolved_count"):
            if metrics.get(name) is not None and all(row.get(name) is not None for row in by_kind.values()):
                if sum(row[name] for row in by_kind.values()) != metrics[name]:
                    raise ValueError("Per-kind aggregates disagree with corpus " + name)
        if labels is not None:
            for label in LABELS:
                if sum(row["predicted_label_counts"][label] for row in by_kind.values()) != labels[label]:
                    raise ValueError("Per-kind label aggregates disagree with corpus counts")


def validate_external_record(record: dict) -> None:
    if record.get("evidence_status") not in ("pending", "externally_reported_not_rescored", "supplied_predictions_locally_rescored"):
        raise ValueError("External aggregate records cannot claim locally rescored evidence")
    if not isinstance(record.get("model_name"), str) or not record["model_name"]:
        raise ValueError("External record requires a supplied model display name")
    if "conditions" in record:
        if record["evidence_status"] != "supplied_predictions_locally_rescored" or not isinstance(record.get("source"), dict) or record.get("artifacts", {}).get("raw_predictions_provided") is not True or not isinstance(record.get("local_rescore"), dict):
            raise ValueError("Multi-condition supplied scores require raw-prediction and local-rescore provenance")
        if set(record["conditions"]) != {"audit_notools", "audit_tools", "diag_notools", "diag_tools"}:
            raise ValueError("Unexpected supplied Claude audit conditions")
        for report in record["conditions"].values():
            if len(report["methods"]) != 1:
                raise ValueError("Each audit condition requires exactly one method")
            _local_metrics(next(iter(report["methods"].values()))["all"])
        return
    metrics = record.get("metrics")
    if not isinstance(metrics, dict) or set(metrics) != set(CORPORA):
        raise ValueError("Explicit metrics or nulls are required for all four corpus/conditions")
    if record["evidence_status"] == "pending":
        if any(value is not None for value in metrics.values()) or record.get("source") is not None:
            raise ValueError("Pending results require null metrics and no report source; zero is not missing")
        return
    if not isinstance(record.get("source"), dict):
        raise ValueError("An external report-only record needs a source artifact")
    if record["evidence_status"] == "supplied_predictions_locally_rescored":
        if record.get("artifacts", {}).get("raw_predictions_provided") is not True or not isinstance(record.get("local_rescore"), dict):
            raise ValueError("Locally rescored supplied results require raw-prediction and local-score provenance")
    for values in metrics.values():
        if values is not None:
            validate_reported_metrics(values)
    if all(values is None for values in metrics.values()):
        raise ValueError("A results report must contain at least one reported metric group")


def load_external_record(repo_root: Path, relative: str) -> dict:
    record = _read(contained_path(repo_root, relative))
    validate_external_record(record)
    if record["source"] is not None:
        source = record["source"]
        path = contained_path(repo_root, source["path"])
        if _sha(path) != source["sha256"]:
            raise ValueError("Archived external report hash differs from its provenance record")
    return record


def _local_metrics(group: dict, failure_adjusted: bool = False) -> dict:
    matrix = group["confusion_matrix_reference_rows_prediction_columns"]
    labels = {label: sum(matrix[truth][label] for truth in LABELS) for label in LABELS}
    ordinary = sum(matrix[label][label] for label in LABELS)
    values = {
        "episodes": group["episodes"], "claims": group["claims"],
        "agreement_correct": group["failure_adjusted_correct"] if failure_adjusted else ordinary,
        "agreement_basis": "failure-adjusted agreement" if failure_adjusted else "three-label agreement",
        "ordinary_agreement_correct": ordinary,
        "resolved_count": group["resolved_count"], "endorsements": group["endorsements"],
        "false_support_count": group["false_support_count"], "predicted_label_counts": labels,
        "conversion_failure_claims": group.get("conversion_failure_claims"),
    }
    # Per-kind local metric groups have one claim per episode, so only corpus
    # groups (seven claims per episode) use the external aggregate validator.
    if values["claims"] == 7 * values["episodes"]:
        validate_reported_metrics(values)
    return values


def rescore_grok(repo_root: Path) -> dict | None:
    """Rescore supplied files with the unchanged official evaluator; no inference."""
    from .evaluation import read_jsonl, score, write_json, markdown_report, validate, validate_diagnostics
    directory = repo_root / "results/external/grok-4.7"
    bundle_path = directory / "supplied_artifacts_manifest.json"
    if not bundle_path.exists():
        return None  # Original report-only archival state remains supported.
    bundle = _read(bundle_path)
    for name, expected in bundle["files"].items():
        path = contained_path(directory, name)
        if _sha(path) != expected["sha256"] or path.stat().st_size != expected["bytes"]:
            raise ValueError("Supplied Grok artifact differs from archived bytes: " + name)
    validate(repo_root / "data")
    validate_diagnostics(repo_root / "data/diagnostics")
    scores, score_artifacts, metrics = {}, {}, {}
    for name, data_relative, prediction_filename, split in (
        ("main_reporting", "data", "grok_predictions_main.jsonl", "test"),
        ("diagnostics", "data/diagnostics", "grok_predictions_diagnostics.jsonl", "all"),
    ):
        data = repo_root / data_relative
        supplied = read_jsonl(directory / prediction_filename)
        result = score(supplied, read_jsonl(data / "reference.jsonl"), _read(data / "metadata.json"), read_jsonl(data / "cases.jsonl"), split=split)
        if len(result["methods"]) != 1:
            raise ValueError("Each supplied Grok prediction file must contain exactly one method")
        group = next(iter(result["methods"].values()))
        if group["all"]["episodes"] != (60 if name == "main_reporting" else 8):
            raise ValueError("Supplied Grok score selected an unexpected corpus denominator")
        target = directory / "rescored" / name
        write_json(target / "summary.json", result)
        (target / "summary.md").write_text(markdown_report(result), encoding="utf-8", newline="\n")
        scores[name] = result
        score_artifacts[name] = {"path": str((target / "summary.json").relative_to(repo_root)), "sha256": _sha(target / "summary.json"),
                                 "input_prediction_episodes": len(supplied), "selected_episodes": group["all"]["episodes"], "selected_split": split}
        values = _local_metrics(group["all"])
        values["by_kind"] = {}
        for kind, kind_metrics in group["by_kind"].items():
            kind_values = _local_metrics(kind_metrics)
            del kind_values["episodes"]
            values["by_kind"][kind] = kind_values
        metrics[name] = values
    historical = _read(directory / "reported_results.json")
    systems = _read(directory / "systems.json")
    declared = next(row for row in systems["systems"] if row["system"] == "grok-4.7")
    protocol = _read(directory / "protocol.json")
    record = {
        "schema_version": "1", "model_name": "Grok 4.7",
        "model_name_source": "User-supplied display name and provider-declared system metadata; immutable model snapshot not supplied.",
        "evidence_status": "supplied_predictions_locally_rescored",
        "source": {"path": str(bundle_path.relative_to(repo_root)), "sha256": _sha(bundle_path), "type": "provided_prediction_bundle_manifest", "reported_release": "1.1.0"},
        "run_id_as_reported": declared["run_id"], "exact_model_snapshot": declared.get("model_snapshot"), "sampling_parameters": None,
        "sampling_description_as_reported": historical["sampling_description_as_reported"],
        "interface_as_reported": declared["interface"], "temperature_as_reported": declared["temperature"],
        "actual_model_inference_independently_verified": False,
        "inference_provenance": "Provider-declared only. Supplied prediction files and exact local score reproduction do not prove an actual foundation-model invocation or its share of the computation.",
        "protocol": {"id_as_reported": protocol["protocol_id"], "input_modality": "source_text", "episodes_per_call_as_reported": historical["protocol"]["episodes_per_call_as_reported"],
                     "tools_as_reported": declared["tools"], "reference_visible_during_judgment_as_reported": declared["reference_visible_during_judgment"],
                     "actual_tool_execution_independently_verified": False, "exact_integer_replay_required_by_supplied_protocol": True},
        "artifacts": {"report_provided": True, "raw_predictions_provided": True, "score_dump_provided": True, "machine_readable_run_results_provided": True, "protocol_card_provided": True,
                      "archive_directory": str(directory.relative_to(repo_root)), "manifest": str(bundle_path.relative_to(repo_root))},
        "local_rescore": {**score_artifacts,
                          "supplied_main_summary_byte_identical_to_local_rescore": (directory / "summary.json").read_bytes() == (directory / "rescored/main_reporting/summary.json").read_bytes(),
                          "procedure": "Official evaluation.score; main predictions contain 100 episodes and are filtered to the 60-episode test/reporting partition; eight diagnostics scored separately."},
        "metrics": {**metrics, "paired_text": None, "paired_image": None},
        "limitations": ["Numerical agreement has been independently reproduced from supplied predictions; the actual model execution has not been independently verified.",
                        "The provider describes a uniform tool-assisted procedure, not a sampled API decode, with temperature not applicable. No immutable snapshot or provider invocation trace is supplied.",
                        "Exact policy replay is declared by the provider, unlike the assistant pilot's integrity-only preprocessing. Scores are not a matched model ranking.",
                        "The original Markdown report and all six later attachments remain byte-for-byte preserved. Historical report-only transcription is retained separately."]}
    validate_external_record(record)
    write_json(directory / "supplied_results.json", record)
    return record


def build_comparison(repo_root: Path) -> dict:
    main_path = "results/summary.json"
    diagnostic_path = "results/diagnostics/summary.json"
    pilot_path = "results/pilot/summary.json"
    main, diagnostic, pilot = (_read(repo_root / name) for name in (main_path, diagnostic_path, pilot_path))
    if pilot["model_run"]["model_display_name"] != OUR_MODEL:
        raise ValueError("Update the user-supplied assistant display name and rescore the archived pilot before generating this comparison")
    checker_main = main["methods"]["boundary"]["by_split"]["test"]
    checker_diagnostic = diagnostic["methods"]["boundary"]["all"]
    systems = [{
        "model_name": "Bundled boundary checker",
        "evidence_status": "reproducible_deterministic_checker",
        "source_artifacts": [{"path": name, "sha256": _sha(repo_root / name)} for name in (main_path, diagnostic_path)],
        "protocol": {"type": "bounded deterministic source parser, hash checks and exact policy replay", "episodes_per_call": None, "input_modalities": ["source_text"], "model_inference": False},
        "metrics": {"main_reporting": _local_metrics(checker_main), "diagnostics": _local_metrics(checker_diagnostic), "paired_text": None, "paired_image": None},
    }]
    assistant_metrics, assistant_scope_groups = {}, {}
    for name in CORPORA:
        report = pilot["reports"].get(name)
        if report is None:
            assistant_metrics[name] = None
            continue
        group = next(iter(report["methods"].values()))
        assistant_metrics[name] = _local_metrics(group["all"], failure_adjusted=True)
        assistant_scope_groups[name] = {scope: _local_metrics(values, failure_adjusted=True) for scope, values in group["scope_groups"].items()}
    systems.append({
        "model_name": OUR_MODEL,
        "model_name_source": "User-supplied display name; not an exposed immutable provider snapshot.",
        "evidence_status": "locally_rescored_archived_outputs",
        "source_artifacts": [{"path": pilot_path, "sha256": _sha(repo_root / pilot_path)}],
        "protocol": {"id": pilot["protocol"], "main_text_episodes_per_context": 17, "paired_episodes_per_context": 6,
                     "tools": ["citation presence, kind, version and SHA-256 observations", "rendered source PNG viewing in image condition"],
                     "policy_replay_by_tool": False,
                     "input_modalities": ["source_text", "rendered_source_images_with_unchanged_populated_records"],
                     "tool_execution_evidence": pilot["model_run"].get("tool_activity_evidence"),
                     "exact_model_snapshot": pilot["model_run"].get("exact_model_snapshot"),
                     "sampling_parameters": pilot["model_run"].get("sampling_parameters"),
                     "failure_policy": pilot["failure_policy"]},
        "metrics": assistant_metrics, "scope_groups": assistant_scope_groups,
    })
    claude_record = None
    for expected_name, relative in EXTERNAL_MODELS:
        if expected_name == "Grok 4.7" and (repo_root / "results/external/grok-4.7/supplied_results.json").exists():
            relative = "results/external/grok-4.7/supplied_results.json"
        if expected_name == "Claude Fable 5.1" and (repo_root / "results/external/claude-fable-5.1/supplied_results.json").exists():
            relative = "results/external/claude-fable-5.1/supplied_results.json"
        record = load_external_record(repo_root, relative)
        if record["model_name"] != expected_name:
            raise ValueError("External record model name differs from the user-specified display name")
        if expected_name == "Claude Fable 5.1" and "conditions" in record:
            claude_record = record
            for condition, label in (("notools", "no computational tools"), ("tools", "SHA-256 + arithmetic")):
                main_group = next(iter(record["conditions"]["audit_" + condition]["methods"].values()))
                diagnostic_group = next(iter(record["conditions"]["diag_" + condition]["methods"].values()))
                systems.append({"model_name": record["model_name"], "display_name": f"{record['model_name']} ({label})", "condition": condition,
                                "evidence_status": record["evidence_status"], "actual_model_inference_independently_verified": False,
                                "model_id_configured": record["model_id_configured"], "exact_model_snapshot": None,
                                "record_artifact": {"path": relative, "sha256": _sha(repo_root / relative)},
                                "protocol": {**record["protocol"], "computational_tool_condition": label},
                                "metrics": {"main_reporting": _local_metrics(main_group["all"]), "diagnostics": _local_metrics(diagnostic_group["all"]), "paired_text": None, "paired_image": None},
                                "main_reporting_by_kind": {kind: _local_metrics(values) for kind, values in main_group["by_kind"].items()},
                                "limitations": record["limitations"]})
        else:
            systems.append({**record, "record_artifact": {"path": relative, "sha256": _sha(repo_root / relative)}})
    return {
        "schema_version": "1", "comparison_type": "evidence-qualified inventory; protocols differ, not a matched ranking",
        "systems": systems,
        "claude_source_extraction": None if claude_record is None else {"model_name": "Claude Fable 5.1", "evidence_status": "supplied_raw_responses_locally_rescored", "unit": "unique source document, distinct from episode-level claim auditing",
            "conditions": {condition: {key: value for key, value in claude_record["extraction"][condition].items() if key != "rows"} for condition in ("extract_text", "extract_image")},
            "document_validation": claude_record["extraction"]["document_validation"],
            "quote_metric_reconciliation": claude_record["extraction"]["reported_quote_metric_reconciliation"],
            "record_artifact": "results/external/claude-fable-5.1/rescored/extraction.json"},
        "claude_error_analysis": None if claude_record is None else {"audit_notools_disagreements": claude_record["error_analysis"]["audit_notools_disagreements"], "by_kind_and_transition": claude_record["error_analysis"]["by_kind_and_transition"], "false_supports": claude_record["error_analysis"]["false_supports"], "interpretation": claude_record["error_analysis"]["interpretation"]},
        "corpus_denominators": {"main_reporting": {"episodes": 60, "claims": 420}, "diagnostics": {"episodes": 8, "claims": 56}, "paired_text": {"episodes": 12, "claims": 84}, "paired_image": {"episodes": 12, "claims": 84}},
        "constraints": [
            "Main reporting, diagnostics and paired source-rendering conditions are reported separately and never pooled.",
            "Grok prediction artifacts, when supplied, are rescored locally; this numerical verification does not independently establish actual foundation-model execution. The structured evidence status identifies whether a row is rescored or report-only.",
            "Claude Fable 5.1 has separate no-computational-tool and SHA-256-plus-arithmetic audit conditions; any null condition means unavailable rather than zero. Historical pending metadata remains preserved.",
            "Grok declares exact-replay tools and one episode per call; the archived assistant pilot supplies citation-integrity observations only and batches episodes. These are different protocols.",
            "Model display names are supplied by the user. Exact immutable model snapshots and external sampling settings are not available.",
            "The Grok description 'not a sampled decode' is preserved as a reported statement, not confirmation of deterministic model behavior.",
            "The image pilot audits already-populated records using rendered versions of the same short sources; it does not establish document-to-feature extraction accuracy.",
            "All systems are judged against author-written conformance references on public, designed fixtures; no real-world banking generalisation, fairness, compliance, causal actionability or reviewer benefit is established.",
        ],
    }


def markdown_comparison(comparison: dict) -> str:
    status_names = {
        "reproducible_deterministic_checker": "Reproduced deterministic checker",
        "locally_rescored_archived_outputs": "Archived outputs, locally rescored",
        "externally_reported_not_rescored": "External report only; not rescored",
        "supplied_predictions_locally_rescored": "Supplied predictions, locally rescored; inference unverified",
        "pending": "Pending; no results supplied",
    }

    def ratio(numerator, denominator):
        if numerator is None:
            return "—"
        return f"{numerator}/{denominator if denominator is not None else '—'}"

    lines = ["# Evidence-qualified model results", "", "These rows are an inventory of differently evidenced runs and tool conditions, not a matched model ranking. Archived assistant outputs and externally supplied predictions remain explicitly distinguished. Model display names were supplied by the user; immutable serving-model snapshots remain unavailable.", ""]
    for corpus, heading in (("main_reporting", "Main reporting corpus: 60 episodes, 420 claims"), ("diagnostics", "Diagnostic corpus: 8 episodes, 56 claims")):
        lines.extend(["## " + heading, "", "| System | Evidence | Agreement | Resolved | False support / endorsements |", "|---|---|---:|---:|---:|"])
        for system in comparison["systems"]:
            m = system["metrics"][corpus]
            values = ["—", "—", "—"] if m is None else [ratio(m["agreement_correct"], m["claims"]), ratio(m.get("resolved_count"), m["claims"]), ratio(m.get("false_support_count"), m.get("endorsements"))]
            lines.append(f"| {system.get('display_name', system['model_name'])} | {status_names[system['evidence_status']]} | {' | '.join(values)} |")
        lines.append("")
    grok = next(system for system in comparison["systems"] if system["model_name"] == "Grok 4.7")
    grok_rescored = grok["evidence_status"] == "supplied_predictions_locally_rescored"
    diagnostic_note = (
        "The Grok diagnostic resolved count and endorsement denominator are now computed from its supplied predictions, not inferred from reported perfect agreement. The original report omitted these quantities; its unchanged report and historical transcription are retained."
        if grok_rescored else
        "Grok's diagnostic report does not state its resolved count or endorsement denominator. Those fields remain unavailable rather than reconstructed from reference labels."
    )
    claude_available = comparison.get("claude_source_extraction") is not None
    claude_note = " Claude's two audit conditions have been rescored separately from supplied artifacts." if claude_available else " Claude's blank entries are pending, not zero."
    lines.extend([diagnostic_note + claude_note + " The assistant's agreement is failure-adjusted; any malformed or missing batch would count as incorrect even when its reference label is unresolved. Correct reference-unresolved outcomes are abstentions, not response failures.", "",
                  "## Paired source-rendering pilot: GPT-6.1 Sol Ultra only", "", "| Condition | Agreement | Resolved | False support / endorsements |", "|---|---:|---:|---:|"])
    assistant = next(s for s in comparison["systems"] if s["model_name"] == OUR_MODEL)
    for corpus, name in (("paired_text", "Matched text, two contexts of six episodes"), ("paired_image", "Rendered source images, same episode order and context size")):
        m = assistant["metrics"][corpus]
        values = ["—", "—", "—"] if m is None else [ratio(m["agreement_correct"], m["claims"]), ratio(m["resolved_count"], m["claims"]), ratio(m["false_support_count"], m["endorsements"])]
        lines.append(f"| {name} | {' | '.join(values)} |")
    lines.extend(["", "These 12 episodes are a selected subset of the main reporting corpus, not additional independent observations. Their text prompts were rerun in matched six-episode contexts. Only source rendering changes; the supplied extracted values and decision records remain populated. Grok and Claude have no supplied results for this particular paired claim-audit condition.", ""])
    if claude_available:
        extraction = comparison["claude_source_extraction"]
        lines.extend(["## Claude Fable 5.1: separate source-extraction task", "", "The extraction task contains 25 unique source documents (20 contracts and five transaction summaries), with 55 target fields. It requires feature values from a document, unlike the GPT image-source audit above, which retains populated decision records. These denominators are neither pooled nor treated as matched cross-model scores.", "",
                      "| Source condition | Documents with all fields correct | Fields correct | Strict support-quote substring | Whitespace-normalized support quote |", "|---|---:|---:|---:|---:|"])
        for condition, label in (("extract_text", "Text"), ("extract_image", "Rendered document image")):
            values = extraction["conditions"][condition]
            lines.append(f"| {label} | {values['documents_all_fields_correct']}/{values['documents']} | {values['fields_correct']}/{values['fields_total']} | {values['quotes_exact_substrings']}/{values['documents']} | {values['quotes_whitespace_normalized_substrings']}/{values['documents']} |")
        lines.extend(["", "Strict quote matching checks each supplied string/list fragment against the literal source. Replacing line breaks with spaces can pass the separately labelled whitespace-normalized measure but is not an exact substring. The report's quoted-support figures of 25/25 text and 24/25 image reproduce only under normalization; the source report remains unchanged. Field accuracy is unaffected by this distinction.", "",
                      "The source set and field truths were independently checked against retained corpus sources and their literal templates. Stored PNGs and prompt files are hash-verifiable; original rendering seeds/code and image-delivery execution traces were not supplied. This is a small synthetic extraction check, not evidence about authentic scanned contracts or unseen document formats.", "",
                      "## Claude no-computational-tool error analysis", "", "There are 61 main-corpus disagreements: 55 lineage abstentions, four dispute-grounding abstentions and two false supports in commitment grounding. The false supports occur on two actually mismatching contract citations; recognizing a zero-looking digest by itself is not proof of mismatch. The contract's grounding claim requires usable citation evidence, so separating claim scopes does not remove that prerequisite.", "",
                      "Unavailable hash computation can make lineage abstention appropriate for the condition even though it disagrees with the fully evidenced construction reference. High reference agreement alone does not demonstrate that the model verified every prerequisite. The tool/no-tool difference on these fixed fixtures does not establish the causal claim that semantic reasoning was not the bottleneck.", ""])
    lines.extend([
                  "## Protocol and evidence differences", "", "| System | Decision-relevant tool support | Context | Evidence available |", "|---|---|---|---|",
                  "| Bundled boundary checker | Bounded parser, hash checks, exact policy replay | Deterministic code | Dataset, code and generated scores |",
                  "| GPT-6.1 Sol Ultra | Citation-integrity observations; policy reasoning by the assistant | 17 episodes per primary text context; 6 per paired context | Frozen prompts, literal outputs, run metadata and offline scores; tool activity self-reported |",
                  "| Grok 4.7 | Provider declares hash checks and exact policy replay | Provider declares one episode per call | " + ("Supplied predictions, protocol/run metadata and score dump; predictions rescored locally, model execution unverified" if grok_rescored else "Attached Markdown report only; predictions and execution details unavailable") + " |",
                  ("| Claude Fable 5.1 (two audit conditions) | No computational tools, or SHA-256 + arithmetic, as declared | Provider declares fresh instance per episode | Complete bundle, raw responses and local rescoring; configured model, tool enforcement and chronology not independently attested |" if claude_available else "| Claude Fable 5.1 | Not supplied | Not supplied | Pending |"), "",
                  "The Grok metadata describes a uniform tool-assisted procedure, ‘not a sampled API decode’, with temperature ‘not applicable; procedure applied uniformly’. Those descriptions are retained literally. Supplied predictions establish what was scored; they do not prove an actual model invocation or identify how much computation came from replay tools. Neither inference settings nor tool execution were independently verified. Identical scores therefore do not establish equal model capability.", "",
                  "Archived external report: [Grok 4.7 report](../external/grok-4.7/report.md). The original report and any later-supplied attachments retain their exact bytes and hashes. No claim-level predictions were invented from report aggregates or reference labels.", "",
                  "Claude's configured identifier is `claude-fable-5-1`, with harness-default sampling and possible fallback. Per-call prompts and responses can be verified offline, but the fresh-context and computational-tool policies remain provider declarations. No original runtime is recreated during rescoring.", "",
                  "None of these results estimates banking deployment accuracy, fairness, compliance, causal actionability or reviewer benefit. See `comparison.json` for precise evidence statuses, null fields, source hashes and protocol declarations.", ""])
    return "\n".join(lines)


def generate_comparison(repo_root: Path, output: Path | None = None) -> dict:
    from .claude import rescore_claude
    rescore_grok(repo_root)
    rescore_claude(repo_root)
    comparison = build_comparison(repo_root)
    output = output if output is not None else repo_root / "results/models"
    output.mkdir(parents=True, exist_ok=True)
    (output / "comparison.json").write_text(json.dumps(comparison, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    (output / "comparison.md").write_text(markdown_comparison(comparison), encoding="utf-8", newline="\n")
    return comparison


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        result = generate_comparison(args.root, args.output)
    except (ValueError, KeyError, OSError, TypeError) as error:
        print("error: " + str(error), file=sys.stderr)
        return 2
    print(json.dumps({s.get("display_name", s["model_name"]): s["evidence_status"] for s in result["systems"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
