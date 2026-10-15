"""Retry pre-model memory quota failures at five-minute intervals, preserving attempts."""
from pathlib import Path
import datetime
import fcntl
import json
import os
import subprocess
import sys
import time

ROOT=Path('/ws/users/raymone/edgebench/swe-rollouts-003-20261015-r4')
TASK=ROOT/'04_pytest_fixtures'

def save(phase,**kw):
    p=TASK/'quota-wait-status.json'
    p.write_text(json.dumps({'phase':phase,'watcher_pid':os.getpid(),
        'updated_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'retry_interval_seconds':300,'max_wait_seconds':21600,**kw},indent=2)+'\n')

def main():
    lock=(TASK/'quota-wait.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    deadline=time.monotonic()+21600
    while time.monotonic()<deadline:
        latest=sorted(TASK.glob('run-6h-*'))
        latest=[p for p in latest if p.is_dir()][-1]
        if (latest/'evaluation/events.jsonl').exists():
            save('learning_attempt_exists_stop_quota_retries',run=str(latest));return
        results=list((latest/'jobs/trial').glob('*/result.json'))
        if len(results)!=1:
            save('holding_non_quota_state',run=str(latest));return
        error=json.loads(results[0].read_text()).get('exception_info') or {}
        if error.get('exception_type')!='RateLimitException' or 'Account resource quota exceeded' not in error.get('exception_message',''):
            save('holding_non_quota_failure',run=str(latest));return
        index=int(latest.name.rsplit('-',1)[1])+1
        run=f'run-6h-{index:03d}'
        stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
        save('fresh_account_check_then_quota_retry',next_run=run)
        with (TASK/('quota-retry-'+stamp+'.log')).open('xb') as log:
            child=subprocess.Popen([sys.executable,'-u',str(ROOT/'scripts/retry_after_quota.py'),run],stdout=log,stderr=subprocess.STDOUT)
            while child.poll() is None:
                if (TASK/run/'evaluation/events.jsonl').exists():save('learning_attempt_started',run=str(TASK/run),worker_pid=child.pid)
                time.sleep(30)
        save('waiting_after_attempt',last_attempt=run,host_exit_code=child.returncode)
        time.sleep(300)
    save('quota_wait_deadline')

if __name__=='__main__':main()
