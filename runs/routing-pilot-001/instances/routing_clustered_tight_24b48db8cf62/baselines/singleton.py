"""Deterministic baselines using only the public input contract."""
import json
import sys

MODE = "singleton"


def solve(case, mode=MODE):
    customers = {c["id"]: c for c in case["customers"]}
    depot, fee = case["depot"], case["vehicle_cost"]

    def route_cost(route):
        if not route:
            return 0
        clock, load, length, pos = 0, 0, 0, depot
        if case["max_stops"] is not None and len(route) > case["max_stops"]:
            return None
        for node in route:
            c = customers[node]
            d = sum(abs(a - b) for a, b in zip(pos, c["xy"]))
            length += d
            clock = max(clock + d, c["ready"])
            load += c["demand"]
            if clock > c["due"] or load > case["capacity"]:
                return None
            clock += c["service"]
            pos = c["xy"]
        back = sum(abs(a - b) for a, b in zip(pos, depot))
        return length + back + fee if clock + back <= case["horizon"] else None

    routes = [[c] for c in sorted(customers)]
    if mode == "singleton":
        return {"routes": routes}
    remaining = set(customers)
    routes = []
    while remaining:
        route = []
        while remaining:
            feasible = [(route_cost(route + [c]), c) for c in sorted(remaining)]
            feasible = [(cost, c) for cost, c in feasible if cost is not None]
            if not feasible:
                break
            _, chosen = min(feasible)
            route.append(chosen)
            remaining.remove(chosen)
        if not route:
            raise ValueError("generator violated singleton feasibility")
        routes.append(route)
    if mode == "greedy":
        return {"routes": routes}
    # Best-improvement relocate search; deterministic iteration budget, no private data.
    for _ in range(80):
        best_gain, best = 0, None
        costs = [route_cost(r) for r in routes]
        for a, left in enumerate(routes):
            for index, customer in enumerate(left):
                shorter = left[:index] + left[index + 1:]
                new_left = route_cost(shorter)
                if new_left is None:
                    continue
                for b, right in enumerate(routes):
                    if a == b:
                        continue
                    for pos in range(len(right) + 1):
                        longer = right[:pos] + [customer] + right[pos:]
                        new_right = route_cost(longer)
                        if new_right is not None:
                            gain = costs[a] + costs[b] - new_left - new_right
                            if gain > best_gain:
                                best_gain, best = gain, (a, b, shorter, longer)
        if best is None:
            break
        a, b, left, right = best
        routes[a], routes[b] = left, right
        routes = [r for r in routes if r]
    return {"routes": routes}


if __name__ == "__main__":
    print(json.dumps(solve(json.load(sys.stdin))))
