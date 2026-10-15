from pathlib import Path
ROOT=Path('/ws/users/raymone/edgebench/remaining-three-001');context=ROOT/'game-pilot/task/environment'
p=context/'bootstrap.sh';p.write_text(p.read_text().replace('LD_LIBRARY_PATH=/opt/runtime/edge-game-libs ',''))
p=context/'public/play_public.py';p.write_text(p.read_text().replace("'LD_LIBRARY_PATH':'/opt/runtime/edge-game-libs',",''))
s=(ROOT/'launch_agent.py').read_text().replace("ROOT/'admission-002/report.json'","ROOT/'admission-003/report.json'")
(ROOT/'launch_agent_game.py').write_text(s)
s=(ROOT/'advance_remaining_pilot.py').read_text().replace("'admission-002/report.json'","'admission-003/report.json'").replace("str(ROOT/'launch_agent.py')","str(ROOT/'launch_agent_game.py')").replace("out/'advance.json'","out/'advance-003.json'")
(ROOT/'advance_game_003.py').write_text(s)
print('game bootstrap and public helper use the matching loader only for the ELF process')
