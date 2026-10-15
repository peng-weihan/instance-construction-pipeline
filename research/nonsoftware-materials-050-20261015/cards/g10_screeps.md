# G10_SCREEPS · Screeps Engine

状态：潜力 high / hold_reference；素材研究，未构题/运行/难度验收。
来源：[screeps/engine](https://github.com/screeps/engine/tree/a90d26fc9eb943147799e65d0bf9d4d0d79a2722)
固定版本：`a90d26fc9eb943147799e65d0bf9d4d0d79a2722`
来源单元：移动/采集/生命周期处理器和mock房间测试；不含完整服务器服务栈
材料：[manifest](../sources/g10_screeps/manifest.json)，含文件树、原文URL和SHA256。

拟题：**有限时域殖民地资源与维护策略**
在预置离线小房间中交付殖民地策略，协调采集、运输、建造、维修与单位更替；以有限tick窗口验收，不接在线永久世界。
交付：策略脚本、产能与维护计划、tick轨迹和资源账本。

自然难点一：单位生命周期、疲劳与身体构成改变运输产能，扩张会增加持续维护负担。
自然难点二：同步意图竞争道路/资源，生产计划与空间拥堵形成反馈，单个采集脚本不能闭合。
正常基线：官方可用采集/搬运/生成脚本，静态角色配比和路径缓存，允许成熟社区方案正常适配。
首个探针：先证明driver/存储/常量依赖可离线冻结，完整房间快照重置且无跨局写入；mock单元测试不足以证明任务环境可用。
降级/淘汰：若仍需线上服务器、不可控tick等待或不可重置持久世界则淘汰当前范围；若普通角色模板饱和则下调。

独立评分：外置只读快照judge重新计算入库、建筑/单位状态、存活和维护债务，拒绝策略自报日志；硬性tick预算。
生成与划分：留出房间连通与资源分布、单位寿命组合和扰动时间；固定服务版本，每局独立存储/命名空间。
谱系/污染：独立Screeps意图式世界，不是OpenTTD/RTS换皮；不能把搭建服务器工程计为策略长程难。
离线与计算：根engine依赖外部driver/持久化服务；仅有mock与片段，完整离线环境未取，优先hold_reference。
许可观察：根LICENSE.txt为ISC式许可；完整服务器、驱动和社区代码另核对。

证据：[1](https://github.com/screeps/engine/blob/a90d26fc9eb943147799e65d0bf9d4d0d79a2722/src/processor/intents/movement.js#L110)；[2](https://github.com/screeps/engine/blob/a90d26fc9eb943147799e65d0bf9d4d0d79a2722/spec/engine/processor/intents/movement.test.js#L13)；[3](https://github.com/screeps/engine/blob/a90d26fc9eb943147799e65d0bf9d4d0d79a2722/spec/helpers/mocks/intents.js#L1)
证据1：同格移动竞争按拉拽状态和MOVE能力/载重等排序，策略必须考虑交通与疲劳。
证据2：测试构造损坏MOVE身体部件并检查不能移动/占格，使用mock intents推进。
证据3：测试scope自定义房间对象和gameTime，reset只清mock对象，不能等同完整服务器reset。
实际选读：src/processor/intents/movement.js:110-149；spec/engine/processor/intents/movement.test.js:13-51；spec/helpers/mocks/intents.js:1-17
覆盖边界：上述定向阅读，不推断整个仓库均已审计。
