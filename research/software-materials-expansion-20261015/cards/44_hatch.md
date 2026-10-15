# 44_hatch — 可移动的离线多环境交付包与安装审计
- 来源：[pypa/hatch](https://github.com/pypa/hatch)；SHA `ac9c0c9544795b380c2a5f63f80c1f46db3c5d4c`；M1 / `hold`。
- 已有：已有 PEP751 pylock、pip/uv locker 插件、矩阵共享锁输入合并、过期校验、extras/groups、带哈希的 uv 解算和 locked 安装。
- 拟任务缺口：拟增加环境矩阵的离线交付包清单、依赖工件归集/校验和目标机安装审计；不能把锁文件支持冒称缺失。插件/uv 缓存可能已足够，故 hold。
- 产品/子系统边界：面向离线实验室发布一份多环境 bundle：显式列出支持的平台/Python，收齐锁定 wheels 与本地项目工件，迁移目录后安装并运行项目脚本；不要求一个 venv 二进制跨架构搬运。
## 模块链与固定证据
- [`src/hatch/env/lock.py:1`](https://github.com/pypa/hatch/blob/ac9c0c9544795b380c2a5f63f80c1f46db3c5d4c/src/hatch/env/lock.py#L1)：现有锁文件为 PEP751 并委托 pip/uv
- [`src/hatch/env/lock.py:217`](https://github.com/pypa/hatch/blob/ac9c0c9544795b380c2a5f63f80c1f46db3c5d4c/src/hatch/env/lock.py#L217)：已有共享锁文件的矩阵输入合并入口
- [`src/hatch/env/lockers/uv.py:66`](https://github.com/pypa/hatch/blob/ac9c0c9544795b380c2a5f63f80c1f46db3c5d4c/src/hatch/env/lockers/uv.py#L66)：现有 uv compile 使用哈希、extras/groups 与源参数
- [`tests/cli/env/test_lock.py:376`](https://github.com/pypa/hatch/blob/ac9c0c9544795b380c2a5f63f80c1f46db3c5d4c/tests/cli/env/test_lock.py#L376)：真实测试已有锁文件内容同步判定
## 组合场景
1. 两矩阵环境共享部分依赖且 extras 不同，bundle 去重并在离线目录恢复正确版本与脚本。
2. bundle 缺少某平台 wheel 或哈希不符，安装前明确指出包/目标环境且不回退公网。
3. 迁移根目录后安装；对已存在但依赖漂移的环境生成差异，再恢复锁定清单。
## 基线与退出
- 强合法基线：原生 hatch env lock + uv/pip 离线缓存或 wheelhouse + 普通归档脚本；允许复用全部成熟解析/安装器。
- 首探/退出：先导出两环境锁，收集 wheelhouse，在断网且不同绝对路径机器安装；若现有命令+短包装即可完整满足审计与错误恢复则不构成长题。
- 早期完成后的剩余假设：简单纯 Python bundle 成功后，extras/groups 合并、环境 marker 与平台 wheel 缺失诊断仍需证明。
- 早期完成后的剩余假设：一次离线安装成功后，工件损坏、局部安装失败、项目路径移动与配置漂移的审计/恢复可能未覆盖。
- 独立 oracle / 原生回归：用独立 importlib.metadata/脚本输出与 wheel 哈希验证真实安装，拦截网络；保留 test_lock、环境创建/脚本原生回归，不能以 mock resolver 证明离线运行。
- 许可观察：LICENSE.txt 为 MIT；打包的第三方 wheels 与后端另列许可，未做全依赖审计。
- 离线/架构风险：Python>=3.10；uv/pip 与不同 OS/CPU wheels 必须预置；sdist 编译和本地路径包是关键风险，不承诺跨架构搬运环境。
- 官方在线核对：[primary](https://github.com/pypa/hatch)；[primary](https://hatch.pypa.io/latest/how-to/environment/lockfiles/)；[primary](https://hatch.pypa.io/latest/plugins/locker/)
- 仅完成定向源码/测试阅读，未构造完整题包或运行；task_constructed=false；runtime_verified=false；six_hour_difficulty_verified=false。
