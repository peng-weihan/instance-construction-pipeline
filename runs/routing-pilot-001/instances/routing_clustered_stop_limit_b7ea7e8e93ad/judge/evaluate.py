"""Evaluate one-file Python solvers; root containers drop solver privileges.

The explicit trusted-host mode is for author-owned baselines, not a sandbox.
Solver output is captured and parsed, never forwarded into the grader protocol.
"""
import argparse
from collections import Counter
import json
import math
import os
from pathlib import Path
import resource
import shutil
import signal
import subprocess
import sys
import tempfile

try:
    from .checker import check
except ImportError:
    from checker import check


OUTPUT_LIMIT = 128 * 1024


def strict_json(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("duplicate JSON key")
            result[key] = value
        return result

    def constant(value):
        raise ValueError("non-finite JSON number")

    return json.loads(raw, object_pairs_hook=pairs, parse_constant=constant)


def run_case(case, solver, timeout, trusted_host=False):
    if os.getuid() != 0 and not trusted_host:
        raise RuntimeError("Use a root Judge container, or --trusted-host for author-owned code.")
    if not solver.is_file() or solver.is_symlink() or solver.stat().st_size > 1024 * 1024:
        return {"feasible": False, "reason": "submission_file", "cost": None, "score": 0.0}

    def limits():
        resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
        resource.setrlimit(resource.RLIMIT_FSIZE, (OUTPUT_LIMIT, OUTPUT_LIMIT))
        cpu = max(1, math.ceil(timeout))
        resource.setrlimit(resource.RLIMIT_CPU, (cpu, cpu + 1))
        if sys.platform == "linux":
            resource.setrlimit(resource.RLIMIT_AS, (512 * 1024**2, 512 * 1024**2))
        if os.getuid() == 0:
            os.setgroups([])
            os.setgid(65534)
            os.setuid(65534)

    with tempfile.TemporaryDirectory(prefix="ef-solver-") as tmp:
        root = Path(tmp)
        root.chmod(0o755)
        entry = root / "solver.py"
        shutil.copyfile(solver, entry)
        entry.chmod(0o644)
        with tempfile.TemporaryFile() as stdout, tempfile.TemporaryFile() as stderr:
            proc = subprocess.Popen(
                [sys.executable, "-I", str(entry)], cwd=root,
                stdin=subprocess.PIPE, stdout=stdout, stderr=stderr,
                env={"PATH": "/usr/local/bin:/usr/bin:/bin", "LANG": "C.UTF-8"},
                start_new_session=True, preexec_fn=limits)
            reason = None
            try:
                proc.communicate(json.dumps(case).encode(), timeout=timeout)
            except subprocess.TimeoutExpired:
                reason = "timeout"
            finally:
                try:
                    os.killpg(proc.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                proc.wait()
            stdout.seek(0)
            raw = stdout.read(OUTPUT_LIMIT + 1)
            if reason is None and (len(raw) >= OUTPUT_LIMIT or proc.returncode == -signal.SIGXFSZ):
                reason = "output_limit"
            if reason is None and proc.returncode != 0:
                reason = "process_exit"
            if reason is None:
                try:
                    return check(case, strict_json(raw))
                except (ValueError, TypeError, UnicodeDecodeError, RecursionError):
                    reason = "malformed_json"
            return {"feasible": False, "reason": reason, "cost": None, "score": 0.0}


def evaluate(cases, solver, timeout=2.0, trusted_host=False, author_details=False):
    if not cases:
        raise ValueError("An empty evaluation split cannot be graded.")
    if not math.isfinite(timeout) or timeout <= 0:
        raise ValueError("timeout must be positive and finite")
    rows = [run_case(case, Path(solver), timeout, trusted_host) for case in cases]
    passed = sum(r["feasible"] for r in rows)
    valid = passed == len(rows)
    result = {
        "valid": valid,
        "score": sum(r["score"] for r in rows) / len(rows) if valid else 0.0,
        "pass_rate": passed / len(rows), "total_tests": len(rows), "passed": passed,
        "failed": len(rows) - passed,
        "summary": f"{passed}/{len(rows)} feasible; all cases required for a valid submission",
        "metrics": {"failure_counts": dict(Counter(r["reason"] for r in rows if not r["feasible"]))},
    }
    if author_details:
        result["author_case_results"] = rows
    return result


def emit(report):
    print(">>>>> Start Structured Result")
    print(json.dumps(report, allow_nan=False, sort_keys=True))
    print(">>>>> End Structured Result")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", required=True, type=Path)
    parser.add_argument("--solver", required=True, type=Path)
    parser.add_argument("--timeout", type=float, default=2.0)
    parser.add_argument("--trusted-host", action="store_true")
    args = parser.parse_args()
    try:
        report = evaluate(strict_json(args.cases.read_bytes()), args.solver, args.timeout, args.trusted_host)
    except Exception as exc:
        report = {"valid": False, "score": 0.0, "pass_rate": 0.0,
                  "summary": f"evaluator_error:{type(exc).__name__}"}
    emit(report)


if __name__ == "__main__":
    main()
