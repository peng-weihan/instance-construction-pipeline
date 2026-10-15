"""Fresh point processes with source-aligned marginals and feasibility witnesses.

No original point set, customer record, route, BKS or node-permuted instance is reused.
Distribution summaries are author-side calibration inputs, not solver-visible answers.
"""
from collections import Counter, defaultdict
import math
from pathlib import Path
import random
import statistics

from .contract import check_routes, digest, distance10, geometry_fingerprint, read_instance

FAMILIES = ["C1", "C2", "R1", "R2", "RC1", "RC2"]


def family_of(name):
    return name[:3] if name.startswith("RC") else name[:2]


def features(case):
    nodes = case["nodes"][1:]
    horizon = case["nodes"][0][5]
    pairs = [min(math.hypot(a[1] - b[1], a[2] - b[2]) for b in nodes if a[0] != b[0]) for a in nodes]
    span = math.hypot(max(a[1] for a in nodes) - min(a[1] for a in nodes),
                      max(a[2] for a in nodes) - min(a[2] for a in nodes))
    return {"customers": len(nodes), "capacity": case["capacity"], "max_vehicles": case["max_vehicles"],
            "horizon": horizon, "service_mean": statistics.mean(n[6] for n in nodes),
            "integer_coordinate_ratio": statistics.mean(float(n[1]).is_integer() and float(n[2]).is_integer() for n in nodes),
            "demand_mean": statistics.mean(n[3] for n in nodes),
            "demand_cv": statistics.pstdev(n[3] for n in nodes) / statistics.mean(n[3] for n in nodes),
            "nn_scaled": statistics.mean(pairs) / max(span, 1),
            "window_mean_ratio": statistics.mean((n[5] - n[4]) / horizon for n in nodes),
            "ready_mean_ratio": statistics.mean(n[4] / horizon for n in nodes)}


def build_profiles(source_directory):
    grouped = defaultdict(list)
    fingerprints = []
    for path in sorted(Path(source_directory).glob("*.txt")):
        case = read_instance(path)
        grouped[family_of(case["name"])].append(case)
        fingerprints.append(geometry_fingerprint(case))
    profiles = {}
    for family in FAMILIES:
        cases = grouped[family]
        nodes = [n for case in cases for n in case["nodes"][1:]]
        fs = [features(c) for c in cases]
        profiles[family] = {
            "family": family, "customers": 100, "capacity": cases[0]["capacity"],
            "max_vehicles": cases[0]["max_vehicles"], "horizon": cases[0]["nodes"][0][5],
            "service": statistics.median(n[6] for n in nodes),
            "bbox": [min(n[1] for n in nodes), max(n[1] for n in nodes), min(n[2] for n in nodes), max(n[2] for n in nodes)],
            "depot_mean": [statistics.mean(c["nodes"][0][i] for c in cases) for i in [1, 2]],
            "demand_histogram": dict(Counter(n[3] for n in nodes)),
            "narrow_window_widths": sorted(set(round(n[5] - n[4]) for n in nodes if 0 < n[5] - n[4] < cases[0]["nodes"][0][5] * 0.4)),
            "reference_feature_ranges": {key: [min(f[key] for f in fs), max(f[key] for f in fs)] for key in fs[0]},
            "source_count": len(cases),
        }
    return profiles, fingerprints


def sample(profile, seed, name):
    rng = random.Random(seed)
    n, family, horizon = profile["customers"], profile["family"], profile["horizon"]
    xmin, xmax, ymin, ymax = profile["bbox"]
    centers = [(rng.uniform(xmin + 8, xmax - 8), rng.uniform(ymin + 8, ymax - 8)) for _ in range(10)]
    demands, weights = zip(*[(int(k), v) for k, v in profile["demand_histogram"].items()])
    coordinates = set()
    nodes = [[0, *profile["depot_mean"], 0, 0, horizon, 0]]
    for i in range(1, n + 1):
        while True:
            clustered = family.startswith("C") or (family.startswith("RC") and i <= n // 2)
            if clustered:
                cx, cy = centers[(i - 1) % len(centers)]
                xy = (round(max(xmin, min(xmax, rng.gauss(cx, 5)))),
                      round(max(ymin, min(ymax, rng.gauss(cy, 5)))))
            else:
                xy = (round(rng.uniform(xmin, xmax)), round(rng.uniform(ymin, ymax)))
            if xy not in coordinates:
                coordinates.add(xy)
                break
        nodes.append([i, *xy, rng.choices(demands, weights=weights)[0], 0, horizon, profile["service"]])
    case = {"name": name, "capacity": profile["capacity"], "max_vehicles": profile["max_vehicles"], "nodes": nodes}
    remaining, routes, arrivals = set(range(1, n + 1)), [], {}
    while remaining:
        route, load, clock, previous = [], 0, 0, 0
        while remaining:
            options = []
            for i in remaining:
                leg = distance10(nodes[previous], nodes[i])
                finish = clock + leg + round(nodes[i][6] * 10)
                if load + nodes[i][3] <= case["capacity"] and finish + distance10(nodes[i], nodes[0]) <= horizon * 10:
                    options.append((leg, i))
            if not options:
                break
            options.sort()
            # Randomized construction only supplies a feasibility certificate.
            leg, chosen = options[rng.randrange(min(3, len(options)))]
            clock += leg
            arrivals[chosen] = clock / 10
            clock += round(nodes[chosen][6] * 10)
            load += nodes[chosen][3]
            previous = chosen
            route.append(chosen)
            remaining.remove(chosen)
        if not route:
            raise ValueError("infeasible singleton")
        routes.append(route)
    if len(routes) > case["max_vehicles"]:
        raise ValueError("planted fleet exceeds source fleet")
    coverage = rng.choice([0.5, 0.75, 1.0])
    for node in nodes[1:]:
        if rng.random() > coverage:
            continue
        width = rng.choice(profile["narrow_window_widths"])
        arrival = arrivals[node[0]]
        ready = max(0, math.floor(arrival - width * rng.uniform(0.25, 0.75)))
        due = min(horizon, max(math.ceil(arrival), ready + width))
        node[4], node[5] = ready, due
    # Identifier order must not reveal route membership or sampling order.
    old_ids = list(range(1, n + 1))
    rng.shuffle(old_ids)
    mapping = {old: new for new, old in enumerate(old_ids, 1)}
    case["nodes"] = [nodes[0]] + [[new, *nodes[old][1:]] for new, old in enumerate(old_ids, 1)]
    routes = [[mapping[i] for i in route] for route in routes]
    result = check_routes(case, routes)
    if not result["valid"]:
        raise ValueError(result)
    return case, routes, {"coverage_draw": coverage, "seed": seed, "profile_sha256": digest(profile)}


def distribution_gate(case, profile):
    observed = features(case)
    exact = ["customers", "capacity", "max_vehicles", "horizon", "service_mean", "integer_coordinate_ratio"]
    tolerances = {"demand_mean": 0.2, "demand_cv": 0.3, "nn_scaled": 0.4,
                  "window_mean_ratio": 0.1, "ready_mean_ratio": 0.1}
    checks = {}
    for key, value in observed.items():
        lo, hi = profile["reference_feature_ranges"][key]
        margin = 0 if key in exact else (max(abs(lo), abs(hi)) * tolerances[key])
        if key in ["window_mean_ratio", "ready_mean_ratio"]:
            margin = tolerances[key]
        checks[key] = lo - margin <= value <= hi + margin
    return {"passed": all(checks.values()), "features": observed, "checks": checks,
            "interpretation": "Marginal envelope screen; not a proof of equality of joint distributions."}
