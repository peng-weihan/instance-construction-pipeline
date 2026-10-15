import json,re,shutil,itertools
from pathlib import Path
from runtime import PUBLIC,PRIVATE,ROOT,SubmissionError,InfrastructureError,workdir,run,check,result

def grade(submission,suite):
    policy=submission/'policy.lua'
    if policy.is_symlink() or not policy.is_file() or policy.stat().st_size>2_000_000:raise SubmissionError('policy.lua missing or too large')
    config=json.loads((PUBLIC/'match_contract.json').read_text());catalog=json.loads((PRIVATE/'scenarios.json').read_text())
    scenarios=[x for x in catalog if x['split']==suite];seeds=[29,61,101] if suite=='audit' else [17]
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
                  '--ai-config',str(seat)+':/work/userdata/data/add-ons/EdgeCandidate/custom_ai.cfg',
                  '--turns','45','--rng-seed',str(seed),'--log-info','ai/testing','--exit-at-end']
            name=f'{scene["id"]}/{pair[0]}-{pair[1]}/seat{seat}/seed{seed}'
            try:
                rc,out,err=run(work,args,timeout=40);log=out+'\n'+err
            except SubmissionError:
                checks.append(check(name,False,'policy/game wall-time forfeit'));values.append(0);continue
            if 'error scripting/lua' in log or rc:
                checks.append(check(name,False,'policy or scenario execution failed'));values.append(0);continue
            winners=[int(v) for v in re.findall(r'WINNER:\s*(\d+)',log)]
            ends=[int(v) for v in re.findall(r'GAME_END_TURN:\s*(\d+)',log)]
            if len(ends)!=1 or not (winners or 'DRAW:' in log):
                raise InfrastructureError('engine result log missing or ambiguous')
            turn=max(1,min(45,ends[0]));win=seat in winners
            values.append((.8+.2*(45-turn)/44) if win else 0);wins+=win;turns.append(turn)
            checks.append(check(name,True,'win' if win else 'loss/draw'))
    return result(sum(values)/len(values),checks,{'games':len(values),'wins':wins,'win_rate':wins/len(values),'finished_game_turns':turns,'match_scores':values})
