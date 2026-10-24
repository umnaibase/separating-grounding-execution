#!/usr/bin/env python3
"""Generate the entirely fictional, deterministic conformance corpus.

Only Python's standard library is required. This module does not import the
checker. Reference labels are constructed from source-authoring facts and an
independently expressed policy calculation, not copied from checker predictions.
The source-authoring facts are not written into the observable cases.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path


VERSION = "1.0.0"
RELEASE_VERSION = "1.1.0"
FIXED_SEED = "explainability-boundaries-fixtures-v1"
WINDOW = "2026-01-01/2026-01-31"
POLICY = {
    "id": "toy-v1",
    "dispute_threshold": {"numerator": 1, "denominator": 50},
    "commitment_threshold_months": 6,
}
CLAIM_KINDS = (
    "contract_lineage",
    "commitment_grounding",
    "dispute_grounding",
    "conditional_execution",
    "final_action_by_rule",
    "candidate_stability",
    "sufficient_dispute_reason",
)
VARIANTS = ("clean", "extraction_error", "source_gap", "ambiguity", "intervention")
GAPS = (
    "missing_contract",
    "missing_transactions",
    "conflicting_contracts",
    "invalid_contract_hash",
    "wrong_contract_version",
    "unsupported_worded_contract",
)
INTERVENTIONS = (
    "changed_output",
    "same_valued_intervention",
    "incomplete_history",
    "trace_fault",
)


def digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def opaque(namespace: str, key: str) -> str:
    return namespace + "_" + digest(FIXED_SEED + ":" + namespace + ":" + key)[:16]


def contract_text(months: int, framework: int, template: int) -> str:
    """Three expressly bounded numeric templates; semantic facts stay separate."""
    if template == 0:
        return (
            f"Minimum penalty-free cancellation time: {months} months.\n"
            f"Service framework duration: {framework} months."
        )
    if template == 1:
        return (
            f"The service framework lasts {framework} months. "
            f"The merchant may terminate after {months} months without penalty."
        )
    return (
        f"Penalty-free termination is available once {months} months have elapsed. "
        f"Framework duration: {framework} months."
    )


def words(number: int) -> str:
    # This finite vocabulary is deliberately outside the bounded checker's
    # documented numeric grammar but unambiguous to a reader.
    return {3: "three", 5: "five", 6: "six", 9: "nine", 12: "twelve", 18: "eighteen"}[number]


def source(source_id: str, kind: str, text: str, version: str = "1") -> dict:
    return {"source_id": source_id, "kind": kind, "version": version, "text": text}


def cite(item: dict) -> dict:
    return {
        "source_id": item["source_id"],
        "version": item["version"],
        "sha256": digest(item["text"]),
    }


def make_execution(inputs: dict) -> dict:
    """The simulated producer's deterministic policy, using integer arithmetic."""
    dispute_trigger = 50 * inputs["disputed"] >= inputs["eligible"]
    commitment_trigger = inputs["commitment_months"] < 6
    decision = "manual_review" if dispute_trigger or commitment_trigger else "standard_processing"
    return {
        "input": copy.deepcopy(inputs),
        "policy": copy.deepcopy(POLICY),
        "trace": {
            "dispute_trigger": dispute_trigger,
            "commitment_trigger": commitment_trigger,
        },
        "rule_output": decision,
        "final_output": decision,
        "override": None,
        "action_history_complete": True,
    }


