Build EdgeKV, a transactional, recoverable RESP3 service for deterministic replay.

The project is `/home/workspace/edgekv`. Submit Python source files under
`submission/`; the grader snapshots those files and launches
`python3 -B submission/server.py --socket PATH --data DIRECTORY [--failpoint POINT]`.
The process must bind a Unix SOCK_STREAM socket only after successful recovery.
PATH may be relative to the process working directory. DIRECTORY already exists
and is exclusively owned by this service. The grading runtime is Python 3.12.8
with its standard library; no install step or network access is available. All
source files, including the entry point and any imported modules, must be in
submission. Source limit: 128 regular .py files, 2 MiB total; symlinks are rejected.
The grader runs compilation and execution under a separate unprivileged UID.

The starter implements a real incremental socket transport, typed command store,
logical time, and development JSON-lines persistence. Complete the transaction
and journal subsystems, adapting other modules as needed. There is no migration
requirement for the starter's development journal. `python3 public/smoke.py`
runs the preserved public regressions. You can start your server with
`python3 submission/server.py --socket ./dev.sock --data ./dev-data`.

Wire contract

Requests are RESP arrays of 1..1024 non-null bulk strings. Command names are ASCII
case insensitive; keys and values are arbitrary bytes, including empty strings.
Each bulk is at most 1,048,576 bytes. Accept fragmented and pipelined requests.
Input buffers need only support 2,097,152 bytes, output buffers 8,388,608 bytes.
No inline requests, nested request arrays, or RESP push messages are required.
Array/bulk length headers contain only decimal digits and CRLF. Empty arrays,
negative/excessive lengths, non-bulk arguments, bad terminators and malformed
headers produce one `-ERR Protocol error...\r\n`, then close that connection.
Discard following bytes on that connection. A truncated request on disconnect
has no effect. Other connections continue to operate. Error text after the first
word is diagnostic; error class and RESP reply types are authoritative.

Use RESP3 from connection establishment: simple strings for OK/PONG/QUEUED/TYPE,
bulk strings for data, integer replies, arrays for ranges/EXEC, `_\r\n` for null,
and simple errors. `HELLO 3` returns a map with bulk keys: server=`edgekv`,
version=`1`, proto=3, id=a positive integer unique among connections in this
process, mode=`standalone`, role=`master`, modules=empty array. `HELLO` with any
other single argument returns NOPROTO. No RESP2 negotiation is required.

Bounded commands (argument counts exclude the command word)

- PING [message]: PONG or echo the bulk message. HELLO version: as above.
- SET key value [PX milliseconds]: overwrite any type, return OK; clear prior TTL
  unless PX is present. Only this option is supported. TTL must be positive.
- GET key: bulk string or null. INCR key: missing means 0; increment signed 64-bit
  integer and return integer. Existing values must be canonical decimal bytes:
  `0` or optional minus followed by a nonzero digit and digits. Reject +1, -0,
  leading zeros, whitespace, overflow. Successful INCR preserves TTL.
- DEL key [key...]: count keys actually removed (duplicates count once).
  EXISTS key [key...]: count present arguments (duplicates count repeatedly).
- LPUSH key value [value...]: prepend in argument order, so `LPUSH l a b`
  produces `[b,a]`; return length. Preserve TTL. LRANGE key start stop: inclusive
  range, negative indexes count from end, clamp to bounds, missing means empty
  array. Indices use the same canonical signed 64-bit syntax.
- TYPE key: simple string `none`, `string`, or `list`.
- PEXPIRE key milliseconds: set deadline to clock+milliseconds, return 1; missing
  key returns 0. Nonpositive duration deletes a present key. PERSIST key clears
  TTL and returns 1 only when an existing TTL was removed. PTTL key: remaining
  milliseconds, -1 for no TTL, -2 for missing.
- CLOCK absolute_ms: global logical time starts at 0. Advance monotonically;
  equal is allowed, negative/backwards is ERR. Expire every key with deadline
  <= new time before returning OK. All expiry is driven by CLOCK, never wall
  time, sleeps, socket scheduling, or process downtime. Time is persisted.
- MULTI, EXEC, DISCARD, WATCH key [key...], UNWATCH: rules below.
- QUIT: OK and close, abandoning the connection's pending transaction/watches.

GET/INCR on lists and LPUSH/LRANGE on strings return WRONGTYPE. Unknown commands,
wrong arity, unsupported SET options, malformed integers and arithmetic/deadline
overflow return ERR. PEXPIRE durations may be negative; all stored deadlines and
logical time must be in [0, 2^63-1]. No error may modify data, TTL or watch versions.
SET accepts exactly 2..4 arguments at admission; optional syntax is checked at
execution. All other counts follow the command synopsis exactly.

Deterministic events and transactions

The judge serializes events by waiting for a reply before submitting a dependent
event. Different clients may each have pending MULTI queues. Pipelined commands
on one socket execute in wire order. Each complete command, or entire EXEC, is
one indivisible event relative to commands from other clients. No ordering across
independent ready sockets is required. No concurrency throughput score exists.

