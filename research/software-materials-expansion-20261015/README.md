# 软件工程出题素材池：累计 50 项

从 [50 项总目录](CATALOG_50.md) 开始阅读；[调研报告](REPORT.md) 解释筛选结论。本批在此前 15 项上新增 35 个主仓库，五条构造路线各 10 项。

每项固定源码 commit，保存关键实现、测试/规格和许可材料，并提供拟题范围、正常基线及首个否证探针。23 项先验证范围，27 项暂缓并优先排查现有能力、基线或工具链。当前为素材研究，尚未构造新题或验证六小时难度。

- [50 项总目录](CATALOG_50.md)
- [结构化候选 JSON](candidates.json) / [CSV](candidates.csv)
- [50 份素材卡](cards/)
- [来源与文件摘要](source-manifests.json)
- [旧来源去重](previous-source-check.json)
- [完整性检查](inventory-check.json)
- [首批 15 项报告快照](REPORT_15.md) / [首批登记](candidates-15.json)

复核：先运行本目录的 collect_and_validate.py，再运行 render_catalog.py，最后再运行完整性检查以核对生成目录的链接。上述脚本不运行候选源码、基准或模型。
