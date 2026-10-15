# jq CLI reconstruction pilot — hold for evidence

This package has a real official jq-1.7.1 source/release reference, an actual offline reference build recipe, a partial general evaluator starter, frozen behavior tests and two distinct partial-control implementations. It rebuilds a compositional CLI; submitting one filter does not satisfy the task.

Use Python 3.12 for authoring:

```
python3.12 authoring/prepare.py
python3.12 authoring/run_controls.py
python3.12 authoring/finalize_report.py
```

The retained source/build archive is self-contained and the grader needs only Python standard library plus frozen private fixtures. To rebuild the original reference and regenerate truth, use `python3.12 authoring/prepare.py --build-reference --regenerate`; a C compiler and make are required. No optional regex dependency is used. `--fetch-missing` is an explicit author-only option for downloading missing archives from fixed URLs and checking SHA256. The existing local controls used the real unmodified release built on macOS; Linux behavior is pending. The system Apple jq was version-recorded separately and was not the oracle.

Native solution recipe: set `SUBMISSION_DIR` to a new local directory and run `sh solution/solve.sh`; it validates the bundled release hash, compiles the original program with static libjq, and installs jq plus the Python entrypoint into the scored artifact directory. The recipe itself was executed successfully on the host and its installed artifact was scored by the same grader. It is private author/reference material and is never copied into the work context. Judge images contain fixed expected outputs and no jq executable, eliminating a callable private answer engine.

Build contexts: `docker build -f environment/Dockerfile environment` and `docker build -f verifier/Dockerfile verifier`. These commands were not run. task.toml names separate work/judge images; the pipeline profile records snapshot artifacts and valid-then-score selection, with runtime integration still unverified. See source-card.md and AUTHORING_REPORT.json for evidence and limitations.
