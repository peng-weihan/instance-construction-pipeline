# 性能方向：10项定向复评

全部B：有技术难度上限，但没有实测剩余收益，不进入A。这里未运行任何候选或基准。

先做P1（DuckDB、libvips、LZ4、Lucene），再做P2（simdjson、RE2、libjxl）；LMDB、oneTBB、fast_float的关键未知更适合后置。优先级依据验证成本和工作负载可解释性，不是预计收益大小。

实现成熟并不排除小内核的高难潜力；本轮拒绝用代码量降低fast_float评价。其后置原因是强基线后的可测余量未知与精确oracle成本。

## 实际选读范围

| 来源 | 文件 | 已读行区间 | 文件总行数 |
|---|---|---|---|
| 34_duckdb | src/execution/radix_partitioned_hashtable.cpp | 241–300 | 1325 |
| 34_duckdb | test/sql/aggregate/aggregates/aggregate_state_spilling.test_slow | 1–87 | 155 |
| 35_simdjson | include/simdjson/generic/ondemand/parser-inl.h | 24–70 | 320 |
| 35_simdjson | tests/ondemand/ondemand_document_stream_tests.cpp | 1–75 | 2765 |
| 35_simdjson | benchmark/bench_stream_formats.cpp | 147–183 | 296 |
| 36_libvips | libvips/resample/thumbnail.c | 490–520 | 2102 |
| 36_libvips | libvips/resample/thumbnail.c | 878–935 | 2102 |
| 36_libvips | test/test-suite/test_resample.py | 176–225 | 325 |
| 57_lz4 | lib/lz4.c | 479–505 | 2883 |
| 57_lz4 | lib/lz4.c | 1025–1080 | 2883 |
| 57_lz4 | tests/fuzzer.c | 430–475 | 2333 |
| 57_lz4 | doc/lz4_Frame_format.md | 30–64 | 440 |
| 58_lucene | lucene/core/src/java/org/apache/lucene/search/WANDScorer.java | 45–135 | 688 |
| 58_lucene | lucene/core/src/test/org/apache/lucene/search/TestWANDScorer.java | 90–155 | 1138 |
| 59_re2 | re2/re2.cc | 734–790 | 1355 |
| 59_re2 | re2/re2.cc | 875–917 | 1355 |
| 59_re2 | re2/testing/dfa_test.cc | 53–132 | 376 |
| 60_fast_float | include/fast_float/parse_number.h | 219–263 | 635 |
| 60_fast_float | include/fast_float/parse_number.h | 298–344 | 635 |
| 60_fast_float | tests/basictest.cpp | 155–222 | 2495 |
| 61_libjxl | lib/jxl/enc_modular.cc | 310–365 | 1861 |
| 61_libjxl | doc/encode_effort.md | 1–49 | 49 |
| 61_libjxl | tools/benchmark/benchmark_codec_jxl.cc | 310–344 | 408 |
| 62_lmdb | libraries/liblmdb/mdb.c | 2651–2682 | 12923 |
| 62_lmdb | libraries/liblmdb/mdb.c | 2704–2770 | 12923 |
| 62_lmdb | libraries/liblmdb/mtest.c | 24–100 | 178 |
| 63_onetbb | src/tbb/arena.cpp | 364–430 | 950 |
| 63_onetbb | src/tbb/task_dispatcher.cpp | 31–73 | 241 |
| 63_onetbb | test/tbb/test_task_arena.cpp | 1890–1951 | 2329 |

合计：定向选读已完成；未达到全仓架构审计的30%覆盖门槛，不宣称全仓覆盖。每项核对实现和测试/规格，libjxl本次核对官方effort规格而未核对原生正确性测试。

在线官方交叉核对：DuckDB external aggregation、oneTBB chunking、libjxl effort说明与Symas LMDB简介。网页当前版本只用于核对强基线的存在，技术判断绑定素材commit；上游速度宣传未作本题收益证据。
