"""Scoring occurs after prediction, with explicit reference-key access."""

from __future__ import annotations

from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path

from .audit import KINDS, LABELS, METHODS, audit_case


def read_jsonl(path: Path) -> list[dict]:
    records = []
    with path.open(encoding="utf-8") as handle:
        for number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError as error:
                raise ValueError(f"{path.name}:{number}: invalid JSON") from error
            if not isinstance(item, dict):
                raise ValueError(f"{path.name}:{number}: record must be an object")
            records.append(item)
    return records


def write_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in records), encoding="utf-8", newline="\n")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _index(records: list[dict], field: str = "case_id") -> dict:
    result = {}
    for record in records:
        key = record.get(field)
        if not isinstance(key, str) or key in result:
            raise ValueError(f"Missing or duplicate {field}")
        result[key] = record
    return result


def validate(data_dir: Path) -> dict:
    cases = read_jsonl(data_dir / "cases.jsonl")
    refs = read_jsonl(data_dir / "reference.jsonl")
    metadata = json.loads((data_dir / "metadata.json").read_text(encoding="utf-8"))
    case_map, ref_map, meta_map = _index(cases), _index(refs), _index(metadata["cases"])
    if set(case_map) != set(ref_map) or set(case_map) != set(meta_map):
        raise ValueError("Case, reference, and metadata IDs must match exactly")
    families, family_variants = defaultdict(set), defaultdict(list)
    claim_count = 0
    for cid, case in case_map.items():
        claims = case.get("claims")
        if not isinstance(claims, list) or len(claims) != len(KINDS):
            raise ValueError(f"{cid}: expected seven claims")
        claim_map = _index(claims, "claim_id")
        if set(c.get("kind") for c in claims) != set(KINDS):
            raise ValueError(f"{cid}: claim kinds must match the contract")
        labels = ref_map[cid].get("labels", {})
        rationales = ref_map[cid].get("rationale", {})
        if set(labels) != set(claim_map) or set(rationales) != set(claim_map):
            raise ValueError(f"{cid}: reference claims/rationales mismatch")
        if any(v not in LABELS for v in labels.values()):
            raise ValueError(f"{cid}: invalid reference label")
        meta = meta_map[cid]
        if meta.get("split") not in ("dev", "test"):
            raise ValueError(f"{cid}: invalid split")
        families[meta["scenario_id"]].add(meta["split"])
        family_variants[meta["scenario_id"]].append(meta["variant"])
        if not isinstance(case.get("sources"), list) or not isinstance(case.get("citations"), dict):
            raise ValueError(f"{cid}: invalid source structure")
        _index(case["sources"], "source_id")
        claim_count += len(claims)
    if any(len(splits) != 1 for splits in families.values()):
        raise ValueError("A scenario family crosses split boundaries")
    required = {"clean", "extraction_error", "source_gap", "ambiguity", "intervention"}
    if any(len(values) != 5 or set(values) != required for values in family_variants.values()):
        raise ValueError("Each scenario requires the five declared variants")
    if len(cases) != 100 or len(families) != 20:
        raise ValueError("This v1 release requires 100 episodes and 20 scenario families")
    split_families = Counter(next(iter(splits)) for splits in families.values())
    if dict(split_families) != {"dev": 8, "test": 12}:
        raise ValueError("Expected eight dev and twelve test families")
    # Intentional source hash/version faults are evidence cases, not corrupt files.
    manifest_path = data_dir / "manifest.json"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        files = manifest.get("files", manifest.get("sha256", {}))
        if isinstance(files, list):
            files = {item.get("path", item.get("name")): item["sha256"] for item in files}
        if not isinstance(files, dict):
            raise ValueError("Malformed dataset manifest")
        for name in ("cases.jsonl", "reference.jsonl", "metadata.json"):
            expected = files.get(name)
            if isinstance(expected, dict):
                expected = expected.get("sha256")
            if expected != digest(data_dir / name):
                raise ValueError(f"Dataset manifest mismatch: {name}")
    else:
        raise ValueError("Dataset integrity manifest is missing")
    return {"episodes": len(cases), "claims": claim_count, "scenario_families": len(families),
            "split_families": dict(sorted(split_families.items())), "manifest_verified": True}


