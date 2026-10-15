"""Collect non-secret live status of the three owned learner runs."""
from pathlib import Path
import collections,datetime,json
ROOT=Path('/ws/users/raymone/edgebench')
paths={'restler':ROOT/'restler-agent-001/run-6h-001','lean':ROOT/'next-two-001/lean-pilot/run-6h-002','packing':ROOT/'next-two-001/packing-pilot/run-6h-001'}
out={'observed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'runs':{}}
for name,r in paths.items():
 m=json.loads((r/'run-manifest.json').read_text());d={k:m.get(k) for k in ['status','pid','model','account','learning_budget_seconds','evaluation_interval_seconds']};d['host_alive']=Path('/proc',str(m.get('pid'))).exists()
 e=r/'evaluation/events.jsonl'
 if e.exists():
  events=[]
  for line in e.read_text().splitlines():
   try:events.append(json.loads(line))
   except ValueError:pass
  for event in events:
   if event.get('event')=='cloud_learning_start_mapping':d['learning_started_utc']=event['remote_started_utc']
 h=r/'evaluation/history.json'
 if h.exists():
  history=json.loads(h.read_text());entries=history['entries'];d.update(completed_grades=len(entries),best_score=history.get('best_score'))
  if entries:d['latest_grade']={k:entries[-1].get(k) for k in ['round','status','snapshot_time_seconds','score','valid','failed_checks']}
 else:d['completed_grades']=0
 files=list((r/'evaluation/session-checkpoint').rglob('rollout-*.jsonl'))
 if files:
  p=max(files,key=lambda q:q.stat().st_mtime);rows=[]
  for line in p.read_text().splitlines():
   try:rows.append(json.loads(line))
   except ValueError:pass
  types=collections.Counter(x.get('payload',{}).get('type') for x in rows)
  d.update(native_records=len(rows),native_tool_calls=types['custom_tool_call']+types['function_call'],native_tool_outputs=types['custom_tool_call_output']+types['function_call_output'],native_last_timestamp=rows[-1].get('timestamp') if rows else None)
 out['runs'][name]=d
(ROOT/'next-two-001/startup-status.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
