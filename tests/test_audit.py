"""Independent semantic and metamorphic checks for the public audit API.

Fixtures are authored directly here; neither the generator nor its construction
reference is imported. These tests check the distinction between source support,
execution faithfulness and action attribution, rather than aggregate accuracy.
"""

import copy
import hashlib
import unittest

from boundarybench.audit import audit_case, decide


SUPPORTED = "supported"
CONTRADICTED = "contradicted"
UNRESOLVED = "unresolved"

KINDS = (
    "contract_lineage",
    "commitment_grounding",
    "dispute_grounding",
    "conditional_execution",
    "final_action_by_rule",
    "candidate_stability",
    "sufficient_dispute_reason",
)


def source(source_id, kind, text, version="1"):
    return {"source_id": source_id, "kind": kind, "version": version, "text": text}


def citation(item):
    return {
        "source_id": item["source_id"],
        "version": item["version"],
        "sha256": hashlib.sha256(item["text"].encode("utf-8")).hexdigest(),
    }


def contract_text(commitment=8):
    # This deliberately small, documented language is a fixture protocol, not
    # a demonstration of natural-language contract interpretation.
    return f"Minimum penalty-free cancellation time: {commitment} months.\nService framework duration: 24 months."


def transaction_text(disputed=1, eligible=100):
    return f"Observation window: 2026-01-01/2026-01-31\nEligible transactions: {eligible}\nDisputed transactions: {disputed}"


def fixture(disputed=1, eligible=100, commitment=8):
    contract = source("contract-A", "contract", contract_text(commitment))
    transactions = source("transactions-A", "transactions", transaction_text(disputed, eligible))
    dispute_trigger = disputed * 50 >= eligible
    commitment_trigger = commitment < 6
    output = "manual_review" if dispute_trigger or commitment_trigger else "standard_processing"
    asserted_values = (
        True,
        commitment,
        {"numerator": disputed, "denominator": eligible},
        output,
        output,
        True,
        True,
    )
    return {
        "case_id": "standalone-case",
        "subject": "Fictional merchant for unit tests",
        "sources": [contract, transactions],
        "citations": {"contract": [citation(contract)], "transactions": [citation(transactions)]},
        "record": {
            "input": {"disputed": disputed, "eligible": eligible, "commitment_months": commitment},
            "policy": {
                "id": "toy-v1",
                "dispute_threshold": {"numerator": 1, "denominator": 50},
                "commitment_threshold_months": 6,
            },
            "trace": {"dispute_trigger": dispute_trigger, "commitment_trigger": commitment_trigger},
            "rule_output": output,
            "final_output": output,
            "override": None,
            "action_history_complete": True,
        },
        "alternatives": [commitment],
        "claims": [
            {"claim_id": f"c{i}", "kind": kind, "text": f"Scoped fixture claim: {kind}", "asserted_value": value}
            for i, (kind, value) in enumerate(zip(KINDS, asserted_values), 1)
        ],
    }


def predictions(case, method="boundary"):
    rows = audit_case(case, method=method)
    return {row["claim_id"]: row for row in rows}


def labels(case, method="boundary"):
    return {key: value["label"] for key, value in predictions(case, method).items()}


def replace_source(case, kind, text, refresh_citation=True):
    index = next(i for i, item in enumerate(case["sources"]) if item["kind"] == kind)
    case["sources"][index]["text"] = text
    if refresh_citation:
        case["citations"][kind] = [citation(case["sources"][index])]


class DecisionSemanticsTests(unittest.TestCase):
    def test_exact_threshold_inclusive_and_commitment_threshold_exclusive(self):
        for disputed, eligible, months, expected in (
            (1, 50, 6, "manual_review"),
            (1, 51, 6, "standard_processing"),
            (0, 100, 5, "manual_review"),
            (0, 100, 6, "standard_processing"),
        ):
            with self.subTest(disputed=disputed, eligible=eligible, months=months):
                case = fixture(disputed, eligible, months)
                self.assertEqual(decide(case["record"]["input"], case["record"]["policy"]), expected)
                self.assertEqual(labels(case)["c4"], SUPPORTED)

    def test_large_integers_are_not_rounded_into_threshold(self):
        # Binary64 cannot distinguish these adjacent numerators reliably.
        denominator = 50 * 10**18
        case = fixture(10**18 - 1, denominator, 6)
        self.assertEqual(decide(case["record"]["input"], case["record"]["policy"]), "standard_processing")
        case["record"]["input"]["disputed"] += 1
        self.assertEqual(decide(case["record"]["input"], case["record"]["policy"]), "manual_review")


