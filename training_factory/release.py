"""Release only complete, validated, difficulty-screened real SFT episodes."""
import argparse
import hashlib
import json
from pathlib import Path

from .calibrate import write_json
from .contract import digest, geometry_fingerprint, pointset_fingerprint, read_instance
from .teacher import adapt_events


def release(run, output):
    run, output = Path(run), Path(output)
    output.mkdir(parents=True, exist_ok=False)
    accepted, audits = [], []
    for episode in sorted((run/'episodes').iterdir()):
        quality_path = episode/'quality.json'
        if not quality_path.exists():
            audits.append({'episode':episode.name,'accepted':False,'reason':'unfinished'})
            continue
        quality = json.loads(quality_path.read_text())
        launch = json.loads((episode/'launch.json').read_text())
        work_name = Path(launch['workdir']).name
        task = next(p for p in (run/'tasks').iterdir() if work_name.startswith(p.name+'-'))
        manifest = json.loads((task/'manifest.json').read_text())
        source = Path(manifest['source_pool'])
        alignment = json.loads((source/'alignment.json').read_text()) if (source/'alignment.json').exists() else {}
        raw = (episode/'events.jsonl').read_bytes()
        checks = {'episode_quality':quality['accepted'], 'alignment_passed':alignment.get('passed') is True,
            'alignment_precedes_teacher': (source/'alignment.json').exists() and
                (source/'alignment.json').stat().st_mtime < (episode/'launch.json').stat().st_mtime,
            'raw_trace_hash':hashlib.sha256(raw).hexdigest()==quality['events_sha256'],
            'requested_model':quality['model']=='gpt-6.1-sol' and launch['model']=='gpt-6.1-sol',
            'budget':quality['teacher_seconds']<=610}
        final_files = json.loads((episode/'final_submission.json').read_text())
        checks['frozen_source'] = digest(final_files)==quality['source_sha256']==(episode/'final.lock').read_text()
        verdict = all(checks.values())
        audits.append({'episode':episode.name,'accepted':verdict,'checks':checks,
                       'final_raw_score':quality['final']['raw_score'],'teacher_seconds':quality['teacher_seconds']})
        if verdict:
            record = json.loads((episode/'sft.jsonl').read_text())
            observed = adapt_events([json.loads(line) for line in raw.decode().splitlines()],
                                    (episode/'prompt.txt').read_text())
            if observed['problems'] or observed['messages'] != record['messages']:
                raise ValueError('SFT messages differ from the observed event adapter')
            record['usage'] = [e.get('usage') for e in map(json.loads, raw.decode().splitlines())
                               if e.get('type') == 'turn.completed']
            record['provenance']['release_checks'] = checks
            record['provenance']['alignment'] = alignment
            record['split_group'] = task.name
            accepted.append(record)
    with (output/'train.jsonl').open('w') as stream:
        for record in accepted:
            stream.write(json.dumps(record,ensure_ascii=False)+'\n')
    summary = {'real_episodes':len(audits),'accepted_sft_episodes':len(accepted),'episodes':audits,
        'teacher_model':'gpt-6.1-sol','split_policy':'Group all trajectories from a task into the same split; '
            'this pilot has no independent task-family validation set.',
        'distribution_claim':'Matched input contract, selected marginals, family counts and solver-response means; '
            'joint and long-horizon agent distribution equality remain unproven.'}
    write_json(output/'summary.json',summary)
    print(json.dumps(summary),flush=True)
    return summary


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--run',required=True)
    parser.add_argument('--output',required=True)
    args=parser.parse_args()
    release(args.run,args.output)
