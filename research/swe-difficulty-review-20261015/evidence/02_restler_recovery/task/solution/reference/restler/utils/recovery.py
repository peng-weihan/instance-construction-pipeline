# Copyright (c) 2026 EdgeBench task authors. Licensed under the MIT License.
"""Durable ordered replay through the native BFS engine.

Only transport responses and nondeterministic primitive values are replayed.
Parsers, dependency propagation, sequence extension, coverage and deletion remain
native engine operations. A service supporting Idempotency-Key resolves an
intent whose response was lost. Never retry such an intent under a new key.
"""
import atexit
import fcntl
import hashlib
import json
import os
from pathlib import Path
import uuid

_session = None


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def sync_dir(path):
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def atomic(path, value):
    tmp = path.with_name(path.name + '.tmp')
    with open(tmp, 'wb') as f:
        f.write(encoded(value))
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)
    sync_dir(path.parent)


class Session:
    def __init__(self, directory, resume, fingerprint):
        self.path = Path(directory).resolve()
        self.path.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.lock = open(self.path / 'lock', 'a+b')
        try:
            fcntl.flock(self.lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            self.lock.close()
            raise ValueError('campaign already owned by another process')
        atexit.register(self.lock.close)
        self.journal = self.path / 'journal.jsonl'
        self.events = []
        self.cursor = 0
        self.chain = '0' * 64
        self.records = 0
        self.completed = False
        self.last_generation = 0
        if self.journal.exists():
            if not resume:
                raise ValueError('campaign exists; specify --resume')
            self.read()
            if self.header.get('fingerprint') != fingerprint:
                raise ValueError('campaign configuration does not match')
        else:
            if resume:
                raise ValueError('no durable campaign to resume')
            self.header = {'kind': 'header', 'version': 1, 'campaign': uuid.uuid4().hex,
                           'fingerprint': fingerprint}
            self.append(self.header)

    def append(self, payload):
        record = {'index': self.records, 'previous': self.chain, 'payload': payload}
        record['sha256'] = digest(encoded(record))
        with open(self.journal, 'ab') as f:
            f.write(encoded(record) + b'\n')
            f.flush()
            os.fsync(f.fileno())
        sync_dir(self.path)
        self.chain = record['sha256']
        self.records += 1

    def read(self):
        data = self.journal.read_bytes()
        end = 0
        for line in data.splitlines(keepends=True):
            if not line.endswith(b'\n'):
                break  # A kill can interrupt only the last append.
            try:
                record = json.loads(line)
                checksum = record.pop('sha256')
                if (record['index'] != self.records or record['previous'] != self.chain
                        or digest(encoded(record)) != checksum):
                    raise ValueError('checksum/ordering')
                p = record['payload']
                kind = p['kind']
                if self.records == 0:
                    if kind != 'header' or p['version'] != 1:
                        raise ValueError('header')
                    self.header = p
                elif kind == 'result':
                    if not self.events or self.events[-1]['kind'] != 'request' or 'response' in self.events[-1]:
                        raise ValueError('orphan result')
                    if p['event'] != len(self.events) - 1:
                        raise ValueError('result identity')
                    self.events[-1]['response'] = p['response']
                elif kind in ('request', 'uuid', 'generation', 'done'):
                    if self.completed or (self.events and self.events[-1]['kind'] == 'request' and 'response' not in self.events[-1]):
                        raise ValueError('event after unresolved intent or completion')
                    self.events.append(p)
                    if kind == 'done':
                        self.completed = True
                else:
                    raise ValueError('record kind')
                self.chain = checksum
                self.records += 1
                end += len(line)
            except Exception as error:
                raise ValueError(f'corrupt durable journal at record {self.records}: {error}') from error
        if not self.records:
            raise ValueError('missing durable header')
        # Never append after a torn tail, or it would become interior corruption.
        with open(self.journal, 'r+b') as f:
            f.truncate(end)
            f.flush()
            os.fsync(f.fileno())

    def event(self, kind, value):
        if self.cursor < len(self.events):
            p = self.events[self.cursor]
            if p['kind'] != kind:
                raise ValueError('replay event kind diverged')
            if kind != 'uuid' and any(p.get(k) != v for k, v in value.items()):
                raise ValueError('replay event content diverged')
        else:
            if self.completed:
                raise ValueError('attempt to extend completed campaign')
            p = dict(kind=kind, **value)
            self.append(p)
            self.events.append(p)
        self.cursor += 1
        return p

    def exchange(self, message, send):
        from engine.transport_layer.response import HttpResponse
        p = self.event('request', {'message': message})
        index = self.cursor - 1
        if 'response' in p:
            return True, HttpResponse(p['response'])
        key = f"{self.header['campaign']}:{index}"
        head, body = message.split('\r\n\r\n', 1)
        if any(line.lower().startswith('idempotency-key:') for line in head.split('\r\n')[1:]):
            raise ValueError('grammar must not supply Idempotency-Key')
        wire = head + '\r\nIdempotency-Key: ' + key + '\r\n\r\n' + body
        ok, response = send(wire)
        if not ok or not response.status_code or response.status_code in ('598', '599'):
            # Do not let failure advance the BFS campaign past an ambiguous write.
            raise RuntimeError('unresolved durable request; restart with --resume')
        result = response.to_str
        self.append({'kind': 'result', 'event': index, 'response': result})
        p['response'] = result
        return True, response


def configure(args):
    global _session
    directory = args.get('recovery_dir')
    if args.get('resume') and not directory:
        raise ValueError('--resume requires --recovery_dir')
    if not directory:
        return
    if (args.get('fuzzing_mode') != 'bfs' or args.get('fuzzing_jobs', 1) != 1
            or args.get('garbage_collection_interval') or args.get('run_gc_after_every_sequence')
            or args.get('disable_checkers') != ['*'] or args.get('enable_checkers')
            or args.get('replay_log') or args.get('replay') or args.get('custom_checkers')
            or args.get('custom_value_generators') or args.get('generate_random_seed')
            or args.get('create_once') or args.get('create_prefix_once')
            or args.get('per_resource_settings') or args.get('authentication')
            or args.get('add_fuzzable_dates') or args.get('token_refresh_cmd')
            or args.get('token_refresh_interval')):
        raise ValueError('recovery requires sequential BFS, disabled checkers, no asynchronous GC/auth/custom generators')
    config = dict(args)
    for name in ('recovery_dir', 'resume', 'settings_file_exists', 'settings', 'restler_grammar', 'custom_mutations', 'grammar_schema'):
        config.pop(name, None)
    for name in ('settings', 'restler_grammar', 'custom_mutations'):
        file = args.get(name)
        if file:
            config[name + '_sha256'] = digest(Path(file).read_bytes())
    schema = args.get('grammar_schema')
    config['grammar_schema_sha256'] = digest(Path(schema).read_bytes()) if schema and Path(schema).is_file() else None
    _session = Session(directory, args.get('resume', False), digest(encoded(config)))


def active():
    return _session is not None


def exchange(message, send):
    return _session.exchange(message, send)


def uuid4():
    if not active():
        return uuid.uuid4()
    p = _session.event('uuid', {'value': str(uuid.uuid4())})
    return uuid.UUID(p['value'])


def generation(number):
    if not active():
        return
    _session.event('generation', {'number': number})
    _session.last_generation = number
    receipt = {'generation': number, 'events': _session.cursor}
    current = _session.path / 'checkpoint.json'
    if current.exists():
        try:
            old = json.loads(current.read_bytes())
            atomic(_session.path / 'checkpoint.previous.json', old)
        except (ValueError, OSError):
            pass
    atomic(current, receipt)


def finish():
    if not active():
        return
    _session.event('done', {})
    if _session.cursor != len(_session.events):
        raise ValueError('replay ended before durable history')
    _session.completed = True
