"""Render curated game and knowledge-source cards; never execute acquired sources."""
import collections
import datetime as dt
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def render(input_files, output, category):
    specs = []
    for filename in input_files:
        specs.extend(json.loads((ROOT / 'drafts' / filename).read_text()))
    rows = []
    scope_lines = [f'# {category}: 定向研究范围', '',
        '仅覆盖下列实现、原生测试/规格及根README/许可；未全仓通读、未执行候选代码、未构题、未验证运行或长程难度。',
        '官方仓库页面在2026-10-15在线核对；WNTR官方文档确认USEPA/WNTR归属。实际保存正文为固定SHA的README/源码/测试，清单含URL及SHA256。', '']
    for spec in specs:
        item = dict(spec)
        ident = item['id']
        source = ROOT / 'sources' / ident
        manifest = json.loads((source / 'manifest.json').read_text())
        assert not manifest['missing_requested_paths'], ident
        assert not manifest['fetch_errors'], ident
        item.update(category=category, repo=manifest['repo'], revision=manifest['revision'],
            source_manifest=f'sources/{ident}/manifest.json', card=f'cards/{ident}.md',
            task_constructed=False, runtime_verified=False, difficulty_verified=False)
        claims = item.pop('claims')
        scopes = item.pop('read_scope')
        item['read_scope'] = []
        for path, start, end, kind in scopes:
            lines = (source / 'files' / path).read_text().splitlines()
            assert 1 <= start <= end <= len(lines), (ident, path, start, end)
            item['read_scope'].append(dict(path=f'sources/{ident}/files/{path}', start=start, end=end, kind=kind))
        assert len(claims) == len(scopes)
        item['evidence'] = [dict(path=f'sources/{ident}/files/{p}', line=start, claim=claim,
            url=f'https://github.com/{item["repo"]}/blob/{item["revision"]}/{p}#L{start}')
            for (p, start, end, kind), claim in zip(scopes, claims)]
        urls = '；'.join(f'[{i+1}]({e["url"]})' for i, e in enumerate(item['evidence']))
        reads = '；'.join(f'{p}:{start}-{end}' for p, start, end, kind in scopes)
        card = [f'# {ident.upper()} · {item["name"]}', '',
            f'状态：潜力 {item["potential"]} / {item["priority"]}；素材研究，未构题/运行/难度验收。',
            f'来源：[{item["repo"]}](https://github.com/{item["repo"]}/tree/{item["revision"]})',
            f'固定版本：`{item["revision"]}`',
            f'来源单元：{item["source_unit"]}',
            f'材料：[manifest](../{item["source_manifest"]})，含文件树、原文URL和SHA256。', '',
            f'拟题：**{item["title"]}**', item['proposed_task'],
            f'交付：{item["deliverable"]}', '',
            f'自然难点一：{item["difficulty_sources"][0]}',
            f'自然难点二：{item["difficulty_sources"][1]}',
            f'正常基线：{item["baseline"]}',
            f'首个探针：{item["first_probe"]}',
            f'降级/淘汰：{item["stop_condition"]}', '',
            f'独立评分：{item["grader_plan"]}',
            f'生成与划分：{item["generation_and_split"]}',
            f'谱系/污染：{item["novelty_and_overlap"]}',
            f'离线与计算：{item["offline_and_compute"]}',
            f'许可观察：{item["license_observation"]}', '',
            f'证据：{urls}',
            *[f'证据{i+1}：{e["claim"]}' for i, e in enumerate(item['evidence'])],
            f'实际选读：{reads}',
            '覆盖边界：上述定向阅读，不推断整个仓库均已审计。']
        assert 20 <= len(card) <= 35, (ident, len(card))
        (ROOT / item['card']).write_text('\n'.join(card) + '\n')
        scope_lines += [f'## {ident} · {item["name"]}', '',
            f'- 版本：{item["revision"]}；{item["priority"]}。',
            *[f'- `{p}:{start}-{end}` ({kind})' for p, start, end, kind in scopes], '']
        rows.append(item)
    (ROOT / 'drafts' / output).write_text(json.dumps(rows, ensure_ascii=False, indent=2) + '\n')
    (ROOT / 'drafts' / output.replace('.json', '.md')).write_text('\n'.join(scope_lines) + '\n')
    print(json.dumps(dict(output=output, count=len(rows), priorities=dict(collections.Counter(x['priority'] for x in rows))), ensure_ascii=False))


render(['games-spec-a.json', 'games-spec-b.json'], 'games.json', 'games')
render(['knowledge-extra-spec.json'], 'knowledge-extra.json', 'knowledge')
