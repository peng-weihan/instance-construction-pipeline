from pathlib import Path
import json,shutil
ROOT=Path(__file__).resolve().parents[2];src=ROOT/'samples/remaining-three-built-001/finance-task-r3';dst=src.with_name('finance-task-r4');shutil.copytree(src,dst)
for folder in ['verifier','environment/verifier/verifier']:
 p=dst/folder/'grader.py';text=p.read_text()
 old="    with workdir() as tmp:\n        work=Path(tmp);snapshot(submission,work/'submission');shutil.copyfile(ROOT/'verifier/policy_worker.py',work/'policy_worker.py')\n        for case in cases:\n"
 new="    for case in cases:\n        with workdir() as tmp:\n            work=Path(tmp);snapshot(submission,work/'submission');shutil.copyfile(ROOT/'verifier/policy_worker.py',work/'policy_worker.py')\n"
 assert old in text;text=text.replace(old,new);p.write_text(text)
note='\n每个年度/成本配置都使用全新的策略进程及独立可写工作目录；一个配置写入的缓存不会进入另一配置。一个配置内可以通过user_state或临时文件保留跨交易日状态。正式评分只使用提交快照，每次调用全部重置。\n'
for p in [dst/'instruction.md',dst/'public/instruction.md',dst/'environment/agent/public/instruction.md',dst/'environment/verifier/public/instruction.md']:p.write_text(p.read_text()+note)
(dst/'REVISION.json').write_text(json.dumps({'previous_revision':'finance-task-r3','fix':'fresh writable directory and snapshot for every independent historical configuration',
 'cause':'actual old-image two-worker probe observed a file from the previous episode',
 'score_formula_constants_and_prices_unchanged':True,'requires_new_six_hour_run':True},indent=2)+'\n')
print(dst)
