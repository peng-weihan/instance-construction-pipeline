#!/bin/sh
set -eu
here=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
workspace=/home/workspace/datafusion-sort-topk/submission
mkdir -p "$workspace"
tar -xzf "$here/reference.tar.gz" --strip-components=1 -C "$workspace"
# Open-solution reference is genuine upstream baseline, not a claimed optimized upper anchor.
