"""Original EdgeBench CVRPTW contract, with an independent strict verifier."""
import hashlib
import json
import math
from pathlib import Path
import re


def stable(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def digest(value):
    return hashlib.sha256(stable(value)).hexdigest()


def read_instance(path):
    headers, tables, section = {}, {}, None
    for line in Path(path).read_text().splitlines():
        line = line.strip()
        if not line or line == "EOF":
            continue
        if line.endswith("_SECTION"):
            section = line
            tables[section] = {}
        elif ":" in line:
            key, value = line.split(":", 1)
            headers[key.strip()] = value.strip()
        elif section and section != "DEPOT_SECTION":
            row = line.split()
            tables[section][int(row[0])] = [float(x) for x in row[1:]]
    n = int(headers["DIMENSION"])
    nodes = []
    for i in range(n):
        xy = tables["NODE_COORD_SECTION"][i]
        q = tables["DEMAND_SECTION"][i][0]
        e, l = tables["TIME_WINDOW_SECTION"][i]
        s = tables["SERVICE_TIME_SECTION"][i][0]
        nodes.append([i, *xy, int(q), e, l, s])
    return {"name": headers["NAME"], "capacity": int(headers["CAPACITY"]),
            "max_vehicles": int(headers["MAX_VEHICLES"]), "nodes": nodes}


def write_instance(case, path):
    rows = [f'NAME : {case["name"]}', f'DIMENSION : {len(case["nodes"])}',
            f'CAPACITY : {case["capacity"]}', f'MAX_VEHICLES : {case["max_vehicles"]}',
            'EDGE_WEIGHT_TYPE : EUC_2D_X10']
    for section, columns in [("NODE_COORD_SECTION", [1, 2]), ("DEMAND_SECTION", [3]),
                             ("TIME_WINDOW_SECTION", [4, 5]), ("SERVICE_TIME_SECTION", [6])]:
        rows.append(section)
        rows.extend(" ".join([str(node[0])] + [f"{node[c]:g}" for c in columns]) for node in case["nodes"])
    rows += ["DEPOT_SECTION", "0", "-1", "EOF"]
    Path(path).write_text("\n".join(rows) + "\n")


def distance10(a, b):
    # C++ std::round on non-negative values, NOT Python banker's rounding or DIMACS truncation.
    return int(math.floor(math.hypot(a[1] - b[1], a[2] - b[2]) * 10 + 0.5))


def check_routes(case, routes):
    def fail(reason):
        return {"valid": False, "reason": reason, "nv": None, "td": None}
    if not isinstance(routes, list) or not routes or len(routes) > case["max_vehicles"]:
        return fail("route_count")
    nodes = case["nodes"]
    seen, cost = set(), 0
    for route in routes:
        if not route:
            return fail("empty_route")
        now, load, previous = 0, 0, 0
        for node_id in route:
            if type(node_id) is not int or not 0 < node_id < len(nodes):
                return fail("customer_id")
            if node_id in seen:
                return fail("duplicate_customer")
            seen.add(node_id)
            node = nodes[node_id]
            leg = distance10(nodes[previous], node)
            now = max(now + leg, round(node[4] * 10))
            if now > round(node[5] * 10):
                return fail("time_window")
            now += round(node[6] * 10)
            load += node[3]
            if load > case["capacity"]:
                return fail("capacity")
            cost += leg
            previous = node_id
        back = distance10(nodes[previous], nodes[0])
        if now + back > round(nodes[0][5] * 10):
            return fail("depot_horizon")
        cost += back
    if seen != set(range(1, len(nodes))):
        return fail("missing_customer")
    return {"valid": True, "reason": "ok", "nv": len(routes), "td": cost / 10}


def read_solution(path):
    lines = [line.rstrip() for line in Path(path).read_text().splitlines() if line.strip()]
    if len(lines) < 3 or not re.fullmatch(r"Routes: \d+", lines[0]):
        raise ValueError("invalid solution header")
    nv = int(lines[0].split(":")[1])
    if len(lines) != nv + 2 or not re.fullmatch(r"Cost: \d+\.\d{2}", lines[-1]):
        raise ValueError("invalid solution length or cost")
    routes = []
    for index, line in enumerate(lines[1:-1], 1):
        match = re.fullmatch(rf"Route {index}: 0((?: \d+)+) 0", line)
        if not match:
            raise ValueError("invalid route")
        routes.append([int(x) for x in match[1].split()])
    return routes, float(lines[-1].split(":")[1])


def verify_solution(case, path):
    try:
        routes, declared = read_solution(path)
        result = check_routes(case, routes)
        if result["valid"] and abs(result["td"] - declared) > 0.05:
            return {"valid": False, "reason": "declared_cost", "nv": None, "td": None}
        return result
    except (ValueError, OSError):
        return {"valid": False, "reason": "format", "nv": None, "td": None}


def write_solution(case, routes, path):
    result = check_routes(case, routes)
    if not result["valid"]:
        raise ValueError(result)
    lines = [f"Routes: {len(routes)}"]
    lines += [f"Route {i}: 0 " + " ".join(map(str, route)) + " 0" for i, route in enumerate(routes, 1)]
    lines.append(f'Cost: {result["td"]:.2f}')
    Path(path).write_text("\n".join(lines) + "\n")


def official_score(result, reference):
    if not result["valid"]:
        return 0.0
    nv, td, bnv, btd = result["nv"], result["td"], reference["nv"], reference["td"]
    if not reference["valid"] or btd <= 0:
        raise ValueError("A checked reference is mandatory; no self-normalization fallback.")
    s = max(0.0, 100 - 30 * max(0, nv - bnv) - 0.5 * max(0, (td - btd) / btd * 100))
    if nv < bnv:
        s += 30 * (bnv - nv)
    if nv <= bnv and td < btd:
        s += min(30, (btd - td) / btd * 100)
    return min(s, 160.0)


def geometry_fingerprint(case):
    """ID/order-independent; catches all original node-permutation copies."""
    def row(n):
        return [float(n[1]), float(n[2]), int(n[3]), float(n[4]), float(n[5]), float(n[6])]
    return digest({"capacity": case["capacity"], "fleet": case["max_vehicles"],
                   "depot": row(case["nodes"][0]), "customers": sorted(row(n) for n in case["nodes"][1:])})


def pointset_fingerprint(case):
    return digest(sorted([float(n[1]), float(n[2])] for n in case['nodes']))
