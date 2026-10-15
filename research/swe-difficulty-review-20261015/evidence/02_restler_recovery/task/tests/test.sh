#!/bin/sh
set -eu
unset PYTHONPATH PYTHONHOME PYTHONSTARTUP LD_PRELOAD
export PATH=/usr/local/bin:/usr/bin:/bin
exec /usr/local/bin/python -I /tests/grader.py
