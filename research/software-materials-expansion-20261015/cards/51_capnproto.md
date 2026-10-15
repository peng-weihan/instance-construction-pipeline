# 51_capnproto — 运行时 Schema 加载、演进与动态访问恢复
- 来源：[capnproto/capnproto](https://github.com/capnproto/capnproto)；SHA `b5ee48b9f3586fc83af8c429623e2c0d2435ec59`；M2 / `build_scope_probe`。
- 已有：上游已有schema加载/校验、版本兼容判定、lazy stubs/brands及动态字段访问。拟恢复既有公开API，缺失只来自尚未实施的源码掩码。
- 拟任务缺口：拟联合掩码SchemaLoader的兼容/依赖修复和关联dynamic访问路径，保留wire layout、编译器/生成绑定及API骨架；不把单个类型判断挖空充当整题。
- 产品/子系统边界：交付真实进程内 schema 生命周期：旧新schema同ID加载保持兼容规则，未加载依赖可延迟补齐，dynamic struct/list/union访问与静态绑定互通；严格遵守load/loadOnce并发与失效契约。
## 模块链与固定证据
- [`c++/src/capnp/schema-loader.h:97`](https://github.com/capnproto/capnproto/blob/b5ee48b9f3586fc83af8c429623e2c0d2435ec59/c++/src/capnp/schema-loader.h#L97)：load文档说明新旧schema替换、stub及兼容/失效限制
- [`c++/src/capnp/schema-loader.c++:622`](https://github.com/capnproto/capnproto/blob/b5ee48b9f3586fc83af8c429623e2c0d2435ec59/c++/src/capnp/schema-loader.c++#L622)：CompatibilityChecker维护新旧/等价及方向冲突
- [`c++/src/capnp/schema-loader.c++:738`](https://github.com/capnproto/capnproto/blob/b5ee48b9f3586fc83af8c429623e2c0d2435ec59/c++/src/capnp/schema-loader.c++#L738)：struct布局/field/union及group演进共享比较逻辑
- [`c++/src/capnp/dynamic.c++:173`](https://github.com/capnproto/capnproto/blob/b5ee48b9f3586fc83af8c429623e2c0d2435ec59/c++/src/capnp/dynamic.c++#L173)：DynamicStruct读取依赖字段schema和底层layout
- [`c++/src/capnp/schema-loader-test.c++:193`](https://github.com/capnproto/capnproto/blob/b5ee48b9f3586fc83af8c429623e2c0d2435ec59/c++/src/capnp/schema-loader-test.c++#L193)：原生测试覆盖upgrade/downgrade及不兼容加载
## 组合场景
1. 旧消息由新schema动态读取，新增字段取default，写回后旧静态绑定仍正确读取原字段。
2. 两个带同ID的版本逐次加载，兼容升级被采用、旧版不覆盖新版，不兼容union/layout变化给出错误。
3. 先load引用未出现类型的schema，再lazy提供依赖并访问嵌套list/struct；loadOnce与按契约并发读取不破坏引用。
## 基线与退出
- 强合法基线：使用保留低层wire与静态绑定、现成反射/CLI包装；先测试静态生成schema是否已覆盖需求。若可直接链接完整库替代所有被验接口则退出/换边界，不能虚称重新恢复。
- 首探/退出：先用静态绑定+最小loader adapter跑同ID旧新schema、lazy依赖和dynamic union；若无真正共享语义恢复工作则hold。掩码可构建性、oracle隔离均待验证。
- 早期完成后的剩余假设：基础scalar读写成功后，list/union/group演进、default与布局偏移、旧新schema混合方向仍可能未恢复。
- 早期完成后的剩余假设：顺序加载成功后，lazy依赖、brands/loadOnce线程契约与仍在使用对象的生命周期边界需按官方规格验证，不能自行放宽。
- 独立 oracle / 原生回归：固定上游API驱动程序作差分oracle；独立静态新旧绑定交叉读写真实消息并检查值，保留schema-loader/dynamic回归和边界校验；不只比较dump字符串。
- 许可观察：根 LICENSE MIT，源码文件亦带MIT头；保留作者/Cloudflare等版权及第三方依赖notice。
- 离线/架构风险：需固定C++/KJ/生成capnp绑定，CMake>=3.16；只离线内存/文件消息首版，TLS/RPC不是必需扩难；异常与线程编译选项要固定，跨CPU布局另验。
- 官方在线核对：[primary](https://github.com/capnproto/capnproto)；[primary](https://capnproto.org/language.html)
- 仅完成定向源码/测试阅读，未构造完整题包或运行；task_constructed=false；runtime_verified=false；six_hour_difficulty_verified=false。
