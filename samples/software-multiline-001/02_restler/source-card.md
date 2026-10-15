# RESTler recovery source and closure decision

Official sources, full archives and licenses:

- https://github.com/microsoft/restler-fuzzer at `6d984deedbc54aad957fa3da0c7e9e5df23a2aee` (MIT), archived under `authoring/sources/restler.tar.gz`.
- https://github.com/apache/polaris at `f838a62e20e7de72946d250883e8d9b1d6d2f68e` (Apache-2.0), full archive under `authoring/sources/polaris.tar.gz`.

The concrete engineering material is the complete RESTler driver, renderer, transport, dependencies, trace/replay and GC. `restler/engine/core/driver.py` already calls `utils/saver.load/save` for BFS, but upstream save immediately returns and load prints “No checkpoints used at this phase” then returns. The old pickle code below those returns is unreachable and even opens binary files with an encoding argument. The apparent existing checkpoint shortcut is not usable. Native trace-database replay, however, already works and is a strong baseline; this task cannot count ordinary replay as a new invention.

The draft reference modifies the actual CLI → configure → driver → atomic save/load chain, fixes module registration for serializable grammar parser functions and restores the actual name-mangled monitor singleton. It is not a replacement miniature fuzzer. The prototype can save BFS generation 2 and resume a new process through generation 3 on RESTler's own full in-process test server. This is component evidence, not a real Polaris/HTTP lifecycle claim. The original native smoke and trace-database replay tests run through `restler.py` in child processes, with 2 passed before changes.

Polaris management semantics and intended truth sources are `spec/polaris-management-service.yml` and `client/python/integration_tests/test_management_apis.py`: create principal, grant principal role, grant catalog role, use authorization, revoke and cleanup. This is real target source, not a small authored Flask substitute. The current host has `/usr/bin/java` but no installed Java Runtime; an actual `./gradlew --offline projects` attempt fails before project startup. Gradle wrapper pins 9.7.1-all with SHA256 `92c1a136d76b5017732a66d2e0a648ebff00dd3687d8bff0d0047a1bd904fdf2`; Maven/Gradle dependency cache, JDK21 closure and server startup/reset remain unconstructed. No Docker/.NET/cloud execution occurred.

Strong B and shortcuts: complete upstream native replay already passes; restoring dormant BFS state is a short integration route, implemented in the draft. It cannot address in-flight side effects, resource IDs after a service reset, external HTTP trace integrity or owned/shared resource cleanup. Those are the real remaining engineering paths, not additional helper probes.

Two post-2h paths (hypotheses): (1) reconcile the request journal with service idempotency and regenerated producer/consumer IDs after crashes; (2) preserve ownership/dependency leases through resume and cancellation while keeping GC/replay behavior consistent. Neither has a verified reference in this package.

Cheapest falsification: first execute the official native CLI and test the dormant saver; then prove a pinned offline Polaris build and repeatable local reset before designing a full state oracle. Native replay and checkpoint prototype were actually exercised; service closure failed at JDK discovery. The formal grader therefore reports `valid=false`, no numeric reward, and records unexecuted groups. Missing service/reference is not candidate zero.

Decision: **hold_for_evidence**. Preserve the working native integration prototype and source evidence. Do not admit this as a completed ordinary oracle, a six-hour task, or a reproduction of full RESTler production recovery. Do not substitute the test-socket server for the absent real Polaris service.

Diagnostic trust limit: native smoke/replay are executed from the recorded candidate-bundled upstream unit tests. They establish these known author controls, but final scoring must freeze trusted copies independently; mutable solver tests cannot constitute a formal oracle. This is an additional formal-grader blocker, alongside the absent external Polaris service.
