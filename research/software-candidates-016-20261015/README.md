# 16 个软件工程候选

入口：[REPORT.md](REPORT.md)。完整候选是素材与设计，不是已验证题目。

复现素材获取及报告渲染，逐条顺序执行：

```sh
.venv/bin/python research/software-candidates-016-20261015/harvest_sources.py
.venv/bin/python research/software-candidates-016-20261015/supplement_sources.py
.venv/bin/python research/software-candidates-016-20261015/write_cards.py
.venv/bin/python research/software-candidates-016-20261015/finalize_inventory.py
.venv/bin/python research/software-candidates-016-20261015/check_inventory.py
```

以上命令在 edgebench 根目录运行。不会启动模型或修改远端文件。
