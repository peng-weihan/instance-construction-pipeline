#!/usr/bin/env python3
"""Trusted controller: candidate generator and generated SDK run in subprocesses.

Host runs provide behavioral evidence only. Container UID/resource isolation is
part of the build context and must be verified separately before acceptance.
"""
import argparse
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
from cases import SCHEMAS, ASSERTIONS, document


def run(command, cwd, stdin=None, timeout=60):
    env = {k: v for k, v in os.environ.items() if k not in {"PYTHONPATH", "PYTHONHOME", "PYTHONSTARTUP", "LD_PRELOAD"}}
    # Explicit PATH includes the pinned ruff dependency used by the generator.
    env["PATH"] = str(Path(sys.executable).parent) + os.pathsep + "/usr/local/bin:/usr/bin:/bin"
    user = {"user": 65534, "group": 65534, "extra_groups": []} if os.getuid() == 0 else {}
    import resource
    def limits():
        resource.setrlimit(resource.RLIMIT_CPU, (45, 45))
        resource.setrlimit(resource.RLIMIT_FSIZE, (2 * 1024 * 1024, 2 * 1024 * 1024))
        if sys.platform.startswith("linux"):
            resource.setrlimit(resource.RLIMIT_AS, (1024 * 1024 * 1024, 1024 * 1024 * 1024))
    with tempfile.TemporaryFile() as stdout, tempfile.TemporaryFile() as stderr:
        p = subprocess.Popen(command, cwd=cwd, env=env, stdin=subprocess.PIPE, stdout=stdout, stderr=stderr,
                             start_new_session=True, text=True, preexec_fn=limits, **user)
        timed_out = False
        try:
            p.communicate(stdin, timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            os.killpg(p.pid, signal.SIGKILL)
            p.communicate()
        finally:
            try:
                os.killpg(p.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        stdout.seek(0)
        stderr.seek(0)
        return {"command": command, "cwd": str(cwd), "exit": p.returncode,
                "stdout": stdout.read(16000).decode(errors="replace"),
                "stderr": stderr.read(16000).decode(errors="replace"), "timeout": timed_out}


def grade(candidate):
    import importlib.util
    for dependency in ["httpx", "pydantic", "jinja2", "attrs", "typer"]:
        if importlib.util.find_spec(dependency) is None:
            raise RuntimeError("judge dependency missing: " + dependency)
    checks, records = [], []
    for name in SCHEMAS:
        if not (candidate / "openapi_python_client/__main__.py").exists():
            checks.append({"name": name, "passed": False, "detail": "missing generator"})
            continue
        with tempfile.TemporaryDirectory(prefix="openapi-pilot-") as tmp:
            temp = Path(tmp)
            temp.chmod(0o777)
            spec = temp / "spec.json"
            spec.write_text(json.dumps(document(name)))
            output = temp / "pilot_client"
            r = run([sys.executable, "-m", "openapi_python_client", "generate", "--path", str(spec), "--meta", "none", "--output-path", str(output)], candidate)
            records.append({"case": name, "phase": "generate", **r})
            if name == "conflict":
                combined = r["stdout"] + r["stderr"]
                passed = r["exit"] != 0 and "Envelope" in combined and "id" in combined
            elif r["exit"] != 0:
                passed = False
            else:
                script = "from pilot_client.models.envelope import Envelope\nfrom pilot_client.types import Unset\n" + ASSERTIONS[name]
                r = run([sys.executable, "-c", script], temp)
                records.append({"case": name, "phase": "sdk-execution", **r})
                passed = r["exit"] == 0
            checks.append({"name": name, "passed": passed})
    score = sum(c["passed"] for c in checks) / 6
    return {"valid": True, "score": score, "pass_rate": score, "checks": checks,
            "metrics": {"passed_semantic_groups": sum(c["passed"] for c in checks), "fixed_denominator": 6},
            "summary": "Generated SDK semantic groups; host execution is not Harbor acceptance", "records": records}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidate", type=Path, default=Path("/home/workspace/openapi_composition/submission"))
    ap.add_argument("--output", type=Path, default=Path("/logs/verifier"))
    args = ap.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    for name in ("reward.txt", "reward.json"):
        (args.output / name).unlink(missing_ok=True)
    try:
        result = grade(args.candidate.resolve())
    except Exception as exc:
        (args.output / "score.json").write_text(json.dumps({"valid": False, "score": None, "error": repr(exc)}, indent=2))
        raise
    (args.output / "score.json").write_text(json.dumps(result, indent=2))
    (args.output / "reward.txt").write_text(str(result["score"]) + "\n")
    print(json.dumps({k: v for k, v in result.items() if k != "records"}, indent=2))

if __name__ == "__main__":
    main()
