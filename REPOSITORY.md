# Git 收录范围

远端：[peng-weihan/instance-construction-pipeline](https://github.com/peng-weihan/instance-construction-pipeline)。默认工作分支为 `main`。

## 单仓库与普通目录

本工作区统一由根目录 Git 仓库管理。`upstream/`、`materials/repos/`、`data/EdgeBench/` 等来源目录以普通文件快照收录，不使用 submodule；克隆本仓库无需执行 `git submodule update`。

原工作区中各来源目录的 `.git` 元数据保留在本地，不进入根仓库的提交。来源版本、文件摘要和许可证继续由已有 manifest 与各项目的许可文件记录。本仓库不为第三方内容重新指定许可证。

## 收录内容

- 各条 pipeline 的实现、原始规约、prompt、配置示例和测试。
- 项目说明、研究报告、论文、来源索引、素材卡与来源证据。
- 各版本候选、题面、starter、参考实现、评分器和构建文件。
- 运行状态、控制实验、评分报告、学习曲线及已导出的训练轨迹。
- 在 Git 单文件大小限制内的任务数据；部分相同文件在不同题包中重复保留，由 Git 对象去重。

具体忽略规则见 [.gitignore](.gitignore)。来源目录自带的 `.gitignore` 也参与首次收录筛选；`upstream/swe-factory/runs/` 中的历史验证证据单独保留。

`data/EdgeBench/assets/` 中已经下载的图片按普通 Git 对象收录，该目录的属性文件覆盖来源快照的 LFS 规则，因此本次收录内容无需 Git LFS 下载。

根目录和必要的测试夹具目录补充 `.gitattributes`，保留冻结文件的原始字节，尤其是专门测试 CRLF 的输入；原始代码、测试和已有来源属性文件保持原样。

## 留在本地的文件

| 范围 | 内容 | 恢复依据 |
|---|---|---|
| `.venv*`、`venv`、`infra-venv` 与 Python 缓存 | 本机解释器环境和安装依赖 | 各模块依赖清单、Dockerfile 与使用文档 |
| `tmp/`、`node_modules/`、`target/`、工具缓存 | 下载缓存、依赖与编译产物 | 对应项目的构建配置 |
| `samples/software-multiline-001/05_toml/tools/` | 下载及解压的本机 Rust 工具链 | 对应题包的构造记录和工具版本 |
| `samples/software-multiline-001/03_wasm/authoring/tools/` | 本机 Python 虚拟环境 | 对应作者记录与依赖 |
| `materials/datasets/` | 原始单细胞 H5AD 数据 | [版本、大小与 SHA256](research/remaining-three-2026-10-15/single-cell-source-manifest.json)、[数据说明](research/remaining-three-2026-10-15/single-cell-data-README.txt)、[来源准备脚本](agent_eval/remaining-three-001/prepare_singlecell_source.py) |
| `materials/downloads/` | 原始下载压缩包 | 对应来源登记和任务 provenance；已整理的题包数据另行收录 |
| `runs/`、`remote_smoke/` 下的传输归档及远端传输 Base64 | 从已有源码和题包生成的重复传输文件 | 对应批次的打包/传输脚本与摘要 |
| 本机认证目录、`.env`、本地认证 JSON 与私有配置 | 凭据和运行环境配置 | 在使用环境独立配置；示例配置可保留 |

这些文件在原工作区中保持原样。Git 克隆包含已收录的内容；重建被排除的数据或工具链时，按原来源版本和摘要恢复。

## 后续更新

常规源码和文档修改按根仓库提交。新增来自另一个 Git 仓库的材料时，按实际文件清单导入，并检查暂存区没有模式为 `160000` 的 gitlink，避免将目录误提交为 submodule。

研究和运行记录可能由其它进程继续更新。每次提交代表当次冻结的文件快照，运行状态以记录中的观测时间为准。
