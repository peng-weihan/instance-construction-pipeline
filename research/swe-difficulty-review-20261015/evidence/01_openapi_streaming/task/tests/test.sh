#!/bin/sh
set -eu
unset PYTHONPATH PYTHONHOME PYTHONSTARTUP LD_PRELOAD LD_LIBRARY_PATH
export PATH=/opt/venv/bin:/usr/local/bin:/usr/bin:/bin
exec /opt/venv/bin/python -I /tests/grader.py
