# O09_OPENWBO 带硬约束与加权偏好的MaxSAT求解

- 类别：optimization；潜力：high；优先级：hold_baseline。素材研究，未构题/运行/验证难度。
- 主来源：sat-group/open-wbo@80f3073e41028b219b0b0ad7c61fba28351f88e6。
- 固定版本清单：[manifest](../sources/o09_openwbo/manifest.json)。
- 本项素材单元：WCNF/PB reader、完整模型代价与OLL参考；所取CNF只是小格式例子

## 拟交付与难度

输入冻结WCNF，提交满足全部硬子句的赋值并最小化未满足软子句权重，在统一时间预算上比较anytime策略。
- 交付：赋值证书、求解策略、目标值与有效性日志。
- 难度来源：硬可行性和软权重冲突共同影响搜索，降低局部软代价可能破坏硬约束。
- 难度来源：core-guided、线性搜索、编码与权重分层有实例依赖，现有选择器是强基线。

## 验证与划分

- 正常基线：Open-WBO原生策略与现代合法MaxSAT/SAT/MIP方案，不以禁solver增加难度。
- 首个探针：先用新生成/有授权结构族测默认与强现成MaxSAT，检查有效最优差距与可重复性。
- 停止条件：现成选择器已解决全部预算实例，或依赖已公开答案/权重溢出漏洞拿分，则重设。
- 独立评测：独立逐字句检查完整赋值，硬约束失败判无效；用安全整数重算软成本，小实例穷举；不信任s OPTIMUM FOUND文字。
- 生成与划分：按底层配置/图/排程编码结构族生成WCNF，排除同一CNF重排/变量置换跨split；完整实例集尚未取得。
- 谱系/重叠：与原SMT solver同属约束求解，新增MaxSAT目标及实例谱系须实质区别；公开SAT小例不是新的高难benchmark。
- 离线/计算：C++和SAT submodule依赖预置；旧WCNF parser版本/硬权重定义需固定，未编译。
- 许可观察：根为MiniSat/Open-WBO MIT式条款，外部MaxSAT语料另核；没有把竞赛数据许可视为已确认。

## 选读证据

- [MaxSAT.cc:149](https://github.com/sat-group/open-wbo/blob/80f3073e41028b219b0b0ad7c61fba28351f88e6/MaxSAT.cc#L149)：模型代价按未满足软子句权重求和。
- [README.md:25](https://github.com/sat-group/open-wbo/blob/80f3073e41028b219b0b0ad7c61fba28351f88e6/README.md#L25)：README区分SATISFIABLE与OPTIMUM FOUND并定义赋值/目标输出。
