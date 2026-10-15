# O03_SCIP 多需求场景下的容量设施选址与补救分配

- 类别：optimization；潜力：high；优先级：hold_baseline。素材研究，未构题/运行/验证难度。
- 主来源：scipopt/scip@38028b9ebdb05b2cf4928e259278934a7c7c52ba。
- 固定版本清单：[manifest](../sources/o03_scip/manifest.json)。
- 本项素材单元：SCFLP官方例子的明确模型、reader、CAP小实例与testset索引

## 拟交付与难度

提交统一开设决策及各需求场景的服务分配，使所有场景可行并降低固定开设成本与平均服务成本。
- 交付：设施开设向量、逐场景分配证书、可重放求解器。
- 难度来源：各场景共享离散开设变量，单场景最优决定可能无法承受其它需求，主问题与补救问题相互约束。
- 难度来源：完整MIP与分解方法的界、warm start和场景工作量存在时间/内存取舍，现成Benders已是强基线。

## 验证与划分

- 正常基线：SCIP现有monolithic和Benders模型及HiGHS等合法建模；不禁求解器。
- 首个探针：在同资源下比较现成两种模型的结构阶梯和可行证书，不先假设分解一定更优。
- 停止条件：现成模型普遍解决，或新场景只是无意义扩大数量，则撤销该难度设计。
- 独立评测：独立检查二元开设、容量和每场景需求，按公开概率/等权定义重算目标；小实例穷举开设集+LP。
- 生成与划分：使用新的成本/容量/需求联合生成过程，按场景相关性和设施紧张程度拆分；CAP文件仅示例，未证明可直接再分发其原数据。
- 谱系/重叠：模型来源于既有SCFLP，题目需新的场景族和可验证研究目标；不把现有Benders当待实现功能。
- 离线/计算：SCIP C/C++与LP后端全依赖、实例生成器和参考未构建；不把编译耗时计为难度。
- 许可观察：当前根Apache-2.0；CAP文件来自OR-Library谱系，数据再使用条款尚需核实。

## 选读证据

- [examples/SCFLP/doc/xternal_scflp.c:62](https://github.com/scipopt/scip/blob/38028b9ebdb05b2cf4928e259278934a7c7c52ba/examples/SCFLP/doc/xternal_scflp.c#L62)：SCFLP规格明确共享开设变量、各场景服务/容量约束和等权目标。
- [examples/SCFLP/src/probdata_scflp.c:260](https://github.com/scipopt/scip/blob/38028b9ebdb05b2cf4928e259278934a7c7c52ba/examples/SCFLP/src/probdata_scflp.c#L260)：实现把设施容量与逐场景customer变量连接。
