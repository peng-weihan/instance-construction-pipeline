# 75_pandoc 文档 AST、扩展语义与跨格式转换兼容

路线 M5；hold_wrapper_probe。来源 [jgm/pandoc](https://github.com/jgm/pandoc/tree/35742c0001ab2da45cebae1c37eacc2439f147ed)，固定 `35742c0001ab2da45cebae1c37eacc2439f147ed`。

**已有：** 已有 Markdown reader、YAML metadata 的递归 Markdown 解析、共享 Pandoc AST 与扩展/脚注回归。
**拟交付：** 限定 Markdown/JSON AST/HTML 等可执行读写合同，交付 metadata、引用/脚注、嵌套 block/inline、过滤和 writer 选项的一致转换；不按全部格式数量堆范围。
**拟缺口：** 拟重建限定的完整读写链，starter 未制作；成熟 reader/writer/AST 包装可能已足额满足。
**工程链：** reader options/YAML → block+inline parsing → shared AST → filters → writer/CLI

**三个组合场景（设计）：**
1. YAML 中含 Markdown 元数据，正文有嵌套脚注/引用，经 AST filter 后输出 HTML 保持链接和层级。
2. 切换公开扩展与 writer 选项，同一 AST 的 JSON 和 HTML 结果符合各自合同。
3. 递归脚注、原始标记和 Unicode 组合，错误/警告与退出行为可重复；不默认往返字节无损。

**初步完成后的剩余工作（假设）：**
- 常见段落转换后，metadata/引用/脚注与 AST 过滤的组合可能尚未完成。
- 单格式通过后，跨 reader/writer 的扩展和属性保留仍可能需统一。

**判据：** 冻结 reference 的规范化 AST/HTML，加独立节点/链接检查；不把 Markdown 文本往返相同当正确性。
**强正常基线：** 成熟 Markdown/HTML 库与标准 AST/filter 工具组合；若只是少量 AST 适配，当前范围降级。
**首探与退出：** 先用现成 reader/AST/writer 完成三个组合场景，再判断真正缺失的完整能力；先固定语义范围和非确定 metadata 规范化。
**许可观察：** 根 COPYING.md 为 GPLv2 文本；实际 Haskell 依赖、数据/模板通知另核。
**离线/架构：** GHC/Cabal 和 reader/writer 依赖闭包较重，构建等待不计难度；不把完整 Pandoc 可选生态全塞入镜像。

**源码与测试证据：**
- [Markdown reader 与 YAML metadata 共用文档解析状态](../sources/75_pandoc/files/src/Text/Pandoc/Readers/Markdown.hs#L67) / [固定上游](https://github.com/jgm/pandoc/blob/35742c0001ab2da45cebae1c37eacc2439f147ed/src/Text/Pandoc/Readers/Markdown.hs#L67)
- [脚注缩进、文本归属及递归脚注的 AST 回归](../sources/75_pandoc/files/test/Tests/Readers/Markdown.hs#L514) / [固定上游](https://github.com/jgm/pandoc/blob/35742c0001ab2da45cebae1c37eacc2439f147ed/test/Tests/Readers/Markdown.hs#L514)

实际定向阅读：Markdown reader:67–95；Markdown tests:510–526；HTML writer 仅结构定位。

状态：素材已取；未构造题包、未构建/运行参考或候选、未运行模型，六小时难度未验证。
