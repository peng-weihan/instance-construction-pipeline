# Harbor 0.23.0 与本批适配契约

```text
<project-name>/
  instruction.md
  task.toml
  environment/           # work 构建上下文：公开素材/开发反馈
    Dockerfile
  verifier/              # judge 构建上下文，与environment平级
    Dockerfile
    tests/               # 与根tests评分代码一致，构建时核对哈希
    private/             # 隐藏目标/参考指标，work不能访问
  tests/
    test.sh
    grader.py
  solution/
    solve.sh             # 原生Oracle注入/solution，安装到submission
  authoring/
    provenance.json
    score-spec.json
    build-manifest.json
  pipeline-profile.json  # 本项目周期适配器扩展
  AUTHORING_REPORT.json
```

这是本 skill 的布局约定，Harbor通用格式不强制叫verifier这个目录。当前Harbor配置没有通用build_context字段：用实际构建命令 `docker build -f environment/Dockerfile environment` 和 `docker build -f verifier/Dockerfile verifier`，把镜像绑定至支持的 `docker_image`，上下文路径记录在metadata/构建manifest中。native加载默认environment目录不意味着任意外置judge Dockerfile会被自动构建。

judge上下文也可用平铺评分文件，如 `verifier/checker.py` 配 `COPY checker.py /tests/checker.py`，无需为了结构检查增加一个未被Dockerfile使用的tests副本。检查必须追踪实际COPY源到容器目标，并核对镜像内最终字节；仅有同名镜像或未被使用的相同副本不能证明一致。

## 真正路径映射

- 项目 `/home/workspace/<project-name>`：Dockerfile WORKDIR 和 `[environment].workdir` 指向同处；`[verifier.environment].workdir` 也明确设置。
- 全部考生输出放在 `<workspace>/submission/`。推荐按真实文件列artifacts，如 `<workspace>/submission/solver.py`；可声明整个submission，但必须确认所有待评文件可在大小上限内快照。不能包含整个项目/private/logs/凭据。
- Oracle `solution/solve.sh` 使用自身脚本目录取参考文件，写submission，避免假定宿主路径或 `/app/solution`。
- 根tests由Harbor注入 `/tests`；周期适配器judge镜像须预带相同 `/tests/test.sh`。复制submission快照保留原绝对路径，grader直接读取该路径，不另写一套映射评分公式。
- `test.sh` 在可靠PATH下用固定解释器启动，清PYTHONPATH/PYTHONHOME/PYTHONSTARTUP/LD_PRELOAD；清理必须发生在解释器启动之前。仅Python函数里清变量无法防止解释器先被劫持。
- judge只读目标/评分程序，候选以非特权UID运行；保护 `/logs/verifier`，不把宿主Docker socket或账号挂进去，结束时杀掉进程组并限制输出/CPU/内存。

隔离核对不能只测试私有目录是否可列出：目录模式0711会隐藏列表，却允许考生打开已知名称的0644答案文件。用实际候选UID核对一个真实私有文件的读取权限，以及reward文件的写权限；只记录权限结果，不输出答案内容。修复可遍历的私有路径或文件权限，不能仅修改探针期望值让检查通过。

编译考生源码也属于执行不可信输入：编译器与其汇编器、链接器须以不能读取私有数据的身份运行，设置实际时间、资源和输出预算。只在运行生成的二进制时降权不够；本批真实复现过 root 编译 `.incbin` 私有文件成功、把私有字节嵌入产物的漏洞。给编译阶段可写的公开构建目录；评分代码、隐藏数据和reward目录仍由judge保护。用真实编译身份验证已知私有路径不能被嵌入，不输出私有内容。

## Schema核对

查实际Harbor `src/harbor/models/task/config.py`。0.23.0支持 `[verifier].environment_mode="separate"`、`[verifier.environment]`、`workdir`、`network_mode="no-network"` 和根 `artifacts`。三个作用域agent/verifier/environment显式声明策略；构建联网例外按需求写理由并固定依赖，运行任务不能要求联网。模型API传输由评测框架配置，不在题包里注入账号或放宽任务资源网络。

