"""Summarize frozen pilot histories; never extend observed runs to six hours."""
import csv
import datetime as dt
import json
import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "runs/remaining-three-001/roll-growth-live-20261015.json"
OUT = ROOT / "runs/remaining-three-001/growth-review-20261015"
OUT.mkdir(exist_ok=True)
data = json.loads(SOURCE.read_text())
observed = dt.datetime.fromisoformat(data["observed_utc"])
titles = {"restler": "软件工程 · 早期 RESTler", "lean": "形式化数学 · Lean",
          "packing": "组合优化 · 不规则排样", "game": "游戏 · Wesnoth",
          "science_live": "科学／机器学习 · 当前运行", "finance_live": "金融 · 当前独立重跑"}
font = font_manager.FontProperties(fname="/System/Library/Fonts/Supplemental/Arial Unicode.ttf")
plt.rcParams.update({"font.family": font.get_name(), "axes.unicode_minus": False,
                     "font.size": 10, "svg.fonttype": "none"})
summary = {"observed_utc": data["observed_utc"], "formal_acceptance": False,
           "score_definition": "best valid completed submission by snapshot time; no score rescaling",
           "tasks": {}}
rows = []
for key, run in data["runs"].items():
    stop = run.get("stop")
    cutoff = (stop["actual_stop_dispatch_elapsed_sec"] if stop else
              (observed - dt.datetime.fromisoformat(run["learning_started_utc"])).total_seconds())
    points, improvements = [], []
    best = -math.inf
    for entry in sorted(run["history"]["entries"], key=lambda e: e["snapshot_time_seconds"]):
        score = entry.get("score")
        if not (entry.get("status") == "completed" and entry.get("valid") is True
                and isinstance(score, (float, int)) and math.isfinite(score)):
            continue
        time = entry["snapshot_time_seconds"]
        if time > cutoff:
            assert stop and entry["kind"] == "final" and not stop["surviving_learning_processes"]
            time = cutoff
        if score > best + 1e-10:
            improvements.append({"hours": time / 3600, "score": score, "round": entry["round"]})
        best = max(best, score)
        points.append((time / 3600, score, best))
        rows.append({"task": key, "round": entry["round"], "snapshot_hours": time / 3600,
                     "feedback_seconds": entry.get("feedback_time_seconds"), "score": score,
                     "best_so_far": best})
    checkpoints = {str(h): max((p[1] for p in points if p[0] <= h), default=None)
                   for h in range(1, 7) if h <= cutoff / 3600 + 1e-6}
    two = checkpoints.get("2")
    summary["tasks"][key] = {"observed_learning_hours": cutoff / 3600,
        "completed_valid_grades": len(points), "best_score": best,
        "checkpoints": checkpoints, "relative_gain_since_2h": best / two - 1 if two else None,
        "last_improvement_hours": improvements[-1]["hours"], "improvements": improvements,
        "host_process_exists": run["host_process_exists"],
        "stop_reason": stop["reason"] if stop else None,
        "history_sha256": run["history_sha256"], "points": points}

fig, axes = plt.subplots(3, 2, figsize=(12, 11), sharex=True, sharey=True)
for ax, (key, title) in zip(axes.flat, titles.items()):
    s = summary["tasks"][key]
    xs, ys, bs = zip(*s["points"])
    end = s["observed_learning_hours"]
    color = "#2467bd" if not key.endswith("live") else "#148574"
    ax.scatter(xs, ys, s=12, color=color, alpha=.23)
    ax.step([*xs, end], [*bs, bs[-1]], where="post", color=color, lw=2.1)
    if end < 5.999:
        ax.axvspan(end, 6, color="#eeeeee")
        ax.axvline(end, color="#999999", ls="--", lw=.8)
    note = f"最高 {s['best_score']:.4f}；最后涨分 {s['last_improvement_hours']:.2f}h"
    if key == "lean":
        note += "\n约28分钟满分；另有 CLI 恢复异常"
    elif key == "restler":
        note += "\n约14分钟满分；4h左右因评分故障中断"
    elif key == "finance_live":
        old = summary["tasks"]["finance_previous"]
        ox, _, ob = zip(*old["points"])
        ax.step([*ox, old["observed_learning_hours"]], [*ob, ob[-1]], where="post",
                color="#b18a58", lw=1.2, ls="--", label="前次金融（4h13m中断）")
        ax.legend(fontsize=8, frameon=False, loc="lower right")
    ax.text(.03, .07, note, transform=ax.transAxes, fontsize=9,
            bbox={"facecolor": "white", "edgecolor": "none", "alpha": .85})
    ax.set_title(title)
    ax.set_xlim(0, 6.1)
    ax.set_ylim(0, 1.05)
    ax.set_xticks(range(7))
    ax.grid(alpha=.18)
    ax.set_xlabel("学习时间（小时）")
    ax.set_ylabel("原始归一化奖励")
    ax.spines[["top", "right"]].set_visible(False)
cst = observed.astimezone(dt.timezone(dt.timedelta(hours=8)))
fig.suptitle(f"真实解题轨迹 · gpt-6.1-sol · 截至 {cst:%m-%d %H:%M} 北京时间", fontsize=15)
fig.text(.5, .012, "实线为有效提交的历史最高分，淡点为各次得分；灰区无观测，未补齐到6小时。\n"
         "按快照时点回溯；冻结后的final归入学习截止点。单条轨迹不代表三次均值或独立审计集成绩。",
         ha="center", fontsize=9, color="#555555")
fig.tight_layout(rect=[0, .055, 1, .96])
for suffix in ["png", "pdf", "svg"]:
    fig.savefig(OUT / f"learning_curves.{suffix}", dpi=170)
with (OUT / "submissions.csv").open("w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0]))
    w.writeheader()
    w.writerows(rows)
for s in summary["tasks"].values():
    del s["points"]
(OUT / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({k: {x: v[x] for x in ["best_score", "relative_gain_since_2h", "last_improvement_hours"]}
                  for k, v in summary["tasks"].items()}, ensure_ascii=False, indent=2))
