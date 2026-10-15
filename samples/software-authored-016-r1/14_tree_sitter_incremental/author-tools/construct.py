from pathlib import Path
import shutil,subprocess,json,hashlib,tarfile
R=Path(__file__).resolve().parents[1]; T=R/'task'; S=R/'material-src/tree-sitter'; G=R/'material-src/tree-sitter-python'
def write(p,s):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(s)
def cp(src,dst):shutil.copytree(src,dst,ignore=shutil.ignore_patterns('.git'),dirs_exist_ok=True)
cp(S,T/'environment/starter');cp(G,T/'environment/grammar')
# Linked recovery gaps; the complete original remains outside the work context.
p=T/'environment/starter/lib/src/subtree.c';s=p.read_text();s=s.replace('    ts_subtree_set_has_changes(&result);','    // Recovery: invalidation propagation is incomplete.');
s=s.replace('.start = length_saturating_sub(edit.start, child_left),','.start = edit.start,').replace('.old_end = length_saturating_sub(edit.old_end, child_left),','.old_end = edit.old_end,').replace('.new_end = length_saturating_sub(edit.new_end, child_left),','.new_end = edit.new_end,');p.write_text(s)
p=T/'environment/starter/lib/src/parser.c';s=p.read_text();a=s.index('    if (!ts_subtree_external_scanner_state_eq(self->reusable_node.last_external_token');b=s.index('    const char *reason',a);s=s[:a]+'    // Recovery: scanner compatibility gate is incomplete.\n\n'+s[b:];s=s.replace('if (!ts_parser__can_reuse_first_leaf(self, *state, result, table_entry)) {','if (false) { /* Recovery: first-leaf parse-state compatibility. */');p.write_text(s)
p=T/'environment/starter/lib/src/get_changed_ranges.c';s=p.read_text().replace('    ts_subtree_has_changes(old_tree) ||','    false || /* Recovery: edited-subtree comparison. */');p.write_text(s)
p=T/'environment/starter/lib/src/tree.c';s=p.read_text().replace('    ts_range_edit(&self->included_ranges[i], edit);','    // Recovery: included-range coordinate updates are incomplete.');p.write_text(s)
cp(T/'environment/grammar',T/'verifier/public/grammar');shutil.copytree(S/'lib/include',T/'verifier/public/include',dirs_exist_ok=True)
shutil.copy(R/'author-tools/probe.c',T/'verifier/probe.c')
# Complete immutable source export, not a set of selected files.
subprocess.run(['git','-C',str(S),'archive','--format=tar','-o',str(T/'verifier/private/reference.tar'),'HEAD'],check=True)
# Private inverse patch, apply from submission root.
pieces=[]
for f in ['parser.c','subtree.c','tree.c','get_changed_ranges.c']:
 rel='lib/src/'+f
 r=subprocess.run(['diff','-u','--label','a/'+rel,'--label','b/'+rel,str(T/'environment/starter'/rel),str(S/rel)],capture_output=True)
 assert r.returncode==1;pieces.append(r.stdout.decode())
write(T/'solution/restore.patch',''.join(pieces));write(T/'verifier/private/restore.patch',''.join(pieces))
write(T/'solution/solve.sh','''#!/bin/sh
set -eu
here=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
cd /home/workspace/tree-sitter/submission
patch -p1 < "$here/restore.patch"
''');(T/'solution/solve.sh').chmod(0o755)
# Frozen snapshot hashes (all tracked repository files).
manifest={'source':{'url':'https://github.com/tree-sitter/tree-sitter','revision':subprocess.check_output(['git','-C',str(S),'rev-parse','HEAD'],text=True).strip(),'license':'MIT'},'grammar':{'url':'https://github.com/tree-sitter/tree-sitter-python','revision':subprocess.check_output(['git','-C',str(G),'rev-parse','HEAD'],text=True).strip(),'tag':'v0.23.6','license':'MIT','generated_artifacts':['src/parser.c','src/scanner.c','src/grammar.json','src/node-types.json']},'files':{}}
for prefix,root in [('source',S),('grammar',G)]:
 names=subprocess.check_output(['git','-C',str(root),'ls-files','-z']).decode().split('\0')
 for n in filter(None,names):
  p=root/n
  if p.is_file():manifest['files'][prefix+'/'+n]=hashlib.sha256(p.read_bytes()).hexdigest()
write(R/'material-src/manifest.json',json.dumps(manifest,indent=2)+'\n');write(T/'authoring/provenance.json',json.dumps({k:v for k,v in manifest.items() if k!='files'},indent=2)+'\n')
shutil.copy(R/'material-src/manifest.json',T/'authoring/source-manifest.json')
