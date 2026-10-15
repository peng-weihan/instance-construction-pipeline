"""Post-hoc easy-class ablation; never changes a running task or its scores."""
import csv
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'runs/remaining-three-001/science-easy-ablation-20261015'
raw_path = OUT / 'raw-diagnostics.json'
data = json.loads(raw_path.read_text())
records = sorted(data['entries'], key=lambda x: x['entry']['snapshot_time_seconds'])
names = json.loads((ROOT / 'samples/remaining-three-built-001/singlecell_cross_site_graph_lab-r1/public/classes.json').read_text())
times = np.array([r['entry']['snapshot_time_seconds'] / 3600 for r in records])
original = np.array([r['entry']['score'] for r in records])
assert len(records) and np.isfinite(original).all()
batch_names = [b['batch'] for b in records[0]['raw_metrics']['batches']]
assert all([b['batch'] for b in r['raw_metrics']['batches']] == batch_names for r in records)
f1 = np.array([[b['f1_by_class'] for b in r['raw_metrics']['batches']] for r in records])
confusion = np.array([[b['confusion'] for b in r['raw_metrics']['batches']] for r in records])
support = confusion.sum(axis=3)
assert np.array_equal(support, np.broadcast_to(support[0], support.shape))
present = support[0] > 0
tp = np.diagonal(confusion, axis1=2, axis2=3)
den = support + confusion.sum(axis=2)
recomputed_f1 = np.divide(2 * tp, den, out=np.zeros_like(tp, dtype=float), where=den > 0)
assert np.max(np.abs(recomputed_f1 - f1)) < 1e-12

def score(mask):
    assert all(mask.sum(axis=1) > 0)
    return np.mean([(f1[:, b, mask[b]]).mean(axis=1) for b in range(len(batch_names))], axis=0)

assert np.max(np.abs(score(present) - original)) < 1e-12
early = np.flatnonzero(times <= 1)
assert early.size
anchor = early[np.argmax(original[early])]
variants = {'original': {'mask': present, 'scores': original, 'threshold': None}}
for threshold in [.80, .90, .95]:
    mask = present & (f1[anchor] < threshold)
    variants[f'drop_easy_{threshold:.2f}'] = {'mask': mask, 'scores': score(mask), 'threshold': threshold}

summary = {'observed_utc': data['observed_utc'], 'source': data['source'],
    'raw_sha256': hashlib.sha256(raw_path.read_bytes()).hexdigest(),
    'history_sha256': data['history_sha256'], 'valid_submissions': len(records),
    'latest_scored_snapshot_hours': float(times[-1]), 'formal_acceptance': False,
    'analysis_type': 'post-hoc diagnostic; existing policy optimized original reward',
    'selection_rule': 'At the original-score best submission within first hour, exclude supported batch-class terms with F1 >= threshold. Mask fixed thereafter. Three thresholds reported without picking a winner.',
    'anchor': {'round': records[anchor]['entry']['round'], 'hours': float(times[anchor]), 'score': float(original[anchor])},
    'aggregation': 'equal batch mean of retained supported-class F1; full original confusion matrices retained, including all false positives',
    'variants': {}}
curve_rows = []
for key, v in variants.items():
    s = v['scores']; best = np.maximum.accumulate(s)
    improve = np.flatnonzero(np.r_[True, np.diff(best) > 1e-10])
    checkpoints = {str(h): float(best[np.flatnonzero(times <= h)[-1]])
                   for h in [0.5, 1, 2, 3, 4, 5, 6] if times[-1] >= h}
    two = checkpoints.get('2')
    summary['variants'][key] = {'threshold': v['threshold'],
        'retained_terms': int(v['mask'].sum()), 'removed_terms': int((present & ~v['mask']).sum()),
        'best_score': float(best[-1]), 'checkpoints': checkpoints,
        'absolute_gain_after_2h': float(best[-1] - two) if two is not None else None,
        'relative_gain_after_2h': float(best[-1] / two - 1) if two else None,
        'last_improvement_hours': float(times[improve[-1]]),
        'new_highs_after_2h': int((times[improve] > 2).sum()),
        'removed_classes': [{'batch': batch_names[b], 'class_id': int(c), 'name': names[str(c)],
                             'anchor_f1': float(f1[anchor, b, c]), 'support': int(support[0, b, c])}
                            for b, c in zip(*np.where(present & ~v['mask']))]}
    for i, r in enumerate(records):
        curve_rows.append({'variant': key, 'round': r['entry']['round'], 'snapshot_hours': times[i],
                           'score': s[i], 'best_so_far': best[i]})
