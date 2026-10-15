# 61_libjxl JPEG XL 无损 Modular 编码的压缩率与资源效率

- 路线：M3；优先级：`hold_until_baseline`。素材候选，未构题/构建/运行/校准。
- 固定源码：`libjxl/libjxl@ef67fde2ec16d52e644c5a0969230b9a85e3eb31`；源码哈希/清单见 `../sources/61_libjxl/manifest.json`。
- 完整候选范围：整数像素/alpha 输入→Modular 变换与预测/树→熵编码→标准码流→独立解码；先固定无损，避免混用有损质量指标。
- 原题锚点：`notebook_lossless_compression`, `ffmpeg_swscale_reimplementation`；仅借难度机制，不承诺同等运行难度。
- 已有能力：已有 effort/speed tier、palette 和估计成本后撤回变换，非缺少基本压缩选择；原生 benchmark 分别计编码和解码。
- 拟议缺口：未证实缺口：正常 effort/线程/Modular 配置的 Pareto 前沿后，特定图族是否仍有训练/树构建或缓冲成本。

## 三类工作负载/工作流

- 截图/扁平 RGBA：palette 选择与建树成本
- 噪声/摄影纹理：压缩大小与无效搜索
- 高位深/大幅图：预测/熵建模、并行与峰值内存

- 最强正常基线：Release+本机 Highway、正常 effort/Modular/线程/已有启发式；按相同无损合同测 encode/decode 时间、字节和RSS前沿。
- 首探/否证：先扫现成参数和独立 seed 图片；配置前沿足够、收益只因关质量/元数据或在噪声内则撤销。
- 正确性 oracle：冻结上游交叉解码、逐像素含 alpha/位深校对、标准码流解码；元数据/方向独立合同。benchmark 也特别固定 orientation，不能忽略其设置。
- 测量计划：固定硬件/CPU/内存/存储与 seed，分离准备/实现执行；交错重复测正确结果的时间、RSS/分配及特定资源，记录噪声与跨 seed 泛化。奖励上下端点均未测；上游宣传倍率不是本题收益。
- 后续结构假设 1：强配置后若成本估计反复扫描为热点，研究预测/变换评估的共享统计或提前终止，保持无损。
- 后续结构假设 2：强配置后若多 group 树构建/状态复制为热点，研究并行任务和内存布局；不能宣称已有算法缺失。
- 离线：CMake、Highway/Brotli 和使用的 codec/test data 需预置，submodule 指针不等于已下载；未构建。
- 许可观察：根 BSD 风格许可；构建文件有 Apache-2.0，依赖分别核查；未完整分发审计。
- 平台风险：Highway x86/ARM dispatch、整数边界和线程资源分平台校准。

## 源码与官方证据

- [lib/jxl/enc_modular.cc:314](https://github.com/libjxl/libjxl/blob/ef67fde2ec16d52e644c5a0969230b9a85e3eb31/lib/jxl/enc_modular.cc#L314)：已有 speed-tier 控制变换搜索。
- [lib/jxl/enc_modular.cc:333](https://github.com/libjxl/libjxl/blob/ef67fde2ec16d52e644c5a0969230b9a85e3eb31/lib/jxl/enc_modular.cc#L333)：已有按成本/颜色数选择 palette 的机制。
- [tools/benchmark/benchmark_codec_jxl.cc:268](https://github.com/libjxl/libjxl/blob/ef67fde2ec16d52e644c5a0969230b9a85e3eb31/tools/benchmark/benchmark_codec_jxl.cc#L268)：基准分别计编码耗时。
- [tools/benchmark/benchmark_codec_jxl.cc:322](https://github.com/libjxl/libjxl/blob/ef67fde2ec16d52e644c5a0969230b9a85e3eb31/tools/benchmark/benchmark_codec_jxl.cc#L322)：基准显式保持原 orientation 比较。
- [third_party/CMakeLists.txt:19](https://github.com/libjxl/libjxl/blob/ef67fde2ec16d52e644c5a0969230b9a85e3eb31/third_party/CMakeLists.txt#L19)：第三方 SIMD/编码依赖需要预置。
- 官方上下文：[1](https://github.com/libjxl/libjxl/blob/main/doc/encode_effort.md)；[2](https://github.com/libjxl/libjxl/blob/main/doc/benchmarking.md)。
