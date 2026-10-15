# K08_OPENQUAKE · OpenQuake 风险评估

状态：潜力 high / hold_data；素材研究，未构题/运行/难度验收。
来源：[gem/oq-engine](https://github.com/gem/oq-engine/tree/cf5abdc04016ca9220d8e916432590c1a4e64249)
固定版本：`cf5abdc04016ca9220d8e916432590c1a4e64249`
来源单元：脆弱性计算、classical risk回归测试和含暴露/危害/损失参考的小案例
材料：[manifest](../sources/k08_openquake/manifest.json)，含文件树、原文URL和SHA256。

拟题：**资产群地震风险与加固投资建议**
基于给定暴露清单、危险度曲线、脆弱性和加固选项，交付损失评估、预算内加固组合及风险降低/不确定性说明。
交付：资产分类/单位审计、基准和加固后损失表、预算分配、尾部风险/敏感性及证据报告。

自然难点一：资产分类与脆弱性对应错误会系统改变损失，不能仅把坐标和价值输入黑箱。
自然难点二：加固方案在均值损失、尾部风险和有限预算间取舍，脆弱性假设变化可推翻排序。
正常基线：运行原生classical risk小例，按预期年损失降低/成本贪心加固，允许正常调用OpenQuake和优化库。
首个探针：先以已取exposure/vulnerability/hazard小例核对expected CSV，另构可手算的两资产加固例；确认加固前后脆弱性与会计口径。
降级/淘汰：若只运行公开job.ini并复述CSV即完成合同则不算难；缺少可信加固成本/效果或参考风险闭合时先hold_data。

独立评分：私有数据重新计算资产聚合、预算和方案风险；检查分组/合计/单位、敏感性与引用一致，评分风险改善和解释约束，不只最小cost。
生成与划分：优先合成暴露/危害与加固选项，控制相关性及脆弱性误设；按区域/建筑类别组合留出，公开case只用于健康检查。
谱系/污染：独立灾害/工程风险方向，不是投资组合金融；地震预测/反演属科学，当前任务交风险决策与证据链。
离线与计算：完整引擎及依赖未构建，已取小XML/CSV/job和期望输出；大规模危险度/全球资产数据未下载。
许可观察：根AGPL-3.0；外部危险度和暴露数据单独授权，发行容器/服务方式需匹配条款。

证据：[1](https://github.com/gem/oq-engine/blob/cf5abdc04016ca9220d8e916432590c1a4e64249/openquake/risklib/scientific.py#L186)；[2](https://github.com/gem/oq-engine/blob/cf5abdc04016ca9220d8e916432590c1a4e64249/openquake/calculators/tests/classical_risk_test.py#L26)
证据1：VulnerabilityFunction定义强度、均值损失率、变异系数及LN/BT等分布，并检查输入。
证据2：classical risk测试对导出平均损失/损失曲线/风险图与参考CSV比较，拒绝超范围概率。
实际选读：openquake/risklib/scientific.py:186-230；openquake/calculators/tests/classical_risk_test.py:26-47
覆盖边界：上述定向阅读，不推断整个仓库均已审计。
