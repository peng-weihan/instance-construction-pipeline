"""Generate -> verify -> export -> select on feedback -> finalize once."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import secrets
import shutil
import subprocess
import sys
import tempfile
import time

from . import __version__
from . import baseline
from .exporter import export_task, inspect_payload
from .generator import PROFILES, canonical, derive_seed, digest, generate_case, generate_instance
from .quality import NEGATIVE_PROGRAMS, exact_oracle
from .runtime.checker import check
from .runtime.evaluate import evaluate

PACKAGE = Path(__file__).resolve().parent


def write_json(path, value, exclusive=False):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb" if exclusive else "wb") as f:
        f.write(canonical(value) + b"\n")


def read_json(path):
    return json.loads(path.read_text())


def file_hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inventory(root):
    return {str(p.relative_to(root)): file_hash(p) for p in sorted(root.rglob("*")) if p.is_file()}


def exported_lifecycle(judge_payload, solver):
    """Execute exported evaluator bytes with a copied submission on a trusted host."""
    with tempfile.TemporaryDirectory(prefix="ef-lifecycle-") as directory:
        temp = Path(directory)
        for name, data in judge_payload.items():
            (temp / name).write_bytes(data)
        shutil.copyfile(solver, temp / "solver.py")
        result = subprocess.run([sys.executable, str(temp / "evaluate.py"), "--cases", str(temp / "cases.json"),
                                 "--solver", str(temp / "solver.py"), "--trusted-host"],
                                capture_output=True, text=True,
                                timeout=2 * len(json.loads(judge_payload["cases.json"])) + 15)
        if result.returncode:
            raise RuntimeError(f"Exported evaluator failed: {result.stderr[:1000]}")
        block = result.stdout.split(">>>>> Start Structured Result\n", 1)[1].split("\n>>>>> End Structured Result", 1)[0]
        return json.loads(block), result.stdout


def specification(profile, config):
    return f"""# Constrained routing solver

Build a general solver for the `{profile}` distribution. The configuration is
`{json.dumps(config, sort_keys=True)}`. Public examples and hidden cases are independent.

Your only submitted file is `solver.py`, a Python 3.12 standard-library program.
Each process reads ONE JSON object from stdin and writes ONE JSON object to stdout:
`{{"routes": [[customer_id, ...], ...]}}`. No extra keys, logging, score claims,
duplicate JSON keys, boolean IDs or non-finite numbers are accepted.
Processes start fresh for each case, with 2 seconds and 512 MiB on the Linux Judge.
Output is limited to 128 KiB. Do not use local files, subprocesses or network services.

Every customer must be visited exactly once. Each nonempty route starts at the depot
at time zero and returns before `horizon`. Manhattan distance is both travel cost
and travel time. Waiting is permitted. Service START must be in the inclusive
`[ready, due]` interval; service duration is then added. Sum of demands must not exceed
`capacity`; `max_stops` is a route stop limit, or null when absent. There is no hard
vehicle-count limit. All coordinates, demands and times are integers.

Cost = total travel distance + vehicle_cost * number of routes.
Singleton cost = sum of round trips plus one vehicle fee per customer.
Case score = 100 * max(0, 1 - cost / singleton_cost).
All cases must be feasible; any invalid case makes the submission invalid with score 0.
Otherwise the overall score is the equally weighted mean of case scores.
Singleton routes are always feasible and score 0. Lower valid costs always score higher;
no best-known-solution table or candidate-reported cost is used.