def validate_diagnostics(data_dir: Path) -> dict:
    """Validate the separately reported four paired candidate-set diagnostics."""
    cases = read_jsonl(data_dir / "cases.jsonl")
    refs = _index(read_jsonl(data_dir / "reference.jsonl"))
    metadata = json.loads((data_dir / "metadata.json").read_text(encoding="utf-8"))
    case_map, meta_map = _index(cases), _index(metadata["cases"])
    if len(cases) != 8 or set(case_map) != set(refs) or set(case_map) != set(meta_map):
        raise ValueError("Diagnostics require exactly eight matching cases, references and metadata records")
    families = defaultdict(list)
    expected_sets = {(6, 9), (3, 5), (3, 6, 9), (6, 9, 12)}
    for cid, case in case_map.items():
        claims = _index(case["claims"], "claim_id")
        if len(claims) != 7 or {c["kind"] for c in claims.values()} != set(KINDS):
            raise ValueError("Diagnostic episodes require seven distinct claim kinds")
        ref = refs[cid]
        if set(ref["labels"]) != set(claims) or set(ref["rationale"]) != set(claims):
            raise ValueError("Diagnostic reference coverage differs from observable claims")
        if any(label not in LABELS for label in ref["labels"].values()):
            raise ValueError("Invalid diagnostic reference label")
        meta = meta_map[cid]
        candidates = case["alternatives"]
        if tuple(candidates) not in expected_sets or meta["candidate_commitments"] != candidates:
            raise ValueError("Unexpected diagnostic candidate set")
        if meta["split"] != "diagnostic":
            raise ValueError("Diagnostic episodes must remain separate from main-corpus splits")
        inputs = case["record"]["input"]
        if inputs != {"disputed": 25, "eligible": 1500, "commitment_months": candidates[0]}:
            raise ValueError("Diagnostics require the stipulated fixed inputs and first consumed candidate")
        stability = next(claim for claim in claims.values() if claim["kind"] == "candidate_stability")
        if type(stability["asserted_value"]) is not bool:
            raise ValueError("Diagnostic stability assertion must be Boolean")
        families[meta["scenario_id"]].append((tuple(candidates), stability["asserted_value"]))
    if len(families) != 4 or any(len(pair) != 2 or pair[0][0] != pair[1][0] or {p[1] for p in pair} != {True, False} for pair in families.values()):
        raise ValueError("Diagnostics require four positive/negative assertion pairs")
    if {pair[0][0] for pair in families.values()} != expected_sets:
        raise ValueError("Diagnostic pairs must cover every declared candidate set")
    manifest_path = data_dir / "manifest.json"
    if not manifest_path.exists():
        raise ValueError("Diagnostic integrity manifest is missing")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for name in ("cases.jsonl", "reference.jsonl", "metadata.json"):
        expected = manifest.get("files", {}).get(name, {})
        if expected.get("sha256") != digest(data_dir / name) or expected.get("bytes") != (data_dir / name).stat().st_size:
            raise ValueError(f"Diagnostic manifest mismatch: {name}")
    return {"episodes": 8, "claims": 56, "scenario_families": 4, "split_families": {"diagnostic": 4}, "manifest_verified": True}


def predict(cases: list[dict], method: str) -> list[dict]:
    _index(cases)
    return [{"case_id": case["case_id"], "method": method, "claims": audit_case(case, method)} for case in cases]


def _divide(n: int, d: int):
    return n / d if d else None


