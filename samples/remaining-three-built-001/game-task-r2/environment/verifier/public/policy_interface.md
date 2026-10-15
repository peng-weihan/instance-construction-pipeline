# 合法动作策略接口

policy.lua 返回 {decide=function(state) ... end}。actions、units、villages、terrain 都是从 1 开始的 Lua 数组；actions 每次重新枚举，index 不能跨调用缓存。

decide 返回 nil 时放弃本次候选动作，默认 AI 可接管；返回 {index=i,priority=p} 时与其他候选动作按优先级竞争，并不保证本次一定执行。策略不应把一次 evaluation 调用当作已经执行了一步。p 默认为 110000，须在 [1,250000] 内。

- move：unit_id、x、y、moves_left、chance_to_be_hit。后者是百分数，越小越安全；由 100-defense_on(terrain) 计算。moves_left 是 find_reach 路径查询的剩余移动力，实际执行使用 checked_move_full，会结束该单位的移动，不承诺保留此余量。
- attack：unit_id、目标移动位置 x/y、target_id、tx/ty、expected_own_hp、expected_enemy_hp、kill_probability。HP 是引擎单次战斗模拟的平均值；kill_probability 在 [0,1]。执行经 robust_move_and_attack，合法性仍由引擎确认。
- recruit：unit_type、x/y、cost。引擎仅枚举当前阵营可招募且位置合法的动作。

units 包含双方当前地图单位的普通字段；villages.owner=0 表示无人占领。time_of_day 包含 id、lawful_bonus。state 是数据副本，修改它不会更改游戏状态。完整字段及允许的 Lua 基础函数见 adapter.lua。模块内状态可跨回合保留，每局重新初始化。无法 require 其他模块、读取文件、调用引擎或控制 RNG。
