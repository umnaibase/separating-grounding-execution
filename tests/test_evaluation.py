"""Independent checks of scoring denominators, coverage and reproducibility."""

import copy
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

from boundarybench.evaluation import metrics, score, validate, reproduce, write_jsonl
from boundarybench.external import export_prompts


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"


def score_fixture():
    # Deliberately hand-labelled scoring inputs, independent of the checker.
    cases, refs, meta, predictions = [], [], [], []
    for cid, partition in (("dev-example", "dev"), ("test-example", "test")):
        cases.append({"case_id": cid, "claims": [{"claim_id": "reason", "kind": "conditional_execution"}]})
        refs.append({"case_id": cid, "labels": {"reason": "supported"}})
        meta.append({"case_id": cid, "scenario_id": cid, "split": partition,
                     "variant": "clean", "subtype": "hand-authored"})
        predictions.append({"case_id": cid, "method": "independent",
                            "claims": [{"claim_id": "reason", "kind": "conditional_execution", "label": "supported"}]})
    return predictions, refs, {"cases": meta}, cases


class MetricDenominatorTests(unittest.TestCase):
    def test_confusion_matrix_and_both_false_support_denominators(self):
        rows = [
            {"case_id": str(i), "scenario_id": str(i // 2), "reference": truth, "prediction": prediction}
            for i, (truth, prediction) in enumerate((
                ("supported", "supported"), ("supported", "unresolved"),
                ("contradicted", "supported"), ("contradicted", "contradicted"),
                ("unresolved", "supported"), ("unresolved", "unresolved"),
            ))
        ]
        result = metrics(rows)
        self.assertEqual(result["claims"], 6)
        self.assertEqual(result["episodes"], 6)
        self.assertEqual(result["scenario_families"], 3)
        self.assertEqual(result["accuracy"], 0.5)
        self.assertAlmostEqual(result["resolution_coverage"], 2 / 3)
        self.assertEqual(result["resolved_prediction_accuracy"], 0.5)
        self.assertEqual(result["false_support_count"], 2)
        self.assertEqual(result["endorsements"], 3)
        self.assertAlmostEqual(result["false_support_frequency"], 1 / 3)
        self.assertAlmostEqual(result["false_support_among_endorsements"], 2 / 3)
        self.assertEqual(result["confusion_matrix_reference_rows_prediction_columns"], {
            "supported": {"supported": 1, "contradicted": 0, "unresolved": 1},
            "contradicted": {"supported": 1, "contradicted": 1, "unresolved": 0},
            "unresolved": {"supported": 1, "contradicted": 0, "unresolved": 1},
        })
        self.assertAlmostEqual(result["per_class"]["supported"]["precision"], 1 / 3)
        self.assertEqual(result["per_class"]["supported"]["recall"], 0.5)
        self.assertEqual(result["per_class"]["supported"]["f1"], 0.4)

    def test_abstention_is_not_perfect_accuracy_and_zero_denominators_are_null(self):
        result = metrics([
            {"case_id": "a", "scenario_id": "same-family", "reference": truth, "prediction": "unresolved"}
            for truth in ("supported", "contradicted")
        ])
        self.assertEqual(result["accuracy"], 0)
        self.assertEqual(result["resolution_coverage"], 0)
        self.assertIsNone(result["resolved_prediction_accuracy"])
        self.assertIsNone(result["false_support_among_endorsements"])
        self.assertEqual(result["false_support_frequency"], 0)
        empty = metrics([])
        for name in ("accuracy", "resolution_coverage", "false_support_frequency", "false_support_among_endorsements"):
            self.assertIsNone(empty[name])


class ScoringCoverageTests(unittest.TestCase):
    def test_complete_scoring_and_split_selection(self):
        args = score_fixture()
        all_report = score(*args)
        self.assertEqual(all_report["methods"]["independent"]["all"]["claims"], 2)
        test_report = score(*args, split="test")
        self.assertEqual(test_report["methods"]["independent"]["all"]["claims"], 1)
        self.assertEqual(set(test_report["methods"]["independent"]["by_split"]), {"test"})

    def test_missing_case_cannot_improve_accuracy_by_selective_reporting(self):
        predictions, refs, metadata, cases = score_fixture()
        with self.assertRaises(ValueError):
            score(predictions[:1], refs, metadata, cases)

    def test_coverage_is_required_separately_for_every_method(self):
        predictions, refs, metadata, cases = score_fixture()
        partial = copy.deepcopy(predictions[0])
        partial["method"] = "selective-method"
        with self.assertRaises(ValueError):
            score(predictions + [partial], refs, metadata, cases)

    def test_claim_omission_or_duplication_is_rejected(self):
        for mutation in ("omit", "duplicate"):
            with self.subTest(mutation=mutation):
                predictions, refs, metadata, cases = score_fixture()
                predictions[0]["claims"] = [] if mutation == "omit" else predictions[0]["claims"] * 2
                with self.assertRaises(ValueError):
                    score(predictions, refs, metadata, cases)

    def test_unknown_case_cannot_be_hidden_by_split_filter(self):
        predictions, refs, metadata, cases = score_fixture()
        extra = copy.deepcopy(predictions[0])
        extra["case_id"] = "not-in-metadata"
        with self.assertRaises(ValueError):
            score(predictions + [extra], refs, metadata, cases, split="test")

    def test_duplicate_prediction_reference_and_metadata_ids_are_rejected(self):
        for collection in ("predictions", "reference", "metadata"):
            with self.subTest(collection=collection):
                predictions, refs, metadata, cases = score_fixture()
                target = {"predictions": predictions, "reference": refs, "metadata": metadata["cases"]}[collection]
                target.append(copy.deepcopy(target[0]))
                with self.assertRaises(ValueError):
                    score(predictions, refs, metadata, cases)

    def test_claim_kind_cannot_be_changed_to_improve_per_kind_results(self):
        predictions, refs, metadata, cases = score_fixture()
        predictions[0]["claims"][0]["kind"] = "candidate_stability"
        with self.assertRaises(ValueError):
            score(predictions, refs, metadata, cases)


class ReleaseIntegrityTests(unittest.TestCase):
    def test_shipped_dataset_validates(self):
        result = validate(DATA)
        self.assertEqual(result["episodes"], 100)
        self.assertEqual(result["claims"], 700)
        self.assertEqual(result["scenario_families"], 20)
        self.assertEqual(result["split_families"], {"dev": 8, "test": 12})
        self.assertTrue(result["manifest_verified"])

    def test_semantically_ignored_file_change_is_detected_by_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "data"
            shutil.copytree(DATA, target)
            with (target / "cases.jsonl").open("a", encoding="utf-8") as handle:
                handle.write("\n")
            with self.assertRaisesRegex(ValueError, "manifest mismatch"):
                validate(target)

    def test_missing_manifest_is_not_silently_trusted(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "data"
            shutil.copytree(DATA, target)
            (target / "manifest.json").unlink()
            with self.assertRaisesRegex(ValueError, "manifest.*missing"):
                validate(target)

    def test_reproduction_is_byte_identical_between_runs(self):
        with tempfile.TemporaryDirectory() as tmp:
            a, b = Path(tmp) / "a", Path(tmp) / "b"
            report = reproduce(DATA, a)
            reproduce(DATA, b)
            self.assertEqual(len(report["methods"]), 3)
            for name in ("predictions.jsonl", "summary.json", "summary.md"):
                self.assertEqual((a / name).read_bytes(), (b / name).read_bytes())


class CommandLineTests(unittest.TestCase):
    def run_cli(self, *arguments):
        return subprocess.run([sys.executable, "-m", "boundarybench", *map(str, arguments)],
                              cwd=ROOT, text=True, capture_output=True, check=False)

    def test_validate_cli(self):
        result = self.run_cli("validate", "--data-dir", DATA)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["claims"], 700)

    def test_audit_cli_does_not_require_any_reference_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            # This directory deliberately contains no reference or metadata.
            first_case = json.loads((DATA / "cases.jsonl").read_text(encoding="utf-8").splitlines()[0])
            write_jsonl(tmp / "input.jsonl", [first_case])
            result = self.run_cli("audit", "--cases", tmp / "input.jsonl", "--output", tmp / "output.jsonl")
            self.assertEqual(result.returncode, 0, result.stderr)
            prediction = json.loads((tmp / "output.jsonl").read_text(encoding="utf-8"))
            self.assertEqual(len(prediction["claims"]), 7)

    def test_reproduce_then_score_test_split_cli(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            reproduced = self.run_cli("reproduce", "--data-dir", DATA, "--output", tmp / "reproduced")
            self.assertEqual(reproduced.returncode, 0, reproduced.stderr)
            scored = self.run_cli("score", "--predictions", tmp / "reproduced" / "predictions.jsonl",
                                  "--reference", DATA / "reference.jsonl", "--metadata", DATA / "metadata.json",
                                  "--cases", DATA / "cases.jsonl", "--split", "test", "--output", tmp / "scored")
            self.assertEqual(scored.returncode, 0, scored.stderr)
            report = json.loads((tmp / "scored" / "summary.json").read_text(encoding="utf-8"))
            self.assertEqual(len(report["methods"]), 3)
            for result in report["methods"].values():
                self.assertEqual(result["all"]["episodes"], 60)
                self.assertEqual(result["all"]["claims"], 420)
                self.assertEqual(result["all"]["scenario_families"], 12)

    def test_cli_validation_errors_return_nonzero(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self.run_cli("validate", "--data-dir", tmp)
            self.assertEqual(result.returncode, 2)
            self.assertIn("error:", result.stderr)


class ExternalPromptTests(unittest.TestCase):
    def test_export_requires_no_reference_labels_and_filters_splits(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            data = tmp / "input"
            data.mkdir()
            for name in ("cases.jsonl", "metadata.json"):
                shutil.copyfile(DATA / name, data / name)
            self.assertFalse((data / "reference.jsonl").exists())
            for split, expected in (("test", 60), ("all", 100), ("dev", 40)):
                output = tmp / f"{split}.jsonl"
                with redirect_stdout(io.StringIO()):
                    export_prompts(data, split, output)
                self.assertEqual(len(output.read_text(encoding="utf-8").splitlines()), expected)

    def test_model_messages_exclude_join_id_subject_and_reference_metadata(self):
        case = json.loads((DATA / "cases.jsonl").read_text(encoding="utf-8").splitlines()[0])
        case["case_id"] = "FORBIDDEN_JOIN_ID_SENTINEL"
        case["subject"] = "FORBIDDEN_SUBJECT_SENTINEL"
        case["reference"] = {"labels": "FORBIDDEN_REFERENCE_SENTINEL"}
        case["metadata"] = "FORBIDDEN_METADATA_SENTINEL"
        metadata = {"cases": [{"case_id": case["case_id"], "split": "test",
                               "private_note": "FORBIDDEN_PRIVATE_NOTE_SENTINEL"}]}
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            write_jsonl(tmp / "cases.jsonl", [case])
            (tmp / "metadata.json").write_text(json.dumps(metadata), encoding="utf-8")
            with redirect_stdout(io.StringIO()):
                export_prompts(tmp, "test", tmp / "prompts.jsonl")
            prompt = json.loads((tmp / "prompts.jsonl").read_text(encoding="utf-8"))
            self.assertEqual(prompt["case_id"], case["case_id"])
            for message in prompt["messages"]:
                self.assertNotIn("FORBIDDEN_", message["content"])
            observable = json.loads(prompt["messages"][1]["content"])
            self.assertEqual(set(observable), {"sources", "citations", "record", "alternatives", "claims"})
            self.assertEqual(observable["claims"], case["claims"])


if __name__ == "__main__":
    unittest.main()
