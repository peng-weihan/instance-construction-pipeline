#!/bin/sh
set -eu
HERE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
DEST="${HTTPX_SUBMISSION_DIR:-/home/workspace/httpx/submission}/httpx"
mkdir -p "$DEST"
cp "$HERE"/reference-httpx/*.py "$DEST"/
cp "$HERE"/reference-httpx/py.typed "$DEST"/
