from pathlib import Path
import shutil,subprocess
R=Path('/ws/users/raymone/edgebench/remaining-three-001');task=R/'wesnoth_frontier_campaign_ai';ctx=R/'game-probe-context';ctx.mkdir()
s=(task/'verifier/runtime.py').read_text().replace("'--unshare-all','--die-with-parent'","'--unshare-all','--share-net','--uid','2000','--gid','2000','--die-with-parent'")
(ctx/'runtime.py').write_text(s);shutil.copyfile(R/'probe_game_match.py',ctx/'probe_game_match.py')
(ctx/'Dockerfile').write_text('FROM edge-raymone-game:initial\nCOPY runtime.py /judge/verifier/runtime.py\nCOPY probe_game_match.py /probe_game_match.py\nENV PYTHONPATH=/judge/verifier\nENTRYPOINT ["/opt/runtime/venv/bin/python", "/probe_game_match.py"]\n')
subprocess.run(['docker','build','--network','none','-t','edge-raymone-game:probe001',str(ctx)],check=True)
out=R/'game-match-probe-001';out.mkdir()
args=['docker','run','--rm','--name','edge-raymone-game-match-probe-001','--network','none','--read-only','--tmpfs','/tmp:rw,exec,size=4g','--cpus','2','--memory','8g','--pids-limit','256','--cap-drop','ALL']
for cap in ['SYS_ADMIN','SETUID','SETGID','SETFCAP','CHOWN','DAC_OVERRIDE','FOWNER','KILL']:args+=['--cap-add',cap]
for option in ['seccomp=unconfined','apparmor=unconfined','systempaths=unconfined']:args+=['--security-opt',option]
args+=['--mount','type=bind,source='+str(out)+',target=/diagnostics','--mount','type=bind,source='+str(task/'solution')+',target=/author-reference,readonly','edge-raymone-game:probe001']
subprocess.run(args,check=True,timeout=180)
