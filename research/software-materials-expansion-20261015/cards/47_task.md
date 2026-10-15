# 47_task — 声明式任务的本地内容寻址工件缓存
- 来源：[go-task/task](https://github.com/go-task/task)；SHA `ad2782e1709f0bcf8fbbe0d8e00c2d239141e099`；M1 / `build_scope_probe`。
- 已有：已有 sources checksum/timestamp、generates 存在检查、status 命令、并发/依赖与错误时指纹处理；现有 checksum 不等于已交付工件归档/恢复系统。
- 拟任务缺口：拟增加显式选择的输出工件缓存及键/清单、完整性校验、原子发布/恢复和并发使用；只保证声明输入/工具链身份，不推断任意 shell 的全部副作用。
- 产品/子系统边界：面向可重复本地构建，删除 outputs 后由缓存恢复产物而不运行命令；变量/声明环境/依赖身份变更应 miss；取消或失败不发布可命中条目，保留非缓存任务行为。
## 模块链与固定证据
- [`internal/fingerprint/sources_checksum.go:31`](https://github.com/go-task/task/blob/ad2782e1709f0bcf8fbbe0d8e00c2d239141e099/internal/fingerprint/sources_checksum.go#L31)：已有 source checksum 与 generates 存在性判定
- [`status.go:11`](https://github.com/go-task/task/blob/ad2782e1709f0bcf8fbbe0d8e00c2d239141e099/status.go#L11)：现有 Status 编译任务并询问 fingerprinter
- [`task.go:127`](https://github.com/go-task/task/blob/ad2782e1709f0bcf8fbbe0d8e00c2d239141e099/task.go#L127)：实际任务执行入口负责依赖、命令及释放
- [`task_test.go:502`](https://github.com/go-task/task/blob/ad2782e1709f0bcf8fbbe0d8e00c2d239141e099/task_test.go#L502)：原生测试覆盖重复运行 up-to-date 与 checksum 文件不重写
## 组合场景
1. 构建代码生成与打包依赖链后删 outputs，重跑从缓存恢复，记录证明命令未执行且字节正确。
2. 同源但 MODE/声明工具链不同生成两类产物，键互不污染，改依赖后下游按契约失效。
3. 两进程争用同键且一方中断，后续运行看不到半成品；损坏缓存可诊断并安全重建。
## 基线与退出
- 强合法基线：现有 status/sources/generates + tar/sha256 缓存包装器，或直接调用成熟本地构建缓存；外部包装合法，不以修改核心文件数计难度。
- 首探/退出：先以短包装实现最小恢复并引入变量变化、并发同键与失败后残片；若现成缓存工具无需额外语义可完整完成则降级。
- 早期完成后的剩余假设：单任务缓存恢复成功后，依赖身份、变量/环境键、输出路径集合和被删除/多余产物处理仍需设计。
- 早期完成后的剩余假设：单进程成功后，同键并发构建、取消/失败原子性、工件损坏后的 miss/诊断可能未覆盖。
- 独立 oracle / 原生回归：独立命令执行计数、产物字节/权限清单与全量无缓存构建比较；保留 task_test.go 的 status/checksum/依赖/信号回归，不只相信 hit 日志。
- 许可观察：根 LICENSE 为 MIT；缓存打包/压缩依赖另审。
- 离线/架构风险：固定 go.mod 要求 Go1.26.4，需预装模块缓存；路径/权限/符号链接在 Linux 与 Windows 不同，初版明确输出类型与平台边界。
- 官方在线核对：[primary](https://github.com/go-task/task)；[primary](https://taskfile.dev/docs/guide/up-to-date)
- 仅完成定向源码/测试阅读，未构造完整题包或运行；task_constructed=false；runtime_verified=false；six_hour_difficulty_verified=false。
