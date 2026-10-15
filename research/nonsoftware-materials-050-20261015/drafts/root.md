# 根分析：组合优化10项与专业知识前5项

选择具体模型、证书、示例或领域案卷作为素材单元，主来源不是已出好的新题。每项核对实现和原生测试或规格。所有算法/数据调用均未执行，未做难度或奖励端点测量。

重要纠正：VTR当前relative_macro_list尚不支持，正式候选只用已实现region约束；Open-WBO需独立校赋值而不信最优状态文字；NetworKit是模块度优化不是节点分类；集合覆盖只有目录CSV与下载器，没有完整benchmark实例。专业5项以领域报告与可复算数值为主，不能改写成修工具源码。

## 实际选读范围

| 来源 | 路径 | 起止行 | 类型 |
|---|---|---|---|
| o01_ortools | sources/o01_ortools/files/examples/python/jobshop_with_maintenance_sat.py | 65–108 | implementation |
| o01_ortools | sources/o01_ortools/files/examples/python/jobshop_ft06_distance_sat.py | 15–40 | specification |
| o02_pyvrp | sources/o02_pyvrp/files/pyvrp/cpp/CostEvaluator.h | 200–258 | implementation |
| o02_pyvrp | sources/o02_pyvrp/files/tests/test_CostEvaluator.py | 135–180 | test |
| o03_scip | sources/o03_scip/files/examples/SCFLP/doc/xternal_scflp.c | 62–121 | specification |
| o03_scip | sources/o03_scip/files/examples/SCFLP/src/probdata_scflp.c | 260–305 | implementation |
| o04_networkit | sources/o04_networkit/files/networkit/cpp/community/PLM.cpp | 83–139 | implementation |
| o04_networkit | sources/o04_networkit/files/networkit/cpp/community/test/CommunityGTest.cpp | 155–200 | test |
| o04_networkit | sources/o04_networkit/files/networkit/cpp/community/test/CommunityGTest.cpp | 282–325 | test |
| o05_mapf | sources/o05_mapf/files/src/ActionModel.cpp | 490–533 | implementation |
| o05_mapf | sources/o05_mapf/files/Input_Output_Format.md | 100–125 | specification |
| o06_vtr | sources/o06_vtr/files/vpr/src/place/placer.cpp | 252–301 | implementation |
| o06_vtr | sources/o06_vtr/files/doc/src/vpr/relative_placement_constraints.rst | 1–48 | specification |
| o06_vtr | sources/o06_vtr/files/doc/src/vpr/placement_constraints.rst | 1–45 | specification |
| o07_kahypar | sources/o07_kahypar/files/kahypar/partition/metrics.h | 95–151 | implementation |
| o07_kahypar | sources/o07_kahypar/files/tests/partition/metrics_test.cc | 87–129 | test |
| o08_bqskit | sources/o08_bqskit/files/bqskit/passes/mapping/layout/sabre.py | 14–83 | implementation |
| o08_bqskit | sources/o08_bqskit/files/tests/passes/mapping/test_sabre.py | 1–55 | test |
| o08_bqskit | sources/o08_bqskit/files/bqskit/passes/mapping/sabre.py | 100–155 | implementation |
| o09_openwbo | sources/o09_openwbo/files/MaxSAT.cc | 149–205 | implementation |
| o09_openwbo | sources/o09_openwbo/files/README.md | 25–85 | specification |
| o10_setcover | sources/o10_setcover/files/include/setcoveringsolver/solution.hpp | 75–123 | implementation |
| o10_setcover | sources/o10_setcover/files/README.md | 1–48 | specification |
| o10_setcover | sources/o10_setcover/files/scripts/download_data.py | 1–37 | implementation |
| o10_setcover | sources/o10_setcover/files/include/setcoveringsolver/solution.hpp | 40–76 | specification |
| o10_setcover | sources/o10_setcover/files/include/setcoveringsolver/solution.hpp | 147–187 | implementation |
| k01_beancount | sources/k01_beancount/files/beancount/parser/booking_full.py | 150–204 | implementation |
| k01_beancount | sources/k01_beancount/files/beancount/ops/balance_test.py | 13–62 | test |
| k02_openfisca | sources/k02_openfisca/files/openfisca_france/model/prelevements_obligatoires/impot_revenu/ir.py | 580–631 | implementation |
| k02_openfisca | sources/k02_openfisca/files/tests/impot_revenu/pfu_bareme.yaml | 1–64 | test |
| k02_openfisca | sources/k02_openfisca/files/openfisca_france/model/prelevements_obligatoires/impot_revenu/ir.py | 1326–1375 | implementation |
| k03_chainladder | sources/k03_chainladder/files/chainladder/methods/mack.py | 108–171 | implementation |
| k03_chainladder | sources/k03_chainladder/files/chainladder/methods/tests/test_mack.py | 43–84 | test |
| k04_stockpyl | sources/k04_stockpyl/files/src/stockpyl/sim.py | 54–101 | implementation |
| k04_stockpyl | sources/k04_stockpyl/files/tests/test_ss.py | 1–72 | test |
| k04_stockpyl | sources/k04_stockpyl/files/src/stockpyl/sim.py | 199–251 | implementation |
| k05_cvxportfolio | sources/k05_cvxportfolio/files/cvxportfolio/simulator.py | 260–354 | implementation |
| k05_cvxportfolio | sources/k05_cvxportfolio/files/cvxportfolio/tests/test_simulator.py | 316–364 | test |

定向选读，不宣称全仓架构覆盖率；未读内容不计，原生测试没有被执行。
