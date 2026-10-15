"""Retain failed preparation evidence and regrade the same candidate snapshots."""
from pathlib import Path
import asyncio
import json
import sys
import traceback
from build_packages import ROOT, dump, inventory

key = sys.argv[1]
out = ROOT / key
sys.path[:0] = [str(ROOT / 'framework'), str(ROOT / 'framework/sdk')]
from edgebench_harbor.package_scorer import DockerScorer
profile = json.loads((out / 'task/pipeline-profile.json').read_text())
if key.startswith('09_'):
    profile['judge_writable_root'] = True
    dump(out / 'task/pipeline-profile.json', profile)
images = json.loads((out / 'images.json').read_text())
state = json.loads((out / 'prepare-status.json').read_text())
state.update(phase='running_score_controls_r2', error=None, traceback=None)
dump(out / 'prepare-status.json', state)


async def main():
    scorer = DockerScorer(out / 'task', images['verifier']['image_id'], profile['verifier_timeout_sec'])
    results = {}
    for name in ['reference', 'starter', 'empty', 'partial']:
        snapshot = out / 'controls' / name / 'snapshot'
        report, seconds = await scorer.grade(snapshot, out / 'controls' / name / 'grading-r2')
        results[name] = {'score': report['score'], 'valid': report['valid'], 'seconds': seconds,
                        'failed_checks': report['failed_checks'], 'candidate_hashes': inventory(snapshot)}
        dump(out / 'scorer-controls-r2.json', {'passed': False, 'status': 'running', 'results': results})
        print(key, name, report['score'], seconds, flush=True)
    assert results['reference']['score'] == 1.0
    assert results['empty']['score'] == 0.0
    assert 0 < results['partial']['score'] < 1
    dump(out / 'scorer-controls.json', {'passed': True, 'status': 'completed', 'results': results,
        'image_id': images['verifier']['image_id'], 'task_hashes': inventory(out / 'task'),
        'formal_native_harbor_controls': False, 'score_entry': 'unchanged authored /tests/test.sh',
        'model_runs': 0, 'formal_acceptance': False})
    state.update(phase='ready_for_cloud_admission')
    dump(out / 'prepare-status.json', state)


try:
    asyncio.run(main())
except Exception as exc:
    state.update(phase='preparation_failed', error=repr(exc), traceback=traceback.format_exc())
    dump(out / 'prepare-status.json', state)
    raise
