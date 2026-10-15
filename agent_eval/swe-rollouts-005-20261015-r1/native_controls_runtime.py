"""No-inference Harbor control instances; private containers, no host mounts."""
import hashlib
import json
import shlex
import uuid
from pathlib import Path

from harbor.models.task.config import NetworkMode
from harbor.models.verifier.result import VerifierResult
from harbor.verifier.base import BaseVerifier
from .docker_runtime import EdgeBenchDockerEnvironment, call, CAPS


class PackageControlEnvironment(EdgeBenchDockerEnvironment):
    def _validate_definition(self):
        if not self.task_env_config.docker_image.startswith('sha256:'):
            raise ValueError('Native controls require a frozen image')
        if self.network_policy.network_mode != NetworkMode.NO_NETWORK:
            raise ValueError('No model/network permitted in native controls')

    async def start(self, force_build=False):
        try:
            args = ['docker', 'create', '--name', self.name, '--network', 'none',
                    '--cpus', str(self.task_env_config.cpus), '--memory', str(self.task_env_config.memory_mb) + 'm',
                    '--pids-limit', '512', '--cap-drop', 'ALL', '--user', 'root']
            for cap in CAPS:
                args += ['--cap-add', cap]
            args += ['--entrypoint', '/bin/sh', self.task_env_config.docker_image,
                     '-c', 'exec sleep infinity']
            await call(args)
            self.evidence.update(created=True, image_id=self.task_env_config.docker_image,
                                 network='none', inference_allowed=False, host_mounts=[])
            self.save()
            await call(['docker', 'start', self.name])
            await self.checked('mkdir -p /logs/agent /logs/verifier /logs/artifacts /artifacts; chmod 700 /logs/verifier')
        except BaseException:
            await self.stop()
            raise

    async def stop(self, delete=True):
        await call(['docker', 'rm', '-f', self.name], check=False)
        result = await call(['docker', 'inspect', self.name], check=False)
        self.evidence['destroyed'] = result.return_code != 0 and 'no such object' in result.stderr.lower()
        self.evidence['owned_disk_removed'] = self.evidence['destroyed']
        self.save()
        if not self.evidence['destroyed']:
            raise RuntimeError('Own native-control container absence not confirmed')


class PackageNativeVerifier(BaseVerifier):
    async def verify(self):
        profile = json.loads((self.task.paths.task_dir / 'pipeline-profile.json').read_text())
        root = profile['submission_root']
        code = ('from pathlib import Path;import hashlib,json;r=Path(' + repr(root) + ');'
                'print(json.dumps({p.relative_to(r).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() '
                'for p in r.rglob("*") if p.is_file()}))')
        result = await self.environment.checked('/usr/local/bin/python3 -I -c ' + shlex.quote(code))
        hashes = json.loads(result.stdout)
        result = await self.environment.exec('/bin/sh /tests/test.sh', user='root', cwd='/',
                                              timeout_sec=self.task.config.verifier.timeout_sec)
        target = self.trial_paths.verifier_dir
        target.mkdir(parents=True, exist_ok=True)
        self.trial_paths.test_stdout_path.write_text(result.stdout or '')
        (target / 'test-stderr.txt').write_text(result.stderr or '')
        await self.environment.download_dir('/logs/verifier', target)
        report = json.loads((target / 'score.json').read_text())
        reward = float((target / 'reward.txt').read_text())
        if report.get('valid') is not True or not 0 <= reward <= 1 or reward != report.get('score'):
            raise RuntimeError('Native score/reward invalid or mismatched')
        (target / 'actual-input-and-entry.json').write_text(json.dumps({
            'candidate_hashes': hashes, 'authoritative_entry': '/tests/test.sh',
            'actual_exit_code': result.return_code, 'reward': reward}, indent=2))
        return VerifierResult(rewards={'reward': reward})
