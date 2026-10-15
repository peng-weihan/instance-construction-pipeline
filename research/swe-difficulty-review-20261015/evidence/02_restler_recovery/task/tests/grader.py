#!/usr/bin/env python3
"""Root orchestration; no candidate imports occur in this interpreter."""
import argparse
import json
import re
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import traceback

ROOT_MODULES = ('restler.py', 'restler_settings.py')

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--submission',type=Path,default=Path('/home/workspace/restler-recovery/submission'))
    parser.add_argument('--private',type=Path,default=Path('/opt/restler-judge/private'))
    parser.add_argument('--spec',type=Path,default=Path('/opt/restler-judge/score-spec.json'))
    parser.add_argument('--scratch',type=Path,default=Path('/work/grade'))
    parser.add_argument('--output',type=Path,default=Path('/logs/verifier'))
    args = parser.parse_args()
    args.output.mkdir(parents=True,exist_ok=True)
    for name in ('reward.txt','reward.json'):
        (args.output/name).unlink(missing_ok=True)
    try:
        spec = json.loads(args.spec.read_text())
        sys.path.insert(0,str(args.private))
        from harness import Campaign,own,demote,stop,clean_env,configure_limits,seal
        configure_limits(spec['limits'])
        groups = {g['name']:False for g in spec['groups']}
        diagnostics = {}
        raw = {}
        args.scratch.mkdir(parents=True)
        os.chmod(args.scratch,0o755)
        source = args.scratch/'candidate'
        shutil.copytree(args.private/'base/restler', source)
        malformed = []
        submitted = args.submission/'restler'
        names = list(ROOT_MODULES)
        for directory in ('engine','utils'):
            folder = submitted/directory
            if folder.exists():
                names.extend(str(p.relative_to(submitted)) for p in folder.rglob('*.py'))
            else: malformed.append('missing '+directory)
        for name in sorted(set(names)):
            src = submitted/name
            if not src.exists():
                malformed.append('missing '+name)
                continue
            if src.is_symlink() or not src.is_file() or any(p.is_symlink() for p in src.parents):
                malformed.append('nonregular '+name); continue
            if src.stat().st_size > spec['limits']['output_bytes']:
                malformed.append('oversized '+name); continue
            dest = source/name
            dest.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(src,dest)
        own(source)
        log = open(args.scratch/'compile.log','wb')
        p = subprocess.Popen([sys.executable,'-I','-m','compileall','-q',str(source)],
            env=clean_env(source),cwd=source,stdout=log,stderr=log,preexec_fn=demote,start_new_session=True)
        try: compilation=p.wait(timeout=spec['limits']['compile_timeout_sec'])
        except subprocess.TimeoutExpired: compilation=-999
        finally: stop(p);log.close()
        raw['compile_exit']=compilation
        seal(source)
        def campaign(label,src=source):
            c = Campaign(args.scratch/label,src,args.private/'service',args.private,spec['limits'])
            return c
        def execute(c,**kw):
            c.start(**kw); return c.wait()
        def equal(c,oracle):
            return (c.semantic_audit()==oracle['audit'] and c.state()==oracle['state']
                    and c.summary()==oracle['summary'])
        # This oracle is the unmodified production CLI with only a disclosed None-GC
        # logging fix. It is rebuilt separately; no recovery implementation creates
        # expected requests or resource state.
        trusted = args.scratch/'trusted'
        shutil.copytree(args.private/'base/restler', trusted);seal(trusted)
        c=campaign('native-oracle',trusted)
        try:
            c.open_gateway()
            rc=execute(c,recovery=False)
            oracle={'audit':c.semantic_audit(),'state':c.state(),'summary':c.summary()}
            c.save_audit()
            if rc or not oracle['audit'] or not any(x['method']=='DELETE' and x['status']==204 for x in oracle['audit']):
                raise RuntimeError('trusted native campaign failed; inspect native-oracle log')
            raw['native_operations']=len(oracle['audit'])
            raw['native_live_resources']=len(oracle['state'])
        finally:c.close()
        if not malformed and compilation==0:
            c=campaign('legacy')
            try:
                c.open_gateway();rc=execute(c,recovery=False)
                groups['legacy_native_campaign']=rc==0 and equal(c,oracle)
                c.save_audit()
            finally:c.close()
            c=campaign('fresh')
            try:
                c.open_gateway();rc=execute(c)
                fresh=rc==0 and equal(c,oracle)
                groups['fresh_durable_campaign']=fresh
                n,hits=len(c.gateway.audit),c.gateway.hits
                rc=execute(c,resume=True)
                alias_dict=c.client/'same-contents.json'
                alias_dict.write_bytes((c.public/'dictionary.json').read_bytes())
                alias_grammar=c.client/'same_grammar.py'
                alias_grammar.write_bytes((c.public/'campaign_grammar.py').read_bytes())
                alias_rc=execute(c,resume=True,dictionary=alias_dict,grammar=alias_grammar)
                groups['completed_resume_no_wire']=fresh and rc==0 and alias_rc==0 and len(c.gateway.audit)==n and c.gateway.hits==hits
                # Same contents under a changed path are allowed. Changed contents
                # are rejected before sending; this tests the real CLI boundary.
                changed=c.client/'different-dictionary.json'
                changed.write_text('{"restler_fuzzable_string":["changed"]}')
                os.chmod(changed,0o644)
                rc=execute(c,resume=True,dictionary=changed)
                groups['configuration_binding']=fresh and rc!=0 and len(c.gateway.audit)==n and c.gateway.hits==hits
                c.save_audit()
            finally:c.close()
            delete_at=next(i+1 for i,a in enumerate(oracle['audit']) if a['method']=='DELETE')
            for label,ordinal,group,torn in [
                ('kill-create',spec['faults']['create_ordinal'],'pending_create_after_kill',False),
                ('kill-delete',delete_at,'dependency_and_delete_recovery',False),
                ('torn',delete_at,'torn_tail_and_snapshot_fallback',True)]:
                c=campaign(label)
                try:
                    c.open_gateway(fault=ordinal);first=execute(c)
                    fired=c.gateway.fired.is_set()
                    stop(c.backend);c.start_backend() # same native service, same persistent SQLite
                    if torn:
                        journal=c.client/'recovery/journal.jsonl'
                        if journal.exists():
                            with open(journal,'ab') as f:f.write(spec['faults']['torn_suffix'].encode())
                        ckpt=c.client/'recovery/checkpoint.json'
                        if ckpt.parent.exists():ckpt.write_bytes(b'{broken')
                    rc=execute(c,resume=True)
                    groups[group]=(fired and first!=0 and rc==0 and equal(c,oracle) and c.gateway.hits==1)
                    diagnostics[label]={'first_exit':first,'resume_exit':rc,'fault_fired':fired,'ledger_hits':c.gateway.hits}
                    c.save_audit()
                finally:c.close()
            c=campaign('drop')
            try:
                c.open_gateway(drop=spec['faults']['drop_ordinal']);rc=execute(c)
                groups['lost_response_same_process']=rc==0 and equal(c,oracle) and c.gateway.hits==1
                c.save_audit()
            finally:c.close()
            c=campaign('uuid')
            try:
                grammar=c.client/'uuid_grammar.py'
                # Exercise the native UUID primitive, not a synthetic UUID helper.
                grammar.write_text((args.private/'campaign_grammar.py').read_text().replace(
                    "p.restler_fuzzable_string('entry', quoted=False)","p.restler_fuzzable_uuid4('unused', quoted=False)"))
                c.open_gateway(fault=spec['faults']['uuid_ordinal']);first=execute(c,grammar=grammar)
                rc=execute(c,resume=True,grammar=grammar)
                bodies=[json.loads(a['body'])['body'] for a in c.gateway.audit if a['method']=='POST']
                native_uuid=campaign('native-uuid-oracle',trusted)
                try:
                    native_uuid.open_gateway()
                    native_rc=execute(native_uuid,recovery=False,grammar=grammar)
                    if native_rc: raise RuntimeError('trusted native UUID campaign failed')
                    def canonical(value):
                        return re.sub(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}',
                                      '<UUID>',json.dumps(value,sort_keys=True))
                    groups['uuid_replay']=(c.gateway.fired.is_set() and first!=0 and rc==0 and c.gateway.hits==1
                        and len(set(bodies))>1 and canonical(c.semantic_audit())==canonical(native_uuid.semantic_audit())
                        and canonical(c.state())==canonical(native_uuid.state()) and c.summary()==native_uuid.summary())
                    native_uuid.save_audit()
                finally:native_uuid.close()
                c.save_audit()
            finally:c.close()
            c=campaign('corruption')
            try:
                c.open_gateway(fault=spec['faults']['create_ordinal']);execute(c)
                journal=c.client/'recovery/journal.jsonl'
                existed=journal.exists()
                if existed:
                    data=bytearray(journal.read_bytes());data[spec['faults']['corrupt_byte_offset']]=ord('!');journal.write_bytes(data)
                n,hits=len(c.gateway.audit),c.gateway.hits
                rc=execute(c,resume=True)
                groups['corrupt_journal_fails_closed']=existed and rc!=0 and n==len(c.gateway.audit) and hits==c.gateway.hits
                c.save_audit()
            finally:c.close()
            c=campaign('owner')
            try:
                c.open_gateway()
                # Stop the first process synchronously once it owns the first intent.
                original=c.gateway.kill
                holder=[]
                c.gateway.fault_at=1
                c.gateway.kill=lambda:(os.killpg(holder[0].pid,signal.SIGSTOP),holder.append(True))
                holder.append(c.start())
                first=holder[0]
                for _ in range(500):
                    if len(holder)>1 or first.poll() is not None:break
                    import time;time.sleep(.01)
                ready=len(holder)>1
                n,hits=len(c.gateway.audit),c.gateway.hits
                rc=execute(c,resume=True)
                groups['exclusive_owner']=ready and rc!=0 and len(c.gateway.audit)==n and c.gateway.hits==hits
                stop(first)
                c.save_audit()
            finally:c.close()
            c=campaign('unsupported')
            try:
                c.open_gateway()
                exits=[]
                for extra in (['--fuzzing_jobs','2'],['--fuzzing_mode','random-walk'],['--garbage_collection_interval','30']):
                    exits.append(execute(c,extra=extra))
                groups['unsupported_options_fail_closed']=(groups['fresh_durable_campaign']
                    and all(x!=0 for x in exits) and not c.gateway.audit)
            finally:c.close()
        diagnostics['invalid_submission']=malformed
        checks=[{'name':name,'passed':bool(value)} for name,value in groups.items()]
        score=sum(g['weight'] for g in spec['groups'] if groups[g['name']])
        report={'valid':True,'score':score,'pass_rate':sum(groups.values())/len(groups),
                'checks':checks,'metrics':raw,'diagnostics':diagnostics}
        (args.output/'score.json').write_text(json.dumps(report,indent=2)+'\n')
        (args.output/'reward.txt').write_text(f'{score!r}\n')
        print(json.dumps(report))
        return 0
    except Exception:
        for name in ('reward.txt','reward.json'):(args.output/name).unlink(missing_ok=True)
        report={'valid':False,'score':None,'error':traceback.format_exc()}
        (args.output/'score.json').write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps(report))
        return 2

if __name__=='__main__':sys.exit(main())
