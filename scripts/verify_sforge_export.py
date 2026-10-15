"""Check exported contracts using the pinned official SForge checkout.

Requires PyYAML and typing_extensions, as the official loader does.
Does not build containers or call an LLM.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "upstream/EdgeBench"))

from sforge.harness.benchmark import load_benchmark
from sforge.harness.dockerfiles import get_dockerfile_base, get_dockerfile_judge, get_dockerfile_work
from sforge.harness.log_parsers.structured_json import parse_structured_json
from sforge.harness.score_rescale import rescale_score
from sforge.harness.selection import select_best
from sforge.harness.task_spec import load_all_tasks


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", type=Path, required=True)
    args = parser.parse_args()
    run = args.run.resolve()
    summary = json.loads((run / "summary.json").read_text())
    expected = {r["task_id"] for r in summary["instances"] if r["quality_passed"]}
    records = []
    for phase in ["feedback", "final"]:
        directory = run / "export" / phase
        benchmark = load_benchmark(directory)
        tasks = load_all_tasks(directory, benchmark)
        assert {t.task_id for t in tasks} == expected
        for task in tasks:
            assert task.judge.parser == "structured_json"
            assert task.judge.selection == "valid_then_score"
            assert task.submit_paths == ["solver.py"]
            assert not task.internet and not task.game_mode
            assert len(task.work_image_hash) == len(task.judge_image_hash) == 64
            base = get_dockerfile_base(task.base_image_spec, task.platform)
            work = get_dockerfile_work(task.platform, task.base_image_tag, task.cwd)
            judge = get_dockerfile_judge(task.platform, task.base_image_tag, task.cwd)
            assert "USER agent" in work and "setup_judge.sh" in judge and "useradd" in base
            instance = run / "instances" / task.task_id
            checked_outputs = 0
            if phase == "feedback":
                reports = json.loads((instance / "reports/exported_lifecycle.json").read_text())
                entries = []
                for name, reference in reports.items():
                    raw = (instance / "reports" / f"exported_{name}.log").read_text()
                    parsed = parse_structured_json(raw)
                    assert parsed == reference
                    assert abs(rescale_score(task.judge.rescale, parsed["score"]) - parsed["score"]) < 1e-9
                    entries.append({"round": name, "status": "completed", **parsed})
                    checked_outputs += 1
                best = select_best(entries, score_direction="maximize", policy="valid_then_score")
                assert best["best_round"] == "search" and best["best_valid"]
            records.append({"task_id": task.task_id, "phase": phase, "official_loader": "passed",
                            "dockerfile_render": "passed", "actual_judge_outputs_parsed": checked_outputs,
                            "work_image_key": task.work_image_key, "judge_image_key": task.judge_image_key})
    for result in summary["instances"]:
        instance = run / "instances" / result["task_id"]
        manifest = json.loads((instance / "manifest.json").read_text())
        for name, expected_hash in manifest["files"].items():
            assert hashlib.sha256((instance / name).read_bytes()).hexdigest() == expected_hash, name
    result = {"status": "passed", "tasks_checked": len(records),
              "actual_judge_outputs_parsed": sum(r["actual_judge_outputs_parsed"] for r in records),
              "source_commit": subprocess.check_output(["git", "-C", str(ROOT / "upstream/EdgeBench"), "rev-parse", "HEAD"], text=True).strip(),
              "python": sys.version, "records": records,
              "container_built_or_run": False, "model_evaluation_run": False}
    destination = run / "sforge_contract_validation.json"
    if destination.exists():
        if json.loads(destination.read_text()) != result:
            raise RuntimeError("Existing validation differs; preserve it and use a fresh run directory.")
    else:
        with destination.open("x") as f:
            json.dump(result, f, indent=2)
            f.write("\n")
    print(json.dumps({k: v for k, v in result.items() if k != "records"}, indent=2))


if __name__ == "__main__":
    main()
