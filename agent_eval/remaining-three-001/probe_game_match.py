"""Execute one real engine game with the same candidate namespace and budget."""
import json,shutil,time
from pathlib import Path
from runtime import PUBLIC,PRIVATE,ROOT,workdir,run,SubmissionError
OUT=Path('/diagnostics');OUT.mkdir(exist_ok=True)
config=json.loads((PUBLIC/'match_contract.json').read_text());scene=json.loads((PRIVATE/'scenarios.json').read_text())[0]
scene=next(x for x in json.loads((PRIVATE/'scenarios.json').read_text()) if x['split']=='public')
for name,policy in [('starter',PUBLIC/'submission/policy.lua'),('reference',Path('/author-reference/policy.lua'))]:
    with workdir() as tmp:
        work=Path(tmp);addon=work/'userdata/data/add-ons/EdgeCandidate';addon.mkdir(parents=True)
        for src,filename in [(policy,'policy.lua'),(ROOT/'verifier/adapter.lua','adapter.lua'),(ROOT/'verifier/custom_ai.cfg','custom_ai.cfg'),(PUBLIC/'scenarios'/(scene['id']+'.cfg'),'scenario.cfg')]:shutil.copyfile(src,addon/filename)
        (addon/'_main.cfg').write_text('#ifdef MULTIPLAYER\n{~add-ons/EdgeCandidate/scenario.cfg}\n#endif\n')
        args=['/opt/runtime/wesnoth/bin/wesnoth','--data-dir','/opt/runtime/wesnoth/share/wesnoth','--userdata-dir','/work/userdata','--userconfig-dir','/work/config','--usercache-dir','/work/cache','--nogui','--nosound','--multiplayer','--era','era_default','--scenario',scene['id'],'--side','1:Loyalists','--side','2:Rebels','--controller','1:ai','--controller','2:ai','--ai-config','1:~add-ons/EdgeCandidate/custom_ai.cfg','--turns','45','--rng-seed','17','--log-info','ai/testing','--exit-at-end']
        start=time.monotonic()
        try:rc,stdout,stderr=run(work,args,timeout=40)
        except SubmissionError as e:rc=None;stdout='';stderr=str(e)
        (OUT/(name+'-stdout.txt')).write_text(stdout);(OUT/(name+'-stderr.txt')).write_text(stderr)
        report={'policy':name,'exit_code':rc,'seconds':time.monotonic()-start,'actual_engine_command':args,'stdout_tail':stdout[-1500:],'stderr_tail':stderr[-3000:]}
        (OUT/(name+'-report.json')).write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)
