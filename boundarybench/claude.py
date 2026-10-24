"""Verify and rescore the supplied Claude artifact bundle without live calls.

Raw responses, exported prompts, images and provider reports remain unchanged.
Numerical verification does not attest the serving model or tool enforcement.
"""

from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path
import re

from .evaluation import read_jsonl, score, write_json, write_jsonl, markdown_report
from .artifact_paths import contained_path


LABELS = ("supported", "contradicted", "unresolved")
CONDITIONS = ("audit_notools", "audit_tools", "diag_notools", "diag_tools")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("Duplicate JSON object key: " + key)
            result[key] = value
        return result
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique)


def unique_rows(rows: list[dict], key: str) -> dict:
    result = {}
    for row in rows:
        identifier = row.get(key)
        if not isinstance(identifier, str) or identifier in result:
            raise ValueError("Missing or duplicate " + key)
        result[identifier] = row
    return result


def verify_archive(archive: Path, repo_root: Path) -> dict:
    manifest = load_json(archive / "source_manifest.json")
    for relative, expected in manifest["files"].items():
        path = contained_path(archive, relative)
        if sha(path) != expected["sha256"] or path.stat().st_size != expected["bytes"]:
            raise ValueError("Claude archive hash mismatch: " + relative)
    bundle = archive / "bundle/fm_eval"
    expected_files = {str(p.relative_to(archive)) for p in bundle.rglob("*") if p.is_file()}
    expected_files.update(("fm_eval_claude-fable-5-1_results_bundle.zip", "report.md"))
    if set(manifest["files"]) != expected_files:
        raise ValueError("Claude source manifest must cover every bundle file, original ZIP and report")
    system = load_json(bundle / "results/system_report_claude-fable-5-1.json")
    if set(system["artifact"]["data_sha256"]) != {"cases.jsonl", "reference.jsonl", "diagnostics/cases.jsonl", "diagnostics/reference.jsonl"}:
        raise ValueError("Claude corpus manifest must contain the four expected data files")
    for relative, expected in system["artifact"]["data_sha256"].items():
        if sha(contained_path(repo_root / "data", relative)) != expected:
            raise ValueError("Claude declared corpus hash differs: " + relative)
    for filename in ("audit_reporting.jsonl", "audit_diagnostics.jsonl", "extraction_docs.jsonl"):
        if sha(bundle / "prompts" / filename) != system["prompts"][filename + "_sha256"]:
            raise ValueError("Claude exported prompt hash mismatch: " + filename)
    counts = {}
    if set(system["prompts"]["agent_wrapper_manifests"]) != set(CONDITIONS) | {"extract_text", "extract_image"}:
        raise ValueError("Claude wrapper manifest must cover all six conditions")
    for condition, relative in system["prompts"]["agent_wrapper_manifests"].items():
        rows = load_json(contained_path(bundle, relative))
        key = "doc_id" if condition.startswith("extract_") else "case_id"
        unique_rows(rows, key)
        for row in rows:
            if sha(contained_path(bundle, row["prompt_file"])) != row["sha256"]:
                raise ValueError("Claude wrapper prompt hash mismatch: " + row["prompt_file"])
        counts[condition] = len(rows)
    return {"archived_files_verified": len(manifest["files"]), "prompt_manifest_counts": counts,
            "total_per_call_prompt_hashes_verified": sum(counts.values()), "declared_data_hashes_verified": 4,
            "execution_provenance": "Provider declarations and self-reports; model identity and tool enforcement are not independently attested."}


