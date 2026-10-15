# 35 simdjson：严格语义下的混合 JSON 流处理效率

- 路线：M3；优先级：`hold_until_baseline`。素材候选，尚未构题、构建或运行。
- 固定源码：`simdjson/simdjson@9c003534b1be3bc4f1322bfa7a770a7ffbf247d9`；源码片段、文件树和 SHA-256 见 `../sources/35_simdjson/manifest.json`。
- 完整候选范围：CPU dispatch→stage1 结构与 UTF-8 扫描→stream batch 边界→On-Demand 字段访问→数值/字符串输出与错误；不能只评扫描字节。
- 原 EdgeBench 锚点：`integer_compression_codec` 的精确语义、`vliw_kernel_optimization` 的体系结构约束；不能由 SIMD 标签推出剩余收益。

## 已有能力与可考察取舍

- 已按 CPU 指令集选择实现，也可强制实现：`src/implementation.cpp:286-312`；从 fallback 切到本机 SIMD 不算未有的结构创新。
- parser 已复用容量和 string buffer，`iterate` 必要时扩容后执行 stage1：`include/simdjson/generic/ondemand/parser-inl.h:24-66`。
- stage1 已有 ARM/x64 位索引差异、展开写索引和双块流水：`src/generic/stage1/json_structural_indexer.h:30-126,179-193`。应尊重已有快路径，而非重复“增加向量化”。
- 当前原生基准已有四种流格式、大小 payload、threaded 与 sliced 多线程：`benchmark/bench_stream_formats.cpp:11-200`；不能把拆流并行作为未知新功能。
- 负载 A：大量短记录，只取少数字段；batch、并行启动开销与首条延迟取舍。
- 负载 B：长字符串、转义、多字节 UTF-8 与高结构密度；扫描/解码吞吐与缓冲区占用取舍。
- 负载 C：大小记录交替与数值密集内容；parser 容量复用、峰值内存和负载均衡取舍。

## 基线、否证和测量计划

- 最强合理基线：Release/NDEBUG、本机最佳受支持 dispatch、parser/string-buffer 复用与预分配；扫原生 batch、threaded 和 sliced 路径；按访问合同比较 DOM/On-Demand，不允许后者少做规定工作。
- Oracle：冻结上游同访问序列，加独立标准解析器校对全量字段、整数范围/浮点合同、文档数与错误输入；UTF-8/边界/截断使用原生 document-stream tests 并补组合数据。
- 原生 sliced benchmark 内部有错误后 `continue` 且 sum 只防优化，不能直接当正确性 oracle；独立 runner 必须比对每条文档的结果和错误，避免“漏解析更快”。
- 严格区分按需字段访问和完整 JSON 验证；不能宣称访问 id 就验证了所有未读取值。不同实现的错误暴露时点亦需明确合同。
- 独立测量：生成/加载与解析分计时；固定 core/ISA/频率策略、相同已触达页；交错重复跑不同 seed，记录 GB/s、docs/s、首条/尾部延迟、峰值 RSS 和错误结果。
- 首探：在 A/B/C 上扫已有 dispatch/batch/parser 复用和原生并行路径；如果只改配置/调用方式即可达到目标，则不发题；奖励端点和收益门槛均待测。
- 剩余结构假设 1：配置优化后，在混合超短/长记录下，改进分批/调度的重复边界扫描与分配；须 profile 证实原有 sliced/threaded 路径仍有成本。
- 剩余结构假设 2：配置优化后，针对高结构密度/大量转义内容改进 stage1 索引写出与 stage2 消费局部性；须通过 ISA 分别验证，不能假设普适收益。

## 离线与许可

- README:276-287 声明库 Apache-2.0 或 MIT 可选，并列出部分 vendored 组件的其他许可；根两份许可已存，完整依赖审计未完成。
- `dependencies/CMakeLists.txt:1-42` 默认允许下载，并拉 Google Benchmark、counters 和固定 corpus；离线镜像必须预置这些依赖/数据，禁下载配置下验证实际构建。
- x86 AVX2/AVX512 与 ARM 路径、频率/降频和编译器均影响结果；同架构强基线，不能用强制 fallback 造易题。
- 官方上下文：[性能建议](https://github.com/simdjson/simdjson/blob/9c003534b1be3bc4f1322bfa7a770a7ffbf247d9/doc/performance.md)、[On-Demand 设计](https://github.com/simdjson/simdjson/blob/9c003534b1be3bc4f1322bfa7a770a7ffbf247d9/doc/ondemand_design.md)。没有采用宣传倍率作为本卡证据。
