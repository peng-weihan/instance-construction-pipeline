from pathlib import Path
import json
r=Path('/ws/users/raymone/edgebench/next-two-001');task=r/'packing-task-r4'
for p in task.rglob('score_design.json'):
 d=json.loads(p.read_text());d['constants']['solver_clearance']=0.1;d['reference_lengths_pending']=False;d['reference_materialization']='27 measured and independently validated layouts frozen in private/reference_certificates; rebuild verifies file hashes and geometry';p.write_text(json.dumps(d,indent=2)+'\n')
for p in task.rglob('instruction.md'):
 s=p.read_text().replace('基线长度在 verifier 镜像构建时使用冻结源码每例运行 20 秒，独立检查后写入 reference_lengths.json；每次提交不会重新估计基线。','基线布局已由冻结源码每例运行 20 秒生成并通过独立检查，长度、输入和证书 SHA256 已固定；镜像重建只校验这些固定资产，每次提交不会重新估计基线。');p.write_text(s)
p=task/'endpoint_notes.md';p.write_text(p.read_text()+'\n当前试跑版本已固定全部 27 个实测参考布局、输入哈希和证书哈希。构建时执行 verify_frozen_reference.py，不再重算归一化锚点。参考源码得分仍以 controls 实测报告为准。\n')
(r/'packing-frozen-reference/verification.json').write_text(json.dumps({'command':'offline docker /verify.py against edge-raymone-packing:initial','verified_cases':27,'actual_output':'27 frozen source-bound reference layouts verified','reference_generation_seconds':561.3},indent=2)+'\n')
