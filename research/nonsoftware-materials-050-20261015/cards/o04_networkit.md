# O04_NETWORKIT 多结构加权图的模块度最大化

- 类别：optimization；潜力：medium；优先级：hold_baseline。素材研究，未构题/运行/验证难度。
- 主来源：networkit/networkit@5f03e17cec0918add08f0f7c00c103ee0119da5b。
- 固定版本清单：[manifest](../sources/o04_networkit/manifest.json)。
- 本项素材单元：PLM实现、CommunityGTest的PLM/Leiden可行分区回归

## 拟交付与难度

给定冻结的加权无向图与resolution参数，输出完整节点分区并最大化明确模块度，在同计算预算上比较策略泛化。
- 交付：分区证书、可重复搜索程序与原始模块度/时间。
- 难度来源：单节点局部增益与社区总体体积相连，局部最大值和多层聚合会改变最终分区。
- 难度来源：稀疏/重尾/弱社区图的搜索与并行收益不同；不能把有语义标签的分类准确率偷偷换成模块度。

## 验证与划分

- 正常基线：现成PLM、ParallelLeiden、正常多次重启与resolution；允许其他成熟社区工具。
- 首个探针：固定目标定义与资源，对结构不同图族跑PLM/Leiden，检查默认方案是否已达到有效上限。
- 停止条件：成熟默认方法已饱和，或难点仅来自目标未定义/不恰当resolution，则重设。
- 独立评测：独立检查每节点唯一归属，直接由边和社区度和重算Q；小图枚举分区，输出社区编号置换不影响评分。
- 生成与划分：生成新的图实体和拓扑族，按degree/assortativity/overlap结构划分，不能只换节点ID；公开PGP图不放hidden。
- 谱系/重叠：与原graph_node_classification和图分割有图谱系联系，但本任务无监督优化分区而非预测标签；不能据此声称完全无重叠。
- 离线/计算：C++/OpenMP/Python和图数据预置，线程与随机性固定；没有实际速度或最优差距测量。
- 许可观察：根MIT式许可文本（License.txt），外部图数据独立核权；当前只取测试代码未取其引用PGP/CAIDA图。

## 选读证据

- [networkit/cpp/community/PLM.cpp:83](https://github.com/networkit/networkit/blob/5f03e17cec0918add08f0f7c00c103ee0119da5b/networkit/cpp/community/PLM.cpp#L83)：PLM明确按邻居社区亲和度及gamma计算移动的模块度增益。
- [networkit/cpp/community/test/CommunityGTest.cpp:282](https://github.com/networkit/networkit/blob/5f03e17cec0918add08f0f7c00c103ee0119da5b/networkit/cpp/community/test/CommunityGTest.cpp#L282)：PLM/Leiden测试检查输出是proper clustering，未证明其最优。
