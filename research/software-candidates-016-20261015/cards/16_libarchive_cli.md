# 16_libarchive_cli：归档读写、链接与流式格式的CLI兼容

优先级：**P2**（素材筛选顺序，不是质量通过）。状态：素材证据已取得、设计提案；新 profile 未完成构造或验证。

来源：[参照源码](https://github.com/libarchive/libarchive/tree/b10312a52e5e4d1baf047b563e501b4fb184adde)；commit `b10312a52e5e4d1baf047b563e501b4fb184adde`。

许可观察：主体 BSD-2-Clause 风格；COPYING 明示个别文件和构建脚本多许可，不能只给一个总许可证。

## 已有能力与拟出的题

libarchive 已能读写多格式流式归档，并带 tar/cpio/zcat；现有实现是参考，不应把给一个已可调用 libarchive 的 wrapper 当成新大工程。

构造归档读写及 bsdtar 风格 CLI 的行为兼容任务：tar/pax、长路径/Unicode、链接/元数据、重复 -C 和分段流，按明确文件系统合同验证真实解包状态。

原题类别参照：git_rewrite_in_zig / cfzip_compression_engine：持久文件状态与 CLI/格式兼容。 新仓库/合同/数据不同；仅为机制相近，尚无同分布或训练收益实证。

交付范围：

- 可嵌入 reader/writer 与 CLI

- 明确支持格式、平台元数据、符号链接和路径策略，隔离临时目录；不以一次往返自证格式正确

## 参考与迭代评分

固定 libarchive/bsdtar 作跨读写参考，同时独立检查成员内容、元数据和退出状态；只在格式规定范围比较字节，压缩时间戳/UID/locale 固定。

拟评分维度：

- 格式解析与写出互通

- 分段/截断流

- 长路径/PAX 元数据

- 链接及多 -C 的文件状态

- 错误与确定性

评分维度是设计，尚未冻结权重、测试分组、归一化常量或奖励端点。完整题必须把这些写入机器可读元数据；性能题只能在实测后填 baseline/reference。每次提交只取源码/静态配置快照，独立无状态 verifier 重建运行，返回 validity、named checks、raw metrics 和 [0,1] score。构建或评分基础设施失败不能伪装成任务低分。

## 六小时潜力与第一道筛选

以下是待验证的后续改进路径，不是时长估计：

- 普通文件之后实现 PAX/长路径和 hardlink/symlink 语义

- 解决前向流输入、截断、文件位置和部分成功的错误行为

最强廉价基线：系统 tar、libarchive 或现成 archive binding 可能充分解题；必须先按正常工具合同试包装。若已有库全覆盖，应淘汰这条实现题。

先做的否证探针：先取固定格式的跨工具读写最小场景，并测现成 binding；再决定是兼容实现题还是已有能力包装题。

构造风险：

- 平台权限、mtime、顺序与路径行为需明示，不能跨平台盲目字节比较

- 压缩库和 fixture 的来源许可需单独收齐

- 成员数量/文件体积变大本身不构成长程

## 实际取得的源码证据

- [实际流式格式/CLI 范围](https://github.com/libarchive/libarchive/blob/b10312a52e5e4d1baf047b563e501b4fb184adde/README.md#L4)；本地 [`sources/16_libarchive_cli/files/README.md:4`](../sources/16_libarchive_cli/files/README.md)。

- [真实 PAX 支持实现](https://github.com/libarchive/libarchive/blob/b10312a52e5e4d1baf047b563e501b4fb184adde/libarchive/archive_read_support_format_tar.c#L128)；本地 [`sources/16_libarchive_cli/files/libarchive/archive_read_support_format_tar.c:128`](../sources/16_libarchive_cli/files/libarchive/archive_read_support_format_tar.c)。

- [真实多 -C 文件系统行为测试](https://github.com/libarchive/libarchive/blob/b10312a52e5e4d1baf047b563e501b4fb184adde/tar/test/test_option_C_upper.c#L9)；本地 [`sources/16_libarchive_cli/files/tar/test/test_option_C_upper.c:9`](../sources/16_libarchive_cli/files/tar/test/test_option_C_upper.c)。

完整已下载文件、大小、SHA-256 和原始 URL：[manifest](../sources/16_libarchive_cli/manifest.json)。[完整 Git 文件树索引](../sources/16_libarchive_cli/git-tree.json)不是完整 checkout；依赖/vendor、额外 grammar/服务/互通数据仍按上文风险补齐。

