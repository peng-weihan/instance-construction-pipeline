# 49_dbt — 可离线重放的模型选择与 defer 影响审查包
- 来源：[dbt-labs/dbt](https://github.com/dbt-labs/dbt)；SHA `8843d3dfca9a2ea2646a6273701a89ffffd4b11e`；M1 / `hold`。
- 已有：请求旧 repo 已重定向到 dbt-labs/dbt；固定 main 是 Rust dbt v2，v1 Python 在1.latest。已有 state selector、manifest 比较、defer 关系重写和详细 explain 日志/服务。
- 拟任务缺口：拟将 manifest、selection/defer 输入及原因链收成可移交的离线审查包；不得把已有 state/explain 功能重命名为新题。现存命令可覆盖多少未验证。
- 产品/子系统边界：限定本地 manifest 与小型固定适配器：同一包在另一目录离线生成相同选择集合/生产关系映射并解释差异，能校验 artifacts 版本和输入漂移；不涉及云服务产品重造。
## 模块链与固定证据
- [`README.md:9`](https://github.com/dbt-labs/dbt/blob/8843d3dfca9a2ea2646a6273701a89ffffd4b11e/README.md#L9)：官方声明 canonical dbt、Rust v2 main 与 Python v1 分支迁移
- [`crates/dbt-scheduler/src/node_selector.rs:68`](https://github.com/dbt-labs/dbt/blob/8843d3dfca9a2ea2646a6273701a89ffffd4b11e/crates/dbt-scheduler/src/node_selector.rs#L68)：已有 manifest select/exclude 与 state 条件过滤
- [`crates/dbt-defer/src/lib.rs:63`](https://github.com/dbt-labs/dbt/blob/8843d3dfca9a2ea2646a6273701a89ffffd4b11e/crates/dbt-defer/src/lib.rs#L63)：已有本地/云 defer state 优先级及关系重写流程
- [`crates/dbt-schemas/src/schemas/prev_state/mod.rs:38`](https://github.com/dbt-labs/dbt/blob/8843d3dfca9a2ea2646a6273701a89ffffd4b11e/crates/dbt-schemas/src/schemas/prev_state/mod.rs#L38)：StateArtifacts 已携带 manifest/run/freshness 与版本相关状态
- [`crates/dbt-state/src/explain/tests.rs:29`](https://github.com/dbt-labs/dbt/blob/8843d3dfca9a2ea2646a6273701a89ffffd4b11e/crates/dbt-state/src/explain/tests.rs#L29)：原生测试已有 explain JSONL、错误行号与记录版本检查
## 组合场景
1. 改宏与模型配置后用 state:modified 选择并审查受影响上下游，结果与约定图一致。
2. dev选择部分模型，未选非ephemeral上游defer到prod，包中记录每个关系映射及依据。
3. 同一审查包迁移目录离线重放得到一致结果；缺失/不兼容manifest明确报错且不触发云回退。
## 基线与退出
- 强合法基线：原生 selectors/state/defer/explain + manifest归档脚本；允许用已有导出/文档机制。若只是打包几个JSON不升格长题。
- 首探/退出：先以本地 manifest 和现有 explain 生成/拷贝/重放审查材料；若完整选择/关系/原因已可直接获取则退出。还需先证实当前 Rust开源部分可独立离线构建运行。
- 早期完成后的剩余假设：单一模型选择正确后，宏/契约/配置变更、ephemeral/inline 排除、选择与defer不同state源的组合仍可能待解。
- 早期完成后的剩余假设：一次审查包可读后，旧manifest格式、artifact身份校验、目录迁移及原因归属一致性仍需验证。
- 独立 oracle / 原生回归：独立小图/人工SQL关系oracle对照选择集合与编译SQL，保留 selector/defer/explain真实回归；只读日志测试不等于数据库执行验收。
- 许可观察：根 LICENSE Apache-2.0，README区分仓库源码许可与定制分发产品许可；只基于此源码，不把商业二进制权利视为自动获得。
- 离线/架构风险：Rust2024 workspace 与适配器/SQL编译依赖较重；当前路径含云state与遥测，先证明关闭网络仍可运行；CPU驱动、离线vendor和独立构建均待验证。
- 官方在线核对：[primary](https://github.com/dbt-labs/dbt-core)；[primary](https://github.com/dbt-labs/dbt)
- 仅完成定向源码/测试阅读，未构造完整题包或运行；task_constructed=false；runtime_verified=false；six_hour_difficulty_verified=false。
