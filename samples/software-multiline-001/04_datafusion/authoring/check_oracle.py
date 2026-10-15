from pathlib import Path
import importlib.util,sqlite3,json,hashlib,functools
r=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('workloads',r/'tests/workloads.py');w=importlib.util.module_from_spec(spec);spec.loader.exec_module(w)
checks=[];expected={};near=[]
for s in w.CORRECTNESS:
 rows=[w.row(i,s) for i in range(s['rows'])];db=sqlite3.connect(':memory:');db.execute('create table rows(id integer,key integer,tag text,payload text)');db.executemany('insert into rows values(?,?,?,?)',rows)
 direction='DESC' if s['descending'] else 'ASC';nulls='FIRST' if s['nulls_first'] else 'LAST';tagdir='ASC' if s['descending'] else 'DESC';tagnull='LAST' if s['nulls_first'] else 'FIRST'
 sql=f'SELECT id,key,tag,payload FROM rows ORDER BY key {direction} NULLS {nulls}, tag {tagdir} NULLS {tagnull}, id ASC'
 if s['k'] is not None:sql+=' LIMIT '+str(s['k'])
 independent=[list(x) for x in db.execute(sql)];answer=w.expected(s);assert answer==independent,s['id'];db.close()
 expected[s['id']]=answer;checks.append({'case':s['id'],'rows':s['rows'],'passed':True,'evidence':'Python comparator equals SQLite SQL ORDER BY with explicit null policy','expected_sha256':hashlib.sha256(json.dumps(answer,ensure_ascii=False).encode()).hexdigest()})
 # Semantic classifier probes only: these are not DataFusion solutions or timing controls.
 truncated=answer[:-1]
 wrong={**s,'nulls_first':not s['nulls_first']};wronganswer=w.expected(wrong)
 near.append({'case':s['id'],'short_fetch_rejected':truncated!=answer,'inverted_null_policy_rejected':wronganswer!=answer})
(r/'verifier/private/correctness-expected.json').write_text(json.dumps(expected,ensure_ascii=False)+'\n')
(r/'authoring/evidence/oracle-crosscheck.json').write_text(json.dumps({'checks':checks,'semantic_classifier_probes':near,'scope':'Python workload/oracle check only; no DataFusion binary executed; no performance observation'},indent=2)+'\n')
print(json.dumps({'sqlite_matches':len(checks),'short_fetch_rejections':sum(x['short_fetch_rejected'] for x in near),'null_policy_rejections':sum(x['inverted_null_policy_rejected'] for x in near)}))
