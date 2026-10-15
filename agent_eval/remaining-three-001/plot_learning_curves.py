"""Plot observed pilot submissions without extrapolating interrupted runs."""
from pathlib import Path
import csv
import argparse
import hashlib
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "runs/remaining-three-001/current-review"
parser = argparse.ArgumentParser()
parser.add_argument("--all", action="store_true")
args = parser.parse_args()
OUT = SOURCE / ("all-curves" if args.all else "curves")
OUT.mkdir(exist_ok=True)
font = font_manager.FontProperties(fname="/System/Library/Fonts/Supplemental/Arial Unicode.ttf")
plt.rcParams.update({"font.family": font.get_name(), "axes.unicode_minus": False,
                     "font.size": 11, "svg.fonttype": "none"})
kinds = ["restler", "lean", "packing", "game", "finance"] if args.all else ["game", "finance"]
titles = {"restler": "软件工程 · RESTler", "lean": "形式化数学 · Lean", "packing": "组合优化 · 不规则排样",
          "game": "游戏 · Wesnoth 战术策略", "finance": "金融 · 跨资产配置"}
fig, grid = plt.subplots(3 if args.all else 1, 2, figsize=(13, 13 if args.all else 5.5), sharex=True, sharey=True)
axes = grid.flatten()
colors = {"game": "#2467bd", "finance": "#13826d", "restler": "#a45b1e", "lean": "#8154ad", "packing": "#287b91"}
report = {"time_axis": "snapshot capture time, hours since learning start",
          "score": "original normalized score, no transformation",
          "final_snapshot": "After confirmed process freeze, final capture is mapped to the learning cutoff; no extra learning time.",
          "formal_acceptance": False, "tasks": {}}
all_rows = []
for ax, kind in zip(axes, kinds):
    title = titles[kind]
    history_path = SOURCE / kind / "history.json"
    stop_path = SOURCE / kind / "cloud-learning-stop.json"
    history = json.loads(history_path.read_text())
    stop = json.loads(stop_path.read_text())
    cutoff = stop["actual_stop_dispatch_elapsed_sec"] / 3600
    assert not stop["surviving_learning_processes"]
    entries = sorted(history["entries"], key=lambda e: e["snapshot_time_seconds"])
    xs, ys, bests, feedbacks = [], [], [], []
    best = 0.0
    for e in entries:
        raw_time = e["snapshot_time_seconds"] / 3600
        if raw_time > cutoff + .00001:
            assert e["kind"] == "final", "Unexpected post-cutoff learning submission"
        t = min(raw_time, cutoff)
        completed = e["status"] == "completed"
        score = e.get("score")
        if completed:
            assert score is not None and 0 <= score <= 1
            best = max(best, score)
            xs.append(t)
            ys.append(score)
            bests.append(best)
            feedbacks.append(e.get("feedback_time_seconds", 0) / 3600)
        all_rows.append({"task": kind, "round": e["round"], "kind": e["kind"],
                         "status": e["status"], "valid": e.get("valid"),
                         "snapshot_hours": raw_time, "plotted_hours": t,
                         "feedback_hours": e.get("feedback_time_seconds", 0) / 3600,
                         "score": score, "best_so_far": best if completed else None})
    ax.scatter(xs, ys, s=13, c=colors[kind], alpha=.23, linewidths=0,
               label="每次提交得分", zorder=2)
    ax.step(xs + [cutoff], bests + [bests[-1]], where="post", linewidth=2.5,
            color=colors[kind], label="历史最高分", zorder=3)
    checkpoints = {}
    for hour in [1, 2, 3, 4, 5, 6]:
        if hour > cutoff + .001:
            continue
        eligible = [y for x, y in zip(xs, ys) if x <= hour]
        if eligible:
            checkpoints[str(hour)] = max(eligible)
    for hour in [1, 2, 4, 6]:
        if str(hour) in checkpoints:
            val = checkpoints[str(hour)]
            ax.plot(hour, val, "o", color=colors[kind], ms=5, zorder=4)
            ax.annotate(f"{val:.4f}", (hour, val), xytext=(-17 if hour == 6 else 0, 12),
                        textcoords="offset points", ha="center", fontsize=10, color=colors[kind])
    if kind in ["finance", "restler"]:
        ax.axvspan(cutoff, 6, facecolor="#f1f1f1", zorder=0)
        ax.axvline(cutoff, color="#bd4d42", linestyle="--", linewidth=1.3)
        ax.text(cutoff + .1, .23, ("4小时13分中断\nDocker / systemd 故障" if kind == "finance" else "4小时01分中断\n离线评分故障") + "\n后续无观测数据",
                color="#a03b32", fontsize=10, va="center")
        if kind == "finance":
            ax.annotate(f"最高 {best:.4f}", (2.4492, best), xytext=(2.55, .49),
                        arrowprops={"arrowstyle": "->", "color": colors[kind]},
                        fontsize=11, color=colors[kind])
        else:
            ax.text(.2, .54, "约14分钟即达满分\n现版本难度不足", color=colors[kind])
    elif kind == "game":
        ax.text(.16, .19, "2→6小时：相对提升 11.02%\n约3.35小时出现明显跃升", fontsize=11,
                color=colors[kind], bbox={"facecolor": "white", "edgecolor": "none", "alpha": .9})
    elif kind == "lean":
        ax.text(.2, .5, "首小时内已达满分\n6小时窗口内 CLI 启动1799次\n恢复异常，不能视为持续正常解题", color=colors[kind], fontsize=10)
    elif kind == "packing":
        gain = checkpoints["6"] / checkpoints["2"] - 1
        ax.text(.2, .76, f"2→6小时：相对提升 {gain:.2%}\n后半程有明显进步", color=colors[kind])
    ax.set_title(title, fontsize=14, pad=13, weight="bold")
    ax.set_xlim(0, 6.15)
    ax.set_ylim(0, 1.1)
    ax.set_xticks(range(7))
    ax.set_xlabel("交互时间（小时）")
    ax.grid(alpha=.18)
    ax.spines[["top", "right"]].set_visible(False)
    if not args.all:
        ax.legend(loc="lower right", frameon=False, fontsize=10)
    report["tasks"][kind] = {"learning_hours": cutoff, "best_score": best,
        "completed_grades": len(xs), "checkpoints_by_snapshot_hour": checkpoints,
        "stop_reason": stop["reason"], "history_sha256": hashlib.sha256(history_path.read_bytes()).hexdigest(),
        "stop_record_sha256": hashlib.sha256(stop_path.read_bytes()).hexdigest()}
