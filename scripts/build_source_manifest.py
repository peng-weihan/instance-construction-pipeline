"""Record local source revisions and hashes; no network or benchmark execution."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
PAPERS = {
    "edgebench-2607.05155": "2607.05155",
    "reasoning-gym-2505.24760": "2505.24760",
    "ale-bench-2506.09050": "2506.09050",
    "re-bench-2411.15114": "2411.15114",
    "mle-bench-2410.07095": "2410.07095",
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    repos = []
    for directory, url in [
        ("upstream/EdgeBench", "https://github.com/ByteDance-Seed/EdgeBench"),
        ("data/EdgeBench", "https://huggingface.co/datasets/ByteDance-Seed/EdgeBench"),
    ]:
        commit = subprocess.check_output(
            ["git", "-C", str(ROOT / directory), "rev-parse", "HEAD"], text=True).strip()
        files = []
        for path in sorted((ROOT / directory).rglob("*")):
            if path.is_file() and ".git" not in path.relative_to(ROOT / directory).parts:
                files.append({"path": str(path.relative_to(ROOT)), "bytes": path.stat().st_size,
                              "sha256": digest(path)})
        repos.append({"path": directory, "source_url": url, "commit": commit, "files": files})
    # Check resolved HF LFS assets against pointer digests from the immutable Git tree.
    for path in (ROOT / "data/EdgeBench/assets").iterdir():
        rel = str(path.relative_to(ROOT / "data/EdgeBench"))
        blob = subprocess.check_output(["git", "-C", str(ROOT / "data/EdgeBench"),
                                        "show", f"HEAD:{rel}"])
        if blob.startswith(b"version https://git-lfs.github.com/spec/v1"):
            pointer = dict(line.split(" ", 1) for line in blob.decode().splitlines())
            assert digest(path) == pointer["oid"].removeprefix("sha256:"), rel
            assert path.stat().st_size == int(pointer["size"]), rel
    papers = []
    for stem, arxiv_id in PAPERS.items():
        path = ROOT / "papers" / f"{stem}.pdf"
        assert path.read_bytes().startswith(b"%PDF"), path
        version = re.search(r"arXiv:" + re.escape(arxiv_id) + r"(v\d+)",
                            path.with_suffix(".txt").read_text()).group(1)
        papers.append({"path": str(path.relative_to(ROOT)),
                       "text_path": f"papers/{stem}.txt",
                       "source_url": f"https://arxiv.org/abs/{arxiv_id}",
                       "download_url": f"https://arxiv.org/pdf/{arxiv_id}",
                       "arxiv_version": version,
                       "immutable_url": f"https://arxiv.org/pdf/{arxiv_id}{version}",
                       "sha256": digest(path), "bytes": path.stat().st_size})
    out = {"manifest_created_at_utc": datetime.now(timezone.utc).isoformat(),
           "repositories": repos, "papers": papers,
           "acquisition_scope": {
               "public_task_definitions": 51,
               "full_task_metadata_from_paper": 134,
               "hf_lfs_assets_resolved_and_verified": True,
               "docker_images_pulled": False,
               "hidden_data_and_evaluators_inspected_inside_images": False,
               "model_evaluations_run": False,
               "notes": "Task definitions and paper metadata are distinct from image-contained runtime data and graders."
           }}
    (ROOT / "research/source_manifest.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2) + "\n")
    print(f"Verified {len(papers)} PDFs, {len(repos)} repositories and all HF LFS assets.")


if __name__ == "__main__":
    main()
