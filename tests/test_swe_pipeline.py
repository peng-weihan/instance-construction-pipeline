"""Regression tests for known false-admission failure modes; no model/container calls."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from edge_factory.swe import catalog, gate, plan


class SWEPipelineTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.job = Path(self.temp.name)
        self.evidence = []
        self.add_report('spec', {'formula': 'weighted correct functionality'})
        for role, score in [('starter', .2), ('reference', 1), ('independent_baseline', .4)]:
            self.add_report(role, {'valid': True, 'score': score})
        self.card = {'route': 'M1', 'source': {'revision': 'a' * 40, 'license': 'MIT'},
                     'anchors': ['schemathesis_datagen_pipeline'], 'system_boundary': 'product roadmap',
                     'provided_components': ['working engine'], 'missing_capabilities': ['new product capabilities'],
                     'requirements': [{'id': 'R1', 'behavior': 'stateful feature', 'production_modules': ['engine'],
                                       'acceptance': 'stateful behavior checked', 'milestone': 'M1', 'evidence_ids': ['spec']}],
                     'integration_scenarios': [{'id': 'I1', 'requirements': ['R1']}],
                     'late_work_paths': [{'capability': c, 'prerequisites': ['R1'], 'artifact': 'source', 'metric_effect': 'behavior coverage'} for c in ['integration', 'recovery']],
                     'shortcut_probes': ['normal plugin baseline'], 'evidence': self.evidence,
                     'controls': [{'role': role, 'report_evidence_id': role,
                                   'provenance': 'independent' if role == 'independent_baseline' else role}
                                  for role in ['starter', 'reference', 'independent_baseline']],
                     'scoring': {'active_ceiling': 1, 'direction': 'higher_is_better',
                                 'formula': 'weighted correct functionality', 'spec_evidence_id': 'spec'}}
        for relative in ['task/instruction.md', 'task/task.toml', 'task/environment/Dockerfile',
                         'task/verifier/Dockerfile', 'task/tests/test.sh', 'task/solution/solve.sh']:
            p = self.job / relative; p.parent.mkdir(parents=True, exist_ok=True); p.write_text('test fixture\n')

    def add_report(self, name, content):
        p = self.job / (name + '.json'); p.write_text(json.dumps(content))
        self.evidence[:] = [x for x in self.evidence if x['id'] != name]
        self.evidence.append({'id': name, 'path': p.name, 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()})

    def inspect(self):
        (self.job / 'SCOPE_CARD.json').write_text(json.dumps(self.card))
        return gate(self.job)

    def test_no_static_input_can_be_called_difficulty_or_runtime_verified(self):
        r = self.inspect()
        self.assertEqual(r['issues'], [])
        self.assertEqual(r['outcome'], 'needs_independent_scope_and_runtime_review')
        self.assertFalse(r['six_hour_verified']); self.assertFalse(r['runtime_verified'])

    def test_disabled_performance_and_saturated_starter_block_even_reference_below_one(self):
        self.card['route'] = 'M3'; self.card['anchors'] = ['exchange_core_throughput']
        self.card['scoring'].update(active_ceiling=.25, performance={'enabled': False})
        for role in ['starter', 'reference', 'independent_baseline']:
            self.add_report(role, {'valid': True, 'score': .25})
        r = self.inspect()
        self.assertIn('performance_reward_disabled', r['issues'])
        self.assertIn('starter_already_saturates_active_score', r['issues'])
        self.assertEqual(r['outcome'], 'blocked')

    def test_full_score_ordinary_reparse_is_a_blocker(self):
        self.add_report('independent_baseline', {'valid': True, 'score': 1})
        self.assertIn('independent_baseline_already_saturates_active_score', self.inspect()['issues'])

    def test_gold_mutation_does_not_count_as_independent_baseline(self):
        self.card['controls'][-1]['provenance'] = 'reference_mutation'
        self.assertIn('reference_mutation_is_not_independent_baseline', self.inspect()['issues'])

    def test_invalid_score_is_not_zero_and_claimed_score_cannot_override_real_bytes(self):
        self.add_report('starter', {'valid': False, 'score': None})
        self.assertIn('control_not_valid_starter', self.inspect()['issues'])
        self.add_report('starter', {'valid': True, 'score': .2})
        self.card['controls'][0]['score'] = 0
        self.assertIn('claimed_score_disagrees_starter', self.inspect()['issues'])

    def test_missing_tampered_or_outside_evidence_fails_closed(self):
        (self.job / 'starter.json').write_text('{"valid": true, "score": 0}')
        self.assertTrue(any('hash mismatch' in x for x in self.inspect()['issues']))
        self.evidence[0]['path'] = '../outside.json'
        self.assertTrue(any('inside the author job' in x for x in self.inspect()['issues']))

    def test_ambiguous_reports_and_duplicate_improvement_paths_are_not_accepted(self):
        p = self.job / 'starter.json'
        p.write_text('{"valid":false,"valid":true,"score":0.2}')
        next(x for x in self.evidence if x['id'] == 'starter')['sha256'] = hashlib.sha256(p.read_bytes()).hexdigest()
        self.assertTrue(any('Duplicate JSON key' in x for x in self.inspect()['issues']))
        self.add_report('starter', {'valid': True, 'score': .2})
        self.card['late_work_paths'][1] = self.card['late_work_paths'][0]
        self.assertIn('duplicate_late_work_paths', self.inspect()['issues'])

    def test_all_original_tasks_are_classified_once_and_plan_is_non_destructive(self):
        c = catalog()
        self.assertEqual({k: v['original_count'] for k, v in c['routes'].items()}, {'M1': 13, 'M2': 12, 'M3': 6, 'M4': 3, 'M5': 2})
        source = self.job / 'sources.json'
        source.write_text(json.dumps({'jobs': [{'id': 'one', 'route': 'M1', 'repo': 'example/project',
            'url': 'https://github.com/example/project.git', 'revision': 'b' * 40, 'scope_brief': 'full system'}]}))
        out = self.job / 'new-plan'; plan(source, out, Path('/remote/new-plan'))
        with self.assertRaises(FileExistsError): plan(source, out, Path('/remote/new-plan'))
        self.assertEqual(json.loads((out / 'launch-plan.json').read_text())['phase'], 'authoring_only')


if __name__ == '__main__': unittest.main()
