# 主分析交叉验证

三组均完成后才合并。主分析抽查17个额外行区间，记录见root-cross-checks.json。

- 产品/CLI：确认Alembic自动生成无法识别表/列rename，但原生rename操作存在；Task已有输入指纹和执行生命周期，工件恢复仍是拟题设计；SQLFluff空渲染占位符回归确实保留原模板而修复别处缩进。未把这些旧功能说成新缺口。
- 系统/状态：确认Cap’n Proto旧schema handle随升级观察到新版本且仍可按旧类型使用，不能扩成任意并发load；Flecs merge中observer添加Position的行为有原生断言；yq相对更新children-first和alias/explode组合有回归。Thrift/Capn/Flecs应另按恢复路线构题，原库存标签未改。
- 恢复：确认Jinja super按当前block找下一层，编译器finally执行close/aclose；Helix选择区按方向映射粘性，History保存逆操作/原选区并按LCA组合；Tantivy自动reload不是提交屏障，失败commit不可见有明确原生测试。不能以未保证的异步时序构造判错。
- Miller的mixed-format/0001命令确实只有JSON双输入，跨格式交付保留为设计，未宣称已运行或核验。
- 性能由主分析负责，10项全部保留B。已有配置和算法均纳入强基线假设，未测得剩余收益。

跨源谱系：SQLFluff/Jinja/dbt共享模板语义，Ruff/syn/其它parser共享恢复机制，消息与schema来源存在协议/算法谱系。14个A不是14个独立任务族，也不是14个验收题。

所有A仍待健康starter/强替换基线。没有根据已有源码复杂度推出恢复缺口难度，未以作者工具链或噪声成本替代求解难度。
