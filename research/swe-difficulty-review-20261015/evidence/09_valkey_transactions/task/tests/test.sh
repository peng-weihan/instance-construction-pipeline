#!/bin/sh
set -eu
unset PYTHONPATH PYTHONHOME PYTHONSTARTUP LD_PRELOAD
PATH=/usr/local/bin:/usr/bin:/bin
export PATH
here=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
if [ -x /usr/local/bin/python3 ]; then
    interpreter=/usr/local/bin/python3
else
    interpreter=/usr/bin/python3
fi
exec "$interpreter" -I -S "$here/grader_entry.py" "$@"
