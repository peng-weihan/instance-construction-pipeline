#!/bin/sh
set -eu
unset PYTHONPATH PYTHONHOME PYTHONSTARTUP LD_PRELOAD
exec /usr/local/bin/python3.12 -I /tests/grader.py
