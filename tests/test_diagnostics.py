"""Explicit expected branch cases for the author-written v1.1 diagnostics."""

import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

from boundarybench.audit import METHODS, audit_case, decide
from boundarybench.evaluation import read_jsonl, reproduce, reproduce_diagnostics, validate_diagnostics


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DIAGNOSTICS = DATA / "diagnostics"

# Explicit expectations, written from the toy-policy boundary rather than
# copied from checker output. A false assertion negates the stability claim.
EXPECTED = {
    ((6, 9), True): ("supported", ["standard_processing", "standard_processing"]),
    ((6, 9), False): ("contradicted", ["standard_processing", "standard_processing"]),
    ((3, 5), True): ("supported", ["manual_review", "manual_review"]),
    ((3, 5), False): ("contradicted", ["manual_review", "manual_review"]),
    ((3, 6, 9), True): ("contradicted", ["manual_review", "standard_processing", "standard_processing"]),
    ((3, 6, 9), False): ("supported", ["manual_review", "standard_processing", "standard_processing"]),
    ((6, 9, 12), True): ("supported", ["standard_processing", "standard_processing", "standard_processing"]),
    ((6, 9, 12), False): ("contradicted", ["standard_processing", "standard_processing", "standard_processing"]),
}

MAIN_V1_SHA256 = {
    "data/cases.jsonl": "24385a6efe0374c74a8e79fb80fd8c916c3a4cb22677adb8bd13732b668b237a",
    "data/reference.jsonl": "fd13946efec40caa483b64d4593fb767baad598ad91c5c36043ea640388b9e41",
    "data/metadata.json": "8127c5c326b782c3682291888d36bd2d024a7cbafe371a48839ac78bad996345",
    "results/predictions.jsonl": "fe15abbef438db26bee2399a45ae2ea206968638c64349db8ba9a2b3ecd4c2bc",
    "results/summary.json": "7f1013738be85e26254d1e297dcabe7073fcec71e0cf55567e3550746af23072",
    "results/summary.md": "071b0b00edf26a459f7cf66d28d1c0feff64109050905c69026f467a2247b8dc",
}


class DiagnosticBranchTests(unittest.TestCase):
    def test_all_candidate_boundaries_and_both_assertion_polarities(self):
        cases = read_jsonl(DIAGNOSTICS / "cases.jsonl")
        references = {r["case_id"]: r["labels"] for r in read_jsonl(DIAGNOSTICS / "reference.jsonl")}
        seen = set()
        for case in cases:
            claim = next(c for c in case["claims"] if c["kind"] == "candidate_stability")
            key = (tuple(case["alternatives"]), claim["asserted_value"])
            seen.add(key)
            with self.subTest(candidates=key[0], asserted_stable=key[1]):
                c6_label, expected_outcomes = EXPECTED[key]
                outcomes = [decide({**case["record"]["input"], "commitment_months": n}, case["record"]["policy"]) for n in case["alternatives"]]
                self.assertEqual(outcomes, expected_outcomes)
                expected_labels = {"c1": "supported", "c2": "unresolved", "c3": "supported", "c4": "supported", "c5": "supported", "c6": c6_label, "c7": "contradicted"}
                self.assertEqual(references[case["case_id"]], expected_labels)
                for method in METHODS:
                    actual = {p["claim_id"]: p["label"] for p in audit_case(case, method)}
                    self.assertEqual(actual["c6"], c6_label)
                    self.assertEqual(actual["c7"], "contradicted")
                    if method == "boundary":
                        self.assertEqual(actual, expected_labels)
        self.assertEqual(seen, set(EXPECTED))

    def test_positive_negative_pairs_preserve_the_observed_evidence(self):
        pairs = {}
        for case in read_jsonl(DIAGNOSTICS / "cases.jsonl"):
            key = tuple(case["alternatives"])
            if key not in pairs:
                pairs[key] = case
                continue
            positive = pairs[key]
            for field in ("subject", "sources", "citations", "record", "alternatives"):
                self.assertEqual(case[field], positive[field])
            for left, right in zip(case["claims"], positive["claims"]):
                if left["kind"] != "candidate_stability":
                    self.assertEqual(left, right)
            self.assertNotEqual(case["claims"][5]["asserted_value"], positive["claims"][5]["asserted_value"])
            self.assertIn("do not all", case["claims"][5]["text"])

    def test_every_candidate_has_valid_cited_source_evidence_but_no_precedence(self):
        for case in read_jsonl(DIAGNOSTICS / "cases.jsonl"):
            with self.subTest(case_id=case["case_id"]):
                refs = case["citations"]["contract"]
                retained = {s["source_id"]: s for s in case["sources"]}
                self.assertEqual(len(refs), len(case["alternatives"]))
                for ref in refs:
                    source = retained[ref["source_id"]]
                    self.assertEqual(ref["version"], source["version"])
                    self.assertEqual(ref["sha256"], hashlib.sha256(source["text"].encode()).hexdigest())
                labels = {p["claim_id"]: p["label"] for p in audit_case(case)}
                self.assertEqual(labels["c1"], "supported")
                self.assertEqual(labels["c2"], "unresolved")


