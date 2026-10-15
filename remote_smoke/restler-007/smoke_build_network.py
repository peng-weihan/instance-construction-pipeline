"""Remote-only container smoke test. Does not launch a model or certify difficulty."""
import argparse
import hashlib
import json
import platform
import subprocess
import time
import uuid
from pathlib import Path


def command(argv, log, timeout):
    with log.open('w') as stream:
        process = subprocess.run(argv, stdout=stream, stderr=subprocess.STDOUT, timeout=timeout)
    if process.returncode:
        raise RuntimeError(f'command failed ({process.returncode}); see {log.name}')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--task', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--build-network', choices=['default', 'host'], default='default')
    args = parser.parse_args()
    task, output = Path(args.task).resolve(), Path(args.output).resolve()
    permitted = Path('/ws/users/raymone')
    if platform.system() != 'Linux' or not task.is_relative_to(permitted) or not output.is_relative_to(permitted):
        raise SystemExit('Run only in the personal /ws/users/raymone subtree on the Linux development host.')
    output.mkdir(parents=True, exist_ok=False)
    token = uuid.uuid4().hex[:12]
    agent, judge = f'edge-raymone-agent:{token}', f'edge-raymone-judge:{token}'
    state = {'status': 'started', 'task': task.name, 'started_unix': time.time(),
             'model_runs': 0, 'six_hour_runs': 0, 'accepted': False, 'architecture': platform.machine(),
             'agent_image': agent, 'judge_image': judge, 'reports': {},
             'build_network': args.build_network, 'runtime_network': 'none'}
    status_file = output / 'run_status.json'
    def save():
        status_file.write_text(json.dumps(state, indent=2) + '\n')
    save()
    def container(argv, name, log, timeout):
        try:
            command(['docker', 'run', '--name', name, '--rm', *argv], log, timeout)
        finally:
            subprocess.run(['docker', 'rm', '-f', name], capture_output=True, timeout=30)
    try:
        manifest = json.loads((task / 'files.sha256.json').read_text())
        for entry in manifest:
            actual = hashlib.sha256((task / entry['path']).read_bytes()).hexdigest()
            if actual != entry['sha256']:
                raise ValueError('transferred file digest mismatch: ' + entry['path'])
        command(['docker', 'info', '--format', '{{json .}}'], output / 'docker_info.json', 30)
        state['stage'] = 'image_build'; save()
        for side, image in [('agent', agent), ('verifier', judge)]:
            command(['docker', 'build', '--network', args.build_network, '-t', image, str(task / 'environment' / side)],
                    output / (side + '_build.log'), 2400)
        for side, image in [('agent', agent), ('verifier', judge)]:
            state[side + '_image_id'] = subprocess.check_output(
                ['docker', 'image', 'inspect', '--format', '{{.Id}}', image], text=True).strip()
        reference = output / 'reference'; reference.mkdir()
        empty = output / 'empty'; empty.mkdir()
        starter = task / 'public' / 'repo' / 'restler'
        state['stage'] = 'reference_materialization'; save()
        container(['--network', 'none', '--read-only', '--tmpfs', '/tmp:rw,exec,size=1g',
                   '--memory', '4g', '--cpus', '2', '--cap-drop', 'ALL',
                   '--mount', f'type=bind,source={task / "solution"},target=/solution,readonly',
                   '--mount', f'type=bind,source={reference},target=/out',
                   '--entrypoint', '/opt/runtime/venv/bin/python', state['agent_image_id'],
                   '/solution/solve.py', '--public', '/opt/public', '--output', '/out'],
                  'edge-raymone-reference-' + token, output / 'reference.log', 120)
        state['stage'] = 'grading'; save()
        for label, submission, suite in [('reference_public', reference, 'public'),
                                         ('reference_feedback', reference, 'feedback'),
                                         ('reference_audit', reference, 'audit'),
                                         ('starter_feedback', starter, 'feedback'),
                                         ('empty_feedback', empty, 'feedback')]:
            name = 'edge-raymone-' + token + '-' + label
            log = output / (label + '.json')
            container(['--network', 'none', '--read-only', '--tmpfs', '/tmp:rw,exec,size=12g',
                       '--memory', '12g', '--cpus', '2', '--pids-limit', '512',
                       '--cap-drop', 'ALL', '--cap-add', 'SYS_ADMIN',
                       '--security-opt', 'seccomp=unconfined', '--security-opt', 'apparmor=unconfined',
                       '--mount', f'type=bind,source={submission},target=/submission,readonly',
                       state['verifier_image_id'], '--submission', '/submission', '--suite', suite],
                      name, log, 900)
            report = json.loads(log.read_text())
            if report.get('status') != 'scored' or type(report.get('valid')) != bool:
                raise ValueError('invalid feedback schema: ' + label)
            if not isinstance(report.get('checks'), list) or not report['checks']:
                raise ValueError('missing named checks: ' + label)
            state['reports'][label] = report; save()
        positive = state['reports']['reference_feedback']
        negative = state['reports']['empty_feedback']
        state['reference_has_positive_score'] = positive['valid'] and positive['score'] > 0
        state['empty_rejected'] = negative['valid'] is False and negative['score'] == 0
        state['reference_all_suites_full_score'] = all(
            state['reports'][label]['valid'] and abs(state['reports'][label]['score'] - 1) < 1e-12
            for label in ['reference_public', 'reference_feedback', 'reference_audit'])
        state['status'] = 'smoke_completed' if state['reference_all_suites_full_score'] and state['empty_rejected'] else 'needs_repair'
        state['scope'] = 'Direct Docker reference/public/feedback/audit, unchanged starter and empty controls. No native Harbor, isolation audit, determinism or six-hour claim. Current local empty-submission valid=false semantics still need Harbor alignment.'
    except Exception as error:
        state['status'] = 'failed'
        state['error'] = f'{type(error).__name__}: {error}'
        raise
    finally:
        state['finished_unix'] = time.time(); save()


if __name__ == '__main__':
    main()