def make_claims(record: dict) -> list[dict]:
    inputs = record["input"]
    claims = [
        (
            "Every cited contract matches the retained source bytes and version.",
            True,
        ),
        (
            "The valid cited contract evidence unambiguously supports the recorded "
            "minimum penalty-free commitment in months.",
            inputs["commitment_months"],
        ),
        (
            "The valid cited transaction evidence unambiguously supports the recorded "
            "disputed-to-eligible transaction fraction in the fixture observation window.",
            {"numerator": inputs["disputed"], "denominator": inputs["eligible"]},
        ),
        (
            "The recorded recommendation and both trace predicates match toy-v1 "
            "executed on the recorded inputs.",
            record["rule_output"],
        ),
        (
            "The complete retained action history establishes that toy-v1 produced "
            "the final action without an intervention.",
            record["final_output"],
        ),
        (
            "Every declared candidate commitment yields the same policy recommendation, "
            "holding the remaining recorded inputs fixed.",
            True,
        ),
        (
            "The dispute predicate alone is sufficient for manual review conditional "
            "on the recorded inputs and toy-v1, without claiming source truth or final human action.",
            True,
        ),
    ]
    return [
        {"claim_id": f"c{i + 1}", "kind": kind, "text": text, "asserted_value": value}
        for i, (kind, (text, value)) in enumerate(zip(CLAIM_KINDS, claims))
    ]


def annotate(case: dict, authored: dict) -> dict:
    """Construction reference: authored semantics plus independent arithmetic.

    `authored` describes what usable, cited fixture evidence establishes. It does
    not include a privileged answer where that evidence is missing/conflicting.
    In particular, a hidden intended merchant value never resolves a missing
    source. No source parser or audit-checker implementation is imported here.
    """
    record = case["record"]
    inputs = record["input"]
    labels, rationale = {}, {}
    labels["c1"] = authored["contract_lineage"]
    rationale["c1"] = authored["lineage_rationale"]

    values = authored["usable_commitments"]
    if values is None or len(set(values)) != 1:
        labels["c2"] = "unresolved"
        rationale["c2"] = authored["commitment_rationale"]
    else:
        actual = values[0]
        labels["c2"] = "supported" if actual == inputs["commitment_months"] else "contradicted"
        rationale["c2"] = (
            f"Usable cited fixture text establishes {actual} months for penalty-free exit; "
            f"the consumed value is {inputs['commitment_months']} months. "
            + authored["commitment_rationale"]
        )

    counts = authored["usable_counts"]
    if counts is None:
        labels["c3"] = "unresolved"
        rationale["c3"] = "The retained cited transaction evidence is unavailable or unusable."
    else:
        disputed, eligible = counts
        equal_fraction = disputed * inputs["eligible"] == inputs["disputed"] * eligible
        labels["c3"] = "supported" if equal_fraction else "contradicted"
        rationale["c3"] = (
            f"Usable cited evidence gives {disputed}/{eligible}; the consumed fraction is "
            f"{inputs['disputed']}/{inputs['eligible']}. Fraction equality is tested by cross multiplication."
        )

    # Reference arithmetic deliberately uses the complementary pass condition;
    # it does not call make_execution or reuse the checker's inference function.
    below_dispute_threshold = inputs["disputed"] * 50 < inputs["eligible"]
    meets_commitment_threshold = inputs["commitment_months"] >= 6
    expected = (
        "standard_processing"
        if below_dispute_threshold and meets_commitment_threshold
        else "manual_review"
    )
    correct_trace = (
        record["trace"]["dispute_trigger"] == (not below_dispute_threshold)
        and record["trace"]["commitment_trigger"] == (not meets_commitment_threshold)
    )
    consistent = record["rule_output"] == expected and correct_trace
    labels["c4"] = "supported" if consistent else "contradicted"
    rationale["c4"] = (
        f"Independent calculation yields {expected}; both recorded predicates "
        + ("match" if correct_trace else "do not match")
        + ". This judgment is conditional on consumed inputs, not source accuracy."
    )

    if record["override"] is not None:
        labels["c5"] = "contradicted"
        rationale["c5"] = "The retained history explicitly records an intervention, including any same-valued intervention."
    elif record["final_output"] != expected:
        labels["c5"] = "contradicted"
        rationale["c5"] = "The final action differs from the independently computed policy output."
    elif not record["action_history_complete"]:
        labels["c5"] = "unresolved"
        rationale["c5"] = "History completeness is not stipulated; no logged override does not establish absence of intervention."
    elif not consistent:
        labels["c5"] = "unresolved"
        rationale["c5"] = "An inconsistent execution trace prevents attribution despite an equal final outcome."
    else:
        labels["c5"] = "supported"
        rationale["c5"] = "The stipulated complete history contains no override and the final action matches consistent policy execution."

    candidates = case["alternatives"]
    if not candidates:
        labels["c6"] = "unresolved"
        rationale["c6"] = "No candidate analysis was retained."
    else:
        outcomes = {
            "standard_processing" if below_dispute_threshold and n >= 6 else "manual_review"
            for n in candidates
        }
        labels["c6"] = "supported" if len(outcomes) == 1 else "contradicted"
        rationale["c6"] = (
            f"The declared candidates {candidates} yield {sorted(outcomes)} with remaining inputs fixed. "
            "No exhaustiveness or real-world causal claim is made."
        )

    labels["c7"] = "contradicted" if below_dispute_threshold else "supported"
    rationale["c7"] = (
        f"For consumed counts {inputs['disputed']}/{inputs['eligible']}, "
        + ("the dispute predicate is false" if below_dispute_threshold else "the dispute predicate alone triggers manual review")
        + "; this is independent of the final human action and source truth."
    )
    return {"case_id": case["case_id"], "labels": labels, "rationale": rationale}