with (OUT / 'curves.csv').open('w', newline='') as file:
    writer = csv.DictWriter(file, fieldnames=list(curve_rows[0])); writer.writeheader(); writer.writerows(curve_rows)
class_rows = []
at2 = np.flatnonzero(times <= 2); best2 = at2[np.argmax(original[at2])]
best_now = int(np.argmax(original))
for b, c in zip(*np.where(present)):
    class_rows.append({'batch': batch_names[b], 'class_id': int(c), 'name': names[str(c)],
        'support': int(support[0, b, c]), 'f1_1h_original_best': float(f1[anchor, b, c]),
        'f1_2h_original_best': float(f1[best2, b, c]),
        'f1_latest_original_best': float(f1[best_now, b, c]),
        'delta_after_2h_on_original_best': float(f1[best_now, b, c] - f1[best2, b, c])})
with (OUT / 'class_diagnostics.csv').open('w', newline='') as file:
    writer = csv.DictWriter(file, fieldnames=list(class_rows[0])); writer.writeheader(); writer.writerows(class_rows)
easy90 = present & ~variants['drop_easy_0.90']['mask']
delta = f1[best_now] - f1[best2]
easy_contribution = float(np.mean([(delta[b, easy90[b]]).sum() / present[b].sum() for b in range(len(batch_names))]))
hard_contribution = float(np.mean([(delta[b, present[b] & ~easy90[b]]).sum() / present[b].sum() for b in range(len(batch_names))]))
assert abs(easy_contribution + hard_contribution - (original[best_now] - original[best2])) < 1e-12
summary['attribution_original_best_2h_to_current'] = {
    'easy90_contribution': easy_contribution, 'retained_contribution': hard_contribution,
    'interpretation': 'net contributions at original-reward-best submissions, not independent subset optima'}
