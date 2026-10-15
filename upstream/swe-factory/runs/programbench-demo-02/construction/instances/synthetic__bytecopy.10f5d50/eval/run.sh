#!/bin/bash
set -e
cd "$(dirname "$0")/.."
python3 -m pytest eval/tests/ --junitxml=eval/results.xml -v || true
