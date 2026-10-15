# 52_flecs — 延迟世界修改、观察者与查询缓存一致性恢复
- 来源：[SanderMertens/flecs](https://github.com/SanderMertens/flecs)；SHA `cc2924199858433cbf9fdaca25b291883ebd09de`；M2 / `build_scope_probe`。
- 已有：上游已有ECS deferred commands、stage合并、observer事件和cached query/change monitor。官方canonical仍SanderMertens/flecs，未观察到转flecs-hub。
- 拟任务缺口：拟联合掩码延迟命令flush/批处理与相关查询失效/事件桥接，保留实体存储/查询编译器/公开API；不是上游缺功能，当前未制作可构建掩码。
- 产品/子系统边界：恢复一帧世界演进的完整子系统：defer期间可见性、merge后add/set/remove/delete、observer副作用再次入队、缓存查询结果/changed标志一致；首版单进程固定stage，不以实体数量估难。
## 模块链与固定证据
- [`src/commands.c:1199`](https://github.com/SanderMertens/flecs/blob/cc2924199858433cbf9fdaca25b291883ebd09de/src/commands.c#L1199)：flush处理stage队列、实体存活、批处理与递归合并
- [`src/query/cache/change_detection.c:79`](https://github.com/SanderMertens/flecs/blob/cc2924199858433cbf9fdaca25b291883ebd09de/src/query/cache/change_detection.c#L79)：query monitor追踪表/字段变化并区分读取需求
- [`src/observer.c:348`](https://github.com/SanderMertens/flecs/blob/cc2924199858433cbf9fdaca25b291883ebd09de/src/observer.c#L348)：observer执行应用run/callback并共享迭代器生命周期
- [`test/core/src/Commands.c:36`](https://github.com/SanderMertens/flecs/blob/cc2924199858433cbf9fdaca25b291883ebd09de/test/core/src/Commands.c#L36)：原生测试规定defer新实体在merge前后组件可见性
- [`test/query/src/Cached.c:4`](https://github.com/SanderMertens/flecs/blob/cc2924199858433cbf9fdaca25b291883ebd09de/test/query/src/Cached.c#L4)：原生缓存查询测试验证实体、字段ID与迭代结果
## 组合场景
1. 同帧defer新实体并add/set/remove，merge前不可见、merge后组件与observer事件符合API契约。
2. OnSet观察者再次添加/删除组件，flush继续处理重入命令，最终query与事件账本一致且无重复析构。
3. 缓存query建立后删除并复用实体ID、变更继承来源，迭代与changed行为同固定原版一致，空merge不产生虚假变化。
## 基线与退出
- 强合法基线：缓存层可用uncached全扫描，commands可先缓冲再调用保留immediate APIs；这是合法强基线。先看简单队列是否已满足全部可观察语义，不以禁用低效算法抬难度。
- 首探/退出：先实现通用缓冲队列+immediate API+uncached查询，跑defer可见性、observer重入和delete/reuse组合；若已完整覆盖则收缩/hold，性能要求另需实测依据。
- 早期完成后的剩余假设：add/set基本成功后，remove/delete顺序、实体ID回收、observer在flush中再修改与析构事件仍可能未恢复。
- 早期完成后的剩余假设：查询结果正确后，cached changed/skip、继承与共享源字段失效、重复merge与资源生命周期仍需验证。
- 独立 oracle / 原生回归：固定上游C API驱动输出世界/事件/查询账本作差分，简单子集另用独立关系模型；保留Commands/Cached/Observer原生回归，原型运行量不代表长时难度。
- 许可观察：根 LICENSE MIT，含Sander Mertens与Meta版权；保留声明，测试工具/依赖另审。
- 离线/架构风险：C/C++与CMake，tests默认关闭且测试runner依赖需预置；无公网/图形需求。原生非amalgamated源与发行单文件不得互作隐藏答案；跨CPU/编译选项另验。
- 官方在线核对：[primary](https://github.com/SanderMertens/flecs)；[primary](https://github.com/SanderMertens/flecs/blob/master/docs/ObserversManual.md)
- 仅完成定向源码/测试阅读，未构造完整题包或运行；task_constructed=false；runtime_verified=false；six_hour_difficulty_verified=false。