(OUT / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n')

fig, axes = plt.subplots(1, 2, figsize=(12, 4.6))
colors = ['#333333', '#d17b19', '#2467bd', '#139873']
for (key, v), color in zip(variants.items(), colors):
    best = np.maximum.accumulate(v['scores']); s = summary['variants'][key]
    label = 'Original' if key == 'original' else f'Remove 1h F1 >= {v["threshold"]:.2f} ({s["removed_terms"]} classes)'
    axes[0].step(times, best, where='post', label=label, color=color)
    base = best[np.flatnonzero(times <= 2)[-1]]
    ix = times >= 2
    axes[1].step(np.r_[2, times[ix]], np.r_[0, 100 * (best[ix] - base)], where='post', color=color, label=label)
axes[0].set(xlabel='Snapshot time (hours)', ylabel='Best-so-far macro-F1', ylim=(0, 1), xlim=(0, 6))
axes[1].set(xlabel='Snapshot time (hours)', ylabel='Gain since 2h (percentage points)', xlim=(2, 6))
for ax in axes:
    ax.grid(alpha=.2); ax.spines[['top', 'right']].set_visible(False)
    ax.axvspan(times[-1], 6, color='#eeeeee')
axes[0].legend(fontsize=8, loc='lower right')
fig.suptitle('Science pilot: removing easy class-score terms (post-hoc diagnostic)')
fig.text(.5, .02, f'{len(records)} scored snapshots; observed through {times[-1]:.2f}h. Gray: no scored snapshots. Same trajectory; no retraining.', ha='center', fontsize=9)
fig.tight_layout(rect=[0, .06, 1, .94])
for ext in ['png', 'pdf', 'svg']: fig.savefig(OUT / f'curves.{ext}', dpi=180)

lines = ['# 科学题：移除简单类别后的曲线诊断', '',
    f'数据冻结：{data["observed_utc"]}；{len(records)} 次有效提交，最新已评分快照 {times[-1]:.3f} 小时。', '',
    '这是已有轨迹的事后重算，未改动运行中的任务、奖励或反馈。原始分数与混淆矩阵重算误差小于 1e-12。', '',
    '## 固定筛选规则', '',
    f'取第一小时内原奖励最高的提交（{records[anchor]["entry"]["round"]}，{times[anchor]:.3f}h），将该时刻 F1 ≥ 0.80 / 0.90 / 0.95 的类别分别视为简单类别。三种阈值均报告，筛选不读取一小时后的表现。', '',
    '移除的是宏平均中的类别计分项，保留完整混淆矩阵与全部误分类影响；并未删除细胞样本或重新训练。无真实样本的类别原本就不计入分数。具名 recall pass/fail 是诊断项，不是奖励分母。', '',
    '| 方案 | 保留类别计分项 | 2h最高分 | 当前最高分 | 2h后绝对增长（百分点） | 2h后相对增长 | 最后涨分时间 |',
    '|---|---:|---:|---:|---:|---:|---:|']
for key, s in summary['variants'].items():
    lines.append(f'| {key} | {s["retained_terms"]} | {s["checkpoints"]["2"]:.6f} | {s["best_score"]:.6f} | {s["absolute_gain_after_2h"]*100:.6f} | {s["relative_gain_after_2h"]*100:.6f}% | {s["last_improvement_hours"]:.3f}h |')
lines += ['', '## 本次结论', '',
    '三种删减均没有增强后期增长。删去 F1≥0.80 的8类或 F1≥0.90 的6类后，当前最佳分都在第一小时内取得，2小时后没有新高。删去 F1≥0.95 的4类后，只保留更小的一次后期增长，最后涨分时间也没有推迟。', '',
    f'按原奖励选出的2小时最佳提交和当前最佳提交比较：早期 F1≥0.90 的6类贡献 {easy_contribution*100:+.6f} 个百分点，剩余27类净贡献 {hard_contribution*100:+.6f} 个百分点，合计 {(easy_contribution+hard_contribution)*100:+.6f} 个百分点。部分难类确实提高，但被其他难类退步抵消。', '',
    '这条轨迹的平台不能主要归因为简单项把后期进步稀释；单纯删项无法证明该任务具备6小时持续改进价值。后续应研究困难类别的误差结构与模型实际尝试，再设计有可学习改进空间的跨站点任务。', '',
    '## 如何解读', '',
    '删掉早期高分项可以降低起点、放大其余类别的权重；是否产生更长的增长，要看后期绝对增量和新高时间，不能仅看相对百分比。改变计分项后历史最佳提交会重新选择，因此每个方案独立计算 best-so-far。', '',
    '这不是独立验证或新评分下的真实学习曲线：模型当时只收到原评分反馈。正式修改任务时，应提前固定筛选规则/类别，在新的独立轨迹及未用于筛选的批次上检验。', '',
    '逐类别结果见 class_diagnostics.csv，逐提交曲线见 curves.csv，筛选出的类别与公式见 summary.json。']
(OUT / 'REPORT.md').write_text('\n'.join(lines) + '\n')
print(json.dumps({'anchor': summary['anchor'], 'n': len(records), 'latest_hours': float(times[-1]),
                  'variants': {k: {x: v[x] for x in ['retained_terms', 'removed_terms', 'best_score', 'checkpoints', 'absolute_gain_after_2h', 'relative_gain_after_2h', 'last_improvement_hours', 'new_highs_after_2h']} for k, v in summary['variants'].items()}}, indent=2))
