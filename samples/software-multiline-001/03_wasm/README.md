# WebAssembly profile pilot — hold for evidence

The package contains a real Python bytecode interpreter, independent V8-generated expected results, a deliberately incomplete starter, eight semantic scoring groups, and two semantically broken references. This is a bounded profile smoke test, not a full Wasm implementation or an accepted six-hour task.

Use Python 3.12 for authoring:

```
python3.12 authoring/prepare.py
python3.12 authoring/run_controls.py
python3.12 authoring/finalize_report.py
```

Frozen scoring needs only Python's standard library and the bundled private fixtures. To regenerate oracle fixtures offline on macOS arm64 or Linux x64, use `python3.12 authoring/prepare.py --regenerate` with Node v24.13.1 already available. Pinned wasmtime/importlib_resources wheels are bundled. `--fetch-node` is an explicit author-only network option with official URL and SHA256 verification. `--fetch-missing` retrieves only missing pinned source archives and checks hashes. None of those authoring tools are copied into the work image. If regenerating changes fixture bytes, update the recorded fixture digest through `authoring/assemble.py`, re-run all controls and review the scoring contract before accepting a new version.

Build contexts are independent: `docker build -f environment/Dockerfile environment` and `docker build -f verifier/Dockerfile verifier`. Images have not been built or run in this round. Required image names are in task.toml; separate judge image binding is explicit and is not assumed to happen automatically. `pipeline-profile.json` records snapshot artifacts and valid-then-score selection for later adapter integration; actual best-of-run behavior has not been executed.

See source-card.md, AUTHORING_REPORT.json and authoring/controls/summary.json for measured evidence and remaining blockers. Root tests/grader.py and verifier/tests/grader.py are byte-identical copies of one authoritative scorer.
