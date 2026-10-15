# 48_apisix — Standalone 配置包的预检、分阶段激活与回退
- 来源：[apache/apisix](https://github.com/apache/apisix)；SHA `64a4afdd1353bd302f03cc8f0f780b8a78176137`；M1 / `build_scope_probe`。
- 已有：已有 YAML/JSON standalone、配置刷新/版本与 digest 应用状态、逐项 schema/plugin 检查、Admin 引用校验。不是新增热更新或普通 schema 验证。
- 拟任务缺口：拟增加资源包级 preflight、完整候选快照、按版本激活/回退与 worker 状态诊断；源码已逐项过滤无效资源，整体新契约是否必要待复现。
- 产品/子系统边界：单节点多 worker 的离线 gateway 交付：route/service/upstream/plugin_config 作为一份版本包验证；不完整包不替换 last-good；每个请求读取自洽版本并报告 worker 进度，不承诺跨节点瞬时原子提交。
## 模块链与固定证据
- [`apisix/core/config_yaml.lua:164`](https://github.com/apache/apisix/blob/64a4afdd1353bd302f03cc8f0f780b8a78176137/apisix/core/config_yaml.lua#L164)：已有内存配置版本更新
- [`apisix/core/config_yaml.lua:189`](https://github.com/apache/apisix/blob/64a4afdd1353bd302f03cc8f0f780b8a78176137/apisix/core/config_yaml.lua#L189)：已有 digest 对资源类型的应用记录
- [`apisix/core/config_yaml.lua:305`](https://github.com/apache/apisix/blob/64a4afdd1353bd302f03cc8f0f780b8a78176137/apisix/core/config_yaml.lua#L305)：资源按 schema/checker 逐项验证后插入
- [`apisix/admin/routes.lua:56`](https://github.com/apache/apisix/blob/64a4afdd1353bd302f03cc8f0f780b8a78176137/apisix/admin/routes.lua#L56)：Admin route 已验证 schema、upstream/service/plugin 引用
- [`t/admin/standalone-plugin-validation.t:48`](https://github.com/apache/apisix/blob/64a4afdd1353bd302f03cc8f0f780b8a78176137/t/admin/standalone-plugin-validation.t#L48)：原生测试明确缺失 plugin 会导致 standalone 路由匹配失败
## 组合场景
1. 一起切换 route→service→upstream 与插件参数，连续真实请求只得到对应版本的自洽响应。
2. 包中一个资源含未知插件或悬空引用，预检指出路径且继续服务旧版本，不静默丢弃相关路由。
3. 激活中一个 worker 重启，节点最终恢复同版本；显式回退后真实流量与状态都指向 last-good。
## 基线与退出
- 强合法基线：完整 YAML/JSON 原子文件替换 + 原生 validator/digest 状态 + 外部预检/发布包装器；不能禁止已有 APISIX 控制面或配置管理工具。
- 首探/退出：先把同一版本 route/service/upstream 全量文件替换并加入未知插件/坏引用，观测 last-good 与 worker 版本；若原生流程+短预检已满足全部契约则 hold。
- 早期完成后的剩余假设：合法包发布成功后，资源间引用、plugin merge/cache 与请求中途切换的版本一致性仍需验证。
- 早期完成后的剩余假设：单 worker 正常后，部分 worker 重启、无效更新后的 last-good、版本回退/状态报告可能未覆盖。
- 独立 oracle / 原生回归：独立 HTTP 后端标记版本、持续客户端与 worker 状态检查；保留 standalone YAML/JSON/plugin validation 和原生 Admin 回归，不用单次200或自报 digest 证明一致性。
- 许可观察：根 LICENSE Apache-2.0，NOTICE 已保留；OpenResty/Lua rocks 及镜像依赖另审。
- 离线/架构风险：需预置 OpenResty/LuaJIT、lyaml、Test::Nginx 等；只 standalone 无公网/etcd 首版，Linux目标镜像/多worker能力需另验，不能以 host mock代替。
- 官方在线核对：[primary](https://github.com/apache/apisix)；[primary](https://apisix.apache.org/docs/apisix/deployment-modes/)
- 仅完成定向源码/测试阅读，未构造完整题包或运行；task_constructed=false；runtime_verified=false；six_hour_difficulty_verified=false。
