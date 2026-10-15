# Optimize a C++17 CVRPTW solver

Improve the supplied general-purpose vehicle-routing solver. Submit only `src/`,
`include/`, and `Makefile`. `make` must produce `cvrptw_solver` with the interface:

    ./cvrptw_solver <input.txt> <output.txt> <time_budget_sec>

The six families C1, C2, R1, R2, RC1, RC2 contain 100 customers each. They vary
in clustered/random/mixed geometry, capacity, service duration and time windows.
All hidden inputs are freshly generated. Public examples are in instances/public/.
The feedback and final suites each contain 56 independent cases, with counts
C1=9, C2=8, R1=12, R2=11, RC1=8, RC2=8. Every customer must appear exactly once;
capacity, service-start windows, depot return horizon and MAX_VEHICLES are strict.
Distance is Euclidean rounded to 0.1 per edge (`std::round(distance * 10) / 10`).
Waiting is permitted. Routes begin/end at depot 0. Output syntax:

    Routes: 1
    Route 1: 0 1 2 0
    Cost: 123.40

The public C++ checker is tools/verify.cpp. It independently recomputes feasibility
and distance. Self-reported costs must agree within 0.05. The illustration above
is only syntax, not a valid solution for an example input.

Score prioritizes reducing vehicles, then distance. For feasible output (nv,td)
and a frozen checked reference (bnv,btd), per-case raw score is:

    s = max(0, 100 - 30*max(0,nv-bnv) - 0.5*max(0,100*(td-btd)/btd))
    if nv < bnv: s += 30*(bnv-nv)
    if nv <= bnv and td < btd: s += min(30,100*(btd-td)/btd)
    s = min(s,160)

Infeasible/timeout cases score zero. Mean raw score is reported; 100 means matching
the reference, not a proof of optimality. References can be beaten. Do not read
hidden inputs, reference solutions, author assets or grader internals. Do not
hard-code instances or install external solvers. Use the standard C++17 library.

Run `python3 feedback.py` to submit the permitted source files for aggregate
feedback. It can take about one minute. The pilot uses 1 second per case; final
validation uses 3 seconds per case. The full evaluation profile uses 60 seconds
per case and a 20-minute total deadline. Respect the budget argument in all modes.
Only feedback may guide changes; final evaluation runs once after code is frozen.

You have 10 minutes to develop. Test correctness, improve the heuristic, and leave
the best code in place. Explain your changes and actual tests in your final answer.
Run feedback.py on the exact final source before finishing; do not make untested
edits after the last feedback call. A successful trajectory needs all final cases
feasible and mean raw score at least 90. Strong improvements are useful even if
that acceptance threshold is not reached.
For trace reproducibility, make edits with shell commands (e.g. Python or heredoc)
so their exact text appears in the command log. Do not use apply_patch or subagents.
