# Offline WebAssembly i32 runtime

Build a command-line runtime for the profile in `profile.md`. The input is real WebAssembly binary bytecode, not WAT or an opcode JSON format. Preserve instance memory across a request's ordered calls; reset the entire instance for every next JSON line.

The scored artifact is `/home/workspace/wasm-profile/submission/`. Implement `submission/runner.py`; it is started with Python 3.12 and may launch additional files or executables saved under submission. Normal development tools and language choices are allowed. The work image has Python and a C/C++ toolchain; it has no Wasm engine installed. Runtime network access is disabled. The private reference and judge fixtures are not part of the work environment.

Run `python3 submission/runner.py` and send one request per line:

```json
{"module":"0061736d01000000","calls":[],"memory":[]}
```

`module` contains lowercase hexadecimal binary bytes. Every call is `{"export":"function_name","args":[signed_i32,...]}`. Every optional memory observation is `{"offset":0,"length":4}`. Return one compact or whitespace-formatted JSON value per line, with no other stdout:

```json
{"results":[],"memory":[]}
```

Each successful i32 result must be a signed integer in [-2147483648,2147483647]; a void function returns JSON null. A trapped call appends `{"trap":true}` and subsequent calls continue on the same instance. Traps retain prior memory writes. Memory observations are hexadecimal strings after all calls. Invalid binary framing returns `{"error":"invalid"}`. Initialization failure returns `{"error":"trap"}`. Stderr is for diagnostics and the process should exit zero for handled requests.

The profile covers arithmetic and comparisons, structured branching including br_table, loops and locals, recursive direct calls and return, data initialization, unaligned loads and stores, growth and bounds traps. It does not require the full WebAssembly language or general static type validation; exact limits are in the profile. Public examples and their expected outputs are in `dev_cases.json`. The starter only rejects modules and is intentionally incomplete.

Scoring is the arithmetic mean of the pass fractions of eight fixed ability groups: integer operations, binary framing, structured control, loops, calls, linear memory, traps, and composed programs. Each group has weight 1/8 regardless of how many examples it contains. Wrong, missing and timed-out cases remain in the denominator. Tests observe behavior, with a fresh candidate process per request and 3 seconds of wall time, 2 CPU seconds, 512 MiB address space on Linux, and 1 MiB per output file. A valid but wrong submission can score zero. Artifacts are evaluated from file snapshots; process state and files outside submission do not count.
