import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'drafts/formal.json'

def add(rows):
    existing = json.loads(OUT.read_text()) if OUT.exists() else []
    by_id = {x['id']: x for x in existing}
    for row in rows:
        ident = row['id']
        manifest = json.loads((ROOT / 'sources' / ident / 'manifest.json').read_text())
        row.update(category='formal', repo=manifest['repo'], revision=manifest['revision'],
                   source_manifest=f'sources/{ident}/manifest.json', card=f'cards/{ident}.md',
                   task_constructed=False, runtime_verified=False, difficulty_verified=False)
        row['read_scope'] = [dict(path=f'sources/{ident}/files/{p}', start=a, end=b, kind=k)
                             for p,a,b,k in row.pop('ranges')]
        row['evidence'] = [dict(path=e['path'], line=e['start'], claim=claim,
            url=f"https://github.com/{row['repo']}/blob/{row['revision']}/"+
                e['path'].split('/files/',1)[1]+f"#L{e['start']}")
            for e,claim in zip(row['read_scope'],row.pop('claims'))]
        row['deliverable'] = row.get('deliverable', '固定定义与命题签名的证明文件、依赖清单和作者侧假设报告；在干净评测进程中重新内核检查。')
        row['grader_plan'] = row.get('grader_plan', 'grader持有独立目标声明，对提交proof进行类型检查；递归检查公理/依赖，拒绝sorryAx、Admitted或新增无证明假设。评分只计预定义引理和终点，不计代码量；另审命题忠实性与非空假设。')
        row['generation_and_split'] = row.get('generation_and_split', '按定义、证明方法和依赖子图划分开发/隐藏目标；改符号或换自然数不计新实例。归一化比较库内同义定理；作者参考证明不进入求解环境，保留普通合法自动化和基础库。')
        hits=[]
        for f in (ROOT/'sources'/ident/'files').rglob('*'):
            if f.is_file() and f.suffix in ['.lean','.v']:
                lines=[i+1 for i,x in enumerate(f.read_text(errors='replace').splitlines())
                       if re.search(r'\b(sorry|axiom|admit|Admitted)\b',x)]
                if lines: hits.append({'path':str(f.relative_to(ROOT)), 'lines':lines})
        row['static_trust_observation']={'lexical_hits_in_acquired_proof_files_including_comments':hits,
            'transitive_axioms_checked':False,'kernel_executed':False,
            'scope':'仅所取文件静态词法扫描；没有命中也不证明传递依赖无公理。'}
        if manifest.get('source_repo_alias'): row['source_repo_alias']=manifest['source_repo_alias']
        by_id[ident]=row
        lines=[f"# {ident.upper()} · {row['name']}",'',f"固定来源：`{row['repo']}` @ `{row['revision']}`。",
            f"具体材料：{row['source_unit']}",f"拟题：{row['title']}",'',f"交付：{row['proposed_task']}",
            f"证明产物：{row['deliverable']}",'', '复杂性来源：']
        lines += ['- '+x for x in row['difficulty_sources']]
        lines += ['',f"正常基线：{row['baseline']}",f"首个探针：{row['first_probe']}",
                  f"淘汰条件：{row['stop_condition']}",'',f"独立评测：{row['grader_plan']}",
                  f"生成与划分：{row['generation_and_split']}",f"谱系/污染：{row['novelty_and_overlap']}",
                  f"离线与计算：{row['offline_and_compute']}",f"许可观察：{row['license_observation']}",
                  f"潜力：{row['potential']}；优先级：{row['priority']}。",
                  '证据：']
        lines += [f"- [{e['claim']}]({e['url']})；实际阅读 {r['start']}–{r['end']} 行。" for e,r in zip(row['evidence'],row['read_scope'])]
        lines += ['','状态：仅获取固定版本的定向片段；未构题、未构建、未执行内核、未校准长程难度。']
        (ROOT/row['card']).write_text('\n'.join(lines)+'\n')
    OUT.write_text(json.dumps(sorted(by_id.values(),key=lambda x:x['id']),ensure_ascii=False,indent=2)+'\n')

if __name__ == '__main__':
    import sys
    for arg in sys.argv[1:]:
        add(json.loads(Path(arg).read_text()))
