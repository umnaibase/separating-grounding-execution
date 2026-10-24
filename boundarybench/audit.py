"""Evidence-only claim checks. This module never reads labels or metadata.

The bounded source parsers intentionally abstain outside their exact documented
grammar. A hash verifies consistency, not authenticity. Execution attribution is
conditional on the fixture's stipulated complete and trustworthy action history.
"""

from __future__ import annotations

import hashlib
import re
from typing import Any

LABELS = ("supported", "contradicted", "unresolved")
METHODS = ("execution_only", "provenance", "boundary")
KINDS = (
    "contract_lineage", "commitment_grounding", "dispute_grounding",
    "conditional_execution", "final_action_by_rule", "candidate_stability",
    "sufficient_dispute_reason",
)
POLICY = {
    "id": "toy-v1",
    "dispute_threshold": {"numerator": 1, "denominator": 50},
    "commitment_threshold_months": 6,
}
WINDOW = "2026-01-01/2026-01-31"


def _integer(value: Any, minimum: int = 0) -> bool:
    return type(value) is int and value >= minimum


def _policy_valid(policy: Any) -> bool:
    if not isinstance(policy, dict) or policy != POLICY:
        return False
    threshold = policy.get("dispute_threshold", {})
    return all(type(v) is int for v in (
        threshold.get("numerator"), threshold.get("denominator"),
        policy.get("commitment_threshold_months"),
    ))


def _fraction_valid(disputed: Any, eligible: Any) -> bool:
    return _integer(disputed) and _integer(eligible, 1) and disputed <= eligible


def decide(inputs: dict, policy: dict) -> str:
    """Evaluate the toy policy using exact integer arithmetic; invalid => error."""
    if not _policy_valid(policy):
        raise ValueError("Unsupported policy artifact")
    if not isinstance(inputs, dict):
        raise ValueError("Inputs must be an object")
    d, e, c = (inputs.get(k) for k in ("disputed", "eligible", "commitment_months"))
    if not _fraction_valid(d, e) or not _integer(c):
        raise ValueError("Invalid or missing policy input")
    return "manual_review" if d * 50 >= e or c < 6 else "standard_processing"


def parse_contract(text: str) -> int | None:
    """Full-match the three supported numeric templates; no fuzzy interpretation."""
    patterns = (
        r"Minimum penalty-free cancellation time: (?P<n>\d+) months\.\s*Service framework duration: (?P<f>\d+) months\.",
        r"The service framework lasts (?P<f>\d+) months\. The merchant may terminate after (?P<n>\d+) months without penalty\.",
        r"Penalty-free termination is available once (?P<n>\d+) months have elapsed\. Framework duration: (?P<f>\d+) months\.",
    )
    if not isinstance(text, str):
        return None
    for pattern in patterns:
        match = re.fullmatch(pattern, text.strip(), flags=re.ASCII)
        if match:
            n, f = int(match["n"]), int(match["f"])
            return n if f >= n else None
    return None


def parse_transactions(text: str) -> tuple[int, int] | None:
    pattern = (
        r"Observation window: " + re.escape(WINDOW)
        + r"\nEligible transactions: (?P<e>\d+)\nDisputed transactions: (?P<d>\d+)"
    )
    if not isinstance(text, str):
        return None
    match = re.fullmatch(pattern, text.strip(), flags=re.ASCII)
    if not match:
        return None
    d, e = int(match["d"]), int(match["e"])
    return (d, e) if _fraction_valid(d, e) else None


