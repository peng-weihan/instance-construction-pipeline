#!/bin/sh
set -eu
unset PYTHONPATH PYTHONHOME PYTHONSTARTUP LD_PRELOAD LD_LIBRARY_PATH
export PATH=/usr/local/bin:/usr/bin:/bin
here=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
if [ -x /usr/local/bin/python3 ]; then
  exec /usr/local/bin/python3 -I "$here/grader.py" "$@"
fi
exec /usr/bin/python3 -I "$here/grader.py" "$@"
