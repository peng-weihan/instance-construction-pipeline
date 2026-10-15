"""Compile author bundles into self-contained SForge setup commands."""
import base64
import hashlib
import json
from pathlib import Path

from .generator import canonical


def setup_command(files, destination, private=False):
    payload = canonical({name: base64.b64encode(data).decode() for name, data in files.items()})
    encoded = base64.b64encode(payload).decode()
    sha = hashlib.sha256(payload).hexdigest()
    return (
        "python3 - <<'PY'\nimport base64, hashlib, json\nfrom pathlib import Path\n"
        f"raw = base64.b64decode({encoded!r})\n"
        f"assert hashlib.sha256(raw).hexdigest() == {sha!r}\n"
        f"root = Path({destination!r})\nroot.mkdir(parents=True, exist_ok=True)\n"
        f"root.chmod({0o700 if private else 0o755})\n"
        "for name, content in json.loads(raw).items():\n"
        "    path = root / name\n"
        "    path.parent.mkdir(parents=True, exist_ok=True)\n"
        "    path.write_bytes(base64.b64decode(content))\n"
        "    path.chmod(0o644)\n"
        "PY"
    )


def export_task(instance, task_id, phase, output, base_image):
    public = {p.name: p.read_bytes() for p in (instance / "public").iterdir() if p.is_file()}
    judge = {name: (instance / "judge" / name).read_bytes() for name in ["checker.py", "evaluate.py"]}
    judge["cases.json"] = (instance / "judge" / f"{phase}.json").read_bytes()
    task = {
        "task_id": task_id, "name": f"Generated CVRPTW {task_id}",
        "base_image": "python312", "platform": "linux/amd64", "cwd": "/home/workspace",
        "submit_paths": ["solver.py"], "submit_exclude": [], "internet": False, "game_mode": False,
        "work": {"specs_dir": "/home/workspace", "agent_query": "Read SPEC.md and improve solver.py. Use public cases locally and submit for aggregate feedback.",
                 "setup_cmds": [setup_command(public, "/home/workspace")], "cpu_limit": 1, "mem_limit": "1g"},
        "judge": {"setup_cmds": ["mkdir -p /home/workspace", setup_command(judge, "/opt/edgefactory", private=True),
                                 "chmod 700 /tmp/setup_judge.sh"],
                  "eval_cmd": "python3 /opt/edgefactory/evaluate.py --cases /opt/edgefactory/cases.json --solver /home/workspace/solver.py --timeout 2",
                  "eval_timeout": 2 * len(json.loads(judge["cases.json"])) + 30,
                  "parser": "structured_json", "score_direction": "maximize", "selection": "valid_then_score",
                  "rescale": {"kind": "linear", "lower": 0, "upper": 100}, "cpu_limit": 1, "mem_limit": "1g"},
    }
    output.mkdir(parents=True, exist_ok=True)
    benchmark = {"name": f"edgefactory_{phase}", "base_images": {"python312": {
        "official_image": base_image, "extra_packages": ["bash", "git", "curl", "ca-certificates"],
        "pip_packages": []}}}
    # JSON is a YAML subset and needs no additional writer dependency.
    (output / "BENCHMARK.yaml").write_bytes(canonical(benchmark) + b"\n")
    (output / f"{task_id}.json").write_bytes(canonical(task) + b"\n")
    return task


def inspect_payload(command):
    """Read generated payload without executing its installation commands."""
    import ast
    tree = ast.parse(command.split("\n", 1)[1].rsplit("\nPY", 1)[0])
    raw_assignment = next(node for node in tree.body if isinstance(node, ast.Assign)
                          and any(isinstance(t, ast.Name) and t.id == "raw" for t in node.targets))
    data = base64.b64decode(ast.literal_eval(raw_assignment.value.args[0]))
    return {name: base64.b64decode(content) for name, content in json.loads(data).items()}
