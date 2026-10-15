"""Run real Harbor Oracle/NOP and compare their actual inputs and partial rewards."""
from pathlib import Path
import json
import os
import shutil
import subprocess
import sys

from build_packages import ROOT, dump, inventory

KEY = sys.argv[1]
P = ROOT / KEY
F = ROOT / 'framework'
sys.path[:0] = [str(F), str(F / 'sdk')]
from harbor.models.task.config import TaskConfig, NetworkMode
from launcher_support import configure
life = configure(F)
out = P / 'native-controls'
out.mkdir()
task = out / 'task'
shutil.copytree(P / 'task', task)
cfg = TaskConfig.model_validate_toml((task / 'task.toml').read_text())
images = json.loads((P / 'images.json').read_text())
periodic = json.loads((P / 'scorer-controls.json').read_text())
assert periodic['passed']
cfg.environment.docker_image = images['agent']['image_id']
cfg.environment.network_mode = NetworkMode.NO_NETWORK
cfg.environment.allowed_hosts = None
cfg.agent.user = 'root'
cfg.agent.timeout_sec = 1800
cfg.agent.network_mode = NetworkMode.NO_NETWORK
cfg.agent.allowed_hosts = None
cfg.verifier.environment.docker_image = images['verifier']['image_id']
cfg.verifier.environment.network_mode = NetworkMode.NO_NETWORK
cfg.verifier.environment.allowed_hosts = None
cfg.verifier.network_mode = NetworkMode.NO_NETWORK
cfg.verifier.allowed_hosts = None
(task / 'task.toml').write_text(cfg.model_dump_toml())
report = {'kind': 'actual_native_harbor_controls', 'model_requests': 0, 'passed': False,
          'source_task_hashes': inventory(P / 'task'), 'results': {}}
for role, expected_key in [('oracle', 'reference'), ('nop', 'starter'), ('partial', 'partial')]:
    if role == 'partial':
        profile = json.loads((P / 'task/pipeline-profile.json').read_text())
        source = P / 'controls/partial/snapshot' / profile['submission_root'].lstrip('/')
        shutil.rmtree(task / 'solution')
        (task / 'solution').mkdir()
        shutil.copytree(source, task / 'solution/partial-input')
        target = profile['submission_root']
        (task / 'solution/solve.sh').write_text('#!/bin/sh\nset -eu\nrm -rf ' + target
            + '\nmkdir -p ' + target + '\ncp -R /solution/partial-input/. ' + target + '/\n')
    command = [sys.executable, str(F / 'harbor_entry.py'), 'run', '--path', str(task),
        '--agent', 'oracle' if role == 'partial' else role,
        '--env', 'edgebench_harbor.native_controls_runtime:PackageControlEnvironment',
        '--verifier', 'edgebench_harbor.native_controls_runtime:PackageNativeVerifier',
        '--jobs-dir', str(out / 'jobs'), '--job-name', role, '--n-concurrent', '1',
        '--n-attempts', '1', '--max-retries', '0', '--yes']
    with (out / (role + '-console.log')).open('wb') as f:
        result = subprocess.run(command, stdout=f, stderr=subprocess.STDOUT, timeout=2400)
    results = list((out / 'jobs' / role).glob('*/result.json'))
    trials = [json.loads(f.read_text()) for f in results]
    rewards = [x['verifier_result']['rewards']['reward'] for x in trials
               if x.get('verifier_result') and not x.get('exception_info')]
    expected = periodic['results'][expected_key]['score']
    ledgers = list((out / 'jobs' / role).glob('**/docker-*.json'))
    input_paths = list((out / 'jobs' / role).glob('**/actual-input-and-entry.json'))
    same_input = False
    if len(input_paths) == 1:
        actual = json.loads(input_paths[0].read_text())['candidate_hashes']
        prefix = json.loads((P / 'task/pipeline-profile.json').read_text())['submission_root'].lstrip('/') + '/'
        wanted = {k.removeprefix(prefix): v for k, v in periodic['results'][expected_key]['candidate_hashes'].items()}
        same_input = actual == wanted
    report['results'][role] = {'host_exit_code': result.returncode, 'rewards': rewards,
        'periodic_expected': expected, 'same_candidate_hashes': same_input,
        'owned_instances_deleted': len(ledgers) == 2 and all(json.loads(x.read_text()).get('destroyed') for x in ledgers),
        'passed': result.returncode == 0 and rewards == [expected] and same_input
            and len(ledgers) == 2 and all(json.loads(x.read_text()).get('destroyed') for x in ledgers)}
    dump(out / 'report.json', report)
    if not report['results'][role]['passed']:
        raise RuntimeError('Actual native ' + role + ' control failed; inspect its raw evidence')
report['passed'] = True
dump(out / 'report.json', report)
print('NATIVE_CONTROLS_PASSED', KEY, flush=True)