MULTI returns OK and begins a per-connection queue. Valid ordinary commands return
QUEUED and have no effects until EXEC; integer/SET-option/WRONGTYPE errors are
execution-time errors. Unknown commands and wrong arity are admission errors;
they return ERR immediately and mark the transaction dirty. MULTI, WATCH, CLOCK,
HELLO and QUIT inside MULTI are also immediate ERR and dirty the transaction.
EXEC and DISCARD are control commands, never queued. UNWATCH is queued like an
ordinary command. Commands admitted after an error still return QUEUED.

EXEC without MULTI is ERR. A dirty EXEC returns EXECABORT, runs nothing and clears
transaction/watches. Otherwise an invalidated watch makes EXEC return RESP3 null
and run nothing. Otherwise execute all queued commands in order, return the array
of their replies, including any errors. An execution-time error does not roll back
or stop subsequent commands. Empty successful EXEC returns an empty array.
DISCARD without MULTI is ERR; otherwise return OK and clear queue/errors/watches.
Every completed EXEC clears them too, including watches before executing its queue.

WATCH records versions of keys, including missing keys. Repeated WATCH accumulates
keys and preserves the earliest version of each. Any successful mutation by any
client (including this one), even SET of the same bytes, invalidates a watch.
Create-then-delete also invalidates. Expiration on CLOCK, effective PEXPIRE/PERSIST,
INCR and LPUSH are mutations. Deleting absent keys, ineffective PERSIST, failed
commands, reads and unrelated keys do not invalidate. UNWATCH outside MULTI clears
watches immediately; a queued UNWATCH cannot rescue an already invalidated EXEC.
Disconnect discards only that client's state; committed data survives.

Durable effect journal

`DIRECTORY/journal.ekv` is the sole persistent state. Do not depend on other files
for recovery. It is an append-only sequence of frames. Each header is 12 bytes:
ASCII `EKV1`, uint32 big-endian payload length (1..16,777,216), uint32 big-endian
CRC32 of the following payload. Payload is UTF-8 JSON:
`{"seq":1,"now":0,"changes":[["aw==",["s","dg==",null]]]}`.
This example stores byte key `k`, string `v`, no TTL. JSON whitespace/order is free.
Exactly these top-level keys are required. seq starts at 1 and increases by one
per frame. now is the logical clock after this event. changes lists unique keys,
encoded standard padded base64. Entries are null for deletion, or
`["s", base64_value, absolute_deadline_or_null]`, or
`["l", [base64_element,...], absolute_deadline_or_null]`.
Write keys in byte-lexicographic order. A touched key appears once with its final
value, even if changed repeatedly in one EXEC. Successful SET of identical bytes
is still touched. All read-only/no-effect events produce no frame. Clock advances
produce a frame even with no touched keys. Each nonempty effectful EXEC produces
exactly one frame; failed or watch-aborted EXEC produces none. Runtime errors do
not suppress the other commands' effects in that frame.

Append the whole event's frame, flush/fsync the file, then publish its replies to
any client. Fsync the containing data directory when creating the journal. A disk
write/fsync failure must terminate the process before exposing replies or serving
another command; partial in-memory effects must not escape. The supported fault
model is abrupt process death and prefix-truncated writes on a POSIX local disk;
no claims about device firmware or media loss are required.

On startup replay complete frames in order. An incomplete final header (1..11
bytes), or a valid full header followed by too few payload bytes, is a torn tail:
truncate it to the last complete frame and fsync before accepting clients. A
complete frame with bad magic, out-of-range length, checksum, JSON/schema, sequence
or non-monotonic clock is corruption: terminate nonzero before binding the socket,
without modifying the file. For valid input replay all changes of a frame
atomically. Connection IDs, queues, watches and versions are process-local and
must not be recovered. Repeated recovery plus new writes must continue sequence
numbers without gaps. External readers may independently construct valid frames;
reading only your own serialization is insufficient.

`--failpoint` defaults to `none`. The other values affect the first event that
would append a frame after startup (recovery itself does not trigger them):
`before-write` exits with status 86 before any new frame bytes;
`mid-header` writes the first 6 header bytes and fsyncs, then exits 86;
`mid-body` writes the full header and floor(payload_length/2) payload bytes and
fsyncs, then exits 86; `after-sync` writes and fsyncs the entire frame, then exits
86 before any event reply. Queue admission and read-only events must not trigger
these. Tests restart without the failpoint. Before-write and torn frames lose the
entire interrupted event; after-sync recovers the entire event even though the
client saw no reply. Retrying an unacknowledged event can repeat its effects;
exactly-once retry semantics are not required.

Scoring and feedback

The frozen score is a weighted mean of independent scenario pass fractions:
protocol 0.15, typed commands/logical clock 0.15, transactions 0.20, WATCH 0.20,
recovery 0.15, crash/publication 0.15. Their fixed scenario counts are 5,4,5,5,5,5.
All scenarios remain in the denominator. Missing files, invalid source, crashes,
bad replies and candidate timeouts are ordinary scored failures. Infrastructure
failures produce an invalid result with no numerical reward. Limits are 512 MiB,
12 CPU seconds per service process, 15 seconds startup/expected death, 2 seconds
per socket read, 15 seconds compilation, 64 MiB files and 96 open descriptors.
These are safeguards, not performance objectives. The native reward equals the
structured score in [0,1]; feedback includes named check/group pass results.
Tests include command→transaction→journal→restart transitions and independent
journal inputs. Hidden scenario values are not a substitute for this contract.