def build_case(family: int, variant: str) -> tuple[dict, dict, dict]:
    index = family - 1
    eligible = (800, 1000, 1200, 1500, 2000)[index % 5]
    disputed = eligible // 50 + (-1, 0, 1, -5, 5)[index % 5]
    commitment = (3, 5, 6, 9, 12, 18)[index % 6]
    framework = 24 + 12 * (index % 3)
    # Templates are distributed across both splits, not advertised as a
    # held-out natural-language generalisation experiment.
    template = index % 3
    base_key = str(family)
    contract = source(opaque("src", base_key + ":contract"), "contract", contract_text(commitment, framework, template))
    transactions = source(
        opaque("src", base_key + ":transactions"),
        "transactions",
        f"Observation window: {WINDOW}\nEligible transactions: {eligible}\nDisputed transactions: {disputed}",
    )
    case = {
        "case_id": opaque("case", base_key + ":" + variant),
        "subject": f"Fictional merchant {family:03d}",
        "sources": [contract, transactions],
        "citations": {"contract": [cite(contract)], "transactions": [cite(transactions)]},
        "record": make_execution({"disputed": disputed, "eligible": eligible, "commitment_months": commitment}),
        "alternatives": [commitment],
    }
    authored = {
        "contract_lineage": "supported",
        "lineage_rationale": "All cited contract bytes and versions match their retained fixture artifacts.",
        "usable_commitments": [commitment],
        "commitment_rationale": "The framework duration and penalty-free exit time are distinct quantities.",
        "usable_counts": (disputed, eligible),
    }
    subtype = "faithful_record"

    if variant == "extraction_error":
        inputs = copy.deepcopy(case["record"]["input"])
        if index % 2 == 0:
            inputs["commitment_months"] = framework
            subtype = "framework_duration_as_commitment"
        else:
            inputs["disputed"] = disputed + 1
            subtype = "disputed_count_increment"
        case["record"] = make_execution(inputs)
        case["alternatives"] = [inputs["commitment_months"]]
    elif variant == "source_gap":
        subtype = GAPS[index % len(GAPS)]
        if subtype == "missing_contract":
            case["sources"] = [transactions]
            authored["contract_lineage"] = "unresolved"
            authored["lineage_rationale"] = "A contract is cited but its retained source artifact is absent."
            authored["usable_commitments"] = None
            authored["commitment_rationale"] = "No retained cited contract establishes the commitment."
            case["alternatives"] = []
        elif subtype == "missing_transactions":
            case["sources"] = [contract]
            authored["usable_counts"] = None
        elif subtype == "conflicting_contracts":
            alternate = 3 if commitment >= 6 else 9
            other = source(opaque("src", base_key + ":contract-conflict"), "contract", contract_text(alternate, framework, (template + 1) % 3))
            case["sources"].append(other)
            case["citations"]["contract"].append(cite(other))
            authored["usable_commitments"] = [commitment, alternate]
            authored["commitment_rationale"] = "Two valid cited contracts give different exit times and no precedence rule resolves them."
            case["alternatives"] = [commitment, alternate]
        elif subtype == "invalid_contract_hash":
            case["citations"]["contract"][0]["sha256"] = "0" * 64
            authored["contract_lineage"] = "contradicted"
            authored["lineage_rationale"] = "The cited digest deliberately differs from the retained contract bytes."
            authored["usable_commitments"] = None
            authored["commitment_rationale"] = "A digest mismatch makes the cited contract unusable for source grounding."
        elif subtype == "wrong_contract_version":
            case["citations"]["contract"][0]["version"] = "2"
            authored["contract_lineage"] = "contradicted"
            authored["lineage_rationale"] = "The citation asserts version 2 but only version 1 is retained."
            authored["usable_commitments"] = None
            authored["commitment_rationale"] = "The mismatched citation version makes the contract unusable for source grounding."
        elif subtype == "unsupported_worded_contract":
            contract["text"] = (
                f"The minimum penalty-free cancellation time is {words(commitment)} months. "
                f"The service framework lasts {framework} months."
            )
            case["citations"]["contract"] = [cite(contract)]
            authored["commitment_rationale"] = (
                "The source states the number in words. Its semantics are unambiguous to the construction reference, "
                "while the released bounded numeric parser intentionally abstains."
            )
    elif variant == "ambiguity":
        contract["text"] = contract_text(3, framework, template)
        other = source(opaque("src", base_key + ":contract-ambiguous"), "contract", contract_text(9, framework, (template + 1) % 3))
        case["sources"].append(other)
        case["citations"]["contract"] = [cite(contract), cite(other)]
        inputs = copy.deepcopy(case["record"]["input"])
        inputs["commitment_months"] = 3
        case["record"] = make_execution(inputs)
        case["alternatives"] = [3, 9]
        authored["usable_commitments"] = [3, 9]
        authored["commitment_rationale"] = "Equally authoritative fixture contracts specify 3 and 9 months; no source precedence is stipulated."
        subtype = "conflicting_commitments_stable" if disputed * 50 >= eligible else "conflicting_commitments_sensitive"
    elif variant == "intervention":
        subtype = INTERVENTIONS[index % len(INTERVENTIONS)]
        record = case["record"]
        initial = record["rule_output"]
        if subtype == "changed_output":
            final = "manual_review" if initial == "standard_processing" else "standard_processing"
            record["final_output"] = final
            record["override"] = {"from": initial, "to": final, "reason": "Fictional reviewer changes the recommended action."}
        elif subtype == "same_valued_intervention":
            record["override"] = {"from": initial, "to": initial, "reason": "Fictional reviewer actively confirms the same action."}
        elif subtype == "incomplete_history":
            record["action_history_complete"] = False
        else:
            record["trace"]["commitment_trigger"] = not record["trace"]["commitment_trigger"]

    case["claims"] = make_claims(case["record"])
    reference = annotate(case, authored)
    metadata = {
        "case_id": case["case_id"],
        "scenario_id": opaque("scenario", base_key),
        "split": "dev" if family <= 8 else "test",
        "variant": variant,
        "subtype": subtype,
    }
    return case, reference, metadata


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text(
        "".join(json.dumps(row, sort_keys=True, ensure_ascii=False, separators=(",", ":")) + "\n" for row in rows),
        encoding="utf-8",
        newline="\n",
    )


