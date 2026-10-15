"""Run the authored authoritative test.sh in a fresh, offline, private judge."""
import asyncio
import json
import math
import time
import uuid
from pathlib import Path


class DockerScorer:
    def __init__(self, task_dir, image, timeout_sec=1200):
        self.task_dir = Path(task_dir)
        self.image = image
        self.timeout_sec = timeout_sec
        self.job_wall_timeout_sec = timeout_sec + 120
        self.profile = json.loads((self.task_dir / 'pipeline-profile.json').read_text())
        if not image.startswith('sha256:'):
            raise ValueError('immutable judge image ID required')

    async def grade(self, snapshot, folder):
        folder = Path(folder)
        folder.mkdir(parents=True, exist_ok=True)
        source = Path(snapshot) / self.profile['submission_root'].lstrip('/')
        if not source.is_dir():
            source = folder / 'empty-submission'
            source.mkdir()
        logs = folder / 'verifier'
        logs.mkdir()
        logs.chmod(0o700)
        name = 'edge-raymone-swe-judge-' + uuid.uuid4().hex[:12]
        argv = ['docker', 'run', '--rm', '--name', name, '--network', 'none',
                '--cpus', '2', '--memory', str(self.profile['judge_memory_mb']) + 'm',
                '--pids-limit', '512', '--cap-drop', 'ALL', '--user', '0:0']
        if not self.profile.get('judge_writable_root', False):
            argv.append('--read-only')
        for cap in ['SETUID', 'SETGID', 'CHOWN', 'DAC_OVERRIDE', 'FOWNER', 'KILL']:
            argv += ['--cap-add', cap]
        for path in ['/tmp', '/work', '/candidate-builds', '/candidate-runs']:
            argv += ['--tmpfs', path + ':rw,exec,size=2g,mode=1777']
        argv += ['--mount', f'type=bind,source={source.resolve()},target={self.profile["submission_root"]},readonly',
                 '--mount', f'type=bind,source={logs.resolve()},target=/logs/verifier',
                 '--entrypoint', '/bin/sh', self.image, '/tests/test.sh']
        began = time.monotonic()
        proc = None
        try:
            proc = await asyncio.create_subprocess_exec(*argv, stdout=asyncio.subprocess.PIPE,
                                                       stderr=asyncio.subprocess.PIPE)
            out, err = await asyncio.wait_for(proc.communicate(), self.timeout_sec)
            (folder / 'test-stdout.txt').write_bytes(out)
            (folder / 'test-stderr.txt').write_bytes(err)
            (folder / 'execution.json').write_text(json.dumps({'command': argv,
                'exit_code': proc.returncode, 'elapsed_seconds': time.monotonic() - began}, indent=2))
            if not (logs / 'score.json').exists() or not (logs / 'reward.txt').exists():
                raise RuntimeError('judge did not produce score and reward; private logs retained')
            raw = json.loads((logs / 'score.json').read_text())
            reward = float((logs / 'reward.txt').read_text())
            if (raw.get('valid') is not True or not math.isfinite(reward)
                    or not 0 <= reward <= 1 or reward != raw.get('score')):
                raise RuntimeError('invalid judge observation or reward mismatch; no zero substituted')
            checks = raw.get('checks', [])
            if isinstance(checks, dict):
                checks = [{'name': k, **(v if isinstance(v, dict) else {'passed': v})}
                          for k, v in checks.items()]
            normalized_checks = []
            for c in checks:
                if isinstance(c, dict):
                    passed = c.get('passed', c.get('pass', c.get('status') == 'pass'))
                    normalized_checks.append({**c, 'passed': bool(passed)})
            pass_rate = raw.get('pass_rate')
            if not isinstance(pass_rate, (int, float)):
                pass_rate = (sum(c['passed'] for c in normalized_checks) / len(normalized_checks)
                             if normalized_checks else 0.0)
            # Shape-only adaptation. The author's numerical score/reward stays authoritative.
            report = {**raw, 'status': 'scored', 'score': reward, 'valid': True,
                      'pass_rate': pass_rate, 'checks': normalized_checks,
                      'failed_checks': raw.get('failed_checks', [c.get('name', 'unnamed')
                          for c in normalized_checks if not c['passed']]),
                      'raw_metrics': raw.get('raw_metrics', {'author_score': raw['score']}),
                      'summary': raw.get('summary', 'Authoritative task checks completed')}
            (folder / 'feedback.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
            return report, time.monotonic() - began
        finally:
            clean = await asyncio.create_subprocess_exec('docker', 'rm', '-f', name,
                       stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL)
            await clean.wait()
            if proc is not None and proc.returncode is None:
                proc.kill()
                await proc.wait()