def metrics(rows: list[dict]) -> dict:
    matrix = {truth: {pred: 0 for pred in LABELS} for truth in LABELS}
    for row in rows:
        matrix[row["reference"]][row["prediction"]] += 1
    n = len(rows)
    correct = sum(matrix[label][label] for label in LABELS)
    resolved = sum(row["prediction"] != "unresolved" for row in rows)
    resolved_correct = sum(row["prediction"] == row["reference"] and row["prediction"] != "unresolved" for row in rows)
    endorsements = sum(row["prediction"] == "supported" for row in rows)
    false_support = sum(row["prediction"] == "supported" and row["reference"] != "supported" for row in rows)
    per_class = {}
    for label in LABELS:
        tp = matrix[label][label]
        predicted = sum(matrix[truth][label] for truth in LABELS)
        actual = sum(matrix[label].values())
        per_class[label] = {"precision": _divide(tp, predicted), "recall": _divide(tp, actual),
                            "f1": _divide(2 * tp, predicted + actual), "reference_count": actual}
    return {
        "claims": n, "episodes": len({r["case_id"] for r in rows}),
        "scenario_families": len({r["scenario_id"] for r in rows}),
        "accuracy": _divide(correct, n), "resolved_count": resolved,
        "resolution_coverage": _divide(resolved, n),
        "resolved_prediction_accuracy": _divide(resolved_correct, resolved),
        "endorsements": endorsements, "false_support_count": false_support,
        "false_support_frequency": _divide(false_support, n),
        "false_support_among_endorsements": _divide(false_support, endorsements),
        "confusion_matrix_reference_rows_prediction_columns": matrix, "per_class": per_class,
    }


def score(predictions: list[dict], refs: list[dict], metadata: dict, cases: list[dict] | None = None,
          split: str = "all") -> dict:
    ref_map, meta_map = _index(refs), _index(metadata["cases"])
    selected = {cid for cid, meta in meta_map.items() if split == "all" or meta["split"] == split}
    if not selected or selected - ref_map.keys():
        raise ValueError("No complete reference set for the selected split")
    case_map = _index(cases) if cases is not None else None
    by_method, seen = defaultdict(list), set()
    for record in predictions:
        cid, method = record.get("case_id"), record.get("method")
        if cid not in meta_map or cid not in ref_map or not isinstance(method, str) or not method:
            raise ValueError("Prediction has unknown case or missing method")
        if (method, cid) in seen:
            raise ValueError("Duplicate prediction for method and case")
        seen.add((method, cid))
        if cid not in selected:
            continue
        claim_map = _index(record["claims"], "claim_id")
        labels = ref_map[cid]["labels"]
        if set(claim_map) != set(labels):
            raise ValueError(f"{cid}: predictions must cover each reference claim exactly once")
        observed_claims = _index(case_map[cid]["claims"], "claim_id") if case_map else None
        for claim_id, pred in claim_map.items():
            if pred.get("label") not in LABELS or pred.get("kind") not in KINDS:
                raise ValueError("Invalid prediction label or claim kind")
            if observed_claims and pred["kind"] != observed_claims[claim_id]["kind"]:
                raise ValueError("Prediction claim kind differs from the dataset")
            by_method[method].append({"case_id": cid, "claim_id": claim_id, "kind": pred["kind"],
                                     "reference": labels[claim_id], "prediction": pred["label"], **{
                                         k: meta_map[cid][k] for k in ("scenario_id", "split", "variant", "subtype")}})
    if not by_method:
        raise ValueError("No predictions supplied")
    report = {"protocol": "1.0.0", "experiment_type": "claim auditing on synthetic constructed episodes",
              "statistical_unit": "scenario family; variants and claims are dependent",
              "uncertainty_intervals": "Not reported: deliberately constructed finite cases are not a random deployment sample.",
              "reference_origin": "deterministic construction; no independent human annotation claimed", "methods": {}}
    for method, rows in sorted(by_method.items()):
        actual_ids = {r["case_id"] for r in rows}
        if actual_ids != selected:
            raise ValueError(f"{method}: missing cases; incomplete scoring is not allowed")
        group = {"all": metrics(rows), "by_split": {}, "by_kind": {}, "by_variant": {}, "by_scenario": {}}
        for key, field in (("by_split", "split"), ("by_kind", "kind"), ("by_variant", "variant"), ("by_scenario", "scenario_id")):
            for value in sorted({r[field] for r in rows}):
                group[key][value] = metrics([r for r in rows if r[field] == value])
        # Per-kind results in the test partition, avoiding aggregate-only reporting.
        group["test_by_kind"] = {kind: metrics([r for r in rows if r["split"] == "test" and r["kind"] == kind]) for kind in KINDS}
        report["methods"][method] = group
    return report


