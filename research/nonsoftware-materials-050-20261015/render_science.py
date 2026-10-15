"""Render source-grounded science cards, updating the pool one item at a time."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent

def add(raw):
    item = dict(raw)
    identity = json.loads((ROOT / 'sources' / item['id'] / 'manifest.json').read_text())
    item.update(category='science', repo=identity['repo'], revision=identity['revision'],
        source_manifest=f"sources/{item['id']}/manifest.json", card=f"cards/{item['id']}.md",
        task_constructed=False, runtime_verified=False, difficulty_verified=False)
    item['evidence'] = []
    item['read_scope'] = []
    for path, start, end, kind, claim in item.pop('segments'):
        local = f"sources/{item['id']}/files/{path}"
        url = f"https://github.com/{item['repo']}/blob/{item['revision']}/{path}#L{start}-L{end}"
        item['evidence'].append(dict(path=local, line=start, claim=claim, url=url))
        item['read_scope'].append(dict(path=local, start=start, end=end, kind=kind))
    path = ROOT / 'drafts/science.json'
    items = json.loads(path.read_text()) if path.exists() else []
    items = [old for old in items if old['id'] != item['id']] + [item]
    items.sort(key=lambda entry: entry['id'])
    path.write_text(json.dumps(items, ensure_ascii=False, indent=2) + '\n')
    lines = [f"# {item['id'].upper()} · {item['name']}", '',
        f"- 主来源：[{item['repo']}](https://github.com/{item['repo']}/tree/{item['revision']})。",
        f"- 固定版本：`{item['revision']}`。",
        f"- 来源单元：{item['source_unit']}",
        f"- 评估：`{item['potential']}`；优先级 `{item['priority']}`。", '',
        f"**拟题：{item['title']}**", item['proposed_task'],
        f"交付：{item['deliverable']}", '', '**困难的因果来源**']
    lines += [f"- {x}" for x in item['difficulty_sources']]
    lines += ['', f"基线：{item['baseline']}", f"首轮探针：{item['first_probe']}",
        f"淘汰/降档：{item['stop_condition']}", '',
        f"独立评分：{item['grader_plan']}",
        f"生成与划分：{item['generation_and_split']}",
        f"独立性与谱系：{item['novelty_and_overlap']}",
        f"离线/计算：{item['offline_and_compute']}",
        f"许可观察：{item['license_observation']}", '', '**实际选读证据**']
    for e,s in zip(item['evidence'],item['read_scope']):
        lines += [f"- [{e['claim']}]({e['url']})；本地 [选读 {s['start']}–{s['end']} 行](../{s['path']})。"]
    lines += ['', '状态：仅来源、定向选读和设计假设；未构题、未运行候选、未校准长程难度。']
    (ROOT / item['card']).write_text('\n'.join(lines) + '\n')
    print(item['id'], item['priority'], len(lines), 'lines')

if __name__ == '__main__':
    import sys
    for name in sys.argv[1:]:
        add(json.loads(Path(name).read_text()))
