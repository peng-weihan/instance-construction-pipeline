"""Authoritative integer CVRPTW checker. No submission-supplied costs are trusted."""


def distance(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def check(case, answer):
    def fail(reason):
        return {"feasible": False, "reason": reason, "cost": None, "score": 0.0}

    if type(answer) is not dict or set(answer) != {"routes"}:
        return fail("output_schema")
    routes = answer["routes"]
    if type(routes) is not list or not routes:
        return fail("empty_routes")
    customers = {c["id"]: c for c in case["customers"]}
    seen, travel = set(), 0
    for route in routes:
        if type(route) is not list or not route:
            return fail("empty_route")
        if case["max_stops"] is not None and len(route) > case["max_stops"]:
            return fail("stop_limit")
        time, load, last = 0, 0, case["depot"]
        for node in route:
            if type(node) is not int or node not in customers:
                return fail("unknown_customer")
            if node in seen:
                return fail("duplicate_customer")
            seen.add(node)
            c = customers[node]
            load += c["demand"]
            if load > case["capacity"]:
                return fail("capacity")
            leg = distance(last, c["xy"])
            travel += leg
            time = max(time + leg, c["ready"])
            if time > c["due"]:
                return fail("time_window")
            time += c["service"]
            last = c["xy"]
        leg = distance(last, case["depot"])
        travel += leg
        if time + leg > case["horizon"]:
            return fail("depot_horizon")
    if seen != set(customers):
        return fail("missing_customer")
    cost = travel + case["vehicle_cost"] * len(routes)
    singleton_cost = sum(2 * distance(case["depot"], c["xy"]) + case["vehicle_cost"]
                         for c in customers.values())
    score = 100.0 * max(0.0, 1.0 - cost / singleton_cost)
    return {"feasible": True, "reason": "ok", "cost": cost, "score": score,
            "vehicles": len(routes), "travel": travel, "singleton_cost": singleton_cost}
