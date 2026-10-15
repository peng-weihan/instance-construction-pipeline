"""Seeded task distributions; feasibility is planted before identifiers are shuffled."""
import hashlib
import hmac
import json
import random

PROFILES = {
    "uniform_loose": {"customers": 24, "distribution": "uniform", "window_slack": 100,
                      "capacity": 12, "max_stops": None, "vehicle_cost": 50},
    "clustered_tight": {"customers": 32, "distribution": "clustered", "window_slack": 15,
                        "capacity": 12, "max_stops": None, "vehicle_cost": 80},
    "clustered_stop_limit": {"customers": 40, "distribution": "clustered", "window_slack": 50,
                             "capacity": 12, "max_stops": 4, "vehicle_cost": 100},
}


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def derive_seed(secret, *namespace):
    return int.from_bytes(hmac.new(secret.encode(), canonical(namespace), hashlib.sha256).digest(), "big")


def generate_case(config, seed):
    rng = random.Random(seed)
    n = config["customers"]
    ids = list(range(1, n + 1))
    rng.shuffle(ids)
    customers, witness = [], []
    for start in range(0, n, 4):
        count = min(4, n - start)
        center = (rng.randint(20, 80), rng.randint(20, 80))
        points = []
        for j in range(count):
            if config["distribution"] == "clustered":
                xy = [max(1, min(100, center[k] + rng.randint(-12, 12))) for k in range(2)]
            else:
                xy = [rng.randint(1, 100), rng.randint(1, 100)]
            points.append((ids[start + j], xy))
        # A simple geometric certificate, not an optimal route or the evaluation baseline.
        points.sort(key=lambda pair: (pair[1][0], pair[1][1]))
        clock, previous, route = 0, [0, 0], []
        for node, xy in points:
            clock += abs(xy[0] - previous[0]) + abs(xy[1] - previous[1])
            service = rng.randint(1, 4)
            customers.append({"id": node, "xy": xy, "demand": rng.randint(1, 3),
                              "ready": max(0, clock - config["window_slack"]),
                              "due": clock + config["window_slack"], "service": service})
            clock += service
            previous = xy
            route.append(node)
        witness.append(route)
    case = {"depot": [0, 0], "capacity": config["capacity"], "horizon": 2000,
            "max_stops": config["max_stops"], "vehicle_cost": config["vehicle_cost"],
            "customers": sorted(customers, key=lambda c: c["id"])}
    return case, {"routes": witness}


def generate_instance(secret, profile, replica, counts):
    config = PROFILES[profile]
    cases, certificates = {}, {}
    for split, count in counts.items():
        cases[split], certificates[split] = [], []
        for index in range(count):
            seed = derive_seed(secret, "routing-v1", profile, replica, split, index)
            case, witness = generate_case(config, seed)
            cases[split].append(case)
            certificates[split].append(witness)
    return config.copy(), cases, certificates
