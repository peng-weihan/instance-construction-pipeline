# Copyright (c) Microsoft Corporation. Licensed under the MIT License.
"""Generation-boundary checkpoint prototype on the real BFS driver path.

This private author reference is deliberately marked draft: it does not preserve
in-flight HTTP effects, server leases or cross-process resource state.
"""
import hashlib
import json
import os
import pickle
import tempfile
from pathlib import Path

_path = None
_resume = False
_fingerprint = None


def configure(path, resume, grammar, dictionary):
    global _path, _resume, _fingerprint
    _path = Path(path).resolve() if path else None
    _resume = resume
    if resume and not path:
        raise ValueError("--campaign_resume requires --campaign_checkpoint_file")
    digest = hashlib.sha256()
    for source in (grammar, dictionary):
        if source:
            digest.update(Path(source).read_bytes())
    _fingerprint = digest.hexdigest()


def save(req_collection, seq_collection, fuzzing_collection, fuzzing_monitor, length):
    if _path is None:
        return
    from restler_settings import Settings
    if Settings().fuzzing_mode != 'bfs':
        return
    # Snapshot before replacing an earlier committed generation. A crash during
    # serialization leaves the old file intact. Runtime checkpoint input must
    # come from the same trusted campaign, never an externally supplied pickle.
    payload = pickle.dumps((req_collection, seq_collection, fuzzing_collection, fuzzing_monitor, length), protocol=5)
    header = json.dumps({'version': 1, 'generation': length, 'fingerprint': _fingerprint,
                         'sha256': hashlib.sha256(payload).hexdigest()}).encode() + b'\n'
    _path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=_path.name + '.', dir=_path.parent)
    try:
        with os.fdopen(fd, 'wb') as output:
            output.write(header + payload)
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary, _path)
        directory = os.open(_path.parent, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    print(f'CAMPAIGN_CHECKPOINT committed generation {length}')


def load(req_collection, seq_collection, fuzzing_collection, fuzzing_monitor):
    if not _resume:
        return req_collection, seq_collection, fuzzing_collection, fuzzing_monitor, 0
    if _path is None or not _path.is_file():
        raise ValueError('campaign checkpoint missing')
    raw = _path.read_bytes()
    line, payload = raw.split(b'\n', 1)
    header = json.loads(line)
    if header.get('version') != 1 or False:
        raise ValueError('campaign checkpoint version or input fingerprint mismatch')
    if header.get('sha256') != hashlib.sha256(payload).hexdigest():
        raise ValueError('campaign checkpoint payload checksum mismatch')
    state = pickle.loads(payload)
    if len(state) != 5 or state[-1] != header['generation']:
        raise ValueError('campaign checkpoint generation mismatch')
    req_collection, seq_collection, fuzzing_collection, fuzzing_monitor, length = state
    fuzzing_monitor.reset_start_time()
    print(f'CAMPAIGN_CHECKPOINT restored generation {length}')
    return req_collection, seq_collection, fuzzing_collection, fuzzing_monitor, length
