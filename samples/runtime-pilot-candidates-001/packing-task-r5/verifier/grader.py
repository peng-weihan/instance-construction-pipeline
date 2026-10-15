import json,shutil
from pathlib import Path
from runtime import PUBLIC,PRIVATE,ROOT,SubmissionError,InfrastructureError,workdir,snapshot,run,result,check,scoring_constants
from geometry import validate
def grade(submission,suite):
    c=scoring_constants()
    refs=PRIVATE/'reference_lengths.json'
    if not refs.exists():raise InfrastructureError('build-time reference material missing')
    refs=json.loads(refs.read_text());rows=[r for r in json.loads((PRIVATE/'workloads.json').read_text()) if r['split']==suite]
    checks=[];scores=[];lengths=[]
    with workdir() as tmp:
        work=Path(tmp);shutil.copytree(PUBLIC/'repo',work/'repo')
        for rel in ['src/irregular','include/packingsolver/irregular']:
            if (work/'repo'/rel).exists():shutil.rmtree(work/'repo'/rel)
            snapshot(submission/rel,work/'repo'/rel)
        shutil.copyfile(ROOT/'verifier/build.py',work/'build.py')
        rc,out,err=run(work,['python','build.py'],timeout=900,pin_cpu=False)
        if rc:return result(0,[check('build',False,'submitted source did not build')],{'cases':len(rows)})
        bins=[p for p in (work/'build').rglob('packingsolver_irregular') if p.is_file() and p.stat().st_mode&0o111]
        if len(bins)!=1:raise SubmissionError('expected exactly one solver executable')
        binary='/work/'+str(bins[0].relative_to(work));checks.append(check('build',True))
        for row in rows:
            root=PUBLIC/'cases' if suite=='public' else PRIVATE/(suite+'_cases');case=root/(row['id']+'.json')
            shutil.copyfile(case,work/'input.json')
            (work/'certificate.json').unlink(missing_ok=True)
            try:
                rc,out,err=run(work,[binary,'--input','input.json','--certificate','certificate.json','--time-limit',str(c['per_case_seconds']),'--verbosity-level','0','--item-item-minimum-spacing',str(c['solver_clearance'])],timeout=c['wall_seconds'])
                if rc:raise ValueError('solver did not exit successfully')
                v=validate(json.loads(case.read_text()),json.loads((work/'certificate.json').read_text()),c)
                ref=refs[row['id']]['length'];lb=v['area_lower_bound'];gain=max(0,min(1,(ref-v['length'])/max(ref-lb,max(c['epsilon_absolute'],c['epsilon_reference_fraction']*ref))))
                scores.append(c['validity_weight']+c['improvement_weight']*gain);lengths.append(v['length']);checks.append(check(row['id'],True))
            except (ValueError,KeyError,TypeError,OSError,SubmissionError) as e:
                scores.append(0);checks.append(check(row['id'],False,str(e)))
    return result(sum(scores)/len(rows),checks,{'case_scores':scores,'feasible_lengths':lengths,'case_count':len(rows)})
