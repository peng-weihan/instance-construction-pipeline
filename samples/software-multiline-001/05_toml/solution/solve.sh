#!/bin/sh
set -eu
here=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
workspace=/home/workspace/toml-string-recovery
mkdir -p "$workspace"
rm -rf "$workspace/submission"
tar -xzf "$here/reference.tar.gz" -C "$workspace"
