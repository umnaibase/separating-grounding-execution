"""Evidence-status and missing-value checks for report-only model aggregates."""

import copy
import json
from pathlib import Path
import unittest

from boundarybench.comparison import load_external_record, validate_external_record, validate_reported_metrics


ROOT = Path(__file__).resolve().parents[1]


class ExternalEvidenceTests(unittest.TestCase):
    def test_pending_model_metrics_are_null_not_zero(self):
        pending = load_external_record(ROOT, "results/external/claude-fable-5.1/reported_results.json")
        self.assertEqual(pending["model_name"], "Claude Fable 5.1")
        self.assertEqual(pending["evidence_status"], "pending")
        self.assertTrue(all(value is None for value in pending["metrics"].values()))
        invalid = copy.deepcopy(pending)
        invalid["metrics"]["main_reporting"] = {"claims": 420, "agreement_correct": 0}
        with self.assertRaisesRegex(ValueError, "null metrics"):
            validate_external_record(invalid)

    def test_report_only_grok_provenance_does_not_imply_rescoring_or_missing_metrics(self):
        record = load_external_record(ROOT, "results/external/grok-4.7/reported_results.json")
        self.assertEqual(record["evidence_status"], "externally_reported_not_rescored")
        self.assertFalse(record["artifacts"]["raw_predictions_provided"])
        self.assertEqual(record["metrics"]["diagnostics"]["agreement_correct"], 56)
        self.assertIsNone(record["metrics"]["diagnostics"]["resolved_count"])
        self.assertIsNone(record["metrics"]["diagnostics"]["endorsements"])
        self.assertEqual(record["metrics"]["diagnostics"]["false_support_count"], 0)
        invalid = copy.deepcopy(record)
        invalid["evidence_status"] = "locally_rescored_archived_outputs"
        with self.assertRaisesRegex(ValueError, "cannot claim locally rescored"):
            validate_external_record(invalid)

    def test_inconsistent_reported_numerators_and_label_totals_are_rejected(self):
        record = json.loads((ROOT / "results/external/grok-4.7/reported_results.json").read_text())
        original = record["metrics"]["main_reporting"]
        validate_reported_metrics(original)
        for field, bad_value in (("agreement_correct", 421), ("resolved_count", 387), ("false_support_count", 334)):
            with self.subTest(field=field):
                invalid = copy.deepcopy(original)
                invalid[field] = bad_value
                with self.assertRaises(ValueError):
                    validate_reported_metrics(invalid)

    def test_supplied_predictions_can_have_rescored_status_without_verified_inference(self):
        record = load_external_record(ROOT, "results/external/grok-4.7/supplied_results.json")
        self.assertEqual(record["evidence_status"], "supplied_predictions_locally_rescored")
        self.assertFalse(record["actual_model_inference_independently_verified"])
        self.assertEqual(record["metrics"]["main_reporting"]["claims"], 420)
        self.assertEqual(record["local_rescore"]["main_reporting"]["input_prediction_episodes"], 100)
        self.assertEqual(record["local_rescore"]["main_reporting"]["selected_episodes"], 60)
        self.assertEqual(record["metrics"]["diagnostics"]["resolved_count"], 48)
        self.assertEqual(record["metrics"]["diagnostics"]["endorsements"], 36)
        self.assertTrue(record["local_rescore"]["supplied_main_summary_byte_identical_to_local_rescore"])


if __name__ == "__main__":
    unittest.main()
