#!/bin/sh
set -eu
here=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
cd "${SUBMISSION_ROOT:-/home/workspace/tree-sitter/submission}"
patch -p1 < "$here/restore.patch"
