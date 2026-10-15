# 30_mitmproxy — 会话隔离与动态关联的离线 HTTP 工作流回放版本
- 来源：[mitmproxy/mitmproxy](https://github.com/mitmproxy/mitmproxy)；固定版本 `77355977e5ea540b51ed029a40ed1dc2f1c2ba7b`。
- 路线：M1_existing_project_roadmap；优先级：`build_scope_probe`。
- 许可观察：根 LICENSE 显示 MIT，pyproject 分类亦为 MIT；保留版权许可；mitmproxy_rs、TLS/压缩等依赖与测试证书需单独清点。
- 证据层级：已固定文件树和摘录哈希，已读核心实现与原生测试；未 clone/build/运行模型。
- 状态：task_constructed=false；runtime_verified=false；difficulty_verified=false。

## 已有能力与拟新增范围
- 已有：已有服务端哈希匹配/响应队列、指定请求头和忽略参数匹配、响应日期刷新、客户端队列与串行/无限并发、flow metadata 及文件持久化。
- 拟新增：拟增加声明式多步场景、每会话变量捕获/替换、依赖调度、会话隔离与可复现结果报告；未确认整个插件生态不存在同能力，也未运行复现。
- 产品交付：面向团队复现登录→创建→查询→删除等 HTTP 业务链，交付场景格式/校验、客户端执行器与离线服务端匹配模式、取消/失败清理、兼容旧 replay 命令及导出报告。首版限 HTTP，WebSocket 只按原行为回归。

## 实际模块链与证据
- [`mitmproxy/addons/serverplayback.py:177`](https://github.com/mitmproxy/mitmproxy/blob/77355977e5ea540b51ed029a40ed1dc2f1c2ba7b/mitmproxy/addons/serverplayback.py#L177)：服务端匹配键来自请求字段及配置，不应把可配置匹配宣称缺失
- [`mitmproxy/addons/serverplayback.py:225`](https://github.com/mitmproxy/mitmproxy/blob/77355977e5ea540b51ed029a40ed1dc2f1c2ba7b/mitmproxy/addons/serverplayback.py#L225)：已有按哈希消费响应队列/复用
- [`mitmproxy/addons/clientplayback.py:174`](https://github.com/mitmproxy/mitmproxy/blob/77355977e5ea540b51ed029a40ed1dc2f1c2ba7b/mitmproxy/addons/clientplayback.py#L174)：现有执行器使用全局请求队列与串行或无限并发模式
- [`mitmproxy/addons/clientplayback.py:196`](https://github.com/mitmproxy/mitmproxy/blob/77355977e5ea540b51ed029a40ed1dc2f1c2ba7b/mitmproxy/addons/clientplayback.py#L196)：已有 live/intercepted/missing/WebSocket 回放约束
- [`mitmproxy/flow.py:143`](https://github.com/mitmproxy/mitmproxy/blob/77355977e5ea540b51ed029a40ed1dc2f1c2ba7b/mitmproxy/flow.py#L143)：flow metadata 已随状态序列化，可作为扩展基线
- [`mitmproxy/io/io.py:43`](https://github.com/mitmproxy/mitmproxy/blob/77355977e5ea540b51ed029a40ed1dc2f1c2ba7b/mitmproxy/io/io.py#L43)：已有 HAR/原生 flow 读取，场景格式不能替代兼容回归
- [`test/mitmproxy/addons/test_clientplayback.py:59`](https://github.com/mitmproxy/mitmproxy/blob/77355977e5ea540b51ed029a40ed1dc2f1c2ba7b/test/mitmproxy/addons/test_clientplayback.py#L59)：真实本地 HTTP/HTTPS/upstream 与两种并发的原生测试
- [`test/mitmproxy/addons/test_serverplayback.py:209`](https://github.com/mitmproxy/mitmproxy/blob/77355977e5ea540b51ed029a40ed1dc2f1c2ba7b/test/mitmproxy/addons/test_serverplayback.py#L209)：原生测试覆盖队列顺序与响应消费

## 三个端到端场景
1. 两位用户交错完成登录→创建→查询，响应产生的不同 ID/token 正确进入各自请求，会话间不串变量。
2. 中间步骤返回失败或被取消，后继依赖请求不发出，其余会话继续；停止后无悬挂任务，报告区分失败、跳过与取消。
3. 保存/重载场景后离线重放，匹配消费和报告可复现；录制 flow 保持原内容，旧 server/client replay 命令仍工作。

## 难度否证与剩余工作
- 最强正常基线：内置 client/server replay + use_headers/ignore_params + 官方 addon scripting 实现捕获与替换；允许现有 cookie/header 管理插件，先核实是否可直接满足整体契约，不能人为禁止正常组合。
- 首个否证探针：先做极小 addon：从响应 JSON 捕获 ID 并替换后续 path/header，再执行两个交错会话；若原生队列+配置已保证隔离/取消/报告且只需薄 glue，则降级或换题。尚未执行。
- 早期实现后仍可能剩余（假设）：单会话 token/ID 替换成功后，多会话并发中变量作用域、顺序依赖、失败后的后继跳过及确定性消费仍可能未解决。
- 早期实现后仍可能剩余（假设）：单次业务链成功后，取消在途请求、重复启动/重载场景、原始录制不可变、报告/流导出可复现及旧命令兼容仍需跨生命周期验证。

## 评测与环境
- 独立评测及原生回归：独立 loopback HTTP 服务记录请求顺序、token/ID 归属和活跃连接；用可控 barrier 驱动交错/取消而非睡眠猜测；原生 test_clientplayback/test_serverplayback 与 flow IO 回归，报告不作为唯一 oracle。
- 离线与跨架构：Python>=3.12，含 mitmproxy_rs 与 cryptography 等原生依赖，必须预置目标架构 wheels/工具链；首轮 loopback HTTP 与测试 CA，避免公网、真实账号、根权限透明代理；TLS 与 ARM64/x86_64 安装待验证。
