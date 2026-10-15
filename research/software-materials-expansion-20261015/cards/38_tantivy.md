# 38_tantivy 全文索引的写入、提交、读视图与失败恢复

路线：M4；优先级：build_scope_probe；状态：素材已取、范围待验证。
来源：[quickwit-oss/tantivy](https://github.com/quickwit-oss/tantivy/tree/8a4cfc40f5b7446c0700471aa50290dbb7f8ea97)；固定版本 `8a4cfc40f5b7446c0700471aa50290dbb7f8ea97`。

**已有能力：** 健康上游已有IndexWriter/IndexReader、显式reload和commit失败测试；自动reload不是commit返回时同步可见。

**拟交付：** 恢复同一个全文索引工作区的写入/提交/删除、reader reload、segment管理和失败处理行为，形成建索引→查询→修改→重开的完整链。

**拟缺口：** 在健康参考上选择关联实现缺口，保留schema/公开API和可运行骨架。不是给原生Tantivy补一个其实已有的事务提交功能。

**工程链：** schema/tokenization → writer/segment → metadata commit → reader reload → query/collector → GC

**原题参照：** Rust内容寻址多crate恢复/Codeflash因果退化；实际mask尚未选定。

**三个组合场景（设计）：**

1. 提交A→显式reload→保存旧searcher→提交B和删除→reload，新旧读视图各遵守公开契约。
2. 在元数据保存失败时提交B被拒绝，重新打开仍只看到先前成功提交A；随后能继续写。
3. 多segment合并/回收与查询并存，重开后文档集合、删除和排序结果保持一致。

**基础完成后的剩余工作假设：**

- 基础索引可查询后，delete/commit/reload的可见性仍需跨层集成。
- 正常提交恢复后，失败发布、segment生命周期和旧读视图可能仍需修订。

**独立评测：** 小型独立文档集合/查询解释模型，加固定gold的API差分和原生failpoints；先限定查询语义及排序并列规则。

**最强正常基线：** 正常索引库或简单全量重建实现；全量重建若达到所有公开正确性/资源要求，应承认可行。

**首个否证探针：** 完整gold使用Manual reload跑提交/删除/失败/重开纵向场景，再用正常全量重建基线比较；避免把异步reload窗口误判成bug。

**许可观察：** 根LICENSE为MIT文本；子crate和压缩/分词依赖后续单列。

**离线和资源：** Rust/Cargo离线闭包未构建；特定SIMD/文件系统行为需x86/ARM验证。测试优先显式reload与可控故障。

**已读证据：**

- [reload策略及commit返回不保证自动reload已完成](../sources/38_tantivy/files/src/reader/mod.rs#L15) / [固定上游](https://github.com/quickwit-oss/tantivy/blob/8a4cfc40f5b7446c0700471aa50290dbb7f8ea97/src/reader/mod.rs#L15)
- [保存元数据失败后新文档不可见的原生回归](../sources/38_tantivy/files/tests/failpoints/mod.rs#L42) / [固定上游](https://github.com/quickwit-oss/tantivy/blob/8a4cfc40f5b7446c0700471aa50290dbb7f8ea97/tests/failpoints/mod.rs#L42)

定向阅读范围：reader/mod.rs:15-44；tests/failpoints/mod.rs:42-105；index_writer只做入口定位。

未构造题包、未运行gold/候选/容器/模型，未验证六小时难度。下载文件是选读材料，不是完整checkout或依赖包。