def generate_diagnostics(output: Path) -> dict:
    """Author-written v1.1 diagnostic pairs, separate from the original corpus.

    The expected outcomes and labels below are an explicit construction table,
    not results copied from the checker or from make_execution. Each pair changes
    only the Boolean candidate-stability assertion and its statement.
    """
    constructions = (
        ((6, 9), "supported", "contradicted", "Both candidates yield standard_processing."),
        ((3, 5), "supported", "contradicted", "Both candidates yield manual_review through the commitment predicate."),
        ((3, 6, 9), "contradicted", "supported", "Three months yields manual_review; six and nine months yield standard_processing."),
        ((6, 9, 12), "supported", "contradicted", "All three candidates yield standard_processing."),
    )
    cases, references, memberships = [], [], []
    for family, (candidates, positive_label, negative_label, outcome_rationale) in enumerate(constructions, 1):
        contracts = [
            source(opaque("diag-src", f"{family}:contract:{number}"), "contract", contract_text(number, 24, (family - 1) % 3))
            for number in candidates
        ]
        transactions = source(
            opaque("diag-src", f"{family}:transactions"), "transactions",
            f"Observation window: {WINDOW}\nEligible transactions: 1500\nDisputed transactions: 25",
        )
        for assertion, expected in ((True, positive_label), (False, negative_label)):
            variant = "positive_assertion" if assertion else "negative_assertion"
            record = make_execution({"disputed": 25, "eligible": 1500, "commitment_months": candidates[0]})
            case = {
                "case_id": opaque("diag-case", f"{family}:{variant}"),
                "subject": f"Fictional diagnostic merchant {family:03d}",
                "sources": copy.deepcopy(contracts + [transactions]),
                "citations": {"contract": [cite(item) for item in contracts], "transactions": [cite(transactions)]},
                "record": record,
                "alternatives": list(candidates),
                "claims": make_claims(record),
            }
            case["claims"][5]["asserted_value"] = assertion
            if not assertion:
                case["claims"][5]["text"] = (
                    "The declared candidate commitments do not all yield the same policy recommendation, "
                    "holding the remaining recorded inputs fixed."
                )
            cases.append(case)
            references.append({
                "case_id": case["case_id"],
                "labels": {"c1": "supported", "c2": "unresolved", "c3": "supported", "c4": "supported", "c5": "supported", "c6": expected, "c7": "contradicted"},
                "rationale": {
                    "c1": "All cited contract bytes and versions match the retained fixtures.",
                    "c2": "Valid equally authoritative contracts specify distinct penalty-free exit times with no precedence; the consumed commitment is therefore not unambiguously grounded.",
                    "c3": "The retained transaction source explicitly states 25 disputed of 1500 eligible transactions, exactly matching the consumed fraction.",
                    "c4": "The retained rule output and both predicates faithfully execute toy-v1 on the consumed first candidate and 25/1500 dispute fraction.",
                    "c5": "The stipulated complete history contains no override and the final output matches faithful conditional policy execution.",
                    "c6": outcome_rationale + (" The claim asserts stability." if assertion else " The claim asserts the negation of stability."),
                    "c7": "25/1500 is strictly below 1/50 because 25 times 50 equals 1250, less than 1500. The dispute predicate alone is not sufficient for manual review.",
                },
            })
            memberships.append({
                "case_id": case["case_id"], "scenario_id": opaque("diag-scenario", str(family)),
                "split": "diagnostic", "variant": variant,
                "subtype": "straddling_commitments" if candidates == (3, 6, 9) else "homogeneous_commitments",
                "candidate_commitments": list(candidates),
            })
    metadata = {
        "dataset_name": "Candidate stability diagnostic extension",
        "version": RELEASE_VERSION,
        "main_corpus_version": VERSION,
        "provenance": "Author-written synthetic conformance extension with explicit construction-reference labels; no external or independent annotations.",
        "purpose": "Exercise homogeneous and straddling candidate sets below the dispute threshold, including positive and negative stability assertions.",
        "statistical_unit": "paired diagnostic family; neither episodes nor claims are independent samples",
        "cases_count": 8, "claims_count": 56, "scenario_families": 4,
        "candidate_sets": [list(item[0]) for item in constructions],
        "fixed_inputs": {"disputed": 25, "eligible": 1500},
        "label_counts": dict(sorted(Counter(label for ref in references for label in ref["labels"].values()).items())),
        "cases": memberships,
    }
    output.mkdir(parents=True, exist_ok=True)
    write_jsonl(output / "cases.jsonl", cases)
    write_jsonl(output / "reference.jsonl", references)
    write_json(output / "metadata.json", metadata)
    files = {
        name: {"sha256": hashlib.sha256((output / name).read_bytes()).hexdigest(), "bytes": (output / name).stat().st_size}
        for name in ("cases.jsonl", "reference.jsonl", "metadata.json")
    }
    write_json(output / "manifest.json", {"version": RELEASE_VERSION, "algorithm": "sha256", "files": files})
    return {"cases": 8, "claims": 56, "label_counts": metadata["label_counts"], "files": files}


