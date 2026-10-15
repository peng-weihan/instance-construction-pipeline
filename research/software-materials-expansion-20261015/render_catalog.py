"""Render the catalog from the validated material registry."""
from collections import Counter
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ROUTES = {
    'M1': '产品演进：交付完整产品里程碑',
    'M2': '系统能力：规格驱动的完整子系统',
    'M3': '性能优化：保持正确性的资源取舍',
    'M4': '实现恢复：恢复关联实现与生命周期',
    'M5': '行为兼容：重实现可观察工作流',
}
LABELS = {
    'build_scope_probe': '先验证范围',
    'hold': '暂缓，先排查现有能力',
    'hold_until_baseline': '待强性能基线',
    'hold_wrapper_probe': '待包装基线',
    'hold_harness_probe': '待可重复判据',
    'hold_scope_probe': '待范围收敛',
    'hold_toolchain_probe': '待离线工具链',
}


def main():
    items = json.loads((ROOT / 'candidates.json').read_text())['candidates']
    counts = Counter(x['priority'] for x in items)
    lines = [
        '# 软件工程出题素材：50 项总目录', '',
        '调研日期：2026-10-15。本批从原有 15 项扩充至 50 项，新增 35 个主仓库。', '',
        '目录序号 1–50 用于浏览；素材 ID 沿用此前登记的 28–77。每行素材卡包含已有能力、'
        '拟交付范围、端到端场景、正常基线、首个否证探针、独立判据、许可和离线风险；'
        '固定源码链接到本次保存的 commit。', '',
        f"初筛：**{counts['build_scope_probe']} 项先验证范围，"
        f"{len(items)-counts['build_scope_probe']} 项暂缓并优先排查基线或工具链**。"
        '所有范围均为研究假设，尚未构题或验证长程难度。五类各 10 项用于扩展覆盖，'
        '不代表原题比例或正式出题配额。', '',
        '[调研报告](REPORT.md) · [CSV](candidates.csv) · [JSON](candidates.json) · '
        '[完整性检查](inventory-check.json)', '',
    ]
    for route, title in ROUTES.items():
        lines += [f'## {route} {title}', '',
                  '| 序号 | 来源与证据 | 可细化的交付方向 | 初筛 |',
                  '|---|---|---|---|']
        for x in items:
            if x['route'] != route:
                continue
            upstream = f"https://github.com/{x['repo']}/tree/{x['revision']}"
            links = f"[{x['repo']}]({upstream}) · [素材卡]({x['card']})"
            task = x['title'].replace('|', chr(92)+'|').replace(chr(10), ' ')
            lines.append(f"| {x['pool_index']} | {links} | {task} | {LABELS[x['priority']]} |")
        lines.append('')
    lines += [
        '## 阅读与筛选', '',
        '优先读素材卡中的已有能力和正常基线。成熟库、原生扩展或简单配置若能完整满足范围，'
        '应停止该设计或换完整交付目标；不能靠禁止普通依赖增加难度。', '',
        '性能方向的 10 项全部等待基线测量。实现恢复方向需要先跑通健康参考，再定义关联缺口。'
        '主仓库互不重复也不保证任务族独立，应另按协议、算法、依赖和测试生成谱系划分。', '',
        'dbt、CEL-Go、Pydantic Core 的迁移或别名已归一，各只计一个来源。'
        '旧仓库材料保留作迁移证据，不额外计数。', '',
    ]
    (ROOT / 'CATALOG_50.md').write_text(chr(10).join(lines))


if __name__ == '__main__':
    main()
