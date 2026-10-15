-- Trusted engine adapter. The submitted policy receives plain copies of observations
-- and legal actions, never Wesnoth userdata, engine globals, filesystem or RNG access.
local AH = wesnoth.require "ai/lua/ai_helper.lua"
local ca, chosen, planner = {}, nil, nil
local function clone(x)
    if type(x) ~= 'table' then return x end
    local out = {}; for k,v in pairs(x) do out[k]=clone(v) end; return out
end
local function load_planner()
    local env = {assert=assert, error=error, ipairs=ipairs, pairs=pairs, next=next,
        tonumber=tonumber, tostring=tostring, type=type, select=select, pcall=pcall,
        math={}, string={}, table={}}
    for _,k in ipairs({'abs','ceil','floor','sqrt','exp','log','min','max','sin','cos','huge','pi'}) do env.math[k]=math[k] end
    for _,k in ipairs({'byte','char','find','format','gmatch','gsub','len','lower','match','sub','upper'}) do env.string[k]=string[k] end
    for _,k in ipairs({'concat','insert','remove','sort','unpack'}) do env.table[k]=table[k] end
    local text=filesystem.read_file('~add-ons/EdgeCandidate/policy.lua')
    local f,err=load(text,'candidate_policy','t',env); if not f then error(err) end
    local p=f(); if type(p)~='table' or type(p.decide)~='function' then error('return table with decide(state)') end
    return p
end
local function observation()
    local side=wesnoth.current.side
    local state={side=side, turn=wesnoth.current.turn, gold=wesnoth.sides[side].gold, units={}, villages={}, actions={}}
    local units=wesnoth.units.find_on_map({side=side})
    for _,u in ipairs(wesnoth.units.find_on_map({})) do
        state.units[#state.units+1]={id=u.id,side=u.side,x=u.x,y=u.y,type=u.type,
            hitpoints=u.hitpoints,max_hitpoints=u.max_hitpoints,moves=u.moves,
            attacks_left=u.attacks_left,canrecruit=u.canrecruit,cost=u.cost,level=u.level}
    end
    for x,y in wesnoth.current.map:iter() do
        local terrain=wesnoth.terrain_types[wesnoth.current.map[{x,y}]]
        if terrain.village then state.villages[#state.villages+1]={x=x,y=y,owner=wesnoth.map.get_owner(x,y) or 0} end
    end
    for _,a in ipairs(AH.get_attacks(units,{simulate_combat=true,include_occupied=false})) do
        local u=wesnoth.units.get(a.src.x,a.src.y);local enemy=wesnoth.units.get(a.target.x,a.target.y)
        state.actions[#state.actions+1]={kind='attack',unit_id=u.id,x=a.dst.x,y=a.dst.y,
            target_id=enemy.id,tx=a.target.x,ty=a.target.y,
            expected_own_hp=a.att_stats and a.att_stats.average_hp or u.hitpoints,
            expected_enemy_hp=a.def_stats and a.def_stats.average_hp or enemy.hitpoints,
            kill_probability=a.def_stats and a.def_stats.hp_chance[0] or 0}
    end
    for _,u in ipairs(units) do
        if u.moves>0 then
            for _,loc in ipairs(wesnoth.paths.find_reach(u)) do
                if (loc[1]~=u.x or loc[2]~=u.y) and not wesnoth.units.get(loc[1],loc[2]) then
                    local legal=ai.check_move(u,loc[1],loc[2])
                    if legal.ok then state.actions[#state.actions+1]={kind='move',unit_id=u.id,x=loc[1],y=loc[2],moves_left=loc[3]} end
                end
            end
        end
    end
    for _,name in ipairs(wesnoth.sides[side].recruit) do
        for x,y in wesnoth.current.map:iter() do
            local terrain=wesnoth.terrain_types[wesnoth.current.map[{x,y}]]
            if terrain.castle then
                local legal=ai.check_recruit(name,x,y)
                if legal.ok then state.actions[#state.actions+1]={kind='recruit',unit_type=name,x=x,y=y,cost=wesnoth.unit_types[name].cost} end
            end
        end
    end
    return state
end
function ca:evaluation(cfg,data)
    if not planner then planner=load_planner() end
    local state=observation();chosen=nil
    local answer=planner.decide(clone(state))
    if answer==nil then return 0 end
    if type(answer)~='table' or type(answer.index)~='number' or answer.index%1~=0 or not state.actions[answer.index] then error('invalid action index') end
    local priority=answer.priority or 110000
    if type(priority)~='number' or priority~=priority or priority<1 or priority>250000 then error('invalid priority') end
    chosen=state.actions[answer.index]
    return priority
end
function ca:execution(cfg,data)
    if not chosen then return end
    local a=chosen;chosen=nil
    if a.kind=='recruit' then AH.checked_recruit(ai,a.unit_type,a.x,a.y)
    else
        local u=wesnoth.units.find_on_map({id=a.unit_id})[1]
        if not u then return end
        if a.kind=='attack' then AH.robust_move_and_attack(ai,u,{a.x,a.y},{a.tx,a.ty})
        else AH.checked_move_full(ai,u,a.x,a.y) end
    end
end
return ca
