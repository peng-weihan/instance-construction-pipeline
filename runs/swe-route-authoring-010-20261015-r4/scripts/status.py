"""Verify native process identities and real tools; never print prompts or auth."""
from pathlib import Path
import collections
import datetime
import json

ROOT = Path(__file__).resolve().parents[1]


def inspect(path):
    d = json.loads(path.read_text())
    pid = d.get('native_pid')
    live = False
    try:
        f = Path('/proc', str(pid), 'stat').read_text().rsplit(')', 1)[1].split()
        live = f[0] != 'Z' and f[19] == str(d.get('native_start_ticks'))
    except OSError:
        pass
    trace = path.parent / 'trajectory.jsonl'
    count = 0
    if trace.exists():
        for line in trace.read_text().splitlines():
            try:
                e = json.loads(line)
                if e.get('type') == 'item.completed' and e.get('item', {}).get('type') in ('command_execution', 'mcp_tool_call', 'file_change'):
                    count += 1
            except ValueError:
                pass
    return {k: d.get(k) for k in ['id', 'route', 'account', 'work_kind', 'state', 'native_started_utc', 'native_exit_code']} | {
        'native_pid': pid, 'native_process_alive': live, 'completed_tool_items': count,
        'trajectory_bytes': trace.stat().st_size if trace.exists() else 0}


def main():
    startup = json.loads((ROOT / 'startup.json').read_text())
    plan = json.loads((ROOT / 'launch-plan.json').read_text())
    rows = [inspect(Path(plan['existing_author_status']))]
    for job in startup['dispatched']:
        p = ROOT / 'jobs' / job['id'] / 'status.json'
        rows.append(inspect(p) if p.exists() else {'id': job['id'], 'state': 'no_status_yet', 'native_process_alive': False})
    report = {'observed_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'actual_active_authors': sum(r['native_process_alive'] for r in rows),
              'active_by_account': dict(collections.Counter(r['account'] for r in rows if r['native_process_alive'])),
              'rows': rows, 'teacher_runs_started_by_this_batch': 0}
    (ROOT / 'live-status.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(report, ensure_ascii=False))


if __name__ == '__main__':
    main()