for ax in axes[::2]:
    ax.set_ylabel("归一化奖励（0–1，越高越好）")
for ax in axes[len(kinds):]:
    ax.axis("off")
    science_status = SOURCE.parent / "science-startup-status.json"
    science = json.loads(science_status.read_text()) if science_status.exists() else {}
    text = "科学／机器学习：正在准备启动\n尚无真实 agent 评分曲线"
    if science.get("learning_started_cst"):
        text = "科学／机器学习：已启动首条轨迹\n" + science["learning_started_cst"] + "（北京时间）\n尚无完整学习曲线"
    ax.text(.08, .7, text, transform=ax.transAxes, fontsize=13, color="#555555")
fig.suptitle(("五题" if args.all else "两题") + "真实轨迹的学习曲线 · gpt-6.1-sol", fontsize=17, y=.99 if args.all else .98)
if args.all:
    from matplotlib.lines import Line2D
    fig.legend(handles=[Line2D([],[],color="#555555",lw=2.5,label="历史最高分"),
                        Line2D([],[],color="#888888",marker="o",linestyle="none",alpha=.4,label="每次提交得分")],
               loc="upper center",bbox_to_anchor=(.5,.965),ncol=2,frameon=False)
fig.text(.5, .015 if args.all else .025, "横轴按提交快照时间；粗线为截至该时点提交的最好成绩，淡点为各次得分；灰区没有观测数据。\n"
         "每题仅展示1条轨迹；不代表三次均值或独立审计集结果。Lean 的六小时窗口存在大量恢复异常。" if args.all else
         "横轴按提交快照时间；粗线为截至该时点提交的最好成绩，淡点为各次得分。\n每题仅1条轨迹；金融未满6小时；本图不代表三次均值或独立审计集结果。", ha="center", fontsize=10, color="#555555")
fig.tight_layout(rect=[0, .055 if args.all else .11, 1, .96 if args.all else .92])
for suffix in ["png", "pdf", "svg"]:
    fig.savefig(OUT / f"learning_curves.{suffix}", dpi=190, facecolor="white")
with (OUT / "submissions.csv").open("w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=list(all_rows[0]))
    writer.writeheader()
    writer.writerows(all_rows)
(OUT / "curve_summary.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
print(json.dumps(report, ensure_ascii=False, indent=2))
