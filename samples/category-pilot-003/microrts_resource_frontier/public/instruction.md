# 资源边境策略机器人

基于固定 microRTS 引擎实现 submission.FrontierAI。公开地图包含成对瓶颈通道、有限的基地资源与需要争夺的扩张资源。目标是在多种对手和尺度下维持经济、安排兵种、选择进攻时机并打赢完整对局。

继承 AI/AbstractionLayerAI 或保留 WorkerRush 作为基础均可；构造器接受 UnitTypeTable，clone/reset/getAction 行为遵守原 API。提交仅含一个 FrontierAI.java，可使用内部类。评分器在冻结引擎中编译并创建全新实例，不接受修改引擎、地图、对手、随机种子或 match runner；禁止反射、进程/网络/文件访问和改写 GameState。通过合法 PlayerAction 行动。

每局最多 6000 cycles，每次 getAction 最多 100ms；面对 WorkerRush、LightRush、RangedRush、HeavyRush 四种固定对手，每张地图用四个种子和两个座位配对。每组 3 张图，共 96 局；胜 1、平 0.5、负 0，全部比赛等权。违规或超时局按负计并返回具名诊断，基础接口无法运行则本次提交无效。公开/反馈/最终地图在家庭资源与扩张压力上不同，最终表现要求完整策略泛化。

提交源文件快照后，由独立 verifier 重新模拟整个对局；得分不依赖 agent 容器中的活进程或正在进行的游戏。参考模型的运行时间是 3 小时，局内模拟只是单次评分工作负载，二者不要混淆。
