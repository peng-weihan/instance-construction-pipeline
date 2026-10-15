import json,re,shutil,itertools,time,hashlib
from pathlib import Path
from runtime import PUBLIC,PRIVATE,ROOT,SubmissionError,InfrastructureError,workdir,run,check,result,scoring_constants

def grade(submission,suite):
    c=scoring_constants()
    policy=submission/'policy.lua'
    if policy.is_symlink() or not policy.is_file() or policy.stat().st_size>2_000_000:raise SubmissionError('policy.lua missing or too large')
    config=json.loads((PUBLIC/'match_contract.json').read_text());catalog=json.loads((PRIVATE/'scenarios.json').read_text())
    scenarios=[x for x in catalog if x['split']==suite]
    seeds=config['audit' if suite=='audit' else 'canonical_feedback']['seeds']
    checks=[];values=[];wins=0;turns=[]
    for scene,pair,seat,seed in itertools.product(scenarios,config['faction_pairings'],[1,2],seeds):
        with workdir() as tmp:
            work=Path(tmp);addon=work/'userdata/data/add-ons/EdgeCandidate';addon.mkdir(parents=True)
            shutil.copyfile(policy,addon/'policy.lua');shutil.copyfile(ROOT/'verifier/adapter.lua',addon/'adapter.lua')
            folder=PUBLIC/'scenarios' if suite=='public' else PRIVATE/(suite+'_scenarios')
            shutil.copyfile(folder/(scene['id']+'.cfg'),addon/'scenario.cfg')
            (addon/'_main.cfg').write_text('#ifdef MULTIPLAYER\n{~add-ons/EdgeCandidate/scenario.cfg}\n#endif\n')
            shutil.copyfile(ROOT/'verifier/custom_ai.cfg',addon/'custom_ai.cfg')
            args=['/opt/runtime/wesnoth/bin/wesnoth','--data-dir','/opt/runtime/wesnoth/share/wesnoth',
                  '--userdata-dir','/work/userdata','--userconfig-dir','/work/config','--usercache-dir','/work/cache',
                  '--nogui','--nosound','--multiplayer','--era','era_default','--scenario',scene['id'],
                  '--side','1:'+pair[0],'--side','2:'+pair[1],'--controller','1:ai','--controller','2:ai',
                  '--ai-config',str(seat)+':~add-ons/EdgeCandidate/custom_ai.cfg',
                  '--turns',str(c['turn_cap']),'--rng-seed',str(seed),'--log-info','ai/testing','--exit-at-end']
            name=f'{scene["id"]}/{pair[0]}-{pair[1]}/seat{seat}/seed{seed}'
            began=time.monotonic()
            try:
                rc,out,err=run(work,args,timeout=c['wall_seconds']);log=out+'\n'+err
            except SubmissionError:
                checks.append(check(name,False,'policy/game wall-time forfeit'));values.append(0);continue
            logdir=Path('/logs/verifier/engine');logdir.mkdir(parents=True,exist_ok=True)
            stem=hashlib.sha256(name.encode()).hexdigest()[:16]
            (logdir/(stem+'.log')).write_text(log)
            (logdir/(stem+'.json')).write_text(json.dumps({'case':name,'command':args,'exit_code':rc,'seconds':time.monotonic()-began}))
            if rc and 'candidate_policy' not in log and 'invalid action index' not in log and 'invalid priority' not in log:
                raise InfrastructureError('game failed outside an identified candidate policy error')
            if 'error scripting/lua' in log or rc:
                checks.append(check(name,False,'policy or scenario execution failed'));values.append(0);continue
            winners=[int(v) for v in re.findall(r'WINNER:\s*(\d+)',log)]
            ends=[int(v) for v in re.findall(r'GAME_END_TURN:\s*(\d+)',log)]
            if len(ends)!=1 or not (winners or 'DRAW:' in log):
                raise InfrastructureError('engine result log missing or ambiguous')
            turn=max(c['earliest_turn'],min(c['turn_cap'],ends[0]));win=seat in winners
            efficiency=(c['turn_cap']-turn)/(c['turn_cap']-c['earliest_turn'])
            values.append((c['win_weight']+c['efficiency_weight']*efficiency) if win else c['loss_draw_forfeit']);wins+=win;turns.append(turn)
            checks.append(check(name,True,'win' if win else 'loss/draw'))
    return result(sum(values)/len(values),checks,{'games':len(values),'wins':wins,'win_rate':wins/len(values),'finished_game_turns':turns,'match_scores':values})
