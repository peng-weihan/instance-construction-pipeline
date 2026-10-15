"""One six-hour official-Codex Aliyun learner, with an offline authored judge."""
from pathlib import Path
import datetime
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import tomllib

from build_packages import ROOT, dump, inventory

KEY, ACCOUNT_NAME = sys.argv[1:3]
PILOT = ROOT / KEY
F = ROOT / 'framework'
ACCOUNT = Path('/ws/users/wcgu/new-codex-group') / ACCOUNT_NAME
sys.path[:0] = [str(F), str(F / 'sdk')]
import toml
from launcher_support import configure
from harbor.models.task.config import TaskConfig, NetworkMode, VerifierEnvironmentMode
from edgebench_harbor.static_native import selected_binding, configure_native_transport
from edgebench_harbor.grading_budget import host_outer_budget


def main():
    lifetime = configure(F)
    controls = json.loads((PILOT / 'scorer-controls.json').read_text())
    native = json.loads((PILOT / 'native-controls/report.json').read_text())
    assert all(native['results'].get(x, {}).get('passed') for x in ['oracle', 'nop'])
    admission = json.loads((PILOT / 'admission/report.json').read_text())
    frozen = json.loads((F / 'framework-version.json').read_text())
    assert controls['passed'] and admission['passed']
    identity = selected_binding(ACCOUNT)
    assert admission['selected_native_identity']['account'] == identity['account'] == ACCOUNT_NAME
    assert admission['cli_sha256'] == identity['cli_sha256']
    files = {p.relative_to(F).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
             for p in F.rglob('*') if p.is_file() and '__pycache__' not in p.parts
             and p.name != 'framework-version.json'}
    assert files == frozen['runtime_file_hashes']
    assert admission['runtime_tree_sha256'] == frozen['runtime_tree_sha256']
    task = PILOT / 'task'
    assert inventory(task) == controls['task_hashes']
    assert inventory(task / 'environment') == admission['cloud_context_file_hashes']
    images = json.loads((PILOT / 'images.json').read_text())
    assert images['verifier']['image_id'] == controls['image_id']
    out = PILOT / 'run-6h-001'
    out.mkdir(mode=0o700, exist_ok=False)
    snapshot = out / 'task'
    shutil.copytree(task, snapshot)
    profile = json.loads((task / 'pipeline-profile.json').read_text())
    cfg = TaskConfig.model_validate_toml((snapshot / 'task.toml').read_text())
    hosts = [identity['proxy_ip'], 'chatgpt.com', 'api.ipify.org']
    cfg.environment.network_mode = NetworkMode.ALLOWLIST
    cfg.environment.allowed_hosts = hosts
    cfg.agent.network_mode = NetworkMode.ALLOWLIST
    cfg.agent.allowed_hosts = hosts
    cfg.agent.user = 'agent'
    cfg.agent.timeout_sec = host_outer_budget(21600, 600, 120, profile['grading_workers'], profile['verifier_timeout_sec'])
    cfg.verifier.environment_mode = VerifierEnvironmentMode.SHARED
    cfg.verifier.environment = None
    cfg.verifier.network_mode = NetworkMode.ALLOWLIST
    cfg.verifier.allowed_hosts = hosts
    (snapshot / 'task.toml').write_text(cfg.model_dump_toml())
    ipc = out / 'ipc'
    ipc.mkdir(mode=0o700)
    dump(ipc / 'public.json', {'artifacts': profile['artifacts'],
        'snapshot_limit_bytes': 128000000, 'response_timeout_sec': 3600})
    toolchain = json.loads(Path(os.environ['TBSCI_TOOLCHAIN_MANIFEST']).read_text())['codex']
    protocol = {**profile, 'backend': 'aliyun-learner-docker-verifier',
        'budget_sec': 21600, 'interval_sec': 600, 'ipc_host': str(ipc),
        'controller_root': str(out / 'evaluation'), 'docker_task_dir': str(snapshot),
        'verifier_image': images['verifier']['image_id'], 'selected_codex_home': str(ACCOUNT),
        'codex_static_package': toolchain['codex_package_hashes'], 'runtime_max_outage_sec': 600}
    dump(out / 'protocol.json', protocol)
    config = configure_native_transport(tomllib.loads((ACCOUNT / 'config.toml').read_text()), 'responses-websocket')
    config.update(model='gpt-6.1-sol', model_reasoning_effort='high', web_search='disabled',
        mcp_servers={}, approval_policy='never', sandbox_mode='danger-full-access')
    config.pop('sandbox_workspace_write', None)
    config.setdefault('features', {}).update(apps=False, hooks=False, multi_agent=False)
    config.get('shell_environment_policy', {}).get('set', {}).pop('CODEX_HOME', None)
    with tempfile.TemporaryDirectory(prefix='raymone-swe-roll-config-') as temp:
        conf = Path(temp) / 'config.toml'
        conf.write_text(toml.dumps(config))
        conf.chmod(0o600)
        command = [sys.executable, str(F / 'harbor_entry.py'), 'run', '--path', str(snapshot),
            '--env', 'edgebench_harbor.official_cloud_supervision:SupervisedOfficialCodexCloudEnvironment',
            '--ek', 'selected_codex_home=' + str(ACCOUNT), '--ek', 'cloud_context=' + str(snapshot / 'environment'),
            '--ek', 'protocol=' + str(out / 'protocol.json'), '--agent', 'codex', '--model', 'gpt-6.1-sol',
            '--ak', 'version=0.160.0', '--ak', 'reasoning_effort=high', '--ak', 'web_search=disabled',
            '--ak', 'config=' + str(conf), '--verifier', 'edgebench_harbor.verifier:BestSubmissionVerifier',
            '--verifier-kwarg', 'controller_root=' + str(out / 'evaluation'),
            '--jobs-dir', str(out / 'jobs'), '--job-name', 'trial', '--n-concurrent', '1',
            '--n-attempts', '1', '--max-retries', '0', '--yes']
        env = {k: v for k, v in os.environ.items() if not k.startswith(('OPENAI_', 'CODEX_', 'AZURE_', 'ANTHROPIC_'))}
        env['CODEX_AUTH_JSON_PATH'] = str(ACCOUNT / 'auth.json')
        record = {'kind': 'six_hour_engineering_pilot', 'formal_acceptance': False,
            'task': KEY, 'model': 'gpt-6.1-sol', 'reasoning_effort': 'high', 'account': ACCOUNT_NAME,
            'runtime_tree_sha256': frozen['runtime_tree_sha256'], 'task_hashes': inventory(task),
            'learning_budget_seconds': 21600, 'evaluation_interval_seconds': 600,
            'difficulty_early_stop': False, 'backend': 'Aliyun learner + offline Docker verifier',
            'cli_sha256': identity['cli_sha256'], 'command': command, 'status': 'starting',
            'started_utc': datetime.datetime.now(datetime.timezone.utc).isoformat()}
        dump(out / 'run-manifest.json', record)
        with (out / 'console.log').open('wb') as log:
            process = subprocess.Popen(command, env=env, stdout=log, stderr=subprocess.STDOUT,
                stdin=subprocess.DEVNULL, start_new_session=True)
            record.update(status='host_harbor_started', pid=process.pid,
                host_start_ticks=Path('/proc', str(process.pid), 'stat').read_text().rsplit(')', 1)[1].split()[19])
            dump(out / 'run-manifest.json', record)
            code = process.wait()
        record.update(status='host_finished', exit_code=code,
            finished_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
        dump(out / 'run-manifest.json', record)
    return code


if __name__ == '__main__':
    raise SystemExit(main())
