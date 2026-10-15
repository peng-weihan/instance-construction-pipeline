# 策略协议

提交目录根为 policy.py，可带自己的 Python 模块和参数文件。评分器只调用 initialize(metadata) 与 decide(history,state)。

- initialize 每次评分调用一次，metadata 包含 assets 和 mandate；返回值成为首个 state.user_state。初始化异常属于无效提交。
- decide 每个评分交易日调用一次，必须返回一个 dict，包含 weights、risk_scale、variance_daily、q05_daily、rebalance、rebalance_reason。weights 的键必须恰为 assets；rebalance 必须是真正的 bool。
- 可选 user_state 字段会成为下一日的 state.user_state；省略时沿用上次状态。状态仅在同次评分中保留，不跨提交。策略不能修改可信账本状态。
- history.assets 给出 prices 每行的列顺序；dates 与 prices 等长。最多 253 行，最后一行是执行交易所用的前一收盘价。当天收益在决策之后才进入可信账本。
- state.day_index 从该评分区间的 0 开始，不是整个训练集的行号。其他字段为 weights、cash_weight、nav、last_rebalance_index、mandatory_rebalance、recent_forecasts、user_state。
- recent_forecasts 最多包含最近 20 个已完成时点的 date、return、variance_daily、q05_daily。不存在当前或未来收益。初始持仓为全现金；首次决策必须修复最低风险资产敞口要求。
- 无调仓时 weights 必须等于输入的漂移权重；风险缩放仍在范围内，预测仍必须有限。risk_scale 不会自动重新缩放权重。

约束、成本和风险目标以 mandate.json 为准，记账顺序见 accounting.md。评分公共区间使用 dev，训练数据只提供历史上下文；隐藏反馈和审计使用各自时间区间。stdout 会被适配器重定向到 stderr，不作为评分结果。