class SourceAndExecutionTests(unittest.TestCase):
    def test_clean_all_claims_and_evidence_contract(self):
        case = fixture()
        expected = dict(zip((f"c{i}" for i in range(1, 8)), (
            SUPPORTED, SUPPORTED, SUPPORTED, SUPPORTED, SUPPORTED, SUPPORTED, CONTRADICTED,
        )))
        self.assertEqual(labels(case), expected)
        rows = audit_case(case)
        self.assertEqual(len(rows), 7)
        for row in rows:
            self.assertIn(row["kind"], KINDS)
            self.assertIsInstance(row["check"], str)
            self.assertTrue(row["check"].strip())
            self.assertIsInstance(row["evidence"], list)
            self.assertTrue(all(isinstance(item, str) for item in row["evidence"]))

    def test_incorrect_extraction_can_have_faithful_execution(self):
        case = fixture(commitment=4)
        replace_source(case, "contract", contract_text(8))
        result = labels(case)
        self.assertEqual(result["c1"], SUPPORTED)
        self.assertEqual(result["c2"], CONTRADICTED)
        self.assertEqual(result["c4"], SUPPORTED)
        self.assertEqual(result["c5"], SUPPORTED)

    def test_missing_source_withholds_source_support_only(self):
        case = fixture()
        case["sources"] = [item for item in case["sources"] if item["kind"] != "contract"]
        result = labels(case)
        self.assertEqual(result["c1"], UNRESOLVED)
        self.assertEqual(result["c2"], UNRESOLVED)
        self.assertEqual(result["c3"], SUPPORTED)
        self.assertEqual(result["c4"], SUPPORTED)

    def test_known_digest_mismatch_is_lineage_contradiction_not_semantic_support(self):
        case = fixture()
        replace_source(case, "contract", contract_text(4), refresh_citation=False)
        result = labels(case)
        self.assertEqual(result["c1"], CONTRADICTED)
        self.assertEqual(result["c2"], UNRESOLVED)
        self.assertEqual(result["c4"], SUPPORTED)

    def test_version_mismatch_with_same_text_does_not_establish_lineage(self):
        case = fixture()
        case["citations"]["contract"][0]["version"] = "not-the-retained-version"
        result = labels(case)
        self.assertEqual(result["c1"], CONTRADICTED)
        self.assertEqual(result["c2"], UNRESOLVED)

    def test_valid_but_conflicting_contracts_are_unresolved(self):
        case = fixture()
        second = source("contract-B", "contract", contract_text(4))
        case["sources"].append(second)
        case["citations"]["contract"].append(citation(second))
        result = labels(case)
        self.assertEqual(result["c1"], SUPPORTED)
        self.assertEqual(result["c2"], UNRESOLVED)

    def test_conflicting_transactions_are_unresolved(self):
        case = fixture()
        second = source("transactions-B", "transactions", transaction_text(7, 100))
        case["sources"].append(second)
        case["citations"]["transactions"].append(citation(second))
        self.assertEqual(labels(case)["c3"], UNRESOLVED)

    def test_unsupported_source_language_is_not_silently_interpreted(self):
        case = fixture()
        replace_source(case, "contract", "The merchant may leave whenever it wishes, subject to secret terms.")
        result = labels(case)
        self.assertEqual(result["c1"], SUPPORTED)
        self.assertEqual(result["c2"], UNRESOLVED)

    def test_negated_or_appended_clause_cannot_pass_by_substring_match(self):
        for text in (
            "It is false that " + contract_text(8),
            contract_text(8) + "\nHowever, early cancellation is prohibited.",
            "Minimum penalty-free cancellation time: eight months.\nService framework duration: 24 months.",
        ):
            with self.subTest(text=text):
                case = fixture()
                replace_source(case, "contract", text)
                result = labels(case)
                self.assertEqual(result["c1"], SUPPORTED)
                self.assertEqual(result["c2"], UNRESOLVED)

    def test_framework_duration_is_not_the_penalty_free_commitment(self):
        for text in (
            "The service framework lasts 24 months. The merchant may terminate after 8 months without penalty.",
            "Penalty-free termination is available once 8 months have elapsed. Framework duration: 24 months.",
        ):
            with self.subTest(text=text):
                case = fixture(commitment=8)
                replace_source(case, "contract", text)
                self.assertEqual(labels(case)["c2"], SUPPORTED)

    def test_malformed_inputs_withhold_only_dependent_computational_claims(self):
        for key, value in (("disputed", True), ("eligible", 0), ("eligible", None),
                           ("commitment_months", -1), ("commitment_months", "8")):
            with self.subTest(key=key, value=value):
                case = fixture()
                case["record"]["input"][key] = value
                result = labels(case)
                self.assertEqual(result["c4"], UNRESOLVED)
                if key == "commitment_months":
                    # Stability substitutes valid candidates for this field.
                    # The sufficient-dispute claim depends only on the ratio.
                    self.assertEqual(result["c6"], SUPPORTED)
                    self.assertEqual(result["c7"], CONTRADICTED)
                else:
                    self.assertEqual(result["c6"], UNRESOLVED)
                    self.assertEqual(result["c7"], UNRESOLVED)

    def test_grounding_checks_asserted_values_not_just_claim_kind(self):
        case = fixture()
        case["claims"][1]["asserted_value"] = 24
        case["claims"][2]["asserted_value"] = {"numerator": 2, "denominator": 100}
        result = labels(case)
        self.assertEqual(result["c2"], CONTRADICTED)
        self.assertEqual(result["c3"], CONTRADICTED)

    def test_execution_and_action_check_asserted_outcome(self):
        case = fixture()
        case["claims"][3]["asserted_value"] = "manual_review"
        case["claims"][4]["asserted_value"] = "manual_review"
        result = labels(case)
        self.assertEqual(result["c4"], CONTRADICTED)
        self.assertEqual(result["c5"], CONTRADICTED)

    def test_rule_trace_inconsistency_is_detected(self):
        case = fixture(disputed=3, eligible=100)
        case["record"]["trace"]["dispute_trigger"] = False
        self.assertEqual(labels(case)["c4"], CONTRADICTED)

    def test_two_trigger_trace_cannot_be_replaced_by_short_circuit(self):
        case = fixture(disputed=3, eligible=100, commitment=4)
        case["record"]["trace"]["commitment_trigger"] = False
        self.assertEqual(labels(case)["c4"], CONTRADICTED)

    def test_unsupported_policy_cannot_get_execution_endorsement(self):
        case = fixture()
        case["record"]["policy"]["id"] = "unvalidated-policy"
        result = labels(case)
        for claim in ("c4", "c6", "c7"):
            self.assertEqual(result[claim], UNRESOLVED)

    def test_authenticity_is_outside_supported_claim_scope(self):
        # These are fabricated text sources. Support can only establish their
        # relationship to the retained record; no real merchant is validated.
        case = fixture()
        self.assertEqual(labels(case)["c1"], SUPPORTED)
        self.assertEqual(labels(case)["c2"], SUPPORTED)
        case["external_world_truth"] = {"contract_authentic": False}
        self.assertEqual(labels(case)["c1"], SUPPORTED)
        self.assertEqual(labels(case)["c2"], SUPPORTED)


