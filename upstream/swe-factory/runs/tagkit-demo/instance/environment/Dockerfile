FROM nl2repo-tagkit-dependencies
USER root
RUN python3 -c 'exec('"'"'from pathlib import Path\nimport shutil\nroots = ("/workspace", "/testbed", "/repo", "/app", "/src")\ndef remove(path):\n    if path.is_symlink() or path.is_file():\n        path.unlink()\n    elif path.exists():\n        shutil.rmtree(path)\nfor root in roots:\n    remove(Path(root))\nPath("/workspace").mkdir(parents=True)\nPath("/logs").mkdir(parents=True, exist_ok=True)\nlibrary = Path("/usr/local/lib")\nif library.exists():\n    artifacts = [p for p in library.rglob("*") if p.name.endswith(".egg-link") or p.name.startswith("__editable__")]\n    for path in sorted(artifacts, key=lambda p: len(p.parts), reverse=True):\n        remove(path)\n    for path in library.rglob("*.pth"):\n        if "site-packages" in path.parts and any(root in path.read_text(errors="replace") for root in roots):\n            remove(path)\n'"'"')'
COPY start.md /workspace/start.md
WORKDIR /workspace
