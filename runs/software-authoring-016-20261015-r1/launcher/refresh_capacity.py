"""Refresh actual use for three explicitly authorized shared accounts; never prune leases."""
from pathlib import Path
import datetime,fcntl,hashlib,json,os,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[1]
REG=Path('/ws/users/wcgu/edgebench/dev/task/1013/_nonobtuse-coordination/account-model-concurrency-v001')
def ticks(pid):return Path('/proc',str(pid),'stat').read_text().rsplit(')',1)[1].split()[19]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def assess(row,s):
 assert s['account']==row['account'] and s['limit']==10
 assert s.get('global_actual_audit',{}).get('foreground_reservation_includes_multiplexed_agents'), 'existing foreground reservation policy not confirmed'
 assert type(s['external_reserved']) is int and 0<=s['external_reserved']<=10
 bypid={}
 for key,v in s['leases'].items():
  assert v['lease']==key and v['account']==s['account'] and v.get('model_slots',1)==1
  assert v['host_pid'] not in bypid
  bypid[v['host_pid']]=v
 assert not row['SDK_observation_errors'],'unaccounted SDK observation errors'
 active={v['host_pid'] for v in row['active_SDK_learners']}
 assert active<=set(bypid),'unreserved active SDK learner'
 reviewed=[]
 for h in row['actual_host_selectors']:
  if h['pid'] in bypid:
   assert h['start_ticks']==bypid[h['pid']]['host_start_ticks']
   reviewed.append({'host_pid':h['pid'],'canonical_lease':bypid[h['pid']]['lease']})
  else:
   assert h['pid'] not in active
   assert h['learner_ledgers'] and all(x.get('destroyed') for x in h['learner_ledgers']),'unreserved host may enter model'
 for h in row['unknown_hosts']:
  assert h['pid'] in bypid and h['start_ticks']==bypid[h['pid']]['host_start_ticks'],'unreserved unknown host'
 uncovered_native=[]
 for h in row['actual_selected_codex_processes']:
  covered=h['pid'] in bypid and h['start_ticks']==bypid[h['pid']]['host_start_ticks']
  covered=covered or any(h['pid']==v.get('native_pid') and h['start_ticks']==v.get('native_start_ticks') for v in bypid.values())
  # code-mode hosts are tool children, not additional model sessions.
  if not covered and not h.get('native_exec') and not h.get('foreground_primary'):
   pid=h['pid']
   for _ in range(12):
    try:
     fields=Path('/proc',str(pid),'stat').read_text().rsplit(')',1)[1].split();pid=int(fields[1])
    except (OSError,ValueError):break
    if pid<=1:break
    roots=[x for x in row['actual_selected_codex_processes'] if x.get('native_exec') or x.get('foreground_primary')]
    # A code-mode tool host belongs to its native model session. Count the
    # session root once, including roots covered by external reservations.
    root=next((x for x in roots if x['pid']==pid),None)
    if root:
     try:covered=ticks(pid)==root['start_ticks']
     except OSError:covered=False
     if covered:break
  if not covered:uncovered_native.append(h)
 uncovered_docker=[d for d in row['Docker_bindings'] if not any(pid in bypid for pid in d['host_pids'])]
 assert len(uncovered_native)+len(uncovered_docker)<=s['external_reserved'],'unreserved foreground/native/Docker usage'
 assert len(s['leases'])+s['external_reserved']<10,'no spare slot on this account'
 return {'covered_host_uses':reviewed,'native_uses_covered_by_external_reservations':uncovered_native,'Docker_uses_covered_by_external_reservations':uncovered_docker,'spare_slots':10-s['external_reserved']-len(s['leases'])}
def main():
 q=subprocess.run([sys.executable,str(ROOT/'authoring/review_raymone123_actual_unused_accounts_r1.py')],capture_output=True,text=True,check=True)
 p=Path(json.loads(q.stdout.splitlines()[-1])['report']);a=json.loads(p.read_text());rows={v['account']:v for v in a['accounts']}
 stamp=datetime.datetime.now(datetime.timezone.utc)
 report={'observed_epoch':a['observed_epoch'],'actual_readonly_audit':str(p),'actual_readonly_audit_sha256':sha(p),'authorization':'User requested starting authoring using supplied raymone/1,2,3; preserve every foreign lease and reservation','accounts':[],'models_started':0}
 states={}
 for n in [3]:
  s=json.loads((REG/f'raymone{n}.json').read_text());states[n]=s
  report['accounts'].append({'account':s['account'],**assess(rows[s['account']],s),'canonical_leases_preserved':s['leases'],'external_reserved_preserved':s['external_reserved']})
 assert time.time()-a['observed_epoch']<100
 dest=ROOT/'reports'/('shared-capacity-'+stamp.strftime('%Y%m%dT%H%M%S%fZ')+'.json');dest.write_text(json.dumps(report,indent=2)+'\n')
 for n in [3]:
  with (REG/f'raymone{n}.lock').open('a') as lock:
   fcntl.flock(lock,fcntl.LOCK_EX);path=REG/f'raymone{n}.json';s=json.loads(path.read_text());old=states[n]
   assert s['leases']==old['leases'] and s['external_reserved']==old['external_reserved'],'capacity changed; rerun actual audit'
   assert time.time()-a['observed_epoch']<100
   s['global_actual_audit']={**s.get('global_actual_audit',{}),'observed_epoch':a['observed_epoch'],'receipt':str(dest),'receipt_sha256':sha(dest),'unknown_unreserved_slots':0,'foreground_reservation_includes_multiplexed_agents':True,'scope':'Fresh host/SDK/Docker audit for explicitly authorized three native author jobs; all existing leases and reservations preserved.'}
   s.setdefault('events',[]).append({'event':'user_authorized_native_author_capacity_refresh','utc':stamp.isoformat(),'receipt':str(dest),'preserved_leases':len(s['leases']),'external_reserved_unchanged':s['external_reserved']})
   tmp=path.with_suffix('.raymone-native-author-refresh.tmp');tmp.write_text(json.dumps(s,indent=2)+'\n');tmp.chmod(0o600);tmp.replace(path)
 (ROOT/'reports/latest-capacity.json').write_text(json.dumps({'receipt':str(dest),'observed_epoch':a['observed_epoch'],'spare_slots':{r['account']:r['spare_slots'] for r in report['accounts']}},indent=2)+'\n')
 print(json.dumps({'receipt':str(dest),'spare_slots':{r['account']:r['spare_slots'] for r in report['accounts']}}))
if __name__=='__main__':main()
