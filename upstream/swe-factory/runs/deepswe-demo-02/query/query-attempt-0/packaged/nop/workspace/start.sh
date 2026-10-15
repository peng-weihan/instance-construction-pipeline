#!/bin/sh
set -eu
cd /workspace
git init -q
git add -Af
git -c user.name=Factory -c user.email=factory@example.invalid -c commit.gpgsign=false commit -qm Problem
git rev-parse HEAD > /tmp/factory-baseline
