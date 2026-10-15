# 在固定预算下突破异形排样基线

修改真实 PackingSolver irregular 求解器，目标为 fixed-height open-dimension-x。每例必须放入全部零件、遵守旋转/镜像限制并保持几何可行。保持 CLI 与 certificate 格式；提交 repo/src/irregular/ 与 repo/include/packingsolver/irregular/。

每个生产订单固定单核亲和性下 20 秒（线程共享同一核），与冻结的原始求解器使用同一资源预算。无效或遗漏的例子记零且不从分母删除。有效性占 20%，剩余 80% 衡量相对原始参考布局缩短的长度；原样提交基线无法获得改进分。评分器独立验证轮廓，不能相信候选自己报告的面积、相交或长度。

公开订单来自椅具、凳具和梯具；反馈及审计使用独立设计族。订单大小变化是同一道任务的工作负载，不算新题。可从 profile、初始布局、排序、邻域、重启与几何查询加速逐步推进。不得缓存隐藏实例的答案表。预算 6 小时。

提交目录根含 src/irregular 与 include/packingsolver/irregular。其余构建文件由评分器恢复，新增 CMake 规则不接受。基线布局已由冻结源码每例运行 20 秒生成并通过独立检查，长度、输入和证书 SHA256 已固定；镜像重建只校验这些固定资产，每次提交不会重新估计基线。seed 参数在当前上游 CLI 标为 not used，不能作为确定性保证；最终固定的是保存的参考布局。独立检查器支持本批全部 polygon/holes 输入，几何容差见 scoring_metadata.json。

求解器调用统一附带 --item-item-minimum-spacing 0.1，为接触布局留出数值安全裕量；参考布局和提交使用相同参数。独立几何检查的重叠容差及评分公式保持不变。