class AlternativeAndActionTests(unittest.TestCase):
    def test_boolean_assertions_are_evaluated_as_propositions(self):
        case = fixture()
        case["claims"][5]["asserted_value"] = False
        case["claims"][6]["asserted_value"] = False
        result = labels(case)
        self.assertEqual(result["c6"], CONTRADICTED)
        self.assertEqual(result["c7"], SUPPORTED)

    def test_empty_candidates_are_unresolved_not_vacuously_stable(self):
        case = fixture()
        case["alternatives"] = []
        self.assertEqual(labels(case)["c6"], UNRESOLVED)

    def test_invalid_candidate_makes_stability_unresolved(self):
        for invalid in (-1, 5.5, "6", True, None):
            with self.subTest(candidate=invalid):
                case = fixture()
                case["alternatives"] = [8, invalid]
                self.assertEqual(labels(case)["c6"], UNRESOLVED)

    def test_ambiguity_changes_decision_at_low_dispute_rate(self):
        case = fixture()
        case["alternatives"] = [4, 8]
        self.assertEqual(labels(case)["c6"], CONTRADICTED)

    def test_same_ambiguity_stays_stable_when_other_predicate_suffices(self):
        case = fixture(disputed=2, eligible=100)
        case["alternatives"] = [4, 8]
        result = labels(case)
        self.assertEqual(result["c6"], SUPPORTED)
        self.assertEqual(result["c7"], SUPPORTED)

    def test_intervention_with_same_value_still_contradicts_rule_only_attribution(self):
        case = fixture()
        outcome = case["record"]["final_output"]
        case["record"]["override"] = {"from": outcome, "to": outcome, "reason": "Human confirmation"}
        result = labels(case)
        self.assertEqual(result["c4"], SUPPORTED)
        self.assertEqual(result["c5"], CONTRADICTED)

    def test_incomplete_history_does_not_prove_no_override(self):
        case = fixture()
        case["record"]["action_history_complete"] = False
        self.assertEqual(labels(case)["c5"], UNRESOLVED)

    def test_known_intervention_contradicts_even_if_history_incomplete(self):
        case = fixture()
        case["record"]["action_history_complete"] = False
        outcome = case["record"]["final_output"]
        case["record"]["override"] = {"from": outcome, "to": outcome, "reason": "Human confirmation"}
        self.assertEqual(labels(case)["c5"], CONTRADICTED)

    def test_matching_rule_output_does_not_hide_final_action_mismatch(self):
        case = fixture()
        case["record"]["final_output"] = "manual_review"
        case["claims"][4]["asserted_value"] = "manual_review"
        result = labels(case)
        self.assertEqual(result["c4"], SUPPORTED)
        self.assertEqual(result["c5"], CONTRADICTED)


