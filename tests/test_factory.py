import json
from pathlib import Path
import tempfile
import unittest

from edge_factory.baseline import solve
from edge_factory.exporter import inspect_payload
from edge_factory.generator import PROFILES, derive_seed, generate_case, generate_instance
from edge_factory.pipeline import finalize, read_json, run
from edge_factory.quality import NEGATIVE_PROGRAMS, exact_oracle
from edge_factory.runtime.checker import check
from edge_factory.runtime.evaluate import evaluate, strict_json


def fixture():
    return {"depot": [0, 0], "capacity": 3, "horizon": 20, "max_stops": None,
            "vehicle_cost": 10, "customers": [
                {"id": 1, "xy": [1, 0], "demand": 1, "ready": 1, "due": 1, "service": 1},
                {"id": 2, "xy": [2, 0], "demand": 1, "ready": 3, "due": 3, "service": 1},
                {"id": 3, "xy": [3, 0], "demand": 1, "ready": 5, "due": 5, "service": 1}]}


class CheckerTests(unittest.TestCase):
    def test_exact_boundary_cost_and_score(self):
        case = fixture()
        result = check(case, {"routes": [[1, 2, 3]]})
        self.assertTrue(result["feasible"])
        self.assertEqual(result["cost"], 16)
        self.assertEqual(result["singleton_cost"], 42)
        self.assertAlmostEqual(result["score"], 100 * (1 - 16 / 42))
        self.assertEqual(exact_oracle(case)[0], 16)

    def test_constraint_near_misses(self):
        for field, value, reason in [("capacity", 2, "capacity"), ("max_stops", 2, "stop_limit"),
                                      ("horizon", 8, "depot_horizon")]:
            case = fixture()
            case[field] = value
            self.assertEqual(check(case, {"routes": [[1, 2, 3]]})["reason"], reason)
        self.assertEqual(check(fixture(), {"routes": [[2, 1, 3]]})["reason"], "time_window")

    def test_missing_duplicate_and_forged_answers(self):
        for answer, reason in [({"routes": [[1], [2]]}, "missing_customer"),
                                ({"routes": [[1], [1]]}, "duplicate_customer"),
                                ({"routes": [[True]]}, "unknown_customer"),
                                ({"routes": [[1], [2], [3]], "cost": 0}, "output_schema")]:
            self.assertEqual(check(fixture(), answer)["reason"], reason)

    def test_strict_json_rejects_nonfinite_and_duplicates(self):
        for raw in ['{"a": NaN}', '{"a": Infinity}', '{"routes":[],"routes":[]}']:
            with self.assertRaises(ValueError):
                strict_json(raw)


class GeneratorTests(unittest.TestCase):
    def test_feasible_across_profiles_and_seeds(self):
        for name, profile in PROFILES.items():
            for seed in range(20):
                case, witness = generate_case(profile, seed)
                self.assertTrue(check(case, witness)["feasible"], (name, seed))
                previous = 0
                for mode in ["singleton", "greedy", "search"]:
                    score = check(case, solve(case, mode))
                    self.assertTrue(score["feasible"], (name, seed, mode))
                    self.assertGreaterEqual(score["score"] + 1e-9, previous)
                    previous = score["score"]

    def test_namespace_seed_and_deterministic_assets(self):
        counts = {"public": 2, "feedback": 2, "final": 2}
        first = generate_instance("author-secret", "uniform_loose", 0, counts)
        self.assertEqual(first, generate_instance("author-secret", "uniform_loose", 0, counts))
        self.assertNotEqual(first, generate_instance("author-secret", "uniform_loose", 1, counts))
        self.assertNotEqual(derive_seed("s", "ab", "c"), derive_seed("s", "a", "bc"))
        self.assertNotEqual(first[1]["feedback"], first[1]["final"])

    def test_checker_and_independent_oracle_agree(self):
        for profile in PROFILES.values():
            for seed in range(4):
                case, _ = generate_case({**profile, "customers": 6}, seed)
                cost, answer = exact_oracle(case)
                self.assertEqual(check(case, answer)["cost"], cost)
                self.assertGreaterEqual(check(case, solve(case))["cost"], cost)


class RunnerTests(unittest.TestCase):
    def test_adversarial_programs_cannot_forge_reward(self):
        with tempfile.TemporaryDirectory() as directory:
            for name, program in NEGATIVE_PROGRAMS.items():
                path = Path(directory) / f"{name}.py"
                path.write_text(program)
                result = evaluate([fixture()], path, timeout=0.1 if name == "timeout" else 2, trusted_host=True)
                self.assertFalse(result["valid"], name)
                self.assertEqual(result["score"], 0)

    def test_missing_input_and_empty_suite_fail_closed(self):
        result = evaluate([fixture()], Path("no_such_solver.py"), trusted_host=True)
        self.assertFalse(result["valid"])
        with self.assertRaises(ValueError):
            evaluate([], Path("no_such_solver.py"), trusted_host=True)


class LifecycleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.temp.name) / "run"
        cls.summary = run(cls.root, ["uniform_loose"], 1, {"public": 1, "feedback": 2, "final": 2},
                          seed="test-author-secret", trusted_host=True)
        cls.instance = cls.root / "instances" / cls.summary["instances"][0]["task_id"]

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_export_contains_no_unintended_assets(self):
        task_id = self.instance.name
        task = read_json(self.root / "export/feedback" / f"{task_id}.json")
        work = inspect_payload(task["work"]["setup_cmds"][0])
        judge = inspect_payload(task["judge"]["setup_cmds"][1])
        self.assertEqual(set(work), {"SPEC.md", "solver.py", "checker.py", "evaluate.py", "cases.json"})
        self.assertEqual(set(judge), {"checker.py", "evaluate.py", "cases.json"})
        self.assertNotIn(b"Best-improvement", work["solver.py"])
        self.assertNotIn(b"def solve", work["solver.py"])
        self.assertEqual(json.loads(work["cases.json"]), read_json(self.instance / "public/cases.json"))
        self.assertEqual(json.loads(judge["cases.json"]), read_json(self.instance / "judge/feedback.json"))
        self.assertNotEqual(json.loads(judge["cases.json"]), read_json(self.instance / "judge/final.json"))
        self.assertIn("chmod 700 /tmp/setup_judge.sh", task["judge"]["setup_cmds"])

    def test_all_gates_and_final_receipt(self):
        qc = read_json(self.instance / "reports/quality.json")
        self.assertTrue(qc["passed"], qc)
        selected = read_json(self.instance / "reports/selection.json")
        final = read_json(self.instance / "reports/final.json")
        self.assertEqual(final["solver_sha256"], selected["solver_sha256"])
        self.assertFalse(selected["final_score_used_for_selection"])

    def test_final_cannot_be_repeated(self):
        with self.assertRaises(FileExistsError):
            finalize(self.instance, trusted_host=True)

    def test_changed_selected_solver_is_rejected_before_final(self):
        path = self.instance / "selected/solver.py"
        original = path.read_bytes()
        try:
            path.write_bytes(original + b"\n# changed\n")
            with self.assertRaisesRegex(ValueError, "Selected solver changed"):
                finalize(self.instance, trusted_host=True)
        finally:
            path.write_bytes(original)

    def test_existing_output_is_never_overwritten(self):
        with self.assertRaises(FileExistsError):
            run(self.root, ["uniform_loose"], 1, {"public": 1, "feedback": 1, "final": 1}, trusted_host=True)


if __name__ == "__main__":
    unittest.main()
