#!/bin/sh
set -eu
root=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
target=${SUBMISSION_DIR:-/home/workspace/wasm-profile/submission}
mkdir -p "$target"
cp "$root/runtime.py" "$target/runner.py"