def convert_audit_raw(raw_directory: Path, prompts: list[dict], method: str) -> tuple[list[dict], list[dict]]:
    """Validate coverage and reproduce provider conversion, preserving raw files.

    Missing/invalid claims retain their scheduled denominator as explicitly
    flagged unresolved conversions. Duplicate/unknown identities are rejected,
    rather than silently overwritten by a dictionary. No labels are inferred.
    """
    prompt_map = unique_rows(prompts, "case_id")
    extras = {p.stem for p in raw_directory.glob("*.json")} - set(prompt_map)
    if extras:
        raise ValueError("Unexpected Claude raw audit response IDs")
    output, failures = [], []
    for cid, prompt in prompt_map.items():
        supplied_claims = json.loads(prompt["messages"][1]["content"])["claims"]
        expected = unique_rows(supplied_claims, "claim_id")
        if len(expected) != 7:
            raise ValueError("Audit prompt requires seven unique claims")
        response_path = contained_path(raw_directory, cid + ".json")
        status, got = "ok", {}
        if not response_path.exists():
            status = "missing_response"
        else:
            try:
                response = load_json(response_path)
                claims = response.get("claims", [])
                if not isinstance(claims, list):
                    raise TypeError("claims must be a list")
            except (json.JSONDecodeError, TypeError, AttributeError) as error:
                status = "parse_error: " + str(error)
            else:
                got = unique_rows(claims, "claim_id")
                if set(got) - set(expected):
                    raise ValueError("Unknown Claude raw claim ID")
        converted = []
        for claim_id, expected_claim in expected.items():
            actual = got.get(claim_id)
            if actual is None or actual.get("label") not in LABELS:
                reason = status if status != "ok" else "missing or invalid label"
                converted.append({"claim_id": claim_id, "kind": expected_claim["kind"], "label": "unresolved", "check": f"RESPONSE_FAILURE ({reason})", "evidence": [], "response_failure": True})
                failures.append({"case_id": cid, "claim_id": claim_id, "reason": reason})
            else:
                if actual.get("kind") != expected_claim["kind"]:
                    raise ValueError("Claude raw claim kind differs from its prompt")
                converted.append({"claim_id": claim_id, "kind": expected_claim["kind"], "label": actual["label"],
                                  "check": str(actual.get("check", ""))[:500],
                                  "evidence": actual.get("evidence", []) if isinstance(actual.get("evidence"), list) else []})
        output.append({"case_id": cid, "method": method, "claims": converted})
    return output, failures


def source_truth(document: dict) -> dict:
    """Independent, full-string interpretation of the finite public templates."""
    text = document["text"]
    if document["kind"] == "transactions":
        match = re.fullmatch(r"Observation window: (?P<window>\d{4}-\d{2}-\d{2}/\d{4}-\d{2}-\d{2})\nEligible transactions: (?P<eligible>\d+)\nDisputed transactions: (?P<disputed>\d+)", text)
        if not match:
            raise ValueError("Unknown transaction ground-truth template")
        return {"observation_window": match["window"], "eligible": int(match["eligible"]), "disputed": int(match["disputed"])}
    if document["kind"] != "contract":
        raise ValueError("Unknown extraction document kind")
    patterns = (
        r"Minimum penalty-free cancellation time: (?P<n>\d+) months\.\nService framework duration: (?P<f>\d+) months\.",
        r"The service framework lasts (?P<f>\d+) months\. The merchant may terminate after (?P<n>\d+) months without penalty\.",
        r"Penalty-free termination is available once (?P<n>\d+) months have elapsed\. Framework duration: (?P<f>\d+) months\.",
        r"The minimum penalty-free cancellation time is (?P<n>eighteen) months\. The service framework lasts (?P<f>\d+) months\.",
    )
    for pattern in patterns:
        match = re.fullmatch(pattern, text)
        if match:
            return {"commitment_months": 18 if match["n"] == "eighteen" else int(match["n"]), "framework_months": int(match["f"])}
    raise ValueError("Unknown contract ground-truth template")


