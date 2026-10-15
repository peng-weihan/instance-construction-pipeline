# Material transformation and ownership

The fixed material is https://github.com/valkey-io/valkey at
`cf5efa70192faedacb6741ee2a8f800d0482862f`. `../material-src/valkey`
is a complete detached checkout, not the earlier selected-file evidence bundle.
`../material-src/source-manifest.json` hashes all tracked files and lists license
files, including vendored dependency notices. No source revision was substituted.
The build uses the repository's vendored C dependencies with MALLOC=libc, TLS off.
Valkey's `COPYING` is BSD-3-Clause and is preserved in both build contexts.

Read source anchors: `src/multi.c` transaction admission/reset/EXEC and watches;
`src/aof.c` append-only opening/replay/durability; `tests/unit/multi.tcl` and
`tests/unit/protocol.tcl` native regressions. Valkey already implements all of the
ordinary protocol/transaction/persistence concepts. This instance does not claim
any of them is a missing feature in Valkey. Its original artifact is an independent
service for deterministic event replay with a transparent effect journal.

All service implementation, the socket client, grader and scenarios are new
BSD-3-Clause task-author code. No upstream test bodies or original EdgeBench hidden
tests were copied. The names and bounded behavior of common commands follow the
pinned upstream; CLOCK and EKV1 are an explicit original extension. No complete
Valkey implementation or reference answer enters the work image. Legitimate reuse
is allowed; submitted dependencies must fit the documented offline Python source
contract. A Valkey wrapper that actually implements the whole contract is valid.

Construction is controlled recovery: freeze the complete reference in
`verifier/private/reference` and identical `solution/reference`, then replace the
transaction dispatcher and journal with useful simpler implementations in the
starter. `solution/reference.patch` is the clean inverse patch; `authoring` records
its hashes. The starter preserves the transport, typed store, logical clock and
real best-effort JSON-lines restart behavior. It can already run public regressions.
No dummy solve script or fixed numerical reward is used.

The independent semantic evidence consists of literal multi-client traces, a
separate wire encoder/decoder, externally constructed EKV1 frames, CRC validation,
all-or-nothing recovered transaction effects and syscall-level SIGKILL/failpoint
restarts. Tests never import candidate implementation code. Expected recovery
states do not come from a reference self-roundtrip. `../evidence/baseline.json`
records observed pinned Valkey behavior; native upstream regression output is in
`../evidence/valkey-native-final.log`. This is behavioral triangulation, not an
independent human author review: the same author designed the spec, gold and tests.

Public split: instruction, starter, five actual socket smoke regressions and one
journal payload example. Feedback split: 29 named semantic scenarios in six frozen
weighted groups, available only in the verifier context; candidate receives pass
flags and group metrics, not expected replies. Author-audit split:
`verifier/private/audit`, with additional header-cut and WATCH/PERSIST invariants;
it never changes a submission's score or chooses a submission. Audit code and
actual executed status are recorded separately. No test-seed renaming is claimed
to create an independent task or distribution.

The work Docker context is exactly `environment/`; the judge context is exactly
`verifier/`. The private source snapshot, controls and scorer are root-protected.
Compilation and execution both use UID 39009, no supplementary groups, resource
limits and process-group cleanup. Only regular Python snapshot files cross from
submission to the candidate build directory. Private test and reward path access
is checked with that actual UID. No host Docker socket or credentials are mounted.
Container network is disabled. Local host checks share the host kernel and are
not a substitute for the pending container security and ARM checks.

Leakage risks: public Valkey semantics are known and intended; score feedback can
reveal named failure dimensions. Authoring/reference/solution directories must not
be mounted into the agent environment. Separate image contexts prevent accidental
COPY of the parent job, logs or source checkout. The judge contains private answer
files, so permissions and runtime identity are essential. A privileged-container
or kernel escape is outside this draft's threat model. Runtime writes remain in
candidate data/runtime directories; the grader alone writes score/reward files.

Final local controls and their actual commands are recorded in
`../evidence/local-check-matrix-r3.json`; structured reward and native reward
file parity is checked there. These are direct local Python/shell invocations,
not a Harbor trial or container execution. Schema validation loads the supplied
Harbor schema snapshot with locally installed 0.23.0 helper modules; it explicitly
rejects unknown fields rather than relying on Pydantic extra-field ignoring.
Power-loss/device failure and malicious kernel escapes were not tested. The
reference implements fsync-before-reply; local process-death tests validate the
framing/recovery boundary, not an independent device-level durability guarantee.
