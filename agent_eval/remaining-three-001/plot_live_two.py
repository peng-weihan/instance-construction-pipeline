"""Fetch and plot observed science/finance-r3 scores, never future results."""
from pathlib import Path
import csv
import datetime as dt
import hashlib
import json
import math
import subprocess

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

ROOT = Path(__file__).resolve().parents[2]
REMOTE = r'''
from pathlib import Path
import datetime,json
root=Path('/ws/users/raymone/edgebench/remaining-three-001')
out={'tasks':{}}
for kind,relative in [('science','science-pilot'),('finance','finance-pilot-r3')]:
 run=root/relative/'run-6h-001'
 m=json.loads((run/'run-manifest.json').read_text())
 events=[json.loads(s) for s in (run/'evaluation/events.jsonl').read_text().splitlines() if s.strip()]
 mapping=[e for e in events if e.get('event')=='cloud_learning_start_mapping'][0]
 stop=run/'evaluation/cloud-learning-stop.json'
 out['tasks'][kind]={'run_root':str(run),'manifest':{k:m.get(k) for k in ['status','pid','model','learning_budget_seconds','evaluation_interval_seconds','started_utc','exit_code']},'host_alive':Path('/proc',str(m.get('pid'))).exists(),'learning_started_utc':mapping['remote_started_utc'],'history':json.loads((run/'evaluation/history.json').read_text()),'stop':json.loads(stop.read_text()) if stop.exists() else None}
now=datetime.datetime.now(datetime.timezone.utc)
out['observed_utc']=now.isoformat()
for item in out['tasks'].values():
 item['elapsed_seconds']=(now-datetime.datetime.fromisoformat(item['learning_started_utc'])).total_seconds()
print(json.dumps(out))
'''


def duration(seconds):
    seconds = int(seconds)
    return f"{seconds//3600}小时{seconds%3600//60:02d}分{seconds%60:02d}秒"


