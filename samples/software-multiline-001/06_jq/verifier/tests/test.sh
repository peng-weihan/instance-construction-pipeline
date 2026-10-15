#!/bin/sh
set -eu
unset PYTHONPATH PYTHONHOME PYTHONSTARTUP LD_PRELOAD
exec /usr/local/bin/python3 -I /tests/grader.py