def _source_check(case: dict, kind: str) -> tuple[str, list[dict], str, list[str]]:
    """Resolve citations without consulting reference annotations."""
    citations = case.get("citations", {})
    refs = citations.get(kind) if isinstance(citations, dict) else None
    sources = case.get("sources")
    if not isinstance(refs, list) or not refs or not isinstance(sources, list):
        return "unresolved", [], "No usable citations or retained source list.", []
    retained, evidence, issues = [], [], []
    missing = False
    for ref in refs:
        if not isinstance(ref, dict) or not isinstance(ref.get("source_id"), str):
            missing = True
            continue
        source_id = ref["source_id"]
        evidence.append("source:" + source_id)
        found = [s for s in sources if isinstance(s, dict) and s.get("source_id") == source_id]
        if len(found) != 1:
            missing = True
            continue
        source = found[0]
        if source.get("kind") != kind:
            issues.append("Cited source kind does not match the requested source kind.")
            continue
        if not isinstance(source.get("text"), str) or not isinstance(ref.get("sha256"), str):
            missing = True
            continue
        if not isinstance(source.get("version"), str) or not isinstance(ref.get("version"), str):
            missing = True
            continue
        actual = hashlib.sha256(source["text"].encode("utf-8")).hexdigest()
        if actual != ref["sha256"] or source["version"] != ref["version"]:
            issues.append("Retained bytes or version differ from the citation.")
        else:
            retained.append(source)
    if issues:
        return "contradicted", [], " ".join(sorted(set(issues))), evidence
    if missing:
        return "unresolved", [], "A cited artifact is missing, ambiguous, or malformed.", evidence
    return "supported", retained, "Cited bytes and versions match; authenticity is not checked.", evidence


def _execution(record: dict) -> tuple[str, str, list[str]]:
    evidence = ["record.input", "record.policy", "record.trace", "record.rule_output"]
    try:
        expected = decide(record.get("input"), record.get("policy"))
    except (ValueError, TypeError):
        return "unresolved", "Required inputs or a supported policy are unavailable.", evidence
    inputs, trace = record["input"], record.get("trace")
    output = record.get("rule_output")
    if output not in ("manual_review", "standard_processing") or not isinstance(trace, dict):
        return "unresolved", "Required execution output or trace is unavailable.", evidence
    if any(type(trace.get(k)) is not bool for k in ("dispute_trigger", "commitment_trigger")):
        return "unresolved", "Trace predicates are missing or malformed.", evidence
    correct = (
        output == expected
        and trace["dispute_trigger"] == (inputs["disputed"] * 50 >= inputs["eligible"])
        and trace["commitment_trigger"] == (inputs["commitment_months"] < 6)
    )
    return (
        "supported" if correct else "contradicted",
        "Both trace predicates and the recorded output agree with exact replay." if correct
        else "A trace predicate or recorded output disagrees with exact replay.",
        evidence,
    )


