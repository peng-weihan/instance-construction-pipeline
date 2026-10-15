# K06_PYPSA · PyPSA 能源规划

状态：潜力 high / hold_baseline；素材研究，未构题/运行/难度验收。
来源：[PyPSA/PyPSA](https://github.com/PyPSA/PyPSA/tree/6c45594596cbc5612511ee9202a9e269e5001d88)
固定版本：`6c45594596cbc5612511ee9202a9e269e5001d88`
来源单元：优化接口、储能回归测试和storage-hvdc小网络CSV
材料：[manifest](../sources/k06_pypsa/manifest.json)，含文件树、原文URL和SHA256。

拟题：**电网与储能投资的情景规划审计**
给定多期负荷、风光时序、成本和排放预算，交付容量/储能/输电投资建议及逐时运行证据，比较低成本、可靠性与政策约束下的方案。
交付：投资方案表、可重算调度与排放账本、约束核对、情景敏感性及面向决策者的建议。

自然难点一：储能跨时段守恒、网架瓶颈和投资期权重相互制约，年度总量平衡不足以保证逐时供电。
自然难点二：成本、排放和可靠性假设改变方案排序，必须把建议与可复核的运行证据一致起来。
正常基线：允许直接调用PyPSA/HiGHS正常求解，先用默认容量扩展+逐情景求解并生成标准报告。
首个探针：用小storage-hvdc网络闭合单位、时序权重、储能守恒和情景报告；评估现成notebook是否已覆盖合同。
降级/淘汰：若题目只是正确填表后一次optimize即全解，则作为专业练习不评高难；不能靠禁用求解器增难。

独立评分：独立重算投资/运行成本、逐时平衡、线容量、SOC和排放；报告结论需引用方案单元格和情景计算，定性判断依预声明规则，不只比最优cost。
生成与划分：用小网络程序生成负荷/可再生相关时序、网架瓶颈、成本和政策情景；按时序机制/瓶颈族留出，公开原CSV仅开发例。
谱系/污染：不同于现有金融与地下水反演；与组合优化共享LP但交付是可审计能源决策。不能把同库多电网seed计新来源。
离线与计算：已取小CSV和接口/测试，未取得完整电网/气象数据；优先合成网+固定HiGHS，CPU模型规模待测。
许可观察：根MIT；真实电网和气象数据授权独立核对，小CSV来源权属随发行再审。

证据：[1](https://github.com/PyPSA/PyPSA/blob/6c45594596cbc5612511ee9202a9e269e5001d88/pypsa/optimization/optimize.py#L550)；[2](https://github.com/PyPSA/PyPSA/blob/6c45594596cbc5612511ee9202a9e269e5001d88/test/test_lopf_storage.py#L14)；[3](https://github.com/PyPSA/PyPSA/blob/6c45594596cbc5612511ee9202a9e269e5001d88/pypsa/optimization/optimize.py#L682)
证据1：原生optimize支持多投资期、输电损耗、机组约束及extra_functionality，默认求解器为HiGHS。
证据2：储能回归测试将优化发电时序与固定参考比较，并构造跨时段储能小系统。
证据3：求解后只有status=ok才赋值solution/duals并后处理，判题要验证状态而非读取残留结果。
实际选读：pypsa/optimization/optimize.py:550-595；test/test_lopf_storage.py:14-47；pypsa/optimization/optimize.py:682-700
覆盖边界：上述定向阅读，不推断整个仓库均已审计。
