import argparse
import json
import sys
from pathlib import Path

from .generator import PROFILES
from .pipeline import finalize, read_json, run
from .runtime.evaluate import emit, evaluate


def main():
    if len(sys.argv) > 1 and sys.argv[1] == 'swe':
        from .swe import main as swe_main
        raise SystemExit(swe_main(sys.argv[2:]))
    parser = argparse.ArgumentParser(description="EdgeBench routing prototypes and evidence-led SWE authoring")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser('swe', help='Classify, harvest, plan and inspect long-horizon SWE authoring (swe --help)')
    build = commands.add_parser("run", help="Generate a fresh batch and run bundled author baselines")
    build.add_argument("--output", type=Path, required=True)
    build.add_argument("--profiles", nargs="+", choices=list(PROFILES), default=list(PROFILES))
    build.add_argument("--replicas", type=int, default=2)
    build.add_argument("--public-cases", type=int, default=3)
    build.add_argument("--feedback-cases", type=int, default=6)
    build.add_argument("--final-cases", type=int, default=6)
    build.add_argument("--seed", help="Optional author-only deterministic demo seed; default is random 256-bit secret")
    build.add_argument("--base-image", default="python:3.12-slim-bookworm")
    build.add_argument("--trusted-host", action="store_true")
    grade = commands.add_parser("evaluate", help="Evaluate an author-owned solver on public or feedback cases")
    grade.add_argument("--instance", type=Path, required=True)
    grade.add_argument("--solver", type=Path, required=True)
    grade.add_argument("--split", choices=["public", "feedback"], default="feedback")
    grade.add_argument("--trusted-host", action="store_true")
    final = commands.add_parser("finalize", help="Evaluate a frozen selection once; refuses any repeated final test")
    final.add_argument("--instance", type=Path, required=True)
    final.add_argument("--trusted-host", action="store_true")
    args = parser.parse_args()
    if args.command == "run":
        result = run(args.output, args.profiles, args.replicas,
                     {"public": args.public_cases, "feedback": args.feedback_cases, "final": args.final_cases},
                     seed=args.seed, trusted_host=args.trusted_host, base_image=args.base_image)
        print(json.dumps({key: value for key, value in result.items() if key != "instances"}, indent=2))
    elif args.command == "evaluate":
        path = args.instance / ("public/cases.json" if args.split == "public" else "judge/feedback.json")
        emit(evaluate(read_json(path), args.solver, trusted_host=args.trusted_host))
    else:
        emit(finalize(args.instance, args.trusted_host))


if __name__ == "__main__":
    main()
