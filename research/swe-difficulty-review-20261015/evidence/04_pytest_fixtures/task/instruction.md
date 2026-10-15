Implement a deterministic fixture lifecycle journal in the real pytest repository at
`/home/workspace/pytest-fixture-trace/submission` (fixed upstream commit
`c9c19f8e62c12834ad83193a1869cc82fe9c700e`). The starter is a complete pytest
checkout with a working hook-only diagnostic baseline. It observes setup and
post-finalization, but does not yet satisfy the causal event contract below.

All graded source and configuration changes must be inside `submission/`. Deliver
an installable pytest wheel from this project, preserving its native entrypoints.
You may implement the feature in core, plugins, or both. Ordinary dependencies and
tools supplied in the image are permitted. The evaluator builds your project from
a source snapshot, installs that wheel, and runs fresh pytest subprocesses offline.
Public development checks outside submission are feedback only; editing them does
not change authoritative checks.

Run `python -m pytest --fixture-trace=PATH ...`. With this option, write UTF-8 JSONL
to PATH, truncating it for each invocation. PATH's parent already exists. With the
option absent, do not create a journal or call the new trace observer hook. Do not
change fixture results, cache comparison counts, exception propagation, setup or
cleanup order, or pytest exit status. The supported boundary is single-process
pytest on Python 3.12, ordinary synchronous fixtures, built-in scopes, native
parametrization, fixture overrides, and synchronous pluggy hook wrappers. xdist,
async plugins, concurrent sessions, and abrupt process termination are not part of
this task. Preserve the upstream fixture regressions, including error locations.

Each event has `schema: 1`, consecutive integer `seq` starting at 1, and `event`.
Fields described below are mandatory; do not serialize user fixture values,
parameter values, callback reprs, exception messages, addresses, timestamps, or
absolute runtime paths. Node IDs and base IDs use pytest's existing relative IDs.
Definition and instance IDs are positive integers, assigned deterministically in
first-observed order. No implementation-specific fields are needed.

| event | Other fields and meaning |
|---|---|
| `definition` | `fixture`, `name`, `baseid`, `scope`: emit once per real FixtureDef identity before referring to it. Overrides with the same name have different IDs. Scope here is the declared fixture scope. |
| `setup_start` | `fixture`, `instance`, `nodeid`, `scope`, `param_index`: allocate one globally unique instance ID immediately before the native setup-hook invocation, after dependencies and cache checks. Scope is the effective request scope. Param index is the integer native request index, or null without a parameter. |
| `setup_end` | `fixture`, `instance`, `outcome`, `error`: exactly one per start, after setup hook wrappers complete. Outcome is `passed`, `skipped` (pytest skip), or `error`. Error is null on success and the exception class name otherwise. |
| `resolve` | `fixture`, `instance`, `parent`, `requested`, `kind`, `nodeid`, `outcome`, `error`: emit at completion of every native `_get_active_fixturedef(name)` resolution, except the special `request` fixture. Parent is the requesting fixture's definition ID, or null for an item request. Kind is `item` for null parent, `static` when name is in the parent's declared argument names, and `dynamic` otherwise. Successful resolution uses `passed`/null and the resolved identity; exceptions use `error` or `skipped`, exception class name, and null fixture/instance. This traces definition resolution, including exceptions, rather than source-text calls. |
| `cache_hit` | `fixture`, `instance`, `nodeid`, `layer`, `outcome`: report both the per-item `_fixture_defs` shortcut (`layer: item`) and FixtureDef's cache-key hit (`layer: instance`). Outcome is `value` or `error` for a cached exception. Emit before returning/rethrowing. Do not add cache-key comparisons. |
| `finalize_start` | `fixture`, `instance`, `reason`: only when finishing a still-cached instance. Reason is `parameter` for a cache-key mismatch, `dependency` when a dependency's registered callback initiates finishing, or `scope` for scheduled/direct finishing. The actual first effective finish determines reason; later no-op callbacks emit nothing. |
| `finalizer_start` | `fixture`, `instance`, `ordinal`: immediately before each registered callback executes, including native post-finalizer-hook and dependency callbacks. Ordinals start at 1 in registration order for each instance. |
| `finalizer_end` | `fixture`, `instance`, `ordinal`, `outcome`, `error`: after that callback returns or raises; use the same outcome/error vocabulary as setup. Continue running all finalizers after callback errors, as native pytest does. Callbacks registered during cleanup must retain native behavior. |
| `invalidate` | `fixture`, `instance`, `reason`: once after callbacks complete and the native cache and finalizer list have been cleared, even after failures. Same reason as the effective finalize_start. |
| `finalize_end` | `fixture`, `instance`, `errors`: immediately after invalidate, before native finalization exceptions propagate. Errors is the count of directly failing callbacks, not flattened exception leaves. |
| `report` | `nodeid`, `when`, `outcome`: one per completed runtest report, after makereport wrappers. When is setup/call/teardown; outcome is pytest's passed/failed/skipped. |

Every event for a particular fixture instance carries that same fixture and
instance ID. A resolve failure has null IDs even if a failed setup generated its
own lifecycle events. A cache hit can happen without a setup event on that item.
A resolve may follow nested resolutions and lifecycle events. Pytest resolves
signature dependencies at multiple internal points; retain those observations
rather than deduplicating them. The special `request` object is excluded entirely.
A no-op finish emits no lifecycle/finalizer/invalidation events. The native
post-finalizer hook still sees the cached value, at its original position.

Add public hook specification `pytest_fixture_trace_event(event)`. Enabled tracing
notifies registered plugins once for every journal event, in sequence order, using
an immutable mapping of JSON-safe scalar fields. Write the journal row before
notification. Notification hooks must not mutate the authoritative row. For a
benign observer that synchronously requests an already-active fixture, queue
nested notifications so every observer receives seq order without recursive
notification dispatch. Preserve normal setup-hook wrapper behavior. Observers
that raise, recursively request the fixture currently being set up, or deliberately
alter pytest execution are outside the noninterference guarantee.

The score has six equally weighted semantic groups: identities/schema,
dependency resolution, cache semantics, invalidation/order, exception lifecycle,
and plugins/behavior. Each group contains four frozen checks. Passing more checks
in one group does not change another group's weight. A frozen set of six upstream
fixture regression tests gates the score; if that gate fails the score is zero.
Correct but incomplete implementations earn partial credit. Broken source builds,
timeouts and malformed diagnostics are scored submission failures. No performance
score is used. The verifier cannot access the network; dependencies are preloaded.

For local feedback, run these commands from `submission/`:

```sh
python -m pytest ../dev_checks/test_trace_public.py -q
python -m pytest testing/python/fixtures.py -q
```

The environment initially installs submission in editable mode. If you change
packaging, reinstall with `python -m pip install --no-deps --no-build-isolation -e .`.
The public smoke check is intentionally small; it is not a complete contract test.
