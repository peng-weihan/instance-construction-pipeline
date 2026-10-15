"""Verify copied working-tree bytes and symlinks; Git internals are mutable."""
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess

ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path("/Users/raymone/Desktop/01_Research/swe-factory")
COPY = ROOT / "upstream/swe-factory"


def inventory(root):
    records = {}
    for parent, dirs, files in os.walk(root, followlinks=False):
        dirs[:] = [name for name in dirs if name != ".git"]
        for name in dirs + files:
            path = Path(parent) / name
            mode = stat.S_IMODE(path.lstat().st_mode)
            if path.is_symlink():
                value = {"type": "symlink", "target": os.readlink(path), "mode": mode}
            elif path.is_file():
                value = {"type": "file", "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                         "bytes": path.stat().st_size, "mode": mode}
            else:
                value = {"type": "directory", "mode": mode}
            records[str(path.relative_to(root))] = value
    return records


def main():
    a, b = inventory(SOURCE), inventory(COPY)
    changed = [key for key in sorted(a.keys() | b.keys()) if a.get(key) != b.get(key)]
    assert not changed, f"Copy differs on {len(changed)} entries: {changed[:10]}"
    tree_hash = hashlib.sha256(json.dumps(a, sort_keys=True).encode()).hexdigest()
    result = {"source_path": str(SOURCE), "copied_path": str(COPY),
              "copy_method": "cp -a", "working_tree_identical": True,
              "comparison_scope": "All entries except .git internals; contents, symlink targets and modes.",
              "entries": len(a), "working_tree_sha256": tree_hash,
              "git_commit": subprocess.check_output(["git", "-C", str(COPY), "rev-parse", "HEAD"], text=True).strip(),
              "git_status": subprocess.check_output(["git", "-C", str(COPY), "status", "--short"], text=True),
              "pipeline_execution_this_session": False}
    (ROOT / "research/reference_copy_manifest.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(f"Verified identical copy: {len(a)} working-tree entries; Git HEAD {result['git_commit']}.")


if __name__ == "__main__":
    main()
