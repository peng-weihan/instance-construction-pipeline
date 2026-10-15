#!/bin/sh
set -eu
here=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
submission=/home/workspace/pytest-fixture-trace/submission
mkdir -p "$submission"
tar -xzf "$here/reference.tar.gz" -C "$submission"
