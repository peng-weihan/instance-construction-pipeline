#!/bin/sh
set -eu
HERE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
DEST=/home/workspace/restler-recovery/submission/restler
mkdir -p "$DEST"
cp "$HERE/reference/restler/restler.py" "$DEST/restler.py"
for FILE in engine/core/driver.py engine/core/request_utilities.py engine/transport_layer/messaging.py utils/recovery.py; do
  mkdir -p "$DEST/$(dirname "$FILE")"
  cp "$HERE/reference/restler/$FILE" "$DEST/$FILE"
done
