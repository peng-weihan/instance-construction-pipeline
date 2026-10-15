"""Install only our new five-route batch; never mutate old author jobs or skills."""
from pathlib import Path
import json
import shutil
import sys

ROOT = Path(sys.argv[1]).resolve()
OLD = Path('/ws/users/raymone/edgebench/swe-authoring-016-20261015-r1')
guidance = ROOT / 'guidance'; guidance.mkdir(exist_ok=False)
for name in ['deepswe.md', 'programbench.md', 'nl2repo.md']:
    dst = guidance / 'factory-original' / name; dst.parent.mkdir(exist_ok=True)
    shutil.copyfile(ROOT / 'incoming-factory' / name, dst)
for name in ['harbor-0.23.0-task-config.py', 'python-3.12.8-image-pin.json', 'python-3.12.8-manifest-index.json']:
    shutil.copyfile(OLD / 'guidance' / name, guidance / name)
for src, dst in [
    ('/ws/users/wcgu/skills/edgebench-task-authoring', 'authoring-skill'),
    ('/ws/users/wcgu/task-qc', 'task-qc-skill')]:
    # Copy just instructions/references, never task data, credentials or programs.
    source = Path(src); target = guidance / dst; target.mkdir()
    shutil.copyfile(source / 'SKILL.md', target / 'SKILL.md')
    shutil.copytree(source / 'references', target / 'references')
incoming = ROOT / 'incoming-guidance'
for p in incoming.iterdir(): shutil.copyfile(p, guidance / p.name)
for job in json.loads((ROOT / 'launch-plan.json').read_text())['jobs']:
    p = Path(job['cwd']) / 'prompt.md'
    p.write_text(p.read_text() + f'''

已部署指导与控制器：
- {guidance}/original-task-scale-review.md：上一轮8题逐题审查与原题规模对照。
- {guidance}/scope-requirements.md：用户本轮工程量要求。
- {guidance}/factory-original：三个factory原始规约；其余guidance含规范与实际Harbor schema快照。
- 执行静态检查：PYTHONPATH={ROOT}/controller python3 -m edge_factory.swe gate --job {job['cwd']} --output {job['cwd']}/STATIC_ADMISSION.json
这个gate只校验本地材料/报告一致性；它不能验证难度、真实执行或完整Harbor运行，结果不得写accepted。
输出源码/依赖/原生控制的实际记录，不追求快速交一个薄题。可以用普通构建测试子进程，不得再开模型/CLI agent/子代理。
完整真实任务构造优先于泛泛计划；实测不能闭合时明确held，不编造性能分。保留全部失败和原始分母。
''')
    job['prompt_sha256'] = __import__('hashlib').sha256(p.read_bytes()).hexdigest()
plan = json.loads((ROOT / 'launch-plan.json').read_text())
for job in plan['jobs']:
    job['prompt_sha256'] = __import__('hashlib').sha256((Path(job['cwd']) / 'prompt.md').read_bytes()).hexdigest()
(ROOT / 'launch-plan.json').write_text(json.dumps(plan, ensure_ascii=False, indent=2) + '\n')
print('Installed five new independent author jobs; old jobs/skills untouched.')
