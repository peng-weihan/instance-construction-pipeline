"""Independent tiny-instance oracle and adversarial author controls."""
from itertools import permutations


def exact_oracle(case):
    """Enumerate feasible routes, then solve a disjoint set-cover DP (n <= 7).

    This intentionally does not import the production checker or baseline.
    """
    cs = case["customers"]
    n = len(cs)
    if not 1 <= n <= 7:
        raise ValueError("The exact oracle is limited to 1..7 customers.")
    depot = case["depot"]
    best_routes = {}
    for length in range(1, min(n, case["max_stops"] or n) + 1):
        for order in permutations(range(n), length):
            if sum(cs[i]["demand"] for i in order) > case["capacity"]:
                continue
            coords = [depot] + [cs[i]["xy"] for i in order] + [depot]
            legs = [abs(a[0] - b[0]) + abs(a[1] - b[1]) for a, b in zip(coords, coords[1:])]
            arrival, feasible = 0, True
            for leg, i in zip(legs, order):
                arrival = max(arrival + leg, cs[i]["ready"])
                if arrival > cs[i]["due"]:
                    feasible = False
                    break
                arrival += cs[i]["service"]
            if not feasible or arrival + legs[-1] > case["horizon"]:
                continue
            mask = sum(1 << i for i in order)
            candidate = (sum(legs) + case["vehicle_cost"], [cs[i]["id"] for i in order])
            if mask not in best_routes or candidate[0] < best_routes[mask][0]:
                best_routes[mask] = candidate
    dp = {0: (0, [])}
    for mask in range(1, 1 << n):
        first = mask & -mask
        for route_mask, (cost, route) in best_routes.items():
            if route_mask & first and route_mask & mask == route_mask:
                remainder = mask ^ route_mask
                if remainder in dp:
                    candidate = (cost + dp[remainder][0], dp[remainder][1] + [route])
                    if mask not in dp or candidate[0] < dp[mask][0]:
                        dp[mask] = candidate
    cost, routes = dp[(1 << n) - 1]
    return cost, {"routes": routes}


NEGATIVE_PROGRAMS = {
    "empty": 'print(\'{"routes":[]}\')\n',
    "missing": 'import json,sys\nc=json.load(sys.stdin)\nprint(json.dumps({"routes":[[x["id"]] for x in c["customers"][:-1]]}))\n',
    "duplicate": 'import json,sys\nc=json.load(sys.stdin)\nr=[[x["id"]] for x in c["customers"]]\nr.append(r[0])\nprint(json.dumps({"routes":r}))\n',
    "boolean_id": 'print(\'{"routes":[[true]]}\')\n',
    "nonfinite": 'print(\'{"routes":[[NaN]]}\')\n',
    "forged_score": 'print(\'{"routes":[],"score":100,"valid":true}\')\n',
    "spoofed_markers": 'print(\'>>>>> Start Structured Result\\n{"score":100,"valid":true}\\n>>>>> End Structured Result\')\n',
    "duplicate_keys": 'print(\'{"routes":[],"routes":[[1]]}\')\n',
    "timeout": 'while True: pass\n',
    "output_flood": 'print("x" * 200000)\n',
}