def markdown_report(report: dict) -> str:
    def fmt(value):
        return "n/a" if value is None else f"{100 * value:.2f}%"
    if report.get("reference_checker_ablations"):
        provenance = "These measurements describe the shipped synthetic cases and bounded checker. They are not foundation-model results or evidence of deployment effectiveness. The ablations receive the same sources and records. Disabled checking capabilities abstain; this is not a competitive model comparison."
    else:
        provenance = "These measurements describe supplied predictions on synthetic constructed cases. Model identity, prompt, parameters, tool access and raw-response provenance must be reported separately if external models produced these predictions. These figures do not establish deployment effectiveness."
    lines = ["# Controlled-suite claim results", "", provenance, "",
             "| Split | Method | Episodes | Families | Claims | Accuracy | Resolved | Resolved accuracy | False support / endorsements |",
             "|---|---|---:|---:|---:|---:|---:|---:|---:|"]
    for method, group in report["methods"].items():
        for split, m in group["by_split"].items():
            lines.append(f"| {split} | {method} | {m['episodes']} | {m['scenario_families']} | {m['claims']} | {fmt(m['accuracy'])} | {fmt(m['resolution_coverage'])} | {fmt(m['resolved_prediction_accuracy'])} | {m['false_support_count']} / {m['endorsements']} |")
    lines += ["", "Accuracy includes all three labels. Resolution coverage counts supported or contradicted predictions. False support counts an endorsement whose reference is contradicted or unresolved; zero observed errors is not a general guarantee.", "",
              "All variants of a scenario belong to one split. The test set is public, constructed, and was inspected during software validation. It is not a blind model-selection benchmark. No sampling-based confidence intervals or significance claims are made.", "",
              "## Test claims by kind", "",
              "| Method | Kind | Claims | Accuracy | Resolved | False support |", "|---|---|---:|---:|---:|---:|"]
    for method, group in report["methods"].items():
        for kind, m in group["test_by_kind"].items():
            lines.append(f"| {method} | {kind} | {m['claims']} | {fmt(m['accuracy'])} | {fmt(m['resolution_coverage'])} | {m['false_support_count']} |")
    lines += ["", "See `summary.json` for all class confusion matrices, per-class precision/recall/F1, per-variant results, and each scenario family's results. Null rates have a zero denominator and are not zero errors.", ""]
    return "\n".join(lines)


def reproduce(data_dir: Path, output: Path) -> dict:
    integrity = validate(data_dir)
    cases = read_jsonl(data_dir / "cases.jsonl")
    # Inference completes and is saved before reference labels enter the scorer.
    predictions = []
    for method in METHODS:
        predictions.extend(predict(cases, method))
    write_jsonl(output / "predictions.jsonl", predictions)
    refs = read_jsonl(data_dir / "reference.jsonl")
    metadata = json.loads((data_dir / "metadata.json").read_text(encoding="utf-8"))
    report = score(predictions, refs, metadata, cases)
    report["experiment_type"] = "synthetic controlled conformance and capability ablation"
    report["reference_checker_ablations"] = True
    report["data_validation"] = integrity
    report["data_sha256"] = {name: digest(data_dir / name) for name in ("cases.jsonl", "reference.jsonl", "metadata.json")}
    write_json(output / "summary.json", report)
    (output / "summary.md").write_text(markdown_report(report), encoding="utf-8", newline="\n")
    # Preserve the original report content and denominators. The v1.1 extension
    # has its own integrity checks, predictions, labels, and report directory.
    if (data_dir / "diagnostics").is_dir():
        reproduce_diagnostics(data_dir / "diagnostics", output / "diagnostics")
    return report


