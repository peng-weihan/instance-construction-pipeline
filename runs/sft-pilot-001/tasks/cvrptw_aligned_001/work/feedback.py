#!/usr/bin/env python3
"""Submit an allowed source snapshot to the local aggregate-feedback queue."""
import base64, json, pathlib, time, uuid
root = pathlib.Path(__file__).resolve().parent
files = {}
for top in ["src", "include", "Makefile"]:
    target = root / top
    paths = [target] if target.is_file() else sorted(target.rglob("*"))
    for p in paths:
        if p.is_symlink(): raise SystemExit("Symlinks are not accepted")
        if p.is_file(): files[str(p.relative_to(root))] = base64.b64encode(p.read_bytes()).decode()
if sum(len(v) for v in files.values()) > 4_000_000: raise SystemExit("Submission too large")
queue = root / ".feedback"
queue.mkdir(exist_ok=True)
rid = uuid.uuid4().hex
temporary = queue / (rid + ".tmp")
temporary.write_text(json.dumps({"files": files}))
temporary.rename(queue / (rid + ".request.json"))
response = queue / (rid + ".response.json")
deadline = time.monotonic() + 180
while not response.exists():
    if time.monotonic() > deadline: raise SystemExit("Feedback service did not respond in 180 seconds")
    time.sleep(.25)
print(response.read_text())