def validate_documents(documents: list[dict], source_cases: list[dict]) -> dict:
    docs = unique_rows(documents, "doc_id")
    occurrences = Counter((s["kind"], s["text"]) for case in source_cases for s in case["sources"])
    keys = {(d["kind"], d["text"]) for d in documents}
    if len(docs) != 25 or len(keys) != 25 or keys != set(occurrences):
        raise ValueError("Extraction documents must cover exactly the 25 unique retained sources")
    for doc in documents:
        if doc["doc_id"] != "doc_" + hashlib.sha256(doc["text"].encode()).hexdigest()[:12]:
            raise ValueError("Extraction document ID differs from source-text digest")
        if doc["n_episodes"] != occurrences[(doc["kind"], doc["text"])]:
            raise ValueError("Extraction source occurrence count mismatch")
        truth = source_truth(doc)
        supplied = {key: value for key, value in doc["truth"].items() if key != "template"}
        if "window" in supplied:
            supplied["observation_window"] = supplied.pop("window")
        if supplied != truth or any(type(supplied[key]) is not type(value) for key, value in truth.items()):
            raise ValueError("Supplied extraction truth differs from the literal source template")
    return {"documents": 25, "contracts": sum(d["kind"] == "contract" for d in documents), "transactions": sum(d["kind"] == "transactions" for d in documents), "retained_source_occurrences": sum(occurrences.values()), "field_denominator": sum(len(source_truth(d)) for d in documents), "truth_validation": "Derived anew from complete literal source templates and checked against both supplied truths and retained corpus sources."}


def score_extraction(documents: list[dict], raw_directory: Path) -> dict:
    docs = unique_rows(documents, "doc_id")
    if {p.stem for p in raw_directory.glob("*.json")} - set(docs):
        raise ValueError("Unexpected extraction response document")
    rows = []
    for doc_id, document in docs.items():
        truth = source_truth(document)
        path = contained_path(raw_directory, doc_id + ".json")
        failure = None
        try:
            raw = load_json(path)
            fields = raw["fields"]
            if not isinstance(fields, dict) or raw.get("kind") != document["kind"]:
                raise ValueError("Malformed extraction kind or fields")
            if set(fields) != set(truth):
                failure = "missing or unexpected extraction field"
        except (ValueError, OSError, KeyError, TypeError) as error:
            raw, fields, failure = {}, {}, str(error)
        correct = {key: key in fields and type(fields[key]) is type(value) and fields[key] == value for key, value in truth.items()}
        quote = raw.get("verbatim_support")
        pieces = quote if isinstance(quote, list) else [quote]
        valid_quote = bool(pieces) and all(isinstance(piece, str) and bool(piece) for piece in pieces)
        exact_quote = valid_quote and all(piece in document["text"] for piece in pieces)
        normalized_quote = valid_quote and all(bool(piece.split()) and " ".join(piece.split()) in " ".join(document["text"].split()) for piece in pieces)
        confusion = document["kind"] == "contract" and fields.get("commitment_months") == truth.get("framework_months") and truth["framework_months"] != truth["commitment_months"]
        rows.append({"doc_id": doc_id, "kind": document["kind"], "expected_fields": truth, "observed_fields": fields,
                     "field_correct": correct, "all_fields_correct": all(correct.values()) and failure is None,
                     "response_failure": failure, "support_quote_exact_substrings": bool(exact_quote),
                     "support_quote_whitespace_normalized_substrings": bool(normalized_quote),
                     "framework_as_commitment_confusion": confusion,
                     "spelled_eighteen_source": "eighteen months" in document["text"]})
    return {"documents": len(rows), "documents_all_fields_correct": sum(row["all_fields_correct"] for row in rows),
            "fields_correct": sum(sum(row["field_correct"].values()) for row in rows), "fields_total": sum(len(row["field_correct"]) for row in rows),
            "response_failures": sum(row["response_failure"] is not None for row in rows),
            "quotes_exact_substrings": sum(row["support_quote_exact_substrings"] for row in rows),
            "quotes_whitespace_normalized_substrings": sum(row["support_quote_whitespace_normalized_substrings"] for row in rows),
            "quote_definition": "For a string, require a nonempty substring; for a list, every piece must be nonempty and must match. Strict uses exact source bytes decoded as text. Normalized replaces each whitespace run with one space in source and quote, rejects fragments empty after normalization, and is not verbatim matching.",
            "framework_as_commitment_confusions": sum(row["framework_as_commitment_confusion"] for row in rows), "contracts": sum(row["kind"] == "contract" for row in rows),
            "spelled_eighteen_documents": sum(row["spelled_eighteen_source"] for row in rows),
            "spelled_eighteen_commitment_correct": sum(row["spelled_eighteen_source"] and row["field_correct"].get("commitment_months", False) for row in rows),
            "rows": rows}


