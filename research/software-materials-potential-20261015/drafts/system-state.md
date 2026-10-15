# 系统与状态链：15 项高难出题潜力复评

这部分承接已完成的材料库存，判断规格/状态复杂性在合理 starter 下是否仍由求解者完成；它为跨路线选题排序提供语义依据。只针对固定版本片段定向选读，不是全仓架构审计，未达到或宣称 repo-analyzer 全仓覆盖阈值，也不计算虚构覆盖百分比。

15 项均至少核对一处实现和一处原生测试或规范。没有制作缺口、构建运行健康参考、测强基线或执行求解实验；A 仅表示优先细化。

分档：{'C': 7, 'A': 5, 'B': 3}。A 5 / B 3 / C 7 / D 0。potential 记录系统语义的高难上限，与当前拟题成熟度分开。

## 关键结论

- 优先细化 Cap’n Proto、Flecs、rsync、yq、Miller：身份/生命周期、defer/observer、链接/跨次同步、树节点/alias 更新、typed record/DSL/EOS 等把多个交付阶段连成共享状态。基础功能完成后仍有自然剩余工作。
- Thrift、restic、Wireshark 条件保留：分别卡在可构建恢复边界、成熟组件/整工具代理和格式范围、离线健康参考/两遍重组能力与依赖。
- Mosquitto、BMv2、Avro、NATS、GraphQL、CEL、FlatBuffers 判 C 针对当前宽泛系统合同。完整上游工具存在不是降档依据；真正问题是库存尚未给出合理 starter/宿主/产物边界，使复杂性成为求解者剩余工程。各卡保留具体宿主或恢复重开方向，先用正常依赖验证。
- Thrift、Cap’n Proto、Flecs 的库存 route=M2，但现范围实质是模块恢复，建议归 M4。原库存不改，也不把掩码恢复标成新增上游功能。

## 需要主代理交叉核对

1. Cap’n Proto 的公开 load/loadOnce 契约与 Upgrade 测试：保持旧 handle 后升级是可观测生命周期，不应扩成不受保证的任意并发 load。
2. Flecs Commands_add_in_observer_during_merge 表明 merge 后 observer 引发的 Position 也必须存在；通用队列+immediate API+全扫描仍是合法淘汰基线。
3. yq 相对赋值按 children-first 遍历，alias 测试改变 .a 后 .b/.c 同变；不能由此顺便声称 encoder/in-place 链已完整核验。
4. Miller 名为 mixed-format 的所读 fixture 0001 实际是 JSON 双输入；不能把文件夹名称当成 CSV+JSON 跨格式运行证据。
5. Wireshark 测试明确 nghttp2 和 -2 两遍分析依赖；构建时间不能算求解难度。

## 逐项判断

