"""Read-only research extraction from public Docker image layers. Never runs images.

Selected layer members are evidence, not a fully reconstructed OCI filesystem.
All extracted originals stay outside sample/training directories.
"""
import argparse, concurrent.futures, hashlib, io, json, pathlib, tarfile
import requests

ROOT=pathlib.Path(__file__).resolve().parents[1]
OUT=ROOT/'research/comparison-2026-10-14/original_image_metadata'

def run(task,extract,max_layer_bytes=30_000_000,only_layer=None):
    OUT.mkdir(parents=True,exist_ok=True)
    spec=json.loads((ROOT/'data/EdgeBench'/f'{task}.json').read_text())
    repo='seededge/edgebench.work.'+task; tag=spec['work']['image_tag']
    s=requests.Session()
    r=s.get('https://auth.docker.io/token',params={'service':'registry.docker.io','scope':'repository:'+repo+':pull'},timeout=30);r.raise_for_status()
    headers={'Authorization':'Bearer '+r.json()['token'],'Accept':'application/vnd.oci.image.index.v1+json,application/vnd.docker.distribution.manifest.list.v2+json,application/vnd.oci.image.manifest.v1+json,application/vnd.docker.distribution.manifest.v2+json'}
    base='https://registry-1.docker.io/v2/'+repo
    r=s.get(base+'/manifests/'+tag,headers=headers,timeout=30);r.raise_for_status();manifest=r.json()
    if 'manifests' in manifest:
        (OUT/(task+'.index.json')).write_text(json.dumps(manifest,indent=2))
        desc=next(x for x in manifest['manifests'] if x.get('platform',{}).get('architecture')=='amd64' and x.get('platform',{}).get('os')=='linux')
        r=s.get(base+'/manifests/'+desc['digest'],headers=headers,timeout=30);r.raise_for_status();manifest=r.json()
    (OUT/(task+'.json')).write_text(json.dumps(manifest,indent=2))
    config=s.get(base+'/blobs/'+manifest['config']['digest'],headers=headers,timeout=30);config.raise_for_status()
    (OUT/(task+'.config.json')).write_text(json.dumps(config.json(),indent=2))
    layers=manifest.get('layers',[]); found=[]; skipped=[]
    if extract:
        for index,layer in list(enumerate(layers))[-8:]:
            if only_layer is not None and index!=only_layer:continue
            if layer['size']>max_layer_bytes:
                skipped.append({'index':index,'reason':'size limit','bytes':layer['size']});continue
            r=s.get(base+'/blobs/'+layer['digest'],headers=headers,timeout=60);r.raise_for_status();raw=r.content
            assert hashlib.sha256(raw).hexdigest()==layer['digest'].split(':')[1]
            with tarfile.open(fileobj=io.BytesIO(raw),mode='r:*') as tf:
                for m in tf:
                    if not m.isfile() or m.size>2_000_000:continue
                    name=m.name.lstrip('./')
                    if '..' in pathlib.PurePosixPath(name).parts:continue
                    if any(x in name for x in ['.lake/','site-packages/','node_modules/','.git/']):continue
                    keep=(name.endswith(('TODO.md','task_instruction.md','SEBENCH_TASK.md')) or
                          (task=='lean_analysis_proofs' and name.startswith('home/workspace/se-bmk-intern/analysis/') and name.endswith(('.lean','.toml'))) or
                          (task=='portfolio_risk_calibration' and name.startswith('home/workspace/') and name.endswith(('.py','.json','.txt','.md'))))
                    if not keep:continue
                    data=tf.extractfile(m).read();dest=OUT/'author_only'/task/f'layer_{index}'/name
                    dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
                    found.append({'layer':index,'path':name,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
    report={'task':task,'image':repo+':'+tag,'manifest_sha256':hashlib.sha256((OUT/(task+'.json')).read_bytes()).hexdigest(),
            'extraction':'selected layer members, not full OCI filesystem; whiteouts not applied',
            'layers':[{'index':i,'size':l['size'],'digest':l['digest']} for i,l in enumerate(layers)],
            'found':found,'skipped':skipped,'image_executed':False}
    (OUT/(task+'.extraction.json')).write_text(json.dumps(report,indent=2))
    return {'task':task,'layers':len(layers),'found':[(x['layer'],x['path'],x['bytes']) for x in found], 'skipped':skipped}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--extract',action='store_true');p.add_argument('--max-layer-bytes',type=int,default=30_000_000);p.add_argument('--only-layer',type=int);p.add_argument('tasks',nargs='+');a=p.parse_args()
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        futures={pool.submit(run,t,a.extract,a.max_layer_bytes,a.only_layer):t for t in a.tasks}
        for future in concurrent.futures.as_completed(futures):
            try: print(json.dumps(future.result(),ensure_ascii=False),flush=True)
            except Exception as exc: print(json.dumps({'task':futures[future],'error':type(exc).__name__+': '+str(exc)}),flush=True)
