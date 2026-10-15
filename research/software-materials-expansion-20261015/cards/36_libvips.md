# 36 libvips：图像缩略处理流水线的资源与吞吐优化

- 路线：M3；优先级：`hold_until_baseline`。素材候选，尚未构题、构建或运行。
- 固定源码：`libvips/libvips@06564b0a4c3f473d0e0cb9f9977ab647888aa43d`；源码片段、文件树和 SHA-256 见 `../sources/36_libvips/manifest.json`。
- 完整候选范围：解码/缩小加载→区域调度与缓存→缩放→alpha/颜色管理→输出；限定支持的 codec/质量合同，禁止降低语义换速度。
- 原 EdgeBench 锚点：`ffmpeg_swscale_reimplementation` 的图像兼容/数值约束与 `exchange_core_throughput` 的线程/资源取舍；原生已有高性能不等于尚有可测优化空间。

## 已有能力与可考察取舍

- thumbnail 已使用 shrink-on-load；linear 模式不能用 JPEG 的 Y 空间预缩小：`libvips/resample/thumbnail.c:496-499,545-615`。
- alpha 已预乘/反预乘，UCHAR 还有快路径：`libvips/resample/thumbnail.c:878-935`；不能把这些当成缺失功能。
- tilecache 已有 LRU/顺序淘汰、tile 大小/容量、threaded 和 persistent 开关：`libvips/conversion/tilecache.c:837-869`。
- threadpool 已按等待工人数动态扩缩：`libvips/iofuncs/threadpool.c:655-697`；水平缩小已有 Highway 动态 SIMD：`libvips/resample/shrinkh_hwy.cpp:50-148`。
- 负载 A：大幅 JPEG 缩略与长过滤链，预缩小/流水线与质量、解码成本取舍。
- 负载 B：RGBA、linear-light、不同 kernel 和奇数尺寸，像素精度与向量尾部/中间缓冲成本取舍。
- 负载 C：随机 ROI/重复 tile 与多张不同图并发，缓存命中、重计算、锁竞争、峰值 RSS 和尾延迟取舍。

## 基线、否证和测量计划

- 最强合理基线：Release、Highway/支持 ISA、既有 `thumbnail`、合法 sequential 访问；调 concurrency/tile/cache/persistent，Linux allocator；按官方建议选择操作缓存和复用策略。
- 不能以 `resize` 代替更合适的已有 `thumbnail` 故意造弱起点；linear/颜色/alpha 等语义必须一致，不能用关闭这些要求取得收益。
- Oracle：冻结上游输出与独立小图标量参考核对尺寸、像素/舍入、alpha、orientation、颜色；整数精确路径和浮点容差分开；输入 codec/元数据固定。
- 原生 `test_resample.py:82-260` 覆盖 reduce/resize/shrink/thumbnail、crop、多页及 RGBA，但平均值检查不足以充当逐像素 oracle。
- `libvips/deprecated/im_benchmark.c:51-70` 是历史 SMP 处理流水线，自己声明未专门优化；仅可借负载结构，不能当当前强基线或现成可靠计时器。
- 独立测量：预置图片/合成纹理；强制实际 sink 求值，避免只测惰性图构造；分别记录 decode/处理/encode 与端到端时间、RSS、分配、tile 重算和 p95；固定 codec 和线程并交错重复运行。
- 首探：先对 A/B/C 比较已有 thumbnail/SIMD/cache/concurrency/allocator 配置；若收益完全来自已知 API/配置或噪声，否证该优化题；奖励端点和收益门槛均待测。
- 剩余结构假设 1：配置优化后，改进多图并发时区域分配/缓存临界区与调度，可能降低锁等待及尾部延迟；先证实不是外部 codec 的瓶颈。
- 剩余结构假设 2：配置优化后，优化 alpha/颜色/缩小组合路径中重复区域搬运或数值转换；先证明精度合同允许且已有 fast path 未消除成本。

## 离线与许可

- 根 LICENSE 是 LGPL-2.1 文本；抽查源码保留 LGPL version 2 or later 头部，分发时需按具体文件/组件核查，不能概括为 MIT。
- `meson.build` 含 GLib、expat、JPEG/PNG/TIFF、Highway/ORC 等依赖；只启用任务需要的格式并预置对应库、测试绑定和数据。完整构建、依赖许可、镜像体积尚未验证。
- x86/ARM 的 Highway target、codec、allocator 和数值输出要分架构核对；不要关闭 SIMD 形成弱基线。
- 官方上下文：[开发者性能建议](https://www.libvips.org/API/current/developer-checklist.html)。页面示例速度来自上游，本卡没有复测或引用其倍率作为我们的收益。