class MetamorphicIsolationTests(unittest.TestCase):
    def test_ids_subject_metadata_and_reference_cannot_change_predictions(self):
        baseline = fixture()
        altered = copy.deepcopy(baseline)
        altered["case_id"] = "test-extraction_error-999"
        altered["subject"] = "Clean supported supported supported"
        altered["metadata"] = {"split": "test", "variant": "clean", "scenario_id": "anything"}
        altered["reference"] = {"labels": {f"c{i}": CONTRADICTED for i in range(1, 8)}}
        altered["labels"] = {f"c{i}": UNRESOLVED for i in range(1, 8)}
        for method in ("execution_only", "provenance", "boundary"):
            with self.subTest(method=method):
                self.assertEqual(audit_case(baseline, method=method), audit_case(altered, method=method))

    def test_source_only_changes_leave_conditional_claims_unchanged(self):
        baseline = fixture()
        altered = copy.deepcopy(baseline)
        replace_source(altered, "contract", contract_text(2))
        replace_source(altered, "transactions", transaction_text(12, 100))
        before, after = labels(baseline), labels(altered)
        self.assertEqual(after["c2"], CONTRADICTED)
        self.assertEqual(after["c3"], CONTRADICTED)
        for claim in ("c4", "c5", "c6", "c7"):
            self.assertEqual(before[claim], after[claim])

    def test_capability_ablations_do_not_infer_from_disabled_sources(self):
        case = fixture()
        execution = labels(case, "execution_only")
        provenance = labels(case, "provenance")
        boundary = labels(case, "boundary")
        self.assertEqual([execution[f"c{i}"] for i in (1, 2, 3)], [UNRESOLVED] * 3)
        self.assertEqual(provenance["c1"], SUPPORTED)
        self.assertEqual([provenance[f"c{i}"] for i in (2, 3)], [UNRESOLVED] * 2)
        for claim in ("c4", "c5", "c6", "c7"):
            self.assertEqual(execution[claim], boundary[claim])
            self.assertEqual(provenance[claim], boundary[claim])

    def test_input_episode_is_not_mutated(self):
        case = fixture()
        before = copy.deepcopy(case)
        audit_case(case)
        self.assertEqual(case, before)


if __name__ == "__main__":
    unittest.main()
