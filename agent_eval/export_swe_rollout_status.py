"""Read-only task/trace/queue summaries; do not export secrets or trajectory bodies."""
from pathlib import Path
import collections
import datetime
import json
import os
import re

BASE=Path('/ws/users/raymone/edgebench')
BATCHES={
    'swe-rollouts-003-20261015-r4':['02_restler_recovery','04_pytest_fixtures','09_valkey_transactions'],
    'swe-rollouts-002-20261015-r6':['01_openapi_streaming','03_httpx_transport'],
    'swe-rollouts-005-20261015-r5':['18_polars_streaming','19_ruff_project_analysis','20_libcst_project_migration','21_coverage_context_merge','22_sphinx_incremental_build'],
}

def read(p,default=None):
    try:return json.loads(p.read_text())
    except (OSError,ValueError):return default

def alive(pid,ticks=None):
    try:
        s=Path('/proc',str(pid),'stat').read_text().rsplit(')',1)[1].split()
        return s[0]!='Z' and (ticks is None or s[19]==str(ticks))
    except (OSError,ValueError):return False

def main():
    now=datetime.datetime.now(datetime.timezone.utc)
    result={'observed_utc':now.isoformat(),'model':'gpt-6.1-sol','learning_budget_seconds':21600,
        'grading_interval_seconds':600,'difficulty_early_stop':False,'tasks':[],'queues':[],
        'first_attempt_startup_failure':'r2 missing strace; zero native model turns; own instances stopped and removed',
        'not_queued_for_current_contract':['10_datafusion_sort','12_croaring_kernels','14_tree_sitter_incremental']}
    for batch,keys in BATCHES.items():
        root=BASE/batch
        q=read(root/'ready-queue-status.json')
        if q:result['queues'].append({'batch':batch,**q,'actual_queue_process_alive':alive(q.get('queue_pid'))})
        for key in keys:
            p=root/key
            row={'task':key,'batch':batch,'path':str(p),'phase':'waiting_preparation'}
            state=read(p/'prepare-status.json',{})
            if state:row.update(phase=state.get('phase'),preparation_error=state.get('error'))
            controls=read(p/'scorer-controls.json',{})
            row['periodic_controls_passed']=controls.get('passed',False)
            row['controls']={k:{j:v.get(j) for j in ['score','valid','seconds']} for k,v in controls.get('results',{}).items()}
            native=read(p/'native-controls/report.json',{})
            row['native_controls_passed']=native.get('passed',False)
            row['native_control_details']={k:v.get('passed') for k,v in native.get('results',{}).items()}
            worker=read(p/'roll-status.json',{})
            if worker:row.update(phase=worker.get('phase'),account=worker.get('account'),worker_alive=alive(worker.get('worker_pid')))
            admission_dirs=[x for x in p.iterdir() if x.is_dir() and re.fullmatch(r'admission(?:-\d+)?',x.name)] if p.exists() else []
            admission_dir=max(admission_dirs,key=lambda x:int(x.name.split('-')[-1]) if '-' in x.name else 0) if admission_dirs else p/'admission'
            admission=read(admission_dir/'report.json',{})
            row['latest_admission_path']=str(admission_dir)
            row['actual_model_smoke_passed']=admission.get('passed',False)
            runs=sorted(r for r in p.glob('run-6h-*') if r.is_dir())
            if runs:
                run=runs[-1];row['latest_run']=str(run)
                manifest=read(run/'run-manifest.json',{})
                row['host_alive']=alive(manifest.get('pid'),manifest.get('host_start_ticks'))
                row['account']=manifest.get('account',row.get('account'))
                events=[]
                ev=run/'evaluation/events.jsonl'
                if ev.exists():
                    for line in ev.read_text().splitlines():
                        try:events.append(json.loads(line))
                        except ValueError:pass
                clocks=[e for e in events if e.get('event')=='cloud_learning_start_mapping']
                if clocks:
                    row['learning_started_utc']=clocks[0]['remote_started_utc']
                    start=datetime.datetime.fromisoformat(row['learning_started_utc'])
                    row['planned_learning_end_utc']=(start+datetime.timedelta(seconds=21600)).isoformat()
                    row['elapsed_learning_seconds']=max(0,(now-start).total_seconds())
                counts=collections.Counter()
                for file in (run/'evaluation/session-checkpoint').glob('**/*.jsonl'):
                    for line in file.read_text().splitlines():
                        try:e=json.loads(line)
                        except ValueError:continue
                        payload=e.get('payload',{})
                        if e.get('type')=='response_item':counts[payload.get('type','unknown')]+=1
                row['native_session_response_item_counts']=dict(counts)
                row['native_tool_outputs']=counts['custom_tool_call_output']+counts['function_call_output']
                histories=read(run/'evaluation/history.json',[])
                if isinstance(histories,dict):
                    row['best_score']=histories.get('best_score')
                    row['best_valid']=histories.get('best_valid')
                    histories=histories.get('entries',histories.get('submissions',histories.get('history',[])))
                row['history_entries']=len(histories) if isinstance(histories,list) else None
                best=read(run/'evaluation/best.json')
                if best:row['best_observation']=best
                stopped=any(e.get('event')=='learning_stopped' for e in events)
                if clocks and row['native_tool_outputs'] and row['host_alive'] and not stopped:row['phase']='learning'
                for file in (run/'jobs/trial').glob('*/result.json'):
                    error=read(file,{}).get('exception_info') or {}
                    if error:row.update(phase='infrastructure_failed',exception_type=error.get('exception_type'))
                row['latest_run_cloud_instances']=[{k:d.get(k) for k in ['created','destroyed','sandbox_id','native_audit_exec_preflight']}
                    for file in (run/'jobs/trial').glob('*/aliyun-*.json') for d in [read(file,{})]]
                requested_stop=read(run/'user-requested-saturation-stop.json')
                if requested_stop:
                    row.update(phase='user_stopped_after_full_score',
                        user_requested_stop=requested_stop,
                        formal_six_hour_completed=False)
            result['tasks'].append(row)
    result['phase_counts']=dict(collections.Counter(t['phase'] for t in result['tasks']))
    out=BASE/'rollout-status-20261015';out.mkdir(exist_ok=True)
    stamp=now.strftime('%Y%m%dT%H%M%SZ');path=out/(stamp+'.json')
    path.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'receipt':str(path),'observed_utc':result['observed_utc'],'phase_counts':result['phase_counts'],
        'tasks':[{k:r.get(k) for k in ['task','phase','native_tool_outputs','history_entries','learning_started_utc']} for r in result['tasks']]}))

if __name__=='__main__':main()
