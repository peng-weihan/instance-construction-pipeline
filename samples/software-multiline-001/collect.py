"""Collect author evidence without executing candidates or inventing acceptance.

Run with the project's Python 3.12. This is a construction inventory, not QC.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
import tomllib

ROOT = Path(__file__).resolve().parent


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def collect(route: dict) -> dict:
    base = ROOT / route["id"]
    required = ["instruction.md", "task.toml", "source-card.md", "environment/Dockerfile", "verifier/Dockerfile", "tests/test.sh", "solution/solve.sh", "authoring/provenance.json", "authoring/score-spec.json", "authoring/build-manifest.json", "AUTHORING_REPORT.json"]
    present = [x for x in required if (base / x).is_file()]
    result = {**route, "directory": str(base.relative_to(ROOT)), "present": present, "missing": [x for x in required if x not in present], "file_hashes": {x: sha(base / x) for x in present}, "formal_acceptance": False, "six_hour_difficulty_verified": False}
    for rel, key in [("AUTHORING_REPORT.json", "author_report"), ("authoring/provenance.json", "provenance"), ("authoring/score-spec.json", "score_spec")]:
        if (base / rel).is_file():
            try:
                result[key] = json.loads((base / rel).read_text())
            except (ValueError, OSError) as error:
                result[key + "_read_error"] = str(error)
    if (base / "task.toml").is_file():
        try:
            config = tomllib.loads((base / "task.toml").read_text())
            result["toml_parse"] = "pass"
            result["declared_protocol"] = {
                "schema_version": config.get("schema_version"),
                "reward_type": config.get("metadata", {}).get("reward_type"),
                "agent_timeout_sec": config.get("agent", {}).get("timeout_sec"),
                "agent_network_mode": config.get("agent", {}).get("network_mode"),
                "environment_network_mode": config.get("environment", {}).get("network_mode"),
                "verifier_network_mode": config.get("verifier", {}).get("network_mode"),
                "verifier_environment_mode": config.get("verifier", {}).get("environment_mode"),
                "verifier_environment_network_mode": config.get("verifier", {}).get("environment", {}).get("network_mode"),
                "artifacts": config.get("artifacts"),
            }
            result["contains_legacy_local_schema"] = str(config.get("schema", "")).startswith("edgebench.local-task")
        except (ValueError, OSError) as error:
            result["toml_parse"] = "fail"
            result["toml_error"] = str(error)
    tests, mirror = base / "tests/grader.py", base / "verifier/tests/grader.py"
    if tests.is_file() and mirror.is_file():
        result["grader_mirror_byte_equal"] = sha(tests) == sha(mirror)
    result["inventory_only"] = True
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / "BATCH_STATUS.json")
    args = parser.parse_args()
    plan = json.loads((ROOT / "routes.json").read_text())
    routes = [collect(route) for route in plan["routes"]]
    report = {"batch": plan["batch"], "generated_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(), "source_plan_sha256": sha(ROOT / "routes.json"), "inventory_only": True, "route_count": len(routes), "routes": routes, "teacher_rollouts_started_by_collector": 0, "warning": "File presence, TOML parsing and author reports are not container, Harbor or difficulty acceptance."}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    for route in routes:
        print(f"{route['id']}: {len(route['present'])}/{len(route['present'])+len(route['missing'])} required files; author_report={'author_report' in route}; inventory only")


if __name__ == "__main__":
    main()
