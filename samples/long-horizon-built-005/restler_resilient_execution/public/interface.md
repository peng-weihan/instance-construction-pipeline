Policy is configured under a new `execution_policy` key in RESTler settings.
All durations are seconds; max_attempts includes the first attempt. A response at the deadline is too late.
Attempt k (k=1 for the first retry) has base delay min(cap, base*2**(k-1)); use the larger of this and a valid Retry-After.
For HTTP-date parsing, capture wall-clock and monotonic time once per response; convert to nonnegative delay. Malformed Retry-After uses backoff.
With nonzero jitter_fraction j, multiply the chosen delay by Uniform(1-j,1+j) using an injected RNG; record the chosen delay. Tests use fixed RNG streams.
Never sleep past deadline, never issue a new transport request at/after deadline. Cancellation stops new work and starts cleanup; cleanup_deadline_seconds is a separate budget measured from cleanup start. At that deadline stop issuing deletions and record unreleased resource IDs as cleanup_incomplete, without extending the work deadline.
Policy precedence: exact normalized path+method > exact path defaults > global. Unknown keys and negative durations are configuration errors.
Resource graph is a DAG; cycles are rejected before execution. A parent can be deleted only after all children and references are gone.
Canonical event keys: event_index, request_id, resource_id, event, attempt, elapsed_ms, decision, reason. No raw body/auth/key values.
Implement `python -m engine.tools.replay_execution INPUT.jsonl --policy POLICY.json --output TRACE.jsonl` from the restler directory.
Integration remains through existing rendering, transport, async and GC call sites; a standalone mock implementation earns no integration checks.
