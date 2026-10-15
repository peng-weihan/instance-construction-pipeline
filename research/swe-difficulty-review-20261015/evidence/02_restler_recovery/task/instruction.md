Implement durable sequential BFS campaigns in the real RESTler engine.

The project is the complete `microsoft/restler-fuzzer` snapshot at
`6d984deedbc54aad957fa3da0c7e9e5df23a2aee`. The editable Python engine is in
`/home/workspace/restler-recovery/submission/restler`. Keep the real
`restler.py` → BFS driver → dependency parsers → HTTP transport execution chain.
The existing saver is deliberately disabled upstream; existing socket reconnects
are part of the starting behavior. A small public compatibility fix lets native
runs without a garbage collector finish logging their summary.

Add `--recovery_dir DIR` and `--resume` to `restler/restler.py`. A fresh durable
campaign uses an empty DIR. Resume must require an existing campaign; an existing
campaign without `--resume` must fail. Without either option preserve ordinary
native behavior. Settings files may supply `recovery_dir` and `resume` through
RESTler's existing settings merge.

Durable execution must preserve the same ordered upstream operations, statuses,
BFS generations, response-derived resource IDs and final live resources as an
uninterrupted native run. A resumed run may reconstruct internal state by replay;
it must not resend requests whose responses are already durable. Parsers and BFS
extension must still execute normally. Finishing an already completed campaign
must succeed without contacting the service. Persist generated UUID4 and UUID
suffix values so native grammar rendering remains consistent across restart.
Keep native coverage and monitoring consistent with the completed campaign.

The supported profile is BFS, one worker, disabled checkers (`--disable_checkers
'*'`), no GC, refreshable authentication, create-once resources, scenario replay,
or custom value generators. Unsupported parallelism, non-BFS modes and GC must
fail before service requests or campaign mutation. Fail closed if resumed grammar,
dictionary, settings contents or effective execution options change. File path
identity alone is insufficient. Hold an exclusive process lock on DIR throughout
execution. Concurrent ownership must fail before sending requests.

Use a durable write-ahead request journal and generation/completion records.
Expose it as `DIR/journal.jsonl`: append records with a terminating newline. A
partial final record without a newline may be discarded; corruption in a complete
record must fail closed before network activity. Bind the journal to its campaign
and configuration and detect missing/reordered/corrupt history. Keep a diagnostic
`checkpoint.json` generation receipt, atomically replaced; a damaged receipt must
not destroy recoverable journal history. You may retain previous receipts. Do not
load executable pickle data as your durable format. Crash points include an
intent persisted before its response is durably received and a generation receipt
interrupted after an older complete journal prefix.

Requests use this explicit service protocol: append an `Idempotency-Key` header
whose value identifies the campaign and logical request occurrence. Retry an
unresolved occurrence with the identical key, including retries inside
`HttpSock.sendRecv`. Distinct occurrences, including repeated identical POST
bodies, need distinct keys. The service gateway durably caches the original HTTP
status/body for each key and rejects the same key with different request contents.
Faults occur after the real backend response AND the gateway ledger commit, before
client receipt. Client SIGKILL, dropped responses and service process restart
preserve the backend SQLite database and gateway ledger. Backend failure between
a business commit and the ledger commit is outside this protocol's guarantee.
Do not claim exactly-once behavior for an arbitrary API without this capability.
An unresolved transport failure must not silently advance exploration.

The service is the repository's unmodified FastAPI demo blog app, backed by its
real SQLite models and routes. It assigns IDs, exposes intentional upstream bugs,
and may reuse a deleted highest ID. This task does not fix those bugs. The public
grammar exercises create → response parser → dependent GET/DELETE, multiple
candidate values and repeated request sequences. Hidden feedback varies fault
boundaries and uses the real native UUID primitive. Logs and timestamps need not
be byte-identical. Persisted resource checksums are outside the comparison.

Submit production Python source in `submission/restler`: `restler.py`,
`restler_settings.py`, and Python modules beneath `engine/` or `utils/` may be
changed or added. Other source, public grammars, tests, service code and grading
configuration are fixed by the verifier. All graded artifacts must be beneath
`submission`. Dependencies are preinstalled from the supplied offline wheel lock;
stdlib implementations and installed libraries are allowed. Do not replace the
production project with a separate client or an answer-producing test runner.

For native regressions run, from the project root:

```sh
PYTHONPATH=submission/restler python -m pytest -q -p no:cacheprovider \
  submission/restler/unit_tests/test_candidate_values.py \
  submission/restler/unit_tests/test_restler_settings.py
python public/dev_probe.py --source submission/restler --work dev-run
```

The development probe starts the actual blog server and protocol gateway on local
loopback, kills RESTler after a committed service operation, resumes it and writes
an audit. Use a new work directory for each run. Its result is diagnostic, not the
private grade. Source and native tests for the .NET compiler remain available, but
the task uses a supplied Python grammar and does not require compiler changes.

The frozen score is the weighted sum of twelve semantic checks: legacy native
behavior 0.10, fresh durable campaign 0.10, completed resume without wire traffic
0.10, lost create response with process kill 0.15, dependent delete/resource
recovery 0.10, dropped response in the same process 0.10, UUID replay 0.10, torn
journal tail/receipt fallback 0.05, corrupt-history rejection 0.05, configuration
binding 0.05, exclusive ownership 0.05, unsupported-option rejection 0.05. Each
check has a fixed denominator. No performance score is enabled. Invalid candidate
code is an ordinary scored failure. Grader/service infrastructure errors invalidate
the experiment and yield no numeric reward.
