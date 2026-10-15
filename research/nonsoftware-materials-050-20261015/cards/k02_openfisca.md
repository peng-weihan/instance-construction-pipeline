# K02_OPENFISCA 固定政策年度的家庭税负与改革影响分析

- 类别：knowledge；潜力：high；优先级：scope_probe。素材研究，未构题/运行/验证难度。
- 主来源：openfisca/openfisca-france@16b2e69633e840fdf5f39b74f96dfd2382898dd5。
- 固定版本清单：[manifest](../sources/k02_openfisca/manifest.json)。
- 本项素材单元：France所得税公式、明确2018年度PFU/barème测试；不是当前税务意见

## 拟交付与难度

给定冻结政策参数与原创家庭样本，交付改革前后税负、分组分布效应、边际税率与可追溯政策依据；模型可直接调用。
- 交付：可复算分析代码、家庭/分组结果表、改革差异分解与证据备忘录。
- 难度来源：家庭实体、年度和税基/扣除规则联合决定税负，按个人简单乘税率会破坏完整口径。
- 难度来源：改革会同时改变群体排序和分布指标，需要一致的反事实与证据链而非只报总额。

## 验证与划分

- 正常基线：原生OpenFisca模拟/改革API、表格分组与标准政策分析脚本；普通模型调用允许。
- 首个探针：先重现固定2018测试，再用最短模拟+groupby做一份原创改革案例，检查所需分析是否实质超出调用。
- 停止条件：仅调用一个变量并套固定报告即可全解，或缺少冻结参数/政策出处无法确定正确答案，则收紧范围。
- 独立评测：冻结健康引擎与独立小家庭手算对照税额；验证加权分布/差异、政策年度引用和案例一致性，叙述论证另订rubric。
- 生成与划分：合成家庭和自明改革参数，不用真实个人税表；按家庭结构/收入来源/年度边界拆分，政策版本锁定而不声称现行法规。
- 谱系/重叠：新主来源和专业政策案例；不能仅换人名/金额构造所谓全新任务族。与原专业知识范围的hidden材料仍未知。
- 离线/计算：完整OpenFisca-France/Core、参数树和依赖需离线锁定；当前只保存公式/测试片段，未取全部政策材料或执行。
- 许可观察：根AGPL-3.0；政策文献和参数来源条款另核，结果按冻结研究情境解释。

## 选读证据

- [openfisca_france/model/prelevements_obligatoires/impot_revenu/ir.py:1326](https://github.com/openfisca/openfisca-france/blob/16b2e69633e840fdf5f39b74f96dfd2382898dd5/openfisca_france/model/prelevements_obligatoires/impot_revenu/ir.py#L1326)：ir_brut按家庭份额及period对应bareme计算，而不是单一平税率。
- [tests/impot_revenu/pfu_bareme.yaml:1](https://github.com/openfisca/openfisca-france/blob/16b2e69633e840fdf5f39b74f96dfd2382898dd5/tests/impot_revenu/pfu_bareme.yaml#L1)：2018原生测试明确同一收入结构在PFU/barème选择下的不同结果。