class DiagnosticReleaseTests(unittest.TestCase):
    def test_separate_diagnostic_shape_and_integrity(self):
        result = validate_diagnostics(DIAGNOSTICS)
        self.assertEqual(result, {"episodes": 8, "claims": 56, "scenario_families": 4, "split_families": {"diagnostic": 4}, "manifest_verified": True})
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "diagnostics"
            shutil.copytree(DIAGNOSTICS, target)
            with (target / "cases.jsonl").open("a", encoding="utf-8") as handle:
                handle.write("\n")
            with self.assertRaisesRegex(ValueError, "manifest mismatch"):
                validate_diagnostics(target)

    def test_main_corpus_and_original_aggregate_reports_are_preserved(self):
        for name, expected in MAIN_V1_SHA256.items():
            with self.subTest(file=name):
                self.assertEqual(hashlib.sha256((ROOT / name).read_bytes()).hexdigest(), expected)

    def test_offline_generation_and_reproduction_preserve_original_and_new_results(self):
        with tempfile.TemporaryDirectory() as temp:
            temp = Path(temp)
            process = subprocess.run([sys.executable, str(ROOT / "scripts/generate_data.py"), "--output", str(temp / "data")], cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(process.returncode, 0, process.stderr)
            for relative in ("cases.jsonl", "reference.jsonl", "metadata.json", "manifest.json"):
                self.assertEqual((temp / "data" / relative).read_bytes(), (DATA / relative).read_bytes())
                self.assertEqual((temp / "data/diagnostics" / relative).read_bytes(), (DIAGNOSTICS / relative).read_bytes())
            main = reproduce(temp / "data", temp / "results")
            self.assertEqual(main["methods"]["boundary"]["all"]["claims"], 700)
            for relative in ("predictions.jsonl", "summary.json", "summary.md"):
                self.assertEqual((temp / "results" / relative).read_bytes(), (ROOT / "results" / relative).read_bytes())
                self.assertEqual((temp / "results/diagnostics" / relative).read_bytes(), (ROOT / "results/diagnostics" / relative).read_bytes())
            separate = reproduce_diagnostics(temp / "data/diagnostics", temp / "separate")
            self.assertEqual(separate["methods"]["boundary"]["all"]["claims"], 56)
            self.assertEqual(separate["methods"]["boundary"]["all"]["accuracy"], 1)
            self.assertNotIn("test_by_kind", separate["methods"]["boundary"])

    def test_diagnostics_cli_runs_without_the_main_corpus(self):
        with tempfile.TemporaryDirectory() as temp:
            temp = Path(temp)
            shutil.copytree(DIAGNOSTICS, temp / "data")
            process = subprocess.run([sys.executable, "-m", "boundarybench", "diagnostics", "--data-dir", str(temp / "data"), "--output", str(temp / "results")], cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(process.returncode, 0, process.stderr)
            report = json.loads((temp / "results/summary.json").read_text())
            self.assertEqual(report["data_validation"]["claims"], 56)
            self.assertEqual(report["protocol"], "1.1.0")


if __name__ == "__main__":
    unittest.main()
