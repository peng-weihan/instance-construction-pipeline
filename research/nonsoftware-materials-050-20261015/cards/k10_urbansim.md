# K10_URBANSIM · UrbanSim 城市规划

状态：潜力 medium / hold_data；素材研究，未构题/运行/难度验收。
来源：[UDST/urbansim](https://github.com/UDST/urbansim/tree/1a9a68e9bfe34dd31c68bf9480c4fc65334663e0)
固定版本：`1a9a68e9bfe34dd31c68bf9480c4fc65334663e0`
来源单元：区位选择、供需调价、人口转移模型与合成fixture测试
材料：[manifest](../sources/k10_urbansim/manifest.json)，含文件树、原文URL和SHA256。

拟题：**住房供给情景的城市分布影响评估**
给定合成地块/家庭/就业和已说明区位选择模型，比较分区或住房供给方案，交付分布影响、容量/预算核对与敏感性建议。
交付：基准/备选情景表、家庭/住房/就业账本、分群可达性/价格/迁移影响、模型假设与建议。

自然难点一：家庭选择概率与住宅容量约束共同决定分配，增建总量不等于目标群体实际获得住房。
自然难点二：供需调价与迁移改变后续分布，方案优劣取决于行为参数和政策目标，不能只报一个均值。
正常基线：按现有容量比例分配、一次区位选择+官方供需模型，允许直接使用UrbanSim模型和成熟统计方法。
首个探针：先用原生合成fixture闭合人口/容量守恒和价格调整，再看多个备选情景的结论是否可独立复算；专业情景数据尚待生成。另检查非字符串alt_segmenter分支的类型错误风险，先冻结可用字符串列接口。
降级/淘汰：若只是运行官方示例和描述图表则下调；若没有明确评价目标/模型可识别性而只能主观判报告，则hold_data。

独立评分：核对容量、人口/岗位守恒、预算、分群指标和模型版本；对同一给定模型重算情景及敏感性，以证据一致性和预声明目标评分，不把政策偏好当唯一真答案。
生成与划分：合成地块/家庭分布、容量、行为参数和政策限制，按空间结构/人群相关性留出；真实城市数据只有授权与可复算后再引入。
谱系/污染：独立城市发展专业任务，交评估方案而非训练预测模型；同模型不同城市不能机械计新来源。
离线与计算：pandas/统计依赖较旧需冻结；已取源码、测试和小travel数据，不含完整真实城市模型/私有家庭微观数据。
许可观察：根BSD式再分发条款；真实地块/家庭/就业数据许可与隐私处理另定，当前仅公开测试与拟生成合成数据。

证据：[1](https://github.com/UDST/urbansim/blob/1a9a68e9bfe34dd31c68bf9480c4fc65334663e0/urbansim/models/supplydemand.py#L84)；[2](https://github.com/UDST/urbansim/blob/1a9a68e9bfe34dd31c68bf9480c4fc65334663e0/urbansim/models/tests/test_supplydemand.py#L103)；[3](https://github.com/UDST/urbansim/blob/1a9a68e9bfe34dd31c68bf9480c4fc65334663e0/urbansim/models/supplydemand.py#L134)
证据1：供需函数按子市场迭代调整价格并设变化裁剪，依赖已拟合区位选择模型。
证据2：测试用合成价格和子市场倍率比较五轮调价及base_multiplier效果，提供可独立复算的小fixture。
证据3：实现逐轮乘价格并累计子市场倍率，先复制alternatives再过滤；非字符串alt_segmenter分支需健康测试（源码使用isinstance(..., np.array)）。
实际选读：urbansim/models/supplydemand.py:84-130；urbansim/models/tests/test_supplydemand.py:103-150；urbansim/models/supplydemand.py:134-173
覆盖边界：上述定向阅读，不推断整个仓库均已审计。
