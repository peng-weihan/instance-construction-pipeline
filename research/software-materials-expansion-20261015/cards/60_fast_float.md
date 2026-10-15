# 60_fast_float 正确舍入十进制数值解析的批量吞吐

- 路线：M3；优先级：`hold_until_baseline`。素材候选，未构题/构建/运行/校准。
- 固定源码：`fastfloat/fast_float@166d2b3df29cf8101bb715bde2125610881df791`；源码哈希/清单见 `../sources/60_fast_float/manifest.json`。
- 完整候选范围：有界字符输入→数值词法→fast path/高精度回退→结果位模式、终止指针及错误；覆盖 float/double 与指定格式。
- 原题锚点：`integer_compression_codec`, `vliw_kernel_optimization`；仅借难度机制，不承诺同等运行难度。
- 已有能力：已有 Clinger 快路径、compute_float 与过多位数字回退；包含舍入模式检测和 signed-zero 测试，不能照旧 README 简化行为。
- 拟议缺口：未证实缺口：编译器正常优化后，混合位数/指数的词法分支与稀有高精度路径是否仍有空间。

## 三类工作负载/工作流

- 短整数/短小数：fast path 与分支开销
- 超长有效位/半 ULP/次正规：精确回退与吞吐
- 指数极值/非法尾部：错误/指针合同与扫描成本

- 最强正常基线：当前 header-only Release、正常本机编译与已有快路径；合理 char buffer/循环布局；同语义 std::from_chars 作参考，不拿 locale strtod 宣传倍率当本题收益。
- 首探/否证：短数/难舍入/异常混合数据先测位模式正确的强配置；若只有换 API、编译选项或噪声差异则撤销。
- 正确性 oracle：MPFR 或整数有理数精确舍入参考+冻结上游，比较 IEEE 位、负零、返回指针/ec；原生不同 rounding-mode 测试。NaN 按已订语义而非未规定 payload 比较。
- 测量计划：固定硬件/CPU/内存/存储与 seed，分离准备/实现执行；交错重复测正确结果的时间、RSS/分配及特定资源，记录噪声与跨 seed 泛化。奖励上下端点均未测；上游宣传倍率不是本题收益。
- 后续结构假设 1：强配置后若词法分支对混合数值仍主导，研究扫描与分类布局，保持终止指针/错误精确。
- 后续结构假设 2：强配置后若长尾回退重复计算仍主导，研究中间乘积/边界信息复用，须独立精确舍入验证。
- 离线：核心 header-only；benchmark CMake 会下载 counters 和未固定 master 的外部数据，正式镜像须固定两者并离线预置；测试 doctest 另预置。
- 许可观察：根 Apache-2.0/Boost/MIT 三份许可已存；依据具体选择保留文本，依赖另核。
- 平台风险：x86/ARM 的乘法/浮点环境与 compiler 影响路径；不要用 fast-math 弱化合同。

## 源码与官方证据

- [include/fast_float/parse_number.h:219](https://github.com/fastfloat/fast_float/blob/166d2b3df29cf8101bb715bde2125610881df791/include/fast_float/parse_number.h#L219)：已有 Clinger 快路径及舍入环境处理。
- [include/fast_float/parse_number.h:303](https://github.com/fastfloat/fast_float/blob/166d2b3df29cf8101bb715bde2125610881df791/include/fast_float/parse_number.h#L303)：快路径与过长数字分流。
- [tests/basictest.cpp:172](https://github.com/fastfloat/fast_float/blob/166d2b3df29cf8101bb715bde2125610881df791/tests/basictest.cpp#L172)：原生测试在不同舍入模式核验零位模式。
- [benchmarks/CMakeLists.txt:36](https://github.com/fastfloat/fast_float/blob/166d2b3df29cf8101bb715bde2125610881df791/benchmarks/CMakeLists.txt#L36)：基准外部数据来源需额外固定。
- 官方上下文：[1](https://github.com/fastfloat/fast_float)。
