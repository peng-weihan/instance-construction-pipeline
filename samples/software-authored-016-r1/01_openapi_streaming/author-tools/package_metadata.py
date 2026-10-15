from pathlib import Path
import json,hashlib,difflib,shutil,datetime
r=Path(__file__).resolve().parents[1];task=r/'task';author=task/'authoring'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
source=json.loads((r/'material-src/manifest.json').read_text());branch=json.loads((r/'evidence/reference-branch.json').read_text());frozen=json.loads((r/'evidence/frozen/results.json').read_text())
assert len(frozen)==9 and all(x['valid'] for x in frozen)
assert all(x['score']==1.0 for x in frozen[:5]);assert len(set(x['grader_sha256'] for x in frozen))==1
assert all(x['grader_sha256']==sha(task/'tests/grader.py') for x in frozen)
controls=author/'controls';controls.mkdir(exist_ok=True)
control_records=[]
start=task/'environment/submission'
for name in ['cheap','no_auth_override','eager']:
 data=[];root=r/'controls'/name
 for p in sorted(root.rglob('*')):
  if not p.is_file() or any(x in p.parts for x in ['__pycache__','.ruff_cache','.pytest_cache','.mypy_cache']):continue
  relative=p.relative_to(root);original=start/relative
  if original.exists() and original.read_bytes()==p.read_bytes():continue
  data.extend(difflib.unified_diff(original.read_text().splitlines(keepends=True) if original.exists() else [],p.read_text().splitlines(keepends=True),fromfile='a/'+str(relative) if original.exists() else '/dev/null',tofile='b/'+str(relative)))
 patch=controls/(name+'.patch');patch.write_text(''.join(data))
 actual=next(x for x in frozen if x['name']==name)
 control_records.append({'name':name,'base':'../../environment/submission','patch':patch.name,'patch_sha256':sha(patch),'observed_score':actual['score'],'observed_passed':actual['passed'],'expected_direction':'below full reference; preserve meaningful passing dimensions','evidence':f'../control-evidence/{name}/score.json'})
control_records += [{'name':'nop','source':'../../environment/submission','observed_score':next(x['score'] for x in frozen if x['name']=='nop'),'expected_direction':'native regression floor, streaming checks fail'},{'name':'reference','source':'../../solution/reference','branch_commit':branch['reference_commit'],'observed_scores':[x['score'] for x in frozen[:5]],'expected_direction':'declared ordinary oracle upper bound 1'}]
(controls/'controls.json').write_text(json.dumps(control_records,indent=2)+'\n')
for item in frozen:
 dest=author/'control-evidence'/item['name'];dest.mkdir(parents=True,exist_ok=True)
 for filename in ['score.json','traces.json','reward.txt']:shutil.copyfile(r/item['evidence']/filename,dest/filename)
(author/'frozen-replay-results.json').write_text(json.dumps(frozen,indent=2)+'\n')
shutil.copyfile(r/'material-src/manifest.json',author/'source-manifest.json')
shutil.copyfile('/ws/users/raymone/edgebench/swe-authoring-016-20261015-r1/guidance/python-3.12.8-image-pin.json',author/'python-image-pin.json')
provenance={
 'id':'openapi-streaming-contexts','authoring_method':'original engineering evolution on fixed upstream; new contract and independent observable probes','source':{'url':source['repository'],'revision':source['revision'],'license':'MIT','license_sha256':source['license_sha256'],'tracked_files':source['tracked_files'],'full_checkout':'../../material-src/openapi-python-client','sha256_inventory':'source-manifest.json'},'reference':branch,
 'inputs':{'card':'01_openapi_streaming.md from supplied batch inputs','source_manifest':'01_openapi_streaming/manifest.json from supplied batch inputs','batch_report':'inputs/REPORT.md','guidance':['factory-methods.md','package-contract.md','source-selection.md','material-and-scoring.md','reference-anchors.md','harbor-0.23.0-task-config.py']},
 'model':{'requested':'gpt-6.1-sol','parent_status_recorded':'gpt-6.1-sol','evidence':'../../status.json','additional_model_sessions_started':0,'subagents_started':0},
 'transformation':{'public_starter':'full upstream tracked tree unchanged','reference_changed_files':branch['changed_files'],'new_assets':['original OpenAPI fixture','root HTTP observer','unprivileged SDK exerciser','semantic grouped grader','packaging and controls'],'existing_upstream_features_reused':['httpx.iter_lines/aiter_lines','model conversion','client injection','multipart file arrays']},
 'leakage_split':{'work_context':'environment only: public upstream, public schema and smoke, baseline wheel','judge_context':'verifier only: root expectations/native regressions/reference patch, immutable test harness','oracle_injection':'solution/reference, separate from work image','author_audit':'authoring/control-evidence plus job evidence; absent work image'},
 'trajectory':'../../trajectory.jsonl retained by parent, contents not rewritten','teacher_rollouts_started':0,'edgebench_original_hidden_tests_used':False}
(author/'provenance.json').write_text(json.dumps(provenance,indent=2)+'\n')
build={'base':json.loads((author/'python-image-pin.json').read_text()),'toolchain':'CPython 3.12; local checks on 3.12.3; pinned container would use 3.12.8','images_built':False,'arm_runtime_verified':False,'container_runtime_verified':False,'network':{'agent':'no-network','verifier':'no-network','build_dependency_install':'offline --no-index --require-hashes; initial immutable base-image pull may require registry access'},'contexts':{},'source':{'baseline':source['revision'],'reference':branch['reference_commit']},'dependency_manifest':'dependency-manifest.json','project_wheel':{'origin_revision':source['revision'],'filename':'openapi_python_client-0.29.1-py3-none-any.whl','sha256':sha(task/'environment/wheelhouse/openapi_python_client-0.29.1-py3-none-any.whl')},'docker_build_commands':['docker build --network=none -f environment/Dockerfile -t edgebench-openapi-streaming-work:1.0.0-draft environment','docker build --network=none -f verifier/Dockerfile -t edgebench-openapi-streaming-judge:1.0.0-draft verifier'],'build_commands_executed':False,'native_entry':'/tests/test.sh -> /opt/venv/bin/python -I /tests/grader.py','tests_copies_match':True}
for name in ['environment','verifier']:
 context=task/name;files=[p for p in sorted(context.rglob('*')) if p.is_file()]
 build['contexts'][name]={'path':name,'dockerfile':name+'/Dockerfile','file_count':len(files),'bytes':sum(p.stat().st_size for p in files),'self_contained':True,'files':[{'path':str(p.relative_to(context)),'bytes':p.stat().st_size,'sha256':sha(p)} for p in files]}
(author/'build-manifest.json').write_text(json.dumps(build,indent=2)+'\n')
# Explicitly freeze the authoritative test/spec inputs used by the same-snapshot replay.
(author/'grading-freeze.json').write_text(json.dumps({'grader_sha256':sha(task/'tests/grader.py'),'worker_sha256':sha(task/'tests/worker.py'),'score_spec_sha256':sha(author/'score-spec.json'),'private_integrity_sha256':sha(task/'verifier/private/integrity.json'),'reference_patch_sha256':sha(task/'solution/reference.patch'),'reference_source_manifest':[{'path':str(p.relative_to(task/'solution/reference')),'sha256':sha(p)} for p in sorted((task/'solution/reference').rglob('*')) if p.is_file()],'control_replay_results':'frozen-replay-results.json'},indent=2)+'\n')
print('self-contained contexts and frozen controls inventoried')