def rescore_claude(repo_root: Path) -> dict | None:
    archive = repo_root / "results/external/claude-fable-5.1"
    if not (archive / "source_manifest.json").exists():
        return None
    integrity = verify_archive(archive, repo_root)
    bundle = archive / "bundle/fm_eval"
    provider = load_json(bundle / "results/system_report_claude-fable-5-1.json")
    conditions, local_rescore, errors, source_cases = {}, {}, [], []
    for condition in CONDITIONS:
        is_main = condition.startswith("audit_")
        data = repo_root / ("data" if is_main else "data/diagnostics")
        prompt_file = "audit_reporting.jsonl" if is_main else "audit_diagnostics.jsonl"
        filename_stem = "claude-fable-5-1_" + condition
        supplied_path = bundle / "predictions" / (filename_stem + ".jsonl")
        supplied = read_jsonl(supplied_path)
        methods = {row["method"] for row in supplied}
        if len(methods) != 1:
            raise ValueError("Claude condition requires one supplied method identifier")
        method = next(iter(methods))
        prompts = read_jsonl(bundle / "prompts" / prompt_file)
        converted, failures = convert_audit_raw(bundle / "raw" / condition, prompts, method)
        if converted != supplied or failures != load_json(bundle / "predictions" / (filename_stem + ".failures.json")):
            raise ValueError("Reconverted Claude raw response differs from supplied predictions/failures: " + condition)
        cases, refs = read_jsonl(data / "cases.jsonl"), read_jsonl(data / "reference.jsonl")
        metadata = load_json(data / "metadata.json")
        selected_ids = {row["case_id"] for row in metadata["cases"] if not is_main or row["split"] == "test"}
        if set(unique_rows(prompts, "case_id")) != selected_ids:
            raise ValueError("Claude prompts do not cover the selected corpus exactly")
        if condition in ("audit_notools", "diag_notools"):
            source_cases.extend(case for case in cases if case["case_id"] in selected_ids)
        result = score(converted, refs, metadata, cases, split="test" if is_main else "all")
        target = archive / "rescored" / condition
        write_jsonl(target / "predictions.jsonl", converted)
        write_json(target / "summary.json", result)
        (target / "summary.md").write_text(markdown_report(result), encoding="utf-8", newline="\n")
        local_rescore[condition] = {"path": str((target / "summary.json").relative_to(repo_root)), "sha256": sha(target / "summary.json"),
                                    "supplied_summary_byte_identical": (target / "summary.json").read_bytes() == (bundle / "results" / condition / "summary.json").read_bytes(),
                                    "raw_conversion_matches_supplied_predictions": True, "response_failure_claims": len(failures)}
        conditions[condition] = result
        if condition == "audit_notools":
            ref_map = unique_rows(refs, "case_id")
            for row in converted:
                labels = {claim["claim_id"]: claim["label"] for claim in row["claims"]}
                for claim in row["claims"]:
                    truth = ref_map[row["case_id"]]["labels"][claim["claim_id"]]
                    if truth != claim["label"]:
                        errors.append({"case_id": row["case_id"], "claim_id": claim["claim_id"], "kind": claim["kind"], "reference": truth, "prediction": claim["label"], "false_support": claim["label"] == "supported" and truth != "supported", "lineage_prediction": labels["c1"], "retained_reason": claim["check"]})
    documents = read_jsonl(bundle / "prompts/extraction_docs.jsonl")
    document_validation = validate_documents(documents, source_cases)
    extraction = {condition: score_extraction(documents, bundle / "raw" / condition) for condition in ("extract_text", "extract_image")}
    extraction["document_validation"] = document_validation
    extraction["reported_quote_metric_reconciliation"] = {"provider_report_claims": {"text": "25/25 exact substring", "image": "24/25 exact substring"},
        "local_strict_exact": {condition: value["quotes_exact_substrings"] for condition, value in extraction.items() if condition.startswith("extract_")},
        "local_whitespace_normalized": {condition: value["quotes_whitespace_normalized_substrings"] for condition, value in extraction.items() if condition.startswith("extract_")},
        "interpretation": "The reported quote counts agree only after whitespace normalization. Preserve both metrics and do not describe the normalized result as verbatim or exact matching."}
    write_json(archive / "rescored/extraction.json", extraction)
    error_analysis = {"audit_notools_disagreements": len(errors), "by_kind_and_transition": dict(Counter(row["kind"] + ":" + row["reference"] + "->" + row["prediction"] for row in errors)),
                      "false_supports": [row for row in errors if row["false_support"]], "all_disagreements": errors,
                      "interpretation": "The two false supports endorse commitment grounding without valid contract citation evidence. A separate scope label does not remove the grounding prerequisite. No-tools lineage abstention can reflect unavailable computation; reference agreement is not a pure measure of semantic capability. These condition differences do not establish a causal claim that semantic reasoning is not the bottleneck."}
    case_map = unique_rows(source_cases, "case_id")
    for error in error_analysis["false_supports"]:
        case = case_map[error["case_id"]]
        error["contract_hash_verification"] = []
        for citation in case["citations"]["contract"]:
            for source in case["sources"]:
                if source["source_id"] == citation["source_id"] and source["version"] == citation["version"]:
                    computed = hashlib.sha256(source["text"].encode("utf-8")).hexdigest()
                    error["contract_hash_verification"].append({"source_id": source["source_id"], "version": source["version"], "cited_sha256": citation["sha256"], "computed_utf8_sha256": computed, "matches": computed == citation["sha256"]})
    write_json(archive / "rescored/error_analysis.json", error_analysis)
    record = {"schema_version": "1", "model_name": "Claude Fable 5.1", "model_id_configured": provider["system"]["model_id_configured"],
              "model_identity_note": provider["system"]["model_id_note"], "exact_model_snapshot": None,
              "evidence_status": "supplied_predictions_locally_rescored", "actual_model_inference_independently_verified": False,
              "source": {"path": str((archive / "source_manifest.json").relative_to(repo_root)), "sha256": sha(archive / "source_manifest.json"), "type": "provided_bundle_manifest"},
              "protocol": {"access_route_as_reported": provider["system"]["access_route"], "sampling_as_reported": provider["system"]["sampling"], "sampling_parameters": None,
                           "attempts_per_call_as_reported": provider["system"]["attempts_per_call"], "retry_policy_as_reported": provider["system"]["retry_policy"],
                           "tool_enforcement_as_reported": provider["system"]["tool_restriction_enforcement"], "operator_contamination_as_reported": provider["run"]["operator_note"],
                           "fresh_context_and_tool_enforcement_independently_verified": False,
                           "scoring_chronology": "Provider-declared; original archive timestamps do not independently establish execution/scoring order."},
              "artifacts": {"report_provided": True, "raw_predictions_provided": True, "raw_responses_provided": True, "images_provided": True, "prompts_provided": True, "archive_directory": str(archive.relative_to(repo_root))},
              "integrity_verification": integrity, "local_rescore": local_rescore, "conditions": conditions,
              "extraction": extraction, "error_analysis": error_analysis,
              "limitations": ["Supplied artifacts permit offline numerical rescoring, not independent attestation of the serving model, fresh-context execution, chronology or tool enforcement.", "The configured model identifier and harness defaults are provider declarations; fallback and undisclosed sampling remain possible.", "The two audit tool conditions are not a matched cross-system benchmark with the GPT or Grok runs.", "The extraction experiment uses 25 unique short synthetic source documents, not real or scanned-original financial documents.", "Original image-rendering code/seeds, prompt-building code and runtime image-delivery traces were not supplied. Stored image assets are hash-verifiable, but their original generation and delivery cannot be independently reconstructed.", "Extraction and claim auditing have different units and denominators and are not pooled. The GPT rendered-source pilot retained populated decision records.", "Quoted support has strict and whitespace-normalized checks; reported exact-substring claims were not literally reproduced."]}
    write_json(archive / "supplied_results.json", record)
    return record
