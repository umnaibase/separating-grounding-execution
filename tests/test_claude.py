"""Offline supplied-response verification; no model calls or inferred labels."""

import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from boundarybench.artifact_paths import contained_path
from boundarybench.claude import convert_audit_raw, load_json, score_extraction, verify_archive
from boundarybench.comparison import load_external_record, rescore_grok
from boundarybench.evaluation import read_jsonl


ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "results/external/claude-fable-5.1"
BUNDLE = ARCHIVE / "bundle/fm_eval"


class ClaudeArtifactTests(unittest.TestCase):
    def test_artifact_paths_reject_absolute_parent_and_symlink_escapes(self):
        with tempfile.TemporaryDirectory() as folder:
            directory = Path(folder)
            root = directory / "root"
            root.mkdir()
            (root / "escape").symlink_to(directory, target_is_directory=True)
            for relative in ("../outside.json", str(directory / "outside.json"), "escape/outside.json"):
                with self.subTest(relative=relative), self.assertRaisesRegex(ValueError, "path"):
                    contained_path(root, relative)
            self.assertEqual(contained_path(root, "valid/file.json"), root / "valid/file.json")
            prompt = copy.deepcopy(read_jsonl(BUNDLE / "prompts/audit_reporting.jsonl")[0])
            prompt["case_id"] = "../outside"
            with self.assertRaisesRegex(ValueError, "contained relative"):
                convert_audit_raw(root, [prompt], "fixture")
            document = {"doc_id": "../outside", "kind": "contract", "text": "Minimum penalty-free cancellation time: 1 months.\nService framework duration: 24 months."}
            with self.assertRaisesRegex(ValueError, "contained relative"):
                score_extraction([document], root)

    def test_nested_claude_and_grok_manifest_paths_are_contained(self):
        for target in ("wrapper_manifest", "prompt_file"):
            def changed_loader(path):
                value = load_json(path)
                if target == "wrapper_manifest" and path.name == "system_report_claude-fable-5-1.json":
                    value["prompts"]["agent_wrapper_manifests"]["audit_notools"] = "../outside.json"
                elif target == "prompt_file" and path.name == "manifest.json":
                    value[0]["prompt_file"] = "../outside.json"
                return value
            with self.subTest(target=target), patch("boundarybench.claude.load_json", side_effect=changed_loader):
                with self.assertRaisesRegex(ValueError, "contained relative"):
                    verify_archive(ARCHIVE, ROOT)
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            directory = root / "results/external/grok-4.7"
            directory.mkdir(parents=True)
            (directory / "supplied_artifacts_manifest.json").write_text(json.dumps({"files": {"../outside.json": {"sha256": "0" * 64, "bytes": 0}}}))
            with self.assertRaisesRegex(ValueError, "contained relative"):
                rescore_grok(root)

    def test_normalized_quotes_reject_blank_string_and_list_fragments(self):
        document = {"doc_id": "fixture", "kind": "contract", "text": "Minimum penalty-free cancellation time: 1 months.\nService framework duration: 24 months."}
        with tempfile.TemporaryDirectory() as folder:
            directory = Path(folder)
            raw = {"kind": "contract", "fields": {"commitment_months": 1, "framework_months": 24}}
            for quote in (" \t\n ", ["1 months", " \t\n "]):
                with self.subTest(quote=quote):
                    raw["verbatim_support"] = quote
                    (directory / "fixture.json").write_text(json.dumps(raw))
                    result = score_extraction([document], directory)
                    self.assertEqual(result["quotes_whitespace_normalized_substrings"], 0)
                    self.assertEqual(result["fields_correct"], 2)

    def test_raw_conversion_matches_all_four_supplied_conditions(self):
        for condition in ("audit_notools", "audit_tools", "diag_notools", "diag_tools"):
            with self.subTest(condition=condition):
                prompts = read_jsonl(BUNDLE / "prompts" / ("audit_reporting.jsonl" if condition.startswith("audit_") else "audit_diagnostics.jsonl"))
                supplied = read_jsonl(BUNDLE / "predictions" / ("claude-fable-5-1_" + condition + ".jsonl"))
                converted, failures = convert_audit_raw(BUNDLE / "raw" / condition, prompts, supplied[0]["method"])
                self.assertEqual(converted, supplied)
                self.assertEqual(failures, [])

    def test_missing_audit_keeps_denominator_and_duplicate_claim_is_rejected(self):
        prompt = read_jsonl(BUNDLE / "prompts/audit_reporting.jsonl")[0]
        with tempfile.TemporaryDirectory() as folder:
            directory = Path(folder)
            converted, failures = convert_audit_raw(directory, [prompt], "fixture")
            self.assertEqual(len(failures), 7)
            self.assertEqual(len(converted[0]["claims"]), 7)
            self.assertTrue(all(c["label"] == "unresolved" and c["response_failure"] for c in converted[0]["claims"]))
            raw = json.loads((BUNDLE / "raw/audit_notools" / (prompt["case_id"] + ".json")).read_text())
            raw["claims"].append(copy.deepcopy(raw["claims"][0]))
            (directory / (prompt["case_id"] + ".json")).write_text(json.dumps(raw))
            with self.assertRaisesRegex(ValueError, "duplicate claim_id"):
                convert_audit_raw(directory, [prompt], "fixture")

    def test_archive_hashes_verify_and_changed_asset_is_rejected(self):
        verified = verify_archive(ARCHIVE, ROOT)
        self.assertEqual(verified["archived_files_verified"], 456)
        self.assertEqual(verified["total_per_call_prompt_hashes_verified"], 186)
        with tempfile.TemporaryDirectory() as folder:
            directory = Path(folder)
            manifest = {"files": {"asset.txt": {"sha256": "0" * 64, "bytes": 7}}}
            (directory / "source_manifest.json").write_text(json.dumps(manifest))
            (directory / "asset.txt").write_text("changed")
            with self.assertRaisesRegex(ValueError, "archive hash mismatch"):
                verify_archive(directory, ROOT)

    def test_extraction_typed_fields_missing_response_and_quote_definitions(self):
        document = {"doc_id": "fixture", "kind": "contract", "text": "Minimum penalty-free cancellation time: 1 months.\nService framework duration: 24 months."}
        with tempfile.TemporaryDirectory() as folder:
            directory = Path(folder)
            missing = score_extraction([document], directory)
            self.assertEqual((missing["fields_total"], missing["fields_correct"], missing["response_failures"]), (2, 0, 1))
            raw = {"kind": "contract", "fields": {"commitment_months": True, "framework_months": 24}, "verbatim_support": document["text"].replace("\n", " ")}
            path = directory / "fixture.json"
            path.write_text(json.dumps(raw))
            result = score_extraction([document], directory)
            self.assertEqual(result["fields_correct"], 1)  # Boolean is not integer 1.
            self.assertEqual(result["quotes_exact_substrings"], 0)
            self.assertEqual(result["quotes_whitespace_normalized_substrings"], 1)
            raw["fields"]["commitment_months"] = 1
            raw["verbatim_support"] = document["text"].splitlines()
            path.write_text(json.dumps(raw))
            self.assertEqual(score_extraction([document], directory)["quotes_exact_substrings"], 1)
            raw["verbatim_support"].append("absent fragment")
            path.write_text(json.dumps(raw))
            self.assertEqual(score_extraction([document], directory)["quotes_whitespace_normalized_substrings"], 0)
            with self.assertRaisesRegex(ValueError, "duplicate doc_id"):
                score_extraction([document, document], directory)

    def test_current_claude_results_are_rescored_and_preserve_false_supports(self):
        record = load_external_record(ROOT, "results/external/claude-fable-5.1/supplied_results.json")
        self.assertEqual(record["evidence_status"], "supplied_predictions_locally_rescored")
        self.assertFalse(record["actual_model_inference_independently_verified"])
        self.assertEqual(len(record["conditions"]), 4)
        self.assertTrue(all(r["supplied_summary_byte_identical"] for r in record["local_rescore"].values()))
        errors = record["error_analysis"]
        self.assertEqual(errors["audit_notools_disagreements"], 61)
        self.assertEqual(len(errors["false_supports"]), 2)
        for error in errors["false_supports"]:
            self.assertTrue(error["contract_hash_verification"])
            self.assertTrue(all(not check["matches"] for check in error["contract_hash_verification"]))
        for condition, strict, normalized in (("extract_text", 20, 25), ("extract_image", 21, 24)):
            group = record["extraction"][condition]
            self.assertEqual((group["fields_correct"], group["fields_total"]), (55, 55))
            self.assertEqual((group["quotes_exact_substrings"], group["quotes_whitespace_normalized_substrings"]), (strict, normalized))


if __name__ == "__main__":
    unittest.main()
