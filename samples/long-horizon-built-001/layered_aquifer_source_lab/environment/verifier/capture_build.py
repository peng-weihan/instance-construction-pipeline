"""Record actual dependency versions during an explicitly requested image build."""
import hashlib,json,subprocess
from pathlib import Path
record={'python':subprocess.check_output(['python','--version'],text=True).strip(),
        'pip':subprocess.check_output(['python','-m','pip','freeze'],text=True).splitlines(),
        'debian_packages':subprocess.check_output(['dpkg-query','-W','-f=${Package}=${Version}\n'],text=True).splitlines(),
        'dependency_git_revisions':{}}
for git in Path('/opt/runtime').rglob('.git'):
    if git.is_dir():
        p=git.parent
        record['dependency_git_revisions'][str(p)]=subprocess.check_output(['git','-C',str(p),'rev-parse','HEAD'],text=True).strip()
Path('/opt/runtime/build_manifest.json').write_text(json.dumps(record,indent=2)+'\n')
