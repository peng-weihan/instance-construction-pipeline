#!/bin/sh
set -eu
unset PYTHONPATH PYTHONHOME PYTHONSTARTUP LD_PRELOAD LD_LIBRARY_PATH
export PATH=/usr/bin:/bin LANG=C LC_ALL=C
exec /usr/local/bin/python3 -I /tests/grader.py
