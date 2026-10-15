# Bounded three-bitmap histograms in CRoaring

Work in `/home/workspace/croaring`. The upstream source (with optional external real-data benchmark corpora omitted) is in `submission/`, fixed at CRoaring `f2d9c6d3affaed28c8a899e96d85334ce4ae35af` (Apache-2.0 OR MIT). This is an original extension, not an upstream missing-bug claim. Preserve native CRoaring semantics and portable interoperability.

Implement and optimize the C ABI declared in `public/roaring_venn3.h`:

```c
int roaring_bitmap_venn3_batch(const roaring_venn3_query_t *queries,
                             size_t n, uint64_t (*out)[8]);
```

A descriptor contains three valid 32-bit CRoaring bitmaps `a,b,c` and half-open 64-bit endpoints `begin,end`. For each integer `x` in `[begin,end)`, form mask `(x in a) | ((x in b)<<1) | ((x in c)<<2)`. Output the cardinality of each mask in bins 0 through 7. Bin 0 includes integers absent from all three inputs. This API must not enumerate the entire 2^32 universe merely to count absent integers. Endpoints may equal 4294967296; histogram totals must equal `end-begin`. Empty intervals produce eight zeroes.

Return 0 on success. Return -1 if any descriptor has a NULL bitmap, `begin>end`, or `end>4294967296`, or if `n>0` and either array pointer is NULL. Validate the entire batch before writing any output: an invalid final descriptor must leave earlier output untouched. `n=0` accepts NULL array pointers and succeeds. Do not dereference NULL for this case. Resource exhaustion is outside scored valid-input semantics.

Inputs may be empty, identical pointers, or shared copy-on-write clones, and may contain array, bitset, run or shared containers at any high key, including 65535. Inputs and their portable bytes must remain unchanged; copies sharing storage must also remain unchanged. Output has `n` rows and does not overlap inputs/descriptors. Calls are independent; persistent mutable caches are unnecessary. Preserve the existing C ABI and container layouts; compile cleanly as C11. Both the normal CPU-dispatched build and a build with x64/NEON acceleration disabled are checked. Ordinary supported library APIs and configurations are allowed.

Only `submission/src/` and `submission/include/` are graded source snapshots. You may change native kernels and add `.c` files under `src/`. Tests, compiler commands, the API declaration and grader remain authoritative outside the snapshot. Existing native regressions must pass. Do not remove or replace the actual library with a different program. Build scripts in submissions are not executed. No external downloads are available at agent or verifier runtime.

The starter is a correct ordinary API composition, including smallest-intersection selection and batch duplicate reuse. Its performance is a serious baseline. Improve actual engine paths without breaking semantics; dense, sparse, run, mixed and bounded-window distributions have different tradeoffs.

Local development commands:

```sh
python3 public/build.py submission build
python3 public/native.py submission build
# A public CLI fixture: no private expected answers required.
printf '0 3\n2 1 2\n2 2 3\n1 2\n1\n0 1 2 0 4\n' | build/runner
# Expect R 0 and V 1 1 1 0 0 0 0 1 (plus portable P lines).
gcc -O3 -march=native -std=c11 -Ipublic -Isubmission/include public/bench.c public/ordinary.c build/libroaring.a -o ordinary-bench
```

Draft scoring is deliberately explicit: four semantic groups (full universe, bounded ranges, batch validation/aliasing, portable/COW interoperability) each contribute up to 0.10, proportional to frozen cases across native and scalar builds. Failure of the five preserved native regression suites gates the score to zero. Compiler failures and timeouts are ordinary scored failures. The active maximum is 0.40. A further 0.60 performance contribution is **disabled**, with no numerical performance anchors or timing-based reward in this draft. Raw local benchmark timings are for author review. Target-platform performance scoring and six-hour difficulty have not been validated; this package is not yet accepted for a formal training run.
