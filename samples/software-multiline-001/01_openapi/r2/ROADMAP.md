# Next candidate: actual endpoint execution and resource ownership

This is a research direction only, not a second constructed task. Frozen r1 is left intact and explicitly rejected for long-horizon admission: a cheap schema preprocessor already obtains its upper score.

Use the same complete generator, but first prove defects in generated network behavior using a real independent HTTP observer. Existing research source `open-issues.json` contains these official issue leads:

- #1255, binary arrays in multipart request bodies: https://github.com/openapi-generators/openapi-python-client/issues/1255 . Trace file-array representation through internal properties, multipart encoding, actual part headers/content and server observation. Couple this to repeated calls and file-position/ownership behavior explicitly specified by the new SDK contract. Reproduction at the fixed revision is still required.
- #1394, list form-data generation: https://github.com/openapi-generators/openapi-python-client/issues/1394 . Distinguish repeated fields, JSON encodings and upload parts; explicit standards/application choices must replace assumptions.
- #1451/#1276, required multi-body endpoints and identical model types: https://github.com/openapi-generators/openapi-python-client/issues/1451 and https://github.com/openapi-generators/openapi-python-client/issues/1276 . A correct API must select content type unambiguously and retain requiredness through signatures, imports, request encoding and sync/async calls.
- #1372, explicit anonymous security alternatives: https://github.com/openapi-generators/openapi-python-client/issues/1372 . Test actual observed authorization headers for public, authenticated and mixed endpoints; per-operation overrides must not leak credentials across shared clients.

Potential coherent deliverable: a generated transport API that chooses request representation explicitly, respects endpoint security and defines caller-versus-client ownership for uploaded streams in sync/async calls. A real HTTP service must observe bytes and resources independently of candidate self-reported traces; cancellation/exception tests should inspect open resources and server effects. Do not append twenty similarly shaped JSON model cases to r1.

A prerequisite is a runnable prototype reference and cheap-saturation audit against normal httpx APIs. These issue fixes may themselves still be quick template changes. If ordinary library wrapping closes the contract cheaply, reject this candidate too. No six-hour difficulty estimate, score, reference or completed implementation is asserted here.
