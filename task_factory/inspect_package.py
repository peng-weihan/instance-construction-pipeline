"""Static construction inspection only. Does not import/run graders or solutions."""
import argparse,ast,csv,hashlib,json,math,re,tomllib
from pathlib import Path
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    ap=argparse.ArgumentParser();ap.add_argument('batch');a=ap.parse_args();root=Path(a.batch)
    index=json.loads((root/'index.json').read_text());assert len(index)==6
    report={'scope':'static source/package/material inspection only','solver_runs':0,'grader_runs':0,'docker_builds':0,'tasks':[]}
    for row in index:
        p=root/row['task_id'];cfg=tomllib.loads((p/'task.toml').read_text());assert cfg['agent']['timeout_seconds']==21600
        assert cfg['agent']['network']==cfg['verifier']['network']=='none'
        manifest=json.loads((p/'files.sha256.json').read_text())
        listed={entry['path'] for entry in manifest}
        actual={str(f.relative_to(p)) for f in p.rglob('*') if f.is_file() and f.name!='files.sha256.json'}
        assert len(listed)==len(manifest) and listed==actual,'manifest must cover every task file exactly once'
        for entry in manifest:assert sha(p/entry['path'])==entry['sha256'],entry['path']
        assert (p/'instruction.md').read_bytes()==(p/'public/instruction.md').read_bytes()
        score=json.loads((p/cfg['score']['metadata']).read_text())
        design=json.loads((p/'public/score_design.json').read_text())
        assert score['constants']==design['constants'],'scoring constants diverged'
        assert score['formula']==design.get('formula',design.get('aggregation'))
        assert 'scoring_constants()' in (p/'verifier/grader.py').read_text()
        own=list((p/'verifier').glob('*.py'))+list((p/'solution').rglob('*.py'))+list((p/'tools').glob('*.py'))
        for f in own:ast.parse(f.read_text(),filename=str(f))
        for side in ['agent','verifier']:
            ctx=p/'environment'/side;docker=(ctx/'Dockerfile').read_text()
            assert re.search(r'FROM ubuntu@sha256:[0-9a-f]{64}',docker)
            for f in (p/'public').rglob('*'):
                if f.is_file():assert sha(f)==sha(ctx/'public'/f.relative_to(p/'public'))
            if side=='agent':
                assert not any((ctx/x).exists() for x in ['private','verifier','solution'])
            else:
                for folder in ['private','verifier']:
                    for f in (p/folder).rglob('*'):
                        if f.is_file():assert sha(f)==sha(ctx/folder/f.relative_to(p/folder))
        r={'task_id':p.name,'manifest_files':len(manifest),'python_sources_parsed':len(own),'separate_build_contexts':True,'hashes_match':True,
           'manifest_complete':True,'scoring_metadata_consistent':True,'grader_loads_scoring_metadata':True}
        if row['category']=='software':
            suites=json.loads((p/'private/behavior_cases.json').read_text())
            assert all(set(x['group'] for x in rows)=={'policy','retry','idempotency','async','leases','trace','replay'} for rows in suites.values())
            r['behavior_checks']={k:len(v) for k,v in suites.items()}
        elif row['category']=='formal':
            targets=json.loads((p/'public/targets.json').read_text());assert len(targets)==31
            pat=re.compile(r'(/- BEGIN TASK PROOF ([^\n]+) -/)(.*?)(/- END TASK PROOF \2 -/)',re.S)
            count=0
            for f in (p/'solution/reference').rglob('*.lean'):
                rel=f.relative_to(p/'solution/reference');ref=f.read_text();start=(p/'public/repo'/rel).read_text()
                clean=lambda s:pat.sub(lambda m:m[1]+'<PROOF>'+m[4],s)
                assert clean(ref)==clean(start)
                for match in pat.finditer(ref):assert not re.search(r'\bsorry\b',match[3]);count+=1
            assert count==31;r['reference_proof_bodies']=count
        elif row['category']=='finance':
            dates=[];counts={}
            for name in ['train','dev','feedback','audit']:
                folder=p/('public/data' if name in ['train','dev'] else 'private/data')
                data=list(csv.reader((folder/(name+'_prices.csv')).open()));header=data.pop(0);assert len(header)==9
                assert all(len(row)==9 and all(math.isfinite(float(v)) and float(v)>0 for v in row[1:]) for row in data)
                counts[name]=len(data);dates += [row[0] for row in data]
            assert dates==sorted(set(dates));r['price_rows']=counts
            mandate=json.loads((p/'public/mandate.json').read_text());c=score['constants']
            for key,alias in [('annual_days','year_days'),('cost','cost_per_abs_weight_change'),('borrow','short_borrow_annual'),('financing','negative_cash_financing_annual')]:assert c[key]==mandate[alias]
            worst=max(counts[x] for x in ['dev','feedback','audit'])*c['decision_seconds']+c['initialize_seconds']
            assert cfg['verifier']['timeout_seconds']>worst
            r['protocol_deadline_sum_seconds']=worst
        elif row['category']=='game':
            maps=list((p/'public/scenarios').glob('*.map'))+list((p/'private').rglob('*.map'))
            assert len(maps)==9 and len({sha(f) for f in maps})==9
            for f in maps:
                lines=[s.split(',') for s in f.read_text().splitlines()]
                assert len(lines)==25 and all(len(x)==25 for x in lines)
            r['unique_maps']=9
            match=json.loads((p/'public/match_contract.json').read_text());c=score['constants']
            assert c['wall_seconds']==match['per_game_wall_cap_seconds'] and c['turn_cap']==match['turn_cap']
            worst=match['audit']['games']*c['wall_seconds']
            assert cfg['verifier']['timeout_seconds']>worst
            r['audit_game_deadline_sum_seconds']=worst
        elif row['category']=='packing':
            rows=json.loads((p/'private/workloads.json').read_text());families={}
            for x in rows:
                if x['family'] in families:assert families[x['family']]==x['split']
                families[x['family']]=x['split']
            assert len(rows)==27;r['workloads']=27;r['geometry_families']=len(families)
        elif row['category']=='science':
            r['observations']={}
            for split in ['public','feedback','audit']:
                file=p/('public' if split=='public' else 'private')/(split+'_observations.csv')
                r['observations'][split]=len(list(csv.DictReader(file.open())))
        report['tasks'].append(r)
    (root/'static_inspection.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(report,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
