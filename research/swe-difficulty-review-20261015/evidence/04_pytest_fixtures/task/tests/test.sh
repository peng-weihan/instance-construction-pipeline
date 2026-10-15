#!/bin/sh
set -eu
unset PYTHONPATH PYTHONHOME PYTHONSTARTUP LD_PRELOAD
export PATH=/opt/venv/bin:/usr/bin:/bin
exec /opt/venv/bin/python -I /tests/grader.py