def generate(output: Path) -> dict:
    cases, references, memberships = [], [], []
    for family in range(1, 21):
        for variant in VARIANTS:
            case, reference, membership = build_case(family, variant)
            cases.append(case)
            references.append(reference)
            memberships.append(membership)
    counts = Counter(label for reference in references for label in reference["labels"].values())
    per_kind = defaultdict(Counter)
    for reference in references:
        for index, kind in enumerate(CLAIM_KINDS, 1):
            per_kind[kind][reference["labels"][f"c{index}"]] += 1
    metadata = {
        "dataset_name": "Explainability Boundaries: Fictional Merchant Audit Fixtures",
        "version": VERSION,
        "seed": FIXED_SEED,
        "observation_window": WINDOW,
        "provenance": "Entirely programmatically authored fictional sources, consumed features, and injected faults; no real entities, private data, or foundation-model outputs.",
        "reference_method": "Construction semantics plus independent policy arithmetic; no human-annotation study or checker-generated labels.",
        "statistical_unit": "scenario family",
        "scenario_families": 20,
        "cases_count": len(cases),
        "claims_count": 7 * len(cases),
        "split_scenario_counts": {"dev": 8, "test": 12},
        "split_case_counts": {"dev": 40, "test": 60},
        "label_counts": dict(sorted(counts.items())),
        "label_counts_by_kind": {kind: dict(sorted(per_kind[kind].items())) for kind in CLAIM_KINDS},
        "public_benchmark_limit": "Split labels and generation templates are public. No secret test set, independent sample of banking cases, or absence of test inspection is claimed.",
        "assumptions": [
            "Retained valid cited fixture sources are authoritative within the fictional episode; source authenticity and external truth are not evaluated.",
            "When action_history_complete is true it is a stipulated fixture property, not a proved completeness property of real logs.",
            "Contract commitment means minimum time until penalty-free exit, not the service-framework duration.",
            "Multiple valid conflicting contracts have equal authority; no document precedence is inferred.",
            "Reference source grounding may be supported on explicit spelled-out number text that the bounded numeric checker cannot parse.",
            "Candidate stability is conditional only on explicitly listed commitments; list completeness and causal action feasibility are not asserted.",
        ],
        "cases": memberships,
    }
    output.mkdir(parents=True, exist_ok=True)
    write_jsonl(output / "cases.jsonl", cases)
    write_jsonl(output / "reference.jsonl", references)
    write_json(output / "metadata.json", metadata)
    files = {}
    for name in ("cases.jsonl", "reference.jsonl", "metadata.json"):
        contents = (output / name).read_bytes()
        files[name] = {"sha256": hashlib.sha256(contents).hexdigest(), "bytes": len(contents)}
    diagnostics = generate_diagnostics(output / "diagnostics")
    for name in ("cases.jsonl", "reference.jsonl", "metadata.json", "manifest.json"):
        contents = (output / "diagnostics" / name).read_bytes()
        files["diagnostics/" + name] = {"sha256": hashlib.sha256(contents).hexdigest(), "bytes": len(contents)}
    manifest = {"version": RELEASE_VERSION, "main_corpus_version": VERSION, "algorithm": "sha256", "files": files}
    write_json(output / "manifest.json", manifest)
    return {"cases": len(cases), "claims": 7 * len(cases), "label_counts": dict(counts), "files": files, "diagnostics": diagnostics}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parents[1] / "data")
    args = parser.parse_args()
    print(json.dumps(generate(args.output), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
