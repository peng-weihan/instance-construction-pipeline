import base64
import copy
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from training_factory.contract import (check_routes, distance10, geometry_fingerprint,
    official_score, read_instance, verify_solution, write_instance, write_solution, pointset_fingerprint)
from training_factory.generator import build_profiles, distribution_gate, sample
from training_factory.teacher import adapt_events, decode_submission

ROOT = Path(__file__).resolve().parents[1]


class ContractTests(unittest.TestCase):
    def setUp(self):
        self.case = {'name': 'tiny', 'capacity': 2, 'max_vehicles': 2,
                     'nodes': [[0,0,0,0,0,100,0], [1,3,4,1,0,100,0], [2,6,8,1,0,100,0]]}

    def test_original_rounding_not_manhattan_or_bankers(self):
        self.assertEqual(distance10([0,0,0], [1,3,4]), 50)
        self.assertEqual(distance10([0,0,0], [1,0.25,0]), 3)

    def test_constraints_reject_near_misses(self):
        self.assertTrue(check_routes(self.case, [[1,2]])['valid'])
        for routes in [[[1]], [[1,1,2]], [[0,1,2]], [[1],[],[2]]]:
            self.assertFalse(check_routes(self.case, routes)['valid'])
        for field, value, reason in [(3,3,'capacity'), (5,4,'time_window')]:
            bad = copy.deepcopy(self.case)
            bad['nodes'][1][field] = value
            self.assertEqual(check_routes(bad, [[1,2]])['reason'], reason)
        bad = copy.deepcopy(self.case)
        bad['nodes'][0][5] = 19
        self.assertEqual(check_routes(bad, [[1,2]])['reason'], 'depot_horizon')

    def test_original_cpp_checker_and_roundtrip(self):
        verifier = ROOT / 'runs/alignment-calibration-001/tools/original_verify'
        with tempfile.TemporaryDirectory() as directory:
            inp, out = Path(directory)/'case.txt', Path(directory)/'solution.txt'
            write_instance(self.case, inp)
            write_solution(self.case, [[1,2]], out)
            self.assertEqual(geometry_fingerprint(read_instance(inp)), geometry_fingerprint(self.case))
            self.assertTrue(verify_solution(read_instance(inp), out)['valid'])
            result = subprocess.run([verifier, inp, out], capture_output=True)
            self.assertEqual(result.returncode, 0)
            out.write_text(out.read_text().replace('Cost: 20.00', 'Cost: 19.00'))
            self.assertFalse(verify_solution(self.case, out)['valid'])
            self.assertNotEqual(subprocess.run([verifier, inp, out], capture_output=True).returncode, 0)

    def test_scoring_requires_reference_and_vehicle_priority(self):
        ref = {'valid': True, 'nv': 2, 'td': 100}
        self.assertEqual(official_score(ref, ref), 100)
        self.assertEqual(official_score({'valid': True, 'nv': 3, 'td': 100}, ref), 70)
        self.assertEqual(official_score({'valid': True, 'nv': 1, 'td': 90}, ref), 140)
        with self.assertRaises((KeyError, ValueError)):
            official_score(ref, {})

    def test_permutation_and_numeric_representation_cannot_evade_fingerprint(self):
        permuted = copy.deepcopy(self.case)
        permuted['name'] = 'changed'
        permuted['nodes'] = [permuted['nodes'][0], permuted['nodes'][2], permuted['nodes'][1]]
        for i, row in enumerate(permuted['nodes']):
            row[0] = i
            row[1:] = map(float, row[1:])
        self.assertEqual(geometry_fingerprint(self.case), geometry_fingerprint(permuted))


class GeneratorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = ROOT / 'data/routing_alignment/original_judge/internal/cases/raw'
        cls.profiles, cls.excluded = build_profiles(cls.source)

    def test_six_families_reproducible_fresh_feasible(self):
        geometries = {pointset_fingerprint(read_instance(p)) for p in self.source.glob('*.txt')}
        for family, profile in self.profiles.items():
            for seed in range(3):
                a, routes, _ = sample(profile, seed, 'fresh')
                b, routes2, _ = sample(profile, seed, 'fresh')
                self.assertEqual(a,b)
                self.assertEqual(routes,routes2)
                self.assertTrue(check_routes(a,routes)['valid'])
                self.assertNotIn(geometry_fingerprint(a), self.excluded)
                self.assertNotIn(pointset_fingerprint(a), geometries)

    def test_integer_coordinate_gate(self):
        case, _, _ = sample(self.profiles['C1'], 0, 'bad')
        case['nodes'][1][1] += .1
        self.assertFalse(distribution_gate(case, self.profiles['C1'])['checks']['integer_coordinate_ratio'])


class TraceTests(unittest.TestCase):
    def test_real_mcp_payload_preserved_and_failed_approval_excluded(self):
        item = {'id':'m1','type':'mcp_tool_call','server':'edge_shell','tool':'shell',
                'arguments':{'command':'make','timeout_seconds':30},
                'result':{'content':[{'type':'text','text':'{"returncode":0}'}]},'status':'completed'}
        events = [{'type':'item.completed','item':item},{'type':'turn.completed'}]
        adapted = adapt_events(events,'solve')
        self.assertFalse(adapted['problems'])
        self.assertEqual(json.loads(adapted['messages'][1]['tool_calls'][0]['function']['arguments']),item['arguments'])
        item['result'] = None
        item['status'] = 'failed'
        self.assertIn('missing_mcp_payload',adapt_events(events,'solve')['problems'])

    def test_completed_real_event_adapter(self):
        events = [{'type':'item.completed', 'item':{'id':'a', 'type':'command_execution', 'status':'completed',
            'command':'make', 'exit_code':0, 'aggregated_output':'compiler output'}}, {'type':'turn.completed'}]
        result = adapt_events(events, 'solve')
        self.assertFalse(result['problems'])
        self.assertEqual(result['command_count'],1)
        self.assertEqual(json.loads(result['messages'][1]['tool_calls'][0]['function']['arguments']), {'command':'make'})

    def test_missing_edits_and_incomplete_turn_rejected(self):
        result = adapt_events([{'type':'item.completed','item':{'type':'file_change','changes':[]}}], 'solve')
        self.assertIn('non_replayable_file_change', result['problems'])
        self.assertIn('turn_not_completed', result['problems'])

    def test_reasoning_is_not_exported(self):
        result = adapt_events([{'type':'item.completed','item':{'type':'reasoning','text':'private'}}], 'solve')
        self.assertNotIn('private', json.dumps(result['messages']))

    def test_submission_path_escape_rejected(self):
        payload = {'src/solver.cpp':base64.b64encode(b'int main(){}').decode(), 'Makefile':base64.b64encode(b'all:').decode()}
        self.assertEqual(len(decode_submission(payload)),2)
        for name in ['../judge/reference.json','/etc/passwd','src/../../secret']:
            with self.assertRaises(ValueError):
                decode_submission({**payload,name:'eA=='})


if __name__ == '__main__':
    unittest.main()
