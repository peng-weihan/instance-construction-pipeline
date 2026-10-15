#!/bin/sh
set -eu
here=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
target=/home/workspace/openapi_composition/submission
mkdir -p "$target"
tar -xzf "$here/reference.tar.gz" -C "$target"
