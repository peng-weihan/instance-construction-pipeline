"""Pinned PyVRP reference; every returned answer is checked independently."""
import time
from .contract import check_routes, distance10


def solve_reference(case, iterations=1500, seed=0):
    from pyvrp import Model
    from pyvrp.stop import MaxIterations
    start = time.monotonic()
    model = Model()
    nodes = case["nodes"]
    locations = [model.add_location(row[1], row[2]) for row in nodes]
    depot = model.add_depot(locations[0], tw_early=0, tw_late=round(nodes[0][5] * 10))
    max_arc = max(distance10(a, b) for a in nodes for b in nodes)
    # Greater than any possible total distance: lexicographic vehicle-count priority.
    vehicle_cost = (2 * len(nodes) + 1) * max_arc + 1
    model.add_vehicle_type(num_available=case["max_vehicles"], capacity=case["capacity"],
                           start_depot=depot, end_depot=depot, fixed_cost=vehicle_cost,
                           tw_late=round(nodes[0][5] * 10))
    for location, row in zip(locations[1:], nodes[1:]):
        model.add_client(location, delivery=row[3], service_duration=round(row[6] * 10),
                         tw_early=round(row[4] * 10), tw_late=round(row[5] * 10))
    for i, a in enumerate(locations):
        for j, b in enumerate(locations):
            d = distance10(nodes[i], nodes[j])
            model.add_edge(a, b, distance=d, duration=d)
    result = model.solve(MaxIterations(iterations), seed=seed, display=False, collect_stats=False)
    routes = [[activity.idx + 1 for activity in route if activity.is_client()]
              for route in result.best.routes()]
    verified = check_routes(case, routes)
    if result.is_feasible() != verified["valid"]:
        raise ValueError("Reference and independent verifier disagree")
    return {**verified, "routes": routes, "solver": "pyvrp", "solver_version": "0.14.0",
            "seed": seed, "iterations": iterations, "elapsed_seconds": time.monotonic() - start}
