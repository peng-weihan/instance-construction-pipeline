# 41_curl HTTP传输CLI的重定向、重试、续传与输出兼容

路线：M5；优先级：hold_wrapper_probe；状态：素材已取、范围待验证。
来源：[curl/curl](https://github.com/curl/curl/tree/03f3f4c6d97be3c2c9ad42010f65e61bf0a2c05c)；固定版本 `03f3f4c6d97be3c2c9ad42010f65e61bf0a2c05c`。

**已有能力：** 原生curl已有Retry-After、退避、部分下载自动续传前提及协议级测试；这些是兼容目标而非新增上游需求。

**拟交付：** 仅HTTP/1.1和明确列出的CLI契约，交付请求、响应、文件输出、续传、重试和错误的兼容替代实现；首轮不扩成curl全部协议。

**拟缺口：** 新的CLI/库交付规格与骨架尚未构造。若正常libcurl绑定或成熟HTTP库即可完成全部合同，此范围应降级，不临时禁库。

**工程链：** 命令配置 → 传输状态 → HTTP头/重定向 → retry/resume → 输出文件 → 退出码

**原题参照：** Git式外部行为重实现；与既有HTTPX/mitmproxy共享HTTP语义谱系，数据划分须保留关联。

**三个组合场景（设计）：**

1. 部分响应写文件后断开→按公开续传选项继续，服务端Range行为和最终字节均匹配。
2. 重定向后收到可重试状态及Retry-After→有界重试→成功，检查请求链、输出及退出码。
3. chunked响应在完成前断开→报告部分文件错误，已有输出如何保留按固定reference确定。

**基础完成后的剩余工作假设：**

- 普通GET完成后，重定向、凭据和重试/续传的交互可能需要统一传输状态。
- 成功下载后，部分输出、header重置和失败退出仍可能要求跨模块修复。

**独立评测：** 离线loopback脚本服务器记录wire和事件，固定reference给stdout/stderr/退出/输出文件差分；时间用可控逻辑或独立非计时判据。

**最强正常基线：** libcurl绑定＋现成参数解析器，或成熟HTTP客户端；这是必须先给机会的强合法方案。

**首个否证探针：** 先用libcurl绑定实现限定命令矩阵，若适配即可全部满足则当前profile不推进长程。不能据curl支持很多协议就声称该HTTP子集很大。

**许可观察：** 根COPYING为curl版权及permission notice；测试/可选TLS依赖的许可后续核对。

**离线和资源：** 完整curl的TLS/HTTP2等依赖不自动进入任务。用本地服务可离线，但短写、文件时间与超时判据需稳定化。

**已读证据：**

- [输出文件在重试中可否续传的严格前提](../sources/41_curl/files/src/tool_operate.c#L332) / [固定上游](https://github.com/curl/curl/blob/03f3f4c6d97be3c2c9ad42010f65e61bf0a2c05c/src/tool_operate.c#L332)
- [重试状态、退避和Retry-After已有合同](../sources/41_curl/files/docs/cmdline-opts/retry.md#L20) / [固定上游](https://github.com/curl/curl/blob/03f3f4c6d97be3c2c9ad42010f65e61bf0a2c05c/docs/cmdline-opts/retry.md#L20)
- [chunked传输提前断开返回CURLE_PARTIAL_FILE](../sources/41_curl/files/tests/data/test207#L38) / [固定上游](https://github.com/curl/curl/blob/03f3f4c6d97be3c2c9ad42010f65e61bf0a2c05c/tests/data/test207#L38)

定向阅读范围：tool_operate.c:332-355；retry.md:15-65；test207:1-62；test1059:1-30。

未构造题包、未运行gold/候选/容器/模型，未验证六小时难度。下载文件是选读材料，不是完整checkout或依赖包。
