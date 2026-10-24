"""Pilot isolation, schedules and prespecified failure-denominator checks.

Any invented responses here are temporary unit-test fixtures, never model
observations and never written to the published pilot results directories.
"""

import copy
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from boundarybench.pilot import (
    export, sanitize, integrity_observations, verify_frozen, read_jsonl,
    _responses, score_pilot, write_json,
)


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"


class PilotInputTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.base = Path(cls.temp.name)
        # Export must work without any reference.jsonl or checker predictions.
        cls.sources = cls.base / "source"
        for relative in ("cases.jsonl", "metadata.json", "diagnostics/cases.jsonl", "diagnostics/metadata.json"):
            destination = cls.sources / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(DATA / relative, destination)
        cls.pilot = cls.base / "pilot"
        cls.selection = export(cls.sources, cls.pilot)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_export_covers_reporting_and_diagnostics_without_reference_files(self):
        self.assertEqual(self.selection["main_reporting_episodes"], 60)
        self.assertEqual(self.selection["diagnostic_episodes"], 8)
        prompts = read_jsonl(self.pilot / "prompts/text_cases.jsonl")
        episodes = {p["episode_id"] for p in prompts}
        scheduled = [e for b in self.selection["text_batches"] for e in b["episode_ids"]]
        self.assertEqual(len(episodes), 68)
        self.assertEqual(len(scheduled), len(set(scheduled)))
        self.assertEqual(set(scheduled), episodes)
        self.assertTrue(all(len(b["episode_ids"]) == 17 for b in self.selection["text_batches"]))

    def test_frozen_export_is_deterministic_and_refuses_overwrite(self):
        second = self.base / "second"
        if second.exists():
            shutil.rmtree(second)
        export(self.sources, second)
        for path in self.pilot.rglob("*"):
            if path.is_file():
                self.assertEqual(path.read_bytes(), (second / path.relative_to(self.pilot)).read_bytes())
        verify_frozen(self.pilot)
        with self.assertRaisesRegex(ValueError, "Refusing to replace"):
            export(self.sources, self.pilot)

    def test_model_inputs_exclude_original_ids_metadata_and_source_text_for_images(self):
        join = json.loads((self.pilot / "join_map.json").read_text())["records"]
        forbidden_ids = {row["original_case_id"] for row in join} | {row["scenario_id"] for row in join}
        forbidden_ids |= {old for row in join for old in row["source_id_map"]}
        for relative in ("prompts/text_cases.jsonl", "prompts/image_cases.jsonl"):
            serialized = (self.pilot / relative).read_text()
            for forbidden in forbidden_ids:
                self.assertNotIn(forbidden, serialized)
        for batch_info in self.selection["text_batches"] + self.selection["paired_text_batches"] + self.selection["image_batches"]:
            batch = json.loads((self.pilot / batch_info["path"]).read_text())
            self.assertNotIn("Return JSON with one key, claims", batch["instructions"])
            self.assertIn("Return exactly one JSON object with the key episodes", batch["instructions"])
            self.assertIn("false asserts", batch["instructions"])
            for row in batch["episodes"]:
                observable = row["observable"]
                self.assertNotIn("subject", observable)
                self.assertNotIn("metadata", observable)
                self.assertNotIn("case_id", observable)
                for source in observable["sources"]:
                    self.assertRegex(source["source_id"], r"^s\d{2}$")
                    if batch_info in self.selection["image_batches"]:
                        self.assertNotIn("text", source)

    def test_paired_conditions_have_identical_order_and_nontext_evidence(self):
        paired = {row["episode_id"] for row in self.selection["paired_image_episodes"]}
        self.assertEqual(len(paired), 12)
        for left, right in zip(self.selection["paired_text_batches"], self.selection["image_batches"]):
            self.assertEqual(left["episode_ids"], right["episode_ids"])
            self.assertEqual(len(left["episode_ids"]), 6)
            text = json.loads((self.pilot / left["path"]).read_text())["episodes"]
            image = json.loads((self.pilot / right["path"]).read_text())["episodes"]
            for t, i in zip(text, image):
                stripped = copy.deepcopy(t["observable"])
                for source in stripped["sources"]:
                    del source["text"]
                actual = copy.deepcopy(i["observable"])
                del actual["source_image"]
                self.assertEqual(stripped, actual)

    def test_integrity_frontend_does_not_interpret_source_or_policy(self):
        case = read_jsonl(DATA / "cases.jsonl")[0]
        observed, _ = sanitize(case)
        original = integrity_observations(observed)
        # Semantics and policy can change without affecting byte/citation checks
        # provided the text and citations are retained identically.
        observed["record"]["policy"] = {"nonsense": "must not be executed"}
        observed["record"]["input"] = {"not": "numeric"}
        observed["alternatives"] = [None]
        observed["claims"] = [{"pretend": "instructions"}]
        self.assertEqual(integrity_observations(observed), original)
        self.assertTrue(all("label" not in item and "decision" not in item for item in original))
        observed["sources"].append(copy.deepcopy(observed["sources"][0]))
        ambiguous = integrity_observations(observed)
        self.assertEqual(ambiguous[0]["matching_retained_artifacts"], 2)

    def test_freeze_integrity_detects_prompt_changes(self):
        target = self.base / "tampered"
        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(self.pilot, target)
        path = target / "batches/text_batch_01.json"
        path.write_text(path.read_text() + "\n")
        with self.assertRaisesRegex(ValueError, "Frozen pilot input mismatch"):
            verify_frozen(target)


