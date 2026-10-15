Optimize the pinned Apache DataFusion 50.0.0 sorting engine while preserving its results and native regressions. The workspace is `/home/workspace/datafusion`; deliver production Rust source in `submission/`. This is an open performance task, with a usable full upstream starter. Existing external sort, TopK, memory reservations, and spill are already implemented.

The fixed source is apache/datafusion commit `10343c18292fc3a9ca62b59c8bb530169fe79b82`, Apache-2.0. Dependencies and Cargo.lock are frozen and vendored. The installed Rust toolchain is 1.90.0 (MSRV 1.86). Network access is disabled. Keep builds outside `submission` using the provided CARGO_TARGET_DIR.

The authoritative build reconstructs the original checkout and takes your `.rs` files only from these production directories:

- `datafusion/physical-plan/src/sorts/`
- `datafusion/physical-plan/src/topk/`
- `datafusion/physical-plan/src/spill/`
- `datafusion/execution/src/memory_pool/`

Keep every existing source file in these directories. New Rust modules are allowed. Other edits, Cargo changes, examples, fixtures, and test edits are not taken into the authoritative build. Existing `#[cfg(test)] mod tests` sections are restored from upstream. Preserve their module boundary. The real probe is injected by the verifier. Candidate compilation and execution run without access to private expected answers or rewards.

Workloads execute actual RecordBatches through SortExec, its bounded TopK path, and partition-local SortExec followed by SortPreservingMergeExec. A direct sort_batch workload also exercises the kernel. Full sorts, sorted/reverse/duplicate data, low-memory external sort, binary UTF-8 including empty/non-ASCII/NUL strings, NULL placement, floating values including infinities, canonical positive NaN, and both signed zeros are covered. Every output column must preserve the original row.

Each order has an explicit final `id ASC` key, so equal primary values have a unique result; no implicit tie stability is assumed. NULLS FIRST/LAST is independent of ASC/DESC. Strings use binary UTF-8 order, without locale collation. Float64 uses Arrow's total order (`-0 < +0`, positive NaN above +infinity before applying DESC). LIMIT/OFFSET applies after global order; planner-equivalent empty execution handles LIMIT 0. Partition boundaries and output batch sizes cannot change the result. Low-memory cases must actually spill. These limits apply to DataFusion memory-pool reservations; the process also holds the immutable input and validation data. Whole-process RSS is an author audit metric and is not graded in this draft. Keep ordinary upstream semantics beyond this probe, including error handling and memory release.

The public `public/baseline-configs.json` preserves the strongest configurations observed in a bounded host sweep. Timings there are screening evidence, not portable score anchors. Use truthful existing input-order metadata whenever available; SortExec already skips satisfied orderings. Random input must never be falsely advertised as sorted.

Use the public check:

```sh
cargo build --manifest-path submission/Cargo.toml --locked --offline --release -p datafusion-physical-plan --example edgebench_sort
python3 public/check_public.py "$CARGO_TARGET_DIR/release/examples/edgebench_sort"
cargo test --manifest-path submission/Cargo.toml --locked --offline --release -p datafusion-physical-plan --lib 'sorts::sort::tests::' -- --test-threads=1
```

Public feedback includes three small cases and an independent scalar oracle. The verifier uses a frozen larger case matrix in six semantic groups plus the original sort unit regression suite. Graded artifacts are source snapshots; generated executables, reports, and caches do not count as submissions.

This delivered revision is a construction draft: correctness contributes at most 0.25, using numeric 0.04, UTF-8 0.03, floating 0.03, TopK 0.03, partitions 0.03, spill 0.04, and native regressions 0.05. Each semantic group receives its weight times its fraction of passed frozen cases. Compilation or missing-source failure scores zero. Infrastructure failures produce an invalid result without a numerical reward. The remaining 0.75 performance weight is disabled pending measured normalization and reproducibility qualification; it is not redistributed. Raw engine times, parent wall times and spill metrics are reported. Peak memory and physical I/O scoring are also pending. Correctness alone does not establish an optimization or task completion. Do not treat this draft as a calibrated six-hour benchmark.
