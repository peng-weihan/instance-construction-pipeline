# O07_KAHYPAR 平衡约束下的超图k路划分

- 类别：optimization；潜力：high；优先级：hold_baseline。素材研究，未构题/运行/验证难度。
- 主来源：kahypar/kahypar@d207276070d176097273f7d4ee94043067eb97f0。
- 固定版本清单：[manifest](../sources/o07_kahypar/manifest.json)。
- 本项素材单元：cut/km1明确目标、平衡分区回归与小.hgr例子

## 拟交付与难度

在节点权重和公开不平衡阈值下输出k路分区，选择并冻结cut或km1一个目标，以相同资源预算优化。
- 交付：节点块编号证书、划分策略、平衡与目标原始数值。
- 难度来源：一个超边连接多个分区，改动单点影响多个局部增益和块容量，不能用普通图边cut替代。
- 难度来源：coarsening、初始分区、refinement和重启预算相互影响，已有多层方法是强基线。

## 验证与划分

- 正常基线：KaHyPar默认与正常配置，多重启/成熟超图划分器；不故意禁现成工具。
- 首个探针：确认cut和km1独立复算一致后，对结构不同超图测默认/最佳合法配置的余量。
- 停止条件：默认或简单多重启已经饱和，或评价混淆cut/km1/平衡，则重设。
- 独立评测：独立统计每块节点总权重和每条超边覆盖块数，重算cut或km1；小例子穷举确认，不使用候选metric。
- 生成与划分：新的hyperedge重叠、节点权重与社区/网表生成族，按底层超图谱系拆分；小.hgr仅格式验证。
- 谱系/重叠：与本批FPGA、图模块度存在表示/算法联系，属于不同约束目标但非完全独立训练族。
- 离线/计算：C++/CMake依赖和配置预置；x86/ARM线程/随机性及GPL依赖未跑。
- 许可观察：根GPL-3.0文本，依赖/外部网表各自核权。

## 选读证据

- [kahypar/partition/metrics.h:95](https://github.com/kahypar/kahypar/blob/d207276070d176097273f7d4ee94043067eb97f0/kahypar/partition/metrics.h#L95)：原生metric分别实现hyperedge cut与(k-1)加权连接度目标。
- [tests/partition/metrics_test.cc:87](https://github.com/kahypar/kahypar/blob/d207276070d176097273f7d4ee94043067eb97f0/tests/partition/metrics_test.cc#L87)：原生测试对demo图cut给出精确值，不证明优化质量已校准。
