# 73_restic restic 本地仓库快照备份与恢复互操作

- 路线：M5；优先级：`scope_probe`。素材候选，未构题/构建/运行/校准。
- 固定源码：`restic/restic@9da3b87b07706956e8dc5fd5cb259b99ec940f51`；源码哈希/清单见 `../sources/73_restic/manifest.json`。
- 完整候选范围：完整限定工作流：本地仓库初始化→备份→修改后增量快照→列出/选择快照→包含/排除选择恢复→内容/元数据校验；先限定本地后端和格式版本。
- 原题锚点：`git_rewrite_in_zig`；仅借难度机制，不承诺同等运行难度。
- 已有能力：已有 parent-tree 复用、chunker/blob uploader 与并行文件/树保存；restore 有 overwrite 策略和 include/exclude 合同。
- 拟议缺口：拟构造同格式/行为的兼容客户端，不声称上游缺失；需先确认库/合法现成工具能否已满足完整工作流。

## 三类工作负载/工作流

- 未变/改名/局部修改文件跨两个快照恢复
- hardlink/symlink/权限/空目录和选择恢复
- 中断/失败输入后原仓库仍可读、已有快照和已提交数据可恢复

- 最强正常基线：正常库、格式/加密/分块组件及合法工具包装先试；允许合理已有组件。若调用现成 restic 即满足合同，撤销或在出题前重新定义真实交付，不事后禁工具。
- 首探/否证：先固定仓库格式和 CLI 子集，交叉打开上游/候选写出的仓库并做增量→恢复旅程；简单组合足够或互操作范围无法离线明确则 hold。
- 正确性 oracle：冻结上游互读+独立源目录字节/元数据清单、snapshot 引用可达检查；不要求随机加密 ciphertext/生成时间逐字节一致；原生 backup/restore integration tests 仅作种子。
- 后续结构假设 1：若现有组件仍不足，协调分块/内容寻址、索引、pack 与 snapshot tree，保证跨客户端读取和增量复用。
- 后续结构假设 2：若流程组合仍不足，协同恢复元数据、overwrite、选择规则及失败清理，保持旧快照和仓库一致。
- 离线：当前 go.mod 要 Go 1.25.8/toolchain1.25.10，module cache 与本地后端测试素材需预置；不以云账号或网络耗时制造难度。
- 许可观察：根 BSD-2-Clause 已存；加密/存储等依赖许可未全审。
- 平台风险：Linux 文件元数据、hardlink/symlink与 Windows 语义不同；先固定 Linux，ARM 加密/分块及格式互读另验。

## 源码与官方证据

- [internal/archiver/archiver.go:864](https://github.com/restic/restic/blob/9da3b87b07706956e8dc5fd5cb259b99ec940f51/internal/archiver/archiver.go#L864)：已有 chunker/uploader 与文件树 worker。
- [internal/archiver/archiver.go:883](https://github.com/restic/restic/blob/9da3b87b07706956e8dc5fd5cb259b99ec940f51/internal/archiver/archiver.go#L883)：Snapshot 复用 parent tree 保存。
- [internal/restorer/restorer.go:54](https://github.com/restic/restic/blob/9da3b87b07706956e8dc5fd5cb259b99ec940f51/internal/restorer/restorer.go#L54)：恢复 overwrite 合同已有多种策略。
- [cmd/restic/cmd_restore_integration_test.go:102](https://github.com/restic/restic/blob/9da3b87b07706956e8dc5fd5cb259b99ec940f51/cmd/restic/cmd_restore_integration_test.go#L102)：原生集成测试连接 backup/check/选择 restore。
- [doc/design.rst:35](https://github.com/restic/restic/blob/9da3b87b07706956e8dc5fd5cb259b99ec940f51/doc/design.rst#L35)：仓库格式要求原子写入，且随机 IV 使加密文件字节不适合作为等价条件。
- 官方上下文：[1](https://restic.readthedocs.io/en/stable/050_restore.html)；[2](https://github.com/restic/restic/blob/master/doc/design.rst)。
