# 42_cmark_gfm GFM文档的解析、AST位置、扩展与渲染兼容

路线：M5；优先级：hold_wrapper_probe；状态：素材已取、范围待验证。
来源：[github/cmark-gfm](https://github.com/github/cmark-gfm/tree/27d942c8b0a62d192f616e5bf3578f4b6a89e180)；固定版本 `27d942c8b0a62d192f616e5bf3578f4b6a89e180`。

**已有能力：** 上游已有block/inline分层、GFM table等扩展、API source-position测试和扩展规范样例。

**拟交付：** 一个可嵌入Markdown库及CLI，明确CommonMark/GFM子集、AST与source positions、分块输入和HTML输出契约；不只把固定文本转成HTML。

**拟缺口：** 拟构造独立兼容实现和统一API骨架；普通Markdown库是否已完整覆盖还未运行，不能把多个格式标签当新难点。

**工程链：** UTF-8/chunks → block parsing → inline delimiter → extension nodes → AST/source positions → render/CLI

**原题参照：** Expat式解析库/ABI兼容和Git式CLI行为；继承行为目标，不复制原题材料。

**三个组合场景（设计）：**

1. 表格单元含转义pipe、嵌套inline和Unicode，AST及HTML按固定reference一致。
2. 同一文档以不同输入切分喂入，结果和source positions一致；位置单位需先抽取真实API合同。
3. 嵌套list/quote内扩展与原始HTML交互，切换公开渲染选项后输出及CLI失败行为保持兼容。

**基础完成后的剩余工作假设：**

- 普通段落/列表渲染完成后，block与inline/扩展组合仍可能要求统一解析表示。
- HTML结果可用后，AST API、位置和分块输入兼容可能还有工程工作。

**独立评测：** 规范＋固定reference差分，另以独立AST不变量检查位置/父子关系；新生成语料与引用的官方样例分开留来源。

**最强正常基线：** pulldown-cmark、markdown-it等合法成熟实现加API适配。若全部输出/API要求可薄封装完成则降级，不事后禁止。

**首个否证探针：** 先比较两种正常解析库对AST/位置/扩展/分块接口的覆盖，再选择真正需要新实现的完整范围。

**许可观察：** COPYING含BSD两条款及其他文件归属；test/extensions.txt头部单独标CC-BY-SA-4.0，不能把测试材料统一当BSD。

**离线和资源：** 源码C/CMake及scanner构建闭包未验证；纯文本/CPU适合离线，但Unicode位置、渲染选项和gold版本须固定。

**已读证据：**

- [table行解析与inline内容、空cell和pipe处理](../sources/42_cmark_gfm/files/extensions/table.c#L189) / [固定上游](https://github.com/github/cmark-gfm/blob/27d942c8b0a62d192f616e5bf3578f4b6a89e180/extensions/table.c#L189)
- [table与inline格式及Unicode组合的规范样例](../sources/42_cmark_gfm/files/test/extensions.txt#L39) / [固定上游](https://github.com/github/cmark-gfm/blob/27d942c8b0a62d192f616e5bf3578f4b6a89e180/test/extensions.txt#L39)
- [source position API场景](../sources/42_cmark_gfm/files/api_test/main.c#L996) / [固定上游](https://github.com/github/cmark-gfm/blob/27d942c8b0a62d192f616e5bf3578f4b6a89e180/api_test/main.c#L996)
- [扩展测试文本单独声明CC-BY-SA-4.0](../sources/42_cmark_gfm/files/test/extensions.txt#L6) / [固定上游](https://github.com/github/cmark-gfm/blob/27d942c8b0a62d192f616e5bf3578f4b6a89e180/test/extensions.txt#L6)

定向阅读范围：table.c:189-231；extensions.txt:1-75；api_test/main.c:990-1010；其他parser文件仅结构定位。

未构造题包、未运行gold/候选/容器/模型，未验证六小时难度。下载文件是选读材料，不是完整checkout或依赖包。
