# 37_tokio 异步运行时的任务、计时器与关闭生命周期恢复

路线：M4；优先级：hold_harness_probe；状态：素材已取、范围待验证。
来源：[tokio-rs/tokio](https://github.com/tokio-rs/tokio/tree/52ac7816230efabcae6fcc09cbe7ae630a48eddf)；固定版本 `52ac7816230efabcae6fcc09cbe7ae630a48eddf`。

**已有能力：** 固定源码已经实现原子任务生命周期、取消、通知和虚拟时间测试；这些是拟保留的gold能力。

**拟交付：** 对健康固定版本构造关联子系统的受控恢复：任务状态、通知/取消、计时器和runtime关闭共同可用。不是为现有Tokio修复一个已知上游bug。

**拟缺口：** 拟选择一组完整生命周期实现作受控缺口，保留公开API、健康I/O和可起步路径；具体mask、参考健康性和实际工作量尚未验证。

**工程链：** spawn/JoinHandle → 原子任务状态 → scheduler通知 → timer → cancellation/shutdown

**原题参照：** Rust multicrate/regex-automata恢复；不能按并发分支数量预言时长。

**三个组合场景（设计）：**

1. 任务等待计时器时取消，再次唤醒不得重复完成，JoinHandle观察到合同内结果。
2. 虚拟时间前进、计时器重设和任务自唤醒交错，完成与资源析构恰当。
3. runtime关闭时有等待、已通知和已完成任务，退出后资源被释放；不要求所有合法执行具有相同poll顺序。

**基础完成后的剩余工作假设：**

- 基本spawn/join恢复后，通知与取消竞争仍需统一状态和引用所有权。
- 单线程计时恢复后，关闭与多线程路径的组合可能需要跨模块修订。

**独立评测：** 原生单线程/虚拟时间回归、选定并发模型检查和独立资源计数；比较合法结果/不变量，不比较偶然调度顺序。

**最强正常基线：** 使用最直接的锁式状态机、正常futures/同步工具或串行调度；若满足完整合同应允许通过。

**首个否证探针：** 先在健康gold重放选定测试多次，证实不依赖wall-clock和偶然调度；再做一份独立锁式实现，评估是否快速闭合。

**许可观察：** 根LICENSE为MIT；依赖及分发闭包后续逐项记录。

**离线和资源：** Rust vendor与MSRV未验证；OS reactor及线程模型需分别验证Linux x86/ARM。并发检查不可把概率性失败写成确定奖励。

**已读证据：**

- [running/idle、通知、取消和引用计数协同](../sources/37_tokio/files/tokio/src/runtime/task/state.rs#L117) / [固定上游](https://github.com/tokio-rs/tokio/blob/52ac7816230efabcae6fcc09cbe7ae630a48eddf/tokio/src/runtime/task/state.rs#L117)
- [原生暂停时间与计时器测试](../sources/37_tokio/files/tokio/tests/time_sleep.rs#L21) / [固定上游](https://github.com/tokio-rs/tokio/blob/52ac7816230efabcae6fcc09cbe7ae630a48eddf/tokio/tests/time_sleep.rs#L21)

定向阅读范围：state.rs:110-180；time_sleep.rs:18-70；其他已下载文件只做符号/结构定位。

未构造题包、未运行gold/候选/容器/模型，未验证六小时难度。下载文件是选读材料，不是完整checkout或依赖包。
