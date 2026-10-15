# EdgeBench 软件候选当前状态

核验时间：2026-10-15T11:15:48.813963+00:00（2026-10-15 19:15 CST）。16 个候选均实际启动过；5 个题包草案已构造、1 个题包暂缓、5 个当前设计被筛掉、5 个仍在出题，无排队。模型全部 gpt-6.1-sol/high。

| 状态 | 数量 | 路线 |
|---|---:|---|
| 题包草案已构造，待审查与运行验证 | 5 | 01_openapi_streaming, 09_valkey_transactions, 14_tree_sitter_incremental, 02_restler_recovery, 04_pytest_fixtures |
| 有题包但因廉价解暂缓 | 1 | 05_uv_resolution |
| 当前设计已筛掉 | 5 | 06_wasm_validation, 07_arrow_ipc, 08_http2_session, 15_jq_composition, 16_libarchive_cli |
| 正在出题 | 5 | 10_datafusion_sort, 13_toml_lossless, 03_httpx_transport, 11_rocksdb_compaction, 12_croaring_kernels |

草案已有题面、task.toml、参考解入口、评分入口和双环境 Dockerfile；文件存在与作者报告不代表语义审查、容器运行或六小时难度通过。新增 pytest 草案尚待父级审查；uv 虽有题包，最强廉价包装基线达 1.0，暂缓。

## 实质产物与判断

- **OpenAPI SDK**：真实生成器演进题包草案已取回本地，含题面、源码 starter、私有参考分支、评分器、双环境构建上下文、离线依赖与材料来源。作者本地参考五次 1.0，实际简化 wrapper 0.60；缺少六小时难度证据，且评分观测/单 schema 泛化仍需加固。
- **Tree-sitter**：真实 C runtime 跨文件恢复草案已取回，含独立冻结 grammar、逆补丁、API/Unicode/edit/ranges 检查。starter 仅改 full-reparse 为 0.46861；完整参考 API 加 full-reparse 的对照为 1.0，后者不能当成独立廉价解。当前合同不要求高效增量复用，暂缓长程认定。
- **WASM**：作者已完成真实源材料和强廉价基线探针；普通 Wasmtime wrapper 通过冻结的 76 例，独立 V8 对照也通过。作者明确拒绝当前 profile，不计为合格完整训练题，不为它启动六小时解题。不是所有 WASM 新任务都被否定。
- **其他路线**均已实际启动并执行工具，当前状态见上表；任务目录存在不当作构造完成证据。

[两个已完成草案入口](../../samples/software-authored-016-r1/README.md) / [本次实时状态来源](reports/current-edge-task-summary.json) / [全量调度状态](reports/all-pool-status.json)。

素材获取到实际题包的流程已经走通；从草案到具有六小时持续改进价值，仍没有实证。原题、参考、NOP 和部分解只是不同层次的证据。
