#!/bin/sh
set -eu
here=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
target=/home/workspace/restler_campaign_recovery/submission
mkdir -p "$target"
tar -xzf "$here/reference-draft.tar.gz" -C "$target"
printf '%s\n' 'Installed held native checkpoint prototype. Full Polaris reference is incomplete.'
