# K03_CHAINLADDER 赔付三角的准备金与不确定性审阅案卷

- 类别：knowledge；潜力：medium；优先级：hold_data。素材研究，未构题/运行/验证难度。
- 主来源：casact/chainladder-python@90c7b3532499b662e57b5be2275a848ce90d5a70。
- 固定版本清单：[manifest](../sources/k03_chainladder/manifest.json)。
- 本项素材单元：Mack点估计/误差实现与论文数值回归、RAA/GENINS小三角

## 拟交付与难度

给定新的截尾赔付三角及公开精算假设，交付IBNR、预测误差、发展因子敏感性和业务准备金建议；直接使用成熟模型。
- 交付：准备金/不确定性表、时间截尾回测、假设检查与审阅备忘录。
- 难度来源：点估计和误差依赖同一发展因子/方差假设，拟合良好不等于风险区间可靠。
- 难度来源：日历效应、异常origin和tail选择会改变业务结论，需要可复算的敏感性与保留年份验证。

## 验证与划分

- 正常基线：MackChainladder、标准chain ladder/Bornhuetter-Ferguson和成熟bootstrap方法；公开RAA现成答案是必试捷径。
- 首个探针：先看标准模型对新三角是否足够，并核对误差与文献；没有新的授权/合成案例前不发布题。
- 停止条件：直接load_sample+fit即可给完整答案，或没有可信风险真值/评分合同，则重设。
- 独立评测：独立三角运算核点估计、冻结健康Mack及新生成过程校区间，检查假设/引用与建议的一致性；不能把单一隐藏未来赔付当唯一正确准备金。
- 生成与划分：新的多业务线/日历/结算机制生成器或授权实体，按保险业务与时间截尾分组；RAA/GENINS仅公开校准，不作hidden。
- 谱系/重叠：精算区别于原投资配置，但时间统计与风险机制共享；新保险实体和生成过程尚未构造。
- 离线/计算：CPU Python/NumPy/SciPy/pandas；两份小CSV已取，真实新保险案卷未取，未运行误差/回测。
- 许可观察：代码MPL-2.0；公开三角自身的来源/复用许可需单独确认，不从代码许可外推。

## 选读证据

- [chainladder/methods/mack.py:108](https://github.com/casact/chainladder-python/blob/90c7b3532499b662e57b5be2275a848ce90d5a70/chainladder/methods/mack.py#L108)：Mack fit产生IBNR、parameter/process risk及预测误差，成熟实现已存在。
- [chainladder/methods/tests/test_mack.py:43](https://github.com/casact/chainladder-python/blob/90c7b3532499b662e57b5be2275a848ce90d5a70/chainladder/methods/tests/test_mack.py#L43)：原生测试用Mack论文固定数值回归方差/误差。
