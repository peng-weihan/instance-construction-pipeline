import json,re,shutil
from pathlib import Path
from runtime import PUBLIC,PRIVATE,SubmissionError,InfrastructureError,workdir,snapshot,run,result,check,scoring_constants
PAT=re.compile(r'(/- BEGIN TASK PROOF ([^\n]+) -/)(.*?)(/- END TASK PROOF \2 -/)',re.S)
FORBIDDEN=re.compile(r'\b(axiom|unsafe|opaque|macro|elab|initialize|implemented_by|extern|run_tac)\b|#\s*(eval|print|check|reduce)|set_option\s+(debug|compiler)|sorryAx')
def skeleton(text):return PAT.sub(lambda m:m[1]+'<PROOF>'+m[4],text)
def grade(submission,suite):
    c=scoring_constants()
    targets=json.loads((PUBLIC/'targets.json').read_text());files=sorted({t['file'] for t in targets})
    checks=[];unfinished=set()
    with workdir() as tmp:
        work=Path(tmp);shutil.copytree('/opt/runtime/lean-project',work/'repo',symlinks=False)
        incoming=work/'incoming';snapshot(submission,incoming)
        for f in files:
            if not (incoming/f).is_file():raise SubmissionError('missing target file '+f)
            original=(PUBLIC/'repo'/f).read_text()
            try:changed=(incoming/f).read_text()
            except UnicodeDecodeError:raise SubmissionError('Lean source must be UTF-8')
            if skeleton(original)!=skeleton(changed):raise SubmissionError('edit outside marked proof bodies: '+f)
            if len(PAT.findall(original))!=len(PAT.findall(changed)):raise SubmissionError('proof markers changed')
            for m in PAT.finditer(changed):
                if re.search(r"\b(sorry|admit)\b",m[3]):unfinished.add(m[2])
                if FORBIDDEN.search(m[3]):raise SubmissionError('unsupported command or axiom in proof '+m[2])
            (work/'repo'/f).write_text(changed)
        # A fresh build uses the fixed manifest and previously fetched dependency closure.
        modules=sorted({t['file'][:-5].replace('/','.') for t in targets})
        rc,out,err=run(work,['sh','-c','cd repo && lake build '+' '.join(modules)],timeout=1200)
        if rc<0 or rc>=128:raise InfrastructureError('Lean compiler terminated abnormally: '+str(rc))
        if rc:return result(0,[check('lean_build',False,(out+'\n'+err)[-550:])],{'targets':len(targets)})
        source='\n'.join('import '+m for m in modules)+'\n'
        for i,t in enumerate(targets):source+=f'#eval IO.println "TASK_TARGET_{i}"\n#print axioms {t["full_name"]}\n'
        (work/'repo/TaskCheck.lean').write_text(source)
        rc,out,err=run(work,['sh','-c','cd repo && lake env lean TaskCheck.lean'],timeout=300)
        if rc:raise InfrastructureError('Lean declaration checker failed: '+str(rc)+' '+err[-300:])
        checks=[check('lean_build',True)];groups={};allowed=set(c['allowed_axioms'])
        for i,t in enumerate(targets):
            chunk=out.split('TASK_TARGET_'+str(i)+'\n',1)
            text=chunk[1].split('TASK_TARGET_',1)[0] if len(chunk)==2 else ''
            match=re.search(r'depends on axioms:\s*\[([^\]]*)\]',text,re.S)
            no_axioms='does not depend on any axioms' in text
            names={x.strip() for x in match[1].split(',') if x.strip()} if match else set()
            ok=bool(t['name'] not in unfinished and (match or no_axioms) and names<=allowed and 'error:' not in text)
            g='moment_and_process' if t['group'] in ['moment','process'] else t['group']
            groups.setdefault(g,[]).append(ok)
            checks.append(check(t['name'],ok,'kernel dependency closure accepted' if ok else 'unfinished, unexpected axiom, or declaration check failed'))
        weights=c['group_weights']
        rates={g:sum(v)/len(v) for g,v in groups.items()}
        return result(sum(weights[g]*rates[g] for g in weights),checks,{'group_completion':rates,'completed_targets':sum(sum(x) for x in groups.values()),'target_count':len(targets),'checker_exit_code':rc})
