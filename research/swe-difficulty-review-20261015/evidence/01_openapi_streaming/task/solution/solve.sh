#!/bin/sh
set -eu
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
TARGET=${SUBMISSION_DIR:-/home/workspace/openapi-streaming/submission}
mkdir -p "$TARGET"
cp -R "$SCRIPT_DIR/reference/." "$TARGET/"
