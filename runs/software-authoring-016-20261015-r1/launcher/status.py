"""Sanitized live status for only this batch; never copies auth or full trajectories."""
from pathlib import Path
import collections,datetime,json
ROOT=Path(__file__).resolve().parents[1]
def alive(pid,start_ticks):
 try:
  fields=Path('/proc',str(pid),'stat').read_text().rsplit(')',1)[1].split()
  return fields[19]==start_ticks and fields[0]!='Z'
 except (OSError,ValueError):return False
result={'observed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'remote_root':str(ROOT),'phase':'task_authoring_not_solver','jobs':[]}
startup=ROOT/'startup.json'
if startup.exists():
 data=json.loads(startup.read_text());result.update({'started_utc':data['started_utc'],'queued':data['queued'],'scheduler_pid':data['scheduler_pid'],'queue_state':data.get('queue_state')})
for job in json.loads((ROOT/'launch-plan.json').read_text())['jobs']:
 d=Path(job['cwd']);p=d/'status.json'
 s=json.loads(p.read_text()) if p.exists() else {**job,'state':'queued'}
 events=collections.Counter();items=collections.Counter();successful_commands=0;completed_tools=0;threads=[];last_tool=None;errors=[]
 traj=d/'trajectory.jsonl'
 if traj.exists():
  with traj.open(errors='replace') as f:
   for line in f:
    try:e=json.loads(line)
    except ValueError:continue
    events[e.get('type','unknown')]+=1
    if e.get('thread_id'):threads.append(e['thread_id'])
    if e.get('type')=='item.completed':
     i=e.get('item',{});kind=i.get('type','unknown');items[kind]+=1
     if kind=='command_execution' and i.get('exit_code')==0:successful_commands+=1
     if kind in ['command_execution','mcp_tool_call','tool_call','web_search']:
      completed_tools+=1;last_tool={'type':kind,'status':i.get('status'),'exit_code':i.get('exit_code'),'tool':i.get('tool')}
    if e.get('type') in ['error','turn.failed']:errors.append({'type':e['type']})
 s.update({'native_alive':alive(s.get('native_pid'),s.get('native_start_ticks')) if s.get('native_pid') else False,'worker_alive':alive(s.get('worker_pid'),s.get('worker_start_ticks')) if s.get('worker_pid') else False,'thread_ids':list(dict.fromkeys(threads)),'event_counts':dict(events),'completed_item_types':dict(items),'successful_shell_commands':successful_commands,'completed_tool_items':completed_tools,'last_completed_tool':last_tool,'trajectory_bytes':traj.stat().st_size if traj.exists() else 0,'task_directory_exists':(d/'task').is_dir(),'author_result_exists':(d/'AUTHOR_RESULT.json').is_file(),'reported_error_events':errors})
 result['jobs'].append(s)
(ROOT/'reports/live-status.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(result,ensure_ascii=False))
