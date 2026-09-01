"""Console entry point for ``osp`` and ``open-scholar-peer``."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .runtime import OSPError, OSPRun, RunOptions, discover_run, doctor


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog="osp", description="OpenCode-native Open ScholarPeer review CLI")
    commands = root.add_subparsers(dest="command", required=True)
    review = commands.add_parser("review", help="prepare and run an isolated OSP review")
    review.add_argument("paper", type=Path, help="PDF, TeX directory, source archive, or OSP workspace")
    review.add_argument("--output", type=Path, default=Path("osp-review"), help="parent directory for timestamped runs")
    review.add_argument("--mode", choices=("autonomous",), default="autonomous")
    review.add_argument("--headless", action="store_true", help="auto-approve OpenCode permissions in the isolated workspace")
    review.add_argument("--model")
    review.add_argument("--provider")
    review.add_argument("--variant")
    review.add_argument("--timeout", type=int, default=1800)
    review.add_argument("--venue")
    review.add_argument("--domain")
    review.add_argument("--brief", type=Path)
    review.add_argument("--previous-review", type=Path)
    review.add_argument("--revision-context", type=Path)
    review.add_argument("--network-policy", choices=("online", "offline"), default="online")
    review.add_argument("--prepare-only", action="store_true", help="import and validate input without invoking OpenCode")
    review.add_argument("--no-mcp", action="store_true", help="do not create the OSP MCP runtime")
    review.add_argument("--trail", type=Path, help="copy final provenance to an immutable local trail")
    review.add_argument("--trail-repo", help="Hugging Face dataset repository for --upload")
    review.add_argument("--upload", action="store_true", help="upload the explicitly requested trail")
    status = commands.add_parser("status", help="show run state")
    status.add_argument("run", type=Path)
    status.add_argument("--json", action="store_true")
    validate = commands.add_parser("validate", help="validate a prepared or completed run")
    validate.add_argument("run", type=Path)
    validate.add_argument("--json", action="store_true")
    resume = commands.add_parser("resume", help="resume a failed or interrupted run without changing scope")
    resume.add_argument("run", type=Path)
    checkpoint = commands.add_parser("checkpoint", help="write a checked run checkpoint")
    checkpoint.add_argument("run", type=Path)
    commands.add_parser("doctor", help="check required local tools")
    return root


def options(args: argparse.Namespace) -> RunOptions:
    return RunOptions(
        output=args.output,
        mode=args.mode,
        headless=args.headless,
        model=args.model,
        provider=args.provider,
        variant=args.variant,
        timeout=args.timeout,
        venue=args.venue,
        domain=args.domain,
        brief=args.brief,
        previous_review=args.previous_review,
        revision_context=args.revision_context,
        network_policy=args.network_policy,
        prepare_mcp=not args.no_mcp,
        trail=args.trail,
        trail_repo=args.trail_repo,
        upload=args.upload,
    )


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        if args.command == "review":
            run = OSPRun.prepare(args.paper, options(args))
            print(f"Prepared isolated OSP run: {run.run_dir}")
            if args.prepare_only:
                checks = run.validate()
                print("\n".join(f"{'PASS' if check.passed else 'INFO'} {check.name}: {check.detail}" for check in checks))
                return 0
            run.run(options(args))
            print(f"Review complete: {run.state()['final_review']}")
            return 0
        if args.command == "status":
            state = discover_run(args.run).state()
            if args.json:
                print(json.dumps(state, indent=2, sort_keys=True))
            else:
                print(f"Run: {state['run_id']}\nStatus: {state['status']}")
                for phase, entry in state["phases"].items():
                    print(f"  {phase}: {entry['status']} (attempts={entry['attempts']})")
            return 0
        if args.command == "validate":
            checks = discover_run(args.run).validate()
            valid = all(check.passed for check in checks)
            if args.json:
                print(json.dumps({"valid": valid, "checks": [check.__dict__ for check in checks]}, indent=2))
            else:
                print("\n".join(f"{'PASS' if check.passed else 'FAIL'} {check.name}: {check.detail}" for check in checks))
            return 0 if valid else 2
        if args.command == "resume":
            run = discover_run(args.run)
            state = run.state()
            scope = dict(state["scope"]["options"])
            for field in ("brief", "previous_review", "revision_context", "trail"):
                if scope.get(field):
                    scope[field] = Path(scope[field])
            restored = RunOptions(output=run.run_dir.parent, **scope)
            run.run(restored)
            print(f"Review complete: {run.state()['final_review']}")
            return 0
        if args.command == "checkpoint":
            run = discover_run(args.run)
            run.verify_scope()
            print(run.checkpoint("manual"))
            return 0
        checks = doctor()
        for check in checks:
            print(f"{'PASS' if check.passed else 'FAIL'} {check.name}: {check.detail}")
        return 0 if all(check.passed for check in checks) else 2
    except OSPError as exc:
        print(f"osp: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
