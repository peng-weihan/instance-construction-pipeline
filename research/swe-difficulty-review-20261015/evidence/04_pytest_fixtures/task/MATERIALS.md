# 素材与实例转换

原项目为 pytest-dev/pytest，固定提交
`c9c19f8e62c12834ad83193a1869cc82fe9c700e`，来源
https://github.com/pytest-dev/pytest/tree/c9c19f8e62c12834ad83193a1869cc82fe9c700e ，
MIT，原 LICENSE/AUTHORS 保留。完整归档从 GitHub codeload 的同提交 URL 取得；
不是仅将输入卡的四个选读文件当完整源码。作者目录 material-src/manifest.json
记录归档 SHA256、727 个原 Git blob 与本地 SHA256；.git_archival.txt 的
export-subst 展开单列。构建生成的版本文件属于构建产物，不冒充原 Git blob。

复制：完整生产源码、原生文档和测试放入公开 submission；验证器中的
native/test_native.py 和 conftest.py 是原 testing/python/fixtures.py 和
 testing/conftest.py 的逐字副本（只改变评分副本路径）。不依赖考生修改后的测试。
新写：事件合同、hook-only starter 模块/注册及 hookspec、公开 smoke、真正的
core 参考扩展、独立工作负载、评分控制器、评分元数据和隔离打包。未复制
原 EdgeBench 隐藏测试或历史任务答案。机制参照仅指真实开发工具的跨层扩展。

原生已具备缓存比较、动态 getfixturevalue、依赖 finalizer 和异常清理。
新增的是可观察的因果诊断协议，绝不将上述能力称为缺失的 pytest 功能。
作者先运行一个独立普通 hook 插件：两个参数实例正常完成，六次缓存读取没有
逐请求 hook 通知。进一步实现的公开 hook-only baseline 在最终评分器上实测
0.50；它完整保留，允许求解者复用或继续做插件，不禁止合法工具。

独立 oracle 是 fixture 体自己写的 body.jsonl、固定的工作负载语义与原生回归。
评分器不导入参考实现，也不拿参考生成日志作为 expected。通过断言检查实际
依赖边、实例数、缓存层、异常类型、清理顺序、失效原因、报告和 observer 协议；
用 trace on/off 比较体日志、插件日志及退出码，用同工作负载重跑检查可复现性。
参考达 1 只是这些冻结检查下的可达上限证据，不是对整个新协议的形式化证明。

分层：public 为完整 starter、题面、一个 smoke；feedback 为六组 24 项冻结判分
检查及 6 项原生回归门控，返回具名通过与否；author-audit 为整个上游 fixture
文件回归、权限/故障分类/补丁往返检查，均不用于事后选择考生提交。未宣称
存在由另一个作者独立设计的保留集；同一作者的语义盲点仍需后续审阅。
两份 near-miss 来自参考的局部突变，只用于评分器辨别力，不算廉价独立解。

私有参考只在 solution/；private 测试只进 verifier 构建上下文，二者均不进
work 镜像。编译和运行都降为 UID 65534，私有目录及 reward 目录由 root 保护。
本机审计同样保护 reference-src、controls、author-tools、evidence 与作者轨迹。
候选收到公开测试输入是正常黑盒执行需求；不能把私有断言代码、参考源码或
reward 写权限一同暴露。源码符号和公开上游历史可能让求解者快速理解核心；
这属于真实工具生态，不能通过隐藏合法源码来假造难度。
