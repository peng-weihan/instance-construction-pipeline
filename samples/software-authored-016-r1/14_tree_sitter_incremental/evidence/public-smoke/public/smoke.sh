#!/bin/sh
set -eu
cd "${PROJECT_ROOT:-/home/workspace/tree-sitter}"
mkdir -p submission/build
cc -std=c11 -D_DEFAULT_SOURCE -O1 -Isubmission/lib/include -Isubmission/lib/src public/probe.c submission/lib/src/lib.c grammar/src/parser.c grammar/src/scanner.c -o submission/build/probe
for input in public/*.bin; do
  echo "$input"
  submission/build/probe < "$input" > submission/build/"$(basename "$input")".out
done
