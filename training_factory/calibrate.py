"""Generate fresh candidates, screen distributions, and measure solver difficulty."""
import argparse
from concurrent.futures import ProcessPoolExecutor
import hashlib
import json
from pathlib import Path
import subprocess
import time

from .contract import (digest, geometry_fingerprint, official_score, read_instance, stable,
                       verify_solution, write_instance, write_solution)
from .generator import FAMILIES, build_profiles, distribution_gate, sample
from .reference import solve_reference


def write_json(path, value):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_bytes(stable(value) + b"\n")


def evaluate_binary(binary, case, input_path, output_path, budget=1, verifier=None):
    start = time.monotonic()
    try:
        process = subprocess.run([str(Path(binary).resolve()), str(Path(input_path).resolve()),
                                  str(Path(output_path).resolve()), str(budget)], capture_output=True,
                                 text=True, timeout=budget + 3)
        result = verify_solution(case, output_path) if process.returncode == 0 else {
            "valid": False, "reason": "process_exit", "nv": None, "td": None}
        if verifier:
            native = subprocess.run([str(Path(verifier).resolve()), str(Path(input_path).resolve()),
                                     str(Path(output_path).resolve())], capture_output=True, text=True, timeout=5)
            if result["valid"] != (native.returncode == 0):
                raise ValueError(f"Python/C++ verifier disagreement: {result}, {native.stdout}, {native.stderr}")
    except subprocess.TimeoutExpired:
        result = {"valid": False, "reason": "timeout", "nv": None, "td": None}
    return {**result, "elapsed_seconds": time.monotonic() - start}


def construct(output, source, baseline, verifier, per_family=4, seed=0, iterations=3000, long_iterations=12000,
              source_multiples=0, public_per_family=0):
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=False)
    profiles, excluded = build_profiles(source)
    write_json(output / "profiles.json", profiles)
    write_json(output / "excluded_original_fingerprints.json", excluded)
    write_json(output / "config.json", {"per_family": per_family, "seed": seed, "iterations": iterations,
        "generator_version": "aligned-v3-integer", "source_multiples": source_multiples,
        "public_per_family": public_per_family,
        "long_iterations": long_iterations, "reference_solver": "pyvrp==0.14.0",
        "distribution_target": "official image's 56 Solomon-100 cases; new independent point sets",
        "source_files_sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in Path(source).glob('*.txt')}})
    records, seen = [], set(excluded)
    pool = ProcessPoolExecutor(max_workers=3)
    for family in FAMILIES:
        count = profiles[family]["source_count"] * source_multiples + public_per_family if source_multiples else per_family
        for index in range(count):
            # Retry only the source envelope/feasibility generator, never silently relax gates.
            rejections = []
            for attempt in range(100):
                instance_seed = int(digest(["aligned-v3-integer", seed, family, index, attempt])[:16], 16)
                name = f"SYN_{family}_{instance_seed:016x}"
                try:
                    case, witness, generation = sample(profiles[family], instance_seed, name)
                    gate = distribution_gate(case, profiles[family])
                    if not gate["passed"]:
                        rejections.append({"attempt": attempt, "reason": "distribution", "checks": gate["checks"]})
                        continue
                    fingerprint = geometry_fingerprint(case)
                    if fingerprint in seen:
                        rejections.append({"attempt": attempt, "reason": "duplicate"})
                        continue
                    seen.add(fingerprint)
                    break
                except ValueError as exc:
                    rejections.append({"attempt": attempt, "reason": str(exc)})
            else:
                raise RuntimeError(f"No valid generated candidate for {family}/{index}")
            directory = output / "candidates" / name
            directory.mkdir(parents=True)
            input_path = directory / "instance.txt"
            write_instance(case, input_path)
            write_solution(case, witness, directory / "construction_witness.sol")
            native = subprocess.run([str(Path(verifier).resolve()), str(input_path), str(directory / "construction_witness.sol")],
                                    capture_output=True, text=True, timeout=5)
            if native.returncode:
                raise ValueError(f"Original verifier rejected construction witness: {native.stderr}")
            weak = evaluate_binary(baseline, case, input_path, directory / "starter.sol", verifier=verifier)
            futures = [pool.submit(solve_reference, case, iterations=budget, seed=rs)
                       for budget, rs in [(iterations, 0), (long_iterations, 0), (long_iterations, 1)]]
            short, long, repeat = [f.result() for f in futures]
            feasible = [r for r in [short, long, repeat] if r["valid"]]
            if not feasible:
                record = {"name": name, "family": family, "accepted": False, "reason": "reference_infeasible"}
            else:
                reference = min(feasible, key=lambda r: (r["nv"], r["td"]))
                write_solution(case, reference["routes"], directory / "reference.sol")
                verified = subprocess.run([str(Path(verifier).resolve()), str(input_path), str(directory / "reference.sol")],
                                           capture_output=True, text=True, timeout=5)
                if verified.returncode:
                    raise ValueError(f"Original verifier rejected reference: {verified.stderr}")
                weak_score = official_score(weak, reference)
                record = {"name": name, "family": family, "accepted": weak_score <= 85,
                          "reason": "proxy_hardness_pass" if weak_score <= 85 else "starter_too_close_to_reference",
                          "starter": weak, "starter_score": weak_score,
                          "short_reference_score": official_score(short, reference),
                          "long_reference_score": official_score(long, reference),
                          "reference": {k: v for k, v in reference.items() if k != "routes"},
                          "fingerprint": fingerprint}
            record["distribution"] = gate
            record["generation"] = generation
            record["generation_rejections"] = rejections
            write_json(directory / "record.json", record)
            write_json(directory / "reference_runs.json", {"short": short, "long": long, "repeat": repeat})
            records.append(record)
            write_json(output / "summary.json", {"complete": False, "records": records})
            print(json.dumps({k: record[k] for k in ["name", "family", "accepted", "reason"]} |
                             {"starter_score": record.get("starter_score"), "short_score": record.get("short_reference_score"),
                              "reference_seconds": sum(x["elapsed_seconds"] for x in [short, long, repeat])}), flush=True)
    pool.shutdown()
    summary = {"complete": True, "generated": len(records), "accepted": sum(r["accepted"] for r in records),
               "original_instances_in_training": 0, "records": records,
               "status": "distribution_and_solver_proxy_screened_not_agent_calibrated"}
    write_json(output / "summary.json", summary)
    return summary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--source", type=Path, default=Path("data/routing_alignment/original_judge/internal/cases/raw"))
    parser.add_argument("--baseline", type=Path, default=Path("runs/alignment-calibration-001/tools/original_baseline"))
    parser.add_argument("--verifier", type=Path, default=Path("runs/alignment-calibration-001/tools/original_verify"))
    parser.add_argument("--per-family", type=int, default=4)
    parser.add_argument("--seed", type=int, default=20261014)
    parser.add_argument("--iterations", type=int, default=3000)
    parser.add_argument("--long-iterations", type=int, default=12000)
    parser.add_argument("--source-multiples", type=int, default=0)
    parser.add_argument("--public-per-family", type=int, default=0)
    args = parser.parse_args()
    construct(args.output, args.source, args.baseline, args.verifier, args.per_family, args.seed,
              args.iterations, args.long_iterations, args.source_multiples, args.public_per_family)


if __name__ == "__main__":
    main()
