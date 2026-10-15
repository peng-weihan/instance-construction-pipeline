# 28_alembic — 显式重命名意图驱动的数据库重构迁移版本
- 来源：[sqlalchemy/alembic](https://github.com/sqlalchemy/alembic)；固定版本 `1bc21b86dd6ddd07ac696e2d73b6cb200dd97bbd`。
- 路线：M1_existing_project_roadmap；优先级：`build_scope_probe`。
- 许可观察：根 LICENSE 与 pyproject.toml 显示 MIT；保留版权及许可；SQLAlchemy、数据库驱动与镜像另行清点，未做全依赖许可审计。
- 证据层级：已固定文件树和摘录哈希，已读核心实现与原生测试；未 clone/build/运行模型。
- 状态：task_constructed=false；runtime_verified=false；difficulty_verified=false。

## 已有能力与拟新增范围
- 已有：已有数据库反射、metadata 差分、操作树、upgrade/downgrade 与 Python 渲染；表/列重命名操作本身存在。官方明确自动差分会把重命名识别为 add/drop，需人工修订。
- 拟新增：拟增加声明式 rename intent 的验证、反射对象身份映射、依赖顺序、可审查迁移渲染及回退；缺口限于这套整体自动化流程，尚未复现运行。
- 产品交付：以 SQLite 与固定 PostgreSQL 两种交付后端为候选：用户提交目标 metadata 和明确的旧名→新名意图，生成保留数据且可逆的重构版本；冲突/过期意图应在生成前报结构化诊断。允许使用原生 rewriter/DDL，不能仅以存在 rename API 判定完成。

## 实际模块链与证据
- [`docs/build/autogenerate.rst:162`](https://github.com/sqlalchemy/alembic/blob/1bc21b86dd6ddd07ac696e2d73b6cb200dd97bbd/docs/build/autogenerate.rst#L162)：自动生成不推断表/列重命名，不能把 rename 操作本身冒称新增
- [`alembic/autogenerate/compare/tables.py:83`](https://github.com/sqlalchemy/alembic/blob/1bc21b86dd6ddd07ac696e2d73b6cb200dd97bbd/alembic/autogenerate/compare/tables.py#L83)：反射与目标表名集合比较，新增/删除/共有表走不同路径
- [`alembic/autogenerate/api.py:171`](https://github.com/sqlalchemy/alembic/blob/1bc21b86dd6ddd07ac696e2d73b6cb200dd97bbd/alembic/autogenerate/api.py#L171)：差分进入 MigrationScript 操作树
- [`alembic/operations/ops.py:1444`](https://github.com/sqlalchemy/alembic/blob/1bc21b86dd6ddd07ac696e2d73b6cb200dd97bbd/alembic/operations/ops.py#L1444)：原生 RenameTableOp 已存在，是必须纳入的强基线
- [`alembic/autogenerate/render.py:555`](https://github.com/sqlalchemy/alembic/blob/1bc21b86dd6ddd07ac696e2d73b6cb200dd97bbd/alembic/autogenerate/render.py#L555)：AlterColumnOp 渲染已支持新列名与类型等修改
- [`tests/test_autogen_diffs.py:1837`](https://github.com/sqlalchemy/alembic/blob/1bc21b86dd6ddd07ac696e2d73b6cb200dd97bbd/tests/test_autogen_diffs.py#L1837)：原生回归验证操作反转及 schema 对象结构

## 三个端到端场景
1. 客户表与其字段共同重命名，外键引用和索引同步处理；升级后业务查询读到原记录，降级恢复原 schema 与记录。
2. 同次重构包含 rename、nullable/default/type 变更；生成脚本在两个固定后端实际执行，再次 autogenerate 无虚假差分。
3. 两个 schema 有同名表且一份意图已过期；预检指出准确对象并不生成危险 add/drop，修正后稳定输出可审查版本。

## 难度否证与剩余工作
- 最强正常基线：原生 op.rename_table / alter_column(new_column_name=...) + process_revision_directives/Rewriter；允许直接复用，人工迁移脚本作为语义参考。插件生态是否已经完整满足需后续专门核对。
- 首个否证探针：先用最短 Rewriter 把单表单列 rename 的 add/drop 改写；若三个综合场景也仅需薄配置且无通用剩余语义，则降级为短题/hold。尚未执行。
- 早期实现后仍可能剩余（假设）：单次 rename 成功后，联合外键/索引/约束和同次类型变更的反射身份、执行顺序与 downgrade 数据保持仍需验证。
- 早期实现后仍可能剩余（假设）：简单名称映射成功后，交换名称、跨 schema 同名对象、过期/歧义意图的校验及可重复生成仍可能缺失；先用产品规格决定是否纳入。

## 评测与环境
- 独立评测及原生回归：独立 SQLite/PostgreSQL Inspector 和数据查询检查最终 schema、外键与行值；生成脚本实际 upgrade→downgrade→upgrade；复用 test_autogen_diffs/test_autogen_render/batch 回归，不能仅比生成文本。
- 离线与跨架构：Python>=3.10、SQLAlchemy>=2.0；SQLite 可离线，PostgreSQL 服务/驱动需预装并提供独立 DB，不能用 mock 声称 DDL 运行兼容；不同 CPU 镜像/驱动 wheel 待验证。
