# 77_wireshark 离线抓包的跨帧重组、字段与过滤兼容

路线 M5；hold_toolchain_probe。来源 [wireshark/wireshark](https://github.com/wireshark/wireshark/tree/455e49bcca6882e317d83d76feb86cf88a27df1f)，固定 `455e49bcca6882e317d83d76feb86cf88a27df1f`。

**已有：** 已有通用重组、TCP/dissector 状态及多帧 gRPC/HTTP2 回归；官方 GitHub 是主 GitLab 的只读镜像。
**拟交付：** 以合成 PCAP 为输入，冻结 Ethernet/IP/TCP 与明确应用协议子集，交付跨帧重组、会话状态、选定 display-filter/字段输出和 TShark CLI 兼容；不处理实时抓包或全部 dissector。
**拟缺口：** 新的受限兼容实现尚未构造；不能凭 dissector 数量计难度，若现成解析/重组库足够则收缩预算或换范围。
**工程链：** PCAP reader → protocol tree/conversation → TCP/reassembly → application messages → display filter → CLI fields

**三个组合场景（设计）：**
1. 一个应用消息跨多帧、同帧又包含多消息，输出消息字段与相应帧归属遵守固定合同。
2. 乱序/重复片段与多会话交错，先完成重组再执行字段过滤；错误片段不污染其他会话。
3. 同一合成捕获执行一次/二次分析及选定输出模式，稳定字段和退出行为可重复；不比较动态路径或环境字段。

**初步完成后的剩余工作（假设）：**
- 单帧解析成功后，跨包会话、重组边界和应用消息的共同状态仍可能未闭合。
- 字段解析可用后，display-filter 类型语义、两遍分析与 CLI 组合可能还有工作。

**判据：** 冻结 TShark 及独立合成包/消息生成器，比较字段/会话/重组和消息字节；不要求无关时间戳/主机信息逐字节相同。
**强正常基线：** Scapy/dpkt/成熟 PCAP 和协议库、现成重组工具；先测试普通适配是否覆盖全部选定合同。
**首探与退出：** 先构建不含 GUI/实时抓包的健康参考，跑一条可控重组轨迹；依赖过重或 wrapper 已全解则 hold。
**许可观察：** 根 COPYING 为 GPLv2 文本；各 dissector、外部协议库和捕获 fixture 的归属后续单列。
**离线/架构：** C/C++/GLib 等依赖较重；仅离线合成 PCAP 不需 root 或 NIC。HTTP2 回归显式依赖 nghttp2，必须将所选参考能力固定。

**源码与测试证据：**
- [按片序号进入通用重组状态逻辑](../sources/77_wireshark/files/epan/reassemble.c#L2464) / [固定上游](https://github.com/wireshark/wireshark/blob/455e49bcca6882e317d83d76feb86cf88a27df1f/epan/reassemble.c#L2464)
- [原生 HTTP2/gRPC 流式多帧重组与二次分析测试](../sources/77_wireshark/files/test/suite_dissection.py#L381) / [固定上游](https://github.com/wireshark/wireshark/blob/455e49bcca6882e317d83d76feb86cf88a27df1f/test/suite_dissection.py#L381)

实际定向阅读：reassemble.c:2464–2497；suite_dissection.py:381–410；TCP/dfilter 仅结构定位。

状态：素材已取；未构造题包、未构建/运行参考或候选、未运行模型，六小时难度未验证。
