"""Freeze the explicitly added raymone/4..6 program package separately."""
from pathlib import Path
import hashlib
import json
import shutil
import subprocess

from build_packages import ROOT, dump

source = ROOT / 'framework'
target = ROOT / 'framework-raymone456'
subprocess.run(['cp', '-a', '--reflink=auto', str(source), str(target)], check=True)
package_source = Path('/ws/users/wcgu/new-codex-group/raymone/4/bin/codex').resolve().parent.parent
expected = '76a9d2cc570a9be1386e00040891ca3829d33488ad9f26dcf35dcd7e339eda30'
shutil.rmtree(target / 'codex-static-package')
shutil.copytree(package_source, target / 'codex-static-package')
package = target / 'codex-static-package'
assert not any(p.is_symlink() or p.name in ['auth.json', 'static-egress.json', 'config.toml']
               for p in package.rglob('*'))
hashes = {p.relative_to(package).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
          for p in package.rglob('*') if p.is_file()}
assert hashes['bin/codex'] == expected
assert {'bin/codex-code-mode-host', 'codex-path/rg', 'codex-resources/bwrap', 'codex-package.json'} <= hashes.keys()
locks = {}
for n in ['4', '5', '6']:
    home = Path('/ws/users/wcgu/new-codex-group/raymone') / n
    assert hashlib.sha256((home / 'bin/codex').read_bytes()).hexdigest() == expected
    assert (home / 'auth.json').is_file()
    binding = json.loads((home / 'static-egress.json').read_text())
    locks['raymone/' + n] = {k: binding[k] for k in ['host', 'http_port', 'socks_port', 'expected_exit_ip']}
dump(target / 'selected-account-bindings.json', locks)
path = target / 'edgebench_harbor/static_native.py'
text = path.read_text().replace('2a4ec9fb603d1f9deb487644f394d486024d323d14920a6c908c96332b3fca37', expected)
text = text.replace("['1', '2', '3']", "['4', '5', '6']")
path.write_text(text)
manifest_path = target / 'toolchain-manifest.json'
manifest = json.loads(manifest_path.read_text())
for entry in manifest.values():
    entry.update(codex_binary=str(package / 'bin/codex'), codex_sha256=expected,
                 codex_code_mode_host=str(package / 'bin/codex-code-mode-host'),
                 codex_code_mode_host_sha256=hashes['bin/codex-code-mode-host'],
                 codex_package_root=str(package), codex_package_hashes=hashes,
                 codex_package_tree_sha256=hashlib.sha256(json.dumps(hashes, sort_keys=True).encode()).hexdigest())
dump(manifest_path, manifest)
components = ['edgebench_harbor/package_scorer.py', 'edgebench_harbor/native_controls_runtime.py',
              'edgebench_harbor/cloud.py', 'edgebench_harbor/official_supervision.py',
              'edgebench_harbor/official_cloud_supervision.py', 'harbor/agents/installed/codex.py']
same = {}
for name in components:
    before = hashlib.sha256((source / name).read_bytes()).hexdigest()
    after = hashlib.sha256((target / name).read_bytes()).hexdigest()
    assert before == after
    same[name] = after
files = {p.relative_to(target).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
         for p in target.rglob('*') if p.is_file() and '__pycache__' not in p.parts
         and p.name != 'framework-version.json'}
dump(target / 'framework-version.json', {'status': 'frozen', 'kind': 'six_hour_engineering_pilot',
    'formal_acceptance': False, 'runtime_file_hashes': files,
    'runtime_tree_sha256': hashlib.sha256(json.dumps(files, sort_keys=True).encode()).hexdigest(),
    'source': str(source), 'authorized_accounts': ['raymone/4', 'raymone/5', 'raymone/6']})
dump(ROOT / 'additional-accounts.json', {'homes': ['/ws/users/wcgu/new-codex-group/raymone/' + n for n in ['4', '5', '6']],
    'authorization': 'user added raymone-04, raymone-05, raymone-06', 'actual_cli_sha256': expected,
    'program_package_source': str(package_source), 'program_package_files': len(hashes),
    'frozen_framework': str(target), 'unchanged_score_and_supervision_components': same,
    'real_model_admission': 'not_yet_run', 'model_runs_started': 0,
    'reason': 'Cloud account total-memory quota currently exhausted; login file presence is not live model validation'})
print('EXTRA_ACCOUNTS_PACKAGE_PREPARED', len(hashes), flush=True)
