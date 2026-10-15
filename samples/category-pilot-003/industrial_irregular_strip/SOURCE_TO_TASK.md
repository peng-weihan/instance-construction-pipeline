# 素材 → 题目

来源：MIT 的 PackingSolver 求解器以及仓库内 OpenCutList 工业零件轮廓。原 JSON 均已存档，逐例原文件与变换后 SHA 见 private/case_manifest.json。数据的独立授权仍需核对，代码 MIT 不自动替代零件数据权利说明。

只转换容器目标：bin-packing-with-leftovers 改为原引擎支持的 open-dimension-x，固定原高度、一个足够长的矩形条带。保持真实非凸多边形、孔洞、旋转限制、件数。共 9 例按来源设计族分为 3/3/3；不使用 deer_2、sofa_structure_r180 等明显同源变体跨集。

任务产物是“优化通用求解器”，不是为九份输入逐一提交坐标。借用 ProgramBench 的固定源码与 CLI 契约、DeepSWE 的真实项目工作单元；没有执行它们的构建或 QC。参考实现为完整下载的原始求解器，其性能不是已测基线。尚未运行 CMake、geometry verifier 或排样算法；外部 CMake 依赖需后续补齐以实现离线运行。
