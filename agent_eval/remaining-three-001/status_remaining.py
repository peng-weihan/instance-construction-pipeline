from pathlib import Path
import collections,datetime,json
ROOT=Path('/ws/users/raymone/edgebench/remaining-three-001');report={'observed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'tasks':{}}
for kind in ['game','finance','science']:
 root=ROOT/(kind+'-pilot-r3' if kind=='finance' and (ROOT/'finance-pilot-r3').exists() else kind+'-pilot-r2' if kind=='finance' and (ROOT/'finance-pilot-r2').exists() else kind+'-pilot');data={'pilot_root':str(root)}
 admission=root/('admission-003' if (root/'admission-003/report.json').exists() else ('admission-002' if (root/'admission-002/report.json').exists() else 'admission'))/'report.json'
 for label,path in [('admission',admission),('controls',root/'scorer-controls/report.json'),('isolation',root/'isolation.json')]:
  if path.exists():
   r=json.loads(path.read_text());data[label]={k:r.get(k) for k in ['status','passed','error','actual_host_exit_code','successful_terminal_tool_completions','actual_file_contents_verified','actual_native_session_files','own_container_and_disk_cleanup_confirmed'] if k in r}
   if r.get('exception_redacted'):data[label]['exception_summary']=r['exception_redacted'].get('exception_message')
 for run in sorted(root.glob('run-6h-*')):
  m=run/'run-manifest.json'
  if not m.exists():continue
  m=json.loads(m.read_text());x={k:m.get(k) for k in ['status','pid','account','model','learning_budget_seconds','evaluation_interval_seconds','started_utc','exit_code']};x['host_alive']=Path('/proc',str(m.get('pid'))).exists()
  events=run/'evaluation/events.jsonl'
  if events.exists():
   for line in events.read_text().splitlines():
    try:e=json.loads(line)
    except ValueError:continue
    if e.get('event')=='cloud_learning_start_mapping':x['learning_started_utc']=e['remote_started_utc']
  history=run/'evaluation/history.json'
  if history.exists():
   h=json.loads(history.read_text());entries=h['entries'];x.update(completed_grades=sum(e.get('status')=='completed' for e in entries),best_score=h.get('best_score'))
  native=list((run/'evaluation/session-checkpoint').rglob('rollout-*.jsonl'))
  if native:
   p=max(native,key=lambda p:p.stat().st_mtime);rows=[]
   for line in p.read_text().splitlines():
    try:rows.append(json.loads(line))
    except ValueError:pass
   types=collections.Counter(r.get('payload',{}).get('type') for r in rows)
   x.update(native_records=len(rows),native_tool_calls=types['function_call']+types['custom_tool_call'],native_tool_outputs=types['function_call_output']+types['custom_tool_call_output'],last_native_timestamp=rows[-1].get('timestamp') if rows else None)
  data[run.name]=x
 report['tasks'][kind]=data
(ROOT/'startup-status.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
