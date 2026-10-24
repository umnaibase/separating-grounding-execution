"""Offline command-line interface. Run from the repository root."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from .audit import METHODS
from .evaluation import (read_jsonl, write_json, write_jsonl, predict, score,
                         validate, reproduce, reproduce_diagnostics, markdown_report)


def main() -> int:
    parser = argparse.ArgumentParser(description="Synthetic explanation-boundary audit suite (offline)")
    subs = parser.add_subparsers(dest="command", required=True)
    p = subs.add_parser("reproduce", help="Validate, run all ablations, and reproduce reports")
    p.add_argument("--data-dir", type=Path, default=Path("data"))
    p.add_argument("--output", type=Path, default=Path("results"))
    p = subs.add_parser("diagnostics", help="Reproduce the separate eight-episode candidate-stability diagnostic report")
    p.add_argument("--data-dir", type=Path, default=Path("data/diagnostics"))
    p.add_argument("--output", type=Path, default=Path("results/diagnostics"))
    p = subs.add_parser("validate", help="Check release integrity, annotation coverage and family splits")
    p.add_argument("--data-dir", type=Path, default=Path("data"))
    p = subs.add_parser("audit", help="Make predictions without reading reference labels")
    p.add_argument("--cases", type=Path, default=Path("data/cases.jsonl"))
    p.add_argument("--method", choices=METHODS, default="boundary")
    p.add_argument("--output", type=Path, required=True)
    p = subs.add_parser("score", help="Score previously generated predictions")
    p.add_argument("--predictions", type=Path, required=True)
    p.add_argument("--reference", type=Path, default=Path("data/reference.jsonl"))
    p.add_argument("--metadata", type=Path, default=Path("data/metadata.json"))
    p.add_argument("--cases", type=Path, default=Path("data/cases.jsonl"))
    p.add_argument("--split", choices=("all", "dev", "test"), default="all")
    p.add_argument("--output", type=Path, required=True)
    p = subs.add_parser("export-prompts", help="Export audit prompts without labels; invokes no model")
    p.add_argument("--data-dir", type=Path, default=Path("data"))
    p.add_argument("--split", choices=("all", "dev", "test"), default="test")
    p.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.command == "reproduce":
            report = reproduce(args.data_dir, args.output)
            print(json.dumps(report["data_validation"], sort_keys=True))
            print(f"Reproduced {len(report['methods'])} capability ablations in {args.output}")
            if (args.data_dir / "diagnostics").is_dir():
                print(f"Reproduced the separate eight-episode diagnostics in {args.output / 'diagnostics'}")
            archived = args.data_dir.parent / "results" / "pilot"
            if (args.data_dir / "pilot" / "manifest.json").is_file() and (archived / "model_run.json").is_file():
                from .pilot import score_pilot
                score_pilot(args.data_dir / "pilot", args.data_dir,
                            archived / "raw" / "text", args.output / "pilot",
                            archived / "model_run.json", archived / "raw" / "image",
                            archived / "raw" / "paired_text")
                print(f"Rescored archived assistant outputs in {args.output / 'pilot'}; no live model was invoked")
                if (args.data_dir.parent / "results" / "external" / "grok-4.7" / "reported_results.json").is_file():
                    from .comparison import generate_comparison
                    generate_comparison(args.data_dir.parent, args.output / "models")
                    print(f"Reproduced the evidence-qualified comparison in {args.output / 'models'}")
        elif args.command == "diagnostics":
            report = reproduce_diagnostics(args.data_dir, args.output)
            print(json.dumps(report["data_validation"], sort_keys=True))
            print(f"Reproduced diagnostics separately in {args.output}")
        elif args.command == "validate":
            print(json.dumps(validate(args.data_dir), sort_keys=True))
        elif args.command == "audit":
            cases = read_jsonl(args.cases)
            write_jsonl(args.output, predict(cases, args.method))
            print(f"Wrote predictions for {len(cases)} episodes")
        elif args.command == "score":
            report = score(read_jsonl(args.predictions), read_jsonl(args.reference),
                           json.loads(args.metadata.read_text(encoding="utf-8")),
                           read_jsonl(args.cases), args.split)
            write_json(args.output / "summary.json", report)
            (args.output / "summary.md").write_text(markdown_report(report), encoding="utf-8", newline="\n")
            print(f"Scored {len(report['methods'])} methods in {args.output}")
        elif args.command == "export-prompts":
            from .external import export_prompts
            export_prompts(args.data_dir, args.split, args.output)
    except (ValueError, KeyError, TypeError, OSError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
