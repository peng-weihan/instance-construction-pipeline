# 39_rustls TLS记录、握手恢复与应用I/O的关联状态恢复

路线：M4；优先级：hold_harness_probe；状态：素材已取、范围待验证。
来源：[rustls/rustls](https://github.com/rustls/rustls/tree/d37c3c338fe30c3fdc70f0696997909ffd15f5b8)；固定版本 `d37c3c338fe30c3fdc70f0696997909ffd15f5b8`。

**已有能力：** 上游已有early-data状态与长度检查、ticket获取/消费和多次恢复测试；不是待实现的上游功能。

**拟交付：** 恢复固定Rustls版本的有限TLS1.3会话与记录生命周期实现，保留可信密码provider和证书fixture；不用手写密码原语增加工作。

**拟缺口：** 受控恢复跨握手/会话/应用数据的实现，具体缺口和参考互通尚未构造；需区别于原EdgeBench的Python trace状态机。

**工程链：** record分片 → handshake状态/transcript → session ticket → early/app data → close/error

**原题参照：** regex-automata式跨表示恢复；原TLS trace任务仅作机制参照，不复制其题目或检查。

**三个组合场景（设计）：**

1. 完整握手取得ticket→多次尝试恢复→按参考契约消费ticket，耗尽后走完整握手。
2. early-data分片跨多个输入到达，长度超限或消息次序错误被拒绝；正常握手继续的边界需明确。
3. 应用部分读写、对端关闭和alert交错，公开API返回与资源生命周期保持一致。

**基础完成后的剩余工作假设：**

- 完整握手可用后，ticket消费、恢复兼容性及early-data状态仍可能未闭合。
- 内存pair通过后，部分I/O、关闭和错误路径可能要求记录层与API协同。

**独立评测：** 固定证书/随机源/crypto provider下的原生pair测试及独立TLS对端；随机密文不直接作逐字节相等判据。

**最强正常基线：** 保留crypto provider并用成熟TLS组件/API适配；如果正常适配就完成所有公开行为，应重估恢复范围。

**首个否证探针：** 先编译健康gold及离线pair测试，再判断是否可确定地恢复完整状态链；验证引用原版TLS材料的重复风险。

**许可观察：** 根LICENSE声明Apache-2.0、MIT、ISC三选一；三份文本均已取得，crypto及证书材料另核。

**离线和资源：** 密码provider可能带原生构建/汇编依赖；离线构建、固定熵源与x86/ARM未验证。本任务是基准素材研究。

**已读证据：**

- [early-data上限及EndOfEarlyData推进状态](../sources/39_rustls/files/rustls/src/server/tls13.rs#L1245) / [固定上游](https://github.com/rustls/rustls/blob/d37c3c338fe30c3fdc70f0696997909ffd15f5b8/rustls/src/server/tls13.rs#L1245)
- [ticket使用、并行尝试和耗尽后不恢复的测试](../sources/39_rustls/files/rustls-test/tests/api/resume.rs#L327) / [固定上游](https://github.com/rustls/rustls/blob/d37c3c338fe30c3fdc70f0696997909ffd15f5b8/rustls-test/tests/api/resume.rs#L327)

定向阅读范围：server/tls13.rs:1240-1300；resume.rs:327-403；client/io文件只做关键词定位。

未构造题包、未运行gold/候选/容器/模型，未验证六小时难度。下载文件是选读材料，不是完整checkout或依赖包。