def main():
    cmd = ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=8", "-o", "ControlPath=/tmp/edgebench-raymone-smoke.sock", "root@173.231.10.234", "python3", "-"]
    response = subprocess.run(cmd, input=REMOTE, capture_output=True, text=True, timeout=45, check=True)
    data = json.loads(response.stdout)
    stamp = dt.datetime.fromisoformat(data["observed_utc"]).strftime("%Y%m%dT%H%M%SZ")
    out = ROOT / "runs/remaining-three-001" / ("live-two-" + stamp)
    out.mkdir()
    raw = response.stdout.encode()
    (out / "source-snapshot.json").write_bytes(raw)
    font = font_manager.FontProperties(fname="/System/Library/Fonts/Supplemental/Arial Unicode.ttf")
    plt.rcParams.update({"font.family": font.get_name(), "axes.unicode_minus": False, "font.size": 11, "svg.fonttype": "none"})
    observed = dt.datetime.fromisoformat(data["observed_utc"]).astimezone(dt.timezone(dt.timedelta(hours=8)))
    summary = {"observed_cst": observed.isoformat(), "source_sha256": hashlib.sha256(raw).hexdigest(), "time_axis": "snapshot capture time since actual cloud learning start; feedback time retained in CSV", "future_scores_extrapolated": False, "formal_acceptance": False, "tasks": {}}
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.5), sharex=True, sharey=True)
    xmax = max(1.25, math.ceil(max(x["elapsed_seconds"] for x in data["tasks"].values()) / 900) / 4)
    all_rows = []
    for ax, (kind, task) in zip(axes, data["tasks"].items()):
        alive = task["host_alive"]
        stop = task.get("stop")
        if stop:
            cutoff = stop["actual_stop_dispatch_elapsed_sec"]
        elif alive:
            cutoff = task["elapsed_seconds"]
        else:
            raise RuntimeError(f"{kind}: no live process or confirmed stop evidence; refuse elapsed-time claim")
        history = task["history"]
        entries = sorted(history["entries"], key=lambda e: e.get("snapshot_time_seconds", float("inf")))
        points = []
        best = None
        for e in entries:
            score = e.get("score")
            completed = e.get("status") == "completed" and e.get("valid") is True and isinstance(score, (float, int)) and math.isfinite(score)
            if completed:
                assert 0 <= score <= 1
                t = e["snapshot_time_seconds"]
                assert t <= cutoff + 1, "Unexpected snapshot after observed cutoff"
                best = score if best is None else max(best, score)
                points.append((t / 3600, score, best, e["round"]))
            all_rows.append({"task":kind,"round":e.get("round"),"kind":e.get("kind"),"status":e.get("status"),"valid":e.get("valid"),"snapshot_seconds":e.get("snapshot_time_seconds"),"feedback_seconds":e.get("feedback_time_seconds"),"score":score,"best_so_far":best if completed else None})
        if not points:
            raise RuntimeError(f"{kind}: no valid completed scores")
        xs, ys, bs, labels = zip(*points)
        color = "#2866bc" if kind == "science" else "#148574"
        ax.scatter(xs, ys, color=color, s=22, alpha=.38, label="每次提交得分", zorder=2)
        ax.step([*xs, cutoff / 3600], [*bs, bs[-1]], where="post", color=color, linewidth=2.5, label="历史最高分", zorder=3)
        ax.axvspan(cutoff / 3600, xmax, facecolor="#f1f1f1", zorder=0)
        ax.axvline(cutoff / 3600, color="#888888", linewidth=1, linestyle="--")
        ax.text(.04, .08, f"已运行 {duration(cutoff)}\n有效判分 {len(points)} 次\n当前最高 {max(ys):.4f}", transform=ax.transAxes, color=color, bbox={"facecolor":"white","edgecolor":"none","alpha":.9})
        title = "科学／机器学习 · 单细胞跨站点分类" if kind == "science" else "金融 · 独立重跑（r3）"
        ax.set_title(title, weight="bold", pad=12)
        ax.set_xlim(0, xmax)
        ax.set_ylim(0, 1.03)
        ax.set_xticks([i / 4 for i in range(int(xmax * 4) + 1)])
        ax.set_xlabel("实际学习时间（小时）")
        ax.grid(alpha=.18)
        ax.spines[["top","right"]].set_visible(False)
        ax.legend(loc="upper left", frameon=False)
        checkpoint = {}
        for minute in [15, 30, 45, 60, 90, 120, 240, 360]:
            if minute * 60 > cutoff:
                checkpoint[str(minute)] = None
            else:
                scores = [p[1] for p in points if p[0] * 3600 <= minute * 60]
                checkpoint[str(minute)] = max(scores) if scores else None
        first, last = points[0], points[-1]
        peak = next(p for p in points if p[1] == max(ys))
        start = dt.datetime.fromisoformat(task["learning_started_utc"]).astimezone(dt.timezone(dt.timedelta(hours=8)))
        summary["tasks"][kind] = {"run_root":task["run_root"],"model":task["manifest"]["model"],"host_alive":alive,"learning_started_cst":start.isoformat(),"expected_six_hour_end_cst":(start+dt.timedelta(hours=6)).isoformat(),"elapsed_seconds":cutoff,"elapsed_text":duration(cutoff),"completed_valid_grades":len(points),"first_score":first[1],"first_snapshot_seconds":first[0]*3600,"last_score":last[1],"last_snapshot_seconds":last[0]*3600,"best_score":max(ys),"best_first_snapshot_seconds":peak[0]*3600,"checkpoints_by_minute":checkpoint,"pending_or_invalid_entries":len(entries)-len(points)}
    axes[0].set_ylabel("原始归一化奖励（0–1）")
    fig.suptitle("两条正在运行的真实学习曲线 · gpt-6.1-sol", fontsize=16, y=.98)
    fig.text(.5,.025,f"截至北京时间 {observed:%Y-%m-%d %H:%M:%S}；粗线取已完成有效提交的最高分，淡点为逐次得分。\n横轴按快照时间回溯；灰区尚无观测。每题仅1条轨迹，未到2小时／6小时，不判断后期增长。",ha="center",fontsize=10,color="#555555")
    fig.tight_layout(rect=[0,.12,1,.92])
    for suffix in ("png","pdf","svg"):
        fig.savefig(out / ("learning_curves." + suffix), dpi=180, facecolor="white")
    with (out / "submissions.csv").open("w",newline="") as stream:
        writer=csv.DictWriter(stream,fieldnames=list(all_rows[0]));writer.writeheader();writer.writerows(all_rows)
    (out / "curve_summary.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2)+"\n")
    (ROOT / "runs/remaining-three-001/latest-live-two-curves.json").write_text(json.dumps({"directory":str(out),"observed_cst":summary["observed_cst"]},ensure_ascii=False,indent=2)+"\n")
    print(json.dumps({"directory":str(out),**summary},ensure_ascii=False,indent=2))


if __name__ == "__main__":
    main()
