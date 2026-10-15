#!/bin/sh
set -eu
unset PYTHONPATH PYTHONHOME PYTHONSTARTUP LD_PRELOAD LD_LIBRARY_PATH
export PATH=/opt/rust/bin:/usr/local/bin:/usr/bin:/bin
exec /usr/local/bin/python3 -I /tests/entry.py "$@"