class PilotFailureTests(unittest.TestCase):
    def setUp(self):
        self.expected = {"one": {f"c{i + 1}": kind for i, kind in enumerate((
            "contract_lineage", "commitment_grounding", "dispute_grounding",
            "conditional_execution", "final_action_by_rule", "candidate_stability", "sufficient_dispute_reason",
        ))}}
        self.schedule = [{"path": "batches/test_batch.json", "episode_ids": ["one"]}]
        self.fixture = {"episodes": [{"episode_id": "one", "claims": [
            {"claim_id": cid, "kind": kind, "label": "unresolved", "check": "UNIT TEST FIXTURE, NOT MODEL OUTPUT", "evidence": []}
            for cid, kind in self.expected["one"].items()
        ]}]}

    def test_valid_literal_output_is_preserved_and_marked_nonfailure(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "test_batch.json"
            write_json(path, self.fixture)
            original = path.read_bytes()
            predictions, hashes, failures = _responses(Path(directory), self.expected, self.schedule)
            self.assertEqual(path.read_bytes(), original)
            self.assertEqual(failures, [])
            self.assertTrue(hashes["test_batch.json"])
            self.assertFalse(any(c["conversion_failure"] for c in predictions["one"]["claims"]))

    def test_malformed_omitted_duplicate_or_wrong_values_fail_entire_batch(self):
        mutations = []
        wrong = copy.deepcopy(self.fixture)
        wrong["episodes"][0]["claims"][0]["label"] = "probably supported"
        mutations.append(wrong)
        wrong = copy.deepcopy(self.fixture)
        wrong["episodes"][0]["claims"].pop()
        mutations.append(wrong)
        wrong = copy.deepcopy(self.fixture)
        wrong["episodes"].append(copy.deepcopy(wrong["episodes"][0]))
        mutations.append(wrong)
        wrong = copy.deepcopy(self.fixture)
        wrong["episodes"][0]["claims"][1] = copy.deepcopy(wrong["episodes"][0]["claims"][0])
        mutations.append(wrong)
        mutations.extend([{"episodes": []}, {"claims": []}])
        for mutation in mutations:
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "test_batch.json"
                write_json(path, mutation)
                raw = path.read_bytes()
                predictions, _, failures = _responses(Path(directory), self.expected, self.schedule)
                self.assertEqual(len(failures), 1)
                self.assertEqual(len(predictions["one"]["claims"]), 7)
                self.assertTrue(all(c["conversion_failure"] and c["label"] == "unresolved" for c in predictions["one"]["claims"]))
                self.assertEqual(path.read_bytes(), raw)

    def test_missing_or_duplicate_json_keys_fail_without_retry(self):
        with tempfile.TemporaryDirectory() as directory:
            predictions, hashes, failures = _responses(Path(directory), self.expected, self.schedule)
            self.assertEqual(hashes["test_batch.json"], None)
            self.assertEqual(failures[0]["claims_converted"], 7)
            (Path(directory) / "test_batch.json").write_text('{"episodes":[],"episodes":[]}')
            _, _, failures = _responses(Path(directory), self.expected, self.schedule)
            self.assertIn("Duplicate JSON", failures[0]["reason"])

    def test_all_missing_scoring_keeps_denominators_and_never_rewards_reference_unresolved(self):
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            pilot = directory / "pilot"
            export(DATA, pilot)
            run = directory / "run.json"
            write_json(run, {"status": "completed", "run_id": "unit-test-only", "model_display_name": "NO MODEL: UNIT TEST"})
            report = score_pilot(pilot, DATA, directory / "missing", directory / "report", run,
                                 directory / "missing-images", directory / "missing-paired-text")
            for name, expected in (("main_reporting", 420), ("diagnostics", 56), ("paired_text", 84), ("paired_image", 84)):
                group = next(iter(report["reports"][name]["methods"].values()))
                self.assertEqual(group["all"]["claims"], expected)
                self.assertEqual(group["all"]["conversion_failure_claims"], expected)
                self.assertEqual(group["all"]["failure_adjusted_agreement"], 0)
                self.assertGreater(group["all"]["ordinary_label_agreement"], 0)
                self.assertEqual(group["scope_groups"]["six_reasoning_scopes"]["claims"], expected * 6 // 7)
            paired = next(iter(report["reports"]["paired_image"]["methods"].values()))
            self.assertEqual(paired["scope_groups"]["source_grounding_c2_c3"]["claims"], 24)
            self.assertEqual(report["spelled_eighteen_commitment_claims"]["metrics"]["claims"], 2)
            self.assertEqual(len(report["conversion_failures"]["text"]), 4)
            self.assertEqual(len(report["conversion_failures"]["paired_text"]), 2)
            self.assertEqual(len(report["conversion_failures"]["image"]), 2)


if __name__ == "__main__":
    unittest.main()
