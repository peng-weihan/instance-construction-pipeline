#!/bin/sh
set -eu
root=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
target=${SUBMISSION_DIR:-/home/workspace/jq-profile/submission}
build=$(mktemp -d)
trap 'rm -rf "$build"' EXIT
python3 - "$root/jq-1.7.1-release.tar.gz" <<'PYCODE'
import hashlib,sys
assert hashlib.sha256(open(sys.argv[1],'rb').read()).hexdigest()=='478c9ca129fd2e3443fe27314b455e211e0d8c60bc8ff7df703873deeee580c2'
PYCODE
tar -xzf "$root/jq-1.7.1-release.tar.gz" -C "$build"
cd "$build/jq-1.7.1"
./configure --disable-docs --disable-maintainer-mode --disable-shared --enable-static --without-oniguruma
make -j2
mkdir -p "$target"
cp jq "$target/jq"
cp "$root/runner.py" "$target/runner.py"