def _check(case: dict, claim: dict, method: str) -> tuple[str, str, list[str]]:
    kind, assertion = claim.get("kind"), claim.get("asserted_value")
    record = case.get("record")
    record = record if isinstance(record, dict) else {}
    if kind == "contract_lineage":
        if method == "execution_only":
            return "unresolved", "Provenance checking is disabled in this ablation.", []
        if type(assertion) is not bool:
            return "unresolved", "Malformed lineage assertion.", []
        status, _, detail, refs = _source_check(case, "contract")
        if status != "unresolved" and assertion is False:
            status = "contradicted" if status == "supported" else "supported"
        return status, detail, refs
    if kind in ("commitment_grounding", "dispute_grounding"):
        if method != "boundary":
            return "unresolved", "Semantic checking is disabled in this ablation.", []
        source_kind = "contract" if kind == "commitment_grounding" else "transactions"
        status, sources, detail, refs = _source_check(case, source_kind)
        if status != "supported":
            return "unresolved", "Grounding unavailable: " + detail, refs
        if kind == "commitment_grounding":
            if not _integer(assertion):
                return "unresolved", "Malformed commitment assertion.", refs
            values = [parse_contract(source["text"]) for source in sources]
            if any(v is None for v in values):
                return "unresolved", "A source is outside the supported numeric contract grammar.", refs
            if len(set(values)) != 1:
                return "unresolved", "Valid cited contracts conflict; no precedence is specified.", refs
            equal = values[0] == assertion
        else:
            if not isinstance(assertion, dict) or not _fraction_valid(
                assertion.get("numerator"), assertion.get("denominator")
            ):
                return "unresolved", "Malformed dispute-fraction assertion.", refs
            values = [parse_transactions(source["text"]) for source in sources]
            if any(v is None for v in values):
                return "unresolved", "A source is outside the supported transaction grammar/window.", refs
            d0, e0 = values[0]
            if any(d * e0 != d0 * e for d, e in values):
                return "unresolved", "Valid cited transaction fractions conflict.", refs
            equal = d0 * assertion["denominator"] == assertion["numerator"] * e0
        return (
            "supported" if equal else "contradicted",
            "Unique interpreted source evidence matches the claim." if equal
            else "Unique interpreted source evidence differs from the claim.", refs,
        )
    if kind == "conditional_execution":
        status, detail, refs = _execution(record)
        if assertion not in ("manual_review", "standard_processing"):
            return "unresolved", "Malformed rule-output assertion.", refs
        if status == "supported" and assertion != record.get("rule_output"):
            return "contradicted", "Claimed rule output differs from the retained execution.", refs
        return status, detail, refs
    if kind == "final_action_by_rule":
        refs = ["record.final_output", "record.override", "record.action_history_complete"]
        if assertion not in ("manual_review", "standard_processing"):
            return "unresolved", "Malformed final-action assertion.", refs
        final = record.get("final_output")
        if final not in ("manual_review", "standard_processing"):
            return "unresolved", "Final output is unavailable.", refs
        if assertion != final:
            return "contradicted", "The assertion names a different final action.", refs
        if record.get("override") is not None:
            return "contradicted", "A retained intervention contradicts policy-only attribution, even if values match.", refs
        try:
            expected = decide(record.get("input"), record.get("policy"))
        except (ValueError, TypeError):
            return "unresolved", "Policy replay is unavailable.", refs
        if final != expected:
            return "contradicted", "Final action differs from the recorded policy's deterministic output.", refs
        if record.get("action_history_complete") is not True or "override" not in record:
            return "unresolved", "Complete action history is not stipulated; equal outputs do not establish attribution.", refs
        status, _, execution_refs = _execution(record)
        if status != "supported":
            return "unresolved", "An unavailable or inconsistent execution record prevents attribution.", refs + execution_refs
        return "supported", "Policy-only attribution is supported conditional on the stipulated complete action history.", refs + execution_refs
    if kind == "candidate_stability":
        refs = ["alternatives", "record.input", "record.policy"]
        candidates = case.get("alternatives")
        if type(assertion) is not bool or not isinstance(candidates, list) or not candidates:
            return "unresolved", "No nonempty candidate set or valid assertion is available.", refs
        if any(not _integer(c) for c in candidates):
            return "unresolved", "A candidate commitment is invalid.", refs
        try:
            outcomes = {decide({**record["input"], "commitment_months": c}, record.get("policy")) for c in candidates}
        except (ValueError, TypeError, KeyError):
            return "unresolved", "Candidate replay cannot be completed.", refs
        stable = len(outcomes) == 1
        return (
            "supported" if stable == assertion else "contradicted",
            "Exact enumeration gives " + ", ".join(sorted(outcomes)) + "; candidate completeness is not asserted.", refs,
        )
    if kind == "sufficient_dispute_reason":
        refs = ["record.input.disputed", "record.input.eligible", "record.policy"]
        inputs = record.get("input")
        if not isinstance(inputs, dict) or not _policy_valid(record.get("policy")) or type(assertion) is not bool:
            return "unresolved", "Required policy or assertion is invalid.", refs
        d, e = inputs.get("disputed"), inputs.get("eligible")
        if not _fraction_valid(d, e):
            return "unresolved", "Dispute fraction is unavailable or invalid.", refs
        sufficient = d * 50 >= e
        return (
            "supported" if sufficient == assertion else "contradicted",
            "Exact threshold comparison " + ("meets" if sufficient else "does not meet")
            + " the dispute predicate; source truth and final action are outside this claim.", refs,
        )
    return "unresolved", "Unsupported claim kind.", []


def audit_case(case: dict, method: str = "boundary") -> list[dict]:
    """Audit observable evidence only. No file I/O or reference-key access."""
    if method not in METHODS:
        raise ValueError("Unknown audit method: " + str(method))
    # Do not expose IDs, split, variant, hidden construction facts, or labels.
    observable = {key: case.get(key) for key in ("sources", "citations", "record", "alternatives", "claims")}
    claims = observable.get("claims")
    if not isinstance(claims, list):
        raise ValueError("Claims must be a list")
    results = []
    for claim in claims:
        if not isinstance(claim, dict) or not isinstance(claim.get("claim_id"), str):
            raise ValueError("Each claim requires a claim_id")
        status, detail, evidence = _check(observable, claim, method)
        results.append({"claim_id": claim["claim_id"], "kind": claim.get("kind"),
                        "label": status, "check": detail, "evidence": evidence})
    return results
