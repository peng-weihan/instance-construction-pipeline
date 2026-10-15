# 74_sqlfluff 模板化 SQL 的诊断、修复与源位置兼容

路线 M5；hold_scope_probe。来源 [sqlfluff/sqlfluff](https://github.com/sqlfluff/sqlfluff/tree/1fdd794c925efa62f93ad78ff0d35ea41c60bea7)，固定 `1fdd794c925efa62f93ad78ff0d35ea41c60bea7`。

**已有：** 已有多轮 fix、初始诊断保留、循环检测、Jinja 源映射和避免修改模板内容的原生回归。
**拟交付：** 冻结明确 SQL 方言与规则集，交付模板渲染→解析→lint→冲突处理→修复回写的库和 CLI 兼容，覆盖配置与退出行为；不要求上游全部方言。
**拟缺口：** 新兼容实现/骨架未构造；若仅接几条 lint 规则或成熟 SQL 工具即完成，应作为短任务。
**工程链：** configuration/Jinja source mapping → dialect parser → rules → patch merge → original source/CLI

**三个组合场景（设计）：**
1. Jinja 表达式渲染为空且贴近引号，其他位置缩进修复后原模板表达式保留。
2. 多个规则提出相交或重复补丁，多轮修复稳定，初始诊断和最终 SQL 分别匹配固定契约。
3. 同 SQL 在两种明确方言与配置覆盖下运行，忽略注释、lint/fix/输出/退出保持一致。

**初步完成后的剩余工作（假设）：**
- 基础 SQL 格式化后，模板源位置与可安全编辑范围仍需整合。
- 单规则成功后，补丁冲突、多轮收敛和诊断归属可能仍需工作。

**判据：** 固定 SQLFluff 输出加独立补丁边界/幂等性检查；在可执行子集用数据库核验语义，模板本身不由字符串相等代替。
**强正常基线：** 现成 SQL parser/formatter 和 Jinja 映射工具；目标实现不能作为候选委托执行，但其他正常组件允许。
**首探与退出：** 先列拟规则/方言的现有替代实现映射；若仅几条转换和模板保护即覆盖，不推进六小时。
**许可观察：** 根 LICENSE.md 为 MIT；Jinja/dbt 插件、方言 fixture 与依赖需分别固定。
**离线/架构：** Python/模板插件和固定方言可离线；与本池 Jinja/dbt 共享语义谱系，不能当独立随机划分。

**源码与测试证据：**
- [fix 流程保留初始诊断、检测版本循环并限制轮数](../sources/74_sqlfluff/files/src/sqlfluff/core/linter/linter.py#L457) / [固定上游](https://github.com/sqlfluff/sqlfluff/blob/1fdd794c925efa62f93ad78ff0d35ea41c60bea7/src/sqlfluff/core/linter/linter.py#L457)
- [空 Jinja 占位符相邻引号时安全修复源文本的回归](../sources/74_sqlfluff/files/test/core/linter/fix_test.py#L211) / [固定上游](https://github.com/sqlfluff/sqlfluff/blob/1fdd794c925efa62f93ad78ff0d35ea41c60bea7/test/core/linter/fix_test.py#L211)

实际定向阅读：linter.py:457–490；fix_test.py:211–239；parser/templater 只定位。

状态：素材已取；未构造题包、未构建/运行参考或候选、未运行模型，六小时难度未验证。
