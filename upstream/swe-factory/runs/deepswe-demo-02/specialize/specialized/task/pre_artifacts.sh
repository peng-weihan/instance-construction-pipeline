#!/bin/sh
set -eu
cd /workspace
git add -Af
git diff --cached --binary "$(cat /tmp/factory-baseline)" > /tmp/model.patch