def markdown_diagnostic_report(report: dict) -> str:
    boundary = report["methods"]["boundary"]["all"]
    boundary_correct = sum(boundary["confusion_matrix_reference_rows_prediction_columns"][label][label] for label in LABELS)
    c7_correct = {
        method: sum(row["predictions_c7"][method] == row["reference_c7"] for row in report["diagnostic_matrix"])
        for method in METHODS
    }
    lines = [
        "# Candidate-stability diagnostics — release 1.1.0", "",
        "This author-written conformance extension is reported separately from the preserved 100-episode main corpus. It contains eight episodes (56 claims), arranged in four positive/negative assertion pairs. The construction-reference labels are not external or independently collected annotations.", "",
        "Every episode uses 25 disputed transactions out of 1,500, below the toy 2% threshold. Valid conflicting contract records retain each declared candidate, with no precedence. Consumed commitment is the first listed candidate; execution is faithful and history is stipulated complete with no intervention.", "",
        "| Method | Episodes | Claims | Accuracy | Resolved | False support / endorsements |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for method, group in report["methods"].items():
        m = group["all"]
        lines.append(f"| {method} | {m['episodes']} | {m['claims']} | {100*m['accuracy']:.2f}% | {100*m['resolution_coverage']:.2f}% | {m['false_support_count']} / {m['endorsements']} |")
    lines += ["", "## Stability assertion matrix", "", "| Candidates | Asserted stable | Reference c6 | execution_only c6 | provenance c6 | boundary c6 |", "|---|---|---|---|---|---|"]
    for case in report["diagnostic_matrix"]:
        labels = case["predictions_c6"]
        lines.append(f"| {case['candidate_commitments']} | {str(case['asserted_stable']).lower()} | {case['reference_c6']} | {labels['execution_only']} | {labels['provenance']} | {labels['boundary']} |")
    lines += [
        "", "Every c7 construction reference (the dispute predicate alone suffices for manual review) is contradicted. Correct c7 predictions: " + ", ".join(f"{method} {count}/8" for method, count in c7_correct.items()) + ". The homogeneous candidate sets demonstrate stable decisions without that sufficient dispute reason. The straddling set changes its recommendation at six months. Negative assertions reverse the c6 support/contradiction label.", "",
        f"Other construction labels in every episode are c1 supported, c2 unresolved, c3 supported, c4 supported and c5 supported. The boundary checker matches {boundary_correct} of {boundary['claims']} construction labels. The ablations abstain on disabled capabilities; these are not competitive model baselines.", "",
        "These are targeted branch checks, not random observations or evidence of generalisation. Their counts and percentages are not pooled with the main-corpus results. See `summary.json` and `predictions.jsonl` for complete confusion matrices and retained checks.", "",
    ]
    return "\n".join(lines)


def reproduce_diagnostics(data_dir: Path, output: Path) -> dict:
    integrity = validate_diagnostics(data_dir)
    cases = read_jsonl(data_dir / "cases.jsonl")
    predictions = []
    for method in METHODS:
        predictions.extend(predict(cases, method))
    # Predictions are generated without loading reference labels.
    write_jsonl(output / "predictions.jsonl", predictions)
    refs = read_jsonl(data_dir / "reference.jsonl")
    metadata = json.loads((data_dir / "metadata.json").read_text(encoding="utf-8"))
    report = score(predictions, refs, metadata, cases)
    report.update({
        "protocol": "1.1.0",
        "experiment_type": "separate author-written candidate-stability conformance diagnostics",
        "reference_checker_ablations": True,
        "statistical_unit": "paired diagnostic family; episodes and claims are dependent",
        "data_validation": integrity,
        "data_sha256": {name: digest(data_dir / name) for name in ("cases.jsonl", "reference.jsonl", "metadata.json")},
    })
    for group in report["methods"].values():
        del group["test_by_kind"]  # This extension has no main-corpus test split.
    reference_map = _index(refs)
    predictions_map = {(p["case_id"], p["method"]): _index(p["claims"], "claim_id") for p in predictions}
    report["diagnostic_matrix"] = [{
        "case_id": case["case_id"],
        "candidate_commitments": case["alternatives"],
        "asserted_stable": next(c["asserted_value"] for c in case["claims"] if c["kind"] == "candidate_stability"),
        "reference_c6": reference_map[case["case_id"]]["labels"]["c6"],
        "reference_c7": reference_map[case["case_id"]]["labels"]["c7"],
        "predictions_c6": {method: predictions_map[(case["case_id"], method)]["c6"]["label"] for method in METHODS},
        "predictions_c7": {method: predictions_map[(case["case_id"], method)]["c7"]["label"] for method in METHODS},
    } for case in cases]
    write_json(output / "summary.json", report)
    (output / "summary.md").write_text(markdown_diagnostic_report(report), encoding="utf-8", newline="\n")
    return report
