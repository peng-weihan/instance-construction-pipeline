# 40_rsync 目录同步工具的过滤、链接、更新与多步状态兼容

路线：M5；优先级：build_scope_probe；状态：素材已取、范围待验证。
来源：[RsyncProject/rsync](https://github.com/RsyncProject/rsync/tree/b70a61f394d0d4c71ee349a9260b4ed8babbb6be)；固定版本 `b70a61f394d0d4c71ee349a9260b4ed8babbb6be`。

**已有能力：** 固定rsync已实现目录作用域过滤、删除、硬链接和增量更新回归。参考实现可用于作者观察，学生环境与被执行提交不委托目标rsync。

**拟交付：** 明确支持范围内的本地目录同步替代实现：文件选择、目录层级、过滤/保护、链接、更新和itemized输出，连续多次运行后文件树及副作用与参考一致。远端协议首轮不自动纳入。

**拟缺口：** 构造新的兼容实现规格和可构建骨架；实现语言/部署约束须预先作为产品目标公开，普通文件/校验库保持允许。

**工程链：** 参数/过滤规则 → file list → generator决策 → receiver写入/链接 → 输出/退出 → 再次同步

**原题参照：** Git→Zig的多命令/持久副作用兼容；范围限定为另一独立工具。

**三个组合场景（设计）：**

1. 初次同步含硬链接的树→目标局部被改写→再次更新，内容与硬链接关系和输出保持参考契约。
2. 按目录加载filter，P保护与普通exclude同时存在，再执行delete-excluded，检查最终集合和受保护文件。
3. 首次同步后移动/删除/新增源文件，dry-run与实际运行，再次运行无多余变化；检查退出码与文件元数据。

**基础完成后的剩余工作假设：**

- 基本复制完成后，过滤/保护/删除优先级仍可能要求统一决策模型。
- 单次正确后，跨次增量、链接身份和dry-run/itemize一致性仍可能存在工作。

**独立评测：** 固定reference＋独立文件树快照：内容、类型、链接关系、约定时间/权限和退出码。每场景独立临时根，固定locale/umask。

**最强正常基线：** 标准库全量copy＋现成ignore/path工具。若完整满足公开合同就允许；不凭空要求delta算法或用重复文件堆难度。

**首个否证探针：** 在同文件系统普通UID下跑gold的过滤/硬链接/二次同步，再用简单全量复制方案验证是否只剩少量参数适配。

**许可观察：** 根COPYING包含GPLv3文本及OpenSSL/xxhash例外；具体分发文件和第三方依赖单列。

**离线和资源：** POSIX硬链接/时间精度/权限需统一；不以root专属chown或不同平台偶然输出作难点。远端SSH与daemon运行不在已取得运行证据内。

**已读证据：**

- [目录作用域filter及遇I/O错误时的删除决策](../sources/40_rsync/files/generator.c#L320) / [固定上游](https://github.com/RsyncProject/rsync/blob/b70a61f394d0d4c71ee349a9260b4ed8babbb6be/generator.c#L320)
- [保护规则与exclude在delete-excluded下的不同效果](../sources/40_rsync/files/testsuite/delete_test.py#L88) / [固定上游](https://github.com/RsyncProject/rsync/blob/b70a61f394d0d4c71ee349a9260b4ed8babbb6be/testsuite/delete_test.py#L88)
- [改写后再次同步仍保持硬链接及跨批次场景](../sources/40_rsync/files/testsuite/hardlinks_test.py#L43) / [固定上游](https://github.com/RsyncProject/rsync/blob/b70a61f394d0d4c71ee349a9260b4ed8babbb6be/testsuite/hardlinks_test.py#L43)

定向阅读范围：generator.c:320-363；delete_test.py:86-109；hardlinks_test.py:20-75；manpage仅定向定位。

未构造题包、未运行gold/候选/容器/模型，未验证六小时难度。下载文件是选读材料，不是完整checkout或依赖包。
