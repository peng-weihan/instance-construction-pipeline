# 29_sphinx — 基于内容指纹的可解释文档增量构建模式
- 来源：[sphinx-doc/sphinx](https://github.com/sphinx-doc/sphinx)；固定版本 `b04a2101295ac3fb725b16111eda0284b6da4cca`。
- 路线：M1_existing_project_roadmap；优先级：`hold`。
- 许可观察：根 LICENSE.rst 与 pyproject.toml 显示代码默认 BSD-2-Clause，文件有 otherwise indicated 条款；主题、文档资产与依赖需再清点。
- 证据层级：已固定文件树和摘录哈希，已读核心实现与原生测试；未 clone/build/运行模型。
- 状态：task_constructed=false；runtime_verified=false；difficulty_verified=false。

## 已有能力与拟新增范围
- 已有：已有增量读写、依赖记录、mtime 失效、缺失依赖重读、配置失效、并行环境合并和扩展事件。并非从零实现增量编译。
- 拟新增：拟增加可选内容指纹缓存和稳定依赖/失效原因清单，覆盖时间戳保留的输入修改及源目录迁移；尚未验证插件能否已低成本满足全部交付，故 hold。
- 产品交付：交付一套可在文档 CI 使用的构建模式：保留增量收益，对 source/include/autodoc 显式依赖输出可解释的重读/重写原因，串并行与移动工作目录后的语义输出一致。单纯输出依赖 JSON 不足以形成长程题。

## 实际模块链与证据
- [`sphinx/environment/__init__.py:521`](https://github.com/sphinx-doc/sphinx/blob/b04a2101295ac3fb725b16111eda0284b6da4cca/sphinx/environment/__init__.py#L521)：已有 added/changed/removed 判定
- [`sphinx/environment/__init__.py:849`](https://github.com/sphinx-doc/sphinx/blob/b04a2101295ac3fb725b16111eda0284b6da4cca/sphinx/environment/__init__.py#L849)：已有 _has_doc_changed 以 source/dependency mtime 与缺失状态判定
- [`sphinx/environment/collectors/dependencies.py:24`](https://github.com/sphinx-doc/sphinx/blob/b04a2101295ac3fb725b16111eda0284b6da4cca/sphinx/environment/collectors/dependencies.py#L24)：依赖需随文档 purge，并合并并行 worker 状态
- [`sphinx/builders/__init__.py:389`](https://github.com/sphinx-doc/sphinx/blob/b04a2101295ac3fb725b16111eda0284b6da4cca/sphinx/builders/__init__.py#L389)：read→dependent update→环境持久化→write 是真实构建链
- [`sphinx/builders/__init__.py:705`](https://github.com/sphinx-doc/sphinx/blob/b04a2101295ac3fb725b16111eda0284b6da4cca/sphinx/builders/__init__.py#L705)：重读与重写不同，ToC 依赖还会扩大输出集合
- [`tests/test_builders/test_incremental_reading.py:20`](https://github.com/sphinx-doc/sphinx/blob/b04a2101295ac3fb725b16111eda0284b6da4cca/tests/test_builders/test_incremental_reading.py#L20)：原生测试已有源文件增删改与缺失资源重读
- [`tests/test_environment/test_environment_record_dependencies.py:14`](https://github.com/sphinx-doc/sphinx/blob/b04a2101295ac3fb725b16111eda0284b6da4cca/tests/test_environment/test_environment_record_dependencies.py#L14)：原生测试验证 autodoc Python 模块依赖
- [`doc/extdev/event_callbacks.rst:32`](https://github.com/sphinx-doc/sphinx/blob/b04a2101295ac3fb725b16111eda0284b6da4cca/doc/extdev/event_callbacks.rst#L32)：env-get-outdated/purge/merge 等事件已提供扩展入口

## 三个端到端场景
1. CI 恢复保留旧 mtime 的共享 include，多个页面正确更新而无关文档不重读，原因清单关联同一输入。
2. autodoc 模块移除一个依赖后再删除旧文件；下一次构建不保留幽灵依赖，生成结果与 fresh build 一致。
3. 同项目连续以 -j1/-jN 构建并迁移工作目录，逻辑输出与相对路径清单一致；配置变更触发相应失效。

## 难度否证与剩余工作
- 最强正常基线：官方 env-get-outdated + note_dependency + purge/merge 事件组成扩展，内容 hash 用标准库；与强制 -E/-a 全量构建语义 oracle 对比。全量构建若不满足事先约定的无关文档不重读要求，才构成有效区别。
- 首个否证探针：先用标准扩展实现保留 mtime 的 include 修改、串并行持久化、清单输出；若不改核心即完整满足，且无第二层产品交付，则停止升格 long-horizon。尚未执行。
- 早期实现后仍可能剩余（假设）：hash 单个 include 成功后，删除与重新出现、共享依赖、autodoc 的依赖清理/合并及缓存升级仍需一致。
- 早期实现后仍可能剩余（假设）：串行构建正确后，源目录迁移、并行进程合并、配置/扩展版本变更及读写集合的稳定原因归属仍可能需要设计；都需先证明不能被简单插件覆盖。

## 评测与环境
- 独立评测及原生回归：独立对生成 HTML 的链接/内容与全量 fresh build 比较；用 source-read 和写入事件观测实际集合而非信任自报清单；保留 test_incremental_reading、record_dependencies、HTML/ToC 回归。
- 离线与跨架构：Python>=3.12、docutils>=0.21,<0.23；首轮只用 HTML/dummy 且固定主题扩展，禁用外链/网络资产；LaTeX/Graphviz 不应无依据加入；并行在目标 Linux CPU 镜像另验。
