-- Reference planner: capture economy, selective attacks, protect the leader,
-- diversify recruitment. It performs actual decisions; it is not a score stub.
local policy={}
local function dist(x,y,a,b) return math.abs(x-a)+math.abs(y-b)*.8 end
function policy.decide(s)
    local units={};local counts={};local army=0
    for _,u in ipairs(s.units) do
        units[u.id]=u
        if u.side==s.side then counts[u.type]=(counts[u.type] or 0)+1;army=army+1 end
    end
    local best,bestscore=nil,-math.huge
    for i,a in ipairs(s.actions) do
        local value=-1000
        if a.kind=='attack' then
            local u,e=units[a.unit_id],units[a.target_id]
            value=65*a.kill_probability+2*(e.hitpoints-a.expected_enemy_hp)-2.5*(u.hitpoints-a.expected_own_hp)
            if e.canrecruit then value=value+35 end
            if u.canrecruit and a.expected_own_hp<u.max_hitpoints*.5 then value=value-120 end
        elseif a.kind=='recruit' then
            value=18-(counts[a.unit_type] or 0)*5-a.cost*.12
            if army<5 then value=value+15 end
        elseif a.kind=='move' then
            local u=units[a.unit_id];value=-5
            if not u.canrecruit then
                local before,after=1000,1000
                for _,v in ipairs(s.villages) do
                    if v.owner~=s.side then before=math.min(before,dist(u.x,u.y,v.x,v.y));after=math.min(after,dist(a.x,a.y,v.x,v.y)) end
                    if a.x==v.x and a.y==v.y then
                        if v.owner~=s.side then value=value+35 end
                        value=value+25*(1-u.hitpoints/u.max_hitpoints)
                    end
                end
                value=value+(before-after)*2
                for _,e in ipairs(s.units) do
                    if e.side~=s.side and dist(a.x,a.y,e.x,e.y)<3 and u.hitpoints<u.max_hitpoints*.4 then value=value-25 end
                end
            end
        end
        if value>bestscore then best,bestscore=i,value end
    end
    if best and bestscore>0 then return {index=best,priority=110000+math.min(100000,bestscore*500)} end
    return nil -- Defer to the frozen default CA for other actions.
end
return policy
