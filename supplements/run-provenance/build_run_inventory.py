#!/usr/bin/env python3
"""Reproduce a provenance inventory from the unchanged released archive."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path


def build_inventory(root: Path) -> dict:
    source_files = {}

    def read(relative: str):
        data = (root / relative).read_bytes()
        source_files[relative] = {
            "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
        }
        return json.loads(data)

    join_rows = read("data/pilot/join_map.json")["records"]
    join = {row["episode_id"]: row for row in join_rows}
    metadata = {
        row["case_id"]: row for row in read("data/metadata.json")["cases"]
    }
    primary_episodes = set()
    affected_episodes = set()
    affected_families = set()
    reporting_sibling_groups = []
    diagnostic_sibling_groups = []
    batches = []
    for index in range(1, 5):
        relative = f"data/pilot/batches/text_batch_{index:02d}.json"
        batch = read(relative)
        episode_ids = [episode["episode_id"] for episode in batch["episodes"]]
        assert len(episode_ids) == 17 and len(set(episode_ids)) == 17
        assert not primary_episodes.intersection(episode_ids)
        primary_episodes.update(episode_ids)
        counts = Counter(join[episode_id]["collection"] for episode_id in episode_ids)
        family_groups = defaultdict(list)
        for episode_id in episode_ids:
            item = join[episode_id]
            family_groups[(item["collection"], item["scenario_id"])].append(item)
        siblings = []
        for (collection, family), rows in sorted(family_groups.items()):
            if len(rows) < 2:
                continue
            group = {
                "batch_id": batch["batch_id"],
                "collection": collection,
                "family_id": family,
                "episode_ids": [row["episode_id"] for row in rows],
                "original_case_ids": [row["original_case_id"] for row in rows],
                "variants": [
                    metadata[row["original_case_id"]]["variant"]
                    if row["original_case_id"] in metadata else None
                    for row in rows
                ],
                "size": len(rows),
            }
            siblings.append(group)
            if collection == "main_reporting":
                reporting_sibling_groups.append(group)
                affected_episodes.update(group["episode_ids"])
                affected_families.add(family)
            else:
                diagnostic_sibling_groups.append(group)
        batches.append({
            "batch_id": batch["batch_id"],
            "input_path": relative,
            "episode_count": len(episode_ids),
            "reporting_episodes": counts["main_reporting"],
            "diagnostic_episodes": counts["diagnostic"],
            "mixed_reporting_and_diagnostics": bool(
                counts["main_reporting"] and counts["diagnostic"]
            ),
            "sibling_groups": siblings,
        })
    assert len(primary_episodes) == 68

    gpt = read("results/pilot/model_run.json")
    worker_instructions = read("results/pilot/worker_instructions.json")
    claude = read(
        "results/external/claude-fable-5.1/bundle/fm_eval/results/"
        "system_report_claude-fable-5-1.json"
    )
    grok = read("results/external/grok-4.7/systems.json")["systems"][0]
    claude_system = claude["system"]
    models = [
        {
            "display_name": "GPT-6.1 Sol Ultra",
            "display_name_provenance": gpt["model_identity_provenance"],
            "run_id": gpt["run_id"],
            "configured_harness_model_id": None,
            "harness_family_as_declared": gpt["model_family_as_declared_by_session"],
            "provider_api_model_string": None,
            "attested_serving_snapshot": gpt["exact_model_snapshot"],
            "snapshot_date": None,
            "access_route": "Session assistant with fresh inference-worker contexts",
            "access_route_evidence": "Archived worker instructions and run record",
            "temperature": None,
            "sampling_parameters": gpt["sampling_parameters"],
            "provider_endpoint": gpt["provider_endpoint"],
            "configuration": gpt["model_configuration"],
            "author_association_as_recorded": gpt["author_model_relationship"],
            "attempts_per_batch_as_recorded": gpt["attempts_per_batch"],
            "response_retries_as_recorded": gpt["response_retries"],
            "attempt_unit": "One response per scheduled multi-episode context",
            "primary_audit_contexts": 4,
            "primary_audit_episodes": 68,
            "paired_text_audit_contexts": 2,
            "paired_image_audit_contexts": 2,
            "paired_episodes_per_context": 6,
            "primary_episode_isolation": False,
            "fresh_context_as_declared": all(
                worker["fork_turns"] == "none"
                for worker in worker_instructions["workers"]
            ),
            "context_isolation": {
                "fork_turns_values_as_recorded": sorted({
                    worker["fork_turns"]
                    for worker in worker_instructions["workers"]
                }),
                "parent_configuration_as_recorded": gpt["model_configuration"],
                "persistent_memory_isolation_independently_attested": None,
                "project_context_isolation_independently_attested": None,
                "instruction_state_isolation_independently_attested": None,
                "interpretation": "Declared fresh contexts and lookup restrictions do not independently verify isolation of persistent memory, project context or instruction state. Shared artifact-construction and auditing provenance adds dependence beyond generator/checker conformance.",
            },
            "tools": "Frontend supplies retained-artifact presence, kind, version and digest comparisons; workers read inputs and write responses",
            "semantic_labels_precomputed": False,
            "frontend_scope_note": "Integrity computation is supplied. Source interpretation, policy reasoning and application of the grounding prerequisite remain model tasks; a prerequisite bypass is possible in the output.",
            "tool_activity_evidence": gpt["tool_activity_evidence"],
            "full_platform_tool_traces_archived": False,
        },
        {
            "display_name": "Claude Fable 5.1",
            "configured_harness_model_id": claude_system["model_id_configured"],
            "configured_agent_parameter": "fable",
            "model_identifier_note": claude_system["model_id_note"],
            "run_id": None,
            "record_schema": claude["schema_version"],
            "run_date_as_reported": claude["run"]["date"],
            "provider_api_model_string": None,
            "attested_serving_snapshot": None,
            "snapshot_date": None,
            "access_route_as_reported": claude_system["access_route"],
            "temperature": None,
            "sampling_as_reported": claude_system["sampling"],
            "attempts_per_call_as_reported": claude_system["attempts_per_call"],
            "retry_policy_as_reported": claude_system["retry_policy"],
            "attempt_unit": "One episode or source document per fresh model instance, as reported",
            "total_calls_as_reported": claude["run"]["total_calls"],
            "audit_calls": 136,
            "extraction_calls": 50,
            "tools_available_as_reported": claude_system["tools_available_to_model"],
            "tool_restriction_enforcement_as_reported": claude_system["tool_restriction_enforcement"],
            "operator_exposure_as_reported": claude["run"]["operator_note"],
            "full_platform_tool_traces_archived": False,
            "per_call_prompts_and_literal_responses_archived": True,
        },
        {
            "display_name": "Grok 4.7",
            "configured_harness_model_id": None,
            "supplier_system_identifier": grok["system"],
            "identifier_kind": "Supplier's system string; not an attested API identifier",
            "run_id": grok["run_id"],
            "run_date_as_reported": grok["date"],
            "provider_api_model_string": None,
            "attested_serving_snapshot": None,
            "snapshot_date": None,
            "access_route_as_reported": grok["interface"],
            "temperature": None,
            "temperature_supplier_text": grok["temperature"],
            "temperature_note": "Supplier text does not establish a numeric temperature or serving configuration",
            "attempts_per_call": None,
            "retry_policy": None,
            "tools_as_reported": grok["tools"],
            "native_prompts_archived": False,
            "native_response_and_execution_traces_archived": False,
            "predictions_archived": True,
            "provenance_note": "Structured predictions can be rescored; the inference procedure cannot be examined from these records",
        },
    ]
    return {
        "schema_version": "mfmb2026-archived-run-inventory/1.0",
        "release": "explainability-boundaries 1.2.2",
        "purpose": "Supplemental provenance and context-composition analysis of existing archived records; no new model evaluation",
        "missing_field_convention": "null means unavailable in the cited record; configured identifiers are not serving attestations",
        "evidence_note": "Attempt counts, fresh contexts and restrictions are archived declarations, not independently attested platform behaviour",
        "models": models,
        "gpt_primary_context_composition": {
            "definition_of_affected": "A reporting episode shares its scheduled context with at least one reporting episode having the same scenario_id in the archival join map",
            "reporting_episodes": sum(batch["reporting_episodes"] for batch in batches),
            "diagnostic_episodes": sum(batch["diagnostic_episodes"] for batch in batches),
            "affected_reporting_episodes": len(affected_episodes),
            "affected_reporting_episode_ids": sorted(affected_episodes),
            "affected_reporting_families": len(affected_families),
            "affected_reporting_family_ids": sorted(affected_families),
            "reporting_sibling_groups": len(reporting_sibling_groups),
            "reporting_group_size_distribution": dict(sorted(
                Counter(group["size"] for group in reporting_sibling_groups).items()
            )),
            "diagnostic_sibling_groups": len(diagnostic_sibling_groups),
            "mixed_contexts": sum(batch["mixed_reporting_and_diagnostics"] for batch in batches),
            "batches": batches,
            "interpretation": "Co-occurrence permits within-context comparison; this inventory does not demonstrate that a model used it or estimate its effect",
        },
        "source_files": dict(sorted(source_files.items())),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    inventory = build_inventory(args.artifact_root)
    args.output.write_text(json.dumps(inventory, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
