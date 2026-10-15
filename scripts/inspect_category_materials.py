"""Static construction inventory only. Never executes a task or verifier."""
from pathlib import Path
import ast, csv, hashlib, json, re, sys, xml.etree.ElementTree as ET

root=Path(sys.argv[1]).resolve()
checks=[]
def check(name, passed, evidence):
    checks.append({'name':name,'pass':bool(passed),'evidence':evidence})

index=json.loads((root/'index.json').read_text())
check('six_categories',len(index)==6 and len({x['category'] for x in index})==6,len(index))
for item in index:
    p=root/item['task_id']; tag=p.name
    for name in ['construction.json','public/instruction.md','public/evaluation_contract.draft.json','SOURCE_TO_TASK.md','file_manifest.json']:
        check(tag+'/'+name,(p/name).is_file(),str(p/name))
    manifest=json.loads((p/'file_manifest.json').read_text())
    mismatches=[]
    for rec in manifest:
        f=p/rec['path']
        if not f.is_file() or hashlib.sha256(f.read_bytes()).hexdigest()!=rec['sha256']: mismatches.append(rec['path'])
    check(tag+'/manifest_hashes',not mismatches,{'files':len(manifest),'mismatches':mismatches})
    contract=json.loads((p/'public/evaluation_contract.draft.json').read_text())
    check(tag+'/submission_paths',all((p/'public'/x).exists() for x in contract['submit_paths']),contract['submit_paths'])
    check(tag+'/draft_status',item['accepted'] is False and item['runtime_verified'] is False,item['status'])
    check(tag+'/no_git_in_public',not any((p/'public').rglob('.git')),'public is a source snapshot')
    f=p/'private/ablation_manifest.json'
    if f.exists():
        records=json.loads(f.read_text());count=0
        for rel in {r['file'] for r in records}:
            tree=ast.parse((p/'public/repo'/rel).read_text())
            count+=sum(isinstance(n,ast.Raise) and 'NotImplementedError' in ast.unparse(n) for n in ast.walk(tree))
        check(tag+'/nine_function_holes',count==9,{'holes':count,'removed_lines':sum(r['removed_lines'] for r in records)})
    f=p/'private/targets.json'
    if f.exists():
        targets=json.loads(f.read_text());rel=targets[0]['file'];text=(p/'public/repo'/rel).read_text()
        check(tag+'/sixteen_proof_holes',len(re.findall(r'(?m)^  sorry$',text))==16,len(targets))
        check(tag+'/signatures_preserved',all(t['signature'] in text for t in targets),'literal original signatures')
    f=p/'private/case_manifest.json'
    if f.exists():
        cases=json.loads(f.read_text());ids=[r['id'] for r in cases]
        check(tag+'/case_source_partition',len(ids)==len(set(ids))==9,{s:sum(r['split']==s for r in cases) for s in ['public','feedback','final']})
        check(tag+'/nonzero_geometry',all(r['total_item_area']>0 and r['maximum_length']>r['area_lower_bound_length'] for r in cases),'area bound sanity only; no collision checks')
    f=p/'private/split_manifest.json'
    if f.exists():
        splits=json.loads(f.read_text())['splits']
        check(tag+'/chronological_partition',splits['public']['last']<splits['feedback']['first'] and splits['feedback']['last']<splits['final']['first'],splits)
    f=p/'private/data_generation.json'
    if f.exists():
        d=json.loads(f.read_text()); check(tag+'/synthetic_label',d['synthetic'] and not d['observed_field_data'],d['counts'])
        for split,count in d['counts'].items():
            where='public' if split=='public' else 'private'
            rows=list(csv.DictReader((p/where/f'{split}_observations.csv').open()))
            check(tag+'/'+split+'_row_count',len(rows)==count,len(rows))
    f=p/'private/map_manifest.json'
    if f.exists():
        maps=json.loads(f.read_text());collisions=[]
        for m in maps:
            folder='public/maps' if m['split']=='public' else 'private/'+m['split']+'_maps'
            tree=ET.parse(p/folder/m['id']).getroot(); n=int(tree.attrib['width']); terrain=tree.find('terrain').text
            coords=[]
            for u in tree.find('units'):
                x,y=int(u.attrib['x']),int(u.attrib['y']);coords.append((x,y))
                if not(0<=x<n and 0<=y<n) or terrain[y*n+x]!='0':collisions.append(m['id'])
            if len(set(coords))!=len(coords):collisions.append(m['id'])
        check(tag+'/map_format_and_initial_occupancy',not collisions,{'maps':len(maps),'bad':collisions,'not_checked':'pathfinding, fairness, game dynamics'})
report={'scope':'static material integrity; not runtime verification or acceptance',
        'checks':checks,'passed':sum(c['pass'] for c in checks),'total':len(checks),
        'runtime_validation_runs':0,'difficulty_claim':'uncalibrated'}
(root/'material_inventory_check.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k!='checks'},ensure_ascii=False))
for c in checks:
    if not c['pass']:print('FAIL',c['name'],c['evidence'])
sys.exit(0 if all(c['pass'] for c in checks) else 1)