当前schema未定义顶层 `reward_type`；使用 `[metadata]` 或其子表记录 `reward_type="bounded_continuous"` 与评分公式/常量，并在产题报告指出本批文档与实际schema的映射。不要依赖未知字段被Pydantic忽略来宣称配置生效；如客户后来提供扩展schema，应升级并实测再应用。

原生输出 `/logs/verifier/reward.txt` 是一个0–1有限数。周期所需结构化报告示例（值必须真实计算）：

```json
{"valid":true,"score":0.0,"pass_rate":0.0,"summary":"实际诊断摘要","checks":[{"name":"constraint-name","passed":false}],"metrics":{"raw_objective":123.0}}
```

优化题的pass_rate是可行/检查通过率，不能用归一化质量分冒充；归一化score写入两种输出。有效但错误的提交可得0，内部异常返回失败而非生成上述示例来凑0。

## 本地检查命令

```bash
/ws/users/wcgu/edgebench/venv/bin/python \
  /ws/users/wcgu/skills/edgebench-task-authoring/scripts/check_package.py \
  --task /absolute/task --project-name example-project \
  --harbor-root /ws/users/wcgu/edgebench/dev/harbor \
  --output /absolute/new-check-dir/path-check.json
```

该工具核对配置、目录、声明路径与遗留/app引用；静态通过不是镜像构建/原生试跑通过。原生Oracle/NOP命令以此版本 `harbor run --help` 和真实job配置为准，不复制未知CLI参数。现有负责人可使用其native_job/assemble_basic_qc辅助工具，保留真实子trial证据，不能手填成功。

## 普通提交失败与结构化结果

缺文件、语法错误、编译失败、非法输出和考生程序超时属于提交结果，评分器正常处理后写 `valid=true`、实际0分和具体诊断；不要退出到缺reward，也不要把它们当成评分基础设施故障。依赖缺失、私有数据损坏、评分器自身异常等才是无效实验，不生成假0。成功与普通失败均将同一计算结果写入 `/logs/verifier/reward.txt` 与 `/logs/verifier/score.json`。编译同样要有时间、资源、输出限制；无论候选父进程是否正常退出，最后清理它的进程组。

Harbor 原生 verifier 从 reward.txt/reward.json 解析奖励，不读取 score.json 的 valid 标志；仅以非零退出码加 valid=false、同时写 reward=0，仍可能被原生入口读取为0分。基础设施失败须保留结构化无效诊断、非零退出且不留下数值 reward 文件（包括旧 reward.json）；score 为 null/省略，不能伪造一个已完成的0分。原生入口应得到 verifier 异常/缺奖励，周期入口应得到无效评分。实际验证两种入口的故障分类，普通错误提交的有效0分分支仍保留。

编译故障分类依据实际失败组件，不能仅凭 stderr 包含“not found”“permission denied”就认定基础设施故障：考生引用不存在的头文件、或尝试嵌入不可读私有文件，也会产生这些诊断，属于普通提交失败。验证可信编译器/启动器及题目承诺的依赖可用，再区分它们的故障与考生源码造成的错误；保留两类分支的实际证据。

## 周期适配器 profile

`pipeline-profile.json` 是本项目适配器配置，不是 Harbor 元数据。当前 runner 要求 `artifacts`、`verifier_image`、`selection`、`score_direction`；本批高分为优采用 `score_direction="maximize"`，推荐 `selection="valid_then_score"`。工作镜像使用 `agent_image`，其他资源字段以实际 `sforge-harbor-adapter/edgebench_harbor/runner.py` 为准。不要添加 runner 不支持的 `task`、`title`；任务路径放在后续 `pipeline-config.json`，标题放在题包元数据。静态检查器核对当前 profile 字段，并以真实 runner 源码测试防止契约漂移。