| 来源 | 档 | 上限 | 作者成本 | 当前关键判断 |
|---|---|---|---|---|
| 31_mosquitto | C | high | high | 当前泛化 broker 合同重设范围；可保留嵌入宿主事务存储/事件调度的持久会话引擎，或自然连通的受损会话子系统恢复。宿主 ABI 与持久点约束须来自真实应用目标，不能临时挡原工具。 |
| 32_bmv2 | C | high | high | 当前离线子集解释器合同重设为真实宿主内的 packet/控制状态执行接口，或连通模块恢复；冻结 JSON feature manifest，不笼统重写 P4。 |
| 33_avro | C | high | medium | 当前 schema/codec/resolution/OCF CLI 重设；可保留与宿主类型身份/投影执行计划集成的系统或受损连通实现，需先找到真实产物缺口。 |
| 40_rsync | A | high | medium | M5 独立可部署本地目录同步替代实现：目录作用域 filter/保护/delete、硬链接、更新、dry-run/itemize 与多次同步结果；固定 POSIX，先排远程协议。独立部署契约需公开，普通文件/校验库允许。 |
| 50_thrift | B | high | high | 建议按 M4 恢复题细化：跨文件 include/type/constant/service 共享语义→JSON 反射和固定 Python 生成；保留 lexer/语法框架与低层 runtime。 |
| 51_capnproto | A | high | high | 建议 M4 恢复进程内 schema 生命周期：同 ID 升降级、stub 依赖、旧 handle、dynamic struct/list/union 与静态绑定互通；首轮无需 RPC。 |
| 52_flecs | A | high | high | 建议 M4 恢复一帧 ECS 世界演进：defer 可见性→merge/add/set/remove/delete→observer 重入→查询结果与 changed；固定单 stage，保留实体存储与即时操作基础。 |
| 53_nats | C | high | high | 当前泛化单节点 JetStream 子集重设范围；可保留宿主事务日志/虚拟时钟/进程内状态 API 集成或自然连通受损 consumer/store 恢复，先给实际 starter。 |
| 54_graphql | C | high | medium | 当前通用 GraphQL 服务内核重新限定；可考虑真实宿主 resolver/typed-value/事件资源生命周期的执行引擎集成或受损 completion/error 链恢复。不能仅加 HTTP endpoint。 |
| 55_cel_go | C | high | medium | 当前通用 CEL compile/eval API 重设；可保留与真实宿主对象/unknown/成本记账接口相关的运行时集成，或 typed AST→plan→activation 受损链恢复。固定基础 CEL 功能集。 |
| 56_flatbuffers | C | high | medium | 当前 .fbs→binary/reflection/verifier CLI 重设；仅在真实新语言后端/宿主 ABI 与动态对象布局集成、或连通受损实现恢复时继续。 |
| 72_yq | A | high | medium | M5 多文档 YAML 更新兼容：限定选择/递归/绝对和相对赋值/删除/合并表达式，联动 node identity、alias、tag/style/comment 与原位文件更新；不声称支持全部 yq。 |
| 73_restic | B | high | high | M5 本地固定格式仓库的独立兼容客户端：init→backup→增量 snapshot→选择 restore→check；先定 Linux 元数据子集及 v1/v2。云后端/账号不进入首版。 |
| 76_miller | A | high | medium | M5 typed CSV/JSON→限定 DSL begin/main/end→filter/group/join→writer/CLI 的记录流兼容；选有状态完整工作流，不以全部 verbs 数量为目标。 |
| 77_wireshark | B | high | high | M5 合成 PCAP 的有限离线分析替代：Ethernet/IP/TCP 加明确应用协议，跨帧重组→字段/类型过滤→固定 TShark 输出；首版先选健康参考可稳定支持的协议，不含 GUI/实时捕获。 |


## 实际阅读范围

下表列出实际请求并阅读的区间；文件未读部分和未获取实现不计。大文件仅选段，不声称该文件达到 30% 阅读覆盖。类型为测试/规格的 API 头仅用于契约核对。

