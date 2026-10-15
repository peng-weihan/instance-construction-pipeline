#!/bin/sh
set -eu
here=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
target=${1:-/home/workspace/edgekv/submission}
mkdir -p "$target"
cp "$here"/reference/*.py "$target"/
