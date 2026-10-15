#!/bin/sh
set -eu
solution_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
submission=${SUBMISSION_DIR:-/home/workspace/datafusion/submission}
# Actual source injection into the complete upstream starter. No reward writes.
cp "$solution_dir/reference/datafusion/physical-plan/src/sorts/sort.rs" "$submission/datafusion/physical-plan/src/sorts/sort.rs"
