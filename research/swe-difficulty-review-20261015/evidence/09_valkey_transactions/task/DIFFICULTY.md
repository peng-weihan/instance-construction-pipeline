# Difficulty hypothesis, not acceptance

Decision: build a coherent pilot; formal six-hour difficulty and ARM/container
acceptance are deferred. Full reward on the finite scenarios would establish only
reference reachability. It would not establish a useful six-hour learning curve.

The strongest cheap baseline actually run is the pinned Valkey server with RESP3,
AOF and appendfsync=always, using two real clients. It already solves runtime-error
continuation, MULTI/EXEC/WATCH and ordinary persistence. Native multi/protocol tests
also pass. The direct-server probe fails CLOCK and does not emit EKV1 frames;
`../evidence/baseline.json` records both successes and boundaries. This is not
proof that a wrapper is expensive. No complete wrapper implementation was run.
A wrapper combining logical TTL metadata and event snapshots might saturate this
contract early; do not ban that strategy or describe its cost as measured.

The public starter is stronger than an empty dictionary function: incremental
binary RESP3 framing, socket lifecycle, typed command semantics, signed integer
checks, TTL transitions and JSON-lines restarts all work. Candidate source is
executed as a real service; transactions must coordinate independent connections
and persist effects before replies. There is no throughput or delay score.

Two concrete later improvement paths, whose duration remains hypothetical:
1. Build proper per-client admission/queue/reset state and mutation versions,
   then distinguish syntax/arity admission failures from execution-time errors.
   WATCH must survive repeated registration and observe same-value writes,
   create/delete, self-writes and logical expiry. An invalidated EXEC must not
   produce effects or a journal frame. Local artifacts: transaction module plus
   multi-client replay transcripts; feedback: transactions and watch groups.
2. Replace development persistence with a transaction effect journal. Group all
   successful EXEC effects even around runtime errors, persist clock and TTL,
   continue sequence after recovery, truncate only incomplete tails, reject
   complete corruption, and place failpoints around the durability/reply boundary.
   Artifacts: journal implementation and repeatable restart cases; feedback:
   recovery/crash groups and cross-module transaction scenarios.

Early-saturation risks are material: the bounded command set is modest; expert
models know Redis semantics; the reference is compact; the protocol/store are
already supplied; naive full snapshots or an embedded upstream engine can reduce
implementation effort. More cases/LOC would not establish difficulty. There is
no six-hour run, no measured 2h plateau and no proven 2–6h improvement in this draft.

Cheapest remaining falsification: implement the legitimate strongest wrapper
baseline against the SAME frozen score and public contract, then replay its
snapshot. If ordinary library integration reaches full behavior cheaply, mark
this instance hold/reject for difficulty rather than tightening tool restrictions.
Then run a separately authorized six-hour calibration only in a future phase.
Repeated local regrades and byte-cut audits address correctness/noise, not model
difficulty. Any results listed in AUTHORING_REPORT must point to executed evidence.

Frozen local evidence (not difficulty acceptance): five fresh reference snapshots
score 1.00; unchanged starter/NOP 0.36; ignore-WATCH control 0.81; stop-on-runtime-
error EXEC control approximately 0.92. Python and shell entry points agree. See
`../evidence/local-check-matrix-r3.json`. Initial checks were unstable because
the host Python site initialization path delayed unprivileged startup; disabling
site initialization with -S removed the measured startup variability. Historical
failed checks remain in evidence and are not counted as successful final runs.
The target pinned Python 3.12.8 container still needs real runtime validation;
host checks used Python 3.12.3.
