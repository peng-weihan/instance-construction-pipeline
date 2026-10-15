# K01_BEANCOUNT 多币种交易与成本批次的月结核对案卷

- 类别：knowledge；潜力：high；优先级：scope_probe。素材研究，未构题/运行/验证难度。
- 主来源：beancount/beancount@9747213802acb733ce53acc6e963f5961f47d6cd。
- 固定版本清单：[manifest](../sources/k01_beancount/manifest.json)。
- 本项素材单元：booking/余额断言、小账簿与账簿生成器；未来原始凭证包尚待独立生成

## 拟交付与难度

给定新生成的银行流水、交易凭证和公开会计政策，交付可核账簿、差异解释、成本批次与月结报表；允许现成Beancount。
- 交付：分录账簿、逐凭证到分录映射、余额/损益表及差异说明。
- 难度来源：同一交易的币种、成本批次和前序库存共同决定记账，单笔平衡不保证期间余额/批次正确。
- 难度来源：漏单、重复、跨期与冲销需要跨材料对账，完整证据链比单次调用记账器多实质工作。

## 验证与划分

- 正常基线：原生Beancount+正常导入/规则工具、Decimal表格核算；不能要求重实现会计引擎。
- 首个探针：用短导入脚本和健康Beancount完成一套原创凭证旅程，检查是否还有真实对账/政策选择工作。
- 停止条件：资料已直接给完整分录或规则映射即可全解，或评分只有排版主观印象，则重设案卷。
- 独立评测：独立事件账本与Decimal计算检查双重记账、余额、批次和报表；核对凭证引用与差异归因，叙述质量另订rubric。
- 生成与划分：由隐藏经济事件生成多份可交叉核对凭证，按业务事件/币种/跨期结构拆分；公开example账簿不直接作为hidden答案。
- 谱系/重叠：与金融策略共享会计/现金概念，但主交付是结账证据与报表，不是投资收益；需新凭证实体和政策案例。
- 离线/计算：CPU Python加parser扩展，原生成器只生成账簿，未制作原始凭证包或健康评分；无真实个人财务信息。
- 许可观察：根GPL-2.0文本；凭证另按原创生成授权，示例头和关联工具许可各核。

## 选读证据

- [beancount/parser/booking_full.py:150](https://github.com/beancount/beancount/blob/9747213802acb733ce53acc6e963f5961f47d6cd/beancount/parser/booking_full.py#L150)：booking按前序库存与币种组处理交易，并处理lot reduction与插值容差。
- [beancount/ops/balance_test.py:13](https://github.com/beancount/beancount/blob/9747213802acb733ce53acc6e963f5961f47d6cd/beancount/ops/balance_test.py#L13)：原生余额测试给出跨交易的具体账簿与余额错误断言。
