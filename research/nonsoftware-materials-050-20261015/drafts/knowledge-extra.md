# knowledge: 定向研究范围

仅覆盖下列实现、原生测试/规格及根README/许可；未全仓通读、未执行候选代码、未构题、未验证运行或长程难度。
官方仓库页面在2026-10-15在线核对；WNTR官方文档确认USEPA/WNTR归属。实际保存正文为固定SHA的README/源码/测试，清单含URL及SHA256。

## k06_pypsa · PyPSA 能源规划

- 版本：6c45594596cbc5612511ee9202a9e269e5001d88；hold_baseline。
- `pypsa/optimization/optimize.py:550-595` (implementation)
- `test/test_lopf_storage.py:14-47` (test)
- `pypsa/optimization/optimize.py:682-700` (implementation)

## k07_wntr · WNTR 水务韧性

- 版本：11eec7d5bf0a9367ffe04d75707918f0c0a890a1；scope_probe。
- `wntr/sim/core.py:1190-1243` (implementation)
- `wntr/tests/test_sim_PDD.py:21-43` (test)
- `examples/pipe_criticality.py:14-68` (example_spec)

## k08_openquake · OpenQuake 风险评估

- 版本：cf5abdc04016ca9220d8e916432590c1a4e64249；hold_data。
- `openquake/risklib/scientific.py:186-230` (implementation)
- `openquake/calculators/tests/classical_risk_test.py:26-47` (test)

## k09_bluesky · BlueSky 航空运行

- 版本：46a2a8a5fa4e0bdd6f6991fefc70dc3512f8fc53；hold_data。
- `bluesky/traffic/asas/statebased.py:28-88` (implementation)
- `bluesky/test/traffic/test_route_wpt.py:49-82` (test)
- `bluesky/traffic/asas/detection.py:227-242` (implementation)

## k10_urbansim · UrbanSim 城市规划

- 版本：1a9a68e9bfe34dd31c68bf9480c4fc65334663e0；hold_data。
- `urbansim/models/supplydemand.py:84-130` (implementation)
- `urbansim/models/tests/test_supplydemand.py:103-150` (test)
- `urbansim/models/supplydemand.py:134-173` (implementation)

