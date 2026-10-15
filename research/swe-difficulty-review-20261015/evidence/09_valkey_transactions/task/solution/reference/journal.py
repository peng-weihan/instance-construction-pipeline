"""Append-only framed effect journal. A whole EXEC is exactly one frame."""
import base64
import json
import os
import struct
import zlib

MAGIC = b'EKV1'
LIMIT = 16777216

def b64(raw):
    return base64.b64encode(raw).decode('ascii')

def un64(raw):
    if not isinstance(raw,str):
        raise ValueError('base64 type')
    decoded = base64.b64decode(raw, validate=True)
    if b64(decoded) != raw:
        raise ValueError('noncanonical base64')
    return decoded

def pack_entry(entry):
    if entry is None:
        return None
    kind, value, deadline = entry
    return [kind, b64(value) if kind == 's' else list(map(b64,value)), deadline]

def unpack_entry(entry):
    if entry is None:
        return None
    if not isinstance(entry,list) or len(entry)!=3:
        raise ValueError('entry shape')
    kind, value, deadline = entry
    if kind not in ('s','l') or (deadline is not None and (type(deadline) is not int or not 0 <= deadline < 2**63)):
        raise ValueError('entry')
    if kind == 'l' and not isinstance(value,list):
        raise ValueError('list shape')
    return [kind, un64(value) if kind == 's' else list(map(un64,value)), deadline]

class Journal:
    def __init__(self, path, store, failpoint='none'):
        self.path, self.store, self.failpoint = path, store, failpoint
        self.seq = 0
        existed = os.path.exists(path)
        self.file = open(path, 'a+b', buffering=0)
        if not existed:
            os.fsync(self.file.fileno())
            directory = os.open(os.path.dirname(path) or '.', os.O_RDONLY)
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
        self.recover()

    def recover(self):
        self.file.seek(0)
        good = 0
        while True:
            header = self.file.read(12)
            if not header:
                break
            if len(header) < 12:
                self.file.truncate(good)
                os.fsync(self.file.fileno())
                break
            magic, length, crc = struct.unpack('>4sII', header)
            if magic != MAGIC or not 1 <= length <= LIMIT:
                raise ValueError('corrupt journal header')
            payload = self.file.read(length)
            if len(payload) < length:
                self.file.truncate(good)
                os.fsync(self.file.fileno())
                break
            if zlib.crc32(payload) != crc:
                raise ValueError('corrupt journal checksum')
            rec = json.loads(payload)
            if not isinstance(rec,dict) or set(rec) != {'seq','now','changes'} or type(rec['seq']) is not int or rec['seq'] != self.seq+1:
                raise ValueError('journal sequence')
            if type(rec['now']) is not int or not self.store.now <= rec['now'] < 2**63:
                raise ValueError('journal clock')
            # Decode the entire record before applying any effects.
            if not isinstance(rec['changes'],list) or any(not isinstance(pair,list) or len(pair)!=2 for pair in rec['changes']):
                raise ValueError('changes shape')
            changes = [(un64(key), unpack_entry(value)) for key, value in rec['changes']]
            if len({k for k,v in changes}) != len(changes):
                raise ValueError('duplicate key')
            for key, entry in changes:
                if entry is None:
                    self.store.data.pop(key, None)
                else:
                    self.store.data[key] = entry
            self.store.now = rec['now']
            self.seq = rec['seq']
            good += 12 + length
        self.file.seek(0, os.SEEK_END)

    def commit(self, old_now):
        if not self.store.changed and old_now == self.store.now:
            return
        changes = [[b64(k), pack_entry(self.store.data.get(k))] for k in sorted(self.store.changed)]
        payload = json.dumps({'seq':self.seq+1, 'now':self.store.now, 'changes':changes},
                             sort_keys=True, separators=(',',':')).encode()
        if len(payload) > LIMIT:
            raise OSError('journal record limit')
        header = struct.pack('>4sII', MAGIC, len(payload), zlib.crc32(payload))
        def write_all(raw):
            while raw:
                n = self.file.write(raw)
                if not n:
                    raise OSError('short write')
                raw = raw[n:]
        if self.failpoint == 'before-write':
            os._exit(86)
        if self.failpoint == 'mid-header':
            write_all(header[:6])
            os.fsync(self.file.fileno())
            os._exit(86)
        write_all(header)
        if self.failpoint == 'mid-body':
            write_all(payload[:len(payload)//2])
            os.fsync(self.file.fileno())
            os._exit(86)
        write_all(payload)
        os.fsync(self.file.fileno())
        self.seq += 1
        if self.failpoint == 'after-sync':
            os._exit(86)
