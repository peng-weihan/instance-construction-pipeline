# games: 定向研究范围

仅覆盖下列实现、原生测试/规格及根README/许可；未全仓通读、未执行候选代码、未构题、未验证运行或长程难度。
官方仓库页面在2026-10-15在线核对；WNTR官方文档确认USEPA/WNTR归属。实际保存正文为固定SHA的README/源码/测试，清单含URL及SHA256。

## g01_open_spiel · OpenSpiel / Goofspiel

- 版本：48401890ee9857e611678302371378175a8e4c6b；hold_baseline。
- `open_spiel/games/goofspiel/goofspiel.cc:418-465` (implementation)
- `open_spiel/games/goofspiel/goofspiel_test.cc:30-59` (test)

## g02_minigrid · MiniGrid / BabyAI

- 版本：b34a5755dbef71e3f1662552259a94b255c1a8bb；hold_baseline。
- `minigrid/envs/babyai/core/levelgen.py:59-90` (implementation)
- `tests/test_envs.py:54-94` (test)

## g03_magent2 · MAgent2 / Battle

- 版本：f3fca5a78504615986dfba37d85137c9e15d1db6；hold_baseline。
- `magent2/environments/battle/battle.py:129-155` (implementation)
- `magent2/environments/magent_env.py:38-85` (implementation)
- `tests/test_render.py:25-47` (test)
- `magent2/environments/battle/battle.py:181-205` (implementation)

## g04_lux · Lux AI Season 2

- 版本：5bcb3c775d536cecda32a3c041a9814279b79c5b；hold_reference。
- `luxai_s2/luxai_s2/env.py:760-808` (implementation)
- `luxai_s2/tests/collision.py:12-48` (test)
- `luxai_s2/luxai_s2/env.py:995-1015` (implementation)

## g05_hanabi · Hanabi Learning Environment

- 版本：54e79594f4b6fb40ebb3004289c6db0e34a8b5fb；hold_baseline。
- `hanabi_learning_environment/hanabi_lib/hanabi_state.cc:250-286` (implementation)
- `hanabi_learning_environment/rl_env.py:343-366` (implementation)
- `examples/rl_env_example.py:34-64` (example_spec)
- `hanabi_learning_environment/hanabi_lib/hanabi_game.cc:42-66` (implementation)

## g06_flatland · Flatland

- 版本：e355074d0f7afe0df8de92caed2274330369dbcf；scope_probe。
- `flatland/envs/rail_env.py:451-490` (implementation)
- `tests/test_flatland_envs_rail_env_policies.py:13-35` (test)

## g07_textworld · TextWorld / Cooking

- 版本：6d88a0845bc904751d3b7f128d61f21cabdf6f70；hold_baseline。
- `textworld/challenges/tw_cooking/cooking.py:799-843` (implementation)
- `textworld/challenges/tests/test_cooking.py:15-56` (test)

## g08_halite · Halite III

- 版本：e1050ee924292997b3a446b4be4c821848944fd8；hold_reference。
- `game_engine/core/HaliteImpl.cpp:450-477` (implementation)
- `game_engine/test/integration_test.py:15-60` (test)

## g09_pommerman · Pommerman

- 版本：5315f6da378f495737dfe34a4ba7f50c84423ce7；hold_reference。
- `pommerman/envs/v0.py:148-202` (implementation)
- `examples/simple_ffa_run.py:14-34` (example_spec)

## g10_screeps · Screeps Engine

- 版本：a90d26fc9eb943147799e65d0bf9d4d0d79a2722；hold_reference。
- `src/processor/intents/movement.js:110-149` (implementation)
- `spec/engine/processor/intents/movement.test.js:13-51` (test)
- `spec/helpers/mocks/intents.js:1-17` (test_fixture)

