"""Read-only source reconnaissance. No build, task generation, or model calls."""
from __future__ import annotations

import concurrent.futures
import datetime as dt
import hashlib
import json
from pathlib import Path
import urllib.request

ROOT = Path(__file__).resolve().parent / "sources"
REPOS = ["openapi-generators/openapi-python-client", "apache/datafusion", "apache/polaris", "jqlang/jq"]


def get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "edgebench-source-research", "Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(req, timeout=45) as response:
        return response.read()


def mine(repo: str) -> dict:
    folder = ROOT / repo.replace("/", "__")
    folder.mkdir(parents=True, exist_ok=True)
    meta = json.loads(get(f"https://api.github.com/repos/{repo}"))
    commit = json.loads(get(f"https://api.github.com/repos/{repo}/commits/{meta['default_branch']}"))
    sha = commit["sha"]
    tree = json.loads(get(f"https://api.github.com/repos/{repo}/git/trees/{sha}?recursive=1"))
    blobs = [x for x in tree["tree"] if x["type"] == "blob"]
    paths = [x["path"] for x in blobs]
    (folder / "tree.json").write_text(json.dumps({"sha": sha, "truncated": tree.get("truncated"), "blobs": blobs}, indent=2) + "\n")
    selected = [p for p in paths if p in {"README.md", "LICENSE", "LICENSE.txt", "COPYING", "CHANGELOG.md", "pyproject.toml", "benchmarks/README.md", "datafusion/sqllogictest/README.md", "end_to_end_tests/README.md", "spec/README.md"}]
    records = []
    for path in selected:
        content = get(f"https://raw.githubusercontent.com/{repo}/{sha}/{path}")
        dest = folder / "files" / path
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(content)
        records.append({"path": path, "sha256": hashlib.sha256(content).hexdigest(), "bytes": len(content), "url": f"https://github.com/{repo}/blob/{sha}/{path}"})
    evidence = {
        "repo": repo, "default_branch": meta["default_branch"], "commit": sha,
        "commit_date": commit["commit"]["committer"]["date"],
        "retrieved_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "license_metadata": meta.get("license"), "tree_truncated": tree.get("truncated"),
        "blob_count": len(blobs), "selected_files": records,
        "status": "source_reconnaissance_only_not_constructed_or_calibrated",
    }
    (folder / "manifest.json").write_text(json.dumps(evidence, indent=2) + "\n")
    return evidence


if __name__ == "__main__":
    ROOT.mkdir(parents=True, exist_ok=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        for result in pool.map(mine, REPOS):
            print(json.dumps({k: result[k] for k in ("repo", "commit", "blob_count", "tree_truncated", "status")}))
