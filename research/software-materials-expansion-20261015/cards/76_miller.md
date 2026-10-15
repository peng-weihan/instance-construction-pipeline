# 76_miller 带 DSL 和跨记录状态的表格流处理兼容

路线 M5；build_scope_probe。来源 [johnkerl/miller](https://github.com/johnkerl/miller/tree/3fa2b291fc7bd93f491c93c2453e7d50a18d645d)，固定 `3fa2b291fc7bd93f491c93c2453e7d50a18d645d`。

**已有：** 已有 sorted/unsorted join、左右未配对输出、空字段策略和 begin/main/end 执行阶段；跨格式原生回归可作行为观察。
**拟交付：** 限定完整记录流工作流：CSV/JSON 输入、类型与缺失值、DSL begin/main/end、filter/group/join、格式输出和 CLI 失败语义。
**拟缺口：** 拟建立独立兼容规格和实现骨架，不能只转换几个命令参数；现成 SQL/awk/dataframe 包装须先测。
**工程链：** format reader/typed record → DSL/CST → per-record/context state → join/group → writer/CLI

**三个组合场景（设计）：**
1. JSON 与 CSV 记录按复合键关联，重复键、缺失/空值及左右未匹配行在 pipeline 中保持固定语义。
2. DSL begin 累计跨记录状态，main 更新/筛选，end 输出汇总；改变输入分块不改变结果。
3. 排序与未排序 join 两路径接 group/format 转换，输出顺序、类型和错误边界按参考定义。

**初步完成后的剩余工作（假设）：**
- 普通 filter/投影完成后，DSL 跨记录状态与流水线阶段仍可能需集成。
- 单格式通过后，join 重复键/未配对行、类型/空值与输出格式可能仍需统一。

**判据：** 冻结 Miller 差分加独立小型记录/关系模型；比较记录类型、顺序与选定字节格式，原生 fixture 分开保留来源。
**强正常基线：** DuckDB/awk/pandas/现成解析库的合法组合；如可完整满足固定 DSL 与 CLI 合同就接受并降低任务定位。
**首探与退出：** 先用普通关系工具适配完整工作流，不只测一条 join；再选择确实需要新实现的 DSL/类型/流式状态范围。
**许可观察：** 根 LICENSE.txt 为 BSD-2-Clause；数据与 Go 依赖后续按实际包固定。
**离线/架构：** Go 与文本 fixture 适合离线，但文件/流顺序、数值类型、locale 和外部 prepipe 支持边界须明确。

**源码与测试证据：**
- [join 配对/空值/有序与无序模式已有不同合同](../sources/76_miller/files/pkg/transformers/join.go#L18) / [固定上游](https://github.com/johnkerl/miller/blob/3fa2b291fc7bd93f491c93c2453e7d50a18d645d/pkg/transformers/join.go#L18)
- [DSL begin/main/end 作用域执行分离](../sources/76_miller/files/pkg/dsl/cst/root.go#L433) / [固定上游](https://github.com/johnkerl/miller/blob/3fa2b291fc7bd93f491c93c2453e7d50a18d645d/pkg/dsl/cst/root.go#L433)
- [原生跨格式 join 命令与配套 expected](../sources/76_miller/files/test/cases/verb-join-mixed-format/0001/cmd#L1) / [固定上游](https://github.com/johnkerl/miller/blob/3fa2b291fc7bd93f491c93c2453e7d50a18d645d/test/cases/verb-join-mixed-format/0001/cmd#L1)

实际定向阅读：join.go:18–37；root.go:433–460；该 join cmd/expout 与关联 JSON fixture 全读。

状态：素材已取；未构造题包、未构建/运行参考或候选、未运行模型，六小时难度未验证。
