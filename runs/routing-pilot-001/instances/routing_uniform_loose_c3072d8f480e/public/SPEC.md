# Constrained routing solver

Build a general solver for the `uniform_loose` distribution. The configuration is
`{"capacity": 12, "customers": 24, "distribution": "uniform", "max_stops": null, "vehicle_cost": 50, "window_slack": 100}`. Public examples and hidden cases are independent.

Your only submitted file is `solver.py`, a Python 3.12 standard-library program.
Each process reads ONE JSON object from stdin and writes ONE JSON object to stdout:
`{"routes": [[customer_id, ...], ...]}`. No extra keys, logging, score claims,
duplicate JSON keys, boolean IDs or non-finite numbers are accepted.
Processes start fresh for each case, with 2 seconds and 512 MiB on the Linux Judge.
Output is limited to 128 KiB. Do not use local files, subprocesses or network services.

Every customer must be visited exactly once. Each nonempty route starts at the depot
at time zero and returns before `horizon`. Manhattan distance is both travel cost
and travel time. Waiting is permitted. Service START must be in the inclusive
`[ready, due]` interval; service duration is then added. Sum of demands must not exceed
`capacity`; `max_stops` is a route stop limit, or null when absent. There is no hard
vehicle-count limit. All coordinates, demands and times are integers.

Cost = total travel distance + vehicle_cost * number of routes.
Singleton cost = sum of round trips plus one vehicle fee per customer.
Case score = 100 * max(0, 1 - cost / singleton_cost).
All cases must be feasible; any invalid case makes the submission invalid with score 0.
Otherwise the overall score is the equally weighted mean of case scores.
Singleton routes are always feasible and score 0. Lower valid costs always score higher;
no best-known-solution table or candidate-reported cost is used.

Start with `solver.py`. Run a public check:
`python3 evaluate.py --cases cases.json --solver solver.py --trusted-host`
`checker.py` documents the exact constraints. External feedback returns aggregate score,
feasible fraction and counts of failure types. Hidden routes and per-case costs stay private.
The controller selects one frozen program on feedback before a separate one-time final test.
