#!/bin/sh
set -eu
git apply --binary "$(dirname "$0")/solution.patch"
