# 70_pydantic_core 类型校验、联合分支和模型序列化的关联恢复

路线 M4；build_scope_probe。来源 [pydantic/pydantic](https://github.com/pydantic/pydantic/tree/8cd3bec6c7e1d360d92193841613465d30f63955)，固定 `8cd3bec6c7e1d360d92193841613465d30f63955`。

**已有：** 当前主仓已经实现 smart/left-to-right union、严格/宽松校验、模型构造和序列化；旧 pydantic-core 独立仓已归档迁入主仓。
**拟交付：** 在健康固定 Pydantic Core 子项目中设计 schema→验证→模型构造→序列化→结构化错误的完整行为包，恢复相互关联实现，保留公开 Python API 与可信基础类型。
**拟缺口：** 拟在已验证健康参考上构造关联缺口，尚未选定 mask；不把这些既有能力宣称为新功能，也不把归档和主仓算两项。
**工程链：** schema graph → validator context/union choice → model instance → serializer/error location

**三个组合场景（设计）：**
1. 嵌套模型 union 中多个分支成功，按固定版本的字段计数/精确性选择，序列化保持模型身份与别名契约。
2. 同一 schema 在 Python/JSON、strict/lax 输入间切换，递归容器的错误位置与上下文不串状态。
3. 模型默认值、include/exclude、嵌套 union 与序列化错误组合；多次调用共享已编译 schema 仍隔离。

**初步完成后的剩余工作（假设）：**
- 基础字段可验证后，跨 union 分支的上下文恢复与多层模型选择仍可能需修订。
- 验证成功后，序列化、默认值和结构化错误的共同契约可能仍未闭合。

**判据：** 原生 schema/API 回归加固定 reference 差分；独立检查模型身份、错误路径和序列化值，不只检查是否抛异常。
**强正常基线：** 正常 JSON Schema/数据校验库加适配，允许成熟 Rust/Python 工具；若完整行为包可以薄包装完成则降级。
**首探与退出：** 先运行健康 gold 的 union/model/serializer 纵向用例，再用最强适配实现同一 API；验证实际关联缺口足够完整。
**许可观察：** 当前主仓 LICENSE 为 MIT；Rust/PyO3/JSON 等依赖和 fixture 后续逐项固定。
**离线/架构：** 需要匹配 Rust、Python、PyO3 与离线 vendor；健康构建和 x86/ARM 未验证。归档旧源码仅作迁移记录。

**源码与测试证据：**
- [smart union 选择使用字段计数/精确性并恢复验证状态](../sources/70_pydantic_core_current/files/pydantic-core/src/validators/union.rs#L103) / [固定上游](https://github.com/pydantic/pydantic/blob/8cd3bec6c7e1d360d92193841613465d30f63955/pydantic-core/src/validators/union.rs#L103)
- [原生模型 union 测试检查实际模型身份](../sources/70_pydantic_core_current/files/pydantic-core/tests/validators/test_union.py#L56) / [固定上游](https://github.com/pydantic/pydantic/blob/8cd3bec6c7e1d360d92193841613465d30f63955/pydantic-core/tests/validators/test_union.py#L56)

实际定向阅读：union.rs:103–159；test_union.py:56–93；其他下载文件仅结构定位。

状态：素材已取；未构造题包、未构建/运行参考或候选、未运行模型，六小时难度未验证。
