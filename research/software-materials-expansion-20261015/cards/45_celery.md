# 45_celery — 可审计的工作流取消与补偿执行契约
- 来源：[celery/celery](https://github.com/celery/celery)；SHA `4b7a3652e3297730c0e018ce3038e0121de983bc`；M1 / `hold`。
- 已有：已有 chain/group/chord、errback、任务 retry/ack、stamping 和撤销机制；复杂失败传播已有原生测试，不能按功能名判缺失。
- 拟任务缺口：拟交付一个限定 Redis broker/backend 的工作流取消/补偿层：持久化操作记录、明确取消边界及幂等补偿；与现有 stamped revoke/errback 的差额待验证。
- 产品/子系统边界：面向订单批处理：多步/并行任务持有 workflow 身份，取消阻止未开始的步骤，已确认外部副作用按声明补偿；允许重投递，不承诺任意用户任务 exactly-once。
## 模块链与固定证据
- [`celery/canvas.py:2395`](https://github.com/celery/celery/blob/4b7a3652e3297730c0e018ce3038e0121de983bc/celery/canvas.py#L2395)：chord 已区分 eager/async、header/body 参数和调度
- [`celery/backends/base.py:1403`](https://github.com/celery/celery/blob/4b7a3652e3297730c0e018ce3038e0121de983bc/celery/backends/base.py#L1403)：backend 已汇集 chord 部分结果并处理失败回调
- [`t/unit/tasks/test_canvas.py:1140`](https://github.com/celery/celery/blob/4b7a3652e3297730c0e018ce3038e0121de983bc/t/unit/tasks/test_canvas.py#L1140)：原生测试覆盖 chord header 失败传播到后继链
- [`celery/worker/request.py:824`](https://github.com/celery/celery/blob/4b7a3652e3297730c0e018ce3038e0121de983bc/celery/worker/request.py#L824)：worker 已有 acknowledge 生命周期，需与新记录语义对齐
## 组合场景
1. 并行分支一个产生已确认副作用，用户取消；未开始分支不运行，已完成分支补偿且报告可审计。
2. worker 在副作用确认与 ack 附近退出后重投递，幂等业务记录不重复，补偿不会重复扣回。
3. 一个补偿临时失败，重启后继续补偿而不重启原业务链，其他 workflow 正常推进。
## 基线与退出
- 强合法基线：原生 Canvas link_error + revoke_by_stamped_headers + 用户幂等键/事务 outbox；已有成熟 workflow 框架也应作为可行替代，不能禁止正常库制造难度。
- 首探/退出：先用现有 stamping/revoke/errback 和最小操作日志跑取消/重投递场景；若已满足规定的副作用与补偿契约则退出，另选材料。
- 早期完成后的剩余假设：正常取消成功后，取消与 chord/body 同时入队、retry/ack 重投递和补偿幂等仍需验证。
- 早期完成后的剩余假设：一次补偿成功后，worker 重启时操作记录恢复、失败补偿重试及跨 workflow 隔离可能未完成。
- 独立 oracle / 原生回归：真实本地 Redis+worker 与独立 SQLite 业务副作用账本检查状态/幂等；可控 barrier 注入取消/退出；保留 Canvas/request/backend 原生回归；eager/mock 不能代表分布式行为。
- 许可观察：根 LICENSE 为 BSD-3-Clause；Kombu/Redis 客户端与镜像另审。
- 离线/架构风险：需预置 broker/backend 和 worker 进程管理；不同池/平台 revoke 与终止能力不同，初版仅固定 Linux worker 池，离线依赖待封装。
- 官方在线核对：[primary](https://github.com/celery/celery)；[primary](https://docs.celeryq.dev/en/latest/userguide/workers.html)
- 仅完成定向源码/测试阅读，未构造完整题包或运行；task_constructed=false；runtime_verified=false；six_hour_difficulty_verified=false。