Start with `solver.py`. Run a public check:
`python3 evaluate.py --cases cases.json --solver solver.py --trusted-host`
`checker.py` documents the exact constraints. External feedback returns aggregate score,
feasible fraction and counts of failure types. Hidden routes and per-case costs stay private.
The controller selects one frozen program on feedback before a separate one-time final test.
"""


def finalize(instance, trusted_host):
    receipt = read_json(instance / "reports/selection.json")
    solver = instance / "selected/solver.py"
    if file_hash(solver) != receipt["solver_sha256"]:
        raise ValueError("Selected solver changed after feedback selection.")
    cases_path = instance / "judge/final.json"
    if file_hash(cases_path) != receipt["final_cases_sha256"]:
        raise ValueError("Final cases changed after selection.")
    # Reserve before evaluation; even interrupted final runs cannot silently be repeated.
    lock = instance / "reports/final.lock"
    with lock.open("x") as f:
        f.write(receipt["solver_sha256"] + "\n")
    report = evaluate(read_json(cases_path), solver, trusted_host=trusted_host, author_details=True)
    report["selection_sha256"] = file_hash(instance / "reports/selection.json")
    report["solver_sha256"] = receipt["solver_sha256"]
    write_json(instance / "reports/final.json", report, exclusive=True)
    return report


def build_instance(root, secret, profile, replica, counts, base_image, trusted_host):
    started = time.monotonic()
    config, cases, certificates = generate_instance(secret, profile, replica, counts)
    source_sha = {str(p.relative_to(PACKAGE)): file_hash(p) for p in sorted(PACKAGE.rglob("*.py"))}
    content_hash = digest({"version": __version__, "source_sha256": source_sha, "config": config, "cases": cases})
    task_id = f"routing_{profile}_{content_hash[:12]}"
    instance = root / "instances" / task_id
    instance.mkdir(parents=True, exist_ok=False)
    journal = instance / "events.jsonl"

    def event(stage, **details):
        with journal.open("ab") as f:
            f.write(canonical({"stage": stage, "elapsed_seconds": round(time.monotonic() - started, 4), **details}) + b"\n")

    event("generated", profile=profile, replica=replica, counts=counts)
    for directory in ["public", "judge", "author", "baselines", "reports", "selected", "controls"]:
        (instance / directory).mkdir()
    for split, rows in cases.items():
        write_json(instance / ("public/cases.json" if split == "public" else f"judge/{split}.json"), rows)
    write_json(instance / "author/certificates.json", certificates)
    (instance / "public/SPEC.md").write_text(specification(profile, config))
    for name in ["checker.py", "evaluate.py"]:
        for target in ["public", "judge"]:
            shutil.copyfile(PACKAGE / "runtime" / name, instance / target / name)
    template = (PACKAGE / "baseline.py").read_text()
    for mode in ["singleton", "greedy", "search"]:
        (instance / "baselines" / f"{mode}.py").write_text(template.replace('MODE = "search"', f'MODE = "{mode}"'))
    # Public starter must not carry the private greedy/search implementations.
    (instance / "public/solver.py").write_text(
        'import json, sys\ncase = json.load(sys.stdin)\n'
        'print(json.dumps({"routes": [[c["id"]] for c in case["customers"]]}))\n')

    gates = {}
    regenerated = generate_instance(secret, profile, replica, counts)
    gates["deterministic_generation"] = (config, cases, certificates) == regenerated
    case_digests = [digest(case) for rows in cases.values() for case in rows]
    gates["no_exact_case_duplicates"] = len(case_digests) == len(set(case_digests))
    gates["all_certificates_feasible"] = all(check(case, answer)["feasible"]
        for split, rows in cases.items() for case, answer in zip(rows, certificates[split]))
    tiny_config = {**config, "customers": 6}
    tiny, _ = generate_case(tiny_config, derive_seed(secret, task_id, "tiny_oracle"))
    optimal_cost, optimal_answer = exact_oracle(tiny)
    checked = check(tiny, optimal_answer)
    baseline_tiny = check(tiny, baseline.solve(tiny))
    gates["tiny_exact_oracle"] = checked["feasible"] and checked["cost"] == optimal_cost and baseline_tiny["cost"] >= optimal_cost
    write_json(instance / "author/tiny_oracle.json", {"case": tiny, "optimum": optimal_cost, "answer": optimal_answer})
    event("certificates_and_oracle", gates=gates)

    negative_reports = {}
    for name, program in NEGATIVE_PROGRAMS.items():
        path = instance / "controls" / f"{name}.py"
        path.write_text(program)
        negative_reports[name] = evaluate(cases["feedback"][:1], path, timeout=0.15 if name == "timeout" else 2,
                                          trusted_host=trusted_host, author_details=True)
    gates["negative_controls_rejected"] = all(not r["valid"] and r["score"] == 0 for r in negative_reports.values())
    write_json(instance / "reports/negative_controls.json", negative_reports)
    event("negative_controls", rejected=sum(not r["valid"] for r in negative_reports.values()))

    feedback = {}
    for mode in ["singleton", "greedy", "search"]:
        solver = instance / "baselines" / f"{mode}.py"
        report = evaluate(cases["feedback"], solver, trusted_host=trusted_host, author_details=True)
        report["solver_sha256"] = file_hash(solver)
        feedback[mode] = report
        write_json(instance / "reports" / f"feedback_{mode}.json", report)
    gates["baselines_feasible"] = all(r["valid"] for r in feedback.values())
    gates["score_separation"] = feedback["search"]["score"] - feedback["singleton"]["score"] >= 10
    gates["search_not_worse_than_greedy"] = feedback["search"]["score"] + 1e-9 >= feedback["greedy"]["score"]
    repeat = evaluate(cases["feedback"], instance / "baselines/search.py", trusted_host=trusted_host)
    gates["repeatable_search_score"] = repeat["score"] == feedback["search"]["score"] and repeat["valid"]
    event("feedback_calibration", scores={name: r["score"] for name, r in feedback.items()})

    # Decode payloads and run the exact exported Judge bytes through a local lifecycle.
    tasks = {phase: export_task(instance, task_id, phase, instance / "export" / phase, base_image)
             for phase in ["feedback", "final"]}
    work_payload = inspect_payload(tasks["feedback"]["work"]["setup_cmds"][0])
    judge_payload = inspect_payload(tasks["feedback"]["judge"]["setup_cmds"][1])
    gates["work_contains_only_public_assets"] = work_payload == {p.name: p.read_bytes() for p in (instance / "public").iterdir()}
    gates["feedback_judge_has_no_final_cases"] = set(judge_payload) == {"checker.py", "evaluate.py", "cases.json"} and json.loads(judge_payload["cases.json"]) == cases["feedback"]
    lifecycle = {}
    for name, solver in [("search", instance / "baselines/search.py"), ("empty", instance / "controls/empty.py"),
                         ("spoofed_markers", instance / "controls/spoofed_markers.py")]:
        report, output = exported_lifecycle(judge_payload, solver)
        lifecycle[name] = report
        (instance / "reports" / f"exported_{name}.log").write_text(output)
    gates["exported_lifecycle"] = (lifecycle["search"]["valid"] and lifecycle["search"]["score"] == feedback["search"]["score"]
                                   and all(not lifecycle[name]["valid"] and lifecycle[name]["score"] == 0
                                           for name in ["empty", "spoofed_markers"]))
    write_json(instance / "reports/exported_lifecycle.json", lifecycle)
    event("exported", phases=["feedback", "final"])

    qc = {"passed": all(gates.values()), "gates": gates, "negative_controls": len(negative_reports),
          "feedback_scores": {name: r["score"] for name, r in feedback.items()},
          "container_verified": False, "long_horizon_calibrated": False}
    write_json(instance / "reports/quality.json", qc)
    final = None
    if qc["passed"]:
        for phase in ["feedback", "final"]:
            destination = root / "export" / phase
            destination.mkdir(parents=True, exist_ok=True)
            for name in ["BENCHMARK.yaml", f"{task_id}.json"]:
                shutil.copyfile(instance / "export" / phase / name, destination / name)
        selected = max(feedback, key=lambda name: (feedback[name]["valid"], feedback[name]["score"], name))
        shutil.copyfile(instance / "baselines" / f"{selected}.py", instance / "selected/solver.py")
        receipt = {"selection_rule": "highest valid feedback score; ties by mode name", "selected": selected,
                   "solver_sha256": file_hash(instance / "selected/solver.py"),
                   "feedback_score": feedback[selected]["score"], "feedback_report_sha256": file_hash(instance / "reports" / f"feedback_{selected}.json"),
                   "final_cases_sha256": file_hash(instance / "judge/final.json"), "final_score_used_for_selection": False}
        write_json(instance / "reports/selection.json", receipt, exclusive=True)
        event("selected_on_feedback", selected=selected)
        final = finalize(instance, trusted_host)
        event("final_evaluated_once", score=final["score"], valid=final["valid"])
    event("completed", status="host_verified" if qc["passed"] else "rejected")
    manifest = {"task_id": task_id, "family_id": "constrained_routing", "generator_version": __version__,
                "profile": profile, "replica": replica, "config": config, "case_counts": counts,
                "case_content_sha256": content_hash, "case_sha256": {k: [digest(c) for c in v] for k, v in cases.items()},
                "generator_source_sha256": source_sha,
                "status": "host_verified" if qc["passed"] else "rejected", "container_verified": False,
                "long_horizon_calibrated": False, "base_image": base_image,
                "base_image_digest_pinned": "@sha256:" in base_image,
                "files": inventory(instance)}
    write_json(instance / "manifest.json", manifest)
    return {"task_id": task_id, "profile": profile, "status": manifest["status"],
            "quality_passed": qc["passed"], "feedback_scores": qc["feedback_scores"],
            "final_score": final["score"] if final else None,
            "elapsed_seconds": round(time.monotonic() - started, 3)}


def run(output, profiles, replicas, counts, seed=None, trusted_host=False, base_image="python:3.12-slim-bookworm"):
    if not trusted_host:
        raise ValueError("This trial runner requires --trusted-host for the bundled author-owned programs.")
    if not profiles or len(set(profiles)) != len(profiles) or not set(profiles) <= PROFILES.keys():
        raise ValueError("Provide distinct known profiles.")
    if replicas < 1 or set(counts) != {"public", "feedback", "final"} or any(n < 1 for n in counts.values()):
        raise ValueError("Replica and split counts must all be positive.")
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=False)
    secret = str(seed) if seed is not None else secrets.token_hex(32)
    write_json(output / "author_secrets.json", {"root_seed": secret, "fixed_demo_seed": seed is not None})
    (output / "author_secrets.json").chmod(0o600)
    source_hashes = {str(p.relative_to(PACKAGE)): file_hash(p) for p in sorted(PACKAGE.rglob("*.py"))}
    write_json(output / "run_config.json", {"version": __version__, "profiles": profiles, "replicas": replicas,
        "counts": counts, "source_sha256": source_hashes, "python": sys.version,
        "created_at_utc": datetime.now(timezone.utc).isoformat(), "execution": "trusted_host",
        "base_image": base_image, "container_verified": False, "model_calls": 0})
    results = []
    for profile in profiles:
        for replica in range(replicas):
            result = build_instance(output, secret, profile, replica, counts, base_image, trusted_host)
            results.append(result)
            write_json(output / "summary.json", {"instances": results, "completed": False})
            print(json.dumps(result, ensure_ascii=False), flush=True)
    all_digests = [h for r in results for split in read_json(output / "instances" / r["task_id"] / "manifest.json")["case_sha256"].values() for h in split]
    unique = len(all_digests) == len(set(all_digests))
    summary = {"instances": results, "completed": True, "instances_generated": len(results),
               "host_verified": sum(r["quality_passed"] for r in results), "cases_generated": len(all_digests),
               "no_exact_duplicates_across_batch": unique, "container_verified": False,
               "long_horizon_calibrated": False, "model_calls": 0}
    write_json(output / "summary.json", summary)
    if not unique or not all(r["quality_passed"] for r in results):
        raise RuntimeError(f"Some quality gates failed; inspect {output / 'summary.json'}")
    return summary
