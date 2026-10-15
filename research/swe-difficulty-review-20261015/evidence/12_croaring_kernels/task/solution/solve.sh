#!/bin/sh
set -eu
here=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
workspace=${CROARING_WORKSPACE:-/home/workspace/croaring}
install -m 644 "$here/venn3.c" "$workspace/submission/src/venn3.c"
install -m 644 "$here/roaring_venn3.h" "$workspace/submission/include/roaring/roaring_venn3.h"
