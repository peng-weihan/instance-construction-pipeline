#!/bin/sh
set -eu
cc -O0 repo/main.c -o executable
chmod +x executable