| 来源 | 文件 | 行区间 | 类型 |
|---|---|---|---|
| 31_mosquitto | sources/31_mosquitto/files/src/database.c | 1071–1119 | implementation |
| 31_mosquitto | sources/31_mosquitto/files/test/broker/15-persist-client-msg-out-v5-0.py | 30–109 | test_or_spec |
| 32_bmv2 | sources/32_bmv2/files/src/bm_sim/match_tables.cpp | 75–123 | implementation |
| 32_bmv2 | sources/32_bmv2/files/tests/test_parser.cpp | 201–246 | test_or_spec |
| 33_avro | sources/33_avro/files/lang/c++/impl/parsing/ResolvingDecoder.cc | 160–214 | implementation |
| 33_avro | sources/33_avro/files/doc/content/en/docs/1.12.0/Specification/_index.md | 681–731 | test_or_spec |
| 40_rsync | sources/40_rsync/files/generator.c | 320–363 | implementation |
| 40_rsync | sources/40_rsync/files/testsuite/delete_test.py | 86–105 | test_or_spec |
| 40_rsync | sources/40_rsync/files/testsuite/hardlinks_test.py | 20–75 | test_or_spec |
| 50_thrift | sources/50_thrift/files/compiler/cpp/src/thrift/thrifty.yy | 310–355 | implementation |
| 50_thrift | sources/50_thrift/files/compiler/cpp/tests/cpp/t_cpp_parser_string_constant_tests.cc | 28–85 | test_or_spec |
| 51_capnproto | sources/51_capnproto/files/c++/src/capnp/schema-loader.c++ | 622–683 | implementation |
| 51_capnproto | sources/51_capnproto/files/c++/src/capnp/schema-loader-test.c++ | 193–252 | test_or_spec |
| 51_capnproto | sources/51_capnproto/files/c++/src/capnp/schema-loader.h | 97–169 | test_or_spec |
| 51_capnproto | sources/51_capnproto/files/c++/src/capnp/dynamic.c++ | 173–218 | implementation |
| 52_flecs | sources/52_flecs/files/src/commands.c | 1199–1264 | implementation |
| 52_flecs | sources/52_flecs/files/test/core/src/Commands.c | 1–68 | test_or_spec |
| 52_flecs | sources/52_flecs/files/test/core/src/Commands.c | 3092–3158 | test_or_spec |
| 52_flecs | sources/52_flecs/files/src/query/cache/change_detection.c | 79–125 | implementation |
| 53_nats | sources/53_nats/files/server/consumer.go | 3745–3811 | implementation |
| 53_nats | sources/53_nats/files/server/jetstream_consumer_test.go | 982–1041 | test_or_spec |
| 54_graphql | sources/54_graphql/files/src/execution/Executor.ts | 765–832 | implementation |
| 54_graphql | sources/54_graphql/files/src/execution/__tests__/nonnull-test.ts | 175–225 | test_or_spec |
| 55_cel_go | sources/55_cel_go_canonical/files/cel/env.go | 597–628 | implementation |
| 55_cel_go | sources/55_cel_go_canonical/files/cel/program.go | 467–511 | implementation |
| 55_cel_go | sources/55_cel_go_canonical/files/cel/cel_test.go | 2071–2120 | test_or_spec |
| 56_flatbuffers | sources/56_flatbuffers/files/include/flatbuffers/verifier.h | 147–213 | implementation |
| 56_flatbuffers | sources/56_flatbuffers/files/tests/parser_test.cpp | 833–887 | test_or_spec |
| 72_yq | sources/72_yq/files/pkg/yqlib/operator_assign.go | 1–82 | implementation |
| 72_yq | sources/72_yq/files/pkg/yqlib/operator_assign_test.go | 1–90 | test_or_spec |
| 73_restic | sources/73_restic/files/internal/archiver/archiver.go | 864–930 | implementation |
| 73_restic | sources/73_restic/files/cmd/restic/cmd_restore_integration_test.go | 102–170 | test_or_spec |
| 73_restic | sources/73_restic/files/doc/design.rst | 35–79 | test_or_spec |
| 76_miller | sources/76_miller/files/pkg/transformers/join.go | 18–60 | implementation |
| 76_miller | sources/76_miller/files/pkg/transformers/join.go | 399–458 | implementation |
| 76_miller | sources/76_miller/files/pkg/dsl/cst/root.go | 433–485 | implementation |
| 76_miller | sources/76_miller/files/test/cases/verb-join-mixed-format/0001/cmd | 1–1 | test_or_spec |
| 76_miller | sources/76_miller/files/test/cases/verb-join-mixed-format/0001/expout | 1–22 | test_or_spec |
| 77_wireshark | sources/77_wireshark/files/epan/reassemble.c | 2412–2462 | implementation |
| 77_wireshark | sources/77_wireshark/files/epan/reassemble.c | 2464–2520 | implementation |
| 77_wireshark | sources/77_wireshark/files/test/suite_dissection.py | 381–430 | test_or_spec |


所有逐项残余里程碑、强简单方案风险、首个淘汰探针、停止条件与 pinned 上游证据见 [system-state.json](system-state.json)。本复评不改原候选登记。

上述状态链判断给下一阶段明确的工作顺序：先证明普通依赖不能薄适配真实交付，再做健康 starter/独立 judge，最后用求解实验校准长程难度。
