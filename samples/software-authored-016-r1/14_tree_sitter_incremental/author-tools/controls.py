from pathlib import Path
import shutil,subprocess,json
R=Path(__file__).resolve().parents[1];T=R/'task';S=R/'material-src/tree-sitter';E=R/'evidence';C=E/'controls';C.mkdir(exist_ok=True)
def make(name,base):
 p=C/name;shutil.copytree(base/'lib',p/'lib',dirs_exist_ok=True);return p
def fullparse(p):
 f=p/'lib/src/parser.c';s=f.read_text();start=s.index('TSTree *ts_parser_parse(\n');a=s.index('  TSTree *result = NULL;',start);s=s[:a]+'  old_tree = NULL; /* honest full-reparse baseline */\n'+s[a:];f.write_text(s)
# Strongest baseline first: correct non-parser APIs, always parse from scratch.
base=make('full_reparse_complete_apis',S);fullparse(base)
p=make('full_reparse_starter',T/'environment/starter');fullparse(p)
p=make('edit_only',T/'environment/starter')
for f in ['subtree.c','tree.c']:shutil.copy(S/'lib/src'/f,p/'lib/src'/f)
p=make('range_only',T/'environment/starter');shutil.copy(S/'lib/src/get_changed_ranges.c',p/'lib/src/get_changed_ranges.c')
# A semantic near miss: all restored except scanner compatibility safety gate.
p=make('scanner_gate_missing',S);f=p/'lib/src/parser.c';s=f.read_text();a=s.index('    if (!ts_subtree_external_scanner_state_eq(self->reusable_node.last_external_token');b=s.index('    const char *reason',a);f.write_text(s[:a]+s[b:])
commands=[]
for name,path in [('full_reparse_complete_apis',base),('reference',S),('full_reparse_starter',C/'full_reparse_starter'),('edit_only',C/'edit_only'),('range_only',C/'range_only'),('scanner_gate_missing',C/'scanner_gate_missing')]:
 cmd=['python',str(T/'tests/grader.py'),'--submission',str(path),'--base',str(T/'verifier'),'--output',str(E/name),'--build-parent',str(R/'candidate-builds')]
 print('RUN',name,flush=True);r=subprocess.run(cmd,capture_output=True,text=True);(E/(name+'.log')).write_text(r.stdout+r.stderr);commands.append({'name':name,'command':cmd,'exit_code':r.returncode});print(r.stdout,flush=True)
(E/'control-commands.json').write_text(json.dumps(commands,indent=2)+'\n')
