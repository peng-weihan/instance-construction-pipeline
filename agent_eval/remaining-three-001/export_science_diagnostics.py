"""Read-only, frozen export of completed science grading diagnostics."""
from pathlib import Path
import datetime as dt
import hashlib
import json

root = Path('/ws/users/raymone/edgebench/remaining-three-001/science-pilot/run-6h-001')
history_bytes = (root / 'evaluation/history.json').read_bytes()
history = json.loads(history_bytes)
entries = []
for entry in history['entries']:
    if entry.get('status') != 'completed' or entry.get('valid') is not True:
        continue
    feedback_path = root / 'evaluation/submissions' / entry['round'] / 'feedback.json'
    feedback_bytes = feedback_path.read_bytes()
    feedback = json.loads(feedback_bytes)
    assert feedback['valid'] is True and abs(feedback['score'] - entry['score']) < 1e-12
    entries.append({'entry': entry, 'feedback_sha256': hashlib.sha256(feedback_bytes).hexdigest(),
                    'raw_metrics': feedback['raw_metrics']})
print(json.dumps({'observed_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
                  'source': str(root), 'history_sha256': hashlib.sha256(history_bytes).hexdigest(),
                  'entries': entries}, ensure_ascii=False))
