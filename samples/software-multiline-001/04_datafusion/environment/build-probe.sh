#!/bin/sh
set -eu
workspace=/home/workspace/datafusion-sort-topk/submission
mkdir -p "$workspace/datafusion/physical-plan/src/bin"
cp /opt/devprobe/edgebench-sort.rs "$workspace/datafusion/physical-plan/src/bin/edgebench-sort.rs"
cd "$workspace"
cargo build --offline --release --locked -p datafusion-physical-plan --bin edgebench-sort --jobs 2
